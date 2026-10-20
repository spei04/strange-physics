# WORLD1: immutable worlds and explicit preview grants

This is the typed API review checkpoint for SP-01.d/WORLD1, issue #94.
The modules define bounded messages, pure lossless codecs and intrinsic
cross-message joins. They do not implement authorization, persistence, HTTP,
catalog resolution or a browser client. Runtime predicates follow independent
API review. WEB1 stream/replay contracts remain a separate unit.

## Boundaries and identities

An immutable `WorldVersionRecord` is world-owned private data, containing the
actual CORE `WorldDefinition`, its canonical message SHA-256, a safe view and
historical author ancestry. It is not an ART1 run artifact and does not invent a
run ID. World and version IDs are opaque server allocations, never hashes of
hidden definitions. The safe view includes public space, title, version number,
parent ID and creation time; it excludes law, seed, change schedule, definition
digest and private identity ancestry. Author-written titles can themselves
reveal information: schema separation alone does not establish scientific
blindness or validate an official study's labels.

The schema names four separate closures:
- `x-agent-safe-models`: safe world/version metadata.
- `x-management-output-models`: owner-only grant metadata, including recipient ID;
  these are not agent-stream or run payload roots.
- `x-author-input-models`: intentionally sensitive customer definition input.
- `x-granted-definition-models`: intentionally sensitive definition output,
  available only through the complete current preview boundary.

Private authority, catalog, commits and selection records are not public request
roots. Parsing a trusted projection establishes neither its authenticity nor
its currency. Frozen CORE, SCI, existing run requests and C2 public scopes stay
unchanged.

Browser `noise_seed` is a canonical decimal string in [0, 2^64-1], including
values above JavaScript's exact integer range. JSON Schema and runtime reject
numeric transport, signs, leading zeroes, whitespace, exponents, non-ASCII
digits and overflow. The pure adapter converts to the unchanged CORE integer.
Supported spring/radial/velocity parameters use existing family validators,
preserve absent versus explicitly supplied defaults and signed zero, and reject
unknown keys, explicit null and out-of-domain values. CORE's general plugin
`LawSpec` is not itself admission to this supported browser profile.

The canonical private definition digest is the unchanged SCI message hash of
the actual CORE definition. The mutation request digest instead hashes the
actual browser request, including its decimal seed and expected head. These
identities are deliberately distinct. Exact scientific joins compare canonical message hashes,
including signed zero; Pydantic value equality alone is insufficient. Conversion must round-trip exact CORE
values; it must not silently insert parameter defaults or alter change timing.

## Current browser capability policy

The future complete WORLD1 guard is separately named and browser-only. It uses
the accepted C2 human/session/workspace validation seam without adding a world
flag to `authorize_product`, using `runs:create` as a write proxy or widening
service/run credentials.

| Capability | Current role | Transport and additional conditions |
| --- | --- | --- |
| worlds:read | owner, researcher, viewer | Current browser session and exact workspace |
| worlds:write | owner, researcher | Current browser session, exact Origin and CSRF |
| worlds:preview-grants:manage | owner | GET/list: current authority; issue/renew/revoke: Origin/CSRF and configured recent actual authentication |
| worlds:preview | Current role in configured preview reader roles | Current browser identity plus explicit live exact-version recipient grant |

The complete boundary must validate server time/policy, reject ambiguous or mixed
credentials, enforce the existing Origin/CSRF rules, then validate current human
actor/session, principal generation, membership incarnation/revision and
workspace state. Disabled-owner and quarantine conditions remain effective.
Owner-only management and every current identity/role check precede freshness
advice. Ordinary world creation/versioning does not add a recent-authentication
requirement. Shared identity helpers, if extracted, remain explicitly incomplete;
the existing product guard must still perform its existing permission/scope
checks.

Current authorization precedes private resource lookup, errors and receipt
replay. Owner management metadata is a separate output purpose, not an agent-safe
stream or run payload. A role, creation provenance, terminal run or possession of an ID never
grants truth access. Definition disclosure is unavailable for official-blind
versions. Public creation/versioning only produces customer-authored versions.
A trusted official catalog producer remains separately responsible for official
definitions; this unit creates no official-authoring route.

## Version commit and retry

Initial creation uses a workspace/principal/operation/key idempotency namespace
before a server world ID exists. `WorldMutationScope.world_id=null` is allowed
only for the initial create-version request with null expected parent, revision
zero and no parent/head. The immutable creation receipt binds the allocated
world/version IDs. Retrying that same creation must reuse this receipt and IDs;
it must not allocate another world. Appends and all grant mutations require the
exact existing world ID. The resource target is part of the retained scope and
request binding, not a way to create a fresh idempotency namespace by changing
targets.

