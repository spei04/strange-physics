"""Package and runtime-approval projections; no build, extraction or signature verifier."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.artifact_contracts import (
    ArtifactRef,
    Number,
    ObjectVerification,
    StorageLocator,
)
from strange_physics.contracts import Identifier, Message
from strange_physics.research_contracts import Digest, message_sha256

Positive = Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
ArchivePath = Annotated[
    str,
    Field(
        min_length=1,
        max_length=512,
        pattern=r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$",
        json_schema_extra={"not": {"pattern": "[^A-Za-z0-9_./-]"}},
    ),
]
Entrypoint = Annotated[
    str,
    Field(
        min_length=3,
        max_length=256,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$",
        json_schema_extra={"not": {"pattern": "[^A-Za-z0-9_.:]"}},
    ),
]
Commit = Annotated[
    str,
    Field(
        min_length=40,
        max_length=64,
        pattern=r"^([0-9a-f]{40}|[0-9a-f]{64})$",
        json_schema_extra={"not": {"pattern": "[^0-9a-f]"}},
    ),
]


def canonical_path(path: str) -> None:
    if any(part in {"", ".", ".."} for part in path.split("/")):
        raise ValueError("Archive path must have canonical relative segments")


class PackageManifest(Message):
    """Detached JSON manifest: syntax/profile only, never an import or Agent conformance test.

    message_sha256 of this complete parsed manifest is agent_package_sha256 in
    CreateRunRequest and CheckpointBinding, distinct from raw archive, detached
    manifest, lock and OCI image hashes.

    The source archive does not contain this generation-bearing manifest, avoiding
    a self-referential archive hash. Configuration-dependent Agent.identity is
    retained in original run admission, separately from this package entrypoint.
    """

    schema_version: Literal["strange-physics.python-agent.v1"]
    source: ArtifactRef
    agent_protocol: Literal["strange-physics.agent.v1"]
    entrypoint: Entrypoint
    lock_profile: Literal["uv-lock.v1"]
    lock_path: ArchivePath
    lock_bytes_sha256: Digest

    @model_validator(mode="after")
    def path(self) -> Self:
        canonical_path(self.lock_path)
        return self


class PackageObjectRecord(Message):
    """Workspace/package ownership; no fabricated run ID."""

    workspace_id: Identifier
    package_id: Identifier
    ref: ArtifactRef
    locator: StorageLocator
    state: Literal["uploading", "available", "tombstoned", "deleted"]
    revision: Number
    created_at: Number


class VerifiedPackageObject(Message):
    record: PackageObjectRecord
    verification: ObjectVerification

    @model_validator(mode="after")
    def exact_object(self) -> Self:
        row, proof = self.record, self.verification
        ref = row.ref
        if (
            row.locator != proof.locator
            or (ref.generation, ref.sha256, ref.size_bytes, ref.media_type)
            != (proof.generation, proof.sha256, proof.size_bytes, proof.media_type)
            or proof.observed_at < row.created_at
        ):
            raise ValueError("Package proof must bind the complete exact object generation")
        return self


class PackageSource(Message):
    """Trusted producer parsed actual verified detached manifest bytes into manifest."""

    archive: VerifiedPackageObject
    manifest_object: VerifiedPackageObject
    manifest: PackageManifest

    @model_validator(mode="after")
    def exact_source(self) -> Self:
        archive, manifest = self.archive.record, self.manifest_object.record
        if (
            (archive.workspace_id, archive.package_id)
            != (manifest.workspace_id, manifest.package_id)
            or archive.ref.artifact_id == manifest.ref.artifact_id
            or self.manifest.source != archive.ref
            or archive.state != "available"
            or manifest.state != "available"
            or manifest.ref.media_type != "application/json"
        ):
            raise ValueError("Package source must join available archive and detached manifest")
        return self


class ExecutionResources(Message):
    cpu_seconds: Positive
    wall_seconds: Positive
    memory_bytes: Positive
    process_count: Positive
    scratch_bytes: Number
    output_bytes: Number


class PackagePolicy(Message):
    """Explicit producer/predecode/cumulative caps; these are not deployment defaults."""

    policy_id: Identifier
    max_metadata_bytes: Positive
    max_manifest_bytes: Positive
    max_lock_bytes: Positive
    max_archive_bytes: Positive
    max_entries: Annotated[int, Field(strict=True, ge=1, le=10_000)]
    max_path_bytes: Annotated[int, Field(strict=True, ge=1, le=512)]
    max_path_depth: Annotated[int, Field(strict=True, ge=1, le=64)]
    max_entry_bytes: Number
    max_expanded_bytes: Number
    max_expansion_ratio: Positive
    build_limits: ExecutionResources
    build_recipe_sha256: Digest
    builder_image_sha256: Digest
    build_sandbox_profile: Identifier
    dependency_network_policy: Identifier


class ArchiveEntry(Message):
    path: ArchivePath
    kind: Literal["file", "directory"]
    expanded_bytes: Number
    bytes_sha256: Digest | None

    @model_validator(mode="after")
    def safe_entry(self) -> Self:
        canonical_path(self.path)
        if (self.kind == "file") != (self.bytes_sha256 is not None):
            raise ValueError("Only regular files have content hashes")
        if self.kind == "directory" and self.expanded_bytes != 0:
            raise ValueError("Directories have no expanded file bytes")
        return self


class PackageInspection(Message):
    """Trusted bounded full-archive inspection; not an extractor or proof by construction."""

    inspection_id: Identifier
    inspector_id: Identifier
    source: PackageSource
    policy_sha256: Digest
    entries: Annotated[tuple[ArchiveEntry, ...], Field(min_length=1, max_length=10_000)]
    observed_at: Number

    @model_validator(mode="after")
    def inventory(self) -> Self:
        paths = tuple(entry.path for entry in self.entries)
        if tuple(sorted(set(paths))) != paths:
            raise ValueError("Complete entries must be unique and sorted")
        files = {entry.path: entry for entry in self.entries if entry.kind == "file"}
        if any(any(parent in files for parent in path_parents(path)) for path in paths):
            raise ValueError("A regular file cannot also be an archive ancestor")
        lock = files.get(self.source.manifest.lock_path)
        if lock is None or lock.bytes_sha256 != self.source.manifest.lock_bytes_sha256:
            raise ValueError("Actual lock entry must match the detached manifest")
        if any(
            item.verification.observed_at > self.observed_at
            for item in (self.source.archive, self.source.manifest_object)
        ):
            raise ValueError("Inspection cannot precede its byte evidence")
        return self


def path_parents(path: str) -> tuple[str, ...]:
    parts = path.split("/")
    return tuple("/".join(parts[:n]) for n in range(1, len(parts)))


class LockResolutionEvidence(Message):
    """Actual trusted lock interpretation; digest equality alone does not prove pinned inputs."""

    verification_id: Identifier
    verifier_id: Identifier
    inspection_sha256: Digest
    lock_bytes_sha256: Digest
    policy_sha256: Digest
    outcome: Literal["complete_pinned"]
    observed_at: Number


class VerifiedBuildEvidence(Message):
    """Real build/provenance verifier output. No unsigned client attestation is accepted."""

    build_id: Identifier
    verifier_id: Identifier
    provenance_verification_id: Identifier
    provenance_bytes_sha256: Digest
    source_sha256: Digest
    lock_bytes_sha256: Digest
    recipe_sha256: Digest
    builder_image_sha256: Digest
    runtime_image_sha256: Digest
    build_policy_sha256: Digest
    completed_at: Number
    verified_at: Number

    @model_validator(mode="after")
    def time(self) -> Self:
        if self.verified_at < self.completed_at:
            raise ValueError("Build verification cannot precede completion")
        return self


class SubmittedBuild(Message):
    kind: Literal["submitted_agent"]
    inspection: PackageInspection
    lock: LockResolutionEvidence
    build: VerifiedBuildEvidence

    @model_validator(mode="after")
    def source_binding(self) -> Self:
        inspection, lock, build = self.inspection, self.lock, self.build
        if (
            lock.inspection_sha256 != message_sha256(inspection)
            or lock.lock_bytes_sha256 != inspection.source.manifest.lock_bytes_sha256
            or lock.policy_sha256 != inspection.policy_sha256
            or build.source_sha256 != message_sha256(inspection.source)
            or build.lock_bytes_sha256 != lock.lock_bytes_sha256
            or build.build_policy_sha256 != inspection.policy_sha256
            or lock.observed_at < inspection.observed_at
            or build.completed_at < lock.observed_at
        ):
            raise ValueError("Submitted build must bind actual source, lock and inspection policy")
        return self


class BuiltinSource(Message):
    """Real trusted repository/build inputs; never a fabricated uploaded package."""

    repository_id: Identifier
    commit: Commit
    tree: Commit
    lock_bytes_sha256: Digest
    recipe_sha256: Digest


class BuiltinBuild(Message):
    kind: Literal["builtin_analytic"]
    source: BuiltinSource
    build: VerifiedBuildEvidence

    @model_validator(mode="after")
    def source_binding(self) -> Self:
        if (
            self.build.source_sha256 != message_sha256(self.source)
            or self.build.lock_bytes_sha256 != self.source.lock_bytes_sha256
            or self.build.recipe_sha256 != self.source.recipe_sha256
        ):
            raise ValueError("Builtin build must bind actual repository, lock and recipe evidence")
        return self


class ImageScanEvidence(Message):
    scan_id: Identifier
    verifier_id: Identifier
    build_sha256: Digest
    runtime_image_sha256: Digest
    scan_policy_sha256: Digest
    outcome: Literal["passed", "rejected", "unknown"]
    observed_at: Number
    valid_until: Number

    @model_validator(mode="after")
    def time(self) -> Self:
        if self.valid_until <= self.observed_at:
            raise ValueError("Scan evidence must have positive validity")
        return self


class ApprovalState(Message):
    """Current promotion/revocation row; retained approval snapshots are provenance only."""

    approval_id: Identifier
    revision: Number
    state: Literal["quarantined", "approved", "revoked"]
    approval_policy_sha256: Digest
    build_sha256: Digest
    scan_sha256: Digest
    profile_sha256: Digest
    decided_at: Number


def approval_binding(
    build: SubmittedBuild | BuiltinBuild,
    scan: ImageScanEvidence,
    approval: ApprovalState,
    profile: Message,
) -> None:
    if (
        scan.build_sha256 != message_sha256(build)
        or scan.runtime_image_sha256 != build.build.runtime_image_sha256
        or scan.observed_at < build.build.verified_at
        or approval.build_sha256 != message_sha256(build)
        or approval.scan_sha256 != message_sha256(scan)
        or approval.profile_sha256 != message_sha256(profile)
        or approval.decided_at < scan.observed_at
        or (
            approval.state == "approved"
            and (scan.outcome != "passed" or approval.decided_at >= scan.valid_until)
        )
    ):
        raise ValueError("Runtime approval must join exact verified build and scan")


class SubmittedAgentProfile(Message):
    kind: Literal["submitted_agent"]
    agent_protocol: Literal["strange-physics.agent.v1"]


class BuiltinPredictionProfile(Message):
    kind: Literal["builtin_analytic"]
    purpose: Literal["native_prediction"]
    predictor_profile: Literal["strange-physics.linear-spring-prediction.v1"]
    predictor_version: Identifier
    prediction_config_sha256: Digest


class SubmittedRuntimeApproval(Message):
    kind: Literal["submitted_agent"]
    profile: SubmittedAgentProfile
    build: SubmittedBuild
    scan: ImageScanEvidence
    approval: ApprovalState

    @model_validator(mode="after")
    def binding(self) -> Self:
        approval_binding(self.build, self.scan, self.approval, self.profile)
        return self


class BuiltinAnalyticApproval(Message):
    kind: Literal["builtin_analytic"]
    profile: BuiltinPredictionProfile
    build: BuiltinBuild
    scan: ImageScanEvidence
    approval: ApprovalState

    @model_validator(mode="after")
    def binding(self) -> Self:
        approval_binding(self.build, self.scan, self.approval, self.profile)
        return self


PACKAGE_MODELS: tuple[type[Message], ...] = (
    PackageManifest,
    PackageObjectRecord,
    VerifiedPackageObject,
    PackageSource,
    ExecutionResources,
    PackagePolicy,
    ArchiveEntry,
    PackageInspection,
    LockResolutionEvidence,
    VerifiedBuildEvidence,
    SubmittedBuild,
    BuiltinSource,
    BuiltinBuild,
    ImageScanEvidence,
    ApprovalState,
    SubmittedRuntimeApproval,
    BuiltinAnalyticApproval,
    SubmittedAgentProfile,
    BuiltinPredictionProfile,
)
