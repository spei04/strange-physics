"""Synthetic owner/controller and manager APIs; never spawn a process/service."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import pytest
from test_d1_owned_capture import INVOCATION, MISSING, Clock, Manager, Records, spec, state

from scripts import d1_capture_owner as owner
from scripts import d1_owned_capture as owned
from scripts.grid_q1_supervisor import CommandFailure, Fault, Plan, Snapshot, Systemd


def first(result: dict[str, object]) -> dict[str, object]:
    value = result["first_fault"]
    assert type(value) is dict
    return value


class FakeChild:
    def __init__(
        self, clock: Clock, *, timeout: bool = False, code: int = 0, reap_error: bool = False
    ) -> None:
        self.clock = clock
        self.timeout = timeout
        self.code = code
        self.reap_error = reap_error
        self.killed = False
        self.waits: list[float] = []

    def wait(self, timeout: float) -> int:
        self.waits.append(timeout)
        if self.killed:
            if self.reap_error:
                raise OSError("synthetic unreapable controller")
            return -9
        if self.timeout:
            self.clock.value += timeout
            raise subprocess.TimeoutExpired("fixed-controller", timeout)
        return self.code

    def kill(self) -> None:
        assert not self.killed
        self.killed = True


class Start:
    def __init__(
        self, child: FakeChild, records: Records, clock: Clock, *, complete: bool = False
    ) -> None:
        self.child = child
        self.records = records
        self.clock = clock
        self.complete = complete
        self.calls = 0
        self.failure: BaseException | None = None

    def start(self, item: owned.CaptureSpec, path: Path, digest: str) -> FakeChild:
        self.calls += 1
        assert "capture-owner-intent.json" in self.records.records
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        request = json.loads(raw)
        assert request["unit"] == item.unit and request["started"] == 100.0
        assert request["deadline"] == 400.0
        if self.failure is not None:
            raise self.failure
        if self.complete:
            manager = Manager(self.records, self.clock)
            result = owned.execute(
                item,
                manager,
                self.records,
                self.clock.now,
                self.clock.sleep,
                self.clock.usage,
                original_start=100.0,
            )
            assert result["status"] == "provisional_complete", result
            self.records.raw["capture-request.json"] = (
                item.root / "capture-request.json"
            ).read_bytes()
        return self.child


class WatchManager(Manager):
    def stop(self, plan: Plan, invocation: str, timeout: float) -> None:
        assert invocation == INVOCATION
        assert "capture-owner-terminal.json" in self.records.records
        self.events.append("owner-stop")
        if self.stop_error is not None:
            raise self.stop_error
        self.stopped = True


@pytest.fixture(autouse=True)
def no_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Actual child/service/primitive forbidden")

    monkeypatch.setattr(owner.Controller, "start", denied)
    monkeypatch.setattr(Systemd, "command", denied)
    monkeypatch.setattr(owned, "preflight", lambda item: None)


def setup(
    tmp_path: Path,
    *,
    timeout: bool = False,
    complete: bool = False,
    code: int = 0,
    reap_error: bool = False,
) -> tuple[owned.CaptureSpec, Clock, Records, Start, WatchManager]:
    root = tmp_path / "run"
    root.mkdir(mode=0o700)
    item = spec(root)
    clock = Clock()
    records = Records(root, [])
    child = FakeChild(clock, timeout=timeout, code=code, reap_error=reap_error)
    return (
        item,
        clock,
        records,
        Start(child, records, clock, complete=complete),
        WatchManager(records, clock),
    )


def watch(
    values: tuple[owned.CaptureSpec, Clock, Records, Start, WatchManager],
) -> dict[str, object]:
    item, clock, records, start, manager = values
    return owner.watch(item, start, manager, records, clock.now, clock.sleep, clock.usage)


def test_independent_owner_arms_before_child_and_rejoins_actual_records(tmp_path: Path) -> None:
    values = setup(tmp_path, complete=True)
    item, clock, records, start, manager = values
    result = watch(values)
    assert result["status"] == "provisional_complete", result
    assert result["accepted"] is False and result["named_ownership_released"] is False
    assert result["child_reaped"] is True and result["cgroup_closed"] is True
    assert start.calls == 1 and not start.child.killed
    assert records.events.index("capture-owner-intent.json") < records.events.index(
        "capture-intent.json"
    )
    assert manager.submissions == 0 and clock.now() < 400
    assert (item.root / "capture-owner-request.json").stat().st_size < 4096


@pytest.mark.parametrize("initial_missing", (False, True), ids=("known", "late-ack"))
def test_cutoff_survives_blocked_controller_and_binds_late_named_unit(
    tmp_path: Path, initial_missing: bool
) -> None:
    values = setup(tmp_path, timeout=True)
    item, clock, records, start, manager = values
    plan = owned.fixed_plan(item, 100.0)
    queue = [
        state(plan, "running", populated=True),
        state(plan, "exited", populated=True, cpu=200),
        state(plan, "exited", cpu=300),
    ]
    manager.queue = deque(([MISSING] if initial_missing else []) + queue)
    result = watch(values)
    assert start.child.killed and start.child.waits == [240.0, 5.0]
    assert start.calls == 1 and manager.submissions == 0
    assert result["status"] == "incomplete" and result["cleanup_confirmed"] is True
    assert first(result)["kind"] == "TimeoutExpired"
    assert records.events.index("capture-owner-terminal.json") < records.events.index("owner-stop")
    assert "SIGTERM" in records.events and "SIGKILL" in records.events
    assert clock.now() < 400


@pytest.mark.parametrize(
    "kind",
    ("missing", "manager", "unreaped", "identity"),
    ids=("missing", "manager-stall", "unreaped", "identity"),
)
def test_unknown_closure_never_releases_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    values = setup(tmp_path, timeout=True, reap_error=kind == "unreaped")
    item, clock, records, start, manager = values
    plan = owned.fixed_plan(item, 100.0)
    if kind == "manager":

        def failed_snapshot(plan: Plan, timeout: float) -> Snapshot:
            clock.value = 401.0
            raise TimeoutError("synthetic manager stall")

        monkeypatch.setattr(manager, "snapshot", failed_snapshot)
    elif kind == "unreaped":
        manager.queue.append(state(plan, "exited", cpu=300))
    elif kind == "identity":
        manager.queue.extend(
            [state(plan, "running", populated=True), state(plan, "exited", invocation="f" * 32)]
        )
    result = watch(values)
    assert result["status"] == "incomplete" and result["accepted"] is False
    assert result["named_ownership_released"] is False and start.calls == 1
    if kind == "unreaped":
        assert result["child_reaped"] is False and result["cleanup_confirmed"] is True
        supplemental = result["supplemental"]
        assert type(supplemental) is list
        assert any(item["stage"] == "controller_reap" for item in supplemental)
    else:
        assert result["cleanup_confirmed"] is False
    assert first(result)["kind"] == "TimeoutExpired"


@pytest.mark.parametrize(
    "field",
    ("source", "invocation", "report", "status"),
    ids=("source", "invocation", "report", "status"),
)
def test_actual_child_record_substitution_is_not_acknowledgement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    values = setup(tmp_path, complete=True)
    _, _, records, start, _ = values
    original = start.start

    def changed(item: owned.CaptureSpec, path: Path, digest: str) -> FakeChild:
        child = original(item, path, digest)
        record = json.loads(records.raw["capture-final.json"])
        if field == "source":
            record["spec"]["source_commit"] = "0" * 40
        elif field == "invocation":
            record["invocation_id"] = "0" * 32
        elif field == "report":
            record["report_join"] = {}
        else:
            record["status"] = "complete"
        records.raw["capture-final.json"] = owned.encoded(record)
        return child

    monkeypatch.setattr(start, "start", changed)
    result = watch(values)
    assert result["status"] == "incomplete" and first(result)["kind"] == "ValueError"
    assert start.calls == 1


@pytest.mark.parametrize(
    "name",
    ("capture-owner-intent.json", "capture-owner-terminal.json", "capture-owner-final.json"),
    ids=("intent", "terminal", "final"),
)
def test_owner_receipt_failure_preserves_no_retry(tmp_path: Path, name: str) -> None:
    values = setup(tmp_path, timeout=True)
    item, _, records, start, manager = values
    records.fail = name
    manager.queue.append(state(owned.fixed_plan(item, 100.0), "exited", cpu=300))
    result = watch(values)
    assert result["status"] == "incomplete" and result["named_ownership_released"] is False
    assert start.calls == (0 if name.endswith("intent.json") else 1)
    if name.endswith("terminal.json"):
        assert manager.stopped is False


@pytest.mark.parametrize(
    "kind", ("root", "store", "existing"), ids=("public-root", "wrong-store", "consumed")
)
def test_preclaim_and_consumed_failures_have_no_child_or_manager_work(
    tmp_path: Path, kind: str
) -> None:
    values = setup(tmp_path)
    item, _, records, start, manager = values
    if kind == "root":
        item.root.chmod(0o755)
    elif kind == "store":
        records.root = item.root / "elsewhere"
    else:
        records.records["capture-owner-intent.json"] = {"prior": True}
    result = watch(values)
    assert result["intent_acknowledged"] is False
    assert start.calls == 0 and manager.submissions == 0
    assert "snapshot" not in records.events


def test_start_failure_keeps_named_unknown_and_cannot_retry(tmp_path: Path) -> None:
    values = setup(tmp_path)
    _, _, records, start, _ = values
    start.failure = OSError("child start acknowledgement unknown")
    result = watch(values)
    assert first(result)["kind"] == "OSError"
    assert result["child_reaped"] is False and result["cgroup_closed"] is False
    assert result["named_ownership_released"] is False
    before = list(records.events)
    again = watch(values)
    assert again["intent_acknowledged"] is False and start.calls == 1
    assert records.events[len(before) :] == ["capture-owner-intent.json"]


@pytest.mark.parametrize("secondary", (False, True), ids=("primary", "supplemental"))
def test_command_failure_preserves_underlying_first_and_close_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, secondary: bool
) -> None:
    values = setup(tmp_path, timeout=secondary)
    _, _, _, start, manager = values
    original = OSError("synthetic original command failure")
    close = Fault.capture("log_close", PermissionError("synthetic close uncertainty"))
    failure = CommandFailure(original, (close,))
    if secondary:

        def snapshot(plan: Plan, timeout: float) -> NoReturn:
            raise failure

        monkeypatch.setattr(manager, "snapshot", snapshot)
    else:
        start.failure = failure
    result = watch(values)
    assert first(result)["kind"] == ("TimeoutExpired" if secondary else "OSError")
    if not secondary:
        assert first(result)["detail"] == str(original)
    supplemental = result["supplemental"]
    assert type(supplemental) is list
    assert {
        "stage": "log_close",
        "kind": "PermissionError",
        "detail": "synthetic close uncertainty",
    } in supplemental
    if secondary:
        assert {
            "stage": "owner_reconcile",
            "kind": "OSError",
            "detail": str(original),
        } in supplemental



def retained_terminal_start(
    values: tuple[owned.CaptureSpec, Clock, Records, Start, WatchManager],
    monkeypatch: pytest.MonkeyPatch,
    *,
    failed: bool = True,
) -> Callable[[owned.CaptureSpec, Path, str], FakeChild]:
    """Produce real fake-controller receipts, then model the observed cleared group."""
    _, _, records, start, manager = values
    original = start.start

    def completed(item: owned.CaptureSpec, path: Path, digest: str) -> FakeChild:
        child = original(item, path, digest)
        terminal = json.loads(records.raw["capture-terminal-before-stop.json"])
        final = json.loads(records.raw["capture-final.json"])
        properties = terminal["snapshot"]["properties"]
        properties["ControlGroup"] = ""
        terminal["snapshot"]["populated"] = None
        if failed:
            properties.update(
                ActiveState="failed", SubState="failed", Result="exit-code", ExecMainStatus="1"
            )
            controller_fault = {
                "stage": "attempt", "kind": "ValueError", "detail": "Named service failed"
            }
            terminal.update(first_fault=controller_fault, report_join=None)
            final.update(status="incomplete", first_fault=controller_fault, report_join=None)
        records.raw["capture-terminal-before-stop.json"] = owned.encoded(terminal)
        records.raw["capture-final.json"] = owned.encoded(final)
        if failed:
            # Actual manager read after controller cleanup: quota files are gone.
            current = dict(properties)
            del current["ObservedCPUMax"]
            del current["ObservedCPUMaxBurst"]
            current["CPUUsageNSec"] = "350"
            manager.queue.append(Snapshot(current, None))
        return child

    monkeypatch.setattr(start, "start", completed)
    return completed


@pytest.mark.parametrize("failed", (False, True), ids=("success", "failed-child"))
def test_reaped_controller_rejoins_live_before_cleared_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: bool
) -> None:
    values = setup(tmp_path, complete=True, code=1 if failed else 0)
    item, _, records, start, manager = values
    retained_terminal_start(values, monkeypatch, failed=failed)
    result = watch(values)
    assert result["status"] == ("incomplete" if failed else "provisional_complete"), result
    assert result["accepted"] is False and result["named_ownership_released"] is False
    assert result["child_reaped"] is True and result["child_code"] == (1 if failed else 0)
    assert result["invocation_id"] == INVOCATION
    assert result["cgroup"] == "/user.slice/" + item.unit
    assert result["cgroup_closed"] is True and result["cleanup_confirmed"] is True
    assert result["cgroup_cpu_ns"] == (350 if failed else 300)
    assert start.calls == 1 and manager.submissions == 0 and not start.child.killed
    assert "owner-stop" not in records.events
    if failed:
        assert first(result)["detail"] == "Owned controller returned a failure"
        assert result["supplemental"] == []
        assert "read:capture-service.json" not in records.events
        saved = records.records["capture-owner-terminal.json"]["snapshot"]
        assert type(saved) is dict
        assert "ObservedCPUMax" not in saved["properties"]
    else:
        assert result["first_fault"] is None


@pytest.mark.parametrize(
    "case",
    (
        "missing-live", "malformed-live", "request", "source", "started", "profile",
        "unit", "invocation", "group", "quota", "burst", "decreasing-cpu",
        "terminal-cpu", "terminal-unit", "final-source", "boolean-cpu",
    ),
    ids=(
        "missing-live", "malformed-live", "request", "source", "started", "profile",
        "unit", "invocation", "group", "quota", "burst", "decreasing-cpu",
        "terminal-cpu", "terminal-unit", "final-source", "boolean-cpu",
    ),
)
def test_failed_child_cannot_adopt_unjoined_retained_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    values = setup(tmp_path, complete=True, code=1)
    _, _, records, start, manager = values
    completed = retained_terminal_start(values, monkeypatch)

    def changed(item: owned.CaptureSpec, path: Path, digest: str) -> FakeChild:
        child = completed(item, path, digest)
        if case == "missing-live":
            del records.raw["capture-observation-00.json"]
            return child
        if case == "malformed-live":
            records.raw["capture-observation-00.json"] = b"{"
            return child
        name = (
            "capture-request.json" if case == "request"
            else "capture-intent.json" if case in ("source", "started", "profile")
            else "capture-terminal-before-stop.json" if case.startswith("terminal-")
            else "capture-final.json" if case == "final-source"
            else "capture-observation-00.json"
        )
        record = json.loads(records.raw[name])
        if case == "request":
            record["unit"] = "different.service"
        elif case in ("source", "final-source"):
            record["spec"]["source_commit"] = "0" * 40
        elif case == "started":
            record["started"] = 99.0
        elif case == "profile":
            record["profile"]["cpu_quota_percent"] = 49
        elif case == "unit":
            record["unit"] = "different.service"
        elif case == "invocation":
            record["invocation_id"] = "f" * 32
            record["snapshot"]["properties"]["InvocationID"] = "f" * 32
        elif case == "group":
            record["cgroup"] = "/user.slice/different.service"
            record["snapshot"]["properties"]["ControlGroup"] = record["cgroup"]
        elif case in ("quota", "burst"):
            key = "ObservedCPUMax" if case == "quota" else "ObservedCPUMaxBurst"
            record["snapshot"]["properties"][key] = "60000 100000" if case == "quota" else "1"
        elif case == "decreasing-cpu":
            record["snapshot"]["properties"]["CPUUsageNSec"] = "400"
            record["cgroup_cpu_ns"] = 400
        elif case == "terminal-cpu":
            record["cgroup_cpu_ns"] = 301
        elif case == "terminal-unit":
            record["snapshot"]["properties"]["Id"] = "different.service"
        else:
            record["cgroup_cpu_ns"] = True
        records.raw[name] = owned.encoded(record)
        return child

    monkeypatch.setattr(start, "start", changed)
    result = watch(values)
    assert result["status"] == "incomplete" and result["accepted"] is False
    assert first(result)["detail"] == "Owned controller returned a failure"
    assert result["invocation_id"] is None and result["cgroup"] is None
    assert result["cgroup_closed"] is False and result["cleanup_confirmed"] is False
    assert start.calls == 1 and manager.submissions == 0 and not manager.stopped
    supplemental = result["supplemental"]
    assert type(supplemental) is list
    assert any(row["stage"] == "controller_receipts" for row in supplemental)


@pytest.mark.parametrize(
    "case", ("unit", "invocation", "group", "profile", "quota", "cpu"),
    ids=("unit", "invocation", "group", "profile", "quota", "cpu"),
)
def test_cleared_manager_snapshot_must_match_verified_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    values = setup(tmp_path, complete=True, code=1)
    _, _, _, start, manager = values
    completed = retained_terminal_start(values, monkeypatch)

    def changed(item: owned.CaptureSpec, path: Path, digest: str) -> FakeChild:
        child = completed(item, path, digest)
        current = manager.queue.pop()
        props = dict(current.properties)
        if case == "unit":
            props["Id"] = "different.service"
        elif case == "invocation":
            props["InvocationID"] = "f" * 32
        elif case == "group":
            props["ControlGroup"] = "/user.slice/different.service"
        elif case == "profile":
            props["CPUQuotaPerSecUSec"] = "600ms"
        elif case == "quota":
            props["ObservedCPUMax"] = "60000 100000"
        else:
            props["CPUUsageNSec"] = "299"
        manager.queue.append(Snapshot(props, None))
        return child

    monkeypatch.setattr(start, "start", changed)
    result = watch(values)
    assert first(result)["detail"] == "Owned controller returned a failure"
    assert result["status"] == "incomplete" and result["accepted"] is False
    assert result["cleanup_confirmed"] is False and not manager.stopped
    assert start.calls == 1 and manager.submissions == 0
    supplemental = result["supplemental"]
    assert type(supplemental) is list
    assert any(row["stage"] == "owner_reconcile" for row in supplemental)
