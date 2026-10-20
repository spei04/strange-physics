"""Browser-session conformance predicates, not token verification or HTTP handlers.

All *trusted* inputs come from an authenticated adapter/current transaction.
Parsing these models never establishes identity, CSRF validity or persistence.
"""

from __future__ import annotations

from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, TypeAdapter, WithJsonSchema, model_validator
from pydantic.json_schema import JsonSchemaValue, models_json_schema

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation
from strange_physics.control_contracts import Error as ControlError
from strange_physics.research_contracts import Count, Digest

Seconds = Annotated[int, Field(ge=1, le=2**31 - 1)]
Text = Annotated[str, Field(min_length=1, max_length=512)]
HttpsURI = Annotated[
    str,
    Field(
        min_length=9,
        max_length=2048,
        pattern=r"^https://[!-~]+$",
        json_schema_extra={"not": {"pattern": "[^!-~]"}},
    ),
]
Secret = Annotated[SecretStr, Field(min_length=1, max_length=16384)]
ResponseSecret = Annotated[
    SecretStr,
    Field(min_length=1, max_length=16384),
    # Preserve runtime redaction without marking intentionally returned values write-only.
    WithJsonSchema({"type": "string", "minLength": 1, "maxLength": 16384, "readOnly": True}),
]
Flow = Literal["managed_broker", "oidc_code"]
LoginState = Literal["pending", "verifying", "verified", "committed", "restart_required"]
ErrorCode = Literal[
    "invalid_request",
    "policy_unavailable",
    "unauthenticated",
    "forbidden",
    "ambiguous_credentials",
    "unsupported_flow",
    "login_expired",
    "proof_rejected",
    "login_conflict",
    "reconciliation_required",
    "reauthentication_required",
    "session_conflict",
]
COOKIE_NAME = "__Host-sp_session"
PREAUTH_COOKIE_NAME = "__Host-sp_login"
RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def uri_origin(value: str) -> str:
    """Accept a deliberately narrow canonical HTTPS profile; never normalize input."""
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or any(c in value for c in ("\\", "%", "?", "#"))
        or any(ord(c) < 33 or ord(c) > 126 for c in value)
    ):
        raise ValueError("URI must be canonical HTTPS without credentials, query or fragment")
    host = parsed.hostname
    if (
        host is None
        or parsed.netloc.split(":")[0] != host
        or any(
            not label
            or label.startswith("-")
            or label.endswith("-")
            or any(not (c.isascii() and (c.islower() or c.isdigit() or c == "-")) for c in label)
            for label in host.split(".")
        )
    ):
        raise ValueError("URI host must be canonical lowercase ASCII")
    port = parsed.port
    authority = host if port is None else f"{host}:{port}"
    if parsed.netloc != authority or port == 443 or port == 0:
        raise ValueError("URI port must be canonical; omit default HTTPS port")
    if any(part in {".", ".."} for part in parsed.path.split("/")):
        raise ValueError("URI cannot contain dot segments")
    return f"https://{authority}"


class ProviderPolicy(Message):
    provider_id: Identifier
    flow: Flow
    issuer: HttpsURI
    audience: Text
    tenant_id: Identifier | None
    callback_uri: HttpsURI | None
    callback_method: Literal["GET"] | None
    response_mode: Literal["query"] | None
    upstream_providers: tuple[Literal["google.com", "github.com"], ...]

    @model_validator(mode="after")
    def validate_profile(self) -> Self:
        uri_origin(self.issuer)
        if self.flow == "oidc_code":
            if self.callback_uri is None or self.callback_method != "GET":
                raise ValueError("OIDC requires an exact GET callback")
            uri_origin(self.callback_uri)
            if self.response_mode != "query" or self.upstream_providers:
                raise ValueError("OIDC supports only query code response, without broker providers")
        else:
            if (self.callback_uri, self.callback_method, self.response_mode) != (None, None, None):
                raise ValueError("Managed callback belongs to the broker, not the app adapter")
            if not self.upstream_providers or len(set(self.upstream_providers)) != len(
                self.upstream_providers
            ):
                raise ValueError("Broker requires unique approved upstream providers")
            if self.issuer != f"https://securetoken.google.com/{self.audience}":
                raise ValueError("Managed broker issuer must match configured project audience")
        return self


