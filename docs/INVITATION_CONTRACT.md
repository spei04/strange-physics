# Invitations — ID-B/B2

This contract adds issuance, owner-visible listing, revocation and authenticated
redemption to the B1 human workspace model. Source predicates, JSON Schema,
synthetic fixtures and HTTP definitions are conformance artifacts. They do not
verify providers, generate secure randomness, deliver email, implement HTTP/SQL
handlers, enforce distributed throttling or demonstrate production security.

B3 explicit identity linking and ID-C credential lifecycle remain separate reviews.
SP-01.b and its full C-ID dependency gate remain unfinished. SP-08.b/SP-08.d and
their database/security dependencies must implement these interfaces and supply
integration evidence. No invitation operation links or merges identities.

## Public surface and authority

| Route | Authority | Result |
| --- | --- | --- |
| POST /v1/workspaces/{workspace_id}/invitations | Current recent human owner | Fresh 201 InvitationIssued; exact retry 200 InvitationView without token |
| GET /v1/workspaces/{workspace_id}/invitations | Current human owner | Bounded owner-visible metadata page |
| POST /v1/workspaces/{workspace_id}/invitations/{invitation_id}/revoke | Current recent human owner | Revoked metadata, or safe conflict if acceptance already won |
| POST /v1/invitations/redeem | Current recent human recipient plus independently verified eligibility | Current resulting membership; never an implicit role change |

Mutations use the existing ID-A recent actual authentication policy, exact Origin,
session CSRF and Idempotency-Key. Renewal/last_seen is not fresh authentication.
No bearer-only or mixed credential administration is accepted. The B1
management_session_error mapping applies, including its explicit freshness header.
Listing requires current authorization without an extra freshness challenge.
Workspace quarantine/effective ownerlessness blocks invitation administration and
redemption through the same current owner eligibility rules as B1.

Owner-only metadata includes canonical recipient email, role, inviter app ID,
expiry, state, revision and accepted principal when applicable. It excludes token,
token digest, issuing membership revision and provider identities. Cursors bind
caller, workspace, filter/order, snapshot and expiry; each page reauthorizes the
current owner. They never confer authority.

Authenticate before tenant visibility, then current authority and request scope.
Redemption has a separate possession/recipient authorization path: unknown token,
wrong token, wrong recipient, unavailable inviter grant, expired pending grant and
revocation produce the same fixed 404 Error without disclosing recipient, tenant,
provider or account details. Owner listing is not a token-probing endpoint.
The handler must normalize response shape and avoid existence-dependent side
channels. Schema-invalid requests receive safe generic input errors, never a
dump of the request, token, provider assertion or validation context.

## Secret and URL contract

The issuer generates 32 independent CSPRNG bytes and encodes exactly 43 canonical
unpadded base64url characters. Validate exact alphabet/length/unused final bits,
strictly decode, and re-encode to the identical text before establishing token
identity. Synthetic public fixtures demonstrate encoding, not entropy.

Store only SHA-256 of the byte concatenation of the ASCII domain separator
strange-physics.invitation-token.v1, one NUL byte, and the decoded 32 token bytes.
Token-digest uniqueness and atomic invitation allocation are storage obligations.
Lookup/verification uses the derived digest and a constant-time comparison.
High-entropy token possession is required but is not sufficient for membership.

A fresh committed issuance attempts a 201 response containing ResponseSecret
plaintext token and safe invitation metadata. Runtime repr/default serialization
redacts the secret; the HTTP serializer must intentionally extract it only for
that initial authorized response. Response JSON Schema marks it readOnly rather
than incorrectly writeOnly. Redemption request Schema marks it writeOnly.
All other responses, receipts, audit events and default serializers omit plaintext.

There is no exactly-once client delivery claim. A crash or network loss after
commit can lose the only plaintext response. An idempotent retry returns current
metadata only, even if the original response never reached the client or the
invitation has since expired/been accepted. This is an explicit exception to
byte-for-byte response replay. No stored response body, resend or secret recovery
mechanism is introduced.

