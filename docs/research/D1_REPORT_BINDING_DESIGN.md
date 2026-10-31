# D1 private report and evidence binder

Source design, 2026-10-30. This specifies remaining work-package B, not an
implemented schema, a runner, numerical admission or a scientific result.
It is based on adapter source `cd61304a32f0383f4f14698fa69f381d7e4a8411`,
which adds the complete D03 derived-material recheck to A1 `8e6b6a3`,
A2 `139ceb6` and the separate unit3 tuple repair. The material repair is
source-accepted; engineering validation remains pending. A separate in-memory
primitive-recording facade has passed source review and awaits engineering
qualification. Its durable sink and actual installation remain unimplemented
and required before a run; source acceptance does not establish durable failure
transcripts.
The [frozen protocol](RA_N03_CALIBRATION_SLICE.md),
[work package](D1_INTEGRATION_WORK_PACKAGE.md) and
[adapter proof](D1_PREFIX_EVIDENCE.md) remain authoritative for scientific
choices. This document changes no profile, gate, oracle guard or allowance.

Owner exposure-policy and custody decisions are resolved; the actual inventory
production, supplied-material checks and independent review are still pending.
A typed receipt or this report design does not establish historical completeness.

## Responsibility and implementation boundary

B converts retained material from units1–3 and A into a bounded, independently
checkable **private** report. It must prove that every number belongs to the
fixed input, prefix, probability vector and probe it claims, and that omissions
cannot turn into favorable averages. It does not call a predictor, simulator,
oracle, exp/ln, fixture generator or provider. It does not select sigma, add
worlds, release evaluator truth to a learner, authorize execution or rerun work.

Cheap reconstruction means parsing, exact byte reconstruction, hashing, interval
arithmetic, sorting/CDF sweeps, rational feasibility checks and existing pure
certificate/score functions. These are additional measured operations, not free
work. Reconstruction cannot prove that a fabricated but internally consistent
transcript actually ran; source/runtime pins, execution receipts and the retained
first-fault/call ledger supply that separate boundary.

Proposed implementation modules are `tests/d1_report_contracts.py` (strict
private persistence models and bounded parsing) and `tests/d1_report_binding.py`
(actual-material reconstruction and deterministic report construction). They
follow the existing test-helper convention, not a new production API. Synthetic
schema examples can be published; real reports, blueprints, inventory material,
truth, raw errors and host paths stay owner-private. No HTTP route or
`NativeWorldCatalog` change is required.

## One fixed row manifest

The report contains exactly **135 top-level rows**, in this order and with
these keys. This is a result denominator, not an execution-call or file count.
The case order is `M01,M02,M03,M04,D03,F02,F04,W03`; grids are `256,1024`;
scale order is `0.125,0.25,0.5`, except D/W have only `0.25`.

| Group | Exact keys / count | Required content |
| --- | --- | --- |
| Fixture | case; 8 | Unit3 outcome, public projection reference, private source/label/proof/inventory joins, unavailable reason. |
| Belief | case/grid/scale; 40 | Entire prefix result, all-node qualification, posterior future forecast/score, matching prior-pair reference. |
| Prior future | case/grid; 16 | Uniform physical-dk forecast on the same future probe, its own certificate/score and pre-truth freeze identity. |
| Prequential | case/grid/record0 plus D03/grid/record1; 18 | Forecast frozen before conditioning, exact observation release, signed innovation; second D03 row points to the M03 equivalence witness. |
| Refinement | case/scale/256-to-1024; 20 | All four fine masses per coarse cell, TV, finite mean/variance differences and fixed numerical gates. |
| Scale | M01–04,F02,F04 / grid1024 / adjacent scale pair; 12 | Half-to-base and base-to-double diagnostics. No scale promotion. |
| Stress | D03:M03/grid/base (2); F02:M02,F04:M04/grid/scale (12); W03:M03/grid/base (2); total16 | Matched identity, signed residual/width/score contrasts; duplicate repeated-loss check separately identified. |
| Primary | M01–04/grid1024/base; 4 | Exact posterior-minus-prior co-primary score enclosures, per-world errors, width/inclusion and evidence refs. |
| Aggregate | matched/base/continuous-dk; 1 | Equal-weight four-world decision, completed denominator, maximum matched-world absolute-error enclosure and all required-gate disposition. |

