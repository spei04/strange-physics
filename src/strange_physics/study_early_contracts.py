"""Private available-stage witnesses and no-score evidence, never execution authority."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Identifier, Message, ObservationBundle
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticInput,
    ClassicalDiagnosticResult,
)
from strange_physics.native_prediction_contracts import NativePredictionResult
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativePreparationResult
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeCandidateResult,
    SelectedNativeCandidate,
)
from strange_physics.research_contracts import Digest
from strange_physics.study_contracts import (
    MAX_LEDGER_RECORDS,
    MAX_PUBLICATION_BYTES,
    NativeBudgetView,
    SafeCount,
    StudyAttemptReservation,
    StudyAttemptUpdate,
    StudyCellOutcome,
)
from strange_physics.study_scoring_contracts import StudyMaterialIdentity

MAX_EARLY_WITNESS_BYTES = 16 * 1024 * 1024


class EarlyCandidateWitness(Message):
    kind: Literal["candidate"] = "candidate"
    actual_input: NativeCandidateInput
    result: NativeCandidateResult


class EarlySelectionWitness(Message):
    kind: Literal["selection"] = "selection"
    candidate_attempt_id: Identifier
    selected: SelectedNativeCandidate


class EarlyPreparationWitness(Message):
    kind: Literal["preparation"] = "preparation"
    actual_input: NativeEvaluationInput
    result: NativePreparationResult


class EarlyPredictionWitness(Message):
    kind: Literal["prediction"] = "prediction"
    preparation_attempt_id: Identifier
    attempt_id: Identifier
    probe_id: Identifier
    transport: Literal["result", "missing", "invalid"]
    result: NativePredictionResult | None

    @model_validator(mode="after")
    def result_presence(self) -> Self:
        if (self.transport == "result") != (self.result is not None):
            raise ValueError("Only result transport contains a typed actual prediction")
        return self


class EarlyDiagnosticWitness(Message):
    kind: Literal["classical_diagnostic"] = "classical_diagnostic"
    actual_input: ClassicalDiagnosticInput
    result: ClassicalDiagnosticResult


EarlyStageWitness = Annotated[
    EarlyCandidateWitness
    | EarlySelectionWitness
    | EarlyPreparationWitness
    | EarlyPredictionWitness
    | EarlyDiagnosticWitness,
    Field(discriminator="kind"),
]


class StudyEarlyWitnesses(Message):
    schema_version: Literal["strange-physics.study-early-witnesses.v1"] = (
        "strange-physics.study-early-witnesses.v1"
    )
    stages: Annotated[tuple[EarlyStageWitness, ...], Field(max_length=MAX_LEDGER_RECORDS)]

    @model_validator(mode="after")
    def bounded(self) -> Self:
        bounded_canonical(self, MAX_EARLY_WITNESS_BYTES)
        return self


class StudyEarlyAttempt(Message):
    """Complete cell accounting projection, including unselected retries."""

    reservation: StudyAttemptReservation
    state: Literal["reserved", "running", "unknown", "completed", "failed", "rejected"]
    latest_update: StudyAttemptUpdate | None
    known_cpu_ns: SafeCount | None
    known_wall_ns: SafeCount | None
    known_artifact_bytes: SafeCount | None

    @model_validator(mode="after")
    def joins(self) -> Self:
        r, u = self.reservation, self.latest_update
        if r.phase != "comparison":
            raise ValueError("Cell evidence retains comparison attempts only")
        if u is None:
            if self.state != "reserved" or any(
                v is not None
                for v in (self.known_cpu_ns, self.known_wall_ns, self.known_artifact_bytes)
            ):
                raise ValueError("Unstarted work cannot invent measurements")
        else:
            if u.attempt_id != r.attempt_id or u.state != self.state:
                raise ValueError("Update belongs to another attempt/state")
            if u.facts is not None and (
                u.facts.operation,
                u.facts.input_sha256,
                u.facts.config_sha256,
            ) != (r.operation, r.input_sha256, r.config_sha256):
                raise ValueError("Facts differ from the reservation")
            for known, latest in (
                (self.known_cpu_ns, u.cpu_ns),
                (self.known_wall_ns, u.wall_ns),
                (self.known_artifact_bytes, u.artifact_bytes),
            ):
                if latest is not None and known != latest:
                    raise ValueError("Retain all latest nonnull measurements")
        return self


class StudyEarlyMaterial(Message):
    kind: Literal[
        "world_catalog",
        "pool",
        "candidate_config",
        "prediction_config",
        "scoring_policy",
        "classical_diagnostic_config",
    ]
    identity: StudyMaterialIdentity


class StudyEarlyPurchaseRow(Message):
    operation_id: Identifier
    ordinal: Annotated[int, Field(ge=0, le=11)]
    experiment_sha256: Digest
    record_sha256: Digest | None
    status: Literal["pending", "completed", "failed"]

    @model_validator(mode="after")
    def presence(self) -> Self:
        if (self.status == "pending") != (self.record_sha256 is None):
            raise ValueError("Pending rows have no invented record")
        return self


EarlyStage = Literal[
    "unstarted",
    "purchases",
    "candidate_unavailable",
    "selection_unavailable",
    "preparation_unavailable",
    "preparation_rejected",
    "predictions_unavailable",
    "scoring_unavailable",
    "material_recovery",
]


class StudyEarlyEvidence(Message):
    """Owner/evaluator-only original evidence; never a numerical or MAP proof."""

    schema_version: Literal["strange-physics.study-early-evidence.v1"] = (
        "strange-physics.study-early-evidence.v1"
    )
    ledger_identity: StudyMaterialIdentity
    ledger_revision: Annotated[int, Field(ge=1, le=MAX_LEDGER_RECORDS)]
    accounting_plan_sha256: Digest
    manifest_sha256: Digest
    cell_id: Identifier
    journal_id: Identifier
    journal_raw_sha256: Digest | None
    current_prefix: ObservationBundle | None
    reserved_slots: Annotated[int, Field(ge=0, le=12)]
    journal_rows: Annotated[tuple[StudyEarlyPurchaseRow, ...], Field(max_length=12)]
    pending_operation_ids: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    missing_reservation_ids: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    failed_operation_ids: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    materials: Annotated[tuple[StudyEarlyMaterial, ...], Field(min_length=5, max_length=6)]
    witnesses_identity: StudyMaterialIdentity
    witnesses: StudyEarlyWitnesses
    attempts: Annotated[tuple[StudyEarlyAttempt, ...], Field(max_length=MAX_LEDGER_RECORDS)]
    missing_result_attempt_ids: Annotated[
        tuple[Identifier, ...], Field(max_length=MAX_LEDGER_RECORDS)
    ]
    historical_attempt_ids: Annotated[tuple[Identifier, ...], Field(max_length=MAX_LEDGER_RECORDS)]
    stage: EarlyStage
    budget: NativeBudgetView
    outcome: StudyCellOutcome

    @model_validator(mode="after")
    def joins(self) -> Self:
        if (self.journal_raw_sha256 is None) != (self.current_prefix is None):
            raise ValueError("An absent Journal has no invented prefix")
        if len(self.journal_rows) > self.reserved_slots:
            raise ValueError("Journal rows cannot exceed charged intents")
        if self.outcome.cell_id != self.cell_id or self.outcome.journal_id != self.journal_id:
            raise ValueError("Outcome scope differs from actual evidence")
        if self.outcome.status == "complete" or self.outcome.report_sha256 is not None:
            raise ValueError("Available scores require the scored publication boundary")
        ids = [a.reservation.attempt_id for a in self.attempts]
        if len(set(ids)) != len(ids) or any(
            a.reservation.cell_id != self.cell_id for a in self.attempts
        ):
            raise ValueError("Retain distinct same-cell accounting envelopes")
        if not set(self.missing_result_attempt_ids) <= set(ids) or not set(
            self.historical_attempt_ids
        ) <= set(ids):
            raise ValueError("Missing/historical material must name an actual attempt")
        if len({m.kind for m in self.materials}) != len(self.materials):
            raise ValueError("Material roles must be unique")
        bounded_canonical(self, MAX_PUBLICATION_BYTES)
        return self


def parse_study_early_witnesses(raw: bytes) -> StudyEarlyWitnesses:
    return parse_bounded_json(
        raw,
        StudyEarlyWitnesses,
        max_bytes=MAX_EARLY_WITNESS_BYTES,
        max_depth=40,
        max_nodes=2_000_000,
    )


def parse_study_early_evidence(raw: bytes) -> StudyEarlyEvidence:
    return parse_bounded_json(
        raw,
        StudyEarlyEvidence,
        max_bytes=MAX_PUBLICATION_BYTES,
        max_depth=40,
        max_nodes=2_000_000,
    )


EARLY_MODELS: tuple[type[Message], ...] = (StudyEarlyWitnesses, StudyEarlyEvidence)


def study_early_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(m, "validation") for m in EARLY_MODELS], title="Private study early-stop evidence v1"
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-study-early.schema.json"
    schema["x-private-roots"] = [m.__name__ for m in EARLY_MODELS]
    schema["description"] = (
        "Owner/evaluator-only witnesses and evidence. No selector audience, execution, "
        "measurement authenticity, MAP, or scientific readiness is asserted by parsing."
    )
    return schema
