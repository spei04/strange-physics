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
        assert f.budget.copies + 1 <= COPY_LIMIT
        f.budget.copies += 1
        with path.open("ab") as out:
            out.write(b"x")
        if fault == "raw":
            return original(*args, **kwargs)
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


def test_freeze_stale_head_and_wrong_wrapper_are_denied_before_work(
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
    "limits,expected", [((100, 1000), 100), ((-1, 1000), 500), ((700, 800), 500)]
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
