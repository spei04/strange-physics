"""Synthetic retained SQLite/ticket conformance; no measured or numerical calls.

These fixtures install typed rows and facts directly. They prove resolver joins
and temporal transport rules, not a purchased-history or measurement boundary.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest
from test_comparison_stage_binding import failed_prediction, fixture, preparation
from test_study_ledger import LOCK, append, empty, reserve

from strange_physics import comparison_stage_resolver as retained
from strange_physics import measured_candidates as measured
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.comparison_stage_binding import comparison_prediction_input
from strange_physics.comparison_stage_resolver import (
    RetainedStageWitness,
    _before_feedback,
    _Resolver,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    NativePredictionResult,
)
from strange_physics.native_scoring_contracts import NativePreparationResult, NativeProbeOutcome
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPredictionInput,
    NativePredictionReference,
    NativePredictionRequest,
    NativeStageReceipt,
)
from strange_physics.publication_store import Extents, digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorkFacts,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_ledger import (
    StudyLedgerError,
    freeze_native_study,
    study_manifest,
    summarize_study,
)


@pytest.fixture(autouse=True)
def no_measured_or_numerical_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Resolver tests use synthetic retained evidence only")

    for name in (
        "strange_physics.measured_candidates._run_child",
        "strange_physics.measured_candidates._commit_native_execution",
        "strange_physics.simulation.simulate",
        "strange_physics.measured_candidates.produce_native_candidates",
        "strange_physics.native_stage_dispatch.predict_native_spring",
        "strange_physics.native_stage_dispatch.score_native_predictions",
        "strange_physics.native_scoring.evaluate_spring_predictions",
    ):
        monkeypatch.setattr(name, forbidden)


@dataclass
class Evidence:
    store: CandidateStore
    resolver: _Resolver
    request: NativePredictionRequest
    reference: NativePredictionReference
    actual: NativePredictionInput
    result: NativePredictionResult
    prepared: NativePreparationResult
    original: NativeStudyLedger
    ledger: NativeStudyLedger
    receipt: NativeStageReceipt
    output: Path

    def resolve(self, *, historical: bool = False) -> NativeProbeOutcome:
        return self.resolver.prediction(
            self.reference,
            preparation_logical_id="prepare",
            preparation_receipt_sha256="a" * 64,
            expected=self.actual,
            preparation=self.prepared,
            probe_index=0,
            historical_transport=historical,
        )


def private(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    path.chmod(0o600)


@contextmanager
def evidence(
    root: Path,
    *,
    status: Literal["result", "missing", "invalid"] = "result",
    closure: bool = True,
    state: Literal["failed", "unknown"] = "failed",
) -> Iterator[Evidence]:
    root.mkdir(mode=0o700)
    context, freeze, cell = fixture()
    prepared = preparation(context)
    actual = comparison_prediction_input(
        context, prepared, preparation_attempt_id="prepare", probe_index=0
    )
    material = NativeComparisonPredictionInput(
        preparation_logical_id="prepare",
        preparation_receipt_sha256="a" * 64,
        probe_index=0,
        prediction=actual,
    )
    data = raw(material)
    before = freeze_native_study(
        empty(),
        event_id="freeze",
        manifest=freeze.manifest,
        expected_revision=0,
        expected_purpose="synthetic_validation",
        source_commit=freeze.manifest.source_commit,
        uv_lock_bytes=LOCK,
        engine_fingerprint=freeze.manifest.engine_fingerprint,
        artifacts={key: value.encode() for key, value in freeze.artifacts.items()},
    )
    request = NativePredictionRequest(
        mode="execute",
        logical_id="prediction-0",
        attempt_id="predict-0",
        retry_of=None,
        phase="comparison",
        cell_id=cell,
        ticket=0,
        expected_revision=len(before.records),
        expected_head_sha256=head(before),
        input_path=str(root / "never-consulted-input"),
        input_raw_sha256=digest(data),
        input_bytes=len(data),
        input_sha256=message_sha256(actual),
        config_sha256=message_sha256(actual.config),
        cpu_reservation_ns=12_000_000_000,
        artifact_reservation_bytes=MIB,
        output_limit_bytes=512 * 1024,
        wall_limit_ns=30_000_000_000,
    )
    reservation = StudyAttemptReservation(
        attempt_id=request.attempt_id,
        phase="comparison",
        cell_id=cell,
        operation="prediction",
        config_sha256=request.config_sha256,
        input_sha256=request.input_sha256,
        retry_of=None,
        cpu_reservation_ns=request.cpu_reservation_ns,
        artifact_reservation_bytes=request.artifact_reservation_bytes,
        purchase=None,
    )
    original = append(before, reservation)
    result = failed_prediction(actual, request.attempt_id)
    ledger = append(
        original,
        StudyAttemptUpdate(
            attempt_id=request.attempt_id,
            state=state,
            cpu_ns=1,
            wall_ns=2,
            artifact_bytes=3,
            facts=NativeWorkFacts.model_validate_json(result.facts.model_dump_json())
            if closure or state == "failed"
            else None,
        ),
    )
    receipt = NativeStageReceipt(
        operation="prediction",
        logical_id=request.logical_id,
        original_attempt_id=request.attempt_id,
        request_sha256=measured._identity(request),
        original_revision=len(original.records),
        original_head_sha256=head(original),
        original_ledger_sha256=digest(raw(original)),
        input_raw_sha256=digest(data),
        result_raw_sha256=digest(raw(result)),
        source_commit=freeze.manifest.source_commit,
        installation_sha256="b" * 64,
    )
    control = CandidateControl(
        root=str(root),
        plan_sha256=message_sha256(ledger.plan),
        source_commit=freeze.manifest.source_commit,
        uv_lock_sha256=freeze.manifest.uv_lock_sha256,
        engine_fingerprint=freeze.manifest.engine_fingerprint,
        installation_sha256="b" * 64,
        attempt_id="synthetic-control",
        tickets=6,
        recovery_tickets=2,
        recovery_work_cpu_ns=8_000_000_000,
        recovery_work_artifact_bytes=2 * MIB,
        ticket_cpu_ns=5_000_000_000,
        ticket_wall_ns=30_000_000_000,
        ticket_artifact_bytes=8192,
        bootstrap_artifact_bytes=4 * MIB,
        bootstrap_cpu_ns=5_000_000_000,
        database_limit_bytes=MIB,
        finalization_records=6,
        finalization_bytes=32 * 1024,
        publication=PublicationEscrow(
            calls=0,
            material_bytes=0,
            journal_bytes=0,
            ledger_bytes=8 * MIB,
            output_bytes=64 * 1024,
            control_cpu_ns=0,
            control_artifact_bytes=0,
            work_cpu_ns=0,
        ),
    )
    admission = CandidateAdmission(control=control, seed_ledger_sha256=digest(raw(ledger)))
    meter = Extents(root, database_name="candidate.sqlite3")
    with ExitStack() as scope:
        store = CandidateStore(root, admission, raw(ledger), meter)
        scope.callback(store.close)
        private(root / "candidate-ticket-0", raw(request))
        private(root / "candidate-input-0", data)
        output = root / "candidate-output-0"
        if status == "result":
            private(output, raw(result))
        elif status == "invalid":
            private(output, b"{")
        reference = NativePredictionReference(
            logical_id=request.logical_id,
            attempt_id=request.attempt_id,
            ticket=request.ticket,
            request_raw_sha256=digest(raw(request)),
            status=status,
            receipt_sha256=digest(raw(receipt)) if status == "result" else None,
            output_raw_sha256=digest(output.read_bytes()) if status != "missing" else None,
        )
        if closure:
            with store.transaction():
                store.db.execute(
                    "INSERT INTO closures VALUES(?,?,?,?,?,?,?)",
                    (
                        request.logical_id,
                        measured._identity(request),
                        raw(request),
                        "candidate-input-0",
                        "candidate-output-0",
                        raw(receipt),
                        digest(raw(receipt)),
                    ),
                )
        yield Evidence(
            store,
            _Resolver(store, ledger, cell, meter, scope),
            request,
            reference,
            actual,
            result,
            prepared,
            original,
            ledger,
            receipt,
            output,
        )


def test_closed_failed_result_is_result_and_never_downgraded(tmp_path: Path) -> None:
    with evidence(tmp_path / "store") as e:
        assert e.resolve().result == e.result
        assert e.resolve().status == "result"
        assert e.result.facts.outcome == "failed"
        for status in ("missing", "invalid"):
            e.reference = NativePredictionReference.model_validate(
                e.reference.model_dump()
                | {
                    "status": status,
                    "receipt_sha256": None,
                    "output_raw_sha256": None if status == "missing" else digest(raw(e.result)),
                }
            )
            with pytest.raises(StudyLedgerError, match="comparison_prediction_transport"):
                e.resolve()


@pytest.mark.parametrize("status", ["missing", "invalid"])
def test_unknown_transport_preserves_hold_and_rechecks_raw_witness(
    tmp_path: Path,
    status: Literal["missing", "invalid"],
) -> None:
    with evidence(tmp_path / "store", status=status, closure=False, state="unknown") as e:
        before = summarize_study(e.ledger).budget
        assert e.resolve().status == status
        e.resolver.witness.recheck()
        assert summarize_study(e.store.ledger()).budget == before
        assert before.unresolved_attempts == 1
        private(e.output, b"}")
        with pytest.raises(StudyLedgerError, match="comparison_retained_changed"):
            e.resolver.witness.recheck()


def test_valid_unclosed_result_is_not_invalid_transport(tmp_path: Path) -> None:
    with evidence(tmp_path / "store", closure=False, state="unknown") as e:
        e.reference = NativePredictionReference.model_validate(
            e.reference.model_dump() | {"status": "invalid", "receipt_sha256": None}
        )
        with pytest.raises(StudyLedgerError, match="comparison_prediction_unclosed_result"):
            e.resolve()


def test_bound_input_mismatch_is_invalid_only_without_a_closure(tmp_path: Path) -> None:
    with evidence(tmp_path / "store", closure=False, state="unknown") as e:
        other = failed_prediction(e.actual, "foreign-attempt")
        private(e.output, raw(other))
        e.reference = NativePredictionReference.model_validate(
            e.reference.model_dump()
            | {
                "status": "invalid",
                "receipt_sha256": None,
                "output_raw_sha256": digest(raw(other)),
            }
        )
        assert e.resolve().status == "invalid"


def test_closed_unknown_or_lost_output_is_not_authoritative_result(tmp_path: Path) -> None:
    with evidence(tmp_path / "unknown", state="unknown") as e:
        with pytest.raises(StudyLedgerError, match="comparison_parent_unknown"):
            e.resolve()
    with evidence(tmp_path / "lost") as e:
        e.output.unlink()
        with pytest.raises(FileNotFoundError):
            e.resolve()


@pytest.mark.parametrize("change", ["attempt", "raw", "probe", "reservation", "source", "install"])
def test_actual_ticket_original_reservation_and_receipt_joins(
    tmp_path: Path,
    change: str,
) -> None:
    with evidence(tmp_path / "store") as e:
        assert e.resolve().result == e.result
        e.resolver.witness = RetainedStageWitness()
        if change == "attempt":
            e.reference = e.reference.model_copy(update={"attempt_id": "foreign"})
        elif change == "raw":
            private(e.store.root / "candidate-ticket-0", raw(e.request) + b" ")
        elif change == "probe":
            value = NativeComparisonPredictionInput.model_validate_json(
                (e.store.root / "candidate-input-0").read_bytes()
            ).model_copy(update={"probe_index": 1})
            private(e.store.root / "candidate-input-0", raw(value))
        elif change == "reservation":
            e.resolver.view = NativeStudyLedger(plan=e.ledger.plan, records=e.ledger.records[:1])
        else:
            changed = e.receipt.model_copy(
                update={
                    "source_commit" if change == "source" else "installation_sha256": "c"
                    * (40 if change == "source" else 64)
                }
            )
            e.store.db.execute(
                "UPDATE closures SET receipt=?,receipt_digest=? WHERE logical_id=?",
                (raw(changed), digest(raw(changed)), e.request.logical_id),
            )
            e.reference = e.reference.model_copy(update={"receipt_sha256": digest(raw(changed))})
        error = {
            "attempt": "comparison_prediction_ticket",
            "raw": "comparison_prediction_ticket",
            "probe": "comparison_prediction_input",
            "reservation": "comparison_prediction_reservation",
            "source": "comparison_parent_identity",
            "install": "comparison_parent_identity",
        }[change]
        with pytest.raises(StudyLedgerError, match=error):
            e.resolve()


@pytest.mark.parametrize("status", ["missing", "invalid"])
def test_historical_transport_does_not_read_a_later_retry_closure(
    tmp_path: Path,
    status: Literal["missing", "invalid"],
) -> None:
    with evidence(tmp_path / "store", status=status, closure=False, state="unknown") as e:
        original = e.resolve()
        # Synthetic row-adapter temporal test: a later logical closure is outside
        # the supplied historical prefix. Its content is deliberately unreadable,
        # proving the historical unavailable branch does not consult it.
        e.store.db.execute(
            "INSERT INTO closures VALUES(?,?,?,?,?,?,?)",
            (e.request.logical_id, "later", b"later", "later", "later", b"later", "later"),
        )
        if status == "missing":
            private(e.output, raw(e.result))
        replay_resolver = _Resolver(
            e.store, e.ledger, e.resolver.cell_id, e.resolver.meter, e.resolver.scope
        )
        e.resolver = replay_resolver
        assert e.resolve(historical=True) == original
        e.resolver.witness.recheck()
        with pytest.raises(StudyLedgerError, match="comparison_prediction_transport"):
            e.resolve()
        if status == "invalid":
            e.output.unlink()
            with pytest.raises(StudyLedgerError, match="comparison_prediction_transport"):
                e.resolve(historical=True)


def test_selection_is_fixed_before_any_possible_evaluator_feedback(tmp_path: Path) -> None:
    with evidence(tmp_path / "store") as e:
        _before_feedback(e.ledger, e.resolver.cell_id)
        scoring = reserve(
            "score",
            phase="comparison",
            cell_id=e.resolver.cell_id,
            operation="scoring",
            config_sha256=e.store.admission.control.plan_sha256,
        )
        # Admission validates role identity. Use the actual frozen policy digest.
        scoring = scoring.model_copy(
            update={"config_sha256": study_manifest(e.ledger).artifact("scoring_policy").sha256}
        )
        later = append(e.ledger, scoring)
        with pytest.raises(StudyLedgerError, match="comparison_selection_after_feedback"):
            _before_feedback(later, e.resolver.cell_id)
        _before_feedback(e.ledger, e.resolver.cell_id)


def test_comparison_unwrap_keeps_existing_plain_stage_parsing() -> None:
    from test_comparison_stage_binding import references, scoring_fixture

    from strange_physics.native_stage_dispatch import parse_stage_input
    from strange_physics.native_stage_execution_contracts import (
        NativeComparisonPreparationInput,
        NativeComparisonScoreInput,
    )

    scoring, _, _ = scoring_fixture()
    prepared = scoring.preparation
    predicted = comparison_prediction_input(
        scoring.context, prepared, preparation_attempt_id="prepare", probe_index=0
    )
    prep = NativeComparisonPreparationInput(
        candidate_logical_id="candidate",
        candidate_receipt_sha256="c" * 64,
        context=scoring.context,
    )
    prediction = NativeComparisonPredictionInput(
        preparation_logical_id="prepare",
        preparation_receipt_sha256="a" * 64,
        probe_index=0,
        prediction=predicted,
    )
    score = NativeComparisonScoreInput(
        preparation_logical_id="prepare",
        preparation_receipt_sha256="a" * 64,
        predictions=references(scoring),
        scoring=scoring,
    )
    assert parse_stage_input("preparation", raw(prep), comparison=True) == scoring.context
    assert parse_stage_input("prediction", raw(prediction), comparison=True) == predicted
    assert parse_stage_input("scoring", raw(score), comparison=True) == scoring
    assert parse_stage_input("preparation", raw(scoring.context)) == scoring.context
    assert parse_stage_input("prediction", raw(predicted)) == predicted
    assert parse_stage_input("scoring", raw(scoring)) == scoring
    with pytest.raises(ValueError):
        parse_stage_input("preparation", raw(prep))
    with pytest.raises(ValueError):
        parse_stage_input("scoring", raw(prediction), comparison=True)


def test_manifest_reused_only_for_the_same_validated_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[NativeStudyLedger] = []
    original = study_manifest

    def counted(view: NativeStudyLedger) -> NativeStudyManifest:
        calls.append(view)
        return original(view)

    monkeypatch.setattr(retained, "study_manifest", counted)
    with evidence(tmp_path / "store") as e:
        assert e.resolve().result == e.result
        assert e.resolve().result == e.result
        assert len(calls) == 1
        # A different, valid historical view must undergo its own semantic scan.
        e.resolver.view = NativeStudyLedger(plan=e.ledger.plan, records=e.ledger.records[:1])
        assert e.resolver.manifest() == original(e.ledger)
        assert len(calls) == 2
        e.resolver.view = NativeStudyLedger(plan=e.ledger.plan)
        with pytest.raises(StudyLedgerError, match="manifest_missing"):
            e.resolver.manifest()
        assert len(calls) == 3
        # Failure cannot leave the previous manifest authoritative for this view.
        with pytest.raises(StudyLedgerError, match="manifest_missing"):
            e.resolver.manifest()
        assert len(calls) == 4
        e.resolver.view = e.ledger
        assert e.resolve().result == e.result
        assert len(calls) == 5


def test_replaced_view_revalidates_the_full_hash_chain(tmp_path: Path) -> None:
    with evidence(tmp_path / "store") as e:
        assert e.resolve().result == e.result
        bad = e.ledger.records[0].model_copy(update={"previous_sha256": "f" * 64})
        # Deliberately bypass validation only in adversarial synthetic input.
        e.resolver.view = e.ledger.model_copy(update={"records": (bad, *e.ledger.records[1:])})
        with pytest.raises(ValueError, match="canonical hash chain is broken"):
            e.resolve()


def test_validated_prefix_heads_preserve_empty_normal_and_historical_identity(
    tmp_path: Path,
) -> None:
    with evidence(tmp_path / "store") as e:
        for length in range(len(e.ledger.records)):
            prefix = NativeStudyLedger(plan=e.ledger.plan, records=e.ledger.records[:length])
            assert e.ledger.records[length].previous_sha256 == head(prefix)
        assert e.ledger.records[0].previous_sha256 == message_sha256(e.ledger.plan)
        assert e.ledger.records[e.request.expected_revision].previous_sha256 == (
            e.request.expected_head_sha256
        )
        # The same original receipt/prefix survives a later unrelated reservation.
        original = measured._closure(e.store, e.request, e.ledger)
        assert original is not None and original[3] == e.original
        later = append(e.ledger, reserve("later-reference"))
        replay = measured._closure(e.store, e.request, later)
        assert replay == original
        wrong_head = e.request.model_copy(update={"expected_head_sha256": "f" * 64})
        private(e.store.root / "candidate-ticket-0", raw(wrong_head))
        e.store.db.execute(
            "UPDATE closures SET request=? WHERE logical_id=?",
            (raw(wrong_head), e.request.logical_id),
        )
        with pytest.raises(StudyLedgerError, match="candidate_closure_corrupt"):
            measured._closure(e.store, wrong_head, later)


def test_original_receipt_ledger_digest_is_still_checked(tmp_path: Path) -> None:
    with evidence(tmp_path / "store") as e:
        assert e.resolve().result == e.result
        changed = e.receipt.model_copy(update={"original_ledger_sha256": "f" * 64})
        e.store.db.execute(
            "UPDATE closures SET receipt=?,receipt_digest=? WHERE logical_id=?",
            (raw(changed), digest(raw(changed)), e.request.logical_id),
        )
        e.reference = e.reference.model_copy(update={"receipt_sha256": digest(raw(changed))})
        with pytest.raises(StudyLedgerError, match="candidate_closure_corrupt"):
            e.resolve()
