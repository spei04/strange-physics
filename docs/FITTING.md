# Local linear spring fitting

The local API is `fit_linear_spring(request: SpringFitInput, config:
SpringFitConfig) -> SpringFitResult`. SP-04.a adds the implementation separately
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
model provenance. Schema validation alone cannot prove those relationships.

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

Prediction, independent evaluation, uncertainty estimates and the full I1
scientific checkpoint remain separate work. No evaluator labels, private world
parameters, journal state or future records enter this fitter.
