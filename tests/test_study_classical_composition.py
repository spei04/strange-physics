"""Synthetic cross-component tests; no study runner, real measurements or cell publisher."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from test_study_journal import sql
from test_study_ledger import LOCK, append, empty, materials, reserve, update
from test_study_scoring import Material, bind, changed_history, make_material, raw, typed

import strange_physics.evaluation as evaluator
import strange_physics.prediction as old_prediction
from strange_physics import study_contracts as c
from strange_physics import study_ledger as ledger
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.native_classical import (
    classical_condition_sha256,
    run_classical_diagnostic,
    validate_classical_diagnostic_result,
)
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
    ClassicalDiagnosticResult,
)
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import message_sha256


@dataclass(frozen=True)
class JointMaterial:
    native: Material
    actual: ClassicalDiagnosticInput
    result: ClassicalDiagnosticResult


@pytest.fixture(scope="module")
def joint(tmp_path_factory: pytest.TempPathFactory) -> JointMaterial:
    path = tmp_path_factory.mktemp("joint-journal") / "journal.db"
    native = make_material(path)
    config = ClassicalDiagnosticConfig(
        fit_config=SpringFitConfig(),
        prediction_config=SpringPredictionConfig(),
        scoring_policy=native.actual.context.policy,
    )
    # This is a fresh synthetic freeze, not mutation of an already admitted study.
    manifest = ledger.study_manifest(native.history)
    body = raw(config)
    data = manifest.model_dump(mode="json")
    data["artifacts"].append(
        dict(
            kind="classical_diagnostic_config",
            sha256=hashlib.sha256(body).hexdigest(),
            byte_count=len(body),
        )
    )
    manifest = typed(c.NativeStudyManifest, data)
    artifacts = materials()[1] | native.artifacts | {"classical_diagnostic_config": body}
    history = ledger.freeze_native_study(
        empty(),
        event_id="freeze",
        manifest=manifest,
        expected_revision=0,
        expected_purpose="synthetic_validation",
        source_commit=manifest.source_commit,
        uv_lock_bytes=LOCK,
        engine_fingerprint=manifest.engine_fingerprint,
        artifacts=artifacts,
    )
    for record in native.history.records[1:]:
        assert isinstance(record.event, c.StudyAttemptReservation | c.StudyAttemptUpdate)
        history = append(history, record.event, record.event_id)
    native = changed_history(native, history)
    evidence = bind(native, path)
    actual = ClassicalDiagnosticInput(
        context=native.actual.context, config=config, world=native.actual.world
    )
    assert evidence.observation_sha256 == message_sha256(actual.context.candidates.observations)
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    validate_classical_diagnostic_result(result, actual, attempt_id="diagnostic")
    return JointMaterial(native, actual, result)


@pytest.fixture
def journal(tmp_path: Path, joint: JointMaterial) -> Path:
    path = tmp_path / "journal.db"
    path.write_bytes(joint.native.journal_bytes)
    path.chmod(0o600)
    return path


def reservation(
    joint: JointMaterial, identity: str = "diagnostic", **changes: Any
) -> c.StudyAttemptReservation:
    values: dict[str, Any] = dict(
        phase="comparison",
        cell_id=joint.native.cell,
        operation="classical_diagnostic",
        config_sha256=message_sha256(joint.actual.config),
        input_sha256=message_sha256(joint.actual),
    )
    values.update(changes)
    return reserve(identity, **values)


def terminal(
    history: c.NativeStudyLedger, result: ClassicalDiagnosticResult
) -> c.NativeStudyLedger:
    # Deliberately synthetic measurements: facts never measure CPU, wall or bytes.
    return append(
        history,
        c.StudyAttemptUpdate(
            attempt_id=result.facts.attempt_id,
            state=result.facts.outcome,
            cpu_ns=17,
            wall_ns=23,
            artifact_bytes=5,
            facts=c.NativeWorkFacts.model_validate_json(result.facts.model_dump_json()),
        ),
    )


def test_actual_journal_classical_and_one_frozen_accounting_envelope(
    joint: JointMaterial, journal: Path
) -> None:
    native, actual, result = joint.native, joint.actual, joint.result
    before = bind(native, journal)
    journal_bytes = journal.read_bytes()
    context_bytes = raw(actual.context)
    assert len(actual.context.candidates.observations.records) == 12
    assert before.failed_purchase_operation_ids == ("operation-11",)
    assert result.payload.fit is not None and result.payload.fit.result is not None
    assert result.payload.fit.result.diagnostics.failed_record_count == 1
    assert result.payload.fit.model is not None and result.payload.protocol is not None
    assert result.payload.evaluation is not None
    assert result.payload.evaluation.status == "scored"
    primary_protocol = native.actual.preparation.payload.protocol
    assert primary_protocol is not None
    assert classical_condition_sha256(primary_protocol) == classical_condition_sha256(
        result.payload.protocol
    )
    assert message_sha256(primary_protocol) != message_sha256(result.payload.protocol)
    assert result.facts.observation_sha256 == before.observation_sha256
    assert (
        result.facts.config_sha256
        == ledger.study_manifest(native.history).artifact("classical_diagnostic_config").sha256
    )
    assert result.facts.output_sha256 == message_sha256(result.payload)

    history = terminal(append(native.history, reservation(joint)), result)
    after = bind(changed_history(native, history), journal)
    assert raw(after.score) == raw(before.score)
    assert after.budget.charged_cpu_ns == before.budget.charged_cpu_ns + 17
    assert after.budget.charged_artifact_bytes == before.budget.charged_artifact_bytes + 5
    assert after.budget.purchased_slots == 12
    assert after.unresolved_cell_attempt_ids == ()
    assert len(after.attempts) == 27  # Diagnostic is a distinct outer ledger operation.
    snapshots = ledger.study_cell_attempts(history, native.cell)
    assert len(snapshots) == len(ledger.study_cell_attempts(native.history, native.cell)) + 1
    assert snapshots[-1].latest_update is not None
    assert snapshots[-1].latest_update.facts is not None
    assert message_sha256(snapshots[-1].latest_update.facts) == message_sha256(result.facts)
    assert ledger.read_study_ledger(raw(history)) == history
    assert ledger.summarize_study(history).cells[0].status == "in_progress"
    assert not any(isinstance(r.event, c.StudyCellOutcome) for r in history.records)
    assert journal.read_bytes() == journal_bytes and raw(actual.context) == context_bytes


@pytest.mark.parametrize("stage", ["prediction", "evaluator"])
def test_diagnostic_unscorable_or_failed_preserves_native_primary_and_cost(
    joint: JointMaterial, journal: Path, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = bind(joint.native, journal)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ArithmeticError("synthetic diagnostic stage failure")

    if stage == "prediction":
        monkeypatch.setattr(old_prediction, "_state_at_time", fail)
    else:
        monkeypatch.setattr(evaluator, "_probe_mse", fail)
    result = run_classical_diagnostic(joint.actual, attempt_id="diagnostic")
    validate_classical_diagnostic_result(result, joint.actual, attempt_id="diagnostic")
    evaluation = result.payload.evaluation
    assert evaluation is not None
    if stage == "prediction":
        assert evaluation.status == "unscorable"
        assert evaluation.diagnostics.failed_prediction_count == 24
        assert result.facts.completed_count == 1
    else:
        assert evaluation.report is None
        assert evaluation.diagnostics.failed_prediction_count == 0
        assert result.facts.failed_count == 1
    history = terminal(append(joint.native.history, reservation(joint)), result)
    after = bind(changed_history(joint.native, history), journal)
    assert raw(after.score) == raw(before.score)
    assert after.budget.charged_cpu_ns == before.budget.charged_cpu_ns + 17
    assert after.budget.unresolved_attempts == 0
    assert ledger.summarize_study(history).cells[0].status == "in_progress"


@pytest.mark.parametrize("field", ["world", "prefix", "candidate", "selected"])
def test_diagnostic_result_cannot_substitute_verified_native_material(
    joint: JointMaterial, journal: Path, field: str
) -> None:
    before = bind(joint.native, journal)
    data = joint.actual.model_dump(mode="json")
    if field == "world":
        data["world"]["noise_seed"] += 1
    elif field == "prefix":
        data["context"]["candidates"]["observations"]["records"][-1]["operation_id"] = "foreign"
    elif field == "candidate":
        data["context"]["candidate_attempt_id"] = "foreign"
    else:
        data["context"]["selected"]["candidate_result_sha256"] = "f" * 64
    substituted = typed(ClassicalDiagnosticInput, data)
    with pytest.raises(ValueError):
        validate_classical_diagnostic_result(joint.result, substituted, attempt_id="diagnostic")
    assert raw(bind(joint.native, journal).score) == raw(before.score)


@pytest.mark.parametrize("case", ["before_freeze", "foreign_cell", "wrong_config", "wrong_input"])
def test_actual_diagnostic_facts_require_frozen_cell_and_exact_reservation(
    joint: JointMaterial, case: str
) -> None:
    history = joint.native.history
    if case == "before_freeze":
        with pytest.raises(ledger.StudyLedgerError, match="unknown_cell"):
            append(empty(), reservation(joint))
    elif case == "foreign_cell":
        with pytest.raises(ledger.StudyLedgerError):
            append(history, reservation(joint, cell_id="foreign-cell"))
    elif case == "wrong_config":
        with pytest.raises(ledger.StudyLedgerError):
            append(history, reservation(joint, config_sha256="f" * 64))
    else:
        history = append(history, reservation(joint, input_sha256="f" * 64))
        with pytest.raises(ledger.StudyLedgerError, match="facts_mismatch"):
            terminal(history, joint.result)


@pytest.mark.parametrize("phase", ["reference", "calibration", "sensitivity", "accounting"])
def test_classical_envelope_cannot_bypass_comparison_scope(
    joint: JointMaterial, phase: str
) -> None:
    with pytest.raises(ValueError):
        reservation(joint, phase=phase, cell_id=None)


def test_interruption_and_retry_hold_original_budget_without_erasing_primary(
    joint: JointMaterial, journal: Path
) -> None:
    before = bind(joint.native, journal)
    original = reservation(joint)
    history = append(joint.native.history, original)
    history = append(history, update(original, "running", cpu_ns=7, artifact_bytes=2))
    history = append(
        history,
        update(original, "unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None),
    )
    interrupted = bind(changed_history(joint.native, history), journal)
    assert raw(interrupted.score) == raw(before.score)
    assert interrupted.unresolved_cell_attempt_ids == ("diagnostic",)
    assert interrupted.budget.charged_cpu_ns == before.budget.charged_cpu_ns + 100
    assert interrupted.budget.charged_artifact_bytes == before.budget.charged_artifact_bytes + 10
    held = ledger.study_cell_attempts(history, joint.native.cell)[-1]
    assert held.state == "unknown" and held.cpu_ns == 7 and held.artifact_bytes == 2

    retry = reservation(joint, "diagnostic-retry", retry_of="diagnostic")
    history = append(history, retry)
    result = run_classical_diagnostic(joint.actual, attempt_id=retry.attempt_id)
    validate_classical_diagnostic_result(result, joint.actual, attempt_id=retry.attempt_id)
    history = terminal(history, result)
    after = bind(changed_history(joint.native, history), journal)
    assert raw(after.score) == raw(before.score)
    assert after.unresolved_cell_attempt_ids == ("diagnostic",)
    assert after.budget.charged_cpu_ns == before.budget.charged_cpu_ns + 100 + 17
    assert after.budget.charged_artifact_bytes == before.budget.charged_artifact_bytes + 10 + 5
    assert after.budget.purchased_slots == 12 and after.budget.unresolved_attempts == 1
    assert ledger.summarize_study(history).cells[0].status == "in_progress"


@pytest.mark.parametrize("mutation", ["pending", "missing", "world"])
def test_current_journal_still_gates_joint_fixture_material(
    joint: JointMaterial, journal: Path, mutation: str
) -> None:
    if mutation == "pending":
        sql(journal, "UPDATE experiments SET record_json=NULL WHERE ordinal=11")
    elif mutation == "missing":
        sql(journal, "DELETE FROM experiments WHERE ordinal=11")
    else:
        sql(journal, "UPDATE run SET engine_fingerprint=?", ("f" * 64,))
    with pytest.raises(ValueError):
        bind(joint.native, journal)
