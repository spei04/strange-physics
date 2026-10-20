from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.linking_contracts import (
    LINK_MODELS,
    PUBLIC_MODELS,
    IdentityAssociation,
    IdentityNamespace,
    LinkActor,
    LinkAudit,
    LinkChallenge,
    LinkClaimConsumption,
    LinkCommitRequest,
    LinkError,
    LinkExchangeRequest,
    LinkPolicy,
    LinkReceipt,
    LinkResult,
    LinkStartRequest,
    LinkStatus,
    identity_namespace,
    link_claim_retain_until,
    link_status,
    linking_json_schema,
    replay_link_commit,
    validate_link_binding,
    validate_link_callback,
    validate_link_commit,
    validate_link_proof,
    validate_link_start,
    validate_link_transition,
    validate_link_verification,
)
from strange_physics.session_contracts import (
    DeploymentSessionPolicy,
    LoginTransaction,
    OIDCCallbackEvidence,
    ProofClaimOwner,
    TrustedIdentityProof,
    proof_claim_key,
    validate_proof,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/linking.examples.json").read_text())
SESSION = json.loads((ROOT / "contracts/session.examples.json").read_text())["valid"]
MODELS = {m.__name__: m for m in LINK_MODELS}


def value[T: Message](model: type[T], **changes: Any) -> T:
    data = copy.deepcopy((SESSION | FIXTURES["valid"])[model.__name__])
    return model.model_validate_json(json.dumps(data | changes))


def changed[T: Message](model: T, **changes: Any) -> T:
    return type(model).model_validate_json(json.dumps(model.model_dump(mode="json") | changes))


def claim(purpose: str = "link_identity", transaction_id: str = "link-1") -> ProofClaimOwner:
    return ProofClaimOwner.model_validate_json(
        json.dumps({"purpose": purpose, "transaction_id": transaction_id})
    )


def bound(**changes: Any) -> dict[str, Any]:
    return (
        dict(
            session_policy=value(DeploymentSessionPolicy),
            link_policy=value(LinkPolicy),
            context=value(LinkActor),
            challenge=value(LinkChallenge),
            now=1025,
        )
        | changes
    )


def proof_args(**changes: Any) -> dict[str, Any]:
    challenge = value(LinkChallenge)
    return bound() | dict(proof=challenge.proof, claimed_by=claim()) | changes


def commit_args(**changes: Any) -> dict[str, Any]:
    challenge = value(LinkChallenge)
    proof = challenge.proof
    assert proof is not None
    return (
        dict(
            session_policy=value(DeploymentSessionPolicy),
            link_policy=value(LinkPolicy),
            context=value(LinkActor),
            before=challenge,
            after=changed(challenge, state="committed", revision=3, consumed_at=1025),
            request=value(LinkCommitRequest),
            existing=None,
            associated=IdentityAssociation(
                identity=identity_namespace(proof),
                principal_id="principal-1",
                active=True,
                revision=0,
                linked_at=1025,
            ),
            claimed_by=claim(),
            consumption=value(LinkClaimConsumption),
            receipt=value(LinkReceipt),
            audit=value(LinkAudit),
            now=1025,
        )
        | changes
    )


def replay_args(**changes: Any) -> dict[str, Any]:
    commit = commit_args()
    return (
        dict(
            session_policy=commit["session_policy"],
            link_policy=commit["link_policy"],
            context=commit["context"],
            challenge=commit["after"],
            request=commit["request"],
            associated=commit["associated"],
            consumption=commit["consumption"],
            receipt=commit["receipt"],
            audit=commit["audit"],
            now=1026,
        )
        | changes
    )


def denied(code: str, status: int = 409) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda error: error.status == status)


@pytest.mark.parametrize("model", LINK_MODELS)
def test_all_synthetic_shapes(model: type[Message]) -> None:
    value(model)


