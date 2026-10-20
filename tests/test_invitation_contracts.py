from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation, Membership
from strange_physics.invitation_contracts import (
    INVITATION_MODELS,
    PUBLIC_MODELS,
    CreateInvitationRequest,
    CurrentRecipientIdentity,
    InvitationIssued,
    InvitationPolicy,
    InvitationReceipt,
    InvitationRecord,
    InvitationView,
    RedeemInvitationRequest,
    RedemptionContext,
    RedemptionResult,
    RevokeInvitationRequest,
    VerifiedEmailAssertion,
    authorize_invitation_owner,
    canonical_email,
    check_owner_invitation_replay,
    check_redemption_replay,
    invitation_json_schema,
    invitation_token_sha256,
    invitation_view,
    redemption_request_sha256,
    validate_invitation_issue,
    validate_invitation_redemption,
    validate_invitation_revoke,
)
from strange_physics.session_contracts import DeploymentSessionPolicy
from strange_physics.workspace_contracts import BrowserActor, WorkspaceAuthority

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/invitation.examples.json").read_text())
WORKSPACE = json.loads((ROOT / "contracts/workspace.examples.json").read_text())["valid"]
SESSION = json.loads((ROOT / "contracts/session.examples.json").read_text())["valid"]
MODELS = {m.__name__: m for m in INVITATION_MODELS}


def value[T: Message](model: type[T], **changes: Any) -> T:
    data = copy.deepcopy((WORKSPACE | SESSION | FIXTURES["valid"])[model.__name__])
    return model.model_validate_json(json.dumps(data | changes))


def changed[T: Message](model: T, **changes: Any) -> T:
    return type(model).model_validate_json(json.dumps(model.model_dump(mode="json") | changes))


def denied(code: str, status: int = 404) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda error: error.status == status)


def issue_args(**changes: Any) -> dict[str, Any]:
    return (
        dict(
            session_policy=value(DeploymentSessionPolicy),
            invitation_policy=value(InvitationPolicy),
            actor=value(BrowserActor),
            workspace=value(WorkspaceAuthority),
            membership=Membership.model_validate_json(
                json.dumps(WORKSPACE["MemberPage"]["items"][0])
            ),
            request=value(CreateInvitationRequest),
            issued=value(InvitationIssued),
            record=value(InvitationRecord),
            workspace_id="ws-1",
            pending_count=0,
            recipient_pending=False,
            now=1020,
        )
        | changes
    )


def redeem_args(**changes: Any) -> dict[str, Any]:
    context = value(RedemptionContext)
    return (
        dict(
            session_policy=value(DeploymentSessionPolicy),
            invitation_policy=value(InvitationPolicy),
            context=context,
            before=value(InvitationRecord),
            after=value(
                InvitationRecord,
                state="accepted",
                revision=1,
                accepted_principal_id="recipient-1",
                resolved_at=1020,
            ),
            request=value(RedeemInvitationRequest),
            resulting_member=value(RedemptionResult).membership,
            resulting_workspace=changed(
                context.workspace,
                workspace=context.workspace.workspace.model_dump() | {"revision": 3},
            ),
            now=1020,
        )
        | changes
    )


def recipient_context(**changes: Any) -> RedemptionContext:
    return value(RedemptionContext, **changes)


@pytest.mark.parametrize("model", INVITATION_MODELS)
def test_shared_synthetic_shapes(model: type[Message]) -> None:
    value(model)