class DeploymentSessionPolicy(Message):
    schema_version: Literal["strange-physics.session-policy.v1"] = (
        "strange-physics.session-policy.v1"
    )
    policy_id: Identifier
    app_origins: Annotated[tuple[HttpsURI, ...], Field(min_length=1, max_length=16)]
    return_uris: Annotated[tuple[HttpsURI, ...], Field(min_length=1, max_length=32)]
    providers: Annotated[tuple[ProviderPolicy, ...], Field(min_length=1, max_length=8)]
    idle_seconds: Seconds
    absolute_seconds: Seconds
    recent_auth_seconds: Seconds
    login_ttl_seconds: Seconds
    clock_skew_seconds: Annotated[int, Field(ge=0, le=300)]
    transaction_retention_seconds: Seconds

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        if self.idle_seconds > self.absolute_seconds:
            raise ValueError("Idle lifetime cannot exceed absolute lifetime")
        if self.transaction_retention_seconds < self.login_ttl_seconds:
            raise ValueError("Retained transaction outcomes must outlive login eligibility")
        for values in (self.app_origins, self.return_uris):
            if len(set(values)) != len(values):
                raise ValueError("URI policy entries must be unique")
        for origin in self.app_origins:
            if uri_origin(origin) != origin:
                raise ValueError("An origin has no path or trailing slash")
        for value in self.return_uris:
            if uri_origin(value) not in self.app_origins:
                raise ValueError("Return URI must belong to an approved app origin")
        if len({p.provider_id for p in self.providers}) != len(self.providers):
            raise ValueError("Provider identities must be unique")
        for provider in self.providers:
            if provider.callback_uri and uri_origin(provider.callback_uri) not in self.app_origins:
                raise ValueError("App callback must belong to an approved origin")
        return self


class LoginOption(Message):
    provider_id: Identifier
    flow: Flow


class LoginOptions(Message):
    providers: Annotated[tuple[LoginOption, ...], Field(min_length=1, max_length=8)]


class LoginStartRequest(Message):
    provider_id: Identifier
    return_uri: HttpsURI


class BrokerExchangeRequest(Message):
    transaction_id: Identifier
    id_token: Secret


class OIDCCallbackRequest(Message):
    code: Secret
    state: Secret


class OIDCDeniedCallbackRequest(Message):
    error: Secret
    state: Secret


class LoginStatusResponse(Message):
    transaction_id: Identifier
    state: LoginState
    expired: bool
    next_action: Literal[
        "verify_once",
        "reconcile_or_restart",
        "commit_same_transaction",
        "bootstrap_or_login",
        "fresh_login",
    ]


class LoginStartResponse(Message):
    transaction_id: Identifier
    provider_id: Identifier
    flow: Flow
    expires_at: Count
    authorization_url: ResponseSecret | None

    @model_validator(mode="after")
    def validate_flow(self) -> Self:
        if (self.authorization_url is not None) != (self.flow == "oidc_code"):
            raise ValueError("Only the OIDC adapter supplies an authorization URL")
        return self


class CSRFResponse(Message):
    scope: Literal["preauth", "session"]
    token: ResponseSecret


class SessionView(Message):
    session_id: Identifier
    generation: Count
    authenticated_at: Count
    idle_expires_at: Count
    absolute_expires_at: Count

    @model_validator(mode="after")
    def validate_times(self) -> Self:
        if not self.authenticated_at < self.idle_expires_at <= self.absolute_expires_at:
            raise ValueError("Session view deadlines must follow authentication")
        return self


class SessionBootstrap(Message):
    authenticated: bool
    principal_id: Identifier | None
    session: SessionView | None

    @model_validator(mode="after")
    def validate_projection(self) -> Self:
        if self.authenticated != (self.principal_id is not None and self.session is not None):
            raise ValueError("Authenticated bootstrap requires principal and session")
        if not self.authenticated and (self.principal_id is not None or self.session is not None):
            raise ValueError("Signed-out bootstrap contains no identity")
        return self


class RenewalRequest(Message):
    expected_generation: Count


class SessionError(Message):
    code: ErrorCode
    request_id: Identifier


