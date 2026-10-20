from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import (
    ContractViolation,
    CreateRunRequest,
    IdempotencyScope,
    Membership,
    RunLease,
    StoredRequest,
    VerifiedCredential,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.session_contracts import DeploymentSessionPolicy
from strange_physics.workspace_contracts import (
    PUBLIC_MODELS,
    WORKSPACE_MODELS,
    BrowserActor,
    CreateWorkspaceRequest,
    IdempotencyKey,
    ManagementReceipt,
    MemberRevokeRequest,
    MemberRoleRequest,
    PrincipalStatus,
    SecurityRevocation,
    SecurityRevocationAuthority,
    WorkspaceAuthority,
    WorkspaceCreationGrant,
    WorkspaceView,
    authorize_management,
    authorize_product,
    check_creation_replay,
    check_member_replay,
    check_product_idempotency,
    management_session_error,
    validate_human_actor,
    validate_member_change,
    validate_security_revocation,
    validate_workspace_creation,
    workspace_json_schema,
    workspace_status,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "contracts/workspace.examples.json").read_text())
SESSION = json.loads((ROOT / "contracts/session.examples.json").read_text())["valid"]
CONTROL = json.loads((ROOT / "contracts/control.examples.json").read_text())["valid"]
MODELS = {m.__name__: m for m in WORKSPACE_MODELS}


def value[T: Message](model: type[T], **changes: Any) -> T:
    data = copy.deepcopy((EXAMPLES["valid"] | SESSION | CONTROL)[model.__name__])
    data.update(changes)
    return model.model_validate_json(json.dumps(data))


def changed[T: Message](obj: T, **changes: Any) -> T:
    return type(obj).model_validate_json(json.dumps(obj.model_dump(mode="json") | changes))


def owner(**changes: Any) -> Membership:
    return value(Membership, **({"role": "owner"} | changes))


def actor(**changes: Any) -> BrowserActor:
    return value(BrowserActor, **changes)


def authority(owners: tuple[str, ...] = ("principal-1",), **changes: Any) -> WorkspaceAuthority:
    return WorkspaceAuthority(
        workspace=value(WorkspaceView, **changes), active_owner_ids=owners, disabled_owner_ids=()
    )


def policy() -> DeploymentSessionPolicy:
    return value(DeploymentSessionPolicy)


def denied(code: str, status: int = 403) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda e: e.status == status)


@pytest.mark.parametrize("model", WORKSPACE_MODELS)
def test_shared_shapes(model: type[Message]) -> None:
    value(model)


@pytest.mark.parametrize("case", EXAMPLES["schema_negative"] + EXAMPLES["runtime_negative"])
def test_shared_negative_shapes(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        value(MODELS[case["model"]], **{case["field"]: case["value"]})


def test_schema_public_boundary_and_safe_projection() -> None:
    assert (
        json.loads((ROOT / "contracts/workspace.schema.json").read_text())
        == workspace_json_schema()
    )
    public = {m.__name__ for m in PUBLIC_MODELS}
    assert public.isdisjoint({"BrowserActor", "SecurityRevocation", "ManagementReceipt"})
    assert set(Membership.model_fields) == {
        "workspace_id",
        "principal_id",
        "role",
        "active",
        "revision",
    }
    assert set(CreateWorkspaceRequest.model_fields) == {"display_name"}


@pytest.mark.parametrize(
    "patch,code,status",
    [
        ({"has_session_cookie": False}, "unauthenticated", 401),
        ({"has_session_cookie": False, "has_bearer": True}, "unauthenticated", 401),
        ({"has_bearer": True}, "ambiguous_credentials", 400),
        ({"csrf_matches": False}, "forbidden", 403),
        ({"csrf_scope": "preauth"}, "forbidden", 403),
        ({"origin": "https://other.example"}, "forbidden", 403),
    ],
)
def test_only_current_human_session_and_csrf(patch: dict[str, Any], code: str, status: int) -> None:
    current = actor()
    with denied(code, status):
        validate_human_actor(
            policy(),
            changed(current, context=current.context.model_dump(mode="json") | patch),
            now=1020,
            mutation=True,
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"revoked": True},
        {"principal_active": False},
        {"generation": 1},
    ],
)
def test_current_session_lookup_not_a_cached_actor(patch: dict[str, Any]) -> None:
    current = actor()
    with denied("unauthenticated", 401):
        validate_human_actor(
            policy(),
            changed(current, session=current.session.model_dump(mode="json") | patch),
            now=1020,
            mutation=True,
        )


def test_fail_closed_policy_expiry_and_exact_freshness_boundary() -> None:
    with denied("policy_unavailable", 503):
        validate_human_actor(None, actor(), now=1020, mutation=True)
    validate_human_actor(policy(), actor(), now=1109, mutation=True)
    with denied("reauthentication_required", 401):
        validate_human_actor(policy(), actor(), now=1110, mutation=True)
    # Ordinary reads remain permitted; last_seen/generation renewal cannot restore auth_time.
    renewed = changed(actor(), session=SESSION["SessionRecord"] | {"last_seen_at": 1110})
    validate_human_actor(policy(), renewed, now=1110, mutation=False)
    with denied("reauthentication_required", 401):
        validate_human_actor(policy(), renewed, now=1110, mutation=True)
    with denied("unauthenticated", 401):
        validate_human_actor(policy(), actor(), now=4610, mutation=False)


def test_freshness_signal_is_explicit_and_absent_for_other_session_failures() -> None:
    fixture = EXAMPLES["freshness_failure"]
    status, body, headers = management_session_error(
        ContractViolation(fixture["internal_code"], fixture["status"]), request_id="request-1"
    )
    assert (status, body.model_dump(mode="json"), headers) == (
        fixture["status"],
        fixture["body"],
        fixture["headers"],
    )
    for code, expected in [
        ("unauthenticated", 401),
        ("forbidden", 403),
        ("ambiguous_credentials", 400),
        ("policy_unavailable", 503),
    ]:
        status, _, headers = management_session_error(
            ContractViolation(code, expected), request_id="request-1"
        )
        assert status == expected and headers == {}
    with pytest.raises(ValueError):
        management_session_error(
            ContractViolation("reauthentication_required", 403), request_id="request-1"
        )


def test_visibility_precedes_role_and_quarantine_details() -> None:
    with denied("not_found", 404):
        authorize_management(
            policy(),
            actor(),
            authority(state="quarantined"),
            owner(),
            workspace_id="foreign",
            now=1020,
            owner_required=True,
            mutation=True,
        )
    for role in ("researcher", "viewer"):
        member = value(Membership, role=role)
        current = authority(("other-owner",), state="quarantined")
        authorize_management(
            policy(),
            actor(),
            current,
            member,
            workspace_id="ws-1",
            now=1020,
            owner_required=False,
            mutation=False,
        )
        with denied("forbidden"):
            authorize_management(
                policy(),
                actor(),
                current,
                member,
                workspace_id="ws-1",
                now=1020,
                owner_required=True,
                mutation=False,
            )
    with denied("forbidden"):
        authorize_management(
            policy(),
            actor(),
            authority(),
            owner(active=False),
            workspace_id="ws-1",
            now=1020,
            owner_required=False,
            mutation=False,
        )


def creation(**changes: Any) -> None:
    grant = value(WorkspaceCreationGrant)
    args: dict[str, Any] = dict(
        policy=policy(),
        actor=actor(),
        grant=grant,
        consumed_grant=changed(grant, consumed_workspace_id="ws-1"),
        request=value(CreateWorkspaceRequest),
        created=authority(revision=0),
        initial_member=owner(revision=0),
        now=1020,
    )
    args.update(changes)
    validate_workspace_creation(**args)


def test_creation_is_one_atomic_private_owner_bootstrap() -> None:
    creation()
    for grant in [
        value(WorkspaceCreationGrant, principal_id="other"),
        value(WorkspaceCreationGrant, revoked=True),
        value(WorkspaceCreationGrant, expires_at=1020),
    ]:
        with denied("forbidden"):
            creation(grant=grant)
    with denied("incompatible_state", 409):
        creation(grant=value(WorkspaceCreationGrant, consumed_workspace_id="prior"))
    invalid_proposals: list[dict[str, Any]] = [
        {"initial_member": owner(revision=1)},
        {"created": authority(("other",), revision=0)},
        {"created": authority(revision=0, display_name="different")},
        {"consumed_grant": value(WorkspaceCreationGrant, consumed_workspace_id="other")},
    ]
    for patch in invalid_proposals:
        with denied("incompatible_state", 409):
            creation(**patch)


