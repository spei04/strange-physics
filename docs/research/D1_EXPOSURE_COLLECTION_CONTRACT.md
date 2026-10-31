# D1 exposure collection: structural contract slice

Source-only implementation of the approved [bounded design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_EXPOSURE_INVENTORY_DESIGN.md).
The repository owner is the initial evaluation custodian; the protected actual
six-world inventory and its authenticated disposition remain pending. No history
was extracted and no overlap, scientific qualification or execution was performed
for this source checkpoint. The23 test functions contain91 authored cases/273 expected phases by AST census;
none has been imported or executed. Formatting, linting, typing, schema generation
and runtime qualification remain pending.

The scoped files are `tests/d1_exposure_collection.py`, its synthetic test module,
and this guide. These are private engineering helpers, not a public SDK or a new
registry. The existing `D1ExposureInventory`, its 1,024-row/one-MiB limits, physical
codecs, `NativeWorldCatalog` and supplied-inventory checker are unchanged.

## Exact byte and identity boundary

Public helper entrypoints are `parse_context(bytes)`, `parse_root(bytes)`,
`parse_part(bytes)` and `verify_collection(root_bytes, tuple[NamedPartBytes,...])`.
Only exact bytes/tuple/name types are accepted. No entrypoint accepts a prevalidated
model in place of raw bytes; internal models are metadata, not authority. Every
local DTO additionally inherits strict types, forbidden extras, frozen/default
validation and `revalidate_instances="always"`. The legacy projection codecs are
only populated through strict byte parsing here; arbitrary caller model instances
cannot bypass the raw boundary.

Sealed context/root/part bytes use the named profile
`python-json-sorted-compact-ascii-no-nan.v1`: Python JSON with sorted keys,
compact comma/colon separators, `ensure_ascii=True`, `allow_nan=False`, and ASCII
encoding of the typed JSON-mode values, including defaults and explicit nulls.
There is no Unicode normalization and this is not RFC8785/JCS. Bounded strict JSON
parsing precedes typed validation, which precedes exact raw/canonical byte equality.
Noncanonical whitespace/escaping/default omission, duplicate keys, nonfinite
numbers, extras, malformed UTF-8, type-changing representations and field overflow
are rejected. Canonical spelling of projection zeros follows the unchanged D1
codec. Named historical input bytes keep their original declared raw identities;
they are neither recoded nor read by this helper.

The context has no part digest or root reference. Its canonical digest binds the
collection ID, protocol/source/policy/extractor, exact UTC-second cutoff, input
metadata/edges, starting anchors and declared unresolved boundaries. Each part
binds that context digest. Root descriptors bind every part's exact raw hash,
byte length, index, role and row count. This graph is acyclic. The raw root hash
is returned separately; it is not the context hash. A coherent substituted root
and substituted parts can be structurally consistent: authenticating the expected
root/source/owner remains an external requirement.

The caller supplies the entire declared ordered part tuple. Missing, extra,
duplicated, swapped, renamed, corrupt or cross-context parts fail before any
collection result. Every record ID is unique globally, source IDs/digests join
named inputs, all world references resolve to physical-world records, and world
projections agree across those references. Role/count and per-input row denominators
are recomputed from every row. One row with several bindings to the same input
counts once for that input; bindings and repeated input-reference edges remain
present. No convenient page, first 1,024 rows or early no-match acceptance exists.

## Metadata that is retained

| Types | Scope |
| --- | --- |
| `CollectionContext`, `InputReference`, `InputEdge` | At most 256 named inputs, immutable Git commit/blob or run/attempt metadata (or explicit unresolved origin), raw byte size/hash, normalized relative path, up to 256 edges per input; at most 32 distinct starting anchors. All named inputs must be reachable through declared edges; cycles terminate under the bounded ID set, never trigger recursive reads. |
| `CoverageGap`, `InputCoverage` | Explicit earlier/external gaps and exactly one ordered disposition per input. Processed, unsupported and unknown describe the meaning of a collected input, not proof that the bytes were collected. Missing/unprocessed/failed extraction cannot be labeled a sealed success: the later writer must retain a separate failure record. |
| `SourceBinding`, `CompatibilitySet`, `Projections` | Up to eight raw input/locator/rule bindings per row; optional complete decoded-string digest/locator/codec triple. Exact JSON pointer syntax is checked, including the empty root pointer. World/query/history compatibility is independent, has a fixed reason plus bounded detail and refers to actual row binding indices. Compatible means a complete existing D1 projection is supplied; it remains a claim, not scientific evidence. |
| `WorldRecord` | Claimed physical meaning, including optional existing world/query/history projections. Unknown/incompatible dimensions have no fabricated projection. |
| `OccurrenceRecord` | Explicit run/attempt/job/terminal metadata, subject locator, distinct physical roles (or unknown alone), at most one world reference, and an explicit reason if no world is known. No actual execution membership is proved. |
| `MaterialRecord` | Source/fake/analytic/unknown material with provenance and optional world reference. Analytic-only labels are not automatically turned into physical observations. |
| `Part`, `PartReference`, `CollectionRoot` | Consecutive single-role parts, exact raw bindings, all input coverage, and three row-kind counts. |

