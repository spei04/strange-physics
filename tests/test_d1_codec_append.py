"""Independent raw vectors and owned fake callbacks; no recorder/sink installation."""

from __future__ import annotations

import builtins
import json
import math
import os
import threading
from copy import deepcopy
from typing import Any, NoReturn

import pytest
from d1_codec_append import BridgeStopped, CodecAppendBridge, _context, classify_raw
from d1_primitive_codec import PrimitiveEventCodec
from d1_primitive_codec_table import PROTOCOL_SHA256, TableIdentity, build_table, parse_table

DECIMAL: dict[str, object] = {"kind": "decimal", "parts": ["1", "12300", "-4"]}


def raw(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def intent() -> dict[str, Any]:
    return {
        "ordinal": 0,
        "call_id": "c00000",
        "instance_id": "i12",
        "primitive": "log",
        "scope": ["ct", "s0"],
        "arguments": deepcopy(DECIMAL),
    }


def event(
    call: dict[str, Any] | None = None, *, sequence: int = 0, returned: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "kind": "intent" if returned is None else "returned",
        "intent": intent() if call is None else call,
        "returned": returned,
        "fault": None,
    }


def failed(
    call: dict[str, Any] | None, *, sequence: int, phase: str = "primitive", ordinal: int = 0
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "kind": "failed",
        "intent": call,
        "returned": None,
        "fault": {
            "ordinal": ordinal,
            "phase": phase,
            "exception_type": "builtins.ValueError",
            "exception_type_complete": True,
            "call_id": None if call is None or phase == "reentry" else call["call_id"],
        },
    }


def context() -> dict[str, Any]:
    return {
        "schema": "strange-physics.d1-primitive-sink.v1",
        "recorder_id": "recorder0",
        "run_id": "run0",
        "source_commit": "1" * 40,
        "source_tree": "2" * 40,
        "protocol_sha256": PROTOCOL_SHA256,
        "source_manifest_sha256": "3" * 64,
        "recorder_sha256": "4" * 64,
        "sink_sha256": "6" * 64,
        "max_calls": 55100,
        "max_bytes": 16000000,
        "max_events": 110201,
        "event_capacity": 15979520,
        "event_bytes": 4096,
        "shard_bytes": 4194304,
        "max_shards": 16,
        "context_bytes": 4096,
        "terminal_bytes": 16384,
    }


@pytest.fixture(scope="module")
def table_raw() -> bytes:
    return build_table(
        TableIdentity(
            "1" * 40, "2" * 40, PROTOCOL_SHA256, "3" * 64, "4" * 64, "5" * 64, "run0", "recorder0"
        ),
        ("fake-owned-member",) * 14,
    )


@pytest.fixture(autouse=True)
def forbid_primitives(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("No primitive or installed recorder/sink in this suite")

    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.removeprefix("tests.") in {
            "d1_primitive_recording",
            "d1_primitive_sink",
            "endpoint_belief_reference",
            "d1_fixture_reference",
            "d1_prefix_evidence",
            "d1_bounds",
        } or name.startswith("strange_physics"):
            forbidden()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for name in ("exp", "log", "sin", "cos", "sqrt"):
        monkeypatch.setattr(math, name, forbidden)


def make(table_raw: bytes, lines: list[bytes]) -> CodecAppendBridge:
    return CodecAppendBridge(table_raw, raw(context()), append=lines.append)


def test_exact_lines_only_acknowledge_after_callback_returns(table_raw: bytes) -> None:
    observations: list[tuple[bytes, int]] = []

    def append(line: bytes) -> None:
        current = bridge.snapshot()
        assert current.last_attempt is not None and current.last_attempt.callback == "entered"
        observations.append((line, current.acknowledgements))

    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    bridge.append(raw(event()))
    bridge.append(raw(event(sequence=1, returned=deepcopy(DECIMAL))))
    assert observations == [
        (raw(["i", 0, 0, 12, 2, [4, 2], ["d", "1", "12300", "-4"]]), 0),
        (raw(["r", 1, 0, ["d", "1", "12300", "-4"]]), 1),
    ]
    snapshot = bridge.snapshot()
    assert (
        snapshot.raw_attempts,
        snapshot.physical_attempts,
        snapshot.callback_returns,
        snapshot.acknowledgements,
    ) == (2, 2, 2, 2)
    assert snapshot.next_ordinal == 1 and snapshot.next_sequence == 2
    assert snapshot.activation == "not-established"
    assert snapshot.binding.material_authenticity == "unchecked"


def test_return_write_error_preserves_last_intent_after_codec_advance(table_raw: bytes) -> None:
    lines: list[bytes] = []
    original = OSError("owned fake short-write uncertainty")

    def append(line: bytes) -> None:
        lines.append(line)
        if len(lines) == 2:
            raise original

    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    bridge.append(raw(event()))
    with pytest.raises(OSError) as caught:
        bridge.append(raw(event(sequence=1, returned=deepcopy(DECIMAL))))
    assert caught.value is original
    before = bridge.snapshot()
    assert before.next_ordinal == 1 and before.next_sequence == 2
    assert before.physical_bytes == sum(
        map(len, lines)
    )  # Full unknown reservations, not measured writes.
    assert (
        before.first_failed_attempt is not None and before.first_failed_attempt.callback == "raised"
    )
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=2, phase="return_sink")))
    after = bridge.snapshot()
    assert len(lines) == 2 and after.physical_attempts == 2 and after.acknowledgements == 1
    assert after.last_attempt is not None and after.last_attempt.kind == "failed"
    assert after.last_attempt.callback == "not_entered" and after.terminal_consumed
    assert after.first_failed_attempt == before.first_failed_attempt
    assert bridge.first_exception is original


