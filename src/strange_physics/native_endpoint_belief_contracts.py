"""Restricted terminal-position belief messages; supplied material, not Journal authority."""

from __future__ import annotations

import hashlib
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Identifier, Message
from strange_physics.finite_log_weight_contracts import (
    FiniteLogWeightInput,
    FiniteLogWeightResult,
    bind_finite_log_weight_result,
)
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeCandidateResult,
    validate_native_candidate_result,
)
from strange_physics.research_contracts import Digest, message_sha256

MAX_CELLS = 1_025
MAX_RECORDS = 12
MAX_PREDICTIONS = MAX_CELLS * MAX_RECORDS
MAX_INPUT_BYTES = 16 * 1024**2
MAX_RESULT_BYTES = 4 * 1024**2
MAX_JSON_NODES = 2_000_000
NodeIndex = Annotated[int, Field(ge=0, lt=MAX_CELLS)]
RecordIndex = Annotated[int, Field(ge=0, lt=MAX_RECORDS)]
PredictionCount = Annotated[int, Field(ge=0, le=MAX_PREDICTIONS)]
FrameCount = Annotated[int, Field(ge=0, le=2 * MAX_PREDICTIONS)]
Reason = Literal[
    "no_completed_records",
    "candidate_unavailable",
    "unsupported_observation_noise",
    "prediction_budget",
    "prior_arithmetic",
    "likelihood_arithmetic",
    "prediction_failure",
    "normalization_failure",
]


class EndpointCell(Message):
    left: Annotated[float, Field(ge=0.0, le=4.0)]
    right: Annotated[float, Field(ge=0.0, le=4.0)]

    @model_validator(mode="after")
    def positive_width(self) -> Self:
        if self.left >= self.right:
            raise ValueError("Each cell requires positive physical width")
        return self


class EndpointBeliefProfile(Message):
    schema_version: Literal["strange-physics.endpoint-belief-profile.v1"] = (
        "strange-physics.endpoint-belief-profile.v1"
    )
    feature: Literal["terminal-x.v1"] = "terminal-x.v1"
    likelihood: Literal["independent-gaussian-discrepancy.v1"] = (
        "independent-gaussian-discrepancy.v1"
    )
    reference_measure: Literal["physical-k-lebesgue.v1"] = "physical-k-lebesgue.v1"
    prior: Literal["uniform-support-density.v1"] = "uniform-support-density.v1"
    discrepancy: Annotated[float, Field(gt=0.0)]
    cells: Annotated[tuple[EndpointCell, ...], Field(min_length=1, max_length=MAX_CELLS)]

    @model_validator(mode="after")
    def contiguous_partition(self) -> Self:
        if any(a.right != b.left for a, b in zip(self.cells, self.cells[1:], strict=False)):
            raise ValueError("Cells must partition one contiguous support")
        return self


class NativeEndpointBeliefInput(Message):
    """Typed construction helper; execution accepts bounded raw JSON only."""

    schema_version: Literal["strange-physics.native-endpoint-belief-input.v1"] = (
        "strange-physics.native-endpoint-belief-input.v1"
    )
    attempt_id: Identifier
    candidate_attempt_id: Identifier
    candidate_input: NativeCandidateInput
    candidate_result: NativeCandidateResult
    prediction_config: NativePredictionConfig
    profile: EndpointBeliefProfile
    prediction_budget: PredictionCount

    @model_validator(mode="after")
    def ordered_representatives(self) -> Self:
        nodes = self.candidate_input.pool.coefficients
        if len(nodes) != len(self.profile.cells):
            raise ValueError("Every ordered candidate needs exactly one cell")
        if any(
            not cell.left <= node <= cell.right
            for cell, node in zip(self.profile.cells, nodes, strict=True)
        ):
            raise ValueError("Each physical coefficient must lie in its declared cell")
        duration = self.candidate_input.observations.space.sampling.duration
        for record in self.candidate_input.observations.records:
            if record.trajectory is not None and (
                record.trajectory.frames[-1].time.hex() != duration.hex()
            ):
                raise ValueError("Terminal observations must retain the exact declared duration")
        bounded_canonical(self, MAX_INPUT_BYTES)
        return self


