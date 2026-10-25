"""Finite test-only construction; never a public purchase or import API."""

from __future__ import annotations

import json
import math
import os
import resource
import signal
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

from test_study_ledger import materials

import strange_physics.session as session_module
from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.contracts import Experiment, ParticleInitial
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.native_classical_contracts import (
    ClassicalDiagnosticConfig,
    ClassicalDiagnosticInput,
)
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_scoring_contracts import NativeEvaluationInput, NativeScoringPolicy
from strange_physics.native_spring_contracts import (
    NativeCandidateConfig,
    NativeCandidateInput,
    NativeCandidateResult,
    NativeSpringPool,
)
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.publication_store import Extents, digest, head, raw, root_lock
from strange_physics.research_contracts import message_sha256
from strange_physics.session import LocalSession
from strange_physics.simulation import SimulationError
from strange_physics.study_contracts import (
    NativeAccountingPlan,
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorldCatalog,
    StudyAttemptReservation,
    StudyPurchase,
)
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalInput,
    NativeComparisonClassicalRequest,
    NativeComparisonInput,
    NativeFreezeInput,
    NativeFreezeRequest,
)
from strange_physics.study_journal import read_study_journal
from strange_physics.study_ledger import append_study_attempt, study_manifest

JOURNAL_LIMIT = 128 * 1024
FILE_LIMIT = 262400
EPOCH_LIMIT = 36
COPY_LIMIT = 4 * MIB
STORE_ENVELOPE = 4329472


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def restrict_limit(which: int, ceiling: int) -> None:
    soft, hard = resource.getrlimit(which)
    bound = min([ceiling, *(v for v in (soft, hard) if v != resource.RLIM_INFINITY)])
    resource.setrlimit(which, (bound, bound))


@dataclass
class SetupBudget:
    """Retained unknown hold; bounded actual setup phases, never settled to zero."""

    deadline: int
    parent_cpu: int = 0
    child_cpu: int = 0
    copies: int = 0
    child_epochs: int = 0

    @contextmanager
    def phase(self) -> Iterator[None]:
        assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
        assert signal.getitimer(signal.ITIMER_PROF) == (0.0, 0.0)
        previous = {s: signal.getsignal(s) for s in (signal.SIGPROF, signal.SIGALRM)}
        started = time.process_time_ns()
        remaining = self.deadline - time.monotonic_ns()
        cpu = 60_000_000_000 - self.parent_cpu
        if min(remaining, cpu) <= 0:
            raise RuntimeError("fixture_setup_limit")

        def expire(signum: int, frame: object) -> None:
            raise RuntimeError("fixture_setup_limit")

        try:
            for s in previous:
                signal.signal(s, expire)
            signal.setitimer(signal.ITIMER_REAL, remaining / 1e9)
            signal.setitimer(signal.ITIMER_PROF, cpu / 1e9)
            yield
        finally:
            self.parent_cpu += time.process_time_ns() - started
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.setitimer(signal.ITIMER_PROF, 0)
            for s, handler in previous.items():
                signal.signal(s, handler)
        assert self.parent_cpu <= 60_000_000_000
        assert self.child_cpu <= 60_000_000_000
        assert time.monotonic_ns() <= self.deadline

    def write(self, path: Path, value: bytes) -> None:
        # Count cumulative exports, including any later removed files.
        if self.copies + len(value) > COPY_LIMIT:
            raise RuntimeError("fixture_copy_limit")
        if path.exists() or path.is_symlink():
            raise RuntimeError("fixture_copy_reuse")
        self.copies += len(value)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        sync_directory(path.parent)


