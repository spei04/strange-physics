"""One fixed bounded Journal writer; the caller owns reservation and atomic closure."""

from __future__ import annotations

import math
import os
import signal
from dataclasses import dataclass
from pathlib import Path

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import ExperimentRecord, Message
from strange_physics.journal import Journal
from strange_physics.laws import reference_registry
from strange_physics.publication_store import digest, raw
from strange_physics.purchase_execution_binding import BoundPurchase, validate_purchase_prefix
from strange_physics.purchase_execution_contracts import (
    PURCHASE_RESULT_BYTES,
    NativePurchaseAttemptContext,
    NativePurchaseInput,
    NativePurchaseJournalIdentity,
    NativePurchasePrefix,
    NativePurchaseRequest,
)
from strange_physics.purchase_journal import JournalEpochs
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import engine_fingerprint
from strange_physics.simulation import SimulationError, simulate
from strange_physics.study_ledger import StudyLedgerError
from strange_physics.workflow_io import read_bytes


class PurchaseWriterOutput(Message):
    record: ExperimentRecord
    context: NativePurchaseAttemptContext
    journal: NativePurchaseJournalIdentity


@dataclass(frozen=True)
class PurchaseWriterObservation:
    """Unavailable wait4 usage is None; confirmed reap gates the separate holder."""

    reaped: bool
    cpu_ns: int | None
    status: int | None
    output: bytes | None
    error: BaseException | None


def _identity(path: Path) -> NativePurchaseJournalIdentity:
    value = read_bytes(path, limit=128 * 1024)
    return NativePurchaseJournalIdentity(sha256=digest(value), byte_count=len(value))


