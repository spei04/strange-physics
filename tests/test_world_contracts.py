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
