"""Exclusive bounded retention of recorder bytes; no execution or authenticity proof."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path
from typing import Literal

from strange_physics.workflow_io import private_stat, safe_path

CONTEXT_BYTES = 4096
TERMINAL_BYTES = 16384
METADATA_BYTES = CONTEXT_BYTES + TERMINAL_BYTES
EVENT_BYTES = 4096
SHARD_BYTES = 4 * 1024**2
MAX_SHARDS = 16
MAX_BYTES = 64 * 1024**2
MAX_CALLS = 55_100
MAX_FAULTS = 16
SCHEMA = "strange-physics.d1-primitive-sink.v1"
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z")
_SHARD = re.compile(r"events-(0[0-9]|1[0-5])\.jsonl\Z")
type Identity = tuple[int, int, int, int]


@dataclass(frozen=True)
class SinkContext:
    recorder_id: str
    run_id: str
    source_commit: str
    source_tree: str
    protocol_sha256: str
    source_manifest_sha256: str
    recorder_sha256: str
    sink_sha256: str
    max_calls: int
    max_bytes: int

    @property
    def max_events(self) -> int:
        return 2 * self.max_calls + 1

    @property
    def event_capacity(self) -> int:
        return self.max_bytes - METADATA_BYTES


def _context_bytes(value: SinkContext) -> bytes:
    if type(value) is not SinkContext:
        raise ValueError("Exact sink context required")
    for name in ("recorder_id", "run_id"):
        text = getattr(value, name)
        if type(text) is not str or _TOKEN.fullmatch(text) is None:
            raise ValueError("Bounded opaque sink identity required")
    for name, size in (
        ("source_commit", 40),
        ("source_tree", 40),
        ("protocol_sha256", 64),
        ("source_manifest_sha256", 64),
        ("recorder_sha256", 64),
        ("sink_sha256", 64),
    ):
        text = getattr(value, name)
        if type(text) is not str or re.fullmatch("[0-9a-f]{" + str(size) + "}", text) is None:
            raise ValueError("Exact source identity required")
    if type(value.max_calls) is not int or not 1 <= value.max_calls <= MAX_CALLS:
        raise ValueError("Explicit recorder call ceiling required")
    if type(value.max_bytes) is not int or not METADATA_BYTES < value.max_bytes <= MAX_BYTES:
        raise ValueError("Total byte ceiling must include both metadata reservations")
    fields = asdict(value) | {
        "schema": SCHEMA,
        "max_events": value.max_events,
        "event_capacity": value.event_capacity,
        "event_bytes": EVENT_BYTES,
        "shard_bytes": SHARD_BYTES,
        "max_shards": MAX_SHARDS,
        "context_bytes": CONTEXT_BYTES,
        "terminal_bytes": TERMINAL_BYTES,
    }
    return _encode(fields, CONTEXT_BYTES)


def _encode(value: object, limit: int) -> bytes:
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")
    if len(raw) > limit:
        raise ValueError("Bounded sink metadata exceeded")
    return raw


def _identity(info: os.stat_result) -> Identity:
    return info.st_dev, info.st_ino, info.st_uid, info.st_mode


class SinkStopped(ValueError):
    pass


@dataclass(frozen=True)
class SinkFault:
    phase: str
    exception_type: str
    exception_type_complete: bool


@dataclass(frozen=True)
class SinkSnapshot:
    reserved_events: int
    confirmed_events: int
    reserved_bytes: int
    confirmed_bytes: int
    written_bytes: int
    stopped: bool
    finish_consumed: bool
    faults: tuple[SinkFault, ...]
    unretained_fault_count: int


@dataclass(frozen=True)
class ShardObservation:
    name: str
    bytes: int
    sha256: str
    complete_lines: int
    trailing_fragment_bytes: int


@dataclass(frozen=True)
class SinkCloseout:
    snapshot: SinkSnapshot
    terminal_acknowledged: bool
    descriptors_closed: bool
    terminal_sha256: str | None


@dataclass(frozen=True, slots=True)
class ContextObservation:
    raw: bytes
    sha256: str
    byte_length: int


@dataclass(frozen=True)
class SinkInspection:
    context_sha256: str | None
    context_canonical: bool
    terminal_sha256: str | None
    terminal_state: Literal["missing", "present-unconfirmed"]
    shards: tuple[ShardObservation, ...]
    actual_bytes: int
    acknowledgement: Literal["not-inferred"] = "not-inferred"
    execution: Literal["not-inferred"] = "not-inferred"
    authenticity: Literal["unchecked"] = "unchecked"


class _Anchor:
    """Pin parent/root descriptors; a private single writer remains a premise."""

    def __init__(
        self, root: Path, *, create: bool, expected_parent: Identity | None = None
    ) -> None:
        if not isinstance(root, Path):
            raise ValueError("Path required")
        if not root.is_absolute() or ".." in root.parts or root.name in ("", "."):
            raise ValueError("Normalized absolute root required")
        safe_path(root)
        self.path = root
        self.closure_uncertain = False
        self.close_faults: list[BaseException] = []
        self.parent: int | None = None
        self.directory: int | None = None
        try:
            self.parent = os.open(
                root.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
            parent = os.fstat(self.parent)
            private_stat(parent, directory=True)
            self.parent_identity = _identity(parent)
            if expected_parent is not None and self.parent_identity != expected_parent:
                raise ValueError("Actual parent differs from the required pinned parent")
            if create:
                os.mkdir(root.name, mode=0o700, dir_fd=self.parent)
                os.fsync(self.parent)
            self.directory = os.open(
                root.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=self.parent,
            )
            directory = os.fstat(self.directory)
            private_stat(directory, directory=True)
            if directory.st_mode & 0o777 != 0o700:
                raise ValueError("Exact private root mode required")
            self.root_identity = _identity(directory)
            self.check()
        except BaseException as primary:
            for error in self.close():
                primary.add_note("Supplemental anchor close failure: " + type(error).__name__[:96])
            raise

    def check(self) -> None:
        if self.parent is None or self.directory is None:
            raise SinkStopped("Root descriptors are closed")
        parent, root = os.fstat(self.parent), os.fstat(self.directory)
        private_stat(parent, directory=True)
        private_stat(root, directory=True)
        if (
            _identity(parent) != self.parent_identity
            or _identity(root) != self.root_identity
            or _identity(os.stat(self.path.parent, follow_symlinks=False)) != self.parent_identity
            or _identity(os.stat(self.path.name, dir_fd=self.parent, follow_symlinks=False))
            != self.root_identity
        ):
            raise ValueError("Pinned directory identity changed")

    def open_file(self, name: str, *, create: bool) -> tuple[int, Identity]:
        self.check()
        flags = os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
        flags |= os.O_WRONLY | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY
        fd = os.open(name, flags, 0o600, dir_fd=self.directory)
        try:
            info = os.fstat(fd)
            private_stat(info)
            if info.st_nlink != 1 or info.st_mode & 0o777 != 0o600:
                raise ValueError("Exclusive private single-link file required")
            identity = _identity(info)
            self.file_check(name, fd, identity, info.st_size)
            return fd, identity
        except BaseException as primary:
            try:
                os.close(fd)
            except BaseException as supplemental:
                self.closure_uncertain = True
                self.close_faults.append(supplemental)
                primary.add_note(
                    "Supplemental file close failure: " + type(supplemental).__name__[:96]
                )
            raise

    def file_check(self, name: str, fd: int, identity: Identity, size: int) -> None:
        self.check()
        info = os.fstat(fd)
        named = os.stat(name, dir_fd=self.directory, follow_symlinks=False)
        private_stat(info)
        if (
            _identity(info) != identity
            or _identity(named) != identity
            or info.st_nlink != 1
            or named.st_nlink != 1
            or info.st_size != size
            or named.st_size != size
        ):
            raise ValueError("Pinned file identity or extent changed")

    def sync(self) -> None:
        self.check()
        assert self.directory is not None
        os.fsync(self.directory)
        self.check()

    def close(self) -> list[BaseException]:
        errors: list[BaseException] = []
        for name in ("directory", "parent"):
            fd = getattr(self, name)
            setattr(self, name, None)  # Never retry an ambiguously closed descriptor.
            if fd is not None:
                try:
                    os.close(fd)
                except BaseException as error:
                    self.closure_uncertain = True
                    errors.append(error)
        return errors


def _write_remaining(fd: int, raw: bytes, progress: list[int], check: Callable[[], None]) -> None:
    offset = 0
    for _ in range(len(raw)):
        check()
        count = os.write(fd, memoryview(raw)[offset:])
        if type(count) is not int or not 1 <= count <= len(raw) - offset:
            raise OSError("No valid private-write progress")
        offset += count
        progress[0] += count
        check()
        if offset == len(raw):
            return
    raise OSError("Private write exceeded its positive-progress bound")


def _read_file(anchor: _Anchor, name: str, limit: int) -> bytes:
    fd, identity = anchor.open_file(name, create=False)
    primary: BaseException | None = None
    try:
        before = os.fstat(fd)
        if before.st_size > limit:
            raise ValueError("File exceeds declared read bound")
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            raw = os.read(fd, min(65536, remaining))
            if not raw:
                raise ValueError("File shortened while reading")
            chunks.append(raw)
            remaining -= len(raw)
        anchor.file_check(name, fd, identity, before.st_size)
        after = os.fstat(fd)
        if (before.st_mtime_ns, before.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("File changed while reading")
        return b"".join(chunks)
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            os.close(fd)
        except BaseException as close_error:
            anchor.closure_uncertain = True
            anchor.close_faults.append(close_error)
            if primary is None:
                raise
            primary.add_note("Supplemental read descriptor close failure")


def _observe(name: str, raw: bytes) -> ShardObservation:
    offset = lines = 0
    while True:
        newline = raw.find(b"\n", offset)
        if newline < 0:
            break
        if newline + 1 - offset > EVENT_BYTES or lines >= 2 * MAX_CALLS + 1:
            raise ValueError("Observed line count or extent exceeds recorder bounds")
        lines += 1
        offset = newline + 1
    if len(raw) - offset >= EVENT_BYTES:
        raise ValueError("Observed fragment exceeds event bound")
    return ShardObservation(
        name, len(raw), hashlib.sha256(raw).hexdigest(), lines, len(raw) - offset
    )


def _canonical_context(raw: bytes) -> bool:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate metadata key")
            result[key] = value
        return result

    try:
        data = json.loads(raw, object_pairs_hook=pairs)
        if type(data) is not dict:
            return False
        names = tuple(SinkContext.__dataclass_fields__)
        # Construction itself does not coerce values; _context_bytes checks raw types.
        context = SinkContext(**{name: data[name] for name in names})
        return _context_bytes(context) == raw
    except (KeyError, TypeError, ValueError, RecursionError):
        return False


def inspect_sink(root: Path, *, max_bytes: int) -> SinkInspection:
    """Raw presence only. Never resumes, repairs, acknowledges or authenticates."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError("Explicit bounded inspection allowance required")
    anchor = _Anchor(root, create=False)
    primary: BaseException | None = None
    try:
        assert anchor.directory is not None
        with os.scandir(anchor.directory) as entries:
            names = sorted(entry.name for entry in islice(entries, MAX_SHARDS + 3))
        if len(names) > MAX_SHARDS + 2 or any(
            name not in ("context.json", "terminal.json") and _SHARD.fullmatch(name) is None
            for name in names
        ):
            raise ValueError("Unexpected or excessive sink files")
        shard_names = [name for name in names if _SHARD.fullmatch(name)]
        if shard_names != [f"events-{i:02}.jsonl" for i in range(len(shard_names))]:
            raise ValueError("Missing or substituted shard")
        actual = 0
        context_raw: bytes | None = None
        terminal_raw: bytes | None = None
        shards: list[ShardObservation] = []
        for name in names:
            limit = (
                CONTEXT_BYTES
                if name == "context.json"
                else TERMINAL_BYTES
                if name == "terminal.json"
                else SHARD_BYTES
            )
            raw = _read_file(anchor, name, min(limit, max_bytes - actual))
            actual += len(raw)
            if name == "context.json":
                context_raw = raw
            elif name == "terminal.json":
                terminal_raw = raw
            else:
                shards.append(_observe(name, raw))
                if sum(row.complete_lines for row in shards) > 2 * MAX_CALLS + 1:
                    raise ValueError("Observed total line count exceeds recorder bound")
        return SinkInspection(
            hashlib.sha256(context_raw).hexdigest() if context_raw is not None else None,
            context_raw is not None and _canonical_context(context_raw),
            hashlib.sha256(terminal_raw).hexdigest() if terminal_raw is not None else None,
            "present-unconfirmed" if terminal_raw is not None else "missing",
            tuple(shards),
            actual,
        )
    except BaseException as error:
        primary = error
        raise
    finally:
        errors = anchor.close()
        if errors:
            if primary is None:
                raise errors[0]
            primary.add_note("Supplemental inspection anchor close failure")


