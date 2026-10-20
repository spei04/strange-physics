"""Local SDK adapters for the bounded purchased-fit-predict-score vertical slice."""

from __future__ import annotations

import math
from pathlib import Path
from time import monotonic_ns
from typing import TypedDict

from strange_physics.contracts import (
    Anchor,
    Experiment,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Structure,
    Vector,
)
from strange_physics.evaluation import evaluate_spring_predictions
from strange_physics.evaluation_contracts import (
    ProbePrediction,
    SpringEvaluationProbe,
    SpringEvaluationProtocol,
    SpringPredictionSubmissions,
    validate_spring_evaluation_result,
)
from strange_physics.fitting import fit_linear_spring
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    SpringFitInput,
    message_sha256,
)
from strange_physics.workflow_contracts import (
    ProbeRMSE,
    SpringFitArtifact,
    SpringPredictionArtifact,
    SpringPreparationArtifact,
    SpringScoreArtifact,
)
from strange_physics.workflow_io import WorkflowError
from strange_physics.workflow_journal import JournalSnapshot, read_journal

_FIT_CONFIG = SpringFitConfig()
_PREDICTION_CONFIG = SpringPredictionConfig()


class _PreparationProvenance(TypedDict):
    fit_artifact_sha256: str
    observation_sha256: str
    journal_bytes_sha256: str
    source_world_sha256: str
    engine_fingerprint: str
    elapsed_ms: int


