"""Versioned contracts for the trusted local spring research slice.

These messages validate scientific interfaces; they do not fit, predict or score.
"""

from __future__ import annotations

import hashlib
import math
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import (
    Experiment,
    Message,
    Number,
    ObservationBundle,
    Structure,
    Trajectory,
)
from strange_physics.serialization import canonical_json

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Index = Annotated[int, Field(ge=0, le=9_999)]
Count = Annotated[int, Field(ge=0, le=2**53 - 1)]
CANONICAL_PROFILE = "strange-physics.python-json.v1"


def message_sha256(message: Message) -> str:
    """Hash every JSON-mode field, including defaults, using the documented profile."""
    return hashlib.sha256(
        canonical_json(message.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()


class SpringFitInput(Message):
    """Only the supplied purchased prefix is available to a fitter."""

    schema_version: Literal["strange-physics.spring-fit-input.v1"] = (
        "strange-physics.spring-fit-input.v1"
    )
    observations: ObservationBundle
    through_index: Index
    fit_config_sha256: Digest

    @model_validator(mode="after")
    def validate_prefix(self) -> Self:
        if self.through_index != len(self.observations.records) - 1:
            raise ValueError(
                "fit input must contain exactly the purchased prefix through its index"
            )
        if not any(record.status == "completed" for record in self.observations.records):
            raise ValueError("fit input requires at least one completed observation")
        return self


class LinearSpringModel(Message):
    """A fitted shared linear coefficient, with explicit observation provenance."""

    schema_version: Literal["strange-physics.linear-spring-model.v1"] = (
        "strange-physics.linear-spring-model.v1"
    )
    linear: Annotated[float, Field(ge=0)]
    through_index: Index
    fit_record_indices: Annotated[tuple[Index, ...], Field(min_length=1, max_length=10_000)]
    observation_sha256: Digest
    fitter_version: Annotated[str, Field(min_length=1, max_length=128)]
    fit_config_sha256: Digest

    @model_validator(mode="after")
    def validate_selection(self) -> Self:
        if tuple(sorted(set(self.fit_record_indices))) != self.fit_record_indices:
            raise ValueError("fit record indices must be unique and strictly increasing")
        if self.fit_record_indices[-1] > self.through_index:
            raise ValueError("fit record selection extends beyond the purchased prefix")
        return self


def validate_model_for_fit(model: LinearSpringModel, fit_input: SpringFitInput) -> None:
    """Check provenance against the actual public prefix, including failed records."""
    if model.through_index != fit_input.through_index:
        raise ValueError("model and fit input prefix indices differ")
    if model.observation_sha256 != message_sha256(fit_input.observations):
        raise ValueError("model observation digest does not match the purchased prefix")
    if model.fit_config_sha256 != fit_input.fit_config_sha256:
        raise ValueError("model and fit input configuration digests differ")
    if any(
        fit_input.observations.records[index].status != "completed"
        for index in model.fit_record_indices
    ):
        raise ValueError("a fitted model cannot select failed observation records")


class PredictionRequest(Message):
    """Public prediction probes may exceed purchased-action bounds."""

    schema_version: Literal["strange-physics.prediction-request.v1"] = (
        "strange-physics.prediction-request.v1"
    )
    model_sha256: Digest
    structure: Structure
    experiment: Experiment
    times: Annotated[
        tuple[Annotated[float, Field(ge=0, le=10)], ...],
        Field(min_length=2, max_length=2_001),
    ]
    integration_dt: Annotated[float, Field(ge=0.0001, le=0.05)]

    @model_validator(mode="after")
    def validate_prediction_grid(self) -> Self:
        if tuple(p.id for p in self.experiment.particles) != self.structure.particle_ids:
            raise ValueError("prediction particle identities and order must match the structure")
        if self.times[0] != 0:
            raise ValueError("prediction times must start at zero")
        if any(a >= b for a, b in zip(self.times, self.times[1:], strict=False)):
            raise ValueError("prediction times must strictly increase")
        for time in self.times:
            ratio = time / self.integration_dt
            if not math.isclose(ratio, round(ratio), rel_tol=0, abs_tol=1e-8):
                raise ValueError("prediction times must align with the integration grid")
        if round(self.times[-1] / self.integration_dt) > 20_000:
            raise ValueError("prediction exceeds the supported integration work limit")
        return self


def validate_prediction_model(model: LinearSpringModel, request: PredictionRequest) -> None:
    """Bind a request to the serialized model, not just an asserted digest string."""
    if message_sha256(model) != request.model_sha256:
        raise ValueError("prediction model digest does not match the model artifact")


class PredictionResponse(Message):
    schema_version: Literal["strange-physics.prediction-response.v1"] = (
        "strange-physics.prediction-response.v1"
    )
    model_sha256: Digest
    trajectory: Trajectory


def validate_prediction_response(request: PredictionRequest, response: PredictionResponse) -> None:
    """Validate cross-message identity, exact requested times and particle shape."""
    if response.model_sha256 != request.model_sha256:
        raise ValueError("prediction response model digest does not match the request")
    if tuple(frame.time for frame in response.trajectory.frames) != request.times:
        raise ValueError("prediction response times must exactly match the request")
    if any(
        len(frame.positions) != len(request.structure.particle_ids)
        for frame in response.trajectory.frames
    ):
        raise ValueError("prediction response particle count must match the request")


class EvaluationReport(Message):
    """Development diagnostic: any failed prediction makes primary errors unscorable."""

    schema_version: Literal["strange-physics.evaluation-report.v1"] = (
        "strange-physics.evaluation-report.v1"
    )
    split: Literal["development"] = "development"
    status: Literal["scored", "unscorable"]
    model_sha256: Digest
    protocol_sha256: Digest
    failure_policy: Literal["unscorable-on-any-failure.v1"] = "unscorable-on-any-failure.v1"
    probe_count: Annotated[int, Field(ge=1, le=2**53 - 1)]
    valid_prediction_count: Count
    failed_prediction_count: Count
    position_mse: Annotated[Number, Field(ge=0)] | None
    normalized_position_mse: Annotated[Number, Field(ge=0)] | None
    normalization_scale: Annotated[Number, Field(gt=0)]
    evaluation_runtime_ms: Count

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        if self.valid_prediction_count + self.failed_prediction_count != self.probe_count:
            raise ValueError("prediction counts must sum to the probe count")
        scale_squared = self.normalization_scale * self.normalization_scale
        if not math.isfinite(scale_squared) or scale_squared == 0:
            raise ValueError("squared normalization scale must be finite and positive")
        if self.failed_prediction_count:
            if (
                self.status != "unscorable"
                or self.position_mse is not None
                or self.normalized_position_mse is not None
            ):
                raise ValueError(
                    "any prediction failure requires unscorable status and null errors"
                )
            return self
        if (
            self.status != "scored"
            or self.position_mse is None
            or self.normalized_position_mse is None
        ):
            raise ValueError("all-valid predictions require scored status and numeric errors")
        expected = self.position_mse / scale_squared
        if not math.isfinite(expected) or (self.position_mse > 0 and expected == 0):
            raise ValueError("normalization overflow or underflow is not a valid score")
        if not math.isclose(self.normalized_position_mse, expected, rel_tol=1e-12, abs_tol=0):
            raise ValueError("normalized MSE must equal position MSE divided by scale squared")
        return self


def research_json_schema() -> JsonSchemaValue:
    """Generate the frozen local subset; semantic and cross-message checks still apply."""
    _, schema = models_json_schema(
        [
            (SpringFitInput, "validation"),
            (LinearSpringModel, "validation"),
            (PredictionRequest, "validation"),
            (PredictionResponse, "validation"),
            (EvaluationReport, "validation"),
        ],
        title="Strange Physics local scientific contracts v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["x-contract-status"] = "local-v1"
    schema["x-canonical-profile"] = CANONICAL_PROFILE
    schema["description"] = (
        "Local scientific interface subset. Validate a named $defs entry and execute "
        "the documented semantic and cross-message checks. No fitted results, "
        "predictor implementation or scored benchmark protocol is implied."
    )
    return schema
