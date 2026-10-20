from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import run_credential_contracts as c
from strange_physics.contracts import Message
from strange_physics.control_contracts import (
    ContractViolation,
    CreateRunRequest,
    IdempotencyScope,
    Membership,
    RunView,
    StoredRequest,
    VerifiedCredential,
)
from strange_physics.product_authority import admit_run_ownership
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credentials import change_run_credential
from strange_physics.workspace_contracts import (
    WorkspaceAuthority,
    WorkspaceView,
    authorize_product,
    check_product_idempotency,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/run-credentials.examples.json").read_text())["valid"]
CONTROL = json.loads((ROOT / "contracts/control.examples.json").read_text())["valid"]


def value[T: Message](model: type[T]) -> T:
    return model.model_validate_json(
        json.dumps(copy.deepcopy((CONTROL | FIXTURES)[model.__name__]))
    )


def changed[T: Message](model: T, **changes: Any) -> T:
    return type(model).model_validate(model.model_dump() | changes)


def workspace(member: Membership) -> WorkspaceAuthority:
    return WorkspaceAuthority(
        workspace=WorkspaceView(
            workspace_id=member.workspace_id,
            display_name="Synthetic",
            visibility="private",
            state="active",
            revision=2,
        ),
        active_owner_ids=(member.principal_id,) if member.role == "owner" else ("other-owner",),
        disabled_owner_ids=(),
    )


def args(operation: str = "replace", **changes: Any) -> dict[str, Any]:
    current = value(c.RunAuthorityState)
    if operation == "issue":
        current = changed(
            current,
            credentials=changed(
                current.credentials,
                records=(),
                revision=0,
                last_generation=0,
                current_credential_id=None,
            ),
        )
        request: c.RunCredentialIssueRequest = c.RunCredentialIssueRequest(
            expected_run_revision=4, expected_credential_revision=0
        )
    elif operation == "replace":
        request = c.RunCredentialReplaceRequest(
            expected_run_revision=4, expected_credential_revision=1, credential_id="worker-key-1"
        )
    else:
        request = c.RunCredentialRevokeRequest(
            expected_run_revision=4, expected_credential_revision=1, credential_id="worker-key-1"
        )
    return (
        dict(
            policy=value(c.RunCredentialPolicy),
            coordinator=value(c.RunCoordinatorAuthority),
            current=current,
            workspace=workspace(current.owner.grant.membership),
            operation=operation,
            request=request,
            key="request-1",
            lookup=c.RunCredentialLookup(state="absent", receipt=None, audit=None),
            now=1200,
            new_credential_id="worker-key-2",
            audit_event_id="audit-2",
        )
        | changes
    )


def plan(**kw: Any) -> c.RunCredentialPlan:
    result = change_run_credential(**kw)
    assert isinstance(result, c.RunCredentialPlan)
    return result


def replay_args(original: dict[str, Any], committed: c.RunCredentialPlan) -> dict[str, Any]:
    return original | dict(
        current=changed(original["current"], credentials=committed.credentials),
        lookup=c.RunCredentialLookup(
            state="committed", receipt=committed.receipt, audit=committed.audit
        ),
        now=original["now"] + 1,
        new_credential_id=None,
        audit_event_id=None,
    )


def denied(code: str, status: int = 403) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda e: e.status == status)


def credential(authority: c.ProductAuthority) -> VerifiedCredential:
    if authority.kind == "run":
        claims = authority.verified_claims
        return VerifiedCredential(
            issuer=claims.issuer,
            subject=claims.principal_id,
            principal_id=claims.principal_id,
            credential_id=claims.credential_id,
            kind="run",
            workspace_id=claims.workspace_id,
            scopes=claims.scopes,
            expires_at=claims.expires_at,
            revoked=False,
            run_id=claims.run_id,
            attempt_id=claims.attempt_id,
            lease_epoch=claims.lease_epoch,
        )
    if authority.kind == "user":
        session = authority.actor.session
        return changed(
            value(VerifiedCredential),
            principal_id=session.principal_id,
            credential_id=session.session_id,
            workspace_id=authority.owner.grant.membership.workspace_id,
            expires_at=session.absolute_expires_at,
            revoked=session.revoked,
        )
    key = next(
        r.key for r in authority.current.records if r.key.credential_id == authority.credential_id
    )
    return changed(
        value(VerifiedCredential),
        kind="service",
        principal_id=key.principal_id,
        credential_id=key.credential_id,
        workspace_id=key.workspace_id,
        scopes=key.scopes,
        expires_at=key.expires_at,
        revoked=key.revoked_at is not None,
    )


