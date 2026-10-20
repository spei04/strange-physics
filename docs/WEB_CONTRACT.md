# WEB1 — committed run streams and bounded replay

Status: typed API, intrinsic joins and synthetic fixtures for review. Runtime
authorization/recovery predicates, durable HTTP/database/object producers, a
network SSE server, browser parser and replay UI are not implemented by this
checkpoint. This is the second independently reviewed unit of SP-01.d; WORLD1
is already integrated. CORE, SCI, ART and C2 messages remain unchanged.

## Surface and information boundary

Five GET operations are specified in `contracts/web.openapi.json`:

| Operation | Result |
| --- | --- |
| `streamRunEvents` | fetch-stream SSE containing `EventDelivery` |
| `getRunSnapshot` | a requested immutable capture, or a new atomic capture |
| `getRunHistoryPage` | one hash-linked page belonging to the selected snapshot |
| `getRunReplayChunk` | the exact immutable generation pinned by that history |
| `getRunExperimentRecord` | the complete CORE record selected by a committed event |

The public schema roots are explicitly enumerated by `web_json_schema()`.
Run events expose only captured RunView, an experiment record reference, a
checkpoint ID/through-index, or the frozen ModelReceipt. Experiment records
can legitimately report scientific failure; that is distinct from an incomplete
object download. There is no generic arbitrary-object read endpoint.

Private cursor lookups, policy, storage locators, readback evidence and supplied
binding models are not public request/response roots. Their validation does not
authenticate a producer or confer access. Hidden definitions, private definition
hashes, evaluator labels/results, preview-recipient metadata and worker/session
authority cannot become event payloads. WORLD1 granted truth disclosure uses its
separate currently authorized route and never consumes this safe sequence.
Even an owner or author receives the same agent-safe event projection here.

## Current authority and ordering

Every later complete read boundary must invoke the existing C2
`authorize_product` with `runs:read`, accepting only a current human browser
session OR a current workspace service authority. The service must satisfy its
current role, scope, key/grant ancestry and ceiling. Reject ambiguous cookie and
bearer presentation, user-bearer substitutes and worker run credentials. The
draft workspaceBearer description is reconciled to service identity; browser
human access uses sessionCookie on explicitly permitted routes.

Use accepted current browser Origin/session/principal-generation/membership/
workspace checks. These GET operations do not introduce mutation CSRF or recent
authentication requirements. In particular, no RunLease, live worker, current
attempt, write permission or running-state requirement may be added. Queued,
completed, failed, cancelled and expired historical runs remain readable when
current read authority permits.

Current identity and workspace authorization precedes every private cursor,
snapshot, catalog or archive lookup and every distinguishing 404/410/recovery
response. Recheck actual current authority and required projection/retention
policy before each event/body batch and on reconnect/resync. Reusing a stale
authority object across batches is not a fresh check. Revocation or policy loss
blocks the next batch; cursor possession, a retained snapshot and a successful
earlier batch never authorize subsequent bytes. Required policy unavailability
maps to existing `temporarily_unavailable`/503, with no permissive default.

## Sequence, identity and SSE encoding

`StreamNamespace` binds workspace, run, `agent-safe.v1` projection and the
`strange-physics.run-event.v1` event schema. The first committed event is **0**.
Empty head/snapshot watermark is **−1**, with retained start **0** and public
snapshot resume cursor **null**. Safe event sequences never reset across attempts,
retention, restart or archive movement; private events cannot introduce gaps.

Every new public integer counter/time is strict, excludes booleans, and lies in
0..2^53−1; only an explicit empty watermark permits −1. Timestamps are integer
Unix seconds. Existing RunView counters already have this safe bound and are
not narrowed. Reaching the sequence ceiling requires an explicit producer
failure before the next append; never wrap, round or reset the namespace.

An immutable `RunEvent.event_id` is distinct from its opaque resume cursor.
`EventDelivery` carries the actual event, `message_sha256(event)` and
`resume_cursor`. A server frame uses this exact canonical encoding:

```text
id: <resume_cursor>
event: <event.type>
data: <canonical EventDelivery JSON>

```

