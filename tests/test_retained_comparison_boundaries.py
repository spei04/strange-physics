"""Four-call comparison guard supplement with explicitly injected purchase intents.

The one root declares its entire profile before admission. Its real current-engine
11+1 Journal tests guard composition, not paid-purchase authority or a study.
The separate 50-call specimen supplies the latter purchased-history success path.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
from pathlib import Path
from typing import Any

import freeze_journal_fixture as fixture_module
import pytest
from freeze_journal_fixture import (
    COPY_LIMIT,
    STORE_ENVELOPE,
    Fixture,
    comparison_request,
    generate_journal,
    inject_intents,
    prepare,
)
from test_measured_candidates import actual_build, current, last_update
from test_measured_purchase import forbidden
from test_native_spring_contracts import selection
from test_retained_comparison_stages import stage_request_data

import strange_physics.measured_candidates as supervisor
import strange_physics.measured_native_stages as stages
from strange_physics.candidate_execution_contracts import MIB, CandidateControl
from strange_physics.candidate_store import CandidateStore
from strange_physics.comparison_stage_resolver import RetainedStageWitness
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.measured_study import commit_journal_candidates, commit_native_freeze
from strange_physics.native_prediction_contracts import NativePredictionConfig
from strange_physics.native_scoring_contracts import (
    NativeEvaluationInput,
    NativePreparationResult,
    NativeScoringPolicy,
)
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPreparationInput,
    NativePreparationRequest,
)
from strange_physics.publication_store import digest, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import NativeStudyLedger, StudyAttemptReservation
from strange_physics.study_execution_contracts import NativeComparisonInput
from strange_physics.study_ledger import StudyLedgerError, summarize_study

__all__ = ["actual_build"]

DECLARED_BYTES = 337289216
DECLARED_CPU_NS = 371000000000
PROOF_LIMIT = 64 * 1024
# Bootstrap originals, candidate original, two preparation originals, one byte
# mutation, original capture restoration, and the final bounded proof.
SETUP_EXPORT_CEILING = MIB + 128 * 1024 + 2 * MIB + 1 + 128 * 1024 + PROOF_LIMIT


def boundary_control(**values: Any) -> CandidateControl:
    """Four normal slots and three protected recoveries, fixed before seed writes."""
    return CandidateControl(**(values | {"tickets": 7, "recovery_tickets": 3}))


def closure_hashes(fixture: Fixture) -> dict[str, str]:
    """Read closed metadata without creating another writable store connection."""
    with fixture.budget.phase():
        with sqlite3.connect(
            f"file:{fixture.root / 'candidate.sqlite3'}?mode=ro", uri=True
        ) as db:
            return dict(db.execute("SELECT logical_id,receipt_digest FROM closures").fetchall())


def overwrite(path: Path, value: bytes, *, offset: int = 0) -> None:
    """The caller prepays each overwrite; never weaken SetupBudget.write reuse checks."""
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, "r+b") as output:
        output.seek(offset)
        assert output.write(value) == len(value)
        output.flush()
        os.fsync(output.fileno())


def test_four_call_history_substitution_and_final_witness_rollback(
    tmp_path: Path,
    actual_build: TrustedInstallation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert COPY_LIMIT == 4 * MIB and SETUP_EXPORT_CEILING == 3473409
    assert SETUP_EXPORT_CEILING <= COPY_LIMIT
    with monkeypatch.context() as patch:
        patch.setattr(fixture_module, "CandidateControl", boundary_control)
        f = prepare(tmp_path / "boundaries", actual_build, classical=True)
    assert f.budget.copies <= MIB
    c = f.control
    assert (c.tickets, c.recovery_tickets, c.database_limit_bytes) == (7, 3, 2 * MIB)
    assert (c.finalization_records, c.finalization_bytes) == (14, 64 * 1024)
    assert c.database_envelope() == STORE_ENVELOPE == 4329472
    assert c.required_control_bytes() == 125476864
    assert (
        c.required_control_bytes()
        + 48 * MIB
        + 12 * MIB
        + 56 * MIB
        + c.recovery_tickets * c.recovery_work_artifact_bytes
        + c.publication.required_bytes()
        == DECLARED_BYTES
    )
    assert (
        c.tickets * c.ticket_cpu_ns
        + c.bootstrap_cpu_ns
        + 120_000_000_000
        + 60_000_000_000
        + 56_000_000_000
        + c.recovery_tickets * c.recovery_work_cpu_ns
        + c.publication.control_cpu_ns
        + c.publication.work_cpu_ns
        == DECLARED_CPU_NS
    )
    assert 36 * (131072 + 262400) + 4 * STORE_ENVELOPE + COPY_LIMIT == 35677184

    calls: list[str] = []
    children: list[tuple[str, int]] = []
    real_child = supervisor._run_child

    def counted_child(request: Any, *args: Any, **kwargs: Any) -> tuple[bytes | None, int]:
        result, cpu = real_child(request, *args, **kwargs)
        assert cpu >= 0
        children.append((request.operation, cpu))
        return result, cpu

    monkeypatch.setattr(supervisor, "_run_child", counted_child)
    calls.append("freeze")
    frozen = commit_native_freeze(f.root, f.freeze_request)
    inject_intents(f)  # One prepaid setup transaction, not public purchase execution.
    generate_journal(f)  # One bounded child; eleven simulations and one labeled fault.
    candidate_request = comparison_request(f, raw(frozen.receipt))
    assert f.budget.copies <= MIB + 128 * 1024
    calls.append("comparison_candidate")
    candidate = commit_journal_candidates(f.root, candidate_request)
    assert [operation for operation, _ in children] == ["comparison_candidate"]

    with f.budget.phase():
        material = NativeComparisonInput.model_validate_json(
            (f.root / "candidate-input-1").read_bytes()
        )
        observations = material.candidate.observations
        assert len(observations.records) == 12
        assert [record.status for record in observations.records] == ["completed"] * 11 + ["failed"]
        assert observations.records[-1].error == "simulation_failed"
        assert observations.engine_fingerprint == actual_build.engine_fingerprint
        capture_path = f.root / "candidate-journal-1"
        original_capture = capture_path.read_bytes()
        assert len(original_capture) <= 128 * 1024
        assert digest(original_capture) == material.journal_sha256
        chosen = selection(candidate.result, index=1)
        assert chosen.selection_claim == "selected-candidate-only"
        context = NativeEvaluationInput(
            candidates=material.candidate,
            candidate_result=candidate.result,
            candidate_attempt_id=candidate_request.attempt_id,
            selected=chosen,
            policy=NativeScoringPolicy.model_validate_json(f.freeze.artifacts["scoring_policy"]),
            prediction_config=NativePredictionConfig.model_validate_json(
                f.freeze.artifacts["prediction_config"]
            ),
        )
        good = NativeComparisonPreparationInput(
            candidate_logical_id=candidate_request.logical_id,
            candidate_receipt_sha256=digest(raw(candidate.receipt)),
            context=context,
        )
        data = context.model_dump(mode="json")
        velocity = data["candidates"]["observations"]["records"][-1]["experiment"]["particles"][0][
            "velocity"
        ]
        assert velocity[0] == 0.0 and math.copysign(1.0, velocity[0]) == 1.0
        velocity[0] = -0.0
        changed_context = NativeEvaluationInput.model_validate_json(json.dumps(data))
        changed = good.model_copy(update={"context": changed_context})
        assert changed_context.candidates.observations.records[-1].status == "failed"
        assert message_sha256(changed_context) != message_sha256(context)
        assert raw(changed_context.candidate_result) == raw(context.candidate_result)
    original_closures = closure_hashes(f)
    assert set(original_closures) == {"freeze", "candidate"}
    original_ledger = current(f.root)
    assert len(original_ledger.records) == 19
    assert summarize_study(original_ledger).budget.unresolved_attempts == 14

    bad_request = NativePreparationRequest(
        **stage_request_data(
            f,
            changed,
            changed_context,
            context.policy,
            ticket=2,
            operation="preparation",
            input_limit=MIB,
            output_limit=8 * MIB,
            artifact_limit=24 * MIB,
        )
    )
    # Recomputed raw and inner hashes prove this is not a stale-envelope rejection.
    assert bad_request.input_raw_sha256 == digest(raw(changed))
    assert bad_request.input_sha256 == message_sha256(changed_context)
    calls.append("preparation_history_denied")
    with monkeypatch.context() as patch:
        patch.setattr(supervisor, "_run_child", forbidden)
        with pytest.raises(StudyLedgerError, match="^comparison_preparation_material$"):
            stages.commit_native_preparation(f.root, bad_request)
    rejected = current(f.root)
    first_update = last_update(rejected)
    assert first_update.attempt_id == bad_request.attempt_id
    assert first_update.state == "unknown" and first_update.facts is None
    assert first_update.cpu_ns is not None and first_update.cpu_ns >= 0
    assert any(
        isinstance(record.event, StudyAttemptReservation)
        and record.event.attempt_id == bad_request.attempt_id
        and record.event.input_sha256 == bad_request.input_sha256
        for record in rejected.records
    )
    assert not (f.root / "candidate-output-2").exists()
    assert closure_hashes(f) == original_closures
    assert summarize_study(rejected).budget.unresolved_attempts == 15

    good_request = NativePreparationRequest(
        **stage_request_data(
            f,
            good,
            context,
            context.policy,
            ticket=3,
            operation="preparation",
            input_limit=MIB,
            output_limit=8 * MIB,
            artifact_limit=24 * MIB,
        )
    )
    # Reserve both deliberate overwrite and restoration before the measured call.
    # Their execution CPU belongs to the active work clock or the later setup phase.
    with f.budget.phase():
        assert f.budget.copies + 1 + len(original_capture) + PROOF_LIMIT <= COPY_LIMIT
        f.budget.copies += 1 + len(original_capture)
    seen_store: CandidateStore | None = None
    mutation: dict[str, str | int | bool] = {}
    real_replace = CandidateStore.replace
    real_recheck = RetainedStageWitness.recheck

    def remember_store(
        store: CandidateStore, before: NativeStudyLedger, after: NativeStudyLedger
    ) -> None:
        nonlocal seen_store
        seen_store = store
        real_replace(store, before, after)

    def mutate_at_final_check(witness: RetainedStageWitness) -> None:
        store = seen_store
        if store is not None and store.db.in_transaction and not mutation:
            row = store.db.execute(
                "SELECT receipt_digest FROM closures WHERE logical_id=?",
                (good_request.logical_id,),
            ).fetchone()
            if row is not None:
                # All earlier checks saw unchanged bytes. The inserted closure and
                # completed update are still inside the transaction to be rolled back.
                assert last_update(store.ledger()).state == "completed"
                assert [operation for operation, _ in children] == [
                    "comparison_candidate",
                    "preparation",
                ]
                assert capture_path in witness.files
                assert digest(capture_path.read_bytes()) == digest(original_capture)
                overwrite(
                    capture_path,
                    bytes([original_capture[-1] ^ 1]),
                    offset=len(original_capture) - 1,
                )
                mutation.update(
                    inside_transaction=True,
                    provisional_receipt_sha256=row[0],
                    changed_capture_sha256=digest(capture_path.read_bytes()),
                )
        real_recheck(witness)

    calls.append("preparation_final_witness_denied")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(CandidateStore, "replace", remember_store)
            patch.setattr(RetainedStageWitness, "recheck", mutate_at_final_check)
            with pytest.raises(StudyLedgerError, match="^comparison_retained_changed$"):
                stages.commit_native_preparation(f.root, good_request)
    finally:
        if mutation:
            with f.budget.phase():
                overwrite(capture_path, original_capture)
                assert capture_path.read_bytes() == original_capture

    assert mutation["inside_transaction"] is True
    assert mutation["changed_capture_sha256"] != digest(original_capture)
    final = current(f.root)
    second_update = last_update(final)
    assert second_update.attempt_id == good_request.attempt_id
    assert second_update.state == "unknown" and second_update.facts is None
    assert second_update.cpu_ns is not None and second_update.cpu_ns >= children[-1][1]
    assert final.records[: len(rejected.records)] == rejected.records
    assert final.records[: len(original_ledger.records)] == original_ledger.records
    assert closure_hashes(f) == original_closures
    with f.budget.phase():
        preparation = NativePreparationResult.model_validate_json(
            (f.root / "candidate-output-3").read_bytes()
        )
        assert preparation.payload.status == "prepared"
        assert preparation.facts.attempt_id == good_request.attempt_id
        assert preparation.facts.observation_sha256 == message_sha256(observations)
        assert preparation.facts.outcome == "completed"

    assert calls == [
        "freeze",
        "comparison_candidate",
        "preparation_history_denied",
        "preparation_final_witness_denied",
    ]
    assert [operation for operation, _ in children] == ["comparison_candidate", "preparation"]
    assert len(final.records) == 23
    assert summarize_study(final).budget.unresolved_attempts == 16
    assert all((f.root / f"candidate-ticket-{i}").is_file() for i in range(4))
    assert all(not (f.root / f"candidate-ticket-{i}").exists() for i in range(4, 7))
    assert len(raw(final)) <= 256 * 1024
    assert 256 * 1024 + 16 * 4096 + c.finalization_bytes == 393216
    assert 393216 <= c.publication.ledger_bytes
    assert (f.root / "candidate.sqlite3").stat().st_size <= c.database_limit_bytes
    supervisor._capacity(f.root, final, c)
    assert f.budget.child_epochs <= 36 and f.budget.store_attempts <= 4
    assert f.budget.parent_cpu + f.budget.child_cpu <= 120_000_000_000
    proof = {
        "scope": "Four synthetic guard calls; injected intents are not paid purchases.",
        "public_calls": calls,
        "measured_children": children,
        "setup_journal_children": 1,
        "setup_simulations": 11,
        "setup_explicit_faults": 1,
        "declared_bytes": DECLARED_BYTES,
        "declared_cpu_ns": DECLARED_CPU_NS,
        "ledger_records": len(final.records),
        "unresolved_holds": summarize_study(final).budget.unresolved_attempts,
        "original_capture_sha256": digest(original_capture),
        "mutation": mutation,
        "first_unknown": first_update.model_dump(mode="json"),
        "second_unknown": second_update.model_dump(mode="json"),
        "setup_copies_before_proof": f.budget.copies,
        "setup_parent_cpu_before_proof_ns": f.budget.parent_cpu,
        "setup_child_cpu_ns": f.budget.child_cpu,
        "setup_journal_write_epochs": f.budget.child_epochs,
        "guard_removal_execution": "Not included; another public run needs its own declared calls.",
    }
    with f.budget.phase():
        proof_raw = json.dumps(proof, sort_keys=True).encode()
        assert len(proof_raw) <= PROOF_LIMIT
        f.budget.write(f.root / "boundary-proof.json", proof_raw)
    assert f.budget.copies <= SETUP_EXPORT_CEILING <= COPY_LIMIT
