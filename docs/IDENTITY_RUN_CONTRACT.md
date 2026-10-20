# Identity, run and SQL contract v1 — first control subset

SP-01.b / issue #52, part 1. The full task remains in progress until remaining
C-ID contracts are reviewed; downstream full-contract consumers remain blocked.
This bounded contract covers the eleven routes in the
[partial OpenAPI draft](../contracts/draft/openapi.json).
[Schema](../contracts/control.schema.json),
[pure conformance checks](../src/strange_physics/control_contracts.py),
and [synthetic examples](../contracts/control.examples.json) define the subset.
The [browser-session subset](BROWSER_SESSION_CONTRACT.md) adds ID-A interfaces.
Membership/invitation/linking (ID-B) and credential lifecycle (ID-C) remain open;
full-contract consumers stay blocked.
Producer/consumer acceptance is recorded separately after independent review.

There is no hosted API, token issuer, SQL migration, RLS policy or deployment
here. These predicates do not verify credentials, read current membership,
acquire locks, verify objects, stop workers or prove a transaction committed.
Examples are invented contract data, not credentials, scientific results or
operational evidence. CORE and the local SDK are unchanged.

## Scope

| Frozen here | Remaining dependency |
| --- | --- |
| Identity/current membership separation, role/scope predicates | OIDC/session verifier and cookie/CSRF HTTP implementation; service credential rotation |
| Run/operation projections and transitions | HTTP handlers, dispatch and recovery |
| Scoped idempotency and checkpoint history | Durable SQL transactions and concurrency tests |
| SQL keys, relationships, transaction and tenant isolation obligations | Migrations, RLS policies, runtime DB roles |
| Eleven existing route identities and scopes | Remaining product routes |
| Checkpoint index/identity/size/full-payload replay | ART envelope, object generation/hash verification and retention (SP-01.c) |
| Model submission operation/receipt identity | ART envelope and hosted EXEC protocol |
| Event stream authorization scope | WEB schema, cursor retention/resync and SSE renewal (SP-01.d) |

OpenAPI remains partial and unimplemented. Local SCI schema acceptance does not
freeze a hosted prediction protocol. Checkpoint and model ART bodies, and WEB
events remain explicitly draft.

## Identity and current authority

Identity is the verified (issuer, subject) pair. The external verifier checks
issuer allowlist, audience, signature, expiry and revocation, then resolves that
pair to a stable application principal. Email/domain neither links accounts nor
grants workspace membership. Account linking needs explicit proof.

A current membership/grant is loaded independently of credential claims. It
binds workspace, principal, active state, role and revision. Authorization is
checked on every request, before returning idempotent responses, and again in
the mutation transaction. Revocation denies that caller and inherited
credentials according to their issuer authority. It does not implicitly cancel
every historical run. An independent service/run principal has its own current
grant and lifecycle. Resolving credential ancestry/revocation is the issuer's
responsibility before constructing the trusted projection.

VerifiedCredential, Membership and RunLease are internal trusted projections,
never request bodies or evidence that verification happened. The authorize
predicate checks only relationships and current values supplied by the eventual
verifier/transaction. Success does not prove those inputs were securely obtained.

Owner/researcher can create/cancel runs within explicit scopes; viewer can read.
Owner powers on future administration routes do not grant hidden-law, provider
secret or evaluator-result access. Service credentials require explicit current
grants and narrow scopes. Workspace credentials cannot impersonate the worker.
Run credentials are bound to workspace/run/attempt/epoch and worker-only scopes.
Refresh does not change the stable principal/idempotency identity.

| Operation ID | Method | Credential | Required scope |
| --- | --- | --- | --- |
| createRun | POST | workspace | runs:create |
| getRun | GET | workspace | runs:read |
| cancelRun | POST | workspace | runs:cancel |
| streamRunEvents | GET | workspace | runs:read |
| getWorkspaceOperation | GET | workspace | runs:read |
| getExperimentSpace | GET | run | experiments:read |
| listExperiments | GET | run | experiments:read |
| getRunOperation | GET | run | experiments:read |
| runExperiment | POST | run | experiments:write |
| saveCheckpoint | PUT | run | checkpoints:write |
| submitModel | POST | run | models:write |

