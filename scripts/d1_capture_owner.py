"""One fixed parent deadline owner for D1 capture; no scientific entry point.

Source, interpreter, startup and manager custody must be established externally.
A durable name claim survives a lost submit acknowledgement; it is not authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import d1_owned_capture as owned
from scripts.grid_q1_supervisor import (
    CommandFailure,
    Fault,
    Snapshot,
    Supervisor,
    Systemd,
    confirms_empty_unit_cleanup,
    private_bytes,
)


class Child(Protocol):
    def wait(self, timeout: float) -> int: ...
    def kill(self) -> None: ...


class Starter(Protocol):
    def start(self, spec: owned.CaptureSpec, path: Path, digest: str) -> Child: ...


class Controller:
    """Only this fixed child can submit. No command is selected by a plan."""

    def start(self, spec: owned.CaptureSpec, path: Path, digest: str) -> subprocess.Popen[bytes]:
        script = Path(__file__).resolve()
        if script != spec.checkout / "scripts/d1_capture_owner.py":
            raise ValueError("Fixed owner source location differs")
        return subprocess.Popen(
            [
                str(spec.interpreter),
                "-I",
                "-B",
                "-X",
                f"pycache_prefix={spec.root / 'owner-pycache'}",
                str(script),
                "controller",
                str(path),
                digest,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=spec.root,
            close_fds=True,
            env={**os.environ, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )


def read_record(files: owned.ReceiptIO, name: str) -> dict[str, object]:
    raw = files.read(name, owned.REPORT_BYTES)
    if type(raw) is not bytes or not 0 < len(raw) <= owned.REPORT_BYTES:
        raise ValueError("Bounded retained owner record required")
    value = json.loads(raw, object_pairs_hook=owned._pairs, parse_constant=owned._constant)
    if type(value) is not dict:
        raise ValueError("Retained record must be an object")
    return value


def terminal_snapshot(value: object) -> Snapshot:
    if type(value) is not dict or set(value) != {"properties", "populated"}:
        raise ValueError("Exact retained terminal snapshot required")
    properties, populated = value["properties"], value["populated"]
    if type(properties) is not dict or any(
        type(k) is not str or type(v) is not str for k, v in properties.items()
    ):
        raise ValueError("Exact snapshot property strings required")
    if populated is not None and type(populated) is not bool:
        raise ValueError("Exact populated observation required")
    return Snapshot(properties, populated)


def watch(
    spec: owned.CaptureSpec,
    starter: Starter,
    manager: Supervisor,
    files: owned.ReceiptIO,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
    sample_usage: Callable[[], dict[str, float]] = owned.usage,
) -> dict[str, object]:
    """A separate parent, armed before its one submit-capable child starts.

    Every wait/command is clipped to the original deadline. Arbitrary kernel,
    manager or filesystem stalls remain unknown; no kernel-wide 300s claim.
    """
    started = clock()
    cutoff, deadline = started + owned.WORK_SECONDS, started + owned.TERMINAL_SECONDS
    baseline = sample_usage()
    child: Child | None = None
    child_code: int | None = None
    child_reaped = claimed = stopped = closed = False
    first: Fault | None = None
    supplemental: list[Fault] = []
    latest: Snapshot | None = None
    invocation: str | None = None
    group: str | None = None
    child_result: dict[str, object] | None = None
    successful_child = False
    plan: owned.CapturePlan | None = None
    terminal_saved = False

    def fault(stage: str, error: BaseException) -> None:
        nonlocal first
        original = error.primary if isinstance(error, CommandFailure) else error
        item = Fault.capture(stage, original)
        if first is None:
            first = item
        elif len(supplemental) < 16:
            supplemental.append(item)
        if isinstance(error, CommandFailure):
            supplemental.extend(error.supplemental[: max(0, 16 - len(supplemental))])

    def remaining(end: float = deadline) -> float:
        value = min(5.0, end - clock())
        if value <= 0:
            raise TimeoutError("Original owner deadline")
        return value

    def bind(value: Snapshot) -> None:
        nonlocal latest, invocation, group, closed
        assert plan is not None
        value.bind(plan, invocation)
        if group is None:
            if not value.cgroup or value.populated is None:
                raise ValueError("No observed invocation/group before disappearance")
            group = value.cgroup
        elif value.cgroup and value.cgroup != group:
            raise ValueError("Owner observed a substituted group")
        if latest is not None and value.cpu_ns < latest.cpu_ns:
            raise ValueError("Owner observed decreasing CPU")
        latest, invocation = value, value.invocation
        closed = value.terminal and value.populated is not True

    try:
        spec.validate()
        if files.root != spec.root:
            raise ValueError("Owner receipt root differs")
        plan = owned.fixed_plan(spec, started)  # Validates root before any write.
        request = {
            "schema": "d1-capture-owner-v1",
            "spec": spec.record(),
            "unit": spec.unit,
            "started": started,
            "deadline": deadline,
            "parent_pid": os.getpid(),
        }
        raw = owned.encoded(request)
        if len(raw) > owned.REQUEST_BYTES:
            raise ValueError("Owner request bound")
        digest = hashlib.sha256(raw).hexdigest()
        files.write(
            "capture-owner-intent.json",
            {
                **request,
                "request_sha256": digest,
                "baseline": baseline,
                "no_retry": True,
            },
        )
        claimed = True
        (spec.root / "owner-control").mkdir(mode=0o700)
        (spec.root / "owner-pycache").mkdir(mode=0o700)
        path = spec.root / "capture-owner-request.json"
        owned.write_request(path, raw)
        remaining(cutoff)
        child = starter.start(spec, path, digest)
        # No manager/large-inventory operation can block this wait path.
        child_code = child.wait(max(0.001, cutoff - clock()))
        child_reaped = True
        if clock() >= cutoff:
            raise TimeoutError("Controller returned at/after original work cutoff")
        if child_code != 0:
            raise RuntimeError("Owned controller returned a failure")
        child_result = read_record(files, "capture-final.json")
        terminal = read_record(files, "capture-terminal-before-stop.json")
        if (
            child_result.get("status") != "provisional_complete"
            or child_result.get("accepted") is not False
            or child_result.get("spec") != spec.record()
            or child_result.get("unit") != spec.unit
            or child_result.get("cgroup_closed") is not True
            or child_result.get("cleanup_confirmed") is not True
            or child_result.get("first_fault") is not None
            or child_result.get("supplemental") != []
            or terminal.get("unit") != spec.unit
            or terminal.get("closed") is not True
        ):
            raise ValueError("Controller completion is not an exact provisional join")
        bind(terminal_snapshot(terminal.get("snapshot")))
        assert invocation is not None and group is not None
        if child_result.get("invocation_id") != invocation or child_result.get("cgroup") != group:
            raise ValueError("Controller terminal identity differs")
        joined = owned.join_report(plan, files, invocation, group, started, deadline)
        if joined != child_result.get("report_join") or joined != terminal.get("report_join"):
            raise ValueError("Controller report bytes differ from retained terminal joins")
        successful_child = True
    except BaseException as operation_error:
        fault("owner", operation_error)
    finally:
        if child is not None and not child_reaped:
            try:
                child.kill()  # Owned Popen handle only; no caller-selected PID/group.
            except BaseException as kill_error:
                fault("controller_kill", kill_error)
            try:
                child_code = child.wait(remaining())
                child_reaped = True
            except BaseException as reap_error:
                fault("controller_reap", reap_error)

    if not claimed:
        return {
            "status": "incomplete",
            "accepted": False,
            "intent_acknowledged": False,
            "named_ownership_released": False,
            "first_fault": None if first is None else asdict(first),
            "supplemental": [asdict(item) for item in supplemental],
            "no_retry": True,
        }
    assert plan is not None
    # Reconcile the predetermined name even when submission acknowledgement was
    # lost. Absence without an earlier terminal binding is never proof of closure.
    try:
        sent_term = sent_kill = False
        for _ in range(8):
            observed = manager.snapshot(plan, remaining())
            if (
                latest is not None
                and closed
                and confirms_empty_unit_cleanup(plan, latest, observed)
            ):
                stopped = True
                break
            if observed.properties.get("LoadState") == "not-found":
                pause(min(2.0, remaining()))
                continue
            bind(observed)
            if closed:
                break
            assert invocation is not None
            if not sent_term:
                manager.signal(plan, invocation, "SIGTERM", remaining())
                sent_term = True
                pause(min(2.0, remaining()))
            elif not sent_kill:
                manager.signal(plan, invocation, "SIGKILL", remaining())
                sent_kill = True
            else:
                pause(min(1.0, remaining()))
        if not closed:
            raise TimeoutError("Named capture closure remains unknown; claim retained")
    except BaseException as reconcile_error:
        fault("owner_reconcile", reconcile_error)
    try:
        remaining()
        files.write(
            "capture-owner-terminal.json",
            {
                "unit": spec.unit,
                "invocation_id": invocation,
                "cgroup": group,
                "snapshot": None if latest is None else asdict(latest),
                "closed": closed,
                "child_reaped": child_reaped,
                "child_code": child_code,
                "first_fault": None if first is None else asdict(first),
                "supplemental": [asdict(item) for item in supplemental],
            },
        )
        terminal_saved = True
    except BaseException as terminal_error:
        fault("owner_terminal", terminal_error)
    if closed and not stopped and terminal_saved and invocation is not None and latest is not None:
        try:
            manager.stop(plan, invocation, remaining())
            after = manager.snapshot(plan, remaining())
            if not confirms_empty_unit_cleanup(plan, latest, after):
                raise ValueError("Owner stop did not preserve empty invocation")
            stopped = True
        except BaseException as stop_error:
            fault("owner_stop", stop_error)
    result: dict[str, object] = {
        "status": "provisional_complete"
        if successful_child and child_reaped and closed and stopped and first is None
        else "incomplete",
        "accepted": False,
        "unit": spec.unit,
        "started": started,
        "deadline": deadline,
        "child_reaped": child_reaped,
        "child_code": child_code,
        "controller_descendants_closed": None,
        "invocation_id": invocation,
        "cgroup": group,
        "cgroup_closed": closed,
        "cleanup_confirmed": stopped,
        "terminal_saved": terminal_saved,
        "named_ownership_released": False,
        "external_ledger_closure_required": True,
        "cgroup_cpu_ns": None if latest is None else latest.cpu_ns,
        "first_fault": None if first is None else asdict(first),
        "supplemental": [asdict(item) for item in supplemental],
        "no_retry": True,
    }
    try:
        remaining()
        result["parent_cli_delta_before_final"] = owned._usage_delta(baseline, sample_usage())
        result["scopes_not_added"] = True
        files.write("capture-owner-final.json", result)
        remaining()
    except BaseException as final_error:
        result["status"] = "incomplete"
        result["final_receipt_error"] = asdict(Fault.capture("owner_final", final_error))
    return result


def run_capture(spec: owned.CaptureSpec) -> dict[str, object]:
    return watch(
        spec, Controller(), Systemd(spec.root / "owner-control"), owned.CaptureFiles(spec.root)
    )


def controller_entry(path: Path, digest: str) -> int:
    raw = private_bytes(path, owned.REQUEST_BYTES)
    if hashlib.sha256(raw).hexdigest() != owned._digest(digest):
        raise ValueError("Owner request bytes differ")
    value = owned.decoded(raw, owned.REQUEST_BYTES)
    if (
        set(value) != {"schema", "spec", "unit", "started", "deadline", "parent_pid"}
        or value["schema"] != "d1-capture-owner-v1"
    ):
        raise ValueError("Exact fixed owner request required")
    spec = owned._spec(value["spec"])
    started, deadline, parent = value["started"], value["deadline"], value["parent_pid"]
    if (
        type(started) is not float
        or not math.isfinite(started)
        or started < 0
        or type(deadline) is not float
        or deadline != started + 300.0
        or type(parent) is not int
        or parent <= 1
        or os.getppid() != parent
        or value["unit"] != spec.unit
        or path != spec.root / "capture-owner-request.json"
        or Path(__file__).resolve() != spec.checkout / "scripts/d1_capture_owner.py"
        or sys.flags.isolated != 1
        or sys.flags.dont_write_bytecode != 1
        or sys.pycache_prefix != str(spec.root / "owner-pycache")
        or not started <= time.monotonic() < started + owned.WORK_SECONDS
    ):
        raise ValueError("Original owner/source/startup/window binding differs")
    result = owned.execute(
        spec, Systemd(spec.control_root), owned.CaptureFiles(spec.root), original_start=started
    )
    return 0 if result.get("status") == "provisional_complete" else 1


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] != "controller":
        raise ValueError("Only the source-owned controller child entry exists")
    return controller_entry(Path(sys.argv[2]), sys.argv[3])


if __name__ == "__main__":
    raise SystemExit(main())
