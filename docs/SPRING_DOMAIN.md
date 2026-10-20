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

Both ratios have limit one at zero. These identities hold across phases and
pooled windows when the integrated design is informative. They do not authorize
correcting an estimate using the unknown true k.

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

## Measurement and integration status

Preregistered; implementation and measured results pending. The report will keep
exact-sample quadrature, actual RK4-observation bias, refinement, floating-point
stress and noise outcomes distinct. Tests must also cover mass/order/topology,
partial-window rejection, failed-record accounting and absence of hidden inputs.
Exact-source local tests, full CI and independent review are required before
SP-03.b is accepted. Neither this document nor finite successful fixtures close
SP-04.a, SP-04.b, SP-06.a, I1 or the full R1 milestone.
