"""Pure purchase wire/action conformance; no simulation, Journal or installed-build claim."""

from __future__ import annotations

import json
from typing import Any

import pytest
from test_study_ledger import LOCK, append, empty, materials, reserve, update

from strange_physics.contracts import Experiment, ExperimentRecord, ParticleInitial
from strange_physics.publication_store import digest, raw
from strange_physics.purchase_execution_binding import (
    bind_purchase_capture,
    bind_purchase_material,
    purchase_facts,
    validate_purchase_result,
)
from strange_physics.purchase_execution_contracts import (
    NativePurchaseActions,
    NativePurchaseAttemptContext,
    NativePurchaseInput,
    NativePurchaseJournalIdentity,
    NativePurchasePrefix,
    NativePurchaseReconciliationReceipt,
    NativePurchaseReference,
    NativePurchaseRequest,
    NativePurchaseResult,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    NativeStudyLedger,
    NativeStudyManifest,
    NativeWorldCatalog,
)
from strange_physics.study_execution_contracts import NativeFreezeInput
from strange_physics.study_journal import StudyJournalReservation, StudyJournalSnapshot
from strange_physics.study_ledger import StudyLedgerError, freeze_native_study


def fixture(ordinal: int = 0) -> tuple[NativePurchaseInput, NativeFreezeInput, NativeStudyLedger]:
    manifest, artifacts = materials()
    catalog = NativeWorldCatalog.model_validate_json(artifacts["world_catalog"])
    pid = catalog.worlds[0].definition.space.structure.particle_ids[0]
    actions = tuple(
        Experiment(particles=(ParticleInitial(id=pid, position=(float(i) / 8, 0.0)),))
        for i in range(4)
    )
    for role in ("calibration", "menu"):
        artifacts[role] = raw(
            NativePurchaseActions.model_validate({"role": role, "actions": actions})
        )
    data = manifest.model_dump(mode="json")
    for ref in data["artifacts"]:
        value = artifacts[ref["kind"]]
        ref.update(sha256=digest(value), byte_count=len(value))
    manifest = NativeStudyManifest.model_validate_json(json.dumps(data))
    frozen = NativeFreezeInput.model_validate_json(
        json.dumps(
            {
                "manifest": manifest.model_dump(mode="json"),
                "artifacts": {k: v.decode() for k, v in artifacts.items()},
            }
        )
    )
    ledger = freeze_native_study(
        empty(),
        event_id="freeze",
        manifest=manifest,
        expected_revision=0,
        expected_purpose="synthetic_validation",
        source_commit=manifest.source_commit,
        uv_lock_bytes=LOCK,
        engine_fingerprint=manifest.engine_fingerprint,
        artifacts=artifacts,
    )
    action = actions[ordinal] if ordinal < 4 else actions[0]
    actual = NativePurchaseInput.model_validate(
        {
            "freeze_logical_id": "freeze",
            "freeze_receipt_sha256": "a" * 64,
            "cell_id": manifest.cells[0].cell_id,
            "purchase": {
                "operation_id": f"op-{ordinal}",
                "ordinal": ordinal,
                "experiment_sha256": message_sha256(action),
                "calibration": ordinal < 4,
            },
            "experiment": action,
            "journal_path": "/private/run.sqlite",
            "predecessor": None
            if ordinal == 0
            else NativePurchaseReference(
                logical_id=f"purchase-{ordinal - 1}", receipt_sha256="b" * 64, kind="execution"
            ),
            "initial_journal": None
            if ordinal == 0
            else NativePurchaseJournalIdentity(sha256="c" * 64, byte_count=24576),
        }
    )
    return actual, frozen, ledger


