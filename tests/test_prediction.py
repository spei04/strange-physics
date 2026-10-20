from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext
from functools import lru_cache
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Sampling,
    Structure,
    Vector,
)
from strange_physics.fitting import fit_linear_spring
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import (
    SpringPredictionConfig,
    SpringPredictionResult,
    validate_spring_prediction_result,
)
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    SpringFitInput,
    message_sha256,
)

CONFIG = SpringPredictionConfig()
FIT_CONFIG = SpringFitConfig()
COEFFICIENTS = (0.0, 1e-8, 1e-4, 0.3, 0.9, 2.0, 4.0)
MASSES = (0.5, 1.0, 2.0)
TIMES = tuple(index * 0.05 for index in range(41))
COMPONENT_ATOL = 1e-12
FIT_PREDICT_RMSE = 0.001
U = 1 / math.sqrt(2)
PROBES: tuple[tuple[Vector, Vector, Vector, Vector | None], ...] = (
    ((-0.5, 0.0), (3.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
    ((-0.5, 0.0), (3.0, 0.0), (-2.0, 0.0), (-1.0, 0.0)),
    ((0.0, -0.5), (0.0, 3.0), (0.0, 2.0), (0.0, 1.0)),
    ((0.0, -0.5), (0.0, 3.0), (0.0, -2.0), (0.0, -1.0)),
    ((-0.5 * U, -0.5 * U), (3 * U, 3 * U), (2 * U, -2 * U), (U, -U)),
    ((0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
    ((0.0, 0.0), (1.5, 0.2), (0.3, -0.6), (0.2, 0.1)),
    ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), None),
)
State = tuple[Vector, Vector]


def _model(coefficient: float) -> LinearSpringModel:
    # Synthetic model provenance for direct propagation tests, not a fitted claim.
    return LinearSpringModel(
        linear=coefficient,
        through_index=0,
        fit_record_indices=(0,),
        observation_sha256="0" * 64,
        fitter_version=FIT_CONFIG.fitter_version,
        fit_config_sha256=message_sha256(FIT_CONFIG),
    )


def _request(
    model: LinearSpringModel,
    mass: float = 0.5,
    probe: int = 0,
    times: tuple[float, ...] = TIMES,
    dt: float = 0.01,
) -> PredictionRequest:
    anchor, position, velocity, impulse = PROBES[probe]
    return PredictionRequest(
        model_sha256=message_sha256(model),
        structure=Structure(
            particle_ids=("mobile",),
            anchors=(Anchor(id="fixed", position=anchor),),
            connections=(Connection(a="mobile", b="fixed"),),
        ),
        experiment=Experiment(
            particles=(
                ParticleInitial(id="mobile", position=position, velocity=velocity, mass=mass),
            ),
            impulse=None if impulse is None else Impulse(particle_id="mobile", vector=impulse),
        ),
        times=times,
        integration_dt=dt,
    )


@lru_cache(maxsize=512)
def _oracle(
    coefficient: float,
    mass: float,
    anchor: Vector,
    position: Vector,
    velocity: Vector,
    impulse: Vector | None,
    times: tuple[float, ...],
) -> tuple[State, ...]:
    # Independent ODE power series, not production cos/sinc or a simulator helper.
    # Exact binary inputs enter Decimal; the 80-term/80-digit policy is preregistered.
    with localcontext() as context:
        context.prec = 80
        decimal = Decimal.from_float
        a = decimal(coefficient) / decimal(mass)
        series = []
        for coordinate in range(2):
            initial_velocity = decimal(velocity[coordinate])
            if impulse is not None:
                initial_velocity += decimal(impulse[coordinate]) / decimal(mass)
            coefficients = [
                decimal(position[coordinate]) - decimal(anchor[coordinate]),
                initial_velocity,
            ]
            for index in range(78):
                coefficients.append(-a * coefficients[index] / ((index + 2) * (index + 1)))
            series.append(coefficients)
        states = []
        for time in times:
            positions, velocities = [], []
            t = decimal(time)
            for coordinate in range(2):
                coefficients = series[coordinate]
                displacement = coefficients[-1]
                derivative = Decimal(79) * coefficients[-1]
                for index in range(78, -1, -1):
                    displacement = displacement * t + coefficients[index]
                    if index:
                        derivative = derivative * t + Decimal(index) * coefficients[index]
                positions.append(float(decimal(anchor[coordinate]) + displacement))
                velocities.append(float(derivative))
            states.append(((positions[0], positions[1]), (velocities[0], velocities[1])))
        return tuple(states)


def _labels(coefficient: float, request: PredictionRequest) -> tuple[State, ...]:
    particle = request.experiment.particles[0]
    return _oracle(
        coefficient,
        particle.mass,
        request.structure.anchors[0].position,
        particle.position,
        particle.velocity,
        None if request.experiment.impulse is None else request.experiment.impulse.vector,
        request.times,
    )


def _assert_response(
    result: SpringPredictionResult,
    model: LinearSpringModel,
    request: PredictionRequest,
) -> None:
    assert result.status == "predicted" and result.response is not None
    assert tuple(frame.time for frame in result.response.trajectory.frames) == request.times
    assert result.diagnostics.computed_frame_count == len(request.times)
    assert result.diagnostics.returned_frame_count == len(request.times)
    assert result.diagnostics.failed_frame_index is None
    assert result.diagnostics.accuracy_claim == "none"
    parsed = SpringPredictionResult.model_validate_json(
        json.dumps(result.model_dump(mode="json"), allow_nan=False)
    )
    validate_spring_prediction_result(parsed, model, request, CONFIG)
    assert parsed == result


def _component_errors(
    coefficient: float,
    request: PredictionRequest,
    result: SpringPredictionResult,
) -> tuple[float, float]:
    assert result.response is not None
    expected = _labels(coefficient, request)
    position_error, velocity_error = 0.0, 0.0
    for frame, (position, velocity) in zip(
        result.response.trajectory.frames, expected, strict=True
    ):
        for coordinate in range(2):
            position_error = max(
                position_error, abs(frame.positions[0][coordinate] - position[coordinate])
            )
            velocity_error = max(
                velocity_error, abs(frame.velocities[0][coordinate] - velocity[coordinate])
            )
    return position_error, velocity_error


def test_oracle_zero_stiffness_and_initial_impulse_self_checks() -> None:
    model = _model(0.0)
    request = _request(model, 0.5, 0, (0.0, 2.0))
    assert _labels(0.0, request) == (((3.0, 0.0), (4.0, 0.0)), ((11.0, 0.0), (4.0, 0.0)))
    assert _labels(4.0, request)[0] == ((3.0, 0.0), (4.0, 0.0))


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
@pytest.mark.parametrize("mass", MASSES)
@pytest.mark.parametrize("probe", range(8))
def test_preregistered_independent_analytic_prediction(
    coefficient: float,
    mass: float,
    probe: int,
) -> None:
    model = _model(coefficient)
    request = _request(model, mass, probe)
    result = predict_linear_spring(model, request, CONFIG)
    _assert_response(result, model, request)
    position_error, velocity_error = _component_errors(coefficient, request, result)
    assert position_error <= COMPONENT_ATOL
    assert velocity_error <= COMPONENT_ATOL


@pytest.mark.parametrize("coefficient", [math.ulp(0.0), 1e-320, 1e-300])
@pytest.mark.parametrize("mass", MASSES)
@pytest.mark.parametrize("probe", [0, 5])
def test_preregistered_near_zero_and_division_underflow(
    coefficient: float,
    mass: float,
    probe: int,
) -> None:
    model = _model(coefficient)
    before = model.model_dump_json()
    request = _request(model, mass, probe)
    result = predict_linear_spring(model, request, CONFIG)
    _assert_response(result, model, request)
    assert model.model_dump_json() == before
    assert max(_component_errors(coefficient, request, result)) <= COMPONENT_ATOL
    if coefficient == math.ulp(0.0) and mass == 2:
        assert coefficient > 0 and coefficient / mass == 0


DENSE = tuple(index * 0.001 for index in range(2001))
GRIDS = (
    ((0.0, 0.03, 0.11, 0.29, 0.75, 1.37, 2.0), 0.01),
    ((0.0, 0.0001), 0.0001),
    (DENSE, 0.0001),
    ((DENSE[0], *DENSE[1:2000:2], DENSE[-1]), 0.0001),
    ((0.0, 0.15 + 2e-11, 2.0), 0.01),
)


@pytest.mark.parametrize(
    ("times", "dt"),
    GRIDS,
    ids=["irregular", "short", "max-frames", "nonuniform-dense", "exact-float"],
)
def test_preregistered_grids_preserve_and_evaluate_exact_requested_times(
    times: tuple[float, ...],
    dt: float,
) -> None:
    model = _model(4.0)
    request = _request(model, times=times, dt=dt)
    result = predict_linear_spring(model, request, CONFIG)
    _assert_response(result, model, request)
    assert max(_component_errors(4.0, request, result)) <= COMPONENT_ATOL


def test_reference_step_metadata_does_not_change_shared_time_trajectories() -> None:
    model = _model(4.0)
    responses = [
        predict_linear_spring(model, _request(model, dt=dt), CONFIG) for dt in (0.01, 0.005, 0.0025)
    ]
    assert all(result.response == responses[0].response for result in responses)
    assert len({result.diagnostics.request_sha256 for result in responses}) == 3


def test_time_zero_preserves_tiny_initial_position_and_impulse_exactly_once() -> None:
    model = _model(4.0)
    data = _request(model).model_dump(mode="json")
    data["experiment"]["particles"][0]["position"] = [1e-320, -1e-320]
    data["experiment"]["particles"][0]["velocity"] = [-0.25, 0.5]
    data["experiment"]["impulse"]["vector"] = [0.25, -0.5]
    request = PredictionRequest.model_validate_json(json.dumps(data))
    result = predict_linear_spring(model, request, CONFIG)
    _assert_response(result, model, request)
    assert result.response is not None
    first = result.response.trajectory.frames[0]
    assert first.positions == ((1e-320, -1e-320),)
    assert first.velocities == ((0.25, -0.5),)


def test_reversing_valid_connection_preserves_prediction_and_radius_three_is_supported() -> None:
    model = _model(0.9)
    request = _request(model)
    original = predict_linear_spring(model, request, CONFIG)
    data = request.model_dump(mode="json")
    data["structure"]["connections"] = [{"a": "fixed", "b": "mobile"}]
    reversed_request = PredictionRequest.model_validate_json(json.dumps(data))
    changed = predict_linear_spring(model, reversed_request, CONFIG)
    _assert_response(changed, model, reversed_request)
    assert original.response == changed.response
    assert math.hypot(*request.experiment.particles[0].position) == 3.0


def test_public_identity_and_time_errors_are_rejected_before_prediction() -> None:
    model = _model(0.9)
    base = _request(model).model_dump(mode="json")
    cases: list[dict[str, Any]] = []
    for times in ([0.0, 0.1, 0.05], [0.0, 0.01, 0.010000000001]):
        cases.append(dict(base, times=times))
    data = json.loads(json.dumps(base))
    data["experiment"]["particles"][0]["id"] = "wrong"
    data["experiment"]["impulse"]["particle_id"] = "wrong"
    cases.append(data)
    data = json.loads(json.dumps(base))
    data["structure"]["particle_ids"] = ["mobile", "other"]
    data["experiment"]["particles"].append(dict(data["experiment"]["particles"][0], id="other"))
    data["experiment"]["particles"].reverse()
    cases.append(data)
    for data in cases:
        with pytest.raises(ValidationError):
            PredictionRequest.model_validate_json(json.dumps(data))


def _rejected(
    model: LinearSpringModel,
    request: PredictionRequest,
    status: str,
    reason: str,
) -> None:
    result = predict_linear_spring(model, request, CONFIG)
    assert result.status == status and result.reason == reason
    assert result.response is None and result.diagnostics.returned_frame_count == 0
    assert result.diagnostics.computed_frame_count == 0
    assert result.diagnostics.failed_frame_index is None
    validate_spring_prediction_result(result, model, request, CONFIG)
    json.dumps(result.model_dump(mode="json"), allow_nan=False)


def test_model_hash_precedes_runtime_and_domain_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    model_data = _model(1e308).model_dump(mode="json")
    model_data["fitter_version"] = "unsupported"
    model = LinearSpringModel.model_validate_json(json.dumps(model_data))
    data = _request(model).model_dump(mode="json")
    data["model_sha256"] = "f" * 64
    request = PredictionRequest.model_validate_json(json.dumps(data))

    def forbidden(*args: object) -> float:
        pytest.fail("preflight failure must not call trigonometry")

    monkeypatch.setattr(math, "cos", forbidden)
    _rejected(model, request, "model_mismatch", "model_digest_mismatch")
    data["model_sha256"] = message_sha256(model)
    _rejected(
        model,
        PredictionRequest.model_validate_json(json.dumps(data)),
        "unsupported_runtime",
        "unsupported_fitter_version",
    )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("fitter_version", "other-fitter.v1", "unsupported_fitter_version"),
        ("fit_config_sha256", "f" * 64, "unsupported_fit_configuration"),
    ],
)
def test_runtime_compatibility_uses_model_metadata(field: str, value: str, reason: str) -> None:
    data = _model(0.9).model_dump(mode="json")
    data[field] = value
    model = LinearSpringModel.model_validate_json(json.dumps(data))
    _rejected(model, _request(model), "unsupported_runtime", reason)


