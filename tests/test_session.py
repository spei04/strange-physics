from __future__ import annotations

import json
import sqlite3
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from strange_physics.contracts import Checkpoint, Experiment, ObservationBundle, ParticleInitial
from strange_physics.journal import BudgetExhausted, IdempotencyConflict, IncompatibleRun, Journal
from strange_physics.laws import FloatArray, Geometry, LawSpec, reference_registry
from strange_physics.session import LocalSession
from strange_physics.worlds import WorldDefinition


def test_idempotent_retry_does_not_spend_another_experiment(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        first = session.run_experiment(experiment, operation_id="same")
        assert session.run_experiment(experiment, operation_id="same") == first
        assert session.remaining_budget == world.space.budget - 1
        assert len(session.records()) == 1
        changed = Experiment(particles=(ParticleInitial(id="p", position=(0.5, 0.0)),))
        with pytest.raises(IdempotencyConflict):
            session.run_experiment(changed, operation_id="same")


def test_budget_is_enforced_but_old_requests_remain_retrievable(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        for index in range(world.space.budget):
            session.run_experiment(experiment, operation_id=f"step-{index}")
        with pytest.raises(BudgetExhausted):
            session.run_experiment(experiment, operation_id="extra")
        assert session.run_experiment(experiment, operation_id="step-0").index == 0
        assert session.remaining_budget == 0


def test_invalid_requests_do_not_consume_budget(tmp_path: Path, world: WorldDefinition) -> None:
    invalid = Experiment(particles=(ParticleInitial(id="p", position=(50.0, 0.0)),))
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        with pytest.raises(ValueError, match="position"):
            session.run_experiment(invalid, operation_id="invalid")
        assert session.remaining_budget == world.space.budget


def test_regime_persists_across_resets_and_process_reopen(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    path = tmp_path / "run.sqlite"
    with LocalSession.create(path, "run", world) as session:
        first = session.run_experiment(experiment, operation_id="before-0")
        assert (
            session.run_experiment(experiment, operation_id="before-1").trajectory
            == first.trajectory
        )
    with LocalSession.open(path) as session:
        assert (
            session.run_experiment(experiment, operation_id="before-2").trajectory
            == first.trajectory
        )
        changed = session.run_experiment(experiment, operation_id="after-3")
        assert changed.trajectory != first.trajectory
        assert (
            session.run_experiment(experiment, operation_id="after-4").trajectory
            == changed.trajectory
        )


def test_public_bundle_contains_no_hidden_configuration(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    with LocalSession.create(tmp_path / "run.sqlite", "opaque-id", world) as session:
        session.run_experiment(experiment, operation_id="step")
        payload = session.export().model_dump_json()
        for private_key in (
            "initial_law",
            "changed_law",
            "change_after",
            "noise_seed",
            "parameters",
        ):
            assert private_key not in payload
        assert "spring" not in payload
        assert ObservationBundle.model_validate_json(payload) == session.export()


def test_private_journal_permissions(tmp_path: Path, world: WorldDefinition) -> None:
    path = tmp_path / "run.sqlite"
    with LocalSession.create(path, "run", world):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        LocalSession.create(path, "replacement", world)


def test_an_unrelated_database_is_not_modified(tmp_path: Path) -> None:
    path = tmp_path / "other.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE original (value TEXT)")
    before = path.read_bytes()
    with pytest.raises(IncompatibleRun, match="unrecognized"):
        LocalSession.open(path)
    assert path.read_bytes() == before


def test_reserved_experiment_survives_crash_before_simulation(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    path = tmp_path / "run.sqlite"
    LocalSession.create(path, "run", world).close()
    journal = Journal(path)
    journal.reserve("step", experiment, world.space.budget)
    journal.close()
    with LocalSession.open(path) as session:
        assert session.remaining_budget == world.space.budget - 1
        with pytest.raises(ValueError, match="pending"):
            session.export()
        recovered = session.resume_pending()
        assert len(recovered) == 1
        assert recovered[0].status == "completed"
        assert session.remaining_budget == world.space.budget - 1


def test_concurrent_retry_has_one_logical_result(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    path = tmp_path / "run.sqlite"
    LocalSession.create(path, "run", world).close()

    def run() -> str:
        with LocalSession.open(path) as session:
            return session.run_experiment(experiment, operation_id="shared").model_dump_json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(2)))
    assert results[0] == results[1]
    with LocalSession.open(path) as session:
        assert len(session.records()) == 1
        assert session.remaining_budget == world.space.budget - 1


class BrokenLaw:
    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        raise ValueError("private-law-coefficient=12345")


def test_plugin_failures_are_recorded_and_consume_budget_without_leaking_details(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    registry = reference_registry()
    registry.register("broken", lambda _: BrokenLaw(), implementation_id="broken-v1")
    definition = WorldDefinition(
        space=world.space, noise_seed=0, initial_law=LawSpec(kind="broken", parameters={})
    )
    path = tmp_path / "run.sqlite"
    with LocalSession.create(path, "run", definition, registry=registry) as session:
        result = session.run_experiment(experiment, operation_id="failure")
        assert result.status == "failed"
        assert result.error == "simulation_failed"
        assert session.remaining_budget == world.space.budget - 1
        assert session.run_experiment(experiment, operation_id="failure") == result
        assert "private-law" not in session.export().model_dump_json()
    with sqlite3.connect(path) as db:
        kind, locations = db.execute(
            "SELECT exception_type, stack_locations FROM failures"
        ).fetchone()
    assert kind == "ValueError"
    assert any("test_session.py" in line for line in json.loads(locations))


def test_checkpoint_is_bounded_monotonic_and_tied_to_committed_work(
    tmp_path: Path,
    world: WorldDefinition,
    experiment: Experiment,
) -> None:
    with LocalSession.create(tmp_path / "run.sqlite", "run", world) as session:
        with pytest.raises(ValueError, match="uncommitted"):
            session.save_checkpoint(Checkpoint(agent_id="agent", through_index=0, state={}))
        session.run_experiment(experiment, operation_id="step")
        saved = Checkpoint(agent_id="agent", through_index=0, state={"count": 1})
        session.save_checkpoint(saved)
        session.save_checkpoint(saved)
        assert session.checkpoint("agent") == saved
        with pytest.raises(ValueError, match="backwards"):
            session.save_checkpoint(Checkpoint(agent_id="agent", through_index=-1, state={}))
        with pytest.raises(IdempotencyConflict, match="immutable"):
            session.save_checkpoint(
                Checkpoint(agent_id="agent", through_index=0, state={"count": 2})
            )
        with pytest.raises(ValueError, match="256 KiB"):
            session.save_checkpoint(
                Checkpoint(agent_id="large", through_index=0, state={"data": "x" * 262_144})
            )
        with pytest.raises(ValueError):
            session.save_checkpoint(
                Checkpoint(agent_id="nonfinite", through_index=0, state={"data": float("nan")})
            )


def test_runtime_mismatch_requires_explicit_migration(
    tmp_path: Path,
    world: WorldDefinition,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "run.sqlite"
    LocalSession.create(path, "run", world).close()
    monkeypatch.setattr("strange_physics.session.engine_fingerprint", lambda _: "different")
    with pytest.raises(IncompatibleRun, match="changed"):
        LocalSession.open(path)