class JournalConnection(sqlite3.Connection):
    """Fixed fixture SQL only; admission counts precede every possible write epoch."""

    epochs: int = 0
    configured: bool = False

    def _epoch(self) -> None:
        if self.epochs >= EPOCH_LIMIT:
            raise RuntimeError("fixture_epoch_limit")
        self.epochs += 1

    def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
        normalized = " ".join(sql.upper().split())
        if ";" in normalized.rstrip(";") or normalized.startswith(("ATTACH", "DETACH", "VACUUM")):
            raise RuntimeError("fixture_sql_scope")
        if normalized.startswith("BEGIN"):
            if normalized != "BEGIN IMMEDIATE":
                raise RuntimeError("fixture_sql_scope")
            self._epoch()
        elif normalized.startswith(("INSERT ", "UPDATE ", "DELETE ", "CREATE ")):
            if not self.configured:
                raise RuntimeError("fixture_schema_before_limits")
            if not self.in_transaction:
                self._epoch()
        elif normalized.startswith("PRAGMA "):
            key = normalized[7:].split("=")[0].strip()
            if key not in {
                "PAGE_SIZE",
                "MAX_PAGE_COUNT",
                "CACHE_SPILL",
                "SYNCHRONOUS",
                "JOURNAL_MODE",
                "APPLICATION_ID",
                "USER_VERSION",
            }:
                raise RuntimeError("fixture_sql_scope")
            if "=" in normalized and key not in {"CACHE_SPILL", "SYNCHRONOUS"}:
                # Connection-only spill/synchronous settings do not write the DB.
                self._epoch()
        elif not normalized.startswith(("SELECT ", "COMMIT", "ROLLBACK")):
            raise RuntimeError("fixture_sql_scope")
        return super().execute(sql, parameters)

    def executescript(self, sql_script: str, /) -> sqlite3.Cursor:
        # Journal's reviewed six fixed schema statements contain no embedded ';'.
        statements = [s.strip() for s in sql_script.split(";") if s.strip()]
        if len(statements) != 6 or not self.configured:
            raise RuntimeError("fixture_schema_scope")
        cursor: sqlite3.Cursor | None = None
        for statement in statements:
            cursor = self.execute(statement)
        assert cursor is not None
        return cursor

    def configure(self) -> None:
        self.execute("PRAGMA page_size=4096")
        self.execute("PRAGMA max_page_count=32")
        self.execute("PRAGMA journal_mode=DELETE")
        self.execute("PRAGMA cache_spill=OFF")
        self.execute("PRAGMA synchronous=FULL")
        assert self.execute("PRAGMA page_size").fetchone()[0] == 4096
        assert self.execute("PRAGMA max_page_count").fetchone()[0] == 32
        assert self.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert self.execute("PRAGMA cache_spill").fetchone()[0] == 0
        assert self.execute("PRAGMA synchronous").fetchone()[0] == 2
        self.configured = True


@dataclass
class Fixture:
    root: Path
    build: TrustedInstallation
    budget: SetupBudget
    control: CandidateControl
    freeze: NativeFreezeInput
    freeze_request: NativeFreezeRequest
    experiment: Experiment
    journal: Path


