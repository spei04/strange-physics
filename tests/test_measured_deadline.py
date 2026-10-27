"""Deadline classification and settlement; no numerical producer is executed."""

from __future__ import annotations

import json
import signal
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NoReturn

import pytest
from pydantic import BaseModel, ValidationError, field_validator
from test_comparison_stage_binding import scoring_fixture
from test_measured_candidates import actual_build, current, last_update, setup
from test_native_spring_contracts import inputs, synthetic_result

from strange_physics import measured_candidates as executor
from strange_physics import measured_publication as publisher
from strange_physics import native_scoring as scoring
from strange_physics.candidate_store import CandidateStore
from strange_physics.installed_identity import TrustedInstallation
from strange_physics.native_spring_contracts import NativeCandidateInput
from strange_physics.publication_store import raw
from strange_physics.study_ledger import StudyLedgerError, summarize_study

__all__ = ["actual_build"]

BUDGET_NS = 5_000_000_000


def interrupt() -> NoReturn:
    """Invoke the installed real handler synchronously, without sleeps or CPU burn."""
    handler = signal.getsignal(signal.SIGPROF)
    assert callable(handler)
    handler(signal.SIGPROF, None)
    raise AssertionError("The deadline handler must interrupt")


@pytest.fixture(autouse=True)
def forbid_numerical_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Deadline regressions must not run a numerical producer")

    for name in (
        "strange_physics.simulation.simulate",
        "strange_physics.native_candidates.produce_native_candidates",
        "strange_physics.native_prediction.predict_native_spring",
        "strange_physics.native_scoring.score_native_predictions",
        "strange_physics.native_scoring.evaluate_spring_predictions",
        "strange_physics.measured_candidates.produce_native_candidates",
        "strange_physics.measured_candidates.produce_stage",
    ):
        monkeypatch.setattr(name, forbidden)


@pytest.mark.parametrize(
    "validator,reason",
    [
        ("validate_native_candidate_result", "preparation_mismatch"),
        ("validate_selected_native_candidate", "preparation_mismatch"),
        ("validate_native_preparation_result", "preparation_mismatch"),
        ("validate_native_prediction_result", "prediction_mismatch"),
    ],
)
@pytest.mark.parametrize("deadline", [False, True])
def test_nested_scientific_validation_distinguishes_deadline_from_semantic_error(
    monkeypatch: pytest.MonkeyPatch, validator: str, reason: str, deadline: bool
) -> None:
    actual, _, _ = scoring_fixture()
    called = 0

    def fail(*args: object, **kwargs: object) -> NoReturn:
        nonlocal called
        called += 1
        if deadline:
            interrupt()
        raise ValueError("Synthetic semantic contradiction")

    monkeypatch.setattr(scoring, validator, fail)
    if deadline:
        with pytest.raises(StudyLedgerError, match="^publication_deadline$") as caught:
            with publisher._deadline(
                BUDGET_NS, BUDGET_NS, BUDGET_NS, BUDGET_NS, time.process_time_ns()
            ):
                scoring._submissions(actual, attempt_id="score")
        assert isinstance(caught.value.__cause__, publisher._DeadlineInterrupt)
        assert not isinstance(caught.value.__cause__, ValueError)
    else:
        with publisher._deadline(
            BUDGET_NS, BUDGET_NS, BUDGET_NS, BUDGET_NS, time.process_time_ns()
        ):
            assert scoring._submissions(actual, attempt_id="score") == (reason, None)
    assert called == 1


@pytest.mark.parametrize("deadline", [False, True])
def test_pydantic_does_not_reclassify_deadline_as_invalid_input(deadline: bool) -> None:
    class Payload(BaseModel):
        value: int

        @field_validator("value")
        @classmethod
        def validate_value(cls, value: int) -> int:
            if deadline:
                interrupt()
            raise ValueError("Synthetic semantic contradiction")

    expected = StudyLedgerError if deadline else ValidationError
    message = "^publication_deadline$" if deadline else "Synthetic semantic contradiction"
    with pytest.raises(expected, match=message):
        with publisher._deadline(
            BUDGET_NS, BUDGET_NS, BUDGET_NS, BUDGET_NS, time.process_time_ns()
        ):
            Payload.model_validate({"value": 1})


@pytest.mark.parametrize("boundary", ["start_cpu", "start_wall", "work"])
def test_synchronous_deadlines_keep_existing_public_code(boundary: str) -> None:
    with pytest.raises(StudyLedgerError, match="^publication_control_deadline$") as caught:
        with publisher._deadline(
            0 if boundary == "start_cpu" else BUDGET_NS,
            BUDGET_NS,
            0 if boundary == "start_wall" else BUDGET_NS,
            BUDGET_NS,
            time.process_time_ns(),
        ) as clock:
            assert boundary == "work"
            clock.phase_started -= BUDGET_NS
            clock.work()
    assert isinstance(caught.value.__cause__, publisher._DeadlineInterrupt)
    assert caught.value.__cause__.code == "publication_control_deadline"


