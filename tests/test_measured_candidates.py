"""Real installed candidate execution on synthetic public prefixes, never a study."""

from __future__ import annotations

import copy
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
from test_native_spring_contracts import inputs

import strange_physics
from strange_physics import measured_candidates as executor
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    CandidateRequest,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.installed_identity import BuildFile, TrustedInstallation
from strange_physics.laws import reference_registry
from strange_physics.native_spring_contracts import NativeCandidateInput
from strange_physics.publication_store import digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import engine_fingerprint
from strange_physics.study_contracts import (
    NativeAccountingPlan,
    NativeStudyLedger,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_ledger import (
    StudyLedgerError,
    append_study_attempt,
    read_study_ledger,
    summarize_study,
)

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


def setup(
    root: Path, build: TrustedInstallation, actual: NativeCandidateInput | None = None
) -> CandidateRequest:
    root.mkdir(mode=0o700)
    actual = inputs() if actual is None else actual
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
    ledger = current(root)
    return change(
        request,
        mode="recover",
        ticket=ticket,
        attempt_id=f"recover-{ticket}",
        retry_of=None,
        expected_revision=len(ledger.records),
        expected_head_sha256=head(ledger),
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
    data = inputs().model_dump(mode="json")
    failed = copy.deepcopy(data["observations"]["records"][1])
    failed["index"] = 0
    data["observations"]["records"] = [failed]
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
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
    altered = raw(inputs((0.0, 1.0, 4.0)))
    with pytest.raises(StudyLedgerError, match="candidate_request_conflict"):
        executor.commit_native_candidates(
            root,
            change(
                recovery(root, request),
                input_raw_sha256=digest(altered),
                input_sha256=message_sha256(inputs((0.0, 1.0, 4.0))),
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
