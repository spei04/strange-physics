# Browser sessions and bootstrap contract v1

SP-01.b / ID-A / issue #57. This freezes the browser-session subset alongside
the [first control subset](IDENTITY_RUN_CONTRACT.md). ID-B (workspaces, membership,
invitations, explicit identity linking) and ID-C (service/run credential lifecycle)
remain unfinished. The full parent and its downstream implementation gates stay
open; this is not a hosted authentication service or production-readiness claim.

[Schema](../contracts/session.schema.json), [HTTP subset](../contracts/session.openapi.json),
[synthetic fixtures](../contracts/session.examples.json) and
[pure predicates](../src/strange_physics/session_contracts.py) describe the interface.
The fixtures use invented origins, times, digests and credentials. Their lifetime
values are not deployment recommendations or approval.

## Trust boundary and required policy

Public request bodies contain only the named public fields. They cannot supply
BrowserContext, TrustedIdentityProof, LoginTransaction, SessionRecord or
SessionCredential. Those are internal snapshots from a trusted adapter/current
transaction. A successful pure predicate does not prove signature validation,
browser possession, token revocation, SQL atomicity, random-secret generation,
cookie delivery, or concurrent safety. Implementations must establish each input.

DeploymentSessionPolicy is required before any authentication route operates.
Missing policy returns 503 policy_unavailable, never permissive defaults.
Each policy_id identifies one immutable version; reusing it for changed values
is forbidden. Deployments must retain the policy needed by live records or
invalidate those records explicitly on policy replacement.

| Required input | Meaning |
| --- | --- |
| app_origins | Exact canonical HTTPS origins, no path/trailing slash |
| return_uris | Exact approved HTTPS return locations on those origins |
| providers | Unique IDs, flow, issuer, audience, explicit tenant or null; adapter-specific profile |
| idle_seconds / absolute_seconds | Server-enforced idle and original absolute session limits |
| recent_auth_seconds | Maximum age of actual authentication for establishing a session |
| login_ttl_seconds | Eligibility window for the one-use login transaction |
| clock_skew_seconds | Explicit tolerated verifier clock skew, bounded by the contract |
| transaction_retention_seconds | Outcome/proof-binding reconciliation window, at least login TTL |

Origins/URIs use exact comparison, without wildcard, suffix, query, percent
decoding, dot-segment normalization, credentials, fragment or implicit localhost
exception. Ports are canonical and default 443 is omitted. Return locations
belong to the request's trusted target origin. An approved origin on another
host is not same-origin authority for this request. The adapter must derive the
target from trusted deployment/proxy configuration, not unchecked Host or
forwarded headers. Concrete production inputs remain the SP-02.c deployment
decision; no values have been configured here.

Managed hosted sign-in uses Google Identity Platform for Google/GitHub.
Its issuer is https://securetoken.google.com/{project-id}, audience is that
project, and tenant equality is checked when configured (including explicit
absence when null). Only approved upstream provider identities are accepted.
Raw GitHub OAuth access tokens, login names, profile email and domains are not
application identities.

Self-hosted OIDC is a separate authorization-code adapter. It validates the
configured issuer/audience/tenant, signature/key/algorithm, expiry, nonce and
PKCE S256, with exact redirect matching. Only GET callback with query response
mode is supported initially. Its __Host-sp_login browser-binding cookie uses
SameSite=Lax so it can accompany that top-level callback; form_post/cross-site
POST requires a separately reviewed profile and is rejected here. Validate
state, browser binding and callback identity before exchanging a code; validate
nonce/PKCE/claims before persisting verified evidence. Do not exchange a code
just because a later pure predicate could reject it.

Managed broker SDK callback checks happen inside the configured broker flow.
The app's later same-origin proof exchange validates preauth CSRF/browser binding,
fresh verified broker claims and exclusive proof ownership. It does not pretend
the broker token contains the app's nonce. Broker persistence should be disabled
or cleared after exchange as appropriate to the supported SDK flow.

Configure the broker to create separate accounts for different providers,
with explicit application linking only. Automatic email-based merge can
undermine the application's stable principal boundary. This is a deployment
conformance obligation, not a provider setting changed by this PR.

## Public routes and HTTP rules

All responses, including failures, carry Cache-Control: no-store,
Pragma: no-cache, Referrer-Policy: no-referrer and
Cross-Origin-Resource-Policy: same-origin. Exclude authentication responses from
shared/CDN/service-worker caching. No credentialed cross-origin CORS or reflected
Origin. Never log bodies/tokens/CSRF/cookies, authorization headers, callback
queries, authorization URLs, or Set-Cookie. Redact at ingress as well as in
application logs. Auth protocol code/state query values are the narrowly
specified callback mechanism; never put app session or CSRF credentials in URLs.

