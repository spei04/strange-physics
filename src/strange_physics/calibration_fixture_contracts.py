"""D1 synthetic development material; supplied claims never authorize a run.

Public observations and evaluator-private construction/exposure data are separate
roots. No endpoint generator, predictor, numerical certificate or historical
inventory discovery is implemented here.
"""

from __future__ import annotations

import math
import re
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Limits, Message, ObservationBundle
from strange_physics.research_contracts import CANONICAL_PROFILE, Digest, message_sha256

MAX_PUBLIC_BYTES = 32 * 1024
MAX_PRIVATE_BYTES = 1024 * 1024
MAX_INVENTORY_ROWS = 1024
type CaseId = Literal["M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03"]
CASE_IDS: tuple[CaseId, ...] = ("M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03")
type Mechanism = Literal["zero-rest-spring", "spring-plus-k-over-eight-force"]
type FailureStage = Literal["reference", "rounding", "public_binding", "exposure"]
type ProtocolHash = Literal["657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"]
PROTOCOL_SHA256: ProtocolHash = "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$", min_length=40, max_length=40)]
HexText = Annotated[str, Field(min_length=1, max_length=32)]
InventoryIndex = Annotated[int, Field(ge=0, lt=MAX_INVENTORY_ROWS)]


def _finite_hex(text: str) -> float:
    try:
        value = float.fromhex(text)
    except OverflowError:
        raise ValueError("Binary64 hexadecimal exponent is out of range") from None
    if not math.isfinite(value) or value.hex() != text:
        raise ValueError("Canonical finite binary64 hex required")
    return value


def _same(a: float, b: float) -> bool:
    return a.hex() == b.hex()


def _opaque(value: str, prefix: str) -> bool:
    # This grammar is not proof of secret-independent ID issuance.
    return re.fullmatch(prefix + r"-[0-9a-f]{32}", value) is not None


