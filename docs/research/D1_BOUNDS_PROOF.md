# Conditional D1 moment, CDF, quantile and score bounds

This source-only unit implements the algebraic part of
[RA-N03-D1](RA_N03_CALIBRATION_SLICE.md), protocol SHA-256
`657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
The numerical batch remains disabled. No D1 labels, forecasts, reference
solutions, tests or calibration results were generated while authoring it.

The three files are `tests/d1_bounds.py`, `tests/test_d1_bounds.py` and this note.
The implementation reuses the unchanged Q1 directed interval operations and
bounded Interval/endpoint/arithmetic messages. There are no physics, oracle,
transcendental, provider, simulator, filesystem or process calls in the new
bounds module. The tests use rational distributions and deliberately synthetic
surrogate arrays; their premise snapshots are not physical D1 qualifications.

## Trust and exact joins

These are conditional internal helpers, not an authenticated report format.
A producer still must establish the named source/protocol, actual public
prefix, complete reference work, emitted weights and ordered future vector.
A hash-shaped string or a conditional certificate cannot establish those facts.

`D1Identity` binds case, grid, scale, source commit, protocol, observation,
future query, future vector, normalized-mass material and evidence identities.
`D1PrefixPremises` requires one record for M/F/W, two identical recorded
binary64 points for D03, the exact 256 or 1024 indices in every training channel
and the future channel, and no failed or omitted nodes. D/W accept base scale
only. The recorded training value is an exact point, not an interval-valued
observation. The whole-prefix arithmetic remainder includes native summation of
all record terms; an individual-record remainder is insufficient.

Certificates retain their premise snapshot. Predictive entry recomputes the
certificate's arithmetic and gates, checks actual array lengths and named
identities, and rejects failed premises. Score joins recompute moment-expansion,
quantile and score expressions and require the same query/source/truth for the
prior and posterior. A later bounded driver/report binder must still bind the
actual raw arrays and reference artifacts; this module does not discover them
or authenticate arbitrary caller-created output objects.

## Prefix and moment derivation

For record j, `f_j(k)=q_j*cos(sqrt(k)/2)`; `|f'_j|<=|q_j|/8=D_j`.
The admitted recorded point lies in `[q_j/2,q_j]`. With
`epsilon=1e-12+1e-60`, a sufficient residual bound is
`R_j=q_j/2+epsilon`. All values are nonnegative and evaluated outward.

For the Gaussian working loss, the whole-prefix log derivative is bounded by

    L = sum_j R_j*D_j/sigma^2.

Every cell has half-width `h=2/N`, so its unnormalized density differs from the
midpoint density by a log factor of at most `a=h*L`. For a uniform physical-dk
prior, the continuous cell masses are bounded reweightings of the midpoint
masses with factors in `[exp(-a),exp(a)]`. Positive normalization gives a
total-variation bound no larger than `tanh(a)<=a`; using `a` is conservative.
The implementation evaluates neither exp nor tanh.

Each record's endpoint-induced log error is bounded by

    R_j*epsilon/sigma^2 + epsilon^2/(2*sigma^2).

Sum those contributions before adding the independently established complete
native/reference arithmetic remainder. Component A is the maximum of that
propagated whole-prefix bound and the observed whole-prefix error envelope.
B bounds centered log evidence; C includes normalized-log and emitted-probability
representation error. All three must be at most 1e-9. The single fixed3e-9
reserve is overlapping sufficient bookkeeping, not three independent noise
sources. A duplicate contributes twice to the derivative and endpoint sums,
but does not create a second reserve. Failure of any component remains failure.

The resulting `delta=a+3e-9` is a conservative total-variation bound between the
continuous posterior's cell masses and the SAME normalized emitted-weight
vector used below. A bound to a different normalizer/vector is insufficient.

For future `g(k)=cos(3*sqrt(k)/4)`, use `|g|<=1`, `|g'|<=9/32` and
`|(g^2)'|<=9/16`. Relative to the emitted midpoint moments:

    mean error <= 2*delta + 9/(16*N) + epsilon
    second-moment error <= 2*delta + 9/(8*N) + 3*epsilon
    variance error <= second_error + 2*mean_error + mean_error^2.

