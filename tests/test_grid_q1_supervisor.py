"""Synthetic control failures only: no systemd service, GRID or reference invocation."""

import hashlib
import json
import os
import subprocess
from collections import deque
from dataclasses import replace
from pathlib import Path

import pytest

from scripts import grid_q1_supervisor as control


@pytest.fixture(autouse=True)
def no_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Synthetic qualification must not start a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)


def plan(root: Path) -> control.Plan:
    return control.Plan(
        root, "a" * 64, "b" * 64, 10, 2, 3, 10, 100_000, 1_000_000_000, 1, 10, 1, 1, 15
    )


def state(
    item: control.Plan,
    phase: str = "running",
    *,
    cpu: str = "100000000",
    invocation: str = "c" * 32,
    populated: bool | None = False,
) -> control.Snapshot:
    values = {
        **item.required,
        "Id": item.unit,
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": phase,
        "InvocationID": invocation,
        "ControlGroup": "/user.slice/grid-q1-fixture.service",
        "CPUUsageNSec": cpu,
        "RuntimeMaxUSec": "10s",
        "RuntimeRandomizedExtraUSec": "0",
        "TimeoutStartUSec": "2s",
        "TimeoutStopUSec": "3s",
        "CPUQuotaPerSecUSec": "100ms",
        "CPUQuotaPeriodUSec": "100ms",
        "Result": "success",
        "ExecMainCode": "1",
        "ExecMainStatus": "0",
        "ExecMainStartTimestampMonotonic": "1",
        "ExecMainExitTimestampMonotonic": "2" if phase == "exited" else "0",
        "ObservedCPUMax": (
            f"{item.quota_period_us * item.cpu_quota_percent // 100} {item.quota_period_us}"
        ),
        "ObservedCPUMaxBurst": "0",
    }
    return control.Snapshot(values, populated)


MISSING = control.Snapshot({"LoadState": "not-found", "ActiveState": "inactive"}, None)


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeSupervisor:
    def __init__(
        self,
        snapshots: list[control.Snapshot],
        events: list[str],
        *,
        submit_error: Exception | None = None,
        signal_error: Exception | None = None,
        stop_error: Exception | None = None,
        post_stop_snapshot: control.Snapshot = MISSING,
    ) -> None:
        self.snapshots = deque(snapshots)
        self.last = snapshots[-1]
        self.events = events
        self.submit_error = submit_error
        self.signal_error = signal_error
        self.stop_error = stop_error
        self.submissions = 0
        self.stopped = False
        self.post_stop_snapshot = post_stop_snapshot

    def snapshot(self, item: control.Plan, timeout: float) -> control.Snapshot:
        assert timeout > 0
        self.events.append("snapshot")
        if self.stopped:
            return self.post_stop_snapshot
        if self.snapshots:
            self.last = self.snapshots.popleft()
        return self.last

    def submit(self, item: control.Plan, timeout: float) -> None:
        self.events.append("submit")
        self.submissions += 1
        if self.submit_error is not None:
            raise self.submit_error

    def signal(self, item: control.Plan, invocation: str, signal_name: str, timeout: float) -> None:
        self.events.append(signal_name)
        if self.signal_error is not None:
            raise self.signal_error

    def stop(self, item: control.Plan, invocation: str, timeout: float) -> None:
        self.events.append("stop")
        if self.stop_error is not None:
            raise self.stop_error
        self.stopped = True


class FakeReceipts:
    def __init__(self, events: list[str], fail: tuple[str, ...] = ()) -> None:
        self.events = events
        self.fail = fail
        self.records: dict[str, dict[str, object]] = {}
        self.controller_result: dict[str, object] = {
            "final_status": "complete",
            "within_envelope": True,
            "diagnostic_outcome": "passed",
        }

    def write(self, name: str, record: dict[str, object]) -> None:
        self.events.append(name)
        if name in self.fail:
            raise OSError("Synthetic receipt persistence failure")
        if name in self.records:
            raise FileExistsError(name)
        self.records[name] = record

    def result(self, item: control.Plan, invocation: str) -> dict[str, object]:
        return self.controller_result


def run(item: control.Plan, backend: FakeSupervisor, receipts: FakeReceipts) -> dict[str, object]:
    clock = Clock()
    return control.execute(item, backend, receipts, clock.now, clock.sleep)


