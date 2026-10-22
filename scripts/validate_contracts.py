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

    native = json.loads((ROOT / "native-spring.examples.json").read_text())
    for name, fixture in native["valid"].items():
        check(f"native-spring.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in native[group]:
            value = copy.deepcopy(native["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"native-spring.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    native_prediction = json.loads((ROOT / "native-prediction.examples.json").read_text())
    for name, fixture in native_prediction["valid"].items():
        check(f"native-prediction.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in native_prediction[group]:
            value = copy.deepcopy(native_prediction["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"native-prediction.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    native_scoring = json.loads((ROOT / "native-scoring.examples.json").read_text())
    for name, fixture in native_scoring["valid"].items():
        check(f"native-scoring.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in native_scoring[group]:
            value = copy.deepcopy(native_scoring["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"native-scoring.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    native_classical = json.loads((ROOT / "native-classical.examples.json").read_text())
    for name, fixture in native_classical["valid"].items():
        check(f"native-classical.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in native_classical[group]:
            value = copy.deepcopy(native_classical["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"native-classical.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    study = json.loads((ROOT / "study.examples.json").read_text())
    for name, fixture in study["valid"].items():
        check(f"study.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in study[group]:
            value = copy.deepcopy(study["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"study.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    web = json.loads((ROOT / "web.examples.json").read_text())
    for name, fixture in web["valid"].items():
        check(f"web.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in web[group]:
            value = copy.deepcopy(web["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(f"web.schema.json#/$defs/{fixture['model']}", value, group == "runtime_negative")
    for value in web["events"]:
        check("web.schema.json#/$defs/RunEvent", value)
        wrong = copy.deepcopy(value)
        wrong["type"] = (
            "checkpoint.committed"
            if value["type"] != "checkpoint.committed"
            else "run.state_changed"
        )
        check("web.schema.json#/$defs/RunEvent", wrong, False)
    web_api = documents[ROOT / "web.openapi.json"]
    for path, routes in web_api["paths"].items():
        escaped = path.replace("~", "~0").replace("/", "~1")
        for method, operation in routes.items():
            for index, parameter in enumerate(operation["parameters"]):
                reference = f"web.openapi.json#/paths/{escaped}/{method}/parameters/{index}/schema"
                good = (
                    ["1", "18446744073709551616"]
                    if parameter["name"] == "generation"
                    else ["token", "A" * 64]
                )
                bad = ["", "a\n", "a\r", "a\x00", "a" * 65]
                for value in good:
                    check(reference, value)
                for value in bad:
                    check(reference, value, False)
            retry_reference = (
                f"web.openapi.json#/paths/{escaped}/{method}"
                "/responses/429/headers/Retry-After/schema"
            )
            for value in ["0", "1", "9999999999"]:
                check(retry_reference, value)
            for value in ["1\n", "0\n", "1\r\n", "-1", "+1", "01", "1e2", "١"]:
                check(retry_reference, value, False)
            if "410" in operation["responses"]:
                check("web.schema.json#/$defs/ResyncRequired", web["valid"]["ResyncRequired"])

    world = json.loads((ROOT / "world.examples.json").read_text())
    for name, fixture in world["valid"].items():
        check(f"world.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in world[group]:
            value = copy.deepcopy(world["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"world.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )
    for name in ["renewal_commit", "revocation_commit"]:
        check("world.schema.json#/$defs/PreviewMutationCommit", world[name])

    check("control.schema.json#/$defs/Error", world["service_unavailable"])
    world_api = documents[ROOT / "world.openapi.json"]
    first_world = world["valid"]["CreateWorldVersionRequest"]
    append_world = copy.deepcopy(first_world)
    append_world.update(expected_head_revision=1, expected_version_id="world-version-1")
    for name, good, wrong in [
        ("InitialWorldRequest", first_world, append_world),
        ("AppendWorldRequest", append_world, first_world),
    ]:
        check(f"world.openapi.json#/components/schemas/{name}", good)
        check(f"world.openapi.json#/components/schemas/{name}", wrong, False)
    path_values = json.loads((ROOT / "session.examples.json").read_text())["path_identifiers"]
    key_values = json.loads((ROOT / "control.examples.json").read_text())["idempotency_keys"]
    for path, routes in world_api["paths"].items():
        escaped = path.replace("~", "~0").replace("/", "~1")
        for method, operation in routes.items():
            unavailable = operation["responses"]["503"]["content"]["application/json"]["schema"]
            check(unavailable["$ref"], world["service_unavailable"])
            response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
            response_name = response_schema["$ref"].rsplit("/", 1)[-1]
            check(response_schema["$ref"], world["valid"][response_name])
            for index, parameter in enumerate(operation["parameters"]):
                reference = (
                    f"world.openapi.json#/paths/{escaped}/{method}/parameters/{index}/schema"
                )
                values = (
                    key_values
                    if parameter["name"] == "Idempotency-Key"
                    else path_values
                    if parameter["in"] == "path" or parameter["name"] == "grant_id"
                    else None
                )
                if values is not None:
                    for group, items in values.items():
                        for item in items:
                            check(reference, item, group == "valid")
                elif parameter["name"] == "page_size":
                    for value in (1, 128):
                        check(reference, value)
                    for value in (0, 129, True):
                        check(reference, value, False)

    registration = json.loads((ROOT / "model-registration.examples.json").read_text())
    for name, fixture in registration["valid"].items():
        check(f"model-registration.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in registration[group]:
            value = copy.deepcopy(registration["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"model-registration.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

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

    fitting = json.loads((ROOT / "fitting.examples.json").read_text())
    for name, fixture in fitting["valid"].items():
        check(f"fitting.schema.json#/$defs/{name}", fixture)
    check("research.schema.json#/$defs/SpringFitInput", fitting["input"])
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in fitting[group]:
            value = copy.deepcopy(fitting["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"fitting.schema.json#/$defs/{fixture['model']}", value, group == "runtime_negative"
            )

    prediction = json.loads((ROOT / "prediction.examples.json").read_text())
    for name, fixture in prediction["valid"].items():
        check(f"prediction.schema.json#/$defs/{name}", fixture)
    check("research.schema.json#/$defs/LinearSpringModel", prediction["model"])
    check("research.schema.json#/$defs/PredictionRequest", prediction["request"])
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in prediction[group]:
            value = copy.deepcopy(prediction["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"prediction.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    evaluation = json.loads((ROOT / "evaluation.examples.json").read_text())
    for name, fixture in evaluation["valid"].items():
        check(f"evaluation.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in evaluation[group]:
            value = copy.deepcopy(evaluation["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"evaluation.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    workflow = json.loads((ROOT / "workflow.examples.json").read_text())
    for name, fixture in workflow["valid"].items():
        check(f"workflow.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in workflow[group]:
            value = copy.deepcopy(workflow["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"workflow.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

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

    invitations = json.loads((ROOT / "invitation.examples.json").read_text())
    for name, fixture in invitations["valid"].items():
        check(f"invitation.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in invitations[group]:
            value = copy.deepcopy(invitations["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"invitation.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )
    invitation_api = documents[ROOT / "invitation.openapi.json"]
    for path, routes in invitation_api["paths"].items():
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
                        f"invitation.openapi.json#/paths/{escaped}/{method}"
                        f"/parameters/{index}/schema"
                    )
                    for group, items in values.items():
                        for item in items:
                            check(reference, item, group == "valid")

    linking = json.loads((ROOT / "linking.examples.json").read_text())
    for name, fixture in linking["valid"].items():
        check(f"linking.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in linking[group]:
            value = copy.deepcopy(linking["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"linking.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    check("linking.schema.json#/$defs/LinkError", linking["rate_limit"]["body"])
    rate_schema = (
        "linking.openapi.json#/paths/~1v1~1identity-links/post/responses/429"
        "/content/application~1json/schema"
    )
    check(rate_schema, linking["rate_limit"]["body"])
    check(rate_schema, linking["rate_limit"]["body"] | {"code": "proof_rejected"}, False)

    services = json.loads((ROOT / "service.examples.json").read_text())
    for name, fixture in services["valid"].items():
        check(f"service.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in services[group]:
            value = copy.deepcopy(services["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"service.schema.json#/$defs/{fixture['model']}", value, group == "runtime_negative"
            )

    run_credentials = json.loads((ROOT / "run-credentials.examples.json").read_text())
    for name, fixture in run_credentials["valid"].items():
        check(f"run-credentials.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in run_credentials[group]:
            value = copy.deepcopy(run_credentials["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"run-credentials.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    artifacts = json.loads((ROOT / "artifacts.examples.json").read_text())
    for name, fixture in artifacts["valid"].items():
        check(f"artifacts.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in artifacts[group]:
            value = copy.deepcopy(artifacts["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"artifacts.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    execution = json.loads((ROOT / "execution.examples.json").read_text())
    for name, fixture in execution["valid"].items():
        check(f"execution.schema.json#/$defs/{name}", fixture)
    for group in ["schema_negative", "runtime_negative"]:
        for fixture in execution[group]:
            value = copy.deepcopy(execution["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            check(
                f"execution.schema.json#/$defs/{fixture['model']}",
                value,
                group == "runtime_negative",
            )

    for value in execution["normal_completion"]:
        check("execution.schema.json#/$defs/WorkerTerminationRequest", value)

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
