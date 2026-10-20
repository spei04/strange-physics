"""Additive development evaluation contracts; full results contain private labels."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message, Vector
from strange_physics.research_contracts import (
    Count,
    Digest,
    EvaluationReport,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
)
from strange_physics.worlds import WorldDefinition

ProbeCount = Annotated[int, Field(ge=0, le=24)]
Nonnegative = Annotated[float, Field(ge=0)]
PredictionAssessment = Literal["not_assessed", "valid", "missing", "failed", "invalid"]
EvaluationStatus = Literal[
    "scored", "unscorable", "protocol_failure", "evaluator_failure", "arithmetic_failure"
]
EvaluationReason = Literal[
    "prediction_failure",
    "model_digest_mismatch",
    "duplicate_probe",
    "request_digest_mismatch",
    "request_model_mismatch",
    "unsupported_probe",
    "submission_limit",
    "duplicate_submission",
    "foreign_submission",
    "submission_request_mismatch",
    "invalid_normalization_scale",
    "unsupported_world",
    "reference_failure",
    "metric_failure",
    "normalization_failure",
]
ReferenceProfile = Literal["decimal80-taylor128-tail1e-60.v1"]


class SpringEvaluationProbe(Message):
    probe_id: Identifier
    request_sha256: Digest
    request: PredictionRequest


class SpringEvaluationProtocol(Message):
    """Public retained protocol; semantic input failures are scorer outcomes."""

    schema_version: Literal["strange-physics.spring-evaluation-protocol.v1"] = (
        "strange-physics.spring-evaluation-protocol.v1"
    )
    split: Literal["development"] = "development"
    model_sha256: Digest
    probes: Annotated[tuple[SpringEvaluationProbe, ...], Field(min_length=1, max_length=24)]
    normalization_scale: Annotated[float, Field(gt=0)]
    averaging: Literal["equal-xy-time-within-probe-then-equal-probes.v1"] = (
        "equal-xy-time-within-probe-then-equal-probes.v1"
    )
    failure_policy: Literal["unscorable-on-any-failure.v1"] = "unscorable-on-any-failure.v1"
    reference_profile: ReferenceProfile = "decimal80-taylor128-tail1e-60.v1"
    domain: Literal["single-spring-counterfactual-k0-4-t2.v1"] = (
        "single-spring-counterfactual-k0-4-t2.v1"
    )
    timing: Literal["validation-reference-and-metrics-monotonic-ms.v1"] = (
        "validation-reference-and-metrics-monotonic-ms.v1"
    )


class ProbePrediction(Message):
    """A transport adapter may mark unparseable output invalid without raw error text."""

    probe_id: Identifier
    request_sha256: Digest
    status: Literal["response", "failed", "invalid"]
    response: PredictionResponse | None

    @model_validator(mode="after")
    def response_presence(self) -> Self:
        if (self.status == "response") != (self.response is not None):
            raise ValueError("Only a response entry carries a parsed prediction")
        return self


class SpringPredictionSubmissions(Message):
    """Versioned retained submission collection; order is part of its input hash."""

    schema_version: Literal["strange-physics.spring-prediction-submissions.v1"] = (
        "strange-physics.spring-prediction-submissions.v1"
    )
    entries: Annotated[tuple[ProbePrediction, ...], Field(max_length=48)]


class ProbeAssessment(Message):
    probe_index: Annotated[int, Field(ge=0, le=23)]
    probe_id: Identifier
    request_sha256: Digest
    prediction_status: PredictionAssessment
    position_mse: Nonnegative | None
    metric_role: Literal["non-primary-diagnostic"] = "non-primary-diagnostic"

    @model_validator(mode="after")
    def only_valid_predictions_have_metrics(self) -> Self:
        if self.position_mse is not None and self.prediction_status != "valid":
            raise ValueError("Only a valid prediction can have a diagnostic metric")
        return self


class ReferenceProbe(Message):
    probe_id: Identifier
    request_sha256: Digest
    times: Annotated[tuple[Nonnegative, ...], Field(min_length=2, max_length=2_001)]
    positions: Annotated[tuple[Vector, ...], Field(min_length=2, max_length=2_001)]

    @model_validator(mode="after")
    def exact_frame_shape(self) -> Self:
        if (
            len(self.times) != len(self.positions)
            or self.times[0] != 0
            or any(a >= b for a, b in zip(self.times, self.times[1:], strict=False))
        ):
            raise ValueError("Reference positions need an exact increasing zero-origin grid")
        return self


class SpringReferenceArtifact(Message):
    """Evaluator-only labels and provenance; a private-world hash is not confidentiality."""

    schema_version: Literal["strange-physics.spring-reference-artifact.v1"] = (
        "strange-physics.spring-reference-artifact.v1"
    )
    source_world_sha256: Digest
    protocol_sha256: Digest
    reference_profile: ReferenceProfile = "decimal80-taylor128-tail1e-60.v1"
    probes: Annotated[tuple[ReferenceProbe, ...], Field(min_length=1, max_length=24)]

    @model_validator(mode="after")
    def unique_probes(self) -> Self:
        if len({probe.probe_id for probe in self.probes}) != len(self.probes):
            raise ValueError("Reference probes must have unique identities")
        return self


class SpringEvaluationDiagnostics(Message):
    actual_model_sha256: Digest
    protocol_sha256: Digest
    submissions_sha256: Digest
    requested_probe_count: Annotated[int, Field(ge=1, le=24)]
    submitted_entry_count: Count
    valid_prediction_count: ProbeCount
    failed_prediction_count: ProbeCount
    prediction_not_assessed_count: ProbeCount
    computed_metric_count: ProbeCount
    metric_not_assessed_count: ProbeCount
    reference_completed_probe_count: ProbeCount
    reference_failed_probe_index: Annotated[int, Field(ge=0, le=23)] | None
    evaluation_runtime_ms: Count

    @model_validator(mode="after")
    def complete_counts(self) -> Self:
        if (
            self.valid_prediction_count
            + self.failed_prediction_count
            + self.prediction_not_assessed_count
            != self.requested_probe_count
            or self.computed_metric_count + self.metric_not_assessed_count
            != self.requested_probe_count
            or self.computed_metric_count > self.valid_prediction_count
            or self.reference_completed_probe_count > self.requested_probe_count
            or (
                self.reference_failed_probe_index is not None
                and (
                    self.reference_failed_probe_index != self.reference_completed_probe_count
                    or self.reference_failed_probe_index >= self.requested_probe_count
                )
            )
        ):
            raise ValueError("Counts must retain every requested probe")
        return self


class SpringEvaluationResult(Message):
    """Private evaluator artifact; export only explicit report/protocol projections."""

    schema_version: Literal["strange-physics.spring-evaluation-result.v1"] = (
        "strange-physics.spring-evaluation-result.v1"
    )
    status: EvaluationStatus
    reason: EvaluationReason | None
    report: EvaluationReport | None
    report_sha256: Digest | None
    diagnostics: SpringEvaluationDiagnostics
    probes: Annotated[tuple[ProbeAssessment, ...], Field(min_length=1, max_length=24)]
    reference: SpringReferenceArtifact | None
    reference_sha256: Digest | None

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        d = self.diagnostics
        if (
            len(self.probes) != d.requested_probe_count
            or tuple(probe.probe_index for probe in self.probes) != tuple(range(len(self.probes)))
            or sum(p.prediction_status == "valid" for p in self.probes) != d.valid_prediction_count
            or sum(p.prediction_status == "not_assessed" for p in self.probes)
            != d.prediction_not_assessed_count
            or sum(p.position_mse is not None for p in self.probes) != d.computed_metric_count
        ):
            raise ValueError("Ordered probe diagnostics must match aggregate counts")
        allowed: dict[str, set[str | None]] = {
            "scored": {None},
            "unscorable": {"prediction_failure"},
            "protocol_failure": {
                "model_digest_mismatch",
                "duplicate_probe",
                "request_digest_mismatch",
                "request_model_mismatch",
                "unsupported_probe",
                "submission_limit",
                "duplicate_submission",
                "foreign_submission",
                "submission_request_mismatch",
                "invalid_normalization_scale",
            },
            "evaluator_failure": {"unsupported_world", "reference_failure"},
            "arithmetic_failure": {"metric_failure", "normalization_failure"},
        }
        if self.reason not in allowed[self.status]:
            raise ValueError("Failure reason must match its stage")
        if (self.report is not None) != (self.status in {"scored", "unscorable"}):
            raise ValueError("Only scored/unscorable outcomes may carry an SCI report")
        if self.report is None:
            if self.report_sha256 is not None:
                raise ValueError("Absent reports have no artifact hash")
        else:
            report = self.report
            if (
                self.report_sha256 != message_sha256(report)
                or report.status != self.status
                or report.model_sha256 != d.actual_model_sha256
                or report.protocol_sha256 != d.protocol_sha256
                or report.probe_count != d.requested_probe_count
                or report.valid_prediction_count != d.valid_prediction_count
                or report.failed_prediction_count != d.failed_prediction_count
                or report.evaluation_runtime_ms != d.evaluation_runtime_ms
                or d.prediction_not_assessed_count != 0
                or (self.status == "scored" and d.metric_not_assessed_count != 0)
                or (self.status == "unscorable" and d.computed_metric_count != 0)
            ):
                raise ValueError("Report must bind retained timing, counts and canonical bytes")
        if self.reference is None:
            if self.reference_sha256 is not None:
                raise ValueError("Absent references have no artifact hash")
        elif (
            self.reference_sha256 != message_sha256(self.reference)
            or self.reference.protocol_sha256 != d.protocol_sha256
            or len(self.reference.probes) != d.requested_probe_count
            or d.reference_completed_probe_count != d.requested_probe_count
            or d.reference_failed_probe_index is not None
        ):
            raise ValueError("Reference artifact must be complete and hash-bound")
        if self.status == "scored" and self.reference is None:
            raise ValueError("A scored outcome requires its complete private reference")
        if self.status in {"evaluator_failure", "arithmetic_failure"} and (
            d.valid_prediction_count != d.requested_probe_count or d.prediction_not_assessed_count
        ):
            raise ValueError("Evaluator/arithmetic failure cannot relabel valid predictions")
        if self.status == "evaluator_failure" and (
            self.reference is not None or d.computed_metric_count
        ):
            raise ValueError("Failed reference generation cannot claim computed metrics")
        if self.status == "arithmetic_failure" and self.reference is None:
            raise ValueError("Metric arithmetic follows complete reference generation")
        if self.status == "unscorable" and self.reference is not None:
            raise ValueError("Unscorable predictions do not generate reference labels")
        if self.status == "protocol_failure" and (
            d.prediction_not_assessed_count != d.requested_probe_count
            or d.computed_metric_count
            or self.reference is not None
            or d.reference_completed_probe_count
            or d.reference_failed_probe_index is not None
        ):
            raise ValueError("Invalid associations cannot claim assessed predictions")
        return self


def submissions_sha256(submissions: tuple[ProbePrediction, ...]) -> str:
    return message_sha256(SpringPredictionSubmissions(entries=submissions))


def validate_spring_evaluation_result(
    result: SpringEvaluationResult,
    model: LinearSpringModel,
    protocol: SpringEvaluationProtocol,
    submissions: tuple[ProbePrediction, ...],
    world: WorldDefinition,
) -> None:
    """Bind retained actual inputs and artifact shape, not metric numerical authenticity."""
    d = result.diagnostics
    if (
        d.actual_model_sha256 != message_sha256(model)
        or d.protocol_sha256 != message_sha256(protocol)
        or d.submissions_sha256 != submissions_sha256(submissions)
        or d.requested_probe_count != len(protocol.probes)
        or d.submitted_entry_count != len(submissions)
    ):
        raise ValueError("Result does not match actual model, protocol and submissions")
    for actual, probe in zip(result.probes, protocol.probes, strict=True):
        if actual.probe_id != probe.probe_id or actual.request_sha256 != message_sha256(
            probe.request
        ):
            raise ValueError("Result probe identities must match the actual ordered requests")
    if (
        result.report is not None
        and result.report.normalization_scale != protocol.normalization_scale
    ):
        raise ValueError("Report normalization must match the actual retained protocol")
    if result.reference is not None:
        if result.reference.source_world_sha256 != message_sha256(world):
            raise ValueError("Private reference does not match the actual source world")
        for reference, probe in zip(result.reference.probes, protocol.probes, strict=True):
            if (
                reference.probe_id != probe.probe_id
                or reference.request_sha256 != message_sha256(probe.request)
                or reference.times != probe.request.times
                or len(reference.positions) != len(probe.request.times)
            ):
                raise ValueError("Reference must match actual probe identities and exact grids")


EVALUATION_MODELS: tuple[type[Message], ...] = (
    SpringEvaluationProbe,
    SpringEvaluationProtocol,
    ProbePrediction,
    SpringPredictionSubmissions,
    ProbeAssessment,
    ReferenceProbe,
    SpringReferenceArtifact,
    SpringEvaluationDiagnostics,
    SpringEvaluationResult,
)


def evaluation_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(model, "validation") for model in EVALUATION_MODELS],
        title="Strange Physics independent development evaluation v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/evaluation.schema.json"
    schema["description"] = (
        "Public probe protocol and explicitly private development evaluation artifacts. "
        "Full results/reference labels must never be sent to a live agent."
    )
    return schema
