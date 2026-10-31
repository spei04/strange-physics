"""Synthetic rational witness tests; no D1 observations or actual numeric producers."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, Inexact, Rounded, localcontext
from fractions import Fraction
from typing import NoReturn, cast

import d1_bounds
import pytest
from d1_repeated_loss import (
    RepeatedLossInput,
    RepeatedLossNode,
    repeated_loss_witness,
)
from endpoint_belief_reference import EndpointOracle
from grid_q1_bounds import Interval
from grid_q1_evidence import point

import strange_physics.finite_log_weights as finite_weights
import strange_physics.native_endpoint_beliefs as beliefs
import strange_physics.native_prediction as prediction
import strange_physics.simulation as simulation

D = Decimal
DEFAULT_MASSES = (Interval(D("0.1"), D("0.1")), Interval(D("0.9"), D("0.9")))


@pytest.fixture(autouse=True)
def no_numerics(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def deny(*args: object, **kwargs: object) -> NoReturn:
        calls.append("forbidden")
        raise AssertionError("No oracle, forward, normalizer, CDF or score evaluation")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(prediction, "predict_native_spring", deny)
    monkeypatch.setattr(prediction, "_state_at_time", deny)
    monkeypatch.setattr(beliefs, "predict_native_spring", deny)
    monkeypatch.setattr(beliefs, "compute_native_endpoint_belief", deny)
    monkeypatch.setattr(beliefs, "normalize_finite_log_weights", deny)
    monkeypatch.setattr(finite_weights, "normalize_finite_log_weights", deny)
    monkeypatch.setattr(simulation, "simulate", deny)
    for name in ("enclose_cdf", "generalized_quantile", "enclose_predictive", "enclose_scores"):
        monkeypatch.setattr(d1_bounds, name, deny)
    return calls


def inputs(
    emitted: tuple[float, ...] = (1.0, 3.0),
    masses: tuple[Interval, ...] = DEFAULT_MASSES,
    one_error: str = "0",
    two_error: str = "0",
) -> RepeatedLossInput:
    count = len(emitted)
    return RepeatedLossInput(
        count,
        tuple(
            RepeatedLossNode(i, e, mass, Fraction(1, count))
            for i, (e, mass) in enumerate(zip(emitted, masses, strict=True))
        ),
        D(one_error),
        D(two_error),
    )


def changed_node(value: RepeatedLossInput, node: RepeatedLossNode) -> RepeatedLossInput:
    return replace(value, nodes=(node, *value.nodes[1:]))


def test_exact_two_node_square_law_retains_components(no_numerics: list[str]) -> None:
    value = inputs()
    result = repeated_loss_witness(value)
    assert result.inputs is value
    assert result.squared_sum == point(D(10))
    assert result.gamma == point(D(0)) and result.allowance == point(D(1))
    assert tuple(n.transformed_probability for n in result.nodes) == (
        point(D("0.1")),
        point(D("0.9")),
    )
    assert all(n.observed_ratio == point(D(1)) for n in result.nodes)
    assert result.disposition == "contained"
    assert result.disjoint_indices == result.overlap_indices == ()
    assert result.material_authenticity == "unchecked"
    assert result.qualification == "unavailable" and not hasattr(result, "passed")
    assert not no_numerics


@pytest.mark.parametrize("count", (1, 2, 256, 1024))
def test_exact_uniform_surrogates(count: int) -> None:
    # Powers of two make the exact mass Decimal finite; these are not D1 worlds.
    mass = D(Fraction(1, count).numerator) / D(Fraction(1, count).denominator)
    result = repeated_loss_witness(inputs((1.0,) * count, (point(mass),) * count))
    assert len(result.nodes) == count
    assert result.disposition == "contained"
    assert tuple(n.index for n in result.nodes) == tuple(range(count))
    assert all(n.transformed_probability == point(mass) for n in result.nodes)


def test_exact_fraction_reference_enclosed_without_reference_calls() -> None:
    value = inputs(
        (1.0, 2.0, 3.0),
        (
            Interval(D("0.07"), D("0.08")),
            Interval(D("0.28"), D("0.29")),
            Interval(D("0.64"), D("0.65")),
        ),
    )
    result = repeated_loss_witness(value)
    squares = tuple(Fraction.from_float(n.one_emitted) ** 2 for n in value.nodes)
    denominator = sum(squares, Fraction(0))
    for source, bound, squared in zip(value.nodes, result.nodes, squares, strict=True):
        exact = squared / denominator
        assert Fraction(bound.transformed_probability.lower) <= exact
        assert exact <= Fraction(bound.transformed_probability.upper)
        expected_lower = Fraction(source.two_probability.lower) / exact
        expected_upper = Fraction(source.two_probability.upper) / exact
        assert Fraction(bound.observed_ratio.lower) <= expected_lower
        assert expected_upper <= Fraction(bound.observed_ratio.upper)
    assert result.disposition == "overlap"


def test_nonzero_derived_allowance_and_inclusive_lower_endpoint() -> None:
    value = inputs(
        (1.0, 1.0), (point(D("0.375")), point(D("0.625"))), one_error="0.03125", two_error="0.125"
    )
    result = repeated_loss_witness(value)
    assert result.gamma == point(D("0.25"))
    assert result.allowance.lower == D("0.75")
    assert Fraction(result.allowance.upper) >= Fraction(4, 3)
    assert result.nodes[0].observed_ratio.lower == result.allowance.lower
    assert result.disposition == "contained"


def test_inclusive_both_allowance_endpoints_with_feasible_mass_intervals() -> None:
    result = repeated_loss_witness(
        inputs(
            (1.0, 1.0),
            (Interval(D("0.25"), D(1)), Interval(D("0.25"), D("0.75"))),
            two_error="0.5",
        )
    )
    assert result.allowance == Interval(D("0.5"), D(2))
    assert result.nodes[0].observed_ratio == result.allowance
    assert result.disposition == "contained"


def test_disjoint_retains_every_node_and_original_input() -> None:
    value = inputs((1.0, 1.0), (point(D("0.25")), point(D("0.75"))))
    result = repeated_loss_witness(value)
    assert result.disposition == "disjoint" and result.disjoint_indices == (0, 1)
    assert len(result.nodes) == 2 and result.inputs == value
    assert result.nodes[0].observed_ratio == point(D("0.5"))
    assert result.nodes[1].observed_ratio == point(D("1.5"))


def test_overlap_is_never_a_pass_or_a_disjoint_claim() -> None:
    result = repeated_loss_witness(
        inputs(
            (1.0, 1.0),
            (Interval(D("0.5"), D("0.51")), Interval(D("0.49"), D("0.5"))),
        )
    )
    assert result.disposition == "overlap"
    assert result.overlap_indices == (0, 1) and result.disjoint_indices == ()
    assert result.nodes[0].observed_ratio.lower == D(1)
    assert result.nodes[1].observed_ratio.upper == D(1)


def test_disjoint_takes_precedence_but_retains_overlapping_nodes() -> None:
    result = repeated_loss_witness(
        inputs(
            (1.0, 1.0, 1.0),
            (point(D("0.1")), Interval(D("0.3"), D("0.4")), Interval(D("0.5"), D("0.6"))),
        )
    )
    assert result.disposition == "disjoint"
    assert result.disjoint_indices == (0, 2) and result.overlap_indices == (1,)


def test_hostile_ambient_context_cannot_change_result() -> None:
    value = inputs(
        (1.0, 2.0, 3.0),
        (
            Interval(D("0.07"), D("0.08")),
            Interval(D("0.28"), D("0.29")),
            Interval(D("0.64"), D("0.65")),
        ),
        one_error="1e-10",
        two_error="2e-10",
    )
    expected = repeated_loss_witness(value)
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.Emin, context.Emax = -2, 2
        context.traps[Inexact] = context.traps[Rounded] = True
        assert repeated_loss_witness(value) == expected


def test_signed_zero_error_is_retained_but_does_not_change_bound() -> None:
    value = inputs(one_error="-0", two_error="-0")
    result = repeated_loss_witness(value)
    assert result.inputs.one_log_ratio_upper.is_signed()
    assert result.inputs.two_log_ratio_upper.is_signed()
    assert result.gamma.lower == result.gamma.upper == D(0)
    assert result.disposition == "contained"


@pytest.mark.parametrize(
    "bad", (0.0, -0.0, -1.0, float("nan"), float("inf"), float("-inf"), 1e-300, 1e129, 1, True)
)
def test_invalid_emitted_values_fail_closed(bad: object) -> None:
    value = inputs()
    with pytest.raises(ValueError):
        node = replace(value.nodes[0], one_emitted=cast(float, bad))
        repeated_loss_witness(changed_node(value, node))


@pytest.mark.parametrize(
    "bad", (D("NaN"), D("Infinity"), D("-Infinity"), D("-0.1"), D("1.1"), D("1e-257"), 0, True)
)
def test_invalid_component_bounds(bad: object) -> None:
    with pytest.raises(ValueError):
        repeated_loss_witness(replace(inputs(), one_log_ratio_upper=cast(Decimal, bad)))


@pytest.mark.parametrize("one,two", (("0.25", "0"), ("0", "1"), ("0.2", "0.3")))
def test_gamma_at_or_beyond_one_is_not_rounded_down(one: str, two: str) -> None:
    with pytest.raises(ValueError, match="gamma"):
        repeated_loss_witness(inputs(one_error=one, two_error=two))


@pytest.mark.parametrize("count", (0, 1025, True))
def test_invalid_declared_count(count: int) -> None:
    with pytest.raises(ValueError):
        repeated_loss_witness(replace(inputs(), count=count))


@pytest.mark.parametrize("kind", ("missing", "duplicate", "reversed", "bool_index", "list"))
def test_incomplete_or_wrong_order_never_uses_survivors(kind: str) -> None:
    value = inputs()
    if kind == "missing":
        nodes = value.nodes[:1]
    elif kind == "duplicate":
        nodes = (value.nodes[0], value.nodes[0])
    elif kind == "reversed":
        nodes = tuple(reversed(value.nodes))
    elif kind == "bool_index":
        nodes = (replace(value.nodes[0], index=False), value.nodes[1])
    else:
        nodes = cast(tuple[RepeatedLossNode, ...], list(value.nodes))
    with pytest.raises(ValueError):
        repeated_loss_witness(replace(value, nodes=nodes))


@pytest.mark.parametrize(
    "mass", (Fraction(0), Fraction(-1), Fraction(1, 3), Fraction(1), D("0.5"), 0.5)
)
def test_wrong_or_inexact_prior_cannot_use_uniform_simplification(mass: object) -> None:
    value = inputs()
    with pytest.raises(ValueError, match="uniform"):
        node = replace(value.nodes[0], prior_mass=cast(Fraction, mass))
        repeated_loss_witness(changed_node(value, node))


@pytest.mark.parametrize(
    "lower,upper",
    (
        ("0", "0.1"),
        ("-0", "0.1"),
        ("-0.1", "0.1"),
        ("0.1", "1.1"),
        ("0.2", "0.1"),
        ("NaN", "0.1"),
        ("0.1", "Infinity"),
    ),
)
def test_bypassed_interval_is_revalidated(lower: str, upper: str) -> None:
    value = inputs()
    mass = object.__new__(Interval)
    object.__setattr__(mass, "lower", D(lower))
    object.__setattr__(mass, "upper", D(upper))
    with pytest.raises(ValueError):
        repeated_loss_witness(changed_node(value, replace(value.nodes[0], two_probability=mass)))


@pytest.mark.parametrize("direction", ("above", "below"))
def test_exact_feasibility_rejects_sub_precision_residual(direction: str) -> None:
    tiny = D("0." + "5" + "0" * 108 + "1") if direction == "above" else D("0." + "4" + "9" * 109)
    value = inputs((1.0, 1.0), (point(D("0.5")), point(tiny)))
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = context.traps[Rounded] = True
        with pytest.raises(ValueError, match="normalized"):
            repeated_loss_witness(value)


def test_exact_feasibility_accepts_narrow_interval_containing_one() -> None:
    below, above = D("0." + "4" + "9" * 109), D("0." + "5" + "0" * 108 + "1")
    result = repeated_loss_witness(inputs((1.0, 1.0), (point(D("0.5")), Interval(below, above))))
    assert result.disposition == "overlap"


def test_supplied_claims_are_conditional_not_material_authentication() -> None:
    # A caller can supply a different internally consistent synthetic pair. Its
    # containment does not authenticate either vector against a primitive record.
    value = inputs((1.0, 1.0), (point(D("0.5")), point(D("0.5"))))
    result = repeated_loss_witness(value)
    assert result.disposition == "contained"
    assert result.material_authenticity == "unchecked" and result.qualification == "unavailable"
