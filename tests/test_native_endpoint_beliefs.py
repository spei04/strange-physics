from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, cast

import pytest
from endpoint_belief_reference import REFERENCE_ERROR, EndpointOracle, Key, binary

import strange_physics.native_endpoint_beliefs as endpoint
import strange_physics.native_prediction as native_prediction
from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Frame,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Sampling,
    Structure,
    Trajectory,
)
from strange_physics.control_contracts import ContractViolation
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_endpoint_belief_contracts import (
    MAX_INPUT_BYTES,
    EndpointBeliefProfile,
    EndpointCell,
    NativeEndpointBeliefInput,
    NativeEndpointBeliefResult,
    bind_native_endpoint_belief_result,
    native_endpoint_belief_json_schema,
    parse_native_endpoint_belief_input,
    parse_native_endpoint_belief_result,
)
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import NativePredictionConfig, NativePredictionInput
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
)
from strange_physics.research_contracts import PredictionRequest, message_sha256

GRIDS = (16, 64, 256)
SCALES = (0.125, 0.25, 0.5)
RecordProperty = Callable[[str, object], None]


def _grid(count: int, upper: float = 1.0) -> tuple[tuple[float, ...], tuple[EndpointCell, ...]]:
    edges = tuple(upper * i / count for i in range(count + 1))
    return (
        tuple((a + b) / 2 for a, b in zip(edges, edges[1:], strict=False)),
        tuple(EndpointCell(left=a, right=b) for a, b in zip(edges, edges[1:], strict=False)),
    )


@pytest.fixture(scope="module")
def oracle() -> Iterator[EndpointOracle]:
    value = EndpointOracle()
    # A bounded shared table is explicit. It is never an unbounded/global memoizer.
    for count in GRIDS:
        for k in _grid(count)[0]:
            for time in (1.0, 2.0):
                value.position((k, 1.0, 0.0, 1.0, 0.0, 0.0, time))
    for k in _grid(1024, 4.0)[0]:
        value.position((k, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))
    for k in (1.0 / 3.0, 1.0):
        value.position((k, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))
    yield value
    print("ENDPOINT_REFERENCE_CENSUS " + json.dumps({
        "series_values": value.series_values, "coefficients_each": 80, "precision": 100,
        "lookups": value.lookups, "exp": value.exp_calls, "ln": value.log_calls,
        "trig_values": value.trig_calls, "trig_terms_each": 80, "machin_terms": value.machin_terms,
    }, sort_keys=True))
    assert value.series_values <= 1728 and value.trig_calls == 4 and value.machin_terms == 128


@dataclass
class Audit:
    oracle: EndpointOracle
    belief: int = 0
    producer: int = 0
    requested_models: int = 0
    fit: int = 0
    future: int = 0
    normalizers: int = 0
    max_forward_error: Decimal = Decimal(0)
    fitted_values: dict[Key, float] = field(default_factory=dict)


@pytest.fixture
def audit(
    oracle: EndpointOracle, monkeypatch: pytest.MonkeyPatch, record_property: RecordProperty
) -> Iterator[Audit]:
    value = Audit(oracle)
    original_predict = endpoint.predict_native_spring
    original_normalize = endpoint.normalize_finite_log_weights

    def counted_predict(
        actual: NativePredictionInput, *, attempt_id: str
    ) -> Any:
        value.fit += 1
        result = original_predict(actual, attempt_id=attempt_id)
        if result.payload.response is not None:
            particle = actual.request.experiment.particles[0]
            impulse = actual.request.experiment.impulse
            key = (
                actual.model.linear, particle.mass, actual.request.structure.anchors[0].position[0],
                particle.position[0], particle.velocity[0],
                0.0 if impulse is None else impulse.vector[0], actual.request.times[-1],
            )
            observed = result.payload.response.trajectory.frames[-1].positions[0][0]
            reference = oracle.position(key)
            with localcontext() as context:
                context.prec = 100
                value.max_forward_error = max(
                    value.max_forward_error, abs(binary(observed) - reference)
                )
            value.fitted_values[key] = observed
        return result

    def counted_normalize(actual: Any) -> Any:
        value.normalizers += 1
        return original_normalize(actual)

    monkeypatch.setattr(endpoint, "predict_native_spring", counted_predict)
    monkeypatch.setattr(endpoint, "normalize_finite_log_weights", counted_normalize)
    yield value
    record_property("endpoint_calls", json.dumps({
        "belief": value.belief, "producer": value.producer,
        "requested_models": value.requested_models, "fit_predictions": value.fit,
        "future_predictions": value.future, "normalizers": value.normalizers,
        "max_forward_error": str(value.max_forward_error),
    }, sort_keys=True))


