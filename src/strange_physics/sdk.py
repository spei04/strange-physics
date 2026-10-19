"""Small agent protocol and recoverable local driver."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from pydantic import JsonValue

from strange_physics.contracts import (
    Checkpoint,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Vector,
)
from strange_physics.serialization import canonical_json
from strange_physics.session import LocalSession


@dataclass(frozen=True)
class AgentView:
    space: ExperimentSpace
    history: tuple[ExperimentRecord, ...]
    state: dict[str, JsonValue]


class Agent(Protocol):
    """Identity includes configuration/version; mutable working state belongs in checkpoints.

    select and observe must derive their output from the supplied view. External
    side effects require their own durable identities; the local driver does not
    promise to restore arbitrary process memory or reissue paid model calls safely.
    """

    @property
    def identity(self) -> str: ...

    def initial_state(self) -> dict[str, JsonValue]: ...

    def select(self, view: AgentView) -> Experiment: ...

    def observe(self, view: AgentView, result: ExperimentRecord) -> dict[str, JsonValue]: ...


def random_experiment(space: ExperimentSpace, *, seed: int, index: int) -> Experiment:
    if not 0 <= seed < 2**64 or index < 0:
        raise ValueError("seed must be unsigned 64-bit and index cannot be negative")
    rng = np.random.default_rng(np.random.SeedSequence([seed, index, 2]))

    def disk(radius: float) -> Vector:
        angle = float(rng.uniform(0, 2 * np.pi))
        distance = radius * float(np.sqrt(rng.uniform()))
        return distance * float(np.cos(angle)), distance * float(np.sin(angle))

    particles = tuple(
        ParticleInitial(
            id=identity,
            position=disk(space.limits.position_norm),
            velocity=disk(space.limits.velocity_norm),
            mass=float(rng.uniform(space.limits.min_mass, space.limits.max_mass)),
        )
        for identity in space.structure.particle_ids
    )
    target = int(rng.integers(len(particles)))
    return Experiment(
        particles=particles,
        impulse=Impulse(
            particle_id=particles[target].id,
            vector=disk(space.limits.impulse_norm),
        ),
    )


@dataclass(frozen=True)
class RandomAgent:
    seed: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.seed < 2**64:
            raise ValueError("agent seed must be an unsigned 64-bit integer")

    @property
    def identity(self) -> str:
        return f"random-v1-{self.seed}"

    def initial_state(self) -> dict[str, JsonValue]:
        return {"completed": 0}

    def select(self, view: AgentView) -> Experiment:
        return random_experiment(view.space, seed=self.seed, index=len(view.history))

    def observe(self, view: AgentView, result: ExperimentRecord) -> dict[str, JsonValue]:
        return {"completed": result.index + 1}


def run_agent(
    session: LocalSession,
    agent: Agent,
    *,
    max_new_experiments: int | None = None,
) -> ObservationBundle:
    """Resume accepted work, replay uncheckpointed observations, then choose new actions."""
    if max_new_experiments is not None and max_new_experiments < 0:
        raise ValueError("maximum new experiments cannot be negative")
    session.bind_agent(agent.identity)
    session.resume_pending()
    checkpoint = session.checkpoint(agent.identity)
    if checkpoint is None:
        checkpoint = Checkpoint(
            agent_id=agent.identity, through_index=-1, state=agent.initial_state()
        )
        session.save_checkpoint(checkpoint)

    def view(history: tuple[ExperimentRecord, ...], saved: Checkpoint) -> AgentView:
        # Do not let an agent mutate the in-memory checkpoint through a nested dictionary.
        state: dict[str, JsonValue] = json.loads(canonical_json(saved.state))
        return AgentView(session.space, history, state)

    history = session.records()
    for result in history:
        if result.index > checkpoint.through_index:
            state = agent.observe(view(history[: result.index], checkpoint), result)
            checkpoint = Checkpoint(
                agent_id=agent.identity, through_index=result.index, state=state
            )
            session.save_checkpoint(checkpoint)

    new_count = 0
    while session.remaining_budget and (
        max_new_experiments is None or new_count < max_new_experiments
    ):
        index = len(history)
        if index < session.space.calibration_experiments:
            experiment = random_experiment(session.space, seed=0, index=index)
        else:
            experiment = agent.select(view(history, checkpoint))
        result = session.run_experiment(experiment, operation_id=f"experiment-{index:05d}")
        state = agent.observe(view(history, checkpoint), result)
        checkpoint = Checkpoint(agent_id=agent.identity, through_index=result.index, state=state)
        session.save_checkpoint(checkpoint)
        history = (*history, result)
        new_count += 1
    return session.export()
