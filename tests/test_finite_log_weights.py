from __future__ import annotations

import builtins
import copy
import json
import math
from collections.abc import Iterator
from decimal import Decimal, localcontext
from pathlib import Path
from typing import NoReturn

import pytest
from pydantic import ValidationError

import strange_physics.finite_log_weight_contracts as contracts
import strange_physics.finite_log_weights as runtime
from strange_physics.control_contracts import ContractViolation
from strange_physics.finite_log_weight_contracts import (
    MAX_ENTRIES,
    MAX_INPUT_BYTES,
    MAX_JSON_DEPTH,
    MAX_JSON_NODES,
    FiniteLogWeight,
    FiniteLogWeightInput,
    FiniteLogWeightResult,
    NormalizedLogWeight,
    ShiftedLogNormalizer,
    bind_finite_log_weight_result,
    finite_log_weight_json_schema,
    parse_finite_log_weight_input,
    parse_finite_log_weight_result,
)
from strange_physics.research_contracts import message_sha256

ROOT = Path(__file__).resolve().parents[1]
CENSUS = {"normalizer_invocations": 0, "decimal_vectors": 0}


@pytest.fixture(scope="module", autouse=True)
def _report_census() -> Iterator[None]:
    CENSUS.update(normalizer_invocations=0, decimal_vectors=0)
    yield
    print("FINITE_LOG_WEIGHT_CENSUS=" + json.dumps(CENSUS, sort_keys=True))


def _input(values: tuple[float | None, ...], failed: tuple[int, ...] = ()) -> FiniteLogWeightInput:
    return FiniteLogWeightInput(
        entries=tuple(
            FiniteLogWeight(
                item_sha256=f"{i:064x}",
                kind="upstream_failed"
                if i in failed
                else "exact_zero"
                if value is None
                else "finite",
                log_weight=None if i in failed else value,
            )
            for i, value in enumerate(values)
        )
    )


def _normalize(actual: FiniteLogWeightInput) -> FiniteLogWeightResult:
    CENSUS["normalizer_invocations"] += 1
    assert CENSUS["normalizer_invocations"] <= 80
    return runtime.normalize_finite_log_weights(actual)


def _oracle(actual: FiniteLogWeightInput) -> tuple[Decimal, tuple[Decimal | None, ...]]:
    """Direct unshifted finite sum; never call production's exp/fsum/log algorithm."""
    CENSUS["decimal_vectors"] += 1
    assert CENSUS["decimal_vectors"] <= 20
    with localcontext() as context:
        # >435 digits preserve 1+exp(-1000), unlike an 80-digit oracle.
        context.prec = 700
        values = tuple(
            None if entry.log_weight is None else Decimal.from_float(entry.log_weight)
            for entry in actual.entries
        )
        total = sum((value.exp() for value in values if value is not None), Decimal(0))
        log_total = total.ln()
        maximum = max(value for value in values if value is not None)
        return log_total - maximum, tuple(
            None if value is None else value - log_total for value in values
        )


def _assert_reference(actual: FiniteLogWeightInput, result: FiniteLogWeightResult) -> Decimal:
    assert result.status == "normalized"
    assert result.normalizer is not None
    expected_sum, expected_logs = _oracle(actual)
    with localcontext() as context:
        context.prec = 700
        sum_error = abs(Decimal.from_float(result.normalizer.log_scaled_sum) - expected_sum)
        errors: list[tuple[int, Decimal, Decimal]] = []
        zeros_preserved = True
        for index, (entry, expected) in enumerate(zip(result.entries, expected_logs, strict=True)):
            if expected is None:
                zeros_preserved &= entry.kind == "exact_zero" and entry.log_probability is None
            elif entry.kind == "finite" and entry.log_probability is not None:
                tolerance = Decimal("1e-12") + 4 * Decimal.from_float(math.ulp(float(expected)))
                error = abs(Decimal.from_float(entry.log_probability) - expected)
                errors.append((index, error, tolerance))
            else:
                zeros_preserved = False
        worst = max(errors, key=lambda item: item[1])
        # Print before the numerical assertions so a failed criterion retains its
        # actual error and independent reference, including a tiny positive tail.
        print(
            "FINITE_LOG_WEIGHT_REFERENCE="
            + json.dumps(
                {
                    "input_sha256": message_sha256(actual),
                    "entries": len(actual.entries),
                    "decimal_precision": 700,
                    "centered_log_normalizer_reference": str(expected_sum),
                    "reference_centered_sum_positive": expected_sum > 0,
                    "centered_log_normalizer_absolute_error": str(sum_error),
                    "centered_log_normalizer_tolerance": "1e-12",
                    "maximum_normalized_log_error_index": worst[0],
                    "maximum_normalized_log_error": str(worst[1]),
                    "tolerance_at_maximum_error": str(worst[2]),
                    "all_normalized_errors_within_tolerance": all(
                        error <= tolerance for _, error, tolerance in errors
                    ),
                },
                sort_keys=True,
            )
        )
        assert zeros_preserved
        assert sum_error <= Decimal("1e-12")
        assert all(error <= tolerance for _, error, tolerance in errors)
    return expected_sum