@pytest.mark.parametrize("case", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_shared_negative_fixtures(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        value(MODELS[case["model"]], **{case["field"]: case["value"]})


def test_schema_and_public_boundary_match() -> None:
    schema = linking_json_schema()
    assert schema == json.loads((ROOT / "contracts/linking.schema.json").read_text())
    assert schema["x-public-models"] == [m.__name__ for m in PUBLIC_MODELS]
    for name in ("LinkActor", "LinkChallenge", "LinkReceipt", "LinkAudit", "IdentityNamespace"):
        assert name not in schema["x-public-models"]
    request = value(LinkExchangeRequest)
    token = FIXTURES["valid"]["LinkExchangeRequest"]["id_token"]
    assert token not in repr(request) and token not in request.model_dump_json()


def test_complete_association_has_no_new_principal_session_or_grants() -> None:
    context = value(LinkActor)
    initial = context.model_dump_json()
    pending = value(LinkChallenge, state="pending", proof=None, revision=0)
    validate_link_start(
        value(DeploymentSessionPolicy),
        value(LinkPolicy),
        context,
        value(LinkStartRequest),
        pending,
        now=1020,
    )
    verifying = changed(pending, state="verifying", revision=1)
    validate_link_transition(pending, verifying, expected_revision=0)
    verified = value(LinkChallenge)
    validate_link_proof(**proof_args(challenge=verifying, claimed_by=None))
    validate_link_verification(
        value(DeploymentSessionPolicy),
        value(LinkPolicy),
        context,
        verifying,
        verified,
        now=1025,
        claimed_by=claim(),
    )
    validate_link_commit(**commit_args())
    assert replay_link_commit(**replay_args()) == value(LinkResult)
    assert context.model_dump_json() == initial


@pytest.mark.parametrize(
    "field",
    [
        "principal_id",
        "session_id",
        "generation",
        "authenticated_at",
        "link_policy_id",
        "session_policy_id",
        "primary_revision",
        "browser_binding_sha256",
    ],
)
def test_challenge_is_owned_by_exact_current_primary_and_policy(field: str) -> None:
    original = value(LinkChallenge)
    previous = getattr(original, field)
    replacement = (
        previous + 1 if type(previous) is int else "9" * 64 if "sha256" in field else "other"
    )
    data = original.model_dump(mode="json") | {field: replacement}
    # For browser binding, retained proof must itself remain structurally challenge-bound.
    if field == "browser_binding_sha256":
        data["proof"]["browser_binding_sha256"] = replacement
    with denied("not_found", 404):
        validate_link_binding(
            **bound(challenge=LinkChallenge.model_validate_json(json.dumps(data))), mutation=True
        )


@pytest.mark.parametrize(
    "change",
    [
        "revoked",
        "principal_disabled",
        "primary_disabled",
        "primary_other_owner",
        "primary_identity_changed",
        "session_generation",
        "actual_authentication",
        "principal_kind",
        "csrf",
        "origin",
        "bearer",
        "cookie",
        "browser_binding",
    ],
)
def test_current_primary_authority_precedes_receipt_replay(change: str) -> None:
    data = value(LinkActor).model_dump(mode="json")
    if change == "revoked":
        data["actor"]["session"]["revoked"] = True
    elif change == "principal_disabled":
        data["principal"]["active"] = False
    elif change == "primary_disabled":
        data["primary"]["active"] = False
    elif change == "primary_other_owner":
        data["primary"]["principal_id"] = "other"
    elif change == "primary_identity_changed":
        data["primary"]["identity"]["subject"] = "other"
    elif change == "session_generation":
        data["actor"]["session"]["generation"] = 1
        data["actor"]["credential"]["generation"] = 1
        data["authenticated_identity"]["generation"] = 1
    elif change == "actual_authentication":
        data["actor"]["session"]["authenticated_at"] = 0
    elif change == "principal_kind":
        data["principal"]["kind"] = "service"
        with pytest.raises(ValidationError):
            LinkActor.model_validate_json(json.dumps(data))
        return
    elif change == "csrf":
        data["actor"]["context"]["csrf_matches"] = False
    elif change == "origin":
        data["actor"]["context"]["origin"] = "https://evil.example"
    elif change == "bearer":
        data["actor"]["context"]["has_bearer"] = True
    elif change == "cookie":
        data["actor"]["context"]["has_session_cookie"] = False
    else:
        data["actor"]["context"]["browser_binding_sha256"] = None
    expected = {
        "session_generation": ("not_found", 404),
        "csrf": ("forbidden", 403),
        "origin": ("forbidden", 403),
        "bearer": ("ambiguous_credentials", 400),
    }.get(change, ("unauthenticated", 401))
    with denied(*expected):
        replay_link_commit(
            **replay_args(
                context=LinkActor.model_validate_json(json.dumps(data)),
                receipt=None,
            )
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"purpose": "login"},
        {"transaction_id": "other"},
        {"provider_id": "other"},
        {"browser_binding_sha256": "9" * 64},
        {"issuer": "https://other.example"},
        {"audience": "other"},
        {"tenant_id": "other"},
        {"upstream_provider": "github.com", "flow": "oidc_code"},
        {"subject": "primary-subject"},
        {"auth_time": 1019},
        {"auth_time": 1020},
        {"auth_time": 1026, "issued_at": 1026},
        {"issued_at": 1020},
        {"verified_at": 1020},
        {"expires_at": 1025},
    ],
)
def test_secondary_requires_separate_challenge_bound_actual_fresh_auth(
    changes: dict[str, Any],
) -> None:
    proof = value(LinkChallenge).proof
    assert proof is not None
    with denied("proof_rejected", 401):
        validate_link_proof(
            **proof_args(
                challenge=value(LinkChallenge, state="verifying", proof=None),
                proof=changed(proof, **changes),
                claimed_by=None,
            )
        )


