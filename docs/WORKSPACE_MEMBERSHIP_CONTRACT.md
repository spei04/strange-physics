# Private workspace and membership contract — ID-B/B1

This bounded contract extends the reviewed browser-session and control contracts.
It defines conformance predicates, public HTTP shapes and required transaction
behavior. It does not implement handlers, database isolation, RLS, principal
verification, security-event verification or production recovery.

B2 invitation redemption and B3 explicit identity linking remain separate reviews
under SP-01.b / issue #63. Service/run credential lifecycle also remains unfinished;
this increment does not complete C-ID or unblock producers requiring its full freeze.
The APIs in workspace.openapi.json are the authoritative B1 route candidates.
Their implementation is assigned to SP-08.b/SP-08.d and their database dependencies;
actual integration evidence is still required.

## Human authority and safe responses

All B1 routes require a current ID-A human app session. A bearer credential alone
cannot administer a workspace, list memberships or obtain the caller's membership.
Cookie plus bearer is ambiguous and returns 400 using the unchanged control Error
envelope. Mutations additionally require the exact configured Origin, session-bound
CSRF and an Idempotency-Key. The entire ID-A cookie, no-store, origin, logging,
response-header and policy-failure contract applies.

DeploymentSessionPolicy is immutable/versioned and must be present. Its explicit
recent_auth_seconds also governs workspace creation and owner mutations, including
retries: server now minus the session's actual authenticated_at must be strictly
less than that limit. Equality fails. Renewal, last_seen_at or credential rotation
cannot refresh authentication. Read-only status/list routes require a current
session and applicable membership, without a gratuitous freshness challenge.
Concrete time limits remain a deployment-policy approval in SP-02.c.

A valid but insufficiently recent session produces the internal decision
reauthentication_required. management_session_error maps this deliberately to 401,
the existing Error code unauthenticated, fixed message "Recent authentication
required.", retryable false and X-Authentication-Action: reauthenticate. The
header is absent for missing, invalid, expired, rotated or revoked sessions.
Clients use the header to initiate the normal ID-A login flow, never an automatic
mutation retry or inferred provider challenge. ID-C may reuse this meaning after
its own review. Other ID-A failures preserve their existing mapping; application
not_found, forbidden, incompatible_state and idempotency_conflict retain the
control envelope and safe fixed messages. No provider error, email or account
existence detail is included.

Authorize in this order: current session/HTTP constraints, current tenant visibility,
then current role/quarantine, then target and revision details. Foreign or nonvisible
workspace/target bindings return 404. Insufficient role within a visible workspace
returns generic 403. Inactive membership yields generic 403 without disclosing
target details. Principal identifiers are stable app IDs, never emails.

| Operation | Authority | Quarantined/effectively ownerless workspace |
| --- | --- | --- |
| List caller workspaces | Current human session; each result has current active membership | Safe status projection only |
| Workspace status / own membership | Current human session and caller-bound active membership | Allowed; no results or control access |
| List members | Current owner membership | Denied |
| Create workspace | Current recent human session and current approved onboarding grant | Creates a new private workspace only |
| Change role / revoke member | Current recent owner, target binding, shared revision | Denied |
| Product data/control/worker operation | Existing control permission plus current workspace authority | Denied, including cached replies |

Membership views contain only workspace ID, app principal ID, role, active flag
and revision. No email, issuer, subject, session, credential hash or security-event
reason appears. Member listing is owner-only. Cursor producers bind each opaque
cursor to caller, tenant, filter, ordering/snapshot and expiry; a cursor is never
authority. Page size is 1–100; next_cursor is null at the end. Each page repeats
current authorization. Membership snapshots and cursors are not immutable grants.

## Workspace bootstrap

CreateWorkspaceRequest contains only display_name. Server policy chooses approval,
workspace ID, private visibility and initial owner; public owner_id, role and
visibility injections are rejected. Display names are untrusted text: UI rendering
must escape them, and adapters must avoid using them as filesystem/object paths.

One current WorkspaceCreationGrant authorizes one workspace for one stable principal.
Its ID, principal, expiry and revoked status are server-owned. A fresh creation
requires an unconsumed grant. In one transaction, consume it, create a private
active workspace at revision 0 and its creator's active owner membership at revision
0, and commit the receipt and response. Never return success between these writes.

Creation receipt scope is caller + workspace_create + grant + key; its outcome_id
is the created workspace ID. An exact retry still needs the current approved,
unexpired grant, current recent session and current creator-owner authority in
the resulting active workspace. Revoking that membership or quarantining the
workspace fences the replay. Grant revocation/expiry also fences it. A consumed
grant without a matching receipt cannot create another workspace. A different
request with the same scoped key conflicts.

## Owner snapshots, principal disablement and quarantine

WorkspaceAuthority is a trusted current transaction input, never a public request.
active_owner_ids is the complete sorted unique set of *active owner membership
rows*. disabled_owner_ids is the complete sorted unique subset whose app principals
are currently disabled. Enabled owners are their difference. Database producers
must join current principal state; counting membership rows alone is insufficient.
PrincipalStatus binds a target's current active status to its stable principal ID
and explicitly requires kind=human. B1 management and owner sets use the separate
human membership relation only. Service identities and run grants may share a
control Membership projection, but are never candidates for administrative
ownership or role-change targets. SQL producers must enforce this distinction;
parsing a kind=human claim is not identity verification. ID-C must preserve the
separation rather than count service/run grants as usable owners.

