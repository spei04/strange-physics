"""Bounded synthetic freeze/Journal fixtures; no study or purchase producer claim."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from freeze_journal_fixture import (
    COPY_LIMIT,
    EPOCH_LIMIT,
    JournalConnection,
    SetupBudget,
    comparison_request,
    generate_journal,
    inject_intents,
    prepare,
    restrict_limit,
)
from test_measured_candidates import actual_build, current, last_update

from strange_physics import measured_candidates as supervisor
from strange_physics.candidate_execution_contracts import MIB
from strange_physics.candidate_store import CandidateStore
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_study import commit_journal_candidates, commit_native_freeze
from strange_physics.publication_store import raw
from strange_physics.study_execution_binding import (
    bind_captured_candidate,
    validate_frozen_materials,
)
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeFreezeInput,
    NativeFreezeRequest,
)
from strange_physics.study_ledger import StudyLedgerError, study_manifest, summarize_study

__all__ = ["actual_build"]


def recover(request: NativeFreezeRequest | NativeComparisonCandidateRequest, ticket: int) -> Any:
    data = request.model_dump()
    data.update(
        mode="recover",
        attempt_id=f"recovery-{ticket}",
        ticket=ticket,
        cpu_reservation_ns=8_000_000_000,
        artifact_reservation_bytes=2 * MIB,
    )
    return type(request).model_validate(data)


def test_fixture_guards_precede_schema_and_extra_epoch(tmp_path: Path) -> None:
    db = sqlite3.connect(tmp_path / "guard.sqlite", isolation_level=None, factory=JournalConnection)
    try:
        with pytest.raises(RuntimeError, match="schema_before"):
            db.execute("CREATE TABLE denied(x)")
        assert db.execute("SELECT count(*) FROM sqlite_master").fetchone()[0] == 0
        db.configure()
        assert db.epochs == 3
        db.execute("CREATE TABLE allowed(x)")
        db.epochs = EPOCH_LIMIT
        with pytest.raises(RuntimeError, match="epoch_limit"):
            db.execute("BEGIN IMMEDIATE")
        assert not db.in_transaction
        with pytest.raises(RuntimeError, match="sql_scope"):
            db.execute("ATTACH DATABASE ':memory:' AS other")
    finally:
        db.close()


def test_setup_copies_count_deleted_files_and_deny_before_creation(tmp_path: Path) -> None:
    b = SetupBudget(time.monotonic_ns() + 1_000_000_000)
    b.copies = COPY_LIMIT - 1
    b.write(tmp_path / "last", b"x")
    (tmp_path / "last").unlink()
    with pytest.raises(RuntimeError, match="copy_limit"):
        b.write(tmp_path / "over", b"y")
    assert not (tmp_path / "over").exists()
    b.deadline = time.monotonic_ns() - 1
    with pytest.raises(RuntimeError, match="setup_limit"), b.phase():
        pytest.fail("expired phase entered")


def test_freeze_event_and_receipt_are_atomic_with_original_paid_recovery(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f = prepare(tmp_path / "freeze", actual_build)
    assert not (f.root / "candidate.sqlite3").exists()
    value = commit_native_freeze(f.root, f.freeze_request)
    assert len(value.original_ledger.records) == 3
    assert len(value.ledger.records) == 5
    assert study_manifest(value.ledger) == f.freeze.manifest
    assert value.result.facts.operation == "accounting"
    assert value.measurements.parent_cpu_ns > 0 and value.measurements.child_cpu_ns == 0
    (f.root / "freeze-input.json").unlink()

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("freeze producer replayed")

    monkeypatch.setattr(supervisor, "propose_freeze", forbidden)
    replay = commit_native_freeze(f.root, recover(f.freeze_request, 3))
    assert replay.replayed and raw(replay.receipt) == raw(value.receipt)
    assert replay.result_raw == value.result_raw and replay.original_ledger == value.original_ledger
    assert len(replay.ledger.records) == 7


def test_four_call_genuine_prefix_lock_and_original_replay(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f = prepare(tmp_path / "mixed", actual_build)
    frozen = commit_native_freeze(f.root, f.freeze_request)
    inject_intents(f)
    generate_journal(f)
    request = comparison_request(f, raw(frozen.receipt))
    assert f.budget.child_epochs == 35
    original = supervisor._run_child
    checks = []

    def contender() -> None:
        code = """
