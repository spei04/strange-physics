from __future__ import annotations

import json
import os
import stat
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import NoReturn

import pytest
from endpoint_belief_reference import EndpointOracle
from grid_q1_bounds import Interval
from grid_q1_driver import Counts, Driver, label
from grid_q1_evidence import (
    EXPECTED_WORK,
    Artifact,
    CaseRow,
    Comparison,
    Gate,
    GridQ1Report,
    IntervalRow,
    OperationRow,
    Output,
    WorkCount,
    around,
    divide,
    encoded,
    minus,
    moments,
    parse_report,
    point,
    probabilities,
    probability_log_envelope,
)
from grid_q1_inputs import History
from grid_q1_reference import EXPECTED, GridQ1Reference


@pytest.fixture(autouse=True)
def no_reference_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("No real reference operations in synthetic driver tests")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, forbidden)


def test_tiny_allowance_is_not_rounded_away() -> None:
    result = around(Decimal(1), Decimal("1e-48"))
    assert result.lower < 1 < result.upper


def test_emitted_weights_are_exactly_renormalized_intervals() -> None:
    p = probabilities((0.1, 0.2))
    # Binary64 0.2 is exactly twice binary64 0.1: exact mass is 1/3.
    # Rational comparison does not reproduce the interval implementation.
    assert Fraction(p[0].lower) * 3 < 1 < Fraction(p[0].upper) * 3
    assert Fraction(p[1].lower) * 3 < 2 < Fraction(p[1].upper) * 3


def test_outward_moments_retain_negative_values() -> None:
    p = probabilities((1.0, 1.0))
    mean, second, variance = moments(p, (-1.0, 1.0))
    assert mean.lower <= 0 <= mean.upper
    assert second.lower <= 1 <= second.upper
    assert variance.lower <= 1 <= variance.upper


