from __future__ import annotations

import hashlib
import json
import math
import platform
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Literal

import numpy as np
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
    Limits,
    ObservationBundle,
    ParticleInitial,
    Sampling,
    Structure,
    Trajectory,
)
from strange_physics.laws import FloatArray, SpringLaw, SpringParameters
from strange_physics.research_contracts import PredictionRequest, SpringFitInput, message_sha256
from strange_physics.simulation import simulate

STIFFNESSES = (0.0, 1e-8, 1e-4, 0.3, 0.9, 2.0, 4.0)
MASSES = (0.5, 1.0, 2.0)
TIMESTEPS = (0.01, 0.005, 0.0025)
AMPLITUDES = (0.0, 1e-12, 1e-10, 1e-8, 1e-6, 1e-5, 1e-4, 1e-2)
DESIGN_RMS_FLOOR = 1e-6
COEFFICIENT_ABSOLUTE_FLOOR = 1e-8
PREDICTION_RMSE_LIMIT = 0.001
ANCHOR = complex(0.25, -0.4)
TIMES = tuple(i * 0.05 for i in range(41))
Method = Literal["simpson", "trapezoid"]
Source = Literal["analytic", "rk4"]


def _vector(value: complex) -> tuple[float, float]:
    return value.real, value.imag


def _structure(anchor: complex = ANCHOR) -> Structure:
    return Structure(
        particle_ids=("p",),
        anchors=(Anchor(id="a", position=_vector(anchor)),),
        connections=(Connection(a="p", b="a"),),
    )


def _effective_velocity(experiment: Experiment) -> complex:
    particle = experiment.particles[0]
    velocity = complex(*particle.velocity)
    if experiment.impulse is not None:
        assert experiment.impulse.particle_id == particle.id
        velocity += complex(*experiment.impulse.vector) / particle.mass
    return velocity


def _continuous(
    time: float, *, k: float, mass: float, position: complex, velocity: complex, anchor: complex
) -> tuple[complex, complex]:
    # Evaluator/fixture oracle only; no production force or integration call.
    if k == 0:
        return position + velocity * time, velocity
    rate = math.sqrt(k / mass)
    cosine, sine = math.cos(rate * time), math.sin(rate * time)
    displacement = position - anchor
    return (
        anchor + displacement * cosine + velocity * sine / rate,
        -displacement * rate * sine + velocity * cosine,
    )


def _purchases(masses: tuple[float, ...]) -> tuple[Experiment, ...]:
    specifications = (
        (complex(0.7, 0.2), complex(-0.2, 0.3), None),
        (complex(-0.6, 0.5), complex(0.4, -0.1), complex(0.3, 0.4)),
        (complex(1.2, -0.3), complex(0.0, 0.5), None),
        (complex(-0.3, -1.0), complex(-0.4, 0.2), complex(-0.4, 0.3)),
    )
    assert len(masses) == len(specifications)
    return tuple(
        Experiment(
            particles=(
                ParticleInitial(
                    id="p",
                    position=_vector(ANCHOR + displacement),
                    velocity=_vector(velocity),
                    mass=mass,
                ),
            ),
            impulse=None if impulse is None else Impulse(particle_id="p", vector=_vector(impulse)),
        )
        for mass, (displacement, velocity, impulse) in zip(masses, specifications, strict=True)
    )


def _prefix(
    k: float,
    masses: tuple[float, ...],
    *,
    dt: float = 0.01,
    noise: float = 0.0,
    seed: int = 0,
    source: Source = "rk4",
    amplitude: float | None = None,
) -> ObservationBundle:
    space = ExperimentSpace(
        structure=_structure(),
        sampling=Sampling(dt=dt, position_noise=noise, velocity_noise=noise),
    )
    experiments = (
        _purchases(masses)
        if amplitude is None
        else (
            Experiment(
                particles=(
                    ParticleInitial(id="p", position=_vector(ANCHOR + amplitude), mass=masses[0]),
                )
            ),
        )
    )
    records = []
    for index, experiment in enumerate(experiments):
        if source == "analytic":
            assert noise == 0
            particle = experiment.particles[0]
            states = [
                _continuous(
                    time,
                    k=k,
                    mass=particle.mass,
                    position=complex(*particle.position),
                    velocity=_effective_velocity(experiment),
                    anchor=ANCHOR,
                )
                for time in TIMES
            ]
            trajectory = Trajectory(
                frames=tuple(
                    Frame(
                        time=time, positions=(_vector(position),), velocities=(_vector(velocity),)
                    )
                    for time, (position, velocity) in zip(TIMES, states, strict=True)
                )
            )
        else:
            trajectory = simulate(
                space,
                experiment,
                SpringLaw(SpringParameters(linear=k)),
                noise_seed=seed,
                experiment_index=index,
            )
        records.append(
            ExperimentRecord(
                operation_id=f"calibration-{index}",
                index=index,
                experiment=experiment,
                status="completed",
                trajectory=trajectory,
            )
        )
    return ObservationBundle(
        run_id="synthetic-spring-calibration",
        engine_version=f"test-fixture-{source}-v1",
        engine_fingerprint="0" * 64,
        space=space,
        records=tuple(records),
    )


