# D1 report structure: B1 sub-slice

Source only, 2026-10-30. `tests/d1_report_contracts.py` implements a structural
envelope from the [report design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md). Its78 authored
synthetic cases have not been collected or executed. This is not completion of
B1's numerical payload codecs or gate registry, not the material binder, and
not permission to run D1. Numerical, recorder, production and workflow source
are unchanged.

## Fixed identities and honest states

`fixed_row_manifest()` gives exactly135 ordered row identities:8 fixture,
40 belief,16 prior future,18 prequential,20 refinement,12 scale,16 stress,
4 primary and1 aggregate. Every row remains present after interruption, including
unrun rows. The exact case/grid/scale rules and comparison pairs come from the
frozen protocol. Per-kind denominators count all four states and are compared
with the actual rows; missing, duplicate, extra or reordered rows are rejected.

Dependencies identify the material needed for a completed row, not temporal
proof. Fixture rows have no row dependency. Prior and record0 prequential rows
need the corresponding fixture. A belief needs its fixture, same-grid prior and
record0 prequential row; D03 also needs its record1 prequential row. That second
row needs both M03/D03 fixtures and the matched M03/base belief. Refinement and
scale rows name their exact ordered belief operands. Duplicate stress rows add
the D03 record1 witness; force and weak rows name their exact matched beliefs.
Each primary row names the finest/base M belief and matching prior. The aggregate
requires the other134 rows, preserving the whole panel and diagnostics.

These dependencies do not create new scientific operations or replicates. They
do not prove that pools or forecasts preceded truth release. Intermediate
numerical results can be retained as partial material while the encompassing
report row is still attempted; a completed row means its entire declared row
evaluation is present. Row order is the report's fixed grouping, not the
operator's execution order.

A completed row requires a completion reference and has no partial/fault/reason
substitute. Failed rows require fault references and reasons. Attempted rows
retain an explicit unknown/in-progress reason and may reference partial data;
unrun rows have a reason but no returned material. A failed row cannot disappear
from a denominator. A declared complete execution requires all rows completed
and no control fault. A late control failure can retain all completed rows in
an explicitly incomplete envelope.

The schema is named `strange-physics.d1-report-structure.v1`, distinct from the
future full private report. `validation_scope` is always `structure-only`,
`material_authenticity` is always `unchecked`, and `qualification` and `utility`
are always `unavailable`. A structurally complete envelope therefore cannot
promote itself to a numerical pass or scientific rejection. Known numerical
outcomes, fixed gates and full forecast/contrast fields need the later reviewed
payload and binder. No arbitrary gate or `passed` field is accepted here.

## Scalar and table-reference codecs

`DecimalAtom` stores sign, coefficient digits and exponent. `encode_decimal`
and `decode_decimal` preserve exact Decimal quantum and signed zero, with no
rounding: at most120 digits, exponent -256 through128 and magnitude at most1e128.
`Binary64Atom` uses the exact canonical `float.hex()` spelling; malformed,
nonfinite, noncanonical and overflowing inputs fail validation. `IntervalAtom`
requires ordered endpoints. These are representation checks, not independently
computed error bounds or reference values.

`TableRef` identifies a proposed typed row-material table by opaque ID, role,
normalized relative path, codec tag, raw hash, optional separately identified
canonical hash, physical byte length and record count. The role must match the
first path component and proposed `<role>-v1` codec tag. Paths reject absolute
locations, traversal, empty components and foreign suffixes. Table IDs and paths
are unique; identical content hashes at different paths do not erase copied
bytes. A `TableSlot` points to an in-range record of the exact required kind.
Completed top-level rows cannot alias the same payload slot. The40 supporting
prior-pair views are not extra top-level rows or40 independent prior tables;
that alias binder remains outside this slice.

All referenced descriptors must join the enclosing table list and every listed
table must be used. Failure references use the separate fault role. Zero hashes
cannot stand in for missing material. The parser does not open paths, follow
references, verify payload bytes or resolve symlinks; its normalized relative
path is only the first prerequisite for the later confined resolver. The
proposed table codec tags identify roles, not an implemented raw-array format.

## Public validation boundary and resource limits

`parse_report_structure(raw)` reuses the project's bounded strict JSON parser:
at most4 MiB, depth16 and100,000 structural nodes before typed decoding. Duplicate
JSON keys, nonfinite literals, extras and malformed UTF-8 are rejected.
`validate_report_structure(value)` serializes/reparses the actual nested object;
`model_construct` and `model_copy` do not bypass that public boundary. Scalar
decoders likewise revalidate their actual models. Trusted internal model methods
are not alternate public validation entrypoints.

There are at most512 table descriptors, each declaring at most4 MiB and37,120
records. Their declared byte sum may not exceed the unchanged64 MiB science
ceiling. These metadata checks do not demonstrate any real writer's fit. The
report itself, native/reference arrays, manifests, copied inputs, temporary and
partial files, memory overhead and filesystem blocks still need a complete
physical inventory. The earlier16 KiB summary-row and512-byte compact-record
targets remain unproved. No scientific or engineering allocation is created.

## Later schema integration and missing work

No schema generator, schema/example JSON, CI registration or schema evaluation
runs in this slice. A later source-reviewed generator can use the same synthetic
valid/schema-negative/runtime-negative example separation as
`scripts/generate_calibration_fixture_schema.py`, importing this test helper
through the repository's existing bare-helper source layout. Proposed artifacts
are `contracts/draft/d1-report-structure.schema.json` and its structural examples.
Registration in `scripts/validate_contracts.py` must be explicit and reviewed.
The generator must contain no truth, predictor or oracle imports. No production
package allowlist addition follows from these test-side files.

JSON Schema can check fixed scalar/tuple lengths, ranges, extras and unavailable
claim literals. Ordered manifest, denominator, dependency, table-role/index,
canonical scalar and bypass checks also require runtime validation. Negative
examples must retain that distinction rather than claiming schema alone proves
cross-material validity. Generation and the configured engineering checks need
a separately bounded unit, with all failures retained.

The authored cases cover full/incomplete envelopes, all-row mutations, forged
nested objects, missing dependencies, substituted tables, exact scalar boundaries,
parser errors and declared-byte overflow using metadata only. They use no actual
D1 labels, forecasts, scientific helpers or reference calculations. Pending work
includes the numerical gate registry, real compact-array codecs and worst-shape
fit proof, payload/source/execution binder,40 prior aliases, actual failure
recorder installation, durable writer and final operational closure. No design
or structural acceptance substitutes for those gates.
