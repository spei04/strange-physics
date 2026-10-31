"""Private declared-scope exposure metadata; no extraction, resolver or comparison.

Only raw-byte entrypoints are verification boundaries. Hashing supplied part
bytes authenticates neither their producer nor the named historical inputs.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, ConfigDict, Field, model_validator

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.calibration_fixture_contracts import (
    PROTOCOL_SHA256,
    D1PhysicalHistory,
    D1QuerySignature,
    D1WorldSignature,
)
from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation

MIB = 1024**2
ROOT_BYTES = PART_BYTES = INPUT_BYTES = DIAGNOSTIC_BYTES = MIB
ROW_BYTES, ALL_PART_BYTES, ALL_INPUT_BYTES = 32 * 1024, 16 * MIB, 32 * MIB
MAX_PARTS, MAX_ROWS, MAX_PART_ROWS, MAX_INPUTS = 64, 65536, 1024, 256
CANONICAL_PROFILE = "python-json-sorted-compact-ascii-no-nan.v1"
KINDS = ("physical-world", "execution-occurrence", "design-or-analytic-material")
type Kind = Literal["physical-world", "execution-occurrence", "design-or-analytic-material"]
Hash = Annotated[str, Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
Commit = Annotated[str, Field(min_length=40, max_length=40, pattern=r"^[0-9a-f]{40}$")]


def _opaque(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value) is None:
        raise ValueError("Opaque ASCII contract ID required")
    return value


def _text(value: str, maximum: int) -> str:
    if not value or len(value.encode("utf-8")) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError("Nonempty bounded UTF-8 metadata without control characters required")
    return value


def _path(value: str) -> str:
    _text(value, 512)
    parts = value.split("/")
    if any(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", p) is None for p in parts):
        raise ValueError("Normalized relative ASCII path required")
    return value


def _locator(value: str) -> str:
    if value == "":
        return value  # The empty JSON pointer names the root value.
    return _text(value, 1024)


def _detail(value: str) -> str:
    return _text(value, 512)


def _utc(value: str) -> str:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value) is None:
        raise ValueError("Exact UTC second timestamp required")
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return value


OpaqueId = Annotated[str, Field(min_length=1, max_length=128), AfterValidator(_opaque)]
RelativePath = Annotated[str, Field(min_length=1, max_length=512), AfterValidator(_path)]
Locator = Annotated[str, Field(max_length=1024), AfterValidator(_locator)]
Detail = Annotated[str, Field(min_length=1, max_length=512), AfterValidator(_detail)]
UTCSecond = Annotated[str, Field(min_length=20, max_length=20), AfterValidator(_utc)]


class _Metadata(Message):
    model_config = ConfigDict(revalidate_instances="always")


class Reason(_Metadata):
    code: Literal[
        "extracted",
        "no-records",
        "exact-projection",
        "unsupported-format",
        "unsupported-world",
        "unsupported-query",
        "unsupported-history",
        "ambiguous-role",
        "unresolved-source",
        "unresolved-execution",
        "earlier-external-gap",
        "post-cutoff-gap",
        "source-design",
        "analytic-only",
    ]
    detail: Detail


class GitOrigin(_Metadata):
    kind: Literal["git-blob"]
    commit: Commit
    blob: Commit


class ExecutionIdentity(_Metadata):
    run_id: OpaqueId
    attempt_id: OpaqueId
    job_id: OpaqueId | None = None
    terminal: Literal["completed", "failed", "incomplete", "unknown"]


class RunOrigin(_Metadata):
    kind: Literal["run-attempt"]
    execution: ExecutionIdentity


class UnresolvedOrigin(_Metadata):
    kind: Literal["unresolved"]
    reason: Reason


Origin = Annotated[GitOrigin | RunOrigin | UnresolvedOrigin, Field(discriminator="kind")]


class InputEdge(_Metadata):
    target_input_id: OpaqueId
    locator: Locator


class InputReference(_Metadata):
    input_id: OpaqueId
    format: Literal["retained-json", "literal-source", "unsupported"]
    storage: Literal["private-evidence", "git-object"]
    relative_path: RelativePath
    byte_length: Annotated[int, Field(ge=1, le=INPUT_BYTES)]
    raw_sha256: Hash
    origin: Origin
    references: Annotated[tuple[InputEdge, ...], Field(max_length=256)] = ()

    @model_validator(mode="after")
    def storage_identity(self) -> Self:
        if (self.storage == "git-object") != isinstance(self.origin, GitOrigin):
            raise ValueError("Immutable Git objects and their exact origin must agree")
        return self


class CoverageGap(_Metadata):
    gap_id: OpaqueId
    reason: Reason


class CollectionContext(_Metadata):
    schema_version: Literal["strange-physics.d1-exposure-context.v1"] = (
        "strange-physics.d1-exposure-context.v1"
    )
    collection_id: OpaqueId
    protocol_sha256: Literal["657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"] = (
        PROTOCOL_SHA256
    )
    source_commit: Commit
    policy_sha256: Hash
    extractor_id: OpaqueId
    cutoff_utc: UTCSecond
    anchors: Annotated[tuple[OpaqueId, ...], Field(min_length=1, max_length=32)]
    inputs: Annotated[tuple[InputReference, ...], Field(min_length=1, max_length=MAX_INPUTS)]
    gaps: Annotated[tuple[CoverageGap, ...], Field(max_length=256)] = ()

    @model_validator(mode="after")
    def input_graph(self) -> Self:
        by_id = {i.input_id: i for i in self.inputs}
        if len(by_id) != len(self.inputs) or len(set(self.anchors)) != len(self.anchors):
            raise ValueError("Distinct named inputs and anchors required")
        if any(a not in by_id for a in self.anchors):
            raise ValueError("Every starting anchor must be a named input")
        if len({g.gap_id for g in self.gaps}) != len(self.gaps):
            raise ValueError("Coverage gap IDs must be unique")
        objects: dict[str, int] = {}
        for item in self.inputs:
            prior_size = objects.setdefault(item.raw_sha256, item.byte_length)
            if prior_size != item.byte_length:
                raise ValueError("One raw object digest cannot claim conflicting byte lengths")
            if any(e.target_input_id not in by_id for e in item.references):
                raise ValueError("Input edges must resolve inside the frozen input list")
        if sum(objects.values()) > ALL_INPUT_BYTES:
            raise ValueError("Distinct declared input bytes exceed the read ceiling")
        reachable = set(self.anchors)
        pending = list(self.anchors)
        while pending:
            for edge in by_id[pending.pop()].references:
                if edge.target_input_id not in reachable:
                    reachable.add(edge.target_input_id)
                    pending.append(edge.target_input_id)
        if reachable != set(by_id):
            raise ValueError("Every named input needs a declared path from a starting anchor")
        return self


class SourceBinding(_Metadata):
    input_id: OpaqueId
    raw_sha256: Hash
    locator_kind: Literal["json-pointer", "source-literal"]
    locator: Locator
    rule_id: OpaqueId
    decoded_sha256: Hash | None = None
    decoded_locator: Locator | None = None
    decoder: Literal["utf8-json-string.v1"] | None = None

    @model_validator(mode="after")
    def decoded_join(self) -> Self:
        if self.locator_kind == "json-pointer" and (
            (self.locator and not self.locator.startswith("/"))
            or re.search(r"~(?![01])", self.locator) is not None
        ):
            raise ValueError("Exact JSON pointer syntax required")
        if self.locator_kind == "source-literal" and not self.locator:
            raise ValueError("Nonempty source literal locator required")
        values = (self.decoded_sha256, self.decoded_locator, self.decoder)
        if any(v is None for v in values) and not all(v is None for v in values):
            raise ValueError("Embedded decoding requires the full byte/locator/codec binding")
        if self.decoded_locator is not None and (
            (self.decoded_locator and not self.decoded_locator.startswith("/"))
            or re.search(r"~(?![01])", self.decoded_locator) is not None
        ):
            raise ValueError("Exact decoded JSON pointer syntax required")
        return self


class Compatibility(_Metadata):
    status: Literal["compatible", "incompatible", "unknown"]
    reason: Reason
    source_indices: Annotated[
        tuple[Annotated[int, Field(ge=0, lt=8)], ...], Field(min_length=1, max_length=8)
    ]


class CompatibilitySet(_Metadata):
    world: Compatibility
    query: Compatibility
    history: Compatibility


class Projections(_Metadata):
    world: D1WorldSignature | None = None
    query: D1QuerySignature | None = None
    history: D1PhysicalHistory | None = None


class _Record(_Metadata):
    record_id: OpaqueId
    bindings: Annotated[tuple[SourceBinding, ...], Field(min_length=1, max_length=8)]
    compatibility: CompatibilitySet
    projections: Projections

    @model_validator(mode="after")
    def compatibility_provenance(self) -> Self:
        for name in ("world", "query", "history"):
            status = getattr(self.compatibility, name)
            if len(set(status.source_indices)) != len(status.source_indices) or any(
                i >= len(self.bindings) for i in status.source_indices
            ):
                raise ValueError("Compatibility must reference this row's actual source bindings")
            if (status.status == "compatible") != (getattr(self.projections, name) is not None):
                raise ValueError("Compatible projection requires its complete existing D1 codec")
        return self


class WorldRecord(_Record):
    kind: Literal["physical-world"]


class OccurrenceRecord(_Record):
    kind: Literal["execution-occurrence"]
    execution: ExecutionIdentity
    subject_locator: Locator
    roles: Annotated[
        tuple[Literal["observation-truth", "candidate", "reference", "unknown"], ...],
        Field(min_length=1, max_length=4),
    ]
    world_id: OpaqueId | None
    unresolved_world: Reason | None

    @model_validator(mode="after")
    def role_and_world(self) -> Self:
        if len(set(self.roles)) != len(self.roles) or (
            "unknown" in self.roles and len(self.roles) != 1
        ):
            raise ValueError("Distinct established roles or one explicit unknown role required")
        if (self.world_id is None) != (self.unresolved_world is not None):
            raise ValueError("Absent world needs an explicit unresolved disposition")
        return self


class MaterialRecord(_Record):
    kind: Literal["design-or-analytic-material"]
    role: Literal["analytic-only", "source-design", "fake-design", "unknown"]
    world_id: OpaqueId | None = None


Record = Annotated[WorldRecord | OccurrenceRecord | MaterialRecord, Field(discriminator="kind")]


class Part(_Metadata):
    schema_version: Literal["strange-physics.d1-exposure-part.v1"] = (
        "strange-physics.d1-exposure-part.v1"
    )
    context_sha256: Hash
    index: Annotated[int, Field(ge=0, lt=MAX_PARTS)]
    kind: Kind
    records: Annotated[tuple[Record, ...], Field(min_length=1, max_length=MAX_PART_ROWS)]

    @model_validator(mode="after")
    def role_and_rows(self) -> Self:
        if any(r.kind != self.kind for r in self.records):
            raise ValueError("Part kind must match every discriminated row")
        for record in self.records:
            bounded_canonical(record, ROW_BYTES)
        return self


class PartReference(_Metadata):
    path: RelativePath
    index: Annotated[int, Field(ge=0, lt=MAX_PARTS)]
    kind: Kind
    byte_length: Annotated[int, Field(ge=1, le=PART_BYTES)]
    raw_sha256: Hash
    row_count: Annotated[int, Field(ge=1, le=MAX_PART_ROWS)]


class InputCoverage(_Metadata):
    input_id: OpaqueId
    disposition: Literal["processed", "unsupported", "unknown"]
    row_count: Annotated[int, Field(ge=0, le=MAX_ROWS)]
    reference_edges: Annotated[int, Field(ge=0, le=256)]
    reason: Reason


class RoleCounts(_Metadata):
    physical_world: Annotated[int, Field(ge=0, le=MAX_ROWS)]
    execution_occurrence: Annotated[int, Field(ge=0, le=MAX_ROWS)]
    design_or_analytic_material: Annotated[int, Field(ge=0, le=MAX_ROWS)]


class CollectionRoot(_Metadata):
    schema_version: Literal["strange-physics.d1-exposure-collection.v1"] = (
        "strange-physics.d1-exposure-collection.v1"
    )
    canonical_profile: Literal["python-json-sorted-compact-ascii-no-nan.v1"] = (
        "python-json-sorted-compact-ascii-no-nan.v1"
    )
    context: CollectionContext
    context_sha256: Hash
    parts: Annotated[tuple[PartReference, ...], Field(max_length=MAX_PARTS)]
    coverage: Annotated[tuple[InputCoverage, ...], Field(min_length=1, max_length=MAX_INPUTS)]
    row_counts: RoleCounts
    material_authenticity: Literal["unchecked"] = "unchecked"
    historical_completeness: Literal["not-established"] = "not-established"
    overlap_conclusion: Literal["unavailable"] = "unavailable"

    @model_validator(mode="after")
    def manifest_shape(self) -> Self:
        if self.context_sha256 != hashlib.sha256(_canonical(self.context, ROOT_BYTES)).hexdigest():
            raise ValueError("Context digest must bind the exact canonical context")
        if tuple(p.index for p in self.parts) != tuple(range(len(self.parts))):
            raise ValueError("All part indices must be consecutive and ordered")
        if len({p.path for p in self.parts}) != len(self.parts):
            raise ValueError("Part paths must be unique")
        if sum(p.byte_length for p in self.parts) > ALL_PART_BYTES:
            raise ValueError("All declared part bytes must fit the fixed aggregate ceiling")
        if sum(p.row_count for p in self.parts) > MAX_ROWS:
            raise ValueError("All declared rows must fit the fixed aggregate ceiling")
        if tuple(c.input_id for c in self.coverage) != tuple(
            i.input_id for i in self.context.inputs
        ):
            raise ValueError("Exactly one ordered disposition per expected input required")
        for coverage, item in zip(self.coverage, self.context.inputs, strict=True):
            if coverage.reference_edges != len(item.references):
                raise ValueError("Repeated declared locators still count as separate edges")
        return self


def _canonical(value: Message, limit: int) -> bytes:
    bounded_canonical(value, limit)
    return json.dumps(
        value.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _parse[M: Message](raw: bytes, model: type[M], limit: int) -> M:
    if type(raw) is not bytes:
        raise ContractViolation("invalid_request", 422)
    parsed = parse_bounded_json(raw, model, max_bytes=limit, max_depth=24, max_nodes=32768)
    if raw != _canonical(parsed, limit):
        raise ContractViolation("invalid_request", 422)
    return parsed


def parse_context(raw: bytes) -> CollectionContext:
    return _parse(raw, CollectionContext, ROOT_BYTES)


def parse_root(raw: bytes) -> CollectionRoot:
    return _parse(raw, CollectionRoot, ROOT_BYTES)


def parse_part(raw: bytes) -> Part:
    return _parse(raw, Part, PART_BYTES)


@dataclass(frozen=True)
class NamedPartBytes:
    path: str
    raw: bytes


@dataclass(frozen=True)
class StructuralCollection:
    root: CollectionRoot
    parts: tuple[Part, ...]
    raw_root_sha256: str
    actual_part_bytes: int
    unique_raw_input_objects: int
    declared_distinct_input_bytes: int

    @property
    def verification_scope(self) -> Literal["supplied-all-part-structure-only"]:
        return "supplied-all-part-structure-only"

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"

    @property
    def overlap_conclusion(self) -> Literal["unavailable"]:
        return "unavailable"


def verify_collection(
    root_raw: bytes, supplied: tuple[NamedPartBytes, ...]
) -> StructuralCollection:
    """Verify every declared byte part, never a selected page or filesystem path.

    The resolver must separately prove the directory has no undeclared files and
    authenticate root/source/input custody. This function opens nothing.
    """
    root = parse_root(root_raw)
    if type(supplied) is not tuple or len(supplied) != len(root.parts):
        raise ContractViolation("invalid_request", 422)
    parts: list[Part] = []
    records: dict[str, WorldRecord | OccurrenceRecord | MaterialRecord] = {}
    input_map = {item.input_id: item for item in root.context.inputs}
    coverage = dict.fromkeys(input_map, 0)
    counts = dict.fromkeys(KINDS, 0)
    actual_bytes = 0
    for bound, actual in zip(root.parts, supplied, strict=True):
        if (
            type(actual) is not NamedPartBytes
            or type(actual.raw) is not bytes
            or type(actual.path) is not str
        ):
            raise ContractViolation("invalid_request", 422)
        if actual.path != bound.path or len(actual.raw) != bound.byte_length:
            raise ContractViolation("invalid_request", 422)
        actual_bytes += len(actual.raw)
        if (
            actual_bytes > ALL_PART_BYTES
            or hashlib.sha256(actual.raw).hexdigest() != bound.raw_sha256
        ):
            raise ContractViolation("invalid_request", 422)
        part = parse_part(actual.raw)
        if (part.context_sha256, part.index, part.kind, len(part.records)) != (
            root.context_sha256,
            bound.index,
            bound.kind,
            bound.row_count,
        ):
            raise ContractViolation("invalid_request", 422)
        for row in part.records:
            if row.record_id in records:
                raise ContractViolation("invalid_request", 422)
            records[row.record_id] = row
            counts[row.kind] += 1
            used: set[str] = set()
            for binding in row.bindings:
                source = input_map.get(binding.input_id)
                if source is None or source.raw_sha256 != binding.raw_sha256:
                    raise ContractViolation("invalid_request", 422)
                if (binding.locator_kind == "source-literal") != (
                    source.format == "literal-source"
                ):
                    raise ContractViolation("invalid_request", 422)
                used.add(binding.input_id)
            for input_id in used:
                coverage[input_id] += 1
        parts.append(part)
    for row in records.values():
        if isinstance(row, (OccurrenceRecord, MaterialRecord)) and row.world_id is not None:
            world = records.get(row.world_id)
            if (
                not isinstance(world, WorldRecord)
                or row.projections.world != world.projections.world
            ):
                raise ContractViolation("invalid_request", 422)
    expected_counts = RoleCounts(
        physical_world=counts["physical-world"],
        execution_occurrence=counts["execution-occurrence"],
        design_or_analytic_material=counts["design-or-analytic-material"],
    )
    if root.row_counts != expected_counts or any(
        c.row_count != coverage[c.input_id] for c in root.coverage
    ):
        raise ContractViolation("invalid_request", 422)
    objects = {item.raw_sha256: item.byte_length for item in root.context.inputs}
    return StructuralCollection(
        root,
        tuple(parts),
        hashlib.sha256(root_raw).hexdigest(),
        actual_bytes,
        len(objects),
        sum(objects.values()),
    )