def _config_hash(method: Method) -> str:
    return hashlib.sha256(f"test-only.spring-domain.{method}.v1".encode()).hexdigest()


def _fit_input(prefix: ObservationBundle, method: Method = "simpson") -> SpringFitInput:
    return SpringFitInput(
        observations=prefix,
        through_index=len(prefix.records) - 1,
        fit_config_sha256=_config_hash(method),
    )


def _require_domain(fit: SpringFitInput, method: Method) -> None:
    prefix = fit.observations
    structure = prefix.space.structure
    if fit.fit_config_sha256 != _config_hash(method):
        raise ValueError("configuration does not match declared integration method")
    if (
        len(structure.particle_ids) != 1
        or len(structure.anchors) != 1
        or len(structure.connections) != 1
        or set((structure.connections[0].a, structure.connections[0].b))
        != {structure.particle_ids[0], structure.anchors[0].id}
    ):
        raise ValueError("unsupported first-spring topology")
    if math.hypot(*structure.anchors[0].position) > 0.5:
        raise ValueError("anchor exceeds declared calibration domain")
    sampling = prefix.space.sampling
    if sampling.duration != 2.0 or sampling.sample_interval != 0.05 or sampling.dt not in TIMESTEPS:
        raise ValueError("unsupported sampling; no partial window may be dropped")
    for record in prefix.records:
        particle = record.experiment.particles[0]
        if not 0.5 <= particle.mass <= 2.0:
            raise ValueError("mass outside calibration domain")
        if math.hypot(*particle.position) > 2 or math.hypot(*particle.velocity) > 2:
            raise ValueError("purchased condition outside calibration domain")
        if record.experiment.impulse and math.hypot(*record.experiment.impulse.vector) > 1:
            raise ValueError("impulse outside calibration domain")


@dataclass(frozen=True)
class Estimate:
    status: Literal[
        "estimated", "insufficient_excitation", "negative_estimate", "nonfinite_estimate"
    ]
    raw: float | None
    design_rms: float | None
    failure_reason: str | None
    row_count: int
    completed_indices: tuple[int, ...]
    failed_count: int
    prefix_sha256: str


def _columns(fit: SpringFitInput, method: Method) -> tuple[FloatArray, FloatArray, tuple[int, ...]]:
    _require_domain(fit, method)
    anchor = np.asarray(fit.observations.space.structure.anchors[0].position)
    h = fit.observations.space.sampling.sample_interval
    design, response, completed = [], [], []
    for record in fit.observations.records:
        if record.status == "failed":
            continue
        assert record.trajectory is not None
        frames = record.trajectory.frames
        if len(frames) != 41 or (len(frames) - 1) % 2:
            raise ValueError("complete paired windows are required")
        mass = record.experiment.particles[0].mass
        for start in range(0, len(frames) - 2, 2):
            first, middle, last = frames[start : start + 3]
            r0 = np.asarray(first.positions[0]) - anchor
            r1 = np.asarray(middle.positions[0]) - anchor
            r2 = np.asarray(last.positions[0]) - anchor
            # Public finite observations can still overflow derived arithmetic.
            with np.errstate(over="ignore", invalid="ignore"):
                integral = h * (
                    (r0 + 4 * r1 + r2) / 3 if method == "simpson" else (r0 + 2 * r1 + r2) / 2
                )
                design.append(-integral / mass)
                response.append(np.asarray(last.velocities[0]) - first.velocities[0])
        completed.append(record.index)
    return (
        np.asarray(design, dtype=np.float64).reshape(-1, 2),
        np.asarray(response, dtype=np.float64).reshape(-1, 2),
        tuple(completed),
    )


