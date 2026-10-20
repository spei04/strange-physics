# Independent spring development evaluation — SP-06.a

Status: implemented and independently reviewed at source commit
`82fc9145b576fcb01e58815989bc2c1ebd1087a0`; integration and hosted CI remain gates.
This is a bounded local development evaluator, not an official benchmark freeze,
hosted execution, security isolation or production-readiness evidence.

## API and artifact boundary

The callable is `strange_physics.evaluation.evaluate_spring_predictions`:

```python
evaluate_spring_predictions(
    model: LinearSpringModel,
    protocol: SpringEvaluationProtocol,
    submissions: tuple[ProbePrediction, ...],
    world: WorldDefinition,
) -> SpringEvaluationResult
```

The additive protocol and result types are defined in
[evaluation_contracts.py](../src/strange_physics/evaluation_contracts.py).
Pass the validated `SpringPredictionSubmissions.entries` tuple as `submissions`.
The actual `WorldDefinition` and full result/reference artifacts are
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
labels. A finite nonnegative learned coefficient above 4 is not a protocol failure:
the predictor may return failed/unsupported output, which remains an unscorable
prediction outcome. The true-k bound never filters learned models. The evaluator does not import the fitter or predictor implementation.

SDK integration separately verifies the actual private journal and exact public
purchased prefix. It freezes protocol and normalization before outcomes and
requires action-condition disjointness from every purchased experiment, comparing
structure, mass, initial state and impulse rather than operation IDs. Overlap is
a failure, not permission to redraw or select probes based on predictions.

## Fixed independent reference algorithm

The reference algorithm and numerical thresholds were preregistered in
`bf47bd7278761c033ec69b0e52bde6b91777f15d` before measurements. The final context
also explicitly isolates the existing precision and rounding profile from caller
exponent bounds, flags and traps; no acceptance threshold changed:

- Convert every actual binary64 input with Decimal.from_float. Use Decimal
  precision 80 and round-half-even, explicit exponent bounds [-999999,999999],
  no clamp, cleared flags and InvalidOperation/DivisionByZero/Overflow traps.
  The context is independent of caller Decimal settings. Perform the coefficient/mass division and
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
  Downstream recurrence-error magnifications sum to at most cosh(sqrt(32))<144;
  final displacement weights total at most 11.5, giving less than 1,656 before
  arithmetic/input-sensitivity allowances. This grounds the conservative 1e6
  allowance rather than estimating it from observed errors.
- Final conversion to binary64 adds at most half an ulp. The position bound
  abs(anchor)+abs(x0-anchor)+abs(v0+J/m)*t <=12 gives a worst absolute conversion
  allowance of 2^-50. This float conversion dominates the two Decimal bounds.
  The existing direct 1e-12 component test criterion is not changed.

The finite reference tests compare ballistic and known oscillator cases,
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
report, with all requested probes counted and primary MSE fields null. Reference
generation is not started for an unscorable result. No mean over survivors is a
primary score.

Reference-generation and arithmetic failures produce an outer typed failure,
not false failed-prediction counts. Any retained partial metrics are explicitly
non-primary diagnostics; all unassessed probes stay visible.

## Timing and report bytes

