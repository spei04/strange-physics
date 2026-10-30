"""Conditional outward bounds for the fixed GRID-Q1 proposal.

Pure Decimal bookkeeping only: no predictor, oracle, transcendental calculation,
I/O, authentication or runtime admission. A passing certificate still requires
the driver's exact input/coverage/reference provenance and other GRID-Q1 gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Context, Decimal
from typing import Literal

type History = Literal["flat", "boundary", "interior"]

PRECISION = 100
ENDPOINT_LIMIT = Decimal("1e-12")
REFERENCE_LIMIT = Decimal("1e-60")
LOG_LIMIT = Decimal("1e-9")
FIXED_RESERVE = Decimal("3e-9")
RESIDUAL_LIMIT = Decimal("0.500000000001")
SCALES = (Decimal("0.125"), Decimal("0.25"), Decimal("0.5"))
COUNTS = (64, 256, 1024)
HISTORIES = ("flat", "boundary", "interior")


def _decimal(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{label} requires a finite Decimal")
    parts = value.as_tuple()
    if (
        len(parts.digits) > 120
        or not isinstance(parts.exponent, int)
        or not -256 <= parts.exponent <= 128
        or not Decimal("-1e128") <= value <= Decimal("1e128")
    ):
        raise ValueError(f"{label} exceeds the bounded Decimal representation")


def _error(value: Decimal, label: str) -> None:
    _decimal(value, label)
    if not Decimal(0) <= value <= Decimal(1):
        raise ValueError(f"{label} requires a nonnegative error bound at most one")


def _context() -> Context:
    # A fresh explicit context prevents the caller's precision/rounding/traps
    # from silently changing any certificate. Only nonnegative bounds use it.
    return Context(prec=PRECISION, rounding=ROUND_CEILING, Emin=-999999, Emax=999999)


@dataclass(frozen=True)
class Interval:
    lower: Decimal
    upper: Decimal

    def __post_init__(self) -> None:
        _decimal(self.lower, "Interval lower")
        _decimal(self.upper, "Interval upper")
        if self.lower > self.upper:
            raise ValueError("Interval endpoints must be ordered")


@dataclass(frozen=True)
class EndpointEvidence:
    """Observed distance to a reference center plus its separate error allowance.

    These immutable index tuples describe one history/grid/scale, not the whole
    campaign. The driver binds each index to its exact physical query and source.
    """

    max_abs_error_upper: Decimal
    reference_error_upper: Decimal
    requested: tuple[int, ...]
    completed: tuple[int, ...]
    failed: tuple[int, ...]

    def __post_init__(self) -> None:
        _error(self.max_abs_error_upper, "Endpoint observed error")
        _decimal(self.reference_error_upper, "Endpoint reference allowance")
        if self.reference_error_upper != REFERENCE_LIMIT:
            raise ValueError("Endpoint reference allowance must equal the fixed 1e-60")
        for sequence in (self.requested, self.completed, self.failed):
            if (
                not isinstance(sequence, tuple)
                or len(sequence) > 1024
                or any(type(index) is not int or not 0 <= index < 1024 for index in sequence)
            ):
                raise ValueError("Endpoint coverage requires bounded immutable index tuples")


@dataclass(frozen=True)
class ArithmeticEvidence:
    """Complete, outward error envelopes with explicit reference allowances.

    node_observed is the complete observed joint-log error envelope.
    node_other is the non-endpoint arithmetic/reference allowance in its
    independently derived bound. shifted and normalized are complete observed
    errors. probability_representation is the inclusive log-ratio bound between
    actual normalized emitted weights and the independent finite probabilities.
    It is deliberately allowed to overlap the other errors.
    """

    node_observed_error_upper: Decimal
    node_other_arithmetic_upper: Decimal
    shifted_log_evidence_error_upper: Decimal
    normalized_log_error_upper: Decimal
    probability_representation_log_error_upper: Decimal

    def __post_init__(self) -> None:
        for label, value in (
            ("Node observed error", self.node_observed_error_upper),
            ("Node other arithmetic", self.node_other_arithmetic_upper),
            ("Shifted log-evidence error", self.shifted_log_evidence_error_upper),
            ("Normalized-log error", self.normalized_log_error_upper),
            ("Probability representation error", self.probability_representation_log_error_upper),
        ):
            _error(value, label)


@dataclass(frozen=True)
class GridPremises:
    history: History
    count: int
    scale: Decimal
    recorded_x: Interval
    training: EndpointEvidence
    future: EndpointEvidence
    arithmetic: ArithmeticEvidence
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.history not in HISTORIES or type(self.count) is not int or self.count not in COUNTS:
            raise ValueError("Outside the fixed GRID-Q1 history/grid domain")
        _scale(self.scale)
        if not isinstance(self.recorded_x, Interval):
            raise ValueError("Recorded x requires an exact point Interval")
        value = self.recorded_x.lower
        if value != self.recorded_x.upper or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("Recorded x requires an exact point in [0,1]")
        if Decimal.from_float(float(value)) != value:
            raise ValueError("Recorded x must equal its exact binary64 value")
        if (
            (self.history == "flat" and value != 0)
            or (self.history == "boundary" and value != 1)
            or (self.history == "interior" and value < Decimal("0.5"))
        ):
            raise ValueError("Recorded x does not satisfy the fixed history premise")
        for endpoint in (self.training, self.future):
            if not isinstance(endpoint, EndpointEvidence):
                raise ValueError("Both endpoint channels require typed evidence")
            expected = tuple(range(self.count))
            if (
                endpoint.requested != expected
                or endpoint.completed != expected
                or endpoint.failed != ()
            ):
                raise ValueError("Exact ordered endpoint coverage is incomplete or failed")
        if not isinstance(self.arithmetic, ArithmeticEvidence):
            raise ValueError("Arithmetic evidence is required")
        if (
            not isinstance(self.evidence_sha256, str)
            or len(self.evidence_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.evidence_sha256)
        ):
            raise ValueError("Evidence identity requires a lowercase SHA-256 digest")


@dataclass(frozen=True)
class GridCertificate:
    """Bounds are conditional; passed=False is not a usable certificate.

    Even passed=True certifies only these bound predicates, not the independent
    flat-moment, refinement, source identity or scientific adequacy gates.
    """

    endpoint_log_error_upper: Decimal
    reserve_components: tuple[Decimal, Decimal, Decimal]
    actual_reserve_upper: Decimal
    fixed_reserve_upper: Decimal
    delta_upper: Decimal
    tv_upper: Decimal
    mean_upper: Decimal
    second_moment_upper: Decimal
    variance_upper: Decimal
    finest_gate_applies: bool
    passed: bool
    reasons: tuple[str, ...]


def _scale(value: Decimal) -> None:
    _decimal(value, "Scale")
    if value not in SCALES:
        raise ValueError("Outside the fixed GRID-Q1 discrepancy set")


def endpoint_log_allowance(residual_upper: Decimal, scale: Decimal) -> Decimal:
    """R*epsilon/sigma^2 + epsilon^2/(2*sigma^2), rounded upward.

    epsilon is the fixed observed endpoint ceiling plus its reference allowance.
    The caller must establish the residual premise; no endpoint is evaluated.
    """
    _error(residual_upper, "Residual")
    _scale(scale)
    context = _context()
    epsilon = context.add(ENDPOINT_LIMIT, REFERENCE_LIMIT)
    variance = context.multiply(scale, scale)  # Exact for the three fixed dyadic scales.
    linear = context.divide(context.multiply(residual_upper, epsilon), variance)
    quadratic = context.divide(
        context.multiply(epsilon, epsilon), context.multiply(Decimal(2), variance)
    )
    return context.add(linear, quadratic)


def certify_grid(premises: GridPremises) -> GridCertificate:
    """Compute the frozen sufficient bounds without running any reference.

    Malformed/unsupported/missing premises raise ValueError. Complete numerical
    evidence that fails a ceiling returns all conditional bounds and reasons.
    Neither outcome permits silently replacing a fixture, scale or grid.
    """
    if not isinstance(premises, GridPremises):
        raise ValueError("Typed GRID-Q1 premises are required")
    context = _context()
    arithmetic = premises.arithmetic
    endpoint = endpoint_log_allowance(RESIDUAL_LIMIT, premises.scale)
    a = max(
        arithmetic.node_observed_error_upper,
        context.add(endpoint, arithmetic.node_other_arithmetic_upper),
    )
    b = arithmetic.shifted_log_evidence_error_upper
    c = context.add(
        arithmetic.normalized_log_error_upper,
        arithmetic.probability_representation_log_error_upper,
    )
    actual_reserve = context.add(context.add(a, b), c)
    radius = context.divide(Decimal(2), Decimal(premises.count))
    variation = context.divide(
        context.multiply(context.multiply(Decimal("0.125"), RESIDUAL_LIMIT), radius),
        context.multiply(premises.scale, premises.scale),
    )
    delta = context.add(variation, FIXED_RESERVE)
    epsilon = context.add(ENDPOINT_LIMIT, REFERENCE_LIMIT)
    mean = context.add(
        context.add(
            context.multiply(Decimal(2), delta), context.divide(Decimal(1), premises.count)
        ),
        epsilon,
    )
    second = context.add(
        context.add(context.multiply(Decimal(2), delta), radius),
        context.multiply(Decimal(3), epsilon),
    )
    variance = context.add(
        context.add(second, context.multiply(Decimal(2), mean)), context.multiply(mean, mean)
    )
    reasons: list[str] = []
    for condition, reason in (
        (premises.training.max_abs_error_upper <= ENDPOINT_LIMIT, "training_endpoint_error"),
        (premises.future.max_abs_error_upper <= ENDPOINT_LIMIT, "future_endpoint_error"),
        (a <= LOG_LIMIT, "node_log_error"),
        (b <= LOG_LIMIT, "shifted_log_evidence_error"),
        (c <= LOG_LIMIT, "normalized_and_probability_error"),
        (actual_reserve <= FIXED_RESERVE, "reserve_total"),
    ):
        if not condition:
            reasons.append(reason)
    finest = premises.count == 1024
    if finest:
        for bound, ceiling, reason in (
            (delta, Decimal("0.0081"), "finest_cell_mass"),
            (mean, Decimal("0.018"), "finest_mean"),
            (second, Decimal("0.019"), "finest_second_moment"),
            (variance, Decimal("0.056"), "finest_variance"),
        ):
            if bound > ceiling:
                reasons.append(reason)
    return GridCertificate(
        endpoint_log_error_upper=endpoint,
        reserve_components=(a, b, c),
        actual_reserve_upper=actual_reserve,
        fixed_reserve_upper=FIXED_RESERVE,
        delta_upper=delta,
        tv_upper=delta,
        mean_upper=mean,
        second_moment_upper=second,
        variance_upper=variance,
        finest_gate_applies=finest,
        passed=not reasons,
        reasons=tuple(reasons),
    )
