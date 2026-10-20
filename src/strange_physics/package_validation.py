"""Pure package-policy and submitted-runtime approval checks; no extraction or build."""

from __future__ import annotations

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.package_contracts import (
    PackageInspection,
    PackagePolicy,
    SubmittedRuntimeApproval,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.session_contracts import server_time
from strange_physics.worker_contracts import WorkerPolicy


def metadata_size(value: Message) -> int:
    """Models have protocol structural caps; adapters still cap bytes before decode."""
    return len(canonical_json(value.model_dump(mode="json")).encode("utf-8"))


def validate_package_inspection(
    inspection: PackageInspection, policy: PackagePolicy | None, *, now: int
) -> PackagePolicy:
    """Validate a trusted completed inspection against actual configured policy."""
    server_time(now)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    source = inspection.source
    archive = source.archive.record.ref
    manifest = source.manifest_object.record.ref
    entries = inspection.entries
    expanded = sum(entry.expanded_bytes for entry in entries)
    lock = next(entry for entry in entries if entry.path == source.manifest.lock_path)
    if inspection.policy_sha256 != message_sha256(policy):
        raise ContractViolation("policy_unavailable", 503)
    if (
        inspection.observed_at > now
        or archive.size_bytes > policy.max_archive_bytes
        or manifest.size_bytes > policy.max_manifest_bytes
        or lock.expanded_bytes > policy.max_lock_bytes
        or len(entries) > policy.max_entries
        or expanded > policy.max_expanded_bytes
        or expanded > archive.size_bytes * policy.max_expansion_ratio
        or metadata_size(inspection) > policy.max_metadata_bytes
        or any(
            entry.expanded_bytes > policy.max_entry_bytes
            or len(entry.path.encode("utf-8")) > policy.max_path_bytes
            or len(entry.path.split("/")) > policy.max_path_depth
            for entry in entries
        )
    ):
        raise ContractViolation("invalid_request", 422)
    return policy


def validate_submitted_approval(
    approval: SubmittedRuntimeApproval,
    package_policy: PackagePolicy | None,
    worker_policy: WorkerPolicy | None,
    *,
    now: int,
) -> WorkerPolicy:
    """Current approved exact image and policy; retained source rows are provenance."""
    server_time(now)
    if not isinstance(approval, SubmittedRuntimeApproval):
        raise ContractViolation("forbidden", 403)
    if worker_policy is None:
        raise ContractViolation("policy_unavailable", 503)
    package = validate_package_inspection(approval.build.inspection, package_policy, now=now)
    build, scan, promoted = approval.build.build, approval.scan, approval.approval
    if (
        worker_policy.build_policy_sha256 != message_sha256(package)
        or scan.scan_policy_sha256 != worker_policy.scan_policy_sha256
        or promoted.approval_policy_sha256 != worker_policy.approval_policy_sha256
        or build.recipe_sha256 != package.build_recipe_sha256
        or build.builder_image_sha256 != package.builder_image_sha256
    ):
        raise ContractViolation("policy_unavailable", 503)
    if (
        promoted.state != "approved"
        or not promoted.decided_at <= now < scan.valid_until
        or metadata_size(approval) > worker_policy.max_metadata_bytes
    ):
        raise ContractViolation("forbidden", 403)
    return worker_policy
