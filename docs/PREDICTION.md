# Local linear spring prediction

## Preregistration

This SP-04.b plan is committed before implementation measurements. It preserves
the frozen SCI messages, the accepted SP-03.b domain/manifests, study distributions,
dependencies and existing assertions. A failed assumption must be recorded and
reviewed; it does not authorize tuning tolerances or dropping difficult cases.

The production API will accept the actual `LinearSpringModel`, a validated
`PredictionRequest`, and a required fixed `SpringPredictionConfig`. Its additive
result contains the unchanged SCI `PredictionResponse` only on complete success,
with separate safe diagnostics. No private world, evaluator labels, observation
prefix, executable package, pickle or hosted service is an input.

Recompute the actual model digest before propagation. Hash the actual request
and configuration into diagnostics; the frozen request has no asserted prediction
configuration digest, so do not claim to verify one. A result binder checks actual
input hashes, counts and SCI response alignment. These checks establish shape and
provenance, not numerical authenticity, purchase authorization or forecast accuracy.

### Fixed runtime and domain

The versioned profile describes an analytic stationary shared zero-rest linear
spring. Its compatibility allowlist binds the SCI model schema, accepted
paired-Simpson fitter version and actual fixed fitter-configuration digest.
Compatibility metadata is not proof that a model was authentically fitted.

Support one mobile particle connected to one static anchor, in either edge
orientation; coefficient k in [0,4], mass in [0.5,2], anchor norm at most 0.5,
initial-position norm at most 3, initial-velocity norm at most 2, impulse norm
at most 1 and horizon at most 2 seconds. Fitted coefficients above 4 remain valid
fitting artifacts but are unsupported by this predictor. Never clamp them.

Unseen radius-3 positions deliberately exceed purchased-action bounds. Do not
call `ExperimentSpace.validate_experiment` on prediction probes. Public SCI
validation still enforces identities/order, finite inputs, positive masses,
strictly increasing times, grid alignment and resource limits.

Accept any SCI-valid requested grid within [0,2], with at most 2,001 frames and
the existing 20,000 reference-step cap. This explicitly supports more output grids
than the finite 41-sample SP-03.b calibration matrix. For this analytic runtime,
`integration_dt` is alignment/replay metadata, not an executed integrator step
or an accuracy knob. Preserve and evaluate every exact requested float timestamp;
do not snap or regenerate it.

Apply the requested impulse exactly once as J/m before frame zero. With
r=x0-anchor, v0=v_initial+J/m, a=k/m and z=sqrt(a)*t, use

```text
x(t) = anchor + r*cos(z) + v0*t*sinc(z)
v(t) = v0*cos(z) - r*a*t*sinc(z)
sinc(0) = 1
```

Return the exact requested initial position at t=0, with the once-adjusted
velocity. For k=0 use the ballistic expression x0+v0*t. Do not divide by a tiny
angular frequency or derive the velocity factor as sqrt(a)*sin(z). Test
subnormal k and k/m underflow; the model coefficient itself remains unchanged.

Under this domain displacement magnitude is at most D=3.5, post-impulse speed
at most V=4 and phase at most 2*sqrt(8). Conservative output norm guards are
0.5+3.5+4*2=12 for position and 4+3.5*sqrt(8)<14 for velocity. They bound numerical
outputs and are not forecast accuracy criteria. Check every derived/output scalar
for finiteness. Work is constant per frame; no ODE integration loop is introduced.

### Failure and count policy

Model-hash mismatch precedes runtime compatibility and scientific-domain checks,
which all precede propagation. Return safe typed reasons for mismatched model,
unsupported runtime/domain, arithmetic failure or output-bound violation. Do not
include exception strings, hidden state or a fallback forecast.

Requested-frame count is the full manifest. Computed-frame count counts successfully
computed sequential frames. On a frame failure, its index equals the computed count.
Any failure has no response and zero returned frames, including when some earlier
frames were computed. Success returns all requested frames, with exactly their
timestamps and particle order. Never return a surviving-frame partial trajectory.

### Independent oracle and fixed tolerances

The oracle uses only Python standard-library Decimal arithmetic, with
`Decimal.from_float` for the exact binary input values and local precision 80.
It independently applies impulse/mass, then solves the oscillator ODE by the
power-series recurrence

```text
b[0] = x0 - anchor
b[1] = v_initial + J/m
b[n+2] = -(k/m)*b[n] / ((n+2)*(n+1))
x(t) = anchor + sum(b[n] * t**n, n=0..79)
v(t) = sum(n*b[n] * t**(n-1), n=1..79)
```

These 80 terms are independent of production cos/sinc evaluation and of the
simulator. With |z|<=2*sqrt(8), the first omitted even/odd terms and a geometric
tail bound give position truncation below 8.13e-59 and velocity truncation below
3.25e-57; use the looser conservative bound 1e-54. Decimal roundoff is separate
from the analytic truncation bound and far below the test tolerance at this
fixed precision. Self-check the oracle at k=0 and t=0.

