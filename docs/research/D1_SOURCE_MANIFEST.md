# D1 source-manifest declaration parser

This records the pure parser implementation and its ordinary engineering checks for
[D1_SOURCE_MANIFEST_DESIGN.md](D1_SOURCE_MANIFEST_DESIGN.md), including the reviewed
clarifications at `344c2a023a27d5e8b67c8a8db77f4f000fecbd35` and
`5b5b79a24f83eea98fbda6ddf27acacc95602fd6`. The authoring branch starts at
`2dee6722d8e0561898ce8689bf88be7d3e7447bc`. The initial authoring checkpoint ran no imports or checks. The later bounded
engineering verification is recorded below; no D1 scientific batch was run.
Initial code `0b4838360aadcd1f29a7194b794fffc3540cda29` is preserved; source repair
`a554201c317697c47c90d75e553659bc282c8cdc` and isolated-test successor
`5f5273a6692b03fce7dbcdc53973eff47302e8d1` preserve the review history.

The implementation scope is `tests/d1_source_manifest.py`, its synthetic test
module `tests/test_d1_source_manifest.py`, and this note. The preceding two
design-only clarification commits are retained separately. A final narrow design
wording change makes the already-enforced positive runtime-member length explicit. No SDK, exported schema, builder, resolver,
filesystem interface, installation hook or scientific driver is introduced.

## Raw-byte boundaries

* `parse_manifest(raw: bytes) -> ManifestView` validates exact S bytes and fixed
  first-version declaration joins.
* `parse_catalog(raw: bytes) -> CatalogView` validates exact policy bytes, closed
  row forms and the fixed role/definition/dispatch requirements.
* `compare_declarations(manifest_raw: bytes, catalog_raw: bytes) -> DeclaredSources`
  reparses both inputs, compares every policy projection, and joins the declared
  catalog hash and byte length to the actual supplied catalog bytes.

All views and nested records are frozen/slotted; sequences are tuples and raw
material is immutable `bytes`. They are output-only. No boundary accepts a
constructed view, and forcibly mutating one does not bypass the raw-byte check.
There is no authenticated, ready, installed or admitted flag.

The module imports only `hashlib`, `json`, `re`, `dataclasses` and `typing` plus
future annotations. It imports no D1/scientific helper or production module.
Existing `bounded_json` supplies the node-counting convention, but its Message
validation boundary has different number/error semantics and a production import
closure. This focused stdlib parser therefore implements the bounded scan and
strict JSON hooks locally, without changing or importing that utility.

## Fixed checks and declared comparisons

Before JSON decoding, enforce exact immutable bytes, the byte limit, depth 3,
2,048 nodes and no unfinished container/string. Count containers, object keys and
scalar values. Outside-string numeric/integer tokens have at most 10 characters
**including the sign**, checked before decoder entry; the conversion hook retains
the same bound defensively. Quoted digit strings are not numeric tokens.
Float/nonfinite tokens are rejected before numeric conversion. Reject duplicate
keys after JSON escape decoding. After parsing, require exact canonical compact
sorted-key ASCII JSON with one LF; no Unicode normalization or JCS claim is made.
Booleans cannot satisfy integer, case-index, row-code, length or limit fields.

S has exactly the reviewed root keys and 16 fixed limit values. Catalog has the
reviewed six root keys and no limit/digest additions. Both have at most 64 members,
exactly 5 definitions, 14 instances and 23 ordered binding/dispatch rows. The role,
case index, primitive code, definition ID, dispatch ID and capture tag are fixed;
only the final native slot has `native_callable_recorder_slot_v1`.

The four endpoint definitions share one checkout member and the exact
`endpoint_belief_reference` module/`EndpointOracle` method names. Every definition
joins a non-null member module. Python methods/functions require checkout source;
a runtime builtin requires a declared runtime member. Runtime-member lengths are
positive 1–67,108,864; zero/empty runtime artifacts are outside this first-version
declaration policy and would need separate review, without changing the maximum
or implying actual runtime-file fit. d4 remains a declaration
from the supplied catalog, not a selected or verified scientific emitter.

Mandatory checkout locators join the protocol/recorder/codec/sink root hashes and
required null/module declarations. Literal locator strings are globally unique
across both origins, not merely unique within each origin. Exactly one literal `uv.lock` checkout member
has a null module and joins `uv_lock_sha256`; duplicate IDs/declared locators,
alternate lock spelling/origin and a loaded lock declaration fail. Other member
references must exist. S and catalog member projections, definitions, instances,
installation reference and all binding projections must agree. The designated
catalog member is ordinary checkout source, within the catalog cap, and its
hash/length must match the supplied catalog bytes.

This rejects declaration-level aliases and disagreement. It does **not** detect
physical aliases, prove file contents against protected expected bytes, establish
a complete final catalog, or authenticate either input. Arbitrary matching
synthetic pins can describe a coherent but entirely untrusted pair. Actual T
identity/source-reference comparison, source/runtime/loaded-object resolution,
pass1/pass2 ownership and capture proofs, retention and outer admission remain
separate required boundaries. No S/T/C/A file is created here.

## Bounds and work census

| Operand/check | Fixed ceiling |
| --- | ---: |
| S raw bytes |65,536 |
| Catalog raw bytes |131,072 |
| Empty-row canonical header, each document |4,096 |
| Canonical row bytes plus one separator |512 |
| Ordinary checkout/catalog member declared size |1–131,072 |
| One literal lockfile declared size |1–262,144 |
| Runtime member declared size, with no runtime read |1–67,108,864 |
| Members/definitions/instances/bindings |64 /5 /14 /23 |
| Predecode nodes/depth/integer-token characters |2,048 /3 /10 |

