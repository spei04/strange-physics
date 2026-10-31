"""Synthetic native arithmetic separation; no physical/reference computation."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, localcontext
from fractions import Fraction
from typing import NoReturn

import pytest
from endpoint_belief_reference import EndpointOracle
from grid_q1_bounds import (
    ArithmeticEvidence,
    EndpointEvidence,
    GridPremises,
    Interval,
    certify_grid,
)
from grid_q1_driver import NativeArithmetic, native_arithmetic_bound


@pytest.fixture(autouse=True)
def no_reference_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Arithmetic separation tests must not calculate a physical reference")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, forbidden)


def bound(**overrides: float) -> NativeArithmetic:
    values = {
        "recorded": 1.0,
        "predicted": 0.75,
        "scale": 0.25,
        "joint_log_weight": -0.5,
    }
    values.update(overrides)
    return native_arithmetic_bound(
        values["recorded"],
        values["predicted"],
        values["scale"],
        Decimal(0),
        Decimal(0),
        values["joint_log_weight"],
    )


@pytest.mark.parametrize("scale", (0.125, 0.25, 0.5))
def test_conditioned_interval_encloses_exact_rational_target(scale: float) -> None:
    expected = -Fraction(1, 16) / (2 * Fraction.from_float(scale) ** 2)
    actual = bound(scale=scale, joint_log_weight=float(expected))
    interval = actual.conditioned_joint_log_weight
    assert Fraction(interval.lower) < expected < Fraction(interval.upper)
    # Both reference constants contribute, even when every basic operation is exact.
    assert actual.error_upper == Decimal("2e-48")


def test_native_arithmetic_error_cannot_be_replaced_by_reference_uncertainty() -> None:
    actual = bound(joint_log_weight=-0.375)
    assert actual.error_upper >= Decimal("0.125")
    assert actual.error_upper > Decimal("1e-48")
    coverage = tuple(range(64))
    endpoints = EndpointEvidence(Decimal(0), Decimal("1e-60"), coverage, coverage, ())
    certificate = certify_grid(
        GridPremises(
            "boundary",
            64,
            Decimal("0.25"),
            Interval(Decimal(1), Decimal(1)),
            endpoints,
            endpoints,
            ArithmeticEvidence(Decimal(0), actual.error_upper, Decimal(0), Decimal(0), Decimal(0)),
            "a" * 64,
        )
    )
    assert not certificate.passed and "node_log_error" in certificate.reasons
    assert certificate.reserve_components[0] >= actual.error_upper


def test_endpoint_displacement_is_not_mislabeled_as_native_arithmetic() -> None:
    # Both computations use exact synthetic arithmetic at different captured x.
    first = bound(predicted=0.75, joint_log_weight=-0.5)
    second = bound(predicted=0.5, joint_log_weight=-2.0)
    assert (
        Fraction(first.conditioned_joint_log_weight.lower)
        - Fraction(second.conditioned_joint_log_weight.upper)
        > 1
    )
    assert first.error_upper == second.error_upper == Decimal("2e-48")
    assert first.conditioned_joint_log_weight != second.conditioned_joint_log_weight


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("recorded", float("nan")),
        ("predicted", float("inf")),
        ("scale", float("nan")),
        ("joint_log_weight", float("-inf")),
        ("scale", 0.2),
        ("recorded", 1.1),
        ("predicted", 2.1),
        ("joint_log_weight", -33.0),
    ),
)
def test_invalid_or_unsupported_native_values_are_unresolved(field: str, value: float) -> None:
    with pytest.raises(ValueError, match="Native arithmetic"):
        bound(**{field: value})


@pytest.mark.parametrize(
    ("gaussian", "prior"),
    (
        (Decimal("NaN"), Decimal(0)),
        (Decimal(0), Decimal("Infinity")),
        (Decimal(33), Decimal(0)),
        (Decimal(0), Decimal(-33)),
    ),
)
def test_reference_constants_require_finite_bounded_evidence(
    gaussian: Decimal, prior: Decimal
) -> None:
    with pytest.raises(ValueError, match="reference constants"):
        native_arithmetic_bound(1.0, 0.75, 0.25, gaussian, prior, -0.5)


def test_ambient_precision_cannot_remove_the_reference_enclosures() -> None:
    expected = bound()
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert bound() == expected


@pytest.mark.parametrize(("recorded", "predicted"), ((0.0, 0.25), (0.25, 0.0)))
def test_both_residual_signs_use_an_outward_square(recorded: float, predicted: float) -> None:
    actual = bound(recorded=recorded, predicted=predicted)
    assert actual.conditioned_joint_log_weight.lower < Decimal("-0.5")
    assert actual.conditioned_joint_log_weight.upper > Decimal("-0.5")
    assert actual.error_upper == Decimal("2e-48")
