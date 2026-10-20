"""Pure coordinator-only run-credential proposals and current-authorized replay.

No token is signed here. The original handler may act on issue_claims only after
atomic persistence and current-authority revalidation. Retries return metadata.
"""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.product_authority import run_key_valid, validate_run_authority
from strange_physics.research_contracts import Count, message_sha256
from strange_physics.run_credential_contracts import (
    RunAuthorityState,
    RunCoordinatorAuthority,
    RunCredentialAudit,
    RunCredentialIssueRequest,
    RunCredentialLookup,
    RunCredentialOperation,
    RunCredentialOutcome,
    RunCredentialPlan,
    RunCredentialPolicy,
    RunCredentialReceipt,
    RunCredentialRecord,
    RunCredentialReplaceRequest,
    RunCredentialResponse,
    RunCredentialRevokeRequest,
    RunCredentialSet,
    RunCredentialSnapshot,
    RunCredentialView,
    RunTokenClaims,
)
from strange_physics.session_contracts import server_time
from strange_physics.workspace_contracts import (
    IdempotencyKey,
    WorkspaceAuthority,
    validate_product_workspace,
)

type RunCredentialRequest = (
    RunCredentialIssueRequest | RunCredentialReplaceRequest | RunCredentialRevokeRequest
)


def _changed[M: Message](model: M, **changes: object) -> M:
    return type(model).model_validate(model.model_dump() | changes)


def _add(value: int, increment: int) -> int:
    try:
        return TypeAdapter(Count).validate_python(value + increment, strict=True)
    except ValidationError as error:
        raise ContractViolation("incompatible_state", 409) from error


def authorize_coordinator(
    policy: RunCredentialPolicy | None,
    coordinator: RunCoordinatorAuthority,
    current: RunAuthorityState,
    workspace: WorkspaceAuthority,
    *,
    now: int,
) -> RunCredentialPolicy:
    """Private current coordinator permission plus durable owner/workspace/lease."""
    server_time(now)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    if coordinator.revoked or now >= coordinator.expires_at:
        raise ContractViolation("unauthenticated", 401)
    if (coordinator.workspace_id, coordinator.run_id) != (
        current.run.workspace_id,
        current.run.run_id,
    ):
        raise ContractViolation("not_found", 404)
    validate_run_authority(current, now=now)
    validate_product_workspace(workspace, current.run.workspace_id, current.owner.grant.membership)
    return policy


def _view(
    current: RunAuthorityState,
    record: RunCredentialRecord,
    policy: RunCredentialPolicy,
    *,
    now: int,
) -> RunCredentialView:
    state = current.credentials
    return RunCredentialView(
        record=record,
        credential_revision=state.revision,
        current_generation=state.last_generation,
        current_credential_id=state.current_credential_id,
        valid_now=run_key_valid(current, record, policy, now=now),
    )


def _audit(receipt: RunCredentialReceipt) -> RunCredentialAudit:
    return RunCredentialAudit(
        event_id=receipt.audit_event_id,
        actor_id=receipt.actor_id,
        authorization_id=receipt.authorization_id,
        request_sha256=receipt.request_sha256,
        outcome=receipt.outcome,
        snapshot_sha256=message_sha256(receipt.snapshot),
    )


def _record_evolution(before: RunCredentialRecord, after: RunCredentialRecord, *, now: int) -> bool:
    return (
        before.claims == after.claims
        and after.retain_until >= before.retain_until
        and (before.revoked_at is None or after.revoked_at == before.revoked_at)
        and (after.revoked_at is None or after.revoked_at <= now)
    )


