"""Synthetic arithmetic/premise tests; no product or reference module is imported."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, localcontext
from fractions import Fraction
from typing import Literal

import pytest
from grid_q1_bounds import (
    ArithmeticEvidence,
    EndpointEvidence,
    GridPremises,
    History,
    Interval,
    certify_grid,
    endpoint_log_allowance,
)


def premises(
    history: History = "interior", count: int = 1024, scale: Decimal = Decimal("0.125")
) -> GridPremises:
    recorded = {
        "flat": Decimal(0),
        "boundary": Decimal(1),
        "interior": Decimal.from_float(0.8),
    }[history]
    coverage = tuple(range(count))
    endpoints = EndpointEvidence(Decimal(0), Decimal("1e-60"), coverage, coverage, ())
    return GridPremises(
        history,
        count,
        scale,
        Interval(recorded, recorded),
        endpoints,
        endpoints,
        ArithmeticEvidence(*(Decimal(0) for _ in range(5))),
        "a" * 64,
    )


@pytest.mark.parametrize("history", ("flat", "boundary", "interior"))
@pytest.mark.parametrize("scale", (Decimal("0.125"), Decimal("0.25"), Decimal("0.5")))
def test_all_finest_profiles_have_conditional_bounds(history: History, scale: Decimal) -> None:
    actual = certify_grid(premises(history=history, scale=scale))
    assert actual.passed and actual.finest_gate_applies and actual.reasons == ()
    assert actual.delta_upper <= Decimal("0.0081")
    assert actual.mean_upper <= Decimal("0.018")
    assert actual.second_moment_upper <= Decimal("0.019")
    assert actual.variance_upper <= Decimal("0.056")
    assert actual.tv_upper == actual.delta_upper
    assert actual.actual_reserve_upper <= actual.fixed_reserve_upper == Decimal("3e-9")


def test_coarse_bounds_are_retained_without_applying_the_finest_gate() -> None:
    actual = certify_grid(premises(count=64))
    assert actual.passed and not actual.finest_gate_applies
    assert actual.delta_upper > Decimal("0.0081")
    assert actual.mean_upper > Decimal("0.018")


def test_outward_results_enclose_independent_exact_rational_formulas() -> None:
    actual = certify_grid(premises())
    epsilon = Fraction(1, 10**12) + Fraction(1, 10**60)
    residual = Fraction(1, 2) + Fraction(1, 10**12)
    sigma_squared = Fraction(1, 64)
    endpoint = residual * epsilon / sigma_squared + epsilon**2 / (2 * sigma_squared)
    delta = Fraction(1, 8) * residual * Fraction(2, 1024) / sigma_squared + Fraction(3, 10**9)
    mean = 2 * delta + Fraction(1, 1024) + epsilon
    second = 2 * delta + Fraction(2, 1024) + 3 * epsilon
    variance = second + 2 * mean + mean**2
    for upper, exact in (
        (actual.endpoint_log_error_upper, endpoint),
        (actual.delta_upper, delta),
        (actual.mean_upper, mean),
        (actual.second_moment_upper, second),
        (actual.variance_upper, variance),
    ):
        assert Fraction(upper) >= exact
        assert Fraction(upper) - exact < Fraction(1, 10**95)


def test_ambient_decimal_context_cannot_weaken_the_bounds() -> None:
    inputs = premises()
    expected = certify_grid(inputs)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert certify_grid(inputs) == expected


@pytest.mark.parametrize(
    ("field", "reason"),
    (
        ("node_observed_error_upper", "node_log_error"),
        ("node_other_arithmetic_upper", "node_log_error"),
        ("shifted_log_evidence_error_upper", "shifted_log_evidence_error"),
        ("normalized_log_error_upper", "normalized_and_probability_error"),
        ("probability_representation_log_error_upper", "normalized_and_probability_error"),
    ),
)
def test_each_error_channel_can_fail_without_discarding_bounds(field: str, reason: str) -> None:
    inputs = premises()
    evidence = replace(inputs.arithmetic, **{field: Decimal("1.1e-9")})
    actual = certify_grid(replace(inputs, arithmetic=evidence))
    assert not actual.passed and reason in actual.reasons
    assert actual.delta_upper > 0
    assert actual.fixed_reserve_upper == Decimal("3e-9")


@pytest.mark.parametrize("channel", ("training", "future"))
def test_a_failed_endpoint_ceiling_cannot_be_hidden_by_good_log_errors(channel: str) -> None:
    inputs = premises()
    evidence = replace(inputs.training, max_abs_error_upper=Decimal("1.1e-12"))
    if channel == "training":
        changed = replace(inputs, training=evidence)
    else:
        assert channel == "future"
        changed = replace(inputs, future=evidence)
    actual = certify_grid(changed)
    assert not actual.passed and f"{channel}_endpoint_error" in actual.reasons


def test_overlap_is_explicit_and_both_small_components_must_fit_one_slot() -> None:
    inputs = premises()
    evidence = replace(
        inputs.arithmetic,
        normalized_log_error_upper=Decimal("6e-10"),
        probability_representation_log_error_upper=Decimal("6e-10"),
    )
    actual = certify_grid(replace(inputs, arithmetic=evidence))
    assert actual.reserve_components[2] == Decimal("1.2e-9")
    assert not actual.passed and "normalized_and_probability_error" in actual.reasons


def test_complete_observed_error_and_derived_allowance_both_constrain_a() -> None:
    inputs = premises()
    evidence = replace(inputs.arithmetic, node_observed_error_upper=Decimal("9e-10"))
    actual = certify_grid(replace(inputs, arithmetic=evidence))
    assert actual.reserve_components[0] == Decimal("9e-10")
    assert actual.endpoint_log_error_upper < actual.reserve_components[0]
    assert actual.passed


@pytest.mark.parametrize(
    "invalid", (Decimal("NaN"), Decimal("Infinity"), Decimal("-1e-30"), Decimal("1e129"))
)
def test_invalid_endpoint_bounds_are_unresolved(invalid: Decimal) -> None:
    with pytest.raises(ValueError):
        replace(premises().training, max_abs_error_upper=invalid)


@pytest.mark.parametrize(
    ("lower", "upper"),
    (
        (Decimal("NaN"), Decimal(1)),
        (Decimal(1), Decimal(0)),
        (Decimal("0." + "1" * 121), Decimal(1)),
    ),
)
def test_malformed_intervals_are_rejected(lower: Decimal, upper: Decimal) -> None:
    with pytest.raises(ValueError):
        Interval(lower, upper)


@pytest.mark.parametrize("kind", ("missing_request", "missing_result", "duplicate", "reordered"))
def test_coverage_cannot_skip_duplicate_or_reorder_a_node(kind: str) -> None:
    inputs = premises(count=64)
    sequence = tuple(range(64))
    requested = sequence[:-1] if kind == "missing_request" else sequence
    completed = {
        "missing_request": sequence,
        "missing_result": sequence[:-1],
        "duplicate": sequence[:-1] + (62,),
        "reordered": (1, 0) + sequence[2:],
    }[kind]
    evidence = replace(inputs.training, requested=requested, completed=completed)
    with pytest.raises(ValueError, match="coverage"):
        replace(inputs, training=evidence)


def test_any_failure_prevents_a_survivor_certificate() -> None:
    inputs = premises()
    evidence = replace(inputs.future, failed=(0,))
    with pytest.raises(ValueError, match="coverage"):
        replace(inputs, future=evidence)


@pytest.mark.parametrize("count", (0, 65, True))
def test_unsupported_grid_is_not_silently_replaced(count: int) -> None:
    with pytest.raises(ValueError, match="domain"):
        replace(premises(), count=count)


@pytest.mark.parametrize("scale", (Decimal("0.2"), Decimal("NaN"), Decimal("-0.125")))
def test_unsupported_discrepancy_is_not_silently_replaced(scale: Decimal) -> None:
    with pytest.raises(ValueError):
        replace(premises(), scale=scale)


@pytest.mark.parametrize(
    ("history", "recorded"),
    (
        ("interior", Interval(Decimal("0.5"), Decimal(1))),
        ("interior", Interval(Decimal("0.8"), Decimal("0.8"))),
        ("flat", Interval(Decimal(1), Decimal(1))),
        ("boundary", Interval(Decimal(0), Decimal(0))),
    ),
)
def test_recorded_value_must_be_the_exact_history_binary64_point(
    history: History, recorded: Interval
) -> None:
    with pytest.raises(ValueError, match="Recorded x"):
        replace(premises(), history=history, recorded_x=recorded)


@pytest.mark.parametrize("digest", ("", "A" * 64, "a" * 64 + "\n"))
def test_missing_or_malformed_evidence_identity_is_rejected(digest: str) -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        replace(premises(), evidence_sha256=digest)


@pytest.mark.parametrize("channel", ("training", "future"))
def test_the_reference_allowance_cannot_be_replaced(channel: Literal["training", "future"]) -> None:
    inputs = premises()
    with pytest.raises(ValueError, match="fixed 1e-60"):
        evidence = replace(getattr(inputs, channel), reference_error_upper=Decimal(0))
        replace(inputs, **{channel: evidence})


@pytest.mark.parametrize("residual", (Decimal("-1e-20"), Decimal("Infinity")))
def test_endpoint_propagation_rejects_invalid_residual(residual: Decimal) -> None:
    with pytest.raises(ValueError):
        endpoint_log_allowance(residual, Decimal("0.125"))


def test_negative_arithmetic_allowance_is_not_a_credit() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        replace(premises().arithmetic, node_other_arithmetic_upper=Decimal("-1e-30"))


def test_binary64_point_is_preserved_without_interval_likelihood() -> None:
    inputs = premises()
    assert inputs.recorded_x.lower == inputs.recorded_x.upper == Decimal.from_float(0.8)
    assert inputs.recorded_x.lower != Decimal("0.8")
