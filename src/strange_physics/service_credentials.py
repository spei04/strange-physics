"""Pure C1 admission/replay proposals for trusted current database projections.

Callers hold the shared workspace/principal locks, supply complete current
records, and atomically persist the returned plan. These functions do not
verify a bearer, generate a secret, acquire locks or prove a SQL commit.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from pydantic import TypeAdapter, ValidationError

from strange_physics.contracts import Identifier
from strange_physics.control_contracts import ContractViolation, Membership
from strange_physics.credential_authority import GrantAuthority
from strange_physics.research_contracts import Count, message_sha256
from strange_physics.service_contracts import (
    ServiceAudit,
    ServiceCommitSnapshot,
    ServiceCreateRequest,
    ServiceCredentialPolicy,
    ServiceError,
    ServiceKeyIssuedResponse,
    ServiceKeyIssueRequest,
    ServiceKeyMaterial,
    ServiceKeyRecord,
    ServiceKeyRecoverRequest,
    ServiceKeyRevokeRequest,
    ServiceKeyRotateRequest,
    ServiceKeySet,
    ServiceKeyState,
    ServiceKeyView,
    ServiceManager,
    ServiceMutationOutcome,
    ServiceMutationResponse,
    ServiceOperation,
    ServicePermission,
    ServicePlan,
    ServicePrincipalView,
    ServiceReceipt,
    ServiceReceiptLookup,
    ServiceStateRequest,
)
from strange_physics.session_contracts import (
    DeploymentSessionPolicy,
    browser_request,
    require_policy,
    server_time,
)
from strange_physics.workspace_contracts import (
    IdempotencyKey,
    WorkspaceAuthority,
    authorize_management,
    validate_human_actor,
)

type ServiceRequest = (
    ServiceCreateRequest
    | ServiceStateRequest
    | ServiceKeyIssueRequest
    | ServiceKeyRotateRequest
    | ServiceKeyRecoverRequest
    | ServiceKeyRevokeRequest
)


def _add(value: int, increment: int) -> int:
    try:
        return TypeAdapter(Count).validate_python(value + increment, strict=True)
    except ValidationError as error:
        raise ContractViolation("incompatible_state", 409) from error


def authorize_service_management(
    session_policy: DeploymentSessionPolicy | None,
    policy: ServiceCredentialPolicy | None,
    manager: ServiceManager,
    workspace: WorkspaceAuthority,
    *,
    workspace_id: str,
    now: int,
    mutation: bool,
) -> ServiceCredentialPolicy:
    """Apply current authority before freshness and before any receipt disclosure."""
    server_time(now)
    configured = require_policy(session_policy)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    browser_request(configured, manager.actor.context, mutation=mutation)
    validate_human_actor(configured, manager.actor, now=now, mutation=False)
    principal = manager.owner.principal
    if not principal.active or principal.generation != manager.session_principal_generation:
        raise ContractViolation("unauthenticated", 401)
    authorize_management(
        configured,
        manager.actor,
        workspace,
        manager.owner.grant.membership,
        workspace_id=workspace_id,
        now=now,
        owner_required=True,
        mutation=False,
    )
    if mutation and now - manager.actor.session.authenticated_at >= configured.recent_auth_seconds:
        raise ContractViolation("reauthentication_required", 401)
    return policy


def service_key_valid(principal: ServicePrincipalView, key: ServiceKeyState, *, now: int) -> bool:
    """Current ancestry/lifetime predicate; this does not verify the presented secret."""
    server_time(now)
    return (
        principal.active
        and principal.grant.membership.active
        and key.workspace_id == principal.workspace_id
        and key.principal_id == principal.principal_id
        and key.authority_generation == principal.authority_generation
        and key.grant_incarnation == principal.grant.incarnation
        and key.revoked_at is None
        and key.created_at
        <= now
        < min(key.expires_at, key.expires_at if key.retire_at is None else key.retire_at)
        and set(key.scopes) <= set(principal.scope_ceiling)
        and (principal.grant.membership.role != "viewer" or key.scopes == ("runs:read",))
    )


def _bound(current: ServiceKeySet | None, workspace_id: str, principal_id: str) -> ServiceKeySet:
    if (
        current is None
        or current.principal.workspace_id != workspace_id
        or current.principal.principal_id != principal_id
    ):
        raise ContractViolation("not_found", 404)
    return current


def _record(current: ServiceKeySet, credential_id: str) -> ServiceKeyRecord:
    record = next(
        (item for item in current.records if item.key.credential_id == credential_id), None
    )
    if record is None:
        raise ContractViolation("not_found", 404)
    return record


def _view(principal: ServicePrincipalView, record: ServiceKeyRecord, now: int) -> ServiceKeyView:
    return ServiceKeyView(
        key=record.key,
        principal_revision=principal.revision,
        valid_now=service_key_valid(principal, record.key, now=now),
    )


def get_service_principal(
    session_policy: DeploymentSessionPolicy | None,
    policy: ServiceCredentialPolicy | None,
    manager: ServiceManager,
    workspace: WorkspaceAuthority,
    current: ServiceKeySet | None,
    *,
    workspace_id: str,
    principal_id: str,
    now: int,
) -> ServicePrincipalView:
    authorize_service_management(
        session_policy,
        policy,
        manager,
        workspace,
        workspace_id=workspace_id,
        now=now,
        mutation=False,
    )
    return _bound(current, workspace_id, principal_id).principal


def get_service_key(
    session_policy: DeploymentSessionPolicy | None,
    policy: ServiceCredentialPolicy | None,
    manager: ServiceManager,
    workspace: WorkspaceAuthority,
    current: ServiceKeySet | None,
    *,
    workspace_id: str,
    principal_id: str,
    credential_id: str,
    now: int,
) -> ServiceKeyView:
    get_service_principal(
        session_policy,
        policy,
        manager,
        workspace,
        current,
        workspace_id=workspace_id,
        principal_id=principal_id,
        now=now,
    )
    bound = _bound(current, workspace_id, principal_id)
    return _view(bound.principal, _record(bound, credential_id), now)


def _operation(request: ServiceRequest) -> ServiceOperation:
    if isinstance(request, ServiceCreateRequest):
        return "service_create"
    if isinstance(request, ServiceStateRequest):
        return "service_state"
    if isinstance(request, ServiceKeyRotateRequest):
        return "key_rotate"
    if isinstance(request, ServiceKeyIssueRequest):
        return "key_issue"
    if isinstance(request, ServiceKeyRecoverRequest):
        return "key_recover"
    return "key_revoke"


def _path(operation: ServiceOperation, principal_id: str | None, credential_id: str | None) -> None:
    if (principal_id is None) != (operation == "service_create") or (credential_id is not None) != (
        operation in {"key_rotate", "key_recover", "key_revoke"}
    ):
        raise ContractViolation("invalid_request", 422)
    for value in (principal_id, credential_id):
        if value is not None:
            TypeAdapter(Identifier).validate_python(value, strict=True)


def _response(
    current: ServiceKeySet, outcome: ServiceMutationOutcome, *, replayed: bool, now: int
) -> ServiceMutationResponse:
    record = None if outcome.credential_id is None else _record(current, outcome.credential_id)
    return ServiceMutationResponse(
        disposition="replayed" if replayed else "committed",
        outcome=outcome,
        principal=current.principal,
        credential=None if record is None else _view(current.principal, record, now),
    )


def _current_key_follows_snapshot(current: ServiceKeyState, committed: ServiceKeyState) -> bool:
    mutable = {"retire_at", "revoked_at", "retain_until"}
    return (
        current.model_dump(exclude=mutable) == committed.model_dump(exclude=mutable)
        and current.retain_until >= committed.retain_until
        and (committed.revoked_at is None or current.revoked_at == committed.revoked_at)
        and (
            committed.retire_at is None
            or current.retire_at is not None
            and current.retire_at <= committed.retire_at
        )
    )


def _replay(
    policy: ServiceCredentialPolicy,
    manager: ServiceManager,
    request: ServiceRequest,
    operation: ServiceOperation,
    current: ServiceKeySet | None,
    lookup: ServiceReceiptLookup,
    *,
    workspace_id: str,
    principal_id: str | None,
    credential_id: str | None,
    key: str,
    now: int,
) -> ServiceMutationResponse | None:
    if lookup.state == "absent":
        return None
    receipt, audit = lookup.receipt, lookup.audit
    if lookup.state != "committed" or receipt is None or audit is None:
        raise ContractViolation("recovery_required", 409)
    if (
        receipt.workspace_id != workspace_id
        or receipt.actor_id != manager.owner.principal.principal_id
        or receipt.operation != operation
        or receipt.target_principal_id != principal_id
        or receipt.target_credential_id != credential_id
        or receipt.key != key
    ):
        raise ContractViolation("not_found", 404)
    if (
        receipt.actor_generation != manager.owner.principal.generation
        or receipt.actor_grant_incarnation != manager.owner.grant.incarnation
    ):
        raise ContractViolation("forbidden", 403)
    if receipt.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    if receipt.policy_id != policy.policy_id:
        raise ContractViolation("policy_unavailable", 503)
    if now < receipt.outcome.committed_at or now >= receipt.retain_until:
        raise ContractViolation("recovery_required", 409)
    if current is None:
        raise ContractViolation("recovery_required", 409)
    bound = _bound(current, workspace_id, receipt.outcome.principal_id)
    principal = bound.principal
    if (
        principal.authority_generation != receipt.outcome.authority_generation
        or principal.grant.incarnation != receipt.outcome.grant_incarnation
        or (
            operation not in {"service_state", "key_revoke"}
            and (not principal.active or not principal.grant.membership.active)
        )
    ):
        raise ContractViolation("forbidden", 403)
    expected_retention = max(
        (
            _add(receipt.outcome.committed_at, policy.receipt_retention_seconds),
            *(item.expires_at for item in receipt.snapshot.keys),
        )
    )
    if receipt.retain_until != expected_retention:
        raise ContractViolation("recovery_required", 409)
    snapshot = receipt.snapshot
    expected_audit = ServiceAudit(
        event_id=receipt.audit_event_id,
        actor_id=receipt.actor_id,
        actor_generation=receipt.actor_generation,
        actor_grant_incarnation=receipt.actor_grant_incarnation,
        request_sha256=receipt.request_sha256,
        outcome=receipt.outcome,
        snapshot_sha256=message_sha256(snapshot),
    )
    expected_ids = {
        value
        for value in (
            receipt.outcome.credential_id,
            receipt.outcome.replaced_credential_id,
        )
        if value is not None
    }
    if (
        audit != expected_audit
        or principal.revision < snapshot.principal.revision
        or principal.last_key_generation < snapshot.principal.last_key_generation
        or {item.credential_id for item in snapshot.keys} != expected_ids
    ):
        raise ContractViolation("recovery_required", 409)
    for committed in snapshot.keys:
        found = next(
            (
                item.key
                for item in bound.records
                if item.key.credential_id == committed.credential_id
            ),
            None,
        )
        if found is None or not _current_key_follows_snapshot(found, committed):
            raise ContractViolation("recovery_required", 409)
    return _response(bound, receipt.outcome, replayed=True, now=now)


def _updated_set(
    current: ServiceKeySet,
    *,
    principal: ServicePrincipalView | None = None,
    records: tuple[ServiceKeyRecord, ...] | None = None,
) -> ServiceKeySet:
    return ServiceKeySet(
        principal=current.principal if principal is None else principal,
        records=current.records
        if records is None
        else tuple(sorted(records, key=lambda r: r.key.credential_id)),
    )


def _replace(current: ServiceKeySet, updated: ServiceKeyRecord) -> ServiceKeySet:
    return _updated_set(
        current,
        records=tuple(
            updated if record.key.credential_id == updated.key.credential_id else record
            for record in current.records
        ),
    )


def _changed_key(record: ServiceKeyRecord, **changes: int | None) -> ServiceKeyRecord:
    # Revalidate updates; model_copy alone deliberately bypasses validation.
    value = record.key.model_dump() | changes
    return ServiceKeyRecord(
        key=ServiceKeyState.model_validate(value),
        verifier_sha256=record.verifier_sha256,
    )


def _fresh_key(
    policy: ServiceCredentialPolicy,
    manager: ServiceManager,
    current: ServiceKeySet,
    material: ServiceKeyMaterial | None,
    *,
    scopes: tuple[ServicePermission, ...],
    expires_at: int,
    retire_at: int | None,
    now: int,
) -> ServiceKeyRecord:
    if material is None:
        raise ContractViolation("recovery_required", 409)
    if len(current.records) >= policy.max_key_records:
        raise ContractViolation("quota_exceeded", 429)
    if any(
        material.credential_id == record.key.credential_id
        or material.verifier_sha256 == record.verifier_sha256
        for record in current.records
    ):
        raise ContractViolation("incompatible_state", 409)
    principal = current.principal
    key = ServiceKeyState(
        policy_id=policy.policy_id,
        workspace_id=principal.workspace_id,
        principal_id=principal.principal_id,
        credential_id=material.credential_id,
        authority_generation=principal.authority_generation,
        grant_incarnation=principal.grant.incarnation,
        key_generation=_add(principal.last_key_generation, 1),
        scopes=scopes,
        issued_by=manager.owner.principal.principal_id,
        created_at=now,
        expires_at=expires_at,
        retire_at=retire_at,
        revoked_at=None,
        retain_until=max(expires_at, _add(now, policy.receipt_retention_seconds)),
    )
    return ServiceKeyRecord(key=key, verifier_sha256=material.verifier_sha256)


def _new_principal(
    workspace: WorkspaceAuthority,
    request: ServiceCreateRequest,
    new_id: str | None,
) -> ServiceKeySet:
    if new_id is None:
        raise ContractViolation("recovery_required", 409)
    TypeAdapter(Identifier).validate_python(new_id, strict=True)
    if new_id in workspace.active_owner_ids:
        raise ContractViolation("incompatible_state", 409)
    if request.expected_workspace_revision != workspace.workspace.revision:
        raise ContractViolation("incompatible_state", 409)
    return ServiceKeySet(
        principal=ServicePrincipalView(
            workspace_id=workspace.workspace.workspace_id,
            principal_id=new_id,
            display_name=request.display_name,
            active=True,
            revision=0,
            authority_generation=0,
            grant=GrantAuthority(
                membership=Membership(
                    workspace_id=workspace.workspace.workspace_id,
                    principal_id=new_id,
                    role=request.role,
                    active=True,
                    revision=0,
                ),
                incarnation=0,
            ),
            scope_ceiling=request.scope_ceiling,
            last_key_generation=0,
        ),
        records=(),
    )


def _mutate(
    policy: ServiceCredentialPolicy,
    manager: ServiceManager,
    current: ServiceKeySet,
    request: ServiceRequest,
    *,
    credential_id: str | None,
    material: ServiceKeyMaterial | None,
    now: int,
) -> tuple[ServiceKeySet, str | None, str | None]:
    assert not isinstance(request, ServiceCreateRequest)
    principal = current.principal
    if request.expected_revision != principal.revision:
        raise ContractViolation("incompatible_state", 409)
    principal = ServicePrincipalView.model_validate(
        principal.model_dump() | {"revision": _add(principal.revision, 1)}
    )
    if isinstance(request, ServiceStateRequest):
        if material is not None or request.active == current.principal.active:
            raise ContractViolation("incompatible_state", 409)
        principal = ServicePrincipalView.model_validate(
            principal.model_dump()
            | {
                "active": request.active,
                "authority_generation": _add(principal.authority_generation, 1),
            }
        )
        return _updated_set(current, principal=principal), None, None
    target = None if credential_id is None else _record(current, credential_id)
    if isinstance(request, ServiceKeyRevokeRequest):
        assert target is not None
        if material is not None or target.key.revoked_at is not None or now < target.key.created_at:
            raise ContractViolation("incompatible_state", 409)
        revoked_record = _changed_key(
            target,
            revoked_at=now,
            retain_until=max(target.key.retain_until, _add(now, policy.receipt_retention_seconds)),
        )
        return (
            _updated_set(_replace(current, revoked_record), principal=principal),
            target.key.credential_id,
            None,
        )
    if not principal.active or not principal.grant.membership.active:
        raise ContractViolation("forbidden", 403)
    valid = tuple(
        item for item in current.records if service_key_valid(principal, item.key, now=now)
    )
    if len(valid) > 2:
        raise ContractViolation("recovery_required", 409)
    if any(item.key.policy_id != policy.policy_id for item in valid):
        raise ContractViolation("policy_unavailable", 503)
    if target is not None and not service_key_valid(principal, target.key, now=now):
        raise ContractViolation("incompatible_state", 409)
    changed = current
    replaced_id = None
    retirement = None
    if isinstance(request, ServiceKeyRecoverRequest):
        assert target is not None
        scopes, expiry, retirement = target.key.scopes, target.key.expires_at, target.key.retire_at
        changed = _replace(
            changed,
            _changed_key(
                target,
                revoked_at=now,
                retain_until=max(
                    target.key.retain_until, _add(now, policy.receipt_retention_seconds)
                ),
            ),
        )
        replaced_id = target.key.credential_id
    else:
        assert isinstance(request, ServiceKeyIssueRequest)
        scopes, expiry = request.scopes, request.expires_at
        if not now < expiry <= _add(now, policy.max_key_ttl_seconds) or not set(scopes) <= set(
            principal.scope_ceiling
        ):
            raise ContractViolation("invalid_request", 422)
        if isinstance(request, ServiceKeyRotateRequest):
            assert target is not None
            if (
                len(valid) != 1
                or request.overlap_seconds > policy.max_overlap_seconds
                or not set(scopes) <= set(target.key.scopes)
            ):
                raise ContractViolation("incompatible_state", 409)
            retire_at = min(
                target.key.expires_at,
                target.key.expires_at if target.key.retire_at is None else target.key.retire_at,
                _add(now, request.overlap_seconds),
            )
            changed = _replace(
                changed,
                _changed_key(
                    target,
                    retire_at=retire_at,
                    retain_until=max(
                        target.key.retain_until, _add(now, policy.receipt_retention_seconds)
                    ),
                ),
            )
            replaced_id = target.key.credential_id
        elif valid:
            raise ContractViolation("incompatible_state", 409)
    fresh = _fresh_key(
        policy,
        manager,
        changed,
        material,
        scopes=scopes,
        expires_at=expiry,
        retire_at=retirement,
        now=now,
    )
    principal = ServicePrincipalView.model_validate(
        principal.model_dump()
        | {
            "last_key_generation": fresh.key.key_generation,
        }
    )
    updated = _updated_set(changed, principal=principal, records=(*changed.records, fresh))
    if sum(service_key_valid(principal, record.key, now=now) for record in updated.records) > 2:
        raise ContractViolation("incompatible_state", 409)
    return updated, fresh.key.credential_id, replaced_id


def plan_service_operation(
    session_policy: DeploymentSessionPolicy | None,
    policy: ServiceCredentialPolicy | None,
    manager: ServiceManager,
    workspace: WorkspaceAuthority,
    request: ServiceRequest,
    current: ServiceKeySet | None,
    lookup: ServiceReceiptLookup,
    *,
    workspace_id: str,
    principal_id: str | None,
    credential_id: str | None,
    key: str,
    now: int,
    audit_event_id: str,
    new_principal_id: str | None = None,
    material: ServiceKeyMaterial | None = None,
) -> ServicePlan | ServiceMutationResponse:
    """Return a fresh atomic proposal or authorized metadata-only replay.

    The producer performs a complete locked request lookup before calling this
    function. A recovery/expired tombstone must never be presented as absent.
    """
    configured = authorize_service_management(
        session_policy,
        policy,
        manager,
        workspace,
        workspace_id=workspace_id,
        now=now,
        mutation=True,
    )
    TypeAdapter(IdempotencyKey).validate_python(key, strict=True)
    operation = _operation(request)
    _path(operation, principal_id, credential_id)
    replay = _replay(
        configured,
        manager,
        request,
        operation,
        current,
        lookup,
        workspace_id=workspace_id,
        principal_id=principal_id,
        credential_id=credential_id,
        key=key,
        now=now,
    )
    if replay is not None:
        return replay
    TypeAdapter(Identifier).validate_python(audit_event_id, strict=True)
    if isinstance(request, ServiceCreateRequest):
        if current is not None or material is not None:
            raise ContractViolation("incompatible_state", 409)
        updated = _new_principal(workspace, request, new_principal_id)
        workspace = WorkspaceAuthority.model_validate(
            workspace.model_dump()
            | {
                "workspace": workspace.workspace.model_dump()
                | {
                    "revision": _add(workspace.workspace.revision, 1),
                },
            }
        )
        output_key, replaced_key = None, None
    else:
        if new_principal_id is not None:
            raise ContractViolation("invalid_request", 422)
        assert principal_id is not None
        bound = _bound(current, workspace_id, principal_id)
        updated, output_key, replaced_key = _mutate(
            configured,
            manager,
            bound,
            request,
            credential_id=credential_id,
            material=material,
            now=now,
        )
    principal = updated.principal
    outcome = ServiceMutationOutcome(
        operation=operation,
        workspace_id=workspace_id,
        principal_id=principal.principal_id,
        credential_id=output_key,
        replaced_credential_id=replaced_key,
        committed_revision=principal.revision,
        authority_generation=principal.authority_generation,
        grant_incarnation=principal.grant.incarnation,
        committed_at=now,
    )
    affected = {output_key, replaced_key} - {None}
    snapshot = ServiceCommitSnapshot(
        principal=principal,
        keys=tuple(
            record.key for record in updated.records if record.key.credential_id in affected
        ),
    )
    digest = message_sha256(request)
    receipt = ServiceReceipt(
        policy_id=configured.policy_id,
        actor_id=manager.owner.principal.principal_id,
        actor_generation=manager.owner.principal.generation,
        actor_grant_incarnation=manager.owner.grant.incarnation,
        operation=operation,
        workspace_id=workspace_id,
        target_principal_id=principal_id,
        target_credential_id=credential_id,
        key=key,
        request_sha256=digest,
        outcome=outcome,
        snapshot=snapshot,
        audit_event_id=audit_event_id,
        retain_until=max(
            (
                _add(now, configured.receipt_retention_seconds),
                *(item.expires_at for item in snapshot.keys),
            )
        ),
    )
    audit = ServiceAudit(
        event_id=audit_event_id,
        actor_id=receipt.actor_id,
        actor_generation=receipt.actor_generation,
        actor_grant_incarnation=receipt.actor_grant_incarnation,
        request_sha256=digest,
        outcome=outcome,
        snapshot_sha256=message_sha256(snapshot),
    )
    return ServicePlan(
        workspace=workspace,
        key_set=updated,
        receipt=receipt,
        audit=audit,
        response=_response(updated, outcome, replayed=False, now=now),
    )


def validate_initial_key_response(plan: ServicePlan, response: ServiceKeyIssuedResponse) -> None:
    """Check a transient response against its plan, not current authority or SQL commit.

    Only the original handler may use this after independently confirming the
    atomic commit under current authority; retries never enter this path.
    """
    if response.result != plan.response or plan.response.outcome.credential_id is None:
        raise ContractViolation("recovery_required", 409)
    record = _record(plan.key_set, plan.response.outcome.credential_id)
    verifier = base64.urlsafe_b64decode(response.secret.split(".")[2] + "=")
    digest = hashlib.sha256(verifier).hexdigest()
    if not hmac.compare_digest(digest, record.verifier_sha256):
        raise ContractViolation("recovery_required", 409)


def service_error(
    violation: ContractViolation,
    *,
    request_id: str,
    retry_after: int | None = None,
) -> tuple[int, ServiceError, dict[str, str]]:
    statuses = {
        "invalid_request": 422,
        "policy_unavailable": 503,
        "unauthenticated": 401,
        "forbidden": 403,
        "ambiguous_credentials": 400,
        "reauthentication_required": 401,
        "not_found": 404,
        "idempotency_conflict": 409,
        "incompatible_state": 409,
        "recovery_required": 409,
        "quota_exceeded": 429,
        "temporarily_unavailable": 503,
        "rate_limited": 429,
    }
    if statuses.get(violation.code) != violation.status:
        raise ValueError("Unexpected service error code/status")
    headers = {"Cache-Control": "no-store"}
    if violation.code == "reauthentication_required":
        headers["X-Authentication-Action"] = "reauthenticate"
    if violation.status == 429:
        if retry_after is None or type(retry_after) is not int or not 1 <= retry_after <= 86_400:
            raise ValueError("A bounded Retry-After is required for throttled responses")
        headers["Retry-After"] = str(retry_after)
    elif retry_after is not None:
        raise ValueError("Retry-After is only supported on throttled responses")
    error = ServiceError.model_validate({"code": violation.code, "request_id": request_id})
    return violation.status, error, headers
