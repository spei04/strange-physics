"""Pure conformance checks for the identity/run control contract.

Trusted verified credentials and transaction snapshots are inputs, not produced here.
This module is not an authentication service, database, or worker scheduler.
"""

from __future__ import annotations

import hashlib
from typing import Annotated, Literal, Self

from pydantic import Field, JsonValue, TypeAdapter, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import (
    Checkpoint,
    Experiment,
    ExperimentRecord,
    ExperimentSpace,
    Identifier,
    Message,
)
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.serialization import canonical_json

RunStatus = Literal[
    "queued",
    "preparing",
    "running",
    "recovering",
    "evaluating",
    "cancelling",
    "completed",
    "failed",
    "cancelled",
    "expired",
]
OperationKind = Literal["run_creation", "experiment", "cancellation", "model_submission"]
OperationStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
Permission = Literal[
    "runs:read",
    "runs:create",
    "runs:cancel",
    "experiments:read",
    "experiments:write",
    "checkpoints:write",
    "models:write",
]
Role = Literal["owner", "researcher", "viewer"]
PrefixIndex = Annotated[int, Field(ge=-1, le=9_999)]
TERMINAL_RUNS = frozenset({"completed", "failed", "cancelled", "expired"})
TERMINAL_OPERATIONS = frozenset({"completed", "failed", "cancelled"})
RUN_EDGES: dict[str, frozenset[str]] = {
    "queued": frozenset({"preparing", "cancelled", "expired"}),
    "preparing": frozenset({"running", "cancelling", "failed", "expired"}),
    "running": frozenset({"recovering", "evaluating", "cancelling", "failed", "expired"}),
    "recovering": frozenset({"running", "cancelling", "failed", "expired"}),
    "evaluating": frozenset({"completed", "cancelling", "failed", "expired"}),
    "cancelling": frozenset({"cancelled"}),
}
READ_PERMISSIONS = frozenset({"runs:read", "experiments:read"})
RUN_PERMISSIONS = frozenset(
    {
        "experiments:read",
        "experiments:write",
        "checkpoints:write",
        "models:write",
    }
)
ROUTE_PERMISSIONS: dict[str, Permission] = {
    "saveCheckpoint": "checkpoints:write",
    "listExperiments": "experiments:read",
    "runExperiment": "experiments:write",
    "submitModel": "models:write",
    "getRunOperation": "experiments:read",
    "getExperimentSpace": "experiments:read",
    "createRun": "runs:create",
    "getRun": "runs:read",
    "cancelRun": "runs:cancel",
    "streamRunEvents": "runs:read",
    "getWorkspaceOperation": "runs:read",
}


class ContractViolation(ValueError):
    """Safe machine-readable decision; adapters supply a request correlation ID."""

    def __init__(self, code: str, status: int) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


class VerifiedCredential(Message):
    """Internal verified identity projection, never a client-authored request body."""

    issuer: Annotated[str, Field(min_length=1, max_length=512)]
    subject: Annotated[str, Field(min_length=1, max_length=256)]
    principal_id: Identifier
    credential_id: Identifier
    kind: Literal["user", "service", "run"]
    workspace_id: Identifier
    scopes: tuple[Permission, ...]
    expires_at: Count
    revoked: bool
    run_id: Identifier | None = None
    attempt_id: Identifier | None = None
    lease_epoch: Count | None = None

    @model_validator(mode="after")
    def validate_binding(self) -> Self:
        bound = (self.run_id, self.attempt_id, self.lease_epoch)
        if self.kind == "run":
            if any(value is None for value in bound):
                raise ValueError("run credential requires run, attempt and lease epoch")
            if not set(self.scopes) <= RUN_PERMISSIONS:
                raise ValueError("run credential cannot carry workspace permissions")
        elif any(value is not None for value in bound):
            raise ValueError("workspace credential cannot carry run lease binding")
        if len(self.scopes) != len(set(self.scopes)):
            raise ValueError("credential scopes must be unique")
        return self


class Membership(Message):
    """Current application grant, loaded independently of credential claims."""

    workspace_id: Identifier
    principal_id: Identifier
    role: Role
    active: bool
    revision: Count


class RunLease(Message):
    workspace_id: Identifier
    run_id: Identifier
    attempt_id: Identifier
    epoch: Count
    expires_at: Count
    run_deadline: Count
    revoked: bool
    status: RunStatus


