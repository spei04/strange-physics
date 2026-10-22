"""Pure cumulative native accounting; no persistence, process launch or measurements.

A retained ledger is authoritative producer evidence, not proof that real work was
measured. Every proposed append still validates the complete bounded history.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal

from pydantic import JsonValue

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.study_contracts import (
    MAX_LEDGER_RECORDS,
    MAX_STUDY_JSON_BYTES,
    ArtifactKind,
    NativeAccountingPlan,
    NativeBudgetView,
    NativeCellSummary,
    NativeStudyLedger,
    NativeStudyManifest,
    NativeStudySummary,
    NativeWorldCatalog,
    StudyAttemptReservation,
    StudyAttemptUpdate,
    StudyCellOutcome,
    StudyEvent,
    StudyLedgerRecord,
    StudyManifestFreeze,
    StudyPublicationEvent,
    StudyPurchase,
)

# Reserve room for one maximum-sized final update per unresolved envelope.
# IDs, six digests, counts and producer_version are bounded in the typed schema.
MAX_FINAL_RECORD_BYTES = 4096

FINAL = frozenset(("completed", "failed", "rejected"))
SELECTOR_ARTIFACTS: dict[str, ArtifactKind] = {
    "random": "selector_random",
    "uniform_disagreement": "selector_uniform_disagreement",
    "posterior_disagreement": "selector_posterior_disagreement",
}


class StudyLedgerError(ValueError):
    """Bounded diagnostic codes; never include scientific or parser payloads."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass
class _Attempt:
    reservation: StudyAttemptReservation
    state: str = "reserved"
    cpu_ns: int | None = None
    wall_ns: int | None = None
    artifact_bytes: int | None = None
    update: StudyAttemptUpdate | None = None

    def charge(self) -> tuple[int, int]:
        if self.state in FINAL:
            assert self.cpu_ns is not None and self.artifact_bytes is not None
            return self.cpu_ns, self.artifact_bytes
        return (
            max(self.reservation.cpu_reservation_ns, self.cpu_ns or 0),
            max(self.reservation.artifact_reservation_bytes, self.artifact_bytes or 0),
        )


@dataclass
class _State:
    plan: NativeAccountingPlan
    attempts: dict[str, _Attempt] = field(default_factory=dict)
    purchases: dict[str, dict[str, StudyPurchase]] = field(default_factory=dict)
    outcomes: dict[str, StudyCellOutcome] = field(default_factory=dict)
    manifest: NativeStudyManifest | None = None
    cpu_ns: int = 0
    artifact_bytes: int = 0
    unresolved: int = 0

    def over_limit(self) -> bool:
        return (
            self.cpu_ns > self.plan.cpu_limit_ns
            or self.artifact_bytes > self.plan.artifact_limit_bytes
        )

    def slots(self) -> int:
        return sum(len(rows) for rows in self.purchases.values())


def _same(a: Message, b: Message) -> bool:
    return message_sha256(a) == message_sha256(b)


def _cell(state: _State, cell_id: str) -> None:
    if state.manifest is None or cell_id not in {cell.cell_id for cell in state.manifest.cells}:
        raise StudyLedgerError("unknown_cell")


def _comparison_config(state: _State, value: StudyAttemptReservation) -> None:
    if value.cell_id is None:
        return
    assert state.manifest is not None
    cell = next(cell for cell in state.manifest.cells if cell.cell_id == value.cell_id)
    kind: ArtifactKind
    if value.operation == "candidate_production":
        kind = "candidate_config"
    elif value.operation in {"prediction", "forward"}:
        kind = "prediction_config"
    elif value.operation in {"selection", "ranking"}:
        kind = SELECTOR_ARTIFACTS[cell.selector]
    elif value.operation == "scoring":
        kind = "scoring_policy"
    elif value.operation == "likelihood":
        kind = "likelihood"
    elif value.operation == "purchase" and value.purchase is not None:
        kind = "calibration" if value.purchase.calibration else "menu"
    elif value.operation == "preparation":
        # Menu preparation and actual evaluation preparation have distinct inputs.
        # The complete scoring adapter additionally requires the latter producer.
        if value.config_sha256 not in {
            state.manifest.artifact("menu").sha256,
            state.manifest.artifact("scoring_policy").sha256,
        }:
            raise StudyLedgerError("configuration_mismatch")
        return
    elif value.operation == "classical_diagnostic":
        if not any(a.kind == "classical_diagnostic_config" for a in state.manifest.artifacts):
            raise StudyLedgerError("diagnostic_configuration_missing")
        kind = "classical_diagnostic_config"
    else:
        raise StudyLedgerError("invalid_comparison_operation")
    if value.config_sha256 != state.manifest.artifact(kind).sha256:
        raise StudyLedgerError("configuration_mismatch")


