# First-spring domain calibration

## Preregistration

This plan is committed before SP-03.b measurements. It is a test-only calibration
of the first local linear-spring slice, not a production fitter, predictor,
scorer, benchmark, or claim that observations were purchased from a server.
The harness constructs valid public observation prefixes from known synthetic
fixtures. Production fitting remains SP-04.a and local integration remains I1.

No production source, schemas, world distributions, observation cadence,
dependencies or existing assertions change. Results must retain failures.
A result-driven deviation requires an explicit explanation and independent review;
it must not silently change the declared matrices, probes or thresholds.

### Proposed numerical scope

One movable particle connects to one static anchor through one zero-rest-length
linear spring, with a stationary, shared nonnegative coefficient. Masses lie
in [0.5, 2], coefficient k in [0, 4], and anchor norm is at most 0.5.
Purchased initial-position and initial-velocity norms remain at most 2;
impulse norm remains at most 1. Post-impulse speed can reach 4 at mass 0.5.

The first accuracy ratification concerns noiseless observations over two seconds,
sampled every 0.05 seconds (41 frames), with the existing RK4 default step 0.01.
Steps 0.005 and 0.0025 are calibration refinements, not changes to the default.
Unsupported topology, cadence, horizon, masses or actions fail explicitly.
Other families, nonlinear/change regimes and noise guarantees remain later work.
Hidden law type/coefficient must not be supplied to the diagnostic estimator to
select records, windows, settings or acceptance of its input.

Unseen probes use initial-position norm at most 3, the same mass/velocity/impulse
bounds and static anchors of norm at most 0.5. Thus displacement from an anchor
is at most D=3.5 and post-impulse speed at most V=4. These probes use the SCI
prediction contract; they must not be passed through purchased-action validation.
A successful finite calibration matrix alone does not prove every continuous
input in this envelope.

### Fixed parameter and purchase manifests

- Deterministic k: 0, 1e-8, 1e-4, 0.3, 0.9, 2, 4.
- Mass: 0.5, 1, 2.
- RK4 step: 0.01, 0.005, 0.0025.
- Observation spacing: 0.05; horizon: 2.
- Training anchor: (0.25, -0.4).
- Four records, ordered as below. Position is anchor plus the listed displacement.
  The mass is constant within each primary prefix. A separate prefix uses
  masses (0.5, 1, 2, 0.5), for every k at the default step.

| Record | Displacement | Initial velocity | Impulse |
| --- | --- | --- | --- |
| 0 | (0.7, 0.2) | (-0.2, 0.3) | none |
| 1 | (-0.6, 0.5) | (0.4, -0.1) | (0.3, 0.4) |
| 2 | (1.2, -0.3) | (0, 0.5) | none |
| 3 | (-0.3, -1) | (-0.4, 0.2) | (-0.4, 0.3) |

### Fixed unseen-probe manifest

Each accepted coefficient is assessed at each mass 0.5, 1 and 2 against all
eight probes. Here u=(1/sqrt(2),1/sqrt(2)), q=(1/sqrt(2),-1/sqrt(2)).

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

Labels are continuous analytic oscillator positions. The diagnostic prediction
uses the same closed-form propagation at the estimated coefficient, not the
production simulator. This measures coefficient-to-trajectory sensitivity;
a production predictor still needs SP-04.b implementation and separate validation.

Each probe's position MSE is the arithmetic mean of squared coordinate errors
over its 41 times and both coordinates; RMSE is its square root. Enforce
RMSE <=0.001 **for every probe**, retaining individual values, maximum and counts.
Do not hide a failure in an average across probes.

### Estimator and window accounting

The diagnostic estimator accepts only a validated SpringFitInput containing the
exact public prefix. It uses public masses, anchor position and observations.
All completed records contribute every paired window and both coordinates;
failed records remain in prefix/provenance and counts.

For observation spacing h, each adjacent frame triple (0,1,2), (2,3,4), ...,
(38,39,40) gives one velocity increment y=v2-v0 and the design vector

g = -h * (r0 + 4*r1 + r2) / (3*m).

There are 20 windows and 40 scalar rows per completed record. Zero rows remain
included. No odd tail is silently dropped. A separately labeled trapezoidal
diagnostic uses the same endpoints and windows, with
g = -h * (r0 + 2*r1 + r2) / (2*m), so comparisons buy no different measurements.

