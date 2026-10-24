"""Fixed owner-local candidate production and paid exact-result recovery.

This first vertical has no comparison Journal adapter, purchase, selector or
handoff dispatcher. Control holds remain unresolved, never exact zero costs.
"""

from __future__ import annotations

import math
import os
import resource
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.candidate_execution_contracts import (
    MIB,
    REQUEST_BYTES,
    CandidateAdmission,
    CandidateControl,
    CandidateMeasurements,
    CandidateReceipt,
    CandidateRequest,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.installed_identity import TrustedInstallation, verify_native_installation
from strange_physics.measured_publication import _deadline
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeCandidateResult,
    parse_native_candidate_input,
    parse_native_candidate_result,
    validate_native_candidate_result,
)
from strange_physics.native_stage_dispatch import (
    StageInput,
    StageResult,
    observation_engine,
    parse_stage_input,
    parse_stage_result,
    produce_stage,
    stage_config,
    validate_stage,
)
from strange_physics.native_stage_execution_contracts import (
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
    NativeStageReceipt,
)
from strange_physics.publication_store import (
    Extents,
    digest,
    durable_directory,
    head,
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
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    read_study_ledger,
    study_manifest,
    summarize_study,
)
from strange_physics.workflow_io import private_stat, read_bytes, safe_path

VERSION = "strange-physics.measured-candidates.v1"


type ExecutionRequest = (
    CandidateRequest | NativePreparationRequest | NativePredictionRequest | NativeScoreRequest
)
type ExecutionReceipt = CandidateReceipt | NativeStageReceipt
type ExecutionInput = NativeCandidateInput | StageInput
type ExecutionResult = NativeCandidateResult | StageResult


@dataclass(frozen=True)
class CommittedCandidate:
    receipt: CandidateReceipt
    result: NativeCandidateResult
    result_raw: bytes
    original_ledger: NativeStudyLedger
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements
    replayed: bool


@dataclass(frozen=True)
class _CommittedExecution:
    receipt: ExecutionReceipt
    result: ExecutionResult
    result_raw: bytes
    original_ledger: NativeStudyLedger
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements
    replayed: bool


def _request(data: bytes, operation: str) -> ExecutionRequest:
    if operation == "candidate_production":
        model = CandidateRequest
    elif operation == "preparation":
        return parse_bounded_json(
            data, NativePreparationRequest, max_bytes=REQUEST_BYTES, max_depth=8, max_nodes=128
        )
    elif operation == "prediction":
        return parse_bounded_json(
            data, NativePredictionRequest, max_bytes=REQUEST_BYTES, max_depth=8, max_nodes=128
        )
    elif operation == "scoring":
        return parse_bounded_json(
            data, NativeScoreRequest, max_bytes=REQUEST_BYTES, max_depth=8, max_nodes=128
        )
    else:
        raise StudyLedgerError("native_stage_operation")
    return parse_bounded_json(data, model, max_bytes=REQUEST_BYTES, max_depth=8, max_nodes=128)


def _receipt(data: bytes, request: ExecutionRequest) -> ExecutionReceipt:
    if request.operation == "candidate_production":
        return parse_bounded_json(
            data, CandidateReceipt, max_bytes=8192, max_depth=8, max_nodes=128
        )
    value = parse_bounded_json(data, NativeStageReceipt, max_bytes=8192, max_depth=8, max_nodes=128)
    if value.operation != request.operation:
        raise StudyLedgerError("candidate_closure_corrupt")
    return value


def _input_limit(request: ExecutionRequest) -> int:
    return (8 if request.operation in ("candidate_production", "prediction") else 16) * MIB


def _result_limit(request: ExecutionRequest) -> int:
    return (4 if request.operation in ("candidate_production", "prediction") else 8) * MIB


def _input(data: bytes, request: ExecutionRequest) -> ExecutionInput:
    if request.operation == "candidate_production":
        return parse_native_candidate_input(data)
    return parse_stage_input(request.operation, data)


