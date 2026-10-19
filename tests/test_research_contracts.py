from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Frame, ObservationBundle, Trajectory
from strange_physics.research_contracts import (
    EvaluationReport,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    SpringFitInput,
    message_sha256,
    research_json_schema,
    validate_model_for_fit,
    validate_prediction_model,
    validate_prediction_response,
)
from strange_physics.serialization import canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/research.examples.json").read_text())
MODELS = (
    SpringFitInput,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    EvaluationReport,
)


def payload(name: str) -> dict[str, Any]:
    result: dict[str, Any] = copy.deepcopy(FIXTURES["valid"][name])
    return result


def fit_input() -> SpringFitInput:
    return SpringFitInput.model_validate_json(json.dumps(payload("SpringFitInput")))


def model(**changes: object) -> LinearSpringModel:
    value = payload("LinearSpringModel")
    value.update(changes)
    return LinearSpringModel.model_validate_json(json.dumps(value))


def request(**changes: object) -> PredictionRequest:
    value = payload("PredictionRequest")
    value.update(changes)
    return PredictionRequest.model_validate_json(json.dumps(value))


def response(**changes: object) -> PredictionResponse:
    value = payload("PredictionResponse")
    value.update(changes)
    return PredictionResponse.model_validate_json(json.dumps(value))


def report(**changes: object) -> EvaluationReport:
    value = payload("EvaluationReport")
    value.update(changes)
    return EvaluationReport.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("message_type", MODELS)
def test_synthetic_messages_round_trip_and_forbid_hidden_fields(
    message_type: type[SpringFitInput]
    | type[LinearSpringModel]
    | type[PredictionRequest]
    | type[PredictionResponse]
    | type[EvaluationReport],
) -> None:
    value = payload(message_type.__name__)
    parsed = message_type.model_validate_json(json.dumps(value))
    assert parsed.model_dump(mode="json") == value
    value["hidden_law"] = {"linear": 1.0}
    with pytest.raises(ValidationError, match="Extra inputs"):
        message_type.model_validate_json(json.dumps(value))


