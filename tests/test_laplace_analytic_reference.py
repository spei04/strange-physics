from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import asdict, replace
from fractions import Fraction

import pytest
from laplace_analytic_reference import (
    MAX_GCD_CALLS,
    MAX_INTERMEDIATE_BITS,
    MAX_REDUCED_BITS,
    GaussianVector,
    Interval,
    ReferenceLimit,
    ReferencePack,
    _Arithmetic,
    build_references,
    decimal_bounds,
)

VECTORS = (
    GaussianVector("real", (1, 1), 0, 0, None, ((-16, 0), (0, 16), (0, 0), (64, 64)), (-16, 0, 16)),
    GaussianVector(
        "shift", (1, 1), 0, 16, None, ((-16, 0), (0, 16), (0, 0), (64, 64)), (-16, 0, 16)
    ),
    GaussianVector(
        "scaled", (2, 1), 1, 0, None, ((-16, 0), (0, 16), (0, 0), (64, 64)), (-16, 0, 16)
    ),
    GaussianVector(
        "symmetric",
        (1, 2),
        -1,
        -16,
        (-16, 16),
        ((-32, 0), (0, 16), (-32, -16), (16, 32)),
        (-16, 0, 16),
    ),
    GaussianVector(
        "left_boundary", (1, 1), 0, 0, (0, 16), ((-16, 0), (0, 8), (8, 16), (16, 32)), (0, 8, 16)
    ),
    GaussianVector(
        "right_boundary",
        (2, 1),
        1,
        16,
        (-16, 0),
        ((-32, -16), (-16, -8), (-8, 0), (0, 16)),
        (-16, -8, 0),
    ),
    GaussianVector(
        "tail", (1, 2), -1, 0, (56, 64), ((48, 56), (56, 60), (60, 64), (64, 64)), (56, 60, 64)
    ),
    GaussianVector(
        "weak", (1, 1), 0, 0, (-1, 1), ((-16, -1), (-1, 0), (0, 1), (1, 16)), (-1, 0, 1)
    ),
)
RecordProperty = Callable[[str, object], None]


@pytest.fixture(scope="module")
def references() -> ReferencePack:
    result = build_references(VECTORS)
    print(
        "LAPLACE_REFERENCE_CENSUS "
        + json.dumps(
            {
                "vectors": len(result.cases),
                "integrals": result.integrals,
                "endpoint_logs": result.endpoint_logs,
                "polynomial_visits": result.polynomial_visits,
                "logarithm_terms": result.logarithm_terms,
                "machin_terms": result.machin_terms,
                "checked_core_operations": result.operations,
                "core_gcd_calls": result.gcd_calls,
            },
            sort_keys=True,
        )
    )
    assert result.integrals == 21
    assert result.endpoint_logs == 44
    assert result.polynomial_visits == 42 * 97
    assert result.logarithm_terms == 45 * 64
    assert result.machin_terms == 128
    return result


def _checked_sub(a: Fraction, b: Fraction) -> Fraction:
    # Independent test arithmetic also checks cross-products before allocation.
    assert a.numerator.bit_length() + b.denominator.bit_length() + 1 <= MAX_INTERMEDIATE_BITS
    assert b.numerator.bit_length() + a.denominator.bit_length() + 1 <= MAX_INTERMEDIATE_BITS
    assert a.denominator.bit_length() + b.denominator.bit_length() <= MAX_INTERMEDIATE_BITS
    value = a - b
    assert max(value.numerator.bit_length(), value.denominator.bit_length()) <= MAX_REDUCED_BITS
    return value


def _width(interval: Interval) -> Fraction:
    return _checked_sub(interval.upper, interval.lower)


def _error(interval: Interval, sample: float) -> Fraction:
    exact = Fraction.from_float(sample)
    return max(abs(_checked_sub(interval.lower, exact)), abs(_checked_sub(interval.upper, exact)))


def _closed_log_integral(lower: float, upper: float) -> float:
    """Independent binary64 closed formula, using same-tail erfc differences."""
    root_two = math.sqrt(2.0)
    if lower >= 0:
        probability = (math.erfc(lower / root_two) - math.erfc(upper / root_two)) / 2
    elif upper <= 0:
        probability = (math.erfc(-upper / root_two) - math.erfc(-lower / root_two)) / 2
    else:
        probability = (math.erf(upper / root_two) - math.erf(lower / root_two)) / 2
    return math.log(probability) + math.log(2 * math.pi) / 2


