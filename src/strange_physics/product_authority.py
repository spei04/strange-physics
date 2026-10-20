"""Mandatory current-authority composition for product admission and replay.

Inputs are independently verified, complete current transactional projections.
These predicates do not verify tokens, acquire locks or authorize cached grace.
"""

from __future__ import annotations

from strange_physics.control_contracts import (
    READ_PERMISSIONS,
    ContractViolation,
    Membership,
    Permission,
    RunLease,
    RunView,
    VerifiedCredential,
)
from strange_physics.run_credential_contracts import (
    HumanProductAuthority,
    ProductAuthority,
    RunAuthorityState,
    RunCredentialPolicy,
    RunCredentialRecord,
    RunOwnership,
    WorkerScopes,
)
from strange_physics.service_credentials import service_key_valid
from strange_physics.session_contracts import browser_request, require_policy, server_time
from strange_physics.workspace_contracts import (
    WorkspaceAuthority,
    authorize_product,
    validate_human_actor,
)


def validate_run_authority(current: RunAuthorityState, *, now: int) -> None:
    """Durable owner and current running lease, independent of any creator leaf key."""
    server_time(now)
    ownership = current.credentials.ownership
    owner, run, lease = current.owner, current.run, current.lease
    if (
        not owner.principal.active
        or not owner.grant.membership.active
        or owner.principal.generation != ownership.principal_generation
        or owner.grant.incarnation != ownership.grant_incarnation
        or now < ownership.created_at
        or now >= ownership.run_deadline
        or lease.run_deadline != ownership.run_deadline
        or lease.revoked
        or now >= lease.expires_at
    ):
        raise ContractViolation("forbidden", 403)
    if run.status != "running" or lease.status != run.status:
        raise ContractViolation("incompatible_state", 409)


def run_key_valid(
    current: RunAuthorityState,
    record: RunCredentialRecord,
    policy: RunCredentialPolicy,
    *,
    now: int,
) -> bool:
    """Current generation/lease/lifetime only; not bearer verification or permission."""
    try:
        validate_run_authority(current, now=now)
    except ContractViolation:
        return False
    claims, state, lease = record.claims, current.credentials, current.lease
    return (
        record in state.records
        and state.current_credential_id == claims.credential_id
        and state.last_generation == claims.generation
        and claims.policy_id == policy.policy_id
        and claims.issuer == policy.issuer
        and claims.audience == policy.audience
        and claims.attempt_id == lease.attempt_id
        and claims.lease_epoch == lease.epoch
        and claims.issued_at <= now < min(claims.expires_at, lease.expires_at)
        and claims.expires_at - claims.issued_at <= policy.max_ttl_seconds
        and record.revoked_at is None
    )


def validate_human_product_identity(
    authority: HumanProductAuthority, *, mutation: bool, now: int
) -> Membership:
    """Incomplete current browser identity seam, without product permission/workspace checks."""
    server_time(now)
    configured = require_policy(authority.policy)
    browser_request(configured, authority.actor.context, mutation=mutation)
    validate_human_actor(configured, authority.actor, now=now, mutation=False)
    owner = authority.owner
    if (
        not owner.principal.active
        or authority.session_principal_generation != owner.principal.generation
    ):
        raise ContractViolation("unauthenticated", 401)
    return owner.grant.membership


