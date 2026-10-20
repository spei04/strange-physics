"""Fit a shared linear spring from an explicit purchased public prefix only."""

from __future__ import annotations

import math
from dataclasses import dataclass

from strange_physics.contracts import ExperimentRecord, ObservationBundle
from strange_physics.fitting_contracts import (
    FitReason,
    FitStatus,
    SpringFitConfig,
    SpringFitDiagnostics,
    SpringFitResult,
    validate_fit_result,
)
from strange_physics.research_contracts import LinearSpringModel, SpringFitInput, message_sha256


def _domain_reason(prefix: ObservationBundle, config: SpringFitConfig) -> FitReason | None:
    structure, sampling = prefix.space.structure, prefix.space.sampling
    if (
        len(structure.particle_ids) != config.particle_count
        or len(structure.anchors) != config.anchor_count
        or len(structure.connections) != config.connection_count
        or {structure.connections[0].a, structure.connections[0].b}
        != {structure.particle_ids[0], structure.anchors[0].id}
    ):
        return "unsupported_topology"
    if math.hypot(*structure.anchors[0].position) > config.max_anchor_norm:
        return "anchor_outside_domain"
    if (
        sampling.duration != config.duration
        or sampling.sample_interval != config.sample_interval
        or sampling.dt not in config.integration_steps
    ):
        return "unsupported_sampling"
    completed = sum(record.status == "completed" for record in prefix.records)
    rows_per_record = int(config.duration / config.sample_interval)
    if (
        len(prefix.records) > config.max_records
        or completed * rows_per_record > config.max_scalar_rows
    ):
        return "work_limit"
    # Failed actions remain part of the declared prefix domain and provenance,
    # but never supply observed rows or determine a favorable fit selection.
    for record in prefix.records:
        particle = record.experiment.particles[0]
        if not config.min_mass <= particle.mass <= config.max_mass:
            return "mass_outside_domain"
        if math.hypot(*particle.position) > config.max_position_norm:
            return "position_outside_domain"
        if math.hypot(*particle.velocity) > config.max_velocity_norm:
            return "velocity_outside_domain"
        if (
            record.experiment.impulse
            and math.hypot(*record.experiment.impulse.vector) > config.max_impulse_norm
        ):
            return "impulse_outside_domain"
        if record.trajectory is not None and len(record.trajectory.frames) != rows_per_record + 1:
            return "unsupported_sampling"
    return None


@dataclass(frozen=True)
class _Estimate:
    raw: float | None = None
    design_rms: float | None = None
    reason: FitReason | None = None


def _record_reductions(
    record: ExperimentRecord, anchor: tuple[float, float], config: SpringFitConfig
) -> tuple[float, float, FitReason | None]:
    # Each completed record has 20 complete paired windows and 40 scalar rows.
    # Keep only this record's products, then reduce in the public record order.
    assert record.trajectory is not None
    frames = record.trajectory.frames
    mass = record.experiment.particles[0].mass
    squares, products = [], []
    for start in range(0, len(frames) - config.window_stride, config.window_stride):
        first, middle, last = frames[start : start + config.window_samples]
        for coordinate in range(config.coordinates):
            r0 = first.positions[0][coordinate] - anchor[coordinate]
            r1 = middle.positions[0][coordinate] - anchor[coordinate]
            r2 = last.positions[0][coordinate] - anchor[coordinate]
            design = -config.sample_interval * (r0 + 4 * r1 + r2) / (3 * mass)
            response = last.velocities[0][coordinate] - first.velocities[0][coordinate]
            if not math.isfinite(design) or not math.isfinite(response):
                return 0.0, 0.0, "nonfinite_columns"
            square, product = design * design, design * response
            if not math.isfinite(square) or not math.isfinite(product):
                return 0.0, 0.0, "nonfinite_reduction"
            squares.append(square)
            products.append(product)
    try:
        energy, cross = math.fsum(squares), math.fsum(products)
    except OverflowError:
        return 0.0, 0.0, "nonfinite_reduction"
    if not math.isfinite(energy) or not math.isfinite(cross):
        return 0.0, 0.0, "nonfinite_reduction"
    return energy, cross, None


