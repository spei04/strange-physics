"""Owner-local candidate execution contracts; no study or hosted authority."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.contracts import Identifier, Message
from strange_physics.research_contracts import Digest
from strange_physics.study_contracts import Commit, SafeCount

MIB = 1024**2
PrivatePath = Annotated[str, Field(min_length=1, max_length=4096)]
REQUEST_BYTES = 8192
STORE_ATTEMPTS_PER_TICKET = 4


class PublicationEscrow(Message):
    """Upper envelopes, not invented future materials or permission to publish."""

    calls: Annotated[int, Field(ge=0, le=40)]
    material_bytes: Annotated[int, Field(ge=0, le=64 * MIB)]
    journal_bytes: Annotated[int, Field(ge=0, le=32 * MIB)]
    ledger_bytes: Annotated[int, Field(ge=1, le=8 * MIB)]
    output_bytes: Annotated[int, Field(ge=64 * 1024, le=48 * MIB)]
    control_cpu_ns: SafeCount
    control_artifact_bytes: SafeCount
    work_cpu_ns: SafeCount

    def work_bytes_per_call(self) -> int:
        # Match both the publisher's material headroom and request minimum.
        return max(
            16 * MIB,
            4 * (self.material_bytes + self.journal_bytes + self.ledger_bytes + self.output_bytes)
            + 4 * MIB,
        )

    def required_bytes(self) -> int:
        return self.control_artifact_bytes + self.calls * self.work_bytes_per_call()

    @model_validator(mode="after")
    def publisher_floor(self) -> Self:
        if self.calls and self.work_bytes_per_call() > 512 * MIB:
            raise ValueError("Promised publication work exceeds the request ceiling")
        if self.calls and (
            self.control_artifact_bytes < self.calls * 16 * MIB + 16 * MIB
            or self.control_cpu_ns < self.calls * 1_000_000_000 + 1_000_000_000
            or self.work_cpu_ns < self.calls * 4_000_000_000
        ):
            raise ValueError("Publisher control/work floors must remain reserved")
        return self


class CandidateControl(Message):
    version: Literal["strange-physics.candidate-control.v1"] = (
        "strange-physics.candidate-control.v1"
    )
    root: PrivatePath
    plan_sha256: Digest
    source_commit: Commit
    uv_lock_sha256: Digest
    engine_fingerprint: Digest
    installation_sha256: Digest
    attempt_id: Identifier
    tickets: Annotated[int, Field(ge=1, le=3072)]
    recovery_tickets: Annotated[int, Field(ge=1, le=512)]
    recovery_work_cpu_ns: Annotated[int, Field(ge=4_000_000_000, le=120_000_000_000)]
    recovery_work_artifact_bytes: Annotated[int, Field(ge=256 * 1024, le=256 * MIB)]
    ticket_cpu_ns: Annotated[int, Field(ge=1_000_000_000, le=120_000_000_000)]
    ticket_wall_ns: Annotated[int, Field(ge=1_000_000_000, le=300_000_000_000)]
    ticket_artifact_bytes: Annotated[int, Field(ge=8192, le=32 * MIB)]
    bootstrap_artifact_bytes: Annotated[int, Field(ge=256 * 1024, le=32 * MIB)]
    bootstrap_cpu_ns: Annotated[int, Field(ge=1_000_000_000, le=600_000_000_000)]
    database_limit_bytes: Annotated[int, Field(ge=256 * 1024, le=24 * MIB)]
    finalization_records: Annotated[int, Field(ge=4, le=256)]
    finalization_bytes: Annotated[int, Field(ge=16 * 1024, le=2 * MIB)]
    publication: PublicationEscrow

    def database_envelope(self) -> int:
        return 2 * self.database_limit_bytes + self.database_limit_bytes // 512 + 2 * 65536

    def required_control_bytes(self) -> int:
        return self.bootstrap_artifact_bytes + self.tickets * (
            self.ticket_artifact_bytes + STORE_ATTEMPTS_PER_TICKET * self.database_envelope()
        )

    @model_validator(mode="after")
    def finite(self) -> Self:
        if self.recovery_tickets >= self.tickets:
            raise ValueError("Keep distinct finite normal and recovery tickets")
        if self.finalization_records < 2 * self.recovery_tickets + 2 + 3 * self.publication.calls:
            raise ValueError("Reserve recovery, stop and promised publication records")
        if self.finalization_bytes < 4096 * self.finalization_records:
            raise ValueError("Finalization records need a separate byte escrow")
        if (
            self.tickets * self.ticket_cpu_ns
            + self.bootstrap_cpu_ns
            + self.recovery_tickets * self.recovery_work_cpu_ns
            + self.publication.control_cpu_ns
            + self.publication.work_cpu_ns
            > 28_800_000_000_000
        ):
            raise ValueError("Control and protected future work CPU exceed the existing plan")
        if (
            self.required_control_bytes()
            + self.recovery_tickets * self.recovery_work_artifact_bytes
            + self.publication.required_bytes()
            > 1024 * MIB
        ):
            raise ValueError("Control and protected future artifacts exceed the existing plan")
        return self


class CandidateAdmission(Message):
    control: CandidateControl
    seed_ledger_sha256: Digest


class _ExecutionRequest(Message):
    mode: Literal["execute", "recover"]
    logical_id: Identifier
    attempt_id: Identifier
    retry_of: Identifier | None
    phase: Literal["reference", "calibration", "sensitivity", "comparison"]
    cell_id: Identifier | None
    ticket: Annotated[int, Field(ge=0, le=3071)]
    expected_revision: Annotated[int, Field(ge=0, le=8192)]
    expected_head_sha256: Digest
    input_path: PrivatePath
    input_raw_sha256: Digest
    input_bytes: Annotated[int, Field(ge=1, le=8 * MIB)]
    input_sha256: Digest
    config_sha256: Digest
    cpu_reservation_ns: Annotated[int, Field(ge=4_000_000_000, le=120_000_000_000)]
    artifact_reservation_bytes: Annotated[int, Field(ge=256 * 1024, le=256 * MIB)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=4 * MIB)]
    wall_limit_ns: Annotated[int, Field(ge=1_000_000_000, le=300_000_000_000)]

    @model_validator(mode="after")
    def scope(self) -> Self:
        if (self.phase == "comparison") != (self.cell_id is not None):
            raise ValueError("Only comparison names a cell")
        if self.mode == "recover" and self.retry_of is not None:
            raise ValueError("Recovery is accounting, not a numerical retry")
        return self


class CandidateRequest(_ExecutionRequest):
    operation: Literal["candidate_production"] = "candidate_production"


class _ExecutionReceipt(Message):
    logical_id: Identifier
    original_attempt_id: Identifier
    request_sha256: Digest
    original_revision: Annotated[int, Field(ge=0, le=8192)]
    original_head_sha256: Digest
    original_ledger_sha256: Digest
    input_raw_sha256: Digest
    result_raw_sha256: Digest
    source_commit: Commit
    installation_sha256: Digest


class CandidateReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.candidate-execution-receipt.v1"] = (
        "strange-physics.candidate-execution-receipt.v1"
    )


class CandidateMeasurements(Message):
    parent_cpu_ns: SafeCount
    child_cpu_ns: SafeCount
    wall_ns: SafeCount
    created_artifact_bytes: SafeCount
    control_parent_cpu_ns: SafeCount
    control_created_artifact_bytes: SafeCount
    final_tail: Literal["reserved-unresolved"] = "reserved-unresolved"
