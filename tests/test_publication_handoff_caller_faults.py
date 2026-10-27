"""Four real handoff calls with synthetic ancestry; no scientific producers.

Two independent synthetic validation studies exercise caller settlement, protected
retry and a lost seal acknowledgement. They are not copies of an admitted study.
Only ancestry resolution is replaced: typed 11+1 observations and rejected/missing
stage material are supplied, and the "Journal" capture is explicitly an opaque
ObservationBundle document. No authentic Journal, scientific closure, publisher
activation, model accuracy or power-loss guarantee is established here.

The existing V2 limits are unchanged. Each source has 43 tickets (42 normal,
one protected recovery), a 1 MiB DB and the original setup/control holds. Four DB
envelopes plus 6 MiB are 15,212,544 B per control ticket, not 6 MiB. The actual_build
session fixture is separate trusted-harness preparation (one Git subprocess,
no product child); its original three durable files must fit 6 MiB. A bounded
runner must cover that setup before these tests execute. No extra calls belong
to the independently declared 44-call scientific specimen.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pytest
from test_comparison_stage_binding import fixture as synthetic_context
from test_measured_candidates import actual_build as actual_build
from test_native_spring_contracts import synthetic_result
from test_study_ledger import append, reserve

import strange_physics.candidate_store as store_module
import strange_physics.execution_publication_handoff as handoff
from strange_physics import measured_candidates as measured
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore, read_sealed_handoff
from strange_physics.comparison_stage_resolver import BoundRetainedStage, RetainedStageWitness
from strange_physics.contracts import ObservationBundle
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_publication_contracts import PublicationControl
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
    ClassicalDiagnosticOutcome,
    ClassicalDiagnosticResult,
)
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativePreparationOutcome,
    NativePreparationResult,
    NativeProbeOutcome,
    NativeScoreOutcome,
    NativeScoreResult,
    NativeScoringInput,
)
from strange_physics.native_spring_contracts import NativeCandidateInput, NativeWorkFacts
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonScoreInput,
    NativePredictionReference,
    NativeScoreRequest,
)
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.publication_handoff_contracts import (
    HANDOFF_MATERIAL_NAMES,
    HandoffReference,
    PublicationHandoffIntent,
    PublicationHandoffRequest,
    PublicationHandoffSeal,
)
from strange_physics.publication_store import Extents, digest, head, raw, root_lock
from strange_physics.publication_store import durable_directory as real_durable_directory
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    ArtifactKind,
    NativeAccountingPlan,
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorldCatalog,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalInput,
    NativeComparisonClassicalRequest,
    NativeComparisonInput,
    NativeFreezeInput,
)
from strange_physics.study_ledger import (
    StudyLedgerError,
    freeze_native_study,
    read_study_ledger,
    summarize_study,
)

NS = 1_000_000_000


@dataclass
class SetupCopies:
    """Precharge every fixture write, including a conservative DB creation allowance."""

    used: int = 0

    def charge(self, size: int) -> None:
        assert 0 <= size <= 48 * MIB - self.used
        self.used += size

    def write(self, path: Path, value: bytes) -> None:
        assert not path.exists()
        self.charge(len(value))
        with path.open("xb") as stream:
            path.chmod(0o600)
            stream.write(value)


@dataclass(frozen=True)
class SuppliedParent:
    """A typed request and input, deliberately not an authenticated store closure."""

    request: (
        NativeScoreRequest | NativeComparisonClassicalRequest | NativeComparisonCandidateRequest
    )
    actual: NativeScoringInput | ClassicalDiagnosticInput | NativeCandidateInput
    input_raw: bytes
    original: NativeStudyLedger


@dataclass(frozen=True)
class SuppliedCapture:
    path: Path
    byte_count: int
    sha256: str
    witness: RetainedStageWitness

    def recheck(self) -> None:
        self.witness.recheck()


@dataclass
class Case:
    root: Path
    target: Path
    seed: NativeStudyLedger
    admission: CandidateAdmission
    intent: PublicationHandoffIntent
    scoring: NativeScoringInput
    freeze: NativeFreezeInput
    capture: SuppliedCapture
    parents: dict[str, SuppliedParent]
    outputs: dict[str, bytes]
    fail_material_once: bool = False
    calls: list[int] = field(default_factory=list)

    def ledger(self) -> NativeStudyLedger:
        with root_lock(self.root):
            path = self.root / "candidate.sqlite3"
            db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                db.execute("PRAGMA query_only=ON")
                saved, value = db.execute(
                    "SELECT admission,ledger FROM state WHERE id=1"
                ).fetchone()
                assert saved == raw(self.admission)
                return read_study_ledger(value)
            finally:
                db.close()

    def request(
        self, ticket: int, attempt: str, *, recover: str | None = None
    ) -> PublicationHandoffRequest:
        current = self.ledger()
        return PublicationHandoffRequest(
            intent=self.intent,
            attempt_id=attempt,
            mode="execute" if recover is None else "recover",
            recover_attempt_id=recover,
            ticket=ticket,
            expected_revision=len(current.records),
            expected_head_sha256=head(current),
            cpu_reservation_ns=60 * NS,
            artifact_reservation_bytes=16 * MIB,
            wall_limit_ns=30 * NS,
        )

    def call(self, request: PublicationHandoffRequest) -> handoff.CommittedPublicationHandoff:
        self.calls.append(request.ticket)
        assert len(self.calls) <= 3
        return handoff.commit_publication_handoff(self.root, request)


def _rejected_facts(
    attempt: str,
    operation: Literal["preparation", "scoring", "classical_diagnostic"],
    producer: str,
    config: str,
    actual: str,
    observation: str,
    output: str,
) -> NativeWorkFacts:
    return NativeWorkFacts(
        attempt_id=attempt,
        operation=operation,
        producer_version=producer,
        config_sha256=config,
        input_sha256=actual,
        observation_sha256=observation,
        model_sha256=None,
        output_sha256=output,
        unit="preparation" if operation == "preparation" else "work",
        requested_count=1,
        completed_count=0,
        failed_count=0,
        not_assessed_count=1,
        outcome="rejected",
    )


def _material(
    build: TrustedInstallation, plan: NativeAccountingPlan
) -> tuple[NativeScoringInput, ClassicalDiagnosticInput, NativeFreezeInput, bytes, bytes]:
    # This helper builds contracts only. In particular, never call scoring_fixture(),
    # prepare_native_evaluation(), make_material() or the numerical joint fixture.
    initial, frozen, _ = synthetic_context()
    observations = ObservationBundle.model_validate_json(
        json.dumps(
            initial.candidates.observations.model_dump(mode="json")
            | {"engine_fingerprint": build.engine_fingerprint}
        )
    )
    candidate = NativeCandidateInput(
        pool=initial.candidates.pool, config=initial.candidates.config, observations=observations
    )
    candidate_result = synthetic_result(candidate)
    context = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=candidate_result,
        candidate_attempt_id=candidate_result.facts.attempt_id,
        selected=None,
        policy=initial.policy,
        prediction_config=initial.prediction_config,
    )
    observation = message_sha256(observations)
    policy = message_sha256(context.policy)
    prep_payload = NativePreparationOutcome(
        status="rejected",
        reason="selection_unavailable",
        input_sha256=message_sha256(context),
        policy_sha256=policy,
        observation_sha256=observation,
        model_sha256=None,
        protocol=None,
        protocol_sha256=None,
        overlap_probe_index=None,
        overlap_record_index=None,
    )
    prepared = NativePreparationResult(
        payload=prep_payload,
        facts=_rejected_facts(
            "synthetic-preparation",
            "preparation",
            context.policy.scorer_version,
            policy,
            message_sha256(context),
            observation,
            message_sha256(prep_payload),
        ),
    )
    predictions = NativePredictionCollection(
        entries=tuple(
            NativeProbeOutcome(
                probe_id=f"synthetic-probe-{i}",
                request_sha256=digest(f"probe-{i}".encode()),
                attempt_id=f"synthetic-prediction-{i}",
                status="missing",
                result=None,
            )
            for i in range(24)
        )
    )
    world = (
        NativeWorldCatalog.model_validate_json(frozen.artifacts["world_catalog"])
        .worlds[0]
        .definition
    )
    scoring = NativeScoringInput(
        context=context, preparation=prepared, predictions=predictions, world=world
    )
    config = ClassicalDiagnosticConfig(
        fit_config=SpringFitConfig(),
        prediction_config=SpringPredictionConfig(),
        scoring_policy=context.policy,
    )
    diagnostic = ClassicalDiagnosticInput(context=context, config=config, world=world)
    score_payload = NativeScoreOutcome(
        status="rejected",
        reason="preparation_rejected",
        input_sha256=message_sha256(scoring),
        policy_sha256=policy,
        observation_sha256=observation,
        model_sha256=None,
        preparation_sha256=message_sha256(prepared),
        predictions_sha256=message_sha256(predictions),
        submissions=None,
        evaluation=None,
    )
    score_result = NativeScoreResult(
        payload=score_payload,
        facts=_rejected_facts(
            "synthetic-score",
            "scoring",
            context.policy.scorer_version,
            policy,
            message_sha256(scoring),
            observation,
            message_sha256(score_payload),
        ),
    )
    # This is a supplied typed rejection, not an executed diagnostic or a claim
    # that the real binder would accept these synthetic parent/result assertions.
    diagnostic_payload = ClassicalDiagnosticOutcome(
        status="rejected",
        reason="candidate_mismatch",
        input_sha256=message_sha256(diagnostic),
        context_sha256=message_sha256(context),
        config_sha256=message_sha256(config),
        observation_sha256=observation,
        model_sha256=None,
        fit=None,
        protocol=None,
        predictions=(),
        prediction_not_assessed_count=24,
        submissions=None,
        evaluation=None,
        overlap_probe_index=None,
        overlap_record_index=None,
    )
    diagnostic_result = ClassicalDiagnosticResult(
        payload=diagnostic_payload,
        facts=_rejected_facts(
            "synthetic-diagnostic",
            "classical_diagnostic",
            config.producer_version,
            message_sha256(config),
            message_sha256(diagnostic),
            observation,
            message_sha256(diagnostic_payload),
        ),
    )
    artifacts = frozen.artifacts | {"classical_diagnostic_config": raw(config).decode()}
    manifest_data = frozen.manifest.model_dump(mode="json") | {
        "accounting_plan_sha256": message_sha256(plan),
        "source_commit": build.source_commit,
        "uv_lock_sha256": build.uv_lock_sha256,
        "engine_fingerprint": build.engine_fingerprint,
    }
    kinds: tuple[ArtifactKind, ...] = (
        *(
            ref.kind
            for ref in frozen.manifest.artifacts
            if ref.kind != "classical_diagnostic_config"
        ),
        "classical_diagnostic_config",
    )
    manifest_data["artifacts"] = [
        {
            "kind": name,
            "sha256": digest(artifacts[name].encode()),
            "byte_count": len(artifacts[name].encode()),
        }
        for name in kinds
    ]
    freeze = NativeFreezeInput(
        manifest=NativeStudyManifest.model_validate_json(json.dumps(manifest_data)),
        artifacts=artifacts,
    )
    # Explicit strict parsing, rather than model_construct or unchecked model_copy.
    scoring = NativeScoringInput.model_validate_json(raw(scoring))
    diagnostic = ClassicalDiagnosticInput.model_validate_json(raw(diagnostic))
    return scoring, diagnostic, freeze, raw(score_result), raw(diagnostic_result)


def _case(
    tmp_path: Path, build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch, study_id: str
) -> Case:
    root, target = tmp_path / "source", tmp_path / "publisher"
    root.mkdir(mode=0o700)
    target.mkdir(mode=0o700)
    durable = tuple(Path(p) for p in (build.lock_path, build.archive_path, build.provenance_path))
    assert sum(p.stat().st_size for p in durable) <= 6 * MIB
    plan = NativeAccountingPlan(
        study_id=study_id,
        purpose="synthetic_validation",
        approval_id="NATIVE_COMPARISON_APPROVAL_2026_10_21",
    )
    scoring, diagnostic, freeze, score_bytes, diagnostic_bytes = _material(build, plan)
    seed = NativeStudyLedger(plan=plan)
    seed = append(
        seed,
        reserve(
            "setup",
            phase="accounting",
            operation="accounting",
            cpu_reservation_ns=120 * NS,
            artifact_reservation_bytes=48 * MIB,
        ),
    )
    seed = freeze_native_study(
        seed,
        event_id="synthetic-freeze",
        manifest=freeze.manifest,
        expected_revision=len(seed.records),
        expected_purpose="synthetic_validation",
        source_commit=build.source_commit,
        uv_lock_bytes=Path(build.lock_path).read_bytes(),
        engine_fingerprint=build.engine_fingerprint,
        artifacts={name: value.encode() for name, value in freeze.artifacts.items()},
    )
    control = CandidateControl(
        root=str(root),
        plan_sha256=message_sha256(plan),
        source_commit=build.source_commit,
        uv_lock_sha256=build.uv_lock_sha256,
        engine_fingerprint=build.engine_fingerprint,
        installation_sha256=message_sha256(build),
        attempt_id="source-control",
        tickets=43,
        recovery_tickets=1,
        recovery_work_cpu_ns=60 * NS,
        recovery_work_artifact_bytes=16 * MIB,
        ticket_cpu_ns=7 * NS,
        ticket_wall_ns=30 * NS,
        ticket_artifact_bytes=6 * MIB,
        bootstrap_artifact_bytes=4 * MIB,
        bootstrap_cpu_ns=5 * NS,
        database_limit_bytes=MIB,
        finalization_records=16,
        finalization_bytes=64 * 1024,
        publication=PublicationEscrow(
            calls=3,
            material_bytes=2 * MIB,
            journal_bytes=128 * 1024,
            ledger_bytes=512 * 1024,
            output_bytes=2 * MIB,
            control_cpu_ns=16 * NS,
            control_artifact_bytes=64 * MIB,
            work_cpu_ns=90 * NS,
        ),
    )
    assert control.ticket_artifact_bytes + 4 * control.database_envelope() == 15_212_544
    seed = append(
        seed,
        reserve(
            control.attempt_id,
            phase="accounting",
            operation="accounting",
            config_sha256=message_sha256(control),
            input_sha256=control.plan_sha256,
            cpu_reservation_ns=control.bootstrap_cpu_ns + control.tickets * control.ticket_cpu_ns,
            artifact_reservation_bytes=control.required_control_bytes(),
        ),
    )
    admission = CandidateAdmission(control=control, seed_ledger_sha256=digest(raw(seed)))
    copies = SetupCopies()
    copies.write(root / "candidate-admission.json", raw(admission))
    copies.write(root / "candidate-seed.json", raw(seed))
    copies.write(root / "candidate-installation.json", raw(build))
    # Prepay the bootstrap's possible DB/journal writes, not merely its final size.
    copies.charge(4 * control.database_envelope())
    with root_lock(root):
        store = CandidateStore(
            root, admission, raw(seed), Extents(root, database_name="candidate.sqlite3")
        )
        store.close()
    assert (root / "candidate.sqlite3").stat().st_size <= MIB
    capture_raw = raw(scoring.context.candidates.observations)
    assert 100 <= len(capture_raw) <= 128 * 1024
    capture_path = root / "synthetic-observation-capture.json"
    copies.write(capture_path, capture_raw)
    witness = RetainedStageWitness()
    witness.remember(capture_path, capture_raw)
    capture = SuppliedCapture(capture_path, len(capture_raw), digest(capture_raw), witness)
    candidate_raw = raw(
        NativeComparisonInput(
            candidate=scoring.context.candidates,
            freeze_logical_id="synthetic-freeze",
            freeze_receipt_sha256="a" * 64,
            journal_path=str(capture_path),
            journal_sha256=digest(capture_raw),
            journal_bytes=len(capture_raw),
        )
    )
    score_raw = raw(
        NativeComparisonScoreInput(
            preparation_logical_id="synthetic-preparation",
            preparation_receipt_sha256="b" * 64,
            predictions=tuple(
                NativePredictionReference(
                    logical_id=f"synthetic-prediction-{i}",
                    attempt_id=entry.attempt_id,
                    ticket=i,
                    request_raw_sha256=digest(f"request-{i}".encode()),
                    status="missing",
                    receipt_sha256=None,
                    output_raw_sha256=None,
                )
                for i, entry in enumerate(scoring.predictions.entries)
            ),
            scoring=scoring,
        )
    )
    diagnostic_raw = raw(
        NativeComparisonClassicalInput(
            candidate_logical_id="synthetic-candidate",
            candidate_receipt_sha256="c" * 64,
            diagnostic=diagnostic,
        )
    )
    cell = freeze.manifest.cells[0].cell_id
    parents: dict[str, SuppliedParent] = {}
    for operation, request_type, ticket, actual, value, config_hash in (
        (
            "synthetic-candidate",
            NativeComparisonCandidateRequest,
            13,
            scoring.context.candidates,
            candidate_raw,
            message_sha256(scoring.context.candidates.config),
        ),
        (
            "synthetic-score",
            NativeScoreRequest,
            39,
            scoring,
            score_raw,
            message_sha256(scoring.context.policy),
        ),
        (
            "synthetic-diagnostic",
            NativeComparisonClassicalRequest,
            40,
            diagnostic,
            diagnostic_raw,
            message_sha256(diagnostic.config),
        ),
    ):
        input_path = root / f"{operation}.json"
        copies.write(input_path, value)
        request = request_type(
            mode="execute",
            logical_id=operation,
            attempt_id=operation,
            retry_of=None,
            phase="comparison",
            cell_id=cell,
            ticket=ticket,
            expected_revision=len(seed.records),
            expected_head_sha256=head(seed),
            input_path=str(input_path),
            input_raw_sha256=digest(value),
            input_bytes=len(value),
            input_sha256=message_sha256(actual),
            config_sha256=config_hash,
            cpu_reservation_ns=12 * NS,
            artifact_reservation_bytes=16 * MIB,
            output_limit_bytes=2 * MIB,
            wall_limit_ns=30 * NS,
        )
        parents[operation] = SuppliedParent(request, actual, value, seed)
    outputs = {"candidate-output-39": score_bytes, "candidate-output-40": diagnostic_bytes}
    for name, value in outputs.items():
        copies.write(root / name, value)
    # These are source test inputs, not additional output copies made by a producer.
    assert (
        sum(
            len(value.encode())
            for name, value in freeze.artifacts.items()
            if name in HANDOFF_MATERIAL_NAMES
        )
        + len(raw(scoring))
        + len(raw(diagnostic))
        + sum(map(len, outputs.values()))
        <= 2 * MIB
    )
    target_control = PublicationControl(
        root=str(target),
        accounting_plan_sha256=control.plan_sha256,
        source_commit=build.source_commit,
        uv_lock_sha256=build.uv_lock_sha256,
        attempt_id="publisher-control",
        tickets=3,
        ticket_cpu_ns=5 * NS,
        ticket_wall_ns=30 * NS,
        ticket_artifact_bytes=16 * MIB,
    )
    st = target.stat()
    intent = PublicationHandoffIntent(
        transfer_id="synthetic-transfer",
        source_admission_sha256=message_sha256(admission),
        cell_id=cell,
        scoring=HandoffReference(logical_id="synthetic-score", receipt_sha256="d" * 64),
        diagnostic=HandoffReference(logical_id="synthetic-diagnostic", receipt_sha256="e" * 64),
        destination=target_control,
        destination_device=st.st_dev,
        destination_inode=st.st_ino,
    )
    case = Case(root, target, seed, admission, intent, scoring, freeze, capture, parents, outputs)

    class SyntheticResolver:
        def __init__(
            self,
            store: CandidateStore,
            view: NativeStudyLedger,
            cell_id: str,
            meter: Extents,
            scope: ExitStack,
        ) -> None:
            assert store.root == root and cell_id == cell
            assert view.records[: len(seed.records)] == seed.records
            self.witness = RetainedStageWitness()

        def closed(self, logical_id: str, receipt_sha256: str, operation: str) -> SuppliedParent:
            expected = {
                "synthetic-score": ("d" * 64, "scoring"),
                "synthetic-diagnostic": ("e" * 64, "classical_diagnostic"),
                "synthetic-candidate": ("c" * 64, "comparison_candidate"),
            }
            assert expected[logical_id] == (receipt_sha256, operation)
            if case.fail_material_once:
                case.fail_material_once = False
                raise StudyLedgerError("injected_material_failure")
            return parents[logical_id]

    def bound(*args: object, **kwargs: object) -> BoundRetainedStage:
        return BoundRetainedStage(scoring, witness)

    def original_capture(*args: object, **kwargs: object) -> SuppliedCapture:
        return capture

    def original_freeze(*args: object, **kwargs: object) -> NativeFreezeInput:
        return freeze

    monkeypatch.setattr(handoff, "_Resolver", SyntheticResolver)
    monkeypatch.setattr(handoff, "bind_retained_stage", bound)
    monkeypatch.setattr(measured, "_bind_classical", original_capture)
    monkeypatch.setattr(measured, "_retained_freeze", original_freeze)
    return case


@pytest.fixture(autouse=True)
def no_numerical_or_child_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Caller-fault tests must not execute scientific work or product children")

    for name in (
        "strange_physics.simulation.simulate",
        "strange_physics.native_candidates.produce_native_candidates",
        "strange_physics.native_scoring.prepare_native_evaluation",
        "strange_physics.native_prediction.predict_native_spring",
        "strange_physics.native_scoring.score_native_predictions",
        "strange_physics.native_classical.run_classical_diagnostic",
        "strange_physics.measured_candidates._run_child",
        "strange_physics.measured_publication._run_child",
    ):
        monkeypatch.setattr(name, forbidden)


def test_public_unknown_requires_protected_retry_and_keeps_original_hold(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case(tmp_path, actual_build, monkeypatch, "caller-unknown")
    initial = raw(case.seed)
    first = case.request(0, "first-transfer")
    case.fail_material_once = True
    with pytest.raises(StudyLedgerError, match="^injected_material_failure$"):
        case.call(first)
    unknown = case.ledger()
    assert len(unknown.records) == len(case.seed.records) + 2
    assert raw(NativeStudyLedger(plan=unknown.plan, records=unknown.records[:-2])) == initial
    reservation, update = (row.event for row in unknown.records[-2:])
    assert isinstance(reservation, StudyAttemptReservation)
    assert reservation.attempt_id == first.attempt_id
    assert isinstance(update, StudyAttemptUpdate)
    assert update.state == "unknown" and update.facts is None
    assert (
        update.cpu_ns is not None
        and update.wall_ns is not None
        and update.artifact_bytes is not None
    )
    assert summarize_study(unknown).budget.unresolved_attempts == 3
    original_ticket = (case.root / "candidate-ticket-0").read_bytes()
    assert original_ticket == raw(first)
    assert list(case.target.iterdir()) == []

    # Use the correct current head: this must fail on recovery policy, not stale CAS.
    with pytest.raises(StudyLedgerError, match="^handoff_use_protected_recovery$"):
        case.call(case.request(1, "ordinary-retry"))
    assert raw(case.ledger()) == raw(unknown)
    assert (case.root / "candidate-ticket-1").is_file()

    recovered = case.call(case.request(42, "protected-transfer", recover=first.attempt_id))
    assert case.calls == [0, 1, 42]
    assert recovered.ledger.records[: len(unknown.records)] == unknown.records
    assert len(recovered.ledger.records) == len(case.seed.records) + 5
    assert summarize_study(recovered.ledger).budget.unresolved_attempts == 4
    assert (case.root / "candidate-ticket-0").read_bytes() == original_ticket
    assert recovered.measurements.child_cpu_ns == 0
    assert (
        sum(
            isinstance(r.event, StudyAttemptUpdate) and r.event.attempt_id == first.attempt_id
            for r in recovered.ledger.records
        )
        == 1
    )
    settled, publisher_hold = (row.event for row in recovered.ledger.records[-2:])
    assert isinstance(settled, StudyAttemptUpdate) and settled.state == "completed"
    assert isinstance(publisher_hold, StudyAttemptReservation)
    assert publisher_hold.attempt_id == "publisher-control"
    assert update.cpu_ns <= reservation.cpu_reservation_ns
    assert update.artifact_bytes <= reservation.artifact_reservation_bytes
    assert settled.cpu_ns is not None and settled.artifact_bytes is not None
    initial_budget = summarize_study(case.seed).budget
    final_budget = summarize_study(recovered.ledger).budget
    assert final_budget.charged_cpu_ns == (
        initial_budget.charged_cpu_ns
        + reservation.cpu_reservation_ns
        + settled.cpu_ns
        + publisher_hold.cpu_reservation_ns
    )
    assert final_budget.charged_artifact_bytes == (
        initial_budget.charged_artifact_bytes
        + reservation.artifact_reservation_bytes
        + settled.artifact_bytes
        + publisher_hold.artifact_reservation_bytes
    )
    assert (case.target / "scoring_input.json").read_bytes() == raw(case.scoring)
    assert (case.target / "diagnostic_input.json").read_bytes() == raw(
        case.parents["synthetic-diagnostic"].actual
    )
    assert (
        json.loads((case.target / "diagnostic_input.json").read_bytes())["context"]["selected"]
        is None
    )
    captured = json.loads((case.target / "journal.sqlite3").read_bytes())
    assert len(captured["records"]) == 12 and captured["records"][-1]["status"] == "failed"
    with root_lock(case.root):
        seal, sealed_raw = read_sealed_handoff(case.root, case.admission)
    assert seal == recovered.origin.seal and sealed_raw == raw(recovered.ledger)


def test_public_committed_seal_lost_ack_never_appends_unknown_fallback(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _case(tmp_path, actual_build, monkeypatch, "caller-lost-ack")
    seal_method = CandidateStore.seal
    durable_directory = real_durable_directory
    armed: list[CandidateStore] = []

    def arm_after_real_seal(
        store: CandidateStore,
        before: NativeStudyLedger,
        after: NativeStudyLedger,
        seal: PublicationHandoffSeal,
    ) -> None:
        seal_method(store, before, after, seal)
        armed.append(store)

    def lose_ack(path: Path) -> None:
        durable_directory(path)
        if armed:
            store = armed[-1]
            assert path == case.root and not store.db.in_transaction
            assert store.handoff() is not None
            raise OSError("injected_committed_seal_ack")

    monkeypatch.setattr(CandidateStore, "seal", arm_after_real_seal)
    monkeypatch.setattr(store_module, "durable_directory", lose_ack)
    request = case.request(0, "lost-ack-transfer")
    with pytest.raises(OSError) as failure:
        case.call(request)
    assert str(failure.value) == "injected_committed_seal_ack"
    assert case.calls == [0]
    assert len(armed) == 1
    assert any("already sealed" in note for note in getattr(failure.value, "__notes__", ()))
    with root_lock(case.root):
        seal, sealed_raw = read_sealed_handoff(case.root, case.admission)
    final = read_study_ledger(sealed_raw)
    assert len(final.records) == len(case.seed.records) + 3
    assert final.records[: len(case.seed.records)] == case.seed.records
    assert seal.transfer_attempt_id == request.attempt_id
    updates = [
        r.event
        for r in final.records
        if isinstance(r.event, StudyAttemptUpdate) and r.event.attempt_id == request.attempt_id
    ]
    assert len(updates) == 1 and updates[0].state == "completed" and updates[0].facts is not None
    assert summarize_study(final).budget.unresolved_attempts == 3
    assert (case.target / "seed-ledger.json").read_bytes() == sealed_raw
    assert (case.root / "candidate-ticket-0").read_bytes() == raw(request)