No token URL is emitted. Tokens are submitted only in the HTTPS POST JSON body:
never query, path, redirect, referrer, analytics, telemetry or logs. No token-bearing
GET route exists. WEB share-link behavior needs a separate reviewed contract; B2
does not invent a browser route. Apply ID-A no-store/cookie/CSRF rules and
Referrer-Policy: no-referrer. Redact recipient email in routine telemetry as well.
Input/error pipelines must suppress validation input and context values; the
secret-bearing models hide input in exception text, but adapters still must not
log raw request bodies or errors(include_input=True).

Lost-token recovery: an authorized owner obtains metadata by same-key retry or
listing, revokes the old pending invitation, then issues a new invitation with a
new key. Do not create an overlapping pending grant to bypass recovery. If
acceptance won the race, revocation returns a safe conflict/current metadata can
show acceptance; never silently remove the resulting membership. A later member
removal is a separate B1 operation with its own authority and last-owner checks.

## Recipient email is eligibility, not identity

The supported profile is ASCII dot-atom local part and DNS-style domain labels.
Preserve local-part case, dots and plus suffixes exactly; lowercase only the ASCII
domain. Do not trim whitespace, infer a domain-wide grant, remove dots/plus tags,
case-fold local parts, decode Unicode/IDNA, accept quoted local forms or guess
unsupported equivalents. Local part is at most 64 characters, labels at most 63
and address at most 254. Unsupported input fails closed.

VerifiedEmailAssertion must come from the approved provider adapter's cryptographic
verification and explicit verified-email semantics. Its issuer, audience, tenant
(including null) and permitted upstream provider are checked against ID-A policy.
CurrentRecipientIdentity independently binds issuer + tenant + subject/provider
to the stable human app principal and its current session/generation. Its
identity mapping and principal must still be active, including B1's unsettled
security-event fence. Neither body fields nor model construction prove these facts.

The upstream assertion's issued_at establishes claim age; expires_at is upstream
expiry. verified_at is local verification time and never refreshes old claims.
For this bounded profile, future-issued/future-verified claims fail closed;
issued_at <= verified_at <= server now < expires_at, and
now - issued_at < the configured assertion maximum age. Equality expires.
Recipient actual authentication must independently satisfy ID-A freshness.
A newly parsed stale assertion and an old login transaction cannot become a grant.

Missing, private/unavailable or unverified Google/GitHub broker email cannot redeem.
Raw GitHub profile data is not an app identity proof or verified-email assertion.
The adapter must verify issuer/audience/tenant/upstream claims, provider keys,
revocation and current mapping; these predicates do not perform that verification.
No email challenge delivery or provider API is implemented here. Email determines
eligibility for this invitation only; it never creates, chooses or merges an app
principal. Two separately authenticated principals eligible for the same email
still compete for one single-use token; the first atomic winner is bound by ID.

## Immutable grant and terminal state

Issuance fixes policy ID, workspace, inviter principal, issuing inviter membership
revision, canonical recipient email, role, creation time, expiry and token digest.
No public body selects inviter, digest, token, approval or expiry. Policy versions
are immutable and must remain resolvable for supported grants; a policy update
cannot extend an already-issued expiry. Missing required policy fails closed.

Redemption rechecks the inviter's current enabled human owner membership and exact
issuing membership revision. The inviter need not be online. Any change to that
owner grant requires a new invitation; demoting and later restoring the same
principal cannot revive an old token. Global disable/fan-out/reactivation retains
the B1 durable security-fence ordering. Current eligibility is checked again on
accepted receipt retries; loss of inviter authority denies replay without undoing
a previously committed membership.

