"""Fixed configuration and safe result contracts for the local spring fitter.

A fitted artifact records a numerical estimate under a model assumption. It is
not an accuracy, identifiability, prediction or independent-scoring claim.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Message, Number
from strange_physics.research_contracts import (
    Digest,
    Index,
    LinearSpringModel,
    SpringFitInput,
    message_sha256,
    validate_model_for_fit,
)

FitterVersion = Literal["strange-physics.linear-spring.paired-simpson.v1"]
RecordCount = Annotated[int, Field(ge=0, le=10_000)]
ScalarRowCount = Annotated[int, Field(ge=0, le=400_000)]
FitStatus = Literal[
    "fitted",
    "configuration_mismatch",
    "unsupported_domain",
    "insufficient_excitation",
    "numerical_failure",
    "negative_estimate",
]
FitReason = Literal[
    "configuration_digest_mismatch",
    "unsupported_topology",
    "anchor_outside_domain",
    "unsupported_sampling",
    "mass_outside_domain",
    "position_outside_domain",
    "velocity_outside_domain",
    "impulse_outside_domain",
    "work_limit",
    "below_excitation_floor",
    "nonfinite_columns",
    "nonfinite_reduction",
    "nonfinite_coefficient",
    "negative_coefficient",
]


class SpringFitConfig(Message):
    """The reviewed v1 profile is fixed; alternative knobs need a version decision."""

    schema_version: Literal["strange-physics.spring-fit-config.v1"] = (
        "strange-physics.spring-fit-config.v1"
    )
    fitter_version: FitterVersion = "strange-physics.linear-spring.paired-simpson.v1"
    model_assumption: Literal["stationary-shared-zero-rest-linear-spring.v1"] = (
        "stationary-shared-zero-rest-linear-spring.v1"
    )
    algorithm: Literal["paired-simpson-least-squares.v1"] = "paired-simpson-least-squares.v1"
    record_selection: Literal["all-completed-prefix.v1"] = "all-completed-prefix.v1"
    window_samples: Literal[3] = 3
    window_stride: Literal[2] = 2
    coordinates: Literal[2] = 2
    particle_count: Literal[1] = 1
    anchor_count: Literal[1] = 1
    connection_count: Literal[1] = 1
    duration: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    sample_interval: Annotated[float, Field(ge=0.05, le=0.05)] = 0.05
    integration_steps: tuple[
        Annotated[float, Field(ge=0.01, le=0.01)],
        Annotated[float, Field(ge=0.005, le=0.005)],
        Annotated[float, Field(ge=0.0025, le=0.0025)],
    ] = (
        0.01,
        0.005,
        0.0025,
    )
    min_mass: Annotated[float, Field(ge=0.5, le=0.5)] = 0.5
    max_mass: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    max_anchor_norm: Annotated[float, Field(ge=0.5, le=0.5)] = 0.5
    max_position_norm: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    max_velocity_norm: Annotated[float, Field(ge=2.0, le=2.0)] = 2.0
    max_impulse_norm: Annotated[float, Field(ge=1.0, le=1.0)] = 1.0
    min_design_rms: Annotated[float, Field(ge=0.000001, le=0.000001)] = 0.000001
    coefficient_policy: Literal["finite-nonnegative-no-projection.v1"] = (
        "finite-nonnegative-no-projection.v1"
    )
    noise_policy: Literal["fit-declared-noise-without-accuracy-guarantee.v1"] = (
        "fit-declared-noise-without-accuracy-guarantee.v1"
    )
    calibrated_coefficient_max: Annotated[float, Field(ge=4.0, le=4.0)] = 4.0
    max_records: Literal[10_000] = 10_000
    max_scalar_rows: Literal[400_000] = 400_000


class SpringFitDiagnostics(Message):
    """Public provenance and finite scalar diagnostics, with no raw private state."""

    schema_version: Literal["strange-physics.spring-fit-diagnostics.v1"] = (
        "strange-physics.spring-fit-diagnostics.v1"
    )
    through_index: Index
    observation_sha256: Digest
    requested_config_sha256: Digest
    actual_config_sha256: Digest
    fitter_version: FitterVersion
    record_count: RecordCount
    completed_record_count: RecordCount
    failed_record_count: RecordCount
    completed_record_indices: Annotated[tuple[Index, ...], Field(min_length=1, max_length=10_000)]
    scalar_row_count: ScalarRowCount
    design_rms: Annotated[Number, Field(ge=0)] | None
    raw_coefficient: Number | None
    declared_noisy: bool
    estimated_coefficient_in_calibrated_range: bool | None
    accuracy_claim: Literal["none"] = "none"

    @model_validator(mode="after")
    def consistent_diagnostics(self) -> Self:
        indices = self.completed_record_indices
        if (
            self.record_count != self.through_index + 1
            or self.completed_record_count + self.failed_record_count != self.record_count
            or len(indices) != self.completed_record_count
            or tuple(sorted(set(indices))) != indices
            or indices[-1] > self.through_index
        ):
            raise ValueError("Diagnostic prefix, completed selection and counts must agree")
        if self.scalar_row_count not in (0, self.completed_record_count * 40):
            raise ValueError("Diagnostics count every complete paired window and both coordinates")
        expected_range = None if self.raw_coefficient is None else 0 <= self.raw_coefficient <= 4
        if self.estimated_coefficient_in_calibrated_range != expected_range:
            raise ValueError("Calibration range flag must describe the finite raw estimate")
        return self


class SpringFitResult(Message):
    """A model and separate diagnostics, or an explicit rejected fit with no model."""

    schema_version: Literal["strange-physics.spring-fit-result.v1"] = (
        "strange-physics.spring-fit-result.v1"
    )
    status: FitStatus
    reason: FitReason | None
    model: LinearSpringModel | None
    diagnostics: SpringFitDiagnostics

    @model_validator(mode="after")
    def consistent_outcome(self) -> Self:
        diagnostics = self.diagnostics
        mismatch = diagnostics.requested_config_sha256 != diagnostics.actual_config_sha256
        if mismatch != (self.status == "configuration_mismatch"):
            raise ValueError("Configuration status must match the actual configuration digest")
        reasons: dict[str, set[str | None]] = {
            "fitted": {None},
            "configuration_mismatch": {"configuration_digest_mismatch"},
            "unsupported_domain": {
                "unsupported_topology",
                "anchor_outside_domain",
                "unsupported_sampling",
                "mass_outside_domain",
                "position_outside_domain",
                "velocity_outside_domain",
                "impulse_outside_domain",
                "work_limit",
            },
            "insufficient_excitation": {"below_excitation_floor"},
            "numerical_failure": {
                "nonfinite_columns",
                "nonfinite_reduction",
                "nonfinite_coefficient",
            },
            "negative_estimate": {"negative_coefficient"},
        }
        if self.reason not in reasons[self.status]:
            raise ValueError("Fit reason must agree with its status")
        if (self.model is not None) != (self.status == "fitted"):
            raise ValueError("Only a fitted result contains a model")
        raw = diagnostics.raw_coefficient
        if self.status in {"fitted", "negative_estimate"}:
            if (
                raw is None
                or (raw < 0) != (self.status == "negative_estimate")
                or diagnostics.design_rms is None
                or diagnostics.design_rms < 1e-6
                or diagnostics.scalar_row_count != diagnostics.completed_record_count * 40
            ):
                raise ValueError("An estimate requires supported finite design and complete rows")
        elif raw is not None:
            raise ValueError("Rejected numerical, domain or support results have no raw estimate")
        if self.status == "insufficient_excitation" and (
            diagnostics.design_rms is None
            or diagnostics.design_rms >= 1e-6
            or diagnostics.scalar_row_count != diagnostics.completed_record_count * 40
        ):
            raise ValueError("Insufficient excitation requires the declared below-floor design")
        if self.model is not None and (
            self.model.linear != raw
            or self.model.through_index != diagnostics.through_index
            or self.model.fit_record_indices != diagnostics.completed_record_indices
            or self.model.observation_sha256 != diagnostics.observation_sha256
            or self.model.fit_config_sha256 != diagnostics.actual_config_sha256
            or self.model.fitter_version != diagnostics.fitter_version
        ):
            raise ValueError("Model provenance and estimate must match the separate diagnostics")
        return self


def validate_fit_result(
    result: SpringFitResult, fit_input: SpringFitInput, config: SpringFitConfig
) -> None:
    """Bind the result to the actual configuration and entire supplied public prefix."""
    prefix = fit_input.observations
    completed = tuple(record.index for record in prefix.records if record.status == "completed")
    diagnostics = result.diagnostics
    if (
        diagnostics.through_index != fit_input.through_index
        or diagnostics.observation_sha256 != message_sha256(prefix)
        or diagnostics.requested_config_sha256 != fit_input.fit_config_sha256
        or diagnostics.actual_config_sha256 != message_sha256(config)
        or diagnostics.fitter_version != config.fitter_version
        or diagnostics.record_count != len(prefix.records)
        or diagnostics.completed_record_indices != completed
        or diagnostics.completed_record_count != len(completed)
        or diagnostics.failed_record_count != len(prefix.records) - len(completed)
        or diagnostics.declared_noisy
        != bool(prefix.space.sampling.position_noise or prefix.space.sampling.velocity_noise)
    ):
        raise ValueError("Fit result does not match the supplied public prefix and configuration")
    if result.model is not None:
        validate_model_for_fit(result.model, fit_input)


def fitting_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (SpringFitConfig, "validation"),
            (SpringFitDiagnostics, "validation"),
            (SpringFitResult, "validation"),
        ],
        title="Strange Physics local spring fitting v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/fitting.schema.json"
    schema["description"] = (
        "Fixed local fitter configuration and separate safe diagnostics. Fitted means a "
        "numerical estimate under an assumption, not scientific accuracy or supported prediction."
    )
    return schema
