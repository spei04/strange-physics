"""Bounded evaluator-private same-prefix classical diagnostic envelopes."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.evaluation_contracts import (
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    SpringPredictionSubmissions,
)
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_spring_contracts import NativeWorkFacts
from strange_physics.prediction_contracts import SpringPredictionConfig, SpringPredictionResult
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.workflow_contracts import SpringFitArtifact
from strange_physics.worlds import WorldDefinition

MAX_CLASSICAL_BYTES = 16 * 1024 * 1024
ClassicalProducer = Literal["strange-physics.same-prefix-classical-diagnostic.v1"]
CLASSICAL_PRODUCER: ClassicalProducer = "strange-physics.same-prefix-classical-diagnostic.v1"
ClassicalStatus = Literal["rejected", "fit_failed", "preparation_failed", "evaluated"]
ClassicalReason = Literal[
    "candidate_mismatch",
    "selection_mismatch",
    "policy_mismatch",
    "world_space_mismatch",
    "no_completed_records",
    "fit_unavailable",
    "unsupported_topology",
    "purchased_overlap",
]


class ClassicalDiagnosticConfig(Message):
    """Actual fixed configurations, not aliases for the native candidate/predictor."""

    schema_version: Literal["strange-physics.classical-diagnostic-config.v1"] = (
        "strange-physics.classical-diagnostic-config.v1"
    )
    producer_version: ClassicalProducer = CLASSICAL_PRODUCER
    role: Literal["same-prefix-diagnostic-only.v1"] = "same-prefix-diagnostic-only.v1"
    fit_config: SpringFitConfig
    prediction_config: SpringPredictionConfig
    scoring_policy: NativeScoringPolicy
    feedback_policy: Literal["no-primary-substitution-or-selector-feedback.v1"] = (
        "no-primary-substitution-or-selector-feedback.v1"
    )


class ClassicalDiagnosticInput(Message):
    """Private supplied material. Only the later study adapter authenticates the Journal."""

    schema_version: Literal["strange-physics.classical-diagnostic-input.v1"] = (
        "strange-physics.classical-diagnostic-input.v1"
    )
    context: NativeEvaluationInput
    config: ClassicalDiagnosticConfig
    world: WorldDefinition

    @field_validator("world")
    @classmethod
    def bounded_world(cls, value: WorldDefinition) -> WorldDefinition:
        return NativeScoringInput.bounded_world(value)

    @model_validator(mode="after")
    def bounded_input(self) -> Self:
        bounded_canonical(self, MAX_CLASSICAL_BYTES)
        return self


class ClassicalDiagnosticOutcome(Message):
    """Private actual stages. Absent later stages are never fabricated predictions."""

    schema_version: Literal["strange-physics.classical-diagnostic-outcome.v1"] = (
        "strange-physics.classical-diagnostic-outcome.v1"
    )
    role: Literal["same-prefix-diagnostic-only.v1"] = "same-prefix-diagnostic-only.v1"
    status: ClassicalStatus
    reason: ClassicalReason | None
    input_sha256: Digest
    context_sha256: Digest
    config_sha256: Digest
    observation_sha256: Digest
    model_sha256: Digest | None
    fit: SpringFitArtifact | None
    protocol: SpringEvaluationProtocol | None
    predictions: Annotated[tuple[SpringPredictionResult, ...], Field(max_length=24)]
    prediction_not_assessed_count: Annotated[int, Field(ge=0, le=24)]
    submissions: SpringPredictionSubmissions | None
    evaluation: SpringEvaluationResult | None
    overlap_probe_index: Annotated[int, Field(ge=0, le=23)] | None
    overlap_record_index: Annotated[int, Field(ge=0, le=11)] | None

    @model_validator(mode="after")
    def actual_stages(self) -> Self:
        fit = self.fit
        model = None if fit is None else fit.model
        if self.model_sha256 != (None if model is None else message_sha256(model)):
            raise ValueError("Diagnostic model identity must name the real retained fit")
        if fit is not None and (
            len(fit.observations.records) > 12
            or message_sha256(fit.observations) != self.observation_sha256
        ):
            raise ValueError("Retained fit must name the complete bounded purchased prefix")
        if len(self.predictions) + self.prediction_not_assessed_count != 24:
            raise ValueError("All fixed diagnostic predictions must remain accounted for")
        overlap = self.reason == "purchased_overlap"
        if (self.overlap_probe_index is not None) != overlap or (
            self.overlap_record_index is not None
        ) != overlap:
            raise ValueError("Only overlap retains its first probe and purchased indices")
        if self.status == "rejected":
            if self.reason == "no_completed_records":
                if fit is None or fit.input_rejection != "no_completed_records":
                    raise ValueError("Empty/failed-only prefix retains the actual fitter rejection")
            elif (
                self.reason
                not in {
                    "candidate_mismatch",
                    "selection_mismatch",
                    "policy_mismatch",
                    "world_space_mismatch",
                }
                or fit is not None
            ):
                raise ValueError("Preflight rejection cannot claim attempted numerical fitting")
        elif self.status == "fit_failed":
            if (
                self.reason != "fit_unavailable"
                or fit is None
                or fit.result is None
                or model is not None
            ):
                raise ValueError("Fit failure retains a real non-fitted result")
        elif self.status == "preparation_failed":
            if model is None or self.reason not in {"unsupported_topology", "purchased_overlap"}:
                raise ValueError("Preparation failure must retain its real fitted model")
        elif self.reason is not None or model is None:
            raise ValueError("Evaluation requires a real fitted model and no preflight reason")
        if self.status != "evaluated":
            if (
                any(x is not None for x in (self.protocol, self.submissions, self.evaluation))
                or self.predictions
            ):
                raise ValueError("Unavailable downstream stages cannot claim results")
        else:
            p, s, e = self.protocol, self.submissions, self.evaluation
            if (
                p is None
                or s is None
                or e is None
                or len(p.probes) != 24
                or len(self.predictions) != 24
                or len(s.entries) != 24
                or p.model_sha256 != self.model_sha256
                or any(len(probe.request.times) != 41 for probe in p.probes)
                or e.diagnostics.actual_model_sha256 != self.model_sha256
                or e.diagnostics.protocol_sha256 != message_sha256(p)
                or e.diagnostics.submissions_sha256 != message_sha256(s)
                or e.diagnostics.requested_probe_count != 24
                or e.diagnostics.submitted_entry_count != 24
            ):
                raise ValueError("Evaluation retains all actual ordered protocol and result stages")
        bounded_canonical(self, MAX_CLASSICAL_BYTES)
        return self


class ClassicalDiagnosticResult(Message):
    """One aggregate operation; internal fit/probe counts do not settle child attempts."""

    payload: ClassicalDiagnosticOutcome
    facts: NativeWorkFacts

    @model_validator(mode="after")
    def actual_facts(self) -> Self:
        p, f = self.payload, self.facts
        completed = int(
            p.evaluation is not None and p.evaluation.status in {"scored", "unscorable"}
        )
        rejected = int(p.status == "rejected")
        failed = 1 - completed - rejected
        if (
            f.operation != "classical_diagnostic"
            or f.unit != "work"
            or f.producer_version != CLASSICAL_PRODUCER
            or f.config_sha256 != p.config_sha256
            or f.input_sha256 != p.input_sha256
            or f.observation_sha256 != p.observation_sha256
            or f.model_sha256 != p.model_sha256
            or f.output_sha256 != bounded_canonical(p, MAX_CLASSICAL_BYTES)[0]
            or (f.requested_count, f.completed_count, f.failed_count, f.not_assessed_count)
            != (1, completed, failed, rejected)
            or f.outcome != ("completed" if completed else "rejected" if rejected else "failed")
        ):
            raise ValueError("Diagnostic facts must describe the one actual pipeline envelope")
        bounded_canonical(self, MAX_CLASSICAL_BYTES)
        return self


def parse_classical_diagnostic_input(raw: bytes) -> ClassicalDiagnosticInput:
    return parse_bounded_json(
        raw,
        ClassicalDiagnosticInput,
        max_bytes=MAX_CLASSICAL_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )


def parse_classical_diagnostic_result(raw: bytes) -> ClassicalDiagnosticResult:
    return parse_bounded_json(
        raw,
        ClassicalDiagnosticResult,
        max_bytes=MAX_CLASSICAL_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )


CLASSICAL_MODELS: tuple[type[Message], ...] = (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
    ClassicalDiagnosticOutcome,
    ClassicalDiagnosticResult,
)


def native_classical_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(m, "validation") for m in CLASSICAL_MODELS],
        title="Strange Physics same-prefix classical diagnostic v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-classical.schema.json"
    schema["description"] = (
        "Fixed public configuration and evaluator-private diagnostic inputs/outcomes/results. "
        "A parsed or hash-bound result is not actual Journal or numerical-execution proof."
    )
    schema["x-private-roots"] = [
        "ClassicalDiagnosticInput",
        "ClassicalDiagnosticOutcome",
        "ClassicalDiagnosticResult",
    ]
    return schema
