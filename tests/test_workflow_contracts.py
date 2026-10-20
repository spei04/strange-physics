from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.workflow_contracts import WORKFLOW_MODELS, workflow_json_schema

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/workflow.examples.json").read_text())


@pytest.mark.parametrize("model", WORKFLOW_MODELS)
def test_workflow_artifact_round_trip_and_extra_rejection(model: type[Message]) -> None:
    data = copy.deepcopy(FIXTURES["valid"][model.__name__])
    assert model.model_validate_json(json.dumps(data)).model_dump(mode="json") == data
    data["hidden_extra"] = True
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("group", ["schema_negative", "runtime_negative"])
def test_workflow_negative_vectors(group: str) -> None:
    models = {m.__name__: m for m in WORKFLOW_MODELS}
    for fixture in FIXTURES[group]:
        data = copy.deepcopy(FIXTURES["valid"][fixture["model"]])
        data[fixture["field"]] = fixture["value"]
        with pytest.raises(ValidationError):
            models[fixture["model"]].model_validate_json(json.dumps(data))


def test_workflow_schema_matches_source() -> None:
    assert (
        json.loads((ROOT / "contracts/workflow.schema.json").read_text()) == workflow_json_schema()
    )


@pytest.mark.parametrize(
    "case", ["prefix", "configuration", "empty_result", "submission", "request"]
)
def test_actual_fit_and_prediction_inputs_cannot_be_substituted(case: str) -> None:
    name = (
        "SpringFitArtifact"
        if case in {"prefix", "configuration", "empty_result"}
        else ("SpringPredictionArtifact")
    )
    data = copy.deepcopy(FIXTURES["valid"][name])
    if case == "prefix":
        data["observations"]["run_id"] = "different-run"
    elif case == "configuration":
        data["fit_input"]["fit_config_sha256"] = "f" * 64
    elif case == "empty_result":
        data["result"] = None
    elif case == "submission":
        data["submissions"]["entries"][0]["probe_id"] = "other-probe"
    else:
        data["protocol"]["probes"][0]["request_sha256"] = "f" * 64
    model = next(m for m in WORKFLOW_MODELS if m.__name__ == name)
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field", ["maximum_position_rmse", "target_passed", "probes"])
def test_score_summary_cannot_hide_a_probe_or_change_its_result(field: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["SpringScoreArtifact"])
    data[field] = {"maximum_position_rmse": 5.0, "target_passed": False, "probes": []}[field]
    model = next(m for m in WORKFLOW_MODELS if m.__name__ == "SpringScoreArtifact")
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("name", ["../bad.json", "bad.json\n", "completion.json"])
def test_completion_rejects_unsafe_or_recursive_output_names(name: str) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["StageCompletion"])
    data["files"][0]["name"] = name
    model = next(m for m in WORKFLOW_MODELS if m.__name__ == "StageCompletion")
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))
