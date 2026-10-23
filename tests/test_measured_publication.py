"""Synthetic measured publication tests. These do not execute a scientific study."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from test_study_early import purchases
from test_study_scoring import Material, raw
from test_study_scoring import material as material
from test_study_scoring import path as path

from strange_physics import measured_publication as publisher
from strange_physics import publication_store as storage
from strange_physics.bounded_json import parse_bounded_json
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
from strange_physics.workflow_io import read_bytes


def prepare(
    material: Material, path: Path, root: Path, *, control_ns: int = 5_000_000_000
) -> NativePublicationRequest:
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
        ticket_cpu_ns=control_ns,
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
        cpu_reservation_ns=4 * control_ns + 1_000_000_000,
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
    assert len(h.records) == request.expected_revision + 2
    failure = h.records[-1].event
    assert isinstance(failure, StudyAttemptUpdate) and failure.state == "unknown"
    assert failure.cpu_ns is not None and failure.cpu_ns > 0
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
        code = """
import sqlite3,sys
from pathlib import Path
from strange_physics.journal import Journal
j=Journal(Path(sys.argv[1]))
j._db.execute("PRAGMA busy_timeout=0")
try:
    j.record_failure("contender","synthetic",[])
    print("unexpected")
except sqlite3.OperationalError:
    print("blocked")
finally:
    j.close()
"""
        completed = subprocess.run(
            [sys.executable, "-c", code, str(path)], capture_output=True, timeout=10, check=True
        )
        observed.append(completed.stdout.strip())
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


def test_missing_previously_created_store_never_reseeds(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    publisher.commit_native_publication(root, request)
    (root / "publication.sqlite3").unlink()
    with pytest.raises(StudyLedgerError, match="store_missing_after_creation"):
        publisher.commit_native_publication(root, change(request, ticket=1, attempt_id="retry"))
    assert not (root / "publication.sqlite3").exists()


def test_current_store_requires_original_seed_prefix(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    with pytest.raises(StudyLedgerError, match="stale"):
        publisher.commit_native_publication(root, change(request, expected_revision=0))
    seed = read_study_ledger((root / "seed-ledger.json").read_bytes())
    shorter = type(seed)(plan=seed.plan, records=seed.records[:-1])
    with sqlite3.connect(root / "publication.sqlite3") as db:
        db.execute(
            "UPDATE state SET ledger=?,revision=?,head=?",
            (raw(shorter), len(shorter.records), storage.head(shorter)),
        )
        db.execute("DELETE FROM records WHERE sequence>=?", (len(shorter.records),))
    with pytest.raises(StudyLedgerError, match="store_seed_prefix"):
        publisher.commit_native_publication(
            root,
            change(
                request,
                ticket=1,
                attempt_id="retry",
                expected_revision=len(shorter.records),
                expected_head_sha256=storage.head(shorter),
            ),
        )


def test_control_tail_cannot_borrow_settled_work_budget(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root, control_ns=1_000_000_000)
    original = storage.Store.close

    def expensive_close(store: storage.Store) -> None:
        original(store)
        started = time.process_time_ns()
        while time.process_time_ns() - started < 2_000_000_000:
            pass

    monkeypatch.setattr(storage.Store, "close", expensive_close)
    with pytest.raises(StudyLedgerError, match="publication_deadline"):
        publisher.commit_native_publication(root, request)
    # Work may be settled, but the interrupted control tail remains held.
    h = read_study_ledger(current(root))
    assert summarize_study(h).budget.unresolved_attempts == 1
    monkeypatch.setattr(storage.Store, "close", original)
    replay = publisher.commit_native_publication(
        root, change(request, ticket=1, attempt_id="retry")
    )
    assert replay.replayed


def test_child_respects_inherited_hard_file_limit(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    request_path = root / "request.json"
    request_path.write_bytes(raw(request))
    request_path.chmod(0o600)
    code = """
