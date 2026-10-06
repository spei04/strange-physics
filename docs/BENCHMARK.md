# Benchmark protocol — draft, not yet frozen

This document specifies intended evaluation. No benchmark or simulator is
implemented yet. Tune design choices on development worlds, then freeze
this protocol, configuration files and commit before collecting evaluation runs.

## Questions and interpretation

1. With a fixed intervention budget, does experiment selection improve prediction
   on unseen initial conditions?
2. After an unannounced law change, how much predictive accuracy is lost, and how
   quickly does each method recover?
3. Are improvements worth the additional wall time and API cost?

The controlled-selection track uses a shared disclosed model class. Its claims
concern experiment design and adaptation within that class. A separate
agent-discovery track accepts executable predictive models and measures complete
agent performance. Keep results and claims from the two tracks separate.
Incorrect and overconfident models are legitimate outcomes in both.

The scientific details below primarily specify the controlled-selection track.
Budgets, metrics, serialization and failure handling for the agent-discovery track
must also be frozen before an official evaluation. That track is accepted product
scope, but its complete protocol is not yet specified.

## Environment and experiment cost

- Three law families, dimensionless coordinates, one movable probe, known mass.
- Each accepted request resets the probe to chosen initial conditions and applies
  one impulse at time zero. A reset never changes or rewinds the hidden regime.
- Proposed unit cost: 2 simulated seconds, integration step 0.01, and 41 position
  and velocity observations at uniform 0.05-second spacing, including time zero.
- Legal positions and velocities have norm at most 2; impulse norm at most 1;
  mass is between 0.5 and 2. These limits apply equally to all methods.
- Total budget: 40 experiments, including 4 common calibration experiments.
  No method gets free measurements or access to evaluation probes.
- Stationary worlds retain their law for all 40 experiments. Changed worlds have
  one change after 16–24 completed experiments, sampled independently of method
  performance and hidden from agents. This guarantees pre/post-change budgets.
- Methods know that a change is possible, but not its realization, coefficients,
  family label or timing. All receive the same candidate feature dictionary.
- Parameter changes and activation/deactivation of terms are separate strata.
  Family-switch and gradual-drift conditions are deferred.

Small deterministic development fixtures may use reduced budgets and known
change points. They are test fixtures, not scored reference results.

Invalid requests are rejected without a physics observation. Cap proposal retries
at two per slot; then use a fixed seeded valid fallback and report the event. All
provider calls, tokens and retry costs count against the configured compute cap.
An accepted experiment consumes its slot even if numerical integration fails;
log that outcome and do not silently redraw the world. Check validity and solver
stability before freezing the world distribution.

## Methods and controlled comparisons

| Method | Selects the next experiment | Fits the dynamics |
| --- | --- | --- |
| Random | Samples legal conditions from a specified distribution | Shared sparse fitter and ensemble |
| Classical active | Maximizes predicted ensemble disagreement over a common candidate set | The same fitter and ensemble |
| LLM design | Chooses from the same candidate set using observations, residuals and model summaries | The same fitter and ensemble |

Use a common seeded candidate set of 128 interventions per round for the controlled
comparison; random chooses uniformly from that set. Pin this generator. Shared
calibration observations are identical across methods for a paired world.
Independent experiment noise streams are keyed by world and experiment index.

Each method gets the same purchased observations, legal-action schema, current
fit and uncertainty information. The LLM sees the complete numerical observation
record or a fixed disclosed transform; do not claim a matched-information study
if it receives only selective summaries. Set a fixed context-management policy.

Fix a common adaptation policy for the controlled selector comparison. Separately
cross selectors with all-history, sliding-window and detector-reset policies to
measure which component caused an improvement. Use an oracle reset at the true
change only as a labeled diagnostic upper bound, never as an ordinary baseline.

Log model/provider version, settings, prompts, responses, timeouts, token counts,
latency and actual reported cost. Pin numeric fits and cap fitting work per round.
An equal experiment budget is not an equal compute budget; report both. Choose
provider and operational limits before an evaluation sweep. Do not publish estimated
prices as actual costs.

## Model fitting and uncertainty

The initial dictionary contains constant terms, position, cubic radial spring
terms, linear/cubic velocity terms, rotated velocity, and a fixed grid of softened
radial-field features. All methods see the full dictionary. Fit integrated
increments, select sparsity using development-only settings, and assess conditioning.

