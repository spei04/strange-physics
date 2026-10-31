"""Synthetic adapter checks; every real physical/reference method is poisoned."""
from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_UP, Decimal, localcontext
from typing import NoReturn

import pytest
from endpoint_belief_reference import EndpointOracle
from test_calibration_fixture_contracts import public

import d1_prefix_evidence as a
import strange_physics.native_endpoint_beliefs as native_belief
import strange_physics.native_prediction as native_prediction
from strange_physics.contracts import Frame, Trajectory
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_prediction_contracts import NativePredictionOutcome
from strange_physics.native_spring_contracts import NativeWorkFacts
from strange_physics.research_contracts import PredictionResponse, message_sha256

D = Decimal


@pytest.fixture(autouse=True)
def poison_physics(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("No real D1 reference, simulator or native predictor in synthetic tests")
    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(native_prediction, "predict_native_spring", deny)
    monkeypatch.setattr(native_prediction, "_state_at_time", deny)
    monkeypatch.setattr(native_belief, "predict_native_spring", deny)
    monkeypatch.setattr(native_belief, "compute_native_endpoint_belief", deny)


def bound(case: a.CaseId = "M03", count: int = 256) -> a.BoundCandidates:
    value = public(case)
    training = value.observations.records[0].experiment
    particle = training.particles[0].model_copy(update={"position": (1.0, 0.0)})
    future = training.model_copy(update={"particles": (particle,)})
    pool = a.freeze_pool(count, value.observations.space.structure, training, future)
    actual = a.NativeCandidateInput(pool=pool.pool, config=pool.candidate_config,
                                    observations=value.observations)
    # Enumeration binds synthetic public metadata only; no physical forward occurs.
    result = produce_native_candidates(actual, attempt_id="candidate-a")
    return a.bind_candidates(case, pool, value, actual, result, attempt_id="candidate-a")


def fake_prediction(actual: a.NativePredictionInput, *, attempt_id: str) -> a.NativePredictionResult:
    q = actual.request.experiment.particles[0].position[0]
    # This constant synthetic surrogate deliberately ignores the spring coefficient.
    frames = tuple(Frame(time=t, positions=((q if t == 0 else q*0.75, 0.0),),
                         velocities=((0.0, 0.0),)) for t in actual.request.times)
    model_sha = message_sha256(actual.model)
    payload = NativePredictionOutcome(status="predicted", reason=None,
        actual_model_sha256=model_sha, requested_model_sha256=actual.request.model_sha256,
        request_sha256=message_sha256(actual.request), candidate_config_sha256=message_sha256(actual.candidate_config),
        prediction_config_sha256=message_sha256(actual.config), observation_sha256=actual.model.observation_sha256,
        requested_frame_count=2, computed_frame_count=2, returned_frame_count=2, failed_frame_index=None,
        response=PredictionResponse(model_sha256=model_sha, trajectory=Trajectory(frames=frames)))
    return a.NativePredictionResult(payload=payload, facts=NativeWorkFacts(
        attempt_id=attempt_id, operation="prediction", producer_version=actual.config.predictor_version,
        config_sha256=message_sha256(actual.config), input_sha256=message_sha256(actual),
        observation_sha256=actual.model.observation_sha256, model_sha256=model_sha,
        output_sha256=message_sha256(payload), unit="frame", requested_count=2,
        completed_count=2, failed_count=0, not_assessed_count=0, outcome="completed"))


class FakeOracle(EndpointOracle):
    """Counter/transport surrogate; its log/pi values are not numerical evidence."""
    def position(self, key: a.Key) -> Decimal:
        self.lookups += 1
        self.series_values += 1
        assert key not in self.values
        self.values[key] = D.from_float(key[3]*0.75)
        return self.values[key]

    def exp(self, value: Decimal) -> Decimal:
        self.exp_calls += 1
        return D(1)

    def log(self, value: Decimal) -> Decimal:
        self.log_calls += 1
        return D(0)

    def circle_constant(self) -> Decimal:
        self.machin_terms += 128
        return D("3.125")


def reference(monkeypatch: pytest.MonkeyPatch) -> a.D1Reference:
    monkeypatch.setattr(a, "EndpointOracle", FakeOracle)
    return a.D1Reference()


@pytest.mark.parametrize("count", [256, 1024])
def test_prefix_free_pool(count: int) -> None:
    b = bound(count=count)
    assert len(b.frozen.pool.coefficients) == count
    assert b.frozen.pool.coefficients[0] == 2/count
    assert b.frozen.pool.coefficients[-1] == 4-2/count
    assert "observations" not in b.frozen.model_fields
    assert a.rebind(b) == b


@pytest.mark.parametrize("field,value", [("count", 64), ("protocol_sha256", "0"*64),
                                         ("cells", ()), ("pool", a.NativeSpringPool(coefficients=(1.0,)))])
def test_freeze_mutation_is_rederived(field: str, value: object) -> None:
    b = bound()
    with pytest.raises(ValueError):
        a.rebind(replace(b, frozen=b.frozen.model_copy(update={field: value})))


@pytest.mark.parametrize("case", ["M01", "D03", "F02", "W03"])
def test_every_physical_prefix_shape(case: a.CaseId) -> None:
    b = bound(case)
    assert len(b.public.observations.records) == (2 if case == "D03" else 1)
    assert a.request_for(b, 0, future=True).request.times == (0.0, 0.75)
    assert a.request_for(b, 0).request.times == (0.0, 0.5)


def test_candidate_result_cannot_bind_another_run() -> None:
    b = bound()
    other = public("M03", "2")
    with pytest.raises(ValueError):
        a.bind_candidates("M03", b.frozen, other, b.actual, b.result, attempt_id=b.attempt_id)


@pytest.mark.parametrize("node,record", [(-1, 0), (256, 0), (0, 1), (True, 0)])
def test_request_slot_rejected(node: int, record: int) -> None:
    with pytest.raises(ValueError):
        a.request_for(bound(), node, record=record)


def test_prediction_full_request_and_attempt_join() -> None:
    actual = a.request_for(bound(), 0)
    result = fake_prediction(actual, attempt_id="a")
    assert a.bind_prediction(actual, result, attempt_id="a").endpoint() == 0.75
    with pytest.raises(ValueError):
        a.bind_prediction(actual, result, attempt_id="other")
    altered = actual.model_copy(update={"model": actual.model.model_copy(update={"linear": 2.0})})
    with pytest.raises(ValueError):
        a.bind_prediction(altered, result, attempt_id="a")


def test_cache_stages_reference_and_consumes_once(monkeypatch: pytest.MonkeyPatch) -> None:
    b = bound("D03")
    cache = a.FirstRecordCache(b, "first")
    assert len(cache.precompute(fake_prediction)) == 256
    refs = reference(monkeypatch)
    prior = cache.seal_prior(refs)
    assert prior.source == "prior"
    assert prior.finite_mean == a.point(D("0.75"))
    for i in range(256):
        cache.consume(i, 0, 0.25, a.request_for(b, i), "first")
        # The prefix consumes the same logical reference, with no second lookup.
        refs.take_training("D03", 256, 0.25, i, 0)
    cache.require_complete()
    assert refs.census()["lookups"] == 256
    assert refs.census()["logical_completed"] == 256
    with pytest.raises(ValueError):
        cache.consume(0, 0, 0.25, a.request_for(b, 0), "first")


@pytest.mark.parametrize("fault", ["record", "scale", "attempt", "unsealed"])
def test_cache_rejects_wrong_slot_without_forward(fault: str) -> None:
    b = bound("D03")
    cache = a.FirstRecordCache(b, "first")
    with pytest.raises(ValueError):
        cache.consume(0, 1 if fault == "record" else 0, 0.5 if fault == "scale" else 0.25,
                      a.request_for(b, 0), "other" if fault == "attempt" else "first")
    assert cache.failed and cache.attempted == 0


def test_precompute_failure_cannot_retry() -> None:
    cache = a.FirstRecordCache(bound(), "first")
    def fail(actual: a.NativePredictionInput, *, attempt_id: str) -> a.NativePredictionResult:
        raise RuntimeError("injected")
    with pytest.raises(RuntimeError):
        cache.precompute(fail)
    assert cache.attempted == 1 and not cache.rows and cache.failed
    with pytest.raises(ValueError):
        cache.precompute(fake_prediction)


def test_reference_full_endpoint_census_bypasses_legacy_lookups(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    for case in a.CASE_IDS:
        for count in a.COUNTS:
            for scale in a.profile_scales(case):
                for node in range(count):
                    for record in range(2 if case == "D03" else 1):
                        refs.take_training(case, count, scale, node, record)
            for node in range(count):
                refs.future(case, count, node)
    census = refs.census()
    assert census["logical_completed"] == 37120
    assert census["cache_hits"] == 33280
    assert census["lookups"] == census["series_values"] == 3840
    assert census["training_consumed"] == 26880
    assert all(x.lookups == 1280 for x in refs.channels.values())
    with pytest.raises(ValueError):
        refs.require_complete()  # Normalization work has deliberately not occurred.


def test_reference_first_fault_blocks_new_slots(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    def fail(key: a.Key) -> Decimal:
        raise RuntimeError("injected reference failure")
    monkeypatch.setattr(refs.channels["strong"], "position", fail)
    with pytest.raises(RuntimeError):
        refs.training("M01", 256, 0.125, 0, 0)
    assert refs.calls[0].status == "failed"
    with pytest.raises(ValueError):
        refs.training("M01", 256, 0.125, 1, 0)
    assert refs.census()["logical_attempted"] == 1


def test_reference_duplicate_logical_slot_is_not_another_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    refs.take_training("D03", 256, 0.25, 0, 0)
    refs.take_training("D03", 256, 0.25, 0, 1)
    assert refs.census()["lookups"] == 1
    assert refs.census()["cache_hits"] == 1
    with pytest.raises(ValueError):
        refs.take_training("D03", 256, 0.25, 0, 1)


@pytest.mark.parametrize("bad", [D("NaN"), D("Infinity"), D("1.23456789"+"1"*100)])
def test_transcendental_center_shape(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        a.rounded_decimal(bad)


def test_positive_log_perturbation_encloses_rational_argument() -> None:
    result = a.log_perturbation(D(1), a.Interval(D("0.99"), D("1.01")), D(0))
    assert result.enclosure.lower < D("-0.01")
    assert result.enclosure.upper > D("0.01")
    with pytest.raises(ValueError):
        a.log_perturbation(D(1), a.Interval(D(0), D(1)), D(0))


def test_reference_constants_and_normalization_counts_are_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    constants = refs.constants()
    assert refs.constants() is constants
    assert refs.census()["log_calls"] == 6
    assert refs.census()["machin_terms"] == 128
    joint = tuple(a.ReferenceValue(D(0), a.point(0)) for _ in range(256))
    result = refs.normalize("M01", 256, 0.125, joint)
    assert result.probabilities[0].lower <= D(1)/256 <= result.probabilities[0].upper
    assert refs.census()["exp_calls"] == 256 and refs.census()["log_calls"] == 7
    with pytest.raises(ValueError):
        refs.normalize("M01", 256, 0.125, joint)


def test_wider_reference_does_not_enlarge_frozen_allowance(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    joint = tuple(a.ReferenceValue(D(0), a.around(D(0), D("1e-40"))) for _ in range(256))
    with pytest.raises(ValueError, match="reference envelope"):
        refs.normalize("M01", 256, 0.125, joint)
    assert refs.failed and refs.normalizations_completed == 0
    assert refs.census()["exp_calls"] == 256


def test_training_bound_uses_half_time_and_ignores_ambient_context() -> None:
    frozen = bound("W03").frozen
    endpoints = (0.09375,)*256
    expected = a.training_forecast(frozen, endpoints, D("1e-60"), source="prior")
    with localcontext() as c:
        c.prec = 3
        c.rounding = ROUND_UP
        actual = a.training_forecast(frozen, endpoints, D("1e-60"), source="prior")
    assert actual == expected
    assert actual.continuous_mean.lower < D("0.09375") < actual.continuous_mean.upper
    assert a.innovation(actual, 0.09375).lower < 0 < a.innovation(actual, 0.09375).upper


@pytest.mark.parametrize("residual", [D("1e-110"), D("-1e-110")])
def test_forecast_rejects_infeasible_mass_even_below_working_precision(residual: Decimal) -> None:
    frozen = bound().frozen
    with localcontext() as c:
        c.prec = 200
        first = D(1)/256+residual
    masses = (a.point(first),)+(a.point(1.0/256),)*255
    with pytest.raises(ValueError, match="infeasible"):
        a.training_forecast(frozen, (0.75,)*256, D(0), source="matched-base-posterior", masses=masses)
