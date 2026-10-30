# Fixed live qualification before one GRID-Q1 attempt

This is disabled source preparation, not an execution allocation. The original
attempt ended before numerical invocation; its unknown costs and full
reservation remain retained. A new owner decision must cover qualification,
one GRID attempt and closeout together. It cannot retry the original root.

Scientific source remains [cec936a2](https://github.com/spei04/strange-physics/commit/cec936a2a5a6534861eb9183861c4d6fcf931f67).
The fixed 27 profiles and scientific gates do not change. Passing control
qualification establishes only the tested supervisor behavior, not calibrated
uncertainty, selector performance or a full study.

## Exact source and authority layout

The companion [manifest](../scripts/grid_q1_live_qualification.json) contains
source hashes, fixed profiles, field names, argv and writer bounds. Both Python
entrypoints remain disabled. Activation changes exactly one literal
ENABLED = False to ENABLED = True in private exports; no other source changes.

The new logical identity is grid-q1-cec936a2-supervised-v1, rooted in a fresh
owner-bound private directory named qualification-supervised-q1-cec936a2-v1.
The private admission resolves normalized absolute paths; none are published
here. Owned output roots are disjoint:

- source: exact exports with scripts/grid_q1_supervisor.py and the disabled and
  active fixture/supervisor copies; preserve the scripts package identity.
- normal, nonzero and timeout, each with its sibling name-control directory.
- A separate numerical directory directly under the existing GRID evidence
  parent, named qualification-run-q1-cec936a2-supervised-v1, and its sibling
  qualification-run-q1-cec936a2-supervised-v1-control. It must not be a grid
  subdirectory inside the combined root: the unchanged controller rejects that.
- control: combined claims, engineering receipt, phase observations and ledger.

All directories are 0700; regular files are 0600, one link, no symlinks.
The failed original qualification-run-q1-cec936a2-once root is forbidden.

The outer owner record pins source, complete contract, all roots, exact
qualification-kind/root pairs, adapter and fixture hashes, and the GRID
template hash, immutable initial lease-observation references, fixed output-pool
map, engineering receipt reference and active operator reference. Capture both
initial host observations before materialization; each lease reference is a
private path plus SHA-256 under combined control. Their bytes are never replaced
with a later start. Materialize the separate inner owner record first, the GRID
template referring to it second, and the outer owner pinning that template
third. Specs then reference the outer owner path/hash. Full spec hashes are
derived afterward for unit identity; they do not point back into the owner
record. This directed ordering has no SHA fixed-point requirement.

Every failure consumes authority, including preflight or lost acknowledgement.
Exclusive stage claims precede barrier/dispatch checks. A prior combined fault
blocks further scientific dispatch; finish remains available for accounting.
No absent marker, recovered capacity or repaired receipt authorizes retry.

## Materialization before the one invocation

Lead's reviewed private table supplies every literal path and expected digest.
Create fresh roots exclusively, then copy unchanged inputs and flag-only
exports. The following primitive is the exact source-only activation operation;
it does not execute the export:

    raw = source_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_disabled_sha
    assert raw.count(b"\nENABLED = False\n") == 1
    active = raw.replace(b"\nENABLED = False\n", b"\nENABLED = True\n", 1)
    assert hashlib.sha256(active).hexdigest() == expected_active_sha
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(active)
        out.flush()
        os.fsync(out.fileno())
    directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)

Each fixture root receives this active fixture as run.py and a ≤16 KiB
admission.json with the exact companion fields. Its digest is passed to the
worker and determines its systemd unit. The combined manifest pins the ordered
three spec path/hash pairs, fake-engineering receipt, disabled and active core,
GRID template, open-lease observation paths and output pools. Its actual digest
is retained before any dispatch. Owner provenance and literal private paths are
filled after the new approval; field names, profiles and commands are frozen.

