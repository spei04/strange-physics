"""Fixed D1 fixture references and private proof joins; no execution entrypoint.

Calling the producer is numerical work and requires separate admission. Source
pins establish supplied-file consistency, not Git/runtime attestation or authority.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Literal

import endpoint_belief_reference as oracle_module
from endpoint_belief_reference import EndpointOracle, Key
from pydantic import Field

import strange_physics.calibration_fixture_contracts as fixture_module
import strange_physics.contracts as core_module
import strange_physics.bounded_json as json_module
import strange_physics.research_contracts as research_module
from strange_physics.bounded_json import bounded_canonical
from strange_physics.calibration_fixture_contracts import (
    CASE_IDS, PROTOCOL_SHA256, CaseId, D1Blueprint, D1ExposureFinding,
    D1ExposureInventory, D1FixtureOutcome, D1FixtureOutcomes, D1LabelClaim,
    D1PrivateAudit, D1PublicFixture, FailureStage, candidate_material,
    check_supplied_inventory, parse_d1_inventory, parse_d1_public, physical_identity,
    validate_fixture_binding, validate_materialized_fixtures,
)
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.research_contracts import Digest, message_sha256

D = Decimal
SOURCE_PATHS = (
    "docs/research/RA_N03_CALIBRATION_SLICE.md",
    "tests/endpoint_belief_reference.py",
    "tests/d1_fixture_reference.py",
    "src/strange_physics/calibration_fixture_contracts.py",
    "src/strange_physics/contracts.py",
    "src/strange_physics/bounded_json.py",
    "src/strange_physics/research_contracts.py",
)
ORACLE_SHA256 = "039c212450d5cdec851c97e472d1b2fa20a590fa25bd3aa3099d5b04d4bbf4f8"
FILE_LIMIT = 128 * 1024
PROOF_LIMIT = 8 * 1024
ERROR = Fraction(1, 10**60)
NUMERATORS = (1, 5, 13, 27)
# Private order follows the first consumer. D03 and paired future use cached proofs.
QUERY_SPECS = (
    ("train-M01", 1, 0.0, 1.0, 0.5), ("future-M01", 1, 0.0, 1.0, 0.75),
    ("train-M02", 5, 0.0, 1.0, 0.5), ("future-M02", 5, 0.0, 1.0, 0.75),
    ("train-M03", 13, 0.0, 1.0, 0.5), ("future-M03", 13, 0.0, 1.0, 0.75),
    ("train-M04", 27, 0.0, 1.0, 0.5), ("future-M04", 27, 0.0, 1.0, 0.75),
    ("train-F02", 5, 0.125, 1.0, 0.5), ("future-F02", 5, 0.125, 1.0, 0.75),
    ("train-F04", 27, 0.125, 1.0, 0.5), ("future-F04", 27, 0.125, 1.0, 0.75),
    ("train-W03", 13, 0.0, 0.125, 0.5),
)
CASE_SPECS = (
    ("M01", 1, 1.0, 1), ("M02", 5, 1.0, 1), ("M03", 13, 1.0, 1),
    ("M04", 27, 1.0, 1), ("D03", 13, 1.0, 2), ("F02", 5, 1.0, 1),
    ("F04", 27, 1.0, 1), ("W03", 13, 0.125, 1),
)


def checked[T: Message](value: T, model: type[T], limit: int = PROOF_LIMIT) -> T:
    if type(value) is not model:
        raise ValueError("Exact evidence type required")
    bounded_canonical(value, limit)
    return model.model_validate_json(value.model_dump_json())


class SourcePin(Message):
    path: str = Field(max_length=128)
    sha256: Digest


class Sources(Message):
    commit: str = Field(pattern=r"^[0-9a-f]{40}$", min_length=40, max_length=40)
    pins: tuple[SourcePin, ...]
    sizes: tuple[int, ...]


def verify_sources(root: Path, commit: str, pins: tuple[SourcePin, ...]) -> Sources:
    """Read actual bounded source bytes; outer guard owns commit/runtime authenticity."""
    if root != root.resolve() or root.is_symlink():
        raise ValueError("Resolved source checkout required")
    if tuple(p.path for p in pins) != SOURCE_PATHS:
        raise ValueError("Exact seven-file source manifest required")
    expected_loaded = (
        (Path(__file__).resolve(), root / SOURCE_PATHS[2]),
        (Path(oracle_module.__file__).resolve(), root / SOURCE_PATHS[1]),
    )
    if any(actual != expected for actual, expected in expected_loaded):
        raise ValueError("Loaded helper/oracle/contracts are outside the pinned checkout")
    sizes = []
    for pin in pins:
        pin = checked(pin, SourcePin)
        path = root / pin.path
        if path.resolve() != path or path.is_symlink() or not path.is_file():
            raise ValueError("Source must be a regular file at its exact pinned path")
        with path.open("rb") as stream:
            raw = stream.read(FILE_LIMIT + 1)
        if not 0 < len(raw) <= FILE_LIMIT or hashlib.sha256(raw).hexdigest() != pin.sha256:
            raise ValueError("Actual source bytes disagree with the pinned manifest")
        sizes.append(len(raw))
    # A noneditable wheel installation is permitted only with the same bytes.
    for module, pin in zip((fixture_module, core_module, json_module, research_module), pins[3:], strict=True):
        with Path(module.__file__).open("rb") as stream:
            loaded = stream.read(FILE_LIMIT + 1)
        if not 0 < len(loaded) <= FILE_LIMIT or hashlib.sha256(loaded).hexdigest() != pin.sha256:
            raise ValueError("Loaded production module bytes differ from the source pins")
    if pins[0].sha256 != PROTOCOL_SHA256 or pins[1].sha256 != ORACLE_SHA256:
        raise ValueError("Frozen protocol/oracle source changed")
    return Sources(commit=commit, pins=pins, sizes=tuple(sizes))


class Ratio(Message):
    numerator: str = Field(pattern=r"^-?[0-9]+$", max_length=400)
    denominator: str = Field(pattern=r"^[0-9]+$", max_length=400)

    def fraction(self) -> Fraction:
        value = checked(self, Ratio)
        denominator = int(value.denominator)
        if denominator <= 0:
            raise ValueError("Positive denominator required")
        result = Fraction(int(value.numerator), denominator)
        if ratio(result) != value:
            raise ValueError("Reduced canonical rational required")
        return result


def ratio(value: Fraction) -> Ratio:
    return Ratio(numerator=str(value.numerator), denominator=str(value.denominator))


class RoundingProof(Message):
    source_sha256: Digest
    lower: Ratio
    upper: Ratio
    recorded_hex: str = Field(max_length=32)
    lower_midpoint: Ratio
    upper_midpoint: Ratio


def binary(text: str) -> float:
    try:
        value = float.fromhex(text)
    except OverflowError:
        raise ValueError("Out-of-range binary64") from None
    if not math.isfinite(value) or value.hex() != text or not 0 <= value <= 4:
        raise ValueError("Canonical finite binary64 in [0,4] required")
    return value


def midpoint_cell(value: float) -> tuple[Fraction, Fraction]:
    if not math.isfinite(value) or not 0 <= value <= 4:
        raise ValueError("Rounding candidate outside the fixed domain")
    exact = Fraction.from_float(value)
    return (
        (Fraction.from_float(math.nextafter(value, -math.inf)) + exact) / 2,
        (exact + Fraction.from_float(math.nextafter(value, math.inf))) / 2,
    )


def verify_rounding(
    proof: RoundingProof, lower: Fraction, upper: Fraction, source_sha256: str
) -> float:
    proof = checked(proof, RoundingProof)
    value = binary(proof.recorded_hex)
    low_mid, high_mid = midpoint_cell(value)
    if (
        proof.source_sha256 != source_sha256
        or proof.lower.fraction() != lower or proof.upper.fraction() != upper
        or proof.lower_midpoint.fraction() != low_mid
        or proof.upper_midpoint.fraction() != high_mid
        or not low_mid < lower <= upper < high_mid
    ):
        raise ValueError("Strict rounding cell proof failed; no refinement or retry")
    return value


def round_once(
    candidate: float, lower: Fraction, upper: Fraction, source_sha256: str
) -> RoundingProof:
    low_mid, high_mid = midpoint_cell(candidate)
    proof = RoundingProof(
        source_sha256=source_sha256, lower=ratio(lower), upper=ratio(upper),
        recorded_hex=candidate.hex(), lower_midpoint=ratio(low_mid), upper_midpoint=ratio(high_mid),
    )
    verify_rounding(proof, lower, upper, source_sha256)
    return proof


class CoefficientProof(Message):
    numerator: Literal[1, 5, 13, 27]
    denominator: Literal[7] = 7
    rounding: RoundingProof


def coefficient_source(numerator: int) -> str:
    return hashlib.sha256(f"strange-physics.d1-coefficient.v1:{numerator}/7".encode()).hexdigest()


def coefficients() -> tuple[CoefficientProof, ...]:
    result = []
    for n in NUMERATORS:
        value = Fraction(n, 7)
        result.append(CoefficientProof.model_validate({
            "numerator": n,
            "rounding": round_once(float(value), value, value, coefficient_source(n)),
        }))
    return tuple(result)


class Query(Message):
    name: str = Field(max_length=32)
    key: tuple[str, str, str, str, str, str, str]


class Plan(Message):
    source_sha256: Digest
    coefficients: tuple[CoefficientProof, ...]
    queries: tuple[Query, ...]


def fixed_plan(source: Sources, proofs: tuple[CoefficientProof, ...]) -> Plan:
    source = checked(source, Sources, FILE_LIMIT)
    if tuple(p.numerator for p in proofs) != NUMERATORS:
        raise ValueError("Four ordered coefficient proof records required")
    values = {}
    for proof in proofs:
        proof = checked(proof, CoefficientProof)
        exact = Fraction(proof.numerator, 7)
        values[proof.numerator] = verify_rounding(
            proof.rounding, exact, exact, coefficient_source(proof.numerator)
        )
    queries = tuple(Query(name=name, key=(
        values[n].hex(), (1.0).hex(), a.hex(), q.hex(), (0.0).hex(), (0.0).hex(), t.hex(),
    )) for name, n, a, q, t in QUERY_SPECS)
    return Plan(source_sha256=message_sha256(source), coefficients=proofs, queries=queries)


class ReferenceProof(Message):
    query: Query
    source_sha256: Digest
    center: str = Field(max_length=128)
    lower: Ratio
    upper: Ratio
    absolute_reference_error: Literal["1e-60"] = "1e-60"


def reference_proof(query: Query, source_sha256: str, center: Decimal) -> ReferenceProof:
    if type(center) is not Decimal or not center.is_finite():
        raise ValueError("Finite Decimal reference center required")
    parts = center.as_tuple()
    if (
        len(parts.digits) > 120 or not isinstance(parts.exponent, int)
        or not -256 <= parts.exponent <= 128 or not D(0) <= center <= D(1)
    ):
        raise ValueError("Reference center outside the fixed bounded representation")
    exact = Fraction(center)
    return ReferenceProof(
        query=query, source_sha256=source_sha256, center=str(center),
        lower=ratio(exact - ERROR), upper=ratio(exact + ERROR),
    )


def verify_reference(proof: ReferenceProof, query: Query, source: Sources) -> ReferenceProof:
    proof = checked(proof, ReferenceProof)
    expected = reference_proof(query, message_sha256(source), D(proof.center))
    if proof != expected:
        raise ValueError("Reference evidence disagrees with actual query/source/center")
    return proof


class PublicIds(Message):
    run_id: str = Field(pattern=r"^d1r-[0-9a-f]{32}$", min_length=36, max_length=36)
    operations: tuple[str, ...]


def validate_ids(ids: tuple[PublicIds, ...]) -> tuple[PublicIds, ...]:
    if len(ids) != 8:
        raise ValueError("Eight preissued opaque ID groups required")
    result = tuple(checked(value, PublicIds) for value in ids)
    operations = tuple(op for value in result for op in value.operations)
    if (
        len({x.run_id for x in result}) != 8 or len(set(operations)) != 9
        or tuple(len(x.operations) for x in result) != (1, 1, 1, 1, 2, 1, 1, 1)
        or any(re.fullmatch(r"d1o-[0-9a-f]{32}", op) is None for op in operations)
    ):
        raise ValueError("Distinct run/operation identities with exact slot counts required")
    return result


def blueprint(case: CaseId) -> D1Blueprint:
    _, n, q, records = CASE_SPECS[CASE_IDS.index(case)]
    return D1Blueprint.model_validate({
        "case_id": case, "coefficient_numerator": n, "initial_x": q, "record_count": records,
        "mechanism": "spring-plus-k-over-eight-force" if case.startswith("F") else "zero-rest-spring",
        "scales": (0.25,) if case in ("D03", "W03") else (0.125, 0.25, 0.5),
    })


def query_names(case: CaseId) -> tuple[str, str]:
    training = "M03" if case == "D03" else case
    future = "M03" if case in ("D03", "W03") else case
    return "train-" + training, "future-" + future


def build_public(ids: PublicIds, initial_x: float, labels: tuple[float, ...]) -> D1PublicFixture:
    """CORE allowlist only: no blueprint, coefficient, force or future argument."""
    ids = checked(ids, PublicIds)
    if len(labels) != len(ids.operations) or len(labels) not in (1, 2):
        raise ValueError("Every public operation requires one training label")
    experiment = {
        "particles": [{"id": "p0", "position": (initial_x, 0.0), "velocity": (0.0, 0.0), "mass": 1.0}],
        "impulse": {"particle_id": "p0", "vector": (0.0, 0.0)},
    }
    records = tuple({
        "operation_id": op, "index": index, "experiment": experiment, "status": "completed",
        "trajectory": {"frames": (
            {"time": 0.0, "positions": ((initial_x, 0.0),), "velocities": ((0.0, 0.0),)},
            {"time": 0.5, "positions": ((label, 0.0),), "velocities": ((0.0, 0.0),)},
        )},
    } for index, (op, label) in enumerate(zip(ids.operations, labels, strict=True)))
    public = D1PublicFixture.model_validate({"observations": {
        "run_id": ids.run_id, "engine_version": "synthetic-ra-n03-d1.v1",
        "engine_fingerprint": PROTOCOL_SHA256,
        "space": {
            "structure": {
                "particle_ids": ("p0",), "anchors": ({"id": "a0", "position": (0.0, 0.0)},),
                "connections": ({"a": "p0", "b": "a0"},),
            },
            "sampling": {"duration": 0.5, "dt": 1 / 64, "sample_interval": 0.5,
                         "position_noise": 0.0, "velocity_noise": 0.0},
            "budget": len(labels), "calibration_experiments": 0,
        },
        "records": records,
    }})
    return parse_d1_public(public.model_dump_json().encode())


class Failure(Message):
    case: CaseId
    stage: FailureStage
    exception_type: str = Field(max_length=96)
    detail: str = Field(max_length=240)
    query: str | None


class QueryTrace(Message):
    query: Query
    status: Literal["unrun", "attempted", "reference_returned", "reference_failed", "rounding_failed", "completed"]
    returned_center: str | None = Field(default=None, max_length=128)


class Reuse(Message):
    case: CaseId
    query_name: str
    consumer_slots: int = Field(ge=1, le=2)


@dataclass(frozen=True)
class Attempt:
    case: CaseId
    public: D1PublicFixture
    audit: D1PrivateAudit
    findings: tuple[D1ExposureFinding, ...]


@dataclass(frozen=True)
class FixtureBatch:
    root: Path
    commit: str
    pins: tuple[SourcePin, ...]
    sources: Sources | None
    plan: Plan | None
    references: tuple[ReferenceProof, ...]
    roundings: tuple[RoundingProof, ...]
    attempts: tuple[Attempt, ...]
    inventories: tuple[D1ExposureInventory, ...]
    outcomes: D1FixtureOutcomes
    first_fault: Failure | None
    lookup_attempted: int
    lookup_completed: int
    series_completed: int
    source_rechecked: bool
    oracle_census: tuple[int, ...] | None
    query_trace: tuple[QueryTrace, ...]
    reuse: tuple[Reuse, ...]


def bind_attempt(
    attempt: Attempt, plan: Plan, source: Sources,
    references: tuple[ReferenceProof, ...], roundings: tuple[RoundingProof, ...],
    inventories: tuple[D1ExposureInventory, ...],
) -> None:
    """Recompute digests and joins from retained material, never compare bare claims alone."""
    if plan != fixed_plan(source, plan.coefficients):
        raise ValueError("Actual fixed plan differs")
    by_query = {r.query.name: r for r in references}
    if len(by_query) != len(references) or len(roundings) != len(references):
        raise ValueError("Distinct completed reference/rounding pairs required")
    proofs = {message_sha256(r): p for r, p in zip(references, roundings, strict=True)}
    names = query_names(attempt.case)
    claims = []
    for name in names:
        query = next(q for q in plan.queries if q.name == name)
        reference = verify_reference(by_query[name], query, source)
        digest = message_sha256(reference)
        proof = proofs[digest]
        verify_rounding(proof, reference.lower.fraction(), reference.upper.fraction(), digest)
        claims.append(D1LabelClaim(
            recorded_x_hex=proof.recorded_hex, reference_evidence_sha256=digest,
            rounding_evidence_sha256=message_sha256(proof),
        ))
    b = blueprint(attempt.case)
    coefficient = next(p for p in plan.coefficients if p.numerator == b.coefficient_numerator)
    expected_audit = D1PrivateAudit(
        source_commit=source.commit, blueprint=b, public_sha256=message_sha256(attempt.public),
        coefficient_hex=coefficient.rounding.recorded_hex,
        training_labels=(claims[0],) * b.record_count, future_label=claims[1],
    )
    if checked(attempt.audit, D1PrivateAudit, 16 * 1024) != expected_audit:
        raise ValueError("Audit is not bound to the actual reference and rounded material")
    validate_fixture_binding(attempt.public, expected_audit)
    identity = physical_identity(attempt.public, expected_audit)
    expected_findings = tuple(check_supplied_inventory(identity, x) for x in inventories)
    if attempt.findings != expected_findings:
        raise ValueError("Findings are not bound to the actual supplied inventory bytes")


def candidate_materials(batch: FixtureBatch) -> tuple[ObservationBundle, ...]:
    """Explicit all-success projection; the enclosing batch is always evaluator-private."""
    if (
        batch.first_fault is not None or not batch.source_rechecked
        or batch.sources is None or batch.plan is None
        or len(batch.attempts) != 8 or len(batch.references) != 13 or len(batch.roundings) != 13
        or (batch.lookup_attempted, batch.lookup_completed, batch.series_completed) != (13, 13, 13)
        or any(x.status != "materialized" for x in batch.outcomes.outcomes)
        or batch.oracle_census != (13, 13, 0, 0, 0, 0, 13)
        or len(batch.query_trace) != 13 or any(x.status != "completed" for x in batch.query_trace)
    ):
        raise ValueError("Incomplete private construction is not candidate-ready")
    actual = verify_sources(batch.root, batch.commit, batch.pins)
    if actual != batch.sources or tuple(a.case for a in batch.attempts) != CASE_IDS:
        raise ValueError("Current source or case identity differs")
    if tuple(x.query for x in batch.query_trace) != batch.plan.queries:
        raise ValueError("Query trace differs from the actual plan")
    reference_centers = {x.query.name: x.center for x in batch.references}
    if any(
        row.returned_center != reference_centers.get(row.query.name)
        for row in batch.query_trace
    ):
        raise ValueError("Completed query trace must retain its actual reference center")
    if batch.reuse != (
        Reuse(case="D03", query_name="train-M03", consumer_slots=2),
        Reuse(case="D03", query_name="future-M03", consumer_slots=1),
        Reuse(case="W03", query_name="future-M03", consumer_slots=1),
    ):
        raise ValueError("Shared physical proof reuse differs")
    _inventories(batch.inventories)
    for attempt, outcome in zip(batch.attempts, batch.outcomes.outcomes, strict=True):
        if outcome.audit != attempt.audit or outcome.blueprint.case_id != attempt.case:
            raise ValueError("Outcome is not the retained attempt's exact private audit")
        bind_attempt(attempt, batch.plan, actual, batch.references, batch.roundings, batch.inventories)
        if any(x.conclusion != "no-overlap-in-supplied-inventory" for x in attempt.findings):
            raise ValueError("Supplied exposure overlap blocks candidate projection")
    public = tuple(a.public for a in batch.attempts)
    validate_materialized_fixtures(public, batch.outcomes)
    return tuple(candidate_material(x) for x in public)


def _inventories(values: tuple[D1ExposureInventory, ...]) -> tuple[D1ExposureInventory, ...]:
    if tuple(x.inventory_kind for x in values) != ("exposed-development", "reserved-comparison"):
        raise ValueError("Both ordered supplied inventories required")
    return tuple(parse_d1_inventory(x.model_dump_json().encode()) for x in values)


class D1FixtureProducer:
    """One private in-memory attempt. Outer persistent authority still prevents restarts."""

    def __init__(self, root: Path, commit: str, pins: tuple[SourcePin, ...]) -> None:
        self.root, self.commit, self.pins = root, commit, pins
        self.started = False

    def run(
        self, ids: tuple[PublicIds, ...], inventories: tuple[D1ExposureInventory, ...]
    ) -> FixtureBatch:
        if self.started:
            raise ValueError("Producer attempt already consumed; no retry")
        self.started = True
        source: Sources | None = None
        plan: Plan | None = None
        refs: list[ReferenceProof] = []
        rounds: list[RoundingProof] = []
        attempts: list[Attempt] = []
        outcomes: list[D1FixtureOutcome] = []
        fault: Failure | None = None
        case: CaseId = CASE_IDS[0]
        stage: FailureStage = "reference"
        active_query: str | None = None
        requested = completed = series = 0
        source_rechecked = False
        checked_inventories: tuple[D1ExposureInventory, ...] = ()
        oracle: EndpointOracle | None = None
        traces: list[QueryTrace] = []
        reuses: list[Reuse] = []
        try:
            source = verify_sources(self.root, self.commit, self.pins)
            stage = "public_binding"
            ids = validate_ids(ids)
            stage = "exposure"
            checked_inventories = _inventories(inventories)
            stage = "rounding"
            plan = fixed_plan(source, coefficients())
            oracle = EndpointOracle()
            traces = [QueryTrace(query=q, status="unrun") for q in plan.queries]
            # All other methods remain unused. The fixed instance is never reset/replaced.
            cache: dict[tuple[str, ...], tuple[ReferenceProof, RoundingProof]] = {}
            for case, group in zip(CASE_IDS, ids, strict=True):
                b = blueprint(case)
                for name in query_names(case):
                    query = next(q for q in plan.queries if q.name == name)
                    if query.key in cache:
                        reuses.append(Reuse(case=case, query_name=name,
                                            consumer_slots=b.record_count if name.startswith("train") else 1))
                        continue
                    if plan.queries[requested] != query:
                        raise ValueError("Reference traversal differs from the fixed plan")
                    stage, active_query = "reference", name
                    traces[requested] = QueryTrace(query=query, status="attempted")
                    requested += 1
                    key: Key = (
                        binary(query.key[0]), binary(query.key[1]), binary(query.key[2]),
                        binary(query.key[3]), binary(query.key[4]), binary(query.key[5]),
                        binary(query.key[6]),
                    )
                    # Existing oracle inherits the caller context beyond its precision.
                    # Supply every context setting explicitly for this finite invocation.
                    context = Context(prec=100, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                                      capitals=1, clamp=0, flags=[], traps=[])
                    with localcontext(context):
                        center = oracle.position(key)
                    completed += 1
                    traces[requested - 1] = QueryTrace(
                        query=query, status="reference_returned",
                        returned_center=str(center)[:128] if isinstance(center, Decimal) else None,
                    )
                    series = oracle.series_values
                    reference = reference_proof(query, message_sha256(source), center)
                    refs.append(reference)
                    stage = "rounding"
                    proof = round_once(
                        float(center), reference.lower.fraction(), reference.upper.fraction(),
                        message_sha256(reference),
                    )
                    rounds.append(proof)
                    cache[query.key] = reference, proof
                    traces[requested - 1] = QueryTrace(
                        query=query, status="completed", returned_center=str(center),
                    )
                active_query = None
                train_name, future_name = query_names(case)
                train_key = next(q.key for q in plan.queries if q.name == train_name)
                future_key = next(q.key for q in plan.queries if q.name == future_name)
                train_ref, train_round = cache[train_key]
                future_ref, future_round = cache[future_key]
                stage = "public_binding"
                public = build_public(group, b.initial_x, (binary(train_round.recorded_hex),) * b.record_count)
                def claim(ref: ReferenceProof, rounding: RoundingProof) -> D1LabelClaim:
                    return D1LabelClaim(
                        recorded_x_hex=rounding.recorded_hex, reference_evidence_sha256=message_sha256(ref),
                        rounding_evidence_sha256=message_sha256(rounding),
                    )
                coefficient = next(x for x in plan.coefficients if x.numerator == b.coefficient_numerator)
                audit = D1PrivateAudit(
                    source_commit=source.commit, blueprint=b, public_sha256=message_sha256(public),
                    coefficient_hex=coefficient.rounding.recorded_hex,
                    training_labels=(claim(train_ref, train_round),) * b.record_count,
                    future_label=claim(future_ref, future_round),
                )
                stage = "exposure"
                identity = physical_identity(public, audit)
                findings = tuple(check_supplied_inventory(identity, x) for x in checked_inventories)
                attempt = Attempt(case, public, audit, findings)
                attempts.append(attempt)
                bind_attempt(attempt, plan, source, tuple(refs), tuple(rounds), checked_inventories)
                if any(x.conclusion != "no-overlap-in-supplied-inventory" for x in findings):
                    raise ValueError("Overlap in supplied inventory; no historical completeness claim")
                outcomes.append(D1FixtureOutcome(
                    blueprint=b, status="materialized", failure_stage=None, failure_evidence_sha256=None, audit=audit,
                ))
            stage = "reference"
            if (
                (requested, completed, oracle.lookups, oracle.series_values) != (13, 13, 13, 13)
                or (oracle.exp_calls, oracle.log_calls, oracle.trig_calls, oracle.machin_terms) != (0, 0, 0, 0)
                or len(oracle.values) != 13
            ):
                raise ValueError("Fixed reference work census differs")
            validate_materialized_fixtures(
                tuple(x.public for x in attempts), D1FixtureOutcomes(outcomes=tuple(outcomes))
            )
            if verify_sources(self.root, self.commit, self.pins) != source:
                raise ValueError("Source changed during the producer attempt")
            source_rechecked = True
        except BaseException as error:
            # The enclosing runtime must persist this private failure before ending.
            # Returning retained failure is never a success or permission to continue.
            if active_query is not None and requested:
                row = traces[requested - 1]
                traces[requested - 1] = QueryTrace(
                    query=row.query,
                    status="rounding_failed" if stage == "rounding" else "reference_failed",
                    returned_center=row.returned_center,
                )
            fault = Failure(
                case=case, stage=stage, exception_type=type(error).__name__[:96],
                detail=f"{stage} stopped the fixed attempt; retained material is private", query=active_query,
            )
            if len(outcomes) == 8:
                outcomes.pop()
            outcomes.append(D1FixtureOutcome(
                blueprint=blueprint(case), status="failed", failure_stage=stage,
                failure_evidence_sha256=message_sha256(fault), audit=None,
            ))
        while len(outcomes) < 8:
            outcomes.append(D1FixtureOutcome(
                blueprint=blueprint(CASE_IDS[len(outcomes)]), status="unrun",
                failure_stage=None, failure_evidence_sha256=None, audit=None,
            ))
        census = None if oracle is None else (
            oracle.lookups, oracle.series_values, oracle.exp_calls, oracle.log_calls,
            oracle.trig_calls, oracle.machin_terms, len(oracle.values),
        )
        if oracle is not None:
            series = oracle.series_values
        return FixtureBatch(
            self.root, self.commit, self.pins, source, plan, tuple(refs), tuple(rounds),
            tuple(attempts), checked_inventories, D1FixtureOutcomes(outcomes=tuple(outcomes)),
            fault, requested, completed, series, source_rechecked, census, tuple(traces), tuple(reuses),
        )
