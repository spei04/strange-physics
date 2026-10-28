"""Pure restricted endpoint-x finite beliefs; no study authority or calibrated profile."""

from __future__ import annotations

import hashlib
import math
from typing import Literal

from strange_physics.bounded_json import bounded_canonical
from strange_physics.finite_log_weight_contracts import (
    FiniteLogWeight,
    FiniteLogWeightInput,
    FiniteLogWeightResult,
)
from strange_physics.finite_log_weights import normalize_finite_log_weights
from strange_physics.native_endpoint_belief_contracts import (
    MAX_INPUT_BYTES,
    MAX_RESULT_BYTES,
    EndpointNodeEvaluation,
    NativeEndpointBeliefResult,
    Reason,
    _bind_result,
    parse_native_endpoint_belief_input,
)
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import validate_native_candidate_result
from strange_physics.research_contracts import PredictionRequest, message_sha256

LiteralStatus = Literal["normalized", "rejected", "failed"]


def compute_native_endpoint_belief(raw: bytes) -> NativeEndpointBeliefResult:
    """Evaluate all nodes or return one complete failure; accepts raw JSON only.

    Typed models are construction/serialization helpers. Even model_construct or
    model_copy inputs must pass bounded raw parsing before any scientific work.
    Independent endpoint residuals and zero declared observation noise are this
    restricted family's semantics, not validated study assumptions.
    """
    actual = parse_native_endpoint_belief_input(raw)
    source = actual.candidate_input
    candidate = actual.candidate_result
    validate_native_candidate_result(candidate, source, attempt_id=actual.candidate_attempt_id)
    observations = source.observations
    completed = tuple(r.index for r in observations.records if r.status == "completed")
    failed = tuple(r.index for r in observations.records if r.status == "failed")
    count = len(source.pool.coefficients)
    requested = count * len(completed)
    predicted = prediction_failures = frames = frame_failures = likelihood_calls = node_count = 0
    prediction_hashes: list[str] = []
    nodes: list[EndpointNodeEvaluation] = []
    log_input: FiniteLogWeightInput | None = None
    normalized: FiniteLogWeightResult | None = None

    def finish(
        status: LiteralStatus,
        reason: Reason | None = None,
        node_index: int | None = None,
        record_index: int | None = None,
    ) -> NativeEndpointBeliefResult:
        result = NativeEndpointBeliefResult(
            attempt_id=actual.attempt_id,
            input_raw_sha256=hashlib.sha256(raw).hexdigest(),
            input_sha256=bounded_canonical(actual, MAX_INPUT_BYTES)[0],
            profile_sha256=message_sha256(actual.profile),
            candidate_result_sha256=bounded_canonical(candidate, MAX_RESULT_BYTES)[0],
            observation_sha256=bounded_canonical(observations, MAX_INPUT_BYTES)[0],
            status=status,
            reason=reason,
            candidate_count=count,
            completed_record_indices=completed,
            failed_record_indices=failed,
            predictions_requested=requested,
            predictions_completed=predicted,
            predictions_failed=prediction_failures,
            predictions_unassessed=requested - predicted - prediction_failures,
            frames_completed=frames,
            frames_failed=frame_failures,
            frames_unassessed=2 * requested - frames - frame_failures,
            likelihood_evaluations=likelihood_calls,
            completed_nodes=node_count,
            failed_node_index=node_index,
            failed_record_index=record_index,
            prediction_result_sha256=tuple(prediction_hashes),
            nodes=tuple(nodes) if log_input is not None else (),
            normalizer_input=log_input,
            normalization=normalized,
        )
        _bind_result(result, actual, raw)
        return result

    if not completed:
        return finish("rejected", "no_completed_records")
    if candidate.payload.status != "produced":
        return finish("rejected", "candidate_unavailable")
    sampling = observations.space.sampling
    if sampling.position_noise != 0.0 or sampling.velocity_noise != 0.0:
        return finish("rejected", "unsupported_observation_noise")
    if actual.prediction_budget < requested:
        return finish("rejected", "prediction_budget")

    sigma = actual.profile.discrepancy
    try:
        variance = sigma * sigma
        constant = -math.log(sigma) - 0.5 * math.log(2.0 * math.pi)
        if not math.isfinite(variance) or variance <= 0.0 or not math.isfinite(constant):
            return finish("failed", "likelihood_arithmetic")
    except (ArithmeticError, ValueError):
        return finish("failed", "likelihood_arithmetic")
    try:
        cells = actual.profile.cells
        span = cells[-1].right - cells[0].left
        log_priors = []
        for cell in cells:
            mass = (cell.right - cell.left) / span
            if not math.isfinite(mass) or not 0.0 < mass <= 1.0:
                return finish("failed", "prior_arithmetic")
            log_priors.append(math.log(mass))
    except (ArithmeticError, ValueError):
        return finish("failed", "prior_arithmetic")

    for node_index, model in enumerate(candidate.payload.models):
        terms: list[float] = []
        for record_index in completed:
            record = observations.records[record_index]
            assert record.trajectory is not None
            terminal = record.trajectory.frames[-1]
            prediction_input = NativePredictionInput(
                model=model,
                candidate_config=source.config,
                request=PredictionRequest(
                    model_sha256=message_sha256(model),
                    structure=observations.space.structure,
                    experiment=record.experiment,
                    times=(0.0, terminal.time),
                    integration_dt=sampling.dt,
                ),
                config=actual.prediction_config,
            )
            prediction = predict_native_spring(prediction_input, attempt_id=actual.attempt_id)
            validate_native_prediction_result(
                prediction, prediction_input, attempt_id=actual.attempt_id
            )
            prediction_hashes.append(bounded_canonical(prediction, MAX_RESULT_BYTES)[0])
            frames += prediction.payload.computed_frame_count
            frame_failures += prediction.facts.failed_count
            if prediction.payload.status != "predicted":
                prediction_failures += 1
                return finish("failed", "prediction_failure", node_index, record_index)
            predicted += 1
            response = prediction.payload.response
            assert response is not None
            likelihood_calls += 1
            try:
                residual = terminal.positions[0][0] - response.trajectory.frames[-1].positions[0][0]
                standardized = residual / sigma
                value = constant - 0.5 * standardized * standardized
                if not all(math.isfinite(v) for v in (residual, standardized, value)):
                    return finish("failed", "likelihood_arithmetic", node_index, record_index)
                terms.append(value)
            except (ArithmeticError, ValueError):
                return finish("failed", "likelihood_arithmetic", node_index, record_index)
        try:
            likelihood = math.fsum(terms)
            if not math.isfinite(likelihood + log_priors[node_index]):
                return finish("failed", "likelihood_arithmetic", node_index, completed[-1])
            nodes.append(
                EndpointNodeEvaluation(
                    model_sha256=message_sha256(model),
                    log_likelihood=likelihood,
                    log_prior_mass=log_priors[node_index],
                )
            )
            node_count += 1
        except (ArithmeticError, ValueError):
            return finish("failed", "likelihood_arithmetic", node_index, completed[-1])

    log_input = FiniteLogWeightInput(
        entries=tuple(
            FiniteLogWeight(
                item_sha256=node.model_sha256,
                kind="finite",
                log_weight=node.log_likelihood + node.log_prior_mass,
            )
            for node in nodes
        )
    )
    normalized = normalize_finite_log_weights(log_input)
    if normalized.status != "normalized":
        return finish("failed", "normalization_failure")
    return finish("normalized")
