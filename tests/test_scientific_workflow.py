from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

from strange_physics.cli import main
from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentRecord,
    Impulse,
    ObservationBundle,
    ParticleInitial,
    Structure,
)
from strange_physics.laws import LawSpec
from strange_physics.research_contracts import message_sha256
from strange_physics.scientific_workflow import (
    condition_keys,
    fit_spring,
    i1_protocol,
    predict_spring,
    prepare_spring_evaluation,
    score_spring,
)
from strange_physics.session import LocalSession
from strange_physics.workflow_contracts import (
    SpringFitArtifact,
    SpringPreparationArtifact,
    SpringScoreArtifact,
    StageCompletion,
)
from strange_physics.workflow_io import WorkflowError, read_message, read_stage, write_stage
from strange_physics.workflow_journal import read_journal
from strange_physics.worlds import WorldDefinition, reference_world


def world(*, noise: float = 0.0, coefficient: float = 1.0) -> WorldDefinition:
    base = reference_world("spring", particles=1, budget=4, changed=False, noise=noise)
    return WorldDefinition(
        space=base.space,
        noise_seed=7,
        initial_law=LawSpec(kind="spring", parameters={"linear": coefficient, "cubic": 0.0}),
    )


def purchase(position: tuple[float, float] = (1.0, 0.25)) -> Experiment:
    return Experiment(
        particles=(
            ParticleInitial(id="particle-0", mass=1.0, position=position, velocity=(0.25, -0.5)),
        ),
        impulse=Impulse(particle_id="particle-0", vector=(0.2, 0.1)),
    )


def run(
    tmp_path: Path, *, noise: float = 0.0, failed: bool = False, coefficient: float = 1.0
) -> tuple[Path, ObservationBundle]:
    path = tmp_path / "session.sqlite"
    with LocalSession.create(
        path, "test-run", world(noise=noise, coefficient=coefficient)
    ) as session:
        session.run_experiment(purchase(), operation_id="purchase-0")
        if failed:
            experiment = purchase((-0.5, 0.3))
            session._journal.reserve("purchase-1", experiment, 4)
            session._journal.commit(
                ExperimentRecord(
                    operation_id="purchase-1",
                    index=1,
                    experiment=experiment,
                    status="failed",
                    error="simulation_failed",
                )
            )
        return path, session.export()


def state(path: Path) -> tuple[bytes, int, tuple[tuple[str, bytes, int], ...]]:
    return (
        path.read_bytes(),
        path.stat().st_mode,
        tuple(
            (s.name, s.read_bytes(), s.stat().st_mode)
            for suffix in ("-wal", "-shm", "-journal")
            if (s := Path(str(path) + suffix)).exists()
        ),
    )


def test_sdk_known_spring_and_independent_per_probe_gate(tmp_path: Path) -> None:
    journal, observations = run(tmp_path, failed=True)
    before = state(journal)
    fit = fit_spring(observations)
    assert fit.model is not None and abs(fit.model.linear - 1.0) <= 0.01
    assert fit.fit_input is not None and len(fit.fit_input.observations.records) == 2
    assert fit.model.fit_record_indices == (0,)
    prepared = prepare_spring_evaluation(journal, fit)
    assert prepared.status == "prepared" and prepared.protocol is not None
    prediction = predict_spring(fit.model, prepared.protocol)
    score = score_spring(journal, fit, prepared, prediction)
    assert score.result.status == "scored"
    assert len(score.probes) == 24 and score.target_passed
    assert all(p.position_rmse is not None and p.position_rmse <= 0.001 for p in score.probes)
    assert score.maximum_position_rmse == max(
        p.position_rmse for p in score.probes if p.position_rmse is not None
    )
    assert score.result.reference is not None
    public = fit.model.model_dump_json() + prepared.protocol.model_dump_json()
    assert score.result.reference.source_world_sha256 not in public
    assert state(journal) == before


