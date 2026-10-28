"""Bounded algebraic log-weight messages; no scientific profile or authority."""

from __future__ import annotations

import math
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.research_contracts import Digest

MAX_ENTRIES = 1_025
MAX_INPUT_BYTES = 256 * 1024
MAX_RESULT_BYTES = 256 * 1024
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 20_000
Index = Annotated[int, Field(ge=0, le=MAX_ENTRIES - 1)]
Count = Annotated[int, Field(ge=0, le=MAX_ENTRIES)]
Indices = Annotated[tuple[Index, ...], Field(max_length=MAX_ENTRIES)]
OutcomeStatus = Literal["normalized", "upstream_failure", "all_zero", "arithmetic_failure"]
FailureStage = Literal["centering", "exponential", "summation", "log_normalizer", "normalization"]


class FiniteLogWeight(Message):
    item_sha256: Digest
    kind: Literal["finite", "exact_zero", "upstream_failed"]
    log_weight: float | None

    @model_validator(mode="after")
    def value_presence(self) -> Self:
        if (self.kind == "finite") != (self.log_weight is not None):
            raise ValueError("Only a finite entry carries a log weight")
        return self


class FiniteLogWeightInput(Message):
    schema_version: Literal["strange-physics.finite-log-weight-input.v1"] = (
        "strange-physics.finite-log-weight-input.v1"
    )
    entries: Annotated[tuple[FiniteLogWeight, ...], Field(min_length=1, max_length=MAX_ENTRIES)]

    @model_validator(mode="after")
    def ordered_unique_items(self) -> Self:
        if len({entry.item_sha256 for entry in self.entries}) != len(self.entries):
            raise ValueError("Each ordered entry requires a unique correlation label")
        bounded_canonical(self, MAX_INPUT_BYTES)
        return self


class NormalizedLogWeight(Message):
    item_sha256: Digest
    kind: Literal["finite", "exact_zero"]
    log_probability: Annotated[float, Field(le=0.0)] | None

    @model_validator(mode="after")
    def value_presence(self) -> Self:
        if (self.kind == "finite") != (self.log_probability is not None):
            raise ValueError("Only a finite entry carries a normalized log weight")
        return self


class ShiftedLogNormalizer(Message):
    maximum_log_weight: float
    # log(1025) < 7. This is an algorithmic bound, not a scientific tolerance.
    log_scaled_sum: Annotated[float, Field(ge=0.0, le=7.0)]


class FiniteLogWeightResult(Message):
    schema_version: Literal["strange-physics.finite-log-weight-result.v1"] = (
        "strange-physics.finite-log-weight-result.v1"
    )
    algorithm: Literal["maximum-shift-fsum-log.v1"] = "maximum-shift-fsum-log.v1"
    input_sha256: Digest
    status: OutcomeStatus
    input_count: Annotated[int, Field(ge=1, le=MAX_ENTRIES)]
    finite_count: Count
    exact_zero_count: Count
    upstream_failed_indices: Indices
    exp_underflow_indices: Indices
    exp_evaluations: Count
    fsum_evaluations: Annotated[int, Field(ge=0, le=1)]
    log_evaluations: Annotated[int, Field(ge=0, le=1)]
    failure_stage: FailureStage | None
    failure_index: Index | None
    normalizer: ShiftedLogNormalizer | None
    entries: Annotated[tuple[NormalizedLogWeight, ...], Field(max_length=MAX_ENTRIES)]

    @model_validator(mode="after")
    def complete_outcome(self) -> Self:
        for indices in (self.upstream_failed_indices, self.exp_underflow_indices):
            if any(a >= b for a, b in zip(indices, indices[1:], strict=False)) or (
                indices and indices[-1] >= self.input_count
            ):
                raise ValueError("Diagnostic indices must be ordered, unique and in range")
        if (
            self.finite_count + self.exact_zero_count + len(self.upstream_failed_indices)
            != self.input_count
            or self.exp_evaluations > self.finite_count
            or len(self.exp_underflow_indices) > self.exp_evaluations
        ):
            raise ValueError("Counts must partition the complete input")
        if self.status == "normalized":
            if (
                self.upstream_failed_indices
                or not self.finite_count
                or self.normalizer is None
                or self.failure_stage is not None
                or self.failure_index is not None
                or len(self.entries) != self.input_count
                or len({entry.item_sha256 for entry in self.entries}) != self.input_count
                or sum(entry.kind == "finite" for entry in self.entries) != self.finite_count
                or (self.exp_evaluations, self.fsum_evaluations, self.log_evaluations)
                != (self.finite_count, 1, 1)
                or any(self.entries[i].kind != "finite" for i in self.exp_underflow_indices)
            ):
                raise ValueError("Normalization requires every ordered entry and complete work")
        else:
            if self.entries or self.normalizer is not None:
                raise ValueError("Failure cannot expose a partial normalization")
            if self.status in {"upstream_failure", "all_zero"}:
                if (
                    self.failure_stage is not None
                    or self.failure_index is not None
                    or self.exp_underflow_indices
                    or self.exp_evaluations
                    or self.fsum_evaluations
                    or self.log_evaluations
                    or (self.status == "upstream_failure" and not self.upstream_failed_indices)
                    or (
                        self.status == "all_zero"
                        and (self.finite_count or self.upstream_failed_indices)
                    )
                ):
                    raise ValueError("Input failure precedes all normalization work")
            else:
                stage = self.failure_stage
                if self.upstream_failed_indices or not self.finite_count or stage is None:
                    raise ValueError("Arithmetic failure requires usable finite input")
                indexed = stage in {"centering", "exponential", "normalization"}
                if indexed != (self.failure_index is not None) or (
                    self.failure_index is not None and self.failure_index >= self.input_count
                ):
                    raise ValueError("Only an entry-local failure carries an input index")
                counts = (self.exp_evaluations, self.fsum_evaluations, self.log_evaluations)
                if (
                    (stage == "centering" and counts != (0, 0, 0))
                    or (
                        stage == "exponential"
                        and not (1 <= counts[0] <= self.finite_count and counts[1:] == (0, 0))
                    )
                    or (stage == "summation" and counts != (self.finite_count, 1, 0))
                    or (
                        stage in {"log_normalizer", "normalization"}
                        and counts != (self.finite_count, 1, 1)
                    )
                ):
                    raise ValueError("Arithmetic failure must retain the attempted work")
        bounded_canonical(self, MAX_RESULT_BYTES)
        return self


