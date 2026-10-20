"""Whole-object validation and bounded raw delivery over current viewer authority.

The immutable body state is private producer state, not a bearer capability.
No object store fetch, URL, HTTP response or network loop is implemented here.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Literal

from pydantic import ValidationError

from strange_physics.artifact_contracts import ArtifactRef, RunArtifactRecord, VerifiedArtifact
from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import ExperimentRecord
from strange_physics.control_contracts import ContractViolation, RunView
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.web_access import ViewerContext, authorize_viewer, check_run_capture
from strange_physics.web_contracts import (
    MAX_SAFE,
    EventIdentity,
    ExperimentRecordBinding,
    ExperimentRecordRef,
    HistoryPageBinding,
    ReplayChunk,
    ReplayChunkBinding,
    ReplayChunkRef,
    RunEvent,
    SnapshotRecord,
    StreamHead,
    StreamNamespace,
    WebPolicy,
)
from strange_physics.web_replay import _event, _head, _snapshot, _token


@dataclass(frozen=True)
class VerifiedBody:
    """Only returned after full byte and typed verification; no payload is delivered yet."""

    namespace: StreamNamespace
    kind: Literal["experiment", "replay"]
    request_sha256: str
    captured_run: RunView
    policy_sha256: str
    artifact: ArtifactRef
    catalog: RunArtifactRecord
    semantic_sha256: str
    raw: bytes
    offset: int
    started_at: int
    deadline: int


@dataclass(frozen=True)
class BodyBatch:
    data: bytes
    state: VerifiedBody
    complete: bool


def _catalog(
    namespace: StreamNamespace,
    expected: ArtifactRef,
    current: VerifiedArtifact | None,
    *,
    limit: int,
    now: int,
) -> None:
    if current is None:
        raise ContractViolation("not_found", 404)
    catalog = current.record
    if (
        catalog.state != "available"
        or catalog.visibility != "agent-visible"
        or (catalog.workspace_id, catalog.run_id) != (namespace.workspace_id, namespace.run_id)
        or catalog.ref != expected
        or current.verification.observed_at > now
    ):
        raise ContractViolation("recovery_required", 409)
    if expected.media_type != "application/json" or not 1 <= expected.size_bytes <= limit:
        raise ContractViolation("quota_exceeded", 429)


def _raw(raw: bytes, ref: ArtifactRef, limit: int) -> None:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= limit:
        raise ContractViolation("invalid_request", 422)
    if len(raw) != ref.size_bytes or hashlib.sha256(raw).hexdigest() != ref.sha256:
        raise ContractViolation("recovery_required", 409)


def _parse_chunk(
    namespace: StreamNamespace,
    descriptor: ReplayChunkRef,
    artifact: VerifiedArtifact | None,
    raw: bytes,
    configured: WebPolicy,
    now: int,
) -> ReplayChunk:
    """Incomplete material check shared by complete history/body entrypoints."""
    _catalog(namespace, descriptor.artifact, artifact, limit=configured.max_chunk_bytes, now=now)
    assert artifact is not None
    _raw(raw, descriptor.artifact, configured.max_chunk_bytes)
    chunk = parse_bounded_json(
        raw, ReplayChunk, max_bytes=configured.max_chunk_bytes, max_depth=32, max_nodes=1_000_000
    )
    try:
        ReplayChunkBinding(descriptor=descriptor, artifact=artifact, chunk=chunk)
    except ValidationError:
        raise ContractViolation("recovery_required", 409) from None
    if len(chunk.events) > configured.max_chunk_events:
        raise ContractViolation("quota_exceeded", 429)
    return chunk


def _body(
    context: ViewerContext,
    namespace: StreamNamespace,
    configured: WebPolicy,
    *,
    kind: Literal["experiment", "replay"],
    request_sha256: str,
    ref: ArtifactRef,
    catalog: RunArtifactRecord,
    semantic_sha256: str,
    raw: bytes,
    now: int,
) -> VerifiedBody:
    assert context.run is not None
    if now == MAX_SAFE:
        raise ContractViolation("quota_exceeded", 429)
    return VerifiedBody(
        namespace=namespace,
        kind=kind,
        request_sha256=request_sha256,
        captured_run=context.run,
        policy_sha256=message_sha256(configured),
        artifact=ref,
        catalog=catalog,
        semantic_sha256=semantic_sha256,
        raw=raw,
        offset=0,
        started_at=now,
        deadline=min(MAX_SAFE, now + configured.max_delivery_seconds),
    )


def prepare_experiment_body(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_event_id: str,
    event: RunEvent | None,
    head: StreamHead | None,
    artifact: VerifiedArtifact | None,
    raw: bytes,
    now: int,
) -> VerifiedBody:
    configured = authorize_viewer(context, policy, namespace, now=now)
    _token(requested_event_id)
    current = _head(context, namespace, head, now)
    if event is None or event.event_id != requested_event_id:
        raise ContractViolation("not_found", 404)
    _event(event, current, context, now)
    # This branch is deliberately after complete current authority and committed-event binding.
    ref = event.payload
    if not isinstance(ref, ExperimentRecordRef):
        raise ContractViolation("not_found", 404)
    _catalog(namespace, ref.artifact, artifact, limit=configured.max_science_bytes, now=now)
    assert artifact is not None
    _raw(raw, ref.artifact, configured.max_science_bytes)
    record = parse_bounded_json(
        raw,
        ExperimentRecord,
        max_bytes=configured.max_science_bytes,
        max_depth=32,
        max_nodes=1_000_000,
    )
    try:
        ExperimentRecordBinding(event=event, artifact=artifact, record=record)
    except ValidationError:
        raise ContractViolation("recovery_required", 409) from None
    return _body(
        context,
        namespace,
        configured,
        kind="experiment",
        request_sha256=message_sha256(event),
        ref=ref.artifact,
        catalog=artifact.record,
        semantic_sha256=message_sha256(record),
        raw=raw,
        now=now,
    )


def prepare_replay_body(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    requested_snapshot_id: str,
    requested_artifact: ArtifactRef,
    snapshot: SnapshotRecord | None,
    head: StreamHead | None,
    page: HistoryPageBinding | None,
    descriptor_index: int,
    artifact: VerifiedArtifact | None,
    raw: bytes,
    now: int,
) -> VerifiedBody:
    configured = authorize_viewer(context, policy, namespace, now=now)
    _token(requested_snapshot_id)
    current = _head(context, namespace, head, now)
    captured = _snapshot(context, configured, namespace, snapshot, current, now)
    if captured.snapshot_id != requested_snapshot_id or page is None:
        raise ContractViolation("not_found", 404)
    if message_sha256(page.manifest) != message_sha256(captured.history):
        raise ContractViolation("recovery_required", 409)
    if type(descriptor_index) is not int or not 0 <= descriptor_index < len(page.page.chunks):
        raise ContractViolation("invalid_request", 422)
    descriptor = page.page.chunks[descriptor_index]
    if descriptor.artifact != requested_artifact:
        raise ContractViolation("not_found", 404)
    if len(page.page.chunks) > configured.max_page_refs:
        raise ContractViolation("quota_exceeded", 429)
    bounded_canonical(page.page, configured.max_page_bytes)
    chunk = _parse_chunk(namespace, descriptor, artifact, raw, configured, now)
    assert artifact is not None
    for event in chunk.events:
        _event(event, current, context, now)
        if event.occurred_at > captured.captured_at or (
            captured.history.last_event is not None
            and event.event_id == captured.history.last_event.event_id
            and EventIdentity.from_event(event) != captured.history.last_event
        ):
            raise ContractViolation("recovery_required", 409)
        if isinstance(event.payload, RunView):
            check_run_capture(event.payload, captured.run)
    return _body(
        context,
        namespace,
        configured,
        kind="replay",
        request_sha256=hashlib.sha256(
            canonical_json(
                {
                    "purpose": "web.replay-body.v1",
                    "snapshot_id": requested_snapshot_id,
                    "snapshot_sha256": message_sha256(captured),
                    "page_binding_sha256": message_sha256(page),
                    "descriptor_index": descriptor_index,
                    "artifact": requested_artifact.model_dump(mode="json"),
                }
            ).encode("utf-8")
        ).hexdigest(),
        ref=descriptor.artifact,
        catalog=artifact.record,
        semantic_sha256=message_sha256(chunk),
        raw=raw,
        now=now,
    )


def deliver_body_batch(
    context: ViewerContext,
    policy: WebPolicy | None,
    namespace: StreamNamespace,
    *,
    state: VerifiedBody,
    artifact: VerifiedArtifact | None,
    request_sha256: str,
    now: int,
) -> BodyBatch:
    configured = authorize_viewer(context, policy, namespace, now=now)
    assert context.run is not None
    check_run_capture(state.captured_run, context.run)
    if (
        state.kind not in {"experiment", "replay"}
        or state.namespace != namespace
        or state.request_sha256 != request_sha256
        or state.policy_sha256 != message_sha256(configured)
        or not state.started_at <= now < state.deadline
        or state.deadline > min(MAX_SAFE, state.started_at + configured.max_delivery_seconds)
        or type(state.offset) is not int
        or not 0 <= state.offset <= len(state.raw)
    ):
        raise ContractViolation("incompatible_state", 409)
    limit = (
        configured.max_science_bytes if state.kind == "experiment" else configured.max_chunk_bytes
    )
    _catalog(namespace, state.artifact, artifact, limit=limit, now=now)
    assert artifact is not None
    if message_sha256(state.catalog) != message_sha256(artifact.record):
        raise ContractViolation("recovery_required", 409)
    _raw(state.raw, state.artifact, limit)
    end = min(len(state.raw), state.offset + configured.max_body_batch_bytes)
    data = state.raw[state.offset : end]
    after = replace(state, offset=end)
    return BodyBatch(data=data, state=after, complete=end == len(state.raw))
