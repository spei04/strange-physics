"""Bounded analytic propagation of the versioned local linear spring model."""

from __future__ import annotations

import math

from strange_physics.contracts import Frame, Trajectory, Vector
from strange_physics.prediction_contracts import (
    PredictionReason,
    PredictionStatus,
    SpringPredictionConfig,
    SpringPredictionDiagnostics,
    SpringPredictionResult,
    validate_spring_prediction_result,
)
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
)


def _preflight(
    model: LinearSpringModel,
    request: PredictionRequest,
    config: SpringPredictionConfig,
    actual_model_sha256: str,
) -> tuple[PredictionStatus, PredictionReason] | None:
    if request.model_sha256 != actual_model_sha256:
        return "model_mismatch", "model_digest_mismatch"
    if model.schema_version != config.supported_model_version:
        return "unsupported_runtime", "unsupported_model_version"
    if model.fitter_version != config.supported_fitter_version:
        return "unsupported_runtime", "unsupported_fitter_version"
    if model.fit_config_sha256 != config.supported_fit_config_sha256:
        return "unsupported_runtime", "unsupported_fit_configuration"
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


class _NonfiniteState(ArithmeticError):
    """An internal derived value is unrepresentable; never expose raw error text."""


def _state_at_time(
    model: LinearSpringModel, request: PredictionRequest, time: float
) -> tuple[Vector, Vector]:
    particle = request.experiment.particles[0]
    anchor = request.structure.anchors[0].position
    impulse = request.experiment.impulse
    velocity = (
        particle.velocity[0] + (impulse.vector[0] / particle.mass if impulse else 0.0),
        particle.velocity[1] + (impulse.vector[1] / particle.mass if impulse else 0.0),
    )
    if time == 0:
        # Preserve exact requested initial values, including tiny signed components.
        return particle.position, velocity
    if model.linear == 0:
        return (
            particle.position[0] + velocity[0] * time,
            particle.position[1] + velocity[1] * time,
        ), velocity
    displacement = (particle.position[0] - anchor[0], particle.position[1] - anchor[1])
    acceleration_factor = model.linear / particle.mass
    phase = math.sqrt(acceleration_factor) * time
    sinc = 1.0 if phase == 0 else math.sin(phase) / phase
    cosine = math.cos(phase)
    if not all(
        math.isfinite(value)
        for value in (
            *displacement,
            *velocity,
            acceleration_factor,
            phase,
            sinc,
            cosine,
        )
    ):
        raise _NonfiniteState
    # k/m may underflow for a subnormal coefficient. The continuous limit is
    # ballistic; retain the original coefficient and avoid division by frequency.
    position = (
        anchor[0] + displacement[0] * cosine + velocity[0] * time * sinc,
        anchor[1] + displacement[1] * cosine + velocity[1] * time * sinc,
    )
    predicted_velocity = (
        velocity[0] * cosine - displacement[0] * acceleration_factor * time * sinc,
        velocity[1] * cosine - displacement[1] * acceleration_factor * time * sinc,
    )
    return position, predicted_velocity


def predict_linear_spring(
    model: LinearSpringModel,
    request: PredictionRequest,
    config: SpringPredictionConfig,
) -> SpringPredictionResult:
    """Predict all exact requested times, or return a failure with no partial response.

    integration_dt validates grid/replay metadata; this runtime executes the
    analytic equation and does not step an integrator. No evaluator truth or
    hidden world is an input, and successful propagation is not forecast accuracy.
    """
    actual_model_sha256 = message_sha256(model)
    failure = _preflight(model, request, config, actual_model_sha256)
    status: PredictionStatus = "predicted"
    reason: PredictionReason | None = None
    frames: list[Frame] = []
    failed_index = None
    if failure is not None:
        status, reason = failure
    else:
        for index, time in enumerate(request.times):
            try:
                position, velocity = _state_at_time(model, request, time)
            except _NonfiniteState:
                reason = "nonfinite_state"
            except (ArithmeticError, ValueError):
                reason = "arithmetic_failure"
            else:
                if not all(math.isfinite(value) for value in (*position, *velocity)):
                    reason = "nonfinite_state"
                elif (
                    math.hypot(*position) > config.max_output_position_norm
                    or math.hypot(*velocity) > config.max_output_velocity_norm
                ):
                    reason = "output_bound"
                else:
                    frames.append(Frame(time=time, positions=(position,), velocities=(velocity,)))
            if reason is not None:
                status, failed_index = "numerical_failure", index
                break
    response = (
        PredictionResponse(
            model_sha256=actual_model_sha256, trajectory=Trajectory(frames=tuple(frames))
        )
        if status == "predicted"
        else None
    )
    diagnostics = SpringPredictionDiagnostics(
        actual_model_sha256=actual_model_sha256,
        requested_model_sha256=request.model_sha256,
        request_sha256=message_sha256(request),
        prediction_config_sha256=message_sha256(config),
        predictor_version=config.predictor_version,
        requested_frame_count=len(request.times),
        computed_frame_count=len(frames),
        returned_frame_count=len(frames) if response is not None else 0,
        failed_frame_index=failed_index,
    )
    result = SpringPredictionResult(
        status=status, reason=reason, response=response, diagnostics=diagnostics
    )
    validate_spring_prediction_result(result, model, request, config)
    return result
