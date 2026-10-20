from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from strange_physics.contracts import Checkpoint, Experiment, Message, ObservationBundle
from strange_physics.control_contracts import (
    CONTROL_MODELS,
    ROUTE_PERMISSIONS,
    CheckpointBinding,
    ContractViolation,
    CreateRunRequest,
    EmptyRequest,
    ExperimentPage,
    IdempotencyScope,
    Membership,
    Operation,
    RunLease,
    RunView,
    StoredRequest,
    VerifiedCredential,
    authorize,
    check_idempotency,
    checkpoint_request_sha256,
    contiguous_record_prefix,
    control_json_schema,
    validate_checkpoint_metadata,
    validate_experiment_admission,
    validate_operation_update,
    validate_run_transition,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES: dict[str, Any] = json.loads((ROOT / "contracts/control.examples.json").read_text())


def parse[T: Message](model: type[T], **changes: object) -> T:
    value = copy.deepcopy(FIXTURES["valid"][model.__name__])
    value.update(changes)
    return model.model_validate_json(json.dumps(value))


def changed[T: Message](value: T, **changes: object) -> T:
    payload = value.model_dump(mode="json")
    payload.update(changes)
    return type(value).model_validate_json(
        json.dumps(payload, default=lambda item: item.model_dump(mode="json"))
    )


def run_credential(**changes: object) -> VerifiedCredential:
    value = copy.deepcopy(FIXTURES["run_credential"])
    value.update(changes)
    return VerifiedCredential.model_validate_json(json.dumps(value))


def experiments() -> tuple[Operation, ...]:
    return parse(ExperimentPage).items


def checkpoint(**changes: object) -> Checkpoint:
    value = copy.deepcopy(FIXTURES["checkpoint"])
    value.update(changes)
    return Checkpoint.model_validate_json(json.dumps(value))


def check_write(value: Checkpoint | None = None, **changes: Any) -> str:
    args: dict[str, Any] = {
        "path_index": 0,
        "binding": parse(CheckpointBinding),
        "expected_binding": parse(CheckpointBinding),
        "full_request_sha256": FIXTURES["checkpoint_digest"],
        "stored_request_sha256": None,
        "latest_index": -1,
        "committed_prefix": 1,
    }
    args.update(changes)
    return validate_checkpoint_metadata(checkpoint() if value is None else value, **args)


@pytest.mark.parametrize("model", CONTROL_MODELS)
def test_synthetic_round_trips_forbid_hidden_fields(model: type[Message]) -> None:
    value = FIXTURES["valid"][model.__name__]
    assert model.model_validate_json(json.dumps(value)).model_dump(mode="json") == value
    invalid = dict(value, hidden_world={"linear": 1.0})
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate_json(json.dumps(invalid))


@pytest.mark.parametrize("case", FIXTURES["schema_negative"])
def test_shared_structural_negative_fixtures(case: dict[str, Any]) -> None:
    model = next(model for model in CONTROL_MODELS if model.__name__ == case["model"])
    with pytest.raises(ValidationError):
        parse(model, **{case["field"]: case["value"]})


def test_self_contained_schema_matches_runtime_generation() -> None:
    schema = json.loads((ROOT / "contracts/control.schema.json").read_text())
    assert schema == control_json_schema()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                reference = node["$ref"]
                assert isinstance(reference, str) and reference.startswith("#/")
                target = schema
                for part in reference[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                assert isinstance(target, dict)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)


def test_exact_canonical_identity_includes_defaults_and_ignores_key_order() -> None:
    request = parse(CreateRunRequest)
    assert (
        canonical_json(request.model_dump(mode="json")) == FIXTURES["canonical_create"]["utf8_text"]
    )
    assert message_sha256(request) == FIXTURES["canonical_create"]["sha256"]
    reversed_fields = dict(reversed(list(request.model_dump(mode="json").items())))
    same = CreateRunRequest.model_validate_json(json.dumps(reversed_fields))
    assert message_sha256(same) == message_sha256(request)
    assert message_sha256(changed(request, experiment_budget=5)) != message_sha256(request)


@pytest.mark.parametrize("role", ["owner", "researcher"])
def test_workspace_create_requires_current_membership_and_scope(role: str) -> None:
    authorize(
        parse(VerifiedCredential),
        parse(Membership, role=role),
        permission="runs:create",
        workspace_id="ws-1",
        now=100,
    )


@pytest.mark.parametrize(
    ("credential_changes", "membership_changes", "workspace", "code", "status"),
    [
        ({"revoked": True}, {}, "ws-1", "unauthenticated", 401),
        ({"expires_at": 100}, {}, "ws-1", "unauthenticated", 401),
        ({}, {"active": False}, "ws-1", "forbidden", 403),
        ({}, {"role": "viewer"}, "ws-1", "forbidden", 403),
        ({"scopes": ["runs:read"]}, {}, "ws-1", "forbidden", 403),
        ({}, {}, "ws-2", "not_found", 404),
        ({}, {"principal_id": "someone-else"}, "ws-1", "not_found", 404),
    ],
)
def test_current_identity_and_tenant_denials(
    credential_changes: dict[str, object],
    membership_changes: dict[str, object],
    workspace: str,
    code: str,
    status: int,
) -> None:
    with pytest.raises(ContractViolation) as raised:
        authorize(
            parse(VerifiedCredential, **credential_changes),
            parse(Membership, **membership_changes),
            permission="runs:create",
            workspace_id=workspace,
            now=100,
        )
    assert (raised.value.code, raised.value.status) == (code, status)


@pytest.mark.parametrize("kind", ["user", "service"])
def test_workspace_credential_cannot_act_as_worker(kind: str) -> None:
    credential = parse(VerifiedCredential, kind=kind, scopes=["experiments:write"])
    with pytest.raises(ContractViolation, match="forbidden"):
        authorize(
            credential,
            parse(Membership),
            permission="experiments:write",
            workspace_id="ws-1",
            run_id="run-1",
            now=100,
            lease=parse(RunLease),
        )


def test_viewer_read_and_run_lease_authorization() -> None:
    authorize(
        parse(VerifiedCredential),
        parse(Membership, role="viewer"),
        permission="runs:read",
        workspace_id="ws-1",
        now=100,
    )
    authorize(
        run_credential(),
        parse(Membership),
        permission="experiments:write",
        workspace_id="ws-1",
        run_id="run-1",
        now=100,
        lease=parse(RunLease),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"epoch": 4},
        {"attempt_id": "attempt-2"},
        {"revoked": True},
        {"expires_at": 100},
        {"run_deadline": 100},
        {"status": "cancelling"},
        {"status": "recovering"},
        {"status": "completed"},
        {"workspace_id": "ws-2"},
        {"run_id": "run-2"},
    ],
)
def test_worker_commit_rechecks_current_lease_deadline_state(changes: dict[str, object]) -> None:
    with pytest.raises(ContractViolation):
        authorize(
            run_credential(),
            parse(Membership),
            permission="checkpoints:write",
            workspace_id="ws-1",
            run_id="run-1",
            now=100,
            lease=parse(RunLease, **changes),
        )