def test_fixed_manifest_and_all_purchased_condition_exclusion(tmp_path: Path) -> None:
    journal, observations = run(tmp_path)
    fit = fit_spring(observations)
    assert fit.model is not None
    prepared = prepare_spring_evaluation(journal, fit)
    assert prepared.protocol is not None
    probes = prepared.protocol.probes
    assert len(probes) == 24
    assert [p.request.experiment.particles[0].mass for p in probes] == [0.5] * 8 + [1.0] * 8 + [
        2.0
    ] * 8
    assert [p.probe_id for p in probes] == [f"i1-probe-{i:02d}" for i in range(24)]
    assert all(p.request.times == tuple(i * 0.05 for i in range(41)) for p in probes)
    assert all(p.request.integration_dt == 0.01 for p in probes)
    # Explicit hand-picked endpoints check the frozen public policy.
    assert probes[0].request.experiment.particles[0].position == (3.0, 0.0)
    assert probes[7].request.experiment.impulse is None
    assert probes[14].request.experiment.particles[0].position == (1.5, 0.2)
    for probe in probes:
        key, post = condition_keys(probe.request.structure, probe.request.experiment)
        for record in observations.records:
            bought, bought_post = condition_keys(observations.space.structure, record.experiment)
            assert key != bought and post != bought_post


@pytest.mark.parametrize("case", ["none_zero", "reverse_ids", "translation", "post_impulse"])
def test_exact_physical_equivalence_keys(case: str) -> None:
    geometry = Structure(
        particle_ids=("p",),
        anchors=(Anchor(id="a", position=(0.0, 0.0)),),
        connections=(Connection(a="p", b="a"),),
    )
    experiment = Experiment(particles=(ParticleInitial(id="p", position=(1.0, 0.5)),))
    changed_geometry = geometry
    changed = experiment
    if case == "none_zero":
        changed = Experiment(
            particles=experiment.particles, impulse=Impulse(particle_id="p", vector=(0.0, 0.0))
        )
    elif case == "reverse_ids":
        changed_geometry = Structure(
            particle_ids=("other",),
            anchors=(Anchor(id="fixed", position=(0.0, 0.0)),),
            connections=(Connection(a="fixed", b="other"),),
        )
        changed = Experiment(particles=(ParticleInitial(id="other", position=(1.0, 0.5)),))
    elif case == "translation":
        changed_geometry = Structure(
            particle_ids=("p",),
            anchors=(Anchor(id="a", position=(0.25, -0.25)),),
            connections=geometry.connections,
        )
        changed = Experiment(particles=(ParticleInitial(id="p", position=(1.25, 0.25)),))
    else:
        changed = Experiment(
            particles=(ParticleInitial(id="p", position=(1.0, 0.5), velocity=(1.0, -0.5)),),
            impulse=Impulse(particle_id="p", vector=(-1.0, 0.5)),
        )
    a, b = condition_keys(geometry, experiment)
    c, d = condition_keys(changed_geometry, changed)
    assert b == d
    assert (a != c) == (case == "post_impulse")


@pytest.mark.parametrize("failed", [False, True])
def test_actual_purchased_overlap_rejects_without_redraw(tmp_path: Path, failed: bool) -> None:
    path = tmp_path / "session.sqlite"
    with LocalSession.create(path, "overlap", world()) as session:
        session.run_experiment(purchase(), operation_id="first")
        overlap = Experiment(
            particles=(
                ParticleInitial(
                    id="particle-0", mass=1.0, position=(1.5, 0.2), velocity=(0.3, -0.6)
                ),
            ),
            impulse=Impulse(particle_id="particle-0", vector=(0.2, 0.1)),
        )
        if failed:
            session._journal.reserve("overlap", overlap, 4)
            session._journal.commit(
                ExperimentRecord(
                    operation_id="overlap",
                    index=1,
                    experiment=overlap,
                    status="failed",
                    error="simulation_failed",
                )
            )
        else:
            session.run_experiment(overlap, operation_id="overlap")
        fit = fit_spring(session.export())
    prepared = prepare_spring_evaluation(path, fit)
    assert prepared.status == "purchased_overlap" and prepared.protocol is None
    assert (prepared.overlap_probe_index, prepared.overlap_record_index) == (14, 1)


@pytest.mark.parametrize("mode", ["empty", "all_failed", "weak"])
def test_failed_fits_are_retained_and_cannot_prepare(tmp_path: Path, mode: str) -> None:
    path = tmp_path / "session.sqlite"
    with LocalSession.create(path, "failed-fit", world()) as session:
        if mode == "all_failed":
            session._journal.reserve("failed", purchase(), 4)
            session._journal.commit(
                ExperimentRecord(
                    operation_id="failed",
                    index=0,
                    experiment=purchase(),
                    status="failed",
                    error="simulation_failed",
                )
            )
        elif mode == "weak":
            session.run_experiment(
                Experiment(particles=(ParticleInitial(id="particle-0", position=(0.0, 0.0)),)),
                operation_id="zero",
            )
        observations = session.export()
    fit = fit_spring(observations)
    assert fit.model is None
    if mode == "weak":
        assert fit.result is not None and fit.result.status == "insufficient_excitation"
    else:
        assert fit.input_rejection == "no_completed_records" and fit.fit_input is None
    assert prepare_spring_evaluation(path, fit).status == "fit_failed"


