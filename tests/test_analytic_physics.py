from __future__ import annotations

import cmath
import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pytest

from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentSpace,
    Impulse,
    ParticleInitial,
    Sampling,
    Structure,
    Trajectory,
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

ANALYTIC_ATOL = 2e-7
StateOracle = Callable[[float], tuple[complex, complex]]


def _vector(value: complex) -> tuple[float, float]:
    return value.real, value.imag


def _assert_oracle(trajectory: Trajectory, oracle: StateOracle, *, atol: float) -> None:
    for frame in trajectory.frames:
        position, velocity = oracle(frame.time)
        np.testing.assert_allclose(frame.positions[0], _vector(position), rtol=0, atol=atol)
        np.testing.assert_allclose(frame.velocities[0], _vector(velocity), rtol=0, atol=atol)


def _oracle_error(trajectory: Trajectory, oracle: StateOracle) -> float:
    return max(
        max(
            abs(complex(*frame.positions[0]) - oracle(frame.time)[0]),
            abs(complex(*frame.velocities[0]) - oracle(frame.time)[1]),
        )
        for frame in trajectory.frames
    )


def _space(*, anchor: complex | None = None, dt: float = 0.01) -> ExperimentSpace:
    return ExperimentSpace(
        structure=Structure(
            particle_ids=("p",),
            anchors=() if anchor is None else (Anchor(id="a", position=_vector(anchor)),),
            connections=() if anchor is None else (Connection(a="p", b="a"),),
        ),
        sampling=Sampling(dt=dt),
    )


def _oscillator(
    time: float, *, position: complex, velocity: complex, anchor: complex, mass: float, k: float
) -> tuple[complex, complex]:
    # This closed form does not call the force plugin or a numerical integrator.
    if k == 0:
        return position + velocity * time, velocity
    rate = math.sqrt(k / mass)
    cosine, sine = math.cos(rate * time), math.sin(rate * time)
    displacement = position - anchor
    return (
        anchor + displacement * cosine + velocity * sine / rate,
        -displacement * rate * sine + velocity * cosine,
    )


def _velocity_solution(
    time: float, *, position: complex, velocity: complex, mass: float, drag: float, kappa: float
) -> tuple[complex, complex]:
    # kappa is force per velocity; the actual angular rate is kappa / mass.
    rate = complex(-drag, kappa) / mass
    if rate == 0:
        return position + velocity * time, velocity
    exponential = cmath.exp(rate * time)
    return position + velocity * (exponential - 1) / rate, velocity * exponential


@pytest.mark.parametrize("mass", [0.5, 1.0, 2.0])
@pytest.mark.parametrize("k", [0.0, 0.5, 4.0])
def test_oscillator_with_translated_anchor_and_mass(mass: float, k: float) -> None:
    anchor, position, velocity = complex(0.25, -0.4), complex(0.9, 0.2), complex(-0.35, 0.45)
    result = simulate(
        _space(anchor=anchor),
        Experiment(
            particles=(
                ParticleInitial(
                    id="p", position=_vector(position), velocity=_vector(velocity), mass=mass
                ),
            )
        ),
        SpringLaw(SpringParameters(linear=k)),
        noise_seed=0,
    )
    _assert_oracle(
        result,
        lambda t: _oscillator(
            t, position=position, velocity=velocity, anchor=anchor, mass=mass, k=k
        ),
        atol=ANALYTIC_ATOL,
    )


