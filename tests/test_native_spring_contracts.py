from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import ValidationError

import strange_physics.native_spring_contracts as native
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.control_contracts import ContractViolation
from strange_physics.native_spring_contracts import (
    MAX_INPUT_BYTES,
    NATIVE_PRODUCER,
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeCandidateOutcome,
    NativeCandidateResult,
    NativeSpringPool,
    NativeWorkFacts,
    SelectedNativeCandidate,
    native_spring_json_schema,
    parse_native_candidate_input,
    validate_native_candidate_result,
    validate_selected_native_candidate,
)
from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    message_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    NativeSpringPool,
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeWorkFacts,
    NativeCandidateOutcome,
    NativeCandidateResult,
    SelectedNativeCandidate,
)


def inputs(coefficients: tuple[float, ...] = (-0.0, 1.0, 4.0)) -> NativeCandidateInput:
    prefix = json.loads((ROOT / "contracts/fitting.examples.json").read_text())["input"][
        "observations"
    ]
    return NativeCandidateInput(
        pool=NativeSpringPool(coefficients=coefficients),
        config=NativeCandidateConfig(),
        observations=ObservationBundle.model_validate_json(json.dumps(prefix)),
    )


def synthetic_result(
    actual: NativeCandidateInput, *, failure_at: int | None = None, attempt: str = "attempt-1"
) -> NativeCandidateResult:
    """Synthetic contract fixture, not a candidate producer or an executed study."""
    prefix = actual.observations
    indices = tuple(r.index for r in prefix.records if r.status == "completed")
    count = len(actual.pool.coefficients)
    models = (
        tuple(
            LinearSpringModel(
                linear=k,
                through_index=len(prefix.records) - 1,
                fit_record_indices=indices,
                observation_sha256=message_sha256(prefix),
                fitter_version=actual.config.producer_version,
                fit_config_sha256=message_sha256(actual.config),
            )
            for k in actual.pool.coefficients
        )
        if indices and failure_at is None
        else ()
    )
    outcome = NativeCandidateOutcome(
        status="rejected" if not indices else "produced" if failure_at is None else "failed",
        reason="no_completed_records"
        if not indices
        else None
        if failure_at is None
        else "candidate_construction",
        pool_sha256=message_sha256(actual.pool),
        observation_sha256=message_sha256(prefix),
        producer_config_sha256=message_sha256(actual.config),
        through_index=len(prefix.records) - 1,
        completed_record_indices=indices,
        failed_record_count=len(prefix.records) - len(indices),
        requested_candidate_count=count,
        produced_candidate_count=0 if not indices else count if failure_at is None else failure_at,
        failed_candidate_index=failure_at,
        models=models,
    )
    failed = int(failure_at is not None)
    fact_outcome: Literal["completed", "rejected", "failed"] = (
        "completed" if outcome.status == "produced" else outcome.status
    )
    return NativeCandidateResult(
        payload=outcome,
        facts=NativeWorkFacts(
            attempt_id=attempt,
            operation="candidate_production",
            producer_version=NATIVE_PRODUCER,
            config_sha256=message_sha256(actual.config),
            input_sha256=message_sha256(actual),
            observation_sha256=message_sha256(prefix),
            model_sha256=None,
            output_sha256=message_sha256(outcome),
            unit="candidate",
            requested_count=count,
            completed_count=outcome.produced_candidate_count,
            failed_count=failed,
            not_assessed_count=count - outcome.produced_candidate_count - failed,
            outcome=fact_outcome,
        ),
    )


def selection(result: NativeCandidateResult, index: int = 0) -> SelectedNativeCandidate:
    p = result.payload
    return SelectedNativeCandidate(
        candidate_result_sha256=message_sha256(result),
        pool_sha256=p.pool_sha256,
        observation_sha256=p.observation_sha256,
        producer_config_sha256=p.producer_config_sha256,
        candidate_index=index,
        model=p.models[index],
        model_sha256=message_sha256(p.models[index]),
    )


def parse(model: type[Message], value: object) -> Message:
    return model.model_validate_json(json.dumps(value))


def test_actual_pool_prefix_config_and_selected_model_are_bound() -> None:
    actual = inputs()
    result = synthetic_result(actual)
    validate_native_candidate_result(result, actual, attempt_id="attempt-1")
    selected = selection(result)
    validate_selected_native_candidate(selected, result, actual, attempt_id="attempt-1")
    assert selected.selection_claim == "selected-candidate-only"
    assert result.payload.completed_record_indices == (0,)
    assert result.payload.failed_record_count == 1
    assert all(m.fit_record_indices == (0,) for m in result.payload.models)