def _result(data: bytes, request: ExecutionRequest) -> ExecutionResult:
    if request.operation == "candidate_production":
        return parse_native_candidate_result(data)
    return parse_stage_result(request.operation, data)


def _config(actual: ExecutionInput) -> str:
    return (
        message_sha256(actual.config)
        if isinstance(actual, NativeCandidateInput)
        else stage_config(actual)
    )


def _check_engine(actual: ExecutionInput, expected: str) -> None:
    engine = (
        actual.observations.engine_fingerprint
        if isinstance(actual, NativeCandidateInput)
        else observation_engine(actual)
    )
    if engine is not None and engine != expected:
        raise StudyLedgerError("candidate_observation_engine")


def _validate(result: ExecutionResult, actual: ExecutionInput, attempt_id: str) -> None:
    if isinstance(result, NativeCandidateResult) and isinstance(actual, NativeCandidateInput):
        validate_native_candidate_result(result, actual, attempt_id=attempt_id)
    elif not isinstance(result, NativeCandidateResult) and not isinstance(
        actual, NativeCandidateInput
    ):
        validate_stage(result, actual, attempt_id)
    else:
        raise StudyLedgerError("candidate_result_identity")


def _identity(request: ExecutionRequest) -> str:
    return digest(
        canonical_json(
            {
                "operation": request.operation,
                "logical_id": request.logical_id,
                "phase": request.phase,
                "cell_id": request.cell_id,
                "input_raw_sha256": request.input_raw_sha256,
                "input_bytes": request.input_bytes,
                "input_sha256": request.input_sha256,
                "config_sha256": request.config_sha256,
            }
        ).encode()
    )


def _event(attempt: str, kind: str) -> str:
    return "ce-" + digest((attempt + ":" + kind).encode())[:60]


def _append(
    ledger: NativeStudyLedger, value: StudyAttemptReservation | StudyAttemptUpdate
) -> NativeStudyLedger:
    return append_study_attempt(
        ledger,
        event_id=_event(value.attempt_id, value.kind),
        event=value,
        expected_revision=len(ledger.records),
    )


def _admitted(
    root: Path, admission: CandidateAdmission, seed: NativeStudyLedger, current: NativeStudyLedger
) -> None:
    c = admission.control
    if str(root) != c.root or message_sha256(seed.plan) != c.plan_sha256:
        raise StudyLedgerError("candidate_admission_identity")
    if current.plan != seed.plan or current.records[: len(seed.records)] != seed.records:
        raise StudyLedgerError("candidate_seed_prefix")
    reserves = [
        r.event
        for r in seed.records
        if isinstance(r.event, StudyAttemptReservation) and r.event.attempt_id == c.attempt_id
    ]
    if len(reserves) != 1:
        raise StudyLedgerError("candidate_control_hold")
    r = reserves[0]
    if (
        (r.phase, r.cell_id, r.operation, r.config_sha256, r.input_sha256, r.retry_of, r.purchase)
        != ("accounting", None, "accounting", message_sha256(c), c.plan_sha256, None, None)
        or r.cpu_reservation_ns < c.tickets * c.ticket_cpu_ns + c.bootstrap_cpu_ns
        or (r.artifact_reservation_bytes < c.required_control_bytes())
    ):
        raise StudyLedgerError("candidate_control_hold")
    if any(
        isinstance(r.event, StudyAttemptUpdate) and r.event.attempt_id == c.attempt_id
        for r in current.records
    ):
        raise StudyLedgerError("candidate_control_released")


