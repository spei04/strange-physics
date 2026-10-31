# D1 protected bootstrap and original-object capture

Status: source interfaces and the minimal test typing repair at
[0c76a102](https://github.com/spei04/strange-physics/commit/0c76a1021f87f76d638d598d6ea5e64fb608e797)
are independently reviewed. Private engineering qualification is **incomplete**.
Both guard sentinels and collection of 143 cases/zero phases passed at 11629b1.
The subsequent full check passed formatting/lint, then found nine typing errors
in one test among 232 checked files. Renaming an integer index fixed the source
conflict without changing assertions; that repaired source has not repeated the
private check. No private test bodies have run, and the older collection does
not qualify the repaired bytes.

All 19 recorded child processes closed. The three attempts remain charged at
60.297004 CPU seconds and 76.197045 wall seconds; the 120-CPU/300-wall/8-MiB
private account is unchanged. The first collection failure intercepted
retained math.exp before its body; its exact caller remains unknown.
The reviewed successor initializes the pinned Python random module before
adding project paths, then arms the unchanged project/test prohibitions.
That ordinary standard-library initialization may call exp; there is no
whole-invocation zero-exp claim or protected-startup qualification.

The separately admitted original [PR #156 CI run](https://github.com/spei04/strange-physics/actions/runs/41194699505)
passed all six required jobs on frozen 838a211 and merge 92eb0b4, whose tree
matches the head. Python 3.12 and 3.14 each passed 6,240 tests, 232-file typing,
1,567 schema checks, packaging and one 8/8 CLI smoke; each analytic job passed
24 cases/72 phases. The two serializer warnings per runtime and three audit
flag warnings are unchanged. The evidence set retains 25 files/851,370 bytes.
The 1,889 observed job-seconds and 958-second run interval are separate elapsed
scopes, not CPU or a complete cost account.

This is ordinary software evidence. It cannot substitute for the unexecuted
guarded 143-case/429-phase window, protected runtime or scientific admission.
The earlier 233-file typing
estimate below is superseded by the observed 232-file scope.

The standalone controller exits 64. Final capture acceptance remains false
even for a clean direct-child observation. The separate
[named-service lifecycle source](D1_OWNED_CAPTURE.md) is reviewed, with 37 tests
still unrun; it is outside the frozen PR #156 CI scope.
The current environment is not admitted for protected startup. No child
bootstrap, installation, environment repair or D1 scientific batch ran.

## Concrete ownership and call path

`scripts/d1_bootstrap_control.py` runs in an independently accepted, single-threaded
Linux controller context. Its callable `launch(plan_path, plan_sha256, output)`
reads a protected record, checks the actual controller/interpreter, closed
inventory, installed build and fixed module routes, then starts exactly one
child. The independently accepted outer invocation must supply the record path
and digest. A matching checksum or caller possession of this function does not
establish authority. The source does not embed its own record's digest, avoiding
a self-pin cycle.

The fixed child command is:

```text
<pinned-venv>/bin/python -I -B -X pycache_prefix=<fresh-owned-empty-directory> \
    <checkout>/tests/d1_bootstrap.py <protected-record> <record-sha256> <cache-directory>
```

The parent uses no shell, passes only `LANG=C.UTF-8` and `LC_ALL=C.UTF-8`, closes
unrelated descriptors, redirects standard input to the null device, and retains
combined output in one exclusively created owner-readable log. Normal site
initialization remains enabled. The target interpreter is never launched to
perform its own parent preflight.

The child checks its version, virtual-environment prefix, isolated/write-bytecode
flags, cache prefix and exact startup search path. It adds only the fixed helper
directory, never checkout `src`. Standard imports must yield the exact ordinary
source loaders and origins in the protected map. All loaded modules must have
inventory-backed origins or explicitly enumerated built-in/frozen identities.
A pinned file alone does not permit importing it under an arbitrary name.

Before importing any consumers or the original-object helper, the child retains:

1. The actual canonical endpoint module and its actual `EndpointOracle` class.
2. The four exact Python function objects in order `position, exp, log,
   circle_constant`, plus four separately retained code objects.
3. The actual runtime `math` module and its exact built-in `exp` object.

It then imports only the fixed consumers, builds `OriginalAnchors(*held_refs)`,
and calls:

```python
prepare_originals(anchors, root=root, commit=commit, pins=source_pins)
```

The helper belongs to the paired original-owner implementation. It constructs
the actual `D1Reference` and `D1FixtureProducer`, returns the actual 13 owners in
fixed role order, 22 bound methods in fixed slot order, and the retained emitter.
The producer's actual pre-call owner must be the first owner. The bootstrap
rechecks the canonical module, class, functions, separate code objects and emitter
after consumer imports, after anchor construction, and after helper return.
The helper independently checks the original identities around its construction
boundaries. No endpoint method or `math.exp` call is used as an identity probe.

These are strong references in the same child. The capture-only completion record
contains counts and the source commit, not object addresses or serialized
authority. After the child exits, its anchors are gone. A future same-child
continuation requires a separate reviewed integration; a later child cannot
recover these objects from a receipt. No S/T/A retention, recorder, bridge,
cursor, fixture generation, native prediction or scientific evaluation is
activated here. `primitive_calls_permitted: false` is a scope statement, not a
measured call census.

## Protected inputs and closed source map

The launch record has an exact field set, version
`d1-protected-capture-v1`, an exact source commit, canonical absolute paths,
file hashes/sizes/owners, closed directory membership, explicit interpreter
links, startup paths, absent startup-path observations, hook files, built-in and
frozen inventories, installation evidence, and the fixed module map.
Unknown fields, including caller-supplied trust flags, are rejected. The exact
required keys are `version`, `source_commit`, `checkout`, `interpreter`,
`bootstrap`, `controller`, `controller_interpreter`, `site_packages`, `stdlib`,
`venv_root`, `python_version`, `startup_hook_files`, `absent_startup_paths`,
`installation_record`, `files`, `directories`, `links`, `import_map`,
`startup_sys_path`, `frozen_modules`, and `builtin_modules`.
File entries are `path/sha256/bytes/uid`; directories are `path/uid/entries`;
links are `path/uid/target`. The outer record's protected digest and provenance
are separate from those data fields.

The controller checks non-writable group/other permissions and exact owner/type
for files and directories, single-link regular files, and non-writable ancestors.
It reads regular files without following links and checks stable file identity
around each bounded read. Every observed member of a closed directory must have
a file/directory/link entry. Membership scans stop after the expected count plus
one rejecting observation.

Only explicit interpreter links at the three fixed virtual-environment entry
names are allowed. Traversal is literal, bounded by the link inventory, cycle
free, and requires every hop to be an inventoried protected link or regular
file. An unprotected intermediate link is rejected even if its final target is
the expected interpreter. The controller does not use an ultimate `resolve()`
result as evidence for intermediate custody.

The virtual-environment configuration must be pinned, match the exact version
and disable system site packages. The installation must use the fixed Linux
virtual-environment layout. Existing independently accepted release-candidate
installation evidence must match the source commit and interpreter, and its
lock, archive and provenance must be protected. Package and dependency file
membership, sizes and hashes must match that evidence. The source-derived
project modules must also match their checkout counterparts byte for byte while
loading from the installed package.

The current capture path's static closure, including imports inside function
bodies and type-checking branches, is **24 modules and 83 import edges**:

| Origin | Canonical modules |
| --- | --- |
| Checkout helper files, 10 | `d1_bootstrap`, `d1_bounds`, `d1_fixture_reference`, `d1_originals`, `d1_prefix_evidence`, `endpoint_belief_reference`, `grid_q1_bounds`, `grid_q1_evidence`, `grid_q1_inputs`, `grid_q1_reference` |
| Installed package, 14 | `strange_physics`, `bounded_json`, `calibration_fixture_contracts`, `contracts`, `control_contracts`, `finite_log_weight_contracts`, `fitting_contracts`, `laws`, `native_endpoint_belief_contracts`, `native_prediction_contracts`, `native_spring_contracts`, `prediction_contracts`, `research_contracts`, `serialization` |

Names in the second row after `strange_physics` have that package prefix.
This closure is source evidence for this capture path. It does not establish
complete third-party, standard-library, extension, dynamic-loader, installed
distribution or deferred runtime provenance. Those remain prerequisites of the
independently reviewed protected runtime record. Empty or partial runtime
inventory cannot be promoted into an accepted controller context.

No `tests.*` alias, unmapped checkout `tests`/`src` origin, or noncanonical
installed-project alias is allowed. Pinned dependency/runtime modules under
checkout `.venv` remain permitted; their location inside the checkout does not
make them checkout source. The inactive names
include the actual modules `d1_primitive_recording`, `d1_primitive_sink`,
`d1_codec_append`, `d1_table_retention`, the primitive bridge/codec, and owned-file
observation helper. File inventory membership does not make these importable.

Python 3.12's protected `typing.py` registers two namespace classes in
`sys.modules`, `typing.io` and `typing.re`, which intentionally have no module
specification. Only these two names are accepted by exact identity to their
canonical `typing` module attributes. The parent must use the ordinary source
loader and the pinned `<stdlib>/typing.py` origin. An impostor, a different
parent origin, or any other no-specification entry remains rejected. These
synthetic compatibility cases do not execute the target interpreter.

## Current custody and runtime blockers

Read-only readiness inspection found group-writable virtual-environment
directories and `pyvenv.cfg`. Current installed-byte comparisons cover selected
native files, not the complete installation/runtime. No accepted protected
whole-runtime inventory or maintained exclusive custody interval has been
established. The controller must reject these conditions before `Popen`.
This implementation neither chmods nor reinstalls or repairs the environment.

The known normal startup hook was separately read as regular source without
executing it. `_virtualenv.py` is 5,246 bytes with SHA256
`cfb3db86aaa53bb62b5ff764970bec2d71c9228590a0ebec57f6ec926cc0bf1a`.
Its finder handles the reviewed distutils/setuptools distribution hooks. This
is an explicit startup review, not a claim that every runtime/deferred edge has
been reviewed. Its `.pth`, source and deferred runtime requirements belong in
the protected record. The exact reviewed `.pth` is 18 bytes, `import _virtualenv`
without a final newline, SHA256
`69ac3d8f27e679c81b94ab30b3b56e9cd138219b1ba94a1fa3606d5a76a1433d`.
Preflight derives applicable startup candidates from closed directory membership,
requires both exact known hook files when present, and rejects unreviewed
`.pth` files, customization modules and existing startup archives. An empty
caller hook list cannot omit an observed hook. The presence of this reviewed finder does not permit
custom loaders for checkout modules.

The external trust premise includes the independently accepted controller's
interpreter and source, the frozen outer invocation, complete startup/runtime
and installation evidence, and an unchanged exclusive-owner interval. Before
and after checks cannot by themselves exclude a hostile same-UID writer between
checks. Python audit hooks and import checks are not a hostile-code sandbox.

## Process, read and output bounds

These are finite interface ceilings, not measured whole-operation usage or a
new allocation:

| Item | Bound / treatment |
| --- | --- |
| Protected plan | 4 MiB; exact schema; duplicate keys rejected by parent |
| Combined file/directory/link inventory | 32,768 entries |
| One protected file | 64 MiB |
| File payload per full inventory verification | 512 MiB |
| Full inventory verification | Once before child and once after it |
| Additional input reads | Plan once at each parent boundary and once in child; installation record once per verification, at most 4 MiB; virtual-environment config once per verification, at most 64 KiB |
| Directory observation | At most expected membership + 1; output at most 3 entries; cache at most 1 |
| Processes | Exactly one direct child per invocation; no retry |
| Child CPU / address space | 30 CPU seconds / 1 GiB; per-process kernel limits |
| Child wall / termination wait | 60 seconds / 5 seconds |
| Child file size / descriptors | 64 KiB / 128; core dumps disabled |
| Capture-only report | At most 4 KiB |
| Retained child output | One log, at most 64 KiB; one empty cache directory |
| Parent receipt | Returned `LaunchResult`; any outer persistence/publication is separately owned and charged |

The two full verifications can read up to 1 GiB of inventory payload, plus the
separately bounded records above. Per-file reads may hold chunk buffers and
their joined copy simultaneously. Python startup, import decoding, shared
library mappings, parser structures, caches, filesystem metadata and allocator
copies are additional work. These ceilings do not promise that a real inventory
will fit the proposed synthetic engineering scope.

The child may not spawn or use sockets. The first denied event is latched with
at most 128 characters and no arguments; catching the rejection cannot erase
it. The latch is checked after imports, anchor construction, immediately before
owner construction, after preparation and before reporting. It has no production
reset API. This remains a tripwire for the reviewed path, not a sandbox.

Closure reporting refers only to the actual owned direct child. The startup
interval precedes the child audit hook, so leader reap is insufficient evidence
for owned descendant closure. The result may set `capture_observed=True` but
always reports `owned_tree_closed=None`, `captured=False`, and the unproved
outer-closure reason on an otherwise clean observation. No caller boolean can
override this. A reviewed outer owned-group lifecycle must be connected before
final capture acceptance; this integration is explicitly unimplemented.
Timeout or signal/wait failure remains unsuccessful, with unresolved closure
explicit. The parent attempts final wait even if signaling fails. No PID is
reused after reap and there is no detached cleanup or automatic retry.

The result retains exit, timeout/reap state, post-check status, log size,
elapsed invocation wall time and, only after reap, the change in waited-child
CPU usage. That CPU measurement requires the accepted controller to have no
other child workload. It excludes parent preflight, parent readback, SSH/IAP,
source preparation, CI and publication. None is silently assigned zero. The
parent records a provisional capture observation only after direct-child reap,
exact bounded report validation, output census and protected-input recheck.
These conditions do not establish final owned-tree acceptance.

## Bounded engineering qualification proposal

This is a proposal, not an admission. The current authored focused suite has
**101 cases in 35 test functions**, or **303 prospective pytest phases**:
45 controller cases and 56 bootstrap cases. It exercises synthetic file
inventories, fake `Popen` handles, fake modules and owners, negative origin/
custody/chain cases, and direct audit-event validation. No test starts a real
child or imports real D1 consumers to construct actual owners.

The fixture design has at most 188 retained regular pathnames (one pair is a
deliberate hard-link fixture), 13 symlink names, 96 fixture directories plus
31 pytest test directories. There is no FIFO. This is a conservative authored
census before execution, not observed retained output. Regular fixture payload
is below 16 KiB; with symlink literals bounded by 4,096 bytes each, combined
fixture payload stays below 96 KiB. Pytest/JUnit/phase logs, source snapshots,
helper controls and failure records are additional output.

Recommended first qualification uses a fresh, separate cumulative engineering
unit capped at **120 CPU seconds / 300 active wall seconds / 8 MiB retained
output**, with the established per-attempt 5 CPU / 10 wall closeout reservations
and 10 CPU / 30 wall withholding. The paired originals source and tests must
be integrated and reviewed before freezing the actual commands and total
case census; this proposal does not allocate an additional allowance to them.

The necessary checks are:

1. Rehash the integrated source, pinned environment, controller/collector and
   guard. Bind the exact changed Python files. Preserve all raw predecessor
   source and review findings.
2. Perform the established bounded formatting/import-order preparation and
   guarded collect-only step. Require exact frozen node IDs and zero test
   phases; include preparation failures in the same cumulative ledger.
3. Freeze the prepared source, then run format/lint, full source discovery for
   strict typing, and the focused fake-only tests. Do not replace full typing
   with a narrow import-context workaround. The expected combined discovery is
   approximately 233 files (prior 227 plus this slice and paired originals);
   actual source discovery must establish the exact count.
4. Require exact passing phase census, zero real process/network/scientific
   attempts, source/environment/helper parity, complete owned-process closure,
   no-follow output census including symlink and hard-link names, and one
   bounded retained final checkpoint.

The fake-only suite can retain the scientific entry denials and oracle poisons:
it uses synthetic functions and modules instead of actual scientific objects.
All OS fault injection remains helper-local. A fake process's `wait` result
tests the controller's decision logic; it is not a real child-closure result.
The static AST census is not a substitute for guarded collection.

## Separate actual-startup qualification

A successful fake-only run cannot qualify the real protected fresh child.
Existing ordinary collectors add checkout `src`, preimport definitions, poison
oracle methods and pin checkout code origins. Those choices conflict with the
installed-origin and intact-original requirements of this path. They must not
be silently relaxed or represented as real startup evidence.

After the complete external runtime/custody prerequisites are satisfied, a
separate finite proposal must freeze the actual parent invocation, exact record
and installed identities, one child, all source/deferred/runtime inventory and
complete accounting/output closure. It must preserve original function objects
while denying entry by their actual defining code, deny producer/native
scientific entry points, permit only the reviewed zero-call owner constructors,
and check the actual `math.exp` object on C-call profile events. A benign dummy
Python function and benign unrelated C callable can qualify fail-stop behavior;
real scientific functions or `math.exp` must never be negative probes. Profile
and audit instrumentation must not be described as a security sandbox.

Source authoring, pre-anchor assembly, bootstrap, controller work, CI,
transport, failed attempts, final records and publication all remain in scope
of the relevant accounting records. Existing unknown historical usage remains
null, previous failures remain charged, and no old remainder is transferred or
refunded. A complete actual-startup admission is not yet possible, and no
scientific D1 batch follows automatically from this implementation.

## Review history

The initial source checkpoint was independently reviewed before execution.
Successor source repaired an unprotected-intermediate interpreter-link gap,
actual inactive-helper names/unmapped checkout origins, and unbounded directory
enumeration. These were source-review findings, not runtime outcomes. The
synthetic startup and registry tests were also expanded before qualification.

A later source-only review repaired the two Python 3.12 `typing` namespace
aliases without introducing a general no-specification exception. It also made
the heterogeneous startup-policy test fixture type explicit. Neither change
constitutes runtime or typing qualification.
