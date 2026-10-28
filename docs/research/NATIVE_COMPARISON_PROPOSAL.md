# Native spring comparison execution plan

**Current checkpoint (2026-10-28):** The finite-log-weight normalizer (#129) remains delivered through PR #130/main 620c0f0. Endpoint checkpoint #131 has independently accepted focused validation at 32a9f7d: all eight commands passed, including 32 tests in 13.55 seconds, 1,547 external schema checks and exact 96-file package parity. Earlier style/type-check failures remain retained. [PR #132](https://github.com/spei04/strange-physics/pull/132) is open with CI queued; main/candidate delivery is pending. RA-N02.a remains in progress, the scientific profile is unaccepted, and full-study admission stays closed. [Current evidence and assignments](../EXECUTION_LOG.md#2026-10-28--endpoint-focused-validation-accepted-hosted-delivery-pending).

Status: **owner-approved for scoped implementation and the bounded comparison on2026-10-21**. Accepted plan source33ddfbf74837dde29e0f1db3b1b4263e7031ddc2, PR #100. The reviewed native dependency amendment and scoped RA_EXEC are active; scientific/implementation entry gates and all caps remain. See [approval record](APPROVALS.md#native-comparison-2026-10-21).

## Approved decision

The owner approved five native PR tasks and the replacement of only the RA-06/RA-07 prerequisites of RA-07.b with RA-N03/RA-N04. Keep RA-01 and RA-02 in full, preserve all broader tasks, and use an additive native prediction/scoring profile instead of weakening existing contracts. RA_EXEC is accepted for the eight enumerated units in the approval record, including the bounded local comparison below after its prerequisite gates. Provider, paid, official-study and release gates remain separate.

This path uses the grid reference as the common online inference engine for three selectors. The reviewed sequencing recommendation places the first comparison after grid calibration and moves the required Laplace diagnostic and its approximation-versus-grid audit to a later unit. This preserves the full programme while separating the first grid-only result from completion of the grid-plus-Laplace programme. The proposed action bank has128 actions; the proposed discrepancy sensitivity set is half/base/double, all strictly positive. Exact nodes, priors, likelihood, numerical scales and tolerances must be preregistered and independently accepted before measurements; they are not guessed here.

The reason for this order is to hold inference constant while testing experiment selection, then audit Laplace against accepted frozen development fixtures. Laplace remains required. Shared interface preparation and analytic unit design can overlap when their inputs are stable; comparative acceptance still requires those fixtures. The proposed numerical grid profile is not accepted: exact finite-grid normalization alone does not prove useful uncertainty or predictive resolution. If a suitable reference cannot fit the accepted limits, revisit the inference design before any comparison. No dependency, cap or estimate changes here.

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
- **Implementation scope:** Implement a bounded Laplace approximation to the declared scalar log posterior, with explicit support/boundary treatment and conditioning diagnostics. Evaluate or project it onto the same declared cells/nodes and prior/reference measure. Compute approximation posterior weights independently; they are not forced to equal grid weights. Persist actual inputs, method/config identity, approximation/reference error, failures and costs. Laplace is a separately validated diagnostic, not a fourth selector. After the first grid-only result, consume the accepted, frozen RA-N03 development fixtures and perform the transferred Laplace-versus-grid calibration, predictive, ranking, boundary and misspecification audit. Preserve fixture identities and audit-only labels; later findings cannot retroactively tune the first comparison.
- **Out of scope:** No additional inference backend, approximation-selected grid/prior, unrecorded fallback, online-engine substitution or exact-continuous-inference claim.
- **Prerequisites:** RA-N03.
- **Contracts:** BELIEF, STUDY, COST.
- **Acceptance criteria:** Independent tractable cases meet preregistered tolerances. Boundary modes, singular/nonpositive curvature, numerical collapse and unsupported cases fail explicitly. Discretization error and approximation error remain distinct. Grid remains the common online engine unless separately amended. Approximation-versus-grid tolerances, predictions and acquisition rankings are independently assessed on those fixtures with all failures and costs. No Laplace validity or speedup claim precedes this acceptance.
- **Required automated tests:** Independent quadratic posterior and bounded/truncated cases; boundary, multimodal and misspecified cases; Hessian degeneracy; same-cell comparisons; exact-input mismatch; reproducibility and call-budget exhaustion. Frozen fixture identity and label isolation; posterior/predictive/ranking comparisons; transferred audit failures; rejection of retroactive comparison tuning.
- **Security and reliability:** Cap optimization/derivative evaluations and outputs. Do not clip failures into valid estimates, access hidden data or switch approximation silently.
- **Effort / confidence:** 3–5 engineer-days; low.
- **Responsible role:** Research; independent Quality and Platform review.
- **Definition of done:** One independently reviewable PR with exact source/config identities, meaningful acceptance and failure tests, peer review, schemas/examples and documentation, configured formatting/type/security/package checks, and required PR/main CI. Merging code does not waive study, paid, official or release gates.

The revised 3–5-day estimate includes 1–1.5 days of implementation, 1–1.5 days of independent reference tests, 0.5–1 day of transferred grid audit, and 0.5–1 day of review, integration and documentation. With 25% reserve: 3.75–6.25 days. The former 2–3-day allowance is historical. Re-estimate before assignment; split before assignment if delivery exceeds five days. Numerical conditioning or inadequate reference cases use contingency or require a reviewed rescope, not a silent backend replacement.

### RA-N03 — Calibrate native beliefs and numerical-discrepancy sensitivity

- **Objective:** Retain the scientific safeguards otherwise supplied by the broader calibration task.
- **Implementation scope:** Perform independent development calibration and prequential residual/predictive checks with tolerances fixed before outcomes. Justify positive numerical-discrepancy scale using accepted solver/analytic error evidence plus declared residual/correlation assumptions. Freeze a bounded sensitivity set; proposed half/base/double scales must all remain positive. Validate grid finite-sum/analytic references, refinement, predictive behavior, boundary/misspecification behavior and rankings on disjoint development fixtures. Freeze accepted fixture identities for the later RA-N02.b approximation audit; Laplace-specific comparison moves there. Labels flow only into audit output. Sensitivity over fixed purchased histories is diagnostic, not an uncounted adaptive sweep.
- **Out of scope:** No tuning on the six measured worlds or held-out probes, universal coverage, reinterpretation of zero observation noise as discrepancy, silent domain widening or outcome-driven filtering.
- **Prerequisites:** RA-N02.a.
- **Contracts:** BELIEF, STUDY, COST.
- **Acceptance criteria:** Predeclared native-domain grid-reference tolerances and applicable development checks pass, or the profile is rejected and comparison remains blocked. Preserve poor calibration, failures, prior/scale sensitivity and pass/fail/incomplete eligibility. Weights are approximate model-belief weights, not calibrated observation-noise probabilities. Domain/inference changes require a recorded amendment.
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
| RA-N02.b | RA-N03; later approximation implementation and transferred audit |
| RA-N03 | RA-N02.a; grid calibration required before first result |
| RA-N04 | RA-N02.a |
| RA-07.b | RA-N03, RA-N04, SP-04.e; replaces RA-06/RA-07 only |

The activated native graph is acyclic and resolves every ID. At the approved baseline after RA-01 acceptance, RA-07.b had20 nodes:14 accepted prerequisites (including APPROVAL, scoped RA_EXEC and RA-01) and six then-unfinished research tasks: RA-02, RA-N01, RA-N02.a, RA-N03, RA-N04 and RA-07.b. RA-02 and RA-N01 are now accepted for the bounded native implementation; the four later tasks remain unfinished. Only Laplace leaves the first-result closure. The extension remains23 tasks,60 task-dependency edges and nine fixed gate edges:69 fixed edges plus six unchanged conditional edges. The prior18-task/62-fixed-edge graph is historical; the approved baseline168-task/369-edge/ten-gate graph is unchanged.

With scoped RA_EXEC accepted, RA-01 is first. RA-N01 and RA-02 can proceed in parallel after RA-01; RA-N02.a joins them. RA-N03 and RA-N04 can proceed in parallel after RA-N02.a; RA-07.b joins RA-N03/N04 and the accepted SDK workflow. Schedule RA-N02.b after the first result, consuming accepted frozen RA-N03 fixtures. Those fixtures remain disjoint from the six comparison worlds and scoring probes; later Laplace findings cannot retroactively tune the first comparison. This is dependency concurrency, not a promise of simultaneous staff availability.

The four native tasks on the first-result path require 10–16 engineer-days. Including RA-01, RA-02 and RA-07.b, that path is provisionally 17–26 days, or 21.25–32.5 with 25% reserve. N03 retains its full 3–5-day allowance. The later Laplace implementation plus transferred audit is 3–5 days, or 3.75–6.25 with reserve. The five native tasks therefore total 13–21 days, or 20–31 when including RA-01, RA-02 and RA-07.b. These arithmetic totals cover this proposal, not the broader research programme; they are engineering effort, not calendar duration. Historical 12–19 / 19–29 estimates predate the revised audit allocation. Full-programme scope and the conditional GA forecast are unchanged; no total-programme saving is established. Re-estimate at each gate and before later assignment. Split any task that exceeds a small independently reviewable PR.

Integration gates:

1. RA-01: source/license/recipe go/no-go evidence accepted before code reuse.
2. RA-N01 + RA-02: native producer/predictor/scorer identity round trip and complete manifest/cost ledger accepted.
3. RA-N02.a: independent finite-sum/analytic and refinement reference checks accepted for the grid-only first result; no hidden-data or provenance shortcut. RA-N02.b acceptance is required later before any Laplace validity or speedup claim.
4. RA-N03 + RA-N04: calibration/sensitivity passes, common menu/ranking/accounting/arm isolation is accepted, and the full study manifest is frozen.
5. RA-07.b: independently scored paired descriptive results reproduce within the caps, or every failed/incomplete cell and stop reason is retained.

Low-confidence numerical tasks may reject the profile. Contingency is explicit failure and a reviewed narrower domain or revised approximation, not silent fallback, outcome-driven filtering or extra uncounted experiments. Re-estimate after each gate. Execution uses the existing lead plus three-engineer team. Engineering-day estimates are not elapsed-time promises; re-estimate after each accepted unit.

## Unchanged bounded comparison

Six frozen stationary spring development worlds × two policy seeds × three selectors =36 episodes. Each arm buys12 slots including four common calibrations, at most432 purchased slots. Worlds remain one-particle, fixed-anchor, zero-cubic and zero-observation-noise within accepted scorer bounds. Primary output is one actual MAP native candidate, never a mixture under a linear ID.

Freeze pool and producer/config identities, priors/likelihood/discrepancy policy, all six world identities, seeds, menus, disjoint scoring probes, tie/failure/termination policies, budget counters and output records before measurements. The pool definition is common; every serialized candidate and posterior binds its own arm’s purchased prefix. Failed calibrations remain purchased failures. If no usable observations remain, record a typed failure instead of inventing record indices.

Use the existing machine, at most8 CPU-core-hours and1GiB new artifacts, with zero network, provider calls or provisioning. Count ranking, reference, sensitivity, prediction, scoring, retries and failures in the declared comparison cost; no uncounted second sweep. Aggregate policy seeds within each world and report world-paired descriptive outcomes with all failures/incomplete cells. Report only the finite-grid development comparison. No exact continuous-posterior, calibrated observation-noise probability, Laplace validity/speedup, population-superiority, adaptation or official-score claim.

## Current assignment

PR #128/main e587f47 and unpublished candidate 12758851671 are accepted, including all five main jobs, 4,502 tests on both supported Python runtimes and exact 92-file archive/source verification. Quality completed candidate verification; Platform completed independent delivery and bounded parent review; Lead records RA-02/#105 and RA-N01/#106 acceptance. Source-specific selected-run evidence and failed attempts remain separate in the [delivery record](../EXECUTION_LOG.md#2026-10-27--publisher-handoff-delivered-and-native-parents-accepted).

Research delivered the bounded finite-log-weight normalizer subunit (#129) through PR #130/main 620c0f0; independent review and exact main/candidate verification are accepted. RA-N02.a remains in progress. Parallel Laplace analytic-case and finite-reference V2 designs are accepted as preparation only; source implementation, preallocation/intermediate/GCD bounds and practical CPU fit remain unproved, with no deep-tail coverage. Shared scientific-profile and finite-resolution acceptance remain next; Laplace reference implementation is parallel preparation, not a new prerequisite. Research completed restricted endpoint-x source, reference and count work for #131. Focused validation at 32a9f7d is accepted by both independent reviewers: all eight commands, 32 cases and exact 96-file package parity passed. The earlier style/type-check failures remain retained. The narrow-grid counterexample confirms that normalization does not establish finite-resolution adequacy; the scientific profile remains unaccepted. Lead coordinates PR/main/candidate delivery, which is still pending. The provisional 2–4-engineer-day estimate and low confidence are unchanged. Existing owner-approved implementation remains in force. The proposed scientific grid, prior, likelihood, covariance, discrepancy and tolerances remain unaccepted. Full-study global authority/allocation and resource fit remain required before RA-07.b; the retained 36-publication reservation floor alone is 1,168 MiB, above the 1 GiB cap.

RA-01 and SP-04.e remain accepted. The earlier 15–23-engineer-day remainder is historical, not a current forecast; the approved 17–26-day full-path baseline includes completed work. Re-estimate upcoming numerical and allocation work from concrete scope rather than infer a completion date. VAL1 draft PR #101 remains deferred. No comparison has run; broader/paid/official/release gates remain separate.

## 2026-10-24 — Native stages independently reviewed; trust-store repair delivered

Measured preparation/prediction/scoring is delivered in [PR #120](https://github.com/spei04/strange-physics/pull/120), main ff3d47e. All five protected-main jobs passed, with 4,240 tests on each Python 3.12/3.14 runtime; candidate12561739881 matched all 80 package files and both reviewed archives. The bounded synthetic fixture remains conformance evidence. The next freeze/Journal/classical design passed independent review, but its runtime admission is unproved. Quality now implements charged freeze/Journal binding; Platform independently reviews boundaries, Research reviews scientific semantics, and Lead owns assignment and delivery. GitHub alert1 was automatically marked fixed at 20:54:23 UTC on 2026-10-24; no dismissal or audit suppression occurred. Parent issues105/106 and full-study admission remain open. See the [current assignment board](../EXECUTION_LOG.md#current-assignment-board) and [source-specific evidence](../EXECUTION_LOG.md#2026-10-24--measured-native-stages-delivered).

## 2026-10-24 — Charged freeze and Journal-bound comparison candidates

Charged same-store freezing and Journal-bound comparison candidates are source-accepted at 27081a7. The synthetic chain executes freeze, candidate production and two paid recoveries, retaining original results without producer reruns. All 4,263 tests passed on production-equivalent 8545a18; the final test-only refinement passed its targeted regression and guard-removal sensitivity check. Both independent runtime reviews passed. Normal PR/main CI and exact candidate verification remain pending. Classical dispatch, public purchased simulation, publisher handoff and full-study admission remain open; RA-02/#105 and RA-N01/#106 stay in progress.

## 2026-10-24 — Measured freeze and Journal candidates delivered

Charged same-store freeze and Journal-bound comparison candidates are delivered in [PR #121](https://github.com/spei04/strange-physics/pull/121), main 1474e57. All five main jobs passed; both Python 3.12/3.14 suites passed 4,263 tests. Candidate 12577366173 matched all 83 package files and both reviewed author archives. The bounded four-call synthetic chain proves freeze, candidate production and paid original-byte recovery within its declared scope. The next fixed classical unit is prepared; measured public purchases, publisher handoff, full-study admission and explicit parent audit remain open. RA-02/#105 and RA-N01/#106 stay in progress; no research comparison has run.

## 2026-10-24 — Fixed classical execution assigned

Quality now implements the fixed Journal-bound classical diagnostic in the released identity checkout, from accepted main1474e57. Platform independently reviews accounting, boundaries and recovery; Research reviews retained-material and scientific semantics; Lead owns integration and progress. The fresh fixture must freeze actual typed configs before work and demonstrate the existing conditional six-call envelope (278,020,096 bytes / 462 CPU seconds). Classical work is reserved on admission; prior unresolved holds remain. Public purchased simulation, publisher handoff, feasible full-study allocation and explicit parent audit remain open. RA-02/#105 and RA-N01/#106 remain in progress; no research comparison has started.

## 2026-10-24 — Classical six-call author checkpoint

The first fixed classical implementation checkpoint is 0cbff3b. Its bounded synthetic fixture passed freeze, candidate production, classical execution and three paid recoveries: 27 ledger records, 14 unresolved holds, a 28,608-byte ledger and 90,112-byte database. The original 12-row Journal prefix retains 11 successful experiments and one explicit failure; absent native selection permits an independent classical result. Both static reviews found no source blocker. Failure coverage, independent runtime acceptance, configured checks and PR/main delivery remain pending. The 278,020,096-byte / 462-CPU-second envelope describes this finite fixture; it does not admit the full study. Parent issues105/106 remain open.

## 2026-10-24 — Classical execution independently reviewed

The fixed Journal-bound classical implementation at 28431b6 has passed review. All 4,283 tests passed in 926.83 seconds on 11aada9; the final change affects documentation only. Configured lint/type checks, 1,522 schema cases, security checks, package checks and installed-CLI checks passed. The fresh six-call synthetic fixture retains 27 ledger records and 14 unresolved holds within its declared 278,020,096-byte / 462-CPU-second envelope. Research passed seven independent cases with nine public calls and two classical children; Platform passed six structural cases and two guard-removal checks using an explicitly labeled retained-result feeder. Paid recovery preserves original results without numerical reruns. Normal PR/main CI and exact candidate verification remain pending. Public purchased simulation, publisher handoff, feasible full-study allocation and explicit parent audit remain open; no research comparison has run.

## 2026-10-24 — Classical merged; purchase work split

The fixed Journal-bound classical unit merged in [PR #122](https://github.com/spei04/strange-physics/pull/122) as main 1bc87e9 after required PR checks passed. Its tree equals reviewed head 58ce8bf. Protected-main run 40156370203 and exact candidate verification remain pending; this is not a release or a completed research study. Parent issues #105 and #106 remain open.

The next purchase design passed two independent source reviews at revision 3. It preserves immutable purchase identity across retries, separately binds the current paid attempt, and distinguishes new reconciliation evidence from an original measured receipt. Both fixed Journal processes require a 128 KiB file limit before opening SQLite; oversized rollback files must fail with unknown costs retained. The conditional 16-call specimen reserves 589,561,856 bytes and 708 CPU-seconds, including setup, recovery and publication protection. Runtime enforcement and usability remain unproved.

Implementation is split into two sequential PRs: bounded Journal support and capture holding first; then the measured purchase, same-slot retry, paid replay and reconciliation flow. Their provisional estimate is 6–11 engineer-days including review/repair, with moderate confidence. This decomposes remaining parent work; it is not an addition to the historical task estimates. The earlier 15–23-day remainder and approved 17–26-day full path are retained as historical baselines. A current total requires bottom-up re-estimation, including still-open publisher handoff, full-study capacity and parent audit. No new completion date, approval, scientific scope or allocation is established.

## 2026-10-24 — Measured classical delivery accepted

[PR #122](https://github.com/spei04/strange-physics/pull/122) is delivered as main 1bc87e9. All five jobs in [protected-main run 40156370203](https://github.com/spei04/strange-physics/actions/runs/40156370203) passed; Python 3.12 and 3.14 each passed 4,283 tests (477.84 and 545.72 seconds). Unpublished candidate 12584546922 matched all 83 package files and both reviewed author archives. Its 494,358-byte ZIP has SHA-256 ba042b3e3ccf78a1179a29be978e1dd6093fd5c74570b7f5289d7abd0dbf97e4. The exact-source review also checked 13 hosted interpreter-copy observations and both certificate-store guards. Exported requirements bytes were not independently recomputed; copied interpreters still use base standard/shared libraries.

Lead independently read and rehashed the final 14-file/nine-reference evidence index and its 12-record monitor index. The accepted six-call synthetic scope and retained failure/unknown costs remain unchanged. This delivery does not run the research comparison or establish full-study capacity. RA-02/#105 and RA-N01/#106 remain open.

Next, Quality owns the queued bounded Journal/capture-holder PR, followed by complete measured-purchase integration after that prerequisite is accepted. Platform reviews resource limits, process lifetime and durability; Research reviews scientific identities, failure semantics and progress consistency; Lead owns integration and delivery. The existing identity checkout is prepared at accepted main on feat/bounded-purchase-journal; source implementation has not started. V3's conditional profile and the first-result forecast re-estimation remain as recorded above.

## 2026-10-25 — Bounded Journal prerequisite assigned

Quality owns the existing identity checkout for the first of the two reviewed purchase PRs: fixed bounded Journal access and capture holding. Platform reviews resource, process and durability limits; Research reviews identity, failure semantics and ordinary Journal compatibility. The next gate is an immutable source checkpoint and finite lower-level test plan, followed by independent runtime evidence and normal delivery checks. Public measured purchase integration follows this prerequisite's acceptance.

PR #122 remains delivered. The V3 16-call allocation is conditional; no scientific comparison or new allocation has started. Parent issues #105/#106, publisher handoff and full-study capacity remain open. The native first-result forecast still requires bottom-up re-estimation; approved caps and broader programme scope are unchanged.

## 2026-10-25 — Bounded Journal source reviewed

Source 730cc86 passed both scoped runtime reviews; final author checks and PR/main/candidate delivery remain pending. Public purchase integration and the conditional V3 16-call specimen have not run. Parent issues #105/#106, publisher handoff, full-study capacity and the first-result re-estimate remain open. [Evidence and current assignments](../EXECUTION_LOG.md#2026-10-25--bounded-journal-source-accepted-final-checks-pending).

## 2026-10-25 — Bounded Journal final author acceptance

Final source 8c85fef preserves reviewed runtime 730cc86; all 14 configured checks passed, including 4,314 tests. PR/main/candidate delivery is pending. Quality is queued for public purchase integration after delivery; the V3 specimen, publisher handoff, full-study capacity and parent issues #105/#106 remain open. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-25--bounded-journal-final-checks-accepted-delivery-pending).

## 2026-10-25 — Bounded Journal prerequisite delivered

PR #123/main c784f15 and exact 84-file candidate 12589122154 are accepted; all five main jobs passed. Quality is queued for public purchase integration after explicit handoff. The conditional V3 specimen, publisher handoff, full-study capacity and parent issues #105/#106 remain open. [Delivery evidence and assignments](../EXECUTION_LOG.md#2026-10-25--bounded-journal-pr-123-delivered).

## 2026-10-25 — Measured purchase handoff prepared

Quality's PR2 purchase/recovery handoff is prepared from pinned GitHub source, with independent Platform and Research review. Cloud execution awaits restored access and verified checkout ownership, disk and retained evidence. Purchase implementation, V3 and the study remain unstarted; parents and caps are unchanged. See the [implementation handoff](../MEASURED_PURCHASE_HANDOFF.md) and [assignment log](../EXECUTION_LOG.md#current-assignment-board).

## 2026-10-26 — Measured purchase implementation assigned

Verified cloud access and clean, unused checkouts allow the existing identity checkout to pass to Quality at accepted main c784f15. Platform and Research independently review the first immutable source checkpoint. The initial real-purchase/receipt/recovery gate remains distinct from full 12-slot mixed-history and downstream acceptance; V3 remains conditional. The study, caps, parent issues and later Laplace sequencing are unchanged. [Assignments and evidence](../EXECUTION_LOG.md#2026-10-26--measured-purchase-implementation-assigned).

## 2026-10-26 — Pure purchase contracts accepted

Pure contracts/binder 3df6dc3 is accepted and published on the source branch; actual purchase execution and recovery remain in implementation, with no PR/merge or runtime acceptance. The first purchase checkpoint is separate from full mixed-history/downstream proof. V3, caps and parent status remain unchanged. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-26--pure-purchase-contracts-accepted).

## 2026-10-26 — First measured purchase checkpoint accepted

Source 2c43f97 is accepted and published for the first-purchase and bounded recovery checkpoint, including qualified failure/replay evidence. The five selected 075c733 cases and retained bounded full path are independently accepted, with repeated-action calibration/menu limitations. PR124/main dfda60f is delivered: all five jobs in run 40277055513 and exact unpublished candidate 12630997569 are accepted. Next is retained comparison preparation/prediction/scoring binding, then publisher handoff; implementation is unassigned. V3, cumulative caps and parent issues #105/#106 are unchanged. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-26--first-measured-purchase-checkpoint-accepted).


## 2026-10-27 — Pure comparison bindings accepted

Pure payloads and material bindings at bdfed5d are independently accepted and published. The exact-source addendum passed 19 pure tests in 23.14 seconds; 88 source/package/installed files match. The initial test-inventory gap is preserved and closed by that addendum. Quality is implementing the measured supervisor adapter, with Platform and Research reviewing the next immutable source and concrete resource profile before measured calls. This is not actual Journal authority, numerical comparison or parent completion. Caps, graph and grid-first/Laplace-later sequencing remain unchanged. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-27--pure-comparison-bindings-accepted).


## 2026-10-27 — Comparison adapter source reviewed

Independent reviews found no static blocker in c427d39. Research delivered the source-only 45-call fixture at 4a5c84a; Quality is integrating it and implementing the explicit 50-call sequence for successful scoring and recovery after a missing prediction is retried. Its proposed bounds are 1,066,811,392 bytes and 1,338 CPU seconds under unchanged caps, conditional on smaller copy bounds and actual store fit. No measured runtime is admitted or observed. Lead owns progress in released primary; Quality retains identity. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-27--comparison-adapter-source-reviewed).


## 2026-10-27 — Comparison runtime repair

The first bounded integration attempt returned from 39 calls, then stopped during retained-history validation before the first score ran. Its original cost holds and failure evidence are preserved. Quality is removing repeated ledger validation and making the next fixture's overall lifetime explicit; per-call and scientific caps remain unchanged. The independently reviewed four-call boundary fixture is ready for integration. Repaired source/profile review is required before another measured attempt. [Evidence and assignments](../EXECUTION_LOG.md#2026-10-27--first-comparison-run-exposed-validation-cost).

## 2026-10-27 — Retained comparison local checks passed; delivery pending

Source 36c9595 passed 20 synthetic checks, the 50-call successor and the separate four-call boundary fixture. Both peers and Lead accepted the bounded 50-call evidence, and Platform/Lead accepted the separate boundary fixture. The full suite stopped at 1,041 passed/one failed with SIGPROF during candidate installation verification before producer dispatch. Lead/Platform accepted repair 50b1118; formatting-only successor 336d91b passed 16 focused cases in 17.29 seconds. Its subsequent full run stopped at 1,061 passed/one failed during prediction-ingress installation verification. Sealed evidence preserves eight closures and setup/control holds, with no new prediction reservation. The read-only mirror completed in 3.03 CPU seconds; two bounded 30-call diagnostics passed in 88.46/91.76 seconds, the latter retaining full collection without preceding test execution. Neither reproduced the timeout or established its cause. The subsequent normal full-suite observation stopped at 2,389 passed/one failed during paid original-score replay; all 33 watched calls passed. Retained score material matches; a source-proven deadline-masking path and four-second work cost support an expiry inference, without a recorded signal. Deadline propagation is now accepted at 97f4d55 with source-qualified 13+4 focused passes. A read-only computational replay validated the retained score and identified repeated canonical traversal; its profiled timing does not prove four-second fit. Same-invocation parsed-input reuse is now accepted at 1dee2c5: 29 focused cases and one actual 50-call specimen passed, with 103 records, 43 closures and four unresolved holds. The replay result is a single-run observation, not a timing guarantee. Exact 1cc9408 now passed all 15 local configured checks, including 4,421 tests in 1,850.02 seconds in normal complete order. Original and historical score replays returned in the full-context trace; passing physical fixtures were removed under the approved failed-only policy, so selected-run measurements remain separate. PR/main/candidate delivery remains pending. The failed first attempt, unknown costs and fixed-selection conformance limits are preserved. [Current verification and qualifications](../EXECUTION_LOG.md#2026-10-27--retained-comparison-local-full-verification-passed).

## 2026-10-27 — Handoff checkpoints accepted; full-study boundary clarified

The source-seal/store checkpoint 0336b5f passed 26 tests; original diagnostic-input checkpoint 95e9621 has a qualified 30-case pass (pytest exit 0 and 30 passing markers, preserved quiet-output reporting assertion, no retry). Each tested package matches its exact 90-file source and archives; dependency identities stayed unchanged. Quality continues the measured caller/activation, while Research prepares the separate 44-call actual handoff fixture. These checkpoints do not prove measured handoff, full-study feasibility or parent completion.

Full-study review found separate lower bounds above the existing 1 GiB authority and a missing multi-cell coordination boundary: the single-cell/three-ticket seal cannot serve all 36 cells by repetition. Before parent closure, make the bounded authority interface, one global budget, current limitations and later integration ownership explicit. Exact algorithm census and measured full-study fit belong after inference/policies exist and before RA-07.b admission; they are not circular prerequisites for implementing RA-N02.a/RA-N04. No graph, estimates, caps, experiment count or Laplace sequence changed. See the [assignment log and evidence](../EXECUTION_LOG.md#2026-10-27--publisher-handoff-checkpoints-and-study-boundary).

## 2026-10-27 — Handoff caller checked; integration verification in progress

Caller/activation source 6d42df9 passed 22 primitive tests, then the separately reviewed 44-call specimen passed in 240.21 seconds. Independent readback accepted all 44 returns, the complete sealed source prefix, original publication/replay bytes and three retained cost holds. Passing evidence is retained. This is one-cell conformance with fixed selection, not a research comparison or a timing guarantee.

The test-only ca9ee869 supplement is source-reviewed; its two-case/four-call runtime is pending. Research prepares that bounded runner, Quality prepares final static/schema/security/package checks, Platform reviews evidence and Lead updates progress. Both existing cloud checkouts are reused. Hosted full suites, PR/main/candidate delivery and the explicit parent audit remain pending; #105/#106 stay open. Global 36-cell authority/capacity and the grid-first/Laplace-later sequence are unchanged.

[Evidence and assignments](../EXECUTION_LOG.md#2026-10-27--handoff-caller-checked-integration-verification-in-progress).

Finite-grid inference remains the common reference for the first selector comparison. Laplace remains required in RA-N02.b: its approximation audit needs a validated grid reference and frozen validation cases. Source work can overlap once interfaces stabilize; validation follows the reference. The grid is a finite reference, not an exact continuous posterior. No dependency or estimate is changed here.


## 2026-10-27 — Handoff recovery checked; final delivery pending

Caller recovery now has passing evidence across two source-specific runs: the unknown/protected-retry case passed at ca9ee869, and the corrected lost-acknowledgement case passed at 1b43838 in 14.14 seconds. The initial four-call run remains recorded as one pass and one test-assertion failure; it is not relabelled a complete pass. Production package bytes are unchanged. The public handoff API and supported recovery limits are documented.

Quality owns the final ten local static/schema/security/package checks and candidate verification; Platform reviews the final evidence and progress; Research has completed the targeted caller cases; Lead owns source composition and GitHub delivery. Hosted full suites on Python 3.12/3.14, PR/main/candidate verification and explicit parent acceptance remain pending. Parents #105/#106 stay open. Full-study authority/capacity, global caps and grid-first/Laplace-later sequencing are unchanged.

[Evidence and assignments](../EXECUTION_LOG.md#2026-10-27--handoff-recovery-checked-final-delivery-pending).
