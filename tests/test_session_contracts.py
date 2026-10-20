from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.session_contracts import (
    PUBLIC_MODELS,
    RESPONSE_HEADERS,
    SESSION_MODELS,
    BrowserContext,
    DeploymentSessionPolicy,
    LoginStartRequest,
    LoginTransaction,
    OIDCCallbackEvidence,
    RenewalRequest,
    SessionCredential,
    SessionRecord,
    TrustedIdentityProof,
    bootstrap,
    login_options,
    login_recovery,
    login_status,
    proof_claim_key,
    proof_claim_retain_until,
    session_json_schema,
    validate_login_binding,
    validate_login_completion,
    validate_login_start,
    validate_login_transition,
    validate_logout,
    validate_oidc_callback,
    validate_proof,
    validate_renewal,
    validate_session,
    validate_session_update,
    workspace_session_error,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/session.examples.json").read_text())
MODELS = {model.__name__: model for model in SESSION_MODELS}


def value[T: Message](model: type[T], **changes: Any) -> T:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    data.update(changes)
    return model.model_validate_json(json.dumps(data))


def policy() -> DeploymentSessionPolicy:
    return value(DeploymentSessionPolicy)


def browser(**changes: Any) -> BrowserContext:
    return value(BrowserContext, **changes)


def session_browser(**changes: Any) -> BrowserContext:
    return browser(has_session_cookie=True, csrf_scope="session", **changes)


@pytest.mark.parametrize("model", SESSION_MODELS)
def test_all_synthetic_shapes_parse(model: type[Message]) -> None:
    value(model)


@pytest.mark.parametrize("case", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_shared_negative_fixtures(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        value(MODELS[case["model"]], **{case["field"]: case["value"]})


def test_schema_exactly_tracks_models_and_public_boundary() -> None:
    stored = json.loads((ROOT / "contracts/session.schema.json").read_text())
    assert stored == session_json_schema()
    assert stored["x-public-models"] == [model.__name__ for model in PUBLIC_MODELS]
    assert "TrustedIdentityProof" not in stored["x-public-models"]
    assert "principal_id" not in stored["$defs"]["TrustedIdentityProof"]["properties"]


def test_secret_request_fields_do_not_appear_in_repr_or_default_dump() -> None:
    for name, field in [
        ("BrokerExchangeRequest", "id_token"),
        ("OIDCCallbackRequest", "code"),
        ("CSRFResponse", "token"),
    ]:
        parsed = value(MODELS[name])
        secret = FIXTURES["valid"][name][field]
        assert secret not in repr(parsed)
        assert secret not in parsed.model_dump_json()


def test_policy_required_and_all_security_values_explicit() -> None:
    with pytest.raises(ContractViolation, match="policy_unavailable"):
        validate_login_start(None, value(LoginStartRequest), browser())
    for field in policy().model_fields_set - {"schema_version"}:
        data = policy().model_dump(mode="json")
        del data[field]
        with pytest.raises(ValidationError):
            DeploymentSessionPolicy.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "target",
    [
        "https://app.example.evil/workspace",
        "https://app.example/workspace/",
        "https://app.example/workspace?next=https://evil.example",
        "https://APP.example/workspace",
        "https://app.example:443/workspace",
        "https://app.example/%77orkspace",
        "https://app.example/../workspace",
    ],
)
def test_return_uri_requires_exact_match(target: str) -> None:
    request = value(LoginStartRequest, return_uri=target)
    with pytest.raises(ContractViolation, match="invalid_request"):
        validate_login_start(policy(), request, browser())


@pytest.mark.parametrize(
    "changes",
    [
        {"origin": None},
        {"origin": "https://evil.example"},
        {"origin": "https://app.example.evil"},
        {"csrf_matches": False},
        {"csrf_scope": "session"},
        {"has_session_cookie": True, "has_bearer": True},
        {"has_bearer": True},
        {"browser_binding_sha256": None},
    ],
)
def test_login_requires_bound_preauth_csrf_and_rejects_ambiguous_credentials(
    changes: dict[str, Any],
) -> None:
    with pytest.raises(ContractViolation):
        validate_login_start(policy(), value(LoginStartRequest), browser(**changes))


def test_fresh_login_allows_an_invalid_old_cookie_but_never_uses_it_as_identity() -> None:
    assert (
        validate_login_start(
            policy(), value(LoginStartRequest), browser(has_session_cookie=True)
        ).provider_id
        == "managed"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"issuer": "https://evil.example"},
        {"audience": "wrong"},
        {"tenant_id": "wrong"},
        {"provider_id": "oidc"},
        {"transaction_id": "other"},
        {"browser_binding_sha256": "3" * 64},
        {"flow": "oidc_code"},
        {"upstream_provider": None},
        {"auth_time": 800, "issued_at": 1009},
        {"auth_time": 1011},
        {"expires_at": 1010},
        {"verified_at": 999},
        {"issued_at": 1006},
    ],
)
def test_identity_binding_expiry_and_auth_time_reject_unsafe_proofs(
    changes: dict[str, Any],
) -> None:
    transaction = value(LoginTransaction, state="verifying", proof=None)
    with pytest.raises(ContractViolation, match="proof_rejected"):
        validate_proof(
            policy(),
            transaction,
            value(TrustedIdentityProof, **changes),
            now=1010,
            claimed_by_transaction=None,
        )


