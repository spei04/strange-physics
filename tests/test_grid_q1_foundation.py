"""Synthetic GRID-Q1 foundation checks; real reference operations are poisoned."""

from __future__ import annotations

from decimal import Decimal
from typing import NoReturn

import pytest
from endpoint_belief_reference import EndpointOracle, Key
from grid_q1_inputs import candidate_input, coefficient, fixtures, profile
from grid_q1_reference import GridQ1Reference

from strange_physics.research_contracts import message_sha256


@pytest.fixture(autouse=True)
def no_reference_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("A synthetic foundation test attempted reference computation")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)


@pytest.mark.parametrize("count", (64, 256, 1024))
def test_pool_cells_and_prior_are_the_declared_partition(count: int) -> None:
    fixture = fixtures(0.8)[0]
    actual = candidate_input(fixture, count)
    declared = profile(count, 0.25)
    assert len(actual.pool.coefficients) == len(declared.cells) == count
    assert declared.cells[0].left == 0.0
    assert declared.cells[-1].right == 4.0
    assert all(a.right == b.left for a, b in zip(declared.cells, declared.cells[1:], strict=False))
    assert all(
        cell.left < node < cell.right
        and node == (cell.left + cell.right) / 2
        and (cell.right - cell.left) / 4 == 1 / count
        for cell, node in zip(declared.cells, actual.pool.coefficients, strict=True)
    )
    assert declared.reference_measure == "physical-k-lebesgue.v1"
    assert declared.prior == "uniform-support-density.v1"


@pytest.mark.parametrize("count", (0, 65, 1025, True))
def test_undeclared_grid_is_rejected_before_allocation(count: int) -> None:
    with pytest.raises(ValueError, match="fixed GRID-Q1"):
        coefficient(count, 0)


def test_complete_synthetic_records_and_external_identity() -> None:
    rows = fixtures(0.8)
    assert [row.label for row in rows] == ["flat", "boundary", "interior"]
    assert len({row.space_sha256 for row in rows}) == 1
    assert len({row.observations.run_id for row in rows}) == 3
    assert len({message_sha256(row.observations) for row in rows}) == 3
    for row in rows:
        observations = row.observations
        assert observations.space.sampling.sample_interval == 0.5
        assert observations.space.calibration_experiments == 0
        assert observations.space.budget == 1
        assert row.terminal_velocity_semantics == "unused-zero-placeholder"
        assert len(observations.records) == 1
        record = observations.records[0]
        assert record.index == 0 and record.status == "completed" and record.error is None
        assert record.trajectory is not None
        assert tuple(frame.time for frame in record.trajectory.frames) == (0.0, 0.5)
        assert all(frame.velocities == ((0.0, 0.0),) for frame in record.trajectory.frames)


@pytest.mark.parametrize("label", (float("nan"), float("inf"), 0.4, 1.1))
def test_invalid_construction_label_is_rejected(label: float) -> None:
    with pytest.raises(ValueError, match="explicit bounded binary64"):
        fixtures(label)


def test_training_and_future_use_fixed_distinct_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[EndpointOracle, Key]] = []

    def position(oracle: EndpointOracle, key: Key) -> Decimal:
        calls.append((oracle, key))
        oracle.lookups += 1
        return Decimal(0)

    monkeypatch.setattr(EndpointOracle, "position", position)
    reference = GridQ1Reference()
    reference.interior_label()
    reference.training("boundary", 64, 0.125, 0)
    reference.training("interior", 64, 0.25, 0)
    reference.future("flat", 64, 0)
    reference.future("boundary", 64, 0)
    assert calls[0][0] is calls[1][0] is calls[2][0]
    assert calls[3][0] is calls[4][0] and calls[3][0] is not calls[0][0]
    assert calls[1][1] == calls[2][1]
    assert calls[3][1] == calls[4][1]
    assert calls[1][1][-1] == 0.5 and calls[3][1][-1] == 1.0
    assert reference.census()["lookups"] == 5
    with pytest.raises(ValueError, match="already attempted"):
        reference.training("boundary", 64, 0.125, 0)
    with pytest.raises(ValueError, match="already attempted"):
        reference.interior_label()
    assert len(calls) == 5


