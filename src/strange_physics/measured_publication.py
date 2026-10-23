"""Measured early/scored publication, atomic private closure, and original replay.

This Linux-only owner-local producer performs composition, never numerical work.
The caller retains a finite control admission before invoking it. No initializer,
budget reset, arbitrary worker, provider, or network dispatch is exposed here.
"""

from __future__ import annotations

import math
import os
import resource
import signal
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, TypedDict

from pydantic import Field

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.measured_publication_contracts import (
    MIB,
    NativePublicationRequest,
    PublicationAdmission,
    PublicationMeasurements,
)
from strange_physics.publication_store import (
    Extents,
    LockedJournal,
    Store,
    digest,
    durable_directory,
    head,
    journal_snapshot,
    raw,
    regular,
    root_lock,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_contracts import (
    MAX_STUDY_JSON_BYTES,
    NativeStudyLedger,
    NativeWorkFacts,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_early import propose_study_early_stop
from strange_physics.study_journal import MAX_JOURNAL_BYTES
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    read_study_ledger,
    study_manifest,
    summarize_study,
)
from strange_physics.study_publication import propose_study_publication
from strange_physics.study_publication_contracts import StudyPublicationReceipt
from strange_physics.workflow_io import private_stat, read_bytes, safe_path

VERSION = "strange-physics.measured-publication.v1"
REQUEST_BYTES = 128 * 1024


class _Output(Message):
    ledger: NativeStudyLedger
    evidence_json: Annotated[str, Field(min_length=1, max_length=32 * MIB)]
    receipt: StudyPublicationReceipt
    replayed: bool


@dataclass(frozen=True)
class CommittedNativePublication:
    receipt: StudyPublicationReceipt
    evidence_raw: bytes
    ledger: NativeStudyLedger
    measurements: PublicationMeasurements
    replayed: bool


def _identity(request: NativePublicationRequest) -> str:
    # Paths and retry limits are transport/admission metadata, not scientific input.
    return digest(
        canonical_json(
            {
                "mode": request.mode,
                "event_id": request.event_id,
                "cell_id": request.cell_id,
                "journal_sha256": request.journal_sha256,
                "diagnostic_attempt_id": request.diagnostic_attempt_id,
                "files": sorted((f.name, f.sha256, f.byte_count) for f in request.files),
            }
        ).encode()
    )


class _Clock:
    """Disjoint parent control/work CPU budgets; settling work cannot fund cleanup."""

    def __init__(
        self, control: int, work: int, control_wall: int, work_wall: int, started: int
    ) -> None:
        self.control_limit = control
        self.work_limit = work
        self.control_wall_limit = control_wall
        self.work_wall_limit = work_wall
        self.control_wall_used = 0
        self.phase_wall_started = time.monotonic_ns()
        self.wall_deadline = self.phase_wall_started + min(control_wall, work_wall)
        self.phase = "control"
        self.phase_started = started
        self.control_used = 0
        self.work_cpu = 0
        self.work_wall = 0
        self.work_started_wall = 0
        self.exhausted = False

    def _arm(self, amount: int, wall: int) -> None:
        wall = min(wall, self.wall_deadline - time.monotonic_ns())
        if amount <= 0 or wall <= 0:
            self.exhausted = True
            raise StudyLedgerError("publication_control_deadline")
        signal.setitimer(signal.ITIMER_PROF, amount / 1e9)
        signal.setitimer(signal.ITIMER_REAL, wall / 1e9)

    def start(self) -> None:
        self._arm(
            self.control_limit - (time.process_time_ns() - self.phase_started),
            self.control_wall_limit - (time.monotonic_ns() - self.phase_wall_started),
        )

    def work(self) -> None:
        now = time.process_time_ns()
        self.control_used = now - self.phase_started
        self.control_wall_used = time.monotonic_ns() - self.phase_wall_started
        if self.control_used >= self.control_limit:
            raise StudyLedgerError("publication_control_deadline")
        self.phase = "work"
        self.phase_started = now
        self.work_started_wall = time.monotonic_ns()
        self._arm(self.work_limit, self.work_wall_limit)

    def tail(self) -> bool:
        if self.phase == "work":
            now = time.process_time_ns()
            self.work_cpu = now - self.phase_started
            self.work_wall = time.monotonic_ns() - self.work_started_wall
            self.phase = "control"
            self.phase_started = now
            self.exhausted = False
            self._arm(
                self.control_limit - self.control_used,
                self.control_wall_limit - self.control_wall_used,
            )
        return not self.exhausted


@contextmanager
def _deadline(
    control_ns: int, work_ns: int, control_wall_ns: int, work_wall_ns: int, started: int
) -> Iterator[_Clock]:
    if threading.current_thread() is not threading.main_thread() or threading.active_count() != 1:
        raise StudyLedgerError("publication_process_required")
    if any(
        signal.getitimer(timer) != (0.0, 0.0) for timer in (signal.ITIMER_REAL, signal.ITIMER_PROF)
    ):
        raise StudyLedgerError("publication_timer_in_use")
    before = {sig: signal.getsignal(sig) for sig in (signal.SIGALRM, signal.SIGPROF)}
    clock = _Clock(control_ns, work_ns, control_wall_ns, work_wall_ns, started)

    def expired(signum: int, frame: object) -> None:
        clock.exhausted = True
        raise StudyLedgerError("publication_deadline")

    try:
        signal.signal(signal.SIGALRM, expired)
        signal.signal(signal.SIGPROF, expired)
        clock.start()
        yield clock
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.setitimer(signal.ITIMER_PROF, 0)
        for sig, handler in before.items():
            signal.signal(sig, handler)


def _admitted(
    root: Path, admission: PublicationAdmission, seed: NativeStudyLedger, ticket: int
) -> None:
    c = admission.control
    if str(root) != c.root or ticket >= c.tickets:
        raise StudyLedgerError("admission_identity")
    manifest = study_manifest(seed)
    if (message_sha256(seed.plan), manifest.source_commit, manifest.uv_lock_sha256) != (
        c.accounting_plan_sha256,
        c.source_commit,
        c.uv_lock_sha256,
    ):
        raise StudyLedgerError("admission_identity")
    rows = [
        r.event
        for r in seed.records
        if isinstance(r.event, StudyAttemptReservation) and r.event.attempt_id == c.attempt_id
    ]
    if len(rows) != 1:
        raise StudyLedgerError("control_hold_missing")
    r = rows[0]
    if (r.phase, r.operation, r.cell_id, r.config_sha256, r.input_sha256) != (
        "accounting",
        "accounting",
        None,
        message_sha256(c),
        c.accounting_plan_sha256,
    ):
        raise StudyLedgerError("control_hold_mismatch")
    if (
        r.cpu_reservation_ns < c.tickets * c.ticket_cpu_ns + 1_000_000_000
        or r.artifact_reservation_bytes < c.tickets * c.ticket_artifact_bytes + 16 * MIB
    ):
        raise StudyLedgerError("control_hold_insufficient")
    if any(
        isinstance(row.event, StudyAttemptUpdate) and row.event.attempt_id == c.attempt_id
        for row in seed.records
    ):
        raise StudyLedgerError("control_hold_not_retained")
    if summarize_study(seed).budget.over_limit:
        raise StudyLedgerError("budget_exhausted")


def _append(
    ledger: NativeStudyLedger, event_id: str, event: StudyAttemptReservation | StudyAttemptUpdate
) -> NativeStudyLedger:
    return append_study_attempt(
        ledger, event_id=event_id, event=event, expected_revision=len(ledger.records)
    )


def _payloads(request: NativePublicationRequest) -> dict[str, bytes]:
    result = {}
    for f in request.files:
        p = Path(f.path)
        regular(p)
        value = read_bytes(p, limit=f.byte_count)
        if len(value) != f.byte_count or digest(value) != f.sha256:
            raise StudyLedgerError("publication_material_identity")
        result[f.name] = value
    return result


class _ProposalArgs(TypedDict):
    event_id: str
    expected_revision: int
    expected_head_sha256: str
    cell_id: str
    original_ledger_raw: bytes | None
    original_evidence_raw: bytes | None


def _event_id(attempt: str, kind: str) -> str:
    return digest((VERSION + "/" + kind + "/" + attempt).encode())


def _compose(
    request: NativePublicationRequest,
    ledger_raw: bytes,
    snapshot: Path,
    payloads: dict[str, bytes],
    original: bytes | None,
    evidence: bytes | None,
) -> _Output:
    base = read_study_ledger(original if original is not None else ledger_raw)
    common: _ProposalArgs = dict(
        event_id=request.event_id,
        expected_revision=len(base.records),
        expected_head_sha256=head(base),
        cell_id=request.cell_id,
        original_ledger_raw=original,
        original_evidence_raw=evidence,
    )
    excluded = {"witnesses", "scoring_input", "scoring_result", "diagnostic_result"}
    materials = {name: value for name, value in payloads.items() if name not in excluded}
    if request.mode == "early":
        p = propose_study_early_stop(
            ledger_raw, snapshot, materials=materials, witnesses_raw=payloads["witnesses"], **common
        )
        return _Output(
            ledger=p.ledger,
            evidence_json=p.evidence_raw.decode(),
            receipt=p.receipt,
            replayed=p.replayed,
        )
    s = propose_study_publication(
        ledger_raw,
        snapshot,
        materials=materials,
        scoring_input_raw=payloads["scoring_input"],
        scoring_result_raw=payloads["scoring_result"],
        diagnostic_attempt_id=request.diagnostic_attempt_id,
        diagnostic_result_raw=payloads.get("diagnostic_result"),
        **common,
    )
    return _Output(
        ledger=s.ledger,
        evidence_json=s.evidence_raw.decode(),
        receipt=s.receipt,
        replayed=s.replayed,
    )


def _child(
    request: NativePublicationRequest,
    ledger_raw: bytes,
    snapshot: Path,
    payloads: dict[str, bytes],
    original: bytes | None,
    evidence: bytes | None,
    output: Path,
) -> int:
    """Exactly one fixed child, no shell/exec/plugin/numerical dispatch."""
    child_cpu_seconds = max(1, request.cpu_reservation_ns // 2 // 1_000_000_000)
    _, hard_cpu = resource.getrlimit(resource.RLIMIT_CPU)
    cpu_limit = (
        child_cpu_seconds
        if hard_cpu == resource.RLIM_INFINITY
        else min(child_cpu_seconds, hard_cpu)
    )
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, hard_cpu))
    signal.signal(signal.SIGXCPU, signal.SIG_DFL)
    _, hard_file = resource.getrlimit(resource.RLIMIT_FSIZE)
    file_limit = (
        request.output_limit_bytes
        if hard_file == resource.RLIM_INFINITY
        else min(request.output_limit_bytes, hard_file)
    )
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, hard_file))
    signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        result = raw(_compose(request, ledger_raw, snapshot, payloads, original, evidence))
        if len(result) > request.output_limit_bytes:
            return 2
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            view = memoryview(result)
            while view:
                n = os.write(fd, view)
                if n <= 0:
                    return 2
                view = view[n:]
            os.fsync(fd)
        finally:
            os.close(fd)
        return 0
    except Exception:
        # No parser payload, path, hidden-world material, or stack crosses this boundary.
        return 1