def test_replayed_proof_other_transaction_and_replacement_evidence_are_rejected() -> None:
    transaction = value(LoginTransaction)
    proof = value(TrustedIdentityProof)
    validate_proof(policy(), transaction, proof, now=1010, claimed_by_transaction="login-1")
    for claimed, supplied in [
        ("other", proof),
        ("login-1", value(TrustedIdentityProof, proof_sha256="9" * 64)),
    ]:
        with pytest.raises(ContractViolation, match="proof_rejected"):
            validate_proof(
                policy(), transaction, supplied, now=1010, claimed_by_transaction=claimed
            )


@pytest.mark.parametrize(
    "changes,now",
    [
        ({"policy_id": "other"}, 1010),
        ({"expires_at": 1181}, 1010),
        ({}, 1180),
        ({}, 999),
        ({"return_uri": "https://app.example/other"}, 1010),
    ],
)
def test_login_transaction_exact_policy_and_expiry(changes: dict[str, Any], now: int) -> None:
    with pytest.raises(ContractViolation):
        validate_login_binding(policy(), value(LoginTransaction, **changes), browser(), now=now)


def oidc_transaction() -> LoginTransaction:
    return value(LoginTransaction, provider_id="oidc", state="verifying", proof=None)


def test_oidc_callback_is_narrow_get_query_profile_with_all_adapter_checks() -> None:
    transaction = oidc_transaction()
    context = browser(origin="https://idp.example", csrf_matches=False, csrf_scope=None)
    evidence = value(OIDCCallbackEvidence)
    validate_oidc_callback(policy(), transaction, context, evidence, now=1010)
    for field in ["state_matches", "nonce_matches", "pkce_s256_verified"]:
        with pytest.raises(ContractViolation, match="proof_rejected"):
            validate_oidc_callback(
                policy(),
                transaction,
                context,
                value(OIDCCallbackEvidence, **{field: False}),
                now=1010,
            )
    with pytest.raises(ContractViolation):
        validate_oidc_callback(
            policy(),
            transaction,
            context,
            value(OIDCCallbackEvidence, callback_uri="https://app.example/other"),
            now=1010,
        )
    with pytest.raises(ContractViolation):
        validate_oidc_callback(policy(), value(LoginTransaction), context, evidence, now=1010)


def test_login_completion_binds_one_session_and_committed_proof_cannot_create_another() -> None:
    before = value(LoginTransaction)
    after = value(LoginTransaction, state="committed", session_id="session-1", revision=3)
    record = value(SessionRecord)
    validate_login_completion(
        policy(),
        before,
        after,
        browser(),
        record,
        principal_id="principal-1",
        now=1010,
        expected_revision=2,
        claimed_by_transaction="login-1",
    )
    with pytest.raises(ContractViolation):
        validate_login_completion(
            policy(),
            after,
            after,
            browser(),
            record,
            principal_id="principal-1",
            now=1010,
            expected_revision=3,
            claimed_by_transaction="login-1",
        )
    for changed in [
        value(LoginTransaction, state="committed", session_id="other", revision=3),
        value(LoginTransaction, state="committed", session_id="session-1", revision=4),
    ]:
        with pytest.raises(ContractViolation, match="login_conflict"):
            validate_login_completion(
                policy(),
                before,
                changed,
                browser(),
                record,
                principal_id="principal-1",
                now=1010,
                expected_revision=2,
                claimed_by_transaction="login-1",
            )


