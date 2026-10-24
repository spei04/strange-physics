"""Real installed candidate execution on synthetic public prefixes, never a study."""

from __future__ import annotations

import json
import platform
import sqlite3
import subprocess
import sys
import sysconfig
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from test_study_ledger import materials

import strange_physics
import strange_physics.session as session_module
from strange_physics import measured_candidates as executor
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    CandidateRequest,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.contracts import (
    Anchor,
    Connection,
    Experiment,
    ExperimentSpace,
    ParticleInitial,
    Sampling,
    Structure,
)
from strange_physics.installed_identity import BuildFile, TrustedInstallation
from strange_physics.laws import LawSpec, reference_registry
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeSpringPool,
)
from strange_physics.publication_store import Extents, digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import engine_fingerprint
from strange_physics.session import LocalSession
from strange_physics.simulation import SimulationError
from strange_physics.study_contracts import (
    NativeAccountingPlan,
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorkFacts,
    StudyAttemptReservation,
    StudyAttemptUpdate,
    StudyLedgerRecord,
)
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    freeze_native_study,
    read_study_ledger,
    summarize_study,
)
from strange_physics.worlds import WorldDefinition

ROOT = Path(__file__).resolve().parents[1]


def private(path: Path, value: bytes) -> None:
    path.write_bytes(value)
    path.chmod(0o600)