@pytest.mark.parametrize(
    ("drag", "kappa", "mass", "dt"),
    [
        (0.0, 0.0, 0.5, 0.01),
        (0.4, 0.0, 0.5, 0.01),
        (2.0, 0.0, 2.0, 0.01),
        (0.0, 1.5, 0.5, 0.01),
        (0.0, -1.5, 0.5, 0.01),
        (0.0, 3.0, 0.5, 0.005),
        (0.4, 1.5, 0.5, 0.01),
        (0.4, -1.5, 1.0, 0.01),
        (0.4, 1.5, 2.0, 0.01),
    ],
)
def test_linear_drag_rotation_and_combination(
    drag: float, kappa: float, mass: float, dt: float
) -> None:
    position, velocity = complex(-0.3, 0.4), complex(0.7, -0.4)
    result = simulate(
        _space(dt=dt),
        Experiment(
            particles=(
                ParticleInitial(
                    id="p", position=_vector(position), velocity=_vector(velocity), mass=mass
                ),
            )
        ),
        VelocityLaw(VelocityParameters(linear=drag, transverse=kappa)),
        noise_seed=0,
    )
    _assert_oracle(
        result,
        lambda t: _velocity_solution(
            t, position=position, velocity=velocity, mass=mass, drag=drag, kappa=kappa
        ),
        atol=ANALYTIC_ATOL,
    )


@pytest.mark.parametrize("mass", [0.5, 2.0])
@pytest.mark.parametrize("cubic", [0.2, 1.0])
def test_cubic_drag_matches_separable_solution(mass: float, cubic: float) -> None:
    position, velocity = complex(-0.3, 0.4), complex(0.7, -0.4)
    rate = cubic * abs(velocity) ** 2 / mass

    def oracle(time: float) -> tuple[complex, complex]:
        scale = math.sqrt(1 + 2 * rate * time)
        # Rationalized integral avoids subtracting nearly equal square roots.
        return position + velocity * (2 * time / (scale + 1)), velocity / scale

    result = simulate(
        _space(),
        Experiment(
            particles=(
                ParticleInitial(
                    id="p", position=_vector(position), velocity=_vector(velocity), mass=mass
                ),
            )
        ),
        VelocityLaw(VelocityParameters(linear=0.0, cubic=cubic)),
        noise_seed=0,
    )
    _assert_oracle(result, oracle, atol=ANALYTIC_ATOL)


@pytest.mark.parametrize("kind", ["oscillator", "drag", "rotation", "damped_rotation"])
def test_analytic_error_decreases_with_timestep(kind: str) -> None:
    position, velocity = complex(0.8, -0.2), complex(0.3, 0.4)
    anchor = complex(0.1, 0.1) if kind == "oscillator" else None
    mass = 0.5

    def oracle(time: float) -> tuple[complex, complex]:
        if kind == "oscillator":
            return _oscillator(
                time,
                position=position,
                velocity=velocity,
                anchor=complex(0.1, 0.1),
                mass=mass,
                k=2.0,
            )
        return _velocity_solution(
            time,
            position=position,
            velocity=velocity,
            mass=mass,
            drag=0.4 if kind in ("drag", "damped_rotation") else 0.0,
            kappa=1.0 if kind in ("rotation", "damped_rotation") else 0.0,
        )

    law = (
        SpringLaw(SpringParameters(linear=2.0))
        if kind == "oscillator"
        else VelocityLaw(
            VelocityParameters(
                linear=0.4 if kind in ("drag", "damped_rotation") else 0.0,
                transverse=1.0 if kind in ("rotation", "damped_rotation") else 0.0,
            )
        )
    )
    experiment = Experiment(
        particles=(
            ParticleInitial(
                id="p", position=_vector(position), velocity=_vector(velocity), mass=mass
            ),
        )
    )
    errors = [
        _oracle_error(simulate(_space(anchor=anchor, dt=dt), experiment, law, noise_seed=0), oracle)
        for dt in (0.05, 0.025, 0.0125)
    ]
    # RK4 has fourth-order global error; require improvement with margin, not exact ratios.
    assert errors[1] < errors[0] / 10
    assert errors[2] < errors[1] / 10


@dataclass(frozen=True)
class ConstantForce:
    vector: tuple[float, float]

    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        return np.tile(np.asarray(self.vector, dtype=np.float64), (len(positions), 1))


