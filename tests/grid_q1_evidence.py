"""Bounded persisted evidence and directed arithmetic for the disabled GRID-Q1 driver."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Mapping
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Self

from grid_q1_bounds import Interval
from pydantic import AfterValidator, Field, model_validator

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.research_contracts import Digest

D = Decimal
PRECISION = 100
REFERENCE_LOG_ERROR = D("1e-48")
REFERENCE_ENDPOINT_ERROR = D("1e-60")
REPORT_LIMIT = 512 * 1024
OUTPUT_LIMIT = 64 * 1024**2
EVENT_LIMIT = 128 * 1024
Index = Annotated[int, Field(ge=0, lt=1024)]

type OperationKind = Literal["label", "constants", "ensemble", "future", "belief", "flat_moments"]
type ComparisonKind = Literal["refinement", "sensitivity"]
type GateContract = tuple[tuple[str, Decimal | None], ...]

HISTORIES = ("flat", "boundary", "interior")
COUNTS = (64, 256, 1024)
SCALES = (0.125, 0.25, 0.5)
CASE_MANIFEST = tuple((h, n, s) for h in HISTORIES for n in COUNTS for s in SCALES)
EXPECTED_WORK: Mapping[str, int] = MappingProxyType(
    {
        "candidate_producer": 9,
        "candidate_binder": 9,
        "future_prediction": 4032,
        "future_binder": 4032,
        "training_prediction": 12096,
        "training_observer_binder": 12096,
        "belief_compute": 27,
        "belief_raw_binder": 27,
        "belief_result_parser": 27,
        "belief_input_serialization": 27,
        "belief_result_serialization": 27,
        "probability_exp": 12096,
        "normalizer_results": 27,
        "certificate": 27,
        "reference_label": 1,
        "reference_constants": 1,
        "reference_constants_cached": 27,
        "reference_future": 4032,
        "reference_training": 12096,
        "reference_normalization": 27,
        "reference_flat_moments": 1,
        "artifact_serialization": 88,
        "canonical_hash": 60486,
        "native_arithmetic_bound": 12096,
    }
)


def operation_manifest() -> tuple[tuple[str, OperationKind], ...]:
    rows: list[tuple[str, OperationKind]] = [("label", "label"), ("constants", "constants")]
    for history in HISTORIES:
        for count in COUNTS:
            rows.extend(
                (
                    (f"{history}-{count}-ensemble", "ensemble"),
                    (f"{history}-{count}-future", "future"),
                )
            )
            rows.extend((f"{history}-{count}-s{i}", "belief") for i in range(3))
    rows.append(("flat-moments", "flat_moments"))
    return tuple(rows)


def comparison_manifest() -> tuple[tuple[str, ComparisonKind, GateContract], ...]:
    rows: list[tuple[str, ComparisonKind, GateContract]] = []
    for history in HISTORIES:
        for scale in SCALES:
            for coarse, fine in ((64, 256), (256, 1024)):
                required = coarse == 256
                gates: GateContract = (
                    ("cell_tv", D(".001") if required else None),
                    ("mean", D(".0005") if required else None),
                    ("variance", D(".001") if required else None),
                )
                rows.append((f"{history}-{scale}-{coarse}-{fine}", "refinement", gates))
        for count in COUNTS:
            for a, b in ((0.125, 0.25), (0.25, 0.5)):
                rows.append(
                    (
                        f"{history}-{count}-{a}-{b}",
                        "sensitivity",
                        (("cell_tv", None), ("mean", None), ("variance", None)),
                    )
                )
    return tuple(rows)


OPERATION_MANIFEST = operation_manifest()
COMPARISON_MANIFEST = comparison_manifest()


def number(text: str) -> Decimal:
    if len(text) > 160 or not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]{1,3})?", text):
        raise ValueError("Bounded finite decimal spelling required")
    value = D(text)
    exponent = value.as_tuple().exponent
    if not value.is_finite() or not isinstance(exponent, int) or not -200 <= exponent <= 20:
        raise ValueError("Decimal exponent outside the diagnostic domain")
    if value.copy_abs() > D("1e20"):
        raise ValueError("Decimal magnitude outside the diagnostic domain")
    return value


def finite_text(text: str) -> str:
    number(text)
    return text


def hex_text(text: str) -> str:
    value = float.fromhex(text)
    if not math.isfinite(value) or value.hex() != text:
        raise ValueError("Canonical finite binary64 hex required")
    return text


DecimalText = Annotated[str, Field(min_length=1, max_length=160), AfterValidator(finite_text)]
HexFloat = Annotated[str, Field(min_length=1, max_length=32), AfterValidator(hex_text)]


def point(value: Decimal | float | int) -> Interval:
    if isinstance(value, float):
        value = D.from_float(value)
    elif isinstance(value, int):
        value = D(value)
    return Interval(value, value)


def plus(a: Interval, b: Interval) -> Interval:
    with localcontext(Context(prec=PRECISION)) as c:
        c.prec = PRECISION
        c.rounding = ROUND_FLOOR
        lower = a.lower + b.lower
        c.rounding = ROUND_CEILING
        upper = a.upper + b.upper
    return Interval(lower, upper)


def negative(a: Interval) -> Interval:
    # copy_negate is exact and does not use the ambient decimal context.
    return Interval(a.upper.copy_negate(), a.lower.copy_negate())


def minus(a: Interval, b: Interval) -> Interval:
    return plus(a, negative(b))


def times(a: Interval, b: Interval) -> Interval:
    with localcontext(Context(prec=PRECISION)) as c:
        c.prec = PRECISION
        c.rounding = ROUND_FLOOR
        lower = min(x * y for x in (a.lower, a.upper) for y in (b.lower, b.upper))
        c.rounding = ROUND_CEILING
        upper = max(x * y for x in (a.lower, a.upper) for y in (b.lower, b.upper))
    return Interval(lower, upper)


def divide(a: Interval, b: Interval) -> Interval:
    if b.lower <= 0 <= b.upper:
        raise ValueError("Interval division through zero")
    with localcontext(Context(prec=PRECISION)) as c:
        c.prec = PRECISION
        c.rounding = ROUND_FLOOR
        lower = min(x / y for x in (a.lower, a.upper) for y in (b.lower, b.upper))
        c.rounding = ROUND_CEILING
        upper = max(x / y for x in (a.lower, a.upper) for y in (b.lower, b.upper))
    return Interval(lower, upper)


def square(a: Interval) -> Interval:
    result = times(a, a)
    return Interval(D(0), result.upper) if a.lower <= 0 <= a.upper else result


def total(values: tuple[Interval, ...]) -> Interval:
    if not 1 <= len(values) <= 1024:
        raise ValueError("Declared finite vector required")
    result = point(0)
    for value in values:
        result = plus(result, value)
    return result


def absolute_upper(a: Interval) -> Decimal:
    return max(a.lower.copy_abs(), a.upper.copy_abs())


def around(center: Decimal, error: Decimal) -> Interval:
    if error < 0:
        raise ValueError("Nonnegative enclosure allowance required")
    return plus(point(center), Interval(error.copy_negate(), error))


def probabilities(weights: tuple[float, ...]) -> tuple[Interval, ...]:
    """Enclose exact normalized binary64-exp outputs, not a rounded probability array."""
    if not 1 <= len(weights) <= 1024:
        raise ValueError("Declared finite weights required")
    exact = tuple(point(value) for value in weights)
    if any(not p.lower.is_finite() or p.lower <= 0 for p in exact):
        raise ValueError("Every emitted weight must be positive and finite")
    denominator = total(exact)
    return tuple(divide(p, denominator) for p in exact)


def moments(
    weights: tuple[Interval, ...], values: tuple[float, ...]
) -> tuple[Interval, Interval, Interval]:
    if len(weights) != len(values):
        raise ValueError("Complete ordered mixture required")
    x = tuple(point(value) for value in values)
    mean = total(tuple(times(p, v) for p, v in zip(weights, x, strict=True)))
    second = total(tuple(times(p, square(v)) for p, v in zip(weights, x, strict=True)))
    return mean, second, minus(second, square(mean))


def probability_log_envelope(
    actual: tuple[Interval, ...], reference: tuple[Decimal, ...]
) -> Decimal:
    """Inclusive log-ratio envelope without another exp/ln evaluation.

    Reference probability centers have a relative 1e-48 allowance. For positive
    ratios with |ratio-1| <= r < 1, |log ratio| <= r/(1-r).
    """
    if len(actual) != len(reference):
        raise ValueError("Complete reference vector required")
    worst = D(0)
    for p, center in zip(actual, reference, strict=True):
        ref = times(point(center), around(D(1), REFERENCE_LOG_ERROR))
        if ref.lower <= 0:
            raise ValueError("Reference probability is not positive")
        radius = absolute_upper(minus(divide(p, ref), point(1)))
        if radius >= 1:
            raise ValueError("Emitted/reference probability ratio unresolved")
        bound = divide(point(radius), minus(point(1), point(radius))).upper
        worst = max(worst, bound)
    return worst


class IntervalRow(Message):
    lower: DecimalText
    upper: DecimalText

    @model_validator(mode="after")
    def finite_ordered(self) -> Self:
        if number(self.lower) > number(self.upper):
            raise ValueError("Reversed interval")
        return self


def interval_row(value: Interval) -> IntervalRow:
    return IntervalRow(lower=str(value.lower), upper=str(value.upper))


class Artifact(Message):
    path: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}\.json$")]
    sha256: Digest
    bytes: Annotated[int, Field(ge=1, le=16 * 1024**2)]

    @model_validator(mode="after")
    def generated_name(self) -> Self:
        if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}\.json", self.path) is None:
            raise ValueError("Generated artifact basename required")
        return self


class WorkCount(Message):
    name: Annotated[str, Field(pattern=r"^[a-z_]{1,64}$")]
    attempted: Annotated[int, Field(ge=0, le=1_000_000)]
    completed: Annotated[int, Field(ge=0, le=1_000_000)]

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.completed > self.attempted:
            raise ValueError("Completions cannot exceed attempts")
        return self


class OperationRow(Message):
    key: Annotated[str, Field(pattern=r"^[a-z0-9-]{1,80}$")]
    kind: OperationKind
    status: Literal["unrun", "attempted", "completed", "failed"]
    error_type: Annotated[str, Field(max_length=80)] | None = None

    @model_validator(mode="after")
    def failure(self) -> Self:
        if (self.status == "failed") != (self.error_type is not None):
            raise ValueError("Failed operations require a diagnostic type")
        return self


class Gate(Message):
    name: Annotated[str, Field(max_length=80)]
    observed_upper: DecimalText
    limit: DecimalText | None
    passed: bool

    @model_validator(mode="after")
    def exact_gate(self) -> Self:
        value = number(self.observed_upper)
        if value < 0:
            raise ValueError("Gate is a nonnegative error bound")
        if self.limit is not None:
            if self.passed != (value <= number(self.limit)):
                raise ValueError("Gate outcome does not match its fixed bound")
        elif not self.passed:
            raise ValueError("Ungated diagnostic must not claim a failed threshold")
        return self


def require_gates(gates: tuple[Gate, ...], expected: GateContract) -> None:
    actual = tuple((g.name, None if g.limit is None else number(g.limit)) for g in gates)
    if actual != expected:
        raise ValueError("Exact ordered gate names and limits required")


def case_gate_contract(count: int) -> GateContract:
    finest = count == 1024
    return (
        ("training_endpoint", D("1e-12")),
        ("future_endpoint", D("1e-12")),
        ("node_log", D("1e-9")),
        ("centered_log_evidence", D("1e-9")),
        ("normalized_log", D("1e-9")),
        ("reserve-0", D("1e-9")),
        ("reserve-1", D("1e-9")),
        ("reserve-2", D("1e-9")),
        ("cell_tv_bound", D(".0081") if finest else None),
        ("continuous_mean_bound", D(".018") if finest else None),
        ("continuous_second_bound", D(".019") if finest else None),
        ("continuous_variance_bound", D(".056") if finest else None),
    )


class CaseRow(Message):
    history: Literal["flat", "boundary", "interior"]
    count: int
    scale: float
    evidence: Artifact
    certificate: Artifact
    mean: IntervalRow
    second_moment: IntervalRow
    variance: IntervalRow
    boundary_mass: IntervalRow
    gates: Annotated[tuple[Gate, ...], Field(min_length=12, max_length=14)]
    passed: bool

    @model_validator(mode="after")
    def all_gates(self) -> Self:
        if self.count not in COUNTS or self.scale not in SCALES:
            raise ValueError("Outside the fixed grid/scale manifest")
        expected = case_gate_contract(self.count)
        # During flat-moments, a failure may leave an actual 14/12-gate prefix.
        # The enclosing terminal report, not a fabricated placeholder, requires 14.
        if self.history == "flat" and len(self.gates) == 14:
            expected += (
                ("flat_exact_mean", number(self.gates[9].observed_upper)),
                ("flat_exact_second", number(self.gates[10].observed_upper)),
            )
        require_gates(self.gates, expected)
        key = f"{self.history}-{self.count}-s{SCALES.index(self.scale)}"
        if (self.evidence.path, self.certificate.path) != (
            key + "-evidence.json",
            key + "-certificate.json",
        ):
            raise ValueError("Case evidence must retain its exact profile identity")
        if self.passed != all(g.passed for g in self.gates):
            raise ValueError("No failed case gate may be hidden")
        return self


class Comparison(Message):
    key: Annotated[str, Field(max_length=80)]
    kind: ComparisonKind
    gates: Annotated[tuple[Gate, ...], Field(min_length=3, max_length=3)]

    @model_validator(mode="after")
    def fixed_comparison(self) -> Self:
        match = next((row for row in COMPARISON_MANIFEST if row[0] == self.key), None)
        if match is None or self.kind != match[1]:
            raise ValueError("Exact comparison key and kind required")
        require_gates(self.gates, match[2])
        return self


class GridQ1Report(Message):
    schema_version: Literal["strange-physics.grid-q1-qualification.v1"] = (
        "strange-physics.grid-q1-qualification.v1"
    )
    scientific_claim: Literal["diagnostic-only-unaccepted-profile"] = (
        "diagnostic-only-unaccepted-profile"
    )
    protocol_commit: Literal["08ce72b1c82be1d299e873d84f6ba184a6387da6"] = (
        "08ce72b1c82be1d299e873d84f6ba184a6387da6"
    )
    source_commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    authority_sha256: Digest
    terminal_velocity_semantics: Literal["unused-zero-placeholder"] = "unused-zero-placeholder"
    outcome: Literal["passed", "failed", "incomplete"]
    operations: Annotated[tuple[OperationRow, ...], Field(min_length=48, max_length=48)]
    cases: Annotated[tuple[CaseRow, ...], Field(max_length=27)]
    comparisons: Annotated[tuple[Comparison, ...], Field(max_length=36)]
    work: Annotated[tuple[WorkCount, ...], Field(max_length=64)]
    reference_census: Annotated[
        dict[str, Annotated[int, Field(ge=0, le=100_000)]], Field(max_length=10)
    ]
    artifacts: Annotated[tuple[Artifact, ...], Field(max_length=160)]
    fatal_type: Annotated[str, Field(max_length=80)] | None
    fatal_detail: Annotated[str, Field(max_length=240)] | None

    @model_validator(mode="after")
    def no_survivor_acceptance(self) -> Self:
        if tuple((r.key, r.kind) for r in self.operations) != OPERATION_MANIFEST:
            raise ValueError("Exact ordered operation key/kind manifest required")
        if len({w.name for w in self.work}) != len(self.work):
            raise ValueError("Work keys must be unique")
        first_unfinished = next(
            (i for i, row in enumerate(self.operations) if row.status != "completed"),
            len(self.operations),
        )
        if any(row.status != "unrun" for row in self.operations[first_unfinished + 1 :]):
            raise ValueError("Operations must retain the completed/failed/unrun prefix")
        identities = tuple((r.history, r.count, r.scale) for r in self.cases)
        if identities != CASE_MANIFEST[: len(identities)]:
            raise ValueError("Case records must retain their ordered manifest prefix")
        by_path = {a.path: a for a in self.artifacts}
        if len(by_path) != len(self.artifacts):
            raise ValueError("Artifact paths must be unique")
        status = {r.key: r.status for r in self.operations}
        for row in self.cases:
            key = f"{row.history}-{row.count}-s{SCALES.index(row.scale)}"
            if status[key] == "unrun":
                raise ValueError("An unrun profile cannot have completed case evidence")
            for artifact in (row.evidence, row.certificate):
                if by_path.get(artifact.path) != artifact:
                    raise ValueError("Case artifact path/hash/size must join retained artifacts")
        flat = tuple(row for row in self.cases if row.history == "flat")
        updated = tuple(len(row.gates) == 14 for row in flat)
        if any(updated[i] and not updated[i - 1] for i in range(1, len(updated))):
            raise ValueError("Flat exact checks must retain their actual updated prefix")
        if any(updated) and status["flat-moments"] == "unrun":
            raise ValueError("Flat exact checks require an attempted flat-moments operation")
        comparisons = tuple((row.key, row.kind) for row in self.comparisons)
        expected_comparisons = tuple((key, kind) for key, kind, _ in COMPARISON_MANIFEST)
        if comparisons != expected_comparisons[: len(comparisons)]:
            raise ValueError("Comparison records must retain their exact ordered prefix")
        if comparisons and (not all(updated) or status["flat-moments"] == "unrun"):
            raise ValueError("Comparisons follow all flat exact checks")
        complete = first_unfinished == len(self.operations)
        if self.outcome in {"passed", "failed"}:
            if (
                not complete
                or len(self.cases) != 27
                or len(self.comparisons) != 36
                or self.fatal_type is not None
            ):
                raise ValueError("A full diagnostic requires every declared operation")
            if len(flat) != 9 or not all(updated):
                raise ValueError("Full terminal reports require both flat exact-moment gates")
            observed = {w.name: (w.attempted, w.completed) for w in self.work}
            expected_work = {key: (value, value) for key, value in EXPECTED_WORK.items()}
            if observed != expected_work:
                raise ValueError("Exact planned full-success work counts required")
            from grid_q1_reference import EXPECTED

            if self.reference_census != EXPECTED:
                raise ValueError("Complete reference census required")
            passed = all(c.passed for c in self.cases) and all(
                g.passed for c in self.comparisons for g in c.gates
            )
            if (self.outcome == "passed") != passed:
                raise ValueError("Diagnostic outcome must retain every fixed gate")
        elif self.fatal_type is None:
            raise ValueError("Incomplete work requires an explicit diagnostic")
        if (self.fatal_type is None) != (self.fatal_detail is None):
            raise ValueError("Incomplete diagnostic detail must accompany its type")
        return self


def parse_report(raw: bytes) -> GridQ1Report:
    return parse_bounded_json(
        raw, GridQ1Report, max_bytes=REPORT_LIMIT, max_depth=20, max_nodes=40_000
    )


def encoded(value: Message, limit: int) -> bytes:
    result = json.dumps(
        value.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if len(result) > limit:
        raise ValueError("Artifact exceeds its byte bound")
    return result


def _sync_directory(path: Path) -> None:
    """Persist a known local directory entry; propagate unsupported/I/O failures."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Output:
    """Exclusive new directory, fixed generated names, finite aggregate output."""

    def __init__(self, root: Path) -> None:
        if not root.is_absolute() or ".." in root.parts or root.parent.resolve() != root.parent:
            raise ValueError("Normalized absolute output under a real private parent required")
        parent = root.parent.stat()
        if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
            raise ValueError("Output parent must be private and owner controlled")
        root.mkdir(mode=0o700, parents=False, exist_ok=False)
        _sync_directory(root.parent)
        self.root = root
        self.bytes = 0
        self.event_bytes = 0
        self.artifacts: list[Artifact] = []

    def event(self, row: OperationRow) -> None:
        raw = encoded(row, 1024) + b"\n"
        if self.event_bytes + len(raw) > EVENT_LIMIT:
            raise ValueError("Event bound exhausted")
        path = self.root / "events.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "ab") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if self.event_bytes == 0:
            _sync_directory(self.root)
        self.event_bytes += len(raw)

    def write(self, name: str, raw: bytes) -> Artifact:
        artifact = Artifact(path=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        if (
            len(self.artifacts) >= 160
            or self.bytes + len(raw) > OUTPUT_LIMIT - REPORT_LIMIT - EVENT_LIMIT
        ):
            raise ValueError("Artifact allocation exhausted")
        fd = os.open(self.root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_directory(self.root)
        self.bytes += len(raw)
        self.artifacts.append(artifact)
        return artifact

    def finish(self, report: GridQ1Report) -> None:
        if report.artifacts != tuple(self.artifacts):
            raise ValueError("Final report must join this writer's completed artifacts")
        raw = encoded(report, REPORT_LIMIT)
        if parse_report(raw) != report:
            raise ValueError("Report roundtrip mismatch")
        fd = os.open(
            self.root / "report.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_directory(self.root)
