"""Native model registration shapes; trusted projections are not authorization or accuracy."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.artifact_contracts import ArtifactRef, Number, VerifiedArtifact
from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import (
    IdempotencyScope,
    ModelSubmissionResult,
    Operation,
    StoredRequest,
    validate_operation_update,
)
from strange_physics.package_contracts import BuiltinAnalyticApproval
from strange_physics.prediction_contracts import PredictorVersion, SpringPredictionConfig
from strange_physics.research_contracts import Digest, Index, LinearSpringModel, message_sha256
from strange_physics.worker_contracts import OriginalExecutionAdmission, WorkerLaunchRecord

MODEL_BYTES = 256 * 1024
LEDGER_BYTES = 8 * 1024 * 1024
PREFIX_BYTES = 8 * 1024 * 1024


class SubmitModelRequest(Message):
    """Public native JSON profile. Registration does not invoke a predictor."""

    model_artifact: ArtifactRef
    model_sha256: Digest
    through_index: Index
    predictor_profile: Literal["strange-physics.linear-spring-prediction.v1"] = (
        "strange-physics.linear-spring-prediction.v1"
    )
    predictor_version: PredictorVersion = "strange-physics.linear-spring.analytic.v1"
    prediction_request_schema: Literal["strange-physics.prediction-request.v1"] = (
        "strange-physics.prediction-request.v1"
    )
    prediction_response_schema: Literal["strange-physics.prediction-response.v1"] = (
        "strange-physics.prediction-response.v1"
    )
    prediction_config_sha256: Digest
    runtime_image_sha256: Digest

    @model_validator(mode="after")
    def native_object(self) -> Self:
        if self.model_artifact.media_type != "application/json":
            raise ValueError("Native models require application/json")
        if not 1 <= self.model_artifact.size_bytes <= MODEL_BYTES:
            raise ValueError("Native model object exceeds protocol byte bounds")
        return self


class ModelRegistrationPolicy(Message):
    """Required configured policy; reference maxima may be lowered, never silently truncated."""

    policy_id: Identifier
    max_model_bytes: Annotated[int, Field(ge=1, le=MODEL_BYTES)]
    max_ledger_bytes: Annotated[int, Field(ge=1, le=LEDGER_BYTES)]
    max_canonical_prefix_bytes: Annotated[int, Field(ge=1, le=PREFIX_BYTES)]
    max_metadata_bytes: Annotated[int, Field(ge=1, le=4 * 1024 * 1024)]
    max_json_depth: Annotated[int, Field(ge=1, le=32)]
    max_json_nodes: Annotated[int, Field(ge=1, le=1_000_000)]
    trusted_repository_id: Identifier
    recipe_sha256: Digest
    builder_image_sha256: Digest
    build_policy_sha256: Digest
    scan_policy_sha256: Digest
    approval_policy_sha256: Digest


class RunEngineBinding(Message):
    """Immutable trusted run-creation engine selection, not a client or predictor claim."""

    workspace_id: Identifier
    run_id: Identifier
    admission_id: Identifier
    admission_sha256: Digest
    creation_request_sha256: Digest
    world_version_id: Identifier
    ownership_sha256: Digest
    space_sha256: Digest
    engine_version: Annotated[str, Field(min_length=1, max_length=128)]
    engine_fingerprint: Digest
    committed_at: Number


def validate_engine_admission(
    binding: RunEngineBinding, admission: OriginalExecutionAdmission
) -> None:
    """Actual immutable admission join. Currency and producer authenticity are separate."""
    run = admission.admitted_run
    if (
        (binding.workspace_id, binding.run_id) != (run.workspace_id, run.run_id)
        or binding.admission_id != admission.admission_id
        or binding.admission_sha256 != message_sha256(admission)
        or binding.creation_request_sha256 != message_sha256(admission.request)
        or binding.world_version_id != admission.request.world_version_id
        or binding.ownership_sha256 != message_sha256(admission.ownership)
        or binding.space_sha256 != message_sha256(run.space)
        or binding.committed_at < admission.ownership.created_at
    ):
        raise ValueError("Engine selection must bind the actual original run admission")


class ModelLedgerSnapshot(Message):
    """Private complete ledger from one transaction. Raw bytes must be capped before parsing."""

    engine: RunEngineBinding
    run_revision: Number
    operations: Annotated[tuple[Operation, ...], Field(max_length=10_000)]

    @model_validator(mode="after")
    def scoped(self) -> Self:
        if any(
            operation.kind != "experiment"
            or (operation.workspace_id, operation.run_id)
            != (self.engine.workspace_id, self.engine.run_id)
            for operation in self.operations
        ):
            raise ValueError("Scientific ledger must contain only the exact run's experiments")
        return self


class ModelSubmissionAdmission(Message):
    """Immutable accepted operation identity, separate from its mutable execution status."""

    request: SubmitModelRequest
    request_sha256: Digest
    scope: IdempotencyScope
    operation_id: Identifier
    worker: WorkerLaunchRecord
    run_revision: Number
    accepted_at: Number

    @model_validator(mode="after")
    def accepted(self) -> Self:
        launch = self.worker
        owner = launch.admission.ownership
        if (
            self.request_sha256 != message_sha256(self.request)
            or self.scope.kind != "model_submission"
            or (self.scope.workspace_id, self.scope.resource_id, self.scope.principal_id)
            != (owner.workspace_id, owner.run_id, owner.principal_id)
            or self.run_revision < launch.run_revision
            or not launch.created_at <= self.accepted_at < launch.deadline
        ):
            raise ValueError("Model admission must bind its original scope, worker and request")
        return self


def validate_submission_operation(
    admission: ModelSubmissionAdmission, stored: StoredRequest
) -> None:
    """Bind a status-bearing operation to its immutable accepted request."""
    operation = stored.operation
    if (
        stored.scope != admission.scope
        or stored.request_sha256 != admission.request_sha256
        or operation.operation_id != admission.operation_id
        or operation.kind != "model_submission"
        or (operation.workspace_id, operation.run_id)
        != (admission.scope.workspace_id, admission.scope.resource_id)
    ):
        raise ValueError("Stored model operation must match its exact accepted request")


class ModelRegistrationRecord(Message):
    """Immutable commit evidence. Actual bytes/prefix and current authority need runtime checks."""

    model_id: Identifier
    submission: ModelSubmissionAdmission
    model: LinearSpringModel
    artifact: VerifiedArtifact
    prediction_config: SpringPredictionConfig
    approval: BuiltinAnalyticApproval
    engine: RunEngineBinding
    worker: WorkerLaunchRecord
    run_revision: Number
    committed_at: Number
    policy_sha256: Digest
    ledger_bytes_sha256: Digest
    ledger_size_bytes: Annotated[int, Field(ge=1, le=LEDGER_BYTES)]
    canonical_prefix_bytes: Annotated[int, Field(ge=1, le=PREFIX_BYTES)]

    @model_validator(mode="after")
    def committed(self) -> Self:
        accepted, worker = self.submission, self.worker
        request, model = accepted.request, self.model
        config, approval, artifact = self.prediction_config, self.approval, self.artifact
        validate_engine_admission(self.engine, worker.admission)
        old = accepted.worker
        if (
            worker.admission != old.admission
            or worker.request.lease_epoch < old.request.lease_epoch
            or (worker.request.lease_epoch == old.request.lease_epoch and worker != old)
            or (
                worker.request.lease_epoch > old.request.lease_epoch
                and (
                    worker.created_at < accepted.accepted_at
                    or worker.run_revision < accepted.run_revision
                )
            )
            or self.run_revision < max(accepted.run_revision, worker.run_revision)
            or self.committed_at < max(accepted.accepted_at, self.engine.committed_at)
            or not worker.created_at <= self.committed_at < worker.deadline
            or self.engine.committed_at > accepted.accepted_at
            or request.model_sha256 != message_sha256(model)
            or request.through_index != model.through_index
            or request.model_artifact != artifact.record.ref
            or (artifact.record.workspace_id, artifact.record.run_id)
            != (accepted.scope.workspace_id, accepted.scope.resource_id)
            or artifact.record.visibility != "agent-visible"
            or artifact.record.state != "available"
            or artifact.verification.observed_at > self.committed_at
            or request.prediction_config_sha256 != message_sha256(config)
            or request.predictor_version != config.predictor_version
            or request.predictor_profile != approval.profile.predictor_profile
            or request.predictor_version != approval.profile.predictor_version
            or request.prediction_config_sha256 != approval.profile.prediction_config_sha256
            or request.runtime_image_sha256 != approval.build.build.runtime_image_sha256
            or approval.approval.state != "approved"
            or not approval.approval.decided_at <= self.committed_at < approval.scan.valid_until
        ):
            raise ValueError("Model commit must join exact artifact, native runtime and provenance")
        return self


class ModelRegistrationOutbox(Message):
    event_id: Identifier
    workspace_id: Identifier
    run_id: Identifier
    operation_id: Identifier
    model_id: Identifier
    request_sha256: Digest
    record_sha256: Digest
    committed_at: Number


def validate_model_completion(
    stored: StoredRequest,
    record: ModelRegistrationRecord,
    outbox: ModelRegistrationOutbox,
) -> None:
    """Complete immutable model/operation/outbox closure, not evidence of fitting accuracy."""
    validate_submission_operation(record.submission, stored)
    operation = stored.operation
    result = operation.result
    if (
        operation.status != "completed"
        or not isinstance(result, ModelSubmissionResult)
        or result.value.model_id != record.model_id
        or result.value.model_sha256 != message_sha256(record.model)
        or result.value.through_index != record.model.through_index
        or (outbox.workspace_id, outbox.run_id, outbox.operation_id)
        != (operation.workspace_id, operation.run_id, operation.operation_id)
        or outbox.model_id != record.model_id
        or outbox.request_sha256 != record.submission.request_sha256
        or outbox.record_sha256 != message_sha256(record)
        or outbox.committed_at != record.committed_at
    ):
        raise ValueError("Completed model receipt requires the exact immutable record and outbox")


class ModelRegistrationLookup(Message):
    """Exact scoped authoritative lookup; partial crash states remain representable for repair."""

    scope: IdempotencyScope
    stored: StoredRequest | None
    admission: ModelSubmissionAdmission | None
    record: ModelRegistrationRecord | None
    outbox: ModelRegistrationOutbox | None

    @model_validator(mode="after")
    def scope_kind(self) -> Self:
        if self.scope.kind != "model_submission":
            raise ValueError("Model lookup requires the exact model idempotency scope")
        return self


class ModelAdmissionPlan(Message):
    """Atomic new pending operation/admission proposal; not a completed model."""

    admission: ModelSubmissionAdmission
    stored: StoredRequest

    @model_validator(mode="after")
    def pending(self) -> Self:
        validate_submission_operation(self.admission, self.stored)
        if self.stored.operation.status != "pending":
            raise ValueError("Fresh model admission must be pending")
        return self


class ModelCommitPlan(Message):
    """Atomic pending/running to completed operation, immutable record and outbox proposal."""

    before: StoredRequest
    after: StoredRequest
    record: ModelRegistrationRecord
    outbox: ModelRegistrationOutbox

    @model_validator(mode="after")
    def closure(self) -> Self:
        validate_submission_operation(self.record.submission, self.before)
        if self.before.scope != self.after.scope or self.before.operation.status not in {
            "pending",
            "running",
        }:
            raise ValueError("Only the same accepted pending/running model operation can commit")
        validate_operation_update(self.before.operation, self.after.operation)
        validate_model_completion(self.after, self.record, self.outbox)
        return self


class ModelSubmissionReplay(Message):
    """Safe operation projection. Producing it requires current complete worker authorization."""

    operation: Operation

    @model_validator(mode="after")
    def model_kind(self) -> Self:
        if self.operation.kind != "model_submission":
            raise ValueError("Model replay must carry a model-submission operation")
        return self


MODEL_REGISTRATION_MODELS: tuple[type[Message], ...] = (
    SubmitModelRequest,
    ModelRegistrationPolicy,
    RunEngineBinding,
    ModelLedgerSnapshot,
    ModelSubmissionAdmission,
    ModelRegistrationRecord,
    ModelRegistrationOutbox,
    ModelRegistrationLookup,
    ModelAdmissionPlan,
    ModelCommitPlan,
    ModelSubmissionReplay,
)


def model_registration_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in MODEL_REGISTRATION_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/model-registration.schema.json"
    schema["x-contract-status"] = "COMP1 API review; runtime and full SP-01.c freeze pending"
    schema["x-public-models"] = ["SubmitModelRequest"]
    schema["description"] = (
        "Only SubmitModelRequest is public. Other projections require trusted current producers; "
        "schemas do not authenticate engine selection, byte identity, fitting or execution."
    )
    return schema
