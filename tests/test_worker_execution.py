from __future__ import annotations

import copy
import inspect
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics import artifact_contracts as a
from strange_physics import package_contracts as p
from strange_physics import worker_contracts as w
from strange_physics import worker_execution as e
from strange_physics.contracts import Message
from strange_physics.control_contracts import (
    ContractViolation,
    ExperimentPage,
    Operation,
    VerifiedCredential,
)
from strange_physics.package_validation import validate_package_inspection
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import RunProductAuthority
from strange_physics.workspace_contracts import WorkspaceAuthority, WorkspaceView

ROOT = Path(__file__).resolve().parents[1]
EXEC = json.loads((ROOT / "contracts/execution.examples.json").read_text())["valid"]
ART = json.loads((ROOT / "contracts/artifacts.examples.json").read_text())["valid"]
CONTROL = json.loads((ROOT / "contracts/control.examples.json").read_text())["valid"]
RUN = json.loads((ROOT / "contracts/run-credentials.examples.json").read_text())["valid"]


def value[M: Message](model: type[M]) -> M:
    return model.model_validate_json(
        json.dumps(copy.deepcopy((EXEC | RUN | ART | CONTROL)[model.__name__]))
    )


def changed[M: Message](model: M, **fields: Any) -> M:
    return type(model).model_validate(model.model_dump() | fields)


def args() -> dict[str, Any]:
    authority = value(RunProductAuthority)
    current = authority.current
    workspace = WorkspaceAuthority(
        workspace=WorkspaceView(
            workspace_id=current.run.workspace_id,
            display_name="Synthetic",
            visibility="private",
            state="active",
            revision=2,
        ),
        active_owner_ids=(current.owner.principal.principal_id,),
        disabled_owner_ids=(),
    )
    environment = e.WorkerEnvironment(
        current=current,
        workspace=workspace,
        credential_policy=authority.policy,
        package_policy=value(p.PackagePolicy),
        worker_policy=value(w.WorkerPolicy),
        approval=value(p.SubmittedRuntimeApproval),
        isolation=value(w.IsolationEvidence),
    )
    return dict(
        request=value(w.WorkerLaunchRequest),
        admission=value(w.OriginalExecutionAdmission),
        environment=environment,
        control_policy=value(w.WorkerControlPolicy),
        authority=value(w.WorkerControlAuthority),
        lookup=changed(value(w.WorkerLaunchLookup), record=None, lifecycle=None, outbox=None),
        restore=None,
        launch_id="launch-1",
        now=1200,
    )


def planned(data: dict[str, Any]) -> w.WorkerLaunchPlan:
    result = e.admit_worker_launch(**data)
    assert isinstance(result, w.WorkerLaunchPlan)
    return result


def retain(data: dict[str, Any], plan: w.WorkerLaunchPlan) -> None:
    data["lookup"] = changed(
        data["lookup"], record=plan.record, lifecycle=plan.lifecycle, outbox=plan.outbox
    )


def advance(
    data: dict[str, Any], instance: w.RuntimeInstance | None
) -> w.WorkerLifecycleTransition:
    return e.advance_worker_launch(
        **{k: v for k, v in data.items() if k != "launch_id"}, instance=instance
    )


def active() -> dict[str, Any]:
    data = args()
    plan = planned(data)
    retain(data, plan)
    transition = advance(data, None)
    data["lookup"] = changed(data["lookup"], lifecycle=transition.after)
    data["now"] = 1201
    instance = w.RuntimeInstance(
        provider_namespace="synthetic-provider",
        instance_id="instance-1",
        launch_id=plan.record.launch_id,
        launch_record_sha256=message_sha256(plan.record),
        confirmed_at=1201,
    )
    transition = advance(data, instance)
    data["lookup"] = changed(data["lookup"], lifecycle=transition.after)
    data["now"] = 1202
    return data


def bearer(
    environment: e.WorkerEnvironment, *, old: bool = False
) -> tuple[VerifiedCredential, RunProductAuthority]:
    state = environment.current.credentials
    record = (
        state.records[0]
        if old
        else next(r for r in state.records if r.claims.credential_id == state.current_credential_id)
    )
    claims = record.claims
    authority = RunProductAuthority(
        kind="run",
        policy=environment.credential_policy,
        current=environment.current,
        verified_claims=claims,
    )
    credential = VerifiedCredential(
        issuer=claims.issuer,
        subject=claims.principal_id,
        principal_id=claims.principal_id,
        credential_id=claims.credential_id,
        kind="run",
        workspace_id=claims.workspace_id,
        scopes=claims.scopes,
        expires_at=claims.expires_at,
        revoked=False,
        run_id=claims.run_id,
        attempt_id=claims.attempt_id,
        lease_epoch=claims.lease_epoch,
    )
    return credential, authority


def broker(
    data: dict[str, Any], operation: str = "execute_experiment", *, old: bool = False
) -> None:
    credential, authority = bearer(data["environment"], old=old)
    e.authorize_worker_broker(
        operation, credential, authority, data["environment"], data["lookup"], now=data["now"]
    )