def product(
    authority: c.ProductAuthority, permission: str = "experiments:read", **changes: Any
) -> dict[str, Any]:
    if authority.kind == "service":
        member = authority.current.principal.grant.membership
    elif authority.kind == "user":
        member = authority.owner.grant.membership
    else:
        member = authority.current.owner.grant.membership
    return (
        dict(
            workspace=workspace(member),
            credential=credential(authority),
            membership=member,
            authority=authority,
            permission=permission,
            workspace_id=member.workspace_id,
            now=1200,
            run_id=authority.current.run.run_id if authority.kind == "run" else None,
            lease=authority.current.lease if authority.kind == "run" else None,
        )
        | changes
    )


@pytest.mark.parametrize("operation", ["issue", "replace", "revoke"])
def test_atomic_operations_and_metadata_only_replay(operation: str) -> None:
    original = args(operation)
    committed = plan(**original)
    assert committed.credentials.revision == original["current"].credentials.revision + 1
    assert committed.audit.snapshot_sha256 == message_sha256(committed.receipt.snapshot)
    assert all(
        r.retain_until >= committed.receipt.retain_until for r in committed.receipt.snapshot.records
    )
    assert (committed.issue_claims is not None) == (operation != "revoke")
    response = change_run_credential(**replay_args(original, committed))
    assert isinstance(response, c.RunCredentialResponse)
    assert response.disposition == "replayed"
    assert not hasattr(response, "issue_claims")
    assert response.outcome == committed.response.outcome


@pytest.mark.parametrize(
    "ttl,lease_expiry,expected", [(30, 1500, 1230), (300, 1300, 1300), (1000, 2500, 2000)]
)
def test_issuance_lifetime_is_policy_lease_and_original_deadline_bounded(
    ttl: int, lease_expiry: int, expected: int
) -> None:
    original = args("issue")
    original["policy"] = changed(original["policy"], max_ttl_seconds=ttl)
    original["current"] = changed(
        original["current"], lease=changed(original["current"].lease, expires_at=lease_expiry)
    )
    committed = plan(**original)
    assert committed.issue_claims is not None
    assert committed.issue_claims.expires_at == expected


def test_replacement_fences_old_worker_immediately_and_retains_common_evidence() -> None:
    original = args()
    committed = plan(**original)
    current = changed(original["current"], credentials=committed.credentials)
    previous = value(c.RunProductAuthority)
    old = changed(previous, current=current)
    with denied("unauthenticated", 401):
        authorize_product(**product(old, "checkpoints:write"))
    assert committed.issue_claims is not None
    new = changed(old, verified_claims=committed.issue_claims)
    authorize_product(**product(new, "checkpoints:write"))
    assert committed.credentials.last_generation == 2
    assert committed.credentials.ownership == original["current"].credentials.ownership
    assert committed.credentials.records[0].revoked_at == 1200
    assert {r.retain_until for r in committed.receipt.snapshot.records} == {2100}