@pytest.mark.parametrize("case", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_shared_negatives(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        value(MODELS[case["model"]], **{case["field"]: case["value"]})


def test_generated_schema_and_public_secret_boundary() -> None:
    schema = invitation_json_schema()
    assert schema == json.loads((ROOT / "contracts/invitation.schema.json").read_text())
    assert "InvitationReceipt" not in {m.__name__ for m in PUBLIC_MODELS}
    response = schema["$defs"]["InvitationIssued"]["properties"]["token"]
    request = schema["$defs"]["RedeemInvitationRequest"]["properties"]["token"]
    assert response["readOnly"] is True and "writeOnly" not in response
    assert request["writeOnly"] is True and "readOnly" not in request
    assert "token_sha256" not in InvitationView.model_fields
    assert "token" not in InvitationReceipt.model_fields
    for model in (InvitationIssued, RedeemInvitationRequest):
        parsed = value(model)
        token = FIXTURES["valid"][model.__name__]["token"]
        assert token not in repr(parsed) and token not in parsed.model_dump_json()


@pytest.mark.parametrize(
    "email",
    [
        " name@example.test",
        "name@example.test ",
        "name@example.test\n",
        "ü@example.test",
        '"name"@example.test',
        "name..x@example.test",
        "name@example",
        "name@-example.test",
    ],
)
def test_unsupported_email_fails_closed(email: str) -> None:
    with pytest.raises(ValidationError):
        value(CreateInvitationRequest, recipient_email=email)


def test_email_profile_preserves_local_case_plus_and_dots() -> None:
    assert canonical_email("Recipient+lab@EXAMPLE.test") == "Recipient+lab@example.test"
    assert canonical_email("Recipient+lab@example.test") != canonical_email(
        "recipient+lab@example.test"
    )
    assert canonical_email("first.last@example.test") != canonical_email("firstlast@example.test")
    assert canonical_email("name+lab@example.test") != canonical_email("name@example.test")


@pytest.mark.parametrize(
    "token", ["A" * 42, "A" * 44, "A" * 42 + "B", "A" * 43 + "=", "A" * 42 + "!", "A" * 43 + "\n"]
)
def test_noncanonical_token_rejected_before_identity(token: str) -> None:
    with pytest.raises(ValidationError):
        value(RedeemInvitationRequest, token=token)
    with pytest.raises(ValueError):
        invitation_token_sha256(SecretStr(token))


def test_different_secrets_have_different_explicit_request_identity_despite_equal_masks() -> None:
    first = value(RedeemInvitationRequest)
    second = value(
        RedeemInvitationRequest,
        token=base64.urlsafe_b64encode(b"x" * 32).decode("ascii").rstrip("="),
    )
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert redemption_request_sha256(first) != redemption_request_sha256(second)
    assert invitation_token_sha256(first.token) != invitation_token_sha256(second.token)
    assert first.token.get_secret_value() not in redemption_request_sha256(first)


def test_issue_requires_current_owner_atomic_grant_and_admission_caps() -> None:
    validate_invitation_issue(**issue_args())
    failures: list[dict[str, Any]] = [
        {"request": value(CreateInvitationRequest, expected_workspace_revision=1)},
        {"pending_count": value(InvitationPolicy).max_pending_per_workspace},
        {"recipient_pending": True},
        {"record": value(InvitationRecord, role="owner")},
        {"record": value(InvitationRecord, expires_at=1621)},
        {"record": value(InvitationRecord, inviter_principal_id="other")},
    ]
    for patch in failures:
        with denied("incompatible_state", 409):
            validate_invitation_issue(**issue_args(**patch))
    with denied("policy_unavailable", 503):
        validate_invitation_issue(**issue_args(invitation_policy=None))
    with denied("reauthentication_required", 401):
        validate_invitation_issue(**issue_args(now=1110))
    with denied("not_found"):
        validate_invitation_issue(**issue_args(workspace_id="foreign"))


def test_owner_metadata_retry_has_no_secret_and_does_not_reapply_original_revision() -> None:
    source = issue_args()
    args: dict[str, Any] = dict(
        policy=source["session_policy"],
        actor=source["actor"],
        workspace=changed(
            source["workspace"],
            workspace=source["workspace"].workspace.model_dump() | {"revision": 3},
        ),
        membership=source["membership"],
        request=source["request"],
        workspace_id="ws-1",
        invitation_id=None,
        key="issue-1",
        stored=value(InvitationReceipt),
        record=value(InvitationRecord),
        now=1020,
    )
    metadata = check_owner_invitation_replay(**args)
    assert metadata == value(InvitationView)
    assert metadata is not None and "token" not in metadata.model_dump()
    accepted = redeem_args()["after"]
    accepted_metadata = check_owner_invitation_replay(**(args | {"record": accepted}))
    assert accepted_metadata is not None and accepted_metadata.state == "accepted"
    with denied("forbidden", 403):
        check_owner_invitation_replay(
            **(args | {"membership": changed(source["membership"], active=False)})
        )
    with denied("idempotency_conflict", 409):
        check_owner_invitation_replay(
            **(args | {"request": value(CreateInvitationRequest, role="owner")})
        )


def test_owner_listing_uses_current_human_membership_without_extra_freshness() -> None:
    source = issue_args()
    args: dict[str, Any] = dict(
        policy=source["session_policy"],
        actor=source["actor"],
        workspace=source["workspace"],
        membership=source["membership"],
        workspace_id="ws-1",
        now=1110,
        mutation=False,
    )
    authorize_invitation_owner(**args)
    with denied("forbidden", 403):
        authorize_invitation_owner(
            **(args | {"membership": changed(source["membership"], role="viewer")})
        )
    with denied("unauthenticated", 401):
        actor = source["actor"]
        authorize_invitation_owner(
            **(
                args
                | {
                    "actor": changed(
                        actor, context=actor.context.model_dump() | {"has_session_cookie": False}
                    )
                }
            )
        )


@pytest.mark.parametrize(
    "field,value_patch",
    [
        ("email", "other@example.test"),
        ("email_verified", False),
        ("issued_at", 900),
        ("issued_at", 1021),
        ("verified_at", 1021),
        ("expires_at", 1020),
        ("subject", "other"),
        ("provider_id", "unknown"),
        ("issuer", "https://untrusted.example"),
        ("session_id", "other"),
        ("session_generation", 1),
    ],
)
def test_recipient_claim_binding_and_actual_upstream_freshness(
    field: str, value_patch: Any
) -> None:
    assertion = value(VerifiedEmailAssertion, **{field: value_patch})
    context = recipient_context(email_assertion=assertion.model_dump(mode="json"))
    with denied("not_found"):
        validate_invitation_redemption(**redeem_args(context=context))


def test_fresh_local_parse_does_not_refresh_old_claim_or_actual_authentication() -> None:
    assertion = value(VerifiedEmailAssertion, issued_at=900, verified_at=1020)
    with denied("not_found"):
        validate_invitation_redemption(
            **redeem_args(
                context=recipient_context(email_assertion=assertion.model_dump(mode="json"))
            )
        )
    with denied("reauthentication_required", 401):
        validate_invitation_redemption(**redeem_args(now=1110))


@pytest.mark.parametrize("field", ["principal", "identity_active", "subject"])
def test_recipient_current_mapping_is_separate_from_verified_upstream_claim(field: str) -> None:
    identity = value(CurrentRecipientIdentity)
    changes: dict[str, Any] = {
        "principal": identity.principal.model_dump() | {"principal_id": "other"},
        "identity_active": False,
        "subject": "other",
    }
    with denied("not_found"):
        validate_invitation_redemption(
            **redeem_args(
                context=recipient_context(
                    recipient_identity=changed(identity, **{field: changes[field]}).model_dump(
                        mode="json"
                    )
                )
            )
        )


def test_inviter_need_not_be_online_but_must_remain_current_enabled_owner() -> None:
    validate_invitation_redemption(**redeem_args())
    context = value(RedemptionContext)
    bad_contexts = [
        changed(
            context, inviter_membership=context.inviter_membership.model_dump() | {"role": "viewer"}
        ),
        changed(
            context, inviter_membership=context.inviter_membership.model_dump() | {"active": False}
        ),
        changed(
            context, inviter_principal=context.inviter_principal.model_dump() | {"active": False}
        ),
        changed(
            context,
            workspace=context.workspace.model_dump() | {"disabled_owner_ids": ["principal-1"]},
        ),
        changed(
            context,
            workspace=context.workspace.model_dump()
            | {"workspace": context.workspace.workspace.model_dump() | {"state": "quarantined"}},
        ),
    ]
    for current in bad_contexts:
        with denied("not_found"):
            validate_invitation_redemption(**redeem_args(context=current))


@pytest.mark.parametrize("current_role", ["owner", "researcher", "viewer"])
@pytest.mark.parametrize("invited_role", ["owner", "researcher", "viewer"])
def test_existing_active_membership_is_never_implicitly_elevated_or_demoted(
    current_role: str, invited_role: str
) -> None:
    context = value(RedemptionContext)
    member = changed(value(RedemptionResult).membership, role=current_role, revision=7)
    workspace = context.workspace
    if current_role == "owner":
        workspace = changed(workspace, active_owner_ids=["principal-1", "recipient-1"])
    context = changed(
        context, recipient_membership=member.model_dump(), workspace=workspace.model_dump()
    )
    args = redeem_args(
        context=context,
        before=value(InvitationRecord, role=invited_role),
        after=value(
            InvitationRecord,
            role=invited_role,
            state="accepted",
            revision=1,
            accepted_principal_id="recipient-1",
            resolved_at=1020,
        ),
        resulting_member=member,
        resulting_workspace=workspace,
    )
    validate_invitation_redemption(**args)
    with denied("incompatible_state", 409):
        validate_invitation_redemption(**(args | {"resulting_member": changed(member, revision=8)}))


def test_inactive_member_cannot_be_resurrected() -> None:
    member = changed(value(RedemptionResult).membership, active=False)
    with denied("not_found"):
        validate_invitation_redemption(
            **redeem_args(context=recipient_context(recipient_membership=member.model_dump()))
        )


def revoke_args(**changes: Any) -> dict[str, Any]:
    source = issue_args()
    return (
        dict(
            policy=source["session_policy"],
            actor=source["actor"],
            workspace=source["workspace"],
            membership=source["membership"],
            before=value(InvitationRecord),
            after=value(InvitationRecord, state="revoked", revision=1, resolved_at=1020),
            request=value(RevokeInvitationRequest),
            workspace_id="ws-1",
            invitation_id="invite-1",
            now=1020,
        )
        | changes
    )


def test_consume_and_revoke_have_one_terminal_winner_without_membership_side_effects() -> None:
    validate_invitation_revoke(**revoke_args())
    validate_invitation_redemption(**redeem_args())
    with denied("incompatible_state", 409):
        validate_invitation_revoke(
            **revoke_args(
                before=redeem_args()["after"],
                request=value(RevokeInvitationRequest, expected_invitation_revision=1),
            )
        )
    with denied("not_found"):
        validate_invitation_redemption(**redeem_args(before=revoke_args()["after"]))
    with denied("incompatible_state", 409):
        validate_invitation_revoke(
            **revoke_args(
                after=value(
                    InvitationRecord,
                    recipient_email="other@example.test",
                    state="revoked",
                    revision=1,
                    resolved_at=1020,
                )
            )
        )


def replay_args(**changes: Any) -> dict[str, Any]:
    args = redeem_args()
    member = args["resulting_member"]
    context = changed(
        args["context"],
        recipient_membership=member.model_dump(),
        workspace=args["resulting_workspace"].model_dump(),
    )
    return (
        dict(
            session_policy=args["session_policy"],
            invitation_policy=args["invitation_policy"],
            context=context,
            record=args["after"],
            request=args["request"],
            key="redeem-1",
            stored=value(
                InvitationReceipt,
                principal_id="recipient-1",
                operation="redeem",
                target_invitation_id="invite-1",
                key="redeem-1",
                request_sha256=redemption_request_sha256(args["request"]),
            ),
            now=1020,
        )
        | changes
    )


def test_redemption_retry_checks_current_recipient_inviter_and_actual_membership() -> None:
    args = replay_args()
    assert check_redemption_replay(**args) == value(RedemptionResult)
    context = args["context"]
    for current in [
        changed(
            context,
            recipient_membership=context.recipient_membership.model_dump() | {"active": False},
        ),
        changed(
            context, inviter_membership=context.inviter_membership.model_dump() | {"role": "viewer"}
        ),
        changed(
            context,
            actor=context.actor.model_dump()
            | {"session": context.actor.session.model_dump() | {"revoked": True}},
        ),
    ]:
        with pytest.raises(ContractViolation):
            check_redemption_replay(**(args | {"context": current}))
    viewer = changed(context.recipient_membership, role="viewer", revision=1)
    result = check_redemption_replay(
        **(args | {"context": changed(context, recipient_membership=viewer.model_dump())})
    )
    assert result is not None and result.membership.role == "viewer"


def test_pending_expiry_is_distinct_from_bounded_accepted_metadata_retry() -> None:
    expired = value(InvitationRecord, expires_at=1021)
    assert invitation_view(expired, now=1021).state == "expired"
    with denied("not_found"):
        validate_invitation_redemption(**redeem_args(before=expired, now=1021))
    accepted = changed(
        expired, state="accepted", revision=1, accepted_principal_id="recipient-1", resolved_at=1020
    )
    assert check_redemption_replay(**replay_args(record=accepted, now=1021)) is not None
    with denied("not_found"):
        check_redemption_replay(
            **replay_args(
                record=accepted,
                now=1021,
                invitation_policy=value(InvitationPolicy, retry_window_seconds=1),
            )
        )


def test_same_redemption_key_with_different_valid_token_conflicts() -> None:
    request = value(
        RedeemInvitationRequest,
        token=base64.urlsafe_b64encode(b"x" * 32).decode("ascii").rstrip("="),
    )
    other = changed(
        replay_args()["record"],
        invitation_id="invite-2",
        token_sha256=invitation_token_sha256(request.token),
    )
    with denied("idempotency_conflict", 409):
        check_redemption_replay(**replay_args(record=other, request=request))


def test_a_second_principal_cannot_replay_or_reconsume_first_principals_invite() -> None:
    context = value(RedemptionContext)
    identity = context.recipient_identity.model_dump(mode="json")
    identity["principal"]["principal_id"] = "recipient-2"
    actor = context.actor.model_dump(mode="json")
    actor["session"]["principal_id"] = "recipient-2"
    current = changed(context, actor=actor, recipient_identity=identity)
    second_member = changed(value(RedemptionResult).membership, principal_id="recipient-2")
    validate_invitation_redemption(
        **redeem_args(
            context=current,
            after=value(
                InvitationRecord,
                state="accepted",
                revision=1,
                accepted_principal_id="recipient-2",
                resolved_at=1020,
            ),
            resulting_member=second_member,
        )
    )
    with denied("not_found"):
        validate_invitation_redemption(
            **redeem_args(context=current, before=redeem_args()["after"])
        )


def test_tenant_namespace_includes_explicit_null_and_current_mapping() -> None:
    base = value(RedemptionContext)
    for identity_tenant, assertion_tenant in [
        ("tenant-a", None),
        (None, "tenant-a"),
        ("tenant-a", "tenant-a"),
    ]:
        context = changed(
            base,
            recipient_identity=base.recipient_identity.model_dump()
            | {"tenant_id": identity_tenant},
            email_assertion=base.email_assertion.model_dump() | {"tenant_id": assertion_tenant},
        )
        with denied("not_found"):
            validate_invitation_redemption(**redeem_args(context=context))
    configured = value(DeploymentSessionPolicy)
    providers = [p.model_dump(mode="json") for p in configured.providers]
    providers[0]["tenant_id"] = "tenant-a"
    configured = changed(configured, providers=providers)
    with denied("not_found"):
        validate_invitation_redemption(**redeem_args(session_policy=configured))
    context = changed(
        base,
        recipient_identity=base.recipient_identity.model_dump() | {"tenant_id": "tenant-a"},
        email_assertion=base.email_assertion.model_dump() | {"tenant_id": "tenant-a"},
    )
    validate_invitation_redemption(**redeem_args(session_policy=configured, context=context))


@pytest.mark.parametrize(
    "patch",
    [
        {"audience": "other-project"},
        {"upstream_provider": None},
    ],
)
def test_email_assertion_cannot_skip_provider_audience_or_upstream_policy(
    patch: dict[str, Any],
) -> None:
    with denied("not_found"):
        validate_invitation_redemption(
            **redeem_args(
                context=recipient_context(
                    email_assertion=value(VerifiedEmailAssertion, **patch).model_dump(mode="json")
                )
            )
        )


def test_restoring_owner_does_not_revive_old_invitation_grant() -> None:
    context = value(RedemptionContext)
    for role, revision in [("researcher", 5), ("owner", 6)]:
        current = changed(
            context,
            inviter_membership=context.inviter_membership.model_dump()
            | {
                "role": role,
                "revision": revision,
            },
        )
        with denied("not_found"):
            validate_invitation_redemption(**redeem_args(context=current))
    replay = replay_args()
    current = replay["context"]
    with denied("not_found"):
        check_redemption_replay(
            **(
                replay
                | {
                    "context": changed(
                        current,
                        inviter_membership=current.inviter_membership.model_dump()
                        | {"revision": 6},
                    )
                }
            )
        )


def test_invalid_secret_errors_do_not_include_raw_token_in_text_or_safe_details() -> None:
    raw = "A" * 43 + "!"
    with pytest.raises(ValidationError) as error:
        value(RedeemInvitationRequest, token=raw)
    assert raw not in str(error.value)
    assert raw not in str(error.value.errors(include_input=False, include_context=False))


def test_http_exposes_plaintext_only_on_fresh_issue_and_never_in_urls() -> None:
    api = json.loads((ROOT / "contracts/invitation.openapi.json").read_text())
    assert len(api["paths"]) == 3
    for path, methods in api["paths"].items():
        assert "token" not in path and "email" not in path
        for method, operation in methods.items():
            expected: dict[str, list[str]] = {"sessionCookie": []}
            if method == "post":
                expected["csrfHeader"] = []
            assert operation["security"] == [expected]
            assert all(
                p["name"] not in {"token", "recipient_email"} for p in operation["parameters"]
            )
            assert operation["x-response-headers"]["Cache-Control"] == "no-store"
            assert "429" in operation["responses"]
            if operation["operationId"] == "issueInvitation":
                responses = operation["responses"]
                assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
                    "/InvitationView"
                )
                assert responses["201"]["content"]["application/json"]["schema"]["$ref"].endswith(
                    "/InvitationIssued"
                )
            else:
                assert "201" not in operation["responses"]
