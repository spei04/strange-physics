from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.fitting_contracts import (
    SpringFitConfig,
    SpringFitDiagnostics,
    SpringFitResult,
    fitting_json_schema,
    validate_fit_result,
)
from strange_physics.research_contracts import SpringFitInput, message_sha256
from strange_physics.serialization import canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/fitting.examples.json").read_text())
MODELS = (SpringFitConfig, SpringFitDiagnostics, SpringFitResult)


def result_payload() -> dict[str, Any]:
    return copy.deepcopy(FIXTURES["valid"]["SpringFitResult"])


def fit_input() -> SpringFitInput:
    return SpringFitInput.model_validate_json(json.dumps(FIXTURES["input"]))


@pytest.mark.parametrize("model", MODELS)
def test_additive_messages_round_trip_and_reject_hidden_fields(model: type[Message]) -> None:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    parsed = model.model_validate_json(json.dumps(data))
    assert parsed.model_dump(mode="json") == data
    data["hidden_world"] = {"linear": 0.5}
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate_json(json.dumps(data))


def test_fixed_configuration_canonical_bytes_and_digest_include_defaults() -> None:
    config = SpringFitConfig()
    vector = FIXTURES["canonical_config"]
    assert config.model_dump(mode="json") == FIXTURES["valid"]["SpringFitConfig"]
    assert canonical_json(config.model_dump(mode="json")) == vector["utf8_text"]
    assert message_sha256(config) == vector["sha256"]
    # JSON object order/whitespace are not part of the typed canonical profile.
    reordered = dict(reversed(list(config.model_dump(mode="json").items())))
    assert (
        message_sha256(SpringFitConfig.model_validate_json(json.dumps(reordered)))
        == (vector["sha256"])
    )
    with pytest.raises(ValidationError, match="frozen"):
        config.__setattr__("min_design_rms", 1e-5)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("min_design_rms", 1e-5),
        ("algorithm", "trapezoid"),
        ("duration", 1.95),
        ("sample_interval", 0.1),
        ("integration_steps", [0.01, 0.005, 0.001]),
        ("record_selection", "best-completed"),
        ("max_mass", 3.0),
        ("max_records", 10001),
        ("coefficient_policy", "clip-positive"),
        ("noise_policy", "denoise"),
    ],
)
def test_v1_settings_cannot_be_silently_retuned(field: str, value: object) -> None:
    data = SpringFitConfig().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        SpringFitConfig.model_validate_json(json.dumps(data))


def test_separate_schema_matches_models_and_does_not_change_sci_fixture() -> None:
    assert json.loads((ROOT / "contracts/fitting.schema.json").read_text()) == fitting_json_schema()
    for model in MODELS:
        assert fitting_json_schema()["$defs"][model.__name__]["additionalProperties"] is False
    result = SpringFitResult.model_validate_json(json.dumps(result_payload()))
    validate_fit_result(result, fit_input(), SpringFitConfig())
    assert result.model is not None
    assert result.model.schema_version == "strange-physics.linear-spring-model.v1"


@pytest.mark.parametrize("group", ["schema_negative", "runtime_negative"])
def test_fixture_rejections_are_enforced_by_runtime(group: str) -> None:
    models = {model.__name__: model for model in MODELS}
    for case in FIXTURES[group]:
        data = copy.deepcopy(FIXTURES["valid"][case["model"]])
        data[case["field"]] = case["value"]
        with pytest.raises(ValidationError):
            models[case["model"]].model_validate_json(json.dumps(data))