@pytest.mark.parametrize("coefficient", [4.0001, 1e308])
def test_finite_above_domain_models_fail_before_propagation(
    coefficient: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model(coefficient)

    def forbidden(*args: object) -> float:
        pytest.fail("unsupported coefficient must not enter propagation")

    monkeypatch.setattr(math, "sqrt", forbidden)
    _rejected(model, _request(model), "unsupported_domain", "coefficient_outside_domain")


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("topology", "unsupported_topology"),
        ("anchor", "anchor_outside_domain"),
        ("mass-low", "mass_outside_domain"),
        ("mass-high", "mass_outside_domain"),
        ("position", "position_outside_domain"),
        ("velocity", "velocity_outside_domain"),
        ("impulse", "impulse_outside_domain"),
        ("horizon", "horizon_outside_domain"),
        ("huge-position", "position_outside_domain"),
    ],
)
def test_valid_public_request_can_be_outside_scientific_domain(case: str, reason: str) -> None:
    model = _model(0.9)
    data = _request(model).model_dump(mode="json")
    particle = data["experiment"]["particles"][0]
    if case == "topology":
        data["structure"]["connections"] = []
    elif case == "anchor":
        data["structure"]["anchors"][0]["position"] = [0.51, 0.0]
    elif case.startswith("mass"):
        particle["mass"] = 0.49 if case == "mass-low" else 2.01
    elif case == "position":
        particle["position"] = [3.01, 0.0]
    elif case == "huge-position":
        particle["position"] = [1e308, 1e308]
    elif case == "velocity":
        particle["velocity"] = [2.01, 0.0]
    elif case == "impulse":
        data["experiment"]["impulse"]["vector"] = [1.01, 0.0]
    else:
        data["times"] = [0.0, 2.01]
    _rejected(
        model,
        PredictionRequest.model_validate_json(json.dumps(data)),
        "unsupported_domain",
        reason,
    )


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("nonfinite", "nonfinite_state"),
        ("exception", "arithmetic_failure"),
        ("divergent", "output_bound"),
    ],
)
def test_numerical_fault_after_frame_zero_retains_failure_counts_without_partial_output(
    fault: str,
    reason: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model(4.0)
    request = _request(model)

    def broken_cosine(value: float) -> float:
        if fault == "exception":
            raise ValueError("private diagnostic text must not escape")
        return math.nan if fault == "nonfinite" else 1000.0

    monkeypatch.setattr(math, "cos", broken_cosine)
    result = predict_linear_spring(model, request, CONFIG)
    assert result.status == "numerical_failure" and result.reason == reason
    assert result.response is None
    assert result.diagnostics.requested_frame_count == 41
    assert result.diagnostics.computed_frame_count == result.diagnostics.failed_frame_index == 1
    assert result.diagnostics.returned_frame_count == 0
    encoded = json.dumps(result.model_dump(mode="json"), allow_nan=False)
    assert "private diagnostic text" not in encoded
    validate_spring_prediction_result(result, model, request, CONFIG)


def _purchased_prefix(
    coefficient: float, masses: tuple[float, ...], dt: float
) -> ObservationBundle:
    # Fixed SP-03.b synthetic purchases. Hidden truth is test setup only.
    from strange_physics.laws import SpringLaw, SpringParameters
    from strange_physics.simulation import simulate

    anchor = (0.25, -0.4)
    rows: tuple[tuple[Vector, Vector, Vector | None], ...] = (
        ((0.7, 0.2), (-0.2, 0.3), None),
        ((-0.6, 0.5), (0.4, -0.1), (0.3, 0.4)),
        ((1.2, -0.3), (0.0, 0.5), None),
        ((-0.3, -1.0), (-0.4, 0.2), (-0.4, 0.3)),
    )
    space = ExperimentSpace(
        structure=Structure(
            particle_ids=("p",),
            anchors=(Anchor(id="a", position=anchor),),
            connections=(Connection(a="p", b="a"),),
        ),
        sampling=Sampling(dt=dt),
        budget=4,
        calibration_experiments=0,
    )
    records = []
    for index, ((displacement, velocity, impulse), mass) in enumerate(
        zip(rows, masses, strict=True)
    ):
        experiment = Experiment(
            particles=(
                ParticleInitial(
                    id="p",
                    position=(anchor[0] + displacement[0], anchor[1] + displacement[1]),
                    velocity=velocity,
                    mass=mass,
                ),
            ),
            impulse=None if impulse is None else Impulse(particle_id="p", vector=impulse),
        )
        observed = simulate(
            space,
            experiment,
            SpringLaw(SpringParameters(linear=coefficient)),
            noise_seed=0,
            experiment_index=index,
        )
        records.append(
            ExperimentRecord(
                index=index,
                operation_id=f"purchase-{index}",
                experiment=experiment,
                status="completed",
                trajectory=observed,
            )
        )
    return ObservationBundle(
        run_id="synthetic-production-fit-predict",
        engine_version="test-only-noiseless-rk4",
        engine_fingerprint="0" * 64,
        space=space,
        records=tuple(records),
    )


FIT_CASES = tuple(
    (coefficient, (mass,) * 4, dt)
    for coefficient in COEFFICIENTS
    for mass in MASSES
    for dt in (0.01, 0.005, 0.0025)
) + tuple((coefficient, (0.5, 1.0, 2.0, 0.5), 0.01) for coefficient in COEFFICIENTS)


@pytest.mark.parametrize(("coefficient", "masses", "dt"), FIT_CASES)
def test_production_fit_to_unseen_prediction_meets_each_probe_bound(
    coefficient: float,
    masses: tuple[float, ...],
    dt: float,
) -> None:
    prefix = _purchased_prefix(coefficient, masses, dt)
    fit = fit_linear_spring(
        SpringFitInput(
            observations=prefix,
            through_index=3,
            fit_config_sha256=message_sha256(FIT_CONFIG),
        ),
        FIT_CONFIG,
    )
    assert fit.status == "fitted" and fit.model is not None
    assert fit.model.fit_record_indices == (0, 1, 2, 3)
    assert fit.diagnostics.scalar_row_count == 160
    probe_count = 0
    for mass in MASSES:
        for probe in range(8):
            request = _request(fit.model, mass, probe)
            prediction = predict_linear_spring(fit.model, request, CONFIG)
            _assert_response(prediction, fit.model, request)
            assert prediction.response is not None
            labels = _labels(coefficient, request)
            squared_errors = [
                (frame.positions[0][coordinate] - expected[0][coordinate]) ** 2
                for frame, expected in zip(
                    prediction.response.trajectory.frames, labels, strict=True
                )
                for coordinate in range(2)
            ]
            assert len(squared_errors) == 82
            assert math.sqrt(math.fsum(squared_errors) / 82) <= FIT_PREDICT_RMSE
            probe_count += 1
    assert probe_count == 24


def test_no_impulse_preserves_signed_initial_velocity_at_frame_zero() -> None:
    model = _model(0.9)
    data = _request(model, probe=7).model_dump(mode="json")
    data["experiment"]["particles"][0]["velocity"] = [-0.0, -1e-320]
    request = PredictionRequest.model_validate_json(json.dumps(data))
    result = predict_linear_spring(model, request, CONFIG)
    assert result.response is not None
    velocity = result.response.trajectory.frames[0].velocities[0]
    assert velocity == (-0.0, -1e-320)
    assert math.copysign(1.0, velocity[0]) == -1.0