Resource lookup always uses (authorized workspace, requested resource ID);
the client body is never authority. Foreign tenant/object denial is
nonenumerating 404 not_found. Missing/expired/revoked credentials receive 401
unauthenticated; current credentials without membership/scope receive 403
forbidden. Error messages must use approved public text, never stack locals,
exceptions, credentials, hidden truth or held-out results. Error validates shape,
not information content; handlers must supply the safe-message allowlist.

Run calls also require requested run, current attempt and epoch, server time
strictly before credential/lease/run deadlines, and running state. Replacement,
revocation, cancellation or terminal transition invalidates old worker writes.
Server time is integer UTC Unix seconds; equality at expiry is expired.
Lease epoch is authority generation; run revision is a state CAS version.
SSE periodic reauthorization (target <=30 seconds) is later integration work.

## Run and operation states

| From | Allowed next states |
| --- | --- |
| queued | preparing, cancelled, expired |
| preparing | running, cancelling, failed, expired |
| running | recovering, evaluating, cancelling, failed, expired |
| recovering | running, cancelling, failed, expired |
| evaluating | completed, cancelling, failed, expired |
| cancelling | cancelled |
| completed / failed / cancelled / expired | none |

State transitions compare expected revision and increment exactly once.
Identity and experiment space remain immutable. State transitions cannot change
accepted counters. Admission is a separate serialized transaction incrementing
revision with ordinal/debit; the state predicate is not that transaction.

Entering evaluating/completed additionally requires a transaction-derived committed
prefix equal to experiments_accepted - 1. Settled resource counts cannot prove
that every accepted slot produced an observation. Compute this prefix from the
complete authoritative accepted ledger, not a page or client assertion.
Failure/cancellation can settle with incomplete observations.

Terminal states require zero active workers and zero unsettled resource
reservations, from the same authoritative transaction. Failure/expiry may need
prior termination/reconciliation; expired authority is not proof a worker
stopped. Cancelling reaches cancelled after settlement even if a wall deadline
passes. Timeouts cannot bypass reconciliation.

Operations move pending → running/completed/failed/cancelled; running →
completed/failed/cancelled. Exact terminal snapshots may replay; changed terminal
payloads and reopening are rejected. Workspace/run/operation ID, kind, normalized
request digest and accepted ordinal are immutable. Every completed experiment
record must hash to the normalized request digest, including physical failures.
Before durable result commit, the adapter must also apply existing CORE
ExperimentSpace/ObservationBundle validation against pinned RunView.space:
action bounds/topology/ordered particle identity, trajectory shape and full
published sampling count/times. Operation alone has no pinned space and does
not certify those properties. Out-of-order results require equivalent per-record
CORE checks before persistence and full bundle validation before prefix export;
that adapter remains later integration work. Completed requires a typed
result of its own kind and no Error; failed requires Error and no result;
pending/running/cancelled have neither. Result tenant/run or operation/ordinal
must match the envelope. Cancellation completes only with a cancelled RunView.
ModelReceipt acknowledges submission and never exposes held-out scores.

Run counters always satisfy:

    experiments_accepted + budget_remaining == space.budget

Every accepted slot stays charged, including pending/aborted execution.
A physical simulator failure completes the Operation with a failed
ExperimentRecord and existing simulation_failed code. It advances the observable
prefix. Infrastructure failure can terminate an operation without a CORE record;
it cannot fabricate a physical failure or trajectory.

## Accepted slots, gaps and recovery

