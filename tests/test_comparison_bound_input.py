"""Parsed-input handoff conformance; synthetic ancestors, no measured/child work.

These tests use real bounded wrapper parsers and material validators. Retained
parent lookups are synthetic adapters; store authority and public closure
coverage remain in the existing resolver and measured-boundary fixtures.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from test_comparison_stage_binding import (
    failed_prediction,
    references,
    scoring_fixture,
)
from test_comparison_stage_resolver import evidence, no_measured_or_numerical_work, private

from strange_physics import comparison_stage_resolver as retained
from strange_physics import measured_candidates as measured
from strange_physics.comparison_stage_binding import (
    bind_preparation_material,
    comparison_prediction_input,
)
from strange_physics.comparison_stage_resolver import BoundRetainedStage, _Resolver
from strange_physics.native_prediction_contracts import NativePredictionInput
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePreparationResult,
    NativeProbeOutcome,
)
from strange_physics.native_stage_dispatch import StageInput
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPredictionInput,
    NativeComparisonPreparationInput,
    NativeComparisonScoreInput,
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
    StageOperation,
)
from strange_physics.publication_store import digest, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_execution_contracts import NativeFreezeInput
from strange_physics.study_ledger import StudyLedgerError

__all__ = ["no_measured_or_numerical_work"]


@contextmanager
def bound_input(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: StageOperation,
    *,
    replayed: bool = False,
) -> Iterator[tuple[BoundRetainedStage, retained.ComparisonStageRequest]]:
    scoring, frozen, _ = scoring_fixture()
    parent = NativeComparisonPreparationInput(
        candidate_logical_id="candidate",
        candidate_receipt_sha256="b" * 64,
        context=scoring.context,
    )
    prediction = comparison_prediction_input(
        scoring.context, scoring.preparation, preparation_attempt_id="prepare", probe_index=0
    )
    wrappers = {
        "preparation": parent,
        "prediction": NativeComparisonPredictionInput(
            preparation_logical_id="prepare",
            preparation_receipt_sha256="a" * 64,
            probe_index=0,
            prediction=prediction,
        ),
        "scoring": NativeComparisonScoreInput(
            preparation_logical_id="prepare",
            preparation_receipt_sha256="a" * 64,
            predictions=references(scoring),
            scoring=scoring,
        ),
    }
    expected: StageInput = (
        scoring.context
        if operation == "preparation"
        else prediction
        if operation == "prediction"
        else scoring
    )
    wrapper = wrappers[operation]
    data = raw(wrapper)
    parsed: list[StageInput] = []
    parser_name = f"parse_comparison_{'score' if operation == 'scoring' else operation}_input"
    original_parser = getattr(retained, parser_name)

    def parse(value: bytes) -> Any:
        material = original_parser(value)
        parsed.append(
            getattr(
                material,
                {"preparation": "context", "prediction": "prediction", "scoring": "scoring"}[
                    operation
                ],
            )
        )
        return material

    with evidence(root) as e:
        witness_path = root / "synthetic-parent-witness"
        private(witness_path, b"original")

        def preparation_context(
            resolver: _Resolver, material: NativeComparisonPreparationInput
        ) -> NativeFreezeInput:
            resolver.witness.read(witness_path, 8)
            bind_preparation_material(
                material.context,
                candidate=scoring.context.candidates,
                result=scoring.context.candidate_result,
                attempt_id=scoring.context.candidate_attempt_id,
                freeze=frozen,
                cell_id=resolver.cell_id,
            )
            return frozen

        def preparation(
            resolver: _Resolver, logical_id: str, receipt_sha256: str
        ) -> tuple[
            NativeComparisonPreparationInput, NativePreparationResult, str, NativeFreezeInput
        ]:
            assert (logical_id, receipt_sha256) == ("prepare", "a" * 64)
            preparation_context(resolver, parent)
            return parent, scoring.preparation, "prepare", frozen

        def outcome(
            resolver: _Resolver, reference: Any, *, probe_index: int, **kwargs: Any
        ) -> NativeProbeOutcome:
            # This adapter supplies typed transport; it does not authenticate history.
            return scoring.predictions.entries[probe_index]

        models: dict[
            StageOperation,
            type[NativePreparationRequest]
            | type[NativePredictionRequest]
            | type[NativeScoreRequest],
        ] = {
            "preparation": NativePreparationRequest,
            "prediction": NativePredictionRequest,
            "scoring": NativeScoreRequest,
        }
        request = models[operation].model_validate(
            e.request.model_dump()
            | {
                "operation": operation,
                "attempt_id": "score" if operation == "scoring" else "prepare",
                "input_bytes": len(data),
                "input_raw_sha256": digest(data),
                "input_sha256": message_sha256(expected),
                "config_sha256": measured._config(expected),
            }
        )
        with monkeypatch.context() as patch:
            patch.setattr(retained, parser_name, parse)
            patch.setattr(_Resolver, "preparation_context", preparation_context)
            patch.setattr(_Resolver, "preparation", preparation)
            patch.setattr(_Resolver, "prediction", outcome)
            bound = retained.bind_retained_stage(
                e.store,
                request,
                data,
                e.ledger,
                e.store.meter,
                e.resolver.scope,
                replayed=replayed,
            )
            # Identity, not only equality: consumers receive the exact strict
            # parser-owned inner value, never a second parse or unchecked copy.
            assert bound.actual is parsed[0]
            assert raw(bound.actual) == raw(expected)
            assert message_sha256(bound.actual) == request.input_sha256
            assert measured._config(bound.actual) == request.config_sha256
            bound.witness.recheck()
            yield bound, request


@pytest.mark.parametrize("operation", ["preparation", "prediction", "scoring"])
@pytest.mark.parametrize("replayed", [False, True])
def test_bounded_wrapper_hands_off_its_validated_inner_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: StageOperation, replayed: bool
) -> None:
    with bound_input(tmp_path / "store", monkeypatch, operation, replayed=replayed) as (bound, _):
        assert bound.witness.files
        measured._check_engine(bound.actual, "e" * 64)


def test_returned_preparation_still_rejects_foreign_engine_and_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with bound_input(tmp_path / "store", monkeypatch, "preparation") as (bound, request):
        actual = bound.actual
        assert isinstance(actual, NativeEvaluationInput)
        from strange_physics.native_scoring import prepare_native_evaluation

        result = prepare_native_evaluation(actual, attempt_id=request.attempt_id)
        measured._validate(result, actual, request.attempt_id)
        foreign = actual.model_copy(
            update={
                "candidates": actual.candidates.model_copy(
                    update={
                        "observations": actual.candidates.observations.model_copy(
                            update={"engine_fingerprint": "f" * 64}
                        )
                    }
                )
            }
        )
        with pytest.raises(StudyLedgerError, match="^candidate_observation_engine$"):
            measured._check_engine(foreign, "e" * 64)
        with pytest.raises(ValueError, match="^Preparation differs"):
            measured._validate(result, actual, "foreign-attempt")


def test_returned_prediction_keeps_signed_zero_config_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with bound_input(tmp_path / "store", monkeypatch, "prediction") as (bound, request):
        actual = bound.actual
        assert isinstance(actual, NativePredictionInput)
        result = failed_prediction(actual, request.attempt_id)
        measured._validate(result, actual, request.attempt_id)
        # Both zeros satisfy the type's range; canonical identity must distinguish them.
        changed = NativePredictionInput.model_validate_json(
            raw(
                actual.model_copy(
                    update={"config": actual.config.model_copy(update={"min_coefficient": -0.0})}
                )
            )
        )
        assert measured._config(changed) != request.config_sha256
        with pytest.raises(ValueError, match="^Prediction differs"):
            measured._validate(result, changed, request.attempt_id)


def test_returned_witness_still_denies_late_raw_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "store"
    with bound_input(root, monkeypatch, "prediction") as (bound, _):
        private(root / "synthetic-parent-witness", b"changed!")
        with pytest.raises(StudyLedgerError, match="^comparison_retained_changed$"):
            bound.witness.recheck()
