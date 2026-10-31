# D1 primitive identity table: source-only slice

This slice implements only bounded construction and structural validation of
identity-table bytes from the [reviewed codec proposal](D1_PRIMITIVE_CODEC_CONTRACT.md).
It does not implement event encoding, activation, a source resolver, primitive
installation or sink I/O. No source authentication, exposure/history conclusion,
scientific qualification, allocation or full-transcript fit follows from a valid
table. The full 55,100-call plan and all existing ceilings remain unchanged.

## Files and boundary

- `tests/d1_primitive_codec_table.py`: standard-library-only byte boundary.
- `tests/test_d1_primitive_codec_table.py`: independent literal table and synthetic
  malformed/limit tests; no scientific modules, callbacks or file writes.
- This note: scope, static bounds and pending integration.

`build_table(identity: TableIdentity, source_binding_refs: tuple[str, ...])`
returns immutable canonical `bytes`. It revalidates the exact dataclass's raw
Python fields before encoding, constructs only the fixed rows, then passes the
actual bytes through `parse_table`. No caller can supply row policy or limits.

`parse_table(raw: bytes)` accepts exact immutable bytes and returns a frozen
`TableView`: raw bytes, their SHA-256, a new frozen identity, fourteen source
references and tuple-of-tuple rows containing only exact strings, integers or
null. Its `material_authenticity` property is always `unchecked`. This is an
output view, not a credential: no API accepts a caller-constructed view as proof.
A later decoder must bind the actual table bytes at its boundary; mutation via
Python's deliberate frozen-object bypass cannot turn an existing view into new
validated material.

The fixed protocol hash is the reviewed D1 protocol identity. Other source,
tree, manifest, recorder and codec hashes are checked for exact lowercase
hexadecimal shape only. Run/recorder IDs use the sink's existing opaque ASCII
rule `[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}`. Source binding references use that same
convention narrowed to 1–32 characters:
`[A-Za-z0-9][A-Za-z0-9_.:-]{0,31}`. They are opaque member names, never paths to
resolve; controls, whitespace, quotes, slashes and Unicode are rejected.
Several instances may name the same source member. Their distinct fixed
instance IDs and roles remain separate; source-member existence, callable
identity and actual execution are unchecked.

## Fixed structure and byte rules

The root has exactly the proposal's fields. The eight cases and all 105 rows
must have the exact order, arities, roles, profile/grid/scale/prefix joins,
ensembles, thirteen queries, seven constants and primitive/scope/value
vocabularies. Boolean equality cannot substitute for an integer; JSON floats
are not admitted. Unknown keys, duplicate JSON keys, rows, aliases, missing
parts and reordered rows are rejected. Only the fourteen bounded source-member
strings are supplied by the constructor in addition to the eight identity
fields; no actual scientific values are constructed.

Before JSON decoding, the parser rejects more than 57,856 bytes and nesting
deeper than root/rows/row. During decoding it rejects duplicate keys, floating
or nonstandard numeric tokens, and integer tokens longer than five digits
(excluding an optional minus, which cannot match a fixed nonnegative field).
This small schema has no compatible public `Message` model; importing the
existing model-based bounded parser would add unrelated contracts. The local
strict parser retains the same duplicate-key and pre-decode bounding principles.

After exact structural validation, raw bytes must equal sorted-key compact JSON
with `ensure_ascii=True`, `allow_nan=False`, separators `(',', ':')`, ASCII/UTF-8
bytes and one LF. This is the existing Python profile, not JCS. Each row's raw
serialization excludes LF; `r_j+1 <= 512` reserves its separator. The canonical
`rows=[]` header including LF is bounded by 4,096. Both checks are explicit;
caller data cannot increase them.

Independent static arithmetic gives maximum H=823 bytes and raw row maxima
I/P/E/Q/C/V/S/T = 68/16/12/39/15/25/12/26 bytes. The source-domain family-max
bound is therefore 3,625 bytes for a full table, including conservative
separators. These are deductions from field lengths, not measured encodings or
a replacement for 57,856/4,096/512 fail-closed caps. Valid extrema cannot reach
the larger declared caps. Tests use actual maximal identity/reference strings
and independently specified rows; separate test-only lowered caps exercise
inclusive separator/LF checks. Oversized, padded and overlong inputs are invalid
defenses, not claimed valid boundary examples.

## Static work and pending checks

One `parse_table` call scans at most 57,856 bytes for depth, performs one bounded
JSON parse, checks exactly 105 rows (at most seven atoms per row), serializes each
row once for its cap, constructs one expected 105-row tuple, serializes one empty
header and one full table, compares exact bytes and computes one SHA-256. Parser
allocation is bounded by input size/depth, followed by the exact schema. No
oracle, exp/log, native emission, prediction, label generation or filesystem
operation occurs.

`build_table` additionally snapshots eight identity fields, validates fourteen
source references, constructs one 105-row set and serializes one full table,
then uses the same parser. Repeated validation/construction is explicit work;
it is not another scientific call or a source-authentication check. A later
installer/decoder must account for its actual repeated passes and copies.

The 20 test functions define 95 authored cases (285 expected pytest phases).
They cover the independent complete table, maximal legal field
lengths, legitimate repeated source-member refs, immutable output snapshots,
raw-type bypasses, semantic joins, malformed/truncated input, canonical spelling,
duplicate keys, booleans, Unicode, nesting and pre-parse caps. They remain
unexecuted at this source checkpoint. Formatting, configured typing and the
bounded synthetic test unit require separate engineering controls.

Activation S/T/C/A joins, source/history authentication, table retention,
event-array encoding/expansion and acknowledgement, failure installation,
actual transcript/copy fit, aggregate science bytes and operational closure
remain later work. A table accepted here cannot activate a primitive or approve
an overall report.