def workspace_session_error(
    violation: ContractViolation,
    *,
    request_id: str,
) -> tuple[int, ControlError]:
    """Map authentication failures into the existing workspace Error envelope."""
    mapping = {
        "ambiguous_credentials": (400, "invalid_request", "Use one authentication method.", False),
        "policy_unavailable": (
            503,
            "temporarily_unavailable",
            "Authentication policy is unavailable.",
            True,
        ),
        "unauthenticated": (401, "unauthenticated", "Authentication required.", False),
        "forbidden": (403, "forbidden", "Request is not permitted.", False),
    }
    if violation.code not in mapping:
        raise ValueError("Unsupported workspace session failure")
    status, code, message, retryable = mapping[violation.code]
    if violation.status != status:
        raise ValueError("Workspace session failure has an inconsistent status")
    # Validate against the unchanged control schema instead of widening its vocabulary.
    error = ControlError.model_validate(
        {
            "code": code,
            "message": message,
            "request_id": request_id,
            "retryable": retryable,
            "operation_id": None,
        }
    )
    return status, error


class BrowserContext(Message):
    """Trusted HTTP adapter projection; CSRF comparisons must be constant-time."""

    target_origin: HttpsURI
    origin: HttpsURI | None
    has_session_cookie: bool
    has_bearer: bool
    csrf_scope: Literal["preauth", "session"] | None
    csrf_matches: bool
    browser_binding_sha256: Digest | None


class TrustedIdentityProof(Message):
    """Minimal durable verifier result; never accepted from a public request."""

    transaction_id: Identifier
    provider_id: Identifier
    browser_binding_sha256: Digest
    proof_sha256: Digest
    flow: Flow
    issuer: HttpsURI
    audience: Text
    tenant_id: Identifier | None
    upstream_provider: Literal["google.com", "github.com"] | None
    subject: Text
    auth_time: Count
    issued_at: Count
    expires_at: Count
    verified_at: Count


class LoginTransaction(Message):
    """Current durable snapshot; adapters own locks, unique claims and retention."""

    transaction_id: Identifier
    policy_id: Identifier
    provider_id: Identifier
    browser_binding_sha256: Digest
    return_uri: HttpsURI
    created_at: Count
    expires_at: Count
    revision: Count
    state: LoginState
    proof: TrustedIdentityProof | None
    session_id: Identifier | None

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("Login expiry must follow creation")
        if (self.proof is not None) != (self.state in {"verified", "committed"}):
            raise ValueError("Only verified/committed transactions retain verified evidence")
        if (self.session_id is not None) != (self.state == "committed"):
            raise ValueError("Only committed transaction has a session identity")
        if self.proof and (
            self.proof.transaction_id != self.transaction_id
            or self.proof.provider_id != self.provider_id
            or self.proof.browser_binding_sha256 != self.browser_binding_sha256
        ):
            raise ValueError("Proof belongs to a different login")
        return self


class OIDCCallbackEvidence(Message):
    """Results of actual adapter checks, not client-supplied boolean claims."""

    callback_uri: HttpsURI
    method: Literal["GET"]
    response_mode: Literal["query"]
    state_matches: bool
    nonce_matches: bool
    pkce_s256_verified: bool


class SessionRecord(Message):
    """Current server session family; no opaque cookie secret is stored here."""

    session_id: Identifier
    policy_id: Identifier
    principal_id: Identifier
    generation: Count
    created_at: Count
    authenticated_at: Count
    last_seen_at: Count
    absolute_expires_at: Count
    revoked: bool
    principal_active: bool

    @model_validator(mode="after")
    def validate_times(self) -> Self:
        if not self.created_at <= self.last_seen_at < self.absolute_expires_at:
            raise ValueError("Session activity must fit original lifetime")
        return self


class SessionCredential(Message):
    """Trusted hash lookup result, including narrowly retained logout-only history."""

    session_id: Identifier
    generation: Count


def require_policy(policy: DeploymentSessionPolicy | None) -> DeploymentSessionPolicy:
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    return policy


def server_time(now: int) -> None:
    TypeAdapter(Count).validate_python(now, strict=True)