def test_old_receipt_replays_metadata_after_replacement_but_cannot_remint() -> None:
    first_args = args("issue")
    first = plan(**first_args)
    second_args = args(
        "replace",
        current=changed(first_args["current"], credentials=first.credentials),
        request=c.RunCredentialReplaceRequest(
            expected_run_revision=4, expected_credential_revision=1, credential_id="worker-key-2"
        ),
        new_credential_id="worker-key-3",
        now=1250,
    )
    second = plan(**second_args)
    retry = replay_args(first_args, first)
    retry["current"] = changed(retry["current"], credentials=second.credentials)
    retry["now"] = 1251
    response = change_run_credential(**retry)
    assert isinstance(response, c.RunCredentialResponse)
    assert not response.credential.valid_now
    assert response.credential.current_credential_id == "worker-key-3"
    assert response.outcome.credential_id == "worker-key-2"


def test_new_attempt_replacement_keeps_original_owner_and_deadline() -> None:
    original = args()
    original["current"] = changed(
        original["current"],
        lease=changed(original["current"].lease, attempt_id="attempt-2", epoch=4),
    )
    committed = plan(**original)
    assert committed.issue_claims is not None
    assert (committed.issue_claims.attempt_id, committed.issue_claims.lease_epoch) == (
        "attempt-2",
        4,
    )
    assert committed.credentials.ownership == original["current"].credentials.ownership
    old = value(c.RunProductAuthority)
    with denied("unauthenticated", 401):
        authorize_product(**product(changed(old, current=original["current"])))
    retry = replay_args(original, committed)
    retry["current"] = changed(
        retry["current"], lease=changed(retry["current"].lease, attempt_id="attempt-3", epoch=5)
    )
    with denied("forbidden"):
        change_run_credential(**retry)


@pytest.mark.parametrize("field", ["receipt", "audit"])
def test_missing_atomic_receipt_evidence_is_recovery_required(field: str) -> None:
    original = args()
    committed = plan(**original)
    retry = replay_args(original, committed)
    retry["lookup"] = changed(retry["lookup"], **{field: None})
    with denied("recovery_required", 409):
        change_run_credential(**retry)


@pytest.mark.parametrize("mutation", ["event", "snapshot", "request", "actor"])
def test_audit_must_exactly_match_original_atomic_receipt(mutation: str) -> None:
    original = args()
    committed = plan(**original)
    retry = replay_args(original, committed)
    changes = {
        "event": {"event_id": "foreign"},
        "snapshot": {"snapshot_sha256": "f" * 64},
        "request": {"request_sha256": "e" * 64},
        "actor": {"actor_id": "foreign"},
    }
    retry["lookup"] = changed(retry["lookup"], audit=changed(committed.audit, **changes[mutation]))
    with denied("recovery_required", 409):
        change_run_credential(**retry)


@pytest.mark.parametrize("field", ["revoked_at", "retain_until"])
def test_equal_revision_requires_exact_affected_records_and_later_allows_monotonic(
    field: str,
) -> None:
    original = args("issue")
    committed = plan(**original)
    retry = replay_args(original, committed)
    record = committed.credentials.records[0]
    changed_record = changed(
        record, **{field: 1201 if field == "revoked_at" else record.retain_until + 1}
    )
    state = changed(
        committed.credentials,
        records=(changed_record,),
        current_credential_id=None if field == "revoked_at" else record.claims.credential_id,
    )
    retry["current"] = changed(retry["current"], credentials=state)
    with denied("recovery_required", 409):
        change_run_credential(**retry)
    retry["current"] = changed(
        retry["current"], credentials=changed(state, revision=state.revision + 1)
    )
    assert isinstance(change_run_credential(**retry), c.RunCredentialResponse)


