"""Worker envelopes and atomic proposal shapes; no controller, broker or process launcher."""

from __future__ import annotations

import hashlib
from typing import Annotated, Literal, Self

from pydantic import Field, JsonValue, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.artifact_contracts import Number
from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import (
    CheckpointBinding,
    CreateRunRequest,
    RunCreationResult,
    RunView,
    StoredRequest,
)
from strange_physics.package_contracts import (
    PACKAGE_MODELS,
    ExecutionResources,
    Positive,
    SubmittedRuntimeApproval,
)
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.run_credential_contracts import RunOwnership, WorkerPermission
from strange_physics.serialization import canonical_json
from strange_physics.session_contracts import HttpsURI

WorkerPurpose = Literal["workers:launch", "workers:terminate"]
BrokerOperation = Literal[
    "list_experiments", "execute_experiment", "save_checkpoint", "submit_model"
]
BROKER_PERMISSIONS: dict[BrokerOperation, WorkerPermission] = {
    "list_experiments": "experiments:read",
    "execute_experiment": "experiments:write",
    "save_checkpoint": "checkpoints:write",
    "submit_model": "models:write",
}
LaunchState = Literal["prepared", "dispatch_unknown", "active", "fenced", "stopping", "stopped"]
_ALLOWED_STATES: dict[str, frozenset[str]] = {
    "prepared": frozenset({"dispatch_unknown", "fenced"}),
    "dispatch_unknown": frozenset({"active", "fenced"}),
    "active": frozenset({"fenced"}),
    "fenced": frozenset({"stopping", "stopped"}),
    "stopping": frozenset({"stopped"}),
    "stopped": frozenset(),
}


def configuration_sha256(value: dict[str, JsonValue]) -> str:
    """Bound structure before canonical serialization; adapters also cap predecode bytes."""
    pending: list[tuple[JsonValue, int]] = [(value, 1)]
    nodes = 0
    text_characters = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > 10_000 or depth > 32:
            raise ValueError("Agent configuration exceeds structural bounds")
        if isinstance(item, dict):
            if nodes + len(pending) + 2 * len(item) > 10_000:
                raise ValueError("Agent configuration exceeds structural bounds")
            nodes += len(item)
            text_characters += sum(len(key) for key in item)
            if text_characters > 262_144:
                raise ValueError("Agent configuration exceeds aggregate byte budget")
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            if nodes + len(pending) + len(item) > 10_000:
                raise ValueError("Agent configuration exceeds structural bounds")
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            text_characters += len(item)
            if text_characters > 262_144:
                raise ValueError("Agent configuration exceeds aggregate byte budget")
    content = canonical_json(value).encode("utf-8")
    if len(content) > 262_144:
        raise ValueError("Agent configuration exceeds protocol byte budget")
    return hashlib.sha256(content).hexdigest()


class OriginalExecutionAdmission(Message):
    """Original atomic producer record, never assembled from a launch caller's current values."""

    admission_id: Identifier
    request: CreateRunRequest
    stored_request: StoredRequest
    admitted_run: RunView
    ownership: RunOwnership
    agent_configuration: dict[str, JsonValue]
    checkpoint_binding: CheckpointBinding

    @model_validator(mode="after")
    def original(self) -> Self:
        original, owner, stored = self.admitted_run, self.ownership, self.stored_request
        operation = stored.operation
        digest = message_sha256(self.request)
        if (
            operation.kind != "run_creation"
            or operation.status != "completed"
            or not isinstance(operation.result, RunCreationResult)
        ):
            raise ValueError("Original admission requires the committed creation receipt")
        result = operation.result.value
        if (
            stored.request_sha256 != digest
            or operation.request_sha256 != digest
            or stored.scope.principal_id != owner.principal_id
            or (original.workspace_id, original.run_id) != (owner.workspace_id, owner.run_id)
            or (operation.workspace_id, operation.run_id) != (owner.workspace_id, owner.run_id)
            or (result.workspace_id, result.run_id) != (owner.workspace_id, owner.run_id)
            or result.space != original.space
            or original.space.budget != self.request.experiment_budget
            or original.status != "queued"
            or original.revision != 0
            or original.experiments_accepted != 0
            or owner.run_deadline - owner.created_at > self.request.limits.max_wall_seconds
            or self.checkpoint_binding.agent_package_sha256 != self.request.agent_package_sha256
            or self.checkpoint_binding.agent_config_sha256
            != configuration_sha256(self.agent_configuration)
        ):
            raise ValueError("Execution admission must bind original body, run, owner and config")
        return self


