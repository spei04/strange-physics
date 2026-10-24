"""Bounded candidate metadata, immutable receipt references and monotone initialization."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from strange_physics.candidate_execution_contracts import MIB, CandidateAdmission
from strange_physics.publication_store import (
    Extents,
    digest,
    durable_directory,
    head,
    raw,
    regular,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import MAX_STUDY_JSON_BYTES, NativeStudyLedger
from strange_physics.study_ledger import StudyLedgerError, read_study_ledger
from strange_physics.workflow_io import read_bytes

PAGE = 4096
STORE_ID = 0x53504341


class CandidateStore:
    def __init__(
        self, root: Path, admission: CandidateAdmission, seed: bytes, meter: Extents
    ) -> None:
        self.root, self.meter, self.admission = root, meter, admission
        self.path = root / "candidate.sqlite3"
        existing = regular(self.path, missing=True)
        marker = root / "candidate-created"
        marked = regular(marker, missing=True)
        if (existing is None) != (marked is None):
            raise StudyLedgerError("candidate_store_missing_or_partial")
        if marked and read_bytes(marker, limit=64) != digest(raw(admission)).encode():
            raise StudyLedgerError("candidate_store_identity")
        for suffix in ("-wal", "-shm"):
            if Path(str(self.path) + suffix).exists():
                raise StudyLedgerError("candidate_store_mode")
        if existing is None:
            meter.write(marker, digest(raw(admission)).encode())
            durable_directory(root)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        elif not 100 <= existing.st_size <= admission.control.database_limit_bytes:
            raise StudyLedgerError("candidate_store_corrupt")
        regular(Path(str(self.path) + "-journal"), missing=True)
        self.db = sqlite3.connect(self.path, timeout=0, isolation_level=None)
        try:
            if existing is None:
                self.db.execute(f"PRAGMA page_size={PAGE}")
            if self.db.execute("PRAGMA page_size").fetchone()[0] != PAGE:
                raise StudyLedgerError("candidate_store_page_size")
            self.db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 16 * MIB)
            self.db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8192)
            for pragma in (
                "trusted_schema=OFF",
                "temp_store=MEMORY",
                "cache_spill=OFF",
                "synchronous=FULL",
                "journal_size_limit=-1",
            ):
                self.db.execute("PRAGMA " + pragma)
            if (
                self.db.execute("PRAGMA journal_mode=PERSIST").fetchone()[0] != "persist"
                or self.db.execute("PRAGMA cache_spill").fetchone()[0] != 0
                or self.db.execute("PRAGMA auto_vacuum").fetchone()[0] != 0
                or self.db.execute("PRAGMA temp_store").fetchone()[0] != 2
            ):
                raise StudyLedgerError("candidate_store_mode")
            self.limit_control_growth()
            if existing is None:
                with self.transaction():
                    self.db.execute(f"PRAGMA application_id={STORE_ID}")
                    self.db.execute("PRAGMA user_version=1")
                    self.db.execute(
                        "CREATE TABLE state(id INTEGER PRIMARY KEY CHECK(id=1), "
                        "admission BLOB NOT NULL,ledger BLOB NOT NULL,revision INTEGER "
                        "NOT NULL,head TEXT NOT NULL,stopped INTEGER NOT NULL)"
                    )
                    self.db.execute(
                        "CREATE TABLE records(sequence INTEGER PRIMARY KEY,"
                        "event_id TEXT UNIQUE NOT NULL,digest TEXT NOT NULL)"
                    )
                    self.db.execute(
                        "CREATE TABLE closures(logical_id TEXT PRIMARY KEY,"
                        "identity TEXT NOT NULL,request BLOB NOT NULL,"
                        "input_name TEXT NOT NULL,result_name TEXT NOT NULL,"
                        "receipt BLOB NOT NULL,receipt_digest TEXT NOT NULL)"
                    )
                    ledger = read_study_ledger(seed)
                    self.db.execute(
                        "INSERT INTO state VALUES(1,?,?,?,?,0)",
                        (raw(admission), raw(ledger), len(ledger.records), head(ledger)),
                    )
                    self._records(ledger, 0)
            if (
                self.db.execute("PRAGMA application_id").fetchone()[0] != STORE_ID
                or self.db.execute("PRAGMA user_version").fetchone()[0] != 1
            ):
                raise StudyLedgerError("candidate_store_corrupt")
            tables = set(
                self.db.execute(
                    "SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
            )
            if tables != {(n, "table") for n in ("state", "records", "closures")}:
                raise StudyLedgerError("candidate_store_corrupt")
            row = self.db.execute("SELECT admission,stopped FROM state WHERE id=1").fetchone()
            if row is None or row[0] != raw(admission) or row[1] not in (0, 1):
                raise StudyLedgerError("candidate_store_identity")
            current = self.ledger()
            original = read_study_ledger(seed)
            if (
                current.plan != original.plan
                or current.records[: len(original.records)] != original.records
            ):
                raise StudyLedgerError("candidate_store_seed_prefix")
        except BaseException:
            self.close()
            raise

    def limit_control_growth(self) -> None:
        # A single retained DB/PERSIST pair has a lifetime extent envelope, not
        # a fresh large per-ticket artifact allocation. Neither file may shrink.
        self.meter.sample()
        existing = sum(v[1] for v in self.meter.high.values())
        self.limit_growth(self.admission.control.database_envelope() - existing)

    def limit_growth(self, amount: int) -> None:
        self.meter.sample()
        pages = self.db.execute("PRAGMA page_count").fetchone()[0]
        retained = self.meter.high.get(Path(str(self.path) + "-journal"), (0, 0))[1]
        growth = max(0, pages * (PAGE + 8) + 2 * 65536 - retained)
        if amount < growth:
            raise StudyLedgerError("candidate_sqlite_headroom")
        limit = min(
            self.admission.control.database_limit_bytes // PAGE, pages + (amount - growth) // PAGE
        )
        if (
            limit < max(1, pages)
            or self.db.execute(f"PRAGMA max_page_count={limit}").fetchone()[0] != limit
        ):
            raise StudyLedgerError("candidate_sqlite_headroom")

    def _records(self, ledger: NativeStudyLedger, start: int) -> None:
        self.db.executemany(
            "INSERT INTO records VALUES(?,?,?)",
            [(x.sequence, x.event_id, message_sha256(x)) for x in ledger.records[start:]],
        )

    def ledger(self) -> NativeStudyLedger:
        row = self.db.execute(
            "SELECT length(ledger),revision,head FROM state WHERE id=1"
        ).fetchone()
        if row is None or not 0 < row[0] <= MAX_STUDY_JSON_BYTES:
            raise StudyLedgerError("candidate_store_corrupt")
        if self.db.execute("SELECT count(*) FROM records").fetchone()[0] > 8192:
            raise StudyLedgerError("candidate_store_corrupt")
        ledger = read_study_ledger(
            self.db.execute("SELECT ledger FROM state WHERE id=1").fetchone()[0]
        )
        records = self.db.execute(
            "SELECT sequence,event_id,digest FROM records ORDER BY sequence"
        ).fetchall()
        if (len(ledger.records), head(ledger)) != tuple(row[1:]) or records != [
            (x.sequence, x.event_id, message_sha256(x)) for x in ledger.records
        ]:
            raise StudyLedgerError("candidate_store_corrupt")
        return ledger

    def replace(self, before: NativeStudyLedger, after: NativeStudyLedger) -> None:
        if after.records[: len(before.records)] != before.records or after.plan != before.plan:
            raise StudyLedgerError("candidate_store_prefix")
        if (
            self.db.execute(
                "UPDATE state SET ledger=?,revision=?,head=? WHERE id=1 AND revision=? AND head=?",
                (raw(after), len(after.records), head(after), len(before.records), head(before)),
            ).rowcount
            != 1
        ):
            raise StudyLedgerError("candidate_store_cas")
        self._records(after, len(before.records))
        self.meter.sample()

    @property
    def stopped(self) -> bool:
        return bool(self.db.execute("SELECT stopped FROM state WHERE id=1").fetchone()[0])

    def stop(self) -> None:
        self.db.execute("UPDATE state SET stopped=1 WHERE id=1")

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.meter.sample()
            self.db.commit()
            self.meter.sample()
            durable_directory(self.root)
        except BaseException:
            if self.db.in_transaction:
                self.db.rollback()
            self.meter.sample()
            raise

    def close(self) -> None:
        if self.db.in_transaction:
            self.db.rollback()
        self.db.close()
        self.meter.sample()