def denied(code: str, status: int) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda error: error.status == status)


def stop_args(data: dict[str, Any], reason: str = "cancelled") -> dict[str, Any]:
    lookup = data["lookup"]
    authority = data["authority"]
    authority = changed(
        authority,
        claims=changed(
            authority.claims, purpose="workers:terminate", launch_id=lookup.record.launch_id
        ),
    )
    request = changed(
        value(w.WorkerTerminationRequest),
        workspace_id=lookup.workspace_id,
        run_id=lookup.run_id,
        launch_id=lookup.record.launch_id,
        launch_record_sha256=message_sha256(lookup.record),
        expected_lifecycle_revision=lookup.lifecycle.revision,
        reason=reason,
    )
    return dict(
        request=request,
        control_policy=data["control_policy"],
        authority=authority,
        lookup=lookup,
        receipt=None,
        outbox=None,
        termination_id="termination-1",
        now=data["now"],
    )


def stopped_plan(data: dict[str, Any]) -> tuple[dict[str, Any], w.WorkerTerminationPlan]:
    stopped = stop_args(data)
    result = e.terminate_worker_launch(**stopped)
    assert isinstance(result, w.WorkerTerminationPlan)
    stopped.update(
        lookup=changed(stopped["lookup"], lifecycle=result.transition.after),
        receipt=result.termination,
        outbox=result.outbox,
    )
    return stopped, result


def completion(stopped: dict[str, Any], *, never_started: bool = False) -> dict[str, Any]:
    receipt = stopped["receipt"]
    lookup = stopped["lookup"]
    proof = w.WorkerTerminationEvidence(
        verification_id="stop-proof-1",
        verifier_id="synthetic-reconciler",
        termination_id=receipt.termination_id,
        request_sha256=receipt.request_sha256,
        launch_id=receipt.request.launch_id,
        launch_record_sha256=receipt.request.launch_record_sha256,
        fenced_lifecycle_revision=receipt.fenced_lifecycle_revision,
        outcome="never_started" if never_started else "terminated",
        instance=None if never_started else lookup.lifecycle.instance,
        observed_at=stopped["now"] + 1,
    )
    return dict(
        receipt=receipt,
        evidence=proof,
        control_policy=stopped["control_policy"],
        authority=stopped["authority"],
        lookup=lookup,
        outbox=stopped["outbox"],
        now=stopped["now"] + 1,
    )


