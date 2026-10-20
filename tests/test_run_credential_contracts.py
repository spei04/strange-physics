"""C2 producer-shape tests; no token verification, current DB read or signing claim."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.run_credential_contracts import (
    RUN_CREDENTIAL_MODELS,
    ProductAuthorityEnvelope,
    RunAuthorityState,
    RunCredentialIssueRequest,
    RunCredentialPlan,
    RunCredentialRecord,
    RunCredentialReplaceRequest,
    RunCredentialRevokeRequest,
    RunCredentialSet,
    RunCredentialView,
    RunTokenClaims,
    run_credential_json_schema,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/run-credentials.examples.json").read_text())
MODELS = {model.__name__: model for model in RUN_CREDENTIAL_MODELS}


def value[T: Message](model: type[T]) -> T:
    return model.model_validate_json(json.dumps(FIXTURES["valid"][model.__name__]))


def changed[T: Message](original: T, **updates: Any) -> T:
    return type(original).model_validate(original.model_dump() | updates)


@pytest.mark.parametrize("name", tuple(MODELS))
def test_synthetic_producer_fixtures_round_trip(name: str) -> None:
    result = MODELS[name].model_validate_json(json.dumps(FIXTURES["valid"][name]))
    assert MODELS[name].model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("fixture", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_shape_and_semantic_negatives_are_rejected(fixture: dict[str, Any]) -> None:
    data = copy.deepcopy(FIXTURES["valid"][fixture["model"]])
    data[fixture["field"]] = fixture["value"]
    with pytest.raises(ValidationError):
        MODELS[fixture["model"]].model_validate_json(json.dumps(data))


def test_published_schema_matches_runtime_model_generation() -> None:
    actual = json.loads((ROOT / "contracts/run-credentials.schema.json").read_text())
    assert actual == run_credential_json_schema()


@pytest.mark.parametrize(
    "name", ("HumanProductAuthority", "ServiceProductAuthority", "RunProductAuthority")
)
def test_required_tagged_authority_selects_exact_producer(name: str) -> None:
    envelope = ProductAuthorityEnvelope.model_validate_json(
        json.dumps({"authority": FIXTURES["valid"][name]})
    )
    assert type(envelope.authority) is MODELS[name]
    with pytest.raises(ValidationError):
        ProductAuthorityEnvelope.model_validate_json("{}")


@pytest.mark.parametrize(
    "model",
    (RunCredentialIssueRequest, RunCredentialReplaceRequest, RunCredentialRevokeRequest),
)
@pytest.mark.parametrize("field", ("scopes", "principal_id", "expires_at", "run_deadline"))
def test_coordinator_requests_have_no_authority_override(model: type[Message], field: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    data[field] = 2000 if field in {"expires_at", "run_deadline"} else "invented"
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field", ("workspace_id", "run_id", "principal_id", "ownership_sha256"))
def test_complete_records_bind_immutable_run_ownership(field: str) -> None:
    state = value(RunCredentialSet)
    bad = "f" * 64 if field == "ownership_sha256" else "foreign"
    claims = changed(state.records[0].claims, **{field: bad})
    record = changed(state.records[0], claims=claims)
    with pytest.raises(ValidationError):
        changed(state, records=(record,))


def test_complete_state_has_one_current_generation_and_never_a_reactivated_old_pointer() -> None:
    state = value(RunCredentialSet)
    old = state.records[0]
    new = changed(old, claims=changed(old.claims, credential_id="worker-key-2", generation=2))
    current = changed(
        state,
        revision=2,
        last_generation=2,
        current_credential_id="worker-key-2",
        records=(old, new),
    )
    with pytest.raises(ValidationError):
        changed(current, current_credential_id=old.claims.credential_id)
    with pytest.raises(ValidationError):
        changed(current, records=(new, old))
    with pytest.raises(ValidationError):
        changed(current, records=(old, old))


def test_current_metadata_cannot_call_a_historical_or_revoked_key_valid() -> None:
    view = value(RunCredentialView)
    with pytest.raises(ValidationError):
        changed(view, current_credential_id="replacement")
    with pytest.raises(ValidationError):
        changed(view, current_generation=2)
    revoked = changed(view.record, revoked_at=1200)
    with pytest.raises(ValidationError):
        changed(view, record=revoked)
    assert not changed(view, record=revoked, valid_now=False).valid_now


def test_owner_role_is_current_but_does_not_rewrite_original_worker_scopes() -> None:
    state = value(RunAuthorityState)
    grant = state.owner.grant
    viewer_grant = changed(grant, membership=changed(grant.membership, role="viewer", revision=1))
    changed_state = changed(state, owner=changed(state.owner, grant=viewer_grant))
    assert changed_state.credentials.ownership == state.credentials.ownership
    # Actual per-operation admission belongs to the mandatory composition function.
    assert changed_state.owner.grant.membership.role == "viewer"


@pytest.mark.parametrize("field", ("event_id", "request_sha256", "snapshot_sha256"))
def test_atomic_plan_requires_matching_audit_projection(field: str) -> None:
    plan = value(RunCredentialPlan)
    bad = "wrong-audit" if field == "event_id" else "e" * 64
    with pytest.raises(ValidationError):
        changed(plan, audit=changed(plan.audit, **{field: bad}))


def test_atomic_plan_requires_the_exact_affected_record_and_current_metadata() -> None:
    plan = value(RunCredentialPlan)
    altered = changed(plan.response.credential.record, retain_until=2001)
    view = changed(plan.response.credential, record=altered)
    response = changed(plan.response, credential=view)
    with pytest.raises(ValidationError):
        changed(plan, response=response)
    with pytest.raises(ValidationError):
        changed(
            plan,
            response=changed(
                plan.response,
                credential=changed(
                    plan.response.credential, current_credential_id=None, valid_now=False
                ),
            ),
        )


def test_replay_shape_cannot_carry_an_issue_directive_or_bearer() -> None:
    plan = value(RunCredentialPlan)
    replay = changed(plan.response, disposition="replayed")
    assert replay.outcome == plan.receipt.outcome
    for field, item in (("issue_claims", plan.issue_claims), ("secret", "synthetic-bearer")):
        with pytest.raises(ValidationError):
            changed(replay, **{field: item})
    with pytest.raises(ValidationError):
        changed(plan, response=replay)


@pytest.mark.parametrize("field", ("generation", "lease_epoch", "issued_at", "expires_at"))
def test_worker_numeric_claims_reject_boolean_aliases(field: str) -> None:
    with pytest.raises(ValidationError):
        changed(value(RunTokenClaims), **{field: True})


def test_record_retention_does_not_erase_revocation_evidence() -> None:
    record = value(RunCredentialRecord)
    with pytest.raises(ValidationError):
        changed(record, revoked_at=2100)
    with pytest.raises(ValidationError):
        changed(record, revoked_at=1099)
    assert changed(record, revoked_at=2100, retain_until=2100).revoked_at == 2100
