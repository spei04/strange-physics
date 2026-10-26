"""Charged same-store freeze and private Journal-bound candidate production.

These interfaces do not implement publication transfer, future acquisition
policies, or full-study admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strange_physics.candidate_execution_contracts import CandidateMeasurements
from strange_physics.measured_candidates import _commit_native_execution
from strange_physics.native_classical_contracts import ClassicalDiagnosticResult
from strange_physics.native_spring_contracts import NativeCandidateResult
from strange_physics.purchase_execution_contracts import (
    NativePurchaseReceipt,
    NativePurchaseReconciliationReceipt,
    NativePurchaseRequest,
    NativePurchaseResult,
)
from strange_physics.study_contracts import NativeStudyLedger
from strange_physics.study_execution_contracts import (
    NativeClassicalReceipt,
    NativeComparisonCandidateRequest,
    NativeComparisonClassicalRequest,
    NativeComparisonReceipt,
    NativeFreezeReceipt,
    NativeFreezeRequest,
    NativeFreezeResult,
)


@dataclass(frozen=True)
class CommittedStudyTransition[
    Result: NativeFreezeResult | NativeCandidateResult | ClassicalDiagnosticResult
]:
    receipt: NativeFreezeReceipt | NativeComparisonReceipt | NativeClassicalReceipt
    result: Result
    result_raw: bytes
    original_ledger: NativeStudyLedger
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements
    replayed: bool


def commit_native_freeze(
    store_root: Path, request: NativeFreezeRequest
) -> CommittedStudyTransition[NativeFreezeResult]:
    value = _commit_native_execution(store_root, request, expected_operation="freeze")
    assert isinstance(value.receipt, NativeFreezeReceipt)
    assert isinstance(value.result, NativeFreezeResult)
    return CommittedStudyTransition(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )


def commit_journal_candidates(
    store_root: Path, request: NativeComparisonCandidateRequest
) -> CommittedStudyTransition[NativeCandidateResult]:
    value = _commit_native_execution(store_root, request, expected_operation="comparison_candidate")
    assert isinstance(value.receipt, NativeComparisonReceipt)
    assert isinstance(value.result, NativeCandidateResult)
    return CommittedStudyTransition(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )


def commit_journal_classical(
    store_root: Path, request: NativeComparisonClassicalRequest
) -> CommittedStudyTransition[ClassicalDiagnosticResult]:
    """Measure an independent diagnostic of the retained original purchased prefix."""
    value = _commit_native_execution(store_root, request, expected_operation="classical_diagnostic")
    assert isinstance(value.receipt, NativeClassicalReceipt)
    assert isinstance(value.result, ClassicalDiagnosticResult)
    return CommittedStudyTransition(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
    )


@dataclass(frozen=True)
class CommittedPurchase:
    receipt: NativePurchaseReceipt | NativePurchaseReconciliationReceipt
    result: NativePurchaseResult
    result_raw: bytes
    original_ledger: NativeStudyLedger
    ledger: NativeStudyLedger
    measurements: CandidateMeasurements
    replayed: bool
    holder_cpu_ns: int | None
    holder_status: int | None


def commit_journal_purchase(store_root: Path, request: NativePurchaseRequest) -> CommittedPurchase:
    """One fixed paid purchase/reconciliation; intact replay returns original bytes.

    Reconciliation establishes a terminal Journal record, never the interrupted
    attempt's unavailable measurement or original receipt. Its unknown hold survives.
    """
    value = _commit_native_execution(store_root, request, expected_operation="purchase")
    assert isinstance(value.receipt, (NativePurchaseReceipt, NativePurchaseReconciliationReceipt))
    assert isinstance(value.result, NativePurchaseResult)
    epochs = value.purchase_epochs
    return CommittedPurchase(
        value.receipt,
        value.result,
        value.result_raw,
        value.original_ledger,
        value.ledger,
        value.measurements,
        value.replayed,
        epochs.holder_cpu_ns if epochs is not None else None,
        epochs.holder_status if epochs is not None else None,
    )
