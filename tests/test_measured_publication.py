"""Synthetic measured publication tests. These do not execute a scientific study."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from test_study_early import purchases
from test_study_scoring import Material, raw
from test_study_scoring import material as material
from test_study_scoring import path as path

from strange_physics import measured_publication as publisher
from strange_physics import publication_store as storage
from strange_physics.measured_publication_contracts import (
    MIB,
    NativePublicationRequest,
    PublicationAdmission,
    PublicationControl,
    PublicationFile,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import StudyAttemptReservation, StudyAttemptUpdate
from strange_physics.study_early_contracts import StudyEarlyWitnesses, parse_study_early_evidence
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    read_study_ledger,
    study_manifest,
    summarize_study,
)


def prepare(material: Material, path: Path, root: Path) -> NativePublicationRequest:
    root.mkdir(mode=0o700)
    ledger = purchases(material)
    manifest = study_manifest(ledger)
    control = PublicationControl(
        root=str(root),
        accounting_plan_sha256=message_sha256(ledger.plan),
        source_commit=manifest.source_commit,
        uv_lock_sha256=manifest.uv_lock_sha256,
        attempt_id="publication-control",
        tickets=4,
        ticket_cpu_ns=5_000_000_000,
        ticket_wall_ns=30_000_000_000,
        ticket_artifact_bytes=16 * MIB,
    )
    hold = StudyAttemptReservation(
        attempt_id=control.attempt_id,
        phase="accounting",
        operation="accounting",
        cell_id=None,
        config_sha256=message_sha256(control),
        input_sha256=message_sha256(ledger.plan),
        retry_of=None,
        cpu_reservation_ns=21_000_000_000,
        artifact_reservation_bytes=80 * MIB,
        purchase=None,
    )
    ledger = append_study_attempt(
        ledger, event_id="control-reserve", event=hold, expected_revision=len(ledger.records)
    )
    admission = PublicationAdmission(
        control=control, seed_ledger_sha256=storage.digest(raw(ledger))
    )
    for name, data in (("admission.json", raw(admission)), ("seed-ledger.json", raw(ledger))):
        (root / name).write_bytes(data)
        (root / name).chmod(0o600)
    files = []
    payloads = material.artifacts | {"witnesses": raw(StudyEarlyWitnesses(stages=()))}
    for name, data in payloads.items():
        p = root / (name + ".json")
        p.write_bytes(data)
        p.chmod(0o600)
        files.append(
            PublicationFile(
                name=name, path=str(p), sha256=storage.digest(data), byte_count=len(data)
            )
        )
    return NativePublicationRequest(
        mode="early",
        event_id="publish",
        cell_id=material.cell,
        attempt_id="publish-1",
        ticket=0,
        expected_revision=len(ledger.records),
        expected_head_sha256=storage.head(ledger),
        journal_path=str(path),
        journal_sha256=storage.digest(path.read_bytes()),
        files=tuple(files),
        cpu_reservation_ns=8_000_000_000,
        artifact_reservation_bytes=64 * MIB,
        output_limit_bytes=4 * MIB,
        wall_limit_ns=30_000_000_000,
    )


def change(request: NativePublicationRequest, **values: Any) -> NativePublicationRequest:
    return NativePublicationRequest.model_validate(request.model_dump() | values)


def current(root: Path) -> bytes:
    with sqlite3.connect(root / "publication.sqlite3") as db:
        value = db.execute("SELECT ledger FROM state WHERE id=1").fetchone()[0]
        assert isinstance(value, bytes)
        return value


def test_actual_child_original_prefix_and_recovery(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    before = path.read_bytes()
    result = publisher.commit_native_publication(root, request)
    assert path.read_bytes() == before
    assert not Path(str(path) + "-journal").exists()
    assert result.measurements.child_cpu_ns > 0
    assert result.measurements.parent_cpu_ns > 0
    assert result.measurements.wall_ns > 0
    assert result.measurements.created_artifact_bytes > 0
    assert result.receipt.original_revision == request.expected_revision + 1
    evidence = parse_study_early_evidence(result.evidence_raw)
    assert evidence.stage == "candidate_unavailable"
    assert evidence.outcome.status == "incomplete"
    assert evidence.ledger_revision == request.expected_revision + 1
    assert summarize_study(result.ledger).budget.unresolved_attempts == 1
    update = result.ledger.records[-1].event
    assert isinstance(update, StudyAttemptUpdate) and update.state == "completed"
    # Live Journal evolution cannot rewrite the original evidence or receipt.
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO failures VALUES ('later','synthetic','[]')")
    replay = publisher.commit_native_publication(
        root, change(request, ticket=1, attempt_id="replay-1")
    )
    assert replay.replayed
    assert raw(replay.receipt) == raw(result.receipt)
    assert replay.evidence_raw == result.evidence_raw
    assert len(replay.ledger.records) == len(result.ledger.records) + 2
    assert not (root / "work-0").exists() and not (root / "work-1").exists()
    assert all(p.stat().st_mode & 0o077 == 0 for p in root.iterdir())


def test_ticket_never_reexecutes(material: Material, path: Path, tmp_path: Path) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    publisher.commit_native_publication(root, request)
    before = current(root)
    with pytest.raises(StudyLedgerError, match="ticket_consumed"):
        publisher.commit_native_publication(root, request)
    assert current(root) == before


def test_stale_head_consumes_control_ticket_only(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    with pytest.raises(StudyLedgerError, match="stale_publication_head"):
        publisher.commit_native_publication(root, change(request, expected_revision=0))
    assert len(read_study_ledger(current(root)).records) == request.expected_revision
    assert (root / "ticket-0").is_file()


def test_missing_material_retains_durable_work_hold(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    Path(request.files[0].path).unlink()
    with pytest.raises(FileNotFoundError):
        publisher.commit_native_publication(root, request)
    h = read_study_ledger(current(root))
    assert len(h.records) == request.expected_revision + 1
    assert summarize_study(h).budget.unresolved_attempts == 2


def test_closure_corruption_is_not_fresh_absence(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    publisher.commit_native_publication(root, request)
    with sqlite3.connect(root / "publication.sqlite3") as db:
        db.execute("DELETE FROM closures")
    with pytest.raises(StudyLedgerError, match="closure_corrupt"):
        publisher.commit_native_publication(root, change(request, ticket=1, attempt_id="retry"))


def test_changed_declared_material_cannot_replay(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    publisher.commit_native_publication(root, request)
    f = request.files[0]
    bad = PublicationFile.model_validate(f.model_dump() | {"sha256": "f" * 64})
    with pytest.raises(StudyLedgerError, match="publication_conflict"):
        publisher.commit_native_publication(
            root, change(request, ticket=1, attempt_id="retry", files=(bad, *request.files[1:]))
        )


def test_cumulative_deleted_extents_and_persist_bytes(tmp_path: Path) -> None:
    meter = storage.Extents(tmp_path)
    p = tmp_path / "a"
    meter.write(p, b"x" * 19)
    p.unlink()
    meter.write(p, b"x" * 31)
    assert meter.total == 50
    db = tmp_path / "publication.sqlite3"
    meter.write(db, b"x" * 4096)
    # Controlled scratch writes and tracked SQLite extents are disjoint sets.
    # A pre-existing SQLite extent initializes at its existing high-water.
    second = storage.Extents(tmp_path)
    with db.open("ab") as output:
        output.write(b"x" * 4096)
    second.sample()
    assert second.total == 4096
    second.sample()
    assert second.total == 4096


def test_real_journal_writer_is_excluded(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original = publisher._run_child
    observed: list[bytes] = []

    def checked(*args: Any, **kwargs: Any) -> Any:
        read, write = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read)
            from strange_physics.journal import Journal

            journal = Journal(path)
            journal._db.execute("PRAGMA busy_timeout=0")
            try:
                journal.record_failure("contender", "synthetic", [])
                os.write(write, b"unexpected")
            except sqlite3.OperationalError:
                os.write(write, b"blocked")
            finally:
                journal.close()
            os._exit(0)
        os.close(write)
        observed.append(os.read(read, 32))
        os.close(read)
        os.waitpid(pid, 0)
        return original(*args, **kwargs)

    monkeypatch.setattr(publisher, "_run_child", checked)
    publisher.commit_native_publication(root, request)
    assert observed == [b"blocked"]
    from strange_physics.journal import Journal

    journal = Journal(path)
    try:
        journal.record_failure("after", "synthetic", [])
    finally:
        journal.close()
