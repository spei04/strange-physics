"""Closed native stage parsing and binding; never accepts caller-selected code."""

from __future__ import annotations

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    NativePredictionResult,
    parse_native_prediction_input,
    parse_native_prediction_result,
    validate_native_prediction_result,
)
from strange_physics.native_scoring import (
    prepare_native_evaluation,
    score_native_predictions,
    validate_native_preparation_result,
    validate_native_score_result,
)
from strange_physics.native_scoring_contracts import (
    MAX_SCORING_RESULT_BYTES,
    NativeEvaluationInput,
    NativePreparationResult,
    NativeScoreResult,
    NativeScoringInput,
    parse_native_evaluation_input,
    parse_native_score_result,
    parse_native_scoring_input,
)
from strange_physics.native_stage_execution_contracts import StageOperation
from strange_physics.publication_store import raw
from strange_physics.research_contracts import message_sha256

type StageInput = NativeEvaluationInput | NativePredictionInput | NativeScoringInput
type StageResult = NativePreparationResult | NativePredictionResult | NativeScoreResult


def parse_stage_input(operation: StageOperation, data: bytes) -> StageInput:
    if operation == "preparation":
        return parse_native_evaluation_input(data)
    if operation == "prediction":
        return parse_native_prediction_input(data)
    if operation == "scoring":
        return parse_native_scoring_input(data)
    raise ValueError("Unknown fixed native stage")


def parse_stage_result(operation: StageOperation, data: bytes) -> StageResult:
    if operation == "preparation":
        return parse_bounded_json(
            data,
            NativePreparationResult,
            max_bytes=MAX_SCORING_RESULT_BYTES,
            max_depth=32,
            max_nodes=1_000_000,
        )
    if operation == "prediction":
        return parse_native_prediction_result(data)
    if operation == "scoring":
        return parse_native_score_result(data)
    raise ValueError("Unknown fixed native stage")


def produce_stage(operation: StageOperation, data: bytes, attempt_id: str) -> bytes:
    actual = parse_stage_input(operation, data)
    if isinstance(actual, NativeEvaluationInput):
        return raw(prepare_native_evaluation(actual, attempt_id=attempt_id))
    if isinstance(actual, NativePredictionInput):
        return raw(predict_native_spring(actual, attempt_id=attempt_id))
    return raw(score_native_predictions(actual, attempt_id=attempt_id))


def stage_config(actual: StageInput) -> str:
    if isinstance(actual, NativeEvaluationInput):
        return message_sha256(actual.policy)
    if isinstance(actual, NativePredictionInput):
        return message_sha256(actual.config)
    return message_sha256(actual.context.policy)


def observation_engine(actual: StageInput) -> str | None:
    if isinstance(actual, NativeEvaluationInput):
        return actual.candidates.observations.engine_fingerprint
    if isinstance(actual, NativeScoringInput):
        return actual.context.candidates.observations.engine_fingerprint
    # Prediction preserves supplied model provenance; it has no historical
    # engine field. Current execution identity is checked by the supervisor.
    return None


def validate_stage(result: StageResult, actual: StageInput, attempt_id: str) -> None:
    if isinstance(actual, NativeEvaluationInput) and isinstance(result, NativePreparationResult):
        # This recomputes public protocol binding inside measured parent work.
        validate_native_preparation_result(result, actual, attempt_id=attempt_id)
    elif isinstance(actual, NativePredictionInput) and isinstance(result, NativePredictionResult):
        validate_native_prediction_result(result, actual, attempt_id=attempt_id)
    elif isinstance(actual, NativeScoringInput) and isinstance(result, NativeScoreResult):
        validate_native_score_result(result, actual, attempt_id=attempt_id)
    else:
        raise ValueError("Native stage input/result types differ")