Measure perf_counter_ns from scorer entry through association/shape validation,
reference generation and metric computation. Retain integer elapsed milliseconds
in EvaluationReport. Its hash uses the actual normalized canonical report bytes,
including timing, with no trailing newline. The retained byte sequence is
`canonical_json(report.model_dump(mode="json")).encode("utf-8")`, following the
[SCI canonical profile](SCI_CONTRACT.md#canonical-bytes-and-hashes). A prettified
JSON file has different bytes; normalize and validate the typed report before
comparing `report_sha256`. Deterministic metrics and counts do
not imply byte-identical reports across independently timed runs.

Tests include hand-calculated unequal probe/grid metrics; zero/positive
error; missing/all-invalid/explicit failures; duplicate/foreign/hash tampering;
normalization overflow/underflow; evaluator/arithmetic failures and complete
counts; actual report hashing/timing; independent reference cases and per-probe
I1 checks. Run full tests, lint/format, strict types, external schemas, configured
security gate, offline package allowlist and installed-wheel checks as applicable.
Independent source review plus exact integrated-head PR/main CI remain gates.


## Contracts and failure boundaries

The additive definitions have a generated
[JSON Schema](../contracts/evaluation.schema.json) and
[synthetic fixtures](../contracts/evaluation.examples.json). SpringEvaluationProtocol embeds ordered
SpringEvaluationProbe values. ProbePrediction binds an actual request hash to
a response, explicit failed marker or invalid marker; an omitted entry means
missing. SpringPredictionSubmissions is the retained collection whose entries
tuple is passed to the callable. It has a structural ceiling of 48
entries, allowing bounded duplicate/foreign associations to reach explicit
protocol failure; valid evaluation accepts no more than 24 submissions. The callable
validates this 48-entry structural boundary before hashing: larger tuples raise
input ValidationError, while 25–48 entries yield typed submission_limit. Nothing
is truncated.

`SpringEvaluationResult` is evaluator-only: its complete reference artifact and
source-world hash must not be exported with public reports or sent to a live
agent. Persist full results and private source input only in owner-readable
files (0600) within owner-only directories (0700). A hash of a small hidden
parameter domain does not hide that parameter. Public export must select the
explicit protocol/report projection; do not serialize the outer result. ProbeAssessment
values retain ordered statuses and non-primary per-probe MSE. Diagnostics retain
prediction and metric not-assessed counts separately. report_sha256 binds the
actual canonical SCI report including measured timing. The actual-input binder
recomputes model/protocol/submission/reference identities and verifies exact
reference grids; it does not prove numeric authenticity or journal origin.

The structural JSON boundary rejects invalid types, unbounded containers and
nonpositive scale. Semantic association/domain/arithmetic checks produce the
typed scorer outcomes. Only normalized typed inputs belong in the
scorer. The examples contain invented values and timing, not measured results.

## Recorded verification and limits

The final runtime source checkpoint is
`82fc9145b576fcb01e58815989bc2c1ebd1087a0`, tested on Linux Python 3.12.3 with
the unchanged pinned environment. Its 97 focused contract/runtime cases and
1,417 full repository tests passed. Ruff lint and format checks (79 files),
strict mypy (47 source files), all 522 external JSON Schema checks, and the
configured Bandit medium/high severity gate passed. The gate still reports six
existing low-severity findings; this is not a zero-finding security audit.
Offline wheel/sdist building, the package allowlist, and an isolated installed
wheel invocation producing a complete hash-bound report also passed.

An independent reviewer reran all 97 focused cases from immutable source, plus
seven additional boundary cases: huge learned coefficient with supported truth,
reordered nonzero errors, mixed missing/invalid outputs, metric reduction
underflow, and reference failures at the first and last probe. Seven targeted
mutations were detected across mass, impulse, anchor, force sign, averaging,
request identity and squared-error underflow. Caller Decimal-context isolation
was independently checked after the final source repair.

The fixed synthetic matrix uses the previously declared seven coefficients,
three masses and eight conditions from [the predictor evidence](PREDICTION.md),
with 41 frames per probe. It is 21 cohorts and 168 direct-model requests:

| Measurement | Observed value |
| --- | ---: |
| Failed predictions | 0 |
| Maximum absolute position-component difference | 2.6645352591003757e-15 |
| Maximum per-probe position MSE | 4.249608827306303e-31 |

All component differences satisfy the preregistered 1e-12 criterion and every
derived per-probe RMSE satisfies 0.001. Per-probe metrics were identical before
and after explicit Decimal-context isolation. Full reports retain their actual
measured timing and therefore need not have identical hashes across reruns.
The matrix compares direct supported model predictions against independent
labels. It does not measure fitted-model I1 generalization, provide an official
benchmark result, or establish hosted security or production readiness.
Journal binding, action disjointness and the fitted-model SDK/CLI flow remain
separate integration obligations.

Reproduce source checks in the existing pinned environment:

```sh
.venv/bin/pytest tests/test_evaluation_contracts.py tests/test_evaluation.py
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src tests examples
.venv/bin/python scripts/validate_contracts.py
.venv/bin/bandit -r src scripts -ll
```

Exact final integration-head review and protected PR/main CI are still required
before this work can be treated as integrated. Local checks do not replace them.