def prepare(root: Path, build: TrustedInstallation, *, classical: bool = False) -> Fixture:
    budget = SetupBudget(time.monotonic_ns() + 180_000_000_000)
    with budget.phase():
        root.mkdir(mode=0o700)
        sync_directory(root.parent)
        plan = NativeAccountingPlan(
            study_id="freeze-" + root.name[:48],
            purpose="synthetic_validation",
            approval_id="NATIVE_COMPARISON_APPROVAL_2026_10_21",
        )
        seed = NativeStudyLedger(plan=plan)
        seed = append_study_attempt(
            seed,
            event_id="setup-reserve",
            expected_revision=0,
            event=StudyAttemptReservation(
                attempt_id="setup",
                phase="accounting",
                cell_id=None,
                operation="accounting",
                config_sha256=message_sha256(plan),
                input_sha256=message_sha256(plan),
                retry_of=None,
                cpu_reservation_ns=120_000_000_000,
                artifact_reservation_bytes=48 * MIB,
                purchase=None,
            ),
        )
        # Durable before material assembly or any observation generation.
        budget.write(root / "setup-accounting.json", raw(seed))
        control = CandidateControl(
            root=str(root),
            plan_sha256=message_sha256(plan),
            source_commit=build.source_commit,
            uv_lock_sha256=build.uv_lock_sha256,
            engine_fingerprint=build.engine_fingerprint,
            installation_sha256=message_sha256(build),
            attempt_id="control",
            tickets=6,
            recovery_tickets=3,
            recovery_work_cpu_ns=8_000_000_000,
            recovery_work_artifact_bytes=2 * MIB,
            ticket_cpu_ns=5_000_000_000,
            ticket_wall_ns=30_000_000_000,
            ticket_artifact_bytes=8192,
            bootstrap_artifact_bytes=4 * MIB,
            bootstrap_cpu_ns=5_000_000_000,
            database_limit_bytes=2 * MIB,
            finalization_records=14,
            finalization_bytes=64 * 1024,
            publication=PublicationEscrow(
                calls=2,
                material_bytes=MIB,
                journal_bytes=128 * 1024,
                ledger_bytes=512 * 1024,
                output_bytes=MIB,
                control_cpu_ns=11_000_000_000,
                control_artifact_bytes=48 * MIB,
                work_cpu_ns=60_000_000_000,
            ),
        )
        seed = append_study_attempt(
            seed,
            event_id="control-reserve",
            expected_revision=1,
            event=StudyAttemptReservation(
                attempt_id="control",
                phase="accounting",
                cell_id=None,
                operation="accounting",
                config_sha256=message_sha256(control),
                input_sha256=control.plan_sha256,
                retry_of=None,
                cpu_reservation_ns=35_000_000_000,
                artifact_reservation_bytes=control.required_control_bytes(),
                purchase=None,
            ),
        )
        manifest, artifacts = materials()
        data = manifest.model_dump(mode="json")
        data.update(
            accounting_plan_sha256=message_sha256(plan),
            source_commit=build.source_commit,
            uv_lock_sha256=build.uv_lock_sha256,
            engine_fingerprint=build.engine_fingerprint,
        )
        artifacts["pool"] = raw(NativeSpringPool(coefficients=(0.0, 1.0, 4.0)))
        artifacts["candidate_config"] = raw(NativeCandidateConfig())
        if classical:
            policy = NativeScoringPolicy()
            config = ClassicalDiagnosticConfig(
                fit_config=SpringFitConfig(),
                prediction_config=SpringPredictionConfig(),
                scoring_policy=policy,
            )
            artifacts["scoring_policy"] = raw(policy)
            artifacts["prediction_config"] = raw(NativePredictionConfig())
            artifacts["classical_diagnostic_config"] = raw(config)
            data["artifacts"].append(
                {
                    "kind": "classical_diagnostic_config",
                    "sha256": digest(raw(config)),
                    "byte_count": len(raw(config)),
                }
            )
        for ref in data["artifacts"]:
            value = artifacts[ref["kind"]]
            ref.update(sha256=digest(value), byte_count=len(value))
        manifest = NativeStudyManifest.model_validate_json(json.dumps(data))
        actual = NativeFreezeInput.model_validate_json(
            json.dumps(
                {
                    "manifest": manifest.model_dump(mode="json"),
                    "artifacts": {k: v.decode() for k, v in artifacts.items()},
                }
            )
        )
        assert sum(map(len, artifacts.values())) <= 64 * 1024 and len(raw(manifest)) <= 64 * 1024
        value = raw(actual)
        budget.write(root / "freeze-input.json", value)
        budget.write(root / "candidate-seed.json", raw(seed))
        budget.write(root / "candidate-installation.json", raw(build))
        budget.write(
            root / "candidate-admission.json",
            raw(CandidateAdmission(control=control, seed_ledger_sha256=digest(raw(seed)))),
        )
        request = NativeFreezeRequest(
            mode="execute",
            logical_id="freeze",
            attempt_id="freeze-0",
            retry_of=None,
            ticket=0,
            expected_revision=len(seed.records),
            expected_head_sha256=head(seed),
            input_path=str(root / "freeze-input.json"),
            input_raw_sha256=digest(value),
            input_bytes=len(value),
            input_sha256=message_sha256(actual),
            config_sha256=message_sha256(manifest),
            cpu_reservation_ns=20_000_000_000,
            artifact_reservation_bytes=4 * MIB,
            output_limit_bytes=64 * 1024,
            wall_limit_ns=30_000_000_000,
        )
        catalog = NativeWorldCatalog.model_validate_json(artifacts["world_catalog"])
        pid = catalog.worlds[0].definition.space.structure.particle_ids[0]
        experiment = Experiment(particles=(ParticleInitial(id=pid, position=(0.125, 0.25)),))
    return Fixture(
        root,
        build,
        budget,
        control,
        actual,
        request,
        experiment,
        root.parent / (root.name + "-journal.sqlite"),
    )


