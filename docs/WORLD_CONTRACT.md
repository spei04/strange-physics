# WORLD1: immutable worlds and explicit preview grants

This is the integrated pure-contract and predicate unit for SP-01.d/WORLD1,
issue #94. It defines bounded messages, lossless codecs, current-authorization
checks, version/grant proposals and exact retained-recovery joins. Hosted
authority producers, persistence, HTTP, catalog resolution and browser clients
remain unimplemented. WEB1 stream/replay contracts remain a separate unit.

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

The complete WORLD1 guard is separately named and browser-only. It uses
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
requirement. The shared identity helpers remain explicitly incomplete;
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
The producer atomically replaces the idempotency-response lookup with this minimal
uniqueness tombstone before purging an expiring response copy. The witness preserves original scope,
request hash, receipt ID, allocated world ID, original policy hash and retention
chronology. It grants no cleanup, deletion or read authority.

Receipt-response expiry must not purge authoritative immutable transition
provenance still required by WorldVersionLookup.current_commit or
PreviewGrantLookup.latest_commit. Those witnesses remain subject to the current
head/grant and resource/deletion obligations. If one stored row serves both
roles, its response deadline is not permission to delete the required transition
record. An expired-key lookup can retain a current/latest commit witness while
its separate receipt field is absent and its expired witness is present; this
does not restore the expired idempotency response or grant definition access.

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


## Historical API checkpoint validation

The initial typed checkpoint 42cde25 passed 130 focused cases and 820 external
schema checks. Independent review identified canonical signed-zero joins,
historical chronology, opaque-ID page uniqueness and explicit expired-key
evidence that needed tightening. The revised checkpoint includes the browser
OpenAPI contract, original-policy receipt expiration proposals and regressions.
That API-only checkpoint contained no authorization or persistence runtime
predicates. Its evidence is distinct from the later runtime checks below.

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
schema checks, full Ruff and strict mypy81. That API review checkpoint contained
no runtime authorization/persistence predicates.

The exact fd6bac2 API source passed all 2,600 tests, including 177 WORLD1 cases,
full Ruff/format checks, strict mypy81 and 1,201 external schema checks. The
owner-readable verification index and logs remain outside the checkout, bound
to that source/tree. The subsequent 52ba4ee retention clarification changed no model, schema,
predicate, test or permission. Runtime predicates and hosted validation were
separate later gates.

## Historical shared-boundary checkpoint: 83d304c

The first runtime unit added the complete browser-world capability guard and
extracted incomplete current-human/workspace checks already used by C2. Existing
product permission branches, cookie/session duplicate bindings and service/run
scope ceilings remain mandatory. Ordinary world writes require Origin/CSRF;
owner preview mutations additionally require recent authentication only after
current identity, membership, workspace and role checks. Owner metadata reads
do not require recent authentication.

Strict JSON decoding and incremental SCI canonical hashing are shared with
COMP1. COMP1 keeps its existing distinct raw caps, configured depth/node limits
and JSON-mode validation. WORLD1 uses fixed depth 32 and 1,000,000 lexical node
starts plus its configured byte bounds. These utilities are incomplete and
must only process private material after a complete current-authority guard.
Canonical encoding preserves signed zero and the existing ASCII escaping.

That checkpoint did not yet implement world/version or preview persistence
proposals, disclosure, run selection or their recovery paths. No HTTP, database,
browser serializer or production readiness is claimed.

## Runtime predicates and trust boundary

The reviewed runtime is in `world_versions.py` and `world_previews.py`.
Its exact-source evidence and remaining hosted integration gates are recorded below.
These are pure proposals and projections, with no HTTP routes, SQL, locks,
session verifier, cleanup worker, streaming client or browser implementation.

Every complete entrypoint checks current authority before inspecting its private
record/lookup arguments. A hosted producer must also authorize before fetching
or parsing those private arguments, then recheck the same current transactional
snapshots before commit/delivery. Passing a typed snapshot does not authenticate
its producer or establish currency.

- `propose_world_version` accepts actual raw author-request bytes, applies the
  complete `worlds:write` guard, then strictly parses the request. The **whole
  raw author request** must fit `max_definition_bytes`; the converted CORE
  definition separately fits that canonical byte cap. This conservative whole
  request cap includes title/envelope overhead. Both use the configured limit,
  without truncation. Duplicate decoded keys, nonfinite numbers, invalid UTF-8,
  excessive nesting/node starts and invalid supported laws are rejected.
