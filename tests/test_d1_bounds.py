"""Rational/synthetic bounds tests only; no D1 truth, oracle, simulator or predictor."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, localcontext
from fractions import Fraction

import pytest
from d1_bounds import (
    CDFEnvelope,
    CDFKnot,
    D1Identity,
    D1PrefixPremises,
    PanelEntry,
    PredictiveCell,
    PredictiveEnclosure,
    _screen_outcome,
    cdf_at,
    certify_d1_prefix,
    certify_d1_prior,
    classify_matched_panel,
    enclose_cdf,
    enclose_predictive,
    enclose_scores,
    generalized_quantile,
    interval_score,
    pair_scores,
)
from grid_q1_bounds import ArithmeticEvidence, EndpointEvidence, Interval
from grid_q1_evidence import divide, plus, point, times

from strange_physics.calibration_fixture_contracts import CASE_IDS, CaseId

D = Decimal
S, T, U = "a" * 64, "b" * 64, "c" * 64


def identity(case: CaseId = "M03", count: int = 256, scale: str = "0.25") -> D1Identity:
    return D1Identity(case, count, D(scale), "d" * 40, S, T, U, S, T)


def endpoint(count: int) -> EndpointEvidence:
    indices = tuple(range(count))
    return EndpointEvidence(D(0), D("1e-60"), indices, indices, ())


def premises(case: CaseId = "M03", count: int = 256, scale: str = "0.25") -> D1PrefixPremises:
    i = identity(case, count, scale)
    records = 2 if case == "D03" else 1
    label = 0.09375 if case == "W03" else 0.75
    return D1PrefixPremises(
        i,
        (point(label),) * records,
        (endpoint(count),) * records,
        endpoint(count),
        ArithmeticEvidence(D(0), D("1e-48"), D(0), D(0), D(0)),
    )


def cdf(
    locations: tuple[str, ...],
    masses: tuple[str, ...],
    delta: str = "0",
    support: tuple[str, str] = ("-1", "1"),
) -> CDFEnvelope:
    return enclose_cdf(
        tuple(
            PredictiveCell(i, point(D(m)), point(D(x)))
            for i, (x, m) in enumerate(zip(locations, masses, strict=True))
        ),
        D(delta),
        Interval(D(support[0]), D(support[1])),
        S,
    )


def prediction(
    case: CaseId = "M03", *, prior: bool = False, count: int = 256
) -> PredictiveEnclosure:
    p = premises(case, count)
    cert = certify_d1_prior(p.identity, p.future) if prior else certify_d1_prefix(p)
    # Explicit synthetic surrogate arrays. They are not the physical D1 cosine map.
    values = tuple(1.0 - (i + 0.5) / count for i in range(count))
    unit = divide(point(1), point(count))
    weights = (
        (unit,) * count
        if prior
        else (
            (times(unit, point(D("1.98"))),) * (count // 2)
            + (times(unit, point(D("0.02"))),) * (count // 2)
        )
    )
    return enclose_predictive(cert, values, weights, future_values_sha256=U, probabilities_sha256=S)


@pytest.mark.parametrize("case", CASE_IDS)
def test_fixed_prefix_shapes_have_conditional_bounds(case: CaseId) -> None:
    p = premises(case, 1024)
    result = certify_d1_prefix(p)
    assert result.identity == p.identity
    assert result.passed and not result.reasons
    assert result.fixed_reserve == D("3e-9")
    assert result.delta_upper == plus(point(result.variation_upper), point(D("3e-9"))).upper
    assert result.mean_error <= D("0.018")
    assert result.second_error <= D("0.019")
    assert result.variance_error <= D("0.056")


def test_duplicate_sums_every_endpoint_term_with_one_reserve() -> None:
    one = certify_d1_prefix(premises())
    two = certify_d1_prefix(premises("D03"))
    assert two.endpoint_log_upper == times(point(2), point(one.endpoint_log_upper)).upper
    assert two.log_derivative_upper == times(point(2), point(one.log_derivative_upper)).upper
    assert two.variation_upper == times(point(2), point(one.variation_upper)).upper
    assert two.fixed_reserve == one.fixed_reserve == D("3e-9")


def test_weak_excitation_uses_its_own_derivative_and_residual() -> None:
    strong = certify_d1_prefix(premises())
    weak = certify_d1_prefix(premises("W03"))
    assert weak.log_derivative_upper < strong.log_derivative_upper
    assert weak.endpoint_log_upper < strong.endpoint_log_upper
    assert weak.mean_error < strong.mean_error


@pytest.mark.parametrize(
    "change", ("record_missing", "repeated_value", "node_missing", "failed_node")
)
def test_prefix_incompleteness_never_normalizes_survivors(change: str) -> None:
    p = premises("D03")
    with pytest.raises(ValueError):
        if change == "record_missing":
            replace(p, recorded=p.recorded[:1])
        elif change == "repeated_value":
            replace(p, recorded=(point(0.75), point(0.8)))
        elif change == "node_missing":
            replace(p, training=(replace(p.training[0], completed=(0,)), p.training[1]))
        else:
            replace(p, future=replace(p.future, failed=(0,)))


@pytest.mark.parametrize("change", ("grid", "scale", "repeat_scale", "protocol", "digest"))
def test_undeclared_profiles_fail_before_arithmetic(change: str) -> None:
    with pytest.raises(ValueError):
        if change == "grid":
            identity(count=64)
        elif change == "scale":
            identity(scale="0.01")
        elif change == "repeat_scale":
            identity("D03", scale="0.125")
        elif change == "protocol":
            replace(identity(), protocol_sha256=S)
        else:
            replace(identity(), probabilities_sha256="x")


def test_native_whole_prefix_remainder_cannot_be_hidden_by_good_observed_error() -> None:
    p = premises("D03")
    p = replace(p, arithmetic=replace(p.arithmetic, node_other_arithmetic_upper=D("2e-9")))
    result = certify_d1_prefix(p)
    assert not result.passed
    assert "whole_prefix_node_error" in result.reasons
    assert result.reserve_components[0] > D("2e-9")


def test_prior_has_exact_cell_mass_and_no_likelihood_reserve() -> None:
    p = premises()
    result = certify_d1_prior(p.identity, p.future)
    assert result.role == "prior" and result.prefix is None
    assert result.delta_upper == result.variation_upper == result.fixed_reserve == 0
    assert result.mean_error < certify_d1_prefix(p).mean_error


def test_certificate_arithmetic_mutation_is_rejected() -> None:
    cert = replace(certify_d1_prefix(premises()), delta_upper=D(0), mean_error=D(0))
    with pytest.raises(ValueError, match="arithmetic"):
        enclose_predictive(
            cert,
            (0.5,) * 256,
            (point(D("0.00390625")),) * 256,
            future_values_sha256=U,
            probabilities_sha256=S,
        )


def test_endpoint_failure_cannot_be_relabelled_passed() -> None:
    p = premises()
    p = replace(p, future=replace(p.future, max_abs_error_upper=D("1e-11")))
    cert = certify_d1_prefix(p)
    assert not cert.passed
    with pytest.raises(ValueError, match="failed"):
        enclose_predictive(
            replace(cert, passed=True, reasons=()),
            (0.5,) * 256,
            (point(D("0.00390625")),) * 256,
            future_values_sha256=U,
            probabilities_sha256=S,
        )


def test_point_atoms_and_threshold_equality_use_generalized_inverse() -> None:
    value = cdf(("0", "1"), ("0.05", "0.95"))
    assert generalized_quantile(value, D("0.05")).value == point(0)
    assert generalized_quantile(value, D("0.95")).value == point(1)
    assert cdf_at(value, D("-2")) == point(0)
    assert cdf_at(value, D(1)) == point(1)


def test_tied_points_aggregate_before_threshold_comparison() -> None:
    value = cdf(("0", "0", "1"), ("0.02", "0.03", "0.95"))
    assert generalized_quantile(value, D("0.05")).value == point(0)
    assert value.mass_updates == 6
    assert len(value.knots) == 3  # support -1, point0, support/point1


def test_degenerate_support_has_finite_quantiles_even_with_large_delta() -> None:
    value = cdf(("0.5",), ("1",), "0.5", ("0.5", "0.5"))
    for probability in (D("0.05"), D("0.95")):
        assert generalized_quantile(value, probability).value == point(D("0.5"))
    assert cdf_at(value, D("0.49")) == point(0)


def test_uniform_continuous_surrogate_quantile_is_inside_cell_enclosure() -> None:
    # Uniform X on[0,1], represented by four exact cell masses/ranges.
    cells = (
        PredictiveCell(0, point(D("0.25")), Interval(D(0), D("0.25"))),
        PredictiveCell(1, point(D("0.25")), Interval(D("0.25"), D("0.5"))),
        PredictiveCell(2, point(D("0.25")), Interval(D("0.5"), D("0.75"))),
        PredictiveCell(3, point(D("0.25")), Interval(D("0.75"), D(1))),
    )
    value = enclose_cdf(cells, D(0), Interval(D(0), D(1)), S)
    for probability in (D("0.05"), D("0.25"), D("0.5"), D("0.95")):
        enclosed = generalized_quantile(value, probability).value
        assert enclosed.lower <= probability <= enclosed.upper
    assert generalized_quantile(value, D("0.05")).crossing_ambiguous


def test_mass_intervals_crossing_and_delta_tail_remain_ambiguous() -> None:
    cells = (
        PredictiveCell(0, Interval(D("0.04"), D("0.06")), point(0)),
        PredictiveCell(1, Interval(D("0.94"), D("0.96")), point(1)),
    )
    value = enclose_cdf(cells, D(0), Interval(D(0), D(1)), S)
    assert generalized_quantile(value, D("0.05")).value == Interval(D(0), D(1))
    widened = enclose_cdf(cells, D("0.1"), Interval(D(-1), D(1)), S)
    assert generalized_quantile(widened, D("0.05")).value.lower == -1
    assert generalized_quantile(widened, D("0.95")).value.upper == 1


def test_widening_masses_images_and_tv_never_narrows_quantile_claim() -> None:
    narrow = enclose_cdf(
        (
            PredictiveCell(0, point(D("0.25")), point(0)),
            PredictiveCell(1, point(D("0.75")), point(D("0.5"))),
        ),
        D(0),
        Interval(D(-1), D(1)),
        S,
    )
    wide = enclose_cdf(
        (
            PredictiveCell(0, Interval(D("0.2"), D("0.3")), Interval(D("-0.1"), D("0.1"))),
            PredictiveCell(1, Interval(D("0.7"), D("0.8")), Interval(D("0.4"), D("0.6"))),
        ),
        D("0.01"),
        Interval(D(-1), D(1)),
        S,
    )
    for p in (D("0.05"), D("0.95")):
        a, b = generalized_quantile(narrow, p).value, generalized_quantile(wide, p).value
        assert b.lower <= a.lower <= a.upper <= b.upper


@pytest.mark.parametrize(
    "kind", ("missing_mass", "excess_mass", "wrong_index", "bad_support", "nan")
)
def test_invalid_cdf_inputs_fail_closed(kind: str) -> None:
    cells = (PredictiveCell(0, point(1), point(0)),)
    support, delta = Interval(D(-1), D(1)), D(0)
    with pytest.raises(ValueError):
        if kind == "missing_mass":
            cells = (PredictiveCell(0, point(D("0.9")), point(0)),)
        elif kind == "excess_mass":
            cells = (PredictiveCell(0, point(D("1.1")), point(0)),)
        elif kind == "wrong_index":
            cells = (PredictiveCell(1, point(1), point(0)),)
        elif kind == "bad_support":
            support = Interval(D("0.1"), D(1))
        else:
            delta = D("NaN")
        enclose_cdf(cells, delta, support, S)


@pytest.mark.parametrize("residual", ("above", "below", "minimum_exponent"))
@pytest.mark.parametrize("ambient_precision", (3, 80))
def test_exact_mass_feasibility_rejects_tiny_residuals(
    residual: str, ambient_precision: int
) -> None:
    if residual == "above":
        masses = (D("0.5"), D("0.5" + "0" * 108 + "1"))
    elif residual == "below":
        masses = (D("0.5"), D("0.4" + "9" * 109))
    else:
        masses = (D(1), D("1e-256"))
    cells = tuple(PredictiveCell(i, point(m), point(0)) for i, m in enumerate(masses))
    with localcontext() as context:
        context.prec = ambient_precision
        context.rounding = ROUND_DOWN
        context.Emin, context.Emax = -9, 9
        with pytest.raises(ValueError, match="single normalized probability vector"):
            enclose_cdf(cells, D(0), point(0), S)


@pytest.mark.parametrize("ambient_precision", (3, 80))
def test_exact_mass_feasibility_preserves_tiny_feasible_interval(ambient_precision: int) -> None:
    second = Interval(D("0.4" + "9" * 109), D("0.5" + "0" * 108 + "1"))
    cells = (PredictiveCell(0, point(D("0.5")), point(0)), PredictiveCell(1, second, point(0)))
    with localcontext() as context:
        context.prec = ambient_precision
        context.rounding = ROUND_DOWN
        context.Emin, context.Emax = -9, 9
        value = enclose_cdf(cells, D(0), point(0), S)
        assert value.knots == (CDFKnot(D(0), point(1)),)
        assert generalized_quantile(value, D("0.05")).value == point(0)
        assert value.mass_updates == 4


def test_malformed_persisted_cdf_cannot_remove_support_terminal() -> None:
    value = cdf(("0", "1"), ("0.5", "0.5"))
    malformed = replace(value, knots=(*value.knots[:-1], CDFKnot(D(1), point(D("0.9")))))
    with pytest.raises(ValueError, match="incomplete"):
        generalized_quantile(malformed, D("0.95"))


@pytest.mark.parametrize(
    "truth,expected", (("0.5", "1"), ("0", "1"), ("1", "1"), ("-0.1", "3"), ("1.1", "3"))
)
def test_interval_score_exact_boundaries_and_miss_penalty(truth: str, expected: str) -> None:
    assert interval_score(point(0), point(1), point(D(truth))) == point(D(expected))


def test_score_encloses_uncertain_truth_and_ordered_endpoints() -> None:
    score = interval_score(
        Interval(D(0), D("0.1")), Interval(D("0.9"), D(1)), Interval(D("-0.1"), D("1.1"))
    )
    assert score.lower >= 0
    for lo, hi, truth in ((D(0), D(1), D("0.5")), (D("0.1"), D("0.9"), D("-0.1"))):
        exact = interval_score(point(lo), point(hi), point(truth))
        assert score.lower <= exact.lower <= exact.upper <= score.upper
    with pytest.raises(ValueError, match="ordered"):
        interval_score(point(1), point(0), point(0))


def test_predictive_outputs_keep_finite_and_continuous_targets_separate() -> None:
    value = prediction()
    assert value.cdf.mass_updates == value.finite_cdf.mass_updates == 512
    assert (
        value.mean.lower <= value.finite_mean.lower <= value.finite_mean.upper <= value.mean.upper
    )
    assert value.cdf.delta_upper > value.finite_cdf.delta_upper == 0
    assert len(value.cdf.knots) <= 2 * 256 + 2
    assert all(q.probability in (D("0.05"), D("0.95")) for q in value.quantiles)


@pytest.mark.parametrize("kind", ("future", "mass", "length", "prior_mass"))
def test_predictive_joins_reject_other_arrays_or_prior_weights(kind: str) -> None:
    p = premises()
    cert = certify_d1_prior(p.identity, p.future)
    values: tuple[float, ...] = (0.5,) * 256
    masses = (point(D("0.00390625")),) * 256
    future_hash, mass_hash = U, S
    if kind == "future":
        future_hash = T
    elif kind == "mass":
        mass_hash = T
    elif kind == "length":
        values = values[:-1]
    else:
        masses = (point(D("0.003")),) + masses[1:]
    with pytest.raises(ValueError):
        enclose_predictive(
            cert, values, masses, future_values_sha256=future_hash, probabilities_sha256=mass_hash
        )


def test_score_joins_recompute_fields_and_bind_truth() -> None:
    posterior = enclose_scores(prediction(), point(D("0.75")), S)
    prior = enclose_scores(prediction(prior=True), point(D("0.75")), S)
    pair = pair_scores(posterior, prior)
    assert pair.case == "M03"
    with pytest.raises(ValueError, match="Score fields"):
        pair_scores(replace(posterior, squared_loss=point(-1)), prior)
    with pytest.raises(ValueError, match="truth"):
        pair_scores(posterior, replace(prior, truth_evidence_sha256=T))


@pytest.mark.parametrize(
    "point_bounds,interval_bounds,outcome",
    (
        (("-2", "-1"), ("-1", "-0.1"), "local-screen-passed"),
        (("0", "0"), ("-1", "-0.1"), "screen-not-met"),
        (("-1", "-0.1"), ("0", "0"), "screen-not-met"),
        (("-1", "0.1"), ("-1", "-0.1"), "inconclusive"),
        (("-1", "-0.1"), ("-1", "0.1"), "inconclusive"),
        (("0.1", "1"), ("-1", "1"), "screen-not-met"),
    ),
)
def test_frozen_two_metric_sign_rule(
    point_bounds: tuple[str, str], interval_bounds: tuple[str, str], outcome: str
) -> None:
    assert (
        _screen_outcome(Interval(*map(D, point_bounds)), Interval(*map(D, interval_bounds)))
        == outcome
    )


def test_no_survivor_panel_and_no_stress_case_substitution() -> None:
    cases: tuple[CaseId, ...] = ("M01", "M02", "M03", "M04")
    rows = tuple(PanelEntry(case, "unrun", None) for case in cases)
    outcome = classify_matched_panel(rows)
    assert outcome.outcome == "incomplete"
    assert outcome.planned_worlds == 4 and outcome.completed_worlds == 0
    assert outcome.point_difference is None and outcome.interval_difference is None
    with pytest.raises(ValueError):
        classify_matched_panel(rows[:-1])
    with pytest.raises(ValueError):
        classify_matched_panel((*rows[:3], PanelEntry("F04", "unrun", None)))


def test_ambient_decimal_context_does_not_change_certificate_cdf_or_score() -> None:
    p = premises("D03")
    before = certify_d1_prefix(p)
    value = cdf(("0", "1"), ("0.05", "0.95"), "0.01")
    expected_quantile = generalized_quantile(value, D("0.05"))
    expected_score = interval_score(point(0), point(1), point(D("-0.1")))
    with localcontext() as context:
        context.prec = 4
        context.rounding = ROUND_DOWN
        assert certify_d1_prefix(p) == before
        assert generalized_quantile(value, D("0.05")) == expected_quantile
        assert interval_score(point(0), point(1), point(D("-0.1"))) == expected_score


def test_prior_linear_surrogate_contains_known_continuous_moments_and_quantiles() -> None:
    value = prediction(prior=True)
    for interval, exact in (
        (value.mean, Fraction(1, 2)),
        (value.second, Fraction(1, 3)),
        (value.variance, Fraction(1, 12)),
        (value.quantiles[0].value, Fraction(1, 20)),
        (value.quantiles[1].value, Fraction(19, 20)),
    ):
        assert Fraction(interval.lower) <= exact <= Fraction(interval.upper)


def test_full_matched_panel_aggregates_both_metrics_and_preserves_incomplete_rows() -> None:
    cases: tuple[CaseId, ...] = ("M01", "M02", "M03", "M04")
    rows = tuple(
        PanelEntry(
            case,
            "completed",
            pair_scores(
                enclose_scores(prediction(case, count=1024), point(D("0.75")), S),
                enclose_scores(prediction(case, prior=True, count=1024), point(D("0.75")), S),
            ),
        )
        for case in cases
    )
    result = classify_matched_panel(rows)
    assert result.outcome == "local-screen-passed"
    assert result.point_difference is not None and result.point_difference.upper < 0
    assert result.interval_difference is not None and result.interval_difference.upper < 0
    incomplete = classify_matched_panel((*rows[:3], PanelEntry("M04", "failed", None)))
    assert incomplete.outcome == "incomplete" and incomplete.completed_worlds == 3
    assert incomplete.point_difference is None and incomplete.interval_difference is None


@pytest.mark.parametrize("bad", ("NaN", "Infinity", "-Infinity"))
def test_nonfinite_tv_never_enters_cdf_sort_or_accumulation(bad: str) -> None:
    with pytest.raises(ValueError):
        enclose_cdf((PredictiveCell(0, point(1), point(0)),), D(bad), Interval(D(-1), D(1)), S)


def test_signed_zero_and_exact_tie_have_same_quantile_value() -> None:
    value = cdf(("-0", "0", "1"), ("0.02", "0.03", "0.95"))
    assert generalized_quantile(value, D("0.05")).value == point(0)
    assert interval_score(point(D("-0")), point(1), point(0)) == point(1)
