# Explicit identity linking contract — ID-B/B3

This increment defines a separate identity-association journey, strict public
shapes and pure conformance predicates. It implements no provider verification,
broker configuration, HTTP endpoint, SQL transaction, account mutation, recovery
worker or production deployment. SP-01.b remains partial until its remaining
credential and integration contracts are reviewed.

[Schema](../contracts/linking.schema.json),
[HTTP subset](../contracts/linking.openapi.json),
[synthetic fixtures](../contracts/linking.examples.json) and
[conformance code](../src/strange_physics/linking_contracts.py) are reviewed together.
Existing session, workspace and invitation positive journeys remain supported.

## Reviewed internal producer amendment

B3 amends the internal ID-A trusted producer interface before the parent contract
freeze. TrustedIdentityProof now requires purpose, exactly login or link_identity.
ProofClaimOwner contains that purpose and transaction_id. The pure login
validators take claimed_by: ProofClaimOwner | None instead of the previous
claimed_by_transaction string. Old trusted producers must migrate explicitly;
there is no default or compatibility coercion that erases purpose.

The public login HTTP request/response shapes and session.openapi.json remain
unchanged. Session fixtures and generated schema include the explicit new fields.
This is not a declaration that any running producer has been upgraded.

The application's one proof-claim registry is keyed **only by SHA-256 of the
actual proof bytes**. Purpose and transaction ID are the owner VALUE, never an
additional key dimension. Login and linking, all provider aliases, policy
versions and tenants share this registry. Equal login and link IDs therefore
have different owners and cannot consume the same proof. Within each purpose,
transaction IDs are globally unique across provider/policy aliases; ID allocation
and row uniqueness cannot be partitioned by provider. A verifier must not relabel
a previously seen token into a new unclaimed digest or manufacture the digest
from redacted serialization, identity claims or request metadata.

A trusted purpose is derived from the server-owned challenge and authenticated
adapter entry point, never copied from an upstream token's arbitrary claim or a
public body. Token signature, audience, issuer, tenant, revocation, state/nonce,
S256 code exchange and actual proof-byte digest remain verifier obligations.
Parsing these models does not establish any of those facts.

## Identity and primary authority

Identity ownership uses the exact tuple **canonical issuer, verified tenant ID
or explicit null, subject**. The issuer is the exact configured canonical HTTPS
issuer, including its meaningful path. No provider alias, audience, email,
display name, email normalization or domain enters this ownership key. Null is
a namespace value, not a wildcard or missing tenant claim. Tenant derivation must
come from verified evidence and approved provider policy.

LinkActor is a private, current server projection:

- A valid human BrowserActor session and exact current credential generation.
- Independently current active human PrincipalStatus.
- The current active primary IdentityAssociation owned by that same app principal.
- SessionIdentity provenance recording which identity actually authenticated the
  current session family/generation and its original authenticated_at.

An arbitrary identity associated with the principal cannot replace the actual
session-authenticating identity. Renewal cannot update that provenance or the
authentication time. The challenge fixes the primary identity/revision, stable
principal, session family/generation/authenticated_at, browser binding, provider,
session and link policies, expiry, purpose and revision. Session rotation,
mapping changes, policy changes, principal disablement or loss of primary
ownership fences the challenge and its receipts. Start a fresh challenge after
proper reauthentication; do not transfer one to a different session.

Every operation, status read and receipt replay rechecks current authority and
primary mapping before returning an outcome. Primary authentication must remain
strictly younger than recent_auth_seconds. Exact Origin and session CSRF are
required on POSTs; mixed cookie/bearer and bearer-only callers are rejected.
Missing approved policies fail closed. These are server checks, not client form
fields. The existing ID-A no-store, log suppression and browser security rules
apply to all successes and errors.

## Independently fresh secondary authentication

Start creates a pending challenge without looking up or allocating a secondary
app principal. The adapter requests actual secondary reauthentication. Merely
refreshing an ID token or observing a recent issued_at/verified_at is insufficient.

All timestamps are integer UTC seconds. The verified secondary auth_time must be
**strictly greater than challenge.created_at**, no later than server now, and
strictly younger than recent_auth_seconds. Equality fails conservatively: a
real authentication within the same timestamp second may require another fresh
authentication attempt after that boundary. No clock-skew allowance advances
auth_time or supplies freshness. The configured skew applies only to the
verifier's timestamp comparison. A provider that cannot reliably attest actual
authentication time and bind the secondary attempt to this challenge is
unsupported; local parsing cannot supply missing evidence.

The proof must be for a different IdentityNamespace from the primary and match
purpose, challenge ID, browser digest, configured provider, flow, canonical issuer,
audience, explicit tenant and allowed upstream provider. The adapter independently
checks the secondary proof and its fresh-auth challenge; primary session authority
is not secondary identity proof.

Managed broker exchange is a session-CSRF POST. OIDC uses a distinct approved
link callback URI, never the login completion callback, and GET/query
code/state or error/state only. Current primary session/browser and purpose-bound
state must be verified **before code exchange**. Exact callback, nonce and PKCE
S256 checks remain mandatory. Callback evidence may stage verification only;
association always requires a separate session-CSRF commit. Provider denial
returns a fixed safe error after state validation, never an association.

## State, claim reservation and atomic association

The normal sequence is pending -> verifying -> verified -> committed.
Every transition uses revision compare-and-swap; challenge identity is immutable.
Pending can become restart_required before external work begins. Once exchange
begins, an unknown or negative result enters recovery_required unless a complete
verified result was durably recovered. The pure API has no transition out of
recovery_required and does not implement reconciliation.