@pytest.mark.parametrize("target", ["a", "b", "c"])
def test_constant_force_and_targeted_impulse_respect_each_mass(target: str) -> None:
    particles = (
        ParticleInitial(id="a", position=(-0.3, 0.2), velocity=(0.1, -0.2), mass=0.5),
        ParticleInitial(id="b", position=(0.4, -0.1), velocity=(-0.2, 0.3), mass=1.0),
        ParticleInitial(id="c", position=(0.2, 0.3), velocity=(0.4, 0.1), mass=2.0),
    )
    impulse, force = complex(0.3, 0.4), complex(0.3, -0.45)
    result = simulate(
        ExperimentSpace(structure=Structure(particle_ids=("a", "b", "c")), sampling=Sampling()),
        Experiment(
            particles=particles, impulse=Impulse(particle_id=target, vector=_vector(impulse))
        ),
        ConstantForce(_vector(force)),
        noise_seed=0,
    )
    for frame in result.frames:
        for index, particle in enumerate(particles):
            initial = complex(*particle.position)
            speed = complex(*particle.velocity)
            if particle.id == target:
                speed += impulse / particle.mass
            acceleration = force / particle.mass
            np.testing.assert_allclose(
                frame.positions[index],
                _vector(initial + speed * frame.time + acceleration * frame.time**2 / 2),
                rtol=0,
                atol=2e-13,
            )
            np.testing.assert_allclose(
                frame.velocities[index],
                _vector(speed + acceleration * frame.time),
                rtol=0,
                atol=2e-13,
            )


@pytest.mark.parametrize(
    ("law", "expected"),
    [
        (SpringLaw(SpringParameters(linear=1.25, cubic=0.5)), ((-1.05, -1.4), (1.05, 1.4))),
        (
            RadialLaw(RadialParameters(strength=0.5, exponent=1.0, softening=0.5)),
            ((0.24, 0.32), (-0.24, -0.32)),
        ),
        (
            RadialLaw(RadialParameters(strength=0.5, exponent=3.0, softening=0.5)),
            ((0.192, 0.256), (-0.192, -0.256)),
        ),
        (
            VelocityLaw(VelocityParameters(linear=0.4, cubic=0.2, transverse=-0.5)),
            ((0.04, -0.78), (0.33, 0.065)),
        ),
    ],
)
def test_hand_calculated_force_vectors(
    law: SpringLaw | RadialLaw | VelocityLaw, expected: tuple[tuple[float, float], ...]
) -> None:
    actual = law.forces(
        np.asarray([[0.8, 0.5], [0.2, -0.3]]),
        np.asarray([[0.6, 0.8], [-0.4, 0.3]]),
        Geometry(2, ((0, 1),)),
    )
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-13)


@pytest.mark.parametrize(
    ("law", "expected"),
    [
        (SpringLaw(SpringParameters(linear=1.0)), ((1.0, 1.0), (-2.0, 1.0), (1.0, -2.0))),
        (
            RadialLaw(RadialParameters(strength=0.5, exponent=1.0, softening=1.0)),
            ((-0.25, -0.25), (5 / 12, -1 / 6), (-1 / 6, 5 / 12)),
        ),
    ],
)
def test_central_force_accumulation_and_translation(
    law: SpringLaw | RadialLaw, expected: tuple[tuple[float, float], ...]
) -> None:
    positions = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    velocities = np.zeros_like(positions)
    geometry = Geometry(3, ((0, 1), (0, 2), (1, 2)))
    force = law.forces(positions, velocities, geometry)
    np.testing.assert_allclose(force, expected, rtol=0, atol=1e-13)
    np.testing.assert_allclose(force.sum(axis=0), (0.0, 0.0), rtol=0, atol=1e-13)
    np.testing.assert_allclose(
        law.forces(positions + (0.7, -0.4), velocities, geometry),
        expected,
        rtol=0,
        atol=1e-13,
    )
    reversed_edges = Geometry(3, ((1, 0), (2, 0), (2, 1)))
    np.testing.assert_allclose(
        law.forces(positions, velocities, reversed_edges), expected, rtol=0, atol=1e-13
    )


