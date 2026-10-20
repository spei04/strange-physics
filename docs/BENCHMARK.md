# Benchmark protocol — draft, not yet frozen

Execution planning: [ROADMAP.md](ROADMAP.md) and [EXECUTION_BACKLOG.md](EXECUTION_BACKLOG.md) own the approved delivery scope, prerequisite sequence and remaining approval gates. Accepted decisions and implemented behavior described here remain in force. Initial execution was approved on 2026-10-19; concrete paid and release actions retain their separate gates.

This document specifies intended evaluation. The local simulator, random investigator,
bounded spring fitter and predictor are integrated. The independent spring scorer
is reviewed and merged in PR #85; its protected-main acceptance is recorded in the
execution log. The fitted SDK/CLI I1 and official scored/hosted study remain unfinished.
Tune design choices on development worlds, then freeze the protocol, configuration
and commit before collecting evaluation runs.

## Research methods amendment (2026-10-19 cutoff)

The [dated method decision record](research/2026-10-19-METHOD_DECISIONS.md) adds18 proposed PR tasks, explicit sources/license checks and separate comparisons for shared-model selection, richer symbolic models and law-change recovery. Existing random/classical controls and the current I1/C2 assignments continue. New runtime remains behind RA_EXEC; provider, sizing, official-study and release gates remain separate.

The first new result is a local fixed-pool linear-model comparison after its scientific prerequisites:36 development episodes,432 purchased slots maximum,8 CPU-core-hours,1GiB new artifacts and zero provider calls. It does not wait for hosted deployment or all paper-inspired profiles. The optional later feasibility pilot has at most162 episodes; replicated-world sizing requires a separate approval and evidence before confirmatory freeze.

The18-task extension totals48–78 human engineering days plus25% reserve (60–97.5 days). It is recorded separately in execution-backlog.json; the approved168-task/369-edge/ten-gate graph and its conditional W52–67 GA reference remain unchanged. Added scope is not included in that forecast. The dated record owns detailed task contracts, exclusions, tests, effort, dependencies and exit gates.

The amendment separates A0 simple shared-fitter controls, A1 fixed-pool posterior/selector comparisons, B richer structure/full-system comparisons and C adaptation. Common-prefix rankings share exact snapshots; online arms use only their own purchased histories. Evaluator labels/scores never enter proposal memory or model selection. Native linear-model scoring is required for the early offline checkpoint; richer models need reviewed SP-19/20 evaluator binding. The existing40-slot scientific draft below is preserved; the12-slot offline fixture is a separately labeled development study.

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

The platform targets up to eight interacting particles. Single-probe worlds are
reference cases; multi-particle distributions and identifiability controls remain
to be calibrated on development worlds. Public reference suites and a
separate versioned blind evaluation suite are accepted. Keep their manifests,
access rules and reported scores distinct; never label the public suite blind.

## Environment and experiment cost

- Three law families, dimensionless coordinates and one to eight movable particles,
  with fixed-anchor reference cases.
- Agents know particle identities, masses and connections. They do not receive
  the active force laws, hidden coefficients or realized change times.
- Each accepted request chooses initial positions, velocities and masses within
  the published bounds, with at most one impulse on a selected particle at time
  zero. There are no interventions during the ensuing trajectory in this track.
  Resetting initial conditions never changes or rewinds the hidden regime.
- Proposed unit cost: 2 simulated seconds, integration step 0.01, and 41 position
  and velocity observations at uniform 0.05-second spacing, including time zero.
- Legal positions and velocities have norm at most 2; impulse norm at most 1;
  mass is between 0.5 and 2. These limits apply equally to all methods.
- Accepted default scored budget: 40 experiments, including 4 common calibration
  experiments. No method gets free measurements or access to evaluation probes.
  Custom studies can select other budgets; scores with different budgets are
  separate conditions, not directly interchangeable leaderboard entries.
- Stationary worlds retain their law for all 40 experiments. Changed worlds have
  one change after 16–24 accepted experiment slots, sampled independently of
  method performance and hidden from agents. Failed simulations consume slots
  and advance this index. This guarantees pre/post-change budgets and keeps the
  change boundary aligned across paired methods despite simulation failures.
- Methods know that a change is possible, but not its realization, coefficients,
  family label or timing. All receive the same candidate feature dictionary.
- Parameter changes and activation/deactivation of terms are separate strata.
  Family-switch and gradual-drift conditions are deferred.

The law stays fixed within each experiment. Its coefficients or active terms may
change only between experiments, and stationary controls never change. The
proposed 16–24 change window, legal numerical bounds, observation cadence and
solver settings still require development validation before protocol freeze.

Primary scoring measures prediction on held-out conditions and recovery after
changes. Matching the exact hidden equation is a secondary diagnostic, since
equivalent predictive models may have different representations.

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
One draft controlled-track evaluation uses 30 independent worlds per family and
condition, three policy seeds per world, and three selectors. With three families
and three conditions (stationary, coefficient change, term change), this is 2,430
episodes, including 810 LLM-selector episodes. At one selection call per adaptive
experiment, that implies 29,160 selection calls after the four common calibration
experiments; retries and other model calls are additional. Final suite size must
follow a development pilot measuring variability, runtime and cost. Do not launch
the full sweep merely because a provider credential exists.

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

The proposed `strange-physics.observations.v1` observation export covers only the first
record type. It will not be a complete research provenance bundle. A local
in-process scaffold is not safe isolation for an untrusted agent.

Use isolated execution environments and validated serialization for agents and
submitted predictors. Ordinary process separation alone is not sufficient for
untrusted hosted code. Never pass hidden config paths or true change markers in
errors or model context. Test this boundary.
Publish raw numeric artifacts and sanitized provider transcripts for all scored
reference runs, including failures. Keep customer investigations private unless
their owner explicitly publishes them. Replaying a recorded LLM run is
reproducible; resampling a remote model is not guaranteed to produce identical
decisions even at temperature zero.

## Results policy

No fabricated results, unmarked demonstrations or LLM-judged explanation scores
as the primary scientific endpoint. Record exclusions with reasons, retain failed
runs, and disclose implementation changes made after protocol freeze. Re-run the
paired suite after changes that affect the comparison.

2026-10-20 — The reviewed [native sequencing recommendation](research/NATIVE_COMPARISON_PROPOSAL.md) keeps finite-grid calibration before the first comparison and moves Laplace implementation plus its approximation-versus-grid audit to later RA-N02.b. Proposed first-result effort is 17–26 engineer-days (21.25–32.5 with reserve); later Laplace is 3–5 (3.75–6.25 with reserve), low confidence. Full programme scope, active dependencies, RA_EXEC, run caps and GA forecast remain unchanged. This is saved planning only.
