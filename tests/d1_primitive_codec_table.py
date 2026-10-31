"""Pure D1 identity-table bytes; declarations, never source authentication.

Only build_table/parse_table are validation boundaries. Views are immutable in
ordinary use; a caller-created or forcibly mutated view is not verification.
No source resolver, primitive, event codec, activation or filesystem work occurs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from typing import Literal, NoReturn

SCHEMA = "strange-physics.d1-primitive-codec.v1"
PROTOCOL_SHA256 = "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"
MAX_CALLS = 55_100
TABLE_ROWS = 105
TABLE_BYTES = 57_856
HEADER_BYTES = 4_096
ROW_WITH_SEPARATOR_BYTES = 512
CASE_ORDER = ("M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z")
_BINDING = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,31}\Z")
Atom = str | int | None
Row = tuple[Atom, ...]


@dataclass(frozen=True, slots=True)
class TableIdentity:
    source_commit: str
    source_tree: str
    protocol_sha256: str
    source_manifest_sha256: str
    recorder_sha256: str
    codec_sha256: str
    run_id: str
    recorder_id: str


_ID_FIELDS = tuple(field.name for field in fields(TableIdentity))
_ROOT_KEYS = frozenset((*_ID_FIELDS, "schema", "max_calls", "case_order", "rows"))


@dataclass(frozen=True, slots=True)
class TableView:
    raw: bytes
    sha256: str
    identity: TableIdentity
    source_binding_refs: tuple[str, ...]
    rows: tuple[Row, ...]

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"


def _identity(values: dict[str, object]) -> TableIdentity:
    texts: dict[str, str] = {}
    for name in _ID_FIELDS:
        value = values.get(name)
        if type(value) is not str:
            raise ValueError("Exact string identity fields required")
        if name in ("run_id", "recorder_id"):
            if _TOKEN.fullmatch(value) is None:
                raise ValueError("Bounded opaque sink identity required")
        else:
            size = 40 if name in ("source_commit", "source_tree") else 64
            if re.fullmatch("[0-9a-f]{" + str(size) + "}", value) is None:
                raise ValueError("Exact lowercase hexadecimal identity required")
        texts[name] = value
    if texts["protocol_sha256"] != PROTOCOL_SHA256:
        raise ValueError("This table version requires the frozen D1 protocol")
    return TableIdentity(**texts)


def _bindings(values: object) -> tuple[str, ...]:
    if type(values) is not tuple or len(values) != 14:
        raise ValueError("Fourteen ordered instance source references required")
    result: list[str] = []
    for value in values:
        if type(value) is not str or _BINDING.fullmatch(value) is None:
            raise ValueError("Bounded opaque source-manifest member required")
        result.append(value)
    # Several owned instances may use one source member; this is not a resolver.
    return tuple(result)


def _rows(bindings: tuple[str, ...]) -> tuple[Row, ...]:
    rows: list[Row] = []
    roles = (
        "fixture",
        "strong",
        "weak",
        "future",
        *("arithmetic",) * 8,
        "constants",
        "native_emit",
    )
    for j, role in enumerate(roles):
        rows.append(("I", j, f"i{j:02d}", role, j - 4 if 4 <= j <= 11 else None, bindings[j]))
    profile = 0
    for case in range(8):
        for grid in range(2):
            for scale in (1,) if case in (4, 7) else (0, 1, 2):
                rows.append(("P", profile, case, grid, scale, 2 if case == 4 else 1))
                profile += 1
    for ensemble in range(16):
        rows.append(("E", ensemble, ensemble // 2, ensemble % 2))
    queries = (
        ("train-M01", 1, "a0", "x0", "t0"),
        ("future-M01", 1, "a0", "x0", "t1"),
        ("train-M02", 5, "a0", "x0", "t0"),
        ("future-M02", 5, "a0", "x0", "t1"),
        ("train-M03", 13, "a0", "x0", "t0"),
        ("future-M03", 13, "a0", "x0", "t1"),
        ("train-M04", 27, "a0", "x0", "t0"),
        ("future-M04", 27, "a0", "x0", "t1"),
        ("train-F02", 5, "a1", "x0", "t0"),
        ("future-F02", 5, "a1", "x0", "t1"),
        ("train-F04", 27, "a1", "x0", "t0"),
        ("future-F04", 27, "a1", "x0", "t1"),
        ("train-W03", 13, "a0", "x1", "t0"),
    )
    rows.extend(("Q", q, *query) for q, query in enumerate(queries))
    rows.extend(
        ("C", c, token, 3 if c == 0 else 2)
        for c, token in enumerate(("pi", "l2p", "s0", "s1", "s2", "g0", "g1"))
    )
    rows.extend(
        ("V", v, name)
        for v, name in enumerate(("position", "exp", "log", "circle_constant", "native_exp"))
    )
    rows.extend(("S", s, token) for s, token in enumerate(("fx", "ep", "ne", "nz", "ct", "nv")))
    rows.extend(
        ("T", t, token, kind)
        for t, (token, kind) in enumerate(
            (("p", "position_key"), ("d", "decimal"), ("b", "binary64"), ("n", "none"))
        )
    )
    return tuple(rows)


def _encode(value: object, *, newline: bool = True) -> bytes:
    text = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return (text + ("\n" if newline else "")).encode("ascii")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _integer(text: str) -> int:
    if len(text.removeprefix("-")) > 5:
        raise ValueError("Integer token exceeds the fixed table domain")
    return int(text)


def _reject_number(text: str) -> NoReturn:
    raise ValueError("Only strict integer JSON numbers are admitted")


def _depth(raw: bytes) -> None:
    """Reject nesting beyond root/rows/row before the JSON decoder allocates it."""
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
            if depth > 3:
                raise ValueError("Table nesting exceeds three containers")
        elif byte in (93, 125):
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced JSON containers")
    if depth or quoted:
        raise ValueError("Truncated JSON container or string")


def parse_table(raw: bytes) -> TableView:
    """Validate complete canonical bytes, not source truth or an existing view."""
    if type(raw) is not bytes or not 1 <= len(raw) <= TABLE_BYTES:
        raise ValueError("Complete bounded immutable table bytes required")
    _depth(raw)
    try:
        document: object = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_unique_pairs,
            parse_int=_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Invalid strict table JSON") from error
    if type(document) is not dict or set(document) != _ROOT_KEYS:
        raise ValueError("Exact table root fields required")
    if (
        document["schema"] != SCHEMA
        or type(document["max_calls"]) is not int
        or document["max_calls"] != MAX_CALLS
    ):
        raise ValueError("Fixed table schema and call plan required")
    if type(document["case_order"]) is not list or document["case_order"] != list(CASE_ORDER):
        raise ValueError("Exact frozen case order required")
    identity = _identity(document)
    given = document["rows"]
    if type(given) is not list or len(given) != TABLE_ROWS:
        raise ValueError("Exactly 105 complete ordered rows required")
    rows: list[Row] = []
    for row in given:
        if type(row) is not list or not 3 <= len(row) <= 7:
            raise ValueError("Closed flat row forms required")
        atoms: list[Atom] = []
        for atom in row:
            if type(atom) not in (str, int, type(None)):
                raise ValueError("Row atoms cannot be coerced or nested")
            atoms.append(atom)
        if len(_encode(row, newline=False)) + 1 > ROW_WITH_SEPARATOR_BYTES:
            raise ValueError("Canonical row plus separator exceeds 512 bytes")
        rows.append(tuple(atoms))
    if any(len(row) != 6 for row in rows[:14]):
        raise ValueError("Complete instance rows required before source joins")
    bindings = _bindings(tuple(row[5] for row in rows[:14]))
    if tuple(rows) != _rows(bindings):
        raise ValueError("Fixed row identity, order, role or profile/query join changed")
    header = dict(document)
    header["rows"] = []
    if len(_encode(header)) > HEADER_BYTES:
        raise ValueError("Canonical empty-row header exceeds 4096 bytes")
    if _encode(document) != raw:
        raise ValueError("Exact canonical compact ASCII bytes and one LF required")
    return TableView(raw, hashlib.sha256(raw).hexdigest(), identity, bindings, tuple(rows))


def build_table(identity: TableIdentity, source_binding_refs: tuple[str, ...]) -> bytes:
    """Construct only fixed rows; validate raw Python fields before serialization."""
    if type(identity) is not TableIdentity:
        raise ValueError("Exact TableIdentity declaration required")
    try:
        values = {name: getattr(identity, name) for name in _ID_FIELDS}
    except AttributeError as error:
        raise ValueError("Complete TableIdentity declaration required") from error
    checked = _identity(values)
    bindings = _bindings(source_binding_refs)
    document: dict[str, object] = {name: getattr(checked, name) for name in _ID_FIELDS}
    document.update(schema=SCHEMA, max_calls=MAX_CALLS, case_order=CASE_ORDER, rows=_rows(bindings))
    # Parsing the actual encoded bytes makes this the same boundary as receipt input.
    return parse_table(_encode(document)).raw
