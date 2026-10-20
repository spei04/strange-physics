"""Synthetic C1 boundary vectors; runtime lifecycle tests are separate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.service_contracts import SERVICE_MODELS, service_json_schema

ROOT = Path(__file__).resolve().parents[1]
MODELS = {model.__name__: model for model in SERVICE_MODELS}


def fixtures() -> dict[str, Any]:
    value: dict[str, Any] = json.loads((ROOT / "contracts/service.examples.json").read_text())
    return value


@pytest.mark.parametrize("name", tuple(MODELS))
def test_service_synthetic_model_round_trip(name: str) -> None:
    model = MODELS[name].model_validate_json(json.dumps(fixtures()["valid"][name]))
    assert MODELS[name].model_validate_json(model.model_dump_json()) == model


@pytest.mark.parametrize("group", ("schema_negative", "runtime_negative"))
def test_service_negative_vectors(group: str) -> None:
    vectors = fixtures()
    for case in vectors[group]:
        data = copy.deepcopy(vectors["valid"][case["model"]])
        data[case["field"]] = case["value"]
        with pytest.raises(ValidationError):
            MODELS[case["model"]].model_validate_json(json.dumps(data))


def test_published_service_schema_is_exact() -> None:
    assert json.loads((ROOT / "contracts/service.schema.json").read_text()) == service_json_schema()


def test_public_routes_use_safe_messages_and_cookie_owner_security() -> None:
    api = json.loads((ROOT / "contracts/service.openapi.json").read_text())
    operations = [operation for routes in api["paths"].values() for operation in routes.values()]
    assert len(operations) == 9
    assert len({operation["operationId"] for operation in operations}) == 9
    private = {
        "ServiceManager",
        "ServiceKeyRecord",
        "ServiceKeySet",
        "ServiceReceipt",
        "ServiceAudit",
    }
    for path, routes in api["paths"].items():
        for method, operation in routes.items():
            assert operation["security"] == [
                {"sessionCookie": [], **({"csrfHeader": []} if method == "post" else {})}
            ]
            if method == "post":
                required = {p["name"] for p in operation["parameters"] if p["required"]}
                assert {"Origin", "X-CSRF-Token", "Idempotency-Key"} <= required
                assert "requestBody" in operation
            for private_name in private:
                assert f"/{private_name}" not in json.dumps(operation)
            assert path.startswith("/v1/workspaces/{workspace_id}/service-principals")
