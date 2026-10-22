"""Pure native preparation/scoring; no Journal, ledger, selector or network access."""

from __future__ import annotations

from pydantic import TypeAdapter

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Identifier
from strange_physics.evaluation import evaluate_spring_predictions
from strange_physics.evaluation_contracts import (
    ProbePrediction,
    SpringPredictionSubmissions,
    validate_spring_evaluation_result,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    validate_native_prediction_result,
)
from strange_physics.native_scoring_contracts import (
    MAX_SCORING_INPUT_BYTES,
    MAX_SCORING_RESULT_BYTES,
    NATIVE_SCORER,
    NativeEvaluationInput,
    NativePreparationOutcome,
    NativePreparationResult,
    NativeScoreOutcome,
    NativeScoreResult,
    NativeScoringInput,
    PreparationReason,
    ScoringReason,
)
from strange_physics.native_spring_contracts import (
    NativeWorkFacts,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.scientific_workflow import condition_keys, i1_protocol
from strange_physics.workflow_io import WorkflowError


def _preparation(actual: NativeEvaluationInput) -> NativePreparationOutcome:
    candidate = actual.candidates
    reason: PreparationReason | None = None
    protocol = None
    probe_index = record_index = None
    selected = actual.selected
    try:
        validate_native_candidate_result(
            actual.candidate_result, candidate, attempt_id=actual.candidate_attempt_id
        )
    except ValueError:
        reason = "candidate_mismatch"
    if reason is None:
        if actual.candidate_result.payload.status != "produced":
            reason = "candidate_unavailable"
        elif selected is None:
            reason = "selection_unavailable"
        else:
            try:
                validate_selected_native_candidate(
                    selected,
                    actual.candidate_result,
                    candidate,
                    attempt_id=actual.candidate_attempt_id,
                )
            except ValueError:
                reason = "selection_mismatch"
    if reason is None:
        assert selected is not None
        try:
            protocol = i1_protocol(selected.model, candidate.observations.space.structure)
            purchased = tuple(
                condition_keys(candidate.observations.space.structure, record.experiment)
                for record in candidate.observations.records
            )
            for index, probe in enumerate(protocol.probes):
                action, post = condition_keys(probe.request.structure, probe.request.experiment)
                for record, (bought_action, bought_post) in enumerate(purchased):
                    if action == bought_action or post == bought_post:
                        reason, probe_index, record_index = "purchased_overlap", index, record
                        break
                if reason is not None:
                    break
        except WorkflowError:
            reason = "unsupported_topology"
    return NativePreparationOutcome(
        status="prepared" if reason is None else "rejected",
        reason=reason,
        input_sha256=bounded_canonical(actual, MAX_SCORING_INPUT_BYTES)[0],
        policy_sha256=message_sha256(actual.policy),
        observation_sha256=message_sha256(candidate.observations),
        model_sha256=None if selected is None else message_sha256(selected.model),
        protocol=protocol if reason is None else None,
        protocol_sha256=message_sha256(protocol)
        if reason is None and protocol is not None
        else None,
        overlap_probe_index=probe_index,
        overlap_record_index=record_index,
    )


def prepare_native_evaluation(
    actual: NativeEvaluationInput, *, attempt_id: str
) -> NativePreparationResult:
    """Bind supplied purchased material and fixed disjoint probes; no Journal readiness claim."""
    TypeAdapter(Identifier).validate_python(attempt_id)
    payload = _preparation(actual)
    completed = int(payload.status == "prepared")
    return NativePreparationResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="preparation",
            producer_version=NATIVE_SCORER,
            config_sha256=payload.policy_sha256,
            input_sha256=payload.input_sha256,
            observation_sha256=payload.observation_sha256,
            model_sha256=payload.model_sha256,
            output_sha256=bounded_canonical(payload, MAX_SCORING_RESULT_BYTES)[0],
            unit="preparation",
            requested_count=1,
            completed_count=completed,
            failed_count=0,
            not_assessed_count=1 - completed,
            outcome="completed" if completed else "rejected",
        ),
    )


def validate_native_preparation_result(
    result: NativePreparationResult, actual: NativeEvaluationInput, *, attempt_id: str
) -> None:
    """Recompute all public material/protocol joins, not actual Journal authenticity."""
    expected = prepare_native_evaluation(actual, attempt_id=attempt_id)
    if (
        bounded_canonical(result, MAX_SCORING_RESULT_BYTES)[0]
        != bounded_canonical(expected, MAX_SCORING_RESULT_BYTES)[0]
    ):
        raise ValueError("Preparation differs from the actual material and fixed I1 protocol")


