from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from strange_physics import model_submission_contracts as m
from strange_physics import model_submissions as s
from strange_physics import worker_contracts as w
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.control_contracts import ContractViolation, VerifiedCredential
from strange_physics.package_contracts import PackagePolicy
from strange_physics.research_contracts import LinearSpringModel, message_sha256
from strange_physics.run_credential_contracts import RunProductAuthority
from strange_physics.worker_execution import WorkerEnvironment
from strange_physics.workspace_contracts import WorkspaceAuthority, WorkspaceView

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "contracts/model-registration.examples.json").read_text())
EXEC = json.loads((ROOT / "contracts/execution.examples.json").read_text())["valid"]
RUN = json.loads((ROOT / "contracts/run-credentials.examples.json").read_text())["valid"]


def value[M: Message](model: type[M]) -> M:
    return model.model_validate_json(
        json.dumps(copy.deepcopy((EXEC | RUN | DATA["valid"])[model.__name__]))
    )


def changed[M: Message](model: M, **fields: Any) -> M:
    return type(model).model_validate(model.model_dump() | fields)


def args() -> dict[str, Any]:
    authority = value(RunProductAuthority)
    current = authority.current
    worker = value(m.ModelRegistrationRecord).worker
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
    environment = WorkerEnvironment(
        current=current,
        workspace=workspace,
        credential_policy=authority.policy,
        package_policy=value(PackagePolicy),
        worker_policy=value(w.WorkerPolicy),
        approval=worker.approval,
        isolation=value(w.IsolationEvidence),
    )
    record = next(
        r
        for r in current.credentials.records
        if r.claims.credential_id == current.credentials.current_credential_id
    )
    claims = record.claims
    authority = changed(authority, verified_claims=claims)
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
    lifecycle = w.WorkerLaunchLifecycle(
        launch_id=worker.launch_id,
        launch_record_sha256=message_sha256(worker),
        revision=2,
        state="active",
        instance=w.RuntimeInstance(
            provider_namespace="synthetic",
            instance_id="instance-1",
            launch_id=worker.launch_id,
            launch_record_sha256=message_sha256(worker),
            confirmed_at=1201,
        ),
        first_fenced_at=None,
        stopped_at=None,
        stop_outcome=None,
    )
    outbox = w.WorkerCommandOutbox(
        command_id=worker.launch_id,
        workspace_id=worker.request.workspace_id,
        run_id=worker.request.run_id,
        launch_id=worker.launch_id,
        launch_record_sha256=message_sha256(worker),
        request_sha256=worker.request_sha256,
        kind="launch",
    )
    worker_lookup = w.WorkerLaunchLookup(
        workspace_id=worker.request.workspace_id,
        run_id=worker.request.run_id,
        attempt_id=worker.request.attempt_id,
        lease_epoch=worker.request.lease_epoch,
        record=worker,
        lifecycle=lifecycle,
        outbox=outbox,
    )
    example = value(m.ModelRegistrationRecord)
    native = s.NativeModelEnvironment(
        policy=value(m.ModelRegistrationPolicy),
        config=example.prediction_config,
        approval=example.approval,
        engine=example.engine,
        artifact=example.artifact,
    )
    scope = example.submission.scope
    return dict(
        request=example.submission.request,
        scope=scope,
        credential=credential,
        authority=authority,
        worker_environment=environment,
        worker_lookup=worker_lookup,
        native=native,
        lookup=m.ModelRegistrationLookup(
            scope=scope,
            stored=None,
            admission=None,
            record=None,
            outbox=None,
        ),
        operation_id="model-operation-new",
        now=1203,
    )


def pending() -> dict[str, Any]:
    data = args()
    plan = s.admit_model_submission(**data)
    assert isinstance(plan, m.ModelAdmissionPlan)
    data["lookup"] = changed(data["lookup"], stored=plan.stored, admission=plan.admission)
    return data


def commit_args(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k != "operation_id"} | dict(
        model_bytes=DATA["model_bytes_utf8"].encode(),
        ledger_bytes=DATA["ledger_bytes_utf8"].encode(),
        model_id="model-new",
        event_id="event-new",
        now=1204,
    )