def inject_intents(fixture: Fixture) -> None:
    """One test-only existing-store commit; never a production append/import path."""
    root, budget = fixture.root, fixture.budget
    assert (root / "candidate-created").is_file() and (root / "candidate.sqlite3").is_file()
    with budget.phase(), root_lock(root):
        admission = CandidateAdmission.model_validate_json(
            (root / "candidate-admission.json").read_bytes()
        )
        meter = Extents(root, database_name="candidate.sqlite3")
        store = CandidateStore(root, admission, (root / "candidate-seed.json").read_bytes(), meter)
        try:
            before = store.ledger()
            manifest = study_manifest(before)
            after = before
            for ordinal in range(12):
                after = append_study_attempt(
                    after,
                    event_id=f"purchase-{ordinal}",
                    expected_revision=len(after.records),
                    event=StudyAttemptReservation(
                        attempt_id=f"purchase-{ordinal}",
                        phase="comparison",
                        cell_id=manifest.cells[0].cell_id,
                        operation="purchase",
                        config_sha256=manifest.artifact(
                            "calibration" if ordinal < 4 else "menu"
                        ).sha256,
                        input_sha256=message_sha256(fixture.experiment),
                        retry_of=None,
                        cpu_reservation_ns=5_000_000_000,
                        artifact_reservation_bytes=MIB,
                        purchase=StudyPurchase(
                            operation_id=f"operation-{ordinal}",
                            ordinal=ordinal,
                            experiment_sha256=message_sha256(fixture.experiment),
                            calibration=ordinal < 4,
                        ),
                    ),
                )
            store.limit_control_growth()
            with store.transaction():
                store.replace(before, after)
            assert store._transaction_attempts == 2
        finally:
            store.close()
        assert meter.total <= 4 * STORE_ENVELOPE