@pytest.mark.parametrize("values", [(0.0, 1.0), (float("nan"),), (float("inf"),)])
def test_invalid_emitted_weights_cannot_normalize(values: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        probabilities(values)


def test_unresolved_probability_ratio_rejected() -> None:
    with pytest.raises(ValueError, match="unresolved"):
        probability_log_envelope((point(1),), (Decimal("0.1"),))


def test_zero_interval_divisor_rejected() -> None:
    with pytest.raises(ValueError, match="zero"):
        divide(point(1), Interval(Decimal(-1), Decimal(1)))


@pytest.mark.parametrize(
    "bounds",
    [
        ("NaN", "1"),
        ("0", "Infinity"),
        ("1", "0"),
        ("0", "1e999"),
    ],
)
def test_persisted_intervals_reject_invalid_bounds(bounds: tuple[str, str]) -> None:
    with pytest.raises(ValueError):
        IntervalRow(lower=bounds[0], upper=bounds[1])


def test_gate_cannot_lie_about_failure() -> None:
    with pytest.raises(ValueError):
        Gate(name="endpoint", observed_upper="2e-12", limit="1e-12", passed=True)


def test_attempt_is_counted_before_exception() -> None:
    counts = Counts()

    def failing() -> int:
        raise ValueError("retained")

    with pytest.raises(ValueError, match="retained"):
        counts.call("probe", failing)
    assert counts.rows == {"probe": [1, 0]}


def test_unique_rounding_enclosure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(GridQ1Reference, "interior_label", lambda self: Decimal("0.75"))
    value, evidence = label(GridQ1Reference(), Counts())
    assert value == 0.75
    assert Decimal(evidence.enclosure.lower) < Decimal.from_float(value)
    assert Decimal(evidence.enclosure.upper) > Decimal.from_float(value)


def test_output_is_private_and_cannot_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "out"
    output = Output(root)
    output.event(OperationRow(key="label", kind="label", status="attempted"))
    artifact = output.write("one.json", b"{}")
    assert artifact.bytes == 2
    assert (root.stat().st_mode & 0o077) == 0
    assert ((root / "one.json").stat().st_mode & 0o077) == 0
    assert json.loads((root / "events.jsonl").read_text())["status"] == "attempted"
    with pytest.raises(FileExistsError):
        output.write("one.json", b"{}")
    with pytest.raises(FileExistsError):
        Output(root)


def test_actual_interval_difference_encloses_exact_zero() -> None:
    result = minus(point(Decimal("1e-100")), point(Decimal("1e-100")))
    assert result == point(0)


def test_unrun_manifest_is_durable_before_any_work(tmp_path: Path) -> None:
    driver = Driver(tmp_path / "out", "0" * 40, "0" * 64)
    rows = [
        json.loads(line) for line in (tmp_path / "out" / "events.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 48 and all(row["status"] == "unrun" for row in rows)
    assert driver.counts.snapshot() == ()


def test_failed_operation_keeps_later_work_unrun(tmp_path: Path) -> None:
    driver = Driver(tmp_path / "out", "0" * 40, "0" * 64)

    def broken() -> int:
        raise ValueError("synthetic")

    with pytest.raises(ValueError, match="synthetic"):
        driver.operation("label", broken)
    assert driver.operations[0].status == "failed"
    assert all(row.status == "unrun" for row in driver.operations[1:])
    assert driver.active is None


def test_incomplete_manifest_cannot_claim_pass(tmp_path: Path) -> None:
    driver = Driver(tmp_path / "out", "0" * 40, "0" * 64)
    with pytest.raises(ValueError, match="full diagnostic"):
        GridQ1Report(
            source_commit="0" * 40,
            authority_sha256="0" * 64,
            outcome="passed",
            operations=tuple(driver.operations),
            cases=(),
            comparisons=(),
            work=(),
            reference_census={},
            artifacts=(),
            fatal_type=None,
            fatal_detail=None,
        )


def _full_report() -> GridQ1Report:
    """Invented shape-only evidence; no native or reference calculations."""
    histories: tuple[History, ...] = ("flat", "boundary", "interior")
    counts = (64, 256, 1024)
    scales = (0.125, 0.25, 0.5)
    operations = [
        OperationRow(key="label", kind="label", status="completed"),
        OperationRow(key="constants", kind="constants", status="completed"),
    ]
    cases: list[CaseRow] = []
    artifacts: list[Artifact] = []
    for history in histories:
        for count in counts:
            operations.extend(
                (
                    OperationRow(
                        key=f"{history}-{count}-ensemble", kind="ensemble", status="completed"
                    ),
                    OperationRow(
                        key=f"{history}-{count}-future", kind="future", status="completed"
                    ),
                )
            )
            for si, scale in enumerate(scales):
                key = f"{history}-{count}-s{si}"
                operations.append(OperationRow(key=key, kind="belief", status="completed"))
                evidence = Artifact(path=key + "-evidence.json", sha256="0" * 64, bytes=2)
                certificate = Artifact(path=key + "-certificate.json", sha256="1" * 64, bytes=2)
                artifacts.extend((evidence, certificate))
                declared = [
                    ("training_endpoint", "1e-12"),
                    ("future_endpoint", "1e-12"),
                    ("node_log", "1e-9"),
                    ("centered_log_evidence", "1e-9"),
                    ("normalized_log", "1e-9"),
                    ("reserve-0", "1e-9"),
                    ("reserve-1", "1e-9"),
                    ("reserve-2", "1e-9"),
                    ("cell_tv_bound", "0.0081" if count == 1024 else None),
                    ("continuous_mean_bound", "0.018" if count == 1024 else None),
                    ("continuous_second_bound", "0.019" if count == 1024 else None),
                    ("continuous_variance_bound", "0.056" if count == 1024 else None),
                ]
                gates = [
                    Gate(name=name, observed_upper="0", limit=limit, passed=True)
                    for name, limit in declared
                ]
                if history == "flat":
                    gates.extend(
                        (
                            Gate(
                                name="flat_exact_mean", observed_upper="0", limit="0", passed=True
                            ),
                            Gate(
                                name="flat_exact_second", observed_upper="0", limit="0", passed=True
                            ),
                        )
                    )
                zero = IntervalRow(lower="0", upper="0")
                cases.append(
                    CaseRow(
                        history=history,
                        count=count,
                        scale=scale,
                        evidence=evidence,
                        certificate=certificate,
                        mean=zero,
                        second_moment=zero,
                        variance=zero,
                        boundary_mass=zero,
                        gates=tuple(gates),
                        passed=True,
                    )
                )
    operations.append(OperationRow(key="flat-moments", kind="flat_moments", status="completed"))
    comparisons: list[Comparison] = []
    for history in histories:
        for scale in scales:
            for coarse, fine in ((64, 256), (256, 1024)):
                thresholds = ("0.001", "0.0005", "0.001") if coarse == 256 else (None, None, None)
                comparisons.append(
                    Comparison(
                        key=f"{history}-{scale}-{coarse}-{fine}",
                        kind="refinement",
                        gates=tuple(
                            Gate(name=name, observed_upper="0", limit=limit, passed=True)
                            for name, limit in zip(
                                ("cell_tv", "mean", "variance"), thresholds, strict=True
                            )
                        ),
                    )
                )
        for count in counts:
            for a, b in ((0.125, 0.25), (0.25, 0.5)):
                comparisons.append(
                    Comparison(
                        key=f"{history}-{count}-{a}-{b}",
                        kind="sensitivity",
                        gates=tuple(
                            Gate(name=name, observed_upper="0", limit=None, passed=True)
                            for name in ("cell_tv", "mean", "variance")
                        ),
                    )
                )
    return GridQ1Report(
        source_commit="0" * 40,
        authority_sha256="0" * 64,
        outcome="passed",
        operations=tuple(operations),
        cases=tuple(cases),
        comparisons=tuple(comparisons),
        work=tuple(
            WorkCount(name=key, attempted=n, completed=n) for key, n in EXPECTED_WORK.items()
        ),
        reference_census=dict(EXPECTED),
        artifacts=tuple(artifacts),
        fatal_type=None,
        fatal_detail=None,
    )


def test_exact_synthetic_terminal_report_roundtrips() -> None:
    report = _full_report()
    assert parse_report(encoded(report, 512 * 1024)) == report


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "rename",
        "unguarded",
        "weakened",
        "flat_missing",
        "flat_wrong_limit",
        "coarse_spurious_limit",
    ],
)
def test_profile_gate_substitution_is_rejected(change: str) -> None:
    data = _full_report().model_dump(mode="json")
    gates = data["cases"][0]["gates"]
    if change == "missing":
        del gates[0]
    elif change == "duplicate":
        gates[1] = gates[0]
    elif change == "rename":
        gates[0]["name"] = "substitute"
    elif change == "unguarded":
        gates[0]["limit"] = None
    elif change == "weakened":
        gates[0]["limit"] = "1"
    elif change == "flat_missing":
        for case in data["cases"][:9]:
            case["gates"] = case["gates"][:12]
    elif change == "flat_wrong_limit":
        gates[12]["limit"] = "1"
    else:
        gates[8]["limit"] = ".0081"
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "change",
    [
        "kind",
        "missing_gate",
        "weakened",
        "unguarded",
        "renamed",
        "reordered",
    ],
)
def test_comparison_contract_cannot_be_weakened(change: str) -> None:
    data = _full_report().model_dump(mode="json")
    row = data["comparisons"][1]  # Required 256 -> 1024 refinement.
    if change == "kind":
        row["kind"] = "sensitivity"
    elif change == "missing_gate":
        row["gates"].pop()
    elif change == "weakened":
        row["gates"][0]["limit"] = "1"
    elif change == "unguarded":
        row["gates"][0]["limit"] = None
    elif change == "renamed":
        row["gates"][0]["name"] = "substitute"
    else:
        data["comparisons"][0], data["comparisons"][1] = (
            data["comparisons"][1],
            data["comparisons"][0],
        )
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("change", ["key", "kind"])
def test_operation_identity_cannot_change(change: str) -> None:
    data = _full_report().model_dump(mode="json")
    data["operations"][0][change] = "constants"
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "change",
    [
        "empty",
        "missing",
        "extra",
        "attempted",
        "completed",
        "duplicate",
    ],
)
def test_terminal_work_requires_the_whole_exact_census(change: str) -> None:
    data = _full_report().model_dump(mode="json")
    if change == "empty":
        data["work"] = []
    elif change == "missing":
        data["work"].pop()
    elif change == "extra":
        data["work"].append({"name": "invented", "attempted": 1, "completed": 1})
    elif change == "attempted":
        data["work"][0]["attempted"] += 1
    elif change == "completed":
        data["work"][0]["completed"] -= 1
    else:
        data["work"].append(data["work"][0])
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("change", ["missing", "digest", "size", "alias"])
def test_case_artifact_must_join_exact_final_descriptor(change: str) -> None:
    data = _full_report().model_dump(mode="json")
    if change == "missing":
        data["artifacts"].pop(0)
    elif change == "digest":
        data["artifacts"][0]["sha256"] = "2" * 64
    elif change == "size":
        data["artifacts"][0]["bytes"] += 1
    else:
        data["cases"][0]["evidence"] = data["cases"][1]["evidence"]
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("updated", [0, 3])
def test_incomplete_flat_moment_prefix_is_preserved(updated: int) -> None:
    data = _full_report().model_dump(mode="json")
    data["outcome"] = "incomplete"
    data["fatal_type"] = "OSError"
    data["fatal_detail"] = "synthetic interruption"
    data["operations"][-1]["status"] = "failed"
    data["operations"][-1]["error_type"] = "OSError"
    data["comparisons"] = []
    data["work"] = []
    for case in data["cases"][updated:9]:
        case["gates"] = case["gates"][:12]
    report = GridQ1Report.model_validate_json(json.dumps(data))
    assert [len(c.gates) for c in report.cases[:9]] == [14] * updated + [12] * (9 - updated)