def test_above_range_estimate_keeps_all_failed_predictions(tmp_path: Path) -> None:
    journal, observations = run(tmp_path)
    fit = fit_spring(observations)
    # Synthetic mistaken learned coefficient tests failure accounting, not fit accuracy.
    data = fit.model_dump(mode="json")
    data["result"]["model"]["linear"] = 5.0
    data["result"]["diagnostics"]["raw_coefficient"] = 5.0
    data["result"]["diagnostics"]["estimated_coefficient_in_calibrated_range"] = False
    fit = SpringFitArtifact.model_validate_json(json.dumps(data))
    assert fit.model is not None and fit.model.linear > 4
    prepared = prepare_spring_evaluation(journal, fit)
    assert prepared.protocol is not None
    predictions = predict_spring(fit.model, prepared.protocol)
    assert len(predictions.results) == 24
    assert all(r.reason == "coefficient_outside_domain" for r in predictions.results)
    score = score_spring(journal, fit, prepared, predictions)
    assert score.result.status == "unscorable"
    assert len(score.probes) == 24 and score.maximum_position_rmse is None
    assert not score.target_passed and all(p.position_rmse is None for p in score.probes)


def test_noisy_world_retains_evaluator_rejection(tmp_path: Path) -> None:
    journal, observations = run(tmp_path, noise=0.0001)
    fit = fit_spring(observations)
    assert fit.model is not None
    assert fit.result is not None and fit.result.diagnostics.declared_noisy
    prepared = prepare_spring_evaluation(journal, fit)
    assert prepared.protocol is not None
    predictions = predict_spring(fit.model, prepared.protocol)
    score = score_spring(journal, fit, prepared, predictions)
    assert score.result.reason == "unsupported_world"
    assert score.result.report is None and not score.target_passed


@pytest.mark.parametrize(
    "change", ["append", "request", "ordinal", "operation", "world", "fingerprint"]
)
def test_changed_journal_cannot_replace_fitted_prefix(tmp_path: Path, change: str) -> None:
    journal, observations = run(tmp_path)
    fit = fit_spring(observations)
    if change == "append":
        with LocalSession.open(journal) as session:
            session.run_experiment(purchase((0.5, 0.8)), operation_id="later")
    else:
        with sqlite3.connect(journal) as db:
            if change == "request":
                db.execute(
                    "UPDATE experiments SET request_json=?",
                    (purchase((0.5, 0.8)).model_dump_json(),),
                )
            elif change == "ordinal":
                db.execute("UPDATE experiments SET ordinal=1")
            elif change == "operation":
                db.execute("UPDATE experiments SET operation_id='different'")
            elif change == "world":
                d = world().model_dump(mode="json")
                d["space"]["sampling"]["position_noise"] = 0.001
                db.execute("UPDATE run SET world_json=?", (json.dumps(d),))
            else:
                db.execute("UPDATE run SET engine_fingerprint=?", ("f" * 64,))
    before = state(journal)
    with pytest.raises(WorkflowError):
        prepare_spring_evaluation(journal, fit)
    assert state(journal) == before


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_existing_sidecars_are_rejected_without_changes(tmp_path: Path, suffix: str) -> None:
    journal, _ = run(tmp_path)
    sidecar = Path(str(journal) + suffix)
    sidecar.write_bytes(b"private recovery evidence")
    sidecar.chmod(0o600)
    before = state(journal)
    with pytest.raises(WorkflowError, match="journal_nonquiescent"):
        read_journal(journal)
    assert state(journal) == before


