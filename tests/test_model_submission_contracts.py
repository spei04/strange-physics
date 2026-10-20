from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import model_submission_contracts as m
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.control_contracts import ModelReceipt
from strange_physics.research_contracts import LinearSpringModel, message_sha256
from strange_physics.worker_contracts import OriginalExecutionAdmission

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "contracts/model-registration.examples.json").read_text())
MODELS = {model.__name__: model for model in m.MODEL_REGISTRATION_MODELS}


def fixture(name: str) -> dict[str, Any]:
    return copy.deepcopy(EXAMPLES["valid"][name])


def parse[M: Message](model: type[M], data: Any) -> M:
    return model.model_validate_json(json.dumps(data))


def value[M: Message](model: type[M]) -> M:
    return parse(model, fixture(model.__name__))


def changed[M: Message](model: M, **fields: Any) -> M:
    return type(model).model_validate(model.model_dump() | fields)


@pytest.mark.parametrize("name", tuple(MODELS))
def test_synthetic_positive_contracts(name: str) -> None:
    assert parse(MODELS[name], fixture(name))


@pytest.mark.parametrize("case", EXAMPLES["schema_negative"] + EXAMPLES["runtime_negative"])
def test_declared_negative_fixtures(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        parse(MODELS[case["model"]], fixture(case["model"]) | {case["field"]: case["value"]})


def test_schema_matches_and_public_reference_closure_is_narrow() -> None:
    schema = m.model_registration_json_schema()
    assert schema == json.loads((ROOT / "contracts/model-registration.schema.json").read_text())
    assert schema["x-public-models"] == ["SubmitModelRequest"]
    reached: set[str] = set()
    pending = ["SubmitModelRequest"]
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        nodes: list[Any] = [schema["$defs"][name]]
        while nodes:
            node = nodes.pop()
            if isinstance(node, dict):
                reference = node.get("$ref", "")
                if reference.startswith("#/$defs/"):
                    pending.append(reference.removeprefix("#/$defs/"))
                nodes.extend(node.values())
            elif isinstance(node, list):
                nodes.extend(node)
    assert reached == {"SubmitModelRequest", "ArtifactRef"}
    api = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    assert api["components"]["schemas"]["SubmitModelRequest"] == {
        "$ref": "../model-registration.schema.json#/$defs/SubmitModelRequest"
    }
    route = api["paths"]["/v1/runs/{run_id}/models"]["post"]
    assert route["security"] == [{"runBearer": []}]
    assert {"200", "202"} <= route["responses"].keys()


def test_actual_fixture_bytes_and_canonical_identity_remain_distinct() -> None:
    request = value(m.SubmitModelRequest)
    raw = EXAMPLES["model_bytes_utf8"].encode()
    model = LinearSpringModel.model_validate_json(raw)
    assert len(raw) == request.model_artifact.size_bytes
    assert hashlib.sha256(raw).hexdigest() == request.model_artifact.sha256
    assert message_sha256(model) == request.model_sha256
    compact = model.model_dump_json().encode()
    assert hashlib.sha256(compact).hexdigest() != request.model_artifact.sha256
    assert message_sha256(LinearSpringModel.model_validate_json(compact)) == request.model_sha256
    ledger = m.ModelLedgerSnapshot.model_validate_json(EXAMPLES["ledger_bytes_utf8"])
    observations = parse(ObservationBundle, EXAMPLES["observations"])
    assert observations.records == tuple(o.result.value for o in ledger.operations if o.result)
    assert observations.records[1].status == "failed"
    assert model.fit_record_indices == (0,)
    assert message_sha256(observations) == model.observation_sha256


def test_registered_model_can_be_outside_predictor_compatibility() -> None:
    record = value(m.ModelRegistrationRecord)
    assert record.model.linear == 5.0
    assert record.model.fitter_version != record.prediction_config.supported_fitter_version
    assert record.model.fit_config_sha256 != record.prediction_config.supported_fit_config_sha256
    assert record.approval.profile.predictor_version == record.prediction_config.predictor_version
    assert record.approval.profile.prediction_config_sha256 == message_sha256(
        record.prediction_config
    )


@pytest.mark.parametrize(
    "field,wrong",
    [
        ("workspace_id", "other"),
        ("run_id", "other"),
        ("admission_id", "other"),
        ("admission_sha256", "f" * 64),
        ("creation_request_sha256", "f" * 64),
        ("world_version_id", "other"),
        ("ownership_sha256", "f" * 64),
        ("space_sha256", "f" * 64),
        ("committed_at", 0),
    ],
)
def test_engine_selection_joins_actual_original_admission(field: str, wrong: Any) -> None:
    record = value(m.ModelRegistrationRecord)
    with pytest.raises(ValueError):
        m.validate_engine_admission(
            changed(record.engine, **{field: wrong}), record.worker.admission
        )


def test_engine_binding_is_not_recomputed_from_current_predictor_or_package() -> None:
    record = value(m.ModelRegistrationRecord)
    assert record.engine.engine_fingerprint != record.submission.request.runtime_image_sha256
    assert record.engine.engine_version == "synthetic-original-engine"
    m.validate_engine_admission(record.engine, record.worker.admission)


@pytest.mark.parametrize("field", ["workspace_id", "run_id"])
def test_ledger_rejects_cross_scope_operation(field: str) -> None:
    ledger = value(m.ModelLedgerSnapshot)
    first = changed(ledger.operations[0], **{field: "other"})
    with pytest.raises(ValidationError):
        changed(ledger, operations=(first, *ledger.operations[1:]))


@pytest.mark.parametrize(
    "field,wrong",
    [
        ("request_sha256", "f" * 64),
        ("run_revision", 0),
        ("accepted_at", 0),
        ("accepted_at", 2000),
    ],
)
def test_admission_identity_and_chronology(field: str, wrong: Any) -> None:
    with pytest.raises(ValidationError):
        changed(value(m.ModelSubmissionAdmission), **{field: wrong})


@pytest.mark.parametrize("field", ["workspace_id", "resource_id", "principal_id", "kind"])
def test_admission_scope_cannot_change(field: str) -> None:
    admission = value(m.ModelSubmissionAdmission)
    wrong = "experiment" if field == "kind" else "other"
    with pytest.raises(ValidationError):
        changed(admission, scope=changed(admission.scope, **{field: wrong}))


@pytest.mark.parametrize("status", ["running", "cancelled"])
def test_new_admission_proposal_is_pending_only(status: str) -> None:
    plan = value(m.ModelAdmissionPlan)
    with pytest.raises(ValidationError):
        changed(
            plan,
            stored=changed(plan.stored, operation=changed(plan.stored.operation, status=status)),
        )


@pytest.mark.parametrize("field", ["model_id", "model_sha256", "through_index"])
def test_completed_receipt_cannot_reference_another_model(field: str) -> None:
    plan = value(m.ModelCommitPlan)
    result = plan.after.operation.result
    assert result is not None and isinstance(result.value, ModelReceipt)
    wrong: Any = {"model_id": "other", "model_sha256": "f" * 64, "through_index": 0}[field]
    receipt = changed(result.value, **{field: wrong})
    operation = changed(plan.after.operation, result=changed(result, value=receipt))
    after = changed(plan.after, operation=operation)
    with pytest.raises(ValidationError):
        changed(plan, after=after)


@pytest.mark.parametrize(
    "field",
    [
        "workspace_id",
        "run_id",
        "operation_id",
        "model_id",
        "request_sha256",
        "record_sha256",
        "committed_at",
    ],
)
def test_completed_outbox_cannot_substitute_identity(field: str) -> None:
    plan = value(m.ModelCommitPlan)
    wrong: Any = (
        1204 if field == "committed_at" else "f" * 64 if field.endswith("sha256") else "other"
    )
    with pytest.raises(ValidationError):
        changed(plan, outbox=changed(plan.outbox, **{field: wrong}))


@pytest.mark.parametrize("field", ["model", "artifact", "approval", "prediction_config", "engine"])
def test_public_request_rejects_private_projections(field: str) -> None:
    with pytest.raises(ValidationError):
        parse(m.SubmitModelRequest, fixture("SubmitModelRequest") | {field: {}})


def test_missing_closure_is_representable_but_is_not_a_completed_commit() -> None:
    lookup = value(m.ModelRegistrationLookup)
    for field in ("stored", "admission", "record", "outbox"):
        assert changed(lookup, **{field: None})
    plan = fixture("ModelCommitPlan")
    for field in ("after", "record", "outbox"):
        with pytest.raises(ValidationError):
            parse(m.ModelCommitPlan, plan | {field: None})


@pytest.mark.parametrize("status", ["pending", "running", "failed", "cancelled", "completed"])
def test_operation_replay_preserves_all_statuses_without_private_record(status: str) -> None:
    data = fixture("ModelSubmissionReplay")
    operation = data["operation"]
    operation["status"] = status
    if status != "completed":
        operation["result"] = None
    if status == "failed":
        operation["error"] = {
            "code": "invalid_request",
            "message": "Synthetic validation failure",
            "request_id": "synthetic",
            "retryable": False,
            "operation_id": operation["operation_id"],
        }
    replay = parse(m.ModelSubmissionReplay, data)
    assert replay.operation.status == status
    assert set(replay.model_dump()) == {"operation"}
    assert "engine_fingerprint" not in replay.model_dump_json()
    assert "object_key" not in replay.model_dump_json()


def test_commit_allows_running_but_rejects_terminal_source_operation() -> None:
    plan = value(m.ModelCommitPlan)
    running = changed(plan.before, operation=changed(plan.before.operation, status="running"))
    assert changed(plan, before=running)
    cancelled = changed(plan.before, operation=changed(plan.before.operation, status="cancelled"))
    with pytest.raises(ValidationError):
        changed(plan, before=cancelled)


def test_later_attempt_commit_preserves_original_admission_and_scope() -> None:
    record = value(m.ModelRegistrationRecord)
    worker = record.worker
    request = changed(
        worker.request, attempt_id="attempt-next", lease_epoch=worker.request.lease_epoch + 1
    )
    replacement = changed(
        worker,
        launch_id="launch-next",
        request=request,
        request_sha256=message_sha256(request),
        created_at=1202,
        run_revision=5,
    )
    assert changed(record, worker=replacement, run_revision=5)
    wrong_epoch = changed(request, lease_epoch=worker.request.lease_epoch - 1)
    older = changed(replacement, request=wrong_epoch, request_sha256=message_sha256(wrong_epoch))
    with pytest.raises(ValidationError):
        changed(record, worker=older, run_revision=5)
    same_epoch = changed(request, lease_epoch=worker.request.lease_epoch)
    alias = changed(replacement, request=same_epoch, request_sha256=message_sha256(same_epoch))
    with pytest.raises(ValidationError):
        changed(record, worker=alias, run_revision=5)


def test_frozen_core_scientific_messages_remain_external() -> None:
    schema = m.model_registration_json_schema()
    control = json.loads((ROOT / "contracts/control.schema.json").read_text())
    research = json.loads((ROOT / "contracts/research.schema.json").read_text())
    assert schema["$defs"]["ModelReceipt"] == control["$defs"]["ModelReceipt"]
    assert schema["$defs"]["LinearSpringModel"] == research["$defs"]["LinearSpringModel"]
    assert OriginalExecutionAdmission is type(value(m.ModelRegistrationRecord).worker.admission)
