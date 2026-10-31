"""Owned synthetic records and fake systemd APIs; no service or primitive runs."""

from __future__ import annotations

import ast
import hashlib
import json
from collections import deque
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import NoReturn

import pytest

from scripts import d1_bootstrap_control as capture
from scripts import d1_owned_capture as owned
from scripts.grid_q1_supervisor import Plan, Snapshot, Systemd

INVOCATION = "c" * 32
MISSING = Snapshot({"LoadState": "not-found", "ActiveState": "inactive"}, None)


def spec(root: Path) -> owned.CaptureSpec:
    root.chmod(0o700)
    assert len(str(root)) <= 512
    return owned.CaptureSpec(root, Path("/synthetic/source"), Path("/synthetic/python"),
                             Path("/synthetic/protected-plan.json"), "a" * 64, "b" * 40,
                             "d" * 64, "e" * 64, "f" * 64, "1" * 64)


class Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0
        self.value += seconds

    def usage(self) -> dict[str, float]:
        return {"parent_cpu_seconds": self.value / 100, "waited_cli_cpu_seconds": self.value / 200}


def state(plan: Plan, phase: str, *, populated: bool | None = False,
          invocation: str = INVOCATION, cpu: int = 100, failed: bool = False) -> Snapshot:
    return Snapshot({
        **plan.required, "Id": plan.unit, "LoadState": "loaded",
        "ActiveState": "failed" if failed else "active", "SubState": phase,
        "InvocationID": invocation, "ControlGroup": "/user.slice/" + plan.unit,
        "CPUUsageNSec": str(cpu), "RuntimeMaxUSec": "240s", "RuntimeRandomizedExtraUSec": "0",
        "TimeoutStartUSec": "5s", "TimeoutStopUSec": "5s", "CPUQuotaPerSecUSec": "500ms",
        "CPUQuotaPeriodUSec": "100ms", "ObservedCPUMax": "50000 100000",
        "ObservedCPUMaxBurst": "0", "Result": "exit-code" if failed else "success",
        "ExecMainCode": "1", "ExecMainStatus": "1" if failed else "0",
        "ExecMainStartTimestampMonotonic": "1",
        "ExecMainExitTimestampMonotonic": "2" if phase in ("exited", "failed") else "0",
    }, populated)


class Records:
    def __init__(self, root: Path, events: list[str], *, real: bool = False) -> None:
        self.root = root
        self.events = events
        self.records: dict[str, dict[str, object]] = {}
        self.raw: dict[str, bytes] = {}
        self.fail: str | None = None
        self.real = owned.CaptureFiles(root) if real else None

    def write(self, name: str, record: dict[str, object]) -> None:
        self.events.append(name)
        if name == self.fail:
            raise OSError("synthetic persistence failure: " + name)
        if name in self.records:
            raise FileExistsError(name)
        self.records[name] = record
        self.raw[name] = owned.encoded(record)
        if self.real is not None:
            self.real.write(name, record)

    def read(self, name: str, maximum: int) -> bytes:
        self.events.append("read:" + name)
        if self.real is not None:
            return self.real.read(name, maximum)
        raw = self.raw[name]
        assert len(raw) <= maximum
        return raw


def child_report(item: owned.CaptureSpec) -> bytes:
    return (json.dumps({"kind": "d1-capture-only", "source_commit": item.source_commit,
                       "owners": 13, "original_methods": 22, "emitter": "math.exp",
                       "primitive_calls_permitted": False, "retention_activated": False}) + "\n").encode()


def service_report(plan: owned.CapturePlan, records: Records, clock: Clock) -> None:
    raw = child_report(plan.spec)
    records.raw["capture/child.log"] = raw
    if records.real is not None:
        target = plan.root / "capture"
        target.mkdir(mode=0o700)
        (target / "child.log").write_bytes(raw)
        (target / "child.log").chmod(0o600)
    records.write("capture-service.json", {
        "schema": "d1-owned-capture-service-v1", "spec": plan.spec.record(), "unit": plan.unit,
        "invocation_id": INVOCATION, "cgroup": "/user.slice/" + plan.unit,
        "request_sha256": plan.request_sha256, "started": 100.0, "deadline": 400.0,
        "observed_at": clock.now(),
        "launch": asdict(capture.LaunchResult(0, True, False, True, len(raw), 1.0, 0.1,
                                              True, None, False, "outer_owned_tree_closure_unproved")),
        "bootstrap_report_sha256": hashlib.sha256(raw).hexdigest(), "bootstrap_report_bytes": len(raw),
        "first_fault": None,
    })