import os,resource,sys
from pathlib import Path
from strange_physics.measured_publication import commit_native_publication
from strange_physics.measured_publication_contracts import NativePublicationRequest
request=NativePublicationRequest.model_validate_json(Path(sys.argv[2]).read_bytes())
resource.setrlimit(resource.RLIMIT_FSIZE,(2*1024**2,2*1024**2))
pid=os.getpid()
result=commit_native_publication(Path(sys.argv[1]),request)
assert os.getpid()==pid
print(result.receipt.event_id)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, str(root), str(request_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert completed.stdout.strip() == request.event_id


def test_failed_reaped_child_retains_known_measurements_and_hold(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)

    def rejected(*args: Any, **kwargs: Any) -> Any:
        started = time.process_time_ns()
        while time.process_time_ns() - started < 20_000_000:
            pass
        raise ValueError("synthetic child failure")

    monkeypatch.setattr(publisher, "_compose", rejected)
    with pytest.raises(StudyLedgerError, match="publication_child_failed"):
        publisher.commit_native_publication(root, request)
    h = read_study_ledger(current(root))
    final = h.records[-1].event
    assert isinstance(final, StudyAttemptUpdate) and final.state == "unknown"
    assert final.cpu_ns is not None and final.cpu_ns >= 20_000_000
    assert final.wall_ns is not None and final.wall_ns > 0
    assert summarize_study(h).budget.unresolved_attempts == 2
    assert summarize_study(h).budget.charged_cpu_ns >= request.cpu_reservation_ns
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0


def test_sleeping_child_wall_time_is_not_cpu(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original = publisher._compose

    def delayed(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        # This delay is the measured phenomenon, not test synchronization.
        time.sleep(0.05)
        return result

    monkeypatch.setattr(publisher, "_compose", delayed)
    result = publisher.commit_native_publication(root, request)
    measured = result.measurements
    assert measured.wall_ns > measured.parent_cpu_ns + measured.child_cpu_ns
    assert measured.child_cpu_ns > 0


def test_encoded_request_bound_precedes_ticket_consumption(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    from strange_physics.control_contracts import ContractViolation

    root = tmp_path / "store"
    request = prepare(material, path, root)
    files = tuple(
        PublicationFile.model_validate(f.model_dump() | {"path": "\U0001f600" * 4000})
        for f in request.files
    )
    oversized = change(request, files=files)
    assert len(raw(oversized)) > publisher.REQUEST_BYTES
    with pytest.raises(ContractViolation):
        publisher.commit_native_publication(root, oversized)
    assert not (root / "ticket-0").exists()


def test_failed_reservation_cannot_borrow_unretained_work_cpu(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root, control_ns=1_000_000_000)
    original = storage.Store.replace

    def expensive_reservation(
        store: storage.Store,
        before: Any,
        after: Any,
    ) -> None:
        started = time.process_time_ns()
        while time.process_time_ns() - started < 2_000_000_000:
            pass
        original(store, before, after)

    monkeypatch.setattr(storage.Store, "replace", expensive_reservation)
    with pytest.raises(StudyLedgerError, match="publication_deadline"):
        publisher.commit_native_publication(root, request)
    h = read_study_ledger(current(root))
    assert len(h.records) == request.expected_revision
    assert summarize_study(h).budget.unresolved_attempts == 1


@pytest.mark.parametrize(
    "phase,published",
    [
        ("before_reserve", False),
        ("after_reserve", False),
        ("inside_publication", False),
        ("after_publication", True),
        ("inside_settlement", True),
        ("after_settlement", True),
    ],
)
def test_real_process_crash_preserves_atomic_state_and_charges(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    published: bool,
) -> None:
    from collections.abc import Iterator
    from contextlib import contextmanager

    root = tmp_path / "store"
    request = prepare(material, path, root)
    original_replace, original_transaction = storage.Store.replace, storage.Store.transaction
    replaces = transactions = 0

    def interrupted_replace(store: storage.Store, before: Any, after: Any) -> None:
        nonlocal replaces
        replaces += 1
        if phase == "before_reserve" and replaces == 1:
            os._exit(91)
        original_replace(store, before, after)
        if (phase, replaces) in {("inside_publication", 2), ("inside_settlement", 3)}:
            os._exit(91)

    @contextmanager
    def interrupted_transaction(store: storage.Store) -> Iterator[None]:
        nonlocal transactions
        transactions += 1
        number = transactions
        with original_transaction(store):
            yield
        if (phase, number) in {
            ("after_reserve", 1),
            ("after_publication", 2),
            ("after_settlement", 3),
        }:
            os._exit(91)

    with monkeypatch.context() as patch:
        patch.setattr(storage.Store, "replace", interrupted_replace)
        patch.setattr(storage.Store, "transaction", interrupted_transaction)
        pid = os.fork()
        if pid == 0:
            try:
                publisher.commit_native_publication(root, request)
            except BaseException:
                os._exit(92)
            os._exit(93)
        _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 91
    retry = change(request, ticket=1, attempt_id="recovery")
    if published:
        result = publisher.commit_native_publication(root, retry)
        assert result.replayed
        assert parse_study_early_evidence(result.evidence_raw).stage == "candidate_unavailable"
    else:
        # First recovery opens the actual crash state before an external read.
        if phase == "before_reserve":
            result = publisher.commit_native_publication(root, retry)
        else:
            with pytest.raises(StudyLedgerError, match="stale_publication_head"):
                publisher.commit_native_publication(root, retry)
            ledger = read_study_ledger(current(root))
            result = publisher.commit_native_publication(
                root,
                change(
                    retry,
                    ticket=2,
                    attempt_id="retry-after-read",
                    expected_revision=len(ledger.records),
                    expected_head_sha256=storage.head(ledger),
                ),
            )
        assert not result.replayed
    # The old charged work envelope never disappears after a committed reserve.
    attempts = [
        r.event.attempt_id
        for r in result.ledger.records
        if isinstance(r.event, StudyAttemptReservation)
    ]
    assert (request.attempt_id in attempts) == (phase != "before_reserve")
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 1


def test_sqlite_full_rolls_back_publication_but_keeps_reservation(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original = storage.Store.limit_growth
    calls = 0

    def no_work_growth(store: storage.Store, amount: int) -> None:
        nonlocal calls
        calls += 1
        if calls <= 2:
            original(store, amount)
        else:
            pages = store.db.execute("PRAGMA page_count").fetchone()[0]
            store.db.execute(f"PRAGMA max_page_count={pages}")

    monkeypatch.setattr(storage.Store, "limit_growth", no_work_growth)
    with pytest.raises(sqlite3.OperationalError, match="full"):
        publisher.commit_native_publication(root, request)
    h = read_study_ledger(current(root))
    assert summarize_study(h).budget.unresolved_attempts == 2
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0


@pytest.mark.parametrize("failure", [1, 2, 3, 4])
def test_fsync_failure_never_reuses_control_ticket(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: int,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original = os.fsync
    count = 0

    def failed_sync(fd: int) -> None:
        nonlocal count
        count += 1
        if count == failure:
            raise OSError("synthetic fsync failure")
        original(fd)

    monkeypatch.setattr(os, "fsync", failed_sync)
    with pytest.raises(OSError, match="synthetic fsync"):
        publisher.commit_native_publication(root, request)
    monkeypatch.setattr(os, "fsync", original)
    with pytest.raises(StudyLedgerError, match="ticket_consumed"):
        publisher.commit_native_publication(root, request)
    assert (root / "ticket-0").is_file()


@pytest.mark.parametrize("fault", ["wait", "read", "parse", "result", "transaction"])
def test_known_child_cost_survives_parent_failure_and_retry(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original_compose = publisher._compose
    original_wait = os.wait4
    original_read = read_bytes
    original_parse = parse_bounded_json
    original_replace = storage.Store.replace
    waited_cpu = 0
    calls = 0

    def measured_compose(*args: Any, **kwargs: Any) -> Any:
        start = time.process_time_ns()
        while time.process_time_ns() - start < 20_000_000:
            pass
        result = original_compose(*args, **kwargs)
        if fault == "result":
            return result.model_copy(update={"replayed": True})
        return result

    def interrupted_wait(pid: int, flags: int) -> Any:
        nonlocal calls, waited_cpu
        calls += 1
        if fault == "wait" and calls == 1:
            # A real child has done CPU work before the parent's wait is interrupted.
            deadline = time.monotonic() + 10
            while not (root / "work-0" / "output.json").exists():
                if time.monotonic() > deadline:
                    raise AssertionError("child output unavailable")
                time.sleep(0.001)
            raise OSError("synthetic interrupted wait")
        value = original_wait(pid, flags)
        waited_cpu = int((value[2].ru_utime + value[2].ru_stime) * 1_000_000_000)
        return value

    def failed_read(p: Path, **kwargs: Any) -> bytes:
        if fault == "read" and p.name == "output.json":
            raise OSError("synthetic output read failure")
        return original_read(p, **kwargs)

    def failed_parse(data: bytes, model: Any, **kwargs: Any) -> Any:
        if fault == "parse" and model is publisher._Output:
            raise ValueError("synthetic strict output parse failure")
        return original_parse(data, model, **kwargs)

    def failed_replace(store: storage.Store, before: Any, after: Any) -> None:
        original_replace(store, before, after)
        if fault == "transaction" and after.records[-1].event_id == request.event_id:
            raise sqlite3.OperationalError("synthetic publication rollback")

    with monkeypatch.context() as patch:
        patch.setattr(publisher, "_compose", measured_compose)
        patch.setattr(os, "wait4", interrupted_wait)
        patch.setattr(publisher, "read_bytes", failed_read)
        patch.setattr(publisher, "parse_bounded_json", failed_parse)
        patch.setattr(storage.Store, "replace", failed_replace)
        with pytest.raises((StudyLedgerError, sqlite3.OperationalError)):
            publisher.commit_native_publication(root, request)
    assert waited_cpu >= 20_000_000
    ledger = read_study_ledger(current(root))
    update = ledger.records[-1].event
    assert isinstance(update, StudyAttemptUpdate) and update.state == "unknown"
    assert update.cpu_ns is not None and update.cpu_ns >= waited_cpu
    assert update.wall_ns is not None and update.wall_ns > 0
    assert update.artifact_bytes is not None and update.artifact_bytes > 0
    assert request.event_id not in {r.event_id for r in ledger.records}
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0
    result = publisher.commit_native_publication(
        root,
        change(
            request,
            ticket=1,
            attempt_id="retry",
            expected_revision=len(ledger.records),
            expected_head_sha256=storage.head(ledger),
        ),
    )
    assert not result.replayed
    assert result.ledger.records[: len(ledger.records)] == ledger.records
    assert summarize_study(result.ledger).budget.unresolved_attempts == 2


def test_wall_deadline_cannot_restart_for_cleanup(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = change(prepare(material, path, root), wall_limit_ns=1_000_000_000)

    def blocked(*args: Any, **kwargs: Any) -> Any:
        # The wall deadline is the phenomenon under test, not synchronization.
        time.sleep(10)
        raise AssertionError("deadline did not stop child")

    monkeypatch.setattr(publisher, "_compose", blocked)
    began = time.monotonic()
    with pytest.raises(StudyLedgerError):
        publisher.commit_native_publication(root, request)
    assert time.monotonic() - began < 3
    ledger = read_study_ledger(current(root))
    assert summarize_study(ledger).budget.unresolved_attempts == 2
    assert not any(r.event_id == request.event_id for r in ledger.records)


def test_store_page_size_is_an_explicit_byte_limit_precondition(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    result = publisher.commit_native_publication(root, request)
    before = current(root)
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("PRAGMA page_size").fetchone()[0] == 4096
        db.execute("PRAGMA page_size=65536")
        db.execute("VACUUM")
        assert db.execute("PRAGMA page_size").fetchone()[0] == 65536
    with pytest.raises(StudyLedgerError, match="store_page_size"):
        publisher.commit_native_publication(root, change(request, ticket=1, attempt_id="retry"))
    assert current(root) == before == raw(result.ledger)


@pytest.mark.parametrize("late", [False, True])
def test_child_wall_limit_survives_parent_death(
    material: Material,
    path: Path,
    tmp_path: Path,
    late: bool,
) -> None:
    root = tmp_path / "store"
    request = change(prepare(material, path, root), wall_limit_ns=1_000_000_000)
    request_path = root / "request.json"
    request_path.write_bytes(raw(request))
    request_path.chmod(0o600)
    code = """
import ctypes,os,signal,sys,time
from pathlib import Path
from strange_physics import measured_publication as publisher
from strange_physics.measured_publication_contracts import NativePublicationRequest
from strange_physics.publication_store import root_lock
# This isolated test supervisor adopts the orphan for deterministic reap.
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
root=Path(sys.argv[1])
request=NativePublicationRequest.model_validate_json(Path(sys.argv[2]).read_bytes())
marker=root/'test-child-pid'
composed=root/'test-composed'
late=sys.argv[3]=='late'
real_fork=os.fork
def paused_fork():
    child=real_fork()
    if child==0:
        marker.write_text(str(os.getpid()))
        if late:
            os.kill(os.getpid(),signal.SIGSTOP)
    return child
publisher.os.fork=paused_fork
def blocked(*args,**kwargs):
    composed.write_text('started')
    time.sleep(10)
    raise AssertionError('child escaped wall deadline')
publisher._compose=blocked
started=time.monotonic()
parent=real_fork()
if parent==0:
    try:
        publisher.commit_native_publication(root,request)
    finally:
        os._exit(90)
deadline=time.monotonic()+5
while not marker.exists() or (not late and not composed.exists()):
    assert time.monotonic()<deadline
    time.sleep(.001)
child=int(marker.read_text())
os.kill(parent,signal.SIGKILL)
assert os.waitpid(parent,0)[0]==parent
began=time.monotonic()
if late:
    # Delay scheduling past the original absolute deadline, then resume orphan.
    time.sleep(max(0,started+1.3-time.monotonic()))
    os.kill(child,signal.SIGCONT)
pid,status=os.waitpid(child,0)
assert pid==child
if late:
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status)==70
    assert not composed.exists()
else:
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGALRM
assert time.monotonic()-began<3
with root_lock(root):
    pass
print('orphan reaped and inherited lock released')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(root), str(request_path), "late" if late else "on-time"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert result.stdout.strip() == "orphan reaped and inherited lock released"
    ledger = read_study_ledger(current(root))
    assert summarize_study(ledger).budget.unresolved_attempts == 2


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "public", "fifo"])
def test_private_material_boundary_never_publishes(
    material: Material,
    path: Path,
    tmp_path: Path,
    kind: str,
) -> None:
    from strange_physics.workflow_io import WorkflowError

    root = tmp_path / "store"
    request = prepare(material, path, root)
    target = Path(request.files[0].path)
    if kind in {"symlink", "hardlink"}:
        saved = target.with_suffix(".saved")
        target.rename(saved)
        if kind == "symlink":
            target.symlink_to(saved)
        else:
            os.link(saved, target)
    elif kind == "public":
        target.chmod(0o644)
    else:
        target.unlink()
        os.mkfifo(target, 0o600)
    with pytest.raises((WorkflowError, StudyLedgerError), match="unsafe"):
        publisher.commit_native_publication(root, request)
    ledger = read_study_ledger(current(root))
    assert request.event_id not in {r.event_id for r in ledger.records}
    assert summarize_study(ledger).budget.unresolved_attempts == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("ticket", True),
        ("cpu_reservation_ns", False),
        ("wall_limit_ns", float("inf")),
        ("output_limit_bytes", 48 * MIB + 1),
        ("artifact_reservation_bytes", 512 * MIB + 1),
        ("expected_revision", -1),
        ("extra_runner", "anything"),
    ],
)
def test_publication_request_strict_bounds(
    material: Material,
    path: Path,
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    from pydantic import ValidationError

    request = prepare(material, path, tmp_path / "store")
    with pytest.raises(ValidationError):
        change(request, **{field: value})


@pytest.mark.parametrize("column", ["original", "journal", "evidence", "receipt", "request"])
def test_corrupted_retained_snapshot_cannot_publish_fresh(
    material: Material,
    path: Path,
    tmp_path: Path,
    column: str,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    publisher.commit_native_publication(root, request)
    with sqlite3.connect(root / "publication.sqlite3") as db:
        # Column comes only from the closed test parameter set.
        db.execute(f"UPDATE closures SET {column}=?", (b"corrupted snapshot",))
    with pytest.raises(ValueError):
        publisher.commit_native_publication(root, change(request, ticket=1, attempt_id="retry"))
    with sqlite3.connect(root / "publication.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 1


def test_independent_root_contender_consumes_only_its_ticket(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    code = r"""
import sys
from pathlib import Path
from strange_physics.publication_store import root_lock
with root_lock(Path(sys.argv[1])):
    print('locked',flush=True)
    assert sys.stdin.readline()=='release\n'
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", code, str(root)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdout is not None and proc.stdout.readline().strip() == "locked"
        with pytest.raises(StudyLedgerError, match="publication_busy"):
            publisher.commit_native_publication(root, request)
        assert not (root / "store-created").exists()
        assert proc.communicate("release\n", timeout=10)[1] == ""
        assert proc.returncode == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    result = publisher.commit_native_publication(
        root, change(request, ticket=1, attempt_id="retry")
    )
    assert not result.replayed
    assert summarize_study(result.ledger).budget.unresolved_attempts == 1


def test_sqlite_phase_envelopes_include_control_settlement(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from collections.abc import Iterator
    from contextlib import contextmanager

    root = tmp_path / "store"
    request = prepare(material, path, root)
    original_limit = storage.Store.limit_growth
    original_transaction = storage.Store.transaction
    observations: list[tuple[int, int]] = []
    allowance = baseline = 0

    def limited(store: storage.Store, amount: int) -> None:
        nonlocal allowance, baseline
        original_limit(store, amount)
        allowance = amount
        baseline = sum(size for _, size in store.meter.high.values())
        assert store.db.execute("PRAGMA cache_spill").fetchone()[0] == 0

    @contextmanager
    def measured(store: storage.Store) -> Iterator[None]:
        with original_transaction(store):
            yield
        growth = sum(size for _, size in store.meter.high.values()) - baseline
        observations.append((allowance, growth))
        assert 0 <= growth <= allowance

    monkeypatch.setattr(storage.Store, "limit_growth", limited)
    monkeypatch.setattr(storage.Store, "transaction", measured)
    first = publisher.commit_native_publication(root, request)
    replay = publisher.commit_native_publication(
        root, change(request, ticket=1, attempt_id="retry")
    )
    assert replay.replayed and raw(first.receipt) == raw(replay.receipt)
    assert len(observations) == 5  # reserve, publish, settle; replay reserve, settle
    assert all(amount <= 64 * MIB for amount, _ in observations)


def test_sqlite_journal_headroom_denies_before_mutation(
    material: Material,
    path: Path,
    tmp_path: Path,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    result = publisher.commit_native_publication(root, request)
    admission = PublicationAdmission.model_validate_json((root / "admission.json").read_bytes())
    seed = (root / "seed-ledger.json").read_bytes()
    meter = storage.Extents(root)
    with storage.root_lock(root):
        store = storage.Store(root, admission, seed, meter)
        before = current(root)
        try:
            # Even zero DB growth may journal existing pages; it is not free.
            with pytest.raises(StudyLedgerError, match="publication_sqlite_headroom"):
                store.limit_growth(0)
        finally:
            store.close()
    assert current(root) == before == raw(result.ledger)


def test_failed_settlement_deducts_control_growth_without_changing_work_cost(
    material: Material,
    path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "store"
    request = prepare(material, path, root)
    original_limit, original_replace = storage.Store.limit_growth, storage.Store.replace
    limits: list[int] = []
    completed_work_bytes: int | None = None
    injected = 8192

    def limited(store: storage.Store, amount: int) -> None:
        limits.append(amount)
        original_limit(store, amount)

    def interrupted(store: storage.Store, before: Any, after: Any) -> None:
        nonlocal completed_work_bytes
        original_replace(store, before, after)
        event = after.records[-1].event
        if isinstance(event, StudyAttemptUpdate) and event.state == "completed":
            completed_work_bytes = event.artifact_bytes
            # Explicit fault injection of real private control extents; this is
            # not a claim that ordinary settlement SQL naturally grew a file.
            store.meter.write(root / "injected-control-extent", b"x" * injected)
            raise OSError("synthetic settlement write failure")

    with monkeypatch.context() as patch:
        patch.setattr(storage.Store, "limit_growth", limited)
        patch.setattr(storage.Store, "replace", interrupted)
        with pytest.raises(OSError, match="synthetic settlement write failure"):
            publisher.commit_native_publication(root, request)
    assert len(limits) == 5  # initialization, reservation, work, settlement, fallback
    assert limits[-1] <= limits[-2] - injected
    ledger = read_study_ledger(current(root))
    failed = ledger.records[-1].event
    assert isinstance(failed, StudyAttemptUpdate) and failed.state == "unknown"
    assert completed_work_bytes is not None and failed.artifact_bytes == completed_work_bytes
    assert summarize_study(ledger).budget.unresolved_attempts == 2
    replay = publisher.commit_native_publication(
        root,
        change(request, ticket=1, attempt_id="recovery"),
    )
    assert replay.replayed
    assert replay.ledger.records[: len(ledger.records)] == ledger.records
