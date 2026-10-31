"""Disabled fixed systemd fixtures and sequential GRID-Q1 qualification barriers."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import select
import signal
import stat
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts import grid_q1_supervisor as control

ENABLED = False
if __name__ == "__main__" and not ENABLED:
    raise SystemExit("Disabled pending combined source/owner/lease admission")

SOURCE = "cec936a2a5a6534861eb9183861c4d6fcf931f67"
KINDS = ("normal", "nonzero", "timeout")
RECEIPT_BYTES = 16 * 1024
MAX_RECEIPTS = 16
CONTRACT = {
    "lease_seconds": 2400,
    "whole_host_cpu_upper_seconds": 33600,
    "client_max_cpus": 10,
    "server_max_cpus": 4,
    "logical_bytes": 104 * 1024**2,
    "start_free_bytes": 21592276992,
    "later_free_bytes": 20 * 1024**3,
}
QUALIFICATION = {
    "runtime_seconds": 8,
    "start_timeout_seconds": 3,
    "stop_timeout_seconds": 2,
    "cpu_quota_percent": 50,
    "quota_period_us": 100000,
    "cpu_watch_ns": 7000000000,
    "poll_seconds": 1,
    "observations": 8,
    "command_seconds": 1,
    "term_grace_seconds": 1,
    "terminal_seconds": 15,
    "service_file_bytes": 1024**2,
}


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("Expected object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Expected string key")
        result[key] = item
    return result


def string(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected string")
    return value


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected integer")
    return value


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def activate(raw: bytes) -> bytes:
    marker = b"\nENABLED = False\n"
    if raw.count(marker) != 1:
        raise ValueError("Exactly one disabled entry assignment")
    return raw.replace(marker, b"\nENABLED = True\n", 1)


def private_path(value: object, directory: bool = False) -> Path:
    path = Path(string(value))
    if not path.is_absolute() or ".." in path.parts or path != path.resolve():
        raise ValueError("Exact normalized private path")
    info = path.lstat()
    expected = 0o700 if directory else 0o600
    kind = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not kind or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != expected:
        raise ValueError("Private ownership/mode")
    if not directory and info.st_nlink != 1:
        raise ValueError("Input alias")
    return path


def read(path: Path, maximum: int = 128 * 1024) -> bytes:
    private_path(str(path))
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Input extent")
    return raw


def pinned(path_value: object, expected: object) -> tuple[Path, bytes]:
    path = private_path(path_value)
    raw = read(path)
    if digest(raw) != string(expected):
        raise ValueError("Input digest")
    return path, raw


def write(root: Path, name: str, value: dict[str, object]) -> str:
    private_path(str(root), True)
    if "/" in name or not name.endswith(".json"):
        raise ValueError("Fixed receipt name")
    if len(tuple(root.glob("*.json"))) >= MAX_RECEIPTS:
        raise ValueError("Qualification receipt count")
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(raw) > RECEIPT_BYTES:
        raise ValueError("Qualification receipt extent")
    fd = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return digest(raw)


def owner_check(data: dict[str, object]) -> None:
    owner_ref = mapping(data["owner"])
    _, raw = pinned(owner_ref["path"], owner_ref["sha256"])
    owner = mapping(json.loads(raw))
    if (
        owner.get("approved") is not True
        or data.get("owner_admitted") is not True
        or owner.get("combined_id") != data.get("combined_id")
        or owner.get("source") != SOURCE
        or data.get("source") != SOURCE
        or owner.get("contract") != CONTRACT
        or data.get("contract") != CONTRACT
        or owner.get("historical_costs") != "unknowns-preserved-no-reset"
    ):
        raise ValueError("New combined owner authority required")
    adapter = mapping(data.get("adapter"))
    if owner.get("adapter_sha256") != adapter.get("sha256"):
        raise ValueError("Owner-bound adapter source")
    if data.get("kind") in KINDS:
        qualified = mapping(owner.get("qualification_roots"))
        if qualified.get(string(data["kind"])) != [data.get("root"), data.get("control_root")]:
            raise ValueError("Owner-bound qualification roots")
        if owner.get("fixture_active_sha256") != data.get("fixture_active_sha256"):
            raise ValueError("Owner-bound fixture source")
    else:
        grid = mapping(data.get("grid"))
        if (
            owner.get("combined_control_root") != data.get("control_root")
            or owner.get("grid_run_root") != grid.get("root")
            or owner.get("grid_control_root") != grid.get("control_root")
            or owner.get("grid_template_sha256") != grid.get("template_sha256")
            or owner.get("fixture_disabled_sha256") != data.get("fixture_disabled_sha256")
        ):
            raise ValueError("Owner-bound combined plan")
        for field in ("leases", "output_pools", "engineering", "operator"):
            if mapping(data.get(field)) != mapping(owner.get(field)):
                raise ValueError("Owner-bound combined " + field)
        leases = mapping(data["leases"])
        if set(leases) != {"client", "server"}:
            raise ValueError("Exact host lease references")
        lease_paths: set[Path] = set()
        control_root = private_path(data["control_root"], True)
        for reference in leases.values():
            ref = mapping(reference)
            path = Path(string(ref.get("path")))
            if (
                not path.is_absolute()
                or path != path.resolve()
                or path.parent != control_root
                or path in lease_paths
                or re.fullmatch(r"[0-9a-f]{64}", string(ref.get("sha256"))) is None
            ):
                raise ValueError("Owner-bound private lease observation")
            lease_paths.add(path)
    roots = data.get("owned_roots")
    if not isinstance(roots, list) or roots != owner.get("owned_roots"):
        raise ValueError("Exact owner/root binding")
    if len(roots) != len(set(string(root) for root in roots)):
        raise ValueError("Duplicate owned root")
    if any(Path(string(root)).name == "qualification-run-q1-cec936a2-once" for root in roots):
        raise ValueError("Original incomplete authority cannot be reused")


def load(path: Path, expected: str) -> dict[str, object]:
    _, raw = pinned(str(path), expected)
    data = mapping(json.loads(raw))
    owner_check(data)
    return data


def import_core(data: dict[str, object]) -> None:
    ref = mapping(data["adapter"])
    path, _ = pinned(ref["path"], ref["sha256"])
    if path.name != "grid_q1_supervisor.py" or path.parent.name != "scripts":
        raise ValueError("Exact exported scripts layout")
    sys.path.insert(0, str(path.parent.parent))
    from scripts import grid_q1_supervisor as core

    if (
        core.__file__ is None
        or Path(core.__file__).resolve() != path
        or digest(read(path)) != ref["sha256"]
    ):
        raise ValueError("Imported core identity differs from pinned export")


def roots(data: dict[str, object]) -> tuple[Path, Path]:
    inner = private_path(data["root"], True)
    outer = private_path(data["control_root"], True)
    if outer != inner.with_name(inner.name + "-control"):
        raise ValueError("Bound sibling control directory")
    owned = data["owned_roots"]
    if not isinstance(owned, list) or str(inner) not in owned or str(outer) not in owned:
        raise ValueError("Undeclared root")
    return inner, outer


def qualification_plan(data: dict[str, object], spec_sha: str) -> control.Plan:
    import_core(data)
    from scripts import grid_q1_supervisor as core

    inner, _ = roots(data)
    if data.get("kind") not in KINDS or data.get("profile") != QUALIFICATION:
        raise ValueError("Fixed qualification profile")
    return core.Plan(
        inner,
        spec_sha,
        string(data["fixture_active_sha256"]),
        8,
        3,
        2,
        50,
        100000,
        7000000000,
        1,
        8,
        1,
        1,
        15,
        1024**2,
    )


def backend_for(data: dict[str, object], plan: control.Plan) -> control.Systemd:
    from scripts import grid_q1_supervisor as core

    _, outer = roots(data)
    backend = core.Systemd(outer)
    logs = sorted(outer.glob("supervisor-command-*.log"))
    if [p.name for p in logs] != [
        f"supervisor-command-{i:03d}.log" for i in range(1, len(logs) + 1)
    ]:
        raise ValueError("Command log prefix")
    backend.commands = len(logs)
    bound_path = outer / "bound.json"
    if bound_path.exists():
        bound = mapping(json.loads(read(bound_path)))
        if bound.get("unit") != plan.unit:
            raise ValueError("Bound unit changed")
        backend.groups[plan.unit] = string(bound["cgroup"])
        backend.quotas[plan.unit] = (
            string(bound["cpu_max"]),
            string(bound["cpu_max_burst"]),
        )
    return backend


def record_fault(outer: Path, stage: str, error: BaseException) -> None:
    # Core import occurs only after its exact exported path/hash was checked.
    core = sys.modules.get("scripts.grid_q1_supervisor")
    extras: list[dict[str, object]] = []
    if core is not None:
        from scripts import grid_q1_supervisor as checked_core
    if core is not None and isinstance(error, checked_core.CommandFailure):
        extras = [
            {"stage": f.stage, "kind": f.kind, "detail": f.detail} for f in error.supplemental
        ]
        error = error.primary
    import_core_error = type(error).__name__
    detail = str(error)[:512]
    name = "first-fault.json"
    if (outer / name).exists():
        name = f"cleanup-fault-{len(tuple(outer.glob('cleanup-fault-*.json'))):02d}.json"
    write(
        outer,
        name,
        {"stage": stage, "kind": import_core_error, "detail": detail, "supplemental": extras},
    )


def worker(data: dict[str, object], spec_sha: str) -> int:
    inner, _ = roots(data)
    if digest(read(Path(__file__).resolve())) != data.get("fixture_active_sha256"):
        raise ValueError("Fixture source identity")
    kind = string(data["kind"])
    if kind not in KINDS:
        raise ValueError("Fixed fixture kind")
    invocation = os.environ.get("INVOCATION_ID", "")
    if re.fullmatch(r"[0-9a-f]{32}", invocation) is None:
        raise ValueError("Manager invocation identity")
    fifo = inner / "release.fifo"
    os.mkfifo(fifo, 0o600)
    fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
    descendant: int | None = None
    if kind == "timeout":
        ready_r, ready_w = os.pipe()
        descendant = os.fork()
        if descendant == 0:
            os.close(ready_r)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            os.write(ready_w, b"R")
            os.close(ready_w)
            while True:
                signal.pause()
        os.close(ready_w)
        if not select.select([ready_r], [], [], 2)[0] or os.read(ready_r, 1) != b"R":
            raise TimeoutError("Descendant readiness")
        os.close(ready_r)
    token: dict[str, object] = {"spec_sha256": spec_sha, "invocation_id": invocation, "kind": kind}
    write(
        inner,
        "worker-ready.json",
        {
            **token,
            "pid": os.getpid(),
            "descendant_pid": descendant,
            "fixture_sha256": data["fixture_active_sha256"],
        },
    )
    try:
        if not select.select([fd], [], [], 6)[0]:
            raise TimeoutError("Release handshake")
        raw = os.read(fd, 513)
        if len(raw) > 512 or mapping(json.loads(raw)) != token:
            raise ValueError("Release identity")
    finally:
        os.close(fd)
    write(inner, "worker-released.json", token)
    if kind == "timeout":
        while True:
            signal.pause()
    return 0 if kind == "normal" else 7


def start(data: dict[str, object], spec_sha: str) -> None:
    plan = qualification_plan(data, spec_sha)
    inner, outer = roots(data)
    if (outer / "first-fault.json").exists():
        raise ValueError("Prior qualification fault")
    if any(
        os.path.lexists(inner / name)
        for name in ("worker-ready.json", "worker-released.json", "release.fifo")
    ):
        raise ValueError("Fixture already attempted")
    write(
        outer,
        "intent.json",
        {
            "unit": plan.unit,
            "root": str(inner),
            "control_root": str(outer),
            "spec_sha256": spec_sha,
            "source": SOURCE,
            "combined_id": data["combined_id"],
            "monotonic_start": time.monotonic(),
            "realtime_start_ns": time.time_ns(),
            "no_retry": True,
        },
    )
    if digest(read(inner / "run.py")) != data["fixture_active_sha256"]:
        raise ValueError("Qualification executable bytes changed")
    if os.statvfs(inner).f_bavail * os.statvfs(inner).f_frsize < CONTRACT["start_free_bytes"]:
        raise ValueError("Fresh qualification capacity guard")
    backend = backend_for(data, plan)
    if backend.snapshot(plan, 1).properties.get("LoadState") != "not-found":
        raise ValueError("Unit already exists")
    # submit's exact argv invokes the enabled run.py export, never execute().
    backend.submit(plan, 3)


def ready(data: dict[str, object], spec_sha: str) -> None:
    plan = qualification_plan(data, spec_sha)
    inner, outer = roots(data)
    if (outer / "first-fault.json").exists():
        raise ValueError("Prior qualification fault")
    write(outer, "ready-claim.json", {"spec_sha256": spec_sha, "unit": plan.unit})
    backend = backend_for(data, plan)
    deadline = time.monotonic() + 3
    for _ in range(3):
        left = deadline - time.monotonic()
        if left <= 0:
            break
        snapshot = backend.snapshot(plan, min(1, left))
        snapshot.bind(plan, None)
        if snapshot.populated is True and (inner / "worker-ready.json").exists():
            proof = mapping(json.loads(read(inner / "worker-ready.json")))
            if (
                proof.get("invocation_id") != snapshot.invocation
                or proof.get("spec_sha256") != spec_sha
                or proof.get("kind") != data["kind"]
                or proof.get("fixture_sha256") != data["fixture_active_sha256"]
                or (data["kind"] == "timeout" and type(proof.get("descendant_pid")) is not int)
            ):
                raise ValueError("Ready identity")
            write(
                outer,
                "bound.json",
                {
                    "unit": plan.unit,
                    "invocation_id": snapshot.invocation,
                    "cgroup": snapshot.cgroup,
                    "cpu_max": snapshot.properties["ObservedCPUMax"],
                    "cpu_max_burst": snapshot.properties["ObservedCPUMaxBurst"],
                    "worker_ready_sha256": digest(read(inner / "worker-ready.json")),
                    "spec_sha256": spec_sha,
                    "snapshot": snapshot.properties,
                },
            )
            return
        time.sleep(max(0, min(1, deadline - time.monotonic())))
    raise TimeoutError("Ready/binding deadline")


def release(data: dict[str, object], spec_sha: str) -> None:
    plan = qualification_plan(data, spec_sha)
    inner, outer = roots(data)
    if (outer / "first-fault.json").exists():
        raise ValueError("Prior qualification fault")
    bound = mapping(json.loads(read(outer / "bound.json")))
    ready_raw = read(inner / "worker-ready.json")
    if bound.get("spec_sha256") != spec_sha or bound.get("worker_ready_sha256") != digest(
        ready_raw
    ):
        raise ValueError("Bound ready receipt")
    snapshot = backend_for(data, plan).snapshot(plan, 1)
    snapshot.bind(plan, string(bound["invocation_id"]))
    if snapshot.populated is not True:
        raise ValueError("Fixture no longer waiting")
    token = {
        "spec_sha256": spec_sha,
        "invocation_id": bound["invocation_id"],
        "kind": data["kind"],
    }
    write(outer, "release.json", token)
    fifo = inner / "release.fifo"
    info = fifo.lstat()
    if (
        not stat.S_ISFIFO(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise ValueError("Private release FIFO")
    fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        raw = json.dumps(token, sort_keys=True).encode()
        if len(raw) > 512 or os.write(fd, raw) != len(raw):
            raise OSError("Incomplete release")
    finally:
        os.close(fd)


def expected_terminal(kind: str, properties: dict[str, str]) -> bool:
    if kind == "normal":
        return (
            properties.get("Result"),
            properties.get("ExecMainCode"),
            properties.get("ExecMainStatus"),
        ) == ("success", "1", "0")
    if kind == "nonzero":
        return (
            properties.get("Result"),
            properties.get("ExecMainCode"),
            properties.get("ExecMainStatus"),
        ) == ("exit-code", "1", "7")
    return (
        kind == "timeout"
        and properties.get("Result") == "timeout"
        and properties.get("ExecMainCode") in ("2", "3")
        and properties.get("ExecMainStatus") in ("9", "15")
    )


def finish(data: dict[str, object], spec_sha: str) -> bool:
    """One bounded terminal inspection; never submit again, including lost ack."""
    plan = qualification_plan(data, spec_sha)
    from scripts import grid_q1_supervisor as core

    inner, outer = roots(data)
    write(outer, "finish-claim.json", {"unit": plan.unit, "spec_sha256": spec_sha})
    backend = backend_for(data, plan)
    terminal: control.Snapshot | None = None
    before_sha: str | None = None
    invocation: str | None = None
    cleanup = False
    watch_started: float | None = None
    kill_sent = False
    expected = False
    within = False
    final_error: BaseException | None = None
    try:
        intent = mapping(json.loads(read(outer / "intent.json")))
        started = intent["monotonic_start"]
        if (
            not isinstance(started, (int, float))
            or isinstance(started, bool)
            or not math.isfinite(started)
        ):
            raise ValueError("Start anchor")
        deadline = float(started) + 15
        bound_path = outer / "bound.json"
        if bound_path.exists():
            invocation = string(mapping(json.loads(read(bound_path)))["invocation_id"])
        # Leave two seconds for terminal fsync + empty-unit stop/readback.
        observation_deadline = deadline - 2
        for _ in range(15):
            left = observation_deadline - time.monotonic()
            if left <= 0:
                break
            snapshot = backend.snapshot(plan, min(1, left))
            snapshot.bind(plan, invocation)
            if invocation is None:
                invocation = snapshot.invocation
                # A recovered startup cannot qualify: ready/release were not bound.
                record_fault(
                    outer, "unacknowledged_start", RuntimeError("Inspect only; no resubmit")
                )
            if snapshot.cpu_ns > plan.cpu_watch_ns and watch_started is None:
                record_fault(outer, "cpu_watch", RuntimeError("Qualification CPU watch exceeded"))
                backend.signal(
                    plan,
                    snapshot.invocation,
                    "SIGTERM",
                    min(1, max(0.001, observation_deadline - time.monotonic())),
                )
                watch_started = time.monotonic()
            if (
                watch_started is not None
                and not kill_sent
                and snapshot.populated is True
                and time.monotonic() - watch_started >= 1
            ):
                backend.signal(
                    plan,
                    snapshot.invocation,
                    "SIGKILL",
                    min(1, max(0.001, observation_deadline - time.monotonic())),
                )
                kill_sent = True
            if snapshot.terminal and snapshot.populated is not True:
                terminal = snapshot
                break
            time.sleep(max(0, min(1, observation_deadline - time.monotonic())))
        if terminal is None:
            raise TimeoutError("Qualification closure unknown; unit retained")
        expected = expected_terminal(string(data["kind"]), terminal.properties)
        within = terminal.cpu_ns <= 8_000_000_000 and time.monotonic() <= deadline
        before_sha = write(
            outer,
            "terminal-before-stop.json",
            {
                "unit": plan.unit,
                "invocation_id": invocation,
                "cgroup": terminal.cgroup,
                "properties": terminal.properties,
                "cgroup_closed": True,
                "cpu_ns": terminal.cpu_ns,
                "within": within,
                "expected_terminal": expected,
            },
        )
        # Accounting/closure is durable before any stop. Never discard a populated unit.
        left = deadline - time.monotonic()
        if left <= 0 or invocation is None:
            raise TimeoutError("No terminal cleanup time")
        backend.stop(plan, invocation, min(1, left))
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("No cleanup readback time")
        after = backend.snapshot(plan, min(1, left))
        cleanup = core.confirms_empty_unit_cleanup(plan, terminal, after)
        released = mapping(json.loads(read(inner / "worker-released.json")))
        if released != {"spec_sha256": spec_sha, "invocation_id": invocation, "kind": data["kind"]}:
            raise ValueError("Release completion identity")
    except BaseException as error:
        final_error = error
        try:
            record_fault(outer, "finish", error)
        except BaseException as receipt_error:
            print(
                json.dumps(
                    {
                        "first_fault": type(error).__name__,
                        "receipt_fault": type(receipt_error).__name__,
                    }
                ),
                flush=True,
            )
    qualified = (
        final_error is None
        and expected
        and within
        and cleanup
        and not (outer / "first-fault.json").exists()
    )
    # Always attempt the terminal verdict, including failed startup/receipt paths.
    write(
        outer,
        "qualification-verdict.json",
        {
            "status": "qualified" if qualified else "incomplete",
            "kind": data["kind"],
            "spec_sha256": spec_sha,
            "source": SOURCE,
            "fixture_sha256": data["fixture_active_sha256"],
            "adapter": data["adapter"],
            "unit": plan.unit,
            "invocation_id": invocation,
            "cpu_ns": None if terminal is None else terminal.cpu_ns,
            "terminal_receipt_sha256": before_sha,
            "closed": cleanup,
            "no_scientific_calls": True,
            "no_retry": True,
        },
    )
    return qualified


def fixture_barrier(manifest: dict[str, object]) -> list[dict[str, object]]:
    rows = manifest.get("fixtures")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Exactly three qualification units")
    retained: list[dict[str, object]] = []
    for kind, value in zip(KINDS, rows, strict=True):
        row = mapping(value)
        spec_path, spec_raw = pinned(row["path"], row["sha256"])
        spec = load(spec_path, digest(spec_raw))
        if (
            spec["kind"] != kind
            or spec["combined_id"] != manifest["combined_id"]
            or spec["owner"] != manifest["owner"]
            or spec["owned_roots"] != manifest["owned_roots"]
        ):
            raise ValueError("Qualification order/owner")
        _, outer = roots(spec)
        raw = read(outer / "qualification-verdict.json")
        verdict = mapping(json.loads(raw))
        if (
            verdict.get("status") != "qualified"
            or verdict.get("kind") != kind
            or verdict.get("source") != SOURCE
            or verdict.get("spec_sha256") != digest(spec_raw)
            or verdict.get("fixture_sha256") != spec["fixture_active_sha256"]
            or verdict.get("adapter") != spec["adapter"]
            or verdict.get("closed") is not True
            or not 0 <= integer(verdict.get("cpu_ns")) <= 8_000_000_000
        ):
            raise ValueError("Qualification barrier")
        terminal_raw = read(outer / "terminal-before-stop.json")
        if digest(terminal_raw) != verdict["terminal_receipt_sha256"]:
            raise ValueError("Terminal receipt digest")
        retained.append(
            {
                "kind": kind,
                "verdict_sha256": digest(raw),
                "spec_sha256": digest(spec_raw),
                "unit": verdict["unit"],
                "invocation_id": verdict["invocation_id"],
            }
        )
    return retained


def stage_claim(manifest: dict[str, object], stage: str) -> Path:
    outer = private_path(manifest["control_root"], True)
    if (outer / "first-fault.json").exists():
        raise ValueError("Prior combined fault; cleanup only")
    write(
        outer,
        stage + "-claim.json",
        {
            "combined_id": manifest["combined_id"],
            "source": SOURCE,
            "owner": manifest["owner"],
            "no_retry": True,
        },
    )
    return outer


def barrier(manifest: dict[str, object]) -> None:
    outer = stage_claim(manifest, "barrier")
    qualified = fixture_barrier(manifest)
    engineering = mapping(manifest["engineering"])
    _, raw = pinned(engineering["path"], engineering["sha256"])
    evidence = mapping(json.loads(raw))
    adapter = mapping(manifest["adapter"])
    if (
        evidence.get("status") != "accepted_fake_only"
        or evidence.get("scientific_calls") != 0
        or evidence.get("real_process_attempts") != 0
        or evidence.get("adapter_sha256") != adapter["sha256"]
        or evidence.get("fixture_disabled_sha256") != manifest["fixture_disabled_sha256"]
        or evidence.get("all_cases_passed") is not True
    ):
        raise ValueError("Engineering qualification absent or source mismatch")
    write(
        outer,
        "qualification-barrier.json",
        {
            "source": SOURCE,
            "combined_id": manifest["combined_id"],
            "fixtures": qualified,
            "engineering_sha256": digest(raw),
            "owner": manifest["owner"],
        },
    )


def dispatch(manifest: dict[str, object]) -> None:
    outer = stage_claim(manifest, "dispatch")
    current = fixture_barrier(manifest)
    barrier_raw = read(outer / "qualification-barrier.json")
    proof = mapping(json.loads(barrier_raw))
    if proof.get("fixtures") != current or proof.get("owner") != manifest["owner"]:
        raise ValueError("Qualification proof changed")
    grid = mapping(manifest["grid"])
    _, template_raw = pinned(grid["template_path"], grid["template_sha256"])
    template = mapping(json.loads(template_raw))
    inner, grid_outer = roots(grid | {"owned_roots": manifest["owned_roots"]})
    if os.path.lexists(outer / "grid-dispatch-intent.json"):
        raise ValueError("GRID dispatch authority already consumed")
    if template.get("run_root") != str(inner) or template.get("source") != SOURCE:
        raise ValueError("Exact GRID source/root")
    if template.get("supervisor_control_root") != str(grid_outer):
        raise ValueError("GRID control-root binding")
    if os.statvfs(inner).f_bavail * os.statvfs(inner).f_frsize < CONTRACT["start_free_bytes"]:
        raise ValueError("Fresh GRID capacity guard")
    fields = mapping(template["supervisor"])
    if fields.get("qualification_accepted") is not False:
        raise ValueError("Unconsumed qualification barrier required")
    fields["qualification_accepted"] = True
    fields["qualification_barrier_sha256"] = digest(barrier_raw)
    template["supervisor"] = fields
    admission_sha = write(inner, "admission.json", template)
    # write() has a fixed encoding; use exactly the bytes actually persisted.
    admission_sha = digest(read(inner / "admission.json"))
    active_path, active_raw = pinned(grid["active_adapter_path"], grid["active_adapter_sha256"])
    _, disabled_raw = pinned(grid["disabled_adapter_path"], grid["disabled_adapter_sha256"])
    if grid["disabled_adapter_sha256"] != mapping(manifest["adapter"])["sha256"]:
        raise ValueError("Qualification and GRID adapter identities differ")
    if active_raw != activate(disabled_raw):
        raise ValueError("Adapter flag-only activation")
    write(
        outer,
        "grid-dispatch-intent.json",
        {
            "source": SOURCE,
            "combined_id": manifest["combined_id"],
            "owner": manifest["owner"],
            "qualification_barrier_sha256": digest(barrier_raw),
            "admission_sha256": admission_sha,
            "adapter_sha256": digest(active_raw),
            "run_root": str(inner),
            "unit": "grid-q1-" + digest(f"{inner}:{admission_sha}".encode())[:24] + ".service",
            "no_retry": True,
        },
    )
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-I",
            "-B",
            str(active_path),
            "--admission",
            str(inner / "admission.json"),
            "--sha256",
            admission_sha,
        ],
    )


def lease_check(receipt: dict[str, object], maximum_cpus: int) -> None:
    start_ns = integer(receipt.get("start_monotonic_ns"))
    end_ns = integer(receipt.get("end_monotonic_ns"))
    if (
        not 0 <= end_ns - start_ns <= 2_400_000_000_000
        or not 0 < integer(receipt.get("maximum_cpu_count")) <= maximum_cpus
        or receipt.get("boot_start") != receipt.get("boot_end")
        or not receipt.get("boot_start")
        or receipt.get("closed") is not True
    ):
        raise ValueError("Unclosed or invalid host lease")


def output_census(manifest: dict[str, object]) -> dict[str, object]:
    """Logical counts and allocated blocks are distinct; reserve a final-record tail."""
    pools = mapping(manifest["output_pools"])
    expected = {
        "inner": 72 * 1024**2,
        "qualification": 7 * 1024**2,
        "source": 3 * 1024**2,
        "grid_control": 18 * 1024**2,
        "transport": 4 * 1024**2,
    }
    owned = manifest["owned_roots"]
    if not isinstance(owned, list):
        raise ValueError("Owned-root list")
    seen: set[Path] = set()
    totals: dict[str, object] = {}
    files = 0
    logical_total = 0
    for name, limit in expected.items():
        group = pools.get(name)
        if not isinstance(group, list):
            raise ValueError("Exact output pool")
        logical = 0
        allocated = 0
        for raw_path in group:
            root = private_path(raw_path, True)
            if str(root) not in owned or root in seen:
                raise ValueError("Unbound or duplicate output root")
            if any(root.is_relative_to(other) or other.is_relative_to(root) for other in seen):
                raise ValueError("Overlapping output roots")
            seen.add(root)
            for current, directories, names in os.walk(root, followlinks=False):
                for child in [Path(current) / item for item in directories + names]:
                    info = child.lstat()
                    allocated += info.st_blocks * 512
                    if stat.S_ISDIR(info.st_mode):
                        private_path(str(child), True)
                        continue
                    files += 1
                    if files > 10000 or info.st_uid != os.getuid() or info.st_nlink != 1:
                        raise ValueError("Bounded owner-only writer inventory")
                    if (
                        stat.S_ISFIFO(info.st_mode)
                        and name == "qualification"
                        and child.name == "release.fifo"
                    ):
                        if stat.S_IMODE(info.st_mode) != 0o600:
                            raise ValueError("FIFO mode")
                        continue
                    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
                        raise ValueError("Unexpected writer type/mode")
                    logical += info.st_size
        reserve = 256 * 1024 if name == "transport" else 0
        if logical + reserve > limit:
            raise ValueError("Output pool exhausted: " + name)
        totals[name] = {
            "logical_bytes": logical,
            "allocated_bytes": allocated,
            "limit_bytes": limit,
            "reserved_final_bytes": reserve,
        }
        logical_total += logical
    if seen != {Path(string(item)) for item in owned}:
        raise ValueError("Incomplete owned-root inventory")
    return {
        "pools": totals,
        "files": files,
        "logical_bytes": logical_total,
        "logical_limit": 104 * 1024**2,
        "allocated_blocks_are_separate": True,
    }


def closeout(manifest: dict[str, object]) -> bool:
    """Retain a ledger even when earlier stages failed; never retry or clean services."""
    outer = private_path(manifest["control_root"], True)
    records: dict[str, dict[str, object]] = {}
    issues: list[dict[str, object]] = []
    omitted_issues = 0

    def problem(stage: str, error: BaseException) -> None:
        nonlocal omitted_issues
        if len(issues) < 24:
            issues.append(
                {"stage": stage, "kind": type(error).__name__, "detail": str(error)[:160]}
            )
        else:
            omitted_issues += 1

    def retained(key: str, path: Path, required: bool = True) -> dict[str, object] | None:
        records[key] = {"status": "unreadable"}
        try:
            raw = read(path)
            records[key] = {"status": "retained", "sha256": digest(raw)}
            return mapping(json.loads(raw))
        except FileNotFoundError as error:
            records[key]["status"] = "missing"
            if required:
                problem(key, error)
        except BaseException as error:
            records[key]["status"] = "invalid_or_unreadable"
            problem(key, error)
        return None

    def faults(label: str, root: Path) -> None:
        first = retained(label + "/first-fault.json", root / "first-fault.json", False)
        if first is not None:
            problem(
                label + "/prior_fault", RuntimeError("Retained first fault remains authoritative")
            )
        try:
            paths = sorted(root.glob("cleanup-fault-*.json"))
            if len(paths) > MAX_RECEIPTS:
                problem(label + "/cleanup_faults", ValueError("Fault inventory exceeds bound"))
            if paths:
                problem(
                    label + "/prior_cleanup_fault",
                    RuntimeError("Retained cleanup fault remains authoritative"),
                )
            for path in paths[:MAX_RECEIPTS]:
                retained(label + "/" + path.name, path)
        except BaseException as error:
            problem(label + "/cleanup_faults", error)

    faults("combined", outer)
    phases = retained("combined/phase-status.json", outer / "phase-status.json")
    phase_success = False
    if phases is not None:
        try:
            qualification_exit = integer(phases.get("qualification_exit"))
            grid_exit = integer(phases.get("grid_exit"))
            if not 0 <= qualification_exit <= 255 or not 0 <= grid_exit <= 255:
                raise ValueError("Phase exit range")
            phase_success = qualification_exit == 0 and grid_exit == 0
            if not phase_success:
                raise ValueError("Earlier operator phase failed")
        except BaseException as error:
            problem("phase_status", error)

    lease_hashes: dict[str, str] = {}
    for host, maximum in (("client", 10), ("server", 4)):
        try:
            reference = mapping(mapping(manifest["leases"])[host])
            _, raw = pinned(reference["path"], reference["sha256"])
            records["lease/" + host] = {"status": "retained", "sha256": digest(raw)}
            receipt = mapping(json.loads(raw))
            start = integer(receipt.get("start_monotonic_ns"))
            observed = integer(receipt.get("observed_monotonic_ns"))
            if (
                not 0 <= observed - start < 2_400_000_000_000
                or not 0 < integer(receipt.get("maximum_cpu_count")) <= maximum
                or receipt.get("boot_start") != receipt.get("boot_observed")
                or not receipt.get("boot_start")
                or receipt.get("closed") is not False
                or receipt.get("combined_id") != manifest["combined_id"]
                or receipt.get("source") != SOURCE
            ):
                raise ValueError("Invalid owner-bound open lease observation")
            lease_hashes[host] = digest(raw)
        except BaseException as error:
            records.setdefault("lease/" + host, {"status": "unverified"})
            problem("lease/" + host, error)

    try:
        rows = manifest["fixtures"]
        if not isinstance(rows, list) or len(rows) != 3:
            raise ValueError("Exactly three fixture references")
        for kind, value in zip(KINDS, rows, strict=True):
            try:
                row = mapping(value)
                path, raw = pinned(row["path"], row["sha256"])
                records[kind + "/spec"] = {"status": "retained", "sha256": digest(raw)}
                spec = load(path, digest(raw))
                if spec.get("kind") != kind or spec.get("owner") != manifest["owner"]:
                    raise ValueError("Fixture identity")
                _, fixture_root = roots(spec)
                for name in (
                    "intent.json",
                    "bound.json",
                    "qualification-verdict.json",
                    "terminal-before-stop.json",
                ):
                    retained(kind + "/" + name, fixture_root / name)
                faults(kind, fixture_root)
            except BaseException as error:
                problem(kind + "/receipts", error)
    except BaseException as error:
        problem("fixture_inventory", error)
    qualified = False
    try:
        current = fixture_barrier(manifest)
        proof = retained(
            "combined/qualification-barrier.json", outer / "qualification-barrier.json"
        )
        if (
            proof is None
            or proof.get("fixtures") != current
            or proof.get("owner") != manifest["owner"]
        ):
            raise ValueError("Qualification barrier missing or changed")
        qualified = True
    except BaseException as error:
        problem("qualification", error)

    intent = retained("combined/grid-dispatch-intent.json", outer / "grid-dispatch-intent.json")
    result: dict[str, object] | None = None
    grid_complete = False
    try:
        grid = mapping(manifest["grid"])
        grid_root = private_path(grid["control_root"], True)
        result = retained("grid/supervisor-final.json", grid_root / "supervisor-final.json")
        retained("grid/supervisor-fallback.json", grid_root / "supervisor-fallback.json", False)
        primary_fault = retained(
            "grid/supervisor-first-fault.json", grid_root / "supervisor-first-fault.json", False
        )
        if primary_fault is not None:
            problem("grid/primary_fault", RuntimeError("Retained supervisor first fault"))
        for name in (
            "supervisor-intent.json",
            "supervisor-bound.json",
            "supervisor-terminal-before-stop.json",
            "supervisor-controller-result-join.json",
        ):
            retained("grid/" + name, grid_root / name, False)
        faults("grid", grid_root)
        if (
            result is None
            or intent is None
            or result.get("status") != "provisional_complete"
            or result.get("cgroup_closed") is not True
            or result.get("unit_cleanup_confirmed") is not True
            or not isinstance(intent.get("unit"), str)
            or result.get("unit") != intent["unit"]
            or intent.get("source") != SOURCE
            or result.get("first_fault") is not None
            or result.get("cleanup_errors") != []
            or result.get("diagnostic_outcome") not in ("passed", "complete_negative")
        ):
            raise ValueError("GRID result absent, incomplete or unbound")
        grid_complete = True
    except BaseException as error:
        problem("grid_result", error)

    census: dict[str, object] | None = None
    try:
        census = output_census(manifest)
    except BaseException as error:
        problem("output_census", error)
    try:
        usage = os.statvfs(outer)
        if usage.f_bavail * usage.f_frsize < CONTRACT["later_free_bytes"]:
            raise ValueError("Final host reserve")
    except BaseException as error:
        problem("capacity", error)
    provisional = (
        phase_success and qualified and grid_complete and not issues and not omitted_issues
    )
    summary: dict[str, object] = {
        "status": "pending_external_witness",
        "accepted": False,
        "attempt_status": "provisional_complete" if provisional else "incomplete",
        "source": SOURCE,
        "combined_id": manifest["combined_id"],
        "owner": manifest["owner"],
        "leases": lease_hashes,
        "retained_receipts": records,
        "phase_status": None
        if phases is None
        else {
            "qualification_exit": phases.get("qualification_exit"),
            "grid_exit": phases.get("grid_exit"),
        },
        "qualification_complete": qualified,
        "grid_complete": grid_complete,
        "provisional_diagnostic_outcome": result.get("diagnostic_outcome")
        if grid_complete and result
        else None,
        "missing_records_do_not_prove_no_invocation": True,
        "issues": issues,
        "omitted_issue_count": omitted_issues,
        "first_fault_records_unchanged": True,
        "whole_host_cpu_upper_seconds": 33600,
        "not_measured_scientific_cost": True,
        "no_components_added_twice": True,
        "historical_costs": "unknowns-preserved-no-reset",
        "output_census": census,
        "observations_are_not_final_lease_endpoints": True,
        "final_ledger_must_enclose_all_later_writes_and_client_exit": True,
        "no_retry": True,
    }
    summary_sha: str | None = None
    try:
        summary_sha = write(outer, "combined-closeout.json", summary)
    except BaseException as error:
        problem("combined_closeout_write", error)
        summary["attempt_status"] = "incomplete"
        summary["omitted_issue_count"] = omitted_issues
    # The fallback is terminal-only: never overwrite a partial or earlier receipt.
    # No source-owned file writes follow this observed post-write/failure marker.
    marker: dict[str, object] = {
        "kind": "post_write_terminal_witness" if summary_sha else "closeout_write_failed",
        "combined_closeout_sha256": summary_sha,
        "combined_id": manifest["combined_id"],
        "source": SOURCE,
        "server_monotonic_ns": time.monotonic_ns(),
        "accepted": False,
        "ledger_retained": summary_sha is not None,
        "attempt_status": summary["attempt_status"],
        "requires_external_post_exit_and_client_drain": True,
        "transport_boundary": "owned_command_handback_shared_transport_retained",
    }
    if summary_sha is None:
        marker["fallback_summary"] = summary
    try:
        print(json.dumps(marker, sort_keys=True, allow_nan=False), flush=True)
    except BaseException:
        # The durable ledger, if any, remains provisional without a terminal witness.
        return False
    return summary_sha is not None


def main() -> int:
    if not ENABLED:
        raise SystemExit("Disabled pending combined admission")
    os.umask(0o077)
    # systemd's fixed Plan.argv supplies these two positional worker arguments.
    if len(sys.argv) == 3 and not sys.argv[1].startswith("-"):
        data = load(Path(sys.argv[1]), sys.argv[2])
        return worker(data, sys.argv[2])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("start", "ready", "release", "finish", "barrier", "dispatch", "closeout")
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    data = load(args.spec, args.sha256)
    try:
        if args.mode == "start":
            start(data, args.sha256)
        elif args.mode == "ready":
            ready(data, args.sha256)
        elif args.mode == "release":
            release(data, args.sha256)
        elif args.mode == "finish":
            return 0 if finish(data, args.sha256) else 1
        elif args.mode == "barrier":
            barrier(data)
        elif args.mode == "dispatch":
            dispatch(data)
        else:
            return 0 if closeout(data) else 1
    except BaseException as error:
        try:
            record_fault(private_path(data["control_root"], True), args.mode, error)
        except BaseException as receipt_error:
            print(
                json.dumps(
                    {
                        "status": "unknown",
                        "first_fault": type(error).__name__,
                        "receipt_fault": type(receipt_error).__name__,
                    }
                ),
                flush=True,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
