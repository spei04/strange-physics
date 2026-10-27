"""Pure synthetic material conformance; no Journal, child or numerical execution."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError
from test_native_spring_contracts import inputs, selection, synthetic_result
from test_study_ledger import materials

from strange_physics.comparison_stage_binding import (
    bind_prediction_material,
    bind_preparation_material,
    bind_score_material,
    comparison_prediction_input,
)
from strange_physics.contracts import ObservationBundle
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionOutcome,
    NativePredictionResult,
)
from strange_physics.native_scoring import prepare_native_evaluation
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePredictionCollection,
    NativePreparationResult,
    NativeProbeOutcome,
    NativeScoringInput,
    NativeScoringPolicy,
)
from strange_physics.native_spring_contracts import NativeCandidateInput, NativeWorkFacts
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPredictionInput,
    NativeComparisonPreparationInput,
    NativeComparisonScoreInput,
    NativePredictionReference,
    parse_comparison_prediction_input,
    parse_comparison_preparation_input,
    parse_comparison_score_input,
)
from strange_physics.publication_store import digest, raw
from strange_physics.research_contracts import LinearSpringModel, message_sha256
from strange_physics.study_contracts import NativeWorldCatalog
from strange_physics.study_execution_contracts import NativeFreezeInput
from strange_physics.study_ledger import StudyLedgerError


@pytest.fixture(autouse=True)
def forbid_numerical_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Pure binding tests must not execute numerical work")

    for name in (
        "strange_physics.simulation.simulate",
        "strange_physics.native_candidates.produce_native_candidates",
        "strange_physics.native_prediction.predict_native_spring",
        "strange_physics.native_scoring.score_native_predictions",
        "strange_physics.native_scoring.evaluate_spring_predictions",
    ):
        monkeypatch.setattr(name, forbidden)


def fixture() -> tuple[NativeEvaluationInput, NativeFreezeInput, str]:
    manifest, artifacts = materials()
    world = NativeWorldCatalog.model_validate_json(artifacts["world_catalog"]).worlds[0].definition
    candidate = inputs()
    # Synthetic 11+1 typed records preserve a failed row. No current-engine,
    # purchased-history authenticity or scientific accuracy is claimed.
    data = candidate.observations.model_dump(mode="json")
    first, failed = data["records"]
    for record in (first, failed):
        record["experiment"]["particles"][0].update(
            id=world.space.structure.particle_ids[0], position=[0.173, 0.0]
        )
        if record["trajectory"] is not None:
            for frame in record["trajectory"]["frames"]:
                frame["positions"] = [[0.173, 0.0]]
    records = [dict(first, index=i, operation_id=f"op-{i}") for i in range(11)] + [
        dict(failed, index=11, operation_id="op-11")
    ]
    data.update(
        records=records,
        space=world.space.model_dump(mode="json"),
        engine_fingerprint=manifest.engine_fingerprint,
    )
    candidate = NativeCandidateInput(
        pool=candidate.pool,
        config=candidate.config,
        observations=ObservationBundle.model_validate_json(json.dumps(data)),
    )
    result = synthetic_result(candidate)
    context = NativeEvaluationInput(
        candidates=candidate,
        candidate_result=result,
        candidate_attempt_id="attempt-1",
        selected=selection(result),
        policy=NativeScoringPolicy(),
        prediction_config=NativePredictionConfig(),
    )
    for role, value in {
        "pool": candidate.pool,
        "candidate_config": candidate.config,
        "scoring_policy": context.policy,
        "prediction_config": context.prediction_config,
    }.items():
        artifacts[role] = raw(value)
    manifest_data = manifest.model_dump(mode="json")
    for reference in manifest_data["artifacts"]:
        content = artifacts[reference["kind"]]
        reference.update(sha256=digest(content), byte_count=len(content))
    freeze = NativeFreezeInput.model_validate_json(
        json.dumps(
            {
                "manifest": manifest_data,
                "artifacts": {key: content.decode() for key, content in artifacts.items()},
            }
        )
    )
    return context, freeze, freeze.manifest.cells[0].cell_id


def bind_context(context: NativeEvaluationInput, freeze: NativeFreezeInput, cell: str) -> None:
    bind_preparation_material(
        context,
        candidate=context.candidates,
        result=context.candidate_result,
        attempt_id=context.candidate_attempt_id,
        freeze=freeze,
        cell_id=cell,
    )


def preparation(context: NativeEvaluationInput) -> NativePreparationResult:
    # Existing deterministic protocol recomputation; no numerical predictor/evaluator.
    result = prepare_native_evaluation(context, attempt_id="prepare")
    assert result.payload.status == "prepared"
    return result


def failed_prediction(actual: NativePredictionInput, attempt: str) -> NativePredictionResult:
    """Typed synthetic arithmetic failure, not an executed predictor result."""
    payload = NativePredictionOutcome(
        status="numerical_failure",
        reason="arithmetic_failure",
        actual_model_sha256=message_sha256(actual.model),
        requested_model_sha256=actual.request.model_sha256,
        request_sha256=message_sha256(actual.request),
        candidate_config_sha256=message_sha256(actual.candidate_config),
        prediction_config_sha256=message_sha256(actual.config),
        observation_sha256=actual.model.observation_sha256,
        requested_frame_count=41,
        computed_frame_count=0,
        returned_frame_count=0,
        failed_frame_index=0,
        response=None,
    )
    return NativePredictionResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt,
            operation="prediction",
            producer_version=payload.predictor_version,
            config_sha256=payload.prediction_config_sha256,
            input_sha256=message_sha256(actual),
            observation_sha256=payload.observation_sha256,
            model_sha256=payload.actual_model_sha256,
            output_sha256=message_sha256(payload),
            unit="frame",
            requested_count=41,
            completed_count=0,
            failed_count=1,
            not_assessed_count=40,
            outcome="failed",
        ),
    )


def scoring_fixture() -> tuple[NativeScoringInput, NativeFreezeInput, str]:
    context, freeze, cell = fixture()
    prepared = preparation(context)
    protocol = prepared.payload.protocol
    assert protocol is not None and context.selected is not None
    entries = tuple(
        NativeProbeOutcome(
            probe_id=probe.probe_id,
            request_sha256=message_sha256(probe.request),
            attempt_id=f"predict-{i}",
            status="result",
            result=failed_prediction(
                NativePredictionInput(
                    model=context.selected.model,
                    candidate_config=context.candidates.config,
                    request=probe.request,
                    config=context.prediction_config,
                ),
                f"predict-{i}",
            ),
        )
        for i, probe in enumerate(protocol.probes)
    )
    world = (
        NativeWorldCatalog.model_validate_json(freeze.artifacts["world_catalog"])
        .worlds[0]
        .definition
    )
    return (
        NativeScoringInput(
            context=context,
            preparation=prepared,
            predictions=NativePredictionCollection(entries=entries),
            world=world,
        ),
        freeze,
        cell,
    )


def bind_score(
    actual: NativeScoringInput,
    freeze: NativeFreezeInput,
    cell: str,
    entries: tuple[NativeProbeOutcome, ...] | None = None,
) -> None:
    bind_score_material(
        actual,
        context=actual.context,
        preparation=actual.preparation,
        preparation_attempt_id="prepare",
        predictions=actual.predictions.entries if entries is None else entries,
        freeze=freeze,
        cell_id=cell,
        scoring_attempt_id="score",
    )


def references(actual: NativeScoringInput) -> tuple[NativePredictionReference, ...]:
    return tuple(
        NativePredictionReference(
            logical_id=f"prediction-{i}",
            attempt_id=entry.attempt_id,
            ticket=i,
            request_raw_sha256="a" * 64,
            status=entry.status,
            receipt_sha256="b" * 64 if entry.status == "result" else None,
            output_raw_sha256=None if entry.status == "missing" else "c" * 64,
        )
        for i, entry in enumerate(actual.predictions.entries)
    )


def test_full_failed_prefix_selection_and_optional_selection() -> None:
    context, freeze, cell = fixture()
    bind_context(context, freeze, cell)
    assert len(context.candidates.observations.records) == 12
    assert context.candidate_result.payload.failed_record_count == 1
    bind_context(context.model_copy(update={"selected": None}), freeze, cell)
    rejected = prepare_native_evaluation(
        context.model_copy(update={"selected": None}), attempt_id="p"
    )
    assert rejected.payload.reason == "selection_unavailable"
    failed = synthetic_result(context.candidates, failure_at=0)
    bind_context(
        context.model_copy(update={"candidate_result": failed, "selected": None}), freeze, cell
    )


@pytest.mark.parametrize("change", ["prefix", "attempt", "signed_zero", "engine", "pool", "cell"])
def test_preparation_rejects_actual_identity_changes(change: str) -> None:
    context, freeze, cell = fixture()
    bind_context(context, freeze, cell)
    data = context.model_dump(mode="json")
    if change == "prefix":
        data["candidates"]["observations"]["records"][-1]["experiment"]["particles"][0]["position"][
            0
        ] = 0.19
    elif change == "attempt":
        data["candidate_attempt_id"] = "foreign"
    elif change == "signed_zero":
        data["selected"]["model"]["linear"] = 0.0
        data["selected"]["model_sha256"] = message_sha256(
            LinearSpringModel.model_validate_json(json.dumps(data["selected"]["model"]))
        )
    elif change == "engine":
        data["candidates"]["observations"]["engine_fingerprint"] = "f" * 64
    elif change == "pool":
        data["candidates"]["pool"]["coefficients"][0] = 0.0
    else:
        cell = "foreign"
    changed = NativeEvaluationInput.model_validate_json(json.dumps(data))
    with pytest.raises((ValueError, StudyLedgerError)):
        bind_preparation_material(
            changed,
            candidate=context.candidates,
            result=context.candidate_result,
            attempt_id=context.candidate_attempt_id,
            freeze=freeze,
            cell_id=cell,
        )


def test_frozen_raw_and_coherent_pool_substitution_denied() -> None:
    context, freeze, cell = fixture()
    altered = dict(freeze.artifacts)
    altered["pool"] += " "
    with pytest.raises(StudyLedgerError, match="artifact_identity"):
        bind_context(context, freeze.model_copy(update={"artifacts": altered}), cell)
    value = freeze.model_dump(mode="json")
    pool = context.candidates.pool.model_copy(update={"coefficients": (2.0,)})
    value["artifacts"]["pool"] = raw(pool).decode()
    for ref in value["manifest"]["artifacts"]:
        if ref["kind"] == "pool":
            ref.update(sha256=digest(raw(pool)), byte_count=len(raw(pool)))
    with pytest.raises(StudyLedgerError, match="comparison_candidate_config"):
        bind_context(context, NativeFreezeInput.model_validate_json(json.dumps(value)), cell)


def test_all_protocol_probes_are_exact_and_no_numerical_work_occurs() -> None:
    context, _, _ = fixture()
    prepared = preparation(context)
    for i in range(24):
        actual = comparison_prediction_input(
            context, prepared, preparation_attempt_id="prepare", probe_index=i
        )
        bind_prediction_material(
            actual,
            context=context,
            preparation=prepared,
            preparation_attempt_id="prepare",
            probe_index=i,
        )
        with pytest.raises(StudyLedgerError, match="comparison_prediction_material"):
            bind_prediction_material(
                actual,
                context=context,
                preparation=prepared,
                preparation_attempt_id="prepare",
                probe_index=(i + 1) % 24,
            )
    with pytest.raises(ValueError, match="Preparation differs"):
        comparison_prediction_input(
            context, prepared, preparation_attempt_id="foreign", probe_index=0
        )
    with pytest.raises(StudyLedgerError, match="comparison_probe_identity"):
        comparison_prediction_input(
            context, prepared, preparation_attempt_id="prepare", probe_index=24
        )


def test_scoring_binds_all_resolved_results_private_world_and_transport() -> None:
    actual, freeze, cell = scoring_fixture()
    bind_score(actual, freeze, cell)
    entries = actual.predictions.entries
    missing = entries[0].model_copy(update={"status": "missing", "result": None})
    altered = actual.model_copy(
        update={"predictions": NativePredictionCollection(entries=(missing, *entries[1:]))}
    )
    with pytest.raises(StudyLedgerError, match="comparison_score_material"):
        bind_score(altered, freeze, cell, entries)
    # Only separately resolved missing transport is permitted by this pure join.
    bind_score(altered, freeze, cell, (missing, *entries[1:]))
    invalid = entries[1].model_copy(update={"status": "invalid", "result": None})
    mixed = altered.model_copy(
        update={"predictions": NativePredictionCollection(entries=(missing, invalid, *entries[2:]))}
    )
    bind_score(mixed, freeze, cell)
    different = actual.world.model_copy(
        update={
            "initial_law": actual.world.initial_law.model_copy(
                update={"parameters": {"linear": 2.5}}
            )
        }
    )
    with pytest.raises(StudyLedgerError, match="comparison_score_material"):
        bind_score(actual.model_copy(update={"world": different}), freeze, cell)


@pytest.mark.parametrize("change", ["order", "duplicate", "foreign_facts", "score_attempt"])
def test_score_cannot_rebind_prediction_order_or_attempt(change: str) -> None:
    actual, freeze, cell = scoring_fixture()
    entries = list(actual.predictions.entries)
    if change == "order":
        entries[0], entries[1] = entries[1], entries[0]
    elif change == "duplicate":
        entries[1] = entries[1].model_copy(update={"attempt_id": entries[0].attempt_id})
    elif change == "score_attempt":
        entries[0] = entries[0].model_copy(update={"attempt_id": "score"})
    else:
        assert entries[0].result is not None
        entries[0] = entries[0].model_copy(
            update={
                "result": entries[0].result.model_copy(
                    update={
                        "facts": entries[0].result.facts.model_copy(
                            update={"attempt_id": "foreign"}
                        )
                    }
                )
            }
        )
    with pytest.raises((ValueError, StudyLedgerError)):
        bind_score(actual, freeze, cell, tuple(entries))


def test_payload_roundtrips_and_closed_reference_discriminators() -> None:
    scoring, _, _ = scoring_fixture()
    prep = NativeComparisonPreparationInput(
        candidate_logical_id="candidate", candidate_receipt_sha256="a" * 64, context=scoring.context
    )
    prediction = NativeComparisonPredictionInput(
        preparation_logical_id="preparation",
        preparation_receipt_sha256="b" * 64,
        probe_index=0,
        prediction=comparison_prediction_input(
            scoring.context, scoring.preparation, preparation_attempt_id="prepare", probe_index=0
        ),
    )
    score = NativeComparisonScoreInput(
        preparation_logical_id="preparation",
        preparation_receipt_sha256="b" * 64,
        predictions=references(scoring),
        scoring=scoring,
    )
    assert parse_comparison_preparation_input(raw(prep)) == prep
    assert parse_comparison_prediction_input(raw(prediction)) == prediction
    assert parse_comparison_score_input(raw(score)) == score
    for obj, parse in (
        (prep, parse_comparison_preparation_input),
        (prediction, parse_comparison_prediction_input),
        (score, parse_comparison_score_input),
    ):
        with pytest.raises(ValueError):
            parse(raw(obj)[:-1] + b',"hidden":true}')
    data = score.model_dump(mode="json")
    data["predictions"][0]["status"] = "missing"
    with pytest.raises(ValidationError):
        NativeComparisonScoreInput.model_validate_json(json.dumps(data))
    data["predictions"][0]["receipt_sha256"] = None
    data["predictions"][0]["output_raw_sha256"] = None
    with pytest.raises(ValidationError, match="Transport outcomes"):
        NativeComparisonScoreInput.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("key", ["logical_id", "attempt_id", "ticket"])
def test_score_reference_requires_distinct_actual_attempts(key: str) -> None:
    scoring, _, _ = scoring_fixture()
    value: dict[str, Any] = dict(
        preparation_logical_id="preparation",
        preparation_receipt_sha256="b" * 64,
        predictions=[r.model_dump(mode="json") for r in references(scoring)],
        scoring=scoring.model_dump(mode="json"),
    )
    value["predictions"][1][key] = value["predictions"][0][key]
    with pytest.raises(ValidationError, match="distinct retained attempt"):
        NativeComparisonScoreInput.model_validate_json(json.dumps(value))


def test_wrapper_raw_parser_exact_limit_and_one_byte_over() -> None:
    scoring, _, _ = scoring_fixture()
    prep = NativeComparisonPreparationInput(
        candidate_logical_id="candidate",
        candidate_receipt_sha256="a" * 64,
        context=scoring.context,
    )
    prediction = NativeComparisonPredictionInput(
        preparation_logical_id="preparation",
        preparation_receipt_sha256="b" * 64,
        probe_index=0,
        prediction=comparison_prediction_input(
            scoring.context,
            scoring.preparation,
            preparation_attempt_id="prepare",
            probe_index=0,
        ),
    )
    score = NativeComparisonScoreInput(
        preparation_logical_id="preparation",
        preparation_receipt_sha256="b" * 64,
        predictions=references(scoring),
        scoring=scoring,
    )
    for value, parse, limit in (
        (prep, parse_comparison_preparation_input, 16 * 1024**2),
        (prediction, parse_comparison_prediction_input, 8 * 1024**2),
        (score, parse_comparison_score_input, 16 * 1024**2),
    ):
        content = raw(value)
        padded = content + b" " * (limit - len(content))
        assert parse(padded) == value
        with pytest.raises(ValueError):
            parse(padded + b" ")