def _run_child(
    request: NativePublicationRequest,
    ledger_raw: bytes,
    snapshot: Path,
    payloads: dict[str, bytes],
    original: bytes | None,
    evidence: bytes | None,
    output: Path,
) -> tuple[_Output | None, int]:
    child_deadline = time.monotonic_ns() + int(
        signal.getitimer(signal.ITIMER_REAL)[0] * 1_000_000_000
    )
    pid = os.fork()
    if pid == 0:
        code = 70
        try:
            # Fork does not inherit interval timers. Bound orphaned children too.
            remaining_wall = child_deadline - time.monotonic_ns()
            if remaining_wall <= 0:
                os._exit(70)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_REAL, remaining_wall / 1e9)
            code = _child(request, ledger_raw, snapshot, payloads, original, evidence, output)
        except BaseException:
            code = 70
        finally:
            # Resource setup/import/encoding failures must never unwind into the
            # parent's store cleanup or the caller in this forked process.
            os._exit(code)
    reaped = False
    cpu = 0
    try:
        _, status, usage = os.wait4(pid, 0)
        reaped = True
        cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1_000_000_000)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            return None, cpu
        result = parse_bounded_json(
            read_bytes(output, limit=request.output_limit_bytes),
            _Output,
            max_bytes=request.output_limit_bytes,
            max_depth=48,
            max_nodes=4_000_000,
        )
        return result, cpu
    except Exception:
        if not reaped:
            os.kill(pid, signal.SIGKILL)
            _, _, usage = os.wait4(pid, 0)
            reaped = True
            cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1_000_000_000)
        # Successful reap followed by an unreadable/invalid result still has
        # known cost. The caller retains it under the unresolved reservation.
        return None, cpu
    finally:
        if not reaped:
            os.kill(pid, signal.SIGKILL)
            os.wait4(pid, 0)


