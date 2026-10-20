"""Bounded viewer cursor/snapshot/live-batch decisions over trusted committed evidence.

No function mints a cursor, reads a database or sends network bytes. Producers
must bind supplied rows to their authoritative current transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pydantic import TypeAdapter, ValidationError

from strange_physics.bounded_json import bounded_canonical
from strange_physics.contracts import Identifier
from strange_physics.control_contracts import ContractViolation, Error, RunView
from strange_physics.research_contracts import message_sha256
from strange_physics.web_access import ViewerContext, authorize_viewer, check_run_capture
from strange_physics.web_contracts import (
    MAX_SAFE,
    CursorLookup,
    EventBatch,
    EventCursor,
    EventDelivery,
    EventIdentity,
    ResyncRequired,
    RunEvent,
    RunSnapshot,
    SnapshotRecord,
    StreamHead,
    StreamNamespace,
    WebPolicy,
)

RECENT_EVENTS = 256
_TOKEN = TypeAdapter(Identifier)


@dataclass(frozen=True)
class StreamPosition:
    """Private producer-owned walk state, never a client-authored numeric cursor proof."""

    namespace: StreamNamespace
    captured_run: RunView
    policy_sha256: str
    after_sequence: int
    last_event: EventIdentity | None
    recent_events: tuple[EventIdentity, ...]
    last_occurred_at: int | None
    started_at: int
    deadline: int
    delivered_bytes: int = 0


def _head(
    context: ViewerContext, namespace: StreamNamespace, head: StreamHead | None, now: int
) -> StreamHead:
    if head is None:
        raise ContractViolation("recovery_required", 409)
    assert context.run is not None  # Complete current viewer gate precedes every use.
    if (
        head.namespace != namespace
        or head.observed_at > now
        or head.run_revision != context.run.revision
    ):
        raise ContractViolation("recovery_required", 409)
    return head


def _event(event: RunEvent, head: StreamHead, context: ViewerContext, now: int) -> EventIdentity:
    identity = EventIdentity.from_event(event)
    if (
        event.namespace != head.namespace
        or event.sequence > head.committed_through_sequence
        or event.occurred_at > min(now, head.observed_at)
        or (event.sequence == head.committed_through_sequence and identity != head.last_event)
        or (
            head.last_event is not None
            and event.event_id == head.last_event.event_id
            and identity != head.last_event
        )
    ):
        raise ContractViolation("recovery_required", 409)
    if isinstance(event.payload, RunView):
        assert context.run is not None
        check_run_capture(event.payload, context.run)
    return identity


def _snapshot(
    context: ViewerContext,
    configured: WebPolicy,
    namespace: StreamNamespace,
    record: SnapshotRecord | None,
    head: StreamHead,
    now: int,
) -> RunSnapshot:
    if record is None:
        raise ContractViolation("not_found", 404)
    snapshot = record.snapshot
    assert context.run is not None
    if (
        snapshot.namespace != namespace
        or snapshot.captured_at > min(now, head.observed_at)
        or snapshot.history.through_sequence > head.committed_through_sequence
        or (
            snapshot.history.through_sequence == head.committed_through_sequence
            and snapshot.history.last_event != head.last_event
        )
        or (
            snapshot.history.last_event is not None
            and head.last_event is not None
            and snapshot.history.last_event.event_id == head.last_event.event_id
            and snapshot.history.last_event != head.last_event
        )
    ):
        raise ContractViolation("recovery_required", 409)
    check_run_capture(snapshot.run, context.run)
    if (
        snapshot.history.page_count > configured.max_history_pages
        or snapshot.history.total_chunk_bytes > configured.max_history_bytes
    ):
        raise ContractViolation("quota_exceeded", 429)
    bounded_canonical(snapshot, configured.max_page_bytes)
    if record.cursor is not None and record.cursor.issued_at > now:
        raise ContractViolation("recovery_required", 409)
    return snapshot


def read_snapshot(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str | None,
    record: SnapshotRecord | None,
    head: StreamHead | None,
    now: int,
) -> RunSnapshot:
    configured = authorize_viewer(context, policy, namespace, now=now)
    current = _head(context, namespace, head, now)
    if requested_snapshot_id is not None:
        _token(requested_snapshot_id)
        if record is None or record.snapshot.snapshot_id != requested_snapshot_id:
            raise ContractViolation("not_found", 404)
    return _snapshot(context, configured, namespace, record, current, now)


def _token(value: str) -> None:
    # fullmatch is implicit in the explicit ASCII check; '$' alone allows a final newline.
    try:
        _TOKEN.validate_python(value, strict=True)
    except ValidationError:
        raise ContractViolation("invalid_request", 400) from None
    if any(
        char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        for char in value
    ):
        raise ContractViolation("invalid_request", 400)


def _resync(
    context: ViewerContext,
    configured: WebPolicy,
    namespace: StreamNamespace,
    record: SnapshotRecord | None,
    head: StreamHead,
    request_id: str,
    now: int,
) -> ResyncRequired:
    if record is None:
        raise ContractViolation("recovery_required", 409)
    snapshot = _snapshot(context, configured, namespace, record, head, now)
    if (
        snapshot.history.through_sequence != head.committed_through_sequence
        or snapshot.run.revision != head.run_revision
        or (record is not None and record.cursor is not None and now >= record.cursor.expires_at)
    ):
        raise ContractViolation("recovery_required", 409)
    return ResyncRequired(
        error=Error(
            code="cursor_expired",
            message="The stream requires a current snapshot.",
            request_id=request_id,
            retryable=False,
            operation_id=None,
        ),
        namespace=namespace,
        snapshot_id=snapshot.snapshot_id,
    )


def resolve_cursor(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    raw_last_event_id: str | None,
    lookup: CursorLookup,
    resync_snapshot: SnapshotRecord | None,
    request_id: str,
    now: int,
) -> StreamPosition | ResyncRequired:
    configured = authorize_viewer(context, policy, namespace, now=now)
    if raw_last_event_id is not None:
        _token(raw_last_event_id)
    if lookup.namespace != namespace or lookup.requested_cursor != raw_last_event_id:
        raise ContractViolation("recovery_required", 409)
    head = _head(context, namespace, lookup.head, now)
    after, identity, occurred = -1, None, None
    if raw_last_event_id is None:
        if lookup.cursor is not None or lookup.event is not None or lookup.snapshot is not None:
            raise ContractViolation("recovery_required", 409)
    else:
        cursor = lookup.cursor
        if cursor is None:
            if lookup.event is not None or lookup.snapshot is not None:
                raise ContractViolation("recovery_required", 409)
            raise ContractViolation("not_found", 404)
        if cursor.cursor_id != raw_last_event_id or cursor.namespace != namespace:
            raise ContractViolation("not_found", 404)
        if cursor.issued_at > now or cursor.after_sequence > head.committed_through_sequence:
            raise ContractViolation("recovery_required", 409)
        after, identity = cursor.after_sequence, cursor.event
        if after == head.committed_through_sequence and identity != head.last_event:
            raise ContractViolation("recovery_required", 409)
        if (
            identity is not None
            and head.last_event is not None
            and identity.event_id == head.last_event.event_id
            and identity != head.last_event
        ):
            raise ContractViolation("recovery_required", 409)
        if cursor.snapshot_id is None:
            if lookup.snapshot is not None:
                raise ContractViolation("recovery_required", 409)
        else:
            if lookup.snapshot is None:
                raise ContractViolation("recovery_required", 409)
            _snapshot(context, configured, namespace, lookup.snapshot, head, now)
            if (
                lookup.snapshot.cursor != cursor
                or message_sha256(lookup.snapshot.snapshot) != cursor.snapshot_sha256
                or lookup.snapshot.snapshot.snapshot_id != cursor.snapshot_id
            ):
                raise ContractViolation("recovery_required", 409)
        if lookup.event is not None:
            if _event(lookup.event, head, context, now) != identity:
                raise ContractViolation("recovery_required", 409)
            occurred = lookup.event.occurred_at
        elif after >= 0 and lookup.snapshot is None and identity != head.last_event:
            raise ContractViolation("recovery_required", 409)
        if now >= cursor.expires_at:
            return _resync(context, configured, namespace, resync_snapshot, head, request_id, now)
    if after < head.retained_from_sequence - 1:
        return _resync(context, configured, namespace, resync_snapshot, head, request_id, now)
    assert context.run is not None
    return StreamPosition(
        namespace=namespace,
        captured_run=context.run,
        policy_sha256=message_sha256(configured),
        after_sequence=after,
        last_event=identity,
        recent_events=() if identity is None else (identity,),
        last_occurred_at=occurred,
        started_at=now,
        deadline=min(MAX_SAFE, now + configured.max_delivery_seconds),
    )


def _check_stream_state(
    state: StreamPosition,
    context: ViewerContext,
    configured: WebPolicy,
    now: int,
) -> None:
    """Incomplete state join; every exported boundary first performs current authorization."""
    assert context.run is not None
    check_run_capture(state.captured_run, context.run)
    if (
        state.policy_sha256 != message_sha256(configured)
        or now < state.started_at
        or now >= state.deadline
        or state.deadline > min(MAX_SAFE, state.started_at + configured.max_delivery_seconds)
        or not -1 <= state.after_sequence <= MAX_SAFE
        or (state.last_event is None) != (state.after_sequence == -1)
        or (
            state.last_event is not None
            and (
                state.last_event.namespace != state.namespace
                or state.last_event.sequence != state.after_sequence
            )
        )
        or len(state.recent_events) > RECENT_EVENTS
        or not 0 <= state.delivered_bytes <= configured.max_history_bytes
    ):
        raise ContractViolation("incompatible_state", 409)


def prepare_event_batch(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    state: StreamPosition,
    head: StreamHead | None,
    events: tuple[RunEvent, ...],
    cursors: tuple[EventCursor, ...],
    now: int,
) -> tuple[EventBatch | None, StreamPosition]:
    configured = authorize_viewer(context, policy, namespace, now=now)
    if state.namespace != namespace:
        raise ContractViolation("recovery_required", 409)
    _check_stream_state(state, context, configured, now)
    current = _head(context, namespace, head, now)
    if (
        state.after_sequence > current.committed_through_sequence
        or (
            state.after_sequence == current.committed_through_sequence
            and state.last_event != current.last_event
        )
        or (
            state.last_event is not None
            and current.last_event is not None
            and state.last_event.event_id == current.last_event.event_id
            and state.last_event != current.last_event
        )
    ):
        raise ContractViolation("recovery_required", 409)
    if state.after_sequence < current.retained_from_sequence - 1:
        raise ContractViolation("cursor_expired", 410)
    if len(events) != len(cursors) or len(events) > configured.max_batch_events:
        raise ContractViolation("invalid_request", 422)
    after, last, occurred = state.after_sequence, state.last_event, state.last_occurred_at
    seen = list(state.recent_events)
    deliveries = []
    for event, cursor in zip(events, cursors, strict=True):
        identity = _event(event, current, context, now)
        if (
            cursor.namespace != namespace
            or cursor.event != identity
            or cursor.after_sequence != event.sequence
            or cursor.snapshot_id is not None
            or not cursor.issued_at <= now < cursor.expires_at
            or cursor.issued_at < event.occurred_at
            or cursor.expires_at - cursor.issued_at > configured.cursor_ttl_seconds
        ):
            raise ContractViolation("recovery_required", 409)
        matching = next((old for old in seen if old.sequence == event.sequence), None)
        if event.sequence <= after:
            if matching is None:
                raise ContractViolation("cursor_expired", 410)
            if matching != identity:
                raise ContractViolation("recovery_required", 409)
            continue
        if (
            after == MAX_SAFE
            or event.sequence != after + 1
            or any(old.event_id == identity.event_id and old != identity for old in seen)
            or (occurred is not None and event.occurred_at < occurred)
        ):
            raise ContractViolation("recovery_required", 409)
        item = EventDelivery(
            event=event, event_sha256=identity.event_sha256, resume_cursor=cursor.cursor_id
        )
        if len(item.sse_bytes()) > configured.max_event_bytes:
            raise ContractViolation("quota_exceeded", 429)
        deliveries.append(item)
        seen = (seen + [identity])[-RECENT_EVENTS:]
        after, last, occurred = event.sequence, identity, event.occurred_at
    if not deliveries:
        return None, state
    batch = EventBatch(deliveries=tuple(deliveries))
    count = sum(len(item.sse_bytes()) for item in batch.deliveries)
    if (
        count > configured.max_batch_bytes
        or state.delivered_bytes + count > configured.max_history_bytes
    ):
        raise ContractViolation("quota_exceeded", 429)
    return batch, replace(
        state,
        after_sequence=after,
        last_event=last,
        recent_events=tuple(seen),
        last_occurred_at=occurred,
        delivered_bytes=state.delivered_bytes + count,
    )
