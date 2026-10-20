"""Bounded native model registration proposals. No storage, SQL or predictor execution."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from strange_physics.artifact_checkpoints import checkpoint_committed_prefix
from strange_physics.artifact_contracts import VerifiedArtifact
from strange_physics.contracts import Message, ObservationBundle
from strange_physics.control_contracts import (
    ContractViolation,
    IdempotencyScope,
    ModelReceipt,
    ModelSubmissionResult,
    Operation,
    RunView,
    StoredRequest,
    VerifiedCredential,
)
from strange_physics.model_submission_contracts import (
    ModelAdmissionPlan,
    ModelCommitPlan,
    ModelLedgerSnapshot,
    ModelRegistrationLookup,
    ModelRegistrationOutbox,
    ModelRegistrationPolicy,
    ModelRegistrationRecord,
    ModelSubmissionAdmission,
    ModelSubmissionReplay,
    RunEngineBinding,
    SubmitModelRequest,
    validate_engine_admission,
    validate_model_completion,
    validate_submission_operation,
)
from strange_physics.package_contracts import BuiltinAnalyticApproval
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import (
    LinearSpringModel,
    SpringFitInput,
    message_sha256,
    validate_model_for_fit,
)
from strange_physics.run_credential_contracts import RunProductAuthority
from strange_physics.worker_contracts import WorkerLaunchLookup, WorkerLaunchRecord
from strange_physics.worker_execution import WorkerEnvironment, authorize_worker_broker


@dataclass(frozen=True)
class NativeModelEnvironment:
    """Authoritative current projections, fetched in the same producer transaction.

    Engine selection comes from retained run creation; approval is the current
    registry decision for its exact build/profile; artifact is current catalog
    plus complete readback. These inputs are never populated from client claims.
    """

    policy: ModelRegistrationPolicy | None
    config: SpringPredictionConfig
    approval: BuiltinAnalyticApproval
    engine: RunEngineBinding
    artifact: VerifiedArtifact


def _bounded_canonical(value: Message, limit: int) -> tuple[str, int]:
    """SCI-equivalent encoding without accumulating an unbounded encoded string."""
    digest = hashlib.sha256()
    size = 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(value.model_dump(mode="json")):
        # ensure_ascii=True makes every emitted character one UTF-8 byte.
        size += len(chunk)
        if size > limit:
            raise ContractViolation("invalid_request", 422)
        digest.update(chunk.encode("utf-8"))
    return digest.hexdigest(), size


def _json_structure(raw: bytes, policy: ModelRegistrationPolicy) -> None:
    """Bound nesting and lexical node starts before a decoder allocates containers."""
    depth = nodes = 0
    quoted = escaped = scalar = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
            continue
        if byte == 34:
            quoted = True
            scalar = False
            nodes += 1
        elif byte in (91, 123):
            depth += 1
            nodes += 1
            scalar = False
        elif byte in (93, 125):
            depth -= 1
            scalar = False
        elif byte in (9, 10, 13, 32, 44, 58):
            scalar = False
        elif not scalar:
            nodes += 1
            scalar = True
        if depth < 0 or depth > policy.max_json_depth or nodes > policy.max_json_nodes:
            raise ContractViolation("invalid_request", 422)
    if depth != 0 or quoted:
        raise ContractViolation("invalid_request", 422)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite JSON number")
    return value


def _no_constant(text: str) -> None:
    raise ValueError("Nonstandard JSON constant")


def _parse[M: Message](raw: bytes, model: type[M], policy: ModelRegistrationPolicy) -> M:
    _json_structure(raw, policy)
    try:
        # This bounded first parse establishes strict JSON semantics. Discard it
        # before Pydantic's JSON-mode parse, which preserves strict tuple rules.
        json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_float=_finite_float,
            parse_constant=_no_constant,
        )
        return model.model_validate_json(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ContractViolation("invalid_request", 422) from None


def _worker(
    credential: VerifiedCredential,
    authority: RunProductAuthority,
    environment: WorkerEnvironment,
    lookup: WorkerLaunchLookup,
    *,
    now: int,
) -> tuple[WorkerLaunchRecord, RunView]:
    # This is deliberately the first call in both complete entrypoints.
    authorize_worker_broker("submit_model", credential, authority, environment, lookup, now=now)
    if lookup.record is None:  # Defensive invariant; the complete broker already rejects this.
        raise ContractViolation("recovery_required", 409)
    return lookup.record, environment.current.run


def _native(
    request: SubmitModelRequest,
    native: NativeModelEnvironment,
    worker: WorkerLaunchRecord,
    *,
    now: int,
) -> ModelRegistrationPolicy:
    policy = native.policy
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    if not isinstance(native.approval, BuiltinAnalyticApproval):
        raise ContractViolation("forbidden", 403)
    approval, config, artifact = native.approval, native.config, native.artifact
    build = approval.build
    if (
        request.predictor_profile != approval.profile.predictor_profile
        or request.predictor_version != config.predictor_version
        or request.predictor_version != approval.profile.predictor_version
        or request.prediction_config_sha256 != message_sha256(config)
        or request.prediction_config_sha256 != approval.profile.prediction_config_sha256
        or request.runtime_image_sha256 != build.build.runtime_image_sha256
        or build.source.repository_id != policy.trusted_repository_id
        or build.source.recipe_sha256 != policy.recipe_sha256
        or build.build.builder_image_sha256 != policy.builder_image_sha256
        or build.build.build_policy_sha256 != policy.build_policy_sha256
        or approval.scan.scan_policy_sha256 != policy.scan_policy_sha256
        or approval.approval.approval_policy_sha256 != policy.approval_policy_sha256
        or approval.approval.state != "approved"
        or not approval.approval.decided_at <= now < approval.scan.valid_until
    ):
        raise ContractViolation("forbidden", 403)
    try:
        validate_engine_admission(native.engine, worker.admission)
    except ValueError:
        raise ContractViolation("recovery_required", 409) from None
    if (
        native.engine.committed_at > now
        or artifact.record.ref != request.model_artifact
        or (artifact.record.workspace_id, artifact.record.run_id)
        != (worker.request.workspace_id, worker.request.run_id)
        or artifact.record.state != "available"
        or artifact.record.visibility != "agent-visible"
        or artifact.verification.observed_at > now
        or request.model_artifact.size_bytes > policy.max_model_bytes
    ):
        raise ContractViolation("incompatible_state", 409)
    for item in (request, approval, config, native.engine, artifact):
        _bounded_canonical(item, policy.max_metadata_bytes)
    return policy


def _historical_worker(
    old: WorkerLaunchRecord, current: WorkerLaunchRecord, run: RunView, timestamp: int, now: int
) -> None:
    if (
        old.admission != current.admission
        or old.request.lease_epoch > current.request.lease_epoch
        or (old.request.lease_epoch == current.request.lease_epoch and old != current)
        or old.run_revision > run.revision
        or timestamp > now
        or (
            old.request.lease_epoch < current.request.lease_epoch and current.created_at < timestamp
        )
    ):
        raise ContractViolation("recovery_required", 409)


def _renewal(record: ModelRegistrationRecord, native: NativeModelEnvironment) -> None:
    previous, current = record.approval, native.approval
    if (
        previous.build != current.build
        or previous.profile != current.profile
        or native.config != record.prediction_config
        or native.engine != record.engine
        or native.artifact.record != record.artifact.record
    ):
        raise ContractViolation("incompatible_state", 409)
    if previous.approval.approval_id == current.approval.approval_id and (
        current.approval.revision < previous.approval.revision
        or (current.approval.revision == previous.approval.revision and current != previous)
    ):
        raise ContractViolation("recovery_required", 409)


def _lookup(
    request: SubmitModelRequest,
    scope: IdempotencyScope,
    lookup: ModelRegistrationLookup,
    worker: WorkerLaunchRecord,
    run: RunView,
    native: NativeModelEnvironment,
    policy: ModelRegistrationPolicy,
    *,
    now: int,
) -> StoredRequest | None:
    owner = worker.admission.ownership
    if scope.kind != "model_submission" or (
        scope.workspace_id,
        scope.resource_id,
        scope.principal_id,
    ) != (owner.workspace_id, owner.run_id, owner.principal_id):
        raise ContractViolation("not_found", 404)
    if lookup.scope != scope:
        raise ContractViolation("recovery_required", 409)
    stored, accepted = lookup.stored, lookup.admission
    if stored is None:
        if any(item is not None for item in (accepted, lookup.record, lookup.outbox)):
            raise ContractViolation("recovery_required", 409)
        return None
    if accepted is None:
        raise ContractViolation("recovery_required", 409)
    _bounded_canonical(accepted, policy.max_metadata_bytes)
    _bounded_canonical(stored, policy.max_metadata_bytes)
    if stored.scope != scope:
        raise ContractViolation("recovery_required", 409)
    if stored.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    try:
        validate_submission_operation(accepted, stored)
    except ValueError:
        raise ContractViolation("recovery_required", 409) from None
    if accepted.request != request or accepted.run_revision > run.revision:
        raise ContractViolation("recovery_required", 409)
    _historical_worker(accepted.worker, worker, run, accepted.accepted_at, now)
    if worker.request.lease_epoch > accepted.worker.request.lease_epoch and (
        worker.run_revision < accepted.run_revision
    ):
        raise ContractViolation("recovery_required", 409)
    if stored.operation.status != "completed":
        if lookup.record is not None or lookup.outbox is not None:
            raise ContractViolation("recovery_required", 409)
        return stored
    record, outbox = lookup.record, lookup.outbox
    if record is None or outbox is None:
        raise ContractViolation("recovery_required", 409)
    _bounded_canonical(record, policy.max_metadata_bytes)
    _bounded_canonical(outbox, policy.max_metadata_bytes)
    try:
        validate_model_completion(stored, record, outbox)
    except ValueError:
        raise ContractViolation("recovery_required", 409) from None
    if record.submission != accepted or record.run_revision > run.revision:
        raise ContractViolation("recovery_required", 409)
    _historical_worker(record.worker, worker, run, record.committed_at, now)
    if worker.request.lease_epoch > record.worker.request.lease_epoch and (
        worker.run_revision < record.run_revision
    ):
        raise ContractViolation("recovery_required", 409)
    _renewal(record, native)
    return stored


def admit_model_submission(
    request: SubmitModelRequest,
    scope: IdempotencyScope,
    credential: VerifiedCredential,
    authority: RunProductAuthority,
    worker_environment: WorkerEnvironment,
    worker_lookup: WorkerLaunchLookup,
    native: NativeModelEnvironment,
    lookup: ModelRegistrationLookup,
    *,
    operation_id: str,
    now: int,
) -> ModelAdmissionPlan | ModelSubmissionReplay:
    """Authorize then admit a pending operation, or return its exact retained status.

    A completed replay validates the complete immutable commit and current
    catalog/readback/approval; it does not rerun fitting or reinterpret old data.
    """
    worker, run = _worker(credential, authority, worker_environment, worker_lookup, now=now)
    policy = _native(request, native, worker, now=now)
    stored = _lookup(request, scope, lookup, worker, run, native, policy, now=now)
    if stored is not None:
        return ModelSubmissionReplay(operation=stored.operation)
    accepted = ModelSubmissionAdmission(
        request=request,
        request_sha256=message_sha256(request),
        scope=scope,
        operation_id=operation_id,
        worker=worker,
        run_revision=run.revision,
        accepted_at=now,
    )
    operation = Operation(
        workspace_id=run.workspace_id,
        run_id=run.run_id,
        operation_id=operation_id,
        kind="model_submission",
        request_sha256=accepted.request_sha256,
        status="pending",
        accepted_experiment_index=None,
        result=None,
        error=None,
    )
    plan = ModelAdmissionPlan(
        admission=accepted,
        stored=StoredRequest(
            scope=scope, request_sha256=accepted.request_sha256, operation=operation
        ),
    )
    _bounded_canonical(plan, policy.max_metadata_bytes)
    return plan


def _material(
    request: SubmitModelRequest,
    model_bytes: bytes,
    ledger_bytes: bytes,
    native: NativeModelEnvironment,
    worker: WorkerLaunchRecord,
    run: RunView,
    policy: ModelRegistrationPolicy,
) -> tuple[LinearSpringModel, int]:
    if (
        not isinstance(model_bytes, bytes)
        or not isinstance(ledger_bytes, bytes)
        or not 1 <= len(model_bytes) <= policy.max_model_bytes
        or not 1 <= len(ledger_bytes) <= policy.max_ledger_bytes
    ):
        raise ContractViolation("invalid_request", 422)
    ref = native.artifact.record.ref
    if len(model_bytes) != ref.size_bytes or hashlib.sha256(model_bytes).hexdigest() != ref.sha256:
        raise ContractViolation("incompatible_state", 409)
    model = _parse(model_bytes, LinearSpringModel, policy)
    ledger = _parse(ledger_bytes, ModelLedgerSnapshot, policy)
    if (
        message_sha256(model) != request.model_sha256
        or model.through_index != request.through_index
        or ledger.engine != native.engine
        or ledger.run_revision != run.revision
        or run.space != worker.admission.admitted_run.space
    ):
        raise ContractViolation("incompatible_state", 409)
    prefix = checkpoint_committed_prefix(run, ledger.operations)
    if request.through_index > prefix:
        raise ContractViolation("incompatible_state", 409)
    indexed: list[tuple[int, Operation]] = []
    for operation in ledger.operations:
        index = operation.accepted_experiment_index
        if index is None:
            raise ContractViolation("recovery_required", 409)
        indexed.append((index, operation))
    ordered = [operation for _, operation in sorted(indexed, key=lambda item: item[0])]
    records = []
    for operation in ordered[: request.through_index + 1]:
        result = operation.result
        if operation.status != "completed" or result is None or result.kind != "experiment":
            raise ContractViolation("recovery_required", 409)
        records.append(result.value)
    try:
        observations = ObservationBundle(
            run_id=run.run_id,
            engine_version=native.engine.engine_version,
            engine_fingerprint=native.engine.engine_fingerprint,
            space=run.space,
            records=tuple(records),
        )
        digest, size = _bounded_canonical(observations, policy.max_canonical_prefix_bytes)
        if model.observation_sha256 != digest:
            raise ContractViolation("incompatible_state", 409)
        # The canonical size has already been proved bounded before this frozen
        # SCI helper performs its own canonical hash. fit_config remains a claim.
        validate_model_for_fit(
            model,
            SpringFitInput(
                observations=observations,
                through_index=request.through_index,
                fit_config_sha256=model.fit_config_sha256,
            ),
        )
    except ContractViolation:
        raise
    except ValueError:
        raise ContractViolation("invalid_request", 422) from None
    return model, size


def commit_model_submission(
    request: SubmitModelRequest,
    scope: IdempotencyScope,
    credential: VerifiedCredential,
    authority: RunProductAuthority,
    worker_environment: WorkerEnvironment,
    worker_lookup: WorkerLaunchLookup,
    native: NativeModelEnvironment,
    lookup: ModelRegistrationLookup,
    model_bytes: bytes,
    ledger_bytes: bytes,
    *,
    model_id: str,
    event_id: str,
    now: int,
) -> ModelCommitPlan | ModelSubmissionReplay:
    """Validate actual bounded material and propose one atomic completed record.

    Producers re-read current keyset/lease/lifecycle, artifact and approval under
    the same transaction and apply its CAS fences; retained launch credentials
    are historical metadata. This function performs no persistence or I/O.
    """
    worker, run = _worker(credential, authority, worker_environment, worker_lookup, now=now)
    policy = _native(request, native, worker, now=now)
    stored = _lookup(request, scope, lookup, worker, run, native, policy, now=now)
    if stored is None or lookup.admission is None:
        raise ContractViolation("recovery_required", 409)
    if stored.operation.status in {"failed", "cancelled"}:
        # Preserve explicit terminal failure; never create a model from it.
        return ModelSubmissionReplay(operation=stored.operation)
    model, size = _material(request, model_bytes, ledger_bytes, native, worker, run, policy)
    if stored.operation.status == "completed":
        record = lookup.record
        if record is None or model != record.model or size != record.canonical_prefix_bytes:
            raise ContractViolation("recovery_required", 409)
        return ModelSubmissionReplay(operation=stored.operation)
    try:
        record = ModelRegistrationRecord(
            model_id=model_id,
            submission=lookup.admission,
            model=model,
            artifact=native.artifact,
            prediction_config=native.config,
            approval=native.approval,
            engine=native.engine,
            worker=worker,
            run_revision=run.revision,
            committed_at=now,
            policy_sha256=message_sha256(policy),
            ledger_bytes_sha256=hashlib.sha256(ledger_bytes).hexdigest(),
            ledger_size_bytes=len(ledger_bytes),
            canonical_prefix_bytes=size,
        )
        operation = Operation(
            workspace_id=run.workspace_id,
            run_id=run.run_id,
            operation_id=stored.operation.operation_id,
            kind="model_submission",
            request_sha256=stored.request_sha256,
            status="completed",
            accepted_experiment_index=None,
            result=ModelSubmissionResult(
                kind="model_submission",
                value=ModelReceipt(
                    model_id=model_id,
                    model_sha256=message_sha256(model),
                    through_index=model.through_index,
                ),
            ),
            error=None,
        )
        outbox = ModelRegistrationOutbox(
            event_id=event_id,
            workspace_id=run.workspace_id,
            run_id=run.run_id,
            operation_id=operation.operation_id,
            model_id=model_id,
            request_sha256=stored.request_sha256,
            record_sha256=message_sha256(record),
            committed_at=now,
        )
        plan = ModelCommitPlan(
            before=stored,
            after=StoredRequest(
                scope=scope, request_sha256=stored.request_sha256, operation=operation
            ),
            record=record,
            outbox=outbox,
        )
    except ValidationError:
        raise ContractViolation("invalid_request", 422) from None
    _bounded_canonical(plan, policy.max_metadata_bytes)
    return plan
