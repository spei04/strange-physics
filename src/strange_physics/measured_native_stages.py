"""Measured pre-freeze native stages over the candidate store's one ledger.

Only fixed operations are exposed. Results bind supplied material and measured
execution identity; comparison and historical Journal authenticity are absent.
Integrated lineage requires actual retained prior-stage materials to join.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strange_physics.bounded_json import bounded_canonical
from strange_physics.candidate_execution_contracts import REQUEST_BYTES, CandidateMeasurements
from strange_physics.measured_candidates import _commit_native_execution
from strange_physics.native_prediction_contracts import NativePredictionResult
from strange_physics.native_scoring_contracts import NativePreparationResult, NativeScoreResult
from strange_physics.native_stage_dispatch import StageResult
from strange_physics.native_stage_execution_contracts import (
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
    NativeStageReceipt,
)
from strange_physics.publication_store import raw
from strange_physics.study_contracts import NativeStudyLedger


@dataclass(frozen=True)
class CommittedNativeStage[Result: StageResult]:
    receipt: NativeStageReceipt
    result: Result
    result_raw: bytes
    original_ledger: NativeStudyLedger
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements
    replayed: bool


def commit_native_preparation(
    store_root: Path, request: NativePreparationRequest
) -> CommittedNativeStage[NativePreparationResult]:
    bounded_canonical(request, REQUEST_BYTES)
    request = NativePreparationRequest.model_validate_json(raw(request))
    value = _commit_native_execution(store_root, request)
    assert isinstance(value.receipt, NativeStageReceipt)
    assert isinstance(value.result, NativePreparationResult)
    return CommittedNativeStage(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )


def commit_native_prediction(
    store_root: Path, request: NativePredictionRequest
) -> CommittedNativeStage[NativePredictionResult]:
    bounded_canonical(request, REQUEST_BYTES)
    request = NativePredictionRequest.model_validate_json(raw(request))
    value = _commit_native_execution(store_root, request)
    assert isinstance(value.receipt, NativeStageReceipt)
    assert isinstance(value.result, NativePredictionResult)
    return CommittedNativeStage(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )


def commit_native_score(
    store_root: Path, request: NativeScoreRequest
) -> CommittedNativeStage[NativeScoreResult]:
    bounded_canonical(request, REQUEST_BYTES)
    request = NativeScoreRequest.model_validate_json(raw(request))
    value = _commit_native_execution(store_root, request)
    assert isinstance(value.receipt, NativeStageReceipt)
    assert isinstance(value.result, NativeScoreResult)
    return CommittedNativeStage(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )
