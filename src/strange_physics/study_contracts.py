"""Bounded native STUDY/COST messages; parsing never authorizes execution.

The accounting plan exists before cost-bearing reference work. A later manifest
is attached to the same ledger; it never creates a second allowance.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.research_contracts import CANONICAL_PROFILE, Digest, message_sha256

MAX_CPU_NS = 8 * 60 * 60 * 1_000_000_000
MAX_ARTIFACT_BYTES = 1024**3
MAX_LEDGER_RECORDS = 8192
MAX_STUDY_JSON_BYTES = 8 * 1024**2
SafeCount = Annotated[int, Field(ge=0, le=2**53 - 1)]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$", min_length=40, max_length=40)]
Selector = Literal["random", "uniform_disagreement", "posterior_disagreement"]
SELECTORS: tuple[Selector, ...] = (
    "random",
    "uniform_disagreement",
    "posterior_disagreement",
)
ArtifactKind = Literal[
    "native_profile",
    "pool",
    "menu",
    "calibration",
    "prior",
    "likelihood",
    "discrepancy",
    "scorer_protocol",
    "termination_policy",
    "failure_policy",
    "selector_random",
    "selector_uniform_disagreement",
    "selector_posterior_disagreement",
]
ARTIFACT_KINDS = (
    "native_profile",
    "pool",
    "menu",
    "calibration",
    "prior",
    "likelihood",
    "discrepancy",
    "scorer_protocol",
    "termination_policy",
    "failure_policy",
    "selector_random",
    "selector_uniform_disagreement",
    "selector_posterior_disagreement",
)
OperationKind = Literal[
    "candidate_production",
    "selection",
    "prediction",
    "preparation",
    "scoring",
    "purchase",
    "forward",
    "likelihood",
    "ranking",
    "reference",
    "sensitivity",
    "accounting",
]
Phase = Literal["reference", "calibration", "sensitivity", "comparison", "accounting"]


class NativeAccountingPlan(Message):
    schema_version: Literal["strange-physics.native-accounting-plan.v1"] = (
        "strange-physics.native-accounting-plan.v1"
    )
    study_id: Identifier
    purpose: Literal["synthetic_validation", "native_comparison"]
    approval_id: Literal["NATIVE_COMPARISON_APPROVAL_2026_10_21"]
    episode_limit: Annotated[int, Field(ge=36, le=36)] = 36
    purchase_limit: Annotated[int, Field(ge=432, le=432)] = 432
    cpu_limit_ns: Annotated[int, Field(ge=MAX_CPU_NS, le=MAX_CPU_NS)] = MAX_CPU_NS
    artifact_limit_bytes: Annotated[int, Field(ge=MAX_ARTIFACT_BYTES, le=MAX_ARTIFACT_BYTES)] = (
        MAX_ARTIFACT_BYTES
    )
    cost_policy: Literal["all-work-no-reset.v1"] = "all-work-no-reset.v1"


class StudyArtifact(Message):
    """Exact retained producer bytes; no implied semantic validation or public audience."""

    kind: ArtifactKind
    sha256: Digest
    byte_count: Annotated[int, Field(ge=1, le=MAX_STUDY_JSON_BYTES)]
    encoding: Literal["strange-physics.python-json.v1"] = "strange-physics.python-json.v1"


class StudyGate(Message):
    """Trusted acceptance evidence, checked by the run producer, never a capability."""

    unit: Literal["RA-N01", "RA-N02.a", "RA-N03", "RA-N04"]
    source_commit: Commit
    evidence_sha256: Digest


class NativeStudyCell(Message):
    cell_id: Identifier
    world_id: Identifier
    policy_seed: Annotated[int, Field(ge=0, le=2**32 - 1)]
    selector: Selector
    journal_id: Identifier
    purchased_slots: Annotated[int, Field(ge=12, le=12)] = 12
    calibration_slots: Annotated[int, Field(ge=4, le=4)] = 4


class NativeStudyManifest(Message):
    schema_version: Literal["strange-physics.native-study-manifest.v1"] = (
        "strange-physics.native-study-manifest.v1"
    )
    accounting_plan_sha256: Digest
    source_commit: Commit
    uv_lock_sha256: Digest
    world_ids: Annotated[tuple[Identifier, ...], Field(min_length=6, max_length=6)]
    policy_seeds: Annotated[
        tuple[Annotated[int, Field(ge=0, le=2**32 - 1)], ...],
        Field(min_length=2, max_length=2),
    ]
    artifacts: Annotated[tuple[StudyArtifact, ...], Field(min_length=13, max_length=13)]
    gates: Annotated[tuple[StudyGate, ...], Field(min_length=4, max_length=4)]
    cells: Annotated[tuple[NativeStudyCell, ...], Field(min_length=36, max_length=36)]
    failure_policy: Literal["retain-every-cell-and-attempt.v1"] = "retain-every-cell-and-attempt.v1"
    primary_output: Literal["one-selected-native-candidate.v1"] = "one-selected-native-candidate.v1"

    @model_validator(mode="after")
    def complete_matrix(self) -> Self:
        if len(set(self.world_ids)) != 6 or len(set(self.policy_seeds)) != 2:
            raise ValueError("World IDs and policy seeds must be unique")
        if tuple(a.kind for a in self.artifacts) != ARTIFACT_KINDS:
            raise ValueError("Every required artifact must occur once in declared order")
        if tuple(g.unit for g in self.gates) != ("RA-N01", "RA-N02.a", "RA-N03", "RA-N04"):
            raise ValueError("Every numerical/acquisition gate must be retained")
        expected = tuple(
            (world, seed, selector)
            for world in self.world_ids
            for seed in self.policy_seeds
            for selector in SELECTORS
        )
        if tuple((c.world_id, c.policy_seed, c.selector) for c in self.cells) != expected:
            raise ValueError("Cells must be the complete ordered six by two by three matrix")
        if (
            len({c.cell_id for c in self.cells}) != 36
            or len({c.journal_id for c in self.cells}) != 36
        ):
            raise ValueError("Every arm needs a unique cell and journal identity")
        return self

    def artifact(self, kind: ArtifactKind) -> StudyArtifact:
        return next(a for a in self.artifacts if a.kind == kind)


class NativeWorkFacts(Message):
    """Operation-local counts, not measured hardware work or proof of authenticity."""

    attempt_id: Identifier
    operation: OperationKind
    producer_version: Annotated[str, Field(min_length=1, max_length=128)]
    config_sha256: Digest
    input_sha256: Digest
    observation_sha256: Digest | None
    model_sha256: Digest | None
    output_sha256: Digest
    unit: Literal["candidate", "frame", "probe", "selection", "preparation", "record", "work"]
    requested_count: SafeCount
    completed_count: SafeCount
    failed_count: SafeCount
    not_assessed_count: SafeCount
    outcome: Literal["completed", "rejected", "failed"]

    @model_validator(mode="after")
    def partition(self) -> Self:
        if (
            self.completed_count + self.failed_count + self.not_assessed_count
            != self.requested_count
        ):
            raise ValueError("Local unit outcomes must partition all requested work")
        if self.outcome == "completed" and (self.failed_count or self.not_assessed_count):
            raise ValueError("Completed local work cannot omit requested units")
        if self.outcome == "rejected" and (self.completed_count or self.failed_count):
            raise ValueError("Preflight rejection leaves all requested work unassessed")
        return self


class StudyPurchase(Message):
    operation_id: Identifier
    ordinal: Annotated[int, Field(ge=0, le=11)]
    experiment_sha256: Digest
    calibration: bool

    @model_validator(mode="after")
    def calibration_position(self) -> Self:
        if self.calibration != (self.ordinal < 4):
            raise ValueError("The first four reserved slots are calibration slots")
        return self


class StudyAttemptReservation(Message):
    kind: Literal["reserve"] = "reserve"
    attempt_id: Identifier
    phase: Phase
    cell_id: Identifier | None
    operation: OperationKind
    config_sha256: Digest
    input_sha256: Digest
    retry_of: Identifier | None
    cpu_reservation_ns: Annotated[int, Field(ge=1, le=MAX_CPU_NS)]
    artifact_reservation_bytes: Annotated[int, Field(ge=0, le=MAX_ARTIFACT_BYTES)]
    purchase: StudyPurchase | None

    @model_validator(mode="after")
    def scope(self) -> Self:
        if (self.phase == "comparison") != (self.cell_id is not None):
            raise ValueError("Only comparison work names a study cell")
        if (self.operation == "purchase") != (self.purchase is not None):
            raise ValueError("Purchase attempts retain the exact reservation identity")
        if self.purchase is not None and self.cell_id is None:
            raise ValueError("Purchased slots require a comparison cell")
        if self.retry_of == self.attempt_id:
            raise ValueError("A repeated computation needs a fresh attempt identity")
        return self


class StudyAttemptUpdate(Message):
    kind: Literal["update"] = "update"
    attempt_id: Identifier
    state: Literal["running", "unknown", "completed", "failed", "rejected"]
    # Measurements may exceed the reservation: retain the overrun honestly.
    cpu_ns: SafeCount | None
    wall_ns: SafeCount | None
    artifact_bytes: SafeCount | None
    facts: NativeWorkFacts | None

    @model_validator(mode="after")
    def final_measurements(self) -> Self:
        if self.state in {"completed", "failed", "rejected"}:
            if None in (self.cpu_ns, self.wall_ns, self.artifact_bytes) or self.facts is None:
                raise ValueError("Final outcomes need measured costs and complete local facts")
            if self.facts.outcome != self.state:
                raise ValueError("Final state and local outcome differ")
        if self.facts is not None and self.facts.attempt_id != self.attempt_id:
            raise ValueError("Facts belong to another attempt")
        return self


class StudyManifestFreeze(Message):
    kind: Literal["freeze"] = "freeze"
    manifest: NativeStudyManifest


class StudyCellOutcome(Message):
    """Retained metadata from actual-material binding, never evaluator truth."""

    kind: Literal["cell_outcome"] = "cell_outcome"
    cell_id: Identifier
    status: Literal["complete", "failed", "incomplete", "cap_limited"]
    reason: Literal["scored", "unscorable", "execution_failure", "interrupted", "resource_limit"]
    journal_id: Identifier
    observation_sha256: Digest | None
    model_sha256: Digest | None
    report_sha256: Digest | None
    protocol_sha256: Digest
    selector_config_sha256: Digest

    @model_validator(mode="after")
    def complete_evidence(self) -> Self:
        if self.status == "complete":
            if self.reason != "scored" or None in (
                self.observation_sha256,
                self.model_sha256,
                self.report_sha256,
            ):
                raise ValueError("Complete cell needs a scored actual model/prefix/report")
        elif self.reason == "scored":
            raise ValueError("A scored completion must be explicit")
        if self.report_sha256 is not None and (
            self.model_sha256 is None or self.observation_sha256 is None
        ):
            raise ValueError("Retained report requires its actual model and prefix")
        return self


StudyEvent = Annotated[
    StudyAttemptReservation | StudyAttemptUpdate | StudyManifestFreeze | StudyCellOutcome,
    Field(discriminator="kind"),
]


class StudyLedgerRecord(Message):
    event_id: Identifier
    sequence: Annotated[int, Field(ge=0, le=MAX_LEDGER_RECORDS - 1)]
    previous_sha256: Digest
    event: StudyEvent


class NativeStudyLedger(Message):
    schema_version: Literal["strange-physics.native-study-ledger.v1"] = (
        "strange-physics.native-study-ledger.v1"
    )
    plan: NativeAccountingPlan
    records: Annotated[tuple[StudyLedgerRecord, ...], Field(max_length=MAX_LEDGER_RECORDS)] = ()

    @model_validator(mode="after")
    def chain(self) -> Self:
        prior = message_sha256(self.plan)
        ids: set[str] = set()
        for index, record in enumerate(self.records):
            if record.sequence != index or record.previous_sha256 != prior:
                raise ValueError("Ledger sequence or canonical hash chain is broken")
            if record.event_id in ids:
                raise ValueError("A retained event identity may occur only once")
            ids.add(record.event_id)
            prior = message_sha256(record)
        return self


class NativeBudgetView(Message):
    purchased_slots: SafeCount
    remaining_slots: SafeCount
    charged_cpu_ns: SafeCount
    remaining_cpu_ns: SafeCount
    charged_artifact_bytes: SafeCount
    remaining_artifact_bytes: SafeCount
    unresolved_attempts: SafeCount
    over_limit: bool


class NativeCellSummary(Message):
    cell_id: Identifier
    status: Literal["unstarted", "in_progress", "complete", "failed", "incomplete", "cap_limited"]
    purchased_slots: SafeCount
    unresolved_attempts: SafeCount
    outcome: StudyCellOutcome | None


class NativeStudySummary(Message):
    study_id: Identifier
    accounting_plan_sha256: Digest
    ledger_sha256: Digest
    manifest_sha256: Digest | None
    budget: NativeBudgetView
    cells: Annotated[tuple[NativeCellSummary, ...], Field(max_length=36)]


def study_json_schema() -> JsonSchemaValue:
    roots: list[type[Message]] = [
        NativeAccountingPlan,
        NativeStudyManifest,
        NativeWorkFacts,
        NativeStudyLedger,
        NativeStudySummary,
    ]
    _, schema = models_json_schema(
        [(model, "validation") for model in roots],
        title="Native study interfaces and cumulative cost accounting v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["x-contract-status"] = "typed interface; complete ledger transitions pending"
    schema["x-canonical-profile"] = CANONICAL_PROFILE
    schema["x-owner-only-roots"] = [model.__name__ for model in roots]
    schema["description"] = (
        "Native comparison only. No providers, other study tracks or execution authority. "
        "Semantic joins and actual material/measurement producer checks remain required."
    )
    return schema