def provider_for(policy: DeploymentSessionPolicy, provider_id: str) -> ProviderPolicy:
    for provider in policy.providers:
        if provider.provider_id == provider_id:
            return provider
    raise ContractViolation("unsupported_flow", 422)


def browser_request(
    policy: DeploymentSessionPolicy,
    context: BrowserContext,
    *,
    mutation: bool,
    csrf_scope: Literal["preauth", "session"] = "session",
) -> None:
    if context.has_session_cookie and context.has_bearer:
        raise ContractViolation("ambiguous_credentials", 400)
    if context.has_bearer:
        raise ContractViolation("unauthenticated", 401)
    if context.target_origin not in policy.app_origins:
        raise ContractViolation("forbidden", 403)
    if context.origin is not None and context.origin != context.target_origin:
        raise ContractViolation("forbidden", 403)
    if mutation and (
        context.origin != context.target_origin
        or not context.csrf_matches
        or context.csrf_scope != csrf_scope
    ):
        raise ContractViolation("forbidden", 403)


def login_options(policy: DeploymentSessionPolicy | None) -> LoginOptions:
    configured = require_policy(policy)
    return LoginOptions(
        providers=tuple(
            LoginOption(provider_id=p.provider_id, flow=p.flow) for p in configured.providers
        )
    )


def validate_login_start(
    policy: DeploymentSessionPolicy | None,
    request: LoginStartRequest,
    context: BrowserContext,
) -> ProviderPolicy:
    configured = require_policy(policy)
    browser_request(configured, context, mutation=True, csrf_scope="preauth")
    if context.browser_binding_sha256 is None or request.return_uri not in configured.return_uris:
        raise ContractViolation("invalid_request", 422)
    if uri_origin(request.return_uri) != context.target_origin:
        raise ContractViolation("invalid_request", 422)
    provider = provider_for(configured, request.provider_id)
    if provider.callback_uri and uri_origin(provider.callback_uri) != context.target_origin:
        raise ContractViolation("unsupported_flow", 422)
    return provider


def validate_login_binding(
    policy: DeploymentSessionPolicy,
    transaction: LoginTransaction,
    context: BrowserContext,
    *,
    now: int,
    callback: bool = False,
) -> ProviderPolicy:
    server_time(now)
    # The callback has its own state/browser checks, not a generic CSRF exemption.
    if callback:
        if context.has_bearer:
            raise ContractViolation("ambiguous_credentials", 400)
        if context.target_origin not in policy.app_origins:
            raise ContractViolation("forbidden", 403)
    else:
        browser_request(policy, context, mutation=True, csrf_scope="preauth")
    if (
        transaction.policy_id != policy.policy_id
        or transaction.browser_binding_sha256 != context.browser_binding_sha256
        or transaction.return_uri not in policy.return_uris
        or uri_origin(transaction.return_uri) != context.target_origin
        or transaction.expires_at != transaction.created_at + policy.login_ttl_seconds
    ):
        raise ContractViolation("proof_rejected", 401)
    if now < transaction.created_at or now >= transaction.expires_at:
        raise ContractViolation("login_expired", 401)
    return provider_for(policy, transaction.provider_id)


def validate_oidc_callback(
    policy: DeploymentSessionPolicy,
    transaction: LoginTransaction,
    context: BrowserContext,
    evidence: OIDCCallbackEvidence,
    *,
    now: int,
) -> None:
    provider = validate_login_binding(policy, transaction, context, now=now, callback=True)
    if (
        provider.flow != "oidc_code"
        or evidence.callback_uri != provider.callback_uri
        or uri_origin(evidence.callback_uri) != context.target_origin
        or not evidence.state_matches
        or not evidence.nonce_matches
        or not evidence.pkce_s256_verified
        or transaction.state not in {"verifying", "verified"}
    ):
        raise ContractViolation("proof_rejected", 401)


def proof_claim_key(proof: TrustedIdentityProof) -> str:
    """Application-wide unique key; provider/policy aliases must not partition ownership."""
    return proof.proof_sha256