def elapsed_ms(start: int) -> int:
    return max(0, (monotonic_ns() - start) // 1_000_000)


def fit_spring(
    observations: ObservationBundle, config: SpringFitConfig = _FIT_CONFIG
) -> SpringFitArtifact:
    """Fit only purchased public data; retain rejected inputs and every failed record."""
    start = monotonic_ns()
    if not any(r.status == "completed" for r in observations.records):
        return SpringFitArtifact(
            observations=observations,
            config=config,
            fit_input=None,
            result=None,
            input_rejection="no_completed_records",
            elapsed_ms=elapsed_ms(start),
        )
    fit_input = SpringFitInput(
        observations=observations,
        through_index=len(observations.records) - 1,
        fit_config_sha256=message_sha256(config),
    )
    result = fit_linear_spring(fit_input, config)
    return SpringFitArtifact(
        observations=observations,
        config=config,
        fit_input=fit_input,
        result=result,
        input_rejection=None,
        elapsed_ms=elapsed_ms(start),
    )


def _single_spring(structure: Structure) -> bool:
    return (
        len(structure.particle_ids) == 1
        and len(structure.anchors) == 1
        and len(structure.connections) == 1
        and {structure.connections[0].a, structure.connections[0].b}
        == {structure.particle_ids[0], structure.anchors[0].id}
    )


def i1_protocol(model: LinearSpringModel, structure: Structure) -> SpringEvaluationProtocol:
    """Construct the predeclared public policy; never consult truth or predicted outcomes."""
    if not _single_spring(structure):
        raise WorkflowError("invalid_input")
    u = 1 / math.sqrt(2)
    cases: tuple[tuple[Vector, Vector, Vector, Vector | None], ...] = (
        ((-0.5, 0.0), (3.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
        ((-0.5, 0.0), (3.0, 0.0), (-2.0, 0.0), (-1.0, 0.0)),
        ((0.0, -0.5), (0.0, 3.0), (0.0, 2.0), (0.0, 1.0)),
        ((0.0, -0.5), (0.0, 3.0), (0.0, -2.0), (0.0, -1.0)),
        ((-0.5 * u, -0.5 * u), (3 * u, 3 * u), (2 * u, -2 * u), (u, -u)),
        ((0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
        ((0.0, 0.0), (1.5, 0.2), (0.3, -0.6), (0.2, 0.1)),
        ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), None),
    )
    probes: list[SpringEvaluationProbe] = []
    pid = structure.particle_ids[0]
    model_hash = message_sha256(model)
    for mass in (0.5, 1.0, 2.0):
        for anchor, position, velocity, impulse in cases:
            geometry = Structure(
                particle_ids=structure.particle_ids,
                anchors=(Anchor(id=structure.anchors[0].id, position=anchor),),
                connections=structure.connections,
            )
            experiment = Experiment(
                particles=(
                    ParticleInitial(id=pid, mass=mass, position=position, velocity=velocity),
                ),
                impulse=None if impulse is None else Impulse(particle_id=pid, vector=impulse),
            )
            request = PredictionRequest(
                model_sha256=model_hash,
                structure=geometry,
                experiment=experiment,
                times=tuple(i * 0.05 for i in range(41)),
                integration_dt=0.01,
            )
            probes.append(
                SpringEvaluationProbe(
                    probe_id=f"i1-probe-{len(probes):02d}",
                    request_sha256=message_sha256(request),
                    request=request,
                )
            )
    return SpringEvaluationProtocol(
        model_sha256=model_hash, probes=tuple(probes), normalization_scale=1.0
    )


def condition_keys(
    structure: Structure, experiment: Experiment
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Exact specified equivalences, not a numerical tolerance or all physical symmetries."""
    if not _single_spring(structure) or len(experiment.particles) != 1:
        raise WorkflowError("invalid_input")
    particle = experiment.particles[0]
    anchor = structure.anchors[0].position
    relative = (particle.position[0] - anchor[0], particle.position[1] - anchor[1])
    impulse = (0.0, 0.0) if experiment.impulse is None else experiment.impulse.vector
    post = (
        particle.velocity[0] + impulse[0] / particle.mass,
        particle.velocity[1] + impulse[1] / particle.mass,
    )
    return (
        (particle.mass, *relative, *particle.velocity, *impulse),
        (particle.mass, *relative, *post),
    )


def _prepare(
    snapshot: JournalSnapshot, fit: SpringFitArtifact, duration: int
) -> SpringPreparationArtifact:
    if snapshot.observations != fit.observations:
        raise WorkflowError("journal_mismatch")
    common = _PreparationProvenance(
        fit_artifact_sha256=message_sha256(fit),
        observation_sha256=message_sha256(fit.observations),
        journal_bytes_sha256=snapshot.journal_bytes_sha256,
        source_world_sha256=message_sha256(snapshot.world),
        engine_fingerprint=fit.observations.engine_fingerprint,
        elapsed_ms=duration,
    )
    if fit.model is None:
        return SpringPreparationArtifact(
            **common,
            status="fit_failed",
            protocol=None,
            overlap_probe_index=None,
            overlap_record_index=None,
        )
    if not _single_spring(fit.observations.space.structure):
        return SpringPreparationArtifact(
            **common,
            status="unsupported_topology",
            protocol=None,
            overlap_probe_index=None,
            overlap_record_index=None,
        )
    protocol = i1_protocol(fit.model, fit.observations.space.structure)
    purchased = tuple(
        condition_keys(fit.observations.space.structure, r.experiment)
        for r in fit.observations.records
    )
    for pi, probe in enumerate(protocol.probes):
        action, post = condition_keys(probe.request.structure, probe.request.experiment)
        for ri, (bought_action, bought_post) in enumerate(purchased):
            if action == bought_action or post == bought_post:
                return SpringPreparationArtifact(
                    **common,
                    status="purchased_overlap",
                    protocol=None,
                    overlap_probe_index=pi,
                    overlap_record_index=ri,
                )
    return SpringPreparationArtifact(
        **common,
        status="prepared",
        protocol=protocol,
        overlap_probe_index=None,
        overlap_record_index=None,
    )


def prepare_spring_evaluation(
    journal_path: Path, fit: SpringFitArtifact
) -> SpringPreparationArtifact:
    start = monotonic_ns()
    snapshot = read_journal(journal_path)
    prepared = _prepare(snapshot, fit, 0)
    return SpringPreparationArtifact.model_validate(
        prepared.model_dump() | {"elapsed_ms": elapsed_ms(start)}
    )


def predict_spring(
    model: LinearSpringModel,
    protocol: SpringEvaluationProtocol,
    config: SpringPredictionConfig = _PREDICTION_CONFIG,
) -> SpringPredictionArtifact:
    """Public inputs only. Retain a typed result for every ordered manifest probe."""
    start = monotonic_ns()
    if len({p.probe_id for p in protocol.probes}) != len(protocol.probes) or any(
        p.request_sha256 != message_sha256(p.request)
        or p.request.model_sha256 != protocol.model_sha256
        for p in protocol.probes
    ):
        raise WorkflowError("artifact_mismatch")
    results = tuple(predict_linear_spring(model, p.request, config) for p in protocol.probes)
    submissions = SpringPredictionSubmissions(
        entries=tuple(
            ProbePrediction(
                probe_id=p.probe_id,
                request_sha256=p.request_sha256,
                status="response" if r.response is not None else "failed",
                response=r.response,
            )
            for p, r in zip(protocol.probes, results, strict=True)
        )
    )
    return SpringPredictionArtifact(
        model=model,
        protocol=protocol,
        config=config,
        results=results,
        submissions=submissions,
        elapsed_ms=elapsed_ms(start),
    )


def score_spring(
    journal_path: Path,
    fit: SpringFitArtifact,
    preparation: SpringPreparationArtifact,
    predictions: SpringPredictionArtifact,
) -> SpringScoreArtifact:
    """Private evaluator boundary: verify frozen provenance before generating any labels."""
    start = monotonic_ns()
    snapshot = read_journal(journal_path)
    expected = _prepare(snapshot, fit, preparation.elapsed_ms)
    if expected != preparation or preparation.protocol is None or fit.model is None:
        raise WorkflowError("artifact_mismatch")
    if predictions.protocol != preparation.protocol or predictions.model != fit.model:
        raise WorkflowError("artifact_mismatch")
    result = evaluate_spring_predictions(
        fit.model, preparation.protocol, predictions.submissions.entries, snapshot.world
    )
    validate_spring_evaluation_result(
        result, fit.model, preparation.protocol, predictions.submissions.entries, snapshot.world
    )
    probes = tuple(
        ProbeRMSE(
            probe_id=p.probe_id,
            position_mse=p.position_mse,
            position_rmse=None if p.position_mse is None else math.sqrt(p.position_mse),
        )
        for p in result.probes
    )
    complete = result.status == "scored" and all(p.position_rmse is not None for p in probes)
    maximum = (
        max(p.position_rmse for p in probes if p.position_rmse is not None) if complete else None
    )
    return SpringScoreArtifact(
        fit_artifact_sha256=message_sha256(fit),
        preparation_sha256=message_sha256(preparation),
        prediction_artifact_sha256=message_sha256(predictions),
        result=result,
        probes=probes,
        maximum_position_rmse=maximum,
        target_passed=maximum is not None and maximum <= 0.001,
        elapsed_ms=elapsed_ms(start),
    )
