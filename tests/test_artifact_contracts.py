from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.artifact_contracts import (
    ARTIFACT_MODELS,
    PUBLIC_MODELS,
    ArtifactRef,
    CheckpointArtifacts,
    CheckpointCommitPlan,
    CheckpointRecord,
    CheckpointRequest,
    ObjectVerification,
    VerifiedArtifact,
    artifact_json_schema,
)
from strange_physics.contracts import Message
from strange_physics.control_contracts import checkpoint_request_sha256
from strange_physics.research_contracts import message_sha256

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "contracts/artifacts.examples.json").read_text())
MODELS = {model.__name__: model for model in ARTIFACT_MODELS}


def parse[M: Message](model: type[M], value: Any) -> M:
    return model.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("name", tuple(MODELS))
def test_positive_examples(name: str) -> None:
    assert parse(MODELS[name], EXAMPLES["valid"][name])


@pytest.mark.parametrize("case", EXAMPLES["schema_negative"] + EXAMPLES["runtime_negative"])
def test_negative_examples(case: dict[str, Any]) -> None:
    value = copy.deepcopy(EXAMPLES["valid"][case["model"]])
    value[case["field"]] = case["value"]
    with pytest.raises(ValidationError):
        parse(MODELS[case["model"]], value)


def test_generated_schema_and_public_boundary() -> None:
    assert artifact_json_schema() == json.loads(
        (ROOT / "contracts/artifacts.schema.json").read_text()
    )
    assert {model.__name__ for model in PUBLIC_MODELS} == {"ArtifactRef", "CheckpointRequest"}
    request = parse(CheckpointRequest, EXAMPLES["valid"]["CheckpointRequest"])
    text = request.model_dump_json()
    for private in ("namespace_id", "object_key", "verifier_id", "visibility", "checked_at"):
        assert private not in text
    with pytest.raises(ValidationError):
        parse(ArtifactRef, EXAMPLES["valid"]["ArtifactRef"] | {"namespace_id": "secret"})


def test_ordered_full_body_digest_preserves_existing_profile() -> None:
    request = parse(CheckpointRequest, EXAMPLES["valid"]["CheckpointRequest"])
    assert message_sha256(request) == checkpoint_request_sha256(
        request.checkpoint,
        request.runtime_image_sha256,
        tuple(ref.model_dump(mode="json") for ref in request.artifacts),
    )
    other = request.artifacts[0].model_dump(mode="json") | {"artifact_id": "artifact-2"}
    first = request.model_dump(mode="json") | {
        "artifacts": [*request.model_dump(mode="json")["artifacts"], other]
    }
    second = first | {"artifacts": list(reversed(first["artifacts"]))}
    assert message_sha256(parse(CheckpointRequest, first)) != message_sha256(
        parse(CheckpointRequest, second)
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation", "2"),
        ("sha256", "b" * 64),
        ("size_bytes", 13),
        ("media_type", "application/octet-stream"),
        (
            "locator",
            {"provider": "gcs", "namespace_id": "other", "object_key": "ws-1/run-1/artifact-1"},
        ),
    ],
)
def test_actual_object_evidence_joins_every_identity_field(field: str, value: Any) -> None:
    evidence = copy.deepcopy(EXAMPLES["valid"]["VerifiedArtifact"])
    evidence["verification"][field] = value
    with pytest.raises(ValidationError):
        parse(VerifiedArtifact, evidence)


@pytest.mark.parametrize("field,value", [("workspace_id", "other"), ("run_id", "other")])
def test_batch_joins_object_tenant_and_run(field: str, value: str) -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointArtifacts"])
    data["objects"][0]["record"][field] = value
    with pytest.raises(ValidationError):
        parse(CheckpointArtifacts, data)


def test_observation_time_cannot_follow_current_verification_batch() -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointArtifacts"])
    data["objects"][0]["verification"]["observed_at"] = data["checked_at"] + 1
    with pytest.raises(ValidationError):
        parse(CheckpointArtifacts, data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_sha256", "b" * 64),
        ("objects", []),
        ("run_id", "other"),
    ],
)
def test_committed_history_rejects_partial_or_foreign_verification(field: str, value: Any) -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointRecord"])
    data["artifacts"][field] = value
    with pytest.raises(ValidationError):
        parse(CheckpointRecord, data)


@pytest.mark.parametrize("state", ["uploading", "tombstoned", "deleted"])
def test_committed_history_rejects_unavailable_object(state: str) -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointRecord"])
    data["artifacts"]["objects"][0]["record"]["state"] = state
    with pytest.raises(ValidationError):
        parse(CheckpointRecord, data)


@pytest.mark.parametrize("visibility", ["workspace-private", "evaluator-only", "public"])
def test_checkpoint_state_is_explicitly_agent_visible(visibility: str) -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointRecord"])
    data["artifacts"]["objects"][0]["record"]["visibility"] = visibility
    with pytest.raises(ValidationError):
        parse(CheckpointRecord, data)


@pytest.mark.parametrize(
    "projection,field,value",
    [
        ("head", "index", 1),
        ("head", "request_sha256", "b" * 64),
        ("outbox", "run_id", "other"),
        ("outbox", "record_sha256", "b" * 64),
        ("outbox", "request_sha256", "b" * 64),
        ("outbox", "checkpoint_revision", 2),
    ],
)
def test_atomic_proposal_rejects_inconsistent_projection(
    projection: str, field: str, value: Any
) -> None:
    data = copy.deepcopy(EXAMPLES["valid"]["CheckpointCommitPlan"])
    data[projection][field] = value
    with pytest.raises(ValidationError):
        parse(CheckpointCommitPlan, data)


def test_verification_is_explicitly_not_a_storage_reader() -> None:
    proof = parse(ObjectVerification, EXAMPLES["valid"]["ObjectVerification"])
    assert proof.completeness == "complete"
    assert "does not do I/O" in (ObjectVerification.__doc__ or "")


def test_draft_checkpoint_route_uses_public_artifact_schema_only() -> None:
    api = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    assert api["components"]["schemas"]["CheckpointRequest"] == {
        "$ref": "../artifacts.schema.json#/$defs/CheckpointRequest"
    }