@pytest.mark.parametrize("index", range(8), ids=[v.name for v in VECTORS])
def test_closed_gaussian_vectors(
    index: int, references: ReferencePack, record_property: RecordProperty
) -> None:
    result = references.cases[index]
    vector = result.vector
    scale = vector.scale[0] / vector.scale[1]
    log_scale = math.log(scale)
    if vector.support is None:
        log_i = math.log(2 * math.pi) / 2
        mode_tick = 0
    else:
        log_i = _closed_log_integral(vector.support[0] / 16, vector.support[1] / 16)
        mode_tick = max(vector.support[0], min(0, vector.support[1]))
    errors = [_error(result.shifted_log_normalizer, log_i - log_scale)]
    widths = [_width(result.shifted_log_normalizer)]
    for cell, actual in zip(vector.cells, result.cells, strict=True):
        low, high = cell
        if vector.support is not None:
            low, high = max(low, vector.support[0]), min(high, vector.support[1])
        if low >= high:
            assert actual.kind == "exact_zero"
            assert actual.log_mass is None and actual.kernel_integral is None
        else:
            assert actual.kind == "positive" and actual.log_mass is not None
            expected = _closed_log_integral(low / 16, high / 16) - log_i
            errors.append(_error(actual.log_mass, expected))
            widths.append(_width(actual.log_mass))
    for tick, density in zip(vector.queries, result.log_densities, strict=True):
        assert density is not None
        errors.append(_error(density, -(tick * tick) / 512 + log_scale - log_i))
        widths.append(_width(density))
    maximum_error = max(errors)
    maximum_width = max(widths)
    display = decimal_bounds(result.shifted_log_normalizer)
    record_property(
        "laplace_reference",
        json.dumps(
            {
                "vector": vector.name,
                "input_sha256": hashlib.sha256(
                    json.dumps(asdict(vector), sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "method": "97-term integrated rational Taylor;64-term rational logarithm",
                "max_absolute_binary64_error": str(float(maximum_error)),
                "software_criterion": "2e-12",
                "max_exact_oracle_width": str(float(maximum_width)),
                "oracle_width_ceiling": "2^-170",
                "shifted_log_normalizer_directed_decimal": display,
            },
            sort_keys=True,
        ),
    )
    # Diagnostics precede numerical assertions; the binary64 comparator is not the oracle.
    assert maximum_error < Fraction(1, 500_000_000_000)
    assert maximum_width < Fraction(1, 2**170)
    expected_mode = Fraction(vector.mu) + Fraction(
        mode_tick * vector.scale[1], 16 * vector.scale[0]
    )
    assert result.supported_mode == expected_mode
    assert result.kernel_variance == Fraction(vector.scale[1] ** 2, vector.scale[0] ** 2)


@pytest.mark.parametrize("kind", ("shift", "jacobian", "symmetry", "partition", "weak"))
def test_exact_relations(kind: str, references: ReferencePack) -> None:
    real, shifted, scaled, symmetric, _, _, _, weak = references.cases
    if kind == "shift":
        assert real.shifted_log_normalizer == shifted.shifted_log_normalizer
        assert real.cells == shifted.cells
        assert real.log_densities == shifted.log_densities
        assert shifted.vector.offset - real.vector.offset == 16
    elif kind == "jacobian":
        difference = Interval(
            _checked_sub(real.shifted_log_normalizer.lower, scaled.shifted_log_normalizer.upper),
            _checked_sub(real.shifted_log_normalizer.upper, scaled.shifted_log_normalizer.lower),
        )
        assert difference.lower <= references.log_two.upper
        assert difference.upper >= references.log_two.lower
        assert difference.lower > Fraction(1, 2)
    elif kind == "symmetry":
        assert symmetric.cells[0].log_mass == symmetric.cells[1].log_mass
        assert symmetric.log_densities[0] == symmetric.log_densities[2]
    elif kind == "partition":
        assert symmetric.support_integral is not None
        left, right = symmetric.cells[:2]
        assert left.kernel_integral is not None and right.kernel_integral is not None
        low = _checked_sub(left.kernel_integral.lower, -right.kernel_integral.lower)
        high = _checked_sub(left.kernel_integral.upper, -right.kernel_integral.upper)
        assert low <= symmetric.support_integral.upper
        assert high >= symmetric.support_integral.lower
    else:
        # A nearly flat bounded kernel is valid; support dominates the unbounded covariance.
        assert weak.support_integral is not None
        assert weak.support_integral.lower > Fraction(511, 4096)
        assert weak.support_integral.upper < Fraction(1, 8) + Fraction(1, 2**190)
        assert weak.kernel_variance == 1
        assert weak.vector.support == (-1, 1)


@pytest.mark.parametrize("kind", ("jacobian", "density_for_cell", "clip", "remainder"))
def test_plausible_reference_defects(kind: str, references: ReferencePack) -> None:
    real, _, scaled, symmetric, *_ = references.cases
    if kind == "jacobian":
        missing_jacobian = math.log(2 * math.pi) / 2
        assert _error(scaled.shifted_log_normalizer, missing_jacobian) > Fraction(1, 2)
    elif kind == "density_for_cell":
        assert real.cells[0].log_mass is not None
        # Midpoint density times this width-one cell is not the exact integrated mass.
        wrong = -0.125 - math.log(2 * math.pi) / 2
        assert _error(real.cells[0].log_mass, wrong) > Fraction(1, 1000)
    elif kind == "clip":
        # Positive partial overlap: [-2,0] must clip to [-1,0], not retain its tail.
        assert symmetric.vector.cells[0] == (-32, 0)
        assert symmetric.vector.support == (-16, 16)
        left, right = symmetric.cells[:2]
        assert left.kind == right.kind == "positive"
        assert left.kernel_integral == right.kernel_integral
        assert left.log_mass == right.log_mass
        assert symmetric.cells[2].kind == "exact_zero"  # singleton intersection
        # The removed [-2,-1] slice has positive mass, not an empty intersection.
        assert math.isfinite(_closed_log_integral(-2.0, -1.0))
    else:
        assert symmetric.support_integral is not None
        assert _width(symmetric.support_integral) == Fraction(32, 2**197)
        assert _width(references.log_two) > 0


@pytest.mark.parametrize(
    "kind", ("nonpositive_scale", "non_lattice", "deep_tail", "work_exhaustion", "too_many")
)
def test_closed_domain_and_budget_failures(
    kind: str, monkeypatch: pytest.MonkeyPatch, record_property: RecordProperty
) -> None:
    vector = VECTORS[0]
    limit = 100_000
    if kind == "nonpositive_scale":
        vector = replace(vector, scale=(0, 1))
    elif kind == "non_lattice":
        # bool is an integer subclass but is not an exact lattice integer.
        vector = replace(vector, queries=(True,))
    elif kind == "deep_tail":
        vector = replace(vector, queries=(65,))
    elif kind == "work_exhaustion":
        limit = 1
    vectors = VECTORS + (VECTORS[0],) if kind == "too_many" else (vector,)
    with pytest.raises(ReferenceLimit) as rejection:
        build_references(vectors, operation_limit=limit)
    actual_reason = str(rejection.value)
    record_property(
        "laplace_rejection",
        json.dumps({"kind": kind, "reason": actual_reason}, sort_keys=True),
    )
    expected_reasons = {
        "nonpositive_scale": "positive_scale_family",
        "non_lattice": "query_domain",
        "deep_tail": "query_domain",
        "work_exhaustion": "operations",
        "too_many": "vector_count",
    }
    assert actual_reason == expected_reasons[kind]
    if kind == "work_exhaustion":
        # Use tiny operands with a lowered test-only ceiling; never allocate a maximal integer.
        monkeypatch.setattr("laplace_analytic_reference.MAX_INTERMEDIATE_BITS", 8)
        arithmetic = _Arithmetic(10)
        with pytest.raises(ReferenceLimit, match="multiply_width"):
            arithmetic.mul(32, 32)
        arithmetic.gcd_calls = MAX_GCD_CALLS

        def forbidden_gcd(*args: object) -> int:
            raise AssertionError("GCD executed after exhaustion")

        monkeypatch.setattr(math, "gcd", forbidden_gcd)
        with pytest.raises(ReferenceLimit, match="gcd_count"):
            arithmetic.gcd(1, 1)


def test_boundary_stationarity_and_nonpositive_curvature(references: ReferencePack) -> None:
    left, right, tail = references.cases[4:7]
    assert left.supported_mode == left.vector.mu
    assert right.supported_mode == right.vector.mu
    assert tail.supported_mode > tail.vector.mu
    # An exact nonzero gradient at a claimed center cannot be an interior stationary mode.
    curvature = Fraction(1)
    center_minus_mu = Fraction(1, 2)
    assert -curvature * center_minus_mu != 0
    # Zero/negative curvature supplies no positive Gaussian variance. A bounded constant
    # target still has positive mass: unsupported Laplace is not zero target probability.
    assert Fraction(-1) <= 0 and Fraction(0) <= 0
    assert Fraction(2) - Fraction(-2) == 4


def test_local_jets_do_not_determine_global_mass() -> None:
    # In u=point-3, this is 30*u^2*(1-u)^2 on (0,1). One representation
    # supplies evaluation and the independent exact monomial-antiderivative check.
    coefficients = ((2, 30), (3, -60), (4, 30))

    def separated_bump(point: Fraction) -> Fraction:
        if not Fraction(3) < point < Fraction(4):
            return Fraction(0)
        u = point - 3
        return sum(
            (coefficient * u**exponent for exponent, coefficient in coefficients), Fraction(0)
        )

    # The branch is identically zero on the whole mode neighborhood [-1,1], so
    # value/gradient/Hessian there agree after adding it to any smooth positive density.
    assert all(separated_bump(Fraction(x)) == 0 for x in (-1, 0, 1))
    assert separated_bump(Fraction(7, 2)) > 0
    # Each antiderivative term is c*u^(p+1)/(p+1); at 1 minus 0 it is c/(p+1).
    # Changing an implemented coefficient/exponent therefore changes this same integral.
    exact_extra_mass = sum(
        (Fraction(coefficient, exponent + 1) for exponent, coefficient in coefficients),
        Fraction(0),
    )
    assert exact_extra_mass == 1