@pytest.mark.parametrize("model", MODELS)
def test_fixture_schema_roundtrip_and_hidden_input_rejection(model: type[Message]) -> None:
    fixtures = json.loads((ROOT / "contracts/native-spring.examples.json").read_text())
    data = fixtures["valid"][model.__name__]
    parsed = model.model_validate_json(json.dumps(data))
    assert parsed.model_dump(mode="json") == data
    data["private_world"] = {"linear": 1.0}
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "coefficients",
    [
        (),
        (1.0, 0.0),
        (0.0, -0.0),
        (-0.0, 0.0),
        (1.0, 1.0),
        (-1.0,),
        (4.000001,),
        (float("inf"),),
        (float("nan"),),
        tuple(i / 1025 for i in range(1026)),
    ],
)
def test_pool_rejects_invalid_or_duplicate_physical_nodes(coefficients: tuple[float, ...]) -> None:
    with pytest.raises(ValidationError):
        NativeSpringPool(coefficients=coefficients)


def test_pool_upper_count_and_endpoints_are_supported_without_choosing_a_grid() -> None:
    assert (
        len(NativeSpringPool(coefficients=tuple(i / 256 for i in range(1025))).coefficients) == 1025
    )
    assert NativeSpringPool(coefficients=(0.0,)).coefficients == (0.0,)
    assert NativeSpringPool(coefficients=(4.0,)).coefficients == (4.0,)


@pytest.mark.parametrize(
    "field",
    [
        "max_candidates",
        "max_records",
        "max_input_bytes",
        "max_result_bytes",
        "max_json_depth",
        "max_json_nodes",
    ],
)
@pytest.mark.parametrize("value", [True, 0, 9999999])
def test_fixed_strict_support_settings(field: str, value: object) -> None:
    data = NativeCandidateConfig().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        parse(NativeCandidateConfig, data)


def test_pool_identity_is_shared_but_actual_arm_prefix_changes_model_identity() -> None:
    first = inputs()
    data = first.model_dump(mode="json")
    data["observations"]["run_id"] = "other-arm"
    data["observations"]["records"][1]["operation_id"] = "other-failed-purchase"
    second = NativeCandidateInput.model_validate_json(json.dumps(data))
    a, b = synthetic_result(first), synthetic_result(second)
    assert a.payload.pool_sha256 == b.payload.pool_sha256
    assert a.payload.observation_sha256 != b.payload.observation_sha256
    assert message_sha256(a.payload.models[0]) != message_sha256(b.payload.models[0])
    with pytest.raises(ValueError, match="actual pool"):
        validate_native_candidate_result(a, second, attempt_id="attempt-1")


@pytest.mark.parametrize("change", ["failed_record", "pool", "engine", "sampling", "attempt"])
def test_actual_input_binder_rejects_stale_or_foreign_identity(change: str) -> None:
    actual = inputs()
    result = synthetic_result(actual)
    data = actual.model_dump(mode="json")
    attempt = "attempt-1"
    if change == "failed_record":
        data["observations"]["records"][1]["operation_id"] = "different-failed-purchase"
    elif change == "pool":
        data["pool"]["coefficients"][1] = 2.0
    elif change == "engine":
        data["observations"]["engine_fingerprint"] = "f" * 64
    elif change == "sampling":
        data["observations"]["space"]["sampling"]["position_noise"] = 0.002
    else:
        attempt = "different-attempt"
    changed = NativeCandidateInput.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="actual pool"):
        validate_native_candidate_result(result, changed, attempt_id=attempt)


@pytest.mark.parametrize("coefficient", [0.0, -0.0])
def test_each_zero_sign_is_preserved_and_opposite_sign_rehash_is_not_identity(
    coefficient: float,
) -> None:
    actual = inputs((coefficient, 1.0))
    result = synthetic_result(actual)
    validate_native_candidate_result(result, actual, attempt_id="attempt-1")
    data = result.model_dump(mode="json")
    data["payload"]["models"][0]["linear"] = -coefficient
    payload = NativeCandidateOutcome.model_validate_json(json.dumps(data["payload"]))
    data["facts"]["output_sha256"] = message_sha256(payload)
    changed = NativeCandidateResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="exactly preserve"):
        validate_native_candidate_result(changed, actual, attempt_id="attempt-1")


@pytest.mark.parametrize("failed_records", [False, True])
def test_no_completed_records_retains_counts_without_fabricated_models(
    failed_records: bool,
) -> None:
    data = inputs().model_dump(mode="json")
    if failed_records:
        record = data["observations"]["records"][1]
        record["index"] = 0
        data["observations"]["records"] = [record]
    else:
        data["observations"]["records"] = []
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    result = synthetic_result(actual)
    validate_native_candidate_result(result, actual, attempt_id="attempt-1")
    assert result.payload.models == ()
    assert result.payload.completed_record_indices == ()
    assert result.payload.through_index == (0 if failed_records else -1)
    assert result.facts.not_assessed_count == 3
    assert result.facts.failed_count == 0