class Manager:
    def __init__(self, records: Records, clock: Clock) -> None:
        self.records = records
        self.clock = clock
        self.events = records.events
        self.queue: deque[Snapshot] = deque()
        self.submissions = 0
        self.stopped = False
        self.last = MISSING
        self.after = MISSING
        self.submit_error: BaseException | None = None
        self.stop_error: BaseException | None = None
        self.mutation: str | None = None

    def snapshot(self, plan: Plan, timeout: float) -> Snapshot:
        assert 0 < timeout <= 5
        self.events.append("snapshot")
        if self.stopped:
            return self.after
        if self.queue:
            self.last = self.queue.popleft()
        return self.last

    def submit(self, plan: Plan, timeout: float) -> None:
        assert isinstance(plan, owned.CapturePlan)
        self.submissions += 1
        self.events.append("submit")
        service_report(plan, self.records, self.clock)
        if self.mutation is not None:
            raw = self.records.raw["capture-service.json"]
            record = json.loads(raw)
            if self.mutation == "source": record["spec"]["source_commit"] = "0" * 40
            elif self.mutation == "root": record["spec"]["root"] = "/another"
            elif self.mutation == "plan": record["spec"]["protected_plan_sha256"] = "0" * 64
            elif self.mutation == "admission": record["spec"]["admission_sha256"] = "0" * 64
            elif self.mutation == "invocation": record["invocation_id"] = "0" * 32
            elif self.mutation == "group": record["cgroup"] = "/other"
            elif self.mutation == "late": record["observed_at"] = 400.0
            elif self.mutation == "inner-accept": record["launch"]["captured"] = True
            elif self.mutation == "stdout": self.records.raw["capture/child.log"] += b"changed"
            else: raise AssertionError(self.mutation)
            self.records.raw["capture-service.json"] = owned.encoded(record)
        if not self.queue:
            self.queue.extend([state(plan, "running", populated=True),
                               state(plan, "exited", populated=True, cpu=200),
                               state(plan, "exited", populated=False, cpu=300)])
        if self.submit_error is not None:
            raise self.submit_error

    def signal(self, plan: Plan, invocation: str, signal_name: str, timeout: float) -> None:
        assert invocation == INVOCATION and signal_name in ("SIGTERM", "SIGKILL")
        self.events.append(signal_name)

    def stop(self, plan: Plan, invocation: str, timeout: float) -> None:
        assert invocation == INVOCATION
        assert "capture-terminal-before-stop.json" in self.records.records
        self.events.append("stop")
        if self.stop_error is not None:
            raise self.stop_error
        self.stopped = True


@pytest.fixture(autouse=True)
def no_real_service_or_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Real process/service/capture forbidden")
    monkeypatch.setattr(Systemd, "command", denied)
    monkeypatch.setattr(capture, "launch", denied)