def test_schema_matches_models_and_every_reference_resolves() -> None:
    stored = json.loads((ROOT / "contracts/research.schema.json").read_text())
    assert stored == research_json_schema()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                reference = node["$ref"]
                assert isinstance(reference, str) and reference.startswith("#/")
                target = stored
                for part in reference[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                assert isinstance(target, dict)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(stored)
    for message_type in MODELS:
        assert stored["$defs"][message_type.__name__]["additionalProperties"] is False


def test_canonical_model_bytes_and_digest_are_fixed_including_unicode_and_defaults() -> None:
    artifact = model()
    assert (
        canonical_json(artifact.model_dump(mode="json")) == FIXTURES["canonical_model"]["utf8_text"]
    )
    assert message_sha256(artifact) == FIXTURES["canonical_model"]["sha256"]
    assert "\\u03b2" in FIXTURES["canonical_model"]["utf8_text"]
    value = payload("LinearSpringModel")
    del value["schema_version"]
    omitted_default = LinearSpringModel.model_validate_json(json.dumps(value))
    assert message_sha256(omitted_default) == message_sha256(artifact)


@pytest.mark.parametrize("through_index", [0, 2])
def test_fit_input_cannot_hide_future_records_or_claim_a_longer_prefix(through_index: int) -> None:
    value = payload("SpringFitInput")
    value["through_index"] = through_index
    with pytest.raises(ValidationError, match="exactly the purchased prefix"):
        SpringFitInput.model_validate_json(json.dumps(value))


def test_fit_input_rejects_empty_or_all_failed_prefixes() -> None:
    value = payload("SpringFitInput")
    value["observations"]["records"] = []
    with pytest.raises(ValidationError, match="exactly the purchased prefix"):
        SpringFitInput.model_validate_json(json.dumps(value))
    value = payload("SpringFitInput")
    first = value["observations"]["records"][0]
    first.update(status="failed", trajectory=None, error="simulation_failed")
    with pytest.raises(ValidationError, match="at least one completed"):
        SpringFitInput.model_validate_json(json.dumps(value))


@pytest.mark.parametrize(
    "mutation",
    ["illegal_mass", "illegal_position", "wrong_order", "missing_frame", "wrong_time", "index_gap"],
)
def test_fit_input_reuses_purchased_observation_validation(mutation: str) -> None:
    value = payload("SpringFitInput")
    record = value["observations"]["records"][0]
    if mutation == "illegal_mass":
        record["experiment"]["particles"][0]["mass"] = 0.1
    elif mutation == "illegal_position":
        record["experiment"]["particles"][0]["position"] = [3.0, 0.0]
    elif mutation == "wrong_order":
        record["experiment"]["particles"][0]["id"] = "other"
    elif mutation == "missing_frame":
        record["trajectory"]["frames"].pop()
    elif mutation == "wrong_time":
        record["trajectory"]["frames"][1]["time"] = 0.04
    else:
        record["index"] = 1
    with pytest.raises(ValidationError):
        SpringFitInput.model_validate_json(json.dumps(value))


def test_valid_model_prefix_request_and_response_are_bound() -> None:
    validate_model_for_fit(model(), fit_input())
    validate_prediction_model(model(), request())
    validate_prediction_response(request(), response())


@pytest.mark.parametrize("indices", [[], [0, 0], [1, 0], [2]])
def test_model_rejects_empty_duplicate_unsorted_and_future_selection(indices: list[int]) -> None:
    with pytest.raises(ValidationError):
        model(fit_record_indices=indices)


def test_model_cannot_claim_a_failed_record_was_used_for_fit() -> None:
    with pytest.raises(ValueError, match="failed observation records"):
        validate_model_for_fit(model(fit_record_indices=[1]), fit_input())


@pytest.mark.parametrize(
    "changes",
    [
        {"through_index": 2},
        {"observation_sha256": "a" * 64},
        {"fit_config_sha256": "a" * 64},
    ],
)
def test_model_rejects_mismatched_prefix_and_configuration(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        validate_model_for_fit(model(**changes), fit_input())


@pytest.mark.parametrize("mutation", ["run_id", "engine", "sampling", "failed_record", "structure"])
def test_provenance_binds_public_metadata_and_failed_records(mutation: str) -> None:
    value = payload("SpringFitInput")
    bundle = value["observations"]
    if mutation == "run_id":
        bundle["run_id"] = "another-run"
    elif mutation == "engine":
        bundle["engine_fingerprint"] = "a" * 64
    elif mutation == "sampling":
        bundle["space"]["sampling"]["position_noise"] = 0.01
    elif mutation == "failed_record":
        bundle["records"][1]["operation_id"] = "other-failure"
    else:
        bundle["space"]["structure"]["anchors"][0]["position"] = [0.5, 0.0]
    changed = SpringFitInput.model_validate_json(json.dumps(value))
    with pytest.raises(ValueError, match="observation digest"):
        validate_model_for_fit(model(), changed)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -0.1])
def test_model_rejects_nonfinite_or_negative_coefficients(value: float) -> None:
    with pytest.raises(ValidationError):
        model(linear=value)


@pytest.mark.parametrize(
    "times, dt",
    [
        ([0.05, 0.1], 0.01),
        ([0.0, 0.1, 0.05], 0.01),
        ([0.0, 0.05, 0.05], 0.01),
        ([0.0, 0.055], 0.01),
        ([0.0, 10.0], 0.0001),
        ([0.0, float("inf")], 0.01),
    ],
)
def test_prediction_rejects_invalid_time_grids(times: list[float], dt: float) -> None:
    with pytest.raises(ValidationError):
        request(times=times, integration_dt=dt)


def test_prediction_preserves_order_but_allows_extrapolation_probes() -> None:
    value = payload("PredictionRequest")
    value["experiment"]["particles"][0]["position"] = [3.0, 0.0]
    parsed = PredictionRequest.model_validate_json(json.dumps(value))
    assert parsed.experiment.particles[0].position == (3.0, 0.0)
    value["experiment"]["particles"][0]["id"] = "wrong"
    with pytest.raises(ValidationError, match="identities and order"):
        PredictionRequest.model_validate_json(json.dumps(value))


def test_prediction_rejects_shuffled_particle_order() -> None:
    value = payload("PredictionRequest")
    value["structure"]["particle_ids"] = ["p", "q"]
    particle = copy.deepcopy(value["experiment"]["particles"][0])
    particle["id"] = "q"
    value["experiment"]["particles"].insert(0, particle)
    with pytest.raises(ValidationError, match="identities and order"):
        PredictionRequest.model_validate_json(json.dumps(value))