def _reserve(state: _State, value: StudyAttemptReservation) -> None:
    if value.attempt_id in state.attempts:
        raise StudyLedgerError("attempt_reused")
    if state.over_limit():
        raise StudyLedgerError("budget_exhausted")
    if (
        state.cpu_ns + value.cpu_reservation_ns > state.plan.cpu_limit_ns
        or state.artifact_bytes + value.artifact_reservation_bytes > state.plan.artifact_limit_bytes
    ):
        raise StudyLedgerError("budget_exhausted")
    if value.cell_id is not None:
        _cell(state, value.cell_id)
        if value.cell_id in state.outcomes:
            raise StudyLedgerError("cell_sealed")
        _comparison_config(state, value)
    if value.retry_of is not None:
        prior = state.attempts.get(value.retry_of)
        if prior is None:
            raise StudyLedgerError("retry_missing")
        before = prior.reservation.model_dump(
            mode="json",
            exclude={"attempt_id", "retry_of", "cpu_reservation_ns", "artifact_reservation_bytes"},
        )
        after = value.model_dump(
            mode="json",
            exclude={"attempt_id", "retry_of", "cpu_reservation_ns", "artifact_reservation_bytes"},
        )
        if canonical_json(before) != canonical_json(after):
            raise StudyLedgerError("retry_mismatch")
    if value.purchase is not None:
        assert value.cell_id is not None
        rows = state.purchases.setdefault(value.cell_id, {})
        old = rows.get(value.purchase.operation_id)
        if old is not None:
            if value.retry_of is None or not _same(old, value.purchase):
                raise StudyLedgerError("purchase_conflict")
        else:
            if value.retry_of is not None or value.purchase.ordinal != len(rows):
                raise StudyLedgerError("purchase_sequence")
            if len(rows) >= 12 or state.slots() >= state.plan.purchase_limit:
                raise StudyLedgerError("purchase_limit")
            # Even an interrupted Journal.reserve leaves this intent charged.
            rows[value.purchase.operation_id] = value.purchase
    attempt = _Attempt(value)
    state.attempts[value.attempt_id] = attempt
    state.unresolved += 1
    cpu, artifacts = attempt.charge()
    state.cpu_ns += cpu
    state.artifact_bytes += artifacts


def _update(state: _State, value: StudyAttemptUpdate) -> None:
    attempt = state.attempts.get(value.attempt_id)
    if attempt is None:
        raise StudyLedgerError("attempt_missing")
    if attempt.state in FINAL:
        raise StudyLedgerError("attempt_final")
    if attempt.state == "unknown" and value.state == "running":
        raise StudyLedgerError("unknown_work_cannot_resume")
    if value.state == "running" and value.facts is not None:
        raise StudyLedgerError("running_facts")
    if value.facts is not None:
        r = attempt.reservation
        if (value.facts.operation, value.facts.config_sha256, value.facts.input_sha256) != (
            r.operation,
            r.config_sha256,
            r.input_sha256,
        ):
            raise StudyLedgerError("facts_mismatch")
    if attempt.update is not None and attempt.update.facts is not None:
        if value.facts is None or not _same(attempt.update.facts, value.facts):
            raise StudyLedgerError("facts_changed")
    old_cpu, old_artifacts = attempt.charge()
    for key in ("cpu_ns", "wall_ns", "artifact_bytes"):
        before = getattr(attempt, key)
        after = getattr(value, key)
        if before is not None and after is not None and after < before:
            raise StudyLedgerError("measurement_regressed")
        if after is not None:
            setattr(attempt, key, after)
    if value.state in FINAL:
        state.unresolved -= 1
    attempt.state = value.state
    attempt.update = value
    cpu, artifacts = attempt.charge()
    state.cpu_ns += cpu - old_cpu
    state.artifact_bytes += artifacts - old_artifacts


