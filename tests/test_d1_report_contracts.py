"""Synthetic structural fixtures only; no labels, forecasts or physical calls."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

import d1_report_contracts as c
from strange_physics.calibration_fixture_contracts import PROTOCOL_SHA256
from strange_physics.control_contracts import ContractViolation

D = Decimal


def fixture(*, complete: bool = True) -> c.D1ReportStructure:
    tables = tuple(c.TableRef(
        table_id=kind, kind=kind, path=f"{kind}/rows.jsonl", codec=f"{kind}-v1",
        byte_length=1000, raw_sha256="1" * 64, record_count=count
    ) for kind, count in zip(c.KINDS, c.GROUP_COUNTS, strict=True)) if complete else ()
    seen = dict.fromkeys(c.KINDS, 0)
    rows = []
    for ordinal, spec in enumerate(c.ROW_MANIFEST):
        slot = c.TableSlot(table_id=spec.kind, index=seen[spec.kind]) if complete else None
        seen[spec.kind] += 1
        rows.append(c.RowState(
            ordinal=ordinal, key=spec.key, kind=spec.kind, dependencies=spec.dependencies,
            state="completed" if complete else "unrun", completion=slot,
            reason=None if complete else "not-started"
        ))
    frozen = tuple(rows)
    return c.D1ReportStructure(
        protocol_sha256=PROTOCOL_SHA256, source_commit="1" * 40, source_tree="2" * 40,
        run_id="synthetic-only", declared_execution="complete" if complete else "incomplete",
        incomplete_reason=None if complete else "not-started", rows=frozen,
        denominators=c.group_denominators(frozen), tables=tables
    )


def check(value: c.D1ReportStructure) -> c.D1ReportStructure:
    return c.validate_report_structure(value)


def test_exact_manifest_counts_and_critical_dependencies() -> None:
    rows = c.ROW_MANIFEST
    assert len(rows) == len({r.key for r in rows}) == 135
    expected = {
        "fixture": 8, "belief": 40, "prior": 16, "prequential": 18,
        "refinement": 20, "scale": 12, "stress": 16, "primary": 4, "aggregate": 1
    }
    assert {k: sum(r.kind == k for r in rows) for k in expected} == expected
    by_key = {r.key: r for r in rows}
    for count in (256, 1024):
        assert by_key[f"prequential/D03/{count}/record1"].dependencies == (
            "fixture/D03", "fixture/M03", f"belief/M03/{count}/0.25"
        )
        assert f"prequential/D03/{count}/record1" in by_key[f"belief/D03/{count}/0.25"].dependencies
    assert rows[-1].dependencies == tuple(r.key for r in rows[:-1])
    assert not any("D03/256/0.125" in r.key or "W03/1024/0.5" in r.key for r in rows)


@pytest.mark.parametrize("complete", [True, False])
def test_all_rows_round_trip_without_material_acceptance(complete: bool) -> None:
    original = fixture(complete=complete)
    actual = c.parse_report_structure(original.model_dump_json().encode())
    assert actual == original == check(original)
    assert actual.qualification == actual.utility == "unavailable"
    assert actual.material_authenticity == "unchecked"
    assert sum(x.planned for x in actual.denominators) == 135
    assert sum(x.completed if complete else x.unrun for x in actual.denominators) == 135


@pytest.mark.parametrize("fault", ["missing", "duplicate", "extra", "reordered"])
def test_full_denominator_rejects_survivor_or_extra_rows(fault: str) -> None:
    value = fixture()
    rows = value.rows
    if fault == "missing":
        rows = rows[:-1]
    elif fault == "duplicate":
        rows = (rows[1], *rows[1:])
    elif fault == "extra":
        rows = (*rows, rows[0])
    else:
        rows = (rows[1], rows[0], *rows[2:])
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"rows": rows}))


@pytest.mark.parametrize("field,replacement", [
    ("kind", "belief"), ("key", "fixture/renamed"), ("ordinal", 1),
    ("dependencies", ("fixture/M02",)), ("completion", None),
    ("reason", "silently-ignored"), ("state", "unrun"),
])
def test_actual_nested_row_bypasses_are_revalidated(field: str, replacement: object) -> None:
    value = fixture()
    bad = value.rows[0].model_copy(update={field: replacement})
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"rows": (bad, *value.rows[1:])}))


def test_constructed_nested_mapping_is_normalized_before_cross_row_access() -> None:
    value = fixture()
    copied = c.D1ReportStructure.model_construct(**value.model_dump(mode="python"))
    assert check(copied) == value


def test_changed_denominator_is_rejected_even_with_same_total() -> None:
    value = fixture()
    first = value.denominators[0].model_copy(update={"completed": 7, "failed": 1})
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"denominators": (first, *value.denominators[1:])}))


@pytest.mark.parametrize("field,replacement", [
    ("qualification", "qualified"), ("utility", "local-screen-passed"),
    ("material_authenticity", "verified"), ("validation_scope", "numerical"),
    ("protocol_sha256", "f" * 64), ("source_commit", "0" * 40),
    ("source_tree", "0" * 40), ("incomplete_reason", "ignored failure"),
])
def test_structure_cannot_promote_itself_or_hide_control_failure(
    field: str, replacement: object
) -> None:
    with pytest.raises(ContractViolation):
        check(fixture().model_copy(update={field: replacement}))


def test_partial_and_failed_rows_remain_in_denominators() -> None:
    value = fixture(complete=False)
    table = c.TableRef(
        table_id="partial", kind="fixture", path="fixture/partial.json", codec="fixture-v1",
        byte_length=10, raw_sha256="1" * 64, record_count=1
    )
    fault = c.TableRef(
        table_id="first-fault", kind="fault", path="fault/first.json", codec="fault-v1",
        byte_length=10, raw_sha256="2" * 64, record_count=1
    )
    slot = c.TableSlot(table_id="first-fault", index=0)
    failed = value.rows[0].model_copy(update={
        "state": "failed", "fault": slot, "partial": (c.TableSlot(table_id="partial", index=0),),
        "reason": "retained synthetic failure"
    })
    attempted = value.rows[1].model_copy(update={"state": "attempted", "reason": "unknown-exit"})
    rows = (failed, attempted, *value.rows[2:])
    actual = check(value.model_copy(update={
        "rows": rows, "tables": (table, fault), "first_fault": slot,
        "denominators": c.group_denominators(rows)
    }))
    assert actual.denominators[0] == c.Denominator(
        kind="fixture", planned=8, unrun=6, attempted=1, completed=0, failed=1
    )
    assert actual.declared_execution == "incomplete" and len(actual.rows) == 135


@pytest.mark.parametrize("fault", ["failed-no-fault", "unrun-material", "attempted-completion"])
def test_incomplete_states_cannot_fabricate_terminal_evidence(fault: str) -> None:
    value = fixture(complete=False)
    changes: dict[str, object]
    if fault == "failed-no-fault":
        changes = {"state": "failed"}
    elif fault == "unrun-material":
        changes = {"partial": (c.TableSlot(table_id="anything", index=0),)}
    else:
        changes = {"state": "attempted", "completion": c.TableSlot(table_id="anything", index=0)}
    row = value.rows[0].model_copy(update=changes)
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"rows": (row, *value.rows[1:])}))


def test_completed_row_cannot_hide_unfinished_dependency() -> None:
    value = fixture()
    first = value.rows[0].model_copy(update={
        "state": "attempted", "completion": None, "reason": "missing-source"
    })
    rows = (first, *value.rows[1:])
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={
            "rows": rows, "denominators": c.group_denominators(rows),
            "declared_execution": "incomplete", "incomplete_reason": "missing-source"
        }))


@pytest.mark.parametrize("fault", ["unknown", "wrong-kind", "out-of-range", "alias"])
def test_completed_material_must_join_exact_table_role_and_slot(fault: str) -> None:
    value = fixture()
    table_id, index = "fixture", 0
    if fault == "unknown":
        table_id = "missing"
    elif fault == "wrong-kind":
        table_id = "belief"
    elif fault == "out-of-range":
        index = 8
    else:
        index = 1
    bad = value.rows[0].model_copy(update={
        "completion": c.TableSlot(table_id=table_id, index=index)
    })
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"rows": (bad, *value.rows[1:])}))


@pytest.mark.parametrize("fault", ["duplicate-id", "duplicate-path", "orphan", "zero-digest"])
def test_table_descriptor_set_is_exact(fault: str) -> None:
    value = fixture()
    tables = value.tables
    if fault == "duplicate-id":
        tables = (*tables, tables[0])
    elif fault == "duplicate-path":
        tables = (*tables, tables[0].model_copy(update={"table_id": "duplicate"}))
    elif fault == "orphan":
        tables = (*tables, tables[0].model_copy(update={
            "table_id": "unused", "path": "fixture/unused.json"
        }))
    else:
        tables = (tables[0].model_copy(update={"raw_sha256": "0" * 64}), *tables[1:])
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"tables": tables}))


@pytest.mark.parametrize("path", [
    "/fixture/a.json", "fixture/../a.json", "fixture/./a.json", "fixture//a.json",
    "fixture/a.json/", "belief/a.json", "fixture/a.py", "fixture/a.json\n",
])
def test_descriptor_path_does_not_allow_resolver_escape(path: str) -> None:
    data = fixture().tables[0].model_dump(mode="python")
    data["path"] = path
    with pytest.raises(ValueError):
        c.TableRef.model_validate(data)


def test_declared_byte_overflow_fails_without_claiming_physical_fit() -> None:
    value = fixture()
    tables = tuple(c.TableRef(
        table_id=f"t-{r.ordinal}", kind=r.kind, path=f"{r.kind}/{r.ordinal}.json",
        codec=r.kind + "-v1", byte_length=c.TABLE_BYTES, raw_sha256="1" * 64, record_count=1
    ) for r in value.rows)
    rows = tuple(r.model_copy(update={"completion": c.TableSlot(table_id=t.table_id, index=0)})
                 for r, t in zip(value.rows, tables, strict=True))
    with pytest.raises(ContractViolation):
        check(value.model_copy(update={"rows": rows, "tables": tables}))


@pytest.mark.parametrize("text", ["-0.000", "1.2300", "1e-256", "1e128", "-1e128"])
def test_decimal_tuple_round_trip_preserves_exact_representation(text: str) -> None:
    value = D(text)
    assert c.decode_decimal(c.encode_decimal(value)).as_tuple() == value.as_tuple()


@pytest.mark.parametrize("text", ["NaN", "Infinity", "1e129", "1e-257", "1" * 121])
def test_decimal_bounds_are_not_silently_rounded(text: str) -> None:
    with pytest.raises(ValueError):
        c.encode_decimal(D(text))


@pytest.mark.parametrize("changes", [
    {"sign": True}, {"sign": 2}, {"digits": "01"}, {"digits": "1\n"},
    {"exponent": True}, {"exponent": -257}, {"digits": "2", "exponent": 128},
])
def test_constructed_decimal_is_revalidated(changes: dict[str, object]) -> None:
    bad = c.encode_decimal(D(1)).model_copy(update=changes)
    with pytest.raises(ValueError):
        c.decode_decimal(bad)


@pytest.mark.parametrize("value", [0.0, -0.0, 0.125, 1e-300])
def test_binary64_round_trip_is_exact(value: float) -> None:
    assert c.decode_binary64(c.encode_binary64(value)).hex() == value.hex()


@pytest.mark.parametrize("text", [
    "nan", "inf", "0x1p+999999999", "0x1p+0", "0x1.0000000000000p+0\n"
])
def test_binary64_nonfinite_noncanonical_and_overflow_are_contained(text: str) -> None:
    with pytest.raises(ValueError):
        c.Binary64Atom(value=text)


def test_interval_reversal_is_rejected() -> None:
    with pytest.raises(ValueError):
        c.IntervalAtom(lower=c.encode_decimal(D(1)), upper=c.encode_decimal(D(0)))


@pytest.mark.parametrize("fault", ["duplicate-key", "nonfinite", "extra-field", "depth", "bytes"])
def test_bounded_raw_parser_rejects_nonstructural_input(
    fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = fixture(complete=False).model_dump_json().encode()
    if fault == "duplicate-key":
        raw = b'{"run_id":"duplicate",' + raw[1:]
    elif fault == "nonfinite":
        raw = b'{"untrusted":NaN,' + raw[1:]
    elif fault == "extra-field":
        data = json.loads(raw)
        data["passed"] = True
        raw = json.dumps(data).encode()
    elif fault == "depth":
        raw = b"[" * 17 + b"0" + b"]" * 17
    else:
        monkeypatch.setattr(c, "REPORT_BYTES", 64)
    with pytest.raises(ContractViolation):
        c.parse_report_structure(raw)