Each successful parse visits at most 106 rows and performs at most 106 row
serializations, one full canonical serialization, one empty-array header
serialization and one SHA256 of the supplied document. It validates 23 slot joins,
five definitions and 14 instance rows. Member sorting is bounded by 64; fixed root
lookups scan at most four times 64 policies. The source-owned 23-slot tuple is
metadata, constructed without any primitive or dynamic source lookup.

A comparison invokes the two parsers once each: at most 212 row serializations,
two full serializations, two headers and two hashes; no hidden third parse or
source read. These are per-call ceilings; repeated caller validation adds work
and copies, with no attempt-state or aggregate caller budget supplied here.
The accepted inputs total at most 196,608 bytes. Raw input references,
ASCII decode strings, bounded JSON nodes, canonical temporary strings/bytes,
row/header temporaries, typed records and result-held references are separate
memory operands. This is neither an exact peak-memory measurement nor a general
heap/time cap. No payload or evidence file is written. The source design's
33,947,906-byte future two-pass read ceiling remains prospective and is not
consumed, granted or proved by this pure parser. Existing native checks and
repeated `verify_sources` work remain separately counted.

## Authored synthetic checks

Static AST inspection finds **114 cases across 21 test functions**, corresponding
to 342 prospective setup/call/teardown phases. All parameter IDs are explicit and
short; the maximum repository-relative node ID is 109 characters. These are an
authored census, not collection or execution results.

The independent fixture spells out the complete 23-slot catalog and all 16 limit
values without using implementation constants to create expected answers. It
uses invented opaque IDs, source hashes and runtime declarations; only its own
synthetic catalog bytes are hashed. Tests cover:

* Complete literal and runtime-builtin declarations, 64 members, immutable output,
  bounded run IDs and an attainable source row of 422 bytes plus separator.
* Both raw byte caps, key-inclusive node/depth guards before `json.loads`, signed
  integer-token length before decoder entry, legitimate long quoted digits,
  bytes-subclass rejection before overridden hooks, truncation, duplicate/escaped
  keys, noncanonical encodings,
  Unicode, booleans and invalid root/row/limit shapes.
* Otherwise-valid cross-origin locator collision, missing/duplicate/aliased lock
  declarations; lock-only size exception and catalog-cap isolation, fixed
  root-pin/member joins, definition kind/origin/module rules, fixed slot/case/tag
  policy even after coherent S/catalog mutations, and actual supplied catalog
  hash/length and full-projection disagreement.
* Constructed or forcibly mutated views failing the raw boundary, plus explicitly
  test-only lowered row/header guards. Each lowered cap accepts its inclusive
  threshold and rejects one byte less. The row threshold is the maximum across
  every row in all four arrays, so a different longer row cannot mask a missing
  separator. These probes do not pretend a valid fixed-domain row/header reaches
  512/4,096 bytes and do not alter the contract limits.

There are no temporary files, source reads, sinks, recorders, oracle/predictor
objects, primitive calls or protected/history inputs. An autouse import tripwire
rejects scientific/recorder/sink/retention imports within test bodies. Independent
engineering controls must still bind and enforce the actual qualification scope;
this fixture is not an OS sandbox or proof about arbitrary Python code.

The largest authored single raw input is the deliberate 131,073-byte catalog-cap
rejection (the analogous S input is 65,537 bytes). Ordinary encoded fixture shapes,
including the 65-member rejection and one maximum-width source row, are
conservatively below 49,152 bytes by their finite row/string counts. The largest
literal construction loop is 1,024 duplicate key/value pairs for a predecode-node
negative; member expansion adds at most 56 rows. Each case invokes at most four
parser entries, including any parses inside comparison. Generated raw inputs
per case are conservatively below 262,144 bytes; this is source accounting, not
measured allocation. Canonical/parser copies and pytest diagnostics are separate.
No test data is intentionally retained on disk; source, command logs, failure
output and qualification receipts must still fit the separately reviewed unit.

The first authoring AST check caught an indentation error in a new test branch;
it was repaired before the successful static census. Independent source review
then identified predecode-token timing, cross-origin locator uniqueness, frozen
assignment test style and row-cap isolation; the retained repair commits address
those findings and strengthen the otherwise-valid negative baselines. At that source-review checkpoint, no test
body or project import ran. The subsequent verification below used its own reviewed
ordinary engineering admission. Previous failed/closed units and
historical unknown costs are unchanged. No scientific allocation, activation,
source authority or whole-science fit follows from this source checkpoint.

## Verified engineering checkpoint

Source b639f8e00538a68fad209dd2e8ed5483dfae221f passed formatting/lint, full configured typing over
225 files, and all114 synthetic cases with342 ordered passing setup/call/teardown
phases. Independently bound collection recorded114 unique IDs and zero phases;
JUnit matched the executed cases, with no skips, xfails or forbidden events.
The two attempts closed all12 owned children. Source, helper and pinned
environment identities matched before and after checks. Formatting preserved the
test AST; the helper changed only docstring indentation, with identical normalized
text and otherwise identical AST.

The retained account charges58.724645CPU seconds and68.976981761wall seconds,
including closeout holds. Its final census is46 regular files/2,012,584 logical
bytes and six directories, with no links/FIFOs; the separate planning/review records
remain inventoried outside that unit. External control usage and peak memory are
unknown. Earlier failed units and scientific-budget uncertainty remain unchanged.
The private checkpoint digest is d3a7b3781b1b8a80083b3b31ec83e02a72b91220c90a8efa119adbe5c7e456a3.

One original ordinary PR CI attempt is next. That broader suite includes historical
physics checks; it does not grant source authentication, protected inventory,
installation, activation or D1 scientific admission.