def validate_product_authority(
    authority: ProductAuthority,
    credential: VerifiedCredential,
    membership: Membership,
    *,
    permission: Permission,
    workspace_id: str,
    now: int,
    run_id: str | None = None,
    lease: RunLease | None = None,
) -> None:
    """Check all duplicate projections before the lower-level permission primitive."""
    server_time(now)
    if authority.kind != credential.kind:
        raise ContractViolation("unauthenticated", 401)
    if authority.kind == "user":
        current_member = validate_human_product_identity(
            authority, mutation=permission not in READ_PERMISSIONS, now=now
        )
        session = authority.actor.session
        if (
            credential.credential_id != session.session_id
            or credential.principal_id != session.principal_id
            or credential.expires_at != session.absolute_expires_at
            or credential.revoked != session.revoked
        ):
            raise ContractViolation("unauthenticated", 401)
    elif authority.kind == "service":
        if authority.policy is None:
            raise ContractViolation("policy_unavailable", 503)
        principal = authority.current.principal
        record = next(
            (
                r
                for r in authority.current.records
                if r.key.credential_id == authority.credential_id
            ),
            None,
        )
        if (
            record is None
            or credential.credential_id != authority.credential_id
            or record.key.policy_id != authority.policy.policy_id
            or not service_key_valid(principal, record.key, now=now)
            or credential.principal_id != principal.principal_id
            or credential.workspace_id != principal.workspace_id
            or set(credential.scopes) != set(record.key.scopes)
            or credential.expires_at != record.key.expires_at
            or credential.revoked != (record.key.revoked_at is not None)
        ):
            raise ContractViolation("unauthenticated", 401)
        if permission not in principal.scope_ceiling:
            raise ContractViolation("forbidden", 403)
        current_member = principal.grant.membership
    else:
        if authority.policy is None:
            raise ContractViolation("policy_unavailable", 503)
        current = authority.current
        validate_run_authority(current, now=now)
        claims = authority.verified_claims
        run_record = next(
            (
                r
                for r in current.credentials.records
                if r.claims.credential_id == claims.credential_id
            ),
            None,
        )
        if (
            run_record is None
            or run_record.claims != claims
            or not run_key_valid(current, run_record, authority.policy, now=now)
            or credential.issuer != claims.issuer
            or credential.subject != claims.principal_id
            or credential.principal_id != claims.principal_id
            or credential.credential_id != claims.credential_id
            or credential.workspace_id != claims.workspace_id
            or set(credential.scopes) != set(claims.scopes)
            or credential.expires_at != claims.expires_at
            or credential.revoked
            or credential.run_id != claims.run_id
            or credential.attempt_id != claims.attempt_id
            or credential.lease_epoch != claims.lease_epoch
        ):
            raise ContractViolation("unauthenticated", 401)
        if lease != current.lease:
            raise ContractViolation("forbidden", 403)
        if run_id != current.run.run_id:
            raise ContractViolation("not_found", 404)
        current_member = current.owner.grant.membership
    if current_member != membership or current_member.workspace_id != workspace_id:
        raise ContractViolation("not_found", 404)


def admit_run_ownership(
    workspace: WorkspaceAuthority,
    credential: VerifiedCredential,
    membership: Membership,
    run: RunView,
    *,
    authority: ProductAuthority,
    run_deadline: int,
    worker_scopes: WorkerScopes,
    now: int,
) -> RunOwnership:
    """Original admission only; deadline/scopes come from fixed server run policy.

    Persist this ownership with the original run and idempotency receipt. Never
    regenerate it from a retry's leaf credential or from a later lease attempt.
    """
    authorize_product(
        workspace,
        credential,
        membership,
        authority=authority,
        permission="runs:create",
        workspace_id=run.workspace_id,
        now=now,
    )
    if (
        authority.kind == "run"
        or run.status != "queued"
        or run.revision != 0
        or run.experiments_accepted != 0
    ):
        raise ContractViolation("incompatible_state", 409)
    if authority.kind == "user":
        owner = authority.owner
        kind = owner.principal.kind
        generation = owner.principal.generation
        incarnation = owner.grant.incarnation
    else:
        kind = "service"
        generation = authority.current.principal.authority_generation
        incarnation = authority.current.principal.grant.incarnation
    return RunOwnership(
        workspace_id=run.workspace_id,
        run_id=run.run_id,
        principal_id=credential.principal_id,
        principal_kind=kind,
        principal_generation=generation,
        grant_incarnation=incarnation,
        created_at=now,
        run_deadline=run_deadline,
        scopes=worker_scopes,
        created_by_credential_id=credential.credential_id,
    )
