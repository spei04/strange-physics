# Strange Physics — enterprise product blueprint and living roadmap

**Document owner:** product owner and engineering lead
**Last verified:** 2026-10-19
**Repository:** [spei04/strange-physics](https://github.com/spei04/strange-physics)
**Status:** Stage 2 work packages published and initial contract drafts validated; expanded assumptions, contract freeze and first implementation slice await approval.
**Implementation baseline:** 428b5a698b6f5654a9b91f547c9d4e7c196d3aa9, on feat/research-core; [PR #1](https://github.com/spei04/strange-physics/pull/1) is open, not merged.

This is the single maintained enterprise roadmap, requirements register, execution backlog, and progress record. It fills the requested engineering-blueprint template in one file. Existing [accepted decisions](DESIGN_DECISIONS.md), [core contracts](CORE.md), [law definitions](LAWS.md), and [draft benchmark](BENCHMARK.md) remain useful detailed references. This document proposes an expanded release schedule; it does not retroactively approve new scope, change scientific settings, or claim deployed controls. If approved, its R0–R8 schedule supersedes the older M0–M5 schedule; section 10 maps the two.

No broad implementation, new infrastructure, paid sweep, or compliance certification is performed by creating this plan. Previously approved architecture remains accepted. New enterprise gates and quantitative assumptions below are proposals until approved or measured.

**Navigate:** [Progress](#0-progress-evidence-and-how-to-maintain-this-file) · [Product](#1-product-definition-and-planning-assumptions) · [Architecture](#4-architecture-and-trust-boundaries) · [Capacity and cost](#7-capacity-performance-and-cost-model) · [Security](#8-security-requirements-and-threat-model) · [Milestones](#10-dependency-aware-milestones-and-exit-gates) · [Backlog](#11-prioritized-issue-ready-engineering-backlog) · [Team and schedule](#12-team-ownership-and-delivery-schedule) · [Operations](#13-cicd-deployment-reliability-and-operations) · [Approval](#17-decisionprogress-log-and-approval-handoff)

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

| Work item | Status on 2026-10-19 | Evidence / remaining gate |
| --- | --- | --- |
| Personal public repository and established architecture | Verified | Repository is spei04/strange-physics; accepted decisions recorded in DESIGN_DECISIONS.md |
| Three force families, 2D, 1–8 particles, public contracts, SDK and CLI | Verified on feature branch | Baseline commit above; src/strange_physics and numerical/contract tests |
| Local transactional reservations, checkpoints, replay after interruption | Verified locally | journal.py, session.py, sdk.py; failure and concurrency tests; not distributed durability |
| External custom agent and law example | Verified locally | examples/custom_extension.py and tests/test_extensions.py; not outside-team adoption |
| Current code checks in cloud checkout | Verified | 55 tests passed in 10.29 seconds; Ruff lint/format passed; strict mypy passed for 19 source files on 2026-10-19 |
| Existing GitHub CI | Verified at baseline commit | Python 3.12 and 3.14 checks succeeded on PR and push; [CI run](https://github.com/spei04/strange-physics/actions/runs/37415951979), completed 2026-10-06 |
| Baseline integration to main | Planned | PR #1 still open; passing checks do not mean merged or released |
| Stage 2 engineering work packages | Prepared; implementation pending approval | 42 detailed issues, nine milestones and 112 native GitHub blocking relationships verified by read-back; tests, telemetry and exit evidence specified |
| Initial contract pack | Draft; validation passed | Four JSON artifacts with exported core definitions, 11 proposed HTTP operations, research messages and synthetic fixtures; SP-01 freeze remains open |
| Expanded enterprise blueprint | Awaiting approval | This document, including issue-ready work packages, staffing, capacity assumptions and exit gates |
| Shared fitter, active selector, calibrated uncertainty, held-out scoring | Planned | R1; the current random agent does not learn a predictive model |
| Authenticated HTTP service, tenant database, remote execution | Planned | R2–R3; local SQLite is not a hosted security boundary |
| Provider gateway, LLM selector, executable predictor evaluation | Planned | R4; no provider sweep or live model calls established |
| Browser world builder, investigation viewer, supported self-hosting | Planned | R5 |
| Load, adversarial, restore, migration and outside-team validation | Planned | R6–R8 |
| Production infrastructure and actual credit eligibility | Unverified / planned | No product deployment appears in this repository; this review did not inventory the cloud account |
| Development workspace capacity | At risk | Cloud root filesystem: 193 GB total, about 538 MB free at inspection; resolve before dependency or image builds |

The cloud development VM is an existing workspace, not the hosted product deployment. Authoritative source is studio-agent:/home/serenapei/experiments/strange-physics. Reuse it; do not recreate the project or dependencies on the Mac. Its single Git checkout is retained for ongoing work. Existing migration archives and other experiments are not disposable build caches.

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

The staged workflow was requested on 2026-10-19. Preparing issues/contracts is authorized; the expanded plan's assumptions and the first implementation slice still require approval.

| Stage | Deliverable and gate | Current state |
| --- | --- | --- |
| 1 — Plan and challenge | Inspect actual code, compare options, expose assumptions, challenge risks; product owner reviews assumptions before implementation approval | Blueprint and challenge review prepared; A01–A09 and expanded targets await approval |
| 2 — Turn the plan into engineering work | Detailed work packages, GitHub issues/milestones/dependencies, draft API/schema fixtures, tests and milestone exits; review contracts before freezing | 42 work packages, nine milestones and 112 dependency relationships published and verified; initial contract pack drafted and validated; SP-01 freeze remains open |
| 3 — Implement one vertical slice at a time | Start only an approved slice; require tests, review, telemetry and updated documentation; then assess its evidence before selecting the next | Not started for the expanded roadmap |
| 4 — Validate actual production readiness | Audit shipped implementation against REQ01–REQ16 using real test/load/security/deploy/restore evidence; block unsupported claims | Not started; R6–R8 own these gates |

The roadmap remains the single planning/progress Markdown document. GitHub issues hold actionable work packages; machine-readable JSON files hold contract drafts. Creating an issue, schema or milestone never marks its implementation complete. Issue blockers describe completion/integration prerequisites; mock work may start after its explicitly approved interface boundary.

### 0.5 Proposed first implementation slice: fit, predict, score one spring system

**Approval item:** [SP-00](https://github.com/spei04/strange-physics/issues/2). **Delivery scope:** a bounded subset of [SP-03](https://github.com/spei04/strange-physics/issues/5), [SP-04](https://github.com/spei04/strange-physics/issues/6) and [SP-06](https://github.com/spei04/strange-physics/issues/8); its effort is included in those packages, not an added milestone.

A researcher exports purchased observations, fits a shared linear-spring coefficient, saves a typed model, predicts an unseen initial condition and receives an independently computed development report. This exercises the scientific architecture through a usable SDK/CLI path before adding more methods or hosted components.

1. Read existing validated observation exports; pass only public structure and purchased trajectories into the fitter.
2. Fit the noiseless one-particle/fixed-anchor linear-spring fixture using integrated velocity increments; preserve masses and declared units.
3. Save the draft model artifact with observation/config hashes and training prefix; implement prediction from the draft request/response contract.
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
| A02 | No launch date or signed customer SLA supplied | Relative weeks from approval and staffing; pilot W19–22, enterprise GA W30–36; not a commitment | Product, R0 |
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
| Observe results | GET /runs/{r}/experiments and /operations/{op} | Purchased observations only; cursor pagination |
| Save checkpoint | PUT /runs/{r}/checkpoints/{index} | Schema/runtime/hash validation; immutable at an index; complete prefix only |
| Submit predictor | POST /runs/{r}/models | Immutable image/model references; no evaluator score returned |
| Model request | POST /runs/{r}/model-calls | Scoped gateway operation ID and pending/completed/ambiguous state |
| Events / replay | GET /workspaces/{w}/runs/{r}/events and /replay | Authorized SSE cursor or bounded replay chunks |
| Export / publish / delete | POST .../{r}/exports, /publications; DELETE .../{r} | Explicit owner intent; async operation; sanitized publication manifest |
| Usage / audit | GET /workspaces/{w}/usage and /audit | Authorized summaries and cursor export; no raw credentials |

Use OpenAPI 3.1 with stable operation IDs, generated TS client and Python remote adapter. R0/SP-01 freezes request/response/error schemas and examples before parallel backend/frontend implementation. Clients must tolerate declared optional fields and known versioning rules, not unknown experiment fields that the existing strict contracts reject.

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
| [Draft research messages](../contracts/draft/research.schema.json) | Five named definitions for artifact references, the first linear-spring model, prediction requests/responses and development reports. Schema versions explicitly include draft status. |
| [Contract examples](../contracts/examples.json) | Synthetic positive, negative and runtime-only validation fixtures; they are not benchmark results. Validate instances against the named definition, not the schema-library root. |

Validation performed during Stage 2: JSON Schema 2020-12 definition checks; resolution of local/external references; official OpenAPI 3.1 structural meta-schema; unique operation IDs, required path parameters, mutation idempotency headers and nonempty security requirements; nine positive and three negative example validations, plus two documented runtime-only cases. Exported core definitions were compared with current Pydantic schemas, and the existing runtime rejected the missing-impulse-target fixture. The cloud machine's existing system jsonschema 4.10.3 package was used, without installing dependencies or adding a runtime dependency. [OpenAPI schema source](https://spec.openapis.org/oas/3.1/schema/2022-10-07), SHA-256 da01ba28852cac0de53893797cb8d1942bc3b05084f526dcc216717dec314ed0.

JSON Schema does not implement cross-field scientific or security behavior. Runtime obligations include graph identities, impulse targets, increasing/aligned timestamps, particle/mass matching, finite numerical results, checkpoint size/prefix/runtime consistency, quota transactions, tenant/epoch authorization and evaluation-count consistency. The fixture set explicitly identifies structural-validity cases that need semantic rejection.

### 5.5 Remaining contract-freeze gates (SP-01)

- [ ] Review the proposed first slice and ratify its supported numerical domain and test tolerances.
- [ ] Complete the remaining workspace/invitation/world/package/provider/export/audit/enterprise identity contracts before their dependent implementation.
- [ ] Resolve exact SSE cursor expiry, archive resync transport and authorization/session lifecycle.
- [ ] Freeze model/checkpoint compatibility and artifact/runtime identity semantics with research, backend and platform reviewers.
- [ ] Add positive/negative/ambiguous-failure fixtures for the full agreed subset and review privacy visibility.
- [ ] Introduce reproducible, pinned contract validation and generated-client drift checks in CI when freezing the interfaces.
- [ ] Sign off the versioned interface subset and produce client/mock artifacts before parallel consumers depend on it.

The current draft pack is review scaffolding. It does not complete SP-01, imply an API deployment, or waive implementation/production gates.

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
- Membership is checked from current application state. Remove/revoke blocks new API calls immediately; active SSE reauthorizes at least every 30 seconds and run tokens expire/revoke promptly.
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

Proposed baseline effort is **118 engineering person-weeks**, plus **25% contingency = 29.5 person-weeks** for integration, investigation and rework. Effort includes work-package tests/documentation; staffing availability is separately discounted to 70% for review/support/coordination. Nine engineers provide approximately 6.3 delivery person-weeks per calendar week. Capacity alone suggests about 23.4 weeks; dependencies, partner trials and the 30-day operational observation make **W30–36** a more credible GA planning window. These are estimates, not a delivery promise.

The nine-role staffing model is in section 12. R0–R8 collectively complete accepted scope and add enterprise operations. Existing M0 maps to the verified baseline, old M1 to R1/R4, M2 to R2/R3, M3 to R4, M4 to R5, and M5 to R6–R8. Earlier sequencing is preserved where needed by contracts; workstreams overlap only behind stable interfaces.

| Milestone | Target window | Effort | Primary owner | Status |
| --- | --- | --- | --- | --- |
| R0 [Scope, contract and environment readiness](https://github.com/spei04/strange-physics/milestone/1) | W1–2 | 4 PW | TL + product | Blueprint ready for approval; remaining work planned |
| R1 [Scientifically valid learning/evaluation core](https://github.com/spei04/strange-physics/milestone/2) | W2–10 | 12 PW | Research | Planned |
| R2 [Tenant-aware durable control plane](https://github.com/spei04/strange-physics/milestone/3) | W2–11 | 16 PW | Backend | Planned |
| R3 [Isolated remote execution and delivery foundation](https://github.com/spei04/strange-physics/milestone/4) | W3–13 | 18 PW | Platform | Planned |
| R4 [Model gateway and both discovery tracks](https://github.com/spei04/strange-physics/milestone/5) | W8–16 | 14 PW | Research + backend | Planned |
| R5 [Researcher product, replay and self-hosting](https://github.com/spei04/strange-physics/milestone/6) | W3–16 | 12 PW | Frontend + platform | Planned |
| R6 [Integrated security, reliability and capacity gate](https://github.com/spei04/strange-physics/milestone/7) | W13–18 | 12 PW | QE + platform | Planned |
| R7 [Design-partner pilot and reference publication](https://github.com/spei04/strange-physics/milestone/8) | W19–22 | 10 PW | Product + lead | Planned |
| R8 [Enterprise readiness and GA](https://github.com/spei04/strange-physics/milestone/9) | W17–30, reserve through W36 | 20 PW | Lead + platform + security | Planned |

Windows are resource-leveled planning ranges, not instructions to assign every package simultaneously. Research can begin pilot calibration before full hosting; frontend mocks can proceed after SP-01. R6 cannot exit until R1–R5 are integrated.

### R0 — scope, contracts and environment readiness

**Objective/deliverables:** approved requirements, named owners, frozen interface baseline, reconciled existing PR, verified cloud prerequisites and workspace headroom.
**Tasks/subtasks:** SP-00 (review assumptions/staffing/partners), SP-01 (schemas/error cases/mocks/compatibility), SP-02 (credits/IAM/quotas/region/disk preflight).
**Dependencies/entry:** this plan reviewed; repository available; existing working code preserved.
**Acceptance/tests:** all critical interfaces have example success/failure messages and owner review; baseline checks linked; no unresolved account ownership or environment access for the next provisioned step; safe disk-headroom plan recorded.
**Risks:** actual hiring delay, billing/organization restrictions, near-full development disk.
**Exit / done:** product approves scope/schedule assumptions; lead signs interface baseline; infrastructure owners record private preflight evidence. Gate does not itself provision unbounded resources.

### R1 — scientifically valid core

**Objective/deliverables:** fitter, uncertainty, active selector, evaluator and development calibration report.
**Tasks/subtasks:** SP-03 numerical/identifiability matrix; SP-04 fitter and conditioning; SP-05 bootstrap/adaptation/candidate policies; SP-06 scoring/failure/censoring; SP-07 freeze draft and pilot size study.
**Dependencies/entry:** SP-01; reviewed baseline integration; development/evaluation split defined.
**Acceptance/tests:** known solvable fixtures achieve predeclared tolerance; unsupported/ill-conditioned cases explicit; no evaluation feedback; whole-world aggregation and all failures retained; CPU/storage measurements for ensemble scoring. V01/V02/V06.
**Risks:** unidentifiable tasks, correlated uncertainty, expensive rollouts, benchmark tuned to favor one strategy.
**Exit / done:** independently reviewed development report and versioned numerical configuration; official scoring waits for the later full protocol/isolation gate.

### R2 — tenant-aware durable control plane

**Objective/deliverables:** authenticated workspace API, PostgreSQL schema, run/experiment state machine, quotas and event stream foundation.
**Tasks/subtasks:** SP-08 identity/membership; SP-09 reservations/state transitions; SP-10 outbox/fencing/reconciliation; SP-11 RLS/object authorization; SP-12 quota/usage ledger.
**Dependencies/entry:** SP-01 interface freeze; SP-02 environment readiness; SP-27 deploy foundation for staging integration.
**Acceptance/tests:** simultaneous retries produce one logical experiment/debit; stale lease cannot commit; unauthorized lookup/SSE/artifact access denied; owner revocation enforced. V02/V03/V04.
**Risks:** confused deputy, connection exhaustion, accidental at-least-once side effects.
**Exit / done:** full backend conformance suite passes against real PostgreSQL; no uploaded customer code enabled yet.

### R3 — isolated remote execution

**Objective/deliverables:** immutable artifact storage, isolated package builds, sandbox launcher, recoverable remote worker and safe deployment pipeline.
**Tasks/subtasks:** SP-13 content store/checkpoint references; SP-14 build quarantine/scans; SP-15 runtime/network/resource policy; SP-16 end-to-end interruption/cancel; SP-27 IaC/keyless staging deployment.
**Dependencies/entry:** frozen contracts and environment readiness; integrate against R2 reservation/lease APIs.
**Acceptance/tests:** malicious builds cannot obtain deployment secrets; agent cannot reach metadata, arbitrary DNS/network, another run or evaluator; killed worker restores committed prefix with correct budget. V03/V04/V09/V11.
**Risks:** sandbox compatibility, incomplete egress controls, poisoned build output.
**Exit / done:** security/lead approve isolation evidence and a real remote investigation survives repeated forced interruption.

### R4 — models and both discovery tracks

**Objective/deliverables:** durable provider gateway, controlled LLM selector, predictor package protocol and independent scoring pipeline.
**Tasks/subtasks:** SP-17 model-attempt persistence; SP-18 provider adapters/limits/controlled LLM; SP-19 executable predictor validation; SP-20 independent evaluator runtime; SP-21 comparison integration.
**Dependencies/entry:** R1 model/scoring interfaces, R2 durable ledger, R3 isolation; build fixtures can start before full integration.
**Acceptance/tests:** replay uses recorded responses without paid calls; timeout ambiguity visible; no silent provider/model substitution; shared-fitter and agent-discovery results separate; malicious predictor has no truth/output channel. V06/V07/V04.
**Risks:** external rate limits, model-version drift, invalid output and compute imbalance.
**Exit / done:** a capped end-to-end run for every strategy/family and both tracks has a complete private manifest and reproducible evaluation.

### R5 — researcher product and self-hosting

**Objective/deliverables:** accessible authenticated product UI, constrained world builder, live/replay diagnostics, exports, remote SDK and supported self-hosting.
**Tasks/subtasks:** SP-22 workspace/builder; SP-23 live timeline/reconnect; SP-24 predictions/uncertainty/replay; SP-25 remote SDK/export; SP-26 install/upgrade/OIDC adapter.
**Dependencies/entry:** SP-01 mocks; progressive integration with R2/R3/R4.
**Acceptance/tests:** keyboard-accessible essential journeys; network reconnect loses no committed events; local/remote semantic parity; replay uses recorded frames; clean supported self-host install runs an investigation. V02/V05/V10.
**Risks:** frontend races, UI leaks evaluator metadata, self-host support matrix expansion.
**Exit / done:** a researcher completes author → run → inspect → export without operator edits; self-host limitations and isolation requirements explicit.

### R6 — integrated system gate

**Objective/deliverables:** security, load, fault, restore, data-lifecycle and operational evidence; pilot release candidate.
**Tasks/subtasks:** SP-28 load/fairness; SP-29 backup/restore/faults; SP-30 browser/SDK/upgrade E2E; SP-31 security/deletion/revocation matrix.
**Dependencies/entry:** R1–R5 merged and deployed to isolated staging; signed release candidate.
**Acceptance/tests:** pass 100-investigation synthetic provider envelope, two-hour hold/24-hour soak, no duplicate logical charges or cross-tenant leakage; pilot restore and migration gates; on-call contacts and draft runbooks. V04–V12 as relevant.
**Risks:** expensive evaluators, production-only IAM gaps, hidden state races.
**Exit / done:** release-readiness review approves limited design-partner production use; remaining enterprise gaps explicit.

### R7 — design-partner pilot and reference release

**Objective/deliverables:** monitored partner use, complete scored reference release, independent integration and operational feedback.
**Tasks/subtasks:** SP-32 partner onboarding/support; SP-33 protocol freeze/sweep/publication; SP-36 external extension/self-host integration.
**Dependencies/entry:** R6 pass; approved data terms; named partners; priced/capped benchmark run plan.
**Acceptance/tests:** four weeks of partner observation, product outcome denominators recorded, one external custom extension, one independently reproduced report; all scored reference failures published after sanitization. V05/V06/V12.
**Risks:** partner availability, procurement delays, accidental protocol changes, inference expense.
**Exit / done:** product/research/security sign pilot review; issues triaged with owners; no fabricated adoption or research claims.

### R8 — enterprise production and GA

**Objective/deliverables:** SSO/provisioning, audit export, full deletion/DR evidence, measured operating limits, launch/support package.
**Tasks/subtasks:** SP-34 SSO/service identities; SP-35 SCIM/revocation; SP-37 audit/retention/privacy; SP-38 regional recovery; SP-39 repeat supported-capacity validation; SP-40 independent review/on-call/30-day SLO; SP-41 release and post-launch review.
**Dependencies/entry:** R2 security foundation allows early enterprise work; final exit requires R7 and all release blockers resolved.
**Acceptance/tests:** every requirement traced, independent security issues resolved per policy, actual support coverage staffed, 30-day SLO record, documented recovery objectives achieved in drills, self-host upgrade verified, pilot feedback closed or risk-accepted.
**Risks:** SSO federation edge cases, third-party assessment lead time, insufficient operations coverage, unrealistic contractual guarantees.
**Exit / done:** signed launch checklist and immutable release/evidence manifest. “Enterprise ready” is limited to the tested envelope and supported deployment, not unlimited scale.

### Critical path

~~~mermaid
flowchart TD
    R0[R0 approval and interface baseline] --> R1[R1 fitting and scientific validation]
    R0 --> R2[R2 identity and durable state]
    R0 --> R3[R3 execution and delivery foundation]
    R2 --> R3
    R1 --> R4[R4 gateway and discovery tracks]
    R2 --> R4
    R3 --> R4
    R0 --> R5[R5 UI SDK and self-hosting]
    R4 --> R5
    R3 --> R5
    R1 --> R6[R6 integrated evidence]
    R4 --> R6
    R5 --> R6
    R6 --> R7[R7 four-week partner pilot]
    R2 --> R8[R8 enterprise hardening]
    R7 --> R8
    R8 --> GA[GA release gate]
~~~

Arrows represent exit dependencies; prerequisite schema work can unblock earlier mock/incremental implementation. Longest likely path is contract freeze → durable state/isolation → gateway/predictors → end-to-end evidence → partner pilot and operational observation → GA. Scientific validity and customer procurement are independent paths that can become critical. Buying more compute cannot remove either.

## 11. Prioritized, issue-ready engineering backlog

These work packages are published as 42 GitHub issues with nine milestones and matching labels, as authorized for Stage 2. Issue creation does not approve implementation. Each row supplies title, milestone, owner, dependencies, effort, concrete subtasks and testable acceptance; every package is initially **Planned**, except SP-00 whose document draft is ready for review. P0 means release-path priority, not an incident severity.

Use the linked GitHub milestones R0–R8 and the created labels priority:P0/P1/P2; area:research/backend/platform/frontend/security/quality; type:feature/test/docs/infra; status:blocked/needs-approval; gate:pilot/enterprise. Use one accountable owner; cross-team reviews are separate. Person-week estimates include tests and documentation. Before starting a multiweek package, break its named substeps into 1–3-day child issues with a concrete tested output; preserve parent dependencies and acceptance.

| ID / issue title | Milestone; priority; owner; effort | Dependencies | Subtasks and acceptance |
| --- | --- | --- | --- |
| SP-00 Approve scope, staff and evidence baseline ([#2](https://github.com/spei04/strange-physics/issues/2)) | R0; P0; TL/product; 1 PW | This blueprint | Confirm nine-role allocation, partners and gate owners; reconcile PR #1 status; record approved assumptions and unresolved blockers |
| SP-01 Freeze shared schemas and mocks ([#3](https://github.com/spei04/strange-physics/issues/3)) | R0; P0; BE/TL; 2 PW | SP-00 | Version remote/predictor/event/manifest envelopes; define errors/idempotency; generate clients/mock fixtures; V02 compatibility checks pass |
| SP-02 Verify cloud and workspace prerequisites ([#4](https://github.com/spei04/strange-physics/issues/4)) | R0; P0; PL; 1 PW | SP-00 | Private credits/expiry/IAM/quota/region review; preserve active consumers; recover safe disk headroom or resize through approved infrastructure change; no project IDs/secrets in public docs |
| SP-03 Validate numerical domain and baseline ([#5](https://github.com/spei04/strange-physics/issues/5)) | R1; P0; RS; 3 PW | SP-01 | Integrate reviewed core; analytic/stability/identifiability matrix; determine tolerances and profile 1/3/8-particle cases; V01 evidence |
| SP-04 Implement integrated sparse fitter ([#6](https://github.com/spei04/strange-physics/issues/6)) | R1; P0; RS; 3 PW | SP-03 | Feature dictionary and radial grid; integrated increments; conditioning/regularization; known-law recovery and explicit insufficient-support cases |
| SP-05 Add uncertainty, adaptation and active selection ([#7](https://github.com/spei04/strange-physics/issues/7)) | R1; P0; RS; 2 PW | SP-04 | Whole-experiment bootstrap; shared candidate bank; all-history/window/reset; paired calibration and no privileged change signal tests |
| SP-06 Implement held-out metrics and failure policy ([#8](https://github.com/spei04/strange-physics/issues/8)) | R1; P0; RS/QE; 2 PW | SP-04 | Isolated probe generation; normalized error and recovery censoring; invalid-prediction penalty; hand-computed aggregate fixtures pass |
| SP-07 Calibrate and draft frozen study manifests ([#9](https://github.com/spei04/strange-physics/issues/9)) | R1; P0; RS; 2 PW | SP-05/06 | Development pilot, interval coverage, ensemble CPU, effect/precision study; version candidate protocol and separate public/blind manifests |
| SP-08 Build identity and workspace memberships ([#10](https://github.com/spei04/strange-physics/issues/10)) | R2; P0; BE; 3 PW | SP-01/02 | OIDC verification, invitation lifecycle, role endpoints, account linking, owner safeguards; negative role/token tests |
| SP-09 Implement run and experiment transactions ([#11](https://github.com/spei04/strange-physics/issues/11)) | R2; P0; BE; 4 PW | SP-01 | SQL migrations/state transitions; idempotent reservation and debit; terminal states; concurrent key/ordinal conflict tests with PostgreSQL |
| SP-10 Add outbox, fencing and reconciliation ([#12](https://github.com/spei04/strange-physics/issues/12)) | R2; P0; BE; 3 PW | SP-09 | Deterministic launch IDs, lease epochs, duplicate dispatch, orphan/stuck recovery and failed-dispatch replay; V03/V09 |
| SP-11 Enforce tenant and artifact authorization ([#13](https://github.com/spei04/strange-physics/issues/13)) | R2; P0; BE/SE; 3 PW | SP-08/09 | RLS runtime roles, pool reset, object broker, SSE authorization; full cross-tenant mutation/read matrix passes |
| SP-12 Implement quotas and usage accounting ([#14](https://github.com/spei04/strange-physics/issues/14)) | R2; P0; BE; 3 PW | SP-09 | Run/workspace reservations, settlement and fair admission; bounded artifacts/CPU/tokens; concurrent exhaustion and reconciliation tests |
| SP-13 Persist immutable artifacts and checkpoints ([#15](https://github.com/spei04/strange-physics/issues/15)) | R3; P0; PL/BE; 3 PW | SP-01/09/11 | Hash/generation references, upload validation, complete checkpoint commit, orphan cleanup; object-write/DB-commit crash matrix |
| SP-14 Build packages in isolation ([#16](https://github.com/spei04/strange-physics/issues/16)) | R3; P0; PL; 4 PW | SP-02/27 | Quarantined builds, pinned dependencies, resource/egress bounds, scan/provenance; malicious hook cannot access trusted credentials or replace approved image |
| SP-15 Enforce sandbox runtime and broker policy ([#17](https://github.com/spei04/strange-physics/issues/17)) | R3; P0; PL/SE; 4 PW | SP-01/02/27 | RuntimeClass enforcement, per-run identity, deny network/DNS/metadata, resource/process limits; adversarial probes and scientific-stack compatibility |
| SP-16 Connect recoverable remote execution ([#18](https://github.com/spei04/strange-physics/issues/18)) | R3; P0; BE/PL; 4 PW | SP-10/12/13/14/15 | Coordinator launch, committed observation/checkpoint, cancellation/deadline, worker replacement; forced-death tests preserve one logical budget |
| SP-17 Implement durable model-call ledger ([#19](https://github.com/spei04/strange-physics/issues/19)) | R4; P0; BE; 3 PW | SP-09/12/13 | Logical call/attempt states, credential reference, unknown charge and reconciliation, response replay; timeout/crash tests |
| SP-18 Add bounded provider adapters and LLM selector ([#20](https://github.com/spei04/strange-physics/issues/20)) | R4; P0; RS/BE; 3 PW | SP-05/17 | Provider/version pin, secret gateway, context transform and rate limits; schema output validation; fake and capped live provider tests |
| SP-19 Define executable predictor packaging ([#21](https://github.com/spei04/strange-physics/issues/21)) | R4; P0; RS/PL; 3 PW | SP-01/14/15 | Predictor input/output protocol, immutable model references, finite/shape/time/output checks; hostile/malformed predictor fixtures |
| SP-20 Build independent evaluation execution ([#22](https://github.com/spei04/strange-physics/issues/22)) | R4; P0; RS/PL; 3 PW | SP-06/13/15/19 | Networkless predictor jobs, truth separation, snapshot scoring, cost/queue telemetry; no active-run feedback channels |
| SP-21 Integrate the two research tracks ([#23](https://github.com/spei04/strange-physics/issues/23)) | R4; P0; RS/QE; 2 PW | SP-07/16/18/20 | Strategy/world matrix, shared-fitter fairness and complete-agent runs, failure inclusion and full manifest; V06 comparison fixtures |
| SP-22 Build workspace and constrained world UI ([#24](https://github.com/spei04/strange-physics/issues/24)) | R5; P0; FE; 3 PW | SP-01; integrate SP-08 | Roles/run lists, supported graph/law editor, bounds validation, author/agent view distinction; accessible creation journey |
| SP-23 Implement live event timeline and reconnection ([#25](https://github.com/spei04/strange-physics/issues/25)) | R5; P0; FE/BE; 3 PW | SP-01; integrate SP-10/11/16 | Durable sequence, Last-Event-ID/resync, bounded chunks, terminal/cancel states; reconnect/auth-expiry E2E tests |
| SP-24 Implement prediction and replay diagnostics ([#26](https://github.com/spei04/strange-physics/issues/26)) | R5; P0; FE/RS; 2 PW | SP-22/23; integrate SP-20 | Actual/predicted/interval layers, scrub/compare/error curves, post-run truth gate; reference-frame accuracy and performance tests |
| SP-25 Deliver remote SDK, CLI and complete export ([#27](https://github.com/spei04/strange-physics/issues/27)) | R5; P0; BE; 2 PW | SP-01/13/16/21 | Auth/session adapter, async operation polling, content manifest verification and offline replay; local/remote conformance and no-provider replay |
| SP-26 Package supported self-host deployment ([#28](https://github.com/spei04/strange-physics/issues/28)) | R5; P0; PL; 2 PW | SP-08/15/16/27 | Document supported Kubernetes/sandbox + SQL/object/OIDC configuration; trusted dev profile separately labeled; install/upgrade smoke tests |
| SP-27 Create IaC and trusted delivery foundation ([#29](https://github.com/spei04/strange-physics/issues/29)) | R3; P0; PL; 3 PW | SP-02 | Separate env identities/networks, DB/store/queue/registry, keyless CI and staging smoke; Terraform plan/policy and rollback check |
| SP-28 Measure capacity and fairness ([#30](https://github.com/spei04/strange-physics/issues/30)) | R6; P0; QE/PL; 3 PW | SP-16/20/23 | Implement workload generators, numerical/IO profiles, staged load/soak/bursts, tenant fairness; section 7 acceptance evidence |
| SP-29 Prove backup, failover and fault recovery ([#31](https://github.com/spei04/strange-physics/issues/31)) | R6; P0; PL/QE; 3 PW | SP-13/16/27 | Backup/PITR policy, restore DB+objects, worker/DB failures, corrupted object and deletion replay; pilot RPO/RTO drill |
| SP-30 Verify integrated journeys and upgrades ([#32](https://github.com/spei04/strange-physics/issues/32)) | R6; P0; QE; 3 PW | SP-21/24/25/26 | Browser/SDK/service identity E2E, previous-version migration/rollback, export/import; V05/V10 matrix |
| SP-31 Exercise security and data boundaries ([#33](https://github.com/spei04/strange-physics/issues/33)) | R6; P0; SE/QE; 3 PW | SP-11/14/15/18/20 | Adversarial tenant/build/runtime/evaluator and delete/revoke tests, central-log redaction; release blockers fixed |
| SP-32 Onboard and support design partners ([#34](https://github.com/spei04/strange-physics/issues/34)) | R7; P0; TL/product; 3 PW | SP-28/29/30/31 (R6 exit) | Named contacts/data terms, onboarding sessions, four-week usage review, issue triage and operational feedback; report actual denominators |
| SP-33 Freeze and publish scored reference release ([#35](https://github.com/spei04/strange-physics/issues/35)) | R7; P0; RS; 3 PW | SP-07/21/31; priced sweep | Sign frozen protocol, cap run plan, execute paired suite, retain failures, sanitize/publication review; reproducible release manifest |
| SP-34 Add enterprise SSO and service identities ([#36](https://github.com/spei04/strange-physics/issues/36)) | R8; P0; BE/SE; 4 PW | SP-08/11; partner identity requirements | Workspace-bound federation, explicit link/migration, scoped machine credentials and rotation; tenant/issuer confusion and lockout tests |
| SP-35 Add provisioning and rapid deprovisioning ([#37](https://github.com/spei04/strange-physics/issues/37)) | R8; P0; BE; 3 PW | SP-34 | SCIM group/user mapping, idempotent sync, disable/revoke across tokens/SSE/jobs; sole-owner protection and audit tests |
| SP-36 Validate external extension and self-host adoption ([#38](https://github.com/spei04/strange-physics/issues/38)) | R7; P0; TL/PL; 4 PW | SP-25/26; partner availability | Outside team adds agent/law, installs/upgrades, reproduces report; fix documented friction; third-party evidence, not internal example |
| SP-37 Ship enterprise audit and retention controls ([#39](https://github.com/spei04/strange-physics/issues/39)) | R8; P0; BE/SE; 3 PW | SP-11/13/29/31 | Audit export, retention jobs/tombstones, credentials lifecycle, backup-expiry report and privacy documentation; V12 |
| SP-38 Rehearse regional disaster recovery ([#40](https://github.com/spei04/strange-physics/issues/40)) | R8; P0; PL; 3 PW | SP-29/37 | Secondary recovery location, restore ordering/epoch reset/DNS, key access and deletion reconciliation; timed target drill |
| SP-39 Revalidate supported production envelope ([#41](https://github.com/spei04/strange-physics/issues/41)) | R8; P0; QE/PL; 2 PW | SP-28; final runtime/SSO configuration | Repeat changed-path load and cost comparison; publish measured limits and upgrade implications, no unlimited-scale claim |
| SP-40 Complete independent assurance and operations ([#42](https://github.com/spei04/strange-physics/issues/42)) | R8; P0; TL/SE/PL; 3 PW | SP-28/29/30/31; final controls SP-34/35/37 | Pen test and remediation, staffed rota, incident/credential drill, 30-day SLO evidence; no unresolved launch blockers |
| SP-41 Approve GA release and post-launch review ([#43](https://github.com/spei04/strange-physics/issues/43)) | R8; P0; TL/product; 2 PW | SP-32/33/36; SP-34/35/37/38/39/40 | Signed readiness manifest, release notes/support matrix, staged rollout/rollback, D7/D30 review and next-quarter priority reset |

Post-GA P1/P2 candidates have no committed effort until customer/research evidence exists: stronger dedicated deployments/CMEK, additional regions, larger particle systems, more law-change regimes, additional language runtimes, continuous-control/RL and pixel-input tracks. Each requires its own numerical/security/cost acceptance criteria; do not mix new tracks into existing benchmark scores.

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

For seven engineers, combine lead/backend and QE/integration duties explicitly and replan to roughly W36–44 for GA; do not keep nine-person dates. At ten engineers, add the measured bottleneck role (likely frontend or platform/security); potential W28–34 still depends on partner trials, scientific calibration and operational observation. Hiring/ramp-up is outside these elapsed windows and must be added if staff are not ready at W1.

Proposed CODEOWNERS boundaries once directories exist: core/simulation/laws → research + lead; contracts/SDK → backend + research; API/database → backend; execution/infra → platform + security reviewer; evaluator → research + security; web → frontend; operations → platform; this roadmap → lead + product. Do not add empty directories merely to enact ownership.

### 12.2 Parallel development policy

Freeze shared schemas, migrations and examples before dependent implementation. Let the frontend consume mocks, platform test launcher policy against fake broker fixtures, and research implement predictors against the frozen protocol independently. Integrate real paths at W4, W8, W12 and the R6 gate. A mock-based milestone is not a production integration milestone.

Use separate checkouts only for independently active writers. Reuse free cloud checkouts sequentially and install pinned dependencies in copy mode. Never switch a branch beneath another active task or share mutable virtual environments through links. At completion/integration, inspect worktrees and consumers, preserve ignored evidence, then archive unused managed worktrees using the designated archive flow. Do not touch the computer-use project's local workflow.

Contract-affecting PRs need both producer and consumer review; security-boundary changes require security review; scientific protocol changes require research review. Incompatible changes pause downstream integration until fixtures/clients and migration policy are updated.

### 12.3 First eight weeks

These are weekly outcomes, not a promise that all referenced packages finish in that week. Keep work in progress to roughly one primary package per engineer, with pairing for critical interfaces. Assign actual people and weekly capacity at R0.

| Week | Research | Backend / lead | Platform / security | Frontend / quality | Integration decision |
| --- | --- | --- | --- | --- | --- |
| W1 | Audit numerical fixtures and draft identifiability matrix | Approve scope, review baseline PR, define operation/error/state schemas | Verify credits/IAM/region/quotas and disk recovery plan; threat boundaries | Sketch core journeys; define fixtures and evidence harness | SP-00 approved; blocking prerequisites named |
| W2 | Begin domain/convergence profiling | Freeze OpenAPI/events/predictor/manifests; SQL invariant design | IaC/bootstrap plans and identity boundary review | Generate mock client; prototype workspace/builder; contract tests | SP-01 baseline signed; no incompatible parallel contracts |
| W3 | Calibrate supported domains and fitter features | Implement invitations/roles and reservation transactions | Start isolated staging foundation and sandbox compatibility probe | Build workspace flows against mocks; seed DB integration harness | One tested invariant per workstream, preliminary costs |
| W4 | Implement integrated-increment fitter and conditioning tests | First transactional run/experiment slice; auth negative tests | Isolated build prototype and deny-network policy tests | First create/read run integration; failure/permission UI fixtures | End-to-end schema slice, not production uploaded-code approval |
| W5 | Bootstrap ensembles and development diagnostics | Outbox/leases, tenant policies and quota reservations | Content-store/checkpoint ordering; malicious build fixtures | Builder validation and SSE/reconnect implementation | Review information access, transaction races and numerical compute |
| W6 | Candidate/adaptation policies; metric/censoring fixtures | Reconciler and object authorization integration | Remote worker launch prototype against durable APIs | Timeline state transitions and replay-frame tests | Demonstrate recoverable internal run as components become ready |
| W7 | Evaluate stability/coverage; profile ensemble rollout cost | Provider-attempt ledger design; usage reconciliation | Cancellation, DNS/metadata denial, stale-worker and secret tests | Predictions UI mocks; self-host documentation starts from real stack | Scientific and sandbox risks reviewed; adjust backlog estimates |
| W8 | Development comparison harness; protocol calibration continues | Begin gateway integration and remote SDK adapters | Fault-injection integration, image provenance and staging release | Live/replay integration, local/remote contract matrix | W8 cross-team integration review; update pilot/GA forecasts |

Blocking dependencies: approved/frozen contracts; usable cloud projects and sufficient disk/quota; tested identity/tenant enforcement before private data; build/runtime isolation before uploaded code; science/scoring contract before official evaluation; immutable artifact/checkpoint semantics before recovery claims; model pricing/limits before paid runs; named partners before pilot; staffed response before contractual availability claims.

### 12.4 Longer horizon

- **Quarter 1 relative to approval (W1–13):** contracts, valid learning core, tenant control plane, isolated execution, initial UI and gateway integration. No enterprise claim.
- **Quarter 2 (W14–26):** complete integrated product; capacity/security/restore evidence; design-partner pilot, reference release, SSO/offboarding, audit and DR hardening.
- **Quarter 3 (W27–39):** GA gate around W30–36 if evidence permits; measured operations and support; validate demand for dedicated deployments or a new research track.
- **Quarter 4:** scale or research expansion based on actual adoption, bottlenecks and support load. Do not commit to multi-region, GPUs or novel benchmark claims without data.

Review forecasts weekly using completed acceptance outcomes and remaining critical-path risks. Reserve contingency visibly; do not quietly absorb feature additions into the original dates.

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
| RK07 Development VM fills and interrupts work | High / high | 538 MB free observed; preserve consumers/archives, recover approved safe headroom before builds | PL | Before next build; open |
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
| Does a full team mean a very short calendar? | Nine people still depend on shared schemas, scientific calibration, security integration, partner trials and a 30-day SLO observation. Include 25% effort contingency and a W30–36 GA window. |
| Are enterprise requirements being silently invented? | Mark SSO/SCIM, forecast load, SLOs, retention and staffing allocation as proposals; preserve accepted foundation; validate buyer requirements at R0. |
| Could growing history break LLM fairness/cost? | Fixed disclosed context transform and token ceiling; log truncation and retries; equal experiment budget is not equal compute. |
| Are self-hosting and hosted isolation inconsistent? | Document one supported secure deployment and a separately labeled trusted development profile. External install/upgrade evidence is required. |
| Can diagnostics/retention create security and cost debt? | Separate research artifacts from logs/backups; scoped access, deletion tombstones, archive review dates and tested retention. |
| Can a single file stay maintainable? | Stable IDs and section mapping, one progress ledger, links to existing detailed implementation references. Split into multiple canonical documents only after an explicit documentation decision. |

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
| Prioritized engineering backlog / issue-ready Markdown | Section 11 with linked SP-00–SP-41 issues, created labels/milestones and dependency relationships |
| CI/CD implementation plan | Sections 11 SP-27 and 13.1–13.2 |
| Initial risk register | RK01–RK17 in section 14 |
| Launch readiness checklist | Below |

### Launch gate

- [x] Local baseline inspected at its source commit and cloud checks rerun.
- [x] Current scope and limits distinguished from planned enterprise capabilities.
- [x] Single roadmap includes requirements, architecture, contracts, security, capacity, delivery, ownership and evidence model.
- [ ] Product owner approves expanded plan, provisional targets and staffing allocation.
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
| 2026-10-19 | Created consolidated enterprise roadmap | R0–R8, 118 base engineering PW +25% contingency, pilot W19–22, GA W30–36; approval pending |

**Approval scope:** accept this roadmap as the working baseline, including its proposed enterprise features and provisional operating targets, then begin R0. No arbitrary paid benchmark sweep, compliance claim or unlimited infrastructure spend is implied. Cloud provisioning remains tied to concrete priced configuration, verified account permissions and applicable release/approval controls.

**Next executable work after approval:** finish SP-00/01/02; reconcile and integrate the already-reviewed core through the normal PR process; start R1 numerical/fitting work and the R2/R3 foundations behind the frozen contracts. Keep this file current in each subsequent implementation PR.