def test_launch_dispatch_confirmation_and_metadata_replay() -> None:
    data = args()
    result = planned(data)
    assert result.record.deadline == 1300
    assert result.expected_run_revision == data["environment"].current.run.revision
    retain(data, result)
    replay = e.admit_worker_launch(**data)
    assert isinstance(replay, w.WorkerLaunchReplay)
    assert set(type(replay).model_fields) == {
        "launch_id",
        "request_sha256",
        "launch_record_sha256",
        "lifecycle_revision",
        "state",
    }
    with denied("incompatible_state", 409):
        broker(data)
    data = active()
    broker(data)
    replay = e.admit_worker_launch(**data)
    assert isinstance(replay, w.WorkerLaunchReplay) and replay.state == "active"
    assert (
        advance(data, data["lookup"].lifecycle.instance).before
        == advance(data, data["lookup"].lifecycle.instance).after
    )


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "owner_disabled",
        "owner_generation",
        "grant_revoked",
        "grant_incarnation",
        "lease_revoked",
        "lease_expired",
        "deadline_changed",
        "cancelled",
        "workspace_quarantined",
        "key_revoked",
        "key_missing",
        "run_policy",
    ],
)
def test_current_authority_precedes_partial_launch_lookup(replay: bool, fault: str) -> None:
    data = args()
    if replay:
        retain(data, planned(data))
    environment = data["environment"]
    current = environment.current
    code, status = "forbidden", 403
    if fault == "owner_disabled":
        current = changed(
            current,
            owner=changed(current.owner, principal=changed(current.owner.principal, active=False)),
        )
    elif fault == "owner_generation":
        current = changed(
            current,
            owner=changed(current.owner, principal=changed(current.owner.principal, generation=1)),
        )
    elif fault == "grant_revoked":
        current = changed(
            current,
            owner=changed(
                current.owner,
                grant=changed(
                    current.owner.grant,
                    membership=changed(current.owner.grant.membership, active=False),
                ),
            ),
        )
    elif fault == "grant_incarnation":
        current = changed(
            current, owner=changed(current.owner, grant=changed(current.owner.grant, incarnation=1))
        )
    elif fault == "lease_revoked":
        current = changed(current, lease=changed(current.lease, revoked=True))
    elif fault == "lease_expired":
        current = changed(current, lease=changed(current.lease, expires_at=1200))
    elif fault == "deadline_changed":
        current = changed(current, lease=changed(current.lease, run_deadline=2001))
    elif fault == "cancelled":
        current = changed(
            current,
            run=changed(current.run, status="cancelling"),
            lease=changed(current.lease, status="cancelling"),
        )
        code, status = "incompatible_state", 409
    elif fault == "workspace_quarantined":
        environment = replace(
            environment,
            workspace=changed(
                environment.workspace,
                workspace=changed(environment.workspace.workspace, state="quarantined"),
            ),
        )
    elif fault == "key_revoked":
        current = changed(
            current,
            credentials=changed(
                current.credentials,
                records=(changed(current.credentials.records[0], revoked_at=1200),),
                current_credential_id=None,
            ),
        )
        code, status = "unauthenticated", 401
    elif fault == "key_missing":
        current = changed(
            current, credentials=changed(current.credentials, current_credential_id=None)
        )
        code, status = "unauthenticated", 401
    else:
        environment = replace(environment, credential_policy=None)
        code, status = "policy_unavailable", 503
    data["environment"] = replace(environment, current=current)
    data["lookup"] = changed(
        data["lookup"], outbox=value(w.WorkerCommandOutbox), record=None, lifecycle=None
    )
    with denied(code, status):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize(
    "fault",
    [
        "revoked",
        "principal_disabled",
        "principal_generation",
        "expired",
        "future",
        "ttl",
        "issuer",
        "audience",
        "policy",
        "scope",
        "purpose",
        "unavailable",
    ],
)
def test_internal_control_is_independent_current_authority(fault: str) -> None:
    data = args()
    authority = data["authority"]
    claims = authority.claims
    if fault == "principal_disabled":
        authority = changed(authority, principal=changed(authority.principal, active=False))
    elif fault == "principal_generation":
        authority = changed(authority, principal=changed(authority.principal, generation=3))
    elif fault == "unavailable":
        data["control_policy"] = None
    else:
        choices: dict[str, dict[str, Any]] = {
            "revoked": {"revoked": True},
            "expired": {"expires_at": 1200},
            "future": {"issued_at": 1201},
            "ttl": {"expires_at": 1500},
            "issuer": {"issuer": "https://other.example"},
            "audience": {"audience": "foreign"},
            "policy": {"policy_id": "foreign-policy"},
            "scope": {"run_id": "other-run"},
            "purpose": {"purpose": "workers:terminate", "launch_id": "launch-1"},
        }
        fields = choices[fault]
        claims = changed(claims, **fields)
    data["authority"] = changed(authority, claims=claims)
    code = (
        "policy_unavailable"
        if fault == "unavailable"
        else "forbidden"
        if fault in {"scope", "purpose"}
        else "unauthenticated"
    )
    with denied(code, 503 if code == "policy_unavailable" else 403 if code == "forbidden" else 401):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize(
    "fault",
    [
        "worker_policy",
        "package_policy",
        "revoked",
        "isolation_missing",
        "isolation_unknown",
        "isolation_unavailable",
        "isolation_expired",
        "isolation_future",
        "isolation_hash",
        "isolation_network",
        "isolation_sandbox",
    ],
)
@pytest.mark.parametrize("replay", [False, True])
def test_current_runtime_policy_precedes_replay(fault: str, replay: bool) -> None:
    data = args()
    if replay:
        retain(data, planned(data))
    env = data["environment"]
    if fault in {"worker_policy", "package_policy"}:
        env = replace(env, **{fault: None})
    elif fault == "revoked":
        env = replace(
            env,
            approval=changed(
                env.approval, approval=changed(env.approval.approval, state="revoked", revision=1)
            ),
        )
    elif fault == "isolation_missing":
        env = replace(env, isolation=None)
    else:
        choices: dict[str, dict[str, Any]] = {
            "isolation_unknown": {"state": "unknown"},
            "isolation_unavailable": {"state": "unavailable"},
            "isolation_expired": {"valid_until": 1200},
            "isolation_future": {"observed_at": 1201},
            "isolation_hash": {"worker_policy_sha256": "f" * 64},
            "isolation_network": {"network_policy": "foreign"},
            "isolation_sandbox": {"sandbox_profile": "foreign"},
        }
        fields = choices[fault]
        env = replace(env, isolation=changed(env.isolation, **fields))
    data["environment"] = env
    with denied(
        "forbidden" if fault == "revoked" else "policy_unavailable",
        403 if fault == "revoked" else 503,
    ):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize("missing", ["record", "lifecycle", "outbox"])
def test_partial_launch_closure_cannot_be_replayed_or_dispatched(missing: str) -> None:
    data = args()
    retain(data, planned(data))
    data["lookup"] = changed(data["lookup"], **{missing: None})
    with denied("recovery_required", 409):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize(
    "field,new_value",
    [
        ("workspace_id", "foreign"),
        ("run_id", "foreign"),
        ("attempt_id", "foreign"),
        ("lease_epoch", 4),
    ],
)
def test_wrong_target_empty_lookup_is_not_fresh_absence(field: str, new_value: Any) -> None:
    data = args()
    data["lookup"] = changed(data["lookup"], **{field: new_value})
    with denied("recovery_required", 409):
        e.admit_worker_launch(**data)


