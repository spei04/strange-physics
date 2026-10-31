# Proposed D1 loaded-definition boundary

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
starting point, not code that can be copied unchanged:

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
* Fix startup hooks and bytecode-cache policy explicitly. `-I` does not itself
  establish trusted site initialization; `-B` prevents cache writes, not reads.
  Current `.py` hashes therefore do not cover an unverified consumed `.pyc`.
  The next control review must choose either a proven trusted cache inventory or
  a standard fresh-cache arrangement that cannot consume stale caches; this
  document does not select a loader workaround or allocate a new cache/root.
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

The exact startup/cache enforcement, complete import membership, deferred imports,
actual trusted runtime evidence and bootstrap receipts are still unspecified.
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