def test_prediction_binds_actual_model_and_response_digest() -> None:
    with pytest.raises(ValueError, match="model artifact"):
        validate_prediction_model(model(linear=1.1), request())
    with pytest.raises(ValueError, match="response model digest"):
        validate_prediction_response(request(), response(model_sha256="a" * 64))


@pytest.mark.parametrize("mutation", ["missing_frame", "extra_frame", "shift_time", "wrong_shape"])
def test_prediction_response_must_match_requested_times_and_shape(mutation: str) -> None:
    value = payload("PredictionResponse")
    frames = value["trajectory"]["frames"]
    if mutation == "missing_frame":
        frames.pop()
    elif mutation == "extra_frame":
        frames.append({**frames[-1], "time": 0.15})
    elif mutation == "shift_time":
        frames[1]["time"] += 1e-12
    else:
        for frame in frames:
            frame["positions"].append([0.0, 0.0])
            frame["velocities"].append([0.0, 0.0])
    changed = PredictionResponse.model_validate_json(json.dumps(value))
    with pytest.raises(ValueError):
        validate_prediction_response(request(), changed)


def test_prediction_response_rejects_nonfinite_values() -> None:
    value = payload("PredictionResponse")
    value["trajectory"]["frames"][0]["positions"][0][0] = float("nan")
    with pytest.raises(ValidationError):
        PredictionResponse.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("failed_count", [1, 2])
def test_any_failed_prediction_is_unscorable_with_null_primary_errors(failed_count: int) -> None:
    changes = {
        "failed_prediction_count": failed_count,
        "valid_prediction_count": 2 - failed_count,
    }
    with pytest.raises(ValidationError, match="null errors"):
        report(**changes)
    accepted = report(
        **changes, status="unscorable", position_mse=None, normalized_position_mse=None
    )
    assert accepted.position_mse is None
    assert (
        accepted.probe_count == accepted.valid_prediction_count + accepted.failed_prediction_count
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"probe_count": 3},
        {"position_mse": None},
        {"normalized_position_mse": None},
        {"status": "unscorable"},
        {"normalized_position_mse": 2.0},
        {"split": "blind"},
        {"failure_policy": "drop-failed"},
        {"position_mse": float("inf")},
    ],
)
def test_report_rejects_counts_policy_and_score_inconsistencies(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        report(**changes)


@pytest.mark.parametrize("scale", [0.0, 1e-300, 1e300])
def test_report_rejects_unusable_squared_scale(scale: float) -> None:
    with pytest.raises(ValidationError):
        report(normalization_scale=scale)


@pytest.mark.parametrize(
    "mse, scale, normalized",
    [(1e300, 1e-150, float("inf")), (1e-300, 1e150, 0.0)],
)
def test_normalization_overflow_and_underflow_cannot_be_valid_scores(
    mse: float, scale: float, normalized: float
) -> None:
    with pytest.raises(ValidationError):
        report(position_mse=mse, normalization_scale=scale, normalized_position_mse=normalized)


def test_report_accepts_hand_calculated_and_true_zero_errors() -> None:
    assert report(position_mse=9.0, normalization_scale=3.0, normalized_position_mse=1.0)
    assert report(position_mse=0.0, normalized_position_mse=0.0)


def test_model_provenance_requires_valid_observation_bundle_before_hashing() -> None:
    value = payload("SpringFitInput")["observations"]
    value["records"][0]["trajectory"]["frames"][0]["positions"].append([0.0, 0.0])
    with pytest.raises(ValidationError):
        ObservationBundle.model_validate_json(json.dumps(value))


def test_response_frame_contract_enforces_finite_and_equal_vector_counts() -> None:
    with pytest.raises(ValidationError):
        Frame(time=0.0, positions=((1.0, 0.0),), velocities=((0.0, 0.0), (0.0, 0.0)))
    with pytest.raises(ValidationError):
        Trajectory(
            frames=(
                Frame(time=0.0, positions=((1.0, 0.0),), velocities=((0.0, 0.0),)),
                Frame(time=0.0, positions=((1.0, 0.0),), velocities=((0.0, 0.0),)),
            )
        )
