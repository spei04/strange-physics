"""Small synthetic T/C files only; no activation, primitive or power-loss qualification."""

from __future__ import annotations

import builtins
import errno
import hashlib
import json
import os
import threading
from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from typing import Any

import d1_table_retention as retention
import pytest
from d1_primitive_codec_table import PROTOCOL_SHA256, TABLE_BYTES, TableIdentity, build_table
from d1_primitive_sink import (
    ContextObservation,
    PrimitiveFileSink,
    SinkContext,
    _Anchor,
    _read_file,
    _write_remaining,
)


@pytest.fixture(autouse=True)
def no_scientific_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.removeprefix("tests.") in {
            "endpoint_belief_reference", "d1_fixture_reference", "d1_prefix_evidence",
            "d1_bounds", "grid_q1_reference", "grid_q1_driver",
        } or name in {
            "strange_physics.native_prediction", "strange_physics.native_endpoint_beliefs",
            "strange_physics.simulation", "strange_physics.finite_log_weights",
        }:
            raise AssertionError("T retention tests cannot import scientific producers")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


@dataclass
class Case:
    parent: Path
    sink: PrimitiveFileSink
    raw: bytes
    attempt: retention.TableRetentionAttempt


@pytest.fixture
def case(tmp_path: Path) -> Iterator[Case]:
    tmp_path.chmod(0o700)
    context = SinkContext(
        "recorder-a", "run-a", "1" * 40, "2" * 40, PROTOCOL_SHA256,
        "3" * 64, "4" * 64, "6" * 64, 55100, 32768,
    )
    value = PrimitiveFileSink.create(tmp_path / "sink", context)
    raw = build_table(
        TableIdentity(
            "1" * 40, "2" * 40, PROTOCOL_SHA256, "3" * 64,
            "4" * 64, "5" * 64, "run-a", "recorder-a",
        ),
        ("owned-fake-definition",) * 14,
    )
    assert len(raw) <= 4096
    result = Case(
        tmp_path, value, raw, retention.TableRetentionAttempt(tmp_path / "metadata", value, raw)
    )
    sink_fds = (value._anchor.parent, value._anchor.directory)
    original_fstat = os.fstat
    try:
        yield result
    finally:
        anchor = result.attempt._anchor
        if anchor is not None:
            assert anchor.parent is None and anchor.directory is None
        if not value.snapshot().finish_consumed:
            value.finish()
        for descriptor in sink_fds:
            assert descriptor is not None
            with pytest.raises(OSError) as closed:
                original_fstat(descriptor)
            assert closed.value.errno == errno.EBADF


