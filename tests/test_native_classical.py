from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from test_fitting import _constant_columns, _prefix
from test_native_spring_contracts import selection

import strange_physics.evaluation as evaluator
import strange_physics.native_classical as classical
import strange_physics.prediction as old_prediction
from strange_physics.contracts import ObservationBundle
from strange_physics.control_contracts import ContractViolation
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.laws import LawSpec
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_classical import (
    classical_condition_sha256,
    run_classical_diagnostic,
    validate_classical_diagnostic_result,
)
from strange_physics.native_classical_contracts import (
    CLASSICAL_MODELS,
    MAX_CLASSICAL_BYTES,
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
    ClassicalDiagnosticOutcome,
    ClassicalDiagnosticResult,
    native_classical_json_schema,
    parse_classical_diagnostic_input,
    parse_classical_diagnostic_result,
)
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativeScoringPolicy
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
)
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import message_sha256
from strange_physics.scientific_workflow import fit_spring, i1_protocol
from strange_physics.worlds import WorldDefinition

ROOT = Path(__file__).resolve().parents[1]


def material(
    prefix: ObservationBundle | None = None, *, truth: float = 0.9
) -> ClassicalDiagnosticInput:
    prefix = _prefix(failed=True) if prefix is None else prefix
    candidate = NativeCandidateInput(
        pool=NativeSpringPool(coefficients=(0.0, 1.0, 4.0)),
        config=NativeCandidateConfig(),
        observations=prefix,
    )
    produced = produce_native_candidates(candidate, attempt_id="produce")
    context = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=produced,
        candidate_attempt_id="produce",
        selected=selection(produced, 1) if produced.payload.status == "produced" else None,
        policy=NativeScoringPolicy(),
        prediction_config=NativePredictionConfig(),
    )
    return ClassicalDiagnosticInput(
        context=context,
        config=ClassicalDiagnosticConfig(
            fit_config=SpringFitConfig(),
            prediction_config=SpringPredictionConfig(),
            scoring_policy=context.policy,
        ),
        world=WorldDefinition(
            space=prefix.space,
            noise_seed=7,
            initial_law=LawSpec(kind="spring", parameters={"linear": truth}),
        ),
    )


def changed(data: dict[str, Any]) -> ClassicalDiagnosticInput:
    return ClassicalDiagnosticInput.model_validate_json(json.dumps(data))


def rebind(data: dict[str, Any]) -> ClassicalDiagnosticResult:
    payload = ClassicalDiagnosticOutcome.model_validate_json(json.dumps(data["payload"]))
    data["facts"]["output_sha256"] = message_sha256(payload)
    return ClassicalDiagnosticResult.model_validate_json(json.dumps(data))


def test_real_pipeline_retains_fit_old_predictions_private_evaluator_and_primary() -> None:
    actual = material()
    before = message_sha256(actual.context)
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    p = result.payload
    assert p.fit is not None and p.fit.result is not None and p.fit.model is not None
    assert p.fit.result.status == "fitted" and p.fit.result.diagnostics.failed_record_count == 1
    assert p.fit.model.fitter_version == actual.config.fit_config.fitter_version
    assert p.fit.model.fit_config_sha256 == message_sha256(actual.config.fit_config)
    assert p.fit.model.observation_sha256 == message_sha256(actual.context.candidates.observations)
    assert p.evaluation is not None and p.evaluation.status == "scored"
    assert p.evaluation.report is not None
    assert p.evaluation.report_sha256 == message_sha256(p.evaluation.report)
    assert len(p.predictions) == 24 and p.prediction_not_assessed_count == 0
    assert all(r.diagnostics.computed_frame_count == 41 for r in p.predictions)
    assert result.facts.operation == "classical_diagnostic" and result.facts.completed_count == 1
    assert result.facts.input_sha256 == message_sha256(actual)
    assert result.facts.config_sha256 == message_sha256(actual.config)
    assert result.facts.output_sha256 == message_sha256(p)
    assert message_sha256(actual.context) == before
    assert actual.context.selected is not None and p.protocol is not None
    primary = i1_protocol(
        actual.context.selected.model, actual.context.candidates.observations.space.structure
    )
    assert message_sha256(primary) != message_sha256(p.protocol)
    assert classical_condition_sha256(primary) == classical_condition_sha256(p.protocol)
    validate_classical_diagnostic_result(result, actual, attempt_id="diagnostic")


