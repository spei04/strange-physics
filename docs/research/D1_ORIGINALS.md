# D1 same-child original-owner preparation


Current engineering status is [recorded with the integrated bootstrap](D1_BOOTSTRAP.md):
source review accepted the fixed owner preparation and the 0c76a102 test typing
repair. The private check remains incomplete; 143 cases were collected on the
preceding source and no test bodies ran. Ordinary CI verification is pending
and will not substitute for protected-runtime or scientific qualification.

The following paragraph describes the original source-authoring checkpoint.

Source-only checkpoint based on `9cde8f7648be1da7564d93cb4669c8456923fd8e`.
Code commits `678dc99c95016bd254c8872ffcc931676ce7f019` and
`ea909dce691308747de063e27a7ffe5d1275b3c9` add a concrete fixture
owner hook and the fixed preparation call used by the separately authored
bootstrap. No project import, formatter, type check, test collection, test body
or primitive was executed during authoring. This is not runtime qualification,
source authentication, S sealing, installation or scientific admission.

Research owns the two fixture files, `d1_originals.py`, its tests and this guide.
Platform owns the outer control and same-child bootstrap in the other reused
checkout. Quality reviews immutable source; Lead owns integration, resource
coordination and the private ledger. The [accepted ordering](D1_LOADED_DEFINITION_DESIGN.md)
and [S contract](D1_SOURCE_MANIFEST_DESIGN.md) remain in force.

## Concrete integration contract

The fresh bootstrap captures, immediately after their canonical imports:

1. The actual `endpoint_belief_reference` module and exact `EndpointOracle` class.
2. Its four class-dictionary functions in the order `position`, `exp`, `log`,
   `circle_constant`, and each **separate current code object**.
3. The actual `math` module and exact `math.exp` builtin, without invoking it.

These references precede imports of `d1_fixture_reference`, `d1_prefix_evidence`
and `d1_originals`. After fixed consumer imports, bootstrap builds the frozen,
slotted `OriginalAnchors` record with fields in this exact order:

| Field | Type |
| --- | --- |
| `oracle_module` | `ModuleType` |
| `oracle_class` | `type[EndpointOracle]` |
| `functions` | Four `FunctionType` references, in the order above |
| `codes` | Four `CodeType` references, in the same order |
| `math_module` | `ModuleType` |
| `emitter` | `BuiltinFunctionType` |

It calls only the source-owned entry:

```text
prepare_originals(anchors, *, root: Path, commit: str,
                  pins: tuple[SourcePin, ...]) -> PreparedOriginals
```

The seven producer pin paths are fixed by the existing producer contract. The
helper validates their order/shape and the absolute declared root/commit; it does
not read files or authenticate those declarations. The outer protected attempt
owns once-only invocation, partial-construction facts and failure retention. It
must not call this function again to replace missing/failed objects. There is no
module-global resettable singleton or independent retry/permission mechanism.

`PreparedOriginals` is a frozen, output-only record holding `reference`,
`producer`, `owners`, `original_methods` and `emitter`. Its thirteen owners are
ordered fixture, strong, weak, future, eight arithmetic case owners in the fixed
case order, then constants. The 22 bound methods follow S slots j00–j21: four
positions; each arithmetic owner's exp/log; constants log/circle_constant. The
exact emitter is j22. The result remains in this same process; a serialized
address, detached owner map or reconstructed DTO cannot replace these objects.
There is no authentication/readiness flag.

The helper checks the saved function **and** code identities, globals-dictionary
identity, fixed names and absent defaults/closures; canonical module/consumer
aliases; and exact `math.exp` identity before construction, after all owners are
constructed and immediately before completion. It validates actual ordered
reference containers, exact owner types, distinct owners/caches, six strict-zero
integer counters, empty caches, absent pi and no instance method shadows. Bound
slots must join those owners and captured functions. Owner identities are checked
again before return. The three fixed classes must retain ordinary field layouts:
no lookup/set hooks or conflicting class descriptors, and their own built-in
instance-dictionary descriptors. Freshness/container reads use exact instance
dictionaries and exact field sets, not potentially substituted properties.
This closes the constructor-side descriptor window found in the initial review.
No function is invoked as an identity probe.

## Fixture owner lifecycle and legacy behavior

`D1FixtureProducer.prepare_reference_owner()` constructs and retains one actual
owner before any `verify_sources`, inventory, coefficient, plan or producer work.
`prepared_reference_owner` borrows that successful object without allocation or
ownership transfer. A separate retained identity anchors that object. A later
`run` checks it before producer work and again before the first reference call;
missing, wrong-type or substituted prepared owners fail instead of entering the
legacy allocation path. Only a producer whose preparation was never used can
allocate at that legacy point.

Preparation marks its opportunity before construction. Constructor failure,
repeated preparation and swallowed prepare/run reentry latch the first exception
and consume the producer. A subsequent `run` raises that same first preparation
exception object. A callback returning normally after swallowed reentry
cannot produce a successful preparation. No reset or detached owner injection is
available. Existing unprepared callers still allocate at the original point in
`run`, after source/input/inventory/coefficient/plan checks. Thus an unprepared
source failure still allocates no oracle. A prepared source failure instead
retains one unused owner but still reports zero lookups; this earlier metadata
allocation is explicit and is not numerical work or a refund.

The original run body, fixed 13-position traversal, three reuse rows, round-once
rules, existing guards and failure denominators are otherwise unchanged. The
legacy in-memory producer remains callable only under its existing separate
execution authority; the new hook does not authorize `run`.

## Selected emitter and trust that remains external

