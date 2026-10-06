# Strange Physics

**How quickly can an agent recover when the laws of its world change?**

Strange Physics is a planned open-source research platform for developing and
evaluating agents that discover unfamiliar physical laws. Teams will connect
their own agents, define worlds, run controlled investigations, and reproduce
failures after an unannounced change in the governing law.

The product targets are a Python SDK, CLI, hosted service, and self-hosted
deployment. Durable jobs will run agents and executable predictive models in
isolated workers. A live browser interface will show actual motion, predicted
motion, uncertainty, experiments, and model revisions on a shared timeline.

## Status

This repository currently contains a research plan and project skeleton.
**There is no executable simulator, agent, benchmark, browser viewer, or result
yet.** Infrastructure and architecture decisions are under review.

The scientific scope includes three force families, two-dimensional systems with
up to eight interacting particles, fixed-cost experiments, seeded observation
noise, hidden changes between experiments, and versioned run artifacts. Customer
investigations will be private by default; published reference benchmarks will
include every scored run and its failures. A separate blind suite will evaluate
worlds that participants cannot inspect.

Start with the [implementation plan](docs/PLAN.md), the [draft benchmark
protocol](docs/BENCHMARK.md), and the [open design decisions](docs/DESIGN_DECISIONS.md).
These documents describe proposed behavior, not completed features.

## Development setup

The proposed stack is Python with uv for research code and TypeScript/React with
Canvas for the visual interface. The accepted Google Cloud services are Cloud
Run, GKE Sandbox, Cloud SQL PostgreSQL, Cloud Storage and Cloud Tasks. Runtime
versions, dependencies and detailed configuration remain under review. See the
[deployment design](docs/DEPLOYMENT_OPTIONS.md).
Setup commands will be added with the first runnable implementation.

## Research design

Two separate tracks will measure different capabilities:

- **Agent discovery:** agents select experiments, analyze observations, and submit
  executable predictive models. Teams can supply their own implementations.
- **Controlled experiment selection:** random, classical uncertainty-driven and
  LLM selectors use the same model fitter and observation interface. This isolates
  the value of experiment selection.

Primary outcomes are prediction error across the experiment budget and after a
change. Recovery time, false alarms on unchanged worlds, uncertainty calibration,
and compute/API cost are secondary outcomes. Failure to recover stays in the
results. Hidden evaluation scores never feed back into experiment selection.

The accepted default is 40 experiments including four common calibration
experiments. Agents choose initial conditions and an initial impulse, with no
intervention during motion. Particle identities, masses and connections are
visible; active force laws, coefficients and change times are hidden. Laws stay
fixed within each experiment and can change between experiments.

The first release uses numerical observations. Learning from pixels,
reinforcement learning, and GPU training are outside its scope. User-supplied
agent and predictor code requires isolated, resource-limited execution.

## Adoption requirements

- Add an agent and law family without modifying the core platform.
- Reconstruct a completed run from its versioned manifest and recorded artifacts.
- Resume work after worker failure without charging twice for one experiment.
- Run privately on the hosted service or deploy the system independently.
- Enforce configurable run budgets, quotas and cancellation; record model usage.

## Repository map

```text
docs/PLAN.md         architecture, milestones and completion criteria
docs/BENCHMARK.md    proposed evaluation and fairness rules
docs/LAWS.md         equations, units and identifiable interventions
docs/RELATED_WORK.md positioning and prior work
docs/DESIGN_DECISIONS.md decisions to settle before implementation
docs/CHECKPOINTS.md  save points and recovery after worker failure
CONTRIBUTING.md      contribution and research integrity guidelines
```

## Related work

[DiscoveryWorld](https://github.com/allenai/discoveryworld) provides a broader
scientific-discovery environment. [DiscoverPhysics](https://arxiv.org/abs/2605.26087)
is especially close: it studies unfamiliar simulated physics and includes
time-varying interactions. [PhysGym](https://github.com/principia-ai/PhysGym)
studies the role of prior information in interactive scientific reasoning.

The focus here is controlled, unannounced changes, measured recovery, matched
experiment budgets, and inspectable replays. This is a proposed research focus,
not a claim that changing-law discovery has never been studied.

## License

MIT. See [LICENSE](LICENSE).
