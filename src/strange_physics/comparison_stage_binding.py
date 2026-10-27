"""Pure retained-material joins for the fixed comparison stages.

These functions validate supplied typed materials, not SQLite receipt authority,
Journal currency, installed identity or observed missing/invalid transport. The
measured caller must first resolve original closures/tickets, latest attempt
states and source/lock/engine identity under its existing charged authority.
Preparation recomputation is deterministic protocol construction, not prediction
or evaluator work. No selector/MAP or measured execution claim is made here.
"""

from __future__ import annotations

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    validate_native_prediction_result,
)
from strange_physics.native_scoring import validate_native_preparation_result
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativePreparationResult,
    NativeProbeOutcome,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeCandidateResult,
    NativeSpringPool,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import ArtifactKind, NativeWorldCatalog
from strange_physics.study_execution_binding import validate_frozen_materials
from strange_physics.study_execution_contracts import NativeFreezeInput
from strange_physics.study_ledger import StudyLedgerError
from strange_physics.worlds import WorldDefinition


def _artifact[T: Message](freeze: NativeFreezeInput, role: ArtifactKind, model: type[T]) -> T:
    if role not in freeze.artifacts:
        raise StudyLedgerError("comparison_frozen_role")
    return parse_bounded_json(
        freeze.artifacts[role].encode(),
        model,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )


def _world(freeze: NativeFreezeInput, cell_id: str) -> WorldDefinition:
    cells = [cell for cell in freeze.manifest.cells if cell.cell_id == cell_id]
    if len(cells) != 1:
        raise StudyLedgerError("comparison_cell_identity")
    catalog = _artifact(freeze, "world_catalog", NativeWorldCatalog)
    worlds = [entry.definition for entry in catalog.worlds if entry.world_id == cells[0].world_id]
    if len(worlds) != 1:
        raise StudyLedgerError("comparison_world_identity")
    return worlds[0]


def bind_preparation_material(
    actual: NativeEvaluationInput,
    *,
    candidate: NativeCandidateInput,
    result: NativeCandidateResult,
    attempt_id: str,
    freeze: NativeFreezeInput,
    cell_id: str,
) -> None:
    """Bind the full purchased prefix and fixed selection before evaluator feedback."""
    validate_frozen_materials(freeze)
    world = _world(freeze, cell_id)
    if (
        len(candidate.observations.records) != 12
        or candidate.observations.engine_fingerprint != freeze.manifest.engine_fingerprint
        or message_sha256(candidate.observations.space) != message_sha256(world.space)
    ):
        raise StudyLedgerError("comparison_candidate_history")
    pool = _artifact(freeze, "pool", NativeSpringPool)
    config = _artifact(freeze, "candidate_config", NativeCandidateConfig)
    if message_sha256(candidate.pool) != message_sha256(pool) or message_sha256(
        candidate.config
    ) != message_sha256(config):
        raise StudyLedgerError("comparison_candidate_config")
    validate_native_candidate_result(result, candidate, attempt_id=attempt_id)
    if actual.selected is not None:
        validate_selected_native_candidate(
            actual.selected, result, candidate, attempt_id=attempt_id
        )
    expected = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=result,
        candidate_attempt_id=attempt_id,
        selected=actual.selected,
        policy=_artifact(freeze, "scoring_policy", NativeScoringPolicy),
        prediction_config=_artifact(freeze, "prediction_config", NativePredictionConfig),
    )
    if message_sha256(actual) != message_sha256(expected):
        raise StudyLedgerError("comparison_preparation_material")


def comparison_prediction_input(
    context: NativeEvaluationInput,
    preparation: NativePreparationResult,
    *,
    preparation_attempt_id: str,
    probe_index: int,
) -> NativePredictionInput:
    """Recompute the exact protocol; no prediction or evaluator is invoked."""
    validate_native_preparation_result(preparation, context, attempt_id=preparation_attempt_id)
    protocol, selected = preparation.payload.protocol, context.selected
    if preparation.payload.status != "prepared" or protocol is None or selected is None:
        raise StudyLedgerError("comparison_preparation_unavailable")
    if not 0 <= probe_index < 24:
        raise StudyLedgerError("comparison_probe_identity")
    return NativePredictionInput(
        model=selected.model,
        candidate_config=context.candidates.config,
        request=protocol.probes[probe_index].request,
        config=context.prediction_config,
    )


def bind_prediction_material(
    actual: NativePredictionInput,
    *,
    context: NativeEvaluationInput,
    preparation: NativePreparationResult,
    preparation_attempt_id: str,
    probe_index: int,
) -> None:
    expected = comparison_prediction_input(
        context,
        preparation,
        preparation_attempt_id=preparation_attempt_id,
        probe_index=probe_index,
    )
    if message_sha256(actual) != message_sha256(expected):
        raise StudyLedgerError("comparison_prediction_material")


def bind_score_material(
    actual: NativeScoringInput,
    *,
    context: NativeEvaluationInput,
    preparation: NativePreparationResult,
    preparation_attempt_id: str,
    predictions: tuple[NativeProbeOutcome, ...],
    freeze: NativeFreezeInput,
    cell_id: str,
    scoring_attempt_id: str,
) -> None:
    """Compare all 24 independently resolved outcomes, including unknown transports.

    A caller must derive 'missing'/'invalid' from its retained attempt evidence.
    This function cannot turn a supplied transport label into an execution fact.
    """
    bind_preparation_material(
        context,
        candidate=context.candidates,
        result=context.candidate_result,
        attempt_id=context.candidate_attempt_id,
        freeze=freeze,
        cell_id=cell_id,
    )
    validate_native_preparation_result(preparation, context, attempt_id=preparation_attempt_id)
    protocol = preparation.payload.protocol
    if preparation.payload.status != "prepared" or protocol is None or context.selected is None:
        raise StudyLedgerError("comparison_preparation_unavailable")
    attempts = {entry.attempt_id for entry in predictions}
    if (
        len(predictions) != 24
        or len(attempts) != 24
        or attempts.intersection(
            {context.candidate_attempt_id, preparation_attempt_id, scoring_attempt_id}
        )
    ):
        raise StudyLedgerError("comparison_prediction_attempts")
    for entry, probe in zip(predictions, protocol.probes, strict=True):
        if entry.probe_id != probe.probe_id or entry.request_sha256 != message_sha256(
            probe.request
        ):
            raise StudyLedgerError("comparison_probe_identity")
        if entry.result is not None:
            predicted = NativePredictionInput(
                model=context.selected.model,
                candidate_config=context.candidates.config,
                request=probe.request,
                config=context.prediction_config,
            )
            validate_native_prediction_result(entry.result, predicted, attempt_id=entry.attempt_id)
    expected = NativeScoringInput(
        context=context,
        preparation=preparation,
        predictions=NativePredictionCollection(entries=predictions),
        world=_world(freeze, cell_id),
    )
    if message_sha256(actual) != message_sha256(expected):
        raise StudyLedgerError("comparison_score_material")