def proof_claim_retain_until(
    policy: DeploymentSessionPolicy,
    transaction: LoginTransaction,
    proof: TrustedIdentityProof,
) -> int:
    """Minimum tombstone deadline, not permission to consume or verify the proof."""
    if (
        transaction.policy_id != policy.policy_id
        or proof.transaction_id != transaction.transaction_id
        or proof.provider_id != transaction.provider_id
    ):
        raise ValueError("Proof retention requires the bound transaction and policy")
    deadline = max(
        proof.expires_at,
        transaction.created_at + policy.transaction_retention_seconds,
    )
    return TypeAdapter(Count).validate_python(deadline, strict=True)


def validate_proof(
    policy: DeploymentSessionPolicy,
    transaction: LoginTransaction,
    proof: TrustedIdentityProof,
    *,
    now: int,
    claimed_by_transaction: str | None,
) -> None:
    """Check verified evidence against the owner loaded by application-wide proof_claim_key.

    The external verifier checks signature/revocation/code exchange. A claim lookup
    partitioned by provider or policy is not a conforming trusted input.
    """
    server_time(now)
    provider = provider_for(policy, transaction.provider_id)
    if (
        transaction.policy_id != policy.policy_id
        or transaction.state not in {"verifying", "verified"}
        or transaction.expires_at != transaction.created_at + policy.login_ttl_seconds
        or now < transaction.created_at
        or now >= transaction.expires_at
        or proof.transaction_id != transaction.transaction_id
        or proof.provider_id != provider.provider_id
        or proof.browser_binding_sha256 != transaction.browser_binding_sha256
        or proof.flow != provider.flow
        or proof.issuer != provider.issuer
        or proof.audience != provider.audience
        or proof.tenant_id != provider.tenant_id
        or claimed_by_transaction not in {None, transaction.transaction_id}
        or (
            transaction.state == "verified" and claimed_by_transaction != transaction.transaction_id
        )
        or (
            provider.flow == "managed_broker"
            and proof.upstream_provider not in provider.upstream_providers
        )
        or (provider.flow == "oidc_code" and proof.upstream_provider is not None)
        or proof.auth_time > proof.issued_at
        or proof.issued_at > proof.verified_at
        or proof.verified_at > now + policy.clock_skew_seconds
        or proof.verified_at < transaction.created_at
        or proof.auth_time > now
        or now >= proof.expires_at
        or proof.verified_at >= proof.expires_at
        or now - proof.auth_time >= policy.recent_auth_seconds
        or (transaction.proof is not None and transaction.proof != proof)
    ):
        raise ContractViolation("proof_rejected", 401)


def validate_login_commit(
    policy: DeploymentSessionPolicy,
    transaction: LoginTransaction,
    context: BrowserContext,
    session: SessionRecord,
    *,
    principal_id: str,
    now: int,
    claimed_by_transaction: str | None,
    oidc_evidence: OIDCCallbackEvidence | None = None,
) -> None:
    """Check the same transaction's atomic proof-consumption/session creation proposal."""
    provider = provider_for(policy, transaction.provider_id)
    validate_login_binding(
        policy, transaction, context, now=now, callback=provider.flow == "oidc_code"
    )
    if transaction.state != "verified" or transaction.proof is None:
        raise ContractViolation("login_conflict", 409)
    validate_proof(
        policy,
        transaction,
        transaction.proof,
        now=now,
        claimed_by_transaction=claimed_by_transaction,
    )
    if provider.flow == "oidc_code":
        if oidc_evidence is None:
            raise ContractViolation("proof_rejected", 401)
        validate_oidc_callback(policy, transaction, context, oidc_evidence, now=now)
    elif oidc_evidence is not None:
        raise ContractViolation("proof_rejected", 401)
    if (
        session.principal_id != principal_id
        or session.policy_id != policy.policy_id
        or session.generation != 0
        or session.created_at != now
        or session.last_seen_at != now
        or session.authenticated_at != transaction.proof.auth_time
        or session.absolute_expires_at != now + policy.absolute_seconds
        or session.revoked
        or not session.principal_active
    ):
        raise ContractViolation("login_conflict", 409)


