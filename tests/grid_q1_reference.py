"""Finite GRID-Q1 reference allocation; the accepted legacy oracle is unchanged.

No entrypoint runs this module. Six named, single-lifetime oracle instances
partition one declared manifest; none is reset, replaced or created on demand.
This is source preparation, not an admitted or accepted calibration.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, localcontext

from endpoint_belief_reference import PRECISION, EndpointOracle
from grid_q1_inputs import COUNTS, HISTORIES, SCALES, History, coefficient, query

EXPECTED = {
    "training_requests": 12096,
    "future_requests": 4032,
    "label_requests": 1,
    "normalizations": 27,
    "lookups": 16129,
    "series_values": 2689,
    "exp_calls": 12096,
    "log_calls": 34,
    "trig_calls": 4,
    "machin_terms": 128,
}


def allowed_weight(value: Decimal) -> bool:
    if not isinstance(value, Decimal) or not value.is_finite():
        return False
    parts = value.as_tuple()
    return (
        len(parts.digits) <= 120
        and isinstance(parts.exponent, int)
        and -256 <= parts.exponent <= 128
        and Decimal(-32) <= value <= Decimal(4)
    )


@dataclass(frozen=True)
class Constants:
    gaussian: tuple[Decimal, ...]
    log_prior: tuple[Decimal, ...]


@dataclass(frozen=True)
class FiniteReference:
    maximum_log_weight: Decimal
    shifted_log_evidence: Decimal
    normalized_logs: tuple[Decimal, ...]
    probabilities: tuple[Decimal, ...]


class GridQ1Reference:
    """One manifest, with exact input-key caches and no implicit retries.

    Training: <=12,097 lookups / 1,345 series including the interior label.
    Future: <=4,032 lookups / 1,344 series, shared physically across histories.
    Each of three arithmetic channels: 4,032 exp / nine log calls.
    Constants: seven log calls, four trig calls and 128 Machin terms.
    Each named instance independently remains within the old oracle's limits.
    """

    def __init__(self) -> None:
        self._training = EndpointOracle()
        self._future = EndpointOracle()
        self._arithmetic = {history: EndpointOracle() for history in HISTORIES}
        self._constants = EndpointOracle()
        self._training_seen: set[tuple[History, int, float, int]] = set()
        self._future_seen: set[tuple[History, int, int]] = set()
        self._normalization_seen: set[tuple[History, int, float]] = set()
        self._normalization_complete: set[tuple[History, int, float]] = set()
        self._label_started = False
        self._constants_started = False
        self._constant_values: Constants | None = None
        self._moments_started = False
        self._moments: tuple[Decimal, Decimal] | None = None
        self._failed = False

    @contextmanager
    def _work(self) -> Iterator[None]:
        if self._failed:
            raise ValueError("A reference calculation already failed; no continuation")
        try:
            yield
        except BaseException:
            self._failed = True
            raise

    def interior_label(self) -> Decimal:
        if self._label_started:
            raise ValueError("Interior construction label was already attempted")
        self._label_started = True
        with self._work():
            return self._training.position((1.5, 1.0, 0.0, 1.0, 0.0, 0.0, 0.5))

    def training(self, history: History, count: int, scale: float, index: int) -> Decimal:
        query(history, count, scale, index)
        key = (history, count, scale, index)
        if key in self._training_seen:
            raise ValueError("Training reference query was already attempted")
        self._training_seen.add(key)
        with self._work():
            return self._training.position(
                (
                    coefficient(count, index),
                    1.0,
                    0.0,
                    0.0 if history == "flat" else 1.0,
                    0.0,
                    0.0,
                    0.5,
                )
            )

    def future(self, history: History, count: int, index: int) -> Decimal:
        query(history, count, SCALES[0], index)
        key = (history, count, index)
        if key in self._future_seen:
            raise ValueError("Future reference query was already attempted")
        self._future_seen.add(key)
        with self._work():
            return self._future.position((coefficient(count, index), 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))

    def constants(self) -> Constants:
        if self._constant_values is not None:
            return self._constant_values
        if self._constants_started:
            raise ValueError("Constant construction previously failed")
        self._constants_started = True
        with self._work(), localcontext() as context:
            context.prec = PRECISION
            log_two_pi = self._constants.log(2 * self._constants.circle_constant())
            gaussian = tuple(
                -self._constants.log(Decimal.from_float(scale)) - log_two_pi / 2 for scale in SCALES
            )
            log_prior = tuple(self._constants.log(Decimal(1) / count) for count in COUNTS)
        self._constant_values = Constants(gaussian, log_prior)
        return self._constant_values

    def normalize(
        self, history: History, count: int, scale: float, log_weights: tuple[Decimal, ...]
    ) -> FiniteReference:
        """Independent unshifted positive sum, not the production max-shift algorithm.

        Caller supplies independently formed joint log weights. No conversion
        to binary64 precedes the comparisons in the future qualification driver.
        """
        query(history, count, scale, 0)
        key = (history, count, scale)
        if key in self._normalization_seen:
            raise ValueError("Finite reference normalization was already attempted")
        if len(log_weights) != count or any(not allowed_weight(value) for value in log_weights):
            raise ValueError("Every declared node requires one finite Decimal log weight")
        self._normalization_seen.add(key)
        oracle = self._arithmetic[history]
        with self._work(), localcontext() as context:
            context.prec = PRECISION
            weights = tuple(oracle.exp(value) for value in log_weights)
            if any(not weight.is_finite() or weight <= 0 for weight in weights):
                raise ValueError("Direct finite reference lost a positive term")
            total = sum(weights, Decimal(0))
            log_evidence = oracle.log(total)
            maximum = max(log_weights)
            result = FiniteReference(
                maximum,
                log_evidence - maximum,
                tuple(value - log_evidence for value in log_weights),
                tuple(weight / total for weight in weights),
            )
            if any(
                not value.is_finite()
                for value in (
                    result.maximum_log_weight,
                    result.shifted_log_evidence,
                    *result.normalized_logs,
                    *result.probabilities,
                )
            ):
                raise ValueError("Finite reference normalization was nonfinite")
        self._normalization_complete.add(key)
        return result

    def flat_continuous_moments(self) -> tuple[Decimal, Decimal]:
        if self._moments is not None:
            return self._moments
        if self._moments_started:
            raise ValueError("Continuous moment reference previously failed")
        self._moments_started = True
        with self._work(), localcontext() as context:
            context.prec = PRECISION
            sin_two = self._constants.trig(2, sine=True)
            cos_two = self._constants.trig(2, sine=False)
            sin_four = self._constants.trig(4, sine=True)
            cos_four = self._constants.trig(4, sine=False)
            self._moments = (
                sin_two + (cos_two - 1) / 2,
                Decimal(1) / 2 + sin_four / 4 + (cos_four - 1) / 16,
            )
        return self._moments

    def census(self) -> dict[str, int]:
        oracles = (self._training, self._future, self._constants, *self._arithmetic.values())
        return {
            "training_requests": len(self._training_seen),
            "future_requests": len(self._future_seen),
            "label_requests": int(self._label_started),
            "normalizations": len(self._normalization_complete),
            "lookups": sum(oracle.lookups for oracle in oracles),
            "series_values": sum(oracle.series_values for oracle in oracles),
            "exp_calls": sum(oracle.exp_calls for oracle in oracles),
            "log_calls": sum(oracle.log_calls for oracle in oracles),
            "trig_calls": sum(oracle.trig_calls for oracle in oracles),
            "machin_terms": sum(oracle.machin_terms for oracle in oracles),
        }

    def require_complete(self) -> None:
        if (
            self._failed
            or self.census() != EXPECTED
            or len(self._normalization_seen) != 27
            or self._constant_values is None
            or self._moments is None
        ):
            raise ValueError("GRID-Q1 reference manifest is incomplete or differs from its census")
