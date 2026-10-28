# Bounded scientific demo

This cloud-only example connects the existing four-purchase I1 workflow to a
separate terminal-x belief diagnostic over the **same actual observations**.
It uses the installed package, not an editable source import. There is no
server, provider, selector, optimizer or new scientific profile.

## Run once from the existing cloud checkout

Use the reviewed source commit and its matching installed wheel. Keep the
output parent owner-private (0700), outside the checkout; the final output
directory must not exist. The example checks the clean Git head and every
installed package source file before computation.

~~~sh
cd /home/serenapei/experiments/strange-physics-worktrees/identity
.venv/bin/python -I -B examples/bounded_scientific_demo.py \
  --source-commit REVIEWED_COMMIT \
  --output /home/serenapei/.local/state/strange-physics-evidence/DEMO_PARENT/run \
  --cells 16 --discrepancy 0.25
~~~

Replace REVIEWED_COMMIT with the reviewed full commit and DEMO_PARENT with the
allocated private run directory. The finite runner must retain overall CPU,
wall time and cumulative bytes, enforce its declared limits, and stop without
retry on failure. This example checks its 64 MiB output ceiling at stage
boundaries; it is not the durable study budget authority or a filesystem quota.

The five CLI entries are exactly the commands in
[the I1 runbook](LOCAL_SCIENTIFIC_WORKFLOW.md#frozen-execution-sequence), invoked
through their public main function in one process:

1. Purchase four fixed calibration experiments from the stationary, noiseless,
   one-particle seed-7 spring.
2. Fit only the purchased public observations.
3. Prepare the fixed 24 held-out requests; no outcome chooses the requests.
4. Predict all 24 trajectories, each with 41 frames.
5. Score independently from the private Journal, retaining every per-probe RMSE.

A scored result can miss the numerical target. The example therefore checks
all 24 RMSE values against 0.001 in addition to the score's target flag;
score-spring exit zero alone does not establish that target.

The separate endpoint step enumerates 16 midpoint coefficients on the full
supported [0,4] interval, using uniform physical-k cell mass and discrepancy
0.25. Both settings are explicit **illustrative software choices**, not
calibrated measurement noise or an accepted study profile. The native
candidate input retains the original four-row bundle and attempt identity.
It does not relabel the legacy fitted model, choose a MAP model, alter the
held-out predictions, or purchase more data. Zero declared observation noise
does not imply zero discrepancy.

## What to inspect

- REPORT.md: source and conditions, fitted coefficient, all 24 predicted
  endpoints and RMSE values, and a separately
  labelled table of all 16 native normalized log weights. It contains only
  synthetic-development aggregate/derived results, not private world or Journal payloads.
- summary.json: actual identities, target result and belief status.
- run/observations.json and private run/session.sqlite: actual purchases.
- run/fit, run/evaluation, run/predictions and run/score: original typed
  inputs/results and raw-hash completion manifests, including private labels.
- belief/input.json and belief/result.json: exact raw input and output;
  their bounded structural binder is checked without repeating forwards.
- runtime.json, command-0.json through command-4.json, and completion.json:
  observed source/runtime/package bytes, CLI outcomes and file hashes.
  Hashes provide identity, not publication permission or numerical authenticity.

Directories/files are private; existing destinations are never overwritten.
A failed stage leaves partial results for diagnosis with no automatic retry,
replacement probes or filtering. Completion is published after all outputs,
and distinguishes artifact completeness from the numerical target.
Exit 0 means the full demo completed, all 24 development targets passed, and
the finite belief normalized. Exit 1 retains a complete but unsuccessful
scientific/diagnostic outcome; exit 2 retains a stopped partial run where possible.

## Verified development run

The example completed once at source
fab69a44e14e86b76476333ae98d4687034b5769, tree
d7aae8c95ca6588916e8d9269ecbebf62bf36632. Four actual observations produced
fitted k=0.6750572721112501; all 24 fixed held-out probes passed the 0.001
RMSE target, with maximum RMSE 3.154199886178306e-8. The separate illustrative
16-cell / discrepancy 0.25 endpoint diagnostic normalized. Independent
readback checked every displayed endpoint, score and belief weight against
the retained artifacts without rerunning the experiment.

The private run retained 28 files (742,139 bytes), including REPORT.md
(SHA256 a09d6375fd66c073d9f17bd7df0992badb72ad92627538bf075718a8505f8aec)
and completion.json
(SHA256 bf6bd94ab5fe6d4200a3b3bb30d3f0b95d196d7a1d4efef58837be9a2f8c6111).
Observed demo child CPU and wall time were 2.329644 and 2.198229 seconds.
The source-specific local gate also passed all 20 focused tests, configured
typing, lint/format, offline archive checks, and exact 96-file source/wheel/
sdist/installed parity. Its initial test-import typing failure remains in
the cumulative record and ran no experiment. See
[the execution record](EXECUTION_LOG.md#2026-10-28--bounded-demo-integration-and-validation)
for delivery status. These values describe this fixed development run.

The terminal-x component's accepted software tests include exact finite-sum
references and unexcited continuous predictive moments. They also show a
specific 1024-node [0,4], discrepancy 1e-6 computation that normalizes yet is
demonstrably underresolved. A normalized table here consequently establishes
neither grid resolution nor scientific calibration. This demo does not run
that counterexample or claim that its own illustrative grid passes a
resolution study.

## Finite work

On a successful run: five CLI entries, four purchases (164 observed frames),
one 160-row legacy fit, one preparation, 24 predictions (984 frames), one
independent scorer (984 reference positions, including 24 time-zero positions),
one native enumeration of 16 models, 64 two-frame endpoint predictions
(128 frames), and one 16-entry normalizer. The scorer's nonzero-time reference
uses at most 960 x 128 Decimal recurrence steps; validators add binding and
canonicalization, not extra scientific forward calls. Endpoint forwards each
perform their own native binding plus the endpoint's explicit binding; the
final raw endpoint binder does not rerun them. Three read-only Git processes
check source identity; there are no product child processes.

Nine small guard tests are nonnumerical and do not run this workflow.
The combined example passed the finite one-run validation above. It is outside
the measured 12-row study/publisher path. Existing 36-episode / 432-purchase /
8 CPU-hour / 1 GiB / zero-provider study limits stay unchanged; a future study
cannot claim this illustrative run as free calibration.