def committed() -> dict[str, Any]:
    data = pending()
    plan = s.commit_model_submission(**commit_args(data))
    assert isinstance(plan, m.ModelCommitPlan)
    data["lookup"] = changed(
        data["lookup"], stored=plan.after, record=plan.record, outbox=plan.outbox
    )
    data["now"] = 1205
    return data


def denied(code: str, status: int) -> Any:
    return pytest.raises(ContractViolation, match=code, check=lambda error: error.status == status)


def test_pending_commit_and_both_completed_replays() -> None:
    data = pending()
    replay = s.admit_model_submission(**data)
    assert isinstance(replay, m.ModelSubmissionReplay)
    assert replay.operation.status == "pending"
    plan = s.commit_model_submission(**commit_args(data))
    assert isinstance(plan, m.ModelCommitPlan)
    assert plan.record.model.linear == 5
    assert plan.record.model.fitter_version == "unrecognized-but-valid-fitter"
    assert plan.record.canonical_prefix_bytes == 1316
    data["lookup"] = changed(
        data["lookup"], stored=plan.after, record=plan.record, outbox=plan.outbox
    )
    data["now"] = 1205
    for completed_replay in (
        s.admit_model_submission(**data),
        s.commit_model_submission(**(commit_args(data) | {"now": 1205})),
    ):
        assert isinstance(completed_replay, m.ModelSubmissionReplay)
        assert completed_replay.operation == plan.after.operation
        assert "engine_fingerprint" not in completed_replay.model_dump_json()
        assert "object_key" not in completed_replay.model_dump_json()


@pytest.mark.parametrize("entrypoint", ["admit", "commit"])
@pytest.mark.parametrize("fault", ["revoked", "owner_disabled", "fenced"])
def test_complete_worker_authority_precedes_private_inputs(entrypoint: str, fault: str) -> None:
    data = pending()
    if fault == "revoked":
        data["credential"] = changed(data["credential"], revoked=True)
    elif fault == "owner_disabled":
        env = data["worker_environment"]
        current = changed(
            env.current,
            owner=changed(
                env.current.owner, principal=changed(env.current.owner.principal, active=False)
            ),
        )
        data["worker_environment"] = replace(env, current=current)
        data["authority"] = changed(data["authority"], current=current)
    else:
        lookup = data["worker_lookup"]
        data["worker_lookup"] = changed(
            lookup,
            lifecycle=changed(lookup.lifecycle, state="fenced", revision=3, first_fenced_at=1202),
        )
    data["native"] = object()
    data["lookup"] = object()
    with pytest.raises(ContractViolation) as error:
        if entrypoint == "admit":
            s.admit_model_submission(**data)
        else:
            s.commit_model_submission(
                **(commit_args(data) | {"model_bytes": object(), "ledger_bytes": object()})
            )
    assert error.value.status in {401, 403}


@pytest.mark.parametrize("field", ["stored", "admission", "record", "outbox"])
def test_completed_replay_requires_every_commit_witness(field: str) -> None:
    data = committed()
    data["lookup"] = changed(data["lookup"], **{field: None})
    with denied("recovery_required", 409):
        s.admit_model_submission(**data)


@pytest.mark.parametrize("status", ["running", "failed", "cancelled"])
def test_existing_noncompleted_outcomes_remain_explicit(status: str) -> None:
    data = pending()
    operation = data["lookup"].stored.operation
    failure = (
        {
            "code": "invalid_request",
            "message": "Synthetic validation failure",
            "request_id": "synthetic",
            "retryable": False,
            "operation_id": operation.operation_id,
        }
        if status == "failed"
        else None
    )
    stored = changed(
        data["lookup"].stored, operation=changed(operation, status=status, error=failure)
    )
    data["lookup"] = changed(data["lookup"], stored=stored)
    result = s.admit_model_submission(**data)
    assert isinstance(result, m.ModelSubmissionReplay)
    assert result.operation.status == status
    if status in {"failed", "cancelled"}:
        terminal_result = s.commit_model_submission(
            **(commit_args(data) | {"model_bytes": object(), "ledger_bytes": object()})
        )
        assert isinstance(terminal_result, m.ModelSubmissionReplay)
        assert terminal_result.operation.status == status
    else:
        assert isinstance(s.commit_model_submission(**commit_args(data)), m.ModelCommitPlan)


