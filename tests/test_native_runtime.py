from __future__ import annotations

import copy
import json
import math
from typing import Any

import pytest
from pydantic import ValidationError
from test_native_spring_contracts import inputs, selection
from test_prediction import COEFFICIENTS, COMPONENT_ATOL, GRIDS, MASSES, _labels, _request

import strange_physics.native_candidates as candidates
import strange_physics.native_prediction as prediction
from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import ExperimentSpace, Vector
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionResult,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.prediction import _NonfiniteState, _state_at_time, predict_linear_spring
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import LinearSpringModel, PredictionRequest, message_sha256
from strange_physics.study_contracts import NativeWorkFacts as StudyWorkFacts


def prediction_input(coefficient: float = 1.0, **kwargs: Any) -> NativePredictionInput:
    actual = inputs((coefficient,))
    produced = produce_native_candidates(actual, attempt_id="parent-envelope")
    model = produced.payload.models[0]
    return NativePredictionInput(
        model=model,
        candidate_config=actual.config,
        config=NativePredictionConfig(),
        request=_request(model, **kwargs),
    )


def assert_prediction(actual: NativePredictionInput, result: NativePredictionResult) -> None:
    p = result.payload
    assert p.status == "predicted" and p.reason is None and p.response is not None
    validate_native_prediction_result(result, actual, attempt_id="parent-envelope")
    assert p.requested_frame_count == p.computed_frame_count == p.returned_frame_count
    assert result.facts.failed_count == result.facts.not_assessed_count == 0
    assert tuple(f.time for f in p.response.trajectory.frames) == actual.request.times
    for frame, (position, velocity) in zip(
        p.response.trajectory.frames, _labels(actual.model.linear, actual.request), strict=True
    ):
        assert (
            max(abs(a - b) for a, b in zip(frame.positions[0], position, strict=True))
            <= COMPONENT_ATOL
        )
        assert (
            max(abs(a - b) for a, b in zip(frame.velocities[0], velocity, strict=True))
            <= COMPONENT_ATOL
        )


def test_actual_production_selection_prediction_and_ledger_facts_without_map_claim() -> None:
    actual = inputs()
    produced = produce_native_candidates(actual, attempt_id="parent-envelope")
    validate_native_candidate_result(produced, actual, attempt_id="parent-envelope")
    selected = selection(produced, 1)
    validate_selected_native_candidate(selected, produced, actual, attempt_id="parent-envelope")
    assert selected.selection_claim == "selected-candidate-only"
    assert produced.payload.completed_record_indices == (0,)
    assert produced.payload.failed_record_count == 1
    assert tuple(m.linear for m in produced.payload.models) == actual.pool.coefficients
    native = NativePredictionInput(
        model=selected.model,
        candidate_config=actual.config,
        config=NativePredictionConfig(),
        request=_request(selected.model),
    )
    result = predict_native_spring(native, attempt_id="parent-envelope")
    assert_prediction(native, result)
    for facts in (produced.facts, result.facts):
        ledger_facts = StudyWorkFacts.model_validate_json(facts.model_dump_json())
        assert message_sha256(ledger_facts) == message_sha256(facts)
    old = predict_linear_spring(selected.model, native.request, SpringPredictionConfig())
    assert old.status == "unsupported_runtime" and old.reason == "unsupported_fitter_version"


@pytest.mark.parametrize("count", [1, 1025])
def test_full_declared_pool_and_twelve_record_prefix_are_bounded(count: int) -> None:
    data = inputs(tuple(i * 4 / max(1, count - 1) for i in range(count))).model_dump(mode="json")
    base = data["observations"]["records"]
    rows = []
    for index in range(12):
        row = copy.deepcopy(base[index % 2])
        row["index"], row["operation_id"] = index, f"op-{index}"
        rows.append(row)
    data["observations"]["records"] = rows
    data["observations"]["space"]["budget"] = 12
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    result = produce_native_candidates(actual, attempt_id="a")
    assert len(result.payload.models) == count
    assert result.payload.completed_record_indices == tuple(range(0, 12, 2))
    assert result.payload.failed_record_count == 6
    assert bounded_canonical(result, 4 * 1024 * 1024)[1] < 1024 * 1024


@pytest.mark.parametrize("failed_only", [False, True])
def test_empty_or_all_failed_prefix_has_no_fabricated_candidate(failed_only: bool) -> None:
    data = inputs().model_dump(mode="json")
    rows = data["observations"]["records"]
    data["observations"]["records"] = [dict(rows[1], index=0)] if failed_only else []
    result = produce_native_candidates(
        NativeCandidateInput.model_validate_json(json.dumps(data)), attempt_id="a"
    )
    assert result.payload.reason == "no_completed_records" and not result.payload.models
    assert result.facts.completed_count == result.facts.failed_count == 0
    assert result.facts.not_assessed_count == 3


