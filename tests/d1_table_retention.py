"""One conditional T retention; no source resolver, activation or event installation."""

from __future__ import annotations

import hashlib
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from d1_codec_append import _context
from d1_primitive_codec_table import TABLE_BYTES, parse_table
from d1_primitive_sink import (
    Identity,
    PrimitiveFileSink,
    _Anchor,
    _identity,
    _read_file,
    _write_remaining,
)

TABLE_NAME = "identity-table.json"
MAX_FAULTS = 16


class TableRetentionStopped(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TableContextObservation:
    table_raw: bytes
    table_sha256: str
    table_bytes: int
    context_raw: bytes
    context_sha256: str
    context_bytes: int


@dataclass(frozen=True, slots=True)
class RetentionFault:
    phase: str
    exception_type: str
    exception_type_complete: bool


@dataclass(frozen=True, slots=True)
class RetentionSnapshot:
    consumed: bool
    stopped: bool
    reserved_bytes: int
    written_bytes: int
    creation_entered: bool
    anchor_received: bool
    table_creation_entered: bool
    table_created: bool
    table_synced: bool
    table_readback_equal: bool
    metadata_close_confirmed: bool | None
    context_observations: int
    faults: tuple[RetentionFault, ...]
    unretained_fault_count: int


class TableRetentionAttempt:
    """Own metadata descriptors once; the caller retains all sink ownership."""

    first_exception: BaseException | None
    _root: Path
    _sink: PrimitiveFileSink
    _raw: bytes
    _pid: int
    _thread: int
    _busy: bool
    _consumed: bool
    _stopped: bool
    _reserved: int
    _written: int
    _creation_entered: bool
    _table_creation_entered: bool
    _table_created: bool
    _table_synced: bool
    _readback_equal: bool
    _close_confirmed: bool | None
    _observations: int
    _faults: list[RetentionFault]
    _unretained: int
    _anchor: _Anchor | None
    _write_fd: int | None
    _table_identity: Identity | None
    _close_fault_count: int
    _sink_parent: Identity | None
    _sink_root: Identity | None

    def __init__(self, metadata_root: Path, sink: PrimitiveFileSink, table_raw: bytes) -> None:
        # Validation belongs to the consumed attempt, before any filesystem operation.
        self._root, self._sink, self._raw = metadata_root, sink, table_raw
        self._pid, self._thread = os.getpid(), threading.get_ident()
        self.first_exception = None
        self._busy = self._consumed = self._stopped = False
        self._reserved = self._written = self._observations = self._unretained = 0
        self._creation_entered = self._table_creation_entered = False
        self._table_created = self._table_synced = False
        self._readback_equal = False
        self._close_confirmed = None
        self._faults = []
        self._anchor = None
        self._write_fd = None
        self._table_identity = None
        self._close_fault_count = 0
        self._sink_parent = self._sink_root = None

    def snapshot(self) -> RetentionSnapshot:
        """Bounded facts only; neither a serialized receipt nor retry authority."""
        return RetentionSnapshot(
            self._consumed, self._stopped, self._reserved, self._written,
            self._creation_entered, self._anchor is not None, self._table_creation_entered,
            self._table_created,
            self._table_synced, self._readback_equal, self._close_confirmed,
            self._observations, tuple(self._faults), self._unretained,
        )

    def _remember(self, phase: str, error: BaseException) -> None:
        self._stopped = True
        if self.first_exception is None:
            self.first_exception = error
        name = type(error).__module__ + "." + type(error).__qualname__
        if len(self._faults) < MAX_FAULTS:
            self._faults.append(RetentionFault(phase, name[:192], len(name) <= 192))
        else:
            self._unretained += 1

    def _enter(self) -> None:
        if os.getpid() != self._pid or threading.get_ident() != self._thread or self._busy:
            rejected = TableRetentionStopped("Wrong owner or reentrant table retention")
            self._consumed = True
            self._remember("ownership_or_reentry", rejected)
            raise rejected
        if self._consumed:
            raise TableRetentionStopped("Table retention opportunity is consumed")
        self._consumed = self._busy = True

    def _active(self) -> None:
        if os.getpid() != self._pid or threading.get_ident() != self._thread:
            rejected = TableRetentionStopped("Table retention owner changed")
            self._remember("ownership_or_reentry", rejected)
        if self._stopped:
            assert self.first_exception is not None
            raise self.first_exception

    def _sink_identities(self) -> tuple[Identity, Identity]:
        # Borrow only read-only checks, never descriptor ownership or sink state.
        anchor = self._sink._anchor
        anchor.check()
        assert anchor.parent is not None and anchor.directory is not None
        parent = _identity(os.fstat(anchor.parent))
        root = _identity(os.fstat(anchor.directory))
        if parent != anchor.parent_identity or root != anchor.root_identity:
            raise ValueError("Actual sink anchor identity changed")
        return parent, root

    def _check(self) -> None:
        self._active()
        parent, root = self._sink_identities()
        if parent != self._sink_parent or root != self._sink_root:
            raise ValueError("Borrowed sink identity differs from the initial observation")
        anchor = self._anchor
        if anchor is not None:
            anchor.check()
            if anchor.parent_identity != parent or anchor.root_identity[:2] == root[:2]:
                raise ValueError("Distinct sibling metadata root required")
            if self._table_identity is not None:
                named = os.stat(TABLE_NAME, dir_fd=anchor.directory, follow_symlinks=False)
                if _identity(named) != self._table_identity or named.st_nlink != 1:
                    raise ValueError("Created table identity changed")
        self._active()

    def _drain_close_faults(self) -> None:
        anchor = self._anchor
        if anchor is not None:
            for error in anchor.close_faults[self._close_fault_count :]:
                self._remember("metadata_descriptor_close", error)
            self._close_fault_count = len(anchor.close_faults)

    def _close_writer(self) -> None:
        descriptor, self._write_fd = self._write_fd, None
        if descriptor is not None:
            try:
                os.close(descriptor)
            except BaseException as writer_close_error:
                assert self._anchor is not None
                self._anchor.closure_uncertain = True
                self._remember("metadata_write_close", writer_close_error)

    def _cleanup(self) -> None:
        # Independent remaining closes run even after a swallowed reentry or earlier error.
        self._close_writer()
        self._drain_close_faults()
        anchor = self._anchor
        if anchor is None:
            # A constructor may have created a root then failed without returning an anchor.
            self._close_confirmed = False if self._creation_entered else None
            return
        try:
            close_errors = anchor.close()
        except BaseException as cleanup_error:
            self._close_confirmed = False
            self._remember("metadata_anchor_close", cleanup_error)
            return
        self._close_confirmed = not close_errors and not anchor.closure_uncertain
        for close_error in close_errors:
            self._remember("metadata_anchor_close", close_error)

    def retain(self) -> TableContextObservation:
        self._enter()  # A rejected nested call must not release the outer busy flag.
        phase = "preflight"
        work_error_recorded = False
        try:
            try:
                if type(self._sink) is not PrimitiveFileSink or not isinstance(self._root, Path):
                    raise ValueError("Actual owned sink and concrete metadata path required")
                if not self._root.is_absolute() or ".." in self._root.parts:
                    raise ValueError("Normalized absolute metadata root required")
                table = parse_table(self._raw)
                phase = "context_before"
                before = self._sink.observe_context()
                self._observations += 1
                binding_before = _context(before.raw, table)
                self._active()
                self._sink_parent, self._sink_root = self._sink_identities()
                if self._root.name == self._sink._anchor.path.name:
                    raise ValueError("Metadata and sink root names must differ")
                self._reserved = len(table.raw)
                self._check()
                phase = "metadata_create"
                self._creation_entered = True
                self._anchor = _Anchor(self._root, create=True, expected_parent=self._sink_parent)
                self._check()
                phase = "table_create"
                self._table_creation_entered = True
                self._write_fd, identity = self._anchor.open_file(TABLE_NAME, create=True)
                self._table_identity = identity
                self._table_created = True
                self._check()
                phase = "table_write"
                progress = [0]
                try:
                    _write_remaining(self._write_fd, table.raw, progress, self._check)
                finally:
                    self._written += progress[0]
                self._active()
                self._anchor.file_check(TABLE_NAME, self._write_fd, identity, len(table.raw))
                self._check()
                phase = "table_fsync"
                os.fsync(self._write_fd)
                self._check()
                phase = "directory_fsync"
                self._anchor.sync()
                self._anchor.file_check(TABLE_NAME, self._write_fd, identity, len(table.raw))
                self._check()
                self._table_synced = True
                self._close_writer()
                self._active()
                phase = "table_readback"
                actual = _read_file(self._anchor, TABLE_NAME, TABLE_BYTES)
                self._active()
                if actual != table.raw:
                    raise ValueError("Actual retained table bytes differ")
                self._readback_equal = True
                self._check()
                actual_hash = hashlib.sha256(actual).hexdigest()
            except BaseException as work_error:
                work_error_recorded = True
                if self.first_exception is not work_error:
                    self._remember(phase, work_error)
                raise
            finally:
                self._cleanup()
            self._active()  # A swallowed close-hook reentry prohibits the second C read.
            if self._close_confirmed is not True:
                raise TableRetentionStopped("Metadata closure is uncertain")
            phase = "context_after"
            after = self._sink.observe_context()
            self._observations += 1
            binding_after = _context(after.raw, table)
            if after.raw != before.raw or binding_after != binding_before:
                raise ValueError("Fresh context differs from the initial context")
            result = TableContextObservation(
                actual, actual_hash, len(actual), after.raw, after.sha256, after.byte_length,
            )
            self._active()  # Also guard swallowed reentry inside the final observation.
            return result
        except BaseException as retained_error:
            if not work_error_recorded and self.first_exception is not retained_error:
                self._remember(phase, retained_error)
            raise
        finally:
            self._busy = False
