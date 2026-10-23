"""Owner-private, bounded SQLite and Journal exclusion for the fixed publisher.

Linux local filesystems only. The owner must protect ancestors from replacement.
No directory lock claims to exclude a legacy creator that does not acquire it.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.measured_publication_contracts import PublicationAdmission
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_contracts import MAX_STUDY_JSON_BYTES, NativeStudyLedger
from strange_physics.study_journal import MAX_JOURNAL_BYTES
from strange_physics.study_ledger import StudyLedgerError, read_study_ledger
from strange_physics.workflow_io import private_stat, read_bytes, safe_path

PAGE = 4096
MAX_STORE_BYTES = 1024**3
STORE_ID = 0x53505055


def raw(value: Message) -> bytes:
    return canonical_json(value.model_dump(mode="json")).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def head(value: NativeStudyLedger) -> str:
    return message_sha256(value.records[-1] if value.records else value.plan)


def regular(path: Path, *, missing: bool = False) -> os.stat_result | None:
    safe_path(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        if missing:
            return None
        raise
    private_stat(info)
    if info.st_nlink != 1:
        raise StudyLedgerError("unsafe_hardlink")
    return info


def durable_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        private_stat(os.fstat(fd), directory=True)
        os.fsync(fd)
    finally:
        os.close(fd)


class Extents:
    """Cumulative logical newly-created extents, not writes or physical allocation.

    All controlled scratch files are exclusive, written once, and observed before
    deletion. SQLite uses retained PERSIST extents; disappearance/shrink is an
    accounting fault. Crashes retain the full unknown reservation.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.total = 0
        self.high: dict[Path, tuple[int, int]] = {}
        for name in ("publication.sqlite3", "publication.sqlite3-journal"):
            p = root / name
            s = regular(p, missing=True)
            if s is not None:
                self.high[p] = (s.st_ino, s.st_size)

    def sample(self) -> None:
        for name in ("publication.sqlite3", "publication.sqlite3-journal"):
            p = self.root / name
            s = regular(p, missing=True)
            previous = self.high.get(p)
            if s is None:
                if previous is not None:
                    raise StudyLedgerError("extent_disappeared")
                continue
            if previous is not None:
                inode, size = previous
                if s.st_ino != inode or s.st_size < size:
                    raise StudyLedgerError("extent_regressed")
            else:
                size = 0
            self.total += s.st_size - size
            self.high[p] = (s.st_ino, s.st_size)

    def write(self, path: Path, data: bytes) -> None:
        safe_path(path)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            view = memoryview(data)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError("short private write")
                self.total += count
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)


@contextmanager
def root_lock(root: Path) -> Iterator[None]:
    """Cooperating creators use this same lock; lock order is root then Journal."""
    root = safe_path(root)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        private_stat(os.fstat(fd), directory=True)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StudyLedgerError("publication_busy") from None
        before = os.fstat(fd)
        if (root.stat().st_dev, root.stat().st_ino) != (before.st_dev, before.st_ino):
            raise StudyLedgerError("root_replaced")
        yield
        if (root.stat().st_dev, root.stat().st_ino) != (before.st_dev, before.st_ino):
            raise StudyLedgerError("root_replaced")
    finally:
        os.close(fd)