def test_new_launch_request_conflict_preserves_existing_launch() -> None:
    data = args()
    retain(data, planned(data))
    data["request"] = changed(
        data["request"], resources=changed(data["request"].resources, cpu_seconds=30)
    )
    with denied("idempotency_conflict", 409):
        e.admit_worker_launch(**data)


def test_current_key_rotation_and_run_progress_preserve_original_admission() -> None:
    data = active()
    env = data["environment"]
    state = env.current.credentials
    old = changed(state.records[0], revoked_at=1201)
    new = changed(
        state.records[0],
        claims=changed(
            state.records[0].claims,
            credential_id="worker-key-2",
            generation=2,
            issued_at=1201,
            expires_at=1401,
        ),
    )
    current = changed(
        env.current,
        credentials=changed(
            state,
            revision=2,
            last_generation=2,
            current_credential_id="worker-key-2",
            records=(old, new),
        ),
        run=changed(env.current.run, revision=5, experiments_accepted=3, budget_remaining=3),
    )
    data["environment"] = replace(env, current=current)
    replay = e.admit_worker_launch(**data)
    assert isinstance(replay, w.WorkerLaunchReplay)
    assert data["lookup"].record.original_credential_id == "worker-key-1"
    assert data["lookup"].record.admission.ownership.created_by_credential_id == "session-1"
    broker(data)
    with denied("unauthenticated", 401):
        broker(data, old=True)


@pytest.mark.parametrize(
    "operation", ["list_experiments", "execute_experiment", "save_checkpoint", "submit_model"]
)
def test_broker_closed_map_uses_current_role_per_operation(operation: str) -> None:
    data = active()
    env = data["environment"]
    member = changed(env.current.owner.grant.membership, role="viewer")
    current = changed(
        env.current,
        owner=changed(env.current.owner, grant=changed(env.current.owner.grant, membership=member)),
    )
    # Another current human owner preserves workspace viability.
    workspace = changed(env.workspace, active_owner_ids=("other-owner",))
    data["environment"] = replace(env, current=current, workspace=workspace)
    if operation == "list_experiments":
        broker(data, operation)
    else:
        with denied("forbidden", 403):
            broker(data, operation)


@pytest.mark.parametrize(
    "operation",
    ["invoke_predictor", "provider_call", "read_evaluator_labels", "model_call", "runs:create"],
)
def test_unregistered_broker_operations_remain_unavailable(operation: str) -> None:
    with denied("forbidden", 403):
        broker(active(), operation)


def test_expired_bearer_is_denied_before_partial_retained_launch() -> None:
    data = active()
    credential, authority = bearer(data["environment"])
    credential = changed(credential, revoked=True)
    lookup = changed(data["lookup"], record=None, outbox=None)
    with denied("unauthenticated", 401):
        e.authorize_worker_broker(
            "list_experiments", credential, authority, data["environment"], lookup, now=1202
        )


@pytest.mark.parametrize("state", ["fenced", "stopping", "stopped"])
def test_restored_policy_cannot_resurrect_a_fenced_launch(state: str) -> None:
    data = active()
    stopped, plan = stopped_plan(data)
    lifecycle = plan.transition.after
    if state == "stopping":
        lifecycle = changed(lifecycle, state=state, revision=lifecycle.revision + 1)
    elif state == "stopped":
        result = e.complete_worker_termination(**completion(stopped))
        lifecycle = result.transition.after
        data["now"] += 1
    data["lookup"] = changed(data["lookup"], lifecycle=lifecycle)
    # Policy is the original approved/available policy again; durable fence still wins.
    with denied("forbidden", 403):
        broker(data)
    with denied("forbidden", 403):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize(
    "reason",
    [
        "cancelled",
        "lease_lost",
        "authority_revoked",
        "policy_lost",
        "deadline",
        "operator",
        "completed",
        "budget_exhausted",
    ],
)
def test_exact_launch_termination_and_lost_ack_replay(reason: str) -> None:
    data = active()
    stopped = stop_args(data, reason)
    plan = e.terminate_worker_launch(**stopped)
    assert isinstance(plan, w.WorkerTerminationPlan)
    stopped.update(
        lookup=changed(stopped["lookup"], lifecycle=plan.transition.after),
        receipt=plan.termination,
        outbox=plan.outbox,
    )
    assert e.terminate_worker_launch(**stopped) == plan.termination
    result = e.complete_worker_termination(**completion(stopped))
    assert result.transition.after.state == "stopped"
    assert result.transition.after.instance == data["lookup"].lifecycle.instance
    assert "lease" not in type(result).model_fields