def _estimate(fit: SpringFitInput, method: Method = "simpson") -> Estimate:
    # No hidden coefficient, world definition or evaluation probe is an input.
    design, response, completed = _columns(fit, method)
    design_rms, raw = None, None
    status: Literal[
        "estimated", "insufficient_excitation", "negative_estimate", "nonfinite_estimate"
    ] = "nonfinite_estimate"
    failure_reason: str | None = "nonfinite_columns"
    if np.all(np.isfinite(design)) and np.all(np.isfinite(response)):
        with np.errstate(over="ignore", invalid="ignore"):
            energy = float(np.sum(design**2))
            cross_product = float(np.sum(design * response))
        if math.isfinite(energy):
            design_rms = math.sqrt(energy / design.size)
        if not math.isfinite(energy) or not math.isfinite(cross_product):
            failure_reason = "nonfinite_reduction"
        elif design_rms is not None and design_rms < DESIGN_RMS_FLOOR:
            status, failure_reason = "insufficient_excitation", "design_rms_below_floor"
        else:
            raw = cross_product / energy
            if not math.isfinite(raw):
                raw, failure_reason = None, "nonfinite_coefficient"
            elif raw < 0:
                status, failure_reason = "negative_estimate", "negative_coefficient"
            else:
                status, failure_reason = "estimated", None
    return Estimate(
        status=status,
        raw=raw,
        design_rms=design_rms,
        failure_reason=failure_reason,
        row_count=design.size,
        completed_indices=completed,
        failed_count=len(fit.observations.records) - len(completed),
        prefix_sha256=message_sha256(fit.observations),
    )


def _probes() -> tuple[PredictionRequest, ...]:
    u, q = complex(1, 1) / math.sqrt(2), complex(1, -1) / math.sqrt(2)
    specifications = (
        (complex(-0.5, 0), complex(3, 0), complex(2, 0), complex(1, 0)),
        (complex(-0.5, 0), complex(3, 0), complex(-2, 0), complex(-1, 0)),
        (complex(0, -0.5), complex(0, 3), complex(0, 2), complex(0, 1)),
        (complex(0, -0.5), complex(0, 3), complex(0, -2), complex(0, -1)),
        (-0.5 * u, 3 * u, 2 * q, q),
        (0j, 0j, complex(2, 0), complex(1, 0)),
        (0j, complex(1.5, 0.2), complex(0.3, -0.6), complex(0.2, 0.1)),
        (0j, 0j, 0j, None),
    )
    return tuple(
        PredictionRequest(
            model_sha256="0" * 64,
            structure=_structure(anchor),
            times=TIMES,
            integration_dt=0.01,
            experiment=Experiment(
                particles=(
                    ParticleInitial(
                        id="p", position=_vector(position), velocity=_vector(velocity), mass=mass
                    ),
                ),
                impulse=None
                if impulse is None
                else Impulse(particle_id="p", vector=_vector(impulse)),
            ),
        )
        for mass in MASSES
        for anchor, position, velocity, impulse in specifications
    )


def _probe_rmse(k_true: float, k_estimated: float, probe: PredictionRequest) -> float:
    particle = probe.experiment.particles[0]
    anchor = complex(*probe.structure.anchors[0].position)
    squared_errors: list[float] = []
    for time in probe.times:
        reference, _ = _continuous(
            time,
            k=k_true,
            mass=particle.mass,
            position=complex(*particle.position),
            velocity=_effective_velocity(probe.experiment),
            anchor=anchor,
        )
        predicted, _ = _continuous(
            time,
            k=k_estimated,
            mass=particle.mass,
            position=complex(*particle.position),
            velocity=_effective_velocity(probe.experiment),
            anchor=anchor,
        )
        difference = predicted - reference
        squared_errors.extend((difference.real**2, difference.imag**2))
    assert len(squared_errors) == 82
    return math.sqrt(math.fsum(squared_errors) / len(squared_errors))


@dataclass(frozen=True)
class Assessment:
    coefficient_error: float | None
    coefficient_pass: bool
    probe_rmses: tuple[float, ...]
    failed_probe_count: int
    failed_probe_indices: tuple[int, ...] = ()

    @property
    def accepted(self) -> bool:
        return (
            self.coefficient_pass
            and self.failed_probe_count == 0
            and all(error <= PREDICTION_RMSE_LIMIT for error in self.probe_rmses)
        )


def _assess(k_true: float, estimate: Estimate) -> Assessment:
    probes = _probes()
    if estimate.status != "estimated":
        return Assessment(
            coefficient_error=None if estimate.raw is None else abs(estimate.raw - k_true),
            coefficient_pass=False,
            probe_rmses=(),
            failed_probe_count=len(probes),
            failed_probe_indices=tuple(range(len(probes))),
        )
    assert estimate.raw is not None
    error = abs(estimate.raw - k_true)
    rmses: list[float] = []
    failed_indices: list[int] = []
    for index, probe in enumerate(probes):
        try:
            rmse = _probe_rmse(k_true, estimate.raw, probe)
        except (ValueError, OverflowError):
            failed_indices.append(index)
            continue
        if math.isfinite(rmse):
            rmses.append(rmse)
        else:
            failed_indices.append(index)
    return Assessment(
        coefficient_error=error,
        coefficient_pass=error <= max(COEFFICIENT_ABSOLUTE_FLOOR, 0.01 * k_true),
        probe_rmses=tuple(rmses),
        failed_probe_count=len(failed_indices),
        failed_probe_indices=tuple(failed_indices),
    )


