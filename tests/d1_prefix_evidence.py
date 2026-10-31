"""Restricted D1 native/reference joins; numerical methods need separate admission.

No runner, persistence, historical completeness, calibration or authority claim.
The later driver owns exact source/runtime pins and durable one-attempt ordering.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from typing import Literal

from endpoint_belief_reference import EndpointOracle, Key
from grid_q1_bounds import Interval
from grid_q1_evidence import (
    absolute_upper, around, divide, minus, negative, plus, point, probabilities,
    square, times, total,
)

from strange_physics.bounded_json import bounded_canonical
from strange_physics.calibration_fixture_contracts import (
    CASE_IDS, PROTOCOL_SHA256, CaseId, D1PublicFixture, candidate_material, parse_d1_public,
)
from strange_physics.contracts import Experiment, Message, Structure
from strange_physics.native_endpoint_belief_contracts import (
    EndpointBeliefProfile, EndpointCell, NativeEndpointBeliefInput,
    NativeEndpointBeliefResult, bind_native_endpoint_belief_result,
    parse_native_endpoint_belief_input, parse_native_endpoint_belief_result,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig, NativePredictionInput, NativePredictionResult,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig, NativeCandidateInput, NativeCandidateResult,
    NativeSpringPool, parse_native_candidate_input, parse_native_candidate_result,
    validate_native_candidate_result,
)
from strange_physics.research_contracts import PredictionRequest, message_sha256

D = Decimal
COUNTS = (256, 1024)
SCALES = (0.125, 0.25, 0.5)
REFERENCE_ERROR = D("1e-60")
INPUT_LIMIT, RESULT_LIMIT = 16 * 1024**2, 4 * 1024**2


def context() -> Context:
    return Context(prec=100, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                   capitals=1, clamp=0, flags=[], traps=[])


def encoded(value: Message, limit: int = INPUT_LIMIT) -> bytes:
    # The canonical encoder already bounds bytes before retaining this second encoding.
    bounded_canonical(value, limit)
    raw = value.model_dump_json().encode()
    if len(raw) > limit:
        raise ValueError("Actual material exceeds its declared bound")
    return raw


def checked[T: Message](value: T, kind: type[T], limit: int = INPUT_LIMIT) -> T:
    if type(value) is not kind:
        raise ValueError("Exact typed material required")
    return kind.model_validate_json(encoded(value, limit))


def profile_scales(case: CaseId) -> tuple[float, ...]:
    if case not in CASE_IDS:
        raise ValueError("Unknown D1 case")
    return (0.25,) if case in ("D03", "W03") else SCALES


def profile_key(case: CaseId, count: int, scale: float, node: int = 0) -> None:
    if (type(count) is not int or count not in COUNTS or type(scale) is not float
            or scale not in profile_scales(case) or type(node) is not int
            or not 0 <= node < count):
        raise ValueError("Outside the fixed D1 matrix")


def _query(structure: Structure, experiment: Experiment, *, future: bool) -> float:
    if (len(structure.particle_ids) != 1 or len(structure.anchors) != 1
            or structure.anchors[0].position != (0.0, 0.0)
            or len(structure.connections) != 1
            or {structure.connections[0].a, structure.connections[0].b}
            != {structure.particle_ids[0], structure.anchors[0].id}
            or len(experiment.particles) != 1):
        raise ValueError("Fixed public one-particle zero-anchor structure required")
    p = experiment.particles[0]
    q = p.position[0]
    if (p.id != structure.particle_ids[0] or p.mass != 1.0
            or p.velocity != (0.0, 0.0) or p.position[1] != 0.0
            or q not in ((1.0,) if future else (0.125, 1.0))
            or experiment.impulse is None
            or experiment.impulse.particle_id != p.id
            or experiment.impulse.vector != (0.0, 0.0)):
        raise ValueError("Fixed D1 physical query required")
    return q


class PoolMaterial(Message):
    count: int
    structure: Structure
    training: Experiment
    future: Experiment
    pool: NativeSpringPool
    cells: tuple[EndpointCell, ...]
    candidate_config: NativeCandidateConfig
    prediction_config: NativePredictionConfig
    protocol_sha256: str = PROTOCOL_SHA256


def freeze_pool(count: int, structure: Structure, training: Experiment,
                future: Experiment) -> PoolMaterial:
    """Prefix-free construction: no observation, coefficient truth or audit argument.

    Durable before-label ordering is a later driver obligation. The immutable
    physical choices are re-derived at every bind, not inferred from a timestamp.
    """
    profile_key("M01", count, 0.25)
    structure = checked(structure, Structure)
    training, future = checked(training, Experiment), checked(future, Experiment)
    _query(structure, training, future=False)
    _query(structure, future, future=True)
    return PoolMaterial(
        count=count, structure=structure, training=training, future=future,
        pool=NativeSpringPool(coefficients=tuple((4*i+2)/count for i in range(count))),
        cells=tuple(EndpointCell(left=4*i/count, right=4*(i+1)/count) for i in range(count)),
        candidate_config=NativeCandidateConfig(), prediction_config=NativePredictionConfig(),
    )


def _pool(value: PoolMaterial) -> PoolMaterial:
    value = checked(value, PoolMaterial)
    expected = freeze_pool(value.count, value.structure, value.training, value.future)
    if value != expected:
        raise ValueError("Pool/cells/prior/configuration differs from the prefix-free freeze")
    return value


@dataclass(frozen=True)
class BoundCandidates:
    case: CaseId
    frozen: PoolMaterial
    public: D1PublicFixture
    actual: NativeCandidateInput
    result: NativeCandidateResult
    attempt_id: str


def bind_candidates(case: CaseId, frozen: PoolMaterial, public: D1PublicFixture,
                    actual: NativeCandidateInput, result: NativeCandidateResult,
                    *, attempt_id: str) -> BoundCandidates:
    frozen = _pool(frozen)
    profile_key(case, frozen.count, profile_scales(case)[0])
    public = parse_d1_public(encoded(public))
    # Explicit CORE allowlist projection, never removal of private envelope fields.
    observations = candidate_material(public)
    actual = parse_native_candidate_input(encoded(actual))
    result = parse_native_candidate_result(encoded(result, RESULT_LIMIT))
    validate_native_candidate_result(result, actual, attempt_id=attempt_id)
    records = observations.records
    if (actual.observations != observations or actual.pool != frozen.pool
            or actual.config != frozen.candidate_config or result.payload.status != "produced"
            or observations.space.structure != frozen.structure
            or len(records) != (2 if case == "D03" else 1)
            or any(r.experiment != frozen.training or r.status != "completed" for r in records)
            or frozen.training.particles[0].position[0] != (0.125 if case == "W03" else 1.0)):
        raise ValueError("Exact public prefix, fixed pool and physical action must join")
    return BoundCandidates(case, frozen, public, actual, result, attempt_id)


def rebind(bound: BoundCandidates) -> BoundCandidates:
    return bind_candidates(bound.case, bound.frozen, bound.public, bound.actual, bound.result,
                           attempt_id=bound.attempt_id)


def request_for(bound: BoundCandidates, node: int, *, future: bool = False,
                record: int = 0) -> NativePredictionInput:
    # Callers rebind once at their batch boundary; each request still uses exact
    # retained model/configuration and a bounded physical slot.
    profile_key(bound.case, bound.frozen.count, profile_scales(bound.case)[0], node)
    if type(record) is not int or not 0 <= record < len(bound.public.observations.records):
        raise ValueError("Record slot outside the complete prefix")
    model = bound.result.payload.models[node]
    experiment = bound.frozen.future if future else bound.public.observations.records[record].experiment
    return NativePredictionInput(
        model=model, candidate_config=bound.frozen.candidate_config,
        config=bound.frozen.prediction_config,
        request=PredictionRequest(model_sha256=message_sha256(model),
            structure=bound.frozen.structure, experiment=experiment,
            times=(0.0, 0.75 if future else 0.5), integration_dt=1/64),
    )


@dataclass(frozen=True)
class CapturedPrediction:
    actual: NativePredictionInput
    result: NativePredictionResult
    attempt_id: str

    def endpoint(self) -> float:
        response = self.result.payload.response
        if self.result.payload.status != "predicted" or response is None:
            raise ValueError("A failed prediction has no usable endpoint")
        return response.trajectory.frames[-1].positions[0][0]


def bind_prediction(actual: NativePredictionInput, result: NativePredictionResult,
                    *, attempt_id: str) -> CapturedPrediction:
    actual = checked(actual, NativePredictionInput)
    result = checked(result, NativePredictionResult, RESULT_LIMIT)
    validate_native_prediction_result(result, actual, attempt_id=attempt_id)
    return CapturedPrediction(actual, result, attempt_id)


type Predictor = Callable[..., NativePredictionResult]


class FirstRecordCache:
    """One ensemble's precomputed record0, replayable only in its first profile.

    Failed/attempted work remains inspectable. This in-memory latch does not
    substitute for the future driver's durable attempt authority.
    """
    def __init__(self, bound: BoundCandidates, attempt_id: str) -> None:
        self.bound = rebind(bound)
        self.attempt_id = attempt_id
        self.started = False
        self.failed = False
        self.attempted = 0
        self.rows: list[CapturedPrediction] = []
        self.consumed: set[int] = set()
        self.forecast: TrainingForecast | None = None

    def precompute(self, predictor: Predictor) -> tuple[CapturedPrediction, ...]:
        if self.started:
            raise ValueError("Precomputation opportunity already consumed")
        self.started = True
        try:
            for node in range(self.bound.frozen.count):
                actual = request_for(self.bound, node)
                self.attempted += 1
                result = predictor(actual, attempt_id=self.attempt_id)
                row = bind_prediction(actual, result, attempt_id=self.attempt_id)
                self.rows.append(row)
                row.endpoint()
        except BaseException:
            self.failed = True
            raise
        return tuple(self.rows)

    def seal_prior(self, reference: D1Reference) -> TrainingForecast:
        if self.forecast is not None or self.failed or len(self.rows) != self.bound.frozen.count:
            raise ValueError("Complete first-record forward and one prior freeze required")
        try:
            maximum = D(0)
            for node, row in enumerate(self.rows):
                value = reference.training(self.bound.case, self.bound.frozen.count,
                                           profile_scales(self.bound.case)[0], node, 0)
                maximum = max(maximum, absolute_upper(minus(point(row.endpoint()), point(value.center))))
            if maximum > D("1e-12"):
                raise ValueError("Prior endpoint qualification failed")
            error = plus(point(maximum), point(REFERENCE_ERROR)).upper
            self.forecast = training_forecast(self.bound.frozen, tuple(r.endpoint() for r in self.rows),
                                              error, source="prior")
        except BaseException:
            self.failed = True
            raise
        return self.forecast

    def consume(self, node: int, record: int, scale: float, actual: NativePredictionInput,
                attempt_id: str) -> NativePredictionResult:
        if (self.failed or self.forecast is None or scale != profile_scales(self.bound.case)[0]
                or record != 0 or attempt_id != self.attempt_id
                or type(node) is not int or not 0 <= node < len(self.rows) or node in self.consumed):
            self.failed = True
            raise ValueError("Unexpected or repeated exact first-record cache slot")
        self.consumed.add(node)  # A failed replay check cannot reopen the slot.
        row = self.rows[node]
        try:
            if checked(actual, NativePredictionInput) != row.actual:
                raise ValueError("Replay requires the full original request, not only its hash")
            return bind_prediction(actual, row.result, attempt_id=attempt_id).result
        except BaseException:
            self.failed = True
            raise

    def require_complete(self) -> None:
        if self.failed or self.consumed != set(range(self.bound.frozen.count)):
            raise ValueError("Required first-record cache entries remain failed or unconsumed")


@dataclass(frozen=True)
class BoundPrefix:
    candidates: BoundCandidates
    input_raw: bytes
    result_raw: bytes
    actual: NativeEndpointBeliefInput
    result: NativeEndpointBeliefResult
    captures: tuple[CapturedPrediction, ...]


class TrainingObserver:
    """Exact node-major/record-minor callback for the existing producer extension.

    The driver installs this only around the pinned native function and restores
    it in finally. This helper never replaces a global callback by itself.
    """
    def __init__(self, raw: bytes, bound: BoundCandidates, predictor: Predictor,
                 first: FirstRecordCache | None = None) -> None:
        self.bound = rebind(bound)
        bound = self.bound
        self.actual = parse_native_endpoint_belief_input(raw)
        a = self.actual
        profile_key(bound.case, bound.frozen.count, a.profile.discrepancy)
        expected = EndpointBeliefProfile(discrepancy=a.profile.discrepancy, cells=bound.frozen.cells)
        if (a.candidate_input != bound.actual or a.candidate_result != bound.result
                or a.candidate_attempt_id != bound.attempt_id or a.profile != expected
                or a.prediction_config != bound.frozen.prediction_config
                or a.prediction_budget != bound.frozen.count*len(bound.public.observations.records)):
            raise ValueError("Belief input differs from the bound complete prefix/profile")
        if (first is None) == (a.profile.discrepancy == profile_scales(bound.case)[0]):
            raise ValueError("First profile requires its sealed prequential cache exactly once")
        if first is not None and (first.bound != self.bound or a.attempt_id != first.attempt_id
                                  or a.profile.discrepancy != profile_scales(bound.case)[0]):
            raise ValueError("Cache belongs to a different ensemble/first profile/attempt")
        self.raw, self.predictor, self.first = raw, predictor, first
        self.attempted = 0
        self.failed = False
        self.rows: list[CapturedPrediction] = []
        self.finished = False

    def __call__(self, actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
        if self.failed or self.finished or self.attempted >= self.actual.prediction_budget:
            raise ValueError("Unexpected callback after termination or full coverage")
        slot = self.attempted
        self.attempted += 1
        records = len(self.bound.public.observations.records)
        node, record = divmod(slot, records)
        try:
            expected = request_for(self.bound, node, record=record)
            actual = checked(actual, NativePredictionInput)
            if actual != expected or attempt_id != self.actual.attempt_id:
                raise ValueError("Full prediction request/attempt differs from ordered prefix slot")
            result = (self.first.consume(node, record, self.actual.profile.discrepancy,
                                        actual, attempt_id)
                      if self.first is not None and record == 0
                      else self.predictor(actual, attempt_id=attempt_id))
            row = bind_prediction(actual, result, attempt_id=attempt_id)
            self.rows.append(row)
            if row.result.payload.status != "predicted":
                self.failed = True
            return row.result
        except BaseException:
            self.failed = True
            raise

    def finish(self, result_raw: bytes) -> BoundPrefix:
        if self.finished:
            raise ValueError("Belief completion already consumed")
        self.finished = True
        bind_native_endpoint_belief_result(result_raw, self.raw)
        result = parse_native_endpoint_belief_result(result_raw)
        if (self.failed or result.status != "normalized" or len(self.rows) != self.actual.prediction_budget
                or result.prediction_result_sha256 != tuple(message_sha256(x.result) for x in self.rows)):
            raise ValueError("No partial/failed/survivor-only prefix qualification")
        if self.first is not None:
            self.first.require_complete()
        return BoundPrefix(self.bound, self.raw, result_raw, self.actual, result, tuple(self.rows))


@dataclass(frozen=True)
class TrainingForecast:
    pool_sha256: str
    query_sha256: str
    endpoints: tuple[float, ...]
    masses: tuple[Interval, ...]
    endpoint_error: Decimal
    delta: Decimal
    source: Literal["prior", "matched-base-posterior"]
    finite_mean: Interval
    continuous_mean: Interval


def training_forecast(frozen: PoolMaterial, endpoints: tuple[float, ...], error: Decimal,
                      *, source: Literal["prior", "matched-base-posterior"],
                      masses: tuple[Interval, ...] | None = None, delta: Decimal = D(0)) -> TrainingForecast:
    frozen = _pool(frozen)
    if (len(endpoints) != frozen.count or any(type(x) is not float or not math.isfinite(x)
                                            or not -2 <= x <= 2 for x in endpoints)
            or not D(0) <= error <= plus(point(D("1e-12")), point(REFERENCE_ERROR)).upper
            or not D(0) <= delta <= D(1)):
        raise ValueError("Complete finite training endpoints and certified allowances required")
    if source == "prior":
        if masses is not None or delta != 0:
            raise ValueError("Prior forecast has exact uniform masses and zero cell-mass error")
        masses = tuple(point(1.0/frozen.count) for _ in endpoints)
    elif source != "matched-base-posterior" or masses is None or len(masses) != frozen.count:
        raise ValueError("Matched posterior forecast requires the exact qualified vector")
    for mass in masses:
        Interval(mass.lower, mass.upper)
        if mass.lower < 0 or mass.upper > 1:
            raise ValueError("Invalid forecast mass enclosure")
    # Bounded exact rational sums cannot conceal a sub-100-digit residual.
    if not sum((Fraction(p.lower) for p in masses), Fraction(0)) <= 1 <= sum(
        (Fraction(p.upper) for p in masses), Fraction(0)
    ):
        raise ValueError("Forecast mass enclosures are infeasible")
    mean = total(tuple(times(p, point(x)) for p,x in zip(masses, endpoints, strict=True)))
    q = point(frozen.training.particles[0].position[0])
    radius = plus(plus(times(times(point(2), q), point(delta)),
                       divide(q, point(4*frozen.count))), point(error)).upper
    continuous = plus(mean, Interval(radius.copy_negate(), radius))
    return TrainingForecast(message_sha256(frozen), message_sha256(frozen.training), endpoints,
                            masses, error, delta, source, mean, continuous)


def innovation(forecast: TrainingForecast, recorded: float) -> Interval:
    """Release a recorded observation only after the caller retained the forecast."""
    if type(recorded) is not float or not math.isfinite(recorded):
        raise ValueError("Actual finite binary64 observation required")
    return minus(point(recorded), forecast.continuous_mean)


@dataclass(frozen=True)
class ReferenceValue:
    center: Decimal
    enclosure: Interval

    def __post_init__(self) -> None:
        point(self.center)
        Interval(self.enclosure.lower, self.enclosure.upper)
        if not self.enclosure.lower <= self.center <= self.enclosure.upper:
            raise ValueError("Reference center must be retained inside its enclosure")


def _reference(center: Decimal, enclosure: Interval) -> ReferenceValue:
    return ReferenceValue(center, Interval(min(center, enclosure.lower), max(center, enclosure.upper)))


def rounded_decimal(center: Decimal) -> Interval:
    """Enclose a correctly rounded 100-digit Decimal transcendental result.

    This is conditional on the pinned oracle's exp/ln implementation and the
    explicit context, not a claim that an arbitrary supplied number is correct.
    """
    point(center)
    c = context()
    if c.plus(center) != center:
        raise ValueError("Oracle center is not a 100-digit result")
    return Interval(c.next_minus(center), c.next_plus(center))


def log_perturbation(center_argument: Decimal, true_argument: Interval,
                     rounded_log: Decimal) -> ReferenceValue:
    if center_argument <= 0 or true_argument.lower <= 0:
        raise ValueError("Logarithm requires a positive complete argument")
    distance = absolute_upper(minus(point(center_argument), true_argument))
    radius = divide(point(distance), point(min(center_argument, true_argument.lower))).upper
    enclosure = plus(rounded_decimal(rounded_log), Interval(radius.copy_negate(), radius))
    return _reference(rounded_log, enclosure)


@dataclass(frozen=True)
class ReferenceConstants:
    gaussian: tuple[ReferenceValue, ...]
    log_prior: tuple[ReferenceValue, ...]
    pi: ReferenceValue


@dataclass(frozen=True)
class ReferenceNormalization:
    joint: tuple[ReferenceValue, ...]
    emitted: tuple[ReferenceValue, ...]
    sum_center: Decimal
    log_evidence: ReferenceValue
    centered_log_evidence: Interval
    normalized_logs: tuple[Interval, ...]
    probabilities: tuple[Interval, ...]


@dataclass(frozen=True)
class ReferenceCall:
    channel: Literal["strong", "weak", "future"]
    key: Key
    status: Literal["attempted", "completed", "failed"]
    value: ReferenceValue | None = None


class D1Reference:
    """Twelve fixed instances, plus the separate fixture producer's one.

    External cache hits bypass position entirely. No replacement, hidden retry,
    reference refinement, extra log, trig or scientific fixture generation.
    """
    def __init__(self) -> None:
        self.channels = {name: EndpointOracle() for name in ("strong", "weak", "future")}
        self.arithmetic = {case: EndpointOracle() for case in CASE_IDS}
        self.constants_oracle = EndpointOracle()
        self.cache: dict[Key, ReferenceValue] = {}
        self.seen: set[tuple[str, CaseId, int, float, int, int]] = set()
        self.normalized: set[tuple[CaseId, int, float]] = set()
        self.results: dict[tuple[str, CaseId, int, float, int, int], ReferenceValue] = {}
        self.consumed_training: set[tuple[str, CaseId, int, float, int, int]] = set()
        self.calls: list[ReferenceCall] = []
        self.logical_completed = 0
        self.cache_hits = 0
        self.normalizations_completed = 0
        self.failed = False
        self.constants_started = False
        self.constant_values: ReferenceConstants | None = None

    def _endpoint(self, case: CaseId, count: int, scale: float, node: int,
                  record: int, *, future: bool) -> ReferenceValue:
        if self.failed:
            raise ValueError("Reference channel failed; no continuation")
        profile_key(case, count, scale, node)
        if type(record) is not int or record not in range(2 if case == "D03" else 1):
            raise ValueError("Reference record slot outside complete prefix")
        if future and (record != 0 or scale != profile_scales(case)[0]):
            raise ValueError("Future reference is ensemble-only, not repeated for every scale")
        slot = ("future" if future else "training", case, count, scale, node, record)
        if slot in self.seen:
            self.failed = True
            raise ValueError("Logical reference slot was already attempted")
        self.seen.add(slot)
        q = 1.0 if future or case != "W03" else 0.125
        channel: Literal["strong", "weak", "future"] = "future" if future else "weak" if q == 0.125 else "strong"
        key: Key = ((4*node+2)/count, 1.0, 0.0, q, 0.0, 0.0, 0.75 if future else 0.5)
        try:
            if key in self.cache:
                value = self.cache[key]
                self.cache_hits += 1
            else:
                index = len(self.calls)
                self.calls.append(ReferenceCall(channel, key, "attempted"))
                try:
                    with localcontext(context()):
                        center = self.channels[channel].position(key)
                    if type(center) is not Decimal or not D(-2) <= center <= D(2):
                        raise ValueError("Reference endpoint outside the fixed physical envelope")
                    value = ReferenceValue(center, around(center, REFERENCE_ERROR))
                    self.calls[index] = ReferenceCall(channel, key, "completed", value)
                    self.cache[key] = value
                except BaseException:
                    self.calls[index] = ReferenceCall(channel, key, "failed")
                    raise
            self.logical_completed += 1
            self.results[slot] = value
            return value
        except BaseException:
            self.failed = True
            raise

    def training(self, case: CaseId, count: int, scale: float, node: int,
                 record: int) -> ReferenceValue:
        return self._endpoint(case, count, scale, node, record, future=False)

    def take_training(self, case: CaseId, count: int, scale: float, node: int,
                      record: int) -> ReferenceValue:
        """Consume prequential staged reference once, or make the one logical request."""
        slot = ("training", case, count, scale, node, record)
        if self.failed or slot in self.consumed_training:
            self.failed = True
            raise ValueError("Reference prefix slot already consumed or failed")
        value = self.results[slot] if slot in self.results else self.training(case, count, scale, node, record)
        self.consumed_training.add(slot)
        return value

    def future(self, case: CaseId, count: int, node: int) -> ReferenceValue:
        return self._endpoint(case, count, profile_scales(case)[0], node, 0, future=True)

    def constants(self) -> ReferenceConstants:
        if self.failed:
            raise ValueError("Reference channel failed")
        if self.constant_values is not None:
            return self.constant_values
        if self.constants_started:
            raise ValueError("Constant construction already attempted")
        self.constants_started = True
        try:
            oracle = self.constants_oracle
            with localcontext(context()):
                pi_center = oracle.circle_constant()
                if not D(3) < pi_center < D(4):
                    raise ValueError("Machin center outside the fixed enclosure domain")
                pi = ReferenceValue(pi_center, around(pi_center, REFERENCE_ERROR))
                argument = D(2)*pi_center
                two_pi = log_perturbation(argument, times(point(2), pi.enclosure), oracle.log(argument))
                gaussians = []
                for scale in SCALES:
                    log_scale = oracle.log(D.from_float(scale))
                    center = -log_scale - two_pi.center/2
                    enclosure = minus(negative(rounded_decimal(log_scale)),
                                      divide(two_pi.enclosure, point(2)))
                    gaussians.append(_reference(center, enclosure))
                priors = tuple(ReferenceValue(x, rounded_decimal(x))
                               for x in (oracle.log(D(1)/count) for count in COUNTS))
            for value in (*gaussians, *priors):
                if absolute_upper(minus(value.enclosure, point(value.center))) > D("1e-48"):
                    raise ValueError("Derived constant allowance exceeds the frozen reference reserve")
            self.constant_values = ReferenceConstants(tuple(gaussians), priors, pi)
            return self.constant_values
        except BaseException:
            self.failed = True
            raise

    def normalize(self, case: CaseId, count: int, scale: float,
                  joint: tuple[ReferenceValue, ...]) -> ReferenceNormalization:
        if self.failed:
            raise ValueError("Reference channel failed")
        profile_key(case, count, scale)
        key = (case, count, scale)
        if key in self.normalized:
            raise ValueError("Reference normalization already attempted")
        self.normalized.add(key)
        try:
            if len(joint) != count:
                raise ValueError("Every candidate needs its full-prefix reference weight")
            oracle = self.arithmetic[case]
            emitted = []
            with localcontext(context()):
                for value in joint:
                    value.__post_init__()
                    if not D(-32) <= value.enclosure.lower <= value.enclosure.upper <= D(4):
                        raise ValueError("Reference joint outside fixed D1 range")
                    eta = absolute_upper(minus(value.enclosure, point(value.center)))
                    if eta >= D(1):
                        raise ValueError("Log perturbation cannot be bounded by the finite rule")
                    center = oracle.exp(value.center)
                    if center <= 0:
                        raise ValueError("Reference normalization lost a node")
                    # e^-eta >= 1-eta; e^eta <= 1/(1-eta). This is a
                    # relative positive-sum bound, not loose exp derivative amplification.
                    factor = Interval(minus(point(1), point(eta)).lower,
                                      divide(point(1), minus(point(1), point(eta))).upper)
                    emitted.append(_reference(center, times(rounded_decimal(center), factor)))
                sum_center = sum((x.center for x in emitted), D(0))
                exact_sum = total(tuple(x.enclosure for x in emitted))
                log_z = log_perturbation(sum_center, exact_sum, oracle.log(sum_center))
                maximum = Interval(max(x.enclosure.lower for x in joint),
                                   max(x.enclosure.upper for x in joint))
                result = ReferenceNormalization(joint, tuple(emitted), sum_center, log_z,
                    minus(log_z.enclosure, maximum),
                    tuple(minus(x.enclosure, log_z.enclosure) for x in joint),
                    tuple(divide(x.enclosure, exact_sum) for x in emitted))
            require_reference_reserve(result)
            self.normalizations_completed += 1
            return result
        except BaseException:
            self.failed = True
            raise

    def census(self) -> dict[str, int]:
        oracles = (*self.channels.values(), *self.arithmetic.values(), self.constants_oracle)
        return {
            "logical_attempted": len(self.seen), "logical_completed": self.logical_completed,
            "cache_hits": self.cache_hits, "position_attempted": len(self.calls),
            "training_consumed": len(self.consumed_training),
            "position_completed": sum(x.status == "completed" for x in self.calls),
            "normalization_attempted": len(self.normalized),
            "normalization_completed": self.normalizations_completed,
            "lookups": sum(x.lookups for x in oracles),
            "series_values": sum(x.series_values for x in oracles),
            "exp_calls": sum(x.exp_calls for x in oracles),
            "log_calls": sum(x.log_calls for x in oracles),
            "trig_calls": sum(x.trig_calls for x in oracles),
            "machin_terms": sum(x.machin_terms for x in oracles),
        }

    def require_complete(self) -> None:
        expected = dict(logical_attempted=37120, logical_completed=37120, cache_hits=33280,
                        position_attempted=3840, position_completed=3840, training_consumed=26880,
                        normalization_attempted=40, normalization_completed=40,
                        lookups=3840, series_values=3840, exp_calls=25600,
                        log_calls=46, trig_calls=0, machin_terms=128)
        if self.failed or self.census() != expected or any(
            x.lookups != 1280 or x.series_values != 1280 for x in self.channels.values()
        ):
            raise ValueError("Incomplete fixed reference work; old guards remain unchanged")


def require_reference_reserve(value: ReferenceNormalization) -> None:
    """Derived bounds must fit the original reserve, never enlarge it."""
    limit = D("1e-48")
    with localcontext(context()):
        centered = value.log_evidence.center-max(x.center for x in value.joint)
        checks = [absolute_upper(minus(value.centered_log_evidence, point(centered))),
                  absolute_upper(minus(value.log_evidence.enclosure, point(value.log_evidence.center)))]
        for joint, weight, logp, probability in zip(value.joint, value.emitted,
                value.normalized_logs, value.probabilities, strict=True):
            checks.extend((absolute_upper(minus(joint.enclosure, point(joint.center))),
                           absolute_upper(minus(logp, point(joint.center-value.log_evidence.center))),
                           absolute_upper(minus(divide(weight.enclosure, point(weight.center)), point(1))),
                           absolute_upper(minus(divide(probability, point(weight.center/value.sum_center)), point(1)))))
    if any(x > limit for x in checks):
        raise ValueError("Derived reference envelope exceeds the frozen1e-48 allowance")