def _input(
    audit: Audit,
    nodes: tuple[float, ...],
    cells: tuple[EndpointCell, ...],
    *,
    sigma: float = 0.25,
    label: float = 0.75,
    anchor: float = 0.0,
    initial: float = 1.0,
    mass: float = 1.0,
    impulse: float = 0.0,
    repeats: int = 1,
    failed: bool = False,
    all_failed: bool = False,
    noise: float = 0.0,
) -> NativeEndpointBeliefInput:
    experiment = Experiment(
        particles=(ParticleInitial(
            id="mobile", mass=mass, position=(initial, 0.0), velocity=(0.0, 0.0)
        ),),
        impulse=None if impulse == 0 else Impulse(particle_id="mobile", vector=(impulse, 0.0)),
    )
    structure = Structure(
        particle_ids=("mobile",),
        anchors=(Anchor(id="anchor", position=(anchor, 0.0)),),
        connections=(Connection(a="mobile", b="anchor"),),
    )
    trajectory = Trajectory(frames=(
        Frame(time=0.0, positions=((initial, 0.0),), velocities=((0.0, 0.0),)),
        # Explicit synthetic observed x; unused velocity is not fabricated as fitted evidence.
        Frame(time=1.0, positions=((label, 0.0),), velocities=((0.0, 0.0),)),
    ))
    rows = []
    for i in range(repeats):
        rows.append(ExperimentRecord(
            operation_id=f"row-{i}", index=i, experiment=experiment,
            status="failed" if all_failed else "completed",
            trajectory=None if all_failed else trajectory,
            error="simulation_failed" if all_failed else None,
        ))
    if failed:
        rows.append(ExperimentRecord(
            operation_id="failed-row", index=len(rows), experiment=experiment,
            status="failed", error="simulation_failed",
        ))
    observations = ObservationBundle(
        run_id="synthetic-own-prefix", engine_version="synthetic-reference.v1",
        engine_fingerprint="a" * 64,
        space=ExperimentSpace(
            structure=structure,
            sampling=Sampling(duration=1.0, dt=0.05, sample_interval=1.0, position_noise=noise),
            budget=12, calibration_experiments=0,
        ),
        records=tuple(rows),
    )
    actual = NativeCandidateInput(
        pool=NativeSpringPool(coefficients=nodes), config=NativeCandidateConfig(),
        observations=observations,
    )
    audit.producer += 1
    audit.requested_models += len(nodes)
    produced = produce_native_candidates(actual, attempt_id="candidate")
    return NativeEndpointBeliefInput(
        attempt_id="belief", candidate_attempt_id="candidate",
        candidate_input=actual, candidate_result=produced,
        prediction_config=NativePredictionConfig(),
        profile=EndpointBeliefProfile(discrepancy=sigma, cells=cells),
        prediction_budget=len(nodes) * repeats,
    )


def _compute(audit: Audit, actual: NativeEndpointBeliefInput | bytes) -> NativeEndpointBeliefResult:
    raw = actual if isinstance(actual, bytes) else actual.model_dump_json().encode()
    audit.belief += 1
    result = endpoint.compute_native_endpoint_belief(raw)
    # The explicit public binder adds no forward/likelihood/normalizer calls.
    bind_native_endpoint_belief_result(result.model_dump_json().encode(), raw)
    return result


def _key(actual: NativeEndpointBeliefInput, k: float, record_index: int, time: float = 1.0) -> Key:
    record = actual.candidate_input.observations.records[record_index]
    particle = record.experiment.particles[0]
    impulse = record.experiment.impulse
    return (
        k, particle.mass, actual.candidate_input.observations.space.structure.anchors[0].position[0],
        particle.position[0], particle.velocity[0], 0.0 if impulse is None else impulse.vector[0],
        time,
    )


