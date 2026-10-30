from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from scripts import ci_analytic_reference as ci


def reports(root: Path) -> None:
    """Synthetic reports only: no analytic helper import or reference construction."""
    rows: list[dict[str, Any]] = []
    for node in ci.NODE_IDS:
        properties: list[tuple[str, str]] = []
        name = node.split("::")[1]
        if name.startswith("test_closed_gaussian_vectors["):
            vector = name.removeprefix("test_closed_gaussian_vectors[").removesuffix("]")
            properties = [
                (
                    "laplace_reference",
                    json.dumps(
                        {
                            "vector": vector,
                            "input_sha256": ci.VECTOR_HASHES[vector],
                            "software_criterion": "2e-12",
                            "oracle_width_ceiling": "2^-170",
                            "max_absolute_binary64_error": "1e-16",
                            "max_exact_oracle_width": "1e-55",
                            "shifted_log_normalizer_directed_decimal": ["0.1", "0.2"],
                        }
                    ),
                )
            ]
        elif name.startswith("test_closed_domain_and_budget_failures["):
            kind = name.removeprefix("test_closed_domain_and_budget_failures[").removesuffix("]")
            properties = [
                ("laplace_rejection", json.dumps({"kind": kind, "reason": ci.REJECTIONS[kind]}))
            ]
        for phase in ("setup", "call", "teardown"):
            rows.append(
                {
                    "nodeid": node,
                    "when": phase,
                    "outcome": "passed",
                    "properties": properties if phase != "setup" else [],
                }
            )
    write_rows(root, rows)
    suite = ET.Element("testsuite")
    for name in ci.CASE_NAMES:
        ET.SubElement(suite, "testcase", name=name)
    ET.ElementTree(suite).write(root / "junit.xml")
    (root / "pytest.log").write_text(
        "LAPLACE_REFERENCE_CENSUS "
        + json.dumps({**ci.CENSUS, "checked_core_operations": 32694})
        + "\n"
    )
    ci.write_json(
        root / "child.json",
        {
            "exit_code": 0,
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "max_rss_kib": 1000,
            "python": "synthetic",
            "pytest": "synthetic",
        },
    )


def write_rows(root: Path, rows: list[dict[str, Any]]) -> None:
    (root / "phases.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


@pytest.mark.parametrize("console_prefix", ["", ci.MODULE + " "])
def test_reference_reports_accept_complete_evidence(tmp_path: Path, console_prefix: str) -> None:
    reports(tmp_path)
    log = tmp_path / "pytest.log"
    log.write_text(console_prefix + log.read_text())
    result = ci.validate_reports(tmp_path)
    assert (result["cases"], result["phases"]) == (24, 72)
    assert len(result["vectors"]) == 8 and len(result["denials"]) == 5
    assert result["max_absolute_binary64_error"] == 1e-16
    assert result["census"]["core_gcd_calls"] == 2117


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_phase",
        "duplicate_phase",
        "phase_order",
        "skip",
        "failure",
        "foreign_node",
        "missing_vector",
        "input_hash",
        "missing_metric",
        "nan_metric",
        "criterion",
        "denial_reason",
        "missing_census",
        "duplicate_census",
        "gcd_count",
        "operation_bound",
        "junit_skip",
        "junit_missing",
        "child_exit",
        "unknown_usage",
    ],
)
def test_reference_reports_reject_incomplete_or_changed_evidence(
    tmp_path: Path, mutation: str
) -> None:
    reports(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "phases.jsonl").read_text().splitlines()]
    if mutation == "missing_phase":
        rows.pop()
    elif mutation == "duplicate_phase":
        rows.append(rows[-1])
    elif mutation == "phase_order":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation in ("skip", "failure"):
        rows[1]["outcome"] = "skipped" if mutation == "skip" else "failed"
    elif mutation == "foreign_node":
        rows[1]["nodeid"] = "tests/other.py::test_foreign"
    elif mutation == "missing_vector":
        rows[2]["properties"] = []
    elif mutation in ("input_hash", "missing_metric", "nan_metric", "criterion"):
        value = json.loads(rows[2]["properties"][0][1])
        if mutation == "input_hash":
            value["input_sha256"] = "0" * 64
        elif mutation == "missing_metric":
            del value["max_absolute_binary64_error"]
        elif mutation == "nan_metric":
            value["max_absolute_binary64_error"] = "NaN"
        else:
            value["software_criterion"] = "1e-6"
        rows[2]["properties"][0][1] = json.dumps(value)
    elif mutation == "denial_reason":
        row = next(
            r
            for r in rows
            if r["when"] == "teardown"
            and "test_closed_domain_and_budget_failures" in r["nodeid"]
        )
        value = json.loads(row["properties"][0][1])
        value["reason"] = "unexpected"
        row["properties"][0][1] = json.dumps(value)
    elif mutation in ("missing_census", "duplicate_census", "gcd_count", "operation_bound"):
        path = tmp_path / "pytest.log"
        text = path.read_text()
        if mutation == "missing_census":
            path.write_text("")
        elif mutation == "duplicate_census":
            path.write_text(text + text)
        else:
            census = {**ci.CENSUS, "checked_core_operations": 32694}
            census["core_gcd_calls" if mutation == "gcd_count" else "checked_core_operations"] = (
                2116 if mutation == "gcd_count" else 40000
            )
            path.write_text("LAPLACE_REFERENCE_CENSUS " + json.dumps(census) + "\n")
    elif mutation in ("junit_skip", "junit_missing"):
        tree = ET.parse(tmp_path / "junit.xml")
        suite = tree.getroot()
        if mutation == "junit_skip":
            ET.SubElement(suite[0], "skipped")
        else:
            suite.remove(suite[0])
        tree.write(tmp_path / "junit.xml")
    else:
        path = tmp_path / "child.json"
        detail = json.loads(path.read_text())
        detail["exit_code" if mutation == "child_exit" else "cpu_seconds"] = (
            1 if mutation == "child_exit" else None
        )
        path.write_text(json.dumps(detail))
    write_rows(tmp_path, rows)
    with pytest.raises(ValueError):
        ci.validate_reports(tmp_path)


