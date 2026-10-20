from __future__ import annotations

import json
import math

import pytest
from pydantic import ValidationError

from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Frame,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Sampling,
    Structure,
    Trajectory,
)
from strange_physics.fitting import fit_linear_spring
from strange_physics.fitting_contracts import SpringFitConfig, SpringFitResult, validate_fit_result
from strange_physics.research_contracts import SpringFitInput, message_sha256

CONFIG = SpringFitConfig()
TIMES = tuple(i * 0.05 for i in range(41))
COEFFICIENTS = (0.0, 1e-8, 1e-4, 0.3, 0.9, 2.0, 4.0)


def _request(prefix: ObservationBundle) -> SpringFitInput:
    return SpringFitInput(
        observations=prefix,
        through_index=len(prefix.records) - 1,
        fit_config_sha256=message_sha256(CONFIG),
    )


def _prefix(
    coefficient: float = 0.9,
    masses: tuple[float, ...] = (1.0,),
    *,
    noise: float = 0.0,
    dt: float = 0.01,
    failed: bool = False,
) -> ObservationBundle:
    # Continuous labels are independent of the simulator and fitter. The impulse
    # is included once as J/m before t=0, and the displaced anchor is retained.
    anchor = (0.3, -0.4)
    structure = Structure(
        particle_ids=("mobile",),
        anchors=(Anchor(id="fixed", position=anchor),),
        connections=(Connection(a="fixed", b="mobile"),),
    )
    records = []
    for index, mass in enumerate(masses):
        particle = ParticleInitial(
            id="mobile", position=(1.2, 0.8), velocity=(-0.4, 0.6), mass=mass
        )
        impulse = (0.2, -0.3)
        experiment = Experiment(
            particles=(particle,), impulse=Impulse(particle_id="mobile", vector=impulse)
        )
        r = tuple(particle.position[c] - anchor[c] for c in range(2))
        v = tuple(particle.velocity[c] + impulse[c] / mass for c in range(2))
        frames = []
        for time in TIMES:
            if coefficient == 0:
                position = tuple(anchor[c] + r[c] + v[c] * time for c in range(2))
                velocity = v
            else:
                frequency = math.sqrt(coefficient / mass)
                cosine, sine = math.cos(frequency * time), math.sin(frequency * time)
                position = tuple(
                    anchor[c] + r[c] * cosine + v[c] * sine / frequency for c in range(2)
                )
                velocity = tuple(-r[c] * frequency * sine + v[c] * cosine for c in range(2))
            frames.append(
                Frame(
                    time=time,
                    positions=((position[0], position[1]),),
                    velocities=((velocity[0], velocity[1]),),
                )
            )
        records.append(
            ExperimentRecord(
                index=index,
                operation_id=f"purchase-{index}",
                experiment=experiment,
                status="completed",
                trajectory=Trajectory(frames=tuple(frames)),
            )
        )
    if failed:
        records.append(
            ExperimentRecord(
                index=len(records),
                operation_id="failed-purchase",
                experiment=records[0].experiment,
                status="failed",
                error="simulation_failed",
            )
        )
    return ObservationBundle(
        run_id="synthetic-fit-test",
        engine_version="independent-continuous-labels-v1",
        engine_fingerprint="0" * 64,
        space=ExperimentSpace(
            structure=structure,
            sampling=Sampling(dt=dt, position_noise=noise, velocity_noise=noise),
            budget=len(records),
            calibration_experiments=0,
        ),
        records=tuple(records),
    )


def _constant_columns(design: float, response: float = 0.0) -> ObservationBundle:
    # With mass=1, anchor=0 and constant x=y=-10g, the integral column
    # of every 0.1s pair is g. The linear velocity ramp gives each pair y.
    prefix = _prefix(0.0)
    payload = prefix.model_dump(mode="json")
    payload["space"]["structure"]["anchors"][0]["position"] = [0.0, 0.0]
    for index, frame in enumerate(payload["records"][0]["trajectory"]["frames"]):
        frame["positions"] = [[-10 * design, -10 * design]]
        frame["velocities"] = [[index * response / 2, index * response / 2]]
    return ObservationBundle.model_validate_json(json.dumps(payload))


def _round_trip(result: SpringFitResult, request: SpringFitInput) -> None:
    serialized = json.dumps(result.model_dump(mode="json"), allow_nan=False)
    decoded = SpringFitResult.model_validate_json(serialized)
    assert decoded == result
    validate_fit_result(decoded, request, CONFIG)


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
@pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
def test_independent_continuous_oscillator_coefficient_recovery(
    coefficient: float, mass: float
) -> None:
    request = _request(_prefix(coefficient, (mass,), failed=True))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "fitted" and result.model is not None
    # Truth is an evaluator-only test label, never an argument to fitting.
    assert abs(result.model.linear - coefficient) <= max(1e-8, 0.01 * coefficient)
    if coefficient:
        theta = math.sqrt(coefficient / mass) * 0.05
        ratio = 3 * math.sin(theta) / (theta * (2 + math.cos(theta)))
        assert result.model.linear == pytest.approx(coefficient * ratio, abs=2e-14)
    assert result.model.fit_record_indices == (0,)
    assert result.diagnostics.scalar_row_count == 40
    assert result.diagnostics.completed_record_count == 1
    assert result.diagnostics.failed_record_count == 1
    _round_trip(result, request)


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_mixed_masses_bind_full_prefix_and_weight_all_completed_records(coefficient: float) -> None:
    prefix = _prefix(coefficient, (0.5, 1.0, 2.0, 0.5), failed=True)
    request = _request(prefix)
    result = fit_linear_spring(request, CONFIG)
    assert result.model is not None
    assert abs(result.model.linear - coefficient) <= max(1e-8, 0.01 * coefficient)
    assert result.model.observation_sha256 == message_sha256(prefix)
    assert result.model.fit_config_sha256 == message_sha256(CONFIG)
    assert result.model.fit_record_indices == (0, 1, 2, 3)
    assert result.diagnostics.scalar_row_count == 160
    assert result.diagnostics.failed_record_count == 1
    assert fit_linear_spring(request, CONFIG).model_dump_json() == result.model_dump_json()
    _round_trip(result, request)


def test_hand_computed_mass_weighted_estimate_keeps_zero_coordinate_rows() -> None:
    prefix = _prefix(0.0, (0.5, 2.0), failed=True)
    data = prefix.model_dump(mode="json")
    data["space"]["structure"]["anchors"][0]["position"] = [0.0, 0.0]
    for record_index, slope in enumerate([-6.0, -2.0]):
        for frame_index, frame in enumerate(data["records"][record_index]["trajectory"]["frames"]):
            frame["positions"] = [[1.0, 0.0]]
            frame["velocities"] = [[slope * frame_index * 0.05, 0.0]]
    request = _request(ObservationBundle.model_validate_json(json.dumps(data)))
    result = fit_linear_spring(request, CONFIG)
    # Record columns are -0.2 and -0.05; responses are -0.6 and -0.2.
    # Each has 20 x rows and 20 zero y rows. The answer is neither the
    # unweighted mean (3+4)/2 nor a fit that discards zero rows for RMS.
    expected = (0.2 * 0.6 + 0.05 * 0.2) / (0.2**2 + 0.05**2)
    assert result.model is not None
    assert result.model.linear == pytest.approx(expected, abs=2e-14)
    assert result.diagnostics.design_rms == pytest.approx(math.sqrt((0.2**2 + 0.05**2) / 4))
    assert result.diagnostics.scalar_row_count == 80
    assert result.diagnostics.completed_record_indices == (0, 1)


@pytest.mark.parametrize(
    ("factor", "status"),
    [
        (0.0, "insufficient_excitation"),
        (0.5, "insufficient_excitation"),
        (1.0, "fitted"),
        (2.0, "fitted"),
    ],
)
def test_predeclared_excitation_floor_includes_every_scalar_row(factor: float, status: str) -> None:
    request = _request(_constant_columns(factor * 1e-6))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == status
    assert result.diagnostics.design_rms == pytest.approx(factor * 1e-6, abs=1e-21)
    assert result.diagnostics.scalar_row_count == 40
    assert (result.model is None) == (status != "fitted")
    _round_trip(result, request)


@pytest.mark.parametrize("coefficient", [-0.3, 0.0, 4.5, 1e308])
def test_negative_zero_outside_range_and_huge_finite_estimates_are_not_clipped(
    coefficient: float,
) -> None:
    request = _request(_constant_columns(1e-6, 1e-6 * coefficient))
    result = fit_linear_spring(request, CONFIG)
    assert result.diagnostics.raw_coefficient == pytest.approx(coefficient)
    assert result.diagnostics.estimated_coefficient_in_calibrated_range == (0 <= coefficient <= 4)
    assert result.diagnostics.accuracy_claim == "none"
    if coefficient < 0:
        assert result.status == "negative_estimate" and result.model is None
    else:
        assert result.status == "fitted" and result.model is not None
        assert result.model.linear == pytest.approx(coefficient)
    _round_trip(result, request)


@pytest.mark.parametrize(
    ("design", "response", "reason"),
    [
        (1e307, 0.0, "nonfinite_columns"),
        (1e200, 0.0, "nonfinite_reduction"),
        (1e-6, 1e303, "nonfinite_coefficient"),
    ],
)
def test_finite_input_overflow_is_a_counted_json_safe_failure(
    design: float, response: float, reason: str
) -> None:
    request = _request(_constant_columns(design, response))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "numerical_failure"
    assert result.reason == reason and result.model is None
    assert result.diagnostics.raw_coefficient is None
    assert result.diagnostics.scalar_row_count == 40
    assert result.diagnostics.completed_record_indices == (0,)
    _round_trip(result, request)


def test_finite_velocity_difference_and_cross_product_overflow_are_explicit() -> None:
    for positions, first, last, reason in [
        ([1.0, 0.0], -1e308, 1e308, "nonfinite_columns"),
        ([1e101, 0.0], 0.0, 1e210, "nonfinite_reduction"),
    ]:
        data = _prefix().model_dump(mode="json")
        for frame in data["records"][0]["trajectory"]["frames"]:
            frame["positions"] = [positions]
            frame["velocities"] = [[last, 0.0]]
        data["records"][0]["trajectory"]["frames"][0]["velocities"] = [[first, 0.0]]
        request = _request(ObservationBundle.model_validate_json(json.dumps(data)))
        result = fit_linear_spring(request, CONFIG)
        assert result.reason == reason and result.status == "numerical_failure"
        _round_trip(result, request)


def test_overflow_of_finite_record_reductions_is_not_an_accepted_zero_model() -> None:
    record = _constant_columns(1e153).records[0].model_dump(mode="json")
    data = _prefix(0.0, (1.0,) * 8).model_dump(mode="json")
    data["space"]["structure"]["anchors"][0]["position"] = [0.0, 0.0]
    for index in range(8):
        data["records"][index] = dict(record, index=index, operation_id=f"record-{index}")
    request = _request(ObservationBundle.model_validate_json(json.dumps(data)))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "numerical_failure" and result.reason == "nonfinite_reduction"
    assert result.diagnostics.scalar_row_count == 320
    assert result.model is None
    _round_trip(result, request)


@pytest.mark.parametrize("noise", [0.0, 0.002, 0.1])
def test_declared_noise_is_consumed_without_an_accuracy_claim(noise: float) -> None:
    request = _request(_prefix(noise=noise))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "fitted"
    assert result.diagnostics.declared_noisy == bool(noise)
    assert result.diagnostics.accuracy_claim == "none"
    assert result.diagnostics.completed_record_indices == (0,)
    _round_trip(result, request)


def test_actual_config_mismatch_precedes_domain_and_returns_no_estimate() -> None:
    data = _request(_prefix()).model_dump(mode="json")
    data["fit_config_sha256"] = "f" * 64
    data["observations"]["space"]["structure"]["connections"] = []
    request = SpringFitInput.model_validate_json(json.dumps(data))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "configuration_mismatch" and result.model is None
    assert result.diagnostics.actual_config_sha256 == message_sha256(CONFIG)
    assert result.diagnostics.requested_config_sha256 == "f" * 64
    assert result.diagnostics.scalar_row_count == 0
    _round_trip(result, request)


@pytest.mark.parametrize(
    "case",
    ["topology", "anchor", "mass", "position", "velocity", "impulse", "dt", "odd_tail", "cadence"],
)
def test_valid_public_messages_can_be_outside_fitting_domain(case: str) -> None:
    data = _prefix(failed=True).model_dump(mode="json")
    reason = {
        "topology": "unsupported_topology",
        "anchor": "anchor_outside_domain",
        "mass": "mass_outside_domain",
        "position": "position_outside_domain",
        "velocity": "velocity_outside_domain",
        "impulse": "impulse_outside_domain",
        "dt": "unsupported_sampling",
        "odd_tail": "unsupported_sampling",
        "cadence": "unsupported_sampling",
    }[case]
    if case == "topology":
        data["space"]["structure"]["connections"] = []
    elif case == "anchor":
        data["space"]["structure"]["anchors"][0]["position"] = [0.6, 0.0]
    elif case == "dt":
        data["space"]["sampling"]["dt"] = 0.025
    elif case == "odd_tail":
        data["space"]["sampling"]["duration"] = 1.95
        data["records"][0]["trajectory"]["frames"].pop()
    elif case == "cadence":
        data["space"]["sampling"]["sample_interval"] = 0.1
        data["records"][0]["trajectory"]["frames"] = data["records"][0]["trajectory"]["frames"][::2]
    elif case == "mass":
        data["space"]["limits"]["max_mass"] = 3.0
        data["records"][1]["experiment"]["particles"][0]["mass"] = 3.0
    elif case in {"position", "velocity"}:
        data["space"]["limits"][f"{case}_norm"] = 3.0
        data["records"][1]["experiment"]["particles"][0][case] = [2.5, 0.0]
    else:
        data["space"]["limits"]["impulse_norm"] = 2.0
        data["records"][1]["experiment"]["impulse"]["vector"] = [1.5, 0.0]
    request = _request(ObservationBundle.model_validate_json(json.dumps(data)))
    result = fit_linear_spring(request, CONFIG)
    assert result.status == "unsupported_domain" and result.reason == reason
    assert result.model is None and result.diagnostics.scalar_row_count == 0
    assert result.diagnostics.failed_record_count == 1
    _round_trip(result, request)


def test_failed_record_changes_provenance_but_not_estimate_or_selection() -> None:
    original = _prefix(failed=True)
    data = original.model_dump(mode="json")
    data["records"][-1]["operation_id"] = "different-failure"
    changed = ObservationBundle.model_validate_json(json.dumps(data))
    before = fit_linear_spring(_request(original), CONFIG)
    after = fit_linear_spring(_request(changed), CONFIG)
    assert before.model is not None and after.model is not None
    assert before.model.linear == after.model.linear
    assert before.model.fit_record_indices == after.model.fit_record_indices == (0,)
    assert before.model.observation_sha256 != after.model.observation_sha256


def test_prefix_and_all_failed_contract_failures_precede_fitting() -> None:
    data = _request(_prefix(failed=True)).model_dump(mode="json")
    data["through_index"] = 0
    with pytest.raises(ValidationError, match="exactly the purchased prefix"):
        SpringFitInput.model_validate_json(json.dumps(data))
    data["through_index"] = 1
    data["observations"]["records"][0].update(
        status="failed", error="simulation_failed", trajectory=None
    )
    with pytest.raises(ValidationError, match="at least one completed"):
        SpringFitInput.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("dt", [0.01, 0.005, 0.0025])
def test_simulator_public_observations_fit_without_private_world_input(dt: float) -> None:
    # Integration evidence only: hidden truth stays outside the fitter call.
    from strange_physics.laws import SpringLaw, SpringParameters
    from strange_physics.simulation import simulate

    prefix = _prefix(4.0, (0.5,), dt=dt)
    record = prefix.records[0]
    observed = simulate(
        prefix.space,
        record.experiment,
        SpringLaw(SpringParameters(linear=4.0)),
        noise_seed=7,
        experiment_index=0,
    )
    data = prefix.model_dump(mode="json")
    data["records"][0]["trajectory"] = observed.model_dump(mode="json")
    result = fit_linear_spring(
        _request(ObservationBundle.model_validate_json(json.dumps(data))), CONFIG
    )
    assert result.model is not None
    assert abs(result.model.linear - 4.0) < 9e-6