def _finite_reference(
    audit: Audit, actual: NativeEndpointBeliefInput, result: NativeEndpointBeliefResult,
    record_property: RecordProperty,
) -> tuple[Decimal, ...]:
    oracle = audit.oracle
    with localcontext() as context:
        context.prec = 100
        sigma = binary(actual.profile.discrepancy)
        constant = -oracle.log(sigma) - oracle.log(2 * oracle.circle_constant()) / 2
        cells = actual.profile.cells
        span = binary(cells[-1].right) - binary(cells[0].left)
        logs, allowances, likelihood_errors, prior_errors = [], [], [], []
        for k, node, cell in zip(
            actual.candidate_input.pool.coefficients, result.nodes, cells, strict=True
        ):
            terms, allowance = [], Decimal(0)
            for i in result.completed_record_indices:
                record = actual.candidate_input.observations.records[i]
                assert record.trajectory is not None
                y = binary(record.trajectory.frames[-1].positions[0][0])
                reference = oracle.position(_key(actual, k, i))
                residual = y - reference
                terms.append(constant - (residual / sigma) ** 2 / 2)
                epsilon = Decimal("1e-12") + REFERENCE_ERROR
                allowance += (
                    abs(residual) * epsilon / sigma**2 + epsilon**2 / (2 * sigma**2)
                    + Decimal("1e-58")
                )
            likelihood = sum(terms, Decimal(0))
            prior = oracle.log((binary(cell.right) - binary(cell.left)) / span)
            allowance += Decimal.from_float(32 * math.ulp(float(likelihood))) + Decimal("1e-12")
            logs.append(likelihood + prior)
            allowances.append(allowance)
            likelihood_errors.append(abs(binary(node.log_likelihood) - likelihood))
            prior_errors.append(abs(binary(node.log_prior_mass) - prior))
        weights = tuple(oracle.exp(x) for x in logs)
        total = sum(weights, Decimal(0))
        log_z = oracle.log(total)
        expected_logs = tuple(x - log_z for x in logs)
        assert result.normalization is not None and result.normalization.normalizer is not None
        actual_logs = tuple(binary(cast(float, x.log_probability)) for x in result.normalization.entries)
        observed_z = (
            binary(result.normalization.normalizer.maximum_log_weight)
            + binary(result.normalization.normalizer.log_scaled_sum)
        )
        max_error = max(abs(a - b) for a, b in zip(actual_logs, expected_logs, strict=True))
        log_z_error = abs(observed_z - log_z)
        allowed = 2 * max(allowances) + Decimal("1e-12")
        record_property("endpoint_reference", json.dumps({
            "input_sha256": result.input_sha256, "nodes": len(logs), "precision": 100,
            "max_normalized_log_error": str(max_error), "log_evidence_error": str(log_z_error),
            "derived_allowed": str(allowed), "max_forward_error": str(audit.max_forward_error),
            "max_likelihood_error": str(max(likelihood_errors)),
            "max_prior_log_error": str(max(prior_errors)),
        }, sort_keys=True))
        assert audit.max_forward_error <= Decimal("1e-12")
        assert allowed <= Decimal("1e-9")
        assert max_error <= allowed and log_z_error <= allowed
        assert all(error <= limit for error, limit in zip(likelihood_errors, allowances, strict=True))
        assert max(prior_errors) <= Decimal("1e-12")
        return tuple(x / total for x in weights)


def _future(
    audit: Audit, actual: NativeEndpointBeliefInput
) -> tuple[tuple[float, ...], tuple[Decimal, ...]]:
    observed, reference = [], []
    for model in actual.candidate_result.payload.models:
        request = PredictionRequest(
            model_sha256=message_sha256(model),
            structure=actual.candidate_input.observations.space.structure,
            experiment=Experiment(particles=(ParticleInitial(
                id="mobile", position=(1.0, 0.0), mass=1.0, velocity=(0.0, 0.0)
            ),)),
            times=(0.0, 2.0), integration_dt=0.05,
        )
        audit.future += 1
        value = predict_native_spring(NativePredictionInput(
            model=model, candidate_config=actual.candidate_input.config,
            request=request, config=actual.prediction_config,
        ), attempt_id="future")
        assert value.payload.response is not None
        observed.append(value.payload.response.trajectory.frames[-1].positions[0][0])
        reference.append(audit.oracle.position((model.linear, 1.0, 0.0, 1.0, 0.0, 0.0, 2.0)))
    return tuple(observed), tuple(reference)