def _capacity(root: Path, ledger: NativeStudyLedger, c: CandidateControl) -> None:
    budget = summarize_study(ledger).budget
    used = sum(
        regular(root / f"candidate-ticket-{i}", missing=True) is not None
        for i in range(c.tickets - c.recovery_tickets, c.tickets)
    )
    extra_records = c.finalization_records - 2 * used
    extra_bytes = c.finalization_bytes - 8192 * used
    if (
        len(ledger.records) + budget.unresolved_attempts + extra_records > 8192
        or len(raw(ledger)) + budget.unresolved_attempts * 4096 + extra_bytes > MAX_STUDY_JSON_BYTES
    ):
        raise StudyLedgerError("candidate_finalization_headroom")
    remaining_recovery = c.recovery_tickets - used
    p = c.publication
    if (
        p.calls
        and len(raw(ledger)) + budget.unresolved_attempts * 4096 + extra_bytes > p.ledger_bytes
        or budget.remaining_artifact_bytes
        < p.required_bytes() + remaining_recovery * c.recovery_work_artifact_bytes
        or budget.remaining_cpu_ns
        < p.control_cpu_ns + p.work_cpu_ns + remaining_recovery * c.recovery_work_cpu_ns
    ):
        raise StudyLedgerError("candidate_protected_work_headroom")


def _bind_context(
    ledger: NativeStudyLedger, request: ExecutionRequest, c: CandidateControl
) -> None:
    if request.phase == "comparison":
        if request.operation != "candidate_production":
            raise StudyLedgerError("native_stage_comparison_not_available")
        manifest = study_manifest(ledger)
        if (manifest.source_commit, manifest.uv_lock_sha256, manifest.engine_fingerprint) != (
            c.source_commit,
            c.uv_lock_sha256,
            c.engine_fingerprint,
        ) or manifest.artifact("candidate_config").sha256 != request.config_sha256:
            raise StudyLedgerError("candidate_frozen_identity")
        # No supplied bundle is promoted to complete actual-Journal provenance.
        raise StudyLedgerError("candidate_comparison_not_available")


def _run_child(
    request: ExecutionRequest, actual_raw: bytes, output: Path
) -> tuple[bytes | None, int]:
    deadline = time.monotonic_ns() + int(signal.getitimer(signal.ITIMER_REAL)[0] * 1e9)
    pid = os.fork()
    if pid == 0:
        code = 70
        try:
            remaining = deadline - time.monotonic_ns()
            if remaining <= 0:
                os._exit(70)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.setitimer(signal.ITIMER_REAL, remaining / 1e9)
            seconds = max(1, request.cpu_reservation_ns // 2 // 1_000_000_000)
            _, hard = resource.getrlimit(resource.RLIMIT_CPU)
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (seconds if hard == resource.RLIM_INFINITY else min(seconds, hard), hard),
            )
            signal.signal(signal.SIGXCPU, signal.SIG_DFL)
            _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
            limit = request.output_limit_bytes
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (limit if hard == resource.RLIM_INFINITY else min(limit, hard), hard),
            )
            signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if request.operation == "candidate_production":
                actual = parse_native_candidate_input(actual_raw)
                result = raw(produce_native_candidates(actual, attempt_id=request.attempt_id))
            else:
                result = produce_stage(request.operation, actual_raw, request.attempt_id)
            if len(result) > limit:
                os._exit(2)
            fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                view = memoryview(result)
                while view:
                    n = os.write(fd, view)
                    if n <= 0:
                        os._exit(2)
                    view = view[n:]
                os.fsync(fd)
            finally:
                os.close(fd)
            code = 0
        except BaseException:
            code = 70
        finally:
            os._exit(code)
    reaped = False
    cpu = 0
    try:
        _, status, usage = os.wait4(pid, 0)
        reaped = True
        cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            return None, cpu
        return read_bytes(output, limit=request.output_limit_bytes), cpu
    except Exception:
        if not reaped:
            os.kill(pid, signal.SIGKILL)
            _, _, usage = os.wait4(pid, 0)
            reaped = True
            cpu = math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
        return None, cpu
    finally:
        if not reaped:
            os.kill(pid, signal.SIGKILL)
            os.wait4(pid, 0)