def test_intent_append_failure_never_retries_physical_callback(table_raw: bytes) -> None:
    original = PermissionError("fake intent write")
    seen: list[bytes] = []

    def append(line: bytes) -> None:
        seen.append(line)
        raise original

    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    with pytest.raises(PermissionError):
        bridge.append(raw(event()))
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=1, phase="intent_sink")))
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=1, phase="intent_sink")))
    assert len(seen) == 1 and bridge.snapshot().raw_attempts == 2
    assert bridge.first_exception is original and bridge.snapshot().acknowledgements == 0


def test_raw_contract_failure_and_one_failed_event_are_never_acknowledged(table_raw: bytes) -> None:
    call = intent()
    call["scope"] = ["outside/fixed-plan"]  # Valid recorder token, not a table scope.
    first = raw(event(call))
    last = raw(failed(call, sequence=1, phase="intent_sink"))
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    for line in (first, last):
        with pytest.raises(BridgeStopped):
            bridge.append(line)
    snapshot = bridge.snapshot()
    assert lines == [first, last]
    assert (snapshot.fallback_attempts, snapshot.callback_returns, snapshot.acknowledgements) == (
        2,
        2,
        0,
    )
    assert (
        snapshot.first_failed_attempt is not None and not snapshot.first_failed_attempt.acknowledged
    )
    assert snapshot.first_failed_attempt.callback == "returned"
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    assert lines == [first, last]


def test_unavailable_return_stops_then_accepts_only_failed_forensics(table_raw: bytes) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    bridge.append(raw(event()))
    unavailable = raw(
        event(sequence=1, returned={"kind": "unavailable", "parts": ["owned.\u03a9Type"]})
    )
    last = raw(failed(intent(), sequence=2, phase="return_encoding"))
    with pytest.raises(BridgeStopped):
        bridge.append(unavailable)
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    assert lines[1:] == [unavailable, last]
    assert bridge.snapshot().acknowledgements == 1
    assert bridge.snapshot().fallback_attempts == 2


