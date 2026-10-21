"""Synthetic native-study interface checks; no numerical study is executed."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import study_contracts as c
from strange_physics.contracts import Message
from strange_physics.research_contracts import message_sha256

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "contracts/study.examples.json").read_text())
MODELS: dict[str, type[Message]] = {
    "NativeAccountingPlan": c.NativeAccountingPlan,
    "NativeStudyManifest": c.NativeStudyManifest,
    "NativeWorkFacts": c.NativeWorkFacts,
    "NativeStudyLedger": c.NativeStudyLedger,
    "NativeStudySummary": c.NativeStudySummary,
}


def parse(name: str, value: Any) -> Message:
    return MODELS[name].model_validate_json(json.dumps(value))


@pytest.mark.parametrize("name", list(MODELS))
def test_example_roundtrip(name: str) -> None:
    value = parse(name, EXAMPLES["valid"][name])
    assert parse(name, json.loads(value.model_dump_json())) == value
    assert message_sha256(value) == message_sha256(parse(name, EXAMPLES["valid"][name]))


@pytest.mark.parametrize("fixture", EXAMPLES["schema_negative"] + EXAMPLES["runtime_negative"])
def test_negative_examples(fixture: dict[str, Any]) -> None:
    value = copy.deepcopy(EXAMPLES["valid"][fixture["model"]])
    value[fixture["field"]] = fixture["value"]
    with pytest.raises(ValidationError):
        parse(fixture["model"], value)


def test_schema_is_exact() -> None:
    assert c.study_json_schema() == json.loads((ROOT / "contracts/study.schema.json").read_text())


@pytest.mark.parametrize("target", ["cell_id", "journal_id"])
def test_duplicate_arm_identity(target: str) -> None:
    value = copy.deepcopy(EXAMPLES["valid"]["NativeStudyManifest"])
    value["cells"][1][target] = value["cells"][0][target]
    with pytest.raises(ValidationError):
        parse("NativeStudyManifest", value)


@pytest.mark.parametrize("target", ["world_id", "policy_seed", "selector"])
def test_cross_arm_or_missing_matrix(target: str) -> None:
    value = copy.deepcopy(EXAMPLES["valid"]["NativeStudyManifest"])
    value["cells"][0][target] = value["cells"][-1][target]
    with pytest.raises(ValidationError):
        parse("NativeStudyManifest", value)


@pytest.mark.parametrize("target", ["artifacts", "gates", "cells"])
def test_order_and_complete_manifest(target: str) -> None:
    value = copy.deepcopy(EXAMPLES["valid"]["NativeStudyManifest"])
    value[target].reverse()
    with pytest.raises(ValidationError):
        parse("NativeStudyManifest", value)


@pytest.mark.parametrize(
    "field", ["truth", "world_definition", "definition_sha256", "provider_key"]
)
def test_private_or_other_profile_fields_rejected(field: str) -> None:
    value = copy.deepcopy(EXAMPLES["valid"]["NativeStudyManifest"])
    value[field] = "forbidden"
    with pytest.raises(ValidationError):
        parse("NativeStudyManifest", value)


@pytest.mark.parametrize("field", ["sequence", "previous_sha256", "event_id"])
def test_chain_tampering(field: str) -> None:
    value = copy.deepcopy(EXAMPLES["valid"]["NativeStudyLedger"])
    record = value["records"][1]
    record[field] = {
        "sequence": 3,
        "previous_sha256": "f" * 64,
        "event_id": value["records"][0]["event_id"],
    }[field]
    with pytest.raises(ValidationError):
        parse("NativeStudyLedger", value)


@pytest.mark.parametrize("state", ["completed", "failed", "rejected"])
@pytest.mark.parametrize("field", ["cpu_ns", "wall_ns", "artifact_bytes", "facts"])
def test_unknown_cost_never_final(state: str, field: str) -> None:
    facts = copy.deepcopy(EXAMPLES["valid"]["NativeWorkFacts"])
    facts["outcome"] = state
    if state == "failed":
        facts.update(completed_count=3, failed_count=1)
    if state == "rejected":
        facts.update(completed_count=0, not_assessed_count=facts["requested_count"])
    value = {
        "attempt_id": facts["attempt_id"],
        "state": state,
        "cpu_ns": 0,
        "wall_ns": 0,
        "artifact_bytes": 0,
        "facts": facts,
    }
    value[field] = None
    with pytest.raises(ValidationError):
        c.StudyAttemptUpdate.model_validate_json(json.dumps(value))


def test_measurement_can_retain_overrun() -> None:
    facts = c.NativeWorkFacts.model_validate_json(json.dumps(EXAMPLES["valid"]["NativeWorkFacts"]))
    result = c.StudyAttemptUpdate(
        attempt_id=facts.attempt_id,
        state="completed",
        cpu_ns=c.MAX_CPU_NS + 1,
        wall_ns=1,
        artifact_bytes=c.MAX_ARTIFACT_BYTES + 1,
        facts=facts,
    )
    assert result.cpu_ns == c.MAX_CPU_NS + 1


@pytest.mark.parametrize("ordinal", range(12))
def test_calibration_counts_reserved_positions(ordinal: int) -> None:
    good = c.StudyPurchase(
        operation_id=f"operation-{ordinal}",
        ordinal=ordinal,
        experiment_sha256="a" * 64,
        calibration=ordinal < 4,
    )
    value = good.model_dump(mode="json") | {"calibration": ordinal >= 4}
    with pytest.raises(ValidationError):
        c.StudyPurchase.model_validate_json(json.dumps(value))


def test_all_36_unstarted_fixture_is_explicit() -> None:
    summary = c.NativeStudySummary.model_validate_json(
        json.dumps(EXAMPLES["valid"]["NativeStudySummary"])
    )
    assert len(summary.cells) == 36
    assert all(cell.status == "unstarted" and cell.outcome is None for cell in summary.cells)


@pytest.mark.parametrize("value", [0, True])
def test_work_requires_positive_cpu_reservation(value: int | bool) -> None:
    reservation = copy.deepcopy(EXAMPLES["valid"]["NativeStudyLedger"]["records"][0]["event"])
    reservation["cpu_reservation_ns"] = value
    with pytest.raises(ValidationError):
        c.StudyAttemptReservation.model_validate_json(json.dumps(reservation))


@pytest.mark.parametrize(
    "completed, failed, unassessed, valid", [(4, 0, 0, False), (0, 0, 4, False), (2, 1, 1, True)]
)
def test_failed_local_work_requires_failed_unit(
    completed: int, failed: int, unassessed: int, valid: bool
) -> None:
    value = EXAMPLES["valid"]["NativeWorkFacts"] | dict(
        outcome="failed",
        completed_count=completed,
        failed_count=failed,
        not_assessed_count=unassessed,
    )
    if valid:
        assert parse("NativeWorkFacts", value).model_dump()["failed_count"] == 1
    else:
        with pytest.raises(ValidationError):
            parse("NativeWorkFacts", value)


def test_candidate_prediction_and_engine_are_separate() -> None:
    manifest = c.NativeStudyManifest.model_validate_json(
        json.dumps(EXAMPLES["valid"]["NativeStudyManifest"])
    )
    assert (
        manifest.artifact("candidate_config").sha256
        != manifest.artifact("prediction_config").sha256
    )
    assert manifest.engine_fingerprint == "e" * 64
    facts = c.NativeWorkFacts.model_validate_json(json.dumps(EXAMPLES["valid"]["NativeWorkFacts"]))
    assert facts.schema_version == "strange-physics.native-work-facts.v1"