Twenty refinement rows are required even if a comparison has a failed operand.
Sixteen stress rows do not add worlds to the four-world primary denominator.
No stress, scale or grid row is a new statistical replicate. The separate
supporting material comprises 16 pool/candidate/future ensembles, 40
posterior–prior pairs and 56 unique future forecast/score contexts. Supporting
objects are not extra result rows or silently extra numerical constructions.

### Prior aliases are explicit

`d1_bounds.pair_scores` requires matching case, grid, scale, observation and
future identities. A single no-learning prior numerical forecast per case/grid
must therefore have **metadata-only pairing views** for the applicable posterior
profiles. Each view points to the same actual cells, uniform masses, endpoints,
finite/continuous CDFs, moments and score inputs, and binds the target profile's
scale/observation identity. A scale label does not enter its numerical calculation.
The original prior certificate identity is retained; it is not silently rewritten
to satisfy the pairing API. The binder checks every alias against its original
16-row prior material; it
must not accept arbitrary caller-supplied replacement arrays or regenerate
40 priors. Pure validation of 40 views is counted separately. Any necessary
unit2 adapter is a small reviewed interface change, not an extra CDF, prediction,
reference or normalization pass.

## Proposed persistence contract

Use the existing strict `Message`, bounded JSON, digest and finite-interval
conventions, with explicit revalidation of nested values at every boundary.
`model_construct`, `model_copy` and already-parsed Python objects are not trusted.
Reject extra keys, duplicate JSON keys, nonfinite numbers and duplicate row IDs.
This is an internal versioned contract, tentatively
`strange-physics.d1-private-report.v1`; it is not an extension of frozen SCI.

| Type | Required fields and invariants |
| --- | --- |
| `D1ReportIdentity` | Exact protocol digest, source commit/tree and ordered source/runtime pins; execution/admission/owner/inventory refs; run ID. No absent authority is filled with a fake zero digest. Missing external evidence is explicitly unavailable. |
| `D1MaterialRef` | Relative allowlisted role/path, codec version, physical byte length, raw SHA-256, optional typed canonical digest, record count. Raw and canonical hashes have different declared meanings. |
| `D1RowState` | Fixed row key/kind, state `unrun/attempted/completed/failed`, ordinal, dependency refs, completion evidence or first-fault ref, unavailable reason. State transitions are append-only; no reset or second attempt. |
| `D1GateResult` | Name from the exact row-kind gate registry; fixed limit or explicitly diagnostic `null`; observed interval/upper bound or `null`; `passed/failed/unavailable`. Missing measurements cannot pass. |
| `D1ForecastSummary` | Prior/posterior role; source/prefix/query/vector identities; separate finite estimates and continuous enclosures; mean, second moment, variance, tail quantiles, width, signed residual/absolute error, inclusion, losses; references to reconstructible material. |
| `D1ContrastSummary` | Exact ordered operands and kind; actual paired arithmetic and identities; no arbitrary threshold field; diagnostic outcomes separated from numerical gates. |
| `D1WorkCensus` | Fixed operation names with planned/attempted/returned/completed/failed/unrun/unknown counts where applicable; physical call IDs and reference-instance IDs; no summing overlapping CPU scopes. |
| `D1RetentionCensus` | Every physical file/copy, bytes, pool, digest, partial-file disposition; unmeasured bytes are unknown, not zero; source/copy and final-witness refs. |
| `D1PrivateReport` | Identity, exact 135-row manifest, global gate summary, censuses, first fault and supplemental failures, three outcome axes below. No user-supplied `passed` flag is authoritative. |

Decimal endpoints use a versioned canonical representation that preserves the
existing bounded Decimal domain (at most120 digits, exponent−256 through128,
finite magnitude bound). Do not reuse Q1's narrower decimal-text parser blindly.
Binary64 values retain canonical hexadecimal strings and round-trip equality;
conversion overflow is a contained validation failure. Canonical strings for
fixed limits are generated from the registry, not accepted with alternate
spelling. JSON Schema checks shape/ranges/extras; runtime binders enforce
cross-row material, exact coverage, chronology and arithmetic.

