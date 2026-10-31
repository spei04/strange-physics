"""Conditional real recorder/bridge/file handoff with fixed owned fake callbacks only."""

from __future__ import annotations

import builtins
import errno
import json
import math
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, NoReturn

import d1_primitive_sink as sink_module
import pytest
from d1_codec_append import BridgeStopped, CodecAppendBridge, classify_raw
from d1_primitive_codec import PrimitiveEventCodec
from d1_primitive_codec_table import PROTOCOL_SHA256, TableIdentity, build_table
from d1_primitive_recording import PrimitiveRecorder, RecorderStopped
from d1_primitive_sink import PrimitiveFileSink, SinkCloseout, SinkContext, inspect_sink


@pytest.fixture(autouse=True)
def no_scientific_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Only fixed owned fake callbacks in handoff tests")

    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.removeprefix("tests.") in {
            "endpoint_belief_reference", "d1_fixture_reference", "d1_prefix_evidence",
            "d1_bounds", "grid_q1_driver", "grid_q1_reference",
        } or name in {
            "strange_physics.native_prediction", "strange_physics.native_endpoint_beliefs",
            "strange_physics.simulation", "strange_physics.finite_normalizer",
        }:
            forbidden()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for name in ("exp", "log", "sin", "cos", "sqrt"):
        monkeypatch.setattr(math, name, forbidden)


def fake_table() -> bytes:
    return build_table(
        TableIdentity("1" * 40, "2" * 40, PROTOCOL_SHA256, "3" * 64,
                      "4" * 64, "5" * 64, "handoff-run", "handoff-recorder"),
        ("owned-fake-definition",) * 14,
    )


def fake_context() -> SinkContext:
    # Complete fixed call declaration, but this test executes only a tiny prefix.
    # The hash strings are synthetic declarations, not source authentication.
    return SinkContext("handoff-recorder", "handoff-run", "1" * 40, "2" * 40,
                       PROTOCOL_SHA256, "3" * 64, "4" * 64, "6" * 64, 55100, 65536)


def bounded_read(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        result = stream.read(limit + 1)
    assert len(result) <= limit
    return result


@dataclass
class OwnedFiles:
    root: Path
    table: bytes
    sink: PrimitiveFileSink
    context_raw: bytes = b""
    bridge: CodecAppendBridge | None = None
    closeout: SinkCloseout | None = None
    physical_calls: list[bytes] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)
    cleanup_errors: list[BaseException] = field(default_factory=list)
    body_error: BaseException | None = None
    bridge_finishes: int = 0
    sink_finishes: int = 0
    descriptors_checked_closed: bool = False
    payload_bytes: int = 0
    close_injections: int = 0
    close_target_fd: int | None = None


@contextmanager
def owned_files(tmp_path: Path, *, close_fault: OSError | None = None,
                monkeypatch: pytest.MonkeyPatch | None = None) -> Iterator[OwnedFiles]:
    """Test-only resource owner: no metadata activation or production coordinator."""
    tmp_path.chmod(0o700)
    table = fake_table()  # Kept in memory only; no T/A file is added to sink root.
    root = tmp_path / "sink"
    value = OwnedFiles(root, table, PrimitiveFileSink.create(root, fake_context()))
    try:
        value.context_raw = bounded_read(root / "context.json", 4096)
        yield value
    except BaseException as body_error:
        value.body_error = body_error
        raise
    finally:
        owned_fds = tuple(fd for fd in (value.sink._fd, value.sink._anchor.directory,
                                        value.sink._anchor.parent) if fd is not None)
        if value.bridge is not None:
            value.bridge_finishes += 1
            try:
                value.bridge.finish()
            except BaseException as bridge_close_error:
                value.cleanup_errors.append(bridge_close_error)
        value.sink_finishes += 1
        try:
            if close_fault is None:
                value.closeout = value.sink.finish()
            elif monkeypatch is None or value.sink._fd is None:
                value.cleanup_errors.append(AssertionError("Missing owned close-injection target"))
                value.closeout = value.sink.finish()
            else:
                target_fd: int = value.sink._fd
                assert target_fd in owned_fds
                value.close_target_fd = target_fd
                injected_close_error: OSError = close_fault
                real_close = os.close

                def lost_confirmation(fd: int) -> None:
                    real_close(fd)
                    if fd == target_fd and value.close_injections == 0:
                        value.close_injections += 1
                        raise injected_close_error

                # Only this owned fd loses confirmation after an actual close.
                # Reused fd numbers and other descriptors pass through unchanged.
                with monkeypatch.context() as patch:
                    patch.setattr(os, "close", lost_confirmation)
                    value.closeout = value.sink.finish()
        except BaseException as sink_close_error:
            value.cleanup_errors.append(sink_close_error)
        # All event-write mocks have already restored. Inspect the actual owned
        # descriptors without reopening or retrying an ambiguous close.
        try:
            for fd in owned_fds:
                try:
                    os.fstat(fd)
                except OSError as fd_error:
                    assert fd_error.errno == errno.EBADF
                else:
                    raise AssertionError("Owned sink descriptor was not closed")
            value.descriptors_checked_closed = True
            names = {path.name for path in root.iterdir()}
            assert names <= {"context.json", "events-00.jsonl", "terminal.json"}
            value.payload_bytes = sum(path.stat().st_size for path in root.iterdir())
            assert value.payload_bytes <= 32768
        except BaseException as observation_error:
            value.cleanup_errors.append(observation_error)
        if value.cleanup_errors:
            if value.body_error is None:
                raise value.cleanup_errors[0]
            for supplemental_error in value.cleanup_errors:
                value.body_error.add_note("Supplemental owned cleanup observation: " + type(supplemental_error).__name__)