@pytest.mark.parametrize("which", ["model_bytes", "ledger_bytes"])
def test_raw_caps_precede_any_json_parsing(which: str, monkeypatch: pytest.MonkeyPatch) -> None:
    data = commit_args(pending())
    bound = m.MODEL_BYTES if which == "model_bytes" else m.LEDGER_BYTES
    data[which] = b" " * (bound + 1)

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("decoder reached before raw byte bounds")

    monkeypatch.setattr(s, "_parse", unexpected)
    with denied("invalid_request", 422):
        s.commit_model_submission(**data)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e999}',
        b'{"x":' + b"[" * 33 + b"0" + b"]" * 33 + b"}",
        b"\xff",
    ],
)
def test_strict_json_rejects_duplicates_nonfinite_and_depth_before_model(raw: bytes) -> None:
    policy = value(m.ModelRegistrationPolicy)
    with denied("invalid_request", 422):
        s._parse(raw, m.ModelLedgerSnapshot, policy)


def test_canonical_bytes_are_exact_sci_with_unicode_and_signed_zero() -> None:
    observations = ObservationBundle.model_validate_json(json.dumps(DATA["observations"]))
    first = observations.records[0]
    particles = first.experiment.particles
    experiment = changed(
        first.experiment, particles=(changed(particles[0], position=(-0.0, 0.0)), *particles[1:])
    )
    observations = changed(
        observations,
        engine_version="historical-\u03bb-\U0001f680",
        records=(changed(first, experiment=experiment), *observations.records[1:]),
    )
    digest, size = s._bounded_canonical(observations, m.PREFIX_BYTES)
    from strange_physics.serialization import canonical_json

    exact = canonical_json(observations.model_dump(mode="json")).encode()
    assert digest == message_sha256(observations) == hashlib.sha256(exact).hexdigest()
    assert size == len(exact)
    assert b"-0.0" in exact and b"\\u03bb" in exact
    assert s._bounded_canonical(observations, size) == (digest, size)
    with denied("invalid_request", 422):
        s._bounded_canonical(observations, size - 1)


def test_original_engine_and_raw_bytes_mismatch_fail() -> None:
    data = commit_args(pending())
    altered = data["model_bytes"].replace(b"5.0", b"6.0")
    with denied("incompatible_state", 409):
        s.commit_model_submission(**(data | {"model_bytes": altered}))
    ledger = json.loads(data["ledger_bytes"])
    ledger["engine"]["engine_fingerprint"] = "f" * 64
    with denied("incompatible_state", 409):
        s.commit_model_submission(**(data | {"ledger_bytes": json.dumps(ledger).encode()}))


def test_missing_native_policy_fails_after_worker_authority() -> None:
    data = pending()
    data["native"] = replace(data["native"], policy=None)
    with denied("policy_unavailable", 503):
        s.admit_model_submission(**data)


def accept(data: dict[str, Any]) -> dict[str, Any]:
    plan = s.admit_model_submission(**data)
    assert isinstance(plan, m.ModelAdmissionPlan)
    data["lookup"] = changed(data["lookup"], stored=plan.stored, admission=plan.admission)
    return data


def set_model_bytes(data: dict[str, Any], raw: bytes) -> None:
    native = data["native"]
    ref = changed(
        native.artifact.record.ref, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)
    )
    artifact = changed(
        native.artifact,
        record=changed(native.artifact.record, ref=ref),
        verification=changed(
            native.artifact.verification, sha256=ref.sha256, size_bytes=ref.size_bytes
        ),
    )
    model = LinearSpringModel.model_validate_json(raw)
    data["request"] = changed(
        data["request"], model_artifact=ref, model_sha256=message_sha256(model)
    )
    data["native"] = replace(native, artifact=artifact)


