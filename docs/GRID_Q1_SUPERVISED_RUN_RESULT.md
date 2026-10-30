# GRID-Q1 supervised diagnostic result — 2026-10-30

**The one approved diagnostic passed its fixed numerical checks.** Independent
review accepted the retained scientific evidence, service closure and captured
execution intervals. Complete whole-operation cost accounting remains unresolved:
earlier assembly authoring/review, pre-anchor bootstrap and historical unknown
costs are preserved separately.

## Reproducible result identity

- Run: `grid-q1-cec936a2-supervised-v1`; exactly one GRID dispatch.
- Scientific source: [cec936a2a5a6534861eb9183861c4d6fcf931f67](https://github.com/spei04/strange-physics/commit/cec936a2a5a6534861eb9183861c4d6fcf931f67).
- Repair source: [8b16c7eba1da547f9594d620d9dae6e12173ffcd](https://github.com/spei04/strange-physics/commit/8b16c7eba1da547f9594d620d9dae6e12173ffcd).
- Authority: the owner's explicit approval of the [immutable supervised decision](https://github.com/spei04/strange-physics/blob/30bc815eafa1d38cd42a51a79804a1dcca99a2ce/docs/GRID_Q1_SUPERVISED_RUN_DECISION.md).
- Product report SHA-256:
  `8c15752b1a26de2ddccbdebaef394ce943f62d1bc5aa55e235389c0e956f50be`.
- Combined closeout SHA-256:
  `aac5fc2259330eb8c96cb6d7b3eb071dae36d035381e63518b4c6f45600916ae`.

Private evidence remains on `studio-agent`, indexed by
`ra-grid-q1-source-20261030/lead-supervised-final-outcome.json`.
This note publishes aggregate findings and identities, not private artifacts.

## What was checked

All three live controls qualified: normal exit, intentional nonzero exit and
timeout with a child that survives TERM. Invocation identities, actual CPU quota,
terminal accounting and empty control groups (cgroups) were verified before scientific
dispatch. Expected failed service states were retained.

The numerical diagnostic covered 27 fixed synthetic profiles: flat, boundary
and interior histories; grids of 64, 256 and 1,024 nodes; and likelihood scales
0.125, 0.25 and 0.5. All required checks passed. The retained report contains
142 artifacts, 48 completed operations, 144 event records, 18 refinement
comparisons and 18 sensitivity comparisons. Independent review rehashed every
artifact and verified unchanged source, installed package and environment.

Selected maxima from the retained report are below. Display values are rounded;
the report identified above retains full precision. Sensitivity comparisons
are diagnostic contrasts, not invariance requirements.

| Quantity | Largest reported value | Fixed limit |
| --- | ---: | ---: |
| Native future endpoint absolute error bound | 1.38804e-16 | 1e-12 |
| Normalized-log error bound | 4.02198e-15 | 1e-9 |
| Required 256-to-1,024 refinement: total variation | 4.25546e-6 | 0.001 |
| Required refinement: mean difference | 3.70064e-6 | 0.0005 |
| Required refinement: variance difference | 2.72973e-6 | 0.001 |
| Finest-grid continuous total-variation certificate | 0.0078125030 | 0.0081 |
| Finest-grid continuous variance certificate | 0.0510568801 | 0.056 |

The finest-grid continuous mean and second-moment certificate maxima were
0.0166015685 and 0.0175781310, below their respective 0.018 and 0.019 limits.
The largest required refinement differences occurred in the boundary history
at scale 0.125. These results support numerical resolution under the stated
synthetic reference assumptions.

## Execution and accounting

| Observation | Recorded result |
| --- | ---: |
| Inner controller and children CPU / wall | 99.203574 s / 198.875203 s |
| GRID service CPU, including controller | 99.331348 s |
| Three qualification services, combined CPU | 0.373586 s |
| All four services, combined CPU | 99.704934 s |
| Captured client / server intervals | 269.621119 s / 252.189906 s |
| Conservative CPU bound for those host intervals | 3,704.970814 CPU-s |
| Retained logical files plus full terminal allowance | 34,038,996 bytes |

The observed host intervals were below 2,400 seconds each, with unchanged
maximum CPU counts and boot identities. Their conservative CPU bound was below
the 33,600 CPU-second reservation. Output, including the full 256 KiB terminal
allowance, was below 104 MiB. All owned services and controller children closed;
post-exit observations showed no queued jobs. The shared transport was handed
back, without claiming that it terminated.

Controller CPU is included in service CPU; these observations are not additive.
The controller's printed legacy 30 CPU / 90 wall markers are not measurements
of actual overhead. The host bound includes idle and unrelated activity and is
not a bill.

New run-root/admission/export materialization occurred after the immutable host
anchors. Earlier assembler authoring/review and pre-server-anchor bootstrap
were outside those intervals; their unmeasured remainder is explicitly unknown.
The captured execution envelope is accepted. **Complete whole-operation and
historical accounting is not established.** The original failed attempt,
its reservation and all unknown costs remain retained without refund, reset
or reuse. This opportunity is consumed; no retry, additional run, merge,
deployment, installation or purchase occurred.

## Limits and next scientific gate

This is a finite-grid arithmetic and resolution result for the fixed profiles.
It does not establish the adequacy of the Gaussian discrepancy model,
calibrated uncertainty, generalization, experiment-selection quality,
law-change recovery or production readiness. Terminal velocities in these
fixtures are explicitly unused zero placeholders.

Next, review discrepancy assumptions and the numerical profile, then define
and freeze disjoint RA-N03 calibration fixtures before accepting calibration
or downstream selector comparisons. Laplace analytic validation may proceed
in parallel where contracts match; its comparative audit still requires those frozen RA-N03 fixtures, the
same frozen cells, prior and likelihood plus preregistered predictive,
ranking, boundary and misspecification checks. No further numerical allocation
is implied by this result.