def test_termination_remains_possible_after_work_authority_is_lost() -> None:
    data = active()
    original = data["lookup"]
    env = data["environment"]
    current = changed(
        env.current,
        owner=changed(
            env.current.owner, principal=changed(env.current.owner.principal, active=False)
        ),
        lease=changed(env.current.lease, attempt_id="replacement-attempt", epoch=4),
    )
    data["environment"] = replace(
        env,
        current=current,
        workspace=changed(
            env.workspace, workspace=changed(env.workspace.workspace, state="quarantined")
        ),
        isolation=None,
    )
    with pytest.raises(ContractViolation):
        broker(data)
    stopped = stop_args(data)
    plan = e.terminate_worker_launch(**stopped)
    assert isinstance(plan, w.WorkerTerminationPlan)
    assert plan.launch == original.record
    assert data["environment"].current.lease.attempt_id == "replacement-attempt"


def test_unknown_dispatch_stays_pending_until_exact_reconciliation() -> None:
    data = args()
    retain(data, planned(data))
    pending = advance(data, None)
    data["lookup"] = changed(data["lookup"], lifecycle=pending.after)
    stopped, plan = stopped_plan(data)
    assert plan.transition.after.state == "fenced" and plan.transition.after.stop_outcome is None
    result = e.complete_worker_termination(**completion(stopped, never_started=True))
    assert result.transition.after.stop_outcome == "never_started"


def test_known_instance_cannot_be_reconciled_as_never_started() -> None:
    stopped, _ = stopped_plan(active())
    with denied("recovery_required", 409):
        e.complete_worker_termination(**completion(stopped, never_started=True))


@pytest.mark.parametrize(
    "fault", ["launch", "request", "termination", "epoch", "future", "early_instance"]
)
def test_stale_or_inconsistent_stop_acknowledgement_fails_closed(fault: str) -> None:
    stopped, _ = stopped_plan(active())
    data = completion(stopped)
    proof = data["evidence"]
    fields = {
        "launch": {
            "launch_id": "other-launch",
            "instance": changed(proof.instance, launch_id="other-launch"),
        },
        "request": {"request_sha256": "f" * 64},
        "termination": {"termination_id": "other-stop"},
        "epoch": {"fenced_lifecycle_revision": proof.fenced_lifecycle_revision + 1},
        "future": {"observed_at": data["now"] + 1},
        "early_instance": {"instance": changed(proof.instance, confirmed_at=1199)},
    }[fault]
    data["evidence"] = changed(proof, **fields)
    with denied("recovery_required", 409):
        e.complete_worker_termination(**data)


def test_current_internal_authority_is_required_for_termination_replay_and_completion() -> None:
    stopped, _ = stopped_plan(active())
    authority = changed(
        stopped["authority"], principal=changed(stopped["authority"].principal, active=False)
    )
    with denied("unauthenticated", 401):
        e.terminate_worker_launch(**(stopped | {"authority": authority}))
    with denied("unauthenticated", 401):
        e.complete_worker_termination(**(completion(stopped) | {"authority": authority}))


@pytest.mark.parametrize("missing", ["receipt", "outbox"])
def test_partial_termination_receipt_requires_recovery(missing: str) -> None:
    stopped, _ = stopped_plan(active())
    stopped[missing] = None
    with denied("recovery_required", 409):
        e.terminate_worker_launch(**stopped)


@pytest.mark.parametrize(
    "field,limit",
    [
        ("max_archive_bytes", 499),
        ("max_manifest_bytes", 1),
        ("max_lock_bytes", 1),
        ("max_entries", 1),
        ("max_path_bytes", 1),
        ("max_path_depth", 1),
        ("max_entry_bytes", 1),
        ("max_expanded_bytes", 1),
        ("max_expansion_ratio", 1),
        ("max_metadata_bytes", 1),
    ],
)
def test_package_policy_checks_actual_complete_inventory(field: str, limit: int) -> None:
    policy = changed(value(p.PackagePolicy), **{field: limit})
    inspection = value(p.PackageInspection)
    entries = inspection.entries
    if field == "max_path_depth":
        entries = tuple(
            changed(item, path="nested/" + item.path)
            if item.path != inspection.source.manifest.lock_path
            else item
            for item in entries
        )
        entries = tuple(sorted(entries, key=lambda item: item.path))
    if field == "max_expansion_ratio":
        entries = tuple(changed(item, expanded_bytes=1000) for item in entries)
    inspection = changed(inspection, entries=entries, policy_sha256=message_sha256(policy))
    with denied("invalid_request", 422):
        validate_package_inspection(inspection, policy, now=1200)


def test_complete_boundaries_have_no_authorized_or_verified_boolean() -> None:
    functions: list[Callable[..., Any]] = [
        e.admit_worker_launch,
        e.advance_worker_launch,
        e.authorize_worker_broker,
        e.terminate_worker_launch,
        e.complete_worker_termination,
    ]
    for function in functions:
        assert not {"authorized", "verified", "current_key_valid"} & set(
            inspect.signature(function).parameters
        )
    assert "environment" not in inspect.signature(e.terminate_worker_launch).parameters


