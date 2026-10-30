"""Closed test-only rational Gaussian references; no native or inference imports."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from fractions import Fraction
from typing import Literal, cast

MAX_REDUCED_BITS = 2_097_152
MAX_INTERMEDIATE_BITS = 4_194_304
MAX_OPERATIONS = 100_000
MAX_GCD_CALLS = 4_096


class ReferenceLimit(ValueError):
    """The declared reference domain or finite work bound was exceeded."""


@dataclass(frozen=True)
class Interval:
    lower: Fraction
    upper: Fraction


@dataclass(frozen=True)
class GaussianVector:
    name: str
    scale: tuple[int, int]
    mu: int
    offset: int
    support: tuple[int, int] | None
    cells: tuple[tuple[int, int], ...]
    queries: tuple[int, ...]


@dataclass(frozen=True)
class CellReference:
    kind: Literal["positive", "exact_zero"]
    kernel_integral: Interval | None
    log_mass: Interval | None


@dataclass(frozen=True)
class GaussianReference:
    vector: GaussianVector
    supported_mode: Fraction
    kernel_variance: Fraction
    shifted_log_normalizer: Interval
    support_integral: Interval | None
    cells: tuple[CellReference, ...]
    log_densities: tuple[Interval | None, ...]


@dataclass(frozen=True)
class ReferencePack:
    cases: tuple[GaussianReference, ...]
    log_two: Interval
    operations: int
    gcd_calls: int
    integrals: int
    endpoint_logs: int
    polynomial_visits: int
    logarithm_terms: int
    machin_terms: int


class _Arithmetic:
    """Bound every integer allocation before core arithmetic, including GCD input."""

    def __init__(self, operation_limit: int) -> None:
        if type(operation_limit) is not int or not 1 <= operation_limit <= MAX_OPERATIONS:
            raise ReferenceLimit("operation_limit")
        self.limit = operation_limit
        self.operations = 0
        self.gcd_calls = 0
        self.integrals = 0
        self.endpoint_logs = 0
        self.polynomial_visits = 0
        self.logarithm_terms = 0
        self.machin_terms = 0

    def tick(self) -> None:
        if self.operations >= self.limit:
            raise ReferenceLimit("operations")
        self.operations += 1

    def integer(self, value: int) -> None:
        if type(value) is not int or value.bit_length() > MAX_INTERMEDIATE_BITS:
            raise ReferenceLimit("integer_width")

    def add(self, a: int, b: int) -> int:
        self.tick()
        self.integer(a)
        self.integer(b)
        if max(a.bit_length(), b.bit_length()) + 1 > MAX_INTERMEDIATE_BITS:
            raise ReferenceLimit("add_width")
        return a + b

    def mul(self, a: int, b: int) -> int:
        self.tick()
        self.integer(a)
        self.integer(b)
        if a.bit_length() + b.bit_length() > MAX_INTERMEDIATE_BITS:
            raise ReferenceLimit("multiply_width")
        return a * b

    def power(self, a: int, exponent: int) -> int:
        self.tick()
        self.integer(a)
        if type(exponent) is not int or not 0 <= exponent <= 1024:
            raise ReferenceLimit("power_exponent")
        if a.bit_length() * exponent > MAX_INTERMEDIATE_BITS:
            raise ReferenceLimit("power_width")
        # The checked nonnegative integer exponent keeps this power integral.
        return cast(int, a**exponent)

    def divide_exact(self, a: int, b: int) -> int:
        self.tick()
        self.integer(a)
        self.integer(b)
        if b <= 0:
            raise ReferenceLimit("division")
        quotient, remainder = divmod(a, b)
        if remainder:
            raise ReferenceLimit("inexact_integer_division")
        return quotient

    def gcd(self, a: int, b: int) -> int:
        self.tick()
        self.integer(a)
        self.integer(b)
        if self.gcd_calls >= MAX_GCD_CALLS:
            raise ReferenceLimit("gcd_count")
        self.gcd_calls += 1
        return math.gcd(a, b)

    def rational(self, numerator: int, denominator: int = 1) -> Fraction:
        if denominator <= 0:
            raise ReferenceLimit("denominator")
        divisor = self.gcd(numerator, denominator)
        n = self.divide_exact(numerator, divisor)
        d = self.divide_exact(denominator, divisor)
        if max(n.bit_length(), d.bit_length()) > MAX_REDUCED_BITS:
            raise ReferenceLimit("reduced_width")
        # Fraction performs one additional bounded normalization GCD internally.
        if self.gcd_calls >= MAX_GCD_CALLS:
            raise ReferenceLimit("gcd_count")
        self.gcd_calls += 1
        return Fraction(n, d)

    def check_rational(self, value: Fraction) -> None:
        if type(value) is not Fraction:
            raise ReferenceLimit("rational_type")
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_REDUCED_BITS:
            raise ReferenceLimit("rational_width")

    def qadd(self, a: Fraction, b: Fraction) -> Fraction:
        self.check_rational(a)
        self.check_rational(b)
        numerator = self.add(
            self.mul(a.numerator, b.denominator), self.mul(b.numerator, a.denominator)
        )
        return self.rational(numerator, self.mul(a.denominator, b.denominator))

    def qscale(self, a: Fraction, numerator: int, denominator: int = 1) -> Fraction:
        self.check_rational(a)
        return self.rational(self.mul(a.numerator, numerator), self.mul(a.denominator, denominator))

    def compare(self, a: Fraction, b: Fraction) -> int:
        self.check_rational(a)
        self.check_rational(b)
        left = self.mul(a.numerator, b.denominator)
        right = self.mul(b.numerator, a.denominator)
        return (left > right) - (left < right)

    def interval(self, lower: Fraction, upper: Fraction) -> Interval:
        if self.compare(lower, upper) > 0:
            raise ReferenceLimit("interval_order")
        return Interval(lower, upper)

    def iadd(self, a: Interval, b: Interval) -> Interval:
        return self.interval(self.qadd(a.lower, b.lower), self.qadd(a.upper, b.upper))

    def iscale(self, a: Interval, numerator: int, denominator: int = 1) -> Interval:
        low = self.qscale(a.lower, numerator, denominator)
        high = self.qscale(a.upper, numerator, denominator)
        return self.interval(low, high) if numerator >= 0 else self.interval(high, low)

    def isub(self, a: Interval, b: Interval) -> Interval:
        return self.iadd(a, self.iscale(b, -1))

    def point(self, value: Fraction) -> Interval:
        return self.interval(value, value)


def _ticks(value: tuple[int, int], *, positive: bool) -> None:
    if type(value) is not tuple or len(value) != 2:
        raise ReferenceLimit("endpoint_pair")
    if any(type(x) is not int or x.bit_length() > 7 or not -64 <= x <= 64 for x in value):
        raise ReferenceLimit("endpoint_domain")
    if value[0] > value[1] or (positive and value[0] == value[1]):
        raise ReferenceLimit("endpoint_order")


def _validate(vector: GaussianVector) -> None:
    if type(vector) is not GaussianVector:
        raise ReferenceLimit("vector_type")
    if type(vector.name) is not str or not 1 <= len(vector.name) <= 32:
        raise ReferenceLimit("name")
    if type(vector.scale) is not tuple or len(vector.scale) != 2:
        raise ReferenceLimit("scale_shape")
    if any(type(x) is not int or x.bit_length() > 2 for x in vector.scale):
        raise ReferenceLimit("scale_width")
    if vector.scale not in ((1, 2), (1, 1), (2, 1)):
        raise ReferenceLimit("positive_scale_family")
    if type(vector.mu) is not int or vector.mu not in (-1, 0, 1):
        raise ReferenceLimit("location_family")
    if type(vector.offset) is not int or vector.offset not in (-16, 0, 16):
        raise ReferenceLimit("offset_family")
    if vector.support is not None:
        _ticks(vector.support, positive=True)
    if type(vector.cells) is not tuple or len(vector.cells) > 4:
        raise ReferenceLimit("cell_count")
    for cell in vector.cells:
        _ticks(cell, positive=False)
    if type(vector.queries) is not tuple or len(vector.queries) > 4:
        raise ReferenceLimit("query_count")
    for point in vector.queries:
        if type(point) is not int or point.bit_length() > 7 or not -64 <= point <= 64:
            raise ReferenceLimit("query_domain")


def _clip(cell: tuple[int, int], support: tuple[int, int] | None) -> tuple[int, int]:
    if support is None:
        return cell
    return max(cell[0], support[0]), min(cell[1], support[1])


class _Reference:
    def __init__(self, arithmetic: _Arithmetic) -> None:
        self.a = arithmetic
        self.odd97 = self._lcm_odds(97)
        self.odd64 = self._lcm_odds(64)
        factorials = [1]
        for n in range(1, 97):
            factorials.append(arithmetic.mul(factorials[-1], n))
        self.denominator = arithmetic.mul(
            arithmetic.mul(arithmetic.power(2, 868), factorials[96]), self.odd97
        )
        coefficients = []
        for n in range(97):
            value = arithmetic.mul(
                arithmetic.power(2, 864 - 9 * n),
                arithmetic.divide_exact(factorials[96], factorials[n]),
            )
            value = arithmetic.mul(value, arithmetic.divide_exact(self.odd97, 2 * n + 1))
            coefficients.append(value if n % 2 == 0 else -value)
        self.coefficients = tuple(coefficients)
        self.log_two = self._series(1, 3)
        pi = arithmetic.isub(
            arithmetic.iscale(self._atan(5), 16), arithmetic.iscale(self._atan(239), 4)
        )
        two_pi = arithmetic.iscale(pi, 2)
        self.log_two_pi = arithmetic.interval(
            self._log(two_pi.lower).lower, self._log(two_pi.upper).upper
        )

    def _lcm_odds(self, count: int) -> int:
        value = 1
        for n in range(count):
            odd = 2 * n + 1
            value = self.a.mul(self.a.divide_exact(value, self.a.gcd(value, odd)), odd)
        return value

    def _polynomial(self, tick: int) -> int:
        square = self.a.mul(tick, tick)
        value = self.coefficients[-1]
        self.a.polynomial_visits += 1
        for coefficient in reversed(self.coefficients[:-1]):
            value = self.a.add(self.a.mul(value, square), coefficient)
            self.a.polynomial_visits += 1
        return self.a.mul(tick, value)

    def integral(self, left: int, right: int) -> Interval:
        if self.a.integrals >= 47 or not -64 <= left < right <= 64:
            raise ReferenceLimit("integral_domain_or_count")
        self.a.integrals += 1
        polynomial = self.a.rational(
            self.a.add(self._polynomial(right), -self._polynomial(left)), self.denominator
        )
        error = self.a.rational(right - left, self.a.power(2, 198))
        result = self.a.interval(
            self.a.qadd(polynomial, self.a.qscale(error, -1)), self.a.qadd(polynomial, error)
        )
        positive_floor = self.a.rational(right - left, self.a.power(2, 18))
        if self.a.compare(result.lower, positive_floor) <= 0:
            raise ReferenceLimit("integral_positive_bound")
        if (
            max(
                result.lower.numerator.bit_length(),
                result.lower.denominator.bit_length(),
                result.upper.numerator.bit_length(),
                result.upper.denominator.bit_length(),
            )
            > 4096
        ):
            raise ReferenceLimit("integral_width")
        return result

    def _series(self, numerator: int, denominator: int) -> Interval:
        # Homogeneous Horner polynomial avoids a Fraction/GCD at every term.
        if max(numerator.bit_length(), denominator.bit_length()) > 3740:
            raise ReferenceLimit("log_series_input_width")
        if numerator < 0 or denominator <= 0 or self.a.mul(3, numerator) > denominator:
            raise ReferenceLimit("log_series_domain")
        aa = self.a.mul(numerator, numerator)
        bb = self.a.mul(denominator, denominator)
        value = self.a.divide_exact(self.odd64, 127)
        denominator_power = bb
        for n in range(62, -1, -1):
            term = self.a.mul(self.a.divide_exact(self.odd64, 2 * n + 1), denominator_power)
            value = self.a.add(self.a.mul(value, aa), term)
            denominator_power = self.a.mul(denominator_power, bb)
        self.a.logarithm_terms += 64
        series = self.a.rational(
            self.a.mul(self.a.mul(2, numerator), value),
            self.a.mul(self.odd64, self.a.power(denominator, 127)),
        )
        remainder = self.a.rational(
            self.a.mul(2, self.a.power(numerator, 129)),
            self.a.mul(self.a.mul(129, self.a.power(denominator, 127)), self.a.add(bb, -aa)),
        )
        return self.a.interval(series, self.a.qadd(series, remainder))

    def _log(self, value: Fraction) -> Interval:
        if self.a.endpoint_logs >= 96:
            raise ReferenceLimit("log_count")
        self.a.endpoint_logs += 1
        self.a.check_rational(value)
        n, d = value.numerator, value.denominator
        if n <= 0 or max(n.bit_length(), d.bit_length()) > 4096:
            raise ReferenceLimit("log_input")
        # At most 22 exact comparisons; no unbounded range-reduction loop.
        exponent = -18
        for candidate in range(-18, 4):
            if candidate < 0:
                at_least = self.a.mul(n, self.a.power(2, -candidate)) >= d
            else:
                at_least = n >= self.a.mul(d, self.a.power(2, candidate))
            if at_least:
                exponent = candidate
        if exponent < 0:
            yn, yd = self.a.mul(n, self.a.power(2, -exponent)), d
        else:
            yn, yd = n, self.a.mul(d, self.a.power(2, exponent))
        if not yd <= yn < self.a.mul(2, yd):
            raise ReferenceLimit("log_range")
        local = self._series(self.a.add(yn, -yd), self.a.add(yn, yd))
        return self.a.iadd(self.a.iscale(self.log_two, exponent), local)

    def log_integral(self, interval: Interval) -> Interval:
        result = self.a.interval(self._log(interval.lower).lower, self._log(interval.upper).upper)
        self._width(result, 178)
        return result

    def _atan(self, denominator: int) -> Interval:
        square = self.a.mul(denominator, denominator)
        value = self.odd64
        for n in range(1, 64):
            coefficient = self.a.divide_exact(self.odd64, 2 * n + 1)
            value = self.a.add(
                self.a.mul(value, square), coefficient if n % 2 == 0 else -coefficient
            )
        self.a.machin_terms += 64
        lower = self.a.rational(value, self.a.mul(self.odd64, self.a.power(denominator, 127)))
        error = self.a.rational(1, self.a.mul(129, self.a.power(denominator, 129)))
        return self.a.interval(lower, self.a.qadd(lower, error))

    def _width(self, interval: Interval, exponent: int = 170) -> None:
        width = self.a.qadd(interval.upper, self.a.qscale(interval.lower, -1))
        if self.a.compare(width, self.a.rational(1, self.a.power(2, exponent))) >= 0:
            raise ReferenceLimit("reference_uncertainty")

    def case(self, vector: GaussianVector) -> GaussianReference:
        a = self.a
        if vector.support is None:
            support_integral = None
            log_i = a.iscale(self.log_two_pi, 1, 2)
            mode_tick = 0
        else:
            support_integral = self.integral(*vector.support)
            log_i = self.log_integral(support_integral)
            mode_tick = max(vector.support[0], min(0, vector.support[1]))
        scale_power = {(1, 2): -1, (1, 1): 0, (2, 1): 1}[vector.scale]
        log_r = a.iscale(self.log_two, scale_power)
        log_z = a.isub(log_i, log_r)
        self._width(log_z)
        cells = []
        for cell in vector.cells:
            left, right = _clip(cell, vector.support)
            if left >= right:
                cells.append(CellReference("exact_zero", None, None))
                continue
            integral = self.integral(left, right)
            mass = a.isub(self.log_integral(integral), log_i)
            self._width(mass)
            cells.append(CellReference("positive", integral, mass))
        densities: list[Interval | None] = []
        for tick in vector.queries:
            if vector.support is not None and not vector.support[0] <= tick <= vector.support[1]:
                densities.append(None)
                continue
            exponent = a.point(a.rational(-tick * tick, 512))
            density = a.isub(a.iadd(exponent, log_r), log_i)
            self._width(density)
            densities.append(density)
        rn, rd = vector.scale
        mode = a.qadd(a.rational(vector.mu), a.rational(mode_tick * rd, 16 * rn))
        variance = a.rational(rd * rd, rn * rn)
        return GaussianReference(
            vector, mode, variance, log_z, support_integral, tuple(cells), tuple(densities)
        )


def build_references(
    vectors: tuple[GaussianVector, ...], *, operation_limit: int = MAX_OPERATIONS
) -> ReferencePack:
    """Evaluate only the closed test domain; failure returns no partial pack."""
    if type(vectors) is not tuple or not 1 <= len(vectors) <= 8:
        raise ReferenceLimit("vector_count")
    integrals = 0
    names = set()
    for vector in vectors:
        _validate(vector)
        if vector.name in names:
            raise ReferenceLimit("duplicate_name")
        names.add(vector.name)
        integrals += vector.support is not None
        integrals += sum(
            left < right for left, right in (_clip(cell, vector.support) for cell in vector.cells)
        )
    if integrals > 47 or 2 * integrals + 2 > 96:
        raise ReferenceLimit("preflight_work")
    arithmetic = _Arithmetic(operation_limit)
    reference = _Reference(arithmetic)
    cases = tuple(reference.case(vector) for vector in vectors)
    return ReferencePack(
        cases,
        reference.log_two,
        arithmetic.operations,
        arithmetic.gcd_calls,
        arithmetic.integrals,
        arithmetic.endpoint_logs,
        arithmetic.polynomial_visits,
        arithmetic.logarithm_terms,
        arithmetic.machin_terms,
    )


def decimal_bounds(value: Interval) -> tuple[str, str]:
    """Directed diagnostic conversion only; exact rational assertions stay authoritative."""
    if type(value) is not Interval:
        raise ReferenceLimit("display_interval")
    endpoints = (value.lower, value.upper)
    for endpoint in endpoints:
        if type(endpoint) is not Fraction:
            raise ReferenceLimit("display_type")
        if (
            max(endpoint.numerator.bit_length(), endpoint.denominator.bit_length())
            > MAX_REDUCED_BITS
        ):
            raise ReferenceLimit("display_width")
        if abs(endpoint.numerator) >= 128 * endpoint.denominator:
            raise ReferenceLimit("display_magnitude")
    if value.lower > value.upper:
        raise ReferenceLimit("display_order")
    results = []
    for endpoint, rounding in zip(endpoints, (ROUND_FLOOR, ROUND_CEILING), strict=True):
        with localcontext() as context:
            context.prec = 96
            context.rounding = rounding
            result = Decimal(endpoint.numerator) / Decimal(endpoint.denominator)
            results.append(str(result))
    return results[0], results[1]