@pytest.mark.parametrize("case", ["zero", "small", "anchor", "mass", "impulse", "residual"])
def test_scalar_native_likelihood(case: str, audit: Audit, record_property: RecordProperty) -> None:
    k = 0.0 if case == "zero" else 1e-8 if case == "small" else 0.5
    anchor = 0.25 if case == "anchor" else 0.0
    initial = 0.75 if case == "anchor" else 1.0
    mass = 0.5 if case == "mass" else 1.0
    impulse = 0.5 if case == "impulse" else 0.0
    exact = audit.oracle.position((k, mass, anchor, initial, 0.0, impulse, 1.0))
    label = float(exact) + (0.125 if case == "residual" else 0.0)
    actual = _input(audit, (k,), (EndpointCell(left=0.0, right=1.0),),
                    label=label, anchor=anchor, initial=initial, mass=mass, impulse=impulse)
    result = _compute(audit, actual)
    assert result.status == "normalized"
    _finite_reference(audit, actual, result, record_property)
    # Typed helpers cannot bypass the raw ingress, even with copy/construction bypasses.
    with pytest.raises(ContractViolation):
        parse_native_endpoint_belief_input(cast(bytes, actual.model_copy(update={"extra": 1})))
    if case == "zero":
        schema_path = Path(__file__).resolve().parents[1] / (
            "contracts/native-endpoint-belief.schema.json"
        )
        assert json.loads(schema_path.read_text()) == native_endpoint_belief_json_schema()
        # Isolate eligibility: coherent raw/canonical input replacement, same genuine
        # candidate and numerical payload, now with insufficient forward allowance.
        replacement = actual.model_copy(update={"prediction_budget": 0})
        replacement_raw = replacement.model_dump_json().encode()
        mutation = result.model_dump(mode="json")
        mutation["input_raw_sha256"] = hashlib.sha256(replacement_raw).hexdigest()
        mutation["input_sha256"] = bounded_canonical(replacement, MAX_INPUT_BYTES)[0]
        with pytest.raises(ValueError, match="Ineligible"):
            bind_native_endpoint_belief_result(json.dumps(mutation).encode(), replacement_raw)


@pytest.mark.parametrize("case", ["unequal_prior", "boundary", "failed_and_repeated"])
def test_cell_geometry_and_full_history(
    case: str, audit: Audit, record_property: RecordProperty
) -> None:
    if case == "unequal_prior":
        edges = (0.0, 0.125, 0.25, 0.5, 1.0)
        cells = tuple(EndpointCell(left=a, right=b) for a, b in zip(edges, edges[1:], strict=False))
        nodes = tuple((c.left + c.right) / 2 for c in cells)
        actual = _input(audit, nodes, cells, label=0.0, initial=0.0)
    elif case == "boundary":
        nodes = (0.0, 0.25, 0.75, 1.0)
        cells = _grid(4)[1]
        actual = _input(audit, nodes, cells, label=1.0)
    else:
        nodes = (0.125, 0.5, 0.875)
        cells = (EndpointCell(left=0.0, right=0.25), EndpointCell(left=0.25, right=0.75),
                 EndpointCell(left=0.75, right=1.0))
        actual = _input(audit, nodes, cells, label=0.75, repeats=2, failed=True)
    result = _compute(audit, actual)
    weights = _finite_reference(audit, actual, result, record_property)
    if case == "unequal_prior":
        assert all(
            abs(w - (binary(c.right) - binary(c.left))) < Decimal("1e-90")
            for w, c in zip(weights, actual.profile.cells, strict=True)
        )
    if case == "failed_and_repeated":
        assert result.completed_record_indices == (0, 1) and result.failed_record_indices == (2,)
        assert result.predictions_requested == 6
    assert result.status == "normalized"


