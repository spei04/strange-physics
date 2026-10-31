# D1 owned capture lifecycle

Source-only implementation based on `11629b131e4c828e16e547660be43054b531681d`;
code checkpoint `ee7ec8ff16243484ecbafbe4e55c6c25bded42f4` (including the
pre-intent ownership and direct-script import repairs to `1326bf8`). Research owns this
new adapter, its fake-API tests and this guide. No project imports, formatter,
typing, test collection/body, service, capture or scientific operation ran during
authoring. The CLI is literally disabled. This is not an execution admission or
a positive runtime qualification.

The existing [bootstrap](D1_BOOTSTRAP.md) and original-owner source remain
unchanged. `grid_q1_supervisor.py`, its profiles, argv, result validation and
numerical meanings are also unchanged. The new capture path never calls the
GRID `Files.result` or `execute` functions.

## Fixed interface and source responsibility

`CaptureSpec` contains the exact private root, checkout, controller interpreter,
protected-plan path/digest, source commit, external admission digest and three
source digests: this adapter, the existing bootstrap controller and bootstrap.
These are declarations joined to the current protected plan, not authority by
possession of the DTO or a matching checksum.

`run_owned(spec)` is the concrete outer API. It uses the existing `Systemd`
implementation and private receipt writer. `execute(spec, supervisor, files, ...)`
exposes the same operation for reviewed fake backends. No callback from a plan
selects code, a command, a profile or an acceptance rule. The local `CapturePlan`
subclass changes only the named-unit identity and fixed service argv; it retains
`Snapshot.bind` and `confirms_empty_unit_cleanup` unchanged.

The intended service argv is the pinned controller interpreter, `-I -B -X`, a
fresh `service-pycache` prefix under the owned root, the source-owned
`scripts/d1_owned_capture.py`, literal `service`, and the exact request path/hash.
Its direct-script-only root import insertion derives from this source file's
location. Ordinary module imports preserve the global lookup order. It never takes an import root from the plan or adds checkout `src`. That source
root, every imported `scripts` module, interpreter, startup and service-manager
environment require independently protected custody before eventual execution.
Byte checks alone do not exclude a hostile writer or authenticate loaded code.

`service_entry` validates the retained request, startup flags and empty cache;
observes its actual systemd `INVOCATION_ID` and unified `/proc/self/cgroup`; then
calls unchanged `d1_bootstrap_control.launch`. That controller retains its exact
isolated target-interpreter command and installed-package route. This adds no
fixture generation, primitive invocation, S/A retention or recorder installation.
The source-selected CLI remains disabled: an eventual entry activation and its
changed source pins require separate review. The fake service-entry case is not
evidence that the CLI or a real service works.

## One attempt and receipt ordering

1. Sample the original monotonic start and parent/waited-CLI CPU baselines.
   Validate the existing private root and persist an exclusive intent, including
   the absolute deadline and profile, before reading the protected plan. A root/
   receipt-store validation failure returns bounded incomplete facts without any
   receipt write. A failed intent callback returns an existing-intent or unknown-
   acknowledgement disposition; neither permits later receipt I/O or preflight.
   The external owner retains these returned facts and any partial intent bytes.
2. Exclusively create the sibling control root and empty service cache. Persist
   and fsync the canonical bounded request and its containing directory.
3. Call the existing `read_plan` and `validate_plan`, then join actual source
   hashes and fixed controller/bootstrap paths to the spec. Check the remaining
   original deadline, observe the intended unit absent, and submit exactly once.
4. Bind actual InvocationID, cgroup, quota/burst, accounting and fixed properties.
   Persist observations. A leader exit while populated never closes the group or
   permits report acceptance. Disappearance is usable only after an actual group
   and populated-state observation was bound to this invocation.
5. After terminal-empty observation and successful service exit, join the bounded
   service record to the exact spec, request, source, admission, root, invocation,
   group and original deadline. Re-read the actual child log and join its exact
   bytes/hash/length and zero-primitive capture shape. The inner result must still
   say `owned_tree_closed=None`, `captured=False`: the inner API cannot manufacture
   this outer lifecycle's conclusion.
6. Persist terminal accounting and the report join **before** stop. Use the
   existing invocation-bound stop operation, then confirm empty cleanup. Preserve
   retained failed-unit identity, exit/timestamps and nondecreasing accounting.
   Persist the final receipt. The returned status can be `provisional_complete`,
   while `accepted` remains false until the external owner closes the full ledger.

The first observed operation fault and later supplemental facts remain separate.
Lost submission acknowledgement consumes the dispatch opportunity; cleanup may
observe the same unit but never resubmit it or upgrade that history. Signals use
only the existing named-unit operation, which rebinds before TERM/KILL. No bare
PID/group signal is introduced. A missing/late/changed report, receipt failure,
identity drift, accounting decrease or unknown cleanup remains incomplete.
Terminal receipt failure prevents stop. A partial or uncertain write is retained,
not retried or deleted. An existing exclusive intent prevents another dispatch.

