"""Small owned files and synthetic faults; no source authentication or power-loss proof."""

from __future__ import annotations

import builtins
import errno
import hashlib
import os
import threading
from collections.abc import Iterator
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, NoReturn

import d1_primitive_sink as sink
import pytest


@pytest.fixture(autouse=True)
def no_scientific_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__
    forbidden = (
        "endpoint_belief_reference",
        "d1_fixture_reference",
        "d1_prefix_evidence",
        "strange_physics.native_prediction",
        "strange_physics.native_endpoint_beliefs",
        "strange_physics.finite_log_weights",
        "strange_physics.simulation",
    )

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] | list[str] = (),
        level: int = 0,
    ) -> Any:
        if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden):
            raise AssertionError("Context observation cannot import scientific producers")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


@pytest.fixture
def owned_sink(tmp_path: Path) -> Iterator[sink.PrimitiveFileSink]:
    tmp_path.chmod(0o700)
    context = sink.SinkContext(
        "recorder-a",
        "run-a",
        "a" * 40,
        "b" * 40,
        "c" * 64,
        "d" * 64,
        "e" * 64,
        "f" * 64,
        4,
        32768,
    )
    value = sink.PrimitiveFileSink.create(tmp_path / "sink", context)
    anchor_fds = (value._anchor.parent, value._anchor.directory)
    original_fstat = os.fstat
    try:
        yield value
    finally:
        if not value.snapshot().finish_consumed:
            value.finish()
        for descriptor in anchor_fds:
            assert descriptor is not None
            with pytest.raises(OSError) as closed:
                original_fstat(descriptor)
            assert closed.value.errno == errno.EBADF


def deny_read(*args: object, **kwargs: object) -> NoReturn:
    raise AssertionError("Consumed or non-idle observation must not read C")


