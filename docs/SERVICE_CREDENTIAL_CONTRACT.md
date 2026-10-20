# Service principal and API-key contracts — ID-C/C1

Status: lifecycle conformance review checkpoint. Pure admission/replay proposals
and adversarial tests are implemented; these interfaces are not a hosted
issuer, HTTP service, verifier or SQL implementation. ID-C/C2 run credentials
and full C-ID producer/consumer acceptance remain separate gates.

The additive [schema](../contracts/service.schema.json),
[route contract](../contracts/service.openapi.json), and
[synthetic vectors](../contracts/service.examples.json) leave the accepted
session and membership public messages unchanged. The vectors contain invented
tokens and identities only.

## Ownership and scope

A current human workspace owner manages an independently granted service
principal. Service grants are researcher or viewer, never owner; supported
service permissions are runs:read, runs:create and runs:cancel. Viewer scope is
runs:read only. No owner administration or worker authority is expressible.
Creation makes the principal and grant without issuing a key. C1 does not add
grant editing/deletion, a real bearer verifier, run issuance or deployment.

Every management read, mutation and exact retry requires current human session,
principal generation, grant, enabled ownership and workspace checks. Mutations
also require exact Origin, session CSRF and recent actual authentication.
Current invalid authority is rejected before freshness advice or receipt lookup.

Principal authority generation advances through disable/re-enable; grant
incarnation advances through removal/regrant. These durable monotonic counters
prevent active=true from reviving old credentials. Ordinary membership revision,
shared service principal/keyset revision and monotonic key issuance generation
are distinct values. Expiry, revocation, disabling and cleanup never reset the
issuance counter. Service key metadata exposes the current shared revision.
Current trusted producers establish these facts; public metadata is not proof.

## Public operations

| Operation | Method and suffix under /v1/workspaces/{workspace_id}/service-principals |
| --- | --- |
| createServicePrincipal | POST collection |
| listServicePrincipals | GET collection |
| getServicePrincipal | GET /{service_id} |
| setServicePrincipalState | POST /{service_id}/state |
| listServiceCredentials | GET /{service_id}/credentials |
| issueServiceCredential | POST /{service_id}/credentials |
| rotateServiceCredential | POST /{service_id}/credentials/{credential_id}/rotate |
| recoverServiceCredential | POST /{service_id}/credentials/{credential_id}/recover |
| revokeServiceCredential | POST /{service_id}/credentials/{credential_id}/revoke |

All mutation requests carry the required safe CAS revision and Idempotency-Key.
Creation compares the workspace revision; other mutations compare one shared
service principal/keyset revision. List pagination is bounded and cursors must
bind the authorized workspace, principal and snapshot; pages are never the
complete locked keyset used for count or lifecycle admission.

## One-time secret and retries

The initial issuance response is distinct from a metadata-only retry response.
A token is spk1.<public lookup ID>.<canonical unpadded base64url 32-byte verifier>.
Its producer must generate an independent cryptographically random 256-bit
verifier and store only its SHA-256, then compare in constant time. Shape checks
do not establish entropy, safe generation or verification.

Only the initial response carries plaintext. Never put it or the verifier hash
in public metadata, receipts, audit/outbox, logs or tracing. Private verifier
records are not public route bodies. A committed issuance response can be lost;
the server cannot promise exactly-once delivery and never durably stores the
original plaintext response. An exact authorized retry returns its original
committed metadata plus current safe state, without reminting or claiming that
the original key remains valid.

The deduplication scope includes workspace, stable human actor, operation,
target principal, target key and Idempotency-Key, and binds the normalized typed
request digest. A changed request conflicts. Caller revocation or changes to
the original actor/target authority generations or grant incarnations deny
replay. Missing or inconsistent committed key, receipt or audit evidence needs
reconciliation, not another issuance. Replays precede fresh target validity and
CAS checks only after current authority and original receipt binding checks.

## Lifecycle decisions

Deployment policy is explicit; no production limits are silently defaulted.
Issuance requires no currently valid key. Rotation preserves at most two valid
keys and cannot widen scopes; the original key retires by the smaller of its
original expiry and the approved overlap deadline. Retry never extends overlap.

