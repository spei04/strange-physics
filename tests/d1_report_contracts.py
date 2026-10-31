"""D1 report structure only; no payload binder, numerical gate or file resolver."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, ConfigDict, Field, ValidationError, model_validator

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.calibration_fixture_contracts import PROTOCOL_SHA256
from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation

Kind = Literal[
    "fixture",
    "belief",
    "prior",
    "prequential",
    "refinement",
    "scale",
    "stress",
    "primary",
    "aggregate",
]
State = Literal["unrun", "attempted", "completed", "failed"]
KINDS: tuple[Kind, ...] = (
    "fixture",
    "belief",
    "prior",
    "prequential",
    "refinement",
    "scale",
    "stress",
    "primary",
    "aggregate",
)
CASES = ("M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03")
COUNTS = (256, 1024)
SCALES = ("0.125", "0.25", "0.5")
GROUP_COUNTS = (8, 40, 16, 18, 20, 12, 16, 4, 1)
REPORT_BYTES = 4 * 1024**2
TABLE_BYTES = 4 * 1024**2
DECLARED_SCIENCE_BYTES = 64 * 1024**2
Hash = Annotated[str, Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
Commit = Annotated[str, Field(min_length=40, max_length=40, pattern=r"^[0-9a-f]{40}$")]
Key = Annotated[str, Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9/:._-]+$")]
Reason = Annotated[str, Field(min_length=1, max_length=256)]


@dataclass(frozen=True)
class RowSpec:
    key: str
    kind: Kind
    dependencies: tuple[str, ...]


def _scales(case: str) -> tuple[str, ...]:
    return ("0.25",) if case in ("D03", "W03") else SCALES


def fixed_row_manifest() -> tuple[RowSpec, ...]:
    """Fixed result order; dependency edges are not an execution chronology proof."""
    rows: list[RowSpec] = [RowSpec(f"fixture/{c}", "fixture", ()) for c in CASES]
    for c in CASES:
        for n in COUNTS:
            for scale in _scales(c):
                deps: tuple[str, ...] = (
                    f"fixture/{c}",
                    f"prior/{c}/{n}",
                    f"prequential/{c}/{n}/record0",
                )
                if c == "D03":
                    deps += (f"prequential/D03/{n}/record1",)
                rows.append(RowSpec(f"belief/{c}/{n}/{scale}", "belief", deps))
    rows.extend(
        RowSpec(f"prior/{c}/{n}", "prior", (f"fixture/{c}",)) for c in CASES for n in COUNTS
    )
    rows.extend(
        RowSpec(f"prequential/{c}/{n}/record0", "prequential", (f"fixture/{c}",))
        for c in CASES
        for n in COUNTS
    )
    rows.extend(
        RowSpec(
            f"prequential/D03/{n}/record1",
            "prequential",
            ("fixture/D03", "fixture/M03", f"belief/M03/{n}/0.25"),
        )
        for n in COUNTS
    )
    rows.extend(
        RowSpec(
            f"refinement/{c}/{scale}/256-to-1024",
            "refinement",
            (f"belief/{c}/256/{scale}", f"belief/{c}/1024/{scale}"),
        )
        for c in CASES
        for scale in _scales(c)
    )
    rows.extend(
        RowSpec(
            f"scale/{c}/1024/{left}-to-{right}",
            "scale",
            (f"belief/{c}/1024/{left}", f"belief/{c}/1024/{right}"),
        )
        for c in ("M01", "M02", "M03", "M04", "F02", "F04")
        for left, right in (("0.125", "0.25"), ("0.25", "0.5"))
    )
    rows.extend(
        RowSpec(
            f"stress/D03:M03/{n}/0.25",
            "stress",
            (f"belief/D03/{n}/0.25", f"belief/M03/{n}/0.25", f"prequential/D03/{n}/record1"),
        )
        for n in COUNTS
    )
    rows.extend(
        RowSpec(
            f"stress/{force}:{matched}/{n}/{scale}",
            "stress",
            (f"belief/{force}/{n}/{scale}", f"belief/{matched}/{n}/{scale}"),
        )
        for force, matched in (("F02", "M02"), ("F04", "M04"))
        for n in COUNTS
        for scale in SCALES
    )
    rows.extend(
        RowSpec(
            f"stress/W03:M03/{n}/0.25", "stress", (f"belief/W03/{n}/0.25", f"belief/M03/{n}/0.25")
        )
        for n in COUNTS
    )
    rows.extend(
        RowSpec(f"primary/{c}/1024/0.25", "primary", (f"belief/{c}/1024/0.25", f"prior/{c}/1024"))
        for c in ("M01", "M02", "M03", "M04")
    )
    rows.append(
        RowSpec("aggregate/matched/base/continuous-dk", "aggregate", tuple(row.key for row in rows))
    )
    return tuple(rows)


ROW_MANIFEST = fixed_row_manifest()


class _ReportMessage(Message):
    """Revalidate actual local DTO instances before serialization."""

    model_config = ConfigDict(revalidate_instances="always")


class DecimalAtom(_ReportMessage):
    """Lossless bounded Decimal tuple, including quantum and signed zero."""

    sign: Annotated[int, Field(ge=0, le=1)]
    digits: Annotated[str, Field(min_length=1, max_length=120, pattern=r"^(0|[1-9][0-9]*)$")]
    exponent: Annotated[int, Field(ge=-256, le=128)]

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if re.fullmatch(r"0|[1-9][0-9]*", self.digits) is None:
            raise ValueError("Exact Decimal coefficient digits required")
        if self.value().copy_abs() > Decimal("1e128"):
            raise ValueError("Decimal magnitude exceeds the existing interval domain")
        return self

    def value(self) -> Decimal:
        return Decimal((self.sign, tuple(int(x) for x in self.digits), self.exponent))


def encode_decimal(value: Decimal) -> DecimalAtom:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Finite exact Decimal required")
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int) or len(digits) > 120:
        raise ValueError("Finite bounded Decimal coefficient/exponent required")
    return DecimalAtom(sign=sign, digits="".join(map(str, digits)), exponent=exponent)


def decode_decimal(value: DecimalAtom) -> Decimal:
    if type(value) is not DecimalAtom:
        raise ValueError("Exact DecimalAtom required")
    return DecimalAtom.model_validate(vars(value)).value()


def _hex(value: str) -> str:
    try:
        number = float.fromhex(value)
    except (ValueError, OverflowError):
        raise ValueError("Canonical finite binary64 hex required") from None
    if not math.isfinite(number) or number.hex() != value:
        raise ValueError("Canonical finite binary64 hex required")
    return value


Binary64 = Annotated[str, Field(min_length=1, max_length=32), AfterValidator(_hex)]


class Binary64Atom(_ReportMessage):
    value: Binary64


def encode_binary64(value: float) -> Binary64Atom:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("Finite exact binary64 required")
    return Binary64Atom(value=value.hex())


def decode_binary64(value: Binary64Atom) -> float:
    if type(value) is not Binary64Atom:
        raise ValueError("Exact Binary64Atom required")
    return float.fromhex(Binary64Atom.model_validate(vars(value)).value)


class IntervalAtom(_ReportMessage):
    lower: DecimalAtom
    upper: DecimalAtom

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.lower.value() > self.upper.value():
            raise ValueError("Ordered interval endpoints required")
        return self


class TableRef(_ReportMessage):
    table_id: Identifier
    kind: Kind | Literal["fault"]
    path: Annotated[str, Field(min_length=1, max_length=192)]
    codec: Identifier
    byte_length: Annotated[int, Field(ge=1, le=TABLE_BYTES)]
    raw_sha256: Hash
    canonical_sha256: Hash | None = None
    record_count: Annotated[int, Field(ge=1, le=37_120)]

    @model_validator(mode="after")
    def exact_descriptor(self) -> Self:
        parts = self.path.split("/")
        if (
            len(parts) < 2
            or parts[0] != self.kind
            or any(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", x) is None for x in parts)
            or any(x in (".", "..") for x in parts)
            or not self.path.endswith((".json", ".jsonl"))
        ):
            raise ValueError("Normalized relative path in the declared role required")
        if self.codec != self.kind + "-v1":
            raise ValueError("Exact proposed row-table codec tag required")
        if self.raw_sha256 == "0" * 64 or self.canonical_sha256 == "0" * 64:
            raise ValueError("Unavailable evidence cannot use a zero digest")
        return self


class TableSlot(_ReportMessage):
    table_id: Identifier
    index: Annotated[int, Field(ge=0, lt=37_120)]


class RowState(_ReportMessage):
    ordinal: Annotated[int, Field(ge=0, lt=135)]
    key: Annotated[str, Field(min_length=1, max_length=96)]
    kind: Kind
    state: State
    dependencies: Annotated[tuple[Key, ...], Field(max_length=134)]
    completion: TableSlot | None = None
    partial: Annotated[tuple[TableSlot, ...], Field(max_length=8)] = ()
    fault: TableSlot | None = None
    reason: Reason | None = None

    @model_validator(mode="after")
    def exact_state(self) -> Self:
        spec = ROW_MANIFEST[self.ordinal]
        if (self.key, self.kind, self.dependencies) != (spec.key, spec.kind, spec.dependencies):
            raise ValueError("Exact row identity, kind and dependency order required")
        if len(set((x.table_id, x.index) for x in self.partial)) != len(self.partial):
            raise ValueError("Partial material slots must be unique")
        if self.state == "completed":
            if (
                self.completion is None
                or self.partial
                or self.fault is not None
                or self.reason is not None
            ):
                raise ValueError("Completed row requires only its completion material")
        else:
            if self.completion is not None or self.reason is None or not self.reason.strip():
                raise ValueError("Unfinished row needs an explicit reason and no completed result")
            if self.state == "failed" and self.fault is None:
                raise ValueError("Failed row requires retained fault identity")
            if self.state != "failed" and self.fault is not None:
                raise ValueError("Only a failed row claims its own terminal fault")
            if self.state == "unrun" and self.partial:
                raise ValueError("Unrun row cannot have returned material")
        return self


class Denominator(_ReportMessage):
    kind: Kind
    planned: Annotated[int, Field(ge=1, le=135)]
    unrun: Annotated[int, Field(ge=0, le=135)]
    attempted: Annotated[int, Field(ge=0, le=135)]
    completed: Annotated[int, Field(ge=0, le=135)]
    failed: Annotated[int, Field(ge=0, le=135)]


def group_denominators(rows: tuple[RowState, ...]) -> tuple[Denominator, ...]:
    return tuple(
        Denominator(
            kind=kind,
            planned=planned,
            unrun=sum(r.kind == kind and r.state == "unrun" for r in rows),
            attempted=sum(r.kind == kind and r.state == "attempted" for r in rows),
            completed=sum(r.kind == kind and r.state == "completed" for r in rows),
            failed=sum(r.kind == kind and r.state == "failed" for r in rows),
        )
        for kind, planned in zip(KINDS, GROUP_COUNTS, strict=True)
    )


class D1ReportStructure(_ReportMessage):
    schema_version: Literal["strange-physics.d1-report-structure.v1"] = (
        "strange-physics.d1-report-structure.v1"
    )
    validation_scope: Literal["structure-only"] = "structure-only"
    material_authenticity: Literal["unchecked"] = "unchecked"
    qualification: Literal["unavailable"] = "unavailable"
    utility: Literal["unavailable"] = "unavailable"
    protocol_sha256: Hash
    source_commit: Commit
    source_tree: Commit
    run_id: Identifier
    declared_execution: Literal["complete", "incomplete"]
    incomplete_reason: Reason | None = None
    rows: Annotated[tuple[RowState, ...], Field(min_length=135, max_length=135)]
    denominators: Annotated[tuple[Denominator, ...], Field(min_length=9, max_length=9)]
    tables: Annotated[tuple[TableRef, ...], Field(max_length=512)]
    first_fault: TableSlot | None = None

    @model_validator(mode="after")
    def fixed_structure(self) -> Self:
        if self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("Frozen D1 protocol identity required")
        if self.source_commit == "0" * 40 or self.source_tree == "0" * 40:
            raise ValueError("Unavailable source identity cannot be fabricated")
        if tuple(r.ordinal for r in self.rows) != tuple(range(135)):
            raise ValueError("All135 ordered rows are required, including unrun rows")
        if self.denominators != group_denominators(self.rows):
            raise ValueError("Exact all-row state denominators required")
        tables = {t.table_id: t for t in self.tables}
        if len(tables) != len(self.tables) or len({t.path for t in self.tables}) != len(
            self.tables
        ):
            raise ValueError("Table IDs and normalized paths must be unique")
        if sum(t.byte_length for t in self.tables) > DECLARED_SCIENCE_BYTES:
            raise ValueError("Declared table bytes exceed the unchanged science ceiling")
        used: set[str] = set()
        completed_slots: set[tuple[str, int]] = set()

        def join(slot: TableSlot, kind: str) -> None:
            table = tables.get(slot.table_id)
            if table is None or table.kind != kind or slot.index >= table.record_count:
                raise ValueError("Table slot must join its exact role and record range")
            used.add(table.table_id)

        states = {r.key: r.state for r in self.rows}
        for row in self.rows:
            if row.completion is not None:
                join(row.completion, row.kind)
                slot = (row.completion.table_id, row.completion.index)
                if slot in completed_slots:
                    raise ValueError("Top-level completed rows cannot alias one payload slot")
                completed_slots.add(slot)
            for partial in row.partial:
                join(partial, row.kind)
            if row.fault is not None:
                join(row.fault, "fault")
            if row.state == "completed" and any(states[k] != "completed" for k in row.dependencies):
                raise ValueError("A completed row cannot hide an unfinished dependency")
        if self.first_fault is not None:
            join(self.first_fault, "fault")
        if any(r.state == "failed" for r in self.rows) and self.first_fault is None:
            raise ValueError("Failed rows require a retained first fault")
        if used != set(tables):
            raise ValueError("Unreferenced table descriptors are outside this structure envelope")
        if self.declared_execution == "complete":
            if (
                any(r.state != "completed" for r in self.rows)
                or self.first_fault is not None
                or self.incomplete_reason is not None
            ):
                raise ValueError("Complete declaration requires all rows and no control fault")
        elif self.incomplete_reason is None or not self.incomplete_reason.strip():
            raise ValueError("Incomplete declaration requires its explicit reason")
        return self


def parse_report_structure(raw: bytes) -> D1ReportStructure:
    return parse_bounded_json(
        raw, D1ReportStructure, max_bytes=REPORT_BYTES, max_depth=16, max_nodes=100_000
    )


def validate_report_structure(value: D1ReportStructure) -> D1ReportStructure:
    """Revalidate actual nested types before serialization can normalize them."""
    if type(value) is not D1ReportStructure:
        raise ValueError("Exact structural report required")
    try:
        normalized = D1ReportStructure.model_validate(value)
    except ValidationError:
        raise ContractViolation("invalid_request", 422) from None
    bounded_canonical(normalized, REPORT_BYTES)
    return parse_report_structure(normalized.model_dump_json().encode())
