# Service principal and API-key contracts — ID-C/C1

Status: early API/schema review checkpoint. Lifecycle predicates and their
adversarial tests follow this checkpoint; these interfaces are not a hosted
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
the exact original scopes and expiry, uses a fresh key identity/verifier and
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
