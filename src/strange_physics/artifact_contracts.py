"""Artifact and checkpoint messages; trusted storage projections are not public inputs."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Checkpoint, Identifier, Message
from strange_physics.control_contracts import CheckpointBinding
from strange_physics.research_contracts import Digest, message_sha256

Number = Annotated[int, Field(strict=True, ge=0, le=2**53 - 1)]
Index = Annotated[int, Field(strict=True, ge=-1, le=9_999)]
Generation = Annotated[
    str,
    Field(
        min_length=1,
        max_length=20,
        pattern=r"^[1-9][0-9]{0,19}$",
        json_schema_extra={"not": {"pattern": "[^0-9]"}},
    ),
]
MediaType = Annotated[
    str,
    Field(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$",
        json_schema_extra={"not": {"pattern": "[^a-z0-9!#$&^_.+/-]"}},
    ),
]
Visibility = Literal["agent-visible", "workspace-private", "evaluator-only", "public"]


class ArtifactRef(Message):
    """Public immutable object-version identity; neither location nor access authority."""

    artifact_id: Identifier
    generation: Generation
    sha256: Digest
    size_bytes: Number
    media_type: MediaType


class ArtifactPolicy(Message):
    """Required versioned bounds. Values are deployment policy, not production defaults."""

    policy_id: Identifier
    max_envelope_bytes: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]
    max_state_depth: Annotated[int, Field(strict=True, ge=1, le=64)]
    max_state_nodes: Annotated[int, Field(strict=True, ge=1, le=1_000_000)]
    max_artifacts: Annotated[int, Field(strict=True, ge=0, le=128)]
    max_artifact_bytes: Number
    max_total_artifact_bytes: Number
    allowed_media_types: Annotated[tuple[MediaType, ...], Field(min_length=1, max_length=32)]

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if tuple(sorted(set(self.allowed_media_types))) != self.allowed_media_types:
            raise ValueError("Media types must be unique and sorted")
        return self


class StorageLocator(Message):
    """Private configured namespace and server-assigned key; no client URL or credentials."""

    provider: Literal["gcs"]
    namespace_id: Identifier
    object_key: Annotated[
        str,
        Field(
            min_length=1,
            max_length=512,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_./-]*$",
            json_schema_extra={"not": {"pattern": "[^A-Za-z0-9_./-]"}},
        ),
    ]

    @model_validator(mode="after")
    def safe_key(self) -> Self:
        if any(part in {"", ".", ".."} for part in self.object_key.split("/")):
            raise ValueError("Object key must contain only nonempty canonical path segments")
        return self


class RunArtifactRecord(Message):
    """Current tenant/run catalog row; producer establishes currency and namespace ownership."""

    workspace_id: Identifier
    run_id: Identifier
    ref: ArtifactRef
    locator: StorageLocator
    visibility: Visibility
    state: Literal["uploading", "available", "tombstoned", "deleted"]
    revision: Number
    created_at: Number


class ObjectVerification(Message):
    """Trusted complete stored-byte readback, not object user metadata or a client claim.

    The producer verifies the entire raw byte stream at this exact generation,
    with transport checksum validation where supported. This message does not do I/O.
    """

    verification_id: Identifier
    verifier_id: Identifier
    locator: StorageLocator
    generation: Generation
    sha256: Digest
    size_bytes: Number
    media_type: MediaType
    observed_at: Number
    completeness: Literal["complete"]


class VerifiedArtifact(Message):
    record: RunArtifactRecord
    verification: ObjectVerification

    @model_validator(mode="after")
    def bound(self) -> Self:
        ref, proof = self.record.ref, self.verification
        if (
            self.record.locator != proof.locator
            or ref.generation != proof.generation
            or ref.sha256 != proof.sha256
            or ref.size_bytes != proof.size_bytes
            or ref.media_type != proof.media_type
            or proof.observed_at < self.record.created_at
        ):
            raise ValueError("Verification must bind the exact catalog object and complete bytes")
        return self


class CheckpointRequest(Message):
    """Existing public body with the ART v1 reference definition; CORE is unchanged."""

    checkpoint: Checkpoint
    runtime_image_sha256: Digest
    artifacts: Annotated[tuple[ArtifactRef, ...], Field(max_length=128)]

    @model_validator(mode="after")
    def unique_refs(self) -> Self:
        if len({ref.artifact_id for ref in self.artifacts}) != len(self.artifacts):
            raise ValueError("Checkpoint artifacts must have unique logical artifact IDs")
        return self


class CheckpointArtifacts(Message):
    """Current verified ref list for exactly one normalized full request and policy."""

    workspace_id: Identifier
    run_id: Identifier
    request_sha256: Digest
    policy_sha256: Digest
    checked_at: Number
    objects: Annotated[tuple[VerifiedArtifact, ...], Field(max_length=128)]

    @model_validator(mode="after")
    def ordered_scope(self) -> Self:
        ids = tuple(item.record.ref.artifact_id for item in self.objects)
        if len(set(ids)) != len(ids):
            raise ValueError("Verified artifact list cannot repeat a logical artifact")
        for item in self.objects:
            if (
                item.record.workspace_id != self.workspace_id
                or item.record.run_id != self.run_id
                or item.verification.observed_at > self.checked_at
            ):
                raise ValueError("Verification batch must bind one tenant/run and observation time")
        return self


class CheckpointAttempt(Message):
    """Trusted pinned attempt identity/configuration from the current authorized run."""

    workspace_id: Identifier
    run_id: Identifier
    attempt_id: Identifier
    lease_epoch: Number
    binding: CheckpointBinding


class CheckpointRecord(Message):
    """Immutable committed history; its entire verified snapshot is retained privately."""

    workspace_id: Identifier
    run_id: Identifier
    index: Index
    request: CheckpointRequest
    request_sha256: Digest
    binding: CheckpointBinding
    artifacts: CheckpointArtifacts
    attempt_id: Identifier
    lease_epoch: Number
    run_revision: Number
    checkpoint_revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
    committed_at: Number

    @model_validator(mode="after")
    def bound(self) -> Self:
        if (
            self.index != self.request.checkpoint.through_index
            or self.request_sha256 != message_sha256(self.request)
            or self.request.checkpoint.agent_id != self.binding.agent_id
            or self.request.runtime_image_sha256 != self.binding.runtime_image_sha256
            or (self.artifacts.workspace_id, self.artifacts.run_id)
            != (self.workspace_id, self.run_id)
            or self.artifacts.request_sha256 != self.request_sha256
            or self.artifacts.checked_at != self.committed_at
            or tuple(item.record.ref for item in self.artifacts.objects) != self.request.artifacts
            or any(
                item.record.state != "available" or item.record.visibility != "agent-visible"
                for item in self.artifacts.objects
            )
        ):
            raise ValueError("Checkpoint must bind request, runtime and complete ref list")
        return self


class CheckpointHead(Message):
    """Latest immutable checkpoint pointer, changed only by an atomic checkpoint commit."""

    index: Index
    request_sha256: Digest
    checkpoint_revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]


class CheckpointOutbox(Message):
    """Retained dispatch identity; delivery state cannot replace this committed projection."""

    event_id: Identifier
    workspace_id: Identifier
    run_id: Identifier
    index: Index
    request_sha256: Digest
    checkpoint_revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
    record_sha256: Digest


class CheckpointLookup(Message):
    """Bounded target and latest committed closures, under the same run lock.

    Missing target or latest record/outbox projections permit explicit recovery failure.
    Producers establish completeness, absence and currency; parsing proves none of them.
    """

    workspace_id: Identifier
    run_id: Identifier
    index: Index
    revision: Number
    head: CheckpointHead | None
    record: CheckpointRecord | None
    outbox: CheckpointOutbox | None
    latest_record: CheckpointRecord | None
    latest_outbox: CheckpointOutbox | None


class CheckpointCommitPlan(Message):
    """Pure all-or-nothing proposal; success is not proof of a storage or SQL commit."""

    expected_checkpoint_revision: Number
    record: CheckpointRecord
    head: CheckpointHead
    outbox: CheckpointOutbox

    @model_validator(mode="after")
    def atomic(self) -> Self:
        record, head, outbox = self.record, self.head, self.outbox
        if (
            record.checkpoint_revision != self.expected_checkpoint_revision + 1
            or head.index != record.index
            or head.request_sha256 != record.request_sha256
            or head.checkpoint_revision != record.checkpoint_revision
            or (outbox.workspace_id, outbox.run_id, outbox.index)
            != (record.workspace_id, record.run_id, record.index)
            or outbox.request_sha256 != record.request_sha256
            or outbox.checkpoint_revision != record.checkpoint_revision
            or outbox.record_sha256 != message_sha256(record)
        ):
            raise ValueError("Atomic checkpoint proposal must bind history, pointer and outbox")
        return self


class CheckpointReplay(Message):
    """Authorized metadata/body replay; does not move the latest pointer or charge resources."""

    request: CheckpointRequest
    request_sha256: Digest

    @model_validator(mode="after")
    def bound(self) -> Self:
        if self.request_sha256 != message_sha256(self.request):
            raise ValueError("Replay must return its exact original request")
        return self


ARTIFACT_MODELS: tuple[type[Message], ...] = (
    ArtifactRef,
    ArtifactPolicy,
    StorageLocator,
    RunArtifactRecord,
    ObjectVerification,
    VerifiedArtifact,
    CheckpointRequest,
    CheckpointArtifacts,
    CheckpointAttempt,
    CheckpointRecord,
    CheckpointHead,
    CheckpointOutbox,
    CheckpointLookup,
    CheckpointCommitPlan,
    CheckpointReplay,
)
PUBLIC_MODELS: tuple[type[Message], ...] = (ArtifactRef, CheckpointRequest)


def artifact_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in ARTIFACT_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/artifacts.schema.json"
    schema["x-contract-status"] = "ART1 API review; no runtime acceptance or SP-01.c freeze"
    schema["x-public-models"] = [model.__name__ for model in PUBLIC_MODELS]
    schema["description"] = (
        "Bounded artifact and checkpoint messages. Internal storage, authority and commit "
        "evidence are producer obligations, never public inputs or proof of live enforcement."
    )
    return schema