def test_deadline_translates_after_unwind_preserving_notes_and_restoring_handlers() -> None:
    handlers = {s: signal.getsignal(s) for s in (signal.SIGALRM, signal.SIGPROF)}
    with pytest.raises(StudyLedgerError) as caught:
        with publisher._deadline(
            BUDGET_NS, BUDGET_NS, BUDGET_NS, BUDGET_NS, time.process_time_ns()
        ) as clock:
            clock.work()
            try:
                interrupt()
            except publisher._DeadlineInterrupt as error:
                error.add_note("Synthetic settlement diagnostic")
                # The actual settlement transition clears exhausted; the original
                # exception still carries its reason across the boundary.
                assert clock.tail()
                assert not clock.exhausted
                raise
    assert str(caught.value) == "publication_deadline"
    assert caught.value.__notes__ == ["Synthetic settlement diagnostic"]
    assert isinstance(caught.value.__cause__, publisher._DeadlineInterrupt)
    assert caught.value.__cause__.__notes__ == caught.value.__notes__
    assert {s: signal.getsignal(s) for s in handlers} == handlers
    assert all(
        signal.getitimer(timer) == (0.0, 0.0) for timer in (signal.ITIMER_REAL, signal.ITIMER_PROF)
    )


@pytest.mark.parametrize("kind", ["candidate", "publication"])
def test_child_wait_deadline_keeps_existing_known_cpu_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kind: str
) -> None:
    module = executor if kind == "candidate" else publisher
    waits = 0
    kills: list[tuple[int, int]] = []

    def wait4(pid: int, options: int) -> tuple[int, int, Any]:
        nonlocal waits
        assert pid == 12345 and options == 0
        waits += 1
        if waits == 1:
            interrupt()
        return pid, 0, SimpleNamespace(ru_utime=0.125, ru_stime=0.0)

    monkeypatch.setattr(module.os, "fork", lambda: 12345)
    monkeypatch.setattr(module.os, "wait4", wait4)
    monkeypatch.setattr(module.os, "kill", lambda pid, sig: kills.append((pid, sig)))
    # This is only the existing private wait/cleanup transport, with no fork,
    # authority, input parsing, output or producer. No public request is admitted.
    request: Any = SimpleNamespace(output_limit_bytes=1024)
    with publisher._deadline(
        BUDGET_NS, BUDGET_NS, BUDGET_NS, BUDGET_NS, time.process_time_ns()
    ) as clock:
        value: tuple[object, int]
        if kind == "candidate":
            value = executor._run_child(request, b"", tmp_path / "unused")
        else:
            value = publisher._run_child(
                request, b"", tmp_path / "unused-journal", {}, None, None, tmp_path / "unused"
            )
        assert value == (None, 125_000_000)
        assert clock.exhausted
    assert waits == 2 and kills == [(12345, signal.SIGKILL)]


def test_supervisor_deadline_retains_known_cost_unknown_hold_and_cleanup_note(
    tmp_path: Path, actual_build: TrustedInstallation, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Existing synthetic reference authority, one public attempt, no child or
    # simulation. The typed fixture is explicitly supplied, not purchased evidence.
    data = inputs().model_dump(mode="json")
    data["observations"]["engine_fingerprint"] = actual_build.engine_fingerprint
    actual = NativeCandidateInput.model_validate_json(json.dumps(data))
    root = tmp_path / "run"
    request = setup(root, actual_build, actual)
    output = raw(synthetic_result(actual, attempt=request.attempt_id))
    close = CandidateStore.close

    def feed(*args: object, **kwargs: object) -> tuple[bytes, int]:
        (root / "candidate-output-0").write_bytes(output)
        (root / "candidate-output-0").chmod(0o600)
        return output, 0

    def fail_validation(*args: object, **kwargs: object) -> NoReturn:
        interrupt()

    def fail_close(store: CandidateStore) -> None:
        close(store)
        raise OSError("Synthetic close failure")

    monkeypatch.setattr(executor, "_run_child", feed)
    monkeypatch.setattr(executor, "_validate", fail_validation)
    monkeypatch.setattr(CandidateStore, "close", fail_close)
    with pytest.raises(StudyLedgerError) as caught:
        executor.commit_native_candidates(root, request)
    assert str(caught.value) == "publication_deadline"
    assert isinstance(caught.value.__cause__, publisher._DeadlineInterrupt)
    assert any("Final store close failed" in note for note in caught.value.__notes__)
    ledger = current(root)
    update = last_update(ledger)
    assert len(ledger.records) == 3
    assert update.attempt_id == request.attempt_id
    assert update.state == "unknown" and update.facts is None
    assert update.cpu_ns is not None and update.cpu_ns > 0
    assert update.wall_ns is not None and update.wall_ns > 0
    assert update.artifact_bytes == request.input_bytes + len(output)
    assert summarize_study(ledger).budget.unresolved_attempts == 2
