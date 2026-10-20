"""Reviewed VAL1 inventory and byte vectors, before bundle generation."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
from typing import Any, Protocol, cast

import pytest
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import (
    LinearSpringModel,
    PredictionRequest,
    PredictionResponse,
    SpringFitInput,
    validate_model_for_fit,
    validate_prediction_response,
)
from strange_physics.serialization import canonical_json


class SchemaValidator(Protocol):
    def is_valid(self, instance: object) -> bool: ...

    def validate(self, instance: object) -> None: ...


class SchemaValidatorFactory(Protocol):
    def __call__(self, schema: dict[str, Any], *, registry: Any = ...) -> SchemaValidator: ...

    def check_schema(self, schema: dict[str, Any]) -> None: ...


# The locked validator has no bundled typing. Describe only the exercised API;
# no additional stub dependency or global untyped-import exemption is needed.
Draft202012Validator = cast(
    SchemaValidatorFactory,
    importlib.import_module("jsonschema").Draft202012Validator,
)


ROOT = Path(__file__).resolve().parents[1]
TOOLING = ROOT / "contracts/tooling"
MANIFEST: dict[str, Any] = json.loads((TOOLING / "manifest.json").read_text())
FIXTURES: dict[str, Any] = json.loads((TOOLING / "fixtures.json").read_text())
ROOTS = {entry["id"]: entry for entry in MANIFEST["roots"]}
CASES = {entry["id"]: entry for entry in FIXTURES["cases"]}


def document(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / path).read_text()))


def pointer(value: Any, fragment: str) -> Any:
    assert fragment.startswith("/")
    for token in fragment[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validator(reference: str) -> SchemaValidator:
    registry: Any = Registry()
    for source in MANIFEST["sources"]:
        path = ROOT / source["path"]
        value = document(source["path"])
        resource = Resource.from_contents(value, default_specification=DRAFT202012)
        registry = registry.with_resource(path.as_uri(), resource)
        if "$id" in value:
            registry = registry.with_resource(value["$id"], resource)
    path, fragment = reference.split("#", 1)
    uri = (ROOT / path).as_uri() + "#" + fragment
    return Draft202012Validator({"$ref": uri}, registry=registry)


def model(case: dict[str, Any]) -> type[Message]:
    module, name = ROOTS[case["root"]]["runtime_model"].split(":")
    result = getattr(importlib.import_module(module), name)
    assert isinstance(result, type) and issubclass(result, Message)
    return result


def raw(case: dict[str, Any]) -> bytes:
    return base64.b64decode(case["raw_base64"], validate=True)


def strict_value(payload: bytes) -> Any:
    """Independent syntax expectation; actual bounded ingress is tested separately."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def finite(text: str) -> float:
        number = float(text)
        if not math.isfinite(number):
            raise ValueError("nonfinite number")
        return number

    def constant(text: str) -> None:
        raise ValueError("nonstandard constant")

    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=pairs,
        parse_float=finite,
        parse_constant=constant,
    )


def test_manifest_schema_and_version() -> None:
    schema = document("contracts/tooling/manifest.schema.json")
    Draft202012Validator.check_schema(schema)
    check = Draft202012Validator(schema)
    check.validate(MANIFEST)
    for field, value in [
        ("schema_version", "strange-physics.contract-tooling.v999"),
        ("generation_profile", "unknown"),
        ("extra", True),
    ]:
        altered = copy.deepcopy(MANIFEST)
        altered[field] = value
        assert not check.is_valid(altered)


def test_fixture_schema_and_identity_links() -> None:
    schema = document("contracts/tooling/fixtures.schema.json")
    Draft202012Validator.check_schema(schema)
    check = Draft202012Validator(schema)
    check.validate(FIXTURES)
    altered = copy.deepcopy(FIXTURES)
    altered["schema_version"] = "strange-physics.contract-fixtures.v999"
    assert not check.is_valid(altered)
    altered = copy.deepcopy(FIXTURES)
    altered["cases"][0]["expected"]["silent_skip"] = True
    assert not check.is_valid(altered)
    for case in FIXTURES["cases"]:
        assert case["root"] in ROOTS
        expected = case["expected"]
        assert expected["bounded_typed"] == (expected["strict_json"] and expected["typed_json"])
        assert (expected["canonical_base64"] is None) == (expected["canonical_sha256"] is None)
        if case["cross_message"] is not None:
            assert case["cross_message"]["other_case"] in CASES


def test_manifest_exact_sources_roots_and_route_inventory() -> None:
    assert len(ROOTS) == len(MANIFEST["roots"])
    assert len({entry["path"] for entry in MANIFEST["sources"]}) == len(MANIFEST["sources"])
    sources = {entry["path"] for entry in MANIFEST["sources"]}
    for source in MANIFEST["sources"]:
        path = source["path"]
        assert path.startswith("contracts/") and "/draft/" not in path
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == source["sha256"]
    for entry in MANIFEST["roots"]:
        path, fragment = entry["schema"].split("#", 1)
        assert path in sources
        assert pointer(document(path), fragment)
        assert entry["audience"] in MANIFEST["audiences"]
        assert entry["schema"] not in MANIFEST["excluded_roots"]
        module, name = entry["runtime_model"].split(":")
        assert issubclass(getattr(importlib.import_module(module), name), Message)
    actual = []
    for source in MANIFEST["sources"]:
        if source["kind"] != "static-openapi":
            continue
        api = document(source["path"])
        for path, methods in sorted(api["paths"].items()):
            for method, operation in sorted(methods.items()):
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                actual.append(
                    {
                        "source": source["path"],
                        "path": path,
                        "method": method,
                        "operation_id": operation["operationId"],
                        "security": operation.get("security", api.get("security", [])),
                    }
                )
    assert actual == MANIFEST["routes"]
    assert len(actual) == 51
    assert (
        hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
        == MANIFEST["toolchain"]["lock_sha256"]
    )