def test_complete_negative_result_stays_failed() -> None:
    data = _full_report().model_dump(mode="json")
    data["outcome"] = "failed"
    data["cases"][9]["gates"][0]["observed_upper"] = "2e-12"
    data["cases"][9]["gates"][0]["passed"] = False
    data["cases"][9]["passed"] = False
    assert GridQ1Report.model_validate_json(json.dumps(data)).outcome == "failed"


def _incomplete_output_report(output: Output) -> GridQ1Report:
    data = _full_report().model_dump(mode="json")
    data.update(outcome="incomplete", fatal_type="OSError", fatal_detail="synthetic")
    for row in data["operations"]:
        row["status"] = "unrun"
    data.update(
        cases=[],
        comparisons=[],
        work=[],
        reference_census={},
        artifacts=[a.model_dump(mode="json") for a in output.artifacts],
    )
    return GridQ1Report.model_validate_json(json.dumps(data))


def test_output_fsyncs_contents_then_directory_before_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, int]] = []
    original = os.fsync

    def observe(fd: int) -> None:
        info = os.fstat(fd)
        observed.append(("directory" if stat.S_ISDIR(info.st_mode) else "file", info.st_ino))
        original(fd)

    monkeypatch.setattr(os, "fsync", observe)
    output = Output(tmp_path / "out")
    assert observed == [("directory", tmp_path.stat().st_ino)]
    output.event(OperationRow(key="label", kind="label", status="unrun"))
    output.write("one.json", b"{}")
    output.finish(_incomplete_output_report(output))
    root_inode = output.root.stat().st_ino
    assert [kind for kind, _ in observed] == [
        "directory",
        "file",
        "directory",
        "file",
        "directory",
        "file",
        "directory",
    ]
    assert all(observed[i] == ("directory", root_inode) for i in (2, 4, 6))


def test_artifact_fsync_error_propagates_without_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = Output(tmp_path / "out")

    def fail(fd: int) -> NoReturn:
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError, match="fsync failure"):
        output.write("one.json", b"{}")
    assert output.artifacts == []
    assert (output.root / "one.json").read_bytes() == b"{}"


def test_final_directory_sync_failure_cannot_return_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = Output(tmp_path / "out")
    original = os.fsync

    def fail_directory(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("synthetic directory failure")
        original(fd)

    monkeypatch.setattr(os, "fsync", fail_directory)
    with pytest.raises(OSError, match="directory failure"):
        output.finish(_incomplete_output_report(output))
    assert (output.root / "report.json").exists()


def test_complete_report_rejects_empty_fatal_metadata() -> None:
    data = _full_report().model_dump(mode="json")
    data.update(fatal_type="", fatal_detail="")
    with pytest.raises(ValueError):
        GridQ1Report.model_validate_json(json.dumps(data))
