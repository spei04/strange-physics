"""Once-only checkout byte observation; no S authentication or loaded-code proof."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import threading
from dataclasses import dataclass

from d1_source_manifest import CatalogView, parse_catalog

CHUNK_BYTES = 65_536
SOURCE_BYTES = 131_072
LOCK_BYTES = 262_144
MAX_MEMBERS = 64
MAX_FAULTS = 16
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,31}\Z")


@dataclass(frozen=True, slots=True)
class ExpectedCheckoutFile:
    member_id: str
    locator: str
    loaded_module: str | None
    sha256: str
    byte_length: int


@dataclass(frozen=True, slots=True)
class ExpectedCheckoutPlan:
    source_commit: str
    source_tree: str
    catalog_ref: str
    files: tuple[ExpectedCheckoutFile, ...]


@dataclass(frozen=True, slots=True)
class RootIdentity:
    device: int
    inode: int
    uid: int
    mode: int


@dataclass(frozen=True, slots=True)
class FileObservation:
    member_id: str
    sha256: str
    byte_length: int
    identity: tuple[int, int]
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True, slots=True)
class CheckoutObservation:
    source_commit: str
    source_tree: str
    catalog_sha256: str
    root_identity: RootIdentity
    files: tuple[FileObservation, ...]
    unobserved_runtime_member_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObservationFault:
    phase: str
    member_id: str | None
    exception_type: str


@dataclass(frozen=True, slots=True)
class ObservationSnapshot:
    consumed: bool
    completed: bool
    planned: tuple[str, ...]
    entered: tuple[str, ...]
    observed: tuple[FileObservation, ...]
    planned_request_bytes: int
    requested_bytes: int
    known_returned_bytes: int
    read_calls: int
    open_attempts: int
    returned_opens: int
    close_attempts: int
    confirmed_closes: int
    unknown_open: bool
    closure_uncertain: bool
    faults: tuple[ObservationFault, ...]
    fault_overflow: int


class SourceFilesStopped(ValueError):
    """A consumed or faulted observation cannot be resumed."""


def _integer(value: object, upper: int) -> int:
    if type(value) is not int or not 0 <= value <= upper:
        raise ValueError("Exact bounded nonnegative integer required")
    return value


def _text(value: object, maximum: int) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum or not value.isascii():
        raise ValueError("Exact bounded ASCII text required")
    return value


def _digest(value: object, length: int) -> str:
    text = _text(value, length)
    if len(text) != length or re.fullmatch(r"[0-9a-f]+", text) is None:
        raise ValueError("Exact lowercase hexadecimal identity required")
    return text


def _root(value: RootIdentity) -> RootIdentity:
    if type(value) is not RootIdentity:
        raise ValueError("Exact RootIdentity required")
    return RootIdentity(
        _integer(value.device, 2**64 - 1), _integer(value.inode, 2**64 - 1),
        _integer(value.uid, 2**64 - 1), _integer(value.mode, 0o7777),
    )


def _plan(value: ExpectedCheckoutPlan, catalog: CatalogView) -> ExpectedCheckoutPlan:
    if type(value) is not ExpectedCheckoutPlan or type(value.files) is not tuple:
        raise ValueError("Exact plan and immutable complete tuple required")
    if not 1 <= len(value.files) <= MAX_MEMBERS:
        raise ValueError("Checkout plan member ceiling exceeded")
    commit, tree = _digest(value.source_commit, 40), _digest(value.source_tree, 40)
    catalog_ref = _text(value.catalog_ref, 32)
    if _REF.fullmatch(catalog_ref) is None:
        raise ValueError("Opaque catalog member reference required")
    policies = tuple(row for row in catalog.members if row.origin == "checkout_source")
    if len(value.files) != len(policies):
        raise ValueError("Complete checkout subset required")
    files: list[ExpectedCheckoutFile] = []
    for raw, policy in zip(value.files, policies, strict=True):
        if type(raw) is not ExpectedCheckoutFile:
            raise ValueError("Exact expected file record required")
        member = _text(raw.member_id, 32)
        locator = _text(raw.locator, 160)
        module = None if raw.loaded_module is None else _text(raw.loaded_module, 128)
        if (member, locator, module) != (policy.member_id, policy.locator, policy.loaded_module):
            raise ValueError("Expected plan differs from complete ordered catalog checkout subset")
        digest = _digest(raw.sha256, 64)
        limit = LOCK_BYTES if locator == "uv.lock" else SOURCE_BYTES
        length = _integer(raw.byte_length, limit)
        if not length:
            raise ValueError("Empty source members are outside this contract")
        if member == catalog_ref and (
            length > SOURCE_BYTES or length != len(catalog.raw) or digest != catalog.sha256
        ):
            raise ValueError("Expected catalog pin differs from actual supplied bytes")
        files.append(ExpectedCheckoutFile(member, locator, module, digest, length))
    if catalog_ref not in tuple(row.member_id for row in files):
        raise ValueError("Catalog reference must name a checkout member")
    return ExpectedCheckoutPlan(commit, tree, catalog_ref, tuple(files))


def _identity(value: os.stat_result) -> RootIdentity:
    return RootIdentity(value.st_dev, value.st_ino, value.st_uid, stat.S_IMODE(value.st_mode))


def _stamp(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev, value.st_ino, value.st_uid, value.st_mode, value.st_nlink,
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


class CheckoutObservationAttempt:
    """Own returned descriptors, never the caller's borrowed root descriptor."""

    _pid: int
    _thread: int
    _catalog_raw: bytes
    _raw_plan: ExpectedCheckoutPlan
    _root_fd: int
    _raw_root: RootIdentity
    _used: bool
    _busy: bool
    _completed: bool
    _first: BaseException | None
    _faults: list[ObservationFault]
    _overflow: int
    _phase: str
    _member: str | None
    _owned: list[int]
    _planned: tuple[str, ...]
    _entered: list[str]
    _observed: list[FileObservation]
    _planned_bytes: int
    _requested: int
    _returned: int
    _reads: int
    _opens: int
    _returned_opens: int
    _closes: int
    _confirmed_closes: int
    _unknown_open: bool
    _closure_uncertain: bool
    _uid: int

    def __init__(
        self, catalog_raw: bytes, plan: ExpectedCheckoutPlan, *,
        root_fd: int, expected_root: RootIdentity,
    ) -> None:
        self._pid, self._thread = os.getpid(), threading.get_ident()
        self._catalog_raw, self._raw_plan = catalog_raw, plan
        self._root_fd, self._raw_root = root_fd, expected_root
        self._used = self._busy = self._completed = False
        self._first = None
        self._faults = []
        self._overflow = 0
        self._phase, self._member = "validation", None
        self._owned = []
        self._planned = ()
        self._entered = []
        self._observed = []
        self._planned_bytes = self._requested = self._returned = self._reads = 0
        self._opens = self._returned_opens = self._closes = self._confirmed_closes = 0
        self._unknown_open = self._closure_uncertain = False
        self._uid = -1

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot(
            self._used, self._completed, self._planned, tuple(self._entered),
            tuple(self._observed), self._planned_bytes, self._requested, self._returned,
            self._reads, self._opens, self._returned_opens, self._closes,
            self._confirmed_closes, self._unknown_open, self._closure_uncertain,
            tuple(self._faults), self._overflow,
        )

    def _remember(self, error: BaseException) -> None:
        if self._first is None:
            self._first = error
        if len(self._faults) < MAX_FAULTS:
            self._faults.append(ObservationFault(self._phase, self._member, type(error).__name__[:192]))
        else:
            self._overflow += 1

    def _guard(self) -> None:
        if os.getpid() != self._pid or threading.get_ident() != self._thread:
            owner_error = SourceFilesStopped("Wrong observation owner")
            self._remember(owner_error)
        if self._first is not None:
            raise self._first

    def _enter(self) -> None:
        if self._busy:
            reentry_error = SourceFilesStopped("Observation reentry")
            self._remember(reentry_error)
            raise self._first if self._first is not None else reentry_error
        if self._used:
            raise SourceFilesStopped("Observation already consumed")
        self._used = True
        self._guard()
        self._busy = True

    def _open(self, name: str, parent: int, *, directory: bool) -> int:
        self._guard()
        self._phase = "open_directory" if directory else "open_file"
        self._opens += 1
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        flags |= os.O_DIRECTORY if directory else os.O_NONBLOCK
        self._unknown_open = True
        descriptor = os.open(name, flags, dir_fd=parent)
        if type(descriptor) is not int or descriptor < 0:
            raise ValueError("Open did not return a descriptor")
        self._owned.append(descriptor)
        self._returned_opens += 1
        self._unknown_open = False
        self._guard()
        return descriptor

    def _fstat(self, descriptor: int) -> os.stat_result:
        self._guard()
        self._phase = "fstat"
        result = os.fstat(descriptor)
        self._guard()
        return result

    def _named(self, name: str, parent: int) -> os.stat_result:
        self._guard()
        self._phase = "named_stat"
        result = os.stat(name, dir_fd=parent, follow_symlinks=False)
        self._guard()
        return result

    def _kind(self, value: os.stat_result, *, directory: bool) -> None:
        valid = stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)
        if not valid or value.st_uid != self._uid or stat.S_IMODE(value.st_mode) & 0o022:
            raise ValueError("Source kind, owner or writable mode is invalid")
        if not directory and value.st_nlink != 1:
            raise ValueError("Source leaf must have exactly one link")

    def _pair(self, descriptor: int, name: str, parent: int, *, directory: bool) -> os.stat_result:
        actual, named = self._fstat(descriptor), self._named(name, parent)
        self._kind(actual, directory=directory)
        self._kind(named, directory=directory)
        if _stamp(actual) != _stamp(named):
            raise ValueError("Named source differs from held descriptor")
        return actual

    def _root_check(self, descriptor: int, expected: RootIdentity) -> None:
        value = self._fstat(descriptor)
        self._kind(value, directory=True)
        if _identity(value) != expected:
            raise ValueError("Held checkout root identity changed")

    def _read(self, descriptor: int, count: int) -> bytes:
        self._guard()
        self._phase = "read"
        self._reads += 1
        self._requested += count
        raw = os.read(descriptor, count)
        if type(raw) is bytes:
            self._returned += len(raw)
        self._guard()
        if type(raw) is not bytes:
            raise ValueError("Read did not return exact bytes")
        return raw

    def _close_to(self, depth: int) -> None:
        # Cleanup intentionally ignores the sticky work latch, but never retries a slot.
        while len(self._owned) > depth:
            descriptor = self._owned.pop()
            self._phase = "close"
            self._closes += 1
            try:
                os.close(descriptor)
            except BaseException as close_error:
                self._closure_uncertain = True
                self._remember(close_error)
            else:
                self._confirmed_closes += 1

    def _file(
        self, expected: ExpectedCheckoutFile, root: int, root_identity: RootIdentity,
        seen: set[tuple[int, int]],
    ) -> FileObservation:
        self._member = expected.member_id
        self._entered.append(expected.member_id)
        self._root_check(root, root_identity)
        parent = root
        chain: list[tuple[int, str, int, os.stat_result]] = []
        parts = expected.locator.split("/")
        for part in parts[:-1]:
            child = self._open(part, parent, directory=True)
            before_directory = self._pair(child, part, parent, directory=True)
            chain.append((child, part, parent, before_directory))
            parent = child
        leaf = self._open(parts[-1], parent, directory=False)
        before_file = self._pair(leaf, parts[-1], parent, directory=False)
        key = (before_file.st_dev, before_file.st_ino)
        if key in seen:
            raise ValueError("Distinct checkout rows resolved to the same file")
        seen.add(key)
        if before_file.st_size != expected.byte_length:
            raise ValueError("Source extent differs from expected length")
        digest = hashlib.sha256()
        remaining = expected.byte_length
        while remaining:
            count = min(CHUNK_BYTES, remaining)
            chunk = self._read(leaf, count)
            if len(chunk) != count:
                raise ValueError("Short source read; no fill or retry")
            digest.update(chunk)
            del chunk
            remaining -= count
        overflow = self._read(leaf, 1)
        if overflow != b"":
            raise ValueError("Source overflow probe was not EOF")
        del overflow
        after_file = self._pair(leaf, parts[-1], parent, directory=False)
        if _stamp(before_file) != _stamp(after_file):
            raise ValueError("Source metadata changed during read")
        for descriptor, name, ancestor, before in reversed(chain):
            after_directory = self._pair(descriptor, name, ancestor, directory=True)
            if _stamp(before) != _stamp(after_directory):
                raise ValueError("Source ancestor changed during read")
        self._root_check(root, root_identity)
        observed_digest = digest.hexdigest()
        if observed_digest != expected.sha256:
            raise ValueError("Source digest differs from expected pin")
        return FileObservation(
            expected.member_id, observed_digest, expected.byte_length, key,
            before_file.st_mtime_ns, before_file.st_ctime_ns,
        )

    def observe(self) -> CheckoutObservation:
        self._enter()  # Rejected nested/consumed entry must never clean the outer owner.
        result: CheckoutObservation | None = None
        try:
            catalog = parse_catalog(self._catalog_raw)
            self._guard()
            plan = _plan(self._raw_plan, catalog)
            self._guard()
            expected_root = _root(self._raw_root)
            borrowed = _integer(self._root_fd, 2**31 - 1)
            self._planned = tuple(row.member_id for row in plan.files)
            self._planned_bytes = sum(row.byte_length + 1 for row in plan.files)
            self._uid = os.getuid()
            self._guard()
            self._root_check(borrowed, expected_root)
            root = self._open(".", borrowed, directory=True)
            self._root_check(root, expected_root)
            seen: set[tuple[int, int]] = set()
            for expected in plan.files:
                observation = self._file(expected, root, expected_root, seen)
                self._observed.append(observation)
                self._close_to(1)
                self._guard()
            self._member = None
            self._root_check(borrowed, expected_root)
            self._root_check(root, expected_root)
            result = CheckoutObservation(
                plan.source_commit, plan.source_tree, catalog.sha256, expected_root,
                tuple(self._observed), tuple(
                    row.member_id for row in catalog.members if row.origin == "trusted_runtime_member"
                ),
            )
        except BaseException as work_error:
            if work_error is not self._first:
                self._remember(work_error)
        finally:
            self._close_to(0)
            self._busy = False
        self._guard()
        if result is None:
            raise SourceFilesStopped("Observation did not produce a complete result")
        self._completed = True
        return result
