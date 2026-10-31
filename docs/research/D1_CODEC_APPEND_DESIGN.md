# D1 codec append boundary: proposed next source slice

Status: source design only. No adapter, activation, file write or primitive was
executed for this proposal. The next unit is a synchronous, fake-callback-tested
append state machine; actual metadata retention and installation remain separate.
The fixed 55,100 calls, 110,201-event ceiling, 16 MiB proposed transcript partition
and 64 MiB expanded logical ceiling are unchanged. None is a new allocation.

## Exact dependencies and responsibility

This design reads these immutable sources, rather than treating similarly named
working files as qualified implementations:

| Component | Exact source / content identity |
| --- | --- |
| Recorder | `6d3edf1fbc6c01c97ac84bc0a06231b4199a83e8`, `tests/d1_primitive_recording.py`, SHA256 `b7ac0ec37c1e847d8e076abf5d27a7df30fffa8316d473f5a7631fb46f87f185` |
| File sink | `e76284a3c5e950783c4d25c6cb14d22b50398d11`, `tests/d1_primitive_sink.py`, SHA256 `2a72b57fe71a81f5ec44dfd38572c115cd1201ae1311422e577d00a02c14ac96` |
| Codec contract | `af61389b571d3f6f0f169b4cadb79a409f9528d5`, [contract](D1_PRIMITIVE_CODEC_CONTRACT.md) |
| Table | `ca6caa20909029a882835811fe6bbea0e0c5e781`, [table boundary](D1_PRIMITIVE_CODEC_TABLE.md) |
| Event conversion | `20684e3e95e61e9b1b1861596f27a68860ba5a9b`, helper SHA256 `58f23a806cca8e579ce80a1430af7f5a4749481c8bc05788ed8b3c32f71389e9`, [pure codec](D1_PRIMITIVE_CODEC.md) |

`PrimitiveRecorder._emit` reserves the complete original raw Event and marks its
delivery unknown **before** invoking its append callback. Only a normal callback
return changes that record to confirmed. A raised callback never causes a retry.
`PrimitiveFileSink.append` reserves the complete physical line before I/O and
returns only after its bounded write, file identity checks and file fsync succeed.
Its own failure consumes further append opportunities, retaining partial written
bytes and the full reservation. A callback return remains a source-owned retention
promise; it is not proof of a crash-surviving filesystem or authentic execution.

The bridge must preserve both meanings. Logical retention of the exact raw Event
through compact bytes is conditional on retained T and exact replay; byte equality
alone cannot replace the required metadata acknowledgements. It returns normally
for a compact line only after conversion of the actual recorder bytes, exact expansion equality and
one successful physical append. Consequently intent retention precedes the
recorder's primitive callback, and return retention precedes value handoff. It
never invokes a primitive, recreates a cursor or repeats a sink append.

## Small proposed API and ownership

Implement a private `CodecAppendBridge(table_raw: bytes, context_raw: bytes, *,
append: Callable[[bytes], None])` with `append(raw: bytes) -> None`, an immutable
bounded diagnostic `snapshot()`, and a one-use, no-I/O `finish()` that consumes the
bridge. Naming is proposed; this is not an installed recorder callback.

Construction accepts exact immutable bytes, not a caller-constructed TableView,
Conversion, SinkContext or mutable Event graph as validation evidence. Revalidate
T and canonical C, including strict raw types before serialization. C has exactly
the fields emitted by the pinned sink, its schema and derived event/shard/metadata
limits. Reject duplicate/unknown fields, malformed hashes, booleans in integers,
wrong canonical bytes, or inconsistent derived values. Enforce the common run,
recorder, commit/tree, protocol, source-manifest and recorder pins. C's sink pin
and T's codec pin need later S joins; they are not interchangeable fields. Fixed
D1 construction requires `max_calls=55100` and derived `max_events=110201`, not a
caller-selected reduced scientific plan. Small tests simply use an initial prefix.