def _submissions(
    actual: NativeScoringInput, *, attempt_id: str
) -> tuple[ScoringReason | None, SpringPredictionSubmissions | None]:
    context, preparation = actual.context, actual.preparation
    try:
        validate_native_preparation_result(
            preparation, context, attempt_id=preparation.facts.attempt_id
        )
    except ValueError:
        return "preparation_mismatch", None
    if preparation.payload.status != "prepared":
        return "preparation_rejected", None
    protocol, selected = preparation.payload.protocol, context.selected
    assert protocol is not None and selected is not None
    ids = [entry.attempt_id for entry in actual.predictions.entries]
    if len(set(ids)) != 24 or attempt_id in ids:
        return "attempt_reuse", None
    if message_sha256(actual.world.space) != message_sha256(context.candidates.observations.space):
        return "world_space_mismatch", None
    submissions: list[ProbePrediction] = []
    for entry, probe in zip(actual.predictions.entries, protocol.probes, strict=True):
        if entry.probe_id != probe.probe_id or entry.request_sha256 != message_sha256(
            probe.request
        ):
            return "prediction_mismatch", None
        if entry.status == "missing":
            continue
        if entry.status == "invalid":
            submissions.append(
                ProbePrediction(
                    probe_id=probe.probe_id,
                    request_sha256=probe.request_sha256,
                    status="invalid",
                    response=None,
                )
            )
            continue
        assert entry.result is not None
        predicted = NativePredictionInput(
            model=selected.model,
            candidate_config=context.candidates.config,
            request=probe.request,
            config=context.prediction_config,
        )
        try:
            validate_native_prediction_result(entry.result, predicted, attempt_id=entry.attempt_id)
        except ValueError:
            return "prediction_mismatch", None
        response = entry.result.payload.response
        submissions.append(
            ProbePrediction(
                probe_id=probe.probe_id,
                request_sha256=probe.request_sha256,
                status="response" if response is not None else "failed",
                response=response,
            )
        )
    return None, SpringPredictionSubmissions(entries=tuple(submissions))


def score_native_predictions(actual: NativeScoringInput, *, attempt_id: str) -> NativeScoreResult:
    """Execute the unchanged independent evaluator after actual public-input binding.

    The caller supplies a private actual world; only the later Journal/catalog
    publisher can establish its authenticity. This function never selects a model,
    redraws probes, applies an accuracy cutoff, settles a ledger or exports labels.
    """
    TypeAdapter(Identifier).validate_python(attempt_id)
    reason, submissions = _submissions(actual, attempt_id=attempt_id)
    context = actual.context
    selected, protocol = context.selected, actual.preparation.payload.protocol
    evaluation = None
    if reason is None:
        assert selected is not None and protocol is not None and submissions is not None
        evaluation = evaluate_spring_predictions(
            selected.model, protocol, submissions.entries, actual.world
        )
    payload = NativeScoreOutcome(
        status="evaluated" if reason is None else "rejected",
        reason=reason,
        input_sha256=bounded_canonical(actual, MAX_SCORING_INPUT_BYTES)[0],
        policy_sha256=message_sha256(context.policy),
        observation_sha256=message_sha256(context.candidates.observations),
        model_sha256=None if selected is None else message_sha256(selected.model),
        preparation_sha256=message_sha256(actual.preparation),
        predictions_sha256=message_sha256(actual.predictions),
        submissions=submissions,
        evaluation=evaluation,
    )
    completed = int(evaluation is not None and evaluation.status in {"scored", "unscorable"})
    failed = int(evaluation is not None and not completed)
    result = NativeScoreResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="scoring",
            producer_version=NATIVE_SCORER,
            config_sha256=payload.policy_sha256,
            input_sha256=payload.input_sha256,
            observation_sha256=payload.observation_sha256,
            model_sha256=payload.model_sha256,
            output_sha256=bounded_canonical(payload, MAX_SCORING_RESULT_BYTES)[0],
            unit="work",
            requested_count=1,
            completed_count=completed,
            failed_count=failed,
            not_assessed_count=1 - completed - failed,
            outcome="completed" if completed else "failed" if failed else "rejected",
        ),
    )
    validate_native_score_result(result, actual, attempt_id=attempt_id)
    return result


def validate_native_score_result(
    result: NativeScoreResult, actual: NativeScoringInput, *, attempt_id: str
) -> None:
    """Bind private actual material and retained shapes, not numerical authenticity."""
    reason, submissions = _submissions(actual, attempt_id=attempt_id)
    p, f = result.payload, result.facts
    context, selected = actual.context, actual.context.selected
    if (
        f.attempt_id != attempt_id
        or p.reason != reason
        or p.status != ("evaluated" if reason is None else "rejected")
        or p.input_sha256 != bounded_canonical(actual, MAX_SCORING_INPUT_BYTES)[0]
        or p.policy_sha256 != message_sha256(context.policy)
        or p.observation_sha256 != message_sha256(context.candidates.observations)
        or p.model_sha256 != (None if selected is None else message_sha256(selected.model))
        or p.preparation_sha256 != message_sha256(actual.preparation)
        or p.predictions_sha256 != message_sha256(actual.predictions)
        or (p.submissions is None) != (submissions is None)
        or (
            submissions is not None
            and p.submissions is not None
            and message_sha256(submissions) != message_sha256(p.submissions)
        )
    ):
        raise ValueError("Score differs from actual private inputs or derived submissions")
    if reason is None:
        protocol = actual.preparation.payload.protocol
        assert p.evaluation is not None and selected is not None and protocol is not None
        assert submissions is not None
        validate_spring_evaluation_result(
            p.evaluation, selected.model, protocol, submissions.entries, actual.world
        )