ExperimentPage lists accepted experiment Operations in ordinal order, with unique
IDs and workspace/run binding. This replaces the draft record-only page, which
could not represent pending/cancelled reservations. It is an audit view, not an
ObservationBundle. Opaque cursors must bind tenant/run, ordering and snapshot;
cross-page completeness needs server snapshot enforcement and the later cursor
policy, not just a page's structural validation.

Keep four quantities distinct:

- Accepted count: all reserved ordinals, including unobserved/aborted slots.
- Hidden regime/noise identity: pinned to the same accepted ordinal; retry
  cannot shift the regime or choose new randomness.
- Observable prefix: contiguous completed operations containing actual CORE
  records, including failed simulations, beginning at zero.
- Fitted prefix/selection: SCI purchased prefix and completed records selected
  for fitting; failed observations are never fitted evidence.

contiguous_record_prefix stops at missing/pending/running/aborted slots despite
later results. validate_experiment_admission takes the complete accepted ledger,
not a page, and blocks fresh admission while any gap exists. Recoverable work
retries the same nonterminal Operation/request/ordinal/debit/regime identity
under a fresh valid lease. A terminal aborted slot never reopens.
An unrecoverable gap terminates the run as failed/cancelled with explicit cause;
never continue at the next ordinal or shorten it into a successful episode.

Later real outcomes remain auditable. Export the actual contiguous CORE prefix
and a separately labeled accepted-slot/incomplete manifest; retain all debits
and outcomes. Unrecoverable runs remain failures in future study accounting.
CORE does not represent aborted slots; future CORE evolution and hosted export
adapters are separate work.

## Idempotency and canonical requests

POST identity is:

    workspace_id, stable_principal_id, operation_kind, resource_id, Idempotency-Key

Resource is workspace ID for creation and run ID otherwise; kind maps one-to-one
to these four POST routes. Keys are 1–128 printable non-space ASCII characters.
Keep records for the retained run lifetime; deletion/tombstone behavior remains
a later lifecycle decision. Credential ID, attempt epoch, correlation request_id
and timeout never create a new operation identity. Another principal cannot
replay a caller's stored response.

Hash validated, normalized typed messages with canonical profile
strange-physics.python-json.v1: all JSON-mode fields including defaults/nulls,
Python JSON sorted keys, compact separators, ASCII escaping, finite numbers,
UTF-8 and no newline. This is not RFC 8785. Other languages reproduce golden
bytes or use a conforming adapter. Raw client bytes/claimed hashes are not
authority. Cancellation's absent body normalizes to {}. Model hashing remains
conditional on its eventual ART/EXEC validator.

Admission order:

1. Verify identity/current authority, validate request and resource scope.
2. Look up the full idempotency tuple.
3. Same digest returns original Operation (200), even if a fresh admission would
   fail budget. Changed digest returns 409 idempotency_conflict. Revoked access
   receives no stored result.
4. New requests enforce state, complete ledger, limits and budget; atomically
   insert request, operation, ordinal, debit, counters/revision and dispatch
   outbox before acknowledging (202).
5. Lost acknowledgement reconciles the same identity, never a new key or slot.

Invalid requests never reserve. CPU/wall caps are positive; other caps may be
zero to prohibit use. Workspace policy can tighten these syntactic bounds;
provider prices/quota enforcement are not implemented here.

## Cancellation and commit races

Accepting cancellation atomically revokes new launch/broker/result/checkpoint authority and
records transition/dispatch intent. It is not worker termination proof.
Committed records persist; in-flight resources remain explicit until settlement.
Only unused resource reservations can release after reconciliation; accepted
experiment count never refunds.

The first valid locked/CAS commit wins:

- Cancel before experiment acceptance: no ordinal/debit.
- Real result committed before cancellation acceptance: preserve completed Operation and
  record even if the run later becomes cancelled.
- Cancellation acceptance before result: retain ordinal/debit, produce no
  fictitious observation and reject late output, even before settlement.
- Completion/expiry winning the run revision prevents a new cancellation.
  Exact authorized retries may return their original immutable operation;
  fresh terminal-run cancellation conflicts.

