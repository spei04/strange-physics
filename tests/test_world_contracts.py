"""WORLD1 shape/codec/recovery joins; these are not live authorization tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from strange_physics import world_contracts as w
from strange_physics import world_preview_contracts as p
from strange_physics.contracts import Message
from strange_physics.research_contracts import message_sha256
from strange_physics.worlds import WorldDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "contracts/world.examples.json").read_text())
MODELS = {model.__name__: model for model in (*w.WORLD_MODELS, *p.PREVIEW_MODELS)}


def parse(name: str, value: Any) -> Message:
    return MODELS[name].model_validate_json(json.dumps(value))


def fixture(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], copy.deepcopy(FIXTURES["valid"][name]))


@pytest.mark.parametrize("name", sorted(MODELS))
def test_examples_round_trip(name: str) -> None:
    value = parse(name, FIXTURES["valid"][name])
    assert value.model_dump(mode="json") == FIXTURES["valid"][name]


@pytest.mark.parametrize("case", FIXTURES["schema_negative"] + FIXTURES["runtime_negative"])
def test_negative_examples(case: dict[str, Any]) -> None:
    value = fixture(case["model"])
    value[case["field"]] = case["value"]
    with pytest.raises(ValidationError):
        parse(case["model"], value)


@pytest.mark.parametrize("seed", [0, 2**53 - 1, 2**53, 2**53 + 1, 2**64 - 1])
@pytest.mark.parametrize(
    "law",
    [
        {"kind": "spring", "parameters": {}},
        {"kind": "spring", "parameters": {"linear": 0.0, "cubic": 0.0}},
        {"kind": "radial", "parameters": {"strength": -0.0, "exponent": 1.5}},
        {"kind": "velocity", "parameters": {"transverse": -3.0}},
    ],
)
def test_lossless_core_browser_core(seed: int, law: dict[str, Any]) -> None:
    data = copy.deepcopy(FIXTURES["core_definition"])
    data.update(noise_seed=seed, initial_law=law)
    core = WorldDefinition.model_validate_json(json.dumps(data))
    browser = w.BrowserWorldDefinition.from_core(core)
    assert browser.noise_seed == str(seed)
    assert browser.to_core().model_dump_json() == core.model_dump_json()
    assert message_sha256(browser.to_core()) == message_sha256(core)
    assert browser.initial_law.parameters == law["parameters"]
    assert set(browser.initial_law.parameters) == set(law["parameters"])


def test_supported_changed_law_preserves_schedule_and_presence() -> None:
    data = copy.deepcopy(FIXTURES["core_definition"])
    data.update(changed_law={"kind": "velocity", "parameters": {}}, change_after=3)
    core = WorldDefinition.model_validate_json(json.dumps(data))
    browser = w.BrowserWorldDefinition.from_core(core)
    assert browser.to_core().model_dump_json() == core.model_dump_json()
    assert browser.changed_law is not None and browser.changed_law.parameters == {}
    at_calibration = w.BrowserWorldDefinition.model_validate(
        browser.model_dump() | {"change_after": 2}
    )
    assert at_calibration.to_core().change_after == core.space.calibration_experiments
    for change_after in (1, 6):
        with pytest.raises(ValidationError):
            w.BrowserWorldDefinition.model_validate(
                browser.model_dump() | {"change_after": change_after}
            )


@pytest.mark.parametrize(
    "law",
    [
        {"kind": "unknown", "parameters": {}},
        {"kind": "spring", "parameters": {"linear": 4.1}},
        {"kind": "radial", "parameters": {"softening": 0.0}},
        {"kind": "velocity", "parameters": {"drag": None}},
        {"kind": "spring", "parameters": {"linear": True}},
    ],
)
def test_private_core_definition_does_not_bypass_supported_profile(law: dict[str, Any]) -> None:
    value = fixture("WorldVersionRecord")
    value["definition"]["initial_law"] = law
    with pytest.raises(ValidationError):
        parse("WorldVersionRecord", value)


def second_version() -> dict[str, Any]:
    old = fixture("WorldVersionCommit")
    new = copy.deepcopy(old)
    new["receipt_id"] = "world-receipt-2"
    new["scope"].update(world_id="world-1", key="synthetic-next-world")
    new["request"].update(expected_version_id="world-version-1", expected_head_revision=1)
    new["request_sha256"] = message_sha256(
        w.CreateWorldVersionRequest.model_validate_json(json.dumps(new["request"]))
    )
    new["parent"], new["before"] = old["version"], old["result"]["head"]
    view = new["version"]["view"]
    view.update(
        version_id="world-version-2",
        version_number=2,
        parent_version_id="world-version-1",
        created_at=901,
    )
    new["result"] = {
        "version": copy.deepcopy(view),
        "head": {
            "workspace_id": view["workspace_id"],
            "world_id": view["world_id"],
            "version_id": view["version_id"],
            "revision": 2,
            "changed_at": 901,
        },
    }
    new["committed_at"] = 901
    new["receipt_expires_at"] = 4501
    return new


def test_initial_allocated_id_and_append_are_distinct_scopes() -> None:
    initial = parse("WorldVersionCommit", fixture("WorldVersionCommit"))
    assert isinstance(initial, w.WorldVersionCommit)
    assert initial.scope.world_id is None
    assert initial.version.view.world_id == "world-1"
    appended = parse("WorldVersionCommit", second_version())
    assert isinstance(appended, w.WorldVersionCommit)
    assert appended.scope.world_id == initial.version.view.world_id
    for value in (fixture("WorldVersionCommit"), second_version()):
        value["scope"]["world_id"] = "world-1" if value["scope"]["world_id"] is None else None
        with pytest.raises(ValidationError):
            parse("WorldVersionCommit", value)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_parent",
        "missing_head",
        "wrong_parent",
        "cross_world",
        "future_parent",
        "stale_head",
        "wrong_request",
        "official",
        "wrong_author",
        "wrong_result",
    ],
)
def test_version_commit_closure(mutation: str) -> None:
    value = second_version()
    if mutation == "missing_parent":
        value["parent"] = None
    elif mutation == "missing_head":
        value["before"] = None
    elif mutation == "wrong_parent":
        value["parent"]["view"]["version_id"] = "unrelated-parent"
    elif mutation == "cross_world":
        value["parent"]["view"]["world_id"] = "other-world"
    elif mutation == "future_parent":
        value["parent"]["view"]["created_at"] = 902
        value["before"]["changed_at"] = 902
    elif mutation == "stale_head":
        value["before"]["version_id"] = "other-version"
    elif mutation == "wrong_request":
        value["request"]["title"] = "Different"
        value["request_sha256"] = message_sha256(
            w.CreateWorldVersionRequest.model_validate_json(json.dumps(value["request"]))
        )
    elif mutation == "official":
        value["version"]["classification"] = "official_blind"
    elif mutation == "wrong_author":
        value["version"]["author"]["principal_id"] = "different-author"
    else:
        value["result"]["version"]["title"] = "Different"
    with pytest.raises(ValidationError):
        parse("WorldVersionCommit", value)


@pytest.mark.parametrize("field", ["receipt", "target", "current_head", "current_commit"])
def test_partial_version_lookup_remains_representable(field: str) -> None:
    value = fixture("WorldVersionLookup")
    value[field] = None
    parsed = parse("WorldVersionLookup", value)
    assert getattr(parsed, field) is None


def preview_commit(kind: str = "renewal_commit") -> dict[str, Any]:
    return cast(dict[str, Any], copy.deepcopy(FIXTURES[kind]))


def synchronize_preview(value: dict[str, Any]) -> None:
    """Keep outer projections coherent when challenging the actual transition."""
    request_models: dict[str, type[Message]] = {
        "issue_preview": p.IssuePreviewRequest,
        "renew_preview": p.RenewPreviewRequest,
        "revoke_preview": p.RevokePreviewRequest,
    }
    value["request_sha256"] = message_sha256(
        request_models[value["request"]["operation"]].model_validate_json(
            json.dumps(value["request"])
        )
    )
    value["receipt_expires_at"] = (
        value["committed_at"] + value["policy"]["receipt_retention_seconds"]
    )
    new = p.PreviewGrantRecord.model_validate(value["after"])
    value["result"] = p.preview_metadata(new).model_dump(mode="json")


def test_issue_renew_revoke_lifecycle_and_metadata_only_result() -> None:
    issue = p.PreviewMutationCommit.model_validate_json(
        json.dumps(FIXTURES["valid"]["PreviewMutationCommit"])
    )
    renew = p.PreviewMutationCommit.model_validate_json(json.dumps(FIXTURES["renewal_commit"]))
    revoke = p.PreviewMutationCommit.model_validate_json(json.dumps(FIXTURES["revocation_commit"]))
    assert issue.after == renew.before
    assert renew.after == revoke.before
    assert issue.after.recipient == revoke.after.recipient
    assert renew.after.expires_at > issue.after.expires_at
    assert revoke.after.expires_at == renew.after.expires_at
    assert revoke.after.revoked_at == revoke.committed_at
    assert not {"definition", "definition_sha256", "noise_seed", "initial_law"} & set(
        revoke.result.model_dump()
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "expired",
        "revoked",
        "wrong_recipient",
        "new_generation",
        "new_incarnation",
        "inactive",
        "removed",
        "role_not_allowed",
        "too_long",
        "changed_version",
        "wrong_revision",
        "policy_mismatch",
        "no_world",
    ],
)
def test_preview_renewal_rejects_invalid_transition(mutation: str) -> None:
    value = preview_commit()
    if mutation == "expired":
        value["before"]["expires_at"] = value["committed_at"]
    elif mutation == "revoked":
        value["before"].update(revision=2, updated_at=1005, revoked_at=1005)
        value["request"]["expected_revision"] = 2
        value["after"]["revision"] = 3
    elif mutation == "wrong_recipient":
        value["after"]["recipient"]["principal_id"] = "other-recipient"
    elif mutation == "new_generation":
        value["recipient_at_commit"]["principal"]["generation"] += 1
    elif mutation == "new_incarnation":
        value["recipient_at_commit"]["grant"]["incarnation"] += 1
    elif mutation == "inactive":
        value["recipient_at_commit"]["principal"]["active"] = False
    elif mutation == "removed":
        value["recipient_at_commit"]["grant"]["membership"]["active"] = False
    elif mutation == "role_not_allowed":
        value["policy"]["preview_reader_roles"] = ["owner"]
        value["after"]["decision_policy_sha256"] = message_sha256(
            w.WorldPolicy.model_validate_json(json.dumps(value["policy"]))
        )
    elif mutation == "too_long":
        value["request"]["ttl_seconds"] = 901
        value["after"]["expires_at"] = value["committed_at"] + 901
    elif mutation == "changed_version":
        value["after"]["version_id"] = "other-version"
    elif mutation == "wrong_revision":
        value["request"]["expected_revision"] = 2
    elif mutation == "policy_mismatch":
        value["after"]["decision_policy_sha256"] = "f" * 64
    else:
        value["scope"]["world_id"] = None
    synchronize_preview(value)
    with pytest.raises(ValidationError):
        parse("PreviewMutationCommit", value)


@pytest.mark.parametrize("role", ["owner", "researcher", "viewer"])
def test_current_permitted_recipient_role_does_not_rebind_ancestry(role: str) -> None:
    value = preview_commit()
    value["recipient_at_commit"]["grant"]["membership"]["role"] = role
    result = p.PreviewMutationCommit.model_validate_json(json.dumps(value))
    assert result.before is not None and result.after.recipient == result.before.recipient


def test_new_owner_can_renew_without_rewriting_original_issuer() -> None:
    value = preview_commit()
    value["actor"]["principal_id"] = "new-owner"
    value["scope"]["principal_id"] = "new-owner"
    value["after"]["updated_by"]["principal_id"] = "new-owner"
    synchronize_preview(value)
    result = p.PreviewMutationCommit.model_validate_json(json.dumps(value))
    assert result.after.issued_by.principal_id == "principal-1"
    assert result.after.updated_by.principal_id == "new-owner"


@pytest.mark.parametrize("mutation", ["extends_expiry", "wrong_time", "wrong_target"])
def test_revocation_cannot_extend_or_retarget(mutation: str) -> None:
    value = preview_commit("revocation_commit")
    if mutation == "extends_expiry":
        value["after"]["expires_at"] += 1
    elif mutation == "wrong_time":
        value["committed_at"] += 1
    else:
        value["request"]["grant_id"] = "other-grant"
    synchronize_preview(value)
    with pytest.raises(ValidationError):
        parse("PreviewMutationCommit", value)


def test_official_blind_version_never_issues_preview() -> None:
    value = fixture("PreviewMutationCommit")
    value["version"]["classification"] = "official_blind"
    with pytest.raises(ValidationError):
        parse("PreviewMutationCommit", value)


@pytest.mark.parametrize(
    "mutation",
    [
        "catalog_scope",
        "catalog_definition",
        "catalog_space",
        "withdrawn",
        "catalog_future",
        "wrong_version",
        "wrong_creation_hash",
        "budget",
        "space",
    ],
)
def test_actual_world_run_selection_joins(mutation: str) -> None:
    value = fixture("WorldRunSelection")
    if mutation == "catalog_scope":
        value["catalog"]["workspace_id"] = "other-workspace"
    elif mutation == "catalog_definition":
        value["catalog"]["definition_sha256"] = "f" * 64
    elif mutation == "catalog_space":
        value["catalog"]["space_sha256"] = "f" * 64
    elif mutation == "withdrawn":
        value["catalog"]["eligible_for_new_runs"] = False
    elif mutation == "catalog_future":
        value["catalog"]["observed_at"] = value["selected_at"] + 1
    elif mutation == "wrong_version":
        value["catalog"]["version_id"] = "other-version"
    elif mutation == "wrong_creation_hash":
        value["creation_request_sha256"] = "f" * 64
    else:
        definition = value["version"]["definition"]
        if mutation == "budget":
            definition["space"]["budget"] += 1
        else:
            definition["space"]["sampling"]["duration"] = 1.5
        core = WorldDefinition.model_validate_json(json.dumps(definition))
        value["version"]["definition_sha256"] = message_sha256(core)
        value["version"]["view"]["space"] = core.space.model_dump(mode="json")
        value["catalog"]["definition_sha256"] = message_sha256(core)
        value["catalog"]["space_sha256"] = message_sha256(core.space)
    with pytest.raises(ValidationError):
        parse("WorldRunSelection", value)


def test_schema_matches_code_and_safe_closure_excludes_truth_and_private_authority() -> None:
    schema = p.world_json_schema()
    assert schema == json.loads((ROOT / "contracts/world.schema.json").read_text())
    forbidden = {
        "definition",
        "definition_sha256",
        "noise_seed",
        "initial_law",
        "changed_law",
        "change_after",
        "principal_generation",
        "grant_incarnation",
        "issued_by",
        "catalog",
        "admission",
        "identity",
        "recipient_at_commit",
    }
    visited: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            assert not forbidden.intersection(value.get("properties", {}))
            reference = value.get("$ref")
            if reference is not None and reference not in visited:
                visited.add(reference)
                walk(schema["$defs"][reference.rsplit("/", 1)[-1]])
            for key, child in value.items():
                if key != "$ref":
                    walk(child)

    for name in schema["x-agent-safe-models"]:
        walk(schema["$defs"][name])
    assert "WorldDefinition" not in {ref.rsplit("/", 1)[-1] for ref in visited}
    assert schema["x-author-input-models"] == ["CreateWorldVersionRequest"]
    assert schema["x-granted-definition-models"] == ["GrantedWorldDefinition"]


def test_schema_private_snapshots_are_not_public_requests() -> None:
    schema = p.world_json_schema()
    assert not {
        "WorldBrowserAuthority",
        "WorldActorAncestry",
        "WorldVersionRecord",
        "WorldVersionCommit",
        "WorldVersionLookup",
        "WorldRunSelection",
        "PreviewGrantRecord",
        "PreviewMutationCommit",
        "PreviewGrantLookup",
    }.intersection(schema["x-public-models"])


def test_current_authority_is_not_claimed_by_parsing_inactive_snapshots() -> None:
    value = fixture("WorldBrowserAuthority")
    value["identity"]["owner"]["principal"]["active"] = False
    context = w.WorldBrowserAuthority.model_validate_json(json.dumps(value))
    assert context.identity.owner.principal.active is False


def test_page_limits_and_duplicates() -> None:
    for name in ("WorldPage", "PreviewGrantPage"):
        value = fixture(name)
        value["items"] *= 2
        with pytest.raises(ValidationError):
            parse(name, value)
        value["items"] *= 65
        with pytest.raises(ValidationError):
            parse(name, value)


def canonical_fixture(name: str, sign: float) -> dict[str, Any]:
    value = fixture(name)

    def change_positions(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, child in obj.items():
                if key == "position" and isinstance(child, list) and child[0] == 0.0:
                    child[0] = sign
                else:
                    change_positions(child)
        elif isinstance(obj, list):
            for child in obj:
                change_positions(child)

    change_positions(value)
    record = (
        value
        if name == "WorldVersionRecord"
        else value.get("version")
        if name != "GrantedWorldDefinition"
        else None
    )
    if record is not None:
        core = WorldDefinition.model_validate_json(json.dumps(record["definition"]))
        record["definition_sha256"] = message_sha256(core)
    if name == "WorldVersionCommit":
        value["request_sha256"] = message_sha256(
            w.CreateWorldVersionRequest.model_validate_json(json.dumps(value["request"]))
        )
    elif name == "WorldRunSelection":
        version = w.WorldVersionRecord.model_validate_json(json.dumps(value["version"]))
        value["catalog"]["definition_sha256"] = version.definition_sha256
        value["catalog"]["space_sha256"] = message_sha256(version.view.space)
    return value


@pytest.mark.parametrize("sign", [0.0, -0.0])
@pytest.mark.parametrize(
    ("name", "point"),
    [
        ("WorldVersionRecord", "view"),
        ("WorldVersionCommit", "request"),
        ("WorldVersionCommit", "result"),
        ("GrantedWorldDefinition", "version"),
        ("WorldRunSelection", "admission"),
        ("WorldRunSelection", "stored_result"),
    ],
)
def test_canonical_identity_preserves_signed_zero(name: str, point: str, sign: float) -> None:
    value = canonical_fixture(name, sign)
    parse(name, value)  # Equal canonical identities are valid with either sign.
    if point == "request":
        space = value["request"]["definition"]["space"]
    elif point == "result":
        space = value["result"]["version"]["space"]
    elif point == "admission":
        space = value["admission"]["admitted_run"]["space"]
        retained_space = value["admission"]["stored_request"]["operation"]["result"]["value"][
            "space"
        ]
        retained_space["structure"]["anchors"][0]["position"][0] = -sign
    elif point == "stored_result":
        space = value["admission"]["stored_request"]["operation"]["result"]["value"]["space"]
    else:
        space = value[point]["space"]
    space["structure"]["anchors"][0]["position"][0] = -sign
    if point == "request":
        value["request_sha256"] = message_sha256(
            w.CreateWorldVersionRequest.model_validate_json(json.dumps(value["request"]))
        )
    with pytest.raises(ValidationError):
        parse(name, value)


@pytest.mark.parametrize("observed_at", [899, 900, 901])
def test_catalog_observation_cannot_precede_its_version(observed_at: int) -> None:
    value = fixture("WorldRunSelection")
    value["catalog"]["observed_at"] = observed_at
    if observed_at < value["version"]["view"]["created_at"]:
        with pytest.raises(ValidationError):
            parse("WorldRunSelection", value)
    else:
        parse("WorldRunSelection", value)


@pytest.mark.parametrize("created_at", [899, 900, 901])
def test_retained_grant_issuance_cannot_precede_version(created_at: int) -> None:
    value = preview_commit()
    value["before"].update(created_at=created_at, updated_at=created_at)
    value["after"]["created_at"] = created_at
    synchronize_preview(value)
    if created_at < value["version"]["view"]["created_at"]:
        with pytest.raises(ValidationError):
            parse("PreviewMutationCommit", value)
    else:
        parse("PreviewMutationCommit", value)


@pytest.mark.parametrize("model", ["PreviewGrantRecord", "PreviewGrantView"])
@pytest.mark.parametrize("updated_at", [1099, 1100, 1101])
def test_unrevoked_lifecycle_update_precedes_expiry(model: str, updated_at: int) -> None:
    value = fixture(model)
    value.update(revision=2, updated_at=updated_at)
    if updated_at < value["expires_at"]:
        parse(model, value)
    else:
        with pytest.raises(ValidationError):
            parse(model, value)


def test_revocation_after_expiry_remains_valid() -> None:
    value = preview_commit("revocation_commit")
    value["committed_at"] = 2000
    value["after"].update(updated_at=2000, revoked_at=2000)
    synchronize_preview(value)
    parsed = p.PreviewMutationCommit.model_validate_json(json.dumps(value))
    assert parsed.after.revoked_at is not None
    assert parsed.after.revoked_at > parsed.after.expires_at


@pytest.mark.parametrize(
    "field", ["receipt_id", "request_sha256", "allocated_world_id", "policy_sha256"]
)
def test_expiration_is_bound_to_original_receipt(field: str) -> None:
    value = fixture("WorldReceiptExpiration")
    value["expired"][field] = "f" * 64 if field.endswith("sha256") else "different"
    with pytest.raises(ValidationError):
        parse("WorldReceiptExpiration", value)


@pytest.mark.parametrize("change", ["policy", "interval", "too_early", "key"])
def test_expiration_cannot_rewrite_original_retention(change: str) -> None:
    value = fixture("WorldReceiptExpiration")
    if change == "policy":
        value["expired"]["policy_sha256"] = "f" * 64
    elif change == "interval":
        value["expired"]["retention_seconds"] -= 1
        value["expired"]["expires_at"] -= 1
    elif change == "too_early":
        value["observed_at"] -= 1
    else:
        value["expired"]["scope"]["key"] = "another-key"
    with pytest.raises(ValidationError):
        parse("WorldReceiptExpiration", value)


def test_preview_receipt_expiration_preserves_original_policy_and_world() -> None:
    old = p.PreviewMutationCommit.model_validate_json(
        json.dumps(FIXTURES["valid"]["PreviewMutationCommit"])
    )
    expired = w.WorldExpiredMutation(
        scope=old.scope,
        request_sha256=old.request_sha256,
        receipt_id=old.receipt_id,
        allocated_world_id=old.version.view.world_id,
        policy_sha256=message_sha256(old.policy),
        retention_seconds=old.policy.receipt_retention_seconds,
        committed_at=old.committed_at,
        expires_at=old.receipt_expires_at,
    )
    transition = p.WorldReceiptExpiration(
        receipt=old, expired=expired, observed_at=expired.expires_at
    )
    assert transition.expired.scope.world_id == old.version.view.world_id
    # This shape proposal does not execute purge or authorize metadata retrieval.
    assert transition.receipt.receipt_id == old.receipt_id


@pytest.mark.parametrize("model", ["WorldVersionCommit", "PreviewMutationCommit"])
def test_original_receipt_captures_exact_expiry(model: str) -> None:
    value = fixture(model)
    value["receipt_expires_at"] -= 1
    with pytest.raises(ValidationError):
        parse(model, value)


def test_receipt_and_tombstone_partial_combinations_remain_visible() -> None:
    value = fixture("WorldVersionLookup")
    value["expired"] = fixture("WorldExpiredMutation")
    both = parse("WorldVersionLookup", value)
    assert isinstance(both, w.WorldVersionLookup)
    assert both.receipt is not None and both.expired is not None
    # The later runtime must report recovery-required for both, never normalize it.
    value.update(receipt=None, target=None, current_head=None, current_commit=None)
    expired = parse("WorldVersionLookup", value)
    assert isinstance(expired, w.WorldVersionLookup)
    assert expired.expired is not None and expired.scope.world_id is None


def test_world_http_routes_have_explicit_browser_only_boundaries() -> None:
    api = json.loads((ROOT / "contracts/world.openapi.json").read_text())
    capabilities = {"worlds:read", "worlds:write", "worlds:preview", "worlds:preview-grants:manage"}
    operations = [op for path in api["paths"].values() for op in path.values()]
    assert len(operations) == 12
    assert len({op["operationId"] for op in operations}) == len(operations)
    for routes in api["paths"].values():
        for method, op in routes.items():
            assert op["x-world-capability"] in capabilities
            assert op["x-current-authorization-before-lookup"] is True
            assert op["x-implemented"] is False
            mutation = method == "post"
            assert op["security"] == [
                {"sessionCookie": [], "csrfHeader": []} if mutation else {"sessionCookie": []}
            ]
            expected_freshness = mutation and op["x-world-capability"].endswith(":manage")
            assert op["x-recent-authentication"] == expected_freshness
            assert ("X-Authentication-Action" in op["responses"]["401"].get("headers", {})) == (
                expected_freshness
            )
            assert all(param["required"] for param in op["parameters"] if param["in"] == "path")
            result_ref = op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            if op["operationId"] == "readGrantedWorldDefinition":
                assert result_ref.endswith("/GrantedWorldDefinition")
                assert any(
                    param["name"] == "grant_id" and param["required"] for param in op["parameters"]
                )
            else:
                assert result_ref.rsplit("/", 1)[-1] in (
                    p.world_json_schema()["x-agent-safe-models"]
                    + p.world_json_schema()["x-management-output-models"]
                )
            if mutation:
                assert any(
                    param["name"] == "Idempotency-Key" and param["required"]
                    for param in op["parameters"]
                )


def test_route_schemas_distinguish_initial_create_from_append() -> None:
    api = json.loads((ROOT / "contracts/world.openapi.json").read_text())
    initial = api["components"]["schemas"]["InitialWorldRequest"]["allOf"][1]["properties"]
    append = api["components"]["schemas"]["AppendWorldRequest"]["allOf"][1]["properties"]
    assert initial["expected_head_revision"] == {"type": "integer", "const": 0}
    assert initial["expected_version_id"] == {"type": "null"}
    assert append["expected_head_revision"]["minimum"] == 1
    assert append["expected_version_id"]["type"] == "string"


def test_revoke_does_not_retain_an_unbound_recipient_snapshot() -> None:
    value = preview_commit("revocation_commit")
    value["recipient_at_commit"] = fixture("PreviewMutationCommit")["recipient_at_commit"]
    with pytest.raises(ValidationError):
        parse("PreviewMutationCommit", value)


def test_owner_management_output_is_not_an_agent_stream_root() -> None:
    schema = p.world_json_schema()
    assert schema["x-management-output-models"] == ["PreviewGrantView", "PreviewGrantPage"]
    assert not set(schema["x-management-output-models"]) & set(schema["x-agent-safe-models"])
    assert set(schema["x-management-output-models"]) <= set(schema["x-public-models"])


def test_service_run_selection_does_not_require_browser_world_authority() -> None:
    value = fixture("WorldRunSelection")
    ownership = value["admission"]["ownership"]
    ownership.update(
        principal_kind="service",
        principal_id="service-principal",
        created_by_credential_id="service-key",
    )
    value["admission"]["stored_request"]["scope"]["principal_id"] = "service-principal"
    selection = w.WorldRunSelection.model_validate_json(json.dumps(value))
    assert selection.admission.ownership.principal_kind == "service"
    assert selection.version.author.principal_id != selection.admission.ownership.principal_id


def test_opaque_version_id_is_unique_even_across_worlds_in_a_page() -> None:
    value = fixture("WorldPage")
    second = copy.deepcopy(value["items"][0])
    second["world_id"] = "another-world"
    value["items"].append(second)
    with pytest.raises(ValidationError):
        parse("WorldPage", value)
    second["version_id"] = "distinct-version"
    page = w.WorldPage.model_validate_json(json.dumps(value))
    assert len(page.items) == 2
    assert len({item.world_id for item in page.items}) == 2


def test_later_creation_result_keeps_original_admitted_snapshot_compatible() -> None:
    value = fixture("WorldRunSelection")
    result = value["admission"]["stored_request"]["operation"]["result"]["value"]
    result.update(status="running", revision=1)
    selection = w.WorldRunSelection.model_validate_json(json.dumps(value))
    retained = selection.admission.stored_request.operation.result
    assert retained is not None
    assert selection.admission.admitted_run.status == "queued"
    assert selection.admission.admitted_run.revision == 0
    assert retained.value.model_dump()["status"] == "running"
    assert retained.value.model_dump()["revision"] == 1


def test_unavailable_current_policy_or_authority_has_explicit_503_contract() -> None:
    from strange_physics.control_contracts import Error

    error = Error.model_validate_json(json.dumps(FIXTURES["service_unavailable"]))
    assert error.code == "temporarily_unavailable"
    assert error.retryable is True
    api = json.loads((ROOT / "contracts/world.openapi.json").read_text())
    for routes in api["paths"].values():
        for operation in routes.values():
            response = operation["responses"]["503"]
            assert response["content"]["application/json"]["schema"] == {
                "$ref": "control.schema.json#/$defs/Error"
            }
            assert response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"
