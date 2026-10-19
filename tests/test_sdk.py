from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic import JsonValue

from strange_physics.contracts import Experiment, ExperimentRecord
from strange_physics.journal import IncompatibleRun
from strange_physics.sdk import AgentView, RandomAgent, random_experiment, run_agent
from strange_physics.session import LocalSession
from strange_physics.worlds import WorldDefinition, reference_world


def test_checkpointed_resume_matches_uninterrupted_run(
    tmp_path: Path, world: WorldDefinition
) -> None:
    with LocalSession.create(tmp_path / "complete.sqlite", "run", world) as session:
        expected = run_agent(session, RandomAgent(15))
    path = tmp_path / "resumed.sqlite"
    with LocalSession.create(path, "run", world) as session:
        partial = run_agent(session, RandomAgent(15), max_new_experiments=3)
        assert len(partial.records) == 3
    with LocalSession.open(path) as session:
        assert run_agent(session, RandomAgent(15)) == expected
        checkpoint = session.checkpoint(RandomAgent(15).identity)
        assert checkpoint is not None
        assert checkpoint.state == {"completed": world.space.budget}


@dataclass
class CountingAgent:
    crash_on: int | None = None
    identity: str = "counting-v1"

    def initial_state(self) -> dict[str, JsonValue]:
        return {"seen": 0}

    def select(self, view: AgentView) -> Experiment:
        return random_experiment(view.space, seed=9, index=len(view.history))

    def observe(self, view: AgentView, result: ExperimentRecord) -> dict[str, JsonValue]:
        if result.index == self.crash_on:
            raise RuntimeError("worker terminated before checkpoint")
        count = view.state["seen"]
        assert isinstance(count, int)
        return {"seen": count + 1}


def test_crash_after_committed_result_replays_only_uncheckpointed_observation(
    tmp_path: Path,
    world: WorldDefinition,
) -> None:
    path = tmp_path / "run.sqlite"
    with LocalSession.create(path, "run", world) as session:
        with pytest.raises(RuntimeError, match="terminated"):
            run_agent(session, CountingAgent(crash_on=2))
        assert len(session.records()) == 3
        checkpoint = session.checkpoint("counting-v1")
        assert checkpoint is not None
        assert checkpoint.through_index == 1
    with LocalSession.open(path) as session:
        actual = run_agent(session, CountingAgent())
        saved = session.checkpoint("counting-v1")
        assert saved is not None
        assert saved.state == {"seen": world.space.budget}
    with LocalSession.create(tmp_path / "reference.sqlite", "run", world) as session:
        assert actual == run_agent(session, CountingAgent())


def test_calibration_is_shared_but_adaptive_choices_differ(
    tmp_path: Path,
    world: WorldDefinition,
) -> None:
    with LocalSession.create(tmp_path / "one.sqlite", "run", world) as session:
        one = run_agent(session, RandomAgent(10))
    with LocalSession.create(tmp_path / "two.sqlite", "run", world) as session:
        two = run_agent(session, RandomAgent(20))
    calibration = world.space.calibration_experiments
    assert one.records[:calibration] == two.records[:calibration]
    assert one.records[calibration].experiment != two.records[calibration].experiment


def test_cannot_silently_resume_with_different_agent(
    tmp_path: Path, world: WorldDefinition
) -> None:
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        run_agent(session, RandomAgent(1), max_new_experiments=1)
        with pytest.raises(IncompatibleRun, match="agent identity"):
            run_agent(session, RandomAgent(2))


@pytest.mark.parametrize("family", ["spring", "radial", "velocity"])
@pytest.mark.parametrize("particles", [1, 3, 8])
def test_reference_families_support_full_particle_range(
    tmp_path: Path,
    family: str,
    particles: int,
) -> None:
    world = reference_world(family, seed=17, particles=particles, budget=8)
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        result = run_agent(session, RandomAgent(19))
    assert len(result.records) == 8
    assert all(record.status == "completed" for record in result.records)
    assert all(
        record.trajectory and len(record.trajectory.frames[0].positions) == particles
        for record in result.records
    )
