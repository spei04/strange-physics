"""Synthetic SQLite reservation evidence; no simulator or numerical study runs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_study_contracts import EXAMPLES
from test_study_ledger import append, frozen, materials, reserve

from strange_physics import study_contracts as c
from strange_physics import study_journal as j
from strange_physics import study_ledger as l
from strange_physics.contracts import (
    Experiment,
    ExperimentRecord,
    Frame,
    ParticleInitial,
    Trajectory,
)
from strange_physics.control_contracts import ContractViolation
from strange_physics.journal import Journal
from strange_physics.research_contracts import message_sha256
from strange_physics.workflow_io import WorkflowError


def catalog() -> c.NativeWorldCatalog:
    return c.NativeWorldCatalog.model_validate_json(
        json.dumps(EXAMPLES["valid"]["NativeWorldCatalog"])
    )


def experiment() -> Experiment:
    pid = catalog().worlds[0].definition.space.structure.particle_ids[0]
    return Experiment(
        particles=(ParticleInitial(id=pid, position=(0.0, 0.0), velocity=(0.0, 0.0), mass=1.0),),
        impulse=None,
    )


def create(path: Path, statuses: tuple[str, ...] = ()) -> None:
    manifest = materials()[0]
    world = catalog().worlds[0].definition
    db = Journal(path, create=True)
    try:
        db.initialize(manifest.cells[0].journal_id, world, manifest.engine_fingerprint)
        for index, status in enumerate(statuses):
            request = experiment()
            db.reserve(f"operation-{index}", request, 12)
            if status == "pending":
                continue
            if status == "failed":
                record = ExperimentRecord(
                    operation_id=f"operation-{index}",
                    index=index,
                    experiment=request,
                    status="failed",
                    error="simulation_failed",
                )
            else:
                sampling = world.space.sampling
                frames = tuple(
                    Frame(
                        time=k * sampling.sample_interval,
                        positions=((0.0, 0.0),),
                        velocities=((0.0, 0.0),),
                    )
                    for k in range(round(sampling.duration / sampling.sample_interval) + 1)
                )
                record = ExperimentRecord(
                    operation_id=f"operation-{index}",
                    index=index,
                    experiment=request,
                    status="completed",
                    trajectory=Trajectory(frames=frames),
                )
            db.commit(record)
    finally:
        db.close()


def read(path: Path) -> j.StudyJournalSnapshot:
    manifest = materials()[0]
    return j.read_study_journal(
        path, manifest=manifest, catalog=catalog(), cell_id=manifest.cells[0].cell_id
    )


def intent(ledger: c.NativeStudyLedger, index: int) -> c.NativeStudyLedger:
    manifest = materials()[0]
    cell = manifest.cells[0]
    return append(
        ledger,
        reserve(
            f"attempt-{index}",
            phase="comparison",
            cell_id=cell.cell_id,
            operation="purchase",
            config_sha256=manifest.artifact("calibration" if index < 4 else "menu").sha256,
            purchase=dict(
                operation_id=f"operation-{index}",
                ordinal=index,
                experiment_sha256=message_sha256(experiment()),
                calibration=index < 4,
            ),
        ),
    )


def reconcile(ledger: c.NativeStudyLedger, path: Path) -> j.StudyJournalReconciliation:
    return j.reconcile_study_journal(
        ledger, path, catalog=catalog(), cell_id=materials()[0].cells[0].cell_id
    )


def sql(path: Path, statement: str, args: tuple[object, ...] = ()) -> None:
    with sqlite3.connect(path) as db:
        db.execute(statement, args)


def test_empty_and_all_reservation_states_without_science(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path, ("failed", "completed", "pending", "failed"))
    before = path.read_bytes()
    result = read(path)
    assert [r.record.status if r.record else "pending" for r in result.reservations] == [
        "failed",
        "completed",
        "pending",
        "failed",
    ]
    prefix = result.committed_prefix()
    assert [r.status for r in prefix.records] == ["failed", "completed"]
    assert result.journal_bytes_sha256 == hashlib.sha256(before).hexdigest()
    assert path.read_bytes() == before
    assert not hasattr(result, "world") and not hasattr(result, "definition_sha256")


def test_pending_and_failed_calibrations_charged_and_missing_intent_held(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path, ("failed", "pending"))
    ledger = frozen()
    for index in range(3):
        ledger = intent(ledger, index)
    result = reconcile(ledger, path)
    assert result.reserved_slots == 3
    assert result.missing_reservation_ids == ("operation-2",)
    assert result.pending_operation_ids == ("operation-1",)
    assert result.failed_operation_ids == ("operation-0",)
    assert l.summarize_study(ledger).budget.purchased_slots == 3


def test_actual_untracked_reservation_never_assumed_free(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path, ("pending",))
    with pytest.raises(l.StudyLedgerError, match="untracked_purchase"):
        reconcile(frozen(), path)


@pytest.mark.parametrize("column,value", [("id", "another-run"), ("engine_fingerprint", "f" * 64)])
def test_actual_run_and_engine_identity(tmp_path: Path, column: str, value: str) -> None:
    path = tmp_path / "journal.db"
    create(path)
    sql(path, f"UPDATE run SET {column}=?", (value,))
    with pytest.raises(l.StudyLedgerError, match="journal_identity_mismatch"):
        read(path)


def test_actual_private_world_canonical_identity_including_signed_zero(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path)
    data = catalog().worlds[0].definition.model_dump(mode="json")
    data["space"]["structure"]["anchors"][0]["position"][0] = -0.0
    sql(path, "UPDATE run SET world_json=?", (json.dumps(data),))
    with pytest.raises(l.StudyLedgerError, match="journal_world_mismatch"):
        read(path)


@pytest.mark.parametrize(
    "mutation",
    ["gap", "request_sign", "operation", "record_index", "trajectory_grid", "bad_after_pending"],
)
def test_actual_rows_and_all_completed_grids_bound(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "journal.db"
    create(path, ("completed", "pending", "completed"))
    if mutation == "gap":
        sql(path, "UPDATE experiments SET ordinal=4 WHERE ordinal=2")
    elif mutation == "operation":
        sql(path, "UPDATE experiments SET operation_id='other' WHERE ordinal=0")
    elif mutation == "request_sign":
        data = experiment().model_dump(mode="json")
        data["particles"][0]["position"][0] = -0.0
        sql(path, "UPDATE experiments SET request_json=? WHERE ordinal=0", (json.dumps(data),))
    else:
        index = 2 if mutation == "bad_after_pending" else 0
        with sqlite3.connect(path) as db:
            raw = db.execute(
                "SELECT record_json FROM experiments WHERE ordinal=?", (index,)
            ).fetchone()[0]
        data = json.loads(raw)
        if mutation == "record_index":
            data["index"] = 5
        else:
            data["trajectory"]["frames"] = data["trajectory"]["frames"][:2]
        sql(path, "UPDATE experiments SET record_json=? WHERE ordinal=?", (json.dumps(data), index))
    with pytest.raises((l.StudyLedgerError, ValidationError)):
        read(path)


@pytest.mark.parametrize("mutation", ["duplicate", "nonfinite", "depth", "oversize"])
def test_raw_request_predecode_limits(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "journal.db"
    create(path, ("pending",))
    raw = {
        "duplicate": '{"particles":[],"particles":[]}',
        "nonfinite": '{"particles":NaN}',
        "depth": "[" * 33 + "]" * 33,
        "oversize": " " * (j.MAX_RECORD_BYTES + 1),
    }[mutation]
    sql(path, "UPDATE experiments SET request_json=?", (raw,))
    with pytest.raises((l.StudyLedgerError, ContractViolation)):
        read(path)


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_no_live_or_recovery_journal(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / "journal.db"
    create(path)
    Path(str(path) + suffix).write_bytes(b"")
    with pytest.raises(l.StudyLedgerError, match="journal_nonquiescent"):
        read(path)


def test_no_symlink_or_public_journal(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(WorkflowError):
        read(link)
    path.chmod(0o644)
    with pytest.raises(WorkflowError):
        read(path)


def test_catalog_current_manifest_and_cell_scope_before_read(tmp_path: Path) -> None:
    manifest = materials()[0]
    with pytest.raises(l.StudyLedgerError, match="unknown_cell"):
        j.read_study_journal(
            tmp_path / "missing", manifest=manifest, catalog=catalog(), cell_id="unknown"
        )
    data = catalog().model_dump(mode="json")
    data["worlds"].reverse()
    alternate = c.NativeWorldCatalog.model_validate_json(json.dumps(data))
    with pytest.raises(l.StudyLedgerError, match="world_catalog_mismatch"):
        j.read_study_journal(
            tmp_path / "missing",
            manifest=manifest,
            catalog=alternate,
            cell_id=manifest.cells[0].cell_id,
        )


def test_actual_purchase_mismatch_rejected_before_prefix_exposure(tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    create(path, ("pending",))
    sql(path, "UPDATE experiments SET operation_id='different-operation'")
    with pytest.raises(l.StudyLedgerError, match="purchase_journal_mismatch"):
        reconcile(intent(frozen(), 0), path)