def connect(value: OwnedFiles, *, after_append: Callable[[], None] | None = None) -> tuple[CodecAppendBridge, PrimitiveRecorder]:
    def append(line: bytes) -> None:
        value.timeline.append("append-start")
        value.physical_calls.append(line)
        value.sink.append(line)
        value.timeline.append("append-return")
        if after_append is not None:
            after_append()

    bridge = CodecAppendBridge(value.table, value.context_raw, append=append)
    value.bridge = bridge
    return bridge, PrimitiveRecorder(bridge.append, max_calls=55100, max_bytes=67108864)


def log_call(recorder: PrimitiveRecorder, invoke: Callable[[], Decimal]) -> Decimal:
    return recorder.call(call_id="c00000", instance_id="i12", primitive="log",
                         scope=("ct", "s0"), arguments=Decimal("0"), invoke=invoke)


def assert_closed(value: OwnedFiles, *, bridge: bool = True, uncertain: bool = False) -> None:
    assert value.sink_finishes == 1 and value.bridge_finishes == int(bridge)
    assert value.descriptors_checked_closed
    assert value.closeout is not None
    assert value.closeout.descriptors_closed == (not uncertain)
    assert value.closeout.terminal_acknowledged
    terminal = json.loads(bounded_read(value.root / "terminal.json", 16384))
    assert terminal["state"] == "pending_external_confirmation"


@pytest.mark.parametrize("representation", ["decimal", "binary64"], ids=["decimal-quantum", "signed-binary64"])
def test_actual_success_handoff_is_ordered_and_exact(tmp_path: Path, representation: Literal["decimal", "binary64"]) -> None:
    with owned_files(tmp_path) as value:
        bridge, recorder = connect(value)
        invoked: list[str] = []

        def entered() -> None:
            invoked.append("fake")
            value.timeline.append("fake-invoke")
            snapshot = recorder.snapshot()
            assert len(snapshot.events) == 1 and snapshot.events[0].delivery == "confirmed"
            assert bridge.snapshot().acknowledgements == 1
            assert value.sink.snapshot().confirmed_events == 1

        if representation == "decimal":
            def decimal_result() -> Decimal:
                entered()
                return Decimal("1.2500")

            actual_decimal = log_call(recorder, decimal_result)
            assert actual_decimal.as_tuple() == Decimal("1.2500").as_tuple()
        else:
            def binary_result() -> float:
                entered()
                return -0.0

            actual_binary = recorder.call(call_id="c00000", instance_id="i13", primitive="native_exp",
                                          scope=("nv", "p00", "n0000"), arguments=-0.0, invoke=binary_result)
            assert actual_binary.hex() == "-0x0.0p+0"
        value.timeline.append("consumer-handoff")
        assert invoked == ["fake"]
        assert value.timeline == ["append-start", "append-return", "fake-invoke", "append-start", "append-return", "consumer-handoff"]
        records = recorder.snapshot()
        assert (records.invoked, records.returned, records.primitive_failed) == (1, 1, 0)
        assert all(item.delivery == "confirmed" for item in records.events)
        assert bridge.snapshot().acknowledgements == value.sink.snapshot().confirmed_events == 2
        actual_lines = bounded_read(value.root / "events-00.jsonl", 12288).splitlines(keepends=True)
        assert actual_lines == value.physical_calls and len(actual_lines) == 2
        decoder = PrimitiveEventCodec(value.table, mode="expand")
        for line, recorded in zip(actual_lines, records.events, strict=True):
            expansion = decoder.convert(line)
            assert expansion.status == "converted" and expansion.raw_event == recorded.raw
        assert bridge.snapshot().activation == "not-established"
    assert_closed(value)
    assert value.cleanup_errors == []