def test_run_path_cannot_be_substituted_and_credential_binding_is_strict() -> None:
    with pytest.raises(ContractViolation, match="not_found"):
        authorize(
            run_credential(),
            parse(Membership),
            permission="experiments:read",
            workspace_id="ws-1",
            run_id="run-2",
            now=100,
            lease=parse(RunLease),
        )
    for changes in ({"attempt_id": None}, {"scopes": ["runs:create"]}):
        with pytest.raises(ValidationError):
            run_credential(**changes)
    with pytest.raises(ValidationError):
        parse(VerifiedCredential, lease_epoch=0)


def test_idempotency_replay_is_stable_across_credential_refresh() -> None:
    stored = parse(StoredRequest)
    result = check_idempotency(
        parse(VerifiedCredential, credential_id="refreshed-credential"),
        parse(Membership),
        parse(IdempotencyScope),
        parse(CreateRunRequest),
        stored,
        now=100,
    )
    assert result == stored.operation
    assert (
        check_idempotency(
            parse(VerifiedCredential),
            parse(Membership),
            parse(IdempotencyScope),
            parse(CreateRunRequest),
            None,
            now=100,
        )
        is None
    )


@pytest.mark.parametrize("membership_active", [True, False])
def test_duplicate_conflict_and_revocation_order(membership_active: bool) -> None:
    with pytest.raises(ContractViolation) as raised:
        check_idempotency(
            parse(VerifiedCredential),
            parse(Membership, active=membership_active),
            parse(IdempotencyScope),
            parse(CreateRunRequest, experiment_budget=5),
            parse(StoredRequest),
            now=100,
        )
    assert raised.value.code == ("idempotency_conflict" if membership_active else "forbidden")


