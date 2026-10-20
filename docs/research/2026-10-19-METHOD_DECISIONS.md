# Research methods amendment — 2026-10-19

**Status:** proposed research execution extension; planning work is authorized. Runtime tasks, paid pilots and official studies retain the gates below. No new method was implemented or reproduced by this review.
**Owner:** project lead. **Review cutoff:** 2026-10-19 UTC. **Saved:** 2026-10-20 UTC.
**Canonical links:** [roadmap](../ROADMAP.md), [benchmark](../BENCHMARK.md), [execution backlog](../EXECUTION_BACKLOG.md), [machine-readable ledger](../execution-backlog.json).
**Baseline preserved:** 168 approved tasks, 369 dependencies and ten gates. This extension has 18 separate proposed PR tasks. It does not silently rebaseline that graph or its conditional nine-person GA forecast.

## Decision

Build on recent scientific-discovery methods while preserving the controls that make the results interpretable. The current spring I1 slice continues: purchased observations, numerical fit, prediction, independent scoring, then SDK/CLI. Existing simple random exploration, sparse fitting and bootstrap disagreement remain required controls.

Add a bounded model-belief engine, stronger classical symbolic methods, typed LLM hypothesis proposals and explicit change adaptation. Treat them as separate factors before comparing full systems. This is a research plan for testing these ideas, not evidence that any method is state of the art on Strange Physics.

No training GPU is required for the proposed first extension. CPU cost, inference cost and runtime still need measurement. Hosted isolation, service identity, enterprise delivery and all release gates remain part of the approved product plan.

## Primary-source review

Dates below identify publication/version dates rather than claiming every technique is new. Code availability was checked against official repositories through the cutoff. None of these external methods has been run here.