def _replay(
    policy: RunCredentialPolicy,
    coordinator: RunCoordinatorAuthority,
    current: RunAuthorityState,
    operation: RunCredentialOperation,
    request: RunCredentialRequest,
    key: str,
    lookup: RunCredentialLookup,
    *,
    now: int,
) -> RunCredentialResponse | None:
    if lookup.state == "absent":
        return None
    receipt = lookup.receipt
    if (
        lookup.state != "committed"
        or receipt is None
        or lookup.audit is None
        or receipt.retain_until <= now
        or lookup.audit != _audit(receipt)
    ):
        raise ContractViolation("recovery_required", 409)
    outcome, snapshot, state = receipt.outcome, receipt.snapshot, current.credentials
    if (
        receipt.policy_id != policy.policy_id
        or receipt.actor_id != coordinator.actor_id
        or receipt.key != key
        or outcome.operation != operation
        or (outcome.workspace_id, outcome.run_id) != (current.run.workspace_id, current.run.run_id)
    ):
        raise ContractViolation("recovery_required", 409)
    if receipt.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    if (
        isinstance(request, RunCredentialReplaceRequest)
        and request.credential_id != outcome.replaced_credential_id
    ) or (
        isinstance(request, RunCredentialRevokeRequest)
        and request.credential_id != outcome.credential_id
    ):
        raise ContractViolation("recovery_required", 409)
    if (outcome.attempt_id, outcome.lease_epoch) != (current.lease.attempt_id, current.lease.epoch):
        raise ContractViolation("forbidden", 403)
    if (
        state.ownership != snapshot.ownership
        or current.run.revision < outcome.run_revision
        or state.revision < snapshot.credential_revision
        or state.last_generation < snapshot.last_generation
        or now < outcome.committed_at
        or outcome.run_revision != request.expected_run_revision
        or outcome.credential_revision != request.expected_credential_revision + 1
    ):
        raise ContractViolation("recovery_required", 409)
    equal = state.revision == snapshot.credential_revision
    if equal and (
        state.last_generation != snapshot.last_generation
        or state.current_credential_id != snapshot.current_credential_id
    ):
        raise ContractViolation("recovery_required", 409)
    records = {r.claims.credential_id: r for r in state.records}
    for original in snapshot.records:
        record = records.get(original.claims.credential_id)
        if (
            record is None
            or (equal and record != original)
            or not _record_evolution(original, record, now=now)
            or (
                original.revoked_at is None
                and record.revoked_at is not None
                and record.revoked_at < outcome.committed_at
            )
        ):
            raise ContractViolation("recovery_required", 409)
    record = records[outcome.credential_id]
    return RunCredentialResponse(
        disposition="replayed",
        outcome=outcome,
        credential=_view(current, record, policy, now=now),
    )


