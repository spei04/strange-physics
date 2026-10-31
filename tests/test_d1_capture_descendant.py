"""Fake manager/owned descriptor adapters only; no actual fork, service or FIFO."""

from __future__ import annotations

import os
import stat
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from typing import NoReturn

import pytest

from scripts import d1_capture_descendant as benign
from scripts import d1_owned_capture as owned
from scripts.grid_q1_supervisor import CommandFailure, Fault, Plan, Systemd
from test_d1_owned_capture import INVOCATION, MISSING, Clock, Manager, Records, state


class Exit(BaseException):
    def __init__(self, code: int) -> None:
        self.code = code


class FakeHandshake:
    def __init__(self, records: Records, plan: benign.DescendantPlan) -> None:
        self.records = records
        self.plan = plan
        self.prepared = self.released = False
        self.bad_ready = False
        self.fail_release = False

    def prepare(self, plan: benign.DescendantPlan) -> None:
        assert plan is self.plan and "descendant-intent.json" in self.records.records
        assert not self.prepared
        self.prepared = True

    def ready(self) -> dict[str, object]:
        assert self.prepared
        return {"schema": "d1-descendant-ready-v1", "unit": self.plan.unit,
                "invocation_id": INVOCATION, "cgroup": "/user.slice/" + self.plan.unit,
                "token": "f" * 64 if self.bad_ready else self.plan.token}

    def done(self) -> dict[str, object]:
        return {"schema": "d1-descendant-done-v1", "unit": self.plan.unit,
                "invocation_id": INVOCATION, "cgroup": "/user.slice/" + self.plan.unit,
                "token": self.plan.token, "exit_code": 0, "first_fault": None, "supplemental": []}

    def release(self, token: str) -> None:
        assert token == self.plan.token and "descendant-populated.json" in self.records.records
        assert not self.released
        self.released = True
        if self.fail_release:
            raise OSError("synthetic lost release acknowledgement")


class FakeManager(Manager):
    def submit(self, plan: Plan, timeout: float) -> None:
        self.submissions += 1
        assert self.submissions == 1
        self.events.append("submit")
        if not self.queue:
            self.queue.extend([state(plan, "exited", populated=True), state(plan, "exited", cpu=200)])

    def stop(self, plan: Plan, invocation: str, timeout: float) -> None:
        assert invocation == INVOCATION and "descendant-terminal.json" in self.records.records
        self.events.append("stop")
        self.stopped = True


def plan(root: Path) -> benign.DescendantPlan:
    root.chmod(0o700)
    return benign.DescendantPlan(
        root=root, admission_sha256="a" * 64, controller_sha256="b" * 64,
        interpreter=Path("/synthetic/python"), token="c" * 64, started=100.0,
        runtime_seconds=240, start_timeout_seconds=5, stop_timeout_seconds=5,
        cpu_quota_percent=50, quota_period_us=100_000, cpu_watch_ns=120_000_000_000,
        poll_seconds=4, observations=60, command_seconds=5, term_grace_seconds=2,
        terminal_seconds=300, service_file_bytes=1024 * 1024,
    )


@pytest.fixture(autouse=True)
def no_live_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Live manager/pipe operation forbidden")
    monkeypatch.setattr(Systemd, "command", denied)
    monkeypatch.setattr(benign.PipeHandshake, "prepare", denied)
    monkeypatch.setattr(benign.PipeHandshake, "release", denied)


@pytest.mark.parametrize("kind", ("pass", "leader-only", "wrong-ready", "lost-release", "terminal-failed", "late"), ids=("pass", "leader-only", "wrong-ready", "lost-release", "receipt", "late"))
def test_benign_witness_requires_live_descendant_and_bound_release(tmp_path: Path, kind: str) -> None:
    item = plan(tmp_path)
    clock = Clock()
    records = Records(tmp_path, [])
    manager = FakeManager(records, clock)
    handshake = FakeHandshake(records, item)
    if kind == "leader-only":
        manager.queue = deque([state(item, "exited")])
        # The initial absence observation must still precede submission.
        manager.queue.appendleft(MISSING)
    elif kind == "wrong-ready":
        handshake.bad_ready = True
    elif kind == "lost-release":
        handshake.fail_release = True
    elif kind == "terminal-failed":
        records.fail = "descendant-terminal.json"
    elif kind == "late":
        clock.value = 130.0
    result = benign.watch_descendant(item, manager, records, handshake, clock.now, clock.sleep)
    assert result["status"] == ("provisional_complete" if kind == "pass" else "incomplete")
    assert result["accepted"] is False
    if kind == "pass":
        assert result["witnessed_populated_after_leader_exit"] is True
        assert result["release_acknowledged"] is True and result["cleanup_confirmed"] is True
        assert records.events.index("descendant-populated.json") < records.events.index("descendant-terminal.json") < records.events.index("stop")
    if kind in ("leader-only", "wrong-ready", "late"):
        assert not handshake.released
    if kind == "terminal-failed":
        assert not manager.stopped
    assert manager.submissions == (0 if kind == "late" else 1)