def test_unknown_stop_outcome_has_no_success_model() -> None:
    raw = value(w.WorkerTerminationEvidence).model_dump(mode="json") | {"outcome": "unknown"}
    with pytest.raises(ValidationError):
        w.WorkerTerminationEvidence.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize(
    "state,revision",
    [
        ("prepared", 1),
        ("dispatch_unknown", 2),
        ("active", 3),
        ("fenced", 4),
        ("stopping", 5),
        ("stopped", 6),
    ],
)
def test_retained_lifecycle_revision_must_be_reachable(state: str, revision: int) -> None:
    data = active()
    lifecycle = data["lookup"].lifecycle
    if state in {"prepared", "dispatch_unknown"}:
        lifecycle = changed(lifecycle, state=state, instance=None, revision=revision)
    elif state in {"fenced", "stopping", "stopped"}:
        lifecycle = changed(
            lifecycle,
            state=state,
            revision=revision,
            first_fenced_at=1202,
            stopped_at=1202 if state == "stopped" else None,
            stop_outcome="terminated" if state == "stopped" else None,
        )
    else:
        lifecycle = changed(lifecycle, revision=revision)
    data["lookup"] = changed(data["lookup"], lifecycle=lifecycle)
    with denied("recovery_required", 409):
        e.admit_worker_launch(**data)


def test_retained_stop_cannot_complete_before_termination_acceptance() -> None:
    stopped, _ = stopped_plan(active())
    result = e.complete_worker_termination(**completion(stopped))
    stopped.update(
        lookup=changed(stopped["lookup"], lifecycle=result.transition.after),
        receipt=changed(stopped["receipt"], accepted_at=1204),
        now=1205,
    )
    with denied("recovery_required", 409):
        e.terminate_worker_launch(**stopped)


@pytest.mark.parametrize(
    "field",
    [
        "cpu_seconds",
        "wall_seconds",
        "memory_bytes",
        "process_count",
        "scratch_bytes",
        "output_bytes",
    ],
)
def test_current_worker_resource_policy_is_an_actual_bound(field: str) -> None:
    data = args()
    env = data["environment"]
    requested = getattr(data["request"].resources, field)
    if requested == 0:
        data["request"] = changed(
            data["request"], resources=changed(data["request"].resources, **{field: 1})
        )
        requested = 1
    policy = changed(
        env.worker_policy,
        worker_limits=changed(env.worker_policy.worker_limits, **{field: requested - 1}),
    )
    env = replace(
        env,
        worker_policy=policy,
        isolation=changed(env.isolation, worker_policy_sha256=message_sha256(policy)),
    )
    data.update(
        environment=env,
        request=changed(data["request"], worker_policy_sha256=message_sha256(policy)),
    )
    with denied("invalid_request", 422):
        e.admit_worker_launch(**data)


def test_current_configuration_byte_policy_cannot_be_replaced_by_hash_equality() -> None:
    data = args()
    env = data["environment"]
    policy = changed(env.worker_policy, max_configuration_bytes=1)
    data.update(
        environment=replace(
            env,
            worker_policy=policy,
            isolation=changed(env.isolation, worker_policy_sha256=message_sha256(policy)),
        ),
        request=changed(data["request"], worker_policy_sha256=message_sha256(policy)),
    )
    with denied("invalid_request", 422):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize("field", ["recipe_sha256", "builder_image_sha256"])
def test_approval_joins_actual_build_recipe_and_builder_policy(field: str) -> None:
    data = args()
    env = data["environment"]
    original = env.approval
    build = changed(original.build, build=changed(original.build.build, **{field: "f" * 64}))
    scan = changed(original.scan, build_sha256=message_sha256(build))
    approval = changed(
        original,
        build=build,
        scan=scan,
        approval=changed(
            original.approval, build_sha256=message_sha256(build), scan_sha256=message_sha256(scan)
        ),
    )
    data.update(
        environment=replace(env, approval=approval),
        request=changed(data["request"], approval_sha256=message_sha256(approval)),
    )
    with denied("policy_unavailable", 503):
        e.admit_worker_launch(**data)


def test_native_approval_is_not_a_worker_approval_even_with_same_image() -> None:
    data = args()
    env = data["environment"]
    native = value(p.BuiltinAnalyticApproval)
    assert native.build.build.runtime_image_sha256 == env.approval.build.build.runtime_image_sha256
    data["environment"] = e.WorkerEnvironment(**(vars(env) | {"approval": native}))
    with denied("forbidden", 403):
        e.admit_worker_launch(**data)


@pytest.mark.parametrize("now,valid", [(1299, True), (1300, False)])
def test_launch_retry_does_not_reset_original_deadline(now: int, valid: bool) -> None:
    data = active()
    env = data["environment"]
    data.update(
        now=now, environment=replace(env, isolation=changed(env.isolation, valid_until=1400))
    )
    if valid:
        assert isinstance(e.admit_worker_launch(**data), w.WorkerLaunchReplay)
    else:
        with denied("forbidden", 403):
            e.admit_worker_launch(**data)
    assert data["lookup"].record.deadline == 1300


