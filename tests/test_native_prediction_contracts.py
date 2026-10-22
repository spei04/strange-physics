from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from test_native_runtime import prediction_input

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionOutcome,
    NativePredictionResult,
    native_prediction_json_schema,
    parse_native_prediction_input,
    parse_native_prediction_result,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import MAX_INPUT_BYTES, NativeCandidateConfig
from strange_physics.research_contracts import LinearSpringModel, message_sha256

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionOutcome,
    NativePredictionResult,
)


def test_native_profile_pins_actual_existing_candidate_config() -> None:
    assert NativePredictionConfig().supported_candidate_config_sha256 == message_sha256(
        NativeCandidateConfig()
    )
    assert (
        NativePredictionConfig().predictor_version
        == "strange-physics.linear-spring.native-analytic.v1"
    )


@pytest.mark.parametrize(
    "field",
    [
        "particle_count",
        "anchor_count",
        "connection_count",
        "max_reference_steps",
        "max_output_frames",
        "max_input_bytes",
        "max_result_bytes",
    ],
)
@pytest.mark.parametrize("value", [True, 0, 99999999])
def test_fixed_integer_config_is_strict(field: str, value: Any) -> None:
    data = NativePredictionConfig().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        NativePredictionConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("change", ["attempt", "request", "model", "signed_zero", "candidate_hash"])
def test_actual_prediction_binder_rejects_changed_material(change: str) -> None:
    actual = prediction_input(0.0)
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    data = actual.model_dump(mode="json")
    attempt = "parent-envelope"
    if change == "attempt":
        attempt = "different"
    elif change == "request":
        data["request"]["integration_dt"] = 0.005
    else:
        field, value = {
            "model": ("observation_sha256", "f" * 64),
            "signed_zero": ("linear", -0.0),
            "candidate_hash": ("fit_config_sha256", "f" * 64),
        }[change]
        data["model"][field] = value
        data["request"]["model_sha256"] = message_sha256(
            LinearSpringModel.model_validate_json(json.dumps(data["model"]))
        )
    changed = NativePredictionInput.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="actual"):
        validate_native_prediction_result(result, changed, attempt_id=attempt)


@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_frame_count", 2),
        ("computed_frame_count", 0),
        ("returned_frame_count", 0),
        ("failed_frame_index", 0),
        ("observation_sha256", "f" * 64),
        ("prediction_config_sha256", "f" * 64),
        ("actual_model_sha256", "f" * 64),
        ("status", "numerical_failure"),
        ("reason", "output_bound"),
    ],
)
def test_cross_projection_count_and_identity_corruption_rejects(field: str, value: Any) -> None:
    actual = prediction_input()
    data = predict_native_spring(actual, attempt_id="parent-envelope").model_dump(mode="json")
    data["payload"][field] = value
    with pytest.raises(ValidationError):
        NativePredictionResult.model_validate_json(json.dumps(data))


def test_response_request_join_rejects_consistently_rehashed_wrong_time() -> None:
    actual = prediction_input()
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    data = result.model_dump(mode="json")
    data["payload"]["response"]["trajectory"]["frames"][1]["time"] = 0.051
    payload = NativePredictionOutcome.model_validate_json(json.dumps(data["payload"]))
    data["facts"]["output_sha256"] = message_sha256(payload)
    changed = NativePredictionResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="times"):
        validate_native_prediction_result(changed, actual, attempt_id="parent-envelope")


def test_strict_raw_input_result_roundtrip_and_formatting_canonical_identity() -> None:
    actual = prediction_input()
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert parse_native_prediction_input(actual.model_dump_json().encode()) == actual
    assert parse_native_prediction_result(result.model_dump_json().encode()) == result
    alternate = json.dumps(actual.model_dump(mode="json"), indent=2).encode()
    assert message_sha256(parse_native_prediction_input(alternate)) == message_sha256(actual)
    assert alternate != actual.model_dump_json().encode()


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b'{"model":0,"model":1}',
        b'{"x":NaN}',
        b'{"x":1e9999}',
        b"\xff",
        b"[" * 33 + b"0" + b"]" * 33,
        b'{"x":[' + b"0," * 1_000_001 + b"0]}",
        b" " * (MAX_INPUT_BYTES + 1),
    ],
)
def test_strict_input_rejects_bounded_and_malformed_bytes(raw: bytes) -> None:
    with pytest.raises(ContractViolation):
        parse_native_prediction_input(raw)


def test_private_or_extra_fields_are_not_accepted() -> None:
    data = prediction_input().model_dump(mode="json")
    data["private_truth"] = {"linear": 1.0}
    with pytest.raises(ValidationError):
        NativePredictionInput.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("model", MODELS)
def test_generated_schema_fixtures_and_bounded_roundtrip(model: type[Message]) -> None:
    fixture = json.loads((ROOT / "contracts/native-prediction.examples.json").read_text())["valid"][
        model.__name__
    ]
    value = model.model_validate_json(json.dumps(fixture))
    assert value.model_dump(mode="json") == fixture


def test_generated_schema_is_exact_and_has_no_private_inputs() -> None:
    schema = native_prediction_json_schema()
    assert schema == json.loads((ROOT / "contracts/native-prediction.schema.json").read_text())
    names = set(schema["$defs"])
    assert not names & {
        "WorldDefinition",
        "SpringFitArtifact",
        "NativeWorldCatalog",
        "NativeStudyManifest",
    }
    assert {"PredictionRequest", "PredictionResponse", "LinearSpringModel"} <= names


def test_response_time_signed_zero_is_exact_identity_not_float_equality() -> None:
    actual = prediction_input()
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    data = result.model_dump(mode="json")
    data["payload"]["response"]["trajectory"]["frames"][0]["time"] = -0.0
    payload = NativePredictionOutcome.model_validate_json(json.dumps(data["payload"]))
    data["facts"]["output_sha256"] = message_sha256(payload)
    changed = NativePredictionResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="signed-zero"):
        validate_native_prediction_result(changed, actual, attempt_id="parent-envelope")
