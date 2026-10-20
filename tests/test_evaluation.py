from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import evaluation
from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    Frame,
    Impulse,
    Message,
    ParticleInitial,
    Structure,
    Trajectory,
)
from strange_physics.evaluation import evaluate_spring_predictions
from strange_physics.evaluation_contracts import (
    ProbePrediction,
    ReferenceProbe,
    SpringEvaluationProbe,
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    validate_spring_evaluation_result,
)
from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
)
from strange_physics.worlds import WorldDefinition, reference_world

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts/prediction.examples.json").read_text()
)


def changed[T: Message](value: T, **fields: Any) -> T:
    return type(value).model_validate_json(json.dumps(value.model_dump(mode="json") | fields))


def model(k: float = 0.0) -> LinearSpringModel:
    return changed(LinearSpringModel.model_validate_json(json.dumps(FIXTURE["model"])), linear=k)


def world(k: float = 0.0) -> WorldDefinition:
    original = reference_world("spring", particles=1, budget=4, changed=False, noise=0.0)
    return changed(
        original, initial_law={"kind": "spring", "parameters": {"linear": k, "cubic": 0.0}}
    )


def request(
    fitted: LinearSpringModel,
    *,
    times: tuple[float, ...] = (0.0, 1.0),
    mass: float = 1.0,
    anchor: tuple[float, float] = (0.0, 0.0),
    position: tuple[float, float] = (0.0, 0.0),
    velocity: tuple[float, float] = (0.0, 0.0),
    impulse: tuple[float, float] | None = None,
    dt: float = 0.01,
) -> PredictionRequest:
    return PredictionRequest(
        model_sha256=message_sha256(fitted),
        structure=Structure(
            particle_ids=("mobile",),
            anchors=(Anchor(id="anchor", position=anchor),),
            connections=(Connection(a="mobile", b="anchor"),),
        ),
        experiment=Experiment(
            particles=(
                ParticleInitial(id="mobile", mass=mass, position=position, velocity=velocity),
            ),
            impulse=None if impulse is None else Impulse(particle_id="mobile", vector=impulse),
        ),
        times=times,
        integration_dt=dt,
    )


def protocol(
    fitted: LinearSpringModel,
    requests: tuple[PredictionRequest, ...],
    scale: float = 1.0,
) -> SpringEvaluationProtocol:
    return SpringEvaluationProtocol(
        model_sha256=message_sha256(fitted),
        normalization_scale=scale,
        probes=tuple(
            SpringEvaluationProbe(
                probe_id=f"probe-{i}", request=item, request_sha256=message_sha256(item)
            )
            for i, item in enumerate(requests)
        ),
    )


def responses(
    plan: SpringEvaluationProtocol,
    positions: tuple[tuple[tuple[float, float], ...], ...] | None = None,
) -> tuple[ProbePrediction, ...]:
    return tuple(
        ProbePrediction(
            probe_id=probe.probe_id,
            request_sha256=probe.request_sha256,
            status="response",
            response=PredictionResponse(
                model_sha256=probe.request.model_sha256,
                trajectory=Trajectory(
                    frames=tuple(
                        Frame(time=t, positions=(xy,), velocities=((0.0, 0.0),))
                        for t, xy in zip(
                            probe.request.times,
                            ((0.0, 0.0),) * len(probe.request.times)
                            if positions is None
                            else positions[index],
                            strict=True,
                        )
                    )
                ),
            ),
        )
        for index, probe in enumerate(plan.probes)
    )


def fixture(
    count: int = 1,
) -> tuple[
    LinearSpringModel, SpringEvaluationProtocol, tuple[ProbePrediction, ...], WorldDefinition
]:
    fitted = model()
    plan = protocol(fitted, (request(fitted),) * count)
    return fitted, plan, responses(plan), world()


def assert_serializable(result: SpringEvaluationResult) -> None:
    json.dumps(result.model_dump(mode="json"), allow_nan=False)
    assert (
        result.diagnostics.valid_prediction_count
        + result.diagnostics.failed_prediction_count
        + result.diagnostics.prediction_not_assessed_count
        == len(result.probes)
    )
    if result.report is not None:
        assert message_sha256(result.report) == result.report_sha256