def test_actual_configuration_is_required_even_if_asserted_digests_agree() -> None:
    data = result_payload()
    data["diagnostics"]["requested_config_sha256"] = "f" * 64
    data["diagnostics"]["actual_config_sha256"] = "f" * 64
    data["model"]["fit_config_sha256"] = "f" * 64
    result = SpringFitResult.model_validate_json(json.dumps(data))
    request = copy.deepcopy(FIXTURES["input"])
    request["fit_config_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="prefix and configuration"):
        validate_fit_result(
            result, SpringFitInput.model_validate_json(json.dumps(request)), SpringFitConfig()
        )


def test_failed_prefix_records_are_bound_and_cannot_be_selected() -> None:
    result = SpringFitResult.model_validate_json(json.dumps(result_payload()))
    request = copy.deepcopy(FIXTURES["input"])
    request["observations"]["records"][1]["operation_id"] = "different-failure"
    with pytest.raises(ValueError, match="prefix and configuration"):
        validate_fit_result(
            result, SpringFitInput.model_validate_json(json.dumps(request)), SpringFitConfig()
        )
    data = result_payload()
    data["model"]["fit_record_indices"] = [1]
    data["diagnostics"]["completed_record_indices"] = [1]
    with pytest.raises(ValueError, match="prefix and configuration"):
        validate_fit_result(
            SpringFitResult.model_validate_json(json.dumps(data)), fit_input(), SpringFitConfig()
        )


def test_declared_noise_cannot_be_hidden_by_a_result() -> None:
    request = copy.deepcopy(FIXTURES["input"])
    request["observations"]["space"]["sampling"]["position_noise"] = 0.002
    request = SpringFitInput.model_validate_json(json.dumps(request))
    data = result_payload()
    data["diagnostics"]["observation_sha256"] = message_sha256(request.observations)
    data["model"]["observation_sha256"] = message_sha256(request.observations)
    with pytest.raises(ValueError, match="prefix and configuration"):
        validate_fit_result(
            SpringFitResult.model_validate_json(json.dumps(data)), request, SpringFitConfig()
        )


@pytest.mark.parametrize("coefficient", [-0.2, 4.5])
def test_raw_estimate_sign_and_calibration_range_are_explicit(coefficient: float) -> None:
    data = result_payload()
    data["diagnostics"]["raw_coefficient"] = coefficient
    data["diagnostics"]["estimated_coefficient_in_calibrated_range"] = False
    if coefficient < 0:
        data.update(status="negative_estimate", reason="negative_coefficient", model=None)
    else:
        data["model"]["linear"] = coefficient
    result = SpringFitResult.model_validate_json(json.dumps(data))
    validate_fit_result(result, fit_input(), SpringFitConfig())
    assert result.diagnostics.raw_coefficient == coefficient
    assert result.diagnostics.accuracy_claim == "none"
    assert result.diagnostics.estimated_coefficient_in_calibrated_range is False
    assert (result.model is None) == (coefficient < 0)
    json.dumps(result.model_dump(mode="json"), allow_nan=False)


def test_nonfinite_failure_has_json_safe_absence_and_retained_counts() -> None:
    data = result_payload()
    data.update(status="numerical_failure", reason="nonfinite_columns", model=None)
    data["diagnostics"].update(
        raw_coefficient=None, design_rms=None, estimated_coefficient_in_calibrated_range=None
    )
    result = SpringFitResult.model_validate_json(json.dumps(data))
    validate_fit_result(result, fit_input(), SpringFitConfig())
    assert result.diagnostics.record_count == 2
    assert result.diagnostics.failed_record_count == 1
    assert result.diagnostics.scalar_row_count == 40
    assert json.loads(result.model_dump_json())["diagnostics"]["raw_coefficient"] is None
    data["diagnostics"]["raw_coefficient"] = float("inf")
    with pytest.raises(ValidationError):
        SpringFitResult.model_validate_json(json.dumps(data))


def test_configuration_failure_cannot_contain_a_model_or_hide_digest_mismatch() -> None:
    data = result_payload()
    data.update(status="configuration_mismatch", reason="configuration_digest_mismatch", model=None)
    data["diagnostics"].update(
        requested_config_sha256="f" * 64,
        scalar_row_count=0,
        design_rms=None,
        raw_coefficient=None,
        estimated_coefficient_in_calibrated_range=None,
    )
    rejected = SpringFitResult.model_validate_json(json.dumps(data))
    assert rejected.model is None
    data["status"], data["reason"] = "unsupported_domain", "unsupported_sampling"
    with pytest.raises(ValidationError, match="Configuration status"):
        SpringFitResult.model_validate_json(json.dumps(data))


def test_insufficient_support_cannot_be_reported_as_a_fitted_model() -> None:
    data = result_payload()
    data["diagnostics"]["design_rms"] = 1e-7
    with pytest.raises(ValidationError, match="supported finite design"):
        SpringFitResult.model_validate_json(json.dumps(data))
