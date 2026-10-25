"""Bounded SQLite/process conformance only; no simulator or purchase authority."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_study_journal import catalog, create, experiment

from strange_physics.contracts import ExperimentRecord
from strange_physics.journal import Journal
from strange_physics.purchase_journal import (
    JOURNAL_BYTES,
    JournalBoundError,
    JournalEpochs,
    capture_journal,
)


def deadline(seconds: float = 5) -> int:
    return time.monotonic_ns() + int(seconds * 1e9)


def private(path: Path) -> Path:
    path.mkdir(mode=0o700)
    return path


def writer(path: Path, *, soft: int | None = None, reuse: bool = False) -> dict[str, object]:
    epochs = JournalEpochs()
    budget = epochs.writer(deadline())
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        result: dict[str, object] = {}
        try:
            if soft is not None:
                _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
                resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))
            budget.install(cpu_seconds=2)
            result["limit"] = resource.getrlimit(resource.RLIMIT_FSIZE)[0]
            with_open = Journal(path, create=True, bounded=budget)
            try:
                with_open.initialize("fixture", catalog().worlds[0].definition, "e" * 64)
                with_open.reserve("operation", experiment(), 12)
                with_open.record_failure("operation", "SimulationError", [])
                record = ExperimentRecord(
                    operation_id="operation",
                    index=0,
                    experiment=experiment(),
                    status="failed",
                    error="simulation_failed",
                )
                with_open.commit(record)
                result["pending"] = len(with_open.pending())
                result["failed"] = with_open.records()[0].status
                if reuse:
                    with_open.reserve("operation", experiment(), 12)
            finally:
                with_open.close()
            result["ok"] = True
        except BaseException as error:
            result["error"] = str(error)
        finally:
            result["used"] = sorted(budget.used)
            os.write(write_fd, json.dumps(result).encode())
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    budget.close()
    data = os.read(read_fd, 8192)
    os.close(read_fd)
    _, status, _ = os.wait4(pid, 0)
    return {"status": status, "reserved": epochs.used, **(json.loads(data) if data else {})}


def test_bounded_creation_real_small_row_and_failed_record(tmp_path: Path) -> None:
    root = private(tmp_path / "private")
    parent_limits = resource.getrlimit(resource.RLIMIT_FSIZE)
    result = writer(root / "journal.db")
    assert result["ok"] is True
    assert result["reserved"] == 14
    assert len(result["used"]) == 14
    assert result["failed"] == "failed" and result["pending"] == 0
    assert (root / "journal.db").stat().st_size <= JOURNAL_BYTES
    assert not (root / "journal.db-journal").exists()
    assert resource.getrlimit(resource.RLIMIT_FSIZE) == parent_limits


def test_epoch_reuse_denied_before_second_reserve(tmp_path: Path) -> None:
    root = private(tmp_path / "private")
    result = writer(root / "journal.db", reuse=True)
    assert result["error"] == "journal_epoch_reused"
    journal = Journal(root / "journal.db")
    try:
        assert journal.used == 1 and journal.records()[0].status == "failed"
    finally:
        journal.close()


def test_stricter_inherited_soft_limit_is_preserved(tmp_path: Path) -> None:
    root = private(tmp_path / "private")
    result = writer(root / "journal.db", soft=65536)
    assert result["limit"] == 65536
    assert result["ok"] is True


def test_child_guard_does_not_change_parent_limits() -> None:
    epochs = JournalEpochs()
    budget = epochs.writer(deadline())
    before = resource.getrlimit(resource.RLIMIT_FSIZE)
    try:
        with pytest.raises(JournalBoundError, match="journal_child_only"):
            budget.install(cpu_seconds=2)
    finally:
        budget.close()
    assert before == resource.getrlimit(resource.RLIMIT_FSIZE)
    assert epochs.used == 14


def test_forked_copies_cannot_reuse_writer_token() -> None:
    epochs = JournalEpochs()
    budget = epochs.writer(deadline())
    statuses = []
    for _ in range(2):
        pid = os.fork()
        if pid == 0:
            try:
                budget.install(cpu_seconds=2)
                os._exit(0)
            except BaseException:
                os._exit(70)
        statuses.append(os.waitpid(pid, 0)[1])
    budget.close()
    assert statuses == [0, 70 << 8]
    assert epochs.used == 14


def fresh_writer(path: Path) -> subprocess.CompletedProcess[str]:
    code = """import sqlite3,sys
