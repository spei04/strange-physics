"""Conditional repeated-loss algebra; no material authentication or qualification.

The later binder must reconstruct both profiles and their inclusive error bounds
from actual source-bound material. This kernel does not perform those joins, run
any physical/transcendental calculation, or approve a report.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Literal

from grid_q1_bounds import Interval
from grid_q1_evidence import divide, minus, plus, point, square, times, total

D = Decimal
ZERO, ONE, FOUR = D(0), D(1), D(4)
type Relation = Literal["contained", "disjoint", "overlap"]


@dataclass(frozen=True)
class RepeatedLossNode:
    index: int
    one_emitted: float
    two_probability: Interval
    prior_mass: Fraction


@dataclass(frozen=True)
class RepeatedLossInput:
    count: int
    nodes: tuple[RepeatedLossNode, ...]
    one_log_ratio_upper: Decimal
    two_log_ratio_upper: Decimal


@dataclass(frozen=True)
class RepeatedLossNodeBound:
    index: int
    transformed_probability: Interval
    observed_ratio: Interval
    relation: Relation


@dataclass(frozen=True)
class RepeatedLossWitness:
    """A conditional comparison, never a passed report or authenticated record.

    All inputs and per-node results remain available even when a node is
    disjoint. Missing/malformed inputs raise ValueError rather than inventing a
    numerical failure. The binder owns unavailable/failed/unrun report states.
    """

    inputs: RepeatedLossInput
    gamma: Interval
    allowance: Interval
    squared_sum: Interval
    nodes: tuple[RepeatedLossNodeBound, ...]
    disposition: Relation
    disjoint_indices: tuple[int, ...]
    overlap_indices: tuple[int, ...]

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"

    @property
    def qualification(self) -> Literal["unavailable"]:
        return "unavailable"


def _bound(value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError("Exact finite Decimal error bound required")
    Interval(value, value)
    if not ZERO <= value <= ONE:
        raise ValueError("Nonnegative log-ratio error bound at most one required")


def _validate(inputs: RepeatedLossInput) -> tuple[Interval, ...]:
    if type(inputs) is not RepeatedLossInput:
        raise ValueError("Exact repeated-loss input required")
    if type(inputs.count) is not int or not 1 <= inputs.count <= 1024:
        raise ValueError("Bounded complete node count required")
    if type(inputs.nodes) is not tuple or len(inputs.nodes) != inputs.count:
        raise ValueError("Every declared node is required; no surviving subset")
    _bound(inputs.one_log_ratio_upper)
    _bound(inputs.two_log_ratio_upper)
    uniform = Fraction(1, inputs.count)
    exact: list[Interval] = []
    lower_sum = upper_sum = Fraction(0)
    for index, node in enumerate(inputs.nodes):
        if type(node) is not RepeatedLossNode or type(node.index) is not int or node.index != index:
            raise ValueError("Exact unique coefficient-ordered nodes required")
        if type(node.prior_mass) is not Fraction or node.prior_mass != uniform:
            raise ValueError("Exact uniform normalized prior required for square simplification")
        if type(node.one_emitted) is not float:
            raise ValueError("Exact positive finite binary64 emitted value required")
        emitted = point(node.one_emitted)
        if emitted.lower <= ZERO:
            raise ValueError("Every emitted value must be strictly positive")
        mass = node.two_probability
        if type(mass) is not Interval:
            raise ValueError("Directed two-record probability interval required")
        # Recheck raw fields even when a frozen dataclass was bypassed/mutated.
        if type(mass.lower) is not Decimal or type(mass.upper) is not Decimal:
            raise ValueError("Exact Decimal probability endpoints required")
        Interval(mass.lower, mass.upper)
        if not ZERO < mass.lower <= mass.upper <= ONE:
            raise ValueError("Strictly positive probability intervals within [0,1] required")
        # Exact feasibility prevents sub-precision residuals from being hidden
        # by the subsequent 100-digit directed interval arithmetic.
        lower_sum += Fraction(mass.lower)
        upper_sum += Fraction(mass.upper)
        exact.append(emitted)
    if not lower_sum <= 1 <= upper_sum:
        raise ValueError("Probability intervals must admit one normalized vector")
    return tuple(exact)


def repeated_loss_witness(inputs: RepeatedLossInput) -> RepeatedLossWitness:
    """Enclose r_i / (E_i^2 / sum(E^2)) with gamma = 4*c_M + c_D.

    This bounded kernel admits small synthetic counts. The eventual D1 binder
    must additionally restrict the actual rows to M03/D03, N=256/1024, base scale,
    exact shared physical records/prior, verified reference execution and all
    existing profile gates. Supplied error bounds here are conditional premises,
    not a substitute for those obligations or a new tolerance.
    """
    emitted = _validate(inputs)
    gamma = plus(
        times(point(FOUR), point(inputs.one_log_ratio_upper)),
        point(inputs.two_log_ratio_upper),
    )
    if not ZERO <= gamma.lower <= gamma.upper < ONE:
        raise ValueError("Outward gamma must stay in [0,1)")
    gap = minus(point(ONE), point(gamma.upper))
    allowance = Interval(gap.lower, divide(point(ONE), gap).upper)
    squares = tuple(square(value) for value in emitted)
    squared_sum = total(squares)
    if squared_sum.lower <= ZERO:
        raise ValueError("Strictly positive enclosed square sum required")
    nodes: list[RepeatedLossNodeBound] = []
    disjoint: list[int] = []
    overlap: list[int] = []
    for node, squared in zip(inputs.nodes, squares, strict=True):
        transformed = divide(squared, squared_sum)
        if transformed.lower <= ZERO:
            raise ValueError("Strictly positive transformed probability required")
        ratio = divide(node.two_probability, transformed)
        relation: Relation
        if allowance.lower <= ratio.lower and ratio.upper <= allowance.upper:
            relation = "contained"
        elif ratio.upper < allowance.lower or ratio.lower > allowance.upper:
            relation = "disjoint"
            disjoint.append(node.index)
        else:
            relation = "overlap"
            overlap.append(node.index)
        nodes.append(RepeatedLossNodeBound(node.index, transformed, ratio, relation))
    disposition: Relation = "disjoint" if disjoint else "overlap" if overlap else "contained"
    return RepeatedLossWitness(
        inputs,
        gamma,
        allowance,
        squared_sum,
        tuple(nodes),
        disposition,
        tuple(disjoint),
        tuple(overlap),
    )
