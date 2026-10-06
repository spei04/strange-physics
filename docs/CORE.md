# Implemented research core

The first milestone supplies reusable numerical and persistence contracts. It
does not supply a production service, a trained investigator or benchmark results.

## Package boundaries

| Module | Responsibility |
| --- | --- |
| `contracts` | Frozen Pydantic messages, identity/shape/range validation and JSON schemas |
| `laws` | Force protocol, explicit versioned plugin registration and three reference laws |
| `worlds` | Private law/noise/change configuration and development world fixtures |
| `simulation` | Fixed-step float64 RK4 and independent Gaussian observation noise |
| `journal` | Transactional local experiment reservations, outcomes and checkpoints |
| `session` | Trusted local execution adapter; public observation export |
| `sdk` | Agent protocol, common calibration, random selector and recovery driver |
| `cli` | Local investigation, resume, observation validation and schema export |

Python dependencies are locked in `uv.lock`; installation owns its files rather
than hard-linking mutable dependencies from another checkout. The first core uses
NumPy and Pydantic. SciPy/FastAPI are added only when their fitting/service
components need them.

## Experiment and numerical contract

An experiment sets each movable particle's position, velocity and mass and may
apply one impulse to one movable particle at time zero. Particle identities and
order must match the public structure. Each world exposes its legal bounds and
sampling settings. Unknown fields, nonfinite numbers, invalid graph edges,
out-of-range initial conditions and misaligned sampling grids are rejected.

The default is 2 simulated seconds, a 0.01-second integration step and 41 samples
at 0.05-second spacing, including the initial state after the impulse. These
numbers are development defaults pending the scientific calibration milestone.
The integrator rejects nonfinite state and absolute coordinates/velocities over
1e6; it does not silently clip results. Observation noise is applied to the
recorded samples, never fed back into the dynamics.

Default legal radii are 2 for position/velocity and 1 for impulse; masses range
from 0.5 to 2. A request cannot modify duration, sampling or noise to buy more
measurements for one experiment. A law regime remains fixed during integration.
`change_after = 20` means the first 20 zero-indexed experiments (0 through 19)
use the initial law, and experiment 20 uses the replacement. Resets and process
restarts preserve the regime index.

Pairwise spring and radial forces are equal and opposite. Anchors remain fixed,
so an anchored system need not preserve the movable particles' total momentum.
Velocity drag dissipates energy; its transverse component rotates velocity.
See [law equations](LAWS.md).

## Agent interface and checkpoints

An agent provides an immutable configuration/version identity, initial JSON
state, a `select(view)` function, and `observe(view, result)` producing updated
JSON state. The view contains the public space, purchased history and declared
state. The local driver runs the common calibration experiments before asking
the selector for adaptive actions. Calibration consumes the same total budget.

An agent must derive decisions from the supplied view, including explicit random
state when needed. Arbitrary hidden Python object state is not recoverable. Paid
model calls will need a durable provider gateway and their own operation records;
the current local driver does not implement that gateway or retry those calls.

Checkpoints cover a completed prefix, are bounded to 256 KiB of JSON, and cannot
move backwards or overwrite an already-committed checkpoint at the same index.
When a result committed before a crash but its checkpoint did not, the driver
replays that recorded result to `observe` before selecting more experiments.
It does not buy the same experiment again. Bulk model artifacts remain future
work. See [checkpoint semantics](CHECKPOINTS.md).

## Journal identity, failure and durability

The local adapter reserves a unique operation ID and experiment index before
simulation. A valid reservation consumes one budget slot, including a simulation
failure. Repeating the same ID and request returns the stored outcome; using the
ID for a different request fails. Invalid requests consume no slot. A crash
after reservation leaves pending work that can be resumed deterministically.

SQLite uses full synchronous commits and transactionally allocates indices.
Concurrent retries produce one logical recorded experiment; this local adapter
can still compute the same pending simulation twice. The hosted coordinator
must add leases/fencing and distributed reconciliation. Do not describe this as
exactly-once execution or exactly-once provider billing.

Plugin failures return a public `simulation_failed` code and remain in the run.
Private diagnostics store the exception type and stack locations, but not the
exception message or local variables that might contain private parameters.
The journal retains the world/request/runtime identity for reproduction.

The runtime fingerprint includes core Python source, Python patch version,
NumPy/Pydantic versions and declared plugin implementation identities. Resume
rejects mismatches. External plugin authors must update their identity when
behavior changes; arbitrary external source is not automatically captured by
the local adapter. Hosted immutable image digests will strengthen that contract.
Cross-platform bit-for-bit numerical identity is not asserted by this milestone.

## Data boundary and current limits

`session.sqlite` contains private law parameters, noise seed, change boundary and
agent state. It is created owner-readable and ignored by Git. Never publish it
as a replay artifact. `observations.json` contains a versioned public space,
requests, outcomes and numerical trajectories with no private world definition.
The export includes a runtime fingerprint but is not yet a complete scored-run
provenance manifest. A customer's observation record is still private by default.

Local agents/plugins execute in the calling Python process. Typed views and
separate public/private schemas prevent accidental export; they are not a security
boundary against malicious code with filesystem or interpreter access. The
accepted GKE Sandbox/Cloud Run separation, authentication and workspace access
control are required before accepting untrusted hosted packages.

The random investigator does not fit or discover a model. The reference worlds
and common calibration generator are development fixtures. Shared fitting,
uncertainty, active selection, held-out scoring, LLM calls, the browser UI and
cloud deployment remain the next implementation milestones.
