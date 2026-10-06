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

The first implementation milestone is available: a deterministic numerical
simulator, validated experiment/observation contracts, a random investigator,
force and agent plugins, a CLI, and a durable local journal with checkpoint
recovery. The core supports all three reference force families and up to eight
interacting particles.

**This is not yet a production service or a scored discovery benchmark.** Model
fitting, LLM integration, hosted isolation/authentication, the browser interface
and deployment remain on the implementation plan. No research results are claimed.

The scientific scope includes three force families, two-dimensional systems with
up to eight interacting particles, fixed-cost experiments, seeded observation
noise, hidden changes between experiments, and versioned run artifacts. Customer
investigations will be private by default; published reference benchmarks will
include every scored run and its failures. A separate blind suite will evaluate
worlds that participants cannot inspect.

Start with the [implementation plan](docs/PLAN.md), the [draft benchmark
protocol](docs/BENCHMARK.md), [accepted decisions](docs/DESIGN_DECISIONS.md), and
[implemented core](docs/CORE.md). The core documentation distinguishes current
behavior from the remaining production work.

## Development setup

Install Python 3.12 or newer and [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --locked
uv run strange-physics investigate --family spring --particles 3 \
  --directory runs/spring --agent-seed 42 --max-new-experiments 12
uv run strange-physics resume --directory runs/spring --agent-seed 42
uv run strange-physics inspect runs/spring/observations.json
```

The investigation has 40 experiments, with four common calibration experiments.
The first command stops after 12; the second resumes the same run. Other families
are `radial` and `velocity`; add `--stationary` to omit the hidden change. These
are development fixtures, not the future public/blind evaluation suites.

`session.sqlite` contains private world parameters and agent state; do not publish
it. `observations.json` contains only the public observation contract. Both are
created owner-readable, and local runs are ignored by Git. Local agents and force
plugins execute trusted Python code; this adapter is not a sandbox for uploaded
customer code. No GPU, model API key or cloud account is needed for the core.

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests examples
uv run pytest
uv build
```

The accepted hosted stack adds FastAPI, React/TypeScript/Canvas, and Google Cloud
Run, GKE Sandbox, Cloud SQL PostgreSQL, Cloud Storage and Cloud Tasks. These
components are not implemented yet. See the [deployment design](docs/DEPLOYMENT_OPTIONS.md).

## Extend the core

Implement the `ForceLaw` and `Agent` protocols without changing the package.
[The custom extension example](examples/custom_extension.py) adds a uniform field
and a mass-sweep investigator, including resume support:

```sh
uv run python examples/custom_extension.py runs/custom
uv run strange-physics schema observations
```

Plugins must provide a stable implementation identity; changing source, Python,
dependencies or registered plugin versions prevents a silent resume into different
behavior. See [the core contract](docs/CORE.md) for its reproducibility limits.

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
src/strange_physics/ simulation, force plugins, public contracts, journal, SDK and CLI
tests/              physical, protocol, crash-recovery and extension tests
examples/           external law and agent implementations
docs/CORE.md         implemented behavior, file boundaries and limitations
docs/PLAN.md         architecture, milestones and completion criteria
docs/BENCHMARK.md    proposed evaluation and fairness rules
docs/LAWS.md         equations, units and identifiable interventions
docs/RELATED_WORK.md positioning and prior work
docs/DESIGN_DECISIONS.md accepted architecture and implementation decisions
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