@pytest.mark.parametrize(
    "ordinal", [0, 1, 2, 3], ids=["first", "second", "encoding-two", "encoding-three"]
)
def test_failed_fault_ordinal_preserved_without_unseen_unavailable_line(
    table_raw: bytes, ordinal: int
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    bridge.append(raw(event()))
    # Ordinal3 remains valid when unavailable _emit failed before reservation:
    # no unavailable callback and failed uses the very next visible sequence.
    last = raw(failed(intent(), sequence=1, phase="return_encoding", ordinal=ordinal))
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    assert lines[-1] == last and len(lines) == 2
    parsed = classify_raw(last)
    assert parsed.fault is not None and parsed.fault.ordinal == ordinal
    assert parsed.material_authenticity == "unchecked"


@pytest.mark.parametrize(
    "kind", ["null-preflight", "unseen-intent", "reentry"], ids=["null", "unseen", "reentry"]
)
def test_source_terminal_join_variants(table_raw: bytes, kind: str) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    if kind == "reentry":
        bridge.append(raw(event()))
        last = raw(failed(intent(), sequence=1, phase="reentry"))
    elif kind == "unseen-intent":
        last = raw(failed(intent(), sequence=0, phase="intent_sink"))
    else:
        last = raw(failed(None, sequence=0, phase="preflight"))
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    assert lines[-1] == last
    parsed = classify_raw(last)
    if kind == "reentry":
        assert (
            parsed.intent is not None and parsed.fault is not None and parsed.fault.call_id is None
        )


def test_failure_fallback_storage_error_is_not_replaced_by_intentional_stop(
    table_raw: bytes,
) -> None:
    original = OSError("fake raw write")
    calls: list[bytes] = []

    def append(line: bytes) -> None:
        calls.append(line)
        raise original

    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    with pytest.raises(OSError) as caught:
        bridge.append(raw(failed(None, sequence=0, phase="preflight")))
    assert caught.value is original and bridge.first_exception is original
    assert len(calls) == 1 and bridge.snapshot().callback_returns == 0


def test_original_stop_and_later_failure_are_separate(table_raw: bytes) -> None:
    lines: list[bytes] = []
    secondary = PermissionError("fake failed-event append")

    def append(line: bytes) -> None:
        lines.append(line)
        if len(lines) == 2:
            raise secondary

    call = intent()
    call["scope"] = ["other"]
    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    with pytest.raises(BridgeStopped) as first:
        bridge.append(raw(event(call)))
    with pytest.raises(PermissionError) as second:
        bridge.append(raw(failed(call, sequence=1, phase="intent_sink")))
    assert second.value is secondary and bridge.first_exception is first.value
    snapshot = bridge.snapshot()
    assert (
        snapshot.first_failed_attempt is not None
        and snapshot.first_failed_attempt.callback == "returned"
    )
    assert snapshot.last_attempt is not None and snapshot.last_attempt.callback == "raised"


@pytest.mark.parametrize("nested", ["append", "finish"], ids=["append", "finish"])
def test_swallowed_reentry_cannot_acknowledge_or_resurrect(table_raw: bytes, nested: str) -> None:
    nested_errors: list[BaseException] = []
    calls: list[bytes] = []

    def append(line: bytes) -> None:
        calls.append(line)
        try:
            if nested == "append":
                bridge.append(b"not even parsed")
            else:
                bridge.finish()
        except BridgeStopped as error:
            nested_errors.append(error)

    bridge = CodecAppendBridge(table_raw, raw(context()), append=append)
    with pytest.raises(BridgeStopped) as outer:
        bridge.append(raw(event()))
    assert outer.value is nested_errors[0] and bridge.first_exception is nested_errors[0]
    snapshot = bridge.snapshot()
    assert (
        snapshot.callback_returns == 1
        and snapshot.acknowledgements == 0
        and snapshot.physical_blocked
    )
    assert snapshot.last_attempt is not None and snapshot.last_attempt.callback == "returned"
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=1, phase="intent_sink")))
    assert len(calls) == 1
    assert bridge.finish().finish_consumed