def test_full_scope_not_request_id_or_credential_identity_controls_deduplication() -> None:
    for field, value in (
        ("key", "another-key"),
        ("principal_id", "another-principal"),
        ("workspace_id", "ws-2"),
        ("resource_id", "ws-2"),
    ):
        with pytest.raises((ContractViolation, ValueError)):
            check_idempotency(
                parse(VerifiedCredential),
                parse(Membership),
                parse(IdempotencyScope, **{field: value}),
                parse(CreateRunRequest),
                parse(StoredRequest),
                now=100,
            )
    with pytest.raises(ContractViolation, match="invalid_request"):
        check_idempotency(
            parse(VerifiedCredential),
            parse(Membership),
            parse(IdempotencyScope),
            EmptyRequest(),
            None,
            now=100,
        )


def test_experiment_replay_can_return_original_result_when_budget_is_exhausted() -> None:
    op = experiments()[0]
    assert op.result is not None and op.result.kind == "experiment"
    request: Experiment = op.result.value.experiment
    op = changed(op, request_sha256=message_sha256(request))
    scope = IdempotencyScope(
        workspace_id="ws-1",
        principal_id="principal-1",
        kind="experiment",
        resource_id="run-1",
        key="experiment-1",
    )
    stored = StoredRequest(scope=scope, request_sha256=message_sha256(request), operation=op)
    exhausted = parse(RunView, experiments_accepted=6, budget_remaining=0)
    assert exhausted.budget_remaining == 0
    assert (
        check_idempotency(
            run_credential(),
            parse(Membership),
            scope,
            request,
            stored,
            now=100,
            lease=parse(RunLease),
        )
        == op
    )


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled", "expired"])
def test_terminal_run_immutable_and_cancel_complete_race_uses_revision(status: str) -> None:
    before = parse(RunView, status=status)
    after = changed(before, status="cancelled", revision=3)
    with pytest.raises(ContractViolation, match="incompatible_state"):
        validate_run_transition(
            before,
            after,
            expected_revision=2,
            active_workers=0,
            unsettled_reservations=0,
        )
    before = parse(RunView, status="evaluating")
    after = changed(before, status="completed", revision=3)
    validate_run_transition(
        before,
        after,
        expected_revision=2,
        active_workers=0,
        unsettled_reservations=0,
        committed_prefix=contiguous_record_prefix(experiments()[:2]),
    )
    with pytest.raises(ContractViolation):
        validate_run_transition(
            before,
            changed(before, status="cancelling", revision=3),
            expected_revision=1,
            active_workers=0,
            unsettled_reservations=0,
        )