def _estimate(prefix: ObservationBundle, config: SpringFitConfig, row_count: int) -> _Estimate:
    energies, crosses = [], []
    anchor = prefix.space.structure.anchors[0].position
    for record in prefix.records:
        if record.status == "failed":
            continue
        energy, cross, reason = _record_reductions(record, anchor, config)
        if reason is not None:
            return _Estimate(reason=reason)
        energies.append(energy)
        crosses.append(cross)
    try:
        energy, cross = math.fsum(energies), math.fsum(crosses)
    except OverflowError:
        return _Estimate(reason="nonfinite_reduction")
    if not math.isfinite(energy) or not math.isfinite(cross):
        return _Estimate(reason="nonfinite_reduction")
    design_rms = math.sqrt(energy / row_count)
    if design_rms < config.min_design_rms:
        return _Estimate(design_rms=design_rms, reason="below_excitation_floor")
    raw = cross / energy
    if not math.isfinite(raw):
        return _Estimate(design_rms=design_rms, reason="nonfinite_coefficient")
    return _Estimate(
        raw=raw,
        design_rms=design_rms,
        reason="negative_coefficient" if raw < 0 else None,
    )


def fit_linear_spring(request: SpringFitInput, config: SpringFitConfig) -> SpringFitResult:
    """Return an inspectable estimate or an explicit failure from validated messages.

    A fitted result is a numerical artifact under the declared stationary linear
    model assumption. It makes no accuracy, uncertainty or prediction claim.
    No hidden world, evaluator labels or records beyond this prefix are inputs.
    """
    prefix = request.observations
    completed = tuple(record.index for record in prefix.records if record.status == "completed")
    actual_config_sha256 = message_sha256(config)
    prefix_sha256 = message_sha256(prefix)
    status: FitStatus = "configuration_mismatch"
    reason: FitReason | None = "configuration_digest_mismatch"
    estimate, row_count = _Estimate(), 0
    if request.fit_config_sha256 == actual_config_sha256:
        reason = _domain_reason(prefix, config)
        if reason is not None:
            status = "unsupported_domain"
        else:
            # Count the complete manifest even if arithmetic fails before its end.
            row_count = len(completed) * int(config.duration / config.sample_interval)
            estimate = _estimate(prefix, config, row_count)
            reason = estimate.reason
            status = (
                "fitted"
                if reason is None
                else "insufficient_excitation"
                if reason == "below_excitation_floor"
                else "negative_estimate"
                if reason == "negative_coefficient"
                else "numerical_failure"
            )
    diagnostics = SpringFitDiagnostics(
        through_index=request.through_index,
        observation_sha256=prefix_sha256,
        requested_config_sha256=request.fit_config_sha256,
        actual_config_sha256=actual_config_sha256,
        fitter_version=config.fitter_version,
        record_count=len(prefix.records),
        completed_record_count=len(completed),
        failed_record_count=len(prefix.records) - len(completed),
        completed_record_indices=completed,
        scalar_row_count=row_count,
        design_rms=estimate.design_rms,
        raw_coefficient=estimate.raw,
        declared_noisy=bool(
            prefix.space.sampling.position_noise or prefix.space.sampling.velocity_noise
        ),
        estimated_coefficient_in_calibrated_range=(
            None if estimate.raw is None else 0 <= estimate.raw <= config.calibrated_coefficient_max
        ),
    )
    model = None
    if status == "fitted":
        assert estimate.raw is not None
        model = LinearSpringModel(
            linear=estimate.raw,
            through_index=request.through_index,
            fit_record_indices=completed,
            observation_sha256=prefix_sha256,
            fit_config_sha256=actual_config_sha256,
            fitter_version=config.fitter_version,
        )
    result = SpringFitResult(status=status, reason=reason, model=model, diagnostics=diagnostics)
    validate_fit_result(result, request, config)
    return result