The raw least-squares diagnostic is dot(g,y)/dot(g,g), pooling all completed
records. No clipping, positivity projection or hidden-value correction is
allowed. Negative/nonfinite estimates are explicit failures and retain the raw
value when representable. A versioned test-only configuration digest distinguishes
the two integration methods; it contains no hidden coefficient.

### Excitation, zero stiffness and perturbations

Pooled design RMS G=sqrt(sum(g^2)/N), where N counts both coordinates of every
complete window, has units time*coordinate/mass. The predeclared numerical
support floor is G>=1e-6. Zero-design records stay in N; a failed record has no
windows but remains in record counts and the prefix hash. A scalar condition
number of one does not establish excitation.

Physical amplitude sweep: 0, 1e-12, 1e-10, 1e-8, 1e-6, 1e-5, 1e-4, 1e-2,
with k=(0,0.3,4), mass=(0.5,2), anchor=(0.25,-0.4), displacement=(amplitude,0),
zero velocity/impulse and the default grid. Also test explicit design RMS just
below, at and above 1e-6, including zero rows and residual stresses +/-1e-14.

For fixed observed design, coefficient perturbation is bounded by
||delta_y-k*delta_g||_RMS/G. The 1e-6 support floor resolves an absolute
coefficient perturbation of 1e-8 under a declared 1e-14 residual stress.
This is a **roundoff/perturbation diagnostic**, not a proven bound on total
RK4, quadrature or sensor-noise error. Measure actual finite-precision effects
near zero/weak excitation separately. Failure invalidates a claim; it does not
authorize threshold tuning using unseen probes.

Calibration acceptance uses the evaluator-only criterion
abs(k_est-k_true)<=max(1e-8,0.01*k_true). Relative error is undefined at zero;
report absolute error there. The absolute floor dominates below k=1e-6 and
does not imply a uniform relative-accuracy guarantee. Truth never selects
estimator inputs, rows, settings or support status.

### Fixed noise sensitivity

Use position and velocity sensor standard deviation 0.002, seeds 0 through 7,
k=(0,0.3,0.9,4), mass=(0.5,2), the same four-record prefix and default grid:
64 prefixes, 256 records. Retain negative, unsupported and inaccurate outcomes.
Report counts and per-probe errors where a valid nonnegative estimate exists.
No success-rate threshold or noisy accuracy guarantee is preregistered.
The default noisy generator is unchanged; this exercise must not quietly
relabel it as noiseless or remove difficult seeds.

## Analytic bounds, separate from measured evidence

For exact oscillator samples let theta=h*sqrt(k/m). On the declared range,
theta^2<=0.02. Trapezoidal fitting gives

k_trap/k = 2*tan(theta/2)/theta.

Paired Simpson fitting gives

k_simpson/k = 3*sin(theta)/(theta*(2+cos(theta))).

Both ratios have limit one at zero. Each displayed identity holds across phases
and pooled windows sharing k/m and cadence (fixed mass), when the integrated
design is informative. A mixed-mass prefix has one theta_j per record. Its
pooled ratio is sum(W_j*R(theta_j))/sum(W_j), where W_j is that record's sum of
squared observed design rows and R is the applicable ratio above. The weights
are nonnegative, so the same maximum-bias bound holds by convexity. These
identities do not authorize correcting an estimate using the unknown true k.