@pytest.mark.parametrize(
    "mutation,code,status",
    [
        ("coordinator_revoked", "unauthenticated", 401),
        ("coordinator_expired", "unauthenticated", 401),
        ("coordinator_foreign", "not_found", 404),
        ("disabled", "forbidden", 403),
        ("generation", "forbidden", 403),
        ("incarnation", "forbidden", 403),
        ("grant_removed", "forbidden", 403),
        ("lease_revoked", "forbidden", 403),
        ("lease_expired", "forbidden", 403),
        ("deadline_changed", "forbidden", 403),
        ("status", "incompatible_state", 409),
        ("quarantine", "forbidden", 403),
    ],
)
def test_current_authority_precedes_bad_cached_receipt(
    mutation: str, code: str, status: int
) -> None:
    original = args()
    committed = plan(**original)
    retry = replay_args(original, committed)
    retry["lookup"] = changed(retry["lookup"], audit=None)
    current = retry["current"]
    owner = current.owner
    coord = retry["coordinator"]
    if mutation == "coordinator_revoked":
        retry["coordinator"] = changed(coord, revoked=True)
    elif mutation == "coordinator_expired":
        retry["coordinator"] = changed(coord, expires_at=1201)
    elif mutation == "coordinator_foreign":
        retry["coordinator"] = changed(coord, run_id="foreign")
    elif mutation == "disabled":
        current = changed(
            current, owner=changed(owner, principal=changed(owner.principal, active=False))
        )
    elif mutation == "generation":
        current = changed(
            current, owner=changed(owner, principal=changed(owner.principal, generation=1))
        )
    elif mutation == "incarnation":
        current = changed(current, owner=changed(owner, grant=changed(owner.grant, incarnation=1)))
    elif mutation == "grant_removed":
        current = changed(
            current,
            owner=changed(
                owner,
                grant=changed(
                    owner.grant, membership=changed(owner.grant.membership, active=False)
                ),
            ),
        )
    elif mutation == "lease_revoked":
        current = changed(current, lease=changed(current.lease, revoked=True))
    elif mutation == "lease_expired":
        current = changed(current, lease=changed(current.lease, expires_at=1201))
    elif mutation == "deadline_changed":
        current = changed(current, lease=changed(current.lease, run_deadline=2001))
    elif mutation == "status":
        current = changed(current, run=changed(current.run, status="cancelled"))
    elif mutation == "quarantine":
        retry["workspace"] = changed(
            retry["workspace"], workspace=changed(retry["workspace"].workspace, state="quarantined")
        )
    retry["current"] = current
    with denied(code, status):
        change_run_credential(**retry)


@pytest.mark.parametrize("mutation", ["generation", "pointer", "records", "run_revision"])
def test_partial_commit_metadata_cannot_replay(mutation: str) -> None:
    original = args("issue")
    committed = plan(**original)
    retry = replay_args(original, committed)
    state = committed.credentials
    if mutation == "generation":
        state = changed(state, last_generation=2, current_credential_id=None)
    elif mutation == "pointer":
        state = changed(state, current_credential_id=None)
    elif mutation == "records":
        state = changed(state, records=(), current_credential_id=None)
    else:
        retry["current"] = changed(retry["current"], run=changed(retry["current"].run, revision=3))
    retry["current"] = changed(retry["current"], credentials=state)
    with denied("recovery_required", 409):
        change_run_credential(**retry)


def test_replay_rechecks_request_digest_and_current_coordinator_renewal_is_allowed() -> None:
    original = args()
    committed = plan(**original)
    retry = replay_args(original, committed)
    retry["coordinator"] = changed(retry["coordinator"], authorization_id="renewed-authorization")
    assert isinstance(change_run_credential(**retry), c.RunCredentialResponse)
    retry["request"] = changed(retry["request"], credential_id="foreign")
    with denied("idempotency_conflict", 409):
        change_run_credential(**retry)


