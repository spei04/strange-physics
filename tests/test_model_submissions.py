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
from strange_physics.research_contracts import message_sha256
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
