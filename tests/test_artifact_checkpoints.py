from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from strange_physics import artifact_contracts as a
from strange_physics.artifact_checkpoints import (
    validate_artifact_content,
    validate_artifact_update,
    validate_checkpoint_restore_candidate,
    validate_checkpoint_write,
)
from strange_physics.contracts import Message
from strange_physics.control_contracts import (
    ContractViolation,
    ExperimentPage,
    Operation,
    VerifiedCredential,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import RunProductAuthority
from strange_physics.serialization import canonical_json
from strange_physics.workspace_contracts import WorkspaceAuthority, WorkspaceView

ROOT = Path(__file__).resolve().parents[1]
ART = json.loads((ROOT / "contracts/artifacts.examples.json").read_text())["valid"]
RUN = json.loads((ROOT / "contracts/run-credentials.examples.json").read_text())["valid"]
CONTROL = json.loads((ROOT / "contracts/control.examples.json").read_text())["valid"]


def value[T: Message](model: type[T]) -> T:
    return model.model_validate_json(
        json.dumps(copy.deepcopy((ART | RUN | CONTROL)[model.__name__]))
    )


def changed[T: Message](model: T, **changes: Any) -> T:
    return type(model).model_validate(model.model_dump() | changes)


def args(**changes: Any) -> dict[str, Any]:
    authority = value(RunProductAuthority)
    current = authority.current
    authority = changed(
        authority,
        current=changed(
            current,
            run=changed(
                current.run, experiments_accepted=0, budget_remaining=current.run.space.budget
            ),
        ),
    )
    claims = authority.verified_claims
    member = current.owner.grant.membership
    workspace = WorkspaceAuthority(
        workspace=WorkspaceView(
            workspace_id=member.workspace_id,
            display_name="Synthetic",
            visibility="private",
            state="active",
            revision=2,
        ),
        active_owner_ids=(member.principal_id,),
        disabled_owner_ids=(),
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
    request = value(a.CheckpointRequest)
    policy = value(a.ArtifactPolicy)
    evidence = value(a.CheckpointArtifacts)
    evidence = changed(
        evidence,
        workspace_id=member.workspace_id,
        checked_at=1200,
        objects=tuple(
            changed(item, record=changed(item.record, workspace_id=member.workspace_id))
            for item in evidence.objects
        ),
    )
    attempt = a.CheckpointAttempt(
        workspace_id=member.workspace_id,
        run_id=current.run.run_id,
        attempt_id=current.lease.attempt_id,
        lease_epoch=current.lease.epoch,
        binding=value(a.CheckpointRecord).binding,
    )
    return (
        dict(
            request=request,
            workspace=workspace,
            credential=credential,
            membership=member,
            authority=authority,
            policy=policy,
            attempt=attempt,
            artifacts=evidence,
            operations=(),
            lookup=a.CheckpointLookup(
                workspace_id=member.workspace_id,
                run_id=current.run.run_id,
                index=-1,
                revision=0,
                head=None,
                record=None,
                outbox=None,
            ),
            path_index=-1,
            now=1200,
            event_id="checkpoint-event-1",
        )
        | changes
    )


def plan(data: dict[str, Any]) -> a.CheckpointCommitPlan:
    result = validate_checkpoint_write(**data)
    assert isinstance(result, a.CheckpointCommitPlan)
    return result


def replay_args(data: dict[str, Any], committed: a.CheckpointCommitPlan) -> dict[str, Any]:
    return data | dict(
        now=data["now"] + 1,
        event_id=None,
        artifacts=changed(data["artifacts"], checked_at=data["now"] + 1),
        lookup=a.CheckpointLookup(
            workspace_id=committed.record.workspace_id,
            run_id=committed.record.run_id,
            index=committed.record.index,
            revision=committed.record.checkpoint_revision,
            head=committed.head,
            record=committed.record,
            outbox=committed.outbox,
        ),
    )


def denied(code: str, status: int) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda e: e.status == status)


def test_fresh_atomic_commit_and_lost_ack_replay_preserve_exact_body() -> None:
    data = args()
    original_authority = data["authority"]
    result = plan(data)
    assert result.record.request == data["request"]
    assert result.outbox.record_sha256 == message_sha256(result.record)
    assert result.record.checkpoint_revision == 1
    retry = validate_checkpoint_write(**replay_args(data, result))
    assert isinstance(retry, a.CheckpointReplay)
    assert retry.request == data["request"]
    assert data["authority"] == original_authority
    assert result.head.index == -1


def test_complete_boundary_requires_authority_evidence_and_actual_request() -> None:
    signature = inspect.signature(validate_checkpoint_write)
    for name in ("authority", "artifacts", "request", "attempt", "operations"):
        assert signature.parameters[name].default is inspect.Parameter.empty
    assert "artifacts_verified" not in signature.parameters
    assert "full_request_sha256" not in signature.parameters
    assert "committed_prefix" not in signature.parameters


@pytest.mark.parametrize("replay", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "credential_revoked",
        "expired",
        "owner_disabled",
        "grant_revoked",
        "owner_generation",
        "grant_incarnation",
        "lease_revoked",
        "lease_epoch",
        "current_key_removed",
        "cancelled",
        "workspace_frozen",
        "viewer",
    ],
)
def test_current_authority_precedes_partial_lookup_and_invalid_objects(
    replay: bool, fault: str
) -> None:
    data = args()
    if replay:
        data = replay_args(data, plan(data))
    authority = data["authority"]
    current = authority.current
    code, status = "forbidden", 403
    if fault == "credential_revoked":
        data["credential"] = changed(data["credential"], revoked=True)
        code, status = "unauthenticated", 401
    elif fault == "expired":
        data["now"] = authority.verified_claims.expires_at
    elif fault == "owner_disabled":
        current = changed(
            current,
            owner=changed(current.owner, principal=changed(current.owner.principal, active=False)),
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
    elif fault == "owner_generation":
        current = changed(
            current,
            owner=changed(current.owner, principal=changed(current.owner.principal, generation=1)),
        )
    elif fault == "grant_incarnation":
        current = changed(
            current, owner=changed(current.owner, grant=changed(current.owner.grant, incarnation=1))
        )
    elif fault == "lease_revoked":
        current = changed(current, lease=changed(current.lease, revoked=True))
    elif fault == "lease_epoch":
        current = changed(current, lease=changed(current.lease, epoch=4))
    elif fault == "current_key_removed":
        current = changed(
            current, credentials=changed(current.credentials, current_credential_id=None)
        )
    elif fault == "cancelled":
        current = changed(
            current,
            run=changed(current.run, status="cancelling"),
            lease=changed(current.lease, status="cancelling"),
        )
        code, status = "incompatible_state", 409
    elif fault == "workspace_frozen":
        data["workspace"] = changed(
            data["workspace"], workspace=changed(data["workspace"].workspace, state="quarantined")
        )
    else:
        member = changed(current.owner.grant.membership, role="viewer")
        current = changed(
            current,
            owner=changed(current.owner, grant=changed(current.owner.grant, membership=member)),
        )
        data["membership"] = member
    if fault in {"expired", "lease_epoch", "current_key_removed"}:
        code, status = "unauthenticated", 401
    data["authority"] = changed(authority, current=current)
    data["lookup"] = changed(data["lookup"], revision=1, head=None)
    data["artifacts"] = changed(data["artifacts"], request_sha256="f" * 64)
    with denied(code, status):
        validate_checkpoint_write(**data)


@pytest.mark.parametrize("fault", ["request", "policy", "time", "missing", "foreign_run"])
def test_actual_evidence_binding(fault: str) -> None:
    data = args()
    evidence = data["artifacts"]
    if fault == "request":
        evidence = changed(evidence, request_sha256="b" * 64)
    elif fault == "policy":
        evidence = changed(evidence, policy_sha256="b" * 64)
    elif fault == "time":
        evidence = changed(evidence, checked_at=1199)
    elif fault == "missing":
        evidence = changed(evidence, objects=())
    else:
        evidence = changed(
            evidence,
            run_id="other",
            objects=tuple(
                changed(item, record=changed(item.record, run_id="other"))
                for item in evidence.objects
            ),
        )
    with denied("invalid_request", 422):
        validate_checkpoint_write(**(data | {"artifacts": evidence}))


@pytest.mark.parametrize(
    "field,value_",
    [
        ("state", "uploading"),
        ("state", "tombstoned"),
        ("state", "deleted"),
        ("visibility", "evaluator-only"),
        ("visibility", "workspace-private"),
        ("visibility", "public"),
    ],
)
@pytest.mark.parametrize("replay", [False, True])
def test_unavailable_or_unauthorized_object_is_never_acknowledged(
    field: str, value_: Any, replay: bool
) -> None:
    data = args()
    if replay:
        data = replay_args(data, plan(data))
    item = data["artifacts"].objects[0]
    evidence = changed(
        data["artifacts"], objects=(changed(item, record=changed(item.record, **{field: value_})),)
    )
    with denied("invalid_request", 422):
        validate_checkpoint_write(**(data | {"artifacts": evidence}))


@pytest.mark.parametrize(
    "fault",
    [
        "missing_head",
        "missing_record",
        "missing_outbox",
        "foreign_lookup",
        "head_revision",
        "head_hash",
        "outbox_hash",
        "outbox_record",
        "future_commit",
        "regressed_run",
    ],
)
def test_partial_or_corrupt_retained_commit_requires_recovery(fault: str) -> None:
    data = args()
    data = replay_args(data, plan(data))
    lookup = data["lookup"]
    if fault == "missing_head":
        lookup = changed(lookup, head=None)
    elif fault == "missing_record":
        lookup = changed(lookup, record=None)
    elif fault == "missing_outbox":
        lookup = changed(lookup, outbox=None)
    elif fault == "foreign_lookup":
        lookup = changed(lookup, run_id="other")
    elif fault == "head_revision":
        lookup = changed(lookup, revision=2)
    elif fault == "head_hash":
        lookup = changed(lookup, head=changed(lookup.head, request_sha256="b" * 64))
    elif fault == "outbox_hash":
        lookup = changed(lookup, outbox=changed(lookup.outbox, request_sha256="b" * 64))
    elif fault == "outbox_record":
        lookup = changed(lookup, outbox=changed(lookup.outbox, record_sha256="b" * 64))
    elif fault == "future_commit":
        record = changed(
            lookup.record,
            committed_at=1300,
            artifacts=changed(lookup.record.artifacts, checked_at=1300),
        )
        lookup = changed(
            lookup,
            record=record,
            outbox=changed(lookup.outbox, record_sha256=message_sha256(record)),
        )
    else:
        authority = data["authority"]
        data["authority"] = changed(
            authority,
            current=changed(authority.current, run=changed(authority.current.run, revision=0)),
        )
    with denied("recovery_required", 409):
        validate_checkpoint_write(**(data | {"lookup": lookup}))


@pytest.mark.parametrize("fault", ["locator", "created_at", "revision"])
def test_replay_joins_current_artifacts_to_retained_physical_identity(fault: str) -> None:
    data = args()
    data = replay_args(data, plan(data))
    item = data["artifacts"].objects[0]
    if fault == "locator":
        locator = changed(item.record.locator, namespace_id="other")
        item = changed(
            item,
            record=changed(item.record, locator=locator),
            verification=changed(item.verification, locator=locator),
        )
    elif fault == "created_at":
        item = changed(item, record=changed(item.record, created_at=99))
    else:
        item = changed(item, record=changed(item.record, revision=1))
    with denied("recovery_required", 409):
        validate_checkpoint_write(
            **(data | {"artifacts": changed(data["artifacts"], objects=(item,))})
        )


@pytest.mark.parametrize(
    "field,value_",
    [
        ("max_artifacts", 0),
        ("max_artifact_bytes", 11),
        ("max_total_artifact_bytes", 11),
        ("max_envelope_bytes", 1),
        ("max_state_depth", 1),
        ("max_state_nodes", 1),
        ("allowed_media_types", ("application/octet-stream",)),
    ],
)
def test_actual_policy_limits_apply_before_replay(field: str, value_: Any) -> None:
    data = args()
    data = replay_args(data, plan(data))
    policy = changed(data["policy"], **{field: value_})
    evidence = changed(data["artifacts"], policy_sha256=message_sha256(policy))
    with denied("invalid_request", 422):
        validate_checkpoint_write(**(data | {"policy": policy, "artifacts": evidence}))


def test_missing_policy_blocks_before_commit_and_replay() -> None:
    data = args()
    with denied("policy_unavailable", 503):
        validate_checkpoint_write(**(data | {"policy": None}))
    data = replay_args(data, plan(data))
    with denied("policy_unavailable", 503):
        validate_checkpoint_write(**(data | {"policy": None}))


def test_byte_and_state_policy_equal_boundaries() -> None:
    data = args()
    request = data["request"]
    size = len(canonical_json(request.model_dump(mode="json")).encode("utf-8"))
    policy = changed(
        data["policy"],
        max_envelope_bytes=size,
        max_artifacts=1,
        max_artifact_bytes=12,
        max_total_artifact_bytes=12,
        max_state_depth=3,
        max_state_nodes=5,
    )
    data |= {
        "policy": policy,
        "artifacts": changed(data["artifacts"], policy_sha256=message_sha256(policy)),
    }
    assert plan(data)
    with denied("invalid_request", 422):
        validate_checkpoint_write(
            **(data | {"policy": changed(policy, max_envelope_bytes=size - 1)})
        )


def test_changed_existing_body_conflicts_after_valid_current_evidence() -> None:
    data = args()
    data = replay_args(data, plan(data))
    request = changed(
        data["request"], checkpoint=changed(data["request"].checkpoint, state={"x": 1})
    )
    with denied("idempotency_conflict", 409):
        validate_checkpoint_write(
            **(
                data
                | {
                    "request": request,
                    "artifacts": changed(data["artifacts"], request_sha256=message_sha256(request)),
                }
            )
        )


def ledger_data() -> dict[str, Any]:
    data = args()
    authority = data["authority"]
    run = authority.current.run
    operations = tuple(
        changed(op, workspace_id=run.workspace_id) for op in value(ExperimentPage).items[:2]
    )
    assert all(op.status == "completed" for op in operations)
    data["authority"] = changed(
        authority,
        current=changed(
            authority.current,
            run=changed(run, experiments_accepted=2, budget_remaining=run.space.budget - 2),
        ),
    )
    data["operations"] = operations
    return data


def at_index(data: dict[str, Any], index: int) -> dict[str, Any]:
    request = changed(
        data["request"], checkpoint=changed(data["request"].checkpoint, through_index=index)
    )
    return data | {
        "request": request,
        "path_index": index,
        "artifacts": changed(data["artifacts"], request_sha256=message_sha256(request)),
        "lookup": changed(data["lookup"], index=index),
    }


def test_physics_failure_advances_prefix_and_historical_replay_preserves_later_head() -> None:
    data = at_index(ledger_data(), 0)
    first = plan(data)
    later = at_index(data, 1) | {"event_id": "checkpoint-event-2"}
    later |= {
        "lookup": a.CheckpointLookup(
            workspace_id=first.record.workspace_id,
            run_id=first.record.run_id,
            index=1,
            revision=1,
            head=first.head,
            record=None,
            outbox=None,
        )
    }
    second = plan(later)
    retry = replay_args(data, first)
    retry["lookup"] = changed(retry["lookup"], revision=2, head=second.head)
    assert isinstance(validate_checkpoint_write(**retry), a.CheckpointReplay)
    assert retry["lookup"].head.index == 1


@pytest.mark.parametrize("fault", ["missing", "duplicate", "foreign", "pending", "aborted"])
def test_prefix_is_derived_from_complete_accepted_operations(fault: str) -> None:
    data = at_index(ledger_data(), 1)
    first, second = data["operations"]
    code = "recovery_required"
    operations: tuple[Operation, ...]
    if fault == "missing":
        operations = (first,)
    elif fault == "duplicate":
        operations = (first, first)
    elif fault == "foreign":
        operations = (changed(first, workspace_id="other"), second)
    elif fault == "pending":
        operations = (changed(first, status="running", result=None), second)
        code = "incompatible_state"
    else:
        operations = (changed(first, status="cancelled", result=None), second)
        code = "incompatible_state"
    with denied(code, 409):
        validate_checkpoint_write(**(data | {"operations": operations}))


@pytest.mark.parametrize("field,value_", [("attempt_id", "stale"), ("lease_epoch", 2)])
def test_pinned_attempt_must_match_current_lease(field: str, value_: Any) -> None:
    data = args()
    with denied("forbidden", 403):
        validate_checkpoint_write(
            **(data | {"attempt": changed(data["attempt"], **{field: value_})})
        )


@pytest.mark.parametrize("field", ["agent_id", "runtime_image_sha256"])
def test_request_matches_pinned_attempt(field: str) -> None:
    data = args()
    binding = changed(
        data["attempt"].binding, **{field: "other" if field == "agent_id" else "b" * 64}
    )
    with denied("incompatible_state", 409):
        validate_checkpoint_write(**(data | {"attempt": changed(data["attempt"], binding=binding)}))


def test_restore_checks_current_objects_but_confers_no_authority() -> None:
    data = args()
    record = plan(data).record
    validate_checkpoint_restore_candidate(
        record,
        expected_attempt=data["attempt"],
        policy=data["policy"],
        artifacts=data["artifacts"],
        now=data["now"],
    )
    assert "NON-AUTHORIZING" in (validate_checkpoint_restore_candidate.__doc__ or "")
    with denied("invalid_request", 422):
        validate_checkpoint_restore_candidate(
            record,
            expected_attempt=data["attempt"],
            policy=data["policy"],
            artifacts=changed(data["artifacts"], objects=()),
            now=data["now"],
        )
    with denied("incompatible_state", 409):
        validate_checkpoint_restore_candidate(
            record,
            expected_attempt=changed(
                data["attempt"],
                binding=changed(data["attempt"].binding, agent_config_sha256="f" * 64),
            ),
            policy=data["policy"],
            artifacts=data["artifacts"],
            now=data["now"],
        )


def test_raw_byte_verification_rejects_truncation_corruption_and_canonical_hash_substitution() -> (
    None
):
    content = b'{ "x" : 1 }\n'
    ref = changed(
        value(a.ArtifactRef), sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content)
    )
    policy = value(a.ArtifactPolicy)
    validate_artifact_content(ref, content, policy)
    for data in (content[:-1], content.replace(b"1", b"2")):
        with denied("invalid_request", 422):
            validate_artifact_content(ref, data, policy)
    canonical_digest = hashlib.sha256(canonical_json({"x": 1}).encode("utf-8")).hexdigest()
    assert canonical_digest != ref.sha256
    with denied("invalid_request", 422):
        validate_artifact_content(changed(ref, sha256=canonical_digest), content, policy)


