# Strange Physics

**How quickly can an agent recover when the laws of its world change?**

Strange Physics is a research sandbox for active system identification under a
fixed experiment budget. An investigator chooses interventions, observes numerical
trajectories, fits a predictive model, and investigates unexpected failures after
an unannounced change in the governing law.

The planned visual interface lets visitors build a small world and replay an
investigation: actual motion, predicted motion, uncertainty, experiments, and
model revisions on a shared timeline.

## Status

This repository currently contains a research plan and project skeleton.
**There is no executable simulator, agent, benchmark, browser viewer, or result
yet.** Infrastructure and architecture decisions are under review.

The proposed foundation includes three force families, a two-dimensional probe
simulator, fixed-cost experiments, seeded observation noise, hidden changes
between experiments, and versioned trajectory export.

Start with the [implementation plan](docs/PLAN.md), the [draft benchmark
protocol](docs/BENCHMARK.md), and the [open design decisions](docs/DESIGN_DECISIONS.md).
These documents describe proposed behavior, not completed features.

## Development setup

The proposed stack is Python with uv for research code and TypeScript/React with
Canvas for the later replay viewer. Exact runtime versions, dependencies,
deployment and execution boundaries will be selected in the design review.
Setup commands will be added with the first runnable implementation.

## Research design

The proposed primary study compares **random exploration**, **classical uncertainty-driven
exploration**, and **LLM-selected experiments**, using the same model fitter and
observation interface. This isolates the value of experiment selection. A later,
separate study will allow agents to propose model structures.

Primary outcomes are prediction error across the experiment budget and after a
change. Recovery time, false alarms on unchanged worlds, uncertainty calibration,
and compute/API cost are secondary outcomes. Failure to recover stays in the
results. Hidden evaluation scores never feed back into experiment selection.

The first release uses numerical observations. Learning from pixels, arbitrary
user code, reinforcement learning, and GPU training are outside its scope.

## Repository map

```text
docs/PLAN.md         architecture, milestones and completion criteria
docs/BENCHMARK.md    proposed evaluation and fairness rules
docs/LAWS.md         equations, units and identifiable interventions
docs/RELATED_WORK.md positioning and prior work
docs/DESIGN_DECISIONS.md decisions to settle before implementation
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
