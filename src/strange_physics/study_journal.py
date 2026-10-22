"""Private, bounded read-only reconciliation of all local Journal reservations.

Pending rows are retained. This adapter never resumes or repairs a Journal, and
never returns its private law/seed or definition hash to numerical producers.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from strange_physics import __version__
from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import (
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    ObservationBundle,
)
from strange_physics.control_contracts import ContractViolation
from strange_physics.journal import APPLICATION_ID
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    MAX_STUDY_JSON_BYTES,
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorldCatalog,
    StudyPurchase,
)
from strange_physics.study_ledger import StudyLedgerError, study_manifest, study_purchase_intents
from strange_physics.workflow_io import private_stat, read_bytes, safe_path
from strange_physics.worlds import WorldDefinition

MAX_JOURNAL_BYTES = 128 * 1024**2
MAX_RECORD_BYTES = 4 * 1024**2
MAX_WORLD_BYTES = 64 * 1024


@dataclass(frozen=True)
class StudyJournalReservation:
    operation_id: str
    ordinal: int
    experiment: Experiment
    record: ExperimentRecord | None


@dataclass(frozen=True)
class StudyJournalSnapshot:
    """Owner-only evidence; only the validated committed prefix may reach N01."""

    cell_id: str
    world_id: str
    journal_id: str
    journal_bytes_sha256: str
    engine_fingerprint: str
    space: ExperimentSpace
    reservations: tuple[StudyJournalReservation, ...]

    def committed_prefix(self) -> ObservationBundle:
        records: list[ExperimentRecord] = []
        for row in self.reservations:
            if row.record is None:
                break
            records.append(row.record)
        return ObservationBundle(
            run_id=self.journal_id,
            engine_version=__version__,
            engine_fingerprint=self.engine_fingerprint,
            space=self.space,
            records=tuple(records),
        )


def _quiescent(path: Path) -> None:
    private_stat(path.stat())
    if path.stat().st_size > MAX_JOURNAL_BYTES:
        raise StudyLedgerError("journal_limit")
    if any(
        Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink()
        for suffix in ("-wal", "-shm", "-journal")
    ):
        raise StudyLedgerError("journal_nonquiescent")


def read_study_journal(
    path: Path, *, manifest: NativeStudyManifest, catalog: NativeWorldCatalog, cell_id: str
) -> StudyJournalSnapshot:
    """Join actual private world, run, engine and every pending/completed/failed row."""
    cells = [cell for cell in manifest.cells if cell.cell_id == cell_id]
    if len(cells) != 1:
        raise StudyLedgerError("unknown_cell")
    cell = cells[0]
    digest, size = bounded_canonical(catalog, MAX_STUDY_JSON_BYTES)
    ref = manifest.artifact("world_catalog")
    if (digest, size) != (ref.sha256, ref.byte_count) or tuple(
        entry.world_id for entry in catalog.worlds
    ) != manifest.world_ids:
        raise StudyLedgerError("world_catalog_mismatch")
    expected_world = next(
        entry.definition for entry in catalog.worlds if entry.world_id == cell.world_id
    )
    path = safe_path(path)
    _quiescent(path)
    before = read_bytes(path, limit=MAX_JOURNAL_BYTES)
    if before[:16] != b"SQLite format 3\x00" or len(before) < 100:
        raise StudyLedgerError("journal_invalid")
    if before[18:20] != b"\x01\x01":
        raise StudyLedgerError("journal_nonquiescent")
    raw_sha = hashlib.sha256(before).hexdigest()
    del before
    db: sqlite3.Connection | None = None
    rows: list[StudyJournalReservation] = []
    try:
        db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 2 * MAX_RECORD_BYTES + 8192)
        db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8192)
        steps = 0

        def progress() -> int:
            nonlocal steps
            steps += 1000
            return int(steps > 2_000_000)

        db.set_progress_handler(progress, 1000)
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("BEGIN")
        if (
            db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != 1
        ):
            raise StudyLedgerError("journal_invalid")
        tables = db.execute(
            "SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 5"
        ).fetchall()
        if set(tables) != {
            (name, "table") for name in ("run", "experiments", "checkpoints", "failures")
        }:
            raise StudyLedgerError("journal_invalid")
        if db.execute("SELECT COUNT(*) FROM run").fetchone()[0] != 1:
            raise StudyLedgerError("journal_invalid")
        sizes = db.execute(
            "SELECT length(CAST(id AS BLOB)), length(CAST(engine_fingerprint AS BLOB)), "
            "length(CAST(world_json AS BLOB)) FROM run"
        ).fetchone()
        if sizes[0] > 64 or sizes[1] != 64 or sizes[2] > MAX_WORLD_BYTES:
            raise StudyLedgerError("journal_limit")
        totals = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(length(CAST(request_json AS BLOB)) + "
            "COALESCE(length(CAST(record_json AS BLOB)),0)),0), "
            "COALESCE(MAX(length(CAST(request_json AS BLOB))),0), "
            "COALESCE(MAX(length(CAST(record_json AS BLOB))),0), "
            "COALESCE(MAX(length(CAST(operation_id AS BLOB))),0) FROM experiments"
        ).fetchone()
        if (
            totals[0] > 12
            or totals[1] > MAX_STUDY_JSON_BYTES
            or max(totals[2:4]) > MAX_RECORD_BYTES
            or totals[4] > 64
        ):
            raise StudyLedgerError("journal_limit")
        run_id, fingerprint, world_json = db.execute(
            "SELECT id, engine_fingerprint, world_json FROM run"
        ).fetchone()
        if (
            run_id != cell.journal_id
            or fingerprint != manifest.engine_fingerprint
            or not isinstance(world_json, str)
        ):
            raise StudyLedgerError("journal_identity_mismatch")
        world = parse_bounded_json(
            world_json.encode(),
            WorldDefinition,
            max_bytes=MAX_WORLD_BYTES,
            max_depth=32,
            max_nodes=100_000,
        )
        if message_sha256(world) != message_sha256(expected_world):
            raise StudyLedgerError("journal_world_mismatch")
        seen: set[str] = set()
        for operation_id, ordinal, request_json, record_json in db.execute(
            "SELECT operation_id, ordinal, request_json, record_json "
            "FROM experiments ORDER BY ordinal"
        ):
            if (
                not isinstance(operation_id, str)
                or operation_id in seen
                or type(ordinal) is not int
                or ordinal != len(rows)
                or not isinstance(request_json, str)
                or (record_json is not None and not isinstance(record_json, str))
            ):
                raise StudyLedgerError("journal_row_mismatch")
            # A tiny typed record validates opaque IDs without inferring a completion.
            request = parse_bounded_json(
                request_json.encode(),
                Experiment,
                max_bytes=MAX_RECORD_BYTES,
                max_depth=32,
                max_nodes=1_000_000,
            )
            world.space.validate_experiment(request)
            StudyPurchase(
                operation_id=operation_id,
                ordinal=ordinal,
                experiment_sha256=message_sha256(request),
                calibration=ordinal < 4,
            )
            record = (
                None
                if record_json is None
                else parse_bounded_json(
                    record_json.encode(),
                    ExperimentRecord,
                    max_bytes=MAX_RECORD_BYTES,
                    max_depth=32,
                    max_nodes=1_000_000,
                )
            )
            if record is not None and (
                record.index != ordinal
                or record.operation_id != operation_id
                or message_sha256(record.experiment) != message_sha256(request)
            ):
                raise StudyLedgerError("journal_row_mismatch")
            rows.append(StudyJournalReservation(operation_id, ordinal, request, record))
            seen.add(operation_id)
        db.execute("ROLLBACK")
    except (sqlite3.Error, TypeError, OverflowError, ValueError) as error:
        if isinstance(error, StudyLedgerError | ContractViolation):
            raise
        raise StudyLedgerError("journal_invalid") from None
    finally:
        if db is not None:
            db.close()
    _quiescent(path)
    if hashlib.sha256(read_bytes(path, limit=MAX_JOURNAL_BYTES)).hexdigest() != raw_sha:
        raise StudyLedgerError("journal_changed")
    result = StudyJournalSnapshot(
        cell_id,
        cell.world_id,
        cell.journal_id,
        raw_sha,
        manifest.engine_fingerprint,
        expected_world.space,
        tuple(rows),
    )
    # Validate every completed row's scientific shape, not only the initial prefix.
    # Single-row trajectory grids are checked using an index-zero projection; its
    # original ordinal/operation/request remain bound above and in the snapshot.
    try:
        for row in result.reservations:
            if row.record is not None:
                ObservationBundle(
                    run_id=result.journal_id,
                    engine_version=__version__,
                    engine_fingerprint=result.engine_fingerprint,
                    space=result.space,
                    records=(row.record.model_copy(update={"index": 0}),),
                )
    except ValueError:
        raise StudyLedgerError("journal_row_mismatch") from None
    return result


@dataclass(frozen=True)
class StudyJournalReconciliation:
    snapshot: StudyJournalSnapshot
    reserved_slots: int
    missing_reservation_ids: tuple[str, ...]
    pending_operation_ids: tuple[str, ...]
    failed_operation_ids: tuple[str, ...]


def reconcile_study_journal(
    ledger: NativeStudyLedger,
    path: Path,
    *,
    catalog: NativeWorldCatalog,
    cell_id: str,
) -> StudyJournalReconciliation:
    """Read actual bytes and join every purchased intent before exposing a prefix.

    Missing Journal rows retain charged intents; extra or different rows fail.
    A snapshot is never accepted as a replacement for reading the actual Journal.
    """
    manifest = study_manifest(ledger)
    intents = study_purchase_intents(ledger, cell_id)
    snapshot = read_study_journal(path, manifest=manifest, catalog=catalog, cell_id=cell_id)
    if len(snapshot.reservations) > len(intents):
        raise StudyLedgerError("untracked_purchase")
    for actual, expected in zip(snapshot.reservations, intents, strict=False):
        if (
            actual.ordinal != expected.ordinal
            or actual.operation_id != expected.operation_id
            or message_sha256(actual.experiment) != expected.experiment_sha256
        ):
            raise StudyLedgerError("purchase_journal_mismatch")
    return StudyJournalReconciliation(
        snapshot=snapshot,
        reserved_slots=len(intents),
        missing_reservation_ids=tuple(
            item.operation_id for item in intents[len(snapshot.reservations) :]
        ),
        pending_operation_ids=tuple(
            row.operation_id for row in snapshot.reservations if row.record is None
        ),
        failed_operation_ids=tuple(
            row.operation_id
            for row in snapshot.reservations
            if row.record is not None and row.record.status == "failed"
        ),
    )