def authorize(
    credential: VerifiedCredential,
    membership: Membership,
    *,
    permission: Permission,
    workspace_id: str,
    now: int,
    run_id: str | None = None,
    lease: RunLease | None = None,
) -> None:
    """Incomplete primitive: hosted callers must use workspace authorize_product."""
    if not isinstance(now, int) or isinstance(now, bool) or now < 0:
        raise ValueError("server time must be a nonnegative integer")
    if credential.revoked or now >= credential.expires_at:
        raise ContractViolation("unauthenticated", 401)
    if (
        credential.workspace_id != workspace_id
        or membership.workspace_id != workspace_id
        or membership.principal_id != credential.principal_id
    ):
        raise ContractViolation("not_found", 404)
    if not membership.active:
        raise ContractViolation("forbidden", 403)
    if permission not in credential.scopes:
        raise ContractViolation("forbidden", 403)
    if membership.role == "viewer" and permission not in READ_PERMISSIONS:
        raise ContractViolation("forbidden", 403)
    if credential.kind == "run":
        if lease is None:
            raise ContractViolation("not_found", 404)
        if (
            lease.workspace_id != workspace_id
            or lease.run_id != credential.run_id
            or run_id != credential.run_id
        ):
            raise ContractViolation("not_found", 404)
        if (
            lease.revoked
            or lease.attempt_id != credential.attempt_id
            or lease.epoch != credential.lease_epoch
            or now >= min(lease.expires_at, lease.run_deadline)
        ):
            raise ContractViolation("forbidden", 403)
        if lease.status != "running":
            raise ContractViolation("incompatible_state", 409)
    elif permission in RUN_PERMISSIONS:
        raise ContractViolation("forbidden", 403)


class ResourceLimits(Message):
    max_cpu_seconds: Annotated[int, Field(ge=1, le=2**53 - 1)]
    max_wall_seconds: Annotated[int, Field(ge=1, le=2**53 - 1)]
    max_model_calls: Count
    max_input_tokens: Count
    max_output_tokens: Count
    max_artifact_bytes: Count
    max_provider_cost_microusd: Count


class CreateRunRequest(Message):
    world_version_id: Identifier
    agent_package_sha256: Digest
    track: Literal["controlled_selection", "agent_discovery"]
    experiment_budget: Annotated[int, Field(ge=1, le=10_000)]
    limits: ResourceLimits


class RunView(Message):
    workspace_id: Identifier
    run_id: Identifier
    status: RunStatus
    revision: Count
    space: ExperimentSpace
    experiments_accepted: Annotated[int, Field(ge=0, le=10_000)]
    budget_remaining: Annotated[int, Field(ge=0, le=10_000)]

    @model_validator(mode="after")
    def validate_budget(self) -> Self:
        if self.experiments_accepted + self.budget_remaining != self.space.budget:
            raise ValueError("accepted reservations plus remaining must equal the budget")
        return self


def validate_run_transition(
    before: RunView,
    after: RunView,
    *,
    expected_revision: int,
    active_workers: int,
    unsettled_reservations: int,
    committed_prefix: int | None = None,
) -> None:
    """CAS/state check; counts must come from the same authoritative transaction."""
    TypeAdapter(Count).validate_python(expected_revision, strict=True)
    TypeAdapter(Count).validate_python(active_workers, strict=True)
    TypeAdapter(Count).validate_python(unsettled_reservations, strict=True)
    if expected_revision != before.revision or after.revision != before.revision + 1:
        raise ContractViolation("incompatible_state", 409)
    if (before.workspace_id, before.run_id, before.space) != (
        after.workspace_id,
        after.run_id,
        after.space,
    ):
        raise ValueError("run identity and experiment space are immutable")
    if after.experiments_accepted != before.experiments_accepted:
        raise ValueError("state transitions cannot change experiment reservations")
    if after.status not in RUN_EDGES.get(before.status, frozenset()):
        raise ContractViolation("incompatible_state", 409)
    if after.status in {"evaluating", "completed"}:
        if committed_prefix is None:
            raise ValueError("successful progress requires an authoritative committed prefix")
        TypeAdapter(PrefixIndex).validate_python(committed_prefix, strict=True)
        if committed_prefix != before.experiments_accepted - 1:
            raise ContractViolation("incompatible_state", 409)
    if after.status in TERMINAL_RUNS and (active_workers or unsettled_reservations):
        raise ContractViolation("incompatible_state", 409)


