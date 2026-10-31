# Proposed D1 primitive codec and fixed identity contract

Status: source-only proposal for independent review. This is not an adopted
installation, serializer implementation, numerical admission or whole-science
fit certificate. No primitive, project import, encoding batch or scientific
calculation was executed for this document. The complete 55,100-call plan,
16 MiB proposed transcript partition, recorder logical 64 MiB ceiling and
64 MiB whole-science cap remain unchanged.

The [raw-byte proof](D1_TRANSCRIPT_BYTE_FIT.md) disproves 16 MiB full-success
raw JSONL fit. This proposal addresses that representation failure without
omitting calls, arguments, returns or failures. The fixed protocol remains
[657c3c74](https://github.com/spei04/strange-physics/blob/6d3edf1fbc6c01c97ac84bc0a06231b4199a83e8/docs/research/RA_N03_CALIBRATION_SLICE.md).
The [report design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md)
retains its aggregate fit and actual-material binding obligations. The
[source-only sink contract](D1_PRIMITIVE_SINK.md) is unchanged.

## Source and installation boundary

All source observations below refer to published commit
`6d3edf1fbc6c01c97ac84bc0a06231b4199a83e8`:

| Source | SHA-256 | Relevant boundary |
| --- | --- | --- |
| `tests/d1_primitive_recording.py` | `b7ac0ec37c1e847d8e076abf5d27a7df30fffa8316d473f5a7631fb46f87f185` | Exact raw Event encoder and one-use failure state |
| `tests/d1_fixture_reference.py` | `b305a16a5afa8c9bd07db5fad64a5205e8c8621e293ab7f200c80f2043e80bc3` | Thirteen `QUERY_SPECS`; owned `position` call in `D1FixtureProducer.run` |
| `tests/d1_prefix_evidence.py` | `c5d086d29e2a445592161d83d8f1d72d59acbda49fd8d0473576e83793e11ff0` | `D1Reference._endpoint/constants/normalize`; injected `emit` in `qualify_prefix` |
| `src/strange_physics/calibration_fixture_contracts.py` | `b570363bd5ea5d46107ccf208189cc790b5ea24000d5bf412d14f358e04d76fe` | Exact case order and fixture/profile domains |

Those fixture/prefix sources do **not** currently install `PrimitiveRecorder`.
The installation described here is future source work. Its hooks must cover
only the actual thirteen fixture positions, 3,840 endpoint-cache misses,
25,600 reference exponentials, 46 reference logarithms, one circle constant and
25,600 injected native emitted conversions. The emitter hook is the supplied
`emit(native_log_probability)` in `qualify_prefix`; a global `math.exp` patch
would incorrectly intercept the native normalizer's separate 25,600 internal
exponentials. Those remain in the overall work census but outside this recorder
census. The 128 internal Machin terms are not additional recorder calls.

The future installer must bind each actual owned oracle/callable to its pinned
definition/runtime and role, without creating a replacement oracle or invoking
it to verify identity. Current APIs need narrowly reviewed installation hooks;
this proposal does not pretend that every owned instance is already externally
accessible before its first call.

## Fixed private identity tables

Everything in these tables is evaluator-private. Candidate-facing opaque
run/space/operation IDs and actual input/result identities remain unchanged.
A table label is not authentication, a physical query or an exposure receipt.

Canonical header/table bytes use sorted-key compact JSON, ASCII escaping,
`allow_nan=False`, UTF-8 and exactly one final LF; this is not RFC 8785/JCS.
Integer fields require actual integers, excluding booleans. Unknown fields,
rows, aliases, duplicate indexes and noncanonical bytes are rejected.

The immutable table schema is proposed as
`strange-physics.d1-primitive-codec.v1`. Its root has exactly `schema`,
`source_commit`, `source_tree`, `protocol_sha256`, `source_manifest_sha256`,
`recorder_sha256`, `codec_sha256`, `run_id`, `recorder_id`, `max_calls`,
`case_order` and `rows`. Hashes/commit/tree have their existing exact lowercase
hex lengths; run/recorder IDs use the sink's bounded opaque-token rules.
`max_calls` is 55,100. `case_order` is exactly:

```text
0 M01, 1 M02, 2 M03, 3 M04, 4 D03, 5 F02, 6 F04, 7 W03
```

There are exactly 105 rows, concatenated in the group order below. Each group
uses ascending integer index; there are no optional rows. The table enumeration
is an identity ordering, not permission to reorder prequential execution.

| Group | Row form | Count / index order |
| --- | --- | --- |
| Instance | `["I",j,"iNN",role,case_index_or_null,source_binding_ref]` | 14, `j=0..13`; role mapping below |
| Profile | `["P",p,case_index,grid_code,scale_code,record_count]` | 40, case then grid then permitted scale |
| Ensemble | `["E",e,case_index,grid_code]` | 16, `e=2*case_index+grid_code` |
| Fixture query | `["Q",q,name,numerator,anchor_tag,initial_tag,time_tag]` | 13, exact query order below |
| Constant | `["C",c,token,primitive_code]` | 7, exact order below |
| Primitive vocabulary | `["V",v,name]` | 5, index/name mapping below |
| Scope vocabulary | `["S",s,token]` | 6, index/token mapping below |
| Successful value vocabulary | `["T",t,token,kind]` | 4, index/token/kind mapping below |

Every row is capped at 512 bytes **including one conservative separator byte**;
there are no arbitrary payload fields. `source_binding_ref` is a bounded
32-character ASCII member ID in the separately pinned source/runtime manifest,
not a path supplied by an event. The role and query strings below are exact.
The table's header measurement `H` is the exact root serialization with
`rows=[]`; it includes container punctuation, all header values and LF, and
must be at most 4,096 bytes. With row bytes `r_j`, the actual table is bounded
by `H + sum(r_j+1)` (one byte conservative for the final row):

```text
105*512 + 4,096 = 57,856 bytes.
```

A separate activation manifest is capped at 4,096 bytes. Table plus activation
metadata therefore occupy at most 61,952 bytes, within the proposed 65,536-byte
table/activation reservation. Row and header caps are fail-closed contract
requirements; their actual encoder/reconstruction fit still needs tests.

### Instances and profile enumeration

Instance IDs are exactly `i` followed by two decimal digits. They describe
thirteen EndpointOracle instances plus one native-emitter role, not fourteen
oracles:

| j | Role | Case index |
| ---: | --- | --- |
| 0 | `fixture` | null |
| 1 | `strong` | null |
| 2 | `weak` | null |
| 3 | `future` | null |
| 4 through 11 | `arithmetic` | `j-4` |
| 12 | `constants` | null |
| 13 | `native_emit` | null |

Grid codes `0,1` mean 256,1024. Scale codes `0,1,2` mean exactly
0.125,0.25,0.5; D03/W03 admit only code1. Profile IDs are `p` plus two digits:
M01 p00–p05, M02 p06–p11, M03 p12–p17, M04 p18–p23, D03 p24–p25,
F02 p26–p31, F04 p32–p37, W03 p38–p39. Within each case, enumerate grid0
then grid1 and ascending permitted scale. `record_count` is two only for D03,
otherwise one. Ensemble IDs are `e` plus two digits, e00–e15.

Call IDs are exactly `c` plus the five-digit zero-padded recorder call ordinal,
c00000–c55099. The installation's one-use reservation and the actual raw
`Intent.ordinal` must agree; do not derive IDs by copying a growing recorder
snapshot on every call. Call order still must satisfy the frozen scientific
protocol and source bindings. A counter string alone does not prove it did.

Node tokens are `n` plus four zero-padded digits, bounded by the referenced
grid's node count. Physical endpoint-miss scope uses `r0`. D03's second
identical physical query is a cache hit, not another primitive miss; its
logical record1 identity remains in the external consumer/reuse witness.

### Fixture queries and constants

The fixture tags are `a0`/`a1` for anchor0/1⁄8, `x0`/`x1` for initial1/1⁄8,
and `t0`/`t1` for time0.5/0.75. They do not replace the actual seven binary64
argument parts or coefficient rounding proof.

| q | name | numerator | anchor / initial / time |
| ---: | --- | ---: | --- |
| 0 | train-M01 | 1 | a0 / x0 / t0 |
| 1 | future-M01 | 1 | a0 / x0 / t1 |
| 2 | train-M02 | 5 | a0 / x0 / t0 |
| 3 | future-M02 | 5 | a0 / x0 / t1 |
| 4 | train-M03 | 13 | a0 / x0 / t0 |
| 5 | future-M03 | 13 | a0 / x0 / t1 |
| 6 | train-M04 | 27 | a0 / x0 / t0 |
| 7 | future-M04 | 27 | a0 / x0 / t1 |
| 8 | train-F02 | 5 | a1 / x0 / t0 |
| 9 | future-F02 | 5 | a1 / x0 / t1 |
| 10 | train-F04 | 27 | a1 / x0 / t0 |
| 11 | future-F04 | 27 | a1 / x0 / t1 |
| 12 | train-W03 | 13 | a0 / x1 / t0 |

Query tokens are `q` plus two digits. Constants c0–c6 use tokens, in order,
`pi`, `l2p`, `s0`, `s1`, `s2`, `g0`, `g1`: circle constant, log(2*pi),
three scale logs and two prior logs. Their primitive codes are3 for pi and2
for all six logs. Actual Decimal arguments are retained even when metadata
identifies their construction. No constant is recomputed by the decoder.

### Primitive, scope and value vocabulary

Primitive codes are `0 position`, `1 exp`, `2 log`, `3 circle_constant`,
`4 native_exp`. Scope-family codes are `0 fx`, `1 ep`, `2 ne`, `3 nz`,
`4 ct`, `5 nv`. Successful-value codes/rows are `0 p position_key`,
`1 d decimal`, `2 b binary64`, `3 n none`.

These are every legal successful raw scope and compact descriptor:

| Family | Exact reconstructed raw scope | Compact descriptor | Instance / primitive |
| --- | --- | --- | --- |
| Fixture | `("fx","qQQ")` | `[0,q]` | 0 /0 |
| Endpoint miss | `("ep",channel,context,"nNNNN","r0")` | `[1,h,z,node,0]` | `1+h` /0 |
| Reference exp | `("ne","pPP","nNNNN")` | `[2,p,node]` | `4+profile.case_index` /1 |
| Normalization log | `("nz","pPP")` | `[3,p]` | `4+profile.case_index` /2 |
| Constant | `("ct",constant.token)` | `[4,c]` | 12 /constant.primitive_code |
| Native emission | `("nv","pPP","nNNNN")` | `[5,p,node]` | 13 /4 |

For endpoint misses, h0/1/2 maps to channel `s`/`w`/`f`. Strong/weak contexts
are profile IDs p00–p39; future contexts are ensemble IDs e00–e15. Weak accepts
only W03 profiles; strong rejects W03. The actual first consumer determines
the context; the complete physical argument key must match that context,
channel, node and record. A future call has no scale dimension. Separate
logical-consumer material retains all case/grid/scale/node/record identities,
including cache hits, staged prequential consumption, D03 duplication and
future reuse. Do not invent 37,120 recorder calls from those logical requests.

Primitive/value joins are fixed: position takes `p` and returns `d`; exp/log
take and return `d`; circle takes `n` and returns `d`; native_exp takes and
returns `b`. Every field/index/tuple length is validated against its exact
source-owned table; an event cannot choose a new vocabulary or policy.

## Wire arrays, fallback and byte-exact replay

There are exactly two successful wire modes, `"i"` and `"r"`:

```text
["i", sequence, ordinal, instance_index, primitive_index, scope_descriptor, argument]
["r", sequence, ordinal, returned_value]
```

Tagged values are flattened arrays with exact string parts:

```text
["p", hex0, hex1, hex2, hex3, hex4, hex5, hex6]
["d", sign_string, coefficient_digits, exponent_string]
["b", exact_binary64_hex]
["n"]
```

No Decimal arithmetic, float conversion, Unicode normalization or spelling
normalization is allowed during expansion. Decimal quantum and signed zero
survive. The original JSON object field names, explicit null defaults, escaping
and LF are reconstructed according to the pinned recorder encoder, not a
similar serializer. Before physical append, expand the **proposed wire bytes**
and compare them to the actual original recorder line byte-for-byte. Only then
perform one sink append. A return must reference the current matching intent;
a parser needs only the current/just-completed call for stream expansion, not
an arbitrary cross-history reference graph.

Every wire line has exactly one final LF, no leading whitespace, and length
at most4,096 bytes. Its first byte is the discriminator: `[` is a compact
`i`/`r` array; `{` is an exact original canonical raw Event object retained as
a terminal forensic fallback. There is no compact `f` mode or unknown tag.
A fallback never authorizes continued successful work. It retains a failed
Event, a returned-unavailable Event, or the actual original event that could
not satisfy the fixed codec contract. Retain it once where possible and stop;
raise through the recorder's existing failure path rather than return an
acknowledgement that would cause a new primitive invocation. At most the
existing terminal failed-event attempt may follow. Unknown/partial bytes never
become a confirmed event by inspection, and failed fallback retention is an
explicit supplemental unknown.

A successfully expanded intent must be retained and acknowledged before its
primitive is invoked. A returned value must be retained and acknowledged
before it is handed back to the adapter. Codec, raw-compare, write, fsync or
close failures preserve the first fault, distinguish primitive failure from
retention failure, and prohibit retry. Replay means pure data expansion and
validation; it never re-executes the scientific callback.

## Acyclic table/header retention and source joins

Use an acyclic binding order:

```text
source/runtime manifest S -> identity table T -> activation manifest A -> sink context
```

S has no hash of T, A or the sink context. T's `source_manifest_sha256` binds S;
T does not contain its own hash or A's hash. A binds the exact hashes/lengths
of S and T, codec/recorder/source identities, run/recorder IDs and the fixed caps.
Its proposed exact fields are `schema` (literal
`strange-physics.d1-primitive-codec-activation.v1`), `source_manifest_sha256`,
`source_manifest_bytes`, `table_sha256`, `table_bytes`, `table_name` (literal
`identity-table.json`), `source_commit`, `source_tree`, `protocol_sha256`,
`recorder_sha256`, `codec_sha256`, `run_id`, `recorder_id` and `limits`. The
activation file name is `codec-activation.json`; S is supplied as exact retained
bytes by the future owned resolver, not an event-selected path. `limits` has
exactly the named call/event, row/header, table/copy, failure, metadata, slack,
expanded-logical and physical-partition ceilings in this proposal; all values
are source-owned, not choices made by an event. Unknown fields are rejected.
These declared targets are not an owner admission. The unchanged sink context's
`source_manifest_sha256` binds A, with its other pins agreeing with S/T/A. Neither A nor T pins a future
terminal/event receipt. This avoids a circular hash dependency.

Retain and acknowledge the bounded T and A bytes before activating the codec
or any primitive call. Source/runtime binding evidence S must already be
immutable, accessible and matched to the actual owned instances/callable.
The necessary installation hooks and that evidence producer are unfinished.
S is ordinary source/runtime proof material, not a place to hide call/scoped
payload; its physical bytes and any copies remain in the whole-science
accounting. Reusing a prior S requires exact identity/custody/access joins,
not merely a hash string. A new or copied S is not free, and its existing
source-proof pool fit remains unproved.

Tables are separate bounded manifest artifacts, not extra shard events. Their
writer needs its own exclusive/private/no-retry retention proof; the sink's
schema/file allowlist is not changed. No event header, dictionary frame,
per-shard preamble, checksum line or uncounted separator is added to the shard
stream. Event hashes and external indexes belong to explicitly accounted
manifests; the codec cannot add them outside this byte calculation unnoticed.

## Expanded raw-event bound under the proposed identity scheme

Let A be an argument Value size, R a return Value size, p the primitive-name
length and S the raw scope-array size. The existing recorder's object syntax
costs Event52, Intent73 and Value18 bytes before values, as shown in the
[raw-byte proof](D1_TRANSCRIPT_BYTE_FIT.md).

The proposed IDs have lengths6 and3. With a five-digit ordinal:

```text
I <= 73 + A + (6+2) + (3+2) + 5 + (p+2) + S = 93 + A + p + S.
raw pair <= 136 + 2I + R + 6 + 6 = 148 + 2I + R.
```

Maximum raw scope arrays are29 bytes for ep,20 for ne/nv,12 for fx/nz/ct.
The unchanged Value ceilings are position222, Decimal162, binary64 56 and
none26 bytes. Substitution gives:

| Family | Count | A | p | S | I | R | Raw pair ceiling |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixture position | 13 | 222 | 8 | 12 | 335 | 162 | 980 |
| Candidate position | 3,840 | 222 | 8 | 29 | 352 | 162 | 1,014 |
| Reference exp | 25,600 | 162 | 3 | 20 | 278 | 162 | 866 |
| Reference log, all | 46 | 162 | 3 | 12 | 270 | 162 | 850 |
| Circle constant | 1 | 26 | 15 | 12 | 146 | 162 | 602 |
| Native emission | 25,600 | 56 | 10 | 20 | 179 | 56 | 562 |

The success total is40,503,002 bytes. Adding the conservative8,192-byte
non-success allowance described below gives40,511,194, below the unchanged
64 MiB recorder logical ceiling. This is conditional on exactly this identity
contract; it does not apply to the recorder's arbitrary96-character IDs and
six arbitrary scope tokens. The existing recorder retains all raw events and
objects in memory; memory and any serialized snapshot copies remain additional
obligations. Physical compression does not alter `_bytes` or refund unknown
raw-event reservations.

## Compact event bound

Decimal tagged arrays cost at most139 bytes: four quoted strings with lengths
1,1,120,4 plus brackets/commas. Binary64 arrays cost at most32; position arrays
at most194; `n` costs5. These use the existing exact finite-value domain, not
measured D1 values.

With sequence at most six digits, ordinal five, instance index two and primitive
index one, the seven-element intent costs at most
`26 + descriptor_bytes + argument_bytes`, including LF. The four-element
return costs at most `20 + returned_bytes`, including LF. Thus:

```text
compact pair <= 46 + descriptor_bytes + argument_bytes + returned_bytes.
```

Descriptor bounds are fx6; ep15; ne/nv11; nz6; ct5 bytes. They include brackets
and commas, use canonical nonnegative integer spellings, and derive from the
exact index ranges above. No signs, padding or caller-selected strings appear
inside numeric descriptors.

| Family | Count | Descriptor | Argument | Return | Pair ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixture position | 13 | 6 | 194 | 139 | 385 |
| Candidate position | 3,840 | 15 | 194 | 139 | 394 |
| Reference exp | 25,600 | 11 | 139 | 139 | 335 |
| Normalization log | 40 | 6 | 139 | 139 | 330 |
| Constant log | 6 | 5 | 139 | 139 | 329 |
| Circle constant | 1 | 5 | 5 | 139 | 195 |
| Native emission | 25,600 | 11 | 32 | 32 | 121 |

```text
13*385 + 3,840*394 + 25,600*335 + 40*330 + 6*329 + 195 + 25,600*121
= 13,206,934 successful compact bytes.
```

## Failure, copy and framing reservations

One successful call has two events. The first failed call stops subsequent
calls; a returned-unavailable event can replace its normal return, followed
by the existing one failed-event attempt. The stream therefore remains bounded
by `2N+1 = 110,201` events, not an enlarged event allocation.

A conservative8,192-byte allowance covers up to two original4,096-byte raw
fallback lines: a replacement unavailable/nonreconstructible event and the
terminal failed event. The success upper already includes a normal pair for
every planned call, so adding both complete fallback maxima is conservative;
it does not permit two additional events beyond2N+1. A preflight/intent failure
invokes no primitive. An unretainable invalid value or oversized exception
representation remains unavailable, never silently truncated into complete
scientific evidence. No successful raw-fallback continuation is allowed, since
that would invalidate the compact bound.

The proposed conservative physical envelope inside16 MiB is:

| Component | Bytes | Rule |
| --- | ---: | --- |
| Successful compact events | 13,206,934 | Includes all110,200 LFs and framing |
| T plus A reservation | 65,536 | Actual combined upper61,952; no uncounted headers |
| One temporary T/A copy reservation | 65,536 | Full transcript duplicates prohibited; failed copy remains charged |
| Raw failure/replacement allowance | 8,192 | Terminal non-success paths only |
| Existing sink context plus terminal | 20,480 | 4,096+16,384; no metadata copies outside the copy census |
| Conservatively withheld rotation slack | 65,536 | At most16 times4,096; not measured stored bytes or an additional allowance |
| Total conditional envelope | 13,432,214 | Includes reservations, not an observed result |
| Unused difference below16 MiB | 3,345,002 | Does not authorize more calls, records or copies |

A partial write consumes its full reservation; positive short-write continuation
of that same event does not replay it. Any table-write failure consumes its
single opportunity. Further temp files, retries, exports, snapshots, full raw
copies or extra indexes invalidate this envelope unless separately bounded
and reviewed within the unchanged aggregate limits. The file writer's actual
20,480-byte metadata reservation is not counted twice as event payload.

The existing4 MiB shard and16-shard caps remain; the event capacity is still
total sink allowance minus metadata reservations. T/A and their temporary copy
are outside the sink's file allowlist but inside this transcript partition,
so the sink cannot itself receive the entire16 MiB and then ignore them. The
rotation-slack withholding is conservative capacity bookkeeping, not bytes to
add again to measured file sizes. Filesystem-block accounting, if required by
a later admission, is an explicit separate check, not this logical-byte proof.

## Required implementation, tests and remaining unknowns

The first source unit should implement only the bounded table/identity
validators and pure encoder/expander, with actual raw-byte equality tests.
Then install the synchronous append adapter at the exact owned call sites and
qualify source/sink/failure joins. Tests must cover all legal scope families,
index boundaries, wrong case/grid/scale/instance joins, signed zero and Decimal
quantum, Unicode fault escaping, missing/substituted intents, duplicate modes,
unknown/raw fallback, partial frames and every first/supplemental failure path.
Use synthetic extrema and owned fake callbacks; no scientific replay is needed.

A full successful stream adds110,200 raw parses, wire encodings, wire decodes,
expansions and byte comparisons under a straightforward one-pass design;
table validation, source hashing, writes/fsyncs, failed attempts and later
binder/auditor passes require their own source-derived counts. This is not a
measured CPU forecast. Avoid repeatedly copying the growing recorder snapshot
or expanding prior history for each return. No new primitive calls are allowed.

Before adoption, independently establish actual row/header fit, strict parsing
and lossless replay, installation access to all owned instances, exact source/
runtime/callable evidence, first-consumer/cache joins and complete failure
retention. The current callers do not yet supply this identity scheme. Table
order does not settle the unfinished driver's execution schedule. Source S
retention/copies, all other science artifacts, memory, external closure and
whole64 MiB fit remain unresolved. No numerical authority, policy change,
new8-hour balance, cap transfer or production durability claim is made.
