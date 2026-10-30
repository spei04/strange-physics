"""Run the fixed analytic-reference tests once and verify their bounded CI reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.parsers import expat

if TYPE_CHECKING:
    import pytest

MODULE = "tests/test_laplace_analytic_reference.py"
FILE_LIMIT = 128 * 1024
TOTAL_LIMIT = 1024 * 1024
WALL_LIMIT = 360
CLEANUP_LIMIT = 5
VECTOR_HASHES = {
    "real": "396ad8cab37ece43640cf6cabc60553ebeebf13806540f1afdc5d867b60c567c",
    "shift": "e94c701188a4ac6964c748b53efb06bd167efccd10c1f773e79db5357f90f7b5",
    "scaled": "c383fd07f0accb75378f842ef1c52391479ad132e20131a322d95327a6b8c900",
    "symmetric": "6d4fbfa00e371b45b25208573f6c6d92d99106057194351ed45d21d2ff5ab12a",
    "left_boundary": "ffa63b8d56711076c1f01d09a74030555e04a2df180baf74d0e01a8525fdc2c7",
    "right_boundary": "f244ae586da61a5c5d3d2e811a7c91c954344814ae796670766920a5efadf832",
    "tail": "09049de106e81d7a9a8cb7f7d8c7976653d16d12252b77334326b137b14265e0",
    "weak": "610b38026a3fb62b71e59190be05a2307912f157c212b907ef76a414880330d5",
}
REJECTIONS = {
    "nonpositive_scale": "positive_scale_family",
    "non_lattice": "query_domain",
    "deep_tail": "query_domain",
    "work_exhaustion": "operations",
    "too_many": "vector_count",
}
CASE_NAMES = (
    *(f"test_closed_gaussian_vectors[{name}]" for name in VECTOR_HASHES),
    *(
        f"test_exact_relations[{name}]"
        for name in ("shift", "jacobian", "symmetry", "partition", "weak")
    ),
    *(
        f"test_plausible_reference_defects[{name}]"
        for name in ("jacobian", "density_for_cell", "clip", "remainder")
    ),
    *(f"test_closed_domain_and_budget_failures[{name}]" for name in REJECTIONS),
    "test_boundary_stationarity_and_nonpositive_curvature",
    "test_local_jets_do_not_determine_global_mass",
)
NODE_IDS = tuple(f"{MODULE}::{name}" for name in CASE_NAMES)
CENSUS = {
    "vectors": 8,
    "integrals": 21,
    "endpoint_logs": 44,
    "polynomial_visits": 4074,
    "logarithm_terms": 2880,
    "machin_terms": 128,
    "core_gcd_calls": 2117,
}
REPORT_FILES = ("pytest.log", "phases.jsonl", "junit.xml", "child.json", "result.json")


def bounded_read(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(FILE_LIMIT + 1)
    if len(raw) > FILE_LIMIT:
        raise ValueError(f"Report exceeds byte limit: {path.name}")
    return raw


def write_json(path: Path, value: object) -> None:
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    if len(raw) > FILE_LIMIT:
        raise ValueError("Result exceeds byte limit")
    with path.open("xb") as stream:
        stream.write(raw)


class PhaseReports:
    """Observe reports only; do not change test selection or numerical execution."""

    def __init__(self, root: Path) -> None:
        self.path = root / "phases.jsonl"
        self.count = 0
        self.bytes = 0

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.count += 1
        row = {
            "nodeid": report.nodeid,
            "when": report.when,
            "outcome": report.outcome,
            "duration": report.duration,
            "properties": list(report.user_properties),
        }
        if report.failed:
            row["failure"] = str(report.longrepr)[:32768]
        raw = (json.dumps(row, sort_keys=True) + "\n").encode()
        if self.count > 72 or self.bytes + len(raw) > FILE_LIMIT:
            raise ValueError("Phase report bound exceeded")
        with self.path.open("ab") as stream:
            stream.write(raw)
        self.bytes += len(raw)


def child(root: Path) -> int:
    # One audited, non-spawning test module. These are not process-tree limits.
    resource.setrlimit(resource.RLIMIT_CPU, (295, 300))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, FILE_LIMIT))
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ["PYTEST_ADDOPTS"] = ""
    import pytest

    start = time.monotonic()
    code = pytest.main(
        [
            "--noconftest",
            "--import-mode=prepend",
            "-o",
            "addopts=",
            "-o",
            "pythonpath=",
            "-o",
            "junit_family=xunit1",
            "-s",
            "-x",
            "--tb=short",
            "--show-capture=no",
            "-p",
            "no:cacheprovider",
            f"--basetemp={root / 'tmp'}",
            f"--junitxml={root / 'junit.xml'}",
            MODULE,
        ],
        plugins=[PhaseReports(root)],
    )
    usage = resource.getrusage(resource.RUSAGE_SELF)
    write_json(
        root / "child.json",
        {
            "exit_code": int(code),
            "python": sys.version,
            "pytest": pytest.__version__,
            "cpu_seconds": usage.ru_utime + usage.ru_stime,
            "wall_seconds": time.monotonic() - start,
            "max_rss_kib": usage.ru_maxrss,
        },
    )
    return int(code)


def run_child(root: Path) -> dict[str, object]:
    """No pipes or readers: a bounded child log survives failure and timeout."""
    start = time.monotonic()
    timed_out = False
    reaped = False
    code: int | None = None
    with (root / "pytest.log").open("xb") as log:
        process = subprocess.Popen(
            [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--child", str(root)],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            try:
                code = process.wait(timeout=WALL_LIMIT)
                reaped = True
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            if not reaped:
                # The Popen instance still owns this un-reaped child. No saved group/PID is used.
                try:
                    process.kill()
                finally:
                    try:
                        code = process.wait(timeout=CLEANUP_LIMIT)
                        reaped = True
                    except subprocess.TimeoutExpired:
                        pass
    elapsed = time.monotonic() - start
    return {
        "exit_code": code,
        "timed_out": timed_out,
        "reaped": reaped,
        "wall_seconds": elapsed,
        "success": reaped and not timed_out and code == 0 and elapsed <= WALL_LIMIT,
    }


def junit_case_names(raw: bytes) -> list[str]:
    parser = expat.ParserCreate()
    names: list[str] = []

    def start(name: str, attributes: dict[str, str]) -> None:
        if name in ("failure", "error", "skipped"):
            raise ValueError("JUnit contains an unsuccessful case")
        if name == "testcase":
            names.append(attributes.get("name", ""))

    def reject_doctype(*args: object) -> None:
        raise ValueError("JUnit must not declare entities or a document type")

    parser.StartElementHandler = start
    parser.StartDoctypeDeclHandler = reject_doctype
    parser.Parse(raw, True)
    return names


def validate_reports(root: Path) -> dict[str, Any]:
    """Check retained observations; never import or recompute the reference pack."""
    entries = list(root.iterdir())
    if any(p.name not in REPORT_FILES and p.name != "tmp" for p in entries):
        raise ValueError("Unexpected report output")
    total = 0
    for path in entries:
        if path.name == "tmp":
            if path.is_symlink() or (path.exists() and any(path.iterdir())):
                raise ValueError("Unexpected reference temporary output")
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("Reports must be regular files")
        total += len(bounded_read(path))
    if total > TOTAL_LIMIT:
        raise ValueError("Combined report bound exceeded")
    rows = [json.loads(line) for line in bounded_read(root / "phases.jsonl").splitlines()]
    expected = [(node, phase) for node in NODE_IDS for phase in ("setup", "call", "teardown")]
    observed = [(row.get("nodeid"), row.get("when")) for row in rows]
    if (
        len(rows) != 72
        or observed != expected
        or any(row.get("outcome") != "passed" for row in rows)
    ):
        raise ValueError("Expected all 24 cases and 72 ordered passing phases")
    if junit_case_names(bounded_read(root / "junit.xml")) != list(CASE_NAMES):
        raise ValueError("JUnit coverage or outcome mismatch")
    vectors: list[dict[str, Any]] = []
    denials: list[dict[str, Any]] = []
    for row in rows:
        if row["when"] != "teardown":
            continue
        props = row.get("properties")
        if not isinstance(props, list) or len(props) > 1:
            raise ValueError("Unexpected test properties")
        for key, value in props:
            if not isinstance(value, str) or len(value) > 8192:
                raise ValueError("Invalid property encoding")
            data = json.loads(value)
            if key == "laplace_reference":
                name = data.get("vector")
                expected_node = f"{MODULE}::test_closed_gaussian_vectors[{name}]"
                if name not in VECTOR_HASHES or row["nodeid"] != expected_node:
                    raise ValueError("Unexpected vector identity")
                if data.get("input_sha256") != VECTOR_HASHES[name]:
                    raise ValueError("Vector input identity mismatch")
                if (
                    data.get("software_criterion") != "2e-12"
                    or data.get("oracle_width_ceiling") != "2^-170"
                ):
                    raise ValueError("Changed numerical criterion")
                for field, ceiling in (
                    ("max_absolute_binary64_error", 2e-12),
                    ("max_exact_oracle_width", 2.0**-170),
                ):
                    raw = data.get(field)
                    if not isinstance(raw, str) or len(raw) > 128:
                        raise ValueError("Missing or oversized numerical diagnostic")
                    number = float(raw)
                    if not math.isfinite(number) or not 0 <= number < ceiling:
                        raise ValueError("Numerical diagnostic outside fixed criterion")
                bounds = data.get("shifted_log_normalizer_directed_decimal")
                if (
                    not isinstance(bounds, list)
                    or len(bounds) != 2
                    or any(not isinstance(v, str) or len(v) > 256 for v in bounds)
                ):
                    raise ValueError("Missing normalizer diagnostics")
                try:
                    lower, upper = (Decimal(value) for value in bounds)
                except InvalidOperation as error:
                    raise ValueError("Invalid normalizer decimal diagnostics") from error
                if not lower.is_finite() or not upper.is_finite() or lower > upper:
                    raise ValueError("Normalizer diagnostics must be finite and ordered")
                vectors.append(data)
            elif key == "laplace_rejection":
                kind = data.get("kind")
                expected_node = f"{MODULE}::test_closed_domain_and_budget_failures[{kind}]"
                if kind not in REJECTIONS or row["nodeid"] != expected_node:
                    raise ValueError("Unexpected denial identity")
                if data.get("reason") != REJECTIONS[kind]:
                    raise ValueError("Denial reason mismatch")
                denials.append(data)
            else:
                raise ValueError("Unexpected property")
    if (
        [v["vector"] for v in vectors] != list(VECTOR_HASHES)
        or [d["kind"] for d in denials] != list(REJECTIONS)
    ):
        raise ValueError("Missing vector or denial diagnostics")
    prefixes = ("LAPLACE_REFERENCE_CENSUS ", f"{MODULE} LAPLACE_REFERENCE_CENSUS ")
    census_rows = [
        json.loads(line[len(prefix) :])
        for line in bounded_read(root / "pytest.log").decode().splitlines()
        for prefix in prefixes
        if line.startswith(prefix)
    ]
    if len(census_rows) != 1:
        raise ValueError("Expected one reference census")
    census = census_rows[0]
    if (
        {k: v for k, v in census.items() if k != "checked_core_operations"} != CENSUS
        or any(type(census[k]) is not int for k in CENSUS)
    ):
        raise ValueError("Reference census mismatch")
    operations = census.get("checked_core_operations")
    if type(operations) is not int or not 0 < operations < 40000:
        raise ValueError("Reference operation count rejected")
    detail = json.loads(bounded_read(root / "child.json"))
    if detail.get("exit_code") != 0:
        raise ValueError("Child result rejected")
    for field, ceiling in (("cpu_seconds", 300), ("wall_seconds", WALL_LIMIT)):
        value = detail.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= ceiling:
            raise ValueError("Child usage missing or outside bound")
    if type(detail.get("max_rss_kib")) is not int or detail["max_rss_kib"] <= 0:
        raise ValueError("Child memory observation missing")
    if not all(isinstance(detail.get(field), str) for field in ("python", "pytest")):
        raise ValueError("Child runtime identity missing")
    return {
        "cases": 24,
        "phases": 72,
        "vectors": vectors,
        "denials": denials,
        "census": census,
        "usage": detail,
        "max_absolute_binary64_error": max(
            float(v["max_absolute_binary64_error"]) for v in vectors
        ),
        "max_exact_oracle_width": max(float(v["max_exact_oracle_width"]) for v in vectors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    if args.child:
        os.umask(0o077)
        return child(root)
    root.mkdir(mode=0o700)
    os.umask(0o077)
    result: dict[str, Any] = {"success": False, "source": os.environ.get("GITHUB_SHA")}
    try:
        process = run_child(root)
        result["process"] = process
        if not process["success"]:
            raise ValueError("Reference process did not complete within its bound")
        result["reports"] = validate_reports(root)
        result["source_files"] = {
            name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
            for name in (MODULE, "tests/laplace_analytic_reference.py")
        }
        result["success"] = True
    except (OSError, ValueError, KeyError, TypeError, AttributeError, expat.ExpatError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    write_json(root / "result.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
