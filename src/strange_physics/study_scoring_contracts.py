"""Owner-only actual-Journal/native-score evidence; never publication or authority."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Identifier, Message
from strange_physics.native_scoring_contracts import MAX_SCORING_INPUT_BYTES, NativeScoreResult
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.study_contracts import (
    MAX_LEDGER_RECORDS,
    NativeBudgetView,
    SafeCount,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)


class StudyMaterialIdentity(Message):
    """Actual received bytes and independently canonicalized typed message."""

    raw_sha256: Digest
    canonical_sha256: Digest
    byte_count: Annotated[int, Field(ge=1, le=MAX_SCORING_INPUT_BYTES)]


class StudyNativeAttemptEvidence(Message):
    role: Literal["candidate", "preparation", "prediction", "scoring"]
    probe_id: Identifier | None
    reservation: StudyAttemptReservation
    state: Literal["reserved", "running", "unknown", "completed", "failed", "rejected"]
    latest_update: StudyAttemptUpdate | None
    known_cpu_ns: SafeCount | None
    known_wall_ns: SafeCount | None
    known_artifact_bytes: SafeCount | None

    @model_validator(mode="after")
    def joins(self) -> Self:
        if (self.role == "prediction") != (self.probe_id is not None):
            raise ValueError("Only a prediction identifies its probe")
        operation = {
            "candidate": "candidate_production",
            "preparation": "preparation",
            "prediction": "prediction",
            "scoring": "scoring",
        }[self.role]
        if self.reservation.operation != operation or self.reservation.phase != "comparison":
            raise ValueError("Attempt scope differs from its actual native role")
        if self.latest_update is None:
            if self.state != "reserved" or any(
                v is not None
                for v in (self.known_cpu_ns, self.known_wall_ns, self.known_artifact_bytes)
            ):
                raise ValueError("Unstarted reservation has no fabricated measurements")
        else:
            update = self.latest_update
            if update.attempt_id != self.reservation.attempt_id or update.state != self.state:
                raise ValueError("Latest measurement belongs to another attempt or state")
            facts = update.facts
            if facts is not None and (
                facts.operation,
                facts.input_sha256,
                facts.config_sha256,
            ) != (
                self.reservation.operation,
                self.reservation.input_sha256,
                self.reservation.config_sha256,
            ):
                raise ValueError("Retained facts differ from their reservation")
            for known, latest in (
                (self.known_cpu_ns, update.cpu_ns),
                (self.known_wall_ns, update.wall_ns),
                (self.known_artifact_bytes, update.artifact_bytes),
            ):
                if latest is not None and known != latest:
                    raise ValueError("Known measurement must retain the latest nonnull value")
        return self


class StudyNativeScoreEvidence(Message):
    """Private bound material and accounting snapshot, never a complete cell receipt."""

    schema_version: Literal["strange-physics.study-native-score-evidence.v1"] = (
        "strange-physics.study-native-score-evidence.v1"
    )
    ledger_identity: StudyMaterialIdentity
    ledger_revision: Annotated[int, Field(ge=1, le=MAX_LEDGER_RECORDS)]
    accounting_plan_sha256: Digest
    manifest_sha256: Digest
    cell_id: Identifier
    journal_id: Identifier
    journal_raw_sha256: Digest
    observation_sha256: Digest
    scoring_input_identity: StudyMaterialIdentity
    scoring_result_identity: StudyMaterialIdentity
    score: NativeScoreResult
    attempts: Annotated[tuple[StudyNativeAttemptEvidence, ...], Field(min_length=27, max_length=27)]
    failed_purchase_operation_ids: Annotated[tuple[Identifier, ...], Field(max_length=12)]
    unresolved_cell_attempt_ids: Annotated[
        tuple[Identifier, ...], Field(max_length=MAX_LEDGER_RECORDS)
    ]
    budget: NativeBudgetView

    @model_validator(mode="after")
    def retained_identity(self) -> Self:
        if (
            self.scoring_result_identity.canonical_sha256 != message_sha256(self.score)
            or self.score.payload.input_sha256 != self.scoring_input_identity.canonical_sha256
            or self.score.payload.observation_sha256 != self.observation_sha256
        ):
            raise ValueError("Retained actual score and material identities differ")
        roles = tuple(item.role for item in self.attempts)
        if roles != ("candidate", "preparation", *("prediction",) * 24, "scoring"):
            raise ValueError("Every required native attempt must occur in role order")
        ids = tuple(item.reservation.attempt_id for item in self.attempts)
        if len(set(ids)) != 27 or any(
            item.reservation.cell_id != self.cell_id for item in self.attempts
        ):
            raise ValueError("Measured envelopes require distinct identities in the same cell")
        for values in (self.failed_purchase_operation_ids, self.unresolved_cell_attempt_ids):
            if len(set(values)) != len(values):
                raise ValueError("Retained operation and attempt identities must be unique")
        if any(
            item.reservation.attempt_id not in self.unresolved_cell_attempt_ids
            for item in self.attempts
            if item.state in {"reserved", "running", "unknown"}
        ):
            raise ValueError("Unresolved required work cannot disappear from accounting")
        score_update = self.attempts[-1].latest_update
        if (
            score_update is None
            or score_update.facts is None
            or self.attempts[-1].state not in {"completed", "failed", "rejected"}
            or message_sha256(score_update.facts) != message_sha256(self.score.facts)
            or self.budget.unresolved_attempts < len(self.unresolved_cell_attempt_ids)
        ):
            raise ValueError("Score measurements and unresolved accounting must remain explicit")
        bounded_canonical(self, MAX_SCORING_INPUT_BYTES)
        return self


STUDY_SCORING_MODELS: tuple[type[Message], ...] = (
    StudyMaterialIdentity,
    StudyNativeAttemptEvidence,
    StudyNativeScoreEvidence,
)


def study_scoring_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(m, "validation") for m in STUDY_SCORING_MODELS],
        title="Private actual-Journal native-score evidence",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-study-scoring.schema.json"
    schema["x-owner-only-roots"] = [m.__name__ for m in STUDY_SCORING_MODELS]
    schema["description"] = (
        "Evaluator-private material and cost evidence, including truth-derived hashes. "
        "Not execution authority, numerical authenticity, MAP proof or complete-cell publication."
    )
    return schema