def test_audience_boundaries_are_not_blanket_agent_grants() -> None:
    for key, audience in {
        "research.EvaluationReport": "development-evaluator",
        "core.Checkpoint": "agent-checkpoint",
        "world.CreateWorldVersionRequest": "world-author",
        "world.GrantedWorldDefinition": "world-grantee",
        "invitation.InvitationIssued": "credential-once",
        "service.ServiceKeyIssuedResponse": "credential-once",
        "service.ServiceKeyReplayResponse": "owner-management",
        "session.SessionBootstrap": "browser-auth",
        "control.Operation": "control-client-output",
        "execution.PackageManifest": "package-submission",
        "model-registration.SubmitModelRequest": "worker-submission",
    }.items():
        assert ROOTS[key]["audience"] == audience
        assert ROOTS[key]["agent_safe_structure"] is False
    assert ROOTS["world.WorldVersionView"]["agent_safe_structure"] is True
    assert ROOTS["web.EventDelivery"]["agent_safe_structure"] is True


@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda case: case["id"])
def test_shared_byte_vector_layers(case: dict[str, Any]) -> None:
    payload = raw(case)
    expected = case["expected"]
    assert len(payload) <= FIXTURES["bounds"]["max_bytes"]
    assert hashlib.sha256(payload).hexdigest() == case["raw_sha256"]
    if expected["strict_json"]:
        value = strict_value(payload)
    else:
        with pytest.raises((ValueError, UnicodeError)):
            strict_value(payload)
        assert expected["json_schema"] is None
        value = None
    if expected["json_schema"] is not None:
        assert validator(ROOTS[case["root"]]["schema"]).is_valid(value) == expected["json_schema"]

    adapter = model(case)
    parsed = None
    if expected["typed_json"]:
        parsed = adapter.model_validate_json(payload)
    else:
        with pytest.raises(ValueError):
            adapter.model_validate_json(payload)
    if expected["bounded_typed"]:
        assert parse_bounded_json(payload, adapter, **FIXTURES["bounds"]) == parsed
    else:
        with pytest.raises(ContractViolation):
            parse_bounded_json(payload, adapter, **FIXTURES["bounds"])

    encoded = expected["canonical_base64"]
    if encoded is not None:
        assert parsed is not None
        canonical = canonical_json(parsed.model_dump(mode="json")).encode("utf-8")
        assert canonical == base64.b64decode(encoded, validate=True)
        assert hashlib.sha256(canonical).hexdigest() == expected["canonical_sha256"]
    elif parsed is not None:
        with pytest.raises(ValueError):
            canonical_json(parsed.model_dump(mode="json"))
        assert expected["canonical_sha256"] is None

    cross = case["cross_message"]
    if cross is not None:
        other = CASES[cross["other_case"]]
        with pytest.raises(ValueError):
            if cross["helper"] == "validate_model_for_fit":
                validate_model_for_fit(
                    LinearSpringModel.model_validate_json(payload),
                    SpringFitInput.model_validate_json(raw(other)),
                )
            elif cross["helper"] == "validate_prediction_response":
                validate_prediction_response(
                    PredictionRequest.model_validate_json(raw(other)),
                    PredictionResponse.model_validate_json(payload),
                )
            else:
                raise AssertionError("Unknown cross-message helper")
        assert cross["valid"] is False


@pytest.mark.parametrize("case", FIXTURES["wire_cases"], ids=lambda case: case["id"])
def test_shared_wire_schema_vectors(case: dict[str, Any]) -> None:
    assert validator(case["schema"]).is_valid(case["value"]) == case["valid"]


def test_byte_identity_relationships_and_explicit_failures() -> None:
    def digest(name: str) -> str | None:
        return cast(str | None, CASES[name]["expected"]["canonical_sha256"])

    assert len(CASES) == len(FIXTURES["cases"])
    assert digest("opaque-number-0") != digest("opaque-number-1")
    assert digest("opaque-number-1") == digest("opaque-number-2")
    assert digest("opaque-number-3") != digest("opaque-number-4")
    assert digest("typed-number-0") == digest("typed-number-1")
    assert digest("unicode-composed") == digest("unicode-escaped")
    assert CASES["unicode-composed"]["raw_sha256"] != CASES["unicode-escaped"]["raw_sha256"]
    assert digest("unicode-composed") != digest("unicode-decomposed")
    assert digest("opaque-number-8") is None
    assert CASES["all-failed-fit-input"]["expected"]["json_schema"] is True
    assert CASES["all-failed-fit-input"]["expected"]["typed_json"] is False
