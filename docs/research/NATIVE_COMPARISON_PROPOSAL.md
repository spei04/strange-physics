# Proposed native spring comparison path

Status: **proposal only — not approved, activated or implemented**. Prepared 2026-10-20 from the accepted repository and independent Research/Quality dependency audits. The authoritative execution graph and RA_EXEC remain unchanged. This document makes the decision reviewable; it grants no run or infrastructure permission.

## Decision requested

Approve five native PR tasks and replace only the RA-06/RA-07 prerequisites of RA-07.b with RA-N03/RA-N04. Keep RA-01 and RA-02 in full, preserve all broader tasks, and use an additive native prediction/scoring profile instead of weakening existing contracts. Separately activate RA_EXEC before implementation; any approval should explicitly identify whether it also authorizes the bounded local comparison below. Provider, paid, official-study and release gates remain separate.

This path uses the grid reference as the common online inference engine for three selectors. Laplace is a required, separately calibrated approximation diagnostic. The proposed action bank has128 actions; the proposed discrepancy sensitivity set is half/base/double, all strictly positive. Exact nodes, priors, likelihood, numerical scales and tolerances must be preregistered and independently accepted before measurements; they are not guessed here.

## Why the current graph needs a decision

The planned36-episode comparison has no WEB1, hosted deployment or provider prerequisite. Its current29-node closure nevertheless includes symbolic execution, all-family numerical calibration, sparse/bootstrap work and executable-predictor contracts. Removing those dependencies without replacement evidence would be a waiver. The native tasks below retain their relevant controls and leave the broader tasks uncompleted.

There is also a concrete compatibility gap: LinearSpringModel permits a producer identity, but SpringPredictionConfig and predict_linear_spring accept only the paired-Simpson producer and its exact fit-config hash. Fixed-grid candidates cannot honestly reuse those identities. The independent evaluator accepts actual model/request/response identities; existing workflow preparation/scoring wrappers additionally require a SpringFitArtifact. RA-N01 therefore adds a native profile and narrow journal/scoring adapter. It does not forge a fit artifact or alter existing SCI/v1 behavior.

Source: [prediction contract](../../src/strange_physics/prediction_contracts.py), [predictor](../../src/strange_physics/prediction.py), [independent evaluator](../../src/strange_physics/evaluation.py), [workflow](../../src/strange_physics/scientific_workflow.py), and [method decision record](2026-10-19-METHOD_DECISIONS.md).

## Proposed PR tasks

### RA-N01 — Bind native spring candidates to prediction and independent scoring

- **Objective:** Give fixed-grid candidates honest, independently scoreable native identities.
- **Implementation scope:** Add bounded pool/config/candidate receipt and prediction types. Produce real LinearSpringModel artifacts from each arm’s actual purchased ObservationBundle with a distinct native producer/config, full-prefix hash, through_index and completed-record selection. Separate the common immutable pool hash from prefix-dependent model hashes. Add a separate prediction profile that shares the reviewed analytic kernel and accepted domain/work limits while preserving existing v1 bytes and rejection behavior. Add a journal/prefix/model/config/protocol/submission adapter into the unchanged independent evaluator, with disjoint probes. Keep the classical fitter as an honestly labeled same-prefix diagnostic.
- **Out of scope:** No new law families, symbolic DAGs, executable models, mixtures under linear IDs, hosted registration, CORE/SCI changes, broadened v1 predictor acceptance, fake SpringFitArtifact or paired-Simpson provenance.
- **Prerequisites:** RA-01, SP-04.e.
- **Contracts:** MODEL, BELIEF, SCI, STUDY, COST.
- **Acceptance criteria:** Native candidates predict and score with their actual hashes; original v1 rejects their distinct producer/config. Pool identity is shared while each model binds its own arm’s prefix. No completed observations yields a typed failure without invented indices. A primary MAP output names one actual candidate. Preparation rejects changed raw journal or canonical prefix/model/config, wrong requests/responses/protocols and overlapping probes. Missing/invalid predictions and evaluator arithmetic failure remain distinct.
- **Required automated tests:** Producer/config rejection; changed-prefix/hash and signed-zero cases; missing/failed selections; analytic domain/boundary cases; poisoned private inputs; raw/canonical journal and request/probe joins; disjointness; complete failure counts; old/new profile separation.
- **Security and reliability:** Strict byte/count/domain/compute bounds; no eval, dynamic imports, plugins or network; private world/reference labels cannot enter public candidate inputs. Local conformance is not hostile-process isolation.
- **Effort / confidence:** 3–4 engineer-days; medium.
- **Responsible role:** Platform + Research; independent Quality review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