Proposed pure APIs, to freeze with the code review:

```text
parse_d1_private_report(raw: bytes) -> D1PrivateReport
validate_report_manifest(report) -> None
reconstruct_material(tables, actual_source_pins) -> ReconstructedD1Material
bind_prefix_material(material, key) -> QualifiedPrefixEvidence
bind_forecast(material, key, certificate) -> PredictiveEnclosure
bind_prequential(material, key) -> BoundPrequentialRow
bind_contrasts(material, forecasts) -> tuple[BoundContrast, ...]
build_report(material, run_ledger, retention_census) -> D1PrivateReport
validate_report_material(report, material, run_ledger) -> None
```

Only a separate bounded resolver reads files. It accepts the exact manifest,
rejects traversal/symlinks/foreign roots/duplicate physical aliases, reads at most
the declared cap plus one byte, then verifies hashes before decoding. The pure
binder receives actual bytes/tables, never an arbitrary callback that can obtain
new predictions. No serializer implicitly follows URLs or reads a private path
from candidate material.

## Actual-material joins, in dependency order

1. Rehash exact protocol/helper/production/runtime material and join the owner,
   admission, exposure and execution identities. Record which joins establish
   byte equality, supplied-inventory consistency and actual execution. None
   substitutes for the others. The independent inventory review remains an
   explicit prerequisite; absent review makes scientific acceptance unavailable.
2. Revalidate the complete eight unit3 outcomes, four rational-to-binary64
   coefficient proofs, 13 endpoint proofs, trace-center joins and actual public
   projections. A construction failure has no fabricated completed bundle.
   Check all available M03/D03/W03 shared future claims, not only M03 if present.
   Bind opaque public run/space/operation IDs while keeping blueprint mapping
   private. Preserve the honest F equilibrium1/8/private-force and public-anchor0
   separation and the unused terminal-velocity tags.
3. Verify the pre-label pool freeze from actual public structure/query/grid
   material. Join all 16 candidate sets to exact midpoints/cells, candidate
   configuration, later prefix and raw/canonical results. The pool factory must
   not have received observations. A digest created afterward cannot prove
   that ordering; C's event/dispatch evidence must attest it.
4. Reconstruct every native request/result and original attempt identity.
   Join node-major/record-minor slots, the first-record cache's single replay,
   D03's distinct second-record physical call and the 10,240 future captures.
   Validate both initial and terminal frames, including velocity/y values and
   full typed work facts, not just terminal x. Retain original result IDs/digests
   across reuse; equal physical queries do not merge logical slots.
5. Reconstruct each of the 40 exact belief input/result byte strings, validate
   with the existing raw binder, and join every ordered prediction digest and
   complete prefix. Verify the 25,600 actual emitted exp values and ratios from
   their exact sum. No zero, missing, failed or reordered node is dropped.
6. Bind independent endpoint/reference transcripts and per-instance counters.
   Reconstruct full-prefix ideal and conditioned-native interval algebra from
   already recorded inputs/returns. Enforce the fixed1e-48 reference reserve,
   actual1e-60 endpoint premise and unchanged1e-9/3e-9 components; no new oracle,
   exp or log. Compare all retained derived fields/digests to reconstruction.
7. Rebuild unit2 premises from those actual arrays and recompute the 40 posterior
   and16 prior certificates. Construct each of56 predictive contexts once from
   the matched values/vector, with two CDF envelopes and exact .05/.95 queries.
   Bind intervals and score differences to the same continuous physical-dk
   targets; literal finite-grid values remain separate fields.
8. Require persisted forecast identity and truth-release ordering before scoring.
   Rebuild 18 training innovations, including both actual M03-to-D03 equivalence
   witnesses. Private truth may have been generated earlier, but no scoring or
   learner release may precede the corresponding freeze. Subtract the exact
   recorded binary64 training point only after the forecast is fixed.
9. Rebuild all comparisons and the four base/finest M pairs. The aggregate is
   recomputed from those four actual continuous-score enclosures. Verify all
   required numerical gates and every fixed denominator before classification.