# Restore fixtures retain actual ART1 commit closures. Their trusted origin is a
# producer obligation; these tests exercise the complete composition, not bytes I/O.
def restore_data(index: int = 1) -> dict[str, Any]:
    data = args()
    current = data["environment"].current
    operations = tuple(
        changed(op, workspace_id=current.run.workspace_id) for op in value(ExperimentPage).items[:2]
    )
    source = value(a.CheckpointRecord)
    binding = data["admission"].checkpoint_binding
    request = changed(
        source.request,
        checkpoint=changed(
            source.request.checkpoint, agent_id=binding.agent_id, through_index=index
        ),
        runtime_image_sha256=binding.runtime_image_sha256,
    )
    artifacts = changed(
        source.artifacts,
        workspace_id=current.run.workspace_id,
        checked_at=1199,
        request_sha256=message_sha256(request),
        objects=tuple(
            changed(item, record=changed(item.record, workspace_id=current.run.workspace_id))
            for item in source.artifacts.objects
        ),
    )
    record = changed(
        source,
        workspace_id=current.run.workspace_id,
        index=index,
        attempt_id=current.lease.attempt_id,
        lease_epoch=current.lease.epoch,
        run_revision=current.run.revision,
        committed_at=1199,
        request=request,
        request_sha256=message_sha256(request),
        artifacts=artifacts,
        binding=binding,
    )
    candidate = e.RestoreCandidate(
        lookup=checkpoint_lookup(record),
        operations=operations,
        artifacts=changed(artifacts, checked_at=data["now"]),
        policy=value(a.ArtifactPolicy),
    )
    return select_restore(data, candidate)


def checkpoint_lookup(record: a.CheckpointRecord) -> a.CheckpointLookup:
    outbox = a.CheckpointOutbox(
        event_id="restore-event-1",
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        index=record.index,
        checkpoint_revision=record.checkpoint_revision,
        request_sha256=record.request_sha256,
        record_sha256=message_sha256(record),
    )
    return a.CheckpointLookup(
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        index=record.index,
        revision=record.checkpoint_revision,
        head=a.CheckpointHead(
            index=record.index,
            checkpoint_revision=record.checkpoint_revision,
            request_sha256=record.request_sha256,
        ),
        record=record,
        outbox=outbox,
        latest_record=record,
        latest_outbox=outbox,
    )


def select_restore(data: dict[str, Any], candidate: e.RestoreCandidate) -> dict[str, Any]:
    record = candidate.lookup.record
    assert record is not None
    data["request"] = changed(
        data["request"],
        restore=w.CheckpointRestoreRef(
            index=record.index,
            request_sha256=record.request_sha256,
            record_sha256=message_sha256(record),
        ),
    )
    data["restore"] = candidate
    return data


def test_restore_physical_failure_is_observed_and_returns_only_launch_metadata() -> None:
    data = restore_data()
    candidate = data["restore"]
    assert candidate.operations[1].status == "completed"
    assert candidate.operations[1].result.value.status == "failed"
    plan = planned(data)
    assert plan.record.request.restore == data["request"].restore
    assert "artifacts" not in plan.model_dump()
    assert "checkpoint" not in plan.model_dump()
    retain(data, plan)
    assert isinstance(e.admit_worker_launch(**data), w.WorkerLaunchReplay)


def test_initial_restore_with_pending_first_reservation() -> None:
    data = restore_data(-1)
    env = data["environment"]
    data["environment"] = replace(
        env,
        current=changed(
            env.current, run=changed(env.current.run, experiments_accepted=1, budget_remaining=5)
        ),
    )
    first = data["restore"].operations[0]
    data["restore"] = replace(
        data["restore"], operations=(changed(first, status="running", result=None),)
    )
    ref = planned(data).record.request.restore
    assert ref is not None and ref.index == -1


@pytest.mark.parametrize("status", ["pending", "running", "failed", "cancelled"])
def test_restore_cannot_cross_noncompleted_operation_even_with_later_completion(
    status: str,
) -> None:
    data = restore_data()
    first, second = data["restore"].operations
    first = changed(
        first,
        status=status,
        result=None,
        error={
            "code": "execution_failed",
            "message": "Synthetic",
            "request_id": "synthetic-request",
            "retryable": False,
            "operation_id": first.operation_id,
        }
        if status == "failed"
        else None,
    )
    data["restore"] = replace(data["restore"], operations=(first, second))
    with denied("recovery_required", 409):
        planned(data)


