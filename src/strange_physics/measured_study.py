"""Charged same-store freeze and private Journal-bound candidate production.

These interfaces do not implement purchased simulation, classical execution,
publication transfer, future menu semantics, or full-study admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strange_physics.candidate_execution_contracts import CandidateMeasurements
from strange_physics.measured_candidates import _commit_native_execution
from strange_physics.native_spring_contracts import NativeCandidateResult
from strange_physics.study_contracts import NativeStudyLedger
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeComparisonReceipt,
    NativeFreezeReceipt,
    NativeFreezeRequest,
    NativeFreezeResult,
)


@dataclass(frozen=True)
class CommittedStudyTransition[Result: NativeFreezeResult | NativeCandidateResult]:
    receipt: NativeFreezeReceipt | NativeComparisonReceipt
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
