"""Fixed-step RK4 integration with independent observation noise."""

from __future__ import annotations

import numpy as np

from strange_physics.contracts import Experiment, ExperimentSpace, Frame, Trajectory
from strange_physics.laws import FloatArray, ForceLaw, Geometry


class SimulationError(RuntimeError):
    """The simulator could not produce a finite, well-formed trajectory."""


def simulate(
    space: ExperimentSpace,
    experiment: Experiment,
    law: ForceLaw,
    *,
    noise_seed: int,
    experiment_index: int = 0,
) -> Trajectory:
    space.validate_experiment(experiment)
    if noise_seed < 0 or experiment_index < 0:
        raise ValueError("noise seed and experiment index cannot be negative")
    mobile = len(experiment.particles)
    count = mobile + len(space.structure.anchors)
    state = np.zeros((count, 4), dtype=np.float64)
    masses = np.ones(count, dtype=np.float64)
    for index, particle in enumerate(experiment.particles):
        state[index, :2] = particle.position
        state[index, 2:] = particle.velocity
        masses[index] = particle.mass
    for index, anchor in enumerate(space.structure.anchors, mobile):
        state[index, :2] = anchor.position
    if experiment.impulse:
        target = space.structure.particle_ids.index(experiment.impulse.particle_id)
        state[target, 2:] += np.asarray(experiment.impulse.vector) / masses[target]

    geometry = Geometry.from_structure(space.structure)
    config = space.sampling
    steps = round(config.duration / config.dt)
    stride = round(config.sample_interval / config.dt)
    # Domain-separated streams keep observation noise independent of action selection.
    rng = np.random.default_rng(np.random.SeedSequence([noise_seed, experiment_index, 1]))

    def derivative(current: FloatArray) -> FloatArray:
        if not np.isfinite(current).all() or np.max(np.abs(current)) > 1e6:
            raise SimulationError("state exceeded the supported numerical domain")
        positions, velocities = current[:, :2].view(), current[:, 2:].view()
        positions.flags.writeable = False
        velocities.flags.writeable = False
        force = np.asarray(law.forces(positions, velocities, geometry), dtype=np.float64)
        if force.shape != (count, 2) or not np.isfinite(force).all():
            raise SimulationError("force plugin returned an invalid array")
        result = np.zeros_like(current)
        result[:mobile, :2] = current[:mobile, 2:]
        result[:mobile, 2:] = force[:mobile] / masses[:mobile, None]
        return result

    def observe(step: int) -> Frame:
        positions = state[:mobile, :2] + rng.normal(0, config.position_noise, (mobile, 2))
        velocities = state[:mobile, 2:] + rng.normal(0, config.velocity_noise, (mobile, 2))
        return Frame(
            time=step * config.dt,
            positions=tuple((float(row[0]), float(row[1])) for row in positions),
            velocities=tuple((float(row[0]), float(row[1])) for row in velocities),
        )

    frames = [observe(0)]
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            for step in range(1, steps + 1):
                k1 = derivative(state)
                k2 = derivative(state + config.dt * k1 / 2)
                k3 = derivative(state + config.dt * k2 / 2)
                k4 = derivative(state + config.dt * k3)
                state = state + config.dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
                if not np.isfinite(state).all() or np.max(np.abs(state)) > 1e6:
                    raise SimulationError("integration left the supported numerical domain")
                if step % stride == 0:
                    frames.append(observe(step))
    except (FloatingPointError, OverflowError) as error:
        raise SimulationError("numerical integration failed") from error
    return Trajectory(frames=tuple(frames))
