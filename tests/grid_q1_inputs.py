"""Fixed synthetic GRID-Q1 inputs; no purchase, inference or scientific admission."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

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
from strange_physics.native_endpoint_belief_contracts import EndpointBeliefProfile, EndpointCell
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
)
from strange_physics.research_contracts import message_sha256

type History = Literal["flat", "boundary", "interior"]
HISTORIES: tuple[History, ...] = ("flat", "boundary", "interior")
COUNTS = (64, 256, 1024)
SCALES = (0.125, 0.25, 0.5)


def query(history: History, count: int, scale: float, index: int) -> None:
    if (
        history not in HISTORIES
        or type(count) is not int
        or count not in COUNTS
        or type(scale) is not float
        or scale not in SCALES
        or type(index) is not int
        or not 0 <= index < count
    ):
        raise ValueError("Outside the fixed GRID-Q1 query manifest")


def coefficient(count: int, index: int) -> float:
    query("flat", count, SCALES[0], index)
    return (4 * index + 2) / count


def cells(count: int) -> tuple[EndpointCell, ...]:
    query("flat", count, SCALES[0], 0)
    return tuple(EndpointCell(left=4 * i / count, right=4 * (i + 1) / count) for i in range(count))


def profile(count: int, scale: float) -> EndpointBeliefProfile:
    query("flat", count, scale, 0)
    return EndpointBeliefProfile(discrepancy=scale, cells=cells(count))


@dataclass(frozen=True)
class Fixture:
    label: History
    truth_coefficient: float | None
    observations: ObservationBundle
    terminal_velocity_semantics: Literal["unused-zero-placeholder"] = "unused-zero-placeholder"

    @property
    def space_sha256(self) -> str:
        return message_sha256(self.observations.space)


def fixtures(interior_observed_x: float) -> tuple[Fixture, ...]:
    """Construct complete public-shaped data from a separately justified binary64 label.

    This function does not establish the interior label's reference enclosure.
    The eventual driver must retain that enclosure and one-rounding evidence.
    Velocities are explicit unused synthetic fields, never fitted evidence.
    """
    if (
        type(interior_observed_x) is not float
        or not math.isfinite(interior_observed_x)
        or not 0.5 <= interior_observed_x <= 1.0
    ):
        raise ValueError("Interior label must be an explicit bounded binary64 observation")
    space = ExperimentSpace(
        structure=Structure(
            particle_ids=("p0",),
            anchors=(Anchor(id="a0", position=(0.0, 0.0)),),
            connections=(Connection(a="p0", b="a0"),),
        ),
        sampling=Sampling(
            duration=0.5,
            dt=1 / 64,
            sample_interval=0.5,
            position_noise=0.0,
            velocity_noise=0.0,
        ),
        budget=1,
        calibration_experiments=0,
    )
    result: list[Fixture] = []
    rows: tuple[tuple[History, float, float, float | None], ...] = (
        ("flat", 0.0, 0.0, None),
        ("boundary", 1.0, 1.0, 0.0),
        ("interior", 1.0, interior_observed_x, 1.5),
    )
    for history, initial, observed, truth in rows:
        # History labels are external. Identical physical spaces share a digest.
        experiment = Experiment(
            particles=(ParticleInitial(id="p0", position=(initial, 0.0), mass=1.0),),
            impulse=Impulse(particle_id="p0", vector=(0.0, 0.0)),
        )
        observation = ObservationBundle(
            run_id=f"grid-q1-{history}",
            engine_version="synthetic-grid-q1.v1",
            engine_fingerprint="0" * 64,
            space=space,
            records=(
                ExperimentRecord(
                    operation_id=f"grid-q1-{history}-0",
                    index=0,
                    experiment=experiment,
                    status="completed",
                    trajectory=Trajectory(
                        frames=(
                            Frame(time=0.0, positions=((initial, 0.0),), velocities=((0.0, 0.0),)),
                            Frame(time=0.5, positions=((observed, 0.0),), velocities=((0.0, 0.0),)),
                        )
                    ),
                ),
            ),
        )
        result.append(Fixture(history, truth, observation))
    return tuple(result)


def candidate_input(fixture: Fixture, count: int) -> NativeCandidateInput:
    query(fixture.label, count, SCALES[0], 0)
    return NativeCandidateInput(
        pool=NativeSpringPool(coefficients=tuple(coefficient(count, i) for i in range(count))),
        config=NativeCandidateConfig(),
        observations=fixture.observations,
    )