@pytest.mark.parametrize(
    "mutation,code,status",
    [
        ("stale_cas", "idempotency_conflict", 409),
        ("collision", "incompatible_state", 409),
        ("capacity", "incompatible_state", 409),
        ("missing_target", "not_found", 404),
        ("existing_issue", "incompatible_state", 409),
        ("missing_policy", "policy_unavailable", 503),
        ("lookup_unknown", "recovery_required", 409),
    ],
)
def test_fresh_admission_failures_are_explicit(mutation: str, code: str, status: int) -> None:
    original = args()
    if mutation == "stale_cas":
        original["request"] = changed(original["request"], expected_run_revision=3)
    elif mutation == "collision":
        original["new_credential_id"] = "worker-key-1"
    elif mutation == "capacity":
        original["policy"] = changed(original["policy"], max_records=1)
    elif mutation == "missing_target":
        original["request"] = changed(original["request"], credential_id="foreign")
    elif mutation == "existing_issue":
        original["operation"] = "issue"
        original["request"] = c.RunCredentialIssueRequest(
            expected_run_revision=4, expected_credential_revision=1
        )
    elif mutation == "missing_policy":
        original["policy"] = None
    elif mutation == "lookup_unknown":
        original["lookup"] = c.RunCredentialLookup(
            state="recovery_required", receipt=None, audit=None
        )
    with denied(code, status):
        change_run_credential(**original)


def test_historical_revoke_does_not_rewrite_claims_or_revoke_current_key() -> None:
    original = args()
    committed = plan(**original)
    # Revoke an older unrevoked retained key: it is already generation-fenced.
    old = changed(committed.credentials.records[0], revoked_at=None)
    state = changed(committed.credentials, records=(old, committed.credentials.records[1]))
    current = changed(
        original["current"],
        credentials=state,
        lease=changed(original["current"].lease, attempt_id="attempt-2", epoch=4),
    )
    result = plan(
        **args(
            "revoke",
            current=current,
            request=c.RunCredentialRevokeRequest(
                expected_run_revision=4,
                expected_credential_revision=2,
                credential_id="worker-key-1",
            ),
            now=1250,
        )
    )
    assert result.credentials.current_credential_id == "worker-key-2"
    assert result.credentials.records[1] == state.records[1]
    assert result.response.credential.record.claims == old.claims
    assert result.response.outcome.attempt_id == "attempt-2"
    assert result.issue_claims is None