def test_creation_retry_current_authority_and_exact_grant_binding() -> None:
    grant = value(WorkspaceCreationGrant, consumed_workspace_id="ws-1")
    args: dict[str, Any] = dict(
        policy=policy(),
        actor=actor(),
        grant=grant,
        request=value(CreateWorkspaceRequest),
        key="create-1",
        stored=value(ManagementReceipt),
        created=authority(),
        membership=owner(),
        now=1020,
    )
    assert check_creation_replay(**args) == "ws-1"
    failures: list[tuple[dict[str, Any], str, int]] = [
        ({"grant": changed(grant, revoked=True)}, "forbidden", 403),
        ({"membership": owner(active=False)}, "forbidden", 403),
        ({"created": authority(state="quarantined")}, "forbidden", 403),
        ({"created": None}, "not_found", 404),
        (
            {"request": value(CreateWorkspaceRequest, display_name="changed")},
            "idempotency_conflict",
            409,
        ),
    ]
    for patch, code, status in failures:
        with denied(code, status):
            check_creation_replay(**(args | patch))


def change_args(**changes: Any) -> dict[str, Any]:
    target = owner(principal_id="principal-2")
    args: dict[str, Any] = dict(
        policy=policy(),
        actor=actor(),
        before=authority(("principal-1", "principal-2")),
        after=authority(revision=3),
        actor_membership=owner(),
        target=target,
        updated=changed(target, role="viewer", revision=5),
        request=value(MemberRoleRequest),
        workspace_id="ws-1",
        target_principal_id="principal-2",
        target_principal=PrincipalStatus(principal_id="principal-2", active=True),
        now=1020,
    )
    return args | changes


def test_owner_change_cas_and_complete_current_owner_set() -> None:
    validate_member_change(**change_args())
    failures: list[tuple[dict[str, Any], str, int]] = [
        ({"before": authority()}, "incompatible_state", 409),
        (
            {"request": value(MemberRoleRequest, expected_workspace_revision=1)},
            "incompatible_state",
            409,
        ),
        (
            {"request": value(MemberRoleRequest, expected_membership_revision=3)},
            "incompatible_state",
            409,
        ),
        ({"target_principal_id": "foreign"}, "not_found", 404),
        ({"after": authority(revision=4)}, "incompatible_state", 409),
    ]
    for patch, code, status in failures:
        with denied(code, status):
            validate_member_change(**change_args(**patch))


@pytest.mark.parametrize("mutation_request", [value(MemberRoleRequest), value(MemberRevokeRequest)])
def test_elective_last_owner_change_denied(
    mutation_request: MemberRoleRequest | MemberRevokeRequest,
) -> None:
    with denied("incompatible_state", 409):
        validate_member_change(
            **change_args(
                before=authority(),
                after=authority((), state="quarantined", revision=3),
                target=owner(),
                target_principal_id="principal-1",
                target_principal=PrincipalStatus(principal_id="principal-1", active=True),
                request=mutation_request,
                updated=owner(role="viewer", revision=5)
                if isinstance(mutation_request, MemberRoleRequest)
                else owner(active=False, revision=5),
            )
        )


def test_second_competing_owner_change_rechecks_actor_and_shared_revision() -> None:
    # Two proposals from revision 2 cannot both satisfy the refreshed state.
    validate_member_change(**change_args())
    second_actor = changed(
        actor(), session=SESSION["SessionRecord"] | {"principal_id": "principal-2"}
    )
    with denied("forbidden"):
        validate_member_change(
            **change_args(
                actor=second_actor,
                before=authority(revision=3),
                actor_membership=value(
                    Membership, principal_id="principal-2", role="viewer", revision=5
                ),
                target=owner(),
                target_principal_id="principal-1",
            )
        )
    # Real lock/CAS concurrency still belongs to the SQL integration producer.


def test_member_retry_rechecks_authority_before_receipt_but_not_original_cas() -> None:
    request = value(MemberRoleRequest)
    receipt = value(
        ManagementReceipt,
        operation="member_role",
        workspace_id="ws-1",
        target_principal_id="principal-2",
        grant_id=None,
        key="change-1",
        request_sha256=message_sha256(request),
        outcome_id="outcome-1",
    )
    args: dict[str, Any] = dict(
        policy=policy(),
        actor=actor(),
        authority=authority(revision=3),
        membership=owner(),
        request=request,
        workspace_id="ws-1",
        target_principal_id="principal-2",
        key="change-1",
        stored=receipt,
        now=1020,
    )
    assert check_member_replay(**args) == "outcome-1"
    with denied("forbidden"):
        check_member_replay(
            **(
                args
                | {
                    "authority": authority(state="quarantined"),
                    "stored": changed(receipt, request_sha256="0" * 64),
                }
            )
        )
    with denied("idempotency_conflict", 409):
        check_member_replay(**(args | {"key": "other"}))
    with denied("reauthentication_required", 401):
        check_member_replay(**(args | {"now": 1110}))