def test_clock_skew_and_recent_verification_do_not_make_old_authentication_fresh() -> None:
    proof = value(LinkChallenge).proof
    assert proof is not None
    for auth_time in (990, 1020):
        with denied("proof_rejected", 401):
            validate_link_proof(
                **proof_args(
                    challenge=value(LinkChallenge, state="verifying", proof=None),
                    proof=changed(proof, auth_time=auth_time, issued_at=1025, verified_at=1025),
                    session_policy=value(DeploymentSessionPolicy, clock_skew_seconds=300),
                    claimed_by=None,
                )
            )


def test_global_digest_claim_blocks_equal_ids_and_provider_aliases_in_both_directions() -> None:
    configured = value(DeploymentSessionPolicy)
    data = configured.model_dump(mode="json")
    data["providers"].append(data["providers"][0] | {"provider_id": "alias"})
    configured = DeploymentSessionPolicy.model_validate_json(json.dumps(data))
    linking_data = value(LinkPolicy).model_dump(mode="json")
    linking_data["providers"].append({"provider_id": "alias", "callback_uri": None})
    linking = LinkPolicy.model_validate_json(json.dumps(linking_data))
    for alias in ("managed", "alias"):
        challenge = value(
            LinkChallenge, challenge_id="login-1", provider_id=alias, state="verifying", proof=None
        )
        original_proof = value(LinkChallenge).proof
        assert original_proof is not None
        link_proof = changed(original_proof, transaction_id="login-1", provider_id=alias)
        login_proof = value(TrustedIdentityProof, proof_sha256=link_proof.proof_sha256)
        login = value(LoginTransaction, state="verifying", proof=None)
        assert proof_claim_key(link_proof) == proof_claim_key(login_proof)
        with denied("proof_rejected", 401):
            validate_link_proof(
                **proof_args(
                    session_policy=configured,
                    link_policy=linking,
                    challenge=challenge,
                    proof=link_proof,
                    claimed_by=claim("login", "login-1"),
                )
            )
        with denied("proof_rejected", 401):
            validate_proof(
                configured,
                login,
                login_proof,
                now=1025,
                claimed_by=claim("link_identity", "login-1"),
            )
        # Unclaimed wrong-purpose evidence also fails; purpose is not just a lookup partition.
        with denied("proof_rejected", 401):
            validate_proof(
                configured,
                login,
                changed(login_proof, purpose="link_identity"),
                now=1025,
                claimed_by=None,
            )


def test_verified_state_requires_global_owned_claim_and_immutable_evidence() -> None:
    with denied("proof_rejected", 401):
        validate_link_proof(**proof_args(claimed_by=None))
    proof = value(LinkChallenge).proof
    assert proof is not None
    with denied("proof_rejected", 401):
        validate_link_proof(**proof_args(proof=changed(proof, proof_sha256="8" * 64)))
    assert (
        link_claim_retain_until(
            value(DeploymentSessionPolicy), value(LinkPolicy), value(LinkChallenge)
        )
        == 4620
    )


@pytest.mark.parametrize(
    "principal,active",
    [("other", True), ("other", False), ("principal-1", True), ("principal-1", False)],
)
def test_any_preexisting_identity_ownership_conflicts_without_disclosing_owner(
    principal: str, active: bool
) -> None:
    existing = changed(commit_args()["associated"], principal_id=principal, active=active)
    with denied("link_conflict"):
        validate_link_commit(**commit_args(existing=existing))