def _closure(
    store: Store, request: NativePublicationRequest
) -> tuple[bytes, bytes | None, bytes, bytes] | None:
    lengths = store.db.execute(
        "SELECT length(request),length(original),length(journal),"
        "length(evidence),length(receipt) FROM closures WHERE event_id=?",
        (request.event_id,),
    ).fetchone()
    if lengths is None:
        return None
    if any(n is not None and (n < 1 or n > 128 * MIB) for n in lengths):
        raise StudyLedgerError("closure_corrupt")
    row = store.db.execute(
        "SELECT request_digest,request,original,journal,evidence,receipt,"
        "receipt_digest FROM closures WHERE event_id=?",
        (request.event_id,),
    ).fetchone()
    if row[0] != _identity(request) or digest(row[5]) != row[6]:
        raise StudyLedgerError("publication_conflict")
    saved = parse_bounded_json(
        row[1], NativePublicationRequest, max_bytes=REQUEST_BYTES, max_depth=12, max_nodes=1000
    )
    if _identity(saved) != row[0]:
        raise StudyLedgerError("closure_corrupt")
    if (None if row[3] is None else digest(row[3])) != request.journal_sha256:
        raise StudyLedgerError("closure_corrupt")
    return row[2], row[3], row[4], row[5]


def _stored_payloads(store: Store, request: NativePublicationRequest) -> dict[str, bytes]:
    rows = store.db.execute(
        "SELECT name,length(data),digest FROM materials WHERE event_id=?", (request.event_id,)
    ).fetchall()
    expected = {f.name: (f.byte_count, f.sha256) for f in request.files}
    if {name: (size, sha) for name, size, sha in rows} != expected:
        raise StudyLedgerError("closure_corrupt")
    values = dict(
        store.db.execute(
            "SELECT name,data FROM materials WHERE event_id=?", (request.event_id,)
        ).fetchall()
    )
    if any(digest(v) != expected[k][1] for k, v in values.items()):
        raise StudyLedgerError("closure_corrupt")
    return values


