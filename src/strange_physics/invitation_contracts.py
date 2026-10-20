"""Invitation conformance only: no email delivery, identity verification or SQL.

Adapters supply trusted current records. Parsing them never establishes authority.
Plaintext tokens are transient and must not enter receipts or logs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, Field, SecretStr, TypeAdapter, WithJsonSchema, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation, Membership, Role
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.session_contracts import (
    DeploymentSessionPolicy,
    ResponseSecret,
    Seconds,
    server_time,
)
from strange_physics.workspace_contracts import (
    BrowserActor,
    IdempotencyKey,
    PrincipalStatus,
    WorkspaceAuthority,
    authorize_management,
    enabled_owners,
    validate_human_actor,
)

ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_{" + chr(96) + r"|}~-]+"
LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
EMAIL_PATTERN = rf"^{ATOM}(?:\.{ATOM})*@{LABEL}(?:\.{LABEL})+$"
TOKEN_PATTERN = r"^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$"


def canonical_email(value: str) -> str:
    if not value.isascii() or re.fullmatch(EMAIL_PATTERN, value) is None:
        raise ValueError("Unsupported email address profile")
    local, domain = value.rsplit("@", 1)
    if len(local) > 64 or len(value) > 254 or any(len(label) > 63 for label in domain.split(".")):
        raise ValueError("Unsupported email address length")
    return local + "@" + domain.lower()


Email = Annotated[
    str,
    Field(
        min_length=3,
        max_length=254,
        pattern=EMAIL_PATTERN,
        json_schema_extra={"not": {"pattern": "[^!-~]"}},
    ),
    AfterValidator(canonical_email),
]


def token_bytes(token: SecretStr) -> bytes:
    raw = token.get_secret_value()
    if re.fullmatch(TOKEN_PATTERN, raw) is None:
        raise ValueError("Invalid invitation token encoding")
    decoded = base64.urlsafe_b64decode(raw + "=")
    if len(decoded) != 32 or base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=") != raw:
        raise ValueError("Noncanonical invitation token encoding")
    return decoded


def canonical_token(token: SecretStr) -> SecretStr:
    token_bytes(token)
    return token


Token = Annotated[
    SecretStr,
    Field(min_length=43, max_length=43),
    AfterValidator(canonical_token),
    WithJsonSchema(
        {
            "type": "string",
            "minLength": 43,
            "maxLength": 43,
            "pattern": TOKEN_PATTERN,
            "not": {"pattern": "[^A-Za-z0-9_-]"},
            "writeOnly": True,
        }
    ),
]
IssuedToken = Annotated[
    ResponseSecret,
    AfterValidator(canonical_token),
    WithJsonSchema(
        {
            "type": "string",
            "minLength": 43,
            "maxLength": 43,
            "pattern": TOKEN_PATTERN,
            "not": {"pattern": "[^A-Za-z0-9_-]"},
            "readOnly": True,
        }
    ),
]


class InvitationPolicy(Message):
    policy_id: Identifier
    token_lifetime_seconds: Seconds
    email_assertion_max_age_seconds: Seconds
    retry_window_seconds: Seconds
    receipt_retention_seconds: Seconds
    max_pending_per_workspace: Annotated[int, Field(ge=1, le=10000)]
    create_attempt_limit: Annotated[int, Field(ge=1, le=10000)]
    redeem_attempt_limit: Annotated[int, Field(ge=1, le=10000)]
    attempt_window_seconds: Seconds

    @model_validator(mode="after")
    def sufficient_retention(self) -> Self:
        if self.receipt_retention_seconds < self.token_lifetime_seconds + self.retry_window_seconds:
            raise ValueError("Receipt retention must cover lifetime plus retry window")
        return self


class CreateInvitationRequest(Message):
    recipient_email: Email
    role: Role
    expected_workspace_revision: Count


class RevokeInvitationRequest(Message):
    expected_invitation_revision: Count


class RedeemInvitationRequest(Message):
    token: Token


class InvitationRecord(Message):
    """Trusted immutable grant plus serialized resolution; never plaintext token."""

    invitation_id: Identifier
    policy_id: Identifier
    workspace_id: Identifier
    inviter_principal_id: Identifier
    recipient_email: Email
    role: Role
    created_at: Count
    expires_at: Count
    token_sha256: Digest
    revision: Count
    state: Literal["pending", "accepted", "revoked"]
    accepted_principal_id: Identifier | None
    resolved_at: Count | None

    @model_validator(mode="after")
    def resolution(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("Invitation must have positive lifetime")
        if self.state == "pending":
            if self.resolved_at is not None or self.accepted_principal_id is not None:
                raise ValueError("Pending invitation cannot contain a resolution")
        elif self.resolved_at is None or self.resolved_at < self.created_at:
            raise ValueError("Resolved invitation requires its server resolution time")
        if (self.accepted_principal_id is not None) != (self.state == "accepted"):
            raise ValueError("Only accepted invitations bind a recipient principal")
        if self.state == "accepted" and self.resolved_at is not None:
            if self.resolved_at >= self.expires_at:
                raise ValueError("Acceptance must precede expiry")
        return self


class InvitationView(Message):
    """Owner-visible metadata; no token/digest/upstream identity."""

    invitation_id: Identifier
    workspace_id: Identifier
    inviter_principal_id: Identifier
    recipient_email: Email
    role: Role
    created_at: Count
    expires_at: Count
    revision: Count
    state: Literal["pending", "accepted", "revoked", "expired"]
    accepted_principal_id: Identifier | None
    resolved_at: Count | None


class InvitationPage(Message):
    workspace_id: Identifier
    items: Annotated[tuple[InvitationView, ...], Field(max_length=100)]
    next_cursor: Annotated[str, Field(min_length=1, max_length=512)] | None

    @model_validator(mode="after")
    def tenant_page(self) -> Self:
        if any(item.workspace_id != self.workspace_id for item in self.items):
            raise ValueError("Invitation page contains another workspace")
        if len({item.invitation_id for item in self.items}) != len(self.items):
            raise ValueError("Invitation page repeats an identity")
        return self


class InvitationIssued(Message):
    invitation: InvitationView
    token: IssuedToken

    @model_validator(mode="after")
    def pending_only(self) -> Self:
        if self.invitation.state != "pending":
            raise ValueError("Only fresh pending issuance can contain a token")
        return self


class RedemptionResult(Message):
    invitation_id: Identifier
    workspace_id: Identifier
    membership: Membership

    @model_validator(mode="after")
    def tenant_result(self) -> Self:
        if self.membership.workspace_id != self.workspace_id or not self.membership.active:
            raise ValueError("Redemption requires current active membership in its workspace")
        return self


class CurrentRecipientIdentity(Message):
    """Current human identity mapping, checked against the session principal."""

    principal: PrincipalStatus
    provider_id: Identifier
    issuer: Annotated[str, Field(min_length=1, max_length=2048)]
    subject: Annotated[str, Field(min_length=1, max_length=512)]
    identity_active: bool


class VerifiedEmailAssertion(Message):
    """Verified upstream evidence; issued_at is upstream time, not local parsing."""

    provider_id: Identifier
    issuer: Annotated[str, Field(min_length=1, max_length=2048)]
    subject: Annotated[str, Field(min_length=1, max_length=512)]
    session_id: Identifier
    session_generation: Count
    email: Email
    email_verified: bool
    issued_at: Count
    expires_at: Count
    verified_at: Count
    assertion_sha256: Digest

    @model_validator(mode="after")
    def lifetime(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("Email assertion has no positive upstream lifetime")
        return self


class RedemptionContext(Message):
    actor: BrowserActor
    workspace: WorkspaceAuthority
    inviter_membership: Membership
    inviter_principal: PrincipalStatus
    recipient_identity: CurrentRecipientIdentity
    email_assertion: VerifiedEmailAssertion
    recipient_membership: Membership | None


InviteOperation = Literal["issue", "revoke", "redeem"]


class InvitationReceipt(Message):
    """Safe lookup/result identity; never plaintext response bytes."""

    principal_id: Identifier
    operation: InviteOperation
    workspace_id: Identifier
    target_invitation_id: Identifier | None
    key: IdempotencyKey
    request_sha256: Digest
    outcome_invitation_id: Identifier

    @model_validator(mode="after")
    def target_binding(self) -> Self:
        if self.operation == "issue":
            if self.target_invitation_id is not None:
                raise ValueError("Issue key precedes invitation allocation")
        elif self.target_invitation_id != self.outcome_invitation_id:
            raise ValueError("Resolution receipt must bind its target invitation")
        return self


def invitation_token_sha256(token: SecretStr) -> str:
    return hashlib.sha256(b"strange-physics.invitation-token.v1\0" + token_bytes(token)).hexdigest()


def redemption_request_sha256(request: RedeemInvitationRequest) -> str:
    # SecretStr's serialized mask is not the identity of this request.
    value = {"token_sha256": invitation_token_sha256(request.token)}
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def invitation_view(record: InvitationRecord, *, now: int) -> InvitationView:
    server_time(now)
    data = record.model_dump(mode="json", exclude={"policy_id", "token_sha256"})
    if record.state == "pending" and now >= record.expires_at:
        data["state"] = "expired"
    return InvitationView.model_validate(data)


def require_invitation_policy(policy: InvitationPolicy | None) -> InvitationPolicy:
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    return policy


def _receipt(
    stored: InvitationReceipt | None,
    *,
    principal_id: str,
    operation: InviteOperation,
    workspace_id: str,
    target: str | None,
    key: str,
    digest: str,
) -> str | None:
    TypeAdapter(IdempotencyKey).validate_python(key, strict=True)
    if stored is None:
        return None
    expected = dict(
        principal_id=principal_id,
        operation=operation,
        workspace_id=workspace_id,
        target_invitation_id=target,
        key=key,
        request_sha256=digest,
    )
    if stored.model_dump(exclude={"outcome_invitation_id"}) != expected:
        raise ContractViolation("idempotency_conflict", 409)
    return stored.outcome_invitation_id


def authorize_invitation_owner(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    workspace: WorkspaceAuthority,
    membership: Membership,
    *,
    workspace_id: str,
    now: int,
    mutation: bool,
) -> None:
    authorize_management(
        policy,
        actor,
        workspace,
        membership,
        workspace_id=workspace_id,
        now=now,
        owner_required=True,
        mutation=mutation,
    )


def check_owner_invitation_replay(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    workspace: WorkspaceAuthority,
    membership: Membership,
    request: CreateInvitationRequest | RevokeInvitationRequest,
    *,
    workspace_id: str,
    invitation_id: str | None,
    key: str,
    stored: InvitationReceipt | None,
    record: InvitationRecord | None,
    now: int,
) -> InvitationView | None:
    authorize_invitation_owner(
        policy, actor, workspace, membership, workspace_id=workspace_id, now=now, mutation=True
    )
    issuing = isinstance(request, CreateInvitationRequest)
    if issuing != (invitation_id is None):
        raise ContractViolation("invalid_request", 422)
    outcome = _receipt(
        stored,
        principal_id=actor.session.principal_id,
        operation="issue" if issuing else "revoke",
        workspace_id=workspace_id,
        target=invitation_id,
        key=key,
        digest=message_sha256(request),
    )
    if outcome is None:
        return None
    if record is None or record.invitation_id != outcome or record.workspace_id != workspace_id:
        raise ContractViolation("not_found", 404)
    if issuing and record.inviter_principal_id != actor.session.principal_id:
        raise ContractViolation("incompatible_state", 409)
    if not issuing and record.state != "revoked":
        raise ContractViolation("incompatible_state", 409)
    # CURRENT safe metadata only: no token recovery or delivery acknowledgment.
    return invitation_view(record, now=now)


def validate_invitation_issue(
    session_policy: DeploymentSessionPolicy | None,
    invitation_policy: InvitationPolicy | None,
    actor: BrowserActor,
    workspace: WorkspaceAuthority,
    membership: Membership,
    request: CreateInvitationRequest,
    issued: InvitationIssued,
    record: InvitationRecord,
    *,
    workspace_id: str,
    pending_count: int,
    recipient_pending: bool,
    now: int,
) -> None:
    authorize_invitation_owner(
        session_policy,
        actor,
        workspace,
        membership,
        workspace_id=workspace_id,
        now=now,
        mutation=True,
    )
    configured = require_invitation_policy(invitation_policy)
    TypeAdapter(Count).validate_python(pending_count, strict=True)
    if request.expected_workspace_revision != workspace.workspace.revision:
        raise ContractViolation("incompatible_state", 409)
    if pending_count >= configured.max_pending_per_workspace or recipient_pending:
        raise ContractViolation("incompatible_state", 409)
    if (
        record.policy_id != configured.policy_id
        or record.workspace_id != workspace_id
        or record.inviter_principal_id != actor.session.principal_id
        or record.recipient_email != request.recipient_email
        or record.role != request.role
        or record.created_at != now
        or record.expires_at != now + configured.token_lifetime_seconds
        or record.revision != 0
        or record.state != "pending"
        or record.token_sha256 != invitation_token_sha256(issued.token)
        or issued.invitation != invitation_view(record, now=now)
    ):
        raise ContractViolation("incompatible_state", 409)


def _resolution(
    before: InvitationRecord,
    after: InvitationRecord,
    *,
    state: Literal["accepted", "revoked"],
    principal_id: str | None,
    now: int,
) -> None:
    if before.state != "pending":
        raise ContractViolation("incompatible_state", 409)
    expected = before.model_dump() | dict(
        state=state,
        revision=before.revision + 1,
        accepted_principal_id=principal_id,
        resolved_at=now,
    )
    if after.model_dump() != expected:
        raise ContractViolation("incompatible_state", 409)


def validate_invitation_revoke(
    policy: DeploymentSessionPolicy | None,
    actor: BrowserActor,
    workspace: WorkspaceAuthority,
    membership: Membership,
    before: InvitationRecord,
    after: InvitationRecord,
    request: RevokeInvitationRequest,
    *,
    workspace_id: str,
    invitation_id: str,
    now: int,
) -> None:
    authorize_invitation_owner(
        policy, actor, workspace, membership, workspace_id=workspace_id, now=now, mutation=True
    )
    if before.workspace_id != workspace_id or before.invitation_id != invitation_id:
        raise ContractViolation("not_found", 404)
    if request.expected_invitation_revision != before.revision:
        raise ContractViolation("incompatible_state", 409)
    # An accepted invitation is not a membership-revocation endpoint.
    _resolution(before, after, state="revoked", principal_id=None, now=now)


def _redemption_authority(
    session_policy: DeploymentSessionPolicy | None,
    invitation_policy: InvitationPolicy | None,
    context: RedemptionContext,
    record: InvitationRecord,
    request: RedeemInvitationRequest,
    *,
    now: int,
) -> None:
    configured_session = validate_human_actor(session_policy, context.actor, now=now, mutation=True)
    configured = require_invitation_policy(invitation_policy)
    identity, assertion = context.recipient_identity, context.email_assertion
    session = context.actor.session
    providers = {p.provider_id: p for p in configured_session.providers}
    provider = providers.get(assertion.provider_id)
    unavailable = (
        record.policy_id != configured.policy_id
        or (record.state == "pending" and now >= record.expires_at)
        or (
            record.state == "accepted"
            and record.resolved_at is not None
            and now >= record.resolved_at + configured.retry_window_seconds
        )
        or not hmac.compare_digest(record.token_sha256, invitation_token_sha256(request.token))
        or record.state == "revoked"
        or identity.principal.principal_id != session.principal_id
        or not identity.principal.active
        or not identity.identity_active
        or (identity.provider_id, identity.issuer, identity.subject)
        != (assertion.provider_id, assertion.issuer, assertion.subject)
        or (assertion.session_id, assertion.session_generation)
        != (session.session_id, session.generation)
        or provider is None
        or (provider is not None and provider.issuer != assertion.issuer)
        or not assertion.email_verified
        or assertion.email != record.recipient_email
        or assertion.issued_at > now
        or assertion.verified_at > now
        or assertion.verified_at < assertion.issued_at
        or assertion.verified_at >= assertion.expires_at
        or now >= assertion.expires_at
        or now - assertion.issued_at >= configured.email_assertion_max_age_seconds
    )
    inviter, principal, workspace = (
        context.inviter_membership,
        context.inviter_principal,
        context.workspace,
    )
    unavailable = unavailable or (
        workspace.workspace.workspace_id != record.workspace_id
        or workspace.workspace.state != "active"
        or not enabled_owners(workspace)
        or inviter.workspace_id != record.workspace_id
        or inviter.principal_id != record.inviter_principal_id
        or principal.principal_id != inviter.principal_id
        or not principal.active
        or not inviter.active
        or inviter.role != "owner"
        or inviter.principal_id not in enabled_owners(workspace)
    )
    member = context.recipient_membership
    if member is not None:
        unavailable = unavailable or (
            member.workspace_id != record.workspace_id
            or member.principal_id != session.principal_id
            or not member.active
            or (member.role == "owner") != (member.principal_id in workspace.active_owner_ids)
            or member.principal_id in workspace.disabled_owner_ids
        )
    elif session.principal_id in workspace.active_owner_ids:
        unavailable = True
    if record.state == "accepted":
        unavailable = (
            unavailable or record.accepted_principal_id != session.principal_id or member is None
        )
    if unavailable:
        raise ContractViolation("not_found", 404)


def check_redemption_replay(
    session_policy: DeploymentSessionPolicy | None,
    invitation_policy: InvitationPolicy | None,
    context: RedemptionContext,
    record: InvitationRecord,
    request: RedeemInvitationRequest,
    *,
    key: str,
    stored: InvitationReceipt | None,
    now: int,
) -> RedemptionResult | None:
    _redemption_authority(session_policy, invitation_policy, context, record, request, now=now)
    outcome = _receipt(
        stored,
        principal_id=context.actor.session.principal_id,
        operation="redeem",
        workspace_id=record.workspace_id,
        target=record.invitation_id,
        key=key,
        digest=redemption_request_sha256(request),
    )
    if outcome is None:
        return None
    member = context.recipient_membership
    if outcome != record.invitation_id or record.state != "accepted" or member is None:
        raise ContractViolation("incompatible_state", 409)
    return RedemptionResult(
        invitation_id=outcome, workspace_id=record.workspace_id, membership=member
    )


def validate_invitation_redemption(
    session_policy: DeploymentSessionPolicy | None,
    invitation_policy: InvitationPolicy | None,
    context: RedemptionContext,
    before: InvitationRecord,
    after: InvitationRecord,
    request: RedeemInvitationRequest,
    resulting_member: Membership,
    resulting_workspace: WorkspaceAuthority,
    *,
    now: int,
) -> None:
    _redemption_authority(session_policy, invitation_policy, context, before, request, now=now)
    _resolution(
        before, after, state="accepted", principal_id=context.actor.session.principal_id, now=now
    )
    existing = context.recipient_membership
    if existing is not None:
        # Consuming an invite is not a role change or membership reactivation.
        if resulting_member != existing or resulting_workspace != context.workspace:
            raise ContractViolation("incompatible_state", 409)
        return
    expected_member = Membership(
        workspace_id=before.workspace_id,
        principal_id=context.actor.session.principal_id,
        role=before.role,
        active=True,
        revision=0,
    )
    owners = set(context.workspace.active_owner_ids)
    if before.role == "owner":
        owners.add(context.actor.session.principal_id)
    expected_workspace = context.workspace.model_dump() | {
        "workspace": context.workspace.workspace.model_dump()
        | {"revision": context.workspace.workspace.revision + 1},
        "active_owner_ids": tuple(sorted(owners)),
    }
    if (
        resulting_member != expected_member
        or resulting_workspace.model_dump() != expected_workspace
    ):
        raise ContractViolation("incompatible_state", 409)


INVITATION_MODELS: tuple[type[Message], ...] = (
    InvitationPolicy,
    CreateInvitationRequest,
    RevokeInvitationRequest,
    RedeemInvitationRequest,
    InvitationRecord,
    InvitationView,
    InvitationPage,
    InvitationIssued,
    RedemptionResult,
    CurrentRecipientIdentity,
    VerifiedEmailAssertion,
    RedemptionContext,
    InvitationReceipt,
)
PUBLIC_MODELS: tuple[type[Message], ...] = (
    CreateInvitationRequest,
    RevokeInvitationRequest,
    RedeemInvitationRequest,
    InvitationView,
    InvitationPage,
    InvitationIssued,
    RedemptionResult,
)


def invitation_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(m, "validation") for m in INVITATION_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/invitation.schema.json"
    schema["x-public-models"] = [m.__name__ for m in PUBLIC_MODELS]
    schema["x-contract-status"] = (
        "ID-B/B2; linking/credential lifecycle and full C-ID remain unfinished"
    )
    schema["description"] = (
        "Synthetic conformance shapes, not verified identity, HTTP handlers or SQL."
    )
    return schema
