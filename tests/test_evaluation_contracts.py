from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.evaluation_contracts import (
    EVALUATION_MODELS,
    ProbePrediction,
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    SpringPredictionSubmissions,
    evaluation_json_schema,
    submissions_sha256,
    validate_spring_evaluation_result,
)
from strange_physics.research_contracts import LinearSpringModel, message_sha256
from strange_physics.worlds import WorldDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/evaluation.examples.json").read_text())


def value[T: Message](model: type[T]) -> T:
    return model.model_validate_json(json.dumps(FIXTURES["valid"][model.__name__]))


def inputs() -> tuple[
    LinearSpringModel, SpringEvaluationProtocol, tuple[ProbePrediction, ...], WorldDefinition
]:
    return (
        LinearSpringModel.model_validate_json(json.dumps(FIXTURES["model"])),
        value(SpringEvaluationProtocol),
        value(SpringPredictionSubmissions).entries,
        WorldDefinition.model_validate_json(json.dumps(FIXTURES["world"])),
    )


@pytest.mark.parametrize("model", EVALUATION_MODELS)
def test_evaluation_models_round_trip_and_forbid_extra_fields(model: type[Message]) -> None:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    assert model.model_validate_json(json.dumps(data)).model_dump(mode="json") == data
    data["unrecognized"] = "not silently accepted"
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("group", ["schema_negative", "runtime_negative"])
def test_negative_interface_vectors(group: str) -> None:
    models = {model.__name__: model for model in EVALUATION_MODELS}
    for fixture in FIXTURES[group]:
        data = copy.deepcopy(FIXTURES["valid"][fixture["model"]])
        data[fixture["field"]] = fixture["value"]
        with pytest.raises(ValidationError):
            models[fixture["model"]].model_validate_json(json.dumps(data))


def test_schema_and_actual_artifact_binding() -> None:
    assert (
        json.loads((ROOT / "contracts/evaluation.schema.json").read_text())
        == evaluation_json_schema()
    )
    result = value(SpringEvaluationResult)
    validate_spring_evaluation_result(result, *inputs())
    assert result.report is not None
    assert result.report_sha256 == message_sha256(result.report)
    assert result.reference is not None
    assert result.reference_sha256 == message_sha256(result.reference)
    assert result.diagnostics.submissions_sha256 == submissions_sha256(inputs()[2])


@pytest.mark.parametrize("field", ["actual_model_sha256", "protocol_sha256", "submissions_sha256"])
def test_stated_hashes_cannot_replace_actual_input_binding(field: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["SpringEvaluationResult"])
    data["diagnostics"][field] = "f" * 64
    # Use a protocol-failure outcome to isolate the actual-input binder.
    data.update(
        status="protocol_failure",
        reason="duplicate_submission",
        report=None,
        report_sha256=None,
        reference=None,
        reference_sha256=None,
    )
    data["diagnostics"].update(
        valid_prediction_count=0,
        prediction_not_assessed_count=1,
        computed_metric_count=0,
        metric_not_assessed_count=1,
        reference_completed_probe_count=0,
    )
    data["probes"][0].update(prediction_status="not_assessed", position_mse=None)
    result = SpringEvaluationResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="actual model, protocol and submissions"):
        validate_spring_evaluation_result(result, *inputs())


def test_private_truth_hash_is_absent_from_public_protocol_and_report() -> None:
    result = value(SpringEvaluationResult)
    assert result.reference is not None and result.report is not None
    public = value(SpringEvaluationProtocol).model_dump_json() + result.report.model_dump_json()
    assert result.reference.source_world_sha256 not in public
    assert "source_world" not in public and "reference_sha256" not in public
    assert "positions" not in result.report.model_dump_json()


def test_actual_world_and_reference_grids_are_bound_independently() -> None:
    result = value(SpringEvaluationResult)
    model, protocol, submissions, world = inputs()
    changed = world.model_dump(mode="json")
    changed["noise_seed"] += 1
    with pytest.raises(ValueError, match="actual source world"):
        validate_spring_evaluation_result(
            result,
            model,
            protocol,
            submissions,
            WorldDefinition.model_validate_json(json.dumps(changed)),
        )
    data = result.model_dump(mode="json")
    data["reference"]["probes"][0]["times"] = [0.0, 0.5]
    from strange_physics.evaluation_contracts import SpringReferenceArtifact

    reference = SpringReferenceArtifact.model_validate_json(json.dumps(data["reference"]))
    data["reference_sha256"] = message_sha256(reference)
    altered = SpringEvaluationResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="exact grids"):
        validate_spring_evaluation_result(altered, *inputs())