def commit_native_publication(
    store_root: Path, request: NativePublicationRequest
) -> CommittedNativePublication:
    """Consume one retained ticket, reserve work, and atomically commit or replay.

    Pre-admission validation is a caller responsibility, not a free scientific
    attempt. Any admitted crash leaves durable holds. Only an exact retained
    closure may replay; a real retry uses a fresh ticket and attempt identity.
    """
    started_cpu = time.process_time_ns()
    bounded_canonical(request, REQUEST_BYTES)
    request = NativePublicationRequest.model_validate_json(raw(request))
    root = safe_path(store_root)
    private_stat(root.stat(), directory=True)
    admission = parse_bounded_json(
        read_bytes(root / "admission.json", limit=16 * 1024),
        PublicationAdmission,
        max_bytes=16 * 1024,
        max_depth=8,
        max_nodes=128,
    )
    if str(root) != admission.control.root or request.ticket >= admission.control.tickets:
        raise StudyLedgerError("admission_identity")
    control = admission.control
    with _deadline(
        control.ticket_cpu_ns,
        request.cpu_reservation_ns // 2,
        control.ticket_wall_ns,
        request.wall_limit_ns,
        started_cpu,
    ) as clock:
        meter = Extents(root)
        # Exclusive durable ticket consumption precedes lock/store open. Contention
        # consumes a ticket too; no caller can restart on one unknown hold forever.
        ticket_path = root / f"ticket-{request.ticket}"
        try:
            meter.write(ticket_path, raw(request))
        except FileExistsError:
            raise StudyLedgerError("publication_ticket_consumed") from None
        durable_directory(root)
        store: Store | None = None
        work_extent = 0
        work_artifact_bytes: int | None = None
        reservation: StudyAttemptReservation | None = None
        child_cpu = 0
        output_path: Path | None = None
        scratch: Path | None = None
        try:
            with root_lock(root):
                seed_raw = read_bytes(root / "seed-ledger.json", limit=MAX_STUDY_JSON_BYTES)
                if digest(seed_raw) != admission.seed_ledger_sha256:
                    raise StudyLedgerError("admission_identity")
                seed = read_study_ledger(seed_raw)
                _admitted(root, admission, seed, request.ticket)
                store = Store(root, admission, seed_raw, meter)
                current = store.ledger()
                if (
                    current.plan != seed.plan
                    or current.records[: len(seed.records)] != seed.records
                ):
                    raise StudyLedgerError("store_seed_prefix")
                held: dict[str, StudyAttemptReservation] = {}
                for record in current.records:
                    entry = record.event
                    if isinstance(entry, StudyAttemptReservation):
                        held[entry.attempt_id] = entry
                    elif isinstance(entry, StudyAttemptUpdate):
                        prior = held[entry.attempt_id]
                        if (entry.cpu_ns or 0) > prior.cpu_reservation_ns or (
                            entry.artifact_bytes or 0
                        ) > prior.artifact_reservation_bytes:
                            raise StudyLedgerError("publication_measurement_overrun")
                # A supplied seed cannot release the immutable controller hold.
                if any(
                    isinstance(r.event, StudyAttemptUpdate)
                    and r.event.attempt_id == control.attempt_id
                    for r in current.records
                ):
                    raise StudyLedgerError("control_hold_not_retained")
                closure = _closure(store, request)
                event = next((r for r in current.records if r.event_id == request.event_id), None)
                if (closure is None) != (event is None):
                    raise StudyLedgerError("closure_corrupt")
                if closure is None and (len(current.records), head(current)) != (
                    request.expected_revision,
                    request.expected_head_sha256,
                ):
                    raise StudyLedgerError("stale_publication_head")
                if any(
                    isinstance(r.event, StudyAttemptReservation)
                    and r.event.attempt_id == request.attempt_id
                    for r in current.records
                ):
                    raise StudyLedgerError("publication_attempt_reused")
                if (
                    time.process_time_ns() - started_cpu > control.ticket_cpu_ns
                    or meter.total > control.ticket_artifact_bytes
                ):
                    raise StudyLedgerError("control_allowance_overrun")
                reservation = StudyAttemptReservation(
                    attempt_id=request.attempt_id,
                    phase="accounting",
                    operation="accounting",
                    cell_id=None,
                    config_sha256=message_sha256(control),
                    input_sha256=_identity(request),
                    retry_of=None,
                    cpu_reservation_ns=request.cpu_reservation_ns,
                    artifact_reservation_bytes=request.artifact_reservation_bytes,
                    purchase=None,
                )
                reserved = _append(current, _event_id(request.attempt_id, "reserve"), reservation)
                # Include record/closure/finalization space before snapshot or child work.
                original_bytes = len(raw(reserved))
                journal_size = 0 if request.journal_sha256 is None else MAX_JOURNAL_BYTES
                if closure is not None:
                    journal_size = len(closure[1] or b"")
                else:
                    info = regular(Path(request.journal_path), missing=True)
                    journal_size = 0 if info is None else info.st_size
                required = (
                    4
                    * (
                        sum(f.byte_count for f in request.files)
                        + journal_size
                        + original_bytes
                        + request.output_limit_bytes
                    )
                    + 4 * MIB
                )
                if required > request.artifact_reservation_bytes:
                    raise StudyLedgerError("publication_artifact_headroom")
                store.limit_growth(control.ticket_artifact_bytes - meter.total)
                with store.transaction():
                    store.replace(current, reserved)
                current = reserved
                if meter.total > control.ticket_artifact_bytes:
                    raise StudyLedgerError("control_allowance_overrun")
                try:
                    clock.work()
                    work_extent = meter.total
                    store.limit_growth(
                        request.artifact_reservation_bytes
                        - journal_size
                        - request.output_limit_bytes
                    )
                    scratch = root / f"work-{request.ticket}"
                    scratch.mkdir(mode=0o700)
                    durable_directory(root)
                    snapshot = scratch / "journal.sqlite3"
                    output_path = scratch / "output.json"
                    original = None if closure is None else closure[0]
                    original_evidence = None if closure is None else closure[2]
                    payloads = (
                        _payloads(request) if closure is None else _stored_payloads(store, request)
                    )
                    snapshots = (
                        journal_snapshot(Path(request.journal_path), request.journal_sha256)
                        if closure is None
                        else nullcontext(
                            LockedJournal(Path(request.journal_path), None, closure[1])
                        )
                    )
                    with snapshots as locked:
                        journal_raw = locked.original
                        if journal_raw is not None:
                            meter.write(snapshot, journal_raw)
                        result, child_cpu = _run_child(
                            request,
                            raw(current),
                            snapshot,
                            payloads,
                            original,
                            original_evidence,
                            output_path,
                        )
                        if output_path.exists():
                            meter.total += output_path.stat().st_size
                        if result is None:
                            raise StudyLedgerError("publication_child_failed")
                        actual = read_study_ledger(raw(result.ledger))
                        if result.replayed != (closure is not None):
                            raise StudyLedgerError("publication_result_mismatch")
                        evidence_raw, receipt_raw = (
                            result.evidence_json.encode(),
                            raw(result.receipt),
                        )
                        if closure is not None and (evidence_raw, receipt_raw) != (
                            closure[2],
                            closure[3],
                        ):
                            raise StudyLedgerError("closure_corrupt")
                        if closure is None:
                            if (
                                result.receipt.original_revision,
                                result.receipt.original_head_sha256,
                                result.receipt.original_ledger_identity.raw_sha256,
                            ) != (len(current.records), head(current), digest(raw(current))):
                                raise StudyLedgerError("publication_result_mismatch")
                            with store.transaction():
                                # Pread the retained descriptor; a same-inode close
                                # here would silently cancel SQLite's POSIX locks.
                                locked.recheck()
                                store.replace(current, actual)
                                store.db.execute(
                                    "INSERT INTO closures VALUES (?,?,?,?,?,?,?,?)",
                                    (
                                        request.event_id,
                                        _identity(request),
                                        raw(request),
                                        raw(current),
                                        journal_raw,
                                        evidence_raw,
                                        receipt_raw,
                                        digest(receipt_raw),
                                    ),
                                )
                                store.db.executemany(
                                    "INSERT INTO materials VALUES (?,?,?,?)",
                                    [
                                        (request.event_id, n, v, digest(v))
                                        for n, v in payloads.items()
                                    ],
                                )
                            current = actual
                        elif raw(actual) != raw(current):
                            raise StudyLedgerError("publication_result_mismatch")
                    clock.tail()
                    meter.sample()
                    work_artifact_bytes = meter.total - work_extent
                    store.limit_growth(
                        control.ticket_artifact_bytes - (meter.total - work_artifact_bytes)
                    )
                    measured = PublicationMeasurements(
                        parent_cpu_ns=clock.work_cpu,
                        child_cpu_ns=child_cpu,
                        wall_ns=clock.work_wall,
                        created_artifact_bytes=work_artifact_bytes,
                        control_parent_cpu_ns=clock.control_used,
                        control_created_artifact_bytes=work_extent,
                    )
                    overrun = (
                        measured.parent_cpu_ns + child_cpu > request.cpu_reservation_ns
                        or measured.created_artifact_bytes > request.artifact_reservation_bytes
                    )
                    facts = NativeWorkFacts(
                        attempt_id=request.attempt_id,
                        operation="accounting",
                        producer_version=VERSION,
                        config_sha256=reservation.config_sha256,
                        input_sha256=reservation.input_sha256,
                        observation_sha256=None,
                        model_sha256=None,
                        output_sha256=digest(receipt_raw),
                        unit="record",
                        requested_count=1,
                        completed_count=1,
                        failed_count=0,
                        not_assessed_count=0,
                        outcome="completed",
                    )
                    update = StudyAttemptUpdate(
                        attempt_id=request.attempt_id,
                        state="unknown" if overrun else "completed",
                        cpu_ns=measured.parent_cpu_ns + child_cpu,
                        wall_ns=measured.wall_ns,
                        artifact_bytes=measured.created_artifact_bytes,
                        facts=facts,
                    )
                    settled = _append(current, _event_id(request.attempt_id, "measure"), update)
                    with store.transaction():
                        store.replace(current, settled)
                    if overrun:
                        raise StudyLedgerError("publication_measurement_overrun")
                    return CommittedNativePublication(
                        result.receipt, evidence_raw, settled, measured, result.replayed
                    )
                except Exception as error:
                    try:
                        if clock.tail() and clock.work_started_wall:
                            meter.sample()
                            if work_artifact_bytes is None:
                                work_artifact_bytes = meter.total - work_extent
                            # A failed settlement can itself grow retained extents.
                            # Never fund its fallback with the same bytes twice.
                            store.limit_growth(
                                control.ticket_artifact_bytes - (meter.total - work_artifact_bytes)
                            )
                            latest = store.ledger()
                            if not any(
                                isinstance(row.event, StudyAttemptUpdate)
                                and row.event.attempt_id == request.attempt_id
                                for row in latest.records
                            ):
                                meter.sample()
                                failed = StudyAttemptUpdate(
                                    attempt_id=request.attempt_id,
                                    state="unknown",
                                    cpu_ns=clock.work_cpu + child_cpu,
                                    wall_ns=clock.work_wall,
                                    artifact_bytes=work_artifact_bytes,
                                    facts=None,
                                )
                                measured_failure = _append(
                                    latest, _event_id(request.attempt_id, "measure"), failed
                                )
                                with store.transaction():
                                    store.replace(latest, measured_failure)
                    except Exception:
                        # Storage exhaustion or an expired control allowance may
                        # prevent this write. The original durable hold survives.
                        error.add_note("Known-cost recording failed; original work hold retained.")
                    raise

        finally:
            # The measurement's unresolved controller hold covers cleanup, final
            # update, close and acknowledgement; it is never declared exact zero.
            cleanup = clock.tail()
            if cleanup and store is not None:
                store.close()
            if cleanup and scratch is not None:
                for name in ("output.json", "journal.sqlite3"):
                    p = scratch / name
                    if p.exists():
                        p.unlink()
                scratch.rmdir()
                durable_directory(root)
