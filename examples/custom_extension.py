"""Add a trusted local force family and agent without modifying the core package."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import numpy as np
from pydantic import Field, JsonValue

from strange_physics.contracts import (
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Message,
    ObservationBundle,
    ParticleInitial,
    Sampling,
    Structure,
)
from strange_physics.laws import FloatArray, Geometry, LawSpec, reference_registry
from strange_physics.sdk import AgentView, run_agent
from strange_physics.session import LocalSession
from strange_physics.worlds import WorldDefinition


class FieldParameters(Message):
    horizontal_force: Annotated[float, Field(ge=-1, le=1)]


@dataclass(frozen=True)
class UniformField:
    parameters: FieldParameters

    def forces(
        self,
        positions: FloatArray,
        velocities: FloatArray,
        geometry: Geometry,
    ) -> FloatArray:
        result = np.zeros_like(positions)
        result[:, 0] = self.parameters.horizontal_force
        return result


@dataclass(frozen=True)
class MassSweep:
    identity: str = "mass-sweep-v1"

    def initial_state(self) -> dict[str, JsonValue]:
        return {"completed": 0}

    def select(self, view: AgentView) -> Experiment:
        fraction = len(view.history) / max(1, view.space.budget - 1)
        mass = view.space.limits.min_mass + fraction * (
            view.space.limits.max_mass - view.space.limits.min_mass
        )
        return Experiment(
            particles=tuple(
                ParticleInitial(id=identity, position=(0.0, 0.0), mass=mass)
                for identity in view.space.structure.particle_ids
            )
        )

    def observe(self, view: AgentView, result: ExperimentRecord) -> dict[str, JsonValue]:
        return {"completed": result.index + 1}


def investigate(directory: Path) -> ObservationBundle:
    registry = reference_registry()
    registry.register(
        "uniform-field",
        lambda parameters: UniformField(FieldParameters.model_validate(dict(parameters))),
        implementation_id="uniform-field-v1",
    )
    path = directory / "session.sqlite"
    if path.exists():
        session = LocalSession.open(path, registry=registry)
    else:
        world = WorldDefinition(
            space=ExperimentSpace(
                structure=Structure(particle_ids=("probe",)),
                sampling=Sampling(),
                budget=8,
                calibration_experiments=4,
            ),
            initial_law=LawSpec(kind="uniform-field", parameters={"horizontal_force": 0.2}),
            changed_law=LawSpec(kind="uniform-field", parameters={"horizontal_force": -0.2}),
            change_after=4,
            noise_seed=0,
        )
        session = LocalSession.create(path, "custom-investigation", world, registry=registry)
    with session:
        return run_agent(session, MassSweep())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    bundle = investigate(args.directory)
    print(f"Recorded {len(bundle.records)} experiments in {args.directory}")
