"""One fixed I1 walkthrough, plus an explicitly illustrative endpoint diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import stat
import subprocess
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import strange_physics
from strange_physics.cli import main as physics_main
from strange_physics.contracts import ObservationBundle
from strange_physics.native_candidates import produce_native_candidates
from strange_physics.native_endpoint_belief_contracts import (
    EndpointBeliefProfile,
    EndpointCell,
    NativeEndpointBeliefInput,
    bind_native_endpoint_belief_result,
)
from strange_physics.native_endpoint_beliefs import compute_native_endpoint_belief
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.workflow_contracts import (
    SpringFitArtifact,
    SpringPredictionArtifact,
    SpringPreparationArtifact,
    SpringScoreArtifact,
)
from strange_physics.workflow_io import (
    private_stat,
    read_bytes,
    read_message,
    read_stage,
    safe_path,
    stage_message,
)

MIB = 1024 * 1024
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, data: bytes) -> None:
    if len(data) > 16 * MIB:
        raise ValueError("demo_file_limit")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _json(path: Path, value: object) -> None:
    _write(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(SOURCE_ROOT), *args], check=True, capture_output=True, timeout=10
    )
    if len(result.stdout) + len(result.stderr) > 64 * 1024:
        raise ValueError("demo_git_output_limit")
    return result.stdout.decode()


def _identity(expected_commit: str) -> dict[str, object]:
    """Bind actual installed Python files to this clean source, without installation."""
    head, tree = _git("rev-parse", "HEAD", "HEAD^{tree}").splitlines()
    if head != expected_commit or _git("status", "--porcelain"):
        raise ValueError("demo_source_mismatch_or_dirty")
    package = Path(strange_physics.__file__).resolve().parent
    if not package.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError("demo_requires_installed_package")
    entries = _git("ls-tree", "-r", "HEAD", "src/strange_physics").splitlines()
    if not 1 <= len(entries) <= 128:
        raise ValueError("demo_package_count")
    hashes: dict[str, str] = {}
    total = 0
    for entry in entries:
        header, name = entry.split("\t", 1)
        mode, kind, expected = header.split()
        relative = Path(name).relative_to("src/strange_physics")
        if mode != "100644" or kind != "blob" or len(relative.parts) != 1:
            raise ValueError("demo_package_shape")
        path = package / relative
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MIB:
            raise ValueError("demo_package_file")
        data = path.read_bytes()
        total += len(data)
        if total > 4 * MIB:
            raise ValueError("demo_package_size")
        blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data, usedforsecurity=False
        ).hexdigest()
        if blob != expected:
            raise ValueError("demo_installed_package_mismatch")
        hashes[str(relative)] = hashlib.sha256(data).hexdigest()
    if {p.name for p in package.iterdir() if p.is_file() and p.suffix == ".py"} != set(hashes):
        raise ValueError("demo_installed_package_inventory")
    interpreter = Path(sys.executable).resolve()
    if interpreter.stat().st_size > 32 * MIB:
        raise ValueError("demo_interpreter_size")
    with interpreter.open("rb") as stream:
        interpreter_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "source_commit": head, "source_tree": tree,
        "example_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "uv_lock_sha256": hashlib.sha256((SOURCE_ROOT / "uv.lock").read_bytes()).hexdigest(),
        "python": sys.version, "executable": sys.executable,
        "interpreter_sha256": interpreter_sha,
        "installed_package_path": str(package), "installed_package_sha256": hashes,
        "qualification": "Source/package equality; not a sandbox or full dependency audit.",
    }


def _inventory(root: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    total = 0
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            private_stat(info, directory=True)
            continue
        private_stat(info)
        if info.st_nlink != 1 or len(files) >= 64:
            raise ValueError("demo_output_shape")
        data = read_bytes(path, limit=16 * MIB)
        total += len(data)
        if total > 64 * MIB:
            raise ValueError("demo_output_limit")
        files.append({
            "path": str(path.relative_to(root)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return files


def _target_met(rmses: tuple[float | None, ...], claimed: bool) -> bool:
    return claimed and len(rmses) == 24 and all(
        value is not None and math.isfinite(value) and 0 <= value <= 0.001 for value in rmses
    )


def _commands(run: Path) -> tuple[list[str], ...]:
    return (
        ["investigate", "--family", "spring", "--particles", "1", "--budget", "4",
         "--stationary", "--noise", "0", "--seed", "7", "--directory", str(run)],
        ["fit-spring", "--observations", str(run / "observations.json"),
         "--output", str(run / "fit")],
        ["prepare-spring-evaluation", "--journal", str(run / "session.sqlite"),
         "--fit", str(run / "fit"), "--output", str(run / "evaluation")],
        ["predict-spring", "--model", str(run / "fit/model.json"),
         "--manifest", str(run / "evaluation/protocol.json"),
         "--output", str(run / "predictions")],
        ["score-spring", "--journal", str(run / "session.sqlite"),
         "--fit", str(run / "fit"), "--evaluation", str(run / "evaluation"),
         "--predictions", str(run / "predictions"), "--output", str(run / "score")],
    )


def _run(output: Path, cells: int, discrepancy: float, source_commit: str) -> int:
    run = output / "run"
    for index, command in enumerate(_commands(run)):
        stdout, stderr = io.StringIO(), io.StringIO()
        cpu, wall = time.process_time_ns(), time.monotonic_ns()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = physics_main(command)
        if len((stdout.getvalue() + stderr.getvalue()).encode()) > 64 * 1024:
            raise ValueError("demo_cli_log_limit")
        _json(output / f"command-{index}.json", {
            "argv": command, "exit_code": code,
            "cpu_ns": time.process_time_ns() - cpu, "wall_ns": time.monotonic_ns() - wall,
            "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
        })
        print(stdout.getvalue(), end="", flush=True)
        _inventory(output)
        if code:
            raise ValueError(f"demo_stage_{index}_failed")

    observations = read_message(run / "observations.json", ObservationBundle, limit=MIB)
    if len(observations.records) != 4 or any(r.status != "completed" for r in observations.records):
        raise ValueError("demo_requires_four_completed_purchases")
    fit = stage_message(read_stage(run / "fit", "fit"), "fit.json", SpringFitArtifact)
    score = stage_message(read_stage(run / "score", "score"), "score.json", SpringScoreArtifact)
    preparation = stage_message(
        read_stage(run / "evaluation", "prepare"), "preparation.json", SpringPreparationArtifact
    )
    predictions = stage_message(
        read_stage(run / "predictions", "predict"), "predictions.json", SpringPredictionArtifact
    )
    if (
        score.fit_artifact_sha256 != message_sha256(fit)
        or score.preparation_sha256 != message_sha256(preparation)
        or score.prediction_artifact_sha256 != message_sha256(predictions)
        or predictions.model != fit.model or predictions.protocol != preparation.protocol
    ):
        raise ValueError("demo_retained_stage_identity_mismatch")
    if (
        fit.model is None or score.result.status != "scored"
        or fit.observations != observations or len(score.probes) != 24
    ):
        raise ValueError("demo_incomplete_or_mismatched_scientific_outcome")

    # Enumerate native candidates from purchased data; never relabel the fitted model.
    candidate_input = NativeCandidateInput(
        pool=NativeSpringPool(coefficients=tuple((i + 0.5) * 4.0 / cells for i in range(cells))),
        config=NativeCandidateConfig(), observations=observations,
    )
    candidates = produce_native_candidates(candidate_input, attempt_id="demo-candidates")
    actual = NativeEndpointBeliefInput(
        attempt_id="demo-endpoint", candidate_attempt_id="demo-candidates",
        candidate_input=candidate_input, candidate_result=candidates,
        prediction_config=NativePredictionConfig(),
        profile=EndpointBeliefProfile(
            discrepancy=discrepancy,
            cells=tuple(EndpointCell(left=i * 4.0 / cells, right=(i + 1) * 4.0 / cells)
                        for i in range(cells)),
        ),
        prediction_budget=4 * cells,
    )
    belief_dir = output / "belief"
    belief_dir.mkdir(mode=0o700)
    raw_input = (actual.model_dump_json() + "\n").encode()
    _write(belief_dir / "input.json", raw_input)
    cpu, wall = time.process_time_ns(), time.monotonic_ns()
    belief = compute_native_endpoint_belief(raw_input)
    raw_result = (belief.model_dump_json() + "\n").encode()
    _write(belief_dir / "result.json", raw_result)
    bind_native_endpoint_belief_result(raw_result, raw_input)
    passed = _target_met(tuple(p.position_rmse for p in score.probes), score.target_passed)
    _json(output / "summary.json", {
        "claim": "Fixed development walkthrough, not a study or accepted belief calibration.",
        "observation_sha256": message_sha256(observations),
        "engine_fingerprint": observations.engine_version, "purchased_records": 4,
        "fitted_coefficient": fit.model.linear, "fitted_model_sha256": message_sha256(fit.model),
        "scientific_target_met": passed, "maximum_position_rmse": score.maximum_position_rmse,
        "probe_scores": [p.model_dump(mode="json") for p in score.probes],
        "belief_status": belief.status, "belief_reason": belief.reason,
        "belief_profile_sha256": belief.profile_sha256,
        "belief_input_raw_sha256": belief.input_raw_sha256,
        "belief_input_canonical_sha256": belief.input_sha256,
        "belief_cpu_ns": time.process_time_ns() - cpu,
        "belief_wall_ns": time.monotonic_ns() - wall,
        "belief_caveat": (
            "16 midpoint cells on [0,4], discrepancy 0.25: illustrative only. "
            "Normalization does not establish resolution, calibration, MAP or accuracy. "
            "The diagnostic neither selects nor replaces the legacy fitted model."
        ),
    })
    prediction_rows = []
    for probe, result, metric in zip(
        predictions.protocol.probes, predictions.results, score.probes, strict=True
    ):
        if probe.probe_id != metric.probe_id or result.response is None:
            raise ValueError("demo_incomplete_report_prediction")
        endpoint = result.response.trajectory.frames[-1].positions[0]
        prediction_rows.append(
            f"| {probe.probe_id} | {probe.request.experiment.particles[0].mass} | "
            f"{endpoint[0]:.9g}, {endpoint[1]:.9g} | {metric.position_rmse} |"
        )
    lines = [
        "# Bounded scientific walkthrough", "",
        f"Source: {source_commit}.",
        "Stationary noiseless one-particle spring; world seed 7; four seed-0 calibration actions.",
        f"Purchased records: 4. Learned k: {fit.model.linear:.17g}.",
        f"target_passed: {passed}. Worst per-probe RMSE: {score.maximum_position_rmse}.",
        "The fitted model predicts all 24 fixed held-out conditions at masses 0.5, 1 and 2.",
        "Each prediction has 41 times from 0 to 2 seconds; endpoints below are predictions.",
        "Every RMSE uses the independent scorer, with no surviving-probe average.", "",
        "| Probe | Mass | Predicted endpoint (x, y) | Position RMSE |",
        "| --- | ---: | --- | ---: |",
        *prediction_rows, "",
        "## Separate illustrative terminal-x diagnostic", "",
        f"Status: {belief.status}; reason: {belief.reason}.",
        "16 midpoint cells on [0,4]; discrepancy 0.25. No calibrated profile or MAP claim.",
        "These weights do not choose the fitted model above.", "",
    ]
    if belief.normalization is not None and belief.normalization.status == "normalized":
        lines.extend([
            f"Exponential-underflow indices: {belief.normalization.exp_underflow_indices}.",
            "Finite log weights remain retained; underflow is not declared exact-zero mass.", "",
            "| k | Normalized log weight |", "| ---: | ---: |",
        ])
        lines.extend(
            f"| {k} | {entry.log_probability} |"
            for k, entry in zip(candidate_input.pool.coefficients,
                                belief.normalization.entries, strict=True)
        )
    _write(output / "REPORT.md", ("\n".join(lines) + "\n").encode())
    _json(output / ".completion-pending", {
        "files": _inventory(output), "artifact_complete": True,
        "scientific_target_met": passed, "belief_normalized": belief.status == "normalized",
    })
    published = False
    try:
        os.link(output / ".completion-pending", output / "completion.json")
        published = True
        (output / ".completion-pending").unlink()
        directory_fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        if published:
            (output / "completion.json").unlink()
        raise
    print(f"Read {output / 'REPORT.md'}")
    return 0 if passed and belief.status == "normalized" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    # Explicit choices keep software-demo settings from becoming quiet scientific defaults.
    parser.add_argument("--cells", required=True, type=int, choices=(16,))
    parser.add_argument("--discrepancy", required=True, type=float, choices=(0.25,))
    args = parser.parse_args(argv)
    if sys.platform != "linux":
        parser.error("Run this example in the existing cloud Linux environment.")
    os.umask(0o077)
    try:
        output = safe_path(args.output)
        if output.exists() or output.is_relative_to(SOURCE_ROOT):
            raise FileExistsError("demo_output_must_be_new_and_outside_checkout")
        private_stat(output.parent.stat(), directory=True)
        identity = _identity(args.source_commit)
        output.mkdir(mode=0o700)
        _json(output / "runtime.json", identity)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Demo preflight rejected: {type(error).__name__}", file=sys.stderr)
        return 2
    try:
        return _run(output, args.cells, args.discrepancy, args.source_commit)
    except Exception as error:
        # Preserve partial outputs; no retry, resume, replacement probes or survivor averages.
        _json(output / "failure.json", {
            "error_type": type(error).__name__, "message": str(error)[:2048],
        })
        print(f"Demo stopped; retained partial outputs in {output}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
