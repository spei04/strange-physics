"""Synthetic accounting and real SQLite only; no public call or scientific producer."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from test_study_ledger import append, frozen, reserve

from strange_physics.candidate_execution_contracts import (
    MIB,
    CandidateAdmission,
    CandidateControl,
    PublicationEscrow,
)
from strange_physics.candidate_store import CandidateStore
from strange_physics.measured_publication_contracts import PublicationControl
from strange_physics.publication_handoff_contracts import (
    HANDOFF_PRODUCER,
    HandoffReference,
    PublicationHandoffIntent,
    PublicationHandoffSeal,
    handoff_control_hold,
    read_handoff_seal,
    validate_handoff_ledger,
)
from strange_physics.publication_store import Extents, digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    NativeStudyLedger,
    NativeWorkFacts,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_ledger import StudyLedgerError, summarize_study


@dataclass
class Fixture:
    store: CandidateStore
    seed: NativeStudyLedger
    before: NativeStudyLedger
    after: NativeStudyLedger
    seal: PublicationHandoffSeal


def changed(seal: PublicationHandoffSeal, **values: Any) -> PublicationHandoffSeal:
    return PublicationHandoffSeal.model_validate_json(
        json.dumps(seal.model_dump(mode="json") | values)
    )


def reseed(fixture: Fixture, after: NativeStudyLedger) -> PublicationHandoffSeal:
    return changed(
        fixture.seal,
        sealed_revision=len(after.records),
        sealed_head_sha256=head(after),
        seed_ledger_sha256=digest(raw(after)),
        seed_ledger_bytes=len(raw(after)),
    )


@pytest.fixture
def prepared(tmp_path: Path) -> Iterator[Fixture]:
    source = tmp_path / "source"
    source.mkdir(mode=0o700)
    destination = tmp_path / "publisher"
    destination.mkdir(mode=0o700)
    seed = frozen()
    plan_digest = message_sha256(seed.plan)
    control = CandidateControl(
        root=str(source),
        plan_sha256=plan_digest,
        source_commit="a" * 40,
        uv_lock_sha256="b" * 64,
        engine_fingerprint="c" * 64,
        installation_sha256="d" * 64,
        attempt_id="source-control",
        tickets=43,
        recovery_tickets=1,
        recovery_work_cpu_ns=60_000_000_000,
        recovery_work_artifact_bytes=16 * MIB,
        ticket_cpu_ns=7_000_000_000,
        ticket_wall_ns=30_000_000_000,
        ticket_artifact_bytes=6 * MIB,
        bootstrap_artifact_bytes=4 * MIB,
        bootstrap_cpu_ns=5_000_000_000,
        database_limit_bytes=MIB,
        finalization_records=16,
        finalization_bytes=64 * 1024,
        publication=PublicationEscrow(
            **{
                "calls": 3,
                "material_bytes": 2 * MIB,
                "journal_bytes": 128 * 1024,
                "ledger_bytes": 512 * 1024,
                "output_bytes": 2 * MIB,
                "control_cpu_ns": 16_000_000_000,
                "control_artifact_bytes": 64 * MIB,
                "work_cpu_ns": 90_000_000_000,
            }
        ),
    )
    seed = append(
        seed,
        reserve(
            "setup",
            phase="accounting",
            operation="accounting",
            cpu_reservation_ns=120_000_000_000,
            artifact_reservation_bytes=48 * MIB,
        ),
    )
    seed = append(
        seed,
        reserve(
            control.attempt_id,
            phase="accounting",
            operation="accounting",
            config_sha256=message_sha256(control),
            input_sha256=plan_digest,
            cpu_reservation_ns=control.bootstrap_cpu_ns + control.tickets * control.ticket_cpu_ns,
            artifact_reservation_bytes=control.required_control_bytes(),
        ),
    )
    admission = CandidateAdmission(control=control, seed_ledger_sha256=digest(raw(seed)))
    target = PublicationControl(
        root=str(destination),
        accounting_plan_sha256=plan_digest,
        source_commit=control.source_commit,
        uv_lock_sha256=control.uv_lock_sha256,
        attempt_id="publisher-control",
        tickets=3,
        ticket_cpu_ns=5_000_000_000,
        ticket_wall_ns=30_000_000_000,
        ticket_artifact_bytes=16 * MIB,
    )
    intent = PublicationHandoffIntent(
        transfer_id="transfer",
        source_admission_sha256=message_sha256(admission),
        cell_id=summarize_study(seed).cells[0].cell_id,
        scoring=HandoffReference(logical_id="score", receipt_sha256="e" * 64),
        diagnostic=HandoffReference(logical_id="diagnostic", receipt_sha256="f" * 64),
        destination=target,
        destination_device=destination.stat().st_dev,
        destination_inode=destination.stat().st_ino,
    )
    attempt = reserve(
        "transfer-attempt",
        phase="accounting",
        operation="accounting",
        config_sha256=message_sha256(target),
        input_sha256=message_sha256(intent),
        cpu_reservation_ns=60_000_000_000,
        artifact_reservation_bytes=16 * MIB,
    )
    before = append(seed, attempt)
    facts = NativeWorkFacts(
        attempt_id=attempt.attempt_id,
        operation="accounting",
        producer_version=HANDOFF_PRODUCER,
        config_sha256=attempt.config_sha256,
        input_sha256=attempt.input_sha256,
        observation_sha256=None,
        model_sha256=None,
        output_sha256="0" * 64,
        unit="work",
        requested_count=1,
        completed_count=1,
        failed_count=0,
        not_assessed_count=0,
        outcome="completed",
    )
    update = StudyAttemptUpdate(
        attempt_id=attempt.attempt_id,
        state="completed",
        cpu_ns=100,
        wall_ns=200,
        artifact_bytes=300,
        facts=facts,
    )
    # The provisional seal only supplies the control hold. Its final seed hashes
    # are filled from the actual ledger after that hold has been appended.
    seal = PublicationHandoffSeal(
        intent=intent,
        source_admission=admission,
        transfer_attempt_id=attempt.attempt_id,
        bundle_sha256=facts.output_sha256,
        sealed_revision=len(before.records) + 2,
        sealed_head_sha256="0" * 64,
        seed_ledger_sha256="0" * 64,
        seed_ledger_bytes=1,
    )
    after = append(append(before, update), handoff_control_hold(seal))
    seal = changed(
        seal,
        sealed_head_sha256=head(after),
        seed_ledger_sha256=digest(raw(after)),
        seed_ledger_bytes=len(raw(after)),
    )
    store = CandidateStore(
        source, admission, raw(seed), Extents(source, database_name="candidate.sqlite3")
    )
    with store.transaction():
        store.replace(seed, before)
    fixture = Fixture(store, seed, before, after, seal)
    try:
        yield fixture
    finally:
        store.close()


def seal_store(fixture: Fixture) -> None:
    with fixture.store.transaction():
        fixture.store.seal(fixture.before, fixture.after, fixture.seal)


def test_legacy_store_bytes_and_schema_stay_v1(prepared: Fixture) -> None:
    store = prepared.store
    assert store.db.execute("PRAGMA user_version").fetchone() == (1,)
    assert store.handoff() is None
    assert raw(store.ledger()) == raw(prepared.before)
    tables = store.db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    assert tables == [("closures",), ("records",), ("state",)]
    with store.transaction():
        store.stop()
    assert store.stopped
    assert store.handoff() is None


def test_atomic_seal_reopens_with_exact_seed_and_unresolved_holds(prepared: Fixture) -> None:
    seal_store(prepared)
    store = prepared.store
    assert store.db.execute("PRAGMA user_version").fetchone() == (2,)
    actual = store.handoff()
    assert actual is not None
    assert raw(actual) == raw(prepared.seal)
    assert raw(store.ledger()) == raw(prepared.after)
    summary = summarize_study(store.ledger())
    assert summary.budget.unresolved_attempts == 3
    assert summary.budget.charged_artifact_bytes == (
        48 * MIB + store.admission.control.required_control_bytes() + 64 * MIB + 300
    )
    assert summary.budget.remaining_artifact_bytes >= 3 * 23_592_960 + 16 * MIB
    reopened = CandidateStore(
        store.root,
        store.admission,
        raw(prepared.seed),
        Extents(store.root, database_name="candidate.sqlite3"),
    )
    try:
        assert reopened.handoff() == prepared.seal
        with pytest.raises(StudyLedgerError, match="^candidate_store_sealed$"):
            reopened.require_writable()
    finally:
        reopened.close()


@pytest.mark.parametrize("operation", ["replace", "stop", "transaction", "seal"])
def test_seal_denies_all_store_mutators(prepared: Fixture, operation: str) -> None:
    seal_store(prepared)
    store = prepared.store
    with pytest.raises(StudyLedgerError, match="^candidate_store_sealed$"):
        if operation == "replace":
            proposal = append(
                prepared.after, reserve("paid-recovery", phase="accounting", operation="accounting")
            )
            store.replace(prepared.after, proposal)
        elif operation == "stop":
            store.stop()
        elif operation == "transaction":
            with store.transaction():
                pytest.fail("A sealed source cannot enter another write transaction")
        else:
            store.seal(prepared.before, prepared.after, prepared.seal)
    assert raw(store.ledger()) == raw(prepared.after)
    assert store.handoff() == prepared.seal


def test_seal_requires_existing_transaction_and_unstopped_source(prepared: Fixture) -> None:
    with pytest.raises(StudyLedgerError, match="^candidate_handoff_transaction$"):
        prepared.store.seal(prepared.before, prepared.after, prepared.seal)
    with prepared.store.transaction():
        prepared.store.stop()
        with pytest.raises(StudyLedgerError, match="^candidate_stopped$"):
            prepared.store.seal(prepared.before, prepared.after, prepared.seal)
    assert prepared.store.handoff() is None
    assert raw(prepared.store.ledger()) == raw(prepared.before)


def test_seal_rollback_preserves_v1_and_all_original_holds(prepared: Fixture) -> None:
    with pytest.raises(RuntimeError, match="^before-commit$"):
        with prepared.store.transaction():
            prepared.store.seal(prepared.before, prepared.after, prepared.seal)
            raise RuntimeError("before-commit")
    assert prepared.store.db.execute("PRAGMA user_version").fetchone() == (1,)
    assert (
        prepared.store.db.execute("SELECT name FROM sqlite_master WHERE name='handoff'").fetchone()
        is None
    )
    assert raw(prepared.store.ledger()) == raw(prepared.before)
    assert summarize_study(prepared.store.ledger()).budget.unresolved_attempts == 3
    # The failed transaction used its envelope; only the original fourth remains.
    seal_store(prepared)
    assert prepared.store.handoff() == prepared.seal


@pytest.mark.parametrize("field", ["seed_ledger_sha256", "sealed_head_sha256", "bundle_sha256"])
def test_seal_rejects_substituted_seed_or_facts(prepared: Fixture, field: str) -> None:
    bad = changed(prepared.seal, **{field: "1" * 64})
    code = "candidate_handoff_accounting" if field == "bundle_sha256" else "candidate_handoff_seed"
    with pytest.raises(StudyLedgerError, match=f"^{code}$"):
        with prepared.store.transaction():
            prepared.store.seal(prepared.before, prepared.after, bad)
    assert prepared.store.handoff() is None
    assert raw(prepared.store.ledger()) == raw(prepared.before)


@pytest.mark.parametrize("fault", ["unknown", "overrun", "short-hold", "extra-update"])
def test_seal_needs_known_transfer_and_exact_new_control_hold(
    prepared: Fixture, fault: str
) -> None:
    update = prepared.after.records[-2].event
    assert isinstance(update, StudyAttemptUpdate)
    hold = handoff_control_hold(prepared.seal)
    if fault == "unknown":
        update = StudyAttemptUpdate.model_validate(
            update.model_dump() | {"state": "unknown", "cpu_ns": None}
        )
    elif fault == "overrun":
        update = StudyAttemptUpdate.model_validate(update.model_dump() | {"cpu_ns": 60_000_000_001})
    elif fault == "short-hold":
        hold = type(hold).model_validate(
            hold.model_dump() | {"artifact_reservation_bytes": 64 * MIB - 1}
        )
    after = append(append(prepared.before, update), hold)
    if fault == "extra-update":
        after = append(
            after,
            StudyAttemptUpdate(
                attempt_id="setup",
                state="unknown",
                cpu_ns=None,
                wall_ns=None,
                artifact_bytes=None,
                facts=None,
            ),
        )
    code = (
        "candidate_handoff_identity" if fault == "extra-update" else "candidate_handoff_accounting"
    )
    with pytest.raises(StudyLedgerError, match=f"^{code}$"):
        with prepared.store.transaction():
            prepared.store.seal(prepared.before, after, reseed(prepared, after))
    assert raw(prepared.store.ledger()) == raw(prepared.before)


@pytest.mark.parametrize("fault", ["missing-row", "wrong-digest", "downgraded-version"])
def test_reopen_rejects_incomplete_or_downgraded_seal(prepared: Fixture, fault: str) -> None:
    seal_store(prepared)
    store = prepared.store
    if fault == "missing-row":
        store.db.execute("DELETE FROM handoff")
    elif fault == "wrong-digest":
        store.db.execute("UPDATE handoff SET digest=?", ("1" * 64,))
    else:
        store.db.execute("PRAGMA user_version=1")
    with pytest.raises(StudyLedgerError):
        CandidateStore(
            store.root,
            store.admission,
            raw(prepared.seed),
            Extents(store.root, database_name="candidate.sqlite3"),
        )


@pytest.mark.parametrize(
    "fault", ["relative-root", "two-tickets", "same-reference", "wrong-source", "small-control"]
)
def test_versioned_contract_denies_authority_substitutions(prepared: Fixture, fault: str) -> None:
    value = prepared.seal.model_dump(mode="json")
    if fault == "relative-root":
        value["intent"]["destination"]["root"] = "relative"
    elif fault == "two-tickets":
        value["intent"]["destination"]["tickets"] = 2
    elif fault == "same-reference":
        value["intent"]["diagnostic"] = value["intent"]["scoring"]
    elif fault == "wrong-source":
        value["intent"]["destination"]["source_commit"] = "f" * 40
    else:
        value["intent"]["destination"]["ticket_cpu_ns"] = 6_000_000_000
    with pytest.raises(ValueError):
        read_handoff_seal(json.dumps(value).encode())


def test_post_commit_acknowledgement_failure_cannot_append_fallback(
    prepared: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_ack(path: Path) -> None:
        assert path == prepared.store.root
        raise OSError("lost-seal-ack")

    monkeypatch.setattr("strange_physics.candidate_store.durable_directory", fail_ack)
    with pytest.raises(OSError, match="^lost-seal-ack$"):
        seal_store(prepared)
    assert prepared.store.handoff() == prepared.seal
    assert raw(prepared.store.ledger()) == raw(prepared.after)
    with pytest.raises(StudyLedgerError, match="^candidate_store_sealed$"):
        with prepared.store.transaction():
            pytest.fail("Lost acknowledgement must not reopen source accounting")
    assert summarize_study(prepared.store.ledger()).budget.unresolved_attempts == 3


@pytest.mark.parametrize("deficit", [0, 1])
def test_actual_publisher_hold_is_not_protected_twice(prepared: Fixture, deficit: int) -> None:
    c = prepared.store.admission.control
    budget = summarize_study(prepared.after).budget
    protected = (
        c.publication.calls * c.publication.work_bytes_per_call()
        + c.recovery_tickets * c.recovery_work_artifact_bytes
    )
    prefix = append(
        prepared.seed,
        reserve(
            "other-unknown",
            phase="accounting",
            operation="accounting",
            artifact_reservation_bytes=budget.remaining_artifact_bytes - protected + deficit,
        ),
    )
    transfer, update, hold = (record.event for record in prepared.after.records[-3:])
    assert isinstance(transfer, StudyAttemptReservation)
    assert isinstance(update, StudyAttemptUpdate)
    assert isinstance(hold, StudyAttemptReservation)
    final = append(append(append(prefix, transfer), update), hold)
    seal = reseed(prepared, final)
    assert summarize_study(final).budget.remaining_artifact_bytes == protected - deficit
    if deficit:
        with pytest.raises(StudyLedgerError, match="^candidate_handoff_headroom$"):
            validate_handoff_ledger(seal, final)
    else:
        validate_handoff_ledger(seal, final)