@pytest.fixture(scope="module")
def comparisons() -> Iterator[dict[tuple[int, float], dict[str, Any]]]:
    results: dict[tuple[int, float], dict[str, Any]] = {}
    yield results
    if len(results) != 9:
        print("ENDPOINT_COMPARISONS incomplete " + str(len(results)))
        return
    log_two = math.log(2.0)
    for count in GRIDS:
        for sigma in (0.125, 0.25):
            first, doubled = results[(count, sigma)], results[(count, 2*sigma)]
            expected = tuple(
                -log_two + 3*sse/(8*sigma*sigma) for sse in first["sse"]
            )
            difference = tuple(
                b-a for a, b in zip(first["likelihoods"], doubled["likelihoods"], strict=True)
            )
            error = max(abs(a-b) for a, b in zip(difference, expected, strict=True))
            print("ENDPOINT_SCALE_SENSITIVITY " + json.dumps({
                "nodes": count, "sigma": sigma, "double_scale_error": error,
            }, sort_keys=True))
            assert error <= 1e-9
    for sigma in SCALES:
        for coarse, fine in ((16, 64), (64, 256)):
            a, b = results[(coarse, sigma)], results[(fine, sigma)]
            grouped = tuple(math.fsum(b["weights"][4*i:4*i+4]) for i in range(coarse))
            tv = 0.5*math.fsum(abs(x-y) for x,y in zip(a["weights"], grouped, strict=True))
            # Conditional exact-oscillator cell variation plus observed finite-node
            # arithmetic checks; not a continuum certificate for arbitrary inputs.
            bound = math.tanh(a["variation"]) + math.tanh(b["variation"]) + 1e-8
            print("ENDPOINT_REFINEMENT " + json.dumps({
                "coarse": coarse, "fine": fine, "sigma": sigma,
                "coarsened_tv": tv, "conditional_bound": bound,
            }, sort_keys=True))
            assert tv <= bound


@pytest.mark.parametrize("count", GRIDS)
@pytest.mark.parametrize("sigma", SCALES)
def test_excited_refinement_and_discrepancy(
    count: int, sigma: float, audit: Audit, record_property: RecordProperty,
    comparisons: dict[tuple[int, float], dict[str, Any]],
) -> None:
    nodes, cells = _grid(count)
    ideal_y = audit.oracle.position((1.0 / 3.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))
    actual = _input(audit, nodes, cells, sigma=sigma, label=float(ideal_y), failed=True)
    result = _compute(audit, actual)
    weights = _finite_reference(audit, actual, result, record_property)
    predicted, reference = _future(audit, actual)
    assert result.normalization is not None
    ordinary_weights = tuple(math.exp(cast(float, x.log_probability)) for x in result.normalization.entries)
    mean = math.fsum(w * x for w, x in zip(ordinary_weights, predicted, strict=True))
    second = math.fsum(w * x * x for w, x in zip(ordinary_weights, predicted, strict=True))
    with localcontext() as context:
        context.prec = 100
        reference_mean = sum((w * x for w, x in zip(weights, reference, strict=True)), Decimal(0))
        reference_second = sum((w * x * x for w, x in zip(weights, reference, strict=True)), Decimal(0))
        mean_error = abs(binary(mean) - reference_mean)
        variance_error = abs(binary(second - mean * mean) - (reference_second - reference_mean**2))
        # Conservative ideal bound: |x|<=1, |y|<=1, |dx/dk|<=1/2.
        # This is conditional on the named error allowance, never a study certificate.
        radius = max(max(k - c.left, c.right - k) for k, c in zip(nodes, cells, strict=True))
        ideal_log_variation = radius / (sigma * sigma)
        record_property("endpoint_resolution", json.dumps({
            "count": count, "sigma": sigma, "label_rounding_error": str(abs(binary(float(ideal_y)) - ideal_y)),
            "ideal_log_variation_bound": ideal_log_variation,
            "mean_error": str(mean_error), "variance_error": str(variance_error),
            "interpretation": "conditional diagnostic; excess is unresolved, not proof of actual error",
        }, sort_keys=True))
        comparisons[(count, sigma)] = {
            "likelihoods": tuple(node.log_likelihood for node in result.nodes),
            "sse": tuple(
                (float(ideal_y)-audit.fitted_values[(k,1.0,0.0,1.0,0.0,0.0,1.0)])**2
                for k in nodes
            ),
            "weights": ordinary_weights, "variation": ideal_log_variation,
        }
        assert mean_error < Decimal("1e-9") and variance_error < Decimal("1e-9")
        assert result.failed_record_indices == (1,)