class ModelReceipt(Message):
    model_id: Identifier
    model_sha256: Digest
    through_index: PrefixIndex


class RunCreationResult(Message):
    kind: Literal["run_creation"]
    value: RunView


class ExperimentResult(Message):
    kind: Literal["experiment"]
    value: ExperimentRecord


class CancellationResult(Message):
    kind: Literal["cancellation"]
    value: RunView


class ModelSubmissionResult(Message):
    kind: Literal["model_submission"]
    value: ModelReceipt


OperationResult = Annotated[
    RunCreationResult | ExperimentResult | CancellationResult | ModelSubmissionResult,
    Field(discriminator="kind"),
]


class Error(Message):
    code: Literal[
        "unauthenticated",
        "forbidden",
        "not_found",
        "idempotency_conflict",
        "incompatible_state",
        "invalid_request",
        "budget_exhausted",
        "quota_exceeded",
        "temporarily_unavailable",
        "cursor_expired",
        "unsupported_version",
        "execution_failed",
    ]
    message: Annotated[str, Field(min_length=1, max_length=512)]
    request_id: Identifier
    retryable: bool
    operation_id: Identifier | None


class Operation(Message):
    workspace_id: Identifier
    run_id: Identifier
    operation_id: Identifier
    kind: OperationKind
    request_sha256: Digest
    status: OperationStatus
    accepted_experiment_index: Annotated[int, Field(ge=0, le=9_999)] | None
    result: OperationResult | None
    error: Error | None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if (self.kind == "experiment") != (self.accepted_experiment_index is not None):
            raise ValueError("only accepted experiments carry a reserved ordinal")
        if self.status == "completed":
            if self.result is None or self.error is not None:
                raise ValueError("completed operation requires a result and no error")
            if self.result.kind != self.kind:
                raise ValueError("operation result kind must match its operation")
            value = self.result.value
            if isinstance(value, RunView):
                if (value.workspace_id, value.run_id) != (self.workspace_id, self.run_id):
                    raise ValueError("run result must belong to the operation tenant and run")
                if self.kind == "cancellation" and value.status != "cancelled":
                    raise ValueError("cancellation completes only after the run is cancelled")
            elif isinstance(value, ExperimentRecord):
                if message_sha256(value.experiment) != self.request_sha256:
                    raise ValueError("experiment result must match the normalized request digest")
                if (value.operation_id, value.index) != (
                    self.operation_id,
                    self.accepted_experiment_index,
                ):
                    raise ValueError("experiment result must match its operation and ordinal")
        elif self.status == "failed":
            if self.error is None or self.result is not None:
                raise ValueError("failed operation requires an error and no result")
            if self.error.operation_id != self.operation_id:
                raise ValueError("operation failure must refer to this operation")
        elif self.result is not None or self.error is not None:
            raise ValueError("pending, running and cancelled operations have no result or error")
        return self


def validate_operation_update(before: Operation, after: Operation) -> None:
    """Validate payload transition after current commit authority and CORE result checks."""
    immutable = (
        "workspace_id",
        "run_id",
        "operation_id",
        "kind",
        "request_sha256",
        "accepted_experiment_index",
    )
    if any(getattr(before, field) != getattr(after, field) for field in immutable):
        raise ValueError("operation identity, request and reservation are immutable")
    if before.status in TERMINAL_OPERATIONS:
        if before != after:
            raise ContractViolation("incompatible_state", 409)
        return
    allowed = {
        "pending": {"running", "completed", "failed", "cancelled"},
        "running": {"completed", "failed", "cancelled"},
    }
    if after.status not in allowed[before.status]:
        raise ContractViolation("incompatible_state", 409)


class ExperimentPage(Message):
    """All accepted slots, including pending or aborted execution, in ordinal order."""

    workspace_id: Identifier
    run_id: Identifier
    items: Annotated[tuple[Operation, ...], Field(max_length=100)]
    next_cursor: Annotated[str, Field(min_length=1, max_length=512)] | None

    @model_validator(mode="after")
    def validate_items(self) -> Self:
        previous = -1
        seen: set[str] = set()
        for operation in self.items:
            if (operation.workspace_id, operation.run_id) != (self.workspace_id, self.run_id):
                raise ValueError("experiment page contains a foreign operation")
            index = operation.accepted_experiment_index
            if operation.kind != "experiment" or index is None or index <= previous:
                raise ValueError("experiment page must contain increasing accepted ordinals")
            if operation.operation_id in seen:
                raise ValueError("experiment page operation IDs must be unique")
            previous = index
            seen.add(operation.operation_id)
        return self


