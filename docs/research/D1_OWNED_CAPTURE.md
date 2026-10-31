# D1 owned capture lifecycle

The current source adds a fixed independent deadline owner and a separate benign
leader-exit handshake. It is **source authored, not runtime qualified**. The
capture service CLI now accepts only its fixed `service REQUEST SHA256` role;
this source activation is part of the new commit and must be included in the
accepted release, protected source inventory and actual hashes. It grants no
scientific permission, installed-runtime trust or admission.

The earlier lifecycle implementation passed 37 private cases/111 phases, full
233-file typing and all 20 owned child closures at
[f1adcabb](https://github.com/spei04/strange-physics/commit/f1adcabb9a0e7e5d917c240dc772f67943c0eb41).
The pytest-owned sibling-root repair subsequently passed ordinary checks as part
of [d51aab55](https://github.com/spei04/strange-physics/commit/d51aab5567b8b73ee175f3cf6f8a1061a4ff2da8).
Those are historical results, not qualification of this successor. Unit19's
unfinished guarded obligation and every prior failure/charge remain retained.

## Fixed source roles

`scripts/d1_owned_capture.py` retains the existing fake-API `execute` and
`CaptureSpec`, fixed request/report joins, and the invocation-bound GRID utility
primitives. `grid_q1_supervisor.py`, its CLI, profiles and numerical meanings are
unchanged. No GRID result or execution is called.

`run_owned(spec)` now delegates to `scripts/d1_capture_owner.py`. The parent
validates the private output root, writes one exclusive owner intent and one
canonical request containing the original start, deadline, intended unit and
parent PID, then starts exactly one fixed controller child. The child command is
the declared protected controller interpreter, `-I -B -X`, a fresh owned cache,
the source-owned owner script, literal `controller` and that request path/hash.
There is no plan-selected command or import root. The parent's wait occurs
outside the submit-capable child, so a stalled child preflight or submit does not
hold the parent's Python call stack.

The child re-reads the actual request, joins source location/startup/parent PID,
and passes the original start into `execute`; it cannot restart the clock. It
submits only the predetermined capture unit. Its ordinary final record remains
provisional. The parent re-reads the actual final/terminal/service records and
child log and repeats their identity and byte joins before considering the child
successful. A nonzero child or missing/substituted report cannot be promoted by
later successful cleanup.

The independent parent holds the unit name before any possible submit. Lost
acknowledgement never causes another submission. On timeout it kills/reaps only
its own `Popen` handle, then observes the predetermined service name. TERM/KILL
and stop still use the existing invocation-bound `Systemd` operations. An absent
unit without a previously bound terminal snapshot is unknown, not proof that a
late queued submission cannot appear. No reset, retry, name release or inferred
absence is introduced. The parent retains `named_ownership_released=False` and
requires external ledger closure. A reaped controller is not proof of all its
possible descendants: `controller_descendants_closed` remains null. Protected
startup and actual external process closure are separate premises. The actual
invocation **must** use the already-reviewed private `process_guard.py` bytes
`edfef49728f6d5965cf2d5ac75aa74830678343639690499ca14611950501ddd`:
an isolated owned group, `waitid(WNOWAIT)`, group cleanup before leader reap,
and a retained terminal closure receipt. The new controller never calls
`setsid`, requests a new session, or detaches, so its CLI descendants remain in
that enclosing group. The external receipt must bind the original owner
invocation, source/spec/request, original deadline and resulting service records;
unknown group closure cannot admit the capture. This required enclosure is not
installed or authenticated by `run_capture` itself. The separately named service
still requires its own invocation/cgroup terminal-empty proof.

The parent has distinct `owner-control` command logs and owner receipts; it does
not race the controller's receipt names or command-log counters. Terminal-empty
facts are retained before a takeover stop. First and supplemental errors, missing
receipts, unknown writes and unknown cleanup remain failures. A manager/kernel/
filesystem stall may prevent timely physical closure or receipt delivery; the
code never converts that uncertainty into an accepted result.

## Validation placement and original deadlines

There are still exactly three full protected inventory validations. The first
`read_plan`/`validate_plan` and exact source joins now run inside `service_entry`,
immediately before unchanged `d1_bootstrap_control.launch` and its pre/post
passes. The outer parent and controller do no full inventory scan. Their source,
interpreter, imports, environment and manager custody must therefore be
independently established **before** service dispatch. Moving validation inside
the service does not establish those premises.

The existing fixed profile is unchanged: 240-second service runtime,
5-second start/stop timeouts, 50% quota/100 ms, zero observed burst, a 120 CPU-second
watch, at most 60 four-second observations and the original 300-second terminal
deadline. Useful work has a source-owned cutoff at start+240. The service rejects
entry outside the original work window, checks again after its first full
preflight, and refuses launch unless more than 65 seconds remain (the existing
60-second child wait plus 5-second child cleanup). It checks the cutoff after
launch too. The unchanged launch's own pre/post validation can still block: the
65-second reserve is not a bound on those reads.

The independent parent stops waiting for the controller at start+240; controller
kill/reap and named-service reconciliation consume the remaining 60 seconds.
Every subsequent command/wait is clipped to start+300. Takeover permits at most
eight snapshots, one TERM and one KILL, and one terminal-receipt/stop/post-stop
sequence. These worst-case calls are not promised to all fit: exhaustion retains
incomplete state. Even a late systemd submission must pass the original service
work-window check before any target launch. RuntimeMaxSec starts when the service
becomes active; it does not replace the original deadline. Arbitrary manager or
kernel stalls cannot be given a hard 300-second closure guarantee here.

## Separate benign leader-exit qualification

`scripts/d1_capture_descendant.py` supplies one fixed worker and watcher. It is a
separate prospective qualification unit, never a capture report or scientific
fixture. `DescendantPlan` retains the capture resource profile and derives a
separate deterministic unit name. Its request fixes one 64-hex token and original
30-second worker deadline. The watcher has 60 seconds for handshake and cleanup.
These bounds do not allocate a run.

After an exclusive intent, `PipeHandshake.prepare` checks the actual worker
source digest, creates the private control root and release FIFO, and seals the
request. The service worker makes one pipe and forks once. Its child opens the
owned FIFO, retains a ready record bound to the actual invocation/group/token,
and acknowledges readiness to the leader. The leader then exits. The watcher
requires a nonzero leader-exit timestamp, successful leader exit and a still
populated bound cgroup; leader-only/empty fixtures cannot pass. It retains this
observation before one exact token release. The child rejects an expired deadline immediately before waiting and after
reading, even if the exact token was already buffered; it checks the token, closes
its owned descriptors and retains a bounded completion/error record before
exit. The watcher requires the successful completion record, then actual
terminal-empty state, terminal receipt, stop and post-stop closure. A release
write failure consumes that opportunity; cleanup never makes it a success.

The tests substitute helper-local OS/select/time/sys adapters, not shared stdlib
functions. No actual fork, pipe, FIFO, service, profile hook, reference or primitive
runs in the authored fake cases. Actual handshake/cgroup behavior is a later
qualification requirement. The fixture does not rerun any GRID controls.

## Finite source accounting

The three inventory passes retain the prior generic input ceiling
`3 × 512 MiB = 1,610,612,736 bytes`, plus the existing bounded plan/configuration/
installation/request/report/import reads. The owner adds one 16-KiB request read
and up to four 64-KiB retained-record/log reads for its final joins. Request,
JSON-decoding, serialization and retained byte copies are additional work and
memory; no whole-path RSS or actual CPU fit is claimed.

The earlier capture selected-file ceiling was 5,939,200 bytes/142 names: up to
64 receipts, one request, child log, service console and 75 command logs. The
parent adds three 64-KiB receipts, one 16-KiB request and at most 15 8-KiB command
logs: 335,872 bytes/19 names. The selected capture subtotal is therefore
6,275,072 bytes/161 names, plus directories/cache state. The benign selected-file
ceiling is four 64-KiB watcher receipts, three 4-KiB request/ready/done records,
one 1-MiB console, 21 8-KiB command logs and one zero-byte FIFO pathname:
1,495,040 bytes/30 names. Combined selected files are 7,770,112 bytes/191 names.
Protected inventory/artifact inputs, source copies, controls, snapshots, partial
failed files and external publication are **not** included in this subtotal;
it is not an 8-MiB whole-operation-fit claim or a transfer of any allocation.

Parent CPU, waited controller/CLI CPU and service cgroup CPU overlap and remain
separate observations. The three full validations are now service-accounted;
outer setup, interpreter startup, imports, logging, cleanup and publication still
need actual accounting. No prior remainder, source-manifest read budget or
scientific balance is reused.

## Authored verification scope

Static AST census: 79 cases/237 prospective phases in 29 test functions:
41 lifecycle cases/18 functions, 20 parent-owner cases/8 functions, and
18 benign cases/3 functions. They cover original-clock refusal, post-preflight
launch reserve, independent timeout takeover, late acknowledgement, stale
identity/missing units, unreaped child, terminal/final/intent failure, exact
retained report substitutions, no-I/O preclaim/consumed rejection, leader-only
rejection, ready/release joins, fake parent/child branches, fork refusal and close
uncertainty. Command failures retain the underlying first error and supplemental
log-close facts. Worker descriptors are marked consumed before every close;
close-after-consumption cannot retry the same descriptor or skip the remaining
independent closes. Parent read errors survive later close errors. Existing
report/cleanup assertions remain; the preflight test now correctly observes its
moved service-side position.

A conservative fixture payload estimate per retained suite is 1,269,760 bytes:
1,064,960 for lifecycle cases (including three new request/report cases), 102,400
for owner requests, and 102,400 for benign records (eleven requests and seven pairs
of ready/done files, each at most 4 KiB). Two retained
suite sets require 2,539,520 bytes before framework metadata/logs. This is a
source-derived loose upper bound, not measured output. Fake tests create no
symlinks, hardlinks or FIFOs; pytest may create its own links. Most receipt data
stays in bounded fake stores. Actual qualification must census every retained
pathname and failed copy, not reuse the former 1.5-MiB two-suite partition without
reconciliation.

No imports, formatters, typing, collection, tests or service actions were executed
during this source-authoring stage. Planned ordinary checks, in the accepted
engineering environment after review, are:

```
python -m ruff format --check scripts/d1_owned_capture.py scripts/d1_capture_owner.py scripts/d1_capture_descendant.py tests/test_d1_owned_capture.py tests/test_d1_capture_owner.py tests/test_d1_capture_descendant.py
python -m ruff check scripts/d1_owned_capture.py scripts/d1_capture_owner.py scripts/d1_capture_descendant.py tests/test_d1_owned_capture.py tests/test_d1_capture_owner.py tests/test_d1_capture_descendant.py
python -m mypy src tests examples
python -m pytest tests/test_d1_owned_capture.py tests/test_d1_capture_owner.py tests/test_d1_capture_descendant.py
```

Actual accepted installation, complete protected startup/runtime inventory,
closed outer ownership, benign live handshake and one capture-only qualification
remain prerequisites. No source-shape/checksum or fake pass substitutes for them.
The frozen D1 diagnostic and downstream approved 36-episode/432-slot comparison
remain the research purpose; neither is executed by this slice.

## Historical software checkpoint

The following account describes the earlier b2408ab9 checkpoint, not the new
source or its delivery status. The complete earlier bounds, costs and private
qualification record remain in the [immutable lifecycle guide](https://github.com/spei04/strange-physics/blob/b2408ab909863e143ea0d89e1c7eaeeeb2bae8f8/docs/research/D1_OWNED_CAPTURE.md).

### Lifecycle test cleanup correction

The original PR157 CI run failed seven cases on each Python runtime: 6,270
passed and seven failed. Formatting, lint and full typing passed; schema,
package and smoke stages were skipped. The isolated private qualification had
used all-retained pytest paths, while ordinary CI uses failed-only retention.
After a passing case, pytest removed its numbered run directory but left the
adapter's sibling control directory. Reusing the numbered path could therefore
fail before preflight or submission. The original logs did not capture that
first exception, so the cause of that historical CI failure remains a
source/order inference; the new regression separately targets the mechanism.

The reviewed repair at 22779331 places run and control directories inside the
same pytest-owned case directory. Production exclusivity and lifecycle behavior
are unchanged. The new behavioral regression reproduces the old collision,
checks its exact FileExistsError and zero submissions, then removes/recreates
the fixed enclosing directory and requires the intended report-join failure
with one submission and confirmed stop in both cycles. Existing assertions are
preserved with first-fault diagnostics added to the previously failing paths.

The repaired module has 38 cases in 17 functions. All 38 passed in 0.51 seconds
at combined source 5ac97608a2d0c6395942cde258a0090fa9d72a9a using the repository's
failed-only retention policy. This includes the behavioral collision/cleanup
regression and the previously failing paths. Focused formatting/lint passed,
all three child processes closed, and source/environment hashes were unchanged.
The separate ordinary check charged 9.927693 CPU / 14.854678 active-wall seconds,
including its 5/10 closeout reservation. Normal pytest cleanup left no retained
fixtures. This is ordinary software evidence, not private guard or protected
runtime qualification. [Full combined CI](https://github.com/spei04/strange-physics/actions/runs/41223320879)
passed all six required jobs on d51aab55 / merge 512c67f. Both Python runtimes
passed 6,302 tests, 233-file typing, 1,567 schemas, package checks and one 8/8
CLI smoke; both analytic jobs passed 24 cases/72 phases. Existing warnings are
unchanged. The protected-main candidate was skipped. The 2,082 observed
required-job seconds and 968-second run interval are separate elapsed scopes;
whole CI CPU and provider cost remain unknown. The PR stays unmerged, and this
result does not qualify protected startup or a real capture service.

The earlier 37/111 private result remains attached to its original bytes.
Conservative successor fixture planning includes up to four additional request
slots and nested case directories; the original Unit20 fixture census above
is historical.