def _freeze(state: _State, value: StudyManifestFreeze) -> None:
    if state.manifest is not None:
        raise StudyLedgerError("manifest_already_frozen")
    if value.manifest.accounting_plan_sha256 != message_sha256(state.plan):
        raise StudyLedgerError("accounting_plan_mismatch")
    state.manifest = value.manifest


def _outcome(state: _State, value: StudyCellOutcome) -> None:
    _cell(state, value.cell_id)
    assert state.manifest is not None
    if value.cell_id in state.outcomes:
        raise StudyLedgerError("cell_sealed")
    cell = next(cell for cell in state.manifest.cells if cell.cell_id == value.cell_id)
    selector_kind = SELECTOR_ARTIFACTS[cell.selector]
    if (
        value.journal_id != cell.journal_id
        or value.scoring_policy_sha256 != state.manifest.artifact("scoring_policy").sha256
        or value.selector_config_sha256 != state.manifest.artifact(selector_kind).sha256
    ):
        raise StudyLedgerError("outcome_mismatch")
    if value.status == "complete":
        attempts = [a for a in state.attempts.values() if a.reservation.cell_id == value.cell_id]
        if len(state.purchases.get(value.cell_id, {})) != 12 or any(
            a.state not in FINAL for a in attempts
        ):
            raise StudyLedgerError("incomplete_cell")
    state.outcomes[value.cell_id] = value


def _scan(ledger: NativeStudyLedger) -> _State:
    state = _State(ledger.plan)
    # Chain validation is also performed here for direct typed/internal callers.
    prior = message_sha256(ledger.plan)
    ids: set[str] = set()
    _, prefix_bytes = bounded_canonical(NativeStudyLedger(plan=ledger.plan), MAX_STUDY_JSON_BYTES)
    for index, record in enumerate(ledger.records):
        if record.sequence != index or record.previous_sha256 != prior or record.event_id in ids:
            raise StudyLedgerError("ledger_chain")
        ids.add(record.event_id)
        prior, record_bytes = bounded_canonical(record, MAX_STUDY_JSON_BYTES)
        prefix_bytes += record_bytes + int(index > 0)
        value = record.event
        if isinstance(value, StudyAttemptReservation):
            _reserve(state, value)
        elif isinstance(value, StudyAttemptUpdate):
            _update(state, value)
        elif isinstance(value, StudyManifestFreeze):
            _freeze(state, value)
        elif isinstance(value, StudyPublicationEvent):
            _outcome(state, value.outcome)
        else:
            _outcome(state, value)
        if (
            state.unresolved > MAX_LEDGER_RECORDS - index - 1
            or prefix_bytes + state.unresolved * MAX_FINAL_RECORD_BYTES > MAX_STUDY_JSON_BYTES
        ):
            raise StudyLedgerError("ledger_capacity")
    return state


def _accounting_capacity(ledger: NativeStudyLedger, state: _State) -> None:
    _, size = bounded_canonical(ledger, MAX_STUDY_JSON_BYTES)
    unresolved = state.unresolved
    if size + unresolved * MAX_FINAL_RECORD_BYTES > MAX_STUDY_JSON_BYTES:
        raise StudyLedgerError("ledger_capacity")


def read_study_ledger(raw: bytes) -> NativeStudyLedger:
    ledger = parse_bounded_json(
        raw, NativeStudyLedger, max_bytes=MAX_STUDY_JSON_BYTES, max_depth=32, max_nodes=1_000_000
    )
    state = _scan(ledger)
    _accounting_capacity(ledger, state)
    return ledger


def _append(
    ledger: NativeStudyLedger, event_id: str, event: StudyEvent, expected_revision: int
) -> NativeStudyLedger:
    _scan(ledger)
    if type(expected_revision) is not int or expected_revision < 0:
        raise StudyLedgerError("invalid_revision")
    for record in ledger.records:
        if record.event_id == event_id:
            if not _same(record.event, event):
                raise StudyLedgerError("event_conflict")
            return ledger
    if type(expected_revision) is not int or expected_revision != len(ledger.records):
        raise StudyLedgerError("stale_revision")
    if len(ledger.records) >= MAX_LEDGER_RECORDS:
        raise StudyLedgerError("ledger_limit")
    previous = message_sha256(ledger.records[-1]) if ledger.records else message_sha256(ledger.plan)
    record = StudyLedgerRecord(
        event_id=event_id, sequence=len(ledger.records), previous_sha256=previous, event=event
    )
    result = NativeStudyLedger(plan=ledger.plan, records=(*ledger.records, record))
    state = _scan(result)
    _accounting_capacity(result, state)
    return result


