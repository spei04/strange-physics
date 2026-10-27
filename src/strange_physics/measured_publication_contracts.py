"""Private measured-publication admission; these messages do not authorize a study."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.contracts import Identifier, Message
from strange_physics.research_contracts import Digest
from strange_physics.study_contracts import Commit, SafeCount

MIB = 1024**2
PrivatePath = Annotated[str, Field(min_length=1, max_length=4096)]


class PublicationControl(Message):
    version: Literal["strange-physics.publication-control.v1"] = (
        "strange-physics.publication-control.v1"
    )
    root: PrivatePath
    accounting_plan_sha256: Digest
    source_commit: Commit
    uv_lock_sha256: Digest
    attempt_id: Identifier
    tickets: Annotated[int, Field(ge=1, le=64)]
    ticket_cpu_ns: Annotated[int, Field(ge=1_000_000_000, le=120_000_000_000)]
    ticket_wall_ns: Annotated[int, Field(ge=1_000_000_000, le=300_000_000_000)]
    ticket_artifact_bytes: Annotated[int, Field(ge=16 * MIB, le=256 * MIB)]


class PublicationAdmission(Message):
    control: PublicationControl
    seed_ledger_sha256: Digest


class PublicationFile(Message):
    """Raw-byte identity. Paths are private local inputs, never executable names."""

    name: Annotated[str, Field(pattern=r"^[a-z_]+$", min_length=1, max_length=64)]
    path: PrivatePath
    sha256: Digest
    byte_count: Annotated[int, Field(ge=1, le=64 * MIB)]


class NativePublicationRequest(Message):
    mode: Literal["early", "scored"]
    event_id: Identifier
    cell_id: Identifier
    attempt_id: Identifier
    ticket: Annotated[int, Field(ge=0, le=63)]
    expected_revision: Annotated[int, Field(ge=0, le=8192)]
    expected_head_sha256: Digest
    journal_path: PrivatePath
    journal_sha256: Digest | None
    files: Annotated[tuple[PublicationFile, ...], Field(min_length=1, max_length=20)]
    diagnostic_attempt_id: Identifier | None = None
    cpu_reservation_ns: Annotated[int, Field(ge=4_000_000_000, le=120_000_000_000)]
    artifact_reservation_bytes: Annotated[int, Field(ge=16 * MIB, le=512 * MIB)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=48 * MIB)]
    wall_limit_ns: Annotated[int, Field(ge=1_000_000_000, le=300_000_000_000)]

    @model_validator(mode="after")
    def closed_inputs(self) -> Self:
        names = [item.name for item in self.files]
        if len(names) != len(set(names)) or sum(f.byte_count for f in self.files) > 64 * MIB:
            raise ValueError("Publication inputs must be unique and bounded")
        material = {
            "world_catalog",
            "candidate_config",
            "prediction_config",
            "pool",
            "scoring_policy",
            "classical_diagnostic_config",
        }
        extra = set(names) - material
        if self.mode == "early":
            if extra != {"witnesses"} or self.diagnostic_attempt_id is not None:
                raise ValueError("Early publication requires only its witnesses and materials")
        elif extra not in (
            {"scoring_input", "scoring_result"},
            {"scoring_input", "scoring_result", "diagnostic_result"},
            {"scoring_input", "scoring_result", "diagnostic_input", "diagnostic_result"},
        ):
            raise ValueError("Scored publication requires its fixed scoring inputs")
        if ("diagnostic_result" in names) and self.diagnostic_attempt_id is None:
            raise ValueError("A diagnostic result requires its retained attempt")
        return self


class PublicationMeasurements(Message):
    parent_cpu_ns: SafeCount
    child_cpu_ns: SafeCount
    wall_ns: SafeCount
    created_artifact_bytes: SafeCount
    control_parent_cpu_ns: SafeCount
    control_created_artifact_bytes: SafeCount
    final_tail: Literal["reserved-unresolved"] = "reserved-unresolved"