@pytest.fixture
def preflight_api(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []
    def read(path: Path, digest: str) -> dict[str, object]:
        calls.append("read")
        return {"source_commit": "b" * 40, "checkout": "/synthetic/source",
                "controller_interpreter": "/synthetic/python",
                "controller": "/synthetic/source/scripts/d1_bootstrap_control.py",
                "bootstrap": "/synthetic/source/tests/d1_bootstrap.py",
                "venv_root": "/synthetic/venv", "stdlib": "/synthetic/stdlib"}
    def validate(value: dict[str, object]) -> dict[str, str]:
        calls.append("validate")
        return {"/synthetic/source/scripts/d1_owned_capture.py": "e" * 64,
                "/synthetic/source/scripts/d1_bootstrap_control.py": "f" * 64,
                "/synthetic/source/tests/d1_bootstrap.py": "1" * 64}
    monkeypatch.setattr(capture, "read_plan", read)
    monkeypatch.setattr(capture, "validate_plan", validate)
    return calls


def run(item: owned.CaptureSpec, manager: Manager, records: Records, clock: Clock) -> dict[str, object]:
    result = owned.execute(item, manager, records, clock.now, clock.sleep, clock.usage)
    request = item.root / "capture-request.json"
    if request.exists():
        assert request.stat().st_size <= 4096
    return result


def test_fixed_lifecycle_retains_before_cleanup_and_never_accepts_populated(
    tmp_path: Path, preflight_api: list[str],
) -> None:
    item = spec(tmp_path); clock = Clock(); events: list[str] = []
    records = Records(tmp_path, events, real=True); manager = Manager(records, clock)
    result = run(item, manager, records, clock)
    assert preflight_api == ["read", "validate"] and manager.submissions == 1
    assert result["status"] == "provisional_complete" and result["accepted"] is False
    assert result["cgroup_closed"] is True and result["cleanup_confirmed"] is True
    assert events.index("capture-intent.json") < events.index("submit")
    assert events.index("capture-observation-02.json") < events.index("read:capture-service.json")
    assert events.index("capture-terminal-before-stop.json") < events.index("stop") < events.index("capture-final.json")
    terminal = records.records["capture-terminal-before-stop.json"]
    assert terminal["cgroup_cpu_ns"] == 300 and terminal["scopes_not_added"] is True
    assert (tmp_path / "capture-terminal-before-stop.json").is_file()


def test_disabled_cli_and_exact_future_command(tmp_path: Path) -> None:
    item = spec(tmp_path)
    plan = owned.CapturePlan(root=tmp_path, admission_sha256=item.admission_sha256,
          controller_sha256=item.adapter_sha256, spec=item, request_sha256="2" * 64,
          runtime_seconds=240, start_timeout_seconds=5, stop_timeout_seconds=5,
          cpu_quota_percent=50, quota_period_us=100000, cpu_watch_ns=120000000000,
          poll_seconds=4, observations=60, command_seconds=5, term_grace_seconds=2,
          terminal_seconds=300, service_file_bytes=1048576)
    assert owned.main() == 64
    assert plan.argv == ["/synthetic/python", "-I", "-B", "-X",
                         f"pycache_prefix={tmp_path / 'service-pycache'}",
                         "/synthetic/source/scripts/d1_owned_capture.py",
                         "service", str(tmp_path / "capture-request.json"), "2" * 64]
    with pytest.raises(ValueError, match="Fixed capture"):
        replace(plan, runtime_seconds=239)


def test_preflight_exhaustion_has_intent_but_zero_submissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, preflight_api: list[str],
) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    original = owned.preflight
    def late(value: owned.CaptureSpec) -> None:
        original(value); clock.value = 401.0
    monkeypatch.setattr(owned, "preflight", late)
    result = run(item, manager, records, clock)
    assert preflight_api == ["read", "validate"] and manager.submissions == 0
    assert "capture-intent.json" in records.records and result["status"] == "incomplete"


@pytest.mark.parametrize("kind", ("source", "root", "plan", "admission", "invocation", "group", "late", "inner-accept", "stdout"),
                         ids=("source", "root", "plan", "admission", "invocation", "group", "late", "inner", "stdout"))
def test_report_join_cannot_be_substituted(tmp_path: Path, preflight_api: list[str], kind: str) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    manager.mutation = kind
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and result["report_join"] is None
    assert manager.submissions == 1 and manager.stopped


def test_lost_acknowledgement_is_not_retry_or_success(tmp_path: Path, preflight_api: list[str]) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    manager.submit_error = OSError("lost submission acknowledgement")
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and manager.submissions == 1 and manager.stopped
    assert result["first_fault"] == {"stage": "attempt", "kind": "OSError", "detail": "lost submission acknowledgement"}
    assert "SIGTERM" in records.events and result["report_join"] is None


@pytest.mark.parametrize("name", ("capture-terminal-before-stop.json", "capture-final.json"), ids=("terminal", "final"))
def test_receipt_failure_stays_incomplete(tmp_path: Path, preflight_api: list[str], name: str) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    records.fail = name
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and result["accepted"] is False
    assert manager.stopped is (name == "capture-final.json")


def test_cleanup_failure_cannot_promote_capture(tmp_path: Path, preflight_api: list[str]) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    manager.stop_error = PermissionError("synthetic stop failure")
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and result["cleanup_confirmed"] is False
    assert result["first_fault"] == {"stage": "stop", "kind": "PermissionError", "detail": "synthetic stop failure"}


def test_existing_intent_does_not_dispatch_again(tmp_path: Path, preflight_api: list[str]) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    run(item, manager, records, clock)
    before = set(records.records)
    result = run(item, manager, records, clock)
    assert result["reason"] == "exclusive_intent_exists" and manager.submissions == 1
    assert set(records.records) == before


