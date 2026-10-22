"""Native spring candidate identity contracts; no inference or numerical execution.

A selected candidate is not a fitted estimate or a proved posterior maximizer.
The actual pool and entire committed purchased prefix remain separate identities.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Identifier, Message, ObservationBundle
from strange_physics.research_contracts import Digest, LinearSpringModel, message_sha256

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_RESULT_BYTES = 4 * 1024 * 1024
NativeProducer = Literal["strange-physics.linear-spring.native-candidates.v1"]
NATIVE_PRODUCER: NativeProducer = "strange-physics.linear-spring.native-candidates.v1"
CandidateCount = Annotated[int, Field(ge=0, le=1_025)]
CandidateIndex = Annotated[int, Field(ge=0, le=1_024)]
PrefixIndex = Annotated[int, Field(ge=-1, le=11)]
RecordIndex = Annotated[int, Field(ge=0, le=11)]
LocalCount = Annotated[int, Field(ge=0, le=2**53 - 1)]


class NativeSpringPool(Message):
    """A common ordered coefficient pool, independent of any arm or purchased prefix."""

    schema_version: Literal["strange-physics.native-spring-pool.v1"] = (
        "strange-physics.native-spring-pool.v1"
    )
    model_assumption: Literal["stationary-shared-zero-rest-linear-spring.v1"] = (
        "stationary-shared-zero-rest-linear-spring.v1"
    )
    coefficients: Annotated[
        tuple[Annotated[float, Field(ge=0.0, le=4.0)], ...],
        Field(min_length=1, max_length=1_025),
    ]

    @model_validator(mode="after")
    def ordered_physical_nodes(self) -> Self:
        if any(a >= b for a, b in zip(self.coefficients, self.coefficients[1:], strict=False)):
            raise ValueError("Coefficients must be physically distinct and strictly increasing")
        return self


class NativeCandidateConfig(Message):
    """Fixed producer semantics and support caps, not a chosen grid or prior."""

    schema_version: Literal["strange-physics.native-candidate-config.v1"] = (
        "strange-physics.native-candidate-config.v1"
    )
    producer_version: NativeProducer = NATIVE_PRODUCER
    algorithm: Literal["enumerate-declared-pool.v1"] = "enumerate-declared-pool.v1"
    record_selection: Literal["all-completed-prefix.v1"] = "all-completed-prefix.v1"
    failure_policy: Literal["no-partial-candidate-set.v1"] = "no-partial-candidate-set.v1"
    max_candidates: Annotated[int, Field(ge=1_025, le=1_025)] = 1_025
    max_records: Annotated[int, Field(ge=12, le=12)] = 12
    max_input_bytes: Annotated[int, Field(ge=8_388_608, le=8_388_608)] = MAX_INPUT_BYTES
    max_result_bytes: Annotated[int, Field(ge=4_194_304, le=4_194_304)] = MAX_RESULT_BYTES
    max_json_depth: Annotated[int, Field(ge=32, le=32)] = 32
    max_json_nodes: Annotated[int, Field(ge=1_000_000, le=1_000_000)] = 1_000_000


class NativeCandidateInput(Message):
    """Actual pool/config and committed public observations; never pending reservations."""

    schema_version: Literal["strange-physics.native-candidate-input.v1"] = (
        "strange-physics.native-candidate-input.v1"
    )
    pool: NativeSpringPool
    config: NativeCandidateConfig
    observations: ObservationBundle

    @field_validator("observations")
    @classmethod
    def bound_prefix_before_serialization(cls, value: ObservationBundle) -> ObservationBundle:
        # Raw ingress is capped before decode by parse_native_candidate_input.
        # Preserve JSON-mode tuple parsing; bound the typed graph before model_dump.
        if len(value.records) > 12:
            raise ValueError("Native candidate input supports at most twelve committed records")
        if len(value.engine_version) > 128:
            raise ValueError("Native engine-version identity exceeds its character bound")
        return value

    @model_validator(mode="after")
    def canonical_byte_bound(self) -> Self:
        # The structural bounds above and CORE's finite frame/particle bounds cap
        # model_dump allocation. Incremental encoding then caps canonical bytes.
        bounded_canonical(self, self.config.max_input_bytes)
        return self


class NativeWorkFacts(Message):
    """Operation-local facts, not a ledger, timing measurement or proof of execution.

    attempt_id is an opaque ledger-issued parent-envelope correlation. Multiple
    internal operations may share it; RA-02 owns reservation, measurement and totals.
    """

    schema_version: Literal["strange-physics.native-work-facts.v1"] = (
        "strange-physics.native-work-facts.v1"
    )
    attempt_id: Identifier
    operation: Literal["candidate_production", "selection", "prediction", "preparation", "scoring"]
    producer_version: Annotated[str, Field(min_length=1, max_length=128)]
    config_sha256: Digest
    input_sha256: Digest
    observation_sha256: Digest
    model_sha256: Digest | None
    output_sha256: Digest
    unit: Literal["candidate", "frame", "probe", "selection", "preparation"]
    requested_count: LocalCount
    completed_count: LocalCount
    failed_count: LocalCount
    not_assessed_count: LocalCount
    outcome: Literal["completed", "rejected", "failed"]

    @model_validator(mode="after")
    def partition_work(self) -> Self:
        if (
            self.completed_count + self.failed_count + self.not_assessed_count
            != self.requested_count
        ):
            raise ValueError("Local work counts must partition the requested manifest")
        if self.outcome == "completed" and (self.failed_count or self.not_assessed_count):
            raise ValueError("Completed work cannot hide failed or unassessed units")
        if self.outcome == "rejected" and (self.completed_count or self.failed_count):
            raise ValueError("Preflight rejection leaves all requested work unassessed")
        if self.outcome == "failed" and not self.failed_count:
            raise ValueError("Failed work must identify at least one failed unit")
        return self


class NativeCandidateOutcome(Message):
    """A complete declared candidate set, or counted failure with no partial models."""

    schema_version: Literal["strange-physics.native-candidate-outcome.v1"] = (
        "strange-physics.native-candidate-outcome.v1"
    )
    status: Literal["produced", "rejected", "failed"]
    reason: (
        Literal[
            "no_completed_records", "unsupported_domain", "resource_limit", "candidate_construction"
        ]
        | None
    )
    pool_sha256: Digest
    observation_sha256: Digest
    producer_config_sha256: Digest
    producer_version: NativeProducer = NATIVE_PRODUCER
    through_index: PrefixIndex
    completed_record_indices: Annotated[tuple[RecordIndex, ...], Field(max_length=12)]
    failed_record_count: Annotated[int, Field(ge=0, le=12)]
    requested_candidate_count: Annotated[int, Field(ge=1, le=1_025)]
    produced_candidate_count: CandidateCount
    failed_candidate_index: CandidateIndex | None
    models: Annotated[tuple[LinearSpringModel, ...], Field(max_length=1_025)]
    inference_claim: Literal["none"] = "none"

    @field_validator("models")
    @classmethod
    def bound_model_selections(
        cls, value: tuple[LinearSpringModel, ...]
    ) -> tuple[LinearSpringModel, ...]:
        if any(len(model.fit_record_indices) > 12 for model in value):
            raise ValueError("Native model selection exceeds the purchased-prefix bound")
        return value

    @model_validator(mode="after")
    def bound_complete_outcome(self) -> Self:
        indices = self.completed_record_indices
        if (
            tuple(sorted(set(indices))) != indices
            or (indices and indices[-1] > self.through_index)
            or len(indices) + self.failed_record_count != self.through_index + 1
            or self.produced_candidate_count > self.requested_candidate_count
        ):
            raise ValueError("Candidate prefix selection and counts must agree")
        if not indices and (self.status, self.reason) != ("rejected", "no_completed_records"):
            raise ValueError("No completed records requires an explicit rejection")
        if self.reason == "no_completed_records" and indices:
            raise ValueError("Completed records cannot be reported absent")
        if self.status == "produced":
            if (
                self.reason is not None
                or self.produced_candidate_count != self.requested_candidate_count
                or len(self.models) != self.requested_candidate_count
                or self.failed_candidate_index is not None
            ):
                raise ValueError("Production requires the complete requested candidate set")
            for model in self.models:
                if (
                    model.through_index != self.through_index
                    or model.fit_record_indices != indices
                    or model.observation_sha256 != self.observation_sha256
                    or model.fitter_version != self.producer_version
                    or model.fit_config_sha256 != self.producer_config_sha256
                    or not 0 <= model.linear <= 4
                ):
                    raise ValueError("Every model must retain the native producer and exact prefix")
            if any(
                a.linear >= b.linear for a, b in zip(self.models, self.models[1:], strict=False)
            ):
                raise ValueError("Produced candidates must preserve physical node order")
        else:
            if self.models:
                raise ValueError("Rejected or failed production cannot return partial candidates")
            if self.status == "rejected":
                if (
                    self.reason
                    not in {"no_completed_records", "unsupported_domain", "resource_limit"}
                    or self.produced_candidate_count
                    or self.failed_candidate_index is not None
                ):
                    raise ValueError("Preflight rejection precedes all candidate construction")
            elif (
                self.reason != "candidate_construction"
                or self.failed_candidate_index != self.produced_candidate_count
                or self.produced_candidate_count >= self.requested_candidate_count
            ):
                raise ValueError("Construction failure follows the exact produced prefix")
        return self


class NativeCandidateResult(Message):
    """Outcome plus locally accountable identities; output hash excludes these facts."""

    schema_version: Literal["strange-physics.native-candidate-result.v1"] = (
        "strange-physics.native-candidate-result.v1"
    )
    payload: NativeCandidateOutcome
    facts: NativeWorkFacts

    @model_validator(mode="after")
    def bind_local_facts(self) -> Self:
        p, f = self.payload, self.facts
        failed = int(p.failed_candidate_index is not None)
        if (
            f.operation != "candidate_production"
            or f.producer_version != p.producer_version
            or f.unit != "candidate"
            or f.config_sha256 != p.producer_config_sha256
            or f.observation_sha256 != p.observation_sha256
            or f.model_sha256 is not None
            or f.output_sha256 != bounded_canonical(p, MAX_RESULT_BYTES)[0]
            or f.requested_count != p.requested_candidate_count
            or f.completed_count != p.produced_candidate_count
            or f.failed_count != failed
            or f.not_assessed_count
            != p.requested_candidate_count - p.produced_candidate_count - failed
            or f.outcome
            != {"produced": "completed", "rejected": "rejected", "failed": "failed"}[p.status]
        ):
            raise ValueError("Local facts must describe the exact candidate outcome")
        bounded_canonical(self, MAX_RESULT_BYTES)
        return self


def validate_native_candidate_result(
    result: NativeCandidateResult, actual_input: NativeCandidateInput, *, attempt_id: str
) -> None:
    """Bind actual inputs and every candidate, without asserting numerical inference."""
    observations = actual_input.observations
    completed = tuple(r.index for r in observations.records if r.status == "completed")
    p, f = result.payload, result.facts
    if (
        f.attempt_id != attempt_id
        or f.input_sha256 != bounded_canonical(actual_input, MAX_INPUT_BYTES)[0]
        or p.pool_sha256 != message_sha256(actual_input.pool)
        or p.producer_config_sha256 != message_sha256(actual_input.config)
        or p.observation_sha256 != bounded_canonical(observations, MAX_INPUT_BYTES)[0]
        or p.through_index != len(observations.records) - 1
        or p.completed_record_indices != completed
        or p.failed_record_count != len(observations.records) - len(completed)
        or p.requested_candidate_count != len(actual_input.pool.coefficients)
    ):
        raise ValueError("Candidate result differs from the actual pool/config/purchased prefix")
    if p.status == "produced":
        for coefficient, model in zip(actual_input.pool.coefficients, p.models, strict=True):
            expected = LinearSpringModel(
                linear=coefficient,
                through_index=len(observations.records) - 1,
                fit_record_indices=completed,
                observation_sha256=p.observation_sha256,
                fitter_version=actual_input.config.producer_version,
                fit_config_sha256=p.producer_config_sha256,
            )
            if message_sha256(model) != message_sha256(expected):
                raise ValueError(
                    "Candidate model must exactly preserve its declared node and provenance"
                )


class SelectedNativeCandidate(Message):
    """Explicit selected candidate. Posterior/argmax/tie proof belongs to RA-N02.a."""

    schema_version: Literal["strange-physics.selected-native-candidate.v1"] = (
        "strange-physics.selected-native-candidate.v1"
    )
    candidate_result_sha256: Digest
    pool_sha256: Digest
    observation_sha256: Digest
    producer_config_sha256: Digest
    candidate_index: CandidateIndex
    model: LinearSpringModel
    model_sha256: Digest
    selection_claim: Literal["selected-candidate-only"] = "selected-candidate-only"

    @model_validator(mode="after")
    def retain_model_identity(self) -> Self:
        if (
            len(self.model.fit_record_indices) > 12
            or self.model.through_index > 11
            or not 0 <= self.model.linear <= 4
            or self.model_sha256 != message_sha256(self.model)
            or self.model.observation_sha256 != self.observation_sha256
            or self.model.fit_config_sha256 != self.producer_config_sha256
            or self.model.fitter_version != NATIVE_PRODUCER
        ):
            raise ValueError("Selected model must retain its exact native identity")
        return self


def validate_selected_native_candidate(
    selected: SelectedNativeCandidate,
    result: NativeCandidateResult,
    actual_input: NativeCandidateInput,
    *,
    attempt_id: str,
) -> None:
    """Join the selected candidate to an actually bound complete production result."""
    validate_native_candidate_result(result, actual_input, attempt_id=attempt_id)
    p = result.payload
    if (
        p.status != "produced"
        or selected.candidate_index >= len(p.models)
        or selected.candidate_result_sha256 != bounded_canonical(result, MAX_RESULT_BYTES)[0]
        or selected.pool_sha256 != p.pool_sha256
        or selected.observation_sha256 != p.observation_sha256
        or selected.producer_config_sha256 != p.producer_config_sha256
        or selected.model_sha256 != message_sha256(p.models[selected.candidate_index])
    ):
        raise ValueError("Selected candidate differs from the actual complete candidate set")


def parse_native_candidate_input(raw: bytes) -> NativeCandidateInput:
    """Bound raw JSON before decode; canonical identity is separate from raw bytes."""
    return parse_bounded_json(
        raw, NativeCandidateInput, max_bytes=MAX_INPUT_BYTES, max_depth=32, max_nodes=1_000_000
    )


def parse_native_candidate_result(raw: bytes) -> NativeCandidateResult:
    """Bound stored result bytes before decoding; parsing does not prove execution."""
    return parse_bounded_json(
        raw, NativeCandidateResult, max_bytes=MAX_RESULT_BYTES, max_depth=32, max_nodes=1_000_000
    )


def native_spring_json_schema() -> JsonSchemaValue:
    """Additive native contracts; ordinary schema validation does not run binders."""
    _, schema = models_json_schema(
        [
            (m, "validation")
            for m in (
                NativeSpringPool,
                NativeCandidateConfig,
                NativeCandidateInput,
                NativeWorkFacts,
                NativeCandidateOutcome,
                NativeCandidateResult,
                SelectedNativeCandidate,
            )
        ],
        title="Strange Physics native spring candidate contracts v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-spring.schema.json"
    schema["x-contract-status"] = "candidate-api-review"
    schema["description"] = (
        "Additive native pool/prefix/model identity and local work facts. No chosen prior, "
        "posterior, MAP proof, numerical execution or study authorization. Execute semantic "
        "validators and actual-input binders; raw input requires the bounded parser."
    )
    return schema
