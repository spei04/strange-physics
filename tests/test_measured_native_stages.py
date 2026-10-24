"""Synthetic pre-freeze measured chains; no comparison or full-study admission."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from test_measured_candidates import actual_build, change, private, setup
from test_native_spring_contracts import selection

from strange_physics import measured_candidates as supervisor
from strange_physics import measured_native_stages as stages
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    CandidateRequest,
    PublicationEscrow,
)
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.laws import LawSpec
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
)
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativeProbeOutcome,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_spring_contracts import parse_native_candidate_input
from strange_physics.native_stage_execution_contracts import (
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
)
from strange_physics.publication_store import digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    NativeStudyLedger,
    StudyAttemptReservation,
)
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    read_study_ledger,
    summarize_study,
)
from strange_physics.worlds import WorldDefinition

__all__ = ["actual_build"]


def sequence_setup(root: Path, build: TrustedInstallation) -> CandidateRequest:
    publication = PublicationEscrow(
        calls=2,
        material_bytes=4 * MIB,
        journal_bytes=2 * MIB,
        ledger_bytes=512 * 1024,
        output_bytes=4 * MIB,
        control_cpu_ns=3_000_000_000,
        control_artifact_bytes=48 * MIB,
        work_cpu_ns=8_000_000_000,
    )
    first = setup(root, build, publication=publication)
    admission = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    )
    c = CandidateControl.model_validate(
        admission.control.model_dump()
        | {
            "tickets": 30,
            "recovery_tickets": 3,
            "finalization_records": 14,
            "finalization_bytes": 64 * 1024,
        }
    )
    old = read_study_ledger((root / "candidate-seed.json").read_bytes())
    seed = NativeStudyLedger(plan=old.plan, records=())
    seed = append_study_attempt(
        seed,
        event_id="control-reserve",
        expected_revision=0,
        event=StudyAttemptReservation(
            attempt_id=c.attempt_id,
            phase="accounting",
            cell_id=None,
            operation="accounting",
            config_sha256=message_sha256(c),
            input_sha256=c.plan_sha256,
            retry_of=None,
            cpu_reservation_ns=c.tickets * c.ticket_cpu_ns + c.bootstrap_cpu_ns,
            artifact_reservation_bytes=c.required_control_bytes(),
            purchase=None,
        ),
    )
    private(root / "candidate-seed.json", raw(seed))
    private(
        root / "candidate-admission.json",
        raw(CandidateAdmission(control=c, seed_ledger_sha256=digest(raw(seed)))),
    )
    return change(
        first,
        expected_revision=len(seed.records),
        expected_head_sha256=head(seed),
        artifact_reservation_bytes=12 * MIB,
    )


def request_data(
    root: Path,
    value: Any,
    config: Any,
    ledger: NativeStudyLedger,
    ticket: int,
    *,
    operation: str,
    output: int,
    artifact: int,
) -> dict[str, Any]:
    data = raw(value)
    path = root / f"{operation}-{ticket}.json"
    private(path, data)
    return dict(
        operation=operation,
        mode="execute",
        logical_id=f"{operation}-{ticket}",
        attempt_id=f"{operation}-{ticket}",
        retry_of=None,
        phase="reference",
        cell_id=None,
        ticket=ticket,
        expected_revision=len(ledger.records),
        expected_head_sha256=head(ledger),
        input_path=str(path),
        input_raw_sha256=digest(data),
        input_bytes=len(data),
        input_sha256=message_sha256(value),
        config_sha256=message_sha256(config),
        cpu_reservation_ns=12_000_000_000,
        artifact_reservation_bytes=artifact,
        output_limit_bytes=output,
        wall_limit_ns=30_000_000_000,
    )


def prepared(
    root: Path, build: TrustedInstallation
) -> tuple[NativeEvaluationInput, stages.CommittedNativeStage[Any], NativePreparationRequest]:
    first = sequence_setup(root, build)
    candidate = supervisor.commit_native_candidates(root, first)
    actual = parse_native_candidate_input((root / "candidate-input-0").read_bytes())
    chosen = selection(candidate.result, index=1)  # Explicit synthetic choice, not MAP.
    context = NativeEvaluationInput(
        candidates=actual,
        candidate_result=candidate.result,
        candidate_attempt_id=first.attempt_id,
        selected=chosen,
        policy=NativeScoringPolicy(),
        prediction_config=NativePredictionConfig(),
    )
    request = NativePreparationRequest(
        **request_data(
            root,
            context,
            context.policy,
            candidate.ledger,
            1,
            operation="preparation",
            output=8 * MIB,
            artifact=24 * MIB,
        )
    )
    result = stages.commit_native_preparation(root, request)
    assert result.result.payload.status == "prepared"
    assert chosen.model.observation_sha256 == candidate.result.payload.observation_sha256
    assert result.result.facts.model_sha256 == message_sha256(chosen.model)
    return context, result, request


def test_one_ledger_candidate_preparation_24_predictions_score_and_paid_replays(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "run"
    context, preparation, preparation_request = prepared(root, actual_build)
    protocol = preparation.result.payload.protocol
    assert protocol is not None and context.selected is not None
    ledger = preparation.ledger
    entries = []
    prediction_requests = []
    sizes = []
    for index, probe in enumerate(protocol.probes):
        actual = NativePredictionInput(
            model=context.selected.model,
            candidate_config=context.candidates.config,
            request=probe.request,
            config=context.prediction_config,
        )
        request = NativePredictionRequest(
            **request_data(
                root,
                actual,
                actual.config,
                ledger,
                index + 2,
                operation="prediction",
                output=512 * 1024,
                artifact=MIB,
            )
        )
        assert request.input_bytes <= 512 * 1024
        result = stages.commit_native_prediction(root, request)
        assert result.result.payload.status == "predicted"
        assert result.result.facts.model_sha256 == message_sha256(context.selected.model)
        assert result.result.facts.observation_sha256 == message_sha256(
            context.candidates.observations
        )
        assert result.original_ledger.records[:-1] == ledger.records
        entries.append(
            NativeProbeOutcome(
                probe_id=probe.probe_id,
                request_sha256=probe.request_sha256,
                attempt_id=request.attempt_id,
                status="result",
                result=result.result,
            )
        )
        prediction_requests.append(request)
        sizes.append((request.input_bytes, len(result.result_raw)))
        ledger = result.ledger
    score_input = NativeScoringInput(
        context=context,
        preparation=preparation.result,
        predictions=NativePredictionCollection(entries=tuple(entries)),
        world=WorldDefinition(
            space=context.candidates.observations.space,
            noise_seed=31,
            initial_law=LawSpec(kind="spring", parameters={"linear": 1.0}),
        ),
    )
    score_request = NativeScoreRequest(
        **request_data(
            root,
            score_input,
            context.policy,
            ledger,
            26,
            operation="scoring",
            output=8 * MIB,
            artifact=24 * MIB,
        )
    )
    score = stages.commit_native_score(root, score_request)
    assert score.result.payload.evaluation is not None
    assert score.result.payload.evaluation.status == "scored"
    assert len(score.ledger.records) == 55
    assert score.original_ledger.records[:-1] == ledger.records

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Paid recovery reran a numerical child")

    monkeypatch.setattr(supervisor, "_run_child", forbidden)

    def recovery_values(
        original: NativePreparationRequest | NativePredictionRequest | NativeScoreRequest,
        ticket: int,
    ) -> dict[str, Any]:
        Path(original.input_path).unlink()
        return original.model_dump() | {
            "mode": "recover",
            "ticket": ticket,
            "attempt_id": f"recover-{ticket}",
            "cpu_reservation_ns": 8_000_000_000,
            "artifact_reservation_bytes": 2 * MIB,
        }

    recovered_preparation = stages.commit_native_preparation(
        root, NativePreparationRequest.model_validate(recovery_values(preparation_request, 27))
    )
    recovered_prediction = stages.commit_native_prediction(
        root, NativePredictionRequest.model_validate(recovery_values(prediction_requests[0], 28))
    )
    recovered = stages.commit_native_score(
        root, NativeScoreRequest.model_validate(recovery_values(score_request, 29))
    )
    for replay in (recovered_preparation, recovered_prediction, recovered):
        assert replay.replayed
        reservation = replay.original_ledger.records[-1].event
        assert isinstance(reservation, StudyAttemptReservation)
        assert reservation.attempt_id == replay.receipt.original_attempt_id
    assert recovered_preparation.result_raw == preparation.result_raw
    assert recovered_prediction.result == entries[0].result
    assert recovered.result_raw == score.result_raw and recovered.receipt == score.receipt
    budget = summarize_study(recovered.ledger).budget
    assert budget.unresolved_attempts == 1 and budget.remaining_artifact_bytes > 140 * MIB
    private(
        root / "fixture-sizes.json",
        json.dumps(
            {
                "prediction_input_max": max(v[0] for v in sizes),
                "prediction_result_max": max(v[1] for v in sizes),
                "preparation_input": preparation_request.input_bytes,
                "preparation_result": len(preparation.result_raw),
                "score_input": score_request.input_bytes,
                "score_result": len(score.result_raw),
                "final_ledger_bytes": len(raw(recovered.ledger)),
                "db_bytes": (root / "candidate.sqlite3").stat().st_size,
                "purpose": "synthetic fixture, not full-study admission",
            },
            sort_keys=True,
        ).encode(),
    )


def test_preparation_paid_recovery_rejects_candidate_receipt_substitution(
    tmp_path: Path,
    actual_build: TrustedInstallation,
) -> None:
    root = tmp_path / "run"
    _, first, request = prepared(root, actual_build)
    foreign = NativePreparationRequest.model_validate(
        request.model_dump()
        | {
            "mode": "recover",
            "ticket": 27,
            "attempt_id": "foreign",
            "logical_id": "candidates",
            "cpu_reservation_ns": 8_000_000_000,
            "artifact_reservation_bytes": 2 * MIB,
        }
    )
    with pytest.raises(StudyLedgerError, match="request_conflict"):
        stages.commit_native_preparation(root, foreign)
    assert first.receipt.operation == "preparation"
