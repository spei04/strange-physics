# Independent analytic physics fixtures

SP-03.a extends deterministic regression evidence for the existing simulator.
It does not ratify a scientific domain, the default grid over every legal input,
coefficient-recovery tolerances, a fitter, a predictor or an evaluator. The
separate [first-spring calibration](SPRING_DOMAIN.md) records SP-03.b domain,
quadrature, solver and noise evidence. Study distributions, production
force implementations, integration code and dependencies are unchanged.

The fixtures live in [test_analytic_physics.py](../tests/test_analytic_physics.py).
All pre-existing [physics assertions](../tests/test_physics.py) remain intact,
including explicit nonfinite-force failure and observation-noise separation.
New analytic trajectories have zero observation noise. Known parameters belong
to synthetic test fixtures; no private run or journal is exported.

## Independent references

The references use scalar/complex closed forms and hand-calculated quantities.
They never obtain expected trajectories from production forces or another
numerical integration of those forces.

- **Spring:** with fixed anchor position `a`, mass `m`, stiffness `k`,
  initial position `x0` and velocity `v0`, set `w = sqrt(k/m)`.
  Then `x(t) = a + (x0-a) cos(wt) + v0 sin(wt)/w` and
  `v(t) = -(x0-a) w sin(wt) + v0 cos(wt)`.
  The explicit `k=0` branch is ballistic. Complex coordinates represent the
  two independent spatial axes, not a change to the physical model.
- **Linear drag and transverse force:** for force `-c v + kappa R(v)`,
  `lambda = (-c + i kappa)/m`, `v(t) = v0 exp(lambda t)` and
  `x(t) = x0 + v0 (exp(lambda t)-1)/lambda`.
  The zero-rate branch is ballistic. `kappa` is force per velocity; the
  angular rate is `kappa/m`. Signed rotation and drag-plus-rotation are tested.
- **Pure cubic drag:** for force `-c3 |v|^2 v`, let
  `q = c3 |v0|^2/m` and `s = sqrt(1+2qt)`.
  Then `v(t) = v0/s` and `x(t) = x0 + 2t v0/(s+1)`.
  The rationalized integral avoids subtracting nearly equal square roots.
- **Constant force and impulse:** a test-only plugin supplies a constant force.
  The independent reference uses `v_after = v_before + J/m` for the named
  target only, then `v(t)=v_after+Ft/m` and
  `x(t)=x0+v_after*t+Ft^2/(2m)`. The first sample must already include the impulse.

Force tests use hard-coded vector results, including nonlinear terms and graph
accumulation, to complement the trajectory oracles. Central-force tests check
translation, reversed edge orientation and equal/opposite reactions. Proper
rotation covariance covers spring, radial and velocity laws in both forces and
trajectories. Reflection symmetry is not asserted for a fixed signed transverse
coefficient.

## Fixture domain and tolerances

The analytic spring matrix uses masses 0.5, 1 and 2; stiffnesses 0, 0.5 and 4;
a translated anchor; nonzero two-dimensional displacement and velocity; and
two seconds at `dt=0.01`. Velocity fixtures cover zero rates, linear drag,
both rotation signs, combined drag/rotation, and cubic drag at masses 0.5 and 2.
The exact finite fixture inputs are retained in the test parametrizations.

The highest-frequency analytic rotation case has `kappa=3, m=0.5`
(angular rate 6) and deliberately uses `dt=0.005`. This is **not** evidence that
the default `dt=0.01` meets the same bound throughout the legal domain.
Every fixture preserves the published sampling-grid validation.

All component-wise analytic position/velocity comparisons use absolute tolerance
`2e-7`, relative tolerance zero. This bound was declared before execution and
was not relaxed after a failure. It is a regression limit for these smooth,
bounded fixtures. Small RK4 steps give fourth-order global error; the separate
refinement tests require more than tenfold error reduction per step halving,
allowing margin around the asymptotic factor of sixteen. They use actual analytic
error across the trajectory, not differences between two numerical solutions.

Other limits have separate purposes:

| Assertion | Absolute bound / requirement |
| --- | --- |
| Constant-force position/velocity and targeted impulse | `2e-13`; quadratic/linear reference, no truncation error expected from RK4 |
| Hand forces, reciprocity, graph/translation and instantaneous work | `1e-13`; floating-point algebra |
| Rotated trajectories and closed-pair momentum/center of mass | `1e-12`; accumulated floating-point algebra |
| Spring energy drift at fine step | `1e-8 * max(1, initial_energy)`, plus more than eightfold refinement |
| Pure transverse energy drift at fine step | `1e-8 * initial_energy`, plus more than eightfold refinement |
| Drag energy with either rotation sign | Strict decrease between recorded frames for the stated nonzero-velocity fixtures |

These are not universal error bounds, and successful synthetic fixtures do not
establish identifiability under noise or changes. A failing case requires
investigation and numerical justification, not arbitrary tolerance relaxation.

## Conservation and failure boundaries

Momentum and center-of-mass tests use a closed pair of movable particles with
unequal masses. Anchored systems exchange momentum with their fixed supports;
no movable-system momentum conservation is asserted for them.