The two M03-to-D03 witnesses already cause two complete unit3 material
revalidations in A. Report readback is another explicit pass. Do not run the
producer to recreate missing truths or invoke `qualify_prefix` with a live
reference object during reconstruction. A missing required material field is
an unavailable proof, even if a hash or prior successful status exists.

## Fixed gates and decision semantics

The registry is source-owned, tested against the protocol and used both by the
builder and persisted validator. Missing, added, renamed or changed gates and
thresholds cannot produce a valid completed row. Diagnostics have `limit=null`
and no fabricated pass flag.

- Every record/node training endpoint and future endpoint:1e-12, with the
  separately bound1e-60 reference allowance and exact all-node coverage.
- Every profile: whole-prefix node, centered-normalizer and normalized-weight
  component bounds at most1e-9 each; conservative overlapping reserve at most
  3e-9. Preserve observed ideal-node and conditioned-native arithmetic evidence
  separately. Independently derived reference errors must fit1e-48.
- Finest grid: delta≤0.0081, mean bound≤0.018, second bound≤0.019,
  variance bound≤0.056. Coarse rows retain actual bounds without inventing the
  finest-grid thresholds for them.
- All20 refinements: TV≤0.001, finite mean difference≤0.0005 and variance
  difference≤0.001. Fine mass groups are the four actual cells in each coarse
  cell; interval comparisons must use the same emitted-vector definitions.
- D03 repeated-loss identity: compare the independently normalized
  `p_M03^2/prior_mass` vector with the actual D03 vector using derived reference
  and emitted-ratio enclosures. No new exp/log or invented scalar tolerance;
  a nonclosing proof is unavailable/rejected, not a successful identity check.
- Future scores: generalized-inverse tails exactly .05/.95, tie aggregation,
  support endpoints, actual truth enclosure, interval-score multiplier20 and
  exact ordered operands. Ambiguous crossings stay enclosed.

Use three orthogonal outcome fields:

1. `execution`: `complete/incomplete`. Infrastructure, retention, unknown child
   closure, an interrupted operation or an unfinished planned row is incomplete.
2. `qualification`: `qualified/rejected/unavailable`. A known contract,
   reference, numerical or repeated-loss defect is rejected and preserved;
   missing evidence is unavailable. A later transport failure cannot erase an
   already observed rejection or relabel itself a numerical failure.
3. `utility`: `local-screen-passed/screen-not-met/inconclusive/unavailable`.
   Compute only when execution is complete and every required identity,
   numerical and completion gate passes. Both aggregate upper bounds<0 pass;
   either lower bound≥0 does not meet strict improvement, including an exact
   tie; otherwise inconclusive. Missing primary evidence makes both aggregate
   differences null, not an average of survivors.

`completed` means a row's declared evaluation ended with retained evidence,
not that its scientific gate passed. Failed rows may reference partial raw
material but their absent final scores are null. Live or interrupted attempted
rows remain visibly attempted/unknown until an evidence-backed terminal
finalizer records their incomplete disposition; do not fabricate a simulator
failure or a completed measurement. `unrun` rows state which dependency or
first-fault stopped them. For every group, planned equals the sum of its four
row-state counts, and all fixed row keys are present in a terminal incomplete
report. If the final report cannot be written, the ledger/partial artifacts
remain evidence of incompleteness, not a substitute success report.

Matched inclusion/miss summaries use denominator4, force2, duplicate1 and weak1;
unavailable and indeterminate counts remain explicit. No pooled headline
coverage, binomial interval or confidence claim is produced. Preserve each
world's signed residual, width and miss even if the aggregate is favorable.
Stress effects may be finite-panel inadequacy evidence without being coding
errors; do not overwrite the separate matched utility outcome with an unduly
broad statement that D1 passed. No MAP, selector, calibrated-coverage,
unseen-world or full RA-N03 claim follows any outcome.

## What A2 retains, and the missing failure boundary