@pytest.mark.parametrize("index", [0, 1, 2])
def test_failure_retains_exact_prefix_counts_but_no_partial_set(index: int) -> None:
    actual = inputs()
    result = synthetic_result(actual, failure_at=index)
    validate_native_candidate_result(result, actual, attempt_id="attempt-1")
    assert result.payload.models == ()
    assert result.facts.completed_count == index
    assert result.facts.failed_count == 1
    assert result.facts.not_assessed_count == 2 - index


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation", "prediction"),
        ("unit", "frame"),
        ("producer_version", "paired-simpson"),
        ("output_sha256", "f" * 64),
        ("model_sha256", "f" * 64),
        ("config_sha256", "f" * 64),
        ("observation_sha256", "f" * 64),
        ("requested_count", 4),
        ("completed_count", 2),
        ("failed_count", 1),
        ("not_assessed_count", 1),
        ("outcome", "rejected"),
    ],
)
def test_contradictory_local_facts_reject(field: str, value: object) -> None:
    data = synthetic_result(inputs()).model_dump(mode="json")
    data["facts"][field] = value
    with pytest.raises(ValidationError):
        NativeCandidateResult.model_validate_json(json.dumps(data))


def test_facts_are_not_in_their_own_output_hash_and_attempt_is_correlation_only() -> None:
    actual = inputs()
    a = synthetic_result(actual, attempt="envelope-1")
    b = synthetic_result(actual, attempt="envelope-2")
    assert a.facts.output_sha256 == b.facts.output_sha256 == message_sha256(a.payload)
    assert message_sha256(a) != message_sha256(b)
    # Another local operation may share one supervised envelope; no reservation occurs.
    c = synthetic_result(inputs((0.0, 2.0)), attempt="envelope-1")
    assert a.facts.attempt_id == c.facts.attempt_id


@pytest.mark.parametrize("change", ["index", "result_hash", "pool", "model", "map"])
def test_selection_requires_actual_candidate_identity_and_never_claims_map(change: str) -> None:
    actual = inputs()
    result = synthetic_result(actual)
    data = selection(result).model_dump(mode="json")
    if change == "index":
        data["candidate_index"] = 1
    elif change == "result_hash":
        data["candidate_result_sha256"] = "f" * 64
    elif change == "pool":
        data["pool_sha256"] = "f" * 64
    elif change == "map":
        data["selection_claim"] = "proved-map"
    else:
        data["model"]["linear"] = 2.0
        data["model_sha256"] = message_sha256(
            LinearSpringModel.model_validate_json(json.dumps(data["model"]))
        )
    with pytest.raises(ValueError):
        selected = SelectedNativeCandidate.model_validate_json(json.dumps(data))
        validate_selected_native_candidate(selected, result, actual, attempt_id="attempt-1")


def test_input_limits_precede_serialization(monkeypatch: pytest.MonkeyPatch) -> None:
    data = inputs().model_dump(mode="json")

    def forbidden(*args: object, **kwargs: object) -> tuple[str, int]:
        pytest.fail("serializer reached before structural rejection")

    monkeypatch.setattr(native, "bounded_canonical", forbidden)
    for records, engine in [(data["observations"]["records"] * 7, "engine"), ([], "x" * 129)]:
        changed = copy.deepcopy(data)
        changed["observations"].update(records=records, engine_version=engine)
        with pytest.raises(ValidationError):
            NativeCandidateInput.model_validate_json(json.dumps(changed))


def test_raw_parser_rejects_before_decoding_and_preserves_typed_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = inputs()
    assert message_sha256(
        parse_native_candidate_input(actual.model_dump_json().encode())
    ) == message_sha256(actual)
    for raw in [
        b" " * (MAX_INPUT_BYTES + 1),
        b'{"pool":{},"pool":{}}',
        b"NaN",
        b"[" * 33 + b"0" + b"]" * 33,
        b"\xff",
    ]:
        with pytest.raises(ContractViolation):
            parse_native_candidate_input(raw)


def test_frozen_v1_predictor_still_rejects_honest_native_producer() -> None:
    model = synthetic_result(inputs()).payload.models[1]
    fixture: dict[str, Any] = json.loads((ROOT / "contracts/prediction.examples.json").read_text())
    request_data = fixture["request"]
    request_data["model_sha256"] = message_sha256(model)
    request = PredictionRequest.model_validate_json(json.dumps(request_data))
    result = predict_linear_spring(model, request, SpringPredictionConfig())
    assert result.status == "unsupported_runtime"
    assert result.reason == "unsupported_fitter_version"
    assert result.response is None


