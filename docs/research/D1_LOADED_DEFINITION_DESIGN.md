# Proposed D1 loaded-definition boundary

Current implementation checkpoint: the [protected startup/capture source](D1_BOOTSTRAP.md)
and [actual original-owner preparation](D1_ORIGINALS.md) have independent source
review. The minimal typing repair is at 0c76a102. Private engineering checks
remain incomplete: 143 cases were collected on the preceding source, but no
test bodies ran before the 232-file type check failed. The repaired source
passed original ordinary CI on [PR #156](https://github.com/spei04/strange-physics/pull/156):
all six required jobs succeeded, including 6,240 tests and 232-file typing on
both Python 3.12 and 3.14. This evidence cannot establish guarded test execution,
protected runtime or scientific admission.
The separate [named-service lifecycle source](D1_OWNED_CAPTURE.md) is reviewed;
its 37 authored tests and runtime qualification remain pending.
The original proposal below remains design history; actual custody,
whole-process closure, installation/pass2 and scientific admission are pending.

Design only, based on `36fee7865e149a483b8cef377d92bc3a1cc1e100` and the
[accepted S ordering](D1_SOURCE_MANIFEST_DESIGN.md). Research owns this document;
Lead owns central progress and A. Unit18's
[current-file observation](D1_SOURCE_FILES.md) remains unchanged and its
qualification is separate. No project objects were instantiated, no project code
was imported, and no primitives, file fixtures or runtime checks were executed
for this design. No implementation is included.

## Recommendation: establish the import premise before another kernel

The next implementation prerequisite should be a small, disabled **fresh-child
bootstrap/control boundary**, reviewed against a fixed import plan. Then add the
original-binding comparator to that controlled flow. A standalone comparator is
useful for synthetic relationship tests, but another caller-supplied collection
of expected function objects would not make the D1 path safe to wire.

Keep two review units distinct:

1. Establish the controlled import interval and capture original definitions in
   a fresh process. Validate a closed source/runtime import plan, capture before
   mutation/installation, and report missing premises without producing S/A.
2. In that same interval, join the captured definitions to the live twelve
   `D1Reference` owners, the actual fixture owner, and the externally selected
   emitter. Preserve those originals for later installation and pass2 routing.

Neither unit changes study choices, calls a primitive as a probe, supplies a
budget, or makes an unchecked expected-object record authoritative. The final
catalog, fixture hook and d4 selection must be concrete before a complete D1
binding can succeed; partial engineering observations cannot substitute.

## What existing code actually supplies

* `tests/d1_source_files.py` observes current regular-file bytes and descriptor
  identities under independent expected pins and a caller-held root. It does not
  inspect the bytes from which an already-loaded function was created.
* `tests/d1_fixture_reference.py::verify_sources` checks seven checkout files and
  four loaded-module file copies, with helper/oracle path constraints. Its own
  docstring leaves commit/runtime authenticity to the outer guard. `__file__`,
  its resolved path and matching bytes now are origin-consistency observations.
* `src/strange_physics/installed_identity.py::verify_native_installation` requires
  an independently trusted `TrustedInstallation`; it verifies interpreter,
  package/archive, dependency membership/bytes and engine fingerprint. It is
  separately charged work. Its `__file__` origin checks do not retrospectively
  authenticate arbitrary existing D1 code objects or mutable module globals.
* Existing engineering control children demonstrate pinned helper/source inputs,
  isolated interpreter startup, fixed helper paths and capture of defining code
  objects before tests. They deliberately poison oracle methods and deny science.
  Their code-object identities and source hashes are useful engineering controls,
  not an available D1 import attestation or an original-owner installation.

The practical authority chain starts outside the candidate process: independently
accepted source/catalog pins, runtime/interpreter/dependency identity, and exact
reviewed bootstrap/control source and launch configuration. A candidate deriving
all expectations from itself cannot supply this chain. No existing helper currently
provides a complete protected D1 import record or captures all required originals.

## Small bootstrap boundary to make concrete next

Use an ordinary fresh invocation of the pinned interpreter and normal reviewed
Python imports, not a new loader, manual compile/exec, reload, or a second imported
copy manufactured to compare code. The existing isolated-child pattern is a
starting point, not code that can be copied unchanged. Recommend this standard
launch arrangement, still proposed pending protected startup/import-map evidence:

```text
<pinned-venv-python> -I -B -X pycache_prefix=<fresh-owned-empty-directory> <pinned-bootstrap>
```

It retains normal site initialization and the installed-native origin. It does
not authorize creating that directory or launching a process now.

* The outer control fixes exact executable and startup configuration, dependency/
  stdlib/runtime premises, permitted source roots and the import map. The source
  plan precedes S; no SHA(S) is assumed before pass1. Observe current source bytes
  and maintain the trusted immutable interval across imports and later checks.
* Require no preloaded D1 module or alternate `tests.*` alias. Admit only the
  source-owned list of canonical names; neither S strings nor caller-provided
  attribute chains select an import. Account deferred edges too. A final closed
  D1 import map does not yet exist.
* Preserve the native installation origin. Engineering checks prepend checkout
  `src`; `verify_native_installation` expects `strange_physics` from the verified
  site-package directory. A D1 control must not inherit that conflicting path
  list. Only fixed helper roots may be added while production loaded copies are
  joined to the expected checkout bytes and verified installation.
* Independently verify interpreter/venv configuration and startup inputs before
  launch, including applicable `.pth` and `sitecustomize` files. `-I` excludes the
  user site and environment-driven Python paths but retains normal site startup;
  executable startup hooks run before bootstrap checks. A later self-report or
  installation check cannot establish their prior trust. [Python startup](https://docs.python.org/3.12/library/site.html)
* The outer owner establishes an empty, non-symlink, owner-controlled cache prefix
  for this attempt and holds its trusted interval. The explicit command-line
  prefix redirects ordinary source cache reads away from existing `__pycache__`;
  `-B` prevents cache writes. A stale prefix cannot be reused, and its preparation,
  checks, retained failures and closure are counted. Sourceless/zip/custom loaders
  remain excluded for checkout-source members. Separately allowed runtime modules
  need explicit protected runtime coverage and the existing catalog origin/kind
  rules; they are not a fallback for mismatched source. Builtin/extension identity
  remains a runtime premise. [Cache reads](https://docs.python.org/3.12/library/sys.html#sys.pycache_prefix),
  [isolated mode and `-B`](https://docs.python.org/3.12/using/cmdline.html)
* Capture exact module, class, function and code-object references immediately
  after those controlled imports, before any poisoning or wrapper installation.
  Retain strong references through both passes. Name/origin/`co_filename` checks
  join the capture to the plan; they are not the provenance argument by themselves.
* Keep ordinary imports/bootstrap and all guards inside the declared control
  scope. No numerical method/producer or actual recorder/bridge event runs during
  this stage. Missing, unexpected, aliased or mutated imports fail closed. Failure
  is not permission to reload, substitute a dummy owner or retry a scientific unit.

A concrete input contract is the outer controller's exact protected expected
source/runtime plan plus held roots and the reviewed canonical import map. A
concrete transient output is a retained module/definition-anchor set and bounded
import observations, tied to that actual control invocation. It is not a new
serialized trust schema, and constructing its Python type is not authentication.
Inputs must not be supplied through candidate JSON or synthesized after the fact
from inspected objects. Authentication rests on the independently trusted control
that produced/holds the anchors, not a field such as `trusted=True`.

Do not add `-S` as an unreviewed shortcut: before Python 3.14 it affects venv
prefix initialization, while the existing verifier derives its package root from
`sysconfig`. Supporting a different startup path would need a separate compatible
source/control change. [Python version distinction](https://docs.python.org/3.14/library/sys_path_init.html)

The actual protected startup inventory, exact empty-prefix enforcement and closure,
complete import membership/deferred edges, trusted runtime evidence and bootstrap
receipts are still unspecified.
Resolve them in the next source/control review **before claiming this boundary
implemented**. Do not silently enlarge the S source-read allowance: Python's own
imports/startup/cache reads, installation checks and their copies are additional
work. Re-reading at most 64 loaded-source copies under the accepted per-copy bound
is still only file observation; it cannot repair an untrusted prior import.

## Original bindings: bounded interface after that prerequisite

Propose a private `observe_original_bindings(catalog_raw, anchors, reference,
fixture_owner, emitter)` boundary within the same trusted process. `anchors` means
the actual retained bootstrap result, not an independently accepted caller-built
view. Reparse raw catalog bytes; supplied names must equal its fixed five
definitions/14 roles/23 slots. There is no dynamic object discovery or S-selected
attribute evaluation. Return immutable transient role/slot observations and held
original references, without an authentication/readiness flag or serialized
addresses. No oracle/emitter is constructed, reset, replaced or invoked by this
comparator; transient bound-method/output objects are separately counted.

The actual `reference` must have the trusted `D1Reference` class/layout. Read its
fixed `channels` keys `strong/weak/future`, eight named arithmetic entries and
`constants_oracle`; do not accept a detached map of twelve convenient owners.
Require exact dictionary key sets/types and source-owned constant selectors.
The fixture owner must be the **same object** exposed by a reviewed producer
pre-call boundary. Current `D1FixtureProducer.run` creates it locally only after
inventory checks and `coefficients()/fixed_plan`; calling that existing producer
is not a way to obtain it before pass1 without earlier producer work. Designing
that hook is a separate prerequisite, not an implementation choice in this slice.

For d0–d3, compare the four actual class-namespace functions with retained trusted
function **and separate code-object** anchors. Checking the same function object
alone misses a changed `__code__`. Require fixed module/qualified names, the
trusted module globals dictionary identity, the reviewed ordinary attribute
lookup layout, and the source's absent defaults/keyword defaults/closures. Do not
call a descriptor selected by an untrusted class. Exact trusted class checks and
fixed ordinary Python method lookup permit binding; subclasses, partials,
decorators and instance shadows do not substitute for the original.

Require thirteen distinct oracle owners using `is`, not dataclass equality.
Resolve the 22 actual original bound-method slots from those owners and require
exact `__self__` and `__func__` joins to the retained four definitions. Fresh-state
checks may examine the six strict-zero counters, exact empty `values` dictionary
and `pi is None`; distinct empty caches preserve the source's independent-owner
construction. They prove current state only, never absence of past work/reset.
No cache contents are enumerated or numerical method executed.

The 23rd slot is only the injected `emit(native_log_probability)` in
`qualify_prefix`, not the normalizer's internal exponentials. d4's implementation
is still unselected. Its approved `python_function` or `runtime_builtin` kind,
module/member and exact original object must come from the outer reviewed plan;
Python code/globals/default/closure capture details or builtin runtime identity
must be fixed with that selection. Do not quietly choose `math.exp`, a lambda,
or a generic wrapper. A missing d4 anchor prevents a complete result.

Function/global dictionary identities do not freeze their mutable contents,
builtins, dependencies or import hooks. The controlled unchanged interval remains
necessary; there is no claim of hostile-Python isolation. Inspecting an unused
correct callable also proves no routing: this first boundary observes originals
and actual owner containers only. The later installer must capture those retained
originals, and pass2 must join the actual consumer to the exact recorder wrapper.
Post-install checks cannot simply rerun a pre-install no-instance-shadow check:
reviewed wrappers intentionally change the consumer route. Their exact permitted
capture/layout and retained-original checks belong to the separate installer.

## Bounded tests, work and construction order

The comparator's source census can be small: one bounded catalog parse; five
fixed definition rows; thirteen owner rows; 23 slots; at most 78 pairwise owner
identity comparisons and 78 cache-identity comparisons; 104 fixed fresh-state
field inspections; two bounded live dictionaries (3 and 8 entries) and one
constants-owner selection. No filesystem/primitive work or raw source copy belongs
to that kernel. Exact code/default/closure checks for d4 and the bootstrap import,
file/read/FD/copy/receipt census remain unresolved until concrete source exists.
These counts are a proposal to test against code, not an allocation or runtime
measurement. Strong-reference retention and parser/object overhead must be counted.

Meaningful fake-only tests should cover an independent literal role map, a wrong
actual reference container despite correct detached owners, duplicated owners or
shared caches, subclasses/shadows, same-name different functions, mutated
`__code__` on the same function, wrong bound `__self__`, missing/extra slots,
nonzero/bool counters and d4 absence/kind substitution. Invoke none of the fake
primitive callbacks. Scoped mutations must restore originals. Separately test
bootstrap controls with tiny owned non-scientific modules: wrong protected pins,
preloaded/alternate aliases, unexpected origin/import, stale cache policy failure,
substitution before anchor capture and failure with no downstream activation.
A test fixture claiming its own protected pins is only a synthetic control test.
The final literal case/output/operation census precedes any engineering admission.

Keep the accepted acyclic sequence:

`trusted source/runtime/import interval + actual originals -> seal S -> retain C/T
-> construct real Bridge/Recorder and install wrappers -> pass2 current sources,
held originals, captures and actual routing -> candidate A / outer admission`.

Do not reseal S to insert wrapper identities, use deferred append callbacks,
replace oracle instances, repeat imports as a probe, or promote any partial
conditional observation into A. This design supplies neither execution authority
nor the missing final catalog, producer hook, emitter or installer.

## Finite dependency sequence to the first D1 evidence

This orders the existing integration/fit/admission obligations; it adds no
scientific gate, allowance or reset of earlier charges.

1. **Unit18:** the bounded checkout observer is implemented, with qualification
   tracked separately. It supplies current-file observations only. The S/catalog
   parser is implemented; a final complete catalog and trusted import map are not.
2. **Bootstrap and originals:** qualify the concrete launch/control above, bind
   protected runtime/import evidence, bind the twelve actual reference owners,
   expose the same fixture owner through a concrete hook, and fix approved d4.
   The hook/emitter and complete
   original-binding flow are unresolved; existing file checks cannot fill them.
3. **S and installation:** implement actual S construction/retention, join the
   existing C/sink and T-retention components, construct the existing real
   recorder/bridge chain, and install the reviewed wrappers. Verify pass2 against
   held originals and actual consumers before candidate A. Component helpers
   exist; S sealing, installer, complete routing and A joins remain unresolved.
4. **Whole-path fit:** begin source-derived byte/work assessment now using the
   frozen census and existing caps. Complete it when remaining wire formats,
   failure records, call sites and retention copies are concrete, before costly
   execution. Do not wait for D1 labels to discover an impossible layout. Measure
   complete-path resource fit only in separately reviewed bounded qualification
   using admissible synthetic/previously exposed material where valid; those
   measurements cannot substitute for unmeasured D1 work or claim science results.
5. **Admission and evidence:** assemble the existing required source, exposure,
   numerical, accounting, storage and whole-path evidence for reviewed execution
   admission. Only then may the completed fixed D1 batch produce its first retained
   D1 evidence. Missing inputs or unknown costs remain explicit; source progress
   and synthetic checks do not spend an inferred scientific balance.

## Current handoff evidence — 2026-10-31

A read-only review of source `f36f0895` refreshed the known candidate closure to
49 members and 968,648 bytes. Its largest ordinary member is 69,136 bytes;
`uv.lock` is 250,735 bytes. These fit the distinct existing file limits.
This is an incomplete candidate set: final catalog, runtime, bootstrap, installer
and driver choices still need a complete import/member census.

The unchanged [codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md) establishes a
16,860,600-byte lower bound for full-success raw JSONL, exceeding the 16 MiB
transcript partition. Its compact 13,432,214-byte envelope remains conditional on
the exact identities, copies and failure rules. It is not proof that all science
artifacts fit 64 MiB. The 33,947,906-byte two-pass source-read ceiling also excludes
extra `verify_sources` invocations, startup/imports and runtime verification.
Complete those source-derived counts before costly whole-path qualification.

A separate bounded inspection found a noneditable installed package at the
expected engineering-environment location. Fifteen selected files—12 `native_*`
modules plus the initializer, `finite_log_weights` and `installed_identity`—match
the frozen checkout bytes. This establishes current-byte agreement for those
files only. The sole top-level `.pth` file imports `_virtualenv`; its hook body
was not executed or inspected in this check. Four inspected environment
ancestors have mode `0775`, and `pyvenv.cfg` has mode `0664`. These observed
group-write bits do not identify other users or establish hostile access, but
they cannot supply protected startup custody. No permissions were changed.

The next coherent handoff is the concrete protected startup/import plan and
actual original-owner flow described above, including the same fixture-owner
hook and selected d4. Review the startup hook, root/ancestor custody and complete
runtime evidence within that flow. Matching installed bytes must not become an
implicit trusted flag, and another detached expected-object comparator would not
resolve these dependencies. S retention, installation, pass2, the complete binder,
exposure inputs and measured whole-path fit remain unfinished.

The [approved exposure and initial custody decisions](D1_EXPOSURE_DECISIONS.md)
are now present alongside this design. Their approval stands; the actual
six-world inventory and overlap disposition remain pending. These inspections
made no project imports, scientific calls, environment changes or new allocations.


## Next concrete ownership and closure integration

The current controller can observe a valid capture report and a reaped leader.
It deliberately leaves owned-tree closure unknown and final capture acceptance
false. The next integration must connect this observation to the existing
Systemd ownership operations, not add a boolean that declares cleanup complete.

Reuse the reviewed Systemd, Snapshot.bind and terminal/retained-failed cleanup
checks in scripts/grid_q1_supervisor.py. Add a narrow, fixed capture command and
report join. Preserve GRID's existing command, source, result and outcome
validation: those rules describe GRID numerical work and cannot validate a D1
capture report unchanged. This work implements the existing integration
obligation; it creates no scientific gate, budget or retry permission.

The capture-specific plan must bind the source/controller/bootstrap, independently
accepted protected-record digest, one exclusive output/cache root, exact
interpreter and isolated/cache-prefix argv, and an explicitly admitted finite
profile. Record the exclusive intent and whole-attempt deadline/accounting
baseline before the first plan read or preflight. An exhausted preflight must
submit nothing. Keep the same deadline through submission, observation,
termination, stop and final records; a service runtime limit covers its subtree,
not the preceding parent work.

Submit once and retain the actual unit, InvocationID, cgroup, quota and accounting
from that original invocation. Join the exact bounded report bytes/hash to the
same source, admission, unit and output root. Retain terminal accounting before
stop and require the bound terminal/empty state, followed by confirmed cleanup.
A disappeared group is acceptable only under the existing previously-bound
cleanup predicate. Rebind named-unit operations before signaling; never signal a
numeric PID or process group after reap. Missing or late records, lost submission
acknowledgement, first faults and unknown cleanup remain nonaccepted even if
cleanup later succeeds.

The first composition test should use the real preflight/control/report join with
owned synthetic inputs and fake Systemd observations:

absent → bound/running → leader exited but group populated → same invocation
terminal and empty → terminal receipt → stop → confirmed empty

Require one submission and no acceptance while the group is populated. Check the
exact source/report/admission/unit join, retained monotonic accounting and absence
of numeric PID signals. Add stale-identity/report, exhausted-preflight,
lost-acknowledgement, receipt, cleanup and retained-failed cases using the existing
supervisor tests as the behavioral reference.

Actual complete-path qualification remains a separately admitted protected-runtime
test: the real fixed startup/capture, thirteen actual oracle owners, twenty-two
original methods and the retained emitter, zero primitive work, real named-unit
observations and external ledger closure. A separate benign leader/descendant
fixture must demonstrate that leader exit does not prove tree closure. No such
service or test has run. This qualification cannot automatically activate S/A or
the scientific batch, and its complete parent/service costs remain unmeasured.