The fixture verifies its own bytes. The operator also verifies run.py before
submission and verifies the imported core's actual module path/hash. Standalone
-I -B mode inserts only the verified source parent, then imports
scripts.grid_q1_supervisor. No scientific module is imported by the fixture,
and no installed environment is changed.

The unchanged inner controller requires the supported literal capacity_policy
one_run_20_plus_80MiB and its exact inner reservation: 600 CPU seconds, 1,800 wall
seconds, 64 MiB product and 8 MiB control. The outer operator separately imposes
the stricter 20 GiB +112 MiB initial guard. The new separate inner owner joins the
exact source, run root, reservation, capacity policy and historical-cost fields;
its authority_disposition records the new decision and admit_this_single_run
remains false until that decision. Do not insert the outer 33,600/2,400/104 values
into the inner equality check.

At actual scientific dispatch the identity checkout must be clean, at exact
cec936a2/tree 4a3c3623; operational exports come from the separately pinned repair
source. Do not precreate inner source/ or product/: the controller creates them.
Its three helper files and flag-only PREPARATION_FINALIZED activation remain
unchanged. The retained preparation donor also remains in the inner control
precharge: the reviewed census is 24 files/150,673 bytes. Freeze and recheck that
donor; do not move or delete it.

The GRID template has qualification_accepted=false. After qualification, only
that field becomes true and qualification_barrier_sha256 is added. The actual
admission digest is retained with exclusive dispatch intent. The exact active
core CLI starts the reviewed inner controller; the operator never calls
execute() to bypass its entry guard.

## Complete automatic invocation

The fixed [operator source](../scripts/grid_q1_operator.sh) is the complete
qualification → one dispatch → failure-aware closeout → handback sequence.
It is disabled by default. Its private activation changes exactly the anchored
assignment EXECUTION_ENABLED=false to EXECUTION_ENABLED=true; all remaining
bytes match the published source. The owner and combined manifest pin the
active operator reference before any invocation.

After the single approval, the materialization record supplies the exact
normalized private paths and hashes. Run this one cloud command:

    /usr/bin/env -u BASH_ENV /bin/bash --noprofile --norc "$OPERATOR" \
      "$Q" "$M" "$MSHA" "$C" \
      "$NORMAL_SPEC" "$NORMAL_SHA" "$NONZERO_SPEC" "$NONZERO_SHA" \
      "$TIMEOUT_SPEC" "$TIMEOUT_SHA"

There are no model/tool round trips between stages. Preflight verifies its own
bytes, fixture bytes, owner, combined manifest and ordered fixture specs;
an exclusive operator claim consumes this opportunity. It rejects preparation
beyond 180 seconds or less than 2,170 seconds remaining, using the pinned initial
server observation. Preflight is bounded by 10 seconds plus two-second KILL
grace. Each foreground phase has its own timeout; there is no nested outer
process-group closure claim. Shared transport handback still requires an
observed external witness.

Inside that bound, qualification has a 175-second TERM deadline plus five-second
KILL grace. GRID has 1,735+5 seconds and closeout 235+5 seconds. These sum to the
180/1,740/240 phase ceilings. Phase-record and final-marker commands each have
four-second timeouts plus one-second KILL grace. With preparation, this reserves
2,350 seconds and leaves 50 seconds for glue and contingency within the same
2,400-second admission/acceptance window.
A cutoff at the extreme deadline may make an outcome incomplete. No unused
time authorizes a retry.

Each qualifier is detached and executes start → ready → release → finish
automatically. Even a failed start/ready/release attempts bounded finish for
accounting. A failed qualifier prevents later qualification and GRID dispatch.
All foreground commands are waited. An immutable phase-status record is written
before unconditional closeout, including qualification_exit and grid_exit;
125 means GRID was not dispatched. Closeout's exit zero means its ledger was
retained, not that the scientific result passed.

Noclobber output prevents a repeated invocation from truncating old logs.
Qualification and GRID phase logs have 512 KiB file limits; failure to apply
a limit aborts that phase. Closeout writes to captured terminal only, so no log
keeps growing behind the final census. A preflight identity failure invokes no
unverified code; retained intent (if reached), error output and final observed
handback remain an incomplete administrative outcome.

Each worker writes and fsyncs a ready record containing actual InvocationID,
spec/fixture hashes and PID. Timeout additionally forks exactly one child:
the child acknowledges via an anonymous pipe after installing SIGTERM ignore.
The parent then writes the descendant PID. A private nonblocking FIFO carries
an exact ≤512-byte release token. The operator binds actual properties,
InvocationID, cgroup, cpu.max and zero burst before release. This is an explicit
handshake, not a sleep-based race workaround.

After release, normal exits 0; nonzero exits 7; timeout waits while its child
survives TERM until the manager's KILL escalation. Timeout qualification
requires Result=timeout and whole-cgroup closure; MainPID=0 is insufficient.
Terminal CPU/properties are durable before stopping an empty owned unit.
A lost startup acknowledgement may be inspected and closed but never resubmitted
or counted as a qualification pass.

The barrier checks the three ordered spec/verdict/terminal hashes, common
owner/source, exact expected outcomes, non-sentinel CPU ≤8 seconds each and
confirmed cleanup. It also requires the same-source fake-engineering receipt:
all cases pass, zero scientific calls and zero real process attempts.
The final integrated suite passed 108 fake cases/324 phases (52 core and
56 fixture/operator cases). No live service was started by these checks.

Only after the barrier succeeds does the operator invoke the fixture dispatch
CLI exactly once. That process replaces itself with the pinned active core CLI.
Its intent records the deterministic unit ID. Lost acknowledgement inspects that
same ID only; never repeat start or dispatch. Failure closeout preserves known
usage, receipt hashes, missing evidence and first/supplemental faults, including
cases where GRID never started. No reset-failed or collection is needed.

Expected nonzero/timeout services may remain in systemd's failed state after
stop. Acceptance requires the same invocation and terminal outcome, retained
accounting and an empty cgroup. Clearing the failed state is not a prerequisite;
unexpected outcomes and previously recorded faults still prevent acceptance.
See the [systemd 255 stop implementation](https://github.com/systemd/systemd/blob/v255/src/core/unit.c#L1852).

## Resource and complete writer inventory

The proposed contract is unchanged: 2,400 seconds end to end, 104 MiB logical
output, start 20 GiB +112 MiB and later 20 GiB. This is a new explicit one-run
amendment; other historical 50/45 GiB guards are not waived.

Inner output remains 64 MiB product +8 MiB control. Outer output is 16 MiB GRID
console +7 MiB qualification +3 MiB pinned source/admissions +2 MiB GRID
controls +4 MiB transport/ledger. Per qualification unit: at most 100×8 KiB
CLI logs, 16×16 KiB control receipts, three×16 KiB worker/spec JSON files,
one ≤64 KiB fixture copy, and one ≤1 MiB service console. Three units total
at most 6,733,824 bytes, below 7 MiB. The FIFO has no logical payload bytes.
Inventory uses lstat only for it: it is never opened or hashed.

GRID console retains the compatible 16 MiB service file limit. GRID control
uses at most 100×8 KiB CLI logs and 7×64 KiB receipts, within 2 MiB. All pinned
source/admissions must fit 3 MiB. The final no-follow walk rejects links,
devices, unlisted/overlapping roots and more than 10,000 entries, with a
256 KiB final-record reserve in the transport pool. The operator adds two
at-most-512 KiB phase logs and one at-most-16 KiB phase-status record to that
4 MiB transport pool; source/operator exports remain in the 3 MiB source pool.
Captured terminal output is retained in the same transport accounting, with
a 256 KiB allowance; excess or unavailable capture accounting is incomplete. Failed/partial writes
count. Logical bytes and st_blocks are distinct; a scan is not a filesystem
quota or protection against unrelated writers.

Both service profiles use 50%/100 ms CPU quota with actual quota/burst
readback. GRID: runtime 1,710 s, start/stop 10/10 s, watch 580 CPU s, TERM
grace 2 s, terminal 1,740 s. Qualifications: 8/3/2 s, watch 7 CPU s, grace
1 s, terminal 15 s. Failure-inclusive service allowances are 900 CPU seconds
for GRID and eight each for qualification. CPUAccounting measures usage;
CPUQuota is a rate, not a cumulative CPU cap. A retained watch fault overrides
a later manager Result=success.

The conservative whole-host CPU reservation is 33,600 seconds: maximum ten
client CPUs plus four cloud CPUs over the same 2,400-second lease. This includes
transport/IAP/shared supervisor/unrelated work; it is not measured research
cost. Component observations are inside it, never added again. Maximum CPU
counts and boot identities must be verified. Cloud administrative 600 CPU
seconds is a working stop target, not a hard cap or proof of Mac usage.

Wall phases remain 180 preparation +180 qualification +1,740 GRID +240
closeout +60 contingency. The inner 570 runtime plus printed legacy 30 marker
remains a 600 acceptance rule; that marker does not claim all new external
work fits 30/90 and is not an additional actual charge.

## Provisional closeout and observed final witness

The immutable, hash-pinned client/server initial observations contain source/combined ID,
start_monotonic_ns, observed_monotonic_ns, maximum CPU count, boot_start,
boot_observed and closed=false. They are earlier observations, never final
or projected future endpoints.

The closeout command attempts every evidence read and the output census even
when qualification or GRID failed. Missing or invalid evidence remains explicit.
It fsyncs combined-closeout.json with status=pending_external_witness and
accepted=false, separately identifying an incomplete or provisional scientific
attempt. Its terminal marker contains the actual saved summary SHA. If writing
that summary fails, a terminal fallback reports the fault and known hashes;
it cannot establish acceptance.

After waiting for the complete driver, the operator emits an observed server
monotonic/boot/maximum-CPU marker and the sealed summary hash, then returns.
It writes no additional owned file.

The chosen transport boundary is **owned-command handback on the existing
healthy transport**. After the cloud script returns, the lead verifies no queued
unit work and drains the stream. The lead then captures the client observation
through a read-only control-host command. The cloud script emits the server
marker only; it does not automate the client witness. Trusted tool completion
supplies the external post-exit/handback observation. Do not claim the shared SSH/gcloud/
IAP connection terminated. The original failed transport's unknowns remain.

All owned files must be sealed before this final witness. If an additional
durable ledger write is needed, it occurs inside the same window before the
last witness; no further unit files are written afterward. Later progress
summaries cite the transcript as separate administrative work. Actual server
post-exit and client post-drain/handback observations, not projected timestamps,
must establish ≤2,400-second intervals and the verified CPU/boot assumptions.
The source's lease_check validates a closed receipt's scalar conditions;
independent final review must join that receipt to the actual transcript,
all source/admission/unit hashes, cleanup, output and failures.

Unknown/overrun, missing witness, unclosed cgroup, CPU-count change or queued
work means incomplete. A strict complete-negative scientific report remains a
negative result, but failed administrative closeout leaves it provisional.
No passing result from this source preparation is claimed.

The final 108-case suite poisons real process/fork/exec/signal paths and includes
the three-case automatic handshake, approval assembly, failure-aware closeout,
real complete-negative vocabulary and supervisor fault references. Five cases
execute the actual operator terminal snippet under mocked files/host/clock.
Configured types, final focused types, lint/format, shell syntax, disabled entry
and all three embedded Python blocks passed. Independent source reviews accepted
the integrated corrections. Live qualification remains separate.

The closeout CLI returns zero when a ledger is retained, even for an incomplete
attempt. The complete operator additionally reads that sealed ledger and returns
nonzero unless it is provisional_complete and final server boot, CPU and observed
time conditions hold. Neither zero exit nor a provisional ledger replaces the
external client/server witness review.