- A fresh version returns a private `WorldVersionDecision` containing the
  atomic commit proposal and safe result. A live exact receipt returns the
  original safe result with `commit=None`, even after later versions exist.
  Retry allocation IDs are ignored. Actual canonical identities preserve
  signed zero across retained request/definition/space/view joins.
- `read_world_version`, `read_world_head` and `read_world_page` expose only
  safe world metadata. Pages obey current count/byte bounds and exact tenant
  scope. Cursor resolution and bounded database query production remain hosted
  obligations; this unit does not implement pagination storage.
- `propose_preview_mutation` checks current browser owner authority,
  Origin/CSRF and recent authentication before parsing or private recovery.
  New issue/renew additionally requires the current eligible human recipient.
  Renew cannot change version, recipient generation/incarnation or issuer;
  expired/revoked grants require a new grant ID. Revoke needs no eligible
  recipient snapshot and may happen after grant expiry.
- A still-retained, unexpired preview receipt with exact current/latest closure
  can replay original **metadata** to the current authorized owner after the
  recipient left or the grant expired/revoked. This does not reissue, extend,
  reactivate or disclose a definition. The old recipient snapshot is historical
  provenance on this path, not current issuance authority.
- `read_preview_grant` and `read_preview_page` are owner-management reads
  without freshness. `disclose_world_definition` separately checks the actual
  current recipient, exact immutable version, grant generation/incarnation,
  expiry, permanent revocation and current allowed reader roles. Neither
  creator/owner status nor run completion substitutes for that grant. Only
  customer-authored definitions qualify.
- Policy hashes retained on grants/receipts are provenance. Current allowed-role
  checks apply on every disclosure; a still-live unchanged-ancestry grant may
  work again after a temporary role-policy denial is removed. The current TTL
  ceiling governs new issue/renew only; it does not rewrite an old expiry.
- `select_world_for_run` composes unchanged current C2 `runs:create` authority
  for browser humans **or workspace services**. It binds actual immutable
  definition/space, catalog eligibility, original creation request/digest and
  current original ownership. Budget must equal the authored version's budget.
  Existing later creation-result status/revision is allowed while its canonical
  space remains exact. This is new-run admission only; catalog withdrawal does
  not add a new check to already admitted worker/model replay.

The private decisions retain the current authority and policy hashes as
transaction comparison values, not signatures or authorization tokens. Producers
must compare actual current session/principal generations, membership
incarnation/revision, workspace owner/quarantine state and policy under the same
transaction. Fresh grant writes also recheck recipient state and exact prior
grant revision. Version writes CAS the exact head and enforce globally unique
opaque version IDs plus unique per-world version numbers. Allocation IDs and
idempotency namespace IDs are never recycled. A conflict requires scoped
readback and closure validation, not a second allocation.

Version recovery binds the retained target, current head and current immutable
commit, including all supplied predecessor identities and monotonic version/time history.
Grant recovery binds the exact current grant/latest commit and historical
receipt, with immutable target/recipient/issuer and monotonic revision/time/expiry.
These bounded witnesses rely on authoritative immutable records previously
produced by validated atomic transitions; they do not independently reconstruct
every intervening historical transition or detect coordinated corruption of all
trusted database projections. Full receipt plus expired-key witness, missing
required current closure or contradictory projections fail closed.

An exact expired-key witness returns the deliberate expiry failure after current
authority/scope/body/time checks. If all resource witnesses are absent after
later retention/deletion, it still prevents key reuse; that failure-only path
does not authorize deletion or report resource success. Supplied partial or
contradictory resource witnesses fail recovery. Current resource transition
provenance remains required independently of response-receipt retention, as
described above. No cleanup producer is implemented here.

Internal `receipt_expired` and `recovery_required` map to existing public
`incompatible_state`; `policy_unavailable` maps to
`temporarily_unavailable` (503), `reauthentication_required` to
`unauthenticated` (401), and `ambiguous_credentials` to
`invalid_request` (400). Adapters use fixed safe messages, request correlation
IDs and no-store headers; exception details must not contain hidden definitions.