def test_schema_and_canonical_config_match_checked_in_artifacts() -> None:
    assert (
        json.loads((ROOT / "contracts/native-spring.schema.json").read_text())
        == native_spring_json_schema()
    )
    fixture = json.loads((ROOT / "contracts/native-spring.examples.json").read_text())
    assert fixture["canonical_config_sha256"] == message_sha256(NativeCandidateConfig())
    assert all(
        native_spring_json_schema()["$defs"][m.__name__]["additionalProperties"] is False
        for m in MODELS
    )
    reached = json.dumps(native_spring_json_schema())
    assert "WorldDefinition" not in reached
    assert "SpringFitArtifact" not in reached


@pytest.mark.parametrize(
    "field,value",
    [
        ("models", []),
        ("produced_candidate_count", 2),
        ("failed_record_count", 0),
        ("completed_record_indices", [1]),
        ("reason", "unsupported_domain"),
        ("failed_candidate_index", 0),
    ],
)
def test_success_cannot_drop_models_or_falsify_selected_records(field: str, value: object) -> None:
    data = synthetic_result(inputs()).payload.model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        NativeCandidateOutcome.model_validate_json(json.dumps(data))


def test_maximum_prefix_and_candidate_count_are_representable() -> None:
    data = inputs(tuple(i / 256 for i in range(1025))).model_dump(mode="json")
    data["observations"]["space"]["budget"] = 12
    first = data["observations"]["records"][0]
    data["observations"]["records"] = [
        {**first, "index": i, "operation_id": f"purchased-{i}"} for i in range(12)
    ]
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    result = synthetic_result(actual)
    validate_native_candidate_result(result, actual, attempt_id="attempt-1")
    assert result.payload.completed_record_indices == tuple(range(12))
    assert len(result.payload.models) == 1025
    validate_selected_native_candidate(
        selection(result, 1024), result, actual, attempt_id="attempt-1"
    )


def test_raw_result_roundtrip_rejects_oversize_before_json_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = synthetic_result(inputs())
    assert message_sha256(
        native.parse_native_candidate_result(result.model_dump_json().encode())
    ) == message_sha256(result)

    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("JSON decoder reached for oversized raw input")

    monkeypatch.setattr("strange_physics.bounded_json.json.loads", forbidden)
    with pytest.raises(ContractViolation):
        native.parse_native_candidate_result(b" " * (native.MAX_RESULT_BYTES + 1))
    with pytest.raises(ContractViolation):
        parse_native_candidate_input(b" " * (MAX_INPUT_BYTES + 1))


def test_typed_graph_canonical_limit_rejects_before_complete_encoded_string() -> None:
    from strange_physics.contracts import (
        Experiment,
        ExperimentRecord,
        ExperimentSpace,
        Frame,
        ParticleInitial,
        Sampling,
        Structure,
        Trajectory,
    )

    ids = tuple(f"p{i}" for i in range(8))
    space = ExperimentSpace(
        structure=Structure(particle_ids=ids),
        sampling=Sampling(duration=2.0, dt=0.001, sample_interval=0.001),
        budget=12,
    )
    experiment = Experiment(
        particles=tuple(ParticleInitial(id=p, position=(0.0, 0.0)) for p in ids)
    )
    value = 1.7976931348623157e308
    trajectory = Trajectory(
        frames=tuple(
            Frame(
                time=i * 0.001, positions=((value, -value),) * 8, velocities=((value, -value),) * 8
            )
            for i in range(2001)
        )
    )
    observations = ObservationBundle(
        run_id="synthetic-byte-bound",
        engine_version="synthetic",
        engine_fingerprint="0" * 64,
        space=space,
        records=tuple(
            ExperimentRecord(
                operation_id=f"op-{i}",
                index=i,
                experiment=experiment,
                status="completed",
                trajectory=trajectory,
            )
            for i in range(8)
        ),
    )
    with pytest.raises(ValidationError, match="invalid_request"):
        NativeCandidateInput(
            pool=NativeSpringPool(coefficients=(1.0,)),
            config=NativeCandidateConfig(),
            observations=observations,
        )


def test_fixture_negative_groups_are_also_rejected_semantically() -> None:
    fixture = json.loads((ROOT / "contracts/native-spring.examples.json").read_text())
    models = {model.__name__: model for model in MODELS}
    for group in ("schema_negative", "runtime_negative"):
        for case in fixture[group]:
            data = copy.deepcopy(fixture["valid"][case["model"]])
            data[case["field"]] = case["value"]
            with pytest.raises(ValueError):
                models[case["model"]].model_validate_json(json.dumps(data))