The fixture codec emits UTF-8 LF-delimited bytes, including the terminating blank
line. Identifier syntax is bounded ASCII and excludes CR, LF and NUL; event type
is a closed literal. Do not concatenate unchecked input into raw SSE fields.
The canonical JSON data line escapes embedded data characters; that escaping
does not excuse unsafe raw id/event fields.

`id` therefore records an opaque committed cursor, not a numeric sequence or an
arbitrary caller token. A private `EventCursor` binds its exact namespace,
sequence, event ID and canonical event digest, plus issue/expiry. A nonnegative
cursor cannot replace event identity with only a snapshot hash. A snapshot cursor
additionally binds actual snapshot ID/hash; a private −1 start anchor may have no
event. Currency, namespace lookup ownership and expiry are runtime/producer
checks, not implied by parsing.

| Input/state after current authorization | HTTP outcome |
| --- | --- |
| Last-Event-ID absent and sequence 0 retained | start at 0 |
| Last-Event-ID absent but sequence 0 no longer retained | 410 resync |
| Empty, malformed, overlong or framing-control token | 400 invalid_request |
| Unknown token or foreign namespace | 404 not_found |
| Known expired token or retained position no longer resumable | 410 resync |
| Known cursor beyond the authoritative committed head | 409 incompatible_state; recovery/diagnosis |
| Supplied partial/conflicting trusted closure | 409 incompatible_state; recovery |
| Current authentication/permission lost | 401/403; stop |
| Quota/admission throttle | 429 with bounded decimal-seconds Retry-After |
| Required current policy/service unavailable | 503 temporarily_unavailable |

Do not clamp, skip or blindly retry a beyond-head cursor. Inspect HTTP status and
content type before parsing event-stream bytes. The 410 body is
`ResyncRequired`: existing cursor_expired error, scoped opaque snapshot ID and
closed operation IDs for snapshot/history, never a URL or permission-bearing
storage link. Fetch-stream is the supported contract; native EventSource
compatibility is not promised.

Exact repeated event ID/sequence/digest is harmless at-least-once delivery; any
different identity at the same position or reused ID at another position is
corruption. A later client must retain a bounded verified duplicate window and
resync when it cannot verify an older duplicate. No partial frame is applied.
Comment heartbeats have no logical id/cursor and cannot change durable position.
There is no second noncommitted control-event dialect.

## Wire and resource bounds

Reference ceilings below are versioned maxima. `WebPolicy` must be supplied by a
trusted current producer and may select stricter limits; it also supplies total
history page/byte allowances, a delivery deadline and cursor lifetime. There is
no deployment default or client-authored policy.

| Material | Exact reference bound and accounting |
| --- | --- |
| One SSE event | 65,536 UTF-8 bytes for the complete id/event/data frame and delimiters |
| SSE batch | ≤100 events and 1,048,576 bytes for concatenated complete frames |
| Replay chunk | ≤256 consecutive events; ≤4,194,304 raw bytes and canonical typed JSON bytes |
| History page | ≤128 refs and 1,048,576 canonical JSON bytes including array/object punctuation |
| Scientific object | 4,194,304 actual raw bytes, depth 32 and 1,000,000 lexical nodes |
| Each raw object delivery batch | ≤65,536 bytes, with a new current authorization check |

JSON body producers emit the declared canonical representation for pages and
snapshots; bounded raw request/response parsing must reject excess before large
decoding/allocation. Archive/scientific artifacts retain separate raw SHA,
generation and size even when their encoding happens to be canonical.
Fixed parser depth/node limits are not client knobs. Aggregate history byte/
page/deadline accounting is independent of these per-message ceilings. Missing
policy, deadline/cap exhaustion, interruption and missing pages/objects are
explicit incomplete outcomes, never truncation or success over surviving data.
No compression, range-request protocol, direct storage URL or unbounded page
materialization is specified in this version.

The earlier constructive large-record fixture measured 1,779,612 canonical bytes
for one accepted eight-particle/2,001-frame CORE record, requiring 28 batches at
64KiB and fitting the 4MiB body ceiling. It cannot fit in a 64KiB SSE frame.
That is constructive compatibility evidence, not an exhaustive maximum, memory
bound, load test or hosted performance claim. Later body predicates must test
actual maximum-shape material and raw whitespace/encoding expansion.

