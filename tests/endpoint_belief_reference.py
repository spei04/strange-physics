"""Finite independent test references; no production oscillator/integrator imports.

The named fixture domain and the 1e-60 combined truncation/rounding allowance
are derived in docs/NATIVE_ENDPOINT_BELIEFS.md. The 80-coefficient ODE tails
start at 4**40/80! and 4**40/81!; 100-digit recurrence/Horner rounding is
bounded separately. Machin64 and trig80 have their own remainder bounds.
This allowance is not a universal certificate for the binary64 predictor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, localcontext

PRECISION = 100
COEFFICIENTS = 80
REFERENCE_ERROR = Decimal("1e-60")
Key = tuple[float, float, float, float, float, float, float]


def binary(value: float) -> Decimal:
    return Decimal.from_float(value)


@dataclass
class EndpointOracle:
    values: dict[Key, Decimal] = field(default_factory=dict)
    series_values: int = 0
    lookups: int = 0
    exp_calls: int = 0
    log_calls: int = 0
    trig_calls: int = 0
    machin_terms: int = 0
    pi: Decimal | None = None

    def position(self, key: Key) -> Decimal:
        self.lookups += 1
        assert self.lookups <= 16_000
        with localcontext() as context:
            context.prec = PRECISION
            k, mass, anchor, initial, velocity, impulse, time = map(binary, key)
            speed = velocity + impulse / mass
            if initial == anchor and speed == 0:
                return anchor
            if key in self.values:
                return self.values[key]
            assert self.series_values < 1_728
            assert 0 <= k <= 4 and Decimal("0.5") <= mass <= 2 and 0 < time <= 2
            assert k * time * time / mass <= 4
            assert abs(initial - anchor) <= 1 and abs(speed * time) <= 1
            assert abs(anchor) <= 1 and abs(speed) <= 2
            # Independent x''=-(k/m)(x-a) coefficient recurrence, no sqrt/cos/sinc.
            coefficients = [initial - anchor, speed]
            for n in range(COEFFICIENTS - 2):
                coefficients.append(
                    -(k / mass) * coefficients[n] / Decimal((n + 2) * (n + 1))
                )
            value = coefficients[-1]
            for coefficient in reversed(coefficients[:-1]):
                value = value * time + coefficient
            value += anchor
            self.values[key] = value
            self.series_values += 1
            return value

    def exp(self, value: Decimal) -> Decimal:
        self.exp_calls += 1
        assert self.exp_calls <= 5_500
        with localcontext() as context:
            context.prec = PRECISION
            return value.exp()

    def log(self, value: Decimal) -> Decimal:
        self.log_calls += 1
        assert self.log_calls <= 5_600 and value > 0
        with localcontext() as context:
            context.prec = PRECISION
            return value.ln()

    def circle_constant(self) -> Decimal:
        if self.pi is not None:
            return self.pi
        with localcontext() as context:
            context.prec = PRECISION
            sums = []
            for denominator in (5, 239):
                x = Decimal(1) / denominator
                term = x
                total = Decimal(0)
                for n in range(64):
                    total += term / (2 * n + 1)
                    term *= -x * x
                    self.machin_terms += 1
                sums.append(total)
            self.pi = 16 * sums[0] - 4 * sums[1]
            return self.pi

    def trig(self, value: int, *, sine: bool) -> Decimal:
        self.trig_calls += 1
        assert self.trig_calls <= 4 and abs(value) <= 4
        with localcontext() as context:
            context.prec = PRECISION
            x = Decimal(value)
            term = x if sine else Decimal(1)
            total = term
            for n in range(1, 80):
                divisor = (2 * n) * (2 * n + 1) if sine else (2 * n - 1) * (2 * n)
                term *= -x * x / divisor
                total += term
            return total
