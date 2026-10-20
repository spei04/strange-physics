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
hash and range joins, available boundary identity consistency, and totals when
the complete chunk set is present. It does not prove missing earlier pages.
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
fields, escaped Unicode, typed float spelling and signed zero. Ordinary browser
JSON.parse/JSON.stringify is not equivalent and loses −0. Raw byte SHA can be
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
predicates remain held until the immutable API checkpoint is accepted by the
lead, Platform and Quality.
