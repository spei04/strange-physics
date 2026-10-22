from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from test_native_spring_contracts import inputs, selection

import strange_physics.evaluation as evaluator
import strange_physics.native_prediction as predictor
import strange_physics.native_scoring as scoring
import strange_physics.native_scoring_contracts as contracts
from strange_physics.bounded_json import bounded_canonical
from strange_physics.control_contracts import ContractViolation
from strange_physics.evaluation_contracts import SpringEvaluationProtocol
from strange_physics.laws import LawSpec
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
)
from strange_physics.native_scoring import (
    prepare_native_evaluation,
    score_native_predictions,
    validate_native_score_result,
)
from strange_physics.native_scoring_contracts import (
    MAX_SCORING_INPUT_BYTES,
    MAX_SCORING_RESULT_BYTES,
    SCORING_MODELS,
    NativeEvaluationInput,
    NativePredictionCollection,
    NativePreparationOutcome,
    NativeProbeOutcome,
    NativeScoreResult,
    NativeScoringInput,
    NativeScoringPolicy,
    native_scoring_json_schema,
    parse_native_evaluation_input,
    parse_native_score_result,
    parse_native_scoring_input,
)
from strange_physics.native_spring_contracts import NativeCandidateInput
from strange_physics.prediction import _state_at_time
from strange_physics.research_contracts import message_sha256
from strange_physics.scientific_workflow import i1_protocol
from strange_physics.study_contracts import NativeWorkFacts as StudyWorkFacts
from strange_physics.worlds import WorldDefinition

ROOT = Path(__file__).resolve().parents[1]


def context(coefficient: float = 1.0) -> NativeEvaluationInput:
    actual = inputs((coefficient,))
    produced = produce_native_candidates(actual, attempt_id="produce")
    return NativeEvaluationInput(
        candidates=actual,
        candidate_result=produced,
        candidate_attempt_id="produce",
        selected=selection(produced),
        policy=NativeScoringPolicy(),
        prediction_config=NativePredictionConfig(),
    )


def material(coefficient: float = 1.0, truth: float = 1.0) -> NativeScoringInput:
    actual = context(coefficient)
    preparation = prepare_native_evaluation(actual, attempt_id="prepare")
    protocol, selected = preparation.payload.protocol, actual.selected
    assert protocol is not None and selected is not None
    outcomes = tuple(
        NativeProbeOutcome(
            probe_id=probe.probe_id,
            request_sha256=probe.request_sha256,
            attempt_id=f"prediction-{index}",
            status="result",
            result=predict_native_spring(
                NativePredictionInput(
                    model=selected.model,
                    candidate_config=actual.candidates.config,
                    request=probe.request,
                    config=actual.prediction_config,
                ),
                attempt_id=f"prediction-{index}",
            ),
        )
        for index, probe in enumerate(protocol.probes)
    )
    return NativeScoringInput(
        context=actual,
        preparation=preparation,
        predictions=NativePredictionCollection(entries=outcomes),
        world=WorldDefinition(
            space=actual.candidates.observations.space,
            noise_seed=7,
            initial_law=LawSpec(kind="spring", parameters={"linear": truth, "cubic": 0.0}),
        ),
    )


def changed_input(actual: NativeScoringInput, data: dict[str, Any]) -> NativeScoringInput:
    return NativeScoringInput.model_validate_json(json.dumps(data))


def rebind_preparation(data: dict[str, Any]) -> None:
    payload = NativePreparationOutcome.model_validate_json(
        json.dumps(data["preparation"]["payload"])
    )
    data["preparation"]["facts"]["output_sha256"] = message_sha256(payload)


