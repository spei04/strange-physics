"""WEB1 intrinsic wire, capture, provenance and completeness boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from strange_physics import web_contracts as w
from strange_physics.contracts import Message
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/web.examples.json").read_text())
MODELS = {model.__name__: model for model in w.WEB_MODELS}


def fixture(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], copy.deepcopy(FIXTURES["valid"][name]))


def parse(name: str, value: Any) -> Message:
    return MODELS[name].model_validate_json(json.dumps(value, allow_nan=False))


@pytest.mark.parametrize("name", sorted(MODELS))
def test_fixture_round_trip(name: str) -> None:
    result = parse(name, fixture(name))
    assert result.model_dump(mode="json") == fixture(name)


@pytest.mark.parametrize("case", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_invalid_fixtures(case: dict[str, Any]) -> None:
    value = fixture(case["model"])
    value[case["field"]] = case["value"]
    with pytest.raises(ValidationError):
        parse(case["model"], value)


def test_schema_is_generated_and_public_closure_is_safe() -> None:
    schema = json.loads((ROOT / "contracts/web.schema.json").read_text())
    assert schema == w.web_json_schema()
    definitions = schema["$defs"]
    forbidden = {
        "noise_seed",
        "initial_law",
        "changed_law",
        "definition_sha256",
        "locator",
        "object_key",
        "principal_id",
        "recipient_principal_id",
        "credential_id",
        "session_id",
        "world_definition",
        "reference_artifact",
        "policy_sha256",
    }
    seen: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            assert not forbidden.intersection(value.get("properties", {}))
            if "$ref" in value:
                name = value["$ref"].rsplit("/", 1)[-1]
                if name not in seen:
                    seen.add(name)
                    walk(definitions[name])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for name in schema["x-public-models"]:
        walk(definitions[name])
    assert not {"EventCursor", "SnapshotRecord", "VerifiedArtifact", "WebPolicy"} & seen


@pytest.mark.parametrize("index", range(4))
def test_event_discriminator_requires_exact_payload(index: int) -> None:
    value = copy.deepcopy(FIXTURES["events"][index])
    parse("RunEvent", value)
    value["payload"] = copy.deepcopy(FIXTURES["events"][(index + 1) % 4]["payload"])
    with pytest.raises(ValidationError):
        parse("RunEvent", value)


@pytest.mark.parametrize("token", ["", "\r", "\n", "\0", "abc\n", "a\rb", "a\0b", "é", "a" * 65])
@pytest.mark.parametrize("field", ["resume_cursor", "event_id"])
def test_no_sse_framing_injection(token: str, field: str) -> None:
    value = fixture("EventDelivery")
    if field == "resume_cursor":
        value[field] = token
    else:
        value["event"][field] = token
    with pytest.raises(ValidationError):
        parse("EventDelivery", value)


def test_exact_sse_utf8_framing_and_hash_domain() -> None:
    for event, expected in zip(FIXTURES["events"], FIXTURES["sse"], strict=True):
        value = w.RunEvent.model_validate_json(json.dumps(event))
        delivery = w.EventDelivery(
            event=value,
            event_sha256=message_sha256(value),
            resume_cursor=f"cursor-{value.sequence}",
        )
        wire = delivery.sse_bytes()
        assert wire == expected.encode("utf-8")
        assert wire.startswith(f"id: cursor-{value.sequence}\nevent: {value.type}\ndata: ".encode())
        assert wire.count(b"\n") == 4 and wire.endswith(b"\n\n")
        data = wire.split(b"data: ", 1)[1][:-2]
        assert data == canonical_json(delivery.model_dump(mode="json")).encode()
        assert (
            hashlib.sha256(canonical_json(value.model_dump(mode="json")).encode()).hexdigest()
            == delivery.event_sha256
        )
        assert len(wire) <= w.EVENT_BYTES
    assert FIXTURES["sse"][0].startswith("id: cursor-0\n")
    assert '"sequence":0' in FIXTURES["sse"][0]


@pytest.mark.parametrize("count", [-1, True, 2**53])
def test_js_unsafe_or_boolean_sequences_reject(count: int) -> None:
    value = fixture("RunEvent")
    value["sequence"] = count
    with pytest.raises(ValidationError):
        parse("RunEvent", value)


@pytest.mark.parametrize("count", [0, 2**53 - 1])
def test_sequence_endpoints_are_lossless(count: int) -> None:
    value = fixture("RunEvent")
    value["sequence"] = count
    event = parse("RunEvent", value)
    assert event.model_dump(mode="json")["sequence"] == count


def test_empty_head_cursor_and_snapshot_boundaries() -> None:
    head = fixture("StreamHead")
    head.update(committed_through_sequence=-1, retained_from_sequence=0, last_event=None)
    parse("StreamHead", head)
    cursor = fixture("EventCursor")
    cursor.update(after_sequence=-1, event=None, snapshot_id=None, snapshot_sha256=None)
    parse("EventCursor", cursor)
    snap = fixture("RunSnapshot")
    snap["history"].update(
        through_sequence=-1,
        last_event=None,
        page_count=0,
        chunk_count=0,
        total_chunk_bytes=0,
        first_page=None,
    )
    snap["resume_cursor"] = None
    parse("SnapshotRecord", {"snapshot": snap, "cursor": None})
    for field, wrong in [("retained_from_sequence", 1), ("last_event", fixture("EventIdentity"))]:
        with pytest.raises(ValidationError):
            parse("StreamHead", head | {field: wrong})
    with pytest.raises(ValidationError):
        parse("SnapshotRecord", {"snapshot": snap, "cursor": cursor})


@pytest.mark.parametrize("point", ["namespace", "sequence", "event", "expiry", "half_snapshot"])
def test_cursor_intrinsic_joins(point: str) -> None:
    value = fixture("EventCursor")
    if point == "namespace":
        value["event"]["namespace"]["run_id"] = "foreign"
    elif point == "sequence":
        value["event"]["sequence"] -= 1
    elif point == "event":
        value["event"] = None
    elif point == "expiry":
        value["expires_at"] = value["issued_at"]
    else:
        value["snapshot_sha256"] = None
    with pytest.raises(ValidationError):
        parse("EventCursor", value)


@pytest.mark.parametrize("point", ["id", "hash", "event", "namespace", "before_capture"])
def test_snapshot_cursor_binds_actual_capture(point: str) -> None:
    value = fixture("SnapshotRecord")
    cursor = value["cursor"]
    if point == "id":
        cursor["snapshot_id"] = "different"
    elif point == "hash":
        cursor["snapshot_sha256"] = "0" * 64
    elif point == "event":
        cursor["event"]["event_sha256"] = "0" * 64
    elif point == "namespace":
        cursor["namespace"]["run_id"] = "different"
        cursor["event"]["namespace"]["run_id"] = "different"
    else:
        cursor["issued_at"] = value["snapshot"]["captured_at"] - 1
    with pytest.raises(ValidationError):
        parse("SnapshotRecord", value)


@pytest.mark.parametrize(
    "status", ["queued", "running", "recovering", "completed", "failed", "expired", "cancelled"]
)
def test_capture_does_not_require_live_worker_or_running_status(status: str) -> None:
    value = fixture("RunSnapshot")
    value["run"]["status"] = status
    snapshot = w.RunSnapshot.model_validate_json(json.dumps(value))
    cursor = fixture("EventCursor")
    cursor["snapshot_sha256"] = message_sha256(snapshot)
    parse("SnapshotRecord", {"snapshot": snapshot.model_dump(mode="json"), "cursor": cursor})
    # Later state is independent; this historical immutable capture still validates.
    later = copy.deepcopy(value["run"])
    later.update(status="completed", revision=100)
    assert snapshot.run.revision != later["revision"]


@pytest.mark.parametrize("point", ["gap", "reorder", "duplicate_id", "namespace", "time"])
@pytest.mark.parametrize("model", ["ReplayChunk", "EventBatch"])
def test_contiguous_committed_events(point: str, model: str) -> None:
    value = fixture(model)
    events = (
        value["events"] if model == "ReplayChunk" else [d["event"] for d in value["deliveries"]]
    )
    if point == "gap":
        events[1]["sequence"] += 1
    elif point == "reorder":
        events[0]["sequence"], events[1]["sequence"] = events[1]["sequence"], events[0]["sequence"]
    elif point == "duplicate_id":
        events[1]["event_id"] = events[0]["event_id"]
    elif point == "namespace":
        events[0]["namespace"]["run_id"] = "foreign"
    else:
        events[1]["occurred_at"] -= 1
    if model == "EventBatch":
        for delivery in value["deliveries"]:
            delivery["event_sha256"] = message_sha256(
                w.RunEvent.model_validate_json(json.dumps(delivery["event"]))
            )
    with pytest.raises(ValidationError):
        parse(model, value)


def history_pages() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    chunks = []
    for index in range(2):
        events = tuple(
            w.RunEvent.model_validate_json(json.dumps(e))
            for e in FIXTURES["events"][index * 2 : index * 2 + 2]
        )
        chunk = w.ReplayChunk(
            namespace=events[0].namespace,
            first_sequence=events[0].sequence,
            last_sequence=events[-1].sequence,
            events=events,
        )
        body = canonical_json(chunk.model_dump(mode="json")).encode()
        descriptor = fixture("ReplayChunkRef")
        descriptor.update(
            first_sequence=chunk.first_sequence,
            last_sequence=chunk.last_sequence,
            event_count=2,
            first_event=w.EventIdentity.from_event(events[0]).model_dump(mode="json"),
            last_event=w.EventIdentity.from_event(events[-1]).model_dump(mode="json"),
            chunk_sha256=message_sha256(chunk),
        )
        descriptor["artifact"].update(
            artifact_id=f"chunk-{index}",
            size_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
        chunks.append(descriptor)
    second = fixture("HistoryPage") | {
        "page_id": "page-2",
        "page_index": 1,
        "first_chunk_index": 1,
        "chunks": [chunks[1]],
    }
    second_model = w.HistoryPage.model_validate_json(json.dumps(second))
    first = fixture("HistoryPage") | {
        "chunks": [chunks[0]],
        "next_page": {"page_id": "page-2", "page_sha256": message_sha256(second_model)},
    }
    first_model = w.HistoryPage.model_validate_json(json.dumps(first))
    root = fixture("HistoryManifest") | {
        "page_count": 2,
        "chunk_count": 2,
        "total_chunk_bytes": sum(c["artifact"]["size_bytes"] for c in chunks),
        "first_page": {"page_id": "page-1", "page_sha256": message_sha256(first_model)},
    }
    return root, first, second


def test_bounded_page_chain_handoff() -> None:
    root, first, second = history_pages()
    parse("HistoryPageBinding", {"manifest": root, "page": first, "previous": None})
    parse("HistoryPageBinding", {"manifest": root, "page": second, "previous": first})
    assert first["chunks"][-1]["last_sequence"] + 1 == second["chunks"][0]["first_sequence"]


@pytest.mark.parametrize(
    "point",
    [
        "missing",
        "wrong_hash",
        "foreign",
        "wrong_index",
        "gap",
        "wrong_final_event",
        "wrong_total",
        "first_substitution",
    ],
)
def test_page_chain_missing_corrupt_or_misassociated(point: str) -> None:
    root, first, second = history_pages()
    value: dict[str, Any] = {"manifest": root, "page": second, "previous": first}
    if point == "missing":
        value["previous"] = None
    elif point == "wrong_hash":
        first["next_page"]["page_sha256"] = "0" * 64
    elif point == "foreign":
        second["manifest_id"] = "different"
    elif point == "wrong_index":
        second["page_index"] = 2
    elif point == "gap":
        second["first_chunk_index"] = 2
    elif point == "wrong_final_event":
        root["last_event"]["event_sha256"] = "0" * 64
    elif point == "wrong_total":
        root["chunk_count"] = 3
    else:
        value.update(page=first, previous=None)
        root["first_page"]["page_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        parse("HistoryPageBinding", value)


@pytest.mark.parametrize("model", ["ReplayChunkBinding", "ExperimentRecordBinding"])
@pytest.mark.parametrize(
    "point", ["workspace", "run", "generation", "visibility", "state", "raw_hash", "semantic_hash"]
)
def test_raw_catalog_and_semantic_joins(model: str, point: str) -> None:
    value = fixture(model)
    catalog = value["artifact"]["record"]
    proof = value["artifact"]["verification"]
    if point in {"workspace", "run"}:
        catalog[point + "_id"] = "foreign"
    elif point == "generation":
        catalog["ref"]["generation"] = proof["generation"] = "2"
    elif point == "visibility":
        catalog["visibility"] = "evaluator-only"
    elif point == "state":
        catalog["state"] = "deleted"
    elif point == "raw_hash":
        catalog["ref"]["sha256"] = proof["sha256"] = "0" * 64
    elif model == "ReplayChunkBinding":
        value["descriptor"]["chunk_sha256"] = "0" * 64
    else:
        value["event"]["payload"]["record_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        parse(model, value)


def test_scientific_failure_is_complete_record_not_transport_success() -> None:
    value = fixture("ExperimentRecordBinding")
    result = w.ExperimentRecordBinding.model_validate_json(json.dumps(value))
    assert result.record.status == "failed" and result.record.trajectory is None
    assert isinstance(result.event.payload, w.ExperimentRecordRef)
    assert result.event.payload.status == "failed"
    value["record"]["experiment"]["particles"][0]["position"][1] = 0.0
    with pytest.raises(ValidationError):
        parse("ExperimentRecordBinding", value)  # Canonical signed-zero identity differs.


def test_raw_encoding_is_distinct_from_typed_identity() -> None:
    value = fixture("ExperimentRecordBinding")
    record = value["record"]
    raw = FIXTURES["raw_record"].encode()
    canonical = canonical_json(record).encode()
    assert hashlib.sha256(raw).hexdigest() != hashlib.sha256(canonical).hexdigest()
    assert hashlib.sha256(raw).hexdigest() == value["artifact"]["record"]["ref"]["sha256"]
    assert hashlib.sha256(canonical).hexdigest() == value["event"]["payload"]["record_sha256"]
    digest = hashlib.sha256(canonical).hexdigest()
    for ref in (value["artifact"]["record"]["ref"], value["event"]["payload"]["artifact"]):
        ref.update(size_bytes=len(canonical), sha256=digest)
    value["artifact"]["verification"].update(size_bytes=len(canonical), sha256=digest)
    parse("ExperimentRecordBinding", value)


def large_run_event(sequence: int) -> w.RunEvent:
    value = copy.deepcopy(FIXTURES["events"][1])
    ids = [f"p{i}" + "x" * 62 for i in range(8)]
    anchors = [f"a{i}" + "y" * 62 for i in range(8)]
    names = ids + anchors
    value["payload"]["space"]["structure"] = {
        "particle_ids": ids,
        "anchors": [{"id": name, "position": [0.0, -0.0]} for name in anchors],
        "connections": [
            {"a": a, "b": b}
            for i, a in enumerate(names)
            for b in names[i + 1 :]
            if a in ids or b in ids
        ],
    }
    value.update(sequence=sequence, event_id=f"large-{sequence}")
    return w.RunEvent.model_validate_json(json.dumps(value))


def test_batch_cap_counts_actual_framing_overhead() -> None:
    deliveries = []
    for index in range(100):
        event = large_run_event(index)
        item = w.EventDelivery(
            event=event, event_sha256=message_sha256(event), resume_cursor=f"large-cursor-{index}"
        )
        deliveries.append(item)
        total = sum(len(d.sse_bytes()) for d in deliveries)
        if total > w.BATCH_BYTES:
            with pytest.raises(ValidationError):
                w.EventBatch(deliveries=tuple(deliveries))
            w.EventBatch(deliveries=tuple(deliveries[:-1]))
            assert total - len(item.sse_bytes()) <= w.BATCH_BYTES
            break
    else:
        pytest.fail("The legal maximum-shape fixture must exercise the wire batch limit")


def test_chunk_count_and_encoded_byte_caps() -> None:
    base = fixture("ReplayChunk")
    base["events"] = [FIXTURES["events"][0]] * 257
    with pytest.raises(ValidationError):
        parse("ReplayChunk", base)
    events = tuple(large_run_event(index) for index in range(256))
    # This independently accounts for actual braces, commas, keys and typed float spelling.
    raw = canonical_json(
        {
            "schema_version": "strange-physics.replay-chunk.v1",
            "namespace": events[0].namespace.model_dump(mode="json"),
            "first_sequence": 0,
            "last_sequence": 255,
            "events": [e.model_dump(mode="json") for e in events],
        }
    ).encode()
    if len(raw) > w.CHUNK_BYTES:
        with pytest.raises(ValidationError):
            w.ReplayChunk(
                namespace=events[0].namespace, first_sequence=0, last_sequence=255, events=events
            )
    else:
        chunk = w.ReplayChunk(
            namespace=events[0].namespace, first_sequence=0, last_sequence=255, events=events
        )
        assert len(raw) == len(canonical_json(chunk.model_dump(mode="json")).encode())


def test_partial_lookup_is_not_silently_normalized_to_absence() -> None:
    original = fixture("CursorLookup")
    for field in ("head", "cursor", "event", "snapshot"):
        value = original | {field: None}
        lookup = w.CursorLookup.model_validate_json(json.dumps(value))
        assert lookup.model_dump(mode="json")[field] is None
        assert (
            sum(getattr(lookup, k) is not None for k in ("head", "cursor", "event", "snapshot"))
            == 3
        )


def test_openapi_transport_and_error_contract() -> None:
    api = json.loads((ROOT / "contracts/web.openapi.json").read_text())
    assert len(api["paths"]) == 5
    for routes in api["paths"].values():
        assert set(routes) == {"get"}
        operation = routes["get"]
        assert operation["security"] == [{"sessionCookie": []}, {"workspaceBearer": []}]
        assert operation["x-required-scope"] == "runs:read"
        assert operation["x-implementation-status"] == "not-implemented"
        assert {"400", "401", "403", "404", "409", "422", "429", "503"} <= set(
            operation["responses"]
        )
        assert "Retry-After" in operation["responses"]["429"]["headers"]
        assert "runBearer" not in json.dumps(operation)
        if operation["operationId"] != "getRunExperimentRecord":
            resync = operation["responses"]["410"]
            assert set(resync["content"]) == {"application/json"}
            assert resync["content"]["application/json"]["schema"]["$ref"].endswith(
                "/ResyncRequired"
            )
        if operation["operationId"] == "streamRunEvents":
            token = next(p for p in operation["parameters"] if p["name"] == "Last-Event-ID")
            assert token["in"] == "header" and not token["required"]
            response = operation["responses"]["200"]
            assert response["x-event-schema"]["$ref"].endswith("/EventDelivery")
            assert response["content"]["text/event-stream"]["example"] == FIXTURES["sse"][0]
    assert (
        "service identity only"
        in api["components"]["securitySchemes"]["workspaceBearer"]["description"]
    )
    draft = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    assert (
        draft["components"]["schemas"]["RunEvent"]["$ref"] == "../web.schema.json#/$defs/RunEvent"
    )
    assert (
        "user/service"
        not in draft["components"]["securitySchemes"]["workspaceBearer"]["description"]
    )
    assert "web.schema.json" in json.dumps(
        draft["paths"][next(path for path in draft["paths"] if path.endswith("/events"))]
    )


@pytest.mark.parametrize(
    "point", ["total_below", "total_above_complete", "boundary_id_reuse", "repeated_artifact"]
)
def test_available_page_witnesses_cannot_contradict_root(point: str) -> None:
    root, first, second = history_pages()
    if point == "total_below":
        root["total_chunk_bytes"] -= 1
    elif point == "total_above_complete":
        root["total_chunk_bytes"] += 1
    elif point == "boundary_id_reuse":
        second["chunks"][0]["first_event"]["event_id"] = first["chunks"][0]["first_event"][
            "event_id"
        ]
        second_model = w.HistoryPage.model_validate_json(json.dumps(second))
        first["next_page"]["page_sha256"] = message_sha256(second_model)
    else:
        second["chunks"][0]["artifact"] = copy.deepcopy(first["chunks"][0]["artifact"])
        second_model = w.HistoryPage.model_validate_json(json.dumps(second))
        first["next_page"]["page_sha256"] = message_sha256(second_model)
        root["total_chunk_bytes"] = sum(
            page["chunks"][0]["artifact"]["size_bytes"] for page in [first, second]
        )
    with pytest.raises(ValidationError):
        parse("HistoryPageBinding", {"manifest": root, "page": second, "previous": first})


@pytest.mark.parametrize(
    "field",
    [
        "max_event_bytes",
        "max_batch_events",
        "max_chunk_bytes",
        "max_page_refs",
        "max_history_pages",
        "max_delivery_seconds",
        "max_science_bytes",
        "max_body_batch_bytes",
        "cursor_ttl_seconds",
    ],
)
@pytest.mark.parametrize("bad", [0, True])
def test_required_policy_bounds_are_strict(field: str, bad: int) -> None:
    value = fixture("WebPolicy")
    value[field] = bad
    with pytest.raises(ValidationError):
        parse("WebPolicy", value)


@pytest.mark.parametrize("point", ["false_retry", "wrong_code", "operation"])
def test_resync_does_not_claim_mutation_or_blind_retry(point: str) -> None:
    value = fixture("ResyncRequired")
    if point == "false_retry":
        value["error"]["retryable"] = True
    elif point == "wrong_code":
        value["error"]["code"] = "unauthenticated"
    else:
        value["error"]["operation_id"] = "private-operation"
    with pytest.raises(ValidationError):
        parse("ResyncRequired", value)


def page_chain(
    counts: tuple[int, ...] = (1, 1, 1, 1),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    namespace = w.StreamNamespace.model_validate_json(json.dumps(fixture("StreamNamespace")))
    chunks: list[dict[str, Any]] = []
    for index in range(sum(counts)):
        event_data = copy.deepcopy(FIXTURES["events"][2])
        event_data.update(event_id=f"chain-event-{index}", sequence=index)
        event_data["payload"]["checkpoint_id"] = f"chain-checkpoint-{index}"
        event = w.RunEvent.model_validate_json(json.dumps(event_data))
        chunk = w.ReplayChunk(
            namespace=namespace, first_sequence=index, last_sequence=index, events=(event,)
        )
        raw = canonical_json(chunk.model_dump(mode="json")).encode()
        descriptor = fixture("ReplayChunkRef")
        identity = w.EventIdentity.from_event(event).model_dump(mode="json")
        descriptor.update(
            first_sequence=index,
            last_sequence=index,
            event_count=1,
            first_event=identity,
            last_event=copy.deepcopy(identity),
            chunk_sha256=message_sha256(chunk),
        )
        descriptor["artifact"].update(
            artifact_id=f"chain-chunk-{index}",
            sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),
        )
        chunks.append(descriptor)
    pages: list[dict[str, Any]] = []
    offset = 0
    for index, count in enumerate(counts):
        pages.append(
            fixture("HistoryPage")
            | {
                "page_id": f"chain-page-{index}",
                "through_sequence": len(chunks) - 1,
                "page_index": index,
                "first_chunk_index": offset,
                "chunks": chunks[offset : offset + count],
                "next_page": None,
            }
        )
        offset += count
    for index in reversed(range(len(pages) - 1)):
        next_page = w.HistoryPage.model_validate_json(json.dumps(pages[index + 1]))
        pages[index]["next_page"] = {
            "page_id": next_page.page_id,
            "page_sha256": message_sha256(next_page),
        }
    first = w.HistoryPage.model_validate_json(json.dumps(pages[0]))
    root = fixture("HistoryManifest") | {
        "through_sequence": len(chunks) - 1,
        "last_event": chunks[-1]["last_event"],
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "total_chunk_bytes": sum(c["artifact"]["size_bytes"] for c in chunks),
        "first_page": {"page_id": first.page_id, "page_sha256": message_sha256(first)},
    }
    return root, pages


@pytest.mark.parametrize("counts", [(1,), (1, 1), (1, 2, 1), (2, 1, 2, 1, 1)])
def test_all_available_links_in_valid_bounded_chains(counts: tuple[int, ...]) -> None:
    root, pages = page_chain(counts)
    for index, page in enumerate(pages):
        parse(
            "HistoryPageBinding",
            {"manifest": root, "page": page, "previous": None if index == 0 else pages[index - 1]},
        )


@pytest.mark.parametrize("point", ["id", "hash"])
def test_supplied_first_predecessor_must_match_root(point: str) -> None:
    root, pages = page_chain()
    if point == "id":
        pages[0]["page_id"] = "substituted-first"
    else:
        root["first_page"]["page_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        parse("HistoryPageBinding", {"manifest": root, "page": pages[1], "previous": pages[0]})


@pytest.mark.parametrize("point", ["current_root", "previous_root", "next_root", "next_previous"])
def test_known_page_id_ordinal_reuse(point: str) -> None:
    root, pages = page_chain((1, 1, 1, 1, 1))
    index = 3 if point in {"current_root", "previous_root"} else 2
    page, previous = pages[index], pages[index - 1]
    if point == "current_root":
        page["page_id"] = root["first_page"]["page_id"]
    elif point == "previous_root":
        previous["page_id"] = root["first_page"]["page_id"]
    elif point == "next_root":
        page["next_page"]["page_id"] = root["first_page"]["page_id"]
    else:
        page["next_page"]["page_id"] = previous["page_id"]
    actual = w.HistoryPage.model_validate_json(json.dumps(page))
    previous["next_page"] = {"page_id": actual.page_id, "page_sha256": message_sha256(actual)}
    with pytest.raises(ValidationError):
        parse("HistoryPageBinding", {"manifest": root, "page": page, "previous": previous})


def test_known_final_event_cannot_reuse_earlier_supplied_identity() -> None:
    root, pages = page_chain()
    root["last_event"]["event_id"] = pages[0]["chunks"][0]["first_event"]["event_id"]
    with pytest.raises(ValidationError):
        parse("HistoryPageBinding", {"manifest": root, "page": pages[1], "previous": pages[0]})


@pytest.mark.parametrize("offset", [-1, 0, 1])
@pytest.mark.parametrize("boundary", ["minimum", "maximum"])
def test_remaining_raw_bytes_must_be_feasible(boundary: str, offset: int) -> None:
    root, pages = page_chain()
    known = sum(c["artifact"]["size_bytes"] for page in pages[:2] for c in page["chunks"])
    missing = 2
    root["total_chunk_bytes"] = (
        known + (missing if boundary == "minimum" else missing * w.CHUNK_BYTES) + offset
    )
    value = {"manifest": root, "page": pages[1], "previous": pages[0]}
    bad = (boundary == "minimum" and offset < 0) or (boundary == "maximum" and offset > 0)
    if bad:
        with pytest.raises(ValidationError):
            parse("HistoryPageBinding", value)
    else:
        parse("HistoryPageBinding", value)


@pytest.mark.parametrize("point", ["prior_pages", "prior_events", "remaining_pages"])
def test_missing_chunk_and_event_offsets_must_be_feasible(point: str) -> None:
    root, pages = page_chain((1, 3, 1, 1))
    if point == "remaining_pages":
        root["page_count"] = 5
        with pytest.raises(ValidationError):
            parse("HistoryPageBinding", {"manifest": root, "page": pages[1], "previous": pages[0]})
        return
    value = pages[3]
    value["first_chunk_index"] = 2 if point == "prior_pages" else 6
    with pytest.raises(ValidationError):
        parse("HistoryPage", value)


@pytest.mark.parametrize(
    "token", ["0", "1", "9999999999", "1\n", "0\n", "1\r\n", "-1", "+1", "01", "1e2", "١"]
)
def test_retry_after_external_schema_is_canonical_ascii(token: str) -> None:
    api = json.loads((ROOT / "contracts/web.openapi.json").read_text())
    for methods in api["paths"].values():
        schema = methods["get"]["responses"]["429"]["headers"]["Retry-After"]["schema"]
        assert schema["not"] == {"pattern": "[^0-9]"}
    # The dependency-free test checks the same lexical wire profile. The external
    # validator separately executes JSON Schema against each positive and negative.
    import re

    good = token in {"0", "1", "9999999999"}
    schema = next(iter(api["paths"].values()))["get"]["responses"]["429"]["headers"]["Retry-After"][
        "schema"
    ]
    accepted = (
        re.fullmatch(schema["pattern"], token) is not None
        and re.search(schema["not"]["pattern"], token) is None
    )
    assert accepted == good