@pytest.mark.parametrize("index", [0, 1, 2])
def test_construction_failure_accounts_prefix_without_returning_partial_candidates(
    index: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = inputs()
    original = LinearSpringModel
    calls = 0

    def fail(**kwargs: Any) -> LinearSpringModel:
        nonlocal calls
        attempt = calls
        calls += 1
        if attempt == index:
            raise ValueError("private diagnostic must not escape")
        return original(**kwargs)

    monkeypatch.setattr(candidates, "LinearSpringModel", fail)
    result = produce_native_candidates(actual, attempt_id="a")
    assert calls == index + 1
    assert result.payload.status == "failed" and not result.payload.models
    assert result.payload.failed_candidate_index == index
    assert (
        result.facts.completed_count,
        result.facts.failed_count,
        result.facts.not_assessed_count,
    ) == (index, 1, 2 - index)
    assert "private diagnostic" not in result.model_dump_json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("mass", 2.1),
        ("mass", 0.49),
        ("position", [2.1, 0.0]),
        ("velocity", [2.1, 0.0]),
        ("impulse", [1.1, 0.0]),
        ("anchor", [0.51, 0.0]),
    ],
)
@pytest.mark.parametrize("record_index", [0, 1])
def test_unsupported_purchased_domain_checks_failed_records_before_any_construction(
    field: str, value: Any, record_index: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = inputs().model_dump(mode="json")
    space = data["observations"]["space"]
    space["limits"].update(
        min_mass=0.1, max_mass=4.0, position_norm=4.0, velocity_norm=4.0, impulse_norm=4.0
    )
    row = data["observations"]["records"][record_index]
    if field == "anchor":
        space["structure"]["anchors"][0]["position"] = value
    elif field == "impulse":
        row["experiment"]["impulse"] = {
            "particle_id": row["experiment"]["particles"][0]["id"],
            "vector": value,
        }
    else:
        row["experiment"]["particles"][0][field] = value
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))

    def forbidden(**kwargs: Any) -> LinearSpringModel:
        raise AssertionError("preflight must precede construction")

    monkeypatch.setattr(candidates, "LinearSpringModel", forbidden)
    result = produce_native_candidates(actual, attempt_id="a")
    assert result.payload.reason == "unsupported_domain"
    assert result.facts.not_assessed_count == 3


def test_noisy_input_is_provenance_and_not_a_fitted_or_stationarity_claim() -> None:
    actual = inputs()
    data = actual.model_dump(mode="json")
    data["observations"]["space"]["sampling"]["position_noise"] = 0.1
    noisy = NativeCandidateInput.model_validate_json(json.dumps(data))
    first, second = [produce_native_candidates(v, attempt_id="a") for v in (actual, noisy)]
    assert second.payload.status == "produced"
    assert first.payload.pool_sha256 == second.payload.pool_sha256
    assert first.payload.observation_sha256 != second.payload.observation_sha256
    assert first.payload.models[0].linear == second.payload.models[0].linear


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
@pytest.mark.parametrize("mass", MASSES)
@pytest.mark.parametrize("probe", range(8))
def test_native_candidate_pipeline_matches_independent_decimal_oracle(
    coefficient: float, mass: float, probe: int
) -> None:
    actual = prediction_input(coefficient, mass=mass, probe=probe)
    assert_prediction(actual, predict_native_spring(actual, attempt_id="parent-envelope"))


@pytest.mark.parametrize("coefficient", [math.ulp(0.0), 1e-320, 1e-300])
@pytest.mark.parametrize("mass", MASSES)
@pytest.mark.parametrize("probe", [0, 5])
def test_native_tiny_coefficient_and_division_underflow(
    coefficient: float, mass: float, probe: int
) -> None:
    actual = prediction_input(coefficient, mass=mass, probe=probe)
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert_prediction(actual, result)
    assert actual.model.linear == coefficient


@pytest.mark.parametrize("times,dt", GRIDS)
def test_native_exact_requested_grid(times: tuple[float, ...], dt: float) -> None:
    actual = prediction_input(4.0, times=times, dt=dt)
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert_prediction(actual, result)
    assert bounded_canonical(result, 4 * 1024 * 1024)[1] < 1024 * 1024