def _closure(
    store: CandidateStore, request: ExecutionRequest, current: NativeStudyLedger
) -> tuple[ExecutionReceipt, bytes, bytes, NativeStudyLedger] | None:
    row = store.db.execute(
        "SELECT identity,length(request),input_name,result_name,"
        "length(receipt),receipt_digest FROM closures WHERE logical_id=?",
        (request.logical_id,),
    ).fetchone()
    if row is None:
        return None
    if row[0] != _identity(request):
        raise StudyLedgerError("candidate_request_conflict")
    if not 0 < row[1] <= REQUEST_BYTES or not 0 < row[4] <= 8192:
        raise StudyLedgerError("candidate_closure_corrupt")
    saved_raw, receipt_raw = store.db.execute(
        "SELECT request,receipt FROM closures WHERE logical_id=?", (request.logical_id,)
    ).fetchone()
    saved = _request(saved_raw, request.operation)
    receipt = _receipt(receipt_raw, request)
    if _identity(saved) != row[0] or digest(receipt_raw) != row[5]:
        raise StudyLedgerError("candidate_closure_corrupt")
    if (row[2], row[3]) != (f"candidate-input-{saved.ticket}", f"candidate-output-{saved.ticket}"):
        raise StudyLedgerError("candidate_closure_corrupt")
    input_raw = read_bytes(store.root / row[2], limit=_input_limit(saved))
    result_raw = read_bytes(store.root / row[3], limit=_result_limit(saved))
    if (
        digest(input_raw),
        len(input_raw),
        digest(result_raw),
        receipt.request_sha256,
        receipt.logical_id,
        receipt.original_attempt_id,
        receipt.input_raw_sha256,
    ) != (
        request.input_raw_sha256,
        request.input_bytes,
        receipt.result_raw_sha256,
        row[0],
        request.logical_id,
        saved.attempt_id,
        request.input_raw_sha256,
    ):
        raise StudyLedgerError("candidate_closure_corrupt")
    if (
        saved.mode != "execute"
        or receipt.original_revision != saved.expected_revision + 1
        or receipt.original_revision > len(current.records)
    ):
        raise StudyLedgerError("candidate_closure_corrupt")
    original = NativeStudyLedger(
        plan=current.plan, records=current.records[: receipt.original_revision]
    )
    if (head(original), digest(raw(original))) != (
        receipt.original_head_sha256,
        receipt.original_ledger_sha256,
    ):
        raise StudyLedgerError("candidate_closure_corrupt")
    before = NativeStudyLedger(plan=current.plan, records=original.records[:-1])
    reservation = original.records[-1].event
    expected_reservation = StudyAttemptReservation(
        attempt_id=saved.attempt_id,
        phase=saved.phase,
        cell_id=saved.cell_id,
        operation=saved.operation,
        config_sha256=saved.config_sha256,
        input_sha256=saved.input_sha256,
        retry_of=saved.retry_of,
        cpu_reservation_ns=saved.cpu_reservation_ns,
        artifact_reservation_bytes=saved.artifact_reservation_bytes,
        purchase=None,
    )
    if head(before) != saved.expected_head_sha256 or reservation != expected_reservation:
        raise StudyLedgerError("candidate_closure_corrupt")
    updates = [
        r.event
        for r in current.records
        if isinstance(r.event, StudyAttemptUpdate)
        and r.event.attempt_id == receipt.original_attempt_id
    ]
    result = _result(result_raw, request)
    if (
        not updates
        or updates[0].facts is None
        or (message_sha256(updates[0].facts) != message_sha256(result.facts))
    ):
        raise StudyLedgerError("candidate_closure_corrupt")
    return receipt, input_raw, result_raw, original


