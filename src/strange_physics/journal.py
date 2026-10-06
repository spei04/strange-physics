"""Transactional local run journal. Hosted execution will use PostgreSQL."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from strange_physics.contracts import Checkpoint, Experiment, ExperimentRecord
from strange_physics.serialization import canonical_json
from strange_physics.worlds import WorldDefinition

APPLICATION_ID = 0x53504859


class BudgetExhausted(RuntimeError):
    pass


class IdempotencyConflict(ValueError):
    pass


class IncompatibleRun(ValueError):
    pass


@dataclass(frozen=True)
class Reservation:
    index: int
    record: ExperimentRecord | None


class Journal:
    def __init__(self, path: Path, *, create: bool = False) -> None:
        if path.is_symlink():
            raise ValueError("a run journal cannot be a symbolic link")
        if create:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        elif not path.is_file():
            raise FileNotFoundError(path)
        self._db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self._db.row_factory = sqlite3.Row
        if create:
            self._db.executescript(f"""
                PRAGMA application_id = {APPLICATION_ID};
                PRAGMA user_version = 1;
                CREATE TABLE run (
                    id TEXT PRIMARY KEY, world_json TEXT NOT NULL,
                    engine_fingerprint TEXT NOT NULL, agent_id TEXT
                );
                CREATE TABLE experiments (
                    operation_id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE NOT NULL,
                    request_json TEXT NOT NULL, record_json TEXT
                );
                CREATE TABLE checkpoints (
                    agent_id TEXT PRIMARY KEY, checkpoint_json TEXT NOT NULL
                );
                CREATE TABLE failures (
                    operation_id TEXT PRIMARY KEY, exception_type TEXT NOT NULL,
                    stack_locations TEXT NOT NULL
                );
            """)
        elif (
            self._db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or self._db.execute("PRAGMA user_version").fetchone()[0] != 1
        ):
            self.close()
            raise IncompatibleRun("unrecognized journal format")
        os.chmod(path, 0o600)
        self._db.execute("PRAGMA synchronous = FULL")

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._db.execute("ROLLBACK")
            raise
        else:
            self._db.execute("COMMIT")

    def initialize(self, run_id: str, world: WorldDefinition, fingerprint: str) -> None:
        with self._transaction():
            self._db.execute(
                "INSERT INTO run VALUES (?, ?, ?, NULL)",
                (run_id, world.model_dump_json(), fingerprint),
            )

    def configuration(self) -> tuple[str, WorldDefinition, str]:
        row = self._db.execute("SELECT id, world_json, engine_fingerprint FROM run").fetchone()
        if row is None:
            raise IncompatibleRun("journal initialization is incomplete")
        return str(row[0]), WorldDefinition.model_validate_json(row[1]), str(row[2])

    @property
    def used(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM experiments").fetchone()[0])

    def bind_agent(self, agent_id: str) -> None:
        with self._transaction():
            row = self._db.execute("SELECT agent_id FROM run").fetchone()
            if row is None:
                raise IncompatibleRun("journal initialization is incomplete")
            if row[0] is not None and row[0] != agent_id:
                raise IncompatibleRun("this investigation belongs to a different agent identity")
            self._db.execute("UPDATE run SET agent_id = ?", (agent_id,))

    def record_failure(self, operation_id: str, exception_type: str, locations: list[str]) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO failures VALUES (?, ?, ?)",
            (operation_id, exception_type[:256], canonical_json(locations[-20:])),
        )

    def reserve(self, operation_id: str, experiment: Experiment, budget: int) -> Reservation:
        request = canonical_json(experiment.model_dump(mode="json"))
        with self._transaction():
            row = self._db.execute(
                "SELECT ordinal, request_json, record_json FROM experiments WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if row is not None:
                if row[1] != request:
                    raise IdempotencyConflict(
                        "operation identity was already used for another request"
                    )
                return Reservation(
                    int(row[0]), ExperimentRecord.model_validate_json(row[2]) if row[2] else None
                )
            used = self.used
            if used >= budget:
                raise BudgetExhausted("the experiment budget is exhausted")
            self._db.execute(
                "INSERT INTO experiments VALUES (?, ?, ?, NULL)", (operation_id, used, request)
            )
            return Reservation(used, None)

    def commit(self, record: ExperimentRecord) -> ExperimentRecord:
        with self._transaction():
            row = self._db.execute(
                "SELECT ordinal, request_json, record_json FROM experiments WHERE operation_id = ?",
                (record.operation_id,),
            ).fetchone()
            if (
                row is None
                or int(row[0]) != record.index
                or row[1] != canonical_json(record.experiment.model_dump(mode="json"))
            ):
                raise IdempotencyConflict("result does not match a reserved experiment")
            if row[2] is not None:
                return ExperimentRecord.model_validate_json(row[2])
            self._db.execute(
                "UPDATE experiments SET record_json = ? WHERE operation_id = ?",
                (record.model_dump_json(), record.operation_id),
            )
        return record

    def records(self) -> tuple[ExperimentRecord, ...]:
        rows = self._db.execute(
            "SELECT record_json FROM experiments WHERE record_json IS NOT NULL ORDER BY ordinal"
        ).fetchall()
        return tuple(ExperimentRecord.model_validate_json(row[0]) for row in rows)

    def pending(self) -> tuple[tuple[str, Experiment], ...]:
        rows = self._db.execute(
            "SELECT operation_id, request_json FROM experiments "
            "WHERE record_json IS NULL ORDER BY ordinal"
        ).fetchall()
        return tuple((str(row[0]), Experiment.model_validate_json(row[1])) for row in rows)

    def checkpoint(self, agent_id: str) -> Checkpoint | None:
        row = self._db.execute(
            "SELECT checkpoint_json FROM checkpoints WHERE agent_id = ?", (agent_id,)
        ).fetchone()
        return Checkpoint.model_validate_json(row[0]) if row else None

    def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        payload = canonical_json(checkpoint.model_dump(mode="json"))
        if len(payload.encode()) > 262_144:
            raise ValueError("checkpoint state exceeds 256 KiB; store bulk data as artifacts")
        with self._transaction():
            rows = self._db.execute(
                "SELECT ordinal, record_json FROM experiments ORDER BY ordinal"
            ).fetchall()
            prefix = -1
            for row in rows:
                if row[1] is None:
                    break
                prefix = int(row[0])
            if checkpoint.through_index > prefix:
                raise ValueError("checkpoint cannot include uncommitted experiments")
            previous = self.checkpoint(checkpoint.agent_id)
            if previous:
                if previous.through_index > checkpoint.through_index:
                    raise ValueError("checkpoint cannot move backwards")
                if previous.through_index == checkpoint.through_index and previous != checkpoint:
                    raise IdempotencyConflict("a committed checkpoint is immutable")
            self._db.execute(
                "INSERT INTO checkpoints VALUES (?, ?) "
                "ON CONFLICT(agent_id) DO UPDATE SET checkpoint_json = excluded.checkpoint_json",
                (checkpoint.agent_id, payload),
            )

    def close(self) -> None:
        self._db.close()
