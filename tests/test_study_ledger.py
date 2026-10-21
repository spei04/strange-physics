"""Synthetic event transitions and caps; these tests perform no scientific work."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from test_study_contracts import EXAMPLES

from strange_physics import study_contracts as c
from strange_physics import study_ledger as l
from strange_physics.bounded_json import bounded_canonical
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json

LOCK = b"synthetic-lock"


def plan() -> c.NativeAccountingPlan:
    return c.NativeAccountingPlan.model_validate_json(
        json.dumps(EXAMPLES["valid"]["NativeAccountingPlan"])
    )


def materials() -> tuple[c.NativeStudyManifest, dict[str, bytes]]:
    value = EXAMPLES["valid"]["NativeStudyManifest"] | {
        "uv_lock_sha256": hashlib.sha256(LOCK).hexdigest()
    }
    manifest = c.NativeStudyManifest.model_validate_json(json.dumps(value))
    artifacts = {
        key: canonical_json(val).encode() for key, val in EXAMPLES["artifact_payloads"].items()
    }
    return manifest, artifacts


def empty() -> c.NativeStudyLedger:
    return c.NativeStudyLedger(plan=plan())


def frozen(ledger: c.NativeStudyLedger | None = None) -> c.NativeStudyLedger:
    ledger = empty() if ledger is None else ledger
    manifest, artifacts = materials()
    return l.freeze_native_study(
        ledger,
        event_id="freeze",
        manifest=manifest,
        expected_revision=len(ledger.records),
        expected_purpose="synthetic_validation",
        source_commit=manifest.source_commit,
        uv_lock_bytes=LOCK,
        engine_fingerprint=manifest.engine_fingerprint,
        artifacts=artifacts,
    )


def reserve(identity: str = "attempt-0", **updates: Any) -> c.StudyAttemptReservation:
    value = dict(
        attempt_id=identity,
        phase="reference",
        cell_id=None,
        operation="reference",
        config_sha256="a" * 64,
        input_sha256="b" * 64,
        retry_of=None,
        cpu_reservation_ns=100,
        artifact_reservation_bytes=10,
        purchase=None,
    )
    value.update(updates)
    return c.StudyAttemptReservation.model_validate_json(json.dumps(value))


def append(
    ledger: c.NativeStudyLedger,
    event: c.StudyAttemptReservation | c.StudyAttemptUpdate,
    identity: str | None = None,
) -> c.NativeStudyLedger:
    return l.append_study_attempt(
        ledger,
        event_id=identity or f"event-{len(ledger.records)}",
        event=event,
        expected_revision=len(ledger.records),
    )


def facts(reservation: c.StudyAttemptReservation, outcome: str = "completed") -> c.NativeWorkFacts:
    return c.NativeWorkFacts.model_validate_json(
        json.dumps(
            dict(
                attempt_id=reservation.attempt_id,
                operation=reservation.operation,
                producer_version="synthetic.v1",
                config_sha256=reservation.config_sha256,
                input_sha256=reservation.input_sha256,
                observation_sha256=None,
                model_sha256=None,
                output_sha256="c" * 64,
                unit="work",
                requested_count=1,
                completed_count=int(outcome == "completed"),
                failed_count=int(outcome == "failed"),
                not_assessed_count=int(outcome == "rejected"),
                outcome=outcome,
            )
        )
    )


def update(
    reservation: c.StudyAttemptReservation, state: str = "completed", **updates: Any
) -> c.StudyAttemptUpdate:
    value = dict(
        attempt_id=reservation.attempt_id,
        state=state,
        cpu_ns=30,
        wall_ns=50,
        artifact_bytes=3,
        facts=facts(reservation, state).model_dump(mode="json") if state in l.FINAL else None,
    )
    value.update(updates)
    return c.StudyAttemptUpdate.model_validate_json(json.dumps(value))


def purchase(
    ledger: c.NativeStudyLedger,
    ordinal: int,
    identity: str | None = None,
    retry_of: str | None = None,
) -> c.StudyAttemptReservation:
    manifest = materials()[0]
    cell = manifest.cells[0]
    return reserve(
        identity or f"purchase-{ordinal}",
        phase="comparison",
        cell_id=cell.cell_id,
        operation="purchase",
        config_sha256=manifest.artifact("calibration" if ordinal < 4 else "menu").sha256,
        purchase=dict(
            operation_id=f"operation-{ordinal}",
            ordinal=ordinal,
            experiment_sha256="d" * 64,
            calibration=ordinal < 4,
        ),
        retry_of=retry_of,
    )


def test_accounting_starts_before_freeze_and_all_cells_remain() -> None:
    r = reserve()
    ledger = append(empty(), r)
    ledger = append(ledger, update(r, "unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None))
    before = l.summarize_study(ledger)
    assert before.manifest_sha256 is None and before.cells == ()
    ledger = frozen(ledger)
    after = l.summarize_study(ledger)
    assert after.budget == before.budget
    assert len(after.cells) == 36
    assert {cell.status for cell in after.cells} == {"unstarted"}
    assert after.budget.charged_cpu_ns == 100 and after.budget.unresolved_attempts == 1


@pytest.mark.parametrize(
    "field, limit",
    [("cpu_reservation_ns", c.MAX_CPU_NS), ("artifact_reservation_bytes", c.MAX_ARTIFACT_BYTES)],
)
def test_equality_budget_then_one_over(field: str, limit: int) -> None:
    ledger = append(empty(), reserve("initial", **{field: limit}))
    with pytest.raises(l.StudyLedgerError, match="budget_exhausted"):
        append(ledger, reserve("extra", **{field: 1}))
    assert not l.summarize_study(ledger).budget.over_limit


@pytest.mark.parametrize("state", ["completed", "failed", "rejected"])
def test_final_cost_releases_only_unused_reserved_capacity(state: str) -> None:
    r = reserve()
    ledger = append(append(empty(), r), update(r, state))
    budget = l.summarize_study(ledger).budget
    assert (budget.charged_cpu_ns, budget.charged_artifact_bytes, budget.unresolved_attempts) == (
        30,
        3,
        0,
    )
    assert l.read_study_ledger(ledger.model_dump_json().encode()) == ledger


def test_unknown_measurements_never_refund_or_erase_known_values() -> None:
    r = reserve()
    ledger = append(empty(), r)
    ledger = append(ledger, update(r, "running", cpu_ns=110, artifact_bytes=15))
    ledger = append(ledger, update(r, "unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None))
    assert l.summarize_study(ledger).budget.charged_cpu_ns == 110
    with pytest.raises(l.StudyLedgerError, match="measurement_regressed"):
        append(ledger, update(r, cpu_ns=109, artifact_bytes=15))
    with pytest.raises(l.StudyLedgerError, match="unknown_work_cannot_resume"):
        append(ledger, update(r, "running"))
    ledger = append(ledger, update(r, cpu_ns=110, artifact_bytes=15))
    assert l.summarize_study(ledger).budget.unresolved_attempts == 0


def test_measured_overrun_is_retained_and_blocks_new_work() -> None:
    r = reserve()
    ledger = append(
        append(empty(), r),
        update(r, cpu_ns=c.MAX_CPU_NS + 1, artifact_bytes=c.MAX_ARTIFACT_BYTES + 1),
    )
    budget = l.summarize_study(ledger).budget
    assert budget.over_limit and budget.remaining_cpu_ns == budget.remaining_artifact_bytes == 0
    assert budget.charged_cpu_ns == c.MAX_CPU_NS + 1
    with pytest.raises(l.StudyLedgerError, match="budget_exhausted"):
        append(ledger, reserve("next"))


def test_exact_replay_no_charge_conflict_and_original_revision() -> None:
    r = reserve()
    ledger = append(empty(), r, "original")
    result = l.append_study_attempt(ledger, event_id="original", event=r, expected_revision=0)
    assert result is ledger
    with pytest.raises(l.StudyLedgerError, match="event_conflict"):
        l.append_study_attempt(
            ledger, event_id="original", event=reserve("different"), expected_revision=0
        )
    with pytest.raises(l.StudyLedgerError, match="stale_revision"):
        l.append_study_attempt(
            ledger, event_id="fresh", event=reserve("different"), expected_revision=0
        )
    with pytest.raises(l.StudyLedgerError, match="invalid_revision"):
        l.append_study_attempt(ledger, event_id="original", event=r, expected_revision=True)


def test_real_retry_new_cost_and_original_unknown_capacity_held() -> None:
    r = reserve()
    ledger = append(
        append(empty(), r), update(r, "unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None)
    )
    second = reserve("second", retry_of=r.attempt_id)
    ledger = append(ledger, second)
    assert l.summarize_study(ledger).budget.charged_cpu_ns == 200
    ledger = append(ledger, update(second))
    assert l.summarize_study(ledger).budget.charged_cpu_ns == 130
    assert l.summarize_study(ledger).budget.unresolved_attempts == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_sha256", "f" * 64),
        ("config_sha256", "f" * 64),
        ("phase", "sensitivity"),
        ("operation", "sensitivity"),
    ],
)
def test_retry_cannot_retarget(field: str, value: str) -> None:
    ledger = append(empty(), reserve())
    with pytest.raises(l.StudyLedgerError, match="retry_mismatch"):
        append(ledger, reserve("new", retry_of="attempt-0", **{field: value}))


def test_purchase_pending_failed_and_retries_use_original_slot() -> None:
    ledger = frozen()
    r = purchase(ledger, 0)
    ledger = append(ledger, r)
    ledger = append(ledger, update(r, "unknown", cpu_ns=None, wall_ns=None, artifact_bytes=None))
    again = purchase(ledger, 0, "retry-0", r.attempt_id)
    ledger = append(ledger, again)
    ledger = append(ledger, update(again, "failed"))
    summary = l.summarize_study(ledger)
    assert summary.budget.purchased_slots == 1
    assert summary.cells[0].purchased_slots == 1
    assert summary.budget.charged_cpu_ns == 130
    assert len(summary.cells) == 36


def test_all_twelve_slots_count_and_no_thirteenth() -> None:
    ledger = frozen()
    for index in range(12):
        r = purchase(ledger, index)
        ledger = append(append(ledger, r), update(r, "failed"))
    assert l.summarize_study(ledger).budget.purchased_slots == 12
    r = purchase(ledger, 11, "distinct")
    with pytest.raises(l.StudyLedgerError, match="purchase_conflict"):
        append(ledger, r)


@pytest.mark.parametrize("change", ["gap", "reused_ordinal", "changed_action", "no_retry"])
def test_purchase_identity_conflicts(change: str) -> None:
    ledger = frozen()
    r = purchase(ledger, 0)
    ledger = append(ledger, r)
    if change == "gap":
        bad = purchase(ledger, 2)
    elif change == "reused_ordinal":
        data = purchase(ledger, 0, "other").model_dump(mode="json")
        data["purchase"]["operation_id"] = "another"
        bad = c.StudyAttemptReservation.model_validate_json(json.dumps(data))
    elif change == "changed_action":
        data = purchase(ledger, 0, "other", r.attempt_id).model_dump(mode="json")
        data["purchase"]["experiment_sha256"] = "f" * 64
        bad = c.StudyAttemptReservation.model_validate_json(json.dumps(data))
    else:
        bad = purchase(ledger, 0, "other")
    with pytest.raises(l.StudyLedgerError):
        append(ledger, bad)


@pytest.mark.parametrize("field", ["operation", "input_sha256", "config_sha256"])
def test_facts_match_reserved_operation(field: str) -> None:
    r = reserve()
    ledger = append(empty(), r)
    data = update(r).model_dump(mode="json")
    data["facts"][field] = "selection" if field == "operation" else "f" * 64
    with pytest.raises(l.StudyLedgerError, match="facts_mismatch"):
        append(ledger, c.StudyAttemptUpdate.model_validate_json(json.dumps(data)))


def test_terminal_attempt_cannot_receive_a_second_final_record() -> None:
    r = reserve()
    ledger = append(append(empty(), r), update(r))
    with pytest.raises(l.StudyLedgerError, match="attempt_final"):
        append(ledger, update(r))


@pytest.mark.parametrize(
    "mutation", ["lock", "source", "engine", "purpose", "artifact", "missing", "noncanonical"]
)
def test_freeze_binds_actual_materials(mutation: str) -> None:
    manifest, artifacts = materials()
    kwargs: dict[str, Any] = dict(
        event_id="freeze",
        manifest=manifest,
        expected_revision=0,
        expected_purpose="synthetic_validation",
        source_commit=manifest.source_commit,
        uv_lock_bytes=LOCK,
        engine_fingerprint=manifest.engine_fingerprint,
        artifacts=artifacts,
    )
    if mutation == "lock":
        kwargs["uv_lock_bytes"] = b"different"
    elif mutation == "source":
        kwargs["source_commit"] = "f" * 40
    elif mutation == "engine":
        kwargs["engine_fingerprint"] = "f" * 64
    elif mutation == "purpose":
        kwargs["expected_purpose"] = "native_comparison"
    elif mutation == "artifact":
        artifacts["pool"] = b"{}"
    elif mutation == "missing":
        del artifacts["pool"]
    else:
        raw = b'{ "artifact": "pool", "purpose": "synthetic_validation" }'
        artifacts["pool"] = raw
        data = manifest.model_dump(mode="json")
        ref = next(a for a in data["artifacts"] if a["kind"] == "pool")
        ref.update(sha256=hashlib.sha256(raw).hexdigest(), byte_count=len(raw))
        kwargs["manifest"] = c.NativeStudyManifest.model_validate_json(json.dumps(data))
    with pytest.raises(l.StudyLedgerError):
        l.freeze_native_study(empty(), **kwargs)


def test_freeze_replay_and_no_replacement_allowance() -> None:
    ledger = frozen()
    assert frozen(ledger) is ledger
    manifest, artifacts = materials()
    with pytest.raises(l.StudyLedgerError, match="manifest_already_frozen"):
        l.freeze_native_study(
            ledger,
            event_id="different",
            manifest=manifest,
            expected_revision=1,
            expected_purpose="synthetic_validation",
            source_commit=manifest.source_commit,
            uv_lock_bytes=LOCK,
            engine_fingerprint=manifest.engine_fingerprint,
            artifacts=artifacts,
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"plan":NaN}',
        b'{"records":[],"records":[]}',
        b"[" * 33 + b"]" * 33,
        b"\xff",
        b"{}" * (c.MAX_STUDY_JSON_BYTES // 2 + 1),
    ],
)
def test_strict_ledger_input(raw: bytes) -> None:
    with pytest.raises(ContractViolation):
        l.read_study_ledger(raw)


def test_hash_chain_alone_does_not_accept_missing_attempt_update() -> None:
    event = update(reserve())
    record = c.StudyLedgerRecord(
        event_id="made-up", sequence=0, previous_sha256=message_sha256(plan()), event=event
    )
    ledger = c.NativeStudyLedger(plan=plan(), records=(record,))
    with pytest.raises(l.StudyLedgerError, match="attempt_missing"):
        l.read_study_ledger(ledger.model_dump_json().encode())


def test_aggregate_costs_retain_two_large_measured_overruns() -> None:
    first, second = reserve("first"), reserve("second")
    ledger = append(append(empty(), first), second)
    largest = 2**53 - 1
    ledger = append(ledger, update(first, cpu_ns=largest, artifact_bytes=largest))
    ledger = append(ledger, update(second, cpu_ns=largest, artifact_bytes=largest))
    budget = l.summarize_study(ledger).budget
    assert budget.charged_cpu_ns == budget.charged_artifact_bytes == 2 * largest
    assert budget.over_limit


def test_stop_seals_cell_but_unknown_cost_still_reconciles() -> None:
    ledger = frozen()
    r = purchase(ledger, 0)
    ledger = append(ledger, r)
    cell_id = materials()[0].cells[0].cell_id
    ledger = l.seal_unfinished_cell(
        ledger,
        event_id="stop",
        cell_id=cell_id,
        status="incomplete",
        reason="interrupted",
        expected_revision=len(ledger.records),
    )
    assert l.summarize_study(ledger).cells[0].status == "incomplete"
    assert l.summarize_study(ledger).cells[0].outcome is not None
    with pytest.raises(l.StudyLedgerError, match="cell_sealed"):
        append(ledger, purchase(ledger, 1))
    ledger = append(ledger, update(r, "failed"))
    assert l.summarize_study(ledger).cells[0].unresolved_attempts == 0
    assert l.summarize_study(ledger).cells[0].status == "incomplete"


def test_all_432_reservation_intents_and_36_summaries_retained() -> None:
    manifest = materials()[0]
    ledger = frozen()
    records = list(ledger.records)
    previous = message_sha256(records[-1])
    for cell in manifest.cells:
        for ordinal in range(12):
            event = reserve(
                f"attempt-{cell.cell_id}-{ordinal}",
                phase="comparison",
                cell_id=cell.cell_id,
                operation="purchase",
                config_sha256=manifest.artifact("calibration" if ordinal < 4 else "menu").sha256,
                purchase=dict(
                    operation_id=f"operation-{ordinal}",
                    ordinal=ordinal,
                    experiment_sha256="d" * 64,
                    calibration=ordinal < 4,
                ),
            )
            record = c.StudyLedgerRecord(
                event_id=f"event-{len(records)}",
                sequence=len(records),
                previous_sha256=previous,
                event=event,
            )
            records.append(record)
            previous = message_sha256(record)
    retained = c.NativeStudyLedger(plan=plan(), records=tuple(records))
    summary = l.summarize_study(l.read_study_ledger(retained.model_dump_json().encode()))
    assert summary.budget.purchased_slots == 432 and summary.budget.remaining_slots == 0
    assert len(summary.cells) == 36
    assert all(
        cell.purchased_slots == 12 and cell.unresolved_attempts == 12 for cell in summary.cells
    )


def test_record_headroom_preserves_final_accounting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(l, "MAX_LEDGER_RECORDS", 4)
    first, second = reserve("first"), reserve("second")
    ledger = append(append(empty(), first), second)
    with pytest.raises(l.StudyLedgerError, match="ledger_capacity"):
        append(ledger, reserve("third"))
    ledger = append(ledger, update(first))
    ledger = append(ledger, update(second))
    assert l.summarize_study(ledger).budget.unresolved_attempts == 0


def test_byte_headroom_preserves_final_accounting(monkeypatch: pytest.MonkeyPatch) -> None:
    original = c.MAX_STUDY_JSON_BYTES
    r = reserve()
    ledger = append(empty(), r)
    _, size = bounded_canonical(ledger, original)
    monkeypatch.setattr(l, "MAX_STUDY_JSON_BYTES", size + l.MAX_FINAL_RECORD_BYTES)
    assert l.read_study_ledger(ledger.model_dump_json().encode()) == ledger
    with pytest.raises(l.StudyLedgerError, match="ledger_capacity"):
        append(ledger, reserve("second"))
    done = append(ledger, update(r))
    assert l.summarize_study(done).budget.unresolved_attempts == 0


def test_final_update_maximum_escaping_fits_reserved_headroom() -> None:
    r = reserve("a" * 64)
    value = update(r).model_dump(mode="json")
    value["cpu_ns"] = value["wall_ns"] = value["artifact_bytes"] = 2**53 - 1
    value["facts"]["producer_version"] = "😀" * 128
    value["facts"]["requested_count"] = value["facts"]["completed_count"] = 2**53 - 1
    event = c.StudyAttemptUpdate.model_validate_json(json.dumps(value))
    record = c.StudyLedgerRecord(
        event_id="e" * 64, sequence=c.MAX_LEDGER_RECORDS - 1, previous_sha256="f" * 64, event=event
    )
    assert bounded_canonical(record, c.MAX_STUDY_JSON_BYTES)[1] + 1 < l.MAX_FINAL_RECORD_BYTES
