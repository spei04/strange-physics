"""Normalize supplied finite log weights without choosing a scientific model."""

from __future__ import annotations

import math

from strange_physics.bounded_json import bounded_canonical
from strange_physics.finite_log_weight_contracts import (
    MAX_INPUT_BYTES,
    FailureStage,
    FiniteLogWeightInput,
    FiniteLogWeightResult,
    NormalizedLogWeight,
    OutcomeStatus,
    ShiftedLogNormalizer,
    bind_finite_log_weight_result,
    validate_finite_log_weight_input,
)


def normalize_finite_log_weights(actual: FiniteLogWeightInput) -> FiniteLogWeightResult:
    """Return rounded log probabilities or a complete, explicitly classified failure.

    Correlation labels are opaque. No model, prior, likelihood, evaluator, ledger,
    ordinary probability array or external state is consulted.
    """
    actual = validate_finite_log_weight_input(actual)
    failed = tuple(i for i, entry in enumerate(actual.entries) if entry.kind == "upstream_failed")
    finite = tuple(i for i, entry in enumerate(actual.entries) if entry.kind == "finite")
    underflow: list[int] = []
    exp_count = fsum_count = log_count = 0

    def finish(
        status: OutcomeStatus,
        *,
        stage: FailureStage | None = None,
        index: int | None = None,
        normalizer: ShiftedLogNormalizer | None = None,
        entries: tuple[NormalizedLogWeight, ...] = (),
    ) -> FiniteLogWeightResult:
        result = FiniteLogWeightResult(
            input_sha256=bounded_canonical(actual, MAX_INPUT_BYTES)[0],
            status=status,
            input_count=len(actual.entries),
            finite_count=len(finite),
            exact_zero_count=len(actual.entries) - len(finite) - len(failed),
            upstream_failed_indices=failed,
            exp_underflow_indices=tuple(underflow),
            exp_evaluations=exp_count,
            fsum_evaluations=fsum_count,
            log_evaluations=log_count,
            failure_stage=stage,
            failure_index=index,
            normalizer=normalizer,
            entries=entries,
        )
        bind_finite_log_weight_result(result, actual)
        return result

    if failed:
        return finish("upstream_failure")
    if not finite:
        return finish("all_zero")

    values = [entry.log_weight for entry in actual.entries if entry.log_weight is not None]
    maximum = max(values)
    centered: dict[int, float] = {}
    for index in finite:
        value = actual.entries[index].log_weight
        assert value is not None
        difference = value - maximum
        if not math.isfinite(difference):
            return finish("arithmetic_failure", stage="centering", index=index)
        centered[index] = difference

    scaled: list[float] = []
    for index in finite:
        exp_count += 1
        try:
            value = math.exp(centered[index])
        except (ArithmeticError, ValueError):
            return finish("arithmetic_failure", stage="exponential", index=index)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            return finish("arithmetic_failure", stage="exponential", index=index)
        if value == 0.0:
            underflow.append(index)
        scaled.append(value)

    fsum_count = 1
    try:
        total = math.fsum(scaled)
    except (ArithmeticError, ValueError):
        return finish("arithmetic_failure", stage="summation")
    if not math.isfinite(total) or not 1.0 <= total <= len(finite):
        return finish("arithmetic_failure", stage="summation")

    log_count = 1
    try:
        log_total = math.log(total)
    except (ArithmeticError, ValueError):
        return finish("arithmetic_failure", stage="log_normalizer")
    if not math.isfinite(log_total) or not 0.0 <= log_total <= 7.0:
        return finish("arithmetic_failure", stage="log_normalizer")

    normalized: list[NormalizedLogWeight] = []
    for index, entry in enumerate(actual.entries):
        if entry.kind == "exact_zero":
            normalized.append(
                NormalizedLogWeight(
                    item_sha256=entry.item_sha256, kind="exact_zero", log_probability=None
                )
            )
        else:
            value = centered[index] - log_total
            if not math.isfinite(value) or value > 0.0:
                return finish("arithmetic_failure", stage="normalization", index=index)
            normalized.append(
                NormalizedLogWeight(
                    item_sha256=entry.item_sha256, kind="finite", log_probability=value
                )
            )
    return finish(
        "normalized",
        normalizer=ShiftedLogNormalizer(maximum_log_weight=maximum, log_scaled_sum=log_total),
        entries=tuple(normalized),
    )
