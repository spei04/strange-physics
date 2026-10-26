"""Exact frozen action, contiguous history and record/facts joins for purchases."""

from __future__ import annotations

from dataclasses import dataclass

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.contracts import ExperimentRecord
from strange_physics.publication_store import raw
from strange_physics.purchase_execution_contracts import (
    PURCHASE_CONTEXT_BYTES,
    NativePurchaseActions,
    NativePurchaseAttemptContext,
    NativePurchaseInput,
    NativePurchasePrefix,
    NativePurchaseRequest,
    NativePurchaseResult,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import NativeStudyLedger, NativeWorkFacts, NativeWorldCatalog
from strange_physics.study_execution_binding import validate_frozen_materials
from strange_physics.study_execution_contracts import NativeFreezeInput
from strange_physics.study_journal import StudyJournalSnapshot
from strange_physics.study_ledger import StudyLedgerError, study_manifest
from strange_physics.worlds import WorldDefinition

VERSION = "strange-physics.measured-purchase.v1"


@dataclass(frozen=True)
class BoundPurchase:
    world: WorldDefinition
    journal_id: str
    config_sha256: str
    catalog: NativeWorldCatalog


def bind_purchase_material(
    actual: NativePurchaseInput, freeze: NativeFreezeInput, ledger: NativeStudyLedger
) -> BoundPurchase:
    validate_frozen_materials(freeze)
    if raw(study_manifest(ledger)) != raw(freeze.manifest):
        raise StudyLedgerError("purchase_freeze_identity")
    manifest = freeze.manifest
    cells = [cell for cell in manifest.cells if cell.cell_id == actual.cell_id]
    if len(cells) != 1:
        raise StudyLedgerError("purchase_cell_identity")
    catalog = parse_bounded_json(
        freeze.artifacts["world_catalog"].encode(),
        NativeWorldCatalog,
        max_bytes=8 * 1024**2,
        max_depth=32,
        max_nodes=1_000_000,
    )
    world = next(
        entry.definition for entry in catalog.worlds if entry.world_id == cells[0].world_id
    )
    role = "calibration" if actual.purchase.calibration else "menu"
    actions = parse_bounded_json(
        freeze.artifacts[role].encode(),
        NativePurchaseActions,
        max_bytes=64 * 1024,
        max_depth=32,
        max_nodes=100_000,
    )
    if actions.role != role:
        raise StudyLedgerError("purchase_action_role")
    identities = tuple(message_sha256(action) for action in actions.actions)
    expected = message_sha256(actual.experiment)
    if (
        role == "calibration"
        and identities[actual.purchase.ordinal] != expected
        or role == "menu"
        and expected not in identities
    ):
        raise StudyLedgerError("purchase_action_identity")
    world.space.validate_experiment(actual.experiment)
    return BoundPurchase(world, cells[0].journal_id, manifest.artifact(role).sha256, catalog)


def validate_purchase_prefix(actual: NativePurchaseInput, prefix: NativePurchasePrefix) -> None:
    if len(prefix.records) != actual.purchase.ordinal:
        raise StudyLedgerError("purchase_prefix_length")
    ids: set[str] = set()
    for index, record in enumerate(prefix.records):
        if record.index != index or record.operation_id in ids:
            raise StudyLedgerError("purchase_prefix_identity")
        ids.add(record.operation_id)
    if actual.purchase.operation_id in ids:
        raise StudyLedgerError("purchase_operation_reused")


def purchase_facts(
    actual: NativePurchaseInput,
    record: ExperimentRecord,
    context: NativePurchaseAttemptContext,
    *,
    config_sha256: str,
    reconciliation: bool,
) -> NativeWorkFacts:
    bounded_canonical(context, PURCHASE_CONTEXT_BYTES)
    if (
        record.index != actual.purchase.ordinal
        or record.operation_id != actual.purchase.operation_id
        or message_sha256(record.experiment) != actual.purchase.experiment_sha256
    ):
        raise StudyLedgerError("purchase_record_identity")
    failed = record.status == "failed" and not reconciliation
    return NativeWorkFacts(
        attempt_id=context.attempt_id,
        operation="accounting" if reconciliation else "purchase",
        producer_version=VERSION,
        config_sha256=config_sha256,
        input_sha256=message_sha256(actual),
        observation_sha256=message_sha256(record),
        model_sha256=None,
        output_sha256=message_sha256(record),
        unit="record",
        requested_count=1,
        completed_count=0 if failed else 1,
        failed_count=1 if failed else 0,
        not_assessed_count=0,
        outcome="failed" if failed else "completed",
    )


def validate_purchase_result(
    actual: NativePurchaseInput, result: NativePurchaseResult, request: NativePurchaseRequest
) -> None:
    if (
        raw(actual.purchase) != raw(request.purchase)
        or actual.cell_id != request.cell_id
        or result.kind != request.purpose
        or result.context.attempt_id != request.attempt_id
        or (result.kind == "execution" and result.context.row_state == "terminal")
        or (result.kind == "reconciliation" and result.context.row_state != "terminal")
    ):
        raise StudyLedgerError("purchase_result_context")
    expected = purchase_facts(
        actual,
        result.record,
        result.context,
        config_sha256=request.config_sha256,
        reconciliation=result.kind == "reconciliation",
    )
    if message_sha256(expected) != message_sha256(result.facts):
        raise StudyLedgerError("purchase_result_facts")


def bind_purchase_capture(
    actual: NativePurchaseInput,
    result: NativePurchaseResult,
    prefix: NativePurchasePrefix,
    snapshot: StudyJournalSnapshot,
) -> None:
    validate_purchase_prefix(actual, prefix)
    if (
        snapshot.cell_id != actual.cell_id
        or snapshot.journal_bytes_sha256 != result.journal.sha256
        or len(snapshot.reservations) != actual.purchase.ordinal + 1
        or result.context.original_prefix_sha256 != message_sha256(prefix)
    ):
        raise StudyLedgerError("purchase_capture_identity")
    records = tuple(row.record for row in snapshot.reservations)
    if any(record is None for record in records):
        raise StudyLedgerError("purchase_capture_pending")
    for expected, observed in zip((*prefix.records, result.record), records, strict=True):
        if observed is None or message_sha256(expected) != message_sha256(observed):
            raise StudyLedgerError("purchase_capture_prefix")
