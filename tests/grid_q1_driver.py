"""Complete fixed GRID-Q1 diagnostic, callable only by the disabled reviewed entrypoint.

No study authority, purchases, providers or scientific profile acceptance.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from functools import partial
from pathlib import Path
from typing import Annotated, Literal

from grid_q1_bounds import (
    ArithmeticEvidence,
    EndpointEvidence,
    GridPremises,
    Interval,
    certify_grid,
)
from grid_q1_evidence import (
    EXPECTED_WORK,
    REFERENCE_ENDPOINT_ERROR,
    REFERENCE_LOG_ERROR,
    Artifact,
    CaseRow,
    Comparison,
    D,
    DecimalText,
    Gate,
    GridQ1Report,
    HexFloat,
    Index,
    IntervalRow,
    OperationRow,
    Output,
    WorkCount,
    absolute_upper,
    around,
    divide,
    encoded,
    interval_row,
    minus,
    moments,
    plus,
    point,
    probabilities,
    probability_log_envelope,
    square,
    times,
    total,
)
from grid_q1_inputs import (
    COUNTS,
    HISTORIES,
    SCALES,
    Fixture,
    History,
    candidate_input,
    fixtures,
    profile,
)
from grid_q1_reference import EXPECTED, GridQ1Reference
from pydantic import Field

import strange_physics.native_endpoint_beliefs as endpoint
from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Experiment, Impulse, Message, ParticleInitial
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_endpoint_belief_contracts import (
    NativeEndpointBeliefInput,
    bind_native_endpoint_belief_result,
    parse_native_endpoint_belief_result,
)
from strange_physics.native_prediction import predict_native_spring
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionInput,
    NativePredictionResult,
    validate_native_prediction_result,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeCandidateResult,
    validate_native_candidate_result,
)
from strange_physics.research_contracts import Digest, PredictionRequest


class NodeEvidence(Message):
    index: Index
    coefficient: HexFloat
    model_sha256: Digest
    prediction_input_sha256: Digest
    prediction_result_sha256: Digest
    endpoint: HexFloat
    reference_endpoint: DecimalText
    endpoint_error_upper: DecimalText
    joint_log_weight: HexFloat
    reference_joint_log_weight: DecimalText
    native_conditioned_joint_log_weight: IntervalRow
    native_arithmetic_error_upper: DecimalText
    normalized_log_weight: HexFloat
    reference_normalized_log_weight: DecimalText
    exp_weight: HexFloat
    probability: IntervalRow


class CaseEvidence(Message):
    input: Artifact
    result: Artifact
    future: Artifact
    nodes: Annotated[tuple[NodeEvidence, ...], Field(min_length=64, max_length=1024)]
    reference_maximum_log_weight: DecimalText
    reference_shifted_log_evidence: DecimalText
    reference_arithmetic_log_allowance: Literal["1E-48"] = "1E-48"
    probability_log_ratio_upper: DecimalText
    max_native_arithmetic_error_upper: DecimalText


class FutureNode(Message):
    index: Index
    input_sha256: Digest
    result_sha256: Digest
    endpoint: HexFloat
    reference_endpoint: DecimalText
    endpoint_error_upper: DecimalText


class FutureEvidence(Message):
    candidate_input: Artifact
    candidate_result: Artifact
    nodes: Annotated[tuple[FutureNode, ...], Field(min_length=64, max_length=1024)]


class LabelEvidence(Message):
    center: DecimalText
    enclosure: IntervalRow
    recorded_x: HexFloat
    rounding_cell: IntervalRow
    absolute_rounding_error_upper: DecimalText
    reference_error: Literal["1E-60"] = "1E-60"


class FixtureEvidence(Message):
    history: History
    observation_sha256: Digest
    space_sha256: Digest
    observation: Artifact
    truth_coefficient: float | None
    terminal_velocity_semantics: Literal["unused-zero-placeholder"]


class CertificateEvidence(Message):
    evidence_sha256: Digest
    recorded_x: IntervalRow
    endpoint_log_error_upper: DecimalText
    reserve_components: tuple[DecimalText, DecimalText, DecimalText]
    actual_reserve_upper: DecimalText
    fixed_reserve_upper: DecimalText
    delta_upper: DecimalText
    tv_upper: DecimalText
    mean_upper: DecimalText
    second_moment_upper: DecimalText
    variance_upper: DecimalText
    finest_gate_applies: bool
    passed: bool
    reasons: Annotated[tuple[Annotated[str, Field(max_length=160)], ...], Field(max_length=16)]


@dataclass(frozen=True)
class Captured:
    actual: NativePredictionInput
    result: NativePredictionResult
    x: float | None


@dataclass(frozen=True)
class Mixture:
    probabilities: tuple[Interval, ...]
    mean: Interval
    second: Interval
    variance: Interval


class Counts:
    def __init__(self) -> None:
        self.rows: dict[str, list[int]] = {}

    def start(self, name: str) -> None:
        row = self.rows.setdefault(name, [0, 0])
        row[0] += 1
        if row[0] > 100_000:
            raise ValueError("Driver work ceiling")

    def finish(self, name: str) -> None:
        self.rows[name][1] += 1

    def call[T](self, name: str, fn: Callable[[], T]) -> T:
        self.start(name)
        value = fn()
        self.finish(name)
        return value

    def snapshot(self) -> tuple[WorkCount, ...]:
        return tuple(
            WorkCount(name=k, attempted=v[0], completed=v[1]) for k, v in sorted(self.rows.items())
        )


def gate(name: str, value: Decimal, limit: Decimal | None) -> Gate:
    return Gate(
        name=name,
        observed_upper=str(value),
        limit=None if limit is None else str(limit),
        passed=limit is None or value <= limit,
    )


def label(reference: GridQ1Reference, counts: Counts) -> tuple[float, LabelEvidence]:
    center = counts.call("reference_label", reference.interior_label)
    enclosure = around(center, REFERENCE_ENDPOINT_ERROR)
    value = float(center)
    exact = point(value)
    # Strictly inside the two adjacent midpoints proves one nearest rounding,
    # avoiding a tie-to-even ambiguity. All arithmetic here is outward.
    low_mid = divide(plus(point(math.nextafter(value, -math.inf)), exact), point(2))
    high_mid = divide(plus(exact, point(math.nextafter(value, math.inf))), point(2))
    if not (low_mid.upper < enclosure.lower <= enclosure.upper < high_mid.lower):
        raise ValueError("Independent label enclosure does not prove unique binary64 rounding")
    return value, LabelEvidence(
        center=str(center),
        enclosure=interval_row(enclosure),
        recorded_x=value.hex(),
        rounding_cell=interval_row(Interval(low_mid.upper, high_mid.lower)),
        absolute_rounding_error_upper=str(absolute_upper(minus(exact, enclosure))),
    )


@dataclass(frozen=True)
class NativeArithmetic:
    conditioned_joint_log_weight: Interval
    error_upper: Decimal


def native_arithmetic_bound(
    recorded: float,
    predicted: float,
    scale: float,
    gaussian: Decimal,
    log_prior: Decimal,
    joint_log_weight: float,
) -> NativeArithmetic:
    """Separate native arithmetic from endpoint error, using existing constants.

    The endpoint is the exact captured binary64 value. Both independent
    constants receive their own reference allowance; all following interval
    operations are directed. No reference, log, exp or prediction is called.
    """
    values = (recorded, predicted, scale, joint_log_weight)
    if any(type(value) is not float or not math.isfinite(value) for value in values):
        raise ValueError("Native arithmetic requires exact finite binary64 inputs")
    if (
        not 0.0 <= recorded <= 1.0
        or not -2.0 <= predicted <= 2.0
        or scale not in SCALES
        or not -32.0 <= joint_log_weight <= 4.0
    ):
        raise ValueError("Native arithmetic input exceeds the fixed finite domain")
    for value in (gaussian, log_prior):
        if not isinstance(value, Decimal) or not value.is_finite() or value.copy_abs() > D(32):
            raise ValueError("Native arithmetic requires bounded reference constants")
    residual = minus(point(recorded), point(predicted))
    denominator = times(point(2), square(point(scale)))
    penalty = divide(square(residual), denominator)
    conditioned = plus(
        minus(around(gaussian, REFERENCE_LOG_ERROR), penalty),
        around(log_prior, REFERENCE_LOG_ERROR),
    )
    error = absolute_upper(minus(point(joint_log_weight), conditioned))
    return NativeArithmetic(conditioned, error)


class Driver:
    def __init__(self, root: Path, source: str, authority: str) -> None:
        # The trusted external admission verifies the source/install and authority
        # before enabling the entrypoint. These fields retain that exact linkage.
        self.source = source
        self.authority = authority
        self.output = Output(root)
        self.counts = Counts()
        self.reference = GridQ1Reference()
        self.operations = [
            OperationRow(key="label", kind="label", status="unrun"),
            OperationRow(key="constants", kind="constants", status="unrun"),
        ]
        for h in HISTORIES:
            for n in COUNTS:
                self.operations.append(
                    OperationRow(key=f"{h}-{n}-ensemble", kind="ensemble", status="unrun")
                )
                self.operations.append(
                    OperationRow(key=f"{h}-{n}-future", kind="future", status="unrun")
                )
                for s in range(3):
                    self.operations.append(
                        OperationRow(key=f"{h}-{n}-s{s}", kind="belief", status="unrun")
                    )
        self.operations.append(
            OperationRow(key="flat-moments", kind="flat_moments", status="unrun")
        )
        self.cases: list[CaseRow] = []
        self.comparisons: list[Comparison] = []
        self.mixtures: dict[tuple[History, int, float], Mixture] = {}
        self.future_max: dict[tuple[History, int], Decimal] = {}
        self.fatal: str | None = None
        self.fatal_detail: str | None = None
        self.active: int | None = None
        # All unrun rows are durable before any reference/native operation.
        for row in self.operations:
            self.output.event(row)

    def operation[T](self, key: str, fn: Callable[[], T]) -> T:
        index = next(i for i, row in enumerate(self.operations) if row.key == key)
        row = self.operations[index]
        if row.status != "unrun" or self.active is not None:
            raise ValueError("No duplicate or overlapping operations")
        self.active = index
        self.operations[index] = OperationRow(key=row.key, kind=row.kind, status="attempted")
        self.output.event(self.operations[index])
        try:
            value = fn()
        except BaseException as error:
            self.operations[index] = OperationRow(
                key=row.key, kind=row.kind, status="failed", error_type=type(error).__name__
            )
            self.output.event(self.operations[index])
            raise
        else:
            self.operations[index] = OperationRow(key=row.key, kind=row.kind, status="completed")
            self.output.event(self.operations[index])
            return value
        finally:
            self.active = None

    def digest(self, value: Message) -> str:
        return self.counts.call("canonical_hash", lambda: bounded_canonical(value, 16 * 1024**2)[0])

    def save(self, name: str, value: Message) -> Artifact:
        raw = self.counts.call("artifact_serialization", lambda: encoded(value, 16 * 1024**2))
        return self.output.write(name + ".json", raw)

    def ensemble(
        self, fixture: Fixture, count: int
    ) -> tuple[NativeCandidateInput, NativeCandidateResult, Artifact, Artifact]:
        actual = candidate_input(fixture, count)
        attempt = f"q1-{fixture.label}-{count}-candidates"
        inp = self.save(f"{fixture.label}-{count}-candidate-input", actual)
        result = self.counts.call(
            "candidate_producer", lambda: produce_native_candidates(actual, attempt_id=attempt)
        )
        out = self.save(f"{fixture.label}-{count}-candidate-result", result)
        self.counts.call(
            "candidate_binder",
            lambda: validate_native_candidate_result(result, actual, attempt_id=attempt),
        )
        if result.payload.status != "produced" or len(result.payload.models) != count:
            raise ValueError("Candidate production did not complete the whole pool")
        return actual, result, inp, out

    def future(
        self,
        fixture: Fixture,
        count: int,
        actual: NativeCandidateInput,
        candidates: NativeCandidateResult,
        inp: Artifact,
        out: Artifact,
    ) -> tuple[tuple[float, ...], Artifact]:
        nodes: list[FutureNode] = []
        values: list[float] = []
        maximum = D(0)
        experiment = Experiment(
            particles=(ParticleInitial(id="p0", position=(1.0, 0.0), mass=1.0),),
            impulse=Impulse(particle_id="p0", vector=(0.0, 0.0)),
        )
        for index, model in enumerate(candidates.payload.models):
            request = NativePredictionInput(
                model=model,
                candidate_config=actual.config,
                config=NativePredictionConfig(),
                request=PredictionRequest(
                    model_sha256=self.digest(model),
                    structure=fixture.observations.space.structure,
                    experiment=experiment,
                    times=(0.0, 1.0),
                    integration_dt=1 / 64,
                ),
            )
            attempt = f"q1-{fixture.label}-{count}-future-{index}"
            result = self.counts.call(
                "future_prediction", partial(predict_native_spring, request, attempt_id=attempt)
            )
            self.counts.call(
                "future_binder",
                partial(validate_native_prediction_result, result, request, attempt_id=attempt),
            )
            if result.payload.status != "predicted" or result.payload.response is None:
                self.save(f"{fixture.label}-{count}-future-failure-input", request)
                self.save(f"{fixture.label}-{count}-future-failure-result", result)
                raise ValueError("Future prediction failed; no survivor mixture")
            observed = result.payload.response.trajectory.frames[-1].positions[0][0]
            ref = self.counts.call(
                "reference_future", partial(self.reference.future, fixture.label, count, index)
            )
            error = absolute_upper(minus(point(observed), point(ref)))
            maximum = max(maximum, error)
            values.append(observed)
            nodes.append(
                FutureNode(
                    index=index,
                    input_sha256=self.digest(request),
                    result_sha256=self.digest(result),
                    endpoint=observed.hex(),
                    reference_endpoint=str(ref),
                    endpoint_error_upper=str(error),
                )
            )
        self.future_max[(fixture.label, count)] = maximum
        artifact = self.save(
            f"{fixture.label}-{count}-future",
            FutureEvidence(candidate_input=inp, candidate_result=out, nodes=tuple(nodes)),
        )
        return tuple(values), artifact

    def belief(
        self,
        fixture: Fixture,
        count: int,
        scale: float,
        actual: NativeCandidateInput,
        candidates: NativeCandidateResult,
        future: tuple[float, ...],
        future_artifact: Artifact,
    ) -> None:
        si = SCALES.index(scale)
        key = f"{fixture.label}-{count}-s{si}"
        attempt = "q1-" + key
        request = NativeEndpointBeliefInput(
            attempt_id=attempt,
            candidate_attempt_id=f"q1-{fixture.label}-{count}-candidates",
            candidate_input=actual,
            candidate_result=candidates,
            prediction_config=NativePredictionConfig(),
            profile=profile(count, scale),
            prediction_budget=count,
        )
        raw = self.counts.call("belief_input_serialization", lambda: encoded(request, 16 * 1024**2))
        input_artifact = self.output.write(key + "-input.json", raw)
        captured: list[Captured] = []
        original = predict_native_spring
        namespace = vars(endpoint)
        if namespace["predict_native_spring"] is not original:
            raise ValueError("Unexpected prediction callback before diagnostic")

        candidate_config = actual.config

        def observe(actual: NativePredictionInput, *, attempt_id: str) -> NativePredictionResult:
            index = len(captured)
            if (
                index >= count
                or attempt_id != attempt
                or actual.model != candidates.payload.models[index]
            ):
                raise ValueError("Training call is outside ordered bound input")
            record = fixture.observations.records[0]
            expected = NativePredictionInput(
                model=candidates.payload.models[index],
                candidate_config=candidate_config,
                config=request.prediction_config,
                request=PredictionRequest(
                    model_sha256=self.digest(candidates.payload.models[index]),
                    structure=fixture.observations.space.structure,
                    experiment=record.experiment,
                    times=(0.0, 0.5),
                    integration_dt=1 / 64,
                ),
            )
            if actual != expected:
                raise ValueError("Training predictor received a different full request")
            result = self.counts.call(
                "training_prediction", lambda: predict_native_spring(actual, attempt_id=attempt_id)
            )
            # The native predictor and endpoint producer already bind their calls.
            # This additional explicit observer join is counted separately.
            self.counts.call(
                "training_observer_binder",
                lambda: validate_native_prediction_result(result, actual, attempt_id=attempt_id),
            )
            x = None
            if result.payload.response is not None and result.payload.status == "predicted":
                x = result.payload.response.trajectory.frames[-1].positions[0][0]
            captured.append(Captured(actual, result, x))
            return result

        namespace["predict_native_spring"] = observe
        try:
            result = self.counts.call(
                "belief_compute", lambda: endpoint.compute_native_endpoint_belief(raw)
            )
        finally:
            namespace["predict_native_spring"] = original
        result_raw = self.counts.call(
            "belief_result_serialization", lambda: encoded(result, 4 * 1024**2)
        )
        result_artifact = self.output.write(key + "-result.json", result_raw)
        self.counts.call(
            "belief_raw_binder", lambda: bind_native_endpoint_belief_result(result_raw, raw)
        )
        parsed = self.counts.call(
            "belief_result_parser", lambda: parse_native_endpoint_belief_result(result_raw)
        )
        if parsed != result or result.status != "normalized" or len(captured) != count:
            raise ValueError("Whole bound belief did not normalize")
        normal = result.normalization
        if normal is None or normal.normalizer is None or result.normalizer_input is None:
            raise ValueError("Missing finite normalization material")
        self.counts.start("normalizer_results")
        if (
            normal.exp_evaluations != count
            or normal.log_evaluations != 1
            or normal.exp_underflow_indices
        ):
            raise ValueError("Unexpected normalizer work/underflow")
        self.counts.finish("normalizer_results")
        constants = self.counts.call("reference_constants_cached", self.reference.constants)
        record = fixture.observations.records[0]
        if record.trajectory is None:
            raise ValueError("Missing complete observation")
        recorded = record.trajectory.frames[-1].positions[0][0]
        refs: list[Decimal] = []
        joint: list[Decimal] = []
        max_training = D(0)
        for index, item in enumerate(captured):
            if item.x is None:
                raise ValueError("Normalized belief retained a failed training forward")
            if self.digest(item.result) != result.prediction_result_sha256[index]:
                raise ValueError("Captured predictor result differs from retained belief hash")
            ref = self.counts.call(
                "reference_training",
                partial(self.reference.training, fixture.label, count, scale, index),
            )
            refs.append(ref)
            max_training = max(max_training, absolute_upper(minus(point(item.x), point(ref))))
            with localcontext(Context(prec=100)) as context:
                context.prec = 100
                residual = D.from_float(recorded) - ref
                joint.append(
                    constants.gaussian[si]
                    - residual * residual / (2 * D.from_float(scale) ** 2)
                    + constants.log_prior[COUNTS.index(count)]
                )
        reference = self.counts.call(
            "reference_normalization",
            lambda: self.reference.normalize(fixture.label, count, scale, tuple(joint)),
        )
        norm_logs = tuple(entry.log_probability for entry in normal.entries)
        if any(value is None for value in norm_logs):
            raise ValueError("Every declared finite node requires a normalized log weight")
        weights: list[float] = []
        actual_logs: list[float] = []
        for value in norm_logs:
            if value is None:
                raise ValueError("Missing finite log")
            actual_logs.append(value)
            weights.append(self.counts.call("probability_exp", partial(math.exp, value)))
        probs = probabilities(tuple(weights))
        mixture = moments(probs, future)
        ratio = probability_log_envelope(probs, reference.probabilities)
        node_error = D(0)
        log_error = D(0)
        max_native_arithmetic = D(0)
        nodes: list[NodeEvidence] = []
        for i, (item, ref, target, logp, p) in enumerate(
            zip(captured, refs, joint, actual_logs, probs, strict=True)
        ):
            if item.x is None:
                raise ValueError("Missing complete training endpoint")
            entry = result.normalizer_input.entries[i]
            if entry.log_weight is None:
                raise ValueError("Missing finite joint log weight")
            native_x = item.x
            executed_joint = entry.log_weight
            native_arithmetic = self.counts.call(
                "native_arithmetic_bound",
                partial(
                    native_arithmetic_bound,
                    recorded,
                    native_x,
                    scale,
                    constants.gaussian[si],
                    constants.log_prior[COUNTS.index(count)],
                    executed_joint,
                ),
            )
            max_native_arithmetic = max(max_native_arithmetic, native_arithmetic.error_upper)
            node_error = max(
                node_error,
                absolute_upper(minus(point(entry.log_weight), around(target, REFERENCE_LOG_ERROR))),
            )
            log_error = max(
                log_error,
                absolute_upper(
                    minus(point(logp), around(reference.normalized_logs[i], REFERENCE_LOG_ERROR))
                ),
            )
            nodes.append(
                NodeEvidence(
                    index=i,
                    coefficient=actual.pool.coefficients[i].hex(),
                    model_sha256=result.nodes[i].model_sha256,
                    prediction_input_sha256=self.digest(item.actual),
                    prediction_result_sha256=self.digest(item.result),
                    endpoint=item.x.hex(),
                    reference_endpoint=str(ref),
                    endpoint_error_upper=str(absolute_upper(minus(point(item.x), point(ref)))),
                    joint_log_weight=entry.log_weight.hex(),
                    reference_joint_log_weight=str(target),
                    native_conditioned_joint_log_weight=interval_row(
                        native_arithmetic.conditioned_joint_log_weight
                    ),
                    native_arithmetic_error_upper=str(native_arithmetic.error_upper),
                    normalized_log_weight=logp.hex(),
                    reference_normalized_log_weight=str(reference.normalized_logs[i]),
                    exp_weight=weights[i].hex(),
                    probability=interval_row(p),
                )
            )
        # Compare the centered normalizer, preserving maximum and scaled log sum.
        shift_error = absolute_upper(
            minus(
                point(normal.normalizer.log_scaled_sum),
                around(reference.shifted_log_evidence, REFERENCE_LOG_ERROR),
            )
        )
        evidence = self.save(
            key + "-evidence",
            CaseEvidence(
                input=input_artifact,
                result=result_artifact,
                future=future_artifact,
                nodes=tuple(nodes),
                reference_maximum_log_weight=str(reference.maximum_log_weight),
                reference_shifted_log_evidence=str(reference.shifted_log_evidence),
                probability_log_ratio_upper=str(ratio),
                max_native_arithmetic_error_upper=str(max_native_arithmetic),
            ),
        )
        coverage = tuple(range(count))
        certificate = self.counts.call(
            "certificate",
            lambda: certify_grid(
                GridPremises(
                    history=fixture.label,
                    count=count,
                    scale=D.from_float(scale),
                    recorded_x=point(recorded),
                    training=EndpointEvidence(
                        max_training, REFERENCE_ENDPOINT_ERROR, coverage, coverage, ()
                    ),
                    future=EndpointEvidence(
                        self.future_max[(fixture.label, count)],
                        REFERENCE_ENDPOINT_ERROR,
                        coverage,
                        coverage,
                        (),
                    ),
                    arithmetic=ArithmeticEvidence(
                        node_error, max_native_arithmetic, shift_error, log_error, ratio
                    ),
                    evidence_sha256=evidence.sha256,
                )
            ),
        )
        cert = self.save(
            key + "-certificate",
            CertificateEvidence(
                evidence_sha256=evidence.sha256,
                recorded_x=interval_row(point(recorded)),
                endpoint_log_error_upper=str(certificate.endpoint_log_error_upper),
                reserve_components=(
                    str(certificate.reserve_components[0]),
                    str(certificate.reserve_components[1]),
                    str(certificate.reserve_components[2]),
                ),
                actual_reserve_upper=str(certificate.actual_reserve_upper),
                fixed_reserve_upper=str(certificate.fixed_reserve_upper),
                delta_upper=str(certificate.delta_upper),
                tv_upper=str(certificate.tv_upper),
                mean_upper=str(certificate.mean_upper),
                second_moment_upper=str(certificate.second_moment_upper),
                variance_upper=str(certificate.variance_upper),
                finest_gate_applies=certificate.finest_gate_applies,
                passed=certificate.passed,
                reasons=certificate.reasons,
            ),
        )
        gates = [
            gate("training_endpoint", max_training, D("1e-12")),
            gate("future_endpoint", self.future_max[(fixture.label, count)], D("1e-12")),
            gate("node_log", node_error, D("1e-9")),
            gate("centered_log_evidence", shift_error, D("1e-9")),
            gate("normalized_log", log_error, D("1e-9")),
            *(
                gate(f"reserve-{i}", value, D("1e-9"))
                for i, value in enumerate(certificate.reserve_components)
            ),
            gate("cell_tv_bound", certificate.delta_upper, D(".0081") if count == 1024 else None),
            gate(
                "continuous_mean_bound",
                certificate.mean_upper,
                D(".018") if count == 1024 else None,
            ),
            gate(
                "continuous_second_bound",
                certificate.second_moment_upper,
                D(".019") if count == 1024 else None,
            ),
            gate(
                "continuous_variance_bound",
                certificate.variance_upper,
                D(".056") if count == 1024 else None,
            ),
        ]
        if certificate.passed != all(g.passed for g in gates):
            raise ValueError("Certificate and driver fixed gates disagree")
        boundary = plus(total(probs[: count // 4]), total(probs[-count // 4 :]))
        self.mixtures[(fixture.label, count, scale)] = Mixture(
            probs, mixture[0], mixture[1], mixture[2]
        )
        self.cases.append(
            CaseRow(
                history=fixture.label,
                count=count,
                scale=scale,
                evidence=evidence,
                certificate=cert,
                mean=interval_row(mixture[0]),
                second_moment=interval_row(mixture[1]),
                variance=interval_row(mixture[2]),
                boundary_mass=interval_row(boundary),
                gates=tuple(gates),
                passed=all(g.passed for g in gates),
            )
        )

    def comparisons_and_flat(self) -> None:
        flat = self.counts.call("reference_flat_moments", self.reference.flat_continuous_moments)
        # Amend completed flat cases with the independent continuous moment gates.
        for i, row in enumerate(self.cases):
            if row.history != "flat":
                continue
            mixture = self.mixtures[(row.history, row.count, row.scale)]
            delta = next(g.observed_upper for g in row.gates if g.name == "continuous_mean_bound")
            second = next(
                g.observed_upper for g in row.gates if g.name == "continuous_second_bound"
            )
            extra = (
                gate(
                    "flat_exact_mean",
                    absolute_upper(minus(mixture.mean, around(flat[0], D("4e-60")))),
                    D(delta),
                ),
                gate(
                    "flat_exact_second",
                    absolute_upper(minus(mixture.second, around(flat[1], D("4e-60")))),
                    D(second),
                ),
            )
            self.cases[i] = CaseRow(
                **(
                    row.model_dump()
                    | {
                        "gates": row.gates + extra,
                        "passed": row.passed and all(g.passed for g in extra),
                    }
                )
            )
        for h in HISTORIES:
            for s in SCALES:
                for coarse, fine in ((64, 256), (256, 1024)):
                    a = self.mixtures[(h, coarse, s)]
                    b = self.mixtures[(h, fine, s)]
                    grouped = tuple(total(b.probabilities[i : i + 4]) for i in range(0, fine, 4))
                    distance = divide(
                        total(
                            tuple(
                                point(absolute_upper(minus(x, y)))
                                for x, y in zip(a.probabilities, grouped, strict=True)
                            )
                        ),
                        point(2),
                    ).upper
                    required = coarse == 256
                    self.comparisons.append(
                        Comparison(
                            key=f"{h}-{s}-{coarse}-{fine}",
                            kind="refinement",
                            gates=(
                                gate("cell_tv", distance, D(".001") if required else None),
                                gate(
                                    "mean",
                                    absolute_upper(minus(a.mean, b.mean)),
                                    D(".0005") if required else None,
                                ),
                                gate(
                                    "variance",
                                    absolute_upper(minus(a.variance, b.variance)),
                                    D(".001") if required else None,
                                ),
                            ),
                        )
                    )
            for n in COUNTS:
                for s0, s1 in ((0.125, 0.25), (0.25, 0.5)):
                    a, b = self.mixtures[(h, n, s0)], self.mixtures[(h, n, s1)]
                    distance = divide(
                        total(
                            tuple(
                                point(absolute_upper(minus(x, y)))
                                for x, y in zip(a.probabilities, b.probabilities, strict=True)
                            )
                        ),
                        point(2),
                    ).upper
                    self.comparisons.append(
                        Comparison(
                            key=f"{h}-{n}-{s0}-{s1}",
                            kind="sensitivity",
                            gates=(
                                gate("cell_tv", distance, None),
                                gate("mean", absolute_upper(minus(a.mean, b.mean)), None),
                                gate(
                                    "variance", absolute_upper(minus(a.variance, b.variance)), None
                                ),
                            ),
                        )
                    )

    def run(self) -> bool:
        try:
            value, label_evidence = self.operation(
                "label", lambda: label(self.reference, self.counts)
            )
            self.save("label", label_evidence)
            fixtures_ = fixtures(value)
            self.operation(
                "constants",
                lambda: self.counts.call("reference_constants", self.reference.constants),
            )
            for fixture in fixtures_:
                obs = self.save(fixture.label + "-observations", fixture.observations)
                self.save(
                    fixture.label + "-fixture",
                    FixtureEvidence(
                        history=fixture.label,
                        observation_sha256=self.digest(fixture.observations),
                        space_sha256=self.digest(fixture.observations.space),
                        observation=obs,
                        truth_coefficient=fixture.truth_coefficient,
                        terminal_velocity_semantics=fixture.terminal_velocity_semantics,
                    ),
                )
                for n in COUNTS:
                    actual, candidates, inp, out = self.operation(
                        f"{fixture.label}-{n}-ensemble", partial(self.ensemble, fixture, n)
                    )
                    future, future_artifact = self.operation(
                        f"{fixture.label}-{n}-future",
                        partial(self.future, fixture, n, actual, candidates, inp, out),
                    )
                    for si, s in enumerate(SCALES):
                        self.operation(
                            f"{fixture.label}-{n}-s{si}",
                            partial(
                                self.belief,
                                fixture,
                                n,
                                s,
                                actual,
                                candidates,
                                future,
                                future_artifact,
                            ),
                        )
            self.operation("flat-moments", self.comparisons_and_flat)
            self.reference.require_complete()
            for key, expected_count in EXPECTED_WORK.items():
                if self.counts.rows.get(key) != [expected_count, expected_count]:
                    raise ValueError("Driver work census mismatch: " + key)
            if self.reference.census() != EXPECTED:
                raise ValueError("Reference census mismatch")
        except BaseException as error:
            self.fatal = type(error).__name__
            self.fatal_detail = str(error)[:240]
        outcome: Literal["passed", "failed", "incomplete"]
        if self.fatal:
            outcome = "incomplete"
        elif all(c.passed for c in self.cases) and all(
            g.passed for c in self.comparisons for g in c.gates
        ):
            outcome = "passed"
        else:
            outcome = "failed"
        report = GridQ1Report(
            source_commit=self.source,
            authority_sha256=self.authority,
            outcome=outcome,
            operations=tuple(self.operations),
            cases=tuple(self.cases),
            comparisons=tuple(self.comparisons),
            work=self.counts.snapshot(),
            reference_census=self.reference.census(),
            artifacts=tuple(self.output.artifacts),
            fatal_type=self.fatal,
            fatal_detail=self.fatal_detail,
        )
        self.output.finish(report)
        return outcome == "passed"
