"""Read actual available stages and propose a private early-stop event; no execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strange_physics.contracts import ObservationBundle
from strange_physics.native_classical import validate_classical_diagnostic_result
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    validate_native_prediction_result,
)
from strange_physics.native_scoring import validate_native_preparation_result
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativeScoringPolicy
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeCandidateResult,
    NativeSpringPool,
    NativeWorkFacts,
    SelectedNativeCandidate,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    MAX_STUDY_JSON_BYTES,
    NativeStudyLedger,
    NativeWorldCatalog,
    StudyAttemptUpdate,
    StudyCellOutcome,
)
from strange_physics.study_early_contracts import (
    EarlyCandidateWitness,
    EarlyDiagnosticWitness,
    EarlyPredictionWitness,
    EarlyPreparationWitness,
    EarlySelectionWitness,
    EarlyStage,
    StudyEarlyAttempt,
    StudyEarlyEvidence,
    StudyEarlyMaterial,
    StudyEarlyPurchaseRow,
    StudyEarlyWitnesses,
    parse_study_early_evidence,
    parse_study_early_witnesses,
)
from strange_physics.study_journal import StudyJournalReconciliation, reconcile_study_journal
from strange_physics.study_ledger import (
    FINAL,
    SELECTOR_ARTIFACTS,
    StudyAttemptSnapshot,
    StudyLedgerError,
    read_study_ledger,
    study_cell_attempts,
    study_manifest,
    study_purchase_intents,
    summarize_study,
)
from strange_physics.study_publication import MAX_PUBLICATION_INPUT_BYTES, _propose_publication
from strange_physics.study_publication_contracts import StudyPublicationReceipt
from strange_physics.study_scoring import NATIVE_MATERIAL_KINDS, _artifact, _identity
from strange_physics.workflow_io import private_stat, safe_path
from strange_physics.worlds import WorldDefinition


def _journal(
    ledger: NativeStudyLedger,
    path: Path,
    catalog: NativeWorldCatalog,
    cell_id: str,
) -> StudyJournalReconciliation | None:
    path = safe_path(path)
    try:
        path.stat()
    except FileNotFoundError:
        # Actual bounded local absence, never a caller readiness/absence flag.
        private_stat(path.parent.stat(), directory=True)
        return None
    return reconcile_study_journal(ledger, path, catalog=catalog, cell_id=cell_id)


class _Stages:
    """Bind the supplied stage graph against one actual ledger/Journal snapshot."""

    def __init__(
        self,
        prefix: ObservationBundle | None,
        pool: NativeSpringPool,
        candidate_config: NativeCandidateConfig,
        prediction_config: NativePredictionConfig,
        policy: NativeScoringPolicy,
        world: WorldDefinition,
        diagnostic_config: ClassicalDiagnosticConfig | None,
        snapshots: tuple[StudyAttemptSnapshot, ...],
    ) -> None:
        self.prefix, self.pool = prefix, pool
        self.candidate_config, self.prediction_config = candidate_config, prediction_config
        self.policy, self.world, self.diagnostic_config = policy, world, diagnostic_config
        self.attempts = {s.reservation.attempt_id: s for s in snapshots}
        self.bound: set[str] = set()
        self.historical: set[str] = set()
        self.candidates: dict[str, tuple[NativeCandidateInput, NativeCandidateResult]] = {}
        self.preparations: dict[str, EarlyPreparationWitness] = {}
        self.selections: dict[str, SelectedNativeCandidate] = {}
        self.predictions: dict[str, list[EarlyPredictionWitness]] = {}

    def attempt(
        self,
        identity: str,
        operation: str,
        input_sha: str,
        config_sha: str,
        facts: NativeWorkFacts | None,
    ) -> None:
        item = self.attempts.get(identity)
        if item is None:
            raise StudyLedgerError("early_attempt_missing")
        r = item.reservation
        if (r.operation, r.input_sha256, r.config_sha256) != (operation, input_sha, config_sha):
            raise StudyLedgerError("early_attempt_mismatch")
        if facts is not None:
            u = item.latest_update
            if item.state not in FINAL or u is None or u.facts is None:
                raise StudyLedgerError("early_measurement_unresolved")
            if message_sha256(u.facts) != message_sha256(facts):
                raise StudyLedgerError("early_facts_mismatch")
            self.bound.add(identity)

    def candidate(self, actual: NativeCandidateInput, result: NativeCandidateResult) -> None:
        if self.prefix is None:
            raise StudyLedgerError("early_journal_required")
        count = len(actual.observations.records)
        if count > len(self.prefix.records):
            raise StudyLedgerError("early_prefix_mismatch")
        prefix = ObservationBundle(
            run_id=self.prefix.run_id,
            engine_version=self.prefix.engine_version,
            engine_fingerprint=self.prefix.engine_fingerprint,
            space=self.prefix.space,
            records=self.prefix.records[:count],
        )
        expected = NativeCandidateInput(
            pool=self.pool,
            config=self.candidate_config,
            observations=prefix,
        )
        if message_sha256(expected) != message_sha256(actual):
            raise StudyLedgerError("early_prefix_mismatch")
        identity = result.facts.attempt_id
        validate_native_candidate_result(result, expected, attempt_id=identity)
        self.attempt(
            identity,
            "candidate_production",
            message_sha256(expected),
            message_sha256(self.candidate_config),
            result.facts,
        )
        old = self.candidates.get(identity)
        if old is not None and (
            message_sha256(old[0]) != message_sha256(actual)
            or message_sha256(old[1]) != message_sha256(result)
        ):
            raise StudyLedgerError("early_stage_conflict")
        self.candidates[identity] = (expected, result)
        if count < len(self.prefix.records):
            self.historical.add(identity)

    def selection(self, identity: str, selected: SelectedNativeCandidate) -> None:
        pair = self.candidates.get(identity)
        if pair is None:
            raise StudyLedgerError("early_candidate_material_missing")
        actual, result = pair
        validate_selected_native_candidate(selected, result, actual, attempt_id=identity)
        self.selections[message_sha256(selected)] = selected

    def context(self, actual: NativeEvaluationInput) -> None:
        self.candidate(actual.candidates, actual.candidate_result)
        if (
            actual.candidate_attempt_id != actual.candidate_result.facts.attempt_id
            or message_sha256(actual.policy) != message_sha256(self.policy)
            or message_sha256(actual.prediction_config) != message_sha256(self.prediction_config)
        ):
            raise StudyLedgerError("early_context_mismatch")
        if actual.selected is not None:
            self.selection(actual.candidate_attempt_id, actual.selected)

    def bind(self, witnesses: StudyEarlyWitnesses) -> None:
        # Dependency order is independent of the transport order. Duplicate explicit
        # stage IDs reject, while an identical embedded predecessor is reusable.
        seen: set[tuple[str, str]] = set()
        for w in witnesses.stages:
            identity = (
                w.candidate_attempt_id
                if isinstance(w, EarlySelectionWitness)
                else w.attempt_id
                if isinstance(w, EarlyPredictionWitness)
                else w.result.facts.attempt_id
            )
            key = (w.kind, identity)
            if key in seen:
                raise StudyLedgerError("early_duplicate_stage")
            seen.add(key)
        for w in witnesses.stages:
            if isinstance(w, EarlyCandidateWitness):
                self.candidate(w.actual_input, w.result)
            elif isinstance(w, EarlyPreparationWitness | EarlyDiagnosticWitness):
                self.context(
                    w.actual_input
                    if isinstance(w, EarlyPreparationWitness)
                    else w.actual_input.context
                )
        for w in witnesses.stages:
            if isinstance(w, EarlySelectionWitness):
                self.selection(w.candidate_attempt_id, w.selected)
            elif isinstance(w, EarlyPreparationWitness):
                identity = w.result.facts.attempt_id
                validate_native_preparation_result(w.result, w.actual_input, attempt_id=identity)
                self.attempt(
                    identity,
                    "preparation",
                    message_sha256(w.actual_input),
                    message_sha256(self.policy),
                    w.result.facts,
                )
                self.preparations[identity] = w
                if w.actual_input.candidate_attempt_id in self.historical:
                    self.historical.add(identity)
            elif isinstance(w, EarlyDiagnosticWitness):
                config = self.diagnostic_config
                if config is None:
                    raise StudyLedgerError("early_diagnostic_config_missing")
                actual = ClassicalDiagnosticInput(
                    context=w.actual_input.context,
                    config=config,
                    world=self.world,
                )
                if message_sha256(actual) != message_sha256(w.actual_input) or message_sha256(
                    config.scoring_policy
                ) != message_sha256(self.policy):
                    raise StudyLedgerError("early_diagnostic_mismatch")
                identity = w.result.facts.attempt_id
                validate_classical_diagnostic_result(w.result, actual, attempt_id=identity)
                self.attempt(
                    identity,
                    "classical_diagnostic",
                    message_sha256(actual),
                    message_sha256(config),
                    w.result.facts,
                )
                if actual.context.candidate_attempt_id in self.historical:
                    self.historical.add(identity)
        for w in witnesses.stages:
            if not isinstance(w, EarlyPredictionWitness):
                continue
            prepared = self.preparations.get(w.preparation_attempt_id)
            if prepared is None or prepared.result.payload.protocol is None:
                raise StudyLedgerError("early_preparation_material_missing")
            protocol, selected = prepared.result.payload.protocol, prepared.actual_input.selected
            assert selected is not None
            probe = next((p for p in protocol.probes if p.probe_id == w.probe_id), None)
            if probe is None:
                raise StudyLedgerError("early_probe_mismatch")
            prediction = NativePredictionInput(
                model=selected.model,
                candidate_config=self.candidate_config,
                request=probe.request,
                config=self.prediction_config,
            )
            if w.result is not None:
                validate_native_prediction_result(w.result, prediction, attempt_id=w.attempt_id)
            self.attempt(
                w.attempt_id,
                "prediction",
                message_sha256(prediction),
                message_sha256(self.prediction_config),
                None if w.result is None else w.result.facts,
            )
            entries = self.predictions.setdefault(w.preparation_attempt_id, [])
            entries.append(w)
            if w.preparation_attempt_id in self.historical:
                self.historical.add(w.attempt_id)


def reconcile_study_early_stop(
    ledger_raw: bytes,
    journal_path: Path,
    *,
    cell_id: str,
    materials: dict[str, bytes],
    witnesses_raw: bytes,
) -> StudyEarlyEvidence:
    """Compose every supplied actual stage and every charged cell attempt, without work."""
    if sum(map(len, materials.values())) + len(ledger_raw) + len(witnesses_raw) > (
        MAX_PUBLICATION_INPUT_BYTES
    ):
        raise StudyLedgerError("publication_input_limit")
    if sum(map(len, materials.values())) > MAX_STUDY_JSON_BYTES:
        raise StudyLedgerError("native_material_limit")
    allowed = NATIVE_MATERIAL_KINDS | {"classical_diagnostic_config"}
    if set(materials) not in (NATIVE_MATERIAL_KINDS, allowed):
        raise StudyLedgerError("native_material_set_mismatch")
    ledger = read_study_ledger(ledger_raw)
    manifest = study_manifest(ledger)
    cell = next((c for c in manifest.cells if c.cell_id == cell_id), None)
    if cell is None:
        raise StudyLedgerError("unknown_cell")
    catalog = _artifact(manifest, materials, "world_catalog", NativeWorldCatalog)
    if tuple(w.world_id for w in catalog.worlds) != manifest.world_ids:
        raise StudyLedgerError("world_catalog_mismatch")
    pool = _artifact(manifest, materials, "pool", NativeSpringPool)
    candidate_config = _artifact(manifest, materials, "candidate_config", NativeCandidateConfig)
    prediction_config = _artifact(manifest, materials, "prediction_config", NativePredictionConfig)
    policy = _artifact(manifest, materials, "scoring_policy", NativeScoringPolicy)
    config = (
        _artifact(manifest, materials, "classical_diagnostic_config", ClassicalDiagnosticConfig)
        if "classical_diagnostic_config" in materials
        else None
    )
    typed_materials = {
        "world_catalog": catalog,
        "pool": pool,
        "candidate_config": candidate_config,
        "prediction_config": prediction_config,
        "scoring_policy": policy,
    }
    if config is not None:
        typed_materials["classical_diagnostic_config"] = config
    reconciliation = _journal(ledger, journal_path, catalog, cell_id)
    prefix = None if reconciliation is None else reconciliation.snapshot.committed_prefix()
    journal_sha = None if reconciliation is None else reconciliation.snapshot.journal_bytes_sha256
    snapshots = study_cell_attempts(ledger, cell_id)
    # Even omitted bytes cannot turn a known terminal scoring invocation into an
    # earlier failure. Recovery supplies that result to the accepted scored path.
    if any(s.reservation.operation == "scoring" and s.state in FINAL for s in snapshots):
        raise StudyLedgerError("scored_path_required")
    witnesses = parse_study_early_witnesses(witnesses_raw)
    world = next(w.definition for w in catalog.worlds if w.world_id == cell.world_id)
    stages = _Stages(
        prefix, pool, candidate_config, prediction_config, policy, world, config, snapshots
    )
    try:
        stages.bind(witnesses)
    except StudyLedgerError:
        raise
    except ValueError:
        raise StudyLedgerError("early_material_mismatch") from None
    actual_ops = {"candidate_production", "preparation", "prediction", "classical_diagnostic"}
    missing = tuple(
        s.reservation.attempt_id
        for s in snapshots
        if s.reservation.operation in actual_ops
        and (
            s.reservation.operation != "preparation"
            or s.reservation.config_sha256 == message_sha256(policy)
        )
        and s.state in FINAL
        and s.reservation.attempt_id not in stages.bound
    )
    unresolved = any(s.state not in FINAL for s in snapshots)
    intents = study_purchase_intents(ledger, cell_id)
    pending = () if reconciliation is None else reconciliation.pending_operation_ids
    missing_rows = (
        tuple(p.operation_id for p in intents)
        if reconciliation is None
        else reconciliation.missing_reservation_ids
    )
    rows = () if reconciliation is None else reconciliation.snapshot.reservations
    complete_purchases = len(intents) == len(rows) == 12 and not pending and not missing_rows
    current_candidates = {
        identity: result
        for identity, (_, result) in stages.candidates.items()
        if identity not in stages.historical
    }
    current_prepared = {
        identity: p
        for identity, p in stages.preparations.items()
        if identity not in stages.historical
    }
    selected = {
        s.model_sha256: s
        for s in stages.selections.values()
        if prefix is not None and s.observation_sha256 == message_sha256(prefix)
    }
    protocols = {
        p.result.payload.protocol_sha256
        for p in current_prepared.values()
        if p.result.payload.protocol is not None
    }
    stage: EarlyStage
    failed = False
    if missing:
        stage = "material_recovery"
    elif not complete_purchases:
        stage = "unstarted" if not intents and not rows else "purchases"
    elif any(p.result.payload.protocol is not None for p in current_prepared.values()):
        stage = (
            "scoring_unavailable"
            if any(
                len({p.probe_id for p in stages.predictions.get(identity, [])}) == 24
                for identity in current_prepared
            )
            else "predictions_unavailable"
        )
    elif current_prepared:
        stage = "preparation_rejected"
        failed = True
        # A failure on one path cannot erase another available candidate/selection.
        # These are provenance receipts, never proof of the future MAP decision.
        prepared_candidates = {
            p.actual_input.candidate_attempt_id for p in current_prepared.values()
        }
        prepared_selections = {
            message_sha256(p.actual_input.selected)
            for p in current_prepared.values()
            if p.actual_input.selected is not None
        }
        if any(message_sha256(s) not in prepared_selections for s in selected.values()):
            stage, failed = "preparation_unavailable", False
        elif any(
            c.payload.status == "produced" and identity not in prepared_candidates
            for identity, c in current_candidates.items()
        ):
            stage, failed = "selection_unavailable", False
    elif selected:
        stage = "preparation_unavailable"
    elif any(c.payload.status == "produced" for c in current_candidates.values()):
        stage = "selection_unavailable"
    else:
        stage = "candidate_unavailable"
        failed = bool(current_candidates)
    if failed:
        positions = {
            record.event.attempt_id: record.sequence
            for record in ledger.records
            if isinstance(record.event, StudyAttemptUpdate) and record.event.state in FINAL
        }
        last_bound = max(
            (positions[i] for i in (*current_candidates, *current_prepared)), default=-1
        )
        # Generic selector facts do not prove a selected model. Later completed
        # selector work nevertheless prevents an older failure being called final.
        if any(
            s.reservation.operation == "selection"
            and s.state == "completed"
            and positions[s.reservation.attempt_id] > last_bound
            for s in snapshots
        ):
            stage, failed = "selection_unavailable", False
    budget = summarize_study(ledger).budget
    status = "failed" if failed and not unresolved and not missing else "incomplete"
    reason = "execution_failure" if status == "failed" else "interrupted"
    if status == "incomplete" and (
        budget.over_limit or budget.remaining_cpu_ns == 0 or budget.remaining_artifact_bytes == 0
    ):
        status, reason = "cap_limited", "resource_limit"
    outcome = StudyCellOutcome.model_validate(
        {
            "cell_id": cell_id,
            "status": status,
            "reason": reason,
            "journal_id": cell.journal_id,
            "observation_sha256": None if prefix is None else message_sha256(prefix),
            "model_sha256": next(iter(selected)) if len(selected) == 1 else None,
            "report_sha256": None,
            "scoring_policy_sha256": message_sha256(policy),
            "protocol_sha256": (
                next(iter(protocols)) if len(selected) == len(protocols) == 1 else None
            ),
            "selector_config_sha256": manifest.artifact(SELECTOR_ARTIFACTS[cell.selector]).sha256,
        }
    )
    evidence = StudyEarlyEvidence(
        ledger_identity=_identity(ledger_raw, ledger),
        ledger_revision=len(ledger.records),
        accounting_plan_sha256=message_sha256(ledger.plan),
        manifest_sha256=message_sha256(manifest),
        cell_id=cell_id,
        journal_id=cell.journal_id,
        journal_raw_sha256=journal_sha,
        current_prefix=prefix,
        reserved_slots=len(intents),
        journal_rows=tuple(
            StudyEarlyPurchaseRow(
                operation_id=row.operation_id,
                ordinal=row.ordinal,
                experiment_sha256=message_sha256(row.experiment),
                record_sha256=None if row.record is None else message_sha256(row.record),
                status="pending" if row.record is None else row.record.status,
            )
            for row in rows
        ),
        pending_operation_ids=pending,
        missing_reservation_ids=missing_rows,
        failed_operation_ids=() if reconciliation is None else reconciliation.failed_operation_ids,
        materials=tuple(
            StudyEarlyMaterial.model_validate(
                {
                    "kind": kind,
                    "identity": _identity(materials[kind], value).model_dump(mode="json"),
                }
            )
            for kind, value in typed_materials.items()
        ),
        witnesses_identity=_identity(witnesses_raw, witnesses),
        witnesses=witnesses,
        attempts=tuple(
            StudyEarlyAttempt(
                reservation=s.reservation,
                state=s.state,
                latest_update=s.latest_update,
                known_cpu_ns=s.cpu_ns,
                known_wall_ns=s.wall_ns,
                known_artifact_bytes=s.artifact_bytes,
            )
            for s in snapshots
        ),
        missing_result_attempt_ids=missing,
        historical_attempt_ids=tuple(
            s.reservation.attempt_id
            for s in snapshots
            if s.reservation.attempt_id in stages.historical
        ),
        stage=stage,
        budget=budget,
        outcome=outcome,
    )
    latest = _journal(ledger, journal_path, catalog, cell_id)
    if (None if latest is None else latest.snapshot.journal_bytes_sha256) != journal_sha:
        raise StudyLedgerError("journal_changed")
    return evidence


@dataclass(frozen=True)
class StudyEarlyProposal:
    ledger: NativeStudyLedger
    evidence: StudyEarlyEvidence
    evidence_raw: bytes
    receipt: StudyPublicationReceipt
    replayed: bool


def propose_study_early_stop(
    ledger_raw: bytes,
    journal_path: Path,
    *,
    event_id: str,
    expected_revision: int,
    expected_head_sha256: str,
    cell_id: str,
    materials: dict[str, bytes],
    witnesses_raw: bytes,
    original_ledger_raw: bytes | None = None,
    original_evidence_raw: bytes | None = None,
) -> StudyEarlyProposal:
    return StudyEarlyProposal(
        *_propose_publication(
            ledger_raw,
            event_id=event_id,
            expected_revision=expected_revision,
            expected_head_sha256=expected_head_sha256,
            original_ledger_raw=original_ledger_raw,
            original_evidence_raw=original_evidence_raw,
            parse_evidence=parse_study_early_evidence,
            reconcile=lambda raw: reconcile_study_early_stop(
                raw,
                journal_path,
                cell_id=cell_id,
                materials=materials,
                witnesses_raw=witnesses_raw,
            ),
            ledger_identity=lambda evidence: evidence.ledger_identity,
            outcome=lambda evidence: evidence.outcome,
        )
    )
