from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import package_contracts as p
from strange_physics import worker_contracts as w
from strange_physics.contracts import Message
from strange_physics.research_contracts import message_sha256

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "contracts/execution.examples.json").read_text())
MODELS = {model.__name__: model for model in w.EXECUTION_MODELS}


def fixture(name: str) -> dict[str, Any]:
    return copy.deepcopy(EXAMPLES["valid"][name])


def parse[M: Message](model: type[M], value: Any) -> M:
    return model.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("name", tuple(MODELS))
def test_synthetic_positive_contracts(name: str) -> None:
    assert parse(MODELS[name], fixture(name))


@pytest.mark.parametrize("case", EXAMPLES["schema_negative"] + EXAMPLES["runtime_negative"])
def test_declared_negative_fixtures(case: dict[str, Any]) -> None:
    data = fixture(case["model"])
    data[case["field"]] = case["value"]
    with pytest.raises(ValidationError):
        parse(MODELS[case["model"]], data)


def test_schema_matches_and_only_detached_manifest_is_public() -> None:
    schema = w.execution_json_schema()
    assert schema == json.loads((ROOT / "contracts/execution.schema.json").read_text())
    assert schema["x-public-models"] == ["PackageManifest"]
    reached: set[str] = set()
    pending = ["PackageManifest"]
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        nodes: list[Any] = [schema["$defs"][name]]
        while nodes:
            node = nodes.pop()
            if isinstance(node, dict):
                reference = node.get("$ref", "")
                if reference.startswith("#/$defs/"):
                    pending.append(reference.removeprefix("#/$defs/"))
                nodes.extend(node.values())
            elif isinstance(node, list):
                nodes.extend(node)
    assert reached == {"PackageManifest", "ArtifactRef"}
    with pytest.raises(ValidationError):
        parse(p.PackageManifest, fixture("PackageManifest") | {"namespace_id": "private"})


def test_raw_archive_manifest_lock_canonical_profile_and_image_are_separate() -> None:
    source = parse(p.PackageSource, fixture("PackageSource"))
    assert source.manifest_object.record.ref.sha256 != message_sha256(source.manifest)
    assert source.manifest.source == source.archive.record.ref
    assert source.manifest.lock_bytes_sha256 != source.archive.record.ref.sha256
    submitted = parse(p.SubmittedRuntimeApproval, fixture("SubmittedRuntimeApproval"))
    builtin = parse(p.BuiltinAnalyticApproval, fixture("BuiltinAnalyticApproval"))
    assert submitted.build.build.runtime_image_sha256 == builtin.build.build.runtime_image_sha256
    assert submitted.approval.profile_sha256 != builtin.approval.profile_sha256
    assert "package_id" not in builtin.model_dump_json()
    assert "agent_configuration" not in source.manifest.model_dump_json()


@pytest.mark.parametrize(
    "path", ["/absolute", "../escape", "a/../b", "a//b", "a/./b", "a\\b", "a\n"]
)
def test_archive_paths_cannot_escape_or_alias(path: str) -> None:
    with pytest.raises(ValidationError):
        parse(p.ArchiveEntry, fixture("ArchiveEntry") | {"path": path})


def test_archive_inventory_rejects_duplicate_entries_and_file_ancestor() -> None:
    data = fixture("PackageInspection")
    for entries in (
        [*data["entries"], data["entries"][0]],
        [dict(data["entries"][0], path="agent.py/child.py"), *data["entries"]],
    ):
        value = data | {"entries": sorted(entries, key=lambda entry: entry["path"])}
        with pytest.raises(ValidationError):
            parse(p.PackageInspection, value)


@pytest.mark.parametrize("field", ["generation", "sha256", "size_bytes", "media_type"])
def test_package_byte_proof_binds_exact_identity(field: str) -> None:
    data = fixture("VerifiedPackageObject")
    data["verification"][field] = {
        "generation": "5",
        "sha256": "f" * 64,
        "size_bytes": 999,
        "media_type": "text/plain",
    }[field]
    with pytest.raises(ValidationError):
        parse(p.VerifiedPackageObject, data)


@pytest.mark.parametrize(
    "part,field",
    [
        ("lock", "inspection_sha256"),
        ("lock", "policy_sha256"),
        ("lock", "lock_bytes_sha256"),
        ("build", "source_sha256"),
        ("build", "lock_bytes_sha256"),
        ("build", "build_policy_sha256"),
    ],
)
def test_submitted_build_cannot_substitute_source_lock_or_policy(part: str, field: str) -> None:
    data = fixture("SubmittedBuild")
    data[part][field] = "f" * 64
    with pytest.raises(ValidationError):
        parse(p.SubmittedBuild, data)


