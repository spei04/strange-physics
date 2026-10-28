"""Finite V3 subprofiles; real fixed purchases, no SQL intent injection or study."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Literal

import pytest
from freeze_journal_fixture import (
    COPY_LIMIT,
    Fixture,
    classical_request,
    comparison_request,
    prepare,
)
from test_measured_candidates import actual_build, current, last_update

import strange_physics.candidate_store as candidate_store_module
import strange_physics.measured_candidates as supervisor
import strange_physics.purchase_execution as purchase_producer
from strange_physics.candidate_execution_contracts import MIB
from strange_physics.candidate_store import CandidateStore
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_study import (
    CommittedPurchase,
    commit_journal_candidates,
    commit_journal_classical,
    commit_journal_purchase,
    commit_native_freeze,
)
from strange_physics.publication_store import digest, durable_directory, head, raw
from strange_physics.purchase_execution import run_purchase_writer
from strange_physics.purchase_execution_contracts import (
    NativePurchaseInput,
    NativePurchaseReference,
    NativePurchaseRequest,
)
from strange_physics.purchase_journal import JournalEpochs
from strange_physics.research_contracts import message_sha256
from strange_physics.simulation import SimulationError, simulate
from strange_physics.study_contracts import StudyAttemptReservation, StudyPurchase
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalInput,
)
from strange_physics.study_ledger import StudyLedgerError, summarize_study

__all__ = ["actual_build"]


def start(path: Path, build: TrustedInstallation) -> tuple[Fixture, bytes]:
    # V3 setup/control ceilings are retained before original materials. This
    # subsets and full specimen consume only their declared fixed calls.
    f = prepare(path, build, classical=True, purchase=True)
    assert not f.journal.exists()
    value = commit_native_freeze(f.root, f.freeze_request)
    return f, raw(value.receipt)


def purchase_request(
    f: Fixture,
    freeze_receipt: bytes,
    *,
    ordinal: int = 0,
    ticket: int = 1,
    predecessor: CommittedPurchase | None = None,
) -> NativePurchaseRequest:
    with f.budget.phase():
        manifest = f.freeze.manifest
        role: Literal["calibration", "menu"] = "calibration" if ordinal < 4 else "menu"
        metadata = StudyPurchase(
            operation_id=f"operation-{ordinal}",
            ordinal=ordinal,
            calibration=ordinal < 4,
            experiment_sha256=message_sha256(f.experiment),
        )
        actual = NativePurchaseInput(
            freeze_logical_id="freeze",
            freeze_receipt_sha256=digest(freeze_receipt),
            cell_id=manifest.cells[0].cell_id,
            purchase=metadata,
            config_sha256=manifest.artifact(role).sha256,
            experiment=f.experiment,
            journal_path=str(f.journal),
            predecessor=None
            if predecessor is None
            else NativePurchaseReference(
                logical_id=predecessor.receipt.logical_id,
                receipt_sha256=digest(raw(predecessor.receipt)),
                kind=predecessor.receipt.kind,
            ),
            initial_journal=None if predecessor is None else predecessor.result.journal,
        )
        value = raw(actual)
        path = f.root / f"original-purchase-{ticket}.json"
        f.budget.write(path, value)
        ledger = current(f.root)
        return NativePurchaseRequest(
            mode="execute",
            logical_id=f"purchase-{ordinal}",
            purchase_logical_id=f"purchase-{ordinal}",
            purchase=metadata,
            attempt_id=f"purchase-attempt-{ticket}",
            retry_of=None,
            cell_id=actual.cell_id,
            ticket=ticket,
            expected_revision=len(ledger.records),
            expected_head_sha256=head(ledger),
            input_path=str(path),
            input_raw_sha256=digest(value),
            input_bytes=len(value),
            input_sha256=message_sha256(actual),
            config_sha256=actual.config_sha256,
            cpu_reservation_ns=20_000_000_000,
            artifact_reservation_bytes=4 * MIB,
            output_limit_bytes=128 * 1024,
            wall_limit_ns=60_000_000_000,
        )


def recover(request: NativePurchaseRequest, **changes: Any) -> NativePurchaseRequest:
    return NativePurchaseRequest.model_validate(
        {
            **request.model_dump(),
            "mode": "recover",
            "ticket": 15,
            "attempt_id": "paid-recovery",
            "retry_of": None,
            "cpu_reservation_ns": 8_000_000_000,
            "artifact_reservation_bytes": 2 * MIB,
            **changes,
        }
    )


def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("producer must not run")


def test_first_purchase_durable_reservation_actual_cost_and_original_replay(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    f, frozen = start(tmp_path / "first", actual_build)
    request = purchase_request(f, frozen)
    original_writer = run_purchase_writer

    def ordered(*args: Any, **kwargs: Any) -> Any:
        ledger = current(f.root)
        reservation = ledger.records[-1].event
        assert isinstance(reservation, StudyAttemptReservation)
        assert reservation.purchase == request.purchase
        assert reservation.attempt_id == request.attempt_id
        assert not f.journal.exists()  # Still no live Journal before durable intent.
        return original_writer(*args, **kwargs)

    monkeypatch.setattr(supervisor, "run_purchase_writer", ordered)
    value = commit_journal_purchase(f.root, request)
    assert value.result.kind == "execution" and value.result.record.status == "completed"
    assert value.result.record.index == 0 and value.result.context.observed_journal is None
    assert value.holder_status == 0 and value.holder_cpu_ns is not None
    assert value.measurements.child_cpu_ns > 0
    update = last_update(value.ledger)
    assert update.state == "completed"
    assert update.cpu_ns == value.measurements.parent_cpu_ns + value.measurements.child_cpu_ns
    assert update.facts == value.result.facts
    assert len(value.ledger.records) == 7
    assert summarize_study(value.ledger).budget.unresolved_attempts == 2
    Path(request.input_path).unlink()
    monkeypatch.setattr(supervisor, "run_purchase_writer", forbidden)
    monkeypatch.setattr(purchase_producer, "simulate", forbidden)
    replay = commit_journal_purchase(f.root, recover(request))
    assert replay.replayed and replay.result_raw == value.result_raw
    assert (
        raw(replay.receipt) == raw(value.receipt)
        and replay.original_ledger == value.original_ledger
    )
    assert len(replay.ledger.records) == 9
    assert summarize_study(replay.ledger).budget.unresolved_attempts == 2
    assert replay.measurements.child_cpu_ns == 0 and replay.holder_cpu_ns is None


def test_infrastructure_pending_retry_preserves_original_hold(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    f, frozen = start(tmp_path / "pending", actual_build)
    request = purchase_request(f, frozen)
    original_simulate = simulate

    def fault(*args: Any, **kwargs: Any) -> Any:
        raise OSError("declared infrastructure fault")

    monkeypatch.setattr(purchase_producer, "simulate", fault)
    with pytest.raises(StudyLedgerError, match="purchase_writer_unknown"):
        commit_journal_purchase(f.root, request)
    failed = current(f.root)
    assert last_update(failed).state == "unknown" and last_update(failed).facts is None
    assert summarize_study(failed).budget.unresolved_attempts == 3
    monkeypatch.setattr(purchase_producer, "simulate", original_simulate)
    retry = NativePurchaseRequest.model_validate(
        {
            **request.model_dump(),
            "ticket": 2,
            "attempt_id": "retry",
            "retry_of": request.attempt_id,
            "expected_revision": len(failed.records),
            "expected_head_sha256": head(failed),
        }
    )
    value = commit_journal_purchase(f.root, retry)
    assert value.result.context.row_state == "pending"
    assert value.result.record.index == 0
    assert value.result.record.status == "completed"
    assert summarize_study(value.ledger).budget.unresolved_attempts == 3
    assert value.receipt.input_raw_sha256 == request.input_raw_sha256


def test_terminal_without_closure_reconciles_then_allows_next_purchase(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    f, frozen = start(tmp_path / "reconcile", actual_build)
    request = purchase_request(f, frozen)
    original_snapshot = supervisor._purchase_snapshot
    once = False

    def after_terminal(*args: Any, **kwargs: Any) -> None:
        nonlocal once
        if not once:
            once = True
            raise OSError("declared after-Journal-commit fault")
        original_snapshot(*args, **kwargs)

    monkeypatch.setattr(supervisor, "_purchase_snapshot", after_terminal)
    with pytest.raises(OSError, match="after-Journal-commit"):
        commit_journal_purchase(f.root, request)
    before = current(f.root)
    assert last_update(before).state == "unknown"
    monkeypatch.setattr(supervisor, "_purchase_snapshot", original_snapshot)
    original_simulate = simulate
    monkeypatch.setattr(purchase_producer, "simulate", forbidden)
    reconciliation = recover(
        request,
        purpose="reconciliation",
        logical_id="reconciled-purchase-0",
        reconcile_attempt_id=request.attempt_id,
    )
    value = commit_journal_purchase(f.root, reconciliation)
    assert value.receipt.kind == value.result.kind == "reconciliation"
    assert value.result.context.row_state == "terminal"
    assert value.result.facts.operation == "accounting"
    assert summarize_study(value.ledger).budget.unresolved_attempts == 3
    assert value.result.facts.attempt_id == reconciliation.attempt_id
    monkeypatch.setattr(purchase_producer, "simulate", original_simulate)
    next_request = purchase_request(f, frozen, ordinal=1, ticket=2, predecessor=value)
    next_value = commit_journal_purchase(f.root, next_request)
    assert next_value.result.record.index == 1
    assert summarize_study(next_value.ledger).budget.unresolved_attempts == 3


@pytest.mark.parametrize("deficit", [0, 1])
def test_complete_copy_headroom_equal_and_one_below_before_writer(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
    deficit: int,
) -> None:
    f, frozen = start(tmp_path / "headroom", actual_build)
    request = purchase_request(f, frozen)
    envelope = request.input_bytes + 2 * request.output_limit_bytes + 2 * 128 * 1024
    request = NativePurchaseRequest.model_validate(
        {
            **request.model_dump(),
            "artifact_reservation_bytes": envelope - deficit,
        }
    )
    entered = False

    def boundary(*args: Any, **kwargs: Any) -> Any:
        nonlocal entered
        entered = True
        reservation = current(f.root).records[-1].event
        assert isinstance(reservation, StudyAttemptReservation)
        assert reservation.purchase == request.purchase
        assert not f.journal.exists()
        raise OSError("admitted writer boundary")

    monkeypatch.setattr(supervisor, "run_purchase_writer", boundary)
    if deficit:
        with pytest.raises(StudyLedgerError, match="^candidate_work_headroom$"):
            commit_journal_purchase(f.root, request)
        assert len(current(f.root).records) == 5
    else:
        with pytest.raises(OSError, match="admitted writer boundary"):
            commit_journal_purchase(f.root, request)
        assert last_update(current(f.root)).state == "unknown"
    assert entered == (deficit == 0)
    assert not f.journal.exists()


def test_lost_writer_reap_observation_retains_unknown_without_holder_or_signal(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f, frozen = start(tmp_path / "lost-wait", actual_build)
    request = purchase_request(f, frozen)
    actual_wait = os.wait4
    calls = 0

    def lost_wait(pid: int, options: int) -> Any:
        nonlocal calls
        calls += 1
        value = actual_wait(pid, options)
        if calls == 1:
            raise OSError("lost writer wait observation")
        return value

    monkeypatch.setattr(os, "wait4", lost_wait)
    monkeypatch.setattr(os, "kill", forbidden)
    monkeypatch.setattr(supervisor, "capture_journal", forbidden)
    with pytest.raises(OSError, match="lost writer wait observation") as error:
        commit_journal_purchase(f.root, request)
    assert calls == 2
    assert any("unavailable" in note for note in error.value.__notes__)
    ledger = current(f.root)
    update = last_update(ledger)
    assert update.state == "unknown" and update.facts is None
    assert update.cpu_ns is not None and update.cpu_ns >= 0
    assert summarize_study(ledger).budget.unresolved_attempts == 3
    assert not (f.root / "candidate-purchase-capture-1").exists()


def test_sixteen_call_paid_mixed_prefix_and_downstream(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f, frozen = start(tmp_path / "sixteen", actual_build)
    purchases: list[CommittedPurchase] = []
    requests: list[NativePurchaseRequest] = []
    epochs: list[JournalEpochs] = []
    epoch_factory = JournalEpochs

    def tracked_epochs() -> JournalEpochs:
        value = epoch_factory()
        epochs.append(value)
        return value

    def scientific_failure(*args: Any, **kwargs: Any) -> Any:
        raise SimulationError("declared finite last-slot simulation fault")

    monkeypatch.setattr(supervisor, "JournalEpochs", tracked_epochs)
    for ordinal in range(12):
        request = purchase_request(
            f,
            frozen,
            ordinal=ordinal,
            ticket=ordinal + 1,
            predecessor=purchases[-1] if purchases else None,
        )
        assert not (f.root / f"candidate-ticket-{ordinal + 1}").exists()
        with monkeypatch.context() as m:
            if ordinal == 11:
                m.setattr(purchase_producer, "simulate", scientific_failure)
            value = commit_journal_purchase(f.root, request)
        assert value.result.record.index == ordinal
        assert value.result.record.status == ("failed" if ordinal == 11 else "completed")
        assert last_update(value.ledger).state == value.result.facts.outcome
        assert value.holder_status == 0 and value.holder_cpu_ns is not None
        assert summarize_study(value.ledger).budget.unresolved_attempts == 2
        purchases.append(value)
        requests.append(request)
    assert len(epochs) == 12 and all(e.used == 15 for e in epochs)
    assert f.journal.stat().st_size <= 128 * 1024
    candidate_request = comparison_request(f, frozen, ticket=13)
    candidate_request = NativeComparisonCandidateRequest.model_validate(
        {
            **candidate_request.model_dump(),
            "artifact_reservation_bytes": 8 * MIB,
        }
    )
    candidate = commit_journal_candidates(f.root, candidate_request)
    assert candidate.result.payload.status == "produced"
    diagnostic_request = classical_request(
        f,
        raw(candidate.receipt),
        candidate.result,
        candidate_ticket=13,
        ticket=14,
    )
    material = NativeComparisonClassicalInput.model_validate_json(
        Path(diagnostic_request.input_path).read_bytes()
    )
    assert material.diagnostic.context.selected is None
    diagnostic = commit_journal_classical(f.root, diagnostic_request)
    payload = diagnostic.result.payload
    assert payload.status == "evaluated" and payload.evaluation is not None
    assert payload.evaluation.status == "scored" and payload.fit is not None
    assert [r.status for r in payload.fit.observations.records] == ["completed"] * 11 + ["failed"]
    assert raw(payload.fit.observations) == raw(material.diagnostic.context.candidates.observations)
    journal_bytes = f.journal.stat().st_size
    with f.budget.phase():
        for path in [
            f.journal,
            Path(f.freeze_request.input_path),
            Path(candidate_request.input_path),
            Path(diagnostic_request.input_path),
            *(Path(r.input_path) for r in requests),
        ]:
            path.unlink()
    monkeypatch.setattr(supervisor, "run_purchase_writer", forbidden)
    monkeypatch.setattr(supervisor, "_run_child", forbidden)
    monkeypatch.setattr(supervisor, "propose_freeze", forbidden)
    monkeypatch.setattr(purchase_producer, "simulate", forbidden)
    replay = commit_journal_purchase(f.root, recover(requests[-1]))
    assert replay.replayed and replay.result_raw == purchases[-1].result_raw
    assert raw(replay.receipt) == raw(purchases[-1].receipt)
    assert replay.original_ledger == purchases[-1].original_ledger
    ledger = replay.ledger
    assert len(ledger.records) == 35
    assert summarize_study(ledger).budget.unresolved_attempts == 2
    assert len(raw(ledger)) <= 256 * 1024
    assert (f.root / "candidate.sqlite3").stat().st_size <= 2 * MIB
    assert f.control.publication.required_bytes() == 80 * MIB
    assert f.budget.copies <= COPY_LIMIT and f.budget.child_epochs == 0
    assert f.budget.store_attempts == 0  # No fixture-only intent injection.
    assert f.budget.parent_cpu + f.budget.child_cpu <= 120_000_000_000
    proof = {
        "scope": "Synthetic fixed 16-call paid producer conformance, not a study or handoff.",
        "public_calls": 16,
        "purchase_writer_children": 12,
        "holder_children": 12,
        "other_numerical_children": 2,
        "precharged_journal_epochs": sum(e.used for e in epochs),
        "ledger_records": len(ledger.records),
        "ledger_bytes": len(raw(ledger)),
        "unresolved_holds": 2,
        "journal_bytes_before_removal": journal_bytes,
        "store_bytes": (f.root / "candidate.sqlite3").stat().st_size,
        "purchase_measurements": [p.measurements.model_dump() for p in purchases],
        "holder_cpu_ns": [p.holder_cpu_ns for p in purchases],
        "candidate_measurements": candidate.measurements.model_dump(),
        "classical_measurements": diagnostic.measurements.model_dump(),
        "replay_measurements": replay.measurements.model_dump(),
        "setup_parent_cpu_before_proof_ns": f.budget.parent_cpu,
        "setup_copy_bytes_before_proof": f.budget.copies,
        "declared_artifact_bytes": 589561856,
        "declared_cpu_ns": 708000000000,
        "publication_protection_bytes": 80 * MIB,
    }
    with f.budget.phase():
        f.budget.write(
            f.root / "sixteen-call-proof.json", json.dumps(proof, sort_keys=True).encode()
        )


def test_purchase_actual_lost_ack_recovers_original_without_live_paths(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f, frozen = start(tmp_path / "lost-ack", actual_build)
    request = purchase_request(f, frozen)
    close = CandidateStore.close
    fired = False

    def lost_ack(self: CandidateStore) -> None:
        nonlocal fired
        close(self)
        if not fired:
            fired = True
            raise OSError("purchase closure acknowledgement lost")

    with monkeypatch.context() as m:
        m.setattr(CandidateStore, "close", lost_ack)
        with pytest.raises(OSError, match="acknowledgement lost"):
            commit_journal_purchase(f.root, request)
    with f.budget.phase():
        with sqlite3.connect(
            (f.root / "candidate.sqlite3").as_uri() + "?mode=ro",
            uri=True,
        ) as db:
            receipt = db.execute(
                "SELECT receipt FROM closures WHERE logical_id=?",
                (request.logical_id,),
            ).fetchone()[0]
        result = (f.root / "candidate-output-1").read_bytes()
        f.journal.unlink()
        Path(request.input_path).unlink()
        Path(f.freeze_request.input_path).unlink()
    monkeypatch.setattr(supervisor, "run_purchase_writer", forbidden)
    monkeypatch.setattr(purchase_producer, "simulate", forbidden)
    replay = commit_journal_purchase(f.root, recover(request))
    assert replay.result_raw == result and raw(replay.receipt) == receipt
    assert replay.replayed and len(replay.ledger.records) == 9
    assert summarize_study(replay.ledger).budget.unresolved_attempts == 2


def test_missing_journal_retry_keeps_original_unknown_intent(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f, frozen = start(tmp_path / "missing-retry", actual_build)
    request = purchase_request(f, frozen)

    def before_writer(*args: Any, **kwargs: Any) -> Any:
        reservation = current(f.root).records[-1].event
        assert isinstance(reservation, StudyAttemptReservation)
        assert reservation.purchase == request.purchase
        assert not f.journal.exists()
        raise OSError("writer unavailable after reservation")

    with monkeypatch.context() as m:
        m.setattr(supervisor, "run_purchase_writer", before_writer)
        with pytest.raises(OSError, match="writer unavailable"):
            commit_journal_purchase(f.root, request)
    failed = current(f.root)
    assert last_update(failed).state == "unknown" and not f.journal.exists()
    retry = NativePurchaseRequest.model_validate(
        {
            **request.model_dump(),
            "ticket": 2,
            "attempt_id": "retry",
            "retry_of": request.attempt_id,
            "expected_revision": len(failed.records),
            "expected_head_sha256": head(failed),
        }
    )
    value = commit_journal_purchase(f.root, retry)
    assert value.result.record.index == 0 and value.result.context.row_state == "missing"
    assert value.result.context.observed_journal is None
    assert summarize_study(value.ledger).budget.unresolved_attempts == 3
    assert value.receipt.input_raw_sha256 == request.input_raw_sha256


@pytest.mark.parametrize("boundary", ["cas", "reservation_durability"])
def test_purchase_admission_failure_precedes_every_journal_entry(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    f, frozen = start(tmp_path / boundary, actual_build)
    request = purchase_request(f, frozen)
    monkeypatch.setattr(supervisor, "JournalEpochs", forbidden)
    monkeypatch.setattr(supervisor, "run_purchase_writer", forbidden)
    if boundary == "cas":
        request = NativePurchaseRequest.model_validate(
            {
                **request.model_dump(),
                "expected_revision": request.expected_revision + 1,
            }
        )
        with pytest.raises(StudyLedgerError, match="^candidate_stale_head$"):
            commit_journal_purchase(f.root, request)
        assert len(current(f.root).records) == 5
    else:
        durable = durable_directory

        def failed_sync(path: Path) -> None:
            if any(
                isinstance(r.event, StudyAttemptReservation)
                and r.event.attempt_id == request.attempt_id
                for r in current(f.root).records
            ):
                raise OSError("reserved store directory sync")
            durable(path)

        monkeypatch.setattr(candidate_store_module, "durable_directory", failed_sync)
        with pytest.raises(OSError, match="reserved store directory sync"):
            commit_journal_purchase(f.root, request)
        ledger = current(f.root)
        assert len(ledger.records) == 6
        assert isinstance(ledger.records[-1].event, StudyAttemptReservation)
        assert summarize_study(ledger).budget.unresolved_attempts == 3
    assert not f.journal.exists()