def validate_finite_log_weight_input(actual: FiniteLogWeightInput) -> FiniteLogWeightInput:
    """Revalidate supported typed inputs after bounding their serializable fields.

    This covers ordinary instances and Pydantic construction/copy bypasses. It is
    not a sandbox for arbitrary hostile Python objects or monkeypatched classes.
    """
    if (
        type(actual) is not FiniteLogWeightInput
        or len(actual.__dict__) != 2
        or set(actual.__dict__)
        != {
            "schema_version",
            "entries",
        }
    ):
        raise ValueError("Expected a complete finite log-weight input")
    if (
        type(actual.schema_version) is not str
        or len(actual.schema_version) > 128
        or type(actual.entries) is not tuple
        or not 1 <= len(actual.entries) <= MAX_ENTRIES
    ):
        raise ValueError("Typed input exceeds its structural bounds")
    for entry in actual.entries:
        if (
            type(entry) is not FiniteLogWeight
            or len(entry.__dict__) != 3
            or set(entry.__dict__)
            != {
                "item_sha256",
                "kind",
                "log_weight",
            }
        ):
            raise ValueError("Expected complete typed log-weight entries")
        if (
            type(entry.item_sha256) is not str
            or len(entry.item_sha256) != 64
            or type(entry.kind) is not str
            or len(entry.kind) > 16
            or (
                entry.log_weight is not None
                and (type(entry.log_weight) is not float or not math.isfinite(entry.log_weight))
            )
        ):
            raise ValueError("Typed entry exceeds its structural bounds")
    return FiniteLogWeightInput.model_validate(actual.model_dump(mode="python"))


def validate_finite_log_weight_result(result: FiniteLogWeightResult) -> FiniteLogWeightResult:
    """Bound supported typed result instances before serialization and revalidation."""
    fields = (
        "schema_version",
        "algorithm",
        "input_sha256",
        "status",
        "input_count",
        "finite_count",
        "exact_zero_count",
        "upstream_failed_indices",
        "exp_underflow_indices",
        "exp_evaluations",
        "fsum_evaluations",
        "log_evaluations",
        "failure_stage",
        "failure_index",
        "normalizer",
        "entries",
    )
    if (
        type(result) is not FiniteLogWeightResult
        or len(result.__dict__) != len(fields)
        or set(result.__dict__) != set(fields)
    ):
        raise ValueError("Expected a complete finite log-weight result")
    for value in (result.schema_version, result.algorithm, result.input_sha256, result.status):
        if type(value) is not str or len(value) > 128:
            raise ValueError("Typed result metadata exceeds its structural bounds")
    for value in (
        result.input_count,
        result.finite_count,
        result.exact_zero_count,
        result.exp_evaluations,
        result.fsum_evaluations,
        result.log_evaluations,
    ):
        if type(value) is not int or not 0 <= value <= MAX_ENTRIES:
            raise ValueError("Typed result count exceeds its structural bounds")
    for indices in (result.upstream_failed_indices, result.exp_underflow_indices):
        if (
            type(indices) is not tuple
            or len(indices) > MAX_ENTRIES
            or any(type(i) is not int or not 0 <= i < MAX_ENTRIES for i in indices)
        ):
            raise ValueError("Typed result diagnostics exceed their structural bounds")
    if (
        result.failure_stage is not None
        and (type(result.failure_stage) is not str or len(result.failure_stage) > 32)
    ) or (
        result.failure_index is not None
        and (type(result.failure_index) is not int or not 0 <= result.failure_index < MAX_ENTRIES)
    ):
        raise ValueError("Typed failure metadata exceeds its structural bounds")
    if result.normalizer is not None:
        normalizer = result.normalizer
        if (
            type(normalizer) is not ShiftedLogNormalizer
            or len(normalizer.__dict__) != 2
            or set(normalizer.__dict__) != {"maximum_log_weight", "log_scaled_sum"}
            or any(
                type(value) is not float or not math.isfinite(value)
                for value in (normalizer.maximum_log_weight, normalizer.log_scaled_sum)
            )
        ):
            raise ValueError("Expected a bounded typed shifted normalizer")
    if type(result.entries) is not tuple or len(result.entries) > MAX_ENTRIES:
        raise ValueError("Typed result entries exceed their structural bounds")
    for entry in result.entries:
        if (
            type(entry) is not NormalizedLogWeight
            or len(entry.__dict__) != 3
            or set(entry.__dict__) != {"item_sha256", "kind", "log_probability"}
        ):
            raise ValueError("Expected complete typed normalized entries")
        if (
            type(entry.item_sha256) is not str
            or len(entry.item_sha256) != 64
            or type(entry.kind) is not str
            or len(entry.kind) > 16
            or (
                entry.log_probability is not None
                and (
                    type(entry.log_probability) is not float
                    or not math.isfinite(entry.log_probability)
                )
            )
        ):
            raise ValueError("Typed normalized entry exceeds its structural bounds")
    return FiniteLogWeightResult.model_validate(result.model_dump(mode="python"))


def bind_finite_log_weight_result(
    result: FiniteLogWeightResult, actual: FiniteLogWeightInput
) -> None:
    """Bind actual supplied inputs, not numerical correctness or item authenticity."""
    actual = validate_finite_log_weight_input(actual)
    result = validate_finite_log_weight_result(result)
    failed = tuple(i for i, entry in enumerate(actual.entries) if entry.kind == "upstream_failed")
    finite = tuple(i for i, entry in enumerate(actual.entries) if entry.kind == "finite")
    finite_indices = frozenset(finite)
    if (
        result.input_sha256 != bounded_canonical(actual, MAX_INPUT_BYTES)[0]
        or result.input_count != len(actual.entries)
        or result.finite_count != len(finite)
        or result.exact_zero_count != len(actual.entries) - len(failed) - len(finite)
        or result.upstream_failed_indices != failed
        or any(i not in finite_indices for i in result.exp_underflow_indices)
        or (result.failure_index is not None and result.failure_index not in finite_indices)
    ):
        raise ValueError("Result differs from the complete actual input")
    if result.status == "arithmetic_failure" and result.failure_stage == "exponential":
        # An exponential failure is the last attempted finite entry. Underflow
        # diagnostics can only describe successful calls preceding that failure.
        if (
            result.failure_index is None
            or result.exp_evaluations != finite.index(result.failure_index) + 1
            or any(i >= result.failure_index for i in result.exp_underflow_indices)
        ):
            raise ValueError("Failure diagnostics differ from the ordered exponential work")
    if result.status == "normalized":
        for entry, output in zip(actual.entries, result.entries, strict=True):
            if (entry.item_sha256, entry.kind) != (output.item_sha256, output.kind):
                raise ValueError("Result must preserve every item, zero and position")
        values = [actual.entries[i].log_weight for i in finite]
        maximum = max(value for value in values if value is not None)
        if result.normalizer is None or result.normalizer.maximum_log_weight.hex() != maximum.hex():
            raise ValueError("Normalizer must retain the exact actual maximum")


def parse_finite_log_weight_input(raw: bytes) -> FiniteLogWeightInput:
    return parse_bounded_json(
        raw,
        FiniteLogWeightInput,
        max_bytes=MAX_INPUT_BYTES,
        max_depth=MAX_JSON_DEPTH,
        max_nodes=MAX_JSON_NODES,
    )


def parse_finite_log_weight_result(raw: bytes) -> FiniteLogWeightResult:
    return parse_bounded_json(
        raw,
        FiniteLogWeightResult,
        max_bytes=MAX_RESULT_BYTES,
        max_depth=MAX_JSON_DEPTH,
        max_nodes=MAX_JSON_NODES,
    )


def finite_log_weight_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema(
        [
            (model, "validation")
            for model in (
                FiniteLogWeight,
                FiniteLogWeightInput,
                NormalizedLogWeight,
                ShiftedLogNormalizer,
                FiniteLogWeightResult,
            )
        ],
        title="Strange Physics finite log-weight normalization v1",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/finite-log-weight.schema.json"
    schema["description"] = (
        "Bounded algebraic normalization of supplied log weights. Structural validity and "
        "input binding do not authenticate production, candidate provenance or numerical "
        "correctness. No scientific profile, posterior, MAP or marginal-evidence claim."
    )
    return schema