def test_real_classical_fit_can_succeed_without_a_native_selection() -> None:
    data = material().model_dump(mode="json")
    data["context"]["selected"] = None
    result = run_classical_diagnostic(changed(data), attempt_id="diagnostic")
    assert result.payload.evaluation is not None and result.payload.evaluation.status == "scored"


def test_actual_candidate_construction_failure_does_not_hide_classical_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import strange_physics.native_candidates as candidates

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("synthetic construction failure")

    monkeypatch.setattr(candidates, "LinearSpringModel", broken)
    actual = material()
    assert actual.context.candidate_result.payload.status == "failed"
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    assert result.payload.status == "evaluated" and result.facts.completed_count == 1


@pytest.mark.parametrize("coefficient", [0.0, 0.9, 4.0, 5.0])
def test_real_estimate_is_never_clipped_or_replaced(coefficient: float) -> None:
    actual = material(_prefix(coefficient, failed=True), truth=0.9)
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    p = result.payload
    assert p.fit is not None and p.fit.model is not None and p.evaluation is not None
    assert abs(p.fit.model.linear - coefficient) < 1e-4
    if coefficient > 4:
        assert p.fit.model.linear > 4
        assert p.evaluation.status == "unscorable"
        assert p.evaluation.diagnostics.failed_prediction_count == 24
        assert all(r.reason == "coefficient_outside_domain" for r in p.predictions)
    else:
        assert p.evaluation.status == "scored"
    assert result.facts.completed_count == 1


@pytest.mark.parametrize("kind", ["empty", "failed_only"])
def test_no_completed_prefix_retains_real_rejection_without_fabricated_fit(kind: str) -> None:
    data = _prefix(failed=True).model_dump(mode="json")
    if kind == "empty":
        data["records"] = []
    else:
        data["records"] = [data["records"][1]]
        data["records"][0]["index"] = 0
    actual = material(ObservationBundle.model_validate_json(json.dumps(data)))
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    p = result.payload
    assert p.reason == "no_completed_records" and p.fit is not None
    assert p.fit.result is None and p.fit.fit_input is None
    assert p.prediction_not_assessed_count == 24 and p.evaluation is None
    assert result.facts.not_assessed_count == 1


@pytest.mark.parametrize(
    "noise,dt,expected",
    [(0.1, 0.01, "evaluated"), (0.0, 0.005, "evaluated"), (0.0, 0.001, "fit_failed")],
)
def test_old_noisy_and_sampling_semantics_are_not_narrowed_or_resampled(
    noise: float,
    dt: float,
    expected: str,
) -> None:
    result = run_classical_diagnostic(
        material(_prefix(noise=noise, dt=dt, failed=True)), attempt_id="diagnostic"
    )
    assert result.payload.status == expected
    fit = result.payload.fit
    assert fit is not None and fit.result is not None
    assert fit.result.diagnostics.declared_noisy == bool(noise)
    if expected == "fit_failed":
        assert fit.result.reason == "unsupported_sampling"
        assert result.facts.failed_count == 1 and result.payload.prediction_not_assessed_count == 24


@pytest.mark.parametrize(
    "design,response,status",
    [
        (0.0, 0.0, "insufficient_excitation"),
        (1.0, -1.0, "negative_estimate"),
        (1e200, 1.0, "numerical_failure"),
    ],
)
def test_actual_fit_failures_retain_counts_without_downstream_predictions(
    design: float,
    response: float,
    status: str,
) -> None:
    result = run_classical_diagnostic(
        material(_constant_columns(design, response)), attempt_id="diagnostic"
    )
    p = result.payload
    assert p.fit is not None and p.fit.result is not None
    assert p.fit.result.status == status and p.status == "fit_failed"
    assert p.fit.result.diagnostics.completed_record_count == 1
    assert p.protocol is None and p.predictions == () and p.evaluation is None
    assert p.prediction_not_assessed_count == 24 and result.facts.failed_count == 1