| Route | Behavior |
| --- | --- |
| GET /v1/auth/policy | Safe provider ID/flow choices; no internal configuration |
| GET /v1/auth/csrf?scope=preauth or session | Issue opaque synchronizer token for a browser binding or current session family |
| POST /v1/auth/login | Start one bound transaction; return broker guidance or adapter-generated OIDC authorization URL |
| POST /v1/auth/broker/exchange | Verify configured broker proof and commit this transaction's session |
| GET /v1/auth/oidc/callback | code/state or error/state, never both; safe denial after state validation |
| GET /v1/auth/logins/{transaction_id} | Browser-bound safe outcome/action; no identity or proof data |
| GET /v1/auth/session | Current safe bootstrap, or signed-out projection for invalid/missing cookie |
| POST /v1/auth/session/renew | CAS rotation of current session secret/generation |
| POST /v1/auth/session/logout | Revoke this session family; return signed-out projection |

Every cookie mutation, including renewal and logout, requires exact Origin
equal to trusted target_origin and a constant-time comparison against the
correct preauth/session synchronizer token. Missing/null/mismatched Origin,
missing/wrong CSRF, or wrong CSRF scope fails closed. The callback's bound
GET/query state/nonce/PKCE protocol is its explicit alternative; it is not a
blanket exception. Public GET responses remain protected by same-origin browser
policy and the response headers above.

Reject simultaneous app cookie and Authorization bearer before choosing a
credential. Auth routes accept no bearer alternative. Existing workspace routes
now describe cookie authentication as an alternative to workspaceBearer; cookie
mutations additionally need CSRF/Origin. Run-worker routes remain runBearer only.
An app session does not grant workspace scope: derive the user principal, then
apply the existing current membership/scope predicate inside each write/retry.
No truth visibility, role, membership or export grant is added by bootstrap.

Cookies are opaque CSPRNG-generated secrets (at least 256 bits), stored as
one-way keyed hashes in the eventual session store, not plaintext. The cookie is
__Host-sp_session with Secure, HttpOnly, Path=/, SameSite=Lax and no Domain.
The separate __Host-sp_login binding uses the same attributes. Its lifetime is
bounded by the transaction's eligibility/reconciliation policy; it grants no
application session. Max-Age never exceeds remaining server authority.
Session identifiers/generations in JSON are public references, not cookie
secrets. Public SessionBootstrap exposes only authenticated, stable principal ID
and SessionView. Workspace/member information belongs to ID-B.

CSRF/proof/callback fields use SecretStr for safe default representations and
JSON dumps. A real HTTP adapter must explicitly extract secret values into the
intended protected response only; default redacted model dumps are not usable
credentials. Never use a masked request dump as an idempotency or proof digest.
proof_sha256 hashes the actual verified ID-token bytes in the trusted verifier;
the adapter binds its issuer/provider and unique claim to the transaction.
No raw code, ID/access/refresh token or opaque session secret belongs in durable
proof metadata, public status or logs.

## One-use login and durable recovery

The adapter generates a high-entropy browser binding, state, nonce and PKCE
verifier where applicable. Keep short-lived verifier material privately encrypted
or in a protected server store; delete when no longer eligible. Before any
provider exchange, reserve the pending transaction by revision CAS. The
transaction binds provider, exact return URI, immutable policy version, browser
binding digest and server creation/expiry.

Minimal TrustedIdentityProof retains issuer, subject, audience, tenant, approved
upstream provider, actual auth_time, iat, exp, verification time, proof digest and
transaction/browser binding. Verifiers check signature, algorithm, issuer keys,
revocation and all protocol claims outside these predicates. auth_time measures
authentication; a recently refreshed iat cannot make old authentication fresh.\nActual auth_time cannot be later than server commit time; the configured skew\napplies to verifier timing and never creates future authentication authority.
The proof alone does not create a principal. Resolve stable identity ownership
separately under the later identity mapping contract; email never merges it.

| Durable state | Permitted recovery |
| --- | --- |
| pending | CAS to verifying, then perform the one permitted proof exchange |
| verifying | Reconcile prior exchange; if verified evidence cannot be recovered, fresh login |
| verified | Recheck current policy/expiry/revocation and commit only this transaction |
| committed | Reconcile via bootstrap if the cookie arrived; otherwise fresh login |
| restart_required | Fresh transaction and proof only |

validate_login_transition checks structural CAS and allowed edges.
validate_login_binding checks current browser/policy/expiry.
validate_proof checks the externally verified claim bindings and exclusive proof
ownership. An adapter accepting OIDC also requires validate_oidc_callback.
validate_login_completion combines the completion checks, binds the resulting
session ID and preserves the proof. None of these functions performs I/O.

