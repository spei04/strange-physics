# GRID-Q1 conditional bound interface

This source-only helper implements proof bookkeeping for the
[fixed GRID-Q1 proposal](https://github.com/spei04/strange-physics/blob/08ce72b/docs/FINITE_GRID_CALIBRATION_HANDOFF.md).
It does not run the experiment, justify a discrepancy scale, admit a runtime,
or certify the full candidate. Tests are synthetic arithmetic and malformed-
premise cases; no product or reference module is imported by this helper or
its test module. Numerical reference, refinement and scientific acceptance
remain separate.

## Interface and producer obligations

Import from `grid_q1_bounds` with the repository's resolved `tests/` directory on the test/qualification entrypoint import path:

- Frozen `Interval(lower: Decimal, upper: Decimal)`.
- Frozen `EndpointEvidence(max_abs_error_upper, reference_error_upper,
  requested, completed, failed)`. The first two fields are Decimal; the last
  three are immutable integer index tuples for one history/grid/scale. Both
  requested and completed must equal `tuple(range(count))`; failed is empty.
- Frozen `ArithmeticEvidence(node_observed_error_upper,
  node_other_arithmetic_upper, shifted_log_evidence_error_upper,
  normalized_log_error_upper, probability_representation_log_error_upper)`.
  Every field is a complete nonnegative outward Decimal upper envelope.
- Frozen `GridPremises(history, count, scale, recorded_x, training, future,
  arithmetic, evidence_sha256)`. History is flat/boundary/interior, count is
  64/256/1024 and scale is the exact Decimal 0.125/0.25/0.5. The recorded value
  is an exact point interval representing the actual binary64 observation:
  zero for flat, one for boundary, and in [0.5,1] for interior. It is not an
  interval-valued observation. The driver separately retains the interior
  construction enclosure and its one-rounding proof.
- `endpoint_log_allowance(residual_upper: Decimal, scale: Decimal) -> Decimal`.
- `certify_grid(premises: GridPremises) -> GridCertificate`.

A certificate contains `endpoint_log_error_upper`, the ordered A/B/C tuple
`reserve_components`, `actual_reserve_upper`, `fixed_reserve_upper`,
`delta_upper`, `tv_upper`, `mean_upper`, `second_moment_upper`,
`variance_upper`, `finest_gate_applies`, `passed` and ordered `reasons`.
Malformed, unsupported or incomplete premises raise ValueError: retain an
unresolved profile. Well-formed evidence exceeding a ceiling returns failed
status and its conditional values. Never use those values as a certificate
when `passed` is false. A true value covers only this helper's gates.

The evidence digest is an identity field, not a cryptographic authentication
claim. The driver must bind the exact observed bundle, candidate/model/input/
configuration/report bytes, all per-node physical queries, reference source
and error derivations. A count or a maximum alone cannot establish that work.
The fixed domain is support [0,4], mass one, stationary undamped linear spring,
zero rest length, initial q=0/1, zero velocity/impulse, training t=1/2 and future
q=1,t=1. Every oracle query must satisfy its original domain. Exact coefficient
order, unchanged prior/likelihood family and all nine ensembles/27 profiles
remain driver checks; this helper does not infer them from a digest.

All Decimal inputs are finite, at most 120 digits, exponent between -256 and
128, absolute value at most 1e128. Error envelopes are in [0,1]. Reference
endpoint allowance is exactly 1e-60; observed endpoint errors are measured to
the independent reference center and must be at most 1e-12. Bound arithmetic
uses a fresh explicit 100-digit ROUND_CEILING context. All operands are
nonnegative, and denominators are exact positive dyadic values. Thus upward
rounding composes without a denominator-direction mistake or reliance on the
caller's context. This module needs no exp/log/trig evaluation.

## Why the reserved 3e-9 is sufficient

Let epsilon = 1e-12 + 1e-60, R = 1/2 + 1e-12 and tau = 1e-9. The endpoint-
induced likelihood error is bounded outward by

    E = R*epsilon/sigma^2 + epsilon^2/(2*sigma^2).

The actual recorded point lies in the declared range and the ideal training
endpoint is in [1/2,1] for excited histories (zero for flat); hence this R is
conservative. The reference center and its explicit allowance are separate.

The driver supplies complete observed error envelopes, with independent
reference uncertainty already included, and a separately justified remaining
node arithmetic/reference allowance. This helper requires:

    A = max(node_observed_error, E + node_other_arithmetic) <= tau
    B = shifted_log_evidence_error <= tau
    C = normalized_log_error + probability_representation_log_error <= tau.

It retains each component and their outward sum, and requires that sum at most
3*tau. A/B/C intentionally overlap. They are conservative sufficient proof
bookkeeping, not independent errors, disjoint costs or a new scientific
calibration margin. Passing the original observed checks alone is insufficient
if the propagated bound or the emitted-weight envelope fails.

A bounds each complete joint log weight, so it also bounds the maximum-log
perturbation. B bounds the separately compared shifted log-evidence; together
A+B bound the full finite log-evidence error. Do not subtract rounded maxima
and discard the small shifted correction.

The representation term in C is an inclusive absolute log-ratio envelope
between the actual normalized emitted weights and the independent finite
probabilities. The weights mean exact w_i/sum(w_j), with w_i the actual
declared positive binary64 exp outputs. A merely approximately normalized
rounded vector is not a probability measure for this proof. The driver
encloses those exact ratios and all reference errors with outward intervals.
For each ratio z, an interval proving |z-1| <= r < 1 gives
|log(z)| <= r/(1-r), rounded outward. This needs no new transcendental
reference call and makes no unproved claim about correctly rounded native
exp. Adding the normalized-log envelope again overcounts safely.

Let D = (1/8)*R*(2/N)/sigma^2. Within a cell, the ideal log likelihood differs
from its midpoint by at most D. The frozen bound delta = D + 3e-9 dominates
both D+A+B for log evidence and D+C for comparison with the emitted mixture.
The continuous unnormalized cell integrals and finite representative masses
are enclosed by the corresponding multiplicative factors. Normalizing gives
TV of continuous cell probabilities versus finite cell probabilities at most
tanh(delta) <= delta. This statement is not TV between a continuous density
and an atomic measure. The helper returns delta as the conservative TV bound;
it does not evaluate tanh.

## Predictive bounds and limits

For g(k)=cos(sqrt(k)), |g|<=1, |g'|<=1/2 and |(g^2)'|<=1.
The frozen bounds are computed outward:

    mean = 2*delta + 1/N + epsilon
    second = 2*delta + 2/N + 3*epsilon
    variance = second + 2*mean + mean^2.

The square bound uses epsilon<1, so 2*epsilon+epsilon^2<=3*epsilon.
The variance formula uses the true continuous mean's absolute bound one;
it does not assume an approximate mean is exactly inside [-1,1].

These bounds compare continuous moments with the exact finite mixtures of
declared predicted endpoints and normalized emitted weights. The driver
retains outward intervals for the finite mean, second moment and variance.
Extend those intervals by these analytic bounds to enclose continuous moments.
A rounded displayed point additionally needs its interval rounding width;
do not quietly apply the exact-mixture bound to that point.

Only N=1024 applies the original gates: delta<=0.0081, mean<=0.018,
second<=0.019 and variance<=0.056. Coarser bounds remain visible without
pretending to pass a finest-grid test. Independent flat exact moments, all
refinement comparisons and all discrepancy sensitivity outcomes remain
required. Passing this helper establishes neither calibrated probabilities,
scientific model adequacy, the I1 RMSE threshold nor full GRID-Q1 acceptance.
