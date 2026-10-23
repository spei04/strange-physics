"""Synthetic actual-stage early-stop composition; no study or measured producer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Literal

import pytest
from test_study_classical_composition import JointMaterial, reservation, terminal
from test_study_classical_composition import joint as joint
from test_study_journal import sql
from test_study_ledger import append, reserve, update
from test_study_scoring import Material, raw, rechain, settled, typed
from test_study_scoring import material as material
from test_study_scoring import path as path

from strange_physics import study_contracts as c
from strange_physics import study_early as early
from strange_physics import study_ledger as ledger
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.control_contracts import ContractViolation
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_scoring import prepare_native_evaluation
from strange_physics.native_scoring_contracts import NativeEvaluationInput
from strange_physics.native_spring_contracts import NativeCandidateInput
from strange_physics.research_contracts import message_sha256
from strange_physics.study_early_contracts import (
    EarlyCandidateWitness,
    EarlyDiagnosticWitness,
    EarlyPredictionWitness,
    EarlyPreparationWitness,
    EarlySelectionWitness,
    StudyEarlyEvidence,
    StudyEarlyWitnesses,
    parse_study_early_evidence,
    parse_study_early_witnesses,
    study_early_json_schema,
)
from strange_physics.study_journal import reconcile_study_journal
from strange_physics.study_scoring import _artifact
from strange_physics.workflow_io import WorkflowError


def history(value: Material, identities: set[str]) -> c.NativeStudyLedger:
    data = value.history.model_dump(mode="json")
    data["records"] = [
        r
        for r in data["records"]
        if r["event"]["kind"] == "freeze" or r["event"].get("attempt_id") in identities
    ]
    return rechain(data)


def purchases(value: Material, count: int = 12) -> c.NativeStudyLedger:
    return history(value, {f"purchase-{i}" for i in range(count)})


def witnesses(
    value: Material, *, selected: bool = False, prepared: bool = False, count: int = 0
) -> StudyEarlyWitnesses:
    context = value.actual.context
    stages: list[Any] = [
        EarlyCandidateWitness(actual_input=context.candidates, result=context.candidate_result)
    ]
    if selected:
        assert context.selected is not None
        stages.append(
            EarlySelectionWitness(candidate_attempt_id="candidate", selected=context.selected)
        )
    if prepared:
        stages.append(
            EarlyPreparationWitness(actual_input=context, result=value.actual.preparation)
        )
        for e in value.actual.predictions.entries[:count]:
            stages.append(
                EarlyPredictionWitness(
                    preparation_attempt_id="preparation",
                    attempt_id=e.attempt_id,
                    probe_id=e.probe_id,
                    transport=e.status,
                    result=e.result,
                )
            )
    return StudyEarlyWitnesses(stages=tuple(stages))


def bind(
    value: Material, path: Path, h: c.NativeStudyLedger, w: StudyEarlyWitnesses | None = None
) -> StudyEarlyEvidence:
    return early.reconcile_study_early_stop(
        raw(h),
        path,
        cell_id=value.cell,
        materials=value.artifacts,
        witnesses_raw=raw(w or StudyEarlyWitnesses(stages=())),
    )


def propose(
    value: Material, path: Path, h: c.NativeStudyLedger, w: StudyEarlyWitnesses, **changes: Any
) -> early.StudyEarlyProposal:
    args: dict[str, Any] = dict(
        event_id="early-publication",
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
        cell_id=value.cell,
        materials=value.artifacts,
        witnesses_raw=raw(w),
    )
    args.update(changes)
    return early.propose_study_early_stop(raw(h), path, **args)


@pytest.mark.parametrize("count", [0, 1, 4, 11, 12])
def test_actual_purchase_prefix_and_absent_work(material: Material, path: Path, count: int) -> None:
    sql(path, "DELETE FROM experiments WHERE ordinal>=?", (count,))
    h = purchases(material, count)
    e = bind(material, path, h)
    assert e.reserved_slots == len(e.journal_rows) == count
    assert e.current_prefix is not None and len(e.current_prefix.records) == count
    assert e.outcome.status == "incomplete" and e.outcome.report_sha256 is None
    assert e.outcome.model_sha256 is None and e.outcome.protocol_sha256 is None
    assert e.stage == (
        "unstarted" if count == 0 else "candidate_unavailable" if count == 12 else "purchases"
    )
    assert e.budget == ledger.summarize_study(h).budget
    assert len(ledger.summarize_study(h).cells) == 36


@pytest.mark.parametrize("position", range(12))
def test_pending_hole_and_completed_failure_after_it(
    material: Material, path: Path, position: int
) -> None:
    sql(path, "UPDATE experiments SET record_json=NULL WHERE ordinal=?", (position,))
    e = bind(material, path, purchases(material))
    assert e.current_prefix is not None and len(e.current_prefix.records) == position
    assert len(e.journal_rows) == 12 and e.pending_operation_ids == (f"operation-{position}",)
    assert e.journal_rows[position].status == "pending"
    if position < 11:
        assert e.failed_operation_ids == ("operation-11",)
        assert e.journal_rows[-1].record_sha256 is not None


@pytest.mark.parametrize("count", [0, 1, 11])
def test_missing_charged_suffix_is_not_free(material: Material, path: Path, count: int) -> None:
    sql(path, "DELETE FROM experiments WHERE ordinal>=?", (count,))
    e = bind(material, path, purchases(material))
    assert e.missing_reservation_ids == tuple(f"operation-{i}" for i in range(count, 12))
    assert e.budget.purchased_slots == 12 and e.outcome.status == "incomplete"


def test_actual_missing_journal_and_symlink_are_distinct(
    material: Material, tmp_path: Path
) -> None:
    missing = tmp_path / "missing.db"
    e = bind(material, missing, purchases(material, 0))
    assert e.journal_raw_sha256 is None and e.current_prefix is None and not missing.exists()
    link = tmp_path / "link.db"
    link.symlink_to(missing)
    with pytest.raises(WorkflowError, match="unsafe_path"):
        bind(material, link, purchases(material, 0))


@pytest.mark.parametrize("case", ["untracked", "world", "engine"])
def test_journal_identity_cannot_be_assumed(material: Material, path: Path, case: str) -> None:
    h = purchases(material)
    if case == "untracked":
        h = purchases(material, 11)
    elif case == "engine":
        sql(path, "UPDATE run SET engine_fingerprint=?", ("a" * 64,))
    else:
        sql(path, "UPDATE run SET world_json=?", ("{}",))
    with pytest.raises((ledger.StudyLedgerError, ContractViolation)):
        bind(material, path, h)


@pytest.mark.parametrize(
    "level,count,stage",
    [
        ("candidate", 0, "selection_unavailable"),
        ("selected", 0, "preparation_unavailable"),
        ("prepared", 0, "predictions_unavailable"),
        ("prepared", 1, "predictions_unavailable"),
        ("prepared", 23, "predictions_unavailable"),
        ("prepared", 24, "scoring_unavailable"),
    ],
)
def test_real_available_stage_prefixes(
    material: Material, path: Path, level: str, count: int, stage: str
) -> None:
    ids = {f"purchase-{i}" for i in range(12)} | {"candidate"}
    if level == "prepared":
        ids.add("preparation")
        ids.update(f"prediction-{i}" for i in range(count))
    h = history(material, ids)
    w = witnesses(material, selected=level == "selected", prepared=level == "prepared", count=count)
    e = bind(material, path, h, w)
    assert e.stage == stage and e.outcome.status == "incomplete"
    assert len(e.witnesses.stages) == len(w.stages)
    assert e.outcome.report_sha256 is None
    if level != "candidate":
        assert material.actual.context.selected is not None
        assert e.outcome.model_sha256 == material.actual.context.selected.model_sha256


@pytest.mark.parametrize("operation", ["candidate", "preparation", "prediction-0"])
def test_omitted_terminal_material_is_recovery(
    material: Material, path: Path, operation: str
) -> None:
    h = history(material, {f"purchase-{i}" for i in range(12)} | {operation})
    e = bind(material, path, h)
    assert e.stage == "material_recovery"
    assert e.missing_result_attempt_ids == (operation,)
    assert e.outcome.status == "incomplete"


def test_terminal_score_cannot_be_hidden(material: Material, path: Path) -> None:
    with pytest.raises(ledger.StudyLedgerError, match="scored_path_required"):
        bind(material, path, material.history, witnesses(material))


@pytest.mark.parametrize("state", ["reserved", "running", "unknown"])
def test_unknown_and_retry_costs_survive(
    material: Material, path: Path, state: Literal["reserved", "running", "unknown"]
) -> None:
    h = purchases(material)
    f = material.actual.context.candidate_result.facts
    r = reserve(
        "unknown-candidate",
        phase="comparison",
        cell_id=material.cell,
        operation="candidate_production",
        config_sha256=f.config_sha256,
        input_sha256=f.input_sha256,
        cpu_reservation_ns=17,
    )
    h = append(h, r)
    if state != "reserved":
        h = append(
            h,
            c.StudyAttemptUpdate(
                attempt_id=r.attempt_id,
                state=state,
                cpu_ns=23,
                wall_ns=30,
                artifact_bytes=4,
                facts=None,
            ),
        )
    e = bind(material, path, h)
    assert e.outcome.status == "incomplete"
    assert e.budget == ledger.summarize_study(h).budget
    assert e.attempts[-1].state == state
    if state == "unknown":
        retry = typed(
            c.StudyAttemptReservation,
            r.model_dump(mode="json")
            | {
                "attempt_id": "retry",
                "retry_of": r.attempt_id,
            },
        )
        later = append(h, retry)
        again = bind(material, path, later)
        assert again.budget.charged_cpu_ns == e.budget.charged_cpu_ns + 17


def test_actual_global_cap_not_local_absence(material: Material, path: Path) -> None:
    h = purchases(material)
    before = bind(material, path, h)
    r = reserve(
        "cap",
        phase="comparison",
        cell_id=material.cell,
        operation="candidate_production",
        config_sha256=message_sha256(material.actual.context.candidates.config),
        input_sha256=message_sha256(material.actual.context.candidates),
        cpu_reservation_ns=before.budget.remaining_cpu_ns,
    )
    e = bind(material, path, append(h, r))
    assert before.outcome.status == "incomplete"
    assert e.outcome.status == "cap_limited" and e.outcome.reason == "resource_limit"


def test_genuine_selection_unavailable_preflight(material: Material, path: Path) -> None:
    context = typed(
        NativeEvaluationInput, material.actual.context.model_dump(mode="json") | {"selected": None}
    )
    result = prepare_native_evaluation(context, attempt_id="unselected-preparation")
    assert result.payload.reason == "selection_unavailable"
    h = settled(
        history(material, {f"purchase-{i}" for i in range(12)} | {"candidate"}),
        result.facts,
        material.cell,
    )
    w = StudyEarlyWitnesses(stages=(EarlyPreparationWitness(actual_input=context, result=result),))
    e = bind(material, path, h, w)
    assert e.outcome.status == "failed" and e.stage == "preparation_rejected"
    assert e.outcome.model_sha256 is None and e.outcome.protocol_sha256 is None
    assert material.actual.context.selected is not None
    progressed = StudyEarlyWitnesses(
        stages=(
            *w.stages,
            EarlySelectionWitness(
                candidate_attempt_id="candidate", selected=material.actual.context.selected
            ),
        )
    )
    e = bind(material, path, h, progressed)
    assert e.outcome.status == "incomplete" and e.stage == "preparation_unavailable"


@pytest.mark.parametrize("empty", [False, True])
def test_real_no_completed_result_vs_absence(material: Material, path: Path, empty: bool) -> None:
    if empty:
        sql(path, "DELETE FROM experiments")
        h = purchases(material, 0)
    else:
        with sqlite3.connect(path) as db:
            for identity, body in db.execute(
                "SELECT operation_id,record_json FROM experiments"
            ).fetchall():
                data = json.loads(body)
                data.update(status="failed", trajectory=None, error="simulation_failed")
                db.execute(
                    "UPDATE experiments SET record_json=? WHERE operation_id=?",
                    (json.dumps(data), identity),
                )
        h = purchases(material)
    manifest = ledger.study_manifest(h)
    catalog = _artifact(manifest, material.artifacts, "world_catalog", c.NativeWorldCatalog)
    actual_prefix = reconcile_study_journal(
        h, path, catalog=catalog, cell_id=material.cell
    ).snapshot.committed_prefix()
    inp = NativeCandidateInput(
        pool=material.actual.context.candidates.pool,
        config=material.actual.context.candidates.config,
        observations=actual_prefix,
    )
    result = produce_native_candidates(inp, attempt_id="empty-candidate")
    assert result.payload.reason == "no_completed_records"
    h = settled(h, result.facts, material.cell)
    missing = bind(material, path, h)
    e = bind(
        material,
        path,
        h,
        StudyEarlyWitnesses(stages=(EarlyCandidateWitness(actual_input=inp, result=result),)),
    )
    assert missing.stage == "material_recovery" and missing.outcome.status == "incomplete"
    assert e.outcome.status == ("incomplete" if empty else "failed")
    assert e.outcome.model_sha256 is None


def test_explicit_historical_prefix_not_current_success(material: Material, path: Path) -> None:
    full = material.actual.context.candidates.observations
    prefix = typed(
        ObservationBundle,
        full.model_dump(mode="json") | {"records": [full.records[0].model_dump(mode="json")]},
    )
    inp = NativeCandidateInput(
        pool=material.actual.context.candidates.pool,
        config=material.actual.context.candidates.config,
        observations=prefix,
    )
    result = produce_native_candidates(inp, attempt_id="historical")
    h = settled(purchases(material), result.facts, material.cell)
    e = bind(
        material,
        path,
        h,
        StudyEarlyWitnesses(stages=(EarlyCandidateWitness(actual_input=inp, result=result),)),
    )
    assert e.historical_attempt_ids == ("historical",)
    assert e.stage == "candidate_unavailable" and e.outcome.status == "incomplete"
    assert e.current_prefix is not None and len(e.current_prefix.records) == 12


@pytest.mark.parametrize("transport", ["missing", "invalid"])
def test_partial_prediction_transport_retains_measurement(
    material: Material, path: Path, transport: str
) -> None:
    h = history(
        material,
        {f"purchase-{i}" for i in range(12)} | {"candidate", "preparation", "prediction-0"},
    )
    w = witnesses(material, prepared=True, count=1).model_dump(mode="json")
    w["stages"][-1].update(transport=transport, result=None)
    e = bind(material, path, h, typed(StudyEarlyWitnesses, w))
    assert e.missing_result_attempt_ids == ("prediction-0",)
    assert e.stage == "material_recovery" and e.budget == ledger.summarize_study(h).budget


def test_classical_cannot_supply_missing_native_score(joint: JointMaterial, tmp_path: Path) -> None:
    path = tmp_path / "journal.db"
    path.write_bytes(joint.native.journal_bytes)
    path.chmod(0o600)
    h = history(joint.native, {f"purchase-{i}" for i in range(12)} | {"candidate"})
    h = terminal(append(h, reservation(joint)), joint.result)
    w = StudyEarlyWitnesses(
        stages=(EarlyDiagnosticWitness(actual_input=joint.actual, result=joint.result),)
    )
    e = early.reconcile_study_early_stop(
        raw(h),
        path,
        cell_id=joint.native.cell,
        materials=joint.native.artifacts
        | {"classical_diagnostic_config": raw(joint.actual.config)},
        witnesses_raw=raw(w),
    )
    assert e.outcome.status == "incomplete" and e.outcome.report_sha256 is None
    assert e.witnesses.stages[0].kind == "classical_diagnostic"


def test_exact_original_receipt_after_unrelated_append(material: Material, path: Path) -> None:
    h = purchases(material)
    w = StudyEarlyWitnesses(stages=())
    p = propose(material, path, h, w)
    r = reserve("unrelated")
    later = append(append(p.ledger, r), update(r))
    replay = propose(
        material,
        path,
        later,
        w,
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
        original_ledger_raw=raw(h),
        original_evidence_raw=p.evidence_raw,
    )
    assert replay.replayed and replay.ledger == later
    assert raw(replay.receipt) == raw(p.receipt)
    assert replay.evidence.budget != ledger.summarize_study(later).budget
    assert parse_study_early_evidence(p.evidence_raw) == p.evidence


@pytest.mark.parametrize(
    "case", ["ledger", "evidence", "both", "raw", "witness_raw", "prefix", "revision", "head"]
)
def test_replay_and_fresh_cas_fail_closed(material: Material, path: Path, case: str) -> None:
    h = purchases(material)
    w = StudyEarlyWitnesses(stages=())
    p = propose(material, path, h, w)
    args: dict[str, Any] = dict(
        expected_revision=len(h.records),
        expected_head_sha256=message_sha256(h.records[-1]),
        original_ledger_raw=raw(h),
        original_evidence_raw=p.evidence_raw,
    )
    if case in {"ledger", "both"}:
        args["original_ledger_raw"] = None
    if case in {"evidence", "both"}:
        args["original_evidence_raw"] = None
    if case == "raw":
        args["original_evidence_raw"] = b" " + p.evidence_raw
    if case == "witness_raw":
        args["witnesses_raw"] = b" " + raw(w)
    if case == "prefix":
        args["original_ledger_raw"] = raw(p.ledger)
    if case == "revision":
        args["expected_revision"] = True
    if case == "head":
        args["expected_head_sha256"] = "a" * 64
    with pytest.raises(ledger.StudyLedgerError):
        propose(material, path, p.ledger, w, **args)


@pytest.mark.parametrize("case", ["pool", "engine", "prefix", "facts", "duplicate"])
def test_actual_stage_substitution_rejects(material: Material, path: Path, case: str) -> None:
    h = history(material, {f"purchase-{i}" for i in range(12)} | {"candidate"})
    data = witnesses(material).model_dump(mode="json")
    w = data["stages"][0]
    if case == "pool":
        w["actual_input"]["pool"]["coefficients"] = [2.0]
    if case == "engine":
        w["actual_input"]["observations"]["engine_fingerprint"] = "a" * 64
    if case == "prefix":
        w["actual_input"]["observations"]["records"] = []
    if case == "facts":
        w["result"]["facts"]["attempt_id"] = "other"
    if case == "duplicate":
        data["stages"].append(w)
    with pytest.raises((ledger.StudyLedgerError, ValueError)):
        bind(material, path, h, typed(StudyEarlyWitnesses, data))


@pytest.mark.parametrize(
    "body", [b'{"stages":[],"stages":[]}', b'{"stages":NaN}', b'{"stages":Infinity}', b"[]"]
)
def test_strict_witness_parser(body: bytes) -> None:
    with pytest.raises((ContractViolation, ValueError)):
        parse_study_early_witnesses(body)


def test_no_numerical_rerun_and_raw_journal_race(
    material: Material, path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import strange_physics.native_candidates as candidates
    import strange_physics.native_prediction as prediction
    import strange_physics.native_scoring as scoring

    def no(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("numerical execution")

    monkeypatch.setattr(candidates, "produce_native_candidates", no)
    monkeypatch.setattr(prediction, "predict_native_spring", no)
    monkeypatch.setattr(scoring, "score_native_predictions", no)
    h = history(
        material,
        {f"purchase-{i}" for i in range(12)} | {"candidate", "preparation", "prediction-0"},
    )
    w = witnesses(material, prepared=True, count=1)
    e = bind(material, path, h, w)
    assert e.stage == "predictions_unavailable"
    original = early._Stages.bind

    def changed(self: Any, supplied: StudyEarlyWitnesses) -> None:
        original(self, supplied)
        sql(path, "UPDATE experiments SET request_json=' '||request_json WHERE ordinal=0")

    monkeypatch.setattr(early._Stages, "bind", changed)
    with pytest.raises(ledger.StudyLedgerError, match="journal_changed"):
        bind(material, path, h, w)


def test_schema_generated_and_private_roots() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "contracts/native-study-early.schema.json").read_text())
    assert schema == study_early_json_schema()
    assert schema["x-private-roots"] == ["StudyEarlyWitnesses", "StudyEarlyEvidence"]


@pytest.mark.parametrize("selected", [False, True])
def test_new_candidate_after_old_preflight_is_not_hidden(
    material: Material, path: Path, selected: bool
) -> None:
    context = typed(
        NativeEvaluationInput, material.actual.context.model_dump(mode="json") | {"selected": None}
    )
    rejected = prepare_native_evaluation(context, attempt_id="old-preparation")
    h = settled(
        history(material, {f"purchase-{i}" for i in range(12)} | {"candidate"}),
        rejected.facts,
        material.cell,
    )
    fresh = produce_native_candidates(context.candidates, attempt_id="fresh-candidate")
    h = settled(h, fresh.facts, material.cell)
    from test_native_spring_contracts import selection

    stages: list[Any] = [
        EarlyPreparationWitness(actual_input=context, result=rejected),
        EarlyCandidateWitness(actual_input=context.candidates, result=fresh),
    ]
    if selected:
        stages.append(
            EarlySelectionWitness(candidate_attempt_id="fresh-candidate", selected=selection(fresh))
        )
    e = bind(material, path, h, StudyEarlyWitnesses(stages=tuple(stages)))
    assert e.outcome.status == "incomplete"
    assert e.stage == ("preparation_unavailable" if selected else "selection_unavailable")
    assert len(e.attempts) == 15


def test_real_prediction_retry_keeps_both_results(material: Material, path: Path) -> None:
    from strange_physics.native_prediction import predict_native_spring
    from strange_physics.native_prediction_contracts import NativePredictionInput

    context = material.actual.context
    protocol = material.actual.preparation.payload.protocol
    assert context.selected is not None and protocol is not None
    predicted = predict_native_spring(
        NativePredictionInput(
            model=context.selected.model,
            candidate_config=context.candidates.config,
            request=protocol.probes[0].request,
            config=context.prediction_config,
        ),
        attempt_id="prediction-again",
    )
    h = history(
        material,
        {f"purchase-{i}" for i in range(12)} | {"candidate", "preparation", "prediction-0"},
    )
    h = settled(h, predicted.facts, material.cell)
    base = witnesses(material, prepared=True, count=1)
    w = StudyEarlyWitnesses(
        stages=(
            *base.stages,
            EarlyPredictionWitness(
                preparation_attempt_id="preparation",
                attempt_id="prediction-again",
                probe_id=protocol.probes[0].probe_id,
                transport="result",
                result=predicted,
            ),
        )
    )
    e = bind(material, path, h, w)
    assert not e.missing_result_attempt_ids
    assert e.stage == "predictions_unavailable" and len(e.attempts) == 16
    assert e.budget == ledger.summarize_study(h).budget


@pytest.mark.parametrize("state", ["reserved", "running", "unknown"])
def test_unfinished_scoring_does_not_invent_report(
    material: Material, path: Path, state: Literal["reserved", "running", "unknown"]
) -> None:
    h = history(
        material,
        {f"purchase-{i}" for i in range(12)}
        | {"candidate", "preparation"}
        | {f"prediction-{i}" for i in range(24)},
    )
    f = material.result.facts
    r = reserve(
        f.attempt_id,
        phase="comparison",
        cell_id=material.cell,
        operation="scoring",
        config_sha256=f.config_sha256,
        input_sha256=f.input_sha256,
        cpu_reservation_ns=17,
    )
    h = append(h, r)
    if state != "reserved":
        h = append(
            h,
            c.StudyAttemptUpdate(
                attempt_id=r.attempt_id,
                state=state,
                cpu_ns=23,
                wall_ns=30,
                artifact_bytes=4,
                facts=None,
            ),
        )
    e = bind(material, path, h, witnesses(material, prepared=True, count=24))
    assert e.stage == "scoring_unavailable" and e.outcome.report_sha256 is None
    assert e.outcome.status == "incomplete" and e.budget == ledger.summarize_study(h).budget


def test_witness_and_material_caps_precede_parsing(material: Material, path: Path) -> None:
    from strange_physics.study_early_contracts import MAX_EARLY_WITNESS_BYTES

    valid = raw(StudyEarlyWitnesses(stages=()))
    at = valid + b" " * (MAX_EARLY_WITNESS_BYTES - len(valid))
    assert parse_study_early_witnesses(at).stages == ()
    with pytest.raises(ContractViolation):
        parse_study_early_witnesses(at + b" ")
    with pytest.raises(ledger.StudyLedgerError, match="native_material_limit"):
        early.reconcile_study_early_stop(
            b"not json",
            path,
            cell_id=material.cell,
            materials={"pool": b"x" * (c.MAX_STUDY_JSON_BYTES + 1)},
            witnesses_raw=b"not json",
        )
    with pytest.raises((ContractViolation, ValueError)):
        parse_study_early_witnesses(b'{"stages":' + b"[" * 41 + b"0" + b"]" * 41 + b"}")


def test_actual_journal_creation_race_rejects(
    material: Material, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "not-yet.db"
    original = early._Stages.bind

    def created(self: Any, supplied: StudyEarlyWitnesses) -> None:
        original(self, supplied)
        target.write_bytes(material.journal_bytes)
        target.chmod(0o600)
        sql(target, "DELETE FROM experiments")

    monkeypatch.setattr(early._Stages, "bind", created)
    with pytest.raises(ledger.StudyLedgerError, match="journal_changed"):
        bind(material, target, purchases(material, 0))


@pytest.mark.parametrize("variant", ["exact", "post_impulse", "zero_impulse"])
def test_actual_failed_purchase_overlap_is_retained(
    material: Material, path: Path, variant: str
) -> None:
    from test_native_spring_contracts import selection

    from strange_physics.contracts import Experiment

    protocol = material.actual.preparation.payload.protocol
    assert protocol is not None
    data = protocol.probes[7 if variant == "zero_impulse" else 6].request.experiment.model_dump(
        mode="json"
    )
    if variant == "post_impulse":
        particle, impulse = data["particles"][0], data["impulse"]["vector"]
        particle["velocity"] = [
            v + j / particle["mass"] for v, j in zip(particle["velocity"], impulse, strict=True)
        ]
        data["impulse"] = None
    elif variant == "zero_impulse":
        data["impulse"] = {"particle_id": data["particles"][0]["id"], "vector": [-0.0, 0.0]}
    experiment = typed(Experiment, data)
    with sqlite3.connect(path) as db:
        row = json.loads(
            db.execute("SELECT record_json FROM experiments WHERE ordinal=11").fetchone()[0]
        )
        row["experiment"] = data
        db.execute(
            "UPDATE experiments SET request_json=?,record_json=? WHERE ordinal=11",
            (raw(experiment).decode(), json.dumps(row)),
        )
    hd = purchases(material).model_dump(mode="json")
    for record in hd["records"]:
        event = record["event"]
        if event["kind"] == "reserve" and event["attempt_id"] == "purchase-11":
            event["purchase"]["experiment_sha256"] = message_sha256(experiment)
    h = rechain(hd)
    catalog = _artifact(
        ledger.study_manifest(h), material.artifacts, "world_catalog", c.NativeWorldCatalog
    )
    prefix = reconcile_study_journal(
        h, path, catalog=catalog, cell_id=material.cell
    ).snapshot.committed_prefix()
    actual = NativeCandidateInput(
        pool=material.actual.context.candidates.pool,
        config=material.actual.context.candidates.config,
        observations=prefix,
    )
    produced = produce_native_candidates(actual, attempt_id="overlap-candidate")
    assert produced.payload.status == "produced"
    context = NativeEvaluationInput(
        candidates=actual,
        candidate_result=produced,
        candidate_attempt_id="overlap-candidate",
        selected=selection(produced),
        policy=material.actual.context.policy,
        prediction_config=material.actual.context.prediction_config,
    )
    rejected = prepare_native_evaluation(context, attempt_id="overlap-preparation")
    assert rejected.payload.reason == "purchased_overlap"
    h = settled(settled(h, produced.facts, material.cell), rejected.facts, material.cell)
    e = bind(
        material,
        path,
        h,
        StudyEarlyWitnesses(
            stages=(EarlyPreparationWitness(actual_input=context, result=rejected),)
        ),
    )
    assert e.stage == "preparation_rejected" and e.outcome.status == "failed"
    assert e.failed_operation_ids == ("operation-11",) and e.outcome.report_sha256 is None
    assert e.witnesses.stages[0].kind == "preparation"
    assert e.witnesses.stages[0].result.payload.overlap_record_index == 11


def test_scored_and_early_evidence_cannot_replace_each_other(
    material: Material, path: Path
) -> None:
    h = purchases(material)
    w = StudyEarlyWitnesses(stages=())
    proposed = propose(material, path, h, w)
    from strange_physics.study_publication_contracts import parse_study_publication_evidence

    with pytest.raises(ValueError):
        parse_study_publication_evidence(proposed.evidence_raw)
    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1] / "contracts/native-study-publication.examples.json"
        ).read_text()
    )
    scored = fixture["valid"]["StudyPublicationEvidence"]
    with pytest.raises(ValueError):
        parse_study_early_evidence(json.dumps(scored).encode())


def test_compact_external_fixtures_match_typed_layers() -> None:
    import copy

    root = Path(__file__).resolve().parents[1]
    f = json.loads((root / "contracts/native-study-early.examples.json").read_text())
    models: dict[str, type[Message]] = {
        "StudyEarlyWitnesses": StudyEarlyWitnesses,
        "StudyEarlyEvidence": StudyEarlyEvidence,
    }
    for name, value in f["valid"].items():
        typed(models[name], value)
    for group in ("schema_negative", "runtime_negative"):
        for mutation in f[group]:
            value = copy.deepcopy(f["valid"][mutation["model"]])
            value[mutation["field"]] = mutation["value"]
            with pytest.raises(ValueError):
                typed(models[mutation["model"]], value)


def test_legacy_menu_preparation_retains_cost_without_native_recovery(
    material: Material, path: Path
) -> None:
    h = purchases(material)
    r = reserve(
        "menu-preparation",
        phase="comparison",
        cell_id=material.cell,
        operation="preparation",
        config_sha256=ledger.study_manifest(h).artifact("menu").sha256,
    )
    h = append(append(h, r), update(r))
    e = bind(material, path, h)
    assert e.stage == "candidate_unavailable"
    assert not e.missing_result_attempt_ids and e.attempts[-1].reservation == r
    assert e.budget == ledger.summarize_study(h).budget


def test_later_opaque_selection_cannot_make_older_rejection_final(
    material: Material, path: Path
) -> None:
    context = typed(
        NativeEvaluationInput, material.actual.context.model_dump(mode="json") | {"selected": None}
    )
    result = prepare_native_evaluation(context, attempt_id="rejected-prepare")
    h = settled(
        history(material, {f"purchase-{i}" for i in range(12)} | {"candidate"}),
        result.facts,
        material.cell,
    )
    manifest = ledger.study_manifest(h)
    selector = manifest.cells[0].selector
    r = reserve(
        "later-selection",
        phase="comparison",
        cell_id=material.cell,
        operation="selection",
        config_sha256=manifest.artifact(ledger.SELECTOR_ARTIFACTS[selector]).sha256,
    )
    h = append(append(h, r), update(r))
    e = bind(
        material,
        path,
        h,
        StudyEarlyWitnesses(stages=(EarlyPreparationWitness(actual_input=context, result=result),)),
    )
    assert e.stage == "selection_unavailable" and e.outcome.status == "incomplete"
    assert e.outcome.model_sha256 is None
    assert e.attempts[-1].latest_update is not None


@pytest.mark.parametrize("order", ["before", "after", "running", "failed", "rejected"])
def test_selection_completion_order_controls_old_failure(
    material: Material, path: Path, order: str
) -> None:
    context = typed(
        NativeEvaluationInput, material.actual.context.model_dump(mode="json") | {"selected": None}
    )
    result = prepare_native_evaluation(context, attempt_id="late-preparation")
    h = history(material, {f"purchase-{i}" for i in range(12)} | {"candidate"})
    manifest = ledger.study_manifest(h)
    selector = manifest.cells[0].selector
    r = reserve(
        "early-reserved-selection",
        phase="comparison",
        cell_id=material.cell,
        operation="selection",
        config_sha256=manifest.artifact(ledger.SELECTOR_ARTIFACTS[selector]).sha256,
    )
    h = append(h, r)
    if order == "before":
        h = append(h, update(r))
    elif order == "running":
        h = append(h, update(r, "running"))
    h = settled(h, result.facts, material.cell)
    if order != "before":
        h = append(h, update(r, order if order in {"failed", "rejected"} else "completed"))
    w = StudyEarlyWitnesses(stages=(EarlyPreparationWitness(actual_input=context, result=result),))
    actual = bind(material, path, h, w)
    proposal = propose(material, path, h, w)
    later_success = order in {"after", "running"}
    assert actual.outcome.status == ("incomplete" if later_success else "failed")
    assert actual.stage == ("selection_unavailable" if later_success else "preparation_rejected")
    assert proposal.evidence == actual and proposal.receipt.event.outcome == actual.outcome
    assert actual.outcome.model_sha256 is None
