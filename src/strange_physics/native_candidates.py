"""Produce the exact declared native candidate set from public purchased observations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import TypeAdapter

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Identifier
from strange_physics.native_spring_contracts import (
    MAX_INPUT_BYTES,
    MAX_RESULT_BYTES,
    NATIVE_PRODUCER,
    NativeCandidateInput,
    NativeCandidateOutcome,
    NativeCandidateResult,
    NativeWorkFacts,
    validate_native_candidate_result,
)
from strange_physics.research_contracts import LinearSpringModel, message_sha256


def _supported_purchases(actual: NativeCandidateInput) -> bool:
    """Check actual actions, including failed records; never inspect a hidden law."""
    space = actual.observations.space
    structure = space.structure
    if (
        len(structure.particle_ids) != 1
        or len(structure.anchors) != 1
        or len(structure.connections) != 1
        or {structure.connections[0].a, structure.connections[0].b}
        != {structure.particle_ids[0], structure.anchors[0].id}
        or math.hypot(*structure.anchors[0].position) > 0.5
        or space.sampling.duration > 2.0
    ):
        return False
    for record in actual.observations.records:
        particle = record.experiment.particles[0]
        if (
            not 0.5 <= particle.mass <= 2.0
            or math.hypot(*particle.position) > 2.0
            or math.hypot(*particle.velocity) > 2.0
            or (
                record.experiment.impulse is not None
                and math.hypot(*record.experiment.impulse.vector) > 1.0
            )
        ):
            return False
    return True


def produce_native_candidates(
    actual: NativeCandidateInput, *, attempt_id: str
) -> NativeCandidateResult:
    """Enumerate a declared pool, retaining the complete actual committed prefix.

    This does not estimate coefficients or prove that the caller supplied every
    purchased reservation. A Journal adapter must first resolve pending/missing
    intents. The assumption is explicit; no hidden law or evaluator input is used.
    """
    TypeAdapter(Identifier).validate_python(attempt_id)
    observations = actual.observations
    completed = tuple(
        record.index for record in observations.records if record.status == "completed"
    )
    observation_sha = bounded_canonical(observations, MAX_INPUT_BYTES)[0]
    config_sha = message_sha256(actual.config)
    models: list[LinearSpringModel] = []
    failed_index: int | None = None
    status: Literal["produced", "rejected", "failed"] = "produced"
    reason: (
        Literal["no_completed_records", "unsupported_domain", "candidate_construction"] | None
    ) = None
    if not completed:
        status, reason = "rejected", "no_completed_records"
    elif not _supported_purchases(actual):
        status, reason = "rejected", "unsupported_domain"
    else:
        # At most 1,025 models, each with <=12 indices and bounded metadata:
        # construction is bounded before the final canonical result byte check.
        for index, coefficient in enumerate(actual.pool.coefficients):
            try:
                model = LinearSpringModel(
                    linear=coefficient,
                    through_index=len(observations.records) - 1,
                    fit_record_indices=completed,
                    observation_sha256=observation_sha,
                    fitter_version=actual.config.producer_version,
                    fit_config_sha256=config_sha,
                )
            except (ArithmeticError, ValueError):
                status, reason, failed_index = "failed", "candidate_construction", index
                break
            models.append(model)
    count = len(actual.pool.coefficients)
    payload = NativeCandidateOutcome(
        status=status,
        reason=reason,
        pool_sha256=message_sha256(actual.pool),
        observation_sha256=observation_sha,
        producer_config_sha256=config_sha,
        through_index=len(observations.records) - 1,
        completed_record_indices=completed,
        failed_record_count=len(observations.records) - len(completed),
        requested_candidate_count=count,
        produced_candidate_count=len(models),
        failed_candidate_index=failed_index,
        models=tuple(models) if status == "produced" else (),
    )
    failed = int(failed_index is not None)
    result = NativeCandidateResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="candidate_production",
            producer_version=NATIVE_PRODUCER,
            config_sha256=config_sha,
            input_sha256=bounded_canonical(actual, MAX_INPUT_BYTES)[0],
            observation_sha256=observation_sha,
            model_sha256=None,
            output_sha256=bounded_canonical(payload, MAX_RESULT_BYTES)[0],
            unit="candidate",
            requested_count=count,
            completed_count=len(models),
            failed_count=failed,
            not_assessed_count=count - len(models) - failed,
            outcome="completed" if status == "produced" else status,
        ),
    )
    validate_native_candidate_result(result, actual, attempt_id=attempt_id)
    return result
