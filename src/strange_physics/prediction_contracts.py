"""Fixed local spring predictor profile and separate safe outcome contracts."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Message
from strange_physics.fitting_contracts import FitterVersion
from strange_physics.research_contracts import (
    Digest,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
    validate_prediction_model,
    validate_prediction_response,
)

PredictorVersion = Literal["strange-physics.linear-spring.analytic.v1"]
FrameCount = Annotated[int, Field(ge=0, le=2_001)]
PredictionStatus = Literal[
    "predicted", "model_mismatch", "unsupported_runtime", "unsupported_domain", "numerical_failure"
]
PredictionReason = Literal[
    "model_digest_mismatch",
    "unsupported_model_version",
    "unsupported_fitter_version",
    "unsupported_fit_configuration",
    "unsupported_topology",
    "coefficient_outside_domain",
    "anchor_outside_domain",
    "mass_outside_domain",
    "position_outside_domain",
    "velocity_outside_domain",
    "impulse_outside_domain",
    "horizon_outside_domain",
    "resource_limit",
    "arithmetic_failure",
    "nonfinite_state",
    "output_bound",
]


class SpringPredictionConfig(Message):
    """A fixed analytic profile; different domains or policies need a version decision."""

    schema_version: Literal["strange-physics.spring-prediction-config.v1"] = (
        "strange-physics.spring-prediction-config.v1"
    )
    predictor_version: PredictorVersion = "strange-physics.linear-spring.analytic.v1"
    supported_model_version: Literal["strange-physics.linear-spring-model.v1"] = (
        "strange-physics.linear-spring-model.v1"
    )
    supported_fitter_version: FitterVersion = "strange-physics.linear-spring.paired-simpson.v1"
    supported_fit_config_sha256: Literal[
        "50d7cfb3acf86c3c6415add0766e2ce5494943a22044d25e92749f355d3a2286"
    ] = "50d7cfb3acf86c3c6415add0766e2ce5494943a22044d25e92749f355d3a2286"
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
    coordinates: Annotated[int, Field(ge=2, le=2)] = 2
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


class SpringPredictionDiagnostics(Message):
    """Input identities and complete/attempted/returned accounting, without raw errors."""

    schema_version: Literal["strange-physics.spring-prediction-diagnostics.v1"] = (
        "strange-physics.spring-prediction-diagnostics.v1"
    )
    actual_model_sha256: Digest
    requested_model_sha256: Digest
    request_sha256: Digest
    prediction_config_sha256: Digest
    predictor_version: PredictorVersion
    requested_frame_count: Annotated[int, Field(ge=2, le=2_001)]
    computed_frame_count: FrameCount
    returned_frame_count: FrameCount
    failed_frame_index: Annotated[int, Field(ge=0, le=2_000)] | None
    execution_mode: Literal["analytic-no-integration.v1"] = "analytic-no-integration.v1"
    accuracy_claim: Literal["none"] = "none"

    @model_validator(mode="after")
    def consistent_counts(self) -> Self:
        if self.computed_frame_count > self.requested_frame_count:
            raise ValueError("Computed frames cannot exceed the requested manifest")
        if self.returned_frame_count not in (0, self.requested_frame_count):
            raise ValueError("Partial prediction responses are not allowed")
        if self.failed_frame_index is not None and (
            self.failed_frame_index != self.computed_frame_count
            or self.failed_frame_index >= self.requested_frame_count
        ):
            raise ValueError("The failed frame follows exactly the successfully computed prefix")
        return self


class SpringPredictionResult(Message):
    """A complete SCI trajectory or a typed failure with no partial response."""

    schema_version: Literal["strange-physics.spring-prediction-result.v1"] = (
        "strange-physics.spring-prediction-result.v1"
    )
    status: PredictionStatus
    reason: PredictionReason | None
    response: PredictionResponse | None
    diagnostics: SpringPredictionDiagnostics

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        diagnostics = self.diagnostics
        mismatch = diagnostics.actual_model_sha256 != diagnostics.requested_model_sha256
        if mismatch != (self.status == "model_mismatch"):
            raise ValueError("Model mismatch status must match the actual/requested model digests")
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
        if self.status == "predicted":
            if (
                self.response is None
                or diagnostics.computed_frame_count != diagnostics.requested_frame_count
                or diagnostics.returned_frame_count != diagnostics.requested_frame_count
                or diagnostics.failed_frame_index is not None
                or self.response.model_sha256 != diagnostics.actual_model_sha256
                or len(self.response.trajectory.frames) != diagnostics.requested_frame_count
            ):
                raise ValueError("Success requires the complete response and consistent provenance")
        else:
            if self.response is not None or diagnostics.returned_frame_count != 0:
                raise ValueError("Failure cannot return a partial or fallback trajectory")
            if self.status == "numerical_failure":
                if diagnostics.failed_frame_index is None:
                    raise ValueError("A numerical failure must identify the failed frame")
            elif (
                diagnostics.computed_frame_count != 0 or diagnostics.failed_frame_index is not None
            ):
                raise ValueError("Preflight failure must precede any propagation")
        return self


def validate_spring_prediction_result(
    result: SpringPredictionResult,
    model: LinearSpringModel,
    request: PredictionRequest,
    config: SpringPredictionConfig,
) -> None:
    """Bind actual input identities and response shape, not numerical authenticity."""
    diagnostics = result.diagnostics
    if (
        diagnostics.actual_model_sha256 != message_sha256(model)
        or diagnostics.requested_model_sha256 != request.model_sha256
        or diagnostics.request_sha256 != message_sha256(request)
        or diagnostics.prediction_config_sha256 != message_sha256(config)
        or diagnostics.predictor_version != config.predictor_version
        or diagnostics.requested_frame_count != len(request.times)
    ):
        raise ValueError(
            "Prediction result does not match the actual model, request and configuration"
        )
    if result.response is not None:
        validate_prediction_model(model, request)
        validate_prediction_response(request, result.response)


def prediction_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (SpringPredictionConfig, "validation"),
            (SpringPredictionDiagnostics, "validation"),
            (SpringPredictionResult, "validation"),
        ],
        title="Strange Physics local spring prediction v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/prediction.schema.json"
    schema["description"] = (
        "Fixed analytic predictor configuration and complete-or-failed local outcomes. "
        "Provenance validation is not numerical authenticity or forecast accuracy."
    )
    return schema