def assert_consumed(case: Case, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Consumed attempt cannot do filesystem work")

    with monkeypatch.context() as scoped:
        for name in ("open", "read", "write", "fsync", "stat", "fstat", "mkdir", "close"):
            scoped.setattr(os, name, forbidden)
        with pytest.raises(retention.TableRetentionStopped, match="consumed"):
            case.attempt.retain()


def test_success_orders_fresh_context_after_all_metadata_closes(
    case: Case, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_observe = PrimitiveFileSink.observe_context
    observations = 0
    metadata_fds: list[int] = []
    original_write = _write_remaining

    def tracked_write(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        anchor = case.attempt._anchor
        assert anchor is not None and anchor.parent is not None and anchor.directory is not None
        metadata_fds.extend((fd, anchor.parent, anchor.directory))
        original_write(fd, raw, progress, check)

    def observed(value: PrimitiveFileSink) -> ContextObservation:
        nonlocal observations
        observations += 1
        if observations == 2:
            assert case.attempt.snapshot().metadata_close_confirmed is True
            for descriptor in metadata_fds:
                with pytest.raises(OSError) as closed:
                    os.fstat(descriptor)
                assert closed.value.errno == errno.EBADF
        return original_observe(value)

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", tracked_write)
        scoped.setattr(PrimitiveFileSink, "observe_context", observed)
        result = case.attempt.retain()
    assert observations == 2
    retained = (case.parent / "metadata/identity-table.json").read_bytes()
    assert result.table_raw == retained == case.raw
    assert result.context_raw == (case.parent / "sink/context.json").read_bytes()
    assert result.table_sha256 == hashlib.sha256(case.raw).hexdigest()
    assert result.context_sha256 == hashlib.sha256(result.context_raw).hexdigest()
    assert (result.table_bytes, result.context_bytes) == (
        len(case.raw), len(result.context_raw),
    )
    assert not hasattr(result, "__dict__")
    invalid: Any = result
    with pytest.raises(FrozenInstanceError):
        invalid.table_bytes = 0
    state = case.attempt.snapshot()
    assert state.reserved_bytes == state.written_bytes == len(case.raw)
    assert state.table_synced and state.table_readback_equal and not state.stopped
    assert state.context_observations == 2 and state.metadata_close_confirmed is True
    assert case.sink.snapshot().reserved_events == 0
    assert [p.name for p in (case.parent / "metadata").iterdir()] == ["identity-table.json"]
    for descriptor in (case.sink._anchor.parent, case.sink._anchor.directory):
        assert descriptor is not None
        os.fstat(descriptor)
    assert_consumed(case, monkeypatch)


@pytest.mark.parametrize(
    "bad",
    ("mutable", "oversized", "spelling", "identity"),
    ids=("mutable", "oversized", "spelling", "identity"),
)
def test_invalid_table_or_join_cannot_create_metadata(case: Case, bad: str) -> None:
    raw: Any = case.raw
    if bad == "mutable":
        raw = bytearray(case.raw)
    elif bad == "oversized":
        raw = b"x" * (TABLE_BYTES + 1)
    elif bad == "spelling":
        raw = b" " + case.raw
    else:
        fields = json.loads(case.raw)
        fields["source_commit"] = "7" * 40
        raw = (json.dumps(fields, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    case.attempt = retention.TableRetentionAttempt(case.parent / "metadata", case.sink, raw)
    with pytest.raises(ValueError):
        case.attempt.retain()
    assert not (case.parent / "metadata").exists()
    assert not case.attempt.snapshot().creation_entered
    assert case.attempt.snapshot().stopped


@pytest.mark.parametrize(
    "where",
    ("other-parent", "sink-root", "existing"),
    ids=("other-parent", "sink-root", "existing"),
)
def test_parent_and_distinct_root_are_enforced_before_creation(case: Case, where: str) -> None:
    root = case.parent / "metadata"
    if where == "other-parent":
        other = case.parent / "other"
        other.mkdir(mode=0o700)
        root = other / "metadata"
    elif where == "sink-root":
        root = case.parent / "sink"
    else:
        root.mkdir(mode=0o700)
    case.attempt = retention.TableRetentionAttempt(root, case.sink, case.raw)
    with pytest.raises((ValueError, OSError)):
        case.attempt.retain()
    if where == "other-parent":
        assert not root.exists()
    assert not (root / "identity-table.json").exists()
    assert case.sink._anchor.parent is not None and case.sink._anchor.directory is not None
    os.fstat(case.sink._anchor.parent)
    os.fstat(case.sink._anchor.directory)


@pytest.mark.parametrize("owner", ("pid", "thread"), ids=("pid", "thread"))
def test_wrong_owner_attempt_does_not_mutate_sink(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    owner: str,
) -> None:
    before = case.sink.snapshot()
    with monkeypatch.context() as scoped:
        if owner == "pid":
            scoped.setattr(os, "getpid", lambda: case.attempt._pid + 1)
        else:
            scoped.setattr(threading, "get_ident", lambda: case.attempt._thread + 1)
        with pytest.raises(retention.TableRetentionStopped):
            case.attempt.retain()
    assert case.sink.snapshot() == before
    assert not (case.parent / "metadata").exists()
    assert case.attempt.first_exception is not None
    assert_consumed(case, monkeypatch)


@pytest.mark.parametrize("state", ("non-idle", "stopped"), ids=("non-idle", "stopped"))
def test_sink_must_be_idle_before_metadata(case: Case, state: str) -> None:
    if state == "non-idle":
        case.sink.append(b"{}\n")
    else:
        with pytest.raises(ValueError):
            case.sink.append(b"")
    with pytest.raises(ValueError):
        case.attempt.retain()
    assert not (case.parent / "metadata").exists()
    assert case.attempt.snapshot().context_observations == 0


@pytest.mark.parametrize("progress", ("short", "zero"), ids=("short", "zero"))
def test_owned_positive_short_progress_and_zero_stop(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    progress: str,
) -> None:
    original_write, original_read = os.write, os.read
    writes = 0

    def small_write(fd: int, raw: bytes | memoryview) -> int:
        nonlocal writes
        writes += 1
        return 0 if progress == "zero" else original_write(fd, raw[:7])

    def small_read(fd: int, count: int) -> bytes:
        return original_read(fd, min(count, 7))

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "write", small_write)
        scoped.setattr(os, "read", small_read)
        if progress == "short":
            result = case.attempt.retain()
            assert result.table_raw == case.raw and 1 < writes <= len(case.raw)
        else:
            with pytest.raises(OSError):
                case.attempt.retain()
            assert writes == 1 and case.attempt.snapshot().written_bytes == 0
    assert case.attempt.snapshot().reserved_bytes == len(case.raw)


@pytest.mark.parametrize("failure", ("partial", "interrupt"), ids=("partial", "interrupt"))
def test_failed_write_keeps_full_reservation_and_first_error(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    original_write = _write_remaining
    primary = (
        InterruptedError("synthetic interrupted write")
        if failure == "interrupt"
        else OSError(errno.EIO, "synthetic partial write")
    )

    def failed_write(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        original_write(fd, raw[:5], progress, check)
        raise primary

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", failed_write)
        with pytest.raises(OSError) as rejected:
            case.attempt.retain()
    assert rejected.value is primary and case.attempt.first_exception is primary
    assert (case.parent / "metadata/identity-table.json").read_bytes() == case.raw[:5]
    state = case.attempt.snapshot()
    assert state.reserved_bytes == len(case.raw) and state.written_bytes == 5
    assert state.context_observations == 1 and state.metadata_close_confirmed is True
    assert not case.sink.snapshot().stopped
    assert_consumed(case, monkeypatch)


@pytest.mark.parametrize("nth", (1, 2, 3), ids=("parent", "table", "directory"))
def test_sync_failure_stops_without_final_context(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    nth: int,
) -> None:
    original_sync = os.fsync
    primary = OSError(errno.EIO, "synthetic metadata sync failure")
    calls = 0

    def failed_sync(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == nth:
            raise primary
        original_sync(fd)

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "fsync", failed_sync)
        with pytest.raises(OSError) as rejected:
            case.attempt.retain()
    assert rejected.value is primary and case.attempt.first_exception is primary
    state = case.attempt.snapshot()
    assert state.context_observations == 1 and calls == nth
    assert (case.parent / "metadata").is_dir()
    if nth == 1:
        assert state.creation_entered and not state.anchor_received
        assert state.metadata_close_confirmed is False
    assert_consumed(case, monkeypatch)


@pytest.mark.parametrize("kind", ("substitute", "read-error"), ids=("substitute", "read-error"))
def test_readback_requires_actual_equal_bytes(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    primary = OSError(errno.EIO, "synthetic table read error")

    def altered_read(anchor: _Anchor, name: str, limit: int) -> bytes:
        assert name == "identity-table.json" and limit == TABLE_BYTES
        if kind == "read-error":
            raise primary
        return b"substituted\n"

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_read_file", altered_read)
        with pytest.raises((ValueError, OSError)) as rejected:
            case.attempt.retain()
    if kind == "read-error":
        assert rejected.value is primary
    assert case.attempt.snapshot().table_synced
    assert not case.attempt.snapshot().table_readback_equal
    assert case.attempt.snapshot().context_observations == 1


@pytest.mark.parametrize("target", ("writer", "reader", "root"), ids=("writer", "reader", "root"))
def test_owned_close_then_error_never_acknowledges_or_rereads_context(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    original_write, original_read, original_close = _write_remaining, os.read, os.close
    primary = OSError(errno.EIO, "synthetic lost metadata close confirmation")
    target_fd: int | None = None
    captured: list[int] = []
    injections = 0

    def tracked_write(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        nonlocal target_fd
        anchor = case.attempt._anchor
        assert anchor is not None and anchor.parent is not None and anchor.directory is not None
        captured.extend((fd, anchor.parent, anchor.directory))
        if target != "reader":
            target_fd = fd if target == "writer" else anchor.directory
        original_write(fd, raw, progress, check)

    def tracked_read(fd: int, count: int) -> bytes:
        nonlocal target_fd
        anchor = case.attempt._anchor
        if target == "reader" and anchor is not None and anchor.directory is not None:
            target_fd = fd
            captured.append(fd)
        return original_read(fd, count)

    def close_then_error(fd: int) -> None:
        nonlocal injections
        original_close(fd)
        if fd == target_fd and injections == 0:
            injections += 1
            raise primary

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", tracked_write)
        scoped.setattr(os, "read", tracked_read)
        scoped.setattr(os, "close", close_then_error)
        with pytest.raises(OSError) as rejected:
            case.attempt.retain()
    assert rejected.value is primary and case.attempt.first_exception is primary
    assert injections == 1 and case.attempt.snapshot().metadata_close_confirmed is False
    assert case.attempt.snapshot().context_observations == 1
    for fd in set(captured):
        with pytest.raises(OSError) as closed:
            os.fstat(fd)
        assert closed.value.errno == errno.EBADF
    assert_consumed(case, monkeypatch)


@pytest.mark.parametrize("when", ("write", "close", "final-c"), ids=("write", "close", "final-c"))
def test_swallowed_reentry_stays_sticky_at_all_handoffs(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    when: str,
) -> None:
    original_write = _write_remaining
    original_close = os.close
    original_observe = PrimitiveFileSink.observe_context
    root_fd: int | None = None
    observations = 0
    nested: list[BaseException] = []

    def swallowed() -> None:
        assert case.attempt._busy
        with pytest.raises(retention.TableRetentionStopped) as rejected:
            case.attempt.retain()
        nested.append(rejected.value)
        assert case.attempt._busy

    def write_hook(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        nonlocal root_fd
        anchor = case.attempt._anchor
        assert anchor is not None
        root_fd = anchor.directory
        if when == "write":
            swallowed()
            return
        original_write(fd, raw, progress, check)

    def close_hook(fd: int) -> None:
        original_close(fd)
        if when == "close" and fd == root_fd and not nested:
            swallowed()

    def observe_hook(value: PrimitiveFileSink) -> ContextObservation:
        nonlocal observations
        observations += 1
        actual = original_observe(value)
        if when == "final-c" and observations == 2:
            swallowed()
        return actual

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", write_hook)
        scoped.setattr(os, "close", close_hook)
        scoped.setattr(PrimitiveFileSink, "observe_context", observe_hook)
        with pytest.raises(retention.TableRetentionStopped) as rejected:
            case.attempt.retain()
    assert len(nested) == 1 and rejected.value is nested[0]
    assert case.attempt.first_exception is nested[0]
    assert observations == (2 if when == "final-c" else 1)
    assert case.attempt.snapshot().metadata_close_confirmed is True
    assert not case.sink.snapshot().stopped
    assert_consumed(case, monkeypatch)


def test_constructor_unknown_preserves_primary_and_supplemental_close(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_close = os.close
    primary = OSError(errno.EIO, "constructor sync failure")
    supplemental = OSError(errno.EIO, "constructor close uncertainty")
    opened_parent: list[int] = []

    def failed_sync(fd: int) -> None:
        opened_parent.append(fd)
        raise primary

    def close_hook(fd: int) -> None:
        original_close(fd)
        if opened_parent == [fd]:
            raise supplemental

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "fsync", failed_sync)
        scoped.setattr(os, "close", close_hook)
        with pytest.raises(OSError) as rejected:
            case.attempt.retain()
    assert rejected.value is primary and case.attempt.first_exception is primary
    assert any("Supplemental anchor close failure" in note for note in primary.__notes__)
    state = case.attempt.snapshot()
    assert state.creation_entered and not state.anchor_received
    assert state.metadata_close_confirmed is False and state.context_observations == 1
    assert (case.parent / "metadata").is_dir()
    with pytest.raises(OSError) as closed:
        os.fstat(opened_parent[0])
    assert closed.value.errno == errno.EBADF


@pytest.mark.parametrize("change", ("append", "context"), ids=("append", "context"))
def test_intervening_sink_change_prevents_final_join(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    original_read = _read_file

    def altered_sink(anchor: _Anchor, name: str, limit: int) -> bytes:
        raw = original_read(anchor, name, limit)
        if change == "append":
            case.sink.append(b"{}\n")
        else:
            path = case.parent / "sink/context.json"
            path.write_bytes(path.read_bytes().replace(b'"run-a"', b'"run-b"'))
        return raw

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_read_file", altered_sink)
        with pytest.raises(ValueError):
            case.attempt.retain()
    state = case.attempt.snapshot()
    assert state.table_readback_equal and state.metadata_close_confirmed is True
    assert state.context_observations == 1
    assert (case.parent / "metadata/identity-table.json").read_bytes() == case.raw


def test_same_parent_root_substitution_cannot_pass_named_checks(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_write = _write_remaining

    def swapped_root(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        original_write(fd, raw, progress, check)
        (case.parent / "metadata").rename(case.parent / "retained-original")
        (case.parent / "metadata").mkdir(mode=0o700)

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", swapped_root)
        with pytest.raises(ValueError, match="directory identity"):
            case.attempt.retain()
    assert (case.parent / "retained-original/identity-table.json").read_bytes() == case.raw
    assert not (case.parent / "metadata/identity-table.json").exists()
    assert case.attempt.snapshot().context_observations == 1


def test_same_byte_new_table_inode_is_not_the_synced_created_table(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_read = _read_file

    def replaced_table(anchor: _Anchor, name: str, limit: int) -> bytes:
        replacement = case.parent / "replacement"
        replacement.write_bytes(case.raw)
        replacement.chmod(0o600)
        replacement.replace(case.parent / "metadata/identity-table.json")
        return original_read(anchor, name, limit)

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_read_file", replaced_table)
        with pytest.raises(ValueError, match="Created table identity"):
            case.attempt.retain()
    assert case.attempt.snapshot().context_observations == 1


def test_primary_write_error_survives_independent_root_close_error(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_write, original_close = _write_remaining, os.close
    primary = OSError(errno.EIO, "first write error")
    supplemental = OSError(errno.EIO, "later close error")
    root_fd: int | None = None
    injections = 0

    def failed_write(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
        nonlocal root_fd
        anchor = case.attempt._anchor
        assert anchor is not None
        root_fd = anchor.directory
        original_write(fd, raw[:5], progress, check)
        raise primary

    def close_hook(fd: int) -> None:
        nonlocal injections
        original_close(fd)
        if fd == root_fd and injections == 0:
            injections += 1
            raise supplemental

    with monkeypatch.context() as scoped:
        scoped.setattr(retention, "_write_remaining", failed_write)
        scoped.setattr(os, "close", close_hook)
        with pytest.raises(OSError) as rejected:
            case.attempt.retain()
    assert rejected.value is primary and case.attempt.first_exception is primary
    assert injections == 1
    assert [fault.phase for fault in case.attempt.snapshot().faults] == [
        "table_write", "metadata_anchor_close",
    ]
    assert case.attempt.snapshot().metadata_close_confirmed is False
    assert case.attempt.snapshot().context_observations == 1


@pytest.mark.parametrize("when", ("parent-sync", "final-c"), ids=("parent-sync", "final-c"))
def test_swallowed_first_fault_is_raised_instead_of_later_io_error(
    case: Case,
    monkeypatch: pytest.MonkeyPatch,
    when: str,
) -> None:
    original_sync = os.fsync
    original_observe = PrimitiveFileSink.observe_context
    later = OSError(errno.EIO, "distinct error after swallowed reentry")
    nested: list[BaseException] = []
    sync_fds: list[int] = []
    observed_returns = 0

    def first_then_later() -> None:
        with pytest.raises(retention.TableRetentionStopped) as first:
            case.attempt.retain()
        nested.append(first.value)
        assert case.attempt._busy
        raise later

    def sync_hook(fd: int) -> None:
        sync_fds.append(fd)
        if when == "parent-sync":
            first_then_later()
        original_sync(fd)

    def observe_hook(value: PrimitiveFileSink) -> ContextObservation:
        nonlocal observed_returns
        actual = original_observe(value)
        observed_returns += 1
        if when == "final-c" and observed_returns == 2:
            first_then_later()
        return actual

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "fsync", sync_hook)
        scoped.setattr(PrimitiveFileSink, "observe_context", observe_hook)
        with pytest.raises(retention.TableRetentionStopped) as rejected:
            case.attempt.retain()
    assert len(nested) == 1 and rejected.value is nested[0]
    assert rejected.value is not later and case.attempt.first_exception is nested[0]
    state = case.attempt.snapshot()
    expected_phase = "metadata_create" if when == "parent-sync" else "context_after"
    assert [fault.phase for fault in state.faults] == ["ownership_or_reentry", expected_phase]
    assert state.faults[1].exception_type == "builtins.OSError"
    assert state.faults[1].exception_type_complete
    assert state.reserved_bytes == len(case.raw) and state.context_observations == 1
    if when == "parent-sync":
        assert observed_returns == 1 and len(sync_fds) == 1
        assert state.creation_entered and not state.anchor_received
        assert state.metadata_close_confirmed is False and not state.table_creation_entered
        assert (case.parent / "metadata").is_dir()
    else:
        assert observed_returns == 2 and len(sync_fds) == 3
        assert state.table_readback_equal and state.metadata_close_confirmed is True
        assert (case.parent / "metadata/identity-table.json").read_bytes() == case.raw
    for fd in set(sync_fds):
        with pytest.raises(OSError) as closed:
            os.fstat(fd)
        assert closed.value.errno == errno.EBADF
    assert not case.attempt._busy and not case.sink.snapshot().stopped
    assert_consumed(case, monkeypatch)