def test_idle_repeats_read_exact_bytes_without_events_or_anchor_transfer(
    owned_sink: sink.PrimitiveFileSink,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = owned_sink
    expected = (tmp_path / "sink/context.json").read_bytes()
    before = value.snapshot()
    original_read = os.read
    read_fds: list[int] = []

    def tracked_read(fd: int, count: int) -> bytes:
        read_fds.append(fd)
        return original_read(fd, count)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", tracked_read)
        first = value.observe_context()
        second = value.observe_context()
    assert first == second and first is not second
    assert first.raw == expected and first.sha256 == hashlib.sha256(expected).hexdigest()
    assert first.byte_length == len(expected) <= sink.CONTEXT_BYTES
    assert len(read_fds) == 2 and value.snapshot() == before
    assert not hasattr(first, "__dict__")
    malformed: Any = first
    with pytest.raises(FrozenInstanceError):
        malformed.raw = b"substituted"
    for descriptor in (value._anchor.parent, value._anchor.directory):
        assert descriptor is not None
        os.fstat(descriptor)
    assert sorted(p.name for p in (tmp_path / "sink").iterdir()) == ["context.json"]
    closeout = value.finish()
    assert closeout.terminal_acknowledged and closeout.descriptors_closed
    assert closeout.snapshot.reserved_events == closeout.snapshot.confirmed_events == 0


def test_positive_short_reads_preserve_exact_context(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_read = os.read
    calls = 0

    def byte_read(fd: int, count: int) -> bytes:
        nonlocal calls
        calls += 1
        return original_read(fd, min(count, 1))

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", byte_read)
        observation = owned_sink.observe_context()
    assert calls == observation.byte_length <= 4096
    assert not owned_sink.snapshot().stopped


@pytest.mark.parametrize(
    "state",
    ("reserved", "stopped", "finished", "model"),
    ids=("reserved", "stopped", "finished", "model"),
)
def test_ineligible_observation_rejects_before_read(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    value = owned_sink
    if state == "reserved":
        value.append(b"{}\n")
    elif state == "stopped":
        with pytest.raises(ValueError):
            value.append(b"")
    elif state == "finished":
        value.finish()
    else:
        object.__setattr__(value.context, "run_id", "other-run")
    before = value.snapshot()
    prior_fault = value.first_exception
    with monkeypatch.context() as scoped:
        scoped.setattr(sink, "_read_file", deny_read)
        with pytest.raises(ValueError):
            value.observe_context()
        with pytest.raises(ValueError):
            value.append(b"{}\n")
    assert not value._busy
    assert value.snapshot().reserved_events == before.reserved_events
    if prior_fault is not None:
        assert value.first_exception is prior_fault
    if state != "finished":
        assert value.snapshot().stopped


@pytest.mark.parametrize("owner", ("pid", "thread"), ids=("pid", "thread"))
def test_wrong_owner_stops_without_read_and_finish_does_not_promise_terminal_ack(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
    owner: str,
) -> None:
    value = owned_sink
    with monkeypatch.context() as scoped:
        scoped.setattr(sink, "_read_file", deny_read)
        if owner == "pid":
            scoped.setattr(os, "getpid", lambda: value._pid + 1)
        else:
            scoped.setattr(threading, "get_ident", lambda: value._thread + 1)
        with pytest.raises(sink.SinkStopped, match="Wrong owner") as rejected:
            value.observe_context()
    assert value.first_exception is rejected.value and value.snapshot().stopped
    assert not value._busy and value._invalid_owner
    closeout = value.finish()
    assert closeout.descriptors_closed and not closeout.terminal_acknowledged
    assert closeout.snapshot.faults[0].phase == "ownership_or_reentry"


@pytest.mark.parametrize("nested", ("observe", "append"), ids=("observe", "append"))
def test_swallowed_reentry_cannot_return_bytes_or_clear_outer_busy(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
    nested: str,
) -> None:
    value = owned_sink
    original_read = os.read
    nested_errors: list[BaseException] = []

    def reentrant_read(fd: int, count: int) -> bytes:
        assert value._busy
        with pytest.raises(sink.SinkStopped) as rejected:
            if nested == "observe":
                value.observe_context()
            else:
                value.append(b"{}\n")
        nested_errors.append(rejected.value)
        assert value._busy
        return original_read(fd, count)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", reentrant_read)
        with pytest.raises(sink.SinkStopped) as outer:
            value.observe_context()
    assert len(nested_errors) == 1 and outer.value is nested_errors[0]
    assert value.first_exception is outer.value and not value._busy
    assert value.snapshot().reserved_events == 0
    closeout = value.finish()
    assert closeout.descriptors_closed and not closeout.terminal_acknowledged


@pytest.mark.parametrize(
    "change",
    ("contents", "spelling", "oversized", "symlink", "hardlink", "missing", "fifo"),
    ids=("contents", "spelling", "oversized", "symlink", "hardlink", "missing", "fifo"),
)
def test_changed_or_unsafe_context_stops_without_event_reservation(
    owned_sink: sink.PrimitiveFileSink,
    tmp_path: Path,
    change: str,
) -> None:
    value = owned_sink
    path = tmp_path / "sink/context.json"
    expected = path.read_bytes()
    if change == "contents":
        path.write_bytes(expected.replace(b'"run-a"', b'"run-b"'))
    elif change == "spelling":
        path.write_bytes(b" " + expected)
    elif change == "oversized":
        path.write_bytes(b"x" * 4097)
    elif change == "hardlink":
        os.link(path, tmp_path / "context-link")
    else:
        path.unlink()
        if change == "symlink":
            target = tmp_path / "context-target"
            target.write_bytes(expected)
            target.chmod(0o600)
            path.symlink_to(target)
        elif change == "fifo":
            os.mkfifo(path, 0o600)
    with pytest.raises((ValueError, OSError)) as rejected:
        value.observe_context()
    assert value.first_exception is rejected.value
    assert value.snapshot().stopped and value.snapshot().reserved_events == 0
    with pytest.raises(sink.SinkStopped):
        value.observe_context()
    with pytest.raises(sink.SinkStopped):
        value.append(b"{}\n")


def test_identical_safe_replacement_does_not_claim_creation_inode_continuity(
    owned_sink: sink.PrimitiveFileSink,
    tmp_path: Path,
) -> None:
    path = tmp_path / "sink/context.json"
    expected = path.read_bytes()
    original_inode = path.stat().st_ino
    replacement = tmp_path / "replacement"
    replacement.write_bytes(expected)
    replacement.chmod(0o600)
    assert replacement.stat().st_ino != original_inode
    replacement.replace(path)
    observation = owned_sink.observe_context()
    assert observation.raw == expected
    assert not owned_sink.snapshot().stopped


def test_within_read_timestamp_change_rejects_even_identical_returned_bytes(
    owned_sink: sink.PrimitiveFileSink,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "sink/context.json"
    before = path.stat()
    original_read = os.read
    calls = 0

    def changed_read(fd: int, count: int) -> bytes:
        nonlocal calls
        raw = original_read(fd, count)
        calls += 1
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        return raw

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", changed_read)
        with pytest.raises(ValueError, match="changed while reading") as rejected:
            owned_sink.observe_context()
    assert calls == 1 and owned_sink.first_exception is rejected.value
    assert owned_sink.snapshot().stopped


@pytest.mark.parametrize(
    "fault", ("read", "close", "both", "eof"), ids=("read", "close", "both", "eof")
)
def test_read_and_real_close_then_error_preserve_primary_and_uncertainty(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    value = owned_sink
    original_read, original_close = os.read, os.close
    read_error = OSError(errno.EIO, "synthetic context read failure")
    close_error = OSError(errno.EIO, "synthetic lost close confirmation")
    read_fds: list[int] = []
    close_injections = 0

    def faulting_read(fd: int, count: int) -> bytes:
        read_fds.append(fd)
        if fault in ("read", "both"):
            raise read_error
        if fault == "eof":
            return b""
        return original_read(fd, count)

    def close_then_fault(fd: int) -> None:
        nonlocal close_injections
        original_close(fd)
        if fault in ("close", "both") and read_fds == [fd] and close_injections == 0:
            close_injections += 1
            raise close_error

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", faulting_read)
        scoped.setattr(os, "close", close_then_fault)
        with pytest.raises((ValueError, OSError)) as rejected:
            value.observe_context()
    assert len(read_fds) == 1
    with pytest.raises(OSError) as closed:
        os.fstat(read_fds[0])
    assert closed.value.errno == errno.EBADF
    if fault in ("read", "both"):
        assert rejected.value is read_error
    elif fault == "close":
        assert rejected.value is close_error
    else:
        assert "shortened" in str(rejected.value)
    assert value.first_exception is rejected.value
    assert value.snapshot().faults[0].phase == "context_observation"
    uncertain = fault in ("close", "both")
    assert close_injections == int(uncertain)
    assert value._anchor.closure_uncertain is uncertain
    if uncertain:
        assert [row.phase for row in value.snapshot().faults] == [
            "context_observation",
            "descriptor_close",
        ]
    prior_fault = value.first_exception
    with monkeypatch.context() as scoped:
        scoped.setattr(sink, "_read_file", deny_read)
        with pytest.raises(sink.SinkStopped):
            value.observe_context()
        with pytest.raises(sink.SinkStopped):
            value.append(b"{}\n")
    assert value.first_exception is prior_fault and not value._busy
    closeout = value.finish()
    assert closeout.terminal_acknowledged
    assert closeout.descriptors_closed is (not uncertain)


@pytest.mark.parametrize("pending", ("fault", "uncertain"), ids=("fault", "uncertain"))
def test_prior_closure_facts_preclude_new_read(
    owned_sink: sink.PrimitiveFileSink,
    monkeypatch: pytest.MonkeyPatch,
    pending: str,
) -> None:
    # Isolate previously retained state; no pretend OS close or repeated read is performed.
    value = owned_sink
    earlier = OSError(errno.EIO, "earlier synthetic close uncertainty")
    value._anchor.closure_uncertain = True
    if pending == "fault":
        value._anchor.close_faults.append(earlier)
    with monkeypatch.context() as scoped:
        scoped.setattr(sink, "_read_file", deny_read)
        with pytest.raises((ValueError, OSError)):
            value.observe_context()
    assert value.snapshot().stopped and not value._busy
    if pending == "fault":
        assert value.first_exception is earlier
        assert [row.phase for row in value.snapshot().faults] == ["descriptor_close"]
    closeout = value.finish()
    assert closeout.terminal_acknowledged and not closeout.descriptors_closed