def request(actual: NativePurchaseInput, config: str, **changes: Any) -> NativePurchaseRequest:
    data = dict(
        purchase=actual.purchase,
        mode="execute",
        logical_id="purchase",
        purchase_logical_id="purchase",
        attempt_id="attempt",
        retry_of=None,
        cell_id=actual.cell_id,
        ticket=1,
        expected_revision=1,
        expected_head_sha256="a" * 64,
        input_path="/private/input.json",
        input_raw_sha256=digest(raw(actual)),
        input_bytes=len(raw(actual)),
        input_sha256=message_sha256(actual),
        config_sha256=config,
        cpu_reservation_ns=20_000_000_000,
        artifact_reservation_bytes=4 * 1024**2,
        output_limit_bytes=128 * 1024,
        wall_limit_ns=60_000_000_000,
    )
    data.update(changes)
    return NativePurchaseRequest.model_validate(data)


@pytest.mark.parametrize("ordinal", [0, 1, 3, 4, 11])
def test_actual_frozen_role_and_order(ordinal: int) -> None:
    actual, frozen, ledger = fixture(ordinal)
    bound = bind_purchase_material(actual, frozen, ledger)
    role = "calibration" if ordinal < 4 else "menu"
    assert bound.config_sha256 == frozen.manifest.artifact(role).sha256
    assert bound.journal_id == frozen.manifest.cells[0].journal_id
    action = actual.experiment.model_copy(
        update={
            "particles": (
                actual.experiment.particles[0].model_copy(update={"position": (1.0, 0.0)}),
            )
        }
    )
    changed = NativePurchaseInput.model_validate(
        {
            **actual.model_dump(),
            "experiment": action,
            "purchase": {
                **actual.purchase.model_dump(),
                "experiment_sha256": message_sha256(action),
            },
        }
    )
    with pytest.raises(StudyLedgerError, match="purchase_action_identity"):
        bind_purchase_material(changed, frozen, ledger)


def test_signed_zero_is_canonical_membership_not_python_equality() -> None:
    actual, frozen, ledger = fixture()
    particle = actual.experiment.particles[0]
    action = Experiment(particles=(particle.model_copy(update={"position": (-0.0, 0.0)}),))
    assert action == actual.experiment and message_sha256(action) != message_sha256(
        actual.experiment
    )
    changed = NativePurchaseInput.model_validate(
        {
            **actual.model_dump(),
            "experiment": action,
            "purchase": {
                **actual.purchase.model_dump(),
                "experiment_sha256": message_sha256(action),
            },
        }
    )
    with pytest.raises(StudyLedgerError, match="purchase_action_identity"):
        bind_purchase_material(changed, frozen, ledger)


def test_receipt_reference_allows_reconciliation_without_original_receipt() -> None:
    actual, _, _ = fixture(1)
    assert actual.predecessor is not None
    ref = NativePurchaseReference.model_validate(
        {**actual.predecessor.model_dump(), "kind": "reconciliation"}
    )
    assert (
        NativePurchaseInput.model_validate({**actual.model_dump(), "predecessor": ref}).predecessor
        == ref
    )
    valid = NativePurchaseReconciliationReceipt(
        logical_id="reconciliation",
        purchase=actual.purchase,
        original_attempt_id="paid",
        request_sha256="a" * 64,
        original_revision=4,
        original_head_sha256="b" * 64,
        original_ledger_sha256="c" * 64,
        input_raw_sha256="d" * 64,
        result_raw_sha256="e" * 64,
        source_commit="f" * 40,
        installation_sha256="a" * 64,
        purchase_logical_id="purchase",
        unresolved_attempt_id="old",
        context_sha256="b" * 64,
        journal=NativePurchaseJournalIdentity(sha256="c" * 64, byte_count=24576),
    )
    for field, foreign in (
        ("schema_version", "strange-physics.purchase-receipt.v1"),
        ("kind", "execution"),
    ):
        with pytest.raises(ValueError):
            NativePurchaseReconciliationReceipt.model_validate(
                {**valid.model_dump(), field: foreign}
            )