C's total `max_bytes` includes 20,480 metadata bytes. Its event capacity is exactly
that total minus 20,480. Within the proposed physical partition, C must leave the
three 65,536-byte T/A, temporary-copy and rotation reservations outside its total:
`C.max_bytes <= 16777216 - 3*65536`. The 8,192 failure reserve is within the event
budget, not extra sink permission. Checking this inequality does not admit a run.

The bridge owns only its conversion cursor, bounded event state and callback
reference. It neither constructs nor closes the file sink or metadata writers.
Capture one process/thread owner and reject reentry before parsing or calling the
callback; a reentry fault consumes the bridge. No thread-safe or hostile-Python
sandbox claim is made. A returned diagnostic view cannot be supplied back to
resume or authorize the bridge. Construction failure performs no append.

The outer owner calls `finish()` once after the recorder call has unwound, then
calls the existing sink's `finish()` once in its cleanup path, even after a bridge
fault. Bridge finish cannot acknowledge storage or suppress the original error.
A successfully created sink remains owned even if subsequent activation fails;
constructor failure without a returned sink object instead leaves external
cleanup/unknown facts. There is no destructor-based completion, reopen or retry.

## Two validators and one append opportunity per Event

The existing conversion cursor deliberately does not validate terminal raw Events.
Its `unsupported` result is neither a valid forensic record nor a write permission.
A separate bounded pure raw-Event classifier is required in the bridge module.
Reuse the codec's defining bounded parser and exact Value spelling checks through
explicit internal imports or a narrowly reviewed pure extraction; do not invoke
recorder arithmetic or scientific modules just to validate bytes. Any extraction
must preserve the current conversion API and its existing tests.

The classifier checks the exact Event/Intent/Value/Fault object fields, one LF,
canonical compact sorted-key ASCII JSON, duplicate rejection, depth and bounded
number tokens before conversion, and the 4,096-byte predecode limit. Success
Event shapes still require null fault. Terminal `failed` requires null returned
and a complete Fault; `returned/unavailable` requires a complete intent, null
fault and exactly the recorder's single type-name string. Decimal and binary64
spellings remain lossless. Unavailable type text is never interpreted or imported;
its actual escaped bytes must fit the same Event cap, with no invented truncation.

Fault fields are `ordinal`, `phase`, `exception_type`,
`exception_type_complete`, `call_id`. The fault ordinal is the recorder's fault-list
index, **not** the call ordinal or Event sequence. Preserve it rather than replacing
it with a predicted value. Source phases include preflight, intent_sink, primitive,
return_encoding, return_sink and reentry; fault_retention is a supplemental fault
in snapshots. Validate actual phase/type/nullable-call structure against the pinned
recorder and observed local state, retaining gaps caused by unseen supplemental
faults. The exception name is at most 192 characters, with a strict boolean
completeness flag; do not serialize exception arguments, messages or tracebacks.
The existing bounded integer-token parser remains a representation guard, not
proof that the declared fault happened.

A source-shaped Event outside the fixed codec vocabulary may be retained raw as
contract-failure evidence. It does not become a valid D1 call. This requires the
recorder's broader token/Intent grammar separately from the table's fixed scope
joins. Malformed/noncanonical/oversized raw bytes do not get a blind arbitrary
payload fallback. Reject them, consume the bridge, and leave any missing forensic
record explicit. A later failed Event is eligible only if its complete joins can
still be established; otherwise reject it without a physical append.

For ordinary success, one encode-direction cursor already expands its proposed
wire bytes and compares to the original. Require converted status plus exact
`raw_event == raw` and the pinned table digest before passing `wire_event` once
to the callback. Do not introduce a second running decoder or reconstruct a new
cursor after a write error. A successful callback permits one normal return from
the bridge. Inspection of bytes after an exception never changes that decision.

## Failure transition and the recorder's optional failed Event

Keep bridge attempt state distinct from codec progress: next raw Event sequence,
current and last attempted complete intent, the last conversion result, selected
physical byte count/hash, callback not-entered/returned/raised, and a consumed
terminal-opportunity flag. Copy no unbounded event list into this state.

