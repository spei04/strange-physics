"""Validate synthetic fixtures against the published schemas without network access.

Structural JSON Schema checks complement (and never replace) runtime and
cross-message tests. Draft fixtures remain drafts, not scientific evidence.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1] / "contracts"


def main() -> None:
    documents = {
        p: json.loads(p.read_text())
        for p in ROOT.rglob("*.json")
        if (p.name.endswith(".schema.json") or p.name.endswith("openapi.json"))
    }
    registry: Any = Registry()
    for path, document in documents.items():
        resource = Resource.from_contents(document, default_specification=DRAFT202012)
        registry = registry.with_resource(path.as_uri(), resource)
        if "$id" in document:
            registry = registry.with_resource(document["$id"], resource)
        if not path.name.endswith("openapi.json"):
            Draft202012Validator.check_schema(document)
        else:
            for schema in document["components"]["schemas"].values():
                Draft202012Validator.check_schema(schema)

    count = 0

    def check(reference: str, value: Any, valid: bool = True) -> None:
        nonlocal count
        filename, fragment = reference.split("#", 1)
        uri = (ROOT / filename).resolve().as_uri() + "#" + fragment
        validator = Draft202012Validator({"$ref": uri}, registry=registry)
        errors = list(validator.iter_errors(value))
        if bool(errors) == valid:
            raise ValueError(f"Unexpected schema result for {reference}: {errors[:1]}")
        count += 1

    legacy = json.loads((ROOT / "examples.json").read_text())
    for group in ["valid", "invalid", "runtime_invalid"]:
        for fixture in legacy[group]:
            check(fixture["schema"], fixture["value"], group != "invalid")

    research = json.loads((ROOT / "research.examples.json").read_text())
    control = json.loads((ROOT / "control.examples.json").read_text())
    for name, fixture in research["valid"].items():
        check(f"research.schema.json#/$defs/{name}", fixture)
    for name, fixture in control["valid"].items():
        check(f"control.schema.json#/$defs/{name}", fixture)
    for fixture in control["schema_negative"]:
        value = copy.deepcopy(control["valid"][fixture["model"]])
        value[fixture["field"]] = fixture["value"]
        check(f"control.schema.json#/$defs/{fixture['model']}", value, False)

    sessions = json.loads((ROOT / "session.examples.json").read_text())
    for name, fixture in sessions["valid"].items():
        check(f"session.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in sessions[group]:
            value = copy.deepcopy(sessions["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"session.schema.json#/$defs/{fixture['model']}", value, group == "runtime_negative"
            )

    workspaces = json.loads((ROOT / "workspace.examples.json").read_text())
    for name, fixture in workspaces["valid"].items():
        check(f"workspace.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in workspaces[group]:
            value = copy.deepcopy(workspaces["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"workspace.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )
    check("control.schema.json#/$defs/Error", workspaces["freshness_failure"]["body"])
    workspace_api = documents[ROOT / "workspace.openapi.json"]
    for path, routes in workspace_api["paths"].items():
        for method, operation in routes.items():
            escaped = path.replace("~", "~0").replace("/", "~1")
            for index, parameter in enumerate(operation["parameters"]):
                values = (
                    control["idempotency_keys"]
                    if parameter["name"] == "Idempotency-Key"
                    else sessions["path_identifiers"]
                    if parameter["in"] == "path"
                    else None
                )
                if values is not None:
                    reference = (
                        f"workspace.openapi.json#/paths/{escaped}/{method}"
                        f"/parameters/{index}/schema"
                    )
                    for group, items in values.items():
                        for item in items:
                            check(reference, item, group == "valid")

    for fixture in sessions["workspace_session_failures"]:
        check("control.schema.json#/$defs/Error", fixture["output"])

    for group, values in sessions["path_identifiers"].items():
        for value in values:
            check(
                "session.openapi.json#/paths/~1v1~1auth~1logins~1{transaction_id}"
                "/get/parameters/0/schema",
                value,
                group == "valid",
            )

    boundary_paths = {
        "identifiers": [
            "core.schema.json#/$defs/ParticleInitial/properties/id",
            "research.schema.json#/$defs/ParticleInitial/properties/id",
            "control.schema.json#/$defs/VerifiedCredential/properties/principal_id",
        ],
        "digests": [
            "core.schema.json#/$defs/ObservationBundle/properties/engine_fingerprint",
            "research.schema.json#/$defs/LinearSpringModel/properties/observation_sha256",
            "control.schema.json#/$defs/Operation/properties/request_sha256",
        ],
    }
    for kind, references in boundary_paths.items():
        for reference in references:
            for group, values in research["boundary_values"][kind].items():
                for value in values:
                    check(reference, value, group == "valid")

    openapi = documents[ROOT / "draft/openapi.json"]
    for path, routes in openapi["paths"].items():
        if "post" not in routes:
            continue
        parameters = routes["post"].get("parameters", [])
        for index, parameter in enumerate(parameters):
            if parameter.get("name") != "Idempotency-Key":
                continue
            escaped = path.replace("~", "~0").replace("/", "~1")
            reference = f"draft/openapi.json#/paths/{escaped}/post/parameters/{index}/schema"
            for group, values in control["idempotency_keys"].items():
                for value in values:
                    check(reference, value, group == "valid")

    # Resolve every reference, including schema branches that current examples do not exercise.
    def visit(node: Any, base_uri: str) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                registry.resolver(base_uri).lookup(node["$ref"])
            for value in node.values():
                visit(value, base_uri)
        elif isinstance(node, list):
            for value in node:
                visit(value, base_uri)

    for path, document in documents.items():
        visit(document, path.as_uri())
    print(f"{count} external JSON Schema fixture checks passed; all references resolve.")


if __name__ == "__main__":
    main()