@pytest.mark.parametrize(
    "case",
    [
        "pending",
        "wal_header",
        "version",
        "application",
        "corrupt",
        "world_size",
        "row_limit",
        "view",
    ],
)
def test_journal_preflight_is_bounded_and_read_only(tmp_path: Path, case: str) -> None:
    journal, _ = run(tmp_path)
    if case == "pending":
        with sqlite3.connect(journal) as db:
            db.execute(
                "INSERT INTO experiments VALUES ('pending',1,?,NULL)",
                (purchase().model_dump_json(),),
            )
    elif case == "wal_header":
        raw = bytearray(journal.read_bytes())
        raw[18:20] = b"\x02\x02"
        journal.write_bytes(raw)
    elif case == "corrupt":
        journal.write_bytes(b"not a database")
    else:
        with sqlite3.connect(journal) as db:
            if case == "version":
                db.execute("PRAGMA user_version=999")
            elif case == "application":
                db.execute("PRAGMA application_id=0")
            elif case == "world_size":
                db.execute("UPDATE run SET world_json=?", ("x" * (1024 * 1024 + 1),))
            elif case == "row_limit":
                db.executemany(
                    "INSERT INTO experiments VALUES (?,?,?,?)",
                    [(f"x-{i}", i, "{}", "{}") for i in range(1, 10001)],
                )
            else:
                db.execute("CREATE VIEW surprise AS SELECT * FROM run")
    before = state(journal)
    with pytest.raises(WorkflowError):
        read_journal(journal)
    assert state(journal) == before


@pytest.mark.parametrize("case", ["file_symlink", "parent_symlink", "public_mode", "oversize"])
def test_private_input_preflight(tmp_path: Path, case: str) -> None:
    journal, _ = run(tmp_path)
    target = journal
    if case == "file_symlink":
        target = tmp_path / "alias"
        target.symlink_to(journal)
    elif case == "parent_symlink":
        parent = tmp_path / "alias"
        parent.symlink_to(tmp_path, target_is_directory=True)
        target = parent / journal.name
    elif case == "public_mode":
        journal.chmod(0o644)
    else:
        with journal.open("ab") as f:
            f.truncate(128 * 1024 * 1024 + 1)
    with pytest.raises(WorkflowError):
        read_journal(target)


def test_actual_preparation_and_prediction_provenance_join(tmp_path: Path) -> None:
    journal, observations = run(tmp_path)
    fit = fit_spring(observations)
    prepared = prepare_spring_evaluation(journal, fit)
    assert prepared.protocol is not None and fit.model is not None
    predictions = predict_spring(fit.model, prepared.protocol)
    changed = prepared.model_dump() | {"journal_bytes_sha256": "f" * 64}
    with pytest.raises(WorkflowError, match="artifact_mismatch"):
        score_spring(journal, fit, SpringPreparationArtifact.model_validate(changed), predictions)
    model = fit.model.model_copy(update={"linear": 2.0})
    other = predict_spring(model, i1_protocol(model, observations.space.structure))
    with pytest.raises(WorkflowError, match="artifact_mismatch"):
        score_spring(journal, fit, prepared, other)