def append_study_attempt(
    ledger: NativeStudyLedger,
    *,
    event_id: str,
    event: StudyAttemptReservation | StudyAttemptUpdate,
    expected_revision: int,
) -> NativeStudyLedger:
    """Propose one reservation/measurement append; caller atomically persists by CAS."""
    if not isinstance(event, StudyAttemptReservation | StudyAttemptUpdate):
        raise StudyLedgerError("invalid_attempt_event")
    return _append(ledger, event_id, event, expected_revision)


class _ArtifactJSON(Message):
    value: dict[str, JsonValue]


def freeze_native_study(
    ledger: NativeStudyLedger,
    *,
    event_id: str,
    manifest: NativeStudyManifest,
    expected_revision: int,
    expected_purpose: Literal["synthetic_validation", "native_comparison"],
    source_commit: str,
    uv_lock_bytes: bytes,
    engine_fingerprint: str,
    artifacts: dict[str, bytes],
) -> NativeStudyLedger:
    """Bind supplied actual canonical materials; gate/checkout authenticity is external.

    The current runner supplies its independently verified checkout identity. No
    execution or network access occurs here. Later gate-specific type/physics
    validation is not replaced by generic canonical JSON validation.
    """
    _scan(ledger)
    if ledger.plan.purpose != expected_purpose:
        raise StudyLedgerError("purpose_mismatch")
    if not isinstance(uv_lock_bytes, bytes) or not 1 <= len(uv_lock_bytes) <= MAX_STUDY_JSON_BYTES:
        raise StudyLedgerError("lock_limit")
    if (
        source_commit != manifest.source_commit
        or hashlib.sha256(uv_lock_bytes).hexdigest() != manifest.uv_lock_sha256
        or engine_fingerprint != manifest.engine_fingerprint
    ):
        raise StudyLedgerError("runtime_identity_mismatch")
    if (
        set(artifacts) != {ref.kind for ref in manifest.artifacts}
        or sum(len(raw) for raw in artifacts.values()) > MAX_STUDY_JSON_BYTES
    ):
        raise StudyLedgerError("artifact_set_mismatch")
    for ref in manifest.artifacts:
        raw = artifacts[ref.kind]
        if len(raw) != ref.byte_count or hashlib.sha256(raw).hexdigest() != ref.sha256:
            raise StudyLedgerError("artifact_identity_mismatch")
        wrapped = parse_bounded_json(
            b'{"value":' + raw + b"}",
            _ArtifactJSON,
            max_bytes=MAX_STUDY_JSON_BYTES + 10,
            max_depth=33,
            max_nodes=1_000_000,
        )
        if canonical_json(wrapped.value).encode() != raw:
            raise StudyLedgerError("artifact_not_canonical")
    catalog = parse_bounded_json(
        artifacts["world_catalog"],
        NativeWorldCatalog,
        max_bytes=MAX_STUDY_JSON_BYTES,
        max_depth=32,
        max_nodes=1_000_000,
    )
    if tuple(entry.world_id for entry in catalog.worlds) != manifest.world_ids:
        raise StudyLedgerError("world_catalog_mismatch")
    return _append(ledger, event_id, StudyManifestFreeze(manifest=manifest), expected_revision)