@pytest.mark.parametrize("where", [0, 20, 40])
def test_real_old_predictor_frame_failure_retains_each_computed_prefix(
    where: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = old_prediction._state_at_time

    def fail(model: Any, request: Any, time: float) -> Any:
        if time == request.times[where]:
            raise ArithmeticError("synthetic frame failure")
        return original(model, request, time)

    monkeypatch.setattr(old_prediction, "_state_at_time", fail)
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    assert len(result.payload.predictions) == 24
    assert all(
        r.diagnostics.computed_frame_count == where and r.response is None
        for r in result.payload.predictions
    )
    e = result.payload.evaluation
    assert (
        e is not None and e.status == "unscorable" and e.diagnostics.failed_prediction_count == 24
    )
    assert result.facts.completed_count == 1


@pytest.mark.parametrize("stage", ["reference", "metric"])
@pytest.mark.parametrize("where", [0, 12, 23])
def test_evaluator_failures_never_relabel_valid_predictions(
    stage: str,
    where: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "_reference_probe" if stage == "reference" else "_probe_mse"
    original = getattr(evaluator, name)
    calls = 0

    def fail(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        i = calls
        calls += 1
        if i == where:
            raise ArithmeticError("synthetic evaluator failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(evaluator, name, fail)
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    e = result.payload.evaluation
    assert e is not None and e.report is None and e.diagnostics.valid_prediction_count == 24
    assert e.diagnostics.failed_prediction_count == 0 and result.facts.failed_count == 1


@pytest.mark.parametrize(
    "field", ["candidate_attempt", "selection", "failed_purchase", "world_space", "world_seed"]
)
def test_actual_input_substitution_rejects_or_changes_private_result_identity(field: str) -> None:
    actual = material()
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    data = actual.model_dump(mode="json")
    if field == "candidate_attempt":
        data["context"]["candidate_attempt_id"] = "foreign"
    elif field == "selection":
        data["context"]["selected"]["candidate_result_sha256"] = "f" * 64
    elif field == "failed_purchase":
        data["context"]["candidates"]["observations"]["records"][1]["operation_id"] = "changed"
    elif field == "world_space":
        data["world"]["space"]["structure"]["anchors"][0]["position"][0] = 0.2
    else:
        data["world"]["noise_seed"] = 99
    other = changed(data)
    with pytest.raises(ValueError, match="actual"):
        validate_classical_diagnostic_result(result, other, attempt_id="diagnostic")
    if field != "world_seed":
        rejected = run_classical_diagnostic(other, attempt_id="diagnostic")
        assert rejected.payload.status == "rejected" and rejected.payload.fit is None


@pytest.mark.parametrize(
    "mutation", ["protocol_zero", "protocol_order", "prediction_zero", "submission", "fit_prefix"]
)
def test_coherently_rehashed_stage_tampering_is_not_actual_material(mutation: str) -> None:
    actual = material()
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    data = result.model_dump(mode="json")
    p = data["payload"]
    if mutation == "protocol_zero":
        p["protocol"]["probes"][0]["request"]["times"][0] = -0.0
    elif mutation == "protocol_order":
        p["protocol"]["probes"][0], p["protocol"]["probes"][1] = (
            p["protocol"]["probes"][1],
            p["protocol"]["probes"][0],
        )
    elif mutation == "prediction_zero":
        p["predictions"][0]["response"]["trajectory"]["frames"][0]["time"] = -0.0
    elif mutation == "submission":
        p["submissions"]["entries"][0]["response"]["trajectory"]["frames"][0]["positions"][0][
            0
        ] += 0.1
    else:
        p["fit"]["observations"]["run_id"] = "foreign"
    # Intrinsic stage closure or the complete actual-input binder must reject.
    with pytest.raises(ValueError):
        validate_classical_diagnostic_result(rebind(data), actual, attempt_id="diagnostic")


def test_private_world_never_reaches_fit_or_prediction(monkeypatch: pytest.MonkeyPatch) -> None:
    fit = fit_spring
    predict = old_prediction.predict_linear_spring
    calls = [0, 0]

    def watch_fit(*args: Any) -> Any:
        calls[0] += 1
        assert isinstance(args[0], ObservationBundle) and len(args) == 2
        return fit(*args)

    def watch_predict(*args: Any) -> Any:
        calls[1] += 1
        assert len(args) == 3 and not any(isinstance(a, WorldDefinition) for a in args)
        return predict(*args)

    monkeypatch.setattr(classical, "fit_spring", watch_fit)
    monkeypatch.setattr(classical, "predict_linear_spring", watch_predict)
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    assert calls == [1, 24] and result.payload.status == "evaluated"


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
    "parser", [parse_classical_diagnostic_input, parse_classical_diagnostic_result]
)
def test_strict_raw_ingress(raw: bytes, parser: Any) -> None:
    with pytest.raises(ContractViolation):
        parser(raw)


def test_raw_byte_caps_and_actual_roundtrip() -> None:
    actual = material()
    raw = actual.model_dump_json().encode()
    padded = raw + b" " * (MAX_CLASSICAL_BYTES - len(raw))
    assert message_sha256(parse_classical_diagnostic_input(padded)) == message_sha256(actual)
    with pytest.raises(ContractViolation):
        parse_classical_diagnostic_input(padded + b" ")
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    assert parse_classical_diagnostic_result(result.model_dump_json().encode()) == result


@pytest.mark.parametrize(
    "field", ["operation", "config_sha256", "input_sha256", "output_sha256", "completed_count"]
)
def test_one_diagnostic_envelope_cannot_relabel_or_drop_cost_facts(field: str) -> None:
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    data = result.model_dump(mode="json")
    data["facts"][field] = (
        "scoring" if field == "operation" else 0 if field == "completed_count" else "f" * 64
    )
    with pytest.raises(ValidationError):
        ClassicalDiagnosticResult.model_validate_json(json.dumps(data))


def test_schema_and_examples() -> None:
    assert (
        json.loads((ROOT / "contracts/native-classical.schema.json").read_text())
        == native_classical_json_schema()
    )
    fixtures = json.loads((ROOT / "contracts/native-classical.examples.json").read_text())
    for model in CLASSICAL_MODELS:
        model.model_validate_json(json.dumps(fixtures["valid"][model.__name__]))
    models = {model.__name__: model for model in CLASSICAL_MODELS}
    for group in ("schema_negative", "runtime_negative"):
        for case in fixtures[group]:
            data = json.loads(json.dumps(fixtures["valid"][case["model"]]))
            data[case["field"]] = case["value"]
            with pytest.raises(ValueError):
                models[case["model"]].model_validate_json(json.dumps(data))
    assert native_classical_json_schema()["x-private-roots"] == [
        "ClassicalDiagnosticInput",
        "ClassicalDiagnosticOutcome",
        "ClassicalDiagnosticResult",
    ]


@pytest.mark.parametrize(
    "variant", ["exact", "post_impulse", "zero_impulse", "reversed", "translated"]
)
def test_every_failed_purchase_participates_in_fixed_probe_disjointness(variant: str) -> None:
    actual = material()
    assert actual.context.selected is not None
    structure = actual.context.candidates.observations.space.structure
    protocol = i1_protocol(actual.context.selected.model, structure)
    probe = protocol.probes[7 if variant == "zero_impulse" else 6]
    prefix = actual.context.candidates.observations.model_dump(mode="json")
    prefix["space"]["structure"]["anchors"][0]["position"] = [0.0, 0.0]
    exp = probe.request.experiment.model_dump(mode="json")
    if variant == "post_impulse":
        particle, impulse = exp["particles"][0], exp["impulse"]["vector"]
        particle["velocity"] = [
            v + j / particle["mass"] for v, j in zip(particle["velocity"], impulse, strict=True)
        ]
        exp["impulse"] = None
    elif variant == "zero_impulse":
        exp["impulse"] = {"particle_id": structure.particle_ids[0], "vector": [-0.0, 0.0]}
    elif variant == "reversed":
        prefix["space"]["structure"]["connections"] = [
            {"a": structure.particle_ids[0], "b": structure.anchors[0].id}
        ]
    elif variant == "translated":
        prefix["space"]["structure"]["anchors"][0]["position"][0] = 0.25
        exp["particles"][0]["position"][0] += 0.25
    prefix["records"][1]["experiment"] = exp
    result = run_classical_diagnostic(
        material(ObservationBundle.model_validate_json(json.dumps(prefix))), attempt_id="diagnostic"
    )
    p = result.payload
    assert p.status == "preparation_failed" and p.reason == "purchased_overlap"
    assert p.overlap_record_index == 1 and p.fit is not None and p.fit.model is not None
    assert p.protocol is None and p.predictions == () and p.prediction_not_assessed_count == 24
    assert result.facts.failed_count == 1


def test_exact_prefix_signed_zero_cannot_hide_in_old_artifact_python_equality() -> None:
    actual = material(_constant_columns(0.0))
    result = run_classical_diagnostic(actual, attempt_id="diagnostic")
    data = result.model_dump(mode="json")
    prefix = actual.context.candidates.observations.model_dump(mode="json")
    prefix["records"][0]["trajectory"]["frames"][0]["time"] = -0.0
    other_prefix = ObservationBundle.model_validate_json(json.dumps(prefix))
    actual_other_fit = fit_spring(other_prefix, actual.config.fit_config)
    assert actual_other_fit.result is not None and actual_other_fit.fit_input is not None
    # Coherent inner input/result still compares equal to the old artifact's outer prefix.
    data["payload"]["fit"]["fit_input"] = actual_other_fit.fit_input.model_dump(mode="json")
    data["payload"]["fit"]["result"] = actual_other_fit.result.model_dump(mode="json")
    other = rebind(data)
    assert other.payload.fit is not None and other.payload.fit.fit_input is not None
    assert other.payload.fit.fit_input.observations == actual.context.candidates.observations
    with pytest.raises(ValueError, match="canonical prefix"):
        validate_classical_diagnostic_result(other, actual, attempt_id="diagnostic")
    validate_classical_diagnostic_result(result, actual, attempt_id="diagnostic")


def test_poor_valid_classical_score_remains_scored_without_success_filter() -> None:
    result = run_classical_diagnostic(
        material(_prefix(4.0, failed=True), truth=0.0), attempt_id="diagnostic"
    )
    e = result.payload.evaluation
    assert e is not None and e.status == "scored" and e.report is not None
    assert e.report.position_mse is not None and e.report.position_mse > 0.001
    assert result.facts.completed_count == 1 and "target_passed" not in result.model_dump_json()


def test_late_metric_aggregate_failure_retains_all_completed_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = evaluator._mean

    def fail(values: tuple[float, ...]) -> float:
        if len(values) == 24:
            raise ArithmeticError("synthetic aggregate failure")
        return original(values)

    monkeypatch.setattr(evaluator, "_mean", fail)
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    e = result.payload.evaluation
    assert e is not None and e.status == "arithmetic_failure" and e.report is None
    assert e.diagnostics.valid_prediction_count == 24
    assert e.diagnostics.computed_metric_count == 24
    assert e.diagnostics.failed_prediction_count == 0 and result.facts.failed_count == 1


def test_unexpected_interruption_propagates_for_unknown_attempt_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt(*args: Any) -> Any:
        raise RuntimeError("synthetic interrupted supervisor")

    monkeypatch.setattr(classical, "fit_spring", interrupt)
    with pytest.raises(RuntimeError, match="interrupted"):
        run_classical_diagnostic(material(), attempt_id="diagnostic")


@pytest.mark.parametrize(
    "field", ["schema_version", "split", "normalization", "time", "dt", "position", "order"]
)
def test_condition_projection_preserves_every_non_model_identity(field: str) -> None:
    actual = material()
    assert actual.context.selected is not None
    protocol = i1_protocol(
        actual.context.selected.model, actual.context.candidates.observations.space.structure
    )
    data = protocol.model_dump(mode="json")
    if field == "schema_version":
        # A typed version change is forbidden before comparison.
        data["schema_version"] = "foreign"
    elif field == "split":
        data["split"] = "test"
    elif field == "normalization":
        data["normalization_scale"] = 2.0
    elif field == "time":
        data["probes"][0]["request"]["times"][0] = -0.0
    elif field == "dt":
        data["probes"][0]["request"]["integration_dt"] = 0.005
    elif field == "position":
        data["probes"][0]["request"]["experiment"]["particles"][0]["position"][0] += 0.01
    else:
        data["probes"][0], data["probes"][1] = data["probes"][1], data["probes"][0]
    from strange_physics.evaluation_contracts import SpringEvaluationProtocol

    try:
        modified = SpringEvaluationProtocol.model_validate_json(json.dumps(data))
    except ValidationError:
        return
    assert classical_condition_sha256(modified) != classical_condition_sha256(protocol)


def test_result_byte_cap_and_world_free_metadata_bound() -> None:
    result = run_classical_diagnostic(material(), attempt_id="diagnostic")
    raw = result.model_dump_json().encode()
    padded = raw + b" " * (MAX_CLASSICAL_BYTES - len(raw))
    assert parse_classical_diagnostic_result(padded) == result
    with pytest.raises(ContractViolation):
        parse_classical_diagnostic_result(padded + b" ")
    actual = material().model_dump(mode="json")
    actual["world"]["initial_law"]["parameters"]["x" * 65537] = 0.0
    with pytest.raises((ValueError, ContractViolation)):
        changed(actual)
