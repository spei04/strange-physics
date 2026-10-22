"""Pure native scoring contracts; full scoring inputs/results are evaluator-private.

Parsing or a matching hash is not proof of Journal readiness or actual execution.
The existing SCI protocol/report and independent evaluator remain unchanged.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Identifier, Message
from strange_physics.evaluation_contracts import (
    SpringEvaluationProtocol,
    SpringEvaluationResult,
    SpringPredictionSubmissions,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionConfig,
    NativePredictionResult,
)
from strange_physics.native_spring_contracts import (
    NativeCandidateInput,
    NativeCandidateResult,
    NativeWorkFacts,
    SelectedNativeCandidate,
)
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.worlds import WorldDefinition

MAX_SCORING_INPUT_BYTES = 16 * 1024 * 1024
MAX_SCORING_RESULT_BYTES = 8 * 1024 * 1024
MAX_SCORING_WORLD_BYTES = 64 * 1024
NativeScorer = Literal["strange-physics.native-spring-scoring.v1"]
NATIVE_SCORER: NativeScorer = "strange-physics.native-spring-scoring.v1"
PreparationReason = Literal[
    "candidate_mismatch",
    "candidate_unavailable",
    "selection_unavailable",
    "selection_mismatch",
    "unsupported_topology",
    "purchased_overlap",
]
ScoringReason = Literal[
    "preparation_rejected",
    "preparation_mismatch",
    "prediction_mismatch",
    "attempt_reuse",
    "world_space_mismatch",
]


class NativeScoringPolicy(Message):
    """Model-independent frozen recipe, interpreted by unchanged i1_protocol.

    The named recipe fixes all 24 public conditions, order, masses and impulses,
    41 times (i * .05), integration_dt .01, and the exact existing I1 semantics.
    No coefficient, selected candidate, purchased prefix or private world occurs
    here. Source identity separately pins the implementation of that recipe.
    """

    schema_version: Literal["strange-physics.native-scoring-policy.v1"] = (
        "strange-physics.native-scoring-policy.v1"
    )
    scorer_version: NativeScorer = NATIVE_SCORER
    probe_recipe: Literal["strange-physics.i1-spring-probes.v1"] = (
        "strange-physics.i1-spring-probes.v1"
    )
    probe_count: Annotated[int, Field(ge=24, le=24)] = 24
    frames_per_probe: Annotated[int, Field(ge=41, le=41)] = 41
    normalization_scale: Annotated[float, Field(ge=1.0, le=1.0)] = 1.0
    averaging: Literal["equal-xy-time-within-probe-then-equal-probes.v1"] = (
        "equal-xy-time-within-probe-then-equal-probes.v1"
    )
    failure_policy: Literal["unscorable-on-any-failure.v1"] = "unscorable-on-any-failure.v1"
    reference_profile: Literal["decimal80-taylor128-tail1e-60.v1"] = (
        "decimal80-taylor128-tail1e-60.v1"
    )
    overlap_policy: Literal["all-purchases-exact-condition-keys-no-redraw.v1"] = (
        "all-purchases-exact-condition-keys-no-redraw.v1"
    )
    max_input_bytes: Annotated[int, Field(ge=16_777_216, le=16_777_216)] = MAX_SCORING_INPUT_BYTES
    max_result_bytes: Annotated[int, Field(ge=8_388_608, le=8_388_608)] = MAX_SCORING_RESULT_BYTES
    max_world_bytes: Annotated[int, Field(ge=65_536, le=65_536)] = MAX_SCORING_WORLD_BYTES


class NativeEvaluationInput(Message):
    """Actual public purchased material; not proof of an actual complete Journal."""

    schema_version: Literal["strange-physics.native-evaluation-input.v1"] = (
        "strange-physics.native-evaluation-input.v1"
    )
    candidates: NativeCandidateInput
    candidate_result: NativeCandidateResult
    candidate_attempt_id: Identifier
    selected: SelectedNativeCandidate | None
    policy: NativeScoringPolicy
    prediction_config: NativePredictionConfig

    @model_validator(mode="after")
    def bounded_input(self) -> Self:
        bounded_canonical(self, MAX_SCORING_INPUT_BYTES)
        return self


class NativePreparationOutcome(Message):
    schema_version: Literal["strange-physics.native-preparation-outcome.v1"] = (
        "strange-physics.native-preparation-outcome.v1"
    )
    status: Literal["prepared", "rejected"]
    reason: PreparationReason | None
    input_sha256: Digest
    policy_sha256: Digest
    observation_sha256: Digest
    model_sha256: Digest | None
    protocol: SpringEvaluationProtocol | None
    protocol_sha256: Digest | None
    overlap_probe_index: Annotated[int, Field(ge=0, le=23)] | None
    overlap_record_index: Annotated[int, Field(ge=0, le=11)] | None

    @model_validator(mode="after")
    def presence(self) -> Self:
        if self.status == "prepared":
            if (
                self.reason is not None
                or self.protocol is None
                or self.model_sha256 is None
                or len(self.protocol.probes) != 24
                or any(len(p.request.times) != 41 for p in self.protocol.probes)
                or self.protocol.model_sha256 != self.model_sha256
                or self.protocol.normalization_scale != 1.0
                or self.protocol_sha256 != message_sha256(self.protocol)
            ):
                raise ValueError("Preparation requires the complete model-bound I1 protocol")
        elif self.reason is None or self.protocol is not None or self.protocol_sha256 is not None:
            raise ValueError("Rejected preparation returns no protocol")
        overlap = self.reason == "purchased_overlap"
        if (self.overlap_probe_index is not None) != overlap or (
            self.overlap_record_index is not None
        ) != overlap:
            raise ValueError("Only an overlap identifies its first probe and purchased record")
        return self


class NativePreparationResult(Message):
    payload: NativePreparationOutcome
    facts: NativeWorkFacts

    @model_validator(mode="after")
    def actual_facts(self) -> Self:
        p, f = self.payload, self.facts
        completed = int(p.status == "prepared")
        if (
            f.operation != "preparation"
            or f.unit != "preparation"
            or f.producer_version != NATIVE_SCORER
            or f.config_sha256 != p.policy_sha256
            or f.input_sha256 != p.input_sha256
            or f.observation_sha256 != p.observation_sha256
            or f.model_sha256 != p.model_sha256
            or f.output_sha256 != bounded_canonical(p, MAX_SCORING_RESULT_BYTES)[0]
            or (f.requested_count, f.completed_count, f.failed_count, f.not_assessed_count)
            != (1, completed, 0, 1 - completed)
            or f.outcome != ("completed" if completed else "rejected")
        ):
            raise ValueError("Preparation facts must describe the actual outcome")
        return self


class NativeProbeOutcome(Message):
    """One ordered transport outcome; invalid/missing contains no untrusted error text."""

    probe_id: Identifier
    request_sha256: Digest
    attempt_id: Identifier
    status: Literal["result", "missing", "invalid"]
    result: NativePredictionResult | None

    @model_validator(mode="after")
    def presence(self) -> Self:
        if (self.status == "result") != (self.result is not None):
            raise ValueError("Only a result entry carries an actual native prediction")
        if self.result is not None and self.result.payload.requested_frame_count != 41:
            raise ValueError("The fixed native scoring recipe requests exactly 41 frames")
        return self


class NativePredictionCollection(Message):
    """Every fixed probe retains its own expected measured-attempt identity.

    The collection is not a batch reservation or aggregate CPU measurement.
    """

    schema_version: Literal["strange-physics.native-prediction-collection.v1"] = (
        "strange-physics.native-prediction-collection.v1"
    )
    entries: Annotated[tuple[NativeProbeOutcome, ...], Field(min_length=24, max_length=24)]

    @model_validator(mode="after")
    def bounded_collection(self) -> Self:
        bounded_canonical(self, MAX_SCORING_RESULT_BYTES)
        return self


class NativeScoringInput(Message):
    """Evaluator-private actual inputs; never pass this object or its hash to a selector."""

    schema_version: Literal["strange-physics.native-scoring-input.v1"] = (
        "strange-physics.native-scoring-input.v1"
    )
    context: NativeEvaluationInput
    preparation: NativePreparationResult
    predictions: NativePredictionCollection
    world: WorldDefinition

    @field_validator("world")
    @classmethod
    def bounded_world(cls, value: WorldDefinition) -> WorldDefinition:
        # Bound free-form law metadata before model_dump/canonical serialization.
        for law in (value.initial_law, value.changed_law):
            if law is not None and (
                len(law.kind) > 64
                or len(law.parameters) > 32
                or any(len(key) > 128 for key in law.parameters)
            ):
                raise ValueError("Private law metadata exceeds the native scoring bound")
        bounded_canonical(value, MAX_SCORING_WORLD_BYTES)
        return value

    @model_validator(mode="after")
    def bounded_input(self) -> Self:
        bounded_canonical(self, MAX_SCORING_INPUT_BYTES)
        return self


class NativeScoreOutcome(Message):
    """Evaluator-private result, including private reference labels and digests.

    No eligibility or fixture accuracy threshold is applied. A poor valid score
    remains scored. Only explicit protocol/report projections can be exported
    after the study's selection/history freeze; none is online selector feedback.
    """

    schema_version: Literal["strange-physics.native-score-outcome.v1"] = (
        "strange-physics.native-score-outcome.v1"
    )
    status: Literal["evaluated", "rejected"]
    reason: ScoringReason | None
    input_sha256: Digest
    policy_sha256: Digest
    observation_sha256: Digest
    model_sha256: Digest | None
    preparation_sha256: Digest
    predictions_sha256: Digest
    submissions: SpringPredictionSubmissions | None
    evaluation: SpringEvaluationResult | None

    @model_validator(mode="after")
    def evaluation_presence(self) -> Self:
        if self.status == "rejected":
            if self.reason is None or self.submissions is not None or self.evaluation is not None:
                raise ValueError("Preflight rejection cannot claim an evaluator outcome")
        elif self.reason is not None or self.submissions is None or self.evaluation is None:
            raise ValueError("Evaluated output needs actual submissions and evaluator result")
        else:
            e = self.evaluation
            if (
                self.model_sha256 != e.diagnostics.actual_model_sha256
                or e.diagnostics.requested_probe_count != 24
                or e.diagnostics.submitted_entry_count != len(self.submissions.entries)
                or e.diagnostics.submissions_sha256 != message_sha256(self.submissions)
            ):
                raise ValueError("Evaluation must retain actual model and all 24 requested probes")
        bounded_canonical(self, MAX_SCORING_RESULT_BYTES)
        return self


class NativeScoreResult(Message):
    """Private work facts count one invocation, separate from evaluator probe diagnostics."""

    payload: NativeScoreOutcome
    facts: NativeWorkFacts

    @model_validator(mode="after")
    def actual_facts(self) -> Self:
        p, f = self.payload, self.facts
        completed = int(
            p.evaluation is not None and p.evaluation.status in {"scored", "unscorable"}
        )
        failed = int(p.evaluation is not None and not completed)
        if (
            f.operation != "scoring"
            or f.unit != "work"
            or f.producer_version != NATIVE_SCORER
            or f.config_sha256 != p.policy_sha256
            or f.input_sha256 != p.input_sha256
            or f.observation_sha256 != p.observation_sha256
            or f.model_sha256 != p.model_sha256
            or f.output_sha256 != bounded_canonical(p, MAX_SCORING_RESULT_BYTES)[0]
            or (f.requested_count, f.completed_count, f.failed_count, f.not_assessed_count)
            != (1, completed, failed, 1 - completed - failed)
            or f.outcome != ("completed" if completed else "failed" if failed else "rejected")
        ):
            raise ValueError(
                "Scoring facts must count the invocation without relabeling predictions"
            )
        bounded_canonical(self, MAX_SCORING_RESULT_BYTES)
        return self


def parse_native_evaluation_input(raw: bytes) -> NativeEvaluationInput:
    return parse_bounded_json(
        raw,
        NativeEvaluationInput,
        max_bytes=MAX_SCORING_INPUT_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )


def parse_native_scoring_input(raw: bytes) -> NativeScoringInput:
    return parse_bounded_json(
        raw,
        NativeScoringInput,
        max_bytes=MAX_SCORING_INPUT_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )


def parse_native_score_result(raw: bytes) -> NativeScoreResult:
    return parse_bounded_json(
        raw,
        NativeScoreResult,
        max_bytes=MAX_SCORING_RESULT_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )


SCORING_MODELS: tuple[type[Message], ...] = (
    NativeScoringPolicy,
    NativeEvaluationInput,
    NativePreparationOutcome,
    NativePreparationResult,
    NativeProbeOutcome,
    NativePredictionCollection,
    NativeScoringInput,
    NativeScoreOutcome,
    NativeScoreResult,
)


def native_scoring_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [(m, "validation") for m in SCORING_MODELS], title="Strange Physics pure native scoring v1"
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/native-scoring.schema.json"
    schema["description"] = (
        "Mixed-audience schema: policy/public preparation and explicitly private scoring. "
        "NativeScoringInput, NativeScoreOutcome and NativeScoreResult and their hashes are "
        "evaluator-private. Parsing/binders do not prove Journal readiness or execution."
    )
    schema["x-private-roots"] = ["NativeScoringInput", "NativeScoreOutcome", "NativeScoreResult"]
    return schema