@pytest.mark.parametrize(
    "case", ["missing_report", "changed_runtime", "hidden_failed_prediction", "missing_reference"]
)
def test_scored_result_cannot_hide_timing_counts_or_reference_failure(case: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["SpringEvaluationResult"])
    if case == "missing_report":
        data["report"] = None
    elif case == "changed_runtime":
        data["diagnostics"]["evaluation_runtime_ms"] += 1
    elif case == "hidden_failed_prediction":
        data["probes"][0]["prediction_status"] = "failed"
    else:
        data.update(reference=None, reference_sha256=None)
    with pytest.raises(ValidationError):
        SpringEvaluationResult.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field", ["normalization_scale", "probes"])
def test_protocol_is_bounded_and_requires_predeclared_positive_scale(field: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["SpringEvaluationProtocol"])
    data[field] = 0.0 if field == "normalization_scale" else data["probes"] * 25
    with pytest.raises(ValidationError):
        SpringEvaluationProtocol.model_validate_json(json.dumps(data))


def test_transport_manifest_bounds_and_failure_marker_shape() -> None:
    entry = value(ProbePrediction)
    with pytest.raises(ValidationError):
        SpringPredictionSubmissions(entries=(entry,) * 49)
    with pytest.raises(ValidationError, match="parsed prediction"):
        ProbePrediction(
            probe_id=entry.probe_id,
            request_sha256=entry.request_sha256,
            status="failed",
            response=entry.response,
        )


def test_timing_is_included_in_report_identity() -> None:
    result = value(SpringEvaluationResult)
    assert result.report is not None
    data = result.report.model_dump(mode="json")
    data["evaluation_runtime_ms"] += 1
    from strange_physics.research_contracts import EvaluationReport

    changed = EvaluationReport.model_validate_json(json.dumps(data))
    assert message_sha256(changed) != result.report_sha256
    assert changed.position_mse == result.report.position_mse


def test_semantic_bad_protocol_can_reach_the_typed_failure_boundary() -> None:
    data = copy.deepcopy(FIXTURES["valid"]["SpringEvaluationProtocol"])
    data["probes"][0]["request_sha256"] = "f" * 64
    protocol = SpringEvaluationProtocol.model_validate_json(json.dumps(data))
    assert protocol.probes[0].request_sha256 != message_sha256(protocol.probes[0].request)


@pytest.mark.parametrize(
    "case",
    [
        "unscorable_completed",
        "unscorable_failed_index",
        "unsupported_world_completed",
        "unsupported_world_failed_index",
        "reference_failure_missing_index",
    ],
)
def test_failure_stages_cannot_claim_impossible_reference_progress(case: str) -> None:
    from strange_physics.research_contracts import EvaluationReport

    data = copy.deepcopy(FIXTURES["valid"]["SpringEvaluationResult"])
    data.update(reference=None, reference_sha256=None)
    data["probes"][0]["position_mse"] = None
    data["diagnostics"].update(
        computed_metric_count=0,
        metric_not_assessed_count=1,
        reference_completed_probe_count=0,
        reference_failed_probe_index=None,
    )
    if case.startswith("unscorable"):
        data.update(status="unscorable", reason="prediction_failure")
        data["probes"][0]["prediction_status"] = "missing"
        data["diagnostics"].update(valid_prediction_count=0, failed_prediction_count=1)
        data["report"].update(
            status="unscorable",
            valid_prediction_count=0,
            failed_prediction_count=1,
            position_mse=None,
            normalized_position_mse=None,
        )
        data["report_sha256"] = message_sha256(
            EvaluationReport.model_validate_json(json.dumps(data["report"]))
        )
    else:
        data.update(
            status="evaluator_failure", reason="unsupported_world", report=None, report_sha256=None
        )
    if case.endswith("completed"):
        data["diagnostics"]["reference_completed_probe_count"] = 1
    elif case.endswith("failed_index"):
        data["diagnostics"]["reference_failed_probe_index"] = 0
    else:
        data["reason"] = "reference_failure"
    with pytest.raises(ValidationError):
        SpringEvaluationResult.model_validate_json(json.dumps(data))
