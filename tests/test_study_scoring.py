"""Synthetic actual SQLite/material joins; no scientific comparison or publication."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from test_native_spring_contracts import selection
from test_study_journal import catalog, create, experiment, sql
from test_study_ledger import LOCK, append, empty, materials, reserve, update

import strange_physics.evaluation as evaluator
from strange_physics import native_scoring as scoring
from strange_physics import study_contracts as c
from strange_physics import study_ledger as ledger
from strange_physics import study_scoring as binding
from strange_physics.contracts import Experiment, Message
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
)
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativeProbeOutcome,
    NativeScoreOutcome,
    NativeScoreResult,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
    NativeWorkFacts,
)
from strange_physics.research_contracts import EvaluationReport, message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_journal import read_study_journal, reconcile_study_journal
from strange_physics.study_scoring_contracts import (
    StudyNativeScoreEvidence,
    study_scoring_json_schema,
)


def raw(value: Message) -> bytes:
    return canonical_json(value.model_dump(mode="json")).encode()


def typed[M: Message](cls: type[M], data: Any) -> M:
    return cls.model_validate_json(json.dumps(data))


@dataclass(frozen=True)
class Material:
    history: c.NativeStudyLedger
    artifacts: dict[str, bytes]
    actual: NativeScoringInput
    result: NativeScoreResult
    journal_bytes: bytes

    @property
    def cell(self) -> str:
        return ledger.study_manifest(self.history).cells[0].cell_id


def settled(history: c.NativeStudyLedger, facts: NativeWorkFacts, cell: str) -> c.NativeStudyLedger:
    reservation = reserve(
        facts.attempt_id,
        phase="comparison",
        cell_id=cell,
        operation=facts.operation,
        config_sha256=facts.config_sha256,
        input_sha256=facts.input_sha256,
    )
    history = append(history, reservation)
    return append(
        history,
        c.StudyAttemptUpdate(
            attempt_id=facts.attempt_id,
            state=facts.outcome,
            cpu_ns=3,
            wall_ns=7,
            artifact_bytes=1,
            facts=c.NativeWorkFacts.model_validate_json(facts.model_dump_json()),
        ),
    )


def make_material(path: Path) -> Material:
    create(path, ("completed",) * 11 + ("failed",))
    # Synthetic purchased data deliberately differs from every held-out I1 condition.
    request_data = experiment().model_dump(mode="json")
    request_data["particles"][0]["position"] = [0.125, 0.25]
    request = typed(Experiment, request_data)
    with sqlite3.connect(path) as db:
        for identity, record_json in db.execute(
            "SELECT operation_id, record_json FROM experiments"
        ).fetchall():
            record = json.loads(record_json)
            record["experiment"] = request_data
            if record["trajectory"] is not None:
                for frame in record["trajectory"]["frames"]:
                    frame["positions"] = [[0.125, 0.25]]
            db.execute(
                "UPDATE experiments SET request_json=?, record_json=? WHERE operation_id=?",
                (raw(request).decode(), json.dumps(record), identity),
            )
    manifest, artifacts = materials()
    pool = NativeSpringPool(coefficients=(1.0,))
    config = NativeCandidateConfig()
    prediction = NativePredictionConfig()
    policy = NativeScoringPolicy()
    artifacts.update(
        pool=raw(pool),
        candidate_config=raw(config),
        prediction_config=raw(prediction),
        scoring_policy=raw(policy),
    )
    data = manifest.model_dump(mode="json")
    for ref in data["artifacts"]:
        body = artifacts[ref["kind"]]
        ref.update(sha256=hashlib.sha256(body).hexdigest(), byte_count=len(body))
    manifest = typed(c.NativeStudyManifest, data)
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
    cell = manifest.cells[0]
    for index in range(12):
        reservation = reserve(
            f"purchase-{index}",
            phase="comparison",
            cell_id=cell.cell_id,
            operation="purchase",
            config_sha256=manifest.artifact("calibration" if index < 4 else "menu").sha256,
            purchase=dict(
                operation_id=f"operation-{index}",
                ordinal=index,
                experiment_sha256=message_sha256(request),
                calibration=index < 4,
            ),
        )
        history = append(append(history, reservation), update(reservation))
    snapshot = read_study_journal(path, manifest=manifest, catalog=catalog(), cell_id=cell.cell_id)
    candidate = NativeCandidateInput(
        pool=pool, config=config, observations=snapshot.committed_prefix()
    )
    produced = produce_native_candidates(candidate, attempt_id="candidate")
    context = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=produced,
        candidate_attempt_id="candidate",
        selected=selection(produced),
        policy=policy,
        prediction_config=prediction,
    )
    preparation = scoring.prepare_native_evaluation(context, attempt_id="preparation")
    protocol = preparation.payload.protocol
    assert protocol is not None and context.selected is not None
    entries = tuple(
        NativeProbeOutcome(
            probe_id=probe.probe_id,
            request_sha256=probe.request_sha256,
            attempt_id=f"prediction-{index}",
            status="result",
            result=predict_native_spring(
                NativePredictionInput(
                    model=context.selected.model,
                    candidate_config=config,
                    request=probe.request,
                    config=prediction,
                ),
                attempt_id=f"prediction-{index}",
            ),
        )
        for index, probe in enumerate(protocol.probes)
    )
    actual = NativeScoringInput(
        context=context,
        preparation=preparation,
        predictions=NativePredictionCollection(entries=entries),
        world=catalog().worlds[0].definition,
    )
    result = scoring.score_native_predictions(actual, attempt_id="scoring")
    history = settled(history, produced.facts, cell.cell_id)
    history = settled(history, preparation.facts, cell.cell_id)
    for entry in entries:
        assert entry.result is not None
        history = settled(history, entry.result.facts, cell.cell_id)
    history = settled(history, result.facts, cell.cell_id)
    return Material(
        history,
        {key: artifacts[key] for key in binding.NATIVE_MATERIAL_KINDS},
        actual,
        result,
        path.read_bytes(),
    )


@pytest.fixture(scope="module")
def material(tmp_path_factory: pytest.TempPathFactory) -> Material:
    return make_material(tmp_path_factory.mktemp("bound-native") / "journal.db")


@pytest.fixture
def path(tmp_path: Path, material: Material) -> Path:
    value = tmp_path / "journal.db"
    value.write_bytes(material.journal_bytes)
    value.chmod(0o600)
    return value


def bind(value: Material, path: Path, **changes: Any) -> StudyNativeScoreEvidence:
    args: dict[str, Any] = dict(
        cell_id=value.cell,
        materials=value.artifacts,
        scoring_input_raw=raw(value.actual),
        scoring_result_raw=raw(value.result),
    )
    args.update(changes)
    return binding.reconcile_native_study_score(raw(value.history), path, **args)


def rechain(value: dict[str, Any]) -> c.NativeStudyLedger:
    prior = message_sha256(typed(c.NativeAccountingPlan, value["plan"]))
    for i, record in enumerate(value["records"]):
        record["sequence"] = i
        record["previous_sha256"] = prior
        prior = message_sha256(typed(c.StudyLedgerRecord, record))
    return typed(c.NativeStudyLedger, value)


def changed_history(value: Material, history: c.NativeStudyLedger) -> Material:
    return Material(history, value.artifacts, value.actual, value.result, value.journal_bytes)


def test_actual_journal_full_native_and_measurement_joins(material: Material, path: Path) -> None:
    before = raw(material.history), path.read_bytes()
    result = bind(material, path)
    assert result.score == material.result
    assert result.failed_purchase_operation_ids == ("operation-11",)
    assert len(result.attempts) == 27 and not result.unresolved_cell_attempt_ids
    assert result.budget == ledger.summarize_study(material.history).budget
    assert result.journal_raw_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (raw(material.history), path.read_bytes()) == before
    assert all(
        cell.status == ("in_progress" if i == 0 else "unstarted")
        for i, cell in enumerate(ledger.summarize_study(material.history).cells)
    )
    assert not hasattr(result, "complete") and not hasattr(result, "world")


@pytest.mark.parametrize(
    "case", ["pending", "missing", "extra", "wrong_operation", "world", "engine"]
)
def test_actual_journal_never_replaced_by_claimed_input(
    material: Material, path: Path, case: str
) -> None:
    if case == "pending":
        sql(path, "UPDATE experiments SET record_json=NULL WHERE ordinal=5")
    elif case == "missing":
        sql(path, "DELETE FROM experiments WHERE ordinal=11")
    elif case == "extra":
        sql(path, "UPDATE experiments SET ordinal=12 WHERE ordinal=11")
    elif case == "wrong_operation":
        sql(path, "UPDATE experiments SET operation_id='other' WHERE ordinal=5")
    elif case == "world":
        d = material.actual.world.model_dump(mode="json")
        d["space"]["structure"]["anchors"][0]["position"][0] = -0.0
        sql(path, "UPDATE run SET world_json=?", (json.dumps(d),))
    else:
        sql(path, "UPDATE run SET engine_fingerprint=?", ("f" * 64,))
    with pytest.raises(ValueError):
        bind(material, path)


@pytest.mark.parametrize(
    "part", ["pool", "candidate_config", "prediction_config", "scoring_policy", "world_catalog"]
)
def test_frozen_artifact_bytes_are_actual(material: Material, path: Path, part: str) -> None:
    artifacts = material.artifacts | {part: material.artifacts[part] + b" "}
    with pytest.raises(ledger.StudyLedgerError, match="artifact_identity_mismatch"):
        bind(material, path, materials=artifacts)


@pytest.mark.parametrize("field", ["context", "world", "preparation", "predictions"])
def test_coherent_private_input_substitution_rejected(
    material: Material, path: Path, field: str
) -> None:
    d = material.actual.model_dump(mode="json")
    if field == "context":
        d[field]["candidates"]["observations"]["space"]["structure"]["anchors"][0]["position"][
            0
        ] = -0.0
    elif field == "world":
        d[field]["noise_seed"] += 1
    elif field == "preparation":
        d[field]["facts"]["attempt_id"] = "foreign"
    else:
        d[field]["entries"][0]["attempt_id"] = "foreign"
        d[field]["entries"][0]["result"]["facts"]["attempt_id"] = "foreign"
    with pytest.raises(ValueError):
        bind(material, path, scoring_input_raw=json.dumps(d).encode())


@pytest.mark.parametrize("case", ["candidate", "preparation", "scoring", "prediction-0"])
def test_present_results_require_actual_terminal_measurements(
    material: Material, path: Path, case: str
) -> None:
    d = material.history.model_dump(mode="json")
    for record in d["records"]:
        e = record["event"]
        if e["kind"] == "update" and e["attempt_id"] == case:
            e.update(state="unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None, facts=None)
    history = rechain(d)
    held = ledger.summarize_study(history).budget
    assert held.unresolved_attempts == 1
    with pytest.raises(ledger.StudyLedgerError, match="native_result_measurement_unresolved"):
        bind(changed_history(material, history), path)
    assert ledger.summarize_study(history).budget == held


def test_menu_preparation_cannot_impersonate_evaluation(material: Material, path: Path) -> None:
    d = material.history.model_dump(mode="json")
    menu = ledger.study_manifest(material.history).artifact("menu").sha256
    for record in d["records"]:
        e = record["event"]
        if e.get("attempt_id") == "preparation":
            if e["kind"] == "reserve":
                e["config_sha256"] = menu
            else:
                e["facts"]["config_sha256"] = menu
    history = rechain(d)
    ledger.read_study_ledger(raw(history))
    with pytest.raises(ledger.StudyLedgerError, match="native_attempt_mismatch"):
        bind(changed_history(material, history), path)


def test_retained_score_timing_is_bound_without_numerical_rerun(
    material: Material, path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = material.result.model_dump(mode="json")
    e = data["payload"]["evaluation"]
    e["report"]["evaluation_runtime_ms"] += 1
    e["diagnostics"]["evaluation_runtime_ms"] = e["report"]["evaluation_runtime_ms"]
    e["report_sha256"] = message_sha256(typed(EvaluationReport, e["report"]))
    data["facts"]["output_sha256"] = message_sha256(typed(NativeScoreOutcome, data["payload"]))
    result = typed(NativeScoreResult, data)
    d = material.history.model_dump(mode="json")
    for record in d["records"]:
        if record["event"]["kind"] == "update" and record["event"]["attempt_id"] == "scoring":
            record["event"]["facts"] = result.facts.model_dump(mode="json")
    value = Material(
        rechain(d), material.artifacts, material.actual, result, material.journal_bytes
    )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Binder must not rerun the evaluator")

    monkeypatch.setattr(scoring, "evaluate_spring_predictions", forbidden)
    assert bind(value, path).score == result


def rescored(value: Material, actual: NativeScoringInput, result: NativeScoreResult) -> Material:
    data = value.history.model_dump(mode="json")
    for record in data["records"]:
        event = record["event"]
        if event.get("attempt_id") == "scoring":
            if event["kind"] == "reserve":
                event["input_sha256"] = message_sha256(actual)
            else:
                event.update(state=result.facts.outcome, facts=result.facts.model_dump(mode="json"))
    return Material(rechain(data), value.artifacts, actual, result, value.journal_bytes)


@pytest.mark.parametrize("transport", ["missing", "invalid"])
@pytest.mark.parametrize("state", ["reserved", "running", "unknown", "completed"])
def test_missing_transport_preserves_actual_cost_and_unknown_hold(
    material: Material, path: Path, transport: str, state: str
) -> None:
    data = material.actual.model_dump(mode="json")
    data["predictions"]["entries"][12].update(status=transport, result=None)
    actual = typed(NativeScoringInput, data)
    result = scoring.score_native_predictions(actual, attempt_id="scoring")
    value = rescored(material, actual, result)
    events = value.history.model_dump(mode="json")
    for record in list(events["records"]):
        event = record["event"]
        if event["kind"] == "update" and event["attempt_id"] == "prediction-12":
            if state == "reserved":
                events["records"].remove(record)
            elif state != "completed":
                event.update(state=state, facts=None)
    value = changed_history(value, rechain(events))
    bound = bind(value, path)
    attempt = bound.attempts[14]
    assert attempt.state == state
    assert attempt.known_cpu_ns == (None if state == "reserved" else 3)
    assert bound.score.payload.evaluation is not None
    assert bound.score.payload.evaluation.status == "unscorable"
    assert bound.score.facts.completed_count == 1
    assert ("prediction-12" in bound.unresolved_cell_attempt_ids) == (state != "completed")
    assert bound.budget == ledger.summarize_study(value.history).budget


def test_null_update_keeps_known_measurement_and_unrelated_unresolved_attempt(
    material: Material, path: Path
) -> None:
    data = material.actual.model_dump(mode="json")
    data["predictions"]["entries"][0].update(status="missing", result=None)
    actual = typed(NativeScoringInput, data)
    value = rescored(
        material, actual, scoring.score_native_predictions(actual, attempt_id="scoring")
    )
    d = value.history.model_dump(mode="json")
    for record in d["records"]:
        event = record["event"]
        if event["kind"] == "update" and event["attempt_id"] == "prediction-0":
            event.update(state="running", facts=None)
    history = rechain(d)
    history = append(
        history,
        c.StudyAttemptUpdate(
            attempt_id="prediction-0",
            state="unknown",
            cpu_ns=None,
            wall_ns=None,
            artifact_bytes=None,
            facts=None,
        ),
    )
    history = append(
        history,
        reserve(
            "unrelated-work",
            phase="comparison",
            cell_id=value.cell,
            operation="preparation",
            config_sha256=ledger.study_manifest(history).artifact("menu").sha256,
        ),
    )
    bound = bind(changed_history(value, history), path)
    assert bound.attempts[2].known_cpu_ns == 3
    assert bound.attempts[2].known_wall_ns == 7
    assert bound.attempts[2].known_artifact_bytes == 1
    assert bound.unresolved_cell_attempt_ids == ("prediction-0", "unrelated-work")
    assert bound.budget.unresolved_attempts == 2


@pytest.mark.parametrize("stage", ["reference_failure", "metric_failure"])
def test_no_report_evaluator_failure_retains_actual_stage_and_work(
    material: Material, path: Path, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "_reference_probe" if stage == "reference_failure" else "_probe_mse"
    original = getattr(evaluator, name)
    calls = 0

    def fail(*args: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 13:
            raise ArithmeticError("private injected diagnostic")
        return original(*args)

    monkeypatch.setattr(evaluator, name, fail)
    result = scoring.score_native_predictions(material.actual, attempt_id="scoring")
    value = rescored(material, material.actual, result)
    bound = bind(value, path)
    evaluation = bound.score.payload.evaluation
    assert evaluation is not None and evaluation.reason == stage
    assert evaluation.report is None and evaluation.report_sha256 is None
    assert evaluation.diagnostics.valid_prediction_count == 24
    assert evaluation.diagnostics.failed_prediction_count == 0
    assert bound.score.facts.failed_count == 1
    assert bound.attempts[-1].state == "failed"
    assert "private injected" not in bound.model_dump_json()


@pytest.mark.parametrize(
    "field", ["input_sha256", "config_sha256", "output_sha256", "producer_version"]
)
def test_coherent_terminal_measurements_cannot_substitute_actual_facts(
    material: Material, path: Path, field: str
) -> None:
    d = material.history.model_dump(mode="json")
    for record in d["records"]:
        event = record["event"]
        if event.get("attempt_id") == "prediction-1":
            replacement = "foreign.v1" if field == "producer_version" else "d" * 64
            if event["kind"] == "update":
                event["facts"][field] = replacement
            elif field in ("input_sha256", "config_sha256"):
                event[field] = replacement
    value = changed_history(material, rechain(d))
    with pytest.raises(ledger.StudyLedgerError):
        bind(value, path)


def test_read_boundary_detects_journal_change_during_binding(
    material: Material, path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = reconcile_study_journal
    calls = 0

    def changed(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            sql(path, "UPDATE run SET agent_id='another-agent'")
        return original(*args, **kwargs)

    monkeypatch.setattr(binding, "reconcile_study_journal", changed)
    with pytest.raises(ledger.StudyLedgerError, match="journal_changed"):
        bind(material, path)


@pytest.mark.parametrize("part", ["ledger", "input", "result"])
@pytest.mark.parametrize("bad", ["duplicate", "nonfinite", "oversize"])
def test_strict_raw_boundaries(material: Material, path: Path, part: str, bad: str) -> None:
    payload = {
        "ledger": raw(material.history),
        "input": raw(material.actual),
        "result": raw(material.result),
    }[part]
    if bad == "duplicate":
        body = json.loads(payload)
        key = next(iter(body))
        payload = (
            b"{"
            + json.dumps(key).encode()
            + b":"
            + json.dumps(body[key]).encode()
            + b","
            + payload[1:]
        )
    elif bad == "nonfinite":
        payload = payload[:-1] + b',"unexpected":NaN}'
    else:
        cap = 16 if part == "input" else 8
        payload = b" " * (cap * 1024**2 + 1)
    with pytest.raises(ValueError):
        if part == "ledger":
            binding.reconcile_native_study_score(
                payload,
                path,
                cell_id=material.cell,
                materials=material.artifacts,
                scoring_input_raw=raw(material.actual),
                scoring_result_raw=raw(material.result),
            )
        else:
            bind(material, path, **{f"scoring_{part}_raw": payload})


def test_raw_formatting_identity_distinct_from_typed_canonical(
    material: Material, path: Path
) -> None:
    compact = bind(material, path)
    spaced = bind(
        material,
        path,
        scoring_input_raw=json.dumps(material.actual.model_dump(mode="json"), indent=1).encode(),
    )
    assert compact.scoring_input_identity.raw_sha256 != spaced.scoring_input_identity.raw_sha256
    assert (
        compact.scoring_input_identity.canonical_sha256
        == spaced.scoring_input_identity.canonical_sha256
    )


@pytest.mark.parametrize("kind", ["menu", "scoring_policy"])
def test_explicit_preparation_config_roles(kind: c.ArtifactKind) -> None:
    from test_study_ledger import frozen

    history = frozen()
    manifest = ledger.study_manifest(history)
    history = append(
        history,
        reserve(
            "prepare",
            phase="comparison",
            cell_id=manifest.cells[0].cell_id,
            operation="preparation",
            config_sha256=manifest.artifact(kind).sha256,
        ),
    )
    assert ledger.study_cell_attempts(history, manifest.cells[0].cell_id)[0].state == "reserved"


def test_arbitrary_preparation_config_rejected() -> None:
    from test_study_ledger import frozen

    history = frozen()
    with pytest.raises(ledger.StudyLedgerError):
        append(
            history,
            reserve(
                "prepare",
                phase="comparison",
                cell_id=ledger.study_manifest(history).cells[0].cell_id,
                operation="preparation",
                config_sha256="f" * 64,
            ),
        )


def test_optional_classical_role_and_exact_attempt_config_preserve_legacy_bytes() -> None:
    from test_study_contracts import EXAMPLES
    from test_study_ledger import frozen

    original = c.NativeStudyManifest.model_validate_json(
        json.dumps(EXAMPLES["valid"]["NativeStudyManifest"])
    )
    assert len(original.artifacts) == 15
    assert raw(original) == canonical_json(EXAMPLES["valid"]["NativeStudyManifest"]).encode()
    old = frozen()
    with pytest.raises(ledger.StudyLedgerError, match="diagnostic_configuration_missing"):
        append(
            old,
            reserve(
                "diagnostic",
                phase="comparison",
                cell_id=ledger.study_manifest(old).cells[0].cell_id,
                operation="classical_diagnostic",
                config_sha256="f" * 64,
            ),
        )
    manifest, artifacts = materials()
    body = b'{"explicit":"synthetic diagnostic bundle"}'
    artifacts["classical_diagnostic_config"] = body
    d = manifest.model_dump(mode="json")
    d["artifacts"].append(
        dict(
            kind="classical_diagnostic_config",
            sha256=hashlib.sha256(body).hexdigest(),
            byte_count=len(body),
        )
    )
    manifest = typed(c.NativeStudyManifest, d)
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
    accepted = append(
        history,
        reserve(
            "diagnostic",
            phase="comparison",
            cell_id=manifest.cells[0].cell_id,
            operation="classical_diagnostic",
            config_sha256=manifest.artifact("classical_diagnostic_config").sha256,
        ),
    )
    assert len(accepted.records) == 2
    with pytest.raises(ledger.StudyLedgerError):
        append(
            history,
            reserve(
                "diagnostic",
                phase="comparison",
                cell_id=manifest.cells[0].cell_id,
                operation="classical_diagnostic",
                config_sha256=manifest.artifact("prediction_config").sha256,
            ),
        )


def test_owner_only_schema_and_evidence_intrinsic_failures(material: Material, path: Path) -> None:
    value = bind(material, path)
    assert study_scoring_json_schema()["x-owner-only-roots"] == [
        "StudyMaterialIdentity",
        "StudyNativeAttemptEvidence",
        "StudyNativeScoreEvidence",
    ]
    d = value.model_dump(mode="json")
    d["attempts"][2]["reservation"]["attempt_id"] = d["attempts"][3]["reservation"]["attempt_id"]
    with pytest.raises(ValueError):
        typed(StudyNativeScoreEvidence, d)


def test_schema_generation_and_external_fixture_runtime_boundaries() -> None:
    from strange_physics.study_scoring_contracts import STUDY_SCORING_MODELS

    root = Path(__file__).resolve().parents[1] / "contracts"
    assert (
        json.loads((root / "native-study-scoring.schema.json").read_text())
        == study_scoring_json_schema()
    )
    examples = json.loads((root / "native-study-scoring.examples.json").read_text())
    models = {model.__name__: model for model in STUDY_SCORING_MODELS}
    for name, data in examples["valid"].items():
        models[name].model_validate_json(json.dumps(data))
    for group in ("schema_negative", "runtime_negative"):
        for case in examples[group]:
            data = examples["valid"][case["model"]] | {case["field"]: case["value"]}
            with pytest.raises(ValueError):
                models[case["model"]].model_validate_json(json.dumps(data))


@pytest.mark.parametrize("case", ["missing_intent", "unknown_purchase"])
def test_actual_purchases_and_unknown_charges(material: Material, path: Path, case: str) -> None:
    d = material.history.model_dump(mode="json")
    if case == "missing_intent":
        d["records"] = [r for r in d["records"] if r["event"].get("attempt_id") != "purchase-11"]
    else:
        for record in d["records"]:
            event = record["event"]
            if event["kind"] == "update" and event["attempt_id"] == "purchase-11":
                event.update(
                    state="unknown", facts=None, cpu_ns=None, wall_ns=None, artifact_bytes=None
                )
    value = changed_history(material, rechain(d))
    if case == "missing_intent":
        with pytest.raises(ledger.StudyLedgerError, match="untracked_purchase"):
            bind(value, path)
    else:
        bound = bind(value, path)
        assert bound.unresolved_cell_attempt_ids == ("purchase-11",)
        assert bound.budget.unresolved_attempts == 1 and bound.budget.purchased_slots == 12
        assert ledger.summarize_study(value.history).cells[0].status == "in_progress"


@pytest.mark.parametrize("case", ["duplicate", "reordered", "unknown"])
def test_optional_role_is_unique_and_exactly_ordered(case: str) -> None:
    manifest = materials()[0]
    d = manifest.model_dump(mode="json")
    ref = dict(kind="classical_diagnostic_config", sha256="f" * 64, byte_count=2)
    if case == "duplicate":
        d["artifacts"].extend([ref, ref])
    elif case == "reordered":
        d["artifacts"].insert(0, ref)
    else:
        ref["kind"] = "other_config"
        d["artifacts"].append(ref)
    with pytest.raises(ValueError):
        typed(c.NativeStudyManifest, d)


def test_unavailable_preparation_does_not_invent_probe_attempts(
    material: Material, path: Path
) -> None:
    data = material.actual.model_dump(mode="json")
    context_data = data["context"]
    context_data["selected"] = None
    context = typed(NativeEvaluationInput, context_data)
    preparation = scoring.prepare_native_evaluation(context, attempt_id="preparation")
    data["context"] = context.model_dump(mode="json")
    data["preparation"] = preparation.model_dump(mode="json")
    # Actual core preflight does not inspect/evaluate downstream entries.
    actual = typed(NativeScoringInput, data)
    result = scoring.score_native_predictions(actual, attempt_id="scoring")
    before = ledger.summarize_study(material.history).budget
    with pytest.raises(ledger.StudyLedgerError, match="native_preparation_unavailable"):
        bind(material, path, scoring_input_raw=raw(actual), scoring_result_raw=raw(result))
    assert ledger.summarize_study(material.history).budget == before


@pytest.mark.parametrize("phase", ["reference", "calibration", "sensitivity", "accounting"])
def test_classical_operation_cannot_bypass_frozen_cell_with_generic_phase(phase: str) -> None:
    with pytest.raises(ValueError, match="Classical diagnostics"):
        reserve("classical", phase=phase, operation="classical_diagnostic")
    # Existing generic preparation accounting still starts before final freeze.
    history = append(empty(), reserve("ordinary", phase=phase, operation="preparation"))
    assert ledger.summarize_study(history).budget.unresolved_attempts == 1


def test_classical_comparison_cannot_start_before_actual_manifest_freeze() -> None:
    manifest = materials()[0]
    reservation = reserve(
        "classical",
        phase="comparison",
        cell_id=manifest.cells[0].cell_id,
        operation="classical_diagnostic",
        config_sha256="f" * 64,
    )
    with pytest.raises(ledger.StudyLedgerError, match="unknown_cell"):
        append(empty(), reservation)
