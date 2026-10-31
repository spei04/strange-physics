"""Small hand-specified Event/wire vectors only; no primitives, sinks or batches."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, NoReturn

import d1_primitive_codec as codec
import pytest
from d1_primitive_codec_table import PROTOCOL_SHA256, TableIdentity, build_table

ZERO = "0x0.0p+0"
ONE = "0x1.0000000000000p+0"
DECIMAL = {"kind": "decimal", "parts": ["1", "12300", "-4"]}
POSITION = {"kind": "position_key", "parts": [ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE]}
BINARY = {"kind": "binary64", "parts": ["-0x0.0p+0"]}


def raw(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def table_bytes() -> bytes:
    declaration = TableIdentity("1" * 40, "2" * 40, PROTOCOL_SHA256, "3" * 64,
                                "4" * 64, "5" * 64, "run0", "recorder0")
    return build_table(declaration, ("owned-source-member",) * 14)


def intent(instance: int = 12, primitive: str = "log", scope: list[str] | None = None,
           arguments: dict[str, Any] | None = None, ordinal: int = 0) -> dict[str, Any]:
    return {"ordinal": ordinal, "call_id": f"c{ordinal:05d}", "instance_id": f"i{instance:02d}",
            "primitive": primitive, "scope": ["ct", "s0"] if scope is None else scope,
            "arguments": deepcopy(DECIMAL if arguments is None else arguments)}


def event(call: dict[str, Any], *, returned: dict[str, Any] | None = None,
          sequence: int = 0) -> dict[str, Any]:
    return {"sequence": sequence, "kind": "intent" if returned is None else "returned",
            "intent": call, "returned": returned, "fault": None}


def cursor(mode: str = "encode") -> codec.PrimitiveEventCodec:
    # Deliberate raw input also exercises the constructor's strict mode boundary.
    value: Any = mode
    return codec.PrimitiveEventCodec(table_bytes(), mode=value)


@pytest.mark.parametrize(("instance", "primitive", "scope", "argument", "descriptor", "code", "tag"), [
    pytest.param(0, "position", ["fx", "q12"], POSITION, [0, 12], 0, ["p", ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE], id="fixture"),
    pytest.param(1, "position", ["ep", "s", "p03", "n1023", "r0"], POSITION, [1, 0, 3, 1023, 0], 0, ["p", ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE], id="strong"),
    pytest.param(2, "position", ["ep", "w", "p39", "n1023", "r0"], POSITION, [1, 1, 39, 1023, 0], 0, ["p", ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE], id="weak"),
    pytest.param(3, "position", ["ep", "f", "e15", "n1023", "r0"], POSITION, [1, 2, 15, 1023, 0], 0, ["p", ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE], id="future"),
    pytest.param(9, "exp", ["ne", "p26", "n0255"], DECIMAL, [2, 26, 255], 1, ["d", "1", "12300", "-4"], id="reference-exp"),
    pytest.param(8, "log", ["nz", "p25"], DECIMAL, [3, 25], 2, ["d", "1", "12300", "-4"], id="normalization"),
    pytest.param(12, "circle_constant", ["ct", "pi"], {"kind": "none", "parts": []}, [4, 0], 3, ["n"], id="circle"),
    pytest.param(12, "log", ["ct", "g1"], DECIMAL, [4, 6], 2, ["d", "1", "12300", "-4"], id="constant-log"),
    pytest.param(13, "native_exp", ["nv", "p38", "n0255"], BINARY, [5, 38, 255], 4, ["b", "-0x0.0p+0"], id="native-emission"),
])
def test_independent_scope_vectors_roundtrip_exact_original_bytes(
    instance: int, primitive: str, scope: list[str], argument: dict[str, Any],
    descriptor: list[int], code: int, tag: list[str],
) -> None:
    call = intent(instance, primitive, scope, argument)
    expected_raw = [raw(event(call)), raw(event(call, returned=BINARY if code == 4 else DECIMAL, sequence=1))]
    expected_wire = [raw(["i", 0, 0, instance, code, descriptor, tag]),
                     raw(["r", 1, 0, ["b", "-0x0.0p+0"] if code == 4 else ["d", "1", "12300", "-4"]])]
    encoder, decoder = cursor(), cursor("expand")
    for original, compact in zip(expected_raw, expected_wire, strict=True):
        encoded, expanded = encoder.convert(original), decoder.convert(compact)
        assert encoded.status == expanded.status == "converted"
        assert encoded.raw_event == expanded.raw_event == original
        assert encoded.wire_event == expanded.wire_event == compact
        assert encoded.input_bytes == original and expanded.input_bytes == compact
        assert not encoded.retention_confirmed and not expanded.retention_confirmed
        assert encoded.material_authenticity == "unchecked"
        assert encoded.table_sha256 == expanded.table_sha256


@pytest.mark.parametrize("spelling", [
    ZERO, "-0x0.0p+0", "0x0.0000000000001p-1022", "-0x0.0000000000001p-1022",
    "0x0.fffffffffffffp-1022", "0x1.0000000000000p-1022", ONE,
    "0x1.fffffffffffffp+1023", "-0x1.fffffffffffffp+1023",
], ids=["zero", "negative-zero", "min-subnormal", "negative-subnormal", "max-subnormal", "min-normal", "one", "max-finite", "min-finite"])
def test_true_finite_binary64_hex_language_is_lossless(spelling: str) -> None:
    value = {"kind": "binary64", "parts": [spelling]}
    call = intent(13, "native_exp", ["nv", "p00", "n0000"], value)
    encoded = cursor().convert(raw(event(call)))
    assert encoded.status == "converted"
    assert encoded.wire_event == raw(["i", 0, 0, 13, 4, [5, 0, 0], ["b", spelling]])
    assert encoded.wire_event is not None
    expanded = cursor("expand").convert(encoded.wire_event)
    assert expanded.raw_event == raw(event(call))


@pytest.mark.parametrize("spelling", [
    "0x1p+0", "0X1.0000000000000p+0", "0x1.00000000000000p+0", "0x0.0000000000000p+0",
    "0x1.0000000000000p-0", "nan", "inf", "0x1.0000000000000p+1024",
    "0x1.0000000000000p-1023", "0x0.0000000000001p-1021", "0x0.0000000000000p-1022",
    "0x1.0000000000000p0", "0x2.0000000000000p+0", "+0x1.0000000000000p+0",
    "0x1.0000000000000p-01", " 0x0.0p+0", "0x1.000000000000Ap+0",
], ids=["short-fraction", "upper-prefix", "long-fraction", "padded-zero", "negative-zero-exponent", "nan", "infinity", "overflow", "normal-underflow", "subnormal-exponent", "zero-subnormal", "missing-plus", "leading-two", "leading-plus", "padded-exponent", "space", "upper-digit"])
def test_other_hex_spellings_never_normalize_into_success(spelling: str) -> None:
    line = raw(["i", 0, 0, 13, 4, [5, 0, 0], ["b", spelling]])
    result = cursor("expand").convert(line)
    assert result.status == "invalid"
    assert result.raw_event is None and not result.retention_confirmed


@pytest.mark.parametrize("parts", [
    ["0", "0", "0"], ["1", "0", "-256"], ["0", "12300", "-4"],
    ["1", "9" * 120, "128"], ["0", "1" * 120, "-256"],
], ids=["zero", "signed-zero-quantum", "trailing-coefficient-zero", "largest-coefficient", "small-exponent"])
def test_decimal_sign_quantum_and_digits_are_not_evaluated(parts: list[str]) -> None:
    call = intent(arguments={"kind": "decimal", "parts": parts})
    result = cursor().convert(raw(event(call)))
    assert result.status == "converted"
    assert result.wire_event == raw(["i", 0, 0, 12, 2, [4, 2], ["d", *parts]])


@pytest.mark.parametrize("parts", [
    ["0", "01", "0"], ["0", "", "0"], [True, "1", "0"], ["2", "1", "0"],
    ["0", "1", "-0"], ["0", "1", "+0"], ["0", "1", "01"], ["0", "1", "129"],
    ["0", "1", "-257"], ["0", "1" * 121, "0"], ["0", "١", "0"],
], ids=["leading-zero", "empty", "bool-sign", "sign-two", "negative-zero-exponent", "plus-exponent", "padded-exponent", "high-exponent", "low-exponent", "long-coefficient", "unicode-digit"])
def test_invalid_decimal_components_are_rejected_without_coercion(parts: list[object]) -> None:
    result = cursor("expand").convert(raw(["i", 0, 0, 12, 2, [4, 2], ["d", *parts]]))
    assert result.status == "invalid"


@pytest.mark.parametrize("change", ["instance", "primitive", "channel", "node", "query", "record", "context", "case", "scope-bool", "ordinal-bool", "extra"],
                         ids=["instance", "primitive", "channel", "node", "query", "record", "context", "case", "scope-bool", "ordinal-bool", "extra"])
def test_wire_scope_and_identity_substitutions_fail_closed(change: str) -> None:
    value: list[Any] = ["i", 0, 0, 1, 0, [1, 0, 0, 255, 0], ["p", ONE, ZERO, ZERO, ONE, ONE, ZERO, ONE]]
    if change == "instance":
        value[3] = 2
    elif change == "primitive":
        value[4] = 1
    elif change == "channel":
        value[5][1] = 1
    elif change == "node":
        value[5][3] = 256
    elif change == "query":
        value[3], value[5] = 0, [0, 13]
    elif change == "record":
        value[5][4] = 1
    elif change == "context":
        value[5][2] = 40
    elif change == "case":
        value[5][2] = 38
    elif change == "scope-bool":
        value[5][0] = True
    elif change == "ordinal-bool":
        value[2] = False
    else:
        value.append(None)
    result = cursor("expand").convert(raw(value))
    assert result.status == "invalid" and result.raw_event is None


def test_two_calls_use_one_intent_and_exact_contiguous_ordinals() -> None:
    enc, dec = cursor(), cursor("expand")
    for ordinal in range(2):
        call = intent(ordinal=ordinal)
        for original in (raw(event(call, sequence=2 * ordinal)),
                         raw(event(call, returned=DECIMAL, sequence=2 * ordinal + 1))):
            result = enc.convert(original)
            assert result.status == "converted" and result.wire_event is not None
            assert dec.convert(result.wire_event).raw_event == original


@pytest.mark.parametrize("change", ["without-intent", "second-intent", "repeat-sequence", "skip-ordinal", "call-id", "changed-argument", "changed-scope"],
                         ids=["without-intent", "second-intent", "repeat-sequence", "skip-ordinal", "call-id", "changed-argument", "changed-scope"])
def test_raw_ordering_and_complete_intent_identity_are_enforced(change: str) -> None:
    enc = cursor()
    call = intent()
    if change != "without-intent":
        assert enc.convert(raw(event(call))).status == "converted"
    altered = deepcopy(call)
    sequence = 1
    if change == "repeat-sequence":
        sequence = 0
    elif change == "skip-ordinal":
        altered["ordinal"], altered["call_id"] = 1, "c00001"
    elif change == "call-id":
        altered["call_id"] = "other0"
    elif change == "changed-argument":
        altered["arguments"]["parts"] = ["0", "1", "0"]
    elif change == "changed-scope":
        altered["scope"] = ["ct", "s1"]
    value = event(altered, returned=None if change == "second-intent" else DECIMAL, sequence=sequence)
    result = enc.convert(raw(value))
    assert result.status == "invalid"
    later = enc.convert(raw(event(call, returned=DECIMAL, sequence=1)))
    assert later.status == "stopped" and later.reason == result.reason


@pytest.mark.parametrize("kind", ["failed", "unavailable", "wire-fallback"], ids=["raw-failed", "raw-unavailable", "wire-object"])
def test_terminal_inputs_are_explicitly_unsupported_not_acknowledged(kind: str) -> None:
    obj = event(intent())
    machine = cursor("expand" if kind == "wire-fallback" else "encode")
    if kind == "failed":
        obj.update(kind="failed", fault={"ordinal": 0, "phase": "primitive", "exception_type": "builtins.ValueError", "exception_type_complete": True, "call_id": "c00000"})
    elif kind == "unavailable":
        assert machine.convert(raw(obj)).status == "converted"
        obj = event(intent(), returned={"kind": "unavailable", "parts": ["builtins.object"]}, sequence=1)
    original = raw(obj)
    result = machine.convert(original)
    assert result.status == "unsupported" and result.input_bytes == original
    assert result.raw_event is None and result.wire_event is None
    assert not result.retention_confirmed
    assert machine.convert(original).status == "stopped"


@pytest.mark.parametrize("change", ["space", "two-lf", "escape", "duplicate", "float", "bool", "extra", "short-parts"],
                         ids=["wire-space", "two-lf", "escaped-token", "duplicate-key", "float-sequence", "bool-sequence", "extra-key", "short-parts"])
def test_strict_canonical_raw_and_wire_inputs(change: str) -> None:
    call = intent()
    original = raw(event(call))
    mode = "encode"
    if change == "space":
        mode, original = "expand", b'["i", 0,0,12,2,[4,2],["d","1","12300","-4"]]\n'
    elif change == "two-lf":
        original += b"\n"
    elif change == "escape":
        original = original.replace(b'"log"', b'"\\u006cog"')
    elif change == "duplicate":
        original = original.replace(b'"sequence":0', b'"sequence":1,"sequence":0')
    elif change == "float":
        original = original.replace(b'"sequence":0', b'"sequence":0.0')
    elif change == "bool":
        original = original.replace(b'"sequence":0', b'"sequence":false')
    elif change == "extra":
        original = raw(event(call) | {"verified": True})
    else:
        call["arguments"]["parts"].pop()
        original = raw(event(call))
    result = cursor(mode).convert(original)
    assert result.status == "invalid" and not result.retention_confirmed


@pytest.mark.parametrize("kind", ["bytes", "depth"], ids=["oversized", "nested"])
def test_bounds_precede_json_decoding(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    machine = cursor()
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Invalid input reached JSON decoder")
    line = b"x" * 4097 if kind == "bytes" else b"[[[[[]]]]]\n"
    with monkeypatch.context() as scoped:
        scoped.setattr(codec.json, "loads", forbidden)
        result = machine.convert(line)
    assert result.status == "invalid"
    assert result.input_bytes == (None if kind == "bytes" else line)


@pytest.mark.parametrize("line", [b"", b"{", b'{"x":"truncated', b'{"x":NaN}\n', b'{"x":9999999}\n', b'{"x":"\xff"}\n'],
                         ids=["empty", "container", "string", "nan", "integer-length", "non-ascii"])
def test_malformed_bytes_stop_without_truncation(line: bytes) -> None:
    result = cursor().convert(line)
    assert result.status == "invalid" and result.input_bytes == line


@pytest.mark.parametrize("bad", [None, True, "{}", bytearray(b"{}")], ids=["none", "bool", "text", "mutable"])
def test_nonbytes_are_not_coerced(bad: Any) -> None:
    result = cursor().convert(bad)
    assert result.status == "invalid" and result.input_bytes is None


def test_closed_cursor_does_not_parse_again(monkeypatch: pytest.MonkeyPatch) -> None:
    machine = cursor()
    first = machine.convert(b"{")
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Stopped cursor parsed input")
    with monkeypatch.context() as scoped:
        scoped.setattr(codec.json, "loads", forbidden)
        result = machine.convert(raw(event(intent())))
    assert result.status == "stopped" and result.reason == first.reason


def test_table_and_direction_are_validated_before_cursor_creation() -> None:
    with pytest.raises(ValueError):
        codec.PrimitiveEventCodec(b"{}\n", mode="encode")
    with pytest.raises(ValueError):
        cursor("either")


def test_table_source_hash_changes_do_not_authenticate_event_material() -> None:
    declaration = json.loads(table_bytes())
    declaration["source_manifest_sha256"] = "a" * 64
    original = cursor().convert(raw(event(intent())))
    result = codec.PrimitiveEventCodec(raw(declaration), mode="encode").convert(raw(event(intent())))
    assert result.status == original.status == "converted"
    assert result.table_sha256 != original.table_sha256
    assert result.material_authenticity == "unchecked" and not result.retention_confirmed