def test_hand_calculated_macro_mean_uses_each_grid_then_equal_probes() -> None:
    fitted = model()
    plan = protocol(
        fitted,
        (
            request(fitted),
            request(fitted, times=(0.0, 0.2, 1.0)),
        ),
        scale=2.0,
    )
    entries = responses(plan, (((1.0, 3.0), (1.0, 3.0)), ((0.0, 0.0), (2.0, 0.0), (4.0, 0.0))))
    result = evaluate_spring_predictions(fitted, plan, entries, world())
    assert result.status == "scored" and result.report is not None
    assert result.probes[0].position_mse == 5.0
    assert result.probes[1].position_mse == pytest.approx(10 / 3)
    assert result.report.position_mse == pytest.approx(25 / 6)
    assert result.report.normalized_position_mse == pytest.approx(25 / 24)
    assert result.report.position_mse != 4.0  # Pooling all frames would overweight probe two.
    assert_serializable(result)


def test_zero_error_and_actual_input_binding() -> None:
    values = fixture(3)
    result = evaluate_spring_predictions(*values)
    assert result.status == "scored" and result.report is not None
    assert result.report.position_mse == result.report.normalized_position_mse == 0.0
    assert all(item.position_mse == 0.0 for item in result.probes)
    validate_spring_evaluation_result(result, *values)
    assert_serializable(result)