### RA-N02.a — Compute the native finite-grid reference

- **Objective:** Produce reproducible bounded spring-parameter beliefs from purchased observations.
- **Implementation scope:** Freeze coefficient nodes/cells, prior/reference measure, likelihood features/covariance assumptions and strictly positive numerical-discrepancy policy. Enumerate all nodes for stable normalized weights and evidence, recording actual pool/config/prefix/candidate identities, usable records, failed observations and every forward/likelihood cost. Specify bounded scalar prior/likelihood functions for the later approximation. Grid is the common online engine for all three selectors.
- **Out of scope:** No Laplace, SMC, symbolic models, bootstrap, pool search/growth, evaluator feedback, BIC probabilities or claim of exact continuous inference.
- **Prerequisites:** RA-N01, RA-02.
- **Contracts:** BELIEF, MODEL, STUDY, COST.
- **Acceptance criteria:** Independent finite-sum references match preregistered tolerances. Exact means normalization of the declared finite grid; numerical and discretization errors remain separate. Every candidate and failed purchased record stays accounted for. No usable observations or nonfinite/unnormalizable weights yields an explicit failure. All arms use the same definitions and only their own prefix.
- **Required automated tests:** High-precision finite sums and tractable analytic cases; refinement; extreme log weights; prior/discrepancy sensitivity; ordering and failed-record accounting; deterministic replay; cross-arm poisoning; resource exhaustion.
- **Security and reliability:** Bound nodes, bytes and calls before work; no evaluator input, unmetered retry, clipping or silent candidate removal. Preserve source, prior, likelihood and conditioning identities.
- **Effort / confidence:** 2–3 engineer-days; low.
- **Responsible role:** Research; independent Quality and Platform review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

### RA-N02.b — Add and measure the declared native Laplace approximation

- **Objective:** Quantify one approximation against the accepted finite-grid reference.
- **Implementation scope:** Implement a bounded Laplace approximation to the declared scalar log posterior, with explicit support/boundary treatment and conditioning diagnostics. Evaluate or project it onto the same declared cells/nodes and prior/reference measure. Compute approximation posterior weights independently; they are not forced to equal grid weights. Persist actual inputs, method/config identity, approximation/reference error, failures and costs. Laplace is a separately validated diagnostic, not a fourth selector.
- **Out of scope:** No additional inference backend, approximation-selected grid/prior, unrecorded fallback, online-engine substitution or exact-continuous-inference claim.
- **Prerequisites:** RA-N02.a.
- **Contracts:** BELIEF, STUDY, COST.
- **Acceptance criteria:** Independent tractable cases meet preregistered tolerances. Boundary modes, singular/nonpositive curvature, numerical collapse and unsupported cases fail explicitly. Discretization error and approximation error remain distinct. Grid remains the common online engine unless separately amended.
- **Required automated tests:** Independent quadratic posterior and bounded/truncated cases; boundary, multimodal and misspecified cases; Hessian degeneracy; same-cell comparisons; exact-input mismatch; reproducibility and call-budget exhaustion.
- **Security and reliability:** Cap optimization/derivative evaluations and outputs. Do not clip failures into valid estimates, access hidden data or switch approximation silently.
- **Effort / confidence:** 2–3 engineer-days; low.
- **Responsible role:** Research; independent Quality and Platform review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

