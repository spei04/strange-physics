# GRID-Q1 fixture and reference foundation

This checkpoint is source-only. It supplies complete synthetic inputs and a finite reference
allocation for the existing proposed GRID-Q1 manifest. It does not contain an executable
qualification driver, accepted results, a calibrated discrepancy, MAP selection or a study run.

The protocol is the [immutable GRID-Q1 handoff](https://github.com/spei04/strange-physics/blob/08ce72b1c82be1d299e873d84f6ba184a6387da6/docs/FINITE_GRID_CALIBRATION_HANDOFF.md),
byte-identical to the reviewed handoff at progress commit `743ae63`. The executable base is main
`5819563bbef4b94c75aadb3c495c798dc7926876`; these are different source/progress branches.

## Fixed inputs

`tests/grid_q1_inputs.py` declares three histories, midpoint partitions with 64, 256
and 1024 cells over physical k in [0,4], and discrepancy scales 1/8, 1/4 and 1/2.
The cell prior mass is physical width divided by support width, hence 1/N.
These are proposed diagnostic settings, not scientifically justified defaults.

Each complete public-shaped bundle has one completed record, explicit zero observation
noise, duration 1/2, dt 1/64 and sample interval 1/2. The common physical space has one
canonical digest; distinct history labels, run IDs and operation IDs do not invent a
nonexistent space-ID field. The interior binary64 terminal-x label must be supplied from
a separately retained independent enclosure and one-rounding check. Fixture construction
does not authenticate that label or a purchase.

Only terminal x is an observation for this diagnostic. Terminal velocities are explicitly
tagged `unused-zero-placeholder` in the external fixture descriptor and set to zero to
satisfy the public record shape. For the excited interior case they are not physical
velocity observations. The records must not be presented as fully observed trajectories,
simulator output or fitted velocity evidence. This introduces no velocity-reference call.

## Finite reference allocation

`tests/grid_q1_reference.py` reuses the existing independent 80-coefficient, 100-digit
Decimal ODE/Machin/trigonometric math through six fixed named `EndpointOracle` instances.
The accepted old helper and its guards remain byte-identical. Instances are created once,
never reset, replaced or allocated in response to failure.

| Named allocation | Full-manifest work |
| --- | --- |
| Training including the one construction label | 12,097 lookups; 1,345 nontrivial series |
| Future, physically cached across histories | 4,032 lookups; 1,344 nontrivial series |
| Flat arithmetic | 4,032 exp; nine log |
| Boundary arithmetic | 4,032 exp; nine log |
| Interior arithmetic | 4,032 exp; nine log |
| Common constants and continuous flat moments | seven log; four trig; 128 Machin terms |

Every instance stays below the unchanged old limits: 16,000 lookups, 1,728 series,
5,500 exp, 5,600 log and four trig. The new aggregate is explicitly 16,129 lookups,
2,689 series, 12,096 exp, 34 log, four trig and 128 Machin terms. Unexcited training
accounts for 4,032 constant returns; exact-key cache hits account for 9,408 lookups.
The series count comprises 1,344 distinct midpoint coefficients at each of t=1/2
and t=1, plus the non-grid k=3/2 construction label. No initial-frame ODE calls occur.

The seven constant logs are three scale logs, three cell-mass logs and log(2*pi).
The other 27 logs are logs of direct positive finite sums. Reference normalization
uses unshifted Decimal exponentials and one direct sum, retaining maximum log weight
and shifted log evidence separately. It does not call the production normalizer.
Each joint log weight is bounded to [-32,4], 120 digits and exponent [-256,128] before
reference work. This conservative arithmetic guard contains this proposed profile's
single-record residual and prior range; it is not a new scientific tolerance.
Reference errors still need the protocol's explicit propagation/outward-bound checks.

Duplicate requested work is rejected; cache reuse is only by the unchanged oracle's
exact physical input key. A reference exception prevents further calculations.
Incomplete work cannot pass the exact final census. These construction dataclasses
are not the eventual persisted qualification report.

## Next implementation boundary

A separate reviewed source checkpoint must supply the disabled qualification driver and
bounded report schema: retain the interior label enclosure/rounding, construct nine actual
candidate ensembles, make and bind all 27 raw belief results, evaluate 4,032 future native
predictions, and apply all finite-arithmetic, continuous-cell, predictive, refinement and
sensitivity gates from the unchanged handoff. It must retain attempted, completed, failed
and unrun rows, reference counters, identity joins, errors, costs and actual output bytes.
The endpoint evaluator itself performs 12,096 fit predictions and 27 normalizations.
Total native predictions are 16,128 and requested frames 32,256. Each of the 12,096
finite posterior weights may be exponentiated once for actual predictive moments;
that work is separate from both reference and production-normalizer exponentials.

Purchased experiments, measured study-stage entries and publication commits are zero in
this diagnostic manifest. The existing measured stage dispatcher has no endpoint-belief
operation. An externally measured finite diagnostic needs no new publisher prerequisite;
it also cannot claim measured-study throughput or publication authority.

The local engineering gate passed at source `2a762cdc82ed08718cbdaf22d2c3f0ad00359cdd`:
configured format/lint checks, strict typing and all 24 synthetic cases (0.57 pytest seconds).
All 72 phases passed. The adapter checked replacement of the five real oracle methods before
every test body; source-reviewed test responses exercise construction, routing, bounds,
duplicate denial, incomplete census and failure retention without real oracle calculations.
The initial format-check failure and normalized-AST-equal style repair remain retained.
All 96 installed package files matched unchanged production source, and the complete reused
environment matched before and after. No numerical pack, simulator, provider, build, install
or environment change occurred. These checks establish foundation behavior, not GRID-Q1
accuracy, runtime fit or scientific calibration.

Numerical execution remains disabled pending source review, exact remaining driver census,
scientific/accounting and storage admission. No old unit allowance or oracle guard is
reset. Existing runtime storage guards, cumulative scientific limits and the unresolved
full-study capacity constraint remain unchanged.
