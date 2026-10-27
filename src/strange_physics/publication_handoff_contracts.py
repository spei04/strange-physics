"""Versioned one-way ownership records; scientific and filesystem joins are separate.

These records never activate a publisher. The measured caller must authenticate
its retained materials and actual destination before committing the source seal.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.candidate_execution_contracts import MIB, CandidateAdmission
from strange_physics.contracts import Identifier, Message
from strange_physics.measured_publication_contracts import PublicationControl
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.study_contracts import (
    MAX_LEDGER_RECORDS,
    NativeStudyLedger,
    NativeWorkFacts,
    SafeCount,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_ledger import MAX_FINAL_RECORD_BYTES, StudyLedgerError, summarize_study

HANDOFF_INTENT_BYTES = 8192
HANDOFF_SEAL_BYTES = 64 * 1024
HANDOFF_PRODUCER = "strange-physics.execution-publisher-handoff.v1"


class HandoffReference(Message):
    logical_id: Identifier
    receipt_sha256: Digest


class PublicationHandoffIntent(Message):
    schema_version: Literal["strange-physics.publication-handoff-intent.v1"] = (
        "strange-physics.publication-handoff-intent.v1"
    )
    transfer_id: Identifier
    source_admission_sha256: Digest
    cell_id: Identifier
    scoring: HandoffReference
    diagnostic: HandoffReference
    destination: PublicationControl
    destination_device: SafeCount
    destination_inode: Annotated[int, Field(ge=1, le=2**53 - 1)]

    @model_validator(mode="after")
    def single_destination(self) -> Self:
        path = PurePosixPath(self.destination.root)
        if not path.is_absolute() or str(path) != self.destination.root or ".." in path.parts:
            raise ValueError("Handoff destination requires an absolute normalized path")
        if self.destination.tickets != 3:
            raise ValueError("Handoff supports publish, original replay and one recovery spare")
        if self.scoring.logical_id == self.diagnostic.logical_id:
            raise ValueError("Native scoring and the original diagnostic are distinct closures")
        bounded_canonical(self, HANDOFF_INTENT_BYTES)
        return self


class PublicationHandoffSeal(Message):
    schema_version: Literal["strange-physics.publication-handoff-seal.v1"] = (
        "strange-physics.publication-handoff-seal.v1"
    )
    intent: PublicationHandoffIntent
    source_admission: CandidateAdmission
    transfer_attempt_id: Identifier
    bundle_sha256: Digest
    sealed_revision: Annotated[int, Field(ge=3, le=MAX_LEDGER_RECORDS)]
    sealed_head_sha256: Digest
    seed_ledger_sha256: Digest
    seed_ledger_bytes: Annotated[int, Field(ge=1, le=8 * MIB)]

    @model_validator(mode="after")
    def authority(self) -> Self:
        source = self.source_admission.control
        target = self.intent.destination
        escrow = source.publication
        if (
            message_sha256(self.source_admission) != self.intent.source_admission_sha256
            or target.root == source.root
            or target.accounting_plan_sha256 != source.plan_sha256
            or target.source_commit != source.source_commit
            or target.uv_lock_sha256 != source.uv_lock_sha256
            or target.attempt_id in {source.attempt_id, self.transfer_attempt_id}
            or escrow.calls != target.tickets
            or escrow.control_cpu_ns < target.tickets * target.ticket_cpu_ns + 1_000_000_000
            or escrow.control_artifact_bytes
            < target.tickets * target.ticket_artifact_bytes + 16 * MIB
        ):
            raise ValueError("Handoff source, destination or prepaid control allowance differs")
        bounded_canonical(self, HANDOFF_SEAL_BYTES)
        return self


def read_handoff_seal(data: bytes) -> PublicationHandoffSeal:
    return parse_bounded_json(
        data, PublicationHandoffSeal, max_bytes=HANDOFF_SEAL_BYTES, max_depth=8, max_nodes=512
    )


def handoff_control_hold(seal: PublicationHandoffSeal) -> StudyAttemptReservation:
    """Convert promised publisher control into one actual unresolved reservation."""
    target = seal.intent.destination
    escrow = seal.source_admission.control.publication
    return StudyAttemptReservation(
        attempt_id=target.attempt_id,
        phase="accounting",
        cell_id=None,
        operation="accounting",
        config_sha256=message_sha256(target),
        input_sha256=target.accounting_plan_sha256,
        retry_of=None,
        cpu_reservation_ns=escrow.control_cpu_ns,
        artifact_reservation_bytes=escrow.control_artifact_bytes,
        purchase=None,
    )


def validate_handoff_ledger(seal: PublicationHandoffSeal, ledger: NativeStudyLedger) -> None:
    """Check the sealed seed and exact accounting tail, without asserting material truth."""
    source = seal.source_admission.control
    target = seal.intent.destination
    escrow = source.publication
    ledger_digest, ledger_bytes = bounded_canonical(ledger, escrow.ledger_bytes)
    if (
        len(ledger.records) != seal.sealed_revision
        or message_sha256(ledger.records[-1]) != seal.sealed_head_sha256
        or (ledger_digest, ledger_bytes) != (seal.seed_ledger_sha256, seal.seed_ledger_bytes)
        or message_sha256(ledger.plan) != source.plan_sha256
    ):
        raise StudyLedgerError("candidate_handoff_seed")
    reservation, update, hold = (record.event for record in ledger.records[-3:])
    if (
        not isinstance(reservation, StudyAttemptReservation)
        or reservation.attempt_id != seal.transfer_attempt_id
        or reservation.phase != "accounting"
        or reservation.cell_id is not None
        or reservation.operation != "accounting"
        or reservation.config_sha256 != message_sha256(target)
        or reservation.input_sha256 != message_sha256(seal.intent)
        or reservation.retry_of is not None
        or reservation.purchase is not None
        or not isinstance(update, StudyAttemptUpdate)
        or update.attempt_id != reservation.attempt_id
        or update.state != "completed"
        or update.cpu_ns is None
        or update.cpu_ns > reservation.cpu_reservation_ns
        or update.artifact_bytes is None
        or update.artifact_bytes > reservation.artifact_reservation_bytes
        or update.wall_ns is None
        or update.facts
        != NativeWorkFacts(
            attempt_id=reservation.attempt_id,
            operation="accounting",
            producer_version=HANDOFF_PRODUCER,
            config_sha256=reservation.config_sha256,
            input_sha256=reservation.input_sha256,
            observation_sha256=None,
            model_sha256=None,
            output_sha256=seal.bundle_sha256,
            unit="work",
            requested_count=1,
            completed_count=1,
            failed_count=0,
            not_assessed_count=0,
            outcome="completed",
        )
        or hold != handoff_control_hold(seal)
    ):
        raise StudyLedgerError("candidate_handoff_accounting")
    # The old finite source control remains charged. A seal cannot manufacture
    # capacity by settling it or any unrelated setup/unknown attempt in its tail.
    source_holds = [
        record.event
        for record in ledger.records
        if isinstance(record.event, StudyAttemptReservation | StudyAttemptUpdate)
        and record.event.attempt_id == source.attempt_id
    ]
    if len(source_holds) != 1 or not isinstance(source_holds[0], StudyAttemptReservation):
        raise StudyLedgerError("candidate_handoff_source_hold")
    source_hold = source_holds[0]
    if (
        (
            source_hold.phase,
            source_hold.cell_id,
            source_hold.operation,
            source_hold.config_sha256,
            source_hold.input_sha256,
            source_hold.retry_of,
            source_hold.purchase,
        )
        != (
            "accounting",
            None,
            "accounting",
            message_sha256(source),
            source.plan_sha256,
            None,
            None,
        )
        or source_hold.cpu_reservation_ns
        < source.bootstrap_cpu_ns + source.tickets * source.ticket_cpu_ns
        or source_hold.artifact_reservation_bytes < source.required_control_bytes()
    ):
        raise StudyLedgerError("candidate_handoff_source_hold")
    summary = summarize_study(ledger)
    if seal.intent.cell_id not in {cell.cell_id for cell in summary.cells}:
        raise StudyLedgerError("candidate_handoff_cell")
    # Publisher control is already charged by the final reservation. Protect
    # only its remaining work plus the original source recovery allowance here.
    budget = summary.budget
    if (
        budget.over_limit
        or budget.remaining_cpu_ns
        < escrow.work_cpu_ns + source.recovery_tickets * source.recovery_work_cpu_ns
        or budget.remaining_artifact_bytes
        < escrow.calls * escrow.work_bytes_per_call()
        + source.recovery_tickets * source.recovery_work_artifact_bytes
        or len(ledger.records) + budget.unresolved_attempts + source.finalization_records
        > MAX_LEDGER_RECORDS
        or ledger_bytes
        + budget.unresolved_attempts * MAX_FINAL_RECORD_BYTES
        + source.finalization_bytes
        > escrow.ledger_bytes
    ):
        raise StudyLedgerError("candidate_handoff_headroom")
