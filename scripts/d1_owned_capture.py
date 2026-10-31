"""Disabled, fixed D1 capture lifecycle; no scientific or activation authority.

The outer invocation and protected runtime remain independently admitted. The
standard capture controller is reused unchanged inside one named service.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

# Only the direct script bootstrap needs this fixed source-owned import root.
# Ordinary imports preserve lookup order; no plan path or checkout/src is added.
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import d1_bootstrap_control as capture
from scripts.grid_q1_supervisor import (
    CommandFailure,
    Fault,
    Files,
    Plan,
    Snapshot,
    Supervisor,
    Systemd,
    confirms_empty_unit_cleanup,
    private_bytes,
)

ENABLED = False
REQUEST_BYTES = 16 * 1024
REPORT_BYTES = 64 * 1024
PROFILE = {
    "runtime_seconds": 240,
    "start_timeout_seconds": 5,
    "stop_timeout_seconds": 5,
    "cpu_quota_percent": 50,
    "quota_period_us": 100_000,
    "cpu_watch_ns": 120_000_000_000,
    "poll_seconds": 4,
    "observations": 60,
    "command_seconds": 5,
    "term_grace_seconds": 2,
    "terminal_seconds": 300,
    "service_file_bytes": 1024 * 1024,
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def _pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise ValueError("Duplicate record field")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("Nonfinite JSON constant")


def decoded(raw: bytes, limit: int) -> dict[str, object]:
    if type(raw) is not bytes or not 0 < len(raw) <= limit:
        raise ValueError("Exact bounded record bytes required")
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if type(value) is not dict or raw != encoded(value):
        raise ValueError("Exact canonical ASCII object plus LF required")
    return value


def _digest(value: object, length: int = 64) -> str:
    if type(value) is not str or len(value) != length or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("Exact lowercase digest required")
    return value


def _path(value: object) -> Path:
    if type(value) is not str or len(value) > 4096:
        raise ValueError("Exact bounded path string required")
    result = Path(value)
    if not result.is_absolute() or str(result) != value or ".." in result.parts:
        raise ValueError("Canonical absolute path required")
    return result


@dataclass(frozen=True, slots=True)
class CaptureSpec:
    root: Path
    checkout: Path
    interpreter: Path
    protected_plan: Path
    protected_plan_sha256: str
    source_commit: str
    admission_sha256: str
    adapter_sha256: str
    controller_sha256: str
    bootstrap_sha256: str

    def record(self) -> dict[str, object]:
        return {name: str(value) if isinstance(value, Path) else value
                for name, value in vars_from_spec(self).items()}

    def validate(self) -> None:
        for path in (self.root, self.checkout, self.interpreter, self.protected_plan):
            if type(path) is not type(Path()) or _path(str(path)) != path:
                raise ValueError("Exact path objects required")
        for digest in (self.protected_plan_sha256, self.admission_sha256, self.adapter_sha256,
                       self.controller_sha256, self.bootstrap_sha256):
            _digest(digest)
        _digest(self.source_commit, 40)
        if self.root == self.checkout or self.root.is_relative_to(self.checkout):
            raise ValueError("Owned output must be outside checkout")

    @property
    def control_root(self) -> Path:
        return self.root.with_name(self.root.name + "-control")

    @property
    def unit(self) -> str:
        key = f"{self.root}:{self.admission_sha256}".encode()
        return "d1-capture-" + hashlib.sha256(key).hexdigest()[:24] + ".service"


def vars_from_spec(spec: CaptureSpec) -> dict[str, object]:
    return {"root": spec.root, "checkout": spec.checkout, "interpreter": spec.interpreter,
            "protected_plan": spec.protected_plan, "protected_plan_sha256": spec.protected_plan_sha256,
            "source_commit": spec.source_commit, "admission_sha256": spec.admission_sha256,
            "adapter_sha256": spec.adapter_sha256, "controller_sha256": spec.controller_sha256,
            "bootstrap_sha256": spec.bootstrap_sha256}


def _spec(value: object) -> CaptureSpec:
    if type(value) is not dict or set(value) != {
        "root", "checkout", "interpreter", "protected_plan", "protected_plan_sha256",
        "source_commit", "admission_sha256", "adapter_sha256", "controller_sha256", "bootstrap_sha256",
    }:
        raise ValueError("Exact capture binding fields required")
    result = CaptureSpec(
        _path(value["root"]), _path(value["checkout"]), _path(value["interpreter"]),
        _path(value["protected_plan"]), _digest(value["protected_plan_sha256"]),
        _digest(value["source_commit"], 40), _digest(value["admission_sha256"]),
        _digest(value["adapter_sha256"]), _digest(value["controller_sha256"]),
        _digest(value["bootstrap_sha256"]),
    )
    result.validate()
    return result


@dataclass(frozen=True, kw_only=True)
class CapturePlan(Plan):
    spec: CaptureSpec
    request_sha256: str

    def __post_init__(self) -> None:
        super().__post_init__()
        self.spec.validate()
        _digest(self.request_sha256)
        if (self.root != self.spec.root or self.admission_sha256 != self.spec.admission_sha256
                or self.controller_sha256 != self.spec.adapter_sha256
                or any(getattr(self, name) != value for name, value in PROFILE.items())):
            raise ValueError("Fixed capture profile and source binding required")

    @property
    def unit(self) -> str:
        return self.spec.unit

    @property
    def argv(self) -> list[str]:
        return [str(self.spec.interpreter), "-I", "-B", "-X",
                f"pycache_prefix={self.root / 'service-pycache'}",
                str(self.spec.checkout / "scripts/d1_owned_capture.py"), "service",
                str(self.root / "capture-request.json"), self.request_sha256]


class ReceiptIO(Protocol):
    root: Path
    def write(self, name: str, record: dict[str, object]) -> None: ...
    def read(self, name: str, maximum: int) -> bytes: ...


class CaptureFiles:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.writer = Files(root)

    def write(self, name: str, record: dict[str, object]) -> None:
        # Existing exclusive/fsync/dir-fsync writer; GRID result validation is unused.
        self.writer.write(name, record)

    def read(self, name: str, maximum: int) -> bytes:
        return private_bytes(self.root / name, maximum)


def preflight(spec: CaptureSpec) -> None:
    """One additional full validation, after the outer intent and baseline."""
    plan = capture.read_plan(spec.protected_plan, spec.protected_plan_sha256)
    hashes = capture.validate_plan(plan)
    expected = {
        "source_commit": spec.source_commit, "checkout": str(spec.checkout),
        "controller_interpreter": str(spec.interpreter),
        "controller": str(spec.checkout / "scripts/d1_bootstrap_control.py"),
        "bootstrap": str(spec.checkout / "tests/d1_bootstrap.py"),
    }
    if any(plan.get(key) != value for key, value in expected.items()):
        raise ValueError("Capture source/controller/bootstrap/plan join differs")
    for path, digest in (
        (spec.checkout / "scripts/d1_owned_capture.py", spec.adapter_sha256),
        (spec.checkout / "scripts/d1_bootstrap_control.py", spec.controller_sha256),
        (spec.checkout / "tests/d1_bootstrap.py", spec.bootstrap_sha256),
    ):
        if hashes.get(str(path)) != digest:
            raise ValueError("Actual protected callable source digest differs")
    if any(spec.root.is_relative_to(Path(plan[key])) for key in ("venv_root", "stdlib")):
        raise ValueError("Capture output must be outside protected runtime")


def usage() -> dict[str, float]:
    parent, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"parent_cpu_seconds": parent.ru_utime + parent.ru_stime,
            "waited_cli_cpu_seconds": children.ru_utime + children.ru_stime}


def _usage_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    keys = {"parent_cpu_seconds", "waited_cli_cpu_seconds"}
    if set(before) != keys or set(after) != keys:
        raise ValueError("Accounting scope differs")
    result = {key: after[key] - before[key] for key in keys}
    if any(not math.isfinite(value) or value < 0 for value in result.values()):
        raise ValueError("Accounting decreased or unavailable")
    return result


def _bootstrap_report(spec: CaptureSpec, raw: bytes) -> None:
    if not 0 < len(raw) <= capture.LOG_LIMIT:
        raise ValueError("Bounded bootstrap report required")
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    expected = {"kind": "d1-capture-only", "source_commit": spec.source_commit, "owners": 13,
                "original_methods": 22, "emitter": "math.exp", "primitive_calls_permitted": False,
                "retention_activated": False}
    if encoded(value) != encoded(expected):
        raise ValueError("Exact zero-primitive capture report differs")


class ServiceReceiptFailure(RuntimeError):
    def __init__(self, first: Fault, supplemental: Fault) -> None:
        self.first = first
        self.supplemental = supplemental
        super().__init__(f"{first.stage}:{first.kind}:{first.detail}; {supplemental.stage}:{supplemental.kind}")


def service_identity(unit: str) -> tuple[str, str]:
    """Observe only this service's systemd identity; never accept a caller flag."""
    invocation = _digest(os.environ.get("INVOCATION_ID"), 32)
    with Path("/proc/self/cgroup").open("rb") as stream:
        group_raw = stream.read(4097)
    if len(group_raw) > 4096 or not group_raw.startswith(b"0::/") or group_raw.count(b"\n") != 1:
        raise ValueError("One bounded unified service cgroup required")
    group = group_raw[3:-1].decode("ascii")
    if not group.endswith("/" + unit) or ".." in Path(group).parts:
        raise ValueError("Actual service cgroup/unit join differs")
    return invocation, group