Pending transitions exactly once to accepted or revoked. The workspace owner lock,
invitation revision/CAS and current inviter/recipient records serialize consume
versus revoke, concurrent redeemers and principal/owner changes. Acceptance before
expiry binds the recipient's stable principal. Accepted invitations cannot be
revoked; revoked invitations cannot be accepted.

For a new human member, atomically consume the invitation, create the invited-role
membership at revision 0, update the shared workspace revision/complete human
owner set when applicable, and commit receipt plus audit/outbox. Existing active
membership keeps its actual role/revision unchanged, regardless of invited role.
Inactive/revoked membership fails closed rather than being resurrected by a token.
Explicit readmission is outside B2. Receipt retries return the current active
membership, so they cannot advertise or recreate an old elevated role.

## Idempotency, expiry and policy boundaries

Issuance lookup scope is caller + operation + workspace + key; revocation also
includes invitation ID. Redemption lookup is caller + redeem + key, not partitioned
by a caller-selected token/workspace/target. Its stored identity additionally
binds resulting workspace/invitation and the explicit token-specific request digest.
A different valid token with the same caller redemption key conflicts.

Do not use normal message_sha256 on a secret-bearing redemption body: SecretStr
serializes to a shared mask. redemption_request_sha256 hashes UTF-8 bytes of the
existing SCI Python canonical JSON codec applied to an object with token_sha256
containing the domain-separated decoded-token digest. No raw token is stored in
that canonical request identity.

Every redemption retry rechecks current session, freshness, recipient mapping/email eligibility,
inviter grant and workspace state before receipt lookup/response. It also requires
current recipient membership for an already-accepted result. Do not reapply the
original mutation revision after an exact receipt has been found. A removed member
cannot replay an old receipt to recreate membership. Changed request identity
conflicts; corrupted/out-of-scope records fail closed.

Pending admission expires at expires_at. An accepted token can only retrieve a
same-key safe result within resolved_at + retry_window_seconds; equality fails.
This bounded receipt retry may extend past pending-token expiry, but never creates
or changes membership and still requires all current authority. Receipt retention
covers at least token lifetime plus retry window. Retain safe key tombstones so
an expired/retired request is not silently treated as a fresh issuance/redemption;
actual retention/deletion enforcement requires the later storage contract.

InvitationPolicy explicitly requires token lifetime, assertion maximum age,
retry/receipt retention, pending capacity, create/redeem attempt limits and attempt
window. No production values are defaulted; SP-02.c deployment approval supplies
them. At most one unexpired pending invitation exists per workspace + canonical
recipient; capacity counts all unexpired pending grants under the workspace lock.

Pending capacity is not request-rate limiting. Future ingress/adapters must enforce
the configured create/redeem limits across retries, changed keys, invalid tokens
and invalid requests, with authenticated caller/workspace and unauthenticated
network-abuse bounds. Use a generic 429 temporarily_unavailable Error and bounded
Retry-After without existence-dependent detail. Distributed limiter atomicity,
counter storage/privacy and failure behavior require implementation evidence;
these pure predicates and numeric policy fields do not enforce it.

## Required implementation evidence

The transaction must re-read current sessions, identity/principal state, issuer
grant, complete human owner sets and target membership in a coherent snapshot;
revalidate authority at commit under B1's lock order/serialization domain. Commit
grant transition, membership, workspace revision, receipt and audit/outbox together.
Unique token digests, scoped keys, membership identity and one pending recipient
grant need real storage enforcement; partial HTTP success is prohibited.

Integration tests must demonstrate concurrent redeemers, consume/revoke/expiry,
inviter demotion→restoration, global-disable settlement, role changes and principal
mapping revocation races. Inject crashes before/after commit and before secret
response serialization; prove no token replay, duplicate membership or lost
revocation. Exercise unsupported/unverified provider email, cross-tenant mappings,
safe errors/logging, current authorization on cached responses, distributed rate
limits and receipt/tombstone expiry. Synthetic source/schema tests are not proof
of cryptographic verification, entropy, SQL isolation or production readiness.