| Input or failure | Physical action and following state |
| --- | --- |
| Valid compact intent/return | Reserve local attempt, convert once, append once; normal return only on callback success. |
| Source-shaped raw Event fails fixed conversion | At most one exact-original raw append, then raise a dedicated bridge-stop exception; allow only the recorder's one subsequent failed Event. |
| Returned-unavailable | Same raw retention and stop; never hand back an unavailable value. Only one subsequent failed Event may be considered. |
| Failed Event, including primitive failure | Validate against the current/last attempt; at most one raw append, then raise bridge-stop. No further event is eligible. |
| Physical callback raises | Preserve that original exception and unknown delivery; prohibit further physical callbacks. The recorder's failed Event may be classified for diagnostics but cannot restart a stopped sink. |
| Invalid raw envelope, owner/reentry fault or exhausted bound | No arbitrary raw append; stop. A failed Event is not an exemption from parsing, joins or bounds. |
| Any call after terminal opportunity or finish | Reject before callback/I/O; never retry the previous line. |

The existing recorder calls `_abort` at most once per failed call. Its failed
Event sequence is `len(_events)`: an attempted intent/return already reserved by
`_emit` advances that sequence even when its append raised. Thus, after return
conversion has advanced the codec ordinal and cleared its current intent, a sink
failure still requires the bridge's **last attempted complete intent** to validate
the next failed Event. Retain that join until terminal handling is consumed.
Do not compare the failed Event only to the now-advanced codec ordinal.

Conversely, `_emit` can fail its own byte bound before reserving an Event or
calling the bridge. The bridge observes no missing successful line in that case:
the failed Event uses the next sequence actually visible to it. Preflight failures
may supply null intent; a first unseen completed Intent may also be present after
argument validation but before any append. Validate only locally provable joins
and record this lack of an observed intent; never infer a primitive invocation.
A reused/substituted intent or nonconsecutive visible Event sequence is rejected.

The accepted contract requires raw fallback to raise through the existing failure
path. Keep that rule even when the fallback append itself returns successfully.
This intentionally leaves the recorder's RetainedEvent delivery **unknown** and
may add a `fault_retention` supplemental bridge-stop fault. Record separately that
the physical callback returned for these exact bytes. Do not relabel it as a disk
write failure, replace the recorder's first exception, rewrite its snapshot or
claim its unknown record is confirmed. If the physical append also fails, preserve
that original storage error instead of replacing it with the intentional stop.
An exception in later failed-event retention is supplemental to the earlier fault.

This proposal changes no accepted acknowledgement rule. Allowing a normal return
for an already-terminal failed Event would reduce the intentional supplemental
fault, but would be a separate contract revision; it is not proposed here. No new
compact failure mode, retry, cursor rewind or success-after-fallback is introduced.

## Activation remains a separate prerequisite

The fake-callback bridge is conditional on an owned callback; its constructor
cannot establish that the callback is the pinned sink or that files exist.
Before actual installation, the outer resolver must validate actual S and the
actual source/callable/instance bindings, retain T and C, then retain A and bind its
exact bytes to admission. The accepted DAG remains `S -> T`, `S -> C`, then
`S,T,C -> A -> outer admission`. C.source_manifest_sha256 stays SHA(S).

A pins exact C hash and actual length (not its reservation), T hash/length and all
shared identities and the 18 fixed limits in the contract. Retain/acknowledge T,
C and A before an Event or primitive is permitted. A is at most 4,096 bytes; T/A
and one temporary copy keep their existing reservations. T/A must live in a
separate owned metadata location: the unchanged sink inspector allows only C,
terminal and event shards. Do not place extra files in its root or add header
frames to the event stream. S's bytes/copies also require their existing separate
accounting; a matching SHA string is not authenticity or historical completeness.

A concrete exclusive metadata writer, actual-byte resolver/admission join and
installation coordinator remain missing. Activation failure consumes the
opportunity, retains partial metadata and all costs, invokes no primitive, and
attempts owned cleanup with first/supplemental errors kept separate. It must not
manufacture a fresh directory to retry. Final sink receipt remains
`pending_external_confirmation`; intended terminal hash, observed file hash,
append return, final fsync/descriptor closure and external confirmation are
separate facts. No source-owned receipt can certify its own final persistence.