A fresh recovery requires a currently valid unrevoked target under the same
current principal generation and grant incarnation. Its replacement inherits
the exact original scopes, expiry and any earlier retirement deadline, uses a
fresh key identity/verifier and
monotonic issuance generation, and revokes the target immediately in the same
commit. Near-expiry recovery yields a short-lived replacement. Recovery cannot
extend authority; ordinary issuance/rotation is the deliberate lifecycle path.

An already-valid second key may survive recovery with its existing bounded
retirement unchanged, under the same current ancestry. Recovery cannot create
a new overlap or revive an expired, revoked or prior-generation target. Exact
recovery retry finds the original receipt before testing the now-revoked target.
Retained records, deduplication receipts and audit evidence must outlive all
corresponding authority/retry deadlines. SQL transactions, retention enforcement,
concurrent-write tests and recovery drills remain producer obligations.


## Executable conformance boundary

[service_credentials.py](../src/strange_physics/service_credentials.py) exposes
plan_service_operation for all six mutations. The request type determines the
operation; path identities and idempotency scope must match it. It authorizes
the current human owner, resolves the complete locked receipt lookup, returns
an exact metadata-only replay when available, or returns a ServicePlan. A plan
is a proposed state transition, not evidence that anything committed.

The plan includes the new workspace revision for creation, the complete service
keyset, a secret-free original outcome, affected-key snapshots, the receipt and
an audit/outbox event. Committed key snapshots retain original expiry, scopes,
retirement and parent authority metadata. The audit binds their canonical digest.
Replay requires all of that evidence and compatible current key projections;
missing receipt/audit/key state, changed immutable key data, rolled-back counters
or altered retention is recovery_required. Recovery never issues from surviving
partial evidence. Expired or unresolved request tombstones must not be presented
as an absent request.

The original committed revision and current principal/keyset revision are
different fields in a retry response. A later revoked, retired or expired leaf
key may be described with valid_now=false. No secret reappears. A changed parent
generation or grant incarnation prevents replay entirely. Current actor
revocation likewise denies before receipt details or freshness guidance.

get_service_principal and get_service_key apply owner authorization before
lookup/projection. List producers use the same authorize_service_management
boundary plus the bounded same-workspace/principal page validators and their
snapshot-bound cursor implementation. service_key_valid is only an ancestry
and lifetime predicate; it does not verify a presented bearer. C2 must
compose actual verified credentials with these current facts before product
authorization. The separate initial-response validator only binds a transient
secret to a proposed verifier digest; it proves neither current authority nor a
SQL commit and is never a replay path.

The additive [authority wrappers](../src/strange_physics/credential_authority.py)
include producer checks for principal active-state transitions and grant
updates. Disabling and re-enabling each advance the principal generation.
Removing and regranting each advance the grant incarnation. A role/revision
change preserves incarnation and follows current per-operation permissions.
Adapters must update these counters in the same transaction as the existing
principal/membership state. Parsing an active snapshot alone cannot enforce
that obligation. These wrappers do not alter accepted session/B1 wire shapes.

## SQL, secret handling and retention obligations

Before serving these routes, the producer must demonstrate the following real
transaction behavior; pure tests are not evidence of its implementation:

1. Verify the cookie/session and original session principal-generation binding.
   Read the current principal, owner grant, enabled-owner set, workspace and
   target service under a consistent lock order. Apply current authority before
   receipt lookup and repeat it at the commit boundary.
2. Use the full deduplication tuple and preserve the normalized request hash.
   Lookups distinguish never-reserved, committed and unresolved/expired tombstone
   states. Only never-reserved permits a fresh proposal. A corrupt or partial
   commit requires reconciliation.
3. Allocate globally unique principal, key and event IDs. A service principal
   cannot reuse a human identity. Create its independent grant atomically.
   Preserve complete current keysets, not paginated subsets, for key counts.
4. Store the keyset revision, immutable issuance counter, authority generations,
   key verifier record, affected-key snapshots, receipt and audit/outbox in one
   transaction. Existing verifier digests are immutable per key identity.
   Apply database uniqueness constraints for IDs, scope/request identity and
   principal/key generation; compare shared revision under the same lock.
