"""Real classical fit/predict/evaluate composition, never primary selection or Journal I/O."""

from __future__ import annotations

import hashlib

from pydantic import TypeAdapter

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Identifier
from strange_physics.evaluation import evaluate_spring_predictions
from strange_physics.evaluation_contracts import (
    ProbePrediction,
    SpringEvaluationProtocol,
    SpringPredictionSubmissions,
    validate_spring_evaluation_result,
)
from strange_physics.fitting_contracts import validate_fit_result
from strange_physics.native_classical_contracts import (
    CLASSICAL_PRODUCER,
    MAX_CLASSICAL_BYTES,
    ClassicalDiagnosticInput,
    ClassicalDiagnosticOutcome,
    ClassicalDiagnosticResult,
    ClassicalReason,
    ClassicalStatus,
)
from strange_physics.native_spring_contracts import (
    NativeWorkFacts,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import (
    SpringPredictionResult,
    validate_spring_prediction_result,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.scientific_workflow import condition_keys, fit_spring, i1_protocol
from strange_physics.serialization import canonical_json
from strange_physics.workflow_contracts import SpringFitArtifact
from strange_physics.workflow_io import WorkflowError


def classical_condition_sha256(protocol: SpringEvaluationProtocol) -> str:
    """Exclude exactly model-derived identities; preserve every other canonical field."""
    data = protocol.model_dump(mode="json")
    del data["model_sha256"]
    for probe in data["probes"]:
        del probe["request_sha256"]
        del probe["request"]["model_sha256"]
    return hashlib.sha256(canonical_json(data).encode()).hexdigest()


def _preflight(actual: ClassicalDiagnosticInput) -> ClassicalReason | None:
    c = actual.context
    try:
        validate_native_candidate_result(
            c.candidate_result, c.candidates, attempt_id=c.candidate_attempt_id
        )
    except ValueError:
        return "candidate_mismatch"
    if c.selected is not None:
        try:
            validate_selected_native_candidate(
                c.selected, c.candidate_result, c.candidates, attempt_id=c.candidate_attempt_id
            )
        except ValueError:
            return "selection_mismatch"
    if message_sha256(c.policy) != message_sha256(actual.config.scoring_policy):
        return "policy_mismatch"
    if message_sha256(actual.world.space) != message_sha256(c.candidates.observations.space):
        return "world_space_mismatch"
    return None


def _protocol(
    actual: ClassicalDiagnosticInput,
    fit: SpringFitArtifact,
) -> tuple[ClassicalReason | None, SpringEvaluationProtocol | None, int | None, int | None]:
    assert fit.model is not None
    observations = actual.context.candidates.observations
    try:
        protocol = i1_protocol(fit.model, observations.space.structure)
        purchased = tuple(
            condition_keys(observations.space.structure, r.experiment) for r in observations.records
        )
        for i, probe in enumerate(protocol.probes):
            action, post = condition_keys(probe.request.structure, probe.request.experiment)
            for j, (bought_action, bought_post) in enumerate(purchased):
                if action == bought_action or post == bought_post:
                    return "purchased_overlap", None, i, j
    except WorkflowError:
        return "unsupported_topology", None, None, None
    selected = actual.context.selected
    if selected is not None:
        primary = i1_protocol(selected.model, observations.space.structure)
        if classical_condition_sha256(primary) != classical_condition_sha256(protocol):
            raise ValueError("Diagnostic and primary fixed conditions differ")
    return None, protocol, None, None


def _fit_binding(fit: SpringFitArtifact, actual: ClassicalDiagnosticInput) -> None:
    observations = actual.context.candidates.observations
    if message_sha256(fit.observations) != message_sha256(observations) or message_sha256(
        fit.config
    ) != message_sha256(actual.config.fit_config):
        raise ValueError("Diagnostic fit differs from actual prefix/configuration")
    if fit.fit_input is not None:
        if message_sha256(fit.fit_input.observations) != message_sha256(observations):
            raise ValueError("Retained fitter input differs from actual canonical prefix")
        assert fit.result is not None
        validate_fit_result(fit.result, fit.fit_input, actual.config.fit_config)
        if fit.model is not None:
            if canonical_json(fit.model.linear) != canonical_json(
                fit.result.diagnostics.raw_coefficient
            ):
                raise ValueError("Canonical fit estimate differs from actual model")


def run_classical_diagnostic(
    actual: ClassicalDiagnosticInput,
    *,
    attempt_id: str,
) -> ClassicalDiagnosticResult:
    """Execute one bounded private diagnostic; caller separately measures the whole attempt.

    Only public prefix/config reaches the fitter or predictor. This never reads a
    Journal, changes the native choice, redraws probes, or settles child work.
    Unexpected interruption propagates for the supervisor's unknown-cost recovery.
    """
    TypeAdapter(Identifier).validate_python(attempt_id)
    reason = _preflight(actual)
    fit = None
    protocol = None
    predictions: tuple[SpringPredictionResult, ...] = ()
    submissions = None
    evaluation = None
    overlap_probe = overlap_record = None
    status: ClassicalStatus = "rejected"
    if reason is None:
        fit = fit_spring(actual.context.candidates.observations, actual.config.fit_config)
        _fit_binding(fit, actual)
        if fit.input_rejection is not None:
            reason = "no_completed_records"
        elif fit.model is None:
            status, reason = "fit_failed", "fit_unavailable"
        else:
            reason, protocol, overlap_probe, overlap_record = _protocol(actual, fit)
            if reason is not None:
                status = "preparation_failed"
            else:
                assert protocol is not None
                predictions = tuple(
                    predict_linear_spring(fit.model, p.request, actual.config.prediction_config)
                    for p in protocol.probes
                )
                submissions = SpringPredictionSubmissions(
                    entries=tuple(
                        ProbePrediction(
                            probe_id=p.probe_id,
                            request_sha256=p.request_sha256,
                            status="response" if r.response is not None else "failed",
                            response=r.response,
                        )
                        for p, r in zip(protocol.probes, predictions, strict=True)
                    )
                )
                evaluation = evaluate_spring_predictions(
                    fit.model, protocol, submissions.entries, actual.world
                )
                status = "evaluated"
    payload = ClassicalDiagnosticOutcome(
        status=status,
        reason=reason,
        input_sha256=bounded_canonical(actual, MAX_CLASSICAL_BYTES)[0],
        context_sha256=message_sha256(actual.context),
        config_sha256=message_sha256(actual.config),
        observation_sha256=message_sha256(actual.context.candidates.observations),
        model_sha256=None if fit is None or fit.model is None else message_sha256(fit.model),
        fit=fit,
        protocol=protocol,
        predictions=predictions,
        prediction_not_assessed_count=24 - len(predictions),
        submissions=submissions,
        evaluation=evaluation,
        overlap_probe_index=overlap_probe,
        overlap_record_index=overlap_record,
    )
    completed = int(evaluation is not None and evaluation.status in {"scored", "unscorable"})
    rejected = int(status == "rejected")
    failed = 1 - completed - rejected
    result = ClassicalDiagnosticResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="classical_diagnostic",
            producer_version=CLASSICAL_PRODUCER,
            config_sha256=payload.config_sha256,
            input_sha256=payload.input_sha256,
            observation_sha256=payload.observation_sha256,
            model_sha256=payload.model_sha256,
            output_sha256=bounded_canonical(payload, MAX_CLASSICAL_BYTES)[0],
            unit="work",
            requested_count=1,
            completed_count=completed,
            failed_count=failed,
            not_assessed_count=rejected,
            outcome="completed" if completed else "rejected" if rejected else "failed",
        ),
    )
    validate_classical_diagnostic_result(result, actual, attempt_id=attempt_id)
    return result


