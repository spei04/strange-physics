"""Actual byte integrity, full incremental replay and per-batch current authorization."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from typing import Any

import pytest
from test_run_credentials import changed
from test_web_replay import DATA, head, sample, snapshot, viewer, violation

from strange_physics import web_contracts as w
from strange_physics import web_history as history
from strange_physics.artifact_contracts import ArtifactRef, VerifiedArtifact
from strange_physics.contracts import ExperimentRecord, Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.web_delivery import (
    deliver_body_batch,
    prepare_experiment_body,
    prepare_replay_body,
)
from strange_physics.web_history import (
    accept_history_chunk,
    accept_history_page,
    begin_history,
    read_history_page,
)


def raw_message(value: Message) -> bytes:
    return canonical_json(value.model_dump(mode="json")).encode()


def catalog(ref: ArtifactRef) -> VerifiedArtifact:
    original = sample(w.ReplayChunkBinding).artifact
    locator = changed(original.record.locator, object_key=f"runs/run-1/{ref.artifact_id}.json")
    return changed(
        original,
        record=changed(original.record, ref=ref, locator=locator),
        verification=changed(
            original.verification,
            locator=locator,
            generation=ref.generation,
            sha256=ref.sha256,
            size_bytes=ref.size_bytes,
            media_type=ref.media_type,
        ),
    )


def science_args(**changes: Any) -> dict[str, Any]:
    binding = sample(w.ExperimentRecordBinding)
    return (
        dict(
            context=viewer(),
            policy=sample(w.WebPolicy),
            namespace=sample(w.StreamNamespace),
            requested_event_id=binding.event.event_id,
            event=binding.event,
            head=head(),
            artifact=binding.artifact,
            raw=DATA["raw_record"].encode(),
            now=1200,
        )
        | changes
    )


def replace_science_raw(args: dict[str, Any], raw: bytes) -> dict[str, Any]:
    ref = args["event"].payload
    updated = changed(ref.artifact, size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    event = changed(args["event"], payload=changed(ref, artifact=updated))
    return args | {"event": event, "artifact": catalog(updated), "raw": raw}


def chain(
    *,
    count: int = 4,
    fault: str | None = None,
) -> tuple[
    w.SnapshotRecord, list[w.HistoryPage], list[bytes], list[VerifiedArtifact], w.StreamHead
]:
    namespace = sample(w.StreamNamespace)
    descriptors = []
    bodies = []
    artifacts = []
    for index in range(count):
        value = copy.deepcopy(DATA["events"][2])
        event_id = f"walk-event-{0 if fault == 'event' and index == 2 else index}"
        value.update(sequence=index, event_id=event_id)
        event = w.RunEvent.model_validate_json(json.dumps(value))
        chunk = w.ReplayChunk(
            namespace=namespace, first_sequence=index, last_sequence=index, events=(event,)
        )
        raw = raw_message(chunk)
        artifact_id = f"walk-object-{0 if fault == 'object' and index == 2 else index}"
        ref = ArtifactRef(
            artifact_id=artifact_id,
            generation="1",
            sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),
            media_type="application/json",
        )
        identity = w.EventIdentity.from_event(event)
        descriptors.append(
            w.ReplayChunkRef(
                namespace=namespace,
                first_sequence=index,
                last_sequence=index,
                event_count=1,
                first_event=identity,
                last_event=identity,
                artifact=ref,
                chunk_sha256=message_sha256(chunk),
            )
        )
        bodies.append(raw)
        artifacts.append(catalog(ref))
    pages: list[w.HistoryPage] = []
    next_page = None
    for index in reversed(range(count)):
        page_id = f"walk-page-{1 if fault == 'page' and index == 3 else index}"
        page = w.HistoryPage(
            page_id=page_id,
            manifest_id="walk-manifest",
            namespace=namespace,
            through_sequence=count - 1,
            page_index=index,
            first_chunk_index=index,
            chunks=(descriptors[index],),
            next_page=next_page,
        )
        pages.insert(0, page)
        next_page = w.HistoryPageRef(page_id=page.page_id, page_sha256=message_sha256(page))
    root = w.HistoryManifest(
        manifest_id="walk-manifest",
        namespace=namespace,
        run_revision=2,
        through_sequence=count - 1,
        last_event=descriptors[-1].last_event,
        page_count=count,
        chunk_count=count,
        total_chunk_bytes=sum(map(len, bodies)),
        first_page=next_page,
    )
    original = snapshot()
    capture = changed(original.snapshot, history=root)
    assert original.cursor is not None
    cursor = changed(
        original.cursor,
        after_sequence=count - 1,
        event=root.last_event,
        snapshot_sha256=message_sha256(capture),
    )
    record = changed(original, snapshot=capture, cursor=cursor)
    current_head = head(committed_through_sequence=count - 1, last_event=root.last_event)
    return record, pages, bodies, artifacts, current_head


def begin_args(record: w.SnapshotRecord, current: w.StreamHead, **changes: Any) -> dict[str, Any]:
    return (
        dict(
            context=viewer(),
            policy=sample(w.WebPolicy),
            namespace=sample(w.StreamNamespace),
            requested_snapshot_id=record.snapshot.snapshot_id,
            snapshot=record,
            head=current,
            now=1200,
        )
        | changes
    )


def walk_args(state: history.HistoryState, **changes: Any) -> dict[str, Any]:
    return (
        dict(
            context=viewer(),
            policy=sample(w.WebPolicy),
            namespace=sample(w.StreamNamespace),
            requested_snapshot_id=state.snapshot.snapshot_id,
            state=state,
            now=1200,
        )
        | changes
    )


def test_complete_failed_science_is_verified_before_any_delivery() -> None:
    args = science_args()
    body = prepare_experiment_body(**args)
    assert body.offset == 0 and body.semantic_sha256 == args["event"].payload.record_sha256
    assert ExperimentRecord.model_validate_json(body.raw).status == "failed"
    policy = changed(args["policy"], max_body_batch_bytes=128)
    body = prepare_experiment_body(**(args | {"policy": policy}))
    data = b""
    while body.offset < len(body.raw):
        batch = deliver_body_batch(
            args["context"],
            policy,
            args["namespace"],
            state=body,
            artifact=args["artifact"],
            request_sha256=body.request_sha256,
            now=1200,
        )
        assert 0 < len(batch.data) <= 128
        data += batch.data
        body = batch.state
        assert batch.complete == (body.offset == len(body.raw))
    assert data == args["raw"]
    again = deliver_body_batch(
        args["context"],
        policy,
        args["namespace"],
        state=body,
        artifact=args["artifact"],
        request_sha256=body.request_sha256,
        now=1200,
    )
    assert again.complete and again.data == b""


@pytest.mark.parametrize(
    "point",
    [
        "raw_hash",
        "raw_size",
        "semantic_hash",
        "generation",
        "foreign",
        "visibility",
        "future_proof",
        "missing_catalog",
    ],
)
def test_actual_object_and_semantic_identity_before_payload(point: str) -> None:
    args = science_args()
    if point == "raw_hash":
        args["raw"] = args["raw"].replace(b"experiment-1", b"experiment-2")
    elif point == "raw_size":
        args["raw"] += b" "
    elif point == "semantic_hash":
        record = sample(w.ExperimentRecordBinding).record
        data = record.model_dump(mode="json")
        data["experiment"]["particles"][0]["position"][1] = 0.0
        args = replace_science_raw(args, canonical_json(data).encode())
    elif point == "missing_catalog":
        args["artifact"] = None
        with violation("not_found", 404):
            prepare_experiment_body(**args)
        return
    else:
        artifact = args["artifact"]
        if point == "generation":
            artifact = changed(
                artifact,
                record=changed(artifact.record, ref=changed(artifact.record.ref, generation="2")),
                verification=changed(artifact.verification, generation="2"),
            )
        elif point == "foreign":
            artifact = changed(artifact, record=changed(artifact.record, run_id="foreign"))
        elif point == "visibility":
            artifact = changed(
                artifact, record=changed(artifact.record, visibility="evaluator-only")
            )
        else:
            artifact = changed(
                artifact, verification=changed(artifact.verification, observed_at=1201)
            )
        args["artifact"] = artifact
    with violation("recovery_required", 409):
        prepare_experiment_body(**args)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"operation_id":"x","operation_id":"y"}',
        b'{"x":NaN}',
        b'{"x":1e999}',
        b'{"x":"\xff"}',
        b"[" * 33 + b"0" + b"]" * 33,
        b'{"x":1} trailing',
    ],
)
def test_strict_json_failures_after_exact_raw_identity(raw: bytes) -> None:
    with violation("invalid_request", 422):
        prepare_experiment_body(**replace_science_raw(science_args(), raw))


def test_raw_limit_precedes_decoder(monkeypatch: pytest.MonkeyPatch) -> None:
    from strange_physics import web_delivery

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("oversized raw input reached the decoder")

    monkeypatch.setattr(web_delivery, "parse_bounded_json", unexpected)
    args = science_args()
    with violation("invalid_request", 422):
        prepare_experiment_body(**(args | {"raw": b" " * (w.SCIENCE_BYTES + 1)}))


def test_alternate_valid_raw_encoding_preserves_typed_semantic_identity() -> None:
    args = science_args()
    canonical = raw_message(sample(w.ExperimentRecordBinding).record)
    assert canonical != args["raw"]
    body = prepare_experiment_body(**replace_science_raw(args, canonical))
    assert body.semantic_sha256 == args["event"].payload.record_sha256
    assert body.artifact.sha256 != args["event"].payload.artifact.sha256


@pytest.mark.parametrize("point", ["revoked", "policy", "deadline", "catalog", "request"])
def test_body_batch_reauthorization_and_state_binding(point: str) -> None:
    args = science_args()
    body = prepare_experiment_body(**args)
    kw = dict(
        context=args["context"],
        policy=args["policy"],
        namespace=args["namespace"],
        state=body,
        artifact=args["artifact"],
        request_sha256=body.request_sha256,
        now=1200,
    )
    if point == "revoked":
        kw["context"] = replace(
            args["context"], credential=changed(args["context"].credential, revoked=True)
        )
        kw.update(state=object(), artifact=object())
        code, status = "unauthenticated", 401
    elif point == "policy":
        kw["policy"] = changed(args["policy"], revision=2)
        code, status = "incompatible_state", 409
    elif point == "deadline":
        kw["now"] = body.deadline
        code, status = "incompatible_state", 409
    elif point == "catalog":
        kw["artifact"] = changed(
            args["artifact"], record=changed(args["artifact"].record, revision=2)
        )
        code, status = "recovery_required", 409
    else:
        kw["request_sha256"] = "0" * 64
        code, status = "incompatible_state", 409
    with violation(code, status):
        deliver_body_batch(**kw)
    assert body.offset == 0


def test_body_allows_renewed_readback_of_same_immutable_catalog() -> None:
    args = science_args()
    body = prepare_experiment_body(**args)
    renewed = changed(
        args["artifact"],
        verification=changed(
            args["artifact"].verification, observed_at=1200, verification_id="renewed-proof"
        ),
    )
    result = deliver_body_batch(
        args["context"],
        args["policy"],
        args["namespace"],
        state=body,
        artifact=renewed,
        request_sha256=body.request_sha256,
        now=1200,
    )
    assert result.complete


@pytest.mark.parametrize("count", [1, 2, 4])
def test_complete_history_reconstructs_exact_counts_bytes_and_watermark(count: int) -> None:
    record, pages, bodies, artifacts, current = chain(count=count)
    state = begin_history(**begin_args(record, current))
    assert not state.complete and state.after_sequence == -1
    for page, raw, artifact in zip(pages, bodies, artifacts, strict=True):
        previous = state
        state = accept_history_page(**walk_args(state), raw=raw_message(page))
        assert not state.complete and state.after_sequence == previous.after_sequence
        state = accept_history_chunk(
            **walk_args(state), requested_artifact=artifact.record.ref, artifact=artifact, raw=raw
        )
    assert state.complete and state.after_sequence == count - 1
    assert state.chunk_bytes == record.snapshot.history.total_chunk_bytes == sum(map(len, bodies))
    assert state.page_bytes == sum(len(raw_message(page)) for page in pages)
    assert len(state.seen_events) == count
    assert state.metadata_bytes > 0


@pytest.mark.parametrize("fault", ["event", "object", "page"])
def test_nonadjacent_consumed_identity_reuse_never_completes(fault: str) -> None:
    record, pages, bodies, artifacts, current = chain(count=5, fault=fault)
    state = begin_history(**begin_args(record, current))
    rejected = False
    for page, raw, artifact in zip(pages, bodies, artifacts, strict=True):
        try:
            state = accept_history_page(**walk_args(state), raw=raw_message(page))
            state = accept_history_chunk(
                **walk_args(state),
                requested_artifact=artifact.record.ref,
                artifact=artifact,
                raw=raw,
            )
        except ContractViolation as error:
            assert error.code == "recovery_required" and error.status == 409
            rejected = True
            break
    assert rejected and not state.complete
    assert state.after_sequence < 2


def test_missing_reordered_or_corrupt_history_preserves_verified_prefix() -> None:
    record, pages, bodies, artifacts, current = chain()
    state = begin_history(**begin_args(record, current))
    with violation("recovery_required", 409):
        accept_history_page(**walk_args(state), raw=raw_message(pages[1]))
    state = accept_history_page(**walk_args(state), raw=raw_message(pages[0]))
    with violation("incompatible_state", 409):
        accept_history_page(**walk_args(state), raw=raw_message(pages[1]))
    with violation("not_found", 404):
        accept_history_chunk(
            **walk_args(state),
            requested_artifact=artifacts[1].record.ref,
            artifact=artifacts[1],
            raw=bodies[1],
        )
    with violation("recovery_required", 409):
        accept_history_chunk(
            **walk_args(state),
            requested_artifact=artifacts[0].record.ref,
            artifact=artifacts[0],
            raw=bodies[0] + b" ",
        )
    assert state.after_sequence == -1 and state.chunk_bytes == 0 and not state.complete


def test_history_actual_page_overhead_counts_in_aggregate_budget() -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    policy = changed(
        sample(w.WebPolicy), max_history_bytes=record.snapshot.history.total_chunk_bytes
    )
    state = begin_history(**begin_args(record, current, policy=policy))
    # The root's raw-chunk total fits, but real page bytes do not disappear.
    with violation("quota_exceeded", 429):
        accept_history_page(**walk_args(state, policy=policy), raw=raw_message(pages[0]))
    assert state.page_bytes == 0


def test_history_metadata_ceiling_fails_before_index_growth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    state = begin_history(**begin_args(record, current))
    monkeypatch.setattr(history, "INDEX_BYTES", 1)
    with violation("quota_exceeded", 429):
        accept_history_page(**walk_args(state), raw=raw_message(pages[0]))
    assert state.seen_pages == () and state.metadata_bytes == 0


@pytest.mark.parametrize("point", ["policy", "deadline", "revoked", "snapshot", "counter"])
def test_history_every_advance_rechecks_authority_and_bound_state(point: str) -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    state = begin_history(**begin_args(record, current))
    kw = walk_args(state) | {"raw": raw_message(pages[0])}
    if point == "policy":
        kw["policy"] = changed(kw["policy"], revision=2)
        code, status = "recovery_required", 409
    elif point == "deadline":
        kw["now"] = state.deadline
        code, status = "recovery_required", 409
    elif point == "revoked":
        context = kw["context"]
        kw.update(
            context=replace(context, credential=changed(context.credential, revoked=True)),
            state=object(),
            raw=object(),
        )
        code, status = "unauthenticated", 401
    elif point == "snapshot":
        kw["requested_snapshot_id"] = "foreign-snapshot"
        code, status = "not_found", 404
    else:
        kw["state"] = replace(state, page_bytes=1)
        code, status = "recovery_required", 409
    with violation(code, status):
        accept_history_page(**kw)


def test_single_page_and_replay_body_use_actual_capture_and_raw_bytes() -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    args = begin_args(record, current)
    binding = w.HistoryPageBinding(manifest=record.snapshot.history, page=pages[0], previous=None)
    page = read_history_page(
        **args, requested_page_id=pages[0].page_id, binding=binding, raw=raw_message(pages[0])
    )
    assert page == pages[0]
    body = prepare_replay_body(
        **args,
        requested_artifact=artifacts[0].record.ref,
        page=binding,
        descriptor_index=0,
        artifact=artifacts[0],
        raw=bodies[0],
    )
    assert body.semantic_sha256 == pages[0].chunks[0].chunk_sha256 and body.offset == 0
    result = deliver_body_batch(
        args["context"],
        args["policy"],
        args["namespace"],
        state=body,
        artifact=artifacts[0],
        request_sha256=body.request_sha256,
        now=1200,
    )
    assert result.complete and result.data == bodies[0]


def test_empty_history_is_complete_without_invented_page_or_event() -> None:
    record = snapshot()
    capture = changed(
        record.snapshot,
        history=changed(
            record.snapshot.history,
            through_sequence=-1,
            last_event=None,
            page_count=0,
            chunk_count=0,
            total_chunk_bytes=0,
            first_page=None,
        ),
        resume_cursor=None,
    )
    record = changed(record, snapshot=capture, cursor=None)
    current = head(committed_through_sequence=-1, last_event=None)
    state = begin_history(**begin_args(record, current))
    assert state.complete and state.after_sequence == -1
    assert not state.seen_pages and not state.seen_objects and not state.seen_events


def large_record() -> ExperimentRecord:
    value = sample(w.ExperimentRecordBinding).record.model_dump(mode="json")
    value["experiment"]["particles"] = [
        {"id": f"p{i}" + "x" * 62, "position": [0.0, -0.0], "velocity": [0.0, 0.0], "mass": 1.0}
        for i in range(8)
    ]
    value["experiment"]["impulse"] = None
    number = -1.2345678901234567e200
    value.update(
        status="completed",
        error=None,
        trajectory={
            "frames": [
                {
                    "time": i * 0.001,
                    "positions": [[number, number]] * 8,
                    "velocities": [[number, number]] * 8,
                }
                for i in range(2001)
            ]
        },
    )
    return ExperimentRecord.model_validate_json(json.dumps(value))


def test_maximum_frame_particle_shape_fits_reference_and_is_fully_verified() -> None:
    # Maximum frame/particle counts, deliberately long finite observations;
    # this is a legal shape fixture, not a simulated or accurate physical trajectory.
    record = large_record()
    raw = raw_message(record)
    assert 1_500_000 < len(raw) <= w.SCIENCE_BYTES
    args = science_args()
    args = replace_science_raw(args, raw)
    args["event"] = changed(
        args["event"],
        payload=changed(
            args["event"].payload, status="completed", record_sha256=message_sha256(record)
        ),
    )
    body = prepare_experiment_body(**args)
    assert body.offset == 0 and body.semantic_sha256 == message_sha256(record)
    received = 0
    batches = 0
    while body.offset < len(raw):
        batch = deliver_body_batch(
            args["context"],
            args["policy"],
            args["namespace"],
            state=body,
            artifact=args["artifact"],
            request_sha256=body.request_sha256,
            now=1200,
        )
        received += len(batch.data)
        batches += 1
        assert len(batch.data) <= 65536
        body = batch.state
    assert received == len(raw) and batches == (len(raw) + 65535) // 65536


@pytest.mark.parametrize("entry", ["science", "replay", "page", "begin", "chunk"])
def test_all_material_entrypoints_authorize_before_poisoned_private_inputs(entry: str) -> None:
    context = viewer()
    context = replace(context, credential=changed(context.credential, revoked=True))
    poison: Any = object()
    common: dict[str, Any] = dict(
        context=context, policy=None, namespace=sample(w.StreamNamespace), now=1200
    )
    with violation("unauthenticated", 401):
        if entry == "science":
            prepare_experiment_body(
                **common,
                requested_event_id="bad\n",
                event=poison,
                head=poison,
                artifact=poison,
                raw=poison,
            )
        elif entry == "replay":
            prepare_replay_body(
                **common,
                requested_snapshot_id="bad\n",
                requested_artifact=poison,
                snapshot=poison,
                head=poison,
                page=poison,
                descriptor_index=0,
                artifact=poison,
                raw=poison,
            )
        elif entry == "page":
            read_history_page(
                **common,
                requested_snapshot_id="bad\n",
                requested_page_id="bad\n",
                snapshot=poison,
                head=poison,
                binding=poison,
                raw=poison,
            )
        elif entry == "begin":
            begin_history(**common, requested_snapshot_id="bad\n", snapshot=poison, head=poison)
        else:
            accept_history_chunk(
                **common,
                requested_snapshot_id="bad\n",
                requested_artifact=poison,
                state=poison,
                artifact=poison,
                raw=poison,
            )


def test_history_survives_later_run_progress_without_rebinding_space() -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    state = begin_history(**begin_args(record, current))
    context = viewer()
    assert context.run is not None
    later = replace(
        context,
        run=changed(
            context.run, revision=3, status="completed", experiments_accepted=3, budget_remaining=3
        ),
    )
    state = accept_history_page(**walk_args(state, context=later), raw=raw_message(pages[0]))
    state = accept_history_chunk(
        **walk_args(state, context=later),
        requested_artifact=artifacts[0].record.ref,
        artifact=artifacts[0],
        raw=bodies[0],
    )
    assert state.complete


@pytest.mark.parametrize("entry", ["begin", "page", "replay", "batch"])
def test_missing_private_material_has_explicit_failure(entry: str) -> None:
    record, pages, bodies, artifacts, current = chain(count=1)
    args = begin_args(record, current)
    with violation("not_found", 404):
        if entry == "begin":
            begin_history(**(args | {"snapshot": None}))
        elif entry == "page":
            read_history_page(
                **args, requested_page_id=pages[0].page_id, binding=None, raw=raw_message(pages[0])
            )
        elif entry == "replay":
            prepare_replay_body(
                **args,
                requested_artifact=artifacts[0].record.ref,
                page=None,
                descriptor_index=0,
                artifact=artifacts[0],
                raw=bodies[0],
            )
        else:
            science = science_args()
            body = prepare_experiment_body(**science)
            deliver_body_batch(
                science["context"],
                science["policy"],
                science["namespace"],
                state=body,
                artifact=None,
                request_sha256=body.request_sha256,
                now=1200,
            )