def test_namespace_excludes_alias_email_and_distinguishes_tenant_and_null() -> None:
    proof = value(LinkChallenge).proof
    assert proof is not None
    first = identity_namespace(proof)
    assert identity_namespace(changed(proof, provider_id="alias", audience="other")) == first
    assert identity_namespace(changed(proof, tenant_id="tenant-1")) != first
    assert identity_namespace(changed(proof, issuer="https://other.example")) != first
    assert set(IdentityNamespace.model_fields) == {"issuer", "tenant_id", "subject"}
    data = first.model_dump(mode="json")
    del data["tenant_id"]
    with pytest.raises(ValidationError):
        IdentityNamespace.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field", ["associated", "consumption", "receipt", "audit"])
def test_atomic_commit_proposal_rejects_partial_or_mismatched_outputs(field: str) -> None:
    args = commit_args()
    output = args[field]
    if field == "associated":
        args[field] = changed(output, principal_id="allocated-other")
    elif field == "consumption":
        args[field] = changed(output, owner=claim("login", "link-1").model_dump(mode="json"))
    elif field == "receipt":
        args[field] = changed(output, challenge_id="other")
    else:
        args[field] = changed(output, proof_sha256="8" * 64)
    with denied("link_conflict"):
        validate_link_commit(**args)


def test_challenge_cas_allows_only_one_commit_and_never_reopens_recovery() -> None:
    args = commit_args()
    with denied("link_conflict"):
        validate_link_commit(**commit_args(request=value(LinkCommitRequest, expected_revision=1)))
    with denied("recovery_required"):
        validate_link_commit(**commit_args(before=args["after"]))
    recovery = value(LinkChallenge, state="recovery_required")
    for state in ("verified", "committed", "pending"):
        data = recovery.model_dump(mode="json") | {"state": state, "revision": 3}
        if state == "committed":
            data["consumed_at"] = 1025
        if state == "pending":
            data["proof"] = None
        with denied("link_conflict"):
            validate_link_transition(
                recovery, LinkChallenge.model_validate_json(json.dumps(data)), expected_revision=2
            )
    assert link_status(**bound(challenge=recovery)).next_action == "reconcile"


@pytest.mark.parametrize("field", ["associated", "consumption", "receipt", "audit"])
def test_unknown_or_partial_commit_never_replays_success(field: str) -> None:
    with denied("recovery_required"):
        replay_link_commit(**replay_args(**{field: None}))


def test_replay_needs_exact_receipt_current_mapping_and_original_expected_revision() -> None:
    for args in (
        replay_args(request=value(LinkCommitRequest, expected_revision=3)),
        replay_args(associated=changed(commit_args()["associated"], active=False)),
        replay_args(consumption=changed(value(LinkClaimConsumption), retain_until=4621)),
        replay_args(receipt=changed(value(LinkReceipt), proof_sha256="8" * 64)),
        replay_args(audit=changed(value(LinkAudit), occurred_at=1024)),
    ):
        with denied("link_conflict"):
            replay_link_commit(**args)


def test_expiry_and_missing_policy_do_not_supply_defaults() -> None:
    for field in ("session_policy", "link_policy"):
        with denied("policy_unavailable", 503):
            validate_link_binding(**bound(**{field: None}), mutation=True)
    expired = bound(
        now=1080,
        challenge=value(LinkChallenge, expires_at=1080),
        link_policy=value(LinkPolicy, challenge_ttl_seconds=60),
    )
    with denied("link_expired", 401):
        validate_link_binding(**expired, mutation=True)
    assert link_status(**expired).next_action == "start_new_challenge"