@pytest.mark.parametrize("workers,reservations", [(1, 0), (0, 1), (1, 1)])
def test_cancel_ack_is_not_worker_termination_or_reservation_settlement(
    workers: int,
    reservations: int,
) -> None:
    before = parse(RunView, status="running")
    cancelling = changed(before, status="cancelling", revision=3)
    validate_run_transition(
        before,
        cancelling,
        expected_revision=2,
        active_workers=workers,
        unsettled_reservations=reservations,
    )
    with pytest.raises(ContractViolation):
        validate_run_transition(
            cancelling,
            changed(cancelling, status="cancelled", revision=4),
            expected_revision=3,
            active_workers=workers,
            unsettled_reservations=reservations,
        )


def test_state_change_cannot_refund_accepted_experiments_or_change_space() -> None:
    before = parse(RunView)
    after = changed(
        before, status="cancelling", revision=3, experiments_accepted=1, budget_remaining=5
    )
    with pytest.raises(ValueError, match="reservations"):
        validate_run_transition(
            before,
            after,
            expected_revision=2,
            active_workers=0,
            unsettled_reservations=0,
        )
    with pytest.raises(ValidationError, match="budget"):
        parse(RunView, budget_remaining=5)
    after = changed(before, status="cancelling", revision=3, workspace_id="ws-2")
    with pytest.raises(ValueError, match="immutable"):
        validate_run_transition(
            before,
            after,
            expected_revision=2,
            active_workers=0,
            unsettled_reservations=0,
        )


def test_failed_physics_is_completed_operation_and_keeps_charged_slot() -> None:
    op = experiments()[1]
    assert op.status == "completed" and op.accepted_experiment_index == 1
    assert op.result is not None and op.result.kind == "experiment"
    assert op.result.value.status == "failed" and op.result.value.error == "simulation_failed"
    assert contiguous_record_prefix(experiments()) == 1
    assert contiguous_record_prefix(tuple(reversed(experiments()))) == 1
    assert contiguous_record_prefix((experiments()[1],)) == -1


@pytest.mark.parametrize("index", [2, 3, 4])
def test_unobserved_slot_stops_prefix_even_when_later_slot_committed(index: int) -> None:
    blocker = changed(experiments()[index], accepted_experiment_index=0)
    assert contiguous_record_prefix((blocker, experiments()[1])) == -1


def test_duplicate_ordinals_ids_and_foreign_page_are_rejected() -> None:
    for operations in (
        (experiments()[0], experiments()[0]),
        (experiments()[0], changed(experiments()[2], operation_id="op-0")),
        (experiments()[0], changed(experiments()[2], workspace_id="ws-2")),
    ):
        with pytest.raises(ValueError):
            contiguous_record_prefix(operations)
        with pytest.raises(ValidationError):
            parse(ExperimentPage, items=[op.model_dump(mode="json") for op in operations])


def test_operation_kind_identity_and_status_are_coupled() -> None:
    op = experiments()[0]
    for changes in (
        {"kind": "model_submission", "accepted_experiment_index": None},
        {"accepted_experiment_index": 2},
        {"operation_id": "another-op"},
        {"status": "failed"},
        {"status": "pending"},
        {"error": FIXTURES["valid"]["Error"]},
    ):
        with pytest.raises(ValidationError):
            changed(op, **changes)
    run_op = parse(Operation)
    result = copy.deepcopy(run_op.model_dump(mode="json")["result"])
    result["value"]["workspace_id"] = "ws-2"
    with pytest.raises(ValidationError, match="tenant"):
        changed(run_op, result=result)


def test_cancellation_operation_completes_only_after_cancelled_run() -> None:
    op = parse(Operation)
    with pytest.raises(ValidationError, match="cancelled"):
        changed(
            op,
            kind="cancellation",
            result={"kind": "cancellation", "value": parse(RunView).model_dump(mode="json")},
        )
    cancelled = parse(RunView, status="cancelled")
    result = {"kind": "cancellation", "value": cancelled.model_dump(mode="json")}
    assert changed(op, kind="cancellation", result=result).status == "completed"