class WorkerPolicy(Message):
    policy_id: Identifier
    max_metadata_bytes: Positive
    max_configuration_bytes: Annotated[int, Field(strict=True, ge=1, le=262_144)]
    worker_limits: ExecutionResources
    sandbox_profile: Identifier
    network_policy: Identifier
    build_policy_sha256: Digest
    scan_policy_sha256: Digest
    approval_policy_sha256: Digest


class IsolationEvidence(Message):
    """Current trusted policy/capability observation; constructing it proves no isolation."""

    verification_id: Identifier
    verifier_id: Identifier
    worker_policy_sha256: Digest
    sandbox_profile: Identifier
    network_policy: Identifier
    state: Literal["available", "unavailable", "unknown"]
    observed_at: Number
    valid_until: Number

    @model_validator(mode="after")
    def lifetime(self) -> Self:
        if self.valid_until <= self.observed_at:
            raise ValueError("Isolation observation needs positive validity")
        return self


class WorkerControlPolicy(Message):
    """Internal control identity policy, independent of worker admission/isolation policy."""

    policy_id: Identifier
    issuer: HttpsURI
    audience: Annotated[str, Field(min_length=1, max_length=512)]
    max_authorization_seconds: Positive


class WorkerInternalPrincipal(Message):
    principal_id: Identifier
    generation: Number
    active: bool
    purposes: Annotated[tuple[WorkerPurpose, ...], Field(min_length=1, max_length=2)]

    @model_validator(mode="after")
    def canonical(self) -> Self:
        if tuple(sorted(set(self.purposes))) != self.purposes:
            raise ValueError("Internal control purposes must be unique and sorted")
        return self


