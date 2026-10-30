# GRID-Q1: one supervised diagnostic decision

**Status: proposed; not approved or executed.** The original approved attempt
stopped in administrative preparation before the controller or numerical entry
ran. The replacement control code is implemented and independently reviewed.
This decision covers one complete attempt, including its control qualification
and closeout.

## What the earlier approval produced

The [original decision](https://github.com/spei04/strange-physics/blob/4757185b97fbbd28223c5b1ac4cab85ec7cac6cd/docs/GRID_Q1_RUN_DECISION.md)
authorized 600 CPU seconds, 1,800 active-wall seconds and 72 MiB for one run.
During preparation, the Mac wrapper's unconditional process-group cleanup raised
PermissionError before its final accounting receipt. That error may have masked
an earlier fault; the evidence does not identify SSH, authentication or the
server as the cause.

No GRID controller or numerical entry was invoked. The original admission,
reservation, failed preparation and unresolved costs are preserved. The
administrative outcome digest is
`1dff2f97f5cdaae2ec02f1f445b56ed557a927c4933e13a4280c08c7012eb728`.
No missing marker is treated as proof that capacity is unspent. This proposal
does not refund or reuse the original allocation, settle historical unknowns,
or create a fresh eight-hour research balance.

## Concrete reviewed implementation

[Repair source 8b16c7e](https://github.com/spei04/strange-physics/commit/8b16c7eba1da547f9594d620d9dae6e12173ffcd)
contains the disabled supervisor, three fixed service fixtures, complete
operator, frozen manifest and regression tests. The
[incident and repair guide](GRID_Q1_CONTROL_REPAIR.md) and
[exact operator runbook](GRID_Q1_LIVE_QUALIFICATION.md) describe the contracts.

The final code passed 108 isolated cases / 324 test phases, with zero real
process attempts from those cases and zero scientific imports or calls.
Formatting, lint, the configured 193-file type check and final focused type
check passed. The operator passed shell syntax and disabled-entry checks;
all three embedded Python blocks compiled, and five mocked cases exercised its
actual final-observation code. The first typing diagnostics and an intermediate
CPU-limit stop remain retained. Thirty guarded checking processes closed.
Private engineering acceptance:
`491cf0643e5b7653b0d82ee1e16d277cec9b3e66afaaca31712dcc20c47b5f0f`.

The initial hosted Python 3.14 job at a4f4b4e passed 4,890 test bodies but
failed three temporary-directory teardowns. Shared file-operation mocks outlived
the worker call. The test-only successor scopes and restores those mocks before
cleanup, preserves the release assertions, and passed fresh local checks. The
failed run remains retained; required hosted checks must pass on this corrected
source before this decision is handed over for approval. Operational and
scientific bytes are unchanged by that correction.

Independent review closed faults in error retention, failed-service cleanup,
owner/source bindings, acyclic admission construction, failure closeout and
terminal evidence. These checks establish source behavior under mocks.
**Live service qualification and the physics diagnostic have not run.**

Scientific inputs remain pinned to
[cec936a2](https://github.com/spei04/strange-physics/commit/cec936a2a5a6534861eb9183861c4d6fcf931f67),
tree `4a3c3623722dedfdd6f97dd7ed272fb256f350ec`: the same 27 profiles,
reference formulas, thresholds, export bytes and three inner helpers.
[PR136](https://github.com/spei04/strange-physics/pull/136) remains unmerged.

## One approval, one attempt

Approval would authorize these stages together:

1. Capture immutable client/server start, boot and CPU-count observations.
   Materialize the pinned private exports, new inner/outer owner records and
   exact paths. Verify capacity, environment and source. Preparation has a
   180-second ceiling.
2. Run the three fixed synthetic services automatically: successful exit,
   intentional nonzero exit, and timeout with a child that survives TERM.
   Bind actual invocation/cgroup/quota before releasing each handshake; retain
   accounting before cleanup. The phase ceiling is 180 seconds.
3. Only if all three qualify, invoke the unchanged GRID diagnostic once.
   The supervised phase ceiling is 1,740 seconds.
4. Always attempt failure-aware closeout: preserve known usage and receipt
   hashes, identify missing evidence, count all output and retain first faults.
   Closeout has a 240-second ceiling.
5. Observe server exit and client handback within the same overall window.
   The existing shared SSH/IAP connection is handed back with no queued unit
   work; its termination is not claimed.

The fixed operator executes the phases in one cloud invocation, without model
round trips. It uses independent phase timeouts, a bounded preflight and
bounded final-record/marker commands. The overall 2,400-second window is an
admission and acceptance condition, not a claim that filesystem/kernel failure
cannot cause an overrun. Timeout, unknown command closure, missing final
witness or exhausted capacity makes the outcome incomplete.

Every failure consumes the opportunity. There is no automatic retry, second
GRID dispatch, larger sweep, provider call, merge, deployment, dependency
installation or capacity purchase in this decision.

## Complete resource envelope

| Resource | Proposed bound and meaning |
| --- | --- |
| Whole operation | 2,400 seconds / 40 minutes on each observed host interval |
| Conservative CPU reservation | 33,600 CPU seconds: at most 10 client CPUs plus 4 server CPUs, each for 2,400 seconds |
| Scientific controller | Unchanged 570 measured runtime CPU seconds plus its legacy 30-second marker; 600/1,800 inner admission remains |
| GRID service fallback | 900 CPU-second reservation, verified 50% quota, 1,710-second runtime and 10/10-second start/stop timeouts |
| Each of three control fixtures | Eight CPU seconds / 15 terminal seconds; 50% quota, 8-second runtime, 3/2-second start/stop timeouts |
| Retained logical output | 104 MiB total: 72 MiB inner plus 32 MiB outer |
| Initial available storage | 20 GiB +112 MiB = 21,592,276,992 bytes |
| Later available storage | 20 GiB = 21,474,836,480 bytes |

The 33,600 figure is a deliberately conservative **whole-host upper bound**,
including unrelated/idle work and transport overhead. It is not measured
scientific usage or a cloud bill. Component measurements are reported inside
it and never added again. It is valid only if the recorded host intervals,
maximum CPU counts, boot identity and command/service closure satisfy the
contract. Unproved assumptions remain unknown.

This new outer decision explicitly replaces the earlier 30 CPU / 90 wall
external-preparation hold for this attempt only. The inner controller's printed
30-second marker is retained for compatibility; it does not establish the
cost of the new outer procedure.

The 32 MiB outer partition is 16 MiB GRID console, 7 MiB control qualification,
3 MiB source/admissions, 2 MiB GRID supervisor records, and 4 MiB transport/final
ledger. Failed and partial files count. All writer counts, per-file bounds and
the 256 KiB terminal-capture allowance appear in the frozen manifest. The
eight MiB storage cushion above 104 MiB is not additional output authority.

The inner admission keeps its supported literal policy
`one_run_20_plus_80MiB`; the outer guard separately enforces the stricter
112 MiB initial margin. The 24-file / 150,673-byte retained preparation donor
continues to count in the inner control precharge. Other runs retain their
existing storage policies. No shared cache or private evidence is removed.

## Admission and result evidence

The new combined identity is `grid-q1-cec936a2-supervised-v1`.
The numerical root is a fresh direct child of the existing GRID evidence parent,
named `qualification-run-q1-cec936a2-supervised-v1`, with a separate sibling
control directory. The original failed root cannot be reused. The numerical
checkout must be clean at exact cec936a2; operational code is exported from the
separate immutable repair commit.

Private assembly is acyclic: initial observations and engineering receipt,
inner owner, GRID template, outer owner, then fixture specs and combined
manifest. The owner pins roots, immutable observation hashes, output assignments,
engineering, operator and code hashes. The actual spec/admission hashes
determine unique service identities. Activation changes only the reviewed
entry flags after the new approval.

A returned ledger is not an accepted experiment. Final review must join the
actual source/owner/admission/unit hashes, all required terminal receipts,
cgroup closure, actual output counts, immutable initial observations and
observed final tool evidence. Later progress summaries reference that sealed
evidence; no unit files are written after the final witness.

A complete negative is a valid diagnostic result. A pass or negative with
incomplete administrative closeout remains provisional. This diagnostic does
not establish calibrated uncertainty, selector performance, law-change recovery
or full-study readiness. It does not change the approved dependency graph:
Laplace analytic work may proceed in parallel; its comparative audit consumes
accepted, frozen, disjoint calibration fixtures.

## Decision requested

Approve this complete one-attempt envelope and its one-run storage/accounting
amendments, preserving all earlier reservations and unknown costs.

The additional decision is needed because the original preparation did not
close its accounting, and the repaired procedure changes the outer resource
and output envelope. Implementation and source review are complete before this
request; no separate plan/test/run approvals are proposed.