def _bias_ratio(k: float, mass: float, method: Method) -> float:
    if k == 0:
        return 1.0
    theta = 0.05 * math.sqrt(k / mass)
    if method == "trapezoid":
        return 2 * math.tan(theta / 2) / theta
    return 3 * math.sin(theta) / (theta * (2 + math.cos(theta)))


@pytest.mark.parametrize("k", STIFFNESSES)
@pytest.mark.parametrize("mass", MASSES)
@pytest.mark.parametrize("dt", TIMESTEPS)
def test_joint_coefficient_and_per_probe_accuracy(k: float, mass: float, dt: float) -> None:
    analytic = _estimate(_fit_input(_prefix(k, (mass,) * 4, source="analytic")))
    estimate = _estimate(_fit_input(_prefix(k, (mass,) * 4, dt=dt)))
    assessment = _assess(k, estimate)
    assert analytic.raw is not None and estimate.raw is not None
    quadrature_bias = analytic.raw - k
    observation_effect = estimate.raw - analytic.raw
    assert analytic.raw == pytest.approx(k * _bias_ratio(k, mass, "simpson"), abs=1e-12, rel=0)
    assert estimate.status == "estimated"
    assert estimate.row_count == 160
    assert estimate.completed_indices == (0, 1, 2, 3)
    assert estimate.failed_count == 0
    assert assessment.accepted, (k, mass, dt, estimate, assessment)
    assert len(assessment.probe_rmses) == 24
    # Keep each error source visible to the evidence collector.
    assert math.isfinite(quadrature_bias) and math.isfinite(observation_effect)


@pytest.mark.parametrize("k", STIFFNESSES)
def test_shared_coefficient_across_record_mass_changes(k: float) -> None:
    masses = (0.5, 1.0, 2.0, 0.5)
    analytic_input = _fit_input(_prefix(k, masses, source="analytic"))
    analytic = _estimate(analytic_input)
    design, _, _ = _columns(analytic_input, "simpson")
    weights = tuple(float(np.sum(design[i * 20 : (i + 1) * 20] ** 2)) for i in range(4))
    expected = (
        k
        * math.fsum(
            weight * _bias_ratio(k, mass, "simpson")
            for weight, mass in zip(weights, masses, strict=True)
        )
        / math.fsum(weights)
    )
    assert analytic.raw == pytest.approx(expected, abs=1e-12, rel=0)
    estimate = _estimate(_fit_input(_prefix(k, masses)))
    assessment = _assess(k, estimate)
    assert estimate.status == "estimated"
    assert assessment.accepted, (k, estimate, assessment)


def test_trapezoid_coefficient_success_does_not_imply_prediction_success() -> None:
    prefix = _prefix(4.0, (0.5,) * 4, source="analytic")
    trapezoid = _estimate(_fit_input(prefix, "trapezoid"), "trapezoid")
    simpson = _estimate(_fit_input(prefix))
    trap_assessment = _assess(4.0, trapezoid)
    simpson_assessment = _assess(4.0, simpson)
    assert trapezoid.raw is not None and simpson.raw is not None
    assert trapezoid.raw == pytest.approx(4 * _bias_ratio(4.0, 0.5, "trapezoid"), abs=1e-12, rel=0)
    assert trap_assessment.coefficient_pass
    assert not trap_assessment.accepted
    assert trap_assessment.probe_rmses[0] == pytest.approx(0.00633124, abs=5e-9, rel=0)
    assert simpson_assessment.probe_rmses[0] == pytest.approx(8.44936e-6, abs=5e-11, rel=0)
    assert simpson_assessment.accepted


def test_continuous_simpson_and_absolute_floor_bounds() -> None:
    theta_squared_bound = 0.02
    coefficient_bound = 4 * theta_squared_bound**2 / (60 * (3 - theta_squared_bound / 2))
    sensitivity = (3.5 * 2**2 / 2 + 4 * 2**3 / 6) / 0.5
    assert coefficient_bound < 8.919e-6
    assert sensitivity * coefficient_bound < 2.2001e-4
    assert sensitivity * COEFFICIENT_ABSOLUTE_FLOOR < 2.4667e-7
    # Sample checks complement, rather than replace, the continuous proof in the document.
    for k in STIFFNESSES:
        for mass in MASSES:
            assert abs(k * (_bias_ratio(k, mass, "simpson") - 1)) <= coefficient_bound