Bootstrap whole experiments and propagate each fitted model to produce an
ensemble of trajectories. In low-data regimes report insufficient support rather
than inventing a confidence number. Add the specified measurement noise when
evaluating coverage of noisy observations. Report coverage and interval width
separately for in-range and out-of-range conditions.

## Data splits and generalization

Use disjoint development and evaluation world seeds and coefficient samples.
Tune thresholds, feature grids, regularization and prompts only on development
worlds. Freeze manifests before evaluation. A public generator is not a secret
test set: procedural held-out seeds reduce overlap but do not establish freedom
from model pretraining contamination.

For each world, create a fixed evaluator-only bank of 64 initial conditions per
regime: 32 in-range and 32 in a predeclared wider, stable range. Use the same banks
for paired methods. These test interpolation and initial-condition extrapolation;
they do not establish generalization to arbitrary new law families.

The evaluator uses noiseless trajectories for primary prediction errors. It
evaluates committed model snapshots after every experiment without returning
scores to the agent. Any diagnostic probes the agent requests consume the normal
budget. Viewer-only ground truth is added only after the episode ends.

Begin with a development pilot to estimate runtime, variance and recoverability.
Proposed evaluation: 30 independent worlds per family and condition, three policy
seeds per world, and three selectors. This is 1,620 episodes for three families
and two conditions, including 540 LLM episodes and up to 21,600 LLM decisions
before retries. Establish cost with a small pilot first. Do not launch the full
sweep merely because a provider credential exists.

## Metrics

Primary prediction error is mean squared trajectory-position error divided by a
fixed, predeclared coordinate scale squared. Also report raw errors and velocity
errors separately. Avoid normalization by a near-zero per-trajectory variance.

Primary summaries:

- Mean prediction error across the experiment budget, reported separately for
  in-range and extrapolation probes.
- Mean error across a fixed 16-experiment post-change window, available for every
  allowed change point. Keep nonrecovering episodes in this average.

Secondary summaries:

- Recovery latency: experiments after the change until held-out error stays below
  a development-fixed threshold for three consecutive snapshots. Treat runs that
  never recover as right-censored; report recovery fraction at 16 and restricted
  mean recovery time, not an average over successful runs alone.
- Detection delay, missed changes, and false-alarm count/rate on stationary worlds.
- First post-change prediction error, final error, and pre-change fit quality.
- Empirical 90% predictive-interval coverage and interval width.
- World-level failure rate, fallback count, numerical failures, wall time, tokens
  and provider cost.

Freeze the recovery threshold using oracle-fit diagnostics and development noise
levels. Report worlds that were never adequately learned before the change as
well; do not filter those worlds out to improve recovery statistics.

Compute paired method differences within each world. Aggregate across policy
seeds first, then bootstrap independent worlds for 95% confidence intervals.
Do not treat trajectory frames or repeated policy seeds as independent worlds.
Report each family and condition plus a predeclared equal-weight macro average.
Publish error curves and failure distributions alongside rankings.

## Reproducibility and artifact boundaries

Record schema version, code commit, lockfile/config hashes, world and policy seed
identities, solver settings, method settings, purchased observations, selected
experiments, model snapshots and evaluator outputs. Keep three separate artifacts:

1. Agent-visible observation and decision records.
2. Evaluator-only world parameters, change events and held-out trajectories.
3. Completed viewer bundles that may reveal ground truth after the investigation.

The proposed `strange-physics.observations.v1` demo export covers only the first
record type. It will not be a complete research provenance bundle. A local
in-process scaffold is not safe isolation for an untrusted agent.

Use isolated execution environments and validated serialization for agents and
submitted predictors. Ordinary process separation alone is not sufficient for
untrusted hosted code. Never pass hidden
config paths or true change markers in errors or model context. Test this boundary.
Publish raw numeric artifacts and sanitized provider transcripts for all scored
reference runs, including failures. Keep customer investigations private unless
their owner explicitly publishes them. Replaying a recorded LLM run is reproducible; resampling a remote model is
not guaranteed to produce identical decisions even at temperature zero.

## Results policy

No fabricated results, unmarked demonstrations or LLM-judged explanation scores
as the primary scientific endpoint. Record exclusions with reasons, retain failed
runs, and disclose implementation changes made after protocol freeze. Re-run the
paired suite after changes that affect the comparison.
