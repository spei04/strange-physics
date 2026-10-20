"""Pure checkpoint admission/recovery checks; no storage, token verification or SQL I/O."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import TypeAdapter

from strange_physics.artifact_contracts import (
    ArtifactPolicy,
    ArtifactRef,
    CheckpointArtifacts,
    CheckpointAttempt,
    CheckpointCommitPlan,
    CheckpointHead,
    CheckpointLookup,
    CheckpointOutbox,
    CheckpointRecord,
    CheckpointReplay,
    CheckpointRequest,
    Index,
    RunArtifactRecord,
)
from strange_physics.contracts import Identifier
from strange_physics.control_contracts import (
    ContractViolation,
    Membership,
    Operation,
    VerifiedCredential,
    contiguous_record_prefix,
    validate_checkpoint_metadata,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import ProductAuthority
from strange_physics.serialization import canonical_json
from strange_physics.workspace_contracts import WorkspaceAuthority, authorize_product


def validate_artifact_content(ref: ArtifactRef, content: bytes, policy: ArtifactPolicy) -> None:
    """Check an already bounded complete raw buffer; does not read or verify a storage location."""
    if (
        len(content) != ref.size_bytes
        or len(content) > policy.max_artifact_bytes
        or ref.media_type not in policy.allowed_media_types
        or hashlib.sha256(content).hexdigest() != ref.sha256
    ):
        raise ContractViolation("invalid_request", 422)


def validate_artifact_update(before: RunArtifactRecord, after: RunArtifactRecord) -> None:
    """Incomplete lifecycle predicate; the storage/catalog producer supplies authority and CAS."""
    immutable = ("workspace_id", "run_id", "ref", "locator", "visibility", "created_at")
    if any(getattr(before, field) != getattr(after, field) for field in immutable):
        raise ContractViolation("incompatible_state", 409)
    if before == after:
        return
    allowed = {
        "uploading": {"available", "tombstoned"},
        "available": {"tombstoned"},
        "tombstoned": {"deleted"},
        "deleted": set(),
    }
    if after.revision != before.revision + 1 or after.state not in allowed[before.state]:
        raise ContractViolation("incompatible_state", 409)


def _bounded_request(request: CheckpointRequest, policy: ArtifactPolicy) -> None:
    # Visit iteratively before canonical serialization. Transport/decode caps remain
    # mandatory: a Python predicate cannot undo allocation of an unbounded HTTP body.
    stack: list[tuple[Any, int]] = [(request.checkpoint.state, 1)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if depth > policy.max_state_depth or nodes > policy.max_state_nodes:
            raise ContractViolation("invalid_request", 422)
        if isinstance(value, dict):
            nodes += len(value)  # Keys are counted as nodes too.
            if nodes + len(stack) + len(value) > policy.max_state_nodes:
                raise ContractViolation("invalid_request", 422)
            for key, child in value.items():
                if len(key) > policy.max_envelope_bytes:
                    raise ContractViolation("invalid_request", 422)
                stack.append((child, depth + 1))
        elif isinstance(value, list):
            if nodes + len(stack) + len(value) > policy.max_state_nodes:
                raise ContractViolation("invalid_request", 422)
            stack.extend((child, depth + 1) for child in value)
        elif isinstance(value, str) and len(value) > policy.max_envelope_bytes:
            raise ContractViolation("invalid_request", 422)
    if (
        len(canonical_json(request.model_dump(mode="json")).encode("utf-8"))
        > policy.max_envelope_bytes
        or len(canonical_json(request.checkpoint.model_dump(mode="json")).encode("utf-8"))
        > 256 * 1024
        or len(request.artifacts) > policy.max_artifacts
        or sum(ref.size_bytes for ref in request.artifacts) > policy.max_total_artifact_bytes
        or any(
            ref.size_bytes > policy.max_artifact_bytes
            or ref.media_type not in policy.allowed_media_types
            for ref in request.artifacts
        )
    ):
        raise ContractViolation("invalid_request", 422)


def _objects(
    request: CheckpointRequest,
    artifacts: CheckpointArtifacts,
    policy: ArtifactPolicy,
    *,
    workspace_id: str,
    run_id: str,
    now: int,
) -> None:
    if (
        (artifacts.workspace_id, artifacts.run_id) != (workspace_id, run_id)
        or artifacts.request_sha256 != message_sha256(request)
        or artifacts.policy_sha256 != message_sha256(policy)
        or artifacts.checked_at != now
        or tuple(item.record.ref for item in artifacts.objects) != request.artifacts
    ):
        raise ContractViolation("invalid_request", 422)
    for item in artifacts.objects:
        if (
            item.record.state != "available"
            or item.record.visibility != "agent-visible"
            or item.verification.observed_at > now
        ):
            raise ContractViolation("invalid_request", 422)


def _commit_evidence(
    record: CheckpointRecord,
    outbox: CheckpointOutbox,
    *,
    workspace_id: str,
    run_id: str,
    index: int,
    run_revision: int,
    attempt: CheckpointAttempt,
    now: int,
) -> None:
    if (
        (record.workspace_id, record.run_id, record.index) != (workspace_id, run_id, index)
        or record.binding != attempt.binding
        or record.lease_epoch > attempt.lease_epoch
        or (record.lease_epoch == attempt.lease_epoch and record.attempt_id != attempt.attempt_id)
        or record.run_revision > run_revision
        or record.committed_at > now
        or record.request_sha256 != message_sha256(record.request)
        or (outbox.workspace_id, outbox.run_id, outbox.index) != (workspace_id, run_id, index)
        or outbox.request_sha256 != record.request_sha256
        or outbox.checkpoint_revision != record.checkpoint_revision
        or outbox.record_sha256 != message_sha256(record)
    ):
        raise ContractViolation("recovery_required", 409)


def _lookup(
    lookup: CheckpointLookup,
    *,
    workspace_id: str,
    run_id: str,
    index: int,
    prefix: int,
    run_revision: int,
    attempt: CheckpointAttempt,
    now: int,
) -> None:
    if (lookup.workspace_id, lookup.run_id, lookup.index) != (workspace_id, run_id, index):
        raise ContractViolation("recovery_required", 409)
    head, record, outbox = lookup.head, lookup.record, lookup.outbox
    latest, latest_outbox = lookup.latest_record, lookup.latest_outbox
    if head is None:
        if lookup.revision != 0 or any(
            item is not None for item in (record, outbox, latest, latest_outbox)
        ):
            raise ContractViolation("recovery_required", 409)
        return
    if (
        latest is None
        or latest_outbox is None
        or head.checkpoint_revision != lookup.revision
        or head.index > prefix
        or (record is None) != (outbox is None)
        or (record is None and head.index == index)
    ):
        raise ContractViolation("recovery_required", 409)
    _commit_evidence(
        latest,
        latest_outbox,
        workspace_id=workspace_id,
        run_id=run_id,
        index=head.index,
        run_revision=run_revision,
        attempt=attempt,
        now=now,
    )
    if (
        latest.checkpoint_revision != head.checkpoint_revision
        or latest.request_sha256 != head.request_sha256
    ):
        raise ContractViolation("recovery_required", 409)
    if record is None or outbox is None:
        return
    _commit_evidence(
        record,
        outbox,
        workspace_id=workspace_id,
        run_id=run_id,
        index=index,
        run_revision=run_revision,
        attempt=attempt,
        now=now,
    )
    if record.index == head.index:
        if record != latest or outbox != latest_outbox:
            raise ContractViolation("recovery_required", 409)
    elif (
        record.index > head.index
        or record.checkpoint_revision >= latest.checkpoint_revision
        or record.run_revision > latest.run_revision
        or record.lease_epoch > latest.lease_epoch
        or (record.lease_epoch == latest.lease_epoch and record.attempt_id != latest.attempt_id)
        or record.committed_at > latest.committed_at
    ):
        raise ContractViolation("recovery_required", 409)


def _retained_objects(record: CheckpointRecord, current: CheckpointArtifacts) -> None:
    # This lifecycle has no available-to-available catalog revision transition.
    # Renewed byte readbacks may differ; the retained available row may not.
    if tuple(item.record for item in record.artifacts.objects) != tuple(
        item.record for item in current.objects
    ):
        raise ContractViolation("recovery_required", 409)


def validate_checkpoint_write(
    request: CheckpointRequest,
    workspace: WorkspaceAuthority,
    credential: VerifiedCredential,
    membership: Membership,
    *,
    authority: ProductAuthority,
    policy: ArtifactPolicy | None,
    attempt: CheckpointAttempt,
    artifacts: CheckpointArtifacts,
    operations: tuple[Operation, ...],
    lookup: CheckpointLookup,
    path_index: int,
    now: int,
    event_id: str | None,
) -> CheckpointCommitPlan | CheckpointReplay:
    """Complete pure admission boundary; all trusted inputs come from one current commit context.

    The adapter reads complete current authority, natural-key absence, accepted ledger,
    pinned attempt and object catalog under the required locks and verifies storage
    generations. It rechecks the same fences while committing the entire proposal.
    No caller-supplied boolean, claimed request digest or default authority is accepted.
    """
    lease = authority.current.lease if authority.kind == "run" else None
    authorize_product(
        workspace,
        credential,
        membership,
        authority=authority,
        permission="checkpoints:write",
        workspace_id=attempt.workspace_id,
        run_id=attempt.run_id,
        lease=lease,
        now=now,
    )
    if authority.kind != "run":  # Other identities cannot obtain worker permissions.
        raise ContractViolation("forbidden", 403)
    current = authority.current
    if attempt.attempt_id != current.lease.attempt_id or attempt.lease_epoch != current.lease.epoch:
        raise ContractViolation("forbidden", 403)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    TypeAdapter(Index).validate_python(path_index, strict=True)
    if path_index != request.checkpoint.through_index:
        raise ContractViolation("invalid_request", 422)
    if (
        request.runtime_image_sha256 != attempt.binding.runtime_image_sha256
        or request.checkpoint.agent_id != attempt.binding.agent_id
    ):
        raise ContractViolation("incompatible_state", 409)
    _bounded_request(request, policy)
    _objects(
        request,
        artifacts,
        policy,
        workspace_id=attempt.workspace_id,
        run_id=attempt.run_id,
        now=now,
    )
    run = current.run
    if (
        len(operations) != run.experiments_accepted
        or len(operations) > 10_000
        or sorted(
            op.accepted_experiment_index
            for op in operations
            if op.accepted_experiment_index is not None
        )
        != list(range(len(operations)))
        or any((op.workspace_id, op.run_id) != (run.workspace_id, run.run_id) for op in operations)
    ):
        raise ContractViolation("recovery_required", 409)
    try:
        prefix = contiguous_record_prefix(operations)
    except ValueError as error:
        raise ContractViolation("recovery_required", 409) from error
    _lookup(
        lookup,
        workspace_id=attempt.workspace_id,
        run_id=attempt.run_id,
        index=path_index,
        prefix=prefix,
        run_revision=run.revision,
        attempt=attempt,
        now=now,
    )
    digest = message_sha256(request)
    disposition = validate_checkpoint_metadata(
        request.checkpoint,
        path_index=path_index,
        binding=attempt.binding,
        expected_binding=attempt.binding,
        full_request_sha256=digest,
        stored_request_sha256=None if lookup.record is None else lookup.record.request_sha256,
        latest_index=None if lookup.head is None else lookup.head.index,
        committed_prefix=prefix,
    )
    if disposition == "replayed":
        if lookup.record is None or lookup.record.binding != attempt.binding:
            raise ContractViolation("recovery_required", 409)
        _retained_objects(lookup.record, artifacts)
        return CheckpointReplay(request=lookup.record.request, request_sha256=digest)
    if event_id is None or lookup.revision >= 2**53 - 1:
        raise ContractViolation("invalid_request", 422)
    TypeAdapter(Identifier).validate_python(event_id, strict=True)
    record = CheckpointRecord(
        workspace_id=attempt.workspace_id,
        run_id=attempt.run_id,
        index=path_index,
        request=request,
        request_sha256=digest,
        binding=attempt.binding,
        artifacts=artifacts,
        attempt_id=attempt.attempt_id,
        lease_epoch=attempt.lease_epoch,
        run_revision=run.revision,
        checkpoint_revision=lookup.revision + 1,
        committed_at=now,
    )
    return CheckpointCommitPlan(
        expected_checkpoint_revision=lookup.revision,
        record=record,
        head=CheckpointHead(
            index=path_index, request_sha256=digest, checkpoint_revision=record.checkpoint_revision
        ),
        outbox=CheckpointOutbox(
            event_id=event_id,
            workspace_id=attempt.workspace_id,
            run_id=attempt.run_id,
            index=path_index,
            request_sha256=digest,
            checkpoint_revision=record.checkpoint_revision,
            record_sha256=message_sha256(record),
        ),
    )


def validate_checkpoint_restore_candidate(
    record: CheckpointRecord,
    *,
    expected_attempt: CheckpointAttempt,
    policy: ArtifactPolicy,
    artifacts: CheckpointArtifacts,
    now: int,
) -> None:
    """NON-AUTHORIZING compatibility/integrity predicate; never grants payload delivery.

    The later restore adapter must establish current read authority separately,
    verify committed history/outbox and explicitly select this checkpoint. No read
    route or permission is introduced here, and no checkpoint is selected automatically.
    """
    if (
        (record.workspace_id, record.run_id)
        != (expected_attempt.workspace_id, expected_attempt.run_id)
        or record.binding != expected_attempt.binding
        or record.committed_at > now
        or record.request_sha256 != message_sha256(record.request)
    ):
        raise ContractViolation("incompatible_state", 409)
    _bounded_request(record.request, policy)
    _objects(
        record.request,
        artifacts,
        policy,
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        now=now,
    )
    _retained_objects(record, artifacts)