For static anchors, spring energy is
`m |v|^2/2 + k1 |x-a|^2/2 + k3 |x-a|^4/4`.
RK4 is not exactly energy preserving. Tests bound the maximum drift across the
trajectory and check improvement from `dt=0.02` to `0.01`. Pure transverse
fixtures similarly check numerical energy drift from `0.01` to `0.005`.
The exact continuous work identity `v dot kappa R(v)=0` is tested separately.
Adding nonnegative drag dissipates kinetic energy; it does not preserve it.

Malformed force shape raises `SimulationError` rather than producing a
trajectory. Existing nonfinite-force assertions remain unchanged. The local
plugin protocol is trusted Python; these tests do not establish hostile-code
isolation, and no failure is clipped into apparently valid observations.

## Recorded local evidence

Measured 2026-10-20 on Linux x86_64, Python 3.12.3, NumPy 2.5.3 and Pydantic
2.13.5. Test source: `ea3ebf12fa90ad415f970d5127dc1dc15a667ae8`.
The values below were captured from the test oracles and local energy/error
arrays during the full-suite run. Complex error is the Euclidean norm in two
dimensions, so these maxima also bound each individual coordinate error.

| Analytic matrix | Largest position-or-velocity error |
| --- | ---: |
| Spring, including zero stiffness and translated anchor | 6.0121e-8 |
| Linear drag / signed rotation / combination | 6.5304e-8 |
| Pure cubic drag | 6.3751e-10 |

| Refinement fixture | Error at 0.05 | Error at 0.025 | Error at 0.0125 | Reduction factors |
| --- | ---: | ---: | ---: | --- |
| Oscillator | 4.4137e-6 | 2.7262e-7 | 1.6927e-8 | 16.19, 16.11 |
| Linear drag | 5.0714e-9 | 3.1172e-10 | 1.9320e-11 | 16.27, 16.13 |
| Rotation | 1.6665e-6 | 1.0416e-7 | 6.5104e-9 | 16.00, 16.00 |
| Damped rotation | 5.7414e-7 | 3.5293e-8 | 2.1875e-9 | 16.27, 16.13 |

| Energy fixture | Coarse maximum drift | Fine maximum drift | Reduction |
| --- | ---: | ---: | ---: |
| Linear spring | 4.1331e-11 | 1.2920e-12 | 31.99 |
| Linear plus cubic spring | 3.0989e-10 | 1.7241e-11 | 17.97 |
| Pure transverse, worst of both signs | 2.1051e-8 | 6.5806e-10 | 31.99 |

The first focused run passed **64 tests**, including **53 new cases**. The full
suite passed **613 tests**. Repository-wide Ruff and formatting passed (59
formatted files), as did strict mypy (32 source files). The documented diagnostic
also reproduced the measurements and passed all 53 new cases. These are local
checks; required Python 3.12/3.14 hosted CI and exact-head peer review remain
integration requirements. None of these counts represents fitted-model,
generalization, recovery, hosted-service or benchmark evidence.

## Reproduction

Use the repository's existing locked environment. No additional dependency is
needed. Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider tests/test_analytic_physics.py tests/test_physics.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check .
PYTHONDONTWRITEBYTECODE=1 .venv/bin/mypy --cache-dir=/dev/null src tests examples
```

To inspect the recorded quantities without changing the test implementation,
this bounded diagnostic prints the analytic errors, refinement errors and
energy drifts from their executing test frames. It writes no result files:

```python
import json
import sys
import pytest


def capture(frame, event, result):
    if event != "return" or not frame.f_code.co_filename.endswith("tests/test_analytic_physics.py"):
        return
    name, values = frame.f_code.co_name, frame.f_locals
    if name == "_assert_oracle":
        error = frame.f_globals["_oracle_error"](values["trajectory"], values["oracle"])
        print(json.dumps({"test": frame.f_back.f_code.co_name, "max_error": error}))
    elif name == "test_analytic_error_decreases_with_timestep":
        print(json.dumps({"kind": values["kind"], "errors": values["errors"]}))
    elif name in (
        "test_conservative_spring_energy_drift_is_bounded_and_refines",
        "test_transverse_energy_drift_is_bounded_and_refines",
    ):
        print(json.dumps({"test": name, "drifts": values["drifts"]}))


class Measurements:
    def pytest_runtest_call(self, item):
        sys.setprofile(capture)

    def pytest_runtest_teardown(self, item):
        sys.setprofile(None)


raise SystemExit(
    pytest.main(
        ["-s", "-p", "no:cacheprovider", "tests/test_analytic_physics.py"],
        plugins=[Measurements()],
    )
)
```

The capture code is diagnostic instrumentation, not a production API or a second
scorer. The test's closed-form references and acceptance assertions remain the
authority. The separate [SP-03.b calibration](SPRING_DOMAIN.md) declares the first-spring
domain and joint coefficient/prediction criteria; it keeps finite numerical
evidence distinct from analytic bounds and production-fitting acceptance.
