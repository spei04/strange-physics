"""One conditional 44-call execution-to-publisher specimen, not a study.

Fixed selection and repeated actions test authority/material conformance. The
profile is initialized once; failure never permits a retry or larger allowance.
Requires the separately reviewed handoff caller and original diagnostic transport.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import freeze_journal_fixture as fixture_module
import pytest
from freeze_journal_fixture import classical_request, comparison_request, prepare, sync_directory
from test_measured_candidates import actual_build, current, last_update
from test_measured_purchase import forbidden, purchase_request
from test_native_spring_contracts import selection
from test_retained_comparison_stages import stage_request_data

import strange_physics.measured_candidates as supervisor
import strange_physics.measured_native_stages as stages
import strange_physics.measured_publication as publisher
import strange_physics.native_candidates as native_candidates
import strange_physics.native_classical as native_classical
import strange_physics.native_prediction as native_prediction
import strange_physics.native_scoring as native_scoring
import strange_physics.publication_activation as activation
import strange_physics.purchase_execution as purchase_producer
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    PublicationEscrow,
)
from strange_physics.execution_publication_handoff import commit_publication_handoff
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_publication_contracts import (
    NativePublicationRequest,
    PublicationControl,
)
from strange_physics.measured_study import (
    CommittedPurchase,
    commit_journal_candidates,
    commit_journal_classical,
    commit_journal_purchase,
    commit_native_freeze,
)
from strange_physics.native_classical import classical_condition_sha256
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
from strange_physics.publication_handoff_contracts import (
    HANDOFF_MATERIAL_NAMES,
    HandoffReference,
    PublicationHandoffIntent,
    PublicationHandoffRequest,
    validate_handoff_ledger,
)
from strange_physics.publication_store import digest, head, raw
from strange_physics.purchase_execution_contracts import NativePurchaseRequest
from strange_physics.purchase_journal import JournalEpochs, capture_journal
from strange_physics.research_contracts import message_sha256
from strange_physics.simulation import SimulationError
from strange_physics.study_contracts import (
    NativeStudyLedger,
    NativeWorldCatalog,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalInput,
    NativeComparisonInput,
)
from strange_physics.study_ledger import summarize_study
from strange_physics.study_publication_contracts import parse_study_publication_evidence

__all__ = ["actual_build"]

SETUP_LIMIT = 48 * MIB
PREDICTION_LIMIT = 512 * 1024
DECLARED_BYTES = 1026908160
DECLARED_CPU_NS = 1356000000000
# Original exports only: bootstrap, twelve purchases, candidate, classical,
# preparation, 24 predictions, score and proof. Measured copies are separate.
SETUP_EXPORT_CEILING = (
    MIB
    + 12 * 64 * 1024
    + 128 * 1024
    + 256 * 1024
    + 2 * MIB
    + 24 * PREDICTION_LIMIT
    + 2 * MIB
    + 64 * 1024
)


def handoff_control(**values: Any) -> CandidateControl:
    """Construct this finite profile before the first admitted source seed."""
    return CandidateControl(
        **(
            values
            | {
                "tickets": 43,
                "recovery_tickets": 1,
                "recovery_work_cpu_ns": 60_000_000_000,
                "recovery_work_artifact_bytes": 16 * MIB,
                "finalization_records": 16,
                "finalization_bytes": 64 * 1024,
                "publication": PublicationEscrow(
                    calls=3,
                    material_bytes=2 * MIB,
                    journal_bytes=128 * 1024,
                    ledger_bytes=512 * 1024,
                    output_bytes=2 * MIB,
                    control_cpu_ns=16_000_000_000,
                    control_artifact_bytes=64 * MIB,
                    work_cpu_ns=90_000_000_000,
                ),
            }
        )
    )


def test_forty_four_call_original_history_handoff_and_paid_publication_replay(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert SETUP_EXPORT_CEILING == 19_070_976
    assert SETUP_EXPORT_CEILING <= SETUP_LIMIT == 50_331_648
    monkeypatch.setattr(fixture_module, "COPY_LIMIT", SETUP_LIMIT)
    with monkeypatch.context() as setup_override:
        setup_override.setattr(fixture_module, "CandidateControl", handoff_control)
        f = prepare(
            tmp_path / "handoff-source",
            actual_build,
            classical=True,
            purchase=True,
            database_limit_bytes=MIB,
            setup_lifetime_ns=600_000_000_000,
        )
    assert f.control.tickets == 43 and f.control.recovery_tickets == 1
    assert f.control.database_limit_bytes == MIB
    assert f.control.required_control_bytes() == 658_333_696
    assert f.control.publication.required_bytes() == 137_887_744
    assert f.control.publication.work_bytes_per_call() == 23_592_960

    with f.budget.phase():
        # The build fixture established these original paths before prepare.
        # No additional copy or later descriptor/path rebasing is permitted.
        assert raw(f.build) == raw(actual_build)
        trusted_paths = [
            Path(actual_build.lock_path),
            Path(actual_build.archive_path),
            Path(actual_build.provenance_path),
        ]
        trusted_hashes = {}
        for path in trusted_paths:
            info = path.stat()
            assert path.is_file() and not path.is_symlink()
            assert info.st_mode & 0o077 == 0 and info.st_size <= 2 * MIB
            assert not path.is_relative_to(f.root)
            trusted_hashes[str(path)] = digest(path.read_bytes())
        assert trusted_hashes[actual_build.lock_path] == actual_build.uv_lock_sha256
        assert trusted_hashes[actual_build.archive_path] == actual_build.archive_sha256
        assert trusted_hashes[actual_build.provenance_path] == actual_build.provenance_sha256
        seed = NativeStudyLedger.model_validate_json((f.root / "candidate-seed.json").read_bytes())
        setup, control = (record.event for record in seed.records)
        assert isinstance(setup, StudyAttemptReservation)
        assert isinstance(control, StudyAttemptReservation)
        assert setup.artifact_reservation_bytes == SETUP_LIMIT
        assert control.cpu_reservation_ns == 306_000_000_000
        assert f.budget.copies <= MIB

    public_entries: list[tuple[str, int]] = []
    public_returns: list[tuple[str, int]] = []

    def invoke[T](function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        assert len(public_entries) < 44, "undeclared public invocation"
        entry = (function.__name__, args[1].ticket)
        public_entries.append(entry)
        value = function(*args, **kwargs)
        public_returns.append(entry)
        return value

    epochs: list[JournalEpochs] = []
    counts = {"writer": 0, "holder": 0, "other_child": 0}
    writer, holder, child = (
        purchase_producer.run_purchase_writer,
        capture_journal,
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
    frozen = invoke(commit_native_freeze, f.root, f.freeze_request)  # Inline, no child.
    purchases: list[CommittedPurchase] = []
    purchase_requests: list[NativePurchaseRequest] = []
    for ordinal in range(12):
        purchase_call = purchase_request(
            f,
            raw(frozen.receipt),
            ordinal=ordinal,
            ticket=ordinal + 1,
            predecessor=purchases[-1] if purchases else None,
        )
        with monkeypatch.context() as fault:
            if ordinal == 11:
                fault.setattr(purchase_producer, "simulate", scientific_failure)
            value = invoke(commit_journal_purchase, f.root, purchase_call)
        assert value.result.record.index == ordinal
        assert value.result.record.status == ("failed" if ordinal == 11 else "completed")
        assert value.holder_status == 0 and value.holder_cpu_ns is not None
        assert last_update(value.ledger).facts == value.result.facts
        assert summarize_study(value.ledger).budget.unresolved_attempts == 2
        purchase_requests.append(purchase_call)
        purchases.append(value)
    assert len(epochs) == 12 and all(e.used == 15 for e in epochs)

    candidate_request = comparison_request(f, raw(frozen.receipt), ticket=13)
    candidate_request = NativeComparisonCandidateRequest.model_validate(
        candidate_request.model_dump() | {"artifact_reservation_bytes": 8 * MIB}
    )
    candidate = invoke(commit_journal_candidates, f.root, candidate_request)
    assert candidate.result.payload.status == "produced"
    with f.budget.phase():
        material = NativeComparisonInput.model_validate_json(
            (f.root / "candidate-input-13").read_bytes()
        )
        observations = material.candidate.observations
        assert [r.status for r in observations.records] == (["completed"] * 11 + ["failed"])
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
            policy=NativeScoringPolicy.model_validate_json(f.freeze.artifacts["scoring_policy"]),
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
            f,
            prep_input,
            context,
            context.policy,
            ticket=14,
            operation="preparation",
            input_limit=2 * MIB,
            output_limit=8 * MIB,
            artifact_limit=24 * MIB,
        )
    )
    preparation = invoke(stages.commit_native_preparation, f.root, preparation_request)
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
                model=chosen.model,
                candidate_config=context.candidates.config,
                request=probe.request,
                config=context.prediction_config,
            )
            wrapper = NativeComparisonPredictionInput(
                preparation_logical_id=preparation_request.logical_id,
                preparation_receipt_sha256=digest(raw(preparation.receipt)),
                probe_index=index,
                prediction=inner,
            )
        request = NativePredictionRequest(
            **stage_request_data(
                f,
                wrapper,
                inner,
                inner.config,
                ticket=15 + index,
                operation="prediction",
                input_limit=PREDICTION_LIMIT,
                output_limit=PREDICTION_LIMIT,
                artifact_limit=MIB,
            )
        )
        predicted = invoke(stages.commit_native_prediction, f.root, request)
        assert predicted.result.payload.status == "predicted"
        assert len(predicted.result_raw) <= PREDICTION_LIMIT
        assert predicted.result.facts.model_sha256 == message_sha256(chosen.model)
        assert predicted.result.facts.observation_sha256 == message_sha256(observations)
        with f.budget.phase():
            retained_request = (f.root / f"candidate-ticket-{request.ticket}").read_bytes()
            assert retained_request == raw(request)
            references.append(
                NativePredictionReference(
                    logical_id=request.logical_id,
                    attempt_id=request.attempt_id,
                    ticket=request.ticket,
                    request_raw_sha256=digest(retained_request),
                    status="result",
                    receipt_sha256=digest(raw(predicted.receipt)),
                    output_raw_sha256=digest(predicted.result_raw),
                )
            )
            entries.append(
                NativeProbeOutcome(
                    probe_id=probe.probe_id,
                    request_sha256=probe.request_sha256,
                    attempt_id=request.attempt_id,
                    status="result",
                    result=predicted.result,
                )
            )
        prediction_requests.append(request)
        predictions.append(predicted)

    with f.budget.phase():
        catalog = NativeWorldCatalog.model_validate_json(f.freeze.artifacts["world_catalog"])
        cell = f.freeze.manifest.cells[0]
        world = next(w.definition for w in catalog.worlds if w.world_id == cell.world_id)
        scoring = NativeScoringInput(
            context=context,
            preparation=preparation.result,
            predictions=NativePredictionCollection(entries=tuple(entries)),
            world=world,
        )
        score_input = NativeComparisonScoreInput(
            preparation_logical_id=preparation_request.logical_id,
            preparation_receipt_sha256=digest(raw(preparation.receipt)),
            predictions=tuple(references),
            scoring=scoring,
        )
    score_request = NativeScoreRequest(
        **stage_request_data(
            f,
            score_input,
            scoring,
            context.policy,
            ticket=39,
            operation="scoring",
            input_limit=2 * MIB,
            output_limit=8 * MIB,
            artifact_limit=24 * MIB,
        )
    )
    score = invoke(stages.commit_native_score, f.root, score_request)
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
        assert raw(diagnostic_input.diagnostic.context.candidates.observations) == raw(observations)
        assert message_sha256(diagnostic_input.diagnostic.world) == message_sha256(world)
    diagnostic = invoke(commit_journal_classical, f.root, diagnostic_request)
    payload = diagnostic.result.payload
    assert payload.evaluation is not None and payload.evaluation.status == "scored"
    assert payload.fit is not None and raw(payload.fit.observations) == raw(observations)
    assert payload.protocol is not None
    assert classical_condition_sha256(payload.protocol) == classical_condition_sha256(protocol)
    assert len(diagnostic.ledger.records) == 85  # Later work after the original score.

    with f.budget.phase():
        assert len(public_entries) == len(public_returns) == 41
        assert [ticket for _, ticket in public_entries] == list(range(41))
        assert counts == {"writer": 12, "holder": 12, "other_child": 28}
        assert len(raw(scoring)) <= 512 * 1024
        assert len(score.result_raw) <= 256 * 1024
        assert len(raw(diagnostic_input.diagnostic)) <= 128 * 1024
        assert len(raw(diagnostic.result)) <= 512 * 1024
        assert f.journal.stat().st_size <= 128 * 1024
        source_before_transfer = raw(diagnostic.ledger)
        assert len(source_before_transfer) <= 224 * 1024
        assert summarize_study(diagnostic.ledger).budget.unresolved_attempts == 2
        source_admission = CandidateAdmission.model_validate_json(
            (f.root / "candidate-admission.json").read_bytes()
        )
        target = tmp_path / "publisher"
        target.mkdir(mode=0o700)
        sync_directory(target.parent)
        target_stat = target.stat()
        target_control = PublicationControl(
            root=str(target),
            accounting_plan_sha256=f.control.plan_sha256,
            source_commit=f.control.source_commit,
            uv_lock_sha256=f.control.uv_lock_sha256,
            attempt_id="publisher-control",
            tickets=3,
            ticket_cpu_ns=5_000_000_000,
            ticket_wall_ns=30_000_000_000,
            ticket_artifact_bytes=16 * MIB,
        )
        intent = PublicationHandoffIntent(
            transfer_id="original-scored-handoff",
            source_admission_sha256=message_sha256(source_admission),
            cell_id=cell.cell_id,
            scoring=HandoffReference(
                logical_id=score_request.logical_id,
                receipt_sha256=digest(raw(score.receipt)),
            ),
            diagnostic=HandoffReference(
                logical_id=diagnostic_request.logical_id,
                receipt_sha256=digest(raw(diagnostic.receipt)),
            ),
            destination=target_control,
            destination_device=target_stat.st_dev,
            destination_inode=target_stat.st_ino,
        )
        transfer_request = PublicationHandoffRequest(
            intent=intent,
            attempt_id="handoff-41",
            mode="execute",
            recover_attempt_id=None,
            ticket=41,
            expected_revision=len(diagnostic.ledger.records),
            expected_head_sha256=head(diagnostic.ledger),
            cpu_reservation_ns=60_000_000_000,
            artifact_reservation_bytes=16 * MIB,
            wall_limit_ns=30_000_000_000,
        )
    handed = invoke(commit_publication_handoff, f.root, transfer_request)

    with f.budget.phase():
        origin = handed.origin
        assert origin.seal.intent == intent
        assert handed.admission.control == target_control
        assert handed.admission.origin_sha256 == message_sha256(origin)
        assert tuple(raw(r) for r in handed.ledger.records[:85]) == tuple(
            raw(r) for r in diagnostic.ledger.records
        )
        validate_handoff_ledger(origin.seal, handed.ledger)
        assert len(handed.ledger.records) == 88
        assert digest(raw(handed.ledger)) == origin.seal.seed_ledger_sha256
        assert summarize_study(handed.ledger).budget.unresolved_attempts == 3
        publisher_hold = handed.ledger.records[-1].event
        assert isinstance(publisher_hold, StudyAttemptReservation)
        assert publisher_hold.attempt_id == target_control.attempt_id
        expected_materials = {
            name: value.encode()
            for name, value in f.freeze.artifacts.items()
            if name in HANDOFF_MATERIAL_NAMES
        } | {
            "scoring_input": raw(scoring),
            "scoring_result": score.result_raw,
            "diagnostic_input": raw(diagnostic_input.diagnostic),
            "diagnostic_result": raw(diagnostic.result),
        }
        assert sum(map(len, expected_materials.values())) <= 2 * MIB
        assert len(origin.bundle.files) == len(expected_materials) == 10
        for file in origin.bundle.files:
            original = expected_materials[file.name]
            assert file.path == str(target / (file.name + ".json"))
            assert (file.sha256, file.byte_count) == (digest(original), len(original))
            assert Path(file.path).read_bytes() == original
        assert origin.bundle.diagnostic_attempt_id == diagnostic_request.attempt_id
        retained_journal = (f.root / "candidate-journal-13").read_bytes()
        assert (origin.bundle.journal_sha256, origin.bundle.journal_bytes) == (
            digest(retained_journal),
            len(retained_journal),
        )
        assert (target / "journal.sqlite3").read_bytes() == retained_journal
        original_build = (f.root / "candidate-installation.json").read_bytes()
        assert (origin.bundle.installation_raw_sha256, origin.bundle.installation_bytes) == (
            digest(original_build),
            len(original_build),
        )
        assert (target / "installation.json").read_bytes() == original_build
        source_database_hash = digest((f.root / "candidate.sqlite3").read_bytes())
        sealed_ledger_raw = raw(current(f.root))
        assert sealed_ledger_raw == raw(handed.ledger)
        assert not (target / "publication.sqlite3").exists()
        publication_request = NativePublicationRequest(
            mode="scored",
            event_id="publish-original-comparison",
            cell_id=cell.cell_id,
            attempt_id="publish-0",
            ticket=0,
            expected_revision=len(handed.ledger.records),
            expected_head_sha256=head(handed.ledger),
            journal_path=str(target / "journal.sqlite3"),
            journal_sha256=origin.bundle.journal_sha256,
            files=origin.bundle.files,
            diagnostic_attempt_id=origin.bundle.diagnostic_attempt_id,
            cpu_reservation_ns=30_000_000_000,
            artifact_reservation_bytes=23_592_960,
            output_limit_bytes=2 * MIB,
            wall_limit_ns=30_000_000_000,
        )

    publisher_children = 0
    target_verifications: list[str] = []
    compose_child = publisher._run_child
    verify_installation = activation.verify_native_installation

    def tracked_target_verification(build: TrustedInstallation) -> Any:
        ticket = len(target_verifications)
        assert ticket in {0, 1}
        assert (target / f"ticket-{ticket}").is_file()
        assert raw(build) == original_build
        target_verifications.append(message_sha256(build))
        return verify_installation(build)

    def tracked_publication_child(*args: Any, **kwargs: Any) -> Any:
        nonlocal publisher_children
        publisher_children += 1
        return compose_child(*args, **kwargs)

    monkeypatch.setattr(publisher, "_run_child", tracked_publication_child)
    monkeypatch.setattr(activation, "verify_native_installation", tracked_target_verification)
    published = invoke(publisher.commit_native_publication, target, publication_request)
    with f.budget.phase():
        assert not published.replayed
        assert len(published.ledger.records) == 91
        assert published.ledger.records[:88] == handed.ledger.records
        evidence = parse_study_publication_evidence(published.evidence_raw)
        assert raw(evidence.native.score) == score.result_raw
        assert evidence.native.observation_sha256 == message_sha256(observations)
        assert evidence.diagnostic_input_sha256 == message_sha256(diagnostic_input.diagnostic)
        assert evidence.diagnostic_attempt is not None
        assert evidence.diagnostic_attempt.reservation.attempt_id == diagnostic_request.attempt_id
        assert evidence.diagnostic_result is not None
        assert raw(evidence.diagnostic_result) == raw(diagnostic.result)
        assert evidence.outcome.status == "complete" and evidence.outcome.reason == "scored"
        assert published.receipt.original_revision == 89
        assert summarize_study(published.ledger).budget.unresolved_attempts == 3
        # Preserve sealed source/target authority and durable trusted artifacts.
        # Only disposable original inputs/live scientific exports are removed.
        disposable = (
            {
                Path(request.input_path)
                for request in (
                    f.freeze_request,
                    *purchase_requests,
                    candidate_request,
                    preparation_request,
                    *prediction_requests,
                    score_request,
                    diagnostic_request,
                )
            }
            | {f.journal, target / "journal.sqlite3"}
            | {Path(file.path) for file in origin.bundle.files}
        )
        assert not disposable.intersection(trusted_paths)
        for path in disposable:
            assert path.is_file() and not path.is_symlink()
            path.unlink()
        for parent in {p.parent for p in disposable}:
            sync_directory(parent)
        replay_request = NativePublicationRequest.model_validate(
            publication_request.model_dump() | {"attempt_id": "publish-replay-1", "ticket": 1}
        )

    with monkeypatch.context() as replay_only:
        # Deterministic preparation and result binders remain active. The paid
        # publisher composition child validates and returns the original bytes.
        replay_only.setattr(activation, "read_sealed_handoff", forbidden)
        replay_only.setattr(supervisor, "_run_child", forbidden)
        replay_only.setattr(supervisor, "run_purchase_writer", forbidden)
        replay_only.setattr(purchase_producer, "simulate", forbidden)
        replay_only.setattr(native_candidates, "produce_native_candidates", forbidden)
        replay_only.setattr(native_prediction, "predict_native_spring", forbidden)
        replay_only.setattr(native_scoring, "score_native_predictions", forbidden)
        replay_only.setattr(native_classical, "run_classical_diagnostic", forbidden)
        replayed = invoke(publisher.commit_native_publication, target, replay_request)

    with f.budget.phase():
        assert replayed.replayed
        assert raw(replayed.receipt) == raw(published.receipt)
        assert replayed.evidence_raw == published.evidence_raw
        assert len(replayed.ledger.records) == 93
        assert replayed.ledger.records[:91] == published.ledger.records
        replay_reservation, replay_update = (r.event for r in replayed.ledger.records[-2:])
        assert isinstance(replay_reservation, StudyAttemptReservation)
        assert isinstance(replay_update, StudyAttemptUpdate)
        assert replay_reservation.attempt_id == replay_update.attempt_id == "publish-replay-1"
        assert replay_update.state == "completed"
        assert summarize_study(replayed.ledger).budget.unresolved_attempts == 3
        assert digest((f.root / "candidate.sqlite3").read_bytes()) == source_database_hash
        assert raw(current(f.root)) == sealed_ledger_raw
        assert all(
            digest(Path(p).read_bytes()) == expected for p, expected in trusted_hashes.items()
        )
        assert all(not p.exists() for p in disposable)
        assert len(public_entries) == len(public_returns) == 44
        assert [ticket for _, ticket in public_entries] == [*range(42), 0, 1]
        assert counts == {"writer": 12, "holder": 12, "other_child": 28}
        assert publisher_children == 2
        assert target_verifications == [message_sha256(actual_build)] * 2
        assert not (f.root / "candidate-ticket-42").exists()
        assert not (target / "ticket-2").exists()
        ordinary = [
            f.freeze_request,
            *purchase_requests,
            candidate_request,
            preparation_request,
            *prediction_requests,
            score_request,
            diagnostic_request,
        ]
        assert len(ordinary) == 41
        assert sum(r.artifact_reservation_bytes for r in ordinary) == 140 * MIB
        assert sum(r.cpu_reservation_ns for r in ordinary) == 704_000_000_000
        assert (
            SETUP_LIMIT
            + f.control.required_control_bytes()
            + sum(r.artifact_reservation_bytes for r in ordinary)
            + transfer_request.artifact_reservation_bytes
            + f.control.recovery_work_artifact_bytes
            + f.control.publication.required_bytes()
        ) == DECLARED_BYTES
        assert (
            setup.cpu_reservation_ns
            + control.cpu_reservation_ns
            + sum(r.cpu_reservation_ns for r in ordinary)
            + transfer_request.cpu_reservation_ns
            + f.control.recovery_work_cpu_ns
            + f.control.publication.control_cpu_ns
            + f.control.publication.work_cpu_ns
        ) == DECLARED_CPU_NS
        proof = {
            "scope": "Bounded synthetic conformance; no accuracy/MAP/study claim.",
            "public_entries": public_entries,
            "public_returns": public_returns,
            "source_calls": 42,
            "publisher_calls": 2,
            "source_entry_counts": counts,
            "publisher_composition_children": publisher_children,
            "fresh_target_verification_identities": target_verifications,
            "counter_qualification": "Python entry counters, not independent OS process census.",
            "precharged_journal_epochs": sum(e.used for e in epochs),
            "source_scientific_records": 85,
            "sealed_seed_records": 88,
            "publication_records": len(published.ledger.records),
            "final_records": len(replayed.ledger.records),
            "unresolved_holds": 3,
            "declared_artifact_bytes": DECLARED_BYTES,
            "declared_cpu_ns": DECLARED_CPU_NS,
            "setup_export_ceiling_bytes": SETUP_EXPORT_CEILING,
            "setup_copies_before_proof": f.budget.copies,
            "setup_parent_cpu_before_proof_ns": f.budget.parent_cpu,
            "setup_final_tail": "Proof-write CPU follows serialized snapshot; setup hold retained.",
            "source_seal": origin.seal.model_dump(mode="json"),
            "handoff_bundle": origin.bundle.model_dump(mode="json"),
            "original_diagnostic_selection": None,
            "source_database_sha256": source_database_hash,
            "source_ledger_sha256": digest(sealed_ledger_raw),
            "publication_evidence_sha256": digest(published.evidence_raw),
            "publication_receipt_sha256": digest(raw(published.receipt)),
            "durable_trusted_artifacts": trusted_hashes,
            "handoff_measurements": handed.measurements.model_dump(mode="json"),
            "publication_measurements": published.measurements.model_dump(mode="json"),
            "replay_measurements": replayed.measurements.model_dump(mode="json"),
            "remaining_budget": summarize_study(replayed.ledger).budget.model_dump(mode="json"),
        }
        proof_raw = json.dumps(proof, sort_keys=True).encode()
        assert len(proof_raw) <= 64 * 1024
        f.budget.write(tmp_path / "handoff-call-proof.json", proof_raw)
        assert f.budget.copies <= SETUP_EXPORT_CEILING <= SETUP_LIMIT