def _commit_native_execution(
    store_root: Path, request: ExecutionRequest, *, expected_operation: str
) -> _CommittedExecution:
    """Tiny ingress precedes a finite ticket; no automatic retry or free replay."""
    started = time.process_time_ns()
    bounded_canonical(request, REQUEST_BYTES)
    request = _request(raw(request), expected_operation)
    root = safe_path(store_root)
    private_stat(root.stat(), directory=True)
    admission_raw = read_bytes(root / "candidate-admission.json", limit=16 * 1024)
    admission = parse_bounded_json(
        admission_raw, CandidateAdmission, max_bytes=16 * 1024, max_depth=12, max_nodes=256
    )
    c = admission.control
    if str(root) != c.root or request.ticket >= c.tickets:
        raise StudyLedgerError("candidate_admission_identity")
    if (request.ticket >= c.tickets - c.recovery_tickets) != (request.mode == "recover"):
        raise StudyLedgerError("candidate_ticket_scope")
    if request.mode == "recover" and (
        request.cpu_reservation_ns > c.recovery_work_cpu_ns
        or request.artifact_reservation_bytes > c.recovery_work_artifact_bytes
    ):
        raise StudyLedgerError("candidate_recovery_work_limit")
    with _deadline(
        c.ticket_cpu_ns,
        request.cpu_reservation_ns // 2,
        c.ticket_wall_ns,
        request.wall_limit_ns,
        started,
    ) as clock:
        meter = Extents(root, database_name="candidate.sqlite3")
        ticket = raw(request)
        if len(ticket) > c.ticket_artifact_bytes:
            raise StudyLedgerError("candidate_ticket_limit")
        try:
            meter.write(root / f"candidate-ticket-{request.ticket}", ticket)
        except FileExistsError:
            raise StudyLedgerError("candidate_ticket_consumed") from None
        durable_directory(root)
        store: CandidateStore | None = None
        child_cpu = 0
        work_start = 0
        work_bytes: int | None = None
        reservation: StudyAttemptReservation | None = None
        output = root / f"candidate-output-{request.ticket}"
        output_counted = False
        try:
            with root_lock(root):
                seed_raw = read_bytes(root / "candidate-seed.json", limit=MAX_STUDY_JSON_BYTES)
                build_raw = read_bytes(root / "candidate-installation.json", limit=2 * MIB)
                if digest(seed_raw) != admission.seed_ledger_sha256:
                    raise StudyLedgerError("candidate_admission_identity")
                if (
                    len(seed_raw) + len(build_raw) + len(admission_raw) + 64
                    > c.bootstrap_artifact_bytes
                ):
                    raise StudyLedgerError("candidate_bootstrap_artifacts")
                seed = read_study_ledger(seed_raw)
                _admitted(root, admission, seed, seed)
                build = parse_bounded_json(
                    build_raw, TrustedInstallation, max_bytes=2 * MIB, max_depth=8, max_nodes=100000
                )
                if message_sha256(build) != c.installation_sha256:
                    raise StudyLedgerError("candidate_installation_identity")
                observed = verify_native_installation(build)
                if (
                    observed.source_commit,
                    observed.uv_lock_sha256,
                    observed.engine_fingerprint,
                ) != (c.source_commit, c.uv_lock_sha256, c.engine_fingerprint):
                    raise StudyLedgerError("candidate_installation_identity")
                store = CandidateStore(root, admission, seed_raw, meter)
                current = store.ledger()
                _admitted(root, admission, seed, current)
                closure = _closure(store, request, current)
                if request.mode == "recover" and closure is None:
                    raise StudyLedgerError("candidate_receipt_missing")
                if request.mode == "execute" and closure is not None:
                    raise StudyLedgerError("candidate_use_charged_recovery")
                if request.mode == "execute" and (len(current.records), head(current)) != (
                    request.expected_revision,
                    request.expected_head_sha256,
                ):
                    raise StudyLedgerError("candidate_stale_head")
                if request.mode == "execute" and store.stopped:
                    raise StudyLedgerError("candidate_stopped")
                _bind_context(current, request, c)
                if any(
                    isinstance(record.event, StudyAttemptReservation)
                    and record.event.attempt_id == request.attempt_id
                    for record in current.records
                ):
                    raise StudyLedgerError("candidate_attempt_reused")
                operation = "accounting" if closure else request.operation
                reservation = StudyAttemptReservation(
                    attempt_id=request.attempt_id,
                    phase="accounting" if closure else request.phase,
                    cell_id=None if closure else request.cell_id,
                    operation=operation,
                    config_sha256=message_sha256(c) if closure else request.config_sha256,
                    input_sha256=_identity(request) if closure else request.input_sha256,
                    retry_of=request.retry_of,
                    cpu_reservation_ns=request.cpu_reservation_ns,
                    artifact_reservation_bytes=request.artifact_reservation_bytes,
                    purchase=None,
                )
                try:
                    proposed = _append(current, reservation)
                    _capacity(root, proposed, c)
                    if (
                        closure is None
                        and request.artifact_reservation_bytes
                        < request.input_bytes + request.output_limit_bytes
                    ):
                        raise StudyLedgerError("candidate_work_headroom")
                except StudyLedgerError:
                    store.limit_control_growth()
                    with store.transaction():
                        store.stop()
                    raise
                store.limit_control_growth()
                with store.transaction():
                    store.replace(current, proposed)
                current = proposed
                clock.work()
                work_start = meter.total
                if closure:
                    receipt, input_raw, result_raw, original = closure
                    result = _result(result_raw, request)
                else:
                    input_raw = read_bytes(Path(request.input_path), limit=_input_limit(request))
                    if (len(input_raw), digest(input_raw)) != (
                        request.input_bytes,
                        request.input_raw_sha256,
                    ):
                        raise StudyLedgerError("candidate_input_raw_identity")
                    actual = _input(input_raw, request)
                    _check_engine(actual, observed.engine_fingerprint)
                    if (message_sha256(actual), _config(actual)) != (
                        request.input_sha256,
                        request.config_sha256,
                    ):
                        raise StudyLedgerError("candidate_input_identity")
                    meter.write(root / f"candidate-input-{request.ticket}", input_raw)
                    produced, child_cpu = _run_child(request, input_raw, output)
                    if regular(output, missing=True) is not None:
                        meter.total += max(
                            output.stat().st_size, len(produced) if produced is not None else 0
                        )
                        output_counted = True
                    if produced is None:
                        raise StudyLedgerError("candidate_child_failed")
                    result_raw = produced
                    result = _result(result_raw, request)
                    original = current
                    receipt = CandidateReceipt(
                        logical_id=request.logical_id,
                        original_attempt_id=request.attempt_id,
                        request_sha256=_identity(request),
                        original_revision=len(original.records),
                        original_head_sha256=head(original),
                        original_ledger_sha256=digest(raw(original)),
                        input_raw_sha256=request.input_raw_sha256,
                        result_raw_sha256=digest(result_raw),
                        source_commit=c.source_commit,
                        installation_sha256=c.installation_sha256,
                    )
                    if request.operation != "candidate_production":
                        receipt = NativeStageReceipt.model_validate(
                            {
                                **receipt.model_dump(),
                                "schema_version": (
                                    "strange-physics.native-stage-execution-receipt.v1"
                                ),
                                "operation": request.operation,
                            }
                        )
                actual = _input(input_raw, request)
                _check_engine(actual, observed.engine_fingerprint)
                _validate(result, actual, receipt.original_attempt_id)
                if (message_sha256(actual), _config(actual)) != (
                    request.input_sha256,
                    request.config_sha256,
                ) or (receipt.source_commit, receipt.installation_sha256) != (
                    c.source_commit,
                    c.installation_sha256,
                ):
                    raise StudyLedgerError("candidate_result_identity")
                if (
                    closure is None
                    and read_bytes(output, limit=request.output_limit_bytes) != result_raw
                ):
                    raise StudyLedgerError("candidate_output_changed")
                durable_directory(root)
                clock.tail()
                meter.sample()
                work_bytes = meter.total - work_start
                measured = CandidateMeasurements(
                    parent_cpu_ns=clock.work_cpu,
                    child_cpu_ns=child_cpu,
                    wall_ns=clock.work_wall,
                    created_artifact_bytes=work_bytes,
                    control_parent_cpu_ns=clock.control_used,
                    control_created_artifact_bytes=work_start,
                )
                overrun = (
                    clock.work_cpu + child_cpu > request.cpu_reservation_ns
                    or work_bytes > request.artifact_reservation_bytes
                )
                facts = (
                    NativeWorkFacts(
                        attempt_id=request.attempt_id,
                        operation="accounting",
                        producer_version=VERSION
                        if request.operation == "candidate_production"
                        else "strange-physics.measured-native-stages.v1",
                        config_sha256=reservation.config_sha256,
                        input_sha256=reservation.input_sha256,
                        observation_sha256=None,
                        model_sha256=None,
                        output_sha256=digest(raw(receipt)),
                        unit="record",
                        requested_count=1,
                        completed_count=1,
                        failed_count=0,
                        not_assessed_count=0,
                        outcome="completed",
                    )
                    if closure
                    else NativeWorkFacts.model_validate_json(result.facts.model_dump_json())
                )
                settled = _append(
                    current,
                    StudyAttemptUpdate(
                        attempt_id=request.attempt_id,
                        state="unknown" if overrun else facts.outcome,
                        cpu_ns=clock.work_cpu + child_cpu,
                        wall_ns=clock.work_wall,
                        artifact_bytes=work_bytes,
                        facts=facts,
                    ),
                )
                store.limit_control_growth()
                with store.transaction():
                    store.replace(current, settled)
                    if closure is None:
                        store.db.execute(
                            "INSERT INTO closures VALUES(?,?,?,?,?,?,?)",
                            (
                                request.logical_id,
                                _identity(request),
                                raw(request),
                                f"candidate-input-{request.ticket}",
                                f"candidate-output-{request.ticket}",
                                raw(receipt),
                                digest(raw(receipt)),
                            ),
                        )
                    if overrun:
                        store.stop()
                if overrun:
                    raise StudyLedgerError("candidate_measurement_overrun")
                return _CommittedExecution(
                    receipt, result, result_raw, original, settled, measured, closure is not None
                )
        except Exception as error:
            try:
                if (
                    store is not None
                    and reservation is not None
                    and clock.tail()
                    and clock.work_started_wall
                ):
                    meter.sample()
                    if work_bytes is None:
                        if not output_counted and regular(output, missing=True) is not None:
                            meter.total += output.stat().st_size
                        work_bytes = meter.total - work_start
                    latest = store.ledger()
                    if not any(
                        isinstance(r.event, StudyAttemptUpdate)
                        and r.event.attempt_id == request.attempt_id
                        for r in latest.records
                    ):
                        failed = _append(
                            latest,
                            StudyAttemptUpdate(
                                attempt_id=request.attempt_id,
                                state="unknown",
                                cpu_ns=clock.work_cpu + child_cpu,
                                wall_ns=clock.work_wall,
                                artifact_bytes=work_bytes,
                                facts=None,
                            ),
                        )
                        store.limit_control_growth()
                        with store.transaction():
                            store.replace(latest, failed)
            except Exception:
                error.add_note("Known-cost recording failed; original work hold retained.")
            raise
        finally:
            if clock.tail() and store is not None:
                original_error = sys.exception()
                try:
                    store.close()
                except Exception:
                    if original_error is None:
                        raise
                    original_error.add_note("Final store close failed; original failure preserved.")


def commit_native_candidates(store_root: Path, request: CandidateRequest) -> CommittedCandidate:
    """Preserve the original candidate API over the shared fixed supervisor."""
    value = _commit_native_execution(store_root, request, expected_operation="candidate_production")
    assert isinstance(value.receipt, CandidateReceipt)
    assert isinstance(value.result, NativeCandidateResult)
    return CommittedCandidate(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )
