# GRID-Q1 control repair and proposed combined qualification

Status: implemented and independently reviewed. The operational entries remain
disabled. The integrated 108-case suite, formatting, lint and configured type
checks passed.
No live qualification service or numerical attempt has run; the combined
proposal below is not yet approved. Scientific source remains
`cec936a2a5a6534861eb9183861c4d6fcf931f67`; its 27 profiles, reference formulas,
gates and export bytes are unchanged.

## Incident and concrete repair

The approved logical run `grid-q1-cec936a2-once` ended as
`administrative_preparation_incomplete_numerical_not_started`: zero controller
and zero entry invocations. Its admission digest is
`a9c4e26f9170343b990de3bbe00986321f066056f920d62f2bc5dbbb1e0f8f90`,
owner digest
`16ca90482a35149670c9cb77932b89e288d7bc4975e37ec2c67cc1b4d16f2fb5`,
and administrative outcome digest
`1dff2f97f5cdaae2ec02f1f445b56ed557a927c4933e13a4280c08c7012eb728`.
The [original decision](https://github.com/spei04/strange-physics/blob/4757185b97fbbd28223c5b1ac4cab85ec7cac6cd/docs/GRID_Q1_RUN_DECISION.md)
remains unchanged. These are provenance references, not a new permission to run.

The local wrapper called `killpg` unconditionally in cleanup. A
`PermissionError` escaped before `wait4` and the final receipt, potentially
masking a previously captured fault. The original fault is unknown; this does
not establish an SSH, server or authentication failure. The recovered local
elapsed interval did not prove all gcloud/IAP descendant CPU or closure.
All old charges, unknowns and the held reservation remain preserved. There is
no refund, automatic retry, fresh eight-hour balance or reuse of that authority.

The new adapter moves ownership to the existing Linux systemd user manager.
Its repair is operational: it saves the first fault independently, preserves
cleanup errors, retains service accounting before cleanup, and never makes
`Result=success` override an earlier fault. Ordinary CLI command exceptions
also remain separate from log flush/fsync/close failures. A command timeout
plus log-finalization failure must retain both facts.

## Exact ownership and retained accounting

A new owner admission must bind a fresh inner run root, its deterministic
private sibling `<run-root>-control`, source and controller hashes, and the
resulting unique service name. The sibling holds all supervisor output, outside
the unchanged inner controller's 8 MiB pool. A durable exclusive intent precedes
the single submission. Duplicate intent, old result/verification/activation
records, administrative outcomes or held-attempt records deny reuse. Lost
acknowledgement inspects the same unit; it never resubmits.

The service uses `Type=exec`, `ExitType=cgroup`, `RemainAfterExit=yes`,
`CPUAccounting=yes`, `Restart=no`, no randomized runtime extension,
`KillMode=control-group`, `SendSIGKILL=yes`, and `UMask=0077`.
Submission is detached, without `--wait`, `--pipe`, `--pty` or `--collect`.
Actual properties, InvocationID, cgroup identity, CPU quota/period and zero burst
must be read back; requested settings alone are insufficient.

A bound-start receipt retains InvocationID, cgroup and actual quota proof.
Closure requires `populated=0`, or qualified cached terminal state plus the
disappearance of a previously bound path. A missing initial path or
`MainPID=0` is not proof. CPU usage must be finite, nonsentinel and monotonic.
Terminal records retain result/exit status, CPU, and real/monotonic timestamps.

A watch fault is saved before owned-unit termination. Each TERM/KILL action
rechecks InvocationID and actual properties. TERM has a bounded grace before
KILL; no signal payload is used. Systemd may regard TERM as clean, so the saved
first fault remains authoritative. The adapter saves its accounting/closure
receipt before stopping an empty unit. It does not reset or collect the unit.
Stop/readback failures remain independent errors. Final and fallback receipt
writes are attempted even after a cleanup deadline; their byte limits do not
claim immunity to blocked kernel I/O or failing storage.

Fresh result/verification/report hashes are joined to the current admission,
source and InvocationID. A strict report pass or complete negative remains
provisional until service closure and the combined external ledger close.
No stale exit-one report can stand in for the current invocation.

## One prospective combined proposal

This replaces neither historical accounting nor the old approval. One future
owner decision would cover qualification, one unchanged GRID invocation and
closeout together. The proposal is **2,400 seconds end to end**, **104 MiB**
retained logical output, and a deliberately conservative **33,600 CPU-second
whole-host upper reservation**: at most 10 client CPUs plus 4 server CPUs, each
for at most 2,400 seconds.

That whole-host figure includes idle IAP intervals, unrelated work and shared
supervisor overhead. It is not measured research cost, and component usage must
not be added to it again. It is valid only if both recorded closed lease
intervals fit 2,400 seconds and verified maximum CPU counts do not change.
Client and server need explicit start/end anchors, boot/runtime identity and
complete transport/final-reporting coverage. Unknown closure, a longer lease
or a failed CPU-count assumption prevents a within-envelope conclusion.

The proposed wall partition is 180 seconds preparation, 180 qualification,
1,740 GRID supervision, 240 closeout and 60 contingency. Unused portions do not
authorize retries. A 600 CPU-second adapter/cloud-administration working stop
target is not a hard cap or a claim that Mac work fits 600 seconds.

| Proposed service setting | GRID | Each of three synthetic fixture services |
| --- | ---: | ---: |
| CPU quota / period |50% /100 ms |50% /100 ms |
| Runtime maximum |1,710 s |8 s |
| Start / stop timeout |10 s /10 s |3 s /2 s |
| CPU watch |580 s |7 s |
| TERM grace |2 s |1 s |
| Absolute terminal deadline from adapter start |1,740 s |15 s |
| Failure-inclusive service CPU reservation |900 s |8 s |
| Per-file service limit |16 MiB |1 MiB |

CPU accounting measures; quota limits a rate. Neither alone is a cumulative
hard CPU cap. Runtime/shutdown limits, verified `cpu.max` and zero
`cpu.max.burst` support a conservative rate/runtime fallback with margin.
The 900-second GRID reservation covers a roughly 865-second rate/runtime bound
plus margin; it does not legitimize an inner overrun. The scientific subledger
still requires at most 570 actual runtime CPU seconds; the unchanged inner
controller's printed +30 marker retains its legacy 600-second acceptance
arithmetic. The old external 30 CPU/90 wall closure requirement would be
explicitly replaced by this complete outer lease/accounting decision.
The marker is not proof of current external cost and is not added twice.

Storage would require 20 GiB +112 MiB available initially
(21,592,276,992 bytes), then 20 GiB. This is a proposed one-run policy;
other numerical work retains its prior storage policy. The extra 8 MiB over
104 MiB is allocation/metadata cushion, not more logical output authority.
Report logical and allocated bytes separately and refresh capacity at admission.
No capacity purchase, dependency installation or old-cost reset is proposed.

The inner 72 MiB stays 64 MiB product plus 8 MiB inner control.
A proposed outer 32 MiB writer partition is:

| Outer writer pool | Ceiling |
| --- | ---: |
| GRID service console, hard per-file limit |16 MiB |
| Three qualification service consoles plus CLI/terminal/fixture records |7 MiB |
| Adapter/source/admissions |3 MiB |
| GRID CLI snapshots and supervisor receipts |2 MiB |
| Transport and final ledger |4 MiB |

All failed and partial files count. Each known supervisor CLI command has an
8 KiB output-file limit; at most 100 commands are permitted per adapter.
Individual receipts are at most 64 KiB. The aggregate is a proposed admission
and acceptance boundary, not an atomic filesystem quota. Supported local fsync
semantics apply; write/closure/overrun failures remain incomplete.
The separate outer-root mapping is mandatory so outer output cannot silently
consume the inner 8 MiB pool.

## Qualification before the scientific attempt

The integrated source/style/type checks and 108 synthetic regression cases passed
under ordinary engineering work, separate from the original numerical attempt.
The tests
poison real subprocess execution except for explicit fake replacements and
perform no GRID, EndpointOracle, numerical reference or service work. They
cover the original primary-fault plus cleanup PermissionError regression, a
command timeout plus fsync error, missing receipts/accounting/quota, stale
negative output, changed InvocationID, finite deadlines, duplicate authority
and provisional pass/negative classification. All 324 final test phases passed;
25 guarded processes in the final engineering sequence closed. No dependencies
were installed. Earlier failed check attempts remain retained. These results do
not establish live systemd behavior or numerical validity.

The live qualification then uses three bounded synthetic services: normal exit,
intentional nonzero exit, and timeout with a surviving descendant. Short children
must wait for an explicit ready/release handshake: the fixture writes ready and
waits; its source-pinned qualification coordinator releases it only after the
adapter's bound receipt proves InvocationID/cgroup/quota. There is no timing
sleep assumption or relaxed closure check. The timeout fixture's descendant
must demonstrate group termination and retained usage, including TERM/KILL
behavior. These fixtures contain no scientific code.

The final qualification manifest must pin the fixture/coordinator source,
expected exits and finite calls; those live artifacts and their results are not
supplied by a successful synthetic test. Only after all three qualify, fresh
capacity and exact new owner/source admission may one GRID attempt start.
A qualification failure consumes the proposed opportunity and retains evidence;
it does not spend an unused pool on another attempt.

Keep three statuses separate: wrapper qualification, numerical attempt, and
closeout. A pre-dispatch administrative failure is not_started; uncertain
dispatch is attempt_unknown. A fully verified negative GRID report is a valid
scientific diagnostic negative. Either pass or negative with failed usage or
cleanup closeout stays provisional/incomplete. No new calibrated uncertainty,
selector, law-change or full-study claim follows.

## Source-review boundary

The operational adapter, synthetic service fixtures, fake tests, frozen
qualification manifest, runbook and progress documentation change. Scientific
cec exports, production package, dependency lock, 27 profiles and fixed gates
do not. Both Python entries and the fixed shell operator remain disabled. No source review or mock test
can establish actual manager behavior or live fixture performance. The integrated
engineering checks and independent source reviews have passed. Live
qualification, final owner admission and combined lease closeout remain
separate gates; a passing mock suite does not establish those outcomes.

## Final source and decision

The [complete decision](GRID_Q1_SUPERVISED_RUN_DECISION.md) pins repair source
5b84a69c69bd47ee5c467e58eddc8904980191df and the final108-case acceptance.
The [fixed operator](GRID_Q1_LIVE_QUALIFICATION.md) covers qualification,
one dispatch, failure-aware closeout and observed handback in one invocation.
The scientific source remains cec936a2. No live service or diagnostic ran.