class WorkerControlClaims(Message):
    """Verified internal claims, never a public/service/run credential scope."""

    authorization_id: Identifier
    policy_id: Identifier
    issuer: HttpsURI
    audience: Annotated[str, Field(min_length=1, max_length=512)]
    principal_id: Identifier
    principal_generation: Number
    purpose: WorkerPurpose
    workspace_id: Identifier
    run_id: Identifier
    launch_id: Identifier | None
    issued_at: Number
    expires_at: Number
    revoked: bool

    @model_validator(mode="after")
    def scope(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("Control authorization needs positive lifetime")
        if (self.purpose == "workers:terminate") != (self.launch_id is not None):
            raise ValueError(
                "Termination authority must name its exact launch; launch is run-scoped"
            )
        return self


class WorkerControlAuthority(Message):
    claims: WorkerControlClaims
    principal: WorkerInternalPrincipal

    @model_validator(mode="after")
    def same_principal(self) -> Self:
        if self.claims.principal_id != self.principal.principal_id:
            raise ValueError("Internal claims must name the current principal")
        return self


class CheckpointRestoreRef(Message):
    index: Annotated[int, Field(strict=True, ge=-1, le=9_999)]
    request_sha256: Digest
    record_sha256: Digest


class WorkerLaunchRequest(Message):
    workspace_id: Identifier
    run_id: Identifier
    attempt_id: Identifier
    lease_epoch: Number
    admission_sha256: Digest
    approval_sha256: Digest
    worker_policy_sha256: Digest
    resources: ExecutionResources
    restore: CheckpointRestoreRef | None


class WorkerLaunchRecord(Message):
    """Immutable launch intent and retained provenance; logical running is not a process."""

    launch_id: Identifier
    request: WorkerLaunchRequest
    request_sha256: Digest
    admission: OriginalExecutionAdmission
    approval: SubmittedRuntimeApproval
    original_credential_id: Identifier
    original_credential_generation: Positive
    run_revision: Number
    credential_revision: Number
    created_at: Number
    deadline: Number

    @model_validator(mode="after")
    def binding(self) -> Self:
        request, admission = self.request, self.admission
        owner, limits = admission.ownership, admission.request.limits
        source = self.approval.build.inspection.source
        build = self.approval.build.build
        if (
            self.request_sha256 != message_sha256(request)
            or request.admission_sha256 != message_sha256(admission)
            or request.approval_sha256 != message_sha256(self.approval)
            or (request.workspace_id, request.run_id) != (owner.workspace_id, owner.run_id)
            or source.archive.record.workspace_id != owner.workspace_id
            or message_sha256(source.manifest) != admission.request.agent_package_sha256
            or build.runtime_image_sha256 != admission.checkpoint_binding.runtime_image_sha256
            or self.approval.approval.state != "approved"
            or self.created_at < self.approval.approval.decided_at
            or self.created_at >= self.approval.scan.valid_until
            or self.created_at < owner.created_at
            or not self.created_at < self.deadline <= owner.run_deadline
            or self.deadline - self.created_at > request.resources.wall_seconds
            or request.resources.wall_seconds > limits.max_wall_seconds
            or request.resources.cpu_seconds > limits.max_cpu_seconds
            or request.resources.output_bytes > limits.max_artifact_bytes
        ):
            raise ValueError(
                "Launch must bind original admission, submitted approval and resource ceiling"
            )
        return self


class RuntimeInstance(Message):
    """Provider identity is private and trusted; no client URL or command."""

    provider_namespace: Identifier
    instance_id: Identifier
    launch_id: Identifier
    launch_record_sha256: Digest
    confirmed_at: Number


class WorkerLaunchLifecycle(Message):
    launch_id: Identifier
    launch_record_sha256: Digest
    revision: Number
    state: LaunchState
    instance: RuntimeInstance | None
    first_fenced_at: Number | None
    stopped_at: Number | None
    stop_outcome: Literal["terminated", "never_started"] | None

    @model_validator(mode="after")
    def state_shape(self) -> Self:
        if self.instance is not None and (
            self.instance.launch_id != self.launch_id
            or self.instance.launch_record_sha256 != self.launch_record_sha256
        ):
            raise ValueError("Runtime instance must belong to the exact immutable launch")
        stopped = self.state == "stopped"
        fenced = self.state in {"fenced", "stopping", "stopped"}
        if (
            fenced != (self.first_fenced_at is not None)
            or stopped != (self.stopped_at is not None)
            or stopped != (self.stop_outcome is not None)
            or (self.state == "active" and self.instance is None)
            or (self.state in {"prepared", "dispatch_unknown"} and self.instance is not None)
            or (self.stop_outcome == "terminated" and self.instance is None)
            or (self.stop_outcome == "never_started" and self.instance is not None)
            or (
                self.stopped_at is not None
                and self.first_fenced_at is not None
                and self.stopped_at < self.first_fenced_at
            )
        ):
            raise ValueError(
                "Launch work and termination states must have consistent fenced evidence"
            )
        return self


class WorkerLifecycleTransition(Message):
    """Pure transition shape, not authorization or a successful process mutation."""

    before: WorkerLaunchLifecycle
    after: WorkerLaunchLifecycle

    @model_validator(mode="after")
    def monotonic(self) -> Self:
        old, new = self.before, self.after
        if old == new:
            return self
        if (
            (old.launch_id, old.launch_record_sha256) != (new.launch_id, new.launch_record_sha256)
            or new.revision != old.revision + 1
            or new.state not in _ALLOWED_STATES[old.state]
            or (old.first_fenced_at is not None and new.first_fenced_at != old.first_fenced_at)
            or (old.instance is not None and new.instance != old.instance)
        ):
            raise ValueError("Launch transition cannot resurrect or change an immutable instance")
        return self


class WorkerCommandOutbox(Message):
    command_id: Identifier
    kind: Literal["launch", "terminate"]
    workspace_id: Identifier
    run_id: Identifier
    launch_id: Identifier
    launch_record_sha256: Digest
    request_sha256: Digest


class WorkerLaunchLookup(Message):
    """Keyed authoritative lookup; partial projections remain representable for recovery.

    A matching key does not prove absence. Atomic unique attempt admission is required.
    """

    workspace_id: Identifier
    run_id: Identifier
    attempt_id: Identifier
    lease_epoch: Number
    record: WorkerLaunchRecord | None
    lifecycle: WorkerLaunchLifecycle | None
    outbox: WorkerCommandOutbox | None

    @model_validator(mode="after")
    def scope(self) -> Self:
        if self.record is not None:
            request = self.record.request
            if (self.workspace_id, self.run_id, self.attempt_id, self.lease_epoch) != (
                request.workspace_id,
                request.run_id,
                request.attempt_id,
                request.lease_epoch,
            ):
                raise ValueError("Launch lookup must bind its exact run/attempt/epoch key")
        if self.outbox is not None and (self.workspace_id, self.run_id) != (
            self.outbox.workspace_id,
            self.outbox.run_id,
        ):
            raise ValueError("Launch lookup outbox belongs to a different run")
        return self


class WorkerLaunchPlan(Message):
    expected_run_revision: Number
    expected_credential_revision: Number
    record: WorkerLaunchRecord
    lifecycle: WorkerLaunchLifecycle
    outbox: WorkerCommandOutbox

    @model_validator(mode="after")
    def atomic(self) -> Self:
        record, state, outbox = self.record, self.lifecycle, self.outbox
        digest = message_sha256(record)
        if (
            self.expected_run_revision != record.run_revision
            or self.expected_credential_revision != record.credential_revision
            or state.launch_id != record.launch_id
            or state.launch_record_sha256 != digest
            or state.revision != 0
            or state.state != "prepared"
            or outbox.kind != "launch"
            or outbox.launch_id != record.launch_id
            or outbox.launch_record_sha256 != digest
            or outbox.request_sha256 != record.request_sha256
            or (outbox.workspace_id, outbox.run_id)
            != (record.request.workspace_id, record.request.run_id)
        ):
            raise ValueError(
                "Launch proposal must bind record, initial lifecycle and dispatch outbox"
            )
        return self


class WorkerLaunchReplay(Message):
    """Metadata only: never token material, a launch directive or artifact payload authority."""

    launch_id: Identifier
    request_sha256: Digest
    launch_record_sha256: Digest
    lifecycle_revision: Number
    state: LaunchState


class WorkerTerminationRequest(Message):
    workspace_id: Identifier
    run_id: Identifier
    launch_id: Identifier
    launch_record_sha256: Digest
    expected_lifecycle_revision: Number
    reason: Literal[
        "cancelled",
        "lease_lost",
        "authority_revoked",
        "policy_lost",
        "deadline",
        "operator",
        "completed",
        "budget_exhausted",
    ]


class WorkerTerminationRecord(Message):
    termination_id: Identifier
    request: WorkerTerminationRequest
    request_sha256: Digest
    fenced_lifecycle_revision: Positive
    accepted_at: Number

    @model_validator(mode="after")
    def identity(self) -> Self:
        if (
            self.request_sha256 != message_sha256(self.request)
            or self.fenced_lifecycle_revision != self.request.expected_lifecycle_revision + 1
        ):
            raise ValueError("Termination request must commit its exact dispatch fence")
        return self


class WorkerTerminationPlan(Message):
    launch: WorkerLaunchRecord
    termination: WorkerTerminationRecord
    transition: WorkerLifecycleTransition
    outbox: WorkerCommandOutbox

    @model_validator(mode="after")
    def atomic(self) -> Self:
        launch, record, transition, outbox = (
            self.launch,
            self.termination,
            self.transition,
            self.outbox,
        )
        request = record.request
        digest = message_sha256(launch)
        if (
            request.launch_id != launch.launch_id
            or request.launch_record_sha256 != digest
            or (request.workspace_id, request.run_id)
            != (launch.request.workspace_id, launch.request.run_id)
            or transition.before.launch_id != launch.launch_id
            or transition.before.launch_record_sha256 != digest
            or transition.before.revision != request.expected_lifecycle_revision
            or transition.after.revision != record.fenced_lifecycle_revision
            or transition.after.state not in {"fenced", "stopping"}
            or transition.after.first_fenced_at is None
            or transition.after.first_fenced_at < launch.created_at
            or record.accepted_at < launch.created_at
            or transition.after.first_fenced_at > record.accepted_at
            or outbox.kind != "terminate"
            or outbox.command_id != record.termination_id
            or outbox.launch_id != launch.launch_id
            or outbox.launch_record_sha256 != digest
            or outbox.request_sha256 != record.request_sha256
            or (outbox.workspace_id, outbox.run_id) != (request.workspace_id, request.run_id)
        ):
            raise ValueError("Termination must atomically fence only the exact retained launch")
        return self


class WorkerTerminationEvidence(Message):
    """Trusted exact-instance stop or fenced never-started reconciliation."""

    verification_id: Identifier
    verifier_id: Identifier
    termination_id: Identifier
    request_sha256: Digest
    launch_id: Identifier
    launch_record_sha256: Digest
    fenced_lifecycle_revision: Positive
    outcome: Literal["terminated", "never_started"]
    instance: RuntimeInstance | None
    observed_at: Number

    @model_validator(mode="after")
    def exact_instance(self) -> Self:
        if (self.outcome == "terminated") != (self.instance is not None):
            raise ValueError(
                "Termination outcome must distinguish exact instance from never started"
            )
        if self.instance is not None and (
            self.instance.launch_id != self.launch_id
            or self.instance.launch_record_sha256 != self.launch_record_sha256
            or self.instance.confirmed_at > self.observed_at
        ):
            raise ValueError("Termination evidence must bind the exact observed runtime instance")
        return self


class WorkerTerminationCompletion(Message):
    """Per-launch acknowledgement only. It never changes a current lease or global run state."""

    termination: WorkerTerminationRecord
    evidence: WorkerTerminationEvidence
    transition: WorkerLifecycleTransition

    @model_validator(mode="after")
    def exact_ack(self) -> Self:
        record, proof, transition = self.termination, self.evidence, self.transition
        request = record.request
        after = transition.after
        if (
            proof.termination_id != record.termination_id
            or proof.request_sha256 != record.request_sha256
            or proof.launch_id != request.launch_id
            or proof.launch_record_sha256 != request.launch_record_sha256
            or proof.fenced_lifecycle_revision != record.fenced_lifecycle_revision
            or proof.observed_at < record.accepted_at
            or transition.before.revision < record.fenced_lifecycle_revision
            or after.launch_id != request.launch_id
            or after.launch_record_sha256 != request.launch_record_sha256
            or after.state != "stopped"
            or after.stop_outcome != proof.outcome
            or after.instance != proof.instance
            or after.stopped_at != proof.observed_at
            or after.first_fenced_at is None
            or after.first_fenced_at > record.accepted_at
        ):
            raise ValueError("Acknowledgement must close only its fenced immutable launch")
        return self


WORKER_MODELS: tuple[type[Message], ...] = (
    OriginalExecutionAdmission,
    WorkerPolicy,
    IsolationEvidence,
    WorkerControlPolicy,
    WorkerInternalPrincipal,
    WorkerControlClaims,
    WorkerControlAuthority,
    CheckpointRestoreRef,
    WorkerLaunchRequest,
    WorkerLaunchRecord,
    RuntimeInstance,
    WorkerLaunchLifecycle,
    WorkerLifecycleTransition,
    WorkerCommandOutbox,
    WorkerLaunchLookup,
    WorkerLaunchPlan,
    WorkerLaunchReplay,
    WorkerTerminationRequest,
    WorkerTerminationRecord,
    WorkerTerminationPlan,
    WorkerTerminationEvidence,
    WorkerTerminationCompletion,
)
EXECUTION_MODELS = (*PACKAGE_MODELS, *WORKER_MODELS)


def execution_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in EXECUTION_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/execution.schema.json"
    schema["x-contract-status"] = (
        "EXEC1 API review; runtime predicates and full SP-01.c freeze pending"
    )
    schema["x-public-models"] = ["PackageManifest"]
    schema["description"] = (
        "Only detached PackageManifest is public. Inspection, build, approval, internal authority "
        "and launch/termination records require trusted producers; no execution or isolation proof."
    )
    return schema