Proof ownership must be unique across transactions under the same provider.
Persist the minimal verified projection and ownership before attempting session
commit. Commit the transaction's consumed state, unique session and audit event
atomically. Reserve/check current principal authority and stable identity mapping
in that transaction; revoked principals cannot create sessions. Check revision,
proof identity and remaining validity again after waits. New sessions start at
generation zero with last_seen_at = created_at = server commit time, auth_time
from the proof, and original absolute deadline from the pinned policy.

If the broker exchanged a code but persistence failed or its outcome is unknown,
never retry the consumed code as a new operation. A durable verified projection
can finish the same transaction while still eligible. If the projection was lost,
mark restart_required after reconciliation and require new authentication.
No proof is inferred from a provider error, an orphaned callback or browser state.

A response timeout after session commit is not proof that the cookie was absent.
GET session first reconciles a delivered cookie; the outcome route returns only
the safe transaction status. If no new cookie arrived, fresh login is required.
There is no replay endpoint that reissues a committed secret or creates a second
session from consumed proof. A committed record never transitions back.
After the configured reconciliation retention, delete minimal proof claims;
keep only required nonsecret audit/dedup tombstones under the later retention
policy. A purged transaction is never eligible again.

## Renewal, logout and safe failures

Every authenticated request checks current family/principal revocation,
generation, policy, idle and original absolute expiry. At a deadline equality
the session is expired. Adapters update activity under the same current-family
transaction and cannot use an old request to revive an expired session.
A policy change never silently extends a family.

Renewal compares the client expected generation and trusted cookie generation
to the current record by CAS. Only the winner rotates the opaque secret and
increments generation once; it updates last_seen_at but preserves principal,
original creation/absolute deadline and authenticated_at. A loser gets
session_conflict without a replacement cookie. Revocation is checked before
returning conflict. Renewal is not reauthentication and cannot reset auth_time.
If the winning cookie was lost, bootstrap then fresh login resolves it.

Logout revokes the whole family, including any concurrent rotation winner.
A trusted retained prior-generation hash lookup may revoke only its own family
with valid family-bound CSRF and exact Origin; it is never a grace credential for
other access. Keep that historical lookup only under the approved reconciliation
retention and destroy it afterward. Security revocation must fence renewal and
other writes transactionally; SQL concurrency evidence remains future work.

Logout, denied, stale and bootstrap responses never emit cookie deletion.
An HTTP Set-Cookie deletion cannot compare with a newer browser cookie when a
delayed response arrives. Server revocation supplies logout; an invalid cookie
may remain until expiry or fresh login overwrites it. The UI clears private
state and displays signed out. Fresh login/preauth issuance works with an
invalid old cookie. Out-of-order successful rotation/login responses may force
reauthentication but cannot restore revoked server authority.

Errors expose only a fixed machine code and request correlation ID.
400 covers malformed/ambiguous credentials; 401 rejected/expired identity;
403 Origin/CSRF/current-authority denial; 409 CAS/consumption/reconciliation
conflict; 422 unsupported/invalid input; 503 missing policy or unavailable
dependency. No provider body, account existence, foreign workspace metadata or
proof content is returned. On an unavailable/unknown outcome, reconcile rather
than assuming failure or automatically replaying a mutation.

## Validation and remaining evidence

The tests cover required policy, exact origins/returns/callbacks, trusted/public
shape separation, secret redaction, issuer/audience/tenant/provider/browser
bindings, proof replay/expiry, auth_time versus iat, CSRF and credential ambiguity,
one-use completion, partial-persistence/lost-response decisions, deadlines,
revocation, generation CAS and logout-only history. Published schema fixture
checks run independently of Pydantic. Custom semantic/cross-message rejections
are explicitly separated from structural JSON Schema negatives.

Actual signature/JWKS/algorithm/revocation checks, secure cookie/CSRF issuance,
broker integration, real HTTP/CORS/cache behavior, SQL unique constraints and
concurrent races, operational policy approval and browser evidence belong to
SP-08/09/11 and client integration work. A passing pure predicate or schema is
not evidence those systems exist.

Primary references:
[Identity Platform GitHub sign-in](https://docs.cloud.google.com/identity-platform/docs/web/github),
[provider account linking modes](https://docs.cloud.google.com/identity-platform/docs/link-accounts),
[ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens),
[server session exchange](https://firebase.google.com/docs/auth/admin/manage-cookies),
[OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html),
[OAuth security BCP](https://www.rfc-editor.org/rfc/rfc9700.html),
[OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
and [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
Opaque app sessions and the conservative lost-cookie behavior are project
choices, not claims that the providers mandate this implementation.
