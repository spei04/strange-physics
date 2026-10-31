# D1 conditional codec append bridge

Implements the [reviewed append design](D1_CODEC_APPEND_DESIGN.md). Local bounded
verification passed 99 synthetic cases, 297 ordered phases, formatting, lint and
full typing across 219 files at source `1c815203bbe1519207933dd1819fbc93203e6dd5`.
This slice consists of the pure helper, its fake-callback tests and this guide.
Actual recorder/sink wiring and activation remain separate work.

## Conditional interfaces

`classify_raw(raw: bytes) -> RawEvent` reparses exact canonical recorder bytes.
Its immutable outputs describe source-shaped data, not actual execution or
historical completeness. Event bytes are bounded before parsing; duplicate fields,
noncanonical spelling, booleans in integer slots, excessive depth/numbers and
unknown fields are rejected. Decimal/binary64 Values reuse the existing pure
codec's lexical checks: no Decimal, floating-point or scientific calculation is
needed. Raw Intent canonical bytes preserve the full argument/scope binding.

`CodecAppendBridge(table_raw, context_raw, *, append)` validates actual T/C bytes
and owns one encode-direction cursor. Its synchronous `append(raw) -> None` accepts
bytes only, never a caller-created RawEvent/TableView/Conversion. A normal return
requires exact codec replay equality and a successful `None` return from the
supplied callback. Neither a true/false flag nor an awaitable is an acknowledgement.
`finish()` consumes the bridge once with no I/O; `snapshot()` is diagnostic only.
These are not real recorder, file-sink or primitive installation APIs.

The callback type promises retained bytes, but this slice cannot prove what a
callback does. Fake tests establish bridge return ordering only; they do not
establish actual recorder callback/value-handoff ordering or durable storage.
The bridge does not open/close a sink, write metadata, resolve S or authenticate
source. Its snapshot always says activation is not established.

## Context and fixed reservations

The context parser accepts exactly the pinned sink's 18 canonical fields, flat
JSON nesting and at most 4,096 bytes. It checks raw strict types before comparing
shared identities and derived limits. Its integer-token limit is eight digits,
needed for valid C byte limits; the Event parser retains its six-digit limit.
T is reparsed, including its 105 exact rows. Shared T/C run/recorder/source/protocol
pins must agree; declared sink/codec hashes remain declarations needing later S
resolution. Extra verification/authority claims are rejected.

Fixed D1 max_calls=55,100 and max_events=110,201 are mandatory. C includes 20,480
bytes for context/terminal metadata. It must leave three 65,536-byte reservations
outside its total for T/A, their one temporary copy and rotation slack:

```text
C.max_bytes <= 16,777,216 - 3*65,536 = 16,580,608
C.event_capacity = C.max_bytes - 20,480
ordinary_capacity = C.event_capacity - 8,192 > 0
```

Thus a tiny otherwise syntactically valid sink C is rejected before any callback.
Compact lines cannot consume the 8,192-byte failure reserve. Raw fallbacks are
limited to two lines, each at most 4,096 bytes. Compact/fallback bytes both count
against the same event capacity, physical total and 110,201-line ceiling; these
are not extra allocations. The recorder's independent 64 MiB expanded logical
ceiling is unchanged. These inequalities are structural checks, not proof that a
complete transcript or the whole scientific output fits.

## Failure and acknowledgement state

The bridge records raw attempts, visible reserved sequences, compact/fallback
selected-byte reservations, physical callback observations and normal bridge
returns separately. Physical reservations occur before the callback and remain
charged after errors; they are not measured written bytes. Snapshot fields retain
at most the first failed and last attempted Event descriptors (hash/length/status),
not another transcript. Callback state distinguishes not_entered, entered,
returned and raised. A callback return observed during the call is not itself a
normal bridge return.

The independent current/last complete Intent survives codec advancement. A return
write failure can therefore be followed by the recorder's next reserved failed
Event without rewinding or invoking the codec again. A failure before the recorder
reserved an unavailable-return Event consumes no visible sequence: a later failed
Event with ordinal3 can use the immediately next sequence, without inventing an
unseen unavailable line. Exact full-Intent substitutions are rejected.

