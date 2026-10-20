# Independent spring development evaluation — SP-06.a

Status: preregistered implementation plan. No scorer measurements have been run.
This is a bounded local development evaluator, not an official benchmark freeze,
hosted execution, security isolation or production-readiness evidence.

## API and artifact boundary

The planned callable is evaluate_spring_predictions(model, protocol, submissions,
world). The actual WorldDefinition and full result/reference artifacts are
evaluator-only. Public exports are explicit projections of the protocol and
frozen SCI EvaluationReport. No hidden coefficient, private world hash or labels
may enter fit/predict inputs or the public protocol/report.

The versioned protocol contains 1–24 ordered probe IDs and their exact public
PredictionRequests and recomputed hashes. Each request stays inside the accepted
single-particle, one-anchor, zero-rest linear spring counterfactual domain:
private true k in [0,4], mass in [0.5,2], anchor norm <=0.5, initial position norm <=3,
initial velocity norm <=2, impulse norm <=1, horizon <=2 seconds. SCI grid
validation and its 2–2,001 frame/work bounds remain unchanged. Counterfactual
IDs/topology must agree within each request/response; they need not equal the
source world's identity or mass.

The source world must itself be a supported one-particle stationary spring
world, with zero cubic coefficient and zero position/velocity observation noise.
Its coefficient supplies evaluator truth; the fitted coefficient never supplies
labels. A finite nonnegative learned coefficient above4 is not a protocol failure:
the predictor may return failed/unsupported output, which remains an unscorable
prediction outcome. The true-k bound never filters learned models. The evaluator does not import the fitter or predictor implementation.

SDK integration separately verifies the actual private journal and exact public
purchased prefix. It freezes protocol and normalization before outcomes and
requires action-condition disjointness from every purchased experiment, comparing
structure, mass, initial state and impulse rather than operation IDs. Overlap is
a failure, not permission to redraw or select probes based on predictions.

## Fixed independent reference algorithm

These choices are fixed before measurements:

- Convert every actual binary64 input with Decimal.from_float. Use Decimal
  precision 80 and round-half-even, explicit exponent bounds[-999999,999999],\n  no clamp, cleared flags and InvalidOperation/DivisionByZero/Overflow traps.\n  The context is independent of caller Decimal settings. Perform the coefficient/mass division and
  the optional J/m velocity update in Decimal. Apply the impulse once before
  time zero; preserve the requested initial position at zero.
- Let u=(k/m)*t^2. Approved inputs give 0<=u<=32. Compute C=sum((-u)^n/(2n)!)
  and S=sum((-u)^n/(2n+1)!) by separate paired Taylor recurrences, without
  square root, sin/cos, simulator integration or predictor calls.
- Position is anchor+(x0-anchor)*C+(v0+J/m)*t*S. Labels contain positions at the
  exact requested times; no interpolated grid or velocity score is introduced.
- Permit at most 128 paired terms. Once both next-term ratios are <=1, the
  alternating-series omitted tails are bounded by the magnitudes of their next
  terms. Require each coordinate bound
  abs(x0-anchor)*abs(next_C)+abs((v0+J/m)*t)*abs(next_S) <= 1e-60.
  Otherwise continue; exhausting the cap or a nonfinite/invalid value is an
  evaluator failure with no fabricated report. The analytic bound, not equality
  of rounded consecutive sums, determines convergence.
- The omitted-series bound is distinct from Decimal rounding. With u<=32, the
  largest cosine term is <46, absolute partial sums <144, and all recurrence
  denominators/intermediates stay below 1e5. There are fewer than 1e4 Decimal
  operations per frame; a conservative 1e6 amplification allowance on local
  absolute rounding <=1e-75 gives a 1e-64 coordinate rounding allowance.
  Downstream recurrence-error magnifications sum to at most cosh(sqrt(32))<144;\n  final displacement weights total at most11.5, giving less than1,656 before\n  arithmetic/input-sensitivity allowances. This grounds the conservative1e6\n  allowance rather than estimating it from observed errors.
