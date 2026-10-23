"""Evaluator-private publication evidence and receipts; no execution authority."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Identifier, Message
from strange_physics.native_classical_contracts import ClassicalDiagnosticResult
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.study_contracts import (
    MAX_LEDGER_RECORDS,
    MAX_PUBLICATION_BYTES,
    SafeCount,
    StudyAttemptReservation,
    StudyAttemptUpdate,
    StudyCellOutcome,
    StudyLedgerRecord,
    StudyPublicationEvent,
)
from strange_physics.study_scoring_contracts import StudyMaterialIdentity, StudyNativeScoreEvidence


class StudyDiagnosticAttempt(Message):
    reservation: StudyAttemptReservation
    state: Literal["reserved", "running", "unknown", "completed", "failed", "rejected"]
    latest_update: StudyAttemptUpdate | None
    known_cpu_ns: SafeCount | None
    known_wall_ns: SafeCount | None
    known_artifact_bytes: SafeCount | None

    @model_validator(mode="after")
    def snapshot(self) -> Self:
        r, u = self.reservation, self.latest_update
        if r.operation != "classical_diagnostic" or r.phase != "comparison":
            raise ValueError("Diagnostic uses its own frozen comparison envelope")
        if u is None:
            if self.state != "reserved" or any(
                v is not None
                for v in (self.known_cpu_ns, self.known_wall_ns, self.known_artifact_bytes)
            ):
                raise ValueError("Unstarted diagnostic cannot invent measurements")
        else:
            if u.attempt_id != r.attempt_id or u.state != self.state:
                raise ValueError("Diagnostic update identity/state differs")
            if u.facts is not None and (
                u.facts.operation,
                u.facts.config_sha256,
                u.facts.input_sha256,
            ) != (r.operation, r.config_sha256, r.input_sha256):
                raise ValueError("Diagnostic facts differ from the actual reservation")
            for known, latest in (
                (self.known_cpu_ns, u.cpu_ns),
                (self.known_wall_ns, u.wall_ns),
                (self.known_artifact_bytes, u.artifact_bytes),
            ):
                if latest is not None and known != latest:
                    raise ValueError("Retain the latest nonnull diagnostic measurements")
        return self


class StudyPublicationEvidence(Message):
    """Original pre-append evidence. Never contains its event or receipt hash."""

    schema_version: Literal["strange-physics.study-publication-evidence.v1"] = (
        "strange-physics.study-publication-evidence.v1"
    )
    native: StudyNativeScoreEvidence
    diagnostic_config_identity: StudyMaterialIdentity
    diagnostic_input_sha256: Digest
    diagnostic_attempt: StudyDiagnosticAttempt | None
    diagnostic_result_identity: StudyMaterialIdentity | None
    diagnostic_result: ClassicalDiagnosticResult | None
    outcome: StudyCellOutcome

    @model_validator(mode="after")
    def joins(self) -> Self:
        n, a, r = self.native, self.diagnostic_attempt, self.diagnostic_result
        if self.outcome.cell_id != n.cell_id or self.outcome.journal_id != n.journal_id:
            raise ValueError("Publication outcome belongs to its original native evidence")
        if (r is None) != (self.diagnostic_result_identity is None):
            raise ValueError("Retained result and actual-byte identity are inseparable")
        if a is not None and (
            a.reservation.cell_id != n.cell_id
            or a.reservation.input_sha256 != self.diagnostic_input_sha256
            or a.reservation.config_sha256 != self.diagnostic_config_identity.canonical_sha256
            or a.reservation.attempt_id in {x.reservation.attempt_id for x in n.attempts}
        ):
            raise ValueError("Diagnostic must be a separate actual same-cell envelope")
        if r is not None:
            assert self.diagnostic_result_identity is not None
            if (
                a is None
                or a.latest_update is None
                or a.latest_update.facts is None
                or a.state not in {"completed", "failed", "rejected"}
                or message_sha256(a.latest_update.facts) != message_sha256(r.facts)
                or message_sha256(r) != self.diagnostic_result_identity.canonical_sha256
                or r.payload.input_sha256 != self.diagnostic_input_sha256
                or r.payload.config_sha256 != self.diagnostic_config_identity.canonical_sha256
                or r.payload.observation_sha256 != n.observation_sha256
            ):
                raise ValueError("Diagnostic result requires exact terminal measured facts")
        elif a is not None and a.state in {"completed", "failed", "rejected"}:
            raise ValueError("Terminal diagnostic cannot omit its retained result")
        e = n.score.payload.evaluation
        if (
            self.outcome.observation_sha256 != n.observation_sha256
            or self.outcome.model_sha256 != n.score.payload.model_sha256
            or self.outcome.report_sha256 != (None if e is None else e.report_sha256)
            or self.outcome.protocol_sha256
            != (None if e is None else e.diagnostics.protocol_sha256)
            or self.outcome.scoring_policy_sha256 != n.score.payload.policy_sha256
        ):
            raise ValueError("Primary publication retains its actual native result identities")
        unresolved = bool(n.unresolved_cell_attempt_ids) or r is None
        if unresolved:
            cap = (
                n.budget.over_limit
                or n.budget.remaining_cpu_ns == 0
                or n.budget.remaining_artifact_bytes == 0
            )
            pair = ("cap_limited", "resource_limit") if cap else ("incomplete", "interrupted")
        elif e is not None and e.status == "scored":
            pair = ("complete", "scored")
        elif e is not None and e.status == "unscorable":
            pair = ("failed", "unscorable")
        else:
            pair = ("failed", "execution_failure")
        if (self.outcome.status, self.outcome.reason) != pair:
            raise ValueError(
                "Publication status must preserve primary and unresolved cost evidence"
            )
        bounded_canonical(self, MAX_PUBLICATION_BYTES)
        return self


class StudyPublicationReceipt(Message):
    """Original append identity; neither a durable write receipt nor scientific approval."""

    schema_version: Literal["strange-physics.study-publication-receipt.v1"] = (
        "strange-physics.study-publication-receipt.v1"
    )
    event_id: Identifier
    original_ledger_identity: StudyMaterialIdentity
    original_revision: Annotated[int, Field(ge=1, le=MAX_LEDGER_RECORDS - 1)]
    original_head_sha256: Digest
    event: StudyPublicationEvent
    record_sha256: Digest
    resulting_ledger_sha256: Digest

    @model_validator(mode="after")
    def record_identity(self) -> Self:
        record = StudyLedgerRecord(
            event_id=self.event_id,
            sequence=self.original_revision,
            previous_sha256=self.original_head_sha256,
            event=self.event,
        )
        if message_sha256(record) != self.record_sha256:
            raise ValueError("Receipt must bind the exact resulting publication record")
        return self


def parse_study_publication_evidence(raw: bytes) -> StudyPublicationEvidence:
    return parse_bounded_json(
        raw,
        StudyPublicationEvidence,
        max_bytes=MAX_PUBLICATION_BYTES,
        max_depth=40,
        max_nodes=2_000_000,
    )


PUBLICATION_MODELS: tuple[type[Message], ...] = (
    StudyDiagnosticAttempt,
    StudyPublicationEvidence,
    StudyPublicationReceipt,
)


def study_publication_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(m, "validation") for m in PUBLICATION_MODELS],
        title="Private native/classical publication composition",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-study-publication.schema.json"
    schema["x-owner-only-roots"] = [m.__name__ for m in PUBLICATION_MODELS]
    schema["description"] = (
        "Evaluator-private evidence, truth-derived hashes and pure append proposals. "
        "No durable persistence, measured execution, MAP or scientific gate authority."
    )
    return schema
