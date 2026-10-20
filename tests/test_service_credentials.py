"""C1 current-authority, atomic lifecycle, loss/retry and recovery regressions."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.service_contracts import (
    ServiceCreateRequest,
    ServiceCredentialPolicy,
    ServiceKeyIssuedResponse,
    ServiceKeyIssueRequest,
    ServiceKeyMaterial,
    ServiceKeyRecoverRequest,
    ServiceKeyRevokeRequest,
    ServiceKeyRotateRequest,
    ServiceKeySet,
    ServiceManager,
    ServiceMutationResponse,
    ServicePlan,
    ServiceReceiptLookup,
    ServiceStateRequest,
)
from strange_physics.service_credentials import (
    ServiceRequest,
    get_service_key,
    get_service_principal,
    plan_service_operation,
    service_error,
    service_key_valid,
    validate_initial_key_response,
)
from strange_physics.session_contracts import DeploymentSessionPolicy
from strange_physics.workspace_contracts import WorkspaceAuthority

ROOT = Path(__file__).resolve().parents[1]
type Context = tuple[
    DeploymentSessionPolicy, ServiceCredentialPolicy, ServiceManager, WorkspaceAuthority
]


def data(filename: str, name: str) -> Any:
    return json.loads((ROOT / "contracts" / filename).read_text())["valid"][name]


def changed[T: Message](value: T, **fields: object) -> T:
    return type(value).model_validate(value.model_dump() | fields)


def context(now: int = 1100) -> Context:
    session = DeploymentSessionPolicy.model_validate_json(
        json.dumps(data("session.examples.json", "DeploymentSessionPolicy"))
    )
    policy = ServiceCredentialPolicy.model_validate_json(
        json.dumps(data("service.examples.json", "ServiceCredentialPolicy"))
    )
    manager = ServiceManager.model_validate_json(
        json.dumps(data("service.examples.json", "ServiceManager"))
    )
    actor = changed(
        manager.actor,
        session=changed(
            manager.actor.session,
            authenticated_at=now - 10,
            created_at=now,
            absolute_expires_at=now + session.absolute_seconds,
            last_seen_at=now,
        ),
    )
    manager = changed(manager, actor=actor)
    workspace = WorkspaceAuthority.model_validate_json(
        json.dumps(data("workspace.examples.json", "WorkspaceAuthority"))
    )
    workspace = changed(
        workspace, workspace=changed(workspace.workspace, workspace_id="workspace-1")
    )
    return session, policy, manager, workspace


def empty() -> ServiceKeySet:
    original = ServiceKeySet.model_validate_json(
        json.dumps(data("service.examples.json", "ServiceKeySet"))
    )
    return changed(
        original,
        principal=changed(original.principal, revision=0, last_key_generation=0),
        records=(),
    )


def material(index: int) -> ServiceKeyMaterial:
    return ServiceKeyMaterial(
        credential_id=f"key-{index}",
        verifier_sha256=hashlib.sha256(bytes([index]) * 32).hexdigest(),
    )


def lookup(plan: ServicePlan) -> ServiceReceiptLookup:
    return ServiceReceiptLookup(state="committed", receipt=plan.receipt, audit=plan.audit)


def call(
    current: ServiceKeySet | None,
    request: ServiceRequest,
    *,
    now: int = 1100,
    target: str | None = None,
    supplied_material: ServiceKeyMaterial | None = None,
    stored: ServiceReceiptLookup | None = None,
    ctx: Context | None = None,
    key: str = "request-1",
) -> ServicePlan | ServiceMutationResponse:
    session, policy, manager, workspace = context(now) if ctx is None else ctx
    create = isinstance(request, ServiceCreateRequest)
    return plan_service_operation(
        session,
        policy,
        manager,
        workspace,
        request,
        current,
        ServiceReceiptLookup(state="absent", receipt=None, audit=None)
        if stored is None
        else stored,
        workspace_id=workspace.workspace.workspace_id,
        principal_id=None if create else "service-1",
        credential_id=target,
        key=key,
        now=now,
        audit_event_id=f"audit-{now}-{request.__class__.__name__}",
        new_principal_id="service-1" if create else None,
        material=supplied_material,
    )


def plan(current: ServiceKeySet | None, request: ServiceRequest, **kwargs: Any) -> ServicePlan:
    result = call(current, request, **kwargs)
    assert isinstance(result, ServicePlan)
    return result


def issue(*, expires_at: int = 2000) -> tuple[ServiceKeyIssueRequest, ServicePlan]:
    request = ServiceKeyIssueRequest(
        expected_revision=0,
        scopes=("runs:read",),
        expires_at=expires_at,
    )
    return request, plan(empty(), request, supplied_material=material(1))


def rotate() -> tuple[ServiceKeyRotateRequest, ServicePlan]:
    _, first = issue()
    request = ServiceKeyRotateRequest(
        expected_revision=1,
        scopes=("runs:read",),
        expires_at=2200,
        overlap_seconds=60,
    )
    return request, plan(
        first.key_set,
        request,
        target="key-1",
        supplied_material=material(2),
        now=1110,
    )


def assert_denied(code: str, status: int, function: Any, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(ContractViolation) as captured:
        function(*args, **kwargs)
    assert (captured.value.code, captured.value.status) == (code, status)


def test_create_allocates_independent_non_owner_grant_without_key() -> None:
    ctx = context()
    request = ServiceCreateRequest(
        expected_workspace_revision=ctx[3].workspace.revision,
        display_name="Investigator",
        role="researcher",
        scope_ceiling=("runs:cancel", "runs:create", "runs:read"),
    )
    result = plan(None, request, ctx=ctx)
    assert result.key_set.records == ()
    assert result.key_set.principal.grant.membership.role == "researcher"
    assert result.key_set.principal.last_key_generation == 0
    assert result.workspace.workspace.revision == ctx[3].workspace.revision + 1
    assert result.workspace.active_owner_ids == ctx[3].active_owner_ids
    replay = call(result.key_set, request, ctx=ctx, stored=lookup(result))
    assert isinstance(replay, ServiceMutationResponse)
    assert replay.disposition == "replayed"
    assert replay.principal == result.key_set.principal


def test_initial_secret_binds_private_digest_and_never_enters_durable_output() -> None:
    _, result = issue()
    verifier = base64.urlsafe_b64encode(bytes([1]) * 32).decode().rstrip("=")
    token = "spk1.key-1." + verifier
    response = ServiceKeyIssuedResponse(delivery="issued", result=result.response, secret=token)
    validate_initial_key_response(result, response)
    assert token not in result.model_dump_json()
    for safe in (result.receipt, result.audit, result.response):
        assert verifier not in safe.model_dump_json()
        assert material(1).verifier_sha256 not in safe.model_dump_json()
    assert token not in repr(response)
    assert material(1).verifier_sha256 not in repr(result.key_set.records[0])
    wrong = changed(response, secret="spk1.key-1." + "A" * 43)
    assert_denied("recovery_required", 409, validate_initial_key_response, result, wrong)


def test_exact_issuance_retry_is_metadata_only_before_original_cas() -> None:
    request, result = issue()
    replay = call(
        result.key_set,
        request,
        stored=lookup(result),
        supplied_material=material(9),
        now=1110,
    )
    assert isinstance(replay, ServiceMutationResponse)
    assert replay.disposition == "replayed"
    assert replay.outcome == result.receipt.outcome
    assert replay.credential is not None and replay.credential.valid_now
    assert "secret" not in replay.model_dump_json()
    assert replay.principal.last_key_generation == 1
    assert result.key_set.records[0].key.credential_id == "key-1"


def test_changed_request_conflicts_and_fresh_stale_cas_does_not_issue() -> None:
    request, result = issue()
    assert_denied(
        "idempotency_conflict",
        409,
        call,
        result.key_set,
        changed(request, expires_at=2001),
        stored=lookup(result),
    )
    assert_denied(
        "incompatible_state",
        409,
        call,
        result.key_set,
        request,
        supplied_material=material(2),
    )


def test_retry_reports_current_expired_key_and_original_committed_revision() -> None:
    request, initial = issue(expires_at=1150)
    next_key = plan(
        initial.key_set,
        ServiceKeyIssueRequest(expected_revision=1, scopes=("runs:read",), expires_at=2200),
        supplied_material=material(2),
        now=1150,
        key="issue-again",
    )
    replay = call(next_key.key_set, request, stored=lookup(initial), now=1160)
    assert isinstance(replay, ServiceMutationResponse)
    assert replay.outcome.committed_revision == 1 and replay.principal.revision == 2
    assert replay.credential is not None and not replay.credential.valid_now
    assert replay.credential.principal_revision == 2


def test_rotation_caps_overlap_and_cannot_extend_it_on_retry() -> None:
    request, result = rotate()
    assert result.key_set.records[0].key.retire_at == 1170
    assert (
        sum(
            service_key_valid(result.key_set.principal, r.key, now=1110)
            for r in result.key_set.records
        )
        == 2
    )
    replay = call(
        result.key_set,
        request,
        stored=lookup(result),
        target="key-1",
        now=1140,
        supplied_material=material(3),
    )
    assert isinstance(replay, ServiceMutationResponse)
    assert result.key_set.records[0].key.retire_at == 1170
    assert not service_key_valid(result.key_set.principal, result.key_set.records[0].key, now=1170)
    assert_denied(
        "incompatible_state",
        409,
        call,
        result.key_set,
        changed(request, expected_revision=2),
        target="key-2",
        supplied_material=material(3),
        now=1140,
    )


@pytest.mark.parametrize("target", ("key-1", "key-2"))
def test_recovery_of_either_overlap_side_preserves_effective_deadline_and_other_key(
    target: str,
) -> None:
    _, before = rotate()
    old = next(record for record in before.key_set.records if record.key.credential_id == target)
    other = next(record for record in before.key_set.records if record.key.credential_id != target)
    request = ServiceKeyRecoverRequest(expected_revision=2)
    result = plan(
        before.key_set,
        request,
        target=target,
        supplied_material=material(3),
        now=1120,
    )
    replacement = next(
        record for record in result.key_set.records if record.key.credential_id == "key-3"
    )
    revoked = next(
        record for record in result.key_set.records if record.key.credential_id == target
    )
    assert replacement.key.scopes == old.key.scopes
    assert replacement.key.expires_at == old.key.expires_at
    assert replacement.key.retire_at == old.key.retire_at
    assert replacement.key.key_generation == 3
    assert revoked.key.revoked_at == 1120
    assert (
        next(
            record
            for record in result.key_set.records
            if record.key.credential_id == other.key.credential_id
        )
        == other
    )
    assert (
        sum(
            service_key_valid(result.key_set.principal, r.key, now=1120)
            for r in result.key_set.records
        )
        == 2
    )
    replay = call(result.key_set, request, target=target, stored=lookup(result), now=1130)
    assert isinstance(replay, ServiceMutationResponse)
    assert replay.outcome == result.receipt.outcome
    assert_denied(
        "incompatible_state",
        409,
        call,
        result.key_set,
        ServiceKeyRecoverRequest(expected_revision=3),
        target=target,
        supplied_material=material(4),
        now=1130,
        key="fresh-recovery",
    )


@pytest.mark.parametrize("now", (1149, 1150))
def test_near_expiry_recovery_does_not_extend_authority(now: int) -> None:
    _, initial = issue(expires_at=1150)
    request = ServiceKeyRecoverRequest(expected_revision=1)
    if now == 1150:
        assert_denied(
            "incompatible_state",
            409,
            call,
            initial.key_set,
            request,
            target="key-1",
            supplied_material=material(2),
            now=now,
        )
    else:
        result = plan(
            initial.key_set,
            request,
            target="key-1",
            supplied_material=material(2),
            now=now,
        )
        assert result.key_set.records[1].key.expires_at == 1150
        assert not service_key_valid(
            result.key_set.principal, result.key_set.records[1].key, now=1150
        )


def test_disable_reenable_and_remove_regrant_never_revive_old_key_or_reset_counter() -> None:
    request, initial = issue()
    disabled = plan(
        initial.key_set, ServiceStateRequest(expected_revision=1, active=False), now=1110
    )
    enabled = plan(
        disabled.key_set, ServiceStateRequest(expected_revision=2, active=True), now=1120
    )
    assert enabled.key_set.principal.authority_generation == 2
    assert enabled.key_set.principal.last_key_generation == 1
    assert not service_key_valid(
        enabled.key_set.principal, enabled.key_set.records[0].key, now=1120
    )
    assert_denied(
        "forbidden", 403, call, enabled.key_set, request, stored=lookup(initial), now=1120
    )
    new = plan(
        enabled.key_set,
        ServiceKeyIssueRequest(expected_revision=3, scopes=("runs:read",), expires_at=2200),
        supplied_material=material(2),
        now=1130,
    )
    assert new.key_set.records[1].key.key_generation == 2
    regranted = changed(
        new.key_set.principal,
        grant=changed(new.key_set.principal.grant, incarnation=1),
    )
    assert not service_key_valid(regranted, new.key_set.records[1].key, now=1140)
    assert_denied(
        "forbidden",
        403,
        call,
        changed(new.key_set, principal=regranted),
        ServiceKeyIssueRequest(expected_revision=3, scopes=("runs:read",), expires_at=2200),
        stored=lookup(new),
        now=1140,
    )


@pytest.mark.parametrize(
    "case", ("human_generation", "human_disabled", "grant_removed", "grant_regranted", "workspace")
)
def test_current_authority_precedes_retry_and_generation_change_denies_old_receipt(
    case: str,
) -> None:
    request, initial = issue()
    session, policy, manager, workspace = context(1400)
    stale_actor = changed(
        manager.actor, session=changed(manager.actor.session, authenticated_at=990)
    )
    manager = changed(manager, actor=stale_actor)
    expected = ("forbidden", 403)
    if case == "human_generation":
        manager = changed(
            manager,
            owner=changed(
                manager.owner,
                principal=changed(manager.owner.principal, generation=1),
            ),
        )
        expected = ("unauthenticated", 401)
    elif case == "human_disabled":
        manager = changed(
            manager,
            owner=changed(
                manager.owner,
                principal=changed(manager.owner.principal, active=False),
            ),
        )
        expected = ("unauthenticated", 401)
    elif case == "grant_removed":
        manager = changed(
            manager,
            owner=changed(
                manager.owner,
                grant=changed(
                    manager.owner.grant,
                    membership=changed(manager.owner.grant.membership, active=False),
                ),
            ),
        )
    elif case == "grant_regranted":
        manager = context(1400)[2]
        manager = changed(
            manager,
            owner=changed(
                manager.owner,
                grant=changed(manager.owner.grant, incarnation=1),
            ),
        )
    else:
        workspace = changed(workspace, workspace=changed(workspace.workspace, state="quarantined"))
    assert_denied(
        *expected,
        call,
        initial.key_set,
        request,
        now=1400,
        stored=lookup(initial),
        ctx=(session, policy, manager, workspace),
    )


@pytest.mark.parametrize("case", ("csrf", "origin", "mixed", "no_cookie", "stale"))
def test_browser_and_recent_actual_authentication_are_required_for_mutations(case: str) -> None:
    request, initial = issue()
    session, policy, manager, workspace = context()
    expected = ("forbidden", 403)
    browser = manager.actor.context
    if case == "csrf":
        browser = changed(browser, csrf_matches=False)
    elif case == "origin":
        browser = changed(browser, origin="https://other.example")
    elif case == "mixed":
        browser = changed(browser, has_bearer=True)
        expected = ("ambiguous_credentials", 400)
    elif case == "no_cookie":
        browser = changed(browser, has_session_cookie=False)
        expected = ("unauthenticated", 401)
    else:
        manager = changed(
            manager,
            actor=changed(
                manager.actor,
                session=changed(manager.actor.session, authenticated_at=700),
            ),
        )
        expected = ("reauthentication_required", 401)
    manager = changed(manager, actor=changed(manager.actor, context=browser))
    assert_denied(
        *expected,
        call,
        initial.key_set,
        request,
        stored=lookup(initial),
        ctx=(session, policy, manager, workspace),
    )


@pytest.mark.parametrize(
    "case",
    (
        "receipt_missing",
        "audit_missing",
        "recovery",
        "audit_id",
        "audit_digest",
        "key_missing",
        "key_mutated",
        "snapshot_missing",
        "revision_rollback",
    ),
)
def test_partial_or_changed_atomic_evidence_cannot_replay_or_issue(case: str) -> None:
    request, initial = issue()
    stored, current = lookup(initial), initial.key_set
    if case == "receipt_missing":
        stored = changed(stored, receipt=None)
    elif case == "audit_missing":
        stored = changed(stored, audit=None)
    elif case == "recovery":
        stored = ServiceReceiptLookup(state="recovery_required", receipt=None, audit=None)
    elif case == "audit_id":
        stored = changed(stored, audit=changed(initial.audit, event_id="different"))
    elif case == "audit_digest":
        stored = changed(stored, audit=changed(initial.audit, snapshot_sha256="0" * 64))
    elif case == "key_missing":
        current = changed(current, records=())
    elif case == "key_mutated":
        record = changed(current.records[0], key=changed(current.records[0].key, expires_at=2100))
        current = changed(current, records=(record,))
    elif case == "snapshot_missing":
        receipt = changed(initial.receipt, snapshot=changed(initial.receipt.snapshot, keys=()))
        stored = changed(stored, receipt=receipt)
    else:
        current = changed(current, principal=changed(current.principal, revision=0))
    assert_denied(
        "recovery_required",
        409,
        call,
        current,
        request,
        stored=stored,
        supplied_material=material(9),
    )


@pytest.mark.parametrize("operation", ("issue", "recover", "revoke", "state"))
def test_shared_revision_serializes_independent_key_and_state_changes(operation: str) -> None:
    _, initial = issue()
    current = initial.key_set
    if operation == "issue":
        request: ServiceRequest = ServiceKeyIssueRequest(
            expected_revision=0, scopes=("runs:read",), expires_at=2200
        )
        target = None
    elif operation == "recover":
        request = ServiceKeyRecoverRequest(expected_revision=0)
        target = "key-1"
    elif operation == "revoke":
        request = ServiceKeyRevokeRequest(expected_revision=0)
        target = "key-1"
    else:
        request = ServiceStateRequest(expected_revision=0, active=False)
        target = None
    assert_denied(
        "incompatible_state",
        409,
        call,
        current,
        request,
        target=target,
        supplied_material=material(2),
    )


def test_revocation_replay_and_fresh_issuance_do_not_reset_generation() -> None:
    _, initial = issue()
    request = ServiceKeyRevokeRequest(expected_revision=1)
    revoked = plan(initial.key_set, request, target="key-1", now=1110)
    assert not revoked.response.credential.valid_now if revoked.response.credential else False
    replay = call(revoked.key_set, request, target="key-1", stored=lookup(revoked), now=1120)
    assert isinstance(replay, ServiceMutationResponse)
    new = plan(
        revoked.key_set,
        ServiceKeyIssueRequest(expected_revision=2, scopes=("runs:read",), expires_at=2200),
        supplied_material=material(2),
        now=1130,
    )
    assert new.key_set.principal.last_key_generation == 2
    assert new.key_set.records[0].key.revoked_at == 1110


@pytest.mark.parametrize(
    "case", ("reuse_id", "reuse_verifier", "no_material", "scope", "expiry", "ttl", "key_limit")
)
def test_fresh_key_admission_rejects_invalid_material_limits_and_authority(case: str) -> None:
    _, initial = issue()
    revoked = plan(initial.key_set, ServiceKeyRevokeRequest(expected_revision=1), target="key-1")
    current = revoked.key_set
    request = ServiceKeyIssueRequest(expected_revision=2, scopes=("runs:read",), expires_at=2200)
    supplied: ServiceKeyMaterial | None = material(2)
    expected = ("incompatible_state", 409)
    ctx = context()
    if case == "reuse_id":
        supplied = changed(material(2), credential_id="key-1")
    elif case == "reuse_verifier":
        supplied = changed(material(2), verifier_sha256=material(1).verifier_sha256)
    elif case == "no_material":
        supplied = None
        expected = ("recovery_required", 409)
    elif case == "scope":
        current = changed(
            current,
            principal=changed(
                current.principal,
                scope_ceiling=("runs:read",),
            ),
        )
        request = changed(request, scopes=("runs:create",))
        expected = ("invalid_request", 422)
    elif case == "expiry":
        request = changed(request, expires_at=1100)
        expected = ("invalid_request", 422)
    elif case == "ttl":
        request = changed(request, expires_at=9999)
        expected = ("invalid_request", 422)
    else:
        second = plan(current, request, supplied_material=material(2))
        second_revoked = plan(
            second.key_set, ServiceKeyRevokeRequest(expected_revision=3), target="key-2"
        )
        current = second_revoked.key_set
        request = changed(request, expected_revision=4)
        supplied = material(3)
        ctx = (ctx[0], changed(ctx[1], max_key_records=2), ctx[2], ctx[3])
        expected = ("quota_exceeded", 429)
    assert_denied(*expected, call, current, request, supplied_material=supplied, ctx=ctx)


def test_safe_key_metadata_exposes_current_shared_revision_after_authorized_lookup() -> None:
    _, initial = issue()
    session, policy, manager, workspace = context()
    value = get_service_key(
        session,
        policy,
        manager,
        workspace,
        initial.key_set,
        workspace_id="workspace-1",
        principal_id="service-1",
        credential_id="key-1",
        now=1100,
    )
    assert value.principal_revision == 1 and value.valid_now
    assert material(1).verifier_sha256 not in value.model_dump_json()
    assert_denied(
        "not_found",
        404,
        get_service_principal,
        session,
        policy,
        manager,
        workspace,
        initial.key_set,
        workspace_id="workspace-1",
        principal_id="other",
        now=1100,
    )


@pytest.mark.parametrize(
    "code,status",
    (
        ("invalid_request", 422),
        ("policy_unavailable", 503),
        ("unauthenticated", 401),
        ("forbidden", 403),
        ("ambiguous_credentials", 400),
        ("reauthentication_required", 401),
        ("not_found", 404),
        ("idempotency_conflict", 409),
        ("incompatible_state", 409),
        ("recovery_required", 409),
        ("quota_exceeded", 429),
        ("temporarily_unavailable", 503),
        ("rate_limited", 429),
    ),
)
def test_fixed_error_mapping_and_public_header_contract(code: str, status: int) -> None:
    actual, body, headers = service_error(
        ContractViolation(code, status),
        request_id="request-1",
        retry_after=30 if status == 429 else None,
    )
    assert actual == status and body.code == code
    assert headers["Cache-Control"] == "no-store"
    assert ("X-Authentication-Action" in headers) == (code == "reauthentication_required")
    assert ("Retry-After" in headers) == (status == 429)
    assert set(body.model_dump()) == {"code", "request_id"}


@pytest.mark.parametrize("bad", (None, 0, -1, True, 86401))
def test_rate_error_requires_bounded_retry_after(bad: int | None) -> None:
    with pytest.raises(ValueError):
        service_error(ContractViolation("rate_limited", 429), request_id="r", retry_after=bad)


@pytest.mark.parametrize("field", ("generation", "incarnation"))
def test_authority_producer_transitions_require_monotonic_fences(field: str) -> None:
    from strange_physics.credential_authority import validate_grant_update, validate_principal_state

    manager = context()[2]
    if field == "generation":
        before = manager.owner.principal
        disabled = changed(before, active=False, generation=1)
        validate_principal_state(before, disabled)
        enabled = changed(disabled, active=True, generation=2)
        validate_principal_state(disabled, enabled)
        assert_denied(
            "incompatible_state",
            409,
            validate_principal_state,
            disabled,
            changed(enabled, generation=1),
        )
    else:
        before_grant = manager.owner.grant
        removed = changed(
            before_grant,
            membership=changed(before_grant.membership, active=False, revision=1),
            incarnation=1,
        )
        validate_grant_update(before_grant, removed)
        regranted = changed(
            removed, membership=changed(removed.membership, active=True, revision=2), incarnation=2
        )
        validate_grant_update(removed, regranted)
        assert_denied(
            "incompatible_state",
            409,
            validate_grant_update,
            removed,
            changed(regranted, incarnation=1),
        )
        # Current role semantics remain per-operation; a role change is not a fake removal.
        downgraded = changed(
            before_grant, membership=changed(before_grant.membership, role="viewer", revision=1)
        )
        validate_grant_update(before_grant, downgraded)


def test_zero_time_retirement_is_expired_and_not_replaced_by_expiry() -> None:
    _, initial = issue()
    record = initial.key_set.records[0]
    key_state = changed(record.key, created_at=0, retire_at=0)
    assert not service_key_valid(initial.key_set.principal, key_state, now=0)


@pytest.mark.parametrize("change", ("shorten", "extend"))
def test_receipt_retention_cannot_be_changed_after_commit(change: str) -> None:
    request, initial = issue()
    delta = -1 if change == "shorten" else 1
    stored = changed(
        lookup(initial),
        receipt=changed(initial.receipt, retain_until=initial.receipt.retain_until + delta),
    )
    assert_denied("recovery_required", 409, call, initial.key_set, request, stored=stored)


def test_key_generation_exhaustion_fails_without_reset_or_issuance() -> None:
    before = empty()
    before = changed(before, principal=changed(before.principal, last_key_generation=2**53 - 1))
    request = ServiceKeyIssueRequest(expected_revision=0, scopes=("runs:read",), expires_at=2000)
    assert_denied("incompatible_state", 409, call, before, request, supplied_material=material(1))


def test_short_original_expiry_caps_rotation_retirement() -> None:
    _, initial = issue(expires_at=1130)
    result = plan(
        initial.key_set,
        ServiceKeyRotateRequest(
            expected_revision=1, scopes=("runs:read",), expires_at=2200, overlap_seconds=60
        ),
        target="key-1",
        supplied_material=material(2),
        now=1110,
    )
    assert result.key_set.records[0].key.retire_at == 1130
