"""Owned fake files only; no project source, primitives or authority are resolved."""

from __future__ import annotations

import builtins
import errno
import hashlib
import json
import os
import stat
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NoReturn

import d1_source_files as files
import pytest
from d1_source_files import (
    CheckoutObservationAttempt, ExpectedCheckoutFile, ExpectedCheckoutPlan,
    RootIdentity, SourceFilesStopped,
)


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def catalog_fixture() -> dict[str, Any]:
    return {
        "schema": "strange-physics.d1-source-catalog.v1",
        "installation_member_ref": "m03",
        "members": [
            ["m00", "checkout_source", "synthetic/catalog.json", None],
            ["m01", "checkout_source", "tests/d1_primitive_codec.py", "d1_primitive_codec"],
            ["m02", "checkout_source", "synthetic/emitter.py", "synthetic_emitter"],
            ["m03", "checkout_source", "synthetic/installer.py", "synthetic_installer"],
            ["m04", "checkout_source", "uv.lock", None],
            [
                "m05", "checkout_source", "tests/endpoint_belief_reference.py",
                "endpoint_belief_reference",
            ],
            ["m06", "checkout_source", "docs/research/RA_N03_CALIBRATION_SLICE.md", None],
            ["m07", "checkout_source", "tests/d1_primitive_recording.py", "d1_primitive_recording"],
            ["m08", "checkout_source", "tests/d1_primitive_sink.py", "d1_primitive_sink"],
        ],
        "definitions": [
            ["d0", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.position"],
            ["d1", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.exp"],
            ["d2", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.log"],
            [
                "d3", "m05", "python_method", "endpoint_belief_reference",
                "EndpointOracle.circle_constant",
            ],
            ["d4", "m02", "python_function", "synthetic_emitter", "emit"],
        ],
        "instances": [
            ["i00", "fixture", None, "m05"], ["i01", "strong", None, "m05"],
            ["i02", "weak", None, "m05"], ["i03", "future", None, "m05"],
            ["i04", "arithmetic", 0, "m05"], ["i05", "arithmetic", 1, "m05"],
            ["i06", "arithmetic", 2, "m05"], ["i07", "arithmetic", 3, "m05"],
            ["i08", "arithmetic", 4, "m05"], ["i09", "arithmetic", 5, "m05"],
            ["i10", "arithmetic", 6, "m05"], ["i11", "arithmetic", 7, "m05"],
            ["i12", "constants", None, "m05"], ["i13", "native_emit", None, "m02"],
        ],
        "dispatch_policy": [
            ["i00", 0, "d0", "j00",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i01", 0, "d0", "j01",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i02", 0, "d0", "j02",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i03", 0, "d0", "j03",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i04", 1, "d1", "j04",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i04", 2, "d2", "j05",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i05", 1, "d1", "j06",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i05", 2, "d2", "j07",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i06", 1, "d1", "j08",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i06", 2, "d2", "j09",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i07", 1, "d1", "j10",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i07", 2, "d2", "j11",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i08", 1, "d1", "j12",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i08", 2, "d2", "j13",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i09", 1, "d1", "j14",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i09", 2, "d2", "j15",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i10", 1, "d1", "j16",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i10", 2, "d2", "j17",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i11", 1, "d1", "j18",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i11", 2, "d2", "j19",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i12", 2, "d2", "j20",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i12", 3, "d3", "j21",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i13", 4, "d4", "j22",
             "m03", "dispatch", "m03", "run", "native_callable_recorder_slot_v1"],
        ],
    }


@dataclass(frozen=True)
class OwnedFixture:
    root: Path
    fd: int
    raw: bytes
    plan: ExpectedCheckoutPlan
    identity: RootIdentity

    def attempt(self, *, plan: ExpectedCheckoutPlan | None = None) -> CheckoutObservationAttempt:
        return CheckoutObservationAttempt(
            self.raw, self.plan if plan is None else plan,
            root_fd=self.fd, expected_root=self.identity,
        )


@pytest.fixture
def owned(tmp_path: Path) -> Iterator[OwnedFixture]:
    root = tmp_path / "checkout"
    root.mkdir(mode=0o755)
    catalog = catalog_fixture()
    catalog["members"][2] = ["m02", "trusted_runtime_member", "native-emitter", "synthetic_runtime"]
    catalog["definitions"][4] = ["d4", "m02", "runtime_builtin", "synthetic_runtime", "emit"]
    raw = encoded(catalog)
    assert len(raw) < 8192
    expected = []
    for member, origin, locator, module in catalog["members"]:
        if origin != "checkout_source":
            continue
        data = raw if member == "m00" else b"fake:" + member.encode("ascii") + b"\n"
        path = root / locator
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
        expected.append(ExpectedCheckoutFile(member, locator, module, hashlib.sha256(data).hexdigest(), len(data)))
    for directory in (root, root / "synthetic", root / "tests", root / "docs", root / "docs/research"):
        directory.chmod(0o755)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    actual = os.fstat(fd)
    try:
        yield OwnedFixture(
            root, fd, raw, ExpectedCheckoutPlan("a" * 40, "b" * 40, "m00", tuple(expected)),
            RootIdentity(actual.st_dev, actual.st_ino, actual.st_uid, stat.S_IMODE(actual.st_mode)),
        )
    finally:
        os.close(fd)


@pytest.fixture(autouse=True)
def no_scientific_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    original = builtins.__import__

    def guarded(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith((
            "strange_physics", "endpoint_belief_reference", "d1_fixture_reference",
            "d1_prefix_evidence", "d1_primitive_recording", "d1_primitive_sink",
            "d1_codec_append", "d1_table_retention",
        )):
            raise AssertionError("No scientific, recorder, sink or runtime resolution")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)


def denied(*args: Any, **kwargs: Any) -> NoReturn:
    raise AssertionError("Unexpected filesystem operation")


def assert_no_io_retry(attempt: CheckoutObservationAttempt, monkeypatch: pytest.MonkeyPatch) -> None:
    with monkeypatch.context() as scoped:
        for name in ("open", "read", "fstat", "stat", "close"):
            scoped.setattr(os, name, denied)
        with pytest.raises(SourceFilesStopped, match="consumed"):
            attempt.observe()


def changed_plan(owned: OwnedFixture, index: int, **changes: Any) -> ExpectedCheckoutPlan:
    # Intentionally untrusted input fixture; production boundary must revalidate it.
    item = replace(owned.plan.files[index])
    for name, value in changes.items():
        object.__setattr__(item, name, value)
    rows = list(owned.plan.files)
    rows[index] = item
    return replace(owned.plan, files=tuple(rows))


def test_complete_owned_observation_and_consumed_retry(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    attempt = owned.attempt()
    result = attempt.observe()
    assert tuple(row.member_id for row in result.files) == ("m00", "m01", "m03", "m04", "m05", "m06", "m07", "m08")
    assert tuple((row.sha256, row.byte_length) for row in result.files) == tuple(
        (row.sha256, row.byte_length) for row in owned.plan.files
    )
    assert result.unobserved_runtime_member_ids == ("m02",)
    assert not hasattr(result, "authenticated") and not hasattr(result, "ready")
    snapshot = attempt.snapshot()
    assert snapshot.completed and snapshot.read_calls == 16
    assert snapshot.requested_bytes == sum(row.byte_length + 1 for row in owned.plan.files)
    assert snapshot.known_returned_bytes == sum(row.byte_length for row in owned.plan.files)
    assert snapshot.open_attempts == snapshot.returned_opens == snapshot.close_attempts == snapshot.confirmed_closes
    assert not snapshot.unknown_open and not snapshot.closure_uncertain
    assert os.fstat(owned.fd).st_ino == owned.identity.inode
    assert_no_io_retry(attempt, monkeypatch)


@pytest.mark.parametrize("kind", ["missing", "extra", "order", "module", "locator", "bool", "hash", "catalog-pin", "catalog-ref", "empty", "large", "tuple", "commit", "tree"], ids=["missing", "extra", "order", "module", "locator", "bool", "hash", "catalog-pin", "catalog-ref", "empty", "large", "tuple", "commit", "tree"])
def test_plan_failures_precede_owned_io(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    plan = replace(owned.plan)
    if kind == "missing":
        plan = replace(plan, files=plan.files[:-1])
    elif kind == "extra":
        plan = replace(plan, files=plan.files + (plan.files[-1],))
    elif kind == "order":
        plan = replace(plan, files=tuple(reversed(plan.files)))
    elif kind == "module":
        plan = changed_plan(owned, 1, loaded_module="wrong")
    elif kind == "locator":
        plan = changed_plan(owned, 1, locator="../outside")
    elif kind == "bool":
        plan = changed_plan(owned, 1, byte_length=True)
    elif kind == "hash":
        plan = changed_plan(owned, 1, sha256="A" * 64)
    elif kind == "catalog-pin":
        plan = changed_plan(owned, 0, sha256="0" * 64)
    elif kind == "catalog-ref":
        plan = replace(plan, catalog_ref="m02")
    elif kind == "empty":
        plan = changed_plan(owned, 1, byte_length=0)
    elif kind == "large":
        plan = changed_plan(owned, 1, byte_length=131073)
    elif kind == "tuple":
        object.__setattr__(plan, "files", list(plan.files))
    elif kind == "commit":
        object.__setattr__(plan, "source_commit", True)
    else:
        plan = replace(plan, source_tree="a" * 41)
    attempt = owned.attempt(plan=plan)
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", denied)
        scoped.setattr(os, "fstat", denied)
        scoped.setattr(os, "close", denied)
        with pytest.raises(ValueError):
            attempt.observe()
    assert attempt.snapshot().open_attempts == 0
    assert_no_io_retry(attempt, monkeypatch)


@pytest.mark.parametrize("kind", ["raw", "plan-subclass", "record-subclass", "root-bool", "fd-bool", "root-mode"], ids=["raw", "plan-type", "record-type", "root-bool", "fd-bool", "root-mode"])
def test_exact_boundaries_reject_without_opens(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    raw: Any = owned.raw
    plan = owned.plan
    identity = replace(owned.identity)
    descriptor: Any = owned.fd
    if kind == "raw":
        raw = bytearray(raw)
    elif kind == "plan-subclass":
        class PlanSubclass(ExpectedCheckoutPlan):
            pass
        plan = PlanSubclass(plan.source_commit, plan.source_tree, plan.catalog_ref, plan.files)
    elif kind == "record-subclass":
        class FileSubclass(ExpectedCheckoutFile):
            pass
        row = plan.files[0]
        substituted = FileSubclass(row.member_id, row.locator, row.loaded_module, row.sha256, row.byte_length)
        plan = replace(plan, files=(substituted, *plan.files[1:]))
    elif kind == "root-bool":
        object.__setattr__(identity, "inode", True)
    elif kind == "fd-bool":
        descriptor = True
    else:
        identity = replace(identity, mode=65536)
    attempt = CheckoutObservationAttempt(raw, plan, root_fd=descriptor, expected_root=identity)
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", denied)
        scoped.setattr(os, "fstat", denied)
        with pytest.raises(ValueError):
            attempt.observe()
    assert attempt.snapshot().open_attempts == 0


def test_wrong_root_identity_does_not_close_borrowed_root(owned: OwnedFixture) -> None:
    attempt = CheckoutObservationAttempt(owned.raw, owned.plan, root_fd=owned.fd,
        expected_root=replace(owned.identity, inode=owned.identity.inode + 1))
    with pytest.raises(ValueError, match="root identity"):
        attempt.observe()
    assert attempt.snapshot().open_attempts == attempt.snapshot().close_attempts == 0
    assert os.fstat(owned.fd).st_ino == owned.identity.inode


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "hardlink", "writable", "ancestor-link"], ids=["symlink", "fifo", "directory", "hardlink", "writable", "ancestor-link"])
def test_owned_nonregular_or_unsafe_paths(owned: OwnedFixture, kind: str) -> None:
    target = owned.root / "tests/d1_primitive_codec.py"
    if kind == "writable":
        target.chmod(0o666)
    elif kind == "hardlink":
        os.link(target, owned.root / "extra-link")
    elif kind == "ancestor-link":
        directory = owned.root / "tests"
        directory.rename(owned.root / "held-tests")
        directory.symlink_to("held-tests", target_is_directory=True)
    else:
        target.unlink()
        if kind == "symlink":
            target.symlink_to("d1_primitive_sink.py")
        elif kind == "fifo":
            os.mkfifo(target)
        else:
            target.mkdir()
    attempt = owned.attempt()
    with pytest.raises((OSError, ValueError)):
        attempt.observe()
    snapshot = attempt.snapshot()
    assert len(snapshot.observed) == 1
    assert snapshot.returned_opens == snapshot.close_attempts == snapshot.confirmed_closes
    assert os.fstat(owned.fd).st_ino == owned.identity.inode


@pytest.mark.parametrize("kind", ["leaf", "ancestor"], ids=["leaf", "ancestor"])
def test_post_open_same_target_symlink_is_not_followed(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    original_open = os.open
    injected = False
    target = owned.root / ("tests/d1_primitive_codec.py" if kind == "leaf" else "tests")
    selected = "d1_primitive_codec.py" if kind == "leaf" else "tests"
    held_name = "held.py" if kind == "leaf" else "held-tests"

    def substitute(path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal injected
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == selected and not injected:
            injected = True
            target.rename(target.with_name(held_name))
            target.symlink_to(held_name, target_is_directory=kind == "ancestor")
        return descriptor

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", substitute)
        with pytest.raises(ValueError, match="kind"):
            attempt.observe()
    assert injected and len(attempt.snapshot().observed) == 1
    assert attempt.snapshot().confirmed_closes == attempt.snapshot().returned_opens


@pytest.mark.parametrize("kind", ["extent", "mtime", "replacement", "digest"], ids=["extent", "mtime", "replacement", "digest"])
def test_deterministic_read_mutations(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    target = owned.root / "tests/d1_primitive_codec.py"
    old = target.stat()
    original_read = os.read
    injected = False
    if kind == "digest":
        target.write_bytes(b"X" * old.st_size)

    def mutate(descriptor: int, count: int) -> bytes:
        nonlocal injected
        raw = original_read(descriptor, count)
        if not injected and os.fstat(descriptor).st_ino == old.st_ino and raw:
            injected = True
            if kind == "extent":
                with target.open("ab") as stream:
                    stream.write(b"!")
            elif kind == "mtime":
                os.utime(target, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
            elif kind == "replacement":
                target.rename(target.with_name("previous.py"))
                target.write_bytes(raw)
                target.chmod(0o644)
        return raw

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", mutate)
        with pytest.raises(ValueError):
            attempt.observe()
    assert len(attempt.snapshot().observed) == 1
    assert attempt.snapshot().returned_opens == attempt.snapshot().confirmed_closes


@pytest.mark.parametrize("kind", ["short", "zero", "interrupt", "error", "not-bytes", "overflow"], ids=["short", "zero", "interrupt", "error", "type", "overflow"])
def test_read_fault_is_once_only(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    original_read = os.read
    calls = 0
    primary = InterruptedError("synthetic interruption") if kind == "interrupt" else OSError(errno.EIO, "synthetic read")

    def failing(descriptor: int, count: int) -> Any:
        nonlocal calls
        calls += 1
        if kind == "overflow":
            return b"!" if calls == 2 else original_read(descriptor, count)
        if kind == "short":
            return original_read(descriptor, count - 1)
        if kind == "zero":
            return b""
        if kind == "not-bytes":
            return bytearray(b"x")
        raise primary

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", failing)
        with pytest.raises((ValueError, OSError)) as caught:
            attempt.observe()
    assert calls == (2 if kind == "overflow" else 1)
    if kind in ("error", "interrupt"):
        assert caught.value is primary
    assert attempt.snapshot().observed == ()
    assert attempt.snapshot().returned_opens == attempt.snapshot().confirmed_closes
    assert_no_io_retry(attempt, monkeypatch)


def test_exact_chunk_and_eof_request_schedule(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    target = owned.root / "tests/d1_primitive_codec.py"
    data = b"a" * 131072
    target.write_bytes(data)
    plan = changed_plan(owned, 1, byte_length=len(data), sha256=hashlib.sha256(data).hexdigest())
    inode = target.stat().st_ino
    original_read = os.read
    requested: list[int] = []

    def capture(descriptor: int, count: int) -> bytes:
        if os.fstat(descriptor).st_ino == inode:
            requested.append(count)
        return original_read(descriptor, count)

    attempt = owned.attempt(plan=plan)
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", capture)
        result = attempt.observe()
    assert requested == [65536, 65536, 1]
    assert result.files[1].sha256 == hashlib.sha256(data).hexdigest()
    assert attempt.snapshot().requested_bytes == sum(row.byte_length + 1 for row in plan.files)


def test_primary_read_fault_survives_real_close_then_error(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    original_close = os.close
    primary = OSError(errno.EIO, "read first")
    target: int | None = None
    injections = 0

    def fail_read(descriptor: int, count: int) -> NoReturn:
        nonlocal target
        target = descriptor
        raise primary

    def close_then_error(descriptor: int) -> None:
        nonlocal injections
        original_close(descriptor)
        if descriptor == target:
            injections += 1
            raise PermissionError("close confirmation lost")

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read", fail_read)
        scoped.setattr(os, "close", close_then_error)
        with pytest.raises(OSError) as caught:
            attempt.observe()
    assert caught.value is primary and injections == 1 and target is not None
    with pytest.raises(OSError):
        os.fstat(target)
    snapshot = attempt.snapshot()
    assert snapshot.closure_uncertain and snapshot.close_attempts == snapshot.returned_opens
    assert snapshot.confirmed_closes == snapshot.close_attempts - 1
    assert [item.exception_type for item in snapshot.faults] == ["OSError", "PermissionError"]
    assert snapshot.faults[0].phase == "read" and snapshot.faults[1].phase == "close"
    assert_no_io_retry(attempt, monkeypatch)


@pytest.mark.parametrize("phase", ["read", "close"], ids=["read", "close"])
@pytest.mark.parametrize("later_error", [False, True], ids=["swallowed", "later-error"])
def test_sticky_reentry_blocks_work_but_keeps_cleanup(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, phase: str, later_error: bool) -> None:
    original_read, original_close = os.read, os.close
    attempt = owned.attempt()
    nested: list[SourceFilesStopped] = []
    injected = False
    later = OSError(errno.EIO, "after swallowed reentry")

    def reenter() -> None:
        nonlocal injected
        if not injected:
            injected = True
            try:
                attempt.observe()
            except SourceFilesStopped as nested_error:
                nested.append(nested_error)
            if later_error:
                raise later

    def hooked_read(descriptor: int, count: int) -> bytes:
        raw = original_read(descriptor, count)
        reenter()
        return raw

    def hooked_close(descriptor: int) -> None:
        original_close(descriptor)
        reenter()

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "read" if phase == "read" else "close", hooked_read if phase == "read" else hooked_close)
        with pytest.raises(SourceFilesStopped) as caught:
            attempt.observe()
    assert len(nested) == 1 and caught.value is nested[0]
    snapshot = attempt.snapshot()
    assert not snapshot.completed and len(snapshot.entered) == 1
    assert snapshot.close_attempts == snapshot.returned_opens
    assert snapshot.confirmed_closes == snapshot.close_attempts - int(phase == "close" and later_error)
    if later_error:
        assert snapshot.faults[-1].exception_type == "OSError"
    assert os.fstat(owned.fd).st_ino == owned.identity.inode
    assert_no_io_retry(attempt, monkeypatch)


def test_open_entry_failure_retains_unknown_without_fabricated_fd(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = OSError(errno.EIO, "no returned descriptor")

    def fail_open(*args: Any, **kwargs: Any) -> NoReturn:
        raise primary

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", fail_open)
        with pytest.raises(OSError) as caught:
            attempt.observe()
    snapshot = attempt.snapshot()
    assert caught.value is primary and snapshot.unknown_open
    assert snapshot.open_attempts == 1 and snapshot.returned_opens == snapshot.close_attempts == 0
    assert os.fstat(owned.fd).st_ino == owned.identity.inode


@pytest.mark.parametrize("owner", ["pid", "thread"], ids=["pid", "thread"])
def test_wrong_owner_consumes_without_descriptor_work(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, owner: str) -> None:
    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        if owner == "pid":
            scoped.setattr(os, "getpid", lambda: -1)
        else:
            import threading
            scoped.setattr(threading, "get_ident", lambda: -1)
        scoped.setattr(os, "open", denied)
        scoped.setattr(os, "close", denied)
        with pytest.raises(SourceFilesStopped, match="owner"):
            attempt.observe()
    assert attempt.snapshot().consumed and attempt.snapshot().open_attempts == 0
    assert_no_io_retry(attempt, monkeypatch)
@pytest.mark.parametrize("operation", ["fstat", "stat"], ids=["fd-stat", "named-stat"])
def test_stat_error_keeps_prior_observations_and_closes_owned_chain(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, operation: str) -> None:
    original_fstat, original_stat = os.fstat, os.stat
    inode = (owned.root / "tests/d1_primitive_codec.py").stat().st_ino
    primary = OSError(errno.EIO, "stat failure")

    def fail_fstat(descriptor: int) -> os.stat_result:
        result = original_fstat(descriptor)
        if result.st_ino == inode:
            raise primary
        return result

    def fail_named(path: Any, *, dir_fd: int | None = None, follow_symlinks: bool = True) -> os.stat_result:
        if path == "d1_primitive_codec.py":
            assert follow_symlinks is False
            raise primary
        return original_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, operation, fail_fstat if operation == "fstat" else fail_named)
        with pytest.raises(OSError) as caught:
            attempt.observe()
    snapshot = attempt.snapshot()
    assert caught.value is primary
    assert tuple(item.member_id for item in snapshot.observed) == ("m00",)
    assert snapshot.entered == ("m00", "m01") and len(snapshot.planned) == 8
    assert snapshot.returned_opens == snapshot.confirmed_closes
    assert_no_io_retry(attempt, monkeypatch)


@pytest.mark.parametrize("target_name", ["catalog.json", "."], ids=["first-file", "final-root"])
def test_close_uncertainty_alone_cannot_return_success(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, target_name: str) -> None:
    original_open, original_close = os.open, os.close
    target: int | None = None
    injections = 0
    primary = OSError(errno.EIO, "close confirmation lost")

    def capture(path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal target
        result = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == target_name:
            target = result
        return result

    def close_once(descriptor: int) -> None:
        nonlocal injections
        original_close(descriptor)
        if descriptor == target and not injections:
            injections += 1
            raise primary

    attempt = owned.attempt()
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", capture)
        scoped.setattr(os, "close", close_once)
        with pytest.raises(OSError) as caught:
            attempt.observe()
    snapshot = attempt.snapshot()
    assert caught.value is primary and injections == 1 and target is not None
    assert len(snapshot.observed) == (1 if target_name == "catalog.json" else 8)
    assert snapshot.closure_uncertain and not snapshot.completed
    assert snapshot.returned_opens == snapshot.close_attempts == snapshot.confirmed_closes + 1
    with pytest.raises(OSError):
        os.fstat(target)
    assert os.fstat(owned.fd).st_ino == owned.identity.inode
    assert_no_io_retry(attempt, monkeypatch)


@pytest.mark.parametrize("kind", ["members", "lock-size", "id", "locator", "module", "root-range"], ids=["members-65", "lock-cap", "id-long", "path-long", "module-long", "root-range"])
def test_declared_input_caps_precede_owned_io(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    plan = owned.plan
    identity = owned.identity
    if kind == "members":
        plan = replace(plan, files=(plan.files[0],) * 65)
    elif kind == "lock-size":
        plan = changed_plan(owned, 3, byte_length=262145)
    elif kind == "id":
        plan = changed_plan(owned, 1, member_id="x" * 33)
    elif kind == "locator":
        plan = changed_plan(owned, 1, locator="a" * 161)
    elif kind == "module":
        plan = changed_plan(owned, 1, loaded_module="a" * 129)
    else:
        identity = replace(identity, device=2**64)
    attempt = CheckoutObservationAttempt(owned.raw, plan, root_fd=owned.fd, expected_root=identity)
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", denied)
        scoped.setattr(os, "fstat", denied)
        with pytest.raises(ValueError):
            attempt.observe()
    assert attempt.snapshot().open_attempts == 0

def test_renamed_single_link_file_cannot_fill_two_member_rows(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    original_open, original_close = os.open, os.close
    catalog_path = owned.root / "synthetic/catalog.json"
    target = owned.root / "tests/d1_primitive_codec.py"
    plan = changed_plan(owned, 1, byte_length=len(owned.raw), sha256=hashlib.sha256(owned.raw).hexdigest())
    catalog_fd: int | None = None
    moved = False

    def capture(path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal catalog_fd
        result = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == "catalog.json":
            catalog_fd = result
        return result

    def rename_after_close(descriptor: int) -> None:
        nonlocal moved
        original_close(descriptor)
        if descriptor == catalog_fd and not moved:
            moved = True
            target.unlink()
            catalog_path.rename(target)

    attempt = owned.attempt(plan=plan)
    with monkeypatch.context() as scoped:
        scoped.setattr(os, "open", capture)
        scoped.setattr(os, "close", rename_after_close)
        with pytest.raises(ValueError, match="same file"):
            attempt.observe()
    assert moved and target.stat().st_nlink == 1
    assert tuple(row.member_id for row in attempt.snapshot().observed) == ("m00",)
    assert attempt.snapshot().confirmed_closes == attempt.snapshot().returned_opens


@pytest.mark.parametrize("window", ["first", "final"], ids=["first-guard", "final-guard"])
def test_owner_guard_reentry_stays_latched_through_final_close(owned: OwnedFixture, monkeypatch: pytest.MonkeyPatch, window: str) -> None:
    original_pid, original_open, original_close = os.getpid, os.open, os.close
    attempt = owned.attempt()
    nested: list[SourceFilesStopped] = []
    root_descriptor: int | None = None
    root_closed = False
    injected = False

    def capture_root(path: Any, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal root_descriptor
        result = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == ".":
            root_descriptor = result
        return result

    def close_owned(descriptor: int) -> None:
        nonlocal root_closed
        original_close(descriptor)
        if descriptor == root_descriptor:
            root_closed = True

    def swallowed_reentry() -> int:
        nonlocal injected
        if not injected and (window == "first" or root_closed):
            injected = True
            try:
                attempt.observe()
            except SourceFilesStopped as nested_error:
                nested.append(nested_error)
        return original_pid()

    with monkeypatch.context() as scoped:
        scoped.setattr(os, "getpid", swallowed_reentry)
        if window == "first":
            for name in ("open", "read", "fstat", "stat", "close"):
                scoped.setattr(os, name, denied)
        else:
            scoped.setattr(os, "open", capture_root)
            scoped.setattr(os, "close", close_owned)
        with pytest.raises(SourceFilesStopped, match="reentry") as caught:
            attempt.observe()
    assert injected and len(nested) == 1 and caught.value is nested[0]
    snapshot = attempt.snapshot()
    assert snapshot.consumed and not snapshot.completed
    assert snapshot.returned_opens == snapshot.close_attempts == snapshot.confirmed_closes
    if window == "first":
        assert snapshot.open_attempts == snapshot.read_calls == 0
        assert snapshot.observed == () and not root_closed
    else:
        assert root_closed and root_descriptor is not None
        assert len(snapshot.observed) == 8 and snapshot.returned_opens > 0
        with pytest.raises(OSError):
            os.fstat(root_descriptor)
    assert os.fstat(owned.fd).st_ino == owned.identity.inode
    assert_no_io_retry(attempt, monkeypatch)