def test_reference_failure_prevents_continuation(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(oracle: EndpointOracle, key: Key) -> Decimal:
        raise ArithmeticError("original reference failure")

    monkeypatch.setattr(EndpointOracle, "position", broken)
    reference = GridQ1Reference()
    with pytest.raises(ArithmeticError, match="original reference failure"):
        reference.training("boundary", 64, 0.125, 0)
    with pytest.raises(ValueError, match="already failed"):
        reference.future("boundary", 64, 0)
    with pytest.raises(ValueError, match="incomplete"):
        reference.require_complete()


def test_normalization_uses_one_direct_sum_and_retains_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Decimal]] = []

    def exp(oracle: EndpointOracle, value: Decimal) -> Decimal:
        oracle.exp_calls += 1
        calls.append(("exp", value))
        return Decimal(1)

    def log(oracle: EndpointOracle, value: Decimal) -> Decimal:
        oracle.log_calls += 1
        calls.append(("log", value))
        return Decimal(0)

    monkeypatch.setattr(EndpointOracle, "exp", exp)
    monkeypatch.setattr(EndpointOracle, "log", log)
    reference = GridQ1Reference()
    values = (Decimal(-1),) * 64
    result = reference.normalize("flat", 64, 0.125, values)
    assert calls == [("exp", Decimal(-1))] * 64 + [("log", Decimal(64))]
    assert result.maximum_log_weight == -1
    assert result.shifted_log_evidence == 1
    assert result.normalized_logs == values
    assert result.probabilities == (Decimal(1) / 64,) * 64
    assert reference.census()["normalizations"] == 1
    with pytest.raises(ValueError, match="already attempted"):
        reference.normalize("flat", 64, 0.125, values)
    assert len(calls) == 65


@pytest.mark.parametrize(
    "invalid",
    (Decimal("NaN"), Decimal("Infinity"), Decimal(-33), Decimal(5), Decimal("1e-257")),
)
def test_invalid_reference_weights_precede_exp(invalid: Decimal) -> None:
    reference = GridQ1Reference()
    with pytest.raises(ValueError, match="finite Decimal"):
        reference.normalize("flat", 64, 0.125, (invalid,) * 64)
    assert reference.census()["exp_calls"] == 0


def test_partial_vector_precedes_exp() -> None:
    reference = GridQ1Reference()
    with pytest.raises(ValueError, match="finite Decimal"):
        reference.normalize("flat", 64, 0.125, (Decimal(-1),) * 63)
    assert reference.census()["normalizations"] == 0


def test_empty_reference_cannot_claim_completion() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        GridQ1Reference().require_complete()


def test_constants_and_moments_are_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def circle(oracle: EndpointOracle) -> Decimal:
        calls.append("circle")
        oracle.machin_terms += 128
        return Decimal(3)

    def log(oracle: EndpointOracle, value: Decimal) -> Decimal:
        calls.append("log")
        oracle.log_calls += 1
        return Decimal(0)

    def trig(oracle: EndpointOracle, value: int, *, sine: bool) -> Decimal:
        calls.append("trig")
        oracle.trig_calls += 1
        return Decimal(0)

    monkeypatch.setattr(EndpointOracle, "circle_constant", circle)
    monkeypatch.setattr(EndpointOracle, "log", log)
    monkeypatch.setattr(EndpointOracle, "trig", trig)
    reference = GridQ1Reference()
    constants = reference.constants()
    moments = reference.flat_continuous_moments()
    assert reference.constants() is constants
    assert reference.flat_continuous_moments() is moments
    assert calls == ["circle"] + ["log"] * 7 + ["trig"] * 4
    assert reference.census()["log_calls"] == 7
    assert reference.census()["machin_terms"] == 128


def test_partial_reference_failure_keeps_cost_and_cannot_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exp(oracle: EndpointOracle, value: Decimal) -> Decimal:
        oracle.exp_calls += 1
        if oracle.exp_calls == 3:
            raise ArithmeticError("third exponential failed")
        return Decimal(1)

    monkeypatch.setattr(EndpointOracle, "exp", exp)
    reference = GridQ1Reference()
    values = (Decimal(-1),) * 64
    with pytest.raises(ArithmeticError, match="third exponential failed"):
        reference.normalize("flat", 64, 0.125, values)
    assert reference.census()["exp_calls"] == 3
    assert reference.census()["normalizations"] == 0
    with pytest.raises(ValueError, match="already failed"):
        reference.normalize("boundary", 64, 0.125, values)
    assert reference.census()["exp_calls"] == 3