@pytest.mark.parametrize("field", ["source_sha256", "lock_bytes_sha256", "recipe_sha256"])
def test_builtin_evidence_is_real_source_and_recipe_bound(field: str) -> None:
    data = fixture("BuiltinBuild")
    data["build"][field] = "f" * 64
    with pytest.raises(ValidationError):
        parse(p.BuiltinBuild, data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("predictor_version", "different-version"),
        ("prediction_config_sha256", "f" * 64),
    ],
)
def test_builtin_profile_changes_need_matching_approval(field: str, value: str) -> None:
    data = fixture("BuiltinAnalyticApproval")
    data["profile"][field] = value
    with pytest.raises(ValidationError):
        parse(p.BuiltinAnalyticApproval, data)


@pytest.mark.parametrize("outcome", ["unknown", "rejected"])
def test_unknown_or_rejected_scan_cannot_be_approved(outcome: str) -> None:
    data = fixture("SubmittedRuntimeApproval")
    data["scan"]["outcome"] = outcome
    data["approval"]["scan_sha256"] = message_sha256(parse(p.ImageScanEvidence, data["scan"]))
    with pytest.raises(ValidationError):
        parse(p.SubmittedRuntimeApproval, data)


def test_same_image_does_not_allow_builtin_approval_in_agent_launch() -> None:
    data = fixture("WorkerLaunchRecord")
    builtin = fixture("BuiltinAnalyticApproval")
    data["approval"] = builtin
    data["request"]["approval_sha256"] = message_sha256(parse(p.BuiltinAnalyticApproval, builtin))
    data["request_sha256"] = message_sha256(parse(w.WorkerLaunchRequest, data["request"]))
    with pytest.raises(ValidationError):
        parse(w.WorkerLaunchRecord, data)


@pytest.mark.parametrize(
    "fault",
    [
        "body_digest",
        "scope_principal",
        "run_identity",
        "space",
        "initial_status",
        "initial_revision",
        "initial_budget",
        "deadline",
        "configuration",
        "package",
    ],
)
def test_original_admission_requires_actual_original_body_and_joined_receipt(fault: str) -> None:
    data = fixture("OriginalExecutionAdmission")
    if fault == "body_digest":
        data["request"]["world_version_id"] = "different-world"
    elif fault == "scope_principal":
        data["stored_request"]["scope"]["principal_id"] = "different-principal"
    elif fault == "run_identity":
        data["ownership"]["run_id"] = "different-run"
    elif fault == "space":
        data["admitted_run"]["space"]["budget"] += 1
        data["admitted_run"]["budget_remaining"] += 1
    elif fault == "initial_status":
        data["admitted_run"]["status"] = "running"
    elif fault == "initial_revision":
        data["admitted_run"]["revision"] = 1
    elif fault == "initial_budget":
        data["admitted_run"]["experiments_accepted"] = 1
        data["admitted_run"]["budget_remaining"] -= 1
    elif fault == "deadline":
        data["ownership"]["run_deadline"] += 1
    elif fault == "configuration":
        data["agent_configuration"]["seed"] = 2
    else:
        data["checkpoint_binding"]["agent_package_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        parse(w.OriginalExecutionAdmission, data)


def test_general_creation_result_is_not_silently_constrained_to_initial_snapshot() -> None:
    data = fixture("OriginalExecutionAdmission")
    result = data["stored_request"]["operation"]["result"]["value"]
    result["status"] = "running"
    result["revision"] = 2
    result["experiments_accepted"] = 1
    result["budget_remaining"] -= 1
    assert parse(w.OriginalExecutionAdmission, data)


@pytest.mark.parametrize("fault", ["deep", "large", "nodes", "nonfinite"])
def test_configuration_is_bounded_before_hashing(fault: str) -> None:
    value: Any
    if fault == "deep":
        value = 0
        for _ in range(33):
            value = [value]
    elif fault == "large":
        value = "x" * 262_145
    elif fault == "nodes":
        value = list(range(10_001))
    else:
        value = float("inf")
    with pytest.raises(ValueError):
        w.configuration_sha256({"value": value})


def test_internal_termination_authority_is_purpose_and_launch_bound() -> None:
    data = fixture("WorkerControlClaims")
    for changes in (
        {"purpose": "workers:terminate", "launch_id": None},
        {"purpose": "workers:launch", "launch_id": "launch-1"},
        {"purpose": "run-credentials:manage"},
    ):
        with pytest.raises(ValidationError):
            parse(w.WorkerControlClaims, data | changes)
    assert parse(
        w.WorkerControlClaims, data | {"purpose": "workers:terminate", "launch_id": "launch-1"}
    )


def test_broker_map_is_closed_without_prediction_evaluator_or_provider_calls() -> None:
    assert w.BROKER_PERMISSIONS == {
        "list_experiments": "experiments:read",
        "execute_experiment": "experiments:write",
        "save_checkpoint": "checkpoints:write",
        "submit_model": "models:write",
    }


@pytest.mark.parametrize("field", ["expected_run_revision", "expected_credential_revision"])
def test_launch_proposal_binds_actual_cas(field: str) -> None:
    data = fixture("WorkerLaunchPlan")
    data[field] += 1
    with pytest.raises(ValidationError):
        parse(w.WorkerLaunchPlan, data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "terminate"),
        ("launch_id", "other-launch"),
        ("launch_record_sha256", "f" * 64),
        ("workspace_id", "foreign"),
    ],
)
def test_dispatch_outbox_cannot_point_to_another_launch(field: str, value: str) -> None:
    data = fixture("WorkerLaunchPlan")
    data["outbox"][field] = value
    with pytest.raises(ValidationError):
        parse(w.WorkerLaunchPlan, data)


