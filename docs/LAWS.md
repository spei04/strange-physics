# Initial law families

These are implemented dimensionless reference laws for controlled identification. They are
not a faithful electromagnetism or materials simulator. For position vector
`x`, velocity `v`, known mass `m`, and force `F`, integrate `dx/dt = v` and
`dv/dt = F/m`. Reference fixtures place an anchor at the origin; custom structures
may choose other fixed positions. There are no collisions or walls.

The formulas below describe single-particle reference cases. For spring and
radial pair interactions, replace `x` with `x_i - x_j` on every visible undirected
connection, add the resulting force to particle `i`, and subtract it from `j`.
Forces on fixed anchors are discarded by the integrator. Springs have zero rest
length in this version. The velocity law acts independently on each movable
particle. Each regime has one coefficient set shared across its applicable
particles/connections; object-specific coefficients are not implemented.

The structure supports one to eight movable particles and up to eight anchors.
Anchor positions and connection topology are public. The active force family,
coefficients, observation seed and change boundary stay in the private definition.

| Family | Force | Useful interventions | Example hidden change |
| --- | --- | --- | --- |
| Spring | `F = -(k1 + k3 * dot(x,x)) * x` | Vary displacement and mass; excite small and large amplitudes | Activate a cubic restoring term |
| Magnet-like radial field | `F = s * k * x / (dot(x,x) + eps²)^((p+1)/2)` | Vary distance and direction; distinguish field exponent from strength | Attraction becomes repulsion |
| Velocity force | `F = -(c1 + c3 * dot(v,v)) * v + omega * R(v)` | Vary speed and direction; include nonzero velocity | Activate transverse deflection |

`R(vx, vy) = (-vy, vx)`. Spring and drag coefficients are nonnegative in the
initial bounded domain. Radial polarity `s` is -1 or +1; `eps` is a known positive
softening radius. Far from the origin, radial force magnitude scales as `r^-p`.
The transverse velocity term does no instantaneous work because `v dot R(v)=0`.

Mass and impulse are known interventions. An initial impulse `J` changes velocity
by `J/m`. Initial conditions are reset on every experiment while the hidden law
regime persists. The law changes only between experiments in the first version;
absolute simulation time within an experiment cannot reveal the change schedule.

## Numerical choices

Use RK4 with fixed step 0.01 over 2 seconds; save observations every fifth step.
Keep the same observation times and integration accuracy for every method. The
world's deterministic trajectory and independent Gaussian sensor noise are
separate. Initial observations are measured after the impulse.

Bound both legal interventions and generator coefficients. Check representative
and boundary conditions against a smaller timestep before freezing a suite.
The implementation rejects nonfinite state and raises a simulation error rather
than clipping motion into apparently valid data. Consumed experiments stay
consumed if integration fails. Noisy sensor measurements may fall outside the
legal range of initial conditions; do not clip those measurements.

## Identifiability limits

Small displacements make a cubic spring hard to distinguish from a linear one.
Low-speed experiments cannot reveal nonlinear drag. A narrow distance range
confounds radial exponent with field strength. Zero velocity hides transverse
forces completely. These ambiguities motivate active experiment selection.

The planned controlled study evaluates recovery inside a disclosed function
library. The separate discovery track accepts user-defined predictive models.
The fitter, predictor evaluation and scored suites are not implemented yet; the
current random investigator does not claim to recover equations.
