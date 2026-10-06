from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentSpace,
    Impulse,
    ParticleInitial,
    Sampling,
    Structure,
)
from strange_physics.sdk import random_experiment


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_input_is_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        ParticleInitial(id="p", position=(value, 0.0))
    with pytest.raises(ValidationError):
        Sampling(position_noise=value)


def test_unrecognized_fields_and_coercions_are_rejected(experiment: Experiment) -> None:
    payload = experiment.model_dump(mode="json")
    payload["duration"] = 100
    with pytest.raises(ValidationError, match="Extra inputs"):
        Experiment.model_validate_json(json.dumps(payload))
    payload.pop("duration")
    payload["particles"][0]["mass"] = "1.0"
    with pytest.raises(ValidationError):
        Experiment.model_validate_json(json.dumps(payload))


def test_json_round_trip_preserves_tuple_contract(experiment: Experiment) -> None:
    assert Experiment.model_validate_json(experiment.model_dump_json()) == experiment


@pytest.mark.parametrize(
    "edges",
    [
        (Connection(a="p", b="p"),),
        (Connection(a="p", b="missing"),),
        (Connection(a="p", b="a"), Connection(a="a", b="p")),
    ],
)
def test_bad_topology_is_rejected(edges: tuple[Connection, ...]) -> None:
    with pytest.raises(ValidationError):
        Structure(
            particle_ids=("p",), anchors=(Anchor(id="a", position=(0.0, 0.0)),), connections=edges
        )


def test_particle_and_anchor_names_cannot_collide() -> None:
    with pytest.raises(ValidationError):
        Structure(particle_ids=("p",), anchors=(Anchor(id="p", position=(0.0, 0.0)),))


@pytest.mark.parametrize(
    "settings",
    [
        {"dt": 0.03},
        {"sample_interval": 0.07},
        {"sample_interval": 0.005},
        {"duration": 10.0, "dt": 0.0001, "sample_interval": 0.1},
    ],
)
def test_misaligned_or_excessive_grids_are_rejected(settings: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        Sampling.model_validate(settings)


def test_space_rejects_out_of_range_actions(space: ExperimentSpace) -> None:
    for position, mass in [((2.1, 0.0), 1.0), ((0.0, 0.0), 0.1)]:
        experiment = Experiment(particles=(ParticleInitial(id="p", position=position, mass=mass),))
        with pytest.raises(ValueError):
            space.validate_experiment(experiment)
    experiment = Experiment(
        particles=(ParticleInitial(id="p", position=(0.0, 0.0)),),
        impulse=Impulse(particle_id="p", vector=(1.0, 1.0)),
    )
    with pytest.raises(ValueError, match="impulse"):
        space.validate_experiment(experiment)


def test_sampler_respects_published_bounds(space: ExperimentSpace) -> None:
    for index in range(100):
        space.validate_experiment(random_experiment(space, seed=11, index=index))
