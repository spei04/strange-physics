"""Internal C2 authority and coordinator messages; no public mint route or token issuer.

Every snapshot and verified claim is supplied by a trusted current producer.
Parsing these models proves neither signature verification nor database currency.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import RunLease, RunView
from strange_physics.credential_authority import CredentialOwner
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.service_contracts import ServiceCredentialPolicy, ServiceKeySet
from strange_physics.session_contracts import DeploymentSessionPolicy, HttpsURI
from strange_physics.workspace_contracts import BrowserActor, IdempotencyKey

WorkerPermission = Literal[
    "experiments:read", "experiments:write", "checkpoints:write", "models:write"
]
WorkerScopes = Annotated[tuple[WorkerPermission, ...], Field(min_length=1, max_length=4)]
RunCredentialOperation = Literal["issue", "replace", "revoke"]
Audience = Annotated[str, Field(min_length=1, max_length=512)]


def worker_scopes(scopes: tuple[str, ...]) -> None:
    if tuple(sorted(set(scopes))) != scopes:
        raise ValueError("Worker scopes must be unique and canonically sorted")


class RunOwnership(Message):
    """Immutable admission record; creator leaf credentials are audit metadata only."""

    workspace_id: Identifier
    run_id: Identifier
    principal_id: Identifier
    principal_kind: Literal["human", "service"]
    principal_generation: Count
    grant_incarnation: Count
    created_at: Count
    run_deadline: Count
    scopes: WorkerScopes
    created_by_credential_id: Identifier

    @model_validator(mode="after")
    def bounded(self) -> Self:
        worker_scopes(self.scopes)
        if self.run_deadline <= self.created_at:
            raise ValueError("Original run deadline must follow admission")
        return self


class RunCredentialPolicy(Message):
    """Explicit immutable issuer settings; no approved production defaults."""

    policy_id: Identifier
    issuer: HttpsURI
    audience: Audience
    max_ttl_seconds: Annotated[int, Field(ge=1, le=31_536_000)]
    receipt_retention_seconds: Annotated[int, Field(ge=1, le=31_536_000)]
    max_records: Annotated[int, Field(ge=1, le=10_000)]


class RunTokenClaims(Message):
    """Mint proposal or actual verified claims, distinguished by their producer."""

    policy_id: Identifier
    issuer: HttpsURI
    audience: Audience
    credential_id: Identifier
    workspace_id: Identifier
    run_id: Identifier
    principal_id: Identifier
    ownership_sha256: Digest
    attempt_id: Identifier
    lease_epoch: Count
    generation: Annotated[int, Field(ge=1, le=2**53 - 1)]
    scopes: WorkerScopes
    issued_at: Count
    expires_at: Count

    @model_validator(mode="after")
    def bounded(self) -> Self:
        worker_scopes(self.scopes)
        if self.expires_at <= self.issued_at:
            raise ValueError("Worker credential must have positive lifetime")
        return self


class RunCredentialRecord(Message):
    """Retained authoritative state; no serialized bearer or signing material."""

    claims: RunTokenClaims
    revoked_at: Count | None
    retain_until: Count

    @model_validator(mode="after")
    def retained(self) -> Self:
        if self.retain_until < self.claims.expires_at:
            raise ValueError("Record must outlive original credential expiry")
        if self.revoked_at is not None and (
            self.revoked_at < self.claims.issued_at or self.retain_until < self.revoked_at
        ):
            raise ValueError("Revocation must follow issuance and remain retained")
        return self


class RunCredentialSet(Message):
    """Complete retained run state, under one shared run/credential serialization domain."""

    ownership: RunOwnership
    revision: Count
    last_generation: Count
    current_credential_id: Identifier | None
    records: Annotated[tuple[RunCredentialRecord, ...], Field(max_length=10_000)]

    @model_validator(mode="after")
    def binding(self) -> Self:
        claims = tuple(record.claims for record in self.records)
        ids = tuple(item.credential_id for item in claims)
        ownership_digest = message_sha256(self.ownership)
        if (
            tuple(sorted(set(ids))) != ids
            or len({item.generation for item in claims}) != len(claims)
            or any(
                item.workspace_id != self.ownership.workspace_id
                or item.run_id != self.ownership.run_id
                or item.principal_id != self.ownership.principal_id
                or item.ownership_sha256 != ownership_digest
                or item.scopes != self.ownership.scopes
                or item.issued_at < self.ownership.created_at
                or item.expires_at > self.ownership.run_deadline
                or item.generation > self.last_generation
                for item in claims
            )
        ):
            raise ValueError("Run credential records must bind immutable ownership and generations")
        if self.current_credential_id is not None:
            current = next(
                (
                    record
                    for record in self.records
                    if record.claims.credential_id == self.current_credential_id
                ),
                None,
            )
            if (
                current is None
                or current.revoked_at is not None
                or current.claims.generation != self.last_generation
            ):
                raise ValueError("Current credential must name the latest unrevoked generation")
        return self


class RunAuthorityState(Message):
    """Current owner, run, lease and complete credentials; currency is a producer obligation."""

    owner: CredentialOwner
    run: RunView
    lease: RunLease
    credentials: RunCredentialSet

    @model_validator(mode="after")
    def same_resources(self) -> Self:
        ownership = self.credentials.ownership
        if (
            (self.run.workspace_id, self.run.run_id) != (ownership.workspace_id, ownership.run_id)
            or (self.lease.workspace_id, self.lease.run_id)
            != (ownership.workspace_id, ownership.run_id)
            or self.owner.principal.principal_id != ownership.principal_id
            or self.owner.principal.kind != ownership.principal_kind
            or self.owner.grant.membership.workspace_id != ownership.workspace_id
        ):
            raise ValueError("Current run authority must refer to one immutable owner and run")
        return self


class RunCoordinatorAuthority(Message):
    """Current independently verified internal coordinator authorization, never a client body."""

    actor_id: Identifier
    authorization_id: Identifier
    workspace_id: Identifier
    run_id: Identifier
    permission: Literal["run-credentials:manage"]
    expires_at: Count
    revoked: bool


class HumanProductAuthority(Message):
    kind: Literal["user"]
    policy: DeploymentSessionPolicy | None
    actor: BrowserActor
    owner: CredentialOwner
    session_principal_generation: Count

    @model_validator(mode="after")
    def same_human(self) -> Self:
        if (
            self.owner.principal.kind != "human"
            or self.owner.principal.principal_id != self.actor.session.principal_id
        ):
            raise ValueError("Human product authority must bind the same app session principal")
        return self


class ServiceProductAuthority(Message):
    kind: Literal["service"]
    policy: ServiceCredentialPolicy | None
    current: ServiceKeySet
    credential_id: Identifier


class RunProductAuthority(Message):
    kind: Literal["run"]
    policy: RunCredentialPolicy | None
    current: RunAuthorityState
    verified_claims: RunTokenClaims


ProductAuthority = Annotated[
    HumanProductAuthority | ServiceProductAuthority | RunProductAuthority,
    Field(discriminator="kind"),
]


class ProductAuthorityEnvelope(Message):
    """Schema carrier for the mandatory internal union, never a public HTTP envelope."""

    authority: ProductAuthority


class RunCredentialIssueRequest(Message):
    expected_run_revision: Count
    expected_credential_revision: Count


class RunCredentialReplaceRequest(RunCredentialIssueRequest):
    credential_id: Identifier


class RunCredentialRevokeRequest(RunCredentialIssueRequest):
    credential_id: Identifier


class RunCredentialView(Message):
    record: RunCredentialRecord
    credential_revision: Count
    current_generation: Count
    current_credential_id: Identifier | None
    valid_now: bool

    @model_validator(mode="after")
    def current_binding(self) -> Self:
        if self.current_generation < self.record.claims.generation or (
            self.valid_now
            and (
                self.current_credential_id != self.record.claims.credential_id
                or self.current_generation != self.record.claims.generation
                or self.record.revoked_at is not None
            )
        ):
            raise ValueError("Validity requires the current unrevoked credential generation")
        return self


class RunCredentialOutcome(Message):
    operation: RunCredentialOperation
    workspace_id: Identifier
    run_id: Identifier
    ownership_sha256: Digest
    attempt_id: Identifier
    lease_epoch: Count
    credential_id: Identifier
    replaced_credential_id: Identifier | None
    run_revision: Count
    credential_revision: Count
    committed_at: Count

    @model_validator(mode="after")
    def targets(self) -> Self:
        if (self.replaced_credential_id is not None) != (self.operation == "replace"):
            raise ValueError("Only replacement identifies a replaced credential")
        if self.replaced_credential_id == self.credential_id:
            raise ValueError("Replacement must allocate a fresh credential identity")
        return self


class RunCredentialSnapshot(Message):
    ownership: RunOwnership
    run_revision: Count
    credential_revision: Count
    last_generation: Count
    current_credential_id: Identifier | None
    records: Annotated[tuple[RunCredentialRecord, ...], Field(min_length=1, max_length=2)]

    @model_validator(mode="after")
    def records_bound(self) -> Self:
        # An affected subset may omit a different current key on historical-key revocation.
        RunCredentialSet(
            ownership=self.ownership,
            revision=self.credential_revision,
            last_generation=self.last_generation,
            current_credential_id=None,
            records=self.records,
        )
        return self


class RunCredentialReceipt(Message):
    policy_id: Identifier
    actor_id: Identifier
    authorization_id: Identifier
    key: IdempotencyKey
    request_sha256: Digest
    outcome: RunCredentialOutcome
    snapshot: RunCredentialSnapshot
    audit_event_id: Identifier
    retain_until: Count

    @model_validator(mode="after")
    def bound(self) -> Self:
        outcome, snapshot = self.outcome, self.snapshot
        ownership = snapshot.ownership
        expected_ids = {outcome.credential_id}
        if outcome.replaced_credential_id is not None:
            expected_ids.add(outcome.replaced_credential_id)
        if (
            outcome.workspace_id != ownership.workspace_id
            or outcome.run_id != ownership.run_id
            or outcome.ownership_sha256 != message_sha256(ownership)
            or outcome.run_revision != snapshot.run_revision
            or outcome.credential_revision != snapshot.credential_revision
            or {r.claims.credential_id for r in snapshot.records} != expected_ids
            or self.retain_until <= outcome.committed_at
            or any(record.retain_until < self.retain_until for record in snapshot.records)
        ):
            raise ValueError("Receipt must bind the complete retained outcome and affected state")
        return self


class RunCredentialAudit(Message):
    event_id: Identifier
    actor_id: Identifier
    authorization_id: Identifier
    request_sha256: Digest
    outcome: RunCredentialOutcome
    snapshot_sha256: Digest


class RunCredentialLookup(Message):
    state: Literal["absent", "committed", "recovery_required"]
    receipt: RunCredentialReceipt | None
    audit: RunCredentialAudit | None

    @model_validator(mode="after")
    def absence(self) -> Self:
        if self.state == "absent" and (self.receipt is not None or self.audit is not None):
            raise ValueError("Absent means never reserved, not expired or unresolved")
        return self


class RunCredentialResponse(Message):
    disposition: Literal["committed", "replayed"]
    outcome: RunCredentialOutcome
    credential: RunCredentialView

    @model_validator(mode="after")
    def bound(self) -> Self:
        if (
            self.outcome.credential_id != self.credential.record.claims.credential_id
            or self.outcome.workspace_id != self.credential.record.claims.workspace_id
            or self.outcome.run_id != self.credential.record.claims.run_id
            or self.outcome.ownership_sha256 != self.credential.record.claims.ownership_sha256
            or self.outcome.credential_revision > self.credential.credential_revision
            or (
                self.disposition == "committed"
                and self.outcome.credential_revision != self.credential.credential_revision
            )
        ):
            raise ValueError(
                "Response must distinguish original outcome from current safe metadata"
            )
        return self


class RunCredentialPlan(Message):
    """Atomic proposal; issue_claims is an original-handler directive, never a bearer.

    Only a real producer that confirms the commit and rechecks current authority may
    deliver once. A metadata-only retry returns RunCredentialResponse, never this plan.
    """

    credentials: RunCredentialSet
    receipt: RunCredentialReceipt
    audit: RunCredentialAudit
    response: RunCredentialResponse
    issue_claims: RunTokenClaims | None

    @model_validator(mode="after")
    def bound(self) -> Self:
        snapshot, outcome = self.receipt.snapshot, self.receipt.outcome
        if (
            self.credentials.ownership != snapshot.ownership
            or self.credentials.revision != snapshot.credential_revision
            or self.credentials.last_generation != snapshot.last_generation
            or self.credentials.current_credential_id != snapshot.current_credential_id
            or self.response.disposition != "committed"
            or self.response.outcome != outcome
            or self.response.credential.record not in self.credentials.records
            or self.response.credential.credential_revision != self.credentials.revision
            or self.response.credential.current_generation != self.credentials.last_generation
            or self.response.credential.current_credential_id
            != self.credentials.current_credential_id
            or self.audit
            != RunCredentialAudit(
                event_id=self.receipt.audit_event_id,
                actor_id=self.receipt.actor_id,
                authorization_id=self.receipt.authorization_id,
                request_sha256=self.receipt.request_sha256,
                outcome=outcome,
                snapshot_sha256=message_sha256(snapshot),
            )
            or (self.issue_claims is not None) != (outcome.operation in {"issue", "replace"})
            or (
                self.issue_claims is not None
                and self.issue_claims != self.response.credential.record.claims
            )
        ):
            raise ValueError("Atomic proposal must bind state, receipt, audit and delivery intent")
        for record in snapshot.records:
            if record not in self.credentials.records:
                raise ValueError("Affected snapshots must equal the proposed committed records")
        return self


RUN_CREDENTIAL_MODELS: tuple[type[Message], ...] = (
    RunOwnership,
    RunCredentialPolicy,
    RunTokenClaims,
    RunCredentialRecord,
    RunCredentialSet,
    RunAuthorityState,
    RunCoordinatorAuthority,
    HumanProductAuthority,
    ServiceProductAuthority,
    RunProductAuthority,
    ProductAuthorityEnvelope,
    RunCredentialIssueRequest,
    RunCredentialReplaceRequest,
    RunCredentialRevokeRequest,
    RunCredentialView,
    RunCredentialOutcome,
    RunCredentialSnapshot,
    RunCredentialReceipt,
    RunCredentialAudit,
    RunCredentialLookup,
    RunCredentialResponse,
    RunCredentialPlan,
)


def run_credential_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in RUN_CREDENTIAL_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/run-credentials.schema.json"
    schema["description"] = (
        "C2 private producer messages, not public mint routes or evidence of token verification, "
        "current database state, signing, delivery or commit."
    )
    return schema