@pytest.fixture(scope="module")
def predictive_constants(oracle: EndpointOracle) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = 100
        sin2, cos2 = oracle.trig(2, sine=True), oracle.trig(2, sine=False)
        sin4, cos4 = oracle.trig(4, sine=True), oracle.trig(4, sine=False)
        return sin2 + (cos2 - 1) / 2, Decimal(1) / 2 + sin4 / 4 + (cos4 - 1) / 16


@pytest.mark.parametrize("count", GRIDS)
def test_unexcited_prior_future_predictive_integrals(
    count: int, audit: Audit, predictive_constants: tuple[Decimal, Decimal],
    record_property: RecordProperty,
) -> None:
    nodes, cells = _grid(count)
    actual = _input(audit, nodes, cells, label=0.0, initial=0.0)
    result = _compute(audit, actual)
    weights = _finite_reference(audit, actual, result, record_property)
    predicted, reference = _future(audit, actual)
    assert all(abs(w - Decimal(1) / count) < Decimal("1e-90") for w in weights)
    mean = math.fsum(predicted) / count
    second = math.fsum(x * x for x in predicted) / count
    with localcontext() as context:
        context.prec = 100
        exact_mean, exact_second = predictive_constants
        mean_error = abs(binary(mean) - exact_mean)
        second_error = abs(binary(second) - exact_second)
        variance_error = abs(binary(second - mean * mean) - (exact_second - exact_mean**2))
        h = Decimal(1) / count
        record_property("endpoint_continuous_predictive", json.dumps({
            "nodes": count, "mean_error": str(mean_error), "second_moment_error": str(second_error),
            "variance_error": str(variance_error), "mean_bound": str(h + Decimal("1e-11")),
            "reference_error_budget": str(REFERENCE_ERROR),
        }, sort_keys=True))
        assert max(abs(binary(a) - b) for a, b in zip(predicted, reference, strict=True)) < Decimal("1e-12")
        assert mean_error <= h + Decimal("1e-11")
        assert second_error <= 2 * h + Decimal("1e-11")
        assert variance_error <= 4 * h + h*h + Decimal("1e-10")


def test_narrow_off_grid_likelihood_is_demonstrably_underresolved(
    audit: Audit, record_property: RecordProperty
) -> None:
    nodes, cells = _grid(1024, 4.0)
    ideal = audit.oracle.position((1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))
    actual = _input(audit, nodes, cells, sigma=1e-6, label=float(ideal), failed=True)
    result = _compute(audit, actual)
    assert result.status == "normalized" and result.normalization is not None
    assert len(result.normalization.entries) == 1024
    assert result.normalization.exp_underflow_indices
    with localcontext() as context:
        context.prec = 100
        sigma = binary(actual.profile.discrepancy)
        label_error = abs(binary(float(ideal)) - ideal) + REFERENCE_ERROR
        node_error = audit.max_forward_error + REFERENCE_ERROR
        gap = Decimal(1) / 3072 - label_error - node_error
        finite_upper = -(gap / sigma)**2 / 2
        continuous_lower = audit.oracle.log(sigma / 2) - (Decimal("0.5") + label_error/sigma)**2 / 2
        record_property("endpoint_underresolution", json.dumps({
            "nodes": 1024, "sigma": str(sigma), "label_error": str(label_error),
            "observed_forward_error": str(audit.max_forward_error),
            "finite_log_kernel_evidence_upper": str(finite_upper),
            "continuous_log_kernel_evidence_lower": str(continuous_lower),
            "log_gap_lower": str(continuous_lower - finite_upper),
            "claim": "specific exact-grid counterexample plus independently checked binary64 nodes",
        }, sort_keys=True))
        assert audit.max_forward_error < Decimal("1e-12")
        assert continuous_lower - finite_upper > 50_000
        assert result.normalization.normalizer is not None
        observed_log_z = (
            binary(result.normalization.normalizer.maximum_log_weight)
            + binary(result.normalization.normalizer.log_scaled_sum)
        )
        constant = -audit.oracle.log(sigma) - audit.oracle.log(
            2*audit.oracle.circle_constant()
        )/2
        # The conservative1/6 gap bound leaves a large margin to the observed
        # binary64 evidence; this is not an arbitrary tiny absolute-log tolerance.
        assert observed_log_z - constant < finite_upper
        # No enormous-negative Decimal exponentials or fictitious fine-grid oracle.
        for k in nodes:
            reference = audit.oracle.position((k, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0))
            assert abs(reference - ideal) >= Decimal(1) / 3072 - 2 * REFERENCE_ERROR