def service_entry(request_path: Path, expected_sha256: str) -> int:
    """Fixed service role only; CLI stays disabled until reviewed source activation."""
    raw = private_bytes(request_path, REQUEST_BYTES)
    if hashlib.sha256(raw).hexdigest() != _digest(expected_sha256):
        raise ValueError("Actual service request digest differs")
    request = decoded(raw, REQUEST_BYTES)
    if set(request) != {"schema", "spec", "unit", "started", "deadline"} or request["schema"] != "d1-capture-request-v1":
        raise ValueError("Exact service request required")
    spec = _spec(request["spec"])
    if request_path != spec.root / "capture-request.json" or request["unit"] != spec.unit:
        raise ValueError("Fixed request root and unit differ")
    started, deadline = request["started"], request["deadline"]
    if (type(started) is not float or type(deadline) is not float
            or not math.isfinite(started) or not math.isfinite(deadline)
            or deadline - started != 300.0):
        raise ValueError("Original absolute deadline required")
    if (sys.flags.isolated != 1 or sys.flags.dont_write_bytecode != 1
            or sys.pycache_prefix != str(spec.root / "service-pycache")):
        raise ValueError("Fixed isolated service startup differs")
    if next((spec.root / "service-pycache").iterdir(), None) is not None:
        raise ValueError("Fresh service cache is not empty")
    invocation, group = service_identity(spec.unit)
    result: capture.LaunchResult | None = None
    primary: Fault | None = None
    report_sha: str | None = None
    report_size: int | None = None
    try:
        if time.monotonic() >= deadline:
            raise TimeoutError("Original capture deadline reached before launch")
        result = capture.launch(spec.protected_plan, spec.protected_plan_sha256, spec.root / "capture")
        if time.monotonic() >= deadline:
            raise TimeoutError("Original capture deadline reached after launch")
        if not result.capture_observed:
            raise ValueError("Inner capture remains incomplete")
        child_raw = private_bytes(spec.root / "capture/child.log", capture.LOG_LIMIT)
        _bootstrap_report(spec, child_raw)
        report_sha, report_size = hashlib.sha256(child_raw).hexdigest(), len(child_raw)
    except BaseException as service_error:
        primary = Fault.capture("service_capture", service_error)
    record: dict[str, object] = {
        "schema": "d1-owned-capture-service-v1", "spec": spec.record(), "unit": spec.unit,
        "invocation_id": invocation, "cgroup": group, "request_sha256": expected_sha256,
        "started": started, "deadline": deadline, "observed_at": time.monotonic(),
        "launch": None if result is None else asdict(result),
        "bootstrap_report_sha256": report_sha, "bootstrap_report_bytes": report_size,
        "first_fault": None if primary is None else asdict(primary),
    }
    try:
        CaptureFiles(spec.root).write("capture-service.json", record)
    except BaseException as receipt_error:
        if primary is None:
            raise
        raise ServiceReceiptFailure(primary, Fault.capture("service_receipt", receipt_error)) from None
    return 0 if primary is None else 1


