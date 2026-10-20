"""Retained local workflow messages; preparation and score artifacts are private.

Validators bind shape and provenance, not the authenticity of a numerical result.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message, ObservationBundle
from strange_physics.evaluation_contracts import (
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    SpringPredictionSubmissions,
)
from strange_physics.fitting_contracts import (
    SpringFitConfig,
    SpringFitResult,
    validate_fit_result,
)
from strange_physics.prediction_contracts import (
    SpringPredictionConfig,
    SpringPredictionResult,
    validate_spring_prediction_result,
)
from strange_physics.research_contracts import (
    Count,
    Digest,
    LinearSpringModel,
    SpringFitInput,
    message_sha256,
)

Stage = Literal["fit", "prepare", "predict", "score"]
FailureCode = Literal[
    "unsafe_path",
    "input_limit",
    "invalid_input",
    "incomplete_artifacts",
    "artifact_mismatch",
    "journal_nonquiescent",
    "journal_invalid",
    "journal_mismatch",
    "io_failure",
]


class WorkflowFailure(Message):
    schema_version: Literal["strange-physics.workflow-failure.v1"] = (
        "strange-physics.workflow-failure.v1"
    )
    stage: Stage
    code: FailureCode
    elapsed_ms: Count


class SpringFitArtifact(Message):
    schema_version: Literal["strange-physics.workflow-fit.v1"] = "strange-physics.workflow-fit.v1"
    observations: ObservationBundle
    config: SpringFitConfig
    fit_input: SpringFitInput | None
    result: SpringFitResult | None
    input_rejection: Literal["no_completed_records"] | None
    elapsed_ms: Count

    @model_validator(mode="after")
    def actual_input(self) -> Self:
        has_completed = any(r.status == "completed" for r in self.observations.records)
        if not has_completed:
            if (
                self.fit_input is not None
                or self.result is not None
                or self.input_rejection != "no_completed_records"
            ):
                raise ValueError("No completed observations requires retained input rejection")
        else:
            if self.fit_input is None or self.result is None or self.input_rejection is not None:
                raise ValueError("Completed observations require the actual input and fit result")
            if (
                self.fit_input.observations != self.observations
                or self.fit_input.fit_config_sha256 != message_sha256(self.config)
            ):
                raise ValueError("Fit input must bind the retained actual bundle and configuration")
            validate_fit_result(self.result, self.fit_input, self.config)
        return self

    @property
    def model(self) -> LinearSpringModel | None:
        return None if self.result is None else self.result.model


class SpringPreparationArtifact(Message):
    """Evaluator-only receipt; its world digest must not be published."""

    schema_version: Literal["strange-physics.workflow-preparation.v1"] = (
        "strange-physics.workflow-preparation.v1"
    )
    policy: Literal["strange-physics.i1-spring-probes.v1"] = "strange-physics.i1-spring-probes.v1"
    fit_artifact_sha256: Digest
    observation_sha256: Digest
    journal_bytes_sha256: Digest
    source_world_sha256: Digest
    engine_fingerprint: Digest
    status: Literal["prepared", "fit_failed", "unsupported_topology", "purchased_overlap"]
    protocol: SpringEvaluationProtocol | None
    overlap_probe_index: Annotated[int, Field(ge=0, le=23)] | None
    overlap_record_index: Annotated[int, Field(ge=0, le=9999)] | None
    elapsed_ms: Count

    @model_validator(mode="after")
    def complete_manifest(self) -> Self:
        if (self.protocol is not None) != (self.status == "prepared"):
            raise ValueError("Only preparation success contains a public protocol")
        if self.protocol is not None and (
            len(self.protocol.probes) != 24 or self.protocol.normalization_scale != 1.0
        ):
            raise ValueError("The I1 protocol requires all 24 probes and scale one")
        overlap = self.status == "purchased_overlap"
        if (self.overlap_probe_index is not None) != overlap or (
            self.overlap_record_index is not None
        ) != overlap:
            raise ValueError("Overlap rejection retains both exact manifest indices")
        return self


class SpringPredictionArtifact(Message):
    schema_version: Literal["strange-physics.workflow-predictions.v1"] = (
        "strange-physics.workflow-predictions.v1"
    )
    model: LinearSpringModel
    protocol: SpringEvaluationProtocol
    config: SpringPredictionConfig
    results: Annotated[tuple[SpringPredictionResult, ...], Field(min_length=1, max_length=24)]
    submissions: SpringPredictionSubmissions
    elapsed_ms: Count

    @model_validator(mode="after")
    def all_requested_results(self) -> Self:
        probes = self.protocol.probes
        if len(self.results) != len(probes) or len(self.submissions.entries) != len(probes):
            raise ValueError("Every requested probe requires one retained result and submission")
        if len({p.probe_id for p in probes}) != len(probes):
            raise ValueError("Prediction manifest probe identities must be unique")
        for probe, result, submission in zip(
            probes, self.results, self.submissions.entries, strict=True
        ):
            if (
                probe.request_sha256 != message_sha256(probe.request)
                or probe.request.model_sha256 != self.protocol.model_sha256
            ):
                raise ValueError("Manifest must retain actual request and model identities")
            validate_spring_prediction_result(result, self.model, probe.request, self.config)
            if (
                submission.probe_id != probe.probe_id
                or submission.request_sha256 != probe.request_sha256
                or submission.response != result.response
                or submission.status != ("response" if result.response is not None else "failed")
            ):
                raise ValueError("Submission must retain the exact ordered prediction outcome")
        return self


class ProbeRMSE(Message):
    probe_id: Identifier
    position_mse: Annotated[float, Field(ge=0)] | None
    position_rmse: Annotated[float, Field(ge=0)] | None

    @model_validator(mode="after")
    def derived_metric(self) -> Self:
        expected = None if self.position_mse is None else math.sqrt(self.position_mse)
        if self.position_rmse != expected:
            raise ValueError("RMSE is the exact derived square root of the retained MSE")
        return self


class SpringScoreArtifact(Message):
    """Private full evaluator result and complete per-probe development target accounting."""

    schema_version: Literal["strange-physics.workflow-score.v1"] = (
        "strange-physics.workflow-score.v1"
    )
    fit_artifact_sha256: Digest
    preparation_sha256: Digest
    prediction_artifact_sha256: Digest
    result: SpringEvaluationResult
    probes: Annotated[tuple[ProbeRMSE, ...], Field(min_length=1, max_length=24)]
    target_rmse: Annotated[float, Field(ge=0.001, le=0.001)] = 0.001
    maximum_position_rmse: Annotated[float, Field(ge=0)] | None
    target_passed: bool
    elapsed_ms: Count

    @model_validator(mode="after")
    def no_survivor_aggregation(self) -> Self:
        if len(self.probes) != len(self.result.probes):
            raise ValueError("Summary must retain every requested probe")
        for metric, assessment in zip(self.probes, self.result.probes, strict=True):
            if (
                metric.probe_id != assessment.probe_id
                or metric.position_mse != assessment.position_mse
            ):
                raise ValueError("Summary must derive from the exact ordered independent scores")
        values = tuple(p.position_rmse for p in self.probes)
        complete = self.result.status == "scored" and all(v is not None for v in values)
        maximum = max(v for v in values if v is not None) if complete else None
        if self.maximum_position_rmse != maximum or self.target_passed != (
            maximum is not None and maximum <= self.target_rmse
        ):
            raise ValueError("Development target requires all scores and the worst probe")
        return self


class ArtifactFile(Message):
    """Raw serialized bytes, distinct from normalized message hashes."""

    name: Annotated[
        str,
        Field(
            pattern=r"^[a-z][a-z0-9-]{0,47}\.json$",
            max_length=53,
            json_schema_extra={"not": {"pattern": "[^a-z0-9.\\-]"}},
        ),
    ]
    bytes: Annotated[int, Field(ge=1, le=64 * 1024 * 1024)]
    bytes_sha256: Digest


class StageCompletion(Message):
    schema_version: Literal["strange-physics.workflow-completion.v1"] = (
        "strange-physics.workflow-completion.v1"
    )
    stage: Stage
    files: Annotated[tuple[ArtifactFile, ...], Field(min_length=1, max_length=8)]
    input_message_sha256: Annotated[tuple[Digest, ...], Field(max_length=8)]
    elapsed_ms: Count
    meaning: Literal["complete-artifacts-not-scientific-success.v1"] = (
        "complete-artifacts-not-scientific-success.v1"
    )

    @model_validator(mode="after")
    def bounded_unique_files(self) -> Self:
        names = tuple(f.name for f in self.files)
        if len(set(names)) != len(names) or "completion.json" in names:
            raise ValueError("Completion lists unique outputs and does not hash itself")
        if sum(f.bytes for f in self.files) > 64 * 1024 * 1024:
            raise ValueError("Aggregate stage output exceeds 64 MiB")
        return self


WORKFLOW_MODELS: tuple[type[Message], ...] = (
    WorkflowFailure,
    SpringFitArtifact,
    SpringPreparationArtifact,
    SpringPredictionArtifact,
    ProbeRMSE,
    SpringScoreArtifact,
    ArtifactFile,
    StageCompletion,
)


def workflow_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (model, "validation")
            for model in (
                WorkflowFailure,
                SpringFitArtifact,
                SpringPreparationArtifact,
                SpringPredictionArtifact,
                ProbeRMSE,
                SpringScoreArtifact,
                ArtifactFile,
                StageCompletion,
            )
        ],
        title="Strange Physics local scientific workflow v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/workflow.schema.json"
    schema["description"] = (
        "Bounded local workflow artifacts. Preparation and scoring artifacts are private; "
        "shape and provenance checks do not prove numerical authenticity."
    )
    return schema
