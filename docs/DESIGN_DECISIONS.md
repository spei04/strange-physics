# Architecture review

## Settled requirements

- Public GitHub repository under the personal account `spei04`, not an organization.
- Research rigor is the first priority.
- Three law families, structured numerical observations and a replay viewer.
- Compare an LLM agent, random exploration and a classical fitting baseline.
- Fixed experiment budgets and generalization to unseen conditions.
- Investigate adaptation when a learned law changes.
- No training GPU requirement for the first version.

## First decisions

These are questions, not accepted architecture choices. Review them before
implementing their dependent components.

| Decision | Proposed starting point | Decisions that depend on it |
| --- | --- | --- |
| Visitor execution | Public replay viewer; live experiments run locally first | Hosting, credentials, authentication, rate limits, service availability |
| LLM authority | Choose structured experiments; a shared numerical fitter produces predictions | Agent API, model grammar, isolation, fairness claims |
| Research job location | Local CPU runs with checkpoint/resume | Worker lifecycle, storage, queues, scheduling, remote compute |
| Pilot spending cap | At most $25 in total provider spend before reviewing the pilot | Provider/model choice, run count, context limits, retry limits |
| Data publication | Curated completed runs and sanitized transcripts | Record schemas, retention, release storage, public download size |

## Dependent decisions to visit later

- Simulator representation: one probe versus many bodies; 2D versus 1D; solver
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