def security_args(**changes: Any) -> dict[str, Any]:
    return (
        dict(
            authorization=value(SecurityRevocationAuthority),
            event=value(SecurityRevocation),
            before=authority(),
            after=authority((), state="quarantined", revision=3),
            target=owner(),
            updated=owner(active=False, revision=5),
            now=1020,
        )
        | changes
    )


def test_security_revocation_can_quarantine_last_owner_without_public_bypass() -> None:
    validate_security_revocation(**security_args())
    failures: list[tuple[dict[str, Any], str, int]] = [
        ({"authorization": value(SecurityRevocationAuthority, revoked=True)}, "forbidden", 403),
        ({"authorization": value(SecurityRevocationAuthority, expires_at=1020)}, "forbidden", 403),
        ({"authorization": value(SecurityRevocationAuthority, actor_id="other")}, "not_found", 404),
        ({"event": value(SecurityRevocation, workspace_id="other")}, "not_found", 404),
        ({"event": value(SecurityRevocation, principal_id="other")}, "not_found", 404),
        ({"after": authority(revision=3)}, "incompatible_state", 409),
    ]
    for patch, code, status in failures:
        with denied(code, status):
            validate_security_revocation(**security_args(**patch))


def test_quarantine_fences_product_and_cached_operation_before_conflict_details() -> None:
    credential = value(VerifiedCredential)
    member = owner()
    for kind in ("user", "service"):
        current = changed(credential, kind=kind)
        authorize_product(
            authority(),
            current,
            member,
            permission="runs:create",
            workspace_id="ws-1",
            now=100,
        )
        with denied("forbidden"):
            authorize_product(
                authority(state="quarantined"),
                current,
                member,
                permission="runs:create",
                workspace_id="ws-1",
                now=100,
            )
    args: dict[str, Any] = dict(
        workspace=authority(),
        credential=credential,
        membership=member,
        scope=value(IdempotencyScope),
        request=value(CreateRunRequest),
        stored=value(StoredRequest),
        now=100,
    )
    assert check_product_idempotency(**args) == value(StoredRequest).operation
    with denied("forbidden"):
        check_product_idempotency(
            **(
                args
                | {
                    "workspace": authority(state="quarantined"),
                    "stored": changed(
                        value(StoredRequest), scope=CONTROL["IdempotencyScope"] | {"key": "other"}
                    ),
                }
            )
        )
    with denied("not_found", 404):
        check_product_idempotency(
            **(
                args
                | {
                    "workspace": authority(workspace_id="foreign"),
                }
            )
        )


def test_http_boundaries_headers_and_exact_shared_constraints() -> None:
    api = json.loads((ROOT / "contracts/workspace.openapi.json").read_text())
    assert len(api["paths"]) == 6
    for path, methods in api["paths"].items():
        assert not any(word in path for word in ("security", "invite", "link"))
        for method, operation in methods.items():
            expected: dict[str, list[str]] = {"sessionCookie": []}
            if method != "get":
                expected["csrfHeader"] = []
            assert operation["security"] == [expected]
            assert operation["responses"]["401"]["headers"]["X-Authentication-Action"][
                "schema"
            ] == {"type": "string", "const": "reauthenticate"}
            for parameter in operation["parameters"]:
                if parameter["in"] == "path":
                    assert parameter["schema"] == TypeAdapter(Identifier).json_schema()
                if parameter["name"] == "Idempotency-Key":
                    assert parameter["schema"] == TypeAdapter(IdempotencyKey).json_schema()
            assert operation["x-response-headers"]["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "owner_ids,disabled_ids",
    [
        (("principal-1", "principal-2"), ("principal-2",)),
        (("principal-1", "principal-2"), ("principal-1", "principal-2")),
    ],
)
def test_security_fanout_uses_membership_owners_and_current_disabled_principals(
    owner_ids: tuple[str, ...], disabled_ids: tuple[str, ...]
) -> None:
    before = changed(authority(owner_ids), disabled_owner_ids=disabled_ids)
    # Remove principal-1, leaving only a disabled owner row; persist quarantine.
    after = changed(
        authority(("principal-2",), state="quarantined", revision=3),
        disabled_owner_ids=("principal-2",),
    )
    validate_security_revocation(**security_args(before=before, after=after))
    # The second event can remove the final disabled row without owner consent.
    validate_security_revocation(
        **security_args(
            event=value(SecurityRevocation, principal_id="principal-2"),
            before=after,
            after=authority((), state="quarantined", revision=4),
            target=owner(principal_id="principal-2"),
            updated=owner(principal_id="principal-2", active=False, revision=5),
        )
    )