def _write_file(path: Path, value: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(value)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("short purchase output")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_purchase(
    actual: NativePurchaseInput,
    request: NativePurchaseRequest,
    bound: BoundPurchase,
    prefix: NativePurchasePrefix,
    *,
    engine: str,
    journal: Journal,
    observed: NativePurchaseJournalIdentity | None,
) -> tuple[ExperimentRecord, NativePurchaseAttemptContext]:
    validate_purchase_prefix(actual, prefix)
    run, world, fingerprint = journal.configuration()
    if (run, message_sha256(world), fingerprint) != (
        bound.journal_id,
        message_sha256(bound.world),
        engine,
    ):
        raise StudyLedgerError("purchase_journal_identity")
    records, pending = journal.records(), journal.pending()
    if tuple(message_sha256(r) for r in records[: len(prefix.records)]) != tuple(
        message_sha256(r) for r in prefix.records
    ):
        raise StudyLedgerError("purchase_original_prefix")
    own = actual.purchase
    terminal = len(records) == own.ordinal + 1 and not pending
    missing = len(records) == own.ordinal and not pending
    waiting = (
        len(records) == own.ordinal
        and len(pending) == 1
        and pending[0][0] == own.operation_id
        and message_sha256(pending[0][1]) == own.experiment_sha256
    )
    if not (terminal or missing or waiting):
        raise StudyLedgerError("purchase_current_prefix")
    if journal.used != own.ordinal + int(terminal or waiting):
        raise StudyLedgerError("purchase_current_prefix")
    context = NativePurchaseAttemptContext(
        attempt_id=request.attempt_id,
        observed_journal=observed,
        original_prefix_sha256=message_sha256(prefix),
        row_state="terminal" if terminal else "pending" if waiting else "missing",
    )
    if request.purpose == "reconciliation":
        if not terminal:
            raise StudyLedgerError("purchase_reconciliation_not_terminal")
        record = records[-1]
    else:
        if terminal:
            raise StudyLedgerError("purchase_requires_reconciliation")
        if waiting and request.retry_of is None:
            raise StudyLedgerError("purchase_pending_requires_retry")
        reservation = journal.reserve(own.operation_id, actual.experiment, 12)
        if reservation.index != own.ordinal or reservation.record is not None:
            raise StudyLedgerError("purchase_current_prefix")
        registry = reference_registry()
        if engine_fingerprint(registry) != engine:
            raise StudyLedgerError("purchase_execution_engine")
        law = registry.build(bound.world.law_at(own.ordinal))
        try:
            trajectory = simulate(
                bound.world.space,
                actual.experiment,
                law,
                noise_seed=bound.world.noise_seed,
                experiment_index=own.ordinal,
            )
        except SimulationError:
            # Only the declared scientific failure produces a terminal failed row.
            journal.record_failure(own.operation_id, "SimulationError", [])
            record = ExperimentRecord(
                operation_id=own.operation_id,
                index=own.ordinal,
                experiment=actual.experiment,
                status="failed",
                error="simulation_failed",
            )
        else:
            record = ExperimentRecord(
                operation_id=own.operation_id,
                index=own.ordinal,
                experiment=actual.experiment,
                status="completed",
                trajectory=trajectory,
            )
        record = journal.commit(record)
    if (
        record.operation_id != own.operation_id
        or record.index != own.ordinal
        or message_sha256(record.experiment) != own.experiment_sha256
    ):
        raise StudyLedgerError("purchase_record_identity")
    return record, context


def run_purchase_writer(
    actual: NativePurchaseInput,
    request: NativePurchaseRequest,
    bound: BoundPurchase,
    prefix: NativePurchasePrefix,
    output: Path,
    before_path: Path,
    *,
    engine: str,
    epochs: JournalEpochs,
    deadline_ns: int,
) -> PurchaseWriterObservation:
    """No arbitrary producer/SQL. Must be called only after durable reservation."""
    budget = epochs.writer(deadline_ns)
    try:
        pid = os.fork()
    except BaseException:
        budget.close()
        raise
    if pid == 0:
        code = 70
        try:
            # Install before any Journal/file access; never raise this limit later.
            signal.signal(signal.SIGPROF, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_PROF, request.cpu_reservation_ns / 2e9)
            budget.install(cpu_seconds=math.ceil(request.cpu_reservation_ns / 2e9))
            path = Path(actual.journal_path)
            exists = path.exists()
            if not exists and (actual.purchase.ordinal != 0 or request.purpose == "reconciliation"):
                raise StudyLedgerError("purchase_journal_missing")
            if (
                exists
                and actual.purchase.ordinal == 0
                and (request.retry_of is None and request.purpose == "execution")
            ):
                raise StudyLedgerError("purchase_initial_absence")
            journal = Journal(path, create=not exists, bounded=budget)
            try:
                if not exists:
                    journal.initialize(bound.journal_id, bound.world, engine)
                observed = None
                if exists:
                    before_raw = read_bytes(path, limit=128 * 1024)
                    _write_file(before_path, before_raw)
                    observed = NativePurchaseJournalIdentity(
                        sha256=digest(before_raw), byte_count=len(before_raw)
                    )
                record, context = _write_purchase(
                    actual,
                    request,
                    bound,
                    prefix,
                    engine=engine,
                    journal=journal,
                    observed=observed,
                )
            finally:
                journal.close()
            result = PurchaseWriterOutput(record=record, context=context, journal=_identity(path))
            data = raw(result)
            if len(data) > min(request.output_limit_bytes, PURCHASE_RESULT_BYTES):
                raise StudyLedgerError("purchase_child_output_limit")
            _write_file(output, data)
            code = 0
        except BaseException:
            code = 70
        finally:
            os._exit(code)
    status = None
    cpu = None
    reaped = False
    failure: BaseException | None = None
    try:
        budget.close()
        _, status, usage = os.wait4(pid, 0)
        reaped = True
        cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
    except BaseException as error:
        failure = error
        # Ownership may already be gone after an ambiguous wait error. Never
        # signal this PID again. The fixed child retains its original absolute
        # deadline; one further wait may recover observations without a new lease.
        try:
            _, status, usage = os.wait4(pid, 0)
            reaped = True
            cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
        except BaseException:
            error.add_note("Purchase child status/usage unavailable; original allowance retained.")
    captured_output: bytes | None = None
    if (
        failure is None
        and reaped
        and status is not None
        and os.WIFEXITED(status)
        and (os.WEXITSTATUS(status) == 0)
    ):
        try:
            captured_output = read_bytes(
                output, limit=min(request.output_limit_bytes, PURCHASE_RESULT_BYTES)
            )
            parse_bounded_json(
                captured_output,
                PurchaseWriterOutput,
                max_bytes=PURCHASE_RESULT_BYTES,
                max_depth=40,
                max_nodes=100_000,
            )
        except BaseException as error:
            failure = error
    return PurchaseWriterObservation(reaped, cpu, status, captured_output, failure)