def _assert_failure(result: FiniteLogWeightResult, stage: str) -> None:
    assert result.status == "arithmetic_failure"
    assert result.failure_stage == stage
    assert result.entries == () and result.normalizer is None


def _overflow(*args: object, **kwargs: object) -> NoReturn:
    raise OverflowError("injected arithmetic failure")


def _forbidden(*args: object, **kwargs: object) -> NoReturn:
    raise AssertionError("work or serialization occurred before rejection")


def test_singleton_has_unit_log_weight() -> None:
    actual = _input((17.0,))
    result = _normalize(actual)
    _assert_reference(actual, result)
    assert result.entries[0].log_probability == 0.0
    bind_finite_log_weight_result(result, actual)


def test_equal_weights_match_independent_sum() -> None:
    actual = _input((0.0, 0.0, 0.0))
    _assert_reference(actual, _normalize(actual))


def test_unequal_weights_match_independent_sum() -> None:
    actual = _input((0.0, -1.0, -2.0))
    _assert_reference(actual, _normalize(actual))


def test_explicit_zeros_keep_their_original_positions() -> None:
    actual = _input((None, -2.0, None, 0.0))
    result = _normalize(actual)
    _assert_reference(actual, result)
    assert [entry.item_sha256 for entry in result.entries] == [
        entry.item_sha256 for entry in actual.entries
    ]
    assert result.exact_zero_count == 2


def test_exp_underflow_retains_a_finite_log_not_an_exact_zero() -> None:
    actual = _input((0.0, -1000.0, None))
    result = _normalize(actual)
    expected = _assert_reference(actual, result)
    assert expected > 0
    assert result.exp_underflow_indices == (1,)
    assert result.entries[1].kind == "finite"
    assert result.entries[1].log_probability == -1000.0
    assert result.entries[2].kind == "exact_zero"


def test_representable_exp_tail_can_be_absorbed_by_summation() -> None:
    actual = _input((0.0, -500.0))
    result = _normalize(actual)
    expected = _assert_reference(actual, result)
    assert expected > 0
    assert math.exp(-500.0) > 0
    assert result.normalizer is not None
    assert result.normalizer.log_scaled_sum == 0.0
    assert result.exp_underflow_indices == ()


def test_common_shift_preserves_representable_differences() -> None:
    actual = _input((-3.0, -1.0, 0.0))
    shifted = _input((999997.0, 999999.0, 1000000.0))
    first, second = _normalize(actual), _normalize(shifted)
    _assert_reference(actual, first)
    _assert_reference(shifted, second)
    assert first.entries == second.entries
    assert first.input_sha256 != second.input_sha256


def test_permutation_changes_identity_and_preserves_item_correspondence() -> None:
    actual = _input((-3.0, -1.0, 0.0))
    permuted = FiniteLogWeightInput(entries=tuple(reversed(actual.entries)))
    first, second = _normalize(actual), _normalize(permuted)
    _assert_reference(actual, first)
    _assert_reference(permuted, second)
    assert first.entries == tuple(reversed(second.entries))
    assert first.input_sha256 != second.input_sha256


def test_maximum_cardinality_preserves_every_entry() -> None:
    actual = _input((0.0,) * MAX_ENTRIES)
    result = _normalize(actual)
    _assert_reference(actual, result)
    assert len(result.entries) == MAX_ENTRIES
    assert result.exp_evaluations == MAX_ENTRIES