## Immutable capture and paged archive closure

`RunSnapshot` captures one RunView revision, safe-event watermark, immutable
history root and resume cursor atomically. Its identity is opaque. The captured
state remains valid when the current run subsequently advances; current viewer
authority is rechecked independently. A later current RunView must not be required
to equal the historical capture.

A nonempty `HistoryManifest` pins the namespace, captured run revision,
[0,watermark] range, exact final event identity, page/chunk counts, total raw
chunk bytes and first `HistoryPageRef`. An empty manifest has zero counts/bytes,
no page or event, and public resume cursor null.

Each immutable page is bounded, identifies its manifest and page/chunk offsets,
contains contiguous `ReplayChunkRef` descriptors, and hashes its successor.
This linked-page root avoids loading an unbounded descriptor list. A descriptor
pins raw ART identity and canonical typed chunk identity independently, exact
range/count and first/last event identities. Actual `ReplayChunk` repeats its
namespace/range and contains consecutive uniquely identified events.

`HistoryPageBinding` validates the supplied root/page/immediate-predecessor
hash and range joins, including the root identity of any supplied page 0.
Known root/predecessor/current/next page IDs must denote the same ordinal; the
known final event participates in supplied event-identity checks. Prefix/suffix
page, chunk and event offsets must be feasible for nonempty bounded missing
material. Total raw bytes must lie between known bytes plus one byte per missing
chunk and known bytes plus the maximum size per missing chunk, becoming exact
when all chunks are supplied. These are necessary feasibility checks, not proof
that the missing objects exist or contain valid typed chunks. It does not prove missing earlier pages.
The later reader must walk from the exact root in order; enforce aggregate
limits/deadline; reject repeated pages, missing/overlapping/reordered ranges,
wrong hashes/generations, duplicate conflicting events and total mismatches;
and validate every actual typed chunk. Only a complete verified captured history
may be labeled complete. Resume live strictly at watermark+1. Do not advance a
durable verified prefix across a missing page/chunk or incomplete body.

`CursorLookup` deliberately permits absent/partial trusted projections so
runtime recovery can distinguish them from proven absence. The types never
normalize conflicting or missing evidence into a fresh cursor or successful
history.

## Scientific and object identity

An experiment.committed event contains `ExperimentRecordRef`, never an inline
unbounded trajectory. This joins operation ID, accepted experiment ordinal,
completed/failed scientific status, immutable ART reference and canonical
`message_sha256(ExperimentRecord)`. Raw object SHA, canonical SCI identity,
event identity and cursor identity are different domains.

Before any scientific bytes are delivered, the later bounded reader must:
1. Establish current runs:read and the exact committed safe event.
2. Load the exact available, agent-visible, tenant/run-owned ART catalog generation.
3. Enforce raw byte limits and verify complete actual raw SHA/size/generation.
4. Strictly parse the bounded CORE record, rejecting duplicate keys, nonfinite
   numbers, excessive depth/nodes and malformed UTF-8.
5. Recompute canonical identity and join operation/index/status to the event.
6. Deliver bounded raw batches while rechecking current authority.

`ExperimentRecordBinding` and `ReplayChunkBinding` check supplied typed material
against exact catalog/readback/ref identities. They do not prove that a supplied
typed object was decoded from the supplied stored bytes; the actual-byte reader
is a mandatory future producer. Available readback flags are not a hostile-code
sandbox, signature or permission.

Scientific failures remain complete failed records and may be replayed; missing
or interrupted transport is never converted into such a record. Full body
validation precedes first delivery, and a client must withhold completion until
all declared bytes/integrity checks are satisfied.

Python canonical serialization is the existing SCI profile, including default
fields, escaped Unicode, typed float spelling and signed zero. An ordinary browser
JSON.parse → JSON.stringify roundtrip is not equivalent: parsing preserves −0,
but stringification loses its sign. Raw byte SHA can be
verified over the exact received bytes; semantic identity requires preserved
canonical event/record bytes or a separately conformance-tested lossless typed
codec. This Python fixture codec does not establish browser implementation proof
and does not introduce a new SCI hash dialect.

## Producer, client and review obligations

