"""Separate bounded native analytic prediction profile; frozen SCI messages are reused."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.native_spring_contracts import (
    MAX_INPUT_BYTES,
    MAX_RESULT_BYTES,
    NATIVE_PRODUCER,
    NativeCandidateConfig,
    NativeProducer,
    NativeWorkFacts,
)
from strange_physics.prediction_contracts import FrameCount, PredictionReason, PredictionStatus
from strange_physics.research_contracts import (
    Digest,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
    validate_prediction_model,
    validate_prediction_response,
)

NativePredictor = Literal["strange-physics.linear-spring.native-analytic.v1"]
NATIVE_PREDICTOR: NativePredictor = "strange-physics.linear-spring.native-analytic.v1"


class NativePredictionConfig(Message):
    """Fixed counterfactual profile, distinct from purchased-action admission."""

    schema_version: Literal["strange-physics.native-prediction-config.v1"] = (
        "strange-physics.native-prediction-config.v1"
    )
    predictor_version: NativePredictor = NATIVE_PREDICTOR
    supported_producer_version: NativeProducer = NATIVE_PRODUCER
    supported_candidate_config_sha256: Literal[
        "155d375afb628eb79411c3d331ca0d940e2e7bef41d6c3eab17761352c3bebb1"
    ] = "155d375afb628eb79411c3d331ca0d940e2e7bef41d6c3eab17761352c3bebb1"
    equation: Literal["stationary-shared-zero-rest-linear-spring.v1"] = (
        "stationary-shared-zero-rest-linear-spring.v1"
    )
    algorithm: Literal["closed-form-oscillator-sinc.v1"] = "closed-form-oscillator-sinc.v1"
    time_policy: Literal["exact-requested-times.v1"] = "exact-requested-times.v1"
    step_policy: Literal["alignment-replay-metadata-only.v1"] = "alignment-replay-metadata-only.v1"
    failure_policy: Literal["no-partial-response.v1"] = "no-partial-response.v1"
    particle_count: Annotated[int, Field(ge=1, le=1)] = 1
    anchor_count: Annotated[int, Field(ge=1, le=1)] = 1
    connection_count: Annotated[int, Field(ge=1, le=1)] = 1
    min_coefficient: Annotated[float, Field(ge=0.0, le=0.0)] = 0.0
    max_coefficient: Annotated[float, Field(ge=4.0, le=4.0)] = 4.0
    min_mass: Annotated[float, Field(ge=0.5, le=0.5)] = 0.5
    max_mass: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    max_anchor_norm: Annotated[float, Field(ge=0.5, le=0.5)] = 0.5
    max_initial_position_norm: Annotated[float, Field(ge=3.0, le=3.0)] = 3.0
    max_initial_velocity_norm: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    max_impulse_norm: Annotated[float, Field(ge=1.0, le=1.0)] = 1.0
    max_horizon: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    min_integration_dt: Annotated[float, Field(ge=0.0001, le=0.0001)] = 0.0001
    max_integration_dt: Annotated[float, Field(ge=0.05, le=0.05)] = 0.05
    max_reference_steps: Annotated[int, Field(ge=20_000, le=20_000)] = 20_000
    max_output_frames: Annotated[int, Field(ge=2_001, le=2_001)] = 2_001
    max_output_position_norm: Annotated[float, Field(ge=12.0, le=12.0)] = 12.0
    max_output_velocity_norm: Annotated[float, Field(ge=14.0, le=14.0)] = 14.0
    max_input_bytes: Annotated[int, Field(ge=8_388_608, le=8_388_608)] = MAX_INPUT_BYTES
    max_result_bytes: Annotated[int, Field(ge=4_194_304, le=4_194_304)] = MAX_RESULT_BYTES


class NativePredictionInput(Message):
    """Actual model, producer configuration, public probe and predictor configuration.

    Model provenance is captured, not authenticated. Bind an actual candidate
    result separately when production/selection provenance is required.
    """

    schema_version: Literal["strange-physics.native-prediction-input.v1"] = (
        "strange-physics.native-prediction-input.v1"
    )
    model: LinearSpringModel
    candidate_config: NativeCandidateConfig
    request: PredictionRequest
    config: NativePredictionConfig

    @field_validator("model")
    @classmethod
    def bound_selection(cls, value: LinearSpringModel) -> LinearSpringModel:
        if len(value.fit_record_indices) > 12:
            raise ValueError("Native prediction metadata supports at most twelve selected records")
        return value

    @model_validator(mode="after")
    def bound_bytes(self) -> Self:
        bounded_canonical(self, self.config.max_input_bytes)
        return self


class NativePredictionOutcome(Message):
    """Complete SCI response or explicit failure; no partial trajectory or accuracy claim."""

    schema_version: Literal["strange-physics.native-prediction-outcome.v1"] = (
        "strange-physics.native-prediction-outcome.v1"
    )
    status: PredictionStatus
    reason: PredictionReason | None
    actual_model_sha256: Digest
    requested_model_sha256: Digest
    request_sha256: Digest
    candidate_config_sha256: Digest
    prediction_config_sha256: Digest
    observation_sha256: Digest
    predictor_version: NativePredictor = NATIVE_PREDICTOR
    requested_frame_count: Annotated[int, Field(ge=2, le=2_001)]
    computed_frame_count: FrameCount
    returned_frame_count: FrameCount
    failed_frame_index: Annotated[int, Field(ge=0, le=2_000)] | None
    response: PredictionResponse | None
    execution_mode: Literal["analytic-no-integration.v1"] = "analytic-no-integration.v1"
    accuracy_claim: Literal["none"] = "none"

    @model_validator(mode="after")
    def complete_or_failed(self) -> Self:
        if (self.actual_model_sha256 != self.requested_model_sha256) != (
            self.status == "model_mismatch"
        ):
            raise ValueError("Model mismatch status must describe the actual/requested identities")
        reasons: dict[str, set[str | None]] = {
            "predicted": {None},
            "model_mismatch": {"model_digest_mismatch"},
            "unsupported_runtime": {
                "unsupported_model_version",
                "unsupported_fitter_version",
                "unsupported_fit_configuration",
            },
            "unsupported_domain": {
                "unsupported_topology",
                "coefficient_outside_domain",
                "anchor_outside_domain",
                "mass_outside_domain",
                "position_outside_domain",
                "velocity_outside_domain",
                "impulse_outside_domain",
                "horizon_outside_domain",
                "resource_limit",
            },
            "numerical_failure": {"arithmetic_failure", "nonfinite_state", "output_bound"},
        }
        if self.reason not in reasons[self.status]:
            raise ValueError("Prediction reason must agree with its status")
        if self.computed_frame_count > self.requested_frame_count:
            raise ValueError("Computed frames exceed the request")
        if self.status == "predicted":
            if (
                self.response is None
                or self.computed_frame_count != self.requested_frame_count
                or self.returned_frame_count != self.requested_frame_count
                or self.failed_frame_index is not None
                or self.response.model_sha256 != self.actual_model_sha256
                or len(self.response.trajectory.frames) != self.requested_frame_count
            ):
                raise ValueError("Success requires all requested frames and exact model identity")
        else:
            if self.response is not None or self.returned_frame_count != 0:
                raise ValueError("Failure cannot return a partial trajectory")
            if self.status == "numerical_failure":
                if (
                    self.failed_frame_index != self.computed_frame_count
                    or self.computed_frame_count >= self.requested_frame_count
                ):
                    raise ValueError("The failed frame must follow the exact computed prefix")
            elif self.computed_frame_count != 0 or self.failed_frame_index is not None:
                raise ValueError("Preflight rejection must precede all propagation")
        return self


class NativePredictionResult(Message):
    schema_version: Literal["strange-physics.native-prediction-result.v1"] = (
        "strange-physics.native-prediction-result.v1"
    )
    payload: NativePredictionOutcome
    facts: NativeWorkFacts

    @model_validator(mode="after")
    def bind_facts(self) -> Self:
        p, f = self.payload, self.facts
        failed = int(p.failed_frame_index is not None)
        outcome = (
            "completed"
            if p.status == "predicted"
            else "failed"
            if p.status == "numerical_failure"
            else "rejected"
        )
        if (
            f.operation != "prediction"
            or f.unit != "frame"
            or f.producer_version != p.predictor_version
            or f.config_sha256 != p.prediction_config_sha256
            or f.observation_sha256 != p.observation_sha256
            or f.model_sha256 != p.actual_model_sha256
            or f.output_sha256 != bounded_canonical(p, MAX_RESULT_BYTES)[0]
            or f.requested_count != p.requested_frame_count
            or f.completed_count != p.computed_frame_count
            or f.failed_count != failed
            or f.not_assessed_count != p.requested_frame_count - p.computed_frame_count - failed
            or f.outcome != outcome
        ):
            raise ValueError("Local work facts must bind the actual prediction outcome")
        bounded_canonical(self, MAX_RESULT_BYTES)
        return self


def validate_native_prediction_result(
    result: NativePredictionResult, actual: NativePredictionInput, *, attempt_id: str
) -> None:
    """Bind actual material/response shape, not numerical or producer authenticity."""
    p, f = result.payload, result.facts
    if (
        f.attempt_id != attempt_id
        or f.input_sha256 != bounded_canonical(actual, MAX_INPUT_BYTES)[0]
        or p.actual_model_sha256 != message_sha256(actual.model)
        or p.requested_model_sha256 != actual.request.model_sha256
        or p.request_sha256 != message_sha256(actual.request)
        or p.candidate_config_sha256 != message_sha256(actual.candidate_config)
        or p.prediction_config_sha256 != message_sha256(actual.config)
        or p.observation_sha256 != actual.model.observation_sha256
        or p.predictor_version != actual.config.predictor_version
        or p.requested_frame_count != len(actual.request.times)
    ):
        raise ValueError("Prediction differs from the actual model/request/configuration")
    if result.payload.response is not None:
        if (
            actual.model.fitter_version != actual.config.supported_producer_version
            or actual.model.fit_config_sha256 != p.candidate_config_sha256
            or p.candidate_config_sha256 != actual.config.supported_candidate_config_sha256
            or actual.model.through_index > 11
        ):
            raise ValueError("Successful native prediction requires the actual supported producer")
        validate_prediction_model(actual.model, actual.request)
        validate_prediction_response(actual.request, result.payload.response)
        if any(
            frame.time.hex() != time.hex()
            for frame, time in zip(
                result.payload.response.trajectory.frames, actual.request.times, strict=True
            )
        ):
            raise ValueError("Native response times must preserve exact signed-zero identity")


def parse_native_prediction_input(raw: bytes) -> NativePredictionInput:
    return parse_bounded_json(
        raw, NativePredictionInput, max_bytes=MAX_INPUT_BYTES, max_depth=32, max_nodes=1_000_000
    )


def parse_native_prediction_result(raw: bytes) -> NativePredictionResult:
    return parse_bounded_json(
        raw, NativePredictionResult, max_bytes=MAX_RESULT_BYTES, max_depth=32, max_nodes=1_000_000
    )


def native_prediction_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (m, "validation")
            for m in (
                NativePredictionConfig,
                NativePredictionInput,
                NativePredictionOutcome,
                NativePredictionResult,
            )
        ],
        title="Strange Physics native analytic prediction v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-prediction.schema.json"
    schema["description"] = (
        "Distinct native profile using frozen SCI request/response shapes. Actual-material "
        "binders and bounded raw parsers are required; no execution authenticity, MAP "
        "or accuracy claim."
    )
    return schema
