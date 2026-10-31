# D1 transcript byte fit: static finding and proposed codec work

Status: source-derived byte accounting and a proposed implementation work package.
No recorder, codec, primitive, predictor, simulator or scientific batch was run to
produce this note. No transcript was encoded. No partition, cap, protocol or
numerical allocation changes here.

**The unchanged raw JSONL cannot hold the full successful 55,100-call D1
transcript in the proposed 16 MiB transcript partition. Actual fit within the
64 MiB whole-science cap is unproved.** A failed or partial transcript may be
smaller; that does not complete the frozen call plan.

## Immutable source and scope

The proof uses the published
[recorder at 6d3edf1](https://github.com/spei04/strange-physics/blob/6d3edf1fbc6c01c97ac84bc0a06231b4199a83e8/tests/d1_primitive_recording.py),
SHA-256 `b7ac0ec37c1e847d8e076abf5d27a7df30fffa8316d473f5a7631fb46f87f185`.
`Value`, `Intent` and `Event` are at lines 26, 34 and 53; the actual encoder is
at lines 177–185, and successful intent/return emission is at 246/284. Its
changes from the unformatted source in the sink branch are formatting only;
this proof is anchored to the published bytes.

The [frozen D1 protocol](https://github.com/spei04/strange-physics/blob/6d3edf1fbc6c01c97ac84bc0a06231b4199a83e8/docs/research/RA_N03_CALIBRATION_SLICE.md)
has SHA-256 `657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
The [report/binder design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md)
proposes the internal 16 MiB transcript partition within 64 MiB, explicitly
subject to lossless codec fit. That document is not present in the current
integration branch, so this reference uses its verified published identity.
The local [sink contract](D1_PRIMITIVE_SINK.md), source checkpoint
`658583cda860831e19888fbf238f58267922dc97`, separately reserves 4,096 context
bytes and 16,384 terminal bytes inside an explicit total sink ceiling. It does
not demonstrate transcript fit or operational durability.

The frozen successful physical-call census is:

| Primitive | Calls | Argument / return kinds |
| --- | ---: | --- |
| Candidate and fixture position | 3,840 + 13 = 3,853 | Seven binary64 parts / Decimal |
| Independent reference exp and log | 25,600 + 46 = 25,646 | Decimal / Decimal |
| Circle constant | 1 | None / Decimal |
| Native emitted conversion | 25,600 | Binary64 / binary64 |
| Total | 55,100 | Two events per successful call |

There are 110,200 successful intent/return events. The 128 internal Machin
terms are not additional recorder calls. Wrapper-cache hits, reused slots and
later pure reconstruction also must not become new physical primitive calls.

## Lower bound: field names alone disprove 16 MiB raw fit

The encoder writes sorted-key compact JSON plus one LF. Each successful return
repeats its entire `Intent`, including its argument `Value`. For a JSON object
with `m` fields and ASCII key lengths `k_j`, the bytes for keys and structural
punctuation, excluding every value, are:

```text
B_object = 2 braces + (m-1) commas + 3m quote/colon bytes + sum(k_j)
         = 1 + 4m + sum(k_j).
```

| Object | Keys | Sum of key lengths | Key/punctuation bytes |
| --- | --- | ---: | ---: |
| Event | sequence, kind, intent, returned, fault | 31 | 52 |
| Intent | ordinal, call_id, instance_id, primitive, scope, arguments | 48 | 73 |
| Value | kind, parts | 9 | 18 |

A successful pair contains two Event objects, two Intent objects and three
Value objects: argument twice, return once. Its structural bytes and two LFs
therefore cost at least:

```text
2*52 + 2*73 + 3*18 + 2 = 306 bytes/call
55,100 * 306 = 16,860,600 bytes
16 MiB = 16,777,216 bytes
structural excess = 83,384 bytes.
```

This intentionally omits all argument/return digits, identifiers, scopes,
ordinals, sequence numbers and Value-kind/array contents. The two mandatory
`fault:null` values add eight bytes; the quoted `intent` and `returned` kind
values add 18 more. Thus a still-conservative stronger floor is:

```text
306 + 8 + 18 = 332 bytes/call
55,100 * 332 = 18,293,200 bytes.
```

Both floors exclude context, terminal, dictionary, manifest, failure, partial
write and copied-output bytes. These can only increase retained storage. No
particular D1 scientific value or favorable short identifier is needed for the
contradiction.

## Upper bound: accepted encoding domain does not prove 64 MiB fit

For successful values, the existing accepted domain gives these static ceilings:

- Decimal: at most 120 coefficient digits, one sign digit and a four-character
  exponent (`-256` through `128`). Its three-string parts array is at most 135
  bytes, so the full Value object is `18 + 9 + 135 = 162` bytes.
- Finite binary64: `float.hex()` has at most 24 ASCII characters including sign.
  The one-string parts array is at most 28 bytes, giving
  `18 + 10 + 28 = 56` bytes for the Value object.
- Position argument: seven at-most-24-character binary64 strings require at
  most 190 array bytes, giving `18 + 14 + 190 = 222` bytes.
- No argument: `Value("none", ())` requires `18 + 6 + 2 = 26` bytes.

Allowed identity/scope tokens are ASCII and need no JSON escape expansion.
Each call/instance ID may contain 96 characters; six such scope tokens occupy
at most `6*(96+2) + 2 + 5 = 595` array bytes. A successful call ordinal needs
at most five digits; an event sequence needs at most six.

Let `A` be the argument Value size and `p` the unquoted primitive-name length.
Then the Intent ceiling is:

```text
I <= 73 + A + 98 + 98 + 5 + (p+2) + 595 = 871 + A + p.
```

If `R` is the returned Value size and `d0,d1` the event-sequence digit counts,
the exact pair-size expression is `136 + 2I + R + d0 + d1`. Therefore the
conservative pair ceiling is `148 + 2I + R`.

| Primitive family | A | p | I ceiling | R | Pair ceiling | Calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Position | 222 | 8 | 1,101 | 162 | 2,512 | 3,853 |
| Exp/log | 162 | 3 | 1,036 | 162 | 2,382 | 25,646 |
| Circle constant | 26 | 15 | 912 | 162 | 2,134 | 1 |
| Native emitted conversion | 56 | 10 | 937 | 56 | 2,078 | 25,600 |

```text
3,853*2,512 + 25,646*2,382 + 1*2,134 + 25,600*2,078
= 123,966,442 bytes (successful events only).
```

An upper bound above 64 MiB does **not** prove the actual frozen caller material
exceeds 64 MiB. It proves that the broad current token/value domain alone cannot
supply a sufficient fit certificate. Actual fixed call IDs, scope layouts,
source-owned table cardinalities and value-width bounds still need a proof.
The generic 4,096-byte event cap gives a much looser successful ceiling of
451,379,200 bytes, or 451,383,296 for `2N+1` emitted events; these are domain
ceilings, not permissions to write those amounts.

The report design's other proposed science partitions total 48 MiB. The
16 MiB raw transcript failure therefore cannot be solved by silently borrowing
from them, moving science copies into another pool or treating the recorder's
64 MiB domain ceiling as a second allocation. Whole-science fit remains a
separate aggregate obligation.

## Success, failure and unknown delivery

The lower-bound contradiction concerns full success at the fixed census.
Stopping early at a byte ceiling produces an incomplete execution; it cannot
be relabeled a scientific negative or an accepted smaller plan. Failure paths
may retain fewer lines, a returned-but-unavailable value, a failed event or a
partially written line. The successful pair ceilings above do not bound those
fault shapes; their safe type strings and fallback events require separate
4,096-byte event and total-reservation checks.

The recorder marks an event unknown before append and confirms it only after
append returns. Its `_bytes` counter includes every encoded event offered to
the sink, including unknown delivery. The sink separately reserves physical
bytes before I/O and preserves partial/unknown reservations. Raw presence on
inspection does not establish append acknowledgement or primitive execution.
Terminal bytes cannot attest to their own fsync confirmation or final closure;
external closeout must preserve those remaining unknowns.

## Proposed smallest lossless adapter and expander

Keep the recorder's scientific call interface, failure state machine and
logical limits unchanged. Add one scoped append adapter and a pure expander,
with no scientific imports/calls or generic compression framework. The
following wire contract is a proposal for source review, not an adopted codec:

1. Pin a codec version and exact short, source-owned identity plan. A bounded
   immutable table retains the original instance IDs and scope tuples, and any
   call-ID template retains enough exact prefix/width data to reconstruct the
   original ID. Table indexes are not substitutes for missing strings. Source,
   protocol, recorder, codec and table hashes join the context manifest; actual
   callable/source authentication still belongs to installation and the binder.
2. Encode each intent as one positional JSON line carrying its sequence,
   ordinal, exact call identity, instance/primitive/scope references and exact
   tagged argument parts. Every one of the seven position-key components is
   retained. Do not infer scope from outcomes or a partial display label.
3. Encode a returned event as one positional line referencing its already
   retained intent ordinal and carrying exact tagged return parts. Reconstruct
   the complete repeated Intent from that reference. Reject substitution,
   missing intents, duplicate sequence/call IDs and an incorrect ordinal join.
4. Preserve Decimal sign/coefficient/exponent strings and binary64 hex strings
   exactly, including signed zero and Decimal quantum. Freeze the current
   compact sorted-key ASCII-escaping JSON profile and LF when reconstructing
   raw recorder lines; it is not RFC 8785/JCS. No Unicode normalization,
   floating conversion, numeric rounding or alternative spelling is allowed.
5. Before any physical append acknowledgement, expand the proposed wire record
   and byte-compare it with the **actual original recorder line**. A digest-only
   match or a newly recomputed scientific value is insufficient. Append exactly
   once and return only after the reviewed sink acknowledges the line. This
   retains intent-before-call and return-before-handoff ordering.
6. Retain failures, unavailable values, original/supplemental fault facts and
   unknown delivery. A bounded original raw-object line can be a lossless
   fallback when it cannot use a shared-intent encoding; the decoder must
   distinguish this explicitly. No truncation, favorable reconstruction or
   automatic retry follows a codec/sink failure. An oversized/nonreconstructible
   event remains an explicit retention failure, with invocation/return status
   preserved where known.

Tables must be retained and acknowledged before activation. If they are
separate bounded manifest artifacts, their actual bytes and copies remain in
the same transcript partition. They must not become extra shard events that
silently exceed the sink's existing `2*max_calls+1` ceiling. One recorder event
maps to one physical line, still at most 4,096 bytes; framing/tables/context and
failure reserves are not free. A shared-table contract needs exact entry counts
and byte ceilings from the fixed caller plan before implementation can claim
fit. The present allowance for arbitrary 96-character tokens and six scope
parts cannot be assumed compressible.

The unmodified recorder still retains expanded raw events in memory and charges
its logical `_bytes` counter. Compact physical storage does not remove that
existing at-most-64 MiB logical ceiling, object-memory costs or any serialized
snapshot copies. Both expanded logical fit and physical compact fit must be
proved. The sink's own context/terminal reservation and any separate tables
must fit the aggregate 16 MiB target; setting the sink alone to 16 MiB and adding
unaccounted tables outside it is invalid.

## Dependency-ordered implementation and qualification

The smallest independently reviewable work is:

1. **Identity/codec contract and pure functions.** Freeze the exact D1 call-ID,
   instance and scope scheme, table serialization and a positional/fallback
   codec. Implement bounded strict parsing and exact raw-line expansion with
   no primitive replay. Supply synthetic extrema, quantum/signed-zero, escaped
   fault-string and malformed-reference tests. No scientific values are needed.
2. **Synchronous append adapter and sink integration.** Preserve one-use ordering
   and unknown-delivery semantics. Test intent failure causes zero invocation;
   primitive return followed by codec/write failure stays returned; partial
   write/fsync/close failures preserve the first and supplemental faults;
   repeated/foreign callbacks cannot acknowledge a different original event.
   Keep existing recorder and sink tests meaningful.
3. **Complete static fit and fake byte/work qualification.** Prove or reject
   expanded raw fit and compact physical fit over the entire frozen profile,
   including tables, 110,200 successful events, bounded failure/control paths,
   context/terminal reservations, shard tail slack, partial writes and actual
   copy multiplicity. All legitimate fixed-profile values must fit, not just a
   favorable synthetic sample. Count parse/encode/expand/compare/hash/table
   operations, write-loop progress, fsyncs, inspection and every binder replay.
   No extra oracle, native exp, predictor or simulator call is introduced.

No compression ratio, actual call-scope cardinality, codec fit or runtime cost
is established by this note. If a supported fixed-profile shape cannot meet
16 MiB, retain that failed design gate and present a new lossless design or an
explicitly reviewed within-64-MiB partition proposal; do not change a cap here.
Actual-source binding, complete report/binder evidence, aggregate output fit,
operational closure and numerical admission remain prerequisites. Existing
failed work, protected holds and historical cost unknowns remain unchanged.