class EndpointNodeEvaluation(Message):
    model_sha256: Digest
    log_likelihood: float
    log_prior_mass: Annotated[float, Field(le=0.0)]


class NativeEndpointBeliefResult(Message):
    """Complete finite computation or failure; no MAP or calibration claim."""

    schema_version: Literal["strange-physics.native-endpoint-belief-result.v1"] = (
        "strange-physics.native-endpoint-belief-result.v1"
    )
    attempt_id: Identifier
    input_raw_sha256: Digest
    input_sha256: Digest
    profile_sha256: Digest
    candidate_result_sha256: Digest
    observation_sha256: Digest
    status: Literal["normalized", "rejected", "failed"]
    reason: Reason | None
    candidate_count: Annotated[int, Field(ge=1, le=MAX_CELLS)]
    completed_record_indices: Annotated[tuple[RecordIndex, ...], Field(max_length=MAX_RECORDS)]
    failed_record_indices: Annotated[tuple[RecordIndex, ...], Field(max_length=MAX_RECORDS)]
    predictions_requested: PredictionCount
    predictions_completed: PredictionCount
    predictions_failed: Annotated[int, Field(ge=0, le=1)]
    predictions_unassessed: PredictionCount
    frames_completed: FrameCount
    frames_failed: Annotated[int, Field(ge=0, le=1)]
    frames_unassessed: FrameCount
    likelihood_evaluations: PredictionCount
    completed_nodes: Annotated[int, Field(ge=0, le=MAX_CELLS)]
    failed_node_index: NodeIndex | None
    failed_record_index: RecordIndex | None
    prediction_result_sha256: Annotated[tuple[Digest, ...], Field(max_length=MAX_PREDICTIONS)]
    nodes: Annotated[tuple[EndpointNodeEvaluation, ...], Field(max_length=MAX_CELLS)]
    normalizer_input: FiniteLogWeightInput | None
    normalization: FiniteLogWeightResult | None

    @model_validator(mode="after")
    def whole_outcome(self) -> Self:
        completed, failed = self.completed_record_indices, self.failed_record_indices
        for values in (completed, failed):
            if any(a >= b for a, b in zip(values, values[1:], strict=False)):
                raise ValueError("Record indices must be strictly ordered")
        if sorted((*completed, *failed)) != list(range(len(completed) + len(failed))):
            raise ValueError("Record indices must retain the complete contiguous prefix")
        if (
            self.predictions_requested != self.candidate_count * len(completed)
            or self.predictions_completed + self.predictions_failed + self.predictions_unassessed
            != self.predictions_requested
            or self.frames_completed + self.frames_failed + self.frames_unassessed
            != 2 * self.predictions_requested
            or self.frames_completed < 2 * self.predictions_completed
            or self.frames_completed + self.frames_failed
            > 2 * (self.predictions_completed + self.predictions_failed)
            or self.frames_failed > self.predictions_failed
            or len(self.prediction_result_sha256)
            != self.predictions_completed + self.predictions_failed
            or self.likelihood_evaluations > self.predictions_completed
            or self.completed_nodes > self.candidate_count
        ):
            raise ValueError("Work counts must retain every attempted and unassessed unit")
        extra_frames = (self.frames_completed - 2 * self.predictions_completed, self.frames_failed)
        allowed_frames = {(0, 0), (0, 1), (1, 1)} if self.predictions_failed else {(0, 0)}
        if extra_frames not in allowed_frames:
            raise ValueError("Failed two-frame prediction must retain a reachable frame prefix")
        paired = self.normalizer_input is not None and self.normalization is not None
        if (self.normalizer_input is None) != (self.normalization is None):
            raise ValueError("Normalization requires its complete actual log-weight input")
        if paired:
            assert self.normalizer_input is not None and self.normalization is not None
            if (
                len(self.nodes) != self.candidate_count
                or self.completed_nodes != self.candidate_count
                or self.predictions_completed != self.predictions_requested
                or self.likelihood_evaluations != self.predictions_requested
                or len(self.normalizer_input.entries) != self.candidate_count
                or self.failed_node_index is not None
                or self.failed_record_index is not None
            ):
                raise ValueError("Normalization follows complete node and record evaluation")
            for node, entry in zip(self.nodes, self.normalizer_input.entries, strict=True):
                if (
                    entry.kind != "finite"
                    or entry.item_sha256 != node.model_sha256
                    or entry.log_weight != node.log_likelihood + node.log_prior_mass
                ):
                    raise ValueError("Normalizer must receive every complete finite node weight")
            bind_finite_log_weight_result(self.normalization, self.normalizer_input)
        elif self.nodes:
            raise ValueError("An interrupted node pass cannot expose a partial node set")
        rejection_reasons = {
            "no_completed_records",
            "candidate_unavailable",
            "unsupported_observation_noise",
            "prediction_budget",
        }
        if (self.status == "rejected") != (self.reason in rejection_reasons):
            raise ValueError("Status and deterministic failure stage must agree")
        if self.reason in {"prior_arithmetic", "likelihood_arithmetic"} and (
            self.failed_node_index is None
        ):
            if (
                self.predictions_completed
                or self.predictions_failed
                or self.likelihood_evaluations
                or self.completed_nodes
                or paired
                or self.failed_record_index is not None
            ):
                raise ValueError("Preflight arithmetic failure must precede all forward work")
        if self.reason == "prior_arithmetic" and self.failed_node_index is not None:
            raise ValueError("Prior arithmetic is checked before the node loop")
        if self.status == "normalized":
            if (
                not paired
                or self.normalization is None
                or self.normalization.status != "normalized"
                or self.reason is not None
            ):
                raise ValueError("Success requires complete normalization")
        elif self.reason is None or (
            self.normalization is not None and self.normalization.status == "normalized"
        ):
            raise ValueError("Failure cannot carry successful normalized weights")
        if self.status == "rejected" and (
            self.predictions_completed
            or self.predictions_failed
            or self.likelihood_evaluations
            or self.completed_nodes
            or paired
            or self.failed_node_index is not None
            or self.failed_record_index is not None
        ):
            raise ValueError("Rejection precedes cost-bearing forward and likelihood work")
        if self.reason == "normalization_failure" and (self.status != "failed" or not paired):
            raise ValueError("Normalization failure needs its complete failed algebraic result")
        bounded_canonical(self, MAX_RESULT_BYTES)
        return self