@pytest.mark.parametrize("new_row", [False, True])
def test_current_native_approval_renewal_preserves_completed_provenance(new_row: bool) -> None:
    data = committed()
    original = data["lookup"]
    native = data["native"]
    old = native.approval
    scan = changed(old.scan, scan_id="renewed-scan", observed_at=1204, valid_until=1900)
    approval = changed(
        old.approval,
        approval_id="renewed-approval" if new_row else old.approval.approval_id,
        revision=1 if new_row else old.approval.revision + 1,
        scan_sha256=message_sha256(scan),
        decided_at=1204,
    )
    data["native"] = replace(native, approval=changed(old, scan=scan, approval=approval))
    replay = s.admit_model_submission(**data)
    assert isinstance(replay, m.ModelSubmissionReplay)
    assert replay.operation == original.stored.operation
    assert data["lookup"] == original
    assert isinstance(
        s.commit_model_submission(**(commit_args(data) | {"now": 1205})), m.ModelSubmissionReplay
    )


@pytest.mark.parametrize("fault", ["lower_revision", "changed_equal_revision", "different_source"])
def test_replay_rejects_native_approval_rollback_or_changed_build(fault: str) -> None:
    data = committed()
    native = data["native"]
    old = native.approval
    if fault == "different_source":
        source = changed(old.build.source, commit="a" * 40)
        build = changed(
            old.build,
            source=source,
            build=changed(old.build.build, source_sha256=message_sha256(source)),
        )
        scan = changed(old.scan, build_sha256=message_sha256(build))
        approval = changed(
            old.approval, build_sha256=message_sha256(build), scan_sha256=message_sha256(scan)
        )
        revised = changed(old, build=build, scan=scan, approval=approval)
        code = "incompatible_state"
    else:
        revision = old.approval.revision - 1 if fault == "lower_revision" else old.approval.revision
        revised = changed(old, approval=changed(old.approval, revision=revision, decided_at=1204))
        code = "recovery_required"
    data["native"] = replace(native, approval=revised)
    with denied(code, 409):
        s.admit_model_submission(**data)
    if fault == "different_source":
        # A fresh independently approved source is valid; only retained identity is immutable.
        data["lookup"] = m.ModelRegistrationLookup(
            scope=data["scope"], stored=None, admission=None, record=None, outbox=None
        )
        assert isinstance(s.admit_model_submission(**data), m.ModelAdmissionPlan)


def test_raw_formatting_changes_object_identity_but_preserves_canonical_model() -> None:
    data = args()
    model = json.loads(DATA["model_bytes_utf8"])
    raw = json.dumps(model, sort_keys=True, separators=(",", ":")).encode()
    original = data["request"]
    set_model_bytes(data, raw)
    assert data["request"].model_sha256 == original.model_sha256
    assert data["request"].model_artifact.sha256 != original.model_artifact.sha256
    result = s.commit_model_submission(**(commit_args(accept(data)) | {"model_bytes": raw}))
    assert isinstance(result, m.ModelCommitPlan)
    assert result.record.model.linear == 5


@pytest.mark.parametrize(
    "fault", ["count", "gap", "duplicate_id", "pending", "revision", "sampling", "action"]
)
def test_actual_full_ledger_and_public_space_are_required(fault: str) -> None:
    data = commit_args(pending())
    ledger = json.loads(data["ledger_bytes"])
    if fault == "count":
        ledger["operations"].pop()
    elif fault == "gap":
        ledger["operations"][1]["accepted_experiment_index"] = 2
        ledger["operations"][1]["result"]["value"]["index"] = 2
    elif fault == "duplicate_id":
        ledger["operations"][1]["operation_id"] = "op-0"
        ledger["operations"][1]["result"]["value"]["operation_id"] = "op-0"
    elif fault == "pending":
        ledger["operations"][1]["status"] = "pending"
        ledger["operations"][1]["result"] = None
    elif fault == "revision":
        ledger["run_revision"] -= 1
    elif fault == "sampling":
        ledger["operations"][0]["result"]["value"]["trajectory"]["frames"].pop()
    else:
        ledger["operations"][0]["result"]["value"]["experiment"]["particles"][0]["position"][0] = (
            3.0
        )
    with pytest.raises(ContractViolation):
        s.commit_model_submission(**(data | {"ledger_bytes": json.dumps(ledger).encode()}))


def test_failed_scientific_record_cannot_be_selected_as_fit_row() -> None:
    data = args()
    model = json.loads(DATA["model_bytes_utf8"])
    model["fit_record_indices"] = [0, 1]
    raw = json.dumps(model).encode()
    set_model_bytes(data, raw)
    with denied("invalid_request", 422):
        s.commit_model_submission(**(commit_args(accept(data)) | {"model_bytes": raw}))


