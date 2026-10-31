"""Independent synthetic declarations; no source resolution or scientific work."""

from __future__ import annotations

import builtins
import hashlib
import json
from dataclasses import FrozenInstanceError
from typing import Any, NoReturn

import d1_source_manifest as source
import pytest


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def catalog_fixture() -> dict[str, Any]:
    return {
        "schema": "strange-physics.d1-source-catalog.v1",
        "installation_member_ref": "m03",
        "members": [
            ["m00", "checkout_source", "synthetic/catalog.json", None],
            ["m01", "checkout_source", "tests/d1_primitive_codec.py", "d1_primitive_codec"],
            ["m02", "checkout_source", "synthetic/emitter.py", "synthetic_emitter"],
            ["m03", "checkout_source", "synthetic/installer.py", "synthetic_installer"],
            ["m04", "checkout_source", "uv.lock", None],
            [
                "m05", "checkout_source", "tests/endpoint_belief_reference.py",
                "endpoint_belief_reference",
            ],
            ["m06", "checkout_source", "docs/research/RA_N03_CALIBRATION_SLICE.md", None],
            ["m07", "checkout_source", "tests/d1_primitive_recording.py", "d1_primitive_recording"],
            ["m08", "checkout_source", "tests/d1_primitive_sink.py", "d1_primitive_sink"],
        ],
        "definitions": [
            ["d0", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.position"],
            ["d1", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.exp"],
            ["d2", "m05", "python_method", "endpoint_belief_reference", "EndpointOracle.log"],
            [
                "d3", "m05", "python_method", "endpoint_belief_reference",
                "EndpointOracle.circle_constant",
            ],
            ["d4", "m02", "python_function", "synthetic_emitter", "emit"],
        ],
        "instances": [
            ["i00", "fixture", None, "m05"], ["i01", "strong", None, "m05"],
            ["i02", "weak", None, "m05"], ["i03", "future", None, "m05"],
            ["i04", "arithmetic", 0, "m05"], ["i05", "arithmetic", 1, "m05"],
            ["i06", "arithmetic", 2, "m05"], ["i07", "arithmetic", 3, "m05"],
            ["i08", "arithmetic", 4, "m05"], ["i09", "arithmetic", 5, "m05"],
            ["i10", "arithmetic", 6, "m05"], ["i11", "arithmetic", 7, "m05"],
            ["i12", "constants", None, "m05"], ["i13", "native_emit", None, "m02"],
        ],
        "dispatch_policy": [
            ["i00", 0, "d0", "j00",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i01", 0, "d0", "j01",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i02", 0, "d0", "j02",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i03", 0, "d0", "j03",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i04", 1, "d1", "j04",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i04", 2, "d2", "j05",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i05", 1, "d1", "j06",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i05", 2, "d2", "j07",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i06", 1, "d1", "j08",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i06", 2, "d2", "j09",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i07", 1, "d1", "j10",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i07", 2, "d2", "j11",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i08", 1, "d1", "j12",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i08", 2, "d2", "j13",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i09", 1, "d1", "j14",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i09", 2, "d2", "j15",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i10", 1, "d1", "j16",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i10", 2, "d2", "j17",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i11", 1, "d1", "j18",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i11", 2, "d2", "j19",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i12", 2, "d2", "j20",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i12", 3, "d3", "j21",
             "m03", "dispatch", "m03", "run", "bound_method_recorder_slot_v1"],
            ["i13", 4, "d4", "j22",
             "m03", "dispatch", "m03", "run", "native_callable_recorder_slot_v1"],
        ],
    }


def manifest_fixture(catalog: dict[str, Any]) -> dict[str, Any]:
    """Synthetic content pins; only the supplied catalog bytes are actually hashed."""
    catalog_raw = encoded(catalog)
    members = []
    for index, row in enumerate(catalog["members"]):
        digest = hashlib.sha256(catalog_raw).hexdigest() if index == 0 else str(index % 10) * 64
        length = len(catalog_raw) if index == 0 else 262144 if row[2] == "uv.lock" else 1
        if row[2] == "docs/research/RA_N03_CALIBRATION_SLICE.md":
            digest = "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"
        members.append([*row[:3], digest, length, row[3]])
    return {
        "schema": "strange-physics.d1-source-manifest.v1",
        "source_commit": "a" * 40, "source_tree": "b" * 40,
        "protocol_sha256": "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399",
        "uv_lock_sha256": "4" * 64, "recorder_sha256": "7" * 64,
        "codec_sha256": "1" * 64, "sink_sha256": "8" * 64,
        "run_id": "run0", "recorder_id": "recorder0", "catalog_ref": "m00",
        "catalog_sha256": hashlib.sha256(catalog_raw).hexdigest(),
        "runtime_admission_ref": "runtime0", "runtime_admission_sha256": "e" * 64,
        "installation_member_ref": "m03", "members": members,
        "definitions": catalog["definitions"], "instances": catalog["instances"],
        "bindings": [row[:4] for row in catalog["dispatch_policy"]],
        "limits": {
            "manifest_bytes": 65536, "header_bytes": 4096, "row_with_separator_bytes": 512,
            "source_members": 64, "definitions": 5, "instances": 14, "bindings": 23,
            "source_file_bytes": 131072, "lock_file_bytes": 262144, "loaded_source_copies": 64,
            "validation_passes": 2, "json_depth": 3, "json_nodes": 2048, "integer_token_chars": 10,
            "retained_source_copies": 0, "retained_manifest_copies": 0,
        },
    }


@pytest.fixture(autouse=True)
def deny_scientific_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    original = builtins.__import__

    def denied(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith((
            "strange_physics", "endpoint_belief_reference", "d1_fixture_reference",
            "d1_prefix_evidence", "d1_primitive_recording", "d1_primitive_sink",
            "d1_codec_append", "d1_table_retention",
        )):
            raise AssertionError("No scientific, recorder, sink or retention import")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", denied)


def test_literal_catalog_and_manifest_have_complete_declaration_joins() -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    sraw, craw = encoded(manifest), encoded(catalog)
    result = source.compare_declarations(sraw, craw)
    assert result.manifest.raw == sraw and result.catalog.raw == craw
    assert result.manifest.sha256 == hashlib.sha256(sraw).hexdigest()
    assert result.catalog.sha256 == hashlib.sha256(craw).hexdigest()
    assert (
        len(result.manifest.members), len(result.manifest.definitions),
        len(result.manifest.instances), len(result.manifest.bindings),
    ) == (9, 5, 14, 23)
    assert result.manifest.bindings[-1] == source.Binding("i13", 4, "d4", "j22")
    assert all(item.source_member_ref == "m05" for item in result.manifest.instances[:13])
    assert not hasattr(result, "authenticated") and not hasattr(result, "ready")


def test_runtime_builtin_is_only_an_unresolved_declaration() -> None:
    catalog = catalog_fixture()
    catalog["members"][2] = ["m02", "trusted_runtime_member", "native-emitter", "synthetic_runtime"]
    catalog["definitions"][4] = ["d4", "m02", "runtime_builtin", "synthetic_runtime", "exp"]
    manifest = manifest_fixture(catalog)
    manifest["members"][2][4] = 67108864
    result = source.compare_declarations(encoded(manifest), encoded(catalog))
    assert result.manifest.definitions[-1].kind == "runtime_builtin"
    assert result.manifest.members[2].byte_length == 67108864
    assert result.catalog.members[2].locator == "native-emitter"
    manifest["members"][2][4] = 0
    with pytest.raises(ValueError, match="bounded integer"):
        source.parse_manifest(encoded(manifest))


def test_complete_member_limit_and_attainable_row_extrema() -> None:
    catalog = catalog_fixture()
    for index in range(9, 63):
        catalog["members"].append(
            [f"m{index:02d}", "checkout_source", f"synthetic/m{index:02d}.py", None]
        )
    catalog["members"].append(["z" * 32, "checkout_source", "x" * 160, "y" * 128])
    manifest = manifest_fixture(catalog)
    manifest["members"][-1][4] = 131072
    result = source.compare_declarations(encoded(manifest), encoded(catalog))
    assert len(result.manifest.members) == len(result.catalog.members) == 64
    # This source row attains 422 raw bytes plus one separator; it is not a 512B row.
    assert len(encoded(manifest["members"][-1])) == 423
    assert len(encoded(catalog["members"][-1])) == 349


def test_opaque_extrema_and_original_bytes_survive_input_mutation() -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    # Long quoted digits are ordinary opaque text, not outside-string integer tokens.
    manifest["run_id"], manifest["recorder_id"] = "9" * 96, "c" * 96
    manifest["runtime_admission_ref"] = "a" * 32
    raw = encoded(manifest)
    result = source.parse_manifest(raw)
    manifest["members"][0][3] = "f" * 64
    assert result.raw == raw and result.identity.run_id == "9" * 96
    untrusted_view: Any = result
    with pytest.raises(FrozenInstanceError):
        untrusted_view.raw = b"changed"
    untrusted_policy: Any = result.members[0].policy
    with pytest.raises(FrozenInstanceError):
        untrusted_policy.locator = "changed"


@pytest.mark.parametrize("bad", [bytearray(b"{}\n"), memoryview(b"{}\n"), "{}\n", None], ids=["mutable", "view", "text", "none"])
def test_raw_boundaries_reject_nonbytes(bad: Any) -> None:
    with pytest.raises(ValueError):
        source.parse_manifest(bad)
    with pytest.raises(ValueError):
        source.parse_catalog(bad)


@pytest.mark.parametrize("raw", [b"", b"{", b'{"x":"', b"[]\n", b"null\n", b"{\xff}\n", b"{}\x00\n"], ids=["empty", "brace", "string", "list", "null", "nonascii", "nul"])
def test_malformed_raw_declarations(raw: bytes) -> None:
    with pytest.raises(ValueError):
        source.parse_manifest(raw)
    with pytest.raises(ValueError):
        source.parse_catalog(raw)


@pytest.mark.parametrize("change", ["no-lf", "two-lf", "space", "escape", "duplicate", "escaped-key", "float", "nan", "negative-zero"], ids=["no-lf", "two-lf", "space", "escape", "dup", "escaped-dup", "float", "nan", "neg-zero"])
def test_noncanonical_or_ambiguous_json(change: str) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    raw = encoded(manifest)
    if change == "no-lf":
        raw = raw[:-1]
    elif change == "two-lf":
        raw += b"\n"
    elif change == "space":
        raw = b" " + raw
    elif change == "escape":
        raw = raw.replace(b'"run0"', b'"\\u0072un0"')
    elif change == "duplicate":
        raw = raw.replace(b'"run_id":"run0"', b'"run_id":"run0","run_id":"run0"')
    elif change == "escaped-key":
        raw = raw.replace(b'"run_id":"run0"', b'"run_id":"run0","\\u0072un_id":"run0"')
    elif change == "float":
        raw = raw.replace(b'"validation_passes":2', b'"validation_passes":2.0')
    elif change == "nan":
        raw = raw.replace(b'"validation_passes":2', b'"validation_passes":NaN')
    else:
        raw = raw.replace(b'"retained_source_copies":0', b'"retained_source_copies":-0')
    with pytest.raises(ValueError):
        source.parse_manifest(raw)


@pytest.mark.parametrize("kind", ["bytes", "depth", "nodes"], ids=["bytes", "depth", "nodes"])
def test_predecode_guards_run_before_json_allocation(kind: str, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Decoder must not be reached")
    if kind == "bytes":
        sraw, craw = b" " * 65537, b" " * 131073
    elif kind == "depth":
        sraw = craw = b'{"x":[[[0]]]}\n'
    else:
        sraw = craw = b"{" + b",".join(b'"k":0' for _ in range(1024)) + b"}\n"
    with monkeypatch.context() as scoped:
        scoped.setattr(json, "loads", forbidden)
        with pytest.raises(ValueError):
            source.parse_manifest(sraw)
        with pytest.raises(ValueError):
            source.parse_catalog(craw)


@pytest.mark.parametrize("token", [b"10000000000", b"-1000000000"], ids=["eleven-positive", "sign-counted"])
def test_integer_length_is_bounded_before_conversion(
    token: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = b'{"x":' + token + b'}\n'

    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Numeric-token guard must precede decoder entry")

    with monkeypatch.context() as scoped:
        scoped.setattr(json, "loads", forbidden)
        with pytest.raises(ValueError, match="token including sign"):
            source.parse_manifest(raw)
        with pytest.raises(ValueError, match="token including sign"):
            source.parse_catalog(raw)


@pytest.mark.parametrize("field,bad", [("schema", "other"), ("source_commit", "A" * 40), ("source_tree", "0" * 39), ("protocol_sha256", "f" * 64), ("run_id", "r" * 97), ("recorder_id", "bad/id"), ("runtime_admission_ref", "x" * 33), ("runtime_admission_sha256", True), ("catalog_ref", "missing"), ("installation_member_ref", "missing")], ids=["schema", "commit", "tree", "protocol", "run", "recorder", "runtime-ref", "hash-bool", "catalog-ref", "installer-ref"])
def test_manifest_header_fields(field: str, bad: object) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    manifest[field] = bad
    with pytest.raises(ValueError):
        source.parse_manifest(encoded(manifest))


@pytest.mark.parametrize("change", ["missing", "extra", "changed", "boolean"], ids=["missing", "extra", "changed", "bool"])
def test_limits_are_exact_and_cannot_coerce(change: str) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    if change == "missing":
        del manifest["limits"]["lock_file_bytes"]
    elif change == "extra":
        manifest["limits"]["other"] = 0
    elif change == "changed":
        manifest["limits"]["source_file_bytes"] = 262144
    else:
        manifest["limits"]["retained_source_copies"] = False
    with pytest.raises(ValueError):
        source.parse_manifest(encoded(manifest))


@pytest.mark.parametrize("change", ["missing", "extra", "order", "duplicate-id", "duplicate-path", "too-many", "row-extra", "nested", "unicode", "absolute", "dot", "dotdot", "backslash", "control", "module"], ids=["missing", "extra", "order", "id", "path", "count", "shape", "nested", "unicode", "absolute", "dot", "dotdot", "slash", "control", "module"])
def test_member_policy_rejections(change: str) -> None:
    catalog = catalog_fixture()
    if change == "missing":
        catalog["members"].pop(1)
    elif change == "extra":
        catalog["self_sha256"] = "a" * 64
    elif change == "order":
        catalog["members"][0], catalog["members"][1] = catalog["members"][1], catalog["members"][0]
    elif change == "duplicate-id":
        catalog["members"][1][0] = "m00"
    elif change == "duplicate-path":
        catalog["members"][3][2] = catalog["members"][2][2]
    elif change == "too-many":
        catalog["members"] += [[f"m{x:02d}", "checkout_source", f"synthetic/{x}", None] for x in range(9, 65)]
    elif change == "row-extra":
        catalog["members"][0].append("extra")
    elif change == "nested":
        catalog["members"][0][2] = []
    elif change == "unicode":
        catalog["members"][0][2] = "café"
    elif change == "absolute":
        catalog["members"][0][2] = "/catalog"
    elif change == "dot":
        catalog["members"][0][2] = "./catalog"
    elif change == "dotdot":
        catalog["members"][0][2] = "a/../catalog"
    elif change == "backslash":
        catalog["members"][0][2] = "a\\catalog"
    elif change == "control":
        catalog["members"][0][2] = "bad\nfile"
    else:
        catalog["members"][5][3] = "not-a-module"
    with pytest.raises(ValueError):
        source.parse_catalog(encoded(catalog))


@pytest.mark.parametrize("change", ["omit", "duplicate", "alias", "origin", "loaded", "oversize", "length-bool", "root-hash", "ordinary-size", "catalog-size", "runtime-size"], ids=["omit", "duplicate", "alias", "origin", "loaded", "size", "bool", "hash", "ordinary", "catalog", "runtime"])
def test_lock_exception_is_unique_and_cannot_spread(change: str) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    if change == "omit":
        manifest["members"].pop(4)
    elif change == "duplicate":
        manifest["members"].append(["m09", "checkout_source", "uv.lock", "4" * 64, 1, None])
    elif change == "alias":
        manifest["members"][4][2] = "./uv.lock"
    elif change == "origin":
        manifest["members"][4][1] = "trusted_runtime_member"
    elif change == "loaded":
        manifest["members"][4][5] = "uv"
    elif change == "oversize":
        manifest["members"][4][4] = 262145
    elif change == "length-bool":
        manifest["members"][4][4] = True
    elif change == "root-hash":
        manifest["uv_lock_sha256"] = "f" * 64
    elif change == "ordinary-size":
        manifest["members"][2][4] = 131073
    elif change == "catalog-size":
        manifest["members"][0][4] = 131073
    else:
        catalog["members"][2] = ["m02", "trusted_runtime_member", "emitter", "runtime_emitter"]
        catalog["definitions"][4] = ["d4", "m02", "runtime_builtin", "runtime_emitter", "exp"]
        manifest = manifest_fixture(catalog)
        source.parse_manifest(encoded(manifest))
        manifest["members"][2][4] = 67108865
    with pytest.raises(ValueError):
        source.parse_manifest(encoded(manifest))


@pytest.mark.parametrize("slot", [1, 6, 7, 8], ids=["codec", "protocol", "recorder", "sink"])
def test_fixed_source_root_hashes_bind_the_member(slot: int) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    manifest["members"][slot][3] = "f" * 64
    with pytest.raises(ValueError, match="root pin"):
        source.parse_manifest(encoded(manifest))


@pytest.mark.parametrize("change", ["method", "kind", "module", "null-module", "same-member", "runtime-python", "checkout-builtin", "d4-method", "missing-member", "order"], ids=["method", "kind", "module", "null", "shared", "runtime-python", "checkout-builtin", "d4-method", "member", "order"])
def test_coherent_catalog_cannot_override_definition_policy(change: str) -> None:
    catalog = catalog_fixture()
    if change == "method":
        catalog["definitions"][0][4] = "EndpointOracle.exp"
    elif change == "kind":
        catalog["definitions"][0][2] = "python_function"
    elif change == "module":
        catalog["definitions"][0][3] = "other"
    elif change == "null-module":
        catalog["members"][5][3] = None
    elif change == "same-member":
        catalog["members"].append(["m09", "checkout_source", "other.py", "endpoint_belief_reference"])
        catalog["definitions"][1][1] = "m09"
    elif change == "runtime-python":
        catalog["members"][2][1:3] = ["trusted_runtime_member", "emitter"]
    elif change == "checkout-builtin":
        catalog["definitions"][4][2] = "runtime_builtin"
    elif change == "d4-method":
        catalog["definitions"][4][2] = "python_method"
    elif change == "missing-member":
        catalog["definitions"][4][1] = "missing"
    else:
        catalog["definitions"][0], catalog["definitions"][1] = catalog["definitions"][1], catalog["definitions"][0]
    with pytest.raises(ValueError):
        source.compare_declarations(encoded(manifest_fixture(catalog)), encoded(catalog))


@pytest.mark.parametrize("change", ["instance-count", "definition-count", "binding-count", "role", "case", "case-bool", "instance-member", "slot-code", "code-bool", "slot-definition", "slot-order", "dispatch-id", "wrapper-ref", "consumer-ref", "wrapper-name", "native-tag", "method-tag"], ids=["instances", "defs", "bindings", "role", "case", "case-bool", "instance-ref", "code", "code-bool", "slot-def", "order", "dispatch", "wrapper", "consumer", "name", "native-tag", "method-tag"])
def test_complete_fixed_instance_slot_and_capture_joins(change: str) -> None:
    catalog = catalog_fixture()
    if change == "instance-count":
        catalog["instances"].pop()
    elif change == "definition-count":
        catalog["definitions"].pop()
    elif change == "binding-count":
        catalog["dispatch_policy"].pop()
    elif change == "role":
        catalog["instances"][0][1] = "future"
    elif change == "case":
        catalog["instances"][0][2] = 0
    elif change == "case-bool":
        catalog["instances"][4][2] = False
    elif change == "instance-member":
        catalog["instances"][0][3] = "m02"
    elif change == "slot-code":
        catalog["dispatch_policy"][0][1] = 1
    elif change == "code-bool":
        catalog["dispatch_policy"][0][1] = False
    elif change == "slot-definition":
        catalog["dispatch_policy"][0][2] = "d1"
    elif change == "slot-order":
        catalog["dispatch_policy"][0], catalog["dispatch_policy"][1] = catalog["dispatch_policy"][1], catalog["dispatch_policy"][0]
    elif change == "dispatch-id":
        catalog["dispatch_policy"][0][3] = "j01"
    elif change == "wrapper-ref":
        catalog["dispatch_policy"][0][4] = "missing"
    elif change == "consumer-ref":
        catalog["dispatch_policy"][0][6] = "missing"
    elif change == "wrapper-name":
        catalog["dispatch_policy"][0][5] = "not-a-name"
    elif change == "native-tag":
        catalog["dispatch_policy"][-1][-1] = "bound_method_recorder_slot_v1"
    else:
        catalog["dispatch_policy"][0][-1] = "native_callable_recorder_slot_v1"
    with pytest.raises(ValueError):
        source.compare_declarations(encoded(manifest_fixture(catalog)), encoded(catalog))


@pytest.mark.parametrize("change", ["hash", "size", "member", "definition", "instance", "installer"], ids=["hash", "size", "member", "definition", "instance", "installer"])
def test_actual_supplied_catalog_and_complete_projection_are_joined(change: str) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    if change == "hash":
        manifest["catalog_sha256"] = manifest["members"][0][3] = "f" * 64
    elif change == "size":
        manifest["members"][0][4] += 1
    elif change == "member":
        manifest["members"][0][2] = "other/catalog.json"
    elif change == "definition":
        manifest["definitions"] = [row[:] for row in manifest["definitions"]]
        manifest["definitions"][4][4] = "another_emit"
    elif change == "instance":
        manifest["members"].append(["m09", "checkout_source", "other/emitter.py", "9" * 64, 1, "synthetic_emitter"])
        manifest["definitions"] = [row[:] for row in manifest["definitions"]]
        manifest["definitions"][4][1] = "m09"
        manifest["instances"] = [row[:] for row in manifest["instances"]]
        manifest["instances"][-1][3] = "m09"
    else:
        manifest["installation_member_ref"] = "m02"
    # Each operand remains individually structurally valid; only the join fails.
    source.parse_manifest(encoded(manifest))
    source.parse_catalog(encoded(catalog))
    with pytest.raises(ValueError):
        source.compare_declarations(encoded(manifest), encoded(catalog))


def test_constructed_view_never_bypasses_raw_validation() -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    view: Any = source.parse_manifest(encoded(manifest))
    object.__setattr__(view, "raw", b"{}\n")
    with pytest.raises(ValueError):
        source.compare_declarations(view, encoded(catalog))
    with pytest.raises(ValueError):
        source.compare_declarations(view.raw, encoded(catalog))


@pytest.mark.parametrize("which", ["manifest-header", "catalog-header", "manifest-row", "catalog-row"], ids=["s-header", "c-header", "s-row", "c-row"])
def test_structural_reservations_with_explicit_test_only_lowering(which: str, monkeypatch: pytest.MonkeyPatch) -> None:
    catalog = catalog_fixture()
    manifest = manifest_fixture(catalog)
    document = manifest if which.startswith("manifest") else catalog
    parser = source.parse_manifest if which.startswith("manifest") else source.parse_catalog
    arrays = (
        "members", "definitions", "instances",
        "bindings" if which.startswith("manifest") else "dispatch_policy",
    )
    if which.endswith("header"):
        header = dict(document)
        for name in arrays:
            header[name] = []
        limit_name, inclusive = "HEADER_BYTES", len(encoded(header))
    else:
        # One LF and one separator each cost one byte. Include every row array,
        # so a later longer row cannot mask a missing separator in the check.
        limit_name = "ROW_BYTES"
        inclusive = max(len(encoded(row)) for name in arrays for row in document[name])
    parser(encoded(document))
    with monkeypatch.context() as scoped:
        scoped.setattr(source, limit_name, inclusive)
        parser(encoded(document))
        scoped.setattr(source, limit_name, inclusive - 1)
        with pytest.raises(ValueError):
            parser(encoded(document))


@pytest.mark.parametrize("which", ["manifest", "catalog"], ids=["s", "catalog"])
def test_cross_origin_same_locator_is_not_two_members(which: str) -> None:
    catalog = catalog_fixture()
    catalog["members"].extend([
        ["m09", "checkout_source", "shared-token", None],
        ["m10", "trusted_runtime_member", "separate-native", None],
    ])
    document = manifest_fixture(catalog) if which == "manifest" else catalog
    parser = source.parse_manifest if which == "manifest" else source.parse_catalog
    parser(encoded(document))
    document["members"][-1][2] = document["members"][-2][2]
    with pytest.raises(ValueError, match="locator"):
        parser(encoded(document))


def test_bytes_subclass_is_rejected_before_overridden_hooks() -> None:
    class UntrustedBytes(bytes):
        def __len__(self) -> int:
            raise AssertionError("Exact-type check must precede length hook")

        def decode(self, encoding: str = "utf-8", errors: str = "strict") -> str:
            raise AssertionError("Exact-type check must precede decoding hook")

    untrusted: Any = UntrustedBytes(b"{}\n")
    with pytest.raises(ValueError):
        source.parse_manifest(untrusted)
    with pytest.raises(ValueError):
        source.parse_catalog(untrusted)