def join_report(plan: CapturePlan, files: ReceiptIO, invocation: str, cgroup: str,
                started: float, deadline: float) -> dict[str, object]:
    raw = files.read("capture-service.json", REPORT_BYTES)
    # Files.write uses sorted indented JSON, which is bounded and duplicate-checked here.
    if type(raw) is not bytes or not 0 < len(raw) <= REPORT_BYTES:
        raise ValueError("Bounded service report bytes required before parsing")
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if type(value) is not dict or set(value) != {
        "schema", "spec", "unit", "invocation_id", "cgroup", "request_sha256", "started",
        "deadline", "observed_at", "launch", "bootstrap_report_sha256", "bootstrap_report_bytes", "first_fault",
    }:
        raise ValueError("Exact bounded service report shape required")
    expected = {"schema": "d1-owned-capture-service-v1", "spec": plan.spec.record(), "unit": plan.unit,
                "invocation_id": invocation, "cgroup": cgroup, "request_sha256": plan.request_sha256,
                "started": started, "deadline": deadline, "first_fault": None}
    if any(encoded(value[key]) != encoded(item) for key, item in expected.items()):
        raise ValueError("Service report/source/admission/root/invocation join differs")
    observed = value["observed_at"]
    if type(observed) is not float or not started <= observed < deadline:
        raise ValueError("Missing or late capture observation")
    inner = value["launch"]
    keys = {"exit_code", "reaped", "timed_out", "custody_rechecked", "stdout_bytes", "wall_seconds",
            "child_cpu_seconds", "capture_observed", "owned_tree_closed", "captured", "failure"}
    if type(inner) is not dict or set(inner) != keys:
        raise ValueError("Exact inner capture result required")
    for key, item in {"exit_code": 0, "reaped": True, "timed_out": False, "custody_rechecked": True,
                      "capture_observed": True, "owned_tree_closed": None, "captured": False,
                      "failure": "outer_owned_tree_closure_unproved"}.items():
        if encoded(inner[key]) != encoded(item):
            raise ValueError("Inner observation cannot claim whole-tree acceptance")
    for key, upper in (("wall_seconds", 65.0), ("child_cpu_seconds", 30.0)):
        number = inner[key]
        if type(number) not in (int, float) or not math.isfinite(number) or not 0 <= number <= upper:
            raise ValueError("Inner measured scope missing or outside fixed limits")
    child_raw = files.read("capture/child.log", capture.LOG_LIMIT)
    _bootstrap_report(plan.spec, child_raw)
    if (type(inner["stdout_bytes"]) is not int or inner["stdout_bytes"] != len(child_raw)
            or type(value["bootstrap_report_bytes"]) is not int or value["bootstrap_report_bytes"] != len(child_raw)
            or value["bootstrap_report_sha256"] != hashlib.sha256(child_raw).hexdigest()):
        raise ValueError("Exact retained bootstrap bytes differ")
    return {"service_sha256": hashlib.sha256(raw).hexdigest(), "service_bytes": len(raw),
            "bootstrap_sha256": hashlib.sha256(child_raw).hexdigest(), "bootstrap_bytes": len(child_raw),
            "inner_measured_scope": inner}


