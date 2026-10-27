"""Bounded candidate metadata, immutable receipt references and monotone initialization."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from strange_physics.bounded_json import bounded_canonical
from strange_physics.candidate_execution_contracts import (
    MIB,
    STORE_ATTEMPTS_PER_TICKET,
    CandidateAdmission,
)
from strange_physics.publication_handoff_contracts import (
    HANDOFF_SEAL_BYTES,
    PublicationHandoffSeal,
    read_handoff_seal,
    validate_handoff_ledger,
)
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
JOURNAL_MAGIC = bytes.fromhex("d9d505f920a163d7")


def _journal_bound(path: Path, admission: CandidateAdmission) -> None:
    before = regular(path, missing=True)
    if before is None:
        return
    if before.st_size > admission.control.database_envelope():
        raise StudyLedgerError("candidate_store_journal_bound")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        header = os.pread(fd, 28, 0)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            opened.st_dev,
            opened.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise StudyLedgerError("candidate_store_journal_changed")
    finally:
        os.close(fd)
    if header[:8] == JOURNAL_MAGIC:
        # SQLite can resize the DB during hot-journal recovery, before our
        # PRAGMA max_page_count takes effect. Check its actual header first.
        pages = int.from_bytes(header[16:20], "big")
        sector = int.from_bytes(header[20:24], "big")
        page_size = int.from_bytes(header[24:28], "big")
        if (
            len(header) != 28
            or pages > admission.control.database_limit_bytes // PAGE
            or page_size != PAGE
            or not 512 <= sector <= 65536
            or sector & (sector - 1)
        ):
            raise StudyLedgerError("candidate_store_hot_journal_bound")


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
        _journal_bound(Path(str(self.path) + "-journal"), admission)
        # Existing-store recovery gets the same envelope as first initialization.
        # Reserve, closure and one fallback are the only remaining write attempts.
        self._transaction_attempts = 0 if existing is None else 1
        self._initializing = existing is None
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
            self._initializing = False
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            application_id = self.db.execute("PRAGMA application_id").fetchone()[0]
            if application_id != STORE_ID or version not in (1, 2):
                raise StudyLedgerError("candidate_store_corrupt")
            tables = set(
                self.db.execute(
                    "SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
                ).fetchall()
            )
            expected_tables = {("state", "table"), ("records", "table"), ("closures", "table")}
            if version == 2:
                expected_tables.add(("handoff", "table"))
            if tables != expected_tables:
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
            if version == 2:
                self._handoff(current)
        except BaseException as error:
            try:
                self.close()
            except Exception:
                error.add_note("Store cleanup failed; original initialization failure preserved.")
            raise

    def limit_control_growth(self) -> None:
        # Each bounded transaction has a separately prepaid whole DB/PERSIST
        # envelope. Rollback or a later restart may recreate an earlier range;
        # observed high-water extents alone are not a lifetime cost bound.
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
        self.require_writable()
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

    def require_writable(self) -> None:
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version == 2:
            raise StudyLedgerError("candidate_store_sealed")
        if version != 1:
            raise StudyLedgerError("candidate_store_corrupt")

    def handoff(self) -> PublicationHandoffSeal | None:
        """Read the one committed seal against the actual current ledger."""
        return self._handoff(self.ledger())

    def _handoff(self, ledger: NativeStudyLedger) -> PublicationHandoffSeal | None:
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version == 1:
            return None
        if version != 2 or self.db.execute("SELECT count(*) FROM handoff").fetchone()[0] != 1:
            raise StudyLedgerError("candidate_store_corrupt")
        row = self.db.execute("SELECT length(seal),digest FROM handoff WHERE id=1").fetchone()
        if row is None or not 0 < row[0] <= HANDOFF_SEAL_BYTES:
            raise StudyLedgerError("candidate_store_corrupt")
        data = self.db.execute("SELECT seal FROM handoff WHERE id=1").fetchone()[0]
        seal = read_handoff_seal(data)
        if digest(data) != row[1] or raw(seal) != data or seal.source_admission != self.admission:
            raise StudyLedgerError("candidate_handoff_identity")
        validate_handoff_ledger(seal, ledger)
        return seal

    def seal(
        self, before: NativeStudyLedger, after: NativeStudyLedger, seal: PublicationHandoffSeal
    ) -> None:
        """Commit ownership with the final known update and actual publisher hold.

        The caller owns the existing bounded transaction and all material/FD
        witnesses. There is no extra transaction or post-commit source update.
        """
        self.require_writable()
        if not self.db.in_transaction:
            raise StudyLedgerError("candidate_handoff_transaction")
        if self.stopped:
            raise StudyLedgerError("candidate_stopped")
        bounded_canonical(seal, HANDOFF_SEAL_BYTES)
        checked = read_handoff_seal(raw(seal))
        if (
            checked.source_admission != self.admission
            or len(after.records) != len(before.records) + 2
        ):
            raise StudyLedgerError("candidate_handoff_identity")
        # Reparse the proposed seed instead of trusting mutable or constructed
        # models. The usual replace CAS still checks the complete original prefix.
        bounded_canonical(after, MAX_STUDY_JSON_BYTES)
        final = read_study_ledger(raw(after))
        validate_handoff_ledger(checked, final)
        self.replace(before, final)
        self.db.execute(
            "CREATE TABLE handoff(id INTEGER PRIMARY KEY CHECK(id=1),"
            "seal BLOB NOT NULL,digest TEXT NOT NULL)"
        )
        data = raw(checked)
        self.db.execute("INSERT INTO handoff VALUES(1,?,?)", (data, digest(data)))
        self.db.execute("PRAGMA user_version=2")
        self.meter.sample()

    @property
    def stopped(self) -> bool:
        return bool(self.db.execute("SELECT stopped FROM state WHERE id=1").fetchone()[0])

    def stop(self) -> None:
        self.require_writable()
        self.db.execute("UPDATE state SET stopped=1 WHERE id=1")

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if not self._initializing:
            self.require_writable()
        if self._transaction_attempts >= STORE_ATTEMPTS_PER_TICKET:
            raise StudyLedgerError("candidate_transaction_limit")
        self._transaction_attempts += 1
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


def read_sealed_handoff(
    root: Path, admission: CandidateAdmission
) -> tuple[PublicationHandoffSeal, bytes]:
    """Read a committed seal under the caller's source lock, without writable open.

    A hot journal or incomplete database is not an activation authority. No
    recovery is attempted; original source costs and partial bytes are retained.
    """
    path = root / "candidate.sqlite3"
    before = regular(path)
    assert before is not None
    if not 100 <= before.st_size <= admission.control.database_limit_bytes:
        raise StudyLedgerError("candidate_store_corrupt")
    if read_bytes(root / "candidate-created", limit=64) != digest(raw(admission)).encode():
        raise StudyLedgerError("candidate_store_identity")
    for suffix in ("-wal", "-shm"):
        if Path(str(path) + suffix).exists():
            raise StudyLedgerError("candidate_store_mode")
    journal = regular(Path(str(path) + "-journal"), missing=True)
    if journal is not None:
        value = read_bytes(
            Path(str(path) + "-journal"), limit=admission.control.database_envelope()
        )
        if value[:8].strip(b"\x00"):
            raise StudyLedgerError("candidate_store_recovery_required")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0, isolation_level=None)
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 16 * MIB)
        if (
            db.execute("PRAGMA application_id").fetchone()[0],
            db.execute("PRAGMA user_version").fetchone()[0],
        ) != (STORE_ID, 2):
            raise StudyLedgerError("candidate_store_unsealed")
        if set(
            db.execute(
                "SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ) != {(n, "table") for n in ("state", "records", "closures", "handoff")}:
            raise StudyLedgerError("candidate_store_corrupt")
        row = db.execute(
            "SELECT length(admission),length(ledger),revision,head,stopped FROM state WHERE id=1"
        ).fetchone()
        if (
            row is None
            or row[0] != len(raw(admission))
            or not 0 < row[1] <= admission.control.publication.ledger_bytes
            or row[4] != 0
        ):
            raise StudyLedgerError("candidate_store_identity")
        saved, seed = db.execute("SELECT admission,ledger FROM state WHERE id=1").fetchone()
        ledger = read_study_ledger(seed)
        if saved != raw(admission) or (len(ledger.records), head(ledger)) != tuple(row[2:4]):
            raise StudyLedgerError("candidate_store_identity")
        if db.execute(
            "SELECT sequence,event_id,digest FROM records ORDER BY sequence"
        ).fetchall() != [(r.sequence, r.event_id, message_sha256(r)) for r in ledger.records]:
            raise StudyLedgerError("candidate_store_corrupt")
        row = db.execute("SELECT length(seal),digest FROM handoff WHERE id=1").fetchone()
        if (
            row is None
            or not 0 < row[0] <= HANDOFF_SEAL_BYTES
            or db.execute("SELECT count(*) FROM handoff").fetchone()[0] != 1
        ):
            raise StudyLedgerError("candidate_handoff_corrupt")
        seal_raw = db.execute("SELECT seal FROM handoff WHERE id=1").fetchone()[0]
        seal = read_handoff_seal(seal_raw)
        if (
            digest(seal_raw) != row[1]
            or seal_raw != raw(seal)
            or seal.source_admission != admission
        ):
            raise StudyLedgerError("candidate_handoff_corrupt")
        validate_handoff_ledger(seal, ledger)
        after = regular(path)
        assert after is not None
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise StudyLedgerError("candidate_handoff_changed")
        return seal, seed
    finally:
        db.close()