A conservative continuous Simpson bound follows by defining
N(theta)=theta*(2+cos(theta))-3*sin(theta). At zero N, N' and N'' vanish, and
N'''=theta*sin(theta), between zero and theta^2 over this interval. Therefore
0<=N<=theta^5/60. Since 2+cos(theta)>=3-theta^2/2,

0<=1-k_simpson/k<=theta^4/[60*(3-theta^2/2)].

With k<=4, absolute quadrature coefficient bias is at most 8.919e-6.
The tighter endpoint value at k=4,m=0.5 is about 8.91008e-6; it is not the
only support for the continuous bound.

For nonnegative true and estimated coefficients the stable oscillator Green
kernel satisfies |sin(w*t)/w|<=t, including w=0. With identical initial conditions,

||x_est(T)-x_true(T)|| <= |delta_k|/m * (D*T^2/2 + V*T^3/6)
                     <= 24.6667*|delta_k|.

Thus the 1e-8 absolute coefficient floor contributes at most 2.4667e-7 vector
position error, and the conservative Simpson quadrature bound contributes at
most 2.2001e-4. Corresponding coordinate RMSE bounds are these values divided
by sqrt(2), since the report averages both coordinates. These bounds apply to
the exact-sample, continuous-oscillator calculation, not total RK4 error.

A preregistered counterexample prevents coefficient-only acceptance: at k=4,
m=0.5,h=0.05, the trapezoidal relative coefficient bias is about +0.167%, which
passes 1%. The axial-aligned radius-3 probe above has coordinate RMSE about
0.00633124, which fails 0.001. The paired-Simpson counterpart is about 8.44936e-6.
These are analytic planning calculations, not measured solver results.

## Recorded local evidence

Measured 2026-10-20 on Linux x86_64, Python 3.12.3, NumPy 2.5.3 and Pydantic
2.13.5. Preregistration: `5e524a10e4decbd362e779ffaf95d983a0083e3b`;
mixed-mass clarification: `f55d38fcecd5ed08c8d6ec73f21e70680569ba57`.
The unchanged matrices and thresholds preceded measurements.

Harness source: `a92bab9b5b7431bd26c55e720d5c1d4eff64ce55`,
[test_spring_domain.py](../tests/test_spring_domain.py), SHA-256
`2678116fd88e67f904237fd904ba354021331016cc7b71028f72db680a1a70b7`.
Its deterministic JSON report retains every case, configuration, public-prefix
hash, raw estimate/status, completed/failed counts, coefficient error and
individual probe RMSE. The 24 report entries stay aligned to the probe manifest;
failed predictions have null metrics and explicit failed indices. It is
synthetic calibration output, **not an
EvaluationReport or official score**. It writes no journals or private data.

### Noiseless finite matrix

All 63 primary prefixes (21 parameter pairs at each of three RK4 steps) meet
both predeclared criteria across all 1,512 probe evaluations. All seven
mixed-mass prefixes also pass, with 168 probe evaluations and worst RMSE
7.50131e-6. The maximum sampled errors below are Euclidean position/velocity
errors against exact trajectories on the four purchased-condition fixtures;
they are not extrapolation-predictor solver tests.

| RK4 step | Max sampled position error | Max sampled velocity error | Max coefficient effect from RK4 observations | Max total coefficient error | Worst per-probe RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.01 | 3.16841e-8 | 8.67008e-8 | 2.13456e-8 | 8.93142e-6 | 8.46960e-6 |
| 0.005 | 1.97432e-9 | 5.46226e-9 | 1.33381e-9 | 8.91141e-6 | 8.45062e-6 |
| 0.0025 | 1.23204e-10 | 3.42734e-10 | 8.33493e-11 | 8.91016e-6 | 8.44943e-6 |

The maximum exact-sample quadrature coefficient bias is 8.91008e-6 at every
step: reducing the internal solver step does not change observation spacing.
The RK4 coefficient effect is the difference between estimates using numerical
and exact samples, not total coefficient error. It improves about sixteenfold
per halving, while the fixed observation-quadrature bias remains.

The measured RMS residual difference
`(y_rk4-y_exact)-k*(g_rk4-g_exact)` has maxima 2.11099e-9, 1.31876e-10 and
8.24049e-12 at these three steps. These are finite-fixture RK4/roundoff effects,
not the separately declared 1e-14 perturbation stress. At the default step,
zero-stiffness fixtures recover exactly zero; the k=1e-8 fixtures have maximum
absolute coefficient error 1.29241e-16 and maximum probe RMSE 1.10207e-15.
Those measured values do not turn the absolute floor into a relative guarantee.

The preregistered exact-sample counterexample is reproduced: trapezoid returns
4.006680027 with worst RMSE 0.0063312404; Simpson returns 3.999991090 with
worst RMSE 8.4493556e-6. Both pass the coefficient criterion, but trapezoid
fails 21 of 24 probes. No failure is removed or relabeled.

### Weak excitation and numerical support

Of 48 physical weak-excitation prefixes, 34 are explicitly unsupported and
14 meet both accuracy criteria across their 336 probes. Unsupported cases
retain 816 failed probe outcomes; they do not receive invented predictions.
The worst supported RMSE is 8.46961e-6.

| Initial displacement amplitude | Supported / total | Minimum pooled G | Maximum pooled G |
| --- | ---: | ---: | ---: |
| 0 | 0 / 6 | 0 | 0 |
| 1e-12 | 0 / 6 | 2.36439e-14 | 1.41418e-13 |
| 1e-10 | 0 / 6 | 2.36451e-12 | 1.41421e-11 |
| 1e-8 | 0 / 6 | 2.36450e-10 | 1.41421e-9 |
| 1e-6 | 0 / 6 | 2.36450e-8 | 1.41421e-7 |
| 1e-5 | 2 / 6 | 2.36450e-7 | 1.41421e-6 |
| 1e-4 | 6 / 6 | 2.36450e-6 | 1.41421e-5 |
| 1e-2 | 6 / 6 | 2.36450e-4 | 1.41421e-3 |

The near-zero residual difference reaches 2.23212e-17 at amplitude 1e-8 and
2.03405e-15 at amplitude 1e-6. It reaches 2.03699e-14 at amplitude 1e-5 and
2.03706e-11 at amplitude 1e-2. The 1e-14 perturbation stress therefore **does
not bound all observed RK4 residuals**. It supports the predeclared numerical
guard independently of quadrature and discretization errors.

Separate boundary fixtures exercise G immediately below, at and above 1e-6
and signed residual stresses of 1e-14. Negative estimates remain negative
failures; they are never clamped to zero. A failed record remains in the
prefix hash/counts, a completed zero-design record contributes its zero rows
to N, and an all-failed prefix is rejected by the existing SpringFitInput
contract before estimation. Partial windows, mismatched configuration,
unsupported topology/mass, wrong public particle identity and purchased versus
prediction bounds have explicit rejection tests.

Finite public observation values can still overflow derived arithmetic.
Independent review found this edge outside the physical manifest; the harness
now explicitly fails nonfinite derived columns, reductions and coefficients.
It retains the public-prefix hash, row/probe counts and failure reason; an
unrepresentable raw coefficient or design RMS becomes JSON null, never zero
or an accepted model. A finite but extreme coefficient can also overflow
analytic prediction; each probe is attempted, failures retain null metrics,
and any failure prevents joint acceptance. Five overflow regressions verify
report serialization and all 24 outcomes. These repairs change no scientific
manifest or tolerance.

### Noise sensitivity: failures retained

All 64 prefixes and 256 records remain in the report. There are six negative
estimates and 58 valid nonnegative estimates. Only 13/64 prefixes meet the
joint accuracy criteria; coefficient-only acceptance would count 48/64.
This is a negative sensitivity result under the fixed seeds, not a violation
of a preregistered noisy-success guarantee.

| True k (evaluator only) | Negative estimates / 16 | Coefficient passes / 16 | Joint passes / 16 | Computed probes above 0.001 | Worst computed RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 6 | 0 | 0 | 73 | 0.0144729 |
| 0.3 | 0 | 16 | 2 | 115 | 0.0137608 |
| 0.9 | 0 | 16 | 5 | 115 | 0.0116662 |
| 4 | 0 | 16 | 6 | 103 | 0.00489382 |

There are 1,392 computed probe values, of which 406 exceed the RMSE bound,
plus 144 failed probes from the six negative estimates: all 1,536 outcomes
are accounted for. Zero-state probes are retained. No noisy prefix is silently
excluded on the basis of coefficient error or held-out accuracy.

### Reproduction and integration boundary

Use the existing locked environment from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider tests/test_spring_domain.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/test_spring_domain.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check .
PYTHONDONTWRITEBYTECODE=1 .venv/bin/mypy --cache-dir=/dev/null src tests examples
```

The second command recomputes the full report on stdout, including source hash,
environment, preregistration identities and per-probe errors. No output file,
new package, training GPU or hosted service is required.

The calibration suite has 204 passing cases and the full suite passed 817 tests.
Repository-wide Ruff and formatting passed (61 files), as did strict mypy
(33 checked files). Required Python 3.12/3.14 hosted CI and exact-head
independent review remain integration acceptance gates.

The finite results support the declared noiseless first-spring slice and its
fixed manifests. The continuous proof covers exact-sample quadrature only;
the finite RK4 evidence does not certify all continuous inputs or all platforms.
The default noisy generator remains unchanged and does not gain a blanket
accuracy guarantee. SP-04.a must implement the actual versioned fitter and
failure diagnostics. SP-04.b must separately validate production prediction,
including extrapolation and its integration error. SP-06.a owns independent
scoring, and I1 still requires a genuine purchased-observation-to-score path.
No entire R1 milestone or production-readiness gate closes through this report.