def test_reference_junit_rejects_entity_declarations(tmp_path: Path) -> None:
    reports(tmp_path)
    (tmp_path / "junit.xml").write_text(
        '<!DOCTYPE testsuite [<!ENTITY value "unexpected">]>'
        '<testsuite><testcase name="&value;"/></testsuite>'
    )
    with pytest.raises(ValueError, match="must not declare"):
        ci.validate_reports(tmp_path)


def test_reference_report_size_bound(tmp_path: Path) -> None:
    reports(tmp_path)
    (tmp_path / "pytest.log").write_bytes(b"x" * (ci.FILE_LIMIT + 1))
    with pytest.raises(ValueError, match="byte limit"):
        ci.validate_reports(tmp_path)


@pytest.mark.parametrize("state", ["success", "timeout", "unreaped", "late_zero"])
def test_reference_child_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    waits: list[int] = []
    kills: list[bool] = []

    class Process:
        def wait(self, timeout: int) -> int:
            waits.append(timeout)
            if state == "unreaped" or (state == "timeout" and len(waits) == 1):
                raise subprocess.TimeoutExpired("synthetic child", timeout)
            return -9 if state == "timeout" else 0

        def kill(self) -> None:
            kills.append(True)

    def launch(argv: list[str], **kwargs: object) -> Process:
        assert argv[1:3] == ["-I", "-B"]
        assert argv[-2:] == ["--child", str(tmp_path)]
        assert kwargs["stderr"] == subprocess.STDOUT
        assert "stdin" not in kwargs
        return Process()

    monkeypatch.setattr(subprocess, "Popen", launch)
    times = iter([0.0, float(ci.WALL_LIMIT + 1) if state == "late_zero" else 1.0])
    monkeypatch.setattr(ci.time, "monotonic", lambda: next(times))
    result = ci.run_child(tmp_path)
    assert result["success"] is (state == "success")
    assert result["reaped"] is (state != "unreaped")
    assert waits == ([ci.WALL_LIMIT, ci.CLEANUP_LIMIT] if kills else [ci.WALL_LIMIT])
    assert len(kills) == (1 if state in ("timeout", "unreaped") else 0)


def test_reference_output_is_exclusive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ci_analytic_reference.py", str(tmp_path)])
    with pytest.raises(FileExistsError):
        ci.main()


def test_reference_manifest_matches_unchanged_test_source() -> None:
    tree = ast.parse(Path(ci.MODULE).read_text())
    assignment = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "VECTORS" for target in n.targets)
    )
    assert isinstance(assignment.value, ast.Tuple)
    names: list[str] = []
    hashes: dict[str, str] = {}
    fields = ("name", "scale", "mu", "offset", "support", "cells", "queries")
    for item in assignment.value.elts:
        assert isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
        assert item.func.id == "GaussianVector" and not item.keywords
        value = dict(zip(fields, (ast.literal_eval(arg) for arg in item.args), strict=True))
        name = value["name"]
        names.append(name)
        hashes[name] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    assert hashes == ci.VECTOR_HASHES
    cases: list[str] = []
    for function in tree.body:
        if not isinstance(function, ast.FunctionDef) or not function.name.startswith("test_"):
            continue
        if function.name == "test_closed_gaussian_vectors":
            cases.extend(f"{function.name}[{name}]" for name in names)
        elif function.decorator_list:
            decorator = function.decorator_list[0]
            assert isinstance(decorator, ast.Call)
            cases.extend(
                f"{function.name}[{name}]" for name in ast.literal_eval(decorator.args[1])
            )
        else:
            cases.append(function.name)
    assert tuple(cases) == ci.CASE_NAMES
