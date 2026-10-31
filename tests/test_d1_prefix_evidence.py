"""Synthetic adapter checks; every real physical/reference method is poisoned."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_UP, Decimal, localcontext
from typing import NoReturn

import d1_prefix_evidence as a
import pytest
from d1_bounds import D1Certificate, certify_d1_prefix
from d1_fixture_reference import FixtureBatch
from endpoint_belief_reference import EndpointOracle, Key
from grid_q1_bounds import ArithmeticEvidence, Interval
from grid_q1_evidence import absolute_upper, around, minus, point, probabilities
from test_calibration_fixture_contracts import public

import strange_physics.native_endpoint_beliefs as native_belief
import strange_physics.native_prediction as native_prediction
from strange_physics.calibration_fixture_contracts import CASE_IDS, CaseId, candidate_material
from strange_physics.contracts import Frame, ObservationBundle, Trajectory
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_endpoint_belief_contracts import (
    EndpointBeliefProfile,
    NativeEndpointBeliefInput,
    NativeEndpointBeliefResult,
    parse_native_endpoint_belief_input,
    parse_native_endpoint_belief_result,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    NativePredictionOutcome,
    NativePredictionResult,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeSpringPool,
    NativeWorkFacts,
)
from strange_physics.research_contracts import PredictionResponse, message_sha256

D = Decimal


@pytest.fixture(autouse=True)
def poison_physics(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError(
            "No real D1 reference, simulator or native predictor in synthetic tests"
        )

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(native_prediction, "predict_native_spring", deny)
    monkeypatch.setattr(native_prediction, "_state_at_time", deny)
    monkeypatch.setattr(native_belief, "predict_native_spring", deny)
    monkeypatch.setattr(native_belief, "compute_native_endpoint_belief", deny)


def bound(case: CaseId = "M03", count: int = 256, token: str = "1") -> a.BoundCandidates:
    value = public(case, token)
    training = value.observations.records[0].experiment
    particle = training.particles[0].model_copy(update={"position": (1.0, 0.0)})
    future = training.model_copy(update={"particles": (particle,)})
    pool = a.freeze_pool(count, value.observations.space.structure, training, future)
    actual = NativeCandidateInput(
        pool=pool.pool, config=pool.candidate_config, observations=value.observations
    )
    # Enumeration binds synthetic public metadata only; no physical forward occurs.
    result = produce_native_candidates(actual, attempt_id="candidate-a")
    return a.bind_candidates(case, pool, value, actual, result, attempt_id="candidate-a")


def fake_prediction(actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
    q = actual.request.experiment.particles[0].position[0]
    # This constant synthetic surrogate deliberately ignores the spring coefficient.
    frames = tuple(
        Frame(time=t, positions=((q if t == 0 else q * 0.75, 0.0),), velocities=((0.0, 0.0),))
        for t in actual.request.times
    )
    model_sha = message_sha256(actual.model)
    payload = NativePredictionOutcome(
        status="predicted",
        reason=None,
        actual_model_sha256=model_sha,
        requested_model_sha256=actual.request.model_sha256,
        request_sha256=message_sha256(actual.request),
        candidate_config_sha256=message_sha256(actual.candidate_config),
        prediction_config_sha256=message_sha256(actual.config),
        observation_sha256=actual.model.observation_sha256,
        requested_frame_count=2,
        computed_frame_count=2,
        returned_frame_count=2,
        failed_frame_index=None,
        response=PredictionResponse(model_sha256=model_sha, trajectory=Trajectory(frames=frames)),
    )
    return NativePredictionResult(
        payload=payload,
        facts=NativeWorkFacts(
            attempt_id=attempt_id,
            operation="prediction",
            producer_version=actual.config.predictor_version,
            config_sha256=message_sha256(actual.config),
            input_sha256=message_sha256(actual),
            observation_sha256=actual.model.observation_sha256,
            model_sha256=model_sha,
            output_sha256=message_sha256(payload),
            unit="frame",
            requested_count=2,
            completed_count=2,
            failed_count=0,
            not_assessed_count=0,
            outcome="completed",
        ),
    )


class FakeOracle(EndpointOracle):
    """Counter/transport surrogate; its log/pi values are not numerical evidence."""

    def position(self, key: Key) -> Decimal:
        self.lookups += 1
        self.series_values += 1
        assert key not in self.values
        self.values[key] = D.from_float(key[3] * 0.75)
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
    assert b.frozen.pool.coefficients[0] == 2 / count
    assert b.frozen.pool.coefficients[-1] == 4 - 2 / count
    assert "observations" not in a.PoolMaterial.model_fields
    assert a.rebind(b) == b


@pytest.mark.parametrize(
    "field,value",
    [
        ("count", 64),
        ("protocol_sha256", "0" * 64),
        ("cells", ()),
        ("pool", NativeSpringPool(coefficients=(1.0,))),
    ],
)
def test_freeze_mutation_is_rederived(field: str, value: object) -> None:
    b = bound()
    with pytest.raises(ValueError):
        a.rebind(replace(b, frozen=b.frozen.model_copy(update={field: value})))


@pytest.mark.parametrize("case", ["M01", "D03", "F02", "W03"])
def test_every_physical_prefix_shape(case: CaseId) -> None:
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
    assert prior.finite_mean == point(D("0.75"))
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
        cache.consume(
            0,
            1 if fault == "record" else 0,
            0.5 if fault == "scale" else 0.25,
            a.request_for(b, 0),
            "other" if fault == "attempt" else "first",
        )
    assert cache.failed and cache.attempted == 0


def test_precompute_failure_cannot_retry() -> None:
    cache = a.FirstRecordCache(bound(), "first")

    def fail(actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
        raise RuntimeError("injected")

    with pytest.raises(RuntimeError):
        cache.precompute(fail)
    assert cache.attempted == 1 and not cache.rows and cache.failed
    with pytest.raises(ValueError):
        cache.precompute(fake_prediction)


def test_reference_full_endpoint_census_bypasses_legacy_lookups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refs = reference(monkeypatch)
    for case in CASE_IDS:
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

    def fail(key: Key) -> Decimal:
        raise RuntimeError("injected reference failure")

    monkeypatch.setattr(refs.channels["strong"], "position", fail)
    with pytest.raises(RuntimeError):
        refs.training("M01", 256, 0.125, 0, 0)
    assert refs.calls[0].status == "failed"
    with pytest.raises(ValueError):
        refs.training("M01", 256, 0.125, 1, 0)
    assert refs.census()["logical_attempted"] == 1


def test_reference_duplicate_logical_slot_is_not_another_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refs = reference(monkeypatch)
    refs.take_training("D03", 256, 0.25, 0, 0)
    refs.take_training("D03", 256, 0.25, 0, 1)
    assert refs.census()["lookups"] == 1
    assert refs.census()["cache_hits"] == 1
    with pytest.raises(ValueError):
        refs.take_training("D03", 256, 0.25, 0, 1)


@pytest.mark.parametrize("bad", [D("NaN"), D("Infinity"), D("1.23456789" + "1" * 100)])
def test_transcendental_center_shape(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        a.rounded_decimal(bad)


def test_positive_log_perturbation_encloses_rational_argument() -> None:
    result = a.log_perturbation(D(1), Interval(D("0.99"), D("1.01")), D(0))
    assert result.enclosure.lower < D("-0.01")
    assert result.enclosure.upper > D("0.01")
    with pytest.raises(ValueError):
        a.log_perturbation(D(1), Interval(D(0), D(1)), D(0))


def test_reference_constants_and_normalization_counts_are_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refs = reference(monkeypatch)
    constants = refs.constants()
    assert refs.constants() is constants
    assert refs.census()["log_calls"] == 6
    assert refs.census()["machin_terms"] == 128
    joint = tuple(a.ReferenceValue(D(0), point(0)) for _ in range(256))
    result = refs.normalize("M01", 256, 0.125, joint)
    assert result.probabilities[0].lower <= D(1) / 256 <= result.probabilities[0].upper
    assert refs.census()["exp_calls"] == 256 and refs.census()["log_calls"] == 7
    with pytest.raises(ValueError):
        refs.normalize("M01", 256, 0.125, joint)


def test_wider_reference_does_not_enlarge_frozen_allowance(monkeypatch: pytest.MonkeyPatch) -> None:
    refs = reference(monkeypatch)
    joint = tuple(a.ReferenceValue(D(0), around(D(0), D("1e-40"))) for _ in range(256))
    with pytest.raises(ValueError, match="reference envelope"):
        refs.normalize("M01", 256, 0.125, joint)
    assert refs.failed and refs.normalizations_completed == 0
    assert refs.census()["exp_calls"] == 256


def test_training_bound_uses_half_time_and_ignores_ambient_context() -> None:
    frozen = bound("W03").frozen
    endpoints = (0.09375,) * 256
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
        first = D(1) / 256 + residual
    masses = (point(first),) + (point(1.0 / 256),) * 255
    with pytest.raises(ValueError, match="infeasible"):
        a.training_forecast(
            frozen, (0.75,) * 256, D(0), source="matched-base-posterior", masses=masses
        )


@pytest.mark.parametrize("center", [D(0), D("1e-256")])
def test_zero_and_tiny_transcendental_rounding_stay_in_bounded_codec(center: Decimal) -> None:
    result = a.rounded_decimal(center)
    assert result.lower < center < result.upper
    low, high = result.lower.as_tuple().exponent, result.upper.as_tuple().exponent
    assert isinstance(low, int) and isinstance(high, int)
    assert low >= -256 and high >= -256


@pytest.mark.parametrize("records,expected", [(1, D("-2.5")), (2, D(-3))])
def test_full_prefix_has_duplicate_loss_but_only_one_prior(records: int, expected: Decimal) -> None:
    result = a.joint_enclosure(
        (0.75,) * records, (point(0.5),) * records, 0.25, point(0), point(-2)
    )
    assert result == point(expected)


@pytest.mark.parametrize(
    "recorded,predicted,scale",
    [
        ((), (), 0.25),
        ((0.75, 0.75), (point(0.5),), 0.25),
        ((float("nan"),), (point(0.5),), 0.25),
        ((0.75,), (point(3),), 0.25),
        ((0.75,), (point(0.5),), 0.1),
    ],
)
def test_whole_prefix_arithmetic_refuses_missing_or_invalid_terms(
    recorded: tuple[float, ...],
    predicted: tuple[Interval, ...],
    scale: float,
) -> None:
    with pytest.raises(ValueError):
        a.joint_enclosure(recorded, predicted, scale, point(0), point(-2))


def test_conditioned_native_error_is_separate_from_reference_endpoint_error() -> None:
    native = a.joint_enclosure((0.75,), (point(0.5),), 0.25, point(0), point(0))
    ideal = a.joint_enclosure((0.75,), (around(D("0.499"), D("1e-60")),), 0.25, point(0), point(0))
    assert native == point(D("-0.5"))
    assert ideal.upper < native.lower
    assert absolute_upper(minus(point(-0.49), native)) > D("0.009")


@pytest.mark.parametrize(
    "actual,reference",
    [
        ((point(0),), (point(1),)),
        ((point(1),), (point(D("0.1")),)),
        ((point(D("0.5")),), (point(D("0.5")), point(D("0.5")))),
    ],
)
def test_probability_error_does_not_drop_or_repair_nodes(
    actual: tuple[Interval, ...],
    reference: tuple[Interval, ...],
) -> None:
    with pytest.raises(ValueError):
        a.probability_ratio_bound(actual, reference)


def test_identical_exact_probability_vectors_have_zero_ratio_error() -> None:
    values = (point(D("0.25")), point(D("0.75")))
    assert a.probability_ratio_bound(values, values) == 0


def test_future_join_and_failure_do_not_make_new_native_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    b = bound()
    refs = reference(monkeypatch)
    rows = tuple(
        a.bind_prediction(
            a.request_for(b, i, future=True),
            fake_prediction(a.request_for(b, i, future=True), attempt_id="future"),
            attempt_id="future",
        )
        for i in range(256)
    )
    qualified = a.qualify_future(b, "future", rows, refs)
    a.validate_future(qualified)
    assert refs.census()["lookups"] == 256
    with pytest.raises(ValueError):
        a.validate_future(replace(qualified, captures=rows[:-1]))
    bad = replace(qualified.endpoints, max_abs_error_upper=D("1e-10"))
    with pytest.raises(ValueError):
        a.validate_future(replace(qualified, endpoints=bad))
    with pytest.raises(ValueError):
        a.validate_future(replace(qualified, captures=rows[::-1]))
    assert refs.census()["lookups"] == 256


def belief_input(b: a.BoundCandidates, scale: float = 0.25, attempt: str = "belief") -> bytes:
    return a.encoded(
        NativeEndpointBeliefInput(
            attempt_id=attempt,
            candidate_attempt_id=b.attempt_id,
            candidate_input=b.actual,
            candidate_result=b.result,
            prediction_config=b.frozen.prediction_config,
            profile=EndpointBeliefProfile(discrepancy=scale, cells=b.frozen.cells),
            prediction_budget=b.frozen.count * len(b.public.observations.records),
        )
    )


def synthetic_belief_result(raw: bytes, rows: tuple[a.CapturedPrediction, ...]) -> bytes:
    # Construct a complete metadata/result surrogate; no normalizer is executed.
    import hashlib

    from strange_physics.finite_log_weight_contracts import (
        FiniteLogWeight,
        FiniteLogWeightInput,
        FiniteLogWeightResult,
        NormalizedLogWeight,
        ShiftedLogNormalizer,
    )
    from strange_physics.native_endpoint_belief_contracts import EndpointNodeEvaluation

    actual = parse_native_endpoint_belief_input(raw)
    count = len(actual.candidate_input.pool.coefficients)
    assert count == 256
    hashes = tuple(message_sha256(m) for m in actual.candidate_result.payload.models)
    nodes = tuple(
        EndpointNodeEvaluation(model_sha256=h, log_likelihood=0.0, log_prior_mass=0.0)
        for h in hashes
    )
    weights = FiniteLogWeightInput(
        entries=tuple(FiniteLogWeight(item_sha256=h, kind="finite", log_weight=0.0) for h in hashes)
    )
    log_sum = 5.545177444479562
    normal = FiniteLogWeightResult(
        input_sha256=message_sha256(weights),
        status="normalized",
        input_count=count,
        finite_count=count,
        exact_zero_count=0,
        upstream_failed_indices=(),
        exp_underflow_indices=(),
        exp_evaluations=count,
        fsum_evaluations=1,
        log_evaluations=1,
        failure_stage=None,
        failure_index=None,
        normalizer=ShiftedLogNormalizer(maximum_log_weight=0.0, log_scaled_sum=log_sum),
        entries=tuple(
            NormalizedLogWeight(item_sha256=h, kind="finite", log_probability=-log_sum)
            for h in hashes
        ),
    )
    requested = actual.prediction_budget
    records = len(actual.candidate_input.observations.records)
    result = NativeEndpointBeliefResult(
        attempt_id=actual.attempt_id,
        input_raw_sha256=hashlib.sha256(raw).hexdigest(),
        input_sha256=message_sha256(actual),
        profile_sha256=message_sha256(actual.profile),
        candidate_result_sha256=message_sha256(actual.candidate_result),
        observation_sha256=message_sha256(actual.candidate_input.observations),
        status="normalized",
        reason=None,
        candidate_count=count,
        completed_record_indices=tuple(range(records)),
        failed_record_indices=(),
        predictions_requested=requested,
        predictions_completed=requested,
        predictions_failed=0,
        predictions_unassessed=0,
        frames_completed=2 * requested,
        frames_failed=0,
        frames_unassessed=0,
        likelihood_evaluations=requested,
        completed_nodes=count,
        failed_node_index=None,
        failed_record_index=None,
        prediction_result_sha256=tuple(message_sha256(x.result) for x in rows),
        nodes=nodes,
        normalizer_input=weights,
        normalization=normal,
    )
    return a.encoded(result, a.RESULT_LIMIT)


def synthetic_rows(
    b: a.BoundCandidates, attempt: str = "belief"
) -> tuple[a.CapturedPrediction, ...]:
    return tuple(
        a.bind_prediction(
            a.request_for(b, node, record=record),
            fake_prediction(a.request_for(b, node, record=record), attempt_id=attempt),
            attempt_id=attempt,
        )
        for node in range(b.frozen.count)
        for record in range(len(b.public.observations.records))
    )


def test_observer_replays_only_record_zero_and_binds_complete_raw_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    b = bound("D03")
    first = a.FirstRecordCache(b, "first")
    first.precompute(fake_prediction)
    first.seal_prior(reference(monkeypatch))
    calls = []

    def count(actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
        calls.append(message_sha256(actual))
        return fake_prediction(actual, attempt_id=attempt_id)

    raw = belief_input(b, attempt="first")
    observer = a.TrainingObserver(raw, b, count, first)
    for node in range(256):
        for record in range(2):
            observer(a.request_for(b, node, record=record), attempt_id="first")
    assert len(calls) == 256
    assert len(observer.rows) == 512 and first.consumed == set(range(256))
    result = observer.finish(synthetic_belief_result(raw, tuple(observer.rows)))
    assert a.bind_prefix(result) == result
    with pytest.raises(ValueError):
        observer(a.request_for(b, 0), attempt_id="first")


@pytest.mark.parametrize("wrong", ["node", "attempt", "configuration"])
def test_observer_rejects_wrong_callback_before_forward(wrong: str) -> None:
    b = bound()
    raw = belief_input(b)
    calls = []

    def count(actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
        calls.append(actual)
        return fake_prediction(actual, attempt_id=attempt_id)

    observer = a.TrainingObserver(raw, b, count)
    actual = a.request_for(b, 1 if wrong == "node" else 0)
    if wrong == "configuration":
        actual = actual.model_copy(
            update={"request": actual.request.model_copy(update={"times": (0.0, 0.75)})}
        )
    with pytest.raises(ValueError):
        observer(actual, attempt_id="wrong" if wrong == "attempt" else "belief")
    assert observer.failed and not calls and observer.attempted == 1


@pytest.mark.parametrize("wrong", ["missing", "substituted", "raw"])
def test_observer_finish_rejects_incomplete_or_substituted_material(wrong: str) -> None:
    b = bound()
    raw = belief_input(b)
    observer = a.TrainingObserver(raw, b, fake_prediction)
    rows = synthetic_rows(b)
    result_raw = synthetic_belief_result(raw, rows)
    observer.rows = list(rows[:-1] if wrong == "missing" else rows)
    observer.attempted = len(observer.rows)
    if wrong == "substituted":
        observer.rows[0] = rows[1]
    if wrong == "raw":
        result_raw += b" trailing"
    with pytest.raises(ValueError):
        observer.finish(result_raw)
    assert observer.finished


class AlignedOracle(FakeOracle):
    """Primitive transport response for binder tests, not a mathematical oracle."""

    def log(self, value: Decimal) -> Decimal:
        self.log_calls += 1
        return D.from_float(5.545177444479562) if value == D(256) else D(0)


def qualified(monkeypatch: pytest.MonkeyPatch) -> a.QualifiedPrefixEvidence:
    monkeypatch.setattr(a, "EndpointOracle", AlignedOracle)
    refs = a.D1Reference()
    b = bound()
    raw = belief_input(b)
    rows = synthetic_rows(b)
    result_raw = synthetic_belief_result(raw, rows)
    prefix = a.BoundPrefix(
        b,
        raw,
        result_raw,
        parse_native_endpoint_belief_input(raw),
        parse_native_endpoint_belief_result(result_raw),
        rows,
    )
    future_rows = tuple(
        a.bind_prediction(
            a.request_for(b, i, future=True),
            fake_prediction(a.request_for(b, i, future=True), attempt_id="future"),
            attempt_id="future",
        )
        for i in range(256)
    )
    future = a.qualify_future(b, "future", future_rows, refs)
    return a.qualify_prefix(prefix, future, refs, lambda _: 1.0 / 256)


def test_full_prefix_binder_retains_actual_vector_and_complete_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = qualified(monkeypatch)
    assert len(value.nodes) == len(value.probabilities) == 256
    assert value.probabilities == tuple(point(1.0 / 256) for _ in range(256))
    assert value.training[0].max_abs_error_upper == 0
    assert value.arithmetic.node_other_arithmetic_upper < D("1e-48")
    assert len(a.prefix_digest(value)) == 64
    with pytest.raises(ValueError):
        a.bind_prefix(replace(value.bound, captures=value.bound.captures[::-1]))


def duplicate_case(
    monkeypatch: pytest.MonkeyPatch, matched: a.QualifiedPrefixEvidence
) -> tuple[FixtureBatch, a.BoundCandidates, D1Certificate, list[FixtureBatch]]:
    from types import SimpleNamespace
    from typing import cast

    from d1_bounds import D1Identity, D1PrefixPremises, certify_d1_prefix
    from d1_fixture_reference import Attempt, FixtureBatch, Sources
    from test_calibration_fixture_contracts import audit

    duplicate = bound("D03", token="2")
    left = matched.bound.candidates
    attempts = (
        Attempt("M03", left.public, audit(left.public, "M03"), ()),
        Attempt("D03", duplicate.public, audit(duplicate.public, "D03"), ()),
    )
    # Unit3 already tests actual source/rounding/exposure reconstruction. This
    # transport double proves this layer delegates that required check and joins
    # its returned material; it is not a fabricated scientific source receipt.
    batch = cast(
        FixtureBatch,
        SimpleNamespace(
            attempts=attempts, commit="c" * 40, sources=Sources(commit="c" * 40, pins=(), sizes=())
        ),
    )
    checked = []

    def verify(actual: FixtureBatch) -> tuple[ObservationBundle, ...]:
        assert actual is batch
        checked.append(actual)
        return tuple(candidate_material(x.public) for x in actual.attempts)

    monkeypatch.setattr(a, "candidate_materials", verify)
    identity = D1Identity(
        case="M03",
        count=256,
        scale=D("0.25"),
        source_commit="c" * 40,
        observation_sha256=message_sha256(left.actual.observations),
        future_query_sha256=message_sha256(left.frozen.future),
        future_values_sha256=a.future_digest(matched.future),
        probabilities_sha256=a.probability_digest(matched.probabilities),
        evidence_sha256=a.prefix_digest(matched),
    )
    certificate = certify_d1_prefix(
        D1PrefixPremises(
            identity,
            (point(0.75),),
            matched.training,
            matched.future.endpoints,
            matched.arithmetic,
        )
    )
    assert certificate.passed
    return batch, duplicate, certificate, checked


def test_d03_equivalence_preserves_provenance_and_uses_no_new_forward(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matched = qualified(monkeypatch)
    batch, duplicate, certificate, checked = duplicate_case(monkeypatch, matched)
    witness = a.duplicate_forecast(batch, matched, duplicate, certificate)
    assert len(checked) == 1
    assert witness.matched_observation_sha256 != witness.duplicate_observation_sha256
    assert witness.matched_model_sha256 != witness.duplicate_model_sha256
    assert witness.forecast.source == "matched-base-posterior"
    assert witness.forecast.finite_mean == point(D("0.75"))
    with pytest.raises(ValueError):
        a.duplicate_forecast(batch, matched, duplicate, replace(certificate, passed=False))
    wrong = replace(certificate.identity, future_query_sha256="f" * 64)
    assert certificate.prefix is not None
    bad_certificate = certify_d1_prefix(replace(certificate.prefix, identity=wrong))
    with pytest.raises(ValueError):
        a.duplicate_forecast(batch, matched, duplicate, bad_certificate)
    altered = list(matched.emitted)
    altered[0] = 0.25
    with pytest.raises(ValueError):
        a.duplicate_forecast(
            batch, replace(matched, emitted=tuple(altered)), duplicate, certificate
        )


@pytest.mark.parametrize(
    "field",
    [
        "training",
        "arithmetic",
        "node",
        "reference_coverage",
        "constant",
        "sum",
        "probability",
        "normalized_log",
    ],
)
def test_material_recheck_rejects_derived_substitutions(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    value = qualified(monkeypatch)
    if field == "training":
        value = replace(
            value, training=(replace(value.training[0], max_abs_error_upper=D("1e-13")),)
        )
    elif field == "arithmetic":
        value = replace(
            value, arithmetic=replace(value.arithmetic, node_other_arithmetic_upper=D(0))
        )
    elif field == "node":
        value = replace(
            value, nodes=(replace(value.nodes[0], conditioned_joint=point(0)), *value.nodes[1:])
        )
    elif field == "reference_coverage":
        value = replace(value, nodes=(replace(value.nodes[0], references=()), *value.nodes[1:]))
    elif field == "constant":
        gaussian = value.constants.gaussian
        value = replace(
            value,
            constants=replace(
                value.constants,
                gaussian=(replace(gaussian[0], enclosure=point(0)), *gaussian[1:]),
            ),
        )
    elif field == "sum":
        value = replace(value, normalization=replace(value.normalization, sum_center=D(255)))
    elif field == "probability":
        value = replace(
            value,
            normalization=replace(
                value.normalization, probabilities=tuple(point(1.0 / 256) for _ in range(256))
            ),
        )
    else:
        value = replace(
            value,
            normalization=replace(
                value.normalization, normalized_logs=tuple(point(0) for _ in range(256))
            ),
        )
    with pytest.raises(ValueError):
        a.recheck_prefix_evidence(value)


def test_material_recheck_is_pure_under_hostile_context(monkeypatch: pytest.MonkeyPatch) -> None:
    value = qualified(monkeypatch)

    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Recheck must not repeat any primitive/reference computation")

    for oracle in (FakeOracle, AlignedOracle):
        for name in ("position", "exp", "log", "circle_constant", "trig"):
            monkeypatch.setattr(oracle, name, deny)
    with localcontext() as ctx:
        ctx.prec = 3
        ctx.rounding = ROUND_UP
        assert a.recheck_prefix_evidence(value) == value


def test_d03_rejects_coherent_substituted_masses_and_forged_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from d1_bounds import D1Identity, D1PrefixPremises, certify_d1_prefix

    original = qualified(monkeypatch)
    batch, duplicate, certificate, _ = duplicate_case(monkeypatch, original)
    emitted = (0.25, *original.emitted[1:])
    altered = replace(
        original,
        emitted=emitted,
        probabilities=probabilities(emitted),
        arithmetic=ArithmeticEvidence(D(0), D(0), D(0), D(0), D(0)),
    )
    assert altered.bound.input_raw == original.bound.input_raw
    assert altered.bound.result_raw == original.bound.result_raw
    assert altered.bound.captures == original.bound.captures
    # Recompute every claimed vector/evidence/certificate join, rather than
    # relying on a stale hash to make the negative test fail trivially.
    identity = replace(
        certificate.identity,
        probabilities_sha256=a.probability_digest(altered.probabilities),
        evidence_sha256=a.prefix_digest(altered),
    )
    assert type(identity) is D1Identity
    forged = certify_d1_prefix(
        D1PrefixPremises(
            identity,
            (point(0.75),),
            altered.training,
            altered.future.endpoints,
            altered.arithmetic,
        )
    )
    assert forged.passed
    with pytest.raises(ValueError):
        a.duplicate_forecast(batch, altered, duplicate, forged)


@pytest.mark.parametrize("field", ["training", "arithmetic", "constants", "normalization"])
def test_evidence_digest_binds_derived_material(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    value = qualified(monkeypatch)
    if field == "training":
        changed = replace(
            value, training=(replace(value.training[0], max_abs_error_upper=D("1e-13")),)
        )
    elif field == "arithmetic":
        changed = replace(
            value, arithmetic=replace(value.arithmetic, shifted_log_evidence_error_upper=D(0))
        )
    elif field == "constants":
        changed = replace(value, constants=replace(value.constants, log_two_pi_center=D(1)))
    else:
        changed = replace(
            value,
            normalization=replace(
                value.normalization, normalized_logs=tuple(point(0) for _ in range(256))
            ),
        )
    assert a.prefix_digest(changed) != a.prefix_digest(value)