Queued → cancelled requires no remaining active worker/resource. Every result
or checkpoint commit rechecks authority, attempt/epoch and deadlines in the
same transaction as its state checks.

## Checkpoint PUT

Natural identity is (workspace_id, run_id, index). Path equals through_index.
Agent ID and pinned agent package/config/runtime/protocol match trusted
server-side authorized attempt metadata, not client assertions.

Canonical core Checkpoint JSON remains <=256 KiB. ART envelope limits are
separate; the core cap does not permit unlimited metadata. New indices increase
beyond latest but may lag the contiguous record prefix. Initial -1 is valid.
Failed physical records advance it; pending/missing/aborted slots do not.

Hash the entire normalized existing HTTP request: checkpoint, runtime image
digest, ordered artifact list including all metadata. After ART validation,
exact historical replay returns its stored value without moving latest.
Changed existing content or a new decreasing index conflicts (409);
path mismatch/oversize is invalid (422). Hosted immutable per-index history
extends the unchanged local journal, which stores latest only.

The pure checkpoint predicate receives trusted binding, prefix/latest state,
stored/full digests and an externally derived artifact-validation outcome.
A client flag or digest is not evidence. Success proves no durable bytes,
generation/hash, tenant visibility, membership or lease. The handler must
validate ART, compute digests, verify durable generation/hash/size and current
authority, and run the predicates in the same commit context. Object-first
upload followed by SQL failure may leave an orphan; never acknowledge a
reference to missing bytes.

## Required SQL schema and transactions

This is a contract, not executable DDL. Physical names may differ; equivalent
constraints require later migrations and concurrency evidence.

| Relation | Required identity/constraints |
| --- | --- |
| identities | Unique (issuer, subject) → principal; no email-based account merge |
| memberships | Primary (workspace_id, principal_id), role/active/revision |
| runs | Primary (workspace_id, run_id), revision, immutable world/agent/config/runtime, budget checks, deadline |
| attempts | Tenant/run/attempt primary and composite run FK; unique tenant/run/epoch; at most one active epoch |
| operations | Primary tenant/operation; composite tenant/run FK; immutable kind/request; status/result checks |
| idempotency | Unique full scope tuple; composite operation FK with matching kind/resource/request digest; original response |
| experiment_reservations | Unique tenant/run/ordinal and operation; ordinal within budget; immutable request/debit; composite FKs |
| experiment_records | Composite FK to accepted tenant/run/ordinal; immutable typed result; absent for pending/aborted slots |
| checkpoints | Primary tenant/run/index; immutable request/digest/binding; atomic latest pointer with composite FK |
| resource_reservations | Tenant/run/operation FKs; reserved/settled state and actual cost; idempotent settlement |
| outbox | Tenant/run/operation FK; unique dispatch/delivery identity; durable before ack; replay-safe consumer |
| artifact references | Tenant-scoped FKs; verified durable generation/hash/size; ART owns storage schema |

Use CHECKs for numeric/state bounds, budget arithmetic and result/error
nullability where possible; cross-row and JSON semantics need transaction
predicates and validated typed payloads. Naked resource ID FKs cannot cross
tenants. Schema-valid digests do not prove underlying content.

Serialize admission, cancellation, result and checkpoint commits against the run
row/current attempt under an explicit locking/isolation strategy. Recheck
revision, current authority, attempt/epoch and server deadline inside each
transaction. Acceptance commits request/operation/ordinal/debit/counters/revision/
outbox together. Checkpoint commit compares natural key/full content and latest
under one lock. Cancellation fences launch/broker/result/checkpoint writes and emits reconciliation together.
Unique/CAS conflicts re-read under current authority; never ack partial commits.

Runtime DB roles cannot own tables, bypass RLS or grant privileges. Migration
owner is separate from API/worker/evaluator roles. Set tenant context from
verified authority transaction-locally, never client body/SQL; reset on pooled
connection reuse. RLS supplements explicit object authorization and composite
FKs. Error, rollback and nested transaction paths must not retain tenant state.
Workers/evaluators receive least privilege.

