"""One fixed paid transfer from retained execution to a unique publisher.

No numerical work is dispatched. Trusted lock/archive/provenance files must
already be durable at their originally admitted paths; this caller never rebases
an installation descriptor. A successful source seal is irreversible, including
when the final acknowledgement is lost. Recovery then belongs to paid target
activation, not a source append or a free initialization API.
"""

from __future__ import annotations

import json
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from strange_physics import measured_candidates as measured
from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateMeasurements,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.comparison_stage_resolver import (
    RetainedStageWitness,
    _Resolver,
    bind_retained_stage,
)
from strange_physics.installed_identity import TrustedInstallation, verify_native_installation
from strange_physics.measured_publication import _deadline
from strange_physics.measured_publication_contracts import PublicationFile
from strange_physics.native_classical_contracts import ClassicalDiagnosticInput
from strange_physics.native_scoring_contracts import NativeScoringInput
from strange_physics.native_stage_execution_contracts import NativeScoreRequest
from strange_physics.publication_handoff_contracts import (
    HANDOFF_BUILD_BYTES,
    HANDOFF_INTENT_BYTES,
    HANDOFF_MATERIAL_NAMES,
    HANDOFF_PRODUCER,
    HandoffPublicationAdmission,
    PublicationHandoffBundle,
    PublicationHandoffOrigin,
    PublicationHandoffRequest,
    PublicationHandoffSeal,
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
from strange_physics.study_execution_contracts import NativeComparisonClassicalRequest
from strange_physics.study_ledger import StudyLedgerError, read_study_ledger
from strange_physics.workflow_io import private_stat, read_bytes, safe_path


@dataclass(frozen=True)
class CommittedPublicationHandoff:
    origin: PublicationHandoffOrigin
    admission: HandoffPublicationAdmission
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements


def _destination(request: PublicationHandoffRequest, source: Path) -> Path:
    target = safe_path(Path(request.intent.destination.root))
    info = target.stat()
    private_stat(info, directory=True)
    if (
        target.is_relative_to(source)
        or source.is_relative_to(target)
        or (info.st_dev, info.st_ino)
        != (request.intent.destination_device, request.intent.destination_inode)
    ):
        raise StudyLedgerError("handoff_destination_identity")
    return target


def _export(meter: Extents, path: Path, value: bytes, start: int, limit: int) -> None:
    """Resume only exact complete exports; partial bytes are retained and denied."""
    existing = regular(path, missing=True)
    if existing is not None:
        if existing.st_size != len(value) or read_bytes(path, limit=len(value)) != value:
            raise StudyLedgerError("handoff_export_conflict")
        return
    if meter.total - start + len(value) > limit:
        raise StudyLedgerError("handoff_copy_headroom")
    meter.write(path, value)


def _recovery(
    store: CandidateStore, current: NativeStudyLedger, request: PublicationHandoffRequest
) -> None:
    matches = [
        row.event
        for row in current.records
        if isinstance(row.event, StudyAttemptReservation)
        and row.event.operation == "accounting"
        and row.event.input_sha256 == message_sha256(request.intent)
        and row.event.config_sha256 == message_sha256(request.intent.destination)
    ]
    if request.mode == "execute":
        if matches:
            raise StudyLedgerError("handoff_use_protected_recovery")
        return
    prior = next((item for item in matches if item.attempt_id == request.recover_attempt_id), None)
    updates = [
        row.event
        for row in current.records
        if isinstance(row.event, StudyAttemptUpdate)
        and row.event.attempt_id == request.recover_attempt_id
    ]
    if prior is None or updates and updates[-1].state not in {"unknown", "running"}:
        raise StudyLedgerError("handoff_recovery_identity")
    # The immutable prior ticket binds the complete intent, not matching facts alone.
    found = False
    for ticket in range(store.admission.control.tickets):
        path = store.root / f"candidate-ticket-{ticket}"
        if regular(path, missing=True) is None:
            continue
        data = read_bytes(path, limit=HANDOFF_INTENT_BYTES)
        # Ordinary stage tickets have a different closed wire. Only a matching
        # reservation's exact handoff attempt may authenticate this retry.
        fields = json.loads(data)
        if not isinstance(fields, dict) or fields.get("attempt_id") != prior.attempt_id:
            continue
        saved = parse_bounded_json(
            data,
            PublicationHandoffRequest,
            max_bytes=HANDOFF_INTENT_BYTES,
            max_depth=12,
            max_nodes=512,
        )
        found = saved.intent == request.intent and saved.ticket == ticket
        break
    if not found:
        raise StudyLedgerError("handoff_recovery_identity")


def commit_publication_handoff(
    source_root: Path,
    request: PublicationHandoffRequest,
) -> CommittedPublicationHandoff:
    started = time.process_time_ns()
    bounded_canonical(request, HANDOFF_INTENT_BYTES)
    request = parse_bounded_json(
        raw(request),
        PublicationHandoffRequest,
        max_bytes=HANDOFF_INTENT_BYTES,
        max_depth=12,
        max_nodes=512,
    )
    root = safe_path(source_root)
    admission_raw = read_bytes(root / "candidate-admission.json", limit=16 * 1024)
    admission = parse_bounded_json(
        admission_raw, CandidateAdmission, max_bytes=16 * 1024, max_depth=12, max_nodes=256
    )
    control, intent = admission.control, request.intent
    if (
        str(root) != control.root
        or request.ticket >= control.tickets
        or message_sha256(admission) != intent.source_admission_sha256
        or (request.ticket >= control.tickets - control.recovery_tickets)
        != (request.mode == "recover")
        or request.mode == "recover"
        and (
            request.cpu_reservation_ns > control.recovery_work_cpu_ns
            or request.artifact_reservation_bytes > control.recovery_work_artifact_bytes
        )
    ):
        raise StudyLedgerError("handoff_admission_identity")
    with _deadline(
        control.ticket_cpu_ns,
        request.cpu_reservation_ns // 2,
        control.ticket_wall_ns,
        request.wall_limit_ns,
        started,
    ) as clock:
        meter = Extents(root, database_name="candidate.sqlite3")
        try:
            meter.write(root / f"candidate-ticket-{request.ticket}", raw(request))
        except FileExistsError:
            raise StudyLedgerError("candidate_ticket_consumed") from None
        durable_directory(root)
        store: CandidateStore | None = None
        work_start = 0
        work_bytes: int | None = None
        failure: BaseException | None = None
        try:
            with root_lock(root), ExitStack() as scope:
                seed_raw = read_bytes(root / "candidate-seed.json", limit=MAX_STUDY_JSON_BYTES)
                build_raw = read_bytes(
                    root / "candidate-installation.json", limit=HANDOFF_BUILD_BYTES
                )
                if digest(seed_raw) != admission.seed_ledger_sha256:
                    raise StudyLedgerError("candidate_admission_identity")
                if (
                    len(seed_raw) + len(build_raw) + len(admission_raw) + 64
                    > control.bootstrap_artifact_bytes
                ):
                    raise StudyLedgerError("candidate_bootstrap_artifacts")
                seed = read_study_ledger(seed_raw)
                measured._admitted(root, admission, seed, seed)
                build = parse_bounded_json(
                    build_raw,
                    TrustedInstallation,
                    max_bytes=HANDOFF_BUILD_BYTES,
                    max_depth=8,
                    max_nodes=100000,
                )
                observed = verify_native_installation(build)
                if (
                    observed.source_commit,
                    observed.uv_lock_sha256,
                    observed.engine_fingerprint,
                    observed.installation_sha256,
                ) != (
                    control.source_commit,
                    control.uv_lock_sha256,
                    control.engine_fingerprint,
                    control.installation_sha256,
                ):
                    raise StudyLedgerError("candidate_installation_identity")
                store = CandidateStore(root, admission, seed_raw, meter)
                current = store.ledger()
                measured._admitted(root, admission, seed, current)
                store.require_writable()
                if store.stopped:
                    raise StudyLedgerError("candidate_stopped")
                if (len(current.records), head(current)) != (
                    request.expected_revision,
                    request.expected_head_sha256,
                ):
                    raise StudyLedgerError("candidate_stale_head")
                if any(
                    isinstance(row.event, StudyAttemptReservation)
                    and row.event.attempt_id == request.attempt_id
                    for row in current.records
                ):
                    raise StudyLedgerError("candidate_attempt_reused")
                _recovery(store, current, request)
                reservation = StudyAttemptReservation(
                    attempt_id=request.attempt_id,
                    phase="accounting",
                    cell_id=None,
                    operation="accounting",
                    config_sha256=message_sha256(intent.destination),
                    input_sha256=message_sha256(intent),
                    retry_of=None,
                    cpu_reservation_ns=request.cpu_reservation_ns,
                    artifact_reservation_bytes=request.artifact_reservation_bytes,
                    purchase=None,
                )
                reserved = measured._append(current, reservation)
                measured._capacity(root, reserved, control)
                # All exported originals plus the installation descriptor are
                # bounded before writes; retained ancestry is inspected in memory.
                export_bound = (
                    control.publication.material_bytes
                    + control.publication.journal_bytes
                    + HANDOFF_BUILD_BYTES
                )
                if export_bound + 4 * MIB > request.artifact_reservation_bytes:
                    raise StudyLedgerError("handoff_copy_headroom")
                store.limit_control_growth()
                with store.transaction():
                    store.replace(current, reserved)
                current = reserved
                clock.work()
                work_start = meter.total
                try:
                    target = _destination(request, root)
                    scope.enter_context(root_lock(target))
                    allowed = {name + ".json" for name in HANDOFF_MATERIAL_NAMES} | {
                        "journal.sqlite3",
                        "installation.json",
                        "origin.json",
                        "seed-ledger.json",
                        "admission.json",
                    }
                    if any(path.name not in allowed for path in target.iterdir()):
                        raise StudyLedgerError("handoff_destination_occupied")
                    resolver = _Resolver(store, current, intent.cell_id, meter, scope)
                    score = resolver.closed(
                        intent.scoring.logical_id, intent.scoring.receipt_sha256, "scoring"
                    )
                    diagnostic = resolver.closed(
                        intent.diagnostic.logical_id,
                        intent.diagnostic.receipt_sha256,
                        "classical_diagnostic",
                    )
                    if not isinstance(score.request, NativeScoreRequest) or not isinstance(
                        diagnostic.request, NativeComparisonClassicalRequest
                    ):
                        raise StudyLedgerError("handoff_original_inputs")
                    bound = bind_retained_stage(
                        store,
                        score.request,
                        score.input_raw,
                        score.original,
                        meter,
                        scope,
                        replayed=True,
                    )
                    actual = bound.actual
                    if not isinstance(actual, NativeScoringInput) or not isinstance(
                        diagnostic.actual, ClassicalDiagnosticInput
                    ):
                        raise StudyLedgerError("handoff_original_inputs")
                    original_diagnostic = diagnostic.actual
                    if (
                        canonical_json(actual.context.model_dump(mode="json", exclude={"selected"}))
                        != canonical_json(
                            original_diagnostic.context.model_dump(
                                mode="json", exclude={"selected"}
                            )
                        )
                        or message_sha256(actual.world) != message_sha256(original_diagnostic.world)
                        or original_diagnostic.context.selected is not None
                        and (
                            actual.context.selected is None
                            or message_sha256(original_diagnostic.context.selected)
                            != message_sha256(actual.context.selected)
                        )
                    ):
                        raise StudyLedgerError("handoff_diagnostic_context")
                    capture = measured._bind_classical(
                        store,
                        diagnostic.request,
                        diagnostic.input_raw,
                        diagnostic.original,
                        meter,
                        scope,
                    )
                    if bound.witness.files.get(capture.path) != (
                        capture.byte_count,
                        capture.sha256,
                    ):
                        raise StudyLedgerError("handoff_history_identity")
                    classical_material = measured._classical_input(diagnostic.input_raw)
                    candidate = resolver.closed(
                        classical_material.candidate_logical_id,
                        classical_material.candidate_receipt_sha256,
                        "comparison_candidate",
                    )
                    frozen = measured._retained_freeze(
                        store, measured._comparison_input(candidate.input_raw), candidate.original
                    )
                    material_names = HANDOFF_MATERIAL_NAMES - {
                        "scoring_input",
                        "scoring_result",
                        "diagnostic_input",
                        "diagnostic_result",
                    }
                    payloads: dict[str, bytes] = {
                        name: value.encode()
                        for name, value in frozen.artifacts.items()
                        if name in material_names
                    }
                    score_output = resolver.witness.read(
                        root / f"candidate-output-{score.request.ticket}",
                        score.request.output_limit_bytes,
                    )
                    diagnostic_output = resolver.witness.read(
                        root / f"candidate-output-{diagnostic.request.ticket}",
                        diagnostic.request.output_limit_bytes,
                    )
                    payloads.update(
                        scoring_input=raw(actual),
                        scoring_result=score_output,
                        diagnostic_input=raw(original_diagnostic),
                        diagnostic_result=diagnostic_output,
                    )
                    if (
                        sum(map(len, payloads.values())) > control.publication.material_bytes
                        or capture.byte_count > control.publication.journal_bytes
                    ):
                        raise StudyLedgerError("handoff_material_headroom")
                    journal = read_bytes(capture.path, limit=control.publication.journal_bytes)
                    bundle = PublicationHandoffBundle(
                        files=tuple(
                            PublicationFile(
                                name=name,
                                path=str(target / (name + ".json")),
                                sha256=digest(value),
                                byte_count=len(value),
                            )
                            for name, value in sorted(payloads.items())
                        ),
                        journal_sha256=digest(journal),
                        journal_bytes=len(journal),
                        installation_raw_sha256=digest(build_raw),
                        installation_bytes=len(build_raw),
                        diagnostic_attempt_id=diagnostic.request.attempt_id,
                    )
                    for item in bundle.files:
                        _export(
                            meter,
                            Path(item.path),
                            payloads[item.name],
                            work_start,
                            request.artifact_reservation_bytes,
                        )
                    _export(
                        meter,
                        target / "journal.sqlite3",
                        journal,
                        work_start,
                        request.artifact_reservation_bytes,
                    )
                    _export(
                        meter,
                        target / "installation.json",
                        build_raw,
                        work_start,
                        request.artifact_reservation_bytes,
                    )
                    durable_directory(target)
                    exported = RetainedStageWitness()
                    for item in bundle.files:
                        exported.remember(Path(item.path), payloads[item.name])
                    exported.remember(target / "journal.sqlite3", journal)
                    exported.remember(target / "installation.json", build_raw)
                    exported.recheck()
                    bound.witness.recheck()
                    resolver.witness.recheck()
                    capture.recheck()
                    clock.tail()
                    meter.sample()
                    work_bytes = meter.total - work_start
                    measurements = CandidateMeasurements(
                        parent_cpu_ns=clock.work_cpu,
                        child_cpu_ns=0,
                        wall_ns=clock.work_wall,
                        created_artifact_bytes=work_bytes,
                        control_parent_cpu_ns=clock.control_used,
                        control_created_artifact_bytes=work_start,
                    )
                    if (
                        clock.work_cpu > request.cpu_reservation_ns
                        or work_bytes > request.artifact_reservation_bytes
                    ):
                        raise StudyLedgerError("handoff_measurement_overrun")
                    facts = NativeWorkFacts(
                        attempt_id=request.attempt_id,
                        operation="accounting",
                        producer_version=HANDOFF_PRODUCER,
                        config_sha256=reservation.config_sha256,
                        input_sha256=reservation.input_sha256,
                        observation_sha256=None,
                        model_sha256=None,
                        output_sha256=message_sha256(bundle),
                        unit="work",
                        requested_count=1,
                        completed_count=1,
                        failed_count=0,
                        not_assessed_count=0,
                        outcome="completed",
                    )
                    update = StudyAttemptUpdate(
                        attempt_id=request.attempt_id,
                        state="completed",
                        cpu_ns=clock.work_cpu,
                        wall_ns=clock.work_wall,
                        artifact_bytes=work_bytes,
                        facts=facts,
                    )
                    settled = measured._append(current, update)
                    hold = StudyAttemptReservation(
                        attempt_id=intent.destination.attempt_id,
                        phase="accounting",
                        cell_id=None,
                        operation="accounting",
                        config_sha256=message_sha256(intent.destination),
                        input_sha256=control.plan_sha256,
                        retry_of=None,
                        cpu_reservation_ns=control.publication.control_cpu_ns,
                        artifact_reservation_bytes=control.publication.control_artifact_bytes,
                        purchase=None,
                    )
                    final = measured._append(settled, hold)
                    seal = PublicationHandoffSeal(
                        intent=intent,
                        source_admission=admission,
                        transfer_attempt_id=request.attempt_id,
                        bundle_sha256=message_sha256(bundle),
                        sealed_revision=len(final.records),
                        sealed_head_sha256=head(final),
                        seed_ledger_sha256=digest(raw(final)),
                        seed_ledger_bytes=len(raw(final)),
                    )
                    origin = PublicationHandoffOrigin(seal=seal, bundle=bundle)
                    target_admission = HandoffPublicationAdmission(
                        version="strange-physics.handoff-publication-admission.v1",
                        control=intent.destination,
                        seed_ledger_sha256=seal.seed_ledger_sha256,
                        source_root=str(root),
                        origin_sha256=message_sha256(origin),
                    )
                    # These bounded control-tail writes precede the irreversible
                    # source COMMIT. Activation must still prove that COMMIT.
                    tail_start = meter.total
                    tail_limit = control.ticket_artifact_bytes - (meter.total - work_bytes)
                    for name, value in (
                        ("origin.json", raw(origin)),
                        ("seed-ledger.json", raw(final)),
                        ("admission.json", raw(target_admission)),
                    ):
                        _export(meter, target / name, value, tail_start, tail_limit)
                        exported.remember(target / name, value)
                    durable_directory(target)
                    store.limit_control_growth()
                    with store.transaction():
                        exported.recheck()
                        bound.witness.recheck()
                        resolver.witness.recheck()
                        capture.recheck()
                        if (
                            read_bytes(
                                root / "candidate-installation.json", limit=HANDOFF_BUILD_BYTES
                            )
                            != build_raw
                        ):
                            raise StudyLedgerError("handoff_installation_changed")
                        _destination(request, root)
                        store.seal(current, final, seal)
                    return CommittedPublicationHandoff(
                        origin, target_admission, final, measurements
                    )
                except Exception as error:
                    try:
                        if clock.tail() and clock.work_started_wall:
                            # A lost acknowledgement must not append to a seal.
                            store.require_writable()
                            meter.sample()
                            failed = StudyAttemptUpdate(
                                attempt_id=request.attempt_id,
                                state="unknown",
                                cpu_ns=clock.work_cpu,
                                wall_ns=clock.work_wall,
                                artifact_bytes=meter.total - work_start
                                if work_bytes is None
                                else work_bytes,
                                facts=None,
                            )
                            latest = store.ledger()
                            if not any(
                                isinstance(row.event, StudyAttemptUpdate)
                                and row.event.attempt_id == request.attempt_id
                                for row in latest.records
                            ):
                                store.limit_control_growth()
                                with store.transaction():
                                    store.replace(latest, measured._append(latest, failed))
                    except Exception:
                        error.add_note(
                            "Source settlement unavailable or already sealed; "
                            "retained authority and costs are not reset."
                        )
                    raise
        except BaseException as error:
            failure = error
            raise
        finally:
            try:
                if clock.tail() and store is not None:
                    store.close()
            except BaseException:
                if failure is None:
                    raise
                failure.add_note(
                    "Handoff cleanup failed; original diagnostic and retained costs preserved."
                )
