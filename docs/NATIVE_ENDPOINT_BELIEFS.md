# Restricted endpoint-x finite beliefs

This additive pure API evaluates a declared finite spring pool under one explicit model-belief family. It does not choose a scientifically accepted grid, discrepancy, observation covariance, MAP estimate, action or study allocation. RA-N02.a remains in progress.

## Inputs, identities and entry points

`compute_native_endpoint_belief(raw: bytes)` returns a `NativeEndpointBeliefResult`. The public binder is `bind_native_endpoint_belief_result(result_raw: bytes, input_raw: bytes)`; the two bounded parsers are in `native_endpoint_belief_contracts`. Typed messages are construction and serialization helpers. Direct typed arguments fail at raw ingress, including objects made with Pydantic construction/copy bypasses. Serialize them and pass the resulting bytes through the bounded parser.

The input retains an actual `NativeCandidateInput`, its complete `NativeCandidateResult`, original candidate attempt, prediction configuration, and all completed and failed records. Existing actual-input candidate and prediction binders remain in use. The result distinguishes the input's exact raw SHA-256 from canonical input, profile, candidate-result and whole-observation identities. Ordered prediction-result hashes include any returned failure. These checks establish supplied-material consistency, not authenticated Journal ancestry or proof that a serialized result was computed. The binder performs no scientific forward.

The limits are 1–1,025 ordered physical coefficients, at most 12 records, at most 12,300 requested predictions and two requested frames per prediction. Raw input is capped at 16 MiB, depth 40 and 2,000,000 JSON nodes; result input is capped at 4 MiB, depth 24 and 300,000 nodes. Canonical byte checks are separate. A required prediction allowance is checked against the complete candidate × completed-record work before any forward.

## Restricted family

Cells form one contiguous positive-width partition inside physical stiffness `[0,4]`. Each declared coefficient lies in its corresponding closed cell; it need not be a midpoint. The reference measure is physical `dk`, with uniform density over that declared support. Thus cell prior mass is `(right-left)/(support_right-support_left)`, not uniform mass per node. A positive width whose mass underflows is arithmetic failure, never an exact-zero prior declaration.

For every completed record, the feature is its actual terminal x position at the exactly declared duration. Failed records are retained in the input identity and counts, and contribute no observed residual. The required discrepancy `sigma > 0` is independent of the observation-noise fields. This first family rejects nonzero declared position or velocity observation noise. It assumes independent endpoint residuals across completed records; that working assumption, repeated-action independence, and a useful value of sigma are not validated study claims.

For record r and node k the log likelihood is

`-log(sigma) - log(2*pi)/2 - (observed_x_r - predicted_x_r(k))^2/(2*sigma^2)`.

All constants and all completed records are retained. Each node receives the sum of record log likelihoods plus its log cell prior mass. The delivered finite-log-weight normalizer returns rounded normalized logs and a shifted normalizer; finite entries whose exponentials underflow stay finite log entries with explicit diagnostics. No node is dropped or relabeled exact zero.

Preflight rejection, arithmetic failure, native prediction failure and unrelated interruptions are distinct. A prediction or likelihood failure stops the ordered pass and exposes no partial node set. A normalization failure may retain the complete evaluated node set and failed algebraic input/result, but cannot claim successful weights. Deterministic eligibility, status, failure location and work-count joins are checked without recomputing forwards. A failed two-frame prediction has only the reachable extra frame counts `(0,0)`, `(0,1)` or `(1,1)`. Unexpected interruptions propagate.

## Independent software references

The focused source defines synthetic software fixtures, not measured worlds. The independent reference in `tests/endpoint_belief_reference.py` uses the ODE recurrence `c[n+2] = -(k/m)c[n]/((n+2)(n+1))`, 80 coefficients and 100-digit Decimal arithmetic. It imports no production oscillator/integrator. All recorded labels, cell endpoints, sigma and physical inputs enter via `Decimal.from_float`; ideal synthetic labels and their conversion error remain separate.

The finite reference domain is `k*t*t/m <= 4`, `|x0-a| <= 1`, `|v_after*t| <= 1`, `0.5 <= m <= 2`, `0 < t <= 2`, `|v_after| <= 2` and `|a| <= 1`. The omitted even/odd tails start at most at `4^40/80!` and `4^40/81!`; each following ratio is below `4/(81*82)`. Using `80! >= 40^40 * 20^20 * 10^10`, the first even term is below `1e-75`; the two geometric tails together are below `1e-74`.