Opaque IDs have a 128-character ASCII grammar; a schema cannot prove that an
issuer chose them independently of confidential labels or public blueprint keys.
All collection material remains private. A source projection or an analytic
number is not a valid source/run-to-output join merely because this schema accepts
its metadata. Future extractors and independent review must verify role semantics,
execution occurrence identity, actual world deduplication and historical coverage.
The three row counts are not distinct physical-world/execution counts or sample
sizes by implication. Two indexes referencing one event do not establish two
executions; resolving that meaning is deliberately outside this structural slice.

World compatibility remains visible when query/history is incompatible. The
helper does not call the legacy checker or conclude overlap/no-overlap. Every
root/result keeps material authenticity unchecked, historical completeness
not established and overlap conclusion unavailable. It cannot emit a custodian
approval or disclose the actual reserved worlds.

## Bounds, count conventions and failure behavior

The design's limits remain: 256 inputs, 32 anchors, 256 edges/input, one MiB per
input and 32 MiB distinct declared input bytes; 64 parts, 1,024 rows/one MiB per
part, 65,536 rows/16 MiB total parts; one-MiB root; 32-KiB canonical row; eight
source bindings/row. Each parsed document has depth24 and32,768-node ceilings,
which can reject before its separate row cap. Fixed reason detail is at most512
UTF-8 bytes, locators1,024, paths512, and opaque IDs128 ASCII bytes. The metadata
schema additionally bounds declared gap entries at256; overflow must become a
reviewed capacity gap, not silent omission.

A row's32-KiB bound covers its exact canonical serialized row representation.
The actual part-byte ceiling also includes separators/container/schema overhead;
root/part raw lengths are checked independently of normalized values. Original
input objects with the same digest and size share the distinct declared-byte
count, but retain every named input/path/edge/coverage entry. Conflicting sizes
for one digest fail. These are declared counts, not measured reads or cost refunds.

The verifier performs one bounded JSON parse plus canonical comparison per root
and supplied part, one exact part hash/size join, one complete record/edge scan and
one global reference/count pass. It performs no filesystem access, network,
source evaluation, project execution, endpoint/reference generation or overlap
computation. Parsing/hashing/serialization and every independent repeat verification
remain engineering work to record; no runtime or memory-performance bound is
claimed from this source census.

Malformed/missing/substituted bytes raise the existing `ContractViolation` error;
no partial result is returned as accepted and no failed denominator is rewritten
as zero. This pure function writes no failure receipt. The caller must retain
its original input/part census and error in the separately bounded diagnostic
writer before a real extraction is admitted. The prospective collection output
remains18 MiB (16 parts +1 root +1 diagnostic); this helper adds no output grant,
writer, hidden copies, logs or temporary files. Physical fit is unproved.

## Tests and remaining obligations

Tests use small synthetic JSON records, plus bounded metadata-only capacity
cases. They cover all-part substitution/coverage, late dangling references,
independent compatibility, raw strict booleans, opaque IDs/path grammar, embedded
locators, malformed/noncanonical bytes and overflow. Actual reference/predictor/
simulator/legacy-overlap entrypoints are poisoned. No actual historical input or
comparison world is present.

Remaining work includes JSON Schema artifact generation and parity qualification,
the frozen actual input manifest/cutoff, a confined actual-byte resolver (including
no symlink/nonregular/mutable-alias/trailing-file proof), reviewed source extractors,
execution/role/physical deduplication, complete overlap aggregation, durable failed
extraction diagnostics, byte-fit/work accounting, and protected custodian storage
and authenticated review. File paths/hashes here establish only consistency of
supplied metadata/parts. Owner-only permissions under the agents' shared OS identity
do not supply the missing custody boundary. Source authorization is unchanged;
real collection and any scientific batch still require their separate admission.