def generate_journal(fixture: Fixture) -> None:
    """One bounded child, real engine and explicit final simulation fault."""
    budget = fixture.budget
    with budget.phase():
        assert not fixture.journal.exists()
        assert all(
            not Path(str(fixture.journal) + s).exists() for s in ("-journal", "-wal", "-shm")
        )
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            code = 70
            try:
                remaining = budget.deadline - time.monotonic_ns()
                if remaining <= 0:
                    os._exit(70)
                for sig in (signal.SIGALRM, signal.SIGPROF, signal.SIGXFSZ, signal.SIGXCPU):
                    signal.signal(sig, signal.SIG_DFL)
                signal.setitimer(signal.ITIMER_REAL, remaining / 1e9)
                signal.setitimer(signal.ITIMER_PROF, 60)
                for which, limit in (
                    (resource.RLIMIT_FSIZE, FILE_LIMIT),
                    (resource.RLIMIT_CPU, 60),
                    (resource.RLIMIT_CORE, 0),
                ):
                    restrict_limit(which, limit)
                original = sqlite3.connect
                connections: list[JournalConnection] = []

                def fixed_connect(database: Any, *args: Any, **kwargs: Any) -> JournalConnection:
                    path = Path(database)
                    if (
                        path != fixture.journal
                        or path.is_symlink()
                        or path.stat().st_size != 0
                        or connections
                    ):
                        raise RuntimeError("fixture_connection_scope")
                    kwargs["factory"] = JournalConnection
                    db = original(database, *args, **kwargs)
                    assert isinstance(db, JournalConnection)
                    db.configure()
                    connections.append(db)
                    return db

                connect_patch = patch.object(sqlite3, "connect", fixed_connect)
                connect_patch.start()
                catalog = NativeWorldCatalog.model_validate_json(
                    fixture.freeze.artifacts["world_catalog"]
                )
                world = catalog.worlds[0].definition

                def fail(*args: object, **kwargs: object) -> None:
                    raise SimulationError("explicit current-engine fixture fault")

                with LocalSession.create(
                    fixture.journal, fixture.freeze.manifest.cells[0].journal_id, world
                ) as session:
                    for i in range(11):
                        assert (
                            session.run_experiment(
                                fixture.experiment, operation_id=f"operation-{i}"
                            ).status
                            == "completed"
                        )
                    simulation_patch = patch.object(session_module, "simulate", fail)
                    simulation_patch.start()
                    assert (
                        session.run_experiment(
                            fixture.experiment, operation_id="operation-11"
                        ).status
                        == "failed"
                    )
                    assert session.export().engine_fingerprint == fixture.build.engine_fingerprint
                info = {
                    "epochs": connections[0].epochs,
                    "journal_bytes": fixture.journal.stat().st_size,
                    "page_size": 4096,
                    "max_pages": 32,
                    "file_limit": FILE_LIMIT,
                }
                assert info["epochs"] <= EPOCH_LIMIT and info["journal_bytes"] <= JOURNAL_LIMIT
                message = json.dumps(info).encode()
                assert len(message) < 4096 and os.write(write_fd, message) == len(message)
                code = 0
            except BaseException as error:
                os.write(write_fd, json.dumps({"error": type(error).__name__}).encode())
                code = 70
            finally:
                os.close(write_fd)
                os._exit(code)
        os.close(write_fd)
        reaped = False
        try:
            _, status, usage = os.wait4(pid, 0)
            reaped = True
            budget.child_cpu += math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
            message = os.read(read_fd, 4096)
            assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, message
            info = json.loads(message)
            budget.child_epochs = info["epochs"]
        finally:
            if not reaped:
                os.kill(pid, signal.SIGKILL)
                _, _, usage = os.wait4(pid, 0)
                budget.child_cpu += math.ceil((usage.ru_utime + usage.ru_stime) * 1e9)
            os.close(read_fd)
        assert budget.child_epochs <= 36
        assert 36 * (JOURNAL_LIMIT + FILE_LIMIT) + 4 * STORE_ENVELOPE + COPY_LIMIT == 35677184


