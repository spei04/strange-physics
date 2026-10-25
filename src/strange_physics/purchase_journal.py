"""Fixed bounded Journal I/O for the forthcoming measured purchase producer.

This module grants no ledger authority, creates no receipt and settles no cost.
Its caller must durably retain the complete allowance before reserving a budget.
"""

from __future__ import annotations

import hashlib
import math
import os
import resource
import signal
import socket
import sqlite3
import struct
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from strange_physics.workflow_io import private_stat, read_bytes, safe_path

JOURNAL_BYTES = 128 * 1024
JOURNAL_EPOCHS = 15
WRITER_EPOCHS = 14
HOLDER_CPU_SECONDS = 2
_MAX_FRAME = JOURNAL_BYTES + 1
_MAGIC = bytes.fromhex("d9d505f920a163d7")


class JournalBoundError(RuntimeError):
    """Bounded diagnostic code, never private record contents."""


def _remaining(deadline_ns: int) -> float:
    remaining = (deadline_ns - time.monotonic_ns()) / 1e9
    if remaining <= 0:
        raise JournalBoundError("journal_deadline")
    return remaining


def _effective_deadline(deadline_ns: int) -> int:
    # POSIX timers do not survive fork. Capture the parent's stricter timer
    # before forking; child startup/scheduling time consumes this same bound.
    inherited = signal.getitimer(signal.ITIMER_REAL)[0]
    if inherited > 0:
        return min(deadline_ns, time.monotonic_ns() + int(inherited * 1e9))
    return deadline_ns


def _lower_limit(kind: int, ceiling: int) -> None:
    soft, hard = resource.getrlimit(kind)
    values = [ceiling, *(v for v in (soft, hard) if v != resource.RLIM_INFINITY)]
    resource.setrlimit(kind, (min(values), hard))


def _child_limits(parent_pid: int, deadline_ns: int, cpu_seconds: int) -> None:
    if os.getpid() == parent_pid or not 1 <= cpu_seconds <= 120:
        raise JournalBoundError("journal_child_only")
    remaining = _remaining(deadline_ns)
    inherited = signal.getitimer(signal.ITIMER_REAL)[0]
    if inherited > 0:
        remaining = min(remaining, inherited)
    # Set the deadline before any filesystem work, and retain stricter limits.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    _lower_limit(resource.RLIMIT_FSIZE, JOURNAL_BYTES)
    _lower_limit(resource.RLIMIT_CPU, cpu_seconds)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
    signal.signal(signal.SIGXCPU, signal.SIG_DFL)


@dataclass
class JournalEpochs:
    """One parent-owned, single-use 14+1 partition of a prepaid 15-epoch ticket."""

    parent_pid: int = field(default_factory=os.getpid, init=False)
    used: int = field(default=0, init=False)
    _writer_reserved: bool = field(default=False, init=False)
    _holder_reserved: bool = field(default=False, init=False)
    holder_pid: int | None = field(default=None, init=False)
    holder_status: int | None = field(default=None, init=False)
    holder_cpu_ns: int | None = field(default=None, init=False)

    def writer(self, deadline_ns: int) -> JournalWriteBudget:
        if os.getpid() != self.parent_pid or self._writer_reserved:
            raise JournalBoundError("journal_writer_reused")
        deadline_ns = _effective_deadline(deadline_ns)
        _remaining(deadline_ns)
        self._writer_reserved = True
        self.used += WRITER_EPOCHS
        read_fd, write_fd = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            os.write(write_fd, b"W")
        finally:
            os.close(write_fd)
        return JournalWriteBudget(self.parent_pid, deadline_ns, read_fd)

    def holder(self) -> None:
        if os.getpid() != self.parent_pid or self._holder_reserved:
            raise JournalBoundError("journal_holder_reused")
        self._holder_reserved = True
        self.used += 1
        if self.used > JOURNAL_EPOCHS:
            raise JournalBoundError("journal_epochs")


_WRITER_LABELS = frozenset(
    {
        "open",
        "page_size",
        "max_page_count",
        "journal_mode",
        "initialize",
        "reserve",
        "commit",
        "failure",
        *(f"schema-{i}" for i in range(6)),
    }
)