def test_pass_is_provisional_and_accounting_saved_before_stop(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor([MISSING, state(item, "exited")], events)
    receipts = FakeReceipts(events)
    result = run(item, backend, receipts)
    assert result["status"] == "provisional_complete"
    assert result["accepted"] is False
    assert result["external_combined_ledger_closure_required"] is True
    assert events.index("supervisor-intent.json") < events.index("submit")
    assert events.index("supervisor-terminal-before-stop.json") < events.index("stop")
    assert backend.submissions == 1


def test_complete_negative_is_preserved(tmp_path: Path) -> None:
    item = plan(tmp_path)
    ended = state(item, "exited")
    ended.properties.update(ExecMainStatus="1", Result="exit-code")
    events: list[str] = []
    receipts = FakeReceipts(events)
    receipts.controller_result["diagnostic_outcome"] = "failed"
    backend = FakeSupervisor([MISSING, ended], events)
    result = run(item, backend, receipts)
    assert result["status"] == "provisional_complete"
    assert result["diagnostic_outcome"] == "complete_negative"


def test_first_fault_survives_cleanup_permission_error(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    receipts = FakeReceipts(events)
    backend = FakeSupervisor(
        [MISSING, state(item, populated=True)],
        events,
        submit_error=RuntimeError("first transport acknowledgement fault"),
        signal_error=PermissionError("cleanup denied"),
    )
    result = run(item, backend, receipts)
    first = control.object_map(result["first_fault"])
    errors = result["cleanup_errors"]
    assert first["kind"] == "RuntimeError"
    assert first["detail"] == "first transport acknowledgement fault"
    assert isinstance(errors, list)
    assert control.object_map(errors[0])["kind"] == "PermissionError"
    assert events.index("supervisor-first-fault.json") < events.index("SIGTERM")
    assert "supervisor-final.json" in receipts.records
    assert result["status"] == "incomplete"
    assert result["numerical_attempt"] == "attempt_unknown"
    assert backend.submissions == 1


def test_lost_ack_inspects_same_unit_without_resubmission(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor(
        [MISSING, state(item, "exited")], events, submit_error=TimeoutError("lost ack")
    )
    result = run(item, backend, FakeReceipts(events))
    assert backend.submissions == 1
    assert result["cgroup_closed"] is True
    assert result["status"] == "incomplete"
    assert control.object_map(result["first_fault"])["kind"] == "TimeoutError"


def test_existing_unit_is_not_dispatched(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor([state(item)], events)
    result = run(item, backend, FakeReceipts(events))
    assert backend.submissions == 0
    assert result["numerical_attempt"] == "not_started"


def test_exclusive_intent_prevents_second_dispatch(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    receipts = FakeReceipts(events)
    first = FakeSupervisor([MISSING, state(item, "exited")], events)
    run(item, first, receipts)
    second = FakeSupervisor([MISSING], events)
    result = run(item, second, receipts)
    assert second.submissions == 0
    assert result["status"] == "incomplete"


@pytest.mark.parametrize("cpu", ["", "infinity", "18446744073709551615"])
def test_missing_or_sentinel_usage_is_incomplete(tmp_path: Path, cpu: str) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor([MISSING, state(item, "exited", cpu=cpu)], events)
    result = run(item, backend, FakeReceipts(events))
    assert result["status"] == "incomplete"
    assert backend.stopped is False


def test_cpu_fault_remains_authoritative_after_clean_sigterm(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    busy = state(item, cpu=str(item.cpu_watch_ns), populated=True)
    ended = state(item, "exited", cpu=str(item.cpu_watch_ns))
    backend = FakeSupervisor([MISSING, busy, busy, ended], events)
    result = run(item, backend, FakeReceipts(events))
    assert "SIGTERM" in events
    assert result["cgroup_closed"] is True
    assert control.object_map(result["first_fault"])["detail"] == "CPU watch margin reached"
    assert result["status"] == "incomplete"


def test_survivor_escalation_then_unknown_closure(tmp_path: Path) -> None:
    item = replace(plan(tmp_path), observations=10)
    events: list[str] = []
    busy = state(item, populated=True)
    backend = FakeSupervisor([MISSING, busy], events, submit_error=TimeoutError("lost ack"))
    result = run(item, backend, FakeReceipts(events))
    assert "SIGTERM" in events and "SIGKILL" in events
    assert result["cgroup_closed"] is False
    assert result["status"] == "incomplete"
    assert "supervisor-final.json" in events


def test_changed_invocation_is_never_cleaned_as_ours(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor(
        [MISSING, state(item, populated=True), state(item, "exited", invocation="d" * 32)],
        events,
    )
    result = run(item, backend, FakeReceipts(events))
    assert result["status"] == "incomplete"
    assert "stop" not in events and "SIGTERM" not in events


def test_uncaptured_disappeared_cgroup_is_not_closure(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor([MISSING, state(item, "exited", populated=None)], events)
    result = run(item, backend, FakeReceipts(events))
    assert result["cgroup_closed"] is False
    assert result["status"] == "incomplete"


def test_bound_cgroup_disappearance_with_cached_terminal_is_closure(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor(
        [MISSING, state(item, populated=True), state(item, "exited", populated=None)],
        events,
    )
    result = run(item, backend, FakeReceipts(events))
    assert result["status"] == "provisional_complete"


@pytest.mark.parametrize(
    "failed_name",
    [
        "supervisor-first-fault.json",
        "supervisor-terminal-before-stop.json",
        "supervisor-final.json",
    ],
)
def test_receipt_failure_cannot_become_success(tmp_path: Path, failed_name: str) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    receipts = FakeReceipts(events, (failed_name,))
    error = (
        RuntimeError("primary failure") if failed_name == "supervisor-first-fault.json" else None
    )
    backend = FakeSupervisor([MISSING, state(item, "exited")], events, submit_error=error)
    result = run(item, backend, receipts)
    assert result["status"] == "incomplete"
    if failed_name == "supervisor-terminal-before-stop.json":
        assert backend.stopped is False
    if failed_name == "supervisor-final.json":
        assert "supervisor-fallback.json" in receipts.records


def test_missing_both_terminal_receipts_stays_unknown(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    receipts = FakeReceipts(events, ("supervisor-final.json", "supervisor-fallback.json"))
    result = run(item, FakeSupervisor([MISSING, state(item, "exited")], events), receipts)
    assert result["status"] == "incomplete"
    assert "final_receipt_error" in result and "fallback_receipt_error" in result


def test_cleanup_failure_retains_first_receipt_and_final_failure(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    receipts = FakeReceipts(events)
    backend = FakeSupervisor(
        [MISSING, state(item, "exited")],
        events,
        stop_error=PermissionError("stop denied"),
    )
    result = run(item, backend, receipts)
    assert "supervisor-terminal-before-stop.json" in receipts.records
    assert result["status"] == "incomplete"
    assert result["unit_cleanup_confirmed"] is False


@pytest.mark.parametrize(
    "raw,expected",
    [("1s", 1_000_000), ("100ms", 100_000), ("11min", 660_000_000), ("1min 2s", 62_000_000)],
)
def test_systemd_duration_readback(raw: str, expected: int) -> None:
    assert control.duration_us(raw) == expected


@pytest.mark.parametrize("raw", ["infinity", "n/a", "-1s", "1fortnight"])
def test_duration_sentinels_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        control.duration_us(raw)


def test_files_receipt_is_exclusive_and_syncs_file_before_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = os.fsync
    calls: list[str] = []

    def observed(fd: int) -> None:
        calls.append("directory" if os.path.isdir(f"/proc/self/fd/{fd}") else "file")
        original(fd)

    monkeypatch.setattr(os, "fsync", observed)
    files = control.Files(tmp_path)
    files.write("receipt.json", {"status": "synthetic"})
    assert calls == ["file", "directory"]
    assert (tmp_path / "receipt.json").stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        files.write("receipt.json", {"status": "overwrite"})


def test_entry_remains_disabled() -> None:
    assert control.ENABLED is False
    with pytest.raises(SystemExit, match="Disabled"):
        control.main()


def test_manager_timeout_cannot_be_reported_as_pass(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    ended = state(item, "exited")
    ended.properties["Result"] = "timeout"
    result = run(item, FakeSupervisor([MISSING, ended], events), FakeReceipts(events))
    assert result["status"] == "incomplete"


def test_cpu_accounting_must_not_decrease(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    backend = FakeSupervisor(
        [MISSING, state(item, populated=True), state(item, "exited", cpu="50000000")],
        events,
    )
    result = run(item, backend, FakeReceipts(events))
    assert result["status"] == "incomplete"
    assert backend.stopped is False


def test_submission_uses_detached_retained_exact_unit(tmp_path: Path) -> None:
    item = plan(tmp_path)
    captured: list[list[str]] = []

    class Recorder(control.Systemd):
        def command(self, argv: list[str], timeout: float, allow_missing: bool = False) -> str:
            captured.append(argv)
            return ""

    item.control_root.mkdir(mode=0o700)
    Recorder(item.control_root).submit(item, 1)
    argv = captured[0]
    assert "--unit=" + item.unit in argv
    assert "--service-type=exec" in argv
    assert "--remain-after-exit" in argv
    assert "--expand-environment=no" in argv
    for forbidden in ("--wait", "--pipe", "--pty", "--collect"):
        assert forbidden not in argv
    for property_value in (
        "ExitType=cgroup",
        "CPUAccounting=yes",
        "Restart=no",
        "KillMode=control-group",
        "SendSIGKILL=yes",
        "UMask=0077",
        "RuntimeRandomizedExtraSec=0",
        "CPUQuota=10%",
    ):
        assert "--property=" + property_value in argv
    assert argv[-len(item.argv) :] == item.argv


@pytest.mark.parametrize("failure_mode", ("timeout", "nonzero"))
def test_command_and_fsync_failure_preserve_both(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
) -> None:
    def failed_command(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        if failure_mode == "timeout":
            raise subprocess.TimeoutExpired("synthetic-systemctl", 1)
        return subprocess.CompletedProcess(["synthetic-systemctl"], 7)

    def denied(fd: int) -> None:
        raise PermissionError("synthetic-fsync")

    monkeypatch.setattr(subprocess, "run", failed_command)
    monkeypatch.setattr(os, "fsync", denied)
    events: list[str] = []
    receipts = FakeReceipts(events)
    clock = Clock()
    result = control.execute(
        plan(tmp_path),
        control.Systemd(tmp_path),
        receipts,
        clock.now,
        clock.sleep,
    )
    first = control.object_map(result["first_fault"])
    assert first["kind"] == ("TimeoutExpired" if failure_mode == "timeout" else "RuntimeError")
    if failure_mode == "nonzero":
        assert "exited 7" in str(first)
    errors = result["cleanup_errors"]
    assert isinstance(errors, list)
    assert control.object_map(errors[0])["kind"] == "PermissionError"
    assert "supervisor-final.json" in receipts.records
    assert result["status"] == "incomplete"


def admission(root: Path) -> tuple[Path, str]:
    controller = b"# synthetic nonexecuted controller\n"
    (root / "run.py").write_bytes(controller)
    (root / "run.py").chmod(0o600)
    control_root = root.with_name(root.name + "-control")
    control_root.mkdir(mode=0o700)
    data = {
        "admitted": True,
        "source": control.SOURCE,
        "run_root": str(root),
        "supervisor_control_root": str(control_root),
        "supervisor": {
            **control.GRID_PROFILE,
            "qualification_accepted": True,
            "controller_sha256": hashlib.sha256(controller).hexdigest(),
        },
    }
    path = root / "admission.json"
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return path, hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "name",
    [
        "result.json",
        "verification.json",
        "activation.json",
        "controller-exception.json",
        "administrative-outcome.json",
        "held-attempt-receipt.json",
    ],
)
def test_prior_receipt_cannot_support_new_negative(tmp_path: Path, name: str) -> None:
    root = tmp_path / "run"
    root.mkdir(mode=0o700)
    path, digest = admission(root)
    (root / name).write_text(
        '{"final_status":"complete","within_envelope":true,"diagnostic_outcome":"failed"}'
    )
    with pytest.raises(ValueError, match="previous attempt"):
        control.load_plan(path, digest)


@pytest.mark.parametrize("change", ["qualification", "source", "controller", "admission"])
def test_load_plan_requires_exact_qualified_admission(tmp_path: Path, change: str) -> None:
    root = tmp_path / "run"
    root.mkdir(mode=0o700)
    path, digest = admission(root)
    data = control.object_map(json.loads(path.read_bytes()))
    fields = control.object_map(data["supervisor"])
    if change == "qualification":
        fields["qualification_accepted"] = False
        data["supervisor"] = fields
    elif change == "source":
        data["source"] = "d" * 40
    elif change == "controller":
        fields["controller_sha256"] = "e" * 64
        data["supervisor"] = fields
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    if change != "admission":
        digest = hashlib.sha256(raw).hexdigest()
    else:
        digest = "f" * 64
    with pytest.raises(ValueError):
        control.load_plan(path, digest)


def test_quota_proof_is_mandatory_before_cached_closure(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    live = state(item, populated=True)
    live.properties.pop("ObservedCPUMax")
    ended = state(item, "exited", populated=None)
    ended.properties.pop("ObservedCPUMax")
    result = run(item, FakeSupervisor([MISSING, live, ended], events), FakeReceipts(events))
    assert result["status"] == "incomplete"
    assert result["cgroup_closed"] is False


def test_snapshot_and_sleep_share_observation_deadline(tmp_path: Path) -> None:
    item = plan(tmp_path)
    events: list[str] = []
    clock = Clock()
    busy = state(item, populated=True)
    limits: list[float] = []

    class Slow(FakeSupervisor):
        def snapshot(self, item: control.Plan, timeout: float) -> control.Snapshot:
            limits.append(timeout)
            clock.sleep(timeout)
            return super().snapshot(item, timeout)

    backend = Slow([MISSING, busy], events)
    result = control.execute(item, backend, FakeReceipts(events), clock.now, clock.sleep)
    assert result["status"] == "incomplete"
    assert all(0 < value <= item.command_seconds for value in limits)
    assert clock.value <= item.terminal_seconds


def test_complete_negative_accepts_same_retained_failed_unit(tmp_path: Path) -> None:
    item = plan(tmp_path)
    terminal = state(item, "exited")
    terminal.properties.update(
        ActiveState="failed", SubState="failed", Result="exit-code", ExecMainStatus="1"
    )
    after = control.Snapshot(dict(terminal.properties), False)
    events: list[str] = []
    receipts = FakeReceipts(events)
    receipts.controller_result["diagnostic_outcome"] = "failed"
    backend = FakeSupervisor([MISSING, terminal], events, post_stop_snapshot=after)
    result = run(item, backend, receipts)
    assert result["status"] == "provisional_complete"
    assert result["diagnostic_outcome"] == "complete_negative"
    assert result["unit_cleanup_confirmed"] is True
    assert events.index("supervisor-terminal-before-stop.json") < events.index("stop")
    assert after.properties["ActiveState"] == "failed"


@pytest.mark.parametrize("mutation", ["invocation", "outcome", "populated", "cpu"])
def test_retained_failed_cleanup_rejects_changed_evidence(tmp_path: Path, mutation: str) -> None:
    item = plan(tmp_path)
    terminal = state(item, "exited")
    terminal.properties.update(
        ActiveState="failed", SubState="failed", Result="exit-code", ExecMainStatus="1"
    )
    properties = dict(terminal.properties)
    populated = False
    if mutation == "invocation":
        properties["InvocationID"] = "f" * 32
    elif mutation == "outcome":
        properties["Result"] = "timeout"
    elif mutation == "cpu":
        properties["CPUUsageNSec"] = "0"
    else:
        populated = True
    events: list[str] = []
    receipts = FakeReceipts(events)
    receipts.controller_result["diagnostic_outcome"] = "failed"
    backend = FakeSupervisor(
        [MISSING, terminal],
        events,
        post_stop_snapshot=control.Snapshot(properties, populated),
    )
    result = run(item, backend, receipts)
    assert result["status"] == "incomplete"
    assert result["unit_cleanup_confirmed"] is False


def test_unexpected_timeout_stays_incomplete_with_retained_failed_cleanup(tmp_path: Path) -> None:
    item = plan(tmp_path)
    terminal = state(item, "exited")
    terminal.properties.update(
        ActiveState="failed",
        SubState="failed",
        Result="timeout",
        ExecMainCode="2",
        ExecMainStatus="15",
    )
    events: list[str] = []
    backend = FakeSupervisor(
        [MISSING, terminal],
        events,
        post_stop_snapshot=control.Snapshot(dict(terminal.properties), False),
    )
    result = run(item, backend, FakeReceipts(events))
    assert result["status"] == "incomplete"
    assert result["first_fault"] is not None
    assert result["unit_cleanup_confirmed"] is True