The durable producer must allocate each safe sequence exactly once under the
same transaction as the public projection/outbox; enforce scoped sequence and
global opaque event-ID uniqueness; retain immutable payload/hash identity; and
bind snapshots/head/archive watermarks to one consistent read. Event times must
be nondecreasing in committed sequence; same-second commits are valid. Restore
must preserve original namespace/sequence/IDs and reapply revocation/tombstones
before access. Cleanup must not delete chunks/identity witnesses still required
by retained snapshots/cursors; unavailable required history yields resync or
explicit incomplete recovery.

Later fetch-stream clients require bounded incremental UTF-8/SSE parsing across
arbitrary network chunk boundaries, exact cursor/sequence checks, abort on
revocation/navigation/deadline, and bounded reconnect/backoff with Retry-After.
Reconnect uses the last completely verified/applied cursor, never the latest
received partial id. Client retry policy must respect the overall deadline and
must not turn 401/403 or inconsistent-state409 into blind retry. SP-01.e owns
contract-consumer fixtures and mock seams; these types do not implement a
production parser or browser integration.

Review checkpoint commands are focused pytest, Ruff/format, strict mypy and the
external contract validator. Synthetic examples are not storage/authentication,
scientific I1, load, recovery-drill or hosted readiness evidence. Runtime
authoring followed acceptance of the immutable API checkpoint by the lead,
Platform and Quality. Accepted pure predicates still do not supply hosted producers.

## Initial API validation evidence

The initial immutable API checkpoint `3b01cfca44d61127927ca396ae54a04f06a0026d`
passed 2,928 repository tests, including 145 WEB1 cases and an overlapping
371-case WEB/control/session selection; Ruff/format (130 files), strict mypy
(89 source files), 1,373 external schema checks and its original author Bandit selection. The exact CI
security-command scope is distinguished below.
This evidence belongs to that exact source. Independent review then identified
bounded supplied-page/manifest feasibility joins and response-schema constraints;
the replacement preserves the public fields and adds regression cases. The
410 schema now enforces cursor_expired/nonretryable/no-operation, and all WEB1
Retry-After schemas reject non-ASCII-digit framing characters explicitly.
Replacement checks and independent review are recorded separately; neither API
checkpoint establishes runtime authorization or hosted readiness.

### API review completion and historical first partial runtime unit

The repaired API source `c066900b875c4393f74d6e34b7b9fec09e15a83f`
passed 2,962 full tests, 405 focused WEB/control/session cases (179 WEB),
Ruff/format over 130 files, strict mypy over 89 files, and 1,431 external
schema checks. Its original author security command was the narrower
`bandit -r src -ll -ii`; the lead separately checked the exact CI command
`bandit -r src scripts -ll`. These evidence scopes must not be conflated.
All three independent API review scopes accepted the repaired page-history,
resync and header contracts before runtime authoring.

The first runtime unit implements `authorize_viewer`, `resolve_cursor`,
`read_snapshot`, and `prepare_event_batch`. These are pure decisions over
trusted current projections, with no HTTP server, database adapter, cursor
minting or network delivery. Every boundary rechecks current browser or
service `runs:read` authority before private lookup or retained-state inspection.
The private viewer context includes actual transport-presence evidence for
both branches: a service authority object alone does not prove that the HTTP
request omitted a session cookie. Worker credentials and user bearer
presentation remain excluded. Viewer reads have no worker-lease, running-state,
write, mutation-CSRF or management-freshness prerequisite.

A current head and current run come from the same authoritative snapshot and
therefore have the same run revision. A historical capture may precede them;
its immutable space is compared by canonical hash, while later run revision,
reservation progress and status remain valid. Equal revisions require exact
canonical RunView identity. Supplied event/cursor/snapshot contradictions fail
closed. Unknown/foreign cursors differ from malformed, expired and beyond-head
positions only after current authorization. An expired response requires an
actual scoped current resync snapshot; a missing required producer witness
cannot invent one.

Private stream state records the last verified watermark, a bounded 256-event
duplicate window, policy identity, cumulative wire bytes and the original
deadline. Exact duplicates in that window do not advance or consume delivery
bytes; an old duplicate outside it requires resync. Current policy changes
invalidate that state rather than resetting its budget or deadline. The empty
watermark −1 and terminal MAX_SAFE watermark can both produce a lawful empty
poll without emitting an out-of-range next sequence.