| Operation | Material actually available in current A2 | Required before C can execute |
| --- | --- | --- |
| Native precompute/observer | Full typed successful captures, attempts and spent slots in memory; native failure/result or partial capture may exist before adapter failure | Persist each attempted/result boundary and actual rejection object before later binding can fail; preserve original raw results even when a collector refuses them. Memory is not durable evidence. |
| Endpoint reference cache miss | `ReferenceCall` attempted/returned/completed/failed state, key, bounded returned-center text and completed value; completed cache and logical-slot maps | Persist transitions and cache hit/replay identities. A truncated/non-Decimal return is not reconstructible as a valid reference. Record that limitation honestly. |
| Constants | `constants_started`, failure flag and only a completely successful `ReferenceConstants`; local intermediate pi/log/Gaussian values disappear if the method raises | Wrap the existing instance's primitive calls with a narrow recorder that retains exact bounded input and returned value before the adapter consumes it; no second call. |
| Normalization | Attempted-profile set and counters; full `ReferenceNormalization` only on success. Local partial exp list/log result is not retained on failure | Same primitive-return recorder for every exp/log, linked to case/profile/node and source. Store accepted native exp conversions similarly. Preserve returned values on subsequent validation/serialization failure. |
| Derived interval algebra | Complete objects only on successful function return | Retain the actual preceding input/primitive-return material, first fault and last completed stage. Do not claim to recover discarded local temporaries; cheap later reconstruction is explicitly a reconstruction, not an original observation. |

A callback around `normalize()` alone cannot recover its lost partial exp list.
The narrow primitive recorder must run **before** the existing exp/log/pi
return is handed back to A, and record failures before propagating them. It
neither increments a reference call twice nor replaces an oracle instance.
Preflight/reservation/write failure consumes the operation according to the
future admitted lifecycle; it does not authorize retry. This adapter/driver
extension needs its own fake fault tests and source review before numerical
admission. This document does not pretend that extension already exists.

A failed retention write is itself retained where possible as a supplemental
fault; the original computation exception remains first. If both records are
lost, the final report must mark the exact unknown, not reconstruct a favorable
history. No postmortem reconstruction can change a failed attempt into a passed
original run or refund its cost.

## Exact bytes and bounded storage

Use versioned compact tables and shared templates, not one complete API JSON
file per prediction. A raw SHA-256 alone is insufficient. Every omitted shared
field must be deterministically reconstructible from actual retained material,
including IDs, configurations, ordered frames, work facts, result status,
normalizer shift/scaled sum and all actual binary64 values. At creation, compare
reconstructed bytes to the **actual** produced canonical bytes before discarding
the in-memory original. Reject a noncanonical/nonreconstructible result; retain
its bounded failure material and stop. Later binders reproduce the same bytes,
lengths and hashes and run the existing validators.

Do not regenerate scientific endpoints to reconstruct a result. Do not silently
replace raw input whitespace or alternate JSON spellings: retain raw bytes when
they differ, or declare the fixed canonical-input producer contract and reject
the deviation. The latter is the proposed normal path, with a bounded forensic
failure path. Malformed material exceeding that path's cap remains an explicit
retention failure; full data was not preserved. No silent truncation may be
labeled complete evidence.

CDF knots need not be stored twice. Retain the actual values/emitted vector,
certificate inputs, algorithm/codec version, knot counts/digests and quantile
summaries so all112 CDFs can be independently reconstructed with pure sweeps.
The107,632-knot source ceiling remains a reconstruction-work bound, not claimed
physical storage. If implementation chooses to retain knots, those actual
bytes/copies are charged; compression is never an assumed saving.

The following are **proposed fail-closed encoding targets**, not demonstrated
serializer fit or authority to run. Each line includes delimiters/newlines.
Encoding tests must prove fit over all supported fixed-domain shapes before
these limits can enter an admission manifest.

| Record class | Planned ceiling / count | Rationale and remaining proof |
| --- | --- | --- |
| Native successful capture table | 512 bytes/row;37,120 rows | Shared immutable metadata; actual variable frame values, slot/attempt joins and raw identities. Bound full reconstruction in B1; current expanded API objects do not meet this target. |
| Reference primitive-return table | 512 bytes/row;29,500 calls | 25,600 exp+46 ln+1 circle-constant+3,840 candidate position+13 fixture position. Input/return Decimal encodings and shared context keyed once. Machin's128 internal terms are counters, not128 extra public calls. Failure/detail records use the separate reserve. |
| Belief/node compact table | 512 bytes/row;25,600 nodes | Actual native joint/normalization/emitted values and per-record terms; references point to shared capture tables. Complete source-field census and reconstruction proof pending. |
| Top-level summary | 16 KiB/row;135 rows | Arrays/knots live in referenced tables, not recursively copied. Total row allowance2,211,840 bytes leaves report header/manifest space within4 MiB. |
| Decimal / binary64 / fault detail | ≤160 /32 /2,048 bytes per text field | Decimal codec must cover the bounded120-digit/exponent domain without loss; errors are bounded safe type/detail plus actual material refs, not unrestricted traceback dumps. |
| Ordinary artifact/report | ≤4 MiB per file | Shard compact tables by at most256 rows (≤128 KiB at512 bytes/row); keep reports/manifests bounded separately. Existing larger API parse limits are not retention permissions. |