def test_complete_cli_i1_sequence_and_private_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "run"
    assert (
        main(
            [
                "investigate",
                "--family",
                "spring",
                "--particles",
                "1",
                "--budget",
                "4",
                "--stationary",
                "--noise",
                "0",
                "--seed",
                "7",
                "--directory",
                str(root),
            ]
        )
        == 0
    )
    before = state(root / "session.sqlite")
    assert (
        main(
            [
                "fit-spring",
                "--observations",
                str(root / "observations.json"),
                "--output",
                str(root / "fit"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "prepare-spring-evaluation",
                "--journal",
                str(root / "session.sqlite"),
                "--fit",
                str(root / "fit"),
                "--output",
                str(root / "evaluation"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "predict-spring",
                "--model",
                str(root / "fit/model.json"),
                "--manifest",
                str(root / "evaluation/protocol.json"),
                "--output",
                str(root / "predictions"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "score-spring",
                "--journal",
                str(root / "session.sqlite"),
                "--fit",
                str(root / "fit"),
                "--evaluation",
                str(root / "evaluation"),
                "--predictions",
                str(root / "predictions"),
                "--output",
                str(root / "score"),
            ]
        )
        == 0
    )
    report = read_message(root / "score/score.json", SpringScoreArtifact)
    assert report.target_passed and len(report.probes) == 24
    assert all(p.position_rmse is not None and p.position_rmse <= 0.001 for p in report.probes)
    assert len(read_message(root / "observations.json", ObservationBundle).records) == 4
    assert state(root / "session.sqlite") == before
    for name, stage in (
        ("fit", "fit"),
        ("evaluation", "prepare"),
        ("predictions", "predict"),
        ("score", "score"),
    ):
        directory = root / name
        assert directory.stat().st_mode & 0o777 == 0o700
        for path in directory.iterdir():
            assert path.stat().st_mode & 0o777 == 0o600
        manifest = read_message(directory / "completion.json", StageCompletion)
        assert manifest.stage == stage
        assert {f.name for f in manifest.files} == {p.name for p in directory.iterdir()} - {
            "completion.json"
        }
        for f in manifest.files:
            assert f.bytes_sha256 == hashlib.sha256((directory / f.name).read_bytes()).hexdigest()
    assert "source_world" not in capsys.readouterr().out


def test_failed_cli_input_retains_safe_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    private = tmp_path / "private.json"
    private.write_text('{"secret":"do-not-print-this"}')
    private.chmod(0o600)
    output = tmp_path / "failure"
    assert main(["fit-spring", "--observations", str(private), "--output", str(output)]) == 2
    error = capsys.readouterr().err
    assert "do-not-print-this" not in error and "invalid_input" in error
    assert set(read_stage(output, "fit")) == {"failure.json"}


@pytest.mark.parametrize(
    "case", ["tamper_file", "extra_file", "missing_completion", "wrong_input_hash", "wrong_elapsed"]
)
def test_cli_rejects_incomplete_or_tampered_fit_stage(tmp_path: Path, case: str) -> None:
    journal, observations = run(tmp_path)
    source = tmp_path / "observations.json"
    source.write_text(observations.model_dump_json())
    source.chmod(0o600)
    output = tmp_path / "fit"
    assert main(["fit-spring", "--observations", str(source), "--output", str(output)]) == 0
    if case == "tamper_file":
        (output / "model.json").write_text("{}")
    elif case == "extra_file":
        (output / "extra.json").write_text("{}")
    elif case == "missing_completion":
        (output / "completion.json").unlink()
    else:
        d = json.loads((output / "completion.json").read_text())
        if case == "wrong_elapsed":
            d["elapsed_ms"] += 1
        else:
            d["input_message_sha256"] = ["f" * 64]
        (output / "completion.json").write_text(json.dumps(d))
    before = state(journal)
    assert (
        main(
            [
                "prepare-spring-evaluation",
                "--journal",
                str(journal),
                "--fit",
                str(output),
                "--output",
                str(tmp_path / "prepare"),
            ]
        )
        == 2
    )
    assert state(journal) == before


def test_interrupted_write_has_no_completion_and_existing_outputs_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, observations = run(tmp_path)
    path = tmp_path / "partial"
    real = os.fsync
    count = 0

    def fail_second(fd: int) -> None:
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected flush failure")
        real(fd)

    monkeypatch.setattr(os, "fsync", fail_second)
    with pytest.raises(OSError):
        write_stage(
            path,
            "fit",
            {"first.json": observations, "second.json": observations},
            (message_sha256(observations),),
            1,
        )
    assert not (path / "completion.json").exists()
    retained = (path / "first.json").read_bytes()
    with pytest.raises(FileExistsError):
        write_stage(path, "fit", {"fit.json": observations}, (), 1)
    assert (path / "first.json").read_bytes() == retained


def test_preflight_json_limit_before_reading(tmp_path: Path) -> None:
    source = tmp_path / "huge.json"
    with source.open("wb") as f:
        f.truncate(64 * 1024 * 1024 + 1)
    source.chmod(0o600)
    with pytest.raises(WorkflowError, match="input_limit"):
        read_message(source, ObservationBundle)


def test_fully_scored_scientific_miss_is_retained(tmp_path: Path) -> None:
    journal, observations = run(tmp_path)
    fit = fit_spring(observations)
    # A deliberately wrong but provenance-bound learned model is a valid test of
    # independent scoring. This does not claim the fitter produced this estimate.
    data = fit.model_dump(mode="json")
    data["result"]["model"]["linear"] = 2.0
    data["result"]["diagnostics"]["raw_coefficient"] = 2.0
    fit = SpringFitArtifact.model_validate_json(json.dumps(data))
    prepared = prepare_spring_evaluation(journal, fit)
    assert fit.model is not None and prepared.protocol is not None
    predictions = predict_spring(fit.model, prepared.protocol)
    score = score_spring(journal, fit, prepared, predictions)
    assert score.result.status == "scored" and score.result.report is not None
    assert len(score.probes) == 24
    assert score.maximum_position_rmse is not None and score.maximum_position_rmse > 0.001
    assert not score.target_passed
    assert all(p.position_rmse is not None for p in score.probes)


@pytest.mark.parametrize("kind", ["empty", "all_failed"])
def test_cli_failed_fit_preserves_input_without_model(tmp_path: Path, kind: str) -> None:
    journal = tmp_path / "session.sqlite"
    with LocalSession.create(journal, "failed-cli", world()) as session:
        if kind == "all_failed":
            session._journal.reserve("failed", purchase(), 4)
            session._journal.commit(
                ExperimentRecord(
                    operation_id="failed",
                    index=0,
                    experiment=purchase(),
                    status="failed",
                    error="simulation_failed",
                )
            )
        observations = session.export()
    source = tmp_path / "observations.json"
    source.write_text(observations.model_dump_json())
    source.chmod(0o600)
    destination = tmp_path / "fit"
    assert main(["fit-spring", "--observations", str(source), "--output", str(destination)]) == 1
    retained = read_message(destination / "fit.json", SpringFitArtifact)
    assert retained.observations == observations and retained.model is None
    assert set(read_stage(destination, "fit")) == {"fit.json", "config.json"}
    assert (
        main(
            [
                "prepare-spring-evaluation",
                "--journal",
                str(journal),
                "--fit",
                str(destination),
                "--output",
                str(tmp_path / "prepared"),
            ]
        )
        == 1
    )
    assert not (tmp_path / "prepared/protocol.json").exists()


@pytest.mark.parametrize("fail_call", [1, 2, 3, 4])
def test_no_completion_after_any_flush_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_call: int
) -> None:
    _, observations = run(tmp_path)
    destination = tmp_path / "incomplete"
    real = os.fsync
    calls = 0

    def fail(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == fail_call:
            raise OSError("injected fsync failure")
        real(fd)

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        write_stage(
            destination, "fit", {"first.json": observations, "second.json": observations}, (), 1
        )
    assert not (destination / "completion.json").exists()


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "parent_symlink"])
def test_existing_and_symlink_outputs_are_not_overwritten(tmp_path: Path, kind: str) -> None:
    _, observations = run(tmp_path)
    destination = tmp_path / "output"
    if kind == "file":
        destination.write_bytes(b"retained")
    elif kind == "directory":
        destination.mkdir(mode=0o700)
        (destination / "retained").write_bytes(b"retained")
    elif kind == "symlink":
        destination.symlink_to(tmp_path / "missing")
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(tmp_path, target_is_directory=True)
        destination = alias / "output"
    with pytest.raises((OSError, WorkflowError)):
        write_stage(destination, "fit", {"fit.json": observations}, (), 1)
    if kind == "file":
        assert destination.read_bytes() == b"retained"
    elif kind == "directory":
        assert (destination / "retained").read_bytes() == b"retained"
    else:
        assert not (tmp_path / "missing").exists()


def test_predictor_public_model_mismatch_retains_every_probe(tmp_path: Path) -> None:
    _, observations = run(tmp_path)
    fit = fit_spring(observations)
    assert fit.model is not None
    protocol = i1_protocol(fit.model, observations.space.structure)
    other = fit.model.model_copy(update={"linear": 2.0})
    result = predict_spring(other, protocol)
    assert len(result.results) == 24
    assert all(r.status == "model_mismatch" for r in result.results)
    assert all(s.status == "failed" and s.response is None for s in result.submissions.entries)


def test_fixed_probe_manifest_matches_every_preregistered_condition(tmp_path: Path) -> None:
    import math

    _, observations = run(tmp_path)
    fit = fit_spring(observations)
    assert fit.model is not None
    protocol = i1_protocol(fit.model, observations.space.structure)
    u = 1 / math.sqrt(2)
    expected = (
        ((-0.5, 0.0), (3.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
        ((-0.5, 0.0), (3.0, 0.0), (-2.0, 0.0), (-1.0, 0.0)),
        ((0.0, -0.5), (0.0, 3.0), (0.0, 2.0), (0.0, 1.0)),
        ((0.0, -0.5), (0.0, 3.0), (0.0, -2.0), (0.0, -1.0)),
        ((-0.5 * u, -0.5 * u), (3 * u, 3 * u), (2 * u, -2 * u), (u, -u)),
        ((0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (1.0, 0.0)),
        ((0.0, 0.0), (1.5, 0.2), (0.3, -0.6), (0.2, 0.1)),
        ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), None),
    )
    for index, probe in enumerate(protocol.probes):
        particle = probe.request.experiment.particles[0]
        impulse = probe.request.experiment.impulse
        assert (
            probe.request.structure.anchors[0].position,
            particle.position,
            particle.velocity,
            None if impulse is None else impulse.vector,
        ) == expected[index % 8]
        assert particle.mass == (0.5, 1.0, 2.0)[index // 8]
        assert probe.request.structure.connections == observations.space.structure.connections
