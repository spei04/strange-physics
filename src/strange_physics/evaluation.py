"""Independent bounded development scoring with evaluator-only analytic references."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from time import perf_counter_ns

from pydantic import ValidationError

from strange_physics.contracts import Structure, Vector
from strange_physics.evaluation_contracts import (
    EvaluationReason,
    EvaluationStatus,
    PredictionAssessment,
    ProbeAssessment,
    ProbePrediction,
    ReferenceProbe,
    SpringEvaluationDiagnostics,
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    SpringPredictionSubmissions,
    SpringReferenceArtifact,
    validate_spring_evaluation_result,
)
from strange_physics.laws import SpringParameters
from strange_physics.research_contracts import (
    EvaluationReport,
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    message_sha256,
    validate_prediction_response,
)
from strange_physics.worlds import WorldDefinition


def _supported_structure(structure: Structure) -> bool:
    return (
        len(structure.particle_ids) == 1
        and len(structure.anchors) == 1
        and len(structure.connections) == 1
        and {structure.connections[0].a, structure.connections[0].b}
        == {structure.particle_ids[0], structure.anchors[0].id}
        and math.hypot(*structure.anchors[0].position) <= 0.5
    )


def _supported_request(request: PredictionRequest) -> bool:
    if not _supported_structure(request.structure):
        return False
    particle = request.experiment.particles[0]
    impulse = request.experiment.impulse
    return (
        0.5 <= particle.mass <= 2.0
        and math.hypot(*particle.position) <= 3.0
        and math.hypot(*particle.velocity) <= 2.0
        and (impulse is None or math.hypot(*impulse.vector) <= 1.0)
        and request.times[-1] <= 2.0
    )


def _protocol_failure(
    model_sha256: str,
    protocol: SpringEvaluationProtocol,
    submissions: tuple[ProbePrediction, ...],
) -> EvaluationReason | None:
    if protocol.model_sha256 != model_sha256:
        return "model_digest_mismatch"
    if len({probe.probe_id for probe in protocol.probes}) != len(protocol.probes):
        return "duplicate_probe"
    square = protocol.normalization_scale * protocol.normalization_scale
    if not math.isfinite(square) or square == 0:
        return "invalid_normalization_scale"
    for probe in protocol.probes:
        if probe.request_sha256 != message_sha256(probe.request):
            return "request_digest_mismatch"
        if probe.request.model_sha256 != model_sha256:
            return "request_model_mismatch"
        if not _supported_request(probe.request):
            return "unsupported_probe"
    if len(submissions) > 24:
        return "submission_limit"
    seen: set[str] = set()
    probes = {probe.probe_id: probe for probe in protocol.probes}
    for entry in submissions:
        if entry.probe_id in seen:
            return "duplicate_submission"
        seen.add(entry.probe_id)
        if entry.probe_id not in probes:
            return "foreign_submission"
        if entry.request_sha256 != probes[entry.probe_id].request_sha256:
            return "submission_request_mismatch"
    return None


def _prediction_status(
    request: PredictionRequest, entry: ProbePrediction | None
) -> PredictionAssessment:
    if entry is None:
        return "missing"
    if entry.status != "response":
        return entry.status
    assert entry.response is not None
    try:
        validate_prediction_response(request, entry.response)
    except ValueError:
        return "invalid"
    return "valid"


def _world_coefficient(world: WorldDefinition) -> float | None:
    if (
        world.changed_law is not None
        or world.change_after is not None
        or world.initial_law.kind != "spring"
        or not _supported_structure(world.space.structure)
        or world.space.sampling.position_noise != 0
        or world.space.sampling.velocity_noise != 0
    ):
        return None
    try:
        parameters = SpringParameters.model_validate(world.initial_law.parameters)
    except ValidationError:
        return None
    return parameters.linear if parameters.cubic == 0 else None


def _reference_position(coefficient: float, request: PredictionRequest, time: float) -> Vector:
    """Decimal recurrence with a preregistered absolute omitted-tail criterion."""
    particle = request.experiment.particles[0]
    if time == 0:
        return particle.position
    with localcontext() as context:
        context.prec = 80
        context.rounding = ROUND_HALF_EVEN
        d = Decimal.from_float
        mass, t = d(particle.mass), d(time)
        anchor = tuple(d(value) for value in request.structure.anchors[0].position)
        displacement = tuple(
            d(value) - origin for value, origin in zip(particle.position, anchor, strict=True)
        )
        velocity = tuple(d(value) for value in particle.velocity)
        if request.experiment.impulse is not None:
            velocity = tuple(
                value + d(impulse) / mass
                for value, impulse in zip(velocity, request.experiment.impulse.vector, strict=True)
            )
        velocity_time = tuple(value * t for value in velocity)
        u = (d(coefficient) / mass) * t * t
        if not u.is_finite() or not Decimal(0) <= u <= Decimal(32):
            raise ArithmeticError("Reference phase outside reviewed domain")
        cosine_term = sinc_term = Decimal(1)
        cosine = sinc = Decimal(1)
        for index in range(128):
            cosine_denominator = Decimal((2 * index + 1) * (2 * index + 2))
            sinc_denominator = Decimal((2 * index + 2) * (2 * index + 3))
            next_cosine = -cosine_term * u / cosine_denominator
            next_sinc = -sinc_term * u / sinc_denominator
            decreasing = u <= cosine_denominator and u <= sinc_denominator
            tails = tuple(
                abs(r) * abs(next_cosine) + abs(vt) * abs(next_sinc)
                for r, vt in zip(displacement, velocity_time, strict=True)
            )
            if decreasing and all(tail <= Decimal("1e-60") for tail in tails):
                position = tuple(
                    origin + r * cosine + vt * sinc
                    for origin, r, vt in zip(anchor, displacement, velocity_time, strict=True)
                )
                if not all(value.is_finite() for value in position):
                    raise ArithmeticError("Nonfinite reference position")
                converted = (float(position[0]), float(position[1]))
                if not all(math.isfinite(value) for value in converted):
                    raise ArithmeticError("Unrepresentable reference position")
                return converted
            cosine_term, sinc_term = next_cosine, next_sinc
            cosine += cosine_term
            sinc += sinc_term
    raise ArithmeticError("Reference series did not meet its fixed tail bound")


def _reference_probe(
    coefficient: float, probe_id: str, request: PredictionRequest
) -> ReferenceProbe:
    return ReferenceProbe(
        probe_id=probe_id,
        request_sha256=message_sha256(request),
        times=request.times,
        positions=tuple(_reference_position(coefficient, request, time) for time in request.times),
    )


def _mean(values: tuple[float, ...]) -> float:
    total = math.fsum(values)
    mean = total / len(values)
    if not math.isfinite(mean) or (any(value > 0 for value in values) and mean == 0):
        raise ArithmeticError("Unrepresentable mean")
    return mean


def _probe_mse(response: PredictionResponse, reference: ReferenceProbe) -> float:
    errors: list[float] = []
    for frame, label in zip(response.trajectory.frames, reference.positions, strict=True):
        for prediction, actual in zip(frame.positions[0], label, strict=True):
            difference = prediction - actual
            squared = difference * difference
            if (
                not math.isfinite(difference)
                or not math.isfinite(squared)
                or (difference != 0 and squared == 0)
            ):
                raise ArithmeticError("Unrepresentable squared error")
            errors.append(squared)
    return _mean(tuple(errors))


def evaluate_spring_predictions(
    model: LinearSpringModel,
    protocol: SpringEvaluationProtocol,
    submissions: tuple[ProbePrediction, ...],
    world: WorldDefinition,
) -> SpringEvaluationResult:
    """Score a frozen development protocol; returned references/results are private.

    Syntactically invalid or over-48-entry transport artifacts fail their typed
    boundary. Semantic association failures return explicit protocol outcomes.
    Actual journal provenance/disjointness is the trusted SDK adapter's obligation.
    """
    start = perf_counter_ns()
    retained_submissions = SpringPredictionSubmissions(entries=submissions)
    model_hash, protocol_hash = message_sha256(model), message_sha256(protocol)
    submission_hash = message_sha256(retained_submissions)
    assessments = [
        ProbeAssessment(
            probe_index=index,
            probe_id=probe.probe_id,
            request_sha256=message_sha256(probe.request),
            prediction_status="not_assessed",
            position_mse=None,
        )
        for index, probe in enumerate(protocol.probes)
    ]
    reference: SpringReferenceArtifact | None = None
    completed_references = 0
    failed_reference_index = None

    def finish(
        status: EvaluationStatus,
        reason: EvaluationReason | None,
        metrics: tuple[float, float] | None = None,
    ) -> SpringEvaluationResult:
        elapsed = (perf_counter_ns() - start) // 1_000_000
        valid = sum(item.prediction_status == "valid" for item in assessments)
        unassessed = sum(item.prediction_status == "not_assessed" for item in assessments)
        failed = len(assessments) - valid - unassessed
        computed = sum(item.position_mse is not None for item in assessments)
        diagnostics = SpringEvaluationDiagnostics(
            actual_model_sha256=model_hash,
            protocol_sha256=protocol_hash,
            submissions_sha256=submission_hash,
            requested_probe_count=len(assessments),
            submitted_entry_count=len(submissions),
            valid_prediction_count=valid,
            failed_prediction_count=failed,
            prediction_not_assessed_count=unassessed,
            computed_metric_count=computed,
            metric_not_assessed_count=len(assessments) - computed,
            reference_completed_probe_count=completed_references,
            reference_failed_probe_index=failed_reference_index,
            evaluation_runtime_ms=elapsed,
        )
        report = (
            EvaluationReport(
                status="scored" if status == "scored" else "unscorable",
                model_sha256=model_hash,
                protocol_sha256=protocol_hash,
                probe_count=len(assessments),
                valid_prediction_count=valid,
                failed_prediction_count=failed,
                position_mse=None if metrics is None else metrics[0],
                normalized_position_mse=None if metrics is None else metrics[1],
                normalization_scale=protocol.normalization_scale,
                evaluation_runtime_ms=elapsed,
            )
            if status in {"scored", "unscorable"}
            else None
        )
        result = SpringEvaluationResult(
            status=status,
            reason=reason,
            report=report,
            report_sha256=None if report is None else message_sha256(report),
            diagnostics=diagnostics,
            probes=tuple(assessments),
            reference=reference,
            reference_sha256=None if reference is None else message_sha256(reference),
        )
        validate_spring_evaluation_result(result, model, protocol, submissions, world)
        return result

    failure = _protocol_failure(model_hash, protocol, submissions)
    if failure is not None:
        return finish("protocol_failure", failure)
    by_id = {entry.probe_id: entry for entry in submissions}
    assessments = [
        ProbeAssessment(
            probe_index=index,
            probe_id=probe.probe_id,
            request_sha256=probe.request_sha256,
            prediction_status=_prediction_status(probe.request, by_id.get(probe.probe_id)),
            position_mse=None,
        )
        for index, probe in enumerate(protocol.probes)
    ]
    if any(item.prediction_status != "valid" for item in assessments):
        return finish("unscorable", "prediction_failure")
    coefficient = _world_coefficient(world)
    if coefficient is None:
        return finish("evaluator_failure", "unsupported_world")
    labels: list[ReferenceProbe] = []
    for index, probe in enumerate(protocol.probes):
        try:
            labels.append(_reference_probe(coefficient, probe.probe_id, probe.request))
        except (ArithmeticError, ValueError):
            failed_reference_index = index
            return finish("evaluator_failure", "reference_failure")
        completed_references += 1
    reference = SpringReferenceArtifact(
        source_world_sha256=message_sha256(world),
        protocol_sha256=protocol_hash,
        probes=tuple(labels),
    )
    for index, (probe, label) in enumerate(zip(protocol.probes, labels, strict=True)):
        response = by_id[probe.probe_id].response
        assert response is not None
        try:
            error = _probe_mse(response, label)
        except (ArithmeticError, ValueError):
            return finish("arithmetic_failure", "metric_failure")
        assessments[index] = ProbeAssessment(
            probe_index=index,
            probe_id=probe.probe_id,
            request_sha256=probe.request_sha256,
            prediction_status="valid",
            position_mse=error,
        )
    try:
        mean = _mean(
            tuple(item.position_mse for item in assessments if item.position_mse is not None)
        )
    except ArithmeticError:
        return finish("arithmetic_failure", "metric_failure")
    normalized = mean / (protocol.normalization_scale * protocol.normalization_scale)
    if not math.isfinite(normalized) or (mean > 0 and normalized == 0):
        return finish("arithmetic_failure", "normalization_failure")
    return finish("scored", None, (mean, normalized))
