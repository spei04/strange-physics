# D1 event codec: one-event pure conversion

Source-only implementation of the successful intent/return portion of the
[codec proposal](D1_PRIMITIVE_CODEC_CONTRACT.md), using the
[identity-table boundary](D1_PRIMITIVE_CODEC_TABLE.md). No project helper was
imported or executed while authoring this slice. It does not implement sink
retention, activation, source authentication, callback installation or a full
transcript. No scientific inputs, predictions or reference values were generated.

Files are `tests/d1_primitive_codec.py`, `tests/test_d1_primitive_codec.py` and
this note. The implementation imports only standard-library helpers and the
pure table module. It does not import the recorder, an oracle, a simulator,
Decimal or a filesystem/network library.

## API and state boundary

`PrimitiveEventCodec(table_bytes, mode="encode" | "expand")` reparses complete
canonical table bytes once. Its direction is fixed. `convert(line)` consumes
one bounded immutable byte string, returning a frozen `Conversion` with status,
original input bytes, reconstructed raw Event, compact wire Event, table digest
and a bounded source-owned reason. Successful results have status `converted`;
`retention_confirmed` is always false and `material_authenticity` is always
`unchecked`. The output is conversion evidence, not an append callback result.

The cursor starts at sequence/ordinal zero. A successful intent reserves one
current complete intent. Its return must match every identity, scope and
argument component, not only the ordinal. A return advances the ordinal and
clears that intent; both events advance the contiguous sequence. Fixed
c00000–c55099 IDs must equal ordinals. More than one outstanding intent, a
return without intent, skipped/repeated sequence or substituted intent is
invalid. Scope reconstruction uses the admitted table's fixed rows, including
profile/case/grid, weak/strong channel, r0 and instance/primitive joins.

The cursor owns only one current intent and the small table; it does not retain
a growing event history. Any invalid or unsupported input consumes it, and
subsequent calls report `stopped` with the original reason without parsing.
It is stopped before conversion begins, so an unexpected internal exception
also cannot leave a reusable cursor. Deliberate private-state mutation,
concurrent/reentrant use and manufactured result objects are outside this
single-owner pure helper boundary; no downstream interface may treat them as
source or storage authentication.

The codec does not enforce the full scientific execution schedule or each
scope's multiplicity. Actual physical argument/query compatibility, first
consumer/cache/reuse witnesses and the exact 55,100-call composition remain
installer/report-binder obligations. A syntactically valid position key is not
proof that a scientific primitive ran or that its arguments match the declared
world. This prevents table labels from becoming fabricated material authority.

## Bytes and representation

Input is capped at 4,096 bytes before decode. A scanner rejects excess nesting
before the JSON decoder: at most four containers for raw Events and at most
two for compact arrays beginning `[`. Integer tokens are length bounded before
conversion; noninteger/NaN/infinite JSON numbers, duplicate object keys and
boolean substitutions in integer slots are rejected. Fields, arities and tags
are exact. The complete input must equal sorted compact ASCII JSON plus one
LF; no interior/trailing whitespace, alternate escape, numeric spelling or
missing/extra LF is normalized into acceptance.

Encoding forms the fixed `i`/`r` array, parses those actual proposed bytes and
reconstructs the raw Event. It requires byte equality with the original input.
Expansion reconstructs a raw Event, reparses it and requires byte-identical
wire reconstruction. All explicit null fields from the original Event schema
are preserved. Both output forms remain bounded by 4,096 bytes.

Decimal values retain their sign string, canonical coefficient digits and
integer exponent spelling without arithmetic. One zero digit, signed zero,
trailing coefficient zeros and quantum are preserved; leading coefficient
zeros, signed/padded zero exponents, non-ASCII digits, more than 120 digits or
exponents outside −256 through128 are rejected. No Decimal is constructed.

Binary64 values use the exact finite `float.hex()` language, checked lexically:
`[−]0x0.0p+0` for zero, `[−]0x0.` plus thirteen lowercase fraction digits at
`p-1022` with a nonzero fraction for subnormals, or `[−]0x1.` plus thirteen
fraction digits with canonical signed exponent −1022 through+1023 for normals.
The optional minus is the ASCII `-`. Uppercase, shorter/equivalent fractions,
leading plus, padded/negative-zero exponent, zero encoded as a subnormal and
nonfinite spellings are rejected. Strings are never passed through float or
Decimal conversion. Position keys retain all seven exact binary64 strings.

## Unsupported terminal boundary and failures

A raw `failed` Event or raw unavailable value is non-acknowledging
`unsupported`. An expansion input beginning `{` that passes bounded canonical
JSON parsing is likewise unsupported. The returned bounded `input_bytes` are
exact forensic input, not a verified/expanded fallback Event: terminal fault
schema, phase/current-intent/failure joins and actual `{` fallback writing are
not implemented here. Invalid oversized/non-byte input has `input_bytes=None`;
no truncated replacement is presented as complete evidence. Other malformed
bounded inputs are retained only as original input bytes in an invalid result.

No unsupported/invalid result includes output raw/wire bytes or permission to
continue. A future append adapter must recognize this disposition, retain any
eligible original canonical forensic Event once under the existing contract,
propagate failure without acknowledgement, and preserve original/supplemental
unknowns. It may not return normally merely because conversion or file
inspection succeeded. This slice cannot acknowledge intent-before-call or
return-before-handoff retention because it has no sink and invokes no callback.

## Work, tests and open integration

Each successful conversion performs two bounded JSON parses, four canonical
serializations, exact byte comparisons and fixed table/scope lookups. It does
not call exp, log, circle_constant, position, native emission, CDF or scoring.
Constructor table validation and all repeated conversion/audit passes are
additional cheap work to include in the later census. Raw/wire/result copies
are in-memory objects here; any retained copies must be counted by the eventual
writer. No whole-stream encoding or byte-fit batch was performed.

Sixteen test functions define 96 authored cases (288 expected pytest phases).
They use independently specified raw/wire vectors for all six scope
families (including the three endpoint channels), finite binary64 boundaries,
Decimal representation edges, full-intent substitutions, ordering, canonical
and malformed input, terminal/unsupported outcomes and stopped-cursor behavior.
Only tiny one-/two-call streams are constructed; there is no 55,100-call batch.
All parameter IDs are explicit short strings. Tests, formatting and configured
typing remain pending a separate bounded engineering unit.

S/T/C/A activation and retention, actual source/callable authentication,
primitive/recorder installation, terminal forensic replay validation,
scientific call multiplicities and physical-query joins, aggregate logical/
physical/copy fit, external closure and study adequacy remain unfinished.
Successful conversion alone establishes none of them and changes no limit,
threshold, allocation or scientific policy.
