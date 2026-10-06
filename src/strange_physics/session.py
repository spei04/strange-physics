"""Trusted local execution adapter with durable experiment and checkpoint identities."""

from __future__ import annotations

import traceback as traceback_module
from pathlib import Path
from types import TracebackType
from typing import Annotated

from pydantic import Field, TypeAdapter

from strange_physics import __version__
from strange_physics.contracts import (
    Checkpoint,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Identifier,
    ObservationBundle,
)
from strange_physics.journal import IncompatibleRun, Journal
from strange_physics.laws import LawRegistry, reference_registry
from strange_physics.serialization import engine_fingerprint
from strange_physics.simulation import simulate
from strange_physics.worlds import WorldDefinition

_identifier: TypeAdapter[str] = TypeAdapter(Annotated[Identifier, Field(strict=True)])


class LocalSession:
    """In-process adapter for trusted research code, not a hosted-code sandbox."""

    def __init__(self, journal: Journal, registry: LawRegistry) -> None:
        self._journal = journal
        self._registry = registry
        self.run_id, self._world, fingerprint = journal.configuration()
        self._fingerprint = fingerprint
        if fingerprint != engine_fingerprint(registry):
            raise IncompatibleRun("source, runtime, dependencies or registered plugins changed")
        # Validate both regimes before the first experiment can consume budget.
        registry.build(self._world.initial_law)
        if self._world.changed_law:
            registry.build(self._world.changed_law)

    @classmethod
    def create(
        cls,
        path: Path,
        run_id: str,
        world: WorldDefinition,
        *,
        registry: LawRegistry | None = None,
    ) -> LocalSession:
        _identifier.validate_python(run_id)
        registry = registry or reference_registry()
        registry.build(world.initial_law)
        if world.changed_law:
            registry.build(world.changed_law)
        journal = Journal(path, create=True)
        try:
            journal.initialize(run_id, world, engine_fingerprint(registry))
            return cls(journal, registry)
        except BaseException:
            journal.close()
            raise

    @classmethod
    def open(cls, path: Path, *, registry: LawRegistry | None = None) -> LocalSession:
        journal = Journal(path)
        try:
            return cls(journal, registry or reference_registry())
        except BaseException:
            journal.close()
            raise

    @property
    def space(self) -> ExperimentSpace:
        return self._world.space

    @property
    def remaining_budget(self) -> int:
        return self.space.budget - self._journal.used

    def records(self) -> tuple[ExperimentRecord, ...]:
        return self._journal.records()

    def bind_agent(self, agent_id: str) -> None:
        _identifier.validate_python(agent_id)
        self._journal.bind_agent(agent_id)

    def run_experiment(self, experiment: Experiment, *, operation_id: str) -> ExperimentRecord:
        _identifier.validate_python(operation_id)
        self.space.validate_experiment(experiment)
        reservation = self._journal.reserve(operation_id, experiment, self.space.budget)
        if reservation.record:
            return reservation.record
        try:
            law = self._registry.build(self._world.law_at(reservation.index))
            trajectory = simulate(
                self.space,
                experiment,
                law,
                noise_seed=self._world.noise_seed,
                experiment_index=reservation.index,
            )
        except Exception as error:
            # Plugin exceptions can contain private parameters. The public outcome is a code;
            # trusted operators retain stack locations and inputs to reproduce the failure.
            frames = traceback_module.extract_tb(error.__traceback__)
            self._journal.record_failure(
                operation_id,
                type(error).__name__,
                [f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}" for frame in frames],
            )
            record = ExperimentRecord(
                operation_id=operation_id,
                index=reservation.index,
                experiment=experiment,
                status="failed",
                error="simulation_failed",
            )
        else:
            record = ExperimentRecord(
                operation_id=operation_id,
                index=reservation.index,
                experiment=experiment,
                status="completed",
                trajectory=trajectory,
            )
        return self._journal.commit(record)

    def resume_pending(self) -> tuple[ExperimentRecord, ...]:
        return tuple(
            self.run_experiment(experiment, operation_id=key)
            for key, experiment in self._journal.pending()
        )

    def checkpoint(self, agent_id: str) -> Checkpoint | None:
        _identifier.validate_python(agent_id)
        return self._journal.checkpoint(agent_id)

    def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        self._journal.save_checkpoint(checkpoint)

    def export(self) -> ObservationBundle:
        if self._journal.pending():
            raise ValueError("resume pending experiments before exporting the observation history")
        return ObservationBundle(
            run_id=self.run_id,
            engine_version=__version__,
            engine_fingerprint=self._fingerprint,
            space=self.space,
            records=self.records(),
        )

    def close(self) -> None:
        self._journal.close()

    def __enter__(self) -> LocalSession:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