class D1Blueprint(Message):
    """Private fixed construction metadata; no generated endpoint labels."""

    case_id: CaseId
    coefficient_numerator: Literal[1, 5, 13, 27]
    coefficient_denominator: Literal[7] = 7
    mechanism: Mechanism
    initial_x: float
    record_count: Annotated[int, Field(ge=1, le=2)]
    scales: Annotated[tuple[float, ...], Field(min_length=1, max_length=3)]
    counts: tuple[Literal[256], Literal[1024]] = (256, 1024)

    @model_validator(mode="after")
    def fixed_case(self) -> Self:
        expected = {
            "M01": (1, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
            "M02": (5, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
            "M03": (13, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
            "M04": (27, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
            "D03": (13, "zero-rest-spring", 1.0, 2, (0.25,)),
            "F02": (5, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
            "F04": (27, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
            "W03": (13, "zero-rest-spring", 0.125, 1, (0.25,)),
        }[self.case_id]
        actual = (
            self.coefficient_numerator,
            self.mechanism,
            self.initial_x,
            self.record_count,
            self.scales,
        )
        if actual != expected:
            raise ValueError("Outside the fixed eight-case D1 construction matrix")
        return self


class D1PublicFixture(Message):
    """Candidate-visible observations only; no blueprint or private proof digest."""

    schema_version: Literal["strange-physics.d1-public-fixture.v1"] = (
        "strange-physics.d1-public-fixture.v1"
    )
    provenance: Literal["synthetic-terminal-x-development.v1"] = (
        "synthetic-terminal-x-development.v1"
    )
    velocity_semantics: Literal["unused-zero-placeholder"] = "unused-zero-placeholder"
    observations: ObservationBundle

    @model_validator(mode="after")
    def fixed_public_shape(self) -> Self:
        o = self.observations
        s, sampling = o.space.structure, o.space.sampling
        if (
            not _opaque(o.run_id, "d1r")
            or o.engine_version != "synthetic-ra-n03-d1.v1"
            or o.engine_fingerprint != PROTOCOL_SHA256
            or s.particle_ids != ("p0",)
            or len(s.anchors) != 1
            or s.anchors[0].id != "a0"
            or tuple(x.hex() for x in s.anchors[0].position) != ((0.0).hex(), (0.0).hex())
            or len(s.connections) != 1
            or (s.connections[0].a, s.connections[0].b) != ("p0", "a0")
            or o.space.limits != Limits()
            or o.space.calibration_experiments != 0
            or len(o.records) not in (1, 2)
            or o.space.budget != len(o.records)
            or not all(
                _same(actual, expected)
                for actual, expected in (
                    (sampling.duration, 0.5),
                    (sampling.dt, 1 / 64),
                    (sampling.sample_interval, 0.5),
                    (sampling.position_noise, 0.0),
                    (sampling.velocity_noise, 0.0),
                )
            )
        ):
            raise ValueError("D1 public structure, sampling and generic provenance are fixed")
        for record in o.records:
            if not _opaque(record.operation_id, "d1o") or record.status != "completed":
                raise ValueError("D1 materialized records require opaque operations and endpoints")
            experiment, trajectory = record.experiment, record.trajectory
            assert trajectory is not None
            if len(experiment.particles) != 1:
                raise ValueError("D1 has one particle")
            particle = experiment.particles[0]
            initial = particle.position[0]
            if (
                particle.id != "p0"
                or initial not in (0.125, 1.0)
                or not _same(particle.position[1], 0.0)
                or not _same(particle.mass, 1.0)
                or tuple(x.hex() for x in particle.velocity) != ((0.0).hex(), (0.0).hex())
                or experiment.impulse is None
                or experiment.impulse.particle_id != "p0"
                or tuple(x.hex() for x in experiment.impulse.vector) != ((0.0).hex(), (0.0).hex())
                or len(trajectory.frames) != 2
            ):
                raise ValueError(
                    "D1 actions have fixed mass, zero velocity and explicit zero impulse"
                )
            first, last = trajectory.frames
            if (
                not _same(first.time, 0.0)
                or not _same(last.time, 0.5)
                or not _same(first.positions[0][0], initial)
                or not 0.5 * initial <= last.positions[0][0] <= initial
                or any(
                    not _same(frame.positions[0][1], 0.0)
                    or tuple(x.hex() for x in frame.velocities[0]) != ((0.0).hex(), (0.0).hex())
                    for frame in trajectory.frames
                )
            ):
                raise ValueError("D1 retains exactly two terminal-x synthetic frames")
        if len(o.records) == 2:
            a, b = o.records
            if (
                not _same(a.experiment.particles[0].position[0], 1.0)
                or a.experiment != b.experiment
                or a.trajectory != b.trajectory
            ):
                raise ValueError("The only two-record D1 prefix is an exact physical repeat")
        bounded_canonical(self, MAX_PUBLIC_BYTES)
        return self


def parse_d1_public(raw: bytes) -> D1PublicFixture:
    return parse_bounded_json(
        raw, D1PublicFixture, max_bytes=MAX_PUBLIC_BYTES, max_depth=24, max_nodes=2048
    )


def candidate_material(public: D1PublicFixture) -> ObservationBundle:
    """CORE allowlist projection; private envelopes are not accepted arguments."""
    if type(public) is not D1PublicFixture:
        raise ValueError("Candidate projection requires the separate D1 public type")
    bounded_canonical(public, MAX_PUBLIC_BYTES)
    checked = parse_d1_public(public.model_dump_json().encode("utf-8"))
    o = checked.observations
    return ObservationBundle(
        schema_version=o.schema_version,
        run_id=o.run_id,
        engine_version=o.engine_version,
        engine_fingerprint=o.engine_fingerprint,
        space=o.space,
        records=o.records,
    )


class D1LabelClaim(Message):
    """Reference/one-rounding evidence is supplied, not proved by this message."""

    recorded_x_hex: HexText
    reference_evidence_sha256: Digest
    rounding_evidence_sha256: Digest

    @model_validator(mode="after")
    def finite_label(self) -> Self:
        _finite_hex(self.recorded_x_hex)
        return self


class D1PrivateAudit(Message):
    """Evaluator-only map from exposed blueprints to opaque public material."""

    schema_version: Literal["strange-physics.d1-private-audit.v1"] = (
        "strange-physics.d1-private-audit.v1"
    )
    protocol_sha256: ProtocolHash = PROTOCOL_SHA256
    source_commit: Commit
    blueprint: D1Blueprint
    public_sha256: Digest
    coefficient_hex: HexText
    training_labels: Annotated[tuple[D1LabelClaim, ...], Field(min_length=1, max_length=2)]
    future_label: D1LabelClaim
    future_initial_x: Literal[1.0] = 1.0
    future_time: Literal[0.75] = 0.75
    authority: Literal["supplied-material-not-numerical-proof"] = (
        "supplied-material-not-numerical-proof"
    )

    @model_validator(mode="after")
    def exact_blueprint_labels(self) -> Self:
        coefficient = _finite_hex(self.coefficient_hex)
        if (
            not _same(coefficient, self.blueprint.coefficient_numerator / 7)
            or len(self.training_labels) != self.blueprint.record_count
            or (
                self.blueprint.case_id == "D03"
                and self.training_labels[0] != self.training_labels[1]
            )
        ):
            raise ValueError("Private coefficient and label slots must bind the fixed blueprint")
        bounded_canonical(self, MAX_PRIVATE_BYTES)
        return self


def validate_fixture_binding(public: D1PublicFixture, audit: D1PrivateAudit) -> None:
    """Join actual supplied bytes; no claim that an independent reference was executed."""
    observations = candidate_material(public)
    bounded_canonical(audit, MAX_PRIVATE_BYTES)
    audit = parse_d1_audit(audit.model_dump_json().encode("utf-8"))
    if (
        message_sha256(public) != audit.public_sha256
        or len(observations.records) != audit.blueprint.record_count
        or any(
            not _same(record.experiment.particles[0].position[0], audit.blueprint.initial_x)
            for record in observations.records
        )
    ):
        raise ValueError("Private audit does not name this exact public fixture")
    for record, claim in zip(observations.records, audit.training_labels, strict=True):
        assert record.trajectory is not None
        if record.trajectory.frames[-1].positions[0][0].hex() != claim.recorded_x_hex:
            raise ValueError("Audit label and supplied terminal observation differ")


class D1FixtureOutcome(Message):
    """Private construction failures never become failed or completed purchases."""

    blueprint: D1Blueprint
    status: Literal["unrun", "failed", "materialized"]
    failure_stage: FailureStage | None
    failure_evidence_sha256: Digest | None
    audit: D1PrivateAudit | None

    @model_validator(mode="after")
    def honest_outcome(self) -> Self:
        failed = self.status == "failed"
        if (self.failure_stage is not None) != failed or (
            self.failure_evidence_sha256 is not None
        ) != failed:
            raise ValueError("Only an actual failed construction retains failure evidence")
        if (self.audit is not None) != (self.status == "materialized"):
            raise ValueError("Only materialized fixtures may retain label/audit claims")
        if self.audit is not None and self.audit.blueprint != self.blueprint:
            raise ValueError("Outcome and audit name different constructions")
        return self


class D1FixtureOutcomes(Message):
    schema_version: Literal["strange-physics.d1-fixture-outcomes.v1"] = (
        "strange-physics.d1-fixture-outcomes.v1"
    )
    outcomes: Annotated[tuple[D1FixtureOutcome, ...], Field(min_length=8, max_length=8)]

    @model_validator(mode="after")
    def complete_planned_denominator(self) -> Self:
        if tuple(x.blueprint.case_id for x in self.outcomes) != CASE_IDS:
            raise ValueError("Every planned D1 construction must appear exactly once in order")
        hashes = tuple(x.audit.public_sha256 for x in self.outcomes if x.audit is not None)
        if len(set(hashes)) != len(hashes):
            raise ValueError("Different D1 envelopes need distinct actual public identities")
        bounded_canonical(self, MAX_PRIVATE_BYTES)
        return self


def validate_materialized_fixtures(
    public: tuple[D1PublicFixture, ...], outcomes: D1FixtureOutcomes
) -> None:
    """Bind exactly the materialized subset, preserving unavailable denominator rows."""
    bounded_canonical(outcomes, MAX_PRIVATE_BYTES)
    outcomes = parse_bounded_json(
        outcomes.model_dump_json().encode("utf-8"),
        D1FixtureOutcomes,
        max_bytes=MAX_PRIVATE_BYTES,
        max_depth=24,
        max_nodes=32768,
    )
    audits = tuple(x.audit for x in outcomes.outcomes if x.audit is not None)
    if len(public) != len(audits):
        raise ValueError("Materialized public subset must exactly match the retained outcomes")
    by_case: dict[CaseId, tuple[D1PublicFixture, D1PrivateAudit]] = {}
    run_ids: set[str] = set()
    operation_ids: set[str] = set()
    for value, audit in zip(public, audits, strict=True):
        normalized = D1PublicFixture(observations=candidate_material(value))
        validate_fixture_binding(normalized, audit)
        observations = normalized.observations
        if observations.run_id in run_ids:
            raise ValueError("Materialized D1 fixtures require distinct run identities")
        run_ids.add(observations.run_id)
        for record in observations.records:
            if record.operation_id in operation_ids:
                raise ValueError("D1 operation identities are distinct across materialized runs")
            operation_ids.add(record.operation_id)
        by_case[audit.blueprint.case_id] = (normalized, audit)
    shared: tuple[CaseId, ...] = ("M03", "D03", "W03")
    future_labels = tuple(
        by_case[case][1].future_label.recorded_x_hex for case in shared if case in by_case
    )
    if len(set(future_labels)) > 1:
        raise ValueError("Matched/repeat/weak pairs share the same physical future answer")
    if "M03" in by_case and "D03" in by_case:
        matched = by_case["M03"][0].observations.records[0]
        repeated = by_case["D03"][0].observations.records[0]
        if matched.experiment != repeated.experiment or matched.trajectory != repeated.trajectory:
            raise ValueError("Repeat prefix must retain the matched physical first record")


class D1WorldSignature(Message):
    """Private physical world identity, without blueprint/public display identifiers."""

    mechanism: Mechanism
    coefficient_hex: HexText
    structure: Literal["one-particle-zero-anchor-linear-spring.v1"] = (
        "one-particle-zero-anchor-linear-spring.v1"
    )

    @field_validator("coefficient_hex")
    @classmethod
    def normalize_zero(cls, value: str) -> str:
        return (0.0).hex() if _finite_hex(value) == 0.0 else value

    @model_validator(mode="after")
    def coefficient_domain(self) -> Self:
        if not 0 <= _finite_hex(self.coefficient_hex) <= 4:
            raise ValueError("World signature coefficient outside the D1 support")
        return self


class D1QuerySignature(Message):
    initial_x_hex: HexText
    terminal_time_hex: HexText
    mass_hex: Literal["0x1.0000000000000p+0"] = "0x1.0000000000000p+0"
    initial_velocity_hex: Literal["0x0.0p+0"] = "0x0.0p+0"
    impulse_hex: Literal["0x0.0p+0"] = "0x0.0p+0"
    dt_hex: Literal["0x1.0000000000000p-6"] = "0x1.0000000000000p-6"
    feature: Literal["terminal-x-zero-observation-noise.v1"] = (
        "terminal-x-zero-observation-noise.v1"
    )

    @model_validator(mode="after")
    def query_domain(self) -> Self:
        if _finite_hex(self.initial_x_hex) not in (0.125, 1.0) or _finite_hex(
            self.terminal_time_hex
        ) not in (0.5, 0.75):
            raise ValueError("Query signature outside the fixed D1 arguments")
        return self


class D1PhysicalHistory(Message):
    action_sha256: Annotated[tuple[Digest, ...], Field(min_length=1, max_length=2)]
    recorded_x_hex: Annotated[tuple[HexText, ...], Field(min_length=1, max_length=2)]

    @field_validator("recorded_x_hex")
    @classmethod
    def normalize_zeros(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple((0.0).hex() if _finite_hex(x) == 0.0 else x for x in values)

    @model_validator(mode="after")
    def slots(self) -> Self:
        if len(self.action_sha256) != len(self.recorded_x_hex):
            raise ValueError("Every physical history slot retains its action and observation")
        for value in self.recorded_x_hex:
            _finite_hex(value)
        return self


class D1PhysicalIdentity(Message):
    coefficient_hex: HexText
    world_sha256: Digest
    history_sha256: Digest
    action_sha256: Annotated[tuple[Digest, ...], Field(min_length=1, max_length=2)]
    probe_sha256: Digest

    @field_validator("coefficient_hex")
    @classmethod
    def normalize_coefficient(cls, value: str) -> str:
        parsed = _finite_hex(value)
        if not 0 <= parsed <= 4:
            raise ValueError("Exposure coefficient outside the fixed support")
        return (0.0).hex() if parsed == 0.0 else value


def physical_identity(public: D1PublicFixture, audit: D1PrivateAudit) -> D1PhysicalIdentity:
    bounded_canonical(audit, MAX_PRIVATE_BYTES)
    audit = parse_d1_audit(audit.model_dump_json().encode("utf-8"))
    validate_fixture_binding(public, audit)
    world = D1WorldSignature(
        mechanism=audit.blueprint.mechanism, coefficient_hex=audit.coefficient_hex
    )
    action = D1QuerySignature(
        initial_x_hex=audit.blueprint.initial_x.hex(), terminal_time_hex=(0.5).hex()
    )
    probe = D1QuerySignature(initial_x_hex=(1.0).hex(), terminal_time_hex=(0.75).hex())
    actions = (message_sha256(action),) * audit.blueprint.record_count
    history = D1PhysicalHistory(
        action_sha256=actions,
        recorded_x_hex=tuple(x.recorded_x_hex for x in audit.training_labels),
    )
    return D1PhysicalIdentity(
        coefficient_hex=audit.coefficient_hex,
        world_sha256=message_sha256(world),
        history_sha256=message_sha256(history),
        action_sha256=actions,
        probe_sha256=message_sha256(probe),
    )


class D1ExposureEntry(Message):
    """Private producer-supplied signatures in the above canonical D1 codec."""

    source_evidence_sha256: Digest
    identity: D1PhysicalIdentity


class D1ExposureInventory(Message):
    schema_version: Literal["strange-physics.d1-exposure-inventory.v1"] = (
        "strange-physics.d1-exposure-inventory.v1"
    )
    inventory_kind: Literal["exposed-development", "reserved-comparison"]
    entries: Annotated[tuple[D1ExposureEntry, ...], Field(max_length=MAX_INVENTORY_ROWS)]
    completeness: Literal["not-established-by-this-contract"] = "not-established-by-this-contract"

    @model_validator(mode="after")
    def bounded_inventory(self) -> Self:
        bounded_canonical(self, MAX_PRIVATE_BYTES)
        return self


class D1ExposureFinding(Message):
    identity_sha256: Digest
    inventory_sha256: Digest
    inventory_kind: Literal["exposed-development", "reserved-comparison"]
    supplied_entries: Annotated[int, Field(ge=0, le=MAX_INVENTORY_ROWS)]
    reserved_coefficient_entries: Annotated[int, Field(ge=0, le=MAX_INVENTORY_ROWS)]
    first_reserved_coefficient_index: InventoryIndex | None
    overlapping_world_entries: Annotated[int, Field(ge=0, le=MAX_INVENTORY_ROWS)]
    first_overlap_index: InventoryIndex | None
    first_exact_construction_index: InventoryIndex | None
    conclusion: Literal["overlap-in-supplied-inventory", "no-overlap-in-supplied-inventory"]

    @model_validator(mode="after")
    def counts(self) -> Self:
        world_overlap = self.overlapping_world_entries > 0
        reserved_overlap = self.reserved_coefficient_entries > 0
        overlap = world_overlap or reserved_overlap
        if (
            self.overlapping_world_entries > self.supplied_entries
            or self.reserved_coefficient_entries > self.supplied_entries
            or (self.first_overlap_index is not None) != world_overlap
            or (self.first_reserved_coefficient_index is not None) != reserved_overlap
            or (reserved_overlap and self.inventory_kind != "reserved-comparison")
            or (self.first_exact_construction_index is not None and not world_overlap)
            or self.conclusion
            != ("overlap-in-supplied-inventory" if overlap else "no-overlap-in-supplied-inventory")
            or any(
                i is not None and i >= self.supplied_entries
                for i in (
                    self.first_overlap_index,
                    self.first_exact_construction_index,
                    self.first_reserved_coefficient_index,
                )
            )
        ):
            raise ValueError("Exposure finding must retain its supplied denominator and matches")
        return self


def check_supplied_inventory(
    identity: D1PhysicalIdentity, inventory: D1ExposureInventory
) -> D1ExposureFinding:
    """Detect world overlap despite renamed/reordered histories; never certify completeness."""
    bounded_canonical(identity, MAX_PRIVATE_BYTES)
    identity = parse_bounded_json(
        identity.model_dump_json().encode("utf-8"),
        D1PhysicalIdentity,
        max_bytes=MAX_PRIVATE_BYTES,
        max_depth=24,
        max_nodes=32768,
    )
    bounded_canonical(inventory, MAX_PRIVATE_BYTES)
    inventory = parse_d1_inventory(inventory.model_dump_json().encode("utf-8"))
    reserved_coefficients = tuple((n / 7).hex() for n in (1, 5, 13, 27))
    reserved = tuple(
        i
        for i, entry in enumerate(inventory.entries)
        if inventory.inventory_kind == "reserved-comparison"
        and entry.identity.coefficient_hex in reserved_coefficients
    )
    matches = tuple(
        i
        for i, entry in enumerate(inventory.entries)
        if entry.identity.world_sha256 == identity.world_sha256
    )
    exact = tuple(i for i in matches if inventory.entries[i].identity == identity)
    return D1ExposureFinding(
        identity_sha256=message_sha256(identity),
        inventory_sha256=message_sha256(inventory),
        inventory_kind=inventory.inventory_kind,
        supplied_entries=len(inventory.entries),
        reserved_coefficient_entries=len(reserved),
        first_reserved_coefficient_index=reserved[0] if reserved else None,
        overlapping_world_entries=len(matches),
        first_overlap_index=matches[0] if matches else None,
        first_exact_construction_index=exact[0] if exact else None,
        conclusion=(
            "overlap-in-supplied-inventory"
            if matches or reserved
            else "no-overlap-in-supplied-inventory"
        ),
    )


class D1OwnerReviewReference(Message):
    """Untrusted supplied pointer to external review; not a signature, grant or freeze."""

    protocol_sha256: ProtocolHash = PROTOCOL_SHA256
    development_inventory_sha256: Digest
    comparison_inventory_sha256: Digest
    fixture_outcomes_sha256: Digest
    review_evidence_sha256: Digest
    disposition: Literal["pending", "rejected", "externally-reviewed"]
    scope: Literal["historical-completeness-requires-independent-review"] = (
        "historical-completeness-requires-independent-review"
    )


def parse_d1_audit(raw: bytes) -> D1PrivateAudit:
    return parse_bounded_json(
        raw, D1PrivateAudit, max_bytes=MAX_PRIVATE_BYTES, max_depth=24, max_nodes=4096
    )


def parse_d1_inventory(raw: bytes) -> D1ExposureInventory:
    return parse_bounded_json(
        raw, D1ExposureInventory, max_bytes=MAX_PRIVATE_BYTES, max_depth=24, max_nodes=32768
    )


def calibration_fixture_json_schema() -> JsonSchemaValue:
    roots = (
        D1PublicFixture,
        D1PrivateAudit,
        D1FixtureOutcomes,
        D1ExposureInventory,
        D1ExposureFinding,
        D1OwnerReviewReference,
    )
    _, schema = models_json_schema(
        [(model, "validation") for model in roots], title="RA-N03-D1 supplied fixture contracts v1"
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/calibration-fixture.schema.json"
    schema["x-canonical-profile"] = CANONICAL_PROFILE
    schema["x-public-roots"] = ["D1PublicFixture"]
    schema["x-private-roots"] = [model.__name__ for model in roots[1:]]
    schema["description"] = (
        "Synthetic development material only. No generation, reference, historical completeness, "
        "scientific acceptance, journal purchase or execution authority follows from parsing."
    )
    return schema