def test_operation_update_preserves_reservation_and_terminal_payload() -> None:
    pending = experiments()[2]
    running = changed(pending, status="running")
    cancelled = changed(running, status="cancelled")
    validate_operation_update(pending, running)
    validate_operation_update(running, cancelled)
    validate_operation_update(cancelled, cancelled)
    with pytest.raises(ContractViolation):
        validate_operation_update(cancelled, running)
    with pytest.raises(ValueError, match="immutable"):
        validate_operation_update(pending, changed(running, accepted_experiment_index=3))


def test_checkpoint_can_lag_prefix_and_initial_minus_one_is_valid() -> None:
    assert check_write() == "created"
    assert (
        check_write(
            checkpoint(through_index=-1),
            path_index=-1,
            latest_index=None,
            committed_prefix=-1,
        )
        == "created"
    )


def test_historical_checkpoint_retry_does_not_move_latest_and_changed_payload_conflicts() -> None:
    assert (
        check_write(
            latest_index=1,
            stored_request_sha256=FIXTURES["checkpoint_digest"],
        )
        == "replayed"
    )
    with pytest.raises(ContractViolation, match="idempotency_conflict"):
        check_write(latest_index=1, stored_request_sha256="0" * 64)
    with pytest.raises(ContractViolation, match="incompatible_state"):
        check_write(latest_index=1)


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"path_index": 1}, "invalid_request"),
        ({"committed_prefix": -1}, "incompatible_state"),
        ({"binding": {"runtime_image_sha256": "4" * 64}}, "incompatible_state"),
    ],
)
def test_checkpoint_path_prefix_binding_and_artifact_preconditions(
    changes: dict[str, Any],
    code: str,
) -> None:
    if "binding" in changes:
        changes = dict(changes, binding=parse(CheckpointBinding, **changes["binding"]))
    with pytest.raises(ContractViolation, match=code):
        check_write(**changes)


def test_checkpoint_size_and_full_request_identity_include_artifacts_and_runtime() -> None:
    with pytest.raises(ContractViolation, match="invalid_request"):
        check_write(checkpoint(state={"oversized": "x" * (256 * 1024)}))
    cp = checkpoint()
    assert checkpoint_request_sha256(cp, "3" * 64, ()) == FIXTURES["checkpoint_digest"]
    assert checkpoint_request_sha256(cp, "4" * 64, ()) != FIXTURES["checkpoint_digest"]
    assert (
        checkpoint_request_sha256(cp, "3" * 64, ({"opaque": "artifact-1"},))
        != (FIXTURES["checkpoint_digest"])
    )


def test_openapi_keeps_exact_route_set_and_marks_unfrozen_dependencies() -> None:
    api = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    operations = {
        operation["operationId"]: operation
        for path in api["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put"}
    }
    assert set(operations) == set(ROUTE_PERMISSIONS)
    for name, operation in operations.items():
        assert operation["x-required-scope"] == ROUTE_PERMISSIONS[name]
        assert operation["x-implementation-status"] == "not-implemented"
    assert operations["saveCheckpoint"]["x-pending-contracts"] == ["ART"]
    assert operations["submitModel"]["x-pending-contracts"] == ["ART", "EXEC"]
    assert operations["streamRunEvents"]["x-pending-contracts"] == ["WEB"]
    assert api["components"]["schemas"]["Operation"]["$ref"] == (
        "../control.schema.json#/$defs/Operation"
    )


def test_gap_blocks_new_admission_and_later_outcomes_stay_auditable() -> None:
    complete, physics_failure = experiments()[:2]
    gap = changed(complete, status="running", result=None)
    page = parse(
        ExperimentPage, items=[gap.model_dump(mode="json"), physics_failure.model_dump(mode="json")]
    )
    assert page.items[1].status == "completed"
    assert contiguous_record_prefix(page.items) == -1
    with pytest.raises(ContractViolation, match="incompatible_state"):
        validate_experiment_admission(parse(RunView), page.items)
    # Same reserved operation can recover; no new index or debit is created.
    validate_operation_update(gap, complete)
    validate_experiment_admission(parse(RunView), (complete, physics_failure))
    for terminal in ("cancelled", "failed"):
        failed = experiments()[4]
        aborted = changed(
            gap,
            status=terminal,
            error=(
                changed(failed.error, operation_id=gap.operation_id)
                if terminal == "failed" and failed.error is not None
                else None
            ),
        )
        with pytest.raises(ContractViolation, match="incompatible_state"):
            validate_experiment_admission(parse(RunView), (aborted, physics_failure))
        with pytest.raises(ContractViolation):
            validate_operation_update(aborted, complete)


