"""Synthetic metadata only; no historical input reads or exposure conclusions."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, NoReturn

import d1_exposure_collection as c
import pytest
from endpoint_belief_reference import EndpointOracle

import strange_physics.calibration_fixture_contracts as legacy
import strange_physics.native_endpoint_beliefs as beliefs
import strange_physics.native_prediction as prediction
import strange_physics.simulation as simulation
from strange_physics.control_contracts import ContractViolation


@pytest.fixture(autouse=True)
def forbid_science(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Metadata contract tests cannot execute or compare exposure")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(prediction, "predict_native_spring", deny)
    monkeypatch.setattr(prediction, "_state_at_time", deny)
    monkeypatch.setattr(beliefs, "compute_native_endpoint_belief", deny)
    monkeypatch.setattr(beliefs, "predict_native_spring", deny)
    monkeypatch.setattr(simulation, "simulate", deny)
    monkeypatch.setattr(legacy, "check_supplied_inventory", deny)
    monkeypatch.setattr(legacy, "physical_identity", deny)


def raw(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reason(code: str = "unresolved-source") -> dict[str, Any]:
    return {"code": code, "detail": "synthetic metadata only"}


def execution() -> dict[str, Any]:
    return {"run_id": "r0", "attempt_id": "a0", "job_id": None, "terminal": "completed"}


def context() -> dict[str, Any]:
    return {
        "schema_version": "strange-physics.d1-exposure-context.v1",
        "collection_id": "c0",
        "protocol_sha256": legacy.PROTOCOL_SHA256,
        "source_commit": "1" * 40,
        "policy_sha256": "2" * 64,
        "extractor_id": "rule-set-0",
        "cutoff_utc": "2026-10-30T00:00:00Z",
        "anchors": ["i0"],
        "gaps": [{"gap_id": "g0", "reason": reason("earlier-external-gap")}],
        "inputs": [
            {
                "input_id": "i0",
                "format": "retained-json",
                "storage": "private-evidence",
                "relative_path": "synthetic/input.json",
                "byte_length": 12,
                "raw_sha256": "3" * 64,
                "origin": {"kind": "run-attempt", "execution": execution()},
                "references": [],
            }
        ],
    }


def row(kind: str, record_id: str) -> dict[str, Any]:
    value: dict[str, Any] = {
        "kind": kind,
        "record_id": record_id,
        "bindings": [
            {
                "input_id": "i0",
                "raw_sha256": "3" * 64,
                "locator_kind": "json-pointer",
                "locator": "/records/0",
                "rule_id": "rule-0",
                "decoded_sha256": None,
                "decoded_locator": None,
                "decoder": None,
            }
        ],
        "compatibility": {
            name: {"status": "unknown", "reason": reason(), "source_indices": [0]}
            for name in ("world", "query", "history")
        },
        "projections": {"world": None, "query": None, "history": None},
    }
    if kind == "execution-occurrence":
        value.update(
            execution=execution(),
            subject_locator="/records/0",
            roles=["reference"],
            world_id="w0",
            unresolved_world=None,
        )
    if kind == "design-or-analytic-material":
        value.update(role="source-design", world_id="w0")
    return value


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ctx = context()
    parts = [
        {
            "schema_version": "strange-physics.d1-exposure-part.v1",
            "context_sha256": digest(raw(ctx)),
            "index": i,
            "kind": kind,
            "records": [row(kind, record_id)],
        }
        for i, (kind, record_id) in enumerate(zip(c.KINDS, ("w0", "e0", "m0"), strict=True))
    ]
    root = {
        "schema_version": "strange-physics.d1-exposure-collection.v1",
        "canonical_profile": c.CANONICAL_PROFILE,
        "context": ctx,
        "context_sha256": digest(raw(ctx)),
        "parts": [],
        "coverage": [
            {
                "input_id": "i0",
                "disposition": "processed",
                "row_count": 3,
                "reference_edges": 0,
                "reason": reason("extracted"),
            }
        ],
        "row_counts": {
            "physical_world": 1,
            "execution_occurrence": 1,
            "design_or_analytic_material": 1,
        },
        "material_authenticity": "unchecked",
        "historical_completeness": "not-established",
        "overlap_conclusion": "unavailable",
    }
    return root, parts


def seal(
    root: dict[str, Any], parts: list[dict[str, Any]]
) -> tuple[bytes, tuple[c.NamedPartBytes, ...]]:
    """Bind test bytes, without normalizing invalid fields through a model serializer."""
    root = deepcopy(root)
    root["parts"] = []
    supplied = []
    for i, part in enumerate(parts):
        payload = raw(part)
        path = f"parts/p{i}.json"
        root["parts"].append(
            {
                "path": path,
                "index": part["index"],
                "kind": part["kind"],
                "byte_length": len(payload),
                "raw_sha256": digest(payload),
                "row_count": len(part["records"]),
            }
        )
        supplied.append(c.NamedPartBytes(path, payload))
    return raw(root), tuple(supplied)


def refresh_context(root: dict[str, Any], parts: list[dict[str, Any]]) -> None:
    identity = digest(raw(root["context"]))
    root["context_sha256"] = identity
    for part in parts:
        part["context_sha256"] = identity


def test_complete_all_part_bytes_are_verified_but_not_history() -> None:
    root, parts = fixture()
    encoded, supplied = seal(root, parts)
    result = c.verify_collection(encoded, supplied)
    assert len(result.parts) == 3 and result.actual_part_bytes == sum(len(p.raw) for p in supplied)
    assert result.raw_root_sha256 == digest(encoded)
    assert result.unique_raw_input_objects == 1 and result.declared_distinct_input_bytes == 12
    assert result.verification_scope == "supplied-all-part-structure-only"
    assert (
        result.material_authenticity == "unchecked" and result.overlap_conclusion == "unavailable"
    )
    assert len(result.root.context.gaps) == 1
    assert legacy.MAX_INVENTORY_ROWS == 1024 and legacy.MAX_PRIVATE_BYTES == c.MIB


@pytest.mark.parametrize(
    "change", ("missing", "extra", "swapped", "duplicate", "wrong-name", "corrupt")
)
def test_selected_or_substituted_parts_never_verify(change: str) -> None:
    encoded, parts = seal(*fixture())
    if change == "missing":
        actual = parts[:-1]
    elif change == "extra":
        actual = (*parts, parts[0])
    elif change == "swapped":
        actual = (parts[1], parts[0], parts[2])
    elif change == "duplicate":
        actual = (parts[0], parts[0], parts[2])
    elif change == "wrong-name":
        actual = (c.NamedPartBytes("parts/wrong.json", parts[0].raw), *parts[1:])
    else:
        actual = (c.NamedPartBytes(parts[0].path, parts[0].raw[:-1] + b" "), *parts[1:])
    with pytest.raises(ContractViolation):
        c.verify_collection(encoded, actual)


@pytest.mark.parametrize(
    "change", ("hash", "size", "context", "index", "kind", "row-count", "path")
)
def test_manifest_and_part_joins_are_exact(change: str) -> None:
    root, parts = fixture()
    encoded, supplied = seal(root, parts)
    data = json.loads(encoded)
    if change == "hash":
        data["parts"][0]["raw_sha256"] = "4" * 64
    elif change == "size":
        data["parts"][0]["byte_length"] += 1
    elif change == "context":
        parts[-1]["context_sha256"] = "5" * 64
        encoded, supplied = seal(root, parts)
        data = json.loads(encoded)
    elif change == "index":
        data["parts"][1]["index"] = 0
    elif change == "kind":
        data["parts"][1]["kind"] = "physical-world"
    elif change == "row-count":
        data["parts"][1]["row_count"] = 2
    else:
        data["parts"][1]["path"] = data["parts"][0]["path"]
    with pytest.raises(ContractViolation):
        c.verify_collection(raw(data), supplied)


@pytest.mark.parametrize(
    "change",
    ("duplicate-id", "dangling-world", "wrong-world-kind", "input-id", "raw-hash", "locator-kind"),
)
def test_late_cross_part_and_provenance_failures_are_not_skipped(change: str) -> None:
    root, parts = fixture()
    last = parts[-1]["records"][0]
    if change == "duplicate-id":
        last["record_id"] = "w0"
    elif change == "dangling-world":
        last["world_id"] = "absent"
    elif change == "wrong-world-kind":
        last["world_id"] = "e0"
    elif change == "input-id":
        last["bindings"][0]["input_id"] = "absent"
    elif change == "raw-hash":
        last["bindings"][0]["raw_sha256"] = "7" * 64
    else:
        last["bindings"][0]["locator_kind"] = "source-literal"
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


@pytest.mark.parametrize(
    "change", ("missing", "extra", "row-count", "edges", "role-count", "failed-extraction")
)
def test_coverage_and_role_denominators_are_recomputed(change: str) -> None:
    root, parts = fixture()
    if change == "missing":
        root["coverage"] = []
    elif change == "extra":
        root["coverage"].append(deepcopy(root["coverage"][0]))
    elif change == "row-count":
        root["coverage"][0]["row_count"] = 2
    elif change == "edges":
        root["coverage"][0]["reference_edges"] = 1
    elif change == "role-count":
        root["row_counts"]["physical_world"] = 0
    else:
        root["coverage"][0]["disposition"] = "unprocessed"
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


def test_unresolved_world_and_unsupported_input_are_retained_without_clean_conclusion() -> None:
    root, parts = fixture()
    occurrence = parts[1]["records"][0]
    occurrence.update(world_id=None, unresolved_world=reason(), roles=["unknown"])
    root["coverage"][0]["disposition"] = "unknown"
    result = c.verify_collection(*seal(root, parts))
    assert result.root.coverage[0].disposition == "unknown"
    observed = result.parts[1].records[0]
    assert isinstance(observed, c.OccurrenceRecord) and observed.world_id is None
    assert result.overlap_conclusion == "unavailable"


def test_empty_extraction_still_requires_every_input_disposition() -> None:
    root, _ = fixture()
    root["coverage"][0].update(disposition="unsupported", row_count=0)
    root["row_counts"] = dict.fromkeys(root["row_counts"], 0)
    result = c.verify_collection(*seal(root, []))
    assert result.parts == () and len(result.root.coverage) == 1
    assert result.root.historical_completeness == "not-established"


@pytest.mark.parametrize(
    "change",
    (
        "duplicate-input",
        "missing-anchor",
        "duplicate-anchor",
        "dangling-edge",
        "unreachable",
        "conflicting-size",
    ),
)
def test_frozen_input_graph_rejects_implicit_discovery(change: str) -> None:
    root, parts = fixture()
    ctx = root["context"]
    if change == "duplicate-input":
        ctx["inputs"].append(deepcopy(ctx["inputs"][0]))
    elif change == "missing-anchor":
        ctx["anchors"] = ["missing"]
    elif change == "duplicate-anchor":
        ctx["anchors"] *= 2
    elif change == "dangling-edge":
        ctx["inputs"][0]["references"] = [{"target_input_id": "missing", "locator": "/refs/0"}]
    else:
        extra = deepcopy(ctx["inputs"][0])
        extra["input_id"] = "i1"
        ctx["inputs"].append(extra)
        if change == "conflicting-size":
            extra["relative_path"] = "synthetic/mirror.json"
            ctx["inputs"][0]["references"] = [{"target_input_id": "i1", "locator": "/mirror"}]
            root["coverage"][0]["reference_edges"] = 1
            root["coverage"].append(
                {
                    "input_id": "i1",
                    "disposition": "processed",
                    "row_count": 0,
                    "reference_edges": 0,
                    "reason": reason("no-records"),
                }
            )
            refresh_context(root, parts)
            assert c.verify_collection(*seal(root, parts)).unique_raw_input_objects == 1
            extra["byte_length"] += 1
    refresh_context(root, parts)
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


def test_max_edges_count_repeated_locators_without_duplicate_execution_claim() -> None:
    root, parts = fixture()
    root["context"]["inputs"][0]["references"] = [
        {"target_input_id": "i0", "locator": "/same"}
    ] * 256
    root["coverage"][0]["reference_edges"] = 256
    refresh_context(root, parts)
    result = c.verify_collection(*seal(root, parts))
    assert result.root.coverage[0].reference_edges == 256
    assert result.root.row_counts.execution_occurrence == 1


@pytest.mark.parametrize(
    "where",
    (
        "input-byte",
        "input-count",
        "anchor-count",
        "edges",
        "part-count",
        "part-row-count",
        "part-byte",
    ),
)
def test_declared_capacity_overflow_is_not_truncation(where: str) -> None:
    root, parts = fixture()
    ctx = root["context"]
    if where == "input-byte":
        ctx["inputs"][0]["byte_length"] = c.INPUT_BYTES + 1
    elif where == "input-count":
        ctx["inputs"] *= 257
    elif where == "anchor-count":
        ctx["anchors"] *= 33
    elif where == "edges":
        ctx["inputs"][0]["references"] = [{"target_input_id": "i0", "locator": ""}] * 257
    refresh_context(root, parts)
    encoded, supplied = seal(root, parts)
    data = json.loads(encoded)
    if where == "part-count":
        data["parts"] *= 22
    elif where == "part-row-count":
        data["parts"][0]["row_count"] = 1025
    elif where == "part-byte":
        data["parts"][0]["byte_length"] = c.PART_BYTES + 1
    with pytest.raises(ContractViolation):
        c.verify_collection(raw(data), supplied)


@pytest.mark.parametrize(
    "field", ("ROOT_BYTES", "PART_BYTES", "ROW_BYTES", "ALL_PART_BYTES", "ALL_INPUT_BYTES")
)
def test_actual_and_aggregate_byte_limits_stop_before_acceptance(
    field: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    encoded, supplied = seal(*fixture())
    monkeypatch.setattr(c, field, 8)
    with pytest.raises(ContractViolation):
        c.verify_collection(encoded, supplied)


@pytest.mark.parametrize(
    "field,value",
    (
        ("row_count", True),
        ("reference_edges", False),
    ),
)
def test_raw_coverage_boolean_is_not_serialized_to_integer(field: str, value: bool) -> None:
    root, parts = fixture()
    root["coverage"][0][field] = value
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


@pytest.mark.parametrize("change", ("part-index", "input-size", "binding-index", "count"))
def test_other_raw_integer_booleans_are_rejected(change: str) -> None:
    root, parts = fixture()
    if change == "part-index":
        parts[0]["index"] = False
    elif change == "input-size":
        root["context"]["inputs"][0]["byte_length"] = True
        refresh_context(root, parts)
    elif change == "binding-index":
        parts[0]["records"][0]["compatibility"]["world"]["source_indices"] = [False]
    else:
        root["row_counts"]["physical_world"] = True
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


@pytest.mark.parametrize(
    "change",
    ("duplicate-key", "invalid-utf8", "nan", "depth", "extra", "whitespace", "unicode-encoding"),
)
def test_noncanonical_or_unsafe_root_bytes_fail(change: str) -> None:
    encoded, supplied = seal(*fixture())
    if change == "duplicate-key":
        encoded = b'{"context_sha256":"duplicate",' + encoded[1:]
    elif change == "invalid-utf8":
        encoded = b"\xff"
    elif change == "nan":
        encoded = b'{"bad":NaN,' + encoded[1:]
    elif change == "depth":
        encoded = b"[" * 25 + b"0" + b"]" * 25
    elif change == "extra":
        data = json.loads(encoded)
        data["approved"] = True
        encoded = raw(data)
    elif change == "unicode-encoding":
        encoded = encoded.replace(b"synthetic", b"\\u0073ynthetic", 1)
    else:
        encoded += b"\n"
    with pytest.raises(ContractViolation):
        c.verify_collection(encoded, supplied)


def test_part_canonicality_is_checked_even_with_matching_hash_and_length() -> None:
    encoded, supplied = seal(*fixture())
    data = json.loads(encoded)
    padded = supplied[0].raw + b"\n"
    data["parts"][0].update(byte_length=len(padded), raw_sha256=digest(padded))
    with pytest.raises(ContractViolation):
        c.verify_collection(raw(data), (c.NamedPartBytes(supplied[0].path, padded), *supplied[1:]))


@pytest.mark.parametrize(
    "path", ("/absolute", "../escape", "a/../b", "a//b", "a\\b", "a/./b", "é.json", "a" * 513)
)
def test_paths_are_only_normalized_relative_metadata(path: str) -> None:
    root, parts = fixture()
    root["context"]["inputs"][0]["relative_path"] = path
    refresh_context(root, parts)
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


@pytest.mark.parametrize("value", ("-start", "name space", "é", "a\n", "a" * 129))
def test_ids_have_bounded_ascii_grammar_but_no_secrecy_claim(value: str) -> None:
    root, parts = fixture()
    root["context"]["collection_id"] = value
    refresh_context(root, parts)
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


@pytest.mark.parametrize(
    "change",
    (
        "detail-bytes",
        "locator-bytes",
        "pointer-escape",
        "decoded-half",
        "source-index",
        "projection-missing",
        "roles",
        "unknown-world-reason",
    ),
)
def test_provenance_and_compatibility_fields_fail_closed(change: str) -> None:
    root, parts = fixture()
    value = parts[1]["records"][0]
    if change == "detail-bytes":
        value["compatibility"]["world"]["reason"]["detail"] = "界" * 171
    elif change == "locator-bytes":
        value["bindings"][0]["locator"] = "/" + "界" * 342
    elif change == "pointer-escape":
        value["bindings"][0]["locator"] = "/bad~2pointer"
    elif change == "decoded-half":
        value["bindings"][0]["decoded_sha256"] = "6" * 64
    elif change == "source-index":
        value["compatibility"]["history"]["source_indices"] = [1]
    elif change == "projection-missing":
        value["compatibility"]["world"]["status"] = "compatible"
    elif change == "roles":
        value["roles"] = ["unknown", "candidate"]
    else:
        value["world_id"] = None
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


def test_compatible_world_survives_query_incompatibility() -> None:
    root, parts = fixture()
    projection = {
        "mechanism": "zero-rest-spring",
        "coefficient_hex": "0x1.0000000000000p+0",
        "structure": "one-particle-zero-anchor-linear-spring.v1",
    }
    for part in parts:
        value = part["records"][0]
        value["projections"]["world"] = deepcopy(projection)
        value["compatibility"]["world"].update(
            status="compatible", reason=reason("exact-projection")
        )
    parts[1]["records"][0]["compatibility"]["query"].update(
        status="incompatible",
        reason=reason("unsupported-query"),
    )
    result = c.verify_collection(*seal(root, parts))
    value = result.parts[1].records[0]
    assert value.compatibility.world.status == "compatible"
    assert value.compatibility.query.status == "incompatible"
    assert value.projections.world is not None and result.overlap_conclusion == "unavailable"


def test_complete_embedded_byte_binding_and_root_pointer_are_metadata_only() -> None:
    root, parts = fixture()
    parts[0]["records"][0]["bindings"][0].update(
        locator="",
        decoded_sha256="6" * 64,
        decoded_locator="/inside~1key",
        decoder="utf8-json-string.v1",
    )
    result = c.verify_collection(*seal(root, parts))
    binding = result.parts[0].records[0].bindings[0]
    assert binding.locator == "" and binding.decoded_sha256 == "6" * 64
    assert result.material_authenticity == "unchecked"


def test_all_256_named_inputs_and_exact_32_mib_metadata_boundary() -> None:
    root, parts = fixture()
    seed = root["context"]["inputs"][0]
    items, coverage = [], []
    for i in range(256):
        item = deepcopy(seed)
        item.update(
            input_id=f"i{i}",
            relative_path=f"synthetic/i{i}.json",
            byte_length=128 * 1024,
            raw_sha256=f"{i + 1:064x}",
        )
        items.append(item)
        coverage.append(
            {
                "input_id": f"i{i}",
                "disposition": "processed",
                "row_count": 3 if i == 0 else 0,
                "reference_edges": 255 if i == 0 else 0,
                "reason": reason("extracted"),
            }
        )
    items[0]["references"] = [
        {"target_input_id": f"i{i}", "locator": f"/refs/{i}"} for i in range(1, 256)
    ]
    root["context"]["inputs"], root["coverage"] = items, coverage
    for part in parts:
        part["records"][0]["bindings"][0]["raw_sha256"] = items[0]["raw_sha256"]
    refresh_context(root, parts)
    result = c.verify_collection(*seal(root, parts))
    assert result.unique_raw_input_objects == 256
    assert result.declared_distinct_input_bytes == 32 * c.MIB
    # No declared input content is available to this test or verifier.
    items[0]["byte_length"] += 1
    refresh_context(root, parts)
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))


def test_mirrored_object_keeps_both_named_source_edges() -> None:
    root, parts = fixture()
    first = root["context"]["inputs"][0]
    second = deepcopy(first)
    second.update(input_id="i1", relative_path="synthetic/mirror.json")
    first["references"] = [{"target_input_id": "i1", "locator": "/mirror"}]
    root["context"]["inputs"].append(second)
    root["coverage"][0]["reference_edges"] = 1
    root["coverage"].append(
        {
            "input_id": "i1",
            "disposition": "processed",
            "row_count": 1,
            "reference_edges": 0,
            "reason": reason("extracted"),
        }
    )
    parts[-1]["records"][0]["bindings"][0]["input_id"] = "i1"
    root["coverage"][0]["row_count"] = 2
    refresh_context(root, parts)
    result = c.verify_collection(*seal(root, parts))
    assert result.unique_raw_input_objects == 1 and len(result.root.context.inputs) == 2
    assert result.declared_distinct_input_bytes == 12
    assert tuple(x.row_count for x in result.root.coverage) == (2, 1)


@pytest.mark.parametrize(
    "change", ("node-limit", "bindings", "record-extra", "role-tag", "context-extra")
)
def test_bounded_shape_rejects_hidden_payloads(change: str) -> None:
    root, parts = fixture()
    if change == "node-limit":
        # Bounded parser guards structure before DTO validation.
        with pytest.raises(ContractViolation):
            c.parse_context(b"[" + b"0," * 32768 + b"0]")
        return
    if change == "bindings":
        parts[0]["records"][0]["bindings"] *= 9
    elif change == "record-extra":
        parts[0]["records"][0]["raw_observation"] = "hidden bytes"
    elif change == "role-tag":
        parts[0]["records"][0]["kind"] = "unknown-kind"
    else:
        root["context"]["part_hashes"] = []
        refresh_context(root, parts)
    with pytest.raises(ContractViolation):
        c.verify_collection(*seal(root, parts))