@pytest.mark.parametrize("owner", ["pid", "thread"], ids=["pid", "thread"])
def test_wrong_owner_stops_before_any_callback(
    table_raw: bytes, owner: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    with monkeypatch.context() as patch:
        if owner == "pid":
            patch.setattr(os, "getpid", lambda: -1)
        else:
            patch.setattr(threading, "get_ident", lambda: -1)
        with pytest.raises(BridgeStopped):
            bridge.append(raw(event()))
    assert lines == [] and bridge.snapshot().raw_attempts == 0
    assert bridge.finish().finish_consumed


def test_finish_is_once_no_io_and_diagnostics_cannot_resume(table_raw: bytes) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    snapshot = bridge.finish()
    with pytest.raises(BridgeStopped):
        bridge.finish()
    with pytest.raises(BridgeStopped):
        bridge.append(raw(event()))
    assert lines == [] and snapshot.raw_attempts == 0 and snapshot.finish_consumed
    assert bridge.snapshot() == snapshot


@pytest.mark.parametrize(
    "field",
    [
        "source_commit",
        "source_tree",
        "protocol_sha256",
        "source_manifest_sha256",
        "recorder_sha256",
        "run_id",
        "recorder_id",
    ],
    ids=["commit", "tree", "protocol", "manifest", "recorder", "run-id", "recorder-id"],
)
def test_context_shared_identity_mismatch_has_no_callback(table_raw: bytes, field: str) -> None:
    bad = context()
    bad[field] = "wrong"
    lines: list[bytes] = []
    with pytest.raises(ValueError):
        CodecAppendBridge(table_raw, raw(bad), append=lines.append)
    assert lines == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("max_calls", 55099, id="call-plan"),
        pytest.param("max_events", 110200, id="event-plan"),
        pytest.param("event_bytes", 4097, id="event-cap"),
        pytest.param("shard_bytes", 4194305, id="shard-cap"),
        pytest.param("max_shards", 17, id="shards"),
        pytest.param("context_bytes", 4095, id="context-reserve"),
        pytest.param("terminal_bytes", 16383, id="terminal-reserve"),
        pytest.param("max_bytes", 16777216, id="no-partition-withholding"),
        pytest.param("max_bytes", 20480, id="no-event-space"),
        pytest.param("event_capacity", 16000000, id="metadata-counted"),
        pytest.param("max_calls", True, id="boolean"),
        pytest.param("max_bytes", 16000000.0, id="float"),
        pytest.param("sink_sha256", "G" * 64, id="sink-hash"),
        pytest.param("schema", "other", id="schema"),
        pytest.param("verified", True, id="unknown-claim"),
    ],
)
def test_context_rejects_unsupported_claims(table_raw: bytes, field: str, value: object) -> None:
    bad = context()
    bad[field] = value
    with pytest.raises(ValueError):
        CodecAppendBridge(
            table_raw, raw(bad), append=lambda line: pytest.fail("constructor callback")
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "padding",
        "nested",
        "truncated",
        "oversize",
        "long-int",
        "nonfinite",
        "root-list",
        "non-ascii",
    ],
    ids=[
        "duplicate",
        "padding",
        "nested",
        "truncated",
        "oversize",
        "long-int",
        "nonfinite",
        "root-list",
        "non-ascii",
    ],
)
def test_context_raw_parser_is_bounded_and_canonical(table_raw: bytes, mutation: str) -> None:
    original = raw(context())
    if mutation == "duplicate":
        bad = b'{"max_calls":55100,' + original[1:]
    elif mutation == "padding":
        bad = b" " + original
    elif mutation == "nested":
        bad = b'{"x":' + b"[" * 5 + b"0" + b"]" * 5 + b"}\n"
    elif mutation == "truncated":
        bad = original[:-3]
    elif mutation == "oversize":
        bad = b" " * 4097
    elif mutation == "long-int":
        bad = original.replace(b'"max_bytes":16000000', b'"max_bytes":100000000')
    elif mutation == "nonfinite":
        bad = original.replace(b'"max_bytes":16000000', b'"max_bytes":NaN')
    elif mutation == "root-list":
        bad = b"[]\n"
    else:
        bad = original.replace(b"run0", "r\u03a9".encode())
    with pytest.raises(ValueError):
        CodecAppendBridge(table_raw, bad, append=lambda line: pytest.fail("constructor callback"))


def test_eight_digit_context_limit_does_not_widen_event_integers(table_raw: bytes) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    assert bridge.snapshot().binding.max_bytes == 16000000
    bad = raw(event()).replace(b'"sequence":0', b'"sequence":10000000')
    with pytest.raises(ValueError):
        bridge.append(bad)
    assert lines == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("ordinal", 4, id="snapshot-only-four"),
        pytest.param("ordinal", -1, id="negative"),
        pytest.param("ordinal", True, id="bool-ordinal"),
        pytest.param("phase", "fault_retention", id="snapshot-phase"),
        pytest.param("phase", "unknown", id="unknown-phase"),
        pytest.param("call_id", "other", id="call-substitution"),
        pytest.param("exception_type", "x" * 193, id="long-type"),
        pytest.param("exception_type", "", id="empty-type"),
        pytest.param("exception_type_complete", 1, id="bool-coercion"),
        pytest.param("exception_type_complete", False, id="false-short-type"),
        pytest.param("extra", None, id="extra"),
    ],
)
def test_fault_scalar_contract_rejects_forged_shapes(field: str, value: object) -> None:
    bad = failed(intent(), sequence=1)
    bad["fault"][field] = value
    with pytest.raises(ValueError):
        classify_raw(raw(bad))


