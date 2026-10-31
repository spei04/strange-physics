# RA-N03-D1 — deterministic calibration-development slice

**Reviewed protocol v0.1, 2026-10-30; fixed before outcomes. No numerical execution is admitted.** This is a small adequacy and falsification diagnostic, not completion of RA-N03 or a coverage-calibration study. Existing [implementation authorization](APPROVALS.md) permits source work; a run still needs its own complete, reviewed finite proposal.

Independent Research, Quality and Platform review accepted this source-work checkpoint. Acceptance covers the protocol and prospective accounting boundaries; implementation, numerical qualification and run allocation remain pending. [Current assignments](../EXECUTION_LOG.md#current-assignment-board) are maintained separately.

## Decision and existing evidence

The decision is whether the current terminal-position belief family has a defensible interpretation and useful behavior on a named development panel before any calibrated-probability or selector claim. A negative or inconclusive result is useful. Passing every numerical check alone cannot answer that scientific decision.

The [supervised GRID-Q1 result](../GRID_Q1_SUPERVISED_RUN_RESULT.md), preserved at f2318bea862016e085eba5f65c75ed66fa0113f9, checked 27 synthetic profiles and their numerical resolution. Its report SHA-256 is 8c15752b1a26de2ddccbdebaef394ce943f62d1bc5aa55e235389c0e956f50be. It did not calibrate the likelihood. Its fixed inputs, gates, failures and costs remain unchanged.

This protocol specifies a small part of [RA-N03](NATIVE_COMPARISON_PROPOSAL.md#ra-n03--calibrate-native-beliefs-and-numerical-discrepancy-sensitivity), following the safeguards in [METHOD_DECISIONS](2026-10-19-METHOD_DECISIONS.md). It adds no prerequisite on RA-07.b, enterprise delivery or Laplace implementation.

## What positive Gaussian discrepancy means here

The inspected implementation, [native_endpoint_beliefs.py](../../src/strange_physics/native_endpoint_beliefs.py), rejects nonzero declared position or velocity observation noise. For every completed record it nevertheless adds

    log L_j(k) = -log(sigma) - log(2*pi)/2
                 - (recorded_terminal_x_j - predicted_terminal_x_j(k))^2 / (2*sigma^2).

The [contract](../../src/strange_physics/native_endpoint_belief_contracts.py) fixes terminal-x.v1, independent-gaussian-discrepancy.v1, uniform-support-density.v1 and physical-k-lebesgue.v1. Every record in a bundle must have the same terminal time, and at most 12 records are supported.

Keep four quantities distinct:

| Quantity | Meaning in D1 |
| --- | --- |
| Numerical error | Bounded error in the predictor, independent reference, floating arithmetic and finite grid. Measured endpoint bounds around 1e-16 in Q1 do not justify a discrepancy scale of 0.25. |
| Measurement noise | Zero by construction. No random measurement is generated, inferred or relabeled. |
| Model discrepancy | A systematic mismatch between a candidate's dynamics and the generating mechanism; the omitted-force control below supplies one explicit example. It need not be independent, zero-mean or Gaussian. |
| Working loss scale | Sigma controls how strongly deterministic residuals reweight the prior. This is a legitimate interpretation to review, but it does not silently replace the existing model's unvalidated Gaussian/probabilistic interpretation. |

For fixed sigma, the normalized weights can be read as a loss-based update with squared-residual weight 1/(2*sigma^2). That observation supplies no calibration guarantee or scientifically justified default. The distinction is consistent with [Bissiri, Holmes and Walker, version 2 (2016)](https://arxiv.org/abs/1306.6430v2). [Talts et al., version 2 (2020)](https://arxiv.org/abs/1804.06788v2) describe simulation-based calibration of Bayesian algorithms; D1 is not SBC and does not supply its generative sampling assumptions.

Repeating an identical noiseless observation adds the same residual term again. The current implementation therefore changes its weights as if extra likelihood information arrived. D1 must expose that behavior; it must not manufacture independent evidence from repeated records.

## Fixed construction and exposure

Protocol ID: RA-N03-D1-v0.1. Reserve construction IDs D1-M01 through D1-M04, D1-D03, D1-F02, D1-F04 and D1-W03. No RNG, seed search, noise sampling, simulator purchase or provider call is included.

The four coefficient blueprints, in ID order, are 1/7, 5/7, 13/7 and 27/7. Convert each rational once to correctly rounded binary64, retain its hexadecimal representation, and use that exact binary value in all subsequent independent reference calculations. These purposive cases span a low coefficient, two interior regimes and the upper-support region; they are not a random sample of worlds.

All public structures contain one particle p0 of mass 1 and one spring anchor a0 at (0,0), zero initial velocity and zero impulse. Both declared observation-noise values are zero. Training duration is 1/2, dt is 1/64, and the public synthetic record has exactly the frames (0,1/2). Candidate support is [0,4]. The future probe uses initial x=1, zero velocity/impulse, times (0,3/4), and the same mass/anchor/dt. It is a separate request, never a fit record.

| Bundle | Worlds | Initial training x | Generating mechanism | Records used | Sigma |
| --- | --- | ---: | --- | ---: | --- |
| M, matched | M01–M04 | 1 | x'' = -k*x | 1 | 1/8, 1/4, 1/2 |
| D, exact repeat | D03, paired with M03 | 1 | Same matched world; second record copies the exact physical action and observed values, with a new ordinal/operation ID | 2 | 1/4 only |
| F, omitted force | F02 and F04, paired with M02/M04 | 1 | x'' = -k*x + k/8 | 1 | 1/8, 1/4, 1/2 |
| W, weak excitation | W03, paired with M03 | 1/8 | Matched world; future probe still starts at x=1 | 1 | 1/4 only |

The F controls are **synthetic residual fixtures**, not supported purchases from the unchanged zero-force simulator. Their exact independent solution is

    x_F(t) = 1/8 + (q - 1/8) * cos(sqrt(k)*t).

The public candidate structure still has its actual spring anchor at zero; the additional constant force is the deliberately omitted mechanism. It is not hidden measurement noise or a false anchor declaration. No production law, SDK contract or simulator is modified by this protocol.

Construct all endpoints independently using the reviewed bounded ODE/reference method, with one-rounding proofs for recorded binary64 x. For F, the equivalent equilibrium transformation belongs only to the independent fixture generator. Do not use the native predictor to generate its own truth. Preserve reference enclosures and label-construction failures. Terminal velocities remain explicitly tagged unused zero placeholders; no claim that these are full physical trajectories is permitted.

Reserve distinct world, run, space, operation, prefix, candidate, query and evaluator IDs. Before freezing bytes, compare complete construction tuples and raw/canonical identities against earlier software fixtures, GRID-Q1, other exposed development records and probe manifests. A changed coefficient or filename alone is not evidence of disjointness. A separate owner must reject overlap with the six comparison worlds without revealing their labels or using them to tune this panel. Reserve these four coefficient values and all eight matched/paired construction blueprints, including their training and probe tuples, for development only. Future untouched study manifests must exclude those reserved values and variants; the linear-spring law family remains the intended study domain.

The blueprint is public and its authors are exposed to it. It is development data, not a human-blind test. Actual truth metadata, construction intermediates and probe answers remain in the private evaluator projection; the candidate path receives only public structure and the declared prefix. Audits cannot write selector state. A successful D1 does not automatically freeze the complete RA-N03 fixture corpus for Laplace.

## Profiles, ordering and reuse

Use uniform physical dk prior density on [0,4], N in {256,1024}, cells [4i/N,4(i+1)/N], and midpoint representatives (4i+2)/N. Keep exact source, model, candidate, prior, likelihood, full-prefix and prediction configuration identities.

Sigma=1/4 is the **frozen base inherited for this diagnostic**, not a noise estimate or selected winner. Execute both one-record sensitivity endpoints, 1/8 and 1/2, for M and F. D and W use the base only. No smaller sigma, extra duplicate count, alternative prior, shifted grid or outcome-driven follow-up is included.

For each world, freeze the action sequence before opening labels:

1. Form the prior predictive at the first training action from the same retained node endpoints and prior masses; record the signed innovation before conditioning.
2. Condition on the one-record prefix and persist weights and predictions before opening the future answer.
3. Only D03 appends the byte-identical observed values at ordinal 1. Record its prequential innovation using M03's one-record belief, then compute the two-record belief.
4. Produce the future prediction from each declared prefix. Release the future reference answer to the evaluator only after the prediction identity is fixed.

The two D records are not two independent observations for the statistical analysis. Their exact-duplicate relationship is declared, not discovered by selecting similar outcomes. A qualified cache may reuse scalar forward values only for identical physical arguments; prefix-dependent model/result identities and all binding/serialization work must still be retained and charged. The ceiling below assumes full native calls for each declared candidate identity.

## Estimands and precision

The named decision is whether conditioning improves the held-out terminal-position forecast at t=3/4 on the four matched development worlds. Compare the posterior with a frozen **no-learning prior predictive** using the same uniform physical-dk prior, candidate cells, future requests and reference answers. The reference never sees a fitted record. Reuse identical retained node predictions; bind its prior masses and forecast identity separately. Do not substitute a tuned point estimate or the matched true coefficient as the baseline.

At N=1024 and the frozen base sigma=1/4, retain each world's signed residual (truth minus mixture mean), squared/absolute error, interval endpoints, width, inclusion status and score. Also report the maximum absolute error; a favorable aggregate must not erase an individual miss. The co-primary targets are the continuous physical-dk prior and working-posterior predictive distributions defined above. N=1024 supplies finite estimates and certified enclosures of those targets; retain literal finite-grid scores separately. The two co-primary finite-panel estimands, with equal weight on the four M worlds, are

    Delta_point = mean_M[(mu_posterior - y)^2 - (mu_prior - y)^2]
    Delta_interval = mean_M[IS_posterior(y) - IS_prior(y)].

For a central 90% interval [l,u], use

    IS(y) = (u-l) + 20*(l-y)*1[y<l] + 20*(y-u)*1[y>u].

This is the interval score with alpha=0.1 in [Gneiting and Raftery (2007), Section 6.2, equation 43](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf). Width and missed-distance penalties prevent interval inclusion alone from rewarding a vacuously broad band. Squared point loss is paired with the diagnostic mixture mean; neither score silently substitutes that mean for the approved study's primary MAP output.

Secondary paired diagnostics are D03 versus M03, F02/F04 versus their matched partners, W03 versus M03, 256→1024 refinement for every profile, and half/base/double sensitivity at N=1024 only. Retain signed prequential and future residuals for F: increasing sigma can hide coherent omitted-force bias.

Use a central 90% **model-belief predictive interval**, explicitly a nominal mass label, not a demonstrated 90% repeated-sampling coverage guarantee. Preserve the full predictive mean, second moment, variance, interval endpoints and width. The mixture is diagnostic; it is not the approved comparison's primary MAP output. MAP selection/scoring is not implemented by this slice.

Freeze the generalized-inverse convention Q(p)=inf{x:F(x)>=p}, with interval [Q(0.05),Q(0.95)]. Sort finite-grid predictions by endpoint, breaking identical endpoint ties by coefficient index; aggregate the probability mass of exact endpoint ties. No interpolation or random tie-breaking is permitted. The tie order affects provenance only after equal endpoints are aggregated.

Construct interval/CDF enclosures from outward-bounded node probabilities, within-cell ranges of the future map and the continuous cell-mass bound. Do not treat a floating discrete quantile as an exact continuous quantile. Enclose every possible threshold crossing when the bounded CDF does not identify a unique endpoint; a crossing ambiguity is retained, not resolved by rounding. Retain literal finite-grid intervals separately from qualified continuous predictive enclosures. For an uncertain reference endpoint, classify only numerically definite inclusion or exclusion; otherwise use indeterminate.

Propagate endpoint, truth and probability uncertainty outward through squared loss, interval score and the paired differences. Q1's TV/mean proof alone does not certify quantile endpoints or score signs. A new CDF/quantile/score proof and regressions are prerequisites. If ambiguity prevents a decision, report inconclusive; do not invent a narrower certificate.

The grouping unit is the coefficient/world construction. M has four fixed groups; D, F and W reuse those groups as paired interventions. Grids, scales, nodes, repeated records and probes are not new independent samples. There is no population sampling model and no binomial interval, bootstrap confidence interval, p-value or universal coverage claim. A miss count out of four has resolution one quarter and is only a description of this panel. F has denominator two, D and W one each; do not pool them into a headline coverage rate.

**Pre-outcome local utility screen:** after all required numerical, identity and completion gates pass, accept this finite-panel learning screen only if the certified upper bounds of both Delta_point and Delta_interval are strictly below zero. If the certified lower bound of either is nonnegative, the proposed strict-improvement screen is not met (including an exact tie). Otherwise the screen is inconclusive. No post-outcome tradeoff, averaging across the two metrics, sigma selection or stress-case pooling is allowed. Report the per-world outcomes alongside the decision.

This rule supplies a justified relative prediction decision without inventing an absolute product tolerance. It does not show population superiority, calibrated 90% coverage, unseen-law adequacy or completion of RA-N03. Absolute task adequacy remains unresolved: the legacy 0.001 endpoint/RMSE target cannot be borrowed without matching metric, normalization, domain and prediction type. Q1's numerical margins are not scientific utility tolerances. The screen is fixed for review now; its numerical certificates and report implementation are not ready for execution.

## Per-prefix numerical qualification

The old one-record certificate is not automatically transferable. Author a separately versioned D1 proof and independent checks; preserve Q1 code/results unchanged.

For candidate f_j(k)=q_j*cos(sqrt(k)/2), use D_j = |q_j|/8 as a bound on |df_j/dk|. Validate the actual recorded-label enclosure and obtain a residual bound R_j over the full support. The conservative one-record bound R_j <= 1/2 + epsilon applies to M and these F constructions; W can use the tighter 1/16 + epsilon. Here epsilon is the explicitly verified native/reference endpoint allowance, not sigma.

For every admitted prefix use outward arithmetic to certify

    delta(N,sigma,prefix)
       <= (2/N) * sum_j(D_j * R_j / sigma^2) + 3e-9.

The 3e-9 remains conservative, overlapping bookkeeping for separately bounded node, centered-normalizer and normalized-weight errors; it is not three independent scientific noise sources. Re-establish each component <=1e-9 from actual native endpoints, conditioned native arithmetic, reference uncertainty and all record terms. No failed or zero-mass node may be removed to normalize survivors.

Keep the every-node native endpoint gate 1e-12 and verify the independent reference's stated 1e-60 allowance over every new training/future argument. Bound |x0-equilibrium|, |v*t|, k*t^2/m and the number of series/log/exp operations before reusing the reference method; do not silently increase an old oracle's counters. Extend the finite-log reference proof for two records and the new force transformation.

The future candidate map is g(k)=cos(3*sqrt(k)/4): |g|<=1, |g'|<=9/32 and |(g^2)'|<=9/16. Thus conservative continuous-versus-finite predictive bounds are

    mean:   2*delta + 9/(16*N) + epsilon
    second: 2*delta + 9/(8*N) + 3*epsilon
    variance: second_bound + 2*mean_bound + mean_bound^2.

These are resolution bounds on the candidate mixture, not errors against the omitted-force truth. For N=1024, propose the existing compatibility ceilings delta<=0.0081, mean<=0.018, second<=0.019 and variance<=0.056, justified using the new formulas and exact premises before execution. The two-record/base-sigma case must pass its own summed certificate. No four-record or duplicate-half-sigma case is admitted by analogy.

Independently check finite likelihood/prior/evidence/normalized weights; preserve shift and log-scaled-sum separately. Require all-node/finite-log gates above, and the complete 256→1024 stability checks TV<=0.001, mean difference<=0.0005 and variance difference<=0.001. These are numerical adequacy gates, not coverage or utility tests. CDF/quantile enclosure code needs its own proof/tests; the moment certificate alone does not validate interval endpoints.

## Outcomes, denominators and stopping

| Outcome | Interpretation / next decision |
| --- | --- |
| Contract, identity, reference or numerical gate fails | Reject this implementation/profile for the declared slice. Retain the failing row and every attempted/unrun row; no refinement expansion or relaxed tolerance. |
| Duplicate update violates the independently derived repeated-loss identity | Numerical/implementation defect. The expected identity is p2(k) proportional to p1(k)^2 divided by prior mass, with normalization and declared numerical allowances. |
| Duplicate update changes beliefs or narrows intervals beyond numerical uncertainty | Evidence of repeat sensitivity, not a coding failure by itself. It contradicts any interpretation of duplicate noiseless records as new independent information; report the magnitude and changed predictions. |
| Omitted force creates signed predictive bias or a definite interval miss | Retained finite-panel inadequacy evidence. It is not a population coverage estimate; do not enlarge sigma afterward to hide it. |
| All numerical/identity/completion gates pass and both co-primary upper bounds are below zero | Pass the named local learning-utility screen only; retain every per-world miss/width. This is neither calibrated coverage nor absolute task adequacy. |
| Required gates pass but either co-primary lower bound is nonnegative | The strict local improvement criterion is not met; preserve the baseline and score evidence. This is not automatically a numerical defect or population-level failure. |
| Required gates pass but numerical score enclosures do not determine the screen | Inconclusive. No grid expansion, new probe, relaxed sign rule or best-scale promotion under this protocol. |
| Resource, receipt, source, authority or process closure is incomplete | Incomplete attempt; no scientific pass, no successful-survivor headline, no automatic retry. |

Register all 40 belief rows, their frozen prior-reference forecast joins, 20 refinement rows and all declared paired/sensitivity score rows before work. Every row has unrun/attempted/completed/failed status and a reason; keep all candidates within a failed profile accounted for. Missing residuals or widths are null, never zero. If a required row fails, stop the batch, retain its failed/partial outputs and all remaining unrun identities. Report matched-world errors only with both planned and completed denominators; conditional summaries cannot replace the incomplete primary vector.

There is one fixed matrix, one prospective attempt and no sequential stopping for a favorable result. No replacing worlds, silently regenerating endpoints, changing a prior, adding seeds, selecting a sigma, narrowing intervals or rerunning a failure under the same authority. A later amendment must disclose exposure and preserve the original attempt and costs.

## Finite census, costs and implementation gaps

These are analytically counted high-level operations for this protocol, pending reconciliation with authored source. They are neither observed work nor an allocation:

| Item | Planned count |
| --- | ---: |
| Distinct coefficient groups / bundles | 4 / 8 |
| Unique constructed record slots / records across all prefix snapshots | 8 / 9 |
| Candidate ensembles / candidate instances | 16 / 10,240 |
| Belief evaluations / normalized node weights | 40 / 25,600 |
| Native training / future two-frame prediction calls | 26,880 / 10,240 |
| Total native prediction calls / frames | 37,120 / 74,240 |
| 256→1024 refinement / finest-only adjacent-scale contrasts | 20 / 12 |
| Duplicate / force / weak paired contrasts across both grids | 2 / 12 / 2 |
| Purchases, simulator calls, RNG draws, providers, publication calls in the scientific batch | 0 each |

Each belief evaluates every node and completed record; every future request is evaluated once per ensemble and reused only across its declared sigmas. Prequential forecasts reuse the already retained exact training-action node endpoints, with separate mixture/arithmetic costs. No-learning future forecasts reuse the retained future endpoints; their probability, CDF, quantile, score and enclosure work is separately counted, even when a physical baseline is shared across matched worlds. There are 40 independent normalizations in the native path and a separately counted independent reference pass. Reference series, transcendental operations, model binders, JSON/hash/fsync calls and full artifact/receipt counts must be fixed from the authored implementation before admission; the table is not a complete low-level execution census.

Keep one compact per-profile result plus shared exact-input forward/reference evidence, manifests, event records and explicit failed/partial outputs. Do not assume deduplication saves physical bytes when copies are retained. A bounded report schema and source-derived worst-case byte census are still missing; do not inherit Q1's 64+8 MiB allowance or claim the full-study storage floor blocks this source work.

Use the existing accounting ledger in three distinct views: authorized engineering/review/CI work; one measured cloud scientific batch whose cgroup begins before interpreter/bootstrap and ends after all batch writes; and external preparation/transport/review/publication actions with explicit identities/counts and CPU null where unobserved. Preserve failed attempts and whole-operation unknowns. Components inside a cgroup are not added to its aggregate again. A complete activity inventory is not a claim that every CPU second was measured.

The original cumulative 8 CPU-hour/1 GiB comparison authorization has no defensible free balance yet. The failed original GRID allocation remains held; the supervised diagnostic accepted only captured intervals and output, not complete historical/whole-operation accounting. Neither the old 33,600 CPU-second host reservation nor its observed host bound is a new D1 allocation. A complete finite CPU/wall/output forecast and any necessary allocation/attribution decision must precede numerical execution.

### Proposed resource envelope, not admission

Plan one fixed offline scientific service using the unchanged qualified systemd lifecycle: 50% CPU quota with a 100 ms period; 1,710 s runtime plus 10 s startup and 10 s stop allowance; 1,740 s terminal deadline; and a failure-inclusive 900 CPU-second service reservation. A possible 600 CPU-second watch is only an early-stop trigger, not a hard bound on cumulative use. Imports/bootstrap, fixture generation, all eight bundles, independent references, checks, contrasts, serialization, report/fsync and failure records belong inside that measured service.

This is a conservative planning envelope, not a measured forecast, invocation authority or whole-operation CPU cap. Source-derived workload and enforced limits must reconcile before a run proposal. There is no automatic retry or new whole-host lease. Do not repeat the three live lifecycle qualification controls if exact operational bytes and contracts remain unchanged; a necessary tiny preflight must be explicitly enumerated and charged, otherwise omit it.

Propose 96 MiB total new retained output: 64 MiB science/report, 16 MiB implementation/qualification, 8 MiB integration/CI and 8 MiB external control/closeout/publication. Failures, partial files and retained copies count. Authored source must fix actual per-record/per-file ceilings and the complete output census. The proposed initial free-space requirement is 20 GiB + 104 MiB (21,583,888,384 bytes), with 20 GiB required later; the extra 8 MiB is a cushion, not output allowance. This prospective policy requires explicit future admission. It neither inherits the consumed GRID exception nor silently waives the older 50/45 GiB guards. No purchase or cleanup is requested.

External preparation, transport, independent review and publication need bounded action counts and retained records; CPU may remain null where unobserved and must be disclosed separately. Calling the service's 900 CPU-second reservation a complete operation limit would be false. If an all-inclusive CPU ceiling is required, resolve attribution before admission instead of treating missing costs as zero.

Source work can proceed now under existing RA-N03 implementation authorization, in independently reviewable units: (1) explicit synthetic fixture/one-way audit and exposure contracts; (2) D1 prefix/reference/moment/CDF bounds and finite report contracts; (3) one bounded disabled runner and meaningful fake/reference tests with exact census. The runner does not exist yet. No current GRID wrapper or earlier approval automatically admits it.

## Decisions to resolve before a numerical proposal

1. Confirm the working-loss interpretation to test while keeping generative Gaussian and calibrated-probability claims blocked.
2. Independently review the frozen prior-reference, co-primary score/sign rule and exact quantile convention; implement and qualify its endpoint/score enclosures. Absolute product adequacy remains a separate unresolved requirement.
3. Accept exact disjoint/exposure manifests, new per-prefix/reference/CDF bounds and the eight-bundle control matrix.
4. Complete the authored work/output census, engineering qualification and finite allocation/accounting proposal. Existing source authorization is not contingent on this later run decision.

## Route to the existing selector question

D1 answers whether a named deterministic belief update improves a held-out forecast against no learning, and whether duplicate, weak or omitted-force cases reveal important limitations. It does not measure active experiment selection. A favorable screen is only supporting development evidence for the separately required RA-N03 fixture freeze and RA-N04 action-ranking checks; a negative or inconclusive screen can stop that interpretation without expanding the study.

The smallest later informative selector contrast is a preregistered paired comparison of the already proposed posterior-weighted selector against random selection on untouched comparison worlds, with uniform disagreement retained as the planned third reference. Keep the existing six worlds, two seeds, 12 slots per episode (four calibration plus eight selected actions), three selectors and overall 36 episodes/432 slots; this document adds no episodes or execution authority. Freeze the action bank, primary implemented/validated MAP predictor, held-out probes and losses before opening those outcomes. Pair by world/seed, preserve failures and budget slots, and use the already approved study protocol's uncertainty analysis. D1 worlds, labels and stress constructions cannot become test units or be used to tune the selector after those outcomes are exposed.

Parallel Laplace analytic validation can continue where the checked reference and interfaces apply. Comparative Laplace validation still needs accepted/frozen RA-N03 fixtures and its own declared audit; D1 alone does not provide them. Neither path gains an RA-07.b or enterprise prerequisite.

Separately labeled synthetic-noise sanity tests, genuinely independent generative calibration replications, action-ranking validation and full RA-N03 fixture acceptance remain outside D1. A noise lane needs an explicit adapter and distribution contract; it cannot pass noisy samples through the production zero-noise guard by lying in metadata.
