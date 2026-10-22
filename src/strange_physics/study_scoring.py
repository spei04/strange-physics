"""Read actual Journal/native material; do not execute, settle or publish a cell."""

from __future__ import annotations

import hashlib
from pathlib import Path

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    validate_native_prediction_result,
)
from strange_physics.native_scoring import (
    validate_native_preparation_result,
    validate_native_score_result,
)
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativeScoringInput,
    NativeScoringPolicy,
    parse_native_score_result,
    parse_native_scoring_input,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
    NativeWorkFacts,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    MAX_STUDY_JSON_BYTES,
    ArtifactKind,
    NativeStudyManifest,
    NativeWorldCatalog,
)
from strange_physics.study_journal import reconcile_study_journal
from strange_physics.study_ledger import (
    FINAL,
    StudyAttemptSnapshot,
    StudyLedgerError,
    read_study_ledger,
    study_cell_attempts,
    study_manifest,
    summarize_study,
)
from strange_physics.study_scoring_contracts import (
    StudyMaterialIdentity,
    StudyNativeAttemptEvidence,
    StudyNativeScoreEvidence,
)

NATIVE_MATERIAL_KINDS = frozenset(
    ("world_catalog", "pool", "candidate_config", "prediction_config", "scoring_policy")
)


def _identity(raw: bytes, value: Message) -> StudyMaterialIdentity:
    return StudyMaterialIdentity(
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        canonical_sha256=message_sha256(value),
        byte_count=len(raw),
    )


def _artifact[M: Message](
    manifest: NativeStudyManifest, materials: dict[str, bytes], kind: ArtifactKind, model: type[M]
) -> M:
    raw = materials[kind]
    ref = manifest.artifact(kind)
    if len(raw) != ref.byte_count or hashlib.sha256(raw).hexdigest() != ref.sha256:
        raise StudyLedgerError("artifact_identity_mismatch")
    value = parse_bounded_json(
        raw, model, max_bytes=MAX_STUDY_JSON_BYTES, max_depth=32, max_nodes=1_000_000
    )
    if bounded_canonical(value, MAX_STUDY_JSON_BYTES) != (ref.sha256, ref.byte_count):
        raise StudyLedgerError("artifact_typed_identity_mismatch")
    return value


def _attempt(
    attempts: dict[str, StudyAttemptSnapshot],
    identity: str,
    *,
    role: str,
    probe_id: str | None,
    input_sha256: str,
    config_sha256: str,
    facts: NativeWorkFacts | None,
) -> StudyNativeAttemptEvidence:
    item = attempts.get(identity)
    if item is None:
        raise StudyLedgerError("native_attempt_missing")
    reservation = item.reservation
    operation = {
        "candidate": "candidate_production",
        "preparation": "preparation",
        "prediction": "prediction",
        "scoring": "scoring",
    }[role]
    if (
        reservation.phase != "comparison"
        or reservation.operation != operation
        or reservation.config_sha256 != config_sha256
        or reservation.input_sha256 != input_sha256
    ):
        raise StudyLedgerError("native_attempt_mismatch")
    if facts is not None:
        update = item.latest_update
        if item.state not in FINAL or update is None or update.facts is None:
            raise StudyLedgerError("native_result_measurement_unresolved")
        if message_sha256(update.facts) != message_sha256(facts):
            raise StudyLedgerError("native_result_facts_mismatch")
    # Missing/invalid transport retains the actual reservation and known costs,
    # including unknown work; it never invents a terminal result or a refund.
    return StudyNativeAttemptEvidence.model_validate(
        {
            "role": role,
            "probe_id": probe_id,
            "reservation": reservation,
            "state": item.state,
            "latest_update": item.latest_update,
            "known_cpu_ns": item.cpu_ns,
            "known_wall_ns": item.wall_ns,
            "known_artifact_bytes": item.artifact_bytes,
        }
    )