The Python CORE/browser codec and canonical checks are not evidence of a
lossless JavaScript serializer. Browser consumers must preserve string uint64
seeds and signed zero. Ordinary `JSON.stringify` can lose signed zero and is
not the frozen Python/SCI canonical byte profile. WEB1/SP-01.e consumer
conformance remains separate; no new hash dialect is introduced.

## Reviewed runtime evidence

The final runtime source is
`2b882fe3d26879cd7fc1abe7ca623833aef52372`
(tree `bd387b6bbf4f86a8a8f70617d65a10ec8f607b5f`). It passed
2,783 repository tests, including 360 WORLD1 API/authority/runtime cases.
The broader focused compatibility selection passed 557 cases, including
existing C2 and COMP1 consumers. These selections overlap and are not additional
independent test totals. Full Ruff/format checks (127 files), strict mypy
(87 source/test/example files), 1,201 external schema fixtures and the configured
Bandit threshold passed.

Independent lead, Platform and Quality review accepted that exact runtime.
Their checks covered current authority before poisoned private inputs,
historical metadata replay, canonical signed-zero/uint64 identity, current policy
changes, browser/service run selection, supplied version ancestry, and grant
lifecycle reachability. Targeted guard mutations were detected. These are
bounded contract/proposal checks, not deployed authentication or recovery drills.

Review found that comparing a historical receipt only with the latest state
missed contradictions in already-retained predecessors. The repaired version
checks compare every supplied relevant version-record pair, including the
historical receipt's parent and the current head's parent. They bind known
opaque IDs to their implied ordinals, require exact canonical identity at equal
ordinals, enforce adjacent parent links and retain nondecreasing creation times.
They reject reuse of an earlier own or parent ID at another known ordinal.
No additional history is fetched. Final composition review also verified the
historical receipt's own parent/version pair, completing all six pairs among
the four supplied records. Fresh append proposals reject newly allocated IDs
already present in the supplied current version/parent records, including their
parent references. Replay still ignores newly supplied allocation IDs. Global
uniqueness for unseen versions remains a required atomic database constraint.
The earlier 9267733/f23f92f evidence is retained separately; its initial acceptance
was qualified by these final composition findings and superseded by the source
identified above.

Grant history compares the historical outcome with both the current transition's
predecessor and outcome. Equal revisions require exact canonical record/commit
identity. A later state cannot follow revocation. For revision distance `d`,
a still-live outcome requires at least `d` seconds of expiry growth because
each intervening renewal strictly increases an integer expiry; a final revoke
requires at least `d - 1`. Equal transition timestamps remain valid, and a sole
revocation can preserve expiry. These checks reject contradictions in supplied
bounded witnesses without claiming to authenticate all unprovided history.

Offline wheel/sdist construction and the package allowlist passed at the same
runtime source. A temporary wheel-only target installation, using the existing
pinned dependency environment, successfully created a world, issued a preview
grant and disclosed the definition to its exact current recipient. The safe
creation result omitted the definition, and the uint64-max seed round-tripped.
The temporary installation was removed. This proves the packaged callable path,
not HTTP/database enforcement or a deployed browser client.

Owner-readable evidence remains outside the checkout under
`/home/serenapei/.local/state/strange-physics-reviews/world1-author/`.
The `2b882fe3-full/index.json` SHA-256 is
`17463ebca6fec18b349f58b6ec1df0b9312a2274dc476896282281d01a0ef95b`;
the `2b882fe3-package/index.json` SHA-256 is
`8b4c7e9fc8ec6b5f3dd82dd8579ed6e863586d7f5d8f83a488ef7e072ae4994f`.
They bind exact source/tree, commands, logs and retained archive hashes.
Directories are 0700 and files 0600, with a diagnostic review date of 2026-11-19.
Earlier checkpoints and diagnostic failures remain separately identified;
they are not substituted for the final result.

The final author handoff changes documentation only; runtime predicates and
validation semantics remain those of the reviewed source above. PR #95 merged
as caeb58a with the same tree as reviewed e42fb87. All four applicable PR
CI39391162963 and all five protected-main CI39391431584 jobs passed;
the unpublished candidate was checksum/provenance/source verified privately.
WORLD1 is accepted. SP-01.d remains open for WEB1 stream/snapshot/replay
contracts; live hosted producers are separate later implementation work.
