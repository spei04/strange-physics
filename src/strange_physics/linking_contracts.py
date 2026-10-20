"""Explicit identity association contracts; no verifier, HTTP handler or database.

Every trusted input is produced from current server state. These predicates do not
establish cryptographic truth, serialization, delivery, or broker conformance.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, TypeAdapter, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import Count, Digest
from strange_physics.session_contracts import (
    DeploymentSessionPolicy,
    Flow,
    HttpsURI,
    OIDCCallbackEvidence,
    ProofClaimOwner,
    ProviderPolicy,
    ResponseSecret,
    Seconds,
    Secret,
    Text,
    TrustedIdentityProof,
    provider_for,
    server_time,
    uri_origin,
)
from strange_physics.workspace_contracts import BrowserActor, PrincipalStatus, validate_human_actor

LinkState = Literal[
    "pending", "verifying", "verified", "committed", "restart_required", "recovery_required"
]


class IdentityNamespace(Message):
    """Exact canonical issuer + verified tenant (including explicit null) + subject."""

    issuer: HttpsURI
    tenant_id: Identifier | None
    subject: Text

    @model_validator(mode="after")
    def canonical_issuer(self) -> Self:
        uri_origin(self.issuer)
        return self


class IdentityAssociation(Message):
    identity: IdentityNamespace
    principal_id: Identifier
    active: bool
    revision: Count
    linked_at: Count


class SessionIdentity(Message):
    """Current server provenance of the identity that actually authenticated this session."""

    session_id: Identifier
    generation: Count
    authenticated_at: Count
    identity: IdentityNamespace


class LinkActor(Message):
    actor: BrowserActor
    principal: PrincipalStatus
    primary: IdentityAssociation
    authenticated_identity: SessionIdentity


class LinkProvider(Message):
    provider_id: Identifier
    callback_uri: HttpsURI | None

    @model_validator(mode="after")
    def canonical_callback(self) -> Self:
        if self.callback_uri is not None:
            uri_origin(self.callback_uri)
        return self


class LinkPolicy(Message):
    schema_version: Literal["strange-physics.linking-policy.v1"]
    policy_id: Identifier
    session_policy_id: Identifier
    providers: Annotated[tuple[LinkProvider, ...], Field(min_length=1, max_length=8)]
    challenge_ttl_seconds: Seconds
    receipt_retention_seconds: Seconds

    @model_validator(mode="after")
    def bounds(self) -> Self:
        if len({p.provider_id for p in self.providers}) != len(self.providers):
            raise ValueError("Link provider aliases must be unique")
        if self.receipt_retention_seconds < self.challenge_ttl_seconds:
            raise ValueError("Receipt retention must cover the challenge lifetime")
        return self


class LinkStartRequest(Message):
    provider_id: Identifier


class LinkStartResponse(Message):
    challenge_id: Identifier
    provider_id: Identifier
    flow: Flow
    expires_at: Count
    authorization_url: ResponseSecret | None

    @model_validator(mode="after")
    def authorization_flow(self) -> Self:
        if (self.authorization_url is not None) != (self.flow == "oidc_code"):
            raise ValueError("Only OIDC supplies an authorization URL")
        return self


class LinkExchangeRequest(Message):
    id_token: Secret


class LinkCommitRequest(Message):
    expected_revision: Count


class LinkResult(Message):
    challenge_id: Identifier
    state: Literal["linked"]


class LinkStatus(Message):
    challenge_id: Identifier
    state: LinkState
    expires_at: Count
    expired: bool
    next_action: Literal[
        "authenticate_secondary", "reconcile", "commit", "done", "start_new_challenge"
    ]


class LinkError(Message):
    code: Literal[
        "invalid_request",
        "policy_unavailable",
        "unauthenticated",
        "forbidden",
        "ambiguous_credentials",
        "unsupported_flow",
        "reauthentication_required",
        "not_found",
        "link_expired",
        "proof_rejected",
        "link_conflict",
        "recovery_required",
        "temporarily_unavailable",
    ]
    request_id: Identifier


class LinkChallenge(Message):
    purpose: Literal["link_identity"]
    challenge_id: Identifier
    link_policy_id: Identifier
    session_policy_id: Identifier
    provider_id: Identifier
    principal_id: Identifier
    session_id: Identifier
    generation: Count
    authenticated_at: Count
    primary_identity: IdentityNamespace
    primary_revision: Count
    browser_binding_sha256: Digest
    created_at: Count
    expires_at: Count
    revision: Count
    state: LinkState
    proof: TrustedIdentityProof | None
    consumed_at: Count | None

    @model_validator(mode="after")
    def lifecycle(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("Challenge must have a positive lifetime")
        if self.state in {"verified", "committed"} and self.proof is None:
            raise ValueError("Verified/committed challenges retain their proof")
        if self.state in {"pending", "verifying", "restart_required"} and self.proof is not None:
            raise ValueError("Unverified challenges cannot contain proof")
        if (self.consumed_at is not None) != (self.state == "committed"):
            raise ValueError("Only committed challenges are consumed")
        if (
            self.consumed_at is not None
            and not self.created_at < self.consumed_at < self.expires_at
        ):
            raise ValueError("Commit must be within the original challenge lifetime")
        if self.proof is not None and (
            self.proof.purpose != self.purpose
            or self.proof.transaction_id != self.challenge_id
            or self.proof.provider_id != self.provider_id
            or self.proof.browser_binding_sha256 != self.browser_binding_sha256
        ):
            raise ValueError("Proof must belong to this link challenge")
        return self


class LinkReceipt(Message):
    challenge_id: Identifier
    principal_id: Identifier
    identity: IdentityNamespace
    proof_sha256: Digest
    challenge_revision: Count
    committed_at: Count
    retain_until: Count


class LinkClaimConsumption(Message):
    """Atomic consumed tombstone in the SAME global digest registry used by login."""

    proof_sha256: Digest
    owner: ProofClaimOwner
    consumed_at: Count
    retain_until: Count


class LinkAudit(Message):
    event: Literal["identity_linked"]
    challenge_id: Identifier
    principal_id: Identifier
    identity: IdentityNamespace
    proof_sha256: Digest
    occurred_at: Count


def identity_namespace(proof: TrustedIdentityProof) -> IdentityNamespace:
    """Provider aliases, audiences and emails never partition identity ownership."""
    return IdentityNamespace(issuer=proof.issuer, tenant_id=proof.tenant_id, subject=proof.subject)


def _policies(
    session_policy: DeploymentSessionPolicy | None, link_policy: LinkPolicy | None
) -> tuple[DeploymentSessionPolicy, LinkPolicy]:
    if (
        session_policy is None
        or link_policy is None
        or link_policy.session_policy_id != session_policy.policy_id
    ):
        raise ContractViolation("policy_unavailable", 503)
    return session_policy, link_policy


def _provider(
    session_policy: DeploymentSessionPolicy, link_policy: LinkPolicy, provider_id: str
) -> tuple[ProviderPolicy, LinkProvider]:
    provider = provider_for(session_policy, provider_id)
    link_provider = next((p for p in link_policy.providers if p.provider_id == provider_id), None)
    if link_provider is None:
        raise ContractViolation("unsupported_flow", 422)
    if provider.flow == "managed_broker":
        # Google documents that tenants cannot disable automatic account linking.
        # No boolean assertion can enable that profile in this contract.
        if provider.tenant_id is not None or link_provider.callback_uri is not None:
            raise ContractViolation("unsupported_flow", 422)
    elif (
        link_provider.callback_uri is None
        or uri_origin(link_provider.callback_uri) not in session_policy.app_origins
        or link_provider.callback_uri == provider.callback_uri
    ):
        raise ContractViolation("unsupported_flow", 422)
    return provider, link_provider


def _actor(
    session_policy: DeploymentSessionPolicy, context: LinkActor, *, now: int, mutation: bool
) -> None:
    validate_human_actor(session_policy, context.actor, now=now, mutation=mutation)
    session = context.actor.session
    primary_providers = [
        provider
        for provider in session_policy.providers
        if provider.issuer == context.primary.identity.issuer
        and provider.tenant_id == context.primary.identity.tenant_id
    ]
    if not primary_providers:
        raise ContractViolation("unauthenticated", 401)
    if any(p.flow == "managed_broker" and p.tenant_id is not None for p in primary_providers):
        raise ContractViolation("unsupported_flow", 422)
    if now - session.authenticated_at >= session_policy.recent_auth_seconds:
        raise ContractViolation("reauthentication_required", 401)
    if (
        not context.principal.active
        or context.principal.principal_id != session.principal_id
        or not context.primary.active
        or context.primary.principal_id != session.principal_id
        or context.authenticated_identity.session_id != session.session_id
        or context.authenticated_identity.generation != session.generation
        or context.authenticated_identity.authenticated_at != session.authenticated_at
        or context.authenticated_identity.identity != context.primary.identity
        or context.actor.context.browser_binding_sha256 is None
    ):
        raise ContractViolation("unauthenticated", 401)


def validate_link_start(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    request: LinkStartRequest,
    challenge: LinkChallenge,
    *,
    now: int,
) -> None:
    configured, linking = _policies(session_policy, link_policy)
    _actor(configured, context, now=now, mutation=True)
    _provider(configured, linking, request.provider_id)
    if (
        challenge.provider_id != request.provider_id
        or challenge.created_at != now
        or challenge.state != "pending"
        or challenge.revision != 0
    ):
        raise ContractViolation("link_conflict", 409)
    validate_link_binding(configured, linking, context, challenge, now=now, mutation=True)


def validate_link_binding(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    challenge: LinkChallenge,
    *,
    now: int,
    mutation: bool,
    allow_expired: bool = False,
) -> tuple[DeploymentSessionPolicy, LinkPolicy]:
    configured, linking = _policies(session_policy, link_policy)
    _actor(configured, context, now=now, mutation=mutation)
    _provider(configured, linking, challenge.provider_id)
    session = context.actor.session
    if (
        challenge.link_policy_id != linking.policy_id
        or challenge.session_policy_id != configured.policy_id
        or challenge.principal_id != session.principal_id
        or challenge.session_id != session.session_id
        or challenge.generation != session.generation
        or challenge.authenticated_at != session.authenticated_at
        or challenge.primary_identity != context.primary.identity
        or challenge.primary_revision != context.primary.revision
        or challenge.browser_binding_sha256 != context.actor.context.browser_binding_sha256
        or challenge.expires_at != challenge.created_at + linking.challenge_ttl_seconds
        or now < challenge.created_at
    ):
        raise ContractViolation("not_found", 404)
    if not allow_expired and now >= challenge.expires_at:
        raise ContractViolation("link_expired", 401)
    return configured, linking


def validate_link_callback(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    challenge: LinkChallenge,
    evidence: OIDCCallbackEvidence,
    *,
    now: int,
) -> None:
    configured, linking = validate_link_binding(
        session_policy, link_policy, context, challenge, now=now, mutation=False
    )
    provider, adapter = _provider(configured, linking, challenge.provider_id)
    if (
        provider.flow != "oidc_code"
        or evidence.callback_uri != adapter.callback_uri
        or uri_origin(evidence.callback_uri) != context.actor.context.target_origin
        or not evidence.state_matches
        or not evidence.nonce_matches
        or not evidence.pkce_s256_verified
        or challenge.state not in {"verifying", "verified"}
    ):
        raise ContractViolation("proof_rejected", 401)


def validate_link_proof(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    challenge: LinkChallenge,
    proof: TrustedIdentityProof,
    *,
    now: int,
    claimed_by: ProofClaimOwner | None,
    oidc_evidence: OIDCCallbackEvidence | None = None,
) -> None:
    # The adapter selects the flow from server policy, never from the supplied proof.
    configured, linking = validate_link_binding(
        session_policy, link_policy, context, challenge, now=now, mutation=False
    )
    provider, _ = _provider(configured, linking, challenge.provider_id)
    if provider.flow == "managed_broker":
        _actor(configured, context, now=now, mutation=True)
    if provider.flow == "oidc_code":
        if oidc_evidence is None:
            raise ContractViolation("proof_rejected", 401)
        validate_link_callback(configured, linking, context, challenge, oidc_evidence, now=now)
    elif oidc_evidence is not None:
        raise ContractViolation("proof_rejected", 401)
    owner = ProofClaimOwner(purpose="link_identity", transaction_id=challenge.challenge_id)
    if (
        challenge.state not in {"verifying", "verified"}
        or proof.purpose != "link_identity"
        or proof.transaction_id != challenge.challenge_id
        or proof.provider_id != provider.provider_id
        or proof.browser_binding_sha256 != challenge.browser_binding_sha256
        or proof.flow != provider.flow
        or proof.issuer != provider.issuer
        or proof.audience != provider.audience
        or proof.tenant_id != provider.tenant_id
        or claimed_by not in (None, owner)
        or (challenge.state == "verified" and claimed_by != owner)
        or (
            provider.flow == "managed_broker"
            and proof.upstream_provider not in provider.upstream_providers
        )
        or (provider.flow == "oidc_code" and proof.upstream_provider is not None)
        or proof.auth_time <= challenge.created_at
        or proof.auth_time > now
        or proof.auth_time > proof.issued_at
        or proof.issued_at > proof.verified_at
        or proof.verified_at > now + configured.clock_skew_seconds
        or proof.verified_at >= proof.expires_at
        or now >= proof.expires_at
        or now - proof.auth_time >= configured.recent_auth_seconds
        or identity_namespace(proof) == context.primary.identity
        or (challenge.proof is not None and challenge.proof != proof)
    ):
        raise ContractViolation("proof_rejected", 401)


def validate_link_transition(
    before: LinkChallenge, after: LinkChallenge, *, expected_revision: int
) -> None:
    server_time(expected_revision)
    allowed: dict[str, set[str]] = {
        "pending": {"verifying", "restart_required"},
        "verifying": {"verified", "recovery_required"},
        "verified": {"committed", "recovery_required"},
    }
    mutable = {"revision", "state", "proof", "consumed_at"}
    if (
        before.revision != expected_revision
        or after.revision != before.revision + 1
        or after.state not in allowed.get(before.state, set())
        or before.model_dump(exclude=mutable) != after.model_dump(exclude=mutable)
        or (before.proof is not None and after.proof != before.proof)
    ):
        raise ContractViolation("link_conflict", 409)


def validate_link_verification(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    before: LinkChallenge,
    after: LinkChallenge,
    *,
    now: int,
    claimed_by: ProofClaimOwner,
    oidc_evidence: OIDCCallbackEvidence | None = None,
) -> None:
    """Atomic durable proof reservation + verified state, before association."""
    validate_link_binding(session_policy, link_policy, context, before, now=now, mutation=False)
    if before.state != "verifying" or after.state != "verified" or after.proof is None:
        raise ContractViolation("link_conflict", 409)
    validate_link_proof(
        session_policy,
        link_policy,
        context,
        after,
        after.proof,
        now=now,
        claimed_by=claimed_by,
        oidc_evidence=oidc_evidence,
    )
    validate_link_transition(before, after, expected_revision=before.revision)


def link_claim_retain_until(
    session_policy: DeploymentSessionPolicy, link_policy: LinkPolicy, challenge: LinkChallenge
) -> int:
    _policies(session_policy, link_policy)
    if (
        challenge.proof is None
        or challenge.link_policy_id != link_policy.policy_id
        or challenge.session_policy_id != session_policy.policy_id
    ):
        raise ValueError("Retention requires the bound policy and verified challenge")
    deadline = max(
        challenge.proof.expires_at,
        challenge.created_at + session_policy.transaction_retention_seconds,
        challenge.created_at + link_policy.receipt_retention_seconds,
    )
    return TypeAdapter(Count).validate_python(deadline, strict=True)


def validate_link_commit(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    before: LinkChallenge,
    after: LinkChallenge,
    request: LinkCommitRequest,
    *,
    existing: IdentityAssociation | None,
    associated: IdentityAssociation,
    claimed_by: ProofClaimOwner,
    consumption: LinkClaimConsumption,
    receipt: LinkReceipt,
    audit: LinkAudit,
    now: int,
    oidc_evidence: OIDCCallbackEvidence | None = None,
) -> None:
    configured, linking = validate_link_binding(
        session_policy, link_policy, context, before, now=now, mutation=True
    )
    if before.state != "verified" or before.proof is None or after.state != "committed":
        raise ContractViolation("recovery_required", 409)
    validate_link_proof(
        configured,
        linking,
        context,
        before,
        before.proof,
        now=now,
        claimed_by=claimed_by,
        oidc_evidence=oidc_evidence,
    )
    # No special case for inactive ownership, same owner, provider alias or matching email.
    if existing is not None:
        raise ContractViolation("link_conflict", 409)
    validate_link_transition(before, after, expected_revision=request.expected_revision)
    identity = identity_namespace(before.proof)
    owner = ProofClaimOwner(purpose="link_identity", transaction_id=before.challenge_id)
    retain_until = link_claim_retain_until(configured, linking, before)
    if (
        after.consumed_at != now
        or associated
        != IdentityAssociation(
            identity=identity,
            principal_id=before.principal_id,
            active=True,
            revision=0,
            linked_at=now,
        )
        or consumption
        != LinkClaimConsumption(
            proof_sha256=before.proof.proof_sha256,
            owner=owner,
            consumed_at=now,
            retain_until=retain_until,
        )
        or receipt
        != LinkReceipt(
            challenge_id=before.challenge_id,
            principal_id=before.principal_id,
            identity=identity,
            proof_sha256=before.proof.proof_sha256,
            challenge_revision=before.revision,
            committed_at=now,
            retain_until=retain_until,
        )
        or audit
        != LinkAudit(
            event="identity_linked",
            challenge_id=before.challenge_id,
            principal_id=before.principal_id,
            identity=identity,
            proof_sha256=before.proof.proof_sha256,
            occurred_at=now,
        )
    ):
        raise ContractViolation("link_conflict", 409)


def replay_link_commit(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    challenge: LinkChallenge,
    request: LinkCommitRequest,
    *,
    associated: IdentityAssociation | None,
    consumption: LinkClaimConsumption | None,
    receipt: LinkReceipt | None,
    audit: LinkAudit | None,
    now: int,
) -> LinkResult:
    configured, linking = validate_link_binding(
        session_policy, link_policy, context, challenge, now=now, mutation=True, allow_expired=True
    )
    proof = challenge.proof
    if (
        challenge.state != "committed"
        or proof is None
        or receipt is None
        or consumption is None
        or audit is None
        or associated is None
        or challenge.consumed_at is None
    ):
        raise ContractViolation("recovery_required", 409)
    identity = identity_namespace(proof)
    deadline = link_claim_retain_until(configured, linking, challenge)
    if (
        now >= deadline
        or now < challenge.consumed_at
        or request.expected_revision != challenge.revision - 1
        or associated
        != IdentityAssociation(
            identity=identity,
            principal_id=challenge.principal_id,
            active=True,
            revision=0,
            linked_at=challenge.consumed_at,
        )
        or consumption
        != LinkClaimConsumption(
            proof_sha256=proof.proof_sha256,
            owner=ProofClaimOwner(purpose="link_identity", transaction_id=challenge.challenge_id),
            consumed_at=challenge.consumed_at,
            retain_until=deadline,
        )
        or audit
        != LinkAudit(
            event="identity_linked",
            challenge_id=challenge.challenge_id,
            principal_id=challenge.principal_id,
            identity=identity,
            proof_sha256=proof.proof_sha256,
            occurred_at=challenge.consumed_at,
        )
        or receipt
        != LinkReceipt(
            challenge_id=challenge.challenge_id,
            principal_id=challenge.principal_id,
            identity=identity,
            proof_sha256=proof.proof_sha256,
            challenge_revision=request.expected_revision,
            committed_at=challenge.consumed_at,
            retain_until=deadline,
        )
    ):
        raise ContractViolation("link_conflict", 409)
    return LinkResult(challenge_id=challenge.challenge_id, state="linked")


def link_status(
    session_policy: DeploymentSessionPolicy | None,
    link_policy: LinkPolicy | None,
    context: LinkActor,
    challenge: LinkChallenge,
    *,
    now: int,
) -> LinkStatus:
    validate_link_binding(
        session_policy, link_policy, context, challenge, now=now, mutation=False, allow_expired=True
    )
    actions: dict[
        LinkState,
        Literal["authenticate_secondary", "reconcile", "commit", "done", "start_new_challenge"],
    ] = {
        "pending": "authenticate_secondary",
        "verifying": "reconcile",
        "verified": "commit",
        "committed": "done",
        "restart_required": "start_new_challenge",
        "recovery_required": "reconcile",
    }
    expired = now >= challenge.expires_at
    action = actions[challenge.state]
    if expired and challenge.state in {"pending", "verified", "restart_required"}:
        action = "start_new_challenge"
    return LinkStatus(
        challenge_id=challenge.challenge_id,
        state=challenge.state,
        expires_at=challenge.expires_at,
        expired=expired,
        next_action=action,
    )


LINK_MODELS: tuple[type[Message], ...] = (
    IdentityNamespace,
    IdentityAssociation,
    SessionIdentity,
    LinkActor,
    LinkProvider,
    LinkPolicy,
    LinkStartRequest,
    LinkStartResponse,
    LinkExchangeRequest,
    LinkCommitRequest,
    LinkResult,
    LinkStatus,
    LinkError,
    LinkChallenge,
    LinkReceipt,
    LinkClaimConsumption,
    LinkAudit,
)
PUBLIC_MODELS: tuple[type[Message], ...] = (
    LinkStartRequest,
    LinkStartResponse,
    LinkExchangeRequest,
    LinkCommitRequest,
    LinkResult,
    LinkStatus,
    LinkError,
)


def linking_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in LINK_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/linking.schema.json"
    schema["x-contract-status"] = "linking-v1 review; SP-01.b remains partial"
    schema["x-public-models"] = [model.__name__ for model in PUBLIC_MODELS]
    schema["description"] = (
        "Public link shapes plus private trusted projections and pure conformance predicates. "
        "No crypto, broker, HTTP, persistence, race or recovery implementation."
    )
    return schema