def summarize_study(ledger: NativeStudyLedger) -> NativeStudySummary:
    """Derive every frozen cell, never only successful or assessed cells."""
    state = _scan(ledger)
    budget = NativeBudgetView(
        purchased_slots=state.slots(),
        remaining_slots=max(0, state.plan.purchase_limit - state.slots()),
        charged_cpu_ns=state.cpu_ns,
        remaining_cpu_ns=max(0, state.plan.cpu_limit_ns - state.cpu_ns),
        charged_artifact_bytes=state.artifact_bytes,
        remaining_artifact_bytes=max(0, state.plan.artifact_limit_bytes - state.artifact_bytes),
        unresolved_attempts=state.unresolved,
        over_limit=state.over_limit(),
    )
    cells = []
    if state.manifest is not None:
        for cell in state.manifest.cells:
            attempts = [a for a in state.attempts.values() if a.reservation.cell_id == cell.cell_id]
            outcome = state.outcomes.get(cell.cell_id)
            status = (
                outcome.status
                if outcome is not None
                else ("in_progress" if attempts else "unstarted")
            )
            cells.append(
                NativeCellSummary(
                    cell_id=cell.cell_id,
                    status=status,
                    purchased_slots=len(state.purchases.get(cell.cell_id, {})),
                    unresolved_attempts=sum(a.state not in FINAL for a in attempts),
                    outcome=outcome,
                )
            )
    return NativeStudySummary(
        study_id=state.plan.study_id,
        accounting_plan_sha256=message_sha256(state.plan),
        ledger_sha256=message_sha256(ledger),
        manifest_sha256=message_sha256(state.manifest) if state.manifest is not None else None,
        budget=budget,
        cells=tuple(cells),
    )


def study_manifest(ledger: NativeStudyLedger) -> NativeStudyManifest:
    """Return the one retained actual freeze only after complete ledger validation."""
    state = _scan(ledger)
    if state.manifest is None:
        raise StudyLedgerError("manifest_missing")
    return state.manifest


@dataclass(frozen=True)
class StudyAttemptSnapshot:
    """Validated retained facts and accumulated measurements, not execution proof."""

    reservation: StudyAttemptReservation
    state: Literal["reserved", "running", "unknown", "completed", "failed", "rejected"]
    latest_update: StudyAttemptUpdate | None
    cpu_ns: int | None
    wall_ns: int | None
    artifact_bytes: int | None


def study_cell_attempts(
    ledger: NativeStudyLedger, cell_id: str
) -> tuple[StudyAttemptSnapshot, ...]:
    """Project the complete validated cell history, including unresolved retries."""
    state = _scan(ledger)
    _cell(state, cell_id)
    # Derive the finite state from its typed latest update rather than a cast.
    return tuple(
        StudyAttemptSnapshot(
            attempt.reservation,
            "reserved" if attempt.update is None else attempt.update.state,
            attempt.update,
            attempt.cpu_ns,
            attempt.wall_ns,
            attempt.artifact_bytes,
        )
        for attempt in state.attempts.values()
        if attempt.reservation.cell_id == cell_id
    )


def study_purchase_intents(ledger: NativeStudyLedger, cell_id: str) -> tuple[StudyPurchase, ...]:
    """All charged reservation intents, including interrupted-before-Journal writes."""
    state = _scan(ledger)
    _cell(state, cell_id)
    return tuple(state.purchases.get(cell_id, {}).values())


def seal_unfinished_cell(
    ledger: NativeStudyLedger,
    *,
    event_id: str,
    cell_id: str,
    status: Literal["failed", "incomplete", "cap_limited"],
    reason: Literal["execution_failure", "interrupted", "resource_limit"],
    expected_revision: int,
) -> NativeStudyLedger:
    """Retain a stop without inventing a model, protocol or scientific report."""
    manifest = study_manifest(ledger)
    cell = next((cell for cell in manifest.cells if cell.cell_id == cell_id), None)
    if cell is None:
        raise StudyLedgerError("unknown_cell")
    if (status, reason) not in {
        ("failed", "execution_failure"),
        ("incomplete", "interrupted"),
        ("cap_limited", "resource_limit"),
    }:
        raise StudyLedgerError("stop_reason_mismatch")
    outcome = StudyCellOutcome(
        cell_id=cell_id,
        status=status,
        reason=reason,
        journal_id=cell.journal_id,
        observation_sha256=None,
        model_sha256=None,
        report_sha256=None,
        scoring_policy_sha256=manifest.artifact("scoring_policy").sha256,
        protocol_sha256=None,
        selector_config_sha256=manifest.artifact(SELECTOR_ARTIFACTS[cell.selector]).sha256,
    )
    return _append(ledger, event_id, outcome, expected_revision)


def append_study_publication(
    ledger: NativeStudyLedger,
    *,
    event_id: str,
    event: StudyPublicationEvent,
    expected_revision: int,
) -> NativeStudyLedger:
    """Low-level private CAS proposal; the actual-material adapter supplies evidence."""
    if not isinstance(event, StudyPublicationEvent):
        raise StudyLedgerError("invalid_publication_event")
    return _append(ledger, event_id, event, expected_revision)
