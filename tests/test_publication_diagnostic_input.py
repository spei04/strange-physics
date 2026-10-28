"""Original diagnostic transport; synthetic Journal/facts, never measured publication."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any, cast

import pytest
from test_study_classical_composition import JointMaterial, reservation, terminal
from test_study_classical_composition import joint as joint
from test_study_classical_composition import journal as journal
from test_study_ledger import append, reserve, update
from test_study_publication import arguments, history, propose
from test_study_scoring import raw, typed

from strange_physics import measured_publication as publisher
from strange_physics import native_candidates, native_classical, native_prediction, native_scoring
from strange_physics import study_publication as publication
from strange_physics.measured_publication_contracts import (
    MIB,
    NativePublicationRequest,
    PublicationFile,
)
from strange_physics.native_classical_contracts import ClassicalDiagnosticInput
from strange_physics.publication_store import Store
from strange_physics.research_contracts import message_sha256
from strange_physics.study_ledger import StudyLedgerError, summarize_study


@pytest.fixture(scope="module")
def independent(joint: JointMaterial) -> JointMaterial:
    # Compute the actual separate input/result once; never relabel the selected result.
    actual = ClassicalDiagnosticInput(
        context=joint.actual.context.model_copy(update={"selected": None}),
        config=joint.actual.config,
        world=joint.actual.world,
    )
    result = native_classical.run_classical_diagnostic(actual, attempt_id="diagnostic")
    native_classical.validate_classical_diagnostic_result(result, actual, attempt_id="diagnostic")
    return JointMaterial(joint.native, actual, result)


def block_producers(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Publication only validates retained results")

    for module, name in [
        (native_candidates, "produce_native_candidates"),
        (native_prediction, "predict_native_spring"),
        (native_scoring, "score_native_predictions"),
        (native_classical, "run_classical_diagnostic"),
        (native_classical, "fit_spring"),
        (native_classical, "predict_linear_spring"),
        (native_classical, "evaluate_spring_predictions"),
    ]:
        monkeypatch.setattr(module, name, fail)


def test_original_unselected_diagnostic_preserves_full_native_history(
    independent: JointMaterial, journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    block_producers(monkeypatch)
    before = journal.read_bytes()
    original = history(independent)
    result = propose(independent, journal, original, diagnostic_input_raw=raw(independent.actual))
    assert independent.native.actual.context.selected is not None
    assert independent.actual.context.selected is None
    assert result.evidence.diagnostic_input_sha256 == message_sha256(independent.actual)
    assert result.evidence.diagnostic_result == independent.result
    assert raw(result.evidence.native.score) == raw(independent.native.result)
    assert result.evidence.native.failed_purchase_operation_ids == ("operation-11",)
    assert len(independent.actual.context.candidates.observations.records) == 12
    assert result.evidence.outcome.status == "complete"
    assert result.evidence.native.budget == summarize_study(original).budget
    assert journal.read_bytes() == before
    # Omitting the actual independent input still follows the original strict path.
    with pytest.raises(StudyLedgerError, match="^diagnostic_attempt_mismatch$"):
        propose(independent, journal, original)


def test_explicit_same_selection_keeps_legacy_evidence_and_receipt_bytes(
    joint: JointMaterial, journal: Path
) -> None:
    legacy = propose(joint, journal)
    omitted = propose(joint, journal, diagnostic_input_raw=None)
    explicit = propose(joint, journal, diagnostic_input_raw=raw(joint.actual))
    assert legacy.evidence_raw == omitted.evidence_raw == explicit.evidence_raw
    assert raw(legacy.receipt) == raw(omitted.receipt) == raw(explicit.receipt)
    assert raw(legacy.ledger) == raw(omitted.ledger) == raw(explicit.ledger)


def test_original_unselected_receipt_replays_after_later_unknown_hold(
    independent: JointMaterial, journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    block_producers(monkeypatch)
    original = history(independent)
    first = propose(independent, journal, original, diagnostic_input_raw=raw(independent.actual))
    later = append(first.ledger, reserve("later-unknown"))
    replay = propose(
        independent,
        journal,
        later,
        diagnostic_input_raw=raw(independent.actual),
        expected_revision=len(original.records),
        expected_head_sha256=message_sha256(original.records[-1]),
        original_ledger_raw=raw(original),
        original_evidence_raw=first.evidence_raw,
    )
    assert replay.replayed and raw(replay.ledger) == raw(later)
    assert replay.evidence_raw == first.evidence_raw
    assert raw(replay.receipt) == raw(first.receipt)
    assert summarize_study(later).budget.unresolved_attempts == 1
    assert replay.evidence.native.budget.unresolved_attempts == 0


def test_original_input_does_not_settle_an_old_unknown_diagnostic(
    independent: JointMaterial, journal: Path
) -> None:
    old = reservation(independent, "old")
    value = append(append(independent.native.history, old), update(old, "unknown", cpu_ns=150))
    value = terminal(append(value, reservation(independent, retry_of="old")), independent.result)
    result = propose(independent, journal, value, diagnostic_input_raw=raw(independent.actual))
    assert result.evidence.outcome.status == "incomplete"
    assert result.evidence.native.unresolved_cell_attempt_ids == ("old",)
    assert result.evidence.native.budget == summarize_study(value).budget
    assert result.evidence.native.failed_purchase_operation_ids == ("operation-11",)


@pytest.mark.parametrize(
    "field",
    [
        "world",
        "engine",
        "failed-row",
        "action-signed-zero",
        "candidate-attempt",
        "selection",
        "config-signed-zero",
        "prediction-signed-zero",
    ],
)
def test_original_input_rejects_each_nonselection_identity_change(
    joint: JointMaterial, journal: Path, field: str
) -> None:
    data = joint.actual.model_dump(mode="json")
    if field == "world":
        data["world"]["noise_seed"] += 1
    elif field == "engine":
        data["context"]["candidates"]["observations"]["engine_fingerprint"] = "f" * 64
    elif field == "failed-row":
        data["context"]["candidates"]["observations"]["records"].pop()
    elif field == "action-signed-zero":
        particle = data["context"]["candidates"]["observations"]["records"][0]["experiment"][
            "particles"
        ][0]
        assert particle["velocity"][0] == 0.0
        particle["velocity"][0] = -0.0
    elif field == "candidate-attempt":
        data["context"]["candidate_attempt_id"] = "foreign"
    elif field == "selection":
        data["context"]["selected"]["candidate_result_sha256"] = "f" * 64
    elif field == "config-signed-zero":
        data["config"]["prediction_config"]["min_coefficient"] = -0.0
    else:
        data["context"]["prediction_config"]["min_coefficient"] = -0.0
    # Each specimen is independently well-typed; denial must reach the material join.
    actual = typed(ClassicalDiagnosticInput, data)
    assert message_sha256(actual) != message_sha256(joint.actual)
    with pytest.raises(StudyLedgerError, match="^diagnostic_input_mismatch$"):
        propose(joint, journal, diagnostic_input_raw=raw(actual))


@pytest.mark.parametrize("missing", ["result", "attempt"])
def test_explicit_input_requires_result_and_attempt_at_pure_boundary(
    joint: JointMaterial, journal: Path, missing: str
) -> None:
    changes = {"diagnostic_result_raw" if missing == "result" else "diagnostic_attempt_id": None}
    with pytest.raises(StudyLedgerError, match="^diagnostic_input_witness_missing$"):
        publication.reconcile_study_publication(
            raw(history(joint)),
            journal,
            **arguments(joint, diagnostic_input_raw=raw(joint.actual), **changes),
        )


@pytest.mark.parametrize("bad", [b"{}", b'{"context":1,"context":2}', b'{"x":NaN}', b"null"])
def test_explicit_input_uses_strict_parser(joint: JointMaterial, journal: Path, bad: bytes) -> None:
    with pytest.raises(ValueError):
        propose(joint, journal, diagnostic_input_raw=bad)


def test_explicit_input_counts_toward_existing_total_byte_bound(
    joint: JointMaterial, journal: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = arguments(joint)
    baseline = sum(
        len(item)
        for item in (
            raw(history(joint)),
            args["scoring_input_raw"],
            args["scoring_result_raw"],
            args["diagnostic_result_raw"],
            *args["materials"].values(),
        )
    )
    monkeypatch.setattr(publication, "MAX_PUBLICATION_INPUT_BYTES", baseline)
    with pytest.raises(StudyLedgerError, match="^publication_input_limit$"):
        propose(joint, journal, diagnostic_input_raw=raw(joint.actual))


def request(payloads: dict[str, bytes], **changes: Any) -> NativePublicationRequest:
    values: dict[str, Any] = dict(
        mode="scored",
        event_id="publication",
        cell_id="cell",
        attempt_id="publish",
        ticket=0,
        expected_revision=1,
        expected_head_sha256="a" * 64,
        journal_path="/private/journal",
        journal_sha256="b" * 64,
        diagnostic_attempt_id="diagnostic" if "diagnostic_result" in payloads else None,
        files=tuple(
            PublicationFile(
                name=name,
                path="/private/" + name,
                sha256=hashlib.sha256(data).hexdigest(),
                byte_count=len(data),
            )
            for name, data in payloads.items()
        ),
        cpu_reservation_ns=4_000_000_000,
        artifact_reservation_bytes=16 * MIB,
        output_limit_bytes=64 * 1024,
        wall_limit_ns=30_000_000_000,
    )
    return NativePublicationRequest.model_validate(values | changes)


@pytest.mark.parametrize("kind", ["legacy-native", "legacy-diagnostic", "original", "early"])
def test_request_preserves_legacy_and_accepts_paired_original_input(kind: str) -> None:
    payloads = {"scoring_input": b"input", "scoring_result": b"result"}
    if kind in {"legacy-diagnostic", "original"}:
        payloads["diagnostic_result"] = b"diagnostic"
    if kind == "original":
        payloads["diagnostic_input"] = b"original"
    actual = (
        request({"witnesses": b"witnesses"}, mode="early") if kind == "early" else request(payloads)
    )
    assert "diagnostic_input" not in actual.model_dump()
    assert {f.name for f in actual.files} == ({"witnesses"} if kind == "early" else set(payloads))


@pytest.mark.parametrize(
    "fault", ["result", "attempt", "scoring-input", "early", "extra", "duplicate"]
)
def test_request_rejects_partial_or_extra_original_input(fault: str) -> None:
    payloads = {
        "scoring_input": b"input",
        "scoring_result": b"result",
        "diagnostic_input": b"original",
        "diagnostic_result": b"diagnostic",
    }
    changes: dict[str, Any] = {}
    if fault == "result":
        del payloads["diagnostic_result"]
    elif fault == "attempt":
        changes["diagnostic_attempt_id"] = None
    elif fault == "scoring-input":
        del payloads["scoring_input"]
    elif fault == "early":
        changes["mode"] = "early"
    elif fault == "extra":
        payloads["invented"] = b"extra"
    else:
        valid = request(payloads)
        changes["files"] = (*valid.files, valid.files[-1])
    with pytest.raises(ValueError):
        request(payloads, **changes)


def test_original_raw_bytes_are_bound_by_existing_publication_inventory() -> None:
    # This is only the existing read-only inventory seam, not Store initialization/authority.
    payloads = {
        "scoring_input": b"input",
        "scoring_result": b"result",
        "diagnostic_input": b"original",
        "diagnostic_result": b"diagnostic",
    }
    actual = request(payloads)
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE materials(event_id TEXT,name TEXT,data BLOB,digest TEXT)")
        db.executemany(
            "INSERT INTO materials VALUES(?,?,?,?)",
            [(actual.event_id, f.name, payloads[f.name], f.sha256) for f in actual.files],
        )
        holder = type("ReadOnlyInventory", (), {"db": db})()
        assert publisher._stored_payloads(cast(Store, holder), actual) == payloads
        changed = b" " + payloads["diagnostic_input"]
        db.execute("UPDATE materials SET data=? WHERE name='diagnostic_input'", (changed,))
        with pytest.raises(StudyLedgerError, match="^closure_corrupt$"):
            publisher._stored_payloads(cast(Store, holder), actual)
    alternate = request(payloads | {"diagnostic_input": changed})
    assert publisher._identity(alternate) != publisher._identity(actual)