def test_counterfactual_radius_three_and_reversed_edge_are_not_purchase_validation() -> None:
    actual = prediction_input()
    space_data = inputs().observations.space.model_dump(mode="json")
    space_data["structure"] = actual.request.structure.model_dump(mode="json")
    space = ExperimentSpace.model_validate_json(json.dumps(space_data))
    with pytest.raises(ValueError, match="radius"):
        space.validate_experiment(actual.request.experiment)
    data = actual.model_dump(mode="json")
    data["request"]["structure"]["connections"] = [{"a": "fixed", "b": "mobile"}]
    reverse = NativePredictionInput.model_validate_json(json.dumps(data))
    first, second = [
        predict_native_spring(v, attempt_id="parent-envelope") for v in (actual, reverse)
    ]
    assert_prediction(reverse, second)
    assert first.payload.response == second.payload.response
    assert first.facts.input_sha256 != second.facts.input_sha256


@pytest.mark.parametrize("with_impulse", [False, True])
def test_native_t0_preserves_signed_zero_tiny_state_and_once_only_impulse(
    with_impulse: bool,
) -> None:
    data = prediction_input(4.0).model_dump(mode="json")
    particle = data["request"]["experiment"]["particles"][0]
    particle["position"] = [-0.0, 1e-320]
    particle["velocity"] = [-0.0, -1e-320]
    data["request"]["experiment"]["impulse"] = (
        {"particle_id": "mobile", "vector": [0.5, 0.0]} if with_impulse else None
    )
    actual = NativePredictionInput.model_validate_json(json.dumps(data))
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert_prediction(actual, result)
    assert result.payload.response is not None
    frame = result.payload.response.trajectory.frames[0]
    assert math.copysign(1.0, frame.positions[0][0]) == -1
    assert frame.velocities[0][0] == (1.0 if with_impulse else -0.0)
    if not with_impulse:
        assert math.copysign(1.0, frame.velocities[0][0]) == -1


