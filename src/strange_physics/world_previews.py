"""Current-authorized preview grant proposals and explicit definition disclosure.

An original safe receipt may replay after recipient departure or grant expiry,
but new issuance/renewal and every definition disclosure need current recipient
authority. There is no implicit creator/owner or terminal-run truth grant.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.control_contracts import ContractViolation
from strange_physics.credential_authority import CredentialOwner
from strange_physics.research_contracts import message_sha256
from strange_physics.workspace_contracts import validate_product_workspace
from strange_physics.world_authority import authorize_world, world_actor, world_authority_sha256
from strange_physics.world_contracts import (
    BrowserWorldDefinition,
    WorldBrowserAuthority,
    WorldMutationScope,
    WorldPolicy,
    WorldVersionRecord,
)
from strange_physics.world_preview_contracts import (
    GrantedWorldDefinition,
    IssuePreviewRequest,
    PreviewGrantLookup,
    PreviewGrantPage,
    PreviewGrantRecord,
    PreviewGrantView,
    PreviewMutationCommit,
    PreviewRecipient,
    PreviewRequest,
    RenewPreviewRequest,
    RevokePreviewRequest,
    preview_metadata,
)
from strange_physics.world_versions import (
    WORLD_JSON_DEPTH,
    WORLD_JSON_NODES,
    reject_expired_world_key,
    validate_world_record,
)


@dataclass(frozen=True)
class PreviewDecision:
    """Private producer decision; commit=None is original safe metadata replay."""

    result: PreviewGrantView
    commit: PreviewMutationCommit | None
    authority_sha256: str
    current_policy_sha256: str


def _version(
    version: WorldVersionRecord,
    policy: WorldPolicy,
    *,
    workspace_id: str,
    world_id: str,
    now: int,
) -> None:
    validate_world_record(
        version,
        policy,
        workspace_id=workspace_id,
        world_id=world_id,
        version_id=None,
        now=now,
    )
    if version.classification != "customer_authored":
        raise ContractViolation("forbidden", 403)


def _current(
    grant: PreviewGrantRecord | None,
    latest: PreviewMutationCommit | None,
    version: WorldVersionRecord,
    policy: WorldPolicy,
    *,
    now: int,
) -> tuple[PreviewGrantRecord, PreviewMutationCommit]:
    if grant is None or latest is None:
        raise ContractViolation("recovery_required", 409)
    bounded_canonical(latest, policy.max_metadata_bytes)
    if (
        message_sha256(grant) != message_sha256(latest.after)
        or message_sha256(version) != message_sha256(latest.version)
        or latest.committed_at > now
    ):
        raise ContractViolation("recovery_required", 409)
    return grant, latest


def _history(old: PreviewMutationCommit, current: PreviewMutationCommit) -> None:
    before, after = old.after, current.after
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
        message_sha256(old.version) != message_sha256(current.version)
        or any(getattr(before, name) != getattr(after, name) for name in immutable)
        or after.revision < before.revision
        or after.updated_at < before.updated_at
        or after.expires_at < before.expires_at
        or (after.revision == before.revision and message_sha256(old) != message_sha256(current))
        or (after.revision > before.revision and before.revoked_at is not None)
        or (after.revision == before.revision + 1 and current.before != before)
    ):
        raise ContractViolation("recovery_required", 409)


def _recipient(
    recipient: CredentialOwner | None,
    authority: WorldBrowserAuthority,
    policy: WorldPolicy,
    *,
    principal_id: str,
) -> PreviewRecipient:
    if recipient is None:
        raise ContractViolation("not_found", 404)
    member = recipient.grant.membership
    workspace_id = authority.workspace.workspace.workspace_id
    if (member.workspace_id, recipient.principal.principal_id) != (workspace_id, principal_id):
        raise ContractViolation("not_found", 404)
    if (
        recipient.principal.kind != "human"
        or not recipient.principal.active
        or not member.active
        or member.role not in policy.preview_reader_roles
    ):
        raise ContractViolation("forbidden", 403)
    validate_product_workspace(authority.workspace, workspace_id, member)
    return PreviewRecipient(
        workspace_id=workspace_id,
        principal_id=principal_id,
        principal_generation=recipient.principal.generation,
        grant_incarnation=recipient.grant.incarnation,
    )


def _request(raw: bytes, operation: str, policy: WorldPolicy) -> PreviewRequest:
    args = dict(
        max_bytes=policy.max_metadata_bytes,
        max_depth=WORLD_JSON_DEPTH,
        max_nodes=WORLD_JSON_NODES,
    )
    if operation == "issue_preview":
        return parse_bounded_json(raw, IssuePreviewRequest, **args)
    if operation == "renew_preview":
        return parse_bounded_json(raw, RenewPreviewRequest, **args)
    if operation == "revoke_preview":
        return parse_bounded_json(raw, RevokePreviewRequest, **args)
    raise ContractViolation("invalid_request", 422)


def _replay(
    lookup: PreviewGrantLookup,
    request: PreviewRequest,
    version: WorldVersionRecord | None,
    policy: WorldPolicy,
    *,
    now: int,
) -> PreviewGrantView | None:
    receipt, expired = lookup.receipt, lookup.expired
    if receipt is not None and expired is not None:
        raise ContractViolation("recovery_required", 409)
    if expired is not None:
        if expired.allocated_world_id != lookup.scope.world_id:
            raise ContractViolation("recovery_required", 409)
        if lookup.grant is not None or lookup.latest_commit is not None or version is not None:
            if version is None:
                raise ContractViolation("recovery_required", 409)
            _version(
                version,
                policy,
                workspace_id=lookup.scope.workspace_id,
                world_id=expired.allocated_world_id,
                now=now,
            )
            _current(lookup.grant, lookup.latest_commit, version, policy, now=now)
        reject_expired_world_key(expired, lookup.scope, message_sha256(request), now=now)
    if receipt is None:
        return None
    if version is None:
        raise ContractViolation("recovery_required", 409)
    _version(
        version,
        policy,
        workspace_id=lookup.scope.workspace_id,
        world_id=receipt.version.view.world_id,
        now=now,
    )
    _, latest = _current(lookup.grant, lookup.latest_commit, version, policy, now=now)
    if receipt.scope != lookup.scope or receipt.committed_at > now:
        raise ContractViolation("recovery_required", 409)
    _history(receipt, latest)
    if receipt.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    if now >= receipt.receipt_expires_at:
        raise ContractViolation("receipt_expired", 409)
    return receipt.result


def propose_preview_mutation(
    raw_request: bytes,
    scope: WorldMutationScope,
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    version: WorldVersionRecord | None,
    lookup: PreviewGrantLookup,
    recipient: CredentialOwner | None,
    *,
    grant_id: str,
    receipt_id: str,
    now: int,
) -> PreviewDecision:
    """Fresh issue/renew/revoke or exact safe replay, after full current owner authority.

    Allocation IDs are trusted producer inputs and ignored on replay. Recipients
    are current transactional projections for new issue/renew; they are not
    required on replay or revoke. Producers must CAS the actual current
    session/principal/membership/workspace/policy, recipient (where relevant),
    scoped key and grant revision in the same atomic grant+receipt transaction.
    """
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:preview-grants:manage",
        workspace_id=scope.workspace_id,
        mutation=True,
        now=now,
    )
    actor = world_actor(authority)
    if scope.principal_id != actor.principal_id or scope.world_id is None:
        raise ContractViolation("not_found", 404)
    request = _request(raw_request, scope.operation, configured)
    bounded_canonical(lookup, configured.max_metadata_bytes)
    if lookup.scope != scope:
        raise ContractViolation("recovery_required", 409)
    replay = _replay(lookup, request, version, configured, now=now)
    if replay is not None:
        return PreviewDecision(
            replay, None, world_authority_sha256(authority), message_sha256(configured)
        )
    if version is None:
        raise ContractViolation("not_found", 404)
    _version(version, configured, workspace_id=scope.workspace_id, world_id=scope.world_id, now=now)
    before: PreviewGrantRecord | None
    if request.operation == "issue_preview":
        if lookup.grant is not None or lookup.latest_commit is not None:
            raise ContractViolation("recovery_required", 409)
        if request.version_id != version.view.version_id:
            raise ContractViolation("not_found", 404)
        binding = _recipient(
            recipient, authority, configured, principal_id=request.recipient_principal_id
        )
        before = None
    else:
        if lookup.grant is None and lookup.latest_commit is None:
            raise ContractViolation("not_found", 404)
        before, _ = _current(lookup.grant, lookup.latest_commit, version, configured, now=now)
        if request.grant_id != before.grant_id:
            raise ContractViolation("not_found", 404)
        if request.expected_revision != before.revision or before.revoked_at is not None:
            raise ContractViolation("incompatible_state", 409)
        binding = before.recipient
        if request.operation == "renew_preview":
            current_recipient = _recipient(
                recipient, authority, configured, principal_id=before.recipient.principal_id
            )
            if current_recipient != binding:
                raise ContractViolation("forbidden", 403)
            if before.expires_at <= now:
                raise ContractViolation("incompatible_state", 409)
    if request.operation != "revoke_preview":
        if request.ttl_seconds > configured.preview_ttl_seconds:
            raise ContractViolation("invalid_request", 422)
        expires_at = now + request.ttl_seconds
        if before is not None and expires_at <= before.expires_at:
            raise ContractViolation("incompatible_state", 409)
    else:
        if before is None:
            raise ContractViolation("recovery_required", 409)
        expires_at = before.expires_at
    try:
        after = PreviewGrantRecord(
            grant_id=grant_id if before is None else before.grant_id,
            workspace_id=scope.workspace_id,
            world_id=scope.world_id,
            version_id=version.view.version_id,
            recipient=binding,
            issued_by=actor if before is None else before.issued_by,
            updated_by=actor,
            issuance_policy_sha256=message_sha256(configured)
            if before is None
            else before.issuance_policy_sha256,
            decision_policy_sha256=message_sha256(configured),
            created_at=now if before is None else before.created_at,
            updated_at=now,
            expires_at=expires_at,
            revision=1 if before is None else before.revision + 1,
            revoked_at=now if request.operation == "revoke_preview" else None,
        )
        commit = PreviewMutationCommit(
            receipt_id=receipt_id,
            scope=scope,
            request=request,
            request_sha256=message_sha256(request),
            version=version,
            actor=actor,
            recipient_at_commit=None if request.operation == "revoke_preview" else recipient,
            policy=configured,
            before=before,
            after=after,
            result=preview_metadata(after),
            committed_at=now,
            receipt_expires_at=now + configured.receipt_retention_seconds,
        )
    except ValidationError:
        raise ContractViolation("invalid_request", 422) from None
    bounded_canonical(commit, configured.max_metadata_bytes)
    return PreviewDecision(
        commit.result, commit, world_authority_sha256(authority), message_sha256(configured)
    )


def read_preview_grant(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    version: WorldVersionRecord,
    grant: PreviewGrantRecord | None,
    latest_commit: PreviewMutationCommit | None,
    *,
    workspace_id: str,
    world_id: str,
    grant_id: str,
    now: int,
) -> PreviewGrantView:
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:preview-grants:manage",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    _version(version, configured, workspace_id=workspace_id, world_id=world_id, now=now)
    if grant is None and latest_commit is None:
        raise ContractViolation("not_found", 404)
    record, _ = _current(grant, latest_commit, version, configured, now=now)
    if record.grant_id != grant_id:
        raise ContractViolation("not_found", 404)
    return preview_metadata(record)


def read_preview_page(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    page: PreviewGrantPage,
    *,
    workspace_id: str,
    world_id: str,
    now: int,
) -> PreviewGrantPage:
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:preview-grants:manage",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    if len(page.items) > configured.max_page_items:
        raise ContractViolation("invalid_request", 422)
    bounded_canonical(page, configured.max_page_bytes)
    if any(
        (item.workspace_id, item.world_id) != (workspace_id, world_id) or item.updated_at > now
        for item in page.items
    ):
        raise ContractViolation("recovery_required", 409)
    return page


def disclose_world_definition(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    version: WorldVersionRecord,
    grant: PreviewGrantRecord | None,
    latest_commit: PreviewMutationCommit | None,
    *,
    workspace_id: str,
    world_id: str,
    version_id: str,
    grant_id: str,
    now: int,
) -> GrantedWorldDefinition:
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:preview",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    # Recipient and lifecycle gates precede any private definition projection.
    if grant is None:
        if latest_commit is not None:
            raise ContractViolation("recovery_required", 409)
        raise ContractViolation("not_found", 404)
    bounded_canonical(grant, configured.max_metadata_bytes)
    if (grant.workspace_id, grant.world_id, grant.version_id, grant.grant_id) != (
        workspace_id,
        world_id,
        version_id,
        grant_id,
    ):
        raise ContractViolation("not_found", 404)
    recipient = _recipient(
        authority.identity.owner,
        authority,
        configured,
        principal_id=grant.recipient.principal_id,
    )
    if (
        recipient != grant.recipient
        or grant.revoked_at is not None
        or grant.expires_at <= now
        or grant.created_at > now
    ):
        raise ContractViolation("forbidden", 403)
    _version(version, configured, workspace_id=workspace_id, world_id=world_id, now=now)
    _current(grant, latest_commit, version, configured, now=now)
    result = GrantedWorldDefinition(
        version=version.view,
        grant_id=grant_id,
        definition=BrowserWorldDefinition.from_core(version.definition),
    )
    bounded_canonical(result, configured.max_metadata_bytes)
    return result


def world_error_code(code: str) -> str:
    """Fixed adapter vocabulary; no error detail may expose hidden world content."""
    if code == "receipt_expired" or code == "recovery_required":
        return "incompatible_state"
    if code == "policy_unavailable":
        return "temporarily_unavailable"
    if code == "reauthentication_required":
        return "unauthenticated"
    if code == "ambiguous_credentials":
        return "invalid_request"
    return code