@dataclass
class JournalWriteBudget:
    """Fixed writer sub-budget; install inside exactly one forked child."""

    parent_pid: int
    deadline_ns: int
    _token_fd: int = field(repr=False)
    used: set[str] = field(default_factory=set, init=False)
    child_pid: int | None = field(default=None, init=False)

    def install(self, *, cpu_seconds: int) -> None:
        if self.child_pid is not None:
            raise JournalBoundError("journal_limits_reused")
        if os.getpid() == self.parent_pid:
            raise JournalBoundError("journal_child_only")
        # Fork copies Python state, not this kernel pipe's one-use token.
        if os.read(self._token_fd, 1) != b"W":
            raise JournalBoundError("journal_writer_reused")
        self.close()
        _child_limits(self.parent_pid, self.deadline_ns, cpu_seconds)
        self.child_pid = os.getpid()

    def close(self) -> None:
        """Parent closes its token fd after forking; it never changes limits."""
        if self._token_fd >= 0:
            os.close(self._token_fd)
            self._token_fd = -1

    def claim(self, operation: str) -> None:
        if self.child_pid != os.getpid() or os.getpid() == self.parent_pid:
            raise JournalBoundError("journal_child_only")
        _remaining(self.deadline_ns)
        soft, _ = resource.getrlimit(resource.RLIMIT_FSIZE)
        if soft == resource.RLIM_INFINITY or soft > JOURNAL_BYTES:
            raise JournalBoundError("journal_file_limit")
        if operation not in _WRITER_LABELS or operation in self.used:
            raise JournalBoundError("journal_epoch_reused")
        self.used.add(operation)


def _info(path: Path, *, missing: bool = False) -> os.stat_result | None:
    try:
        value = path.lstat()
    except FileNotFoundError:
        if missing:
            return None
        raise
    private_stat(value)
    if value.st_nlink != 1 or value.st_size > JOURNAL_BYTES:
        raise JournalBoundError("journal_file_limit")
    return value


def check_files(path: Path, *, create: bool = False) -> Path:
    path = safe_path(path)
    private_stat(path.parent.stat(), directory=True)
    info = _info(path, missing=create)
    if create and info is not None:
        raise FileExistsError(path)
    if info is not None:
        header = read_bytes(path, limit=JOURNAL_BYTES)
        if (
            len(header) < 100
            or header[:16] != b"SQLite format 3\0"
            or int.from_bytes(header[16:18], "big") != 4096
            or header[18:20] != b"\1\1"
            or int.from_bytes(header[28:32], "big") > 32
        ):
            raise JournalBoundError("journal_profile")
    for suffix in ("-wal", "-shm"):
        if Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink():
            raise JournalBoundError("journal_profile")
    sidecar = Path(str(path) + "-journal")
    if _info(sidecar, missing=True) is not None:
        data = read_bytes(sidecar, limit=JOURNAL_BYTES)
        if create or len(data) < 28 or data[:8] != _MAGIC:
            raise JournalBoundError("journal_hot_header")
        pages = int.from_bytes(data[16:20], "big")
        sector = int.from_bytes(data[20:24], "big")
        size = int.from_bytes(data[24:28], "big")
        if pages > 32 or size != 4096 or not 512 <= sector <= 65536 or sector & (sector - 1):
            raise JournalBoundError("journal_hot_header")
    return path


def configure_writer(db: sqlite3.Connection, budget: JournalWriteBudget) -> None:
    for name, value in (("page_size", 4096), ("max_page_count", 32), ("journal_mode", "DELETE")):
        budget.claim(name)
        db.execute(f"PRAGMA {name}={value}")
    db.execute("PRAGMA cache_spill=OFF")
    db.execute("PRAGMA synchronous=FULL")
    check_profile(db)