For every requested frame and both coordinates, position and velocity component
absolute error against this oracle must be <=1e-12. Do not replace that criterion
with an averaged-only error or tune it after measurement. These finite checks
do not prove an IEEE-754 error bound for every continuous input/platform.

### Fixed predictor matrices

The core matrix has 168 requests: coefficients (0,1e-8,1e-4,0.3,0.9,2,4),
masses (0.5,1,2), and all eight unseen probes below. Use times i*0.05 for i=0..40
and integration_dt=0.01. Let u=(1/sqrt(2),1/sqrt(2)) and
q=(1/sqrt(2),-1/sqrt(2)).

| Probe | Anchor | Initial position | Initial velocity | Impulse |
| --- | --- | --- | --- | --- |
| axial aligned | (-0.5,0) | (3,0) | (2,0) | (1,0) |
| axial opposed | (-0.5,0) | (3,0) | (-2,0) | (-1,0) |
| rotated aligned | (0,-0.5) | (0,3) | (0,2) | (0,1) |
| rotated opposed | (0,-0.5) | (0,3) | (0,-2) | (0,-1) |
| diagonal perpendicular | -0.5u | 3u | 2q | q |
| velocity only | (0,0) | (0,0) | (2,0) | (1,0) |
| unseen in range | (0,0) | (1.5,0.2) | (0.3,-0.6) | (0.2,0.1) |
| zero state | (0,0) | (0,0) | (0,0) | none |

An additional 18 requests use coefficients (smallest positive binary64,1e-320,1e-300),
all three masses, and axial-aligned/velocity-only probes on the same 41 times.
This includes positive k whose division by mass 2 underflows in binary64.

Grid fixtures use the axial-aligned k=4,m=0.5 case unless otherwise stated:

- Irregular (0,0.03,0.11,0.29,0.75,1.37,2), integration_dt=0.01.
- Shortest (0,0.0001), integration_dt=0.0001.
- Dense 2,001 points i*0.001 for i=0..2000, integration_dt=0.0001.
- Nonuniform dense subset containing indices 0,1,3,5,...,1999,2000 of that grid.
- A tolerated timestamp 0.15+2e-11, retained and evaluated exactly at dt=0.01.
- Shared-time trajectories at dt=(0.01,0.005,0.0025) must be identical.

Negative/compatibility tests cover reversed edge orientation, wrong/shuffled
particle identities, reversed/aliased times, horizon 2.01, model/request/config
tampering, incompatible runtime, topology/mass/action violations, huge finite
coefficients/inputs, finite arithmetic guards and count-preserving failures.
Arithmetic/output guard injection must produce no partial response.

### Fit-to-predict development checks

Retain the [SP-03.b](SPRING_DOMAIN.md) noiseless purchased manifests: seven
coefficients, three masses, four ordered purchases, and steps (0.01,0.005,0.0025)
give 63 primary prefixes; seven mixed-mass prefixes use (0.5,1,2,0.5) at the
default step. Purchase anchor is (0.25,-0.4), with the unchanged displacement,
velocity and impulse rows from that document. Generate sampled public observations
with the existing simulator solely as test setup, call the actual production
fitter and predictor, and give truth only to the independent test oracle.

Each of the 70 fitted models must produce all 24 unchanged unseen probes.
For each probe separately, position RMSE over 41 times and both coordinates
must be <=0.001. Retain every failed outcome; do not average only survivors.
The direct model/oracle component criterion above separates predictor arithmetic
from fitted-coefficient error. This development test is not an EvaluationReport,
official benchmark score or completed I1 checkpoint. Independent scoring remains
SP-06.a and SDK/CLI integration remains SP-04.e.

## Planned verification and implementation boundary

Implement the additive fixed config/result contracts and immutable fixtures
first, then obtain independent API review. Implement production propagation and
independent tests next. Run focused/full tests, Ruff lint/format, strict mypy,
external JSON Schema validation, the CI security threshold and offline package
allowlist checks. Preserve the frozen SCI files and dependency manifests.

No hosted service, external provider, training GPU, deployment or paid action
is part of this task. Exact-head independent review and hosted integration checks
remain acceptance gates. Record measured results separately from this plan.

## Implemented local API

`predict_linear_spring(model, request, config)` implements the profile above in
[src/strange_physics/prediction.py](../src/strange_physics/prediction.py). The fixed
configuration, result and diagnostics are separate from the frozen SCI messages.
Their [schema](../contracts/prediction.schema.json) and
[synthetic examples](../contracts/prediction.examples.json) describe interface
behavior; the examples are not measured predictor output.