def _read_descriptor(fd: int) -> bytes:
    before = os.fstat(fd)
    private_stat(before)
    if before.st_nlink != 1 or before.st_size > MAX_JOURNAL_BYTES:
        raise StudyLedgerError("journal_limit")
    chunks = []
    offset = 0
    while offset <= MAX_JOURNAL_BYTES:
        chunk = os.pread(fd, min(1024 * 1024, MAX_JOURNAL_BYTES + 1 - offset), offset)
        if not chunk:
            break
        chunks.append(chunk)
        offset += len(chunk)
    after = os.fstat(fd)
    if offset > MAX_JOURNAL_BYTES or (before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise StudyLedgerError("journal_changed")
    return b"".join(chunks)


@dataclass
class LockedJournal:
    path: Path
    descriptor: int | None
    original: bytes | None

    def recheck(self) -> None:
        if self.descriptor is None:
            if self.path.exists() or self.path.is_symlink():
                raise StudyLedgerError("journal_changed")
            return
        current = regular(self.path)
        held = os.fstat(self.descriptor)
        if current is None or (current.st_dev, current.st_ino) != (held.st_dev, held.st_ino):
            raise StudyLedgerError("journal_changed")
        if _read_descriptor(self.descriptor) != self.original:
            raise StudyLedgerError("journal_changed")
        if any(Path(str(self.path) + suffix).exists() for suffix in ("-journal", "-wal", "-shm")):
            raise StudyLedgerError("journal_nonquiescent")


@contextmanager
def journal_snapshot(path: Path, expected: str | None) -> Iterator[LockedJournal]:
    """Keep every raw same-inode fd open until SQLite releases its POSIX locks."""
    path = safe_path(path)
    private_stat(path.parent.stat(), directory=True)
    info = regular(path, missing=True)
    db: sqlite3.Connection | None = None
    descriptor: int | None = None
    if info is None:
        if expected is not None:
            raise StudyLedgerError("journal_identity_mismatch")
        locked = LockedJournal(path, None, None)
        yield locked
        locked.recheck()
        return
    try:
        for suffix in ("-journal", "-wal", "-shm"):
            if Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink():
                raise StudyLedgerError("journal_nonquiescent")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        before = _read_descriptor(descriptor)
        if len(before) < 100 or before[:16] != b"SQLite format 3\0" or before[18:20] != b"\1\1":
            raise StudyLedgerError("journal_nonquiescent")
        db = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=0, isolation_level=None)
        if db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
            raise StudyLedgerError("journal_nonquiescent")
        try:
            db.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            raise StudyLedgerError("journal_busy") from None
        original = _read_descriptor(descriptor)
        if before != original or digest(original) != expected:
            raise StudyLedgerError("journal_identity_mismatch")
        locked = LockedJournal(path, descriptor, original)
        locked.recheck()
        yield locked
        locked.recheck()
    finally:
        # Closing ANY same-inode fd cancels this process's POSIX locks. Raw fd
        # cleanup must therefore follow SQLite rollback/close, never precede it.
        if db is not None:
            if db.in_transaction:
                db.rollback()
            db.close()
        if descriptor is not None:
            os.close(descriptor)