def test_login_recovery_never_replays_an_unknown_exchange_or_consumed_proof() -> None:
    expected = {
        "pending": "verify_once",
        "verifying": "reconcile_or_restart",
        "verified": "commit_same_transaction",
        "committed": "bootstrap_or_login",
        "restart_required": "fresh_login",
    }
    for state, decision in expected.items():
        transaction = value(
            LoginTransaction,
            state=state,
            proof=FIXTURES["valid"]["TrustedIdentityProof"]
            if state in {"verified", "committed"}
            else None,
            session_id="session-1" if state == "committed" else None,
        )
        assert login_recovery(transaction) == decision
        if state in {"committed", "restart_required"}:
            with pytest.raises(ContractViolation):
                validate_login_transition(
                    transaction, value(LoginTransaction), expected_revision=transaction.revision
                )


@pytest.mark.parametrize(
    "changes,now",
    [
        ({"revoked": True}, 1010),
        ({"principal_active": False}, 1010),
        ({"policy_id": "other"}, 1010),
        ({"generation": 1}, 1010),
        ({}, 1310),
        ({}, 4610),
        ({}, 1009),
        ({"absolute_expires_at": 5000}, 1010),
    ],
)
def test_session_requires_current_authority_original_deadline_and_idle_lifetime(
    changes: dict[str, Any],
    now: int,
) -> None:
    with pytest.raises(ContractViolation):
        validate_session(
            policy(), value(SessionRecord, **changes), value(SessionCredential), now=now
        )


def test_safe_bootstrap_and_invalid_cookie_do_not_expose_identity_or_error_details() -> None:
    context = session_browser(origin=None)
    valid = bootstrap(policy(), value(SessionRecord), value(SessionCredential), context, now=1010)
    assert valid.authenticated and valid.principal_id == "principal-1"
    assert set(valid.model_dump()) == {"authenticated", "principal_id", "session"}
    for record in [None, value(SessionRecord, revoked=True)]:
        signed_out = bootstrap(policy(), record, value(SessionCredential), context, now=1010)
        assert signed_out.model_dump() == {
            "authenticated": False,
            "principal_id": None,
            "session": None,
        }
    assert RESPONSE_HEADERS["Cache-Control"] == "no-store"
    assert "Set-Cookie" not in RESPONSE_HEADERS


@pytest.mark.parametrize("mutation", ["renew", "logout"])
@pytest.mark.parametrize(
    "changes",
    [
        {"csrf_matches": False},
        {"csrf_scope": "preauth"},
        {"origin": None},
        {"origin": "https://evil.example"},
        {"has_bearer": True},
    ],
)
def test_cookie_mutations_always_check_origin_csrf_and_credential_ambiguity(
    mutation: str,
    changes: dict[str, Any],
) -> None:
    context_data = (
        FIXTURES["valid"]["BrowserContext"]
        | {
            "has_session_cookie": True,
            "csrf_scope": "session",
        }
        | changes
    )
    context = BrowserContext.model_validate_json(json.dumps(context_data))
    with pytest.raises(ContractViolation):
        if mutation == "renew":
            validate_renewal(
                policy(),
                value(SessionRecord),
                value(SessionCredential),
                value(RenewalRequest),
                context,
                now=1020,
            )
        else:
            validate_logout(
                policy(), value(SessionRecord), value(SessionCredential), context, now=1020
            )


def test_rotation_cas_preserves_absolute_deadline_and_authentication_time() -> None:
    before = value(SessionRecord)
    after = value(SessionRecord, generation=1, last_seen_at=1020)
    validate_session_update(
        policy(),
        before,
        after,
        value(SessionCredential),
        value(RenewalRequest),
        session_browser(),
        now=1020,
    )
    updates: list[dict[str, object]] = [
        {"absolute_expires_at": 4620},
        {"authenticated_at": 1020},
        {"generation": 2},
        {"principal_id": "other"},
    ]
    for changes in updates:
        altered = after.model_dump(mode="json") | changes
        with pytest.raises(ContractViolation, match="session_conflict"):
            validate_session_update(
                policy(),
                before,
                SessionRecord.model_validate_json(json.dumps(altered)),
                value(SessionCredential),
                value(RenewalRequest),
                session_browser(),
                now=1020,
            )
    with pytest.raises(ContractViolation, match="session_conflict"):
        validate_renewal(
            policy(),
            after,
            value(SessionCredential),
            value(RenewalRequest),
            session_browser(),
            now=1020,
        )
    with pytest.raises(ContractViolation, match="unauthenticated"):
        validate_renewal(
            policy(),
            value(SessionRecord, revoked=True, generation=1),
            value(SessionCredential),
            value(RenewalRequest),
            session_browser(),
            now=1020,
        )