5. Only the original successful handler may serialize the transient initial
   secret after commit confirmation and current authorization. Do not persist
   its response body. A crash before commit has no authority; a crash after
   commit or lost acknowledgment permits only metadata reconciliation. Recovery
   is a distinct authorized fresh request that replaces an eligible key.
6. Keep each receipt until the maximum of commit time plus the explicit policy
   retention and every affected key's original expiry. Keep referenced key
   records and audit evidence at least that long. Every mutation extends the
   affected record's retain_until as needed; it never shortens it. The second
   untouched overlap key retains its original retirement.
7. After full receipt/key details become eligible for cleanup, preserve the
   deduplication tombstone while that principal's scope remains addressable.
   Never reuse expired request identities as fresh admission, reset generation
   counters, or delete records still referenced by retained receipts, incident
   evidence or active consumers. Destructive principal lifecycle and its final
   retention policy remain separate work.
8. Enforce deployment policy, bounded pagination, quotas and rate limiting.
   Responses use Cache-Control: no-store. Fixed ServiceError codes map to the
   exact OpenAPI status; reauthentication guidance only accompanies the explicit
   freshness error, and a 429 requires bounded Retry-After.

Policy IDs identify immutable reviewed settings; changing a policy in place is
not supported. Key retention and counter exhaustion block fresh issuance rather
than deleting evidence or resetting counters. Routine rotation requires exactly
one currently valid key, even for zero overlap; recovery is the bounded path
that can preserve a valid second key. New key material must differ from all
retained identities and verifier hashes; secure random generation and global
uniqueness remain real producer obligations.

Required runtime evidence includes concurrent issue/rotate/recover/revoke versus
state/grant changes, idempotency races, crash injection at every transaction
boundary, no plaintext logging/storage, tenant-isolation checks, actual verifier
tests, retention cleanup with referenced receipts, and recovery drills. C2 run
credentials, mandatory product-authority composition, HTTP handlers, SQL,
provider integration and production-readiness gates remain open.

## Focused verification

Run:

```sh
.venv/bin/pytest tests/test_service_contracts.py tests/test_service_credentials.py
.venv/bin/python scripts/validate_contracts.py
```

The synthetic cases cover public/runtime schema boundaries, current authority
before retry/freshness, shared CAS, monotonic generations/incarnations, secret
response binding, explicit metadata-only retries, key count/lifetime limits,
retirement of both sides of overlap, near-expiry recovery, partial atomic
evidence, immutable snapshots and fixed safe errors. They do not exercise a
database, real key verifier, distributed race or hosted service.

## Review refinements

Key valid_now and admission counts describe only live, unrevoked authority under
the current principal generation and grant incarnation. They are not permission
decisions. Role downgrades cannot make live keys disappear from the two-key
count and permit extra issuance that becomes valid upon role restoration.
The creation scope ceiling is immutable and remains representable after a later
viewer downgrade. The [C2 composition](RUN_CREDENTIAL_CONTRACT.md) intersects each permission with that ceiling,
the key scopes and the current role. Current viewer grants permit read, not
create/cancel, regardless of the creation ceiling.

Fresh issue/rotate scopes must fit the current role and creation ceiling.
Exact recovery also rejects when its original scopes no longer fit, because it
cannot silently narrow or extend the recovered authority. The owner can use the
explicit revoke/rotation lifecycle to obtain a narrower key; recovery continues
to preserve the original expiry and retirement.

Before constructing snapshots/audit, every affected key record is retained at
least until the common receipt deadline, including an older rotation target
when the replacement expires much later. An untouched recovery partner remains
byte-identical. Creation replay additionally requires a current workspace
revision at least the committed creation revision derived from its exact
request, so a missing workspace-side commit cannot appear successful.

At the same shared revision, the current principal and every affected key must
equal their committed snapshots. Later key mutations may advance the shared revision and issuance
counter. Later role changes must advance both membership revision and the
shared principal/keyset revision. Creation identity/name/ceiling are immutable
in C1. Active state cannot change under the same principal generation; grant
active state cannot change under the same incarnation. These checks reject
partial state and known rollback; real producers still establish currency
under the shared transaction lock.