@pytest.mark.parametrize(
    "law",
    [
        SpringLaw(SpringParameters(linear=0.7, cubic=0.2)),
        RadialLaw(RadialParameters(strength=-0.1, exponent=2.0, softening=0.5)),
        VelocityLaw(VelocityParameters(linear=0.4, cubic=0.2, transverse=-0.7)),
    ],
)
def test_proper_rotation_covariance_of_forces_and_trajectories(
    law: SpringLaw | RadialLaw | VelocityLaw,
) -> None:
    rotation = np.asarray([[0.6, -0.8], [0.8, 0.6]])
    positions = np.asarray([[-0.3, 0.1], [0.6, -0.2]])
    velocities = np.asarray([[0.2, -0.1], [-0.05, 0.2]])
    geometry = Geometry(2, ((0, 1),))
    np.testing.assert_allclose(
        law.forces(positions @ rotation.T, velocities @ rotation.T, geometry),
        law.forces(positions, velocities, geometry) @ rotation.T,
        rtol=0,
        atol=1e-13,
    )
    space = ExperimentSpace(
        structure=Structure(particle_ids=("a", "b"), connections=(Connection(a="a", b="b"),)),
        sampling=Sampling(),
    )

    def experiment(transform: FloatArray) -> Experiment:
        points, speeds = positions @ transform.T, velocities @ transform.T
        return Experiment(
            particles=tuple(
                ParticleInitial(
                    id=identity,
                    position=(float(points[i, 0]), float(points[i, 1])),
                    velocity=(float(speeds[i, 0]), float(speeds[i, 1])),
                    mass=mass,
                )
                for i, (identity, mass) in enumerate((("a", 0.5), ("b", 2.0)))
            )
        )

    original = simulate(space, experiment(np.eye(2)), law, noise_seed=0)
    rotated = simulate(space, experiment(rotation), law, noise_seed=0)
    for base, turned in zip(original.frames, rotated.frames, strict=True):
        assert base.time == turned.time
        np.testing.assert_allclose(
            turned.positions, np.asarray(base.positions) @ rotation.T, rtol=0, atol=1e-12
        )
        np.testing.assert_allclose(
            turned.velocities, np.asarray(base.velocities) @ rotation.T, rtol=0, atol=1e-12
        )


@pytest.mark.parametrize(
    "law",
    [
        SpringLaw(SpringParameters(linear=0.7, cubic=0.2)),
        RadialLaw(RadialParameters(strength=-0.1, exponent=1.0, softening=0.5)),
        RadialLaw(RadialParameters(strength=0.1, exponent=3.0, softening=0.5)),
    ],
)
def test_closed_pair_momentum_and_center_of_mass(law: SpringLaw | RadialLaw) -> None:
    particles = (
        ParticleInitial(id="a", position=(-0.3, 0.1), velocity=(0.2, -0.1), mass=0.5),
        ParticleInitial(id="b", position=(0.6, -0.2), velocity=(-0.05, 0.2), mass=2.0),
    )
    result = simulate(
        ExperimentSpace(
            structure=Structure(particle_ids=("a", "b"), connections=(Connection(a="a", b="b"),)),
            sampling=Sampling(),
        ),
        Experiment(particles=particles),
        law,
        noise_seed=0,
    )
    masses = np.asarray([0.5, 2.0])[:, None]
    # Independent hand sums: P=(0, 0.35), total mass=2.5, center=(0.42, -0.14).
    for frame in result.frames:
        np.testing.assert_allclose(
            np.sum(masses * frame.velocities, axis=0), (0.0, 0.35), rtol=0, atol=1e-12
        )
        np.testing.assert_allclose(
            np.sum(masses * frame.positions, axis=0) / 2.5,
            (0.42, -0.14 + 0.14 * frame.time),
            rtol=0,
            atol=1e-12,
        )