At the historical partial checkpoints through `ac70f69`, this unit did not implement complete actual-byte artifact validation,
incremental full history verification or reauthorization between raw body
batches. The following material unit supplies those predicates. The history walk must
retain every consumed page/object/event identity, with an internal 8 MiB
canonical-metadata ceiling additionally capped by policy.max_history_bytes.
That separate metadata bound limits locally verifiable history; it is not a
hosted RSS/load claim. Page bytes plus raw chunk bytes have their own cumulative
delivery budget, and raw chunk totals separately bind the manifest. No index
entry may be silently evicted to declare a history complete.

The first partial-runtime review additionally requires actual supplied event time
to precede or equal both its cursor issuance and any supplied snapshot capture.
Known cursors beyond the current head use the specified incompatible_state/409;
contradictory retained witnesses use recovery_required/409 internally. Optional
snapshot tokens are validated after current authority and before private lookup.
The hosted producer must also preserve the at-most-30-second idle authority
recheck obligation in IDENTITY_RUN_CONTRACT and RUN_CREDENTIAL_CONTRACT, as
well as mandatory checks before every payload. This unit implements no idle
loop, timer, connection manager or network producer.


### Material runtime review checkpoint

`web_delivery` adds `prepare_experiment_body`, `prepare_replay_body`, and
`deliver_body_batch`. Preparation verifies the complete bounded raw object before
returning private `VerifiedBody` state: current run-owned agent-visible available
ART catalog/readback, exact immutable reference and raw SHA/size, strict UTF-8 JSON
with depth 32/node 1,000,000 limits, and actual typed semantic identity. Scientific
records additionally bind the committed event's operation, index and status.
A completely verified failed experiment remains a failed scientific record;
interrupted or invalid transport never becomes a completed record.

Each body batch rechecks current viewer authority, actual current catalog identity,
request/configuration identity and the original deadline before exposing at most
64 KiB of raw bytes. Renewed readback of the same catalog is allowed. Policy
changes invalidate state; they do not restart its deadline or budget. Private
state is an authoritative producer input, not a client offset, range protocol,
read grant or bearer capability. Atomic state/CAS and current authorization at
real delivery remain hosted producer obligations.

`web_history` adds `begin_history`, `read_history_page`, `accept_history_page`
and `accept_history_chunk`. A walk starts from the actual immutable captured
snapshot/root. Each page follows the exact preceding page hash, ordinal and
chunk offset; each chunk follows the exact descriptor, raw ART identity and
consecutive event interval. All consumed page IDs, object identities
`(artifact_id, generation)`, and event IDs remain in a bounded private index.
Nonadjacent reuse fails rather than disappearing from a sliding window. Event
times and embedded historical RunViews must agree with the captured snapshot;
later current run revisions/status/progress remain allowed under the canonical
immutable-space join.

Completion requires the full ordered page/chunk/event counts, final watermark
and event identity, terminal page, and exact manifest raw chunk-byte total.
Missing, reordered, corrupt or over-budget material raises an explicit failure
without advancing the immutable prior state. A single-page/body lookup validates
its supplied authoritative membership projection; only the complete walk proves
all consumed chain relations. Neither interface authenticates arbitrary caller-
constructed trusted projections or performs a database lookup.

The delivery budget charges actual raw page UTF-8 bytes plus actual raw chunk
bytes; the manifest's chunk-byte total counts only the latter. Separately, each
retained identity is charged by its documented canonical accounting line, with
an 8 MiB internal ceiling additionally capped by `policy.max_history_bytes`.
Growth is checked before extending the retained index, with no eviction or
budget/deadline reset. These limits bound this local verifier's supported
history envelope; they are not a hosted memory/load claim.