def reconcile_native_study_score(
    ledger_raw: bytes,
    journal_path: Path,
    *,
    cell_id: str,
    materials: dict[str, bytes],
    scoring_input_raw: bytes,
    scoring_result_raw: bytes,
) -> StudyNativeScoreEvidence:
    """Bind actual closed purchases and retained native results to measured attempts.

    This is a read-only evidence boundary, not a publisher or a measurement
    producer. Current private ledger/producer authenticity and quiescent access
    remain supervisor responsibilities. No diagnostic type or future selector
    implementation is needed to validate an explicitly synthetic fixture.
    """
    ledger = read_study_ledger(ledger_raw)
    manifest = study_manifest(ledger)
    if set(materials) != NATIVE_MATERIAL_KINDS or sum(map(len, materials.values())) > (
        MAX_STUDY_JSON_BYTES
    ):
        raise StudyLedgerError("native_material_set_mismatch")
    catalog = _artifact(manifest, materials, "world_catalog", NativeWorldCatalog)
    pool = _artifact(manifest, materials, "pool", NativeSpringPool)
    candidate_config = _artifact(manifest, materials, "candidate_config", NativeCandidateConfig)
    prediction_config = _artifact(manifest, materials, "prediction_config", NativePredictionConfig)
    policy = _artifact(manifest, materials, "scoring_policy", NativeScoringPolicy)
    reconciliation = reconcile_study_journal(ledger, journal_path, catalog=catalog, cell_id=cell_id)
    if (
        reconciliation.reserved_slots != 12
        or len(reconciliation.snapshot.reservations) != 12
        or reconciliation.pending_operation_ids
        or reconciliation.missing_reservation_ids
    ):
        raise StudyLedgerError("native_purchases_incomplete")
    prefix = reconciliation.snapshot.committed_prefix()
    supplied = parse_native_scoring_input(scoring_input_raw)
    result = parse_native_score_result(scoring_result_raw)
    candidate = NativeCandidateInput(pool=pool, config=candidate_config, observations=prefix)
    context = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=supplied.context.candidate_result,
        candidate_attempt_id=supplied.context.candidate_attempt_id,
        selected=supplied.context.selected,
        policy=policy,
        prediction_config=prediction_config,
    )
    world = next(
        entry.definition
        for entry in catalog.worlds
        if entry.world_id == reconciliation.snapshot.world_id
    )
    actual = NativeScoringInput(
        context=context,
        preparation=supplied.preparation,
        predictions=supplied.predictions,
        world=world,
    )
    if message_sha256(actual) != message_sha256(supplied):
        raise StudyLedgerError("native_actual_material_mismatch")
    protocol, selected = actual.preparation.payload.protocol, context.selected
    # An unavailable candidate/preparation has no real per-probe inputs to bind.
    # Its charged failure remains in the ledger and can use unfinished-cell sealing.
    if protocol is None or selected is None:
        raise StudyLedgerError("native_preparation_unavailable")
    try:
        validate_native_candidate_result(
            context.candidate_result, candidate, attempt_id=context.candidate_attempt_id
        )
        validate_selected_native_candidate(
            selected, context.candidate_result, candidate, attempt_id=context.candidate_attempt_id
        )
        validate_native_preparation_result(
            actual.preparation, context, attempt_id=actual.preparation.facts.attempt_id
        )
        validate_native_score_result(result, actual, attempt_id=result.facts.attempt_id)
    except ValueError:
        raise StudyLedgerError("native_result_mismatch") from None
    snapshots = study_cell_attempts(ledger, cell_id)
    attempts = {item.reservation.attempt_id: item for item in snapshots}
    evidence = [
        _attempt(
            attempts,
            context.candidate_attempt_id,
            role="candidate",
            probe_id=None,
            input_sha256=message_sha256(candidate),
            config_sha256=message_sha256(candidate_config),
            facts=context.candidate_result.facts,
        ),
        _attempt(
            attempts,
            actual.preparation.facts.attempt_id,
            role="preparation",
            probe_id=None,
            input_sha256=message_sha256(context),
            config_sha256=message_sha256(policy),
            facts=actual.preparation.facts,
        ),
    ]
    for entry, probe in zip(actual.predictions.entries, protocol.probes, strict=True):
        if entry.probe_id != probe.probe_id or entry.request_sha256 != message_sha256(
            probe.request
        ):
            raise StudyLedgerError("native_probe_mismatch")
        prediction = NativePredictionInput(
            model=selected.model,
            candidate_config=candidate_config,
            request=probe.request,
            config=prediction_config,
        )
        if entry.result is not None:
            try:
                validate_native_prediction_result(
                    entry.result, prediction, attempt_id=entry.attempt_id
                )
            except ValueError:
                raise StudyLedgerError("native_prediction_mismatch") from None
        evidence.append(
            _attempt(
                attempts,
                entry.attempt_id,
                role="prediction",
                probe_id=probe.probe_id,
                input_sha256=message_sha256(prediction),
                config_sha256=message_sha256(prediction_config),
                facts=None if entry.result is None else entry.result.facts,
            )
        )
    evidence.append(
        _attempt(
            attempts,
            result.facts.attempt_id,
            role="scoring",
            probe_id=None,
            input_sha256=message_sha256(actual),
            config_sha256=message_sha256(policy),
            facts=result.facts,
        )
    )
    bound = StudyNativeScoreEvidence(
        ledger_identity=_identity(ledger_raw, ledger),
        ledger_revision=len(ledger.records),
        accounting_plan_sha256=message_sha256(ledger.plan),
        manifest_sha256=message_sha256(manifest),
        cell_id=cell_id,
        journal_id=reconciliation.snapshot.journal_id,
        journal_raw_sha256=reconciliation.snapshot.journal_bytes_sha256,
        observation_sha256=message_sha256(prefix),
        scoring_input_identity=_identity(scoring_input_raw, actual),
        scoring_result_identity=_identity(scoring_result_raw, result),
        score=result,
        attempts=tuple(evidence),
        failed_purchase_operation_ids=reconciliation.failed_operation_ids,
        unresolved_cell_attempt_ids=tuple(
            item.reservation.attempt_id for item in snapshots if item.state not in FINAL
        ),
        budget=summarize_study(ledger).budget,
    )
    # Recheck actual bytes across the complete binding operation. This does not
    # replace the supervisor's quiescent writer lock or later persistence CAS.
    latest = reconcile_study_journal(ledger, journal_path, catalog=catalog, cell_id=cell_id)
    if latest.snapshot.journal_bytes_sha256 != bound.journal_raw_sha256:
        raise StudyLedgerError("journal_changed")
    return bound
