# Architecture review

## Settled requirements

- Public GitHub repository under the personal account `spei04`, not an organization.
- Research rigor is the first priority.
- Three law families, structured numerical observations and a replay viewer.
- Compare an LLM agent, random exploration and a classical fitting baseline.
- Fixed experiment budgets and generalization to unseen conditions.
- Investigate adaptation when a learned law changes.
- No training GPU requirement for the first version.
- A production research platform that external labs and startups can adopt and
  extend. A recorded demonstration alone does not satisfy the objective.

## Accepted decisions — round 1

The following recommendations were accepted. The proposed $100 pilot ceiling was
not retained: budget should not dominate architecture decisions. This does not
authorize unlimited infrastructure or model-provider spending.

| Decision | Accepted direction | Decisions that depend on it |
| --- | --- | --- |
| Product interfaces | Python SDK, CLI, hosted service, live browser investigations and replays; support self-hosting | Hosting, credentials, authentication, availability and API compatibility |
| Agent authority | Choose experiments, analyze observations and submit executable predictive models; isolate user code; keep a separate shared-fitter benchmark | Runtime contract, isolation, external integrations and scientific claims |
| Research execution | Durable remote jobs from the first production release; local execution uses the same contracts | Worker lifecycle, checkpoints, retries, queues and artifact storage |
| Cost controls | Per-run limits, workspace quotas, usage records, automatic stopping and customer-supplied model credentials; no fixed pilot ceiling yet | Credential handling, provider accounting and operating limits |
| Publication | Open-source platform; publish all scored reference benchmark artifacts, including failures; customer investigations private by default | Workspace permissions, exports, retention and immutable release artifacts |

An outside team must be able to add its own agent and law family without changing
the core, then reconstruct a recorded run from its manifest. Remote model calls
are replayable from records; a fresh model invocation is not guaranteed identical.

## Accepted decisions — round 2

All recommendations from this round were accepted except the AWS provider
recommendation, which was replaced with Google Cloud to use available credits.
The personal GitHub repository remains independent of the deployment account.

| Decision | Accepted direction | Decisions that depend on it |
| --- | --- | --- |
| Hosted access | Approved organizations first; public SDK and self-hosting remain available | Authentication, membership, abuse handling and onboarding |
| Cloud deployment | Google Cloud for the first managed deployment, using an eligible credited billing account; retain portable application interfaces | Dedicated projects, organization policies, task isolation, queues, database and object storage |
| Uploaded runtimes | Python agent and predictor packages first; remote agents use HTTP | Package manifests, dependency builds, SDK and sandbox image |
| Worker network | No general internet access for hosted user code; broker model calls | Egress controls, secrets, provider gateway and dependency installation |
| Initial load | Acceptance test 100 simultaneous investigations per deployment | Worker scheduling, provider backpressure, quotas and load tests |
| Physics scope | Two-dimensional interacting systems with up to eight particles and single-particle reference cases | Integrator, force interfaces, fitting library and visualization |
| Official evaluation | Public reference suites plus a distinct, versioned blind evaluation suite | Test-world isolation, submission limits, result publication and auditing |

The [deployment design](DEPLOYMENT_OPTIONS.md) records source-backed constraints
for Google Cloud. The provider is accepted; service selection, project boundaries
and deployment configuration remain proposals. Billing identifiers and account
details are not part of this public design record.

## Next decisions — round 3

| Decision | Proposed starting point | Decisions that depend on it |
| --- | --- | --- |
| Project boundary | Separate development and production Google Cloud projects, linked to the eligible credited billing account | Organization/folder placement, IAM, environments and deployment permissions |
| Execution architecture | Cloud Run trusted services; separate GKE Sandbox execution; Cloud SQL PostgreSQL, Cloud Storage and Cloud Tasks | Infrastructure code, network/DNS policy, region and quota validation |
| Workspace access | Managed OpenID Connect login, invitation-only membership and owner/researcher/viewer roles | Identity provider selection, authorization model and SDK authentication |
| Agent packaging | Python package plus lockfile; platform builds an immutable image in an isolated build environment | Build dependencies, package registry access, image policy and runtime compatibility |
| Agent recovery | Explicit SDK checkpoint after every committed experiment, including declared state and artifact references | State schema, checkpoint consistency, resume contract and failure tests |
| Reference changes | Both coefficient changes and activation/deactivation of terms within a family, scored separately | World generator, change detector, recovery metrics and protocol freeze |

## Dependent decisions to visit later

- Simulator representation: particle interactions; 2D versus 1D; solver
  accuracy and bounds; force grammar and identifiability.
- Experiment contract: legal controls, units, fixed cost, observation cadence,
  noise model, agent information, invalid-request handling and reset semantics.
- Inference: model dictionary, numerical fit, uncertainty estimation, change
  detector and old-data policy.
- Evaluation: held-out splits, budgets, metrics, number of seeds, pilot power and
  cost, protocol freeze, failure accounting and result artifacts.
- Execution: local process boundaries, generated-code policy, checkpoints,
  reproducibility manifests, timeouts and concurrency.
- Interface: replay schema, renderer, transport for live runs, world builder,
  deployment and visitor limits.
- Operations: secrets, logging, retention, release artifacts, CI and disk use.

Update this record after each review round. A proposal in another document is
not a substitute for an answered decision here.