class PrimitiveFileSink:
    """One process/thread, one exclusive directory, no append recovery or retry."""

    context: SinkContext
    first_exception: BaseException | None
    _context_raw: bytes
    _pid: int
    _thread: int
    _busy: bool
    _stopped: bool
    _finished: bool
    _invalid_owner: bool
    _faults: list[SinkFault]
    _unretained_faults: int
    _reserved_events: int
    _confirmed_events: int
    _reserved_bytes: int
    _confirmed_bytes: int
    _written_bytes: int
    _fd: int | None
    _file_identity: Identity | None
    _file_size: int
    _names: list[str]
    _anchor: _Anchor
    _close_fault_count: int
    _event_capacity: int
    _max_events: int

    def __init__(self) -> None:
        raise TypeError("Use exclusive PrimitiveFileSink.create")

    @classmethod
    def create(cls, root: Path, context: SinkContext) -> PrimitiveFileSink:
        raw = _context_bytes(context)
        value = cls.__new__(cls)
        value.context = context
        value._context_raw = raw
        value._event_capacity = context.event_capacity
        value._max_events = context.max_events
        value._close_fault_count = 0
        value._invalid_owner = False
        value._pid, value._thread = os.getpid(), threading.get_ident()
        value._busy = value._stopped = value._finished = False
        value._faults = []
        value._unretained_faults = 0
        value.first_exception = None
        value._reserved_events = value._confirmed_events = 0
        value._reserved_bytes = value._confirmed_bytes = value._written_bytes = 0
        value._fd = None
        value._file_identity = None
        value._file_size = 0
        value._names = []
        value._anchor = _Anchor(root, create=True)
        try:
            value._metadata("context.json", raw)
        except BaseException as primary:
            value._remember("context", primary)
            for error in value._anchor.close():
                primary.add_note(
                    "Supplemental create anchor close failure: " + type(error).__name__[:96]
                )
            raise
        return value

    def snapshot(self) -> SinkSnapshot:
        return SinkSnapshot(
            self._reserved_events,
            self._confirmed_events,
            self._reserved_bytes,
            self._confirmed_bytes,
            self._written_bytes,
            self._stopped,
            self._finished,
            tuple(self._faults),
            self._unretained_faults,
        )

    def _remember(self, phase: str, error: BaseException) -> None:
        self._stopped = True
        if self.first_exception is None:
            self.first_exception = error
        name = type(error).__module__ + "." + type(error).__qualname__
        if len(self._faults) < MAX_FAULTS:
            self._faults.append(SinkFault(phase, name[:192], len(name) <= 192))
        else:
            self._unretained_faults += 1

    def _drain_close_faults(self) -> None:
        for error in self._anchor.close_faults[self._close_fault_count :]:
            self._remember("descriptor_close", error)
        self._close_fault_count = len(self._anchor.close_faults)

    def _enter(self, *, finishing: bool) -> None:
        if os.getpid() != self._pid or threading.get_ident() != self._thread or self._busy:
            self._invalid_owner = True
            error = SinkStopped("Wrong owner or reentrant sink operation")
            self._remember("ownership_or_reentry", error)
            raise error
        if self._finished or (self._stopped and not finishing):
            raise SinkStopped("The sink opportunity is consumed")
        if not finishing:
            try:
                if _context_bytes(self.context) != self._context_raw:
                    raise ValueError("Sink context changed")
            except BaseException as error:
                self._remember("context_changed", error)
                raise
        self._busy = True
        if finishing:
            self._finished = True  # Before any cleanup or terminal I/O.

    def _check_reentry(self) -> None:
        if self._invalid_owner:
            assert self.first_exception is not None
            raise self.first_exception

    def _check_active(self) -> None:
        if self._stopped:
            assert self.first_exception is not None
            raise self.first_exception

    def _metadata(self, name: str, raw: bytes) -> None:
        fd, identity = self._anchor.open_file(name, create=True)
        primary: BaseException | None = None
        try:
            _write_remaining(fd, raw, [0], self._check_reentry)
            self._anchor.file_check(name, fd, identity, len(raw))
            os.fsync(fd)
            self._anchor.sync()
            self._anchor.file_check(name, fd, identity, len(raw))
            self._check_reentry()
        except BaseException as error:
            primary = error
            self._remember("metadata_write", error)
            raise
        finally:
            try:
                os.close(fd)
            except BaseException as error:
                self._anchor.closure_uncertain = True
                self._remember("metadata_close", error)
                if primary is None:
                    raise
                primary.add_note("Supplemental metadata close failure")

    def _close_active(self) -> None:
        fd, self._fd = self._fd, None
        if fd is not None:
            try:
                os.close(fd)
            except BaseException:
                self._anchor.closure_uncertain = True
                raise

    def observe_context(self) -> ContextObservation:
        """Read current canonical C while idle; never authenticates or transfers ownership."""
        self._enter(finishing=False)
        try:
            if self._reserved_events != 0:
                raise SinkStopped("Context observation requires zero reserved events")
            self._drain_close_faults()
            self._check_active()
            if self._anchor.closure_uncertain:
                raise SinkStopped("Prior descriptor closure is uncertain")
            raw = _read_file(self._anchor, "context.json", CONTEXT_BYTES)
            if raw != self._context_raw:
                raise ValueError("Actual context bytes changed")
            self._drain_close_faults()
            if self._anchor.closure_uncertain:
                raise SinkStopped("Context read descriptor closure is uncertain")
            observation = ContextObservation(raw, hashlib.sha256(raw).hexdigest(), len(raw))
            self._check_reentry()
            self._check_active()
            return observation
        except BaseException as observation_error:
            # Keep a read/validation failure ahead of its supplemental close failure.
            if self.first_exception is not observation_error:
                self._remember("context_observation", observation_error)
            self._drain_close_faults()
            raise
        finally:
            self._busy = False

    def append(self, raw: bytes) -> None:
        self._enter(finishing=False)
        progress = [0]
        phase = "append_preflight"
        try:
            if (
                type(raw) is not bytes
                or not 1 <= len(raw) <= EVENT_BYTES
                or not raw.endswith(b"\n")
                or raw.count(b"\n") != 1
            ):
                raise ValueError("One exact bounded recorder line required")
            if (
                self._reserved_events >= self._max_events
                or self._reserved_bytes + len(raw) > self._event_capacity
            ):
                raise ValueError("Sink event allowance exhausted")
            self._reserved_events += 1
            self._reserved_bytes += len(raw)  # Full reservation remains after unknown delivery.
            self._anchor.check()
            if self._fd is None or self._file_size + len(raw) > SHARD_BYTES:
                phase = "shard_close"
                self._close_active()
                if len(self._names) >= MAX_SHARDS:
                    raise ValueError("Shard allowance exhausted")
                name = f"events-{len(self._names):02}.jsonl"
                phase = "shard_create"
                self._names.append(name)
                self._file_size = 0
                self._fd, self._file_identity = self._anchor.open_file(name, create=True)
                os.fsync(self._fd)
                self._anchor.sync()
            assert self._fd is not None and self._file_identity is not None
            self._anchor.file_check(self._names[-1], self._fd, self._file_identity, self._file_size)
            phase = "append_write"
            _write_remaining(self._fd, raw, progress, self._check_active)
            self._file_size += progress[0]
            self._written_bytes += progress[0]
            progress[0] = 0
            self._check_active()
            self._anchor.file_check(self._names[-1], self._fd, self._file_identity, self._file_size)
            phase = "append_fsync"
            os.fsync(self._fd)
            self._anchor.file_check(self._names[-1], self._fd, self._file_identity, self._file_size)
            self._check_active()
            self._confirmed_events += 1
            self._confirmed_bytes += len(raw)
        except BaseException as error:
            self._file_size += progress[0]
            self._written_bytes += progress[0]
            if self.first_exception is not error:
                self._remember(phase, error)
            self._drain_close_faults()
            raise
        finally:
            self._busy = False

    def finish(self) -> SinkCloseout:
        self._enter(finishing=True)
        terminal_hash: str | None = None
        acknowledged = False
        closed = True
        try:
            try:
                self._close_active()
            except BaseException as error:
                closed = False
                self._remember("data_close", error)
            shards: list[dict[str, object]] = []
            for name in self._names:
                try:
                    observation = _observe(name, _read_file(self._anchor, name, SHARD_BYTES))
                    shards.append(asdict(observation))
                except BaseException as error:
                    self._remember("shard_readback", error)
                    shards.append({"name": name, "observation": "unavailable"})
                self._drain_close_faults()
            try:
                raw = _encode(
                    {
                        "schema": SCHEMA,
                        "state": "pending_external_confirmation",
                        "context_sha256": hashlib.sha256(self._context_raw).hexdigest(),
                        "snapshot_before_terminal": asdict(self.snapshot()),
                        "shards": shards,
                    },
                    TERMINAL_BYTES,
                )
                terminal_hash = hashlib.sha256(raw).hexdigest()
                self._metadata("terminal.json", raw)
                acknowledged = True
            except BaseException as error:
                self._remember("terminal", error)
                self._drain_close_faults()
        finally:
            errors = self._anchor.close()
            closed = closed and not errors and not self._anchor.closure_uncertain
            for close_error in errors:
                self._remember("anchor_close", close_error)
            self._busy = False
        return SinkCloseout(self.snapshot(), acknowledged, closed, terminal_hash)