def check_profile(db: sqlite3.Connection) -> None:
    expected = {
        "page_size": 4096,
        "max_page_count": 32,
        "journal_mode": "delete",
        "cache_spill": 0,
        "synchronous": 2,
        "auto_vacuum": 0,
    }
    for name, wanted in expected.items():
        if db.execute(f"PRAGMA {name}").fetchone()[0] != wanted:
            raise JournalBoundError("journal_profile")
    if db.execute("PRAGMA page_count").fetchone()[0] > 32:
        raise JournalBoundError("journal_profile")


def _raw(fd: int, path: Path) -> bytes:
    before = os.fstat(fd)
    private_stat(before)
    current = _info(path)
    if current is None or (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
        raise JournalBoundError("journal_replaced")
    data = os.pread(fd, JOURNAL_BYTES + 1, 0)
    after = os.fstat(fd)
    if (
        len(data) > JOURNAL_BYTES
        or len(data) != before.st_size
        or before.st_nlink != 1
        or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    ):
        raise JournalBoundError("journal_changed")
    return data


def _send(channel: socket.socket, data: bytes, deadline_ns: int) -> None:
    if not 0 < len(data) <= _MAX_FRAME:
        raise JournalBoundError("journal_frame")
    channel.settimeout(_remaining(deadline_ns))
    channel.sendall(struct.pack("!I", len(data)) + data)


def _receive(channel: socket.socket, deadline_ns: int) -> bytes:
    def exact(length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            channel.settimeout(_remaining(deadline_ns))
            chunk = channel.recv(length - len(chunks))
            if not chunk:
                raise JournalBoundError("journal_eof")
            chunks.extend(chunk)
        return bytes(chunks)

    length = struct.unpack("!I", exact(4))[0]
    if not 0 < length <= _MAX_FRAME:
        raise JournalBoundError("journal_frame")
    return exact(length)


def _holder(
    channel: socket.socket, path: Path, expected: str, parent_pid: int, deadline_ns: int
) -> None:
    # No live Journal fd is opened in the parent. Even raced hot recovery is
    # subject to this child's kernel cap before sqlite first touches the file.
    _child_limits(parent_pid, deadline_ns, HOLDER_CPU_SECONDS)
    path = check_files(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    db: sqlite3.Connection | None = None
    try:
        before = _raw(fd, path)
        db = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=0, isolation_level=None)
        db.execute("BEGIN IMMEDIATE")
        # Connection-only controls do not create new Journal write epochs.
        db.execute("PRAGMA cache_spill=OFF")
        # synchronous is readback-only while the lock is held; changing it in
        # a transaction is forbidden by SQLite.
        # max_page_count is connection state. Read page size/count without a
        # setter here: the kernel cap already limits every possible recovery.
        for name, wanted in (
            ("page_size", 4096),
            ("journal_mode", "delete"),
            ("auto_vacuum", 0),
            ("cache_spill", 0),
            ("synchronous", 2),
            ("application_id", 0x53504859),
            ("user_version", 1),
        ):
            if db.execute(f"PRAGMA {name}").fetchone()[0] != wanted:
                raise JournalBoundError("journal_profile")
        original = _raw(fd, path)
        if before != original or hashlib.sha256(original).hexdigest() != expected:
            raise JournalBoundError("journal_identity")

        def recheck() -> None:
            if _raw(fd, path) != original:
                raise JournalBoundError("journal_changed")
            if any(
                Path(str(path) + s).exists() or Path(str(path) + s).is_symlink()
                for s in ("-journal", "-wal", "-shm")
            ):
                raise JournalBoundError("journal_sidecar")

        recheck()
        _send(channel, b"D" + original, deadline_ns)
        while True:
            command = _receive(channel, deadline_ns)
            if command == b"C":
                recheck()
                _send(channel, b"OK", deadline_ns)
            elif command in (b"S", b"F"):
                if command == b"S":
                    recheck()
                # Acknowledge the caller's COMMIT/rollback while still locked.
                _send(channel, b"OK", deadline_ns)
                return
            else:
                raise JournalBoundError("journal_command")
    finally:
        # Raw close must come AFTER SQLite lock release, including failures.
        if db is not None:
            try:
                if db.in_transaction:
                    db.rollback()
            finally:
                db.close()
        os.close(fd)


@dataclass
class JournalCapture:
    raw: bytes
    sha256: str
    pid: int
    _channel: socket.socket = field(repr=False)
    deadline_ns: int
    holder_cpu_ns: int | None = None
    holder_status: int | None = None

    def recheck(self) -> None:
        _send(self._channel, b"C", self.deadline_ns)
        if _receive(self._channel, self.deadline_ns) != b"OK":
            raise JournalBoundError("journal_protocol")


@contextmanager
def capture_journal(
    path: Path, expected_sha256: str, *, epochs: JournalEpochs, deadline_ns: int
) -> Iterator[JournalCapture]:
    """Hold live exclusion through caller closure; no receipt/cost authority.

    The caller rechecks immediately before COMMIT and exits only after COMMIT
    or rollback. A lost acknowledgement remains a failure, never a free retry.
    """
    epochs.holder()  # Spent even if validation, fork, IPC or cleanup fails.
    deadline_ns = _effective_deadline(deadline_ns)
    _remaining(deadline_ns)
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise JournalBoundError("journal_identity")
    parent, child = socket.socketpair()
    parent_pid = os.getpid()
    try:
        pid = os.fork()
    except BaseException:
        parent.close()
        child.close()
        raise
    if pid == 0:
        code = 70
        try:
            parent.close()
            _holder(child, path, expected_sha256, parent_pid, deadline_ns)
            code = 0
        except BaseException:
            code = 70
        finally:
            try:
                child.close()
            finally:
                os._exit(code)
    epochs.holder_pid = pid
    capture: JournalCapture | None = None
    failure: BaseException | None = None
    graceful = False
    try:
        child.close()
        payload = _receive(parent, deadline_ns)
        if payload[:1] != b"D" or hashlib.sha256(payload[1:]).hexdigest() != expected_sha256:
            raise JournalBoundError("journal_identity")
        capture = JournalCapture(payload[1:], expected_sha256, pid, parent, deadline_ns)
        yield capture
        capture.recheck()
        _send(parent, b"S", deadline_ns)
        if _receive(parent, deadline_ns) != b"OK":
            raise JournalBoundError("journal_protocol")
        graceful = True
    except BaseException as error:
        failure = error
        # Best effort rollback acknowledgement under the SAME deadline.
        try:
            _send(parent, b"F", deadline_ns)
            graceful = _receive(parent, deadline_ns) == b"OK"
        except BaseException:
            pass
        raise
    finally:
        cleanup_errors: list[BaseException] = []
        for endpoint in (parent, child):
            try:
                endpoint.close()
            except BaseException as error:
                cleanup_errors.append(error)

        def kill() -> None:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as error:
                cleanup_errors.append(error)

        if not graceful or cleanup_errors:
            kill()
        status: int | None = None
        usage: resource.struct_rusage | None = None
        try:
            _, status, usage = os.wait4(pid, 0)
        except ChildProcessError as error:
            # Already reaped/unknown ownership: never signal a possibly reused
            # PID and never invent its exit status or usage.
            cleanup_errors.append(error)
        except BaseException as error:
            cleanup_errors.append(error)
            # An ambiguous failed wait may already have reaped this child.
            # Never signal that PID again; the fixed child still obeys its
            # original absolute deadline if it remains alive.
            try:
                _, status, usage = os.wait4(pid, 0)
            except BaseException as second_error:
                cleanup_errors.append(second_error)
        epochs.holder_status = status
        if usage is not None:
            epochs.holder_cpu_ns = math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
        if capture is not None:
            capture.holder_status = status
            capture.holder_cpu_ns = epochs.holder_cpu_ns
        bad_status = status is None or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0
        if cleanup_errors or bad_status:
            if failure is not None:
                failure.add_note(
                    "Journal holder cleanup/status failed; known observations are retained "
                    "and unavailable observations remain unknown under the prepaid allowance."
                )
            elif cleanup_errors:
                raise JournalBoundError("journal_cleanup_unknown") from cleanup_errors[0]
            else:
                raise JournalBoundError("journal_holder_failed")