@pytest.mark.parametrize(
    "mutation",
    [
        "null-call",
        "nonnull-reentry",
        "later-reentry",
        "null-primitive",
        "later-primitive",
        "failed-value",
        "missing-fault",
    ],
    ids=[
        "null-call",
        "nonnull-reentry",
        "later-reentry",
        "null-primitive",
        "later-primitive",
        "failed-value",
        "missing-fault",
    ],
)
def test_phase_aware_fault_joins(mutation: str) -> None:
    bad = failed(intent(), sequence=1)
    if mutation == "null-call":
        bad["fault"]["call_id"] = None
    elif mutation == "nonnull-reentry":
        bad["fault"]["phase"] = "reentry"
    elif mutation == "later-reentry":
        bad["fault"].update(phase="reentry", call_id=None, ordinal=1)
    elif mutation == "null-primitive":
        bad["intent"] = None
        bad["fault"]["call_id"] = None
    elif mutation == "later-primitive":
        bad["fault"]["ordinal"] = 2
    elif mutation == "failed-value":
        bad["returned"] = deepcopy(DECIMAL)
    else:
        bad["fault"] = None
    with pytest.raises(ValueError):
        classify_raw(raw(bad))


@pytest.mark.parametrize(
    "mutation",
    [
        "sequence",
        "return-intent",
        "failed-intent",
        "missing-intent",
        "second-intent",
        "failed-null",
    ],
    ids=[
        "sequence",
        "return-substitution",
        "failed-substitution",
        "return-without-intent",
        "second-intent",
        "erase-intent",
    ],
)
def test_sequence_and_full_intent_substitution_stop_before_write(
    table_raw: bytes, mutation: str
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    bridge.append(raw(event()))
    call = intent()
    call["arguments"] = {"kind": "decimal", "parts": ["1", "12300", "-5"]}
    if mutation == "sequence":
        bad = event(sequence=2, returned=deepcopy(DECIMAL))
    elif mutation == "return-intent":
        bad = event(call, sequence=1, returned=deepcopy(DECIMAL))
    elif mutation == "failed-intent":
        bad = failed(call, sequence=1)
    elif mutation == "missing-intent":
        bad = event(sequence=1, returned=deepcopy(DECIMAL))
        bad["intent"] = None
    elif mutation == "second-intent":
        bad = event(sequence=1)
    else:
        bad = failed(None, sequence=1, phase="preflight")
    with pytest.raises(ValueError):
        bridge.append(raw(bad))
    assert len(lines) == 1 and bridge.snapshot().physical_blocked
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=1)))
    assert len(lines) == 1