@pytest.mark.parametrize("kind", ("stale", "cpu", "group", "disappeared", "failed"), ids=("stale", "cpu", "group", "missing", "failed"))
def test_snapshot_identity_and_failed_outcomes_remain_nonaccepting(
    tmp_path: Path, preflight_api: list[str], monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    original = manager.submit
    def submit(plan: Plan, timeout: float) -> None:
        original(plan, timeout)
        first = state(plan, "running", populated=True, cpu=200)
        last = state(plan, "exited", cpu=300)
        if kind == "stale": last.properties["InvocationID"] = "0" * 32
        elif kind == "cpu": last.properties["CPUUsageNSec"] = "100"
        elif kind == "group": last.properties["ControlGroup"] = "/other"
        elif kind == "disappeared": first = state(plan, "exited", populated=None)
        else:
            last = state(plan, "failed", cpu=300, failed=True)
            manager.after = state(plan, "failed", cpu=301, failed=True)
        manager.queue = deque([first, last])
    monkeypatch.setattr(manager, "submit", submit)
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and manager.submissions == 1
    if kind == "failed":
        assert manager.stopped and result["cleanup_confirmed"] is True
        assert result["terminal_cgroup_cpu_ns"] == 300


@pytest.mark.parametrize("kind", ("invocation", "group", "populated"), ids=("invocation", "group", "populated"))
def test_poststop_observation_must_still_match(tmp_path: Path, preflight_api: list[str], kind: str) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    props = {"LoadState": "loaded", "ActiveState": "inactive"}
    if kind == "invocation": props["InvocationID"] = "0" * 32
    if kind == "group": props["ControlGroup"] = "/other"
    manager.after = Snapshot(props, kind == "populated")
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and result["cleanup_confirmed"] is False


def test_service_entry_wraps_fake_launch_and_retains_exact_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = spec(tmp_path); request = {"schema": "d1-capture-request-v1", "spec": item.record(),
        "unit": item.unit, "started": 100.0, "deadline": 400.0}
    raw = owned.encoded(request); path = tmp_path / "capture-request.json"
    assert len(raw) <= 4096
    path.write_bytes(raw); path.chmod(0o600)
    (tmp_path / "service-pycache").mkdir(mode=0o700)
    calls: list[Path] = []
    def launch(plan_path: Path, digest: str, output: Path) -> capture.LaunchResult:
        calls.append(output); output.mkdir(mode=0o700)
        body = child_report(item); target = output / "child.log"
        target.write_bytes(body); target.chmod(0o600)
        return capture.LaunchResult(0, True, False, True, len(body), 1.0, 0.1,
                                    True, None, False, "outer_owned_tree_closure_unproved")
    with monkeypatch.context() as scoped:
        scoped.setattr(owned, "service_identity", lambda unit: (INVOCATION, "/user.slice/" + unit))
        scoped.setattr(owned, "sys", SimpleNamespace(
            flags=SimpleNamespace(isolated=1, dont_write_bytecode=1),
            pycache_prefix=str(tmp_path / "service-pycache")))
        scoped.setattr(capture, "launch", launch)
        scoped.setattr(owned, "time", SimpleNamespace(monotonic=lambda: 101.0))
        scoped.setenv("INVOCATION_ID", INVOCATION)
        assert owned.service_entry(path, hashlib.sha256(raw).hexdigest()) == 0
    value = json.loads((tmp_path / "capture-service.json").read_bytes())
    assert calls == [tmp_path / "capture"]
    assert value["invocation_id"] == INVOCATION and value["launch"]["captured"] is False
    assert value["bootstrap_report_sha256"] == hashlib.sha256(child_report(item)).hexdigest()


@pytest.mark.parametrize("kind", ("source", "adapter", "controller", "bootstrap"), ids=("source", "adapter", "controller", "bootstrap"))
def test_preflight_joins_actual_validation_map_to_fixed_sources(
    tmp_path: Path, preflight_api: list[str], kind: str,
) -> None:
    item = spec(tmp_path)
    if kind == "source": changed = replace(item, source_commit="0" * 40)
    elif kind == "adapter": changed = replace(item, adapter_sha256="0" * 64)
    elif kind == "controller": changed = replace(item, controller_sha256="0" * 64)
    else: changed = replace(item, bootstrap_sha256="0" * 64)
    with pytest.raises(ValueError):
        owned.preflight(changed)
    assert preflight_api == ["read", "validate"]


def test_existing_named_unit_prevents_submission(tmp_path: Path, preflight_api: list[str]) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, []); manager = Manager(records, clock)
    manager.last = Snapshot({"LoadState": "loaded", "ActiveState": "inactive"}, None)
    result = run(item, manager, records, clock)
    assert result["status"] == "incomplete" and manager.submissions == 0 and not manager.stopped