class IdempotencyScope(Message):
    workspace_id: Identifier
    principal_id: Identifier
    kind: OperationKind
    resource_id: Identifier
    key: Annotated[
        str,
        Field(
            min_length=1,
            max_length=128,
            pattern=r"^[!-~]+$",
            json_schema_extra={"not": {"pattern": "[^!-~]"}},
        ),
    ]


class EmptyRequest(Message):
    """Normalized no-body cancellation request."""


class StoredRequest(Message):
    scope: IdempotencyScope
    request_sha256: Digest
    operation: Operation

    @model_validator(mode="after")
    def validate_binding(self) -> Self:
        if (self.scope.workspace_id, self.scope.kind, self.request_sha256) != (
            self.operation.workspace_id,
            self.operation.kind,
            self.operation.request_sha256,
        ):
            raise ValueError("stored request and operation identity differ")
        expected_resource = (
            self.operation.workspace_id
            if self.scope.kind == "run_creation"
            else self.operation.run_id
        )
        if self.scope.resource_id != expected_resource:
            raise ValueError("idempotency resource must match its operation")
        return self


def check_idempotency(
    credential: VerifiedCredential,
    membership: Membership,
    scope: IdempotencyScope,
    request: Message,
    stored: StoredRequest | None,
    *,
    now: int,
    lease: RunLease | None = None,
) -> Operation | None:
    """Incomplete primitive: hosted callers must use check_product_idempotency."""
    permissions: dict[str, Permission] = {
        "run_creation": "runs:create",
        "experiment": "experiments:write",
        "cancellation": "runs:cancel",
        "model_submission": "models:write",
    }
    authorize(
        credential,
        membership,
        permission=permissions[scope.kind],
        workspace_id=scope.workspace_id,
        now=now,
        run_id=scope.resource_id if credential.kind == "run" else None,
        lease=lease,
    )
    if scope.principal_id != credential.principal_id:
        raise ContractViolation("not_found", 404)
    if credential.kind == "run" and scope.resource_id != credential.run_id:
        raise ContractViolation("not_found", 404)
    if scope.kind == "run_creation" and scope.resource_id != scope.workspace_id:
        raise ContractViolation("not_found", 404)
    expected_type = {
        "run_creation": CreateRunRequest,
        "experiment": Experiment,
        "cancellation": EmptyRequest,
    }.get(scope.kind)
    if expected_type is not None and not isinstance(request, expected_type):
        raise ContractViolation("invalid_request", 422)
    if stored is None:
        return None
    if stored.scope != scope:
        raise ValueError("stored request lookup must use the entire idempotency scope")
    if stored.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    return stored.operation


class CheckpointBinding(Message):
    agent_id: Identifier
    agent_package_sha256: Digest
    agent_config_sha256: Digest
    runtime_image_sha256: Digest
    checkpoint_protocol: Literal["strange-physics.checkpoint.v1"] = "strange-physics.checkpoint.v1"