@pytest.mark.parametrize(
    "change,reason",
    [
        ("request_model", "model_digest_mismatch"),
        ("producer", "unsupported_fitter_version"),
        ("producer_config", "unsupported_fit_configuration"),
        ("coefficient", "coefficient_outside_domain"),
        ("through_index", "resource_limit"),
        ("anchor", "anchor_outside_domain"),
        ("mass", "mass_outside_domain"),
        ("position", "position_outside_domain"),
        ("velocity", "velocity_outside_domain"),
        ("impulse", "impulse_outside_domain"),
        ("horizon", "horizon_outside_domain"),
        ("topology", "unsupported_topology"),
    ],
)
def test_native_preflight_before_kernel(
    change: str, reason: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = prediction_input().model_dump(mode="json")
    if change == "request_model":
        data["request"]["model_sha256"] = "f" * 64
    elif change in {"producer", "producer_config", "coefficient", "through_index"}:
        field, value = {
            "producer": ("fitter_version", SpringPredictionConfig().supported_fitter_version),
            "producer_config": ("fit_config_sha256", "f" * 64),
            "coefficient": ("linear", 4.1),
            "through_index": ("through_index", 12),
        }[change]
        data["model"][field] = value
        data["request"]["model_sha256"] = message_sha256(
            LinearSpringModel.model_validate_json(json.dumps(data["model"]))
        )
    elif change == "anchor":
        data["request"]["structure"]["anchors"][0]["position"] = [0.51, 0.0]
    elif change == "topology":
        data["request"]["structure"]["connections"] = []
    elif change == "horizon":
        data["request"]["times"] = [0.0, 2.01]
    elif change == "impulse":
        data["request"]["experiment"]["impulse"]["vector"] = [1.1, 0.0]
    else:
        value = {"mass": 2.1, "position": [3.01, 0.0], "velocity": [2.01, 0.0]}[change]
        data["request"]["experiment"]["particles"][0][change] = value
    actual = NativePredictionInput.model_validate_json(json.dumps(data))

    def forbidden(*args: Any) -> tuple[Vector, Vector]:
        raise AssertionError("kernel must not run")

    monkeypatch.setattr(prediction, "_state_at_time", forbidden)
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert result.payload.reason == reason and result.payload.response is None
    assert result.facts.failed_count == result.facts.completed_count == 0
    assert result.facts.not_assessed_count == len(actual.request.times)


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("failure", ["arithmetic", "derived_nonfinite", "nonfinite", "bound"])
def test_native_frame_failure_first_middle_last(
    index: int, failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = prediction_input(times=(0.0, 1.0, 2.0))
    original = _state_at_time
    calls = 0

    def fail(
        model: LinearSpringModel, request: PredictionRequest, time: float
    ) -> tuple[Vector, Vector]:
        nonlocal calls
        current = calls
        calls += 1
        if current == index:
            if failure == "arithmetic":
                raise ArithmeticError("secret diagnostic")
            if failure == "derived_nonfinite":
                raise _NonfiniteState
            if failure == "nonfinite":
                return (float("nan"), 0.0), (0.0, 0.0)
            return (12.01, 0.0), (0.0, 0.0)
        return original(model, request, time)

    monkeypatch.setattr(prediction, "_state_at_time", fail)
    result = predict_native_spring(actual, attempt_id="parent-envelope")
    assert calls == index + 1
    assert result.payload.status == "numerical_failure"
    assert (
        result.payload.reason
        == {
            "arithmetic": "arithmetic_failure",
            "derived_nonfinite": "nonfinite_state",
            "nonfinite": "nonfinite_state",
            "bound": "output_bound",
        }[failure]
    )
    assert result.payload.response is None and result.payload.returned_frame_count == 0
    assert result.payload.failed_frame_index == index
    assert (
        result.facts.completed_count,
        result.facts.failed_count,
        result.facts.not_assessed_count,
    ) == (index, 1, 2 - index)
    assert "secret diagnostic" not in result.model_dump_json()


@pytest.mark.parametrize("operation", ["candidate", "prediction"])
def test_invalid_attempt_is_rejected_before_work(
    operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = prediction_input()

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("must reject the invalid identifier first")

    monkeypatch.setattr(candidates, "_supported_purchases", forbidden)
    monkeypatch.setattr(prediction, "_preflight", forbidden)
    with pytest.raises(ValidationError):
        if operation == "candidate":
            produce_native_candidates(inputs(), attempt_id="bad identifier")
        else:
            predict_native_spring(actual, attempt_id="bad identifier")


@pytest.mark.parametrize("change", ["topology", "horizon", "short_grid"])
def test_candidate_topology_horizon_and_non_simpson_sampling(change: str) -> None:
    data = inputs().model_dump(mode="json")
    space = data["observations"]["space"]
    if change == "topology":
        space["structure"]["connections"] = []
    else:
        scale = 2.0 if change == "horizon" else 0.5
        space["sampling"]["duration"] *= scale
        space["sampling"]["sample_interval"] *= scale
        space["sampling"]["dt"] *= scale
        for row in data["observations"]["records"]:
            if row["trajectory"] is not None:
                for frame in row["trajectory"]["frames"]:
                    frame["time"] *= scale
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    result = produce_native_candidates(actual, attempt_id="a")
    if change == "short_grid":
        assert result.payload.status == "produced"
    else:
        assert result.payload.reason == "unsupported_domain"


def test_candidate_producer_changes_failed_purchase_identity_but_not_common_pool() -> None:
    actual = inputs()
    data = actual.model_dump(mode="json")
    data["observations"]["records"][1]["operation_id"] = "different-failed-operation"
    other = NativeCandidateInput.model_validate_json(json.dumps(data))
    a, b = [produce_native_candidates(v, attempt_id="a") for v in (actual, other)]
    assert a.payload.pool_sha256 == b.payload.pool_sha256
    assert a.payload.models[0].fit_record_indices == b.payload.models[0].fit_record_indices
    assert message_sha256(a.payload.models[0]) != message_sha256(b.payload.models[0])
    with pytest.raises(ValueError, match="actual"):
        validate_native_candidate_result(a, other, attempt_id="a")


def test_zero_sign_and_retry_identity_are_preserved_by_actual_producer() -> None:
    negative = produce_native_candidates(inputs((-0.0,)), attempt_id="a")
    positive = produce_native_candidates(inputs((0.0,)), attempt_id="a")
    retry = produce_native_candidates(inputs((-0.0,)), attempt_id="b")
    assert math.copysign(1.0, negative.payload.models[0].linear) == -1
    assert negative.payload.pool_sha256 != positive.payload.pool_sha256
    assert message_sha256(negative.payload.models[0]) != message_sha256(positive.payload.models[0])
    assert negative.facts.output_sha256 == retry.facts.output_sha256
    assert negative.facts.input_sha256 == retry.facts.input_sha256
    assert message_sha256(negative) != message_sha256(retry)


def test_native_kernel_parity_is_not_old_profile_admission() -> None:
    actual = prediction_input(4.0)
    response = predict_native_spring(actual, attempt_id="a").payload.response
    assert response is not None
    # Synthetic valid legacy model is distinct provenance, not a native adapter input.
    from test_prediction import _model

    old_model = _model(4.0)
    old_request = _request(old_model)
    legacy = predict_linear_spring(old_model, old_request, SpringPredictionConfig())
    assert legacy.response is not None
    assert response.trajectory == legacy.response.trajectory
    assert response.model_sha256 != legacy.response.model_sha256
    data = actual.model_dump(mode="json")
    data["model"] = old_model.model_dump(mode="json")
    data["request"] = old_request.model_dump(mode="json")
    foreign = NativePredictionInput.model_validate_json(json.dumps(data))
    assert (
        predict_native_spring(foreign, attempt_id="a").payload.reason
        == "unsupported_fitter_version"
    )