Append requests carry the publicly displayed expected head ID and revision.
The proposed immutable commit binds actual request/hash, exact private
definition, author, parent, old head, next ordinal, new head/result and commit
time. Parent and head must agree and chronology cannot move backwards. Result
metadata exposes the CAS revision without returning definition bytes.

The persistence producer must enforce globally unique opaque version IDs, unique
(workspace, world, version_number), same-world parent foreign keys, immutable
validated commit records, unique idempotency keys under the stated namespace,
and atomic version/receipt/head CAS. Partial `WorldVersionLookup` evidence
stays representable so runtime can reject it as recovery-required rather than
normalize it to absence. Every receipt/target/current-head/current-commit joins
the same allocated world before replay. The target may be historical while the
current head is later: later commits cannot rewrite the original outcome.

These bounded witnesses rely on authoritative immutable records produced by
previously validated atomic commits and enforced ancestry constraints. They do
not load every historic hidden definition or prove ancestry against coherent
corruption of all trusted database projections. Missing or contradictory
witnesses are not success. Stale CAS, request-key conflict and expiry retain
explicit failure outcomes. Replays return original safe metadata only.

Every original receipt retains the actual historical WorldPolicy, its exact
retention-derived receipt_expires_at, and the appropriate policy identity.
A WorldReceiptExpiration proposal binds that original full receipt to an exact
WorldExpiredMutation witness at or after the original expiry. Later current
policy cannot rewrite, shorten or recreate the original retention interval.
The producer atomically replaces the full receipt with this minimal uniqueness
tombstone before purging receipt bodies. The witness preserves original scope,
request hash, receipt ID, allocated world ID, original policy hash and retention
chronology. It grants no cleanup, deletion or read authority.

Tombstone uniqueness lasts for the retained workspace/idempotency namespace's
lifetime under the existing deletion lifecycle (SP-37); namespace IDs are never
reused. This is not indefinite personal-data retention after workspace erasure.
All-null lookup means authoritative never-used absence. Receipt plus tombstone,
missing tombstone after purge or contradictory partial closure is recovery
failure, never fresh absence. On current-authorized retries, changed request
identity is HTTP 409/idempotency_conflict; a matching expired key is HTTP
409/incompatible_state with fixed receipt-expired meaning, never session expiry
or automatic key reuse. A partial/contradictory lookup is HTTP
409/incompatible_state with fixed recovery-required meaning. No historical definition or allocated ID is disclosed by
that expiry error. Existing control error vocabulary is unchanged. Unavailable current session/world
policy or transactional authority maps explicitly to HTTP 503/temporarily_unavailable
on every route and fails closed; internal policy_unavailable is not a new wire
code, and stale policy never supplies fallback permission.

## Preview grant lifecycle

A grant binds one workspace/world/immutable version and one human recipient's
principal ID, generation and membership incarnation. Issuer ancestry is audit
provenance, distinct from current recipient authority. Issuer departure does
not itself revoke another recipient's grant. A currently authorized owner may
renew it while preserving the original issuer, target and recipient ancestry.

Issue and renewal require an active current human recipient, active membership
and a role in current policy. Their expiry is exactly commit time plus requested
TTL, bounded by the actual current policy. Renewal requires the old grant still
live, expected revision exact, revision incremented once and a strictly later
expiry. It cannot rebind a new principal generation/incarnation. Revocation
preserves expiry and immutable ancestry, records revocation time and is
permanent. Expired or revoked grants require a new authorized grant ID; there is
no un-revoke. Revocation can proceed after recipient departure and requires
`recipient_at_commit=null`; it does not retain an unbound recipient snapshot.

Each disclosure rechecks current recipient ancestry, workspace state, policy,
expiry and revocation. Removal/re-addition and disable/re-enable that change
incarnation/generation cannot revive the old grant. A role transition among
explicitly permitted reader roles can retain it. A role or policy transition
that removes permission denies access; restoration of permission may allow the
same still-live, unrevoked grant only when the ancestry is unchanged. This is
temporary role denial, not an implicit new grant. An expired/revoked/ancestry-
stale grant never revives through role restoration.