def validate_classical_diagnostic_result(
    result: ClassicalDiagnosticResult,
    actual: ClassicalDiagnosticInput,
    *,
    attempt_id: str,
) -> None:
    """Bind actual stages/material canonically, not numerical execution or Journal authenticity."""
    TypeAdapter(Identifier).validate_python(attempt_id)
    p = result.payload
    if (
        result.facts.attempt_id != attempt_id
        or p.input_sha256 != bounded_canonical(actual, MAX_CLASSICAL_BYTES)[0]
        or p.context_sha256 != message_sha256(actual.context)
        or p.config_sha256 != message_sha256(actual.config)
        or p.observation_sha256 != message_sha256(actual.context.candidates.observations)
    ):
        raise ValueError("Diagnostic result differs from actual private material/attempt")
    reason = _preflight(actual)
    if reason is not None:
        if p.status != "rejected" or p.reason != reason:
            raise ValueError("Diagnostic result differs from actual preflight rejection")
        return
    fit = p.fit
    if fit is None:
        raise ValueError("Admitted diagnostic must retain its actual fitter artifact")
    _fit_binding(fit, actual)
    if fit.input_rejection is not None:
        if p.status != "rejected" or p.reason != "no_completed_records":
            raise ValueError("Diagnostic must preserve the actual no-completed rejection")
        return
    if fit.model is None:
        if p.status != "fit_failed":
            raise ValueError("Diagnostic must preserve the actual fit failure")
        return
    reason, protocol, probe_index, record_index = _protocol(actual, fit)
    if reason is not None:
        if (p.status, p.reason, p.overlap_probe_index, p.overlap_record_index) != (
            "preparation_failed",
            reason,
            probe_index,
            record_index,
        ):
            raise ValueError("Diagnostic differs from actual purchased/probe preparation")
        return
    if p.status != "evaluated" or p.protocol is None or protocol is None:
        raise ValueError("Prepared diagnostic must retain all attempted stages")
    if message_sha256(protocol) != message_sha256(p.protocol):
        raise ValueError("Diagnostic differs from the exact fixed fitted-model protocol")
    assert p.submissions is not None and p.evaluation is not None
    expected = []
    for probe, prediction in zip(protocol.probes, p.predictions, strict=True):
        validate_spring_prediction_result(
            prediction, fit.model, probe.request, actual.config.prediction_config
        )
        response = prediction.response
        if response is not None and canonical_json(
            tuple(frame.time for frame in response.trajectory.frames)
        ) != canonical_json(probe.request.times):
            raise ValueError("Diagnostic response canonical times differ from actual request")
        expected.append(
            ProbePrediction(
                probe_id=probe.probe_id,
                request_sha256=probe.request_sha256,
                status="response" if response is not None else "failed",
                response=response,
            )
        )
    if message_sha256(SpringPredictionSubmissions(entries=tuple(expected))) != message_sha256(
        p.submissions
    ):
        raise ValueError("Diagnostic submissions differ from actual ordered predictions")
    validate_spring_evaluation_result(
        p.evaluation, fit.model, protocol, p.submissions.entries, actual.world
    )
