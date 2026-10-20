"""Private read-only snapshot of a quiescent rollback-mode local journal."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from strange_physics import __version__
from strange_physics.contracts import Experiment, ExperimentRecord, ObservationBundle
from strange_physics.journal import APPLICATION_ID
from strange_physics.laws import reference_registry
from strange_physics.serialization import engine_fingerprint
from strange_physics.workflow_io import WorkflowError, private_stat, read_bytes, safe_path
from strange_physics.worlds import WorldDefinition

MAX_JOURNAL_BYTES = 128 * 1024 * 1024
MAX_JSON_TOTAL = 64 * 1024 * 1024
MAX_CELL_BYTES = 1024 * 1024


@dataclass(frozen=True)
class JournalSnapshot:
    """Evaluator-only: never send this value to the fitter or predictor."""

    observations: ObservationBundle
    world: WorldDefinition
    journal_bytes_sha256: str


def _quiescent(path: Path) -> None:
    private_stat(path.stat())
    total = path.stat().st_size
    sidecars = tuple(Path(str(path) + suffix) for suffix in ("-wal", "-shm", "-journal"))
    for sidecar in sidecars:
        if sidecar.exists() or sidecar.is_symlink():
            if sidecar.is_symlink():
                raise WorkflowError("journal_nonquiescent")
            total += sidecar.stat().st_size
    if total > MAX_JOURNAL_BYTES:
        raise WorkflowError("input_limit")
    if any(s.exists() or s.is_symlink() for s in sidecars):
        raise WorkflowError("journal_nonquiescent")


def read_journal(path: Path) -> JournalSnapshot:
    """Reject live/recovery journals; never recover, resume or change their files."""
    path = safe_path(path)
    _quiescent(path)
    before = read_bytes(path, limit=MAX_JOURNAL_BYTES)
    if before[:16] != b"SQLite format 3\x00" or len(before) < 100:
        raise WorkflowError("journal_invalid")
    if before[18:20] != b"\x01\x01":
        raise WorkflowError("journal_nonquiescent")
    digest = hashlib.sha256(before).hexdigest()
    del before
    db: sqlite3.Connection | None = None
    try:
        db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 2 * MAX_CELL_BYTES + 8192)
        db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8192)
        steps = 0

        def budget() -> int:
            nonlocal steps
            steps += 1000
            return int(steps > 2_000_000)

        db.set_progress_handler(budget, 1000)
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("BEGIN")
        if (
            db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != 1
        ):
            raise WorkflowError("journal_invalid")
        tables = db.execute(
            "SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 5"
        ).fetchall()
        if set(tables) != {(n, "table") for n in ("run", "experiments", "checkpoints", "failures")}:
            raise WorkflowError("journal_invalid")
        if db.execute("SELECT COUNT(*) FROM run").fetchone()[0] != 1:
            raise WorkflowError("journal_invalid")
        world_size = db.execute("SELECT length(CAST(world_json AS BLOB)) FROM run").fetchone()[0]
        counts = db.execute(
            "SELECT COUNT(*), SUM(record_json IS NULL), "
            "COALESCE(SUM(length(CAST(request_json AS BLOB)) + "
            "length(CAST(record_json AS BLOB))),0), "
            "COALESCE(MAX(length(CAST(request_json AS BLOB))),0), "
            "COALESCE(MAX(length(CAST(record_json AS BLOB))),0) FROM experiments"
        ).fetchone()
        if counts[0] > 10_000 or world_size > MAX_CELL_BYTES or max(counts[3:]) > MAX_CELL_BYTES:
            raise WorkflowError("input_limit")
        if counts[1]:
            raise WorkflowError("journal_nonquiescent")
        if world_size + counts[2] > MAX_JSON_TOTAL:
            raise WorkflowError("input_limit")
        run_id, world_json, fingerprint = db.execute(
            "SELECT id, world_json, engine_fingerprint FROM run"
        ).fetchone()
        if fingerprint != engine_fingerprint(reference_registry()):
            raise WorkflowError("journal_mismatch")
        world = WorldDefinition.model_validate_json(world_json)
        records: list[ExperimentRecord] = []
        cursor = db.execute(
            "SELECT operation_id, ordinal, request_json, record_json "
            "FROM experiments ORDER BY ordinal"
        )
        for operation_id, ordinal, request_json, record_json in cursor:
            request = Experiment.model_validate_json(request_json)
            record = ExperimentRecord.model_validate_json(record_json)
            if (
                ordinal != len(records)
                or record.index != ordinal
                or record.operation_id != operation_id
                or record.experiment != request
            ):
                raise WorkflowError("journal_mismatch")
            records.append(record)
        observations = ObservationBundle(
            run_id=run_id,
            engine_version=__version__,
            engine_fingerprint=fingerprint,
            space=world.space,
            records=tuple(records),
        )
        db.execute("ROLLBACK")
    except (sqlite3.Error, ValidationError, TypeError, OverflowError):
        raise WorkflowError("journal_invalid") from None
    finally:
        if db is not None:
            db.close()
    _quiescent(path)
    if hashlib.sha256(read_bytes(path, limit=MAX_JOURNAL_BYTES)).hexdigest() != digest:
        raise WorkflowError("journal_mismatch")
    return JournalSnapshot(observations, world, digest)
