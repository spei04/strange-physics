from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.prediction_contracts import (
    SpringPredictionConfig,
    SpringPredictionDiagnostics,
    SpringPredictionResult,
    prediction_json_schema,
    validate_spring_prediction_result,
)
from strange_physics.research_contracts import LinearSpringModel, PredictionRequest, message_sha256
from strange_physics.serialization import canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/prediction.examples.json").read_text())
MODELS = (SpringPredictionConfig, SpringPredictionDiagnostics, SpringPredictionResult)


def _result_data() -> dict[str, Any]:
    return copy.deepcopy(FIXTURES["valid"]["SpringPredictionResult"])


def _inputs() -> tuple[LinearSpringModel, PredictionRequest, SpringPredictionConfig]:
    return (
        LinearSpringModel.model_validate_json(json.dumps(FIXTURES["model"])),
        PredictionRequest.model_validate_json(json.dumps(FIXTURES["request"])),
        SpringPredictionConfig(),
    )


@pytest.mark.parametrize("model", MODELS)
def test_additive_prediction_messages_round_trip_and_reject_hidden_fields(
    model: type[Message],
) -> None:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    assert model.model_validate_json(json.dumps(data)).model_dump(mode="json") == data
    data["hidden_world"] = {"linear": 4.0}
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate_json(json.dumps(data))


def test_fixed_config_canonical_bytes_and_fitter_compatibility() -> None:
    config = SpringPredictionConfig()
    assert config.model_dump(mode="json") == FIXTURES["valid"]["SpringPredictionConfig"]
    assert (
        canonical_json(config.model_dump(mode="json")) == FIXTURES["canonical_config"]["utf8_text"]
    )
    assert message_sha256(config) == FIXTURES["canonical_config"]["sha256"]
    assert config.supported_fit_config_sha256 == message_sha256(SpringFitConfig())
    assert config.supported_fitter_version == SpringFitConfig().fitter_version
    with pytest.raises(ValidationError, match="frozen"):
        config.__setattr__("max_coefficient", 5.0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("particle_count", True),
        ("anchor_count", True),
        ("connection_count", True),
        ("coordinates", True),
        ("max_reference_steps", True),
        ("max_output_frames", True),
        ("algorithm", "rk4"),
        ("time_policy", "snap-grid"),
        ("max_coefficient", 5.0),
        ("max_horizon", 10.0),
        ("max_output_frames", 2002),
        ("supported_fit_config_sha256", "f" * 64),
    ],
)
def test_fixed_profile_rejects_retuning_and_boolean_integer_fields(
    field: str, value: object
) -> None:
    data = SpringPredictionConfig().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        SpringPredictionConfig.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("group", ["schema_negative", "runtime_negative"])
def test_synthetic_negative_fixtures_fail_runtime_validation(group: str) -> None:
    models = {model.__name__: model for model in MODELS}
    for case in FIXTURES[group]:
        data = copy.deepcopy(FIXTURES["valid"][case["model"]])
        data[case["field"]] = case["value"]
        with pytest.raises(ValidationError):
            models[case["model"]].model_validate_json(json.dumps(data))


def test_generated_schema_and_actual_input_binder() -> None:
    assert (
        json.loads((ROOT / "contracts/prediction.schema.json").read_text())
        == prediction_json_schema()
    )
    for model in MODELS:
        assert prediction_json_schema()["$defs"][model.__name__]["additionalProperties"] is False
    result = SpringPredictionResult.model_validate_json(json.dumps(_result_data()))
    validate_spring_prediction_result(result, *_inputs())
    assert result.response is not None
    assert result.response.schema_version == "strange-physics.prediction-response.v1"


@pytest.mark.parametrize(
    "field", ["actual_model_sha256", "request_sha256", "prediction_config_sha256"]
)
def test_asserted_digest_strings_cannot_replace_binding_actual_inputs(field: str) -> None:
    data = _result_data()
    data["diagnostics"][field] = "f" * 64
    if field == "actual_model_sha256":
        data["diagnostics"]["requested_model_sha256"] = "f" * 64
        data["response"]["model_sha256"] = "f" * 64
    result = SpringPredictionResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="actual model, request and configuration"):
        validate_spring_prediction_result(result, *_inputs())


def test_result_binder_rejects_changed_request_times_even_if_request_digest_is_updated() -> None:
    model, request, config = _inputs()
    request_data = request.model_dump(mode="json")
    request_data["times"] = [0.0, 1.0]
    changed = PredictionRequest.model_validate_json(json.dumps(request_data))
    data = _result_data()
    data["diagnostics"]["request_sha256"] = message_sha256(changed)
    result = SpringPredictionResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="times must exactly"):
        validate_spring_prediction_result(result, model, changed, config)


def test_numerical_failure_retains_complete_manifest_without_a_partial_response() -> None:
    data = _result_data()
    data.update(status="numerical_failure", reason="nonfinite_state", response=None)
    data["diagnostics"].update(computed_frame_count=1, returned_frame_count=0, failed_frame_index=1)
    result = SpringPredictionResult.model_validate_json(json.dumps(data))
    validate_spring_prediction_result(result, *_inputs())
    json.dumps(result.model_dump(mode="json"), allow_nan=False)
    assert result.diagnostics.requested_frame_count == 2
    data["response"] = FIXTURES["valid"]["SpringPredictionResult"]["response"]
    with pytest.raises(ValidationError, match="partial or fallback"):
        SpringPredictionResult.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    ("computed", "returned", "failed"), [(2, 0, 1), (1, 1, 1), (1, 0, None), (0, 0, 2)]
)
def test_failed_frame_count_relationships_cannot_hide_missing_output(
    computed: int,
    returned: int,
    failed: int | None,
) -> None:
    data = _result_data()
    data.update(status="numerical_failure", reason="arithmetic_failure", response=None)
    data["diagnostics"].update(
        computed_frame_count=computed,
        returned_frame_count=returned,
        failed_frame_index=failed,
    )
    with pytest.raises(ValidationError):
        SpringPredictionResult.model_validate_json(json.dumps(data))


def test_model_mismatch_keeps_actual_and_requested_identities_distinct() -> None:
    model, request, config = _inputs()
    request_data = request.model_dump(mode="json")
    request_data["model_sha256"] = "f" * 64
    changed = PredictionRequest.model_validate_json(json.dumps(request_data))
    data = _result_data()
    data.update(status="model_mismatch", reason="model_digest_mismatch", response=None)
    data["diagnostics"].update(
        requested_model_sha256="f" * 64,
        request_sha256=message_sha256(changed),
        computed_frame_count=0,
        returned_frame_count=0,
    )
    result = SpringPredictionResult.model_validate_json(json.dumps(data))
    validate_spring_prediction_result(result, model, changed, config)
    data["status"], data["reason"] = "unsupported_domain", "unsupported_topology"
    with pytest.raises(ValidationError, match="mismatch status"):
        SpringPredictionResult.model_validate_json(json.dumps(data))


def test_preflight_failure_cannot_claim_any_propagated_frames() -> None:
    data = _result_data()
    data.update(status="unsupported_domain", reason="coefficient_outside_domain", response=None)
    data["diagnostics"].update(computed_frame_count=1, returned_frame_count=0)
    with pytest.raises(ValidationError, match="precede any propagation"):
        SpringPredictionResult.model_validate_json(json.dumps(data))
