# Local linear spring fitting

The local API is `fit_linear_spring(request: SpringFitInput, config:
SpringFitConfig) -> SpringFitResult`. SP-04.a implements this API separately
from the frozen [SCI v1 contracts](SCI_CONTRACT.md). The additive
[configuration/result schema](../contracts/fitting.schema.json) and
[synthetic interface examples](../contracts/fitting.examples.json) describe its
boundary. The examples are interface vectors, not scientific results.

The input contains exactly the purchased prefix through its declared index and
a configuration digest. The caller supplies the actual configuration too.
The fitter compares its canonical SHA-256 with the request before numerical
work. The fixed v1 configuration binds the algorithm, selection, window layout,
sampling and mass/action limits, excitation floor, numerical work limits, noise
policy and coefficient policy. Every field, including defaults, participates in
the existing Python canonical JSON profile. V1 settings cannot be silently
retuned; an alternative profile requires an explicit version decision.

The result keeps the unchanged `LinearSpringModel` separate from diagnostics.
A `fitted` status means that a finite nonnegative numerical estimate was
computed under a **stationary shared zero-rest linear spring assumption**.
Public prefix metadata cannot establish that assumption. Fitted does not claim
ground-truth accuracy, identifiability of a general physical law, uncertainty
calibration, supported prediction, or an independent score.

Diagnostics bind the entire prefix (including failed records), actual and
requested configuration digests, deterministic completed-record selection,
counts, design RMS and raw estimate when representable. Every complete paired
window and both coordinates count, including zero rows. Failed records remain
in provenance and counts but contribute no fit rows. The result binder checks
the actual input and configuration, and the unchanged SCI model binder checks
model provenance. Schema validation alone cannot prove those relationships. The result binder
validates provenance and shape; it does not recompute the coefficient or prove
numerical authenticity. A caller can construct a shape-valid artifact, so
trust in an executing fitter is separate from serialization validation.

All legal declared observation noise is consumed without reweighting,
denoising or selecting favorable records. Nonzero declared noise is explicitly
flagged and no accuracy claim is made. A finite nonnegative estimate above the
calibrated coefficient interval [0,4] is retained and flagged outside that
interval. It is not projected to the boundary or granted prediction support.
A finite negative estimate is retained only in failure diagnostics, with no
model. Unrepresentable numerical diagnostics are null, never JSON infinity.

Explicit failures distinguish configuration mismatch, unsupported scientific
domain, insufficient excitation, numerical failure and a negative estimate.
The scientific domain and evidence are bounded by [SP-03.b](SPRING_DOMAIN.md);
they are narrower than the general SDK's valid messages. Prefix parsing and
hashing are local work proportional to the supplied data. The 400,000 scalar
row limit bounds numerical fitting work; it is not a hosted request-size or
hostile-code security boundary.

The [local analytic predictor](PREDICTION.md) is a separate API. Independent
evaluation, uncertainty estimates and the full I1 scientific checkpoint remain
separate work. No evaluator labels, private world
parameters, journal state or future records enter this fitter.

## Calling the fitter

Parse an observation bundle through the public contract, explicitly supply the
fixed configuration, and retain the whole result:

```python
from pathlib import Path

from strange_physics.contracts import ObservationBundle
from strange_physics.fitting import fit_linear_spring
from strange_physics.fitting_contracts import SpringFitConfig
from strange_physics.research_contracts import SpringFitInput, message_sha256

observations = ObservationBundle.model_validate_json(Path("observations.json").read_text())
config = SpringFitConfig()
request = SpringFitInput(
    observations=observations,
    through_index=len(observations.records) - 1,
    fit_config_sha256=message_sha256(config),
)
result = fit_linear_spring(request, config)
Path("spring-fit.json").write_text(result.model_dump_json(indent=2) + "\n")
```

The supplied bundle must already be exactly the purchased prefix; the fitter
does not slice away future records or silently discard failed records. An empty
or all-failed prefix fails the existing input contract before fitting. Ordinary
domain, support and numerical failures return a serializable result with no
model. Invalid message shapes fail public contract validation.

## Fixed domain and numerical method

The v1 profile accepts one mobile particle joined to one static anchor, with
either connection orientation. Anchor norm is at most 0.5; each purchased
initial position, velocity and impulse has norm at most 2, 2 and 1 respectively;
mass is in [0.5,2]. These checks include failed actions, preserving the same
prefix domain as SP-03.b. It uses duration 2 seconds, nominal observation cadence
0.05 seconds, and one of the calibrated integration steps 0.01, 0.005 or 0.0025
seconds. Public core validation already checks identities, order, observation
shape and times. The fitter additionally rejects unsupported topology or
sampling, including a partial final window.

Each completed record supplies 41 frames. For each pair of intervals with
frames 0/1/2, 2/3/4, ..., 38/39/40, displacement from the known anchor is
integrated using Simpson's rule. For each coordinate:

```text
g = -h * (r_first + 4*r_middle + r_last) / (3*record_mass)
y = v_last - v_first
k_hat = sum(g*y) / sum(g*g)
G = sqrt(sum(g*g) / N)
```

The impulse is already represented in the purchased velocities, including frame
zero; the fitter never applies it again. N counts both coordinates of every
window, including zero rows: 40 scalar rows per completed record. Mixed masses
use their own design columns, and all rows share one estimated coefficient.
Products are checked for finite values, summed with `math.fsum` within each
record, then summed in public record order. Temporary numerical lists contain
at most 40 products per record plus two totals per completed record. They do
not materialize another complete trajectory array.

The fixed eligibility floor is G >= 1e-6. This measures integrated-column RMS
with mass included, not a rank-one condition number or a claim of general
identifiability. The justification and limitations are in
[the calibrated domain](SPRING_DOMAIN.md). No coefficient truth or evaluation
probe is used to select rows or determine this threshold.

The canonical configuration digest is
`50d7cfb3acf86c3c6415add0766e2ce5494943a22044d25e92749f355d3a2286`.
JSON booleans are not accepted in fixed integer configuration fields. Successful
models retain the existing SCI model format and the full prefix/configuration
identity. Changing a failed operation changes the prefix digest even if the
coefficient and completed selection remain identical.

## Failure accounting and evidence

Configuration mismatch precedes domain checks and numerical work. A preflight
failure reports zero scalar rows; completed and failed prefix counts remain
available. Once the domain is supported, scalar rows describe the entire
eligible manifest even if arithmetic fails before the end. A failure never
reports a successful fit from the surviving rows.

Finite public observations can still overflow derived columns, products,
reductions or the coefficient. Those paths return `numerical_failure`; numbers
that cannot be represented are null. Representable finite negative estimates
return `negative_estimate` with the raw value retained. Zero stiffness with
excitation is a fitted estimate; a zero design is insufficient excitation.

Production verification includes independent continuous oscillator labels over
the seven calibrated coefficients and three masses, a mixed-mass prefix, a
hand-computed weighted fit with zero-coordinate rows, below/at/above excitation
thresholds, actual simulated public observations at all three steps, failed
prefix provenance, domain/configuration rejection and finite-input overflow
regressions. No production code imports the calibration test harness.
Reproduce focused checks with:

```sh
.venv/bin/pytest tests/test_fitting.py tests/test_fitting_contracts.py
.venv/bin/python scripts/validate_contracts.py
```

These checks establish the implemented local fitting behavior. The broader
finite calibration evidence, its noisy failures and its analytic-versus-finite
limits remain recorded in SP-03.b. They do not make this a predictor, evaluator,
hosted service or completed I1 checkpoint.
