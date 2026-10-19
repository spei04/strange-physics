from __future__ import annotations

import pytest

from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentSpace,
    ParticleInitial,
    Sampling,
    Structure,
)
from strange_physics.laws import LawSpec
from strange_physics.worlds import WorldDefinition


@pytest.fixture
def space() -> ExperimentSpace:
    return ExperimentSpace(
        structure=Structure(
            particle_ids=("p",),
            anchors=(Anchor(id="a", position=(0.0, 0.0)),),
            connections=(Connection(a="p", b="a"),),
        ),
        sampling=Sampling(),
        budget=6,
        calibration_experiments=2,
    )


@pytest.fixture
def experiment() -> Experiment:
    return Experiment(particles=(ParticleInitial(id="p", position=(1.0, 0.0)),))


@pytest.fixture
def world(space: ExperimentSpace) -> WorldDefinition:
    return WorldDefinition(
        space=space,
        noise_seed=71,
        initial_law=LawSpec(kind="spring", parameters={"linear": 1.0}),
        changed_law=LawSpec(kind="spring", parameters={"linear": 2.0}),
        change_after=3,
    )