def test_huge_common_offset_keeps_normalizer_components_separate() -> None:
    result = _normalize(_input((1e308, 1e308)))
    assert result.normalizer is not None
    assert result.normalizer.maximum_log_weight == 1e308
    assert result.normalizer.log_scaled_sum == math.log(2.0)
    assert all(entry.log_probability == -math.log(2.0) for entry in result.entries)


def test_all_zero_is_distinct_and_does_no_numerical_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "exp", _forbidden)
    monkeypatch.setattr(math, "fsum", _forbidden)
    monkeypatch.setattr(math, "log", _forbidden)
    result = _normalize(_input((None, None)))
    assert result.status == "all_zero"
    assert result.entries == () and result.normalizer is None
    assert (result.exp_evaluations, result.fsum_evaluations, result.log_evaluations) == (0, 0, 0)


def test_all_upstream_failures_are_retained_before_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "exp", _forbidden)
    monkeypatch.setattr(math, "fsum", _forbidden)
    monkeypatch.setattr(math, "log", _forbidden)
    result = _normalize(_input((0.0, None, -3.0, None), failed=(1, 3)))
    assert result.status == "upstream_failure"
    assert result.upstream_failed_indices == (1, 3)
    assert result.finite_count == 2
    assert result.entries == () and result.normalizer is None


def test_finite_inputs_can_overflow_during_centering() -> None:
    result = _normalize(_input((1e308, -1e308)))
    _assert_failure(result, "centering")
    assert result.failure_index == 1 and result.exp_evaluations == 0


def test_exp_arithmetic_error_has_no_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def underflow_then_fail(value: float) -> float:
        nonlocal calls
        calls += 1
        if calls == 1:
            return 0.0
        raise OverflowError("injected arithmetic failure")

    monkeypatch.setattr(math, "exp", underflow_then_fail)
    actual = _input((0.0, -1.0, -2.0))
    result = _normalize(actual)
    _assert_failure(result, "exponential")
    assert result.failure_index == 1 and result.exp_evaluations == 2
    assert result.exp_underflow_indices == (0,)
    for change in ({"failure_index": 2}, {"exp_underflow_indices": [1]}):
        data = result.model_dump(mode="json")
        data.update(change)
        contradictory = FiniteLogWeightResult.model_validate_json(json.dumps(data))
        with pytest.raises(ValueError, match="ordered exponential"):
            bind_finite_log_weight_result(contradictory, actual)


def test_nonfinite_exp_has_no_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "exp", lambda value: math.nan)
    result = _normalize(_input((0.0, -1.0)))
    _assert_failure(result, "exponential")


def test_sum_arithmetic_error_is_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "fsum", _overflow)
    result = _normalize(_input((0.0, -1.0)))
    _assert_failure(result, "summation")
    assert (result.exp_evaluations, result.fsum_evaluations, result.log_evaluations) == (2, 1, 0)


def test_invalid_sum_is_not_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "fsum", lambda values: 0.0)
    _assert_failure(_normalize(_input((0.0, -1.0))), "summation")


def test_log_arithmetic_error_is_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "log", _overflow)
    result = _normalize(_input((0.0, -1.0)))
    _assert_failure(result, "log_normalizer")
    assert result.log_evaluations == 1


def test_nonfinite_log_is_not_a_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(math, "log", lambda value: math.inf)
    _assert_failure(_normalize(_input((0.0, -1.0))), "log_normalizer")


def test_unrelated_interruption_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    class Interruption(Exception):
        pass

    def interrupted(value: float) -> NoReturn:
        raise Interruption("not a numerical failure")

    monkeypatch.setattr(math, "exp", interrupted)
    with pytest.raises(Interruption, match="not a numerical failure"):
        _normalize(_input((0.0, -1.0)))


def test_input_raw_roundtrip() -> None:
    actual = _input((None, -0.0, 1.0))
    assert parse_finite_log_weight_input(actual.model_dump_json().encode()) == actual


def test_result_raw_roundtrip() -> None:
    result = _normalize(_input((None, 0.0)))
    assert parse_finite_log_weight_result(result.model_dump_json().encode()) == result


def test_raw_format_and_canonical_identity_are_distinct() -> None:
    actual = _input((0.0, -2.0))
    result = _normalize(actual)
    compact = actual.model_dump_json().encode()
    spaced = json.dumps(actual.model_dump(mode="json"), indent=2).encode()
    assert compact != spaced
    assert message_sha256(parse_finite_log_weight_input(spaced)) == result.input_sha256