The variance expression uses `|E[g]|<=1`; the true variance is also in [0,1].
The original finest-grid numerical ceilings (.0081, .018, .019, .056) and
endpoint/log ceilings are preserved. They do not measure predictive usefulness.

The no-learning reference has exactly uniform cell masses1/N, so its
`delta=0` and likelihood/reserve terms are absent. It still requires qualified
future endpoints and spatial/endpoint moment allowances. The prior entry
rejects nonuniform supplied mass intervals. It does not reuse a posterior's
mass bound or imply that its predictive function is evaluated exactly.

## Cell CDF and quantile enclosure

Each future cell is enclosed by

    image_i = [native_i-epsilon-(9/32)*h,
               native_i+epsilon+(9/32)*h] intersect [-1,1].

Let `p_i in [l_i,u_i]` enclose the exact normalized emitted weights, with one
common feasible probability vector summing to1. All D1 weights must be strictly
positive; no vanished node is discarded. The generic synthetic CDF kernel also
allows zero mass for algorithmic test distributions.

At any threshold x, entire cells with `image_i.upper<=x` certainly contribute;
cells with `image_i.lower<=x` may contribute. Therefore

    F_lower(x) = max(0, sum_certain l_i - delta)
    F_upper(x) = min(1, sum_possible u_i + delta).

The subset mass error is at most delta by total variation. Within a partially
crossed cell the kernel makes no unproved uniformity assumption. Outward sums
and feasible mass totals are mandatory. Below the exact global support the CDF
is0; at or above its upper endpoint it is1. These support rules remain necessary
when delta exceeds a quantile tail. The generic kernel is bounded to [-2,2] so
the literal emitted distribution can include endpoint roundoff; the continuous
D1 target always uses [-1,1].

The implementation sorts lower and upper image endpoints, accumulates each
mass once in each of two sweeps, and processes every equal-breakpoint group
before considering a threshold. It does not recompute an N-term CDF at every
one of O(N) breakpoints. Bounds are right-continuous monotone step functions.

For `Q(p)=inf{x:F(x)>=p}`,

    inverse(F_upper,p) <= Q(p) <= inverse(F_lower,p).

Use exact Decimal .05 and .95, a >= comparison and no interpolation. Quantile
intervals may span multiple cells or support endpoints. They are retained as
ambiguous enclosures, never replaced by a chosen midpoint. If a score sign
remains decidable over that enclosure, the fixed rule can decide it; otherwise
the result is inconclusive. This follows protocol paragraphs100–106 and does
not require an impossible exact point quantile for a continuous target.

The finite emitted distribution is separately enclosed with point cell images
and delta0. Identical endpoint ties have their masses accumulated together.
The returned finite enclosures do not masquerade as continuous-dk results.
A later driver may additionally retain literal finite-grid estimates, distinctly
labeled and without using rounded crossings to tighten the certificate.

## Scores and finite-panel decision

For uncertain ordered endpoints `l<=u` and truth y, evaluate

    IS = (u-l) + 20*max(l-y,0) + 20*max(y-u,0)

outward. Width is intersected with nonnegative values; impossible ordering is
rejected. Positive-part evaluation handles on-boundary and ambiguous miss
branches without selecting a favorable branch. Squared loss encloses
`(mean-y)^2`. Truth is an independently supplied reference enclosure, not a new
training observation. The same truth/evidence identity must be used in both
paired forecasts.

The panel requires exactly M01/M02/M03/M04, N1024 and base sigma. Scores from
different sources, probes, roles or truths cannot be paired. Any failed/unrun
world makes the panel incomplete, retains all four planned denominators and
returns no survivor-only average. With all four present, average each paired
difference outward. Both upper bounds below0 passes the local screen; either
lower bound nonnegative (including exact tie) means the screen is not met;
otherwise it is inconclusive. Stress cases cannot enter this panel.

This is a descriptive four-world learning-utility screen. It supplies neither
coverage calibration, population superiority, an absolute product tolerance,
the full RA-N03 fixture freeze nor permission to run a selector comparison.

## Finite operation and storage shape