| Source and version | What it contributes | Decision and limitation |
| --- | --- | --- |
| [Model Discovery Agent, v5](https://arxiv.org/html/2608.09696v5), first 2026-08-10, revised 2026-09-27 | LLM model proposals, numerical parameter/evidence updates, predictive checks and adaptive experiments. Current examples include ChemBench, GlucoseBench and NeuronBench. | Adapt bounded belief/pool management in RA-05/06/10. Appendix A.9 uses noise-whitened weighted disagreement as a surrogate; do not present it as an independently novel exact-MI selector. Full public solver availability is unresolved. |
| [LLM-AutoSciLab](https://arxiv.org/html/2605.24043v1), 2026-05-21 | Iterative hypothesis/search-region proposals, numerical refitting, disambiguation/refinement and bootstrap feedback. | RA-08/12 tests these mechanisms on trajectories. The paper's fixed-system setting does not establish within-run change recovery. Appendix E.1 permits ground-truth RMSLE in memory/selection when available, and Appendix C describes an LLM symbolic judge with the true expression. Our agent never receives those evaluator outputs. Pinned released code also inserts ground-truth RMSLE into discovery memory and uses it for final candidate selection; disabling the mid-run flag alone does not remove the final selection path. See the source audit below. |
| [LLM-ACES](https://arxiv.org/html/2606.25039v1), 2026-06-23 | LLM proposes operator sets; PySR fits equations; rollout disagreement selects initial conditions. | Closest direct dynamics comparator: RA-04.a/b/08/11. Preserve this division of labor. Authors report one run per system in the main experiment; our paired-world/seed uncertainty and sealed unseen-condition evaluation remain necessary. |
| [NewtonBench v3](https://arxiv.org/abs/2510.07172v3), first 2025-10-08, revised 2026-02-24 | 324 interactive tasks across 12 physics domains using counterfactual law shifts. | RA-01/02 maps domain/noise tests and external sanity checks. Different laws across tasks are not evidence of recovery after an unannounced change inside one run. Do not substitute its symbolic-accuracy target for our held-out predictive error. |
| [PySR / SymbolicRegression.jl](https://arxiv.org/abs/2305.01582), first 2023-05-02 | Evolutionary symbolic structure search with numerical constant optimization. | Strong classical structure control in RA-04.a/b. It is not an acquisition policy by itself. Pin the Python and Julia environments and bound grammar/search cost. |
| [PySINDy Bayesian example](https://pysindy.readthedocs.io/en/stable/examples/sindy-addl-examples/ba5b7b66/example.html) and [weak-form examples](https://pysindy.readthedocs.io/en/latest/examples/index.html) | Sparse dynamics identification, weak formulations and uncertainty implementations. | RA-04.a/b/05 compares a weak-form classical adapter and explicit likelihoods. The documented SBR implementation puts error on derivatives, unlike state-noise UQ-SINDy; it cannot be substituted for our observation likelihood without a measured noise transformation. |
| [Statistical mechanics of dynamical system identification](https://doi.org/10.1103/4d98-tdlp), 2025-08-21, ZSINDy | Bayesian treatment of sparse identification and uncertainty/bias limits. | Reference for tractable posterior tests in RA-05/06; code reuse deferred because license coverage is unresolved. Do not add another full inference backend before a measured need. |

The inspected papers motivate stronger methods. We found no controlled unannounced within-run law-change recovery protocol in the three discovery methods above. That supports investigating our adaptation question; it does not prove universal novelty. Publication tables are author-reported evidence, not reproduced Strange Physics results.

## Source and reproduction ledger

Repository existence is not a completed reproduction. Pin these inspected identities before any future dependency decision; newer revisions require review.

| Official repository | Inspected commit / release | License and available evidence |
| --- | --- | --- |
| [NewtonBench](https://github.com/HKUST-KnowComp/NewtonBench/tree/912a4ba5f4356ddd06acc16e44460ca30be4abc2) | 912a4ba5f4356ddd06acc16e44460ca30be4abc2; v1.0.1, 2025-12-15 | MIT. Benchmark and agent entry points available. No local reproduction. |
| [PySR](https://github.com/astroautomata/PySR/tree/72a9ab982e72eb1c80a063b8fcc4b551daf9660e) | 72a9ab982e72eb1c80a063b8fcc4b551daf9660e; v2.7.2, 2026-10-19 | Apache-2.0. Method implementation exists; compatibility with our pinned runtime is not tested. |
| [SymbolicRegression.jl](https://github.com/astroautomata/SymbolicRegression.jl/tree/83ca176f2274eb3bf815bf63ec7c91c51f1967e4) | 83ca176f2274eb3bf815bf63ec7c91c51f1967e4; v2.7.2, 2026-10-17 | Apache-2.0. Julia backend; pin compatible lock/runtime before execution. |
| [PySINDy](https://github.com/dynamicslab/pysindy/tree/c4421fcec275c8f4cc5c1e93bebb961b212067ae) | c4421fcec275c8f4cc5c1e93bebb961b212067ae; v2.1.0, 2026-01-08 | Complete LICENSE is MIT with sparsereg and project copyright notices. Preserve attribution; review transitive/runtime dependencies. |
| [LLM-AutoSciLab](https://github.com/scientific-discovery/LLM-AutoSciLab/tree/351aae73e6c6c279e67943b77143b0f118d1e289) | 351aae73e6c6c279e67943b77143b0f118d1e289, 2026-10-01 | Method loops/configs/runners exist. No LICENSE/COPYING file or repository license metadata was found; no release or published raw-run artifacts found in the inspected tree. A website content license does not establish code permission. Resolve a grant before reuse. |
| [LLM-ACES](https://github.com/scientific-discovery/LLM-ACES/tree/34ceeb99f57fb679763ed3ec3fb27b5115d03a18) | 34ceeb99f57fb679763ed3ec3fb27b5115d03a18, 2026-10-16 | Method pipeline, PySR configuration and prompts exist. README says MIT, but linked LICENSE returns 404 and the tree has no license file/metadata. No release/raw-run artifacts found. Clarify coverage before copying. |
| [MDA](https://github.com/murphyk/MDA) | Official full-solver link returned 404 at review | The paper is available; a faithful solver reproduction is not established. Missing public code is not evidence that the method is invalid. |
| [NeuronBench](https://github.com/murphyk/neuronbench/tree/c354622458c460b419cab821d482c879f0578377) / [GlucoseBench](https://github.com/murphyk/glucosebench/tree/6bb0ff6f44513e1e816ac3f0827531a366e8d7a0) | c354622458c460b419cab821d482c879f0578377 / 6bb0ff6f44513e1e816ac3f0827531a366e8d7a0 | MIT benchmark packages and simple baselines; READMEs distinguish them from MDA's posterior/evidence/VoI solver and learned-run artifacts. Benchmark access does not reproduce MDA. |
| [ZSINDy](https://github.com/josephbakarji/zsindy/tree/c31039d826039e62fdf4cbcf71b8423bb1282a54) | c31039d826039e62fdf4cbcf71b8423bb1282a54, 2024-03-09 | No license file/metadata or release found. Theory may inform our design; direct code reuse is deferred. |

A paper-inspired clean implementation must be labeled as such, with departures recorded. “Reproduced” requires an executable recipe, exact source/config/data identities, actual output, cost/failure logs and independent comparison against a stated target. Licensing questions do not authorize contacting authors on the user's behalf.

### AutoSciLab evaluator-access audit

At the pinned revision, [discovery.py](https://github.com/scientific-discovery/LLM-AutoSciLab/blob/351aae73e6c6c279e67943b77143b0f118d1e289/autoscilab/loop/discovery.py#L1925) evaluates proposals against the oracle during discovery, and [memory.py](https://github.com/scientific-discovery/LLM-AutoSciLab/blob/351aae73e6c6c279e67943b77143b0f118d1e289/autoscilab/llm/memory.py#L384) places that score in proposal memory. Final candidate selection also uses ground-truth RMSLE without the mid-run flag guard. This is a source inspection, not execution or a claim about every published run. RA-12 must remove both feedback paths in our adapted protocol and test that boundary; turning off one configuration flag is insufficient.

## Comparison design

### A0 — retain the simple shared-model controls

Keep random, classical bootstrap disagreement and the bounded LLM selector on the same sparse fitter, bootstrap procedure, candidate-menu policy, public information rules and observation budget. Each online arm sees only its own purchased history. Fix adaptation while comparing selectors. These controls answer whether experiment choice helps within one disclosed model class.

### Early offline checkpoint — evidence before provider profiles

RA-07.b follows I1, the classical linear fitter, calibrated model beliefs and acquisition producers. Freeze six stationary spring worlds, two policy seeds and three fixed-pool selectors: **36 episodes**, **12 purchased slots** per episode including four common calibrations, **432 slots** maximum. Freeze world/noise identities, model pool, priors/likelihood, action menus and disjoint probes before measurements. Aggregate seeds within each world; report paired descriptive error, failures and CPU.

Use only supported native LinearSpringModel candidates with real hashes; primary prediction is the declared MAP candidate. The current scorer cannot accept a richer DAG or mixture under a dummy linear identity. Richer profiles need a separately reviewed SP-19/20 model-to-prediction/evaluation binding. New symbolic adapters are not prerequisites for this result.

Proposed limits are **8 CPU-core-hours** and **1 GiB new artifacts** on the existing machine. No provider calls, network use or provisioning. Stop and retain incomplete cells at either cap. This reduced-budget development result is not an official40-slot score, population claim or adaptation result. RA_EXEC still gates implementation; this branch has no SP-18/20 or RA-09–12 prerequisite.

### A1 — isolate acquisition under model uncertainty

Common-prefix ranking diagnostics use the exact same pool, prior, likelihood, posterior snapshot and menu. Online arms share those definitions and inference settings, but each posterior updates only from that arm's purchased history. Histories and posteriors then diverge; no cross-arm observations are shared. Compare random, unweighted disagreement and posterior-weighted disagreement. An optional expected-information-gain arm must pass a distinction/calibration gate.

Changing from A0 bootstrap uncertainty to A1 numerical Bayesian beliefs changes the uncertainty engine; report that as a separate factor. It cannot be called a pure selector improvement.

For a scalar prediction with constant Gaussian observation noise, moment-matched information gain is proportional to log(1 + disagreement/noise variance), which gives the same ranking as disagreement. A new label does not create a new arm. In vector observations, a covariance log-determinant may rank actions differently from a trace. Exact categorical-model mutual information is bounded by posterior model entropy; an unbounded disagreement surrogate is not that quantity. Fix the uncertainty target (model identity versus joint model/parameters), estimator, bias diagnostics, Monte Carlo error and tie rules before results. No silent clipping or dropping difficult candidates.

### B — richer models and full systems

First hold selection fixed and compare sparse-library fitting, classical PySR structure search, LLM proposals plus the same numerical fit, and combined proposals. Use a bounded typed grammar rather than generated Python. Numeric fitting/evidence and LLM structure or operator-prior proposals remain separate.

Then compare named MDA-inspired, ACES-inspired and AutoSciLab-inspired complete profiles. Each profile declares its search space, priors, proposal schedule, inference approximations, selection policy and compute caps. These results describe the whole system, not selector causality. A fixed grammar is disclosed to all relevant controls; if one arm uses a different grammar, report a separate model-class condition.

### C — adaptation after a law changes

Retain all-history, fixed-window and detector-reset controls. Add calibrated change belief with fixed-pool reweight/reset, then open-pool revision after predictive failure. Use predictions made before each new purchased observation for detection. A new action distribution can create residual shifts without a law change; include that negative control.

The initial confirmatory strata remain stationary, abrupt coefficient changes, and term activation/deactivation. Keep 40 accepted slots, four shared calibration actions and the hidden change window after slots 16–24. Failed simulations consume slots. Family switches, gradual drift and recurring regimes are later separately frozen extensions.

Measure held-out error at every budget, the 16-slot post-change error, stationary false alarms, detection delay, censored recovery/nonrecovery, calibration and all costs. An oracle change detector is an explicitly labeled upper bound only. Model pruning and relearning consume resources and remain in provenance. Do not condition averages on successful recovery.

## Data and scientific boundaries

Use existing development worlds for tuning and calibration, then freeze independent test-world, parameter, structure, noise and action-condition manifests. Keep public reference and blind suites distinct. Use paired world/change seeds and common calibration actions; aggregate policy seeds within a world before world-level uncertainty estimates. Treat the world, not individual frames, as the independent sampling unit.

Only purchased observations enter fitting, hypothesis memory, selection or change detection. Evaluator truth, unseen predictions' labels and evaluator scores never return to the agent. Hashes identify artifacts; they do not make public labels secret. Full-system evaluators retain the existing isolation and network restrictions in SP-19/20.

Prediction error is primary. Symbolic recovery is a secondary, explicitly equivalence-aware diagnostic; an LLM judge with the true expression cannot be the primary quality metric. Retain unidentifiable worlds, invalid hypotheses, solver failures, provider failures, timeouts and missing outputs under predeclared rules.

The first belief engine uses a grid reference plus exactly one Laplace approximation. BIC is a separately labeled diagnostic. SMC stays deferred until a measured failure justifies a new scoped task.

No new real-world dataset or private corpus is required for the first extension. External NewtonBench or paper-domain checks need a distinct dataset/license/contamination manifest. Public examples used in prompts or development cannot be described as unseen.

## Proposed interfaces

These are design obligations for future PRs, not changes to frozen contracts.

| ID | Required fields and invariant |
| --- | --- |
| SOURCE | Paper version, repository commit, license grant, dependencies, recipe, expected artifacts, reproduction status and review date. |
| MODEL | Versioned operator DAG, parameter schema/prior, domain/units, complexity and solver limits, model hash, typed invalid/failed outcomes. |
| BELIEF | Observation-prefix/model-pool/config hashes, prior/likelihood identities, parameter samples or approximation, normalized model weights, ESS/conditioning, predictive-check results and numerical failures. |
| ACQUISITION | Frozen posterior/action-menu hashes, objective and target, scores plus error diagnostics, tie rule, selected action, calls/time and failure policy. |
| PROPOSAL | Purchased-prefix/context/prompt/provider identities, typed operator or structure proposal, rejection/deduplication records, numerical-fit link, tokens/retries/cost. No evaluator fields. |
| ADAPT | Pre-update prediction, purchased residual, detector/config state, reset/expand/prune decision, archived hypotheses, change-belief uncertainty and resource cost. |
| STUDY | Track/arm/ablation IDs, world/policy seeds, paired conditions, all config hashes, metric/normalization/failure rules, evaluator access, stop rules and immutable run identity. |
| COST | Purchased slots; physical/virtual forward and likelihood evaluations; posterior updates; proposal/search counts; CPU/wall/memory; provider tokens/cache/retries; evaluator/storage cost; actual versus quoted amounts. |

Review MODEL/BELIEF with SP-19.a and the existing SCI contracts. Richer internal artifacts must not silently change the v1 spring or hosted public wire formats.

## Bounded pilot and cost decision

This is a proposed ceiling, not authority to spend. RA_PILOT requires an exact SKU/price quote, fixed configuration and explicit approval. Existing PAID_TRIAL and OFFICIAL_SWEEP gates remain in force.

1. Start with recorded provider fixtures and small tractable posterior/grammar cases. No training or accelerator allocation.
2. Optional later feasibility pilot: three law families × three strata × one development world seed × two policy seeds × nine profiles = **162 episodes**, at most **6,480 purchased slots**. Nine profiles are A0 random, A0 disagreement, A0 LLM selector; A1 random and weighted disagreement; classical PySR; MDA-inspired, ACES-inspired and AutoSciLab-inspired. With only one independent world per family/stratum, this matrix cannot estimate within-stratum world variance, power or population failure intervals. RA-13.b separately measures replicated-world precision under its own quoted approval. Additional A1 EIG, proposal-only and adaptation ablations must be selected in a separately counted matrix before freeze.
3. A0 LLM selection may call once plus at most two retries in each of 36 adaptive slots. Each richer LLM profile proposes at five fixed budget checkpoints, at most one call plus two retries per checkpoint. Across the pilot this is at most **2,754 provider attempts** (18 × 36 × 3 + 54 × 5 × 3). Numerical fitting is separately capped. Unavailable profiles may be excluded before a run, with explicit reasons and a revised frozen matrix, dependencies and episode/call/token counts. Nine profiles are a maximum, not a prerequisite for the early offline result. Failed calls consume the allowance.
4. Proposed hard ceilings: **3,000 provider attempts**, **48 million input and 6 million output tokens**, **240 CPU-core-hours**, **8 GiB retained new pilot artifacts**, and **US$1,000 total incremental provider/compute/storage spend** before credits/taxes. Stop when any limit is reached; report incomplete cells. These are planning constraints, not measured requirements or price estimates. Existing approved machine costs are disclosed separately; no automatic machine enlargement.
5. Before approval, quote provider model IDs and input/output/cache prices and cloud CPU/storage rates with date/region. Compute the upper bound from the token/call matrix and measured per-episode CPU, including retries and evaluator cost. If the quote exceeds the dollar ceiling, reduce the preregistered matrix or request a new concrete cap before any run. Never reinterpret a cap as permission for unpriced work.
6. Feasibility acceptance includes complete accounting, fixture calibration checks, no leakage, descriptive failures, successful interruption/replay, independent scoring and a resource forecast. An expensive or unsuccessful method is a valid finding.

RA-13.b first adds independent development worlds within each retained stratum under a separately approved sample/stopping rule and quoted cost cap. Policy seeds cannot substitute for independent worlds. A larger official matrix is chosen only after that replicated-world precision and paired-effect evidence. The existing 2,430-episode draft study is not launched or multiplied automatically by the new arms. At the proposed pilot's maximum token volume, provider cost is 48 × input-price-per-million + 6 × output-price-per-million, plus any separately charged cache/tool amounts; actual prices remain unknown until the quote. Report both observed cost and the unused cap.

## Execution extension and gates

The task records below are a separate proposed queue. Existing task IDs and dependencies are unchanged. Every task has a single reviewable deliverable; adapters are split by method. Effort is human engineering effort, not elapsed subagent time.

- **RA_EXEC:** owner accepts the scoped extension and staffing after review of this artifact; implementation gate, currently pending. All 18 task records inherit it transitively.
- **RA_PILOT:** after RA-02, RA-07.b, admitted profile/adaptation dependencies, SP-07.d and SP-18.d, owner approves the exact feasibility matrix, quote and stop limits. Profile exclusions require a revised dependency list and counts. Existing paid-provider gates remain.
- **RA_SIZING:** after RA-13.a, owner approves an independent-world sample/stopping rule and quoted runtime/cost cap for RA-13.b. Feasibility alone cannot pass this gate.
- **RA_OFFICIAL:** after RA-14, independent scientific/security review and existing OFFICIAL_SWEEP approval. It cannot waive pilot, deployment, release or calendar gates.

Base effort is **48–78 engineer-days**, plus a **25% planning reserve (12–19.5 days)**, total **60–97.5 days**. Estimates are medium/low confidence until source reproduction and inference timing exist. This increment is not included in the baseline GA W52–67 reference. A separate forecast is required before adding it to a release promise.

After prerequisites are available, RS1 can deliver representation/belief/proposal/adaptation work while RS2 handles classical adapters/acquisition/profiles, with Quality calibrating/reviewing and Platform checking isolation/runtime dependencies. In the current lead-plus-three execution mode these specialties rotate; active credential and I1 work keeps its current owners. Do not pretend nine human lanes are staffed.

The early branch is RA_EXEC → RA-01 → RA-03 → RA-03.b → RA-05 → RA-06 → RA-07 → RA-07.b, joined by RA-02 and I1. Baseline scientific predecessors still apply; provider profiles and hosted deployment do not.

The larger branch forks after representation: RA-04.a/b builds classical adapters, RA-05/06 builds beliefs, and RA-08 builds proposals after its provider-interface prerequisites. RA-09 joins beliefs, acquisition and proposals. RA-10/11/12 join those producers and accepted SP-20.d isolation. Then RA_PILOT → RA-13.a → RA_SIZING → RA-13.b → RA-14. Baseline scientific/provider/isolation predecessors can dominate availability. RA-08 may proceed alongside belief work; assignment alone never satisfies a prerequisite.

### Milestone exit gates

| Increment | Exit evidence | Scheduling rule |
| --- | --- | --- |
| E0: source and interfaces | RA-01/02/03/03.b reviewed; missing licenses isolated; exact contracts and budgets resolve | After RA_EXEC and every named baseline predecessor |
| E1: classical and uncertainty foundation | RA-04.a/b/05/06 pass tractable tests and predictive calibration or record rejected arms | After E0; parallelize only available work |
| E1a: first offline result | RA-07.b manifest, analytic rankings, complete paired descriptive results and measured CPU | No provider profile or hosted deployment dependency |
| E2: selectors, proposals and adaptation | RA-07/08/09 pass information-boundary and equivalence tests | Depends on actual predecessor acceptance, not calendar week |
| E3: composed profiles | RA-10/11/12 independently reviewed with explicit paper departures | Full-system isolation SP-20.d must already pass |
| E4: development evidence | RA-13.a complete or stopped transparently; exact costs and failures retained | RA_PILOT and existing provider gates required |
| E4b: replicated-world sizing | RA-13.b world-level uncertainty and prospective study-size evidence | Separate RA_SIZING quote/approval |
| E5: study decision | RA-14 frozen manifest, reviewed estimate and capacity/release reforecast | Official sweep remains separately gated |

The first two weeks below are conditional on RA_EXEC, I1 and all task-specific baseline prerequisites. If a prerequisite is missing, continue approved baseline work; do not start the dependent task early.

| Day | Research lane 1 | Research lane 2 / Platform | Quality / lead checkpoint |
| --- | --- | --- | --- |
| 1 | RA-01 paper/version audit | License/runtime inventory | Confirm inherited gates and source ledger |
| 2 | Finish RA-01 recipes | Independent code/license review | Accept or exclude each reuse path |
| 3 | RA-03 typed contract design | RA-02 manifest/cost design with Quality | Producer/consumer review |
| 4 | RA-03 validation/serialization | RA-02 counters and failure cases | Reject mixed-track or leaking manifests |
| 5 | RA-03 review; RA-03.b consumer design | Finish RA-02 | Contracts checkpoint; E0 also needs consumer acceptance |
| 6 | RA-03.b bounded runtime | RA-02 review; independent runtime review | Freeze calibration criteria before measurements |
| 7 | RA-03.b analytic/failure tests | RA-04.a/b design only; implementation waits03.b | Numerical and isolation review |
| 8 | RA-03.b review repairs | Prepare isolated adapter fixtures | Resolve reference mismatches |
| 9 | RA-05 starts only after03.b acceptance | RA-04.a starts only after03.b acceptance | No live provider calls |
| 10 | RA-05 reference design checkpoint | Continue RA-04.a; schedule04.b separately | Re-estimate before RA-06; do not claim E1 early |

Later scheduling is milestone-level until measured throughput exists. The ten-day plan is a best-case work allocation, not a promise that the upper estimates fit ten calendar days. It reserves review gates and carries unfinished work forward rather than compressing estimates.

## PR-sized task records

### RA-01 — Audit source, licenses and reproduction recipes

- **Objective:** Make each borrowed method traceable and lawful to reuse.
- **Owner:** Research + Platform; primary lane RS1.
- **Scope:** Pin paper versions, official code, dependency/runtime versions, license grants and artifact availability. Record the gap between an inspired adapter and faithful reproduction. Prepare one executable recipe per admitted method.
- **Out of scope:** Downloading restricted datasets, contacting authors, running paid providers or claiming reproduction.
- **Prerequisites:** RA_EXEC.
- **Required contracts:** SOURCE (definitions above).
- **Acceptance:** Each source has a dated identity, code/license status, expected outputs and explicit go/no-go. Missing MDA solver or ambiguous licenses blocks reuse of that code.
- **Automated tests:** Validate manifests, URLs/identities and required provenance fields; fixture missing-license rejection.
- **Security and reliability:** Do not execute external code in a privileged process; retain notices and review transitive licenses.
- **Effort / confidence:** 2–3 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-02 — Freeze comparison manifests and cost ledger

- **Objective:** Make comparisons reproducible and cost-complete.
- **Owner:** Quality + Research; primary lane QE.
- **Scope:** Version study cells, seeds, model and selector configurations, budget counters, termination rules and compute accounting; persist all failed/rejected proposals and selected-action identities.
- **Out of scope:** Changing the approved 40-slot distribution or running an official study.
- **Prerequisites:** RA-01, SP-04.e.
- **Required contracts:** STUDY, COST (definitions above).
- **Acceptance:** A manifest prevents mixing A0/A1/B/C results, resolves all referenced hashes, and rejects unavailable budget or evaluator feedback. Pilot totals and stop rules reconcile.
- **Automated tests:** Round-trip/hash tests, duplicate/missing/cross-track cases, token/retry accounting and cap exhaustion.
- **Security and reliability:** No provider secrets in provenance; monotonic accounting, no resume double charging or free retry.
- **Effort / confidence:** 3–4 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-03 — Add bounded symbolic model contracts

- **Objective:** Represent richer hypotheses without arbitrary generated code.
- **Owner:** Research + Platform; primary lane RS1.
- **Scope:** Add a separately versioned typed expression DAG for approved spring/radial/velocity operators, domains, dimensionless units, parameter priors and numerical limits. Preserve frozen LinearSpringModel and SCI v1 bytes. Define the bounded consumer interface; executable solver is RA-03.b.
- **Out of scope:** General Python execution, arbitrary operators, latent stochastic dynamics or a silent v1 migration.
- **Prerequisites:** RA-01, SP-04.e, SP-04.d, SP-19.a.
- **Required contracts:** MODEL (definitions above).
- **Acceptance:** Canonical serialization/deduplication and static bounds pass; invalid shape has a typed outcome; consumer interface explicitly identifies solver/config/error artifacts.
- **Automated tests:** Grammar/property tests, depth/node/parameter caps, canonical identity rules and v1 byte compatibility.
- **Security and reliability:** Bound depth/nodes/parameters and evaluator memory; never eval generated text.
- **Effort / confidence:** 2–3 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-03.b — Execute bounded symbolic models

- **Objective:** Give every admitted hypothesis the same bounded numerical prediction runtime.
- **Owner:** Research + Platform; primary lane RS1.
- **Scope:** Implement validated DAG evaluation to vector fields and the recorded numerical solver; cap steps/time/memory and retain complete request/result provenance. Begin with the calibrated spring subset, extend operators only after their existing SP-03.c calibration passes.
- **Out of scope:** Arbitrary generated code, new solver families, full custom-agent hosting or uncalibrated law claims.
- **Prerequisites:** RA-03.
- **Required contracts:** MODEL (definitions above).
- **Acceptance:** Known trajectories meet preregistered tolerance; every singularity, nonfinite value or cap violation returns a complete typed failure without partial success. Identical source/config/input reproduces metrics.
- **Automated tests:** Independent analytic references, solver refinement, singularity/overflow/underflow, negative/missing IDs, timeout/output limits and interrupted execution.
- **Security and reliability:** No eval or dynamic imports; bounded arithmetic and isolated optional backends; evaluator labels never enter the model.
- **Effort / confidence:** 3–5 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-04.a — Build the classical symbolic-search adapter

- **Objective:** Supply strong non-LLM structure-search controls.
- **Owner:** Research + Platform; primary lane RS2.
- **Scope:** Add an isolated pinned PySR adapter over purchased observations. Fix operator grammar, search budget and selection criterion before testing; retain candidate/failure records.
- **Out of scope:** Weak-form fitting, unrestricted Julia plugins, dependency upgrades or hidden-truth model selection.
- **Prerequisites:** RA-03.b, RA-02.
- **Required contracts:** MODEL, STUDY, COST (definitions above).
- **Acceptance:** The PySR adapter produces validated models under hard CPU/memory/time caps, with exact Python/Julia source and configuration identities.
- **Automated tests:** Known-equation and misspecified dictionary fixtures, noise sensitivity, deterministic seed/config tests, subprocess timeout and malformed output.
- **Security and reliability:** Separate removable dependencies, no mutable cross-checkout links; untrusted optimizer output passes MODEL validation.
- **Effort / confidence:** 3–5 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-04.b — Build the weak-form sparse adapter

- **Objective:** Test a strong noise-aware classical dictionary control.
- **Owner:** Research + Platform; primary lane RS1.
- **Scope:** Implement one pinned weak-form sparse-library adapter over the same purchased position/velocity observations. Record test functions, integral/noise assumptions, dictionary and regularization selection without evaluator feedback.
- **Out of scope:** PySR search, derivative-noise treated as state-noise, multiple weak-form backends or an unreviewed new likelihood.
- **Prerequisites:** RA-03.b, RA-02.
- **Required contracts:** MODEL, STUDY, COST (definitions above).
- **Acceptance:** Known-equation and noisy development fixtures validate the declared dictionary and weak-form error treatment; comparison with the existing integrated fitter retains all failures.
- **Automated tests:** Known integrals, irregular/invalid grids, correlated integral errors, conditioning and sparse-fit failures, data-boundary and replay tests.
- **Security and reliability:** Validate observation shapes and integral covariance assumptions; no calibrated probability claim from sparse coefficients alone.
- **Effort / confidence:** 3–5 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-05 — Implement small-pool numerical model beliefs

- **Objective:** Estimate parameter and model uncertainty with explicit assumptions.
- **Owner:** Research + Quality; primary lane RS1.
- **Scope:** Implement a bounded fixed-pool observation likelihood and tractable grid reference, then exactly one approximation: Laplace parameter/evidence updates. Store priors, weights, conditioning, numerical errors and likelihood evaluations. Treat BIC as a separately labeled diagnostic only; SMC is deferred until a documented failure justifies another scoped task.
- **Out of scope:** Adding multiple inference backends, interpreting BIC as calibrated posterior probability, latent-particle filtering or a general probabilistic programming platform.
- **Prerequisites:** RA-03.b, SP-05.a, SP-06.a.
- **Required contracts:** BELIEF, MODEL (definitions above).
- **Acceptance:** Analytic fixtures reproduce evidence/posterior predictions; approximations are labeled and compared with the reference; misspecification and numerical collapse remain visible.
- **Automated tests:** Quadrature/analytic posterior tests, prior sensitivity, conditioning, weight collapse, log-weight extremes, reproducible resume.
- **Security and reliability:** Validate covariance/noise domain; fail closed on nonfinite weights; preserve complete purchased-data provenance.
- **Effort / confidence:** 4–6 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-06 — Calibrate posterior predictive checks

- **Objective:** Prevent overconfident model beliefs from passing as progress.
- **Owner:** Quality + Research; primary lane QE.
- **Scope:** Measure predictive calibration and prequential residual behavior on tractable development worlds; separate measurement noise, parameter uncertainty and model disagreement; compare posterior approximations.
- **Out of scope:** Tuning thresholds on sealed test worlds or claiming universal coverage.
- **Prerequisites:** RA-05, RA-02.
- **Required contracts:** BELIEF, STUDY (definitions above).
- **Acceptance:** Predeclared coverage/error tolerances pass on held-out development replications or the arm is rejected. Persist poor-calibration results and exact thresholds before pilot selection.
- **Automated tests:** Known-noise coverage tests, correlated-error and misspecified models, zero-noise limiting behavior, posterior-reset replay.
- **Security and reliability:** Only purchased data informs checks; evaluator labels are a one-way audit output.
- **Effort / confidence:** 3–5 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-07 — Implement and distinguish acquisition objectives

- **Objective:** Isolate the effect of experiment selection.
- **Owner:** Research + Quality; primary lane RS2.
- **Scope:** Implement random, unweighted and posterior-weighted disagreement on a fixed action menu. Add model-EIG only after a bounded estimator has a demonstrated distinct ranking and calibrated bias/variance.
- **Out of scope:** Renaming monotone scalar Gaussian disagreement as an independent EIG advance or changing model pool per selector.
- **Prerequisites:** RA-06, RA-02, SP-05.b.
- **Required contracts:** ACQUISITION, BELIEF, STUDY (definitions above).
- **Acceptance:** Scalar constant-noise equivalence test passes. Vector/non-Gaussian examples document any distinction; same posterior/menu/noise/compute policy is shared; ties use a fixed rule.
- **Automated tests:** Analytic ranking/tie fixtures, categorical MI entropy-bound checks, MC error diagnostics, invalid candidate/timeout cases.
- **Security and reliability:** Cap likelihood/forward calls before evaluation; no silent negative-MI clipping or unmetered nested sampling.
- **Effort / confidence:** 2–4 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-07.b — Deliver the first offline fixed-pool comparison

- **Objective:** Produce a useful measured research result before provider profiles or hosted deployment.
- **Owner:** Quality + Research; primary lane QE.
- **Scope:** Run analytic common-prefix rankings and six frozen stationary spring development worlds, two policy seeds and three fixed-pool selectors:36 episodes,12 purchased slots including4 common calibrations,432 maximum slots. Use supported native LinearSpringModel candidates and the existing classical fitter/predictor/scorer; primary prediction is the declared MAP candidate, not an unrepresented mixture. Freeze pool, priors, likelihood, six world/noise identities, action menus and disjoint probes. Each arm uses only its own prefix.
- **Out of scope:** Richer DAG scoring, new symbolic adapters, provider calls, hosted deployment, population superiority, adaptation claims, official scores or new machines.
- **Prerequisites:** RA-06, RA-07, SP-04.e.
- **Required contracts:** STUDY, BELIEF, ACQUISITION, COST (definitions above).
- **Acceptance:** Within8 CPU-core-hours and1GiB new artifacts on the existing machine, independent scoring and world-paired descriptive results reproduce or a cap-limited incomplete result is recorded. Aggregate policy seeds within each world. Use actual native model/request hashes; no dummy linear identity or cross-arm data. No provider/network invocation.
- **Automated tests:** Analytic ranking equivalence, independent scoring, arm-history separation, absent-provider/network spy, cap/interrupt/replay and failure accounting.
- **Security and reliability:** Development-only12-slot budget; sealed labels cannot affect selection. No SP-18/20, RA-04.a/b or RA-09–12 dependency. Richer profiles separately bind actual MODEL identities to the reviewed SP-19/20 evaluator interface.
- **Effort / confidence:** 2–3 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-08 — Implement bounded LLM structure proposals

- **Objective:** Use the LLM for hypotheses while numerical methods fit parameters.
- **Owner:** Research + provider owner; primary lane RS1.
- **Scope:** Parse typed structures or operator-prior suggestions from bounded purchased-data context; numerically fit/evaluate through shared engines; cap prompts, proposals, retries, deduplication and retained rejection reasons. Start with recorded fixtures.
- **Out of scope:** LLM-generated production Python, unbounded self-improvement, access to evaluator truth or live paid calls in this PR.
- **Prerequisites:** RA-03.b, RA-02, SP-18.a, SP-18.b.
- **Required contracts:** PROPOSAL, MODEL, COST (definitions above).
- **Acceptance:** Recorded responses produce the same validated proposal pool and provenance; invalid text consumes the declared budget; numeric fitting remains separate.
- **Automated tests:** Prompt/data-boundary spies, malformed/oversize responses, duplicate structures, replay/cap exhaustion and model identity tests.
- **Security and reliability:** Treat outputs as untrusted; provider credentials stay in existing gateway; no network from model execution.
- **Effort / confidence:** 3–5 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-09 — Add measured change-adaptation policies

- **Objective:** Measure recovery when old explanations stop predicting.
- **Owner:** Research + Quality; primary lane RS1.
- **Scope:** Implement calibrated prequential change belief, fixed-pool reset/reweighting and gated open-pool proposal. Compare all-history, fixed-window, detector-reset and richer adaptation under the same purchased-data rules; persist pruned hypotheses and relearning costs.
- **Out of scope:** Gradual drift, recurrent changes or family switches in the first confirmatory study; oracle change-time input to real methods.
- **Prerequisites:** RA-06, RA-07, RA-08, SP-05.c.
- **Required contracts:** ADAPT, BELIEF, PROPOSAL (definitions above).
- **Acceptance:** Stationary false alarms and failure to recover are retained. Detection uses the prediction made before observing the next outcome. Expansion cannot read change time or held-out labels.
- **Automated tests:** Stationary/abrupt parameter/term fixtures, action-distribution shift, delayed/no detection, posterior collapse, resume across change.
- **Security and reliability:** No survivor averaging or hidden reset cost; stable slot accounting across simulation failures.
- **Effort / confidence:** 3–5 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-10 — Compose an MDA-inspired profile

- **Objective:** Test model-belief updates and hypothesis expansion as one declared system.
- **Owner:** Research + Quality; primary lane RS2.
- **Scope:** Compose existing bounded components into a named profile with weighted acquisition and predictive-check-triggered pool revision. Document every departure from the inspected MDA version.
- **Out of scope:** Claiming a faithful MDA reproduction without its solver/artifacts or adding latent filtering solely to match a paper.
- **Prerequisites:** RA-07, RA-08, RA-09, SP-20.d.
- **Required contracts:** STUDY, BELIEF, PROPOSAL, ADAPT (definitions above).
- **Acceptance:** Profile is executable from one manifest, matches information and budget controls, and reports approximation/departure tables.
- **Automated tests:** Replay identity, pool expansion/pruning and fixed-pool ablations, private-label injection rejection.
- **Security and reliability:** Respect common isolation/output limits and count every likelihood/proposal call.
- **Effort / confidence:** 2–4 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-11 — Compose an ACES-inspired profile

- **Objective:** Test LLM operator priors plus classical symbolic fitting.
- **Owner:** Research + Platform; primary lane RS2.
- **Scope:** Use LLM operator-prior proposals, bounded PySR fits and rollout-disagreement selection. Compare against PySR-only under the same grammar/search/measurement budgets and a fixed-selector proposal ablation.
- **Out of scope:** Claiming that the LLM directly fits equations, copying code without license clearance or using paper validation splits as independent evaluation.
- **Prerequisites:** RA-04.a, RA-07, RA-08, SP-20.d.
- **Required contracts:** STUDY, MODEL, PROPOSAL (definitions above).
- **Acceptance:** Profile records operator priors separately from fitted equations and matches the declared proposal/fitting budgets; paper-inspired status is explicit.
- **Automated tests:** Operator-prior application, forbidden operator rejection, optimizer timeout, fixed-selector and no-LLM control fixtures.
- **Security and reliability:** Licensed implementation only; isolate Julia runtime and validate every symbolic output.
- **Effort / confidence:** 2–4 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-12 — Compose an AutoSciLab-inspired profile

- **Objective:** Test hypothesis refinement and disambiguation separately.
- **Owner:** Research + Quality; primary lane RS2.
- **Scope:** Compose bounded hypothesis/search-region proposals, numerical refitting and disagreement/refinement choices; record bootstrap-confidence versus Bayesian-belief variants as different configurations.
- **Out of scope:** Claiming trajectory-domain or adaptation reproduction of the paper, unlicensed code reuse or post-hoc metric selection.
- **Prerequisites:** RA-06, RA-07, RA-08, SP-20.d.
- **Required contracts:** STUDY, BELIEF, PROPOSAL (definitions above).
- **Acceptance:** Replayable profile states its domain changes and confidence semantics; fixed-pool and no-refinement ablations use matched observations.
- **Automated tests:** Refinement/disambiguation decision fixtures, malformed search regions, bootstrap/posterior type separation and failure propagation.
- **Security and reliability:** Cap all hypothesis revisions and separate evaluator access; preserve rejected searches.
- **Effort / confidence:** 2–4 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-13.a — Run the bounded feasibility pilot

- **Objective:** Measure feasibility, uncertainty and real cost before a study freeze.
- **Owner:** Quality + Research; primary lane QE.
- **Scope:** Run the explicit capped development matrix over admitted profiles; validate paired accounting, timing, interruption and spend. Record exclusions in a revised frozen matrix before running. This one-world-per-stratum pilot is feasibility evidence only.
- **Out of scope:** Population sizing inference from one world per stratum, confirmatory test-set tuning, official sweep, deployment or any cap overrun.
- **Prerequisites:** RA-09, RA-10, RA-11, RA-12, SP-07.d, SP-18.d, RA_PILOT, RA-07.b.
- **Required contracts:** STUDY, COST, ADAPT (definitions above).
- **Acceptance:** All planned and terminated cells are accounted for, budget totals reconcile, information boundaries pass and exact reproduction is possible. No within-stratum population variance, power or world-level precision claim is made.
- **Automated tests:** Resume/retry/kill tests, deliberate missing predictions, cost reconciliation and independent report reproduction.
- **Security and reliability:** Stop at the first cap; preserve partial artifacts privately; no automatic purchase or larger-machine fallback.
- **Effort / confidence:** 3–4 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-13.b — Measure replicated-world precision and study size

- **Objective:** Estimate world-level uncertainty before freezing a confirmatory study.
- **Owner:** Quality + Research; primary lane QE.
- **Scope:** After a separate matrix/quote approval, run a preregistered pilot with multiple independent development worlds in each retained family/condition and paired policy seeds. Use measured variance, censoring and compute costs to size the official study; retain every failed cell.
- **Out of scope:** Unquoted runs, using policy seeds as independent worlds, tuning on sealed evaluation worlds or an automatic official sweep.
- **Prerequisites:** RA-13.a, RA_SIZING.
- **Required contracts:** STUDY, COST, ADAPT (definitions above).
- **Acceptance:** The independent-world sample and stopping rule are frozen before outcomes; interval/precision and prospective size estimates state their assumptions and uncertainty. Reviewer accepts the sizing evidence before RA-14.
- **Automated tests:** World-clustered bootstrap/aggregation fixtures, censored nonrecovery, missing-cell sensitivity, spend/cap/replay checks.
- **Security and reliability:** Number of worlds and compute cap require an explicit quote informed by feasibility; inadequate precision is a recorded failure, not a reason for unapproved retries.
- **Effort / confidence:** 3–4 engineer-days; low, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

### RA-14 — Freeze study and reforecast delivery

- **Objective:** Make a bounded evidence-backed execution decision.
- **Owner:** Project lead + Quality; primary lane TL.
- **Scope:** Freeze admitted arms, metrics, distributions, sealed-world access, paid estimate and runtime caps; map additional work into baseline releases only after replicated-world sizing, pilot throughput and staffing review.
- **Out of scope:** Automatic official sweep, a SOTA/novelty claim or preserving the old GA date as if added work were free.
- **Prerequisites:** RA-13.b, SP-21.c.
- **Required contracts:** STUDY, COST (definitions above).
- **Acceptance:** Independent research/security review signs the manifest and contamination audit; owner receives concrete study cost/release impact; official work still requires OFFICIAL_SWEEP.
- **Automated tests:** DAG/gate/manifest consistency checks, blinded report fixture, evaluator-access and reproducibility audit.
- **Security and reliability:** No release or benchmark claim without actual evidence; keep source/lock/artifacts and failed outcomes.
- **Effort / confidence:** 3–5 engineer-days; medium, plus shared 25% reserve.
- **Definition of done:** One independently reviewable PR; declared acceptance and meaningful automated tests pass at the exact source/config; peer review, schema/API documentation, safe metrics and failure evidence are recorded. Required hosted checks pass before merge. Runtime/paid/release gates are not implied by merging code.

## Highest risks and decisions

1. **Scientific identifiability:** different mechanisms can agree on observed trajectories. Use held-out action conditions, equivalent-model diagnostics and explicit unidentifiable outcomes.
2. **Posterior validity:** cheap evidence approximations can become confidently wrong under misspecification or differentiated noise. A tractable reference and predeclared predictive calibration are gates.
3. **Comparison confounding:** richer grammars, more proposal calls or evaluator feedback can create apparent selector gains. Keep A0/A1/B/C and the cost ledgers separate.
4. **Numerical/search cost:** SMC, repeated ODE rollouts and Julia search can dominate experiment cost. Measure and stop under caps; no training-GPU requirement does not mean cheap execution.
5. **Availability and license gaps:** MDA solver availability and ACES/AutoSciLab code grants may prevent faithful reproduction. Keep paper-inspired implementations explicit or exclude the arm.
6. **Schedule capacity:** this adds 60–97.5 estimated engineering days including reserve, with real baseline prerequisites and reviewer contention. Reforecast after E0 and the pilot.

The owner must decide whether to activate this extension, which bounded pilot matrix/cap to approve after a quote, and whether accepted evidence should move any release target. No runtime task, official study, new infrastructure or paid provider call is authorized by this planning amendment alone.

## Review and maintenance

Lead checks all dependency IDs and cycles against the canonical baseline, plus the extension gates; Quality or Research independently reviews the scientific design and arithmetic. Record exact reviewed commit and CI evidence in the assignment log. Amend this record and the canonical roadmap, benchmark and backlog together if scope, budgets or conclusions change. A written plan is not production readiness or research evidence.