def test_retry_keeps_input_and_slot_while_context_changes() -> None:
    actual, frozen, ledger = fixture()
    bound = bind_purchase_material(actual, frozen, ledger)
    r = reserve(
        "original",
        phase="comparison",
        cell_id=actual.cell_id,
        operation="purchase",
        config_sha256=bound.config_sha256,
        input_sha256=message_sha256(actual),
        purchase=actual.purchase.model_dump(),
    )
    ledger = append(append(ledger, r), update(r, "unknown", facts=None, cpu_ns=0))
    retry = type(r).model_validate(
        {**r.model_dump(), "attempt_id": "retry", "retry_of": "original"}
    )
    assert len(append(ledger, retry).records) == len(ledger.records) + 1
    with pytest.raises(StudyLedgerError, match="retry"):
        append(ledger, type(r).model_validate({**retry.model_dump(), "input_sha256": "f" * 64}))
    with pytest.raises(ValueError, match="distinct paid"):
        request(
            actual, bound.config_sha256, purpose="reconciliation", reconcile_attempt_id="original"
        )


@pytest.mark.parametrize("reconciliation", [False, True])
def test_record_facts_and_whole_capture_binding(reconciliation: bool) -> None:
    actual, frozen, ledger = fixture()
    bound = bind_purchase_material(actual, frozen, ledger)
    prefix = NativePurchasePrefix(records=())
    context = NativePurchaseAttemptContext(
        attempt_id="attempt",
        observed_journal=None
        if not reconciliation
        else NativePurchaseJournalIdentity(sha256="c" * 64, byte_count=24576),
        original_prefix_sha256=message_sha256(prefix),
        row_state="terminal" if reconciliation else "missing",
    )
    record = ExperimentRecord(
        operation_id="op-0",
        index=0,
        experiment=actual.experiment,
        status="failed",
        error="simulation_failed",
    )
    req = request(
        actual,
        bound.config_sha256,
        **(
            {
                "purpose": "reconciliation",
                "mode": "recover",
                "logical_id": "reconciled",
                "reconcile_attempt_id": "old",
            }
            if reconciliation
            else {}
        ),
    )
    result = NativePurchaseResult(
        kind=req.purpose,
        record=record,
        context=context,
        journal=NativePurchaseJournalIdentity(sha256="d" * 64, byte_count=24576),
        facts=purchase_facts(
            actual,
            record,
            context,
            config_sha256=bound.config_sha256,
            reconciliation=reconciliation,
        ),
    )
    validate_purchase_result(actual, result, req)
    assert result.facts.operation == ("accounting" if reconciliation else "purchase")
    assert result.facts.outcome == ("completed" if reconciliation else "failed")
    snapshot = StudyJournalSnapshot(
        actual.cell_id,
        frozen.manifest.cells[0].world_id,
        bound.journal_id,
        "d" * 64,
        frozen.manifest.engine_fingerprint,
        bound.world.space,
        (StudyJournalReservation("op-0", 0, actual.experiment, record),),
    )
    bind_purchase_capture(actual, result, prefix, snapshot)
    from dataclasses import replace

    with pytest.raises(StudyLedgerError, match="purchase_capture_identity"):
        bind_purchase_capture(
            actual, result, prefix, replace(snapshot, journal_bytes_sha256="e" * 64)
        )


def test_128_member_menu_and_one_over_with_unchanged_raw_bound() -> None:
    actual, _, _ = fixture()
    pid = actual.experiment.particles[0].id
    actions = tuple(
        Experiment(particles=(ParticleInitial(id=pid, position=(i / 128, 0.0)),))
        for i in range(129)
    )
    accepted = NativePurchaseActions(role="menu", actions=actions[:128])
    assert len(raw(accepted)) < 64 * 1024
    with pytest.raises(ValueError):
        NativePurchaseActions(role="menu", actions=actions)


@pytest.mark.parametrize("state", ["missing", "pending", "terminal"])
def test_observed_row_requires_actual_journal_identity(state: str) -> None:
    values = dict(
        attempt_id="paid",
        row_state=state,
        original_prefix_sha256="a" * 64,
        observed_journal=NativePurchaseJournalIdentity(sha256="b" * 64, byte_count=24576),
    )
    NativePurchaseAttemptContext.model_validate(values)
    values["observed_journal"] = None
    if state == "missing":
        NativePurchaseAttemptContext.model_validate(values)
    else:
        with pytest.raises(ValueError, match="requires an observed Journal"):
            NativePurchaseAttemptContext.model_validate(values)
