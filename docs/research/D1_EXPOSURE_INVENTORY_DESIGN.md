# Bounded D1 exposure inventory design

Status: source design for the approved exposure policy. No collector, schema,
inventory, overlap result, evaluation world, or numerical admission is created
by this document. The repository owner is the initial evaluation custodian.
An actual immutable six-world inventory and its reviewed overlap disposition
remain pending.

This design implements the direction in [D1 exposure policy
decisions](D1_EXPOSURE_DECISIONS.md), including custody commit
`666ca3850a7baf70689a9b462b94106881a27938`. The frozen
[D1 protocol](RA_N03_CALIBRATION_SLICE.md) remains unchanged, at SHA-256
`657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
Existing source implementation authority permits a bounded nonnumerical slice;
it does not supply missing execution inputs or a scientific allocation.

## Evidence that determines the design

The retained reconnaissance index contains 17 evidence anchors and five source
pins. Its SHA-256 is
`b31f74cea9d555190e152012cf9c15904a50d8496fb3f170dac880c43bed56a6`;
the accompanying decision note is
`d85186cd7e4a8fcbf9ee0f839cadba2bd9030b2f1bd0fc3b5973ecc358ee5914`.
These are starting references, not a complete leaf-artifact or execution census.

- GRID-Q1 has 27 profiles, 142 product artifacts and 144 events. Its disjoint
  64-, 256- and 1,024-cell candidate grids already identify 1,344 candidate
  coefficients. These are distinct from the count of evaluation occurrences.
- An early calibration receipt reports 70 noiseless, 64 noisy and 13 joint-noisy
  cases. The original inputs and test identities still need audited joins;
  those counts do not establish 147 distinct physical worlds.
- A retained 21,934-byte first-purchase freeze contains an exposed test catalog.
  Its six-world shape does not make it the untouched comparison set. Retained
  demo observations are 60,772 bytes; the GRID report is 130,725 bytes. These
  examples establish neither the largest historical input nor total bytes.
- Earlier/external history, all hosted CI occurrences and some source-to-record
  mappings remain unresolved. A software, qualification or CI label does not
  establish whether physical calculations occurred. Conversely, a numerical
  analytic vector does not by itself establish a physical observation.

The existing `D1ExposureInventory` stays at 1,024 entries and one MiB. Its fixed
world/query/history codec and supplied-inventory findings remain unchanged.
The new collection is a separate private contract that can retain more material
and explicitly report what cannot be projected into that codec. It does not
widen `NativeWorldCatalog` or turn a supplied receipt into proof of completeness.

## Frozen input boundary and actual-byte collection

The lead and custodian must first freeze a finite input manifest. It identifies
the source commits, run and attempt identities, selected CI run/job attempts,
artifact references, policy, extraction version and an exact cutoff. A timestamp
alone is insufficient: each included execution needs an immutable identity and
terminal status, or an explicit unresolved disposition. Any exposure-bearing CI
or engineering work after the reconnaissance must be considered when freezing
this manifest; referring to the older index does not silently include it.

Only named files and explicitly named children of retained indexes may be read.
There is no recursive directory discovery, archive search, provider query,
artifact download, project import, test execution or simulator/reference call.
A later source addition requires a new reviewed manifest version. Discovery of
an unexpected dependency is a coverage gap, not permission to follow it without
bounds. The manifest includes unresolved earlier/external boundaries explicitly.

Each input reference contains an opaque source ID, source kind, expected byte
count and SHA-256, immutable Git commit/blob or run/attempt identity where
applicable, and the referring index field or source locator. Paths are resolved
only inside the admitted private evidence roots or exact Git objects. Reject
absolute/traversing child paths, symlinks, nonregular files and mutable aliases;
no extraction through a worktree file standing in for an immutable Git blob.
A collector reads a bounded byte stream, hashes those exact bytes, checks the
expected size/hash, and parses that same stream. A stat check or producer-supplied
digest alone is insufficient. Hash mismatch, change during collection or missing
input yields retained failure evidence and no accepted collection.

Every extracted row binds its raw input digest and a bounded locator: for
example a JSON pointer and array index, or an immutable source literal range
with an extractor rule ID. Embedded JSON strings retain both the containing
input binding and the decoded-byte digest/locator. Decoder rules and text
encoding are explicit; there is no silent replacement of malformed UTF-8,
duplicate JSON keys, nonfinite numbers or ambiguous numeric representations.
An independently reviewed source rule may explain a retained record's meaning;
source text alone cannot establish that a candidate or fixture executed.

The first producer supports retained JSON and narrowly reviewed literal source
records. It never evaluates historical Python, expands executable loops, rebuilds
missing endpoints or infers a hidden law from observations. Nonliteral or
unresolved material remains accounted for as unsupported/unknown. Later source
extractors require a separate reviewed rule and fixtures, not a general-purpose
historical-code interpreter.

## Collection and part contracts

The collection consists of one root manifest, a complete declared set of part
files and one bounded diagnostic summary. All are private. The manifest binds
an immutable collection-context digest, source/policy/extractor identities,
input inventory, cutoff, expected part names/order/kinds, exact byte counts and
hashes, row counts by kind, and unresolved coverage dispositions. The context
contains no part hashes; parts bind the context; the root binds every part. This
avoids a self-referential hash while preventing parts from another extraction
being substituted.

Each part carries a version, context digest, consecutive part index and bounded
records with globally unique IDs. Record kinds are `physical-world`,
`execution-occurrence` and `design-or-analytic-material`. Input coverage is a
separate manifest table with exactly one disposition per expected input. All
records retain provenance; a row may refer to an unresolved world but must not
invent a world ID. Record references must resolve within the complete collection.
An occurrence row refers to at most one world; separate raw subject locators
represent separately evaluated candidates within one run. A world row may bind
one primary provenance record while every additional occurrence retains its own
source edge. Deduplication never discards those edges.

Contract IDs are opaque ASCII strings of at most 128 bytes; digests are exactly
64 lowercase hexadecimal characters, and Git commits exactly 40. Manifest-relative
paths are at most 512 UTF-8 bytes, locators at most 1,024, and a diagnostic reason
combines a fixed enum with at most 512 bytes of detail. A row is at most 32 KiB and
contains at most eight source bindings; additional evidence must use separately
bounded occurrence/material rows. One input has at most 32 declared reference
edges. These are overflow failures, not permission to drop references. Parts do
not embed raw source artifacts, observations or comparison answers as opaque
payloads. The implementation must enforce field limits during validation after bounded
byte/node parsing, before downstream normalization.

A verifier rejects missing, extra, duplicated or swapped parts, conflicting IDs,
wrong context/hash/size/count, dangling references and trailing undeclared files
inside the sealed collection directory. It checks global invariants before
issuing any finding. Parts are an internal storage boundary, not an API allowing
a caller to select convenient pages. No caller can treat the first 1,024 rows,
a prefix of parts, or an early no-match result as collection acceptance.

An incomplete extraction retains its input census, processed/unprocessed counts
and fault reason in a separate failure record. It does not emit a sealed success
manifest. The diagnostic writer reserves space before collection and retains a
bounded overflow/failure reason; it does not silently delete evidence to fit.

### Prospective bounds and preflight

These are proposed format and stop limits for the first implementation, not a
resource grant or evidence that all historical material fits. Each execution
manifest may tighten them; exceeding any bound stops with an explicit gap. The
actual named leaf census and retained-storage headroom must be checked before
an extraction is admitted.

| Boundary | Proposed maximum | Basis and limitation |
| --- | --- | --- |
| Named starting anchors | 32 | Exceeds the observed 17 anchors plus five source pins; these are not all leaves. |
| Distinct input artifacts/Git blobs | 256 | Accommodates the known 142 GRID artifacts plus the observed starting references; older descendants and CI may exceed it. |
| One input byte stream | 1 MiB | Aligns with the existing private parser boundary and exceeds the listed input examples; unseen large files are unresolved, not skipped. |
| Aggregate distinct input bytes read | 32 MiB | Finite metadata/retained-record read ceiling; the complete total is unknown. Repeated references reuse the verified byte binding without dropping occurrence IDs. |
| Parts | 64 | Supports a finite collection beyond the 1,024-row legacy inventory; the actual required part count is not yet known. |
| One part | 1,024 rows and 1 MiB | Both limits apply; a record too large for a part fails. The legacy inventory limit is unchanged. |
| All parts | 65,536 rows and 16 MiB | Both are independent aggregate limits. They provide representational room beyond 1,344 candidate identities without asserting that all execution occurrences fit. |
| Root manifest | 1 MiB | Covers all input dispositions and part bindings; no external undeclared continuation. |
| Diagnostic summary | 1 MiB | Includes failure/truncation reasons and counts; raw inputs are referenced, not copied. |
| New retained collection output | 18 MiB | 16 MiB parts + 1 MiB root + 1 MiB diagnostic; no hidden duplicate copies, logs or temporary part files outside this census. |

Structured JSON parsing retains at most depth 24 and 32,768 nodes per input or
part, plus the byte bounds above. Strings, references and locators need explicit
field limits in the implementation. The verifier processes a bounded collection;
it must not use an unbounded stream, nested archive or implicit recursive graph
to escape these limits. JSON node/byte limits can reject an input before its
row count reaches the maximum, which remains an explicit capacity failure.

The 256-file and 32-MiB read ceilings are provisional admission choices, not a
claim that a 142-artifact report exhausts the history. A metadata-only census of
the exact named chain must report observed totals, unresolved references and
headroom. If those do not fit, stop and review a changed bounded design/scope;
never truncate physical hypotheses or silently omit an incompatible category.

New writes must fit an explicit available output allocation before execution.
The proposed 18-MiB format ceiling does not enlarge the D1 protocol envelope,
reuse consumed engineering/CI allocations or justify deleting retained records.
Unfinished temporary files, diagnostics, failed attempts and terminal control
records count toward the admitted writer/output census. Existing retained input
bytes are reported separately from new writes; shared references are not charged
as newly copied data. Filesystem free space and retained obligations must be
checked at admission; this design makes no current headroom claim.

## Roles, identities and comparison

| Role | Evidence required | Comparison consequence |
| --- | --- | --- |
| Actual observations/truth | Retained output plus a valid source/run/attempt-to-record join | Physical world and available query/history comparisons apply. |
| Evaluated candidate/reference world | Retained evaluation membership or output bound to actual execution, not merely an authored grid | Physical world comparisons apply; retain its candidate/reference role and occurrence. |
| Analytic-only vector | Actual analytic evidence and documented absence of a physical-world interpretation for this rule | Retain analytic exposure; do not silently turn vector values into physical worlds. Ambiguous cases are unknown. |
| Source/fake design | Exact source or fake fixture bytes, without actual physical execution evidence | Retain design exposure; do not relabel fake labels as generated truth or claim human blindness. |

A material item may have several roles established by different evidence. Keep
those provenance edges; role precedence must not hide a physical exposure. An
unresolved role is counted as unknown and prevents an unqualified clean result.

Keep three identities distinct:

1. **Artifact identity:** digest of exact bytes. Mirrored identical bytes may
   share one verified input object; every declared path/reference is retained.
2. **Execution occurrence:** run/attempt/job/test or event identity, role and raw
   record locator. Replays and separate CI jobs retain distinct occurrences.
   Two indexes pointing at the same event do not create a second execution.
   Ambiguous execution identity stays unresolved rather than guessed or merged.
3. **Physical world identity:** a reviewed canonical physical meaning independent
   of display name, file name, fixture name, history ordering or execution count.
   Repeated worlds share an identity while preserving all occurrence edges.

World deduplication does not erase individual outcomes, occurrence denominators
or historical charges. Identical source declarations do not prove identical
execution histories. The producer reports unique worlds, occurrences, source
artifacts and role/compatibility counts separately; none is a statistical sample
size by implication. Global counts are recomputed from rows and edges, not
trusted from a supplied summary.

Compatibility is assessed independently for world, query and history, each with
`compatible`, `incompatible` or `unknown`, a reason and raw provenance. A noisy,
longer-history or differently sampled query can still expose the same world.
Its known world overlap must survive query/history incompatibility.

The first world projection targets the existing `D1WorldSignature` only when
retained evidence establishes its mechanism, coefficient and fixed structure.
It preserves that codec's canonical finite binary64 and zero rules. Query and
history projections separately require every existing fixed field, noise rule,
observation count and ordering constraint. No fabricated mass, time, zero noise,
missing observation or probe digest may be added to make old material fit.
`D1ExposureEntry` is emitted only when the complete existing identity is justified;
world-only matches remain first-class collection findings without a fake legacy
entry. Broader or unknown physical structures retain raw material and an
unresolved comparison unless a separately reviewed rule establishes their relation.

Incompatibility alone is not a no-overlap result. Coefficient comparisons must
establish which physical parameter the value represents, not match unrelated
numbers in analytic vectors. The existing four reserved coefficients and eight
D1 constructions remain development-only exclusions; renamed worlds and paired
variants cannot evade them. The reserved comparison check preserves the existing
coefficient exclusion even when an otherwise recognized mechanism differs.

Complete D1-compatible rows may be supplied to the existing checker in batches
of at most 1,024, each also within its one-MiB limit. A new collection verifier
must aggregate **every** batch and the world-only/unknown findings before
returning a collection result. It cannot convert the old checker's
`no-overlap-in-supplied-inventory` into complete-history acceptance.

The final result distinguishes detected overlap, no detected overlap within the
fully verified declared scope, and incomplete comparison. A detected overlap
remains visible even when other coverage is incomplete. Unknown role, missing
input or unsupported comparison blocks an unqualified no-overlap finding.
Historical/external gaps remain explicit even after the declared scope verifies;
only the approved claim boundary can determine how those gaps affect a future
study. A typed, hashed or signed receipt cannot establish missing historical facts.

## Custodian handoff and the six-world gate

The repository owner has accepted initial custody. This resolves responsibility;
it does not identify the actual six worlds or make the owner an independent
reviewer. Source implementation and peer review may proceed without seeing
comparison answers. Actual selection or generation of those worlds/labels is
outside this design assignment.

1. The lead hands the custodian the frozen policy, collector/source identities,
   complete declared exposure manifest and its unresolved-gap summary. Only the
   protected custody side receives material that could reveal comparison answers.
   Development-side reviewers can verify extraction and coverage using exposure
   provenance and synthetic tests without obtaining reserved-world labels.
2. The custodian identifies or deliberately freezes the actual six-world set,
   its provenance, reservation time and immutable inventory identity. A test
   catalog, empty inventory, six filenames or renamed exposed worlds is
   insufficient. Any earlier access is recorded; it cannot be undone by renaming
   the catalog or changing the custodian.
3. The custodian verifies six distinct intended comparison worlds and the exact
   inventory bytes, checks every declared physical exposure and all D1 reserved
   constructions/coefficients, and reviews incompatible/unknown coverage. The
   protected comparison records retain matches and blockers. Missing historical
   coverage requires an explicit disposition under the approved scientific claim;
   it cannot be converted into a complete-history certification.
4. Development receives a redacted receipt binding the collection/source/policy
   identities, an opaque immutable reserved-inventory reference, six-world count,
   custodian identity and accepted/blocked disposition. Detailed world mappings,
   coefficients, labels, private locators and per-world match answers stay on the
   custody side. A trusted owner review establishes receipt authority; a JSON
   field saying `approved` or naming the owner does not.
5. The lead checks the authenticated disposition and all independent numerical
   admission requirements. A new exposure, changed inventory, answer disclosure
   or material unresolved overlap invalidates the relevant acceptance and requires
   a new reviewed version. Preserve previous findings; do not tune or silently
   replace worlds after inspecting outcomes.

Answers must remain unavailable to Research, experiment selectors and article
writers. The custody store therefore needs an actual access boundary outside
those agents' accessible source/evidence paths. Owner-only Unix permissions
under the same OS identity used by the agents do not establish that boundary.
Do not send answers into the shared chat, source tree, public CI or publications.
This document provisions no storage, account, secret or data transfer. Until a
suitable existing custody boundary is identified and verified, label isolation
and the six-world gate remain unresolved.

Raw semantic hashes of a small coefficient space are not secret commitments.
Do not publish answer-derived hashes or a blueprint-to-inventory mapping as
proof of custody. Use an opaque reference backed by the protected immutable
record; any externally published commitment scheme needs separate review.
Repository ownership and redacted receipts alone do not establish independent
custody, historical non-exposure or human blindness.

## Independently reviewable source slices and checks

| Slice | Scope and prerequisite | Acceptance evidence |
| --- | --- | --- |
| Collection contracts | Separate bounded root/part/coverage/role types and strict parsing; preserve existing D1 caps and codec | Boundary, all-part, canonical-byte and cross-reference tests; unchanged legacy contract tests |
| One retained-input extractor | Exact frozen input/rule manifest; actual-byte hashing and role/occurrence joins; unsupported inputs retained as gaps | Synthetic byte fixtures for the rule; independent review of source locators before any real extraction |
| Collection verifier and private report | All-part aggregation, deduplication, separate compatibility and world-only findings | Overlap survives incompatible query, replay and rename; no partial/no-match success |
| Custodian interface | Redacted handoff/receipt contracts; no real comparison worlds or secrets | Strict public projection, authenticated-review boundary and blocked-gate tests |

These are source units, not new numerical work packages. Freeze concrete file and
test scope, check commands, cumulative CPU/wall/output limits, environment and
failure/closeout behavior before qualifying each coherent implementation. Use
existing engineering controls; no new supervisor or whole-host lease framework
is needed for pure bounded parsing tests. No source slice is considered runnable
or accepted merely because this plan names it.

Required negative tests use small synthetic byte fixtures and include:

- Missing/extra/repeated/swapped parts; wrong hash/size/context; duplicate IDs;
  dangling references; count mismatches; subset-only validation; a match in the
  final part after clean earlier parts; output/part/row/input-limit overflow.
- Missing/corrupt/changing input; unsupported or duplicate-key JSON; invalid
  UTF-8, nonfinite or noncanonical numbers; excessive depth/nodes; oversized
  embedded data; path traversal, symlink/nonregular input and mutable-source
  substitution. Every failure retains its denominator and bounded reason.
- Same physical world with renamed IDs, repeated jobs, replay, reordered history
  and incompatible noise/time; conflicting occurrence claims; duplicate index
  references to one event; unknown world/role; source-only and fake material
  falsely claimed as actual output; analytic values falsely used as coefficients.
- Missing or post-cutoff CI execution, source declaration without executed
  membership, unresolved earlier/external boundary and incompatible input that
  would disappear under a compatible-only filter. None produces complete-history
  or unqualified no-overlap acceptance.
- Empty, non-six, duplicate, exposed-test or unbound reserved inventory; each
  reserved coefficient and paired construction; owner text without trusted review;
  answer-bearing fields, semantic hashes or blueprint mappings in public output;
  subsequent disclosure or inventory change invalidating old acceptance.
- Failed/partial extraction, exhausted output allowance and closeout failure.
  Prior failure records and charges remain visible; no retry gets an implicit
  allocation reset or silently overwrites retained evidence.

Ordinary engineering checks cover formatting, configured typing/linting, schema
references and meaningful parser/projection tests. They must not invoke endpoint
or reference generation, evaluate candidate physics, make provider calls or
construct the actual reserved inventory. Hosted CI that runs historical physical
fixtures remains a separate exposure occurrence, even when this new slice's
own tests are synthetic.

## Accounting and remaining admission evidence

The execution record must separate existing retained inputs, new collector/test
outputs, source preparation, bootstrap/transport, engineering/CI checks,
extraction/comparison, failures, closeout and publication. A measured child or
job duration is not whole-operation CPU or provider cost. Unknown administrative
CPU and historical costs stay unknown; no unused reservation is a proven refund.
One physical execution referenced by several artifacts is not charged again;
new executions and failed attempts retain their actual identities and costs.

Before real collection, the lead needs the concrete contracts/implementation,
passing bounded engineering evidence, a frozen actual input census and cutoff,
reviewed source-to-record mappings, measured storage headroom and a finite
execution/output allocation that includes failure/closeout. Before scientific
admission, the actual protected six-world inventory and custodian disposition
must also exist. These requirements do not imply further source work is blocked:
the owner already approved bounded nonnumerical implementation. No D1 calibration
run, new physical observations, tuning or overlap conclusion is authorized here.