def test_admission_rejects_exhaustion_and_incomplete_or_foreign_ledger() -> None:
    operations = experiments()[:2]
    space = parse(RunView).space.model_dump(mode="json")
    space["budget"] = 2
    exhausted = parse(RunView, space=space, budget_remaining=0)
    with pytest.raises(ContractViolation, match="budget_exhausted"):
        validate_experiment_admission(exhausted, operations)
    for ledger in (
        operations[:1],
        (operations[0], operations[0]),
        (operations[0], changed(operations[1], workspace_id="ws-2")),
    ):
        with pytest.raises(ValueError):
            validate_experiment_admission(parse(RunView), ledger)


def test_cancel_commit_race_preserves_winner_and_never_reopens_terminal_operation() -> None:
    completed = experiments()[0]
    running = changed(completed, status="running", result=None)
    cancelled = changed(running, status="cancelled")
    # Result commits first: cancelling the run cannot overwrite the actual record.
    validate_operation_update(running, completed)
    with pytest.raises(ContractViolation):
        validate_operation_update(completed, cancelled)
    # Cancellation settles first: a late worker result cannot reopen its slot.
    validate_operation_update(running, cancelled)
    with pytest.raises(ContractViolation):
        validate_operation_update(cancelled, completed)


@pytest.mark.parametrize("now", [True, 100.0, float("nan"), -1])
def test_server_time_projection_rejects_invalid_values(now: Any) -> None:
    with pytest.raises(ValueError):
        authorize(
            parse(VerifiedCredential),
            parse(Membership),
            permission="runs:read",
            workspace_id="ws-1",
            now=now,
        )


@pytest.mark.parametrize("field", ["path_index", "committed_prefix", "latest_index"])
def test_checkpoint_integer_metadata_does_not_coerce_booleans(field: str) -> None:
    with pytest.raises(ValidationError):
        check_write(None, **{field: False})


@pytest.mark.parametrize("index", [0, 1])
def test_completed_experiment_binds_the_actual_action_to_its_request_digest(index: int) -> None:
    op = experiments()[index]
    assert op.result is not None and op.result.kind == "experiment"
    assert message_sha256(op.result.value.experiment) == op.request_sha256
    with pytest.raises(ValidationError, match="request digest"):
        changed(op, request_sha256="0" * 64)
    result = op.result.model_dump(mode="json")
    result["value"]["experiment"]["particles"][0]["mass"] = 2.0
    with pytest.raises(ValidationError, match="request digest"):
        changed(op, result=result)


@pytest.mark.parametrize("key", FIXTURES["idempotency_keys"]["valid"])
def test_printable_idempotency_key_edges_are_accepted(key: str) -> None:
    assert parse(IdempotencyScope, key=key).key == key


@pytest.mark.parametrize("key", FIXTURES["idempotency_keys"]["invalid"])
def test_nonportable_idempotency_keys_are_rejected(key: str) -> None:
    with pytest.raises(ValidationError):
        parse(IdempotencyScope, key=key)


def test_all_post_header_key_schemas_equal_runtime_schema() -> None:
    schema = control_json_schema()["$defs"]["IdempotencyScope"]["properties"]["key"]
    api = json.loads((ROOT / "contracts/draft/openapi.json").read_text())
    headers = [
        parameter
        for path in api["paths"].values()
        if "post" in path
        for parameter in path["post"]["parameters"]
        if parameter.get("name") == "Idempotency-Key"
    ]
    assert len(headers) == 4
    assert all(header["required"] and header["schema"] == schema for header in headers)


