"""Service principal and key lifecycle messages; no issuer, verifier, HTTP or SQL.

Public metadata is safe to expose only after current owner authorization.
Private records and atomic proposals are trusted producer inputs, never bodies.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.credential_authority import CredentialOwner, GrantAuthority
from strange_physics.research_contracts import Count, Digest
from strange_physics.workspace_contracts import (
    BrowserActor,
    Cursor,
    DisplayName,
    IdempotencyKey,
    WorkspaceAuthority,
)

ServicePermission = Literal["runs:read", "runs:create", "runs:cancel"]
ServiceRole = Literal["researcher", "viewer"]
ServiceScopes = Annotated[tuple[ServicePermission, ...], Field(min_length=1, max_length=3)]
ServiceOperation = Literal[
    "service_create", "service_state", "key_issue", "key_rotate", "key_recover", "key_revoke"
]
ServiceToken = Annotated[
    str,
    Field(
        pattern=r"^spk1\.[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$",
        json_schema_extra={"not": {"pattern": "[^A-Za-z0-9_.-]"}},
    ),
]


def validate_scopes(scopes: tuple[str, ...], *, viewer: bool = False) -> None:
    if tuple(sorted(set(scopes))) != scopes:
        raise ValueError("Scopes must be unique and canonically sorted")
    if viewer and scopes != ("runs:read",):
        raise ValueError("Viewer service authority permits only runs:read")


class ServiceCredentialPolicy(Message):
    policy_id: Identifier
    max_key_ttl_seconds: Annotated[int, Field(ge=1, le=31_536_000)]
    max_overlap_seconds: Annotated[int, Field(ge=0, le=86_400)]
    receipt_retention_seconds: Annotated[int, Field(ge=1, le=31_536_000)]
    max_key_records: Annotated[int, Field(ge=2, le=10_000)]

    @model_validator(mode="after")
    def bounded_overlap(self) -> Self:
        if self.max_overlap_seconds > self.max_key_ttl_seconds:
            raise ValueError("Overlap cannot exceed the maximum key lifetime")
        return self


class ServiceManager(Message):
    """Current human owner plus original session principal-generation binding."""

    actor: BrowserActor
    owner: CredentialOwner
    session_principal_generation: Count

    @model_validator(mode="after")
    def human_binding(self) -> Self:
        if (
            self.owner.principal.kind != "human"
            or self.owner.principal.principal_id != self.actor.session.principal_id
        ):
            raise ValueError("Service management requires the same human principal")
        return self


class ServicePrincipalView(Message):
    workspace_id: Identifier
    principal_id: Identifier
    display_name: DisplayName
    active: bool
    revision: Count
    authority_generation: Count
    grant: GrantAuthority
    scope_ceiling: ServiceScopes
    last_key_generation: Count

    @model_validator(mode="after")
    def bounded_grant(self) -> Self:
        membership = self.grant.membership
        if (
            membership.workspace_id != self.workspace_id
            or membership.principal_id != self.principal_id
            or membership.role == "owner"
        ):
            raise ValueError("Service principal requires its independent non-owner grant")
        validate_scopes(self.scope_ceiling, viewer=membership.role == "viewer")
        return self


class ServicePrincipalPage(Message):
    workspace_id: Identifier
    items: Annotated[tuple[ServicePrincipalView, ...], Field(max_length=100)]
    next_cursor: Cursor | None

    @model_validator(mode="after")
    def same_workspace(self) -> Self:
        if any(item.workspace_id != self.workspace_id for item in self.items) or len(
            {item.principal_id for item in self.items}
        ) != len(self.items):
            raise ValueError("Principal page must contain unique same-workspace identities")
        return self


class ServiceKeyState(Message):
    """Secret-free durable key state; current validity still needs current ancestry."""

    policy_id: Identifier
    workspace_id: Identifier
    principal_id: Identifier
    credential_id: Identifier
    authority_generation: Count
    grant_incarnation: Count
    key_generation: Annotated[int, Field(ge=1, le=2**53 - 1)]
    scopes: ServiceScopes
    issued_by: Identifier
    created_at: Count
    expires_at: Count
    retire_at: Count | None
    revoked_at: Count | None
    retain_until: Count

    @model_validator(mode="after")
    def lifecycle(self) -> Self:
        validate_scopes(self.scopes)
        if self.expires_at <= self.created_at or self.retain_until < self.expires_at:
            raise ValueError("Key expiry and retained record must outlive issuance")
        if self.retire_at is not None and not self.created_at <= self.retire_at <= self.expires_at:
            raise ValueError("Retirement can only shorten the original lifetime")
        if self.revoked_at is not None and self.revoked_at < self.created_at:
            raise ValueError("Revocation cannot predate issuance")
        if self.revoked_at is not None and self.retain_until < self.revoked_at:
            raise ValueError("Revocation tombstone must retain its committed time")
        return self


class ServiceKeyRecord(Message):
    """Private verifier digest; never expose this record through a public route."""

    key: ServiceKeyState
    verifier_sha256: Digest = Field(repr=False)


class ServiceKeyView(Message):
    key: ServiceKeyState
    principal_revision: Count
    valid_now: bool


class ServiceKeyPage(Message):
    principal: ServicePrincipalView
    items: Annotated[tuple[ServiceKeyView, ...], Field(max_length=100)]
    next_cursor: Cursor | None

    @model_validator(mode="after")
    def same_principal(self) -> Self:
        if any(
            item.key.workspace_id != self.principal.workspace_id
            or item.key.principal_id != self.principal.principal_id
            or item.principal_revision != self.principal.revision
            for item in self.items
        ) or len({item.key.credential_id for item in self.items}) != len(self.items):
            raise ValueError("Key page must bind unique keys to the current shared revision")
        return self


class ServiceKeySet(Message):
    """Complete retained key records under the shared principal lock, never one page."""

    principal: ServicePrincipalView
    records: Annotated[tuple[ServiceKeyRecord, ...], Field(max_length=10_000)]

    @model_validator(mode="after")
    def complete_shape(self) -> Self:
        keys = tuple(record.key for record in self.records)
        if (
            tuple(sorted(key.credential_id for key in keys))
            != tuple(key.credential_id for key in keys)
            or len({key.credential_id for key in keys}) != len(keys)
            or len({key.key_generation for key in keys}) != len(keys)
            or len({record.verifier_sha256 for record in self.records}) != len(keys)
            or any(
                key.workspace_id != self.principal.workspace_id
                or key.principal_id != self.principal.principal_id
                or key.key_generation > self.principal.last_key_generation
                or key.authority_generation > self.principal.authority_generation
                or key.grant_incarnation > self.principal.grant.incarnation
                for key in keys
            )
        ):
            raise ValueError("Key set must bind sorted unique retained keys and issuer generations")
        return self


class ServiceCreateRequest(Message):
    expected_workspace_revision: Count
    display_name: DisplayName
    role: ServiceRole
    scope_ceiling: ServiceScopes

    @model_validator(mode="after")
    def bounded_scopes(self) -> Self:
        validate_scopes(self.scope_ceiling, viewer=self.role == "viewer")
        return self


class ServiceRevisionRequest(Message):
    expected_revision: Count


class ServiceStateRequest(ServiceRevisionRequest):
    active: bool


class ServiceKeyIssueRequest(ServiceRevisionRequest):
    scopes: ServiceScopes
    expires_at: Count

    @model_validator(mode="after")
    def ordered_scopes(self) -> Self:
        validate_scopes(self.scopes)
        return self


class ServiceKeyRotateRequest(ServiceKeyIssueRequest):
    overlap_seconds: Annotated[int, Field(ge=0, le=86_400)]


class ServiceKeyRecoverRequest(ServiceRevisionRequest):
    """Recovery deliberately has no scope or lifetime controls."""


class ServiceKeyRevokeRequest(ServiceRevisionRequest):
    pass


class ServiceMutationOutcome(Message):
    """Original committed metadata, distinct from the current state on replay."""

    operation: ServiceOperation
    workspace_id: Identifier
    principal_id: Identifier
    credential_id: Identifier | None
    replaced_credential_id: Identifier | None
    committed_revision: Count
    authority_generation: Count
    grant_incarnation: Count
    committed_at: Count

    @model_validator(mode="after")
    def operation_binding(self) -> Self:
        if (self.credential_id is not None) != self.operation.startswith("key_"):
            raise ValueError("Only key outcomes name a credential")
        if (self.replaced_credential_id is not None) != (
            self.operation in {"key_rotate", "key_recover"}
        ):
            raise ValueError("Replacement outcomes must identify the original credential")
        if self.credential_id is not None and self.credential_id == self.replaced_credential_id:
            raise ValueError("Replacement uses a new credential identity")
        return self


class ServiceMutationResponse(Message):
    disposition: Literal["committed", "replayed"]
    outcome: ServiceMutationOutcome
    principal: ServicePrincipalView
    credential: ServiceKeyView | None

    @model_validator(mode="after")
    def response_binding(self) -> Self:
        if (
            self.outcome.workspace_id != self.principal.workspace_id
            or self.outcome.principal_id != self.principal.principal_id
            or self.outcome.committed_revision > self.principal.revision
            or self.outcome.authority_generation != self.principal.authority_generation
            or self.outcome.grant_incarnation != self.principal.grant.incarnation
            or (
                self.disposition == "committed"
                and self.outcome.committed_revision != self.principal.revision
            )
            or (self.credential is not None) != (self.outcome.credential_id is not None)
        ):
            raise ValueError("Response must bind the original outcome to current safe metadata")
        if self.credential is not None and (
            self.credential.key.credential_id != self.outcome.credential_id
            or self.credential.key.workspace_id != self.principal.workspace_id
            or self.credential.key.principal_id != self.principal.principal_id
            or self.credential.principal_revision != self.principal.revision
        ):
            raise ValueError("Current credential metadata must match outcome and shared revision")
        return self


class ServiceKeyIssuedResponse(Message):
    delivery: Literal["issued"]
    result: ServiceMutationResponse
    secret: ServiceToken = Field(repr=False)

    @model_validator(mode="after")
    def one_time_secret(self) -> Self:
        if (
            self.result.disposition != "committed"
            or self.result.outcome.operation not in {"key_issue", "key_rotate", "key_recover"}
            or self.result.credential is None
            or self.secret.split(".")[1] != self.result.credential.key.credential_id
        ):
            raise ValueError("Only an initial matching issuance may carry secret material")
        return self


class ServiceKeyReplayResponse(Message):
    delivery: Literal["metadata_only"]
    result: ServiceMutationResponse

    @model_validator(mode="after")
    def no_reissue(self) -> Self:
        if self.result.disposition != "replayed" or self.result.outcome.operation not in {
            "key_issue",
            "key_rotate",
            "key_recover",
        }:
            raise ValueError("Metadata-only delivery is an exact issuance replay")
        return self


class ServiceCommitSnapshot(Message):
    """Original safe principal and affected key projections, retained with the receipt."""

    principal: ServicePrincipalView
    keys: Annotated[tuple[ServiceKeyState, ...], Field(max_length=2)]

    @model_validator(mode="after")
    def same_principal(self) -> Self:
        if (
            tuple(sorted(key.credential_id for key in self.keys))
            != tuple(key.credential_id for key in self.keys)
            or len({key.credential_id for key in self.keys}) != len(self.keys)
            or any(
                key.workspace_id != self.principal.workspace_id
                or key.principal_id != self.principal.principal_id
                for key in self.keys
            )
        ):
            raise ValueError("Commit snapshot must bind sorted unique affected keys")
        return self


class ServiceReceipt(Message):
    """Scoped secret-free deduplication record; never retain an issued response."""

    policy_id: Identifier
    actor_id: Identifier
    actor_generation: Count
    actor_grant_incarnation: Count
    operation: ServiceOperation
    workspace_id: Identifier
    target_principal_id: Identifier | None
    target_credential_id: Identifier | None
    key: IdempotencyKey
    request_sha256: Digest
    outcome: ServiceMutationOutcome
    snapshot: ServiceCommitSnapshot
    audit_event_id: Identifier
    retain_until: Count

    @model_validator(mode="after")
    def receipt_scope(self) -> Self:
        if (
            self.operation != self.outcome.operation
            or self.workspace_id != self.outcome.workspace_id
            or (self.target_principal_id is None) != (self.operation == "service_create")
            or (self.target_credential_id is not None)
            != (self.operation in {"key_rotate", "key_recover", "key_revoke"})
            or self.retain_until <= self.outcome.committed_at
            or self.snapshot.principal.workspace_id != self.workspace_id
            or self.snapshot.principal.principal_id != self.outcome.principal_id
            or self.snapshot.principal.revision != self.outcome.committed_revision
            or self.snapshot.principal.authority_generation != self.outcome.authority_generation
            or self.snapshot.principal.grant.incarnation != self.outcome.grant_incarnation
        ):
            raise ValueError("Receipt must bind its complete operation scope and lifetime")
        if self.target_principal_id is not None and (
            self.target_principal_id != self.outcome.principal_id
        ):
            raise ValueError("Receipt target must match its outcome")
        expected_target = (
            self.outcome.replaced_credential_id
            if self.operation in {"key_rotate", "key_recover"}
            else self.outcome.credential_id
            if self.operation == "key_revoke"
            else None
        )
        if self.target_credential_id != expected_target:
            raise ValueError("Receipt key target must match its committed operation")
        return self


class ServiceAudit(Message):
    event_id: Identifier
    actor_id: Identifier
    actor_generation: Count
    actor_grant_incarnation: Count
    request_sha256: Digest
    outcome: ServiceMutationOutcome
    snapshot_sha256: Digest


class ServiceError(Message):
    code: Literal[
        "invalid_request",
        "policy_unavailable",
        "unauthenticated",
        "forbidden",
        "ambiguous_credentials",
        "reauthentication_required",
        "not_found",
        "idempotency_conflict",
        "incompatible_state",
        "recovery_required",
        "quota_exceeded",
        "temporarily_unavailable",
        "rate_limited",
    ]
    request_id: Identifier


class ServiceKeyMaterial(Message):
    """Fresh server-generated material; plaintext stays outside durable proposals."""

    credential_id: Identifier
    verifier_sha256: Digest = Field(repr=False)


class ServiceReceiptLookup(Message):
    """Complete locked lookup; absent means never reserved, not expired-and-deleted."""

    state: Literal["absent", "committed", "recovery_required"]
    receipt: ServiceReceipt | None
    audit: ServiceAudit | None

    @model_validator(mode="after")
    def absence(self) -> Self:
        if self.state == "absent" and (self.receipt is not None or self.audit is not None):
            raise ValueError("An absent request cannot contain committed evidence")
        return self


class ServicePlan(Message):
    """One atomic SQL proposal, not evidence of commit or permission to deliver a secret."""

    workspace: WorkspaceAuthority
    key_set: ServiceKeySet
    receipt: ServiceReceipt
    audit: ServiceAudit
    response: ServiceMutationResponse

    @model_validator(mode="after")
    def proposal_binding(self) -> Self:
        if (
            self.workspace.workspace.workspace_id != self.key_set.principal.workspace_id
            or self.key_set.principal != self.response.principal
            or self.response.disposition != "committed"
            or self.receipt.outcome != self.response.outcome
            or self.audit.outcome != self.response.outcome
            or self.receipt.audit_event_id != self.audit.event_id
        ):
            raise ValueError("Atomic proposal must bind its state, receipt, audit and response")
        return self


SERVICE_MODELS: tuple[type[Message], ...] = (
    ServiceCommitSnapshot,
    ServiceKeyMaterial,
    ServiceReceiptLookup,
    ServicePlan,
    ServiceCredentialPolicy,
    ServiceManager,
    ServicePrincipalView,
    ServicePrincipalPage,
    ServiceKeyState,
    ServiceKeyRecord,
    ServiceKeyView,
    ServiceKeyPage,
    ServiceKeySet,
    ServiceCreateRequest,
    ServiceStateRequest,
    ServiceKeyIssueRequest,
    ServiceKeyRotateRequest,
    ServiceKeyRecoverRequest,
    ServiceKeyRevokeRequest,
    ServiceMutationOutcome,
    ServiceMutationResponse,
    ServiceKeyIssuedResponse,
    ServiceKeyReplayResponse,
    ServiceReceipt,
    ServiceAudit,
    ServiceError,
)


def service_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in SERVICE_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/service.schema.json"
    schema["description"] = (
        "C1 service/key messages. Private authority, verifier and receipt records are "
        "trusted producer inputs, never public bodies. No HTTP, SQL or token verifier."
    )
    return schema
