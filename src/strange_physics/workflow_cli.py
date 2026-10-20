"""Small CLI adapters over the shared local scientific workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import monotonic_ns

from pydantic import ValidationError

from strange_physics.contracts import Message, ObservationBundle
from strange_physics.evaluation_contracts import SpringEvaluationProtocol
from strange_physics.research_contracts import LinearSpringModel, message_sha256
from strange_physics.scientific_workflow import (
    elapsed_ms,
    fit_spring,
    predict_spring,
    prepare_spring_evaluation,
    score_spring,
)
from strange_physics.workflow_contracts import (
    SpringFitArtifact,
    SpringPredictionArtifact,
    SpringPreparationArtifact,
    Stage,
    StageCompletion,
    WorkflowFailure,
)
from strange_physics.workflow_io import (
    WorkflowError,
    read_message,
    read_stage,
    stage_message,
    write_stage,
)

COMMANDS = ("fit-spring", "prepare-spring-evaluation", "predict-spring", "score-spring")


def add_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    fit = commands.add_parser("fit-spring", help="fit the purchased public spring observations")
    fit.add_argument("--observations", type=Path, required=True)
    prepare = commands.add_parser(
        "prepare-spring-evaluation", help="freeze 24 disjoint public probes from a private journal"
    )
    prepare.add_argument("--journal", type=Path, required=True)
    prepare.add_argument("--fit", type=Path, required=True)
    predict = commands.add_parser("predict-spring", help="predict all public manifest probes")
    predict.add_argument("--model", type=Path, required=True)
    predict.add_argument("--manifest", type=Path, required=True)
    score = commands.add_parser(
        "score-spring", help="independently score the frozen local workflow"
    )
    score.add_argument("--journal", type=Path, required=True)
    score.add_argument("--fit", type=Path, required=True)
    score.add_argument("--evaluation", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    for command in (fit, prepare, predict, score):
        command.add_argument("--output", type=Path, required=True)


def _stage_files(artifact: Message) -> tuple[Stage, dict[str, Message], tuple[str, ...]]:
    if isinstance(artifact, SpringFitArtifact):
        files: dict[str, Message] = {"fit.json": artifact, "config.json": artifact.config}
        if artifact.fit_input is not None:
            files["input.json"] = artifact.fit_input
        if artifact.model is not None:
            files["model.json"] = artifact.model
        return (
            "fit",
            files,
            (message_sha256(artifact.observations), message_sha256(artifact.config)),
        )
    if isinstance(artifact, SpringPreparationArtifact):
        files = {"preparation.json": artifact}
        if artifact.protocol is not None:
            files["protocol.json"] = artifact.protocol
        return "prepare", files, (artifact.fit_artifact_sha256, artifact.observation_sha256)
    if isinstance(artifact, SpringPredictionArtifact):
        return (
            "predict",
            {
                "predictions.json": artifact,
                "config.json": artifact.config,
                "submissions.json": artifact.submissions,
            },
            (
                message_sha256(artifact.model),
                message_sha256(artifact.protocol),
                message_sha256(artifact.config),
            ),
        )
    raise WorkflowError("invalid_input")


def _load[T: Message](path: Path, stage: Stage, name: str, model: type[T]) -> T:
    files = read_stage(path, stage)
    value = stage_message(files, name, model)
    actual_stage, projections, input_hashes = _stage_files(value)
    completion = read_message(path / "completion.json", StageCompletion, limit=16 * 1024)
    if (
        actual_stage != stage
        or set(files) != set(projections)
        or (completion.input_message_sha256 != input_hashes)
    ):
        raise WorkflowError("artifact_mismatch")
    if isinstance(value, (SpringFitArtifact, SpringPreparationArtifact, SpringPredictionArtifact)):
        if completion.elapsed_ms != value.elapsed_ms:
            raise WorkflowError("artifact_mismatch")
    for filename, expected in projections.items():
        parsed = stage_message(files, filename, type(expected))
        if parsed != expected:
            raise WorkflowError("artifact_mismatch")
    return value


def _persist(
    path: Path, artifact: SpringFitArtifact | SpringPreparationArtifact | SpringPredictionArtifact
) -> None:
    stage, files, hashes = _stage_files(artifact)
    write_stage(path, stage, files, hashes, artifact.elapsed_ms)


def run_workflow(args: argparse.Namespace) -> int:
    start = monotonic_ns()
    stages: dict[str, Stage] = {
        "fit-spring": "fit",
        "prepare-spring-evaluation": "prepare",
        "predict-spring": "predict",
        "score-spring": "score",
    }
    stage = stages[args.command]
    try:
        if stage == "fit":
            fit = fit_spring(read_message(args.observations, ObservationBundle))
            _persist(args.output, fit)
            status = fit.input_rejection or (fit.result.status if fit.result else "input_rejected")
            success = fit.model is not None
            summary: dict[str, object] = {"stage": stage, "status": status}
        elif stage == "prepare":
            fit = _load(args.fit, "fit", "fit.json", SpringFitArtifact)
            preparation = prepare_spring_evaluation(args.journal, fit)
            _persist(args.output, preparation)
            success = preparation.status == "prepared"
            summary = {
                "stage": stage,
                "status": preparation.status,
                "probe_count": 24 if success else 0,
            }
        elif stage == "predict":
            predictions = predict_spring(
                read_message(args.model, LinearSpringModel),
                read_message(args.manifest, SpringEvaluationProtocol),
            )
            _persist(args.output, predictions)
            failed = sum(r.response is None for r in predictions.results)
            success = failed == 0
            summary = {
                "stage": stage,
                "status": "predicted" if success else "prediction_failed",
                "probe_count": len(predictions.results),
                "failed": failed,
            }
        else:
            fit = _load(args.fit, "fit", "fit.json", SpringFitArtifact)
            preparation = _load(
                args.evaluation, "prepare", "preparation.json", SpringPreparationArtifact
            )
            predictions = _load(
                args.predictions, "predict", "predictions.json", SpringPredictionArtifact
            )
            score = score_spring(args.journal, fit, preparation, predictions)
            outputs: dict[str, Message] = {"score.json": score}
            if score.result.report is not None:
                outputs["report.json"] = score.result.report
            write_stage(
                args.output,
                stage,
                outputs,
                (message_sha256(fit), message_sha256(preparation), message_sha256(predictions)),
                score.elapsed_ms,
            )
            success = score.result.status == "scored"
            summary = {
                "stage": stage,
                "status": score.result.status,
                "probe_count": len(score.probes),
                "target_passed": score.target_passed,
                "maximum_position_rmse": score.maximum_position_rmse,
            }
        print(json.dumps(summary, sort_keys=True))
        return 0 if success else 1
    except (WorkflowError, ValidationError, OSError) as error:
        code = (
            error.code
            if isinstance(error, WorkflowError)
            else ("invalid_input" if isinstance(error, ValidationError) else "io_failure")
        )
        failure = WorkflowFailure(stage=stage, code=code, elapsed_ms=elapsed_ms(start))
        retained = False
        try:
            write_stage(args.output, stage, {"failure.json": failure}, (), failure.elapsed_ms)
            retained = True
        except (WorkflowError, ValidationError, OSError):
            # An unsafe/existing/unwritable destination must not be overwritten for diagnostics.
            pass
        print(
            json.dumps(
                {"stage": stage, "error": code, "failure_artifact_retained": retained},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
