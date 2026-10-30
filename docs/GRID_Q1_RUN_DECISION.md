# GRID-Q 1: proposed single diagnostic run

**Decision pending; execution remains disabled.** This proposes one finite
qualification run, identified as `grid-q1-cec936a2-once`. It does not allocate
resources, activate the entry, approve a scientific profile or report numerical
results. There is no owner decision record yet.

The source is [PR 136](https://github.com/spei04/strange-physics/pull/136), commit
`cec936a2a5a6534861eb9183861c4d6fcf931f67`, tree
`4a3c3623722dedfdd6f97dd7ed272fb256f350ec`.
It implements the immutable
[GRID-Q 1 handoff](https://github.com/spei04/strange-physics/blob/08ce72b1c82be1d299e873d84f6ba184a6387da6/docs/FINITE_GRID_CALIBRATION_HANDOFF.md);
the [qualification guide](https://github.com/spei04/strange-physics/blob/cec936a2a5a6534861eb9183861c4d6fcf931f67/docs/GRID_Q1_QUALIFICATION.md)
and [bounds contract](https://github.com/spei04/strange-physics/blob/cec936a2a5a6534861eb9183861c4d6fcf931f67/docs/GRID_Q1_BOUNDS.md)
contain the detailed formulas. Configured engineering integration has a separate
acceptance digest `534965235e2261334d12a19dd0644a60d8519368115ef38285e4b7e294860520`;
that is not numerical qualification.

## The decision

Approve or decline **one additional future unit**, at most 600 total CPU seconds,
1,800 total active-wall seconds and 72 MiB total logical retained output.
The existing product ceiling stays 64 MiB; a separate 8 MiB covers preparation,
source exports, logs and control records. All failures consume this same
reservation; no retry, refund, new environment, installation, acquisition or
capacity purchase is proposed.

Historical scientific costs and the remaining scientific balance are unresolved.
Approval must explicitly state how this finite additional unit relates to the
existing authority while preserving those unknowns. It must not create a fresh
eight-hour balance, reuse closed allocations, fabricate a historical upper bound
or assert that an aggregate scientific budget has been reconciled.

A second, inseparable decision is a **one-run storage amendment**:
20 GiB + 80 MiB available at start, then 20 GiB thereafter.
The existing 50 GiB-start/45 GiB-later policy remains for other numerical work.
The 80 MiB start reservation covers 72 MiB logical output plus 8 MiB of block/metadata
cushion; that cushion is not additional output permission.

At 2026-10-30T21:55:43.969473Z the host had 45,873,225,728 available bytes.
It was 7,813,865,472 bytes short of 50 GiB and 2,445,156,352 bytes short of 45 GiB.
The proposed start floor is 21,558,722,560 bytes, leaving 24,314,503,168 bytes at
that observation. These are illustrative host measurements, not a reservation;
preflight must refresh capacity. There are no installs, builds, downloads or
new datasets in this run. Logical bytes and allocated filesystem blocks are
reported separately. The cushion and periodic checks cannot guarantee an
atomic reservation against unrelated writers or arbitrary filesystem behavior.

The owner decision must name the exact source and one normalized, exclusive run
directory corresponding to this logical run identity, and join the admission's
resource/storage decisions. It cannot authorize another fresh directory.
The public source and private preparation remain disabled until that exact
decision and an independently reviewed admission exist.

## Fixed diagnostic, not an experiment search

All 27 profiles are the Cartesian product below; there is no adaptive extension.

| Dimension | Fixed values |
| --- | --- |
| Synthetic history | flat, boundary, interior |
| Equal-width midpoint cells in physical spring coefficient k |64,256,1024 on [0,4] |
| Terminal-x Gaussian residual scale |0.125,0.25,0.5 |
| Prior |uniform density in physical dk; each cell has mass 1/N |

Each history supplies one completed, explicitly synthetic record: mass 1,
anchor 0, zero impulse, duration 0.5, dt 1/64, no declared observation noise, and
frames at 0 and 0.5. Flat starts and ends at x=0; boundary starts and ends at x=1
with external label k=0. Interior starts at x=1 with external label k=1.5; its
observed terminal x must be the uniquely rounded binary 64 value proved by the
independent enclosure. Labels are construction metadata, not inferred answers.
Required velocity fields are visibly tagged unused zero placeholders, not a
physical observed velocity trajectory. Canonical physical-space and complete
observation/configuration identities are retained.

The separate future probe starts at x=1 and ends at t=1. Its predictions are
reused across scales only within the same exact history/grid ensemble.
Flat training likelihood therefore still has a nontrivial prior-predictive
future check. The likelihood uses terminal x only; the stated residual scale
does not establish calibrated noise, omitted-coordinate adequacy or justified
cross-record independence.

## Fixed gates and reference premises

| Check | Required limit |
| --- | --- |
| Native training and future endpoint absolute errors |1e-12 |
| Joint-log, centered-log-evidence and normalized-log errors |1e-9 each |
| Certificate components A, B and C |1e-9 each; fixed combined reserve 3e-9 |
| Finest-grid cell-TV / mean / second-moment / variance bounds |0.0081 /0.018 /0.019 /0.056 |
| Required 256-to-1024 refinement TV / mean / variance |0.001 /0.0005 /0.001 |

The 64-to-256 comparisons and the half/base/double-scale contrasts are retained
diagnostics, not invariance requirements. Flat continuous mean and second-moment
checks use independent exact formulas and their corresponding derived interval
limits. Boundary mass in the first and last quarters is also retained.
A gate failure does not suppress remaining profiles.

One reference wrapper owns six eagerly created, bounded legacy oracles; their
accepted guards and bytes remain unchanged, with no reset or replacement.
The independent 80-coefficient ODE calculation uses 100-digit Decimal arithmetic
and an endpoint enclosure 1e-60. It is not a finer native grid or the production
predictor used as its own oracle. The interior enclosure must lie strictly
inside one binary 64 rounding cell; a tie or unresolved enclosure is incomplete.

The finite reference proof bounds joint-log perturbation by eta<= 1e-56 and uses
positive-sum stability: log-evidence error<=eta, centered/normalized-log
error<= 2eta and normalized-probability relative error<3eta. A separate
post-ODE 40,000-basic-operation bound per vector covers the much smaller rounding
term; it does not include the endpoint series. The complete conservative
reference allowance 1e-48 encloses both terms and does not replace the native
1e-12 endpoint ceiling. Exact dyadic scale/prior arguments and uncertain pi are
handled separately; the declared joint-log domain remains[-32,4].

Each executed joint log is also compared with an outward independent interval
conditioned on that exact native endpoint. This separates native non-endpoint
arithmetic from ideal-endpoint error. Emitted binary 64 exponential weights are
normalized with outward intervals enclosing their exact positive finite ratios;
no correctly-rounded-native-exp assumption or unchecked float dot product is
used. Positive reference lower bounds and relative error r < 1 are prerequisites.
The certificate deliberately overcounts overlapping A/B/C allowances. These
proofs are conditional on this fixed domain and full coverage, not universal
floating-point or scientific adequacy guarantees.

## Full-success work and retained evidence

| Work | Planned count |
| --- | ---: |
| Candidate ensembles / models |9 /4,032 |
| Raw belief computations / raw binders / extra result parsers |27 /27 /27 |
| Training / future native predictions |12,096 /4,032 |
| Requested native frames |32,256 |
| Native normalizer exp / fsum / log |12,096 /27 /27 |
| Native Gaussian-constant and prior logs |12,150 |
| Additional emitted-weight binary 64 exp |12,096 |
| Reference lookups / nontrivial 80-coefficient series |16,129 /2,689 |
| Reference exp / log / trig / Machin terms |12,096 /34 /4 /128 |
| Reference normalizations / certificates |27 /27 |
| Native-conditioned arithmetic bounds / directed basic operations |12,096 /532,224 |
| Driver canonical hashes |60,486 |
| Ordinary artifact serializations / raw belief serializations |88 /54 |
| Retained artifact writes / operations / event lines |142 /48 /144 |
| Refinement / scale-sensitivity comparisons |18 /18 |
| Purchases / simulations / providers / measured publication calls |0 /0 /0 /0 |

Source-derived internal work is distinguished from observed driver counters.
Further contract work includes 44,352 prediction binders, 72 complete candidate
pool joins, 54 input-parser and 54 result-parser calls with two JSON decodes each,
and full-success 287 file/145 directory fsync calls. The driver final tail
encodes/parses its report; the admitted child adds one structural report parse
(two decodes), at most 144 event parses and 142 artifact hash readbacks. All
canonicalization, validation, imports, hashing and cleanup consume CPU and
storage even though they add no scientific forwards.

The strict report binds exact profile/gate names and limits, operation/work
keys, comparison kinds, and artifact path/hash/size identities. Events retain
unrun before work and attempted before calls; completed/failed states and later
unrun rows survive interruption. Successful artifact contents and directory
entries precede the final synced report, subject to supported local filesystem
fsync semantics.

- **Passed:** complete fixed census and evidence; every required diagnostic gate
  passes. This establishes only the finite diagnostic.
- **Complete negative:** complete census and evidence with one or more gate
  failures. Exit 1 is retained as a completed negative result, not a missing run.
- **Incomplete:** a computational, identity, resource, I/O or report failure,
  unknown usage, or partial census. Preserve the actual prefix and all partial
  bytes; never infer completion from file presence or retry in place.

Neither a pass nor a negative result establishes calibrated uncertainty,
selector performance, law-change adaptation, native Laplace accuracy or a
36-cell study result. Laplace work is not an added prerequisite for this diagnostic. The separate
full-study 1,168 MiB-versus 1 GiB capacity problem is unchanged.

## Resource and lifecycle accounting

| Included partition | CPU seconds | Active-wall seconds |
| --- | ---: | ---: |
| Once-only preparation, transport and final bookkeeping hold |30 |90 |
| One isolated child: imports, diagnostic and report readback |540 |1,620 |
| Controller, Git/identity scans and cleanup |30 |90 |
| Total |600 |1,800 |

The child has 539-second soft/540-second hard CPU limits and a bounded wall
observer. Controller wall is 30 seconds preflight plus 60 seconds terminal.
Parent and waited-child CPU, owned process closure and transport receipts are
retained. Overlapping cloud/client wall is counted once. Unknown or excessive
usage cannot become zero or a within-envelope claim; the full reservation stays
charged after preflight failure, timeout or lost acknowledgement. This is
known-process supervision, not arbitrary-descendant or blocked-kernel containment.

Controller complete/within-envelope status is provisional. Final acceptance
requires Lead's separate ledger closure for actual or measurably bounded
preparation, transport and final reporting, including all work after the
controller's last CPU/wall sample, within that same once-only 30 CPU / 90 wall
hold. Its reservation alone is not a measurement. Unknown usage or overrun
prevents final within-envelope acceptance even if the controller says complete.
Any invocation, including failure before a started/source marker exists,
consumes the single-run authority and reservation; marker absence permits
neither a fresh invocation nor a retry.

The 64 MiB product writer permits at most 160 artifacts/16 MiB each and reserves
512 KiB for the report and 128 KiB for events inside that aggregate. Full completion
expects 142 artifacts. Partial writes count. The separate 8 MiB control pool
includes all preparation versions (<= 1 MiB), seven source exports (<= 1 MiB),
active helpers/admission (<= 256 KiB), combined child stdout/stderr (<= 1 MiB),
verification JSON (<= 128 KiB), identity/process/accounting records and final
inventories (each parent metadata file<= 256 KiB). Before child work, 2 MiB of that
pool is reserved for verification and terminal records. It is one aggregate,
not an allowance per file. Overflow fails closed while available output is
drained; files are not deleted to make a run fit.

Before and after, verify the exact source/tree, interpreter, accepted complete
environment and 96 installed/source package files. Retain all raw product output,
events, strict report, bounded logs, admission/owner hashes, source/runtime
identities, process/usage records, logical/allocated-byte inventories and final
structural verification. Terminal readback/cleanup is attempted on failure.
A missing terminal receipt remains incomplete/unknown. Required unique failure
and acceptance evidence stays private; reproducible diagnostics have a review
date, not automatic deletion.

## Exact activation provenance

The preparation controller remains literally disabled. Only after admission,
make a fresh exclusive private run directory, copy the pinned controller/child/
guard, and flip only the controller's reviewed activation literal. Export the
seven exact public source files below into the matching scripts/tests layout.
Flip only the exported entry's `ENABLED = False` literal; verify its separate
hash and unchanged remaining AST. The checkout stays disabled.

The isolated installed interpreter invokes that exported entry through its
original CLI. Its resolved tests path imports bare `grid_q1_driver`; all helper
paths and the single EndpointOracle class identity are verified. Calling Driver
directly, bypassing the guard, resolving a different source or constructing a
second reference instance is outside this proposal.

| Public source export | SHA256 |
| --- | --- |
| `scripts/qualify_grid_q1.py` | `0fc72db22f2b6b4eb912ca414fa85faf00d6efbc500a58e49a0bb8e6b4f90394` |
| `tests/endpoint_belief_reference.py` | `039c212450d5cdec851c97e472d1b2fa20a590fa25bd3aa3099d5b04d4bbf4f8` |
| `tests/grid_q1_bounds.py` | `dc09e5defadee75d4fd9dc1950a7553645881e22a8cda6533daadb9ab5ee5c7f` |
| `tests/grid_q1_driver.py` | `700c90d4bf92805c392732fd82be513f0ef11421d208bbd8a50a5f842f270117` |
| `tests/grid_q1_evidence.py` | `f9d25bf1c2824d21fa152895d8a69d1ac92bf82e3647443d30b5edb57c5e61ad` |
| `tests/grid_q1_inputs.py` | `131b5528481461fd6d1fda453e919121fd5520e51a50b42b47e3379e5973546a` |
| `tests/grid_q1_reference.py` | `c96f0c498520f4836c05c865b2f9e64d4ea40f4d918483572828f1acd3c8ad50` |

- Source-pin manifest SHA 256: `09cae0ec4c12ce200a38ac822144410dfd00bedd873382fe2c266c73274c8017`.
- Flag-only enabled entry SHA 256: `af9070dec412e20df5a425cec6954b1c0b54d3872c02c22530723d2737ea6367`.
- Disabled controller SHA 256: `0257e7fb42dda974d73725d24cc2f644cc449c55ce7018811d82980bb109cd28`.
- Flag-only active controller SHA 256: `8c4cc7f10436d76fc1958546814919fb20cc24ca2626f5ad0dc444da22159b4a`.
- Child SHA 256: `2522baf92328126e744795f9ed3bc451a6596cf2c6addb2a3c4a94fb6568f812`.
- Guard SHA 256: `edfef49728f6d5965cf2d5ac75aa74830678343639690499ca14611950501ddd`.

These are source/proposal pins, not evidence that activation or numerical work
has occurred. Final owner authority, capacity selection, admission digest and
actual preflight observations remain absent. Independent Research and Platform reviews accepted the frozen scientific scope,
source/export identities, resource accounting and storage proposal. Their reviewed
preparation index is
`0ea09093a3723549f643fd393c7af05fdd33b361c8338d56b1e51d4413bcc678`.
Quality prepared the pinned handoff and resolved the review findings. These reviews
confirm a proposal fit for an owner decision; they do not grant execution authority.

## Parallel Laplace validation

Analytic and unit validation of Laplace can continue on checked tractable
references. Comparative acceptance of RA-N02.b additionally requires an accepted
grid reference, independently accepted and frozen RA-N03 development fixtures,
matching prior/likelihood inputs, preregistered accuracy and boundary tests,
label isolation, and complete failure/cost accounting. GRID-Q1 alone does not
freeze those fixtures or establish calibration. Neither completion of the
selector comparison RA-07.b nor enterprise infrastructure is a prerequisite.
