"""Synthetic files/faults only; never a power-loss or scientific durability proof."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, replace
from decimal import Decimal
from pathlib import Path
from typing import NoReturn, cast

import d1_primitive_sink as sink
import pytest
from d1_primitive_recording import PrimitiveRecorder
from endpoint_belief_reference import EndpointOracle

import strange_physics.native_endpoint_beliefs as beliefs
import strange_physics.native_prediction as prediction
import strange_physics.simulation as simulation


@pytest.fixture(autouse=True)
def no_science(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("File sink tests cannot execute scientific producers")
    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(prediction, "predict_native_spring", deny)
    monkeypatch.setattr(prediction, "_state_at_time", deny)
    monkeypatch.setattr(beliefs, "compute_native_endpoint_belief", deny)
    monkeypatch.setattr(simulation, "simulate", deny)


def context(*, max_calls: int = 4, max_bytes: int = 32768) -> sink.SinkContext:
    return sink.SinkContext("recorder-a", "run-a", "a" * 40, "b" * 40, "c" * 64,
                            "d" * 64, "e" * 64, "f" * 64, max_calls, max_bytes)


def create(tmp_path: Path, value: sink.SinkContext | None = None) -> sink.PrimitiveFileSink:
    tmp_path.chmod(0o700)
    return sink.PrimitiveFileSink.create(tmp_path / "sink", context() if value is None else value)


def test_success_keeps_exact_bytes_and_only_pending_external_terminal(tmp_path: Path) -> None:
    value = create(tmp_path)
    raw = b'{"exact":"-0x0.0p+0"}\n'
    value.append(raw)
    closeout = value.finish()
    assert closeout.terminal_acknowledged and closeout.descriptors_closed
    assert closeout.snapshot.confirmed_events == 1 and not closeout.snapshot.stopped
    assert (tmp_path / "sink/events-00.jsonl").read_bytes() == raw
    terminal = json.loads((tmp_path / "sink/terminal.json").read_bytes())
    assert terminal["state"] == "pending_external_confirmation"
    report = sink.inspect_sink(tmp_path / "sink", max_bytes=32768)
    assert report.context_canonical and report.shards[0].complete_lines == 1
    assert report.terminal_state == "present-unconfirmed"
    assert report.acknowledgement == report.execution == "not-inferred"
    assert report.authenticity == "unchecked"
    assert report.actual_bytes == sum(p.stat().st_size for p in (tmp_path / "sink").iterdir())


def test_exact_context_limits_are_derived_without_payload_or_verification_flags(tmp_path: Path) -> None:
    actual = context(max_calls=55100, max_bytes=64 * 1024**2)
    value = create(tmp_path, actual)
    raw = (tmp_path / "sink/context.json").read_bytes()
    parsed = json.loads(raw)
    assert len(raw) <= 4096 and parsed["max_events"] == 110201
    assert parsed["context_bytes"] == 4096 and parsed["terminal_bytes"] == 16384
    assert parsed["event_capacity"] == actual.max_bytes - 20480
    assert parsed["event_bytes"] == 4096 and parsed["shard_bytes"] == 4 * 1024**2
    assert parsed["max_shards"] == 16
    assert not {"path", "payload", "verified", "passed", "qualification"}.intersection(parsed)
    assert value.finish().terminal_acknowledged


@pytest.mark.parametrize("field,bad", (
    ("max_calls", True), ("max_calls", 0), ("max_calls", 55101),
    ("max_bytes", True), ("max_bytes", 20480), ("max_bytes", 64 * 1024**2 + 1),
    ("source_commit", "a" * 40 + "\n"), ("source_tree", "g" * 40),
    ("recorder_id", "../r"), ("run_id", "r" * 97), ("sink_sha256", "f" * 63),
))
def test_invalid_context_cannot_create_a_directory(tmp_path: Path, field: str, bad: object) -> None:
    with pytest.raises(ValueError):
        create(tmp_path, replace(context(), **{field: bad}))
    assert not (tmp_path / "sink").exists()


def test_mutated_context_is_rejected_before_any_append_io(tmp_path: Path) -> None:
    value = create(tmp_path)
    object.__setattr__(value.context, "max_bytes", 65536)
    with pytest.raises(ValueError, match="changed"):
        value.append(b"{}\n")
    assert value.snapshot().reserved_events == 0
    assert not (tmp_path / "sink/events-00.jsonl").exists()
    assert value.finish().snapshot.stopped


@pytest.mark.parametrize("kind", ("existing", "symlink", "public-parent"))
def test_exclusive_private_root_creation(tmp_path: Path, kind: str) -> None:
    target = tmp_path / "sink"
    if kind == "existing":
        target.mkdir(mode=0o700)
    elif kind == "symlink":
        other = tmp_path / "other"
        other.mkdir(mode=0o700)
        target.symlink_to(other, target_is_directory=True)
    else:
        tmp_path.chmod(0o755)
    try:
        with pytest.raises((ValueError, OSError)):
            sink.PrimitiveFileSink.create(target, context())
    finally:
        tmp_path.chmod(0o700)


@pytest.mark.parametrize("bad", (b"", b"{}", b"{}\n{}\n", b"x" * 4096 + b"\n", bytearray(b"{}\n")))
def test_invalid_line_stops_without_reserving_or_writing(tmp_path: Path, bad: object) -> None:
    value = create(tmp_path)
    with pytest.raises(ValueError):
        value.append(cast(bytes, bad))
    assert value.snapshot().stopped and value.snapshot().reserved_events == 0
    with pytest.raises(sink.SinkStopped):
        value.append(b"{}\n")
    assert value.finish().snapshot.stopped


@pytest.mark.parametrize("bound", ("bytes", "events"))
def test_exact_event_allowance_exhaustion_is_not_reusable(tmp_path: Path, bound: str) -> None:
    actual = context(max_calls=1, max_bytes=20483 if bound == "bytes" else 32768)
    value = create(tmp_path, actual)
    count = 1 if bound == "bytes" else 3
    for _ in range(count):
        value.append(b"{}\n")
    with pytest.raises(ValueError, match="allowance"):
        value.append(b"{}\n")
    assert value.snapshot().confirmed_events == count
    assert value.snapshot().reserved_events == count
    assert value.finish().terminal_acknowledged


def test_small_test_only_rotation_preserves_lines_and_fixed_metadata_reservation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Exercise geometry with 8-byte shards; the separate context test pins 4 MiB.
    with monkeypatch.context() as patch:
        patch.setattr(sink, "SHARD_BYTES", 8)
        value = create(tmp_path)
        for raw in (b"123\n", b"456\n", b"7\n"):
            value.append(raw)
        assert (tmp_path / "sink/events-00.jsonl").read_bytes() == b"123\n456\n"
        assert (tmp_path / "sink/events-01.jsonl").read_bytes() == b"7\n"
        result = value.finish()
        assert result.snapshot.confirmed_bytes == 10 and result.terminal_acknowledged
        assert sink.inspect_sink(tmp_path / "sink", max_bytes=32768).actual_bytes < 20480


def test_small_test_only_shard_count_limit_is_fail_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(sink, "SHARD_BYTES", 3)
        patch.setattr(sink, "MAX_SHARDS", 2)
        value = create(tmp_path)
        value.append(b"{}\n")
        value.append(b"{}\n")
        with pytest.raises(ValueError, match="Shard"):
            value.append(b"{}\n")
        assert value.snapshot().reserved_events == 3 and value.snapshot().confirmed_events == 2
        assert value.finish().snapshot.stopped


def test_short_writes_are_one_event_and_fsync_precedes_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = create(tmp_path)
    write, sync = os.write, os.fsync
    calls: list[int] = []
    acknowledged_at_sync: list[int] = []
    def short(fd: int, raw: bytes | memoryview) -> int:
        calls.append(len(raw))
        return write(fd, raw[:1])
    def observe(fd: int) -> None:
        acknowledged_at_sync.append(value.snapshot().confirmed_events)
        sync(fd)
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", short)
        patch.setattr(os, "fsync", observe)
        value.append(b"abc\n")
    assert calls == [4, 3, 2, 1]
    assert set(acknowledged_at_sync) == {0}
    assert value.snapshot().confirmed_events == 1
    value.finish()


@pytest.mark.parametrize("kind", ("zero", "raise", "interrupt", "after-partial"))
def test_write_failure_preserves_unknown_reservation_and_never_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    value = create(tmp_path)
    real = os.write
    count = 0
    primary = KeyboardInterrupt() if kind == "interrupt" else OSError("owned failure")
    def fail(fd: int, raw: bytes | memoryview) -> int:
        nonlocal count
        count += 1
        if kind == "zero":
            return 0
        if kind == "after-partial" and count == 1:
            return real(fd, raw[:2])
        raise primary
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", fail)
        with pytest.raises((OSError, KeyboardInterrupt)):
            value.append(b"abc\n")
        frozen = count
        with pytest.raises(sink.SinkStopped):
            value.append(b"abc\n")
        assert count == frozen
    snap = value.snapshot()
    assert snap.reserved_bytes == 4 and snap.confirmed_bytes == 0
    assert snap.written_bytes == (2 if kind == "after-partial" else 0)
    value.finish()
    report = sink.inspect_sink(tmp_path / "sink", max_bytes=32768)
    assert report.shards[0].trailing_fragment_bytes == (2 if kind == "after-partial" else 0)


@pytest.mark.parametrize("where", ("new-shard-directory", "data"))
def test_fsync_failure_never_turns_readable_bytes_into_ack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, where: str) -> None:
    value = create(tmp_path)
    real = os.fsync
    error = OSError("sync failed")
    def fail(fd: int) -> None:
        if (where == "new-shard-directory" and fd == value._anchor.directory) or (
            where == "data" and fd == value._fd and os.fstat(fd).st_size > 0
        ):
            raise error
        real(fd)
    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", fail)
        with pytest.raises(OSError) as caught:
            value.append(b"{}\n")
    assert caught.value is error and value.first_exception is error
    assert value.snapshot().confirmed_events == 0 and value.snapshot().reserved_bytes == 3
    value.finish()
    report = sink.inspect_sink(tmp_path / "sink", max_bytes=32768)
    assert report.shards[0].complete_lines == (1 if where == "data" else 0)
    assert report.acknowledgement == "not-inferred"


def test_primary_write_error_survives_close_error_and_terminal_is_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = create(tmp_path)
    original = OSError("original")
    with monkeypatch.context() as patch:
        def fail_write(fd: int, raw: bytes | memoryview) -> NoReturn:
            raise original
        patch.setattr(os, "write", fail_write)
        with pytest.raises(OSError):
            value.append(b"{}\n")
    target = value._fd
    real = os.close
    failed = False
    def fail_close(fd: int) -> None:
        nonlocal failed
        real(fd)
        if fd == target and not failed:
            failed = True
            raise PermissionError("ambiguous close")
    with monkeypatch.context() as patch:
        patch.setattr(os, "close", fail_close)
        result = value.finish()
    assert value.first_exception is original
    assert not result.descriptors_closed and result.terminal_acknowledged
    assert any(f.phase == "data_close" for f in result.snapshot.faults)
    assert json.loads((tmp_path / "sink/terminal.json").read_bytes())["state"] == "pending_external_confirmation"


@pytest.mark.parametrize("when", ("intent", "return"))
def test_recorder_retention_failure_does_not_fabricate_primitive_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, when: str) -> None:
    value = create(tmp_path)
    recorder = PrimitiveRecorder(value.append, max_calls=1, max_bytes=8192)
    invoked: list[str] = []
    real = os.write
    writes = 0
    def fail(fd: int, raw: bytes | memoryview) -> int:
        nonlocal writes
        writes += 1
        if writes == (1 if when == "intent" else 2):
            raise OSError("retention")
        return real(fd, raw)
    def owned() -> Decimal:
        invoked.append("owned")
        return Decimal("-0.00")
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", fail)
        with pytest.raises(OSError):
            recorder.call(call_id="c", instance_id="i", primitive="log", scope=("scope",),
                          arguments=Decimal(1), invoke=owned)
    snap = recorder.snapshot()
    assert snap.invoked == snap.returned == (0 if when == "intent" else 1)
    assert snap.primitive_failed == 0 and snap.stopped
    assert len(invoked) == snap.invoked
    assert any(event.delivery == "unknown" for event in snap.events)
    value.finish()


@pytest.mark.parametrize("kind", ("name-swap", "hardlink", "fifo"))
def test_substituted_or_special_files_are_never_followed(tmp_path: Path, kind: str) -> None:
    value = create(tmp_path)
    path = tmp_path / "sink/events-00.jsonl"
    if kind == "fifo":
        os.mkfifo(path, mode=0o600)
    else:
        value.append(b"{}\n")
        if kind == "name-swap":
            path.rename(tmp_path / "original")
            path.write_bytes(b"fake\n")
            path.chmod(0o600)
        else:
            os.link(path, tmp_path / "linked")
    with pytest.raises((ValueError, OSError)):
        value.append(b"{}\n")
    result = value.finish()
    assert result.snapshot.stopped
    if kind == "fifo":
        with pytest.raises(ValueError):
            sink.inspect_sink(tmp_path / "sink", max_bytes=32768)


def test_root_name_substitution_stops_the_pinned_writer(tmp_path: Path) -> None:
    value = create(tmp_path)
    (tmp_path / "sink").rename(tmp_path / "old")
    (tmp_path / "sink").mkdir(mode=0o700)
    with pytest.raises(ValueError, match="identity"):
        value.append(b"{}\n")
    result = value.finish()
    assert not result.terminal_acknowledged and result.snapshot.stopped
    assert not list((tmp_path / "sink").iterdir())


@pytest.mark.parametrize("owner", ("pid", "thread"))
def test_other_owner_cannot_write_or_close(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner: str) -> None:
    value = create(tmp_path)
    with monkeypatch.context() as patch:
        if owner == "pid":
            patch.setattr(os, "getpid", lambda: value._pid + 1)
        else:
            patch.setattr(threading, "get_ident", lambda: value._thread + 1)
        with pytest.raises(sink.SinkStopped):
            value.append(b"{}\n")
        with pytest.raises(sink.SinkStopped):
            value.finish()
    assert not value.snapshot().finish_consumed
    assert value.finish().snapshot.stopped


@pytest.mark.parametrize("operation", ("append", "finish"))
def test_reentry_cannot_be_swallowed_into_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str) -> None:
    value = create(tmp_path)
    real = os.write
    entered = False
    def reenter(fd: int, raw: bytes | memoryview) -> int:
        nonlocal entered
        if not entered:
            entered = True
            with pytest.raises(sink.SinkStopped):
                value.append(b"{}\n") if operation == "append" else value.finish()
        return real(fd, raw)
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", reenter)
        with pytest.raises(sink.SinkStopped):
            value.append(b"{}\n")
    assert value.snapshot().confirmed_events == 0
    value.finish()


@pytest.mark.parametrize("failure", ("write", "fsync", "reentry"))
def test_finish_is_consumed_even_when_terminal_retention_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    value = create(tmp_path)
    write, sync = os.write, os.fsync
    def terminal_write(fd: int, raw: bytes | memoryview) -> int:
        if failure == "write":
            write(fd, raw[:2])
            raise OSError("terminal partial")
        if failure == "reentry":
            with pytest.raises(sink.SinkStopped):
                value.finish()
        return write(fd, raw)
    def terminal_sync(fd: int) -> None:
        if failure == "fsync":
            raise OSError("terminal sync")
        sync(fd)
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", terminal_write)
        patch.setattr(os, "fsync", terminal_sync)
        result = value.finish()
    assert result.snapshot.finish_consumed and not result.terminal_acknowledged
    with pytest.raises(sink.SinkStopped):
        value.finish()
    with pytest.raises(sink.SinkStopped):
        value.append(b"{}\n")
    inspection = sink.inspect_sink(tmp_path / "sink", max_bytes=32768)
    assert inspection.terminal_state == "present-unconfirmed"


@pytest.mark.parametrize("change", ("missing-context", "extra-context-field", "partial-context", "unexpected-file", "shard-gap", "read-budget"))
def test_inspection_never_promotes_partial_or_substituted_material(tmp_path: Path, change: str) -> None:
    value = create(tmp_path)
    value.append(b"{}\n")
    value.finish()
    root = tmp_path / "sink"
    if change == "missing-context":
        (root / "context.json").unlink()
    elif change == "extra-context-field":
        data = json.loads((root / "context.json").read_bytes())
        data["verified"] = True
        (root / "context.json").write_text(json.dumps(data))
    elif change == "partial-context":
        (root / "context.json").write_bytes(b'{"')
    elif change == "unexpected-file":
        (root / "other").write_bytes(b"x")
    elif change == "shard-gap":
        (root / "events-00.jsonl").rename(root / "events-01.jsonl")
    if change in ("unexpected-file", "shard-gap", "read-budget"):
        with pytest.raises(ValueError):
            sink.inspect_sink(root, max_bytes=1 if change == "read-budget" else 32768)
    else:
        report = sink.inspect_sink(root, max_bytes=32768)
        assert not report.context_canonical and report.authenticity == "unchecked"


def test_largest_bounded_identity_context_and_terminal_fit_reserved_bytes(tmp_path: Path) -> None:
    actual = replace(context(max_calls=55100, max_bytes=64 * 1024**2), recorder_id="r" * 96, run_id="u" * 96)
    value = create(tmp_path, actual)
    value.finish()
    assert (tmp_path / "sink/context.json").stat().st_size <= 4096
    assert (tmp_path / "sink/terminal.json").stat().st_size <= 16384
    assert sink.inspect_sink(tmp_path / "sink", max_bytes=32768).actual_bytes < 20480
    # Maximum metadata shape, without allocating sixteen full data shards.
    worst = sink.SinkSnapshot(110201, 110200, 64 * 1024**2, 64 * 1024**2,
                              64 * 1024**2, True, True,
                              tuple(sink.SinkFault("ownership_or_reentry", "e" * 192, False)
                                    for _ in range(sink.MAX_FAULTS)), 99)
    shards = [asdict(sink.ShardObservation(f"events-{i:02}.jsonl", sink.SHARD_BYTES,
                                          "f" * 64, 110201, 4095)) for i in range(16)]
    raw = sink._encode({"schema": sink.SCHEMA, "state": "pending_external_confirmation",
                        "context_sha256": "f" * 64,
                        "snapshot_before_terminal": asdict(worst), "shards": shards}, 16384)
    assert len(raw) <= 16384


def test_first_context_write_failure_keeps_partial_root_and_consumes_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = os.write
    error = OSError("context partial")
    def fail(fd: int, raw: bytes | memoryview) -> NoReturn:
        real(fd, raw[:2])
        raise error
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", fail)
        with pytest.raises(OSError) as caught:
            create(tmp_path)
    assert caught.value is error
    assert (tmp_path / "sink/context.json").read_bytes() == b'{"'
    with pytest.raises(FileExistsError):
        create(tmp_path)
    report = sink.inspect_sink(tmp_path / "sink", max_bytes=32768)
    assert not report.context_canonical and report.terminal_state == "missing"


def test_name_swap_during_fsync_cannot_acknowledge_wrong_named_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = create(tmp_path)
    real = os.fsync
    moved = False
    def swap(fd: int) -> None:
        nonlocal moved
        real(fd)
        if fd == value._fd and os.fstat(fd).st_size and not moved:
            moved = True
            path = tmp_path / "sink/events-00.jsonl"
            path.rename(tmp_path / "preserved")
            path.write_bytes(b"different\n")
            path.chmod(0o600)
    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", swap)
        with pytest.raises(ValueError):
            value.append(b"{}\n")
    assert value.snapshot().confirmed_events == 0 and value.snapshot().reserved_bytes == 3
    value.finish()


def test_exact_4096_byte_event_is_retained_without_truncation(tmp_path: Path) -> None:
    value = create(tmp_path)
    raw = b"x" * 4095 + b"\n"
    value.append(raw)
    result = value.finish()
    assert result.snapshot.confirmed_bytes == 4096
    assert (tmp_path / "sink/events-00.jsonl").read_bytes() == raw