@pytest.mark.parametrize(
    "case",
    ["missing", "all_missing", "failed", "invalid", "wrong_model", "wrong_times", "wrong_shape"],
)
def test_every_failed_prediction_is_counted_without_scoring_survivors(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fitted, plan, entries, truth = fixture(3)
    items = list(entries)
    if case == "missing":
        items.pop(1)
    elif case == "all_missing":
        items = []
    elif case in {"failed", "invalid"}:
        items[1] = changed(items[1], status=case, response=None)
    else:
        response = items[1].response
        assert response is not None
        if case == "wrong_model":
            response = changed(response, model_sha256="f" * 64)
        elif case == "wrong_times":
            response = changed(
                response,
                trajectory=Trajectory(
                    frames=(
                        Frame(time=0.0, positions=((0.0, 0.0),), velocities=((0.0, 0.0),)),
                        Frame(time=0.5, positions=((0.0, 0.0),), velocities=((0.0, 0.0),)),
                    )
                ).model_dump(mode="json"),
            )
        else:
            response = changed(
                response,
                trajectory=Trajectory(
                    frames=tuple(
                        Frame(
                            time=t,
                            positions=((0.0, 0.0), (0.0, 0.0)),
                            velocities=((0.0, 0.0), (0.0, 0.0)),
                        )
                        for t in (0.0, 1.0)
                    )
                ).model_dump(mode="json"),
            )
        items[1] = changed(items[1], response=response.model_dump(mode="json"))

    def unexpected(*args: Any) -> ReferenceProbe:
        raise AssertionError("Unscorable predictions must not generate labels")

    monkeypatch.setattr(evaluation, "_reference_probe", unexpected)
    result = evaluate_spring_predictions(fitted, plan, tuple(items), truth)
    assert result.status == "unscorable" and result.report is not None
    assert result.report.probe_count == 3
    assert result.report.failed_prediction_count == (3 if case == "all_missing" else 1)
    assert result.report.position_mse is result.report.normalized_position_mse is None
    assert result.diagnostics.computed_metric_count == 0
    assert result.diagnostics.reference_completed_probe_count == 0
    assert_serializable(result)


@pytest.mark.parametrize(
    "case,reason",
    [
        ("duplicate_probe", "duplicate_probe"),
        ("model", "model_digest_mismatch"),
        ("request_hash", "request_digest_mismatch"),
        ("request_model", "request_model_mismatch"),
        ("duplicate_submission", "duplicate_submission"),
        ("foreign", "foreign_submission"),
        ("submission_hash", "submission_request_mismatch"),
        ("domain", "unsupported_probe"),
        ("scale_overflow", "invalid_normalization_scale"),
        ("scale_underflow", "invalid_normalization_scale"),
    ],
)
def test_protocol_failures_retain_complete_unassessed_manifest(case: str, reason: str) -> None:
    fitted, plan, entries, truth = fixture(2)
    probes = list(plan.probes)
    if case == "duplicate_probe":
        probes[1] = changed(probes[1], probe_id=probes[0].probe_id)
    elif case == "model":
        plan = changed(plan, model_sha256="f" * 64)
    elif case == "request_hash":
        probes[0] = changed(probes[0], request_sha256="f" * 64)
    elif case in {"request_model", "domain"}:
        req = (
            changed(probes[0].request, model_sha256="f" * 64)
            if case == "request_model"
            else request(fitted, position=(3.1, 0.0))
        )
        probes[0] = changed(
            probes[0], request=req.model_dump(mode="json"), request_sha256=message_sha256(req)
        )
    elif case == "duplicate_submission":
        entries = (entries[0], entries[0])
    elif case == "foreign":
        entries = (changed(entries[0], probe_id="foreign"), entries[1])
    elif case == "submission_hash":
        entries = (changed(entries[0], request_sha256="f" * 64), entries[1])
    else:
        plan = changed(plan, normalization_scale=1e200 if case == "scale_overflow" else 1e-200)
    plan = changed(plan, probes=[p.model_dump(mode="json") for p in probes])
    result = evaluate_spring_predictions(fitted, plan, entries, truth)
    assert result.status == "protocol_failure" and result.reason == reason
    assert result.report is None
    assert result.diagnostics.prediction_not_assessed_count == 2
    assert result.diagnostics.failed_prediction_count == 0
    assert result.diagnostics.metric_not_assessed_count == 2
    assert_serializable(result)


def test_unordered_submission_transport_is_aligned_to_protocol_order() -> None:
    fitted, plan, entries, truth = fixture(3)
    result = evaluate_spring_predictions(fitted, plan, tuple(reversed(entries)), truth)
    assert result.status == "scored"
    assert tuple(probe.probe_id for probe in result.probes) == tuple(
        p.probe_id for p in plan.probes
    )


@pytest.mark.parametrize("count", [25, 48, 49])
def test_submission_capacity_is_explicit_not_truncated(count: int) -> None:
    fitted, plan, entries, truth = fixture()
    if count > 48:
        with pytest.raises(ValidationError):
            evaluate_spring_predictions(fitted, plan, entries * count, truth)
    else:
        result = evaluate_spring_predictions(fitted, plan, entries * count, truth)
        assert result.reason == "submission_limit" and result.report is None
        assert result.diagnostics.submitted_entry_count == count


@pytest.mark.parametrize("case", ["noise", "cubic", "changed", "family", "topology", "coefficient"])
def test_unsupported_truth_does_not_invent_prediction_failures(case: str) -> None:
    fitted, plan, entries, truth = fixture(2)
    data = truth.model_dump(mode="json")
    if case == "noise":
        data["space"]["sampling"]["position_noise"] = 0.002
    elif case == "cubic":
        data["initial_law"]["parameters"]["cubic"] = 0.25
    elif case == "changed":
        data["space"]["budget"] = 6
        data["changed_law"] = data["initial_law"]
        data["change_after"] = 4
    elif case == "family":
        data["initial_law"] = {"kind": "velocity", "parameters": {"linear": 0.1}}
    elif case == "topology":
        data["space"]["structure"]["connections"] = []
    else:
        data["initial_law"]["parameters"]["linear"] = 4.1
    result = evaluate_spring_predictions(
        fitted, plan, entries, WorldDefinition.model_validate_json(json.dumps(data))
    )
    assert result.status == "evaluator_failure" and result.reason == "unsupported_world"
    assert result.report is None and result.diagnostics.valid_prediction_count == 2
    assert result.diagnostics.failed_prediction_count == 0
    assert result.diagnostics.reference_completed_probe_count == 0
    assert_serializable(result)


def test_reference_failure_retains_all_prediction_counts_and_completed_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = fixture(3)
    original = evaluation._reference_probe

    def fail_second(k: float, identity: str, req: PredictionRequest) -> ReferenceProbe:
        if identity == "probe-1":
            raise ArithmeticError("synthetic evaluator fault")
        return original(k, identity, req)

    monkeypatch.setattr(evaluation, "_reference_probe", fail_second)
    result = evaluate_spring_predictions(*values)
    assert result.status == "evaluator_failure" and result.reason == "reference_failure"
    assert result.report is None and result.reference is None
    assert result.diagnostics.valid_prediction_count == 3
    assert result.diagnostics.reference_completed_probe_count == 1
    assert result.diagnostics.reference_failed_probe_index == 1
    assert result.diagnostics.metric_not_assessed_count == 3


@pytest.mark.parametrize("error", [1e308, 1e154, 1e-200])
def test_metric_arithmetic_failures_do_not_relabel_predictions(error: float) -> None:
    fitted, plan, _, truth = fixture(3)
    entries = responses(plan, (((0.0, 0.0),) * 2, ((error, error),) * 2, ((0.0, 0.0),) * 2))
    result = evaluate_spring_predictions(fitted, plan, entries, truth)
    assert result.status == "arithmetic_failure" and result.reason == "metric_failure"
    assert result.report is None and result.reference is not None
    assert result.diagnostics.valid_prediction_count == 3
    assert result.diagnostics.failed_prediction_count == 0
    assert result.diagnostics.computed_metric_count == 1
    assert result.diagnostics.metric_not_assessed_count == 2
    assert result.probes[0].position_mse == 0.0
    assert result.probes[1].position_mse is None
    assert all(p.metric_role == "non-primary-diagnostic" for p in result.probes)
    assert_serializable(result)


@pytest.mark.parametrize("scale,error", [(1e-160, 10.0), (1e150, 1e-100)])
def test_normalization_overflow_and_positive_underflow_are_explicit(
    scale: float,
    error: float,
) -> None:
    fitted, plan, _, truth = fixture()
    plan = changed(plan, normalization_scale=scale)
    entries = responses(plan, (((error, error),) * 2,))
    result = evaluate_spring_predictions(fitted, plan, entries, truth)
    assert result.status == "arithmetic_failure" and result.reason == "normalization_failure"
    assert result.report is None
    assert (
        result.diagnostics.computed_metric_count == result.diagnostics.valid_prediction_count == 1
    )


@pytest.mark.parametrize("failed", [False, True])
def test_poor_learned_coefficient_is_not_filtered_as_invalid_truth(failed: bool) -> None:
    fitted = model(5.0)
    plan = protocol(fitted, (request(fitted),))
    entries = responses(plan)
    if failed:
        predicted = predict_linear_spring(fitted, plan.probes[0].request, SpringPredictionConfig())
        assert predicted.status == "unsupported_domain"
        entries = (changed(entries[0], status="failed", response=None),)
    result = evaluate_spring_predictions(fitted, plan, entries, world())
    assert result.status == ("unscorable" if failed else "scored")


def test_measured_runtime_and_canonical_report_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    moments = iter((1_000_000, 8_500_000))
    monkeypatch.setattr(evaluation, "perf_counter_ns", lambda: next(moments))
    result = evaluate_spring_predictions(*fixture())
    assert result.report is not None
    assert result.report.evaluation_runtime_ms == result.diagnostics.evaluation_runtime_ms == 7
    assert message_sha256(result.report) == result.report_sha256


U = 1 / math.sqrt(2)
PROBES = (
    ((-0.5, 0.0), (3.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
    ((-0.5, 0.0), (3.0, 0.0), (-2.0, 0.0), (-1.0, 0.0)),
    ((0.0, -0.5), (0.0, 3.0), (0.0, 2.0), (0.0, 1.0)),
    ((0.0, -0.5), (0.0, 3.0), (0.0, -2.0), (0.0, -1.0)),
    ((-0.5 * U, -0.5 * U), (3 * U, 3 * U), (2 * U, -2 * U), (U, -U)),
    ((0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
    ((0.0, 0.0), (1.5, 0.2), (0.3, -0.6), (0.2, 0.1)),
    ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), None),
)


@pytest.mark.parametrize("coefficient", [0.0, 1e-8, 1e-4, 0.3, 0.9, 2.0, 4.0])
@pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
def test_independent_reference_matches_fixed_counterfactual_matrix(
    coefficient: float,
    mass: float,
) -> None:
    fitted = model(coefficient)
    requests = tuple(
        request(
            fitted,
            times=tuple(i * 0.05 for i in range(41)),
            mass=mass,
            anchor=a,
            position=x,
            velocity=v,
            impulse=j,
        )
        for a, x, v, j in PROBES
    )
    plan = protocol(fitted, requests)
    entries = []
    for probe in plan.probes:
        predicted = predict_linear_spring(fitted, probe.request, SpringPredictionConfig())
        assert predicted.response is not None
        entries.append(
            ProbePrediction(
                probe_id=probe.probe_id,
                request_sha256=probe.request_sha256,
                status="response",
                response=predicted.response,
            )
        )
    result = evaluate_spring_predictions(fitted, plan, tuple(entries), world(coefficient))
    assert result.status == "scored" and result.reference is not None
    for reference, entry in zip(result.reference.probes, entries, strict=True):
        assert entry.response is not None
        for frame, label in zip(entry.response.trajectory.frames, reference.positions, strict=True):
            assert max(abs(a - b) for a, b in zip(frame.positions[0], label, strict=True)) <= 1e-12
    assert all(
        p.position_mse is not None and math.sqrt(p.position_mse) <= 0.001 for p in result.probes
    )


def test_reference_ballistic_impulse_and_known_oscillator_values() -> None:
    fitted = model()
    req = request(fitted, position=(1.0, 0.0), velocity=(0.0, 1.0), impulse=(1.0, 0.0), mass=0.5)
    assert evaluation._reference_position(0.0, req, 0.0) == (1.0, 0.0)
    assert evaluation._reference_position(0.0, req, 1.0) == (3.0, 1.0)
    oscillator = request(fitted, position=(1.0, 0.0), times=(0.0, math.pi / 2), dt=math.pi / 200)
    assert abs(evaluation._reference_position(1.0, oscillator, math.pi / 2)[0]) <= 1e-15


@pytest.mark.parametrize("coefficient", [math.ulp(0.0), 1e-320, 1e-300])
def test_reference_preserves_finite_near_zero_limit(coefficient: float) -> None:
    fitted = model(coefficient)
    req = request(fitted, position=(1.0, 0.0), velocity=(1.0, 0.0), mass=2.0)
    assert evaluation._reference_position(coefficient, req, 1.0) == (2.0, 0.0)


def test_full_irregular_and_dense_grids_remain_exact() -> None:
    fitted = model(4.0)
    grids = ((0.0, 0.03, 0.11, 0.29, 0.75, 1.37, 2.0), tuple(i * 0.001 for i in range(2001)))
    requests = tuple(
        request(fitted, times=grid, position=(3.0, 0.0), mass=0.5, dt=0.0001) for grid in grids
    )
    plan = protocol(fitted, requests)
    entries = tuple(
        ProbePrediction(
            probe_id=p.probe_id,
            request_sha256=p.request_sha256,
            status="response",
            response=predict_linear_spring(fitted, p.request, SpringPredictionConfig()).response,
        )
        for p in plan.probes
    )
    result = evaluate_spring_predictions(fitted, plan, entries, world(4.0))
    assert result.status == "scored" and result.reference is not None
    assert tuple(p.times for p in result.reference.probes) == grids
    assert all(
        p.position_mse is not None and math.sqrt(p.position_mse) <= 0.001 for p in result.probes
    )


def test_reference_agrees_with_higher_precision_ode_series_at_maximum_phase() -> None:
    from decimal import Decimal, localcontext

    fitted = model(4.0)
    req = request(
        fitted,
        times=(0.0, 2.0),
        mass=0.5,
        anchor=(-0.5, 0.0),
        position=(3.0, 0.0),
        velocity=(2.0, 0.0),
        impulse=(1.0, 0.0),
    )
    with localcontext() as context:
        context.prec = 120
        d = Decimal.from_float
        coefficient = d(4.0) / d(0.5)
        coefficients = [d(3.0) - d(-0.5), d(2.0) + d(1.0) / d(0.5)]
        for order in range(190):
            coefficients.append(-coefficient * coefficients[order] / ((order + 2) * (order + 1)))
        position = d(-0.5) + sum(
            value * d(2.0) ** order for order, value in enumerate(coefficients)
        )
    actual = evaluation._reference_position(4.0, req, 2.0)
    assert abs(actual[0] - float(position)) <= 1e-12
    assert actual[1] == 0.0


def test_reference_context_is_independent_of_callers_decimal_settings() -> None:
    from decimal import ROUND_FLOOR, Inexact, localcontext

    req = request(
        model(4.0),
        times=(0.0, 2.0),
        mass=0.5,
        anchor=(-0.5, 0.0),
        position=(3.0, 0.0),
        velocity=(2.0, 0.0),
        impulse=(1.0, 0.0),
    )
    expected = evaluation._reference_position(4.0, req, 2.0)
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_FLOOR
        context.Emin, context.Emax, context.clamp = -1, 1, 1
        context.traps[Inexact] = True
        actual = evaluation._reference_position(4.0, req, 2.0)
        assert context.prec == 2 and context.traps[Inexact]
    assert actual == expected