db=sqlite3.connect(sys.argv[1],timeout=0,isolation_level=None)
try:
 db.execute("BEGIN IMMEDIATE")
 db.execute("INSERT OR IGNORE INTO failures VALUES ('competitor','test','[]')")
 db.execute("COMMIT")
except sqlite3.OperationalError:
 sys.exit(2)
finally:
 db.close()
"""
    return subprocess.run(
        [sys.executable, "-c", code, str(path)], text=True, capture_output=True, timeout=3
    )


def test_holder_real_lock_rechecks_commit_and_release(tmp_path: Path) -> None:
    path = private(tmp_path / "private") / "journal.db"
    create(path, ("completed", "failed", "pending"))
    raw = path.read_bytes()
    epochs = JournalEpochs()
    with capture_journal(
        path, hashlib.sha256(raw).hexdigest(), epochs=epochs, deadline_ns=deadline()
    ) as capture:
        assert capture.raw == raw
        assert capture.holder_cpu_ns is None
        assert fresh_writer(path).returncode == 2
        capture.recheck()
        assert fresh_writer(path).returncode == 2
        # An actual independent parent store transaction completes while held.
        with sqlite3.connect(path.parent / "store.db") as store:
            store.execute("CREATE TABLE receipt (raw BLOB)")
            store.execute("INSERT INTO receipt VALUES (?)", (raw,))
        assert fresh_writer(path).returncode == 2
    assert epochs.used == 1 and capture.holder_status == 0
    assert capture.holder_cpu_ns is not None and capture.holder_cpu_ns >= 0
    assert fresh_writer(path).returncode == 0
    with pytest.raises(ChildProcessError):
        os.waitpid(capture.pid, os.WNOHANG)


def test_holder_wrong_identity_reaps_and_keeps_epoch(tmp_path: Path) -> None:
    path = private(tmp_path / "private") / "journal.db"
    create(path)
    epochs = JournalEpochs()
    with pytest.raises((JournalBoundError, ConnectionError)):
        with capture_journal(path, "a" * 64, epochs=epochs, deadline_ns=deadline()):
            pytest.fail("wrong identity reached caller")
    assert epochs.used == 1 and epochs.holder_cpu_ns is not None
    assert epochs.holder_status != 0
    assert epochs.holder_pid is not None
    with pytest.raises(ChildProcessError):
        os.waitpid(epochs.holder_pid, os.WNOHANG)


def test_holder_caller_failure_preserved_and_lock_released(tmp_path: Path) -> None:
    path = private(tmp_path / "private") / "journal.db"
    create(path)
    epochs = JournalEpochs()
    with pytest.raises(ValueError, match="original"):
        with capture_journal(
            path,
            hashlib.sha256(path.read_bytes()).hexdigest(),
            epochs=epochs,
            deadline_ns=deadline(),
        ):
            raise ValueError("original")
    assert epochs.holder_status == 0
    assert fresh_writer(path).returncode == 0


def test_expired_holder_deadline_consumes_epoch_without_fork(tmp_path: Path) -> None:
    epochs = JournalEpochs()
    with pytest.raises(JournalBoundError, match="journal_deadline"):
        with capture_journal(
            tmp_path / "missing", "a" * 64, epochs=epochs, deadline_ns=time.monotonic_ns() - 1
        ):
            pytest.fail("expired")
    assert epochs.used == 1 and epochs.holder_pid is None


def test_ordinary_journal_idempotence_unchanged(tmp_path: Path) -> None:
    path = private(tmp_path / "private") / "journal.db"
    create(path, ("failed",))
    journal = Journal(path)
    try:
        original = journal.records()[0]
        assert journal.reserve(original.operation_id, original.experiment, 12).record == original
        assert journal.commit(original) == original
        assert journal.records() == (original,)
    finally:
        journal.close()