def validate_login_transition(
    before: LoginTransaction,
    after: LoginTransaction,
    *,
    expected_revision: int,
) -> None:
    """Structural CAS/one-use guard; callers must also validate proof/commit proposals."""
    TypeAdapter(Count).validate_python(expected_revision, strict=True)
    if before.revision != expected_revision or after.revision != before.revision + 1:
        raise ContractViolation("login_conflict", 409)
    edges = {
        "pending": {"verifying", "restart_required"},
        "verifying": {"verified", "restart_required"},
        "verified": {"committed", "restart_required"},
        "committed": set(),
        "restart_required": set(),
    }
    if after.state not in edges[before.state]:
        raise ContractViolation("login_conflict", 409)
    immutable = before.model_dump(exclude={"state", "proof", "session_id", "revision"})
    if after.model_dump(exclude={"state", "proof", "session_id", "revision"}) != immutable:
        raise ContractViolation("login_conflict", 409)
    if after.state == "committed" and after.proof != before.proof:
        raise ContractViolation("login_conflict", 409)


def validate_login_completion(
    policy: DeploymentSessionPolicy,
    before: LoginTransaction,
    after: LoginTransaction,
    context: BrowserContext,
    session: SessionRecord,
    *,
    principal_id: str,
    now: int,
    expected_revision: int,
    claimed_by_transaction: str | None,
    oidc_evidence: OIDCCallbackEvidence | None = None,
) -> None:
    validate_login_commit(
        policy,
        before,
        context,
        session,
        principal_id=principal_id,
        now=now,
        claimed_by_transaction=claimed_by_transaction,
        oidc_evidence=oidc_evidence,
    )
    validate_login_transition(before, after, expected_revision=expected_revision)
    if after.state != "committed" or after.session_id != session.session_id:
        raise ContractViolation("login_conflict", 409)


def login_recovery(
    transaction: LoginTransaction,
) -> Literal[
    "verify_once",
    "reconcile_or_restart",
    "commit_same_transaction",
    "bootstrap_or_login",
    "fresh_login",
]:
    """A status decision does not authorize proof verification or session creation."""
    decisions: dict[
        LoginState,
        Literal[
            "verify_once",
            "reconcile_or_restart",
            "commit_same_transaction",
            "bootstrap_or_login",
            "fresh_login",
        ],
    ] = {
        "pending": "verify_once",
        "verifying": "reconcile_or_restart",
        "verified": "commit_same_transaction",
        "committed": "bootstrap_or_login",
        "restart_required": "fresh_login",
    }
    return decisions[transaction.state]


def login_status(
    policy: DeploymentSessionPolicy | None,
    transaction: LoginTransaction,
    context: BrowserContext,
    *,
    now: int,
) -> LoginStatusResponse:
    configured = require_policy(policy)
    server_time(now)
    browser_request(configured, context, mutation=False)
    if (
        transaction.policy_id != configured.policy_id
        or transaction.browser_binding_sha256 != context.browser_binding_sha256
        or uri_origin(transaction.return_uri) != context.target_origin
        or now < transaction.created_at
        or now >= transaction.created_at + configured.transaction_retention_seconds
    ):
        raise ContractViolation("unauthenticated", 401)
    expired = now >= transaction.expires_at
    action = login_recovery(transaction)
    if expired and transaction.state != "committed":
        action = "fresh_login"
    return LoginStatusResponse(
        transaction_id=transaction.transaction_id,
        state=transaction.state,
        expired=expired,
        next_action=action,
    )


def validate_session(
    policy: DeploymentSessionPolicy,
    record: SessionRecord,
    credential: SessionCredential,
    *,
    now: int,
) -> None:
    server_time(now)
    if (
        record.policy_id != policy.policy_id
        or record.session_id != credential.session_id
        or record.revoked
        or not record.principal_active
        or record.generation != credential.generation
        or record.absolute_expires_at != record.created_at + policy.absolute_seconds
        or now < record.last_seen_at
        or record.authenticated_at > record.created_at
        or now >= min(record.absolute_expires_at, record.last_seen_at + policy.idle_seconds)
    ):
        raise ContractViolation("unauthenticated", 401)


