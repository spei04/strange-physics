"""Conditional D1 bounds only; no physics, reference, log/exp, I/O or admission.

The producer must authenticate the actual source, prefix, reference, emitted
weights and future samples named by the identity. These functions check supplied
premises; a passing result is not scientific qualification or historical truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    localcontext,
)
from typing import Literal

from grid_q1_bounds import ArithmeticEvidence, EndpointEvidence, Interval
from grid_q1_evidence import around, divide, minus, plus, point, square, times, total

from strange_physics.calibration_fixture_contracts import CASE_IDS, PROTOCOL_SHA256, CaseId

D = Decimal
ZERO, ONE = D(0), D(1)
ENDPOINT_ERROR, REFERENCE_ERROR = D("1e-12"), D("1e-60")
LOG_ERROR, RESERVE = D("1e-9"), D("3e-9")
LOW_TAIL, HIGH_TAIL = D("0.05"), D("0.95")
MAX_CELLS = 1024
type Role = Literal["prior", "posterior"]


def _digest(value: str, size: int = 64) -> None:
    if (
        type(value) is not str
        or len(value) != size
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("Exact lowercase evidence identity required")


def _bounded(value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError("Decimal input required")
    Interval(value, value)


def _interval(value: Interval) -> None:
    if type(value) is not Interval:
        raise ValueError("Directed Interval input required")
    Interval(value.lower, value.upper)


def _nonnegative(value: Decimal, maximum: Decimal = ONE) -> None:
    _bounded(value)
    if not ZERO <= value <= maximum:
        raise ValueError("Error or probability outside its bounded domain")


def _up_add(a: Decimal, b: Decimal) -> Decimal:
    return plus(point(a), point(b)).upper


def _up_mul(a: Decimal, b: Decimal) -> Decimal:
    return times(point(a), point(b)).upper


def _up_div(a: Decimal, b: Decimal) -> Decimal:
    return divide(point(a), point(b)).upper


def _coverage(evidence: EndpointEvidence, count: int) -> None:
    if type(evidence) is not EndpointEvidence:
        raise ValueError("Actual endpoint channel evidence required")
    evidence.__post_init__()
    expected = tuple(range(count))
    if evidence.requested != expected or evidence.completed != expected or evidence.failed != ():
        raise ValueError("Exact all-node ordered coverage required; no surviving subset")


@dataclass(frozen=True)
class D1Identity:
    case: CaseId
    count: int
    scale: Decimal
    source_commit: str
    observation_sha256: str
    future_query_sha256: str
    future_values_sha256: str
    probabilities_sha256: str
    evidence_sha256: str
    protocol_sha256: str = PROTOCOL_SHA256

    def __post_init__(self) -> None:
        if (
            self.case not in CASE_IDS
            or type(self.count) is not int
            or self.count not in (256, 1024)
        ):
            raise ValueError("Outside the fixed D1 case/grid matrix")
        _bounded(self.scale)
        allowed = (D("0.25"),) if self.case in ("D03", "W03") else (D("0.125"), D("0.25"), D("0.5"))
        if self.scale not in allowed or self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("Outside the frozen D1 scale/protocol")
        _digest(self.source_commit, 40)
        for value in (
            self.observation_sha256,
            self.future_query_sha256,
            self.future_values_sha256,
            self.probabilities_sha256,
            self.evidence_sha256,
        ):
            _digest(value)


@dataclass(frozen=True)
class D1PrefixPremises:
    identity: D1Identity
    recorded: tuple[Interval, ...]
    training: tuple[EndpointEvidence, ...]
    future: EndpointEvidence
    arithmetic: ArithmeticEvidence

    def __post_init__(self) -> None:
        if type(self.identity) is not D1Identity:
            raise ValueError("Exact D1 identity required")
        self.identity.__post_init__()
        count = 2 if self.identity.case == "D03" else 1
        if (
            type(self.recorded) is not tuple
            or type(self.training) is not tuple
            or len(self.recorded) != count
            or len(self.training) != count
        ):
            raise ValueError("Every declared prefix record requires its own endpoint evidence")
        q = D("0.125") if self.identity.case == "W03" else ONE
        lower = _up_div(q, D(2))  # Exact for these dyadic values.
        for recorded, training in zip(self.recorded, self.training, strict=True):
            _interval(recorded)
            if (
                recorded.lower != recorded.upper
                or not lower <= recorded.lower <= q
                or D.from_float(float(recorded.lower)) != recorded.lower
            ):
                raise ValueError("Recorded observation must be the actual bounded binary64 point")
            _coverage(training, self.identity.count)
        if count == 2 and self.recorded[0] != self.recorded[1]:
            raise ValueError("D03 repeats the same recorded physical value")
        _coverage(self.future, self.identity.count)
        if type(self.arithmetic) is not ArithmeticEvidence:
            raise ValueError("Whole-prefix arithmetic evidence required")
        self.arithmetic.__post_init__()


@dataclass(frozen=True)
class D1Certificate:
    identity: D1Identity
    role: Role
    prefix: D1PrefixPremises | None
    prior_future: EndpointEvidence | None
    endpoint_log_upper: Decimal
    log_derivative_upper: Decimal
    variation_upper: Decimal
    reserve_components: tuple[Decimal, Decimal, Decimal]
    reserve_upper: Decimal
    fixed_reserve: Decimal
    delta_upper: Decimal
    epsilon: Decimal
    mean_error: Decimal
    second_error: Decimal
    variance_error: Decimal
    passed: bool
    reasons: tuple[str, ...]


def _moments(delta: Decimal, count: int, epsilon: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    mean = _up_add(_up_add(_up_mul(D(2), delta), _up_div(D(9), D(16 * count))), epsilon)
    second = _up_add(
        _up_add(_up_mul(D(2), delta), _up_div(D(9), D(8 * count))),
        _up_mul(D(3), epsilon),
    )
    variance = _up_add(_up_add(second, _up_mul(D(2), mean)), _up_mul(mean, mean))
    return mean, second, variance


def _finest_reasons(identity: D1Identity, bounds: tuple[Decimal, ...]) -> tuple[str, ...]:
    if identity.count != 1024:
        return ()
    return tuple(
        name
        for value, limit, name in zip(
            bounds,
            (D("0.0081"), D("0.018"), D("0.019"), D("0.056")),
            ("finest_cell_mass", "finest_mean", "finest_second", "finest_variance"),
            strict=True,
        )
        if value > limit
    )


def certify_d1_prefix(premises: D1PrefixPremises) -> D1Certificate:
    """Sum all record contributions; one overlapping reserve for the whole prefix."""
    if type(premises) is not D1PrefixPremises:
        raise ValueError("Typed prefix premises required")
    premises.__post_init__()
    identity = premises.identity
    epsilon = _up_add(ENDPOINT_ERROR, REFERENCE_ERROR)
    q = D("0.125") if identity.case == "W03" else ONE
    residual = _up_add(_up_div(q, D(2)), epsilon)
    derivative = _up_div(q, D(8))
    variance = _up_mul(identity.scale, identity.scale)  # Exact dyadic square.
    endpoint_term = _up_add(
        _up_div(_up_mul(residual, epsilon), variance),
        _up_div(_up_mul(epsilon, epsilon), _up_mul(D(2), variance)),
    )
    endpoint, log_derivative = ZERO, ZERO
    for _ in premises.recorded:
        endpoint = _up_add(endpoint, endpoint_term)
        log_derivative = _up_add(log_derivative, _up_div(_up_mul(residual, derivative), variance))
    a = max(
        premises.arithmetic.node_observed_error_upper,
        _up_add(endpoint, premises.arithmetic.node_other_arithmetic_upper),
    )
    b = premises.arithmetic.shifted_log_evidence_error_upper
    c = _up_add(
        premises.arithmetic.normalized_log_error_upper,
        premises.arithmetic.probability_representation_log_error_upper,
    )
    reserve = _up_add(_up_add(a, b), c)
    variation = _up_mul(_up_div(D(2), D(identity.count)), log_derivative)
    delta = _up_add(variation, RESERVE)
    mean, second, var = _moments(delta, identity.count, epsilon)
    reasons = tuple(
        name
        for okay, name in (
            (
                all(e.max_abs_error_upper <= ENDPOINT_ERROR for e in premises.training),
                "training_endpoint",
            ),
            (premises.future.max_abs_error_upper <= ENDPOINT_ERROR, "future_endpoint"),
            (a <= LOG_ERROR, "whole_prefix_node_error"),
            (b <= LOG_ERROR, "centered_normalizer_error"),
            (c <= LOG_ERROR, "normalized_probability_error"),
            (reserve <= RESERVE, "overlapping_reserve"),
        )
        if not okay
    ) + _finest_reasons(identity, (delta, mean, second, var))
    return D1Certificate(
        identity,
        "posterior",
        premises,
        None,
        endpoint,
        log_derivative,
        variation,
        (a, b, c),
        reserve,
        RESERVE,
        delta,
        epsilon,
        mean,
        second,
        var,
        not reasons,
        reasons,
    )


def certify_d1_prior(identity: D1Identity, future: EndpointEvidence) -> D1Certificate:
    """Uniform dk has exact cell masses; no likelihood/no posterior certificate reused."""
    if type(identity) is not D1Identity:
        raise ValueError("Typed prior identity required")
    identity.__post_init__()
    _coverage(future, identity.count)
    epsilon = _up_add(ENDPOINT_ERROR, REFERENCE_ERROR)
    mean, second, variance = _moments(ZERO, identity.count, epsilon)
    reasons: tuple[str, ...] = (
        () if future.max_abs_error_upper <= ENDPOINT_ERROR else ("future_endpoint",)
    )
    reasons += _finest_reasons(identity, (ZERO, mean, second, variance))
    return D1Certificate(
        identity,
        "prior",
        None,
        future,
        ZERO,
        ZERO,
        ZERO,
        (ZERO, ZERO, ZERO),
        ZERO,
        ZERO,
        ZERO,
        epsilon,
        mean,
        second,
        variance,
        not reasons,
        reasons,
    )


def _validate_certificate(certificate: D1Certificate) -> None:
    if type(certificate) is not D1Certificate:
        raise ValueError("Conditional D1 certificate required")
    if (
        certificate.role == "posterior"
        and certificate.prefix is not None
        and (certificate.prior_future is None)
    ):
        expected = certify_d1_prefix(certificate.prefix)
    elif (
        certificate.role == "prior"
        and certificate.prefix is None
        and (certificate.prior_future is not None)
    ):
        expected = certify_d1_prior(certificate.identity, certificate.prior_future)
    else:
        raise ValueError("Certificate lacks its exact conditional premise snapshot")
    if expected != certificate or not certificate.passed:
        raise ValueError("Certificate arithmetic, identity or failed premises disagree")


@dataclass(frozen=True)
class PredictiveCell:
    index: int
    mass: Interval
    image: Interval


@dataclass(frozen=True)
class CDFKnot:
    x: Decimal
    cdf: Interval


@dataclass(frozen=True)
class CDFEnvelope:
    support: Interval
    knots: tuple[CDFKnot, ...]
    evidence_sha256: str
    cell_count: int
    mass_updates: int
    delta_upper: Decimal


@dataclass(frozen=True)
class QuantileEnclosure:
    probability: Decimal
    value: Interval
    crossing_ambiguous: bool


def enclose_cdf(
    cells: tuple[PredictiveCell, ...], delta: Decimal, support: Interval, evidence_sha256: str
) -> CDFEnvelope:
    """Two sorted mass sweeps: cell-mass TV is relative to these same emitted weights."""
    if type(cells) is not tuple or not 1 <= len(cells) <= MAX_CELLS:
        raise ValueError("Bounded complete cell tuple required")
    _nonnegative(delta)
    _interval(support)
    _digest(evidence_sha256)
    if support.lower < D(-2) or support.upper > D(2):
        raise ValueError("Kernel support must stay in [-2,2]; D1 continuous support is [-1,1]")
    for i, cell in enumerate(cells):
        if type(cell) is not PredictiveCell or type(cell.index) is not int or cell.index != i:
            raise ValueError("Every cell must occur exactly once in coefficient order")
        _interval(cell.mass)
        _interval(cell.image)
        if (
            not ZERO <= cell.mass.lower <= cell.mass.upper <= ONE
            or cell.image.lower < support.lower
            or cell.image.upper > support.upper
        ):
            raise ValueError("Cell mass/image is outside its certified support")
    # At most 1024 masses in [0,1], with exponent >= -256: 260 digits
    # represent both sums exactly. Directed 100-digit sums can hide a tiny
    # infeasible residual; the support-endpoint rule must not conceal it.
    exact = Context(
        prec=260,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
        flags=[],
        traps=[Inexact, InvalidOperation, DivisionByZero, Overflow],
    )
    try:
        with localcontext(exact) as context:
            lower_mass = upper_mass = ZERO
            for cell in cells:
                lower_mass = context.add(lower_mass, cell.mass.lower)
                upper_mass = context.add(upper_mass, cell.mass.upper)
    except Inexact as error:
        raise ValueError("Exact mass feasibility precision guard failed") from error
    if not lower_mass <= ONE <= upper_mass:
        raise ValueError("Mass intervals must admit a single normalized probability vector")
    low_events = sorted(cells, key=lambda c: (c.image.lower, c.index))
    high_events = sorted(cells, key=lambda c: (c.image.upper, c.index))
    thresholds = sorted(
        {
            support.lower,
            support.upper,
            *(c.image.lower for c in cells),
            *(c.image.upper for c in cells),
        }
    )
    possible, certain = point(0), point(0)
    low_index = high_index = updates = 0
    knots: list[CDFKnot] = []
    for x in thresholds:
        # Include the whole equal-breakpoint group before checking >= thresholds.
        while low_index < len(cells) and low_events[low_index].image.lower <= x:
            possible = plus(possible, low_events[low_index].mass)
            low_index += 1
            updates += 1
        while high_index < len(cells) and high_events[high_index].image.upper <= x:
            certain = plus(certain, high_events[high_index].mass)
            high_index += 1
            updates += 1
        cdf = (
            point(1)
            if x == support.upper
            else Interval(
                max(ZERO, minus(certain, point(delta)).lower),
                min(ONE, plus(possible, point(delta)).upper),
            )
        )
        knots.append(CDFKnot(x, cdf))
    envelope = CDFEnvelope(support, tuple(knots), evidence_sha256, len(cells), updates, delta)
    _validate_cdf(envelope)
    return envelope


def _validate_cdf(envelope: CDFEnvelope) -> None:
    if type(envelope) is not CDFEnvelope:
        raise ValueError("Typed CDF enclosure required")
    _interval(envelope.support)
    _nonnegative(envelope.delta_upper)
    _digest(envelope.evidence_sha256)
    if (
        type(envelope.cell_count) is not int
        or not 1 <= envelope.cell_count <= MAX_CELLS
        or type(envelope.knots) is not tuple
        or not 1 <= len(envelope.knots) <= 2 * envelope.cell_count + 2
        or envelope.mass_updates != 2 * envelope.cell_count
        or any(type(knot) is not CDFKnot for knot in envelope.knots)
        or envelope.knots[0].x != envelope.support.lower
        or envelope.knots[-1].x != envelope.support.upper
        or envelope.knots[-1].cdf != point(1)
    ):
        raise ValueError("CDF coverage/support/computation census is incomplete")
    previous: CDFKnot | None = None
    for knot in envelope.knots:
        if type(knot) is not CDFKnot:
            raise ValueError("Typed CDF knot required")
        _bounded(knot.x)
        _interval(knot.cdf)
        if not ZERO <= knot.cdf.lower <= knot.cdf.upper <= ONE:
            raise ValueError("CDF range is invalid")
        if previous is not None and (
            knot.x <= previous.x
            or knot.cdf.lower < previous.cdf.lower
            or knot.cdf.upper < previous.cdf.upper
        ):
            raise ValueError("CDF brackets require strictly ordered knots and monotone bounds")
        previous = knot


def cdf_at(envelope: CDFEnvelope, x: Decimal) -> Interval:
    """Right-continuous bracket; linear one-query scan, never an all-threshold loop."""
    _validate_cdf(envelope)
    _bounded(x)
    if x < envelope.support.lower:
        return point(0)
    if x >= envelope.support.upper:
        return point(1)
    result = point(0)
    for knot in envelope.knots:
        if knot.x > x:
            break
        result = knot.cdf
    return result


def generalized_quantile(envelope: CDFEnvelope, probability: Decimal) -> QuantileEnclosure:
    _validate_cdf(envelope)
    _bounded(probability)
    if not ZERO < probability < ONE:
        raise ValueError("An interior quantile probability is required")
    lower = next(knot.x for knot in envelope.knots if knot.cdf.upper >= probability)
    upper = next(knot.x for knot in envelope.knots if knot.cdf.lower >= probability)
    return QuantileEnclosure(probability, Interval(lower, upper), lower != upper)


@dataclass(frozen=True)
class PredictiveEnclosure:
    certificate: D1Certificate
    finite_mean: Interval
    finite_second: Interval
    finite_variance: Interval
    mean: Interval
    second: Interval
    variance: Interval
    finite_quantiles: tuple[QuantileEnclosure, QuantileEnclosure]
    quantiles: tuple[QuantileEnclosure, QuantileEnclosure]
    finite_cdf: CDFEnvelope
    cdf: CDFEnvelope


def _clip(value: Interval, lower: Decimal, upper: Decimal) -> Interval:
    return Interval(max(value.lower, lower), min(value.upper, upper))


def _expand(value: Interval, error: Decimal) -> Interval:
    return plus(value, Interval(error.copy_negate(), error))


def enclose_predictive(
    certificate: D1Certificate,
    values: tuple[float, ...],
    masses: tuple[Interval, ...],
    *,
    future_values_sha256: str,
    probabilities_sha256: str,
) -> PredictiveEnclosure:
    """Enclose continuous dk predictions; literal emitted-distribution estimates stay separate."""
    _validate_certificate(certificate)
    identity = certificate.identity
    identity.__post_init__()
    if not certificate.passed or certificate.reasons:
        raise ValueError("Failed numerical premises cannot yield predictive certificates")
    if (
        certificate.role not in ("prior", "posterior")
        or future_values_sha256 != identity.future_values_sha256
        or probabilities_sha256 != identity.probabilities_sha256
        or type(values) is not tuple
        or type(masses) is not tuple
        or len(values) != identity.count
        or len(masses) != identity.count
    ):
        raise ValueError(
            "Complete ordered prediction/mass arrays and exact evidence joins required"
        )
    for error in (
        certificate.delta_upper,
        certificate.epsilon,
        certificate.mean_error,
        certificate.second_error,
        certificate.variance_error,
    ):
        _nonnegative(error)
    expected_epsilon = _up_add(ENDPOINT_ERROR, REFERENCE_ERROR)
    if certificate.epsilon != expected_epsilon:
        raise ValueError("Future endpoint allowance differs from the fixed qualification")
    if certificate.role == "prior":
        uniform = divide(point(1), point(identity.count))
        if certificate.delta_upper != ZERO or any(mass != uniform for mass in masses):
            raise ValueError("No-learning prior requires exact uniform cell masses")
    samples: list[Interval] = []
    endpoint_lower = minus(point(-1), point(certificate.epsilon)).lower
    endpoint_upper = plus(point(1), point(certificate.epsilon)).upper
    for value in values:
        if type(value) is not float:
            raise ValueError("Actual emitted binary64 endpoint samples required")
        sample = point(value)
        if sample.lower < endpoint_lower or sample.upper > endpoint_upper:
            raise ValueError("Endpoint is incompatible with the qualified global support")
        samples.append(sample)
    for mass in masses:
        _interval(mass)
        if not ZERO < mass.lower <= mass.upper <= ONE:
            raise ValueError("Every actual emitted D1 node needs positive finite mass")
    mean = total(tuple(times(m, x) for m, x in zip(masses, samples, strict=True)))
    second = total(tuple(times(m, square(x)) for m, x in zip(masses, samples, strict=True)))
    raw_variance = minus(second, square(mean))
    finite_variance = Interval(max(ZERO, raw_variance.lower), raw_variance.upper)
    radius = _up_add(certificate.epsilon, _up_div(D(9), D(16 * identity.count)))
    continuous_cells = tuple(
        PredictiveCell(i, mass, _clip(around(value.lower, radius), -ONE, ONE))
        for i, (mass, value) in enumerate(zip(masses, samples, strict=True))
    )
    finite_cells = tuple(
        PredictiveCell(i, mass, value)
        for i, (mass, value) in enumerate(zip(masses, samples, strict=True))
    )
    # Finite emitted endpoints may exceed ideal support by epsilon.
    # Their actual observed extrema are the finite distribution's exact support.
    finite_support = Interval(min(x.lower for x in samples), max(x.upper for x in samples))
    finite_cdf = enclose_cdf(finite_cells, ZERO, finite_support, identity.evidence_sha256)
    cdf = enclose_cdf(
        continuous_cells, certificate.delta_upper, Interval(-ONE, ONE), identity.evidence_sha256
    )
    return PredictiveEnclosure(
        certificate,
        mean,
        second,
        finite_variance,
        _clip(_expand(mean, certificate.mean_error), -ONE, ONE),
        _clip(_expand(second, certificate.second_error), ZERO, ONE),
        _clip(_expand(finite_variance, certificate.variance_error), ZERO, ONE),
        (generalized_quantile(finite_cdf, LOW_TAIL), generalized_quantile(finite_cdf, HIGH_TAIL)),
        (generalized_quantile(cdf, LOW_TAIL), generalized_quantile(cdf, HIGH_TAIL)),
        finite_cdf,
        cdf,
    )


def positive_part(value: Interval) -> Interval:
    _interval(value)
    return Interval(max(ZERO, value.lower), max(ZERO, value.upper))


def interval_score(lower: Interval, upper: Interval, truth: Interval) -> Interval:
    for value in (lower, upper, truth):
        _interval(value)
    if lower.lower > upper.upper:
        raise ValueError("No feasible ordered interval endpoints")
    width = positive_part(minus(upper, lower))
    below = positive_part(minus(lower, truth))
    above = positive_part(minus(truth, upper))
    return plus(width, times(point(20), plus(below, above)))


@dataclass(frozen=True)
class ScoreEnclosure:
    prediction: PredictiveEnclosure
    truth: Interval
    truth_evidence_sha256: str
    squared_loss: Interval
    interval_score: Interval


def enclose_scores(
    prediction: PredictiveEnclosure, truth: Interval, truth_evidence_sha256: str
) -> ScoreEnclosure:
    if type(prediction) is not PredictiveEnclosure or not prediction.certificate.passed:
        raise ValueError("Qualified predictive enclosure required")
    _validate_certificate(prediction.certificate)
    _validate_cdf(prediction.cdf)
    _validate_cdf(prediction.finite_cdf)
    for value in (
        prediction.finite_mean,
        prediction.finite_second,
        prediction.finite_variance,
        prediction.mean,
        prediction.second,
        prediction.variance,
    ):
        _interval(value)
    cert = prediction.certificate
    variance_check = minus(prediction.finite_second, square(prediction.finite_mean))
    if (
        prediction.finite_variance
        != Interval(max(ZERO, variance_check.lower), variance_check.upper)
        or prediction.cdf.evidence_sha256 != cert.identity.evidence_sha256
        or prediction.finite_cdf.evidence_sha256 != cert.identity.evidence_sha256
        or prediction.cdf.support != Interval(-ONE, ONE)
        or prediction.cdf.delta_upper != cert.delta_upper
        or prediction.finite_cdf.delta_upper != ZERO
        or prediction.cdf.cell_count != cert.identity.count
        or prediction.finite_cdf.cell_count != cert.identity.count
        or prediction.mean != _clip(_expand(prediction.finite_mean, cert.mean_error), -ONE, ONE)
        or prediction.second
        != _clip(_expand(prediction.finite_second, cert.second_error), ZERO, ONE)
        or prediction.variance
        != _clip(_expand(prediction.finite_variance, cert.variance_error), ZERO, ONE)
        or prediction.quantiles
        != (
            generalized_quantile(prediction.cdf, LOW_TAIL),
            generalized_quantile(prediction.cdf, HIGH_TAIL),
        )
        or prediction.finite_quantiles
        != (
            generalized_quantile(prediction.finite_cdf, LOW_TAIL),
            generalized_quantile(prediction.finite_cdf, HIGH_TAIL),
        )
    ):
        raise ValueError("Predictive moment/quantile/evidence joins disagree")
    _interval(truth)
    _digest(truth_evidence_sha256)
    if truth.lower < -ONE or truth.upper > ONE:
        raise ValueError("Truth enclosure outside the frozen finite diagnostic support")
    low, high = prediction.quantiles
    if low.probability != LOW_TAIL or high.probability != HIGH_TAIL:
        raise ValueError("Only the frozen central90 interval is scored")
    return ScoreEnclosure(
        prediction,
        truth,
        truth_evidence_sha256,
        square(minus(prediction.mean, truth)),
        interval_score(low.value, high.value, truth),
    )


@dataclass(frozen=True)
class PairedScores:
    case: CaseId
    posterior: ScoreEnclosure
    prior: ScoreEnclosure
    point_difference: Interval
    interval_difference: Interval


def pair_scores(posterior: ScoreEnclosure, prior: ScoreEnclosure) -> PairedScores:
    if type(posterior) is not ScoreEnclosure or type(prior) is not ScoreEnclosure:
        raise ValueError("Two typed score enclosures required")
    for score in (posterior, prior):
        if enclose_scores(score.prediction, score.truth, score.truth_evidence_sha256) != score:
            raise ValueError("Score fields must enclose their actual prediction/truth inputs")
    a, b = posterior.prediction.certificate, prior.prediction.certificate
    ia, ib = a.identity, b.identity
    if (
        a.role != "posterior"
        or b.role != "prior"
        or not a.passed
        or not b.passed
        or ia.case != ib.case
        or ia.count != ib.count
        or ia.scale != ib.scale
        or ia.source_commit != ib.source_commit
        or ia.protocol_sha256 != ib.protocol_sha256
        or ia.observation_sha256 != ib.observation_sha256
        or ia.future_query_sha256 != ib.future_query_sha256
        or ia.future_values_sha256 != ib.future_values_sha256
        or posterior.truth != prior.truth
        or posterior.truth_evidence_sha256 != prior.truth_evidence_sha256
    ):
        raise ValueError(
            "Prior/posterior scores must share exact case/probe/truth/source identities"
        )
    return PairedScores(
        ia.case,
        posterior,
        prior,
        minus(posterior.squared_loss, prior.squared_loss),
        minus(posterior.interval_score, prior.interval_score),
    )


@dataclass(frozen=True)
class PanelEntry:
    case: CaseId
    status: Literal["completed", "failed", "unrun"]
    scores: PairedScores | None


@dataclass(frozen=True)
class PanelDecision:
    outcome: Literal["local-screen-passed", "screen-not-met", "inconclusive", "incomplete"]
    planned_worlds: int
    completed_worlds: int
    point_difference: Interval | None
    interval_difference: Interval | None


def classify_matched_panel(rows: tuple[PanelEntry, ...]) -> PanelDecision:
    if type(rows) is not tuple or len(rows) != 4:
        raise ValueError("All four planned matched-world denominators are required")
    expected = ("M01", "M02", "M03", "M04")
    completed: list[PairedScores] = []
    for row, case in zip(rows, expected, strict=True):
        if type(row) is not PanelEntry or row.case != case:
            raise ValueError("Exact ordered M-world panel required, without stress substitutions")
        if row.status not in ("completed", "failed", "unrun"):
            raise ValueError("Unknown panel outcome")
        if (row.scores is not None) != (row.status == "completed"):
            raise ValueError("Unavailable worlds cannot claim scores")
        if row.scores is not None:
            pair = pair_scores(row.scores.posterior, row.scores.prior)
            if pair != row.scores or pair.case != row.case:
                raise ValueError("Paired score differences must bind their actual evidence")
            identity = pair.posterior.prediction.certificate.identity
            if identity.count != 1024 or identity.scale != D("0.25"):
                raise ValueError("Primary panel is fixed to finest grid and base scale")
            completed.append(pair)
    if len(completed) != 4:
        return PanelDecision("incomplete", 4, len(completed), None, None)
    if len({p.posterior.prediction.certificate.identity.source_commit for p in completed}) != 1:
        raise ValueError("A panel cannot pool different implementation versions")
    point_delta = divide(total(tuple(p.point_difference for p in completed)), point(4))
    interval_delta = divide(total(tuple(p.interval_difference for p in completed)), point(4))
    return PanelDecision(
        _screen_outcome(point_delta, interval_delta), 4, 4, point_delta, interval_delta
    )


def _screen_outcome(
    point_difference: Interval, interval_difference: Interval
) -> Literal["local-screen-passed", "screen-not-met", "inconclusive"]:
    _interval(point_difference)
    _interval(interval_difference)
    if point_difference.upper < ZERO and interval_difference.upper < ZERO:
        return "local-screen-passed"
    if point_difference.lower >= ZERO or interval_difference.lower >= ZERO:
        return "screen-not-met"
    return "inconclusive"