@pytest.mark.parametrize("tail_status", ["completed", "pending"])
def test_current_append_preserves_exact_historical_prefix(tail_status: str) -> None:
    data = committed()
    current = data["worker_environment"].current
    run = changed(current.run, revision=5, experiments_accepted=3, budget_remaining=3)
    current = changed(current, run=run)
    data["worker_environment"] = replace(data["worker_environment"], current=current)
    data["authority"] = changed(data["authority"], current=current)
    ledger = json.loads(DATA["ledger_bytes_utf8"])
    ledger["run_revision"] = 5
    tail = copy.deepcopy(ledger["operations"][0])
    tail["operation_id"] = "op-2"
    tail["accepted_experiment_index"] = 2
    tail["status"] = tail_status
    if tail_status == "pending":
        tail["result"] = None
    else:
        tail["result"]["value"]["operation_id"] = "op-2"
        tail["result"]["value"]["index"] = 2
    ledger["operations"].append(tail)
    result = s.commit_model_submission(
        **(commit_args(data) | {"now": 1205, "ledger_bytes": json.dumps(ledger).encode()})
    )
    assert isinstance(result, m.ModelSubmissionReplay)
    assert result.operation == data["lookup"].stored.operation


def test_same_attempt_key_rotation_uses_current_authority_not_original_audit_key() -> None:
    data = committed()
    current = data["worker_environment"].current
    old = current.credentials.records[0]
    claims = changed(
        old.claims, credential_id="rotated-key", generation=2, issued_at=1204, expires_at=1450
    )
    records = (changed(old, claims=claims), changed(old, revoked_at=1204))
    keys = changed(
        current.credentials,
        revision=2,
        last_generation=2,
        current_credential_id=claims.credential_id,
        records=records,
    )
    current = changed(current, credentials=keys)
    data["worker_environment"] = replace(data["worker_environment"], current=current)
    data["authority"] = changed(data["authority"], current=current, verified_claims=claims)
    data["credential"] = changed(
        data["credential"], credential_id=claims.credential_id, expires_at=claims.expires_at
    )
    assert data["worker_lookup"].record.original_credential_id == "worker-key-1"
    assert isinstance(s.admit_model_submission(**data), m.ModelSubmissionReplay)
    assert isinstance(
        s.commit_model_submission(**(commit_args(data) | {"now": 1205})), m.ModelSubmissionReplay
    )


def test_canonical_prefix_cap_is_separate_and_no_truncation_is_permitted() -> None:
    data = pending()
    native = data["native"]
    data["native"] = replace(native, policy=changed(native.policy, max_canonical_prefix_bytes=1315))
    with denied("invalid_request", 422):
        s.commit_model_submission(**commit_args(data))
    data["native"] = replace(native, policy=changed(native.policy, max_canonical_prefix_bytes=1316))
    assert isinstance(s.commit_model_submission(**commit_args(data)), m.ModelCommitPlan)


def test_json_node_guard_runs_before_decoding(monkeypatch: pytest.MonkeyPatch) -> None:
    policy = changed(value(m.ModelRegistrationPolicy), max_json_nodes=2)

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("JSON decoder reached after lexical node cap")

    monkeypatch.setattr(json, "loads", unexpected)
    with denied("invalid_request", 422):
        s._parse(b'{"a": 1, "b": 2}', m.ModelLedgerSnapshot, policy)


@pytest.mark.parametrize("decided_at", [1012, 1013, 1014])
def test_same_approval_row_revision_cannot_move_decision_time_backwards(decided_at: int) -> None:
    data = committed()
    native = data["native"]
    old = native.approval
    revised = changed(
        old,
        approval=changed(old.approval, revision=old.approval.revision + 1, decided_at=decided_at),
    )
    assert revised.scan == old.scan
    data["native"] = replace(native, approval=revised)
    if decided_at < old.approval.decided_at:
        with denied("recovery_required", 409):
            s.admit_model_submission(**data)
    else:
        assert isinstance(s.admit_model_submission(**data), m.ModelSubmissionReplay)
