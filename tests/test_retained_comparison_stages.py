"""Declared 45-call retained comparison specimen; no study or runtime admission.

This test needs the measured comparison adapter. Fixed index selection, repeated
calibration and a one-action menu test conformance, not MAP or scientific accuracy.
The profile is constructed once before durable seed admission. Any actual cap,
timer, store-fit or copy failure is a failure, never permission to enlarge it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import freeze_journal_fixture as fixture_module
import pytest
from freeze_journal_fixture import Fixture, classical_request, comparison_request, prepare
from test_measured_candidates import actual_build, current, last_update
from test_measured_purchase import forbidden, purchase_request, recover
from test_native_spring_contracts import selection

import strange_physics.measured_candidates as supervisor
import strange_physics.measured_native_stages as stages
import strange_physics.purchase_execution as purchase_producer
from strange_physics.candidate_execution_contracts import MIB, CandidateControl
from strange_physics.contracts import Message
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.native_classical import classical_condition_sha256
from strange_physics.measured_study import (
    CommittedPurchase,
    commit_journal_candidates,
    commit_journal_classical,
    commit_journal_purchase,
    commit_native_freeze,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionResult,
)
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativeProbeOutcome,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPredictionInput,
    NativeComparisonPreparationInput,
    NativeComparisonScoreInput,
    NativePredictionReference,
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
)
from strange_physics.publication_store import digest, head, raw
from strange_physics.purchase_execution_contracts import NativePurchaseRequest
from strange_physics.purchase_journal import JournalEpochs
from strange_physics.research_contracts import message_sha256
from strange_physics.simulation import SimulationError
from strange_physics.study_contracts import NativeWorldCatalog, StudyAttemptReservation
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalInput,
    NativeComparisonInput,
)
from strange_physics.study_ledger import summarize_study

__all__ = ["actual_build"]

SETUP_LIMIT = 48 * MIB
PREDICTION_LIMIT = 512 * 1024
DECLARED_BYTES = 978165760
DECLARED_CPU_NS = 1247000000000
# Original exports only. Measured retained inputs/outputs are charged separately.
# Bootstrap, 12 purchase inputs, candidate, classical, preparation, 24 predictions,
# score and final proof all fit before the first public call; no scratch exports.
SETUP_EXPORT_CEILING = (
    MIB
    + 12 * 64 * 1024
    + 128 * 1024
    + 256 * 1024
    + 16 * MIB
    + 24 * PREDICTION_LIMIT
    + 16 * MIB
    + 64 * 1024
)


def comparison_control(**values: Any) -> CandidateControl:
    """Override the initial test profile only, before any control seed is written."""
    return CandidateControl(
        **(
            values
            | {
                "tickets": 45,
                "recovery_tickets": 4,
                "finalization_records": 16,
                "finalization_bytes": 64 * 1024,
            }
        )
    )


def stage_request_data(
    fixture: Fixture,
    wrapper: Message,
    inner: Message,
    config: Message,
    *,
    ticket: int,
    operation: str,
    input_limit: int,
    output_limit: int,
    artifact_limit: int,
) -> dict[str, Any]:
    with fixture.budget.phase():
        value = raw(wrapper)
        assert len(value) <= input_limit
        assert len(raw(inner)) <= input_limit
        path = fixture.root / f"original-{operation}-{ticket}.json"
        fixture.budget.write(path, value)
        ledger = current(fixture.root)
        return {
            "mode": "execute",
            "logical_id": f"{operation}-{ticket}",
            "attempt_id": f"{operation}-{ticket}",
            "retry_of": None,
            "phase": "comparison",
            "cell_id": fixture.freeze.manifest.cells[0].cell_id,
            "ticket": ticket,
            "expected_revision": len(ledger.records),
            "expected_head_sha256": head(ledger),
            "input_path": str(path),
            "input_raw_sha256": digest(value),
            "input_bytes": len(value),
            "input_sha256": message_sha256(inner),
            "config_sha256": message_sha256(config),
            "cpu_reservation_ns": 12_000_000_000,
            "artifact_reservation_bytes": artifact_limit,
            "output_limit_bytes": output_limit,
            "wall_limit_ns": 30_000_000_000,
        }


def recovery_data(
    original: NativePreparationRequest | NativePredictionRequest | NativeScoreRequest,
    ticket: int,
) -> dict[str, Any]:
    # Preserve the original caller head, input and logical identity.
    return original.model_dump() | {
        "mode": "recover",
        "ticket": ticket,
        "attempt_id": f"recovery-{ticket}",
        "retry_of": None,
        "cpu_reservation_ns": 8_000_000_000,
        "artifact_reservation_bytes": 2 * MIB,
    }


def assert_paid_replay(
    original: CommittedPurchase | stages.CommittedNativeStage[Any],
    replay: CommittedPurchase | stages.CommittedNativeStage[Any],
) -> None:
    assert replay.replayed and replay.result_raw == original.result_raw
    assert raw(replay.receipt) == raw(original.receipt)
    assert replay.original_ledger == original.original_ledger
    assert replay.measurements.child_cpu_ns == 0
    update = last_update(replay.ledger)
    assert update.state == "completed" and update.facts is not None
    assert update.facts.operation == "accounting"
    assert update.cpu_ns == replay.measurements.parent_cpu_ns


def test_forty_five_call_retained_comparison_and_original_replays(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert SETUP_EXPORT_CEILING <= SETUP_LIMIT == 50331648
    # All exports, including later removed files/proof, share the pre-write cap.
    monkeypatch.setattr(fixture_module, "COPY_LIMIT", SETUP_LIMIT)
    with monkeypatch.context() as setup:
        setup.setattr(fixture_module, "CandidateControl", comparison_control)
        f = prepare(
            tmp_path / "comparison",
            actual_build,
            classical=True,
            purchase=True,
            database_limit_bytes=MIB,
        )
    assert f.budget.copies <= MIB
    assert f.control.tickets == 45 and f.control.recovery_tickets == 4
    assert f.control.database_limit_bytes == MIB
    assert f.control.required_control_bytes() == 688758784
    assert f.control.publication.required_bytes() == 80 * MIB
    recovery_start = f.control.tickets - f.control.recovery_tickets
    assert recovery_start == 41

    epochs: list[JournalEpochs] = []
    counts = {"writer": 0, "holder": 0, "other_child": 0}
    writer, holder, child = (
        supervisor.run_purchase_writer,
        supervisor.capture_journal,
        supervisor._run_child,
    )

    def tracked_epochs() -> JournalEpochs:
        value = JournalEpochs()
        epochs.append(value)
        return value

    def tracked_writer(*args: Any, **kwargs: Any) -> Any:
        counts["writer"] += 1
        return writer(*args, **kwargs)

    def tracked_holder(*args: Any, **kwargs: Any) -> Any:
        counts["holder"] += 1
        return holder(*args, **kwargs)

    def tracked_child(*args: Any, **kwargs: Any) -> Any:
        counts["other_child"] += 1
        return child(*args, **kwargs)

    def scientific_failure(*args: Any, **kwargs: Any) -> Any:
        raise SimulationError("declared comparison last-slot simulation fault")

    monkeypatch.setattr(supervisor, "JournalEpochs", tracked_epochs)
    monkeypatch.setattr(supervisor, "run_purchase_writer", tracked_writer)
    monkeypatch.setattr(supervisor, "capture_journal", tracked_holder)
    monkeypatch.setattr(supervisor, "_run_child", tracked_child)
    frozen = commit_native_freeze(f.root, f.freeze_request)  # Inline, no child.
    purchases: list[CommittedPurchase] = []
    purchase_requests: list[NativePurchaseRequest] = []
    for ordinal in range(12):
        request = purchase_request(
            f, raw(frozen.receipt), ordinal=ordinal, ticket=ordinal + 1,
            predecessor=purchases[-1] if purchases else None,
        )
        with monkeypatch.context() as fault:
            if ordinal == 11:
                fault.setattr(purchase_producer, "simulate", scientific_failure)
            value = commit_journal_purchase(f.root, request)
        assert value.result.record.index == ordinal
        assert value.result.record.status == ("failed" if ordinal == 11 else "completed")
        assert value.holder_status == 0 and value.holder_cpu_ns is not None
        assert last_update(value.ledger).facts == value.result.facts
        assert summarize_study(value.ledger).budget.unresolved_attempts == 2
        purchase_requests.append(request)
        purchases.append(value)
    assert len(epochs) == 12 and all(e.used == 15 for e in epochs)

    candidate_request = comparison_request(f, raw(frozen.receipt), ticket=13)
    candidate_request = NativeComparisonCandidateRequest.model_validate(
        candidate_request.model_dump() | {"artifact_reservation_bytes": 8 * MIB}
    )
    candidate = commit_journal_candidates(f.root, candidate_request)
    assert candidate.result.payload.status == "produced"
    with f.budget.phase():
        material = NativeComparisonInput.model_validate_json(
            (f.root / "candidate-input-13").read_bytes()
        )
        observations = material.candidate.observations
        assert [r.status for r in observations.records] == (
            ["completed"] * 11 + ["failed"]
        )
        assert tuple(raw(r) for r in observations.records) == tuple(
            raw(p.result.record) for p in purchases
        )
        assert observations.engine_fingerprint == actual_build.engine_fingerprint
        assert digest((f.root / "candidate-journal-13").read_bytes()) == material.journal_sha256
        assert tuple(r.index for r in observations.records) == tuple(range(12))
        chosen = selection(candidate.result, index=1)
        assert chosen.selection_claim == "selected-candidate-only"
        # Fixed before either evaluator runs; not MAP, acquisition or fit accuracy.
        context = NativeEvaluationInput(
            candidates=material.candidate,
            candidate_result=candidate.result,
            candidate_attempt_id=candidate_request.attempt_id,
            selected=chosen,
            policy=NativeScoringPolicy.model_validate_json(
                f.freeze.artifacts["scoring_policy"]
            ),
            prediction_config=NativePredictionConfig.model_validate_json(
                f.freeze.artifacts["prediction_config"]
            ),
        )
        prep_input = NativeComparisonPreparationInput(
            candidate_logical_id=candidate_request.logical_id,
            candidate_receipt_sha256=digest(raw(candidate.receipt)),
            context=context,
        )
    preparation_request = NativePreparationRequest(
        **stage_request_data(
            f, prep_input, context, context.policy, ticket=14, operation="preparation",
            input_limit=16 * MIB, output_limit=8 * MIB, artifact_limit=24 * MIB,
        )
    )
    preparation = stages.commit_native_preparation(f.root, preparation_request)
    protocol = preparation.result.payload.protocol
    assert preparation.result.payload.status == "prepared" and protocol is not None
    assert len(protocol.probes) == 24 and protocol.normalization_scale == 1.0
    assert all(len(p.request.times) == 41 for p in protocol.probes)
    assert preparation.result.facts.observation_sha256 == message_sha256(observations)

    predictions: list[stages.CommittedNativeStage[NativePredictionResult]] = []
    prediction_requests: list[NativePredictionRequest] = []
    references: list[NativePredictionReference] = []
    entries: list[NativeProbeOutcome] = []
    for index, probe in enumerate(protocol.probes):
        with f.budget.phase():
            inner = NativePredictionInput(
                model=chosen.model, candidate_config=context.candidates.config,
                request=probe.request, config=context.prediction_config,
            )
            wrapper = NativeComparisonPredictionInput(
                preparation_logical_id=preparation_request.logical_id,
                preparation_receipt_sha256=digest(raw(preparation.receipt)),
                probe_index=index, prediction=inner,
            )
        request = NativePredictionRequest(
            **stage_request_data(
                f, wrapper, inner, inner.config, ticket=15 + index, operation="prediction",
                input_limit=PREDICTION_LIMIT, output_limit=PREDICTION_LIMIT, artifact_limit=MIB,
            )
        )
        predicted = stages.commit_native_prediction(f.root, request)
        assert predicted.result.payload.status == "predicted"
        assert len(predicted.result_raw) <= PREDICTION_LIMIT
        assert predicted.result.facts.model_sha256 == message_sha256(chosen.model)
        assert predicted.result.facts.observation_sha256 == message_sha256(observations)
        with f.budget.phase():
            retained_request = (f.root / f"candidate-ticket-{request.ticket}").read_bytes()
            assert retained_request == raw(request)
            references.append(
                NativePredictionReference(
                    logical_id=request.logical_id, attempt_id=request.attempt_id,
                    ticket=request.ticket, request_raw_sha256=digest(retained_request),
                    status="result", receipt_sha256=digest(raw(predicted.receipt)),
                    output_raw_sha256=digest(predicted.result_raw),
                )
            )
            entries.append(
                NativeProbeOutcome(
                    probe_id=probe.probe_id, request_sha256=probe.request_sha256,
                    attempt_id=request.attempt_id, status="result", result=predicted.result,
                )
            )
        prediction_requests.append(request)
        predictions.append(predicted)

    with f.budget.phase():
        catalog = NativeWorldCatalog.model_validate_json(f.freeze.artifacts["world_catalog"])
        cell = f.freeze.manifest.cells[0]
        world = next(w.definition for w in catalog.worlds if w.world_id == cell.world_id)
        scoring = NativeScoringInput(
            context=context, preparation=preparation.result,
            predictions=NativePredictionCollection(entries=tuple(entries)), world=world,
        )
        score_input = NativeComparisonScoreInput(
            preparation_logical_id=preparation_request.logical_id,
            preparation_receipt_sha256=digest(raw(preparation.receipt)),
            predictions=tuple(references), scoring=scoring,
        )
    score_request = NativeScoreRequest(
        **stage_request_data(
            f, score_input, scoring, context.policy, ticket=39, operation="scoring",
            input_limit=16 * MIB, output_limit=8 * MIB, artifact_limit=24 * MIB,
        )
    )
    score = stages.commit_native_score(f.root, score_request)
    assert score.result.payload.evaluation is not None
    assert score.result.payload.evaluation.status == "scored"  # No score threshold.
    assert score.result.facts.outcome == "completed"
    assert score.result.facts.observation_sha256 == message_sha256(observations)

    diagnostic_request = classical_request(
        f, raw(candidate.receipt), candidate.result, candidate_ticket=13, ticket=40
    )
    with f.budget.phase():
        diagnostic_input = NativeComparisonClassicalInput.model_validate_json(
            Path(diagnostic_request.input_path).read_bytes()
        )
        assert diagnostic_input.diagnostic.context.selected is None
        assert raw(diagnostic_input.diagnostic.context.candidates.observations) == raw(
            observations
        )
        assert message_sha256(diagnostic_input.diagnostic.world) == message_sha256(world)
    diagnostic = commit_journal_classical(f.root, diagnostic_request)
    payload = diagnostic.result.payload
    assert payload.evaluation is not None and payload.evaluation.status == "scored"
    assert payload.fit is not None and raw(payload.fit.observations) == raw(observations)
    assert payload.protocol is not None
    assert classical_condition_sha256(payload.protocol) == classical_condition_sha256(protocol)
    assert len(diagnostic.ledger.records) == 85  # Later work after the original score.

    with f.budget.phase():
        journal_bytes = f.journal.stat().st_size
        assert journal_bytes <= 128 * 1024
        assert digest(f.journal.read_bytes()) == material.journal_sha256
        retained_inputs = {
            r.ticket: digest((f.root / f"candidate-input-{r.ticket}").read_bytes())
            for r in (
                purchase_requests[-1],
                preparation_request,
                prediction_requests[0],
                score_request,
            )
        }
        assert retained_inputs == {
            r.ticket: r.input_raw_sha256
            for r in (
                purchase_requests[-1],
                preparation_request,
                prediction_requests[0],
                score_request,
            )
        }
        for path in [
            f.journal, Path(f.freeze_request.input_path), Path(candidate_request.input_path),
            Path(preparation_request.input_path), Path(score_request.input_path),
            Path(diagnostic_request.input_path),
            *(Path(r.input_path) for r in purchase_requests),
            *(Path(r.input_path) for r in prediction_requests),
        ]:
            path.unlink()

    # Preserve deterministic protocol validation; prohibit numerical dispatch and
    # actual producer aliases. Recovery must use original retained material only.
    for name in (
        "strange_physics.measured_candidates._run_child",
        "strange_physics.measured_candidates.run_purchase_writer",
        "strange_physics.measured_candidates.capture_journal",
        "strange_physics.measured_candidates.produce_native_candidates",
        "strange_physics.measured_candidates.run_classical_diagnostic",
        "strange_physics.measured_candidates.produce_stage",
        "strange_physics.purchase_execution.simulate",
        "strange_physics.native_stage_dispatch.predict_native_spring",
        "strange_physics.native_stage_dispatch.score_native_predictions",
        "strange_physics.native_scoring.evaluate_spring_predictions",
    ):
        monkeypatch.setattr(name, forbidden)
    purchase_replay = commit_journal_purchase(
        f.root,
        recover(
            purchase_requests[-1],
            ticket=recovery_start,
            attempt_id=f"recovery-{recovery_start}",
        ),
    )
    prep_replay = stages.commit_native_preparation(
        f.root,
        NativePreparationRequest.model_validate(
            recovery_data(preparation_request, recovery_start + 1)
        ),
    )
    prediction_replay = stages.commit_native_prediction(
        f.root,
        NativePredictionRequest.model_validate(
            recovery_data(prediction_requests[0], recovery_start + 2)
        ),
    )
    score_replay = stages.commit_native_score(
        f.root,
        NativeScoreRequest.model_validate(recovery_data(score_request, recovery_start + 3)),
    )
    assert_paid_replay(purchases[-1], purchase_replay)
    assert_paid_replay(preparation, prep_replay)
    assert_paid_replay(predictions[0], prediction_replay)
    assert_paid_replay(score, score_replay)
    assert purchase_replay.holder_cpu_ns is None
    assert counts == {"writer": 12, "holder": 12, "other_child": 28}

    with f.budget.phase():
        ledger = score_replay.ledger
        budget = summarize_study(ledger).budget
        assert len(ledger.records) == 93 and budget.unresolved_attempts == 2
        assert len(raw(ledger)) <= 256 * 1024
        assert (f.root / "candidate.sqlite3").stat().st_size <= MIB
        assert all(
            (f.root / f"candidate-ticket-{i}").is_file()
            for i in (*range(41), *range(recovery_start, recovery_start + 4))
        )
        assert retained_inputs == {
            ticket: digest((f.root / f"candidate-input-{ticket}").read_bytes())
            for ticket in retained_inputs
        }
        assert not (f.root / "candidate-ticket-45").exists()
        assert f.budget.child_epochs == f.budget.store_attempts == 0
        assert f.budget.parent_cpu + f.budget.child_cpu <= 120_000_000_000
        assert f.budget.copies <= SETUP_EXPORT_CEILING
        supervisor._capacity(f.root, ledger, f.control)
        assert budget.remaining_artifact_bytes >= f.control.publication.required_bytes()
        assert budget.remaining_cpu_ns >= (
            f.control.publication.control_cpu_ns + f.control.publication.work_cpu_ns
        )
        setup = ledger.records[0].event
        control = ledger.records[1].event
        assert isinstance(setup, StudyAttemptReservation)
        assert setup.artifact_reservation_bytes == SETUP_LIMIT
        assert isinstance(control, StudyAttemptReservation)
        assert control.cpu_reservation_ns == 320_000_000_000
        ordinary = [
            f.freeze_request, *purchase_requests, candidate_request, preparation_request,
            *prediction_requests, score_request, diagnostic_request,
        ]
        assert len(ordinary) == 41
        assert sum(r.artifact_reservation_bytes for r in ordinary) == 146800640
        assert sum(r.cpu_reservation_ns for r in ordinary) == 704_000_000_000
        assert (
            SETUP_LIMIT + f.control.required_control_bytes()
            + sum(r.artifact_reservation_bytes for r in ordinary)
            + 4 * f.control.recovery_work_artifact_bytes
            + f.control.publication.required_bytes()
        ) == DECLARED_BYTES
        assert (
            setup.cpu_reservation_ns + control.cpu_reservation_ns
            + sum(r.cpu_reservation_ns for r in ordinary)
            + 4 * f.control.recovery_work_cpu_ns
            + f.control.publication.control_cpu_ns + f.control.publication.work_cpu_ns
        ) == DECLARED_CPU_NS
        proof = {
            "scope": "Synthetic retained comparison conformance, not MAP/study/publication.",
            "public_calls": 45, "normal_calls": 41, "paid_recoveries": 4,
            "entry_counts": counts, "precharged_journal_epochs": sum(e.used for e in epochs),
            "ledger_records": len(ledger.records), "ledger_bytes": len(raw(ledger)),
            "unresolved_holds": budget.unresolved_attempts,
            "journal_bytes_before_removal": journal_bytes,
            "store_bytes": (f.root / "candidate.sqlite3").stat().st_size,
            "setup_copy_bytes_before_proof": f.budget.copies,
            "setup_export_ceiling_bytes": SETUP_EXPORT_CEILING,
            "setup_parent_cpu_before_proof_ns": f.budget.parent_cpu,
            "declared_artifact_bytes": DECLARED_BYTES, "declared_cpu_ns": DECLARED_CPU_NS,
            "remaining_artifact_bytes": budget.remaining_artifact_bytes,
            "remaining_cpu_ns": budget.remaining_cpu_ns,
            "publication_protection_bytes": f.control.publication.required_bytes(),
            "purchase_measurements": [p.measurements.model_dump() for p in purchases],
            "purchase_holder_cpu_ns": [p.holder_cpu_ns for p in purchases],
            "candidate_measurements": candidate.measurements.model_dump(),
            "preparation_measurements": preparation.measurements.model_dump(),
            "prediction_measurements": [p.measurements.model_dump() for p in predictions],
            "score_measurements": score.measurements.model_dump(),
            "classical_measurements": diagnostic.measurements.model_dump(),
            "recovery_measurements": [
                p.measurements.model_dump()
                for p in (purchase_replay, prep_replay, prediction_replay, score_replay)
            ],
            "recovery_holder_cpu_ns": purchase_replay.holder_cpu_ns,
        }
        proof_bytes = json.dumps(proof, sort_keys=True).encode()
        assert len(proof_bytes) <= 64 * 1024
        f.budget.write(f.root / "comparison-call-proof.json", proof_bytes)
        assert f.budget.copies <= SETUP_EXPORT_CEILING <= SETUP_LIMIT