1. Authorize the primary and claim the challenge's pending revision for verification.
   Persist the one-use adapter state, intent and verifier attempt before exchange.
2. Verify once. In one transaction, reserve the global actual-proof-digest claim
   for the exact typed owner and store the verified evidence plus verified challenge.
   A different owner conflicts even when its ID or provider alias matches. A
   verified challenge without its owned durable claim cannot advance.
3. For commit, recheck current primary session, policy, identity mapping and
   freshness; validate the retained proof and global ownership. Read the secondary
   IdentityNamespace in the authoritative ownership index under the same
   serialization protocol. The proof is verified evidence, not a login request.
4. A previously unbound identity may be associated to the existing stable human
   principal. Any existing association, including inactive ownership or ownership
   by the same principal through another operation, returns the same safe conflict.
   No foreign principal ID, account, email, grant or membership detail is returned.
5. Atomically insert the association, retain/consume the global proof claim,
   consume the exact challenge revision, store the exact receipt and append the
   audit event. validate_link_commit requires all corresponding output projections.
   There is no success between these writes.

The existing reserved claim remains exclusively owned while the association
transaction writes its consumed tombstone. Reservation and consumption are phases
of the same global registry, not independent login and linking stores. The
tombstone/receipt deadline is at least the maximum of proof expiry, challenge
creation plus session transaction retention, and challenge creation plus link
receipt retention. Garbage collection must not make a consumed proof usable
again. Purging evidence and preserving a minimal replay tombstone are separate
retention decisions.

The SQL producer must enforce unique IdentityNamespace ownership, global
purpose/transaction uniqueness, global proof digest uniqueness and challenge
revision CAS under one lock order or serializable conflict/retry protocol.
Primary disablement, identity mapping changes and proof claim changes share the
commit serialization boundary. None of this is proven by pure predicate tests.

LinkChallenge ID is the commit's natural idempotency key; expected_revision is
the original verified revision. An exact committed retry rechecks current
authority, original primary mapping, resulting active secondary association,
global consumed claim and retained receipt. It never calls a verifier, reclaims
proof, reapplies association or extends retention. An altered revision, changed
mapping, absent receipt/claim or partial result cannot return success. A revoked
or rotated session cannot retrieve the receipt. Status is safe metadata only;
a producer may expose committed/done only from the atomic durable commit record,
never from an optimistic broker/UI state.

## Recovery and broker divergence

A crash before durable verified evidence does not authorize repeating a one-use
code exchange. Reconcile the stored verifier attempt and global claim through
trusted evidence; when outcome is unknown, keep recovery_required. An unknown
application commit is resolved only by reading the durable challenge, namespace
association, global consumed claim, exact receipt and audit together. A missing
member of that atomic set is an incident/recovery state, not successful linking.

Normal B3 never calls a broker account-link/merge API. If a broker unexpectedly
merges identities, changes the canonical subject, or reports success while
application commit fails, quarantine that challenge in recovery_required and
block automatic association. Do not infer success from email or mint another
principal/session to “finish” the flow. Corrective broker reconciliation is a
separately reviewed trusted procedure with its own audit and evidence; no public
force, merge, union, unlink or recovery override is provided here.

Provider conformance must establish that distinct external identities stay
distinct before app-controlled association. Google documents that
[Identity Platform tenants cannot disable account linking](https://docs.cloud.google.com/identity-platform/docs/multi-tenancy).
Consequently the managed-broker tenant profile is explicitly rejected by B3;
there is no enablement boolean. The existing ID-A shape can describe a tenant,
but its deployment remains blocked until an actual reviewed broker profile can
meet the isolation requirement. Top-level separate-provider-account
[configuration](https://docs.cloud.google.com/identity-platform/docs/link-accounts)
also requires live conformance evidence. Google documents
[automatic linking behavior](https://docs.cloud.google.com/identity-platform/docs/concepts-manage-users)
and [tenant-specific linking/reauthentication routing](https://docs.cloud.google.com/identity-platform/docs/multi-tenancy-authentication);
setting a client tenant value alone is not proof of safe separation.

## Public boundary and producer exit evidence

The five candidate paths are challenge creation, challenge status, managed proof
exchange, separate association commit and dedicated OIDC callback. Public bodies
never accept principal IDs, identity ownership snapshots, trusted proof purpose,
proof claims, grants, audit facts or reconciliation authority. Errors are fixed
LinkError codes plus request correlation ID; adapters suppress raw validation and
provider details. Ownership conflict is generic link_conflict/409. Stale actual
primary authentication uses reauthentication_required/401 plus the established
X-Authentication-Action: reauthenticate header. Invalid/revoked sessions do not
receive that freshness header. Rate limits are server producer obligations,
including bounded attempts and challenge retention; no limiter is implemented.

Required later evidence includes real cryptographic verifier negative cases,
forced secondary authentication/precision behavior, broker alias/tenant isolation,
concurrent proof reservations across login/link, equal-ID and namespace races,
revocation/rotation during commit, durable atomicity, crash points before/after
exchange and commit, receipt reconciliation, retention cleanup and sensitive-log
canaries. Synthetic parsing, pure transitions and static checks are insufficient
to approve a hosted deployment.

Product streams remain governed by current authoritative authorization: immediately
before **every payload batch**, reload/check the current session or credential,
current grant and workspace state (and applicable run lease). At most 30 seconds
between idle checks bounds detection while no payload is sent; it is never a
cached authorization grace period. Close on revocation, policy/authority
uncertainty or failed reauthorization without delivering another payload.