At material checkpoint `96f4b5779a0d5116b06562b440d6e5303250f11a`,
the initial selection passed 312 WEB tests (179 API, 83 stream/replay,
50 material), full `mypy src tests examples` over 95 files, and Ruff. The full
mypy invocation exposed the partial checkpoint's test-module import convention:
imports now use the same bare test-module names as repository-wide discovery,
without suppression or configuration weakening. A legal CORE maximum-count
fixture with eight particles, 2,001 frames and long finite numeric values is
1,757,646 canonical bytes and reconstructs in 27 bounded body batches. It is a
synthetic shape check, not an exhaustive serialization maximum, simulated
trajectory, ObservationBundle admission, or RSS/load result. Full repository,
package and independent material review results are recorded separately after
this checkpoint; no hosted HTTP/object-store producer is implemented here.


### Reviewed pure-runtime composition

Independent review of the material unit identified two supplied-capture joins:
a replay body's embedded RunView must be compatible with the captured RunView,
not merely the later current run; every consumed event that shares the captured
root's final event ID must also match its exact sequence and canonical digest.
The repaired preparation path enforces both, including interior chunk events.
Valid earlier/equal captures and later current progress remain supported.

Author self-review then found that a whole-page request hash did not distinguish
two requested chunks on that page. The private replay request binding now covers
its purpose, exact requested snapshot ID and actual canonical snapshot hash,
canonical page-binding hash, descriptor index, and exact requested ArtifactRef.
Swapped prepared state is rejected even when both objects independently validate.
This is internal request-state integrity; it introduces no public hash dialect,
invocation permission, or change to SCI canonical identity. Scientific-body
request semantics remain unchanged.

Lead, Platform and Quality accepted runtime source
`85c0a98a3cf20e7063564e73b0625694d162ba38` after the capture and request repairs.
The earlier `93902d3` acceptance was qualified by the subsequently discovered
request-binding gap; it must not be presented as the final composition result.
The WEB schema status now describes reviewed pure contracts/predicates with
hosted producers pending. This annotation changes no field, wire dialect,
CORE/SCI/ART/C2 interface, deployment state or authorization policy. Final exact
source checks and their evidence identity follow separately.


### Final author validation evidence

Exact source `f2d1068aaa8ddfc3f65d867121ff9362314670b0` (tree
`85a23b26cd43a0adb3e2904c87d3713ff1a5d9e3`) passed 3,104 repository tests,
including 321 WEB cases (179 API, 83 stream/replay, 59 material). Ruff and format
checks passed over 136 files, full `mypy src tests examples` over 95 files, and
1,431 external schema fixtures/references. Static security used the exact
configured command `bandit -r src scripts -ll`. The prior annotation checkpoint
`00800555` passed the same 3,104 tests but failed a 105-character status line;
its retained failure was repaired by formatting only, then all final checks
were rerun on the source identified here.

The offline wheel and source archive match the explicit source allowlist.
The project wheel was installed without dependencies into a temporary private
target and exercised using the existing pinned interpreter/dependencies and
synthetic test fixtures. All 21 imported project modules resolved inside that
installed target. Actual cursor/event, scientific-body, full-history,
replay-body and exact-request substitution checks passed. The target was
removed after verification. This is an installed-project packaging smoke,
not a newly provisioned isolated runtime or a hosted producer test.

The sealed owner-only author index is
`/home/serenapei/.local/state/strange-physics-reviews/web1-author/f2d1068-final/index.json`,
SHA-256 `a5506d5d53a8f27565ad214af15075167fecf6aefb2ae1ff2a5b7ae596a734a2`.
It binds source/tree, exact commands/statuses, logs, package hashes, pinned
manifests/runtime versions and temporary-install removal. Reproducible
private diagnostics have a 2026-11-19 review date; required release evidence
remains subject to its retention policy. Earlier API/partial/material evidence
and qualified findings remain separate rather than being relabeled as final.

Independent acceptance scopes overlap and are not an aggregate test count.
The lead's large scientific-body checks covered a distinct 1,779,612-byte record
with matching eight-particle run space, exact browser/service slicing and
midstream revocation. Platform and Quality separately reviewed supplied
history/capture/request identity, aggregate budgets, authority ordering, strict
parsing and per-batch checks, including targeted guard mutations. All accepted
the repaired pure-runtime composition before this final author pass. Exact
integrated PR/main CI, network dependency auditing and hosted producer/runtime
readiness remain separate lead-owned gates; this document does not assert they
have completed for this authored checkpoint.
