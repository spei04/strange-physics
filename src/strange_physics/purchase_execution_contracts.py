"""Closed private purchase messages; no selector or original-cost authority is inferred."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.candidate_execution_contracts import (
    PrivatePath,
    _ExecutionReceipt,
    _ExecutionRequest,
)
from strange_physics.contracts import Experiment, ExperimentRecord, Identifier, Message
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.study_contracts import NativeWorkFacts, StudyPurchase

PURCHASE_INPUT_BYTES = 64 * 1024
PURCHASE_RESULT_BYTES = 128 * 1024
PURCHASE_CONTEXT_BYTES = 8192
PURCHASE_COPY_BYTES = 2 * 1024**2
PURCHASE_CONTROL_BYTES = 6 * 1024**2
PURCHASE_CONTROL_NS = 7_000_000_000
PURCHASE_HOLDER_NS = 2_000_000_000


class NativePurchaseActions(Message):
    """Frozen calibration order or menu membership; never an acquisition policy."""

    schema_version: Literal["strange-physics.purchase-actions.v1"] = (
        "strange-physics.purchase-actions.v1"
    )
    role: Literal["calibration", "menu"]
    actions: Annotated[tuple[Experiment, ...], Field(min_length=1, max_length=128)]

    @model_validator(mode="after")
    def action_scope(self) -> Self:
        if self.role == "calibration" and len(self.actions) != 4:
            raise ValueError("Calibration requires exactly four ordered actions")
        if self.role == "menu" and len({message_sha256(a) for a in self.actions}) != len(
            self.actions
        ):
            raise ValueError("Menu actions must have distinct canonical identities")
        return self


class NativePurchaseReference(Message):
    logical_id: Identifier
    receipt_sha256: Digest
    kind: Literal["execution", "reconciliation"]


class NativePurchaseJournalIdentity(Message):
    sha256: Digest
    byte_count: Annotated[int, Field(ge=100, le=128 * 1024)]


class NativePurchaseInput(Message):
    """Immutable original intent. A retry never substitutes a current descriptor."""

    freeze_logical_id: Identifier
    freeze_receipt_sha256: Digest
    cell_id: Identifier
    purchase: StudyPurchase
    experiment: Experiment
    journal_path: PrivatePath
    predecessor: NativePurchaseReference | None
    initial_journal: NativePurchaseJournalIdentity | None

    @model_validator(mode="after")
    def original_identity(self) -> Self:
        if message_sha256(self.experiment) != self.purchase.experiment_sha256:
            raise ValueError("Purchase must bind the whole canonical experiment")
        if (self.purchase.ordinal == 0) != (
            self.predecessor is None and self.initial_journal is None
        ):
            raise ValueError(
                "First purchase requires initial absence; later purchases need a prefix"
            )
        if (self.predecessor is None) != (self.initial_journal is None):
            raise ValueError("Retained predecessor and initial Journal identity are paired")
        return self


class NativePurchaseRequest(_ExecutionRequest):
    operation: Literal["purchase"] = "purchase"
    purpose: Literal["execution", "reconciliation"] = "execution"
    phase: Literal["comparison"] = "comparison"
    cell_id: Identifier
    purchase_logical_id: Identifier
    purchase: StudyPurchase
    reconcile_attempt_id: Identifier | None = None
    input_bytes: Annotated[int, Field(ge=1, le=PURCHASE_INPUT_BYTES)]
    output_limit_bytes: Annotated[int, Field(ge=64 * 1024, le=PURCHASE_RESULT_BYTES)]

    @model_validator(mode="after")
    def purchase_scope(self) -> Self:
        if self.purpose == "execution":
            if self.logical_id != self.purchase_logical_id or self.reconcile_attempt_id is not None:
                raise ValueError("Execution retains its original purchase logical identity")
        elif (
            self.mode != "recover"
            or self.logical_id == self.purchase_logical_id
            or self.reconcile_attempt_id is None
            or self.retry_of is not None
        ):
            raise ValueError("Reconciliation is a distinct paid operation, never a purchase retry")
        return self


class NativePurchasePrefix(Message):
    records: Annotated[tuple[ExperimentRecord, ...], Field(max_length=12)]


class NativePurchaseAttemptContext(Message):
    """Observed only during paid work, separately bound from immutable intent."""

    attempt_id: Identifier
    observed_journal: NativePurchaseJournalIdentity | None
    original_prefix_sha256: Digest
    row_state: Literal["missing", "pending", "terminal"]

    @model_validator(mode="after")
    def observed_row(self) -> Self:
        if self.row_state != "missing" and self.observed_journal is None:
            raise ValueError("A pending or terminal row requires an observed Journal")
        return self


class NativePurchaseResult(Message):
    kind: Literal["execution", "reconciliation"]
    record: ExperimentRecord
    context: NativePurchaseAttemptContext
    journal: NativePurchaseJournalIdentity
    facts: NativeWorkFacts


class NativePurchaseReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.purchase-receipt.v1"] = (
        "strange-physics.purchase-receipt.v1"
    )
    operation: Literal["purchase"] = "purchase"
    kind: Literal["execution"] = "execution"
    purchase: StudyPurchase
    context_sha256: Digest
    journal: NativePurchaseJournalIdentity


class NativePurchaseReconciliationReceipt(_ExecutionReceipt):
    schema_version: Literal["strange-physics.purchase-reconciliation-receipt.v1"] = (
        "strange-physics.purchase-reconciliation-receipt.v1"
    )
    operation: Literal["purchase"] = "purchase"
    kind: Literal["reconciliation"] = "reconciliation"
    purchase_logical_id: Identifier
    purchase: StudyPurchase
    unresolved_attempt_id: Identifier
    context_sha256: Digest
    journal: NativePurchaseJournalIdentity