def bootstrap(
    policy: DeploymentSessionPolicy | None,
    record: SessionRecord | None,
    credential: SessionCredential | None,
    context: BrowserContext,
    *,
    now: int,
) -> SessionBootstrap:
    configured = require_policy(policy)
    server_time(now)
    browser_request(configured, context, mutation=False)
    if not context.has_session_cookie or record is None or credential is None:
        return SessionBootstrap(authenticated=False, principal_id=None, session=None)
    try:
        validate_session(configured, record, credential, now=now)
    except ContractViolation:
        return SessionBootstrap(authenticated=False, principal_id=None, session=None)
    return SessionBootstrap(
        authenticated=True,
        principal_id=record.principal_id,
        session=SessionView(
            session_id=record.session_id,
            generation=record.generation,
            authenticated_at=record.authenticated_at,
            idle_expires_at=min(
                record.absolute_expires_at, record.last_seen_at + configured.idle_seconds
            ),
            absolute_expires_at=record.absolute_expires_at,
        ),
    )


def validate_renewal(
    policy: DeploymentSessionPolicy,
    record: SessionRecord,
    credential: SessionCredential,
    request: RenewalRequest,
    context: BrowserContext,
    *,
    now: int,
) -> None:
    browser_request(policy, context, mutation=True)
    if not context.has_session_cookie:
        raise ContractViolation("unauthenticated", 401)
    validate_session(
        policy,
        record,
        SessionCredential(session_id=credential.session_id, generation=record.generation),
        now=now,
    )
    if (
        request.expected_generation != record.generation
        or credential.generation != record.generation
    ):
        raise ContractViolation("session_conflict", 409)
    validate_session(policy, record, credential, now=now)


def validate_session_update(
    policy: DeploymentSessionPolicy,
    before: SessionRecord,
    after: SessionRecord,
    credential: SessionCredential,
    request: RenewalRequest,
    context: BrowserContext,
    *,
    now: int,
) -> None:
    """CAS precondition; actual secret rotation/transaction commit belongs to the adapter."""
    validate_renewal(policy, before, credential, request, context, now=now)
    expected = before.model_dump()
    expected.update(generation=before.generation + 1, last_seen_at=now)
    if after.model_dump() != expected:
        raise ContractViolation("session_conflict", 409)


def validate_logout(
    policy: DeploymentSessionPolicy,
    record: SessionRecord,
    credential: SessionCredential,
    context: BrowserContext,
    *,
    now: int,
) -> None:
    """Only family revocation; historical hash lookup has no ordinary access authority."""
    server_time(now)
    browser_request(policy, context, mutation=True)
    if (
        not context.has_session_cookie
        or record.policy_id != policy.policy_id
        or credential.session_id != record.session_id
        or credential.generation > record.generation
        or now < record.created_at
    ):
        raise ContractViolation("unauthenticated", 401)


SESSION_MODELS: tuple[type[Message], ...] = (
    ProviderPolicy,
    DeploymentSessionPolicy,
    LoginOption,
    LoginOptions,
    LoginStartRequest,
    BrokerExchangeRequest,
    OIDCCallbackRequest,
    OIDCDeniedCallbackRequest,
    LoginStatusResponse,
    LoginStartResponse,
    CSRFResponse,
    SessionView,
    SessionBootstrap,
    RenewalRequest,
    SessionError,
    BrowserContext,
    TrustedIdentityProof,
    LoginTransaction,
    OIDCCallbackEvidence,
    SessionRecord,
    SessionCredential,
)
PUBLIC_MODELS = (
    LoginOption,
    LoginOptions,
    LoginStartRequest,
    BrokerExchangeRequest,
    OIDCCallbackRequest,
    OIDCDeniedCallbackRequest,
    LoginStatusResponse,
    LoginStartResponse,
    CSRFResponse,
    SessionView,
    SessionBootstrap,
    RenewalRequest,
    SessionError,
)


def session_json_schema() -> JsonSchemaValue:
    _, schema = models_json_schema([(model, "validation") for model in SESSION_MODELS])
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://strange-physics.dev/contracts/session.schema.json"
    schema["x-contract-status"] = "session-v1; SP-01.b remains partial"
    schema["x-public-models"] = [model.__name__ for model in PUBLIC_MODELS]
    schema["description"] = (
        "Browser session shapes plus pure conformance checks. Internal trusted projections "
        "must never be populated from public bodies. No verifier, handler or persistence proof."
    )
    return schema