@pytest.mark.parametrize("amplitude", AMPLITUDES)
@pytest.mark.parametrize("k", [0.0, 0.3, 4.0])
@pytest.mark.parametrize("mass", [0.5, 2.0])
def test_physical_excitation_sweep(amplitude: float, k: float, mass: float) -> None:
    prefix = _prefix(k, (mass,), amplitude=amplitude)
    analytic_prefix = _prefix(k, (mass,), amplitude=amplitude, source="analytic")
    estimate = _estimate(_fit_input(prefix))
    analytic = _estimate(_fit_input(analytic_prefix))
    assessment = _assess(k, estimate)
    design, response, _ = _columns(_fit_input(prefix), "simpson")
    analytic_design, analytic_response, _ = _columns(_fit_input(analytic_prefix), "simpson")
    residual_effect = float(
        np.sqrt(np.mean(((response - analytic_response) - k * (design - analytic_design)) ** 2))
    )
    assert estimate.row_count == 40
    assert estimate.completed_indices == (0,)
    assert estimate.failed_count == 0
    assert math.isfinite(residual_effect)
    assert estimate.design_rms is not None
    if estimate.design_rms < DESIGN_RMS_FLOOR:
        assert estimate.status == "insufficient_excitation"
        assert estimate.raw is None
        assert assessment.failed_probe_count == 24
    else:
        assert estimate.status == "estimated"
        assert assessment.accepted, (amplitude, k, mass, estimate, assessment)
        assert analytic.raw is not None
    if amplitude == 0:
        assert estimate.design_rms == 0


def _column_prefix(design_rms: float, residual: float = 0.0) -> ObservationBundle:
    # A public synthetic stationary-position record isolates the numerical support guard.
    # Both coordinates have the same g, so their pooled RMS is the requested value.
    displacement = -design_rms / 0.1
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(displacement, displacement)),)
    )
    return ObservationBundle(
        run_id="synthetic-column-boundary",
        engine_version="synthetic-v1",
        engine_fingerprint="0" * 64,
        space=ExperimentSpace(structure=_structure(0j), sampling=Sampling()),
        records=(
            ExperimentRecord(
                operation_id="column-boundary",
                index=0,
                experiment=experiment,
                status="completed",
                trajectory=Trajectory(
                    frames=tuple(
                        Frame(
                            time=time,
                            positions=((displacement, displacement),),
                            velocities=((time / 0.1 * residual, time / 0.1 * residual),),
                        )
                        for time in TIMES
                    )
                ),
            ),
        ),
    )


@pytest.mark.parametrize("factor", [1 - 1e-9, 1.0, 1 + 1e-9])
def test_design_rms_support_boundary(factor: float) -> None:
    estimate = _estimate(_fit_input(_column_prefix(DESIGN_RMS_FLOOR * factor)))
    assert estimate.design_rms == pytest.approx(DESIGN_RMS_FLOOR * factor, rel=1e-15, abs=0)
    assert estimate.status == ("insufficient_excitation" if factor < 1 else "estimated")
    assert estimate.row_count == 40


@pytest.mark.parametrize("residual", [-1e-14, 1e-14])
def test_residual_stress_and_negative_estimate_remain_visible(residual: float) -> None:
    estimate = _estimate(_fit_input(_column_prefix(DESIGN_RMS_FLOOR, residual)))
    assert estimate.raw == pytest.approx(residual / DESIGN_RMS_FLOOR, rel=1e-12, abs=0)
    assert estimate.status == ("negative_estimate" if residual < 0 else "estimated")
    assert estimate.raw is not None
    assert abs(estimate.raw) <= COEFFICIENT_ABSOLUTE_FLOOR * (1 + 1e-12)
    if residual < 0:
        assessment = _assess(0.0, estimate)
        assert not assessment.accepted
        assert assessment.failed_probe_count == 24
        assert assessment.probe_rmses == ()


def test_failed_and_uninformative_records_stay_in_counts_and_hash() -> None:
    prefix = _prefix(0.9, (1.0,) * 4)
    zero = _prefix(0.9, (1.0,), amplitude=0).records[0]
    records = (
        prefix.records[0],
        ExperimentRecord(
            operation_id="failed",
            index=1,
            experiment=prefix.records[1].experiment,
            status="failed",
            error="simulation_failed",
        ),
        ExperimentRecord(
            operation_id="zero",
            index=2,
            experiment=zero.experiment,
            status="completed",
            trajectory=zero.trajectory,
        ),
        prefix.records[3],
    )
    combined = ObservationBundle(**{**prefix.model_dump(), "records": records})
    estimate = _estimate(_fit_input(combined))
    assert estimate.status == "estimated"
    assert estimate.row_count == 120
    assert estimate.completed_indices == (0, 2, 3)
    assert estimate.failed_count == 1
    assert estimate.prefix_sha256 == message_sha256(combined)
    assert estimate.prefix_sha256 != message_sha256(prefix)
    design, response, _ = _columns(_fit_input(combined), "simpson")
    np.testing.assert_array_equal(design[20:40], np.zeros((20, 2)))
    np.testing.assert_array_equal(response[20:40], np.zeros((20, 2)))
    assert estimate.design_rms == float(np.sqrt(np.sum(design**2) / 120))


