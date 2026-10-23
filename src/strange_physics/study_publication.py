"""Compose actual retained evidence and propose an append; never execute or persist."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from strange_physics.bounded_json import bounded_canonical
from strange_physics.native_classical import validate_classical_diagnostic_result
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
    parse_classical_diagnostic_result,
)
from strange_physics.native_scoring_contracts import parse_native_scoring_input
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_contracts import (
    MAX_PUBLICATION_BYTES,
    NativeStudyLedger,
    NativeWorldCatalog,
    StudyCellOutcome,
    StudyPublicationEvent,
    StudyPublicationReference,
)
from strange_physics.study_journal import reconcile_study_journal
from strange_physics.study_ledger import (
    FINAL,
    SELECTOR_ARTIFACTS,
    StudyLedgerError,
    append_study_publication,
    read_study_ledger,
    study_cell_attempts,
    study_manifest,
)
from strange_physics.study_publication_contracts import (
    StudyDiagnosticAttempt,
    StudyPublicationEvidence,
    StudyPublicationReceipt,
    parse_study_publication_evidence,
)
from strange_physics.study_scoring import (
    NATIVE_MATERIAL_KINDS,
    _artifact,
    _identity,
    reconcile_native_study_score,
)
from strange_physics.study_scoring_contracts import StudyNativeScoreEvidence

MAX_PUBLICATION_INPUT_BYTES = 64 * 1024 * 1024


def _head(ledger: NativeStudyLedger) -> str:
    return message_sha256(ledger.records[-1] if ledger.records else ledger.plan)


def _outcome(
    native: StudyNativeScoreEvidence, diagnostic_present: bool, ledger: NativeStudyLedger
) -> StudyCellOutcome:
    manifest = study_manifest(ledger)
    cell = next(c for c in manifest.cells if c.cell_id == native.cell_id)
    evaluation = native.score.payload.evaluation
    # Incompleteness never erases an available primary report or unknown charges.
    unresolved = bool(native.unresolved_cell_attempt_ids) or not diagnostic_present
    status: str
    reason: str
    if unresolved:
        cap = (
            native.budget.over_limit
            or native.budget.remaining_cpu_ns == 0
            or native.budget.remaining_artifact_bytes == 0
        )
        status, reason = ("cap_limited", "resource_limit") if cap else ("incomplete", "interrupted")
    elif evaluation is not None and evaluation.status == "scored":
        status, reason = "complete", "scored"
    elif evaluation is not None and evaluation.status == "unscorable":
        status, reason = "failed", "unscorable"
    else:
        status, reason = "failed", "execution_failure"
    return StudyCellOutcome.model_validate(
        dict(
            cell_id=native.cell_id,
            status=status,
            reason=reason,
            journal_id=native.journal_id,
            observation_sha256=native.observation_sha256,
            model_sha256=native.score.payload.model_sha256,
            report_sha256=None if evaluation is None else evaluation.report_sha256,
            scoring_policy_sha256=manifest.artifact("scoring_policy").sha256,
            protocol_sha256=None if evaluation is None else evaluation.diagnostics.protocol_sha256,
            selector_config_sha256=manifest.artifact(SELECTOR_ARTIFACTS[cell.selector]).sha256,
        )
    )


def reconcile_study_publication(
    ledger_raw: bytes,
    journal_path: Path,
    *,
    cell_id: str,
    materials: dict[str, bytes],
    scoring_input_raw: bytes,
    scoring_result_raw: bytes,
    diagnostic_attempt_id: str | None,
    diagnostic_result_raw: bytes | None,
) -> StudyPublicationEvidence:
    """Bind actual closed native purchases and a separate classical diagnostic.

    A missing/unresolved diagnostic retains an incomplete primary result and
    accounting holds. No caller readiness flag or numerical producer is used.
    Earlier unavailable selection/preparation remains outside this boundary.
    """
    supplied = (ledger_raw, scoring_input_raw, scoring_result_raw, *materials.values())
    if diagnostic_result_raw is not None:
        supplied += (diagnostic_result_raw,)
    if any(not isinstance(raw, bytes) for raw in supplied) or sum(map(len, supplied)) > (
        MAX_PUBLICATION_INPUT_BYTES
    ):
        raise StudyLedgerError("publication_input_limit")
    if set(materials) != NATIVE_MATERIAL_KINDS | {"classical_diagnostic_config"}:
        raise StudyLedgerError("publication_material_set")
    ledger = read_study_ledger(ledger_raw)
    manifest = study_manifest(ledger)
    if not any(a.kind == "classical_diagnostic_config" for a in manifest.artifacts):
        raise StudyLedgerError("diagnostic_configuration_missing")
    config = _artifact(
        manifest, materials, "classical_diagnostic_config", ClassicalDiagnosticConfig
    )
    native_materials = {k: materials[k] for k in NATIVE_MATERIAL_KINDS}
    native = reconcile_native_study_score(
        ledger_raw,
        journal_path,
        cell_id=cell_id,
        materials=native_materials,
        scoring_input_raw=scoring_input_raw,
        scoring_result_raw=scoring_result_raw,
    )
    actual_native = parse_native_scoring_input(scoring_input_raw)
    actual = ClassicalDiagnosticInput(
        context=actual_native.context, config=config, world=actual_native.world
    )
    if message_sha256(config.scoring_policy) != message_sha256(actual.context.policy):
        raise StudyLedgerError("diagnostic_policy_mismatch")
    snapshots = study_cell_attempts(ledger, cell_id)
    attempt = None
    if diagnostic_attempt_id is not None:
        item = next(
            (s for s in snapshots if s.reservation.attempt_id == diagnostic_attempt_id), None
        )
        if item is None:
            raise StudyLedgerError("diagnostic_attempt_missing")
        r = item.reservation
        if (
            r.operation != "classical_diagnostic"
            or r.phase != "comparison"
            or r.input_sha256 != message_sha256(actual)
            or r.config_sha256 != message_sha256(config)
            or r.attempt_id in {a.reservation.attempt_id for a in native.attempts}
        ):
            raise StudyLedgerError("diagnostic_attempt_mismatch")
        attempt = StudyDiagnosticAttempt(
            reservation=r,
            state=item.state,
            latest_update=item.latest_update,
            known_cpu_ns=item.cpu_ns,
            known_wall_ns=item.wall_ns,
            known_artifact_bytes=item.artifact_bytes,
        )
    elif any(s.reservation.operation == "classical_diagnostic" for s in snapshots):
        raise StudyLedgerError("diagnostic_attempt_required")
    result = None
    identity = None
    if diagnostic_result_raw is not None:
        if attempt is None:
            raise StudyLedgerError("diagnostic_attempt_missing")
        result = parse_classical_diagnostic_result(diagnostic_result_raw)
        try:
            validate_classical_diagnostic_result(
                result, actual, attempt_id=attempt.reservation.attempt_id
            )
        except ValueError:
            raise StudyLedgerError("diagnostic_result_mismatch") from None
        u = attempt.latest_update
        if attempt.state not in FINAL or u is None or u.facts is None:
            raise StudyLedgerError("diagnostic_measurement_unresolved")
        if message_sha256(u.facts) != message_sha256(result.facts):
            raise StudyLedgerError("diagnostic_facts_mismatch")
        identity = _identity(diagnostic_result_raw, result)
    elif attempt is not None and attempt.state in FINAL:
        raise StudyLedgerError("diagnostic_result_missing")
    evidence = StudyPublicationEvidence(
        native=native,
        diagnostic_config_identity=_identity(materials["classical_diagnostic_config"], config),
        diagnostic_input_sha256=message_sha256(actual),
        diagnostic_attempt=attempt,
        diagnostic_result_identity=identity,
        diagnostic_result=result,
        outcome=_outcome(native, result is not None, ledger),
    )
    # Native reconciliation checks bytes across its work; check again across the
    # diagnostic binder without rerunning any numerical computation.

    catalog = _artifact(manifest, materials, "world_catalog", NativeWorldCatalog)
    latest = reconcile_study_journal(ledger, journal_path, catalog=catalog, cell_id=cell_id)
    if latest.snapshot.journal_bytes_sha256 != native.journal_raw_sha256:
        raise StudyLedgerError("journal_changed")
    return evidence


@dataclass(frozen=True)
class StudyPublicationProposal:
    ledger: NativeStudyLedger
    evidence: StudyPublicationEvidence
    evidence_raw: bytes
    receipt: StudyPublicationReceipt
    replayed: bool


def propose_study_publication(
    ledger_raw: bytes,
    journal_path: Path,
    *,
    event_id: str,
    expected_revision: int,
    expected_head_sha256: str,
    cell_id: str,
    materials: dict[str, bytes],
    scoring_input_raw: bytes,
    scoring_result_raw: bytes,
    diagnostic_attempt_id: str | None,
    diagnostic_result_raw: bytes | None,
    original_ledger_raw: bytes | None = None,
    original_evidence_raw: bytes | None = None,
) -> StudyPublicationProposal:
    """Pure append/CAS proposal. Replay requires original private witnesses.

    Evidence -> original ledger/materials; event -> evidence/outcome; receipt ->
    resulting record/head. No result hash feeds back into its own hashed input.
    The caller must atomically persist both evidence and ledger under a real CAS.
    """
    current = read_study_ledger(ledger_raw)
    found = next((r for r in current.records if r.event_id == event_id), None)
    if found is not None:
        if (
            not isinstance(found.event, StudyPublicationEvent)
            or original_ledger_raw is None
            or original_evidence_raw is None
        ):
            raise StudyLedgerError("publication_replay_witness_missing")
        original = read_study_ledger(original_ledger_raw)
        prefix = NativeStudyLedger(plan=current.plan, records=current.records[: found.sequence])
        if len(original.records) != found.sequence or message_sha256(original) != message_sha256(
            prefix
        ):
            raise StudyLedgerError("publication_original_prefix_mismatch")
        retained = parse_study_publication_evidence(original_evidence_raw)
        if _reference(original_evidence_raw, retained) != found.event.evidence:
            raise StudyLedgerError("event_conflict")
        base_raw = original_ledger_raw
    else:
        if original_ledger_raw is not None or original_evidence_raw is not None:
            raise StudyLedgerError("unexpected_publication_witness")
        original = current
        base_raw = ledger_raw
    if type(expected_revision) is not int or expected_revision != len(original.records):
        raise StudyLedgerError("stale_revision")
    if expected_head_sha256 != _head(original):
        raise StudyLedgerError("stale_head")
    evidence = reconcile_study_publication(
        base_raw,
        journal_path,
        cell_id=cell_id,
        materials=materials,
        scoring_input_raw=scoring_input_raw,
        scoring_result_raw=scoring_result_raw,
        diagnostic_attempt_id=diagnostic_attempt_id,
        diagnostic_result_raw=diagnostic_result_raw,
    )
    evidence_raw = canonical_json(evidence.model_dump(mode="json")).encode()
    if found is not None:
        assert original_evidence_raw is not None
        if message_sha256(evidence) != message_sha256(retained):
            raise StudyLedgerError("event_conflict")
        evidence_raw = original_evidence_raw
    event = StudyPublicationEvent(
        outcome=evidence.outcome, evidence=_reference(evidence_raw, evidence)
    )
    proposed = append_study_publication(
        original, event_id=event_id, event=event, expected_revision=expected_revision
    )
    record = proposed.records[-1]
    if found is not None and message_sha256(record) != message_sha256(found):
        raise StudyLedgerError("event_conflict")
    receipt = StudyPublicationReceipt(
        event_id=event_id,
        original_ledger_identity=evidence.native.ledger_identity,
        original_revision=expected_revision,
        original_head_sha256=_head(original),
        event=event,
        record_sha256=message_sha256(record),
        resulting_ledger_sha256=message_sha256(proposed),
    )
    return StudyPublicationProposal(
        current if found is not None else proposed,
        evidence,
        evidence_raw,
        receipt,
        found is not None,
    )


def _reference(raw: bytes, evidence: StudyPublicationEvidence) -> StudyPublicationReference:
    digest, _ = bounded_canonical(evidence, MAX_PUBLICATION_BYTES)
    if not 1 <= len(raw) <= MAX_PUBLICATION_BYTES:
        raise StudyLedgerError("publication_evidence_limit")
    return StudyPublicationReference(
        raw_sha256=hashlib.sha256(raw).hexdigest(), canonical_sha256=digest, byte_count=len(raw)
    )