@pytest.mark.parametrize(
    "fault",
    [
        "count",
        "duplicate_ordinal",
        "duplicate_id",
        "foreign_workspace",
        "foreign_run",
        "ordinal_gap",
    ],
)
def test_restore_requires_actual_complete_scoped_unique_ledger(fault: str) -> None:
    data = restore_data()
    first, second = data["restore"].operations
    operations: tuple[Operation, ...]
    if fault == "count":
        operations = (first,)
    elif fault == "duplicate_ordinal":
        operations = (first, first)
    elif fault == "duplicate_id":
        operations = (
            first,
            changed(
                second,
                operation_id=first.operation_id,
                result=changed(
                    second.result,
                    value=changed(second.result.value, operation_id=first.operation_id),
                ),
            ),
        )
    elif fault == "foreign_workspace":
        operations = (changed(first, workspace_id="other"), second)
    elif fault == "foreign_run":
        operations = (changed(first, run_id="other"), second)
    else:
        # Shift both ordinal and the contained scientific record to a real gap.
        operations = (
            first,
            changed(
                second,
                accepted_experiment_index=2,
                result=changed(second.result, value=changed(second.result.value, index=2)),
            ),
        )
    data["restore"] = replace(data["restore"], operations=operations)
    with denied("recovery_required", 409):
        planned(data)


@pytest.mark.parametrize("field", ["record", "outbox", "latest_record", "latest_outbox", "head"])
def test_restore_requires_target_and_latest_committed_witnesses(field: str) -> None:
    data = restore_data()
    data["restore"] = replace(
        data["restore"], lookup=changed(data["restore"].lookup, **{field: None})
    )
    with denied("recovery_required", 409):
        planned(data)


@pytest.mark.parametrize(
    "field,wrong", [("index", 0), ("request_sha256", "0" * 64), ("record_sha256", "0" * 64)]
)
def test_restore_ref_joins_all_actual_selected_identities(field: str, wrong: Any) -> None:
    data = restore_data()
    data["request"] = changed(
        data["request"], restore=changed(data["request"].restore, **{field: wrong})
    )
    with denied("incompatible_state", 409):
        planned(data)


@pytest.mark.parametrize(
    "fault",
    [
        "future_epoch",
        "foreign_same_epoch",
        "future_revision",
        "future_commit",
        "outbox_hash",
        "catalog_revision",
    ],
)
def test_restore_rejects_invalid_current_lineage_commit_and_catalog(fault: str) -> None:
    data = restore_data()
    candidate = data["restore"]
    record = candidate.lookup.record
    if fault in {"future_epoch", "foreign_same_epoch", "future_revision", "future_commit"}:
        updates: dict[str, dict[str, Any]] = {
            "future_epoch": {"lease_epoch": 4},
            "foreign_same_epoch": {"attempt_id": "other"},
            "future_revision": {"run_revision": 5},
            "future_commit": {
                "committed_at": 1201,
                "artifacts": changed(record.artifacts, checked_at=1201),
            },
        }
        record = changed(record, **updates[fault])
        candidate = replace(candidate, lookup=checkpoint_lookup(record))
        select_restore(data, candidate)
    elif fault == "outbox_hash":
        data["restore"] = replace(
            candidate,
            lookup=changed(
                candidate.lookup, outbox=changed(candidate.lookup.outbox, record_sha256="0" * 64)
            ),
        )
    else:
        item = candidate.artifacts.objects[0]
        data["restore"] = replace(
            candidate,
            artifacts=changed(
                candidate.artifacts,
                objects=(
                    changed(item, record=changed(item.record, revision=item.record.revision + 1)),
                ),
            ),
        )
    with denied("recovery_required", 409):
        planned(data)


def test_restore_older_compatible_attempt_and_historical_target_behind_latest() -> None:
    data = restore_data(0)
    candidate = data["restore"]
    older = changed(candidate.lookup.record, lease_epoch=2, attempt_id="attempt-old")
    candidate = replace(candidate, lookup=checkpoint_lookup(older))
    later = restore_data(1)["restore"].lookup.record
    later = changed(later, checkpoint_revision=2)
    later_lookup = checkpoint_lookup(later)
    candidate = replace(
        candidate,
        lookup=changed(
            candidate.lookup,
            revision=2,
            head=later_lookup.head,
            latest_record=later,
            latest_outbox=later_lookup.outbox,
        ),
    )
    select_restore(data, candidate)
    ref = planned(data).record.request.restore
    assert ref is not None and ref.index == 0


@pytest.mark.parametrize("missing", [True, False])
def test_restore_presence_is_exact_without_automatic_selection(missing: bool) -> None:
    data = restore_data()
    if missing:
        data["restore"] = None
    else:
        data["request"] = changed(data["request"], restore=None)
    with denied("recovery_required" if missing else "invalid_request", 409 if missing else 422):
        planned(data)


def test_restore_private_evidence_not_examined_before_current_authority() -> None:
    data = restore_data()
    env = data["environment"]
    data["environment"] = replace(
        env,
        current=changed(
            env.current,
            owner=changed(
                env.current.owner, principal=changed(env.current.owner.principal, active=False)
            ),
        ),
    )
    # This invalid transient object would raise AttributeError if dereferenced.
    data["restore"] = object()
    with denied("forbidden", 403):
        planned(data)
