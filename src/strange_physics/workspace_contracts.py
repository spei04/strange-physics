"""Workspace/membership conformance, not an HTTP service or SQL transaction.

All actor, grant, ownership, receipt and security-event inputs are trusted current
snapshots. Public callers cannot establish those facts by parsing these models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field, TypeAdapter, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import (
    ContractViolation,
    Error,
    IdempotencyScope,
    Membership,
    Operation,
    Permission,
    Role,
    RunLease,
    StoredRequest,
    VerifiedCredential,
    authorize,
    check_idempotency,
)
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.session_contracts import (
    BrowserContext,
    DeploymentSessionPolicy,
    SessionCredential,
    SessionRecord,
    browser_request,
    require_policy,
    server_time,
    validate_session,
    workspace_session_error,
)

if TYPE_CHECKING:
    from strange_physics.run_credential_contracts import ProductAuthority


DisplayName = Annotated[str, Field(min_length=1, max_length=128)]
Cursor = Annotated[str, Field(min_length=1, max_length=512)]
IdempotencyKey = Annotated[str, IdempotencyScope.model_fields["key"]]
ManagementKind = Literal["workspace_create", "member_role", "member_revoke"]


class CreateWorkspaceRequest(Message):
    display_name: DisplayName


class WorkspaceView(Message):
    workspace_id: Identifier
    display_name: DisplayName
    visibility: Literal["private"]
    state: Literal["active", "quarantined"]
    revision: Count


class WorkspacePage(Message):
    items: Annotated[tuple[WorkspaceView, ...], Field(max_length=100)]
    next_cursor: Cursor | None

    @model_validator(mode="after")
    def unique_items(self) -> Self:
        if len({w.workspace_id for w in self.items}) != len(self.items):
            raise ValueError("Workspace page must not repeat identities")
        return self


class MemberPage(Message):
    workspace_id: Identifier
    workspace_revision: Count
    items: Annotated[tuple[Membership, ...], Field(max_length=100)]
    next_cursor: Cursor | None

    @model_validator(mode="after")
    def validate_items(self) -> Self:
        if any(m.workspace_id != self.workspace_id for m in self.items):
            raise ValueError("Member page contains a foreign workspace")
        if len({m.principal_id for m in self.items}) != len(self.items):
            raise ValueError("Member page must not repeat principals")
        return self


class MemberRoleRequest(Message):
    expected_workspace_revision: Count
    expected_membership_revision: Count
    role: Role


class MemberRevokeRequest(Message):
    expected_workspace_revision: Count
    expected_membership_revision: Count


class MemberChangeResult(Message):
    workspace_id: Identifier
    workspace_revision: Count
    membership: Membership

    @model_validator(mode="after")
    def validate_workspace(self) -> Self:
        if self.membership.workspace_id != self.workspace_id:
            raise ValueError("Membership result belongs to another workspace")
        return self


class BrowserActor(Message):
    """Verified human session lookup and HTTP context; never a public body."""

    session: SessionRecord
    credential: SessionCredential
    context: BrowserContext


class WorkspaceCreationGrant(Message):
    """One current server-approved onboarding grant permits one private workspace."""

    grant_id: Identifier
    principal_id: Identifier
    expires_at: Count
    revoked: bool
    consumed_workspace_id: Identifier | None


class WorkspaceAuthority(Message):
    """Complete current owner set from the same locked workspace revision.

    SQL producers establish completeness and currency under the shared lock.
    active_owner_ids counts active human owner membership rows; disabled_owner_ids
    identifies rows whose principals are currently disabled. During security fan-out,
    stored workspace state can lag; composed authorization checks both facts.
    """

    workspace: WorkspaceView
    active_owner_ids: tuple[Identifier, ...]
    disabled_owner_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_owners(self) -> Self:
        if tuple(sorted(set(self.active_owner_ids))) != self.active_owner_ids:
            raise ValueError("Owner identities must be unique and sorted")
        if tuple(sorted(set(self.disabled_owner_ids))) != self.disabled_owner_ids or not set(
            self.disabled_owner_ids
        ).issubset(self.active_owner_ids):
            raise ValueError("Disabled owners must be a unique sorted subset of membership owners")
        if self.workspace.state == "active" and not self.active_owner_ids:
            raise ValueError("An active workspace requires a current active owner")
        return self


class PrincipalStatus(Message):
    """Current verified human app-principal state, bound to its stable identity."""

    kind: Literal["human"]
    principal_id: Identifier
    active: bool


class SecurityRevocationAuthority(Message):
    """Current verified internal permission; never supplied by the public caller."""

    actor_id: Identifier
    authorization_id: Identifier
    workspace_id: Identifier
    permission: Literal["members:security-revoke"]
    expires_at: Count
    revoked: bool


class SecurityRevocation(Message):
    """Verified internal event, never an elective HTTP reason or a caller credential."""

    event_id: Identifier
    actor_id: Identifier
    authorization_id: Identifier
    workspace_id: Identifier
    principal_id: Identifier


class ManagementReceipt(Message):
    """Immutable receipt identity; stored response must be bound to this outcome."""

    principal_id: Identifier
    operation: ManagementKind
    workspace_id: Identifier | None
    target_principal_id: Identifier | None
    grant_id: Identifier | None
    key: IdempotencyKey
    request_sha256: Digest
    outcome_id: Identifier

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.operation == "workspace_create":
            if self.workspace_id is not None or self.target_principal_id is not None:
                raise ValueError("Creation is scoped to the caller before workspace allocation")
            if self.grant_id is None:
                raise ValueError("Creation receipt binds its server onboarding grant")
        elif (
            self.workspace_id is None
            or self.target_principal_id is None
            or self.grant_id is not None
        ):
            raise ValueError("Membership receipt requires workspace and target, without grant")
        return self


def validate_human_actor(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    *,
    now: int,
    mutation: bool,
) -> DeploymentSessionPolicy:
    configured = require_policy(policy)
    browser_request(configured, actor.context, mutation=mutation)
    if not actor.context.has_session_cookie:
        raise ContractViolation("unauthenticated", 401)
    validate_session(configured, actor.session, actor.credential, now=now)
    if mutation and now - actor.session.authenticated_at >= configured.recent_auth_seconds:
        raise ContractViolation("reauthentication_required", 401)
    return configured


def management_session_error(
    violation: ContractViolation, *, request_id: str
) -> tuple[int, Error, dict[str, str]]:
    """Explicit freshness signal; other ID-A failures retain their control mapping."""
    if violation.code == "reauthentication_required":
        if violation.status != 401:
            raise ValueError("Unexpected freshness status")
        return (
            401,
            Error(
                code="unauthenticated",
                message="Recent authentication required.",
                request_id=request_id,
                retryable=False,
                operation_id=None,
            ),
            {"X-Authentication-Action": "reauthenticate"},
        )
    status, error = workspace_session_error(violation, request_id=request_id)
    return status, error, {}


def enabled_owners(authority: WorkspaceAuthority) -> frozenset[str]:
    return frozenset(authority.active_owner_ids).difference(authority.disabled_owner_ids)


def workspace_status(authority: WorkspaceAuthority) -> WorkspaceView:
    """Safe current status projection, including security fan-out before state persistence."""
    if not enabled_owners(authority):
        return authority.workspace.model_copy(update={"state": "quarantined"})
    return authority.workspace


def _member_binding(authority: WorkspaceAuthority, member: Membership) -> None:
    if member.workspace_id != authority.workspace.workspace_id:
        raise ContractViolation("not_found", 404)
    is_owner = member.active and member.role == "owner"
    if is_owner != (member.principal_id in authority.active_owner_ids):
        raise ContractViolation("incompatible_state", 409)


def authorize_management(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    authority: WorkspaceAuthority,
    membership: Membership,
    *,
    workspace_id: str,
    now: int,
    owner_required: bool,
    mutation: bool,
) -> None:
    """Recheck before every read, mutation and receipt lookup, under the current snapshot."""
    validate_human_actor(policy, actor, now=now, mutation=mutation)
    if (
        authority.workspace.workspace_id != workspace_id
        or membership.workspace_id != workspace_id
        or membership.principal_id != actor.session.principal_id
    ):
        raise ContractViolation("not_found", 404)
    if not membership.active or (owner_required and membership.role != "owner"):
        raise ContractViolation("forbidden", 403)
    _member_binding(authority, membership)
    if membership.principal_id in authority.disabled_owner_ids:
        raise ContractViolation("forbidden", 403)
    # Only safe workspace/self status reads are permitted through quarantine.
    if (authority.workspace.state != "active" or not enabled_owners(authority)) and (
        mutation or owner_required
    ):
        raise ContractViolation("forbidden", 403)


def _creation_authority(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    grant: WorkspaceCreationGrant,
    *,
    now: int,
) -> None:
    validate_human_actor(policy, actor, now=now, mutation=True)
    if grant.principal_id != actor.session.principal_id:
        raise ContractViolation("forbidden", 403)
    if grant.revoked or now >= grant.expires_at:
        raise ContractViolation("forbidden", 403)


def _receipt(
    stored: ManagementReceipt | None,
    *,
    principal_id: str,
    operation: ManagementKind,
    workspace_id: str | None,
    target_principal_id: str | None,
    grant_id: str | None,
    key: str,
    request: Message,
) -> str | None:
    TypeAdapter(IdempotencyKey).validate_python(key, strict=True)
    if stored is None:
        return None
    expected = {
        "principal_id": principal_id,
        "operation": operation,
        "workspace_id": workspace_id,
        "target_principal_id": target_principal_id,
        "grant_id": grant_id,
        "key": key,
        "request_sha256": message_sha256(request),
    }
    if stored.model_dump(exclude={"outcome_id"}) != expected:
        raise ContractViolation("idempotency_conflict", 409)
    return stored.outcome_id


def check_creation_replay(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    grant: WorkspaceCreationGrant,
    request: CreateWorkspaceRequest,
    *,
    key: str,
    stored: ManagementReceipt | None,
    created: WorkspaceAuthority | None,
    membership: Membership | None,
    now: int,
) -> str | None:
    _creation_authority(policy, actor, grant, now=now)
    # A creation receipt discloses a workspace: recheck its current visibility first.
    if stored is not None:
        if created is None or membership is None:
            raise ContractViolation("not_found", 404)
        authorize_management(
            policy,
            actor,
            created,
            membership,
            workspace_id=grant.consumed_workspace_id or "",
            now=now,
            owner_required=True,
            mutation=True,
        )
        if stored.outcome_id != grant.consumed_workspace_id:
            raise ContractViolation("incompatible_state", 409)
    return _receipt(
        stored,
        principal_id=actor.session.principal_id,
        operation="workspace_create",
        workspace_id=None,
        target_principal_id=None,
        grant_id=grant.grant_id,
        key=key,
        request=request,
    )


def check_member_replay(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    authority: WorkspaceAuthority,
    membership: Membership,
    request: MemberRoleRequest | MemberRevokeRequest,
    *,
    workspace_id: str,
    target_principal_id: str,
    key: str,
    stored: ManagementReceipt | None,
    now: int,
) -> str | None:
    authorize_management(
        policy,
        actor,
        authority,
        membership,
        workspace_id=workspace_id,
        now=now,
        owner_required=True,
        mutation=True,
    )
    # Do not reapply original target/workspace CAS before returning an exact receipt.
    return _receipt(
        stored,
        principal_id=actor.session.principal_id,
        operation="member_role" if isinstance(request, MemberRoleRequest) else "member_revoke",
        workspace_id=workspace_id,
        target_principal_id=target_principal_id,
        grant_id=None,
        key=key,
        request=request,
    )


def validate_workspace_creation(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    grant: WorkspaceCreationGrant,
    consumed_grant: WorkspaceCreationGrant,
    request: CreateWorkspaceRequest,
    created: WorkspaceAuthority,
    initial_member: Membership,
    *,
    now: int,
) -> None:
    """Fresh admission only, after authorized receipt lookup; one atomic proposal."""
    _creation_authority(policy, actor, grant, now=now)
    if grant.consumed_workspace_id is not None:
        raise ContractViolation("incompatible_state", 409)
    workspace = created.workspace
    expected_grant = grant.model_dump() | {"consumed_workspace_id": workspace.workspace_id}
    if (
        consumed_grant.model_dump() != expected_grant
        or workspace.display_name != request.display_name
        or workspace.state != "active"
        or workspace.revision != 0
        or created.active_owner_ids != (actor.session.principal_id,)
        or created.disabled_owner_ids
        or initial_member
        != Membership(
            workspace_id=workspace.workspace_id,
            principal_id=actor.session.principal_id,
            role="owner",
            active=True,
            revision=0,
        )
    ):
        raise ContractViolation("incompatible_state", 409)


def _validate_member_proposal(
    before: WorkspaceAuthority,
    after: WorkspaceAuthority,
    target: Membership,
    updated: Membership,
    *,
    role: Role,
    active: bool,
    security: bool,
) -> None:
    _member_binding(before, target)
    expected_member = target.model_dump() | {
        "role": role,
        "active": active,
        "revision": target.revision + 1,
    }
    owners = set(before.active_owner_ids)
    owners.discard(target.principal_id)
    if active and role == "owner":
        owners.add(target.principal_id)
    disabled = set(before.disabled_owner_ids).intersection(owners)
    if not owners.difference(disabled) and not security:
        raise ContractViolation("incompatible_state", 409)
    state = (
        "quarantined"
        if not owners.difference(disabled) or before.workspace.state == "quarantined"
        else "active"
    )
    expected_workspace = before.workspace.model_dump() | {
        "revision": before.workspace.revision + 1,
        "state": state,
    }
    if (
        updated.model_dump() != expected_member
        or after.workspace.model_dump() != expected_workspace
        or after.active_owner_ids != tuple(sorted(owners))
        or after.disabled_owner_ids != tuple(sorted(disabled))
    ):
        raise ContractViolation("incompatible_state", 409)


def validate_member_change(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    before: WorkspaceAuthority,
    after: WorkspaceAuthority,
    actor_membership: Membership,
    target: Membership,
    updated: Membership,
    request: MemberRoleRequest | MemberRevokeRequest,
    *,
    workspace_id: str,
    target_principal_id: str,
    target_principal: PrincipalStatus,
    now: int,
) -> None:
    """Fresh elective mutation only; receipts are checked before these CAS preconditions."""
    authorize_management(
        policy,
        actor,
        before,
        actor_membership,
        workspace_id=workspace_id,
        now=now,
        owner_required=True,
        mutation=True,
    )
    if (
        target.workspace_id != workspace_id
        or target.principal_id != target_principal_id
        or target_principal.principal_id != target.principal_id
    ):
        raise ContractViolation("not_found", 404)
    if target.principal_id == actor_membership.principal_id and target != actor_membership:
        raise ContractViolation("incompatible_state", 409)
    if (
        request.expected_workspace_revision != before.workspace.revision
        or request.expected_membership_revision != target.revision
        or not target.active
        or (isinstance(request, MemberRoleRequest) and not target_principal.active)
    ):
        raise ContractViolation("incompatible_state", 409)
    if target.role == "owner" and target_principal.active != (
        target.principal_id not in before.disabled_owner_ids
    ):
        raise ContractViolation("incompatible_state", 409)
    _validate_member_proposal(
        before,
        after,
        target,
        updated,
        role=request.role if isinstance(request, MemberRoleRequest) else target.role,
        active=isinstance(request, MemberRoleRequest),
        security=False,
    )


def validate_security_revocation(
    authorization: SecurityRevocationAuthority,
    event: SecurityRevocation,
    before: WorkspaceAuthority,
    after: WorkspaceAuthority,
    target: Membership,
    updated: Membership,
    *,
    now: int,
) -> None:
    """Trusted security revocation proceeds without an elective owner's/session's consent.

    Event authenticity, current principal disablement, dedup and all-workspace
    fan-out are adapter obligations. This predicate cannot verify an event.
    """
    server_time(now)
    if authorization.revoked or now >= authorization.expires_at:
        raise ContractViolation("forbidden", 403)
    if (
        authorization.workspace_id != event.workspace_id
        or authorization.actor_id != event.actor_id
        or authorization.authorization_id != event.authorization_id
        or event.workspace_id != before.workspace.workspace_id
        or target.workspace_id != event.workspace_id
        or target.principal_id != event.principal_id
    ):
        raise ContractViolation("not_found", 404)
    if not target.active:
        raise ContractViolation("incompatible_state", 409)
    _validate_member_proposal(
        before,
        after,
        target,
        updated,
        role=target.role,
        active=False,
        security=True,
    )


def validate_product_workspace(
    workspace: WorkspaceAuthority, workspace_id: str, membership: Membership
) -> None:
    """Incomplete workspace fence; callers still need current identity and permission."""
    if workspace.workspace.workspace_id != workspace_id:
        raise ContractViolation("not_found", 404)
    _member_binding(workspace, membership)
    if (
        workspace.workspace.state != "active"
        or not enabled_owners(workspace)
        or membership.principal_id in workspace.disabled_owner_ids
    ):
        raise ContractViolation("forbidden", 403)


def authorize_product(
    workspace: WorkspaceAuthority,
    credential: VerifiedCredential,
    membership: Membership,
    *,
    authority: ProductAuthority,
    permission: Permission,
    workspace_id: str,
    now: int,
    run_id: str | None = None,
    lease: RunLease | None = None,
) -> None:
    """Mandatory composed product boundary; caller provides CURRENT workspace state."""
    from strange_physics.product_authority import validate_product_authority

    validate_product_authority(
        authority,
        credential,
        membership,
        permission=permission,
        workspace_id=workspace_id,
        now=now,
        run_id=run_id,
        lease=lease,
    )
    authorize(
        credential,
        membership,
        permission=permission,
        workspace_id=workspace_id,
        now=now,
        run_id=run_id,
        lease=lease,
    )
    validate_product_workspace(workspace, workspace_id, membership)


def check_product_idempotency(
    workspace: WorkspaceAuthority,
    credential: VerifiedCredential,
    membership: Membership,
    scope: IdempotencyScope,
    request: Message,
    stored: StoredRequest | None,
    *,
    authority: ProductAuthority,
    now: int,
    lease: RunLease | None = None,
) -> Operation | None:
    """Never return an existing operation or admit new work from a quarantined workspace."""
    from strange_physics.product_authority import validate_product_authority

    permissions: dict[str, Permission] = {
        "run_creation": "runs:create",
        "experiment": "experiments:write",
        "cancellation": "runs:cancel",
        "model_submission": "models:write",
    }
    validate_product_authority(
        authority,
        credential,
        membership,
        permission=permissions[scope.kind],
        workspace_id=scope.workspace_id,
        now=now,
        run_id=scope.resource_id if credential.kind == "run" else None,
        lease=lease,
    )
    # Authorize and bind the complete scope before inspecting any stored outcome.
    validate_product_workspace(workspace, scope.workspace_id, membership)
    check_idempotency(credential, membership, scope, request, None, now=now, lease=lease)
    return check_idempotency(
        credential,
        membership,
        scope,
        request,
        stored,
        now=now,
        lease=lease,
    )


WORKSPACE_MODELS: tuple[type[Message], ...] = (
    CreateWorkspaceRequest,
    WorkspaceView,
    WorkspacePage,
    MemberPage,
    MemberRoleRequest,
    MemberRevokeRequest,
    MemberChangeResult,
    BrowserActor,
    WorkspaceCreationGrant,
    WorkspaceAuthority,
    SecurityRevocationAuthority,
    PrincipalStatus,
    SecurityRevocation,
    ManagementReceipt,
)
PUBLIC_MODELS: tuple[type[Message], ...] = (
    CreateWorkspaceRequest,
    WorkspaceView,
    WorkspacePage,
    Membership,
    MemberPage,
    MemberRoleRequest,
    MemberRevokeRequest,
    MemberChangeResult,
)


def workspace_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in WORKSPACE_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/workspace.schema.json"
    schema["x-contract-status"] = "ID-B/B1; invitations/linking and full SP-01.b remain incomplete"
    schema["x-public-models"] = [model.__name__ for model in PUBLIC_MODELS]
    schema["description"] = (
        "Private workspace and membership contracts, not handlers, SQL isolation or "
        "verified authority. Internal snapshots are never public request inputs."
    )
    return schema
