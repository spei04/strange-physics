"""Explicit customer-world preview grants. No implicit role, creator or terminal disclosure."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.credential_authority import CredentialOwner
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.world_contracts import (
    WORLD_MODELS,
    BrowserWorldDefinition,
    WorldActorAncestry,
    WorldExpiredMutation,
    WorldMutationScope,
    WorldPolicy,
    WorldVersionCommit,
    WorldVersionRecord,
    WorldVersionView,
)


class PreviewRecipient(Message):
    workspace_id: Identifier
    principal_id: Identifier
    principal_generation: Count
    grant_incarnation: Count


class IssuePreviewRequest(Message):
    operation: Literal["issue_preview"] = "issue_preview"
    version_id: Identifier
    recipient_principal_id: Identifier
    ttl_seconds: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]


class RenewPreviewRequest(Message):
    operation: Literal["renew_preview"] = "renew_preview"
    grant_id: Identifier
    expected_revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
    ttl_seconds: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]


class RevokePreviewRequest(Message):
    operation: Literal["revoke_preview"] = "revoke_preview"
    grant_id: Identifier
    expected_revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]


PreviewRequest = Annotated[
    IssuePreviewRequest | RenewPreviewRequest | RevokePreviewRequest,
    Field(discriminator="operation"),
]


class PreviewGrantRecord(Message):
    """Private recipient ancestry; issuer audit is distinct from current recipient authority."""

    grant_id: Identifier
    workspace_id: Identifier
    world_id: Identifier
    version_id: Identifier
    recipient: PreviewRecipient
    issued_by: WorldActorAncestry
    updated_by: WorldActorAncestry
    issuance_policy_sha256: Digest
    decision_policy_sha256: Digest
    created_at: Count
    updated_at: Count
    expires_at: Count
    revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
    revoked_at: Count | None

    @model_validator(mode="after")
    def shape(self) -> Self:
        if (
            any(
                x != self.workspace_id
                for x in (
                    self.recipient.workspace_id,
                    self.issued_by.workspace_id,
                    self.updated_by.workspace_id,
                )
            )
            or not self.created_at <= self.updated_at
            or self.expires_at <= self.created_at
            or (self.revoked_at is None and self.updated_at >= self.expires_at)
            or (self.revoked_at is not None and self.revoked_at != self.updated_at)
            or (
                self.revision == 1
                and (
                    self.created_at != self.updated_at
                    or self.revoked_at is not None
                    or self.issued_by != self.updated_by
                    or self.issuance_policy_sha256 != self.decision_policy_sha256
                )
            )
        ):
            raise ValueError("Grant scope, issuance and lifecycle chronology must be consistent")
        return self


class PreviewGrantView(Message):
    """Safe management metadata exposes CAS revision, never law, seed or definition digest."""

    grant_id: Identifier
    workspace_id: Identifier
    world_id: Identifier
    version_id: Identifier
    recipient_principal_id: Identifier
    revision: Annotated[int, Field(strict=True, ge=1, le=2**53 - 1)]
    created_at: Count
    updated_at: Count
    expires_at: Count
    revoked_at: Count | None

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if (
            self.created_at > self.updated_at
            or self.expires_at <= self.created_at
            or (self.revoked_at is None and self.updated_at >= self.expires_at)
            or (self.revoked_at is not None and self.revoked_at != self.updated_at)
            or (
                self.revision == 1
                and (self.created_at != self.updated_at or self.revoked_at is not None)
            )
        ):
            raise ValueError("Safe grant metadata must preserve lifecycle chronology")
        return self


def preview_metadata(record: PreviewGrantRecord) -> PreviewGrantView:
    """Pure shape projection; a complete current authority boundary is still required."""
    return PreviewGrantView(
        grant_id=record.grant_id,
        workspace_id=record.workspace_id,
        world_id=record.world_id,
        version_id=record.version_id,
        recipient_principal_id=record.recipient.principal_id,
        revision=record.revision,
        created_at=record.created_at,
        updated_at=record.updated_at,
        expires_at=record.expires_at,
        revoked_at=record.revoked_at,
    )


class PreviewGrantPage(Message):
    items: Annotated[tuple[PreviewGrantView, ...], Field(max_length=128)]
    next_cursor: Identifier | None

    @model_validator(mode="after")
    def unique_items(self) -> Self:
        ids = tuple(x.grant_id for x in self.items)
        if len(ids) != len(set(ids)) or len({(x.workspace_id, x.world_id) for x in self.items}) > 1:
            raise ValueError("Grant page requires unique records within one world")
        return self


class GrantedWorldDefinition(Message):
    """Sensitive browser output only after actual current version-specific recipient grant."""

    version: WorldVersionView
    grant_id: Identifier
    definition: BrowserWorldDefinition

    @model_validator(mode="after")
    def same_public_space(self) -> Self:
        if message_sha256(self.version.space) != message_sha256(self.definition.space):
            raise ValueError("Granted definition must match its safe public space")
        return self


class PreviewMutationCommit(Message):
    """Immutable metadata-only receipt plus atomic grant transition. Not an authority proof."""

    receipt_id: Identifier
    scope: WorldMutationScope
    request: PreviewRequest
    request_sha256: Digest
    version: WorldVersionRecord
    actor: WorldActorAncestry
    recipient_at_commit: CredentialOwner | None
    policy: WorldPolicy
    before: PreviewGrantRecord | None
    after: PreviewGrantRecord
    result: PreviewGrantView
    committed_at: Count
    receipt_expires_at: Count

    @model_validator(mode="after")
    def closure(self) -> Self:
        request, old, new = self.request, self.before, self.after
        view = self.version.view
        if (
            self.scope.operation != request.operation
            or self.receipt_expires_at != self.committed_at + self.policy.receipt_retention_seconds
            or self.request_sha256 != message_sha256(request)
            or self.version.classification != "customer_authored"
            or (new.workspace_id, new.world_id, new.version_id)
            != (view.workspace_id, view.world_id, view.version_id)
            or (self.scope.workspace_id, self.scope.world_id, self.scope.principal_id)
            != (view.workspace_id, view.world_id, self.actor.principal_id)
            or self.actor.workspace_id != view.workspace_id
            or new.updated_by != self.actor
            or new.updated_at != self.committed_at
            or view.created_at > new.created_at
            or new.decision_policy_sha256 != message_sha256(self.policy)
            or self.result != preview_metadata(new)
        ):
            raise ValueError(
                "Preview commit must bind actual scope, policy, version and safe result"
            )
        if request.operation == "issue_preview":
            if (
                old is not None
                or new.revision != 1
                or new.created_at != self.committed_at
                or new.issued_by != self.actor
                or new.version_id != request.version_id
                or new.recipient.principal_id != request.recipient_principal_id
            ):
                raise ValueError("Issuance requires a new grant and exact recipient/version")
        else:
            if old is None:
                raise ValueError("Renew/revoke requires retained grant")
            immutable = (
                "grant_id",
                "workspace_id",
                "world_id",
                "version_id",
                "recipient",
                "issued_by",
                "issuance_policy_sha256",
                "created_at",
            )
            if (
                any(getattr(old, field) != getattr(new, field) for field in immutable)
                or request.grant_id != old.grant_id
                or request.expected_revision != old.revision
                or new.revision != old.revision + 1
                or old.revoked_at is not None
                or self.committed_at < old.updated_at
            ):
                raise ValueError("Transition must preserve immutable ancestry and never un-revoke")
        if request.operation == "revoke_preview":
            if (
                old is None
                or self.recipient_at_commit is not None
                or new.expires_at != old.expires_at
                or new.revoked_at != self.committed_at
            ):
                raise ValueError("Revocation is permanent and cannot extend expiry")
        else:
            if (
                new.revoked_at is not None
                or request.ttl_seconds > self.policy.preview_ttl_seconds
                or new.expires_at != self.committed_at + request.ttl_seconds
                or (
                    old is not None
                    and (old.expires_at <= self.committed_at or new.expires_at <= old.expires_at)
                )
            ):
                raise ValueError("Live renewal needs a later expiry within current policy")
            recipient = self.recipient_at_commit
            if (
                recipient is None
                or recipient.principal.kind != "human"
                or not recipient.principal.active
                or not recipient.grant.membership.active
                or recipient.grant.membership.role not in self.policy.preview_reader_roles
                or (
                    recipient.grant.membership.workspace_id,
                    recipient.principal.principal_id,
                    recipient.principal.generation,
                    recipient.grant.incarnation,
                )
                != (
                    new.recipient.workspace_id,
                    new.recipient.principal_id,
                    new.recipient.principal_generation,
                    new.recipient.grant_incarnation,
                )
            ):
                raise ValueError("Issue/renew must bind current eligible recipient ancestry")
        return self


class PreviewGrantLookup(Message):
    """Scoped partial persistence evidence; runtime must reject missing/inconsistent closure."""

    scope: WorldMutationScope
    receipt: PreviewMutationCommit | None
    expired: WorldExpiredMutation | None
    grant: PreviewGrantRecord | None
    latest_commit: PreviewMutationCommit | None

    @model_validator(mode="after")
    def operation(self) -> Self:
        if self.scope.operation == "create_version":
            raise ValueError("Preview lookup requires a preview mutation")
        return self


class WorldReceiptExpiration(Message):
    """Original full receipt to exact tombstone proposal; no cleanup or deletion authorization."""

    receipt: WorldVersionCommit | PreviewMutationCommit
    expired: WorldExpiredMutation
    observed_at: Count

    @model_validator(mode="after")
    def original_receipt(self) -> Self:
        old, new = self.receipt, self.expired
        version = old.version
        if (
            new.scope != old.scope
            or new.request_sha256 != old.request_sha256
            or new.receipt_id != old.receipt_id
            or new.allocated_world_id != version.view.world_id
            or new.policy_sha256 != message_sha256(old.policy)
            or new.retention_seconds != old.policy.receipt_retention_seconds
            or new.committed_at != old.committed_at
            or new.expires_at != old.receipt_expires_at
            or self.observed_at < new.expires_at
        ):
            raise ValueError("Expiration must preserve the exact original committed receipt")
        return self


PREVIEW_MODELS: tuple[type[Message], ...] = (
    PreviewRecipient,
    IssuePreviewRequest,
    RenewPreviewRequest,
    RevokePreviewRequest,
    PreviewGrantRecord,
    PreviewGrantView,
    PreviewGrantPage,
    GrantedWorldDefinition,
    PreviewMutationCommit,
    PreviewGrantLookup,
    WorldReceiptExpiration,
)
AUTHOR_INPUT_MODELS = ("CreateWorldVersionRequest",)
GRANTED_OUTPUT_MODELS = ("GrantedWorldDefinition",)


def world_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(model, "validation") for model in (*WORLD_MODELS, *PREVIEW_MODELS)]
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/world.schema.json"
    schema["x-contract-status"] = (
        "WORLD1 reviewed pure contracts and proposals; hosted producers and WEB1 pending"
    )
    schema["x-agent-safe-models"] = [
        "WorldVersionView",
        "WorldHead",
        "WorldPage",
        "WorldVersionResult",
    ]
    schema["x-management-output-models"] = ["PreviewGrantView", "PreviewGrantPage"]
    schema["x-author-input-models"] = list(AUTHOR_INPUT_MODELS)
    schema["x-granted-definition-models"] = list(GRANTED_OUTPUT_MODELS)
    schema["x-public-models"] = [
        *schema["x-agent-safe-models"],
        *schema["x-management-output-models"],
        *AUTHOR_INPUT_MODELS,
        *GRANTED_OUTPUT_MODELS,
        "IssuePreviewRequest",
        "RenewPreviewRequest",
        "RevokePreviewRequest",
    ]
    schema["description"] = (
        "Sensitive author input and granted definition roots are distinct from agent-safe views. "
        "Private authority, catalog, lineage and commit models require trusted producers. "
        "No schema establishes authorization, persistence, blindness or worker readiness."
    )
    return schema