### RA-N03 — Calibrate native beliefs and numerical-discrepancy sensitivity

- **Objective:** Retain the scientific safeguards otherwise supplied by the broader calibration task.
- **Implementation scope:** Perform independent development calibration and prequential residual/predictive checks with tolerances fixed before outcomes. Justify positive numerical-discrepancy scale using accepted solver/analytic error evidence plus declared residual/correlation assumptions. Freeze a bounded sensitivity set; proposed half/base/double scales must all remain positive. Compare grid and Laplace errors, boundary/misspecification behavior and rankings on disjoint development fixtures. Labels flow only into audit output. Sensitivity over fixed purchased histories is diagnostic, not an uncounted adaptive sweep.
- **Out of scope:** No tuning on the six measured worlds or held-out probes, universal coverage, reinterpretation of zero observation noise as discrepancy, silent domain widening or outcome-driven filtering.
- **Prerequisites:** RA-N02.b.
- **Contracts:** BELIEF, STUDY, COST.
- **Acceptance criteria:** Predeclared native-domain reference/approximation tolerances and applicable development checks pass, or the profile is rejected and comparison remains blocked. Preserve poor calibration, failures, prior/scale sensitivity and pass/fail/incomplete eligibility. Weights are approximate model-belief weights, not calibrated observation-noise probabilities. Domain/approximation changes require a recorded amendment.
- **Required automated tests:** Separately labeled synthetic-noise sanity cases; correlated discrepancy, weak excitation, boundary coefficients, misspecification, zero-noise limits with positive discrepancy; prequential ordering; replay/reset; evaluator-feedback rejection.
- **Security and reliability:** Calibration audit cannot write selector state. Bound reference/sensitivity work and outputs, record costs and all outcomes, prohibit silent redraws or successful-only summaries.
- **Effort / confidence:** 3–5 engineer-days; low.
- **Responsible role:** Quality + Research; Platform boundary review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

### RA-N04 — Freeze the native action menu and three acquisition policies

- **Objective:** Isolate experiment selection under common model and inference settings.
- **Implementation scope:** Freeze a proposed seeded 128-action bank and four calibration actions within accepted purchased-action bounds, with immutable IDs and duplicate/repetition rules. Implement random, uniform-candidate disagreement and posterior-weighted disagreement with fixed observable vector/scaling, reduction and ties. Common-prefix rankings share identical pool/prior/likelihood/posterior/menu. Online arms share definitions and use only their own prefixes. All outputs use the same declared MAP rule. Retain pending/failed action identities and slot/call accounting.
- **Out of scope:** No full-family generator, bootstrap, LLM selector, EIG arm, evaluator-guided menu, adaptive pool or easier-menu fallback after failure.
- **Prerequisites:** RA-N02.a.
- **Contracts:** ACQUISITION, BELIEF, STUDY, COST.
- **Acceptance criteria:** Common-prefix identities and ties are deterministic. Random selects only eligible declared actions; weighted/uniform disagreement match hand calculations. Invalid/nonfinite candidates or scores follow the preregistered whole-selection failure policy, without silent dropping. Each arm separately purchases four calibration plus eight remaining slots. Demonstrate scalar constant-noise monotone information-surrogate equivalence without claiming a new EIG method.
- **Required automated tests:** Ranking/ties; permutation/identity integrity; shared menu and divergent own histories; cross-arm poisoning; four-plus-eight accounting; invalid candidates and cap exhaustion; absent provider/network invocation; deterministic replay.
- **Security and reliability:** Bound bank/scoring calls, forbid evaluator feedback and unmetered retries, and fail closed on inconsistent state.
- **Effort / confidence:** 2–4 engineer-days; medium.
- **Responsible role:** Research + Quality; Platform contract review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

## Dependency review and scheduling

Proposed edges:

| Task | Prerequisites |
| --- | --- |
| RA-N01 | RA-01, SP-04.e |
| RA-N02.a | RA-N01, RA-02 |
| RA-N02.b | RA-N02.a |
| RA-N03 | RA-N02.b |
| RA-N04 | RA-N02.a |
| RA-07.b | RA-N03, RA-N04, SP-04.e; replaces RA-06/RA-07 only |

The proposed graph is acyclic and resolves every ID. RA-07.b has21 nodes:12 accepted prerequisites (including APPROVAL), eight proposed research tasks and pending RA_EXEC. The extension would have23 tasks,60 task-dependency edges and nine fixed gate edges:69 fixed edges plus the unchanged six conditional edges. The current published graph remains18 tasks,62 fixed plus six conditional edges. The approved baseline168-task/369-edge/ten-gate graph is unchanged.

After RA_EXEC, RA-01 is first. RA-N01 and RA-02 can proceed in parallel after RA-01; RA-N02.a joins them. RA-N02.b and RA-N04 can proceed in parallel; RA-N03 follows RA-N02.b; RA-07.b joins RA-N03/N04 and the accepted SDK workflow. This is dependency concurrency, not a promise of simultaneous staff availability.

The five native tasks add12–19 engineer-days. Including RA-01, RA-02 and RA-07.b, the unfinished path is19–29 days, or23.75–36.25 with25% reserve. These are engineering effort estimates. Do not subtract speculative reuse from broader tasks or alter the conditional GA forecast. If a task grows beyond a small independently reviewable PR, split it before assignment.

Integration gates:

1. RA-01: source/license/recipe go/no-go evidence accepted before code reuse.
2. RA-N01 + RA-02: native producer/predictor/scorer identity round trip and complete manifest/cost ledger accepted.
3. RA-N02.a/b: independent reference and approximation tests accepted; no hidden-data or provenance shortcut.
4. RA-N03 + RA-N04: calibration/sensitivity passes, common menu/ranking/accounting/arm isolation is accepted, and the full study manifest is frozen.
5. RA-07.b: independently scored paired descriptive results reproduce within the caps, or every failed/incomplete cell and stop reason is retained.

Low-confidence numerical tasks may reject the profile. Contingency is explicit failure and a reviewed narrower domain or revised approximation, not silent fallback, outcome-driven filtering or extra uncounted experiments. Re-estimate after each gate. Until approval and staffing are known, no calendar dates or day-by-day execution promises are assigned to this new scope.

## Unchanged bounded comparison

Six frozen stationary spring development worlds × two policy seeds × three selectors =36 episodes. Each arm buys12 slots including four common calibrations, at most432 purchased slots. Worlds remain one-particle, fixed-anchor, zero-cubic and zero-observation-noise within accepted scorer bounds. Primary output is one actual MAP native candidate, never a mixture under a linear ID.

Freeze pool and producer/config identities, priors/likelihood/discrepancy policy, all six world identities, seeds, menus, disjoint scoring probes, tie/failure/termination policies, budget counters and output records before measurements. The pool definition is common; every serialized candidate and posterior binds its own arm’s purchased prefix. Failed calibrations remain purchased failures. If no usable observations remain, record a typed failure instead of inventing record indices.

Use the existing machine, at most8 CPU-core-hours and1GiB new artifacts, with zero network, provider calls or provisioning. Count ranking, reference, sensitivity, prediction, scoring, retries and failures in the declared comparison cost; no uncounted second sweep. Aggregate policy seeds within each world and report world-paired descriptive outcomes with all failures/incomplete cells. No population-superiority, adaptation or official-score claim.

## Current assignment

Quality independently accepted this as a planning proposal at ad89f8d: source compatibility, resolved acyclic dependencies, closure counts and effort totals agree. The active graphs and gates are unchanged. WEB1 runtime is independently reviewed; Research completes final source checks/evidence and the lead integrates. Platform reviews integration consistency; Quality has prepared SP-01.e/#98, with no source authoring before exact WEB1 acceptance. No native implementation task or experiment has started. RA_EXEC remains pending.