@pytest.mark.parametrize(
    "raw_bad",
    [
        pytest.param(b" " * 4097, id="predecode-cap"),
        pytest.param(b'{"sequence":0,"sequence":0}\n', id="duplicate"),
        pytest.param(b'{"sequence":false}\n', id="bool"),
        pytest.param(b"[[[[[0]]]]]\n", id="deep"),
        pytest.param(b"{} \n", id="whitespace"),
        pytest.param(b"{\n", id="truncated"),
        pytest.param(b"[]\n", id="array"),
        pytest.param(b"{}\n", id="missing"),
    ],
)
def test_bad_raw_input_is_not_blindly_fallback_retained(table_raw: bytes, raw_bad: bytes) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    with pytest.raises(ValueError):
        bridge.append(raw_bad)
    assert lines == [] and bridge.snapshot().stopped


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        pytest.param("_raw_attempts", 110201, id="event-count"),
        pytest.param("_raw_bytes", 67108864, id="logical-bytes"),
        pytest.param("_physical_attempts", 110201, id="physical-count"),
        pytest.param("_physical_bytes", 15979520, id="physical-bytes"),
    ],
)
def test_reservation_edges_without_building_a_batch(
    table_raw: bytes, attribute: str, value: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    # Test-only counter seam, not an authenticated checkpoint or resume API.
    monkeypatch.setattr(bridge, attribute, value)
    with pytest.raises(BridgeStopped):
        bridge.append(raw(event()))
    assert lines == [] and bridge.snapshot().acknowledgements == 0


def test_table_bytes_are_revalidated_before_context_or_callback(table_raw: bytes) -> None:
    lines: list[bytes] = []
    with pytest.raises(ValueError):
        CodecAppendBridge(b" " + table_raw, raw(context()), append=lines.append)
    assert lines == []


@pytest.mark.parametrize("capacity", [1, 8192], ids=["tiny", "failure-only"])
def test_tiny_context_does_not_claim_a_failure_reserve(table_raw: bytes, capacity: int) -> None:
    supplied = context()
    supplied.update(max_bytes=20480 + capacity, event_capacity=capacity)
    lines: list[bytes] = []
    with pytest.raises(ValueError):
        CodecAppendBridge(table_raw, raw(supplied), append=lines.append)
    assert lines == []


def test_ordinary_capacity_cannot_borrow_from_terminal_reserve(
    table_raw: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    ordinary = bridge.snapshot().binding.ordinary_capacity
    assert ordinary == 15979520 - 8192
    # Explicit synthetic accounting seam; no full stream or resume evidence.
    monkeypatch.setattr(bridge, "_compact_bytes", ordinary)
    monkeypatch.setattr(bridge, "_physical_bytes", ordinary)
    with pytest.raises(BridgeStopped, match="failure reserve"):
        bridge.append(raw(event()))
    assert lines == []
    last = raw(failed(intent(), sequence=1, phase="intent_sink"))
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    result = bridge.snapshot()
    assert lines == [last] and result.compact_bytes == ordinary
    assert result.fallback_bytes == len(last)
    assert result.physical_bytes == ordinary + len(last)
    assert result.physical_bytes <= result.binding.event_capacity


@pytest.mark.parametrize("boundary", ["event", "context"], ids=["event", "context"])
def test_predecode_cap_before_json_loader(
    table_raw: bytes, boundary: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)

    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Oversized bytes must not reach JSON decoding")

    parsed_table = parse_table(table_raw)
    with monkeypatch.context() as patch:
        patch.setattr(json, "loads", forbidden)
        with pytest.raises(ValueError):
            if boundary == "event":
                bridge.append(b" " * 4097)
            else:
                # Internal parser test, not a public constructed-view boundary.
                _context(b" " * 4097, parsed_table)
    assert lines == []


def test_internal_conversion_error_allows_one_source_joined_failed_event(
    table_raw: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    original = RuntimeError("owned fake converter fault")
    calls: list[bytes] = []

    def broken(self: PrimitiveEventCodec, line: bytes) -> NoReturn:
        calls.append(line)
        raise original

    monkeypatch.setattr(PrimitiveEventCodec, "convert", broken)
    with pytest.raises(RuntimeError) as caught:
        bridge.append(raw(event()))
    assert caught.value is original and lines == []
    last = raw(failed(intent(), sequence=1, phase="intent_sink"))
    with pytest.raises(BridgeStopped):
        bridge.append(last)
    assert lines == [last] and len(calls) == 1
    assert bridge.first_exception is original and bridge.snapshot().acknowledgements == 0


def test_reparsed_boundary_rejects_output_view_as_input(table_raw: bytes) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    invalid_input: Any = classify_raw(raw(event()))
    with pytest.raises(ValueError):
        bridge.append(invalid_input)
    assert lines == [] and bridge.snapshot().raw_attempts == 0


@pytest.mark.parametrize("value", [False, 0], ids=["boolean", "integer"])
def test_non_none_callback_return_cannot_acknowledge(table_raw: bytes, value: object) -> None:
    calls: list[bytes] = []

    def malformed(line: bytes) -> Any:
        calls.append(line)
        return value

    bridge = CodecAppendBridge(table_raw, raw(context()), append=malformed)
    with pytest.raises(ValueError, match="return None"):
        bridge.append(raw(event()))
    assert bridge.snapshot().callback_returns == 1 and bridge.snapshot().acknowledgements == 0
    with pytest.raises(BridgeStopped):
        bridge.append(raw(failed(intent(), sequence=1, phase="intent_sink")))
    assert len(calls) == 1


@pytest.mark.parametrize("completed", [False, True], ids=["after-intent", "after-return"])
def test_terminal_phase_cannot_backtrack_observed_progress(
    table_raw: bytes, completed: bool
) -> None:
    lines: list[bytes] = []
    bridge = make(table_raw, lines)
    bridge.append(raw(event()))
    if completed:
        bridge.append(raw(event(sequence=1, returned=deepcopy(DECIMAL))))
    before = len(lines)
    terminal = failed(intent(), sequence=before, phase="primitive" if completed else "preflight")
    with pytest.raises(ValueError):
        bridge.append(raw(terminal))
    assert len(lines) == before and bridge.snapshot().terminal_consumed