For the stated Decimal domain, coefficient intermediates and Horner values are below `1e4`; using `1e-94` as an absolute rounding allowance per primitive is deliberately conservative at precision 100. Recurrence multipliers are at most 4 and 4/3 for the first even/odd update and at most 2/3 thereafter. Fewer than 400 primitive operations, including the rounded k/m and post-impulse speed, give a coefficient-error allowance below `1e-90`. A conservative Horner amplification bound `80 * 2^80 * 1e-90 < 1e-63` includes these coefficient errors and its additional rounding. Combined with the tails, the shared absolute reference allowance `1e-60` is conservative for these cases. It is not a certificate for the production binary64 kernel outside them.

The circle constant uses `16*atan(1/5)-4*atan(1/239)`, 64 alternating terms per arctangent. The absolute truncation bound is
`16/(129*5^129) + 4/(129*239^129) < 1e-89`.
The four sin/cos references at 2 and 4 use 80 terms each; the largest first omitted term is `4^160/160!`, with tail ratio at most `16/(161*162)`. Their finite Decimal rounding and truncation are also below `1e-89`, and hence below the shared `1e-60` allowance. These are bounded test formulas, not a general quadrature package.

Ordinary likelihood references retain Decimal exp/ln at precision 100, direct positive finite sums, and Decimal comparisons without an early float conversion. For each actual residual R, the recorded allowance includes `|R|*epsilon/sigma^2 + epsilon^2/(2*sigma^2)`, where `epsilon=1e-12+1e-60`, plus the explicit reference and floating arithmetic terms. The full per-case allowance must remain below `1e-9`; the 1e-12 component check must itself pass at every evaluated node. The allowances are software checks for the named fixtures, not scientific calibration.

## Resolution and predictive limitations

Ordinary fixtures use 16, 64 and 256 midpoint cells with three test discrepancies. Their conditional cell-variation diagnostic uses the actual representative radius `max(k-left,right-k)`; half-width is used only for midpoint cells. An exceeded diagnostic is unresolved, not proof of actual grid error. Refinement compares fine masses coarsened onto the actual parent cells. Normalization or two-grid agreement alone does not certify a continuous posterior.

An independent unexcited-history case preserves the uniform physical-k prior. An excited future probe at t=2 then has continuous mean `sin(2)+(cos(2)-1)/2` and second moment `1/2+sin(4)/4+(cos(4)-1)/16`. The tests compare weighted predictive moments and their finite-grid errors against those independent expressions. This is distinct from prediction under a selected/MAP model.

The separate 1,024-midpoint, support-[0,4], sigma-1e-6 counterexample is retained deliberately. For `f(k)=cos(sqrt(k))`, `|f'(k)| >= 1/6` on that support. With ideal truth k=1 every midpoint is at least 1/512 away, so every feature differs by at least 1/3072. The test subtracts actual label rounding and an independently checked error at all 1,024 binary64 nodes. A width-`2*sigma` neighborhood around 1 gives a positive continuous kernel-evidence lower bound, while every node has an exponentially small upper bound. This demonstrates a particular underresolved grid without a huge fine-grid surrogate or Laplace assumption; it does not make a replacement study profile accepted.

## Validation and integration status

Handwritten source and reference tests are a review checkpoint. Schema generation, configured static checks, package refresh and the focused numerical run require their exact bounded validation handoff; no outcomes are asserted here. The fixed generator is `scripts/generate_native_endpoint_belief_schema.py`; `scripts/validate_contracts.py` checks structural examples, which do not authenticate computation.

The planned focused collection has 32 cases, 32 candidate-producer entries, 2,388 successful fitted predictions plus two fault entries, 1,344 future predictions and 22 normalizations. That is 3,734 predictor entries, at most 7,468 requested frames and 7,464 successful returned frames. The shared oracle has 1,452 distinct ODE values and 7,834 lookups, 1,361 Decimal exp calls, 1,427 Decimal ln calls, 128 Machin terms and four 80-term trigonometric references. These are source-derived counts pending observed reconciliation; all parser/binder reconstruction, setup and diagnostics remain charged work.

Later study profile selection must assess discrepancy, record dependence, prior/support, finite resolution, predictive behavior and resource fit on accepted evidence. Scientific reference/calibration work reused for that acceptance must be included cumulatively in the existing 8 CPU-hour/1 GiB accounting. No full-study allocation, publisher authority, graph change or MAP claim is added here.