@pytest.mark.parametrize("method", ["simpson", "trapezoid"])
def test_every_middle_sample_and_final_endpoint_contribute(method: Method) -> None:
    prefix = _prefix(0.9, (1.0,) * 4, source="analytic")
    original = _estimate(_fit_input(prefix, method), method)
    data = prefix.model_dump(mode="json")
    data["records"][0]["trajectory"]["frames"][39]["positions"][0][0] += 0.01
    changed = ObservationBundle.model_validate_json(json.dumps(data))
    estimate = _estimate(_fit_input(changed, method), method)
    assert estimate.raw != original.raw
    data = prefix.model_dump(mode="json")
    data["records"][0]["trajectory"]["frames"][40]["velocities"][0][1] += 0.01
    changed = ObservationBundle.model_validate_json(json.dumps(data))
    assert _estimate(_fit_input(changed, method), method).raw != original.raw


def test_sampling_tail_and_configuration_mismatch_are_rejected() -> None:
    prefix = _prefix(0.9, (1.0,) * 4)
    data = prefix.model_dump(mode="json")
    data["space"]["sampling"]["duration"] = 1.95
    for record in data["records"]:
        record["trajectory"]["frames"] = record["trajectory"]["frames"][:-1]
    odd_tail = ObservationBundle.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="partial window"):
        _estimate(_fit_input(odd_tail))
    with pytest.raises(ValueError, match="configuration"):
        _estimate(_fit_input(prefix, "trapezoid"))


@pytest.mark.parametrize("mass", [0.49, 2.01])
def test_calibration_mass_domain_is_narrower_than_configurable_public_limits(mass: float) -> None:
    prefix = _prefix(0.9, (1.0,) * 4)
    data = prefix.model_dump(mode="json")
    data["space"]["limits"] = Limits(min_mass=0.1, max_mass=3.0).model_dump(mode="json")
    data["records"][0]["experiment"]["particles"][0]["mass"] = mass
    valid_public = ObservationBundle.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="mass"):
        _estimate(_fit_input(valid_public))


def test_public_identity_order_and_first_spring_topology_boundaries() -> None:
    prefix = _prefix(0.9, (1.0,) * 4)
    data = prefix.model_dump(mode="json")
    data["records"][0]["experiment"]["particles"][0]["id"] = "wrong"
    with pytest.raises(ValidationError, match="identities and order"):
        ObservationBundle.model_validate_json(json.dumps(data))
    data = prefix.model_dump(mode="json")
    data["space"]["structure"]["connections"] = []
    valid_public = ObservationBundle.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="topology"):
        _estimate(_fit_input(valid_public))


def test_prediction_extrapolation_is_not_a_purchased_action() -> None:
    probe = _probes()[0]
    assert probe.experiment.particles[0].position == (3.0, 0.0)
    assert abs(_effective_velocity(probe.experiment)) == 4.0
    assert (
        abs(
            complex(*probe.experiment.particles[0].position)
            - complex(*probe.structure.anchors[0].position)
        )
        == 3.5
    )
    with pytest.raises(ValueError, match="legal radius"):
        ExperimentSpace(structure=probe.structure, sampling=Sampling()).validate_experiment(
            probe.experiment
        )


def test_per_probe_acceptance_cannot_hide_one_bad_probe() -> None:
    assessment = Assessment(
        coefficient_error=0.0,
        coefficient_pass=True,
        probe_rmses=(0.002,) + (0.0,) * 23,
        failed_probe_count=0,
    )
    assert math.sqrt(math.fsum(x * x for x in assessment.probe_rmses) / 24) < 0.001
    assert not assessment.accepted


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("k", [0.0, 0.3, 0.9, 4.0])
@pytest.mark.parametrize("mass", [0.5, 2.0])
def test_fixed_noise_sensitivity_retains_all_outcomes(seed: int, k: float, mass: float) -> None:
    prefix = _prefix(k, (mass,) * 4, noise=0.002, seed=seed)
    estimate = _estimate(_fit_input(prefix))
    assessment = _assess(k, estimate)
    assert estimate.row_count == 160
    assert estimate.completed_indices == (0, 1, 2, 3)
    assert estimate.failed_count == 0
    assert estimate.prefix_sha256 == message_sha256(prefix)
    assert len(assessment.probe_rmses) + assessment.failed_probe_count == 24
    # This is sensitivity accounting, not an assertion that noisy accuracy passed.
    assert all(math.isfinite(error) and error >= 0 for error in assessment.probe_rmses)


