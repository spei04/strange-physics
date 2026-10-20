"""WEB1 bounded viewer messages; trusted evidence is not access authority.

This module validates intrinsic shapes and supplied joins only. Current identity,
transactional append, retention and complete raw-byte verification need producers.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.artifact_contracts import ArtifactRef, VerifiedArtifact
from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import ExperimentRecord, Identifier, Message
from strange_physics.control_contracts import ContractViolation, Error, ModelReceipt, RunView
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.serialization import canonical_json

MAX_SAFE = 2**53 - 1
EVENT_BYTES = 64 * 1024
BATCH_BYTES = 1024 * 1024
CHUNK_BYTES = 4 * 1024 * 1024
SCIENCE_BYTES = 4 * 1024 * 1024
PAGE_BYTES = 1024 * 1024
Number = Annotated[int, Field(strict=True, ge=0, le=MAX_SAFE)]
Watermark = Annotated[int, Field(strict=True, ge=-1, le=MAX_SAFE)]
Positive = Annotated[int, Field(strict=True, ge=1, le=MAX_SAFE)]
ExperimentIndex = Annotated[int, Field(strict=True, ge=0, le=9_999)]


def _bytes(value: Message, limit: int) -> int:
    try:
        return bounded_canonical(value, limit)[1]
    except ContractViolation:
        raise ValueError("Canonical message exceeds its reference byte bound") from None


class StreamNamespace(Message):
    workspace_id: Identifier
    run_id: Identifier
    projection_version: Literal["agent-safe.v1"] = "agent-safe.v1"
    event_schema_version: Literal["strange-physics.run-event.v1"] = "strange-physics.run-event.v1"


class WebPolicy(Message):
    """Required trusted deployment bounds; smaller limits may reject, never truncate."""

    policy_id: Identifier
    revision: Number
    max_event_bytes: Annotated[int, Field(strict=True, ge=1, le=EVENT_BYTES)]
    max_batch_bytes: Annotated[int, Field(strict=True, ge=1, le=BATCH_BYTES)]
    max_batch_events: Annotated[int, Field(strict=True, ge=1, le=100)]
    max_chunk_bytes: Annotated[int, Field(strict=True, ge=1, le=CHUNK_BYTES)]
    max_chunk_events: Annotated[int, Field(strict=True, ge=1, le=256)]
    max_page_bytes: Annotated[int, Field(strict=True, ge=1, le=PAGE_BYTES)]
    max_page_refs: Annotated[int, Field(strict=True, ge=1, le=128)]
    max_history_pages: Annotated[int, Field(strict=True, ge=1, le=10_000)]
    max_history_bytes: Positive
    max_delivery_seconds: Annotated[int, Field(strict=True, ge=1, le=86_400)]
    max_science_bytes: Annotated[int, Field(strict=True, ge=1, le=SCIENCE_BYTES)]
    max_body_batch_bytes: Annotated[int, Field(strict=True, ge=1, le=65_536)]
    cursor_ttl_seconds: Annotated[int, Field(strict=True, ge=1, le=604_800)]

    @model_validator(mode="after")
    def compatible_bounds(self) -> Self:
        if self.max_batch_bytes < self.max_event_bytes:
            raise ValueError("A batch must be able to carry its permitted event")
        return self


class ExperimentRecordRef(Message):
    """Public exact object and typed SCI identity; neither URL nor read permission."""

    operation_id: Identifier
    index: ExperimentIndex
    status: Literal["completed", "failed"]
    artifact: ArtifactRef
    record_sha256: Digest

    @model_validator(mode="after")
    def bounded_json_object(self) -> Self:
        if (
            self.artifact.media_type != "application/json"
            or not 1 <= self.artifact.size_bytes <= SCIENCE_BYTES
        ):
            raise ValueError("Scientific record requires a bounded nonempty JSON object")
        return self


class CheckpointEvent(Message):
    checkpoint_id: Identifier
    through_index: Annotated[int, Field(strict=True, ge=-1, le=9_999)]


class RunEvent(Message):
    schema_version: Literal["strange-physics.run-event.v1"] = "strange-physics.run-event.v1"
    namespace: StreamNamespace
    event_id: Identifier
    sequence: Number
    occurred_at: Number
    operation_id: Identifier | None
    type: Literal[
        "run.state_changed", "experiment.committed", "checkpoint.committed", "model.submitted"
    ]
    payload: RunView | ExperimentRecordRef | CheckpointEvent | ModelReceipt

    @model_validator(mode="after")
    def payload_identity(self) -> Self:
        expected = {
            "run.state_changed": RunView,
            "experiment.committed": ExperimentRecordRef,
            "checkpoint.committed": CheckpointEvent,
            "model.submitted": ModelReceipt,
        }
        if not isinstance(self.payload, expected[self.type]):
            raise ValueError("Event discriminator must identify its exact safe payload")
        if isinstance(self.payload, RunView) and (
            self.payload.workspace_id,
            self.payload.run_id,
        ) != (self.namespace.workspace_id, self.namespace.run_id):
            raise ValueError("Run event must bind its captured tenant and run")
        if isinstance(self.payload, ExperimentRecordRef):
            if self.operation_id != self.payload.operation_id:
                raise ValueError("Experiment event must identify its committed operation")
        if isinstance(self.payload, ModelReceipt) and self.operation_id is None:
            raise ValueError("Model event requires its completed submission operation")
        _bytes(self, EVENT_BYTES)
        return self


class EventIdentity(Message):
    namespace: StreamNamespace
    sequence: Number
    event_id: Identifier
    event_sha256: Digest

    @classmethod
    def from_event(cls, event: RunEvent) -> Self:
        return cls(
            namespace=event.namespace,
            sequence=event.sequence,
            event_id=event.event_id,
            event_sha256=message_sha256(event),
        )


class EventDelivery(Message):
    """SSE id is resume_cursor; data is this exact canonical message, not just the event."""

    event: RunEvent
    event_sha256: Digest
    resume_cursor: Identifier

    @model_validator(mode="after")
    def integrity_and_wire_bound(self) -> Self:
        if self.event_sha256 != message_sha256(self.event):
            raise ValueError("Delivery must bind actual canonical event identity")
        data_bytes = _bytes(self, EVENT_BYTES)
        overhead = len(f"id: {self.resume_cursor}\nevent: {self.event.type}\ndata: \n\n")
        if data_bytes + overhead > EVENT_BYTES:
            raise ValueError("Complete SSE frame exceeds its UTF-8 wire bound")
        return self

    def sse_bytes(self) -> bytes:
        """Deterministic wire fixture codec; not an SSE parser, server or authorization."""
        data = canonical_json(self.model_dump(mode="json"))
        return f"id: {self.resume_cursor}\nevent: {self.event.type}\ndata: {data}\n\n".encode()


class EventBatch(Message):
    deliveries: Annotated[tuple[EventDelivery, ...], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def contiguous(self) -> Self:
        events = tuple(item.event for item in self.deliveries)
        _consecutive(events)
        if len({item.resume_cursor for item in self.deliveries}) != len(self.deliveries):
            raise ValueError("Each committed delivery has a distinct opaque cursor")
        if sum(len(item.sse_bytes()) for item in self.deliveries) > BATCH_BYTES:
            raise ValueError("Concatenated SSE frames exceed the exact wire batch bound")
        return self


def _consecutive(events: tuple[RunEvent, ...]) -> None:
    first = events[0]
    if (
        len({event.event_id for event in events}) != len(events)
        or any(event.namespace != first.namespace for event in events)
        or any(event.sequence != first.sequence + index for index, event in enumerate(events))
        or any(
            left.occurred_at > right.occurred_at
            for left, right in zip(events, events[1:], strict=False)
        )
    ):
        raise ValueError("Events must have unique identities and contiguous chronological order")


class StreamHead(Message):
    """One trusted current snapshot; sequence never resets at lease or retention boundaries."""

    namespace: StreamNamespace
    committed_through_sequence: Watermark
    retained_from_sequence: Number
    last_event: EventIdentity | None
    run_revision: Number
    observed_at: Number

    @model_validator(mode="after")
    def exact_watermark(self) -> Self:
        if self.retained_from_sequence > self.committed_through_sequence + 1:
            raise ValueError("Retained boundary cannot skip an uncommitted sequence")
        if self.committed_through_sequence == -1:
            if self.last_event is not None or self.retained_from_sequence != 0:
                raise ValueError("Empty head starts at zero without inventing an event")
        elif (
            self.last_event is None
            or self.last_event.namespace != self.namespace
            or self.last_event.sequence != self.committed_through_sequence
        ):
            raise ValueError("Nonempty head must retain its exact final event identity")
        return self


class EventCursor(Message):
    """Private authenticated lookup result; possession does not authorize any read."""

    cursor_id: Identifier
    namespace: StreamNamespace
    after_sequence: Watermark
    event: EventIdentity | None
    snapshot_id: Identifier | None
    snapshot_sha256: Digest | None
    issued_at: Number
    expires_at: Number

    @model_validator(mode="after")
    def exact_position(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("Cursor must have a nonempty lifetime")
        if (self.snapshot_id is None) != (self.snapshot_sha256 is None):
            raise ValueError("Snapshot anchor requires both actual immutable identities")
        if self.after_sequence == -1:
            if self.event is not None:
                raise ValueError("Start anchor cannot invent a committed event")
        elif (
            self.event is None
            or self.event.namespace != self.namespace
            or self.event.sequence != self.after_sequence
        ):
            raise ValueError("Every nonnegative cursor retains its exact event identity")
        return self


class ReplayChunk(Message):
    schema_version: Literal["strange-physics.replay-chunk.v1"] = "strange-physics.replay-chunk.v1"
    namespace: StreamNamespace
    first_sequence: Number
    last_sequence: Number
    events: Annotated[tuple[RunEvent, ...], Field(min_length=1, max_length=256)]

    @model_validator(mode="after")
    def exact_range(self) -> Self:
        _consecutive(self.events)
        if (
            self.events[0].namespace != self.namespace
            or self.events[0].sequence != self.first_sequence
            or self.events[-1].sequence != self.last_sequence
        ):
            raise ValueError("Replay chunk must bind its exact consecutive event range")
        _bytes(self, CHUNK_BYTES)
        return self


class ReplayChunkRef(Message):
    namespace: StreamNamespace
    first_sequence: Number
    last_sequence: Number
    event_count: Annotated[int, Field(strict=True, ge=1, le=256)]
    first_event: EventIdentity
    last_event: EventIdentity
    artifact: ArtifactRef
    chunk_sha256: Digest

    @model_validator(mode="after")
    def exact_range(self) -> Self:
        if (
            self.event_count != self.last_sequence - self.first_sequence + 1
            or self.first_event.namespace != self.namespace
            or self.last_event.namespace != self.namespace
            or self.first_event.sequence != self.first_sequence
            or self.last_event.sequence != self.last_sequence
            or (self.event_count == 1 and self.first_event != self.last_event)
            or (self.event_count > 1 and self.first_event.event_id == self.last_event.event_id)
            or self.artifact.media_type != "application/json"
            or not 1 <= self.artifact.size_bytes <= CHUNK_BYTES
        ):
            raise ValueError(
                "Chunk descriptor must bind exact range, boundary identities and bytes"
            )
        return self


class HistoryPageRef(Message):
    page_id: Identifier
    page_sha256: Digest


class HistoryPage(Message):
    """Immutable bounded linked page; the root pins the first page, each page pins the next."""

    page_id: Identifier
    manifest_id: Identifier
    namespace: StreamNamespace
    through_sequence: Watermark
    page_index: Number
    first_chunk_index: Number
    chunks: Annotated[tuple[ReplayChunkRef, ...], Field(min_length=1, max_length=128)]
    next_page: HistoryPageRef | None

    @model_validator(mode="after")
    def ordered_chunks(self) -> Self:
        if (
            any(c.namespace != self.namespace for c in self.chunks)
            or self.chunks[-1].last_sequence > self.through_sequence
            or len({(c.artifact.artifact_id, c.artifact.generation) for c in self.chunks})
            != len(self.chunks)
            or any(
                right.first_sequence != left.last_sequence + 1
                for left, right in zip(self.chunks, self.chunks[1:], strict=False)
            )
            or not self.page_index <= self.first_chunk_index <= self.page_index * 128
            or not self.first_chunk_index
            <= self.chunks[0].first_sequence
            <= self.first_chunk_index * 256
            or (self.page_index == 0 and self.chunks[0].first_sequence != 0)
            or (self.next_page is not None and self.next_page.page_id == self.page_id)
            or (self.next_page is None and self.chunks[-1].last_sequence != self.through_sequence)
            or (
                self.next_page is not None
                and self.chunks[-1].last_sequence == self.through_sequence
            )
        ):
            raise ValueError("History page must preserve ordered contiguous captured coverage")
        identities = tuple(
            identity for chunk in self.chunks for identity in (chunk.first_event, chunk.last_event)
        )
        _identity_pairs(identities)
        _bytes(self, PAGE_BYTES)
        return self


def _identity_pairs(identities: tuple[EventIdentity, ...]) -> None:
    by_id: dict[str, EventIdentity] = {}
    by_sequence: dict[int, EventIdentity] = {}
    for identity in identities:
        if identity.event_id in by_id and by_id[identity.event_id] != identity:
            raise ValueError("Known event ID cannot identify a different sequence or digest")
        if identity.sequence in by_sequence and by_sequence[identity.sequence] != identity:
            raise ValueError("Known sequence cannot identify a different event or digest")
        by_id[identity.event_id] = by_sequence[identity.sequence] = identity


class HistoryManifest(Message):
    """Immutable root; full verification requires all hash-linked pages and actual chunks."""

    manifest_id: Identifier
    namespace: StreamNamespace
    run_revision: Number
    through_sequence: Watermark
    last_event: EventIdentity | None
    page_count: Annotated[int, Field(strict=True, ge=0, le=10_000)]
    chunk_count: Number
    total_chunk_bytes: Number
    first_page: HistoryPageRef | None

    @model_validator(mode="after")
    def coverage_counts(self) -> Self:
        if self.through_sequence == -1:
            if (
                self.page_count != 0
                or self.chunk_count != 0
                or self.total_chunk_bytes != 0
                or self.first_page is not None
                or self.last_event is not None
            ):
                raise ValueError("Empty captured history has no chunks, pages or event")
        elif (
            self.first_page is None
            or self.last_event is None
            or self.last_event.namespace != self.namespace
            or self.last_event.sequence != self.through_sequence
            or not 1 <= self.page_count <= self.chunk_count <= self.page_count * 128
            or not self.chunk_count <= self.through_sequence + 1 <= self.chunk_count * 256
            or not self.chunk_count <= self.total_chunk_bytes <= self.chunk_count * CHUNK_BYTES
        ):
            raise ValueError("Nonempty history requires a bounded complete-range manifest")
        return self


class HistoryPageBinding(Message):
    """One bounded manifest/page/predecessor join; it cannot certify missing earlier pages."""

    manifest: HistoryManifest
    page: HistoryPage
    previous: HistoryPage | None

    @model_validator(mode="after")
    def exact_page(self) -> Self:
        root, page, previous = self.manifest, self.page, self.previous
        actual = HistoryPageRef(page_id=page.page_id, page_sha256=message_sha256(page))
        if (
            page.manifest_id != root.manifest_id
            or page.namespace != root.namespace
            or page.through_sequence != root.through_sequence
            or page.page_index >= root.page_count
            or page.first_chunk_index + len(page.chunks) > root.chunk_count
            or (page.next_page is None) != (page.page_index == root.page_count - 1)
        ):
            raise ValueError("Page must belong to the exact captured manifest")
        if page.page_index == 0:
            if previous is not None or actual != root.first_page:
                raise ValueError("First page must match the immutable root")
        elif (
            previous is None
            or previous.manifest_id != page.manifest_id
            or previous.namespace != page.namespace
            or previous.through_sequence != page.through_sequence
            or previous.next_page != actual
            or previous.page_index + 1 != page.page_index
            or previous.first_chunk_index + len(previous.chunks) != page.first_chunk_index
            or previous.chunks[-1].last_sequence + 1 != page.chunks[0].first_sequence
        ):
            raise ValueError("Later page must bind its actual preceding hash link and coverage")
        known_pages = (page,) if previous is None else (previous, page)
        assert root.first_page is not None  # Nonempty manifest is required by the checks above.
        page_ordinals: dict[str, int] = {root.first_page.page_id: 0}
        for known_page in known_pages:
            if (
                known_page.page_id in page_ordinals
                and page_ordinals[known_page.page_id] != known_page.page_index
            ):
                raise ValueError("Known page ID cannot be reused at a different ordinal")
            page_ordinals[known_page.page_id] = known_page.page_index
            if known_page.page_index == 0 and root.first_page != HistoryPageRef(
                page_id=known_page.page_id, page_sha256=message_sha256(known_page)
            ):
                raise ValueError("Every supplied first page must bind the immutable root")
            remaining_pages = root.page_count - known_page.page_index - 1
            remaining_chunks = (
                root.chunk_count - known_page.first_chunk_index - len(known_page.chunks)
            )
            remaining_events = root.through_sequence - known_page.chunks[-1].last_sequence
            if not (
                remaining_pages <= remaining_chunks <= remaining_pages * 128
                and remaining_chunks <= remaining_events <= remaining_chunks * 256
            ):
                raise ValueError("Missing pages and chunks must admit complete nonempty coverage")
        if page.next_page is not None:
            next_id, next_index = page.next_page.page_id, page.page_index + 1
            if next_id in page_ordinals and page_ordinals[next_id] != next_index:
                raise ValueError("Next page cannot reuse a known earlier page identity")
        supplied = page.chunks if previous is None else previous.chunks + page.chunks
        if len(
            {(chunk.artifact.artifact_id, chunk.artifact.generation) for chunk in supplied}
        ) != len(supplied):
            raise ValueError("Supplied pages cannot repeat an immutable chunk object")
        assert root.last_event is not None
        _identity_pairs(
            tuple(
                identity for chunk in supplied for identity in (chunk.first_event, chunk.last_event)
            )
            + (root.last_event,)
        )
        known_bytes = sum(chunk.artifact.size_bytes for chunk in supplied)
        missing_chunks = root.chunk_count - len(supplied)
        if (
            not known_bytes + missing_chunks
            <= root.total_chunk_bytes
            <= known_bytes + missing_chunks * CHUNK_BYTES
        ):
            raise ValueError("Manifest byte total must agree with all supplied chunk evidence")
        if page.next_page is None and (
            page.first_chunk_index + len(page.chunks) != root.chunk_count
            or page.chunks[-1].last_event != root.last_event
        ):
            raise ValueError("Final page must end at the exact captured event and chunk count")
        return self


class RunSnapshot(Message):
    snapshot_id: Identifier
    namespace: StreamNamespace
    captured_at: Number
    run: RunView
    history: HistoryManifest
    resume_cursor: Identifier | None

    @model_validator(mode="after")
    def captured_identity(self) -> Self:
        if (
            (self.run.workspace_id, self.run.run_id)
            != (self.namespace.workspace_id, self.namespace.run_id)
            or self.history.namespace != self.namespace
            or self.history.run_revision != self.run.revision
            or (self.resume_cursor is None) != (self.history.through_sequence == -1)
        ):
            raise ValueError("Snapshot must capture one run revision, history and resume boundary")
        _bytes(self, PAGE_BYTES)
        return self


class SnapshotRecord(Message):
    """Trusted captured closure; later live run/head may advance without changing this record."""

    snapshot: RunSnapshot
    cursor: EventCursor | None

    @model_validator(mode="after")
    def exact_cursor(self) -> Self:
        snapshot = self.snapshot
        if snapshot.resume_cursor is None:
            if self.cursor is not None:
                raise ValueError("Empty public snapshot has no invented resume ID")
        elif (
            self.cursor is None
            or self.cursor.cursor_id != snapshot.resume_cursor
            or self.cursor.namespace != snapshot.namespace
            or self.cursor.after_sequence != snapshot.history.through_sequence
            or self.cursor.event != snapshot.history.last_event
            or self.cursor.snapshot_id != snapshot.snapshot_id
            or self.cursor.snapshot_sha256 != message_sha256(snapshot)
            or self.cursor.issued_at < snapshot.captured_at
        ):
            raise ValueError("Snapshot cursor must bind actual capture and preserved final event")
        return self


class CursorLookup(Message):
    """Partial authoritative lookup states remain representable for fail-closed recovery."""

    namespace: StreamNamespace
    requested_cursor: Identifier | None
    head: StreamHead | None
    cursor: EventCursor | None
    event: RunEvent | None
    snapshot: SnapshotRecord | None


class ReplayChunkBinding(Message):
    """Intrinsic supplied join; producers still verify actual raw bytes before typed parsing."""

    descriptor: ReplayChunkRef
    artifact: VerifiedArtifact
    chunk: ReplayChunk

    @model_validator(mode="after")
    def exact_artifact(self) -> Self:
        descriptor, catalog, chunk = self.descriptor, self.artifact.record, self.chunk
        if (
            catalog.state != "available"
            or catalog.visibility != "agent-visible"
            or (catalog.workspace_id, catalog.run_id)
            != (descriptor.namespace.workspace_id, descriptor.namespace.run_id)
            or catalog.ref != descriptor.artifact
            or chunk.namespace != descriptor.namespace
            or message_sha256(chunk) != descriptor.chunk_sha256
            or len(chunk.events) != descriptor.event_count
            or EventIdentity.from_event(chunk.events[0]) != descriptor.first_event
            or EventIdentity.from_event(chunk.events[-1]) != descriptor.last_event
        ):
            raise ValueError("Replay binding must join exact available run object and chunk")
        return self


class ExperimentRecordBinding(Message):
    """Private record/readback join, not a public response or a live read authorization."""

    event: RunEvent
    artifact: VerifiedArtifact
    record: ExperimentRecord

    @model_validator(mode="after")
    def exact_science(self) -> Self:
        ref, catalog = self.event.payload, self.artifact.record
        if not isinstance(ref, ExperimentRecordRef):
            raise ValueError("Scientific retrieval requires a committed experiment event")
        if (
            catalog.state != "available"
            or catalog.visibility != "agent-visible"
            or (catalog.workspace_id, catalog.run_id)
            != (self.event.namespace.workspace_id, self.event.namespace.run_id)
            or catalog.ref != ref.artifact
            or (self.record.operation_id, self.record.index, self.record.status)
            != (ref.operation_id, ref.index, ref.status)
            or message_sha256(self.record) != ref.record_sha256
        ):
            raise ValueError("Scientific body must match raw identity and exact typed record")
        _bytes(self.record, SCIENCE_BYTES)
        return self


class ResyncRequired(Message):
    error: Annotated[
        Error,
        Field(
            json_schema_extra={
                "properties": {
                    "code": {"const": "cursor_expired"},
                    "retryable": {"const": False},
                    "operation_id": {"type": "null"},
                }
            }
        ),
    ]
    namespace: StreamNamespace
    snapshot_route: Literal["getRunSnapshot"] = "getRunSnapshot"
    history_route: Literal["getRunHistoryPage"] = "getRunHistoryPage"
    snapshot_id: Identifier

    @model_validator(mode="after")
    def expired_error(self) -> Self:
        if (
            self.error.code != "cursor_expired"
            or self.error.retryable
            or self.error.operation_id is not None
        ):
            raise ValueError("Resync is an explicit read-only cursor expiry response")
        return self


WEB_MODELS: tuple[type[Message], ...] = (
    StreamNamespace,
    WebPolicy,
    ExperimentRecordRef,
    CheckpointEvent,
    RunEvent,
    EventIdentity,
    EventDelivery,
    EventBatch,
    StreamHead,
    EventCursor,
    ReplayChunk,
    ReplayChunkRef,
    HistoryPageRef,
    HistoryPage,
    HistoryManifest,
    RunSnapshot,
    SnapshotRecord,
    CursorLookup,
    ReplayChunkBinding,
    ExperimentRecordBinding,
    ResyncRequired,
    HistoryPageBinding,
)
PUBLIC_MODELS = (
    "StreamNamespace",
    "ExperimentRecordRef",
    "CheckpointEvent",
    "RunEvent",
    "EventIdentity",
    "EventDelivery",
    "EventBatch",
    "ReplayChunk",
    "ReplayChunkRef",
    "HistoryPageRef",
    "HistoryPage",
    "HistoryManifest",
    "RunSnapshot",
    "ResyncRequired",
)


def web_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in WEB_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/web.schema.json"
    schema["x-contract-status"] = "WEB1 API review; runtime and hosted producers pending"
    schema["x-public-models"] = list(PUBLIC_MODELS)
    schema["x-agent-safe-models"] = list(PUBLIC_MODELS)
    schema["description"] = (
        "Fetch-stream and bounded replay contracts. Private cursor/catalog/policy/readback "
        "models are trusted projections, not authority. Raw bytes and typed canonical "
        "identity differ. Parsing does not establish completeness or production readiness."
    )
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    event = definitions["RunEvent"]
    assert isinstance(event, dict)
    event["oneOf"] = [
        {"properties": {"type": {"const": kind}, "payload": {"$ref": f"#/$defs/{name}"}}}
        for kind, name in [
            ("run.state_changed", "RunView"),
            ("experiment.committed", "ExperimentRecordRef"),
            ("checkpoint.committed", "CheckpointEvent"),
            ("model.submitted", "ModelReceipt"),
        ]
    ]
    return schema