This distinction supports a security-event interval where a principal is already
disabled but its membership row and persisted workspace state have not yet been
updated. The snapshot can represent that interval. workspace_status projects
quarantined whenever no enabled owner remains. authorize_product and
check_product_idempotency require the full WorkspaceAuthority, rather than only
a WorkspaceView, and deny both persisted quarantine and zero enabled owners.
Thus delayed event fan-out cannot turn an effectively ownerless workspace into
an authorized product workspace. Current principal disablement independently
invalidates that principal's sessions/credentials immediately.

Every product adapter must compose these predicates with the current credential,
membership and lease fences before reads, stream establishment/delivery, worker
claims/results/checkpoint/artifact commits or cached responses. Old control
authorize/check_idempotency alone are insufficient after B1. In particular,
check_product_idempotency validates current scope/authority and effective workspace
state before examining stored identity/conflict details. Every long-lived stream
and write fence must refresh authority; an initial check does not grant a lease
over future revocation. Safe status routes are the explicit limited exception.

An elective change must preserve at least one enabled owner. Two owner rows with
one disabled principal therefore do not permit the remaining enabled owner to
demote/revoke themself. A disabled researcher cannot be promoted to owner:
the independently current PrincipalStatus must match the target and be enabled
for role changes. Existing owner status must agree with disabled_owner_ids.
A security revocation may remove the last enabled owner's row; the same atomic
proposal then persists quarantine. Quarantine remains sticky even if a later
snapshot contains an enabled owner. Recovery requires a separate reviewed trusted
workflow; there is no public force, security-reason or unquarantine option here.

## Required SQL transaction and replay behavior

These are obligations for real adapters, not proof supplied by pure predicates.

1. Resolve and validate the current human session (or verified internal security
   authorization). Lock/read the current workspace, actor membership, target
   membership and relevant principal status within one coherent authorization
   snapshot. Revalidate authority at commit under the same serialization domain.
2. All ownership-changing transactions serialize on the workspace row/revision,
   including other-target changes, security revocation and principal-status effects
   on owner eligibility. Principal disablement and owner promotion must share an
   enforceable lock order or serializable conflict/retry protocol. Merely reading
   an earlier complete set does not suffice.
3. Produce complete membership-owner and disabled-owner sets from that snapshot;
   reject duplicates, mixed revisions and actor/target inconsistencies. The model
   cannot prove that SQL omitted no rows. No paginated member page is an owner set.
4. Authenticate and current-authorize before receipt lookup. Receipt uniqueness is
   caller + operation + workspace + target + key for member mutations, and the
   creation scope above. Bind the normalized typed request digest using the SCI
   canonical codec and retain immutable safe response/outcome bytes. Never trust
   a caller-provided receipt or digest.
5. On an exact authorized replay, return the bound historical result. Do not apply
   the original expected workspace/target revision again: the first commit already
   advanced them. Current caller authority, recent authentication and quarantine
   still apply. A creator/owner who lost authority cannot replay their old receipt.
6. On absence, check both expected_workspace_revision and
   expected_membership_revision, verify the target and calculate the proposal.
   Compare-and-swap the shared workspace revision and target revision, each by one.
   Persist mutation + owner/quarantine changes + immutable receipt + audit/outbox
   event atomically. A conflict rereads everything, including actor authority.
7. Respond only after commit. Crash recovery must distinguish an absent receipt
   from a committed outcome and replay the latter only after current authorization.
   Receipt retention must cover the supported retry window; expired receipt keys
   must not silently reexecute. Retention values require versioned deployment policy.

The two-owner race tests show that refreshed proposals reject the losing mutation;
they do not demonstrate actual SQL locks, linearizability or database race handling.
Those require integration tests with concurrent transactions and failure injection.

## Trusted security revocation

SecurityRevocationAuthority is a separately verified, current internal permission
scoped to a workspace, with named actor, authorization ID, explicit expiry and
revocation. SecurityRevocation binds that authority and actor to a unique audit
event and target principal. Model parsing does not verify either source.
There is no corresponding public route or owner-selected security boolean.

The internal producer verifies event provenance, current authorization and intended
target, fences global principal access when applicable, and durably fans out to
every affected workspace without requiring the revoked owner's session/consent.
Per workspace, use the same serialization rules and commit membership removal,
owner-set updates, quarantine, audit/outbox and event dedup atomically.
A duplicate committed event is acknowledged from the trusted internal event
receipt; fresh proposal validation intentionally rejects an already-inactive target.
Security revocation cannot resurrect membership, erase quarantine or delegate
recovery authority to the disabled principal. Principal disablement must durably
record a pending security-event fence. Reactivation is forbidden while any
affected workspace settlement is pending; an effectively ownerless interval must
latch persisted quarantine before that fence can be released. Re-enabling a
principal cannot erase that interval or infer workspace recovery. The future
reviewed recovery producer must enforce this ordering across crashes and retries;
B1 exposes no principal-reactivation API. Trusted PrincipalStatus,
session and credential producers must continue projecting the principal as
inactive/revoked while this durable fence is unsettled; an administrator
reactivation request cannot override it. Coordinator/storage enforcement and
crash/failure-injection evidence remain required, not demonstrated by these pure
current-state predicates. Partial fan-out is retryable and
observable; failed delivery is never silently declared complete.

Required future evidence includes concurrent owner changes with principal disable,
current revocation on every adapter/cache path, invitation/link integration,
cross-tenant SQL/RLS negatives, event replay/fan-out failure recovery, audit integrity
and browser transport tests. Synthetic fixtures and this review are not that evidence.