@pytest.mark.parametrize("kind", ("leader", "child", "timeout", "bad-token", "fork-failed", "close-failed", "parent-close", "child-ready-close", "read-close"), ids=("leader", "child", "timeout", "bad-token", "fork", "close", "parent-close", "ready-close", "read-close"))
def test_fixed_worker_fake_descriptors_preserve_order_and_owned_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    item = plan(tmp_path)
    path = tmp_path / "descendant-request.json"
    path.write_bytes(item.request)
    path.chmod(0o600)
    events: list[tuple[str, object]] = []
    read_error = OSError("synthetic ready read failure")
    late_close_error = PermissionError("synthetic lost close acknowledgement")

    def fork() -> int:
        events.append(("fork", 0))
        if kind == "fork-failed":
            raise OSError("synthetic fork refusal")
        return 42 if kind in ("leader", "parent-close", "read-close") else 0

    def close(fd: int) -> None:
        events.append(("close", fd))
        if (kind == "close-failed" and fd == 20) or (kind in ("parent-close", "child-ready-close") and fd == 11) or (kind == "read-close" and fd == 10):
            raise late_close_error

    def read(fd: int, size: int) -> bytes:
        events.append(("read", fd))
        if kind == "read-close":
            raise read_error
        if kind == "leader":
            return b"R"
        return (("f" * 64 if kind == "bad-token" else item.token) + "\n").encode()

    def write(fd: int, raw: bytes) -> int:
        events.append(("write", (fd, raw)))
        return len(raw)

    def exit_child(code: int) -> NoReturn:
        events.append(("exit", code))
        raise Exit(code)

    fake_os = SimpleNamespace(
        pipe=lambda: (10, 11), fork=fork, close=close, read=read, write=write,
        open=lambda *args: 20, getuid=os.getuid,
        fstat=lambda fd: SimpleNamespace(st_mode=stat.S_IFIFO | 0o600, st_uid=os.getuid()),
        O_RDWR=os.O_RDWR, O_NONBLOCK=os.O_NONBLOCK, O_NOFOLLOW=os.O_NOFOLLOW, _exit=exit_child,
    )
    def selected(readers: list[int], writers: list[int], errors: list[int], timeout: float) -> tuple[list[int], list[int], list[int]]:
        events.append(("select", tuple(readers)))
        assert 0 <= timeout <= 30
        return ([] if kind == "timeout" else readers), [], []

    with monkeypatch.context() as scoped:
        scoped.setattr(benign, "os", fake_os)
        scoped.setattr(benign, "select", SimpleNamespace(select=selected))
        scoped.setattr(benign, "time", SimpleNamespace(monotonic=lambda: 100.0))
        scoped.setattr(benign, "sys", SimpleNamespace(flags=SimpleNamespace(isolated=1, dont_write_bytecode=1)))
        scoped.setattr(owned, "service_identity", lambda unit: (INVOCATION, "/user.slice/" + unit))
        if kind == "leader":
            assert benign.worker(path, item.request_sha256) == 0
            assert events[-1] == ("close", 10)
            assert not (tmp_path / "descendant-ready.json").exists()
        elif kind == "parent-close":
            with pytest.raises(PermissionError) as raised_parent:
                benign.worker(path, item.request_sha256)
            assert raised_parent.value is late_close_error
            assert events.count(("close", 11)) == 1 and events.count(("close", 10)) == 1
            assert not any(event[0] == "select" for event in events)
        elif kind == "read-close":
            with pytest.raises(CommandFailure) as raised_pair:
                benign.worker(path, item.request_sha256)
            assert raised_pair.value.primary is read_error
            assert raised_pair.value.supplemental == (Fault.capture("worker_close", late_close_error),)
            assert events.count(("close", 10)) == events.count(("close", 11)) == 1
        elif kind == "fork-failed":
            with pytest.raises(OSError, match="fork refusal"):
                benign.worker(path, item.request_sha256)
            assert events[-2:] == [("close", 10), ("close", 11)]
        else:
            with pytest.raises(Exit) as raised:
                benign.worker(path, item.request_sha256)
            assert raised.value.code == (0 if kind == "child" else 1)
            assert ("write", (11, b"R")) in events
            if kind == "child-ready-close":
                assert not any(event[0] == "select" for event in events)
                assert events.count(("close", 11)) == 1
            else:
                assert events.index(("write", (11, b"R"))) < events.index(("select", (20,)))
            assert ("close", 20) in events
            ready = owned.decoded((tmp_path / "descendant-ready.json").read_bytes(), 4096)
            assert ready["token"] == item.token and ready["invocation_id"] == INVOCATION
            done = owned.decoded((tmp_path / "descendant-done.json").read_bytes(), 4096)
            assert done["exit_code"] == raised.value.code
            if kind in ("close-failed", "child-ready-close"):
                assert done["first_fault"] == {"stage": "worker_close", "kind": "PermissionError", "detail": str(late_close_error)}
                assert done["supplemental"] == []
    assert os.close is not close


def test_benign_command_failure_preserves_primary_and_close_facts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    item = plan(tmp_path)
    clock = Clock()
    records = Records(tmp_path, [])
    manager = FakeManager(records, clock)
    handshake = FakeHandshake(records, item)
    original = manager.submit
    first = OSError("synthetic submit acknowledgement lost")
    close = Fault.capture("log_close", PermissionError("synthetic close failure"))

    def submit(value: Plan, timeout: float) -> NoReturn:
        original(value, timeout)
        raise CommandFailure(first, (close,))

    monkeypatch.setattr(manager, "submit", submit)
    result = benign.watch_descendant(item, manager, records, handshake, clock.now, clock.sleep)
    assert result["first_fault"] == {"stage": "benign", "kind": "OSError", "detail": str(first)}
    assert result["supplemental"] == [{"stage": "log_close", "kind": "PermissionError", "detail": "synthetic close failure"}]
    assert result["status"] == "incomplete" and manager.submissions == 1
    assert result["cleanup_confirmed"] is True and not handshake.released