def execute(spec: CaptureSpec, supervisor: Supervisor, files: ReceiptIO,
            clock: Callable[[], float] = time.monotonic, pause: Callable[[float], None] = time.sleep,
            sample_usage: Callable[[], dict[str, float]] = usage) -> dict[str, object]:
    """One owned attempt; returned success is provisional pending external ledger."""
    started = clock()
    baseline = sample_usage()
    deadline = started + 300.0
    first: Fault | None = None
    supplemental: list[Fault] = []
    plan: CapturePlan | None = None
    latest: Snapshot | None = None
    after_snapshot: Snapshot | None = None
    invocation: str | None = None
    group: str | None = None
    dispatch = claimed = intent_attempted = closed = stopped = terminal_saved = False
    joined: dict[str, object] | None = None

    def fault(stage: str, error: BaseException) -> None:
        nonlocal first
        original = error.primary if isinstance(error, CommandFailure) else error
        item = Fault.capture(stage, original)
        if first is None:
            first = item
        else:
            supplemental.append(item)
        if isinstance(error, CommandFailure):
            supplemental.extend(error.supplemental)

    def remaining(end: float = deadline) -> float:
        value = min(5.0, end - clock())
        if value <= 0:
            raise TimeoutError("Original absolute capture deadline")
        return value

    def bind(snapshot: Snapshot) -> None:
        nonlocal latest, invocation, group, closed
        assert plan is not None
        snapshot.bind(plan, invocation)
        if group is None:
            if not snapshot.cgroup or snapshot.populated is None:
                raise ValueError("Actual populated-state/group binding required before disappearance")
            group = snapshot.cgroup
        elif snapshot.cgroup and snapshot.cgroup != group:
            raise ValueError("Bound service group changed")
        if latest is not None and snapshot.cpu_ns < latest.cpu_ns:
            raise ValueError("Cgroup accounting decreased")
        invocation = snapshot.invocation
        latest = snapshot
        closed = snapshot.terminal and snapshot.populated is not True

    try:
        spec.validate()
        if files.root != spec.root:
            raise ValueError("Receipt root differs from intended root")
        # Validate the existing private run root before writing into it; no plan read yet.
        request = {"schema": "d1-capture-request-v1", "spec": spec.record(), "unit": spec.unit,
                   "started": started, "deadline": deadline}
        request_raw = encoded(request)
        if len(request_raw) > REQUEST_BYTES:
            raise ValueError("Request byte bound")
        plan = CapturePlan(root=spec.root, admission_sha256=spec.admission_sha256,
                           controller_sha256=spec.adapter_sha256, spec=spec,
                           request_sha256=hashlib.sha256(request_raw).hexdigest(),
                           runtime_seconds=240, start_timeout_seconds=5, stop_timeout_seconds=5,
                           cpu_quota_percent=50, quota_period_us=100_000,
                           cpu_watch_ns=120_000_000_000, poll_seconds=4, observations=60,
                           command_seconds=5, term_grace_seconds=2, terminal_seconds=300,
                           service_file_bytes=1024 * 1024)
        intent_attempted = True
        files.write("capture-intent.json", {"spec": spec.record(), "unit": spec.unit,
                    "started": started, "deadline": deadline, "cpu_baseline": baseline,
                    "no_retry": True, "profile": PROFILE})
        claimed = True
        spec.control_root.mkdir(mode=0o700)
        (spec.root / "service-pycache").mkdir(mode=0o700)
        # Canonical request bytes are fixed; the standard indented writer is not used here.
        request_path = spec.root / "capture-request.json"
        fd = os.open(request_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(request_raw); stream.flush(); os.fsync(stream.fileno())
        directory = os.open(spec.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        preflight(spec)
        remaining(started + 245.0)
        initial = supervisor.snapshot(plan, remaining())
        if initial.properties.get("LoadState") != "not-found":
            raise ValueError("Intended unit already exists; no submission")
        remaining(started + 245.0)
        dispatch = True
        supervisor.submit(plan, remaining())
        for index in range(60):
            bind(supervisor.snapshot(plan, remaining(started + 245.0)))
            assert latest is not None
            files.write(f"capture-observation-{index:02d}.json", {
                "unit": plan.unit, "invocation_id": invocation, "cgroup": group,
                "snapshot": asdict(latest), "elapsed": clock() - started,
                "parent_cli_delta": _usage_delta(baseline, sample_usage()),
                "cgroup_cpu_ns": latest.cpu_ns, "scopes_not_added": True,
            })
            if latest.cpu_ns >= plan.cpu_watch_ns:
                raise RuntimeError("Cgroup CPU watch reached")
            if closed:
                break
            pause(min(4.0, max(0.0, started + 245.0 - clock())))
        if not closed or latest is None:
            raise TimeoutError("Observation limit exhausted")
        if (latest.properties.get("Result") != "success"
                or latest.properties.get("ExecMainCode") != "1"
                or latest.properties.get("ExecMainStatus") != "0"):
            raise ValueError("Named capture service did not exit successfully")
        assert invocation is not None and group is not None
        joined = join_report(plan, files, invocation, group, started, deadline)
        if next((spec.root / "service-pycache").iterdir(), None) is not None:
            raise ValueError("Service cache changed")
        remaining()
    except BaseException as attempt_error:
        fault("attempt", attempt_error)
        if not claimed:
            # No later receipt may use an unvalidated root or uncertain claim.
            # An intent callback may have partially written before raising.
            if intent_attempted and isinstance(attempt_error, FileExistsError):
                reason = "exclusive_intent_exists"
            elif intent_attempted:
                reason = "intent_acknowledgement_unknown"
            else:
                reason = "pre_intent_validation_failed"
            return {"status": "incomplete", "accepted": False, "reason": reason,
                    "intent_attempted": intent_attempted, "intent_acknowledged": False,
                    "dispatch_attempted": False, "external_ledger_closure_required": True,
                    "first_fault": None if first is None else asdict(first),
                    "supplemental": [asdict(item) for item in supplemental], "no_retry": True}
    if dispatch and not closed and plan is not None:
        try:
            bind(supervisor.snapshot(plan, remaining()))
            if not closed:
                assert invocation is not None
                supervisor.signal(plan, invocation, "SIGTERM", remaining())
                pause(min(2.0, remaining()))
                bind(supervisor.snapshot(plan, remaining()))
                if not closed:
                    supervisor.signal(plan, invocation, "SIGKILL", remaining())
                for _ in range(4):
                    if closed:
                        break
                    bind(supervisor.snapshot(plan, remaining()))
                    if not closed:
                        pause(min(1.0, remaining()))
                if not closed:
                    raise TimeoutError("Named unit closure remains unknown")
        except BaseException as cleanup_error:
            fault("termination", cleanup_error)
    try:
        remaining()
        files.write("capture-terminal-before-stop.json", {
            "unit": spec.unit, "invocation_id": invocation, "cgroup": group,
            "snapshot": None if latest is None else asdict(latest), "closed": closed,
            "first_fault": None if first is None else asdict(first),
            "supplemental": [asdict(item) for item in supplemental], "report_join": joined,
            "parent_cli_delta": _usage_delta(baseline, sample_usage()),
            "cgroup_cpu_ns": None if latest is None else latest.cpu_ns,
            "scopes_not_added": True,
        })
        terminal_saved = True
    except BaseException as terminal_error:
        fault("terminal_receipt", terminal_error)
    if closed and terminal_saved and plan is not None and invocation is not None and latest is not None:
        try:
            supervisor.stop(plan, invocation, remaining())
            after = supervisor.snapshot(plan, remaining())
            after_snapshot = after
            if (after.invocation not in ("", invocation) or after.cgroup not in ("", group)
                    or after.properties.get("Id") not in (None, plan.unit)):
                raise ValueError("Post-stop identity changed")
            if after.invocation and after.cpu_ns < latest.cpu_ns:
                raise ValueError("Post-stop CPU accounting decreased")
            if not confirms_empty_unit_cleanup(plan, latest, after):
                raise ValueError("Empty named-unit cleanup not confirmed")
            stopped = True
        except BaseException as stop_error:
            fault("stop", stop_error)
    final_usage: dict[str, float] | None = None
    try:
        final_usage = _usage_delta(baseline, sample_usage())
    except BaseException as accounting_error:
        fault("final_accounting", accounting_error)
    record: dict[str, object] = {
        "status": "provisional_complete" if first is None and not supplemental and closed and stopped and joined is not None else "incomplete",
        "accepted": False, "external_ledger_closure_required": True,
        "spec": spec.record(), "unit": spec.unit, "invocation_id": invocation, "cgroup": group,
        "dispatch_attempted": dispatch, "cgroup_closed": closed, "cleanup_confirmed": stopped,
        "terminal_receipt_saved": terminal_saved, "report_join": joined,
        "cleanup_snapshot": None if after_snapshot is None else asdict(after_snapshot),
        "terminal_cgroup_cpu_ns": None if latest is None else latest.cpu_ns,
        "parent_cli_delta_before_final_receipt": final_usage, "scopes_not_added": True,
        "first_fault": None if first is None else asdict(first),
        "supplemental": [asdict(item) for item in supplemental],
        "elapsed_before_final_receipt": clock() - started, "no_retry": True,
    }
    try:
        remaining()
        files.write("capture-final.json", record)
        remaining()
    except BaseException as final_error:
        record["status"] = "incomplete"
        record["final_receipt_error"] = asdict(Fault.capture("final_receipt", final_error))
    return record


def run_owned(spec: CaptureSpec) -> dict[str, object]:
    """Fixed concrete API for a separately admitted outer invocation, not a CLI."""
    return execute(spec, Systemd(spec.control_root), CaptureFiles(spec.root))


def main() -> int:
    if not ENABLED:
        return 64
    if len(sys.argv) != 4 or sys.argv[1] != "service":
        raise ValueError("Only fixed capture service entry is supported")
    return service_entry(Path(sys.argv[2]), sys.argv[3])


if __name__ == "__main__":
    raise SystemExit(main())
