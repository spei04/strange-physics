"""Concrete fixed freeze proposal and captured-Journal material joins."""

from __future__ import annotations

from pathlib import Path

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
)
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativeScoringPolicy
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeCandidateResult,
    NativeSpringPool,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.publication_store import digest, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_contracts import NativeStudyLedger, NativeWorkFacts, NativeWorldCatalog
from strange_physics.study_execution_contracts import NativeFreezeInput, NativeFreezeResult
from strange_physics.study_journal import reconcile_study_journal
from strange_physics.study_ledger import (
    StudyLedgerError,
    _ArtifactJSON,
    freeze_native_study,
    study_manifest,
)

VERSION = "strange-physics.measured-freeze.v1"


def validate_frozen_materials(actual: NativeFreezeInput) -> None:
    """Recheck retained originals without replaying a freeze transition."""
    if set(actual.artifacts) != {r.kind for r in actual.manifest.artifacts}:
        raise StudyLedgerError("artifact_set_mismatch")
    if sum(len(value.encode()) for value in actual.artifacts.values()) > 8 * 1024**2:
        raise StudyLedgerError("artifact_set_mismatch")
    for ref in actual.manifest.artifacts:
        value = actual.artifacts[ref.kind].encode()
        if (len(value), digest(value)) != (ref.byte_count, ref.sha256):
            raise StudyLedgerError("artifact_identity_mismatch")
        parsed = parse_bounded_json(
            b'{"value":' + value + b"}",
            _ArtifactJSON,
            max_bytes=8 * 1024**2 + 10,
            max_depth=33,
            max_nodes=1_000_000,
        )
        if canonical_json(parsed.value).encode() != value:
            raise StudyLedgerError("artifact_not_canonical")


def freeze_result(actual: NativeFreezeInput, attempt_id: str) -> NativeFreezeResult:
    """Deterministic result identity; only propose_freeze authorizes the event."""
    identity = message_sha256(actual.manifest)
    return NativeFreezeResult(
        manifest_sha256=identity,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="accounting",
            producer_version=VERSION,
            config_sha256=identity,
            input_sha256=message_sha256(actual),
            observation_sha256=None,
            model_sha256=None,
            output_sha256=identity,
            unit="record",
            requested_count=1,
            completed_count=1,
            failed_count=0,
            not_assessed_count=0,
            outcome="completed",
        ),
    )


def propose_freeze(
    ledger: NativeStudyLedger,
    actual: NativeFreezeInput,
    *,
    attempt_id: str,
    source_commit: str,
    lock_bytes: bytes,
    engine: str,
) -> NativeStudyLedger:
    return freeze_native_study(
        ledger,
        event_id="ce-" + digest((attempt_id + ":freeze").encode())[:60],
        manifest=actual.manifest,
        expected_revision=len(ledger.records),
        expected_purpose=ledger.plan.purpose,
        source_commit=source_commit,
        uv_lock_bytes=lock_bytes,
        engine_fingerprint=engine,
        artifacts={key: value.encode() for key, value in actual.artifacts.items()},
    )


def bind_captured_candidate(
    ledger: NativeStudyLedger,
    actual: NativeCandidateInput,
    *,
    freeze: NativeFreezeInput,
    snapshot_path: Path,
    cell_id: str,
    journal_sha256: str,
) -> None:
    """Consume a different-inode snapshot while its producer holds the real Journal."""
    validate_frozen_materials(freeze)
    manifest = study_manifest(ledger)
    if raw(manifest) != raw(freeze.manifest):
        raise StudyLedgerError("comparison_freeze_identity")
    catalog = parse_bounded_json(
        freeze.artifacts["world_catalog"].encode(),
        NativeWorldCatalog,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    pool = parse_bounded_json(
        freeze.artifacts["pool"].encode(),
        NativeSpringPool,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    config = parse_bounded_json(
        freeze.artifacts["candidate_config"].encode(),
        NativeCandidateConfig,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    reconciled = reconcile_study_journal(ledger, snapshot_path, catalog=catalog, cell_id=cell_id)
    if reconciled.snapshot.journal_bytes_sha256 != journal_sha256:
        raise StudyLedgerError("comparison_journal_capture")
    if (
        reconciled.reserved_slots != 12
        or len(reconciled.snapshot.reservations) != 12
        or reconciled.missing_reservation_ids
        or reconciled.pending_operation_ids
    ):
        raise StudyLedgerError("comparison_incomplete_prefix")
    expected = NativeCandidateInput(
        pool=pool, config=config, observations=reconciled.snapshot.committed_prefix()
    )
    if message_sha256(actual) != message_sha256(expected):
        raise StudyLedgerError("comparison_candidate_input")


def bind_classical_material(
    actual: ClassicalDiagnosticInput,
    *,
    candidate: NativeCandidateInput,
    result: NativeCandidateResult,
    attempt_id: str,
    freeze: NativeFreezeInput,
    cell_id: str,
) -> None:
    """Bind concrete retained materials; selection is optional, never a selector proof."""
    validate_frozen_materials(freeze)
    validate_native_candidate_result(result, candidate, attempt_id=attempt_id)
    selected = actual.context.selected
    if selected is not None:
        validate_selected_native_candidate(selected, result, candidate, attempt_id=attempt_id)
    if "classical_diagnostic_config" not in freeze.artifacts:
        raise StudyLedgerError("classical_frozen_config_missing")
    catalog = parse_bounded_json(
        freeze.artifacts["world_catalog"].encode(),
        NativeWorldCatalog,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    cells = [cell for cell in freeze.manifest.cells if cell.cell_id == cell_id]
    if len(cells) != 1:
        raise StudyLedgerError("classical_cell_identity")
    world = next(
        entry.definition for entry in catalog.worlds if entry.world_id == cells[0].world_id
    )
    policy = parse_bounded_json(
        freeze.artifacts["scoring_policy"].encode(),
        NativeScoringPolicy,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    prediction = parse_bounded_json(
        freeze.artifacts["prediction_config"].encode(),
        NativePredictionConfig,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    config = parse_bounded_json(
        freeze.artifacts["classical_diagnostic_config"].encode(),
        ClassicalDiagnosticConfig,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    if message_sha256(config.scoring_policy) != message_sha256(policy):
        raise StudyLedgerError("classical_policy_identity")
    expected = ClassicalDiagnosticInput(
        context=NativeEvaluationInput(
            candidates=candidate,
            candidate_result=result,
            candidate_attempt_id=attempt_id,
            selected=selected,
            policy=policy,
            prediction_config=prediction,
        ),
        config=config,
        world=world,
    )
    if message_sha256(actual) != message_sha256(expected):
        raise StudyLedgerError("classical_material_identity")