def test_required_authority_has_no_optional_bypass_on_either_complete_guard() -> None:
    for function in (authorize_product, check_product_idempotency):
        parameter = inspect.signature(function).parameters["authority"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize("permission", ["experiments:write", "checkpoints:write", "models:write"])
def test_viewer_downgrade_blocks_each_worker_write_but_preserves_explicit_read(
    permission: str,
) -> None:
    original = value(c.RunProductAuthority)
    owner = original.current.owner
    current = changed(
        original.current,
        owner=changed(
            owner,
            grant=changed(
                owner.grant, membership=changed(owner.grant.membership, role="viewer", revision=1)
            ),
        ),
    )
    authority = changed(original, current=current)
    authorize_product(**product(authority, "experiments:read"))
    with denied("forbidden"):
        authorize_product(**product(authority, permission))


@pytest.mark.parametrize(
    "mutation", ["claims", "credential", "lease", "membership", "policy", "scope"]
)
def test_duplicate_worker_projections_and_actual_verified_claims_must_match(mutation: str) -> None:
    authority = value(c.RunProductAuthority)
    call = product(authority, "checkpoints:write")
    if mutation == "claims":
        call["authority"] = changed(
            authority, verified_claims=changed(authority.verified_claims, audience="foreign")
        )
    elif mutation == "credential":
        call["credential"] = changed(call["credential"], subject="foreign")
    elif mutation == "lease":
        call["lease"] = changed(call["lease"], epoch=4)
    elif mutation == "membership":
        call["membership"] = changed(call["membership"], revision=1)
    elif mutation == "policy":
        assert authority.policy is not None
        call["authority"] = changed(authority, policy=changed(authority.policy, audience="foreign"))
    elif mutation == "scope":
        call["credential"] = changed(call["credential"], scopes=("checkpoints:write",))
    with pytest.raises(ContractViolation):
        authorize_product(**call)


def test_original_leaf_is_audit_only_and_service_owner_uses_worker_permissions() -> None:
    original = value(c.RunProductAuthority)
    owner = changed(
        original.current.owner,
        principal=changed(original.current.owner.principal, kind="service"),
        grant=changed(
            original.current.owner.grant,
            membership=changed(original.current.owner.grant.membership, role="researcher"),
        ),
    )
    ownership = changed(
        original.current.credentials.ownership,
        principal_kind="service",
        created_by_credential_id="revoked-workspace-key",
    )
    claims = changed(original.verified_claims, ownership_sha256=message_sha256(ownership))
    record = changed(original.current.credentials.records[0], claims=claims)
    state = changed(original.current.credentials, ownership=ownership, records=(record,))
    authority = changed(
        original,
        current=changed(original.current, owner=owner, credentials=state),
        verified_claims=claims,
    )
    # Creator leaf keys are not inputs; worker and workspace-key scopes differ.
    authorize_product(**product(authority, "models:write"))


def test_human_product_write_preserves_csrf_without_management_freshness() -> None:
    authority = value(c.HumanProductAuthority)
    call = product(authority, "runs:create", now=1200)
    assert authority.policy is not None
    assert 1200 - authority.actor.session.authenticated_at >= authority.policy.recent_auth_seconds
    authorize_product(**call)
    bad = changed(
        authority,
        actor=changed(
            authority.actor, context=changed(authority.actor.context, csrf_matches=False)
        ),
    )
    authorize_product(**product(bad, "runs:read", now=1200))
    with denied("forbidden"):
        authorize_product(**product(bad, "runs:create", now=1200))


@pytest.mark.parametrize("mutation", ["principal", "generation", "session", "credential", "grant"])
def test_human_current_projection_is_mandatory(mutation: str) -> None:
    authority = value(c.HumanProductAuthority)
    call = product(authority, "runs:read")
    if mutation == "principal":
        authority = changed(
            authority,
            owner=changed(
                authority.owner, principal=changed(authority.owner.principal, active=False)
            ),
        )
    elif mutation == "generation":
        authority = changed(
            authority,
            owner=changed(
                authority.owner, principal=changed(authority.owner.principal, generation=1)
            ),
        )
    elif mutation == "session":
        authority = changed(
            authority,
            actor=changed(authority.actor, session=changed(authority.actor.session, revoked=True)),
        )
    elif mutation == "credential":
        call["credential"] = changed(call["credential"], credential_id="foreign")
    elif mutation == "grant":
        call["membership"] = changed(call["membership"], revision=1)
    call["authority"] = authority
    with pytest.raises(ContractViolation):
        authorize_product(**call)


def test_service_permission_intersection_and_lifetime_ancestry_are_distinct() -> None:
    authority = value(c.ServiceProductAuthority)
    authorize_product(**product(authority, "runs:read"))
    principal = authority.current.principal
    key = authority.current.records[0]
    expanded = changed(key, key=changed(key.key, scopes=("runs:create", "runs:read")))
    authority = changed(authority, current=changed(authority.current, records=(expanded,)))
    authorize_product(**product(authority, "runs:create"))
    viewer = changed(
        principal,
        grant=changed(
            principal.grant,
            membership=changed(principal.grant.membership, role="viewer", revision=1),
        ),
    )
    downgraded = changed(authority, current=changed(authority.current, principal=viewer))
    authorize_product(**product(downgraded, "runs:read"))
    with denied("forbidden"):
        authorize_product(**product(downgraded, "runs:create"))
    narrowed = changed(
        authority,
        current=changed(
            authority.current, principal=changed(principal, scope_ceiling=("runs:read",))
        ),
    )
    with denied("forbidden"):
        authorize_product(**product(narrowed, "runs:create"))
    revoked = changed(
        authority,
        current=changed(
            authority.current,
            records=(changed(expanded, key=changed(expanded.key, revoked_at=1200)),),
        ),
    )
    with denied("unauthenticated", 401):
        authorize_product(**product(revoked, "runs:read"))


def test_durable_ownership_admission_uses_actual_human_and_service_ancestry() -> None:
    for authority in (value(c.HumanProductAuthority), value(c.ServiceProductAuthority)):
        if authority.kind == "service":
            record = authority.current.records[0]
            authority = changed(
                authority,
                current=changed(
                    authority.current,
                    records=(
                        changed(
                            record, key=changed(record.key, scopes=("runs:create", "runs:read"))
                        ),
                    ),
                ),
            )
        call = product(authority, "runs:create")
        run = changed(
            value(RunView), workspace_id=call["workspace_id"], status="queued", revision=0
        )
        ownership = admit_run_ownership(
            call["workspace"],
            call["credential"],
            call["membership"],
            run,
            authority=authority,
            run_deadline=2000,
            worker_scopes=("experiments:read", "models:write"),
            now=1200,
        )
        assert ownership.principal_id == call["credential"].principal_id
        assert ownership.created_by_credential_id == call["credential"].credential_id
        assert ownership.scopes == ("experiments:read", "models:write")
        with denied("incompatible_state", 409):
            admit_run_ownership(
                call["workspace"],
                call["credential"],
                call["membership"],
                changed(run, revision=1),
                authority=authority,
                run_deadline=2000,
                worker_scopes=ownership.scopes,
                now=1200,
            )


@pytest.mark.parametrize("mutation", ["expired", "replaced", "revoked", "generation", "quarantine"])
def test_worker_cached_operation_rejects_current_fences_before_result(mutation: str) -> None:
    authority = value(c.RunProductAuthority)
    current = authority.current
    if mutation == "expired":
        now = 1400
    else:
        now = 1200
    if mutation == "replaced":
        committed = plan(**args())
        authority = changed(authority, current=changed(current, credentials=committed.credentials))
    elif mutation == "revoked":
        committed = plan(**args("revoke"))
        authority = changed(authority, current=changed(current, credentials=committed.credentials))
    elif mutation == "generation":
        authority = changed(
            authority,
            current=changed(
                current,
                owner=changed(
                    current.owner, principal=changed(current.owner.principal, generation=1)
                ),
            ),
        )
    call = product(authority, "experiments:write", now=now)
    if mutation == "quarantine":
        call["workspace"] = changed(
            call["workspace"], workspace=changed(call["workspace"].workspace, state="quarantined")
        )
    scope = IdempotencyScope(
        workspace_id=call["workspace_id"],
        principal_id=call["credential"].principal_id,
        kind="experiment",
        resource_id="run-1",
        key="experiment-retry",
    )
    # Invalid request/receipt shapes must not bypass current authority rejection.
    with pytest.raises(ContractViolation) as caught:
        check_product_idempotency(
            call["workspace"],
            call["credential"],
            call["membership"],
            scope,
            value(CreateRunRequest),
            value(StoredRequest),
            authority=authority,
            now=now,
            lease=call["lease"],
        )
    assert caught.value.code in {"unauthenticated", "forbidden"}


@pytest.mark.parametrize(
    "field,value_",
    [
        ("policy_id", "foreign"),
        ("attempt_id", "foreign-attempt"),
        ("lease_epoch", 99),
        ("issued_at", 1101),
        ("revoked_issue", 1100),
        ("false_revoke", None),
    ],
)
def test_receipt_operation_claims_and_commit_state_cannot_disagree(field: str, value_: Any) -> None:
    receipt = value(c.RunCredentialReceipt)
    data = receipt.model_dump(mode="json")
    if field == "policy_id":
        data[field] = value_
    elif field in {"attempt_id", "lease_epoch"}:
        data["outcome"][field] = value_
    elif field == "issued_at":
        data["outcome"]["committed_at"] = value_
    elif field == "revoked_issue":
        data["snapshot"]["records"][0]["revoked_at"] = value_
        data["snapshot"]["current_credential_id"] = None
    elif field == "false_revoke":
        data["outcome"]["operation"] = "revoke"
    with pytest.raises(ValidationError):
        c.RunCredentialReceipt.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("operation", ["replace", "revoke"])
def test_expired_current_worker_can_be_replaced_or_revoked_by_current_coordinator(
    operation: str,
) -> None:
    original = args(operation, now=1450)
    committed = plan(**original)
    assert committed.response.outcome.committed_at == 1450
    if committed.issue_claims is not None:
        assert committed.issue_claims.expires_at == 1500


@pytest.mark.parametrize(
    "mutation", ["retention_decreased", "revocation_cleared", "claims_changed"]
)
def test_later_revision_does_not_permit_nonmonotonic_replay_evidence(mutation: str) -> None:
    original = args()
    committed = plan(**original)
    retry = replay_args(original, committed)
    records = list(committed.credentials.records)
    if mutation == "retention_decreased":
        records[0] = changed(records[0], retain_until=records[0].retain_until - 1)
    elif mutation == "revocation_cleared":
        records[0] = changed(records[0], revoked_at=None)
    else:
        records[0] = changed(records[0], claims=changed(records[0].claims, audience="foreign"))
    retry["current"] = changed(
        retry["current"],
        credentials=changed(
            committed.credentials,
            revision=committed.credentials.revision + 1,
            records=tuple(records),
        ),
    )
    with denied("recovery_required", 409):
        change_run_credential(**retry)


def test_retained_receipt_expiry_is_recovery_state_never_fresh_admission() -> None:
    original = args("issue")
    committed = plan(**original)
    retry = replay_args(original, committed)
    # A short valid receipt deadline is reached while the lease and token remain live.
    receipt = changed(committed.receipt, retain_until=1201)
    audit = changed(committed.audit)
    retry["lookup"] = c.RunCredentialLookup(state="committed", receipt=receipt, audit=audit)
    with denied("recovery_required", 409):
        change_run_credential(**retry)


def test_worker_cached_success_is_bound_to_stable_owner_and_current_attempt() -> None:
    from strange_physics.control_contracts import ExperimentPage

    authority = value(c.RunProductAuthority)
    call = product(authority, "experiments:write")
    original = value(ExperimentPage).items[0]
    assert original.result is not None and original.result.kind == "experiment"
    request = original.result.value.experiment
    scope = IdempotencyScope(
        workspace_id=call["workspace_id"],
        principal_id=call["credential"].principal_id,
        kind="experiment",
        resource_id="run-1",
        key="experiment-1",
    )
    operation = changed(
        original, workspace_id=call["workspace_id"], request_sha256=message_sha256(request)
    )
    stored = StoredRequest(scope=scope, request_sha256=message_sha256(request), operation=operation)
    assert (
        check_product_idempotency(
            call["workspace"],
            call["credential"],
            call["membership"],
            scope,
            request,
            stored,
            authority=authority,
            now=1200,
            lease=call["lease"],
        )
        == operation
    )
    assert (
        check_product_idempotency(
            call["workspace"],
            call["credential"],
            call["membership"],
            scope,
            request,
            None,
            authority=authority,
            now=1200,
            lease=call["lease"],
        )
        is None
    )


@pytest.mark.parametrize("field", ["principal_generation", "grant_incarnation"])
def test_run_reenable_or_regrant_cannot_restore_old_worker(field: str) -> None:
    original = value(c.RunProductAuthority)
    owner = original.current.owner
    if field == "principal_generation":
        owner = changed(owner, principal=changed(owner.principal, active=True, generation=2))
    else:
        owner = changed(owner, grant=changed(owner.grant, incarnation=2))
    authority = changed(original, current=changed(original.current, owner=owner))
    with denied("forbidden"):
        authorize_product(**product(authority, "experiments:read"))


def test_session_policy_failure_uses_existing_public_error_envelope() -> None:
    from strange_physics.session_contracts import workspace_session_error

    authority = value(c.HumanProductAuthority)
    with denied("policy_unavailable", 503) as caught:
        authorize_product(**product(changed(authority, policy=None), "runs:read"))
    status, error = workspace_session_error(caught.value, request_id="request-1")
    assert status == 503 and error.code == "temporarily_unavailable"
    assert error.retryable and error.operation_id is None
