"""Current-authorized immutable world version proposals and safe projections.

No persistence is performed. The producer locks/rechecks the current authority,
policy, scoped key and world head; atomically inserts version/head/receipt under
unique namespace and version-ID constraints, then re-reads exact closure after
a conflict or lost acknowledgement. Typed snapshots are trusted DB projections,
not client evidence and not proof that a database read is current.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Never

from pydantic import ValidationError

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.control_contracts import ContractViolation, Membership, VerifiedCredential
from strange_physics.product_authority import admit_run_ownership
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import ProductAuthority
from strange_physics.worker_contracts import OriginalExecutionAdmission
from strange_physics.workspace_contracts import WorkspaceAuthority, authorize_product
from strange_physics.world_authority import authorize_world, world_actor, world_authority_sha256
from strange_physics.world_contracts import (
    CreateWorldVersionRequest,
    WorldBrowserAuthority,
    WorldCatalogEligibility,
    WorldExpiredMutation,
    WorldHead,
    WorldMutationScope,
    WorldPage,
    WorldPolicy,
    WorldRunSelection,
    WorldVersionCommit,
    WorldVersionLookup,
    WorldVersionRecord,
    WorldVersionResult,
    WorldVersionView,
)

WORLD_JSON_DEPTH = 32
WORLD_JSON_NODES = 1_000_000


@dataclass(frozen=True)
class WorldVersionDecision:
    """Private transaction proposal, or metadata replay with commit=None."""

    result: WorldVersionResult
    commit: WorldVersionCommit | None
    authority_sha256: str
    current_policy_sha256: str


def validate_world_record(
    version: WorldVersionRecord,
    policy: WorldPolicy,
    *,
    workspace_id: str,
    world_id: str,
    version_id: str | None,
    now: int,
) -> None:
    """Incomplete bounded scope/chronology check; never authorizes a definition read."""
    bounded_canonical(version, policy.max_metadata_bytes)
    bounded_canonical(version.definition, policy.max_definition_bytes)
    view = version.view
    if (view.workspace_id, view.world_id) != (workspace_id, world_id) or (
        version_id is not None and view.version_id != version_id
    ):
        raise ContractViolation("not_found", 404)
    if view.created_at > now:
        raise ContractViolation("recovery_required", 409)


def _head(
    head: WorldHead | None,
    commit: WorldVersionCommit | None,
    policy: WorldPolicy,
    *,
    workspace_id: str,
    world_id: str,
    now: int,
) -> WorldVersionCommit:
    if head is None or commit is None:
        raise ContractViolation("recovery_required", 409)
    bounded_canonical(commit, policy.max_metadata_bytes)
    validate_world_record(
        commit.version,
        policy,
        workspace_id=workspace_id,
        world_id=world_id,
        version_id=head.version_id,
        now=now,
    )
    if head != commit.result.head or commit.committed_at > now:
        raise ContractViolation("recovery_required", 409)
    if commit.parent is not None:
        _version_history(commit.parent, commit.version)
    return commit


def _version_history(older: WorldVersionRecord, newer: WorldVersionRecord) -> None:
    old, new = older.view, newer.view
    distance = new.version_number - old.version_number
    if (
        (old.workspace_id, old.world_id) != (new.workspace_id, new.world_id)
        or distance < 0
        or old.created_at > new.created_at
        or (distance == 0 and message_sha256(older) != message_sha256(newer))
        or (distance > 0 and old.version_id == new.version_id)
        or (
            distance > 0
            and old.parent_version_id is not None
            and old.parent_version_id in (new.version_id, new.parent_version_id)
        )
        or (distance == 1 and new.parent_version_id != old.version_id)
        or (distance > 1 and new.parent_version_id == old.version_id)
    ):
        raise ContractViolation("recovery_required", 409)


def _history(target: WorldVersionRecord, current: WorldVersionCommit) -> None:
    _version_history(target, current.version)
    if target.view.version_number < current.version.view.version_number:
        # The latest commit already retains this predecessor. Compare both
        # witnesses without fetching or claiming verification of the full history.
        if current.parent is None:
            raise ContractViolation("recovery_required", 409)
        _version_history(target, current.parent)


def reject_expired_world_key(
    expired: WorldExpiredMutation,
    scope: WorldMutationScope,
    request_sha256: str,
    *,
    now: int,
) -> Never:
    """Failure-only tombstone check after current auth; not cleanup or resource authority."""
    if expired.scope != scope or expired.expires_at > now:
        raise ContractViolation("recovery_required", 409)
    if expired.request_sha256 != request_sha256:
        raise ContractViolation("idempotency_conflict", 409)
    raise ContractViolation("receipt_expired", 409)


def _version_replay(
    lookup: WorldVersionLookup,
    request: CreateWorldVersionRequest,
    policy: WorldPolicy,
    *,
    now: int,
) -> WorldVersionResult | None:
    scope = lookup.scope
    if lookup.receipt is not None and lookup.expired is not None:
        raise ContractViolation("recovery_required", 409)
    if lookup.expired is not None:
        expired = lookup.expired
        parts = (lookup.target, lookup.current_head, lookup.current_commit)
        if any(x is not None for x in parts):
            if any(x is None for x in parts):
                raise ContractViolation("recovery_required", 409)
            target = lookup.target
            if target is None:
                raise ContractViolation("recovery_required", 409)
            current = _head(
                lookup.current_head,
                lookup.current_commit,
                policy,
                workspace_id=scope.workspace_id,
                world_id=expired.allocated_world_id,
                now=now,
            )
            validate_world_record(
                target,
                policy,
                workspace_id=scope.workspace_id,
                world_id=expired.allocated_world_id,
                version_id=None,
                now=now,
            )
            _history(target, current)
        reject_expired_world_key(expired, scope, message_sha256(request), now=now)
    receipt = lookup.receipt
    if receipt is None:
        return None
    target = lookup.target
    if receipt.scope != scope or target is None:
        raise ContractViolation("recovery_required", 409)
    current = _head(
        lookup.current_head,
        lookup.current_commit,
        policy,
        workspace_id=scope.workspace_id,
        world_id=receipt.version.view.world_id,
        now=now,
    )
    validate_world_record(
        target,
        policy,
        workspace_id=scope.workspace_id,
        world_id=receipt.version.view.world_id,
        version_id=receipt.version.view.version_id,
        now=now,
    )
    if (
        message_sha256(target) != message_sha256(receipt.version)
        or receipt.committed_at > now
        or (
            current.version.view.version_id == target.view.version_id
            and message_sha256(current) != message_sha256(receipt)
        )
    ):
        raise ContractViolation("recovery_required", 409)
    _history(target, current)
    if receipt.parent is not None:
        _version_history(receipt.parent, receipt.version)
        _history(receipt.parent, current)
    if receipt.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    if now >= receipt.receipt_expires_at:
        raise ContractViolation("receipt_expired", 409)
    return receipt.result


def propose_world_version(
    raw_request: bytes,
    scope: WorldMutationScope,
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    lookup: WorldVersionLookup,
    *,
    new_world_id: str | None,
    version_id: str,
    receipt_id: str,
    now: int,
) -> WorldVersionDecision:
    """Authorize, parse bounded author input, then propose one version or safe replay.

    The raw whole author request uses the configured definition byte ceiling;
    the converted CORE definition must separately fit the same canonical cap.
    New IDs are server allocations and ignored on replay. The producer must
    check their global uniqueness in the same atomic commit.
    """
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:write",
        workspace_id=scope.workspace_id,
        mutation=True,
        now=now,
    )
    actor = world_actor(authority)
    if scope.principal_id != actor.principal_id or scope.operation != "create_version":
        raise ContractViolation("not_found", 404)
    request = parse_bounded_json(
        raw_request,
        CreateWorldVersionRequest,
        max_bytes=configured.max_definition_bytes,
        max_depth=WORLD_JSON_DEPTH,
        max_nodes=WORLD_JSON_NODES,
    )
    definition = request.definition.to_core()
    definition_sha256, _ = bounded_canonical(definition, configured.max_definition_bytes)
    bounded_canonical(lookup, configured.max_metadata_bytes)
    if lookup.scope != scope:
        raise ContractViolation("recovery_required", 409)
    if (scope.world_id is None) != (request.expected_version_id is None):
        raise ContractViolation("invalid_request", 422)
    replay = _version_replay(lookup, request, configured, now=now)
    if replay is not None:
        return WorldVersionDecision(
            replay, None, world_authority_sha256(authority), message_sha256(configured)
        )
    if scope.world_id is None:
        if any(x is not None for x in (lookup.target, lookup.current_head, lookup.current_commit)):
            raise ContractViolation("recovery_required", 409)
        if new_world_id is None:
            raise ContractViolation("invalid_request", 422)
        world_id, parent, before = new_world_id, None, None
    else:
        if new_world_id is not None:
            raise ContractViolation("invalid_request", 422)
        world_id = scope.world_id
        if lookup.current_head is None and lookup.current_commit is None and lookup.target is None:
            raise ContractViolation("not_found", 404)
        current = _head(
            lookup.current_head,
            lookup.current_commit,
            configured,
            workspace_id=scope.workspace_id,
            world_id=world_id,
            now=now,
        )
        parent, before = lookup.target, lookup.current_head
        if parent is None:
            raise ContractViolation("recovery_required", 409)
        validate_world_record(
            parent,
            configured,
            workspace_id=scope.workspace_id,
            world_id=world_id,
            version_id=request.expected_version_id,
            now=now,
        )
        _history(parent, current)
        if (
            current.result.head.version_id != request.expected_version_id
            or current.result.head.revision != request.expected_head_revision
        ):
            raise ContractViolation("incompatible_state", 409)
        known_ids = set()
        for retained in (current.version, current.parent):
            if retained is not None:
                known_ids.add(retained.view.version_id)
                if retained.view.parent_version_id is not None:
                    known_ids.add(retained.view.parent_version_id)
        if version_id in known_ids:
            raise ContractViolation("incompatible_state", 409)
    try:
        view = WorldVersionView(
            workspace_id=scope.workspace_id,
            world_id=world_id,
            version_id=version_id,
            version_number=request.expected_head_revision + 1,
            parent_version_id=request.expected_version_id,
            title=request.title,
            space=definition.space,
            created_at=now,
        )
        version = WorldVersionRecord(
            view=view,
            classification="customer_authored",
            definition=definition,
            definition_sha256=definition_sha256,
            author=actor,
        )
        result = WorldVersionResult(
            version=view,
            head=WorldHead(
                workspace_id=view.workspace_id,
                world_id=world_id,
                version_id=version_id,
                revision=view.version_number,
                changed_at=now,
            ),
        )
        commit = WorldVersionCommit(
            receipt_id=receipt_id,
            scope=scope,
            request=request,
            request_sha256=message_sha256(request),
            parent=parent,
            before=before,
            version=version,
            result=result,
            policy=configured,
            policy_sha256=message_sha256(configured),
            committed_at=now,
            receipt_expires_at=now + configured.receipt_retention_seconds,
        )
    except ValidationError:
        raise ContractViolation("invalid_request", 422) from None
    bounded_canonical(commit, configured.max_metadata_bytes)
    return WorldVersionDecision(
        result, commit, world_authority_sha256(authority), message_sha256(configured)
    )


def read_world_version(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    version: WorldVersionRecord | None,
    *,
    workspace_id: str,
    world_id: str,
    version_id: str,
    now: int,
) -> WorldVersionView:
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:read",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    if version is None:
        raise ContractViolation("not_found", 404)
    validate_world_record(
        version,
        configured,
        workspace_id=workspace_id,
        world_id=world_id,
        version_id=version_id,
        now=now,
    )
    return version.view


def read_world_head(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    head: WorldHead | None,
    current_commit: WorldVersionCommit | None,
    *,
    workspace_id: str,
    world_id: str,
    now: int,
) -> WorldHead:
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:read",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    if head is None and current_commit is None:
        raise ContractViolation("not_found", 404)
    return _head(
        head, current_commit, configured, workspace_id=workspace_id, world_id=world_id, now=now
    ).result.head


def read_world_page(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    page: WorldPage,
    *,
    workspace_id: str,
    world_id: str | None,
    now: int,
) -> WorldPage:
    """Read one trusted scoped page; cursor producers must bind scope/policy and query limits."""
    configured = authorize_world(
        authority,
        policy,
        capability="worlds:read",
        workspace_id=workspace_id,
        mutation=False,
        now=now,
    )
    if len(page.items) > configured.max_page_items:
        raise ContractViolation("invalid_request", 422)
    bounded_canonical(page, configured.max_page_bytes)
    if any(
        item.workspace_id != workspace_id
        or (world_id is not None and item.world_id != world_id)
        or item.created_at > now
        for item in page.items
    ):
        raise ContractViolation("recovery_required", 409)
    return page


def select_world_for_run(
    credential: VerifiedCredential,
    membership: Membership,
    authority: ProductAuthority,
    workspace: WorkspaceAuthority,
    policy: WorldPolicy | None,
    version: WorldVersionRecord,
    catalog: WorldCatalogEligibility,
    admission: OriginalExecutionAdmission,
    *,
    workspace_id: str,
    selection_id: str,
    now: int,
) -> WorldRunSelection:
    """NEW run creation only, using unchanged human/service runs:create authorization.

    This selection joins the existing original admission in its creation
    transaction; it never re-gates later worker/model replay on catalog liveness.
    """
    authorize_product(
        workspace,
        credential,
        membership,
        authority=authority,
        permission="runs:create",
        workspace_id=workspace_id,
        now=now,
    )
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    for item in (version, catalog, admission):
        bounded_canonical(item, policy.max_metadata_bytes)
    validate_world_record(
        version,
        policy,
        workspace_id=workspace_id,
        world_id=catalog.world_id,
        version_id=admission.request.world_version_id,
        now=now,
    )
    expected = admit_run_ownership(
        workspace,
        credential,
        membership,
        admission.admitted_run,
        authority=authority,
        run_deadline=admission.ownership.run_deadline,
        worker_scopes=admission.ownership.scopes,
        now=now,
    )
    if expected != admission.ownership:
        raise ContractViolation("incompatible_state", 409)
    try:
        selection = WorldRunSelection(
            selection_id=selection_id,
            version=version,
            catalog=catalog,
            admission=admission,
            creation_request_sha256=message_sha256(admission.request),
            selected_at=now,
        )
    except ValidationError:
        raise ContractViolation("incompatible_state", 409) from None
    bounded_canonical(selection, policy.max_metadata_bytes)
    return selection
