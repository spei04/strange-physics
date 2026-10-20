# Run credentials and composed product authority — C2

This additive internal contract follows accepted C1. It defines no public mint
route, token signer/verifier, HTTP handler, SQL transaction or worker coordinator.
Schemas/examples describe trusted producer projections, not authority supplied
by a client. C2 and the full SP-01.b composition freeze require independent review.

## Mandatory product admission amendment

The completed C2 implementation amends both existing complete admission functions:
authorize_product and check_product_idempotency gain a required keyword-only
authority: ProductAuthority, without a default. Every current caller must change;
the only existing callers are the workspace contract tests. Public session,
membership, service and control wire shapes remain stable. This early interface
checkpoint defines the union; executable composition and caller migration follow
before C2 acceptance. An unused optional helper is not a completed security boundary.

HumanProductAuthority binds current ID-A policy/session/credential/browser context,
current principal/grant and the original session principal generation. Product
writes require Origin/CSRF. Ordinary product calls do not acquire the separate
recent-authentication rule used by owner-management operations.

ServiceProductAuthority binds the actually resolved key identity to the complete
current C1 keyset and policy. Each operation intersects current role, immutable
creation ceiling and key scopes. Key valid_now is lifetime/ancestry only; it never
proves a permission or an actual bearer verification.

RunProductAuthority binds actual verified run-token claims to current durable
ownership, principal/grant, run, lease and complete credential state. The existing
VerifiedCredential projection must agree with all overlapping token/state fields.
Its stable principal is the owning human or service identity; a worker attempt
does not allocate a new app principal or grant.

Current authentication and matching projections precede scope/role/workspace/run
fences and any cached response. Every write commit and every streamed payload
batch repeats authoritative current checks. The <=30-second interval applies
only to idle checks, with no cached authorization grace. Low-level control
authorize/check_idempotency are incomplete hosted-admission primitives.

## Durable ownership and bounded worker authority

RunOwnership is immutable from original admission through every attempt. It
records workspace/run, stable owning principal kind/ID, original principal
generation and grant incarnation, original deadline, and a canonical fixed
worker-scope subset. created_by_credential_id is audit metadata only. Routine
creator session expiry or service leaf-key rotation/revocation does not revoke
independent durable run ownership.

Current owner disablement, changed generation/incarnation, inactive grant,
quarantine, stale attempt/epoch, credential replacement/revocation, run state or
deadline invalidates the affected operation. Role downgrade retains existing
per-operation semantics: a viewer may use experiments:read when scoped but cannot
write experiments/checkpoints/models. C1 workspace-key permissions and creation
ceilings are not worker permissions; authorized run admission fixes the worker
subset separately. A downgraded runtime's suspension/cancellation/settlement is
a separate liveness obligation, never permission to continue committing writes.

RunTokenClaims includes explicit policy issuer/audience, immutable ownership
digest, run/attempt/epoch, monotonically increasing run-wide credential generation,
fixed scopes and issuance/expiry. Current state retains exactly one current key
pointer and complete records, not a page. Old records and counters cannot be
reset or silently recycled. A proposal's claims are not verified claims; the
eventual signer/verifier must keep these producer paths distinct.

## Private coordinator lifecycle

A separately verified current RunCoordinatorAuthority is required for issue,
replace, revoke and reconciliation. No public browser/service request mints worker
authority. Requests contain expected run and credential revisions and, for
replace/revoke, a target credential ID. There is no scope, owner, deadline or
lifetime override.

Issue/replace derive expiry as the minimum of server time plus the explicit policy
TTL, the current lease expiry and original ownership deadline. Current run/lease
must be running, unrevoked and unexpired, with exact attempt/epoch and deadline
binding. Issuance uses a fresh server-allocated key identity and advances the
run-wide generation. Replacement immediately fences its predecessor; there is
no worker overlap or grace period. The real producer verifies all current
coordinator and owner facts in the same serialization domain.

A fresh proposal atomically binds the complete credential state, original
outcome, affected snapshots, receipt and audit/outbox. Every referenced record
outlives the common receipt deadline. Missing/partial evidence blocks recovery;
an expired or unresolved request tombstone is never an absent lookup.

Only the original successfully committed handler may deliver newly issued token
material after another current-authority check. This module returns a proposal
with issue_claims, not a signed token. A retry returns only safe original/current
metadata and cannot invoke issuance again. A currently authorized coordinator may
reconcile an earlier replaced key in the same current attempt/epoch. An ordinary
worker retry with an expired/revoked/replaced credential fails before inspecting a
cached product result. Coordinator reconciliation and worker admission are
different operations.

At equal revisions, current affected state must exactly match committed
snapshots. At later revisions only declared monotonic evolution is permitted.
Generation, owner, attempt/epoch, policy or security-fence mismatch denies replay.
Producer currency, uniqueness, token verification, signature keys, secure delivery,
database locking, concurrency, crash reconciliation, cleanup and worker stopping
remain implementation obligations.

## Early interface evidence

The internal schema and synthetic examples are generated from
run_credential_contracts.py. No raw bearer, signing key, hidden world or evaluator
label belongs in these records. Schema/runtime tests check shape and cross-message
relationships; they do not demonstrate cryptography, a live database or hosted
authorization. Executable composition/lifecycle and the complete final test matrix
must be reviewed before this contract is accepted.