def test_signed_zero_input_change_is_detected() -> None:
    actual = _input((0.0,))
    changed = _input((-0.0,))
    result = _normalize(actual)
    assert message_sha256(actual) != message_sha256(changed)
    with pytest.raises(ValueError, match="complete actual input"):
        bind_finite_log_weight_result(result, changed)


def test_changed_item_order_is_detected_by_actual_input_binding() -> None:
    actual = _input((0.0, -1.0))
    result = _normalize(actual)
    changed = FiniteLogWeightInput(entries=tuple(reversed(actual.entries)))
    with pytest.raises(ValueError, match="complete actual input"):
        bind_finite_log_weight_result(result, changed)


def test_same_shape_new_value_cannot_reuse_an_old_result() -> None:
    result = _normalize(_input((0.0, -1.0)))
    with pytest.raises(ValueError, match="complete actual input"):
        bind_finite_log_weight_result(result, _input((0.0, -2.0)))


def test_duplicate_correlation_labels_reject() -> None:
    entry = _input((0.0,)).entries[0]
    with pytest.raises(ValidationError, match="unique"):
        FiniteLogWeightInput(entries=(entry, entry))


def test_entry_status_and_value_are_inseparable() -> None:
    for kind, value in (("finite", None), ("exact_zero", 0.0), ("upstream_failed", 0.0)):
        with pytest.raises(ValidationError):
            FiniteLogWeight.model_validate_json(
                json.dumps({"item_sha256": "0" * 64, "kind": kind, "log_weight": value})
            )


def test_malformed_and_nonfinite_raw_json_rejects() -> None:
    valid = _input((0.0,)).model_dump_json().encode()
    assert parse_finite_log_weight_input(valid).entries[0].log_weight == 0.0
    assert b'"log_weight":0.0' in valid
    duplicate = valid.replace(b'"log_weight":0.0', b'"log_weight":-1.0,"log_weight":0.0')
    for raw in (
        b"",
        b"{",
        duplicate,
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e9999}',
        b"\xff",
    ):
        with pytest.raises(ContractViolation):
            parse_finite_log_weight_input(raw)


def test_typed_nonfinite_values_reject() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValidationError):
            FiniteLogWeight(item_sha256="0" * 64, kind="finite", log_weight=value)


def test_raw_byte_ceiling_is_checked_before_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _input((0.0,)).model_dump_json().encode()
    at_limit = raw + b" " * (MAX_INPUT_BYTES - len(raw))
    assert parse_finite_log_weight_input(at_limit).entries[0].log_weight == 0.0
    monkeypatch.setattr(json, "loads", _forbidden)
    with pytest.raises(ContractViolation):
        parse_finite_log_weight_input(at_limit + b" ")


def test_raw_depth_and_node_budgets_reject(monkeypatch: pytest.MonkeyPatch) -> None:
    raws = (
        b"[" * (MAX_JSON_DEPTH + 1) + b"0" + b"]" * (MAX_JSON_DEPTH + 1),
        b"[" + b"0," * MAX_JSON_NODES + b"0]",
    )
    monkeypatch.setattr(json, "loads", _forbidden)
    for raw in raws:
        with pytest.raises(ContractViolation):
            parse_finite_log_weight_input(raw)


def test_cardinality_above_limit_rejects() -> None:
    with pytest.raises(ValidationError):
        _input((0.0,) * (MAX_ENTRIES + 1))


def test_failed_result_cannot_carry_partial_normalization() -> None:
    data = _normalize(_input((0.0, -1.0))).model_dump(mode="json")
    data.update(status="arithmetic_failure", failure_stage="normalization", failure_index=0)
    with pytest.raises(ValidationError, match="partial"):
        FiniteLogWeightResult.model_validate_json(json.dumps(data))


def test_structurally_valid_reordered_output_fails_input_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actual = _input((0.0, -1.0))
    data = _normalize(actual).model_dump(mode="json")
    data["entries"].reverse()
    changed = FiniteLogWeightResult.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="every item"):
        bind_finite_log_weight_result(changed, actual)
    oversized = changed.model_copy(update={"entries": changed.entries * MAX_ENTRIES})
    oversized_diagnostics = changed.model_copy(
        update={"exp_underflow_indices": (0,) * (MAX_ENTRIES + 1)}
    )
    extra_fields = changed.model_copy(update={f"extra_{i}": i for i in range(100)})
    monkeypatch.setattr(FiniteLogWeightResult, "model_dump", _forbidden)
    for malformed in (oversized, oversized_diagnostics, extra_fields):
        with pytest.raises(ValueError):
            bind_finite_log_weight_result(malformed, actual)


