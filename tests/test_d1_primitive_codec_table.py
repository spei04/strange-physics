"""Synthetic identity declarations only; no primitives, scientific imports or I/O."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from typing import Any, NoReturn

import d1_primitive_codec_table as table
import pytest


def example() -> dict[str, Any]:
    """Independent literal contract fixture; does not use the production row builder."""
    return {
        "schema": "strange-physics.d1-primitive-codec.v1",
        "source_commit": "1" * 40,
        "source_tree": "2" * 40,
        "protocol_sha256": "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399",
        "source_manifest_sha256": "3" * 64,
        "recorder_sha256": "4" * 64,
        "codec_sha256": "5" * 64,
        "run_id": "r0",
        "recorder_id": "c0",
        "max_calls": 55100,
        "case_order": ["M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03"],
        "rows": [
            ["I", 0, "i00", "fixture", None, "member0"],
            ["I", 1, "i01", "strong", None, "member1"],
            ["I", 2, "i02", "weak", None, "member2"],
            ["I", 3, "i03", "future", None, "member3"],
            ["I", 4, "i04", "arithmetic", 0, "member4"],
            ["I", 5, "i05", "arithmetic", 1, "member5"],
            ["I", 6, "i06", "arithmetic", 2, "member6"],
            ["I", 7, "i07", "arithmetic", 3, "member7"],
            ["I", 8, "i08", "arithmetic", 4, "member8"],
            ["I", 9, "i09", "arithmetic", 5, "member9"],
            ["I", 10, "i10", "arithmetic", 6, "member10"],
            ["I", 11, "i11", "arithmetic", 7, "member11"],
            ["I", 12, "i12", "constants", None, "member12"],
            ["I", 13, "i13", "native_emit", None, "member13"],
            ["P", 0, 0, 0, 0, 1],
            ["P", 1, 0, 0, 1, 1],
            ["P", 2, 0, 0, 2, 1],
            ["P", 3, 0, 1, 0, 1],
            ["P", 4, 0, 1, 1, 1],
            ["P", 5, 0, 1, 2, 1],
            ["P", 6, 1, 0, 0, 1],
            ["P", 7, 1, 0, 1, 1],
            ["P", 8, 1, 0, 2, 1],
            ["P", 9, 1, 1, 0, 1],
            ["P", 10, 1, 1, 1, 1],
            ["P", 11, 1, 1, 2, 1],
            ["P", 12, 2, 0, 0, 1],
            ["P", 13, 2, 0, 1, 1],
            ["P", 14, 2, 0, 2, 1],
            ["P", 15, 2, 1, 0, 1],
            ["P", 16, 2, 1, 1, 1],
            ["P", 17, 2, 1, 2, 1],
            ["P", 18, 3, 0, 0, 1],
            ["P", 19, 3, 0, 1, 1],
            ["P", 20, 3, 0, 2, 1],
            ["P", 21, 3, 1, 0, 1],
            ["P", 22, 3, 1, 1, 1],
            ["P", 23, 3, 1, 2, 1],
            ["P", 24, 4, 0, 1, 2],
            ["P", 25, 4, 1, 1, 2],
            ["P", 26, 5, 0, 0, 1],
            ["P", 27, 5, 0, 1, 1],
            ["P", 28, 5, 0, 2, 1],
            ["P", 29, 5, 1, 0, 1],
            ["P", 30, 5, 1, 1, 1],
            ["P", 31, 5, 1, 2, 1],
            ["P", 32, 6, 0, 0, 1],
            ["P", 33, 6, 0, 1, 1],
            ["P", 34, 6, 0, 2, 1],
            ["P", 35, 6, 1, 0, 1],
            ["P", 36, 6, 1, 1, 1],
            ["P", 37, 6, 1, 2, 1],
            ["P", 38, 7, 0, 1, 1],
            ["P", 39, 7, 1, 1, 1],
            ["E", 0, 0, 0],
            ["E", 1, 0, 1],
            ["E", 2, 1, 0],
            ["E", 3, 1, 1],
            ["E", 4, 2, 0],
            ["E", 5, 2, 1],
            ["E", 6, 3, 0],
            ["E", 7, 3, 1],
            ["E", 8, 4, 0],
            ["E", 9, 4, 1],
            ["E", 10, 5, 0],
            ["E", 11, 5, 1],
            ["E", 12, 6, 0],
            ["E", 13, 6, 1],
            ["E", 14, 7, 0],
            ["E", 15, 7, 1],
            ["Q", 0, "train-M01", 1, "a0", "x0", "t0"],
            ["Q", 1, "future-M01", 1, "a0", "x0", "t1"],
            ["Q", 2, "train-M02", 5, "a0", "x0", "t0"],
            ["Q", 3, "future-M02", 5, "a0", "x0", "t1"],
            ["Q", 4, "train-M03", 13, "a0", "x0", "t0"],
            ["Q", 5, "future-M03", 13, "a0", "x0", "t1"],
            ["Q", 6, "train-M04", 27, "a0", "x0", "t0"],
            ["Q", 7, "future-M04", 27, "a0", "x0", "t1"],
            ["Q", 8, "train-F02", 5, "a1", "x0", "t0"],
            ["Q", 9, "future-F02", 5, "a1", "x0", "t1"],
            ["Q", 10, "train-F04", 27, "a1", "x0", "t0"],
            ["Q", 11, "future-F04", 27, "a1", "x0", "t1"],
            ["Q", 12, "train-W03", 13, "a0", "x1", "t0"],
            ["C", 0, "pi", 3],
            ["C", 1, "l2p", 2],
            ["C", 2, "s0", 2],
            ["C", 3, "s1", 2],
            ["C", 4, "s2", 2],
            ["C", 5, "g0", 2],
            ["C", 6, "g1", 2],
            ["V", 0, "position"],
            ["V", 1, "exp"],
            ["V", 2, "log"],
            ["V", 3, "circle_constant"],
            ["V", 4, "native_exp"],
            ["S", 0, "fx"],
            ["S", 1, "ep"],
            ["S", 2, "ne"],
            ["S", 3, "nz"],
            ["S", 4, "ct"],
            ["S", 5, "nv"],
            ["T", 0, "p", "position_key"],
            ["T", 1, "d", "decimal"],
            ["T", 2, "b", "binary64"],
            ["T", 3, "n", "none"],
        ],
    }


def raw(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def identity(value: dict[str, Any]) -> table.TableIdentity:
    return table.TableIdentity(
        value["source_commit"],
        value["source_tree"],
        value["protocol_sha256"],
        value["source_manifest_sha256"],
        value["recorder_sha256"],
        value["codec_sha256"],
        value["run_id"],
        value["recorder_id"],
    )


def bindings(value: dict[str, Any]) -> tuple[str, ...]:
    return tuple(row[5] for row in value["rows"][:14])


def test_independent_literal_table_is_complete_but_unauthenticated() -> None:
    document = example()
    encoded = raw(document)
    result = table.parse_table(encoded)
    assert len(result.rows) == 105
    assert result.rows == tuple(tuple(row) for row in document["rows"])
    assert result.identity == identity(document)
    assert result.source_binding_refs == bindings(document)
    assert result.raw == encoded
    assert result.sha256 == hashlib.sha256(encoded).hexdigest()
    assert result.material_authenticity == "unchecked"


def test_constructor_matches_independently_written_full_contract() -> None:
    document = example()
    assert table.build_table(identity(document), bindings(document)) == raw(document)


def test_valid_extrema_are_far_below_declared_caps() -> None:
    document = example()
    document["run_id"] = "r" * 96
    document["recorder_id"] = "c" * 96
    for row in document["rows"][:14]:
        row[5] = "m" * 32
    encoded = table.build_table(identity(document), bindings(document))
    assert encoded == raw(document)
    header = document | {"rows": []}
    assert len(raw(header)) == 823
    expected_maxima = {"I": 68, "P": 16, "E": 12, "Q": 39, "C": 15, "V": 25, "S": 12, "T": 26}
    for group, bound in expected_maxima.items():
        sizes = [len(raw(row)) - 1 for row in document["rows"] if row[0] == group]
        assert max(sizes) == bound
    assert len(encoded) <= 3625 < 57856
    assert (table.HEADER_BYTES, table.ROW_WITH_SEPARATOR_BYTES, table.TABLE_BYTES) == (
        4096,
        512,
        57856,
    )


def test_shared_source_member_does_not_merge_instance_identities() -> None:
    document = example()
    for row in document["rows"][:14]:
        row[5] = "same.member:-_0"
    result = table.parse_table(raw(document))
    assert len(set(row[2] for row in result.rows[:14])) == 14
    assert len(set(result.source_binding_refs)) == 1


def test_well_shaped_source_changes_are_declarations_not_authentication() -> None:
    document = example()
    document["source_commit"] = "a" * 40
    document["source_manifest_sha256"] = "b" * 64
    result = table.parse_table(raw(document))
    assert result.identity.source_commit == "a" * 40
    assert result.material_authenticity == "unchecked"


def test_builder_copies_revalidated_identity_and_views_are_output_only() -> None:
    document = example()
    declaration = identity(document)
    encoded = table.build_table(declaration, bindings(document))
    view = table.parse_table(encoded)
    object.__setattr__(declaration, "run_id", "other")
    assert view.identity.run_id == "r0"
    with pytest.raises(FrozenInstanceError):
        setattr(view, "raw", b"changed")
    untrusted_view: Any = view
    with pytest.raises(ValueError):
        table.parse_table(untrusted_view)


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        pytest.param("source_commit", "a" * 39, id="short-commit"),
        pytest.param("source_commit", "A" * 40, id="upper-commit"),
        pytest.param("source_tree", "2" * 40 + "\n", id="hash-newline"),
        pytest.param("source_tree", True, id="bool-hash"),
        pytest.param("source_manifest_sha256", "g" * 64, id="nonhex"),
        pytest.param("recorder_sha256", "4" * 63, id="short-digest"),
        pytest.param("codec_sha256", "5" * 64 + "\r\n", id="digest-crlf"),
        pytest.param("protocol_sha256", "6" * 64, id="other-protocol"),
        pytest.param("run_id", "", id="empty-run"),
        pytest.param("run_id", "r" * 97, id="long-run"),
        pytest.param("recorder_id", "r" * 97, id="long-recorder"),
        pytest.param("run_id", "é", id="unicode-id"),
        pytest.param("run_id", "-x", id="leading-punctuation"),
        pytest.param("run_id", "x/y", id="path-id"),
        pytest.param("recorder_id", "x\n", id="control-id"),
    ],
)
def test_header_identity_rejects_wrong_shapes(field: str, bad: object) -> None:
    document = example()
    document[field] = bad
    with pytest.raises(ValueError):
        table.parse_table(raw(document))


@pytest.mark.parametrize(
    "change",
    ["missing", "extra", "schema", "count", "bool-count", "case-order"],
    ids=["missing", "extra", "schema", "count", "bool-count", "case-order"],
)
def test_fixed_root_fields_cannot_select_policy(change: str) -> None:
    document = example()
    if change == "missing":
        del document["codec_sha256"]
    elif change == "extra":
        document["verified"] = True
    elif change == "schema":
        document["schema"] += ".unknown"
    elif change == "count":
        document["max_calls"] = 55101
    elif change == "bool-count":
        document["max_calls"] = True
    else:
        document["case_order"][0:2] = ["M02", "M01"]
    with pytest.raises(ValueError):
        table.parse_table(raw(document))


@pytest.mark.parametrize(
    ("row", "column", "bad"),
    [
        pytest.param(0, 1, False, id="bool-index"),
        pytest.param(0, 2, "i01", id="aliased-instance"),
        pytest.param(4, 3, "fixture", id="wrong-role"),
        pytest.param(4, 4, 1, id="wrong-arithmetic-case"),
        pytest.param(13, 4, 7, id="emitter-not-oracle"),
        pytest.param(14, 2, 1, id="profile-case"),
        pytest.param(17, 3, 0, id="profile-grid"),
        pytest.param(38, 4, 0, id="duplicate-scale"),
        pytest.param(38, 5, 1, id="duplicate-prefix"),
        pytest.param(52, 4, 2, id="weak-scale"),
        pytest.param(54, 2, 1, id="ensemble-case"),
        pytest.param(70, 3, 5, id="query-coefficient"),
        pytest.param(78, 4, "a0", id="omitted-force-anchor"),
        pytest.param(82, 5, "x0", id="weak-initial"),
        pytest.param(71, 6, "t0", id="future-time"),
        pytest.param(83, 3, 2, id="constant-primitive"),
        pytest.param(90, 2, "log", id="primitive-name"),
        pytest.param(95, 2, "ep", id="scope-token"),
        pytest.param(101, 3, "binary64", id="value-kind"),
        pytest.param(0, 5, "a" * 33, id="long-binding"),
        pytest.param(0, 5, "a/b", id="binding-path"),
        pytest.param(0, 5, "a\n", id="binding-control"),
        pytest.param(0, 5, 'a"b', id="binding-quote"),
        pytest.param(0, 5, "é", id="binding-unicode"),
        pytest.param(0, 5, "", id="empty-binding"),
    ],
)
def test_row_joins_and_raw_atom_types_are_fixed(row: int, column: int, bad: object) -> None:
    document = example()
    document["rows"][row][column] = bad
    with pytest.raises(ValueError):
        table.parse_table(raw(document))


@pytest.mark.parametrize(
    "change",
    ["missing", "extra", "swap", "duplicate", "short", "nested"],
    ids=["missing", "extra", "swap", "duplicate", "short", "nested"],
)
def test_complete_row_structure_is_required(change: str) -> None:
    document = example()
    rows = document["rows"]
    if change == "missing":
        rows.pop()
    elif change == "extra":
        rows.append(rows[-1])
    elif change == "swap":
        rows[14], rows[15] = rows[15], rows[14]
    elif change == "duplicate":
        rows[15] = rows[14]
    elif change == "short":
        rows[0].pop()
    else:
        rows[0][5] = {"member": "m0"}
    with pytest.raises(ValueError):
        table.parse_table(raw(document))


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"{", id="truncated-container"),
        pytest.param(b'{"x":"abc', id="truncated-string"),
        pytest.param(b'{"x":1,}', id="syntax"),
        pytest.param(b"[]\n", id="root-array"),
        pytest.param(b'{"x":NaN}\n', id="nan"),
        pytest.param(b'{"x":Infinity}\n', id="infinity"),
        pytest.param(b'{"x":1e999}\n', id="float"),
        pytest.param(b'{"x":' + b"9" * 1000 + b"}\n", id="integer-length"),
        pytest.param(b'{"x":"\xff"}\n', id="non-ascii"),
    ],
)
def test_malformed_or_out_of_domain_json_fails_closed(bad: bytes) -> None:
    with pytest.raises(ValueError):
        table.parse_table(bad)


@pytest.mark.parametrize(
    "change",
    ["leading", "trailing", "no-lf", "two-lf", "inside", "escape", "key-order"],
    ids=["leading", "trailing", "no-lf", "two-lf", "inside", "escape", "key-order"],
)
def test_semantically_equal_noncanonical_bytes_are_rejected(change: str) -> None:
    document = example()
    encoded = raw(document)
    if change == "leading":
        encoded = b" " + encoded
    elif change == "trailing":
        encoded = encoded[:-1] + b" \n"
    elif change == "no-lf":
        encoded = encoded[:-1]
    elif change == "two-lf":
        encoded += b"\n"
    elif change == "inside":
        encoded = encoded.replace(b",", b", ", 1)
    elif change == "escape":
        encoded = encoded.replace(b'"run_id":"r0"', b'"run_id":"\\u00720"')
    else:
        encoded = (json.dumps(document, separators=(",", ":")) + "\n").encode("ascii")
    assert json.loads(encoded) == document
    with pytest.raises(ValueError, match="canonical"):
        table.parse_table(encoded)


def test_duplicate_key_cannot_be_hidden_by_last_value_wins() -> None:
    encoded = raw(example())
    bad = encoded.replace(b'"max_calls":55100', b'"max_calls":1,"max_calls":55100')
    assert json.loads(bad) == example()
    with pytest.raises(ValueError, match="strict table JSON"):
        table.parse_table(bad)


def test_float_and_negative_zero_cannot_alias_fixed_integer_atoms() -> None:
    encoded = raw(example())
    for replacement in (b'["I",0.0,', b'["I",-0,'):
        bad = encoded.replace(b'["I",0,', replacement, 1)
        assert json.loads(bad) == example()
        with pytest.raises(ValueError):
            table.parse_table(bad)


@pytest.mark.parametrize("kind", ["bytes", "depth"], ids=["byte-cap", "depth-cap"])
def test_caps_reject_before_json_parser(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Parser must not run after the pre-parse bound is exceeded")

    bad = b"x" * 57857 if kind == "bytes" else b"[[[[]]]]\n"
    with monkeypatch.context() as scoped:
        scoped.setattr(table.json, "loads", forbidden)
        with pytest.raises(ValueError):
            table.parse_table(bad)


@pytest.mark.parametrize("kind", ["row", "header"], ids=["row-reserve", "header-reserve"])
def test_reachable_budget_checks_include_separator_and_lf(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    document = example()
    encoded = raw(document)
    # Test-only lowering exercises inclusive checks; valid records cannot reach the real caps.
    name = "ROW_WITH_SEPARATOR_BYTES" if kind == "row" else "HEADER_BYTES"
    size = (
        max(len(raw(row)) for row in document["rows"])
        if kind == "row"
        else len(raw(document | {"rows": []}))
    )
    with monkeypatch.context() as scoped:
        scoped.setattr(table, name, size)
        assert table.parse_table(encoded).raw == encoded
        scoped.setattr(table, name, size - 1)
        with pytest.raises(ValueError, match="exceeds"):
            table.parse_table(encoded)


@pytest.mark.parametrize(
    "bad",
    [None, True, "json", bytearray(b"{}"), {}],
    ids=["none", "bool", "string", "mutable-bytes", "mapping"],
)
def test_only_immutable_raw_bytes_enter_parser(bad: Any) -> None:
    with pytest.raises(ValueError):
        table.parse_table(bad)


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        pytest.param("source_commit", True, id="bool"),
        pytest.param("run_id", b"r0", id="bytes"),
        pytest.param("recorder_sha256", "4" * 64 + "\n", id="newline"),
    ],
)
def test_constructor_revalidates_forcibly_mutated_identity(field: str, bad: object) -> None:
    document = example()
    declaration = identity(document)
    object.__setattr__(declaration, field, bad)
    with pytest.raises(ValueError):
        table.build_table(declaration, bindings(document))


@pytest.mark.parametrize(
    "bad",
    [[], (), ("m",) * 13, ("m",) * 15, (True,) * 14],
    ids=["list", "empty", "missing", "extra", "bool"],
)
def test_constructor_rejects_malformed_source_reference_tuple(bad: Any) -> None:
    with pytest.raises(ValueError):
        table.build_table(identity(example()), bad)


def test_constructor_rejects_uninitialized_identity_without_attribute_leak() -> None:
    declaration = object.__new__(table.TableIdentity)
    with pytest.raises(ValueError, match="Complete"):
        table.build_table(declaration, bindings(example()))
