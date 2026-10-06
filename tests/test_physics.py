from __future__ import annotations

import math

import numpy as np
import pytest

from strange_physics.contracts import (
    Connection,
    Experiment,
    ExperimentSpace,
    Impulse,
    ParticleInitial,
    Sampling,
    Structure,
)
from strange_physics.laws import (
    FloatArray,
    Geometry,
    RadialLaw,
    RadialParameters,
    SpringLaw,
    SpringParameters,
    VelocityLaw,
    VelocityParameters,
)
from strange_physics.simulation import SimulationError, simulate


def test_linear_oscillator_matches_analytic_solution(
    space: ExperimentSpace,
    experiment: Experiment,
) -> None:
    result = simulate(space, experiment, SpringLaw(SpringParameters(linear=1.0)), noise_seed=0)
    for frame in result.frames:
        assert frame.positions[0] == pytest.approx((math.cos(frame.time), 0.0), abs=2e-9)
        assert frame.velocities[0] == pytest.approx((-math.sin(frame.time), 0.0), abs=2e-9)


def test_smaller_timestep_reduces_integration_error(
    space: ExperimentSpace,
    experiment: Experiment,
) -> None:
    errors = []
    for dt in (0.05, 0.025):
        config = ExperimentSpace(structure=space.structure, sampling=Sampling(dt=dt))
        result = simulate(config, experiment, SpringLaw(SpringParameters(linear=4.0)), noise_seed=0)
        errors.append(abs(result.frames[-1].positions[0][0] - math.cos(4.0)))
    assert errors[1] < errors[0] / 10


def test_pair_forces_preserve_momentum_and_center_of_mass() -> None:
    space = ExperimentSpace(
        structure=Structure(particle_ids=("a", "b"), connections=(Connection(a="a", b="b"),)),
        sampling=Sampling(),
    )
    experiment = Experiment(
        particles=(
            ParticleInitial(id="a", position=(-0.5, 0.0), velocity=(0.1, 0.2), mass=1.0),
            ParticleInitial(id="b", position=(0.5, 0.0), velocity=(-0.1, 0.0), mass=2.0),
        )
    )
    result = simulate(space, experiment, SpringLaw(SpringParameters(cubic=0.1)), noise_seed=0)
    masses = np.asarray([1.0, 2.0])[:, None]
    initial_momentum = np.asarray([-0.1, 0.2])
    initial_center = np.asarray([1 / 6, 0.0])
    for frame in result.frames:
        momentum = np.sum(masses * np.asarray(frame.velocities), axis=0)
        center = np.sum(masses * np.asarray(frame.positions), axis=0) / 3
        np.testing.assert_allclose(momentum, initial_momentum, atol=2e-14)
        np.testing.assert_allclose(
            center, initial_center + frame.time * initial_momentum / 3, atol=2e-14
        )


def test_impulse_changes_velocity_by_momentum_over_mass(space: ExperimentSpace) -> None:
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.0, 0.0), mass=2.0),),
        impulse=Impulse(particle_id="p", vector=(1.0, 0.0)),
    )
    result = simulate(space, experiment, VelocityLaw(VelocityParameters(linear=0.0)), noise_seed=0)
    assert result.frames[0].velocities[0] == (0.5, 0.0)
    assert result.frames[-1].positions[0] == pytest.approx((1.0, 0.0))


def test_drag_dissipates_energy(space: ExperimentSpace) -> None:
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.0, 0.0), velocity=(1.0, 0.5)),)
    )
    result = simulate(
        space, experiment, VelocityLaw(VelocityParameters(linear=0.2, cubic=0.3)), noise_seed=0
    )
    energies = [sum(component**2 for component in frame.velocities[0]) for frame in result.frames]
    assert all(a > b for a, b in zip(energies, energies[1:], strict=False))


def test_transverse_force_preserves_speed(space: ExperimentSpace) -> None:
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.0, 0.0), velocity=(1.0, 0.0)),)
    )
    result = simulate(
        space, experiment, VelocityLaw(VelocityParameters(linear=0.0, transverse=1.0)), noise_seed=0
    )
    for frame in result.frames:
        assert frame.velocities[0] == pytest.approx(
            (math.cos(frame.time), math.sin(frame.time)), abs=2e-9
        )


def test_softened_radial_force_is_finite_at_coincident_positions() -> None:
    positions = np.zeros((2, 2), dtype=np.float64)
    result = RadialLaw(RadialParameters()).forces(positions, positions, Geometry(2, ((0, 1),)))
    np.testing.assert_array_equal(result, np.zeros_like(positions))


@pytest.mark.parametrize("strength", [-0.1, 0.1])
def test_radial_polarity_and_rotation(strength: float) -> None:
    positions = np.asarray([[1.0, 0.0], [0.0, 0.0]])
    velocities = np.zeros_like(positions)
    rotation = np.asarray([[0.0, -1.0], [1.0, 0.0]])
    law = RadialLaw(RadialParameters(strength=strength))
    force = law.forces(positions, velocities, Geometry(2, ((0, 1),)))
    assert force[0, 0] * strength > 0
    np.testing.assert_allclose(
        law.forces(positions @ rotation.T, velocities, Geometry(2, ((0, 1),))), force @ rotation.T
    )
    np.testing.assert_array_equal(force.sum(axis=0), np.zeros(2))


def test_observation_noise_is_reproducible_and_does_not_drive_physics(
    space: ExperimentSpace,
    experiment: Experiment,
) -> None:
    noisy = ExperimentSpace(
        structure=space.structure, sampling=Sampling(position_noise=0.01, velocity_noise=0.01)
    )
    law = SpringLaw(SpringParameters())
    first = simulate(noisy, experiment, law, noise_seed=7, experiment_index=3)
    assert first == simulate(noisy, experiment, law, noise_seed=7, experiment_index=3)
    assert first != simulate(noisy, experiment, law, noise_seed=7, experiment_index=4)
    # Changing only velocity sensor noise cannot affect position observations.
    changed = ExperimentSpace(
        structure=space.structure, sampling=Sampling(position_noise=0.01, velocity_noise=0.1)
    )
    second = simulate(changed, experiment, law, noise_seed=7, experiment_index=3)
    assert [f.positions for f in first.frames] == [f.positions for f in second.frames]


class InvalidForce:
    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        return np.full_like(positions, np.nan)


def test_nonfinite_force_fails_explicitly(space: ExperimentSpace, experiment: Experiment) -> None:
    with pytest.raises(SimulationError, match="invalid array"):
        simulate(space, experiment, InvalidForce(), noise_seed=0)
