# Disabled GRID-Q1 qualification driver

This source checkpoint implements the fixed [GRID-Q1 proposal](https://github.com/spei04/strange-physics/blob/08ce72b1c82be1d299e873d84f6ba184a6387da6/docs/FINITE_GRID_CALIBRATION_HANDOFF.md).
It has not been executed or calibrated. The proposed grids, scales and margins
remain fixed. A completed negative result is a valid diagnostic outcome.
There is no MAP selection, selector comparison, purchased experiment, simulator,
provider, measured publication or scientific-profile acceptance.

## Entry and interface

The literal `ENABLED = False` in `scripts/qualify_grid_q1.py` exits before
expensive imports. Its callable main also checks that flag. A separately
reviewed activation and exact source/install, scientific-accounting and storage
admission are required before invocation. It is not an authorization mechanism:
the trusted outer controller must verify the supplied source and authority hash,
own one process, enforce its admitted CPU/wall/storage envelope and retain
abnormal termination. No new supervisor or new allocation is supplied here.

The future invocation takes `--output` (a new exclusive private directory),
`--source` (exact commit) and `--authority-sha256` (the outer admission digest).
No source discovery, package install, subprocess, network or provider is inside
the driver. The reference instance is created once for that admitted invocation,
not once per retry. No automatic retry exists.

Dependencies: the accepted fixture/reference foundation and the independently
authored `tests/grid_q1_bounds.py` interface at `c0b162b8` must be composed.
The driver source alone must not be imported against a missing or different
bounds implementation. The production package remains unchanged.

## Exact observations and complete work

The independent interior ODE center has its separate absolute 1e-60 enclosure.
The driver proves this enclosure lies strictly between the two adjacent
binary64 rounding midpoints; a tie or unresolved enclosure fails. Only the
single rounded value enters the observed public bundle. Its ideal label,
enclosure, rounding cell and actual rounding-error bound are retained separately.
Boundary and flat observations are exact. Truth labels are construction metadata.

The exact recorded binary64 points, canonical shared physical-space digest,
full observed bundle, defaults, candidate pool/configuration and model order are
retained. Terminal velocities remain visibly tagged unused zero placeholders,
not physical velocity observations or simulator output.

Nine candidate ensembles feed 27 raw endpoint computations. The existing
predictor callback is scoped only to capture its actual calls/results and
validate their full expected input/order; it is restored in `finally`.
There are no added training forwards. Legitimate product failure returns are
allowed through to the original endpoint producer and its complete failure
result is retained. Future predictions use their separately bound requests,
and are reused across sigma only within the same exact history/grid ensemble.

Every operation has a durable unrun row before any numerical work, then an
attempted event before entry. Counters increment before individual work and
complete only after return. A computational exception stops dependent work,
retains the failed operation and leaves later rows unrun. An observed
qualification-gate failure does not suppress the other scales or grids.

## Independent arithmetic allowance

Reference arithmetic uses explicit 100-digit contexts, exact binary64 input
conversion and the unchanged ODE helper. It does not substitute the production
oscillator, finite normalizer or a finer native grid as its oracle.

For this finite domain, all joint log weights must pass the unchanged wrapper's
[-32,4] guard. Scales are at least1/8; recorded/training centers have magnitude
at most2, so a conservative residual bound2 gives endpoint-induced joint-log
error below 129*1e-60. Prior masses1/N are exact dyadic values. The reviewed
Machin pi error is at most 1e-60. The uncertain pi enters log(2*pi), whose
derivative is at most one on this domain. Scale and prior arguments are exact
dyadic values: their log derivatives can exceed one but their argument
uncertainty is zero. Correctly rounded log output error is separate. Thus a conservative joint-log reference perturbation
below1e-56 includes endpoint, pi and constants.

Each 100-digit Decimal operation has bounded finite rounding error; the direct
sums have at most 1024 positive terms. Magnitudes remain below 1e5; a generous
40,000-basic-operation envelope per vector bounds only post-ODE reference
joint/normalization arithmetic, not the endpoint series. The latter already
has its separate 80-coefficient, 1e-60 truncation/rounding proof. Subsequent
basic rounding is below 1e-86. Exp arguments lie in [-32,4], totals between
64*exp(-32) and 1024*exp(4), and reciprocal total below 1e13. These loose
absolute condition bounds apply only to that subsequent arithmetic rounding,
which stays below 1e-60 in absolute log and relative probability error.

The larger preceding joint-center uncertainty is propagated by stability, not
by multiplying it through those loose condition bounds. Write eta <= 1e-56
for the joint-log uncertainty. Positivity gives exp(-eta) <= Z_ref/Z_ideal
<= exp(eta). Full log-evidence error is at most eta; centered-log and
normalized-log errors at most 2*eta; normalized probability relative error is
at most exp(2*eta)-1 < 3*eta. Adding the smaller subsequent rounding gives a
conservative bound below 4e-56. The implemented 1e-48 complete reference
log/relative-probability allowance encloses both sources with margin. It is
not a new acceptance tolerance and does not replace the separate 1e-60
endpoint reference allowance or the observed 1e-12 native endpoint ceiling.

For each already captured native endpoint, the driver also forms an independent
joint-log interval conditioned on that exact binary64 endpoint, using the
existing Gaussian/prior constant centers with explicit uncertainty and outward
residual-square/division arithmetic. The difference from the executed joint
log bounds native non-endpoint arithmetic plus constant-reference uncertainty.
Its complete-vector maximum supplies node_other_arithmetic_upper. The original
ideal-endpoint joint-log envelope remains separate. This adds no exp, log,
oracle, prediction or artifact calls: 12,096 native_arithmetic_bound entries
perform 44 directed basic operations each (532,224 total). Those operations
enclose themselves and are separate from the post-ODE reference-center
40,000-operation rounding envelope.

Reference normalized probabilities are enclosed as center*(1 +/-1e-48)
using outward arithmetic. Every lower endpoint must be positive. Native
probability exp outputs are converted exactly to Decimal and normalized as
intervals enclosing their exact positive finite ratios. No assumption that
native exp is correctly rounded is needed. The inclusive ratio envelope
r/(1-r) requires r<1 and adds no log or exp calls. The certificate's A/B/C
overlap is explicit and conservative; each component still must be<=1e-9,
and the fixed total reserve remains3e-9.

All moment operations, probability aggregation, differences and displayed
bounds use100-digit directed intervals. The finite mean/second moment/variance
are exact-mixture enclosures, not an unchecked binary64 dot product. The
continuous certificate must be applied to those intervals, not to a rounded
display point without its width.

## Gates and retained artifacts

The exact endpoint, node-log, centered-log-evidence and normalized-log gates
are retained separately. The maximum and centered normalizer are never
recombined to discard a small correction. Research's certificate supplies the
outward endpoint allowance, A/B/C, cell-TV and continuous predictive bounds.
The finest gates remain0.0081/0.018/0.019/0.056. All flat continuous moment
checks use the independent four-trigonometric-call formula.

There are18 refinement comparisons: all64-to256 diagnostics and all required
256-to1024 TV/mean/variance gates. Another18 comparisons retain half-to-base
and base-to-double scale sensitivity without asserting invariance. Each
case retains first-plus-last-quarter boundary mass.

The strict `GridQ1Report` schema binds all 48 operation keys to their exact
kinds and all 27 profiles to their exact ordered gate names and thresholds.
The 12 base gates are mandatory; terminal flat cases additionally require
both exact-moment gates, whose limits equal the corresponding reported
derived mean/second bounds. All 36 comparison keys bind their kind, three
gate names and exact required or diagnostic-only thresholds. Required gates
cannot be replaced with arbitrary names or limit=None. Complete passed/failed
reports require every planned work key with exact attempted/completed counts,
the full reference census, and exact path/hash/size joins for all case evidence
and certificates in the final artifact list. Incomplete reports preserve
actual partial counters and ordered operation/case/comparison prefixes,
including a flat-moment failure leaving an actual 14/12-gate update prefix.
They do not fabricate completed flat checks or become terminal passes. Passed means this fixed diagnostic's numerical
gates passed; scientific adequacy is still explicitly unaccepted. Incomplete
or failed results produce nonzero exit status. Unexpected failure of final
report writing must be retained by the outer admitted controller as incomplete.

Artifacts are generated fixed filenames with exclusive no-follow writes:
raw candidate inputs/results, original raw belief inputs/results, compact
per-node captured values/hashes, reference values, exact emitted weights and
probability intervals, future vectors, certificates and the final report.
No arbitrary path extraction or overwrite occurs. Creating the private root
syncs its parent. The initial event file is synced with its containing directory
before numerical work. Artifact contents and directory entries are synced
before their descriptors become complete; the final report must join this
writer's completed descriptors and its contents and directory entry are
synced before return. I/O and unsupported-filesystem failures propagate and
prevent successful completion; partial files remain for outer readback.
This follows local fsync semantics, not a guarantee against unsupported
filesystems, hardware failures or a dishonest outer controller.

Maximum 160 artifacts,
16MiB per artifact,64MiB aggregate with reserved512KiB final report and128KiB
event stream. These are prospective hard checks, not an allocated allowance
or evidence of actual output fit. Parser limits are512KiB/20depth/40000nodes.
The outer controller must census failed/partial files too; the final index
never makes an incomplete operation successful merely because a file exists.

## Full-success source census

| Work | Exact planned count |
| --- | ---: |
| Candidate producer entries / explicit caller binders |9 /9 |
| Models produced |4032 |
| Raw belief compute / raw binder / extra result parser |27 /27 /27 |
| Training native predictions / observer binders |12096 /12096 |
| Future native predictions / explicit binders |4032 /4032 |
| Native prediction frames requested |32256 |
| Native normalizer exp / fsum / log |12096 /27 /27 |
| Native Gaussian-constant and prior log calls |54 +12096 |
| Explicit mixture-weight binary64 exp |12096 |
| Reference training / future / label lookups |12096 /4032 /1 |
| Reference nontrivial series / coefficients each |2689 /80 |
| Reference exp / log / trig / Machin terms |12096 /34 /4 /128 |
| Reference normalization / certificate |27 /27 |
| Native-conditioned arithmetic interval bounds |12096 |
| Additional directed basic interval operations |532224 |
| Driver canonical hash calls |60486 |
| Ordinary artifact serializations / raw belief serializations |88 /54 |
| Fixed generated artifacts |142 |
| Operation rows / event lines |48 /144 |
| Full-success file fsync / directory fsync calls |287 /145 |

Counts above are attempted/completed driver calls or source-derived internal
work as explicitly named. The native predictor self-binds once per call; the
endpoint producer additionally binds each training call. With explicit caller
joins this gives44352 native prediction binder calls on full success.
Candidate validation occurs in producer9, external caller9, endpoint27 and
raw-result binder27:72 complete-pool joins. Pydantic structural validation,
canonical encoding within those contracts and model construction remain real
CPU work, not free or hidden extra scientific forwards.

Raw belief paths entail54 input-parser and54 result-parser calls, each with
the existing bounded parser's two JSON decoding passes. Driver artifact
serialization does not count those internal canonical-hashing passes as a
new numerical operation. The final fixed tail performs one report encoding
and one bounded report parse (two JSON decoding passes); its success is only
established by a retained complete final report. No collection or numerical
probe was used to derive this census.

Synthetic failure tests poison all five real EndpointOracle operations.
They target directed tiny allowances, exact normalization, finite report
bounds, failed attempts, one-rounding evidence and private exclusive outputs.
They are authored but unexecuted at this checkpoint. The old oracle, accepted
old numerical tests and production source/lock/build inputs are unchanged.
