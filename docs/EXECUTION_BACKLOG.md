# Strange Physics — execution backlog

**2026-10-21 execution decision:** The owner approved the [reviewed native comparison plan](research/NATIVE_COMPARISON_PROPOSAL.md) and its bounded run. Scoped RA_EXEC covers eight enumerated units; the five native tasks and RA-07.b replacement dependencies are active. The23-task research graph has69 fixed plus six conditional edges; the approved baseline graph and GA forecast are unchanged. [Approval and limits](research/APPROVALS.md) govern execution. RA-01 is accepted in PR #107. N01 candidate contracts are integrated through PR #109; RA-02 accounting and Journal reconciliation are integrated through PR #110/main f9f450b with verified CI and package evidence. Native candidate production and prediction are delivered through PR #111/main c0e4c86, with all five CI jobs and candidate 12413204172 verified. Pure scoring is delivered through PR #112/main 73d07b6, with all five CI jobs and candidate 12425889219 verified. Classical diagnostic is delivered through PR #113/main 95f1735, with all five CI jobs and candidate 12458927169 verified against the reviewed author archives. The actual-Journal/classical union is delivered through PR #114/main9cb6e58:3,958 tests, both independent reviews, all five main CI jobs and candidate12459573763 accepted. Private publication composition is delivered through PR #115/main4eea1de:4,003 tests, both independent source reviews, all five main CI jobs and exact68-file candidate12485382723 accepted. The complete early no-score composer is delivered through PR #116/main2800188:4,088 tests, 1,522 schema cases, both independent reviews, all five main CI jobs and exact70-file candidate12504965031 accepted. PR #117 measured publication is delivered as main fb537d34 with verified CI and candidate 12541505445. [Delivery and proposed execution design](EXECUTION_LOG.md#2026-10-24--measured-publisher-delivery-accepted-execution-design-reviewed) retain the earlier source-specific failure/repair evidence; candidate-only pre-freeze execution is delivered through PR #118/main 9818ca0: both Python runtimes passed 4,213 tests in PR and main CI, all five main jobs passed, and candidate 12556446152 was independently accepted. Earlier source-specific checks and delivery failures remain preserved. Both #105 and #106 remain in progress; the accepted parent audit requires measured numerical/simulation wrappers before parent closure and finite-grid admission. VAL1 generator work remains deferred with draftPR101 preserved. No comparison has run.

**Execution location (2026-10-23):** All project checkouts, dependencies, builds, tests, datasets, media, logs, run outputs and private evidence stay in the existing studio-agent cloud workspace or hosted CI. The Mac is an SSH/control channel only; do not clone, install, build, run research, download artifacts or stage media there. Reuse the two existing cloud checkouts, preserve active writers and retained evidence, and keep cumulative budgets and review gates. No new capacity purchase or changes to other teams or the separate local computer-use project.

**Status:** Approved by the product owner on 2026-10-19. Initial execution is in progress; concrete paid/release gates remain pending. See [assignment log](EXECUTION_LOG.md).
**Owner:** technical lead and product owner. **Audited:** 2026-10-19. **Source baseline:** 28a4c19e8f9c92b83d886be6b96667d834784f9e.

[Roadmap](ROADMAP.md) owns product requirements, architecture, risks and overall progress. This document owns the execution review, PR-sized assignments, schedule and gates. [execution-backlog.json](execution-backlog.json) contains the same task records, exact dependencies and reproducible scheduling model. Keep all three consistent in the same planning/implementation PR. Legacy PLAN.md milestones are historical mappings, not a second schedule.

The 42 existing GitHub issues become epic rollups. **168 reviewable PR tasks, 369 prerequisite edges and ten approval/calendar gates** replace the coarse assignment graph. Tasks are issue-ready Markdown records; no additional 168 GitHub tickets are required to review this proposal. Select and materialize an individual task when assigning approved work. Parent issues are not independently assignable multiweek changes. Their old native whole-epic blockers are superseded by the leaf DAG: do not infer task readiness from parent issue state.