@pytest.mark.parametrize("cubic", [0.0, 0.2])
def test_conservative_spring_energy_drift_is_bounded_and_refines(cubic: float) -> None:
    anchor, mass, linear = complex(0.1, -0.2), 1.0, 1.0
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.9, 0.1), velocity=(0.2, 0.4)),)
    )
    drifts = []
    for dt in (0.02, 0.01):
        space = ExperimentSpace(
            structure=_space(anchor=anchor).structure,
            sampling=Sampling(dt=dt, sample_interval=0.1),
        )
        result = simulate(
            space,
            experiment,
            SpringLaw(SpringParameters(linear=linear, cubic=cubic)),
            noise_seed=0,
        )
        energies = []
        for frame in result.frames:
            radius_squared = abs(complex(*frame.positions[0]) - anchor) ** 2
            speed_squared = abs(complex(*frame.velocities[0])) ** 2
            energies.append(
                mass * speed_squared / 2
                + linear * radius_squared / 2
                + cubic * radius_squared**2 / 4
            )
        drifts.append(max(abs(energy - energies[0]) for energy in energies))
    assert drifts[1] <= 1e-8 * max(1.0, energies[0])
    assert drifts[1] < drifts[0] / 8


@pytest.mark.parametrize("kappa", [-3.0, 3.0])
def test_transverse_energy_drift_is_bounded_and_refines(kappa: float) -> None:
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.2, -0.3), velocity=(0.7, -0.4), mass=0.5),)
    )
    initial_energy = 0.5 * (0.7**2 + 0.4**2) / 2
    drifts = []
    for dt in (0.01, 0.005):
        result = simulate(
            _space(dt=dt),
            experiment,
            VelocityLaw(VelocityParameters(linear=0.0, transverse=kappa)),
            noise_seed=0,
        )
        energies = [0.5 * abs(complex(*frame.velocities[0])) ** 2 / 2 for frame in result.frames]
        drifts.append(max(abs(energy - initial_energy) for energy in energies))
    assert drifts[1] <= 1e-8 * initial_energy
    assert drifts[1] < drifts[0] / 8


@pytest.mark.parametrize("kappa", [-1.5, 0.0, 1.5])
@pytest.mark.parametrize("mass", [0.5, 2.0])
def test_drag_with_rotation_dissipates_energy(kappa: float, mass: float) -> None:
    result = simulate(
        _space(),
        Experiment(
            particles=(
                ParticleInitial(id="p", position=(0.1, 0.2), velocity=(0.7, -0.4), mass=mass),
            )
        ),
        VelocityLaw(VelocityParameters(linear=0.4, cubic=0.3, transverse=kappa)),
        noise_seed=0,
    )
    energies = [mass * abs(complex(*frame.velocities[0])) ** 2 / 2 for frame in result.frames]
    assert all(later < earlier for earlier, later in zip(energies, energies[1:], strict=False))


def test_velocity_force_work_matches_dissipation() -> None:
    velocities = np.asarray([[0.6, 0.8], [-0.4, 0.3], [0.0, 0.0]])
    positions = np.zeros_like(velocities)
    geometry = Geometry(3, ())
    transverse = VelocityLaw(VelocityParameters(linear=0.0, transverse=-1.5))
    np.testing.assert_allclose(
        np.sum(velocities * transverse.forces(positions, velocities, geometry), axis=1),
        (0.0, 0.0, 0.0),
        rtol=0,
        atol=1e-13,
    )
    combined = VelocityLaw(VelocityParameters(linear=0.4, cubic=0.2, transverse=-1.5))
    np.testing.assert_allclose(
        np.sum(velocities * combined.forces(positions, velocities, geometry), axis=1),
        (-0.6, -0.1125, 0.0),
        rtol=0,
        atol=1e-13,
    )


@dataclass(frozen=True)
class InvalidShapeForce:
    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        return np.zeros((len(positions), 3), dtype=np.float64)


def test_wrong_force_shape_fails_without_a_trajectory() -> None:
    with pytest.raises(SimulationError, match="invalid array"):
        simulate(
            _space(),
            Experiment(particles=(ParticleInitial(id="p", position=(0.2, 0.3)),)),
            InvalidShapeForce(),
            noise_seed=0,
        )