def test_no_completed_records_is_explicitly_unsupported() -> None:
    prefix = _prefix(0.9, (1.0,) * 4)
    failed = tuple(
        ExperimentRecord(
            operation_id=record.operation_id,
            index=record.index,
            experiment=record.experiment,
            status="failed",
            error="simulation_failed",
        )
        for record in prefix.records
    )
    prefix = ObservationBundle(**{**prefix.model_dump(), "records": failed})
    assert len(prefix.records) == 4
    assert all(record.status == "failed" for record in prefix.records)
    with pytest.raises(ValidationError, match="at least one completed observation"):
        _fit_input(prefix)


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("design_reduction", "nonfinite_reduction"),
        ("design_columns", "nonfinite_columns"),
        ("response_columns", "nonfinite_columns"),
        ("coefficient", "nonfinite_coefficient"),
    ],
)
def test_nonfinite_derived_values_fail_and_remain_json_safe(kind: str, reason: str) -> None:
    prefix = _column_prefix(DESIGN_RMS_FLOOR)
    data = prefix.model_dump(mode="json")
    frames = data["records"][0]["trajectory"]["frames"]
    if kind in ("design_reduction", "design_columns"):
        value = 1e200 if kind == "design_reduction" else 1e308
        for frame in frames:
            frame["positions"] = [[value, value]]
    elif kind == "response_columns":
        frames[0]["velocities"] = [[-1e308, -1e308]]
        frames[2]["velocities"] = [[1e308, 1e308]]
    else:
        data = _column_prefix(DESIGN_RMS_FLOOR, residual=5e306).model_dump(mode="json")
    prefix = ObservationBundle.model_validate_json(json.dumps(data, allow_nan=False))
    estimate = _estimate(_fit_input(prefix))
    assert estimate.status == "nonfinite_estimate"
    assert estimate.failure_reason == reason
    assert estimate.raw is None
    assert estimate.row_count == 40
    assert estimate.completed_indices == (0,)
    assert estimate.failed_count == 0
    assert estimate.prefix_sha256 == message_sha256(prefix)
    report = _report_case(0.0, prefix)
    assert report["failed_probe_count"] == 24
    assert report["joint_accuracy_pass"] is False
    assert report["raw_coefficient"] is None
    assert report["failure_reason"] == reason
    assert json.loads(json.dumps(report, allow_nan=False))["failed_probe_count"] == 24


def test_finite_coefficient_with_prediction_overflow_retains_every_probe() -> None:
    prefix = _column_prefix(DESIGN_RMS_FLOOR, residual=1e302)
    estimate = _estimate(_fit_input(prefix))
    assert estimate.status == "estimated"
    assert estimate.raw is not None and math.isfinite(estimate.raw)
    report = _report_case(0.0, prefix)
    assert report["raw_coefficient"] == estimate.raw
    assert report["joint_accuracy_pass"] is False
    assert report["prediction_failure_reason"] == "nonfinite_prediction"
    assert report["failed_probe_count"] == 8
    assert report["failed_probe_indices"] == tuple(range(8))
    serialized = json.loads(json.dumps(report, allow_nan=False))
    outcomes = serialized["per_probe_coordinate_rmse"]
    assert len(outcomes) == 24
    assert outcomes[:8] == [None] * 8
    assert all(value is not None and math.isfinite(value) for value in outcomes[8:])