## Bounds and accounting to qualify, not assumed measurements

The bridge counts attempted raw lines/bytes separately from physical selected
lines/bytes and acknowledged callbacks. It never expands the recorder's 64 MiB
logical ceiling or the sink's C-derived total. At most 110,201 physical lines are
eligible; at most two raw fallback lines of 4,096 bytes fit the existing 8,192
failure allowance. These replace a failed portion of the compact stream rather
than adding permission above `2*N+1`. If recorder or sink capacity prevents the
failed Event, retain that unknown; do not promise a complete terminal record.

No extra shard preamble, delimiter, checksum line or full raw transcript copy is
introduced. The published compact upper bound of 13,432,214 bytes, including its
specified reservations, is conditional on the fixed successful identity plan and
the bounded fallback rule; it is not observed fit or whole-science fit. Count all
retained temporary files, metadata copies, partial bytes and external records.

At construction, a straightforward implementation performs one table parse for
compatibility and the codec's own table parse, plus one C parse; count both
105-row validations unless an explicitly reviewed API removes the duplication.
Each ordinary append performs one raw classification plus one codec conversion
(the latter currently two parses/four canonical serializations), a byte equality
check and at most one physical append. No exp/log/forward/CDF/primitive calls are
added. Terminal classification/serialization and fallback hashing are separate
cheap work, including the optional failed Event. Exact new operation counts must
come from authored implementation, not the scientific primitive census.

Propose at most eight live event-sized immutable byte buffers (32 KiB), one retained
table byte representation and one C representation, plus bounded current/last
intent and diagnostic state. Release per-event temporary references promptly; do
not accumulate Conversion objects or per-event bridge snapshots. This is a target
for source review, not a measured Python heap bound: parsed object/Unicode overhead,
codec table views and the recorder's existing raw Event/object history still need
separate memory qualification. The recorder can retain up to its logical byte cap
plus object overhead; a full snapshot/copy is not free. Diagnostic publication
and cleanup costs need explicit output/accounting reservations before installation.

## Smallest next source unit and focused acceptance

Recommend one private `tests/d1_codec_append.py`, its fake-callback test module and
a scope guide. Include the strict pure terminal classifier and append state machine
together: a terminal parser alone would leave the consumed-cursor edge untested.
No filesystem writer, A/S resolver, source authentication or actual recorder-hook
installation belongs in that unit. Fake callbacks may record bounded bytes or
raise; no real primitive, history, protected inventory or file sink is needed.

Required independent tests include:

- Exact intent/return vectors: callback order, raw replay equality and value
  representation preservation; the fake callable cannot run before intent ack
  and cannot hand back its result before return ack.
- Return append failure after codec ordinal advancement, matching next failed
  Event, substituted last intent rejection and no duplicate physical append.
- Primitive failure, preflight/null intent, unseen-but-source-shaped intent,
  recorder pre-append byte failure, returned-unavailable and original Fault
  ordinal distinct from call ordinal; no fabricated invocation evidence.
- Raw unsupported/failed success followed by intentional stop, plus storage
  failure; original and supplemental exceptions remain distinguishable. The
  recorder's unknown delivery and separate callback-return observation both survive.
- One optional failed Event only, strict sequence and cap exhaustion, stopped
  sink callback never called again, reentry/wrong owner, finish consumed before
  cleanup, and no resume after any unknown delivery.
- Duplicate keys, booleans, unknown fields, malformed/truncated/oversized input,
  noncanonical escapes/whitespace, invalid Fault/Value/Intent joins and raw fallback
  refusing arbitrary payloads. Short independently specified parameter IDs.
- T/C identity, derived-cap and canonical-byte mismatch at construction causes
  zero callbacks; valid matching declarations remain explicitly unauthenticated.

A later independently reviewed slice must supply metadata retention, actual
S/T/C/A binding, pinned sink ownership and operational closeout, then qualify
byte/work/memory fit with failure cases. None of these are completed by this
proposal, nor does this unlock D1 calibration, scientific execution or publication.