class Store:
    """One bounded private closure store; no automatic repair/adoption of partial rows."""

    def __init__(
        self, root: Path, admission: PublicationAdmission, seed: bytes, meter: Extents
    ) -> None:
        self.root, self.meter = root, meter
        self.path = root / "publication.sqlite3"
        self.db: sqlite3.Connection
        existing = regular(self.path, missing=True)
        for suffix in ("-wal", "-shm"):
            if Path(str(self.path) + suffix).exists():
                raise StudyLedgerError("store_mode")
        marker = root / "store-created"
        marker_info = regular(marker, missing=True)
        if existing is None and marker_info is not None:
            raise StudyLedgerError("store_missing_after_creation")
        if existing is not None and marker_info is None:
            raise StudyLedgerError("store_creation_identity")
        if (
            marker_info is not None
            and read_bytes(marker, limit=64) != digest(raw(admission)).encode()
        ):
            raise StudyLedgerError("store_creation_identity")
        if existing is None:
            meter.write(marker, digest(raw(admission)).encode())
            durable_directory(root)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        else:
            if existing.st_size < 100 or existing.st_size > MAX_STORE_BYTES:
                raise StudyLedgerError("store_corrupt")
            regular(Path(str(self.path) + "-journal"), missing=True)
        self.db = sqlite3.connect(self.path, timeout=0, isolation_level=None)
        try:
            self.db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 256 * 1024**2)
            self.db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8192)
            self.db.execute("PRAGMA trusted_schema=OFF")
            self.db.execute("PRAGMA temp_store=MEMORY")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA journal_mode=PERSIST")
            self.db.execute("PRAGMA journal_size_limit=-1")
            self.limit_growth(admission.control.ticket_artifact_bytes // 2)
            if existing is None:
                self.db.execute("BEGIN IMMEDIATE")
                self.db.execute(f"PRAGMA application_id={STORE_ID}")
                self.db.execute("PRAGMA user_version=1")
                self.db.execute(
                    "CREATE TABLE state (id INTEGER PRIMARY KEY CHECK(id=1), "
                    "admission BLOB NOT NULL, ledger BLOB NOT NULL, "
                    "revision INTEGER NOT NULL, head TEXT NOT NULL)"
                )
                self.db.execute(
                    "CREATE TABLE records (sequence INTEGER PRIMARY KEY, "
                    "event_id TEXT UNIQUE NOT NULL, digest TEXT NOT NULL)"
                )
                self.db.execute(
                    "CREATE TABLE closures (event_id TEXT PRIMARY KEY, "
                    "request_digest TEXT NOT NULL, request BLOB NOT NULL, "
                    "original BLOB NOT NULL, journal BLOB, evidence BLOB NOT NULL, "
                    "receipt BLOB NOT NULL, receipt_digest TEXT NOT NULL)"
                )
                self.db.execute(
                    "CREATE TABLE materials (event_id TEXT NOT NULL, name TEXT NOT NULL, "
                    "data BLOB NOT NULL, digest TEXT NOT NULL, "
                    "PRIMARY KEY(event_id,name))"
                )
                ledger = read_study_ledger(seed)
                self.db.execute(
                    "INSERT INTO state VALUES (1,?,?,?,?)",
                    (raw(admission), seed, len(ledger.records), head(ledger)),
                )
                self._records(ledger, 0)
                self.meter.sample()
                self.db.commit()
                self.meter.sample()
                durable_directory(root)
            if (
                self.db.execute("PRAGMA application_id").fetchone()[0] != STORE_ID
                or self.db.execute("PRAGMA user_version").fetchone()[0] != 1
            ):
                raise StudyLedgerError("store_corrupt")
            rows = self.db.execute(
                "SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            ).fetchall()
            if set(rows) != {(n, "table") for n in ("state", "records", "closures", "materials")}:
                raise StudyLedgerError("store_corrupt")
            row = self.db.execute("SELECT admission FROM state WHERE id=1").fetchone()
            if row is None or row[0] != raw(admission):
                raise StudyLedgerError("store_identity")
            self.ledger()
        except BaseException:
            self.close()
            raise

    def limit_growth(self, amount: int) -> None:
        pages = self.db.execute("PRAGMA page_count").fetchone()[0]
        limit = min(MAX_STORE_BYTES // PAGE, pages + amount // PAGE)
        self.db.execute(f"PRAGMA max_page_count={limit}")

    def _records(self, ledger: NativeStudyLedger, start: int) -> None:
        self.db.executemany(
            "INSERT INTO records VALUES (?,?,?)",
            [(r.sequence, r.event_id, message_sha256(r)) for r in ledger.records[start:]],
        )

    def ledger(self) -> NativeStudyLedger:
        row = self.db.execute(
            "SELECT length(ledger),revision,head FROM state WHERE id=1"
        ).fetchone()
        if row is None or not 0 < row[0] <= MAX_STUDY_JSON_BYTES:
            raise StudyLedgerError("store_corrupt")
        data = self.db.execute("SELECT ledger FROM state WHERE id=1").fetchone()[0]
        ledger = read_study_ledger(data)
        if (len(ledger.records), head(ledger)) != tuple(row[1:]):
            raise StudyLedgerError("store_corrupt")
        rows = self.db.execute(
            "SELECT sequence,event_id,digest FROM records ORDER BY sequence"
        ).fetchall()
        if rows != [(r.sequence, r.event_id, message_sha256(r)) for r in ledger.records]:
            raise StudyLedgerError("store_corrupt")
        return ledger

    def replace(self, before: NativeStudyLedger, after: NativeStudyLedger) -> None:
        if after.records[: len(before.records)] != before.records:
            raise StudyLedgerError("store_prefix")
        changed = self.db.execute(
            "UPDATE state SET ledger=?,revision=?,head=? WHERE id=1 AND revision=? AND head=?",
            (raw(after), len(after.records), head(after), len(before.records), head(before)),
        ).rowcount
        if changed != 1:
            raise StudyLedgerError("store_cas")
        self._records(after, len(before.records))
        self.meter.sample()

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


def read_admission(root: Path) -> tuple[PublicationAdmission, bytes, NativeStudyLedger]:
    admission = parse_bounded_json(
        read_bytes(root / "admission.json", limit=16 * 1024),
        PublicationAdmission,
        max_bytes=16 * 1024,
        max_depth=8,
        max_nodes=128,
    )
    seed = read_bytes(root / "seed-ledger.json", limit=MAX_STUDY_JSON_BYTES)
    if digest(seed) != admission.seed_ledger_sha256:
        raise StudyLedgerError("admission_identity")
    ledger = read_study_ledger(seed)
    return admission, seed, ledger