@pytest.mark.parametrize("case", [
    "prefix", "candidate", "cell_gap", "zero_sigma", "variance_underflow",
    "noise", "no_records", "prediction_failure", "budget", "interrupt",
])
def test_exact_input_preflight_and_whole_failure(
    case: str, audit: Audit, monkeypatch: pytest.MonkeyPatch
) -> None:
    nodes, cells = _grid(3)
    actual = _input(audit, nodes, cells, failed=True, all_failed=case == "no_records",
                    noise=0.01 if case == "noise" else 0.0)
    data = actual.model_dump(mode="json")
    if case == "prefix":
        data["candidate_input"]["observations"]["records"][-1]["experiment"]["particles"][0]["position"][0] = -0.0
    elif case == "candidate":
        data["candidate_result"]["facts"]["attempt_id"] = "different"
    elif case == "cell_gap":
        data["profile"]["cells"][1]["left"] = 0.4
    elif case == "zero_sigma":
        data["profile"]["discrepancy"] = 0.0
    elif case == "variance_underflow":
        data["profile"]["discrepancy"] = 1e-300
    elif case == "budget":
        data["prediction_budget"] = 2
    elif case in {"prediction_failure", "interrupt"}:
        def fail(*args: Any, **kwargs: Any) -> Any:
            if case == "prediction_failure":
                raise ArithmeticError("declared test arithmetic")
            raise RuntimeError("unrelated interruption")
        monkeypatch.setattr(native_prediction, "_state_at_time", fail)
    raw = json.dumps(data).encode()
    if case in {"prefix", "candidate", "cell_gap", "zero_sigma"}:
        with pytest.raises((ValueError, ContractViolation)):
            _compute(audit, raw)
        assert audit.fit == audit.normalizers == 0
        return
    if case == "interrupt":
        with pytest.raises(RuntimeError, match="unrelated interruption"):
            _compute(audit, raw)
        assert audit.fit == 1 and audit.normalizers == 0
        return
    result = _compute(audit, raw)
    expected = {
        "variance_underflow": "likelihood_arithmetic", "noise": "unsupported_observation_noise",
        "no_records": "no_completed_records", "prediction_failure": "prediction_failure",
        "budget": "prediction_budget",
    }
    assert result.reason == expected[case] and not result.nodes and result.normalization is None
    if case == "prediction_failure":
        assert (result.predictions_completed, result.predictions_failed) == (0, 1)
        assert (result.frames_completed, result.frames_failed) == (0, 1)
        for frames, failed_frames in ((2, 0), (1, 0)):
            mutation = result.model_dump(mode="json")
            mutation.update(frames_completed=frames, frames_failed=failed_frames,
                            frames_unassessed=2*result.predictions_requested-frames-failed_frames)
            with pytest.raises(ContractViolation):
                parse_native_endpoint_belief_result(json.dumps(mutation).encode())
    if case in {"noise", "budget", "no_records"}:
        mutation = result.model_dump(mode="json")
        mutation.update(status="failed", reason="prior_arithmetic")
        with pytest.raises(ValueError, match="Ineligible"):
            bind_native_endpoint_belief_result(json.dumps(mutation).encode(), raw)
    if case == "variance_underflow":
        mutation = result.model_dump(mode="json")
        mutation["status"] = "rejected"
        with pytest.raises(ContractViolation):
            parse_native_endpoint_belief_result(json.dumps(mutation).encode())