def checkpoint_request_sha256(
    checkpoint: Checkpoint,
    runtime_image_sha256: Digest,
    artifacts: tuple[JsonValue, ...],
) -> str:
    """Hash the complete draft HTTP payload after its external ART validation."""
    TypeAdapter(Digest).validate_python(runtime_image_sha256, strict=True)
    payload = {
        "checkpoint": checkpoint.model_dump(mode="json"),
        "runtime_image_sha256": runtime_image_sha256,
        "artifacts": artifacts,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def contiguous_record_prefix(operations: tuple[Operation, ...]) -> int:
    """Find the observable prefix, not the largest reservation or successful index."""
    if not operations:
        return -1
    identity = (operations[0].workspace_id, operations[0].run_id)
    indices: dict[int, Operation] = {}
    operation_ids: set[str] = set()
    for operation in operations:
        index = operation.accepted_experiment_index
        if operation.kind != "experiment" or index is None:
            raise ValueError("prefix input must contain accepted experiment operations")
        if (operation.workspace_id, operation.run_id) != identity:
            raise ValueError("prefix input cannot span runs or workspaces")
        if index in indices or operation.operation_id in operation_ids:
            raise ValueError("duplicate experiment ordinal or operation ID")
        operation_ids.add(operation.operation_id)
        indices[index] = operation
    prefix = -1
    while prefix + 1 in indices:
        operation = indices[prefix + 1]
        if operation.status != "completed":
            break
        prefix += 1
    return prefix


def validate_experiment_admission(run: RunView, operations: tuple[Operation, ...]) -> None:
    """Fresh admission check after authorized deduplication, under the run SQL lock.

    This requires the complete accepted ledger, not one page. Recovery retries the
    same pending/running operation; no fresh ordinal can bypass an unobserved slot.
    """
    if run.status != "running":
        raise ContractViolation("incompatible_state", 409)
    if len(operations) != run.experiments_accepted:
        raise ValueError("admission requires the complete accepted ledger")
    indices = sorted(
        operation.accepted_experiment_index
        for operation in operations
        if operation.accepted_experiment_index is not None
    )
    if indices != list(range(run.experiments_accepted)):
        raise ValueError("accepted ledger must have exactly the reserved ordinals")
    if any(
        (operation.workspace_id, operation.run_id) != (run.workspace_id, run.run_id)
        for operation in operations
    ):
        raise ValueError("accepted ledger must belong to the run and workspace")
    prefix = contiguous_record_prefix(operations)
    if prefix != run.experiments_accepted - 1:
        raise ContractViolation("incompatible_state", 409)
    if run.budget_remaining == 0:
        raise ContractViolation("budget_exhausted", 429)


def validate_checkpoint_write(
    checkpoint: Checkpoint,
    *,
    path_index: int,
    binding: CheckpointBinding,
    expected_binding: CheckpointBinding,
    full_request_sha256: str,
    stored_request_sha256: str | None,
    latest_index: int | None,
    committed_prefix: int,
    artifacts_verified: bool,
) -> Literal["created", "replayed"]:
    """Run after authorization and external ART validation, under the same SQL lock.

    Stored digest is looked up by (workspace, run, path index), never by index alone.
    Binding comes from the authorized attempt; full digest is computed, not trusted.
    """
    TypeAdapter(Digest).validate_python(full_request_sha256, strict=True)
    if stored_request_sha256 is not None:
        TypeAdapter(Digest).validate_python(stored_request_sha256, strict=True)
    TypeAdapter(PrefixIndex).validate_python(committed_prefix, strict=True)
    if latest_index is not None:
        TypeAdapter(PrefixIndex).validate_python(latest_index, strict=True)
        if latest_index > committed_prefix:
            raise ValueError("stored checkpoint cannot exceed the committed prefix")
    if stored_request_sha256 is not None and (
        latest_index is None or checkpoint.through_index > latest_index
    ):
        raise ValueError("stored checkpoint must be included in latest checkpoint index")
    TypeAdapter(PrefixIndex).validate_python(path_index, strict=True)
    if path_index != checkpoint.through_index:
        raise ContractViolation("invalid_request", 422)
    if len(canonical_json(checkpoint.model_dump(mode="json")).encode("utf-8")) > 256 * 1024:
        raise ContractViolation("invalid_request", 422)
    if binding != expected_binding or checkpoint.agent_id != binding.agent_id:
        raise ContractViolation("incompatible_state", 409)
    if not artifacts_verified:
        raise ContractViolation("invalid_request", 422)
    if checkpoint.through_index > committed_prefix:
        raise ContractViolation("incompatible_state", 409)
    if stored_request_sha256 is not None:
        if stored_request_sha256 != full_request_sha256:
            raise ContractViolation("idempotency_conflict", 409)
        return "replayed"
    if latest_index is not None and checkpoint.through_index <= latest_index:
        raise ContractViolation("incompatible_state", 409)
    return "created"


CONTROL_MODELS: tuple[type[Message], ...] = (
    VerifiedCredential,
    Membership,
    RunLease,
    ResourceLimits,
    CreateRunRequest,
    RunView,
    ModelReceipt,
    Error,
    Operation,
    ExperimentPage,
    IdempotencyScope,
    StoredRequest,
    CheckpointBinding,
    EmptyRequest,
)


def control_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in CONTROL_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/control.schema.json"
    schema["x-contract-status"] = "control-v1"
    schema["description"] = (
        "Identity/run conformance subset. Named definitions require the documented "
        "semantic and cross-message checks. No hosted implementation or ART/WEB freeze."
    )
    return schema