**Navigate:** [Audit](#planning-audit) · [Decisions](#decisions-requiring-approval) · [Estimate](#effort-confidence-and-capacity) · [Milestones](#milestone-schedule-and-exit-gates) · [Critical path](#critical-path-and-parallel-work) · [First ten days](#first-two-weeks-day-by-day) · [Contracts](#contract-register) · [PR tasks](#task-index) · [Dependency review](#dependency-review-and-maintenance)

## Research methods amendment (2026-10-19 cutoff)

The [dated method decision record](research/2026-10-19-METHOD_DECISIONS.md) retains18 broader research tasks and the [native comparison plan](research/NATIVE_COMPARISON_PROPOSAL.md) adds five scoped tasks. The owner approved eight enumerated native-path units on2026-10-21, including RA-01/02/07.b; other research tasks retain their authorization limits. Source/license, shared-model selection, calibration and complete accounting remain required. Provider, sizing, official-study and release gates remain separate.

The first new result is a local fixed-pool linear-model comparison after its scientific prerequisites:36 development episodes,432 purchased slots maximum,8 CPU-core-hours,1GiB new artifacts and zero provider calls. It does not wait for hosted deployment or all paper-inspired profiles. The optional later feasibility pilot has at most162 episodes; replicated-world sizing requires a separate approval and evidence before confirmatory freeze.

The retained23-task research ledger totals61–99 human engineering days plus25% reserve (76.25–123.75 days); this arithmetic envelope includes unapproved broader work. The approved first-result path is17–26 days (21.25–32.5 reserved), followed by later Laplace3–5 (3.75–6.25 reserved). The approved168-task/369-edge/ten-gate baseline and conditional W52–67 GA reference are unchanged. These estimates are not elapsed schedules or additional spending authorization.

## Planning audit

Inspected README, CONTRIBUTING, all ten preexisting docs, four JSON contract artifacts, dependency/CI configuration and public interfaces in contracts/session/journal/sdk. Existing implementation is the local trusted 55-test research core; no fitter, hosted runtime or enterprise controls were implemented by this review. Existing assertions were compared with source and public issue/milestone state. Draft checkpoint PUT already agrees with the design; it is not a discovered defect.

| ID | Finding | Correction |
| --- | --- | --- |
| AR01 | PLAN.md describes dataclasses and postpones NumPy; CORE.md/pyproject already use NumPy/Pydantic. | Correct legacy status/stack and link canonical roadmap/backlog; preserve accepted design. |
| AR02 | RELATED_WORK.md says no simulator exists; DEPLOYMENT_OPTIONS.md calls accepted registry/secrets choices proposed. | Correct current-status contradictions without changing scope. |
| AR03 | Roadmap uses generic /operations/{op} shorthand while draft API scopes operations to a run or workspace; checkpoint PUT was checked and already agrees. | Expand scoped polling paths in roadmap; preserve existing immutable PUT checkpoint contract. SP-01.b validates exact paths/errors. |
| AR04 | SP-01 tried to freeze all present/future interfaces in two weeks and blocked unrelated work. | Subset freezes owned by SP-01.a–d, SP-17.a, SP-19.a, SP-34.a/SP-35.a; consumer dependencies explicit. |
| AR05 | 42 epics of 1–4 person-weeks were not independently assignable PR tasks. | Replace assignment unit with 168 leaf records; parent issues become rollups, not implementation tickets. |
| AR06 | World catalog, provider connection management, publication and SSE server lacked explicit build owners. | Add SP-22.b, SP-17.c, SP-25.d, SP-23.a/b; frontend no longer scheduled against absent backend. |
| AR07 | Service-identity E2E preceded enterprise service identity delivery. | Move basic service/run tokens to SP-08.c; SP-34.d adds enterprise policy only. |
| AR08 | Pilot delete/recovery tests needed tombstones/audit assigned to GA. | Move SP-37.a–c to R3; keep audit export/enterprise retention in R8. |
| AR09 | First spring slice depended on complete three-family research packages. | SP-03.b→04.a/b→06.a→04.e creates early independent evidence; later fitting cannot hide its failure. |
| AR10 | Early integration dates and 118 PW estimate did not model reviewer capacity, missing endpoints or specialist queues. | Bottom-up 689 delivery days, confidence-weighted contingency and nine explicit resource lanes replace unverified dates; one feasible plan forecasts GA W52–67, pilot onboarding W38–50. |
| AR11 | Final load evidence could predate enterprise changes/assessment fixes. | SP-39.a waits for SP-40.b and final identity/retention/DR; changed candidate invalidates affected evidence. |
| AR12 | GA package mixed launch approval with future D7/D30 reviews. | SP-41.c/d are postlaunch only; they cannot block prelaunch readiness. |
| AR13 | Whole-epic blockers conflict with partial-interface parallel work. | Leaf DAG is authoritative; remove legacy native epic blockers after publication and replace issue bodies with exact leaf links. |
| AR14 | Headroom ~423 MiB, external availability, priced approvals and 30-day history were not executable dependencies. | Hard SP-02.b gate and named external/calendar gates; no fabricated completion or wait-time-as-approval. |
| AR15 | Full sweep engineering effort hid unmeasured execution time and design-partner recruitment. | Separate external runtime/participation gates; forecast conditional on measurement and appointments. |
| AR16 | SP-01.c lists DB obligations but its freeze could precede SP-01.b acceptance. | Add SP-01.b before SP-01.c freeze; regenerate both reference schedules. Draft preparation may proceed earlier; accepted transactional semantics must precede freeze. |

Current public source constraints were rechecked on 2026-10-19: dispatch must tolerate duplicate/unordered delivery ([Cloud Tasks](https://docs.cloud.google.com/tasks/docs/common-pitfalls)); sandbox choice still needs enforced configuration and adversarial verification ([GKE Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods)); API validation and runtime semantics are separate obligations ([OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0)). These facts do not validate this product's unimplemented deployment.

## Decisions requiring approval

| Decision | Recommendation | Status / boundary |
| --- | --- | --- |
| D01 — Approve this execution baseline and initial work | Recommended: accept the 168-task backlog; begin with R0, the first-ten-day design/foundation work SP-22.a and SP-27.a, and the bounded spring slice SP-03.a/b, SP-04.a/b/e, SP-06.a when their prerequisites pass. Review each later vertical slice at its integration checkpoint; concrete paid/release gates still require their stated approval. | Approved by product owner on 2026-10-19 at baseline 2d78e35; execute initial scope subject to prerequisites and remaining concrete gates. |
| D02 — Confirm real staffing and specialist capacity | Recommended: nine named engineers, 70% delivery availability, fractional product/design/security and independent assessment; retain two backend, two platform, two research, one frontend, one QE and one lead. | Execution amendment approved: project lead plus up to three engineer subagents, sequential role coverage. Nine-person forecast remains a reference; actual human operations/specialists and external appointments remain unconfirmed. |
| D03 — Accept the revised conditional horizon | Recommended: plan pilot onboarding W38–50, pilot evidence exit W45–59 and GA W52–67; reforecast after two weeks, R0 and each integration checkpoint. | Accepted as a conditional reference horizon, not a promise for subagent execution. Reforecast from actual throughput and external capacity. |
| D04 — Confirm the enterprise release boundary | Recommended: retain both research tracks, secure hosted user code, SDK/CLI/browser, one supported self-host target, federation/SCIM, audit export and external adoption before GA. | Accepted release boundary; customer-specific federation and self-host support still require evidence. |
| D05 — Approve provisional operating and data targets | Recommended: keep the 100-investigation measured envelope, proposed SLO/RPO/RTO matrix, 7-day active deletion, disclosed backup lifecycle, limited initial pilot support and staffed GA response. | Accepted as provisional acceptance hypotheses, not achieved guarantees; specialist/customer validation remains required. |
| D06 — Approve concrete paid and release actions at their gates | Recommended: separate priced staging configuration, capped real-provider trial, official sweep, pilot release and GA rollout approvals. | Separate concrete approvals retained; no staging provisioning, provider spend, official sweep or release approval supplied by backlog approval. The separate 2026-10-20 disk expansion and recovery snapshot approval is executed and accepted under SP-02.b. |

Highest-risk assumptions: (1) the disclosed dictionary is identifiable and useful under noise/change, (2) hostile Python builds and predictors can be contained in the selected real configuration, (3) complete ensemble evaluation fits a practical cost/latency envelope, (4) nine staff plus security/assessor/partner availability exist when needed, (5) the credit-bearing cloud account permits the design and has sufficient quota, and (6) partner and 30-day operational evidence will actually be available. SP-03/07, SP-14/15/19/31, SP-07.b/28, SP-00/40, SP-02, and SP-32/36/40 respectively retire these risks. A negative scientific result is valid; a leakage or validity defect blocks the release.

## Effort, confidence and capacity

Execution now uses one lead and at most three concurrent engineer subagents with rotating roles. The nine-person staffing model and day-by-day schedule below are retained as a human-team reference, not a forecast for this execution mode. [EXECUTION_LOG.md](EXECUTION_LOG.md) owns actual assignments, starts, reviews and blockers. Each execution lane has a responsible owner; specialist human staffing and independent assessment remain release prerequisites.

- Base delivery effort: **689 engineer-days = 137.8 person-weeks**. This includes implementation, author-written tests and documentation. Four days (0.8 PW) are postlaunch; pre-GA work is 685 days (137 PW).
- Explicit uncertainty reserve: **248.3 days = 49.66 PW**, allocated per task: high-confidence +10%, medium +25%, low +50%. Total all-work envelope: **937.3 days = 187.46 PW**. Reserve covers investigation, repair and rework; it is not extra feature scope or a statistical P80 calculation.
- Nine engineers deliver **0.7 day per working day**, or 6.3 PW/week collectively. The remaining 30% covers review, coordination, support and planning. Do not subtract author tests again. Fractional product/design/security and an independent assessor are additional appointment assumptions; external calendars are separate.
- Resource lanes: TL, BE1/BE2, PL1/PL2, RS1/RS2, FE and QE. Peers within backend/platform/research can take either lane. The lead may own independent system verification; selected browser/compatibility checks may be owned by FE. Reviewer capacity stays in the 30% allowance. One author task per lane; no hidden multiassignment.
- Each leaf is 1–5 delivery days and one independently reviewable PR or operational-evidence change. At 70% availability, a five-day task spans about 7.1 working days. If a change exceeds five delivery days after discovery, split by tested behavior before assignment; do not hide an unbounded repair program in a task.
- Base and reserve schedules are **feasible conservative list schedules**, not an optimization proof. The JSON includes the pure scheduling function, role eligibility, all durations and gate delays. No hiring ramp, holidays, unknown approval wait, partner wait beyond stated minima or unmeasured reference-sweep runtime is silently assumed complete.
- High confidence means established local/interface behavior; medium means known implementation patterns with integration risk; low means unproven numerical/security/provider/customer behavior. These are planning judgments, not measured probabilities. Re-estimate after D10, R0, each integration checkpoint and each uncertainty spike.

The original 118 PW plus 25% and GA W30–36 did not account for the expanded task graph and scarce specialist queues. The revised forecast is **pilot onboarding W38–50; R7 evidence exit W45–59; GA W52–67**, from approved, staffed start. Additional evidence waits or material redesign extend it. Keep accepted scope; improve the forecast using measured cycle time rather than compressing security/recovery gates. A seventh or tenth engineer changes role capacity and requires a model rerun.

### Reserve management

Research validity/compute spikes: SP-03.c/d and SP-07.a/b; sandbox/build spikes: SP-15.a and SP-14.b; federation/partner spikes: SP-34.a and SP-00.c; restoration spikes: SP-29.b and SP-38.b. Review immediately at each spike exit. If the low-confidence reserve is consumed or an acceptance invariant needs redesign, stop that path, record an ADR/scope change and rebaseline dependents. Parallel unaffected work may continue after its own gates. Paid sweeps and third-party assessment elapsed time are re-estimated from actual measurements/booking; approval delay is never converted to approval.

## Milestone schedule and exit gates

Weeks are relative five-working-day planning buckets. R8 begins with booking/design work before the pilot; it cannot exit before R7 and operational evidence. Only the first ten reference days below are detailed by day; later windows remain milestone-level forecasts. Actual subagent assignments are recorded separately in EXECUTION_LOG.md. Base exit and reserve exit are separate scenarios, not promised due dates.

| Milestone | Earliest base work | Base exit | Reserve exit | Delivery / reserve PW | Owner |
| --- | --- | --- | --- | --- | --- |
| R0 — Scope, contracts and environment readiness | W1 | W6 | W7 | 6.2 / 1.71 | TL + product |
| R1 — Scientifically valid learning and evaluation core | W2 | W18 | W26 | 17.2 / 6.90 | Research lead |
| R2 — Private durable control plane | W3 | W16 | W20 | 14.0 / 3.95 | Backend lead |
| R3 — Isolated execution and recoverable data | W2 | W24 | W33 | 23.8 / 8.35 | Platform lead + security |
| R4 — Provider integration and both research tracks | W5 | W27 | W36 | 16.2 / 6.30 | Research + backend |
| R5 — Researcher product and supported self-hosting | W1 | W30 | W40 | 19.4 / 5.35 | Frontend + platform |
| R6 — Integrated production pilot readiness | W18 | W35 | W45 | 14.2 / 5.55 | QE + security + platform |
| R7 — Design-partner evidence and reference publication | W35 | W45 | W59 | 8.4 / 3.80 | Product + research |
| R8 — Enterprise GA readiness and rollout | W7 | W52 | W67 | 17.6 / 7.55 | TL + security + platform |
| POST — Postlaunch reviews | W53 | W57 | W72 | 0.8 / 0.20 | TL + product |

### R0 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-00.b](#sp-00-b), [SP-00.c](#sp-00-c), [SP-01.e](#sp-01-e), [SP-02.b](#sp-02-b), [SP-02.c](#sp-02-c). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Signed baseline and subset contracts; named staff/partners pipeline; pinned client/mock checks; safe headroom and priced authorized staging config.

**Blocking risks / done:** No contract consumer starts until its specific subset is accepted; whole R0 exit need not serialize independent numerical work. Gate owner: TL + product. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R1 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-03.d](#sp-03-d), [SP-04.e](#sp-04-e), [SP-07.d](#sp-07-d). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Independent spring slice and full numerical/identifiability report; development uncertainty/failure/precision and total evaluator-cost evidence; both candidate protocols versioned.

**Blocking risks / done:** Invalid domain or uncalibrated uncertainty blocks official study; milestone may end in documented redesign. Gate owner: Research lead. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R2 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-08.d](#sp-08-d), [SP-09.d](#sp-09-d), [SP-10.c](#sp-10-c), [SP-11.c](#sp-11-c), [SP-12.c](#sp-12-c). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Real PostgreSQL concurrency/RLS tests; auth, invitations, basic service/run credentials, budgets, outbox, epochs and revocation verified.

**Blocking risks / done:** No private or uploaded customer runtime before integrated R3 security and release review. Gate owner: Backend lead. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R3 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-13.d](#sp-13-d), [SP-14.d](#sp-14-d), [SP-15.e](#sp-15-e), [SP-16.d](#sp-16-d), [SP-16.e](#sp-16-e), [SP-27.f](#sp-27-f), [SP-37.c](#sp-37-c). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Real staged remote recovery and hostile build/runtime/network evidence; immutable artifacts/checkpoints; basic audit/delete/tombstone replay; signed deploy/rollback/telemetry.

**Blocking risks / done:** SP-37.a–c moved here; managed runtime fail-closed and no missing committed artifacts are nonwaivable. Gate owner: Platform lead + security. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R4 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-17.d](#sp-17-d), [SP-18.d](#sp-18-d), [SP-19.d](#sp-19-d), [SP-20.d](#sp-20-d), [SP-21.c](#sp-21-c). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Capped provider trial; ambiguous billing/replay tested; hostile executable predictor validation; complete controlled and discovery manifests with no truth feedback.

**Blocking risks / done:** Paid-trial gate separate; both tracks and failed rows required, no cherry-picked demonstration. Gate owner: Research + backend. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R5 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-22.e](#sp-22-e), [SP-23.d](#sp-23-d), [SP-24.d](#sp-24-d), [SP-25.e](#sp-25-e), [SP-26.d](#sp-26-d). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Accessible author→run→inspect→export; durable SSE/resync; offline replay; supported fresh install/upgrade with explicit trust limitations.

**Blocking risks / done:** World/provider/publication/SSE backend tasks precede consumers; internal install is not external adoption. Gate owner: Frontend + platform. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R6 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-28.d](#sp-28-d), [SP-29.d](#sp-29-d), [SP-30.d](#sp-30-d), [SP-31.e](#sp-31-e). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** R1–R5 integrated at exact candidate; 100-run hold/soak/fairness, real failover/restore, negative security, deletion, migration and complete journeys pass.

**Blocking risks / done:** Any lost acknowledged state, duplicate logical debit, critical/high exploit, leak or failed restore blocks pilot. Gate owner: QE + security + platform. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R7 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-32.c](#sp-32-c), [SP-33.c](#sp-33-c), [SP-36.d](#sp-36-d). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Actual four-week partner use and outcome denominators; external agent/law/install/upgrade/reproduction; approved scored suite with all failures sanitized.

**Blocking risks / done:** External readiness, price approval and sweep wall time are real dependencies; missing evidence blocks adoption claims. Gate owner: Product + research. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### R8 gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-34.d](#sp-34-d), [SP-35.c](#sp-35-c), [SP-37.f](#sp-37-f), [SP-38.c](#sp-38-c), [SP-39.b](#sp-39-b), [SP-40.e](#sp-40-e), [SP-41.b](#sp-41-b). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** Federation/SCIM/audit/retention validated; independent assessment resolved; regional drill; final capacity test; staffed incident drill and 30-day SLO evidence; explicit rollout approval.

**Blocking risks / done:** R7 and all gate evidence required. Material candidate changes invalidate affected evidence; no compliance or unlimited-scale claim. Gate owner: TL + security + platform. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.

### POST gate

**Entry:** constituent tasks may start only after their explicit prerequisite records and required contract subset are complete; execution approval is recorded; other actual approval gates remain pending.

**Exit tasks:** [SP-41.c](#sp-41-c), [SP-41.d](#sp-41-d). All other task records allocated to this milestone must also be done; the list names its integration joins, not a waiver.

**Required evidence:** D7 and D30 outcomes reviewed with corrective owners and new scope decisions.

**Blocking risks / done:** Scheduled after GA; never used as a pre-GA dependency. Gate owner: TL + product. Dated source, environment, commands/results, reviewer and limitations are required in the release evidence manifest.


### Integration checkpoints

| ID / checkpoint | Joins | Evidence / next decision |
| --- | --- | --- |
| I0 — Baseline and first interface subsets | [SP-00.b](#sp-00-b), [SP-01.a](#sp-01-a), [SP-01.b](#sp-01-b), [SP-01.c](#sp-01-c) | Code identity and core compatibility reviewed; subsets can unblock independent work. |
| I1 — First independent learning slice | [SP-04.e](#sp-04-e) | Observe→fit→predict→independent development score; analytic accuracy, explicit failure and provenance. Stop research expansion if architecture fails. |
| I2 — Private transactional run | [SP-09.d](#sp-09-d), [SP-11.c](#sp-11-c), [SP-12.c](#sp-12-c) | Real PostgreSQL, roles/service tokens, exactly one logical debit and failure outcome. |
| I3 — Recoverable isolated remote run | [SP-16.d](#sp-16-d), [SP-16.e](#sp-16-e), [SP-37.c](#sp-37-c) | Kill/restart/cancel with no duplicate debit, malicious-runtime denial, telemetry and suppression ledger. |
| I4 — Both tracks and usable product | [SP-21.c](#sp-21-c), [SP-24.d](#sp-24-d), [SP-25.e](#sp-25-e), [SP-26.d](#sp-26-d) | Real provider/predictor paths, accessible browser, offline export and supported install; mock success insufficient. |
| I5 — Production pilot release candidate | [SP-30.d](#sp-30-d), [SP-32.a](#sp-32-a) | R1–R6 gates, security specialist and actual support/partner/data readiness; explicit pilot release authorization. |
| I6 — Enterprise candidate and measured operations | [SP-40.b](#sp-40-b), [SP-39.b](#sp-39-b), [SP-40.e](#sp-40-e) | Independent findings resolved, final capacity verified and complete 30-calendar-day SLO record. |
| I7 — GA and postlaunch | [SP-41.a](#sp-41-a), [SP-41.b](#sp-41-b) | Signed readiness plus explicit rollout approval; D7/D30 reviews remain after release. |

## Critical path and parallel work

The base resource-constrained path passes through contract/SQL/authorization → shared backend queue (broker, provider management, SSE and basic lifecycle) → world/live/replay UI → integrated journeys → pilot terms and final privacy controls → external assessment → final load/incident review → 30-day SLO window → GA. Science, sandbox and partner work are near-critical alternative paths; any invalidity or external delay can take over the critical path.

The exact controlling chain is below. **Resource** means the preceding task occupies the same author lane; it is not a fabricated technical dependency. **Dependency** means an explicit prerequisite. **Wait** means an approval/calendar gate. The machine ledger includes every other parallel task and both scenarios.

| Chain node | Incoming constraint | Purpose |
| --- | --- | --- |
| [APPROVAL](#external-and-calendar-gates) | Approval | User approves execution backlog and D01–D06; all work initially blocked |
| [SP-00.a](#sp-00-a) | Dependency | Record approval and named team capacity |
| [SP-00.b](#sp-00-b) | Dependency | Review and integrate the existing baseline |
| [SP-01.b](#sp-01-b) | Dependency | Freeze identity, run and SQL contracts |
| [SP-09.a](#sp-09-a) | Dependency | Create tenant SQL schema and migration harness |
| [SP-09.b](#sp-09-b) | Dependency | Reserve experiments and budgets atomically |
| [SP-09.c](#sp-09-c) | Dependency | Implement run and operation state transitions |
| [SP-09.d](#sp-09-d) | Dependency | Connect trusted simulator results to run transactions |
| [SP-11.a](#sp-11-a) | Dependency | Enforce tenant row policies and safe pool reuse |
| [SP-11.b](#sp-11-b) | Dependency | Authorize every operation and artifact reference |
| [SP-11.c](#sp-11-c) | Dependency | Enforce live revocation and audit decisions |
| [SP-15.c](#sp-15-c) | Dependency | Implement epoch-scoped run broker permissions |
| [SP-17.a](#sp-17-a) | Resource: BE1 | Freeze model-call and credential-management contracts |
| [SP-17.c](#sp-17-c) | Dependency | Manage workspace provider secrets |
| [SP-23.a](#sp-23-a) | Resource: BE1 | Publish committed event and replay endpoints |
| [SP-17.d](#sp-17-d) | Resource: BE1 | Replay recorded model responses offline |
| [SP-37.a](#sp-37-a) | Resource: BE1 | Persist basic security audit events |
| [SP-37.b](#sp-37-b) | Dependency | Implement authorized deletion and retention jobs |
| [SP-34.a](#sp-34-a) | Resource: BE1 | Validate enterprise federation requirements and entitlement |
| [SP-22.b](#sp-22-b) | Resource: BE1 | Implement versioned world and suite catalog API |
| [SP-22.d](#sp-22-d) | Dependency | Build constrained world editor |
| [SP-23.d](#sp-23-d) | Resource: FE | Integrate reconnect and cancellation UX |
| [SP-24.a](#sp-24-a) | Dependency | Implement indexed frame replay and scrubbing |
| [SP-24.b](#sp-24-b) | Dependency | Overlay prediction and uncertainty diagnostics |
| [SP-24.c](#sp-24-c) | Dependency | Compare recorded strategies and failures |
| [SP-22.e](#sp-22-e) | Resource: FE | Integrate world-to-run product journey |
| [SP-24.d](#sp-24-d) | Resource: FE | Verify accessible diagnostic journeys |
| [SP-30.a](#sp-30-a) | Dependency | Test authenticated end-to-end researcher journeys |
| [SP-30.b](#sp-30-b) | Dependency | Verify version compatibility matrix |
| [SP-30.c](#sp-30-c) | Dependency | Verify install, upgrade and recovery as one journey |
| [SP-30.d](#sp-30-d) | Dependency | Review integrated release-candidate evidence |
| [SP-32.a](#sp-32-a) | Dependency | Finalize partner data terms and pilot support scope |
| [SP-37.f](#sp-37-f) | Dependency | Review customer data and support documentation |
| [ASSESSMENT](#external-and-calendar-gates) | Wait | Independent assessment complete; assume ten working days service lead time, verify booking |
| [SP-40.b](#sp-40-b) | Dependency | Remediate independent assessment findings |
| [SP-39.a](#sp-39-a) | Dependency | Revalidate final supported capacity envelope |
| [SP-36.d](#sp-36-d) | Resource: TL | Close partner integration findings |
| [SP-40.c](#sp-40-c) | Resource: TL | Exercise incident and credential response |
| [SP-40.d](#sp-40-d) | Dependency | Start final-candidate SLO evidence collection |
| [SLO_OBSERVATION](#external-and-calendar-gates) | Wait | At least 30 consecutive calendar days; 22 workdays conservative scheduling proxy |
| [SP-40.e](#sp-40-e) | Dependency | Review 30 calendar days of SLO evidence |
| [SP-41.a](#sp-41-a) | Dependency | Sign evidence-based GA readiness |
| [SP-41.b](#sp-41-b) | Dependency | Execute approved progressive GA rollout |

| Parallel stream | Starts after | Can proceed alongside | Integration that cannot be skipped |
| --- | --- | --- | --- |
| Analytic numerical fixtures / scientific contracts | Reviewed baseline and headroom for changed dependencies | Backend schema and platform configuration | SP-03.b before first fit; full numerical calibration before study freeze |
| Backend identity / transaction work | SP-01.b; database harness as declared | Scientific fitting, artifact/worker contracts, frontend journey design | SP-09.d/11.c/12.c before authenticated durable run |
| Isolated build / runtime and artifact storage | SP-01.c, approved infrastructure and exact leaf prerequisites | Research inference and product mocks | SP-14.d/15.e before enabling uploaded code; SP-16.d proves recovery |
| Browser mocks and accessible journeys | SP-22.a then SP-01.e for consuming mock contracts | Backend producers | Real world/SSE/auth routes before SP-22.e/23.d; no mock-only product gate |
| Predictor packaging / held-out evaluation | SP-19.a and artifact/isolation prerequisites | Shared-fitter calibration, gateway transport | Both tracks join at SP-21.c; leak matrix must pass |
| Basic enterprise identity design / assessor booking | Base identity and partner requirements; SP-40.a booking | Pilot product construction | Final config, independent fixes and capacity precede SLO collection |
| Partner observation / reference sweep / external install | R6 pilot gate and their separate approvals | Each other where external participants available | R7 requires all outcomes, not a scheduled meeting |

## External and calendar gates

| Gate | Required predecessors | Minimum modeled elapsed time | Actual release condition |
| --- | --- | --- | --- |
| APPROVAL | User review of this backlog | Not modeled; explicit approval required | User approves execution backlog and D01–D06; all work initially blocked |
| PAID_TRIAL | [SP-17.c](#sp-17-c), [SP-18.c](#sp-18-c), [SP-02.c](#sp-02-c) | Not modeled; explicit approval required | Explicit capped real-provider trial approval |
| PILOT_RELEASE | [SP-32.a](#sp-32-a) | Not modeled; explicit approval required | Limited production pilot release approval |
| PILOT_OBSERVATION | [SP-32.b](#sp-32-b) | 20 working days | Four working weeks of actual partner use; external participation required |
| OFFICIAL_SWEEP | [SP-33.a](#sp-33-a) | Not modeled; explicit approval required | Explicit priced reference collection approval; measured runtime added at freeze |
| ASSESSMENT | [SP-40.a](#sp-40-a), [SP-35.c](#sp-35-c), [SP-37.f](#sp-37-f), [SP-38.c](#sp-38-c) | 10 working days | Independent assessment complete; assume ten working days service lead time, verify booking |
| SLO_OBSERVATION | [SP-40.d](#sp-40-d) | 22 working days | At least 30 consecutive calendar days; 22 workdays conservative scheduling proxy |
| GA_RELEASE | [SP-41.a](#sp-41-a) | Not modeled; explicit approval required | User/product owner authorizes actual GA rollout |
| POST_LAUNCH_D7 | [SP-41.b](#sp-41-b) | 5 working days | At least seven calendar days after successful rollout |
| POST_LAUNCH_D30 | [SP-41.b](#sp-41-b) | 22 working days | At least thirty calendar days after successful rollout |

Zero modeled approval duration is a conditional scheduling input, never evidence of approval. Thirty calendar days is the actual SLO requirement; 22 working days is a conservative no-holiday scheduling proxy. Four-week partner use must contain actual participating organizations. At official protocol freeze, add measured sweep execution/queue time to OFFICIAL_SWEEP/SP-33.b. Assessor work assumes a booked ten-working-day window; replace it with the real booking. Customer/procurement delays have no fabricated upper bound.

## First two weeks: day by day

D1 starts only after the user approves the backlog and the team is available. A task listed on a day may start partway through it, only after its listed predecessors actually finish. The JSON records exact fractional-day start/finish and lane order; this table rounds for daily communication. Unlisted lanes use review capacity or remain uncommitted; do not invent productive delivery work to fill a calendar.

| Day | Lead / quality | Backend | Platform | Research | Frontend | Checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
| D1 (W1) | TL: [SP-00.a](#sp-00-a) | Review / no author task | Review / no author task | Review / no author task | Review / no author task | Continue scoped work; record blockers |
| D2 (W1) | TL: [SP-00.a](#sp-00-a); QE: [SP-00.b](#sp-00-b); TL: [SP-00.c](#sp-00-c) | Review / no author task | PL1: [SP-02.a](#sp-02-a) | Review / no author task | Review / no author task | Target evidence: [SP-00.a](#sp-00-a) |
| D3 (W1) | QE: [SP-00.b](#sp-00-b); TL: [SP-00.c](#sp-00-c) | Review / no author task | PL1: [SP-02.a](#sp-02-a) | Review / no author task | Review / no author task | Continue scoped work; record blockers |
| D4 (W1) | QE: [SP-00.b](#sp-00-b); TL: [SP-00.c](#sp-00-c) | Review / no author task | PL1: [SP-02.a](#sp-02-a) | Review / no author task | Review / no author task | Continue scoped work; record blockers |
| D5 (W1) | QE: [SP-00.b](#sp-00-b); TL: [SP-00.c](#sp-00-c) | BE1: [SP-01.b](#sp-01-b) | PL1: [SP-02.a](#sp-02-a); PL2: [SP-02.b](#sp-02-b); PL1: [SP-02.c](#sp-02-c) | RS1: [SP-01.a](#sp-01-a) | FE: [SP-22.a](#sp-22-a) | Target evidence: [SP-00.b](#sp-00-b), [SP-02.a](#sp-02-a); W1 capacity/approval review |
| D6 (W2) | TL: [SP-00.c](#sp-00-c) | BE1: [SP-01.b](#sp-01-b) | PL2: [SP-02.b](#sp-02-b); PL1: [SP-02.c](#sp-02-c) | RS1: [SP-01.a](#sp-01-a) | FE: [SP-22.a](#sp-22-a) | Target evidence: [SP-00.c](#sp-00-c) |
| D7 (W2) | Review / no author task | BE1: [SP-01.b](#sp-01-b) | PL2: [SP-02.b](#sp-02-b); PL1: [SP-02.c](#sp-02-c) | RS1: [SP-01.a](#sp-01-a) | FE: [SP-22.a](#sp-22-a) | Continue scoped work; record blockers |
| D8 (W2) | Review / no author task | BE1: [SP-01.b](#sp-01-b) | PL2: [SP-02.b](#sp-02-b); PL1: [SP-02.c](#sp-02-c); PL1: [SP-27.a](#sp-27-a) | RS1: [SP-01.a](#sp-01-a); RS2: [SP-03.a](#sp-03-a) | FE: [SP-22.a](#sp-22-a) | Target evidence: [SP-02.b](#sp-02-b), [SP-02.c](#sp-02-c) |
| D9 (W2) | Review / no author task | BE1: [SP-01.b](#sp-01-b) | PL1: [SP-27.a](#sp-27-a) | RS1: [SP-01.a](#sp-01-a); RS2: [SP-03.a](#sp-03-a) | FE: [SP-22.a](#sp-22-a) | Target evidence: [SP-01.a](#sp-01-a), [SP-22.a](#sp-22-a) |
| D10 (W2) | Review / no author task | BE1: [SP-01.b](#sp-01-b) | PL1: [SP-27.a](#sp-27-a) | RS2: [SP-03.a](#sp-03-a) | Review / no author task | Target evidence: [SP-01.b](#sp-01-b); re-estimate remaining R0 and first-slice work, do not declare full contract freeze |

Day-ten outcome is partial contract/preflight evidence, not an implemented hosted service. R0 exit is W6 base/W7 reserve. First independent learning slice SP-04.e is approximately W11 base/W13 reserve in this model. SP-01.b finishes at reference day 10; SP-01.c author work starts on D11 after that acceptance. Draft review can occur earlier without claiming a freeze. If headroom or permissions remain unresolved, keep dependent tasks blocked and reforecast; no project/dependency copies are created on the Mac.

## Contract register

These contracts are requirements for each task, not claims that future interfaces exist. A contract producer/review task can work on a draft; implementation consumers require the freeze task in their transitive prerequisites. SP-01.c additionally waits for SP-01.b DB acceptance before freezing artifact commits and lease semantics. SP-22.a is a journey-specification input, not a consumer implementation. OPS/GOV are existing proposed policy constraints with later concrete authorization gates. Every task's referenced contract obligations below are part of its acceptance and review scope.

<a id="contract-core"></a>
### C-CORE: Current public SDK and laws

**Owner:** Research + SDK. **Freeze:** Existing core or roadmap policy; task-specific changes still reviewed. **Source:** [core.schema.json](../contracts/core.schema.json), [CORE.md](CORE.md), [LAWS.md](LAWS.md), [CHECKPOINTS.md](CHECKPOINTS.md).

Experiment identities, graph/order/mass bounds, finite values, budget/checkpoint prefix and strict unknown-field rejection. Existing local formats are implemented; hosted semantics are not.

<a id="contract-sci"></a>
### C-SCI: Model, prediction and scoring messages

**Owner:** Research + QE. **Freeze:** [SP-01.a](#sp-01-a). **Source:** [research.schema.json](../contracts/research.schema.json), [SCI_CONTRACT.md](SCI_CONTRACT.md), [BENCHMARK.md](BENCHMARK.md).

Versioned model/provenance, exact purchased-data-only fitter prefix, distinct integration steps, finite ordered trajectories, explicit failure counts and fixed coordinate normalizer. The first local subset reports development MSE and normalized MSE; any failed probe makes it unscorable. Full benchmark scoring remains unfrozen.

<a id="contract-http"></a>
### C-HTTP: HTTP operations and error envelopes

**Owner:** Backend + SDK + frontend. **Freeze:** [SP-01.b](#sp-01-b). **Source:** [openapi.json](../contracts/draft/openapi.json), [accepted control and identity contract set](IDENTITY_RUN_CONTRACT.md) (SP-01.b bounded freeze complete; live producers remain later tasks).

OpenAPI 3.1, scoped operation polling, Idempotency-Key on applicable mutations, immutable checkpoint PUT, explicit 401/403/404/409/422/429/503 semantics, version policy. The accepted bounded control/identity route set is not the complete product API; later groups retain their own freeze tasks.

<a id="contract-id"></a>
### C-ID: Identity, membership and credential authority

**Owner:** Backend + security. **Freeze:** [SP-01.b](#sp-01-b). **Source:** [roadmap sections 5–6 and 8](ROADMAP.md#5-api-sdk-events-and-interface-freeze), [accepted control and identity contract set](IDENTITY_RUN_CONTRACT.md) (SP-01.b bounded freeze complete; live producers remain later tasks).

Issuer/subject identity, explicit workspace roles/invitations, scoped machine and run credentials, revocation and secure browser session semantics. Enterprise federation refined by SP-34.a; SCIM frozen by SP-35.a before those consumers.

<a id="contract-db"></a>
### C-DB: Transactional relational invariants

**Owner:** Backend. **Freeze:** [SP-01.b](#sp-01-b). **Source:** [roadmap data model](ROADMAP.md#6-data-model-ownership-and-lifecycle), [accepted control and identity contract set](IDENTITY_RUN_CONTRACT.md) (SP-01.b bounded freeze complete; live producers remain later tasks).

Composite tenant ownership, unique operation/ordinal, atomic debit/result/outbox, revision/epoch checks, immutable terminal state, safe migration/runtime-role separation.

<a id="contract-art"></a>
### C-ART: Artifact and recovery manifests

**Owner:** Platform + backend + research. **Freeze:** [SP-01.c](#sp-01-c). **Source:** [roadmap artifact contracts](ROADMAP.md#52-event-and-artifact-contracts), [CHECKPOINTS.md](CHECKPOINTS.md).

Hash, byte size, media type, storage generation, visibility, runtime/protocol identity, checkpoint completed prefix, deletion tombstones, bounded safe deserialization and complete export.

<a id="contract-exec"></a>
### C-EXEC: Build, worker, lease and broker protocol

**Owner:** Platform + security + backend. **Freeze:** [SP-01.c](#sp-01-c). **Source:** [roadmap trust boundaries](ROADMAP.md#4-architecture-and-trust-boundaries).

Approved image digest, launch ID, lease epoch, attempt identity, resource deadline, cancellation, network scope, quarantined builds and networkless predictors. No fallback from required sandbox.

<a id="contract-web"></a>
### C-WEB: World catalog, committed events and replay

**Owner:** Frontend + backend. **Freeze:** [SP-01.d](#sp-01-d). **Source:** [roadmap event contracts](ROADMAP.md#52-event-and-artifact-contracts).

Immutable world versions/author projection, per-run sequence, typed payload, Last-Event-ID, cursor-expired snapshot/archive resync, bounded replay chunks and post-run truth authorization.

<a id="contract-provider"></a>
### C-PROVIDER: Provider connection and durable call protocol

**Owner:** Backend + research + security. **Freeze:** [SP-17.a](#sp-17-a). **Source:** [roadmap provider rules](ROADMAP.md#73-ai-workload-model).

Connection secret reference, provider/model/version, logical call/attempt state, token reservation, timeout ambiguity, request/response hash, billed/estimated/unknown usage, replay without network.

<a id="contract-pred"></a>
### C-PRED: Executable predictor invocation

**Owner:** Research + platform + security. **Freeze:** [SP-19.a](#sp-19-a). **Source:** [roadmap predictor boundary](ROADMAP.md#32-complete-agent-discovery-track).

Public input only, protocol/image identity, timestamps/order/shape, finite outputs/declared intervals, CPU/wall/output caps and invalid-output failure classification.

<a id="contract-ops"></a>
### C-OPS: Deployment, telemetry and recovery policy

**Owner:** Platform + QE + security. **Freeze:** Existing core or roadmap policy; task-specific changes still reviewed. **Source:** [roadmap operations](ROADMAP.md#13-cicd-deployment-reliability-and-operations), [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md).

Versioned IaC/config, keyless CI, isolated identities, bounded pools/metrics, exact evidence manifests, RPO/RTO/SLO targets and private records. Priced configuration needs SP-02.c; collection/rollout requires separate named gates.

<a id="contract-gov"></a>
### C-GOV: Approval, evidence and release records

**Owner:** Technical lead + product. **Freeze:** Existing core or roadmap policy; task-specific changes still reviewed. **Source:** [roadmap governance](ROADMAP.md#14-risk-register-assumptions-and-governance).

Named decision/gate owner, exact source/config/test identity, unresolved blockers, privacy-safe evidence links, scope/estimate change record and explicit external approvals.


## Task index

The backlog is approved. Each leaf below retains its own PR boundary, prerequisites, status and required evidence. All are P0 for their stated release gate; this does not imply simultaneous assignment. API/storage producers precede consumers. Scope outside a leaf is not silently included in its estimate. Proposed tests are not already implemented. Reviewers are roles until actual staff are named.

| Epic / GitHub issue | PR units | Delivery PW | Assigned milestone(s) |
| --- | --- | --- | --- |
| [SP-00 — Approve scope, staff and evidence baseline](https://github.com/spei04/strange-physics/issues/2) | [SP-00.a](#sp-00-a), [SP-00.b](#sp-00-b), [SP-00.c](#sp-00-c) | 1.2 | R0 |
| [SP-01 — Freeze shared schemas and mocks](https://github.com/spei04/strange-physics/issues/3) | [SP-01.a](#sp-01-a), [SP-01.b](#sp-01-b), [SP-01.c](#sp-01-c), [SP-01.d](#sp-01-d), [SP-01.e](#sp-01-e) | 3.8 | R0 |
| [SP-02 — Verify cloud and workspace prerequisites](https://github.com/spei04/strange-physics/issues/4) | [SP-02.a](#sp-02-a), [SP-02.b](#sp-02-b), [SP-02.c](#sp-02-c) | 1.2 | R0 |
| [SP-03 — Validate numerical domain and baseline](https://github.com/spei04/strange-physics/issues/5) | [SP-03.a](#sp-03-a), [SP-03.b](#sp-03-b), [SP-03.c](#sp-03-c), [SP-03.d](#sp-03-d) | 3.0 | R1 |
| [SP-04 — Implement integrated sparse fitter](https://github.com/spei04/strange-physics/issues/6) | [SP-04.a](#sp-04-a), [SP-04.b](#sp-04-b), [SP-04.c](#sp-04-c), [SP-04.d](#sp-04-d), [SP-04.e](#sp-04-e) | 3.8 | R1 |
| [SP-05 — Add uncertainty, adaptation and active selection](https://github.com/spei04/strange-physics/issues/7) | [SP-05.a](#sp-05-a), [SP-05.b](#sp-05-b), [SP-05.c](#sp-05-c), [SP-05.d](#sp-05-d) | 3.2 | R1 |
| [SP-06 — Implement held-out metrics and failure policy](https://github.com/spei04/strange-physics/issues/8) | [SP-06.a](#sp-06-a), [SP-06.b](#sp-06-b), [SP-06.c](#sp-06-c), [SP-06.d](#sp-06-d) | 3.4 | R1 |
| [SP-07 — Calibrate and draft frozen study manifests](https://github.com/spei04/strange-physics/issues/9) | [SP-07.a](#sp-07-a), [SP-07.b](#sp-07-b), [SP-07.c](#sp-07-c), [SP-07.d](#sp-07-d) | 3.8 | R1 |
| [SP-08 — Build identity and workspace memberships](https://github.com/spei04/strange-physics/issues/10) | [SP-08.a](#sp-08-a), [SP-08.b](#sp-08-b), [SP-08.c](#sp-08-c), [SP-08.d](#sp-08-d) | 3.0 | R2 |
| [SP-09 — Implement run and experiment transactions](https://github.com/spei04/strange-physics/issues/11) | [SP-09.a](#sp-09-a), [SP-09.b](#sp-09-b), [SP-09.c](#sp-09-c), [SP-09.d](#sp-09-d) | 3.4 | R2 |
| [SP-10 — Add outbox, fencing and reconciliation](https://github.com/spei04/strange-physics/issues/12) | [SP-10.a](#sp-10-a), [SP-10.b](#sp-10-b), [SP-10.c](#sp-10-c) | 2.8 | R2 |
| [SP-11 — Enforce tenant and artifact authorization](https://github.com/spei04/strange-physics/issues/13) | [SP-11.a](#sp-11-a), [SP-11.b](#sp-11-b), [SP-11.c](#sp-11-c) | 2.4 | R2 |
| [SP-12 — Implement quotas and usage accounting](https://github.com/spei04/strange-physics/issues/14) | [SP-12.a](#sp-12-a), [SP-12.b](#sp-12-b), [SP-12.c](#sp-12-c) | 2.4 | R2 |
| [SP-13 — Persist immutable artifacts and checkpoints](https://github.com/spei04/strange-physics/issues/15) | [SP-13.a](#sp-13-a), [SP-13.b](#sp-13-b), [SP-13.c](#sp-13-c), [SP-13.d](#sp-13-d) | 3.0 | R3 |
| [SP-14 — Build packages in isolation](https://github.com/spei04/strange-physics/issues/16) | [SP-14.a](#sp-14-a), [SP-14.b](#sp-14-b), [SP-14.c](#sp-14-c), [SP-14.d](#sp-14-d) | 3.6 | R3 |
| [SP-15 — Enforce sandbox runtime and broker policy](https://github.com/spei04/strange-physics/issues/17) | [SP-15.a](#sp-15-a), [SP-15.b](#sp-15-b), [SP-15.c](#sp-15-c), [SP-15.d](#sp-15-d), [SP-15.e](#sp-15-e) | 4.4 | R3 |
| [SP-16 — Connect recoverable remote execution](https://github.com/spei04/strange-physics/issues/18) | [SP-16.a](#sp-16-a), [SP-16.b](#sp-16-b), [SP-16.c](#sp-16-c), [SP-16.d](#sp-16-d), [SP-16.e](#sp-16-e) | 4.6 | R3 |
| [SP-17 — Implement durable model-call ledger](https://github.com/spei04/strange-physics/issues/19) | [SP-17.a](#sp-17-a), [SP-17.b](#sp-17-b), [SP-17.c](#sp-17-c), [SP-17.d](#sp-17-d) | 3.4 | R4 |
| [SP-18 — Add bounded provider adapters and LLM selector](https://github.com/spei04/strange-physics/issues/20) | [SP-18.a](#sp-18-a), [SP-18.b](#sp-18-b), [SP-18.c](#sp-18-c), [SP-18.d](#sp-18-d) | 3.0 | R4 |
| [SP-19 — Define executable predictor packaging](https://github.com/spei04/strange-physics/issues/21) | [SP-19.a](#sp-19-a), [SP-19.b](#sp-19-b), [SP-19.c](#sp-19-c), [SP-19.d](#sp-19-d) | 3.4 | R4 |
| [SP-20 — Build independent evaluation execution](https://github.com/spei04/strange-physics/issues/22) | [SP-20.a](#sp-20-a), [SP-20.b](#sp-20-b), [SP-20.c](#sp-20-c), [SP-20.d](#sp-20-d) | 3.6 | R4 |
| [SP-21 — Integrate the two research tracks](https://github.com/spei04/strange-physics/issues/23) | [SP-21.a](#sp-21-a), [SP-21.b](#sp-21-b), [SP-21.c](#sp-21-c) | 2.8 | R4 |
| [SP-22 — Build workspace and constrained world UI](https://github.com/spei04/strange-physics/issues/24) | [SP-22.a](#sp-22-a), [SP-22.b](#sp-22-b), [SP-22.c](#sp-22-c), [SP-22.d](#sp-22-d), [SP-22.e](#sp-22-e) | 4.2 | R5 |
| [SP-23 — Implement live event timeline and reconnection](https://github.com/spei04/strange-physics/issues/25) | [SP-23.a](#sp-23-a), [SP-23.b](#sp-23-b), [SP-23.c](#sp-23-c), [SP-23.d](#sp-23-d) | 3.6 | R5 |
| [SP-24 — Implement prediction and replay diagnostics](https://github.com/spei04/strange-physics/issues/26) | [SP-24.a](#sp-24-a), [SP-24.b](#sp-24-b), [SP-24.c](#sp-24-c), [SP-24.d](#sp-24-d) | 3.4 | R5 |
| [SP-25 — Deliver remote SDK, CLI and complete export](https://github.com/spei04/strange-physics/issues/27) | [SP-25.a](#sp-25-a), [SP-25.b](#sp-25-b), [SP-25.c](#sp-25-c), [SP-25.d](#sp-25-d), [SP-25.e](#sp-25-e) | 4.4 | R5 |
| [SP-26 — Package supported self-host deployment](https://github.com/spei04/strange-physics/issues/28) | [SP-26.a](#sp-26-a), [SP-26.b](#sp-26-b), [SP-26.c](#sp-26-c), [SP-26.d](#sp-26-d) | 3.8 | R5 |
| [SP-27 — Create IaC and trusted delivery foundation](https://github.com/spei04/strange-physics/issues/29) | [SP-27.a](#sp-27-a), [SP-27.b](#sp-27-b), [SP-27.c](#sp-27-c), [SP-27.d](#sp-27-d), [SP-27.e](#sp-27-e), [SP-27.f](#sp-27-f) | 5.2 | R3 |
| [SP-28 — Measure capacity and fairness](https://github.com/spei04/strange-physics/issues/30) | [SP-28.a](#sp-28-a), [SP-28.b](#sp-28-b), [SP-28.c](#sp-28-c), [SP-28.d](#sp-28-d) | 3.6 | R6 |
| [SP-29 — Prove backup, failover and fault recovery](https://github.com/spei04/strange-physics/issues/31) | [SP-29.a](#sp-29-a), [SP-29.b](#sp-29-b), [SP-29.c](#sp-29-c), [SP-29.d](#sp-29-d) | 3.6 | R6 |
| [SP-30 — Verify integrated journeys and upgrades](https://github.com/spei04/strange-physics/issues/32) | [SP-30.a](#sp-30-a), [SP-30.b](#sp-30-b), [SP-30.c](#sp-30-c), [SP-30.d](#sp-30-d) | 3.0 | R6 |
| [SP-31 — Exercise security and data boundaries](https://github.com/spei04/strange-physics/issues/33) | [SP-31.a](#sp-31-a), [SP-31.b](#sp-31-b), [SP-31.c](#sp-31-c), [SP-31.d](#sp-31-d), [SP-31.e](#sp-31-e) | 4.0 | R6 |
| [SP-32 — Onboard and support design partners](https://github.com/spei04/strange-physics/issues/34) | [SP-32.a](#sp-32-a), [SP-32.b](#sp-32-b), [SP-32.c](#sp-32-c) | 2.2 | R7 |
| [SP-33 — Freeze and publish scored reference release](https://github.com/spei04/strange-physics/issues/35) | [SP-33.a](#sp-33-a), [SP-33.b](#sp-33-b), [SP-33.c](#sp-33-c) | 2.6 | R7 |
| [SP-34 — Add enterprise SSO and service identities](https://github.com/spei04/strange-physics/issues/36) | [SP-34.a](#sp-34-a), [SP-34.b](#sp-34-b), [SP-34.c](#sp-34-c), [SP-34.d](#sp-34-d) | 3.2 | R8 |
| [SP-35 — Add provisioning and rapid deprovisioning](https://github.com/spei04/strange-physics/issues/37) | [SP-35.a](#sp-35-a), [SP-35.b](#sp-35-b), [SP-35.c](#sp-35-c) | 2.8 | R8 |
| [SP-36 — Validate external extension and self-host adoption](https://github.com/spei04/strange-physics/issues/38) | [SP-36.a](#sp-36-a), [SP-36.b](#sp-36-b), [SP-36.c](#sp-36-c), [SP-36.d](#sp-36-d) | 3.6 | R7 |
| [SP-37 — Ship enterprise audit and retention controls](https://github.com/spei04/strange-physics/issues/39) | [SP-37.a](#sp-37-a), [SP-37.b](#sp-37-b), [SP-37.c](#sp-37-c), [SP-37.d](#sp-37-d), [SP-37.e](#sp-37-e), [SP-37.f](#sp-37-f) | 5.2 | R3, R8 |
| [SP-38 — Rehearse regional disaster recovery](https://github.com/spei04/strange-physics/issues/40) | [SP-38.a](#sp-38-a), [SP-38.b](#sp-38-b), [SP-38.c](#sp-38-c) | 2.8 | R8 |
| [SP-39 — Revalidate supported production envelope](https://github.com/spei04/strange-physics/issues/41) | [SP-39.a](#sp-39-a), [SP-39.b](#sp-39-b) | 1.6 | R8 |
| [SP-40 — Complete independent assurance and operations](https://github.com/spei04/strange-physics/issues/42) | [SP-40.a](#sp-40-a), [SP-40.b](#sp-40-b), [SP-40.c](#sp-40-c), [SP-40.d](#sp-40-d), [SP-40.e](#sp-40-e) | 3.8 | R8 |
| [SP-41 — Approve GA release and post-launch review](https://github.com/spei04/strange-physics/issues/43) | [SP-41.a](#sp-41-a), [SP-41.b](#sp-41-b), [SP-41.c](#sp-41-c), [SP-41.d](#sp-41-d) | 2.0 | R8, POST |

<a id="epic-sp-00"></a>
## SP-00 — Approve scope, staff and evidence baseline

Parent: [#2](https://github.com/spei04/strange-physics/issues/2). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-00-a"></a>
### SP-00.a — Record approval and named team capacity

- **Objective:** Establish a reviewed, staffed and evidence-backed start without implying execution approval. This PR delivers record approval and named team capacity.
- **Implementation scope:** Record D01–D06 dispositions, current execution lane owners, reviewer availability and start conditions. Preserve the nine-person forecast as a reference until human staffing exists.
- **Out of scope:** Product implementation or accepting this backlog on the user's behalf.
- **Prerequisites and dependencies:** [APPROVAL](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Each current execution lane has a responsible owner and assignments obey the three-engineer concurrency limit; external human staffing remains an explicit release dependency.
- **Required automated tests:** Validate decision IDs, accountable execution roles, three-engineer concurrency, independent review and approval evidence.
- **Security and reliability:** No implied infrastructure-spend authority; private staffing evidence.
- **Effort and confidence:** 1 delivery engineer-day; high confidence; +0.10 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed for stated scope; evidence in EXECUTION_LOG.md.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-00-b"></a>
### SP-00.b — Review and integrate the existing baseline

- **Objective:** Establish a reviewed, staffed and evidence-backed start without implying execution approval. This PR delivers review and integrate the existing baseline.
- **Implementation scope:** Review PR #1 and existing core; resolve baseline findings and integrate through normal review.
- **Out of scope:** New fitter or merging before approval.
- **Prerequisites and dependencies:** [SP-00.a](#sp-00-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** 55 existing tests and configured checks pass at reviewed integration identity.
- **Required automated tests:** Core CI, lint/types/build and merge-identity verification.
- **Security and reliability:** Preserve private journals and unrelated work; green CI is not review.
- **Effort and confidence:** 2 delivery engineer-days; high confidence; +0.20 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Research, SDK, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed for stated scope; integration 7117060 and review evidence in EXECUTION_LOG.md.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-00-c"></a>
### SP-00.c — Secure partner and assessor availability

- **Objective:** Establish a reviewed, staffed and evidence-backed start without implying execution approval. This PR delivers secure partner and assessor availability.
- **Implementation scope:** Document partner requirements, legal/product contacts and independent-assessor lead times in private evidence.
- **Out of scope:** Outreach without authorization; promising contracts.
- **Prerequisites and dependencies:** [SP-00.a](#sp-00-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Three candidate organizations and external gate owners identified; unavailable commitments explicit.
- **Required automated tests:** Validate readiness checklist owners, deadlines and sanitized evidence.
- **Security and reliability:** No fabricated adoption or public customer identifiers.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-01"></a>
## SP-01 — Freeze shared schemas and mocks

Parent: [#3](https://github.com/spei04/strange-physics/issues/3). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-01-a"></a>
### SP-01.a — Freeze the first scientific interface subset

- **Objective:** Give producers and consumers stable, testable interfaces before parallel implementation. This PR delivers freeze the first scientific interface subset.
- **Implementation scope:** Review observation-only fitter inputs, model provenance, prediction ordering and report compatibility fixtures.
- **Out of scope:** Full sparse fitting or benchmark freeze.
- **Prerequisites and dependencies:** [SP-00.b](#sp-00-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Research/SDK owners sign version; hidden world fields absent.
- **Required automated tests:** Schema/reference checks, positive/negative/runtime fixtures and Pydantic parity.
- **Security and reliability:** Finite/shape boundaries explicit; fixtures are not results.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, SDK, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed. PR #51 merged cc24aef592f3157b67024e3cab41159489c77ffa, tree identical to reviewed 6e72415; all four head CI checks and merge-main CI passed. Research authored, Quality independently reviewed three repairs, lead accepted. 147 tests and schema/static checks passed for the first local SCI subset. Owner: Engineer Research; [issue](https://github.com/spei04/strange-physics/issues/47).
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.


<a id="sp-01-b"></a>
### SP-01.b — Freeze identity, run and SQL contracts

- **Objective:** Give producers and consumers stable, testable interfaces before parallel implementation. This PR delivers freeze identity, run and sql contracts.
- **Implementation scope:** Specify session/membership/service scopes, operations, SQL constraints, idempotency and checkpoint PUT semantics.
- **Out of scope:** Remaining product API groups or implementation.
- **Prerequisites and dependencies:** [SP-00.b](#sp-00-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-ID](#contract-id), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Producer/consumer owners accept route/state/error and conflict examples.
- **Required automated tests:** Operation/path/schema checks and terminal/duplicate/conflict fixtures.
- **Security and reliability:** Membership separate from identity; immutable terminal states.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; complete. PR #88/main 92320173ff0d3278c65cfc251983d57fab9960b1 matches accepted b8d3e5ee96b3b07da53eccbabddebc5a73223ba3 and tree 515e27ebbb594a15ce439b24a14463ed7a4cf9a7; PR CI39367180231 and all protected-main CI39367439199 jobs passed. Integrated 1,692 tests, Ruff/format92, strict mypy57,613 schema checks, configured security checks and offline package validation passed. Earlier control/ID-A/ID-B/C1 integrations and final 749-case composition review are accepted. Interface/SQL obligations are frozen; actual hosted producers, signing and storage remain later tasks.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-01-c"></a>


### SP-01.c — Freeze artifacts, packages and worker interfaces

- **Objective:** Give producers and consumers stable, testable interfaces before parallel implementation. This PR delivers freeze artifacts, packages and worker interfaces.
- **Implementation scope:** Specify object generations, checkpoint prefixes, lease/broker epochs, build quarantine and predictor envelopes.
- **Out of scope:** Provisioning or proving isolation.
- **Prerequisites and dependencies:** [SP-00.b](#sp-00-b), [SP-01.b](#sp-01-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-EXEC](#contract-exec), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Signed version covers partial object/DB writes and stale leases after DB contract acceptance in SP-01.b; earlier drafting does not count as freeze.
- **Required automated tests:** Hash/size/epoch/checkpoint fixtures with corrupt and incomplete cases.
- **Security and reliability:** No trusted pickle; bounded inputs and scoped identities.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, backend, research, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed for the pure contract/predicate scope through issue #89 and PRs #91–93. COMP1 and SP-01.c are complete through PR #93/main11e200253347dc05973e5d7969a3abd145f285e2, matching revieweda75ac1b7099aa8d38d62577d14315dfeb5009f49/treeec01b963f20e95f682ef06a04bcebcd4350db862. All four PR CI39379345399 and all five protected-main CI39379544409 jobs passed. The exact integrated source passed 2,423 tests, 764 schema cases, Ruff/format and strict typing; independent boundary, recovery and composition reviews are accepted. Candidate artifact12245465046 was checksum/provenance verified and retained privately outside checkouts. These are pure contracts and predicates; live SQL/storage/HTTP/build/controller/isolation producers remain later tasks. Existing four delivery plus one reserve days, dependencies and all gates are unchanged.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-01-d"></a>


### SP-01.d — Freeze world, SSE and replay contracts

- **Objective:** Give producers and consumers stable, testable interfaces before parallel implementation. This PR delivers freeze world, sse and replay contracts.
- **Implementation scope:** Specify worlds/versioning, author/agent views, SSE sequence, cursor expiry and snapshot/archive resync.
- **Out of scope:** API producer or UI implementation.
- **Prerequisites and dependencies:** [SP-01.b](#sp-01-b), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Backend/frontend/security approve exact fields and recovery semantics.
- **Required automated tests:** Duplicate/gap/reordered/expired stream, revocation and partial-replay fixtures.
- **Security and reliability:** Resync reauthorizes caller/run; no blind truth in active feed.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Backend, SDK, frontend, Platform, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; complete, issue #94. WORLD1 PR #95 and WEB1 PR #97 passed independent review, exact PR/main checks and private package verification. Hosted producers remain later work.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-01-e"></a>
### SP-01.e — Pin validation, clients and deterministic mocks

- **Objective:** Give producers and consumers stable, testable interfaces before parallel implementation. This PR delivers pin validation, clients and deterministic mocks.
- **Implementation scope:** Pin contract tooling; generate Python/TS fixtures, drift checks and mock server/recorded streams.
- **Out of scope:** Mocks as proof of deployed security.
- **Prerequisites and dependencies:** [SP-01.a](#sp-01-a), [SP-01.b](#sp-01-b), [SP-01.c](#sp-01-c), [SP-01.d](#sp-01-d), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-SCI](#contract-sci), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Clean install regenerates approved subsets without drift.
- **Required automated tests:** CI structural/runtime fixtures, client compatibility and version rejection. Cross-language fixtures must cover Unicode/defaults, float formatting boundaries, signed zero, uint64 decimal strings and opaque JSON numeric identity. Raw artifact SHA verification uses original bytes; typed SCI recomputation must match the frozen profile rather than ordinary JavaScript serialization.
- **Security and reliability:** Synthetic data only; draft routes excluded from freeze.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Backend, SDK, frontend, Research, QE, Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; in progress, issue #98. All five actual prerequisites are complete. Quality owns VAL1 manifest/fixtures before generator implementation; CLIENT1 and MOCK1 follow as separately reviewed units.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-02"></a>
## SP-02 — Verify cloud and workspace prerequisites

Parent: [#4](https://github.com/spei04/strange-physics/issues/4). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-02-a"></a>
### SP-02.a — Verify cloud, credit and quota prerequisites

- **Objective:** Make development and deployment prerequisites concrete, affordable and safe to use. This PR delivers verify cloud, credit and quota prerequisites.
- **Implementation scope:** Read-only region, billing credit coverage/expiry, organization policy, IAM and quota preflight; retain private evidence.
- **Out of scope:** Provisioning or purchases.
- **Prerequisites and dependencies:** [SP-00.a](#sp-00-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Dated service go/no-go and remediation owners; no guessed eligibility.
- **Required automated tests:** Validate sanitized checklist against actual cloud readbacks.
- **Security and reliability:** No account IDs/secrets in public output.
- **Effort and confidence:** 2 delivery engineer-days; medium confidence; +0.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed for stated scope; evidence in EXECUTION_LOG.md.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-02-b"></a>
### SP-02.b — Recover safe workspace headroom

- **Objective:** Make development and deployment prerequisites concrete, affordable and safe to use. This PR delivers recover safe workspace headroom.
- **Implementation scope:** Inventory active consumers/archives; perform only approved resize or verified reproducible-cache cleanup.
- **Out of scope:** Deleting migration archives, active worktrees or recreating project on Mac.
- **Prerequisites and dependencies:** [SP-02.a](#sp-02-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** At least 20 GiB free or measured larger build need; needed consumers preserved.
- **Required automated tests:** Free-space, consumer-path and dependency-integrity readbacks.
- **Security and reliability:** Capacity restored with independently verified ~96.96 GiB free; maintain the 20 GiB gate and preserve active consumers.
- **Effort and confidence:** 2 delivery engineer-days; medium confidence; +0.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; completed after approved online expansion and independent acceptance on 2026-10-20; evidence and limitations in EXECUTION_LOG.md, issue #72.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-02-c"></a>
### SP-02.c — Approve a priced staging configuration

- **Objective:** Make development and deployment prerequisites concrete, affordable and safe to use. This PR delivers approve a priced staging configuration.
- **Implementation scope:** Resolve region/runtime/project configuration and capped trial estimate; obtain provisioning authorization.
- **Out of scope:** Production rollout or unbounded sweep.
- **Prerequisites and dependencies:** [SP-02.a](#sp-02-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Concrete design, permissions and spending cap approved.
- **Required automated tests:** Configuration/policy and cost-dimension checks.
- **Security and reliability:** Credit is not unlimited spend; unsupported combinations block.
- **Effort and confidence:** 2 delivery engineer-days; low confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R0; in progress. Priced proposal saved in STAGING_PROPOSAL.md at 0eba987; approximately $450–550/month low traffic, proposed seven-day $250 operational envelope, neither approved. Target project/credit/IAM/quota facts, exact IaC and concrete authorization remain gates; no provisioning.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.


<a id="epic-sp-03"></a>
## SP-03 — Validate numerical domain and baseline

Parent: [#5](https://github.com/spei04/strange-physics/issues/5). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-03-a"></a>
### SP-03.a — Extend independent analytic physics fixtures

- **Objective:** Ensure numerical results and supported interventions are scientifically defensible. This PR delivers extend independent analytic physics fixtures.
- **Implementation scope:** Add oscillator/drag/rotation references and independent mass/impulse/force invariants.
- **Out of scope:** New integrator or fitter.
- **Prerequisites and dependencies:** [SP-00.b](#sp-00-b), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Existing solver agrees with analytic cases without changing study distributions.
- **Required automated tests:** Analytic trajectories, reciprocity, rotation and applicable energy tests.
- **Security and reliability:** Do not export hidden law state or clip failures.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; completed with independently accepted source 66016cf, 53 new cases and 613 local tests; exact-head CI is required before integration. See NUMERICAL_VALIDATION.md and issue #73.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-03-b"></a>
### SP-03.b — Ratify first-spring domain and tolerances

- **Objective:** Ensure numerical results and supported interventions are scientifically defensible. This PR delivers ratify first-spring domain and tolerances.
- **Implementation scope:** Calibrate excitation/mass cases, timestep refinements and conditioning.
- **Out of scope:** Full-family calibration.
- **Prerequisites and dependencies:** [SP-03.a](#sp-03-a), [SP-01.a](#sp-01-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Ratify or justify ≤1% coefficient error and ≤0.001 position RMSE over two seconds before fit acceptance.
- **Required automated tests:** Analytic convergence, zero excitation and mass/order boundary fixtures.
- **Security and reliability:** Failed tests require numerical justification, not arbitrary loosening.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, SDK, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; completed through PR #78/main db18278821d72d3ba02336e45827d441af0a00b6, tree08efb975 matching reviewed7b27bad. PR CI39358928012 and main CI39359050024 passed. All 70 primary/mixed-mass noiseless prefixes meet the preregistered joint bounds; 13/64 noisy prefixes pass, failures retained. 817 full tests and 204 focused cases/static checks pass. See SPRING_DOMAIN.md; no production fitter/predictor/scorer claim.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-03-c"></a>
### SP-03.c — Validate all-family numerical domains

- **Objective:** Ensure numerical results and supported interventions are scientifically defensible. This PR delivers validate all-family numerical domains.
- **Implementation scope:** Cover 1/3/8 particles, legal bounds, coefficient/term changes and stable extrapolation; report identifiability.
- **Out of scope:** Arbitrary new law families.
- **Prerequisites and dependencies:** [SP-03.b](#sp-03-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Versioned supported domain preserves unstable/unidentifiable case counts.
- **Required automated tests:** Convergence, radial near-origin, weak excitation and failure matrices.
- **Security and reliability:** No redraw or family-label leakage.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, SDK, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-03-d"></a>
### SP-03.d — Profile simulation and failure costs

- **Objective:** Ensure numerical results and supported interventions are scientifically defensible. This PR delivers profile simulation and failure costs.
- **Implementation scope:** Measure CPU/memory/output across supported worlds and failures; record exact environment/config.
- **Out of scope:** 100-run deployment.
- **Prerequisites and dependencies:** [SP-03.c](#sp-03-c), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Reproducible p50/p95 profiles and proposed execution caps.
- **Required automated tests:** Profiling harness, bounded divergence and output-size tests.
- **Security and reliability:** Private true-world diagnostics; microbenchmarks are not capacity evidence.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, SDK, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-04"></a>
## SP-04 — Implement integrated sparse fitter

Parent: [#6](https://github.com/spei04/strange-physics/issues/6). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-04-a"></a>
### SP-04.a — Fit a spring using purchased observations

- **Objective:** Turn purchased observations into inspectable predictive models with explicit failure behavior. This PR delivers fit a spring using purchased observations.
- **Implementation scope:** Fit integrated velocity increments using public masses and valid records; emit coefficient/provenance and conditioning.
- **Out of scope:** Sparse full-family fitting.
- **Prerequisites and dependencies:** [SP-03.b](#sp-03-b), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Analytic fixture meets ratified error; insufficient excitation explicitly fails.
- **Required automated tests:** Coefficient recovery, rank deficiency, order/mass mismatch and no hidden input.
- **Security and reliability:** No evaluator access; bounded compute and safe diagnostics.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; completed through PR #80/main e5a3c8d, reviewed head833d8c7 and matching treecbe89e1d. PR CI39360722931 and main CI39360858087 passed. 1,006 integrated tests, lint/format, strict typing and492 schema checks pass. Fitting only; prediction/scoring/I1 remain later tasks.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-04-b"></a>
### SP-04.b — Predict with the versioned spring model

- **Objective:** Turn purchased observations into inspectable predictive models with explicit failure behavior. This PR delivers predict with the versioned spring model.
- **Implementation scope:** Validate model/hash/runtime and propagate unseen initial conditions with ordered finite outputs.
- **Out of scope:** Executable hosted predictor.
- **Prerequisites and dependencies:** [SP-04.a](#sp-04-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Independent analytic prediction meets ratified bound.
- **Required automated tests:** Serialization, shuffled IDs, reversed times, tampered hashes and divergence.
- **Security and reliability:** Bound output; no pickle or true simulator parameters.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; completed for the bounded spring predictor. PR #82/main 9c341f8 matches reviewed d37118e/tree 4d33a099, with passing PR/main CI. 1,320 full tests and all 1,680 fit-to-predict probes pass. SP-06.a and SP-04.e/I1 remain separate.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-04-c"></a>
### SP-04.c — Implement disclosed integrated feature dictionary

- **Objective:** Turn purchased observations into inspectable predictive models with explicit failure behavior. This PR delivers implement disclosed integrated feature dictionary.
- **Implementation scope:** Implement spring, velocity/rotation, constant and radial-grid graph features with integrated increments.
- **Out of scope:** Automatic feature search.
- **Prerequisites and dependencies:** [SP-04.b](#sp-04-b), [SP-03.c](#sp-03-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Dictionary/version identical for every selector.
- **Required automated tests:** Hand-computed features, reciprocal graph terms, mass scaling and exponent grid.
- **Security and reliability:** No family/exponent oracle; cap feature count.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-04-d"></a>
### SP-04.d — Implement sparse fitting and model persistence

- **Objective:** Turn purchased observations into inspectable predictive models with explicit failure behavior. This PR delivers implement sparse fitting and model persistence.
- **Implementation scope:** Add development-fixed regularization, support selection, degeneracy diagnostics and immutable models.
- **Out of scope:** Ensembles or acquisition.
- **Prerequisites and dependencies:** [SP-04.c](#sp-04-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Supported mixtures meet predeclared development tolerances; unsupported fits explicit.
- **Required automated tests:** Mixture recovery, noisy/rank-deficient cases, serialization and runtime mismatch.
- **Security and reliability:** Bound fitting work; no evaluation tuning.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-04-e"></a>
### SP-04.e — Deliver local fit-predict-score SDK and CLI

- **Objective:** Turn purchased observations into inspectable predictive models with explicit failure behavior. This PR delivers deliver local fit-predict-score sdk and cli.
- **Implementation scope:** Wire typed artifacts into SDK/CLI reproduction with durations and failure classes.
- **Out of scope:** Hosted product or official score.
- **Prerequisites and dependencies:** [SP-04.b](#sp-04-b), [SP-06.a](#sp-06-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** One command sequence completes independent single-spring development scoring.
- **Required automated tests:** CLI round-trip, corrupt artifacts and independent report assertions.
- **Security and reliability:** Trusted local and development-only labels; no provider dependency.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; complete for bounded local I1. PR #90/main d931158 matches accepted8336ca5/treee3198a56; required PR CI39368869540 and all five main CI39369037416 jobs passed. Integrated1,771 tests; installed-wheel CLI4 purchases and known-k SDK fixture each retain24/24 independent scores with every probe within0.001 RMSE. Broader research and hosted gates remain.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-05"></a>
## SP-05 — Add uncertainty, adaptation and active selection

Parent: [#7](https://github.com/spei04/strange-physics/issues/7). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-05-a"></a>


### SP-05.a — Bootstrap complete experiments

- **Objective:** Measure adaptive experiment selection and uncertainty without privileged information. This PR delivers bootstrap complete experiments.
- **Implementation scope:** Resample experiments, propagate ensembles and record support/coverage metadata.
- **Out of scope:** Acquisition or blind calibration.
- **Prerequisites and dependencies:** [SP-04.d](#sp-04-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Never resample frames as independent; low support explicit.
- **Required automated tests:** Deterministic samples, correlated-frame guard and coverage fixtures.
- **Security and reliability:** Disagreement is not calibrated confidence; cap compute.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-05-b"></a>
### SP-05.b — Generate identical candidate banks

- **Objective:** Measure adaptive experiment selection and uncertainty without privileged information. This PR delivers generate identical candidate banks.
- **Implementation scope:** Generate seeded 128-candidate banks and four shared calibration experiments.
- **Out of scope:** LLM integration.
- **Prerequisites and dependencies:** [SP-04.d](#sp-04-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Candidate identities and budgets match across selectors.
- **Required automated tests:** Bounds, noise/seed separation and calibration accounting.
- **Security and reliability:** No true change signal or free measurements.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-05-c"></a>
### SP-05.c — Implement declared adaptation policies

- **Objective:** Measure adaptive experiment selection and uncertainty without privileged information. This PR delivers implement declared adaptation policies.
- **Implementation scope:** Implement all-history/window/detector reset from pre-experiment residuals with checkpointable state.
- **Out of scope:** Gradual-drift track.
- **Prerequisites and dependencies:** [SP-05.a](#sp-05-a), [SP-05.b](#sp-05-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Policies use purchased history only; thresholds versioned.
- **Required automated tests:** Stationary alarms, replay, recovery boundaries and hidden-marker rejection.
- **Security and reliability:** Oracle reset diagnostic only; preserve failed experiments.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-05-d"></a>
### SP-05.d — Select experiments by bounded disagreement

- **Objective:** Measure adaptive experiment selection and uncertainty without privileged information. This PR delivers select experiments by bounded disagreement.
- **Implementation scope:** Rank shared candidates within CPU budget; log ties and explicit fallbacks.
- **Out of scope:** Superiority claim.
- **Prerequisites and dependencies:** [SP-05.c](#sp-05-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Random and active use identical fit/adaptation inputs.
- **Required automated tests:** Tie, timeout, low support and candidate parity fixtures.
- **Security and reliability:** Bound fallback/retries; no uncharged simulations.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-06"></a>
## SP-06 — Implement held-out metrics and failure policy

Parent: [#8](https://github.com/spei04/strange-physics/issues/8). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-06-a"></a>
### SP-06.a — Compute independent development reports

- **Objective:** Produce unbiased, reproducible generalization and recovery measurements. This PR delivers compute independent development reports.
- **Implementation scope:** Score analytic spring predictions with fixed normalization, counts and report hashes.
- **Out of scope:** Full benchmark penalty freeze.
- **Prerequisites and dependencies:** [SP-04.b](#sp-04-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Hand-calculated MSE/normalized MSE/counts match the SCI report; sqrt(position_mse) supplies the ratified RMSE acceptance check; missing output remains failure and unscorable.
- **Required automated tests:** Known errors, all invalid/missing output, normalization and tamper cases.
- **Security and reliability:** Separate evaluator labels from fitter; report failures.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; complete through PR #85/main c20e3b5, matching reviewed3556088 and treecad9249f. Required PR CI39365261896 and all protected-main CI39365449219 jobs passed;1,531 integrated tests. Independent97 focused cases,7 boundary checks and7 mutants. SP-04.e SDK/CLI subsequently completed through PR #90; bounded I1 is accepted.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-06-b"></a>
### SP-06.b — Generate restricted held-out probe banks

- **Objective:** Produce unbiased, reproducible generalization and recovery measurements. This PR delivers generate restricted held-out probe banks.
- **Implementation scope:** Create disjoint splits, paired 32+32 per-regime banks and visibility-tagged manifests.
- **Out of scope:** Hosted isolation.
- **Prerequisites and dependencies:** [SP-03.c](#sp-03-c), [SP-06.a](#sp-06-a), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Seed/world sets disjoint and paired methods share probes.
- **Required automated tests:** Collision, pairing, stable extrapolation and leak fixtures.
- **Security and reliability:** No reconstructible seed to agent; public is not blind.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-06-c"></a>
### SP-06.c — Score penalties and censored recovery

- **Objective:** Produce unbiased, reproducible generalization and recovery measurements. This PR delivers score penalties and censored recovery.
- **Implementation scope:** Implement development penalty, 16-step recovery fraction and restricted latency with all failures included.
- **Out of scope:** Official scored release.
- **Prerequisites and dependencies:** [SP-06.b](#sp-06-b), [SP-04.d](#sp-04-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Crashing cannot improve primary score; unlearned/nonrecovering worlds retained.
- **Required automated tests:** Hand-counted censoring, boundary changes, all-failure and penalty sensitivity.
- **Security and reliability:** No successful-only ranking.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-06-d"></a>
### SP-06.d — Aggregate paired independent worlds

- **Objective:** Produce unbiased, reproducible generalization and recovery measurements. This PR delivers aggregate paired independent worlds.
- **Implementation scope:** Aggregate seeds inside world, bootstrap worlds and report family/condition strata plus declared macro weights.
- **Out of scope:** Interpreting uncollected results.
- **Prerequisites and dependencies:** [SP-06.c](#sp-06-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Counts reconcile; paired estimates and intervals reproduce.
- **Required automated tests:** Hand aggregates, missing/duplicate seeds and world-versus-frame resampling.
- **Security and reliability:** Avoid pseudoreplication; disclose exclusions.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-07"></a>
## SP-07 — Calibrate and draft frozen study manifests

Parent: [#9](https://github.com/spei04/strange-physics/issues/9). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-07-a"></a>
### SP-07.a — Calibrate uncertainty and adaptation

- **Objective:** Choose study settings from development evidence before official evaluation. This PR delivers calibrate uncertainty and adaptation.
- **Implementation scope:** Run capped development studies of noise, regularization, thresholds, coverage and recovery.
- **Out of scope:** Official freeze.
- **Prerequisites and dependencies:** [SP-05.d](#sp-05-d), [SP-06.d](#sp-06-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Candidate settings have sensitivity and negative-result evidence.
- **Required automated tests:** Small CI calibration and reproducible larger development harness.
- **Security and reliability:** No evaluation tuning; failed validity can halt release.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-07-b"></a>
### SP-07.b — Profile complete ensemble evaluation

- **Objective:** Choose study settings from development evidence before official evaluation. This PR delivers profile complete ensemble evaluation.
- **Implementation scope:** Measure snapshots×probes×ensemble workload, failures and limits; update compute model.
- **Out of scope:** Production capacity or GPU training.
- **Prerequisites and dependencies:** [SP-07.a](#sp-07-a), [SP-03.d](#sp-03-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** 40×64 rollout count and ensemble multiplier explicit.
- **Required automated tests:** Repeatable count, timeout, memory and estimator checks.
- **Security and reliability:** Do not size from simulator-only timing.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Platform, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-07-c"></a>
### SP-07.c — Choose study size from precision evidence

- **Objective:** Choose study settings from development evidence before official evaluation. This PR delivers choose study size from precision evidence.
- **Implementation scope:** Estimate paired variance and precision; propose world/seed allocation, stopping and capped cost.
- **Out of scope:** Launching paid evaluation.
- **Prerequisites and dependencies:** [SP-07.a](#sp-07-a), [SP-07.b](#sp-07-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Independent review of justified size; 2430 episodes stays illustrative.
- **Required automated tests:** Interval-precision simulations and count/manifest checks.
- **Security and reliability:** Do not tune study to favor a selector.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-07-d"></a>
### SP-07.d — Version both candidate research protocols

- **Objective:** Choose study settings from development evidence before official evaluation. This PR delivers version both candidate research protocols.
- **Implementation scope:** Complete controlled/discovery resource, snapshot, failure and visibility manifests.
- **Out of scope:** Collecting/publishing reference results.
- **Prerequisites and dependencies:** [SP-07.c](#sp-07-c), [SP-06.d](#sp-06-d), [SP-19.a](#sp-19-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Both tracks have reviewed candidate versions and immutable identities.
- **Required automated tests:** Manifest, hash and cross-track mixing rejection.
- **Security and reliability:** Candidate review is not official scoring approval.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Platform, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R1; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-08"></a>
## SP-08 — Build identity and workspace memberships

Parent: [#10](https://github.com/spei04/strange-physics/issues/10). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-08-a"></a>
### SP-08.a — Verify OIDC identities and sessions

- **Objective:** Provide private workspaces and usable human/machine authentication. This PR delivers verify oidc identities and sessions.
- **Implementation scope:** Implement issuer/audience/signature/expiry verification and session lifecycle; separate hosted and generic OIDC configuration.
- **Out of scope:** Excludes SP-08.b implement workspaces, invitations and roles; SP-08.c issue scoped machine and run credentials; SP-08.d implement secure browser authentication endpoints. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.b](#sp-01-b), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Forged/wrong-issuer/expired tokens denied; logout and key rotation behavior defined.
- **Required automated tests:** Fake issuer, key rollover, nonce/state/CSRF and token validation tests.
- **Security and reliability:** No email-domain membership; safe token errors.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-08-b"></a>
### SP-08.b — Implement workspaces, invitations and roles

- **Objective:** Provide private workspaces and usable human/machine authentication. This PR delivers implement workspaces, invitations and roles.
- **Implementation scope:** Add owner/researcher/viewer memberships, single-use expiring invites and explicit identity linking.
- **Out of scope:** Excludes SP-08.a verify oidc identities and sessions; SP-08.c issue scoped machine and run credentials; SP-08.d implement secure browser authentication endpoints. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-08.a](#sp-08-a), [SP-09.a](#sp-09-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-DB](#contract-db), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Role matrix enforced; sole-owner removal and invite replay rejected.
- **Required automated tests:** Concurrent accept, expiry, cross-workspace invite and account-linking tests.
- **Security and reliability:** Prevent role escalation and confused identity merges.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-08-c"></a>
### SP-08.c — Issue scoped machine and run credentials

- **Objective:** Provide private workspaces and usable human/machine authentication. This PR delivers issue scoped machine and run credentials.
- **Implementation scope:** Implement hashed workspace service credentials plus short-lived audience/run/epoch tokens, rotation and revocation.
- **Out of scope:** Enterprise federation or SCIM.
- **Prerequisites and dependencies:** [SP-08.b](#sp-08-b), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** SDK can authenticate without browser; stale/wrong-run/expired credential denied.
- **Required automated tests:** Scope, rotation, epoch replay, revocation and credential redaction tests.
- **Security and reliability:** Platform provider secrets never enter token claims.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-08-d"></a>
### SP-08.d — Implement secure browser authentication endpoints

- **Objective:** Provide private workspaces and usable human/machine authentication. This PR delivers implement secure browser authentication endpoints.
- **Implementation scope:** Expose callback/session/logout and membership bootstrap with documented CORS/cookie/CSRF choices.
- **Out of scope:** Excludes SP-08.a verify oidc identities and sessions; SP-08.b implement workspaces, invitations and roles; SP-08.c issue scoped machine and run credentials. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-08.c](#sp-08-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Browser and API sessions agree on current role and revocation.
- **Required automated tests:** CSRF/origin, logout, refresh and session fixation tests.
- **Security and reliability:** Fail closed on unknown issuer or session state.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-09"></a>
## SP-09 — Implement run and experiment transactions

Parent: [#11](https://github.com/spei04/strange-physics/issues/11). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-09-a"></a>
### SP-09.a — Create tenant SQL schema and migration harness

- **Objective:** Preserve one logical experiment and budget debit under concurrency and failure. This PR delivers create tenant sql schema and migration harness.
- **Implementation scope:** Add versioned PostgreSQL migrations, composite tenant foreign keys and constraint/index fixtures.
- **Out of scope:** Excludes SP-09.b reserve experiments and budgets atomically; SP-09.c implement run and operation state transitions; SP-09.d connect trusted simulator results to run transactions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.b](#sp-01-b), [SP-02.b](#sp-02-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Schema enforces run/operation/ordinal uniqueness; rollback/forward behavior documented.
- **Required automated tests:** Real PostgreSQL fresh/upgrade, FK, unique and transaction tests.
- **Security and reliability:** Separate migration and runtime roles; parameterized access.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-09-b"></a>
### SP-09.b — Reserve experiments and budgets atomically

- **Objective:** Preserve one logical experiment and budget debit under concurrency and failure. This PR delivers reserve experiments and budgets atomically.
- **Implementation scope:** Commit validated request, ordinal, debit and outbox in one transaction; canonicalize operation keys.
- **Out of scope:** Excludes SP-09.a create tenant sql schema and migration harness; SP-09.c implement run and operation state transitions; SP-09.d connect trusted simulator results to run transactions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.a](#sp-09-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-HTTP](#contract-http), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Concurrent duplicate returns same logical result; changed request conflicts; invalid request not charged.
- **Required automated tests:** Parallel retries, crash boundaries, exhausted budget and hash-conflict tests.
- **Security and reliability:** No acknowledgement before durable commit; no duplicate debit.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend, Research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-09-c"></a>
### SP-09.c — Implement run and operation state transitions

- **Objective:** Preserve one logical experiment and budget debit under concurrency and failure. This PR delivers implement run and operation state transitions.
- **Implementation scope:** Add create/read/cancel/operation routes, revision checks, deadlines and terminal-state immutability.
- **Out of scope:** Excludes SP-09.a create tenant sql schema and migration harness; SP-09.b reserve experiments and budgets atomically; SP-09.d connect trusted simulator results to run transactions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.b](#sp-09-b), [SP-08.b](#sp-08-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Legal transitions and async cancellation observable; unauthorized IDs hidden.
- **Required automated tests:** Race cancel/complete/expire, stale revision and cross-tenant operation tests.
- **Security and reliability:** Accepting cancel is not proof worker stopped.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-09-d"></a>
### SP-09.d — Connect trusted simulator results to run transactions

- **Objective:** Preserve one logical experiment and budget debit under concurrency and failure. This PR delivers connect trusted simulator results to run transactions.
- **Implementation scope:** Adapt public observations to durable result commits and safe numerical failure records.
- **Out of scope:** Excludes SP-09.a create tenant sql schema and migration harness; SP-09.b reserve experiments and budgets atomically; SP-09.c implement run and operation state transitions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.c](#sp-09-c), [SP-01.a](#sp-01-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-DB](#contract-db), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** One accepted experiment has one terminal result/debit and no hidden parameter fields.
- **Required automated tests:** Schema parity, failed integration, duplicate result and malicious error-message tests.
- **Security and reliability:** Trusted simulator identity separate from user code.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Research, SDK, Backend, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

- **Execution constraint (ledger scaling):** Persist immutable observation body identity/hash with authoritative tenant/run/operation/ordinal/status metadata. Production prefix checks use indexed, byte-capped metadata reads under a consistent run revision; they must not materialize complete trajectory history.
- **Additional production evidence:** Verify complete contiguous rows, unique operation IDs, scientific-failure inclusion, incomplete-operation stopping, body-commit/hash joins, concurrent append and bounded rows/bytes read.

<a id="epic-sp-10"></a>
## SP-10 — Add outbox, fencing and reconciliation

Parent: [#12](https://github.com/spei04/strange-physics/issues/12). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-10-a"></a>
### SP-10.a — Dispatch transactional outbox intents

- **Objective:** Recover remote work reliably despite duplicate delivery and stale workers. This PR delivers dispatch transactional outbox intents.
- **Implementation scope:** Implement short idempotent Cloud Tasks handlers, deterministic launch IDs and failed-dispatch records.
- **Out of scope:** Excludes SP-10.b fence worker leases and heartbeats; SP-10.c reconcile abandoned launches and results. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.d](#sp-09-d), [SP-27.c](#sp-27-c), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Duplicate/reordered/delayed delivery does not duplicate logical launch.
- **Required automated tests:** Duplicate delivery, crash after enqueue, retry exhaustion and replay tests.
- **Security and reliability:** Queue never owns authoritative state; bounded retries.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, Platform, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-10-b"></a>
### SP-10.b — Fence worker leases and heartbeats

- **Objective:** Recover remote work reliably despite duplicate delivery and stale workers. This PR delivers fence worker leases and heartbeats.
- **Implementation scope:** Allocate monotonic epochs, renew leases and reject stale result/checkpoint commits.
- **Out of scope:** Excludes SP-10.a dispatch transactional outbox intents; SP-10.c reconcile abandoned launches and results. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.b](#sp-09-b), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Partitioned old worker cannot write after replacement lease.
- **Required automated tests:** Lease expiry, heartbeat race, clock-skew and stale-commit tests.
- **Security and reliability:** Use server timestamps and transaction guards.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, Platform, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-10-c"></a>
### SP-10.c — Reconcile abandoned launches and results

- **Objective:** Recover remote work reliably despite duplicate delivery and stale workers. This PR delivers reconcile abandoned launches and results.
- **Implementation scope:** Recover missed dispatch/expired leases and expose audited retry/deadline decisions.
- **Out of scope:** Excludes SP-10.a dispatch transactional outbox intents; SP-10.b fence worker leases and heartbeats. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-10.a](#sp-10-a), [SP-10.b](#sp-10-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-EXEC](#contract-exec), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Reconciliation converges without resurrecting terminal or cancelled runs.
- **Required automated tests:** Process death, orphan launch, terminal race and replay idempotency tests.
- **Security and reliability:** Retry bounded by run deadline; no invisible restart.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, Platform, security, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-11"></a>
## SP-11 — Enforce tenant and artifact authorization

Parent: [#13](https://github.com/spei04/strange-physics/issues/13). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-11-a"></a>
### SP-11.a — Enforce tenant row policies and safe pool reuse

- **Objective:** Prevent cross-tenant access and honor current authorization on every surface. This PR delivers enforce tenant row policies and safe pool reuse.
- **Implementation scope:** Apply RLS to tenant tables with nonowner runtime role and transaction-local tenant context.
- **Out of scope:** Excludes SP-11.b authorize every operation and artifact reference; SP-11.c enforce live revocation and audit decisions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-08.b](#sp-08-b), [SP-09.d](#sp-09-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Cross-tenant reads/writes denied even under omitted filter and pooled reuse.
- **Required automated tests:** Role-bypass, unset context, FK traversal and connection reuse tests.
- **Security and reliability:** Runtime cannot own tables or bypass RLS.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-11-b"></a>
### SP-11.b — Authorize every operation and artifact reference

- **Objective:** Prevent cross-tenant access and honor current authorization on every surface. This PR delivers authorize every operation and artifact reference.
- **Implementation scope:** Centralize scoped route/object policy, property allowlists and nonenumerating denied lookup.
- **Out of scope:** Excludes SP-11.a enforce tenant row policies and safe pool reuse; SP-11.c enforce live revocation and audit decisions. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-11.a](#sp-11-a), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-ID](#contract-id), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Every route/field has role decision; hashes alone confer no access.
- **Required automated tests:** Endpoint/ID substitution, mass assignment and future-object policy fixtures.
- **Security and reliability:** Signed access grants short-lived and authorized; no raw bucket access.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend, security, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-11-c"></a>
### SP-11.c — Enforce live revocation and audit decisions

- **Objective:** Prevent cross-tenant access and honor current authorization on every surface. This PR delivers enforce live revocation and audit decisions.
- **Implementation scope:** Check current membership/credential status on requests and before every SSE payload batch; reauthorize idle connections at most 30 seconds apart.
- **Out of scope:** SCIM provisioning.
- **Prerequisites and dependencies:** [SP-11.b](#sp-11-b), [SP-08.c](#sp-08-c), [SP-01.d](#sp-01-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Revoked caller denied new work; current authoritative checks before every payload batch; idle reauthorization ≤30 seconds.
- **Required automated tests:** Revocation races, stale token, sole-owner and safe audit/redaction tests.
- **Security and reliability:** No stale membership cache bypass.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security, SDK, frontend, Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-12"></a>
## SP-12 — Implement quotas and usage accounting

Parent: [#14](https://github.com/spei04/strange-physics/issues/14). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-12-a"></a>
### SP-12.a — Reserve and settle resource allowances

- **Objective:** Bound resource consumption and account for usage fairly across tenants. This PR delivers reserve and settle resource allowances.
- **Implementation scope:** Add atomic run/workspace CPU, token, artifact and execution reservations with attempt linkage.
- **Out of scope:** Excludes SP-12.b implement fair bounded admission; SP-12.c expose usage reconciliation and safe summaries. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-09.b](#sp-09-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No concurrent budget overspend; unknown amounts remain explicit.
- **Required automated tests:** Parallel exhaustion, partial settlement, negative amount and crash-retry tests.
- **Security and reliability:** Limit enforcement independent of agent honesty.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

- **Execution constraint (ledger scaling):** Enforce cumulative scientific/output/artifact allowances across attempts and before decoding/materializing data. Per-launch ceilings and a maximum experiment count do not establish a bounded run footprint.
- **Additional production evidence:** Verify replacement cannot reset allowances, unknown amounts remain reserved, and configured input/output byte limits reject before oversized allocation without silent truncation.

<a id="sp-12-b"></a>
### SP-12.b — Implement fair bounded admission

- **Objective:** Bound resource consumption and account for usage fairly across tenants. This PR delivers implement fair bounded admission.
- **Implementation scope:** Separate build, run and evaluation queues; workspace caps and weighted admission with bounded backlog.
- **Out of scope:** Excludes SP-12.a reserve and settle resource allowances; SP-12.c expose usage reconciliation and safe summaries. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-12.a](#sp-12-a), [SP-10.c](#sp-10-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-DB](#contract-db), [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** One tenant cannot monopolize slots; overload yields explicit queued/429 outcome.
- **Required automated tests:** Starvation, burst, cancellation release and scheduler replay tests.
- **Security and reliability:** No unbounded in-memory queue or silent dropping.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-12-c"></a>
### SP-12.c — Expose usage reconciliation and safe summaries

- **Objective:** Bound resource consumption and account for usage fairly across tenants. This PR delivers expose usage reconciliation and safe summaries.
- **Implementation scope:** Create usage query API and reconciler for reserved/settled/unknown amounts and attributable costs.
- **Out of scope:** Excludes SP-12.a reserve and settle resource allowances; SP-12.b implement fair bounded admission. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-12.b](#sp-12-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-DB](#contract-db), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Totals reconcile to immutable attempts without claiming estimated costs as billed.
- **Required automated tests:** Sum/replay/missing usage, tenant access and pagination tests.
- **Security and reliability:** No prompts or credentials in usage output.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, SDK, frontend, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R2; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-13"></a>
## SP-13 — Persist immutable artifacts and checkpoints

Parent: [#15](https://github.com/spei04/strange-physics/issues/15). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-13-a"></a>
### SP-13.a — Implement immutable content storage adapter

- **Objective:** Preserve durable, verifiable artifacts and complete checkpoints. This PR delivers implement immutable content storage adapter.
- **Implementation scope:** Write bounded hash/generation-verified objects and typed references behind portable storage interface.
- **Out of scope:** Excludes SP-13.b expose authorized artifact and package upload lifecycle; SP-13.c commit checkpoint and model references safely; SP-13.d collect abandoned uploads without deleting live state. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.c](#sp-01-c), [SP-27.c](#sp-27-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Corrupt/incomplete objects cannot become committed references.
- **Required automated tests:** Hash mismatch, conditional write, interrupted upload and storage outage tests.
- **Security and reliability:** Private buckets; no user-specified arbitrary filesystem path.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, backend, research, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-13-b"></a>
### SP-13.b — Expose authorized artifact and package upload lifecycle

- **Objective:** Preserve durable, verifiable artifacts and complete checkpoints. This PR delivers expose authorized artifact and package upload lifecycle.
- **Implementation scope:** Stage uploads, validate size/digest/media/archive metadata and expose operation status and authorized read path.
- **Out of scope:** Excludes SP-13.a implement immutable content storage adapter; SP-13.c commit checkpoint and model references safely; SP-13.d collect abandoned uploads without deleting live state. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-13.a](#sp-13-a), [SP-11.b](#sp-11-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-HTTP](#contract-http), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Only owner workspace can finalize/read; pending objects remain quarantined.
- **Required automated tests:** Traversal/decompression/oversize, expired grant and cross-tenant object tests.
- **Security and reliability:** Do not execute uploaded content; bounded reads.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, backend, research, Backend, SDK, frontend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-13-c"></a>
### SP-13.c — Commit checkpoint and model references safely

- **Objective:** Preserve durable, verifiable artifacts and complete checkpoints. This PR delivers commit checkpoint and model references safely.
- **Implementation scope:** Commit completed-prefix checkpoint/model references after durable object verification; enforce index/runtime rules.
- **Out of scope:** Excludes SP-13.a implement immutable content storage adapter; SP-13.b expose authorized artifact and package upload lifecycle; SP-13.d collect abandoned uploads without deleting live state. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-13.b](#sp-13-b), [SP-10.b](#sp-10-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-DB](#contract-db), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Crash between object and SQL leaves recoverable orphan, never missing committed artifact.
- **Required automated tests:** Write/commit crash matrix, hash tamper, stale epoch and prefix mismatch.
- **Security and reliability:** Agent state interpreted only in sandbox; bound JSON size.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, backend, research, Backend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

- **Execution constraint (ledger scaling):** Consume a reviewed internal transactional ledger closure, with exact body/hash and checkpoint/model joins. Native model prefix binding requires producer-verified canonical bundle identities or a bounded streaming hasher proven byte-equivalent to SCI; until available, reject over-limit input before allocation.
- **Additional production evidence:** Exercise missing/duplicate/gapped metadata, append races and exact canonical digest equivalence including scientific failures; verify reference commits and prefix evidence share a snapshot.

<a id="sp-13-d"></a>
### SP-13.d — Collect abandoned uploads without deleting live state

- **Objective:** Preserve durable, verifiable artifacts and complete checkpoints. This PR delivers collect abandoned uploads without deleting live state.
- **Implementation scope:** Implement grace-period reference scan, active-build/run guards and audited scratch cleanup.
- **Out of scope:** Excludes SP-13.a implement immutable content storage adapter; SP-13.b expose authorized artifact and package upload lifecycle; SP-13.c commit checkpoint and model references safely. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-13.c](#sp-13-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-DB](#contract-db), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Only unreferenced inactive objects removed; immutable retained artifacts remain.
- **Required automated tests:** Concurrent finalize, active lease, repeated cleanup and storage-error tests.
- **Security and reliability:** No broad bucket deletion; preserve legal/retention exceptions.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, backend, research, Backend, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-14"></a>
## SP-14 — Build packages in isolation

Parent: [#16](https://github.com/spei04/strange-physics/issues/16). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-14-a"></a>
### SP-14.a — Validate package manifests and safe extraction

- **Objective:** Build customer packages without exposing trusted deployment credentials. This PR delivers validate package manifests and safe extraction.
- **Implementation scope:** Validate pinned lockfiles, source digests, archive paths and build resource declarations.
- **Out of scope:** Excludes SP-14.b execute isolated quarantined builds; SP-14.c scan and promote digest-pinned runtime images; SP-14.d review hostile-build evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-13.b](#sp-13-b), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Invalid or unpinned packages fail before build; accepted source immutable.
- **Required automated tests:** Symlink/path escape, archive bomb, missing lock and digest-change tests.
- **Security and reliability:** Treat install hooks as arbitrary code.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-14-b"></a>
### SP-14.b — Execute isolated quarantined builds

- **Objective:** Build customer packages without exposing trusted deployment credentials. This PR delivers execute isolated quarantined builds.
- **Implementation scope:** Launch build sandbox with constrained dependency fetch, private scratch and no deploy/runtime credentials.
- **Out of scope:** Excludes SP-14.a validate package manifests and safe extraction; SP-14.c scan and promote digest-pinned runtime images; SP-14.d review hostile-build evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-14.a](#sp-14-a), [SP-27.d](#sp-27-d), [SP-15.b](#sp-15-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Build can access only approved mirror/registry paths; timeout and resource kill enforced.
- **Required automated tests:** Malicious install hooks, metadata/DNS/egress probes and exhaustion tests.
- **Security and reliability:** Never reuse trusted CI runner identity or mutable shared volume.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-14-c"></a>
### SP-14.c — Scan and promote digest-pinned runtime images

- **Objective:** Build customer packages without exposing trusted deployment credentials. This PR delivers scan and promote digest-pinned runtime images.
- **Implementation scope:** Produce provenance/SBOM, scan results and quarantine-to-approved transition tied to immutable digest.
- **Out of scope:** Excludes SP-14.a validate package manifests and safe extraction; SP-14.b execute isolated quarantined builds; SP-14.d review hostile-build evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-14.b](#sp-14-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-ART](#contract-art), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Only approved matching image launches; rejected scan stays quarantined.
- **Required automated tests:** Image substitution, unsigned provenance, stale scan and failed promotion tests.
- **Security and reliability:** Promotion identity cannot overwrite trusted base images.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-14-d"></a>
### SP-14.d — Review hostile-build evidence

- **Objective:** Build customer packages without exposing trusted deployment credentials. This PR delivers review hostile-build evidence.
- **Implementation scope:** Run malicious build corpus in staging and verify credential/network/storage boundaries plus cleanup.
- **Out of scope:** Excludes SP-14.a validate package manifests and safe extraction; SP-14.b execute isolated quarantined builds; SP-14.c scan and promote digest-pinned runtime images. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-14.c](#sp-14-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No secret/exfiltration path; failures block uploaded-code enablement.
- **Required automated tests:** End-to-end hostile hook, fork/disk exhaustion and poisoned cache tests.
- **Security and reliability:** Real environment evidence required; mocks insufficient.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-15"></a>
## SP-15 — Enforce sandbox runtime and broker policy

Parent: [#17](https://github.com/spei04/strange-physics/issues/17). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-15-a"></a>
### SP-15.a — Probe scientific runtime compatibility

- **Objective:** Enforce hostile-code isolation rather than relying on a container label. This PR delivers probe scientific runtime compatibility.
- **Implementation scope:** Run pinned NumPy/Pydantic/SciPy trial image in selected sandbox; measure syscall, filesystem and startup behavior.
- **Out of scope:** Broad product runtime.
- **Prerequisites and dependencies:** [SP-02.c](#sp-02-c), [SP-27.c](#sp-27-c), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Supported runtime/version documented or architecture decision reopened.
- **Required automated tests:** Scientific imports, deterministic fixture, limits and unsupported-runtime rejection.
- **Security and reliability:** No fallback to plain container when sandbox fails.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, security, backend, Research, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-15-b"></a>
### SP-15.b — Enforce sandbox and resource admission policy

- **Objective:** Enforce hostile-code isolation rather than relying on a container label. This PR delivers enforce sandbox and resource admission policy.
- **Implementation scope:** Require approved RuntimeClass, digest, read-only base, user/process/disk/CPU/memory/time limits; reject privileged mounts/tokens.
- **Out of scope:** Excludes SP-15.a probe scientific runtime compatibility; SP-15.c implement epoch-scoped run broker permissions; SP-15.d enforce broker-only network and dns; SP-15.e validate hostile-runtime isolation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-15.a](#sp-15-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Invalid pod configurations fail closed; bounded malicious workloads terminated.
- **Required automated tests:** Admission policy, runtime-unavailable, host mount, service-token and exhaustion tests.
- **Security and reliability:** Sandbox layer alone is insufficient; enforce full configuration.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-15-c"></a>
### SP-15.c — Implement epoch-scoped run broker permissions

- **Objective:** Enforce hostile-code isolation rather than relying on a container label. This PR delivers implement epoch-scoped run broker permissions.
- **Implementation scope:** Expose only allowed experiment/checkpoint/model-call operations with run/attempt-bound tokens.
- **Out of scope:** Excludes SP-15.a probe scientific runtime compatibility; SP-15.b enforce sandbox and resource admission policy; SP-15.d enforce broker-only network and dns; SP-15.e validate hostile-runtime isolation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-08.c](#sp-08-c), [SP-11.c](#sp-11-c), [SP-10.b](#sp-10-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-HTTP](#contract-http), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Agent cannot access full workspace API or another run/epoch.
- **Required automated tests:** Audience/scope/epoch substitution, expired token and terminal-run tests.
- **Security and reliability:** No provider/evaluator credentials or privileged diagnostic messages.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Platform, security, backend, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-15-d"></a>
### SP-15.d — Enforce broker-only network and DNS

- **Objective:** Enforce hostile-code isolation rather than relying on a container label. This PR delivers enforce broker-only network and dns.
- **Implementation scope:** Apply runtime egress/DNS/metadata policy and networkless predictor variant with independently verified routing.
- **Out of scope:** Excludes SP-15.a probe scientific runtime compatibility; SP-15.b enforce sandbox and resource admission policy; SP-15.c implement epoch-scoped run broker permissions; SP-15.e validate hostile-runtime isolation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-15.b](#sp-15-b), [SP-15.c](#sp-15-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Agent reaches broker only; predictor has no outbound path including DNS.
- **Required automated tests:** Metadata/private-IP/public-DNS/redirect/IPv6 and broker spoof tests.
- **Security and reliability:** Fail closed when policy unavailable; record policy version.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-15-e"></a>
### SP-15.e — Validate hostile-runtime isolation

- **Objective:** Enforce hostile-code isolation rather than relying on a container label. This PR delivers validate hostile-runtime isolation.
- **Implementation scope:** Run adversarial tenant/runtime corpus and verify process termination and credential separation.
- **Out of scope:** Excludes SP-15.a probe scientific runtime compatibility; SP-15.b enforce sandbox and resource admission policy; SP-15.c implement epoch-scoped run broker permissions; SP-15.d enforce broker-only network and dns. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-15.d](#sp-15-d), [SP-14.d](#sp-14-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Security reviewer signs exact deployed image/network/runtime evidence before uploads enabled.
- **Required automated tests:** Cross-run filesystem, secret probes, resource attack and stale-token tests.
- **Security and reliability:** Unresolved critical/high isolation issue blocks release.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-16"></a>
## SP-16 — Connect recoverable remote execution

Parent: [#18](https://github.com/spei04/strange-physics/issues/18). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-16-a"></a>
### SP-16.a — Coordinate one remote investigation

- **Objective:** Deliver recoverable, observable remote investigations with bounded cancellation. This PR delivers coordinate one remote investigation.
- **Implementation scope:** Connect launch, scoped broker, trusted simulation and committed result/checkpoint loop for one approved image.
- **Out of scope:** Excludes SP-16.b resume an agent from committed checkpoints; SP-16.c cancel, expire and reconcile remote work; SP-16.d prove end-to-end interruption invariants; SP-16.e instrument remote execution and recovery. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-10.c](#sp-10-c), [SP-12.c](#sp-12-c), [SP-13.c](#sp-13-c), [SP-14.d](#sp-14-d), [SP-15.e](#sp-15-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-DB](#contract-db), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Remote run produces same logical observations/budgets as trusted local fixture.
- **Required automated tests:** Local/remote conformance and one complete remote investigation.
- **Security and reliability:** Only approved image and current epoch launch.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Platform, security, backend, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-16-b"></a>
### SP-16.b — Resume an agent from committed checkpoints

- **Objective:** Deliver recoverable, observable remote investigations with bounded cancellation. This PR delivers resume an agent from committed checkpoints.
- **Implementation scope:** Restore declared state, replay committed-but-unobserved result and continue with immutable runtime.
- **Out of scope:** Excludes SP-16.a coordinate one remote investigation; SP-16.c cancel, expire and reconcile remote work; SP-16.d prove end-to-end interruption invariants; SP-16.e instrument remote execution and recovery. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.a](#sp-16-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-ART](#contract-art), [C-CORE](#contract-core); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Replacement never buys/debits an already committed experiment.
- **Required automated tests:** Kill before/after reserve/result/checkpoint with deterministic replay tests.
- **Security and reliability:** Incompatible runtime or corrupt checkpoint fails visibly.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, research, Research, SDK. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

- **Execution constraint (ledger scaling):** Restore through a reviewed internal compact ledger projection with explicit page/row/byte limits and the exact checkpoint target/latest closure. No client-supplied prefix scalar or full-trajectory materialization per restore. Payload delivery separately rechecks current read authority.
- **Additional production evidence:** Measure bounded bytes/rows under maximum supported history and concurrent append/recovery; reject missing body commits, gaps and stale snapshots while preserving initial -1 and committed scientific-failure semantics.

<a id="sp-16-c"></a>
### SP-16.c — Cancel, expire and reconcile remote work

- **Objective:** Deliver recoverable, observable remote investigations with bounded cancellation. This PR delivers cancel, expire and reconcile remote work.
- **Implementation scope:** Revoke launch/broker access, terminate attempts, reconcile held allowances and preserve accepted results.
- **Out of scope:** Excludes SP-16.a coordinate one remote investigation; SP-16.b resume an agent from committed checkpoints; SP-16.d prove end-to-end interruption invariants; SP-16.e instrument remote execution and recovery. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.b](#sp-16-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-DB](#contract-db), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** New work revoked ≤5s; controlled workers terminate ≤60s or explicit fault recorded.
- **Required automated tests:** Cancel/complete races, uncooperative agent, deadline and orphan reconciliation.
- **Security and reliability:** Do not refund pending usage before settlement.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, Backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-16-d"></a>
### SP-16.d — Prove end-to-end interruption invariants

- **Objective:** Deliver recoverable, observable remote investigations with bounded cancellation. This PR delivers prove end-to-end interruption invariants.
- **Implementation scope:** Automate process/network failures across commit boundaries in staging with repeated replacement.
- **Out of scope:** Excludes SP-16.a coordinate one remote investigation; SP-16.b resume an agent from committed checkpoints; SP-16.c cancel, expire and reconcile remote work; SP-16.e instrument remote execution and recovery. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.e](#sp-16-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-DB](#contract-db), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No lost acknowledged result or duplicate logical charge; p95 recovery target measured.
- **Required automated tests:** Forced-death matrix, partitioned stale worker and replay hash consistency.
- **Security and reliability:** Private exact-runtime evidence; failure blocks remote availability claims.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Platform, security, backend, Backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-16-e"></a>
### SP-16.e — Instrument remote execution and recovery

- **Objective:** Deliver recoverable, observable remote investigations with bounded cancellation. This PR delivers instrument remote execution and recovery.
- **Implementation scope:** Add bounded-cardinality launch/recovery/cancel metrics, correlated traces and stuck-run runbook dashboards.
- **Out of scope:** Excludes SP-16.a coordinate one remote investigation; SP-16.b resume an agent from committed checkpoints; SP-16.c cancel, expire and reconcile remote work; SP-16.d prove end-to-end interruption invariants. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.c](#sp-16-c), [SP-27.e](#sp-27-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Alerts detect a deliberately stuck run and identify epoch/operation without private payload.
- **Required automated tests:** Synthetic stuck/failed/cancelled runs and telemetry redaction assertions.
- **Security and reliability:** No run IDs as unbounded metric labels; trace access controlled.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-17"></a>
## SP-17 — Implement durable model-call ledger

Parent: [#19](https://github.com/spei04/strange-physics/issues/19). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-17-a"></a>
### SP-17.a — Freeze model-call and credential-management contracts

- **Objective:** Make model calls replayable and their potentially ambiguous costs visible. This PR delivers freeze model-call and credential-management contracts.
- **Implementation scope:** Specify logical call/attempt/ambiguous states, provider connection CRUD, token reservations and sanitized response replay.
- **Out of scope:** Provider code or paid calls.
- **Prerequisites and dependencies:** [SP-01.b](#sp-01-b), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Gateway/SDK/research/security approve schemas and timeout billing policy.
- **Required automated tests:** Good/bad/ambiguous fixtures, schema and no-secret response checks.
- **Security and reliability:** No user-selected arbitrary provider URL; exact policy version.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, research, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-17-b"></a>
### SP-17.b — Persist provider attempts and ambiguous usage

- **Objective:** Make model calls replayable and their potentially ambiguous costs visible. This PR delivers persist provider attempts and ambiguous usage.
- **Implementation scope:** Implement durable operation/attempt ledger and request/response artifacts with bounded retries and reconciliation.
- **Out of scope:** Excludes SP-17.a freeze model-call and credential-management contracts; SP-17.c manage workspace provider secrets; SP-17.d replay recorded model responses offline. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-17.a](#sp-17-a), [SP-12.c](#sp-12-c), [SP-13.c](#sp-13-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-DB](#contract-db), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Crash after send yields explicit ambiguity; identical key never creates hidden new attempt.
- **Required automated tests:** Send/commit timeout/crash, duplicate key and usage reconciliation tests.
- **Security and reliability:** External billing is not exactly-once; never blindly resend.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, research, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-17-c"></a>
### SP-17.c — Manage workspace provider secrets

- **Objective:** Make model calls replayable and their potentially ambiguous costs visible. This PR delivers manage workspace provider secrets.
- **Implementation scope:** Implement owner-only connect/test/rotate/revoke API with Secret Manager references and fixed approved destinations.
- **Out of scope:** Excludes SP-17.a freeze model-call and credential-management contracts; SP-17.b persist provider attempts and ambiguous usage; SP-17.d replay recorded model responses offline. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-17.a](#sp-17-a), [SP-11.c](#sp-11-c), [SP-27.c](#sp-27-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Keys only accessible to gateway identity; callers receive redacted status.
- **Required automated tests:** Cross-workspace access, revoked key, SSRF/redirect and logging tests.
- **Security and reliability:** Never return stored keys or place secrets in agent images.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, research, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-17-d"></a>
### SP-17.d — Replay recorded model responses offline

- **Objective:** Make model calls replayable and their potentially ambiguous costs visible. This PR delivers replay recorded model responses offline.
- **Implementation scope:** Return stored result for repeat operation; expose billed/estimated/unknown usage and explicit unresolved attempts.
- **Out of scope:** Excludes SP-17.a freeze model-call and credential-management contracts; SP-17.b persist provider attempts and ambiguous usage; SP-17.c manage workspace provider secrets. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-17.b](#sp-17-b), [SP-17.c](#sp-17-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Replay consumes no network/provider request; ambiguity persists until resolved.
- **Required automated tests:** Offline network-denial, response tamper, missing body and repeat replay tests.
- **Security and reliability:** Private prompts retained under run policy; no silent fallback.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, research, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-18"></a>
## SP-18 — Add bounded provider adapters and LLM selector

Parent: [#20](https://github.com/spei04/strange-physics/issues/20). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-18-a"></a>
### SP-18.a — Implement bounded provider transport

- **Objective:** Connect an LLM selector fairly and safely within declared compute limits. This PR delivers implement bounded provider transport.
- **Implementation scope:** Add approved provider/version adapter, token/rate budgets, timeouts, circuit breaker and bounded parsing.
- **Out of scope:** Excludes SP-18.b version the llm information transform; SP-18.c implement controlled llm candidate selection; SP-18.d validate a capped real-provider integration. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-17.d](#sp-17-d), [SP-15.c](#sp-15-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** 429/5xx/malformed responses have visible controlled outcomes without model substitution.
- **Required automated tests:** Fake provider retries/timeout/overflow/circuit and credential denial tests.
- **Security and reliability:** All attempts metered; request destinations fixed.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, research, security, Platform, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-18-b"></a>
### SP-18.b — Version the LLM information transform

- **Objective:** Connect an LLM selector fairly and safely within declared compute limits. This PR delivers version the llm information transform.
- **Implementation scope:** Define purchased-history/fit/candidate transform with context ceiling, truncation record and hypothesis annotations.
- **Out of scope:** Excludes SP-18.a implement bounded provider transport; SP-18.c implement controlled llm candidate selection; SP-18.d validate a capped real-provider integration. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-05.d](#sp-05-d), [SP-17.a](#sp-17-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-PROVIDER](#contract-provider); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Inputs contain same disclosed information and candidate set; transform version immutable.
- **Required automated tests:** Long history, injected annotation, hidden-field and token-ceiling fixtures.
- **Security and reliability:** Treat content as data; hypothesis text is not correctness evidence.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Backend, research, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-18-c"></a>
### SP-18.c — Implement controlled LLM candidate selection

- **Objective:** Connect an LLM selector fairly and safely within declared compute limits. This PR delivers implement controlled llm candidate selection.
- **Implementation scope:** Parse candidate-ID actions; bound invalid proposals to two retries then declared valid fallback.
- **Out of scope:** Excludes SP-18.a implement bounded provider transport; SP-18.b version the llm information transform; SP-18.d validate a capped real-provider integration. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-18.a](#sp-18-a), [SP-18.b](#sp-18-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-PROVIDER](#contract-provider); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Same calibration/fitter/adaptation/budget as other selectors; costs separately recorded.
- **Required automated tests:** Malformed/hallucinated ID, repeated invalid, budget exhaustion and checkpoint replay.
- **Security and reliability:** No unconstrained tool execution or privileged summaries.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Backend, research, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-18-d"></a>
### SP-18.d — Validate a capped real-provider integration

- **Objective:** Connect an LLM selector fairly and safely within declared compute limits. This PR delivers validate a capped real-provider integration.
- **Implementation scope:** Execute explicitly approved small trial with secret references and cap; compare latency/rate/usage to fake fixtures.
- **Out of scope:** Official suite or unlimited spend.
- **Prerequisites and dependencies:** [SP-18.c](#sp-18-c), [SP-17.c](#sp-17-c), [PAID_TRIAL](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PROVIDER](#contract-provider), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Recorded model/version, actual/unknown cost and failure evidence; no unbounded calls.
- **Required automated tests:** Automated cap-stop and response-schema verification plus offline replay.
- **Security and reliability:** Pricing/retention/credential owner sign-off required before calls.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Backend, research, security, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-19"></a>
## SP-19 — Define executable predictor packaging

Parent: [#21](https://github.com/spei04/strange-physics/issues/21). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-19-a"></a>
### SP-19.a — Freeze executable predictor protocol

- **Objective:** Accept executable predictive models under a strict untrusted-code contract. This PR delivers freeze executable predictor protocol.
- **Implementation scope:** Define immutable predictor packaging, batch/time/size limits, optional intervals and compatibility/determinism declarations.
- **Out of scope:** Implementing evaluation runner.
- **Prerequisites and dependencies:** [SP-01.a](#sp-01-a), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PRED](#contract-pred), [C-SCI](#contract-sci), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Research/platform/security sign complete prediction envelope and invalid-output policy.
- **Required automated tests:** Protocol good/bad shapes/timestamps/interval examples and compatibility fixtures.
- **Security and reliability:** No labels, true coefficients or evaluator credentials in request.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, platform, security, QE, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-19-b"></a>
### SP-19.b — Build predictor images through approved pipeline

- **Objective:** Accept executable predictive models under a strict untrusted-code contract. This PR delivers build predictor images through approved pipeline.
- **Implementation scope:** Package predictor entrypoint and immutable references; reuse quarantined build pipeline with approved base runtime.
- **Out of scope:** Excludes SP-19.a freeze executable predictor protocol; SP-19.c validate bounded predictor outputs; SP-19.d exercise hostile predictor fixtures. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-19.a](#sp-19-a), [SP-14.d](#sp-14-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PRED](#contract-pred), [C-EXEC](#contract-exec), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Predictor digest and protocol identity recorded and verified before invocation.
- **Required automated tests:** Digest substitution, missing entrypoint, lock mismatch and rejected build tests.
- **Security and reliability:** No separate less-secure build path.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Research, platform, security, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-19-c"></a>
### SP-19.c — Validate bounded predictor outputs

- **Objective:** Accept executable predictive models under a strict untrusted-code contract. This PR delivers validate bounded predictor outputs.
- **Implementation scope:** Validate finite/order/shape/time/interval outputs and enforce CPU/output envelope independently of predictor.
- **Out of scope:** Excludes SP-19.a freeze executable predictor protocol; SP-19.b build predictor images through approved pipeline; SP-19.d exercise hostile predictor fixtures. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-19.b](#sp-19-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PRED](#contract-pred), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Malformed/nonfinite/oversize results become explicit scored failures.
- **Required automated tests:** NaN, reordered particles, reversed times, invalid intervals and timeout fixtures.
- **Security and reliability:** Never deserialize executable objects in evaluator controller.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, platform, security, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-19-d"></a>
### SP-19.d — Exercise hostile predictor fixtures

- **Objective:** Accept executable predictive models under a strict untrusted-code contract. This PR delivers exercise hostile predictor fixtures.
- **Implementation scope:** Run malicious/malformed predictors in deployed networkless sandbox and verify no truth feedback.
- **Out of scope:** Excludes SP-19.a freeze executable predictor protocol; SP-19.b build predictor images through approved pipeline; SP-19.c validate bounded predictor outputs. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-19.c](#sp-19-c), [SP-15.e](#sp-15-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PRED](#contract-pred), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No filesystem/network/error side channel to restricted evaluator material.
- **Required automated tests:** Exfiltration, secret scan, timing/output overflow and process persistence tests.
- **Security and reliability:** Security reviewer inspects deployed evidence.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Research, platform, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-20"></a>
## SP-20 — Build independent evaluation execution

Parent: [#22](https://github.com/spei04/strange-physics/issues/22). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-20-a"></a>
### SP-20.a — Isolate evaluation truth and job ownership

- **Objective:** Score models without disclosing hidden evaluation truth to active agents. This PR delivers isolate evaluation truth and job ownership.
- **Implementation scope:** Create evaluator-only storage/identity and snapshot job metadata with separate quota and access.
- **Out of scope:** Excludes SP-20.b run networkless predictor jobs; SP-20.c persist complete snapshot scoring; SP-20.d audit evaluation information flow. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-06.b](#sp-06-b), [SP-13.d](#sp-13-d), [SP-27.c](#sp-27-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-ART](#contract-art), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Agent, viewer and gateway roles cannot read blind world/probe state.
- **Required automated tests:** IAM/role substitution, object enumeration and misconfigured startup tests.
- **Security and reliability:** Explicitly public suites separated from blind/customer data.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Research, QE, Platform, backend, research, Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-20-b"></a>
### SP-20.b — Run networkless predictor jobs

- **Objective:** Score models without disclosing hidden evaluation truth to active agents. This PR delivers run networkless predictor jobs.
- **Implementation scope:** Stage only public predictor inputs, execute bounded jobs and collect outputs under trusted controller.
- **Out of scope:** Excludes SP-20.a isolate evaluation truth and job ownership; SP-20.c persist complete snapshot scoring; SP-20.d audit evaluation information flow. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-20.a](#sp-20-a), [SP-19.d](#sp-19-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-PRED](#contract-pred), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Truth stays outside sandbox; duplicate job yields one authoritative output.
- **Required automated tests:** Predictor death, deadline, duplicate launch and input/output staging tests.
- **Security and reliability:** No feedback or long-lived evaluator credentials in sandbox.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Research, platform, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-20-c"></a>
### SP-20.c — Persist complete snapshot scoring

- **Objective:** Score models without disclosing hidden evaluation truth to active agents. This PR delivers persist complete snapshot scoring.
- **Implementation scope:** Score required snapshots/probes with immutable manifests, failures and evaluator queue/cost telemetry.
- **Out of scope:** Excludes SP-20.a isolate evaluation truth and job ownership; SP-20.b run networkless predictor jobs; SP-20.d audit evaluation information flow. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-20.b](#sp-20-b), [SP-06.d](#sp-06-d), [SP-07.d](#sp-07-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-DB](#contract-db), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Run is scored only when all required jobs terminal; counters reconcile.
- **Required automated tests:** Missing snapshot, duplicate result, all-failure and incomplete evaluation tests.
- **Security and reliability:** No active-agent score events or artifacts.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Backend, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-20-d"></a>
### SP-20.d — Audit evaluation information flow

- **Objective:** Score models without disclosing hidden evaluation truth to active agents. This PR delivers audit evaluation information flow.
- **Implementation scope:** Exercise API/event/error/artifact paths while a hostile agent is active; verify post-run viewer gating.
- **Out of scope:** Excludes SP-20.a isolate evaluation truth and job ownership; SP-20.b run networkless predictor jobs; SP-20.c persist complete snapshot scoring. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-20.c](#sp-20-c), [SP-23.b](#sp-23-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-WEB](#contract-web), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No hidden labels/change markers/scores exposed through any active surface.
- **Required automated tests:** Leak canaries in fields, paths, errors, SSE and object broker.
- **Security and reliability:** Leak contaminates suite and blocks scoring; record incident procedure.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Research, QE, Frontend, backend, Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-21"></a>
## SP-21 — Integrate the two research tracks

Parent: [#23](https://github.com/spei04/strange-physics/issues/23). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-21-a"></a>
### SP-21.a — Integrate controlled-selector comparisons

- **Objective:** Demonstrate both accepted research tracks with complete provenance and failures. This PR delivers integrate controlled-selector comparisons.
- **Implementation scope:** Run capped development strategy/family matrix with paired worlds, shared fitter and adaptation.
- **Out of scope:** Excludes SP-21.b integrate complete agent-discovery track; SP-21.c verify cross-track provenance and comparison reports. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-07.d](#sp-07-d), [SP-16.e](#sp-16-e), [SP-18.d](#sp-18-d), [SP-20.d](#sp-20-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-PROVIDER](#contract-provider); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Manifest proves equal purchased information/budget and separate compute costs.
- **Required automated tests:** Pairing, calibration, fallback, failure denominator and replay checks.
- **Security and reliability:** No conclusion that LLM must win.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Backend, research, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-21-b"></a>
### SP-21.b — Integrate complete agent-discovery track

- **Objective:** Demonstrate both accepted research tracks with complete provenance and failures. This PR delivers integrate complete agent-discovery track.
- **Implementation scope:** Run independent custom agent and predictor through experiment/checkpoint/evaluation flow with declared limits.
- **Out of scope:** Excludes SP-21.a integrate controlled-selector comparisons; SP-21.c verify cross-track provenance and comparison reports. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-07.d](#sp-07-d), [SP-16.d](#sp-16-d), [SP-19.d](#sp-19-d), [SP-20.d](#sp-20-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-PRED](#contract-pred), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Complete-agent results separately labeled and reproducible from artifacts.
- **Required automated tests:** Custom model, interrupted agent, invalid predictor and resource-cap journey.
- **Security and reliability:** Do not pool discovery and controlled-selection rankings.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, platform, security, Platform, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-21-c"></a>
### SP-21.c — Verify cross-track provenance and comparison reports

- **Objective:** Demonstrate both accepted research tracks with complete provenance and failures. This PR delivers verify cross-track provenance and comparison reports.
- **Implementation scope:** Cross-check immutable study manifests and paired reporting across both tracks with independently calculated fixtures.
- **Out of scope:** Excludes SP-21.a integrate controlled-selector comparisons; SP-21.b integrate complete agent-discovery track. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-21.a](#sp-21-a), [SP-21.b](#sp-21-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All counts, versions, failures and costs trace to source records.
- **Required automated tests:** Manifest tamper, missing scored row, split collision and offline reproduction.
- **Security and reliability:** Sanitize fixture data; no public customer results.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Research, QE, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R4; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-22"></a>
## SP-22 — Build workspace and constrained world UI

Parent: [#24](https://github.com/spei04/strange-physics/issues/24). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-22-a"></a>
### SP-22.a — Specify accessible workspace journeys

- **Objective:** Let researchers create private worlds and run investigations through an accessible product. This PR delivers specify accessible workspace journeys.
- **Implementation scope:** Define invite/run/world/inspect flows, role states and keyboard/error/loading behavior; review with product.
- **Out of scope:** UI or missing backend implementation.
- **Prerequisites and dependencies:** [SP-00.b](#sp-00-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Annotated journeys and empty/failed/private states accepted before client code.
- **Required automated tests:** Machine-check fixture/state inventory and accessibility checklist completeness.
- **Security and reliability:** Do not reveal world truth in active-agent view.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; in progress. Journey specification/inventory at 90c010c: seven journeys, 28 scenarios, eight accessibility checks and three passing consistency tests. Research reviewed truth boundaries; Quality reviewed inventory. Product/full ID/WEB/ART acceptance remains pending; no UI or accessibility conformance claimed.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.


<a id="sp-22-b"></a>
### SP-22.b — Implement versioned world and suite catalog API

- **Objective:** Let researchers create private worlds and run investigations through an accessible product. This PR delivers implement versioned world and suite catalog api.
- **Implementation scope:** Create/read/list immutable supported world definitions and suite references with author preview and restricted agent projection.
- **Out of scope:** Excludes SP-22.a specify accessible workspace journeys; SP-22.c implement authenticated workspace shell; SP-22.d build constrained world editor; SP-22.e integrate world-to-run product journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.d](#sp-01-d), [SP-11.c](#sp-11-c), [SP-13.b](#sp-13-b), [SP-03.c](#sp-03-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Builder can save/reload valid world; author rights never reveal official blind truth.
- **Required automated tests:** Bounds/version conflict, tenant traversal, unsupported laws and projection leakage.
- **Security and reliability:** Hosted arbitrary law uploads not trusted; approved catalog only.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Frontend, backend, Backend, SDK, frontend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-22-c"></a>
### SP-22.c — Implement authenticated workspace shell

- **Objective:** Let researchers create private worlds and run investigations through an accessible product. This PR delivers implement authenticated workspace shell.
- **Implementation scope:** Build navigation, membership/run lists and authenticated client with role/error states.
- **Out of scope:** Excludes SP-22.a specify accessible workspace journeys; SP-22.b implement versioned world and suite catalog api; SP-22.d build constrained world editor; SP-22.e integrate world-to-run product journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.e](#sp-01-e), [SP-22.a](#sp-22-a), [SP-08.d](#sp-08-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Real session bootstrap and list operations work across supported roles.
- **Required automated tests:** Browser login/logout, wrong role, CSRF/session expiry and empty/error fixtures.
- **Security and reliability:** No credentials in URL/local logs; sanitize user text.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-22-d"></a>
### SP-22.d — Build constrained world editor

- **Objective:** Let researchers create private worlds and run investigations through an accessible product. This PR delivers build constrained world editor.
- **Implementation scope:** Edit graph/initial ranges/approved laws and changes with server validation and immutable save.
- **Out of scope:** Excludes SP-22.a specify accessible workspace journeys; SP-22.b implement versioned world and suite catalog api; SP-22.c implement authenticated workspace shell; SP-22.e integrate world-to-run product journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-22.b](#sp-22-b), [SP-22.c](#sp-22-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Keyboard user creates/reloads supported world with clear author/agent separation.
- **Required automated tests:** Invalid bounds, topology, stale version and accessibility journey tests.
- **Security and reliability:** Client validation complements server; no executable upload path.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-22-e"></a>
### SP-22.e — Integrate world-to-run product journey

- **Objective:** Let researchers create private worlds and run investigations through an accessible product. This PR delivers integrate world-to-run product journey.
- **Implementation scope:** Connect world version and approved package selection to create/read/cancel run with durable operation status.
- **Out of scope:** Excludes SP-22.a specify accessible workspace journeys; SP-22.b implement versioned world and suite catalog api; SP-22.c implement authenticated workspace shell; SP-22.d build constrained world editor. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-22.d](#sp-22-d), [SP-16.e](#sp-16-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Run references exact world/package versions; failed/cancelled state displayed honestly.
- **Required automated tests:** Browser create conflict, permission removal, unavailable worker and cancel race.
- **Security and reliability:** No promise of completion from 202 acceptance.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-23"></a>
## SP-23 — Implement live event timeline and reconnection

Parent: [#25](https://github.com/spei04/strange-physics/issues/25). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-23-a"></a>
### SP-23.a — Publish committed event and replay endpoints

- **Objective:** Expose live progress and history without gaps or privacy violations. This PR delivers publish committed event and replay endpoints.
- **Implementation scope:** Implement per-run sequence events in transaction, bounded SSE batches and authorized replay chunks.
- **Out of scope:** Excludes SP-23.b implement cursor expiry and archive resynchronization; SP-23.c render live investigation timeline; SP-23.d integrate reconnect and cancellation ux. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.d](#sp-01-d), [SP-09.d](#sp-09-d), [SP-11.c](#sp-11-c), [SP-13.c](#sp-13-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No event before commit; no DB connection held per viewer; event freshness instrumented.
- **Required automated tests:** Rollback event absence, sequence uniqueness, tenant access and slow viewer tests.
- **Security and reliability:** No truth/evaluator metadata in active event schemas.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Frontend, backend, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-23-b"></a>
### SP-23.b — Implement cursor expiry and archive resynchronization

- **Objective:** Expose live progress and history without gaps or privacy violations. This PR delivers implement cursor expiry and archive resynchronization.
- **Implementation scope:** Support Last-Event-ID, cursor expiry, authoritative snapshot and archived history pagination with reauthorization.
- **Out of scope:** Excludes SP-23.a publish committed event and replay endpoints; SP-23.c render live investigation timeline; SP-23.d integrate reconnect and cancellation ux. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-23.a](#sp-23-a), [SP-13.d](#sp-13-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-ART](#contract-art), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Reconnect has no silent committed-event gaps; current authoritative checks before every payload batch; revoked idle stream closes ≤30s.
- **Required automated tests:** Duplicate/gap/expired cursor, archive outage and membership revocation tests.
- **Security and reliability:** Archive and snapshot use same tenant/privacy policy.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Frontend, backend, Platform, research, Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-23-c"></a>
### SP-23.c — Render live investigation timeline

- **Objective:** Expose live progress and history without gaps or privacy violations. This PR delivers render live investigation timeline.
- **Implementation scope:** Render experiment/budget/model revisions and terminal/pending states from committed sequence.
- **Out of scope:** Excludes SP-23.a publish committed event and replay endpoints; SP-23.b implement cursor expiry and archive resynchronization; SP-23.d integrate reconnect and cancellation ux. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-22.c](#sp-22-c), [SP-23.b](#sp-23-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Replay is deterministic; duplicates and reconnect do not double-count budget.
- **Required automated tests:** Recorded feed, duplicate/out-of-order events and terminal transition browser tests.
- **Security and reliability:** Treat annotations as untrusted; bounded client memory.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-23-d"></a>
### SP-23.d — Integrate reconnect and cancellation UX

- **Objective:** Expose live progress and history without gaps or privacy violations. This PR delivers integrate reconnect and cancellation ux.
- **Implementation scope:** Handle lost network, auth expiry, archive resync and cancellation progress without misleading completion.
- **Out of scope:** Excludes SP-23.a publish committed event and replay endpoints; SP-23.b implement cursor expiry and archive resynchronization; SP-23.c render live investigation timeline. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-23.c](#sp-23-c), [SP-16.e](#sp-16-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** User sees gap recovery and explicit failed resync; real cancellation path works.
- **Required automated tests:** Browser offline/reconnect/revoke/expired-cursor and slow-consumer tests.
- **Security and reliability:** No cached private data after workspace logout.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-24"></a>
## SP-24 — Implement prediction and replay diagnostics

Parent: [#26](https://github.com/spei04/strange-physics/issues/26). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-24-a"></a>
### SP-24.a — Implement indexed frame replay and scrubbing

- **Objective:** Make actual motion, predictions, uncertainty and failures diagnosable. This PR delivers implement indexed frame replay and scrubbing.
- **Implementation scope:** Load bounded immutable frame chunks; interpolate server data with play/pause/scrub/speed controls.
- **Out of scope:** Excludes SP-24.b overlay prediction and uncertainty diagnostics; SP-24.c compare recorded strategies and failures; SP-24.d verify accessible diagnostic journeys. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-23.d](#sp-23-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Reference frames exact at timestamps; reference-device interaction ≤100ms and ≥30fps target measured.
- **Required automated tests:** Frame alignment, seek/end boundaries, malformed chunk and performance fixtures.
- **Security and reliability:** No second physics solver; bound memory and sanitize content.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Platform, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-24-b"></a>
### SP-24.b — Overlay prediction and uncertainty diagnostics

- **Objective:** Make actual motion, predictions, uncertainty and failures diagnosable. This PR delivers overlay prediction and uncertainty diagnostics.
- **Implementation scope:** Show actual/predicted trajectories, interval levels, errors and insufficient-support states with post-run truth gating.
- **Out of scope:** Excludes SP-24.a implement indexed frame replay and scrubbing; SP-24.c compare recorded strategies and failures; SP-24.d verify accessible diagnostic journeys. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-24.a](#sp-24-a), [SP-20.d](#sp-20-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Viewer distinguishes model uncertainty and failed/missing prediction from truth.
- **Required automated tests:** Layer alignment, absent intervals, failed model and active-truth denial tests.
- **Security and reliability:** No fabricated confidence or hidden evaluation during run.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-24-c"></a>
### SP-24.c — Compare recorded strategies and failures

- **Objective:** Make actual motion, predictions, uncertainty and failures diagnosable. This PR delivers compare recorded strategies and failures.
- **Implementation scope:** Synchronize paired run timelines, budget/error curves and failure/cost indicators from manifest.
- **Out of scope:** Excludes SP-24.a implement indexed frame replay and scrubbing; SP-24.b overlay prediction and uncertainty diagnostics; SP-24.d verify accessible diagnostic journeys. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-24.b](#sp-24-b), [SP-07.d](#sp-07-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Compare only compatible protocol/conditions and disclose mismatches.
- **Required automated tests:** Protocol mismatch, missing/failing run and paired time alignment tests.
- **Security and reliability:** No successful-only filtering by default.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-24-d"></a>
### SP-24.d — Verify accessible diagnostic journeys

- **Objective:** Make actual motion, predictions, uncertainty and failures diagnosable. This PR delivers verify accessible diagnostic journeys.
- **Implementation scope:** Complete keyboard/screen-reader alternatives, error descriptions and supported-browser rendering checks.
- **Out of scope:** Excludes SP-24.a implement indexed frame replay and scrubbing; SP-24.b overlay prediction and uncertainty diagnostics; SP-24.c compare recorded strategies and failures. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-24.c](#sp-24-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Essential investigation/replay usable without canvas-only interaction.
- **Required automated tests:** Automated accessibility, keyboard and browser visual-reference tests.
- **Security and reliability:** No sensitive data in screenshots or diagnostics.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Frontend engineer; base reference lane FE. Required review: Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-25"></a>
## SP-25 — Deliver remote SDK, CLI and complete export

Parent: [#27](https://github.com/spei04/strange-physics/issues/27). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-25-a"></a>
### SP-25.a — Implement remote SDK session adapter

- **Objective:** Support programmatic use, complete exports and explicit safe publication. This PR delivers implement remote sdk session adapter.
- **Implementation scope:** Implement scoped auth, async operation polling, idempotent experiments and checkpoint restoration through frozen interfaces.
- **Out of scope:** Excludes SP-25.b deliver remote cli operations; SP-25.c build complete export manifest and retrieval api; SP-25.d implement explicit sanitized publication lifecycle; SP-25.e verify offline reconstruction across clients. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-01.e](#sp-01-e), [SP-08.c](#sp-08-c), [SP-16.e](#sp-16-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-CORE](#contract-core), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Trusted local and remote semantic conformance passes.
- **Required automated tests:** Retry/cancel/expiry/version/duplicate checkpoint and budget parity tests.
- **Security and reliability:** Tokens redacted; bounded retry and explicit incompatible runtime.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend, Research, Platform, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-25-b"></a>
### SP-25.b — Deliver remote CLI operations

- **Objective:** Support programmatic use, complete exports and explicit safe publication. This PR delivers deliver remote cli operations.
- **Implementation scope:** Add login/config/run/status/cancel/export command paths with secure credential references and meaningful exit codes.
- **Out of scope:** Excludes SP-25.a implement remote sdk session adapter; SP-25.c build complete export manifest and retrieval api; SP-25.d implement explicit sanitized publication lifecycle; SP-25.e verify offline reconstruction across clients. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-25.a](#sp-25-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** CLI completes real remote run and resumes without duplicate experiment.
- **Required automated tests:** Subprocess CLI success/failure, interrupted polling and secret-redaction tests.
- **Security and reliability:** No keys in argv/history or exported manifests.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, SDK, frontend, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-25-c"></a>
### SP-25.c — Build complete export manifest and retrieval API

- **Objective:** Support programmatic use, complete exports and explicit safe publication. This PR delivers build complete export manifest and retrieval api.
- **Implementation scope:** Assemble authorized run package including runtime/config, observations, models, attempts and scores; hash every reference.
- **Out of scope:** Excludes SP-25.a implement remote sdk session adapter; SP-25.b deliver remote cli operations; SP-25.d implement explicit sanitized publication lifecycle; SP-25.e verify offline reconstruction across clients. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-19.a](#sp-19-a), [SP-13.d](#sp-13-d), [SP-11.c](#sp-11-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-HTTP](#contract-http), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Export complete or explicitly incomplete; offline verifier detects missing content.
- **Required automated tests:** Tamper/missing artifact, large export, cross-tenant and pending-evaluation tests.
- **Security and reliability:** Restricted truth/provider secrets excluded from ordinary export.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Platform, backend, research, Backend, SDK, frontend, Research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-25-d"></a>
### SP-25.d — Implement explicit sanitized publication lifecycle

- **Objective:** Support programmatic use, complete exports and explicit safe publication. This PR delivers implement explicit sanitized publication lifecycle.
- **Implementation scope:** Add owner-requested publication review, visibility transition and withdrawal/takedown metadata.
- **Out of scope:** Excludes SP-25.a implement remote sdk session adapter; SP-25.b deliver remote cli operations; SP-25.c build complete export manifest and retrieval api; SP-25.e verify offline reconstruction across clients. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-25.c](#sp-25-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-HTTP](#contract-http), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No automatic publication; sanitized release retains failed scored rows.
- **Required automated tests:** Role/replay publication, secret canary, incomplete release and withdraw tests.
- **Security and reliability:** Public copies not promised fully retractable.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Platform, backend, research, Backend, SDK, frontend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-25-e"></a>
### SP-25.e — Verify offline reconstruction across clients

- **Objective:** Support programmatic use, complete exports and explicit safe publication. This PR delivers verify offline reconstruction across clients.
- **Implementation scope:** Reconstruct recorded outputs in CLI/browser without provider/network calls; verify every manifest hash.
- **Out of scope:** Excludes SP-25.a implement remote sdk session adapter; SP-25.b deliver remote cli operations; SP-25.c build complete export manifest and retrieval api; SP-25.d implement explicit sanitized publication lifecycle. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-25.b](#sp-25-b), [SP-25.d](#sp-25-d), [SP-21.c](#sp-21-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-SCI](#contract-sci), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Independent environment reproduces reports and replay from export.
- **Required automated tests:** Network-denied replay, version mismatch, tamper and missing member tests.
- **Security and reliability:** Never load private journal as public replay.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, backend, research, Research, QE, Frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-26"></a>
## SP-26 — Package supported self-host deployment

Parent: [#28](https://github.com/spei04/strange-physics/issues/28). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-26-a"></a>
### SP-26.a — Package one supported secure self-host installation

- **Objective:** Allow independent deployment within one documented support matrix. This PR delivers package one supported secure self-host installation.
- **Implementation scope:** Create versioned installer/config for documented Kubernetes sandbox, SQL/object/OIDC stack and separately labeled trusted dev mode.
- **Out of scope:** Excludes SP-26.b validate portable identity and storage adapters; SP-26.c implement self-host upgrade and recovery procedure; SP-26.d verify clean install-to-investigation journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.e](#sp-16-e), [SP-27.f](#sp-27-f), [SP-15.e](#sp-15-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Fresh supported environment completes health and isolation preflight.
- **Required automated tests:** Install validation, missing runtime/secret and insecure-profile rejection tests.
- **Security and reliability:** Do not advertise trusted development profile for hostile code.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-26-b"></a>
### SP-26.b — Validate portable identity and storage adapters

- **Objective:** Allow independent deployment within one documented support matrix. This PR delivers validate portable identity and storage adapters.
- **Implementation scope:** Exercise standard OIDC and supported SQL/object configuration without managed-only assumptions.
- **Out of scope:** Excludes SP-26.a package one supported secure self-host installation; SP-26.c implement self-host upgrade and recovery procedure; SP-26.d verify clean install-to-investigation journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-26.a](#sp-26-a), [SP-08.d](#sp-08-d), [SP-13.d](#sp-13-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-ART](#contract-art), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Document explicit supported compatibility matrix and deny unsafe config.
- **Required automated tests:** Issuer mapping, object generation semantics and adapter conformance tests.
- **Security and reliability:** Portable deployment must preserve auth/immutability boundaries.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Backend, security, Platform, backend, research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-26-c"></a>
### SP-26.c — Implement self-host upgrade and recovery procedure

- **Objective:** Allow independent deployment within one documented support matrix. This PR delivers implement self-host upgrade and recovery procedure.
- **Implementation scope:** Automate backup/preflight, expand-contract upgrade, client compatibility and rollback/forward recovery.
- **Out of scope:** Excludes SP-26.a package one supported secure self-host installation; SP-26.b validate portable identity and storage adapters; SP-26.d verify clean install-to-investigation journey. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-26.b](#sp-26-b), [SP-29.b](#sp-29-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Seeded supported previous release upgrades/restores without lost committed data.
- **Required automated tests:** Schema upgrade, old worker/client, interrupted migration and restore tests.
- **Security and reliability:** Do not call seeded predecessor a real published version.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, Backend, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-26-d"></a>
### SP-26.d — Verify clean install-to-investigation journey

- **Objective:** Allow independent deployment within one documented support matrix. This PR delivers verify clean install-to-investigation journey.
- **Implementation scope:** Run documented fresh install and upgrade on supported target without operator edits; retain sanitized evidence.
- **Out of scope:** Excludes SP-26.a package one supported secure self-host installation; SP-26.b validate portable identity and storage adapters; SP-26.c implement self-host upgrade and recovery procedure. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-26.c](#sp-26-c), [SP-25.e](#sp-25-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-WEB](#contract-web), [C-SCI](#contract-sci); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Run, interruption, export and recovery succeed using published instructions.
- **Required automated tests:** Automated install/upgrade/remote journey and invalid-config tests.
- **Security and reliability:** External adoption remains a separate partner gate.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Platform, QE, security, Frontend, backend, Research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R5; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-27"></a>
## SP-27 — Create IaC and trusted delivery foundation

Parent: [#29](https://github.com/spei04/strange-physics/issues/29). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-27-a"></a>
### SP-27.a — Create keyless environment bootstrap and policy checks

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers create keyless environment bootstrap and policy checks.
- **Implementation scope:** Define separate environment identities, Terraform state and narrowly scoped repository/workflow federation with policy checks.
- **Out of scope:** Excludes SP-27.b provision versioned staging data and dispatch services; SP-27.c deploy trusted staging api and worker test substrate; SP-27.d sign trusted images and enforce release provenance; SP-27.e implement telemetry, slo counters and alerts; SP-27.f rehearse progressive deploy and rollback. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-02.b](#sp-02-b), [SP-02.c](#sp-02-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Unauthorized repo/ref/environment cannot obtain deployment authority.
- **Required automated tests:** Terraform validate/plan, IAM policy and forged federation-context tests.
- **Security and reliability:** No long-lived service keys; public CI never runs untrusted package hooks.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-27-b"></a>
### SP-27.b — Provision versioned staging data and dispatch services

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers provision versioned staging data and dispatch services.
- **Implementation scope:** Deploy approved SQL/storage/queue/registry/secret/network configuration through IaC with private endpoints and bounded pools.
- **Out of scope:** Excludes SP-27.a create keyless environment bootstrap and policy checks; SP-27.c deploy trusted staging api and worker test substrate; SP-27.d sign trusted images and enforce release provenance; SP-27.e implement telemetry, slo counters and alerts; SP-27.f rehearse progressive deploy and rollback. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-27.a](#sp-27-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Configuration readback matches plan; no public storage or unintended identity grants.
- **Required automated tests:** IaC drift, connectivity, pool bound and deny-access smoke tests.
- **Security and reliability:** Pricing/cap approval remains precondition; backups enabled from first persistent data.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-27-c"></a>
### SP-27.c — Deploy trusted staging API and worker test substrate

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers deploy trusted staging api and worker test substrate.
- **Implementation scope:** Deploy service skeleton/health checks and controlled runtime trial substrate with environment identities.
- **Out of scope:** Excludes SP-27.a create keyless environment bootstrap and policy checks; SP-27.b provision versioned staging data and dispatch services; SP-27.d sign trusted images and enforce release provenance; SP-27.e implement telemetry, slo counters and alerts; SP-27.f rehearse progressive deploy and rollback. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-27.b](#sp-27-b), [SP-09.a](#sp-09-a), [SP-01.c](#sp-01-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Smoke deployment/rollback recorded; no uploaded code enabled.
- **Required automated tests:** Health/config/identity failure, rollback and isolation preflight tests.
- **Security and reliability:** Fail closed on missing configuration; keep stage independent of prod.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-27-d"></a>
### SP-27.d — Sign trusted images and enforce release provenance

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers sign trusted images and enforce release provenance.
- **Implementation scope:** Add locked build/scanning/SBOM/signature/provenance pipeline and digest verification for trusted images.
- **Out of scope:** Excludes SP-27.a create keyless environment bootstrap and policy checks; SP-27.b provision versioned staging data and dispatch services; SP-27.c deploy trusted staging api and worker test substrate; SP-27.e implement telemetry, slo counters and alerts; SP-27.f rehearse progressive deploy and rollback. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-27.c](#sp-27-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Only intended reviewed source produces accepted deployable artifact.
- **Required automated tests:** Dependency/secret scan, image substitution and provenance policy tests.
- **Security and reliability:** Trusted deployment CI never executes customer hooks.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-27-e"></a>
### SP-27.e — Implement telemetry, SLO counters and alerts

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers implement telemetry, slo counters and alerts.
- **Implementation scope:** Define structured logs/traces, bounded metric labels, eligible-request SLI counters and burn-rate/synthetic alerts.
- **Out of scope:** Excludes SP-27.a create keyless environment bootstrap and policy checks; SP-27.b provision versioned staging data and dispatch services; SP-27.c deploy trusted staging api and worker test substrate; SP-27.d sign trusted images and enforce release provenance; SP-27.f rehearse progressive deploy and rollback. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-27.c](#sp-27-c), [SP-09.c](#sp-09-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Injected failure reaches named test receiver; dashboards reconcile denominators.
- **Required automated tests:** Redaction, cardinality, latency/error denominator and alert-fire/clear tests.
- **Security and reliability:** Do not log raw prompts/world truth; low traffic handled explicitly.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, Backend, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-27-f"></a>
### SP-27.f — Rehearse progressive deploy and rollback

- **Objective:** Create reproducible delivery, monitoring and rollback foundations. This PR delivers rehearse progressive deploy and rollback.
- **Implementation scope:** Implement canary gate, migration ordering and compatible image/client rollback with release manifest.
- **Out of scope:** Excludes SP-27.a create keyless environment bootstrap and policy checks; SP-27.b provision versioned staging data and dispatch services; SP-27.c deploy trusted staging api and worker test substrate; SP-27.d sign trusted images and enforce release provenance; SP-27.e implement telemetry, slo counters and alerts. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-27.d](#sp-27-d), [SP-27.e](#sp-27-e), [SP-16.c](#sp-16-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Failed canary halts expansion; seeded previous version remains recoverable.
- **Required automated tests:** Bad image, interrupted migration, mixed worker versions and rollback smoke.
- **Security and reliability:** No production release authorization inferred from staging rehearsal.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-28"></a>
## SP-28 — Measure capacity and fairness

Parent: [#30](https://github.com/spei04/strange-physics/issues/30). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-28-a"></a>
### SP-28.a — Build representative capacity workload generators

- **Objective:** Establish the supported capacity and fair-overload envelope with measurements. This PR delivers build representative capacity workload generators.
- **Implementation scope:** Generate 1/3/8-particle family mix, viewers/builds, artifact sizes and fake-provider latencies; isolate evaluator pool.
- **Out of scope:** Excludes SP-28.b measure stepped load and latency budgets; SP-28.c run mixed soak and saturation characterization; SP-28.d verify fair admission under faults. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-16.e](#sp-16-e), [SP-20.c](#sp-20-c), [SP-23.b](#sp-23-b), [SP-07.b](#sp-07-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-SCI](#contract-sci), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Workload manifest separates investigations/API/viewers/builds/evaluation and matches declared envelope.
- **Required automated tests:** Generator determinism, numerical/IO distribution and count checks.
- **Security and reliability:** No paid provider stress; keep load artifacts private.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, QE, security, Research, Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-28-b"></a>
### SP-28.b — Measure stepped load and latency budgets

- **Objective:** Establish the supported capacity and fair-overload envelope with measurements. This PR delivers measure stepped load and latency budgets.
- **Implementation scope:** Run 10→25→50→100 investigations, 100 viewers and declared API mix; measure DB/queue/event budgets.
- **Out of scope:** Excludes SP-28.a build representative capacity workload generators; SP-28.c run mixed soak and saturation characterization; SP-28.d verify fair admission under faults. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-28.a](#sp-28-a), [SP-37.c](#sp-37-c), [SP-27.f](#sp-27-f). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Two-hour target hold meets section 7 envelope or fails with bottleneck evidence.
- **Required automated tests:** Automated latency, throughput, integrity and zero-duplicate budget assertions.
- **Security and reliability:** Do not equate offered load or connected sockets with completed capacity.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-28-c"></a>
### SP-28.c — Run mixed soak and saturation characterization

- **Objective:** Establish the supported capacity and fair-overload envelope with measurements. This PR delivers run mixed soak and saturation characterization.
- **Implementation scope:** Execute 24-hour soak and 300 offered-run/5× burst with slow and malicious workloads.
- **Out of scope:** Excludes SP-28.a build representative capacity workload generators; SP-28.b measure stepped load and latency budgets; SP-28.d verify fair admission under faults. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-28.b](#sp-28-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Bounded queue/memory growth; fair rejection and evaluator backlog <24h within supported envelope.
- **Required automated tests:** Long-run leak, overload rejection, backlog and persistence integrity checks.
- **Security and reliability:** 300 offered is stress, not capacity promise; stop on corruption.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-28-d"></a>
### SP-28.d — Verify fair admission under faults

- **Objective:** Establish the supported capacity and fair-overload envelope with measurements. This PR delivers verify fair admission under faults.
- **Implementation scope:** Mix noisy tenants, provider outages and worker failures at supported load; compare fairness and recovery.
- **Out of scope:** Excludes SP-28.a build representative capacity workload generators; SP-28.b measure stepped load and latency budgets; SP-28.c run mixed soak and saturation characterization. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-28.c](#sp-28-c), [SP-29.c](#sp-29-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No monopolization or duplicate charge; latency/recovery thresholds measured.
- **Required automated tests:** Starvation, provider throttling, cancellation and crash-in-load tests.
- **Security and reliability:** Unknown provider costs remain visible.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-29"></a>
## SP-29 — Prove backup, failover and fault recovery

Parent: [#31](https://github.com/spei04/strange-physics/issues/31). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-29-a"></a>
### SP-29.a — Implement backup and recovery-set manifests

- **Objective:** Prove recoverability of acknowledged work and deletion state. This PR delivers implement backup and recovery-set manifests.
- **Implementation scope:** Configure actual PITR/backup policies and verified database+object generation manifests with isolated restore identity.
- **Out of scope:** Excludes SP-29.b restore sql and objects with tombstone replay; SP-29.c exercise worker loss and database failover; SP-29.d rehearse deployment rollback under load. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-13.d](#sp-13-d), [SP-27.b](#sp-27-b), [SP-37.a](#sp-37-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ART](#contract-art), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Recovery point maps every referenced object; lag/expiry visible.
- **Required automated tests:** Backup completeness, missing object, permissions and lag alert tests.
- **Security and reliability:** A successful scheduled job alone is not recoverability evidence.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, backend, research, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-29-b"></a>
### SP-29.b — Restore SQL and objects with tombstone replay

- **Objective:** Prove recoverability of acknowledged work and deletion state. This PR delivers restore sql and objects with tombstone replay.
- **Implementation scope:** Restore into isolation, fence old leases/tokens and reapply deletion/revocation records before access.
- **Out of scope:** Excludes SP-29.a implement backup and recovery-set manifests; SP-29.c exercise worker loss and database failover; SP-29.d rehearse deployment rollback under load. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-29.a](#sp-29-a), [SP-37.c](#sp-37-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ART](#contract-art), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Pilot ≤15min RPO/≤4h RTO measured; no deleted object resurrected to users.
- **Required automated tests:** Timed restore, corrupt object, interrupted replay and revoked identity tests.
- **Security and reliability:** No production data exposed during drill; preserve private evidence.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, backend, research, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-29-c"></a>
### SP-29.c — Exercise worker loss and database failover

- **Objective:** Prove recoverability of acknowledged work and deletion state. This PR delivers exercise worker loss and database failover.
- **Implementation scope:** Force worker/process loss and real HA failover; validate reconnection, epochs, artifact and budget integrity.
- **Out of scope:** Excludes SP-29.a implement backup and recovery-set manifests; SP-29.b restore sql and objects with tombstone replay; SP-29.d rehearse deployment rollback under load. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-29.b](#sp-29-b), [SP-16.e](#sp-16-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Worker p95 recovery ≤5min; DB failover ≤15min target with committed-state validation.
- **Required automated tests:** Fault matrix, stale worker, pool exhaustion and no-duplicate invariants.
- **Security and reliability:** Targets measured in deployed configuration, not assumed from service SLA.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Platform, QE, security, Backend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-29-d"></a>
### SP-29.d — Rehearse deployment rollback under load

- **Objective:** Prove recoverability of acknowledged work and deletion state. This PR delivers rehearse deployment rollback under load.
- **Implementation scope:** Exercise bad deploy/migration under bounded workload and validate compatible rollback or forward fix.
- **Out of scope:** Excludes SP-29.a implement backup and recovery-set manifests; SP-29.b restore sql and objects with tombstone replay; SP-29.c exercise worker loss and database failover. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-29.c](#sp-29-c), [SP-27.f](#sp-27-f). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Committed data, old clients and current leases survive documented recovery path.
- **Required automated tests:** Mixed-version upgrade, partial migration and health-regression rollback tests.
- **Security and reliability:** Destructive schema change cannot bypass recovery review.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-30"></a>
## SP-30 — Verify integrated journeys and upgrades

Parent: [#32](https://github.com/spei04/strange-physics/issues/32). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-30-a"></a>
### SP-30.a — Test authenticated end-to-end researcher journeys

- **Objective:** Validate complete customer journeys and supported upgrades on one candidate. This PR delivers test authenticated end-to-end researcher journeys.
- **Implementation scope:** Automate invite/build/run/interrupt/cancel/replay/export/delete using human and scoped machine identities.
- **Out of scope:** Excludes SP-30.b verify version compatibility matrix; SP-30.c verify install, upgrade and recovery as one journey; SP-30.d review integrated release-candidate evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-21.c](#sp-21-c), [SP-24.d](#sp-24-d), [SP-25.e](#sp-25-e), [SP-26.d](#sp-26-d), [SP-37.c](#sp-37-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-WEB](#contract-web), [C-HTTP](#contract-http), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All supported roles and terminal outcomes verified on release candidate.
- **Required automated tests:** Browser/SDK/CLI cross-tenant negative and interruption journeys.
- **Security and reliability:** Private run data never crosses workspace or public view.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Frontend, backend, Backend, SDK, frontend, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-30-b"></a>
### SP-30.b — Verify version compatibility matrix

- **Objective:** Validate complete customer journeys and supported upgrades on one candidate. This PR delivers verify version compatibility matrix.
- **Implementation scope:** Exercise current/previous supported schema/client/worker/replay versions and declared deprecation policy.
- **Out of scope:** Excludes SP-30.a test authenticated end-to-end researcher journeys; SP-30.c verify install, upgrade and recovery as one journey; SP-30.d review integrated release-candidate evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-30.a](#sp-30-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-HTTP](#contract-http), [C-SCI](#contract-sci), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Unsupported versions fail explicitly; no silent artifact reinterpretation.
- **Required automated tests:** Generated-client drift, old checkpoint and replay migration fixtures.
- **Security and reliability:** Seeded predecessor labeled honestly before second real release.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane FE. Required review: Backend, SDK, frontend, Research, QE, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-30-c"></a>
### SP-30.c — Verify install, upgrade and recovery as one journey

- **Objective:** Validate complete customer journeys and supported upgrades on one candidate. This PR delivers verify install, upgrade and recovery as one journey.
- **Implementation scope:** Run clean and seeded previous-release installations through upgrade/restore using published self-host instructions.
- **Out of scope:** Excludes SP-30.a test authenticated end-to-end researcher journeys; SP-30.b verify version compatibility matrix; SP-30.d review integrated release-candidate evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-30.b](#sp-30-b), [SP-29.d](#sp-29-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No manual undocumented intervention; export hashes/budgets preserved.
- **Required automated tests:** Interrupted install, config mismatch, rollback and restored-client tests.
- **Security and reliability:** No blanket support outside documented matrix.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-30-d"></a>
### SP-30.d — Review integrated release-candidate evidence

- **Objective:** Validate complete customer journeys and supported upgrades on one candidate. This PR delivers review integrated release-candidate evidence.
- **Implementation scope:** Map every pilot requirement to source/run evidence and unresolved defect; freeze candidate identity.
- **Out of scope:** Pilot or GA authorization.
- **Prerequisites and dependencies:** [SP-30.c](#sp-30-c), [SP-28.d](#sp-28-d), [SP-31.e](#sp-31-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No blocking issue waived; owners and expiry for permitted lower-risk exceptions.
- **Required automated tests:** Automated traceability/link completeness and manifest integrity checks.
- **Security and reliability:** Document is not substitute for executed tests.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-31"></a>
## SP-31 — Exercise security and data boundaries

Parent: [#33](https://github.com/spei04/strange-physics/issues/33). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-31-a"></a>
### SP-31.a — Audit tenant and session boundary matrix

- **Objective:** Detect and resolve exploitable security and data-boundary failures. This PR delivers audit tenant and session boundary matrix.
- **Implementation scope:** Run route/property/object/SSE/session authorization corpus including pooled RLS and service credentials.
- **Out of scope:** Excludes SP-31.b audit build and runtime boundary in release configuration; SP-31.c audit research leakage and provider controls; SP-31.d verify deletion, revocation and log privacy; SP-31.e resolve security review and release blockers. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-11.c](#sp-11-c), [SP-22.e](#sp-22-e), [SP-25.d](#sp-25-d), [SP-23.b](#sp-23-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Every supported identity/route has deny and allow evidence.
- **Required automated tests:** ID substitution, CSRF, mass assignment, object grants and revoked stream tests.
- **Security and reliability:** Any cross-tenant access is release blocker.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Backend, security, SDK, frontend, Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-31-b"></a>
### SP-31.b — Audit build and runtime boundary in release configuration

- **Objective:** Detect and resolve exploitable security and data-boundary failures. This PR delivers audit build and runtime boundary in release configuration.
- **Implementation scope:** Repeat hostile build/runtime/network/DNS/metadata corpus with actual release deployment identities.
- **Out of scope:** Excludes SP-31.a audit tenant and session boundary matrix; SP-31.c audit research leakage and provider controls; SP-31.d verify deletion, revocation and log privacy; SP-31.e resolve security review and release blockers. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-15.e](#sp-15-e), [SP-16.e](#sp-16-e), [SP-27.f](#sp-27-f). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-EXEC](#contract-exec), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No trusted secret/evaluator/cloud access; policy fails closed.
- **Required automated tests:** Admission bypass, untrusted build, IPv6/DNS/metadata and resource attacks.
- **Security and reliability:** Independent security specialist reviews evidence.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, security, backend, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-31-c"></a>
### SP-31.c — Audit research leakage and provider controls

- **Objective:** Detect and resolve exploitable security and data-boundary failures. This PR delivers audit research leakage and provider controls.
- **Implementation scope:** Exercise hostile prompts/predictors and gateway limits across UI/API/error/manifest paths.
- **Out of scope:** Excludes SP-31.a audit tenant and session boundary matrix; SP-31.b audit build and runtime boundary in release configuration; SP-31.d verify deletion, revocation and log privacy; SP-31.e resolve security review and release blockers. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-20.d](#sp-20-d), [SP-18.d](#sp-18-d), [SP-21.c](#sp-21-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-PROVIDER](#contract-provider); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No hidden truth or credential exposure; all attempts/fallbacks disclosed.
- **Required automated tests:** Canary leaks, injected text, malformed output and ambiguity/cap tests.
- **Security and reliability:** Compromised suite quarantined; no silent result reuse.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Backend, research, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-31-d"></a>
### SP-31.d — Verify deletion, revocation and log privacy

- **Objective:** Detect and resolve exploitable security and data-boundary failures. This PR delivers verify deletion, revocation and log privacy.
- **Implementation scope:** Exercise owner delete, revoked credentials, active stream/job access and restored tombstones; inspect telemetry redaction.
- **Out of scope:** Excludes SP-31.a audit tenant and session boundary matrix; SP-31.b audit build and runtime boundary in release configuration; SP-31.c audit research leakage and provider controls; SP-31.e resolve security review and release blockers. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.c](#sp-37-c), [SP-31.a](#sp-31-a), [SP-29.b](#sp-29-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-ART](#contract-art), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Active access revoked immediately; seven-day active removal policy executable; backups honor disclosed expiry.
- **Required automated tests:** Delete/revoke races, replayed backup, token expiry and secret/log canaries.
- **Security and reliability:** No promise deletion instantly erases offline public copies.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security, Platform, backend, research, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-31-e"></a>
### SP-31.e — Resolve security review and release blockers

- **Objective:** Detect and resolve exploitable security and data-boundary failures. This PR delivers resolve security review and release blockers.
- **Implementation scope:** Coordinate independent specialist review, triage findings and retest exact fixes; use explicit contingency work for defects.
- **Out of scope:** Open-ended unlimited remediation inside this estimate.
- **Prerequisites and dependencies:** [SP-31.a](#sp-31-a), [SP-31.b](#sp-31-b), [SP-31.c](#sp-31-c), [SP-31.d](#sp-31-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No exploitable critical/high finding; lower exceptions have owner/control/expiry.
- **Required automated tests:** Repeat failed adversarial tests and evidence manifest checks.
- **Security and reliability:** New material finding creates separately scoped repair PR; never rubber-stamp.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R6; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-32"></a>
## SP-32 — Onboard and support design partners

Parent: [#34](https://github.com/spei04/strange-physics/issues/34). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-32-a"></a>
### SP-32.a — Finalize partner data terms and pilot support scope

- **Objective:** Obtain real design-partner adoption and operational feedback. This PR delivers finalize partner data terms and pilot support scope.
- **Implementation scope:** Confirm pilot organizations, terms, approved access, limits and business-hours primary/backup support.
- **Out of scope:** Sending invitations or signing terms without appropriate authority.
- **Prerequisites and dependencies:** [SP-00.c](#sp-00-c), [SP-30.d](#sp-30-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** External commitments and contact roster exist before private customer data.
- **Required automated tests:** Readiness checker verifies required owner/evidence/expiry fields.
- **Security and reliability:** No legal/compliance guarantees invented.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-32-b"></a>
### SP-32.b — Onboard partner investigations

- **Objective:** Obtain real design-partner adoption and operational feedback. This PR delivers onboard partner investigations.
- **Implementation scope:** Observe genuine first-run sessions and capture private numerator/denominator, support friction and repeat-study intent.
- **Out of scope:** Excludes SP-32.a finalize partner data terms and pilot support scope; SP-32.c review four weeks of partner usage. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-32.a](#sp-32-a), [PILOT_RELEASE](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Named participating organizations can run private studies; deviations recorded.
- **Required automated tests:** Run onboarding smoke and telemetry completeness checks.
- **Security and reliability:** Real external attendance required; no internal substitution.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Frontend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-32-c"></a>
### SP-32.c — Review four weeks of partner usage

- **Objective:** Obtain real design-partner adoption and operational feedback. This PR delivers review four weeks of partner usage.
- **Implementation scope:** Assess adoption, repeated studies, support load and failure patterns; assign scoped fixes and acceptance decisions.
- **Out of scope:** Excludes SP-32.a finalize partner data terms and pilot support scope; SP-32.b onboard partner investigations. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [PILOT_OBSERVATION](#external-and-calendar-gates), [SP-36.d](#sp-36-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Actual partner outcomes recorded against proposed targets; launch-impacting gaps resolved.
- **Required automated tests:** Usage denominator, evidence completeness and regression checks for pilot fixes.
- **Security and reliability:** Partner absence blocks evidence, never counted as success.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-33"></a>
## SP-33 — Freeze and publish scored reference release

Parent: [#35](https://github.com/spei04/strange-physics/issues/35). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-33-a"></a>
### SP-33.a — Approve official protocol and priced sweep

- **Objective:** Publish a trustworthy reference study including failures and reproducibility artifacts. This PR delivers approve official protocol and priced sweep.
- **Implementation scope:** Freeze both scored-track manifests and exclusions before collection; obtain explicit cost/credential/publication authority.
- **Out of scope:** Excludes SP-33.b execute and verify scored reference collection; SP-33.c publish sanitized complete reference artifacts. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-07.d](#sp-07-d), [SP-21.c](#sp-21-c), [SP-31.e](#sp-31-e), [SP-30.d](#sp-30-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Signed immutable protocol and capped run plan; no tuning afterward.
- **Required automated tests:** Frozen manifest, seed separation, limits and estimated-count checks.
- **Security and reliability:** Paid sweep approval separate from development approval.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-33-b"></a>
### SP-33.b — Execute and verify scored reference collection

- **Objective:** Publish a trustworthy reference study including failures and reproducibility artifacts. This PR delivers execute and verify scored reference collection.
- **Implementation scope:** Run approved bounded paired suite; retain all scored attempts/failures and exact identities; reconcile costs.
- **Out of scope:** Excludes SP-33.a approve official protocol and priced sweep; SP-33.c publish sanitized complete reference artifacts. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-33.a](#sp-33-a), [OFFICIAL_SWEEP](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-EXEC](#contract-exec), [C-PROVIDER](#contract-provider); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All scheduled rows accounted for or explicitly failed; no selective redraw.
- **Required automated tests:** Automatic completeness, frozen identity, failure denominator and report reproduction.
- **Security and reliability:** Estimate is engineering effort; measured sweep wall time added at freeze.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, QE, Platform, security, backend, Backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-33-c"></a>
### SP-33.c — Publish sanitized complete reference artifacts

- **Objective:** Publish a trustworthy reference study including failures and reproducibility artifacts. This PR delivers publish sanitized complete reference artifacts.
- **Implementation scope:** Review and publish reference manifests/results/failures and sanitized provider transcripts with independent reproduction.
- **Out of scope:** Excludes SP-33.a approve official protocol and priced sweep; SP-33.b execute and verify scored reference collection. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-33.b](#sp-33-b), [SP-25.d](#sp-25-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All scored outcomes available without secrets; claims match measured scope.
- **Required automated tests:** Secret canaries, missing-row detection, hashes and offline report checks.
- **Security and reliability:** Never publish private customer artifacts under reference-release authority.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS2. Required review: Research, QE, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-34"></a>
## SP-34 — Add enterprise SSO and service identities

Parent: [#36](https://github.com/spei04/strange-physics/issues/36). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-34-a"></a>
### SP-34.a — Validate enterprise federation requirements and entitlement

- **Objective:** Support enterprise federation and scoped credential administration. This PR delivers validate enterprise federation requirements and entitlement.
- **Implementation scope:** Verify required partner OIDC/SAML federation flows, IdP entitlements, tenant mapping and failure/lockout design.
- **Out of scope:** Excludes SP-34.b implement workspace-bound enterprise federation; SP-34.c migrate linked identities without lockout; SP-34.d harden enterprise service-credential lifecycle. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-08.d](#sp-08-d), [SP-00.c](#sp-00-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Chosen provider supports concrete partner scenarios or documented ADR change.
- **Required automated tests:** Configuration/schema fixtures and fake-IdP capability tests.
- **Security and reliability:** Do not assume SCIM/federation is included in existing credits.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-34-b"></a>
### SP-34.b — Implement workspace-bound enterprise federation

- **Objective:** Support enterprise federation and scoped credential administration. This PR delivers implement workspace-bound enterprise federation.
- **Implementation scope:** Add federation connection management, issuer binding and safe login/session mapping without domain auto-join.
- **Out of scope:** Excludes SP-34.a validate enterprise federation requirements and entitlement; SP-34.c migrate linked identities without lockout; SP-34.d harden enterprise service-credential lifecycle. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-34.a](#sp-34-a), [SP-11.c](#sp-11-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Wrong-tenant/issuer login denied; approved member authenticates with enterprise IdP.
- **Required automated tests:** Issuer confusion, assertion replay/expiry, key rotation and session tests.
- **Security and reliability:** Security review required; no implicit membership from email.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-34-c"></a>
### SP-34.c — Migrate linked identities without lockout

- **Objective:** Support enterprise federation and scoped credential administration. This PR delivers migrate linked identities without lockout.
- **Implementation scope:** Implement explicit verified linking/migration, recovery admin path and sole-owner protection.
- **Out of scope:** Excludes SP-34.a validate enterprise federation requirements and entitlement; SP-34.b implement workspace-bound enterprise federation; SP-34.d harden enterprise service-credential lifecycle. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-34.b](#sp-34-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Existing users migrate safely without account takeover or ownership loss.
- **Required automated tests:** Duplicate subject/email, concurrent linking, lost IdP and sole-owner tests.
- **Security and reliability:** Audit every link/admin override; no shared break-glass credential.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-34-d"></a>
### SP-34.d — Harden enterprise service-credential lifecycle

- **Objective:** Support enterprise federation and scoped credential administration. This PR delivers harden enterprise service-credential lifecycle.
- **Implementation scope:** Add enterprise scope policy, expiry/rotation reporting and administrator credential audit.
- **Out of scope:** Excludes SP-34.a validate enterprise federation requirements and entitlement; SP-34.b implement workspace-bound enterprise federation; SP-34.c migrate linked identities without lockout. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-34.c](#sp-34-c), [SP-08.c](#sp-08-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Scoped machine identities rotate/revoke without widening privilege.
- **Required automated tests:** Old/new key overlap, expiry, revoke race and least-scope tests.
- **Security and reliability:** Basic service identity already exists in R2; no late prerequisite for pilot.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, Platform, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-35"></a>
## SP-35 — Add provisioning and rapid deprovisioning

Parent: [#37](https://github.com/spei04/strange-physics/issues/37). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-35-a"></a>
### SP-35.a — Freeze SCIM mapping and lifecycle semantics

- **Objective:** Keep enterprise identity provisioning and revocation consistent across live resources. This PR delivers freeze scim mapping and lifecycle semantics.
- **Implementation scope:** Specify Users/Groups mapping, idempotency, version conflict, disable/delete and owner-protection behavior.
- **Out of scope:** Excludes SP-35.b implement bounded provisioning and reconciliation; SP-35.c enforce rapid end-to-end deprovisioning. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-34.d](#sp-34-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Partner/security accept scope and bounded reconciliation semantics.
- **Required automated tests:** SCIM schema fixtures, duplicate mappings and conflicting version cases.
- **Security and reliability:** Disable policy must cover API, stream, job and credential access.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, SDK, frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-35-b"></a>
### SP-35.b — Implement bounded provisioning and reconciliation

- **Objective:** Keep enterprise identity provisioning and revocation consistent across live resources. This PR delivers implement bounded provisioning and reconciliation.
- **Implementation scope:** Implement SCIM endpoints, group role mapping, paginated sync and replay-safe audit.
- **Out of scope:** Excludes SP-35.a freeze scim mapping and lifecycle semantics; SP-35.c enforce rapid end-to-end deprovisioning. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-35.a](#sp-35-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Repeated/out-of-order operations converge without escalation.
- **Required automated tests:** Bulk limits, duplicate provisioning, stale updates and retry tests.
- **Security and reliability:** Service credential narrowly scoped; rate-limit sync.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-35-c"></a>
### SP-35.c — Enforce rapid end-to-end deprovisioning

- **Objective:** Keep enterprise identity provisioning and revocation consistent across live resources. This PR delivers enforce rapid end-to-end deprovisioning.
- **Implementation scope:** Revoke account/service/run access, close streams and stop unauthorized new work; reconcile active jobs.
- **Out of scope:** Excludes SP-35.a freeze scim mapping and lifecycle semantics; SP-35.b implement bounded provisioning and reconciliation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-35.b](#sp-35-b), [SP-37.e](#sp-37-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-EXEC](#contract-exec), [C-WEB](#contract-web); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Disabled principal denied new calls immediately; current authoritative checks before every stream payload batch; idle stream closure ≤30s and job launch ≤5s revocation targets.
- **Required automated tests:** Active session/token/job/SSE disable races and sole-owner exceptions.
- **Security and reliability:** No stale authorization caches or forgotten machine keys.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, Platform, backend, Frontend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-36"></a>
## SP-36 — Validate external extension and self-host adoption

Parent: [#38](https://github.com/spei04/strange-physics/issues/38). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-36-a"></a>
### SP-36.a — Validate an outside team's agent and law extension

- **Objective:** Prove that an outside team can extend, deploy and reproduce the platform. This PR delivers validate an outside team's agent and law extension.
- **Implementation scope:** Observe external author adding agent/law without core changes; record actual friction and review bounded fixes.
- **Out of scope:** Excludes SP-36.b validate independent self-host install and upgrade; SP-36.c independently reproduce a released report; SP-36.d close partner integration findings. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-25.e](#sp-25-e), [SP-26.d](#sp-26-d), [SP-32.b](#sp-32-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-CORE](#contract-core), [C-SCI](#contract-sci), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** External code runs and recovers using supported interfaces; independent author evidence.
- **Required automated tests:** Contract/extension regression and published example replay tests.
- **Security and reliability:** Trusted local law extension differs from reviewed hosted catalog.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Research engineer; base reference lane RS1. Required review: Research, SDK, QE, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-36-b"></a>
### SP-36.b — Validate independent self-host install and upgrade

- **Objective:** Prove that an outside team can extend, deploy and reproduce the platform. This PR delivers validate independent self-host install and upgrade.
- **Implementation scope:** Support outside team using documented target; verify fresh install, upgrade and restore without hidden operator edits.
- **Out of scope:** Excludes SP-36.a validate an outside team's agent and law extension; SP-36.c independently reproduce a released report; SP-36.d close partner integration findings. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-26.d](#sp-26-d), [SP-32.b](#sp-32-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** External operator signs observed install/upgrade results and limitations.
- **Required automated tests:** Independent install/upgrade smoke and reported-friction regressions.
- **Security and reliability:** Partner environment/access must be available; no simulated adoption.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-36-c"></a>
### SP-36.c — Independently reproduce a released report

- **Objective:** Prove that an outside team can extend, deploy and reproduce the platform. This PR delivers independently reproduce a released report.
- **Implementation scope:** External consumer reconstructs manifest/report without model calls; compare hashes and numerical tolerances.
- **Out of scope:** Excludes SP-36.a validate an outside team's agent and law extension; SP-36.b validate independent self-host install and upgrade; SP-36.d close partner integration findings. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-36.a](#sp-36-a), [SP-36.b](#sp-36-b), [SP-33.c](#sp-33-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-SCI](#contract-sci), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Independent reproduction succeeds or limitation blocks claim.
- **Required automated tests:** Offline replay, compatibility and artifact integrity checks.
- **Security and reliability:** Keep private access paths out of public evidence.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Research, QE, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-36-d"></a>
### SP-36.d — Close partner integration findings

- **Objective:** Prove that an outside team can extend, deploy and reproduce the platform. This PR delivers close partner integration findings.
- **Implementation scope:** Triage observed adoption issues, assign reviewable fixes from contingency and obtain retest acceptance.
- **Out of scope:** Excludes SP-36.a validate an outside team's agent and law extension; SP-36.b validate independent self-host install and upgrade; SP-36.c independently reproduce a released report. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-36.c](#sp-36-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No unresolved adoption blocker; scope and external evidence explicit.
- **Required automated tests:** Regression suite for fixed defects and traceability checker.
- **Security and reliability:** Do not hide additional feature work inside documentation-only closure.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R7; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-37"></a>
## SP-37 — Ship enterprise audit and retention controls

Parent: [#39](https://github.com/spei04/strange-physics/issues/39). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-37-a"></a>
### SP-37.a — Persist basic security audit events

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers persist basic security audit events.
- **Implementation scope:** Record actor/action/target/outcome for membership, secrets, publication, deletion and operator changes with restricted append-only role.
- **Out of scope:** Excludes SP-37.b implement authorized deletion and retention jobs; SP-37.c preserve deletion and revocation across recovery; SP-37.d export tamper-evident enterprise audit history; SP-37.e verify enterprise retention and privacy operations; SP-37.f review customer data and support documentation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-11.c](#sp-11-c), [SP-13.c](#sp-13-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-DB](#contract-db), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All pilot-sensitive mutations produce safe immutable audit record.
- **Required automated tests:** Audit omission, tamper permissions, redaction and transaction rollback tests.
- **Security and reliability:** Basic audit is pilot prerequisite, not deferred to enterprise.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Backend, security, Platform, QE. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-37-b"></a>
### SP-37.b — Implement authorized deletion and retention jobs

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers implement authorized deletion and retention jobs.
- **Implementation scope:** Add owner delete/retention configuration, immediate access tombstone and bounded background active-object removal.
- **Out of scope:** Excludes SP-37.a persist basic security audit events; SP-37.c preserve deletion and revocation across recovery; SP-37.d export tamper-evident enterprise audit history; SP-37.e verify enterprise retention and privacy operations; SP-37.f review customer data and support documentation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.a](#sp-37-a), [SP-13.d](#sp-13-d), [SP-10.c](#sp-10-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-ID](#contract-id), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Interactive access revoked on accepted delete; removal target ≤7 days with retriable state.
- **Required automated tests:** Concurrent read/delete, shared artifact refs, legal-hold flag and repeated job tests.
- **Security and reliability:** Keep minimum tombstone identity; no silent auto-expiry.
- **Effort and confidence:** 5 delivery engineer-days; medium confidence; +1.25 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Platform, backend, research, Backend, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-37-c"></a>
### SP-37.c — Preserve deletion and revocation across recovery

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers preserve deletion and revocation across recovery.
- **Implementation scope:** Replicate protected tombstone/revocation ledger outside restored snapshot and block reopening until replay complete.
- **Out of scope:** Excludes SP-37.a persist basic security audit events; SP-37.b implement authorized deletion and retention jobs; SP-37.d export tamper-evident enterprise audit history; SP-37.e verify enterprise retention and privacy operations; SP-37.f review customer data and support documentation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.b](#sp-37-b), [SP-27.b](#sp-27-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ART](#contract-art), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Restored old DB cannot resurrect access; backup expiry policy accurately reported.
- **Required automated tests:** Older-backup restore, missing ledger, interrupted replay and expired-object tests.
- **Security and reliability:** Fail closed if latest suppression ledger unavailable.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, backend, research, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R3; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-37-d"></a>
### SP-37.d — Export tamper-evident enterprise audit history

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers export tamper-evident enterprise audit history.
- **Implementation scope:** Add scoped paginated audit export with integrity manifest and one-year proposed lifecycle controls.
- **Out of scope:** Excludes SP-37.a persist basic security audit events; SP-37.b implement authorized deletion and retention jobs; SP-37.c preserve deletion and revocation across recovery; SP-37.e verify enterprise retention and privacy operations; SP-37.f review customer data and support documentation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.c](#sp-37-c), [SP-34.d](#sp-34-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ID](#contract-id), [C-HTTP](#contract-http), [C-ART](#contract-art); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Authorized admin can verify completeness/integrity; other roles denied.
- **Required automated tests:** Pagination gap, tamper, tenant traversal and export interruption tests.
- **Security and reliability:** Personal data minimized; immutable does not mean publicly readable.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE2. Required review: Backend, security, SDK, frontend, Platform, backend, research. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-37-e"></a>
### SP-37.e — Verify enterprise retention and privacy operations

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers verify enterprise retention and privacy operations.
- **Implementation scope:** Exercise configured retention, key rotation, backup expiry and deletion reporting; document exceptions and supported limits.
- **Out of scope:** Excludes SP-37.a persist basic security audit events; SP-37.b implement authorized deletion and retention jobs; SP-37.c preserve deletion and revocation across recovery; SP-37.d export tamper-evident enterprise audit history; SP-37.f review customer data and support documentation. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.d](#sp-37-d), [SP-29.b](#sp-29-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-ART](#contract-art), [C-OPS](#contract-ops), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Active deletion and disclosed backup lifecycle verified; no stale access through export.
- **Required automated tests:** Time-controlled retention/expiry, rotation and resurrected-object regression tests.
- **Security and reliability:** 35-day lifecycle is proposal requiring real service configuration proof.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Backend engineer; base reference lane BE1. Required review: Platform, backend, research, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-37-f"></a>
### SP-37.f — Review customer data and support documentation

- **Objective:** Make access changes, deletion and retention auditable and recoverable. This PR delivers review customer data and support documentation.
- **Implementation scope:** Complete reviewed data flows, subprocessors, deletion/support limitations and security questionnaire evidence with specialists.
- **Out of scope:** Excludes SP-37.a persist basic security audit events; SP-37.b implement authorized deletion and retention jobs; SP-37.c preserve deletion and revocation across recovery; SP-37.d export tamper-evident enterprise audit history; SP-37.e verify enterprise retention and privacy operations. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-37.e](#sp-37-e), [SP-32.a](#sp-32-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Terms and product claims reflect actual controls and measured support scope.
- **Required automated tests:** Link/evidence completeness and stale-version checks.
- **Security and reliability:** No compliance certification inferred from code or synthetic data.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-38"></a>
## SP-38 — Rehearse regional disaster recovery

Parent: [#40](https://github.com/spei04/strange-physics/issues/40). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-38-a"></a>
### SP-38.a — Create an independent regional recovery set

- **Objective:** Recover service and consistent data after primary-region loss. This PR delivers create an independent regional recovery set.
- **Implementation scope:** Copy recoverable DB/object generations and suppression ledger into approved secondary US location with independent access.
- **Out of scope:** Excludes SP-38.b perform timed secondary-region recovery; SP-38.c resolve and repeat failed recovery steps. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-29.b](#sp-29-b), [SP-37.e](#sp-37-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ART](#contract-art), [C-DB](#contract-db); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Copy completion and consistency measured; recovery set age ≤24h.
- **Required automated tests:** Missing-generation, key/IAM denial and lag/copy integrity tests.
- **Security and reliability:** Residency/key requirements reviewed before replication.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, backend, research, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-38-b"></a>
### SP-38.b — Perform timed secondary-region recovery

- **Objective:** Recover service and consistent data after primary-region loss. This PR delivers perform timed secondary-region recovery.
- **Implementation scope:** Restore isolated services, fence former region, reapply tombstones/credentials and rehearse endpoint cutover.
- **Out of scope:** Excludes SP-38.a create an independent regional recovery set; SP-38.c resolve and repeat failed recovery steps. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-38.a](#sp-38-a), [SP-26.d](#sp-26-d). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Measured regional RPO/RTO ≤24h with tenant/integrity suite passing.
- **Required automated tests:** Timed failover, stale worker, DNS/cutover and duplicate-launch tests.
- **Security and reliability:** No active-active claim; preserve original incident evidence.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-38-c"></a>
### SP-38.c — Resolve and repeat failed recovery steps

- **Objective:** Recover service and consistent data after primary-region loss. This PR delivers resolve and repeat failed recovery steps.
- **Implementation scope:** Turn drill defects into scoped fixes, repeat failed steps and update runbook/evidence manifest.
- **Out of scope:** Excludes SP-38.a create an independent regional recovery set; SP-38.b perform timed secondary-region recovery. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-38.b](#sp-38-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** All regional restore blockers resolved at exact candidate revision.
- **Required automated tests:** Regression tests and repeated failed recovery sequence.
- **Security and reliability:** Additional architectural changes consume explicit contingency/rebaseline.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-39"></a>
## SP-39 — Revalidate supported production envelope

Parent: [#41](https://github.com/spei04/strange-physics/issues/41). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-39-a"></a>
### SP-39.a — Revalidate final supported capacity envelope

- **Objective:** Publish measured limits for the final enterprise configuration. This PR delivers revalidate final supported capacity envelope.
- **Implementation scope:** Repeat changed-path 100-run load/soak with final identity/retention/runtime configuration and compare baselines.
- **Out of scope:** Excludes SP-39.b publish measured cost and operating limits. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-28.d](#sp-28-d), [SP-30.d](#sp-30-d), [SP-35.c](#sp-35-c), [SP-37.f](#sp-37-f), [SP-38.c](#sp-38-c), [SP-40.b](#sp-40-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Final candidate meets section 7 and no data/budget/security regression.
- **Required automated tests:** Automated percentile, soak, fairness and invariants versus prior baseline.
- **Security and reliability:** No stale pre-enterprise performance evidence.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane TL. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-39-b"></a>
### SP-39.b — Publish measured cost and operating limits

- **Objective:** Publish measured limits for the final enterprise configuration. This PR delivers publish measured cost and operating limits.
- **Implementation scope:** Reconcile compute/storage/provider costs and publish supported quotas, queue/capacity limits and scaling triggers.
- **Out of scope:** Excludes SP-39.a revalidate final supported capacity envelope. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-39.a](#sp-39-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Cost separates measured/estimated/unknown and provider versus platform.
- **Required automated tests:** Usage sum, manifest identity and limit/config consistency checks.
- **Security and reliability:** No unlimited scale or future price promises.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-40"></a>
## SP-40 — Complete independent assurance and operations

Parent: [#42](https://github.com/spei04/strange-physics/issues/42). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-40-a"></a>
### SP-40.a — Book independent assessment and support roster

- **Objective:** Obtain independent assurance and demonstrated operational support. This PR delivers book independent assessment and support roster.
- **Implementation scope:** Reserve assessor window, scope APIs/build/runtime/evaluator and appoint ≥4 trained responders with explicit coverage.
- **Out of scope:** Excludes SP-40.b remediate independent assessment findings; SP-40.c exercise incident and credential response; SP-40.d start final-candidate slo evidence collection; SP-40.e review 30 calendar days of slo evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-00.c](#sp-00-c), [SP-19.a](#sp-19-a). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** External assessment slot and actual on-call plan confirmed before GA window.
- **Required automated tests:** Checklist validates trained primary/secondary and escalation coverage.
- **Security and reliability:** No unsupported 24/7 commitment; lead time external.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-40-b"></a>
### SP-40.b — Remediate independent assessment findings

- **Objective:** Obtain independent assurance and demonstrated operational support. This PR delivers remediate independent assessment findings.
- **Implementation scope:** Triage actual assessment, implement bounded fixes and independent retests with exact artifact references.
- **Out of scope:** Excludes SP-40.a book independent assessment and support roster; SP-40.c exercise incident and credential response; SP-40.d start final-candidate slo evidence collection; SP-40.e review 30 calendar days of slo evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-40.a](#sp-40-a), [SP-35.c](#sp-35-c), [SP-37.f](#sp-37-f), [SP-38.c](#sp-38-c), [ASSESSMENT](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ID](#contract-id), [C-EXEC](#contract-exec); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No exploitable critical/high finding; approved lower-risk exceptions dated.
- **Required automated tests:** Reproduce/retest each accepted finding plus relevant regression suites.
- **Security and reliability:** Five days is triage/initial reserve, not a cap on required remediation.
- **Effort and confidence:** 5 delivery engineer-days; low confidence; +2.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security, Backend, backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-40-c"></a>
### SP-40.c — Exercise incident and credential response

- **Objective:** Obtain independent assurance and demonstrated operational support. This PR delivers exercise incident and credential response.
- **Implementation scope:** Run outage/credential-compromise exercise with real roster, communication templates and recovery actions.
- **Out of scope:** Excludes SP-40.a book independent assessment and support roster; SP-40.b remediate independent assessment findings; SP-40.d start final-candidate slo evidence collection; SP-40.e review 30 calendar days of slo evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-40.b](#sp-40-b), [SP-39.b](#sp-39-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-ID](#contract-id); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Operators demonstrate target acknowledgement/containment under agreed coverage.
- **Required automated tests:** Automated alert routing, revocation and runbook command checks.
- **Security and reliability:** No live customer notification during drill without authorization.
- **Effort and confidence:** 4 delivery engineer-days; low confidence; +2.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Platform, QE, security, Backend. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-40-d"></a>
### SP-40.d — Start final-candidate SLO evidence collection

- **Objective:** Obtain independent assurance and demonstrated operational support. This PR delivers start final-candidate slo evidence collection.
- **Implementation scope:** Verify counters/denominators and synthetic checks on production pilot release candidate; freeze observation identity.
- **Out of scope:** Excludes SP-40.a book independent assessment and support roster; SP-40.b remediate independent assessment findings; SP-40.c exercise incident and credential response; SP-40.e review 30 calendar days of slo evidence. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-40.c](#sp-40-c), [SP-32.b](#sp-32-b). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Collection covers eligible requests, launch and execution metrics with private evidence.
- **Required automated tests:** Counter reconciliation, failure injection and missing-data detection.
- **Security and reliability:** Low traffic includes disclosed synthetics; data gaps invalidate window.
- **Effort and confidence:** 4 delivery engineer-days; medium confidence; +1.00 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL2. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-40-e"></a>
### SP-40.e — Review 30 calendar days of SLO evidence

- **Objective:** Obtain independent assurance and demonstrated operational support. This PR delivers review 30 calendar days of slo evidence.
- **Implementation scope:** Review complete rolling-window history, outages/exclusions, error budget and configuration changes.
- **Out of scope:** Excludes SP-40.a book independent assessment and support roster; SP-40.b remediate independent assessment findings; SP-40.c exercise incident and credential response; SP-40.d start final-candidate slo evidence collection. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SLO_OBSERVATION](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops), [C-GOV](#contract-gov); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** 30 calendar days complete; objectives and incident evidence satisfy GA gate or window restarts/rebaselines.
- **Required automated tests:** Window continuity, denominator, SLI and source-identity checks.
- **Security and reliability:** Material affecting change requires fresh relevant evidence; no fabricated uptime.
- **Effort and confidence:** 3 delivery engineer-days; low confidence; +1.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Quality engineer; base reference lane QE. Required review: Platform, QE, security, Technical lead, product. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="epic-sp-41"></a>
## SP-41 — Approve GA release and post-launch review

Parent: [#43](https://github.com/spei04/strange-physics/issues/43). This issue closes only when its leaf tasks and applicable gate evidence pass.

<a id="sp-41-a"></a>
### SP-41.a — Sign evidence-based GA readiness

- **Objective:** Release only against verified gates and learn from actual launch outcomes. This PR delivers sign evidence-based ga readiness.
- **Implementation scope:** Reconcile REQ01–16, support/data terms, release identity, residual risks and signed gate owners.
- **Out of scope:** Launching before signed release authorization.
- **Prerequisites and dependencies:** [SP-32.c](#sp-32-c), [SP-33.c](#sp-33-c), [SP-36.d](#sp-36-d), [SP-39.b](#sp-39-b), [SP-40.e](#sp-40-e). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** No blocking requirement unresolved; product/security/research/platform sign exact candidate.
- **Required automated tests:** Traceability, artifact hash, required-gate and exception-expiry checks.
- **Security and reliability:** GA approval is separate from backlog approval.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-41-b"></a>
### SP-41.b — Execute approved progressive GA rollout

- **Objective:** Release only against verified gates and learn from actual launch outcomes. This PR delivers execute approved progressive ga rollout.
- **Implementation scope:** Run canary/progressive deployment with monitored health, bounded expansion and rehearsed rollback.
- **Out of scope:** Excludes SP-41.a sign evidence-based ga readiness; SP-41.c conduct day-seven launch review; SP-41.d conduct day-thirty planning reset. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [SP-41.a](#sp-41-a), [GA_RELEASE](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Supported deployment passes canary and release manifest records actual outcome.
- **Required automated tests:** Canary synthetic journey, invariant and rollback-trigger checks.
- **Security and reliability:** Stop on security/state/availability regression.
- **Effort and confidence:** 3 delivery engineer-days; medium confidence; +0.75 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Platform/SRE engineer; base reference lane PL1. Required review: Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** R8; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-41-c"></a>
### SP-41.c — Conduct day-seven launch review

- **Objective:** Release only against verified gates and learn from actual launch outcomes. This PR delivers conduct day-seven launch review.
- **Implementation scope:** Review actual adoption/support/cost/incidents and prioritize scoped corrective work.
- **Out of scope:** Blocking pre-GA release on a future postlaunch event.
- **Prerequisites and dependencies:** [POST_LAUNCH_D7](#external-and-calendar-gates). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** D7 evidence and owners recorded; no change to prior release identity.
- **Required automated tests:** Automated operational/adoption summary reconciliation.
- **Security and reliability:** Privacy-safe reporting; unique incident evidence retained.
- **Effort and confidence:** 2 delivery engineer-days; medium confidence; +0.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** POST; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

<a id="sp-41-d"></a>
### SP-41.d — Conduct day-thirty planning reset

- **Objective:** Release only against verified gates and learn from actual launch outcomes. This PR delivers conduct day-thirty planning reset.
- **Implementation scope:** Compare 30-day outcomes to objectives and propose evidence-driven next-quarter work.
- **Out of scope:** Excludes SP-41.a sign evidence-based ga readiness; SP-41.b execute approved progressive ga rollout; SP-41.c conduct day-seven launch review. Also excludes release authorization and expansion beyond the accepted law/deployment scope.
- **Prerequisites and dependencies:** [POST_LAUNCH_D30](#external-and-calendar-gates), [SP-41.c](#sp-41-c). Required inherited approvals must actually be recorded; predicted dates confer no authority.
- **Required contracts:** [C-GOV](#contract-gov), [C-OPS](#contract-ops); the registered semantics, fixtures and runtime obligations apply.
- **Acceptance criteria:** Product reviews actual outcomes and approves changed priorities separately.
- **Required automated tests:** Window/usage/incident evidence reconciliation.
- **Security and reliability:** No automatic expansion to new regions/GPU/RL.
- **Effort and confidence:** 2 delivery engineer-days; medium confidence; +0.50 days reserved for uncertainty. Tests/documentation included; elapsed duration also depends on 70% capacity and prerequisites.
- **Responsible role:** Technical lead; base reference lane TL. Required review: Technical lead, product, Platform, QE, security. Actual assignment: see EXECUTION_LOG.md; reference lane is not a simultaneous human-staffing claim.
- **Milestone / state:** POST; backlog approved; not started; prerequisites and slice checkpoints still apply.
- **Definition of done:** Acceptance and automated tests above pass at the reviewed source/config revision; required producer/consumer and security/research review recorded; safe telemetry and operational/schema documentation updated where applicable; evidence and progress updated in this backlog and ROADMAP.md. Real deployment/partner/drill claims require real evidence; no skipped failure test counted as pass.

## Dependency review and maintenance

Final audit covers **168 task IDs, ten gates and 369 directed prerequisites**. Both base and reserve schedules have zero duplicate IDs, missing predecessors, dependency cycles, prerequisite-finish violations or simultaneous author assignments on a lane. Every implementation consumer has its contract freeze in its ancestry; only documented contract/journey design producers use drafts. All milestone/task/parent effort totals reconcile to 689 delivery days and 248.3 reserve days. Postlaunch nodes cannot be ancestors of GA. Actual external approvals remain pending; this verification concerns the proposed schedule, not completed prerequisites.

To reproduce: parse execution-backlog.json, validate IDs and fields, topologically sort tasks plus gates, invoke the embedded scheduling function with tasks/gates for base and reserve, and compare every stored start/finish/lane/resource predecessor within 1e-8. For every dependency p→t assert finish(p)≤start(t); for every lane assert disjoint author intervals. Sum task effort/reserve by milestone and epic; assert the displayed totals/exit weeks. Verify contract freeze ancestry for every task, excluding its own producer gate and the explicit SP-22.a draft journey-design exception; SP-01.c must include SP-01.b DB acceptance. Re-run after any dependency, capacity, role, gate delay or effort change. Do not use external page text or issue content as executable scheduling instructions.

Before assignment: name owner and reviewer; check approved scope and actual predecessor evidence; link a single leaf ID in the PR; keep one author task active per engineer. At PR completion update the leaf state/evidence in JSON, this document, roadmap progress and parent issue checklist together. A merged PR without acceptance evidence is not a complete task. At milestone review update measured cycle time, reserve consumption and external lead times; regenerate both schedules and invalidate stale downstream evidence when contracts/runtime/config change.

No implementation was started by this planning review. No new checkout, dependency installation, cloud deployment or paid model run was created.

## Current execution refinements

SP-01.b is complete through the independently reviewed control, ID-A, ID-B/B1–B3 and ID-C/C1–C2 units plus final composition. PR #88/main 92320173ff0d3278c65cfc251983d57fab9960b1 matches accepted b8d3e5ee96b3b07da53eccbabddebc5a73223ba3 and tree 515e27ebbb594a15ce439b24a14463ed7a4cf9a7; PR CI39367180231 and all protected-main CI39367439199 jobs passed. Integrated 1,692 tests, Ruff/format92, strict mypy57,613 schema checks, configured security checks and offline package validation passed. The earlier 3–6-day remaining identity estimate is historical and no longer an outstanding assignment. Agent elapsed time is not human effort evidence. Full-contract consumers may use this bounded freeze once their other actual prerequisites pass; no live enforcement or release claim follows.

SP-01.c/#89 is complete through three sequential reviewed units: ART1 immutable artifact/checkpoint identity, EXEC1 package/build/worker authority, and COMP1 native-model provenance and recovery. Exact PR/main checks passed. SP-01.d/#94 is complete through WORLD1 PR #95 and WEB1 PR #97; Quality now owns SP-01.e/#98 VAL1. CORE/SCI bytes and the integrated local I1 workflow stay unchanged. These pure contracts do not establish live producers or deployment.

The coordinated [CI-01 request](https://github.com/spei04/strange-physics/issues/54) adds bounded repository CI/CD maintenance. It does not waive the cloud storage/provisioning gates or complete SP-27.a. Repository-settings coordination owns branch protection; candidate delivery requires protected main and successful required checks. Publication/deployment remain separately gated.

Execution checkpoint 2026-10-20: SP-01.b/c/d and bounded I1 are complete. Quality owns SP-01.e/#98 VAL1; Research and Platform review, and lead integrates. SP-02.b capacity is complete after the approved recovery snapshot and expansion; staging remains NO-GO. Capacity acceptance is not a restore rehearsal or production-readiness claim. Journey/staging documentation does not approve UI or provisioning.


Scientific execution checkpoint 2026-10-20: Research's read-only dependency review
confirms SP-02.b → SP-03.a → SP-03.b → SP-04.a → SP-04.b → SP-06.a → SP-04.e/I1,
with the additional approved joins and accepted predecessors recorded in
[EXECUTION_LOG.md](EXECUTION_LOG.md#scientific-acceptance-checkpoint--i1-complete).
SP-06.a/#83 and SP-04.e/#87 are integrated; bounded I1 is complete through PR #90.
SP-01.b/c/d are integrated; Quality owns SP-01.e/#98 VAL1 after accepted WEB1 integration. The six scientific tasks retain
19 reference engineering days plus 4.75 reserve, not a subagent schedule promise.
No unfinished identity contract or whole-R0 gate is a prerequisite for this local
slice. Enterprise work and its actual consumer gates remain unchanged. I1 has
purchased-prefix-only fitting, unseen-condition predictions and independent
analytic scoring with explicit failures through the installed SDK/CLI;
all24 preregistered probes satisfy the fixed per-probe error gate. The concrete disk/snapshot action is approved and complete;
SP-03.a is integrated through PR #76/main 8510243 with matching tree and passing
PR/main CI. SP-03.b/#75 is integrated through PR #78/main db182788 with matching reviewed tree
and passing PR/main CI, including 817 tests. SP-04.a/#77 is integrated through PR #80/main e5a3c8d with a matching
reviewed tree and passing PR/main CI, including 1,006 tests. SP-04.b/#81 is integrated through PR #82/main 9c341f8 with passing PR/main CI,
1,320 tests and all 1,680 unseen predictions inside the fixed per-probe limit. Noise sensitivity failures remain explicit; no
thresholds or manifests were relaxed.

ART1 integration checkpoint: lead owns primary integration of accepted7a90e96 with accepted SDK/I1 progress8cf6fea at5ad0ef3. Both schema-validator additions and the exact36-entry package allowlist survived independent union review. Platform released identity clean for sequential reuse after main acceptance; no new checkout. EXEC1 and COMP1 remain separate dependent review units, and full SP-01.c freeze remains open.

Historical ART1 completion and EXEC1 API assignment (superseded by the current board): PR #91/main95bdd85e6163147b6b1e29e6f59648a02e8c3d59 matches reviewed8c282eb2072e59c43290ea10991e09adc990d5b6 and treecb539fa21f89ffc5562a66f2c1fa42cb5acdec07; PR CI39370833204 and all five protected-main CI39370975462 jobs passed. Platform receives the reused identity checkout for EXEC1 API contracts/fixtures after this record’s review and explicit handoff; independent API review precedes predicates. Research reviews runtime provenance and SCI boundaries; Quality reviews authorization/lifecycle. Lead maintains primary progress and integration. Full SP-01.c freeze, live enforcement and paid/release gates remain open.

Historical EXEC1 runtime assignment (superseded by accepted runtime and integration preparation below): the API at57f2f303a5fec4b65b1df022b4239a64f537f6bc is accepted by lead, Quality and Research after chronology, lookup-uniqueness, normal-completion and aggregate-configuration repairs. Platform retains exclusive identity source ownership for bounded current-authority/replay/broker/termination predicates. Independent runtime review and exact PR/main checks remain; COMP1 and the full SP-01.c freeze are not complete. The four delivery plus one reserve days and all baseline dependency/gate records remain unchanged.

Production ledger measurement: one schema-valid maximum-shape Operation at57f2f303 serialized to1,757,976 bytes; a10,000-operation history extrapolates to17,579,767,781 bytes (about16.37GiB). No giant history was allocated. Count limits and pure conformance predicates do not prove bounded database reads. Exact existing producer owners and acceptance evidence are added above at SP-09.d, SP-12.a, SP-13.c and SP-16.b; SP-11 retains authorization. COMP1 must preserve actual canonical prefix identity with an explicit byte bound or verified streaming producer. Baseline task graph and estimates remain unchanged.

Historical EXEC1 integration preparation (completed by the acceptance below): EXEC1 runtime fe3b0088d4bca0623459f9024eceb42036e8d491 and doc-only author c66b6a0d6bc82a81195797c742353718bc155136 are independently accepted. All2,281 tests,615 focused cases,722 schemas,Ruff/format112,full mypy74,configured Bandit and offline archive checks passed. Three related lifecycle/history defects were repaired; Quality independently checked84 state/instance combinations,65 receipt histories and6 chronology cases. Research and lead each passed12 additional cases. Pure predicates remain distinct from live producers. Final PR #92 and protected-main checks are pending; COMP1 and full SP-01.c remain open.

EXEC1 completion and COMP1 assignment: EXEC1 is complete through PR #92/main750db15810f4a58a4a8d34776cb3708dc310ef5a, matching reviewed671f10930a743acfb9da888a0eb2c97c6e7f471f/tree13894d9c09bdde0ae8278a5a331c56b377a485fc. All four PR CI39375391014 and all five main CI39375611645 jobs passed. Local2,281 tests,722 schemas,full typing/static/security/package checks and independent lifecycle/provenance review are accepted. The verified candidate artifact12242708007 is retained privately outside checkouts; this is not a published release or live hosted readiness claim. Research receives the reused identity checkout after this record’s review, with an early API checkpoint before runtime. Platform reviews provenance/build/persistence, Quality reviews authorization/recovery, and lead owns progress/integration.

COMP1 runtime assignment: API21cb20146bea3ff42aa15dafe43136ff24ff6081/tree d3e0b3417dfc518215e19123a7fb5c185268e420 is independently accepted;422 focused cases,764 schemas,static/type checks and independent boundary/mutation reviews passed. Research retains exclusive identity ownership for runtime. Platform reviews bounded bytes, actual SCI prefix/original engine and native approval renewal; Quality reviews broker authority, current-state replay and async recovery; lead owns primary progress/integration. The repaired pairwise worker-revision chronology and private actual PredictorVersion compatibility do not change CORE/SCI, public worker contracts, baseline task dependencies, estimates or gates. Full SP-01.c remains in progress.

Draft COMP1 API CI: PR #93/a629729 passed all four applicable CI39377520114 jobs, preserving accepted API21cb201 and reviewed progress. Runtime and full SP-01.c acceptance remain pending; this is early API evidence, not final runtime or hosted-production evidence.

COMP1 runtime integration checkpoint: runtimeb7c944c and finalauthor3ceb846 are independently accepted.2,423 tests,141 focused COMP1 cases,764 schemas,static/type/security/offline package checks passed; independent authorization, prefix, renewal and recovery reviews are recorded in EXECUTION_LOG.md. Combined60a8ac5 preserves accepted source and status annotations. Lead integrates through draft PR #93; exact final PR/main CI remains before SP-01.c completion. Research/Platform prepare SP-01.d read-only; source waits the accepted parent and writer handoff. Hosted production and paid/release gates remain open.

Final integrated60a8ac581fcfed2df9f9381ce116b6d905064242 checks passed2,423 tests,Ruff/format117,mypy78 and764 external schema cases. The private integrated-check index SHA256989c28e24c32236165b6351f1c031a5d7385d188921d55816e2a69c1318e0100 binds the immutable source and captured results; subsequent changes are progress-only. Exact final PR #93 and protected-main CI remain before merge/parent acceptance.

COMP1 completion and SP-01.d handoff: COMP1 and SP-01.c are complete through PR #93/main11e200253347dc05973e5d7969a3abd145f285e2, matching revieweda75ac1b7099aa8d38d62577d14315dfeb5009f49/treeec01b963f20e95f682ef06a04bcebcd4350db862. All four PR CI39379345399 and all five protected-main CI39379544409 jobs passed. The exact integrated source passed 2,423 tests, 764 schema cases, Ruff/format and strict typing; independent boundary, recovery and composition reviews are accepted. Candidate artifact12245465046 was checksum/provenance verified and retained privately outside checkouts. These are pure contracts and predicates; live SQL/storage/HTTP/build/controller/isolation producers remain later tasks.

Research is assigned SP-01.d/#94 in the existing identity checkout after this record is reviewed and the lead explicitly hands off the writer. WORLD1 covers immutable world/version views, browser-only current authorization, explicit preview grants and exact selected-world/run binding. WEB1 follows in a separate PR for streams, snapshots, cursors, replay and large-artifact retrieval. Each unit requires an API/fixture checkpoint before pure runtime predicates. Platform reviews preview/provenance and producer boundaries; Quality reviews authority/recovery/schema consistency and retains read-only SP-01.e preparation. Lead owns primary integration and progress. No dependency, estimate, paid, research-amendment or release gate changes.

WORLD1 source assignment began 2026-10-20 06:23 UTC after Quality accepted handoffc74975b. Research owns the reused identity checkout; Platform/Quality review, lead integrates. The four delivery plus one reserve days, dependencies and gates are unchanged.

WORLD1 API fd6bac2 is independently accepted with 2,600 tests and 1,201 external schema checks. Research is assigned runtime; Platform reviews transition/provenance and Quality current authority/recovery. The accepted types do not establish live storage, HTTP or UI, and SP-01.d remains open through WORLD1 runtime and WEB1.

SP-01.d consumer preparation: one accepted synthetic maximum-count scientific record measured 1,779,612 canonical bytes and needs 28 batches at 64 KiB, supporting the existing 4 MiB raw-body reference bound without proving a global maximum or load behavior. Preserve explicit raw caps and incomplete/oversized failure semantics. Draft WORLD1 PR #95 has passing API-only CI; runtime and WEB1 acceptance still precede full freeze.

WORLD1 runtime 8555602 passed 2,732 full tests and 1,201 schema cases; test-only abdf849 repairs explicit shared-helper imports and passes full strict typing. Independent review found three retained-predecessor consistency gaps in version/grant retry histories. Research owns bounded repairs; Platform and Quality verify the replacement, and lead holds integration. Shared authorization/parser extraction is independently accepted. WEB1 and complete SP-01.d remain pending.

Historical checkpoint (subsequently qualified below): WORLD1 runtime 9267733 was accepted by lead, Platform and Quality after 2,768 full tests, 345 WORLD1 cases, 542 broader focused cases, 1,201 schema checks, Ruff/format127 and strict mypy87. Retained predecessor/ancestor ID and chronology checks, grant renewal-distance consistency and safe head reads were repaired and regression-tested. Exact final PR #95 and protected-main CI remain before integration acceptance. WEB1 and the SP-01.d parent freeze remain open.

Final composition qualified the earlier 9267733 acceptance: the original receipt parent/version pair also needs validation. Research repaired that supplied pair at6abdb3 and retains the identity writer while Platform checks visible version-ID reuse at fresh append allocation; Quality verifies all six supplied-record pairs. Publication and full final acceptance remain held for the replacement. Existing full-test evidence stays attached to its original source.

2026-10-20 08:04 UTC — Final WORLD1 runtime2b882fe is accepted by lead, Platform and Quality after 2,783 full tests, 360 WORLD1 cases, 557 broader focused cases, 1,201 schemas, Ruff/format127, strict mypy87, static security and offline package/installed-callable checks. Final composition repairs validate all six supplied historical/current version pairs and prevent fresh allocation from reusing a visible version ID; valid retries still ignore unused allocation inputs. Final authorf7b1cb1 changes documentation only. This supersedes the qualified9267733 acceptance. Exact final PR #95/main checks remain before integration acceptance; WEB1 and full SP-01.d remain open.

## WORLD1 integration and next assignments

2026-10-20 08:13 UTC — WORLD1 is complete through PR #95/maincaeb58adae55e77187446ac65dc3c85cd98ce37c, matching reviewede42fb87c19a9ffe95edc26c91a9a806e17d1e260/tree648f7775f5ae1b4dc72d72f3833b659fbaf4a977. All four applicable PR CI39391162963 and all five protected-main CI39391431584 jobs passed. The reviewed runtime passed 2,783 tests, 1,201 schema fixtures and configured static/type/security/package checks; current authority, retained-history and allocation repairs were independently accepted. Candidate artifact12249238534 was checksum/provenance/source verified and retained privately. This accepts pure contracts/proposals; live HTTP/database/storage producers remain later work.

Research receives WEB1 API/fixture authoring in the existing identity checkout after the lead verifies this handoff; Platform reviews stream/artifact joins, Quality reviews current authority/recovery and lead owns primary integration. The first checkpoint defines bounded events, cursors, immutable snapshot/archive recovery and exact scientific artifact retrieval before runtime predicates. Viewer reads use current browser/service runs:read, including terminal runs, without worker-lease requirements. SP-01.d stays in progress and SP-01.e stays preparation-only until WEB1 is accepted.

Research and Quality independently audited the planned36-episode local comparison. Its29-node prerequisite closure contains14 accepted nodes and15 unfinished nodes: eight RA tasks, six baseline tasks and pendingRA_EXEC. It has no WEB1, hosted deployment or provider prerequisite. However, native LinearSpringModel selection still depends transitively on symbolic execution and all-family calibration/sparse/bootstrap work. Preserve this graph now; the recommended planning decision is a separately reviewed native-only belief/calibration and fixed-menu/acquisition path using accepted spring fitting/prediction/scoring, with source/license provenance, manifest/cost, arm isolation and discrepancy-scale safeguards retained. This proposal does not approve RA_EXEC or complete the broader tasks.

Next executable scientific preparation: Research owns the native-versus-rich prerequisite proposal and fixed manifest/oracle design; Quality reviews isolation/calibration/accounting and Platform reviews provenance. After explicit RA_EXEC acceptance, the first RA implementation is RA-01 (Research + Platform): dated source/license/recipe go/no-go evidence. SP-03.c and SP-19.a are dependency-ready baseline tasks but need separate assignment outside the completed bounded I1 slice. Any authorized comparison must first freeze pool/priors/likelihood, common calibration and candidate menu, six world identities, two seeds, budget/failure policy, discrepancy scale and sensitivity, disjoint scoring probes and complete output records. Retain36 episodes,12 slots including4 common calibrations,432 maximum slots,8 CPU-core-hours,1GiB new artifacts, existing machine and zero network/provider/provisioning; incomplete outcomes stay visible, with no population/adaptation/official-score claim.

WEB1 API authoring started 2026-10-20T08:15:54.588377+00:00 at accepted handoff69c027c after WORLD1 exact PR/main and candidate acceptance. Research owns the reused identity checkout; Platform reviews stream/artifact joins, Quality current authority/recovery and lead primary integration. Runtime predicates wait for API review. Pins are unchanged; no active prior consumer, cross-checkout dependency symlink or mutable hardlink remains. Available space 103,439,900,672 bytes; no additional checkout or installation.

The [native comparison prerequisite proposal](research/NATIVE_COMPARISON_PROPOSAL.md) defines five small PR tasks, an honest native producer/prediction/scoring adapter and explicit replacement dependencies. It is unapproved planning only; the active graph and RA_EXEC remain unchanged. Independent review precedes any implementation or comparison authorization.

2026-10-20 08:41 UTC — WEB1 API checkpoint3b01cfc passed 2,928 full tests and1,373 schema cases, but independent review requires bounded history-link/count and recovery/header-schema repairs before acceptance. Research owns those repairs in identity; Platform reviews stream/artifact provenance, Quality authority/recovery, and lead primary integration. Lead passed102 independent wire/token/counter/signed-zero and parameterized frame/batch-bound checks. Existing evidence remains tied to3b01cfc; runtime waits replacement review. No hosted producer, native research gate or full SP-01.d acceptance is implied.

2026-10-20 — Quality accepted the native comparison prerequisite proposal as planning-only after independent source, DAG, closure and effort checks. The five tasks and RA-07.b prerequisite replacement are reviewable in docs/research/NATIVE_COMPARISON_PROPOSAL.md. No dependency amendment, RA_EXEC, experiment or infrastructure gate has been activated. WEB1 replacementc066900 is under independent delta review.

2026-10-20 — WEB1 APIc066900 is accepted by lead, Platform and Quality after2,962 full tests,405 focused cases,1,431 external schemas and configured formatting/type/security checks. Review repaired supplied history identity/count feasibility and recovery/header schema parity. Research is assigned bounded runtime in the reused identity checkout; Platform reviews state/provenance/budgets, Quality current authority/recovery and lead primary integration. Every delivery boundary needs fresh browser/service authorization; terminal reads require no worker lease. Full history completion must reject nonadjacent consumed identity reuse and preserve cumulative budgets; actual raw bytes must verify before first delivery. No hosted producer or full SP-01.d completion is claimed.

Planning PR #96 is integrated as ee4831a with reviewed tree3192574; all four applicable PR and five protected-main checks passed. Its native comparison tasks remain a published proposal; the separate scope/RA_EXEC/run decision is pending.

2026-10-20 — Draft PR #97/API integrationf2614ac passed all four applicable CI39396521384 jobs. Partial runtimebc82a23 (70 new tests,378 focused cases) is under independent review. Lead reproduced two missing supplied chronology checks: an event later than its cursor issuance, and a final event later than snapshot capture. Research owns the repairs and separate actual-byte/history unit; Platform checks provenance/state and Quality current authority/recovery. Valid same-second records remain required. Runtime acceptance and full SP-01.d remain open.

2026-10-20 — Partial WEB1 runtimeac70f69 is independently accepted for current viewer authority, cursor recovery, historical snapshots and event batches. All reported chronology, recent-head consistency and error-ordering repairs pass;83 replay and179 API cases pass. Platform verifies the final head guards; Quality authority/outcome and lead chronology evidence remain bound to their reviewed sources. Research now completes actual-byte body/history runtime, Platform reviews provenance/budgets, Quality authorization/recovery and lead primary integration. Full WEB1, SP-01.d and SP-01.e remain pending; this is not hosted enforcement.

2026-10-20 09:13 UTC — Draft PR #97 partial integration e5a6162 failed full CI39398415065 on both Python versions: tests/test_run_credentials.py was discovered under two module names. Security passed; this does not invalidate scoped behavioral review, but integration remains unaccepted. Research owns a test-import convention repair and full mypy src tests examples before the body/history checkpoint. No check settings or acceptance criteria are weakened.

2026-10-20 — WEB1 body/history checkpoint96f4b57 passes312 focused tests and full strict mypy95, including the CI test-import repair. Lead passed44 independent large-body delivery/current-authority cases. Platform identified two missing supplied snapshot joins in single replay-body retrieval; Research repairs them while Platform and Quality complete independent review. Full WEB1/SP-01.d acceptance remains open.

2026-10-20 — WEB1 runtime85c0a98 is independently accepted after captured-run/final-event and exact replay-request binding repairs. Annotation source00800555 changes only WEB status metadata and documentation; final source checks remain active. Quality has prepared SP-01.e/#98 as VAL1 public fixtures/drift checks, CLIENT1 pinned TypeScript compatibility and MOCK1 deterministic streams. Its first manifest/fixture checkpoint and source authoring wait for exact WEB1 PR/main acceptance and the identity writer handoff; existing task dependencies and estimates remain unchanged.

2026-10-20 — Final WEB1 source f2d1068 passes3,104 tests,321 WEB cases,1,431 external schemas, Ruff/format136, strict mypy95, exact configured Bandit and offline package/installed-callable checks. Final author b5f69f0 adds evidence documentation only. Runtime85c0a98 is independently accepted by lead, Platform and Quality; exact PR #97/main and private candidate verification remain before SP-01.d completion. Quality is assigned SP-01.e/#98 next, beginning with VAL1 manifest/fixtures after writer release and exact integration.

2026-10-20 — SP-01.d is complete through WORLD1 PR #95 and WEB1 PR #97/main15714e6ac4b6b300f0170e5aa22722987decd786, matching reviewed73d943b8bfb96be6a898a511af3053e4e5cca568/tree0a10921751ced4f6bf3120035ab102630067b60d. All four applicable PR CI39402376299 and all five protected-main CI39402868552 jobs passed. WEB1 passed 3,104 full tests, 321 focused cases, 1,431 external schema cases, configured lint/type/security checks and offline package/installed-callable checks. Independent reviews accepted the repaired snapshot, event and exact-request joins. Candidate artifact12255421593 was checksum, provenance, lock and packaged-source verified and retained privately. These are pure contracts and predicates; live HTTP/database/storage producers remain later tasks.

Quality owns SP-01.e/#98 VAL1 in the reused identity checkout at accepted WEB1 main15714e6. The first immutable checkpoint contains the public-root/audience manifest, synthetic fixtures and raw/canonical byte goldens. Research reviews scientific identity and fixture semantics; Platform reviews public/private boundaries, references and drift. Generator and CI integration follow checkpoint acceptance; CLIENT1 and MOCK1 remain separate. Lead owns primary integration and progress. No additional checkout or dependency installation; the native proposal and RA_EXEC remain pending.

2026-10-20 — The reviewed [native sequencing recommendation](research/NATIVE_COMPARISON_PROPOSAL.md) keeps finite-grid calibration before the first comparison and moves Laplace implementation plus its approximation-versus-grid audit to later RA-N02.b. Proposed first-result effort is 17–26 engineer-days (21.25–32.5 with reserve); later Laplace is 3–5 (3.75–6.25 with reserve), low confidence. Full programme scope, active dependencies, RA_EXEC, run caps and GA forecast remain unchanged. This is saved planning only.

2026-10-20 — VAL1 manifest/fixtures 10145929997fc959fe31ba0398cdf8dac62e4934 (tree a7daa18e4506d268d334b05f14949da0ec0f8838), published in draft PR #101, are independently accepted after the six review corrections. All 87 focused tests, 1,431 external schema cases and configured static/type/security checks pass; Research adds 150 independent checks, and Platform verifies 96-root closure and repair-sensitive boundaries. Quality retains identity for the next generator assignment. Generation/drift CI, CLIENT1 and MOCK1 remain pending; SP-01.e stays in progress. Planning PR #100 is separately reviewed at 0ecf4f4; active research dependencies and RA_EXEC are unchanged.

## 2026-10-22 — Native candidate/accounting checkpoints

N01 candidate contracts and RA-02 accounting are integrated through PRs #109/#110.
PR #110/main f9f450b passed required CI and exact package verification. Native
candidate production and prediction at c3988d9 pass 3,714 tests and independent
Quality/Research review. At this source-review checkpoint, runtime delivery awaits
exact PR/main/candidate verification; issue #106 records delivery evidence as accepted.
Full source identities and scoped evidence are in execution-backlog.json.

Both #105 and #106 remain in progress. N01 must still bind the actual Journal,
prefix, selected candidate, prediction and scoring protocol to the independent
evaluator, preserve disjoint probes and distinguish missing/invalid predictions
from evaluator failure. RA-02 must then publish scored cells with those actual
artifacts, resolved purchases and complete cost accounting. Their acceptance
precedes RA-N02.a grid inference/reference checks; RA-N03 calibration and RA-N04
selectors follow that gate. Actual study freeze and RA-07.b comparison still wait
for all prerequisites. See the [assignment log](EXECUTION_LOG.md). Graph, efforts,
forecast and cumulative 36 episodes/432 slots/8 CPU-core-hours/1 GiB/no-reset limits
are unchanged. Runtime fixture tests are not calibration or a research comparison.

## 2026-10-22 — Pure scoring checkpoint and remaining composition

Candidate production and prediction are delivered by PR #111/main c0e4c86:
PR CI 39750341047, all five main CI 39750648032 jobs and candidate 12413204172
are accepted. Pure scoring runtime da3d529, released at e21dfdc, passed 3,801
tests, 1,487 schema checks, configured static/type/security/package checks and
independent Quality/Research review. Exact scoring PR/main/package verification
is still required for delivery; issue #106 records acceptance when verified.
Full source and evidence identities are in execution-backlog.json.

Quality next owns the actual-Journal adapter and scored-cell publisher; Platform
owns the honestly labelled same-prefix classical diagnostic; Research reviews
both. Source work starts only after scoring delivery and explicit reuse of the
two existing checkouts. The publisher must reconcile the actual Journal itself,
require all 12 purchased rows with no pending or missing charged intents, and
bind the full prefix, selected candidate, policy, protocol, predictions, report
and measured ledger attempts. The preparation operation currently binds menu;
the new preparation facts bind scoring_policy. Resolve that mapping explicitly
without relabelling a digest. The classical diagnostic uses the actual same
prefix and the existing fitter/config, with failures retained and no substitution
for the primary native candidate.

Before any measured run, the runner must capture actual CPU, wall time and new
artifact bytes for every cost-bearing operation, preserve unknown usage and
retry reservations, persist ledger revisions safely, and recover without a
budget reset or duplicate settlement. Pure facts and update proposals do not
prove those producers. These remain explicit measurement/persistence obligations,
alongside actual-Journal publication and diagnostic acceptance.

Both parent tasks remain in progress. Their completion precedes finite-grid
reference acceptance; calibration and selectors precede actual manifest freeze
and comparison. The cumulative 36 episodes, 432 slots, 8 CPU-core-hours and
1 GiB limits include reference, calibration, sensitivity, ranking, scoring,
retries, failures and later diagnostics. No comparison has run; component tests
are not calibration or research results. Graph, effort and forecast are unchanged.

## 2026-10-22 — Classical and actual-Journal source checkpoints

Pure scoring is delivered through PR #112/main 73d07b6, PR CI 39780967416,
all five main CI 39781313464 jobs and verified candidate 12425889219.
Classical runtime 0ff9e3b/final author c916d9d passed 3,874 tests and both
independent reviews. Journal adapter 531deb8 passed 3,866 tests and its final
comparison-scope repair was independently accepted. The latter reads the actual
Journal and full ledger, requires 12 charged/committed rows with no pending or
missing purchase intents, and binds native material, score and 27 attempt/facts
envelopes. It returns private evidence, not a complete-cell publication.

Lead integrates the released classical checkpoint first, then the Journal
checkpoint with the exact shared registration/schema union and joint checks.
Exact PR/main/package delivery remains required for each. Source identities,
review indices and counts are recorded in execution-backlog.json; issues #105
and #106 record delivery acceptance when verified. Both parent tasks remain
in progress and both existing checkouts are retained for sequential reuse.

The classical result stays separate from the native primary result. A real
terminal diagnostic failure does not invalidate a valid primary score; missing
or unknown diagnostic work keeps complete publication incomplete. Source/interface
verification uses explicit synthetic fixtures and actual fixture Journals.
Actual comparison publication still requires real posterior/MAP and selection
ordering, calibration, a frozen manifest, measured costs, durable persistence
and recovery. These later producers are not fabricated upstream dependencies.
No scientific comparison has run, and the graph, estimates and cumulative
36-episode/432-slot/8-CPU-core-hour/1-GiB no-reset limits are unchanged.


## 2026-10-22 — Classical delivery and Journal integration

PR #113 is accepted at main95f1735d94f3b34b3f5748e705f0805c81eb08e3,
tree dd5dd677897799880b15ebbcf63daf9ae823f340, identical to reviewed head
e1682fc8bd2c2637d39f073798039577d6d88e5a. All four applicable PR checks
passed in run39816999899 and all five protected-main jobs passed in
run39853486062. Candidate12458927169 passed bounded ZIP, source/lock/uv
provenance, checksum and exact64-file archive checks. Both archives match
the accepted author builds byte-for-byte. ZIP SHA256:
09e6ed7e3f1fd327854f0d60716b08e05799e6ce23e3ecc831fea372e5ce7221.
Private acceptance index SHA256:
afcf47ae49a80dbdf36972fe6e87d47b3da58d70da894df5c715f48d5ecb89c9.
Lead rehashed all eight indexed evidence files; runtime-requirements identity
matches the prior accepted lock/toolchain, without independently regenerated
export bytes. This is an unpublished CI package candidate.

Quality now owns the existing identity checkout for the exact Journal/classical
source union and permanent joint regression tests. Platform and Research review
the immutable combined source independently. Lead owns progress records in
primary, then Journal PR/main/package delivery after explicit writer/reviewer
releases. No new checkout is needed. The joint fixtures bind actual Journal
purchases, the same native/classical prefix and frozen-cell accounting; they
preserve the native primary result across diagnostic failures and retain
interrupted costs. They do not implement a complete-cell publisher.

Both parent issues remain in progress. Private publication composition, actual
cost measurement, durable persistence/recovery, inference/MAP, selection and
calibration remain required before the comparison. No comparison has run;
no cumulative cap, dependency, estimate or release forecast changed.


## 2026-10-22 — Reviewed Journal/classical integration checkpoint

Exact source0e6dc0d1d9ce9549e50022b13716944837a3501d, tree
88d073ddf97be48e6dae026f75eb59843ea8b8cf, combines Journal531deb8 with
accepted classical main95f1735. The union preserves235 parent component blobs;
only the two additive registrations, inherited native-study-scoring operation
enum and new19-case joint test file differ. All3,958 tests,1,503 schema cases,
Ruff/format168files, strict mypy119files, configured Bandit, pinned dependency
audit and offline66-file archive checks passed. A temporary installed wheel
ran actual synthetic Journal/native/classical/failure/interruption paths and
was removed. Platform accepted157 authored plus17 independent cases and two
guard mutations; Research accepted19 joint plus16 independent cases and one
guard mutation. Lead verified all37 author,15 Platform and11 Research indexed
artifacts. Author/Platform/Research index SHA256 values respectively:
14530c723db3d27d386c1d5bcb52fb58d3058b10b2774c837ee09fe3a87ae50c,
d157c6f70481a2421b0db561fedffe33d3d47e1fd58dbaf73cea2fa272205789,
b5d3e8c40d3cd02add6c5aac064335f072e29b2077193688ad5b3bf5ce25e2cf.

Lead owns final progress review and normal PR/main/package delivery after
explicit writer release. Research reviews the next bounded private publication
source slice; implementation waits for this delivery and an explicit checkout
handoff. The accepted runtime reads actual Journal/native-score evidence and
maps diagnostic work into the frozen ledger. The joint tests compose those
interfaces; no combined diagnostic publisher or complete-cell API is added.
Native primary results remain separate across diagnostic scored, unscorable,
failed and unresolved outcomes. Real measurements, durable persistence/recovery,
genuine inference/MAP, selection and calibration remain open. Both parent
issues stay in progress, and no scientific run or budget reset has occurred.

Quality released clean0e6dc0d to lead with no active consumers. Release index
SHA256:88a54a57a2a028b5ca1f9cb58db8a3992ff15a63c4bc2ed63814e2febe9d1dc4.
The two existing checkouts remain needed for delivery and the next authorized
source slice; no additional checkout or shared dependency installation was made.


## 2026-10-22 — Journal delivery and publication assignment

PR #114 delivered main9cb6e582001aa89e0f98f1cad1502d37548c29d3,
tree2425b8d203efe206187af12e351896bd3ed737e5, identical to reviewed
head3d3618703a260febb933cebf293a80a2e3a71e87. All four applicable PR
checks39856189431 and all five main jobs39856905014 passed. Candidate
12459573763 passed exact source/lock/uv/provenance/checksum/66-file archive
checks; both archives match accepted author bytes. ZIP SHA256:
d987839046e8f8d4ff883579fe8e67337737cc3ea0f61b2aecdbf9b33b459e82.
Acceptance index SHA256:
41f8abdb76f7e6af57d3fa483420d0d5432bb375a105f818472f34fb50909f24;
lead verified all11 indexed evidence files. The package remains an unpublished
CI candidate; this delivery is not a scientific result or hosted release.

Quality received the reused identity checkout at acceptedmain9cb6e58 for one
bounded private native/classical publication compose-and-propose source slice.
Pinned offline copy-mode sync, installed66-file source equality and5,289 singly
owned dependency files passed before handoff. Platform reviews event/replay/CAS,
cost and package boundaries; Research reviews actual material/outcome joins.
Lead owns primary progress and integration. The slice preserves existing outcome
bytes and separates evidence, event and receipt hashes; changed diagnostic or
raw material must conflict on replay, and unknown work cannot become complete.
Early purchase/selection/preparation-unavailable publication, real measurement,
durable persistence/recovery and genuine inference/selection/calibration remain
explicit obligations. Both parent tasks remain in progress; no comparison ran,
no budget reset and no additional checkout was created.


### 2026-10-23 — Publication source accepted; cloud-only delivery

The private native/classical compose-and-propose source is accepted at cfaab7f222f5b004b42fc08109c998b7826ec85f (tree c89318ab13338bf46629cee49f70ad16d44205b6). It binds actual retained Journal/native/classical materials to additive publication evidence, preserves the primary result when diagnostics fail, and proves original-prefix replay without rerunning numerical work. It returns a pure proposal; durable writes and actual process measurements remain pending.

Quality recovered complete sealed author results:4,003 tests,1,512 schema cases, Ruff/format172, strict mypy122, configured security/dependency checks, exact68-file archives and installed-callable smoke passed. Platform accepted173 authored plus30 independent checks and2 sensitive guard mutations; Research accepted45 authored plus35 independent checks and1 sensitive mutation. These counts overlap and are not added to the full-suite count. Lead rehashed36 author,20 Platform and14 Research evidence files; clean source/environment handoff is accepted. Author index60c08f98c6a239207aa9ef11aa48d01e012771cbbaf16ecb190e754b28d22540 and release indexdbb8346e9db8ce78f4211c950b48eaa7465a1ed80689d29b534f22181d0d70d3 identify retained private evidence. PR/main/candidate delivery remains the next gate.

Lead owns integration in the existing identity checkout and progress in primary. Platform owns final progress/delivery verification; Quality and Research prepare the next independently reviewable parent slice. All project execution, artifacts and evidence remain on studio-agent or hosted CI; the Mac is control only. Both parents105/106 stay in progress. Early no-score composition, real measurement, durable recovery, finite-grid inference, selection, calibration and the frozen comparison remain open. Finite-grid first, later Laplace audit and cumulative approved caps are unchanged. No actual comparison has run and no graph, effort, forecast or approval has changed.


### 2026-10-23 — Publication delivery accepted; complete early-stop work assigned

PR #115 is merged as4eea1ded28ca52d9f0d4efd09ad3c5cd86734dac with the exact reviewed tree1e93425913c4c0c0e43af59024625738dc60f89b. All four applicable PR checks and all five protected-main CI39917632001 jobs passed. Candidate12485382723 was downloaded and inspected entirely on studio-agent: four regular ZIP members, three checksums, source/run/lock/uv provenance, exact68-file wheel/sdist source allowlists and byte equality to reviewed author archives passed. Main evidence indexc18bada7fe54007218ba3c53cbb2a4d077c67c4e74b831c6c2467974e15a0c97 has13 independently rehashed private files. Requirements-export digest continuity was checked; its bytes were not independently recomputed.

Quality has the reused identity checkout on feat/native-early-stop-publication from accepted main4eea1de. The next coherent slice covers actual available purchase/candidate/selection/preparation/partial-prediction evidence and cannot hide an available score. Platform reviews accounting/replay/bounds; Research reviews scientific/material/outcome semantics; lead owns primary progress and integration. The existing pinned environment has68 source files matching installed bytes and5,671 singly-owned dependency files; no reinstall/new checkout was required. Handoff index56750d7d655bb312d65f81ded6e7a7fa7e5df4c6534e1d8812bde754eb904625 and Research plan0696c7e6a728dfc0d542eec7eef79f996a1fc6acef870bc8795d5fe36197a4fd identify this assignment.

After early-stop source closure, the next vertical adds actual measured execution, atomic private publication and crash recovery. Global accounting overhead remains charged without blocking every cell or pretending unknown tail costs are exact. After explicit parent source/delivery acceptance, finite-grid RA-N02.a can start without a dependency on the future actual study. Both parents remain in progress; no scientific comparison has run. Cloud-only execution, cumulative caps, later Laplace audit, graph, estimates and forecasts are unchanged.


### 2026-10-23 — Complete early-stop source accepted; delivery pending

The complete available-stage early-stop composer is accepted at001c8090a7e021263ea0718f9c686db1d9e2f8ea, treea3eaf665abf79cb7eb25e337625654a88b7bbbb8. It retains actual purchase/candidate/selection/preparation/prediction/classical material, failed and missing work, costs and original receipt replay without numerical reruns. Terminal scoring facts with missing score bytes require scored-path recovery; an earlier failure cannot conceal a possible report. Existing scored message/event bytes remain unchanged.

Independent review found that reservation order could conceal a selector completing after a rejected preparation. The bounded repair uses actual completion-update positions and five paired regression tests. Both reviewers accepted the repaired source: Platform31 and Research45 independent cases, plus3 sensitive guard mutations each. Original169/125 focused passes and the deliberately stopped superseded full run are retained as source-specific history, not claimed as repaired full-suite results.

Quality completed4,088 full tests,85 permanent early-stop cases, Ruff/format176, strict mypy125,1,522 external schema cases, configured security/hashed dependency checks, offline70-file archives and project-only installed-callable/replay/guard checks using the pinned dependencies. Lead rehashed88 author,21 Platform and20 Research evidence entries. Author index85eb6b88aecfdc0433a134bf9b4d61e547788850ea02c48e5cf1a78df4bb72af and release indexf821fa84b7a156645f605518edf026b755830b386dcd7b9f1f1fbe9552c321b6 identify the private records. The clean source and owned environment are explicitly released; no active consumers remain.

Lead owns both reused cloud checkouts for progress/integration. Platform verifies progress and PR/main/candidate delivery; Quality and Research prepare the already-reviewed actual measured/durable publication vertical. Both parents remain in progress. Actual measurement, atomic persistence/crash recovery, genuine inference/selection/calibration and the comparison remain separate gates. No scientific run, new budget, graph change or Mac project storage is introduced.


### 2026-10-23 — Early-stop delivery accepted; measured publication assigned

PR #116 is accepted as main2800188783217a65e35a66f5e17492c72f61af0d with reviewed tree1a0a2bb93f3c7b2423ba0882af891e12c5a389bc. All four applicable PR jobs and all five protected-main CI39959551652 jobs passed. Candidate12504965031 was acquired and verified on studio-agent: exact70-file source allowlists, four regular ZIP members, three checksums, source/run/lock/uv provenance and equality to accepted author wheel/sdist bytes passed. ZIP SHA256 e18149df7c7003b2c96feec4fab8545853b7ce05e75d246a067f859a644bbf09 and private acceptance index b93994aeda15106c98a449647d8aa8cb600d39ad84229232d76573e11e8f095d identify the retained delivery; lead rehashed all18 indexed files. Requirements-export digest continuity was checked against same-lock/uv evidence; its bytes were not independently recomputed. No accepted early-stop runtime cases were repeated for this reconciliation.

Quality owns the reused identity checkout on feat/measured-publication from acceptedmain2800188. The existing environment passed70-file installed/source equality,5,606 singly-owned site-file checks and pinned uv0.13.4/lock/pip checks without reinstall. Handoff index474aed266e01590877364b45a995c9a53cac78a645a01828ace7411a239d8a4f records the clean source and absence of active consumers. Lead owns primary progress; Platform reviews durability/concurrency/caps and Research reviews actual measurements, replay and scientific isolation. Both checkouts remain needed; no new checkout, environment or Mac project storage was created.

The next slice implements one measured atomic early/scored publication and recovery path. It must retain finite charged bootstrap/recovery/global tail capacity, actual parent/child CPU and artifact costs, original-snapshot receipt replay, and real SQLite Journal writer exclusion through publication commit. It does not measure prior numerical executions. After publisher acceptance, audit and complete fixed-operation durable reservations and OS measurements for existing candidate/preparation/prediction/scoring/classical and purchased-simulation work before closing105/106 or admitting finite-grid RA-N02.a. Future inference/calibration/selection and the actual study are not prerequisites for that parent audit. Both parents stay in progress; no comparison has run, and cumulative caps, later Laplace audit, graph, effort, forecast and approvals are unchanged.

### 2026-10-24 — PR117 CPU-clock test repair; delivery pending

PR #117 exposed a strictly-positive CPU test assumption in both Python jobs. The accepted test-only repair af694e5 preserves production source 423ea566; required PR/main/candidate delivery remains pending. See the [source-specific checks and failure evidence](EXECUTION_LOG.md#2026-10-24--pr117-cpu-clock-test-repair-delivery-pending).

RA-02/#105 and RA-N01/#106 remain open. The accepted parent audit recommends measured wrappers for the five existing native stages plus purchased simulation, with pre-freeze accounting and feasible cumulative control allowances. No study, cap, graph, approval or estimate change is introduced.

### 2026-10-24 — Measured publisher delivery accepted; execution design reviewed

PR #117 measured publication is delivered as main fb537d34: both Python PR jobs passed 4,146 tests, all five main CI jobs passed, and candidate 12541505445 was independently verified. The six-boundary measured-execution design remains proposed; the lead accepted its review conditions for a candidate-only next slice, while the allocation profile remains unfrozen and later purchase/handoff remain unimplemented. Both parent tasks stay open; no numerical implementation or comparison has started. See the [single detailed delivery/design record](EXECUTION_LOG.md#2026-10-24--measured-publisher-delivery-accepted-execution-design-reviewed). Approved scope, caps, graph, estimates and forecasts are unchanged.

### 2026-10-24 — Candidate-only measured execution delivered

Candidate-only pre-freeze execution is delivered through PR #118/main 9818ca0: both Python runtimes passed 4,213 tests in PR and main CI, all five main jobs passed, and candidate 12556446152 was independently accepted. Earlier source-specific checks and delivery failures remain preserved. Comparison dispatch, the other four numerical wrappers, purchased simulation, handoff and full-study allocation remain open. See the [delivery, repair and scope record](EXECUTION_LOG.md#2026-10-24--candidate-only-measured-execution-delivered). RA-02/#105 and RA-N01/#106 remain in progress; no study, cap, graph, approval, effort or forecast change.

## 2026-10-24 — Native stages independently reviewed; trust-store repair delivered

Measured preparation/prediction/scoring is delivered in [PR #120](https://github.com/spei04/strange-physics/pull/120), main ff3d47e. All five protected-main jobs passed, with 4,240 tests on each Python 3.12/3.14 runtime; candidate12561739881 matched all 80 package files and both reviewed archives. The bounded synthetic fixture remains conformance evidence. The next freeze/Journal/classical design passed independent review, but its runtime admission is unproved. Quality now implements charged freeze/Journal binding; Platform independently reviews boundaries, Research reviews scientific semantics, and Lead owns assignment and delivery. GitHub alert1 was automatically marked fixed at 20:54:23 UTC on 2026-10-24; no dismissal or audit suppression occurred. Parent issues105/106 and full-study admission remain open. See the [current assignment board](EXECUTION_LOG.md#current-assignment-board) and [source-specific evidence](EXECUTION_LOG.md#2026-10-24--measured-native-stages-delivered).

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

Source 730cc86 passed both scoped runtime reviews; final author checks and PR/main/candidate delivery remain pending. Public purchase integration and the conditional V3 16-call specimen have not run. Parent issues #105/#106, publisher handoff, full-study capacity and the first-result re-estimate remain open. [Evidence and current assignments](EXECUTION_LOG.md#2026-10-25--bounded-journal-source-accepted-final-checks-pending).

## 2026-10-25 — Bounded Journal final author acceptance

Final source 8c85fef preserves reviewed runtime 730cc86; all 14 configured checks passed, including 4,314 tests. PR/main/candidate delivery is pending. Quality is queued for public purchase integration after delivery; the V3 specimen, publisher handoff, full-study capacity and parent issues #105/#106 remain open. [Evidence and assignments](EXECUTION_LOG.md#2026-10-25--bounded-journal-final-checks-accepted-delivery-pending).

## 2026-10-25 — Bounded Journal prerequisite delivered

PR #123/main c784f15 and exact 84-file candidate 12589122154 are accepted; all five main jobs passed. Quality is queued for public purchase integration after explicit handoff. The conditional V3 specimen, publisher handoff, full-study capacity and parent issues #105/#106 remain open. [Delivery evidence and assignments](EXECUTION_LOG.md#2026-10-25--bounded-journal-pr-123-delivered).

## 2026-10-25 — Measured purchase handoff prepared

Quality's PR2 purchase/recovery handoff is prepared from pinned GitHub source, with independent Platform and Research review. Cloud execution awaits restored access and verified checkout ownership, disk and retained evidence. Purchase implementation, V3 and the study remain unstarted; parents and caps are unchanged. See the [implementation handoff](MEASURED_PURCHASE_HANDOFF.md) and [assignment log](EXECUTION_LOG.md#current-assignment-board).

## 2026-10-26 — Measured purchase implementation assigned

Verified cloud access and clean, unused checkouts allow the existing identity checkout to pass to Quality at accepted main c784f15. Platform and Research independently review the first immutable source checkpoint. The initial real-purchase/receipt/recovery gate remains distinct from full 12-slot mixed-history and downstream acceptance; V3 remains conditional. The study, caps, parent issues and later Laplace sequencing are unchanged. [Assignments and evidence](EXECUTION_LOG.md#2026-10-26--measured-purchase-implementation-assigned).

## 2026-10-26 — Pure purchase contracts accepted

Pure contracts/binder 3df6dc3 is accepted and published on the source branch; actual purchase execution and recovery remain in implementation, with no PR/merge or runtime acceptance. The first purchase checkpoint is separate from full mixed-history/downstream proof. V3, caps and parent status remain unchanged. [Evidence and assignments](EXECUTION_LOG.md#2026-10-26--pure-purchase-contracts-accepted).