- Final conversion to binary64 adds at most half an ulp. The position bound
  abs(anchor)+abs(x0-anchor)+abs(v0+J/m)*t <=12 gives a worst absolute conversion
  allowance of 2^-50. This float conversion dominates the two Decimal bounds.
  The existing direct 1e-12 component test criterion is not changed.

The finite reference tests will compare ballistic and known oscillator cases,
the existing coefficient/mass/probe matrix, irregular grids and tiny positive
coefficients. A higher-precision diagnostic may check this fixed algorithm, but
no observed result may change these settings or acceptance thresholds.

## Metrics and complete accounting

The fixed averaging rule is an equal mean over both position coordinates and
all requested time points within each probe, then an equal mean across probes.
Irregular grids use equal point weights, not elapsed-time weights. Per-probe MSE
is retained and RMSE is its derived square root; I1 requires every probe RMSE
<=0.001, not only an acceptable macro mean.

Normalization is MSE divided by a fixed predeclared coordinate scale squared.
I1 uses exactly 1.0 coordinate unit. Other development protocols may explicitly
retain another positive fixed scale; it is never estimated from outcomes.
Nonrepresentable scale squares, reductions, errors or normalization are explicit
failures. Positive errors may not silently underflow to zero.

Validate the entire submission association set before any scoring. Duplicate or
foreign IDs, mismatched request hashes, or actual model/protocol mismatch are
protocol failures with report=None and explicit unassessed counts. An associated
response with invalid model identity, time grid or shape is a failed prediction.
Missing, invalid or explicitly failed predictions produce the frozen unscorable
report, with all requested probes counted and primary MSE fields null. No mean
over survivors is a primary score.

Reference-generation and arithmetic failures produce an outer typed failure,
not false failed-prediction counts. Any retained partial metrics are explicitly
non-primary diagnostics; all unassessed probes stay visible.

## Timing and verification

Measure perf_counter_ns from scorer entry through association/shape validation,
reference generation and metric computation. Retain integer elapsed milliseconds
in EvaluationReport. Its hash uses the actual normalized canonical report bytes,
including timing, with no trailing newline. Deterministic metrics and counts do
not imply byte-identical reports across independently timed runs.

Required tests include hand-calculated unequal probe/grid metrics; zero/positive
error; missing/all-invalid/explicit failures; duplicate/foreign/hash tampering;
normalization overflow/underflow; evaluator/arithmetic failures and complete
counts; actual report hashing/timing; independent reference cases and per-probe
I1 checks. Run full tests, lint/format, strict types, external schemas, configured
security gate, offline package allowlist and installed-wheel checks as applicable.
Independent source review plus exact integrated-head PR/main CI remain gates.


## Early contract checkpoint

The additive definitions are in evaluation_contracts.py and
contracts/evaluation.schema.json. SpringEvaluationProtocol embeds ordered
SpringEvaluationProbe values. ProbePrediction binds an actual request hash to
a response, explicit failed marker or invalid marker; an omitted entry means
missing. SpringPredictionSubmissions is the retained collection whose entries
tuple is passed to the planned callable. It has a structural ceiling of48
entries, allowing bounded duplicate/foreign associations to reach explicit
protocol failure; valid evaluation accepts no more than24 submissions. The callable\nvalidates this48-entry structural boundary before hashing: larger tuples raise\ninput ValidationError, while25–48 entries yield typed submission_limit. Nothing\nis truncated.

SpringEvaluationResult is private: its complete SpringReferenceArtifact and
source-world hash must not be exported with public reports. ProbeAssessment
values retain ordered statuses and non-primary per-probe MSE. Diagnostics retain
prediction and metric not-assessed counts separately. report_sha256 binds the
actual canonical SCI report including measured timing. The actual-input binder
recomputes model/protocol/submission/reference identities and verifies exact
reference grids; it does not prove numeric authenticity or journal origin.

The structural JSON boundary rejects invalid types, unbounded containers and
nonpositive scale. Semantic association/domain/arithmetic checks produce the
planned typed scorer outcomes. Only normalized typed inputs belong in the
scorer. The examples contain invented values and timing, not measured results.