def change_run_credential(
    policy: RunCredentialPolicy | None,
    coordinator: RunCoordinatorAuthority,
    current: RunAuthorityState,
    workspace: WorkspaceAuthority,
    *,
    operation: RunCredentialOperation,
    request: RunCredentialRequest,
    key: IdempotencyKey,
    lookup: RunCredentialLookup,
    now: int,
    new_credential_id: str | None = None,
    audit_event_id: str | None = None,
) -> RunCredentialPlan | RunCredentialResponse:
    """Issue, immediately replace, or revoke under one current run/keyset lock.

    Generated identifiers are trusted allocator outputs, not request authority.
    They are required only for fresh admission and ignored on metadata replay.
    """
    configured = authorize_coordinator(policy, coordinator, current, workspace, now=now)
    expected_type = {
        "issue": RunCredentialIssueRequest,
        "replace": RunCredentialReplaceRequest,
        "revoke": RunCredentialRevokeRequest,
    }[operation]
    if type(request) is not expected_type:
        raise ContractViolation("invalid_request", 422)
    TypeAdapter(IdempotencyKey).validate_python(key, strict=True)
    replay = _replay(configured, coordinator, current, operation, request, key, lookup, now=now)
    if replay is not None:
        return replay
    state, lease = current.credentials, current.lease
    if (
        request.expected_run_revision != current.run.revision
        or request.expected_credential_revision != state.revision
    ):
        raise ContractViolation("idempotency_conflict", 409)
    if any(r.claims.issued_at > now for r in state.records):
        raise ContractViolation("recovery_required", 409)
    if audit_event_id is None:
        raise ContractViolation("invalid_request", 422)
    TypeAdapter(Identifier).validate_python(audit_event_id, strict=True)
    records = {r.claims.credential_id: r for r in state.records}
    target: RunCredentialRecord | None = None
    if isinstance(request, (RunCredentialReplaceRequest, RunCredentialRevokeRequest)):
        target = records.get(request.credential_id)
        if target is None:
            raise ContractViolation("not_found", 404)
        if target.revoked_at is not None:
            raise ContractViolation("incompatible_state", 409)
    if operation == "issue" and state.current_credential_id is not None:
        raise ContractViolation("incompatible_state", 409)
    if operation == "replace" and (
        target is None or state.current_credential_id != target.claims.credential_id
    ):
        raise ContractViolation("incompatible_state", 409)
    issue_claims: RunTokenClaims | None = None
    generation = state.last_generation
    current_id = state.current_credential_id
    affected: list[RunCredentialRecord] = []
    if target is not None:
        target = _changed(target, revoked_at=now, retain_until=max(target.retain_until, now))
        affected.append(target)
        if target.claims.credential_id == current_id:
            current_id = None
    if operation in ("issue", "replace"):
        if new_credential_id is None:
            raise ContractViolation("invalid_request", 422)
        TypeAdapter(Identifier).validate_python(new_credential_id, strict=True)
        if new_credential_id in records or len(records) >= configured.max_records:
            raise ContractViolation("incompatible_state", 409)
        generation = _add(generation, 1)
        issue_claims = RunTokenClaims(
            policy_id=configured.policy_id,
            issuer=configured.issuer,
            audience=configured.audience,
            credential_id=new_credential_id,
            workspace_id=state.ownership.workspace_id,
            run_id=state.ownership.run_id,
            principal_id=state.ownership.principal_id,
            ownership_sha256=message_sha256(state.ownership),
            attempt_id=lease.attempt_id,
            lease_epoch=lease.epoch,
            generation=generation,
            scopes=state.ownership.scopes,
            issued_at=now,
            expires_at=min(
                _add(now, configured.max_ttl_seconds),
                lease.expires_at,
                state.ownership.run_deadline,
            ),
        )
        affected.append(
            RunCredentialRecord(
                claims=issue_claims,
                revoked_at=None,
                retain_until=issue_claims.expires_at,
            )
        )
        current_id = new_credential_id
        outcome_id = new_credential_id
    else:
        assert target is not None
        outcome_id = target.claims.credential_id
    retain_until = max(
        _add(now, configured.receipt_retention_seconds), *(r.retain_until for r in affected)
    )
    affected = sorted(
        (_changed(r, retain_until=retain_until) for r in affected),
        key=lambda r: r.claims.credential_id,
    )
    records.update({r.claims.credential_id: r for r in affected})
    proposed = RunCredentialSet(
        ownership=state.ownership,
        revision=_add(state.revision, 1),
        last_generation=generation,
        current_credential_id=current_id,
        records=tuple(records[key] for key in sorted(records)),
    )
    outcome = RunCredentialOutcome(
        operation=operation,
        workspace_id=state.ownership.workspace_id,
        run_id=state.ownership.run_id,
        ownership_sha256=message_sha256(state.ownership),
        attempt_id=lease.attempt_id,
        lease_epoch=lease.epoch,
        credential_id=outcome_id,
        replaced_credential_id=target.claims.credential_id
        if operation == "replace" and target
        else None,
        run_revision=current.run.revision,
        credential_revision=proposed.revision,
        committed_at=now,
    )
    snapshot = RunCredentialSnapshot(
        ownership=state.ownership,
        run_revision=current.run.revision,
        credential_revision=proposed.revision,
        last_generation=generation,
        current_credential_id=current_id,
        records=tuple(affected),
    )
    receipt = RunCredentialReceipt(
        policy_id=configured.policy_id,
        actor_id=coordinator.actor_id,
        authorization_id=coordinator.authorization_id,
        key=key,
        request_sha256=message_sha256(request),
        outcome=outcome,
        snapshot=snapshot,
        audit_event_id=audit_event_id,
        retain_until=retain_until,
    )
    return RunCredentialPlan(
        credentials=proposed,
        receipt=receipt,
        audit=_audit(receipt),
        response=RunCredentialResponse(
            disposition="committed",
            outcome=outcome,
            credential=_view(
                _changed(current, credentials=proposed), records[outcome_id], configured, now=now
            ),
        ),
        issue_claims=issue_claims,
    )