All physical science output remains within64 MiB. A concrete **proposed internal
partition**, subject to the serializer proof, is20 MiB native capture/pool
material,16 MiB reference primitive/transcript material,14 MiB belief/derived
certificate/forecast material,2 MiB fixture/source/exposure proofs,4 MiB report,
4 MiB manifests/events/closeout,4 MiB failures. These sum to64; no reserve can be
borrowed twice or silently transferred. The full source/exposure material may
not fit its2 MiB target; actual approved inventory bytes and copy multiplicity
must be measured before freezing this partition. References to separately
retained pre-existing bytes require immutable hash/path/owner-retention joins,
not a claim that copied bytes are free or that inaccessible evidence suffices.

The first three row ceilings imply finite maximum table bytes, but do **not**
prove complete fit: headers, constants, candidate/normalizer templates,
reconstructed raw-exception bytes, inventory material, copied source/runtime
records, filesystem accounting policy, failed writes and final manifests must
also be included. Freeze exact file count and every remaining record maximum
from authored codec/driver source; those are unresolved here. If a target cannot
hold a legitimate fixed-profile record, report B1 incomplete and redesign
losslessly within64 MiB. Do not raise the protocol cap or drop evidence.

The writer reserves space for its terminal failure/report/closeout before work.
Atomic temporary files count while present; failed/partial writes and duplicate
copies count even when content hashes match. Check proposed and actual file/
pool/total bytes before and after writes; directory fsync and final external
witness are separate events. A successful report parse is not proof of durability
or child closure. Exact fsync/event caps and reserved closeout byte amounts must
come from C before admission, not from an optimistic count of successful files.

The other proposed pools remain16 MiB implementation/qualification,8 MiB CI and
8 MiB external control/closeout/publication:96 MiB total new retained output.
Nothing in B admits this allocation, inherits a consumed GRID exception or
relaxes capacity guards. Do not move science copies into another pool to evade
64 MiB. Historical protected holds and unknown costs remain unchanged.

## Work and failure accounting

Keep three inventories distinct: logical planned rows/slots, physical executed
calls, and validation/serialization/retention operations. Full-success reference
counts are37,120 logical requests/33,280 wrapper hits/3,840 actual candidate
position calls plus13 fixture calls. Native counts remain26,880 training plus
10,240 future calls/74,240 frames;40 beliefs/25,600 node weights;25,600 native
normalizer exp plus25,600 emitted conversions; independent reference25,600 exp,
46 ln and128 Machin terms. No report validation calls any of them again.

For one full binder reconstruction pass, explicitly count at least:

- Eight fixture joins and actual source/inventory reads; both D03 equivalence
  witnesses;16 candidate and16 future joins;37,120 original native-call material
  validations plus separately counted cache replay, callback and future reuse
  validations already present in A.
- Forty raw belief input/result reconstructions and binds;25,600 node/vector
  reconstructions;40 posterior+16 prior certificate/forecast constructions;
  40 metadata-only prior alias joins and paired-score validations.
- 112 CDF constructions/224 fixed-tail queries;143,360 exact feasibility additions
  and143,360 directed sweep updates for construction. Existing score/quantile
  revalidation rescans and any repeat report audit are additional, not included
  in those construction counts.
- 56 future scores,40 posterior/prior differences,18 prequential rows,20+12+16
  contrasts,4 primary rows and1 aggregate; all repeated score/panel validators
  and actual canonical encode/hash operations separately.

