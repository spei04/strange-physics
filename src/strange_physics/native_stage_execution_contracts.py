"""Fixed measured stage requests; supplied provenance is not Journal authority."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from strange_physics.candidate_execution_contracts import (
    MIB,
    _ExecutionReceipt,
    _ExecutionRequest,
)

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
