# Strange Physics — enterprise product blueprint and living roadmap

**Current checkpoint:** format5 passed, but the freeze control incorrectly rejected an allowed formatting-only change. Independent diagnosis is complete; a bounded correction amendment is being prepared before collection or tests. [Next owners and action](EXECUTION_LOG.md#current-assignment-board) · [Current evidence](research/D1_RUNTIME_REPAIR_RESULT.md).

Approved scope and budgets: [research approvals](research/APPROVALS.md). Operating rules: [cloud execution and capacity](EXECUTION_LOG.md#approval-and-execution-capacity).

**Document owner:** product owner and engineering lead
**Last verified:** 2026-10-31
**Repository:** [spei04/strange-physics](https://github.com/spei04/strange-physics)
**Execution:** [Current assignment board](EXECUTION_LOG.md#current-assignment-board); detailed checkpoints below are historical.

This is the maintained enterprise roadmap, requirements register and strategic progress record. The requested blueprint remains consolidated here. The later execution-planning request adds [EXECUTION_BACKLOG.md](EXECUTION_BACKLOG.md) for assignable PR tasks and [execution-backlog.json](execution-backlog.json) for their matching dependency/capacity ledger. Existing [accepted decisions](DESIGN_DECISIONS.md), [core contracts](CORE.md), [law definitions](LAWS.md), and [draft benchmark](BENCHMARK.md) remain useful detailed references. This document proposes an expanded release schedule; it does not retroactively approve new scope, change scientific settings, or claim deployed controls. Its approved R0–R8 scope supersedes the older M0–M5 plan; section 10 maps the two. The nine-person schedule remains a conditional reference, not a promise for the current lead plus three-engineer subagent execution mode.

No broad implementation, new infrastructure, paid sweep, or compliance certification is performed by creating this plan. Previously approved architecture remains accepted. New enterprise gates and quantitative assumptions below are proposals until approved or measured.

**Navigate:** [Progress](#0-progress-evidence-and-how-to-maintain-this-file) · [Product](#1-product-definition-and-planning-assumptions) · [Architecture](#4-architecture-and-trust-boundaries) · [Capacity and cost](#7-capacity-performance-and-cost-model) · [Security](#8-security-requirements-and-threat-model) · [Milestones](#10-dependency-aware-milestones-and-exit-gates) · [Backlog](#11-prioritized-engineering-backlog) · [Team and schedule](#12-team-ownership-and-delivery-schedule) · [Operations](#13-cicd-deployment-reliability-and-operations) · [Approval](#17-decisionprogress-log-and-approval-handoff)

## Research methods amendment (2026-10-19 cutoff)

The [dated method decision record](research/2026-10-19-METHOD_DECISIONS.md) retains18 broader research tasks and the [native comparison plan](research/NATIVE_COMPARISON_PROPOSAL.md) adds five scoped tasks. The owner approved eight enumerated native-path units on2026-10-21, including RA-01/02/07.b; other research tasks retain their authorization limits. Source/license, shared-model selection, calibration and complete accounting remain required. Provider, sizing, official-study and release gates remain separate.

The first new result is a local fixed-pool linear-model comparison after its scientific prerequisites:36 development episodes,432 purchased slots maximum,8 CPU-core-hours,1GiB new artifacts and zero provider calls. It does not wait for hosted deployment or all paper-inspired profiles. The optional later feasibility pilot has at most162 episodes; replicated-world sizing requires a separate approval and evidence before confirmatory freeze.

The retained23-task research ledger totals61–99 human engineering days plus25% reserve (76.25–123.75 days); this arithmetic envelope includes unapproved broader work. The approved first-result path is17–26 days (21.25–32.5 reserved), followed by later Laplace3–5 (3.75–6.25 reserved). The approved168-task/369-edge/ten-gate baseline and conditional W52–67 GA reference are unchanged. These estimates are not elapsed schedules or additional spending authorization.

## 0. Progress, evidence, and how to maintain this file

### 0.1 Status vocabulary

- **Verified:** implemented and checked, with a source identity and verification evidence. Scope must be explicit.
- **In progress:** actual work has started; name the owner and next verification.
- **Planned:** specified but not implemented.
- **Blocked:** a named dependency prevents the next task.
- **Deferred:** intentionally outside the current release.
- **Awaiting approval:** a proposal is ready for a product or architecture decision.

A checked box means its stated scope passed, not that the whole product is production ready. Do not use an overall completion percentage: a local simulator and an enterprise isolation boundary are not interchangeable units of progress.

### 0.2 Current progress ledger

- See the [three-point current assignment board](EXECUTION_LOG.md#current-assignment-board). The [archived ledger](EXECUTION_LOG.md#2026-10-28--progress-view-consolidation) preserves prior task acceptance and limitations.

### 0.3 Update procedure for every implementation change

1. Select a backlog ID and record its owner, branch/PR, start date and status here.
2. Confirm entry criteria and add the acceptance tests before calling the task complete.
3. In the same PR, update the requirement row, milestone checklist and progress ledger with the exact implementation commit, test command/run, date and remaining limitations.
4. Record failed checks and changed assumptions. Never convert a failed or skipped check into a completion.
5. At integration, record merge/release identity and reopen downstream work if a contract changed.
6. At each milestone exit, review capacity, security, scientific validity, costs and this schedule; update the risk register.
7. Archive required evidence privately outside disposable checkouts, with source identity, owner, purpose and retention. Link only sanitized evidence in this public file.

Progress is updated during project work and at reviews; this document does not imply an unattended monitoring service. Keep a short dated change log in section 17.


### 0.4 Staged delivery workflow

The staged workflow and execution backlog were approved on 2026-10-19. Begin the initial scope after its prerequisites; paid infrastructure, provider trials, official sweeps and releases retain their separate gates.

| Stage | Deliverable and gate | Current state |
| --- | --- | --- |
| 1 — Plan and challenge | Inspect actual code, compare options, expose assumptions, challenge risks; product owner reviews assumptions before implementation approval | Blueprint and challenge review accepted; unmeasured targets and external commitments remain provisional |
| 2 — Turn the plan into engineering work | Assignable PR tasks, exact dependencies/contracts/tests, capacity model and exit gates | 168 leaf tasks/42 epics; 369 prerequisites checked in both schedule scenarios; first ten days planned; execution approval recorded; subset freezes remain pending |
| 3 — Implement one vertical slice at a time | Start only an approved slice; require tests, review, telemetry and updated documentation; then assess its evidence before selecting the next | In progress: bounded spring I1 and SP-01.a/b/c/d are accepted; RA-01 accepted; RA-02 accounting integrated; RA-N01 candidate production/prediction independently reviewed; both parents in progress; VAL1 generator deferred |
| 4 — Validate actual production readiness | Audit shipped implementation against REQ01–REQ16 using real test/load/security/deploy/restore evidence; block unsupported claims | Not started; R6–R8 own these gates |

The roadmap owns product/architecture/overall progress; EXECUTION_BACKLOG.md owns assignable task details and schedules, backed by execution-backlog.json. GitHub issues hold epic rollups; The local SCI subset, full control/identity contract set and ART/EXEC/COMP1 contracts are accepted through SP-01.a/b/c. WORLD1 and WEB1 are integrated; the SP-01.d freeze is accepted. Creating an issue, schema or milestone never marks its implementation complete. Issue blockers describe completion/integration prerequisites; mock work may start after its explicitly approved interface boundary.

### 0.5 Proposed first implementation slice: fit, predict, score one spring system

**Approval item:** [SP-00](https://github.com/spei04/strange-physics/issues/2), execution decision D01. **Delivery units:** SP-03.a/b → SP-04.a/b → SP-06.a → SP-04.e, behind approved contracts and headroom. See the [leaf records](EXECUTION_BACKLOG.md#epic-sp-04). Effort is included in those packages; estimated integration W11 base/W13 reserve, not an added milestone.

A researcher exports purchased observations, fits a shared linear-spring coefficient, saves a typed model, predicts an unseen initial condition and receives an independently computed development report. This exercises the scientific architecture through a usable SDK/CLI path before adding more methods or hosted components.

1. Read existing validated observation exports; pass only public structure and purchased trajectories into the fitter.
2. Fit the noiseless one-particle/fixed-anchor linear-spring fixture using integrated velocity increments; preserve masses and declared units.
3. Save the versioned SCI model artifact with observation/config hashes and training prefix; implement prediction from the accepted local request/response contract.
4. Evaluate independent development probes in a separate evaluator component; emit the typed report with valid/failed counts and a declared normalizer/failure policy.
5. Add SDK/CLI entrypoints and exact reproduction instructions; record fit/predict/evaluate duration, numerical diagnostics and failure classes.
6. Review tests and artifact provenance, update this ledger and the linked issues, and approve the next increment only after inspecting the result.

**Initial acceptance targets to ratify on analytic fixtures:** for a noiseless spring with coefficient 1 and mass 1, relative coefficient error ≤1% and held-out position RMSE ≤0.001 over the existing two-second interval. Use an independent analytic solution as the reference. Confirm targets during SP-03; changing them requires a documented numerical justification rather than weakening a failed test.

**Failure cases:** zero-excitation/rank-deficient data; failed observations; mismatched particle ordering/masses; incompatible model/schema/runtime; nonfinite or divergent predictions; mismatched hashes; missing evaluation output. State failure explicitly and retain counts. Ensure the fitter never receives WorldDefinition, true coefficients, change markers or held-out labels.

**Review gate:** scientific correctness, truthful local-execution limitations, runnable reproduction, positive/negative tests, code review, telemetry and documentation. The slice does not establish hosted isolation, noisy-ensemble calibration, an official benchmark or enterprise readiness.

## 1. Product definition and planning assumptions

### 1.1 Vision and business objective

Strange Physics is a research infrastructure product for testing how agents discover unfamiliar physical rules and recover when those rules change. A team brings an agent, defines a controlled world, spends a fixed experiment budget, submits predictive models and receives reproducible measurements of generalization and adaptation.

The commercial value is reducing the engineering and validity burden of building discovery evaluations: private collaborative studies, reliable execution of submitted code, inspectable failures, controlled comparisons, and independent deployment. A compelling animation supports diagnosis; scientific and operational correctness establish the product's value.

### 1.2 Confirmed context

- Research first, with production SDK, CLI, hosted API, browser investigations/replays and self-hosting.
- Public open-source repository under the personal GitHub account; private customer studies by default.
- Hosted uploaded-code access initially restricted to approved organizations.
- Google Cloud using the existing eligible credit-bearing account; keep billing identifiers and account details out of public artifacts.
- Three initial law families; 2D with up to eight interacting particles; numerical observations; no training GPU initially.
- Default scored budget 40 including four shared calibration experiments; law changes occur between experiments.
- Both a controlled experiment-selection track and a complete agent-discovery track.
- User selected **7–10 engineers** for planning on 2026-10-19.
- Budget should not drive a toy architecture. Limits, metering, forecast review and credit verification remain required.

### 1.3 Provisional assumptions and decisions to validate

| ID | Assumption / unknown | Planning treatment | Owner / decision deadline |
| --- | --- | --- | --- |
| A01 | Actual named staff and availability are unknown | Reference plan uses nine engineers at 70% delivery capacity, plus fractional product/design/security | Product + lead, R0 |
| A02 | No launch date or signed customer SLA supplied | Relative weeks from approval and staffing; pilot onboarding W38–50, enterprise GA W52–67; not a commitment | Product, R0 |
| A03 | Initial customers are frontier-lab research groups and AI startups | Recruit three design partners, including one external custom-agent integration | Product, before R6 exit |
| A04 | 100 concurrent investigations is accepted; tenants/RPS/storage unknown | Separate baseline, forecast and stress assumptions in section 7 | Platform + product, R0 then R6 |
| A05 | Exact region, credits, permissions, quotas and expiry not established | One US primary region; us-central1 is a candidate only; verify before provisioning | Platform, R0 |
| A06 | No regulated sensitive datasets are needed for synthetic physics | Treat prompts, packages, credentials, identity and research IP as confidential; exclude health/payment data workloads initially | Security + product, before pilot |
| A07 | Enterprise buyers may require SSO, provisioning, audit export and contractual support | Include SSO and deprovisioning in GA; SCIM and audit export tested before claiming them | Product + security, R0 validation |
| A08 | Customer usage duration, ensemble size and package sizes unknown | Numerical workload and cost assumptions are explicitly provisional; benchmark before capacity claims | Research + platform, R1/R6 |
| A09 | Standard GCP managed services satisfy procurement needs | Validate residency, subprocessors, deletion and support requirements with partners; dedicated deployment is an option | Product + security, before pilot |

These unknowns do not block writing the plan. Staffing appointments, cloud access, named pilot customers, data terms and numerical protocol freeze do block their respective release gates.

### 1.4 Personas and journeys

| Persona | Journey | Outcome and measurement |
| --- | --- | --- |
| Research engineer | Install SDK → run local fixture → package agent → run private study remotely → inspect failures | First valid custom-agent run within one working day using published docs, without core changes |
| Research lead | Select versioned suite → choose matched strategies → review curves, failures and cost → export reproducible report | Every scored row traceable to frozen configuration and artifacts; no hidden feedback |
| Platform/security administrator | Create workspace → invite members/SSO → set quotas and model credentials → audit, revoke and delete | All access changes enforced and audited; deletion and recovery behavior demonstrated |
| Evaluator / benchmark maintainer | Calibrate on development worlds → freeze protocol → run public and blind suites → publish all scored outcomes | Sealed evaluation data never reaches an active agent; exclusions and failures retained |
| Visitor / collaborator | Build a supported world → watch budgeted investigation → replay actual vs predicted motion | Accurate, accessible visualization without implementing physics in the browser |

Anonymous visitors can inspect intentionally public releases. Anonymous arbitrary-code execution is outside the initial hosted scope.

### 1.5 Release scope

**Production MVP / design-partner pilot (R0–R7):** both tracks, three selectors in the controlled track, hosted durable runs, package/predictor isolation, private workspaces, quotas, cost records, world builder and replay, export, supported self-hosting, backups, observability and tested recovery. A limited pilot is still a real service; it has explicit access and support limits.

**Enterprise GA (R8):** demonstrated 100-concurrent-investigation envelope, customer SSO and revocation, service identities, audit export, retention/deletion verification, security review, disaster-recovery evidence, upgrade/rollback process, staffed incident response, measured SLOs and external integration evidence.

**Post-GA:** more law families, gradual drift/multiple changes, calibrated larger systems, richer agent languages, dedicated customer deployments, higher capacity and regional options when demand justifies them. Pixel observations and reinforcement learning become separately versioned research tracks.

**Out of scope for the initial releases:** arbitrary real-world scientific claims, a universal physics engine, collisions/3D/continuous interventions, model training infrastructure, unrestricted agent browsing, a public package marketplace, active-active multi-region writes, a billing/payment platform, and regulated-data certification. No claim that an LLM must outperform classical methods.

### 1.6 Product success criteria

Proposed pilot success, to confirm with partners: three participating organizations; at least two run an independent study repeatedly over four weeks; one implements an agent and a law extension without core modification; at least 80% of observed first-run onboarding sessions complete within one working day. With small samples, publish numerator and denominator.

GA success: all security/scientific/operational gates pass, 100-investigation workload passes the specified test, 30 days of measured SLOs, and one customer completes a self-hosted install/upgrade using the documentation. Revenue, pricing and conversion targets require customer discovery; they are not invented here.

### 1.7 Competitive and technical constraints

[DiscoveryWorld](https://github.com/allenai/discoveryworld) already provides an interactive scientific-discovery environment. [DiscoverPhysics](https://arxiv.org/abs/2605.26087) is closely related to unfamiliar simulated physics and includes time-varying interactions. These are reasons to avoid a first-of-its-kind claim. The proposed differentiation is controlled adaptation measurement combined with extensible, private, recoverable research operations and inspectable replay; its value must be validated with users. See the [existing related-work review](RELATED_WORK.md) for additional leads; implementation status is governed by section 0 here.

Numerical observations limit the initial claim to structured-data discovery. A disclosed feature library constrains the controlled track's hypothesis space. Extrapolation to held-out initial conditions does not establish transfer to arbitrary law families or real physics. No upstream code/assets are assumed copied; evaluate licenses and provenance before reusing dependencies, datasets or examples.

## 2. Requirements, user stories, and traceability

All new items below are must-have for their stated gate unless marked optional. IDs are stable and map to backlog items in section 11. “Local verified” does not include hosted behavior.

| ID | Need / user story | Acceptance criterion | Component; task; accountable role | Gate / current status |
| --- | --- | --- | --- | --- |
| REQ01 | Researcher defines unfamiliar reproducible worlds | Three families and legal interventions; runtime/config hashes; analytic and convergence checks; custom law without core edit | Core; SP-01/03; research | R1; local verified, freeze pending |
| REQ02 | Researcher compares selection strategies fairly | Random, active and LLM use identical candidate set, purchased data, fitter/adaptation policy and budget; costs reported separately | Fitter/selector; SP-04/05/18; research | R4; planned |
| REQ03 | Lead measures adaptation and generalization | Independent held-out banks; in/out-range and change strata; failure/censoring rules; world-level uncertainty intervals | Evaluator; SP-06/07/21; research | R6; planned |
| REQ04 | External team supplies agent and executable predictor | Pinned package → isolated build → digest-pinned execution; finite shape-checked predictions; no evaluation feedback | Execution; SP-14/15/19/20; platform | R4; planned |
| REQ05 | Investigator resumes or cancels safely | One logical reservation/result per key; stale worker rejected; committed checkpoints restored; cancellation bounded | Coordinator; SP-09/10/16; backend | R3; local verified, hosted planned |
| REQ06 | Admin protects private studies | Explicit membership; deny-by-default endpoint/object/SSE access; no domain auto-join; approved hosted-code organizations | Auth/storage; SP-08/11/31; backend | R2 then R6; planned |
| REQ07 | Admin bounds spend and resource use | Atomic experiment/resource reservations, run/workspace quotas, provider-attempt ledger, automatic stopping | Quota/gateway; SP-12/17/18; backend | R4; local experiment budget only |
| REQ08 | Researcher watches and diagnoses runs | Live committed-event timeline; resumable SSE; actual/predicted/uncertainty display; no hidden truth before finish | Web; SP-22/23/24; frontend | R5; planned |
| REQ09 | Researcher invents a world | Validated builder for supported primitives/ranges; versioned save; author-preview and agent-view separated | Web/core; SP-22/24; frontend | R5; planned |
| REQ10 | Team replays and independently deploys | Complete hash-checked manifest; offline replay without provider call; install/upgrade/restore supported stack | Export/self-host; SP-13/25/26/36; platform | R7; local export only |
| REQ11 | Operator sustains production load | Pass section 7 workload envelope with fair admission, bounded queue and no state corruption | All; SP-28/30/39; platform | R8; unmeasured |
| REQ12 | Customer can recover after outages | Restore database/artifact pair, reconcile epochs, enforce tombstones and meet section 13 RPO/RTO tests | Operations; SP-29/38; platform | R6/R8; planned |
| REQ13 | Security team can audit and remove access/data | Credential rotation, audit export, active-object deletion target, backup-expiry policy and revocation tests | IAM/data; SP-31/34/35/37; security | R8; planned |
| REQ14 | Enterprise uses its identity lifecycle | SSO, explicit linking, service accounts, SCIM disable/revoke; sole-owner and lockout protection tested | Identity; SP-34/35; backend | R8; proposed |
| REQ15 | Operator can deploy and support safely | Keyless CI, scanned signed artifacts, staged rollout, rollback, on-call exercise and 30-day SLO observation | Delivery; SP-02/27/32/40/41; platform | R8; core CI only |
| REQ16 | Benchmark is trustworthy and publishable | Freeze before scoring, keep public/blind separate, include all scored failures, embargo changes, sanitize publication | Research/publication; SP-07/21/33; research | R7; draft protocol only |

Quality attributes: correctness and privacy outrank animation smoothness or throughput. Reject overload visibly rather than discard accepted experiments. Support current and previous minor SDK protocol versions after GA; publish a minimum 90-day deprecation window for compatible hosted clients. Incompatible research protocol changes require a new benchmark version, even if the software API remains compatible.

## 3. Scientific design and validity gates

The numerical world uses dimensionless quantities. Initial scope is a visible graph of up to eight mobile particles and fixed anchors with hidden spring, softened radial, or velocity-dependent law terms. World authors may know their own parameters; an agent must only receive its public experiment space and purchased observations. Hosted official blind worlds have no author bypass.

### 3.1 Controlled experiment-selection track

- Four identical calibration experiments within the total 40-experiment budget.
- Random, classical disagreement-driven and LLM selection choose from the same seeded 128-candidate intervention bank per round.
- All use the same disclosed feature dictionary, integrated-increment sparse fitter, bootstrap ensemble, fitting budget and adaptation policy.
- Bootstrap complete experiments, not individual correlated frames.
- Diagnose rank/conditioning and insufficient data explicitly; ensemble disagreement is not automatically calibrated uncertainty.
- Compare all-history, fixed-window and detector-reset adaptation in separate predeclared ablations. Oracle reset is a labeled diagnostic only.
- Shared information and a fixed numerical-to-context transform are versioned. Record truncation/fallback; do not quietly give the LLM privileged summaries.
- Each accepted experiment consumes one slot, including a recorded numerical failure. Bound invalid proposals to two retries, then apply a disclosed valid fallback. Model retries count against compute limits.

### 3.2 Complete agent-discovery track

The agent chooses experiments and model classes and submits an immutable executable predictor after defined rounds. It uses the same physics budget but has separately specified CPU, memory, token, wall-time and output limits. Its results are never pooled with the shared-fitter comparison.

A predictor implements a versioned request/response protocol for a public experiment and timestamps. It returns finite position/velocity arrays and, optionally, declared interval levels. It receives no hidden labels, ground-truth trajectory, world seed, active coefficients or evaluator credential. The evaluator validates shapes, limits and determinism declarations before scoring. No Python pickle is loaded in trusted services.

### 3.3 Freeze and scoring

The [existing benchmark draft](BENCHMARK.md) supplies starting values, not finished results: one hidden change after 16–24 experiments; stationary, coefficient-change and term-change strata; 64 probes per regime split 32 in-range and 32 extrapolation. R1 must validate numerical stability, identifiability and runtime before freezing these settings.

Primary outcomes: normalized trajectory-position error across the full budget, and over the common 16-step post-change window; report interpolation and extrapolation separately. Secondary: recovery fraction, right-censored recovery latency, false alarms, interval coverage/width, raw position and velocity error, failures, latency and cost. Aggregate policy seeds within each independent world before paired world-level bootstrap intervals.

Before scoring, freeze an explicit penalty for invalid/missing/divergent predictions, using development-only scale calibration. Report failure rates alongside penalized scores and successful-only diagnostics; never remove failed worlds from the primary denominator. Verify any clipping/saturation cannot make a deliberately crashing predictor preferable. Require sensitivity analysis of the penalty. Solver failure distributions and exclusions are part of the released protocol.

A draft full sweep is 30 worlds × 3 families × 3 conditions × 3 policy seeds × 3 selectors = 2,430 episodes. It includes 810 LLM episodes and at least 29,160 adaptive-selection calls. This is a sizing example, not an approved paid run or a justified statistical sample size. Choose final size from development effect-size/variance/cost measurements and predeclare confidence-interval precision.

### 3.4 Evaluation isolation and economics

At 40 snapshots × 64 probes, there are 2,560 predictor rollouts per episode, before bootstrap members. At 200 integration steps each, that is 512,000 model integration steps versus 8,000 observed-world steps. Evaluating 20 ensemble members at every snapshot increases the predictor workload to 10.24 million integration steps per episode. Measure this before selecting ensemble size or worker capacity.

Prediction evaluators run separately from interactive experiments, with their own quota and completion state. A run is not “scored” until required evaluation tasks complete. Scores remain inaccessible to active agents, including through indirect event names, UI fields, error messages and artifact paths. Public suites can be inspected; they must never be advertised as secret. Blind-suite submission quotas and release cadence limit adaptive overfitting. Only designated evaluators can access blind artifacts; published reference results and private customer results follow different release policies.

## 4. Architecture and trust boundaries

### 4.1 System context

Start with one modular Python control-plane codebase, deployed as a few services only where identity, lifecycle or resource isolation requires it. No general microservice mesh, Kafka cluster, vector database or distributed training infrastructure is needed.

~~~mermaid
flowchart LR
    U[Researcher: browser SDK CLI] --> I[Managed identity]
    U --> A[Cloud Run API and run broker]
    I --> A
    A --> D[(PostgreSQL control state)]
    A --> O[(Private object storage)]
    D --> Q[Transactional outbox dispatcher]
    Q --> T[Cloud Tasks]
    T --> C[Cloud Run coordinator]
    C --> D
    C --> W[Trusted simulator workers]
    C --> E[Trusted evaluation controller]
    C --> S[Untrusted agent sandbox]
    S --> B[Scoped run broker]
    B --> A
    B --> G[Isolated model gateway]
    G --> P[Approved model providers]
    G --> K[Secret Manager]
    E --> X[Networkless predictor sandbox]
    E --> H[(Restricted worlds and evaluation truth)]
    E --> O
    W --> H
    W --> O
    U --> V[Authorized replay and SSE]
    V --> A
    PKG[Uploaded package] --> BUILD[Isolated build environment]
    BUILD --> REG[Immutable image registry]
    REG --> S
    REG --> X
~~~

The arrows depict allowed functional flows, not unrestricted network access. The agent can reach only narrowly scoped broker endpoints; it cannot reach the full API, database, object buckets, metadata service or provider directly. Trusted controllers stage inputs and collect outputs across the sandbox boundary.

### 4.2 Component responsibilities

| Component | Owns | Boundary / scaling |
| --- | --- | --- |
| Core library | Numerical solver, validated schemas, law plugins and local adapter | No cloud dependency; trusted local code only |
| API / run broker | Authorization, run submission, scoped operations, artifact access and SSE | Stateless Cloud Run; bounded database pool |
| Coordinator / reconciler | Run transitions, reservations, worker leases, cancellation and retries | Durable state in PostgreSQL, not process memory or queue delivery |
| Simulator | Hidden law, deterministic experiment realization and public observation output | Trusted image; separate from submitted code |
| Fitter / selector services | Purchased-data fitting and controlled method implementations | Pinned numerical runtime; no evaluator reads |
| Evaluation controller | Sealed probes/truth, scoring, immutable result manifests | Separate identity and object access; no feedback to agents |
| Agent / predictor runtime | Uploaded code and declared state | Per-run sandbox; distinct agent and networkless predictor policies |
| Build tier | Untrusted installation/build hooks | Isolated from deploy CI and production credentials; output quarantined |
| Model gateway | Provider allowlist, secrets, context limits, usage and attempt records | Separate service identity and bounded outbound access |
| Web client | Builder, run timeline, diagnostics and replay | Uses API contracts; interpolates server frames |
| Artifact store | Immutable trajectories, models, manifests and exports | Database owns authorization and references; generation/hash verification |

Custom law plugins are also code. Local/self-hosted trusted extension remains supported. Hosted world-builder definitions use approved law implementations. A new hosted law package must pass isolated numerical and security review before promotion to the trusted simulator catalog; arbitrary law uploads never execute inside privileged simulator services.

### 4.3 Run lifecycle and consistency

~~~mermaid
stateDiagram-v2
    [*] --> queued
    queued --> preparing
    preparing --> running
    running --> recovering
    recovering --> running
    running --> evaluating
    evaluating --> completed
    queued --> cancelled
    preparing --> cancelling
    running --> cancelling
    recovering --> cancelling
    evaluating --> cancelling
    cancelling --> cancelled
    preparing --> failed
    running --> failed
    recovering --> failed
    evaluating --> failed
    queued --> expired
    preparing --> expired
    running --> expired
    recovering --> expired
    evaluating --> expired
~~~

Use revision-checked transitions, one active lease epoch per run, a deadline, and terminal-state immutability. Retry infrastructure faults within a bounded policy; never convert user-code failure into an unrecorded new experiment. Cancellation first revokes launch permission and broker access, then terminates workers and reconciles in-flight operations. Already accepted results remain visible; unused reserved compute is released only after reconciliation.

Reservation, experiment ordinal, budget debit and outbox entry commit atomically. Worker completion checks the current fencing epoch; database constraints enforce unique operation and ordinal. Store an artifact durably and verify its generation/hash before committing its reference. A crash may leave an orphan object, cleaned only after a grace period and reference scan; it must not leave a supposedly complete result pointing to a missing object.

Cloud Tasks is a wakeup mechanism, not the system of record. Duplicate or delayed delivery must be harmless; task order is not assumed. A periodic reconciler recovers missed dispatches and expired leases. Keep short dispatch handlers, bounded exponential retry with jitter, and an application-owned failed-dispatch table with attempt count, error class, replay action and audit trail; do not assume a native dead-letter queue handles the business workflow. These decisions account for documented [Cloud Tasks delivery behavior](https://docs.cloud.google.com/tasks/docs/common-pitfalls).

Strong consistency is required for memberships, quotas, experiment identity, checkpoint references and run transitions. Event/replay views may lag committed state; show a cursor and lag. Cache immutable content by hash; initially do not add Redis. Never use a stale membership cache to authorize revoked access. SSE polls committed events in bounded batches without holding a database connection per viewer; use resumable cursors and reauthorization.

### 4.4 Embedded architecture decision records

Each record states an accepted foundation or a new proposal. Cost allocations are planning envelopes from section 7, not vendor quotations.

| ADR | Decision / status | Why; alternatives; trade-off | Cost / limit / revisit trigger |
| --- | --- | --- | --- |
| ADR01 | Python + NumPy/Pydantic core, SciPy for fitting; accepted | Scientific tooling and current package; alternatives JAX/Rust later. CPU-first avoids GPU requirement; profiling may reveal hot loops | Engineering and CPU time; optimize numerical kernels only if they exceed 50% of measured compute |
| ADR02 | FastAPI modular control plane on Cloud Run; accepted | Typed HTTP contracts and independent trusted scaling. Alternatives full GKE or many microservices add operations | Shared control-plane envelope $300–1,200/month at target; DB connections and long streams constrain scale; split modules only on independent load/ownership evidence |
| ADR03 | PostgreSQL on regional HA Cloud SQL; accepted | Transactions for budgets/leases/tenancy. Firestore/SQLite do not fit the hosted relational invariants as directly | $500–2,000/month allowance; write/connection ceiling; tune then scale vertically before sharding |
| ADR04 | GCS immutable bulk objects plus DB metadata; accepted | Large histories/models do not belong in hot SQL rows; local filesystem unsuitable for replaceable workers | $100–1,000/month allowance; request/egress and retention growth; change tiers after access measurement |
| ADR05 | Outbox + Cloud Tasks + reconciler; accepted | Managed dispatch and application durability. Pub/Sub for fan-out or workflow engine only when real workflow complexity requires it | Included in control-plane envelope; dispatch/lease lag; revisit if >3 independent event consumers or sustained queue limits |
| ADR06 | Separate GKE Sandbox tier; accepted | Uploaded Python and predictor code need enforced kernel/network/resource boundaries. Plain containers insufficient for stated threat model; dedicated VMs are stronger-cost alternative | $1,500–5,000/month allowance at 100-run forecast, workload dependent; verify gVisor compatibility and quotas; dedicated pools/deployments for buyers requiring stronger separation |
| ADR07 | Managed OIDC; explicit app memberships; accepted | Avoid password implementation; Identity Platform Google/GitHub initially; generic OIDC for self-hosting | Identity/SSO within $100–600/month allowance; provider outage or enterprise federation gaps; validate enterprise flow before promising it |
| ADR08 | React/TypeScript/Vite + Canvas 2D + SSE; accepted | Eight-particle visualization needs no second simulator or WebGL framework. WebSockets unnecessary for committed event feed | Static delivery included in control plane; reconnect/large replay pressure; chunk/index replays before changing renderer |
| ADR09 | Gateway for model calls and isolated builds; accepted | Keep credentials away from arbitrary code; explicit usage/ambiguous-attempt handling. Direct agent internet rejected for first hosted release | Gateway in control plane; model costs separate; provider quotas dictate admission |
| ADR10 | Terraform + keyless GitHub Actions + immutable images; accepted | Reproducible environments and traceable releases; click-managed infrastructure creates drift | Build/storage/security/logging allowance $200–1,000/month; isolated customer builds never share deployment credentials |
| ADR11 | Single US serving region, cross-zone DB, tested backups; accepted | Meet initial operational scope without active-active writes; regional outage requires recovery elsewhere | DR premium and duplicate storage budgeted separately; stricter regional RTO/residency may justify replica/second serving region |
| ADR12 | Separate public, blind and customer suites; accepted | Prevent score leakage and misleading reproducibility claims; one public leaderboard is insufficient | Evaluator compute can dominate; schedule asynchronous scoring and freeze its workload |
| ADR13 | DB row policies plus API/object authorization; proposed | Defense against omitted tenant filters, while retaining explicit application checks. Separate DB per tenant reserved for dedicated customers | Added test/migration complexity; >100 tenants alone does not justify sharding |
| ADR14 | Stage isolated from dev and prod; enterprise identity lifecycle; proposed | Prevent test credentials/data and schema changes affecting customers; enterprise offboarding requires more than social login | Additional nonprod allowance; customer confirmation in R0 decides SSO/SCIM release scope |

GKE Sandbox adds an isolation layer; resource limits, explicit runtime selection and metadata/network controls are still necessary. Validate the exact runtime/version and fail closed if unavailable. See [GKE Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods). This is not a claim that a service selection alone makes customer code safe.

## 5. API, SDK, events, and interface freeze

Current public schemas are Experiment, ExperimentSpace, ExperimentRecord, ObservationBundle and Checkpoint in contracts.py. Preserve their semantics. Add versioned remote envelopes, complete manifests and predictor schemas; do not silently overload the observation export with hidden research metadata.

### 5.1 Proposed HTTP surface

All routes are under /v1. IDs are opaque and tenant-checked; a workspace path is never proof of authorization.

| Operation | Method / path | Result and authority |
| --- | --- | --- |
| Memberships / invitations | GET/POST /workspaces/{w}/members and /invitations | Owner-managed membership; invitation expiry, single use, audited acceptance |
| Versioned worlds and packages | POST /workspaces/{w}/worlds; POST /workspaces/{w}/packages | Validated definition or staged upload; digest and build operation ID |
| Create investigation | POST /workspaces/{w}/runs | 202 with run_id, state, operation_id, request digest and budget summary |
| Read / cancel run | GET /workspaces/{w}/runs/{r}; POST .../{r}/cancel | Current state or 202 cancellation accepted; cancellation not completion |
| Execute experiment | POST /runs/{r}/experiments | Run-scoped token; Idempotency-Key; 202 operation or existing committed result |
| Observe results | GET /runs/{r}/experiments; /runs/{r}/operations/{op}; /workspaces/{w}/runs/{r}/operations/{op} | Purchased observations only; cursor pagination |
| Save checkpoint | PUT /runs/{r}/checkpoints/{index} | Schema/runtime/hash validation; immutable at an index; complete prefix only |
| Submit predictor | POST /runs/{r}/models | Immutable image/model references; no evaluator score returned |
| Model request | POST /runs/{r}/model-calls | Scoped gateway operation ID and pending/completed/ambiguous state |
| Events / replay | GET /workspaces/{w}/runs/{r}/events and /replay | Authorized SSE cursor or bounded replay chunks |
| Export / publish / delete | POST .../{r}/exports, /publications; DELETE .../{r} | Explicit owner intent; async operation; sanitized publication manifest |
| Usage / audit | GET /workspaces/{w}/usage and /audit | Authorized summaries and cursor export; no raw credentials |

Use OpenAPI 3.1 with stable operation IDs, generated TS client and Python remote adapter. R0/SP-01 freezes specific request/response/error subsets and examples before their consumers; provider and executable-predictor freezes are SP-17.a and SP-19.a, with enterprise contracts reviewed before SP-34/35 consumers. Clients must tolerate declared optional fields and known versioning rules, not unknown experiment fields that the existing strict contracts reject.

Mutation idempotency keys are scoped to tenant + route + resource + caller operation. Identical canonical bodies return the original operation; changed bodies return 409. Keep run-operation deduplication records for the lifetime of the run, including partial failures. DELETE tombstones preserve the minimum deduplication identity required by the retention policy.

Errors use code, safe message, request_id, retryable and optional operation_id. Define 401 authentication, 403 permission, non-enumerating 404 object lookup, 409 conflict/incompatible state, 422 schema/range, 429 quota/admission with Retry-After, and 503 transient platform unavailability. Never expose hidden coefficients, stack locals, provider keys or evaluator paths.

### 5.2 Event and artifact contracts

Event envelope: schema_version, event_id, workspace_id, run_id, per-run sequence, type, occurred_at, operation_id, trace_id and typed payload. Unique (run_id, sequence); committed events only. Event timestamps are informational; sequence establishes order. Resume with Last-Event-ID; expired hot cursors receive an explicit resync instruction to retrieve the authoritative snapshot and archived history. No silent gaps.

Run manifest: code commit, immutable runtime digests, lock/config hashes, protocol version, public suite identity or restricted suite reference, intervention/noise identities under appropriate access, strategy/policy/model versions, purchased observations, checkpoints, model artifacts, provider attempts, evaluation outputs and failure records. Visibility classes are agent-visible, workspace-private, evaluator-only and explicitly public. Viewer ground truth is a separately authorized post-run artifact.

Checkpoint JSON remains bounded to 256 KiB; larger state is referenced by immutable artifact digest and size. A restore loads only a complete compatible checkpoint. Bulk deserialization of agent-specific state happens inside its sandbox. Local and hosted adapters must pass the same experiment/checkpoint semantic conformance suite; SQLite and PostgreSQL do not need identical internals.

Predictor request includes protocol version, public structure/experiment and requested timestamps; response includes matching particle order, position/velocity arrays, optional declared intervals and runtime metadata. Batch size, output byte limit, wall timeout and invalid-output scoring are frozen per benchmark. A user predictor cannot choose its own held-out probes.

### 5.3 Inter-team handoff

Publish fixtures for completed, failed, interrupted, cancelled, budget-exhausted and ambiguous-provider runs. Provide a mock HTTP server from the frozen schema and deterministic SSE recordings. Contract changes require backend + SDK + frontend review; changes affecting information access additionally require research and security review. The interface checkpoint blocks parallel code that depends on unsettled fields.


### 5.4 Initial machine-readable contract pack

| Artifact | Scope and status |
| --- | --- |
| [Core schema definitions](../contracts/core.schema.json) | Exported from the existing public Pydantic contracts at the implementation baseline: 15 named definitions. These describe current data formats, including runtime validation obligations. |
| [Draft HTTP API](../contracts/draft/openapi.json) | OpenAPI 3.1 subset with 11 proposed run lifecycle operations, role/token boundaries, errors, idempotency, checkpoints, model receipts and SSE. No endpoint is implemented by this file. |
| [Accepted local SCI messages](SCI_CONTRACT.md) | Exact fit input/prefix, first linear-spring model, predictions and failure-explicit development reports. Historical hosted drafts and ART remain unfrozen. |
| [Contract examples](../contracts/examples.json) | Synthetic positive, negative and runtime-only validation fixtures; they are not benchmark results. Validate instances against the named definition, not the schema-library root. |

Validation performed during Stage 2: JSON Schema 2020-12 definition checks; resolution of local/external references; official OpenAPI 3.1 structural meta-schema; unique operation IDs, required path parameters, mutation idempotency headers and nonempty security requirements; nine positive and three negative example validations, plus two documented runtime-only cases. Exported core definitions were compared with current Pydantic schemas, and the existing runtime rejected the missing-impulse-target fixture. The cloud machine's existing system jsonschema 4.10.3 package was used, without installing dependencies or adding a runtime dependency. [OpenAPI schema source](https://spec.openapis.org/oas/3.1/schema/2022-10-07), SHA-256 da01ba28852cac0de53893797cb8d1942bc3b05084f526dcc216717dec314ed0.

JSON Schema does not implement cross-field scientific or security behavior. Runtime obligations include graph identities, impulse targets, increasing/aligned timestamps, particle/mass matching, finite numerical results, checkpoint size/prefix/runtime consistency, quota transactions, tenant/epoch authorization and evaluation-count consistency. The fixture set explicitly identifies structural-validity cases that need semantic rejection.

### 5.5 Remaining contract-freeze gates

- [ ] Review the proposed first slice and ratify its supported numerical domain and test tolerances.
- [ ] Freeze foundational research/run/identity/artifact/world/event subsets in SP-01.a–d; provider SP-17.a and predictor SP-19.a separately; enterprise federation/SCIM in SP-34.a/35.a before consumers. Extension endpoints must update reviewed schemas before implementation.
- [ ] Resolve exact SSE cursor expiry, archive resync transport and authorization/session lifecycle.
- [ ] Freeze model/checkpoint compatibility and artifact/runtime identity semantics with research, backend and platform reviewers.
- [ ] Add positive/negative/ambiguous-failure fixtures for the full agreed subset and review privacy visibility.
- [ ] Introduce reproducible, pinned contract validation and generated-client drift checks in CI when freezing the interfaces.
- [ ] Sign off the versioned interface subset and produce client/mock artifacts before parallel consumers depend on it.

The current draft pack is review scaffolding. It does not complete a subset freeze, imply an API deployment, or waive execution-backlog approval and production gates.

## 6. Data model, ownership, and lifecycle

### 6.1 Proposed relational model

Use UUID identifiers, UTC timestamps, explicit schema versions, server-assigned tenant context and parameterized queries. All tenant-owned parent/child references include workspace_id; no globally addressable artifact is authorized by its hash alone.

| Entity | Core fields / constraints | Owner and indexes |
| --- | --- | --- |
| users / identities | user_id; unique (issuer, subject); status; verified linking records | Identity; never merge accounts solely by email |
| workspaces / memberships / invitations | workspace_id; member user_id/role/status; unique membership; invitation hash/expiry | Identity; membership lookup by workspace + user |
| service_principals | workspace_id; credential hash/reference, scopes, expiry, last_use, revoked_at | Identity; short-lived run tokens separate from customer API credentials |
| worlds / suites / versions | immutable definition reference/hash; visibility; protocol; restricted seed reference | Research; evaluator identity owns blind truth |
| packages / builds | source digest, lock hash, build state, image digest, scan/provenance references | Platform; workspace ownership and digest lookup |
| runs | workspace_id, status, revision, limits, deadlines, runtime/protocol, lease_epoch | Coordinator; (workspace_id, created_at, id), (status, lease_expiry) |
| experiments | run_id, ordinal, operation key, request hash, accepted_at, result reference, status | Coordinator; unique (run_id, ordinal) and (run_id, operation_key) |
| execution_attempts / leases | run_id, epoch, worker identity, heartbeat, deadline, termination reason | Coordinator; lease-expiry and attempt lookup |
| checkpoints / models | run_id, through_index, schema/runtime, artifact reference | Coordinator/research; immutable prefix and unique checkpoint index |
| artifacts | workspace_id, kind, visibility, digest, size, storage generation, retention/deletion state | Storage; scoped object lookup; no raw signed URLs in long-lived rows |
| model_calls / attempts | run_id, operation key, provider/model version, request digest, status, usage, ambiguity | Gateway; unique logical operation, separate attempted requests |
| quota_reservations / usage_entries | workspace/run, resource type, reserved/settled amount, attempt linkage | Metering; transaction-safe reservation and reconciliation |
| run_events / outbox | run_id + sequence unique; typed payload; dispatch attempts/next_due | Coordinator; per-run cursor and due-outbox indexes |
| evaluation_jobs / results | model snapshot, suite/version, immutable result hash, visibility | Evaluator only; unique model + evaluator version + probe bank |
| audit_events / deletion_jobs | actor, action, target, outcome, reason, time; tombstone scope and progress | Security/operations; tenant/time and unfinished deletion indexes |

Use PostgreSQL row-level policies as defense in depth for tenant tables. Application runtime roles must not own tables or have BYPASSRLS; migrations use a distinct identity. Set transaction-local tenant context after token verification and test pool reuse/reset. Explicit authorization remains necessary for actions, roles, object storage and the evaluator boundary.

Keep trajectories, prompts, binaries and large state in object storage. The DB stores metadata and references. No broad cascade deletion may race active runs: revoke/cancel first, then delete in resumable batches. Avoid cross-tenant deduplication that could reveal artifact existence or couple deletion lifecycles.

### 6.2 Lifecycle policy proposals

| Data class | Default / action | Verification and exception handling |
| --- | --- | --- |
| Customer runs, packages and model artifacts | Retain until owner deletion or configured retention; warn at storage quota, stop new writes safely rather than silently delete | Export completeness and owner-specified retention tests |
| Provider transcripts / research prompts | Private workspace research artifacts; minimize context; configurable capture/redaction; default governed by run retention | Never log full bodies centrally; provider retention terms separately reviewed |
| Hot run events | Proposed 90 days online; archive complete history for retained runs | Archived replay/cursor resync works; no loss of required provenance |
| Application diagnostics | Proposed 30 days searchable; redact bodies/secrets; shorter for sensitive transient data | Access review; review temporary diagnostic archives after 30 days |
| Customer audit history | Proposed one year, configurable contract scope; minimize personal fields | Append-only permissions and tamper-evident export; legal/privacy review before launch |
| Backups / recovery versions | Proposed 35-day backup lifecycle; operational PITR window selected explicitly and tested | Verify actual service support/configuration; old copies expire, not silently retained forever |
| Public scored releases | Durable versioned manifests and all scored outcomes, sanitized before explicit publication | Withdrawal/takedown policy; public copies cannot be promised fully retractable |
| Abandoned uploads/build scratch | Proposed 24-hour grace; delete only unreferenced, inactive objects | Active-consumer check and cleanup audit; no live checkpoint data collected |

Deletion target: revoke interactive access immediately after authorized delete acceptance, remove active objects within seven days, and expire recoverable backup copies within the disclosed backup window. Reapply deletion tombstones before exposing any restored environment. Handle approved legal holds separately and disclose exceptions; do not invent a legal-retention obligation. Backup retention and data-subject terms require review before contractual promises.

Encrypt transport and managed storage; separate IAM identities for simulator, evaluator, API, gateway, build and deployment. Customer-managed encryption keys and dedicated projects are demand-driven options, not silently included certifications.

## 7. Capacity, performance, and cost model

All numbers here are **planning assumptions or acceptance targets**, not measured customer demand or delivered capacity. The accepted goal is 100 simultaneous investigations; it means in-progress agent investigations, not 100 HTTP connections or 100 experiments per second.

### 7.1 Three workload envelopes

| Dimension | Pilot baseline | GA forecast / acceptance envelope | Stress characterization |
| --- | --- | --- | --- |
| Active tenants / registered users | 5 / 50 | 50 / 500 | 200 / 2,000 |
| Simultaneous investigations | 10 | 100 | 300 offered; admit bounded capacity, queue/reject remainder |
| Concurrent interactive viewers | 20 | 100 | 500 |
| External API traffic, reads/writes | 15/5 RPS | 80/20 RPS | 400/100 RPS |
| Approximate internal DB writes | 20/s | 200/s | 600/s; verify event/attempt amplification |
| Runs completed per day | 100 | 1,000 | 3,000 synthetic load, separate from paid model load |
| Physics experiments per day | 4,000 | 40,000 | 120,000 |
| Mean run wall time assumption | 20 minutes | 20 minutes | 20 minutes, plus slow/failing variants |
| Artifact envelope per run | 10–100 MiB | 10–100 MiB | p99 500 MiB; oversize rejected or explicitly reconfigured |
| New artifact volume/day | 1–10 GiB | 10–100 GiB | 30–300 GiB |
| Retained customer data | No automatic expiry | At forecast: about 0.3–3 TiB/month growth before replicas/backups | Test 10 million events + 1 million artifact metadata rows |
| Build concurrency | 1 | 5 | 20 offered; queue with per-tenant limits |
| Separate prediction evaluation concurrency | Measure in R1 | Size independently to keep daily scoring backlog <24 hours | Slow/malicious predictor mix and evaluator saturation |

These daily volumes do not mean every accepted slot is occupied 24 hours/day. At 100 runs × 20 minutes, fully occupied capacity is 7,200 runs/day; the 1,000/day forecast uses about 14% average occupancy with burst headroom. A representative 100-run burst produces roughly 3.33 physics experiments/second over 20 minutes, plus fitting, provider and evaluation work. Validate peak distributions rather than sizing only from daily means.

Eight particles × 41 observations × four float64 coordinates/velocities = 10,496 numeric bytes per experiment; 40 experiments are about 0.4 MiB before JSON, metadata, checkpoints, prompts and predictors. The 10–100 MiB allowance includes those larger artifacts. Measure compressed/uncompressed and evaluator growth separately.

### 7.2 Performance budgets and admission

- Authenticated metadata reads: p95 ≤300 ms, p99 ≤1 second; mutation acceptance p95 ≤500 ms, p99 ≤1.5 seconds, excluding internet client latency and asynchronous execution.
- Warm worker launch p95 ≤10 seconds; cold launch p95 ≤120 seconds. Queue wait measured separately; baseline p95 ≤30 seconds, forecast p95 ≤120 seconds under the declared workload.
- Committed event to authorized viewer: p95 ≤2 seconds. Replay interaction ≤100 ms on the defined reference device for a loaded run; aim for 60 fps, accept ≥30 fps for the eight-particle reference.
- Worker-loss recovery: p95 ≤5 minutes to resumed progress, excluding a known provider outage. Cancellation: revoke new work within 5 seconds; terminate cooperative/infrastructure-controlled execution within 60 seconds.
- Define physics/fitter/predictor CPU budgets after R1 measurements. Tentative worker defaults: 1 vCPU/2 GiB per agent, 2 vCPU/4 GiB for fitting, 1 vCPU/2 GiB per predictor; hard wall/output/process limits per package class.
- Pool connections: allocate <60% of measured DB connection capacity to normal service pools; reserve the rest for migrations, failover/recovery and headroom. No connection per SSE client. Limit instance × pool-size products explicitly.
- Fair scheduling: workspace concurrency cap and weighted round-robin admission; isolate build, interactive, reference sweep and evaluator pools. One tenant cannot occupy all slots.
- Admission reserves experiment, CPU/wall, token and artifact allowances independently. Return 429 for customer quota exhaustion and explicit queued/capacity status for global saturation. Pause new work if durable state cannot be committed.

### 7.3 AI workload model

Budget model requests separately from physics and CPU. For one controlled LLM episode, 36 adaptive choices at an illustrative 8,000 input + 1,000 output tokens per call imply 288,000 input and 36,000 output tokens. At 1,000 all-LLM runs/day, that is 36,000 calls, 288 million input and 36 million output tokens/day before retries. Actual history growth may exceed the illustration; cap context, record transforms and measure.

A burst of 100 investigations with 20-second mean provider latency could create roughly 60 concurrent provider calls if the 36 calls spread evenly across 20 minutes; synchronized rounds can spike higher. Gateways require per-provider/model/workspace request and token-rate limiters, admission queues, timeout/circuit-breaker policy and maximum retry cost.

Provider cost formula per day:
**calls × (input_tokens × input_price_per_million + output_tokens × output_price_per_million) / 1,000,000**, summed over attempts and models. Store provider-reported usage and distinguish billed, estimated and unknown amounts. Pin model/provider/version and timeout policy per scored suite. Do not silently switch models on error; a fallback is a separate declared method/configuration. Ambiguous timeouts may already have cost money: persist uncertainty, reconcile when possible, and require the configured retry policy to authorize another paid attempt.

### 7.4 Cost planning

The following are **engineering allowances**, not current Google quotations or spending authorization. Before provisioning, export a region/SKU/usage-specific estimate from the [Google Cloud calculator](https://cloud.google.com/products/calculator), confirm credit coverage/expiry, include taxes/support/network/backup retention and replace these ranges with a dated estimate.

| Budget category at forecast | Monthly allowance (USD) | Cost drivers |
| --- | --- | --- |
| Trusted control plane, dispatch and static delivery | 300–1,200 | CPU/memory time, instance minima, requests and network |
| Regional HA database | 500–2,000 | CPU/RAM, HA, disk, backup/PITR and connections |
| Sandboxed execution and evaluation | 1,500–5,000 | CPU/RAM duration, utilization, evaluator rollouts, warm capacity |
| Artifacts and data transfer | 100–1,000 initially | Retained bytes, copies, operations, downloads; grows without deletion |
| Identity, secrets and access components | 100–600 | Active users, federation/features and secret access |
| Build, registry, security and telemetry | 200–1,000 | Builds/images, scan usage, log/trace volume |
| Nonproduction and recovery overhead | 500–2,000 | Staging tests, backup copies and recovery drills |
| **Planning total excluding model calls and labor** | **3,200–12,800** | Range sum; no assumed credit discount |

A pilot allowance of $1,500–5,000/month excluding inference/labor is provisional and may overlap GA because secure isolation and HA have fixed costs. With 30,000 runs/month, forecast infrastructure allocation is approximately $0.11–0.43/run before provider usage; this is an allocation of the allowance, not a measured marginal cost or proposed price. An evenly divided allowance across 50 active tenants is $64–256 per tenant/month before inference and labor; real tenants need allocation by attributable workload, retention and shared overhead rather than equal billing. Report cost by tenant, run, physics experiment, provider attempt and evaluator rollout. Alert at 50/80/100% of approved budgets; enforce application quotas because billing alerts are not hard spending stops.

### 7.5 Load plan and evolution triggers

1. Measure a numerical workload matrix: 1/3/8 particles, each family, noise regimes, fitter/ensemble sizes, failing predictors, artifact and package sizes.
2. Load API/SQL separately with fake providers; then run 10 → 25 → 50 → 100 investigations plus viewers and builds. Hold 100 for two hours and run a 24-hour mixed soak; keep immutable environment/version/results.
3. Offer 300 runs and 5× request bursts. Require bounded memory/queue growth, documented rejection, tenant fairness and zero duplicate logical experiments. 300 is not a capacity promise.
4. Inject worker/DB/network/provider faults during the forecast workload. Compare recovery, billing ambiguity and error distributions.
5. Use a small capped real-provider trial for latency/rate validation. Never load-test providers with an unbounded paid sweep.

Add read replicas only after measured read saturation remains after indexing/query reduction; do not use replicas for quota or authorization decisions. Add Redis only for a measured nonauthoritative hot path with explicit invalidation. Partition/archive events when index/maintenance/query latency fails its budget, not merely at a fashionable tenant count. Consider sharding/dedicated deployments when a tenant persistently consumes >25% of cluster capacity or isolation contracts require it. Consider a new queue/workflow system when the existing outbox/reconciler cannot meet measured dispatch/recovery targets. Reevaluate region strategy only for signed residency needs or a stricter tested regional RTO.

## 8. Security requirements and threat model

### 8.1 Assets, adversaries and trust boundaries

Protect customer research code/prompts/results, provider credentials, blind-world configurations, authorization state, experiment/usage ledgers, runtime images and release evidence. Adversaries include malicious tenants and packages, compromised accounts/dependencies, accidental overprivileged services and agents following hostile content. A model response, package README, hypothesis or uploaded artifact is data, never authority to change permissions or execute unrestricted tools.

Boundary reviews cover browser ↔ API, identity ↔ memberships, tenant ↔ tenant, agent ↔ broker, build ↔ registry, gateway ↔ provider, predictor ↔ evaluator and CI ↔ production. Sandbox escape and evaluator leakage are release-blocking risks even at low usage.

### 8.2 Threat-to-control matrix

Taxonomy references: [OWASP Top 10:2025](https://top10.owasp.org/2025/) and [OWASP API Security Top 10:2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/). Controls below are this product's proposed engineering requirements.

| Threat | Required controls and verification | Gate / owner |
| --- | --- | --- |
| Broken object/function/property authorization; tenant traversal | Authorize every row, operation, artifact and event; field allowlists; RLS; cross-tenant ID substitution and mass-assignment tests | Before private pilot; BE + SE |
| Account/session takeover or unsafe identity linking | Verified issuer/audience/signature/expiry; explicit account linking; secure browser cookies and CSRF protection; MFA for operators; service-token expiry/revocation | Pilot; BE + SE |
| SSRF and data exfiltration | Agent egress only to scoped broker; block metadata/private networks/public DNS tunneling; gateway fixed provider destinations and no user-controlled URL redirects | Before any uploaded code; PL + SE |
| Package/build compromise and supply-chain injection | Lockfiles/hashes, dependency allowlist or reviewed mirror, isolated build hooks, no production secrets, image digest verification, provenance/SBOM and quarantine | Before any uploaded code; PL |
| Sandbox escape / resource exhaustion | Enforced sandbox runtime; no privileged pods/host mounts/service-account tokens; read-only base; process/CPU/memory/disk/output/time limits; adversarial test corpus | Pilot; PL + SE |
| Prompt injection / unsafe model output | Treat annotations and observations as untrusted; parse schema-bound actions; tool allowlist; quotas outside the agent; no evaluator or credential retrieval tool | Before model integration; RS + SE |
| Evaluation contamination or hidden-truth leakage | Separate identities/buckets/processes; no active-run score channel; redacted errors; sealed manifest; blind-query limits; adversarial predictor tests | Before official scoring; RS + SE |
| Injection and unsafe rendering/deserialization | Parameterized SQL; validated paths/archive extraction; HTML/Markdown sanitization; CSP; no trusted pickle loading; upload decompression limits | Pilot; BE + FE |
| Unrestricted resource consumption / business-flow abuse | Admission and per-tenant/run quotas; build/publish/invite limits; provider token reservations; no anonymous code execution | Pilot; BE + PL |
| Cryptographic or secret-handling failure | TLS, managed encryption, gateway-only provider keys, secret rotation/revocation, log redaction; no key material in manifests or CI outputs | Pilot; PL + SE |
| Integrity, replay and stale worker writes | Canonical request hashes, idempotency uniqueness, lease epochs, content hashes, generation preconditions and signed image verification | Pilot; BE + PL |
| Misconfiguration / undocumented API exposure | IaC policy checks; route inventory; separate env identities; fail-closed startup configuration; no debug endpoints or public buckets | Pilot; PL + SE |
| Logging gaps / sensitive logs | Actor/action/object/outcome audit events; access restriction; redaction tests; high-signal alerts; immutable export path | Pilot basic; GA export; SE |
| Exceptional conditions / unsafe upstream responses | Bounded response parsing, explicit timeouts, circuit breakers, ambiguous billing states, safe failures and no unbounded retry | Pilot; BE |
| Backup resurrection / malicious deletion | Separate backup identity/project boundary where feasible; restore rehearsal; deletion tombstones reapplied before access; owner and operational audit | Pilot restore; GA DR; PL |

Hosted uploaded-code isolation is never deferred to “enterprise later.” If security gates fail, disable hosted uploads and keep the service internal until fixed. Do not advertise local trusted execution or Docker Compose as hostile-code isolation.

### 8.3 Access and secret design

- Roles: owner manages members, provider connections, quotas, publication and deletion; researcher creates/runs authorized studies; viewer reads permitted artifacts. Owners do not automatically gain official blind-suite truth.
- Membership is checked from current application state. Remove/revoke blocks new API calls immediately. Immediately before every SSE payload batch, recheck current session/credential, grant and workspace authority (and applicable run lease). Recheck idle connections at least every 30 seconds; that interval is not cached authorization for payload delivery. Run tokens expire/revoke promptly.
- Machine clients use workspace-scoped service principals with narrow scopes; store only credential hashes where possible. Run tokens are short-lived, audience-bound, resource-bound and issued to a particular attempt/epoch.
- Operator access uses named accounts, MFA, least privilege and time-bounded elevation. Break-glass use is audited and tested, with no shared permanent administrator password.
- Secret Manager stores provider and OAuth credentials; only the gateway/appropriate identity integration accesses them. Agent checkpoints and public artifacts cannot contain platform credentials.
- Uploaded dependencies are fetched through a constrained build path; runtime installs and general internet access are disabled. Separately audit build-to-registry write permission to prevent replacing trusted images.

### 8.4 Enterprise security and compliance boundary

Before GA: independent penetration test of tenant/API/sandbox/build/evaluator paths; remediate exploitable critical/high findings; document lower-risk exceptions with owner and expiry; SSO/offboarding and key rotation exercised; subprocessor/data-flow inventory, DPA/security questionnaire and customer incident-contact process reviewed by appropriate specialists.

Do not claim SOC 2, ISO 27001, HIPAA or GDPR certification/compliance. If buyers require an assurance program, first define legal/entity/system scope, responsible owners, policies, evidence collection and independent review. Synthetic worlds do not eliminate privacy duties for account data, prompts or uploaded code. Contractual/data-protection conclusions require qualified review; no certification is an automatic result of this architecture.

## 9. Testing and release quality strategy

### 9.1 Verification layers

| Layer / evidence ID | What it protects | Where / frequency | Blocking condition |
| --- | --- | --- | --- |
| V01 Numerical tests | Analytic trajectories, convergence, conservation where valid, noise independence, stable supported domains | Local + every core PR | Solver correctness regression or unexplained numerical change |
| V02 Schema/contract tests | Strict inputs, version compatibility, finite outputs, generated client parity, SSE resync | Local + PR CI; SDK/API matrix | Breaking undeclared schema change |
| V03 Persistence/concurrency integration | Reservations, quotas, PostgreSQL transactions, stale epochs, checkpoint/object ordering | PR CI with PostgreSQL/object adapter; nightly real-service tests | Duplicate debit/result, lost acknowledged result or budget bypass |
| V04 Authorization/isolation | Role matrix, tenant traversal, RLS pool reuse, artifact/SSE paths, sandbox network/DNS/metadata | PR negative tests + staging adversarial suite | Any cross-tenant/evaluator/credential access |
| V05 End-to-end product | Invite → build → run → interrupt/resume → cancel → replay/export → delete | CI smoke; staging full journey; supported browsers | Core journey fails or misrepresents status |
| V06 Research evaluation | Paired seeds, no hidden feedback, frozen splits, failure penalties, bootstrap/censoring | CI small fixed fixtures; scheduled development suite; release full suite | Leakage, changed metric after freeze, missing scored failures |
| V07 Provider protocol | Timeouts, malformed replies, 429/5xx, ambiguous attempts, token reservation, version recording | CI fake providers; capped integration trial | Hidden retry spend or silent model substitution |
| V08 Load/soak/fairness | Section 7 latency/capacity/queue/DB/memory and evaluator backlog | Staging before R6/R8; rerun on material changes | Forecast envelope fails or overload corrupts state |
| V09 Failure injection | Worker death at each commit boundary, duplicate dispatch, DB failover, artifact outage, lease partition | Staging/nightly scoped drills; pre-release | State/usage corruption or recovery beyond target |
| V10 Migration/upgrade/rollback | Expand-contract schemas, older clients/workers, artifact readers, self-host restore | CI migration fixtures + staging restore | Destructive irreversible release without supported recovery |
| V11 Supply chain / security | Dependency/secret/static/container scanning, provenance, policy, hostile archives/build hooks | PR, image build, scheduled vulnerability check | Exposed secret, unsigned substituted image, exploitable critical/high issue |
| V12 Operational/data lifecycle | Alerts, deletion tombstones, backup expiry, audit export, key rotation, incident drill | Pre-pilot/pre-GA; regular production drills in isolated recovery env | Unrestorable data or unowned incident response |

The existing 55 tests cover part of V01–V03 for local execution, not this entire matrix. Do not substitute an arbitrary coverage percentage for failure-mode evidence. New code requires meaningful boundary tests; no tests that merely assert implementation-shaped values.

Requirement-to-verification mapping (all V IDs refer to the table above):

| Requirement | Required verification families |
| --- | --- |
| REQ01 | V01, V02, V06 |
| REQ02 | V02, V06, V07 |
| REQ03 | V01, V04, V06 |
| REQ04 | V02, V04, V11 |
| REQ05 | V03, V09, V10 |
| REQ06 | V04, V05, V12 |
| REQ07 | V03, V07, V08 |
| REQ08 | V02, V04, V05, V08 |
| REQ09 | V01, V02, V05 |
| REQ10 | V02, V05, V10, V12 |
| REQ11 | V08, V09 |
| REQ12 | V09, V10, V12 |
| REQ13 | V04, V11, V12 |
| REQ14 | V02, V04, V05, V12 |
| REQ15 | V08, V09, V10, V11, V12 |
| REQ16 | V04, V06, V11 |

### 9.2 Definition of done for a work package

- Requirement and contract reviewed; explicit acceptance cases implemented.
- Correct positive and negative behavior under realistic failures, with immutable check evidence.
- Lint, format, types and relevant tests pass; new dependencies locked/scanned.
- Security/privacy and research effects reviewed by the appropriate owner.
- Upgrade/configuration/operations documentation updated where behavior changes.
- Telemetry includes useful failure context and excludes secrets.
- This roadmap has status, implementation identity, evidence and limitations updated.
- An external-facing feature is verified in its intended environment; a mock does not prove cloud integration.

### 9.3 Release blockers and acceptable risk

Block release for data loss of acknowledged work outside a disclosed disaster scenario, duplicate logical charges, tenant/evaluator leakage, invalid scientific comparisons, critical/high exploitable security findings, failed restore, absent rollback, or failure of the supported load envelope. A nice UI does not waive these.

Medium/low issues may ship only with scoped impact, compensating control, accountable owner and dated remediation, approved by lead and security/product as appropriate. An AI method performing poorly is a valid research result, not a defect to suppress. Unknown provider charges must be visible and reconciled; do not present estimated costs as final bills.

## 10. Dependency-aware milestones and exit gates

The execution audit replaces the earlier unvalidated 118 PW/25% estimate and W30–36 GA forecast. Bottom-up work is **689 delivery engineer-days (137.8 PW)**, including four postlaunch days, plus **248.3 days (49.66 PW) of confidence-weighted contingency**. Nine engineers at 70% delivery capacity provide 6.3 PW/week collectively; prerequisite chains and specialist queues make elapsed time longer than effort divided by team size.

The [execution backlog](EXECUTION_BACKLOG.md) and [machine-readable plan](execution-backlog.json) contain 168 PR tasks, ten approval/calendar gates, 369 prerequisites and both resource-checked forecast scenarios. Initial execution is approved; assignments and actual status are in EXECUTION_LOG.md. Later slices and concrete paid/release actions retain their gates. Forecast **pilot onboarding W38–50, complete R7 evidence W45–59 and GA W52–67** from a staffed approved start. This is a feasible conservative schedule, not an optimized commitment or statistical confidence interval. Unknown approval/partner delays and measured sweep execution time can extend it. Reforecast after D10, R0 and each integration checkpoint.

Old M0 is the implemented local baseline; M1 maps to R1/R4, M2 to R2/R3, M3 to R4, M4 to R5 and M5 to R6–R8. R0 uses subset contract freezes; the complete product API and enterprise protocol are not promised in two weeks.

| Milestone | Earliest base work | Base / reserve exit | Delivery / reserve PW | Owner / status |
| --- | --- | --- | --- | --- |
| R0 — Scope, contracts and environment readiness | W1 | W6 / W7 | 6.2 / 1.71 | TL + product; in progress |
| R1 — Scientifically valid learning and evaluation core | W2 | W18 / W26 | 17.2 / 6.90 | Research lead; planned, prerequisites pending |
| R2 — Private durable control plane | W3 | W16 / W20 | 14.0 / 3.95 | Backend lead; planned, prerequisites pending |
| R3 — Isolated execution and recoverable data | W2 | W24 / W33 | 23.8 / 8.35 | Platform lead + security; planned, prerequisites pending |
| R4 — Provider integration and both research tracks | W5 | W27 / W36 | 16.2 / 6.30 | Research + backend; planned, prerequisites pending |
| R5 — Researcher product and supported self-hosting | W1 | W30 / W40 | 19.4 / 5.35 | Frontend + platform; planned, prerequisites pending |
| R6 — Integrated production pilot readiness | W18 | W35 / W45 | 14.2 / 5.55 | QE + security + platform; planned, prerequisites pending |
| R7 — Design-partner evidence and reference publication | W35 | W45 / W59 | 8.4 / 3.80 | Product + research; planned, prerequisites pending |
| R8 — Enterprise GA readiness and rollout | W7 | W52 / W67 | 17.6 / 7.55 | TL + security + platform; planned, prerequisites pending |
| POST — Postlaunch reviews | W53 | W57 / W72 | 0.8 / 0.20 | TL + product; planned, prerequisites pending |

### R0 — Scope, contracts and environment readiness

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-00.b](EXECUTION_BACKLOG.md#sp-00-b), [SP-00.c](EXECUTION_BACKLOG.md#sp-00-c), [SP-01.e](EXECUTION_BACKLOG.md#sp-01-e), [SP-02.b](EXECUTION_BACKLOG.md#sp-02-b), [SP-02.c](EXECUTION_BACKLOG.md#sp-02-c); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Signed baseline and subset contracts; named staff/partners pipeline; pinned client/mock checks; safe headroom and priced authorized staging config. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: TL + product.

**Risks / release blockers:** No contract consumer starts until its specific subset is accepted; whole R0 exit need not serialize independent numerical work.

### R1 — Scientifically valid learning and evaluation core

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-03.d](EXECUTION_BACKLOG.md#sp-03-d), [SP-04.e](EXECUTION_BACKLOG.md#sp-04-e), [SP-07.d](EXECUTION_BACKLOG.md#sp-07-d); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Independent spring slice and full numerical/identifiability report; development uncertainty/failure/precision and total evaluator-cost evidence; both candidate protocols versioned. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Research lead.

**Risks / release blockers:** Invalid domain or uncalibrated uncertainty blocks official study; milestone may end in documented redesign.

### R2 — Private durable control plane

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-08.d](EXECUTION_BACKLOG.md#sp-08-d), [SP-09.d](EXECUTION_BACKLOG.md#sp-09-d), [SP-10.c](EXECUTION_BACKLOG.md#sp-10-c), [SP-11.c](EXECUTION_BACKLOG.md#sp-11-c), [SP-12.c](EXECUTION_BACKLOG.md#sp-12-c); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Real PostgreSQL concurrency/RLS tests; auth, invitations, basic service/run credentials, budgets, outbox, epochs and revocation verified. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Backend lead.

**Risks / release blockers:** No private or uploaded customer runtime before integrated R3 security and release review.

### R3 — Isolated execution and recoverable data

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-13.d](EXECUTION_BACKLOG.md#sp-13-d), [SP-14.d](EXECUTION_BACKLOG.md#sp-14-d), [SP-15.e](EXECUTION_BACKLOG.md#sp-15-e), [SP-16.d](EXECUTION_BACKLOG.md#sp-16-d), [SP-16.e](EXECUTION_BACKLOG.md#sp-16-e), [SP-27.f](EXECUTION_BACKLOG.md#sp-27-f), [SP-37.c](EXECUTION_BACKLOG.md#sp-37-c); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Real staged remote recovery and hostile build/runtime/network evidence; immutable artifacts/checkpoints; basic audit/delete/tombstone replay; signed deploy/rollback/telemetry. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Platform lead + security.

**Risks / release blockers:** SP-37.a–c moved here; managed runtime fail-closed and no missing committed artifacts are nonwaivable.

### R4 — Provider integration and both research tracks

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-17.d](EXECUTION_BACKLOG.md#sp-17-d), [SP-18.d](EXECUTION_BACKLOG.md#sp-18-d), [SP-19.d](EXECUTION_BACKLOG.md#sp-19-d), [SP-20.d](EXECUTION_BACKLOG.md#sp-20-d), [SP-21.c](EXECUTION_BACKLOG.md#sp-21-c); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Capped provider trial; ambiguous billing/replay tested; hostile executable predictor validation; complete controlled and discovery manifests with no truth feedback. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Research + backend.

**Risks / release blockers:** Paid-trial gate separate; both tracks and failed rows required, no cherry-picked demonstration.

### R5 — Researcher product and supported self-hosting

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-22.e](EXECUTION_BACKLOG.md#sp-22-e), [SP-23.d](EXECUTION_BACKLOG.md#sp-23-d), [SP-24.d](EXECUTION_BACKLOG.md#sp-24-d), [SP-25.e](EXECUTION_BACKLOG.md#sp-25-e), [SP-26.d](EXECUTION_BACKLOG.md#sp-26-d); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Accessible author→run→inspect→export; durable SSE/resync; offline replay; supported fresh install/upgrade with explicit trust limitations. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Frontend + platform.

**Risks / release blockers:** World/provider/publication/SSE backend tasks precede consumers; internal install is not external adoption.

### R6 — Integrated production pilot readiness

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-28.d](EXECUTION_BACKLOG.md#sp-28-d), [SP-29.d](EXECUTION_BACKLOG.md#sp-29-d), [SP-30.d](EXECUTION_BACKLOG.md#sp-30-d), [SP-31.e](EXECUTION_BACKLOG.md#sp-31-e); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** R1–R5 integrated at exact candidate; 100-run hold/soak/fairness, real failover/restore, negative security, deletion, migration and complete journeys pass. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: QE + security + platform.

**Risks / release blockers:** Any lost acknowledged state, duplicate logical debit, critical/high exploit, leak or failed restore blocks pilot.

### R7 — Design-partner evidence and reference publication

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-32.c](EXECUTION_BACKLOG.md#sp-32-c), [SP-33.c](EXECUTION_BACKLOG.md#sp-33-c), [SP-36.d](EXECUTION_BACKLOG.md#sp-36-d); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Actual four-week partner use and outcome denominators; external agent/law/install/upgrade/reproduction; approved scored suite with all failures sanitized. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: Product + research.

**Risks / release blockers:** External readiness, price approval and sweep wall time are real dependencies; missing evidence blocks adoption claims.

### R8 — Enterprise GA readiness and rollout

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-34.d](EXECUTION_BACKLOG.md#sp-34-d), [SP-35.c](EXECUTION_BACKLOG.md#sp-35-c), [SP-37.f](EXECUTION_BACKLOG.md#sp-37-f), [SP-38.c](EXECUTION_BACKLOG.md#sp-38-c), [SP-39.b](EXECUTION_BACKLOG.md#sp-39-b), [SP-40.e](EXECUTION_BACKLOG.md#sp-40-e), [SP-41.b](EXECUTION_BACKLOG.md#sp-41-b); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** Federation/SCIM/audit/retention validated; independent assessment resolved; regional drill; final capacity test; staffed incident drill and 30-day SLO evidence; explicit rollout approval. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: TL + security + platform.

**Risks / release blockers:** R7 and all gate evidence required. Material candidate changes invalidate affected evidence; no compliance or unlimited-scale claim.

### POST — Postlaunch reviews

**Entry / dependencies:** use the [leaf prerequisite graph](EXECUTION_BACKLOG.md#task-index), not a whole-epic wait. All actual approvals and required contract subsets must exist before dependent work.

**Exit joins:** [SP-41.c](EXECUTION_BACKLOG.md#sp-41-c), [SP-41.d](EXECUTION_BACKLOG.md#sp-41-d); every other task allocated to this milestone must also be done.

**Acceptance / tests / done:** D7 and D30 outcomes reviewed with corrective owners and new scope decisions. Exact source/runtime/config, executed checks, reviewers and limitations are required. Owner: TL + product.

**Risks / release blockers:** Scheduled after GA; never used as a pre-GA dependency.

### Critical path and integration

The resource-constrained base chain runs through contracts/SQL/authorization, backend broker/provider/event/lifecycle work, the real world/live/replay product, integrated journeys, partner terms/final privacy controls, independent assessment, final capacity/incident review and 30 consecutive calendar days of SLO evidence before GA. Research validity, isolation and partner availability can become controlling paths. [Exact chain and parallel work](EXECUTION_BACKLOG.md#critical-path-and-parallel-work) distinguish technical edges from author-resource contention.

Integration checkpoints are I0 baseline/subset contracts, I1 independent spring fit/predict/score, I2 private transactional run, I3 isolated remote recovery, I4 both tracks/product/self-hosting, I5 pilot release candidate, I6 independently assessed final candidate/operations and I7 authorized GA. Each has explicit joining tasks in the [checkpoint table](EXECUTION_BACKLOG.md#integration-checkpoints). Dates alone never pass a gate. D7/D30 reviews are postlaunch, not prerequisites of GA.

## 11. Prioritized engineering backlog

The 42 [GitHub issues](https://github.com/spei04/strange-physics/issues) are epic rollups. The assignable units are the **168 PR-sized task records** in [EXECUTION_BACKLOG.md](EXECUTION_BACKLOG.md#task-index), each containing objective, detailed scope, explicit exclusions, prerequisites, contracts, acceptance, automated tests, security/reliability, effort/confidence, role and definition of done. [execution-backlog.json](execution-backlog.json) is the machine-readable ledger for the same records and both schedules. Keep these synchronized in every relevant PR.

Legacy 112 native whole-epic blocker links are superseded by the finer 369-edge task/gate DAG. They cannot correctly represent partial contract handoffs and parallel child work; parent issue state does not establish leaf readiness. Epic issues remain rollups; current leaf assignments and evidence are recorded in the backlog and execution log. Materialize child issues from the approved leaf records when assigning work; do not implement an entire parent in a single PR.

| Epic / issue | Reviewable units | Delivery PW | Milestone allocation |
| --- | --- | --- | --- |
| [SP-00 — Approve scope, staff and evidence baseline](https://github.com/spei04/strange-physics/issues/2) | [SP-00.a](EXECUTION_BACKLOG.md#sp-00-a), [SP-00.b](EXECUTION_BACKLOG.md#sp-00-b), [SP-00.c](EXECUTION_BACKLOG.md#sp-00-c) | 1.2 | R0 |
| [SP-01 — Freeze shared schemas and mocks](https://github.com/spei04/strange-physics/issues/3) | [SP-01.a](EXECUTION_BACKLOG.md#sp-01-a), [SP-01.b](EXECUTION_BACKLOG.md#sp-01-b), [SP-01.c](EXECUTION_BACKLOG.md#sp-01-c), [SP-01.d](EXECUTION_BACKLOG.md#sp-01-d), [SP-01.e](EXECUTION_BACKLOG.md#sp-01-e) | 3.8 | R0 |
| [SP-02 — Verify cloud and workspace prerequisites](https://github.com/spei04/strange-physics/issues/4) | [SP-02.a](EXECUTION_BACKLOG.md#sp-02-a), [SP-02.b](EXECUTION_BACKLOG.md#sp-02-b), [SP-02.c](EXECUTION_BACKLOG.md#sp-02-c) | 1.2 | R0 |
| [SP-03 — Validate numerical domain and baseline](https://github.com/spei04/strange-physics/issues/5) | [SP-03.a](EXECUTION_BACKLOG.md#sp-03-a), [SP-03.b](EXECUTION_BACKLOG.md#sp-03-b), [SP-03.c](EXECUTION_BACKLOG.md#sp-03-c), [SP-03.d](EXECUTION_BACKLOG.md#sp-03-d) | 3.0 | R1 |
| [SP-04 — Implement integrated sparse fitter](https://github.com/spei04/strange-physics/issues/6) | [SP-04.a](EXECUTION_BACKLOG.md#sp-04-a), [SP-04.b](EXECUTION_BACKLOG.md#sp-04-b), [SP-04.c](EXECUTION_BACKLOG.md#sp-04-c), [SP-04.d](EXECUTION_BACKLOG.md#sp-04-d), [SP-04.e](EXECUTION_BACKLOG.md#sp-04-e) | 3.8 | R1 |
| [SP-05 — Add uncertainty, adaptation and active selection](https://github.com/spei04/strange-physics/issues/7) | [SP-05.a](EXECUTION_BACKLOG.md#sp-05-a), [SP-05.b](EXECUTION_BACKLOG.md#sp-05-b), [SP-05.c](EXECUTION_BACKLOG.md#sp-05-c), [SP-05.d](EXECUTION_BACKLOG.md#sp-05-d) | 3.2 | R1 |
| [SP-06 — Implement held-out metrics and failure policy](https://github.com/spei04/strange-physics/issues/8) | [SP-06.a](EXECUTION_BACKLOG.md#sp-06-a), [SP-06.b](EXECUTION_BACKLOG.md#sp-06-b), [SP-06.c](EXECUTION_BACKLOG.md#sp-06-c), [SP-06.d](EXECUTION_BACKLOG.md#sp-06-d) | 3.4 | R1 |
| [SP-07 — Calibrate and draft frozen study manifests](https://github.com/spei04/strange-physics/issues/9) | [SP-07.a](EXECUTION_BACKLOG.md#sp-07-a), [SP-07.b](EXECUTION_BACKLOG.md#sp-07-b), [SP-07.c](EXECUTION_BACKLOG.md#sp-07-c), [SP-07.d](EXECUTION_BACKLOG.md#sp-07-d) | 3.8 | R1 |
| [SP-08 — Build identity and workspace memberships](https://github.com/spei04/strange-physics/issues/10) | [SP-08.a](EXECUTION_BACKLOG.md#sp-08-a), [SP-08.b](EXECUTION_BACKLOG.md#sp-08-b), [SP-08.c](EXECUTION_BACKLOG.md#sp-08-c), [SP-08.d](EXECUTION_BACKLOG.md#sp-08-d) | 3.0 | R2 |
| [SP-09 — Implement run and experiment transactions](https://github.com/spei04/strange-physics/issues/11) | [SP-09.a](EXECUTION_BACKLOG.md#sp-09-a), [SP-09.b](EXECUTION_BACKLOG.md#sp-09-b), [SP-09.c](EXECUTION_BACKLOG.md#sp-09-c), [SP-09.d](EXECUTION_BACKLOG.md#sp-09-d) | 3.4 | R2 |
| [SP-10 — Add outbox, fencing and reconciliation](https://github.com/spei04/strange-physics/issues/12) | [SP-10.a](EXECUTION_BACKLOG.md#sp-10-a), [SP-10.b](EXECUTION_BACKLOG.md#sp-10-b), [SP-10.c](EXECUTION_BACKLOG.md#sp-10-c) | 2.8 | R2 |
| [SP-11 — Enforce tenant and artifact authorization](https://github.com/spei04/strange-physics/issues/13) | [SP-11.a](EXECUTION_BACKLOG.md#sp-11-a), [SP-11.b](EXECUTION_BACKLOG.md#sp-11-b), [SP-11.c](EXECUTION_BACKLOG.md#sp-11-c) | 2.4 | R2 |
| [SP-12 — Implement quotas and usage accounting](https://github.com/spei04/strange-physics/issues/14) | [SP-12.a](EXECUTION_BACKLOG.md#sp-12-a), [SP-12.b](EXECUTION_BACKLOG.md#sp-12-b), [SP-12.c](EXECUTION_BACKLOG.md#sp-12-c) | 2.4 | R2 |
| [SP-13 — Persist immutable artifacts and checkpoints](https://github.com/spei04/strange-physics/issues/15) | [SP-13.a](EXECUTION_BACKLOG.md#sp-13-a), [SP-13.b](EXECUTION_BACKLOG.md#sp-13-b), [SP-13.c](EXECUTION_BACKLOG.md#sp-13-c), [SP-13.d](EXECUTION_BACKLOG.md#sp-13-d) | 3.0 | R3 |
| [SP-14 — Build packages in isolation](https://github.com/spei04/strange-physics/issues/16) | [SP-14.a](EXECUTION_BACKLOG.md#sp-14-a), [SP-14.b](EXECUTION_BACKLOG.md#sp-14-b), [SP-14.c](EXECUTION_BACKLOG.md#sp-14-c), [SP-14.d](EXECUTION_BACKLOG.md#sp-14-d) | 3.6 | R3 |
| [SP-15 — Enforce sandbox runtime and broker policy](https://github.com/spei04/strange-physics/issues/17) | [SP-15.a](EXECUTION_BACKLOG.md#sp-15-a), [SP-15.b](EXECUTION_BACKLOG.md#sp-15-b), [SP-15.c](EXECUTION_BACKLOG.md#sp-15-c), [SP-15.d](EXECUTION_BACKLOG.md#sp-15-d), [SP-15.e](EXECUTION_BACKLOG.md#sp-15-e) | 4.4 | R3 |
| [SP-16 — Connect recoverable remote execution](https://github.com/spei04/strange-physics/issues/18) | [SP-16.a](EXECUTION_BACKLOG.md#sp-16-a), [SP-16.b](EXECUTION_BACKLOG.md#sp-16-b), [SP-16.c](EXECUTION_BACKLOG.md#sp-16-c), [SP-16.d](EXECUTION_BACKLOG.md#sp-16-d), [SP-16.e](EXECUTION_BACKLOG.md#sp-16-e) | 4.6 | R3 |
| [SP-17 — Implement durable model-call ledger](https://github.com/spei04/strange-physics/issues/19) | [SP-17.a](EXECUTION_BACKLOG.md#sp-17-a), [SP-17.b](EXECUTION_BACKLOG.md#sp-17-b), [SP-17.c](EXECUTION_BACKLOG.md#sp-17-c), [SP-17.d](EXECUTION_BACKLOG.md#sp-17-d) | 3.4 | R4 |
| [SP-18 — Add bounded provider adapters and LLM selector](https://github.com/spei04/strange-physics/issues/20) | [SP-18.a](EXECUTION_BACKLOG.md#sp-18-a), [SP-18.b](EXECUTION_BACKLOG.md#sp-18-b), [SP-18.c](EXECUTION_BACKLOG.md#sp-18-c), [SP-18.d](EXECUTION_BACKLOG.md#sp-18-d) | 3.0 | R4 |
| [SP-19 — Define executable predictor packaging](https://github.com/spei04/strange-physics/issues/21) | [SP-19.a](EXECUTION_BACKLOG.md#sp-19-a), [SP-19.b](EXECUTION_BACKLOG.md#sp-19-b), [SP-19.c](EXECUTION_BACKLOG.md#sp-19-c), [SP-19.d](EXECUTION_BACKLOG.md#sp-19-d) | 3.4 | R4 |
| [SP-20 — Build independent evaluation execution](https://github.com/spei04/strange-physics/issues/22) | [SP-20.a](EXECUTION_BACKLOG.md#sp-20-a), [SP-20.b](EXECUTION_BACKLOG.md#sp-20-b), [SP-20.c](EXECUTION_BACKLOG.md#sp-20-c), [SP-20.d](EXECUTION_BACKLOG.md#sp-20-d) | 3.6 | R4 |
| [SP-21 — Integrate the two research tracks](https://github.com/spei04/strange-physics/issues/23) | [SP-21.a](EXECUTION_BACKLOG.md#sp-21-a), [SP-21.b](EXECUTION_BACKLOG.md#sp-21-b), [SP-21.c](EXECUTION_BACKLOG.md#sp-21-c) | 2.8 | R4 |
| [SP-22 — Build workspace and constrained world UI](https://github.com/spei04/strange-physics/issues/24) | [SP-22.a](EXECUTION_BACKLOG.md#sp-22-a), [SP-22.b](EXECUTION_BACKLOG.md#sp-22-b), [SP-22.c](EXECUTION_BACKLOG.md#sp-22-c), [SP-22.d](EXECUTION_BACKLOG.md#sp-22-d), [SP-22.e](EXECUTION_BACKLOG.md#sp-22-e) | 4.2 | R5 |
| [SP-23 — Implement live event timeline and reconnection](https://github.com/spei04/strange-physics/issues/25) | [SP-23.a](EXECUTION_BACKLOG.md#sp-23-a), [SP-23.b](EXECUTION_BACKLOG.md#sp-23-b), [SP-23.c](EXECUTION_BACKLOG.md#sp-23-c), [SP-23.d](EXECUTION_BACKLOG.md#sp-23-d) | 3.6 | R5 |
| [SP-24 — Implement prediction and replay diagnostics](https://github.com/spei04/strange-physics/issues/26) | [SP-24.a](EXECUTION_BACKLOG.md#sp-24-a), [SP-24.b](EXECUTION_BACKLOG.md#sp-24-b), [SP-24.c](EXECUTION_BACKLOG.md#sp-24-c), [SP-24.d](EXECUTION_BACKLOG.md#sp-24-d) | 3.4 | R5 |
| [SP-25 — Deliver remote SDK, CLI and complete export](https://github.com/spei04/strange-physics/issues/27) | [SP-25.a](EXECUTION_BACKLOG.md#sp-25-a), [SP-25.b](EXECUTION_BACKLOG.md#sp-25-b), [SP-25.c](EXECUTION_BACKLOG.md#sp-25-c), [SP-25.d](EXECUTION_BACKLOG.md#sp-25-d), [SP-25.e](EXECUTION_BACKLOG.md#sp-25-e) | 4.4 | R5 |
| [SP-26 — Package supported self-host deployment](https://github.com/spei04/strange-physics/issues/28) | [SP-26.a](EXECUTION_BACKLOG.md#sp-26-a), [SP-26.b](EXECUTION_BACKLOG.md#sp-26-b), [SP-26.c](EXECUTION_BACKLOG.md#sp-26-c), [SP-26.d](EXECUTION_BACKLOG.md#sp-26-d) | 3.8 | R5 |
| [SP-27 — Create IaC and trusted delivery foundation](https://github.com/spei04/strange-physics/issues/29) | [SP-27.a](EXECUTION_BACKLOG.md#sp-27-a), [SP-27.b](EXECUTION_BACKLOG.md#sp-27-b), [SP-27.c](EXECUTION_BACKLOG.md#sp-27-c), [SP-27.d](EXECUTION_BACKLOG.md#sp-27-d), [SP-27.e](EXECUTION_BACKLOG.md#sp-27-e), [SP-27.f](EXECUTION_BACKLOG.md#sp-27-f) | 5.2 | R3 |
| [SP-28 — Measure capacity and fairness](https://github.com/spei04/strange-physics/issues/30) | [SP-28.a](EXECUTION_BACKLOG.md#sp-28-a), [SP-28.b](EXECUTION_BACKLOG.md#sp-28-b), [SP-28.c](EXECUTION_BACKLOG.md#sp-28-c), [SP-28.d](EXECUTION_BACKLOG.md#sp-28-d) | 3.6 | R6 |
| [SP-29 — Prove backup, failover and fault recovery](https://github.com/spei04/strange-physics/issues/31) | [SP-29.a](EXECUTION_BACKLOG.md#sp-29-a), [SP-29.b](EXECUTION_BACKLOG.md#sp-29-b), [SP-29.c](EXECUTION_BACKLOG.md#sp-29-c), [SP-29.d](EXECUTION_BACKLOG.md#sp-29-d) | 3.6 | R6 |
| [SP-30 — Verify integrated journeys and upgrades](https://github.com/spei04/strange-physics/issues/32) | [SP-30.a](EXECUTION_BACKLOG.md#sp-30-a), [SP-30.b](EXECUTION_BACKLOG.md#sp-30-b), [SP-30.c](EXECUTION_BACKLOG.md#sp-30-c), [SP-30.d](EXECUTION_BACKLOG.md#sp-30-d) | 3.0 | R6 |
| [SP-31 — Exercise security and data boundaries](https://github.com/spei04/strange-physics/issues/33) | [SP-31.a](EXECUTION_BACKLOG.md#sp-31-a), [SP-31.b](EXECUTION_BACKLOG.md#sp-31-b), [SP-31.c](EXECUTION_BACKLOG.md#sp-31-c), [SP-31.d](EXECUTION_BACKLOG.md#sp-31-d), [SP-31.e](EXECUTION_BACKLOG.md#sp-31-e) | 4.0 | R6 |
| [SP-32 — Onboard and support design partners](https://github.com/spei04/strange-physics/issues/34) | [SP-32.a](EXECUTION_BACKLOG.md#sp-32-a), [SP-32.b](EXECUTION_BACKLOG.md#sp-32-b), [SP-32.c](EXECUTION_BACKLOG.md#sp-32-c) | 2.2 | R7 |
| [SP-33 — Freeze and publish scored reference release](https://github.com/spei04/strange-physics/issues/35) | [SP-33.a](EXECUTION_BACKLOG.md#sp-33-a), [SP-33.b](EXECUTION_BACKLOG.md#sp-33-b), [SP-33.c](EXECUTION_BACKLOG.md#sp-33-c) | 2.6 | R7 |
| [SP-34 — Add enterprise SSO and service identities](https://github.com/spei04/strange-physics/issues/36) | [SP-34.a](EXECUTION_BACKLOG.md#sp-34-a), [SP-34.b](EXECUTION_BACKLOG.md#sp-34-b), [SP-34.c](EXECUTION_BACKLOG.md#sp-34-c), [SP-34.d](EXECUTION_BACKLOG.md#sp-34-d) | 3.2 | R8 |
| [SP-35 — Add provisioning and rapid deprovisioning](https://github.com/spei04/strange-physics/issues/37) | [SP-35.a](EXECUTION_BACKLOG.md#sp-35-a), [SP-35.b](EXECUTION_BACKLOG.md#sp-35-b), [SP-35.c](EXECUTION_BACKLOG.md#sp-35-c) | 2.8 | R8 |
| [SP-36 — Validate external extension and self-host adoption](https://github.com/spei04/strange-physics/issues/38) | [SP-36.a](EXECUTION_BACKLOG.md#sp-36-a), [SP-36.b](EXECUTION_BACKLOG.md#sp-36-b), [SP-36.c](EXECUTION_BACKLOG.md#sp-36-c), [SP-36.d](EXECUTION_BACKLOG.md#sp-36-d) | 3.6 | R7 |
| [SP-37 — Ship enterprise audit and retention controls](https://github.com/spei04/strange-physics/issues/39) | [SP-37.a](EXECUTION_BACKLOG.md#sp-37-a), [SP-37.b](EXECUTION_BACKLOG.md#sp-37-b), [SP-37.c](EXECUTION_BACKLOG.md#sp-37-c), [SP-37.d](EXECUTION_BACKLOG.md#sp-37-d), [SP-37.e](EXECUTION_BACKLOG.md#sp-37-e), [SP-37.f](EXECUTION_BACKLOG.md#sp-37-f) | 5.2 | R3, R8 |
| [SP-38 — Rehearse regional disaster recovery](https://github.com/spei04/strange-physics/issues/40) | [SP-38.a](EXECUTION_BACKLOG.md#sp-38-a), [SP-38.b](EXECUTION_BACKLOG.md#sp-38-b), [SP-38.c](EXECUTION_BACKLOG.md#sp-38-c) | 2.8 | R8 |
| [SP-39 — Revalidate supported production envelope](https://github.com/spei04/strange-physics/issues/41) | [SP-39.a](EXECUTION_BACKLOG.md#sp-39-a), [SP-39.b](EXECUTION_BACKLOG.md#sp-39-b) | 1.6 | R8 |
| [SP-40 — Complete independent assurance and operations](https://github.com/spei04/strange-physics/issues/42) | [SP-40.a](EXECUTION_BACKLOG.md#sp-40-a), [SP-40.b](EXECUTION_BACKLOG.md#sp-40-b), [SP-40.c](EXECUTION_BACKLOG.md#sp-40-c), [SP-40.d](EXECUTION_BACKLOG.md#sp-40-d), [SP-40.e](EXECUTION_BACKLOG.md#sp-40-e) | 3.8 | R8 |
| [SP-41 — Approve GA release and post-launch review](https://github.com/spei04/strange-physics/issues/43) | [SP-41.a](EXECUTION_BACKLOG.md#sp-41-a), [SP-41.b](EXECUTION_BACKLOG.md#sp-41-b), [SP-41.c](EXECUTION_BACKLOG.md#sp-41-c), [SP-41.d](EXECUTION_BACKLOG.md#sp-41-d) | 2.0 | R8, POST |

Basic machine/run credentials are SP-08.c; SP-34.d adds enterprise lifecycle. Basic audit/deletion/recovery suppression SP-37.a–c is R3 work despite its parent issue closing at R8. World API SP-22.b, provider-secret API SP-17.c, SSE server/resync SP-23.a/b and publication SP-25.d explicitly precede consuming journeys/tests. First-spring integration is SP-04.e, not completion of the entire sparse-fitting epic.

Post-GA research/scale candidates remain uncommitted: dedicated deployments/CMEK, extra regions, new laws/particle scales, more change regimes/languages, continuous control/RL and pixel input. Each requires separate numerical/security/cost criteria and a new research protocol where applicable.

## 12. Team ownership and delivery schedule

### 12.1 Reference team: nine engineers

| Role / count | Ownership and code boundaries | Required interfaces / review partners | Testing responsibility |
| --- | --- | --- | --- |
| Technical lead (TL), 1 | Architecture, contract review, integration, release ownership; core/shared boundaries | Product, research, security and all subsystem owners | Cross-system invariants and readiness evidence |
| Backend (BE), 2 | API, identity, PostgreSQL state, quotas, broker, gateway, remote SDK | OpenAPI/event/schema freeze; platform execution contracts; frontend client | Transactions, authorization, idempotency, provider and API conformance |
| Platform/SRE (PL), 2 | Terraform, runtime/build isolation, storage, deployment, recovery, on-call systems | Worker/lease/artifact protocols; security policy; backend state machine | Real-cloud isolation, failure/restore, capacity and delivery checks |
| Research engineering (RS), 2 | Simulator validation, fitting, active/LLM selection, uncertainty, protocol and evaluator | Predictor/model/observation contracts; platform evaluator boundary | Numerical validity, leakage, fair comparison and reproducibility |
| Frontend (FE), 1 | Workspace UX, builder, live/replay visualization, accessibility | Generated API client, mock fixtures, event/replay schema | Browser journeys, reconnection, privacy rendering and performance |
| Quality engineering (QE), 1 | Integration harnesses, load/fault matrix, release evidence; not sole test author | All contract owners; staging environment and seeded fixtures | System test orchestration and independent acceptance verification |

Additional fractional support: product/TPM about 0.5 FTE, design about 0.25–0.5 FTE, security specialist about 0.5 FTE during threat-model/isolation/release work, and independent assessor/legal review as needed. These are capacity assumptions, not appointed staff. Each engineer owns tests for their code; QE does not become a queue for all testing.

The resource model requires all nine named lanes at the stated availability. Seven or ten engineers changes the allocation and must be rescheduled from the task graph; the previous unsupported seven-/ten-person date ranges are withdrawn. Hiring/ramp-up and actual external lead times are additional. Reviews are covered by the 30% capacity allowance; named security and partner reviewers remain required.

Proposed CODEOWNERS boundaries once directories exist: core/simulation/laws → research + lead; contracts/SDK → backend + research; API/database → backend; execution/infra → platform + security reviewer; evaluator → research + security; web → frontend; operations → platform; this roadmap → lead + product. Do not add empty directories merely to enact ownership.

### 12.2 Parallel development policy

Freeze shared schemas, migrations and examples before dependent implementation. Let the frontend consume mocks, platform test launcher policy against fake broker fixtures, and research implement predictors against the frozen protocol independently. Integrate real paths at the explicit I0–I7 task joins in EXECUTION_BACKLOG.md; fixed dates do not imply readiness. A mock-based milestone is not a production integration milestone.

Use separate checkouts only for independently active writers. Reuse free cloud checkouts sequentially and install pinned dependencies in copy mode. Never switch a branch beneath another active task or share mutable virtual environments through links. At completion/integration, inspect worktrees and consumers, preserve ignored evidence, then archive unused managed worktrees using the designated archive flow. Do not touch the computer-use project's local workflow.

Contract-affecting PRs need both producer and consumer review; security-boundary changes require security review; scientific protocol changes require research review. Incompatible changes pause downstream integration until fixtures/clients and migration policy are updated.

### 12.3 First two weeks and subsequent scheduling

The [day-by-day D1–D10 plan](EXECUTION_BACKLOG.md#first-two-weeks-day-by-day) records each lane's exact author tasks, predecessor conditions and checkpoints. Day 1 is after user approval and staffing. The machine ledger records fractional-day capacity and dependencies; every proposed start follows predecessor completion. Unassigned lanes can review rather than starting speculative dependent code.

After the first two weeks, schedule at milestone level using section 10. R0 is W6 base/W7 reserve; first independent spring slice W11/W13; pilot onboarding W38–50; R7 evidence W45–59; enterprise GA W52–67. Reforecast after measured cycle time and uncertain-spike outcomes. No calendar launch date is committed.

### 12.4 Capacity and dependency maintenance

The nine-lane plan includes 689 delivery days and 248.3 reserve days. Both scenarios have no resource overlaps or dependency-finish violations. See the [audit method](EXECUTION_BACKLOG.md#dependency-review-and-maintenance). Task-level parallelism is permitted after its specific contract gate; broad parent epic blockers are superseded. Enforce one author task per lane, keep required peer/security review, and rebaseline rather than compress evidence collection when staff or external prerequisites change.

## 13. CI/CD, deployment, reliability and operations

### 13.1 Repository and delivery workflow

Keep the personal repository and existing Python conventions. Small feature branches and reviewed PRs target main; preserve existing work until integrated. Add protected-branch required checks and code-owner review when supported/configured. No direct production deploy from an unreviewed branch. Research protocol releases have their own version and freeze identity.

Current CI is Python 3.12/3.14, locked dependencies, Ruff, strict mypy, pytest, build and CLI smoke. Extend in this order:

1. SP-01: schema snapshot/diff, generated-client and local/remote semantic contract checks.
2. SP-09/13: database migrations, transaction/concurrency and object-store fault integration.
3. SP-14/27: IaC policy/plan, dependency/secret/static/container scans, SBOM and image provenance.
4. SP-23/30: TS lint/types/unit and browser E2E, accessibility and reconnect.
5. R6: ephemeral isolated staging verification, security/fault/load/restore evidence and release manifest.
6. R8: approval gate for production with immutable digests, evidence links and rollback identifier.

GitHub Actions uses short-lived workload identity, restricted to immutable repository/owner identity and the approved environment/ref. Runtime identities are separate from deploy identities. Never pass production secrets to fork PRs or package builds. See [Google's deployment federation guidance](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines).

Maintain dev, isolated staging and prod environments. Separate GCP dev/prod projects are accepted; a distinct staging project is proposed to prevent shared identities/data. If organization constraints force shared nonprod infrastructure, document residual risk before use; never share production customer data or provider secrets with staging.

Use one US primary region, regional production PostgreSQL and tested sandbox-compatible nodes across zones where supported. Set Cloud Run min/max instances, SQL pool budget, queue concurrency and worker pool caps from measured capacity. Approved benchmark sweeps use a separate quota/pool from interactive customers. Store Terraform state privately with locking and controlled recovery access.

### 13.2 Migrations, compatibility and progressive release

Use expand → backfill → dual-read/write only if needed → cutover → contract. Keep old workers/SDKs supported for the published window. Run backfills in bounded resumable batches with progress and rollback checks. Never automatically perform a destructive down-migration during a production rollback.

Release sequence: validate signed image/protocol/config identities → apply compatible schema changes → deploy staging → smoke and required gates → canary trusted API traffic and new runs → observe error/latency/usage → increase rollout → record release. Feature flags are server-controlled and workspace-scoped; they are not authorization controls.

In-flight investigations stay pinned to their runtime and protocol. Route new runs to a new version; retain necessary old worker images/readers until compatible migration or retention expiry. Rollback stops new launches to the bad version, restores previous API/worker defaults and reconciles accepted operations. If the database change is incompatible, prefer a forward fix or rehearsed restore with explicit RPO impact, not an untested reverse migration.

### 13.3 SLI/SLO proposals

These are internal targets until supported by measured service history and customer agreement. Cloud vendor SLAs do not automatically become this product's SLA.

| SLI | Pilot target | GA target / measurement |
| --- | --- | --- |
| Valid API operations served successfully | 99.5% internal objective | 99.9% over rolling 30 days; count eligible requests, include platform 5xx/timeouts and capacity failures within supported envelope |
| Ready-to-run admission/launch latency | Track p95 and failures | ≥99% begin within 120 seconds when within quota and declared capacity; report cold starts separately |
| Platform execution reliability | Explicit terminal outcome; no lost acknowledged experiment | ≥99.5% eligible runs avoid platform-caused terminal failure; user-code/provider/scientific failures separately reported |
| Event freshness | p95 ≤5 seconds | p95 ≤2 seconds from commit to authorized stream |
| Logical budget correctness | No duplicate logical debit | Zero known invariant violations; any violation incident, no error-budget trade |
| Restore success | Every scheduled drill passes or blocks release | Every scheduled drill passes within selected target; real incident evidence retained |

At 99.9%, a 30-day availability budget is approximately 43.2 minutes if measured by time; request-based reporting must state its denominator separately. Keep both user-facing availability and component health dashboards. Do not hide a provider outage from customers merely because it is excluded from the platform-attributable execution metric.

Burn-rate alerts use short and long windows; freeze risky feature releases when the monthly budget is exhausted, except urgent fixes. Assign a measured low-traffic alert path so a single failing synthetic probe is investigated without causing noisy paging.

### 13.4 Backup and disaster-recovery objectives

[Cloud SQL regional HA](https://docs.cloud.google.com/sql/docs/postgres/high-availability) addresses zone/instance failures; it is not a substitute for backups or regional recovery. Configure backups/PITR explicitly and verify the selected edition/location/retention in the [backup documentation](https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups).

| Failure scenario | Proposed RPO (data-loss bound) | Proposed RTO (service recovery) | Gate / proof |
| --- | --- | --- | --- |
| Worker/process loss | 0 committed logical experiments; uncommitted compute may repeat | p95 ≤5 minutes | Pilot forced-termination matrix; epochs prevent stale commits |
| Database zone failover | Target 0 acknowledged DB commits in HA failure model | ≤15 minutes including application reconnection/reconciliation | Pilot real failover drill, object references checked |
| Operator mistake / logical DB corruption | Pilot ≤15 minutes; GA ≤5 minutes within configured PITR window | Pilot ≤4 hours; GA ≤2 hours | Timed point-in-time restore plus object and tombstone validation |
| Entire primary region unavailable | ≤24 hours with daily independently recoverable recovery set | ≤24 hours | GA secondary-region drill; initial product does not promise regional continuity |
| Credential compromise | No automatic data-loss guarantee | Revoke affected access immediately, restore only after containment | Incident/rotation exercise; determine exposure and notify under reviewed obligations |

For regional recovery, retain an independently recoverable DB backup and corresponding artifact generations/manifest in an approved secondary US location, with isolated permissions and keys. Check replication/copy completion, not just successful scheduling. If required data/residency terms prohibit that location, change the recovery design before accepting the customer. A stricter regional RPO/RTO requires a priced replica/replication design and a new ADR; do not promise it from daily backups.

Restore in isolation; fence old worker epochs and revoke old run tokens; restore DB and referenced objects to a consistent recovery point; validate hashes and incomplete transactions; reapply deletion and revocation records; reconcile provider attempts without blind replay; verify tenant tests; switch serving endpoints; then permit new runs. Record duration and actual recovered point. Recovery objectives describe exceptional incidents, not permission to routinely lose committed work.

Frequency: backup success/lag monitored continuously, small restore smoke monthly, full restore quarterly, failover/restore after material schema/storage changes, and regional drill before GA then at least twice yearly. Choose final frequency based on failure evidence and contractual obligations.

### 13.5 Observability and runbooks

Structured metadata logs carry request_id, run_id, operation_id, attempt/lease epoch, component, version and error class. Keep detailed tenant/run dimensions in logs/traces or usage tables, not unbounded metric labels. Never log credentials, raw prompts, hidden worlds or arbitrary exception locals. Sample traces with error/latency bias and retain required incident evidence privately.

Dashboards: API latency/errors/auth failures; DB connections/locks/storage; queue age/outbox/reconciliation lag; worker startup/resource usage/recovery; per-tenant quota fairness; experiment budget invariants; provider tokens/429/latency/ambiguous spend; evaluator backlog/cost; artifact failures/growth; backup age/restore tests; SLO and deployment correlation.

| Runbook | First response and safe action | Recovery evidence |
| --- | --- | --- |
| Stuck run / expired lease | Inspect authoritative state and epoch; fence old attempt; reconcile; relaunch only missing committed work | No extra logical experiment/debit; visible recovery event |
| DB outage / saturation | Stop accepting work that cannot be committed; cap connections; assess failover/backpressure | Integrity queries, latency and outbox drain |
| Provider outage / ambiguous charge | Open circuit, pause affected calls, preserve attempts; avoid undeclared model fallback | Usage reconciled or visibly unknown; replay known responses |
| Sandbox escape suspicion | Stop new uploads/launches; isolate affected pool, revoke identities, preserve evidence | Security-led containment and reviewed rebuild |
| Evaluator leak / contaminated suite | Quarantine results and access; suspend official scoring; rotate affected suite version | Impact analysis and transparent corrected release |
| Artifact corruption / failed checkpoint | Reject corrupt content; restore valid generation or earlier complete checkpoint | Hash verification and disclosed recovery point |
| Regional outage | Execute isolated restore sequence; communicate incident scope; preserve original state for investigation | Timed RPO/RTO and validation checklist |
| Disk/storage exhaustion | Throttle new builds/uploads; inspect consumers; expand approved capacity or remove verified reproducible data | Free-space/headroom and no lost unique work |
| Bad release / migration | Stop canary/new launches; pin previous images; follow compatible rollback or forward fix | Old-client/worker tests, health and integrity checks |

### 13.6 On-call and incident response

Before pilot: named business-hours primary/backup and clear customer escalation hours; no 24/7 promise. Before GA availability contracts: staffed primary/secondary rotation with at least four trained responders, specialist escalation and explicit compensation/support arrangements. If staffing cannot support this, restrict support terms and do not claim round-the-clock response.

SEV1: suspected cross-tenant/credential/evaluator exposure, corrupted budgets/results or widespread outage; target acknowledgement ≤15 minutes under contracted coverage, incident commander/security escalation, initial customer update ≤60 minutes. SEV2: major degraded execution or tenant-scoped outage; acknowledge ≤30 minutes, updates at agreed cadence. SEV3: noncritical defect; business-hours triage. These are proposed service targets requiring a real roster.

Preserve evidence with restricted access, source identity, incident owner and retention requirement; communicate facts and uncertainty without credentials or customer research. Review notification obligations with appropriate counsel. Hold a blameless incident review within five working days of resolution; assign corrective work with deadlines and verify it. Do not delete unique incident evidence under ordinary cache cleanup.

## 14. Risk register, assumptions and governance

Risk ratings are planning judgments. Review dates are concrete follow-ups for the plan, not scheduled automation. If approval/start is later, revise dates visibly at R0.

| Risk | Severity / likelihood | Mitigation / trigger | Owner | Next review / status |
| --- | --- | --- | --- | --- |
| RK01 Hidden evaluation data reaches agent or customer runtime | Critical / medium | Separate identities/storage, no feedback channel, adversarial tests; suspend scoring on any leak | RS + SE | 2026-10-26; open |
| RK02 Uploaded code escapes or exfiltrates secrets | Critical / medium | Isolated build/runtime, deny egress/DNS/metadata, narrow broker, independent review | PL + SE | 2026-10-26; open |
| RK03 Duplicate retries corrupt budgets or provider accounting | High / high | Transactional reservations/fencing, attempt states and ambiguous-cost reporting | BE | 2026-10-26; local protection only |
| RK04 Unidentifiable worlds / biased benchmark | High / medium | Development identifiability/power study, frozen fair protocol, independent scientific review | RS | 2026-10-26; open |
| RK05 Evaluator/ensemble compute dominates cost and queue time | High / high | Measure complete scoring workload, separate pools, cap/size ensemble before freeze | RS + PL | 2026-10-26; open |
| RK06 Credit, region, organization or quota assumptions fail | High / medium | Explicit account preflight and priced region plan before provisioning | PL | 2026-10-26; unverified |
| RK07 Development VM fills and interrupts work | High / high | 423 MiB free observed; preserve consumers/archives, recover approved safe headroom before builds | PL | Before next build; open |
| RK08 Hiring or fractional security coverage delayed | High / medium | Name owners/capacity at R0; rebaseline rather than compress test gates | Product + TL | 2026-10-26; unassigned |
| RK09 Provider rate/version/retention policies change | High / high | Pin recorded versions, allowlisted adapters, contract review, visible circuit/fallback policy | BE + product | 2026-10-26; open |
| RK10 HA mistaken for disaster recovery | High / medium | Independent backups and timed recovery set; disclose regional 24-hour objective | PL | 2026-10-26; open |
| RK11 SSO/SCIM entitlement assumptions do not match buyers | Medium / medium | Verify federation/mapping/deprovisioning with partners before implementation commitment | Product + BE | R0 review, initially 2026-10-26 |
| RK12 Solo frontend or specialist becomes a bottleneck | Medium / high | Mocks early, limit product breadth, lead/BE support, tenth hire follows evidence | TL | Weekly after W1 |
| RK13 Public repo accidentally contains private evidence | Critical / medium | Secret scanning, scoped publication review, private evidence index; no private account IDs | SE + all owners | Every publication |
| RK14 Indefinite run retention grows cost beyond allowances | Medium / high | Storage metering/quotas, owner retention choice, forecast alerts; no silent deletion | BE + PL | Monthly after pilot |
| RK15 Self-host support expands into every platform | Medium / high | One documented supported deployment matrix, explicit trusted-dev profile, upgrade test | PL + product | R5 design review |
| RK16 False novelty/adoption/compliance claims | High / medium | Related-work review, evidence-based release notes, separate targets from measurements | Product + RS | Every release |
| RK17 Approval or partner readiness slips calendar | Medium / high | Relative schedule, dated next actions, no fabricated pilot milestones | Product | Weekly after approval |

### Governance

- Weekly engineering review: critical path, actual capacity, completed acceptance evidence, failing checks, cost/queue growth, open risks and next integration.
- Architecture checkpoints: R0 contracts, before enabling uploaded code, evaluator integration, before pilot, before GA, and any material trust/data/scale change.
- Research review: development calibration, protocol freeze, exceptions/exclusions, result publication; methodology changes after freeze require a new version.
- Scope change: write the requirement/ADR delta, dependencies, effort and evidence impact; product + lead approve material scope and schedule changes; security/research sign relevant boundaries.
- Technical debt: backlog item with affected invariant, user impact, owner, removal condition and deadline; no permanent unowned “temporary” bypass.
- Release readiness: each gate owner signs evidence and residual risk; unresolved blocking requirement prevents the release.
- Progress reports: update sections 0, 10, 11 and 17 in the implementation PR. Record measured results and next blockers, not activity-only percentages.

## 15. Skeptical review and revisions incorporated

| Challenge | Resulting decision / required evidence |
| --- | --- |
| Is this overbuilt for a three-law simulator? | Keep a small scientific core and modular control plane; isolation, durable state and identity solve actual uploaded-code/private-study requirements. Defer service mesh, event platform, sharding, GPUs and active-active regions. |
| Does “100 concurrent” hide the expensive work? | Define investigations, viewers, builds, provider calls and prediction rollouts separately. Add evaluator expansion math, queue targets and end-to-end profiling before sizing. |
| Can models cheat through the UI or errors? | Explicit visibility classes, post-run truth gate and adversarial schema/event/path/error tests; public and blind claims separate. |
| Does checkpointing guarantee exactly-once effects? | Only logical physics reservations/results are deduplicated; external provider attempts can be ambiguous. Checkpoints do not restore arbitrary memory or prevent every repeated CPU computation. |
| Is a sandbox label enough? | No. Verify runtime enforcement, build isolation, IAM, DNS/network/metadata denial, resource limits and broker authorization in the deployed configuration. |
| Is one region enterprise-ready? | It can serve a bounded single-region product with tested recovery and explicit terms. Regional 24-hour RPO/RTO is disclosed; tighter guarantees require a different design and measured evidence. |
| Does a full team mean a very short calendar? | Nine people still depend on shared schemas, scientific calibration, security integration, partner trials and a 30-day SLO observation. Use bottom-up PR effort, confidence-weighted reserves and a verified resource schedule; current forecast is GA W52–67. |
| Are enterprise requirements being silently invented? | Mark SSO/SCIM, forecast load, SLOs, retention and staffing allocation as proposals; preserve accepted foundation; validate buyer requirements at R0. |
| Could growing history break LLM fairness/cost? | Fixed disclosed context transform and token ceiling; log truncation and retries; equal experiment budget is not equal compute. |
| Are self-hosting and hosted isolation inconsistent? | Document one supported secure deployment and a separately labeled trusted development profile. External install/upgrade evidence is required. |
| Can diagnostics/retention create security and cost debt? | Separate research artifacts from logs/backups; scoped access, deletion tombstones, archive review dates and tested retention. |
| Can a single file stay maintainable? | Stable IDs and section mapping, one progress ledger, links to existing detailed implementation references. The execution-planning request now adds one detailed backlog and a matching machine ledger; keep the roadmap strategic and synchronize IDs/progress. |

Remaining unproven assumptions are gates, not concealed conclusions: buyer adoption, generalization usefulness, uncertainty calibration, provider economics, cloud credit terms, hostile-code isolation, true load capacity, restore timings and actual staffing. No research win, deployment or compliance outcome is asserted.

## 16. Requested artifact coverage and launch checklist

The requested artifact paths are represented by useful sections in this single file, as requested. Do not generate duplicate empty documents. Existing domain-specific files remain linked references.

| Requested artifact | Authoritative content here |
| --- | --- |
| docs/product/PRD.md | Sections 1–2 |
| docs/product/USER_STORIES.md | Sections 1.4 and 2 |
| docs/architecture/SYSTEM_OVERVIEW.md | Section 4 |
| docs/architecture/SCALABILITY.md | Section 7 |
| docs/architecture/DATA_MODEL.md | Section 6 |
| docs/architecture/API_CONTRACTS.md | Section 5 |
| docs/architecture/adr/ | Section 4.4, ADR01–ADR14 |
| docs/security/THREAT_MODEL.md | Sections 8.1–8.2 |
| docs/security/SECURITY_REQUIREMENTS.md | Sections 8.2–8.4 and REQ06/13/14 |
| docs/quality/TEST_STRATEGY.md | Section 9 |
| docs/operations/OBSERVABILITY.md | Sections 13.3 and 13.5 |
| docs/operations/INCIDENT_RESPONSE.md | Sections 13.5–13.6 |
| docs/operations/DISASTER_RECOVERY.md | Section 13.4 |
| docs/roadmap/ROADMAP.md | Sections 10–11 |
| docs/roadmap/DELIVERY_SCHEDULE.md | Sections 10 and 12.3–12.4 |
| docs/roadmap/DEPENDENCY_GRAPH.md | Section 10 graph and section 11 explicit dependencies |
| docs/team/OWNERSHIP.md | Section 12.1 |
| docs/REQUIREMENTS_TRACEABILITY.md | REQ01–REQ16 in section 2 → SP tasks → V01–V12 evidence |
| docs/RISKS_AND_ASSUMPTIONS.md | Sections 1.3 and 14 |
| docs/DEFINITION_OF_DONE.md | Sections 9.2–9.3 and milestone exits |
| Prioritized engineering backlog / issue-ready Markdown | EXECUTION_BACKLOG.md plus execution-backlog.json; section 11 maps 168 PR tasks to 42 linked epic issues |
| CI/CD implementation plan | Sections 11 SP-27 and 13.1–13.2 |
| Initial risk register | RK01–RK17 in section 14 |
| Launch readiness checklist | Below |

### Launch gate

- [x] Local baseline inspected at its source commit and cloud checks rerun.
- [x] Current scope and limits distinguished from planned enterprise capabilities.
- [x] Single roadmap includes requirements, architecture, contracts, security, capacity, delivery, ownership and evidence model.
- [x] Product owner approves expanded plan and provisional targets; current lead/three-engineer execution mode recorded. Human operational staffing remains unconfirmed.
- [ ] Named staff, cloud preflight, safe workspace headroom and design partners established.
- [ ] Baseline and new work reviewed/merged; released package/API/client versions identified.
- [ ] R1 scientific validity and both-track protocol gates passed; no hidden feedback.
- [ ] R2/R3 private multi-tenant control plane and uploaded-code isolation passed.
- [ ] R4 durable model/provider/predictor integration and cost controls passed.
- [ ] R5 complete browser/SDK/CLI/export/self-hosting journeys passed.
- [ ] R6 adversarial, failure, load, restore, migration and deletion evidence passed.
- [ ] R7 partner adoption and full scored reference publication verified.
- [ ] Enterprise SSO/deprovisioning/service identities/audit controls verified.
- [ ] Independent security findings resolved or accepted within release policy.
- [ ] RPO/RTO drills, on-call coverage, rollback and 30-day SLO record complete.
- [ ] Capacity/cost/support boundaries and customer data terms published accurately.
- [ ] Release manifest, evidence owners, retention and post-launch review dates recorded.

## 17. Decision/progress log and approval handoff

| Date | Change / decision | Evidence / next action |
| --- | --- | --- |
| 2026-10-06 | Local research core implemented on feature branch | Commit 428b5a6; PR #1 CI passed; not merged |
| 2026-10-19 | Reinspected authoritative cloud repository and existing PR | Clean baseline, same commit; no hosted service in repository |
| 2026-10-19 | User selected a larger team of 7–10 engineers | Nine-engineer reference allocation; actual people and start date pending |
| 2026-10-19 | Reran local-core verification in cloud | 55 tests; Ruff lint/format; strict mypy passed; these do not test future hosted features |
| 2026-10-19 | Validated roadmap structure and effort | 42 work packages sum to 118 PW; dependencies checked for cycles; local links, section references and Markdown structure checked |
| 2026-10-19 | Adopted staged delivery and published engineering work | Stage 2 issue preparation authorized; 42 work packages, nine milestone gates and 112 native dependency relationships created and read-back verified; implementation approval remains pending |
| 2026-10-19 | Drafted initial contracts | Exported current schemas and validated proposed HTTP/research definitions and fixtures; complete interface freeze remains SP-01 |
| 2026-10-19 | Created original consolidated enterprise roadmap | Historical estimate: 118 PW +25%, pilot W19–22/GA W30–36; superseded by execution audit below |
| 2026-10-19 | Audited and split execution backlog | 168 PR tasks/42 epics, 368 prerequisites; reference forecasts validated; subsequently approved below |
| 2026-10-19 | Approved execution and dispatched independent engineers | SP-00.a complete for amended roster; Quality/Research baseline reviews pass, factual doc repairs in 9833e6f; Platform preflight complete with deployment NO-GO; SP-02.b pending exact disk/snapshot approval. See EXECUTION_LOG.md |
| 2026-10-19 | Integrated reviewed baseline | SP-00.b complete: PR #1 merged as 7117060; tree matches reviewed 5cb1895, with four passing CI checks and both peer review scopes |
| 2026-10-19 | Repaired DB-to-artifact freeze dependency | SP-01.b now precedes SP-01.c freeze; 369 edges, both reference schedules regenerated. R0 W6–7, spring W11–13 and R1 W18–26; GA W52–67 unchanged. Effort and current execution staffing unchanged |
| 2026-10-19 | SCI subset independently accepted, integration pending | Research authored; Quality found three schema/grid defects and verified repairs at 8c86e76. No fitter or benchmark claim. Platform prepared unapproved staging cost and seven workspace journeys; Research reviews truth boundaries |
| 2026-10-19 | Integrated SCI; accepted bounded control subset | PR #51 merge cc24aef passed CI. Control part 1 a9fa8cb passed 252 tests and independent review after four fixes. SP-01.b remains partial; remaining identity interfaces require separate PRs and estimate review before dependent work |
| 2026-10-20 00:04 UTC | Continued review and CI/CD reassignment | Control PR #53 integrated with matching CI. Journeys/staging proposal documented but product/provisioning approval remains pending. Quality assigned CI-01; identity authoring queued; branch settings remain with separate coordinator |
| 2026-10-20 00:23 UTC | CI delivery verified; identity work reassigned | PR #56/main 256b409 delivered artifact 12231636153 with independent checksum/source review. Durable evidence recorded; Research assigned ID-A/#57. Cloud capacity and concrete provisioning approvals remain open |
| 2026-10-20 00:42 UTC | ID-A integrated; next engineer assignment | PR #65/main cc576da matches reviewed 34d26d9; 413 tests and required PR/main CI pass. Platform assigned ID-B/B1; Research/Quality review. B2/B3 and ID-C remain separate dependent units |
| 2026-10-20 00:57 UTC | B1 integrated; invitation work assigned next | PR #67/main 1ec45aa matches reviewed b9c4754; 474 tests and required PR CI pass. Platform prepares B2 invitations; Research/Quality review. Full identity and infrastructure gates remain open |
| 2026-10-20 01:12 UTC | B2 integrated; capacity stop | PR #69/main 89e6117 matches reviewed 8267865; 560 tests and PR/main CI passed. Platform assigned B3, blocked on capacity; Quality follows with ID-C. Cloud writes stopped below 100 MiB; the >=20 GiB gate and disk/snapshot approval remain open. Working checkout is preserved; see EXECUTION_LOG.md for resumption steps |
| 2026-10-20 02:25 UTC | Calibration accepted locally; parallel authoring enabled | SP-03.b 43e0589 independently reviewed with 817 tests; exact-head CI remains before integration. Research prepares SP-04.a; Platform owns B3 in a separate cloud checkout with independent dependencies. No production fit/predict/score or noisy accuracy claim |
| 2026-10-20 02:29 UTC | Calibration integrated; production fitter assigned | PR #78/main db182788/tree08efb975 matches reviewed7b27bad; PR CI39358928012 and main CI39359050024 passed. Research owns SP-04.a, Platform repairs B3 review findings, Quality independently reviews both |
| 2026-10-20 02:31 UTC | Linking independently accepted; credential preparation assigned | Source051d8f7 passed branch checks and three reviews; lead integrates with current scientific progress before exact-head CI. Quality prepares ID-C, Research authors fitter, Platform reviews fitter. Current stream authority applies before every payload batch; 30 seconds is idle-only |
| 2026-10-20 02:39 UTC | B3 integrated; C1 credential work assigned | PR #79/main24c8796 has matching reviewed tree and passing PR/main CI; 918 tests. Quality reuses identity checkout; Research continues fitter, Platform reviews. Remaining ID-C effort provisionally6–11 human engineer-days, not agent wall time |

**Capacity decision, 2026-10-20:** the product owner approved the concrete 200→300 GiB boot-disk expansion and recovery snapshot, estimated at ~$10/month incremental disk plus up to ~$10/month snapshot before credits/tax. The action is complete and independently accepted; actual billing remains unmeasured. This approval does not cover staging, model-provider trials or release actions.

**Approval scope:** execution backlog D01–D06 and initial R0/spring scope approved on 2026-10-19. Current execution uses a lead and up to three engineer subagents; the nine-human-team schedule remains conditional. No arbitrary paid benchmark sweep, compliance claim or unlimited infrastructure spend is implied. Cloud provisioning remains tied to concrete priced configuration, verified account permissions and applicable release/approval controls.

**Next executable outcomes:** [RA-02/#105](https://github.com/spei04/strange-physics/issues/105) manifest/accounting contracts and [RA-N01/#106](https://github.com/spei04/strange-physics/issues/106) native prediction/scoring. Both start after accepted RA-01 and SP-04.e, with independent review before integration. The finite-grid reference joins them next; Laplace follows the first comparison and consumes frozen disjoint audit fixtures.

Historical research planning acceptance (2026-10-20): PR #86/main e239eb2c704cd315aadd6064cdb521d1a6d9bbdc matches reviewedc48517b/tree558d68ed; PR CI39365953740 and all main CI39366138629 jobs passed. At that publication the18-task extension was planning-only. Scoped native RA_EXEC is now accepted under the2026-10-21 decision; paid/sizing/official gates remain pending.

Identity integration acceptance: PR #88/main 92320173ff0d3278c65cfc251983d57fab9960b1 matches accepted b8d3e5ee96b3b07da53eccbabddebc5a73223ba3 and tree 515e27ebbb594a15ce439b24a14463ed7a4cf9a7; PR CI39367180231 and all protected-main CI39367439199 jobs passed. Integrated 1,692 tests, Ruff/format92, strict mypy57,613 schema checks, configured security checks and offline package validation passed. SP-01.c began after this parent gate; local SDK/CLI I1 is now complete through PR #90.

I1 integration acceptance: PR #90/main d9311584ea7d719770013f4d41bcd31dc48485a9 matches accepted 8336ca54ebb8d8c4a413765869d886a1ad81152c and tree e3198a560331d2d7688a00668f3b943f4471f358; PR CI39368869540 and all five protected-main CI39369037416 jobs passed. Installed-wheel SDK and CLI each retain all24 preregistered probes with no failures and every probe under0.001 RMSE. SP-04.e is complete; the broader sparse-fitting epic, R1, hosted product and production-readiness gates remain open. ART1 persistence/restore findings are resolved and integrated through PR #91; EXEC1 runtimefe3b008 is integrated through PR #92 with passing exact PR/main checks.

ART1 review checkpoint: accepted runtime29a968b/author7a90e96 and combined5ad0ef3 preserve frozen CORE/SCI bytes. Independent reviews resolved persistence and restore findings;1,954 combined tests,669 schemas,static/security checks and exact36-entry archives passed. Exact PR/main acceptance is complete through PR #91. EXEC1 runtimefe3b008 is integrated; COMP1 remains. This is a bounded contract subset; full SP-01.c and real hosted enforcement remain unfinished.

ART1 integration acceptance: PR #91/main95bdd85e6163147b6b1e29e6f59648a02e8c3d59 matches reviewed8c282eb2072e59c43290ea10991e09adc990d5b6 and treecb539fa21f89ffc5562a66f2c1fa42cb5acdec07; PR CI39370833204 and all five protected-main CI39370975462 jobs passed. The existing identity checkout is reused for Platform’s EXEC1 API assignment after reviewed handoff. Pure package/worker contracts do not establish actual builds, hostile-code isolation, transactional producers or hosted readiness; full SP-01.c remains open through EXEC1 and COMP1.

EXEC1 API acceptance: lead, Quality and Research accepted57f2f303a5fec4b65b1df022b4239a64f537f6bc/treeecd3facfcd1f3e5086ef3fca9c30a4c29f8a0b3a. All137 focused cases and722 external schema cases pass; independent reviewers added15 lead,10 Quality and19 Research cases. Review repaired impossible approval/launch/fence chronology, explicit normal-completion reasons, keyed unique-attempt lookup obligations and aggregate configuration allocation bounds. The subsequent runtimefe3b008 is integrated through PR #92; actual hosted producers and full SP-01.c remain open.

Production scaling requirement from EXEC1 review: a measured1,757,976-byte maximum-shape Operation implies about16.37GiB for10,000 operations. This is a one-object measurement and extrapolation, not a load test. SP-09.d/SP-13.c/SP-16.b must provide bounded authoritative metadata/body-hash reads and a reviewed internal committed-prefix projection; SP-12.a must enforce cumulative allowances. The current full-Operation validator remains a conformance reference. COMP1 must bind exact SCI prefix identity with explicit input byte limits or verified streaming validation. These requirements are in the existing backlog leaves and do not establish hosted performance or change the reference schedule.

Historical EXEC1 integration preparation (completed by the acceptance below): EXEC1 runtime fe3b0088d4bca0623459f9024eceb42036e8d491 and doc-only author c66b6a0d6bc82a81195797c742353718bc155136 are independently accepted. All2,281 tests,615 focused cases,722 schemas,Ruff/format112,full mypy74,configured Bandit and offline archive checks passed. Three related lifecycle/history defects were repaired; Quality independently checked84 state/instance combinations,65 receipt histories and6 chronology cases. Research and lead each passed12 additional cases. Pure predicates remain distinct from live producers. Final PR #92 and protected-main checks are pending; COMP1 and full SP-01.c remain open.

EXEC1 completion and next assignment: EXEC1 is complete through PR #92/main750db15810f4a58a4a8d34776cb3708dc310ef5a, matching reviewed671f10930a743acfb9da888a0eb2c97c6e7f471f/tree13894d9c09bdde0ae8278a5a331c56b377a485fc. All four PR CI39375391014 and all five main CI39375611645 jobs passed. Local2,281 tests,722 schemas,full typing/static/security/package checks and independent lifecycle/provenance review are accepted. The verified candidate artifact12242708007 is retained privately outside checkouts; this is not a published release or live hosted readiness claim. Research starts COMP1 API authoring after reviewed handoff; Platform/Quality review and lead integrates. Mandatory current worker broker authority, separate native analytic approval, actual original run/engine and bounded SCI prefix identity are required. The full SP-01.c gate remains open.

COMP1 API checkpoint: accepted21cb201/tree d3e0b341 after replacement-worker revision ordering and actual PredictorVersion integration repairs.422 focused cases,764 schemas,Ruff/format115 and mypy76 passed, with independent review and guard-mutation checks. Research now authors runtime; Platform reviews byte/prefix/native approval and Quality current authority/recovery. Exact runtime and integration evidence are still required before the SP-01.c freeze; the bounded interfaces do not establish hosted production readiness. The assignment and evidence log is in EXECUTION_LOG.md.

Draft COMP1 API CI: PR #93/a629729 passed all four applicable CI39377520114 jobs, preserving accepted API21cb201 and reviewed progress. Runtime and full SP-01.c acceptance remain pending; this is early API evidence, not final runtime or hosted-production evidence.

COMP1 runtime integration checkpoint: runtimeb7c944c and finalauthor3ceb846 are independently accepted.2,423 tests,141 focused COMP1 cases,764 schemas,static/type/security/offline package checks passed; independent authorization, prefix, renewal and recovery reviews are recorded in EXECUTION_LOG.md. Combined60a8ac5 preserves accepted source and status annotations. Lead integrates through draft PR #93; exact final PR/main CI remains before SP-01.c completion. Research/Platform prepare SP-01.d read-only; source waits the accepted parent and writer handoff. Hosted production and paid/release gates remain open.

Final integrated60a8ac581fcfed2df9f9381ce116b6d905064242 checks passed2,423 tests,Ruff/format117,mypy78 and764 external schema cases. The private integrated-check index SHA256989c28e24c32236165b6351f1c031a5d7385d188921d55816e2a69c1318e0100 binds the immutable source and captured results; subsequent changes are progress-only. Exact final PR #93 and protected-main CI remain before merge/parent acceptance.

COMP1 completion and SP-01.d handoff: COMP1 and SP-01.c are complete through PR #93/main11e200253347dc05973e5d7969a3abd145f285e2, matching revieweda75ac1b7099aa8d38d62577d14315dfeb5009f49/treeec01b963f20e95f682ef06a04bcebcd4350db862. All four PR CI39379345399 and all five protected-main CI39379544409 jobs passed. The exact integrated source passed 2,423 tests, 764 schema cases, Ruff/format and strict typing; independent boundary, recovery and composition reviews are accepted. Candidate artifact12245465046 was checksum/provenance verified and retained privately outside checkouts. These are pure contracts and predicates; live SQL/storage/HTTP/build/controller/isolation producers remain later tasks.

Research is assigned SP-01.d/#94 in the existing identity checkout after this record is reviewed and the lead explicitly hands off the writer. WORLD1 covers immutable world/version views, browser-only current authorization, explicit preview grants and exact selected-world/run binding. WEB1 follows in a separate PR for streams, snapshots, cursors, replay and large-artifact retrieval. Each unit requires an API/fixture checkpoint before pure runtime predicates. Platform reviews preview/provenance and producer boundaries; Quality reviews authority/recovery/schema consistency and retains read-only SP-01.e preparation. Lead owns primary integration and progress. No dependency, estimate, paid, research-amendment or release gate changes.

WORLD1 source assignment started 2026-10-20 06:23 UTC at acceptedc74975b after exact SP-01.c integration and independent handoff review. Research authors the API first; Platform/Quality review and lead integrates. WEB1 and SP-01.e remain pending.

WORLD1 API fd6bac2 is independently accepted with 2,600 tests and 1,201 external schema checks. Research is assigned runtime; Platform reviews transition/provenance and Quality current authority/recovery. The accepted types do not establish live storage, HTTP or UI, and SP-01.d remains open through WORLD1 runtime and WEB1.

WORLD1 draft PR #95/API integration 0b31f6a passed all four applicable CI39384486351 jobs. Runtime and final integration remain pending. Bounded WEB1 preparation supports the 4 MiB body cap and establishes cross-language identity fixtures as a required client check; details and limitations are in EXECUTION_LOG.md.

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

## 2026-10-26 — First measured purchase checkpoint accepted

Source 2c43f97 is accepted and published for the first-purchase and bounded recovery checkpoint, including qualified failure/replay evidence. The five selected 075c733 cases and retained bounded full path are independently accepted, with repeated-action calibration/menu limitations. PR124/main dfda60f is delivered: all five jobs in run 40277055513 and exact unpublished candidate 12630997569 are accepted. Next is retained comparison preparation/prediction/scoring binding, then publisher handoff; implementation is unassigned. V3, cumulative caps and parent issues #105/#106 are unchanged. [Evidence and assignments](EXECUTION_LOG.md#2026-10-26--first-measured-purchase-checkpoint-accepted).


## 2026-10-27 — Retained-Journal comparison bindings assigned

Quality owns the existing identity checkout for strict retained-Journal preparation/prediction/scoring contracts and bindings, with independent Platform and Research review. The capacity/consumer audit supports lightweight work; the first immutable source checkpoint and complete finite resource profile precede measured runtime. Failed rows, exact identities, cumulative holds and paid recovery are required. Publisher handoff and full-study admission remain separate; no caps, graph or grid/Laplace sequence changed. [Assignment and next gate](EXECUTION_LOG.md#2026-10-27--retained-journal-comparison-bindings-assigned).


## 2026-10-27 — Pure comparison bindings accepted

Pure payloads and material bindings at bdfed5d are independently accepted and published. The exact-source addendum passed 19 pure tests in 23.14 seconds; 88 source/package/installed files match. The initial test-inventory gap is preserved and closed by that addendum. Quality is implementing the measured supervisor adapter, with Platform and Research reviewing the next immutable source and concrete resource profile before measured calls. This is not actual Journal authority, numerical comparison or parent completion. Caps, graph and grid-first/Laplace-later sequencing remain unchanged. [Evidence and assignments](EXECUTION_LOG.md#2026-10-27--pure-comparison-bindings-accepted).


## 2026-10-27 — Comparison adapter source reviewed

Independent reviews found no static blocker in c427d39. Research delivered the source-only 45-call fixture at 4a5c84a; Quality is integrating it and implementing the explicit 50-call sequence for successful scoring and recovery after a missing prediction is retried. Its proposed bounds are 1,066,811,392 bytes and 1,338 CPU seconds under unchanged caps, conditional on smaller copy bounds and actual store fit. No measured runtime is admitted or observed. Lead owns progress in released primary; Quality retains identity. [Evidence and assignments](EXECUTION_LOG.md#2026-10-27--comparison-adapter-source-reviewed).


## 2026-10-27 — Comparison runtime repair

The first bounded integration attempt returned from 39 calls, then stopped during retained-history validation before the first score ran. Its original cost holds and failure evidence are preserved. Quality is removing repeated ledger validation and making the next fixture's overall lifetime explicit; per-call and scientific caps remain unchanged. The independently reviewed four-call boundary fixture is ready for integration. Repaired source/profile review is required before another measured attempt. [Evidence and assignments](EXECUTION_LOG.md#2026-10-27--first-comparison-run-exposed-validation-cost).

## 2026-10-27 — Retained comparison delivered; publisher handoff next

Source 36c9595 passed 20 synthetic checks, the 50-call successor and the separate four-call boundary fixture. Both peers and Lead accepted the bounded 50-call evidence, and Platform/Lead accepted the separate boundary fixture. The full suite stopped at 1,041 passed/one failed with SIGPROF during candidate installation verification before producer dispatch. Lead/Platform accepted repair 50b1118; formatting-only successor 336d91b passed 16 focused cases in 17.29 seconds. Its subsequent full run stopped at 1,061 passed/one failed during prediction-ingress installation verification. Sealed evidence preserves eight closures and setup/control holds, with no new prediction reservation. The read-only mirror completed in 3.03 CPU seconds; two bounded 30-call diagnostics passed in 88.46/91.76 seconds, the latter retaining full collection without preceding test execution. Neither reproduced the timeout or established its cause. The subsequent normal full-suite observation stopped at 2,389 passed/one failed during paid original-score replay; all 33 watched calls passed. Retained score material matches; a source-proven deadline-masking path and four-second work cost support an expiry inference, without a recorded signal. Deadline propagation is now accepted at 97f4d55 with source-qualified 13+4 focused passes. A read-only computational replay validated the retained score and identified repeated canonical traversal; its profiled timing does not prove four-second fit. Same-invocation parsed-input reuse is now accepted at 1dee2c5: 29 focused cases and one actual 50-call specimen passed, with 103 records, 43 closures and four unresolved holds. The replay result is a single-run observation, not a timing guarantee. Exact 1cc9408 now passed all 15 local configured checks, including 4,421 tests in 1,850.02 seconds in normal complete order. Original and historical score replays returned in the full-context trace; passing physical fixtures were removed under the approved failed-only policy, so selected-run measurements remain separate. PR127/main 5897f97 and unpublished candidate 12715816385 are accepted after all five main jobs passed, with 4,421 tests on each Python runtime. Quality is assigned the V2 publication-authority handoff; its design is accepted but resource fit and crash recovery remain unproved. Parents #105/#106 and full-study admission remain open. The failed first attempt, unknown costs and fixed-selection conformance limits are preserved. [Current delivery and qualifications](EXECUTION_LOG.md#2026-10-27--retained-comparison-delivery-accepted).

## 2026-10-27 — Handoff checkpoints accepted; full-study boundary clarified

The source-seal/store checkpoint 0336b5f passed 26 tests; original diagnostic-input checkpoint 95e9621 has a qualified 30-case pass (pytest exit 0 and 30 passing markers, preserved quiet-output reporting assertion, no retry). Each tested package matches its exact 90-file source and archives; dependency identities stayed unchanged. Quality continues the measured caller/activation, while Research prepares the separate 44-call actual handoff fixture. These checkpoints do not prove measured handoff, full-study feasibility or parent completion.

Full-study review found separate lower bounds above the existing 1 GiB authority and a missing multi-cell coordination boundary: the single-cell/three-ticket seal cannot serve all 36 cells by repetition. Before parent closure, make the bounded authority interface, one global budget, current limitations and later integration ownership explicit. Exact algorithm census and measured full-study fit belong after inference/policies exist and before RA-07.b admission; they are not circular prerequisites for implementing RA-N02.a/RA-N04. No graph, estimates, caps, experiment count or Laplace sequence changed. See the [assignment log and evidence](EXECUTION_LOG.md#2026-10-27--publisher-handoff-checkpoints-and-study-boundary).

## 2026-10-27 — Handoff caller checked; integration verification in progress

Caller/activation source 6d42df9 passed 22 primitive tests, then the separately reviewed 44-call specimen passed in 240.21 seconds. Independent readback accepted all 44 returns, the complete sealed source prefix, original publication/replay bytes and three retained cost holds. Passing evidence is retained. This is one-cell conformance with fixed selection, not a research comparison or a timing guarantee.

The test-only ca9ee869 supplement is source-reviewed; its two-case/four-call runtime is pending. Research prepares that bounded runner, Quality prepares final static/schema/security/package checks, Platform reviews evidence and Lead updates progress. Both existing cloud checkouts are reused. Hosted full suites, PR/main/candidate delivery and the explicit parent audit remain pending; #105/#106 stay open. Global 36-cell authority/capacity and the grid-first/Laplace-later sequence are unchanged.

[Evidence and assignments](EXECUTION_LOG.md#2026-10-27--handoff-caller-checked-integration-verification-in-progress).


## 2026-10-27 — Handoff recovery checked; final delivery pending

Caller recovery now has passing evidence across two source-specific runs: the unknown/protected-retry case passed at ca9ee869, and the corrected lost-acknowledgement case passed at 1b43838 in 14.14 seconds. The initial four-call run remains recorded as one pass and one test-assertion failure; it is not relabelled a complete pass. Production package bytes are unchanged. The public handoff API and supported recovery limits are documented.

Quality owns the final ten local static/schema/security/package checks and candidate verification; Platform reviews the final evidence and progress; Research has completed the targeted caller cases; Lead owns source composition and GitHub delivery. Hosted full suites on Python 3.12/3.14, PR/main/candidate verification and explicit parent acceptance remain pending. Parents #105/#106 stay open. Full-study authority/capacity, global caps and grid-first/Laplace-later sequencing are unchanged.

[Evidence and assignments](EXECUTION_LOG.md#2026-10-27--handoff-recovery-checked-final-delivery-pending).