def test_stale_logout_only_revokes_its_own_family_without_access_or_cookie_deletion() -> None:
    current = value(SessionRecord, generation=1, last_seen_at=1020)
    stale = value(SessionCredential)
    with pytest.raises(ContractViolation):
        validate_session(policy(), current, stale, now=1020)
    validate_logout(policy(), current, stale, session_browser(), now=1020)
    with pytest.raises(ContractViolation):
        validate_logout(
            policy(),
            current,
            value(SessionCredential, session_id="other"),
            session_browser(),
            now=1020,
        )


def test_http_schema_keeps_trusted_inputs_private_and_run_bearers_exclusive() -> None:
    api = json.loads((ROOT / "contracts/session.openapi.json").read_text())
    assert len(api["paths"]) == 9
    for routes in api["paths"].values():
        for route in routes.values():
            assert route["x-implementation-status"] == "not-implemented"
            assert route["x-response-headers"] == RESPONSE_HEADERS
            assert route["x-allow-cookie-deletion"] is False
    serialized = json.dumps(api)
    assert "TrustedIdentityProof" not in serialized and "SessionRecord" not in serialized
    controls = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    for routes in controls["paths"].values():
        for method, route in routes.items():
            if method not in {"get", "post", "put"}:
                continue
            if {"runBearer": []} in route.get("security", []):
                assert {"sessionCookie": []} not in route["security"]
            if {"workspaceBearer": []} in route.get("security", []):
                assert any("sessionCookie" in item for item in route["security"])
                assert route["x-reject-mixed-credentials"] is True


def test_public_login_options_and_outcome_never_return_trusted_evidence() -> None:
    assert login_options(policy()).model_dump(mode="json") == {
        "providers": [
            {"provider_id": "managed", "flow": "managed_broker"},
            {"provider_id": "oidc", "flow": "oidc_code"},
        ],
    }
    transaction = value(LoginTransaction)
    outcome = login_status(policy(), transaction, browser(origin=None), now=1010)
    assert set(outcome.model_dump()) == {"transaction_id", "state", "expired", "next_action"}
    assert outcome.next_action == "commit_same_transaction"
    assert login_status(policy(), transaction, browser(), now=1180).next_action == "fresh_login"
    with pytest.raises(ContractViolation):
        login_status(policy(), transaction, browser(browser_binding_sha256="9" * 64), now=1010)
    with pytest.raises(ContractViolation):
        login_status(policy(), transaction, browser(), now=4600)


@pytest.mark.parametrize("value_now", [True, -1, 1.2])
def test_server_time_is_never_coerced(value_now: Any) -> None:
    with pytest.raises(ValidationError):
        validate_session(policy(), value(SessionRecord), value(SessionCredential), now=value_now)


def test_missing_or_unknown_deployment_policy_never_gets_defaults() -> None:
    with pytest.raises(ContractViolation, match="policy_unavailable"):
        login_options(None)
    with pytest.raises(ContractViolation, match="unsupported_flow"):
        validate_login_start(policy(), value(LoginStartRequest, provider_id="unknown"), browser())


def test_public_callback_query_rejects_success_plus_error_or_missing_state() -> None:
    from strange_physics.session_contracts import OIDCCallbackRequest, OIDCDeniedCallbackRequest

    cases: list[tuple[type[Message], dict[str, str]]] = [
        (OIDCCallbackRequest, {"code": "synthetic", "error": "denied", "state": "synthetic"}),
        (OIDCDeniedCallbackRequest, {"error": "denied"}),
    ]
    for model, data in cases:
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(data))


def test_verified_state_requires_durable_exclusive_proof_claim() -> None:
    with pytest.raises(ContractViolation, match="proof_rejected"):
        validate_proof(
            policy(),
            value(LoginTransaction),
            value(TrustedIdentityProof),
            now=1010,
            claimed_by_transaction=None,
        )


def test_future_auth_time_cannot_create_an_immediately_invalid_session_view() -> None:
    with pytest.raises(ContractViolation, match="proof_rejected"):
        validate_proof(
            policy(),
            value(LoginTransaction, state="verifying", proof=None),
            value(TrustedIdentityProof, auth_time=1011, issued_at=1011, verified_at=1011),
            now=1010,
            claimed_by_transaction=None,
        )


def test_response_secrets_are_readable_but_still_redacted_and_requests_are_write_only() -> None:
    definitions = session_json_schema()["$defs"]

    def no_write_only(node: Any) -> None:
        if isinstance(node, dict):
            assert node.get("writeOnly") is not True
            for item in node.values():
                no_write_only(item)
        elif isinstance(node, list):
            for item in node:
                no_write_only(item)

    for model, field in [("CSRFResponse", "token"), ("LoginStartResponse", "authorization_url")]:
        no_write_only(definitions[model]["properties"][field])
    for model, field in [
        ("BrokerExchangeRequest", "id_token"),
        ("OIDCCallbackRequest", "code"),
        ("OIDCCallbackRequest", "state"),
        ("OIDCDeniedCallbackRequest", "error"),
    ]:
        assert definitions[model]["properties"][field]["writeOnly"] is True
    response = value(
        MODELS["LoginStartResponse"],
        flow="oidc_code",
        authorization_url="https://idp.example/authorize?state=synthetic",
    )
    assert "https://idp.example" not in repr(response)
    assert "https://idp.example" not in response.model_dump_json()