def test_generated_schema_matches_the_registered_artifact() -> None:
    expected = json.loads((ROOT / "contracts/finite-log-weight.schema.json").read_text())
    assert finite_log_weight_json_schema() == expected
    assert set(expected["$defs"]) == {
        "FiniteLogWeight",
        "FiniteLogWeightInput",
        "NormalizedLogWeight",
        "ShiftedLogNormalizer",
        "FiniteLogWeightResult",
    }


def test_schema_examples_have_complete_runtime_validation() -> None:
    fixtures = json.loads((ROOT / "contracts/finite-log-weight.examples.json").read_text())
    models = {
        model.__name__: model
        for model in (
            FiniteLogWeight,
            FiniteLogWeightInput,
            NormalizedLogWeight,
            ShiftedLogNormalizer,
            FiniteLogWeightResult,
        )
    }
    for name, value in fixtures["valid"].items():
        assert models[name].model_validate_json(json.dumps(value)).model_dump(mode="json") == value
    for group in ("schema_negative", "runtime_negative"):
        for fixture in fixtures[group]:
            value = copy.deepcopy(fixtures["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            with pytest.raises(ValidationError):
                models[fixture["model"]].model_validate_json(json.dumps(value))
    actual = FiniteLogWeightInput.model_validate_json(
        json.dumps(fixtures["valid"]["FiniteLogWeightInput"])
    )
    result = FiniteLogWeightResult.model_validate_json(
        json.dumps(fixtures["valid"]["FiniteLogWeightResult"])
    )
    bind_finite_log_weight_result(result, actual)


def test_operation_counts_match_real_math_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    counts = {"exp": 0, "fsum": 0, "log": 0}
    original_exp, original_fsum, original_log = math.exp, math.fsum, math.log

    def counted_exp(value: float) -> float:
        counts["exp"] += 1
        return original_exp(value)

    def counted_fsum(values: list[float]) -> float:
        counts["fsum"] += 1
        return original_fsum(values)

    def counted_log(value: float) -> float:
        counts["log"] += 1
        return original_log(value)

    monkeypatch.setattr(math, "exp", counted_exp)
    monkeypatch.setattr(math, "fsum", counted_fsum)
    monkeypatch.setattr(math, "log", counted_log)
    result = _normalize(_input((0.0, None, -1000.0)))
    assert counts == {"exp": 2, "fsum": 1, "log": 1}
    assert (result.exp_evaluations, result.fsum_evaluations, result.log_evaluations) == (2, 1, 1)


def test_constructed_oversized_input_is_rejected_before_dump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = _input((0.0,)).entries[0]
    malformed = FiniteLogWeightInput.model_construct(entries=(entry,) * (MAX_ENTRIES + 1))
    monkeypatch.setattr(FiniteLogWeightInput, "model_dump", _forbidden)
    with pytest.raises(ValueError, match="structural bounds"):
        _normalize(malformed)


def test_copy_bypasses_are_revalidated_before_dump(monkeypatch: pytest.MonkeyPatch) -> None:
    actual = _input((0.0,))
    entry = actual.entries[0]
    malformed = (
        actual.model_copy(update={"entries": list(actual.entries)}),
        actual.model_copy(
            update={"entries": (entry.model_copy(update={"item_sha256": "0" * 65}),)}
        ),
        actual.model_copy(update={"entries": (entry.model_copy(update={"log_weight": math.inf}),)}),
        actual.model_copy(update={"unexpected": "field"}),
        actual.model_copy(update={f"extra_{i}": i for i in range(100)}),
        actual.model_copy(
            update={"entries": (entry.model_copy(update={f"extra_{i}": i for i in range(100)}),)}
        ),
    )

    def bounded_set(value: dict[str, object]) -> set[str]:
        assert len(value) <= 3, "key set was allocated before its cardinality bound"
        return builtins.set(value)

    monkeypatch.setattr(contracts, "set", bounded_set, raising=False)
    monkeypatch.setattr(FiniteLogWeightInput, "model_dump", _forbidden)
    for value in malformed:
        with pytest.raises(ValueError):
            _normalize(value)