def comparison_request(fixture: Fixture, freeze_receipt: bytes) -> NativeComparisonCandidateRequest:
    with fixture.budget.phase():
        manifest = fixture.freeze.manifest
        catalog = NativeWorldCatalog.model_validate_json(fixture.freeze.artifacts["world_catalog"])
        snapshot = read_study_journal(
            fixture.journal, manifest=manifest, catalog=catalog, cell_id=manifest.cells[0].cell_id
        )
        candidate = NativeCandidateInput(
            pool=NativeSpringPool.model_validate_json(fixture.freeze.artifacts["pool"]),
            config=NativeCandidateConfig.model_validate_json(
                fixture.freeze.artifacts["candidate_config"]
            ),
            observations=snapshot.committed_prefix(),
        )
        material = NativeComparisonInput(
            candidate=candidate,
            freeze_logical_id="freeze",
            freeze_receipt_sha256=digest(freeze_receipt),
            journal_path=str(fixture.journal),
            journal_sha256=digest(fixture.journal.read_bytes()),
            journal_bytes=fixture.journal.stat().st_size,
        )
        value = raw(material)
        assert len(value) <= 128 * 1024
        fixture.budget.write(fixture.root / "comparison-input.json", value)
        with sqlite3.connect(fixture.root / "candidate.sqlite3") as db:
            ledger = NativeStudyLedger.model_validate_json(
                db.execute("SELECT ledger FROM state").fetchone()[0]
            )
        return NativeComparisonCandidateRequest(
            mode="execute",
            logical_id="candidate",
            attempt_id="candidate-1",
            retry_of=None,
            cell_id=manifest.cells[0].cell_id,
            ticket=1,
            expected_revision=len(ledger.records),
            expected_head_sha256=head(ledger),
            input_path=str(fixture.root / "comparison-input.json"),
            input_raw_sha256=digest(value),
            input_bytes=len(value),
            input_sha256=message_sha256(candidate),
            config_sha256=message_sha256(candidate.config),
            cpu_reservation_ns=12_000_000_000,
            artifact_reservation_bytes=4 * MIB,
            output_limit_bytes=128 * 1024,
            wall_limit_ns=30_000_000_000,
        )


def classical_request(
    fixture: Fixture,
    candidate_receipt: bytes,
    candidate_result: NativeCandidateResult,
) -> NativeComparisonClassicalRequest:
    """Assemble actual typed private input within the original unresolved setup hold."""
    with fixture.budget.phase():
        material = NativeComparisonInput.model_validate_json(
            (fixture.root / "candidate-input-1").read_bytes()
        )
        frozen = fixture.freeze
        catalog = NativeWorldCatalog.model_validate_json(frozen.artifacts["world_catalog"])
        context = NativeEvaluationInput(
            candidates=material.candidate,
            candidate_result=candidate_result,
            candidate_attempt_id="candidate-1",
            selected=None,
            policy=NativeScoringPolicy.model_validate_json(frozen.artifacts["scoring_policy"]),
            prediction_config=NativePredictionConfig.model_validate_json(
                frozen.artifacts["prediction_config"]
            ),
        )
        actual = ClassicalDiagnosticInput(
            context=context,
            config=ClassicalDiagnosticConfig.model_validate_json(
                frozen.artifacts["classical_diagnostic_config"]
            ),
            world=catalog.worlds[0].definition,
        )
        wrapper = NativeComparisonClassicalInput(
            candidate_logical_id="candidate",
            candidate_receipt_sha256=digest(candidate_receipt),
            diagnostic=actual,
        )
        value = raw(wrapper)
        assert len(value) <= 256 * 1024
        fixture.budget.write(fixture.root / "classical-input.json", value)
        with sqlite3.connect(fixture.root / "candidate.sqlite3") as db:
            ledger = NativeStudyLedger.model_validate_json(
                db.execute("SELECT ledger FROM state").fetchone()[0]
            )
        return NativeComparisonClassicalRequest(
            mode="execute",
            logical_id="classical",
            attempt_id="classical-2",
            retry_of=None,
            cell_id=frozen.manifest.cells[0].cell_id,
            ticket=2,
            expected_revision=len(ledger.records),
            expected_head_sha256=head(ledger),
            input_path=str(fixture.root / "classical-input.json"),
            input_raw_sha256=digest(value),
            input_bytes=len(value),
            input_sha256=message_sha256(actual),
            config_sha256=message_sha256(actual.config),
            cpu_reservation_ns=120_000_000_000,
            artifact_reservation_bytes=8 * MIB,
            output_limit_bytes=MIB,
            wall_limit_ns=180_000_000_000,
        )