def parse_native_endpoint_belief_input(raw: bytes) -> NativeEndpointBeliefInput:
    return parse_bounded_json(
        raw,
        NativeEndpointBeliefInput,
        max_bytes=MAX_INPUT_BYTES,
        max_depth=40,
        max_nodes=MAX_JSON_NODES,
    )


def parse_native_endpoint_belief_result(raw: bytes) -> NativeEndpointBeliefResult:
    return parse_bounded_json(
        raw,
        NativeEndpointBeliefResult,
        max_bytes=MAX_RESULT_BYTES,
        max_depth=24,
        max_nodes=300_000,
    )


def _bind_result(
    result: NativeEndpointBeliefResult, actual: NativeEndpointBeliefInput, raw: bytes
) -> None:
    """Identity/count binding only; never recompute a scientific forward."""
    observations = actual.candidate_input.observations
    completed = tuple(r.index for r in observations.records if r.status == "completed")
    failed = tuple(r.index for r in observations.records if r.status == "failed")
    if (
        result.attempt_id != actual.attempt_id
        or result.input_raw_sha256 != hashlib.sha256(raw).hexdigest()
        or result.input_sha256 != bounded_canonical(actual, MAX_INPUT_BYTES)[0]
        or result.profile_sha256 != message_sha256(actual.profile)
        or result.candidate_result_sha256
        != bounded_canonical(actual.candidate_result, MAX_RESULT_BYTES)[0]
        or result.observation_sha256 != bounded_canonical(observations, MAX_INPUT_BYTES)[0]
        or result.candidate_count != len(actual.candidate_input.pool.coefficients)
        or result.completed_record_indices != completed
        or result.failed_record_indices != failed
    ):
        raise ValueError("Belief differs from the exact supplied material and raw input")
    if result.nodes:
        for node, model in zip(result.nodes, actual.candidate_result.payload.models, strict=True):
            if node.model_sha256 != message_sha256(model):
                raise ValueError("Node order must retain the actual bound candidate models")
    if result.failed_node_index is not None and result.failed_node_index >= result.candidate_count:
        raise ValueError("Failed node is outside the declared pool")
    if result.failed_record_index is not None and result.failed_record_index not in completed:
        raise ValueError("A failed computation must refer to a completed scientific record")
    sampling = observations.space.sampling
    expected_rejection: Reason | None = None
    if not completed:
        expected_rejection = "no_completed_records"
    elif actual.candidate_result.payload.status != "produced":
        expected_rejection = "candidate_unavailable"
    elif sampling.position_noise != 0.0 or sampling.velocity_noise != 0.0:
        expected_rejection = "unsupported_observation_noise"
    elif actual.prediction_budget < result.predictions_requested:
        expected_rejection = "prediction_budget"
    if expected_rejection is not None:
        if result.status != "rejected" or result.reason != expected_rejection:
            raise ValueError("Ineligible input cannot claim forward work or normalization")
    elif result.status == "rejected":
        raise ValueError("Eligible input cannot claim a preflight rejection")
    reason = result.reason
    if reason == "prediction_failure":
        if result.failed_node_index is None or result.failed_record_index is None:
            raise ValueError("Prediction failure requires the first failed node and record")
        prior = result.failed_node_index * len(completed) + completed.index(
            result.failed_record_index
        )
        if (
            result.predictions_completed != prior
            or result.predictions_failed != 1
            or result.likelihood_evaluations != prior
            or result.completed_nodes != result.failed_node_index
        ):
            raise ValueError("Prediction failure must retain its exact ordered work prefix")
    if reason == "likelihood_arithmetic" and result.failed_node_index is not None:
        if result.failed_record_index is None:
            raise ValueError("A record likelihood failure requires its actual record")
        attempted = (
            result.failed_node_index * len(completed)
            + completed.index(result.failed_record_index)
            + 1
        )
        if (
            result.predictions_completed != attempted
            or result.predictions_failed
            or result.likelihood_evaluations != attempted
            or result.completed_nodes != result.failed_node_index
        ):
            raise ValueError("Likelihood failure must retain its exact ordered work prefix")


def bind_native_endpoint_belief_result(result_raw: bytes, input_raw: bytes) -> None:
    """Bound raw-only ingress; parsing/input joins do not authenticate computation."""
    actual = parse_native_endpoint_belief_input(input_raw)
    result = parse_native_endpoint_belief_result(result_raw)
    validate_native_candidate_result(
        actual.candidate_result, actual.candidate_input, attempt_id=actual.candidate_attempt_id
    )
    _bind_result(result, actual, input_raw)


def native_endpoint_belief_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (model, "validation")
            for model in (
                EndpointCell,
                EndpointBeliefProfile,
                NativeEndpointBeliefInput,
                EndpointNodeEvaluation,
                NativeEndpointBeliefResult,
            )
        ],
        title="Strange Physics restricted endpoint-x finite beliefs v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-endpoint-belief.schema.json"
    schema["description"] = (
        "Supplied-material endpoint-x Gaussian model-belief family with explicit cells and "
        "positive discrepancy. Raw entry points and actual-input binding are required. "
        "No Journal authority, MAP, covariance calibration or study-profile acceptance."
    )
    return schema