@pytest.fixture(scope="session")
def actual_build(tmp_path_factory: pytest.TempPathFactory) -> TrustedInstallation:
    """Actual installed bytes and actual checkout; explicitly synthetic provenance."""
    folder = tmp_path_factory.mktemp("candidate-installed-build")
    site = Path(sysconfig.get_paths()["purelib"])
    package = Path(strange_physics.__file__).resolve().parent
    assert package == site / "strange_physics"
    files = []
    wheel = folder / "synthetic-installed.zip"
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.iterdir()):
            if not p.is_file():
                continue
            assert p.read_bytes() == (ROOT / "src/strange_physics" / p.name).read_bytes()
            z.write(p, "strange_physics/" + p.name)
            files.append(
                BuildFile(path=p.name, sha256=digest(p.read_bytes()), bytes=p.stat().st_size)
            )
    wheel.chmod(0o600)
    dependencies = []
    for p in sorted(site.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or package in p.parents:
            continue
        dependencies.append(
            BuildFile(
                path=str(p.relative_to(site)), sha256=digest(p.read_bytes()), bytes=p.stat().st_size
            )
        )
    lock = folder / "uv.lock"
    private(lock, (ROOT / "uv.lock").read_bytes())
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    provenance = folder / "provenance.json"
    private(
        provenance,
        json.dumps(
            {
                "source_commit": commit,
                "uv_lock_sha256": digest(lock.read_bytes()),
                "archive_sha256": digest(wheel.read_bytes()),
                "evidence_kind": "synthetic_installed_snapshot",
            }
        ).encode(),
    )
    return TrustedInstallation(
        evidence_kind="synthetic_installed_snapshot",
        source_commit=commit,
        uv_lock_sha256=digest(lock.read_bytes()),
        lock_path=str(lock),
        archive_path=str(wheel),
        archive_sha256=digest(wheel.read_bytes()),
        provenance_path=str(provenance),
        provenance_sha256=digest(provenance.read_bytes()),
        python_version=platform.python_version(),
        python_executable_sha256=digest(Path(sys.executable).resolve().read_bytes()),
        engine_fingerprint=engine_fingerprint(reference_registry()),
        package_files=tuple(files),
        dependency_files=tuple(dependencies),
    )


def actual_input(path: Path, *, completed: bool = True) -> NativeCandidateInput:
    """Real session capture plus explicit fault injection; never relabel historical data."""
    space = ExperimentSpace(
        structure=Structure(
            particle_ids=("p",),
            anchors=(Anchor(id="a", position=(0.0, 0.0)),),
            connections=(Connection(a="p", b="a"),),
        ),
        sampling=Sampling(duration=0.1, dt=0.01, sample_interval=0.05),
        budget=2,
        calibration_experiments=0,
    )
    world = WorldDefinition(
        space=space, noise_seed=31, initial_law=LawSpec(kind="spring", parameters={"linear": 1.0})
    )
    experiment = Experiment(particles=(ParticleInitial(id="p", position=(1.0, 0.0)),))

    def injected(*args: object, **kwargs: object) -> None:
        raise SimulationError("explicit synthetic preparation fault")

    with LocalSession.create(path, "candidate-fixture", world) as session:
        if completed:
            assert session.run_experiment(experiment, operation_id="complete").status == "completed"
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(session_module, "simulate", injected)
            assert session.run_experiment(experiment, operation_id="failure").status == "failed"
        observations = session.export()
    return NativeCandidateInput(
        pool=NativeSpringPool(coefficients=(-0.0, 1.0, 4.0)),
        config=NativeCandidateConfig(),
        observations=observations,
    )


def setup(
    root: Path, build: TrustedInstallation, actual: NativeCandidateInput | None = None
) -> CandidateRequest:
    root.mkdir(mode=0o700)
    actual = actual_input(root / "fixture-observations.sqlite") if actual is None else actual
    data = raw(actual)
    private(root / "input.json", data)
    plan = NativeAccountingPlan(
        study_id="candidate-test",
        purpose="synthetic_validation",
        approval_id="NATIVE_COMPARISON_APPROVAL_2026_10_21",
    )
    ledger = NativeStudyLedger(plan=plan, records=())
    c = CandidateControl(
        root=str(root),
        plan_sha256=message_sha256(plan),
        source_commit=build.source_commit,
        uv_lock_sha256=build.uv_lock_sha256,
        engine_fingerprint=build.engine_fingerprint,
        installation_sha256=message_sha256(build),
        attempt_id="control",
        tickets=6,
        recovery_tickets=2,
        recovery_work_cpu_ns=8_000_000_000,
        recovery_work_artifact_bytes=2 * MIB,
        ticket_cpu_ns=5_000_000_000,
        ticket_wall_ns=30_000_000_000,
        ticket_artifact_bytes=8192,
        bootstrap_artifact_bytes=4 * MIB,
        bootstrap_cpu_ns=5_000_000_000,
        database_limit_bytes=2 * MIB,
        finalization_records=6,
        finalization_bytes=32 * 1024,
        publication=PublicationEscrow(
            calls=0,
            material_bytes=0,
            journal_bytes=0,
            ledger_bytes=8 * MIB,
            output_bytes=64 * 1024,
            control_cpu_ns=0,
            control_artifact_bytes=0,
            work_cpu_ns=0,
        ),
    )
    hold = StudyAttemptReservation(
        attempt_id=c.attempt_id,
        phase="accounting",
        cell_id=None,
        operation="accounting",
        config_sha256=message_sha256(c),
        input_sha256=c.plan_sha256,
        retry_of=None,
        cpu_reservation_ns=c.tickets * c.ticket_cpu_ns + c.bootstrap_cpu_ns,
        artifact_reservation_bytes=c.required_control_bytes(),
        purchase=None,
    )
    ledger = append_study_attempt(
        ledger, event_id="control-reserve", event=hold, expected_revision=0
    )
    private(root / "candidate-installation.json", raw(build))
    private(root / "candidate-seed.json", raw(ledger))
    private(
        root / "candidate-admission.json",
        raw(CandidateAdmission(control=c, seed_ledger_sha256=digest(raw(ledger)))),
    )
    return CandidateRequest(
        mode="execute",
        logical_id="candidates",
        attempt_id="candidate-0",
        retry_of=None,
        phase="reference",
        cell_id=None,
        ticket=0,
        expected_revision=len(ledger.records),
        expected_head_sha256=head(ledger),
        input_path=str(root / "input.json"),
        input_raw_sha256=digest(data),
        input_bytes=len(data),
        input_sha256=message_sha256(actual),
        config_sha256=message_sha256(actual.config),
        cpu_reservation_ns=8_000_000_000,
        artifact_reservation_bytes=2 * MIB,
        output_limit_bytes=MIB,
        wall_limit_ns=30_000_000_000,
    )


def current(root: Path) -> NativeStudyLedger:
    with sqlite3.connect(root / "candidate.sqlite3") as db:
        return read_study_ledger(db.execute("SELECT ledger FROM state WHERE id=1").fetchone()[0])


def last_update(ledger: NativeStudyLedger) -> StudyAttemptUpdate:
    value = ledger.records[-1].event
    assert isinstance(value, StudyAttemptUpdate)
    return value


def change(request: CandidateRequest, **values: Any) -> CandidateRequest:
    return CandidateRequest.model_validate(request.model_dump() | values)


def recovery(root: Path, request: CandidateRequest, ticket: int = 4) -> CandidateRequest:
    """Retain the caller's original head; no free state lookup is required."""
    return change(
        request,
        mode="recover",
        ticket=ticket,
        attempt_id=f"recover-{ticket}",
        retry_of=None,
    )


def test_actual_candidate_and_exact_paid_replay(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    first = executor.commit_native_candidates(root, request)
    assert first.result.payload.status == "produced"
    assert first.result.payload.completed_record_indices == (0,)
    assert first.result.payload.failed_record_count == 1
    assert first.measurements.child_cpu_ns >= 0 and first.measurements.wall_ns > 0
    assert first.measurements.created_artifact_bytes == request.input_bytes + len(first.result_raw)
    assert first.result.facts.attempt_id == request.attempt_id
    (root / "input.json").unlink()

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("recovery must never rerun candidates")

    monkeypatch.setattr(executor, "produce_native_candidates", forbidden)
    second = executor.commit_native_candidates(root, recovery(root, request))
    assert second.replayed and second.receipt == first.receipt
    assert second.result_raw == first.result_raw and second.original_ledger == first.original_ledger
    assert second.measurements.child_cpu_ns == 0
    assert len(second.ledger.records) == len(first.ledger.records) + 2
    assert last_update(second.ledger).facts is not None
    assert last_update(second.ledger).state == "completed"


def test_real_no_completed_rejection(tmp_path: Path, actual_build: TrustedInstallation) -> None:
    actual = actual_input(tmp_path / "failed-observations.sqlite", completed=False)
    request = setup(tmp_path / "run", actual_build, actual)
    result = executor.commit_native_candidates(tmp_path / "run", request)
    assert result.result.payload.reason == "no_completed_records"
    assert last_update(result.ledger).state == "rejected"


def test_missing_material_retains_unknown_and_fresh_retry(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    data = (root / "input.json").read_bytes()
    (root / "input.json").unlink()
    with pytest.raises(FileNotFoundError):
        executor.commit_native_candidates(root, request)
    ledger = current(root)
    update = last_update(ledger)
    assert update.state == "unknown" and update.cpu_ns is not None
    assert summarize_study(ledger).budget.unresolved_attempts == 2
    private(root / "input.json", data)
    retry = change(
        request,
        ticket=1,
        attempt_id="candidate-1",
        retry_of=request.attempt_id,
        expected_revision=len(ledger.records),
        expected_head_sha256=head(ledger),
    )
    result = executor.commit_native_candidates(root, retry)
    assert result.result.payload.status == "produced"
    assert summarize_study(result.ledger).budget.unresolved_attempts == 2


@pytest.mark.parametrize("field,value", [("input_sha256", "f" * 64), ("config_sha256", "e" * 64)])
def test_input_join_denial_retains_hold(
    tmp_path: Path, actual_build: TrustedInstallation, field: str, value: str
) -> None:
    root = tmp_path / "run"
    request = change(setup(root, actual_build), **{field: value})
    with pytest.raises(StudyLedgerError, match="candidate_input_identity"):
        executor.commit_native_candidates(root, request)
    assert summarize_study(current(root)).budget.unresolved_attempts == 2


def test_replay_changed_raw_signed_zero_conflicts(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    executor.commit_native_candidates(root, request)
    payload = json.loads((root / "input.json").read_bytes())
    payload["pool"]["coefficients"] = [0.0, 1.0, 4.0]
    altered = raw(NativeCandidateInput.model_validate_json(json.dumps(payload)))
    with pytest.raises(StudyLedgerError, match="candidate_request_conflict"):
        executor.commit_native_candidates(
            root,
            change(
                recovery(root, request),
                input_raw_sha256=digest(altered),
                input_sha256=message_sha256(NativeCandidateInput.model_validate_json(altered)),
                input_bytes=len(altered),
            ),
        )


def test_real_child_setup_failure_is_unknown(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)

    def fail(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt("synthetic child setup interruption")

    monkeypatch.setattr(executor, "produce_native_candidates", fail)
    with pytest.raises(StudyLedgerError, match="candidate_child_failed"):
        executor.commit_native_candidates(root, request)
    update = last_update(current(root))
    assert update.state == "unknown" and update.facts is None
    assert update.cpu_ns is not None


def test_lost_ack_preserves_atomic_original_result(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    original = CandidateStore.transaction
    count = 0

    @contextmanager
    def lost(self: CandidateStore) -> Iterator[None]:
        nonlocal count
        with original(self):
            yield
        count += 1
        if count == 3:
            raise OSError("synthetic lost acknowledgment")

    with monkeypatch.context() as m:
        m.setattr(CandidateStore, "transaction", lost)
        with pytest.raises(OSError, match="lost acknowledgment"):
            executor.commit_native_candidates(root, request)
    before = current(root)
    assert last_update(before).state == "completed"
    result = executor.commit_native_candidates(root, recovery(root, request))
    assert result.replayed and result.receipt.original_attempt_id == request.attempt_id


def test_store_loss_cannot_reseed(tmp_path: Path, actual_build: TrustedInstallation) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    executor.commit_native_candidates(root, request)
    recover = recovery(root, request)
    for name in ("candidate.sqlite3", "candidate.sqlite3-journal"):
        (root / name).unlink()
    with pytest.raises(StudyLedgerError, match="candidate_store_missing_or_partial"):
        executor.commit_native_candidates(root, recover)


def test_stale_head_and_ticket_reuse(tmp_path: Path, actual_build: TrustedInstallation) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    with pytest.raises(StudyLedgerError, match="candidate_stale_head"):
        executor.commit_native_candidates(root, change(request, expected_head_sha256="a" * 64))
    assert len(current(root).records) == 1
    with pytest.raises(StudyLedgerError, match="candidate_ticket_consumed"):
        executor.commit_native_candidates(root, request)


def test_private_installation_origin_denied(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    monkeypatch.setattr(strange_physics, "__file__", "/tmp/foreign/strange_physics/__init__.py")
    with pytest.raises(StudyLedgerError, match="installed_identity_origin"):
        executor.commit_native_candidates(root, request)
    assert (root / "candidate-ticket-0").exists()
    assert not (root / "candidate.sqlite3").exists()


def test_work_capacity_stop_is_durable(tmp_path: Path, actual_build: TrustedInstallation) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    with pytest.raises(StudyLedgerError, match="candidate_work_headroom"):
        executor.commit_native_candidates(
            root, change(request, artifact_reservation_bytes=256 * 1024)
        )
    with pytest.raises(StudyLedgerError, match="candidate_stopped"):
        executor.commit_native_candidates(root, change(request, ticket=1, attempt_id="next"))
    assert len(current(root).records) == 1


def test_unknown_attempt_cannot_reexecute_under_old_hold(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    data = (root / "input.json").read_bytes()
    (root / "input.json").unlink()
    with pytest.raises(FileNotFoundError):
        executor.commit_native_candidates(root, request)
    before = current(root)
    private(root / "input.json", data)
    duplicate = change(
        request, ticket=1, expected_revision=len(before.records), expected_head_sha256=head(before)
    )
    with pytest.raises(StudyLedgerError, match="candidate_attempt_reused"):
        executor.commit_native_candidates(root, duplicate)
    assert current(root) == before
    assert not (root / "candidate-output-1").exists()


def test_recovery_attempt_must_be_fresh(tmp_path: Path, actual_build: TrustedInstallation) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    executor.commit_native_candidates(root, request)
    paid = recovery(root, request)
    executor.commit_native_candidates(root, paid)
    before = current(root)
    with pytest.raises(StudyLedgerError, match="candidate_attempt_reused"):
        executor.commit_native_candidates(
            root, change(recovery(root, request, 5), attempt_id=paid.attempt_id)
        )
    assert current(root) == before


def test_close_failure_preserves_original_failure(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    (root / "input.json").unlink()
    original = CandidateStore.close

    def broken(self: CandidateStore) -> None:
        original(self)
        raise OSError("synthetic close failure")

    monkeypatch.setattr(CandidateStore, "close", broken)
    with pytest.raises(FileNotFoundError) as caught:
        executor.commit_native_candidates(root, request)
    assert any("Final store close" in n for n in caught.value.__notes__)
    assert last_update(current(root)).state == "unknown"


def test_reaped_malformed_output_retains_known_cost(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)

    def malformed(value: bytes) -> None:
        raise StudyLedgerError("synthetic output parse failure")

    monkeypatch.setattr(executor, "parse_native_candidate_result", malformed)
    with pytest.raises(StudyLedgerError, match="synthetic output parse failure"):
        executor.commit_native_candidates(root, request)
    update = last_update(current(root))
    assert update.state == "unknown" and update.facts is None
    assert update.cpu_ns is not None and update.wall_ns is not None
    assert (
        update.artifact_bytes == request.input_bytes + (root / "candidate-output-0").stat().st_size
    )
    assert summarize_study(current(root)).budget.unresolved_attempts == 2


def test_unicode_request_byte_limit_precedes_ticket(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = change(setup(root, actual_build), input_path="/" + "𐀀" * 4095)
    with pytest.raises(ValueError, match="invalid_request"):
        executor.commit_native_candidates(root, request)
    assert not (root / "candidate-ticket-0").exists()


@pytest.mark.parametrize("path", ["input.json", "candidate-installation.json"])
def test_private_symlink_materials_rejected(
    tmp_path: Path, actual_build: TrustedInstallation, path: str
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    material = root / path
    target = root / (path + ".target")
    material.rename(target)
    material.symlink_to(target)
    with pytest.raises(ValueError, match="unsafe_path"):
        executor.commit_native_candidates(root, request)
    assert not (root / "candidate-output-0").exists()
    if path == "input.json":
        assert last_update(current(root)).state == "unknown"


def synthetic_history(
    seed: NativeStudyLedger, pairs: int, *, running: bool = False
) -> NativeStudyLedger:
    """O(n) real legal history, validated by the public complete-prefix reader."""
    records = list(seed.records)
    previous = head(seed)
    for index in range(pairs):
        identity = f"history-{index}"
        reservation = StudyAttemptReservation(
            attempt_id=identity,
            phase="reference",
            cell_id=None,
            operation="reference",
            config_sha256="a" * 64,
            input_sha256="b" * 64,
            retry_of=None,
            cpu_reservation_ns=1,
            artifact_reservation_bytes=0,
            purchase=None,
        )
        facts = NativeWorkFacts(
            attempt_id=identity,
            operation="reference",
            producer_version="x",
            config_sha256=reservation.config_sha256,
            input_sha256=reservation.input_sha256,
            observation_sha256=None,
            model_sha256=None,
            output_sha256="c" * 64,
            unit="work",
            requested_count=1,
            completed_count=1,
            failed_count=0,
            not_assessed_count=0,
            outcome="completed",
        )
        events: list[StudyAttemptReservation | StudyAttemptUpdate] = [reservation]
        if running and index == 0:
            events.append(
                StudyAttemptUpdate(
                    attempt_id=identity,
                    state="running",
                    cpu_ns=0,
                    wall_ns=0,
                    artifact_bytes=0,
                    facts=None,
                )
            )
        events.append(
            StudyAttemptUpdate(
                attempt_id=identity,
                state="completed",
                cpu_ns=1,
                wall_ns=1,
                artifact_bytes=0,
                facts=facts,
            )
        )
        for event in events:
            record = StudyLedgerRecord(
                event_id=f"history-event-{len(records)}",
                sequence=len(records),
                previous_sha256=previous,
                event=event,
            )
            records.append(record)
            previous = message_sha256(record)
    return read_study_ledger(raw(NativeStudyLedger(plan=seed.plan, records=tuple(records))))


def pad_history(ledger: NativeStudyLedger, target: int) -> NativeStudyLedger:
    """Tune permitted producer-version encoding, retaining real hash-chain semantics."""
    needed = target - len(raw(ledger))
    assert needed >= 0
    records = []
    previous = message_sha256(ledger.plan)
    for record in ledger.records:
        event = record.event
        if isinstance(event, StudyAttemptUpdate) and event.facts is not None and needed:
            extra = min(needed, 1400)
            encoded = extra + 1
            astral, ascii_count = divmod(encoded, 12)
            version = "𐀀" * astral + "x" * ascii_count
            assert 1 <= len(version) <= 128
            value = event.model_dump(mode="json")
            value["facts"]["producer_version"] = version
            event = StudyAttemptUpdate.model_validate_json(json.dumps(value))
            needed -= extra
        replacement = StudyLedgerRecord(
            event_id=record.event_id,
            sequence=record.sequence,
            previous_sha256=previous,
            event=event,
        )
        records.append(replacement)
        previous = message_sha256(replacement)
    assert needed == 0
    result = read_study_ledger(raw(NativeStudyLedger(plan=ledger.plan, records=tuple(records))))
    assert len(raw(result)) == target
    return result


def test_real_ledger_record_finalization_boundary(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    setup(root, actual_build)
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    control = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    ).control
    equal = synthetic_history(seed, 4092)
    assert len(equal.records) == 8185
    executor._capacity(root, equal, control)
    over = synthetic_history(seed, 4092, running=True)
    assert len(over.records) == 8186
    with pytest.raises(StudyLedgerError, match="candidate_finalization_headroom"):
        executor._capacity(root, over, control)


def test_real_ledger_byte_finalization_boundary(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    setup(root, actual_build)
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    control = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    ).control
    base = synthetic_history(seed, 3300)
    target = 8 * MIB - 4096 - control.finalization_bytes
    equal = pad_history(base, target)
    executor._capacity(root, equal, control)
    over = pad_history(base, target + 1)
    with pytest.raises(StudyLedgerError, match="candidate_finalization_headroom"):
        executor._capacity(root, over, control)


def test_foreign_historical_engine_is_not_relabelled(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    data = actual_input(tmp_path / "foreign-observations.sqlite").model_dump(mode="json")
    data["observations"]["engine_fingerprint"] = "f" * 64
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    root = tmp_path / "run"
    request = setup(root, actual_build, actual)
    with pytest.raises(StudyLedgerError, match="candidate_observation_engine"):
        executor.commit_native_candidates(root, request)
    update = last_update(current(root))
    assert update.state == "unknown" and update.facts is None
    assert actual.observations.engine_fingerprint == "f" * 64
    assert not (root / "candidate-output-0").exists()


def test_global_budget_denial_persists_stop(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    remaining = summarize_study(seed).budget.remaining_cpu_ns
    charge = StudyAttemptReservation(
        attempt_id="other-work",
        phase="reference",
        cell_id=None,
        operation="reference",
        config_sha256="a" * 64,
        input_sha256="b" * 64,
        retry_of=None,
        cpu_reservation_ns=remaining,
        artifact_reservation_bytes=0,
        purchase=None,
    )
    seed = append_study_attempt(
        seed, event_id="other-reserve", event=charge, expected_revision=len(seed.records)
    )
    admission = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    )
    private(root / "candidate-seed.json", raw(seed))
    private(
        root / "candidate-admission.json",
        raw(CandidateAdmission(control=admission.control, seed_ledger_sha256=digest(raw(seed)))),
    )
    request = change(request, expected_revision=len(seed.records), expected_head_sha256=head(seed))
    with pytest.raises(StudyLedgerError, match="budget_exhausted"):
        executor.commit_native_candidates(root, request)
    with sqlite3.connect(root / "candidate.sqlite3") as db:
        assert db.execute("SELECT stopped FROM state").fetchone()[0] == 1
    assert current(root) == seed


@pytest.mark.parametrize("field", ["input_raw_sha256", "original_prefix"])
def test_receipt_corruption_cannot_rebind_original_snapshot(
    tmp_path: Path, actual_build: TrustedInstallation, field: str
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    first = executor.commit_native_candidates(root, request)
    with sqlite3.connect(root / "candidate.sqlite3") as db:
        value = json.loads(db.execute("SELECT receipt FROM closures").fetchone()[0])
        if field == "input_raw_sha256":
            value[field] = "f" * 64
        else:
            value.update(
                original_revision=len(first.ledger.records),
                original_head_sha256=head(first.ledger),
                original_ledger_sha256=digest(raw(first.ledger)),
            )
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        db.execute("UPDATE closures SET receipt=?,receipt_digest=?", (encoded, digest(encoded)))
    with pytest.raises(StudyLedgerError, match="candidate_closure_corrupt"):
        executor.commit_native_candidates(root, recovery(root, request))
    assert current(root) == first.ledger


def test_child_output_substitution_cannot_detach_raw_result(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    original = executor._run_child

    def substituted(
        request: CandidateRequest, source: bytes, path: Path
    ) -> tuple[bytes | None, int]:
        result, cpu = original(request, source, path)
        assert result is not None
        private(path, b"{}")
        return result, cpu

    monkeypatch.setattr(executor, "_run_child", substituted)
    with pytest.raises(StudyLedgerError, match="candidate_output_changed"):
        executor.commit_native_candidates(root, request)
    update = last_update(current(root))
    assert update.state == "unknown" and update.cpu_ns is not None
    with sqlite3.connect(root / "candidate.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0


@pytest.mark.parametrize("phase", [2, 3])
def test_sqlite_transaction_failure_retains_correct_prefix(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch, phase: int
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    original = CandidateStore.transaction
    count = 0

    @contextmanager
    def fault(self: CandidateStore) -> Iterator[None]:
        nonlocal count
        count += 1
        current_phase = count
        with original(self):
            yield
            if current_phase == phase:
                raise sqlite3.OperationalError("synthetic database or disk is full")

    with monkeypatch.context() as patch:
        patch.setattr(CandidateStore, "transaction", fault)
        with pytest.raises(sqlite3.OperationalError, match="synthetic database"):
            executor.commit_native_candidates(root, request)
    ledger = current(root)
    assert len(ledger.records) == (1 if phase == 2 else 3)
    assert summarize_study(ledger).budget.unresolved_attempts == (1 if phase == 2 else 2)
    with sqlite3.connect(root / "candidate.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM closures").fetchone()[0] == 0
    retry = change(
        request,
        ticket=1,
        attempt_id="candidate-retry",
        retry_of=None if phase == 2 else request.attempt_id,
        expected_revision=len(ledger.records),
        expected_head_sha256=head(ledger),
    )
    result = executor.commit_native_candidates(root, retry)
    assert result.result.payload.status == "produced"
    assert summarize_study(result.ledger).budget.unresolved_attempts == (1 if phase == 2 else 2)


def test_recovery_work_ceiling_precedes_ticket(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    with pytest.raises(StudyLedgerError, match="candidate_recovery_work_limit"):
        executor.commit_native_candidates(
            root, change(recovery(root, request), cpu_reservation_ns=8_000_000_001)
        )
    assert not (root / "candidate-ticket-4").exists()


@pytest.mark.parametrize("field", ["cpu_reservation_ns", "artifact_reservation_bytes"])
def test_remaining_recovery_work_escrow_is_preserved(
    tmp_path: Path, actual_build: TrustedInstallation, field: str
) -> None:
    root = tmp_path / "run"
    setup(root, actual_build)
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    control = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    ).control
    budget = summarize_study(seed).budget
    remaining = (
        budget.remaining_cpu_ns
        if field == "cpu_reservation_ns"
        else budget.remaining_artifact_bytes
    )
    escrow = control.recovery_tickets * (
        control.recovery_work_cpu_ns
        if field == "cpu_reservation_ns"
        else control.recovery_work_artifact_bytes
    )
    payload: dict[str, Any] = dict(
        attempt_id="boundary",
        phase="reference",
        cell_id=None,
        operation="reference",
        config_sha256="a" * 64,
        input_sha256="b" * 64,
        retry_of=None,
        cpu_reservation_ns=1,
        artifact_reservation_bytes=0,
        purchase=None,
    )
    payload[field] = remaining - escrow
    reservation = StudyAttemptReservation.model_validate(payload)
    equal = append_study_attempt(
        seed, event_id="boundary-event", event=reservation, expected_revision=len(seed.records)
    )
    executor._capacity(root, equal, control)
    payload[field] += 1
    over = append_study_attempt(
        seed,
        event_id="boundary-event",
        event=StudyAttemptReservation.model_validate(payload),
        expected_revision=len(seed.records),
    )
    with pytest.raises(StudyLedgerError, match="candidate_protected_work_headroom"):
        executor._capacity(root, over, control)


@pytest.mark.parametrize("matching_source", [True, False])
def test_frozen_comparison_requires_identity_and_unimplemented_journal_adapter(
    tmp_path: Path, actual_build: TrustedInstallation, matching_source: bool
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    manifest, payloads = materials()
    value = manifest.model_dump(mode="json")
    value.update(
        study_id=seed.plan.study_id,
        source_commit=actual_build.source_commit if matching_source else "f" * 40,
        uv_lock_sha256=actual_build.uv_lock_sha256,
        engine_fingerprint=actual_build.engine_fingerprint,
    )
    actual = NativeCandidateInput.model_validate_json((root / "input.json").read_bytes())
    payloads["candidate_config"] = raw(actual.config)
    for entry in value["artifacts"]:
        if entry["kind"] == "candidate_config":
            entry["sha256"] = digest(payloads["candidate_config"])
            entry["byte_count"] = len(payloads["candidate_config"])
    manifest = NativeStudyManifest.model_validate_json(json.dumps(value))
    seed = freeze_native_study(
        seed,
        event_id="synthetic-freeze",
        manifest=manifest,
        expected_revision=len(seed.records),
        expected_purpose="synthetic_validation",
        source_commit=manifest.source_commit,
        uv_lock_bytes=Path(actual_build.lock_path).read_bytes(),
        engine_fingerprint=manifest.engine_fingerprint,
        artifacts=payloads,
    )
    admission = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    )
    private(root / "candidate-seed.json", raw(seed))
    private(
        root / "candidate-admission.json",
        raw(CandidateAdmission(control=admission.control, seed_ledger_sha256=digest(raw(seed)))),
    )
    request = change(
        request,
        phase="comparison",
        cell_id=manifest.cells[0].cell_id,
        expected_revision=len(seed.records),
        expected_head_sha256=head(seed),
    )
    reason = (
        "candidate_comparison_not_available" if matching_source else "candidate_frozen_identity"
    )
    with pytest.raises(StudyLedgerError, match=reason):
        executor.commit_native_candidates(root, request)
    assert current(root) == seed
    assert not (root / "candidate-output-0").exists()


@pytest.mark.parametrize("reopened", [False, True])
def test_transaction_allowance_covers_rollback_regrowth_and_bounds_retries(
    tmp_path: Path, actual_build: TrustedInstallation, reopened: bool
) -> None:
    root = tmp_path / "run"
    setup(root, actual_build)
    admission = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    )
    seed = (root / "candidate-seed.json").read_bytes()
    if reopened:
        initial = CandidateStore(
            root, admission, seed, Extents(root, database_name="candidate.sqlite3")
        )
        initial.close()
        # Retained sidecar loss between invocations cannot reuse a lifetime hold.
        (root / "candidate.sqlite3-journal").unlink(missing_ok=True)
    store = CandidateStore(root, admission, seed, Extents(root, database_name="candidate.sqlite3"))
    grown = []
    try:
        for _ in range(3):
            store.limit_control_growth()
            before = store.path.stat().st_size
            with pytest.raises(RuntimeError, match="rollback probe"):
                with store.transaction():
                    store.db.execute("CREATE TABLE rollback_probe(payload BLOB)")
                    store.db.execute("INSERT INTO rollback_probe VALUES(zeroblob(131072))")
                    # Allocate dirty pages without sampling. This tests the finite
                    # rollback-attempt bound, not a physical-growth reproduction.
                    grown.append(
                        store.db.execute("PRAGMA page_count").fetchone()[0] * 4096 - before
                    )
                    raise RuntimeError("rollback probe")
            assert store.ledger() == read_study_ledger(seed)
        with pytest.raises(StudyLedgerError, match="candidate_transaction_limit"):
            with store.transaction():
                pytest.fail("fifth startup/write attempt must not begin")
        assert len(grown) == 3 and all(value > 0 for value in grown)
        assert store.path.stat().st_size <= admission.control.database_limit_bytes
    finally:
        store.close()


def test_control_hold_prepays_each_bounded_store_attempt(
    tmp_path: Path, actual_build: TrustedInstallation
) -> None:
    root = tmp_path / "run"
    request = setup(root, actual_build)
    admission = CandidateAdmission.model_validate_json(
        (root / "candidate-admission.json").read_bytes()
    )
    control = admission.control
    expected = control.bootstrap_artifact_bytes + control.tickets * (
        control.ticket_artifact_bytes + 4 * control.database_envelope()
    )
    assert control.required_control_bytes() == expected < 1024 * MIB
    with pytest.raises(ValueError, match="protected future artifacts"):
        CandidateControl.model_validate(control.model_dump() | {"tickets": 3072})
    seed = read_study_ledger((root / "candidate-seed.json").read_bytes())
    hold = seed.records[0].event
    assert isinstance(hold, StudyAttemptReservation)
    insufficient = StudyAttemptReservation.model_validate(
        hold.model_dump()
        | {
            "artifact_reservation_bytes": expected - 1,
        }
    )
    seed = append_study_attempt(
        NativeStudyLedger(plan=seed.plan, records=()),
        event_id="control-reserve",
        event=insufficient,
        expected_revision=0,
    )
    private(root / "candidate-seed.json", raw(seed))
    private(
        root / "candidate-admission.json",
        raw(CandidateAdmission(control=control, seed_ledger_sha256=digest(raw(seed)))),
    )
    request = change(request, expected_head_sha256=head(seed))
    with pytest.raises(StudyLedgerError, match="candidate_control_hold"):
        executor.commit_native_candidates(root, request)
    assert not (root / "candidate.sqlite3").exists()