The service wrapper retains the first capture fault in its report. If that report
write also fails, its raised `ServiceReceiptFailure` retains first and supplemental
facts separately. A failure before the wrapper can form a report leaves the outer
result incomplete; missing evidence does not prove that no service work occurred.

## Finite source bounds and accounting limits

The fixed prospective profile is 300 seconds from the original outer start,
240 seconds service runtime, 5-second start/stop timeouts, 50% CPU quota with a
100 ms period and zero observed burst, a 120 CPU-second cgroup watch, at most
60 four-second polling observations, 5 seconds per control command, and a
2-second TERM grace. Cleanup has at most four final polling observations and
shares the same 300-second deadline. These constants grant no allocation and
reuse no GRID or prior engineering remainder.

A blocking preflight is checked after it returns; this cannot enforce a hard
wall bound while that read is blocked. An external bounded controller covering
initial preflight through final receipts is still required before execution.
Systemd's runtime starts later and cannot replace that whole-attempt deadline.
Likewise the CPU watch is an observation, not a kernel aggregate CPU cap.

There are **three** full protected inventory validations: one outer pre-submit
pass and the unchanged controller's pre/post passes inside the service. The
generic payload ceiling is `3 * 512 MiB = 1,610,612,736 bytes`, plus four bounded
plan reads, three installation-record reads, three configuration reads, request/
report reads, imports and metadata work. This is a source ceiling, not observed
fit or a new S/runtime budget. The distinct S read contract is not enlarged.
Parent CPU, directly waited CLI CPU and cgroup CPU are retained as separate
scopes, never added as though overlap had been resolved. Final receipt writing,
external transport/publication and other post-sample work still need accounting.

The request is at most 16 KiB. Existing receipt writes are at most 64 KiB each;
child log reads are at most 64 KiB; unified-cgroup reading requests at most
4,097 bytes and rejects more than 4,096. The path has at most 60 observation
records and 64 non-request records in total, one request, one inner child log,
one service console and at most 75 existing CLI command logs. Existing limits
remain 8 KiB per command log and 1 MiB for the service console. These selected
file ceilings do not establish complete retained-output or memory fit: copies,
protected inputs, import/runtime state, failed writes and external records remain
in the eventual whole-path census. There is no serialized source authority or
resume capability.

## Authored tests and remaining qualification

Static AST count: **38 cases in 17 functions, 114 prospective phases**, maximum
literal node-ID length 103. All are unexecuted. They cover the absent/running/
leader-exited-populated/terminal-empty/receipt/stop sequence; exact source and
report substitutions; preflight deadline exhaustion; lost acknowledgement;
terminal/final receipt failures; cleanup failures; stale invocation/group/CPU;
retained failed state; duplicate intent; fixed argv/disabled CLI; and service
wrapper first/supplemental errors. Five successor cases cover the direct-script
path guard, invalid public root/mismatched receipt store, and failed intent writes
before or after a fake partial retention. All original test-function ASTs are
unchanged. The path-guard case inspects source AST, not a second module execution;
actual formatting/lint/import qualification is still pending.

The lifecycle tests use fake Systemd snapshots/operations and fake lower-level
protected-plan APIs. They run the actual adapter's preflight joins, state machine
and report joins, not actual protected source validation or service dispatch.
One composition uses the actual existing receipt writer on owned temporary
files. The service-entry tests use a fake launch and fake service identity; they
cannot establish real cgroup, startup, owner capture or process closure.

Source-derived conservative fixture ceiling: at most 33 request files at 4 KiB,
nine other receipt files at 64 KiB and two child logs at 64 KiB, totaling
**856,064 bytes**. Request bounds are asserted in the authored tests. There are
at most 44 regular pathnames, no symlinks, hardlinks or FIFOs, and at most 101
fixture/test/control/cache directories in the original 33-case estimate, plus
four empty temporary roots for the new rejection cases: **105 directories** in
total. Those five new cases create no files; the original payload/pathname upper
bounds remain unchanged. The source-guard case reads this adapter once (currently
28,999 bytes); it creates no fixture output.
Most receipts remain in fake in-memory stores. Actual test data, logs/JUnit,
control records, CPU, wall and memory have not been measured; ordinary finite
controls must account for them before any test execution.

A later positive qualification must separately admit the protected runtime and
complete import/source/installation inventory, service-manager custody, exact
source activation, whole-parent deadline/usage control and real named-group
observations. It must include a benign leader/descendant case proving leader
exit alone is insufficient. Existing Unit19 failures, costs and unknowns remain
retained. No current result qualifies S/A, installation/pass2, exposure evidence,
whole scientific fit or a D1 batch.
