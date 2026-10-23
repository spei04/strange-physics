"""Synthetic private publication proposals, never measured study execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from test_study_classical_composition import (
    JointMaterial,
    reservation,
    terminal,
)
from test_study_classical_composition import joint as joint
from test_study_classical_composition import journal as journal
from test_study_ledger import append, reserve, update
from test_study_scoring import raw, typed

import strange_physics.evaluation as evaluator
import strange_physics.prediction as old_prediction
from strange_physics import native_candidates, native_prediction, native_scoring
from strange_physics import study_contracts as c
from strange_physics import study_ledger as ledger
from strange_physics import study_publication as publication
from strange_physics.native_classical import run_classical_diagnostic
from strange_physics.research_contracts import message_sha256
from strange_physics.study_publication_contracts import (
    parse_study_publication_evidence,
    study_publication_json_schema,
)


def history(joint: JointMaterial) -> c.NativeStudyLedger:
    return terminal(append(joint.native.history, reservation(joint)), joint.result)


def arguments(joint: JointMaterial, **changes: Any) -> dict[str, Any]:
    args: dict[str, Any] = dict(
        cell_id=joint.native.cell,
        materials=joint.native.artifacts
        | {"classical_diagnostic_config": raw(joint.actual.config)},
        scoring_input_raw=raw(joint.native.actual),
        scoring_result_raw=raw(joint.native.result),
        diagnostic_attempt_id="diagnostic",
        diagnostic_result_raw=raw(joint.result),
    )
    args.update(changes)
    return args


def propose(
    joint: JointMaterial, journal: Path, value: c.NativeStudyLedger | None = None, **changes: Any
) -> publication.StudyPublicationProposal:
    h = history(joint) if value is None else value
    args = arguments(joint)
    args.update(
        event_id="publication",
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
    )
    args.update(changes)
    return publication.propose_study_publication(raw(h), journal, **args)


def test_actual_full_evidence_event_receipt_and_no_write(
    joint: JointMaterial, journal: Path
) -> None:
    original = history(joint)
    before = journal.read_bytes()
    p = propose(joint, journal, original)
    assert not p.replayed and len(p.ledger.records) == len(original.records) + 1
    assert raw(p.evidence.native.score) == raw(joint.native.result)
    assert p.evidence.diagnostic_result is not None
    assert raw(p.evidence.diagnostic_result) == raw(joint.result)
    assert p.evidence.outcome.status == "complete"
    assert p.evidence.native.failed_purchase_operation_ids == ("operation-11",)
    record = p.ledger.records[-1]
    assert isinstance(record.event, c.StudyPublicationEvent)
    assert record.event.evidence.raw_sha256 == hashlib.sha256(p.evidence_raw).hexdigest()
    assert record.previous_sha256 == p.receipt.original_head_sha256
    assert p.receipt.resulting_ledger_sha256 == message_sha256(p.ledger)
    assert p.receipt.record_sha256 == message_sha256(record)
    assert p.evidence.native.ledger_identity.raw_sha256 == hashlib.sha256(raw(original)).hexdigest()
    assert p.evidence.native.ledger_revision == record.sequence
    assert ledger.summarize_study(p.ledger).cells[0].outcome == p.evidence.outcome
    assert ledger.summarize_study(p.ledger).budget == ledger.summarize_study(original).budget
    assert journal.read_bytes() == before
    assert parse_study_publication_evidence(p.evidence_raw) == p.evidence


def test_original_receipt_replay_after_unrelated_append(
    joint: JointMaterial, journal: Path
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    other = reserve("unrelated")
    later = append(append(p.ledger, other), update(other))
    replay = propose(
        joint,
        journal,
        later,
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
        original_ledger_raw=raw(h),
        original_evidence_raw=p.evidence_raw,
    )
    assert replay.replayed and replay.ledger == later
    assert raw(replay.receipt) == raw(p.receipt)
    assert replay.evidence_raw == p.evidence_raw
    assert replay.evidence.native.budget != ledger.summarize_study(later).budget


@pytest.mark.parametrize("which", ["revision", "head", "bool"])
def test_fresh_cas_rejects(joint: JointMaterial, journal: Path, which: str) -> None:
    changes = (
        {"expected_revision": 1}
        if which == "revision"
        else (
            {"expected_revision": True} if which == "bool" else {"expected_head_sha256": "0" * 64}
        )
    )
    with pytest.raises(ledger.StudyLedgerError, match="stale"):
        propose(joint, journal, **changes)


@pytest.mark.parametrize("which", ["ledger", "evidence", "both"])
def test_replay_requires_both_original_witnesses(
    joint: JointMaterial, journal: Path, which: str
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    args = dict(
        original_ledger_raw=raw(h) if which == "evidence" else None,
        original_evidence_raw=p.evidence_raw if which == "ledger" else None,
    )
    with pytest.raises(ledger.StudyLedgerError, match="witness_missing"):
        propose(joint, journal, p.ledger, **args)


@pytest.mark.parametrize("which", ["raw_result", "native_raw", "evidence_raw", "timing"])
def test_same_primary_changed_material_cannot_replay(
    joint: JointMaterial, journal: Path, which: str
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    changes: dict[str, Any] = dict(
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
        original_ledger_raw=raw(h),
        original_evidence_raw=p.evidence_raw,
    )
    if which == "raw_result":
        changes["diagnostic_result_raw"] = b" " + raw(joint.result)
    elif which == "native_raw":
        changes["scoring_input_raw"] = b" " + raw(joint.native.actual)
    elif which == "evidence_raw":
        changes["original_evidence_raw"] = b" " + p.evidence_raw
    else:
        data = joint.result.model_dump(mode="json")
        data["payload"]["evaluation"]["diagnostics"]["evaluation_runtime_ms"] += 1
        changes["diagnostic_result_raw"] = json.dumps(data).encode()
    with pytest.raises(ValueError):
        propose(joint, journal, p.ledger, **changes)


def test_conflicting_original_ledger_prefix(joint: JointMaterial, journal: Path) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    alternate = append(joint.native.history, reserve("different"))
    with pytest.raises(ledger.StudyLedgerError, match="original_prefix"):
        propose(
            joint,
            journal,
            p.ledger,
            original_ledger_raw=raw(alternate),
            original_evidence_raw=p.evidence_raw,
        )


@pytest.mark.parametrize("stage", ["prediction", "evaluator"])
def test_terminal_diagnostic_failure_preserves_native_score(
    joint: JointMaterial, journal: Path, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ArithmeticError("synthetic diagnostic failure")

    monkeypatch.setattr(
        old_prediction if stage == "prediction" else evaluator,
        "_state_at_time" if stage == "prediction" else "_probe_mse",
        fail,
    )
    result = run_classical_diagnostic(joint.actual, attempt_id="diagnostic")
    h = terminal(append(joint.native.history, reservation(joint)), result)
    p = propose(joint, journal, h, diagnostic_result_raw=raw(result))
    assert p.evidence.outcome.status == "complete"
    assert raw(p.evidence.native.score) == raw(joint.native.result)
    assert p.evidence.diagnostic_result is not None
    assert p.evidence.diagnostic_result.payload.evaluation is not None
    assert p.evidence.diagnostic_result.payload.evaluation.status == (
        "unscorable" if stage == "prediction" else "arithmetic_failure"
    )


@pytest.mark.parametrize("state", ["missing", "reserved", "running", "unknown", "overrun"])
def test_incomplete_or_actual_cap_preserves_known_cost(
    joint: JointMaterial, journal: Path, state: str
) -> None:
    h = joint.native.history
    r = reservation(joint)
    if state != "missing":
        h = append(h, r)
    if state in {"running", "unknown", "overrun"}:
        h = append(h, update(r, "running", cpu_ns=7, artifact_bytes=2))
    if state in {"unknown", "overrun"}:
        h = append(
            h,
            update(
                r,
                "unknown",
                cpu_ns=c.MAX_CPU_NS + 1 if state == "overrun" else None,
                wall_ns=None,
                artifact_bytes=None,
            ),
        )
    p = propose(
        joint,
        journal,
        h,
        diagnostic_result_raw=None,
        diagnostic_attempt_id=None if state == "missing" else "diagnostic",
    )
    assert p.evidence.outcome.status == ("cap_limited" if state == "overrun" else "incomplete")
    assert joint.native.result.payload.evaluation is not None
    assert p.evidence.outcome.report_sha256 == joint.native.result.payload.evaluation.report_sha256
    assert p.evidence.native.budget == ledger.summarize_study(h).budget
    if state == "unknown":
        assert p.evidence.diagnostic_attempt is not None
        assert p.evidence.diagnostic_attempt.known_cpu_ns == 7
        assert p.evidence.native.budget.charged_cpu_ns >= 100


def test_unknown_retry_preserves_original_hold(joint: JointMaterial, journal: Path) -> None:
    r = reservation(joint, "old")
    h = append(append(joint.native.history, r), update(r, "unknown", cpu_ns=150))
    h = terminal(append(h, reservation(joint, retry_of="old")), joint.result)
    p = propose(joint, journal, h)
    assert p.evidence.outcome.status == "incomplete"
    assert p.evidence.native.unresolved_cell_attempt_ids == ("old",)
    assert p.evidence.native.budget == ledger.summarize_study(h).budget
    assert p.evidence.native.budget.charged_cpu_ns >= 167


@pytest.mark.parametrize(
    "case", ["missing_result", "missing_attempt", "unknown_result", "wrong_input"]
)
def test_partial_or_conflicting_diagnostic_witness_rejects(
    joint: JointMaterial, journal: Path, case: str
) -> None:
    h = history(joint)
    changes: dict[str, Any] = {}
    if case == "missing_result":
        changes["diagnostic_result_raw"] = None
    elif case == "missing_attempt":
        changes["diagnostic_attempt_id"] = None
    elif case == "unknown_result":
        r = reservation(joint)
        h = append(append(joint.native.history, r), update(r, "unknown"))
    else:
        h = append(joint.native.history, reservation(joint, input_sha256="f" * 64))
        changes["diagnostic_result_raw"] = None
    with pytest.raises(ValueError):
        propose(joint, journal, h, **changes)


def test_no_numerical_producer_is_called(
    joint: JointMaterial, journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import strange_physics.fitting as fitting
    import strange_physics.native_classical as classical

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Numerical execution is not reconciliation")

    for module, name in [
        (classical, "run_classical_diagnostic"),
        (classical, "fit_spring"),
        (classical, "predict_linear_spring"),
        (classical, "evaluate_spring_predictions"),
        (native_scoring, "evaluate_spring_predictions"),
        (native_candidates, "produce_native_candidates"),
        (native_prediction, "predict_native_spring"),
        (native_scoring, "score_native_predictions"),
        (old_prediction, "predict_linear_spring"),
        (evaluator, "evaluate_spring_predictions"),
    ]:
        monkeypatch.setattr(module, name, fail)
    # The accepted result binders may reconstruct protocol/preflight, not fit/predict/evaluate.
    monkeypatch.setattr(fitting, "fit_linear_spring", fail)
    assert propose(joint, journal).evidence.outcome.status == "complete"


@pytest.mark.parametrize(
    "raw_bytes", [b"{}", b'{"native":1,"native":2}', b'{"x":NaN}', b"[" * 42 + b"0" + b"]" * 42]
)
def test_strict_evidence_parser_rejects(raw_bytes: bytes) -> None:
    with pytest.raises(ValueError):
        parse_study_publication_evidence(raw_bytes)


def test_existing_outcome_bytes_and_private_schema(joint: JointMaterial, journal: Path) -> None:
    p = propose(joint, journal)
    assert (
        typed(c.StudyCellOutcome, p.evidence.outcome.model_dump(mode="json")) == p.evidence.outcome
    )
    assert not hasattr(p.evidence.outcome, "diagnostic_result")
    schema = study_publication_json_schema()
    assert schema["x-owner-only-roots"] == [
        "StudyDiagnosticAttempt",
        "StudyPublicationEvidence",
        "StudyPublicationReceipt",
    ]
    assert parse_study_publication_evidence(p.evidence_raw) == p.evidence


@pytest.mark.parametrize("case", ["compose", "evidence"])
def test_declared_byte_caps_before_decode(joint: JointMaterial, journal: Path, case: str) -> None:
    with pytest.raises(ValueError):
        if case == "compose":
            propose(
                joint,
                journal,
                scoring_input_raw=b" " * (publication.MAX_PUBLICATION_INPUT_BYTES + 1),
            )
        else:
            parse_study_publication_evidence(b" " * (c.MAX_PUBLICATION_BYTES + 1))


def test_same_prefix_different_original_raw_bytes_conflicts(
    joint: JointMaterial, journal: Path
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    with pytest.raises(ledger.StudyLedgerError, match="event_conflict"):
        propose(
            joint,
            journal,
            p.ledger,
            expected_revision=len(h.records),
            expected_head_sha256=message_sha256(h.records[-1]),
            original_ledger_raw=b" " + raw(h),
            original_evidence_raw=p.evidence_raw,
        )


def test_legacy_outcome_is_readable_but_not_publication_receipt(
    joint: JointMaterial, journal: Path
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    record = p.ledger.records[-1]
    legacy = c.NativeStudyLedger(
        plan=h.plan,
        records=(
            *h.records,
            c.StudyLedgerRecord(
                event_id=record.event_id,
                sequence=record.sequence,
                previous_sha256=record.previous_sha256,
                event=p.evidence.outcome,
            ),
        ),
    )
    assert ledger.read_study_ledger(raw(legacy)) == legacy
    with pytest.raises(ledger.StudyLedgerError, match="witness_missing"):
        propose(
            joint, journal, legacy, original_ledger_raw=raw(h), original_evidence_raw=p.evidence_raw
        )


@pytest.mark.parametrize("field", ["world_catalog", "classical_diagnostic_config"])
def test_actual_frozen_material_cannot_be_substituted(
    joint: JointMaterial, journal: Path, field: str
) -> None:
    args = arguments(joint)
    args["materials"][field] = b" " + args["materials"][field]
    with pytest.raises(ledger.StudyLedgerError, match="artifact_identity"):
        propose(joint, journal, **args)


def test_original_publication_does_not_claim_later_resolution(
    joint: JointMaterial, journal: Path
) -> None:
    r = reservation(joint)
    h = append(joint.native.history, r)
    p = propose(joint, journal, h, diagnostic_result_raw=None)
    later = terminal(p.ledger, joint.result)
    replay = propose(
        joint,
        journal,
        later,
        diagnostic_result_raw=None,
        original_ledger_raw=raw(h),
        original_evidence_raw=p.evidence_raw,
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
    )
    assert replay.evidence.outcome.status == "incomplete"
    assert raw(replay.receipt) == raw(p.receipt)
    assert replay.evidence.native.budget.unresolved_attempts == 1
    assert ledger.summarize_study(later).budget.unresolved_attempts == 0


def test_publication_schema_and_examples_are_current() -> None:
    from strange_physics.study_contracts import study_json_schema
    from strange_physics.study_publication_contracts import PUBLICATION_MODELS

    root = Path(__file__).parents[1] / "contracts"
    schema = study_publication_json_schema()
    assert json.loads((root / "native-study-publication.schema.json").read_text()) == schema
    assert json.loads((root / "study.schema.json").read_text()) == study_json_schema()
    fixtures = json.loads((root / "native-study-publication.examples.json").read_text())
    models = {m.__name__: m for m in PUBLICATION_MODELS}
    for name, value in fixtures["valid"].items():
        models[name].model_validate_json(json.dumps(value))
    # The configured external validator checks schema-negative/runtime-valid distinctions.
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in fixtures[group]:
            name = fixture["model"]
            value = fixtures["valid"][name] | {fixture["field"]: fixture["value"]}
            with pytest.raises(ValueError):
                models[name].model_validate_json(json.dumps(value))


@pytest.mark.parametrize("stage", ["missing_prediction", "evaluator"])
def test_native_failure_remains_distinct_from_terminal_diagnostic(
    joint: JointMaterial, journal: Path, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_study_scoring import settled

    from strange_physics.native_scoring_contracts import NativeScoringInput

    actual = joint.native.actual
    if stage == "missing_prediction":
        data = actual.model_dump(mode="json")
        data["predictions"]["entries"][0].update(status="missing", result=None)
        actual = typed(NativeScoringInput, data)
    else:

        def fail(*args: Any, **kwargs: Any) -> Any:
            raise ArithmeticError("synthetic native evaluator failure")

        monkeypatch.setattr(evaluator, "_probe_mse", fail)
    result = native_scoring.score_native_predictions(actual, attempt_id="scoring")
    h = c.NativeStudyLedger(
        plan=joint.native.history.plan, records=joint.native.history.records[:-2]
    )
    h = settled(h, result.facts, joint.native.cell)
    h = terminal(append(h, reservation(joint)), joint.result)
    p = propose(joint, journal, h, scoring_input_raw=raw(actual), scoring_result_raw=raw(result))
    assert p.evidence.outcome.status == "failed"
    assert p.evidence.outcome.reason == (
        "unscorable" if stage == "missing_prediction" else "execution_failure"
    )
    assert raw(p.evidence.native.score) == raw(result)
    assert p.evidence.diagnostic_result == joint.result
    if stage == "evaluator":
        assert p.evidence.outcome.report_sha256 is None
        assert result.payload.evaluation is not None
        assert result.payload.evaluation.diagnostics.failed_prediction_count == 0


@pytest.mark.parametrize("case", ["pending", "missing", "engine"])
def test_actual_journal_not_replaced_by_old_evidence(
    joint: JointMaterial, journal: Path, case: str
) -> None:
    from test_study_journal import sql

    h = history(joint)
    p = propose(joint, journal, h)
    if case == "pending":
        sql(journal, "UPDATE experiments SET record_json=NULL WHERE ordinal=11")
    elif case == "missing":
        sql(journal, "DELETE FROM experiments WHERE ordinal=11")
    else:
        sql(journal, "UPDATE run SET engine_fingerprint=?", ("f" * 64,))
    with pytest.raises(ValueError):
        propose(
            joint,
            journal,
            p.ledger,
            original_ledger_raw=raw(h),
            original_evidence_raw=p.evidence_raw,
            expected_revision=len(h.records),
            expected_head_sha256=message_sha256(h.records[-1]),
        )


def test_known_original_event_with_changed_kind_conflicts(
    joint: JointMaterial, journal: Path
) -> None:
    h = history(joint)
    p = propose(joint, journal, h)
    with pytest.raises(ledger.StudyLedgerError, match="unexpected_publication_witness"):
        propose(joint, journal, h, original_ledger_raw=raw(h), original_evidence_raw=p.evidence_raw)
    with pytest.raises(ledger.StudyLedgerError, match="stale_head"):
        propose(
            joint,
            journal,
            p.ledger,
            expected_revision=len(h.records),
            original_ledger_raw=raw(h),
            original_evidence_raw=p.evidence_raw,
            expected_head_sha256="a" * 64,
        )