def test_google_identity_platform_tenant_profile_cannot_be_enabled_by_policy() -> None:
    policy = value(DeploymentSessionPolicy).model_dump(mode="json")
    policy["providers"][0]["tenant_id"] = "tenant-1"
    configured = DeploymentSessionPolicy.model_validate_json(json.dumps(policy))
    # An independently valid OIDC primary isolates the blocked secondary profile.
    oidc = next(provider for provider in configured.providers if provider.provider_id == "oidc")
    data = value(LinkActor).model_dump(mode="json")
    identity = {"issuer": oidc.issuer, "tenant_id": oidc.tenant_id, "subject": "primary-subject"}
    data["primary"]["identity"] = identity
    data["authenticated_identity"]["identity"] = identity
    context = LinkActor.model_validate_json(json.dumps(data))
    challenge = value(LinkChallenge, primary_identity=identity)
    with denied("unsupported_flow", 422):
        validate_link_binding(
            **bound(session_policy=configured, context=context, challenge=challenge), mutation=True
        )
    # A managed-tenant primary is also blocked before a valid secondary OIDC flow.
    identity = FIXTURES["valid"]["IdentityNamespace"] | {"tenant_id": "tenant-1"}
    data["primary"]["identity"] = identity
    data["authenticated_identity"]["identity"] = identity
    context = LinkActor.model_validate_json(json.dumps(data))
    with denied("unsupported_flow", 422):
        validate_link_binding(**bound(session_policy=configured, context=context), mutation=True)


def oidc_args() -> dict[str, Any]:
    policy = value(DeploymentSessionPolicy)
    provider = next(p for p in policy.providers if p.provider_id == "oidc")
    original = value(LinkChallenge).proof
    assert original is not None
    proof = changed(
        original,
        provider_id="oidc",
        flow="oidc_code",
        issuer=provider.issuer,
        audience=provider.audience,
        tenant_id=provider.tenant_id,
        upstream_provider=None,
    )
    challenge = value(LinkChallenge, provider_id="oidc", proof=proof.model_dump(mode="json"))
    evidence = value(
        OIDCCallbackEvidence, callback_uri="https://app.example/v1/identity-links/oidc/callback"
    )
    return proof_args(challenge=challenge, proof=proof, oidc_evidence=evidence)


def test_oidc_is_separate_exact_callback_and_cannot_create_a_login() -> None:
    args = oidc_args()
    validate_link_proof(**args)
    for field, replacement in (
        ("callback_uri", "https://app.example/v1/auth/oidc/callback"),
        ("state_matches", False),
        ("nonce_matches", False),
        ("pkce_s256_verified", False),
    ):
        with denied("proof_rejected", 401):
            validate_link_proof(
                **(args | {"oidc_evidence": changed(args["oidc_evidence"], **{field: replacement})})
            )
    with denied("proof_rejected", 401):
        validate_link_proof(**(args | {"oidc_evidence": None}))
    # A managed proof never receives the callback CSRF exception.
    with denied("proof_rejected", 401):
        validate_link_callback(**bound(), evidence=args["oidc_evidence"])


def test_http_is_cookie_only_and_never_exposes_internal_ownership_or_session_creation() -> None:
    api = json.loads((ROOT / "contracts/linking.openapi.json").read_text())
    assert len(api["paths"]) == 5
    for path, routes in api["paths"].items():
        for method, operation in routes.items():
            assert operation["security"] == [
                {"sessionCookie": [], **({"csrfHeader": []} if method == "post" else {})}
            ]
            assert operation["x-response-headers"]["Cache-Control"] == "no-store"
            assert "Set-Cookie" not in json.dumps(operation)
            assert "x-implementation-status" in operation
            assert not {"LinkActor", "LinkChallenge", "LinkReceipt", "LinkAudit"} & set(
                json.dumps(operation).split('"')
            )
            if method == "post":
                assert any(p["name"] == "Origin" for p in operation["parameters"])
            if "{challenge_id}" in path:
                assert any(p["name"] == "challenge_id" for p in operation["parameters"])
    serialized = json.dumps(api)
    assert "bearer" not in json.dumps(api["components"]["securitySchemes"]).lower()
    assert "SessionBootstrap" not in serialized and "LoginTransaction" not in serialized


def test_primary_authentication_age_boundary_is_exact_on_reads_and_commit() -> None:
    link_status(**bound(now=1109))
    with denied("reauthentication_required", 401):
        link_status(**bound(now=1110))
    with denied("reauthentication_required", 401):
        replay_link_commit(**replay_args(now=1110))