Per CDF call with N<=1024:
- two N-element sorts and one <=2N+2 breakpoint sort;
- exactly2N **exact Decimal additions** for mass feasibility, separate from
  directed arithmetic. Since every validated mass lies in [0,1], has exponent
  at least -256 and N<=1024, each sum has at most four integer and256 fractional
  digits. An explicit260-digit Context represents every addition exactly;
  its Inexact trap fails closed if this proof premise is ever violated. Require
  exact sum(lower)<=1<=sum(upper) before any forced terminal CDF=1 rule;
- exactly2N directed mass-update additions and at most2N+2 retained knots;
- at most6N+2 directed interval-add/subtract operations; no physics, log, exp,
  quadrature or root-finding evaluations.

Predictive entry uses two such CDF calls. Its finite point-image CDF actually
has at most N knots, while the continuous CDF has at most2N+2, so their combined
retained shape is at most3N+2 knots. Mass sweeps perform exactly4N updates.
The weighted moment, square and cell-image work is linear; a conservative
source bound is20N+100 arithmetic interval primitive calls including one
certificate recheck. This counts `plus`, `minus`, `times`, `divide`, `square`,
`around` and additions inside `total`; it does not count `point` construction,
Interval construction/validation, comparisons, hashing or sorting. The two CDF
calls additionally make exactly4N exact mass-feasibility additions. These
categories must remain separate in the later complete work census.
Score/panel joins deliberately recheck certificate and expression
consistency; their fixed extra passes must be charged in the later driver
census. A `cdf_at` call performs one bounded linear scan; the quantile path uses
only the two fixed tails, never N calls to `cdf_at`.

These are algorithmic/source bounds, not measured runtime or a final admission
census. The existing eight fixtures/40 posterior beliefs/native forward census
does not change. At most16 prior forecast contexts are needed (one per
fixture/grid) before identity-safe reuse; reuse/serialization counts must be
frozen by the driver. Returning CDF objects does not mandate writing every knot
in every artifact. The bounded report design must explicitly budget any retained
knots/copies against the proposed output limit before numerical admission.

## Authored engineering checks and remaining work

Tests cover every declared prefix; whole-prefix and duplicate remainders; prior
mass identity; malformed coverage/profile/evidence; rational uniform and atomic
surrogates; exact cumulative-mass ties; ambiguous tails and delta>=tail;
exact probability feasibility (including tiny positive/negative residuals,
minimum allowed exponent and a feasible interval under hostile ambient contexts)
and monotone widening; finite-versus-continuous outputs;
ordered interval-score branches; signed bounds, nonfinite values and hostile
ambient Decimal precision; strict co-primary/tie rules; actual four-row
aggregation and incomplete denominators. No D1 truth/forecasts or reference
methods are invoked by these tests.

Independent source review found a rounded-mass feasibility defect: a tiny exact
excess could be hidden by outward rounding before the support-endpoint rule.
The repaired exact sums and eight regressions were independently accepted.
At source `312774cf06a389c2f88cbd664fbfd08d9cc28d36`, formatting, lint,
strict typing across 197 files and all 69 synthetic cases (207 phases) passed.
The first typing attempt failed on two inferred tuple shapes; explicit local
annotations repaired them without changing calculations or assertions.

All owned check processes closed; source and environment stayed unchanged.
The test receipt records zero forbidden calls. These tests perform synthetic
interval arithmetic, with no actual D1 labels, reference solves or batch.
The separate unit2 engineering ledger charged 90.330926 CPU seconds and
105.836336 active wall seconds including retained closeout reservations and
the earlier failed typing attempt. These are not whole-operation costs:
authoring/external control remains unmeasured. Unit1 costs are separate and
retained.

Hosted verification is accepted at source
6af5a5adf86870ca7485e94f6645d784f3cc0fd7:
[PR #139 CI, attempt 1](https://github.com/spei04/strange-physics/actions/runs/41155942409)
passed all six required jobs. Both Python versions passed 5,035 tests, 197-file
typing, 1,567 schema checks, package inspection and 8/8 CLI smoke. Separate
analytic jobs passed 24 cases/72 phases each. The tested merge tree equals the
source tree. This qualifies the source; it does not establish D1 physical
premises or erase earlier local failures.

Actual reference premises for every D1 prefix, the complete finite operation/byte
census, report contracts, disabled runner and numerical allocation are subsequent
work. Passing these synthetic tests does not establish a calibration result.