## Remaining C-ID freeze checklist

A separate coherent SP-01.b follow-up must specify public browser session,
invitation/membership, and service credential management contracts before the
whole C-ID freeze or its dependent tasks can complete:

- Browser login/callback/session introspection/logout and expiry/renewal shapes;
  secure cookie, origin/CSRF, callback state/nonce and explicit account linking.
- Invitation creation/redemption/expiry/revocation and identity binding;
  membership list/change/remove authorization, role changes and last-owner rules.
- Service principal/credential create/list/rotate/revoke scopes, secret handling,
  authority ancestry and revocation propagation.
- Concrete routes, request/response/errors, concurrency/idempotency examples,
  schema/runtime fixtures, security test obligations and producer/consumer review.

This subset neither invents those unfinished route shapes nor counts them as
accepted. No handlers are implied by their later contract freeze.


### Remaining PR units and planning estimate

| Unit | Owner / dependency | Reviewable result |
| --- | --- | --- |
| SP-01.b/ID-A | Research; after control part 1 | Browser sessions/bootstrap, managed broker proof versus OIDC callback, origin/CSRF, renewal/logout and required versioned deployment policy |
| SP-01.b/ID-B | Next backend author; after ID-A | Workspace membership, single-use invitations, last-owner safety and explicit two-identity linking |
| SP-01.b/ID-C | Next backend author; after ID-B | Service/run credential issuance, rotation, revocation ancestry, safe metadata and one-time secret delivery semantics |

Research's remaining estimate is 6–8 engineer-days, medium confidence; this
supersedes the original four-day task estimate for execution planning. Reforecast
at the next planning checkpoint; do not convert agent elapsed time into human
staffing or use the historical comparison schedule as a current promise.
ID-A preparation is complete; authoring is queued behind CI-01. Concrete
origins/callbacks and lifetime values remain explicit deployment-policy inputs.
Missing policy fails closed; no implicit production defaults are approved.

Retain Identity Platform Google/GitHub sign-in and the portable OIDC adapter.
The app verifies the configured broker, not a raw GitHub OAuth token as its own
OIDC identity. Avoid automatic email-based merging, including at the configured
broker; manual linking requires explicit proof.
[Identity Platform GitHub sign-in](https://docs.cloud.google.com/identity-platform/docs/web/github),
[account-linking configuration](https://docs.cloud.google.com/identity-platform/docs/link-accounts),
[token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens).

## Required later integration evidence

Independent review accepts shapes/examples, not production readiness.
Later HTTP/SQL/worker slices must demonstrate:

- Concurrent same-key requests produce one operation/debit/outbox; changed
  content conflicts, revoked retry fails, unknown timeout reconciles once.
- Cross-tenant reads/writes/polls/cursors fail under actual SQL roles; pooled
  context stays isolated on success, errors and rollback.
- Lease/deadline/cancel/result races commit one valid winner; stale output fails;
  terminal state waits for reconciliation.
- Object-first checkpoint commit rejects wrong/missing generation/hash/size/
  authority; SQL rollback/orphan recovery works.
- Recovery preserves accepted identity/regime/noise; gaps block admission and
  remain visible in audit, export and study accounting.
- Process death at each commit/dispatch boundary never creates free retries,
  uncharged experiments or acknowledged missing records.

JSON Schema enforces structural shape; documented semantic validators and cross-message
predicates remain mandatory. Parse untrusted JSON through normal validation; do
not use model_construct/model_copy to bypass it. Frozen models are shallow;
do not mutate nested state after validation/hashing. Use canonical committed
bytes as durable identity.

Current tests cover pure decisions, schema examples, canonical bytes and route
consistency. They do not execute PostgreSQL, verify real tokens, run concurrent
workers, implement HTTP, or measure hosted security.