def test_intent_write_failure_prevents_fake_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = OSError("owned intent-write fault")
    invoked: list[str] = []
    with owned_files(tmp_path) as value:
        bridge, recorder = connect(value)

        def no_write(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> NoReturn:
            assert fd == value.sink._fd and progress == [0] and raw.startswith(b'["i"')
            check()
            raise original

        def fake() -> Decimal:
            invoked.append("unexpected")
            return Decimal("1")

        with monkeypatch.context() as patch:
            patch.setattr(sink_module, "_write_remaining", no_write)
            with pytest.raises(OSError) as caught:
                log_call(recorder, fake)
        assert caught.value is original and recorder.first_exception is original
        assert invoked == [] and recorder.snapshot().invoked == 0
        assert len(value.physical_calls) == 1
        assert value.sink.snapshot().reserved_events == 1 and value.sink.snapshot().confirmed_events == 0
        assert all(item.delivery == "unknown" for item in recorder.snapshot().events)
        assert len(recorder.snapshot().events) == 2  # Intent plus failed logical Event; no physical retry.
        assert bridge.snapshot().physical_blocked and bridge.snapshot().acknowledgements == 0
    assert_closed(value)
    inspection = inspect_sink(value.root, max_bytes=32768)
    assert inspection.shards[0].complete_lines == 0 and inspection.shards[0].trailing_fragment_bytes == 0
    assert inspection.acknowledgement == inspection.execution == "not-inferred"


def test_return_partial_write_keeps_original_and_lost_close_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = OSError("owned return-prefix fault")
    secondary = OSError(errno.EIO, "owned synthetic lost close confirmation")
    invoked: list[str] = []
    fragments: list[bytes] = []

    with pytest.raises(OSError) as caught:
        with owned_files(tmp_path, close_fault=secondary, monkeypatch=monkeypatch) as value:
            bridge, recorder = connect(value)
            real_write = sink_module._write_remaining
            writes: list[bytes] = []

            def partial_return(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
                assert fd == value.sink._fd
                writes.append(raw)
                if len(writes) == 1:
                    real_write(fd, raw, progress, check)
                    return
                assert len(writes) == 2 and raw.startswith(b'["r"')
                check()
                count = os.write(fd, raw[:7])
                assert 0 < count <= 7
                progress[0] += count
                fragments.append(raw[:count])
                raise original

            def fake() -> Decimal:
                invoked.append("fake")
                return Decimal("1.2500")

            with monkeypatch.context() as patch:
                patch.setattr(sink_module, "_write_remaining", partial_return)
                log_call(recorder, fake)
            pytest.fail("A return-write failure cannot hand off the value")
    assert caught.value is original and value.body_error is original
    assert value.cleanup_errors == [] and recorder.first_exception is original
    assert value.close_injections == 1 and value.close_target_fd is not None
    assert value.sink.first_exception is original
    assert value.closeout is not None
    assert any(fault.phase == "data_close" for fault in value.closeout.snapshot.faults)
    assert invoked == ["fake"] and len(value.physical_calls) == 2
    records = recorder.snapshot()
    assert (records.invoked, records.returned, records.primitive_failed) == (1, 1, 0)
    assert [item.delivery for item in records.events] == ["confirmed", "unknown", "unknown"]
    assert bridge.snapshot().next_ordinal == 1 and bridge.snapshot().physical_blocked
    assert value.sink.snapshot().reserved_events == 2 and value.sink.snapshot().confirmed_events == 1
    assert value.sink.snapshot().reserved_bytes == sum(map(len, value.physical_calls))
    assert value.sink.snapshot().written_bytes == len(value.physical_calls[0]) + len(fragments[0])
    assert_closed(value, uncertain=True)
    observed = bounded_read(value.root / "events-00.jsonl", 12288)
    assert observed == value.physical_calls[0] + fragments[0]
    inspection = inspect_sink(value.root, max_bytes=32768)
    assert inspection.shards[0].complete_lines == 1
    assert inspection.shards[0].trailing_fragment_bytes == len(fragments[0])
    assert inspection.acknowledgement == "not-inferred"


def test_fake_primitive_exception_is_distinct_from_forensic_acknowledgement(tmp_path: Path) -> None:
    original = ArithmeticError("owned fake callback exception")
    invoked: list[str] = []
    with owned_files(tmp_path) as value:
        bridge, recorder = connect(value)

        def fake() -> NoReturn:
            invoked.append("fake")
            raise original

        with pytest.raises(ArithmeticError) as caught:
            log_call(recorder, fake)
        assert caught.value is original and recorder.first_exception is original
        records = recorder.snapshot()
        assert invoked == ["fake"] and (records.invoked, records.returned, records.primitive_failed) == (1, 0, 1)
        assert [item.delivery for item in records.events] == ["confirmed", "unknown"]
        assert [fault.phase for fault in records.faults] == ["primitive", "fault_retention"]
        assert bridge.snapshot().callback_returns == 2 and bridge.snapshot().acknowledgements == 1
        assert value.sink.snapshot().confirmed_events == 2 and value.sink.first_exception is None
        lines = bounded_read(value.root / "events-00.jsonl", 12288).splitlines(keepends=True)
        assert lines[1] == records.events[1].raw
        terminal_event = classify_raw(lines[1])
        assert terminal_event.fault is not None and terminal_event.fault.phase == "primitive"
    assert_closed(value)


def test_swallowed_recorder_reentry_invalid_return_produces_fault_three(tmp_path: Path) -> None:
    nested: list[BaseException] = []
    callbacks: list[str] = []
    with owned_files(tmp_path) as value:
        bridge, recorder = connect(value)

        def never() -> Decimal:
            pytest.fail("Stopped reentry must not invoke its fake callback")

        def invalid_after_reentry() -> Any:
            callbacks.append("outer")
            try:
                log_call(recorder, never)
            except RecorderStopped as error:
                nested.append(error)
            return object()  # Deliberately invalid retained Value, not a numeric result.

        with pytest.raises(ValueError) as outer:
            log_call(recorder, invalid_after_reentry)
        records = recorder.snapshot()
        assert callbacks == ["outer"] and len(nested) == 1
        assert recorder.first_exception is nested[0] and outer.value is not nested[0]
        assert [fault.phase for fault in records.faults] == ["reentry", "return_encoding", "return_sink", "return_encoding", "fault_retention"]
        assert [fault.ordinal for fault in records.faults] == [0, 1, 2, 3, 4]
        assert [item.delivery for item in records.events] == ["confirmed", "unknown", "unknown"]
        assert (records.invoked, records.returned, records.primitive_failed) == (1, 1, 0)
        lines = bounded_read(value.root / "events-00.jsonl", 12288).splitlines(keepends=True)
        assert len(lines) == 3 and lines[1:] == [item.raw for item in records.events[1:]]
        unavailable = classify_raw(lines[1])
        failed_event = classify_raw(lines[2])
        assert unavailable.unavailable and failed_event.fault is not None
        assert failed_event.fault.ordinal == 3 and failed_event.fault.phase == "return_encoding"
        assert failed_event.fault.exception_type == type(outer.value).__module__ + "." + type(outer.value).__qualname__
        assert value.sink.snapshot().confirmed_events == 3 and bridge.snapshot().acknowledgements == 1
        assert bridge.snapshot().fallback_attempts == 2
    assert_closed(value)


def test_swallowed_bridge_reentry_after_real_write_never_invokes_fake(tmp_path: Path) -> None:
    nested: list[BaseException] = []
    invoked: list[str] = []
    with owned_files(tmp_path) as value:
        def reenter() -> None:
            assert value.bridge is not None
            try:
                value.bridge.append(b"not parsed during reentry")
            except BridgeStopped as error:
                nested.append(error)

        bridge, recorder = connect(value, after_append=reenter)

        def fake() -> Decimal:
            invoked.append("unexpected")
            return Decimal("1")

        with pytest.raises(BridgeStopped) as caught:
            log_call(recorder, fake)
        assert len(nested) == 1 and caught.value is nested[0]
        assert recorder.first_exception is nested[0] and bridge.first_exception is nested[0]
        assert invoked == [] and recorder.snapshot().invoked == 0
        assert value.sink.snapshot().confirmed_events == 1
        assert bridge.snapshot().callback_returns == 1 and bridge.snapshot().acknowledgements == 0
        assert [item.delivery for item in recorder.snapshot().events] == ["unknown", "unknown"]
        assert len(value.physical_calls) == 1 and bridge.snapshot().physical_blocked
    assert_closed(value)


def test_actual_context_mismatch_still_closes_owned_sink_once(tmp_path: Path) -> None:
    with owned_files(tmp_path) as value:
        actual_context = value.context_raw
        changed_context = actual_context.replace(b'"run_id":"handoff-run"', b'"run_id":"other-run"')
        assert changed_context != actual_context
        callbacks: list[bytes] = []
        with pytest.raises(ValueError):
            CodecAppendBridge(value.table, changed_context, append=callbacks.append)
        assert callbacks == [] and value.sink.snapshot().reserved_events == 0
        assert value.bridge is None
        assert bounded_read(value.root / "context.json", 4096) == actual_context
    assert_closed(value, bridge=False)
    assert not (value.root / "events-00.jsonl").exists()