Safe grant metadata exposes revision and timestamps needed for CAS, not recipient
generation, issuer internals, law or definition hash. Grant-management mutations
and retries return metadata only; they never disclose definition bytes or extend
an existing historical outcome. Current policy/authority are rechecked before
retry. Owner-only metadata GET/list does not require recent authentication; the
issue/renew/revoke mutations do. The immutable mutation receipt records actual policy and transition,
while `PreviewGrantLookup` retains partial receipt/current-grant/latest-commit
evidence for runtime recovery validation. A current grant must be the exact
outcome of its latest committed transition, with immutable target/recipient
and monotonic reachable revisions. A retained issuance receipt is not current
disclosure authority.

## Run selection

A trusted current catalog decision for a NEW run must bind the exact workspace,
world/version, actual definition SHA, public space SHA and eligibility revision.
`WorldRunSelection` joins that immutable version to the actual
`OriginalExecutionAdmission`, actual creation request digest, creation time
and admitted space. The requested world version and experiment budget must
exactly equal the selected version and its space budget. Different budgets
require an explicitly authored version; silent budget projection would change
CORE calibration/change-schedule semantics.

The selection producer must recheck current allowed catalog access and commit
the exact selected version/definition/space with run creation under the same
transaction. A successful earlier catalog read is insufficient. Selection composes existing current
C2 runs:create authority for either a browser human or an authorized workspace
service; browser-only authoring/preview is not a new run-creation requirement.
World author and run creator need not be the same principal. The retained creation
result may have later status/revision than the original queued admitted snapshot
under accepted EXEC1 semantics; WORLD1 adds exact canonical space identity, not
whole-RunView equality. This does not
grant definition disclosure to the agent. Retained selection is immutable
provenance for an already admitted run; later withdrawal of NEW-run eligibility
does not add an availability condition to accepted worker/model replay.

## Resource and producer limits

Versioned reference maxima are 64 KiB per definition, 4 MiB per mutation/recovery
metadata envelope, 1 MiB per catalog/grant page and 128 items per page. Configured
policy can be stricter. Producers check raw bounds before parsing, canonical
definition bounds before persistence, nesting/collection limits before large
allocation and total envelope bytes before returning it. Typed item bounds
alone do not prove operational byte bounds. Oversized data fails explicitly;
there is no truncation, partial successful version or automatic budget change.

Owner-management listing uses current authorization on every bounded page.
Cursors must bind workspace, actor, filter/snapshot and expiry; they are not
permissions. Runtime must check the current policy rather than trust a policy
hash claimed by a caller. No SQL, session producer, catalog, signer, deployed
service or recovery drill is implemented by these types.

## WEB1 seam

WEB1 remains a separate reviewed unit: zero-based safe-event sequence (empty
watermark -1), fetch-stream status-before-body, committed cursor/event digest,
captured snapshot watermark, contiguous immutable archive chunks and bounded
large-record retrieval. Private evaluator events and world truth disclosure do
not consume the common safe sequence. Large legal scientific records use exact
agent-visible run-owned ART references plus semantic SCI identity, never
truncation into a 64 KiB event. Current runs:read precedes every bounded retrieval
batch; a reference is not read permission. WORLD1 does not implement SSE,
archive delivery, network parser or browser retry loops.


## API checkpoint validation

The initial typed checkpoint 42cde25 passed 130 focused cases and 820 external
schema checks. Independent review identified canonical signed-zero joins,
historical chronology, opaque-ID page uniqueness and explicit expired-key
evidence that needed tightening. The revised checkpoint includes the browser
OpenAPI contract, original-policy receipt expiration proposals and regressions.
It still contains no authorization or persistence runtime predicates. Full
repository, runtime-boundary and hosted integration checks remain separate gates.

The 913f386 typed API passed 175 focused cases, 1,188 external JSON Schema
checks (including route input/status projection references), full Ruff checks
and strict mypy over 81 source/test/example files. These are contract/codec
checks, not proof of deployed permissions, durable commits or recovery.

An exact 913f386 author run passed all 2,598 tests, Ruff/format, strict mypy81
and 1,188 external schema checks. Subsequent API review correctly narrowed the
additional retained-run comparison to canonical space identity (preserving
EXEC1 later result status/revision) and added an explicit 503 unavailable-policy
route contract. These later changes are validated separately at their exact
checkpoint; the earlier full-run identity is preserved.

The compatibility/503 replacement passes 177 focused cases, 1,201 external
schema checks, full Ruff and strict mypy81. The current review checkpoint still
has no runtime authorization/persistence predicates.
