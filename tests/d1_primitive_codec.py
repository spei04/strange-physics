"""One-event, conversion-only D1 codec; no acknowledgement or primitive execution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal, NoReturn

from d1_primitive_codec_table import TableView, parse_table

EVENT_BYTES = 4096
MAX_CALLS = 55_100
MAX_EVENTS = 110_201
_HEX = re.compile(r"(-?)0x([01])\.([0-9a-f]{13})p([+-](?:0|[1-9][0-9]{0,3}))\Z")
_EXPONENT = re.compile(r"(?:0|-[1-9][0-9]{0,2}|[1-9][0-9]{0,2})\Z")
_DIGITS = re.compile(r"(?:0|[1-9][0-9]{0,119})\Z")
_EVENT_KEYS = frozenset(("sequence", "kind", "intent", "returned", "fault"))
_INTENT_KEYS = frozenset(("ordinal", "call_id", "instance_id", "primitive", "scope", "arguments"))
_VALUE_KEYS = frozenset(("kind", "parts"))


class _Invalid(ValueError):
    pass


class _Unsupported(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Conversion:
    status: Literal["converted", "unsupported", "invalid", "stopped"]
    input_bytes: bytes | None
    raw_event: bytes | None
    wire_event: bytes | None
    table_sha256: str
    reason: str | None

    @property
    def retention_confirmed(self) -> Literal[False]:
        return False

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"


def _int(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise _Invalid("strict_integer_domain")
    return value


def _str(value: object) -> str:
    if type(value) is not str:
        raise _Invalid("strict_string_required")
    return value


def _list(value: object, size: int | None = None) -> list[object]:
    if type(value) is not list or (size is not None and len(value) != size):
        raise _Invalid("exact_array_shape")
    return value


def _object(value: object, keys: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise _Invalid("exact_object_fields")
    return value


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _Invalid("duplicate_json_key")
        result[key] = value
    return result


def _number(text: str) -> int:
    if len(text.removeprefix("-")) > 6:
        raise _Invalid("integer_token_length")
    return int(text)


def _no_float(text: str) -> NoReturn:
    raise _Invalid("noninteger_json_number")


def _parse(raw: bytes, max_depth: int) -> object:
    if type(raw) is not bytes or not 1 <= len(raw) <= EVENT_BYTES:
        raise _Invalid("event_byte_bound")
    depth = 0
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > max_depth:
                raise _Invalid("event_depth_bound")
        elif byte in (93, 125):
            depth -= 1
            if depth < 0:
                raise _Invalid("unbalanced_json")
    if depth or quoted:
        raise _Invalid("truncated_json")
    try:
        value: object = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_int=_number,
            parse_float=_no_float,
            parse_constant=_no_float,
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        raise _Invalid("invalid_strict_json") from error
    if _canonical(value) != raw:
        raise _Invalid("noncanonical_json_bytes")
    return value


def _hex(value: object) -> str:
    text = _str(value)
    if text in ("0x0.0p+0", "-0x0.0p+0"):
        return text
    if len(text) > 24:
        raise _Invalid("binary64_spelling")
    match = _HEX.fullmatch(text)
    if match is None:
        raise _Invalid("binary64_spelling")
    leading, fraction, exponent_text = match.group(2, 3, 4)
    exponent = int(exponent_text)
    if exponent_text != ("+" + str(exponent) if exponent >= 0 else str(exponent)):
        raise _Invalid("binary64_exponent_spelling")
    if leading == "1":
        if not -1022 <= exponent <= 1023:
            raise _Invalid("binary64_normal_exponent")
    elif exponent != -1022 or fraction == "0" * 13:
        raise _Invalid("binary64_subnormal_spelling")
    return text


def _value(value: object, tag: str, *, wire: bool) -> tuple[dict[str, object], list[object]]:
    kinds = {"p": "position_key", "d": "decimal", "b": "binary64", "n": "none"}
    if wire:
        items = _list(value)
        if not items or items[0] != tag:
            raise _Invalid("value_tag")
        parts = items[1:]
    else:
        obj = _object(value, _VALUE_KEYS)
        if obj["kind"] == "unavailable":
            raise _Unsupported("unavailable_return_requires_adapter")
        if obj["kind"] != kinds[tag]:
            raise _Invalid("value_kind")
        parts = _list(obj["parts"])
    if tag == "p":
        _list(parts, 7)
        strings = [_hex(part) for part in parts]
    elif tag == "b":
        _list(parts, 1)
        strings = [_hex(parts[0])]
    elif tag == "n":
        _list(parts, 0)
        strings = []
    else:
        _list(parts, 3)
        strings = [_str(part) for part in parts]
        sign, digits, exponent = strings
        if sign not in ("0", "1") or _DIGITS.fullmatch(digits) is None:
            raise _Invalid("decimal_coefficient_spelling")
        if _EXPONENT.fullmatch(exponent) is None or not -256 <= int(exponent) <= 128:
            raise _Invalid("decimal_exponent_spelling")
    return {"kind": kinds[tag], "parts": strings}, [tag, *strings]


def _token_index(value: object, prefix: str, digits: int) -> int:
    text = _str(value)
    if re.fullmatch(prefix + "[0-9]{" + str(digits) + "}", text) is None:
        raise _Invalid("fixed_token_spelling")
    return int(text[1:])


def _scope_from_wire(table: TableView, value: object, instance: int, primitive: int) -> list[str]:
    desc = _list(value)
    if not desc:
        raise _Invalid("empty_scope")
    family = _int(desc[0], 0, 5)
    if family == 0:
        _list(desc, 2)
        query = _int(desc[1], 0, 12)
        expected_instance, expected_primitive = 0, 0
        scope = ["fx", f"q{query:02d}"]
    elif family == 1:
        _list(desc, 5)
        channel = _int(desc[1], 0, 2)
        context = _int(desc[2], 0, 15 if channel == 2 else 39)
        row = table.rows[(54 if channel == 2 else 14) + context]
        case, grid = _int(row[2], 0, 7), _int(row[3], 0, 1)
        if (channel == 0 and case == 7) or (channel == 1 and case != 7):
            raise _Invalid("endpoint_channel_case_join")
        node = _int(desc[3], 0, (256 if grid == 0 else 1024) - 1)
        _int(desc[4], 0, 0)
        expected_instance, expected_primitive = 1 + channel, 0
        scope = [
            "ep",
            ("s", "w", "f")[channel],
            f"{'e' if channel == 2 else 'p'}{context:02d}",
            f"n{node:04d}",
            "r0",
        ]
    elif family in (2, 3, 5):
        _list(desc, 2 if family == 3 else 3)
        profile = _int(desc[1], 0, 39)
        row = table.rows[14 + profile]
        case, grid = _int(row[2], 0, 7), _int(row[3], 0, 1)
        if family == 3:
            scope = ["nz", f"p{profile:02d}"]
            expected_instance, expected_primitive = 4 + case, 2
        else:
            node = _int(desc[2], 0, (256 if grid == 0 else 1024) - 1)
            scope = ["ne" if family == 2 else "nv", f"p{profile:02d}", f"n{node:04d}"]
            expected_instance, expected_primitive = (4 + case, 1) if family == 2 else (13, 4)
    else:
        _list(desc, 2)
        constant = _int(desc[1], 0, 6)
        row = table.rows[83 + constant]
        scope = ["ct", _str(row[2])]
        expected_instance, expected_primitive = 12, _int(row[3], 0, 4)
    if (instance, primitive) != (expected_instance, expected_primitive):
        raise _Invalid("scope_instance_primitive_join")
    return scope


def _scope_to_wire(table: TableView, value: object, instance: int, primitive: int) -> list[int]:
    items = [_str(item) for item in _list(value)]
    if not items:
        raise _Invalid("empty_scope")
    family = items[0]
    if family == "fx" and len(items) == 2:
        desc = [0, _token_index(items[1], "q", 2)]
    elif family == "ep" and len(items) == 5:
        if items[1] not in ("s", "w", "f") or items[4] != "r0":
            raise _Invalid("endpoint_scope_tokens")
        channel = ("s", "w", "f").index(items[1])
        desc = [
            1,
            channel,
            _token_index(items[2], "e" if channel == 2 else "p", 2),
            _token_index(items[3], "n", 4),
            0,
        ]
    elif family in ("ne", "nv") and len(items) == 3:
        desc = [
            2 if family == "ne" else 5,
            _token_index(items[1], "p", 2),
            _token_index(items[2], "n", 4),
        ]
    elif family == "nz" and len(items) == 2:
        desc = [3, _token_index(items[1], "p", 2)]
    elif family == "ct" and len(items) == 2:
        tokens = [_str(row[2]) for row in table.rows[83:90]]
        if items[1] not in tokens:
            raise _Invalid("constant_token")
        desc = [4, tokens.index(items[1])]
    else:
        raise _Invalid("fixed_scope_form")
    if _scope_from_wire(table, desc, instance, primitive) != items:
        raise _Invalid("scope_roundtrip")
    return desc


class PrimitiveEventCodec:
    """A single-direction cursor: successful conversion is never sink success.

    Any invalid/unsupported input consumes this cursor. Deliberate private-state
    mutation or concurrent use is outside this single-owner pure helper boundary.
    """

    def __init__(self, table_bytes: bytes, *, mode: Literal["encode", "expand"]) -> None:
        if type(mode) is not str or mode not in ("encode", "expand"):
            raise ValueError("Fixed codec direction required")
        self._table = parse_table(table_bytes)
        self._mode = mode
        self._sequence = self._ordinal = 0
        self._current: dict[str, object] | None = None
        self._stopped = False
        self._first_failure: str | None = None

    def _intent(self, value: object) -> tuple[dict[str, object], list[object]]:
        obj = _object(value, _INTENT_KEYS)
        ordinal = _int(obj["ordinal"], 0, MAX_CALLS - 1)
        if ordinal != self._ordinal or obj["call_id"] != f"c{ordinal:05d}":
            raise _Invalid("call_identity_order")
        instance = _token_index(obj["instance_id"], "i", 2)
        _int(instance, 0, 13)
        names = [_str(row[2]) for row in self._table.rows[90:95]]
        primitive_name = _str(obj["primitive"])
        if primitive_name not in names:
            raise _Invalid("primitive_name")
        primitive = names.index(primitive_name)
        desc = _scope_to_wire(self._table, obj["scope"], instance, primitive)
        argument, compact = _value(
            obj["arguments"], ("p", "d", "d", "n", "b")[primitive], wire=False
        )
        checked: dict[str, object] = {
            "ordinal": ordinal,
            "call_id": f"c{ordinal:05d}",
            "instance_id": f"i{instance:02d}",
            "primitive": primitive_name,
            "scope": _scope_from_wire(self._table, desc, instance, primitive),
            "arguments": argument,
        }
        return checked, ["i", self._sequence, ordinal, instance, primitive, desc, compact]

    def _raw_to_wire(self, value: object) -> tuple[dict[str, object], list[object]]:
        event = _object(value, _EVENT_KEYS)
        sequence = _int(event["sequence"], 0, MAX_EVENTS - 1)
        if sequence != self._sequence:
            raise _Invalid("event_sequence_order")
        if event["kind"] == "failed":
            raise _Unsupported("raw_terminal_requires_adapter_validation")
        if event["fault"] is not None:
            raise _Invalid("successful_event_has_fault")
        intent, compact = self._intent(event["intent"])
        if event["kind"] == "intent":
            if self._current is not None or event["returned"] is not None:
                raise _Invalid("one_current_intent")
        elif event["kind"] == "returned":
            if self._current is None or intent != self._current:
                raise _Invalid("return_intent_substitution")
            tag = "b" if intent["primitive"] == "native_exp" else "d"
            _, returned = _value(event["returned"], tag, wire=False)
            compact = ["r", sequence, self._ordinal, returned]
        else:
            raise _Invalid("event_kind")
        return event, compact

    def _wire_to_raw(self, value: object) -> dict[str, object]:
        if type(value) is dict:
            raise _Unsupported("raw_fallback_requires_adapter_validation")
        items = _list(value)
        if not items or items[0] not in ("i", "r"):
            raise _Invalid("wire_mode")
        _list(items, 7 if items[0] == "i" else 4)
        if _int(items[1], 0, MAX_EVENTS - 1) != self._sequence:
            raise _Invalid("event_sequence_order")
        ordinal = _int(items[2], 0, MAX_CALLS - 1)
        if ordinal != self._ordinal:
            raise _Invalid("call_identity_order")
        returned: dict[str, object] | None
        if items[0] == "i":
            if self._current is not None:
                raise _Invalid("one_current_intent")
            instance, primitive = _int(items[3], 0, 13), _int(items[4], 0, 4)
            scope = _scope_from_wire(self._table, items[5], instance, primitive)
            argument, _ = _value(items[6], ("p", "d", "d", "n", "b")[primitive], wire=True)
            intent: dict[str, object] = {
                "ordinal": ordinal,
                "call_id": f"c{ordinal:05d}",
                "instance_id": f"i{instance:02d}",
                "primitive": self._table.rows[90 + primitive][2],
                "scope": scope,
                "arguments": argument,
            }
            returned = None
        else:
            if self._current is None:
                raise _Invalid("return_without_intent")
            intent = self._current
            returned, _ = _value(
                items[3], "b" if intent["primitive"] == "native_exp" else "d", wire=True
            )
        return {
            "sequence": self._sequence,
            "kind": "intent" if items[0] == "i" else "returned",
            "intent": intent,
            "returned": returned,
            "fault": None,
        }

    def convert(self, line: bytes) -> Conversion:
        original = line if type(line) is bytes and len(line) <= EVENT_BYTES else None
        if self._stopped:
            return Conversion(
                "stopped", original, None, None, self._table.sha256, self._first_failure
            )
        # A parser/internal exception cannot leave a reusable cursor by accident.
        self._stopped = True
        self._first_failure = "internal_conversion_error"
        try:
            depth = (
                2 if self._mode == "expand" and type(line) is bytes and line.startswith(b"[") else 4
            )
            value = _parse(line, depth)
            if self._mode == "encode":
                event, compact = self._raw_to_wire(value)
                wire = _canonical(compact)
                rebuilt = self._wire_to_raw(_parse(wire, 2))
                raw = _canonical(rebuilt)
                if raw != line:
                    raise _Invalid("raw_byte_equivalence")
            else:
                event = self._wire_to_raw(value)
                raw = _canonical(event)
                _, compact = self._raw_to_wire(_parse(raw, 4))
                wire = _canonical(compact)
                if wire != line:
                    raise _Invalid("wire_byte_equivalence")
            if len(raw) > EVENT_BYTES or len(wire) > EVENT_BYTES:
                raise _Invalid("expanded_event_byte_bound")
            if event["kind"] == "intent":
                self._current = _object(event["intent"], _INTENT_KEYS)
            else:
                self._current = None
                self._ordinal += 1
            self._sequence += 1
            self._first_failure = None
            self._stopped = False
            return Conversion("converted", original, raw, wire, self._table.sha256, None)
        except _Unsupported as error:
            self._first_failure = str(error)
            return Conversion("unsupported", original, None, None, self._table.sha256, str(error))
        except _Invalid as error:
            self._first_failure = str(error)
            return Conversion("invalid", original, None, None, self._table.sha256, str(error))