def test_cancellation_acceptance_fences_result_and_checkpoint_before_settlement() -> None:
    credential, membership, lease = run_credential(), parse(Membership), parse(RunLease)
    completed = experiments()[0]
    running = changed(completed, status="running", result=None)
    authorize(
        credential,
        membership,
        permission="experiments:write",
        workspace_id="ws-1",
        run_id="run-1",
        now=100,
        lease=lease,
    )
    validate_operation_update(running, completed)
    # Acceptance closes writes before worker termination/resource reconciliation.
    cancelling_lease = changed(lease, status="cancelling")
    with pytest.raises(ContractViolation, match="incompatible_state"):
        authorize(
            credential,
            membership,
            permission="experiments:write",
            workspace_id="ws-1",
            run_id="run-1",
            now=100,
            lease=cancelling_lease,
        )
    with pytest.raises(ContractViolation, match="incompatible_state"):
        authorize(
            credential,
            membership,
            permission="checkpoints:write",
            workspace_id="ws-1",
            run_id="run-1",
            now=100,
            lease=cancelling_lease,
        )
    # A prior committed result survives; pending slots settle without fake output.
    with pytest.raises(ContractViolation):
        validate_operation_update(completed, changed(running, status="cancelled"))
    validate_operation_update(running, changed(running, status="cancelled"))


@pytest.mark.parametrize("target", ["evaluating", "completed"])
def test_settled_observation_gap_prevents_successful_progress(target: str) -> None:
    before = parse(RunView, status="running" if target == "evaluating" else "evaluating")
    after = changed(before, status=target, revision=3)
    gap = changed(experiments()[0], status="cancelled", result=None)
    ledger = (gap, experiments()[1])
    prefix = contiguous_record_prefix(ledger)
    assert prefix == -1
    with pytest.raises(ContractViolation, match="incompatible_state"):
        validate_run_transition(
            before,
            after,
            expected_revision=2,
            active_workers=0,
            unsettled_reservations=0,
            committed_prefix=prefix,
        )
    with pytest.raises(ValueError, match="authoritative committed prefix"):
        validate_run_transition(
            before, after, expected_revision=2, active_workers=0, unsettled_reservations=0
        )
    validate_run_transition(
        before,
        changed(before, status="failed", revision=3),
        expected_revision=2,
        active_workers=0,
        unsettled_reservations=0,
    )


def test_core_validation_is_required_in_addition_to_operation_shape_and_hash() -> None:
    op = experiments()[0]
    assert op.result is not None and op.result.kind == "experiment"
    run = parse(RunView)

    def bundle(record: dict[str, Any]) -> ObservationBundle:
        return ObservationBundle.model_validate_json(
            json.dumps(
                {
                    "run_id": run.run_id,
                    "engine_version": "synthetic",
                    "engine_fingerprint": "1" * 64,
                    "space": run.space.model_dump(mode="json"),
                    "records": [record],
                }
            )
        )

    bundle(op.result.value.model_dump(mode="json"))
    for mutation in ("mass", "identity", "count", "time"):
        payload = op.model_dump(mode="json")
        record = payload["result"]["value"]
        if mutation == "mass":
            record["experiment"]["particles"][0]["mass"] = 3.0
        elif mutation == "identity":
            record["experiment"]["particles"][0]["id"] = "other-particle"
        elif mutation == "count":
            record["trajectory"]["frames"].pop()
        else:
            record["trajectory"]["frames"][1]["time"] = 0.04
        payload["request_sha256"] = message_sha256(
            Experiment.model_validate_json(json.dumps(record["experiment"]))
        )
        # The envelope cannot know pinned space. The existing CORE validator can.
        Operation.model_validate_json(json.dumps(payload))
        with pytest.raises(ValidationError):
            bundle(record)
