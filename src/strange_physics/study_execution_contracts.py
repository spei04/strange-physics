"""Fixed private freeze and actual-Journal candidate interfaces."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from strange_physics.candidate_execution_contracts import (
    MIB,
    PrivatePath,
    _ExecutionReceipt,
    _ExecutionRequest,
)
from strange_physics.contracts import Identifier, Message
from strange_physics.native_spring_contracts import NativeCandidateInput
from strange_physics.research_contracts import Digest
from strange_physics.study_contracts import ArtifactKind, NativeStudyManifest, NativeWorkFacts


class NativeFreezeInput(Message):
    manifest: NativeStudyManifest
    artifacts: Annotated[dict[ArtifactKind, str], Field(min_length=1, max_length=32)]


class NativeFreezeRequest(Message):
    operation: Literal["freeze"] = "freeze"
    mode: Literal["execute", "recover"]
    logical_id: Identifier
    attempt_id: Identifier
    retry_of: Identifier | None
    phase: Literal["accounting"] = "accounting"
    cell_id: None = None
    ticket: Annotated[int, Field(ge=0, le=3071)]
    expected_revision: Annotated[int, Field(ge=0, le=8192)]
    expected_head_sha256: Digest
    input_path: PrivatePath
    input_raw_sha256: Digest
    input_bytes: Annotated[int, Field(ge=1, le=16 * MIB)]
    input_sha256: Digest
    config_sha256: Digest
    cpu_reservation_ns: Annotated[int, Field(ge=4_000_000_000, le=120_000_000_000)]
    artifact_reservation_bytes: Annotated[int, Field(ge=256 * 1024, le=256 * MIB)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=4 * MIB)]
    wall_limit_ns: Annotated[int, Field(ge=1_000_000_000, le=300_000_000_000)]

    @model_validator(mode="after")
    def recovery_scope(self) -> NativeFreezeRequest:
        if self.mode == "recover" and self.retry_of is not None:
            raise ValueError("Recovery is accounting, not a new freeze retry")
        return self


class NativeFreezeResult(Message):
    manifest_sha256: Digest
    facts: NativeWorkFacts


class NativeFreezeReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.native-freeze-receipt.v1"] = (
        "strange-physics.native-freeze-receipt.v1"
    )
    operation: Literal["freeze"] = "freeze"


class NativeComparisonInput(Message):
    """Private capture request; the numerical producer receives only candidate."""

    candidate: NativeCandidateInput
    freeze_logical_id: Identifier
    freeze_receipt_sha256: Digest
    journal_path: PrivatePath
    journal_sha256: Digest
    journal_bytes: Annotated[int, Field(ge=100, le=32 * MIB)]


class NativeComparisonCandidateRequest(_ExecutionRequest):
    operation: Literal["comparison_candidate"] = "comparison_candidate"
    phase: Literal["comparison"] = "comparison"
    cell_id: Identifier


class NativeComparisonReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.journal-candidate-receipt.v1"] = (
        "strange-physics.journal-candidate-receipt.v1"
    )
    operation: Literal["comparison_candidate"] = "comparison_candidate"
