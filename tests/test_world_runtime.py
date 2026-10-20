"""WORLD1 actual authorization-first proposals, reads and retained closure."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.credential_authority import CredentialOwner
from strange_physics.research_contracts import message_sha256
from strange_physics.world_contracts import (
    CreateWorldVersionRequest,
    WorldBrowserAuthority,
    WorldExpiredMutation,
    WorldMutationScope,
    WorldPage,
    WorldPolicy,
    WorldVersionCommit,
    WorldVersionLookup,
    WorldVersionRecord,
    WorldVersionResult,
)
from strange_physics.world_preview_contracts import (
    IssuePreviewRequest,
    PreviewGrantLookup,
    PreviewGrantPage,
    PreviewGrantView,
    PreviewMutationCommit,
    RenewPreviewRequest,
    RevokePreviewRequest,
)
from strange_physics.world_previews import (
    disclose_world_definition,
    propose_preview_mutation,
    read_preview_grant,
    read_preview_page,
    world_error_code,
)
from strange_physics.world_versions import (
    propose_world_version,
    read_world_head,
    read_world_page,
    read_world_version,
)

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts/world.examples.json").read_text()
)


class WorldRoute(TypedDict):
    workspace_id: str
    world_id: str
    now: int


class GrantRoute(WorldRoute):
    version_id: str
    grant_id: str


def example[M: Message](kind: type[M]) -> M:
    return kind.model_validate_json(json.dumps(FIXTURES["valid"][kind.__name__]))


def changed[M: Message](value: M, **updates: Any) -> M:
    return type(value).model_validate(value.model_dump() | updates)


def raw(value: Message) -> bytes:
    return value.model_dump_json().encode()


def auth(
    now: int = 1020,
    *,
    principal: str = "principal-1",
    role: str = "owner",
    generation: int = 0,
    incarnation: int = 0,
) -> WorldBrowserAuthority:
    value = copy.deepcopy(FIXTURES["valid"]["WorldBrowserAuthority"])
    identity = value["identity"]
    session = identity["actor"]["session"]
    session.update(
        principal_id=principal,
        created_at=now - 10,
        authenticated_at=now - 10,
        last_seen_at=now,
        absolute_expires_at=now + 3590,
    )
    identity["owner"]["principal"].update(principal_id=principal, generation=generation)
    identity["owner"]["grant"]["membership"].update(principal_id=principal, role=role)
    identity["owner"]["grant"]["incarnation"] = incarnation
    identity["session_principal_generation"] = generation
    value["workspace"]["active_owner_ids"] = (
        [principal]
        if role == "owner"
        else ["other-owner" if principal == "principal-1" else "principal-1"]
    )
    return WorldBrowserAuthority.model_validate_json(json.dumps(value))


def recipient() -> CredentialOwner:
    return CredentialOwner.model_validate_json(
        json.dumps(FIXTURES["valid"]["PreviewMutationCommit"]["recipient_at_commit"])
    )


def version_scope(*, world_id: str | None = None, key: str = "create-fresh") -> WorldMutationScope:
    return WorldMutationScope(
        workspace_id="workspace-1",
        principal_id="principal-1",
        world_id=world_id,
        operation="create_version",
        key=key,
    )


def version_lookup(
    commit: WorldVersionCommit, current: WorldVersionCommit | None = None
) -> WorldVersionLookup:
    latest = commit if current is None else current
    return WorldVersionLookup(
        scope=commit.scope,
        receipt=commit,
        expired=None,
        target=commit.version,
        current_head=latest.result.head,
        current_commit=latest,
    )


def fresh_version(now: int = 1020) -> WorldVersionCommit:
    scope = version_scope()
    decision = propose_world_version(
        raw(example(CreateWorldVersionRequest)),
        scope,
        auth(now),
        example(WorldPolicy),
        WorldVersionLookup(
            scope=scope,
            receipt=None,
            expired=None,
            target=None,
            current_head=None,
            current_commit=None,
        ),
        new_world_id="world-1",
        version_id="world-version-1",
        receipt_id="receipt-1",
        now=now,
    )
    assert decision.commit is not None
    assert decision.result == decision.commit.result
    assert decision.authority_sha256 == message_sha256(auth(now))
    return decision.commit


def append_version(previous: WorldVersionCommit, now: int = 1030) -> WorldVersionCommit:
    number = previous.version.view.version_number + 1
    scope = version_scope(world_id="world-1", key=f"append-{number}")
    request = changed(
        previous.request,
        expected_version_id=previous.version.view.version_id,
        expected_head_revision=number - 1,
        title=f"Version {number}",
    )
    lookup = changed(version_lookup(previous), scope=scope, receipt=None)
    result = propose_world_version(
        raw(request),
        scope,
        auth(now),
        example(WorldPolicy),
        lookup,
        new_world_id=None,
        version_id=f"world-version-{number}",
        receipt_id=f"receipt-{number}",
        now=now,
    )
    assert result.commit is not None
    return result.commit


def preview_scope(operation: str, key: str = "preview-fresh") -> WorldMutationScope:
    return WorldMutationScope.model_validate(
        dict(
            workspace_id="workspace-1",
            principal_id="principal-1",
            world_id="world-1",
            operation=operation,
            key=key,
        )
    )


def preview_lookup(
    receipt: PreviewMutationCommit, current: PreviewMutationCommit | None = None
) -> PreviewGrantLookup:
    latest = receipt if current is None else current
    return PreviewGrantLookup(
        scope=receipt.scope,
        receipt=receipt,
        expired=None,
        grant=latest.after,
        latest_commit=latest,
    )


def issue(now: int = 1020) -> PreviewMutationCommit:
    scope = preview_scope("issue_preview")
    result = propose_preview_mutation(
        raw(example(IssuePreviewRequest)),
        scope,
        auth(now),
        example(WorldPolicy),
        example(WorldVersionRecord),
        PreviewGrantLookup(scope=scope, receipt=None, expired=None, grant=None, latest_commit=None),
        recipient(),
        grant_id="grant-fresh",
        receipt_id="preview-receipt",
        now=now,
    )
    assert result.commit is not None
    return result.commit


def transition(
    old: PreviewMutationCommit,
    operation: str,
    now: int,
    *,
    ttl_seconds: int = 400,
) -> PreviewMutationCommit:
    scope = preview_scope(operation, key=f"{operation}-{old.after.revision}")
    if operation == "renew_preview":
        request: Message = RenewPreviewRequest(
            grant_id=old.after.grant_id,
            expected_revision=old.after.revision,
            ttl_seconds=ttl_seconds,
        )
    else:
        request = RevokePreviewRequest(
            grant_id=old.after.grant_id,
            expected_revision=old.after.revision,
        )
    lookup = changed(preview_lookup(old), scope=scope, receipt=None)
    result = propose_preview_mutation(
        raw(request),
        scope,
        auth(now),
        example(WorldPolicy),
        old.version,
        lookup,
        recipient() if operation == "renew_preview" else None,
        grant_id="ignored-existing-id",
        receipt_id=f"{operation}-receipt",
        now=now,
    )
    assert result.commit is not None
    return result.commit


def tombstone(commit: WorldVersionCommit | PreviewMutationCommit) -> WorldExpiredMutation:
    return WorldExpiredMutation(
        scope=commit.scope,
        request_sha256=commit.request_sha256,
        receipt_id=commit.receipt_id,
        allocated_world_id=commit.version.view.world_id,
        policy_sha256=message_sha256(commit.policy),
        retention_seconds=commit.policy.receipt_retention_seconds,
        committed_at=commit.committed_at,
        expires_at=commit.receipt_expires_at,
    )


def test_create_append_and_old_receipt_replay_do_not_allocate() -> None:
    first = fresh_version()
    second = append_version(first)
    third = append_version(second, 1040)
    replay = propose_world_version(
        raw(first.request),
        first.scope,
        auth(1050),
        example(WorldPolicy),
        version_lookup(first, third),
        new_world_id="would-duplicate",
        version_id="would-duplicate-version",
        receipt_id="would-duplicate-receipt",
        now=1050,
    )
    assert replay.commit is None
    assert replay.result == first.result
    assert third.version.view.parent_version_id == second.version.view.version_id


@pytest.mark.parametrize("mask", range(1, 15))
def test_version_partial_lookup_never_means_fresh_absence(mask: int) -> None:
    first = fresh_version()
    lookup = version_lookup(first)
    fields = ("receipt", "target", "current_head", "current_commit")
    lookup = changed(
        lookup,
        **{
            name: getattr(lookup, name) if mask & (1 << i) else None
            for i, name in enumerate(fields)
        },
    )
    with pytest.raises(ContractViolation, match="recovery_required"):
        propose_world_version(
            raw(first.request),
            first.scope,
            auth(1030),
            example(WorldPolicy),
            lookup,
            new_world_id="new-id",
            version_id="new-version",
            receipt_id="new-receipt",
            now=1030,
        )


def test_version_changed_body_stale_head_and_missing_head() -> None:
    first = fresh_version()
    second = append_version(first)
    with pytest.raises(ContractViolation, match="idempotency_conflict"):
        propose_world_version(
            raw(changed(first.request, title="Changed")),
            first.scope,
            auth(1040),
            example(WorldPolicy),
            version_lookup(first, second),
            new_world_id="ignored",
            version_id="ignored",
            receipt_id="ignored",
            now=1040,
        )
    scope = version_scope(world_id="world-1", key="stale-append")
    request = changed(
        first.request, expected_version_id="world-version-1", expected_head_revision=1
    )
    lookup = changed(version_lookup(first, second), scope=scope, receipt=None)
    with pytest.raises(ContractViolation, match="incompatible_state"):
        propose_world_version(
            raw(request),
            scope,
            auth(1040),
            example(WorldPolicy),
            lookup,
            new_world_id=None,
            version_id="third",
            receipt_id="third-receipt",
            now=1040,
        )


@pytest.mark.parametrize("retain", [False, True])
@pytest.mark.parametrize("changed_body", [False, True])
def test_expired_world_key_preserves_uniqueness_without_resource_success(
    retain: bool,
    changed_body: bool,
) -> None:
    first = fresh_version()
    now = first.receipt_expires_at
    lookup = changed(
        version_lookup(first),
        receipt=None,
        expired=tombstone(first),
        **({} if retain else dict(target=None, current_head=None, current_commit=None)),
    )
    request = changed(first.request, title="Different") if changed_body else first.request
    with pytest.raises(ContractViolation) as caught:
        propose_world_version(
            raw(request),
            first.scope,
            auth(now),
            example(WorldPolicy),
            lookup,
            new_world_id="never-created",
            version_id="never-created",
            receipt_id="never",
            now=now,
        )
    assert caught.value.code == ("idempotency_conflict" if changed_body else "receipt_expired")


def test_live_world_receipt_expires_even_before_response_cleanup() -> None:
    first = fresh_version()
    now = first.receipt_expires_at
    with pytest.raises(ContractViolation, match="receipt_expired"):
        propose_world_version(
            raw(first.request),
            first.scope,
            auth(now),
            example(WorldPolicy),
            version_lookup(first),
            new_world_id=None,
            version_id="unused",
            receipt_id="unused",
            now=now,
        )


@pytest.mark.parametrize("mutation", ["both", "future", "partial", "foreign"])
def test_expired_world_contradictions_fail_recovery(mutation: str) -> None:
    first = fresh_version()
    expired = tombstone(first)
    lookup = changed(version_lookup(first), receipt=None, expired=expired)
    now = expired.expires_at
    if mutation == "both":
        lookup = changed(lookup, receipt=first)
    elif mutation == "future":
        now -= 1
    elif mutation == "partial":
        lookup = changed(lookup, current_commit=None)
    else:
        bad_scope = changed(first.scope, key="other-key")
        lookup = changed(lookup, expired=changed(expired, scope=bad_scope))
    with pytest.raises(ContractViolation, match="recovery_required"):
        propose_world_version(
            raw(first.request),
            first.scope,
            auth(now),
            example(WorldPolicy),
            lookup,
            new_world_id=None,
            version_id="unused",
            receipt_id="unused",
            now=now,
        )


def test_retained_target_canonical_identity_cannot_change_signed_zero() -> None:
    first = fresh_version()
    data = first.version.model_dump(mode="json")
    data["definition"]["space"]["sampling"]["position_noise"] = -0.0
    data["view"]["space"]["sampling"]["position_noise"] = -0.0
    from strange_physics.worlds import WorldDefinition

    data["definition_sha256"] = message_sha256(
        WorldDefinition.model_validate_json(json.dumps(data["definition"]))
    )
    target = WorldVersionRecord.model_validate_json(json.dumps(data))
    assert target.definition == first.version.definition
    assert target.view == first.version.view
    assert message_sha256(target) != message_sha256(first.version)
    with pytest.raises(ContractViolation, match="recovery_required"):
        propose_world_version(
            raw(first.request),
            first.scope,
            auth(1030),
            example(WorldPolicy),
            changed(version_lookup(first), target=target),
            new_world_id=None,
            version_id="unused",
            receipt_id="unused",
            now=1030,
        )


@pytest.mark.parametrize(
    "payload",
    [b"not-json", b" " * 65537, b'{"title":NaN}'],
    ids=["syntax", "oversize", "nonfinite"],
)
def test_world_mutation_denied_before_private_lookup_or_parse(payload: bytes) -> None:
    current = auth(role="viewer")
    with pytest.raises(ContractViolation, match="forbidden"):
        propose_world_version(
            payload,
            version_scope(),
            current,
            example(WorldPolicy),
            cast(WorldVersionLookup, object()),
            new_world_id=None,
            version_id="unused",
            receipt_id="unused",
            now=1020,
        )


def test_raw_author_cap_and_stricter_current_policy() -> None:
    first = fresh_version()
    for policy in [
        changed(example(WorldPolicy), max_definition_bytes=len(raw(first.request)) - 1),
        changed(example(WorldPolicy), max_metadata_bytes=10),
    ]:
        with pytest.raises(ContractViolation, match="invalid_request"):
            propose_world_version(
                raw(first.request),
                first.scope,
                auth(1030),
                policy,
                version_lookup(first),
                new_world_id=None,
                version_id="unused",
                receipt_id="unused",
                now=1030,
            )


def test_safe_world_reads_and_bounds() -> None:
    first = fresh_version()
    viewer = auth(role="viewer")
    args: WorldRoute = dict(workspace_id="workspace-1", world_id="world-1", now=1020)
    assert (
        read_world_version(
            viewer, example(WorldPolicy), first.version, version_id="world-version-1", **args
        )
        == first.version.view
    )
    assert (
        read_world_head(viewer, example(WorldPolicy), first.result.head, first, **args)
        == first.result.head
    )
    page = WorldPage(items=(first.version.view,), next_cursor=None)
    assert read_world_page(viewer, example(WorldPolicy), page, **args) == page
    with pytest.raises(ContractViolation, match="invalid_request"):
        read_world_page(viewer, changed(example(WorldPolicy), max_page_bytes=10), page, **args)
    with pytest.raises(ContractViolation, match="recovery_required"):
        read_world_head(viewer, example(WorldPolicy), first.result.head, None, **args)
    official = changed(first.version, classification="official_blind")
    assert (
        read_world_version(
            viewer, example(WorldPolicy), official, version_id="world-version-1", **args
        )
        == official.view
    )


def test_issue_renew_revoke_and_original_safe_replay() -> None:
    first = issue()
    renewed = transition(first, "renew_preview", 1030)
    revoked = transition(renewed, "revoke_preview", 1040)
    result = propose_preview_mutation(
        raw(first.request),
        first.scope,
        auth(1050),
        example(WorldPolicy),
        first.version,
        preview_lookup(first, revoked),
        None,
        grant_id="never-allocated",
        receipt_id="never-created",
        now=1050,
    )
    assert result.commit is None and result.result == first.result
    assert revoked.after.revoked_at == 1040
    assert revoked.recipient_at_commit is None


@pytest.mark.parametrize(
    "recipient_state", ["absent", "inactive", "new_generation", "new_incarnation"]
)
def test_historical_metadata_replay_does_not_reauthorize_old_recipient(
    recipient_state: str,
) -> None:
    first = issue()
    who = recipient()
    if recipient_state == "absent":
        current = None
    elif recipient_state == "inactive":
        current = changed(who, principal=changed(who.principal, active=False))
    elif recipient_state == "new_generation":
        current = changed(who, principal=changed(who.principal, generation=1))
    else:
        current = changed(who, grant=changed(who.grant, incarnation=1))
    now = first.after.expires_at + 1
    result = propose_preview_mutation(
        raw(first.request),
        first.scope,
        auth(now),
        example(WorldPolicy),
        first.version,
        preview_lookup(first),
        current,
        grant_id="unused",
        receipt_id="unused",
        now=now,
    )
    assert result.commit is None and result.result == first.result


@pytest.mark.parametrize("mask", range(1, 7))
def test_preview_partial_lookup_does_not_create_duplicate_grant(mask: int) -> None:
    first = issue()
    lookup = preview_lookup(first)
    fields = ("receipt", "grant", "latest_commit")
    lookup = changed(
        lookup,
        **{
            name: getattr(lookup, name) if mask & (1 << i) else None
            for i, name in enumerate(fields)
        },
    )
    with pytest.raises(ContractViolation, match="recovery_required"):
        propose_preview_mutation(
            raw(first.request),
            first.scope,
            auth(1030),
            example(WorldPolicy),
            first.version,
            lookup,
            recipient(),
            grant_id="unused",
            receipt_id="unused",
            now=1030,
        )


@pytest.mark.parametrize("retain", [False, True])
def test_expired_preview_key_without_resource_cannot_allocate(retain: bool) -> None:
    first = issue()
    now = first.receipt_expires_at
    lookup = changed(
        preview_lookup(first),
        receipt=None,
        expired=tombstone(first),
        **({} if retain else dict(grant=None, latest_commit=None)),
    )
    with pytest.raises(ContractViolation, match="receipt_expired"):
        propose_preview_mutation(
            raw(first.request),
            first.scope,
            auth(now),
            example(WorldPolicy),
            first.version if retain else None,
            lookup,
            None,
            grant_id="never-allocated",
            receipt_id="never-created",
            now=now,
        )


@pytest.mark.parametrize("change", ["generation", "incarnation", "inactive", "removed", "role"])
def test_new_renewal_requires_current_recipient(change: str) -> None:
    first = issue()
    who = recipient()
    if change == "generation":
        who = changed(who, principal=changed(who.principal, generation=1))
    elif change == "incarnation":
        who = changed(who, grant=changed(who.grant, incarnation=1))
    elif change == "inactive":
        who = changed(who, principal=changed(who.principal, active=False))
    elif change == "removed":
        who = changed(
            who, grant=changed(who.grant, membership=changed(who.grant.membership, active=False))
        )
    policy = example(WorldPolicy)
    if change == "role":
        policy = changed(policy, preview_reader_roles=("owner",))
    scope = preview_scope("renew_preview")
    request = RenewPreviewRequest(
        grant_id=first.after.grant_id, expected_revision=1, ttl_seconds=400
    )
    with pytest.raises(ContractViolation, match="forbidden"):
        propose_preview_mutation(
            raw(request),
            scope,
            auth(1030),
            policy,
            first.version,
            changed(preview_lookup(first), scope=scope, receipt=None),
            who,
            grant_id="unused",
            receipt_id="renew",
            now=1030,
        )


@pytest.mark.parametrize("terminal", ["expired", "revoked"])
def test_new_key_cannot_revive_grant(terminal: str) -> None:
    first = issue()
    current = transition(first, "revoke_preview", 1030) if terminal == "revoked" else first
    now = 1040 if terminal == "revoked" else first.after.expires_at
    scope = preview_scope("renew_preview")
    request = RenewPreviewRequest(
        grant_id=current.after.grant_id, expected_revision=current.after.revision, ttl_seconds=400
    )
    with pytest.raises(ContractViolation, match="incompatible_state"):
        propose_preview_mutation(
            raw(request),
            scope,
            auth(now),
            example(WorldPolicy),
            current.version,
            changed(preview_lookup(current), scope=scope, receipt=None),
            recipient(),
            grant_id="unused",
            receipt_id="renew",
            now=now,
        )


def test_revoke_after_expiry_and_recipient_departure() -> None:
    first = issue()
    revoked = transition(first, "revoke_preview", first.after.expires_at + 1)
    assert revoked.after.revoked_at == first.after.expires_at + 1
    assert revoked.after.expires_at == first.after.expires_at


def disclosure(
    first: PreviewMutationCommit, current: WorldBrowserAuthority, now: int = 1030
) -> Message:
    return disclose_world_definition(
        current,
        example(WorldPolicy),
        first.version,
        first.after,
        first,
        workspace_id="workspace-1",
        world_id="world-1",
        version_id=first.after.version_id,
        grant_id=first.after.grant_id,
        now=now,
    )


def test_explicit_recipient_can_preview_owner_creator_cannot() -> None:
    first = issue()
    who = first.after.recipient
    reader = auth(
        1030,
        principal=who.principal_id,
        role="viewer",
        generation=who.principal_generation,
        incarnation=who.grant_incarnation,
    )
    result = disclosure(first, reader)
    assert result.model_dump()["definition"]["noise_seed"] == str(
        first.version.definition.noise_seed
    )
    with pytest.raises(ContractViolation, match="not_found"):
        disclosure(first, auth(1030))
    metadata = read_preview_grant(
        auth(1030),
        example(WorldPolicy),
        first.version,
        first.after,
        first,
        workspace_id="workspace-1",
        world_id="world-1",
        grant_id=first.after.grant_id,
        now=1030,
    )
    assert metadata == first.result and "definition" not in metadata.model_dump()


@pytest.mark.parametrize("change", ["generation", "incarnation", "expired", "revoked", "official"])
def test_disclosure_rechecks_live_grant_and_recipient(change: str) -> None:
    first = issue()
    now = 1030
    who = first.after.recipient
    reader = auth(
        now,
        principal=who.principal_id,
        role="viewer",
        generation=who.principal_generation + int(change == "generation"),
        incarnation=who.grant_incarnation + int(change == "incarnation"),
    )
    grant = first.after
    latest = first
    version = first.version
    if change == "expired":
        now = grant.expires_at
        reader = auth(
            now,
            principal=who.principal_id,
            role="viewer",
            generation=who.principal_generation,
            incarnation=who.grant_incarnation,
        )
    elif change == "revoked":
        latest = transition(first, "revoke_preview", now)
        grant = latest.after
    elif change == "official":
        version = changed(version, classification="official_blind")
    with pytest.raises(ContractViolation, match="forbidden"):
        disclose_world_definition(
            reader,
            example(WorldPolicy),
            version,
            grant,
            latest,
            workspace_id="workspace-1",
            world_id="world-1",
            version_id=grant.version_id,
            grant_id=grant.grant_id,
            now=now,
        )


def test_permitted_role_transition_and_policy_restoration() -> None:
    first = issue()
    who = first.after.recipient
    reader = auth(
        1030,
        principal=who.principal_id,
        role="researcher",
        generation=who.principal_generation,
        incarnation=who.grant_incarnation,
    )
    disclosure(first, reader)
    args: GrantRoute = dict(
        workspace_id="workspace-1",
        world_id="world-1",
        version_id=first.after.version_id,
        grant_id=first.after.grant_id,
        now=1030,
    )
    with pytest.raises(ContractViolation, match="forbidden"):
        disclose_world_definition(
            reader,
            changed(example(WorldPolicy), preview_reader_roles=("owner",)),
            first.version,
            first.after,
            first,
            **args,
        )
    disclose_world_definition(
        reader, example(WorldPolicy), first.version, first.after, first, **args
    )


def test_preview_metadata_page_is_owner_only_and_bounded() -> None:
    first = issue()
    page = PreviewGrantPage(items=(first.result,), next_cursor=None)
    args: WorldRoute = dict(workspace_id="workspace-1", world_id="world-1", now=1030)
    assert read_preview_page(auth(1030), example(WorldPolicy), page, **args) == page
    with pytest.raises(ContractViolation, match="forbidden"):
        read_preview_page(auth(1030, role="viewer"), example(WorldPolicy), page, **args)
    with pytest.raises(ContractViolation, match="invalid_request"):
        read_preview_page(
            auth(1030), changed(example(WorldPolicy), max_page_bytes=10), page, **args
        )


@pytest.mark.parametrize("operation", ["issue_preview", "renew_preview", "revoke_preview"])
def test_preview_mutations_authorize_before_poisoned_state(operation: str) -> None:
    with pytest.raises(ContractViolation, match="forbidden"):
        propose_preview_mutation(
            b"invalid",
            preview_scope(operation),
            auth(role="viewer"),
            example(WorldPolicy),
            cast(WorldVersionRecord, object()),
            cast(PreviewGrantLookup, object()),
            None,
            grant_id="unused",
            receipt_id="unused",
            now=1020,
        )


def test_fixed_wire_error_vocabulary() -> None:
    assert world_error_code("receipt_expired") == "incompatible_state"
    assert world_error_code("recovery_required") == "incompatible_state"
    assert world_error_code("policy_unavailable") == "temporarily_unavailable"
    assert world_error_code("forbidden") == "forbidden"
    assert world_error_code("reauthentication_required") == "unauthenticated"
    assert world_error_code("ambiguous_credentials") == "invalid_request"


def run_selection_args(kind: str = "user", advanced_result: bool = False) -> dict[str, Any]:
    from strange_physics.control_contracts import VerifiedCredential
    from strange_physics.run_credential_contracts import ProductAuthority, ServiceProductAuthority
    from strange_physics.worker_contracts import OriginalExecutionAdmission
    from strange_physics.world_contracts import WorldCatalogEligibility

    now = 1000 if kind == "user" else 1200
    current = auth(now)
    data = copy.deepcopy(FIXTURES["valid"]["WorldRunSelection"])
    admission_data = data["admission"]
    identity: ProductAuthority
    if kind == "user":
        identity = current.identity
        member = identity.owner.grant.membership
        credential = VerifiedCredential(
            issuer="verified-app-session",
            subject=member.principal_id,
            principal_id=member.principal_id,
            credential_id=identity.actor.session.session_id,
            kind="user",
            workspace_id=member.workspace_id,
            scopes=("runs:create",),
            expires_at=identity.actor.session.absolute_expires_at,
            revoked=False,
        )
    else:
        service_data = json.loads(
            (
                Path(__file__).resolve().parents[1] / "contracts/run-credentials.examples.json"
            ).read_text()
        )["valid"]["ServiceProductAuthority"]
        service_data["current"]["records"][0]["key"]["scopes"] = ["runs:create", "runs:read"]
        identity = ServiceProductAuthority.model_validate_json(json.dumps(service_data))
        member = identity.current.principal.grant.membership
        key = identity.current.records[0].key
        credential = VerifiedCredential(
            issuer="verified-workspace-service",
            subject=member.principal_id,
            principal_id=member.principal_id,
            credential_id=key.credential_id,
            kind="service",
            workspace_id=member.workspace_id,
            scopes=key.scopes,
            expires_at=key.expires_at,
            revoked=False,
        )
        admission_data["ownership"].update(
            principal_id=member.principal_id,
            principal_kind="service",
            principal_generation=identity.current.principal.authority_generation,
            grant_incarnation=identity.current.principal.grant.incarnation,
            created_by_credential_id=key.credential_id,
            created_at=now,
        )
        admission_data["stored_request"]["scope"]["principal_id"] = member.principal_id
    if advanced_result:
        admission_data["stored_request"]["operation"]["result"]["value"].update(
            status="running", revision=1
        )
    admission = OriginalExecutionAdmission.model_validate_json(json.dumps(admission_data))
    catalog = WorldCatalogEligibility.model_validate(data["catalog"] | {"observed_at": now})
    return dict(
        credential=credential,
        membership=member,
        authority=identity,
        workspace=current.workspace,
        policy=example(WorldPolicy),
        version=example(WorldVersionRecord),
        catalog=catalog,
        admission=admission,
        workspace_id="workspace-1",
        selection_id="selected-new-run",
        now=now,
    )


@pytest.mark.parametrize("kind", ["user", "service"])
@pytest.mark.parametrize("advanced_result", [False, True])
def test_run_selection_preserves_existing_human_service_and_later_result_semantics(
    kind: str,
    advanced_result: bool,
) -> None:
    from strange_physics.world_versions import select_world_for_run

    args = run_selection_args(kind, advanced_result)
    result = select_world_for_run(**args)
    assert result.admission == args["admission"]
    assert result.version.author.principal_id == "principal-1"
    if kind == "service":
        assert result.admission.ownership.principal_id == "service-1"


@pytest.mark.parametrize("kind", ["user", "service"])
@pytest.mark.parametrize(
    "change", ["catalog_hash", "withdrawn", "budget", "space_zero", "principal"]
)
def test_new_run_selection_rejects_wrong_current_selection(kind: str, change: str) -> None:
    from strange_physics.worker_contracts import OriginalExecutionAdmission
    from strange_physics.world_versions import select_world_for_run

    args = run_selection_args(kind)
    if change == "catalog_hash":
        args["catalog"] = changed(args["catalog"], definition_sha256="f" * 64)
    elif change == "withdrawn":
        args["catalog"] = changed(args["catalog"], eligible_for_new_runs=False)
    elif change in {"budget", "space_zero"}:
        data = args["admission"].model_dump(mode="json")
        run = data["admitted_run"]
        stored = data["stored_request"]["operation"]["result"]["value"]
        if change == "budget":
            for projection in (run, stored):
                projection["space"]["budget"] = 7
                projection["budget_remaining"] = 7
            data["request"]["experiment_budget"] = 7
            from strange_physics.control_contracts import CreateRunRequest

            digest = message_sha256(CreateRunRequest.model_validate(data["request"]))
            data["stored_request"]["request_sha256"] = digest
            data["stored_request"]["operation"]["request_sha256"] = digest
        else:
            for projection in (run, stored):
                projection["space"]["sampling"]["position_noise"] = -0.0
        args["admission"] = OriginalExecutionAdmission.model_validate_json(json.dumps(data))
    else:
        owner = args["admission"].ownership
        data = args["admission"].model_dump(mode="json")
        data["ownership"]["principal_id"] = owner.principal_id + "-other"
        data["stored_request"]["scope"]["principal_id"] = owner.principal_id + "-other"
        args["admission"] = OriginalExecutionAdmission.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="incompatible_state"):
        select_world_for_run(**args)


@pytest.mark.parametrize(
    "operation",
    [
        "version",
        "head",
        "world_page",
        "grant",
        "grant_page",
        "definition",
        "run_selection",
    ],
)
def test_every_exported_read_selection_guard_precedes_poisoned_private_state(
    operation: str,
) -> None:
    from strange_physics.world_versions import select_world_for_run

    current = auth()
    current = changed(
        current,
        identity=changed(
            current.identity,
            owner=changed(
                current.identity.owner,
                principal=changed(current.identity.owner.principal, active=False),
            ),
        ),
    )
    poison: Any = object()
    route: WorldRoute = dict(workspace_id="workspace-1", world_id="world-1", now=1020)
    with pytest.raises(ContractViolation, match="unauthenticated"):
        if operation == "version":
            read_world_version(current, example(WorldPolicy), poison, version_id="version", **route)
        elif operation == "head":
            read_world_head(current, example(WorldPolicy), poison, poison, **route)
        elif operation == "world_page":
            read_world_page(current, example(WorldPolicy), poison, **route)
        elif operation == "grant":
            read_preview_grant(
                current, example(WorldPolicy), poison, poison, poison, grant_id="grant", **route
            )
        elif operation == "grant_page":
            read_preview_page(current, example(WorldPolicy), poison, **route)
        elif operation == "definition":
            disclose_world_definition(
                current,
                example(WorldPolicy),
                poison,
                poison,
                poison,
                version_id="version",
                grant_id="grant",
                **route,
            )
        else:
            args = run_selection_args()
            args.update(
                authority=current.identity,
                version=poison,
                catalog=poison,
                admission=poison,
                now=1020,
            )
            # Keep credential/session duplicate projections coherent so inactivity is the denial.
            args["credential"] = changed(
                args["credential"], expires_at=current.identity.actor.session.absolute_expires_at
            )
            select_world_for_run(**args)


@pytest.mark.parametrize(
    "change", ["wrong_body", "full_and_expired", "partial_after_expiry", "wrong_latest"]
)
def test_preview_recovery_rejects_contradictory_metadata(change: str) -> None:
    first = issue()
    now = 1030
    request = first.request
    lookup = preview_lookup(first)
    if change == "wrong_body":
        assert isinstance(first.request, IssuePreviewRequest)
        request = changed(first.request, ttl_seconds=first.request.ttl_seconds + 1)
    elif change == "full_and_expired":
        now = first.receipt_expires_at
        lookup = changed(lookup, expired=tombstone(first))
    elif change == "partial_after_expiry":
        now = first.receipt_expires_at
        lookup = changed(lookup, receipt=None, expired=tombstone(first), latest_commit=None)
    else:
        # Independently valid new grant cannot replace this retained grant's latest transition.
        other = issue()
        data = other.model_dump(mode="json")
        data["after"]["grant_id"] = "other-grant"
        data["result"]["grant_id"] = "other-grant"
        lookup = changed(
            lookup, latest_commit=PreviewMutationCommit.model_validate_json(json.dumps(data))
        )
    with pytest.raises(ContractViolation) as caught:
        propose_preview_mutation(
            raw(request),
            first.scope,
            auth(now),
            example(WorldPolicy),
            first.version,
            lookup,
            None,
            grant_id="unused",
            receipt_id="unused",
            now=now,
        )
    assert caught.value.code == (
        "idempotency_conflict" if change == "wrong_body" else "recovery_required"
    )


def replay_version(receipt: WorldVersionCommit, latest: WorldVersionCommit) -> WorldVersionResult:
    result = propose_world_version(
        raw(receipt.request),
        receipt.scope,
        auth(1060),
        example(WorldPolicy),
        version_lookup(receipt, latest),
        new_world_id=None,
        version_id="ignored",
        receipt_id="ignored",
        now=1060,
    )
    assert result.commit is None
    return result.result


def replay_preview(
    receipt: PreviewMutationCommit, latest: PreviewMutationCommit
) -> PreviewGrantView:
    result = propose_preview_mutation(
        raw(receipt.request),
        receipt.scope,
        auth(1060),
        example(WorldPolicy),
        receipt.version,
        preview_lookup(receipt, latest),
        None,
        grant_id="ignored",
        receipt_id="ignored",
        now=1060,
    )
    assert result.commit is None
    return result.result


@pytest.mark.parametrize(
    "contradiction",
    [
        "predecessor_time",
        "adjacent_parent_id",
        "predecessor_reused_id",
        "distant_parent_reused_id",
        "same_ordinal_different_content",
    ],
)
def test_version_replay_checks_available_predecessor(contradiction: str) -> None:
    first = fresh_version(1020)
    second = append_version(first, 1030)
    third = append_version(second, 1040)
    fourth = append_version(third, 1050)
    target, latest = first, fourth
    if contradiction == "adjacent_parent_id":
        latest = third
    elif contradiction == "same_ordinal_different_content":
        target = third
    data = latest.model_dump(mode="json")
    if contradiction == "predecessor_time":
        data["parent"]["view"]["created_at"] = 1010
        data["before"]["changed_at"] = 1010
    elif contradiction == "adjacent_parent_id":
        data["parent"]["view"]["parent_version_id"] = "alternate-version-1"
    elif contradiction == "predecessor_reused_id":
        data["parent"]["view"]["version_id"] = first.version.view.version_id
        data["before"]["version_id"] = first.version.view.version_id
        data["request"]["expected_version_id"] = first.version.view.version_id
        data["request_sha256"] = message_sha256(
            CreateWorldVersionRequest.model_validate_json(json.dumps(data["request"]))
        )
        data["version"]["view"]["parent_version_id"] = first.version.view.version_id
        data["result"]["version"]["parent_version_id"] = first.version.view.version_id
    elif contradiction == "distant_parent_reused_id":
        data["parent"]["view"]["parent_version_id"] = first.version.view.version_id
    else:
        data["parent"]["view"]["title"] = "Different retained predecessor"
    contradictory = WorldVersionCommit.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="recovery_required"):
        replay_version(target, contradictory)


@pytest.mark.parametrize("equal_times", [False, True])
@pytest.mark.parametrize("target_number", [1, 2, 3, 4])
def test_version_history_preserves_current_adjacent_and_older_replay(
    equal_times: bool, target_number: int
) -> None:
    history = [fresh_version(1020)]
    for i in range(3):
        history.append(append_version(history[-1], 1020 if equal_times else 1030 + i * 10))
    target = history[target_number - 1]
    assert replay_version(target, history[-1]) == target.result


@pytest.mark.parametrize(
    "contradiction",
    ["unchanged_expiry", "insufficient_expiry_steps", "predecessor_time", "revoked_target"],
)
def test_preview_replay_checks_available_predecessor(contradiction: str) -> None:
    first = issue(1020)
    second = transition(first, "renew_preview", 1030)
    third = transition(second, "renew_preview", 1040)
    fourth = transition(third, "renew_preview", 1050)
    target, latest = first, third
    if contradiction == "predecessor_time":
        target, latest = second, fourth
    elif contradiction == "insufficient_expiry_steps":
        latest = fourth
    elif contradiction == "revoked_target":
        target, latest = transition(first, "revoke_preview", 1030), fourth
    data = latest.model_dump(mode="json")
    if contradiction in {"unchanged_expiry", "insufficient_expiry_steps"}:
        extra = 0 if contradiction == "unchanged_expiry" else 2
        expiry = first.after.expires_at + extra
        data["before"]["expires_at"] = expiry - 1
        data["after"]["expires_at"] = expiry
        data["result"]["expires_at"] = expiry
        data["request"]["ttl_seconds"] = expiry - data["committed_at"]
        data["request_sha256"] = message_sha256(
            RenewPreviewRequest.model_validate_json(json.dumps(data["request"]))
        )
    elif contradiction == "predecessor_time":
        data["before"]["updated_at"] = 1025
    contradictory = PreviewMutationCommit.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="recovery_required"):
        replay_preview(target, contradictory)


@pytest.mark.parametrize("revoke", [False, True])
@pytest.mark.parametrize("target_revision", [1, 2, 3, 4])
def test_preview_history_preserves_equal_time_minimum_expiry_steps(
    revoke: bool, target_revision: int
) -> None:
    history = [issue(1020)]
    for i in range(3):
        history.append(transition(history[-1], "renew_preview", 1020, ttl_seconds=101 + i))
    if revoke:
        history.append(transition(history[-1], "revoke_preview", 1020))
    target = history[target_revision - 1]
    assert replay_preview(target, history[-1]) == target.result


def test_preview_history_preserves_same_revocation_and_sole_revoke_expiry() -> None:
    first = issue(1020)
    revoked = transition(first, "revoke_preview", 1020)
    assert revoked.after.expires_at == first.after.expires_at
    assert replay_preview(first, revoked) == first.result
    assert replay_preview(revoked, revoked) == revoked.result


def test_preview_history_counts_renewals_before_final_revocation() -> None:
    first = issue(1020)
    second = transition(first, "renew_preview", 1030)
    third = transition(second, "renew_preview", 1040)
    revoked = transition(third, "revoke_preview", 1050)
    data = revoked.model_dump(mode="json")
    for field in ("before", "after", "result"):
        data[field]["expires_at"] = first.after.expires_at + 1
    contradictory = PreviewMutationCommit.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="recovery_required"):
        replay_preview(first, contradictory)


@pytest.mark.parametrize(
    "reuse_as",
    [
        "latest_id",
        "latest_parent_id",
        "older_grandparent",
        "grandparent_latest_id",
        "grandparent_reference",
    ],
)
def test_version_history_rejects_reuse_of_known_earlier_parent_ids(reuse_as: str) -> None:
    first = fresh_version(1020)
    second = append_version(first, 1030)
    third = append_version(second, 1040)
    fourth = append_version(third, 1050)
    fifth = append_version(fourth, 1055)
    sixth = append_version(fifth, 1058)
    target, latest = second, fourth
    if reuse_as in {"older_grandparent", "grandparent_latest_id", "grandparent_reference"}:
        target, latest = third, sixth
    data = latest.model_dump(mode="json")
    if reuse_as in {"latest_id", "grandparent_latest_id"}:
        data["version"]["view"]["version_id"] = first.version.view.version_id
        data["result"]["version"]["version_id"] = first.version.view.version_id
        data["result"]["head"]["version_id"] = first.version.view.version_id
    elif reuse_as == "grandparent_reference":
        data["parent"]["view"]["parent_version_id"] = first.version.view.version_id
    else:
        data["parent"]["view"]["version_id"] = first.version.view.version_id
        data["before"]["version_id"] = first.version.view.version_id
        data["request"]["expected_version_id"] = first.version.view.version_id
        data["request_sha256"] = message_sha256(
            CreateWorldVersionRequest.model_validate_json(json.dumps(data["request"]))
        )
        data["version"]["view"]["parent_version_id"] = first.version.view.version_id
        data["result"]["version"]["parent_version_id"] = first.version.view.version_id
    contradictory = WorldVersionCommit.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="recovery_required"):
        replay_version(target, contradictory)


@pytest.mark.parametrize("version_number", [1, 2, 3])
def test_safe_head_read_checks_normal_current_predecessor(version_number: int) -> None:
    history = [fresh_version(1020)]
    for i in range(2):
        history.append(append_version(history[-1], 1030 + i * 10))
    latest = history[version_number - 1]
    assert (
        read_world_head(
            auth(1060),
            example(WorldPolicy),
            latest.result.head,
            latest,
            workspace_id="workspace-1",
            world_id="world-1",
            now=1060,
        )
        == latest.result.head
    )


def test_safe_head_read_rejects_id_reused_from_its_retained_grandparent() -> None:
    first = fresh_version(1020)
    second = append_version(first, 1030)
    third = append_version(second, 1040)
    data = third.model_dump(mode="json")
    data["parent"]["view"]["parent_version_id"] = third.version.view.version_id
    contradictory = WorldVersionCommit.model_validate_json(json.dumps(data))
    with pytest.raises(ContractViolation, match="recovery_required"):
        read_world_head(
            auth(1060),
            example(WorldPolicy),
            contradictory.result.head,
            contradictory,
            workspace_id="workspace-1",
            world_id="world-1",
            now=1060,
        )


@pytest.mark.parametrize("equal_times", [False, True])
@pytest.mark.parametrize("corrupt_parent_reference", [False, True])
def test_distant_replay_checks_historical_receipt_parent_pair(
    equal_times: bool, corrupt_parent_reference: bool
) -> None:
    history = [fresh_version(1020)]
    for i in range(1, 6):
        history.append(append_version(history[-1], 1020 if equal_times else 1020 + i * 5))
    receipt, latest = history[2], history[-1]
    if corrupt_parent_reference:
        data = receipt.model_dump(mode="json")
        data["parent"]["view"]["parent_version_id"] = receipt.version.view.version_id
        receipt = WorldVersionCommit.model_validate_json(json.dumps(data))
        with pytest.raises(ContractViolation, match="recovery_required"):
            replay_version(receipt, latest)
    else:
        assert replay_version(receipt, latest) == receipt.result