import sqlite3,sys
from pathlib import Path
from strange_physics.journal import Journal
with_error=False
j=Journal(Path(sys.argv[1]))
try:
 j._db.execute('PRAGMA busy_timeout=0')
 try:j.record_failure('competing-write','Synthetic',[])
 except sqlite3.OperationalError:with_error=True
finally:j.close()
assert with_error
"""
        done = subprocess.run(
            [sys.executable, "-c", code, str(f.journal)], capture_output=True, text=True, timeout=5
        )
        assert done.returncode == 0, done.stderr
        checks.append("blocked")

    def child(*args: Any, **kwargs: Any) -> Any:
        contender()
        return original(*args, **kwargs)

    replace = CandidateStore.replace

    def checked_replace(self: CandidateStore, before: Any, after: Any) -> None:
        if (
            after.records[-1].event.kind == "update"
            and after.records[-1].event.attempt_id == "candidate-1"
        ):
            contender()
        replace(self, before, after)

    monkeypatch.setattr(supervisor, "_run_child", child)
    monkeypatch.setattr(CandidateStore, "replace", checked_replace)
    result = commit_journal_candidates(f.root, request)
    assert checks == ["blocked", "blocked"]
    assert result.result.facts.outcome == "completed"
    assert result.result.facts.observation_sha256 is not None
    assert summarize_study(result.ledger).budget.purchased_slots == 12
    captured = json.loads((f.root / "candidate-input-1").read_bytes())
    records = captured["candidate"]["observations"]["records"]
    assert len(records) == 12 and [r["status"] for r in records] == ["completed"] * 11 + ["failed"]
    assert (
        captured["candidate"]["observations"]["engine_fingerprint"]
        == actual_build.engine_fingerprint
    )
    assert "world" not in captured["candidate"] and "selection" not in captured["candidate"]
    # Later originals can disappear; paid recovery must use immutable captures.
    f.journal.unlink()
    (f.root / "comparison-input.json").unlink()
    (f.root / "freeze-input.json").unlink()

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("producer rerun during recovery")

    monkeypatch.setattr(supervisor, "_run_child", forbidden)
    monkeypatch.setattr(supervisor, "propose_freeze", forbidden)
    freeze_replay = commit_native_freeze(f.root, recover(f.freeze_request, 3))
    replay = commit_journal_candidates(f.root, recover(request, 4))
    assert freeze_replay.result_raw == frozen.result_raw
    assert replay.result_raw == result.result_raw and raw(replay.receipt) == raw(result.receipt)
    assert replay.original_ledger == result.original_ledger
    assert len(replay.ledger.records) == 23
    assert summarize_study(replay.ledger).budget.unresolved_attempts == 14
    assert len(raw(replay.ledger)) <= 256 * 1024
    assert (f.root / "candidate.sqlite3").stat().st_size <= 2 * MIB
    assert (
        f.budget.copies <= COPY_LIMIT
        and f.budget.parent_cpu + f.budget.child_cpu <= 120_000_000_000
    )
    assert (
        not (f.root / "candidate-ticket-2").exists()
        and not (f.root / "candidate-ticket-5").exists()
    )
    proof = {
        "scope": "Four synthetic calls; no classical, purchase producer or study admission.",
        "ledger_records": len(replay.ledger.records),
        "ledger_bytes": len(raw(replay.ledger)),
        "unresolved_holds": summarize_study(replay.ledger).budget.unresolved_attempts,
        "database_bytes": (f.root / "candidate.sqlite3").stat().st_size,
        "captured_journal_bytes": (f.root / "candidate-journal-1").stat().st_size,
        "setup_parent_cpu_before_proof_ns": f.budget.parent_cpu,
        "setup_child_cpu_ns": f.budget.child_cpu,
        "setup_copy_bytes_before_proof": f.budget.copies,
        "journal_write_epochs": f.budget.child_epochs,
        "publication_escrow_bytes": f.control.publication.required_bytes(),
    }
    with f.budget.phase():
        f.budget.write(f.root / "fixture-proof.json", json.dumps(proof, sort_keys=True).encode())


@pytest.mark.parametrize("fault", ["raw", "after-binding"])
def test_capture_substitution_rejects_without_closure(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    # Independent declared finite variant: two normal calls, no retries/numerical extra calls.
    f = prepare(tmp_path / f"capture-{fault}", actual_build)
    frozen = commit_native_freeze(f.root, f.freeze_request)
    inject_intents(f)
    generate_journal(f)
    request = comparison_request(f, raw(frozen.receipt))
    original = bind_captured_candidate

    def changed(*args: Any, **kwargs: Any) -> Any:
        path = kwargs["snapshot_path"]
        if fault == "after-binding":
            original(*args, **kwargs)
        saved = path.read_bytes() if fault == "raw" else None
        restoration_bytes = len(saved) if saved is not None else 0
        assert f.budget.copies + 1 + restoration_bytes <= COPY_LIMIT
        f.budget.copies += 1 + restoration_bytes
        with path.open("ab") as out:
            out.write(b"x")
        if saved is not None:
            try:
                return original(*args, **kwargs)
            finally:
                # Isolate the reader-digest join: a later capture check sees
                # the original bytes and cannot mask removal of that guard.
                path.write_bytes(saved)
        return None

    monkeypatch.setattr(supervisor, "bind_captured_candidate", changed)
    with pytest.raises(ValueError):
        commit_journal_candidates(f.root, request)
    state = current(f.root)
    assert last_update(state).state == "unknown" and last_update(state).cpu_ns is not None
    with sqlite3.connect(f.root / "candidate.sqlite3") as db:
        assert (
            db.execute("SELECT count(*) FROM closures WHERE logical_id='candidate'").fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("kind", ["pool", "world_catalog", "candidate_config"])
def test_retained_materials_cannot_contradict_frozen_ref(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    kind: str,
) -> None:
    f = prepare(tmp_path / ("artifact-" + kind), actual_build)
    validate_frozen_materials(f.freeze)
    data = f.freeze.model_dump()
    data["artifacts"][kind] = '{"substituted":true}'
    changed = NativeFreezeInput.model_validate(data)
    with pytest.raises(StudyLedgerError, match="artifact_identity"):
        validate_frozen_materials(changed)


def test_freeze_closure_failure_leaves_no_manifest_and_unknown_hold(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f = prepare(tmp_path / "rollback", actual_build)
    original = CandidateStore.replace

    # Detect event type rather than synthesizing a successful freeze result.
    def failing(self: CandidateStore, before: Any, after: Any) -> None:
        original(self, before, after)
        if len(after.records) > len(before.records) + 1:
            raise sqlite3.OperationalError("explicit fixture closure fault")

    monkeypatch.setattr(CandidateStore, "replace", failing)
    with pytest.raises(sqlite3.OperationalError):
        commit_native_freeze(f.root, f.freeze_request)
    state = current(f.root)
    assert last_update(state).state == "unknown"
    with pytest.raises(StudyLedgerError):
        study_manifest(state)
    with sqlite3.connect(f.root / "candidate.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0


def test_freeze_stale_head_is_denied_before_work(
    tmp_path: Path,
    actual_build: TrustedInstallation,
) -> None:
    f = prepare(tmp_path / "stale", actual_build)
    bad = NativeFreezeRequest.model_validate(
        f.freeze_request.model_dump() | {"expected_revision": 0}
    )
    with pytest.raises(StudyLedgerError, match="stale_head"):
        commit_native_freeze(f.root, bad)
    assert len(current(f.root).records) == 2
    assert (f.root / "candidate-ticket-0").exists()


@pytest.mark.parametrize(
    "limits,expected", [((100, 1000), 100), ((-1, 1000), 500), ((700, 800), 500), ((-1, -1), 500)]
)
def test_setup_preserves_inherited_soft_and_hard_limits(
    monkeypatch: pytest.MonkeyPatch, limits: tuple[int, int], expected: int
) -> None:
    import resource

    calls: list[tuple[int, tuple[int, int]]] = []
    monkeypatch.setattr(resource, "getrlimit", lambda which: limits)
    monkeypatch.setattr(resource, "setrlimit", lambda which, value: calls.append((which, value)))
    restrict_limit(resource.RLIMIT_FSIZE, 500)
    assert calls == [(resource.RLIMIT_FSIZE, (expected, expected))]


def test_setup_file_and_directory_are_synced_before_materials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os
    import stat

    actual = os.fsync
    observed: list[str] = []

    def checked(fd: int) -> None:
        observed.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        actual(fd)

    monkeypatch.setattr(os, "fsync", checked)
    budget = SetupBudget(time.monotonic_ns() + 1_000_000_000)
    budget.write(tmp_path / "setup.json", b"retained-hold")
    assert observed == ["file", "directory"]


@pytest.mark.parametrize("fault", ["pool", "manifest-source", "manifest-lock"])
def test_coherent_retained_freeze_corruption_rejects_public_paid_recovery(
    tmp_path: Path, actual_build: TrustedInstallation, fault: str
) -> None:
    from strange_physics import study_ledger
    from strange_physics.candidate_execution_contracts import CandidateAdmission
    from strange_physics.publication_store import Extents, digest, head, root_lock
    from strange_physics.research_contracts import message_sha256
    from strange_physics.study_contracts import NativeStudyLedger
    from strange_physics.study_execution_binding import freeze_result
    from strange_physics.study_execution_contracts import NativeFreezeReceipt

    # One real freeze, one fixed corruption transaction under the setup hold,
    # then a consumed recovery ticket. No observations or numerical call.
    f = prepare(tmp_path / ("coherent-" + fault), actual_build)
    committed = commit_native_freeze(f.root, f.freeze_request)
    data = f.freeze.model_dump()
    if fault == "pool":
        data["artifacts"]["pool"] = data["artifacts"]["pool"].replace("4.0", "5.0")
        assert data["artifacts"]["pool"] != f.freeze.artifacts["pool"]
    else:
        field = "source_commit" if fault == "manifest-source" else "uv_lock_sha256"
        data["manifest"][field] = "a" * (40 if field == "source_commit" else 64)
    changed = NativeFreezeInput.model_validate(data)
    changed_input = raw(changed)
    changed_result = freeze_result(changed, f.freeze_request.attempt_id)
    request = NativeFreezeRequest.model_validate(
        f.freeze_request.model_dump()
        | {
            "input_raw_sha256": digest(changed_input),
            "input_bytes": len(changed_input),
            "input_sha256": message_sha256(changed),
            "config_sha256": message_sha256(changed.manifest),
        }
    )
    after = NativeStudyLedger(plan=committed.ledger.plan)
    for record in committed.ledger.records:
        event = record.event
        if event.kind == "reserve" and event.attempt_id == request.attempt_id:
            event = type(event).model_validate(
                event.model_dump()
                | {"input_sha256": request.input_sha256, "config_sha256": request.config_sha256}
            )
        elif event.kind == "freeze":
            event = type(event)(manifest=changed.manifest)
        elif event.kind == "update" and event.attempt_id == request.attempt_id:
            event = type(event).model_validate(event.model_dump() | {"facts": changed_result.facts})
        after = study_ledger._append(after, record.event_id, event, len(after.records))
    original = NativeStudyLedger(plan=after.plan, records=after.records[:3])
    receipt = NativeFreezeReceipt.model_validate(
        committed.receipt.model_dump()
        | {
            "request_sha256": supervisor._identity(request),
            "input_raw_sha256": digest(changed_input),
            "result_raw_sha256": digest(raw(changed_result)),
            "original_head_sha256": head(original),
            "original_ledger_sha256": digest(raw(original)),
        }
    )
    with f.budget.phase(), root_lock(f.root):
        admission = CandidateAdmission.model_validate_json(
            (f.root / "candidate-admission.json").read_bytes()
        )
        store = CandidateStore(
            f.root,
            admission,
            (f.root / "candidate-seed.json").read_bytes(),
            Extents(f.root, database_name="candidate.sqlite3"),
        )
        try:
            for name, value in (
                ("candidate-input-0", changed_input),
                ("candidate-output-0", raw(changed_result)),
            ):
                assert f.budget.copies + len(value) <= COPY_LIMIT
                f.budget.copies += len(value)
                (f.root / name).write_bytes(value)
            store.limit_control_growth()
            with store.transaction():
                store.db.execute(
                    "UPDATE state SET ledger=?,revision=?,head=? WHERE id=1",
                    (raw(after), len(after.records), head(after)),
                )
                store.db.execute("DELETE FROM records")
                store._records(after, 0)
                store.db.execute(
                    "UPDATE closures SET identity=?,request=?,receipt=?,receipt_digest=? "
                    "WHERE logical_id='freeze'",
                    (
                        supervisor._identity(request),
                        raw(request),
                        raw(receipt),
                        digest(raw(receipt)),
                    ),
                )
            assert store.ledger() == after
        finally:
            store.close()
    expected = "artifact_identity" if fault == "pool" else "freeze_build_identity"
    with pytest.raises(StudyLedgerError, match=expected):
        commit_native_freeze(f.root, recover(request, 3))
    assert (f.root / "candidate-ticket-3").exists()
    assert len(current(f.root).records) == 5


@pytest.mark.parametrize("fault", ["source_commit", "installation_sha256", "logical_alias"])
def test_nested_freeze_uses_selected_sql_row_and_verified_build(
    tmp_path: Path, actual_build: TrustedInstallation, fault: str
) -> None:
    from strange_physics.candidate_execution_contracts import CandidateAdmission
    from strange_physics.contracts import ObservationBundle
    from strange_physics.native_spring_contracts import (
        NativeCandidateConfig,
        NativeCandidateInput,
        NativeSpringPool,
    )
    from strange_physics.publication_store import Extents, digest, root_lock
    from strange_physics.study_contracts import NativeWorldCatalog
    from strange_physics.study_execution_contracts import NativeComparisonInput, NativeFreezeReceipt

    f = prepare(tmp_path / ("nested-" + fault), actual_build)
    committed = commit_native_freeze(f.root, f.freeze_request)
    catalog = NativeWorldCatalog.model_validate_json(f.freeze.artifacts["world_catalog"])
    material = NativeComparisonInput(
        candidate=NativeCandidateInput(
            pool=NativeSpringPool.model_validate_json(f.freeze.artifacts["pool"]),
            config=NativeCandidateConfig(),
            observations=ObservationBundle(
                run_id=f.freeze.manifest.cells[0].journal_id,
                engine_version="synthetic-no-observation",
                engine_fingerprint=actual_build.engine_fingerprint,
                space=catalog.worlds[0].definition.space,
                records=(),
            ),
        ),
        freeze_logical_id="freeze",
        freeze_receipt_sha256=digest(raw(committed.receipt)),
        journal_path=str(f.journal),
        journal_sha256="0" * 64,
        journal_bytes=100,
    )
    with f.budget.phase(), root_lock(f.root):
        admission = CandidateAdmission.model_validate_json(
            (f.root / "candidate-admission.json").read_bytes()
        )
        store = CandidateStore(
            f.root,
            admission,
            (f.root / "candidate-seed.json").read_bytes(),
            Extents(f.root, database_name="candidate.sqlite3"),
        )
        try:
            # Positive uses the real SQLite closure, before changing just one join.
            assert supervisor._retained_freeze(store, material, committed.ledger) == f.freeze
            store.limit_control_growth()
            with store.transaction():
                if fault == "logical_alias":
                    store.db.execute(
                        "INSERT INTO closures SELECT 'alias',identity,request,"
                        "input_name,result_name,"
                        "receipt,receipt_digest FROM closures WHERE logical_id='freeze'"
                    )
                    material = NativeComparisonInput.model_validate(
                        material.model_dump() | {"freeze_logical_id": "alias"}
                    )
                else:
                    receipt = NativeFreezeReceipt.model_validate(
                        committed.receipt.model_dump()
                        | {fault: "a" * (40 if fault == "source_commit" else 64)}
                    )
                    store.db.execute(
                        "UPDATE closures SET receipt=?,receipt_digest=? WHERE logical_id='freeze'",
                        (raw(receipt), digest(raw(receipt))),
                    )
                    material = NativeComparisonInput.model_validate(
                        material.model_dump() | {"freeze_receipt_sha256": digest(raw(receipt))}
                    )
            with pytest.raises(StudyLedgerError, match="comparison_freeze_identity"):
                supervisor._retained_freeze(store, material, committed.ledger)
        finally:
            store.close()


def test_root_creation_sync_uses_existing_setup_timer(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    import signal

    import freeze_journal_fixture as fixture_module

    original = fixture_module.sync_directory
    cpu = [100]
    observed = []

    def checked(path: Path) -> None:
        assert signal.getitimer(signal.ITIMER_REAL)[0] > 0
        assert signal.getitimer(signal.ITIMER_PROF)[0] > 0
        if path == tmp_path:
            cpu[0] += 250_000
            observed.append(path)
        original(path)

    monkeypatch.setattr(fixture_module, "sync_directory", checked)
    monkeypatch.setattr(time, "process_time_ns", lambda: cpu[0])
    f = prepare(tmp_path / "timed-root", actual_build)
    assert observed == [tmp_path]
    assert f.budget.parent_cpu == 250_000
