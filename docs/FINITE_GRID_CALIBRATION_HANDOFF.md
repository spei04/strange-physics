# Finite-grid calibration handoff — proposed GRID-Q1

**Historical pre-run proposal:** preserved below with its original assumptions and forecasts. The completed diagnostic and its limits are recorded in [GRID-Q1 results](GRID_Q1_SUPERVISED_RUN_RESULT.md). Current work follows the reviewed [RA-N03-D1 protocol](research/RA_N03_CALIBRATION_SLICE.md) and [assignment board](EXECUTION_LOG.md#current-assignment-board).

The sequencing is deliberate: the initial one-parameter experiment makes an explicitly checked grid practical. Laplace approximates the posterior around a fitted mode; accurate Gaussian integrals alone do not establish that the approximation captures a boundary, a flat likelihood or multiple explanations. Grid qualification establishes the reference and shared inference keeps the selector comparison focused on experiment choice. Laplace's mathematical validation proceeds in parallel; comparative adoption follows a measured accuracy check against the qualified reference.


Status: source-only proposal, 2026-10-30. Parent: [approved native comparison](research/NATIVE_COMPARISON_PROPOSAL.md), RA-N02.a followed by RA-N03. This document freezes a reviewable proposal, not an admitted run or an accepted scientific profile. Observed errors, elapsed time, coverage and outcomes are all **null / not run**.

## Decision and scope

Can the existing endpoint implementation resolve one declared finite profile, with a separate bound against its continuous target, at its current 1,025-node limit? The smallest proposed experiment uses three fixed one-record development histories, three nested cell partitions and three fixed discrepancy scales. It can reject this candidate without an expanded search.

This is a resolution qualification step within RA-N02.a. It does not complete RA-N03, establish calibrated probabilities, choose the six comparison worlds, tune an action menu, implement MAP or Laplace inference, or run selectors. The 16-cell / 0.25 demo remains illustrative. Using 0.25 below as the center of a declared sensitivity set does not convert that demo or these proposed settings into scientific calibration.

An inadequate or incomplete candidate stays inadequate or incomplete. No automatic scale increase, extra grid, narrower prior, easier action, replacement fixture, precision escalation or rerun follows a failed gate.

## Authoritative source and dependencies

Planning was inspected at primary e9b5851157235823637a8f459c0066e993373faa. Its tree does not contain the delivered endpoint source; it is not a valid execution base for this proposal. Executable source was inspected read-only at identity 704225566e7bc029dfe54ba7cc4b1823d3a9d7be, parent 479896f95b9a6dbb761d494547fbce3ab9111411. Integration must reconcile these branches and pin the actual execution tree and installed package before admission.

| Component inspected at identity 7042255 | SHA-256 / role |
| --- | --- |
| src/strange_physics/native_endpoint_belief_contracts.py | 33d627e0d3d3c4faeb9fc38634dacc251310e5c4d9005f32b2d431924d5e964b |
| src/strange_physics/native_endpoint_beliefs.py | 9892e0543a4cb150df94fb4aa1bd2b7e9305e59c2f23d238726499776d8724d2 |
| docs/NATIVE_ENDPOINT_BELIEFS.md and tests/endpoint_belief_reference.py | Existing restricted family, independent ODE recurrence and explicit error domain; source identities must enter the eventual manifest |
| docs/BOUNDED_SCIENTIFIC_DEMO.md | Separate four-observation workflow; no accepted scientific grid or discrepancy |
| docs/LAPLACE_ANALYTIC_REFERENCE.md | Accepted test-only analytic fixtures; no Laplace algorithm or grid-calibration acceptance |

RA-N01 and RA-02 are the accepted prerequisites for RA-N02.a implementation. RA-N03 and RA-N04 depend on RA-N02.a; RA-07.b depends on RA-N03, RA-N04 and SP-04.e. Later RA-N02.b consumes accepted frozen RA-N03 fixtures. This handoff changes none of those edges. Laplace reference preparation is not a new prerequisite for this grid step.

Full-study allocation is a separate gate. Its unresolved 1,168 MiB reservation floor against the 1 GiB cap does not prevent this source-only handoff or implementation. It also does not authorize a calibration run; that run needs its own reconciled finite allocation within the unchanged cumulative authority.

## Exact proposed inputs

Proposal ID: RA-N02.a-GRID-Q1-v1. All listed settings are proposed and fixed before any outcomes.

Common physical configuration:

- One particle p0, mass 1, anchor (0, 0), zero rest length, stationary linear spring, no cubic term, zero declared position/velocity observation noise.
- Initial velocity (0, 0), applied impulse (0, 0), duration 1/2, integration/replay dt 1/64 and exactly observed frames at times (0, 1/2). All y coordinates are zero. The independent ideal endpoint is x(k) = q cos(sqrt(k)/2).
- Each history has exactly one completed record, ordinal 0, with distinct synthetic run/space/operation identities. Construct the typed public space and complete record; bind the actual candidate input/result/attempt and original full bundle. They are explicitly synthetic development fixtures, not authenticated Journal purchases or observed study episodes.
- Use the existing default NativeCandidateConfig and NativePredictionConfig, pinned by their canonical bytes and hashes. The predictor is the existing analytic oscillator/sinc implementation; dt is replay metadata. No simulator integration or provider call is introduced.

| History ID | Initial x, q | Development truth metadata | Recorded terminal x |
| --- | ---: | --- | --- |
| GRID-Q1-flat | 0 | null: all coefficients produce the same unexcited endpoint | 0, exact |
| GRID-Q1-boundary | 1 | k = 0 | 1, exact |
| GRID-Q1-interior | 1 | k = 3/2 | Independently enclosed cos(sqrt(3/2)/2), rounded once to binary64; retain its enclosure and rounding error |

Truth metadata belongs only to fixture construction and audit. The candidate evaluator receives the actual recorded public values, never the label k. The interior coefficient is deliberately distinct from the earlier endpoint software fixture at 1/3, but that alone does not prove dataset disjointness. Before admitting any scientific reuse, compare complete fixture/world/probe identities against the frozen study manifest. The six study worlds must not be inspected to tune this proposal.

Common coefficient support is [0, 4], with uniform density 1/4 with respect to physical dk. For each N in {64, 256, 1024}, cell i is [4i/N, 4(i+1)/N] and its representative is k_i = (4i+2)/N, for i = 0,...,N-1. Cell mass is 1/N. These endpoints and representatives are exact dyadic binary64 values. All fine cells have declared parent cells; aggregate them before comparing distributions.

The base discrepancy is sigma = 1/4 position units, with the fixed half/base/double set {1/8, 1/4, 1/2}. Evaluate all three scales; do not select the most favorable outcome. For each completed record use exactly:

    log L(k) = -log(sigma) - log(2*pi)/2
               - (recorded_x - predicted_x(k))^2 / (2*sigma^2)

Use terminal-x.v1, independent-gaussian-discrepancy.v1, physical-k-lebesgue.v1 and uniform-support-density.v1. Constants, cell masses and full observation identity are retained. This is the existing working model-belief family, not an empirical assertion that deterministic numerical residuals are independent Gaussian observations.

Future predictive diagnostic: for every candidate/history/grid request an untouched probe with mass 1, anchor (0, 0), initial position (1, 0), zero velocity/impulse, times (0, 1), dt 1/64. Its ideal endpoint is g(k) = cos(sqrt(k)). Compute finite posterior-weighted first and second endpoint moments and variance. These are diagnostic mixtures, not the comparison's primary MAP prediction.

## Independent reference and fixed acceptance gates

Keep four errors separate: endpoint propagation, likelihood/normalization arithmetic, finite-cell resolution and scientific model adequacy.

1. **Input and coverage.** Require all 27 declared history/grid/scale combinations, their exact ordered coefficient/cell/prefix/configuration hashes and all nine candidate ensembles. Record attempted/completed/failed/unrun status for every combination. No failure, zero mass or nonfinite candidate may be discarded to normalize survivors. Any incomplete combination prevents candidate acceptance.

2. **Independent endpoint reference.** Reuse the reviewed 80-coefficient, 100-digit Decimal ODE recurrence with exact binary inputs, and its 1e-60 absolute reference allowance. Every proposed training and future query satisfies k*t*t/m <= 4, |x0-a| <= 1, |v_after*t| <= 1, 0.5 <= m <= 2 and 0 < t <= 2. Require every evaluated binary64 endpoint to differ from its independent reference by at most 1e-12. This gate must be observed at every proposed node; old point tests are not a universal kernel certificate.

3. **Finite arithmetic.** Independently evaluate cell prior masses, likelihood constants, direct positive finite sums and normalized log weights. Require node log-likelihood-plus-prior error, shifted log-evidence error and normalized-log error each at most 1e-9. Before applying that ceiling, retain the actual propagated allowance |R|*epsilon/sigma^2 + epsilon^2/(2*sigma^2), with epsilon = 1e-12 + 1e-60, plus explicit reference/arithmetic allowances. Reject if the derived allowance itself exceeds 1e-9. Preserve maximum-log and log-scaled-sum separately; do not combine away small corrections.

4. **Continuous-mass certificate.** Do not accept pairwise grid agreement as the sole resolution check. For the ideal training endpoint, |dx/dk| <= 1/8 on [0,4]. The three declared histories have |recorded_x - x(k)| <= 1/2 + 1e-12; verify the label enclosure used for this bound. A midpoint cell has radius 2/N. A conservative total log-mass variation bound is

       delta(N,sigma) =
         (1/8)*(1/2 + 1e-12)*(2/N)/sigma^2 + 3e-9.

   The final term reserves the separately passing endpoint/finite-arithmetic/reference errors; the implementation must substantiate that decomposition, not merely print the formula. Bound construction must use exact constants and outward rounding. If any premise fails, the certificate is unresolved and the profile fails this gate.

   The continuous unnormalized cell integral and its finite representative mass differ by a factor between exp(-delta) and exp(delta). Therefore absolute log-evidence error is at most delta. After normalization, total variation between **continuous cell probabilities** and finite cell masses is at most tanh(delta) <= delta. This is not TV between a continuous density and a discrete atomic measure.

   Require delta <= 0.0081 for every 1024-cell history/scale combination. The formula predicts a worst bound slightly above 0.0078125 at sigma=1/8; this is a prospective analytic bound, not an observed result. Retain coarser bounds even when they exceed the fine-grid gate.

5. **Predictive accuracy bound.** On [0,4], |g| <= 1, |g'| <= 1/2 and |(g^2)'| <= 1. Combine the accepted cell-mass bound with the within-cell future approximation and its separately checked endpoint error. At N=1024 require an absolute continuous-mean error bound <= 0.018 position units, second-moment error bound <= 0.019 squared position units, and variance error bound <= 0.056 squared position units. The respective conservative bounds are 2*delta + 1/N + epsilon, 2*delta + 2/N + 3*epsilon, and the second-moment bound plus twice the mean bound and its square. Report these bounds as such, not as measured exact errors or the I1 0.001 RMSE guarantee.

6. **Independent exact predictive check.** For the flat history, the posterior equals the uniform dk prior. The independent continuous future mean is sin(2)+(cos(2)-1)/2; its second moment is 1/2+sin(4)/4+(cos(4)-1)/16. Use the already reviewed bounded trigonometric reference, not a native predictor or a very fine grid as ground truth. Retain actual first/second-moment differences and require them to lie within their declared analytic bounds.

7. **Refinement diagnostics with a pass/fail rule.** For each history/scale compare 256 cells against 1024 cells after exact parent-cell aggregation. Require TV <= 1e-3, absolute future-mean difference <= 5e-4 position units and variance difference <= 1e-3 squared position units. These are proposed operational stability margins, not derived coverage guarantees. They supplement the continuous certificate and may reject the candidate. Report the full 64->256 comparison without deleting a coarse failure or changing either finer gate.

8. **Sensitivity and failure evidence.** Retain all scale-specific results, mass/boundary concentration and predictive differences. No scale-invariance assertion is made: changing sigma changes the target. Existing failed-record, unsupported-noise, prior-mass, identity/order and exhaustion regressions remain required at the integrated source. This experiment adds no correlation or misspecification validity claim; those need separate, bounded RA-N03 fixtures.

The proposed tolerances qualify a deliberately modest resolution diagnostic. They are not scientific defaults, universal error bounds, calibrated credible intervals or the primary benchmark's predictive threshold.

## Smallest finite census and forecast

There are exactly three histories, three grids and three scales: 27 endpoint-belief calls. Nine candidate ensembles contain 3*(64+256+1024) = 4,032 model instances, bound separately to their actual histories. On a fully successful attempt:

| Work | Planned count / ceiling |
| --- | ---: |
| Candidate production entries | 9 |
| Endpoint predictions and scalar likelihood evaluations | 3*3*(64+256+1024) = 12,096 |
| Normalizations | 27 |
| Future native predictions, reused across sigma only for identical bound inputs | 3*(64+256+1024) = 4,032 |
| Native prediction entries total | 16,128 |
| Requested frames | 32,256 |
| Weighted-moment exponential evaluations | at most 12,096, separate from normalizer exponentials |
| Independent ODE reference evaluations | at most 16,129, including the one nontrivial construction label; cache hits and actual calls recorded separately |
| New purchased experiments, selectors, providers, network calls | 0 |

The independent likelihood/reference sums use the same complete declared rows. Freeze the exact Decimal exp/ln counts, reference-loop ceilings, parser/binder reconstruction passes, serialization/output bounds and phase census from source before runtime admission. No hidden extra reference grid, derivative search or optimizer is permitted. Reuse requires exact source/input/configuration identities; count work once physically and attribute it explicitly when reused.

Source preparation and independent protocol review are forecast at 0.5–1 engineer-day each, low confidence. After source/census acceptance, the core calculation is provisionally estimated at 2–5 CPU-minutes, low confidence; serialization and independent reference costs may dominate. The earlier 3,734-prediction endpoint test completed in about 14 seconds, but it is only a scale reference, not a linear timing guarantee for this manifest. Do not start from that estimate.

A prospective validation envelope of at most 600 CPU-seconds, 1,800 active-wall-seconds and 64 MiB newly owned output is proposed for review, **not allocated or authorized**. It must fit within the reconciled existing study balance and current host conditions before any numerical work. Preparation, failed attempts, reference work, logs, finalization and cleanup consume the same unit; there is no automatic retry. No new environment, package, checkout or generic supervisor is required.

## Authority, storage and retained accounting

The owner approval is NATIVE_COMPARISON_APPROVAL_2026_10_21; its retained decision SHA-256 is 7fbb41abdc81e291284de8e82d8be3ae0f62cf7d8fb926c8ac6aa1c79b56f66d. The unchanged scientific ceiling is 8 CPU-core-hours / 1 GiB new artifacts across reference, calibration, sensitivity, ranking, predictions, scoring, failures and later diagnostics. No remaining scientific balance is asserted here.

Before scientific reuse, Lead must reconcile retained costs rather than treating old software tests as free calibration:

| Retained unit | Existing ceiling / hold | Accounting receipt SHA-256 |
| --- | --- | --- |
| Endpoint implementation/validation/delivery | 1,200 CPU seconds / 3,600 active-wall seconds / 64 MiB; failed attempts and protected holds retained | 297a1e646db280840ba3515dfa0b766010128491f6ef2e2ca26c2422e9a1ec62 |
| Four-observation demo/delivery | 120 CPU seconds / 360 active-wall seconds / 64 MiB; separate original failure retained | 577860da96e926cddf1364ac817d646c39684888f410148a095771d5467b71d3 |
| Laplace reference software unit | Full 180 CPU seconds / 420 active-wall seconds hold, 8 MiB output ceiling retained; initial preflight failure plus one numerical process | 811a1c606c43375a3bdaf637f2da0298d09a4b1c8863ae0644a94ecac9be4c17 |

These are distinct ceilings/holds, not measured totals to subtract indiscriminately. The Laplace receipt explicitly says scientific use is not admitted. Its existing reference output is not needed for GRID-Q1. Reconcile earlier native work and any reused developer/CI evidence too; do not derive a fresh 8-hour allowance from this table or double-count shared physical work.

### Reconciliation gaps found during the resume review

The read-only cost audit found additional relevant records. Paths below are
relative to the private evidence root; they identify records, not extra allowance.

| Record | What is retained | What still needs settlement |
| --- | --- | --- |
| ra-n02-normalizer/lead-focused-validation-346f3fe/outcome-index.json (59516084cd0b8e2989bfbca7aa730fa0f40efea2b63e5f359f0686bebecbd245) and failed predecessor lead-focused-validation-6f79454/retained-index.json (3d7cdbfdd9d990c6be0d539de4f79aeb0228cc9b62fb3361ec2e1a8460ba6652) | Successful and failed command receipts; reference child CPU/wall observations | Whole-unit preparation/controller/transport accounting and actual retained bytes; a unit ceiling is not measured usage |
| ra-n01/research-runtime-c3988d9/index.json (a2fc4d86134c2e42cf221ef52d98bf24c26bca9745e4143fd24f518e56a2baf6) | Original and corrected native-reference executions and source identity | Probe CPU/wall were not recorded in those receipts; neither execution can be assumed free |
| Normalizer PR/main hosted suites and ra-n02-normalizer/lead-main-620c0f0-verification/outcome-index.json (99334173b99391f259efd62d5828237cb85761669f11de22df4f01b26db3d1b5) | Separate hosted executions and package-verification records | An explicit scientific-reuse attribution rule; full-suite elapsed time is not component CPU and must not be charged repeatedly to every component |

The smallest next accounting action is an evidence-use manifest for GRID-Q1:
name each exact receipt used for scientific acceptance, distinguish implementation
context from reused measurements, and bind each physical execution once. Then
settle missing usage under an explicit conservative attribution policy or retain
unknown holds. Do not infer a remaining balance from these partial records.

Storage needs one ownership census joining retained artifacts and deletion
records. Deduplicate repeated references to the same physical file, not distinct
copies that happen to share a hash; cleanup does not automatically refund a
permanent hold. Per-test synthetic ledgers under RA-02 do not establish a global
campaign balance. This reconciliation does not require increasing the study cap
or resolving full-study publication allocation before implementation.

The current general source-development readiness gate is 20 GiB, separate from the 100 MiB emergency stop floor. Read-only inspection on 2026-10-30 observed 46,249,340,928 available bytes, above that source gate. Lead and Quality accepted source-only preparation under the separate <=1 MiB source/Git/preparation bound.

The 50 GiB start / 45 GiB later floors belong to prior bounded runtime slices and were concretely carried into the endpoint validation plan: free_start=53,687,091,200 and free_later=48,318,382,080 bytes, plan SHA-256 18c249d396dca7043940a40a33b7084c6693f82f74f347fb4c8028c77b603bcc. The comparison handoff also retains those proposed runtime guards. Current available space is below both. These are not a blanket ban on small source edits; they are also not waived for a new numerical run. Numerical execution remains paused under the retained 50/45 GiB guards; this source proposal does not lower them. Any runtime admission must explicitly select and satisfy its governing storage guards. Do not delete active consumers or purchase capacity to evade a gate.

The full-study publication reservation floor remains 1,168 MiB > 1 GiB. Resolving it is necessary before the full comparison, independently of whether this small source proposal or a separately allocated calibration unit proceeds.

## Handoff and unresolved decisions

Research supplies the fixed input manifest and source-only reference/bound implementation after this protocol review. Quality independently reviews formulas, criteria, failure coverage and fixture separation. Platform reviews count/byte/runtime allocation and provenance. Lead owns exact-source integration and admission.

The highest-risk decision is discrepancy meaning. The proposed dyadic scales make a finite resolution test concrete; accepted solver point-error evidence does **not** justify sigma=1/4 as a scientific numerical-discrepancy model. RA-N03 must separately justify the residual scale and covariance assumptions, or reject the profile. Do not choose a large discrepancy merely to make a coarse grid pass.

A strict solver-error-sized discrepancy may be incompatible with the existing full-support finite pool; the known 1024-node/sigma-1e-6 counterexample already demonstrates that this can occur. If the independently justified scale fails this fixed candidate, record the failed gate and seek a scoped protocol decision. Do not silently expand the pool, shrink the support, change the observation action or reinterpret an unvalidated grid as ground truth.

A second decision is whether the proposed resolution/predictive margins are useful enough for the later selector comparison. They bound this diagnostic, not the I1 threshold. Review them before outcomes. Remaining unknowns are exact integrated source/runtime identity, final source-derived resource census, admissible scientific balance, scientific scale/correlation justification, untouched fixture separation and actual errors/timing. None is filled with a fabricated measurement.

## Source audit follow-up

The first implementation checkpoint corrects the fixture shape: explicit duration/sample interval 1/2 and dt 1/64, complete public-shaped records, external history labels and canonical space digests. Identical physical spaces share a digest; there is no space_id field. Terminal velocities are explicitly unused zero placeholders, so these synthetic records are terminal-x diagnostics rather than full observed trajectories.

The accepted old EndpointOracle remains unchanged. Its single-instance 16,000-lookup / 1,728-series guards cannot cover the proposed 16,129 / 2,689 aggregate. The foundation proposes six fixed, non-resetting named instances with explicit aggregate exp/log/trig counts. The foundation alone did not establish numerical acceptance. The disabled driver, outward error bounds and persisted attempts/results are now implemented with independently accepted engineering checks; the [dated execution entry](EXECUTION_LOG.md#2026-10-30--grid-qualification-implementation-and-engineering-checks) records source reviews and current gates. Cumulative cost reconciliation and numerical admission remain pending. No new publisher is required for this synthetic diagnostic.