Failed-Event Fault.ordinal is preserved in the source-supported range 0..3.
Ordinals2/3 require return_encoding; reentry is first fault0 with null call_id,
even when the Event carries the outer non-null Intent. `fault_retention` and its
possible ordinal4 belong only to subsequent snapshots, never a new failed Event.
The [design's source derivation](D1_CODEC_APPEND_DESIGN.md) describes the swallowed
recorder-reentry/invalid-return/unavailable-retention-failure path. This range does
not authenticate unseen faults, identify a primitive invocation, or equate the
first recorder error with the later outer exception.

A raw fallback is retained byte-for-byte where possible, then the bridge raises
an intentional stop. The recorder would conservatively retain unknown delivery,
while this bridge separately records callback-return observation. It does not
rewrite that history or label intentional stop as a filesystem error. One optional
subsequent failed Event may be classified/retained; no new successful Event is
allowed. A physical callback error permanently blocks further physical callbacks,
although the matching failed Event may still be classified. No append retry or
inspection-based acknowledgement is available.

Single process/thread ownership and reentry are enforced before parsing. A
callback that catches a nested bridge error and returns normally cannot clear the
sticky error: the outer append raises, preserves the callback-return observation,
and never acknowledges. Finish does not clear faults or close external resources.
The caller remains responsible for the existing sink's once-only finish and final
external confirmation. No destructor or automatic reopening is used.

## Work, memory and test boundaries

Construction performs two table parses (including both 105-row validations), one
context parse and their hashes. A successful ordinary append performs one raw
classification and the existing codec conversion: at most three JSON parses and
seven canonical serializations, plus bounded full-byte joins and two Event hashes
(raw/selected physical). Failure classification and fallback hashing are separate
cheap work. There are no added exp/log/predictor/reference/CDF calls. Runtime
controller/accounting must charge all these operations; they are not included in
the 55,100 scientific primitive count by renaming them as primitives.

State is constant in Event count: one codec/table, up to two complete current/last
Intent byte representations, two attempted-Event descriptors, four bounded fault
summaries and a count of omitted diagnostic faults. RawEvent/Conversion parse data
is local to one append. No full raw/compact transcript or per-Event snapshot list
is accumulated by the bridge. Actual exception references can retain tracebacks,
parsed Python objects have overhead, and the existing recorder retains its own
raw Events; the proposal's eight-buffer target is not a measured Python heap cap.
Explicit buffer/heap and full-run byte qualification remain pending. Caller-retained
views, snapshots, files and copies must be counted, not assumed free.

The authored tests use independently specified JSON/vector shapes and owned
callbacks that collect a few bytes or raise. Counter seams exercise boundary
reservations without constructing a transcript. No temporary files, actual sink,
real recorder callback, activation manifest, historical inventory or scientific
material is constructed. The largest authored invalid raw/C padding is 4,097
bytes; a test makes only a small prefix and at most two forensic fallback lines.
Numeric math functions and imports of actual recorder/sink/scientific helpers are
poisoned during test bodies; this is a reviewed-test boundary, not an OS sandbox.

Coverage includes exact compact lines, signed/quantum-preserving source bytes,
return-error-after-cursor-advance, raw fallback without acknowledgement, ordinal3
without a prior unavailable line, original/supplemental errors, swallowed reentry,
wrong owner, strict C joins, malformed bytes, full Intent substitution, independent
logical/physical/fallback accounting and finish consumption. Every parametrized
case has a short explicit ID. Guarded collection confirmed the same 99 ordered
cases across 29 test functions before and after the typing repair. The final
check passed all 297 setup/call/teardown phases with no skips or expected failures.

## Local verification record

| Attempt | Result |
| --- | --- |
| 1 — preparation | 99 cases collected, no test phases; owned sentinel and all six process closures verified. |
| 2 — checks | Formatting and lint passed. Full 219-file typing stopped on three errors caused by reusing an exception-target name; no test bodies ran. |
| 3 — preparation | The three-identifier rename retained every assertion and the same 99 case IDs; source, helpers and environment matched. |
| 4 — checks | Formatting, lint, full 219-file typing and all 99 cases / 297 phases passed; no forbidden entry attempts. |

The typing repair changes only the non-None callback-result branch's local name.
Reversing those three Name nodes gives the preceding module's exact AST; existing
callback-result regressions are unchanged. The original failure and both prior
admissions remain retained.

Independent review confirmed all 23 child processes closed across four attempts,
399 source files and 29 imported-source bindings matched, and the pinned
environment remained unchanged. Retained output was 2,496,065 logical bytes.
The cumulative charge was 96.076355 CPU seconds (76.076355 measured plus four
five-second closeout holds) and 118.771485 active-wall seconds. External control
and whole-operation usage remain unknown; remaining allowance is not transferred.

This record establishes conditional fake-callback behavior only. It does not
establish actual recorder/storage handoff, authenticated source, durable metadata,
activation, a complete transcript fit or scientific qualification. Hosted CI is
reported separately by the associated pull request.

## Remaining installation gates

A later unit must retain/acknowledge actual T, C and A using the accepted acyclic
S -> T/C -> A joins, bind actual A to admission, validate actual owned callback and
source/instance material, and own metadata/resource cleanup. C alone cannot
establish A or source authority. No new metadata files may be placed in the
unchanged sink root or added as stream headers. Source/metadata/copy/failure/closeout
costs and reservations remain required. This checkpoint does not admit scientific
execution, demonstrate operational durability, prove whole-science fit or complete
D1 calibration/report binding.