@pytest.mark.parametrize("mutation_request", [value(MemberRoleRequest), value(MemberRevokeRequest)])
def test_last_enabled_owner_cannot_leave_disabled_owner_as_replacement(
    mutation_request: MemberRoleRequest | MemberRevokeRequest,
) -> None:
    before = changed(authority(("principal-1", "principal-2")), disabled_owner_ids=("principal-2",))
    after = changed(
        authority(("principal-2",), state="quarantined", revision=3),
        disabled_owner_ids=("principal-2",),
    )
    with denied("incompatible_state", 409):
        validate_member_change(
            **change_args(
                before=before,
                after=after,
                target=owner(),
                target_principal_id="principal-1",
                target_principal=PrincipalStatus(principal_id="principal-1", active=True),
                request=mutation_request,
                updated=owner(role="viewer", revision=5)
                if isinstance(mutation_request, MemberRoleRequest)
                else owner(active=False, revision=5),
            )
        )


def test_disabled_researcher_promotion_and_misbound_principal_evidence_fail() -> None:
    args = change_args(
        before=authority(),
        after=authority(("principal-1", "principal-2"), revision=3),
        target=value(Membership, principal_id="principal-2"),
        updated=owner(principal_id="principal-2", revision=5),
        request=value(MemberRoleRequest, role="owner"),
    )
    validate_member_change(**args)
    with denied("incompatible_state", 409):
        validate_member_change(
            **(
                args
                | {
                    "target_principal": PrincipalStatus(principal_id="principal-2", active=False),
                }
            )
        )
    with denied("not_found", 404):
        validate_member_change(
            **(
                args
                | {
                    "target_principal": PrincipalStatus(principal_id="other", active=True),
                }
            )
        )


def test_effective_quarantine_precedes_persisted_state_and_cached_receipt() -> None:
    lagging = changed(authority(), disabled_owner_ids=("principal-1",))
    assert lagging.workspace.state == "active"  # Persisted field before event settlement.
    assert workspace_status(lagging).state == "quarantined"
    with denied("forbidden"):
        check_product_idempotency(
            lagging,
            value(VerifiedCredential),
            owner(),
            value(IdempotencyScope),
            value(CreateRunRequest),
            value(StoredRequest),
            now=100,
        )
    # Use an enabled non-owner for the safe caller-bound status exception.
    observer = changed(actor(), session=SESSION["SessionRecord"] | {"principal_id": "observer"})
    authorize_management(
        policy(),
        observer,
        lagging,
        value(Membership, principal_id="observer"),
        workspace_id="ws-1",
        now=1020,
        owner_required=False,
        mutation=False,
    )
    with pytest.raises(ValidationError):
        changed(authority(), disabled_owner_ids=("not-an-owner",))
    with pytest.raises(ValidationError):
        changed(authority(), disabled_owner_ids=("principal-1", "principal-1"))


def test_run_worker_lease_checks_remain_required_through_product_composition() -> None:
    current = value(
        VerifiedCredential,
        kind="run",
        run_id="run-1",
        attempt_id="attempt-1",
        lease_epoch=3,
        scopes=["checkpoints:write"],
    )
    lease = value(RunLease)
    args: dict[str, Any] = dict(
        workspace=authority(),
        credential=current,
        membership=owner(),
        permission="checkpoints:write",
        workspace_id="ws-1",
        now=100,
        run_id="run-1",
        lease=lease,
    )
    authorize_product(**args)
    with denied("forbidden"):
        authorize_product(**(args | {"workspace": authority(state="quarantined")}))
    with denied("forbidden"):
        authorize_product(**(args | {"lease": changed(lease, epoch=4)}))
