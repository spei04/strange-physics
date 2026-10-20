"""Current WEB viewer/cursor/live-delivery boundaries, without HTTP or DB producers."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from test_run_credentials import changed, product, value

from strange_physics import run_credential_contracts as rc
from strange_physics import web_contracts as w
from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import message_sha256
from strange_physics.web_access import ViewerContext, authorize_viewer
from strange_physics.web_replay import (
    StreamPosition,
    prepare_event_batch,
    read_snapshot,
    resolve_cursor,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "contracts/web.examples.json").read_text())


def sample[T: Message](model: type[T]) -> T:
    return model.model_validate_json(json.dumps(copy.deepcopy(DATA["valid"][model.__name__])))


def viewer(kind: str = "user", **changes: Any) -> ViewerContext:
    authority: rc.ProductAuthority
    if kind == "user":
        authority = value(rc.HumanProductAuthority)
    elif kind == "service":
        authority = value(rc.ServiceProductAuthority)
    else:
        authority = value(rc.RunProductAuthority)
    if kind != "run":
        authority = type(authority).model_validate_json(
            authority.model_dump_json().replace('"workspace-1"', '"ws-1"')
        )
    original = product(authority, "runs:read")
    return ViewerContext(
        authority=authority,
        credential=original["credential"],
        membership=original["membership"],
        workspace=original["workspace"],
        run=sample(w.RunSnapshot).run,
        has_session_cookie=kind == "user",
        has_bearer=kind != "user",
        **changes,
    )


def head(**changes: Any) -> w.StreamHead:
    return changed(sample(w.StreamHead), observed_at=1200, **changes)


def snapshot(*, expires_at: int = 1300) -> w.SnapshotRecord:
    record = sample(w.SnapshotRecord)
    assert record.cursor is not None
    return changed(record, cursor=changed(record.cursor, issued_at=1200, expires_at=expires_at))


def cursor_args(*, absent: bool = False, kind: str = "user") -> dict[str, Any]:
    record = snapshot()
    lookup = changed(
        sample(w.CursorLookup),
        head=head(),
        cursor=record.cursor,
        snapshot=record,
    )
    if absent:
        lookup = changed(lookup, requested_cursor=None, cursor=None, event=None, snapshot=None)
    return dict(
        context=viewer(kind),
        policy=sample(w.WebPolicy),
        namespace=sample(w.StreamNamespace),
        raw_last_event_id=lookup.requested_cursor,
        lookup=lookup,
        resync_snapshot=record,
        request_id="request-1",
        now=1200,
    )


def position(**changes: Any) -> StreamPosition:
    result = resolve_cursor(**(cursor_args(absent=True) | changes))
    assert isinstance(result, StreamPosition)
    return result


def event_args(*, kind: str = "user") -> dict[str, Any]:
    events = tuple(w.RunEvent.model_validate_json(json.dumps(event)) for event in DATA["events"])
    cursors = tuple(
        w.EventCursor(
            cursor_id=f"delivery-{event.sequence}",
            namespace=event.namespace,
            after_sequence=event.sequence,
            event=w.EventIdentity.from_event(event),
            snapshot_id=None,
            snapshot_sha256=None,
            issued_at=1200,
            expires_at=1300,
        )
        for event in events
    )
    context = viewer(kind)
    return dict(
        context=context,
        policy=sample(w.WebPolicy),
        namespace=sample(w.StreamNamespace),
        state=position(context=context),
        head=head(),
        events=events,
        cursors=cursors,
        now=1200,
    )


def violation(code: str, status: int) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda error: error.status == status)


@pytest.mark.parametrize("kind", ["user", "service"])
@pytest.mark.parametrize(
    "status", ["queued", "running", "recovering", "completed", "failed", "cancelled", "expired"]
)
def test_current_viewer_reads_all_run_states_without_lease(kind: str, status: str) -> None:
    context = viewer(kind)
    assert context.run is not None
    context = replace(context, run=changed(context.run, status=status))
    assert authorize_viewer(context, sample(w.WebPolicy), sample(w.StreamNamespace), now=1200)
    result = resolve_cursor(**cursor_args(absent=True, kind=kind) | {"context": context})
    assert isinstance(result, StreamPosition)


@pytest.mark.parametrize("kind", ["user", "service"])
def test_mixed_transport_denied_before_poisoned_lookup(kind: str) -> None:
    args = cursor_args(kind=kind)
    args.update(
        context=replace(args["context"], has_session_cookie=True, has_bearer=True),
        lookup=object(),
        policy=None,
    )
    with violation("ambiguous_credentials", 400):
        resolve_cursor(**args)


@pytest.mark.parametrize(
    "kind,cookie,bearer",
    [
        ("user", False, True),
        ("user", False, False),
        ("service", True, False),
        ("service", False, False),
        ("run", False, True),
    ],
)
def test_no_user_bearer_worker_or_missing_transport(kind: str, cookie: bool, bearer: bool) -> None:
    args = cursor_args()
    args.update(
        context=replace(viewer(kind), has_session_cookie=cookie, has_bearer=bearer), lookup=object()
    )
    with violation("unauthenticated", 401):
        resolve_cursor(**args)


@pytest.mark.parametrize("kind", ["user", "service"])
def test_revoked_current_authority_precedes_lookup_and_policy(kind: str) -> None:
    args = cursor_args(kind=kind)
    context = args["context"]
    args.update(
        context=replace(context, credential=changed(context.credential, revoked=True)),
        lookup=object(),
        policy=None,
    )
    with violation("unauthenticated", 401):
        resolve_cursor(**args)


def test_missing_policy_or_run_fail_closed_after_authority() -> None:
    args = cursor_args()
    with violation("policy_unavailable", 503):
        resolve_cursor(**(args | {"policy": None, "lookup": object()}))
    with violation("not_found", 404):
        resolve_cursor(
            **(args | {"context": replace(args["context"], run=None), "lookup": object()})
        )


@pytest.mark.parametrize("token", ["", "\n", "a\r", "a\0", "é", "x" * 65, 123, True])
def test_malformed_header_after_authority(token: Any) -> None:
    with violation("invalid_request", 400):
        resolve_cursor(**(cursor_args() | {"raw_last_event_id": token, "lookup": object()}))


@pytest.mark.parametrize("point", ["unknown", "foreign", "wrong_id"])
def test_unknown_foreign_cursor_is_not_found(point: str) -> None:
    args = cursor_args()
    lookup = args["lookup"]
    if point == "unknown":
        lookup = changed(lookup, cursor=None, event=None, snapshot=None)
    elif point == "wrong_id":
        lookup = changed(lookup, cursor=changed(lookup.cursor, cursor_id="different"))
    else:
        cursor = lookup.cursor
        ns = changed(cursor.namespace, run_id="foreign")
        lookup = changed(
            lookup, cursor=changed(cursor, namespace=ns, event=changed(cursor.event, namespace=ns))
        )
    with violation("not_found", 404):
        resolve_cursor(**(args | {"lookup": lookup}))


@pytest.mark.parametrize(
    "point",
    [
        "head_missing",
        "head_revision",
        "future_head",
        "event_missing",
        "event_hash",
        "snapshot_missing",
        "beyond_head",
        "requested_alias",
        "partial_unknown",
    ],
)
def test_cursor_supplied_evidence_contradictions(point: str) -> None:
    args = cursor_args()
    lookup = args["lookup"]
    if point == "head_missing":
        lookup = changed(lookup, head=None)
    elif point == "head_revision":
        lookup = changed(lookup, head=changed(lookup.head, run_revision=1))
    elif point == "future_head":
        lookup = changed(lookup, head=changed(lookup.head, observed_at=1201))
    elif point == "event_missing":
        # No snapshot and not the final head: its actual archived event witness is required.
        event = w.RunEvent.model_validate_json(json.dumps(DATA["events"][0]))
        cursor = changed(
            lookup.cursor,
            after_sequence=0,
            event=w.EventIdentity.from_event(event),
            snapshot_id=None,
            snapshot_sha256=None,
        )
        lookup = changed(lookup, cursor=cursor, snapshot=None, event=None)
    elif point == "event_hash":
        lookup = changed(lookup, event=changed(lookup.event, operation_id="different"))
    elif point == "snapshot_missing":
        lookup = changed(lookup, snapshot=None)
    elif point == "beyond_head":
        lookup = changed(lookup, head=head(committed_through_sequence=-1, last_event=None))
    elif point == "requested_alias":
        lookup = changed(lookup, requested_cursor="different")
    else:
        lookup = changed(lookup, cursor=None)
    code = "incompatible_state" if point == "beyond_head" else "recovery_required"
    with violation(code, 409):
        resolve_cursor(**(args | {"lookup": lookup}))


def test_expiry_and_retention_return_actual_scoped_resync() -> None:
    args = cursor_args()
    expired = snapshot(expires_at=1201)
    result = resolve_cursor(
        **(
            args
            | {
                "now": 1201,
                "lookup": changed(args["lookup"], cursor=expired.cursor, snapshot=expired),
            }
        )
    )
    assert isinstance(result, w.ResyncRequired)
    assert result.snapshot_id == args["resync_snapshot"].snapshot.snapshot_id
    assert not result.error.retryable and result.error.operation_id is None
    absent = cursor_args(absent=True)
    result = resolve_cursor(
        **(
            absent
            | {
                "lookup": changed(absent["lookup"], head=head(retained_from_sequence=1)),
            }
        )
    )
    assert isinstance(result, w.ResyncRequired)


@pytest.mark.parametrize("point", ["missing", "expired", "stale_capture"])
def test_expired_cursor_cannot_invent_resync_identity(point: str) -> None:
    args = cursor_args()
    expired = snapshot(expires_at=1201)
    args.update(now=1201, lookup=changed(args["lookup"], cursor=expired.cursor, snapshot=expired))
    if point == "missing":
        args["resync_snapshot"] = None
        code, status = "recovery_required", 409
    elif point == "expired":
        args["resync_snapshot"] = expired
        code, status = "recovery_required", 409
    else:
        args["context"] = replace(args["context"], run=changed(args["context"].run, revision=3))
        args["lookup"] = changed(args["lookup"], head=head(run_revision=3))
        code, status = "recovery_required", 409
    with violation(code, status):
        resolve_cursor(**args)


def test_historical_snapshot_allows_later_current_run_but_not_signed_zero_change() -> None:
    args = cursor_args()
    original = args["context"]
    assert original.run is not None
    later = replace(
        original,
        run=changed(
            original.run, revision=3, status="completed", experiments_accepted=3, budget_remaining=3
        ),
    )
    kw = dict(
        context=later,
        policy=args["policy"],
        namespace=args["namespace"],
        requested_snapshot_id="snapshot-1",
        record=snapshot(),
        head=head(run_revision=3),
        now=1200,
    )
    assert read_snapshot(**kw) == snapshot().snapshot
    bad_space = changed(
        later.run.space, sampling=changed(later.run.space.sampling, position_noise=-0.0)
    )
    with violation("recovery_required", 409):
        read_snapshot(**(kw | {"context": replace(later, run=changed(later.run, space=bad_space))}))


def test_equal_run_revision_requires_actual_canonical_capture() -> None:
    args = cursor_args()
    context = args["context"]
    assert context.run is not None
    context = replace(context, run=changed(context.run, status="completed"))
    with violation("recovery_required", 409):
        read_snapshot(
            context,
            args["policy"],
            args["namespace"],
            requested_snapshot_id=None,
            record=snapshot(),
            head=head(),
            now=1200,
        )


@pytest.mark.parametrize("kind", ["user", "service"])
def test_event_delivery_exact_wire_watermark_and_duplicate_handling(kind: str) -> None:
    args = event_args(kind=kind)
    batch, state = prepare_event_batch(**args)
    assert batch is not None and len(batch.deliveries) == 4
    assert state.after_sequence == 3 and state.last_event == head().last_event
    assert state.delivered_bytes == sum(len(item.sse_bytes()) for item in batch.deliveries)
    repeated, same = prepare_event_batch(**(args | {"state": state}))
    assert repeated is None and same == state
    empty, same = prepare_event_batch(**(args | {"state": state, "events": (), "cursors": ()}))
    assert empty is None and same == state


@pytest.mark.parametrize(
    "point", ["gap", "wrong_cursor", "expired_cursor", "future_cursor", "wrong_head"]
)
def test_event_delivery_requires_actual_committed_cursor_and_sequence(point: str) -> None:
    args = event_args()
    if point == "gap":
        args.update(events=args["events"][1:], cursors=args["cursors"][1:])
    elif point == "wrong_head":
        args["head"] = changed(
            args["head"], last_event=changed(args["head"].last_event, event_sha256="0" * 64)
        )
    else:
        cursor = args["cursors"][0]
        if point == "wrong_cursor":
            cursor = changed(cursor, event=changed(cursor.event, event_sha256="0" * 64))
        elif point == "expired_cursor":
            cursor = changed(cursor, issued_at=1100, expires_at=1200)
        else:
            cursor = changed(cursor, issued_at=1201)
        args["cursors"] = (cursor,) + args["cursors"][1:]
    with violation("recovery_required", 409):
        prepare_event_batch(**args)


@pytest.mark.parametrize("point", ["revoked", "policy", "deadline", "scope"])
def test_every_batch_rechecks_current_authority_and_retained_budget(point: str) -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    args.update(state=state, events=(), cursors=())
    if point == "revoked":
        context = args["context"]
        args["context"] = replace(context, credential=changed(context.credential, revoked=True))
        args["state"] = object()
        code, status = "unauthenticated", 401
    elif point == "policy":
        args["policy"] = changed(args["policy"], revision=2)
        code, status = "incompatible_state", 409
    elif point == "deadline":
        args["now"] = state.deadline
        code, status = "incompatible_state", 409
    else:
        args["state"] = replace(state, namespace=changed(state.namespace, run_id="foreign"))
        code, status = "recovery_required", 409
    with violation(code, status):
        prepare_event_batch(**args)


def test_stricter_wire_policy_and_cumulative_budget_never_truncate() -> None:
    args = event_args()
    policy = changed(args["policy"], max_event_bytes=1)
    args.update(policy=policy, state=position(policy=policy))
    with violation("quota_exceeded", 429):
        prepare_event_batch(**args)
    args = event_args()
    policy = changed(args["policy"], max_history_bytes=1)
    args.update(policy=policy, state=position(policy=policy))
    with violation("quota_exceeded", 429):
        prepare_event_batch(**args)


def test_max_safe_watermark_has_lawful_empty_poll_without_next_number() -> None:
    args = cursor_args()
    event = changed(args["lookup"].event, sequence=w.MAX_SAFE)
    identity = w.EventIdentity.from_event(event)
    cursor = changed(
        args["lookup"].cursor,
        after_sequence=w.MAX_SAFE,
        event=identity,
        snapshot_id=None,
        snapshot_sha256=None,
    )
    terminal = head(committed_through_sequence=w.MAX_SAFE, last_event=identity)
    args["lookup"] = changed(
        args["lookup"], head=terminal, cursor=cursor, event=event, snapshot=None
    )
    state = resolve_cursor(**args)
    assert isinstance(state, StreamPosition) and state.after_sequence == w.MAX_SAFE
    batch, same = prepare_event_batch(
        args["context"],
        args["policy"],
        args["namespace"],
        state=state,
        head=terminal,
        events=(),
        cursors=(),
        now=1200,
    )
    assert batch is None and same.after_sequence == w.MAX_SAFE


def test_empty_stream_starts_at_minus_one_without_cursor() -> None:
    args = cursor_args(absent=True)
    empty_head = head(committed_through_sequence=-1, retained_from_sequence=0, last_event=None)
    state = resolve_cursor(**(args | {"lookup": changed(args["lookup"], head=empty_head)}))
    assert isinstance(state, StreamPosition) and state.after_sequence == -1
    assert state.last_event is None and state.recent_events == ()


@pytest.mark.parametrize("point", ["changed_last_hash", "reused_last_id"])
def test_empty_poll_rejects_contradictory_current_head(point: str) -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    final = head().last_event
    assert final is not None
    if point == "changed_last_hash":
        current = head(last_event=changed(final, event_sha256="0" * 64))
    else:
        current = head(committed_through_sequence=4, last_event=changed(final, sequence=4))
    with violation("recovery_required", 409):
        prepare_event_batch(
            **(args | {"state": state, "head": current, "events": (), "cursors": ()})
        )


def test_unknown_old_duplicate_requires_resync_without_advancing() -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    state = replace(state, recent_events=state.recent_events[1:])
    with violation("cursor_expired", 410):
        prepare_event_batch(
            **(
                args
                | {"state": state, "events": args["events"][:1], "cursors": args["cursors"][:1]}
            )
        )
    assert state.after_sequence == 3


def test_conflicting_duplicate_digest_rejects() -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    event = changed(args["events"][0], occurred_at=99)
    cursor = changed(args["cursors"][0], event=w.EventIdentity.from_event(event))
    with violation("recovery_required", 409):
        prepare_event_batch(**(args | {"state": state, "events": (event,), "cursors": (cursor,)}))


def test_snapshot_and_batch_authority_precedes_poisoned_private_state() -> None:
    args = cursor_args()
    context = args["context"]
    denied = replace(context, credential=changed(context.credential, revoked=True))
    poison: Any = object()
    with violation("unauthenticated", 401):
        read_snapshot(
            denied,
            None,
            args["namespace"],
            requested_snapshot_id=None,
            record=poison,
            head=poison,
            now=1200,
        )
    with violation("unauthenticated", 401):
        prepare_event_batch(
            denied,
            None,
            args["namespace"],
            state=poison,
            head=poison,
            events=(),
            cursors=(),
            now=1200,
        )


def test_human_get_does_not_require_csrf_or_management_freshness() -> None:
    args = cursor_args(absent=True)
    context = args["context"]
    assert isinstance(context.authority, rc.HumanProductAuthority)
    identity = context.authority
    identity = changed(
        identity,
        actor=changed(
            identity.actor,
            context=changed(
                identity.actor.context, csrf_matches=False, csrf_scope=None, origin=None
            ),
        ),
    )
    assert isinstance(
        resolve_cursor(**(args | {"context": replace(context, authority=identity)})), StreamPosition
    )


@pytest.mark.parametrize("issued_at,accepted", [(1198, False), (1199, True), (1200, True)])
def test_cursor_cannot_predate_supplied_committed_event(issued_at: int, accepted: bool) -> None:
    args = cursor_args()
    event = changed(args["lookup"].event, occurred_at=1199)
    identity = w.EventIdentity.from_event(event)
    cursor = changed(
        args["lookup"].cursor,
        event=identity,
        issued_at=issued_at,
        expires_at=issued_at + 100,
        snapshot_id=None,
        snapshot_sha256=None,
    )
    args["lookup"] = changed(
        args["lookup"], cursor=cursor, event=event, snapshot=None, head=head(last_event=identity)
    )
    if accepted:
        assert isinstance(resolve_cursor(**args), StreamPosition)
    else:
        with violation("recovery_required", 409):
            resolve_cursor(**args)


@pytest.mark.parametrize("occurred_at,accepted", [(99, True), (100, True), (101, False)])
def test_snapshot_cannot_predate_its_supplied_final_event(occurred_at: int, accepted: bool) -> None:
    args = cursor_args()
    event = changed(args["lookup"].event, occurred_at=occurred_at)
    identity = w.EventIdentity.from_event(event)
    original = args["lookup"].snapshot
    capture = changed(
        original.snapshot, history=changed(original.snapshot.history, last_event=identity)
    )
    cursor = changed(original.cursor, event=identity, snapshot_sha256=message_sha256(capture))
    record = changed(original, snapshot=capture, cursor=cursor)
    args["lookup"] = changed(
        args["lookup"], cursor=cursor, event=event, snapshot=record, head=head(last_event=identity)
    )
    if accepted:
        assert isinstance(resolve_cursor(**args), StreamPosition)
    else:
        with violation("recovery_required", 409):
            resolve_cursor(**args)


@pytest.mark.parametrize("token", ["", "bad\n"])
def test_snapshot_header_validation_precedes_private_head(token: str) -> None:
    args = cursor_args()
    poison: Any = object()
    with violation("invalid_request", 400):
        read_snapshot(
            args["context"],
            args["policy"],
            args["namespace"],
            requested_snapshot_id=token,
            record=poison,
            head=poison,
            now=1200,
        )
    context = args["context"]
    denied = replace(context, credential=changed(context.credential, revoked=True))
    with violation("unauthenticated", 401):
        read_snapshot(
            denied,
            args["policy"],
            args["namespace"],
            requested_snapshot_id=token,
            record=poison,
            head=poison,
            now=1200,
        )


@pytest.mark.parametrize("observed_at,accepted", [(99, False), (100, True), (1200, True)])
def test_empty_poll_head_cannot_predate_last_delivered_event(
    observed_at: int, accepted: bool
) -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    args.update(state=state, events=(), cursors=(), head=changed(head(), observed_at=observed_at))
    if accepted:
        batch, same = prepare_event_batch(**args)
        assert batch is None and same == state
    else:
        with violation("recovery_required", 409):
            prepare_event_batch(**args)


@pytest.mark.parametrize("reused", [False, True])
def test_advanced_head_compares_every_supplied_recent_identity(reused: bool) -> None:
    args = event_args()
    _, state = prepare_event_batch(**args)
    final = head().last_event
    assert final is not None
    advanced = changed(
        final, sequence=4, event_id=state.recent_events[0].event_id if reused else "fresh-event-4"
    )
    args.update(
        state=state,
        events=(),
        cursors=(),
        head=head(committed_through_sequence=4, last_event=advanced),
    )
    if reused:
        with violation("recovery_required", 409):
            prepare_event_batch(**args)
    else:
        batch, same = prepare_event_batch(**args)
        assert batch is None and same == state
