"""Native analytic propagation, separate from the paired-Simpson predictor profile."""

from __future__ import annotations

import math

from pydantic import TypeAdapter

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Frame, Identifier, Trajectory
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    NativePredictionOutcome,
    NativePredictionResult,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import (
    MAX_INPUT_BYTES,
    MAX_RESULT_BYTES,
    NativeWorkFacts,
)
from strange_physics.prediction import _NonfiniteState, _state_at_time
from strange_physics.prediction_contracts import PredictionReason, PredictionStatus
from strange_physics.research_contracts import PredictionResponse, message_sha256


def _preflight(actual: NativePredictionInput) -> tuple[PredictionStatus, PredictionReason] | None:
    model, request, config = actual.model, actual.request, actual.config
    if request.model_sha256 != message_sha256(model):
        return "model_mismatch", "model_digest_mismatch"
    if model.fitter_version != config.supported_producer_version:
        return "unsupported_runtime", "unsupported_fitter_version"
    candidate_sha = message_sha256(actual.candidate_config)
    if (
        model.fit_config_sha256 != candidate_sha
        or candidate_sha != config.supported_candidate_config_sha256
    ):
        return "unsupported_runtime", "unsupported_fit_configuration"
    if model.through_index > 11:
        return "unsupported_domain", "resource_limit"
    structure = request.structure
    if (
        len(structure.particle_ids) != config.particle_count
        or len(structure.anchors) != config.anchor_count
        or len(structure.connections) != config.connection_count
        or {structure.connections[0].a, structure.connections[0].b}
        != {structure.particle_ids[0], structure.anchors[0].id}
    ):
        return "unsupported_domain", "unsupported_topology"
    if not config.min_coefficient <= model.linear <= config.max_coefficient:
        return "unsupported_domain", "coefficient_outside_domain"
    if math.hypot(*structure.anchors[0].position) > config.max_anchor_norm:
        return "unsupported_domain", "anchor_outside_domain"
    particle = request.experiment.particles[0]
    if not config.min_mass <= particle.mass <= config.max_mass:
        return "unsupported_domain", "mass_outside_domain"
    if math.hypot(*particle.position) > config.max_initial_position_norm:
        return "unsupported_domain", "position_outside_domain"
    if math.hypot(*particle.velocity) > config.max_initial_velocity_norm:
        return "unsupported_domain", "velocity_outside_domain"
    if (
        request.experiment.impulse
        and math.hypot(*request.experiment.impulse.vector) > config.max_impulse_norm
    ):
        return "unsupported_domain", "impulse_outside_domain"
    if request.times[-1] > config.max_horizon:
        return "unsupported_domain", "horizon_outside_domain"
    if (
        len(request.times) > config.max_output_frames
        or not config.min_integration_dt <= request.integration_dt <= config.max_integration_dt
        or round(request.times[-1] / request.integration_dt) > config.max_reference_steps
    ):
        return "unsupported_domain", "resource_limit"
    return None


def predict_native_spring(
    actual: NativePredictionInput, *, attempt_id: str
) -> NativePredictionResult:
    """Return all requested frames or one counted failure without a partial response.

    Only the pure oscillator kernel is shared with v1. No fitter artifact, hidden
    law, purchased-action validator, numerical integrator or ledger is invoked.
    """
    TypeAdapter(Identifier).validate_python(attempt_id)
    model, request, config = actual.model, actual.request, actual.config
    failure = _preflight(actual)
    status: PredictionStatus = "predicted"
    reason: PredictionReason | None = None
    frames: list[Frame] = []
    failed_index: int | None = None
    if failure is not None:
        status, reason = failure
    else:
        # Fixed one-particle topology and <=2,001 frames bound allocation before
        # final canonical-byte validation; no partial list escapes on failure.
        for index, time in enumerate(request.times):
            try:
                position, velocity = _state_at_time(model, request, time)
                if not all(math.isfinite(value) for value in (*position, *velocity)):
                    reason = "nonfinite_state"
                elif (
                    math.hypot(*position) > config.max_output_position_norm
                    or math.hypot(*velocity) > config.max_output_velocity_norm
                ):
                    reason = "output_bound"
                else:
                    frames.append(Frame(time=time, positions=(position,), velocities=(velocity,)))
            except _NonfiniteState:
                reason = "nonfinite_state"
            except (ArithmeticError, ValueError):
                reason = "arithmetic_failure"
            if reason is not None:
                status, failed_index = "numerical_failure", index
                break
    model_sha = message_sha256(model)
    payload = NativePredictionOutcome(
        status=status,
        reason=reason,
        actual_model_sha256=model_sha,
        requested_model_sha256=request.model_sha256,
        request_sha256=message_sha256(request),
        candidate_config_sha256=message_sha256(actual.candidate_config),
        prediction_config_sha256=message_sha256(config),
        observation_sha256=model.observation_sha256,
        predictor_version=config.predictor_version,
        requested_frame_count=len(request.times),
        computed_frame_count=len(frames),
        returned_frame_count=len(frames) if status == "predicted" else 0,
        failed_frame_index=failed_index,
        response=PredictionResponse(
            model_sha256=model_sha, trajectory=Trajectory(frames=tuple(frames))
        )
        if status == "predicted"
        else None,
    )
    failed = int(failed_index is not None)
    result = NativePredictionResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="prediction",
            producer_version=config.predictor_version,
            config_sha256=message_sha256(config),
            input_sha256=bounded_canonical(actual, MAX_INPUT_BYTES)[0],
            observation_sha256=model.observation_sha256,
            model_sha256=model_sha,
            output_sha256=bounded_canonical(payload, MAX_RESULT_BYTES)[0],
            unit="frame",
            requested_count=len(request.times),
            completed_count=len(frames),
            failed_count=failed,
            not_assessed_count=len(request.times) - len(frames) - failed,
            outcome="completed" if status == "predicted" else "failed" if failed else "rejected",
        ),
    )
    validate_native_prediction_result(result, actual, attempt_id=attempt_id)
    return result