@pytest.mark.parametrize("receipt_failure", (False, True), ids=("retained", "receipt-failed"))
def test_service_failure_keeps_first_and_supplemental_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, receipt_failure: bool,
) -> None:
    item = spec(tmp_path); request = {"schema": "d1-capture-request-v1", "spec": item.record(),
        "unit": item.unit, "started": 100.0, "deadline": 400.0}
    raw = owned.encoded(request); path = tmp_path / "capture-request.json"
    assert len(raw) <= 4096
    path.write_bytes(raw); path.chmod(0o600); (tmp_path / "service-pycache").mkdir(mode=0o700)
    calls: list[str] = []
    def failed_launch(plan_path: Path, digest: str, output: Path) -> NoReturn:
        calls.append("launch")
        raise OSError("first synthetic capture failure")
    def failed_write(self: owned.CaptureFiles, name: str, record: dict[str, object]) -> NoReturn:
        raise PermissionError("supplemental synthetic receipt failure")
    with monkeypatch.context() as scoped:
        scoped.setattr(capture, "launch", failed_launch)
        scoped.setattr(owned, "service_identity", lambda unit: (INVOCATION, "/user.slice/" + unit))
        scoped.setattr(owned, "sys", SimpleNamespace(
            flags=SimpleNamespace(isolated=1, dont_write_bytecode=1),
            pycache_prefix=str(tmp_path / "service-pycache")))
        scoped.setattr(owned, "time", SimpleNamespace(monotonic=lambda: 101.0))
        if receipt_failure:
            scoped.setattr(owned.CaptureFiles, "write", failed_write)
            with pytest.raises(owned.ServiceReceiptFailure) as raised:
                owned.service_entry(path, hashlib.sha256(raw).hexdigest())
            assert raised.value.first.kind == "OSError"
            assert raised.value.first.detail == "first synthetic capture failure"
            assert raised.value.supplemental.kind == "PermissionError"
        else:
            assert owned.service_entry(path, hashlib.sha256(raw).hexdigest()) == 1
    assert calls == ["launch"]
    if not receipt_failure:
        value = json.loads((tmp_path / "capture-service.json").read_bytes())
        assert value["launch"] is None and value["first_fault"]["kind"] == "OSError"


def test_import_path_setup_is_guarded_by_direct_script_entry() -> None:
    tree = ast.parse(Path(owned.__file__).read_text(encoding="utf-8"))
    expected_call = ast.parse("sys.path.insert", mode="eval")
    expected_guard = ast.parse('__name__ == "__main__"', mode="eval")
    assert isinstance(expected_call, ast.Expression) and isinstance(expected_guard, ast.Expression)
    mutations = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and ast.dump(node.func) == ast.dump(expected_call.body)]
    assert len(mutations) == 1
    guards = [node for node in tree.body if isinstance(node, ast.If)
              and ast.dump(node.test) == ast.dump(expected_guard.body)
              and mutations[0] in list(ast.walk(node))]
    assert len(guards) == 1 and not guards[0].orelse
    assert len(guards[0].body) == 1 and isinstance(guards[0].body[0], ast.Expr)
    assert guards[0].body[0].value is mutations[0]


@pytest.mark.parametrize("kind", ("public-root", "wrong-store"), ids=("public", "store"))
def test_preintent_rejection_never_writes_or_preflights(
    tmp_path: Path, preflight_api: list[str], kind: str,
) -> None:
    item = spec(tmp_path); clock = Clock(); events: list[str] = []
    records = Records(tmp_path if kind == "public-root" else tmp_path / "different", events)
    manager = Manager(records, clock)
    if kind == "public-root":
        tmp_path.chmod(0o755)
    result = run(item, manager, records, clock)
    assert result["reason"] == "pre_intent_validation_failed"
    assert result["intent_attempted"] is False and result["intent_acknowledged"] is False
    assert result["first_fault"] is not None and result["no_retry"] is True
    assert events == [] and preflight_api == [] and manager.submissions == 0
    assert not records.records and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("partial", (False, True), ids=("before", "partial"))
def test_unacknowledged_intent_has_no_followup_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, preflight_api: list[str], partial: bool,
) -> None:
    item = spec(tmp_path); clock = Clock(); records = Records(tmp_path, [])
    manager = Manager(records, clock)
    def failed_intent(name: str, record: dict[str, object]) -> NoReturn:
        assert name == "capture-intent.json"
        records.events.append(name)
        if partial:
            records.records[name] = record
        raise OSError("intent write acknowledgement lost")
    monkeypatch.setattr(records, "write", failed_intent)
    result = run(item, manager, records, clock)
    assert result["reason"] == "intent_acknowledgement_unknown"
    assert result["intent_attempted"] is True and result["intent_acknowledged"] is False
    assert result["first_fault"] == {"stage": "attempt", "kind": "OSError",
                                     "detail": "intent write acknowledgement lost"}
    assert result["no_retry"] is True and result["dispatch_attempted"] is False
    assert records.events == ["capture-intent.json"] and preflight_api == []
    assert bool(records.records) is partial and manager.submissions == 0
    assert list(tmp_path.iterdir()) == []