```python
from pathlib import Path

from strange_physics.prediction import predict_linear_spring
from strange_physics.prediction_contracts import SpringPredictionConfig
from strange_physics.research_contracts import LinearSpringModel, PredictionRequest

model = LinearSpringModel.model_validate_json(Path("linear-spring-model.json").read_text())
request = PredictionRequest.model_validate_json(Path("prediction-request.json").read_text())
result = predict_linear_spring(model, request, SpringPredictionConfig())
Path("prediction-result.json").write_text(result.model_dump_json(indent=2) + "\n")
```

The configuration digest is
`cd8ed299842b6c45f640f005232a657dbbc4890e309fbd9bb608e037bd6c237f`.
It binds the domain, analytic algorithm, runtime compatibility, exact-time policy,
reference-grid limits, output guards and no-partial-response policy. Fixed integer
fields reject booleans. A different runtime/domain policy requires a reviewed
version decision; this v1 profile does not expose arbitrary tuning knobs.

A positive subnormal coefficient can have k/m round to zero in binary64. The
implementation follows the finite continuous limit without changing the model
artifact. Frame zero returns the original position exactly; when no impulse is
present, it also retains the original velocity tuple, including negative zero.
An impulse is applied once as requested. The direct component-error fixtures
include tiny coefficients and the ballistic limit.

The standalone predictor sees no source observation noise metadata. Its success
therefore asserts complete bounded propagation under the supplied model, never
that the model accurately describes an unknown world or was learned without noise.
Fitting accuracy diagnostics remain separate; prediction does not erase them or
convert them into an accuracy guarantee.

The runtime allocates at most 2,001 frames for one particle and performs constant
work per frame. A frame-level arithmetic failure discards the response even if
earlier frames were computed, while diagnostics retain their count and the failed
index. Runtime/model compatibility and input hashes are not a sandbox, signature,
proof of purchase or proof that the coefficient was actually fitted.

## Reproduction

```sh
.venv/bin/pytest tests/test_prediction.py tests/test_prediction_contracts.py
.venv/bin/python scripts/validate_contracts.py
.venv/bin/pytest -p no:cacheprovider
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy src tests examples
```

Direct oracle tests check every position/velocity component. The development
fit-to-predict test checks each of the 24 probes for every fitted model, with MSE
averaged over 41 times and two coordinates and RMSE as its square root. This
test-local calculation does not implement the independent SCI development scorer.
SP-06.a still owns that evaluator; SP-04.e still owns SDK/CLI reproduction and I1.

## Recorded local evidence

Measured on 2026-10-20, Linux x86_64 with Python 3.12.3. Preregistration:
`9f30fa2da84687892d2d2ce2501f321229b177fb`. Production/test source:
`205b3fc9106ef5290a81037e1da978a0236080e3`. The matrix, Decimal oracle policy,
1e-12 component tolerance and 0.001 per-probe RMSE criterion were unchanged.

| Direct prediction cohort | Requests | Maximum position component error | Maximum velocity component error | Failed |
| --- | ---: | ---: | ---: | ---: |
| Core coefficient/mass/probe matrix | 168 | 2.66454e-15 | 5.32907e-15 | 0 |
| Near-zero/subnormal matrix | 18 | 1.77636e-15 | 0 | 0 |
| Irregular grid, 7 frames | 1 | 1.33227e-15 | 3.55271e-15 | 0 |
| Shortest grid, 2 frames | 1 | 0 | 4.44089e-16 | 0 |
| Dense grid, 2,001 frames | 1 | 3.21965e-15 | 6.21725e-15 | 0 |
| Nonuniform dense grid, 1,002 frames | 1 | 3.16414e-15 | 6.21725e-15 | 0 |
| Exact tolerated timestamp, 3 frames | 1 | 1.33227e-15 | 3.55271e-15 | 0 |

All 70 production fits (63 primary and seven mixed-mass prefixes) generated all
24 unseen predictions: 1,680 probe outcomes, zero failures. The worst per-probe
position RMSE was 8.4695975e-6, at true k=4, purchase mass 0.5, default step 0.01
and the axial-aligned mass-0.5 unseen probe. This is development evidence from
synthetic public observations with independently computed labels, not an official
report. It reproduces the calibrated coefficient-to-trajectory result while
using the actual production fitter and predictor.

A self-review found that adding a synthetic +0.0 when no impulse exists changes
the sign of an initial -0.0 velocity. The source now retains that original tuple,
with a regression test. No physical matrix, coefficient, threshold or tolerance
was changed to obtain a passing result.

The focused suite has 314 cases and the complete local suite passed 1,320 tests.
Repository-wide Ruff lint/format, strict mypy (43 files), 506 external JSON Schema
fixture checks and the configured Bandit threshold passed. These checks validate
the bounded local implementation, not hosted execution or production operations.
Independent review and exact integrated-head hosted CI remain acceptance gates.
