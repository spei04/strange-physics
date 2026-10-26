"""Finite V3 subprofiles; real fixed purchases, no SQL intent injection or study."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from freeze_journal_fixture import Fixture, prepare
from test_measured_candidates import actual_build, current, last_update

import strange_physics.measured_candidates as supervisor
import strange_physics.purchase_execution as purchase_producer
from strange_physics.candidate_execution_contracts import MIB
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_study import (
    CommittedPurchase,
    commit_journal_purchase,
    commit_native_freeze,
)
from strange_physics.publication_store import digest, head, raw
from strange_physics.purchase_execution_contracts import (
    NativePurchaseInput,
    NativePurchaseReference,
    NativePurchaseRequest,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import StudyAttemptReservation, StudyPurchase
from strange_physics.study_ledger import StudyLedgerError, summarize_study

__all__ = ["actual_build"]


def start(path: Path, build: TrustedInstallation) -> tuple[Fixture, bytes]:
    # V3 setup/control ceilings are retained before original materials. This
    # subset consumes freeze, at most two purchases, and one paid recovery.
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
        role = "calibration" if ordinal < 4 else "menu"
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
    original_writer = supervisor.run_purchase_writer

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
    original_simulate = purchase_producer.simulate

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
    original_simulate = purchase_producer.simulate
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
