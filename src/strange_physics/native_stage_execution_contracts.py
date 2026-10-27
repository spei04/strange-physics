"""Fixed measured stage requests; supplied provenance is not Journal authority."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.candidate_execution_contracts import (
    MIB,
    _ExecutionReceipt,
    _ExecutionRequest,
)
from strange_physics.contracts import Identifier, Message
from strange_physics.native_prediction_contracts import NativePredictionInput
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativeScoringInput
from strange_physics.research_contracts import Digest

StageOperation = Literal["preparation", "prediction", "scoring"]


class NativePreparationRequest(_ExecutionRequest):
    operation: Literal["preparation"] = "preparation"
    input_bytes: Annotated[int, Field(ge=1, le=16 * MIB)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=8 * MIB)]


class NativePredictionRequest(_ExecutionRequest):
    operation: Literal["prediction"] = "prediction"


class NativeScoreRequest(_ExecutionRequest):
    operation: Literal["scoring"] = "scoring"
    input_bytes: Annotated[int, Field(ge=1, le=16 * MIB)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=8 * MIB)]


class NativeStageReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.native-stage-execution-receipt.v1"] = (
        "strange-physics.native-stage-execution-receipt.v1"
    )
    operation: StageOperation


# These payloads are deliberately additive. Existing supplied-material requests
# and receipts keep their wire shapes; comparison dispatch is not enabled here.


class NativeComparisonPreparationInput(Message):
    schema_version: Literal["strange-physics.comparison-preparation-input.v1"] = (
        "strange-physics.comparison-preparation-input.v1"
    )
    candidate_logical_id: Identifier
    candidate_receipt_sha256: Digest
    context: NativeEvaluationInput

    @model_validator(mode="after")
    def bounded_input(self) -> Self:
        bounded_canonical(self, 16 * MIB)
        return self


class NativeComparisonPredictionInput(Message):
    schema_version: Literal["strange-physics.comparison-prediction-input.v1"] = (
        "strange-physics.comparison-prediction-input.v1"
    )
    preparation_logical_id: Identifier
    preparation_receipt_sha256: Digest
    probe_index: Annotated[int, Field(ge=0, le=23)]
    prediction: NativePredictionInput

    @model_validator(mode="after")
    def bounded_input(self) -> Self:
        bounded_canonical(self, 8 * MIB)
        return self


class NativePredictionReference(Message):
    """Exact retained ticket/result reference, never proof of unavailable output.

    The measured caller must resolve this against its own immutable ticket,
    request and closure evidence. A missing/invalid label cannot override a
    retained valid terminal result or release its unknown reservation.
    """

    logical_id: Identifier
    attempt_id: Identifier
    ticket: Annotated[int, Field(ge=0, le=3071)]
    request_raw_sha256: Digest
    status: Literal["result", "missing", "invalid"]
    receipt_sha256: Digest | None
    output_raw_sha256: Digest | None

    @model_validator(mode="after")
    def retained_identity(self) -> Self:
        if (self.receipt_sha256 is not None) != (self.status == "result"):
            raise ValueError("Only an intact result references an original receipt")
        if (self.output_raw_sha256 is not None) != (self.status != "missing"):
            raise ValueError("Result/invalid requires retained output; missing cannot claim it")
        return self


class NativeComparisonScoreInput(Message):
    schema_version: Literal["strange-physics.comparison-score-input.v1"] = (
        "strange-physics.comparison-score-input.v1"
    )
    preparation_logical_id: Identifier
    preparation_receipt_sha256: Digest
    predictions: Annotated[
        tuple[NativePredictionReference, ...], Field(min_length=24, max_length=24)
    ]
    scoring: NativeScoringInput

    @model_validator(mode="after")
    def ordered_attempts(self) -> Self:
        for key in ("logical_id", "attempt_id", "ticket"):
            if len({getattr(reference, key) for reference in self.predictions}) != 24:
                raise ValueError("Every ordered probe requires a distinct retained attempt")
        for reference, entry in zip(
            self.predictions, self.scoring.predictions.entries, strict=True
        ):
            if reference.attempt_id != entry.attempt_id or reference.status != entry.status:
                raise ValueError("Transport outcomes must match their retained attempt references")
        bounded_canonical(self, 16 * MIB)
        return self


def parse_comparison_preparation_input(raw: bytes) -> NativeComparisonPreparationInput:
    return parse_bounded_json(
        raw, NativeComparisonPreparationInput, max_bytes=16 * MIB, max_depth=32, max_nodes=1_000_000
    )


def parse_comparison_prediction_input(raw: bytes) -> NativeComparisonPredictionInput:
    return parse_bounded_json(
        raw, NativeComparisonPredictionInput, max_bytes=8 * MIB, max_depth=32, max_nodes=1_000_000
    )


def parse_comparison_score_input(raw: bytes) -> NativeComparisonScoreInput:
    return parse_bounded_json(
        raw, NativeComparisonScoreInput, max_bytes=16 * MIB, max_depth=32, max_nodes=1_000_000
    )
