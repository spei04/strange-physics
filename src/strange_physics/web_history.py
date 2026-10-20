"""Incremental, byte-bounded replay reconstruction; no storage or network producer.

States are private authoritative producer records. They are never accepted as
client prefix claims, and no failure advances the supplied immutable state.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pydantic import ValidationError

from strange_physics.artifact_contracts import ArtifactRef, VerifiedArtifact
from strange_physics.bounded_json import parse_bounded_json
from strange_physics.control_contracts import ContractViolation, RunView
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.web_access import ViewerContext, authorize_viewer, check_run_capture
from strange_physics.web_contracts import (
    MAX_SAFE,
    EventIdentity,
    HistoryPage,
    HistoryPageBinding,
    RunSnapshot,
    SnapshotRecord,
    StreamHead,
    StreamNamespace,
    WebPolicy,
)
from strange_physics.web_delivery import _parse_chunk
from strange_physics.web_replay import _head, _snapshot, _token

INDEX_BYTES = 8 * 1024 * 1024
PageEntry = tuple[str, int, str]
ObjectEntry = tuple[str, str, int, str]
EventEntry = tuple[EventIdentity, int]


@dataclass(frozen=True)
class HistoryState:
    """Bounded private state; all consumed identities remain until completion or failure."""

    snapshot: RunSnapshot
    snapshot_sha256: str
    policy_sha256: str
    started_at: int
    deadline: int
    page: HistoryPage | None = None
    page_chunk_offset: int = 0
    seen_pages: tuple[PageEntry, ...] = ()
    seen_objects: tuple[ObjectEntry, ...] = ()
    seen_events: tuple[EventEntry, ...] = ()
    page_bytes: int = 0
    chunk_bytes: int = 0
    metadata_bytes: int = 0

    @property
    def after_sequence(self) -> int:
        return -1 if not self.seen_events else self.seen_events[-1][0].sequence

    @property
    def complete(self) -> bool:
        root = self.snapshot.history
        return (
            self.after_sequence == root.through_sequence
            and len(self.seen_pages) == root.page_count
            and len(self.seen_objects) == root.chunk_count
            and self.chunk_bytes == root.total_chunk_bytes
            and (not self.seen_events or self.seen_events[-1][0] == root.last_event)
            and (
                self.page is None
                or (self.page.next_page is None and self.page_chunk_offset == len(self.page.chunks))
            )
        )


def _entry_bytes(kind: str, value: PageEntry | ObjectEntry | EventEntry) -> int:
    if kind == "event":
        identity, occurred = value[0], value[1]
        assert isinstance(identity, EventIdentity)
        payload = [kind, identity.event_id, identity.sequence, identity.event_sha256, occurred]
    else:
        payload = [kind, *value]
    # This exact canonical line is the accounting representation; it is not a new SCI hash.
    return len(canonical_json(payload).encode("utf-8")) + 1


def _metadata(state: HistoryState) -> int:
    return (
        sum(_entry_bytes("page", entry) for entry in state.seen_pages)
        + sum(_entry_bytes("object", entry) for entry in state.seen_objects)
        + sum(_entry_bytes("event", entry) for entry in state.seen_events)
    )


def _check_state(
    context: ViewerContext,
    configured: WebPolicy,
    namespace: StreamNamespace,
    requested_snapshot_id: str,
    state: HistoryState,
    now: int,
) -> None:
    _token(requested_snapshot_id)
    assert context.run is not None
    if state.snapshot.snapshot_id != requested_snapshot_id or state.snapshot.namespace != namespace:
        raise ContractViolation("not_found", 404)
    check_run_capture(state.snapshot.run, context.run)
    root = state.snapshot.history
    if (
        state.snapshot_sha256 != message_sha256(state.snapshot)
        or state.policy_sha256 != message_sha256(configured)
        or not state.started_at <= now < state.deadline
        or state.deadline > min(MAX_SAFE, state.started_at + configured.max_delivery_seconds)
        or state.snapshot.captured_at > state.started_at
        or len(state.seen_pages) > root.page_count
        or len(state.seen_objects) > root.chunk_count
        or len(state.seen_events) != state.after_sequence + 1
        or state.after_sequence > root.through_sequence
        or state.page_bytes != sum(entry[1] for entry in state.seen_pages)
        or state.chunk_bytes != sum(entry[2] for entry in state.seen_objects)
        or state.chunk_bytes > root.total_chunk_bytes
        or state.metadata_bytes != _metadata(state)
        or len({entry[0] for entry in state.seen_pages}) != len(state.seen_pages)
        or len({entry[:2] for entry in state.seen_objects}) != len(state.seen_objects)
        or len({entry[0].event_id for entry in state.seen_events}) != len(state.seen_events)
        or any(
            identity.namespace != namespace or identity.sequence != index
            for index, (identity, _) in enumerate(state.seen_events)
        )
        or (
            state.page is None
            and (
                state.seen_pages
                or state.seen_objects
                or state.seen_events
                or state.page_chunk_offset != 0
            )
        )
        or (
            state.page is not None
            and (
                not state.seen_pages
                or state.seen_pages[-1][0] != state.page.page_id
                or state.seen_pages[-1][2] != message_sha256(state.page)
                or state.page.page_index != len(state.seen_pages) - 1
                or not 0 <= state.page_chunk_offset <= len(state.page.chunks)
                or state.page.first_chunk_index + state.page_chunk_offset != len(state.seen_objects)
            )
        )
    ):
        raise ContractViolation("recovery_required", 409)
    if (
        root.page_count > configured.max_history_pages
        or state.page_bytes + state.chunk_bytes > configured.max_history_bytes
        or state.metadata_bytes > min(INDEX_BYTES, configured.max_history_bytes)
    ):
        raise ContractViolation("quota_exceeded", 429)


def _growth(state: HistoryState, configured: WebPolicy, *, delivered: int, metadata: int) -> None:
    if (
        state.page_bytes + state.chunk_bytes + delivered > configured.max_history_bytes
        or state.metadata_bytes + metadata > min(INDEX_BYTES, configured.max_history_bytes)
    ):
        raise ContractViolation("quota_exceeded", 429)


def begin_history(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str,
    snapshot: SnapshotRecord | None,
    head: StreamHead | None,
    now: int,
) -> HistoryState:
    configured = authorize_viewer(context, policy, namespace, now=now)
    _token(requested_snapshot_id)
    current = _head(context, namespace, head, now)
    captured = _snapshot(context, configured, namespace, snapshot, current, now)
    if captured.snapshot_id != requested_snapshot_id:
        raise ContractViolation("not_found", 404)
    if now == MAX_SAFE:
        raise ContractViolation("quota_exceeded", 429)
    return HistoryState(
        snapshot=captured,
        snapshot_sha256=message_sha256(captured),
        policy_sha256=message_sha256(configured),
        started_at=now,
        deadline=min(MAX_SAFE, now + configured.max_delivery_seconds),
    )


def read_history_page(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str,
    requested_page_id: str,
    snapshot: SnapshotRecord | None,
    head: StreamHead | None,
    binding: HistoryPageBinding | None,
    raw: bytes,
    now: int,
) -> HistoryPage:
    """Single authoritative page lookup; full chain completeness is a separate walk."""
    configured = authorize_viewer(context, policy, namespace, now=now)
    _token(requested_snapshot_id)
    _token(requested_page_id)
    current = _head(context, namespace, head, now)
    captured = _snapshot(context, configured, namespace, snapshot, current, now)
    if (
        captured.snapshot_id != requested_snapshot_id
        or binding is None
        or binding.page.page_id != requested_page_id
    ):
        raise ContractViolation("not_found", 404)
    if message_sha256(captured.history) != message_sha256(binding.manifest):
        raise ContractViolation("recovery_required", 409)
    page = parse_bounded_json(
        raw, HistoryPage, max_bytes=configured.max_page_bytes, max_depth=32, max_nodes=1_000_000
    )
    if message_sha256(page) != message_sha256(binding.page):
        raise ContractViolation("recovery_required", 409)
    if len(page.chunks) > configured.max_page_refs:
        raise ContractViolation("quota_exceeded", 429)
    return page


def accept_history_page(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str,
    state: HistoryState,
    raw: bytes,
    now: int,
) -> HistoryState:
    configured = authorize_viewer(context, policy, namespace, now=now)
    _check_state(context, configured, namespace, requested_snapshot_id, state, now)
    if state.complete or (
        state.page is not None and state.page_chunk_offset != len(state.page.chunks)
    ):
        raise ContractViolation("incompatible_state", 409)
    expected = state.snapshot.history.first_page if state.page is None else state.page.next_page
    if expected is None:
        raise ContractViolation("recovery_required", 409)
    page = parse_bounded_json(
        raw, HistoryPage, max_bytes=configured.max_page_bytes, max_depth=32, max_nodes=1_000_000
    )
    if (
        page.page_id != expected.page_id
        or message_sha256(page) != expected.page_sha256
        or page.page_index != len(state.seen_pages)
        or page.first_chunk_index != len(state.seen_objects)
        or page.chunks[0].first_sequence != state.after_sequence + 1
    ):
        raise ContractViolation("recovery_required", 409)
    try:
        HistoryPageBinding(manifest=state.snapshot.history, page=page, previous=state.page)
    except ValidationError:
        raise ContractViolation("recovery_required", 409) from None
    if len(page.chunks) > configured.max_page_refs or any(
        chunk.event_count > configured.max_chunk_events
        or chunk.artifact.size_bytes > configured.max_chunk_bytes
        for chunk in page.chunks
    ):
        raise ContractViolation("quota_exceeded", 429)
    known_pages = {entry[0] for entry in state.seen_pages}
    if page.page_id in known_pages or (
        page.next_page is not None and page.next_page.page_id in known_pages
    ):
        raise ContractViolation("recovery_required", 409)
    entry: PageEntry = (page.page_id, len(raw), message_sha256(page))
    added = _entry_bytes("page", entry)
    _growth(state, configured, delivered=len(raw), metadata=added)
    return replace(
        state,
        page=page,
        page_chunk_offset=0,
        seen_pages=state.seen_pages + (entry,),
        page_bytes=state.page_bytes + len(raw),
        metadata_bytes=state.metadata_bytes + added,
    )


def accept_history_chunk(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str,
    requested_artifact: ArtifactRef,
    state: HistoryState,
    artifact: VerifiedArtifact | None,
    raw: bytes,
    now: int,
) -> HistoryState:
    configured = authorize_viewer(context, policy, namespace, now=now)
    _check_state(context, configured, namespace, requested_snapshot_id, state, now)
    page = state.page
    if state.complete or page is None or state.page_chunk_offset >= len(page.chunks):
        raise ContractViolation("incompatible_state", 409)
    descriptor = page.chunks[state.page_chunk_offset]
    if descriptor.artifact != requested_artifact:
        raise ContractViolation("not_found", 404)
    if (descriptor.artifact.artifact_id, descriptor.artifact.generation) in {
        entry[:2] for entry in state.seen_objects
    }:
        raise ContractViolation("recovery_required", 409)
    chunk = _parse_chunk(namespace, descriptor, artifact, raw, configured, now)
    if chunk.first_sequence != state.after_sequence + 1:
        raise ContractViolation("recovery_required", 409)
    known = {entry[0].event_id for entry in state.seen_events}
    last_time = None if not state.seen_events else state.seen_events[-1][1]
    entries: list[EventEntry] = []
    root = state.snapshot.history
    for event in chunk.events:
        identity = EventIdentity.from_event(event)
        if (
            event.event_id in known
            or event.occurred_at > state.snapshot.captured_at
            or (last_time is not None and event.occurred_at < last_time)
            or (
                root.last_event is not None
                and event.event_id == root.last_event.event_id
                and identity != root.last_event
            )
        ):
            raise ContractViolation("recovery_required", 409)
        if isinstance(event.payload, RunView):
            check_run_capture(event.payload, state.snapshot.run)
        known.add(event.event_id)
        entries.append((identity, event.occurred_at))
        last_time = event.occurred_at
    item: ObjectEntry = (
        descriptor.artifact.artifact_id,
        descriptor.artifact.generation,
        len(raw),
        message_sha256(chunk),
    )
    added = _entry_bytes("object", item) + sum(_entry_bytes("event", entry) for entry in entries)
    _growth(state, configured, delivered=len(raw), metadata=added)
    after = replace(
        state,
        page_chunk_offset=state.page_chunk_offset + 1,
        seen_objects=state.seen_objects + (item,),
        seen_events=state.seen_events + tuple(entries),
        chunk_bytes=state.chunk_bytes + len(raw),
        metadata_bytes=state.metadata_bytes + added,
    )
    if len(after.seen_objects) == root.chunk_count and not after.complete:
        raise ContractViolation("recovery_required", 409)
    return after
