"""Paid target activation and finite protection for a sealed source authority.

The caller consumes a durable publication ticket before entering this module.
Completed targets authenticate retained origin/build material without reopening
source paths. Only marker-only/empty-file initialization cuts are recoverable.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.candidate_store import read_sealed_handoff
from strange_physics.installed_identity import TrustedInstallation, verify_native_installation
from strange_physics.measured_publication_contracts import (
    NativePublicationRequest,
    PublicationAdmission,
)
from strange_physics.publication_handoff_contracts import (
    HANDOFF_BUILD_BYTES,
    HANDOFF_ORIGIN_BYTES,
    HandoffPublicationAdmission,
    PublicationHandoffOrigin,
    validate_handoff_ledger,
)
from strange_physics.publication_store import digest, raw, regular, root_lock
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import MAX_LEDGER_RECORDS, NativeStudyLedger
from strange_physics.study_ledger import MAX_FINAL_RECORD_BYTES, StudyLedgerError, summarize_study
from strange_physics.workflow_io import private_stat, read_bytes, safe_path


def read_publication_admission(data: bytes) -> PublicationAdmission:
    # This is bounded ingress metadata only. Each selected strict parser still
    # rejects duplicate keys, unknown fields and all invalid values.
    if not 0 < len(data) <= 16 * 1024:
        raise StudyLedgerError("admission_identity")
    value = json.loads(data)
    model = (
        HandoffPublicationAdmission
        if isinstance(value, dict) and "version" in value
        else PublicationAdmission
    )
    return parse_bounded_json(data, model, max_bytes=16 * 1024, max_depth=8, max_nodes=128)


def _origin(root: Path, admission: HandoffPublicationAdmission) -> PublicationHandoffOrigin:
    data = read_bytes(root / "origin.json", limit=HANDOFF_ORIGIN_BYTES)
    origin = parse_bounded_json(
        data, PublicationHandoffOrigin, max_bytes=HANDOFF_ORIGIN_BYTES, max_depth=12, max_nodes=2048
    )
    seal = origin.seal
    info = root.stat()
    private_stat(info, directory=True)
    if (
        digest(data) != admission.origin_sha256
        or data != raw(origin)
        or seal.intent.destination != admission.control
        or seal.source_admission.control.root != admission.source_root
        or seal.seed_ledger_sha256 != admission.seed_ledger_sha256
        or (info.st_dev, info.st_ino)
        != (seal.intent.destination_device, seal.intent.destination_inode)
    ):
        raise StudyLedgerError("publication_origin_identity")
    return origin


def _installation(root: Path, origin: PublicationHandoffOrigin) -> None:
    bundle = origin.bundle
    data = read_bytes(root / "installation.json", limit=HANDOFF_BUILD_BYTES)
    if (len(data), digest(data)) != (bundle.installation_bytes, bundle.installation_raw_sha256):
        raise StudyLedgerError("publication_installation_identity")
    build = parse_bounded_json(
        data, TrustedInstallation, max_bytes=HANDOFF_BUILD_BYTES, max_depth=8, max_nodes=100000
    )
    control = origin.seal.source_admission.control
    if message_sha256(build) != control.installation_sha256:
        raise StudyLedgerError("publication_installation_identity")
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
        raise StudyLedgerError("publication_installation_identity")


@contextmanager
def publication_authority(
    root: Path,
    admission: PublicationAdmission,
) -> Iterator[PublicationHandoffOrigin | None]:
    """Hold ordered cooperating locks through the existing publisher's closure.

    A nonempty target must already contain its exact versioned persisted origin;
    Store verifies that before use. It is never reinitialized on validation error.
    """
    with ExitStack() as scope:
        if not isinstance(admission, HandoffPublicationAdmission):
            scope.enter_context(root_lock(root))
            yield None
            return
        existing = regular(root / "publication.sqlite3", missing=True)
        initialize = existing is None or existing.st_size == 0
        if initialize:
            source = safe_path(Path(admission.source_root))
            scope.enter_context(root_lock(source))
        scope.enter_context(root_lock(root))
        origin = _origin(root, admission)
        _installation(root, origin)
        if initialize:
            actual, seed = read_sealed_handoff(source, origin.seal.source_admission)
            if actual != origin.seal or digest(seed) != admission.seed_ledger_sha256:
                raise StudyLedgerError("publication_source_seal")
        # A concurrent partial/initialized transition cannot turn a failed source
        # inspection into authority. Rechecking Store's exact origin is mandatory.
        yield origin


def publication_request_bounds(
    origin: PublicationHandoffOrigin,
    request: NativePublicationRequest,
    seed: NativeStudyLedger,
) -> None:
    seal, bundle = origin.seal, origin.bundle
    escrow = seal.source_admission.control.publication
    validate_handoff_ledger(seal, seed)
    expected = sorted((f.name, f.path, f.sha256, f.byte_count) for f in bundle.files)
    if (
        request.mode != "scored"
        or request.cell_id != seal.intent.cell_id
        or sorted((f.name, f.path, f.sha256, f.byte_count) for f in request.files) != expected
        or request.diagnostic_attempt_id != bundle.diagnostic_attempt_id
        or request.journal_path != str(Path(seal.intent.destination.root) / "journal.sqlite3")
        or request.journal_sha256 != bundle.journal_sha256
        or request.cpu_reservation_ns > escrow.work_cpu_ns // escrow.calls
        or request.artifact_reservation_bytes > escrow.work_bytes_per_call()
        or request.output_limit_bytes > escrow.output_bytes
        or request.wall_limit_ns > seal.intent.destination.ticket_wall_ns
    ):
        raise StudyLedgerError("publication_handoff_bounds")


def publication_remaining_capacity(
    root: Path,
    origin: PublicationHandoffOrigin,
    reserved: NativeStudyLedger,
) -> None:
    """Actual publisher control is already held; protect only future work once."""
    seal = origin.seal
    source, target = seal.source_admission.control, seal.intent.destination
    escrow = source.publication
    consumed = sum(
        regular(root / f"ticket-{i}", missing=True) is not None for i in range(target.tickets)
    )
    remaining = target.tickets - consumed
    budget = summarize_study(reserved).budget
    if (
        budget.over_limit
        or budget.remaining_cpu_ns
        < remaining * (escrow.work_cpu_ns // target.tickets)
        + source.recovery_tickets * source.recovery_work_cpu_ns
        or budget.remaining_artifact_bytes
        < remaining * escrow.work_bytes_per_call()
        + source.recovery_tickets * source.recovery_work_artifact_bytes
        or len(reserved.records) + budget.unresolved_attempts + source.finalization_records
        > MAX_LEDGER_RECORDS
        or len(raw(reserved))
        + budget.unresolved_attempts * MAX_FINAL_RECORD_BYTES
        + source.finalization_bytes
        > escrow.ledger_bytes
    ):
        raise StudyLedgerError("publication_handoff_headroom")