def _report_case(
    k: float,
    prefix: ObservationBundle,
    *,
    analytic_prefix: ObservationBundle | None = None,
    method: Method = "simpson",
) -> dict[str, object]:
    estimate = _estimate(_fit_input(prefix, method), method)
    assessment = _assess(k, estimate)
    computed_rmses = iter(assessment.probe_rmses)
    aligned_rmses = tuple(
        None if index in assessment.failed_probe_indices else next(computed_rmses)
        for index in range(24)
    )
    report: dict[str, object] = {
        "true_k_evaluator_only": k,
        "masses": [record.experiment.particles[0].mass for record in prefix.records],
        "dt": prefix.space.sampling.dt,
        "method": method,
        "status": estimate.status,
        "raw_coefficient": estimate.raw,
        "design_rms": estimate.design_rms,
        "failure_reason": estimate.failure_reason,
        "scalar_row_count": estimate.row_count,
        "completed_indices": estimate.completed_indices,
        "failed_record_count": estimate.failed_count,
        "prefix_sha256": estimate.prefix_sha256,
        "absolute_coefficient_error": assessment.coefficient_error,
        "coefficient_pass": assessment.coefficient_pass,
        "per_probe_coordinate_rmse": aligned_rmses,
        "failed_probe_indices": assessment.failed_probe_indices,
        "prediction_failure_reason": "nonfinite_prediction"
        if estimate.status == "estimated" and assessment.failed_probe_count
        else None,
        "max_probe_coordinate_rmse": max(assessment.probe_rmses, default=None),
        "failed_probe_count": assessment.failed_probe_count,
        "probes_over_rmse_limit": sum(
            value > PREDICTION_RMSE_LIMIT for value in assessment.probe_rmses
        ),
        "joint_accuracy_pass": assessment.accepted,
    }
    if analytic_prefix is not None:
        analytic_fit = _fit_input(analytic_prefix, method)
        analytic_estimate = _estimate(analytic_fit, method)
        observed_g, observed_y, _ = _columns(_fit_input(prefix, method), method)
        exact_g, exact_y, _ = _columns(analytic_fit, method)
        residual = (observed_y - exact_y) - k * (observed_g - exact_g)
        position_errors, velocity_errors = [], []
        for observed_record, exact_record in zip(
            prefix.records, analytic_prefix.records, strict=True
        ):
            assert observed_record.trajectory is not None and exact_record.trajectory is not None
            for observed, exact in zip(
                observed_record.trajectory.frames, exact_record.trajectory.frames, strict=True
            ):
                position_errors.append(
                    abs(complex(*observed.positions[0]) - complex(*exact.positions[0]))
                )
                velocity_errors.append(
                    abs(complex(*observed.velocities[0]) - complex(*exact.velocities[0]))
                )
        report.update(
            exact_sample_estimate=analytic_estimate.raw,
            exact_sample_quadrature_bias=None
            if analytic_estimate.raw is None
            else analytic_estimate.raw - k,
            rk4_observation_coefficient_effect=None
            if estimate.raw is None or analytic_estimate.raw is None
            else estimate.raw - analytic_estimate.raw,
            rk4_observation_residual_rms=float(np.sqrt(np.mean(residual**2))),
            max_sampled_position_vector_error=max(position_errors),
            max_sampled_velocity_vector_error=max(velocity_errors),
        )
    return report


def calibration_report() -> dict[str, object]:
    """Recompute the frozen manifest; all failures stay in this test-only report."""
    primary = []
    for dt in TIMESTEPS:
        for mass in MASSES:
            for k in STIFFNESSES:
                primary.append(
                    _report_case(
                        k,
                        _prefix(k, (mass,) * 4, dt=dt),
                        analytic_prefix=_prefix(k, (mass,) * 4, source="analytic"),
                    )
                )
    mixed = [
        _report_case(
            k,
            _prefix(k, (0.5, 1.0, 2.0, 0.5)),
            analytic_prefix=_prefix(k, (0.5, 1.0, 2.0, 0.5), source="analytic"),
        )
        for k in STIFFNESSES
    ]
    weak = [
        {
            **_report_case(
                k,
                _prefix(k, (mass,), amplitude=amplitude),
                analytic_prefix=_prefix(k, (mass,), amplitude=amplitude, source="analytic"),
            ),
            "amplitude": amplitude,
        }
        for amplitude in AMPLITUDES
        for k in (0.0, 0.3, 4.0)
        for mass in (0.5, 2.0)
    ]
    noise = [
        {**_report_case(k, _prefix(k, (mass,) * 4, noise=0.002, seed=seed)), "seed": seed}
        for seed in range(8)
        for k in (0.0, 0.3, 0.9, 4.0)
        for mass in (0.5, 2.0)
    ]
    methods: tuple[Method, ...] = ("simpson", "trapezoid")
    comparison = [
        _report_case(4.0, _prefix(4.0, (0.5,) * 4, source="analytic"), method=method)
        for method in methods
    ]
    return {
        "report_version": "test-only-spring-domain-v1",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.system(),
            "machine": platform.machine(),
            "numpy": np.__version__,
            "pydantic": version("pydantic"),
        },
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "preregistration_commit": "5e524a10e4decbd362e779ffaf95d983a0083e3b",
        "weighted_ratio_clarification_commit": "f55d38fcecd5ed08c8d6ec73f21e70680569ba57",
        "primary": primary,
        "mixed_mass": mixed,
        "weak_excitation": weak,
        "noise_sensitivity": noise,
        "exact_sample_method_comparison": comparison,
    }


if __name__ == "__main__":
    print(json.dumps(calibration_report(), indent=2, allow_nan=False))