def test_valid_c2_running_status_is_not_a_confirmed_worker_process() -> None:
    data = fixture("WorkerLaunchLifecycle")
    assert data["state"] == "prepared" and data["instance"] is None
    with pytest.raises(ValidationError):
        parse(w.WorkerLaunchLifecycle, data | {"state": "active"})
    instance = fixture("RuntimeInstance")
    assert parse(w.WorkerLaunchLifecycle, data | {"state": "active", "instance": instance})


@pytest.mark.parametrize("state", ["fenced", "stopping", "stopped"])
def test_reapproval_cannot_resurrect_a_fenced_launch_transition(state: str) -> None:
    before = fixture("WorkerLifecycleTransition")["after"]
    before["state"] = state
    if state == "stopped":
        before |= {"stopped_at": 1202, "stop_outcome": "never_started"}
    after = fixture("WorkerLaunchLifecycle")
    after |= {
        "revision": before["revision"] + 1,
        "state": "active",
        "instance": fixture("RuntimeInstance"),
    }
    with pytest.raises(ValidationError):
        parse(w.WorkerLifecycleTransition, {"before": before, "after": after})


@pytest.mark.parametrize(
    "field,value",
    [
        ("launch_id", "newer-launch"),
        ("launch_record_sha256", "f" * 64),
        ("termination_id", "newer-stop"),
        ("request_sha256", "f" * 64),
        ("fenced_lifecycle_revision", 5),
    ],
)
def test_old_ack_cannot_complete_a_different_launch_or_stop(field: str, value: Any) -> None:
    data = fixture("WorkerTerminationCompletion")
    data["evidence"][field] = value
    with pytest.raises(ValidationError):
        parse(w.WorkerTerminationCompletion, data)


def test_unknown_instance_cannot_be_reported_terminated() -> None:
    data = fixture("WorkerTerminationEvidence")
    assert data["instance"] is None
    with pytest.raises(ValidationError):
        parse(w.WorkerTerminationEvidence, data | {"outcome": "terminated"})


def test_termination_shape_uses_retained_launch_not_current_lease_or_owner_state() -> None:
    completion = parse(w.WorkerTerminationCompletion, fixture("WorkerTerminationCompletion"))
    assert completion.transition.after.state == "stopped"
    assert (
        not {"current_lease", "current_owner", "workspace_state"}
        & w.WorkerTerminationCompletion.model_fields.keys()
    )
    assert "never changes" in (w.WorkerTerminationCompletion.__doc__ or "")
    # Runtime authorization is deliberately not provided by these shape validators.


def test_retry_metadata_supplies_lifecycle_revision_without_execution_material() -> None:
    reply = parse(w.WorkerLaunchReplay, fixture("WorkerLaunchReplay"))
    assert reply.lifecycle_revision == 0
    assert set(reply.model_dump()) == {
        "launch_id",
        "request_sha256",
        "launch_record_sha256",
        "lifecycle_revision",
        "state",
    }


def test_termination_transition_cannot_name_another_launch() -> None:
    value = fixture("WorkerTerminationPlan")
    for phase in ["before", "after"]:
        value["transition"][phase]["launch_id"] = "unrelated-launch"
    with pytest.raises(ValidationError):
        parse(w.WorkerTerminationPlan, value)


def test_package_identity_is_canonical_manifest_not_archive() -> None:
    launch = parse(w.WorkerLaunchRecord, fixture("WorkerLaunchRecord"))
    source = launch.approval.build.inspection.source
    digest = message_sha256(source.manifest)
    assert launch.admission.request.agent_package_sha256 == digest
    assert launch.admission.checkpoint_binding.agent_package_sha256 == digest
    assert digest != source.archive.record.ref.sha256
    assert digest != source.manifest_object.record.ref.sha256


@pytest.mark.parametrize("body", EXAMPLES["normal_completion"])
def test_normal_completion_uses_exact_launch_fence(body: dict[str, Any]) -> None:
    value = fixture("WorkerTerminationPlan")
    value["termination"]["request"] = body
    digest = message_sha256(parse(w.WorkerTerminationRequest, body))
    value["termination"]["request_sha256"] = digest
    value["outbox"]["request_sha256"] = digest
    plan = parse(w.WorkerTerminationPlan, value)
    assert plan.transition.after.state == "fenced"
    assert plan.transition.after.stop_outcome is None
    assert plan.termination.request.reason in {"completed", "budget_exhausted"}