For this concrete source flow d4 is the existing injected `math.exp` route:
`runtime_builtin`, module `math`, qualified name `exp`. It is supplied only to
`qualify_prefix`'s `emit(native_log_probability)` slot. It does not replace the
native normalizer's internal exponentials. Capturing the builtin adds no
primitive invocation or change to the frozen 55,100-call census.

The prior D1 adapter tests used a fake emitter; choosing this source route does
not claim actual installed-runtime qualification. The future catalog must bind
its trusted-runtime member, independently protected runtime/library evidence and
actual consumer routing. This helper's checks cannot establish those premises.

Observed installed native byte agreement is not protected startup custody. The
known `0775` environment ancestors, `0664` configuration and `_virtualenv` startup
hook still require the separately reviewed outer preflight. No permission, cache,
interpreter, environment or import-origin modification is made here. Mutable
module/global state and already-loaded provenance remain within that trusted
interval; this is not hostile-Python isolation. Missing bootstrap/runtime proof
must stop before any S/A or activation, even if object joins are self-consistent.

## Authored cases and qualification categories

The counts below are static AST counts, **not collected or passing outcomes**.

| Scope | Functions | Cases | Prospective phases | Permitted future qualification |
| --- | ---: | ---: | ---: | --- |
| New `test_d1_originals.py` | 9 | 42 | 126 | Intact-original capture/constructor tests under defining-code denials |
| Existing fixture tests at the actual base | 17 | 42 | 126 | Existing separately scoped synthetic producer behavior |
| Added fixture hook tests | 8 | 11 | 33 | Explicit fake/zero-work hook regressions |
| Combined fixture module | 25 | 53 | 159 | Existing plus new fake-producer category |
| Both modules | 34 | 95 | 285 | Sum only; not one implicitly admitted run |

The older 43-case historical qualification records are preserved. The actual
current base contains 42 cases; no inherited test was removed or changed. Every
original fixture test function's AST, including its assertions/decorators, is
identical to the base. The new original-test parameter IDs are explicit, short
literals; its maximum static node-ID length is 100. The added fixture cases
use explicit short IDs too, with maximum length 117.

The 42 original cases cover one full actual-container/slot join; ten malformed
anchor variants; five malformed source declarations; five changed consumer/alias
cases; nine wrong owner/container/cache/state cases; three post-construction
function-code/emitter/alias changes; two frozen-output cases; and one exact
constructor-exception case; plus six post-construction descriptor/lookup-hook
substitutions across the oracle/reference/producer classes whose getters must
never run. They never invoke producer `run`, coefficient/plan
work, reference methods or the emitter. Their local fixture denies higher-level
producer/reference paths while preserving the four real function/code anchors.
The reviewed engineering collector must deny entry to all five actual oracle
code objects and `math.exp` c_call without replacing the anchored methods. The
old collector's destructive method replacement is incompatible with these tests.

The eleven new fixture cases cover preparation before producer work; exact owner
reuse across one real producer run with the **existing fake oracle**; legacy
source failure before allocation; prepared source failure retaining an unused
owner; allocation failure/no retry; repeated preparation/no replacement; and
two swallowed preparation reentries (prepare/run); and three prepared-owner
loss/substitution/wrong-type cases rejecting before work or replacement. The
first-error assertions now retain the exact earlier allocation/reentry failure
through subsequent run rejection. The same-owner success case
does execute coefficient/plan and synthetic-result validation work. It does not
execute a real endpoint solve. It belongs to the separately explicit fake-producer
or ordinary CI scope, not the 42-case original-capture check. Scoped mutations
restore before teardown. No test adds actual filesystem fixtures or real threads.

## Finite work, retention and remaining joins

A successful helper call constructs exactly one `D1Reference`, one producer and
13 oracle instances. Its three anchor passes check four definitions each and
perform nine fixed class-layout checks with 96 declared field visits. Two owner
passes validate 26 owner occurrences; owner/cache distinctness uses 312 pairwise
identity comparisons total. The 30 exact instance-dictionary checks scan 256
field keys; ordered owner containers add 22 key-type checks. The six counters
require at most 312 dictionary reads across both passes. The final owner join
adds 13 identity comparisons. There are 22 bound-method captures plus one
retained builtin. These are core-loop source counts, not every interpreter,
attribute, allocation, parsing or import operation. No files, source bytes,
primitive events or numerical arrays are read/written/generated by the helper.

For the 42 original cases, a conservative constructor ceiling is 14 oracles per
case (one deliberate subclass substitution), or 588 across the suite. Core-loop
ceilings scale by at most 42; earlier rejection reduces actual work. In-memory
records and held references remain owned by the test/process. There are zero
new fixture files and zero new fixture payload bytes; logs, JUnit, collection,
source/env records and process receipts need their own finite control census.
CPU, wall time and peak memory are unknown until an admitted engineering check.

The eleven hook cases construct at most twelve oracle objects total, including
the deliberate substituted instance and the failed-constructor opportunity; only
the same-owner success case invokes the fake position callback 13 times. All other
new hook cases stop before reference work. Each uses the existing seven-file
`pins()` read, for 77 such source-file reads across these eleven cases; the one successful fake run also
uses the existing two `verify_sources` passes. Their loaded-file reads,
coefficient/plan work and retained fake-output objects belong to that explicit
producer-test scope. Existing 42-case fixture behavior and its work remain
separately counted; neither is relabeled zero-work or silently added to a
42-case original-capture control allowance.

The bootstrap/control must still supply actual protected startup/import/runtime
premises and retain this exact object graph in its child. Later S retention,
C/T joins, the real recorder/bridge installation, pass2 captures and actual routing,
A/admission, exposure evidence, full report/binder and complete resource fit remain
unfinished. No owner/primitive replacement, extra reference call, relaxed gate,
new allocation, historical-cost reset or D1 scientific run follows from this slice.