def test_oidc_commit_and_retry_preserve_the_existing_primary_session() -> None:
    verified = oidc_args()
    challenge = verified["challenge"]
    proof = verified["proof"]
    identity = identity_namespace(proof)
    args = commit_args(
        before=challenge,
        after=changed(challenge, state="committed", revision=3, consumed_at=1025),
        associated=changed(commit_args()["associated"], identity=identity.model_dump(mode="json")),
        receipt=changed(value(LinkReceipt), identity=identity.model_dump(mode="json")),
        audit=changed(value(LinkAudit), identity=identity.model_dump(mode="json")),
        oidc_evidence=verified["oidc_evidence"],
    )
    validate_link_commit(**args)
    assert replay_link_commit(
        **replay_args(
            challenge=args["after"],
            associated=args["associated"],
            receipt=args["receipt"],
            audit=args["audit"],
        )
    ) == value(LinkResult)


def test_verifying_unknown_exchange_cannot_restart_or_reuse_the_challenge() -> None:
    before = value(LinkChallenge, state="verifying", proof=None, revision=1)
    after = changed(before, state="restart_required", revision=2)
    with denied("link_conflict"):
        validate_link_transition(before, after, expected_revision=1)
    recovery = changed(before, state="recovery_required", revision=2)
    validate_link_transition(before, recovery, expected_revision=1)
    assert link_status(**bound(challenge=recovery)).next_action == "reconcile"


def test_public_verified_status_supplies_the_commit_revision() -> None:
    # A client uses only the declared public response, never internal transition counts.
    observed = LinkStatus.model_validate_json(link_status(**bound()).model_dump_json())
    assert observed.state == "verified" and observed.next_action == "commit"
    request = LinkCommitRequest(expected_revision=observed.revision)
    validate_link_commit(**commit_args(request=request))
    assert replay_link_commit(**replay_args(request=request)) == value(LinkResult)
    completed = link_status(**bound(challenge=commit_args()["after"]))
    assert completed.revision == observed.revision + 1 and completed.next_action == "done"


@pytest.mark.parametrize("change", ["disabled_principal", "disabled_primary", "reassigned_primary"])
def test_stale_invalid_primary_never_receives_freshness_advice(change: str) -> None:
    data = value(LinkActor).model_dump(mode="json")
    if change == "disabled_principal":
        data["principal"]["active"] = False
    elif change == "disabled_primary":
        data["primary"]["active"] = False
    else:
        data["primary"]["principal_id"] = "another-owner"
    context = LinkActor.model_validate_json(json.dumps(data))
    # Actual authentication reaches its age limit at 1110, but invalid authority wins.
    with denied("unauthenticated", 401):
        replay_link_commit(**replay_args(context=context, now=1110, receipt=None))
    with denied("unauthenticated", 401):
        link_status(**bound(context=context, now=1110))
    data["actor"]["context"]["csrf_matches"] = False
    with denied("forbidden", 403):
        replay_link_commit(
            **replay_args(
                context=LinkActor.model_validate_json(json.dumps(data)), now=1110, receipt=None
            )
        )


def test_trusted_proof_keeps_documentation_after_required_purpose_amendment() -> None:
    assert TrustedIdentityProof.__doc__ is not None
    assert TrustedIdentityProof.model_json_schema().get("description")


def test_link_callback_cannot_collide_with_another_providers_login_callback() -> None:
    args = oidc_args()
    data = args["session_policy"].model_dump(mode="json")
    oidc = next(provider for provider in data["providers"] if provider["provider_id"] == "oidc")
    data["providers"].append(
        oidc | {"provider_id": "other-oidc", "callback_uri": args["oidc_evidence"].callback_uri}
    )
    configured = DeploymentSessionPolicy.model_validate_json(json.dumps(data))
    with denied("unsupported_flow", 422):
        validate_link_proof(**(args | {"session_policy": configured}))


def test_rate_limit_has_explicit_safe_code_schema_and_retry_after() -> None:
    fixture = FIXTURES["rate_limit"]
    error = LinkError.model_validate_json(json.dumps(fixture["body"]))
    assert fixture["status"] == 429 and error.code == "rate_limited"
    assert int(fixture["headers"]["Retry-After"]) > 0
    assert (
        "rate_limited" in linking_json_schema()["$defs"]["LinkError"]["properties"]["code"]["enum"]
    )
    api = json.loads((ROOT / "contracts/linking.openapi.json").read_text())
    for routes in api["paths"].values():
        for operation in routes.values():
            response = operation["responses"]["429"]
            assert "Retry-After" in response["headers"]
            assert response["content"]["application/json"]["schema"]["allOf"][1] == {
                "properties": {"code": {"const": "rate_limited"}}
            }