def test_login_outcome_path_reuses_identifier_schema_and_runtime_edges() -> None:
    api = json.loads((ROOT / "contracts/session.openapi.json").read_text())
    parameter = api["paths"]["/v1/auth/logins/{transaction_id}"]["get"]["parameters"][0]
    adapter = TypeAdapter(Identifier)
    assert parameter["schema"] == adapter.json_schema()
    for item in FIXTURES["path_identifiers"]["valid"]:
        assert adapter.validate_python(item, strict=True) == item
    for item in FIXTURES["path_identifiers"]["invalid"]:
        with pytest.raises(ValidationError):
            adapter.validate_python(item, strict=True)


@pytest.mark.parametrize("case", FIXTURES["workspace_session_failures"])
def test_workspace_auth_errors_preserve_existing_safe_control_envelope(
    case: dict[str, Any],
) -> None:
    status, error = workspace_session_error(
        ContractViolation(case["input_code"], case["status"]),
        request_id="request-1",
    )
    assert status == case["status"]
    assert error.model_dump(mode="json") == case["output"]
    api = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    for routes in api["paths"].values():
        for method, route in routes.items():
            if method not in {"get", "post", "put"}:
                continue
            if {"workspaceBearer": []} in route.get("security", []):
                assert str(status) in route["responses"]
                assert route["x-session-error-mapping"][case["input_code"]] == {
                    "status": status,
                    "code": error.code,
                }
                assert "404" in route["responses"]
            else:
                assert "x-session-error-mapping" not in route


def test_workspace_mapping_does_not_remap_object_authority_or_run_conflicts() -> None:
    for code, status in [
        ("not_found", 404),
        ("incompatible_state", 409),
        ("ambiguous_credentials", 401),
    ]:
        with pytest.raises(ValueError):
            workspace_session_error(ContractViolation(code, status), request_id="request-1")


def test_provider_alias_cannot_partition_application_wide_proof_ownership() -> None:
    data = policy().model_dump(mode="json")
    alias = data["providers"][0] | {"provider_id": "managed-alias"}
    data["providers"].append(alias)
    configured = DeploymentSessionPolicy.model_validate_json(json.dumps(data))
    first_transaction = value(LoginTransaction, state="verifying", proof=None)
    first_proof = value(TrustedIdentityProof)
    validate_proof(
        configured, first_transaction, first_proof, now=1010, claimed_by_transaction=None
    )
    alias_transaction = value(
        LoginTransaction,
        transaction_id="login-2",
        provider_id="managed-alias",
        state="verifying",
        proof=None,
    )
    alias_proof = value(TrustedIdentityProof, transaction_id="login-2", provider_id="managed-alias")
    assert proof_claim_key(first_proof) == proof_claim_key(alias_proof)
    claims = {proof_claim_key(first_proof): first_transaction.transaction_id}
    with pytest.raises(ContractViolation, match="proof_rejected"):
        validate_proof(
            configured,
            alias_transaction,
            alias_proof,
            now=1010,
            claimed_by_transaction=claims[proof_claim_key(alias_proof)],
        )


def test_proof_tombstone_outlives_transaction_retention_and_policy_aliases() -> None:
    configured = value(DeploymentSessionPolicy, transaction_retention_seconds=180)
    transaction = value(LoginTransaction, state="verifying", proof=None)
    proof = value(TrustedIdentityProof, expires_at=6000)
    assert proof_claim_retain_until(configured, transaction, proof) == 6000
    assert proof_claim_retain_until(policy(), transaction, value(TrustedIdentityProof)) == 4600
    alternate = value(DeploymentSessionPolicy, policy_id="different-policy")
    alternate_transaction = value(
        LoginTransaction, policy_id="different-policy", state="verifying", proof=None
    )
    assert proof_claim_key(proof) == FIXTURES["valid"]["TrustedIdentityProof"]["proof_sha256"]
    assert proof_claim_retain_until(alternate, alternate_transaction, proof) == 6000
    with pytest.raises(ValueError):
        proof_claim_retain_until(alternate, transaction, proof)