def test_real_candidate_to_fixed_protocol_native_predictions_and_independent_score() -> None:
    actual = material()
    prepared = actual.preparation
    assert actual.context.selected is not None and prepared.payload.protocol is not None
    expected = i1_protocol(
        actual.context.selected.model, actual.context.candidates.observations.space.structure
    )
    assert message_sha256(prepared.payload.protocol) == message_sha256(expected)
    result = score_native_predictions(actual, attempt_id="score")
    validate_native_score_result(result, actual, attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == "scored" and e.report is not None
    assert e.report.position_mse is not None and e.report.position_mse < 1e-24
    assert e.report_sha256 == message_sha256(e.report)
    assert e.diagnostics.valid_prediction_count == e.diagnostics.computed_metric_count == 24
    assert result.facts.unit == "work" and result.facts.completed_count == 1
    assert e.reference is not None and len(e.reference.probes) == 24
    assert result.facts.output_sha256 == message_sha256(result.payload)
    assert result.facts.input_sha256 == message_sha256(actual)
    assert result.facts.config_sha256 == message_sha256(actual.context.policy)
    for facts in (prepared.facts, result.facts):
        mirrored = StudyWorkFacts.model_validate_json(facts.model_dump_json())
        assert message_sha256(mirrored) == message_sha256(facts)


def test_poor_valid_score_is_retained_without_fixture_threshold_or_candidate_switch() -> None:
    actual = material(coefficient=4.0, truth=0.0)
    result = score_native_predictions(actual, attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == "scored" and e.report is not None
    assert e.report.position_mse is not None and e.report.position_mse > 0.001
    assert actual.context.selected is not None
    assert result.payload.model_sha256 == actual.context.selected.model_sha256
    assert result.facts.outcome == "completed"
    assert "target_passed" not in result.model_dump_json()


@pytest.mark.parametrize("status", ["missing", "invalid"])
@pytest.mark.parametrize("index", [0, 12, 23])
def test_all_ordered_prediction_failures_remain_distinct_and_unscorable(
    status: str, index: int
) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    data["predictions"]["entries"][index].update(status=status, result=None)
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == "unscorable" and e.report is not None
    assert e.probes[index].prediction_status == status
    assert e.diagnostics.valid_prediction_count == 23
    assert e.diagnostics.failed_prediction_count == 1
    assert e.report.position_mse is None and e.report.normalized_position_mse is None
    assert e.reference is None and e.diagnostics.computed_metric_count == 0
    assert result.facts.completed_count == 1 and result.facts.failed_count == 0


def test_actual_failed_native_prediction_keeps_its_computed_prefix_and_probe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    assert actual.preparation.payload.protocol is not None
    probe = actual.preparation.payload.protocol.probes[0]
    selected = actual.context.selected
    assert selected is not None
    original = _state_at_time

    def fail(model: Any, request: Any, time: float) -> Any:
        if time == probe.request.times[2]:
            raise ArithmeticError("private injected detail")
        return original(model, request, time)

    monkeypatch.setattr(predictor, "_state_at_time", fail)
    failed = predict_native_spring(
        NativePredictionInput(
            model=selected.model,
            candidate_config=actual.context.candidates.config,
            request=probe.request,
            config=actual.context.prediction_config,
        ),
        attempt_id="prediction-0",
    )
    assert failed.facts.completed_count == 2 and failed.facts.failed_count == 1
    data = actual.model_dump(mode="json")
    data["predictions"]["entries"][0]["result"] = failed.model_dump(mode="json")
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    assert result.payload.evaluation is not None
    assert result.payload.evaluation.probes[0].prediction_status == "failed"
    assert result.facts.completed_count == 1
    assert "private injected detail" not in result.model_dump_json()


@pytest.mark.parametrize("stage", ["unsupported_world", "reference_failure", "metric_failure"])
def test_whole_evaluator_failure_never_relabels_valid_predictions(
    stage: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    if stage == "unsupported_world":
        data = actual.model_dump(mode="json")
        data["world"]["initial_law"]["parameters"]["cubic"] = 0.1
        actual = changed_input(actual, data)
    else:
        name = "_reference_probe" if stage == "reference_failure" else "_probe_mse"
        original = getattr(evaluator, name)
        calls = 0

        def fail(*args: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 13:
                raise ArithmeticError("private numerical detail")
            return original(*args)

        monkeypatch.setattr(evaluator, name, fail)
    result = score_native_predictions(actual, attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.reason == stage and e.report is None
    assert e.diagnostics.valid_prediction_count == 24
    assert e.diagnostics.failed_prediction_count == e.diagnostics.prediction_not_assessed_count == 0
    assert result.facts.failed_count == 1 and result.facts.completed_count == 0
    if stage == "reference_failure":
        assert e.diagnostics.reference_completed_probe_count == 12
        assert e.diagnostics.reference_failed_probe_index == 12
    if stage == "metric_failure":
        assert e.diagnostics.computed_metric_count == 12
        assert e.reference is not None
    assert "private numerical detail" not in result.model_dump_json()


@pytest.mark.parametrize("change", ["failed_purchase", "attempt", "selection", "prefix", "empty"])
def test_preparation_binds_actual_failed_purchases_selection_prefix_and_producer(
    change: str,
) -> None:
    actual = context()
    data = actual.model_dump(mode="json")
    if change == "failed_purchase":
        data["candidates"]["observations"]["records"][1]["operation_id"] = "different"
    elif change == "attempt":
        data["candidate_attempt_id"] = "other"
    elif change == "selection":
        data["selected"] = None
    elif change == "prefix":
        data["candidates"]["observations"]["run_id"] = "other-arm"
    else:
        empty = actual.candidates.model_dump(mode="json")
        empty["observations"]["records"] = []
        candidate = NativeCandidateInput.model_validate_json(json.dumps(empty))
        data["candidates"] = candidate.model_dump(mode="json")
        data["candidate_result"] = produce_native_candidates(
            candidate, attempt_id="produce"
        ).model_dump(mode="json")
        data["selected"] = None
    changed = NativeEvaluationInput.model_validate_json(json.dumps(data))
    result = prepare_native_evaluation(changed, attempt_id="prepare")
    expected = {"selection": "selection_unavailable", "empty": "candidate_unavailable"}.get(
        change, "candidate_mismatch"
    )
    assert result.payload.reason == expected and result.payload.protocol is None
    assert result.facts.not_assessed_count == 1


@pytest.mark.parametrize(
    "variant", ["exact", "post_impulse", "zero_impulse", "reversed", "translated"]
)
def test_failed_purchases_and_equivalent_conditions_reject_without_redrawing(variant: str) -> None:
    actual = context()
    assert actual.selected is not None
    protocol = i1_protocol(actual.selected.model, actual.candidates.observations.space.structure)
    probe = protocol.probes[7 if variant == "zero_impulse" else 6]
    data = actual.candidates.model_dump(mode="json")
    exp = probe.request.experiment.model_dump(mode="json")
    if variant == "post_impulse":
        particle, impulse = exp["particles"][0], exp["impulse"]["vector"]
        particle["velocity"] = [
            v + j / particle["mass"] for v, j in zip(particle["velocity"], impulse, strict=True)
        ]
        exp["impulse"] = None
    elif variant == "zero_impulse":
        exp["impulse"] = {"particle_id": "p", "vector": [-0.0, 0.0]}
    elif variant == "reversed":
        data["observations"]["space"]["structure"]["connections"] = [{"a": "a", "b": "p"}]
    elif variant == "translated":
        data["observations"]["space"]["structure"]["anchors"][0]["position"][0] = 0.25
        exp["particles"][0]["position"][0] += 0.25
    data["observations"]["records"][1]["experiment"] = exp
    candidate = NativeCandidateInput.model_validate_json(json.dumps(data))
    produced = produce_native_candidates(candidate, attempt_id="produce")
    assert produced.payload.status == "produced"
    changed = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=produced,
        selected=selection(produced),
        candidate_attempt_id="produce",
        policy=actual.policy,
        prediction_config=actual.prediction_config,
    )
    result = prepare_native_evaluation(changed, attempt_id="prepare")
    assert result.payload.reason == "purchased_overlap"
    assert result.payload.overlap_record_index == 1 and result.payload.protocol is None
    assert result.facts.outcome == "rejected"


@pytest.mark.parametrize("change", ["time", "order", "request_hash", "model_hash"])
def test_canonical_whole_protocol_recomputation_rejects_coherent_rehash(change: str) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    protocol = data["preparation"]["payload"]["protocol"]
    if change == "time":
        protocol["probes"][0]["request"]["times"][0] = -0.0
    elif change == "order":
        protocol["probes"][0], protocol["probes"][1] = protocol["probes"][1], protocol["probes"][0]
    elif change == "request_hash":
        protocol["probes"][0]["request_sha256"] = "f" * 64
    else:
        protocol["probes"][0]["request"]["model_sha256"] = "f" * 64
    data["preparation"]["payload"]["protocol_sha256"] = message_sha256(
        SpringEvaluationProtocol.model_validate_json(json.dumps(protocol))
    )
    rebind_preparation(data)
    changed = changed_input(actual, data)
    result = score_native_predictions(changed, attempt_id="score")
    assert result.payload.reason == "preparation_mismatch"
    assert result.payload.evaluation is None and result.facts.not_assessed_count == 1


@pytest.mark.parametrize(
    "change", ["probe", "request", "attempt", "swap", "repeat_attempt", "world"]
)
def test_current_actual_prediction_collection_and_world_joins_precede_evaluator(
    change: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    entries = data["predictions"]["entries"]
    if change == "probe":
        entries[0]["probe_id"] = "other"
    elif change == "request":
        entries[0]["request_sha256"] = "f" * 64
    elif change == "attempt":
        entries[0]["attempt_id"] = "different"
    elif change == "swap":
        entries[0], entries[1] = entries[1], entries[0]
    elif change == "repeat_attempt":
        entries[1]["attempt_id"] = entries[0]["attempt_id"]
    else:
        data["world"]["space"]["structure"]["anchors"][0]["position"][0] = -0.0

    def forbidden(*args: Any) -> Any:
        raise AssertionError("evaluator must not receive incoherent material")

    monkeypatch.setattr(scoring, "evaluate_spring_predictions", forbidden)
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    expected = {"repeat_attempt": "attempt_reuse", "world": "world_space_mismatch"}.get(
        change, "prediction_mismatch"
    )
    assert result.payload.reason == expected
    assert result.facts.not_assessed_count == 1


def test_scoring_attempt_cannot_settle_a_probe_prediction_reservation() -> None:
    result = score_native_predictions(material(), attempt_id="prediction-0")
    assert result.payload.reason == "attempt_reuse" and result.facts.not_assessed_count == 1


@pytest.mark.parametrize("change", ["world", "noise_seed", "policy", "prediction", "attempt"])
def test_actual_score_binder_rejects_changed_material_or_scoring_attempt(change: str) -> None:
    actual = material()
    result = score_native_predictions(actual, attempt_id="score")
    data = actual.model_dump(mode="json")
    attempt = "score"
    if change == "world":
        data["world"]["initial_law"]["parameters"]["linear"] = 2.0
    elif change == "noise_seed":
        data["world"]["noise_seed"] = 8
    elif change == "policy":
        data["context"]["candidate_attempt_id"] = "other"
    elif change == "prediction":
        data["predictions"]["entries"][0].update(status="missing", result=None)
    else:
        attempt = "other"
    with pytest.raises(ValueError, match="actual"):
        validate_native_score_result(result, changed_input(actual, data), attempt_id=attempt)


def test_policy_identity_is_independent_of_selected_model_prefix_and_truth() -> None:
    a, b = material(0.0, 1.0), material(4.0, 2.0)
    assert message_sha256(a.context.policy) == message_sha256(b.context.policy)
    assert a.preparation.payload.protocol_sha256 != b.preparation.payload.protocol_sha256
    assert message_sha256(a) != message_sha256(b)
    assert "world" not in a.context.model_dump(mode="json")
    assert "source_world_sha256" not in a.preparation.model_dump_json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("probe_count", True),
        ("probe_count", 23),
        ("frames_per_probe", 40),
        ("normalization_scale", 2.0),
        ("probe_recipe", "redraw"),
        ("max_input_bytes", 1),
    ],
)
def test_policy_cannot_silently_change_probe_or_failure_semantics(field: str, value: Any) -> None:
    data = NativeScoringPolicy().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        NativeScoringPolicy.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b'{"x":0,"x":1}',
        b'{"x":NaN}',
        b'{"x":1e9999}',
        b"\xff",
        b"[" * 33 + b"0" + b"]" * 33,
    ],
)
@pytest.mark.parametrize(
    "parser", [parse_native_evaluation_input, parse_native_scoring_input, parse_native_score_result]
)
def test_raw_ingress_strictness(raw: bytes, parser: Any) -> None:
    with pytest.raises(ContractViolation):
        parser(raw)


def test_node_cap_and_actual_raw_byte_cap_before_decode() -> None:
    raw = b'{"x":[' + b"0," * 1_000_001 + b"0]}"
    with pytest.raises(ContractViolation):
        parse_native_scoring_input(raw)
    actual = material()
    raw = actual.model_dump_json().encode()
    padded = raw + b" " * (MAX_SCORING_INPUT_BYTES - len(raw))
    assert message_sha256(parse_native_scoring_input(padded)) == message_sha256(actual)
    with pytest.raises(ContractViolation):
        parse_native_scoring_input(padded + b" ")
    result = score_native_predictions(actual, attempt_id="score")
    assert parse_native_score_result(result.model_dump_json().encode()) == result
    assert (
        parse_native_evaluation_input(actual.context.model_dump_json().encode()) == actual.context
    )


def test_private_world_metadata_rejects_before_canonical_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    data["world"]["initial_law"]["parameters"] = {f"k{i}": 1.0 for i in range(33)}
    world = WorldDefinition.model_validate_json(json.dumps(data["world"]))
    called = False
    original = bounded_canonical

    def observe(value: Any, limit: int) -> tuple[str, int]:
        nonlocal called
        if isinstance(value, WorldDefinition):
            called = True
        return original(value, limit)

    monkeypatch.setattr(contracts, "bounded_canonical", observe)
    with pytest.raises(ValidationError):
        NativeScoringInput(
            context=actual.context,
            preparation=actual.preparation,
            predictions=actual.predictions,
            world=world,
        )
    assert not called


def test_public_root_reference_closure_excludes_private_truth() -> None:
    schema = native_scoring_json_schema()
    definitions = schema["$defs"]
    todo = [
        "NativeScoringPolicy",
        "NativeEvaluationInput",
        "NativePreparationResult",
        "NativePredictionCollection",
    ]
    seen: set[str] = set()
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        pending = [definitions[name]]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                if "$ref" in value:
                    todo.append(value["$ref"].split("/")[-1])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
    assert not seen & {"WorldDefinition", "LawSpec", "SpringReferenceArtifact", "NativeScoreResult"}
    private = schema["x-private-roots"]
    assert private == ["NativeScoringInput", "NativeScoreOutcome", "NativeScoreResult"]


def test_generated_schema_and_synthetic_examples() -> None:
    schema = json.loads((ROOT / "contracts/native-scoring.schema.json").read_text())
    fixtures = json.loads((ROOT / "contracts/native-scoring.examples.json").read_text())
    assert schema == native_scoring_json_schema()
    for model in SCORING_MODELS:
        data = fixtures["valid"][model.__name__]
        assert model.model_validate_json(json.dumps(data)).model_dump(mode="json") == data


@pytest.mark.parametrize(
    "field", ["input_sha256", "config_sha256", "output_sha256", "completed_count"]
)
def test_facts_are_exact_output_excluding_facts_and_not_hardware_measurement(field: str) -> None:
    result = score_native_predictions(material(), attempt_id="score")
    data = result.model_dump(mode="json")
    data["facts"][field] = 0 if field == "completed_count" else "f" * 64
    with pytest.raises(ValidationError):
        NativeScoreResult.model_validate_json(json.dumps(data))
    assert not {"cpu_ns", "wall_ns", "artifact_bytes"} & set(type(result.facts).model_fields)


def test_private_result_shape_does_not_establish_numerical_authenticity() -> None:
    actual = material()
    result = score_native_predictions(actual, attempt_id="score")
    assert result.payload.evaluation is not None
    assert result.payload.evaluation.report is not None
    # Actual report bytes include the evaluator's measured time. Do not reconstruct
    # a zero-time report to make hashes deterministic across separate executions.
    assert result.payload.evaluation.report.evaluation_runtime_ms >= 0
    assert result.payload.evaluation.report_sha256 == message_sha256(
        result.payload.evaluation.report
    )
    assert bounded_canonical(result, MAX_SCORING_RESULT_BYTES)[0] == message_sha256(result)


def test_all_missing_retains_twenty_four_failures_and_does_not_generate_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    for entry in data["predictions"]["entries"]:
        entry.update(status="missing", result=None)
    data["world"]["initial_law"]["parameters"]["cubic"] = 0.1

    def forbidden(*args: Any) -> Any:
        raise AssertionError("unscorable predictions must not generate reference labels")

    monkeypatch.setattr(evaluator, "_reference_probe", forbidden)
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == "unscorable" and e.report is not None
    assert e.diagnostics.failed_prediction_count == 24 and e.diagnostics.submitted_entry_count == 0
    assert e.diagnostics.valid_prediction_count == 0 and e.reference is None
    assert result.facts.completed_count == 1 and result.facts.failed_count == 0


def test_protocol_failure_is_a_failed_work_unit_without_inventing_failed_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = material()
    monkeypatch.setattr(evaluator, "_protocol_failure", lambda *args: "unsupported_probe")
    result = score_native_predictions(actual, attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == "protocol_failure" and e.report is None
    assert e.diagnostics.prediction_not_assessed_count == 24
    assert e.diagnostics.failed_prediction_count == e.diagnostics.valid_prediction_count == 0
    assert result.facts.failed_count == 1 and result.facts.not_assessed_count == 0


@pytest.mark.parametrize("error,expected", [(1e-100, "scored"), (1e-200, "arithmetic_failure")])
def test_real_metric_underflow_preserves_valid_prediction_counts(
    error: float, expected: str
) -> None:
    actual = material(0.0, 0.0)
    data = actual.model_dump(mode="json")
    prediction = data["predictions"]["entries"][7]["result"]
    prediction["payload"]["response"]["trajectory"]["frames"][1]["positions"][0][0] = error
    from strange_physics.native_prediction_contracts import NativePredictionOutcome

    payload = NativePredictionOutcome.model_validate_json(json.dumps(prediction["payload"]))
    prediction["facts"]["output_sha256"] = message_sha256(payload)
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    e = result.payload.evaluation
    assert e is not None and e.status == expected
    assert e.diagnostics.valid_prediction_count == 24 and e.diagnostics.failed_prediction_count == 0
    if expected == "arithmetic_failure":
        assert e.report is None and e.reason == "metric_failure"
        assert result.facts.failed_count == 1
    else:
        assert e.report is not None and result.facts.completed_count == 1


@pytest.mark.parametrize("index", [0, 12, 23])
def test_bound_result_with_wrong_signed_zero_time_is_integrity_rejection(index: int) -> None:
    actual = material()
    data = actual.model_dump(mode="json")
    prediction = data["predictions"]["entries"][index]["result"]
    prediction["payload"]["response"]["trajectory"]["frames"][0]["time"] = -0.0
    from strange_physics.native_prediction_contracts import NativePredictionOutcome

    payload = NativePredictionOutcome.model_validate_json(json.dumps(prediction["payload"]))
    prediction["facts"]["output_sha256"] = message_sha256(payload)
    result = score_native_predictions(changed_input(actual, data), attempt_id="score")
    assert result.payload.reason == "prediction_mismatch" and result.payload.evaluation is None
    assert result.facts.not_assessed_count == 1


def test_schema_negative_and_runtime_only_fixtures_have_distinct_layers() -> None:
    fixtures = json.loads((ROOT / "contracts/native-scoring.examples.json").read_text())
    models = {model.__name__: model for model in SCORING_MODELS}
    for group in ("schema_negative", "runtime_negative"):
        for fixture in fixtures[group]:
            data = dict(fixtures["valid"][fixture["model"]])
            data[fixture["field"]] = fixture["value"]
            with pytest.raises(ValidationError):
                models[fixture["model"]].model_validate_json(json.dumps(data))


@pytest.mark.parametrize("outcome", ["scored", "unscorable", "failed", "rejected"])
def test_one_actual_scorer_fact_finalizes_one_matching_synthetic_measured_envelope(
    outcome: str,
) -> None:
    from test_study_ledger import append, empty, reserve, update

    from strange_physics.study_ledger import StudyLedgerError, summarize_study

    actual = material()
    data = actual.model_dump(mode="json")
    if outcome == "unscorable":
        data["predictions"]["entries"][0].update(status="missing", result=None)
    elif outcome == "failed":
        data["world"]["initial_law"]["parameters"]["cubic"] = 0.1
    elif outcome == "rejected":
        data["predictions"]["entries"][0]["probe_id"] = "foreign"
    actual = changed_input(actual, data)
    result = score_native_predictions(actual, attempt_id="score")
    facts = StudyWorkFacts.model_validate_json(result.facts.model_dump_json())
    reservation = reserve(
        "score",
        operation="scoring",
        config_sha256=facts.config_sha256,
        input_sha256=facts.input_sha256,
    )
    ledger = append(empty(), reservation)
    final = update(reservation, state=facts.outcome, facts=facts.model_dump(mode="json"))
    settled = append(ledger, final)
    budget = summarize_study(settled).budget
    assert budget.unresolved_attempts == 0 and budget.charged_cpu_ns == 30
    # The timing/cost values are synthetic interface fixtures, not measured study costs.
    with pytest.raises(StudyLedgerError):
        append(settled, final)
    for field in ("config_sha256", "input_sha256"):
        bad = facts.model_dump(mode="json")
        bad[field] = "f" * 64
        with pytest.raises(StudyLedgerError, match="facts_mismatch"):
            append(ledger, update(reservation, state=facts.outcome, facts=bad))
