"""Pure launch, broker and exact-termination proposals; no process or database mutation."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

from strange_physics.artifact_checkpoints import (
    _lookup as _checkpoint_history,
)
from strange_physics.artifact_checkpoints import (
    checkpoint_committed_prefix,
    validate_checkpoint_restore_candidate,
)
from strange_physics.artifact_contracts import (
    ArtifactPolicy,
    CheckpointArtifacts,
    CheckpointAttempt,
    CheckpointLookup,
    Number,
)
from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation, Operation, VerifiedCredential
from strange_physics.package_contracts import PackagePolicy, SubmittedRuntimeApproval
from strange_physics.package_validation import metadata_size, validate_submitted_approval
from strange_physics.product_authority import run_key_valid, validate_run_authority
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import (
    RunAuthorityState,
    RunCredentialPolicy,
    RunCredentialRecord,
    RunProductAuthority,
)
from strange_physics.serialization import canonical_json
from strange_physics.session_contracts import server_time
from strange_physics.worker_contracts import (
    BROKER_PERMISSIONS,
    IsolationEvidence,
    OriginalExecutionAdmission,
    RuntimeInstance,
    WorkerCommandOutbox,
    WorkerControlAuthority,
    WorkerControlPolicy,
    WorkerLaunchLifecycle,
    WorkerLaunchLookup,
    WorkerLaunchPlan,
    WorkerLaunchRecord,
    WorkerLaunchReplay,
    WorkerLaunchRequest,
    WorkerLifecycleTransition,
    WorkerPolicy,
    WorkerPurpose,
    WorkerTerminationCompletion,
    WorkerTerminationEvidence,
    WorkerTerminationPlan,
    WorkerTerminationRecord,
    WorkerTerminationRequest,
)
from strange_physics.workspace_contracts import (
    WorkspaceAuthority,
    _product_workspace,
    authorize_product,
)


@dataclass(frozen=True)
class WorkerEnvironment:
    """Current trusted projections, not a serialized public envelope or proof of currency."""

    current: RunAuthorityState
    workspace: WorkspaceAuthority
    credential_policy: RunCredentialPolicy | None
    package_policy: PackagePolicy | None
    worker_policy: WorkerPolicy | None
    approval: SubmittedRuntimeApproval
    isolation: IsolationEvidence | None


@dataclass(frozen=True)
class RestoreCandidate:
    """Committed selected ART1 candidate; no payload or read authorization."""

    lookup: CheckpointLookup
    operations: tuple[Operation, ...]
    artifacts: CheckpointArtifacts
    policy: ArtifactPolicy


def _changed[M: Message](value: M, **fields: object) -> M:
    return type(value).model_validate(value.model_dump() | fields)


def _increment(value: int) -> int:
    try:
        return TypeAdapter(Number).validate_python(value + 1, strict=True)
    except ValidationError as error:
        raise ContractViolation("incompatible_state", 409) from error


def authorize_worker_control(
    policy: WorkerControlPolicy | None,
    authority: WorkerControlAuthority,
    *,
    purpose: WorkerPurpose,
    workspace_id: str,
    run_id: str,
    launch_id: str | None,
    now: int,
) -> None:
    """Current internal purpose/scope only; never confers worker product permissions."""
    server_time(now)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    claims, principal = authority.claims, authority.principal
    if (
        claims.revoked
        or not principal.active
        or claims.principal_generation != principal.generation
        or claims.policy_id != policy.policy_id
        or claims.issuer != policy.issuer
        or claims.audience != policy.audience
        or not claims.issued_at <= now < claims.expires_at
        or claims.expires_at - claims.issued_at > policy.max_authorization_seconds
    ):
        raise ContractViolation("unauthenticated", 401)
    if (
        claims.purpose != purpose
        or purpose not in principal.purposes
        or (claims.workspace_id, claims.run_id, claims.launch_id)
        != (workspace_id, run_id, launch_id)
    ):
        raise ContractViolation("forbidden", 403)


def _work(
    environment: WorkerEnvironment,
    admission: OriginalExecutionAdmission,
    request: WorkerLaunchRequest,
    *,
    now: int,
) -> RunCredentialRecord:
    current, policy = environment.current, environment.credential_policy
    validate_run_authority(current, now=now)
    _product_workspace(environment.workspace, request.workspace_id, current.owner.grant.membership)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    if (
        current.credentials.ownership != admission.ownership
        or current.run.space != admission.admitted_run.space
        or (request.workspace_id, request.run_id, request.attempt_id, request.lease_epoch)
        != (
            current.run.workspace_id,
            current.run.run_id,
            current.lease.attempt_id,
            current.lease.epoch,
        )
        or request.admission_sha256 != message_sha256(admission)
    ):
        raise ContractViolation("forbidden", 403)
    key = next(
        (
            record
            for record in current.credentials.records
            if record.claims.credential_id == current.credentials.current_credential_id
        ),
        None,
    )
    if key is None or not run_key_valid(current, key, policy, now=now):
        raise ContractViolation("unauthenticated", 401)
    worker = validate_submitted_approval(
        environment.approval, environment.package_policy, environment.worker_policy, now=now
    )
    isolation = environment.isolation
    if (
        request.approval_sha256 != message_sha256(environment.approval)
        or request.worker_policy_sha256 != message_sha256(worker)
        or isolation is None
        or isolation.worker_policy_sha256 != message_sha256(worker)
        or isolation.sandbox_profile != worker.sandbox_profile
        or isolation.network_policy != worker.network_policy
        or isolation.state != "available"
        or not isolation.observed_at <= now < isolation.valid_until
    ):
        raise ContractViolation("policy_unavailable", 503)
    if (
        any(
            getattr(request.resources, name) > getattr(worker.worker_limits, name)
            for name in type(request.resources).model_fields
        )
        or len(canonical_json(admission.agent_configuration).encode("utf-8"))
        > worker.max_configuration_bytes
        or metadata_size(request) > worker.max_metadata_bytes
        or metadata_size(admission) > worker.max_metadata_bytes
    ):
        raise ContractViolation("invalid_request", 422)
    return key


def _lookup_key(lookup: WorkerLaunchLookup, request: WorkerLaunchRequest) -> None:
    if (lookup.workspace_id, lookup.run_id, lookup.attempt_id, lookup.lease_epoch) != (
        request.workspace_id,
        request.run_id,
        request.attempt_id,
        request.lease_epoch,
    ):
        raise ContractViolation("recovery_required", 409)


def _closure(
    lookup: WorkerLaunchLookup, *, now: int
) -> tuple[WorkerLaunchRecord, WorkerLaunchLifecycle]:
    """Complete retained launch/lifecycle/outbox; transaction establishes uniqueness."""
    record, state, outbox = lookup.record, lookup.lifecycle, lookup.outbox
    if record is None or state is None or outbox is None:
        raise ContractViolation("recovery_required", 409)
    digest = message_sha256(record)
    # A known instance enters during active confirmation (revision 2), or
    # later during stop reconciliation. Fenced/stopping cannot invent one.
    known = state.instance is not None
    minimum, maximum = {
        "prepared": (0, 0),
        "dispatch_unknown": (1, 1),
        "active": (2, 2),
        "fenced": (3, 3) if known else (1, 2),
        "stopping": (4, 4) if known else (2, 3),
        "stopped": (2, 5) if known else (2, 4),
    }[state.state]
    if (
        record.created_at > now
        or state.launch_id != record.launch_id
        or state.launch_record_sha256 != digest
        or not minimum <= state.revision <= maximum
        or (state.state == "prepared" and state.revision != 0)
        or outbox.kind != "launch"
        or outbox.launch_id != record.launch_id
        or outbox.launch_record_sha256 != digest
        or outbox.request_sha256 != record.request_sha256
        or (outbox.workspace_id, outbox.run_id)
        != (record.request.workspace_id, record.request.run_id)
        or (
            state.instance is not None
            and not record.created_at <= state.instance.confirmed_at <= now
        )
        or (
            state.first_fenced_at is not None
            and not record.created_at <= state.first_fenced_at <= now
        )
        or (
            (
                state.state in {"fenced", "stopping"}
                or (state.state == "stopped" and state.revision == 5)
            )
            and state.instance is not None
            and state.first_fenced_at is not None
            and state.instance.confirmed_at > state.first_fenced_at
        )
        or (state.stopped_at is not None and state.stopped_at > now)
        or (
            state.instance is not None
            and state.stopped_at is not None
            and state.instance.confirmed_at > state.stopped_at
        )
    ):
        raise ContractViolation("recovery_required", 409)
    return record, state


def _restore(
    request: WorkerLaunchRequest,
    admission: OriginalExecutionAdmission,
    candidate: RestoreCandidate | None,
    *,
    current: RunAuthorityState,
    now: int,
) -> None:
    if request.restore is None:
        if candidate is not None:
            raise ContractViolation("invalid_request", 422)
        return
    if candidate is None or candidate.lookup.record is None or candidate.lookup.outbox is None:
        raise ContractViolation("recovery_required", 409)
    ref, record = request.restore, candidate.lookup.record
    if (
        ref.index != record.index
        or ref.request_sha256 != record.request_sha256
        or ref.record_sha256 != message_sha256(record)
    ):
        raise ContractViolation("incompatible_state", 409)
    attempt = CheckpointAttempt(
        workspace_id=request.workspace_id,
        run_id=request.run_id,
        attempt_id=request.attempt_id,
        lease_epoch=request.lease_epoch,
        binding=admission.checkpoint_binding,
    )
    prefix = checkpoint_committed_prefix(current.run, candidate.operations)
    _checkpoint_history(
        candidate.lookup,
        workspace_id=request.workspace_id,
        run_id=request.run_id,
        index=ref.index,
        prefix=prefix,
        run_revision=current.run.revision,
        attempt=attempt,
        now=now,
    )
    validate_checkpoint_restore_candidate(
        record,
        expected_attempt=attempt,
        policy=candidate.policy,
        artifacts=candidate.artifacts,
        now=now,
    )


def _retained_work(
    environment: WorkerEnvironment,
    admission: OriginalExecutionAdmission,
    request: WorkerLaunchRequest,
    lookup: WorkerLaunchLookup,
    *,
    now: int,
) -> tuple[WorkerLaunchRecord, WorkerLaunchLifecycle]:
    record, state = _closure(lookup, now=now)
    if record.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    current = environment.current
    if (
        record.admission != admission
        or record.approval != environment.approval
        or current.run.revision < record.run_revision
        or current.credentials.revision < record.credential_revision
        or current.credentials.last_generation < record.original_credential_generation
        or (
            current.credentials.current_credential_id == record.original_credential_id
            and current.credentials.last_generation != record.original_credential_generation
        )
        or (
            current.credentials.current_credential_id != record.original_credential_id
            and (
                current.credentials.last_generation <= record.original_credential_generation
                or current.credentials.revision <= record.credential_revision
            )
        )
    ):
        raise ContractViolation("recovery_required", 409)
    if state.state in {"fenced", "stopping", "stopped"} or now >= record.deadline:
        raise ContractViolation("forbidden", 403)
    return record, state


def admit_worker_launch(
    request: WorkerLaunchRequest,
    *,
    admission: OriginalExecutionAdmission,
    environment: WorkerEnvironment,
    control_policy: WorkerControlPolicy | None,
    authority: WorkerControlAuthority,
    lookup: WorkerLaunchLookup,
    restore: RestoreCandidate | None,
    launch_id: str,
    now: int,
) -> WorkerLaunchPlan | WorkerLaunchReplay:
    """Current-authorized atomic proposal or metadata replay; no dispatch or payload."""
    authorize_worker_control(
        control_policy,
        authority,
        purpose="workers:launch",
        workspace_id=request.workspace_id,
        run_id=request.run_id,
        launch_id=None,
        now=now,
    )
    key = _work(environment, admission, request, now=now)
    _lookup_key(lookup, request)
    _restore(request, admission, restore, current=environment.current, now=now)
    if any(value is not None for value in (lookup.record, lookup.lifecycle, lookup.outbox)):
        record, state = _retained_work(environment, admission, request, lookup, now=now)
        return WorkerLaunchReplay(
            launch_id=record.launch_id,
            request_sha256=record.request_sha256,
            launch_record_sha256=message_sha256(record),
            lifecycle_revision=state.revision,
            state=state.state,
        )
    current = environment.current
    TypeAdapter(Identifier).validate_python(launch_id, strict=True)
    try:
        record = WorkerLaunchRecord(
            launch_id=launch_id,
            request=request,
            request_sha256=message_sha256(request),
            admission=admission,
            approval=environment.approval,
            original_credential_id=key.claims.credential_id,
            original_credential_generation=key.claims.generation,
            run_revision=current.run.revision,
            credential_revision=current.credentials.revision,
            created_at=now,
            deadline=min(
                admission.ownership.run_deadline,
                current.lease.expires_at,
                now + request.resources.wall_seconds,
            ),
        )
    except ValidationError as error:
        raise ContractViolation("invalid_request", 422) from error
    digest = message_sha256(record)
    return WorkerLaunchPlan(
        expected_run_revision=current.run.revision,
        expected_credential_revision=current.credentials.revision,
        record=record,
        lifecycle=WorkerLaunchLifecycle(
            launch_id=launch_id,
            launch_record_sha256=digest,
            revision=0,
            state="prepared",
            instance=None,
            first_fenced_at=None,
            stopped_at=None,
            stop_outcome=None,
        ),
        outbox=WorkerCommandOutbox(
            command_id=launch_id,
            kind="launch",
            workspace_id=request.workspace_id,
            run_id=request.run_id,
            launch_id=launch_id,
            launch_record_sha256=digest,
            request_sha256=record.request_sha256,
        ),
    )


def advance_worker_launch(
    request: WorkerLaunchRequest,
    *,
    admission: OriginalExecutionAdmission,
    environment: WorkerEnvironment,
    control_policy: WorkerControlPolicy | None,
    authority: WorkerControlAuthority,
    lookup: WorkerLaunchLookup,
    restore: RestoreCandidate | None,
    instance: RuntimeInstance | None,
    now: int,
) -> WorkerLifecycleTransition:
    """Dispatch intent/confirmed-instance proposal; never calls a provider."""
    result = admit_worker_launch(
        request,
        admission=admission,
        environment=environment,
        control_policy=control_policy,
        authority=authority,
        lookup=lookup,
        restore=restore,
        launch_id="unused-on-replay",
        now=now,
    )
    if not isinstance(result, WorkerLaunchReplay):
        raise ContractViolation("recovery_required", 409)
    record, before = _closure(lookup, now=now)
    if instance is None:
        if before.state == "dispatch_unknown":
            return WorkerLifecycleTransition(before=before, after=before)
        if before.state != "prepared":
            raise ContractViolation("incompatible_state", 409)
        after = _changed(before, revision=_increment(before.revision), state="dispatch_unknown")
    else:
        if (
            instance.launch_id != record.launch_id
            or instance.launch_record_sha256 != message_sha256(record)
            or not record.created_at <= instance.confirmed_at <= now
        ):
            raise ContractViolation("recovery_required", 409)
        if before.state == "active" and before.instance == instance:
            return WorkerLifecycleTransition(before=before, after=before)
        if before.state != "dispatch_unknown":
            raise ContractViolation("incompatible_state", 409)
        after = _changed(
            before, revision=_increment(before.revision), state="active", instance=instance
        )
    return WorkerLifecycleTransition(before=before, after=after)


def authorize_worker_broker(
    operation: str,
    credential: VerifiedCredential,
    authority: RunProductAuthority,
    environment: WorkerEnvironment,
    lookup: WorkerLaunchLookup,
    *,
    now: int,
) -> None:
    """Complete per-operation current C2 + approved active-launch predicate.

    Recheck before every commit and payload batch. A denial never supplies payload.
    Policy-loss producers must atomically fence the exact launch before any later work.
    """
    permission = next(
        (value for name, value in BROKER_PERMISSIONS.items() if name == operation), None
    )
    if permission is None:
        raise ContractViolation("forbidden", 403)
    # Current bearer/role/grant checks precede retained launch evidence.
    authorize_product(
        environment.workspace,
        credential,
        authority.current.owner.grant.membership,
        authority=authority,
        permission=permission,
        workspace_id=authority.current.run.workspace_id,
        run_id=authority.current.run.run_id,
        lease=authority.current.lease,
        now=now,
    )
    if (
        authority.current != environment.current
        or authority.policy != environment.credential_policy
    ):
        raise ContractViolation("forbidden", 403)
    record, state = _closure(lookup, now=now)
    _lookup_key(lookup, record.request)
    _work(environment, record.admission, record.request, now=now)
    _retained_work(environment, record.admission, record.request, lookup, now=now)
    if state.state != "active":
        raise ContractViolation("incompatible_state", 409)


def _termination_closure(
    request: WorkerTerminationRequest,
    lookup: WorkerLaunchLookup,
    *,
    now: int,
) -> tuple[WorkerLaunchRecord, WorkerLaunchLifecycle]:
    launch, state = _closure(lookup, now=now)
    if (
        request.launch_id != launch.launch_id
        or request.launch_record_sha256 != message_sha256(launch)
        or (request.workspace_id, request.run_id) != (lookup.workspace_id, lookup.run_id)
    ):
        raise ContractViolation("not_found", 404)
    return launch, state


def _termination_receipt(
    request: WorkerTerminationRequest,
    receipt: WorkerTerminationRecord,
    outbox: WorkerCommandOutbox | None,
    state: WorkerLaunchLifecycle,
    *,
    now: int,
) -> None:
    if receipt.request_sha256 != message_sha256(request):
        raise ContractViolation("idempotency_conflict", 409)
    # From its committed fence a receipt can remain fenced, advance once to
    # stopping, and then stop. A later receipt may itself commit stopping.
    distance = state.revision - receipt.fenced_lifecycle_revision
    allowed_distances = {"fenced": {0}, "stopping": {0, 1}, "stopped": {1, 2}}
    if distance not in allowed_distances.get(state.state, set()):
        raise ContractViolation("recovery_required", 409)
    if (
        receipt.request != request
        or outbox is None
        or outbox.kind != "terminate"
        or outbox.command_id != receipt.termination_id
        or (
            outbox.workspace_id,
            outbox.run_id,
            outbox.launch_id,
            outbox.launch_record_sha256,
            outbox.request_sha256,
        )
        != (
            request.workspace_id,
            request.run_id,
            request.launch_id,
            request.launch_record_sha256,
            receipt.request_sha256,
        )
        or receipt.accepted_at > now
        or (state.stopped_at is not None and state.stopped_at < receipt.accepted_at)
        or state.revision < receipt.fenced_lifecycle_revision
        or state.state not in {"fenced", "stopping", "stopped"}
        or state.first_fenced_at is None
        or state.first_fenced_at > receipt.accepted_at
        or (
            state.revision == receipt.fenced_lifecycle_revision
            and state.state not in {"fenced", "stopping"}
        )
    ):
        raise ContractViolation("recovery_required", 409)


def terminate_worker_launch(
    request: WorkerTerminationRequest,
    *,
    control_policy: WorkerControlPolicy | None,
    authority: WorkerControlAuthority,
    lookup: WorkerLaunchLookup,
    receipt: WorkerTerminationRecord | None,
    outbox: WorkerCommandOutbox | None,
    termination_id: str,
    now: int,
) -> WorkerTerminationPlan | WorkerTerminationRecord:
    """Exact old-launch proposal/replay; deliberately takes no current work authority."""
    authorize_worker_control(
        control_policy,
        authority,
        purpose="workers:terminate",
        workspace_id=request.workspace_id,
        run_id=request.run_id,
        launch_id=request.launch_id,
        now=now,
    )
    launch, before = _termination_closure(request, lookup, now=now)
    if receipt is not None:
        _termination_receipt(request, receipt, outbox, before, now=now)
        return receipt
    if outbox is not None:
        raise ContractViolation("recovery_required", 409)
    if request.expected_lifecycle_revision != before.revision or before.state == "stopped":
        raise ContractViolation("incompatible_state", 409)
    if before.state == "stopping":
        # A prior committed stop must be reconciled, not overwritten by a new receipt.
        raise ContractViolation("recovery_required", 409)
    TypeAdapter(Identifier).validate_python(termination_id, strict=True)
    after = _changed(
        before,
        revision=_increment(before.revision),
        state="stopping" if before.state == "fenced" else "fenced",
        first_fenced_at=now if before.first_fenced_at is None else before.first_fenced_at,
    )
    record = WorkerTerminationRecord(
        termination_id=termination_id,
        request=request,
        request_sha256=message_sha256(request),
        fenced_lifecycle_revision=after.revision,
        accepted_at=now,
    )
    return WorkerTerminationPlan(
        launch=launch,
        termination=record,
        transition=WorkerLifecycleTransition(before=before, after=after),
        outbox=WorkerCommandOutbox(
            command_id=termination_id,
            kind="terminate",
            workspace_id=request.workspace_id,
            run_id=request.run_id,
            launch_id=request.launch_id,
            launch_record_sha256=request.launch_record_sha256,
            request_sha256=record.request_sha256,
        ),
    )


def complete_worker_termination(
    receipt: WorkerTerminationRecord,
    evidence: WorkerTerminationEvidence,
    *,
    control_policy: WorkerControlPolicy | None,
    authority: WorkerControlAuthority,
    lookup: WorkerLaunchLookup,
    outbox: WorkerCommandOutbox | None,
    now: int,
) -> WorkerTerminationCompletion:
    """Current internal authority + retained exact fence; unknown evidence has no success path."""
    request = receipt.request
    authorize_worker_control(
        control_policy,
        authority,
        purpose="workers:terminate",
        workspace_id=request.workspace_id,
        run_id=request.run_id,
        launch_id=request.launch_id,
        now=now,
    )
    launch, before = _termination_closure(request, lookup, now=now)
    _termination_receipt(request, receipt, outbox, before, now=now)
    if evidence.observed_at > now or (
        evidence.instance is not None and evidence.instance.confirmed_at < launch.created_at
    ):
        raise ContractViolation("recovery_required", 409)
    if before.instance is not None and evidence.instance != before.instance:
        raise ContractViolation("recovery_required", 409)
    try:
        if before.state == "stopped":
            after = before
        else:
            after = _changed(
                before,
                revision=_increment(before.revision),
                state="stopped",
                instance=evidence.instance,
                stopped_at=evidence.observed_at,
                stop_outcome=evidence.outcome,
            )
        return WorkerTerminationCompletion(
            termination=receipt,
            evidence=evidence,
            transition=WorkerLifecycleTransition(before=before, after=after),
        )
    except ValidationError as error:
        raise ContractViolation("recovery_required", 409) from error