@pytest.mark.parametrize(
    "before_state,after_state,valid",
    [
        ("uploading", "available", True),
        ("uploading", "tombstoned", True),
        ("available", "tombstoned", True),
        ("tombstoned", "deleted", True),
        ("tombstoned", "available", False),
        ("deleted", "available", False),
        ("available", "uploading", False),
        ("available", "deleted", False),
    ],
)
def test_artifact_lifecycle_never_resurrects_or_skips_tombstone(
    before_state: str, after_state: str, valid: bool
) -> None:
    before = changed(value(a.RunArtifactRecord), state=before_state)
    after = changed(before, state=after_state, revision=before.revision + 1)
    if valid:
        validate_artifact_update(before, after)
    else:
        with denied("incompatible_state", 409):
            validate_artifact_update(before, after)


def test_artifact_lifecycle_preserves_immutable_identity_and_cas() -> None:
    before = value(a.RunArtifactRecord)
    validate_artifact_update(before, before)
    for after in (
        changed(before, state="tombstoned"),
        changed(before, state="tombstoned", revision=4),
        changed(before, state="tombstoned", revision=3, visibility="public"),
        changed(before, state="tombstoned", revision=3, ref=changed(before.ref, generation="2")),
    ):
        with denied("incompatible_state", 409):
            validate_artifact_update(before, after)