The adapter's2,001,920 full-joint directed operations,115,740 training-mean
operations,23,040 rational mass additions and51,292 adjacent Decimal endpoint
operations remain documented construction counts. The `cd61304a` repair adds
two pure D03 material rechecks: algebra over 1,280 nodes, 2,560 joint-enclosure
calls / 97,280 directed formula operations, and 2,588 adjacent Decimal endpoint
operations. These rechecks add no oracle, exp or log calls. Rebuilding material
during report readback is another counted pass. Source must enumerate exact
repetition, cache scope, failure branches and call IDs before execution; this
document is not a claim of a complete low-level census.

The planned numerical service envelope remains a prospective900 service-CPU
seconds/1,740-second terminal deadline from the protocol. It includes imports,
fixture generation, references, all reconstruction, serialization, fsync and
failure records actually inside the service. Counters are not extra CPU charges
added to the service measurement. External preparation, transport, independent
review and publication retain their own observed or unknown scopes;900 is not
a whole-operation CPU assertion. Earlier unknowns do not become zero, failed
units are not refunded, and the historical8CPU-hour/1GiB balance is not reset.

## Independently reviewable implementation packages

| Package | Concrete scope and interfaces | Meaningful automated acceptance | Exit gate |
| --- | --- | --- | --- |
| B1 — codec and fixed report contract | `d1_report_contracts.py`, schema generator/examples, focused tests and concise contract note. Fixed manifests/gates, bounded scalars/rows, compact shared tables and reconstruction codecs. Existing structural/runtime-negative schema audit registration. | Exact135-row manifest; changed/missing/duplicate gate or limit rejected; canonical decimal/hex boundary cases; nested bypasses; bounded parser; worst-shape synthetic encode/decode equality; altered table/template/attempt/status hashes; size/copy/partial-write overflow cases. No D1 truth or forward calls. | Generated schema/runtime parity; lossless actual-byte codec contract; all fixed counts and per-file/total budget targets either proved or explicitly blocking. No schema-only claim of cross-material validity. |
| B2 — material binder and deterministic classification | `d1_report_binding.py`, fake/rational tests, binder proof note. APIs above; actual reference-return reconstruction, prior aliases, future/score/contrast joins and report derivation. Narrow recorder interface proposal for C if needed. | Wrong prefix/node/order/source/attempt, swapped truth, duplicate slot/replay, stale aliases, fake digest-only evidence, changed emitted vector, missing reference return, D03 reused wrong posterior, altered CDF/quantile; pure rational surrogate scores/ties/ambiguous signs; complete failure/unknown/unrun denominator tests and forbidden-call poison. | Independent source/proof review; exact all-row outcomes with no survivor averages; no oracle/predictor/exp/log calls; derived allowances fit frozen gates or remain unavailable. |
| B3 — failure-retention integration, then C handoff | Narrow adapter primitive recorder plus fake driver integration, without enabling the runner. Complete attempted/returned/failed ledger, exact callback identity/restoration, fixed operation/file/copy census and all reservations. | Exception before/after primitive return; partial exp list; recorder failure followed by cleanup failure; no retry; original first fault retained; terminal serialization/disk-cap failure; completed-negative distinct from infrastructure-incomplete; all later rows explicitly unrun. | Actual trace boundary closes the separate partial-return retention gap; exact failure-inclusive counts/bytes and complete evidence reconstruction; operational source identity reviewed. Numerical allocation remains a separate gate. |

These packages can use synthetic maximum-shape values and previously exposed
analytic/rational surrogates. Engineering tests poison every real scientific
entrypoint. Do not generate D1 labels/forecasts to test a report schema. All
normal configured format/lint/types/test/schema checks and independent review
are required before integration; their source, failures and costs are retained.
A1/A2 formulas cannot change opportunistically while implementing B.

Remaining run gates are precise: accepted adapter and binder source/engineering;
actual exposure inventories and independent owner-reviewed joins; reference/CDF/
score proof; completed primitive failure recorder; exact source-derived work and
physical-byte manifest; frozen execution/operational identity; and explicit
numerical allocation/capacity decision. This source design neither reopens
resolved custody policy nor declares those material gates satisfied. The next
scientific step remains the one fixed D1 diagnostic, not a selector experiment.
