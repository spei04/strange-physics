# D1 startup and owner repair: one complete execution proposal

**Status: unexecuted proposal; no new allocation approved.** Source drafting,
static review and preparation of this whole plan are already authorized.
Tests, diagnostic commands, hosted CI, installation and actual runtime work
remain unrun. This document requests one finite package covering the complete
path below, with conditional transitions and bounded failure closeout.

## Decision and retained starting point

Approve a new local command envelope of **1,190 CPU seconds / 2,970
active-wall seconds**, plus **one original PR CI run and one original
protected-main run: 181 configured job-minutes**, and at most **1 GiB of new
retained output**. These are separate measures, not one elapsed-time or
provider-dollar budget. No new capacity, provider purchase, public release,
deployment, secrets transfer or D1 scientific run is authorized.

The [previous result](D1_RUNTIME_QUALIFICATION_RESULT.md) remains incomplete.
At exact main `5e0b3e7db436061f4d7c9a5e983f7878cea31974`, three continuation
checks passed but capture failed before its report on an unlisted frozen
module. The offending name is unknown. Owner reconciliation also failed after
the service was cleared. Original unknown usage/closure, the full 150 CPU
service hold, all failed attempts and approximately 93.6 MB of prior retained
data remain unchanged.

Closed Unit22's 200/600 software account is not a fresh test allowance.
The previous four-stage continuation is consumed, and neither its arithmetic
remainder nor the old review account supplies retry authority. This proposal
creates no refund, reset or transfer from any old account.

## Source scope and conditional policy change

The independently reviewed, unexecuted source draft is
[ed3053a7137949c6a6adb2619291687325f783f0](https://github.com/spei04/strange-physics/commit/ed3053a7137949c6a6adb2619291687325f783f0),
tree `95019ca816595b367950dc1f9cd84fd837c3eed5`, based on exact main
`5e0b3e7`. Its retained diff SHA-256 is
`c1b71f9106a61ab68e8a8cf553d36f69875e55c35245fe58b4bc5b1405aa1fd1`.
It adds bounded rejection diagnostics and repairs owner reconciliation.
It currently allows **no new frozen-module alias**.

| Changed source | Bytes | SHA-256 |
| --- | ---: | --- |
| `scripts/d1_capture_owner.py` | 21,796 | `f16578450dc41299c8367c61a338597e8ac1b758ac6aeef1510655c15b105cf9` |
| `tests/d1_bootstrap.py` | 26,146 | `a26baa7eeecdced10e18dd80c0ef667dd3cdadce2cbd9338d849b60c7ebed977` |
| `tests/test_d1_capture_owner.py` | 21,125 | `edcdeda4adae7bff602227328d5415bb6f70526e3daf9460d6ca3e27dc2beded` |
| `tests/test_d1_bootstrap.py` | 36,460 | `c452e16db6a9ca7b93246bd0d85f178ebeb1c2648f8092f1e3ab082894e98b23` |

Stage A must first supply actual evidence. The only conditional policy change
within this package is either or both of these exact relations:

| Alias key | Required canonical module |
| --- | --- |
| `importlib._bootstrap` | `_frozen_importlib` |
| `importlib._bootstrap_external` | `_frozen_importlib_external` |

An alias can be admitted only if actual module identity, canonical name,
specification, frozen origin and exact ordinary frozen-loader identity agree,
and the pinned protected standard-library source proves the relation.
The canonical frozen name must already be accepted by the protected inventory.
Require the same module object at both keys; a matching string is insufficient.
Reject impostors, altered specifications/loaders, extra aliases and missing
custody. Do not infer either alias from the old error or permit all modules
with a frozen origin.

If A reveals a different, unsafe, unbounded or unreproduced condition, **stop**.
No broader allowlist, second diagnostic, new project-function scope or new test
target is included. Any permitted alias repair receives source review before
the final freeze, with at most 16 additional regression cases in the existing
targets. The owner repair must preserve failure while reconciling verified
retained terminal identity; controller closure alone cannot manufacture a
successful capture or erase missing evidence.

## Complete local allocation

All ceilings below include their own preparation, receipts and closeout.
Every invocation, failure and retained reservation counts once in its named
partition. They are prospective limits, not measurements.

| Partition | CPU seconds | Active-wall seconds | Bound |
| --- | ---: | ---: | --- |
| A: initial startup-only diagnosis | 40 | 120 | One invocation against the existing accepted installation/source |
| B: software qualification | 400 | 1,200 | At most two reviewed cycles, each at most 200/600 |
| C: candidate acquisition and setup | 150 | 450 | One exact five-file candidate and one new owned installation |
| D: actual runtime qualification | 500 | 900 | One ordered sequence; one capture |
| E: all named reviews and final closeout | 100 | 300 | Includes admission/setup peer reads and final publication records |
| **Total local command ceiling** | **1,190** | **2,970** | No old balance transfer |

D is partitioned as follows. The last reserve is for failure cleanup and
retention only, not another stage attempt or an extension of a service deadline.

| D stage | CPU seconds | Active-wall seconds |
| --- | ---: | ---: |
| Native inventory and closure | 100 | 150 |
| Installation/plan materialization | 25 | 60 |
| Actual-candidate startup-only diagnostic | 20 | 45 |
| Three benign guard probes | 15 | 45 |
| Live-descendant witness | 80 | 90 |
| Capture and its closeout | 200 | 330 |
| **Six-stage subtotal** | **440** | **720** |
| Additional failure cleanup/retention reserve | 60 | 180 |
| **D total** | **500** | **900** |

The fixed capture profile retains its original **300-second outer invocation**
and 150 CPU service reservation. Full required time/reserves must be available
before dispatch; do not shorten the profile to force a fit. Stage closeout
already counted in the subtotal is not added again to the 60/180 reserve.
Named-service CPU and overlapping parent/waited-child scopes remain distinct.

E is one shared review ledger with the following named ceilings. Owner
assignment and every read/seal are recorded before work; a second reviewer
does not silently create a second full allowance.

| E review scope | CPU seconds | Active-wall seconds |
| --- | ---: | ---: |
| A operator, custody and diagnostic admission/outcome | 10 | 30 |
| B source, both cycles and software results | 20 | 60 |
| PR CI identity, complete logs and evidence | 15 | 45 |
| Protected-main candidate identity and CI evidence | 15 | 45 |
| Acquisition/setup/native admission and outcome | 15 | 45 |
| Remaining actual stages, failures and outcome reviews | 15 | 45 |
| Final reconciliation and publication records | 10 | 30 |
| **E total** | **100** | **300** |

Runtime cleanup belongs to D; peer evidence review/publication belongs to E.
No observation is counted in both. Retain measured values, unknown values and
conservative reservations separately. These command accounts do not prove a
kernel-wide or whole-operation CPU bound. Planning, external authoring,
SSH/GitHub administration and provider dollars remain separately unmeasured;
they are not zero. Unlike the prior ledger's missing peer-read coverage,
all new named admission/setup reviewer work must join E.

## Ordered command/control recipe and exit gates

### A — Observe the actual startup boundary once

Before launch, seal the fixed diagnostic, parent checks, exact argv/environment,
source/runtime pins, native/custody preflight, owned fresh cache/output paths,
process guard and admission. Use the existing accepted installation and source
only as read inputs; do not alter them or their old evidence.

The unexecuted diagnostic draft is `startup-frozen-diagnostic-repair-draft.py`,
10,780 bytes, SHA-256
`77b610f8e2739ccf802ab1d59a67ed513e920e94c0f373328394b591bfc6e353`.
Independent static source review found no blocker. This script is not authority: the
parent preflight, aggregate bounds and admission still require sealing before
launch.

Its fixed child command shape is
`K -I -B -X pycache_prefix=R/startup-diagnostic-cache R/controls/startup-frozen-diagnostic.py`,
with no script arguments. Here `K` is the existing accepted installation's
owned interpreter; `R` is the new owned repair root, presently nonexistent.
The private appendix binds their exact paths. The parent copies the pinned
script and exclusively creates an empty mode-0700 cache; it rechecks the old
source, interpreter, native/startup inventory, custody and protected plan before
launch, then verifies owned process/EOF closure and postconditions.

The child follows the exact original eleven standard-library imports plus the
future import and takes its snapshot immediately, without executing the
original initial validator. It imports no project/source modules. Its four
fixed pin reads total 8,663,866 bytes, with at most 139 data/EOF read calls.
The registry is bounded to 512 entries and frozen entries to 64; JSON output
is at most 64 KiB. Exceeding a bound fails rather than truncating. Only the two
named conditional aliases are eligible; another unknown condition stops with
exit 2. These are child bounds; parent preflight and closeout reads must also
appear in the sealed census and fit A's 40/120 envelope.

The parent and child must not import project/source or D1 modules, call D1
primitives, create a service or invoke capture. Use the fixed reviewed
standard-library import sequence under the same interpreter, isolation flags,
site policy and startup conditions. This observes the top-level import boundary;
it does not execute the initial child validators or claim to reproduce every
registry mutation before the original first loaded-module check. A generic inventory from another
interpreter is insufficient. The sealed controller uses the reviewed ordinary
no-site preparation route; the target's normal-site behavior is observed,
not replaced with `-S` to conceal a hook.

Collect bounded module keys and direct specification/loader/identity facts,
plus protected source joins. Do not print environment values or arbitrary
object representations. Require known owned-child closure and unchanged
custody. If the no-project diagnostic cannot reproduce the relevant startup
boundary, fail closed. An empty unlisted-key set also stops this path, even
though the diagnostic script itself exits zero in that case. A successful
metadata observation is evidence for the conditional mapping above, not protected
capture qualification and not proof of the historical unrecorded name.

**Gate:** Research identifies the exact permitted relation from actual A
evidence; Quality accepts the source proof and bounded repair. Otherwise stop
before software qualification or CI.

### B — Freeze and qualify the repaired source

Reuse the existing source checkouts and pinned environment without dependency
changes. One cycle contains formatting/import sorting of the fixed paths,
reviewed commit/freeze, source-bound guarded collection, benign tripwire
sentinels, lint, full `mypy src tests examples`, the seven guarded targets,
final source/environment/output census and closeout. A formatter-created
source change must be committed and recollected before test execution.

Use the existing reviewed process guard and defining-code/C-event denials;
do not replace original objects to make identity tests pass. Benign sentinels
must not invoke a scientific primitive. Owned fixture I/O and helper-local
fault mocks stay within the frozen test contract. No actual service, capture,
scientific runner or provider call is allowed in this software stage.

| Guarded target | Reviewed draft cases |
| --- | ---: |
| `tests/test_d1_originals.py` | 42 |
| `tests/test_d1_bootstrap_control.py` | 62 |
| `tests/test_d1_bootstrap.py` | 95 |
| `tests/test_d1_owned_capture.py` | 41 |
| `tests/test_d1_capture_owner.py` | 44 |
| `tests/test_d1_capture_descendant.py` | 19 |
| `tests/test_d1_runtime_inventory.py` | 26 |
| **Draft total** | **329 cases / 987 prospective phases** |
| **Maximum after permitted alias regressions** | **345 / 1,035** |

The prior baseline was 302/906. Static case arithmetic is not a passing result.
Freeze exact ordered node IDs before bodies; collection has zero test phases.
Full typing discovery and actual phase receipts are decisive. The second
cycle may repair only defects within this reviewed source/target scope, after
manual source review; it is not an automatic rerun. Both cycles and all failed
commands remain within B, with no third cycle, reduced typing scope or weakened
assertions. Freeze exact final source/tree, per-file bytes, dependency lock,
environment and control identities after successful qualification.

**Gate:** exact passing source, complete owned-process closure, unchanged
dependencies and independent acceptance before PR creation. Failure to finish
within the two-cycle limit stops this package.

### Hosted delivery — one PR run, then one protected-main run

Create one PR from the frozen source. The unchanged workflow runs two
20-minute Checks jobs, two 15-minute analytic jobs, a 10-minute security job
and a 3-minute gate: **83 configured job-minutes**. Candidate is skipped on PR.
Retain actual tested head/base/merge tree, original attempt and complete logs.

After required checks and source review pass, perform normal protected-main
integration without changing the qualified content. The original main run
adds the 15-minute candidate job: **98 configured job-minutes**, or **181**
combined. These are job time limits, not CPU, pipeline elapsed time or prices.
No workflow dispatch, rerun, head churn, extra PR run or second main candidate
cycle is included. A base/content conflict or need for another CI cycle stops
this package for a revised plan.

Existing analytic reference cases and fixed 8/8 CLI smokes remain included.
Ordinary CI therefore includes its historical numerical tests; it does not run
the D1 scientific study or reproduce the private guard's complete event census.
Both actual counts and warnings must come from original logs.

**Gate:** all required original PR jobs and all seven original protected-main
jobs succeed, with the exact resulting main source/tree and candidate joined.
Later docs are not relabelled as the candidate.

### C — Acquire and install that exact candidate once

Stream authenticated artifact bytes directly to private cloud storage; no Mac
artifact file. Retain reported GitHub digest separately from observed download
and cloud hashes. Bind run/attempt, artifact ID, exact main/source export, lock
and all five files: wheel, sdist, provenance, checksums and runtime requirements.

Verify the retained requirements bytes against provenance. Do not regenerate
the export with the different cloud uv version. Use the pinned installation
route and one new owned environment: genuine uv metadata, verified regular
interpreter copy before consumers, preserved sibling links, runtime-only locked
dependencies and the verified wheel. Retain every source/archive/installation
join, metadata probe, process receipt and failure. Do not reuse or overwrite
the prior accepted installation, whose capture failed, as a newly accepted
candidate for changed source.

**Gate:** exact-source installation and custody accepted, complete setup child
closure and enough remaining runtime/output capacity before D.

### D — Qualify the actual candidate once

Run the six ordered stages in the D table. Native closure includes exact
loadable/nonloadable classification and pinned deferred/startup membership;
nonloadable build objects remain in the hashed inventory. Materialization
constructs existing record formats and cannot confer authority on itself.

The actual-candidate startup diagnostic uses the same fixed recipe and
evidence-backed mapping accepted after A. Fresh installation paths and byte
pins must join this candidate; no unexpected module or alias is accepted by
updating expectations on the fly. A mismatch means **stop**, without a second
diagnostic, policy bypass or another CI cycle.

Then run the three fixed benign probes, the explicit leader-exit/live-descendant
handshake, and one capture. The C probe remains builtin `len`, not an actual
`math.exp` call. Original-owner anchors, terminal invocation/group identity,
quota/burst evidence and the fixed capture deadline must remain connected.
Reconcile failed controller evidence before destructive cleanup removes the
only identity observations; a failed capture remains failed even if closed.

**Gate after each stage:** preceding receipt, exact source/runtime identity,
CPU/wall/output and future reservations, known closure and independent review.
A failure stops downstream dispatch; only its named bounded cleanup/retention
may proceed. Keep unknown usage and full reservations where reconciliation
fails. No second capture is included, and successful setup/probes cannot stand
in for capture acceptance.

## Output and storage bounds

All new copies, partials and metadata across the new private evidence/runtime
roots count toward one **1,024 MiB** retained-output ceiling.

| Pool | MiB |
| --- | ---: |
| Installed environment | 512 |
| Temporary caches and working files | 128 |
| Candidate ZIP, extracted bundle and validator pair | 48 |
| Source exports and control copies | 32 |
| Evidence | 96 |
| Failure retention reserve | 208 |
| **Total** | **1,024** |

Evidence's 96 MiB is subdivided into software 32, PR CI 12, main CI 12, actual
runtime 32 and reviews/closure 8. Candidate's three representations each have a
16 MiB maximum. Count raw job logs, original analytic ZIPs, fixtures, source
snapshots, admissions, starts, receipts, sibling control directories and failed
outputs. Reuse content-addressed source maps; do not retain a full source export
for every software cycle. Fixed per-file, entry-count, read and descriptor bounds belong in the
sealed appendix; no unrestricted archive extraction or output writer is allowed.

A census records every owned name without following symlinks; hard-link names,
directories, FIFOs and symlinks must not disappear from the entry inventory.
Retained-byte accounting is not a universal transient-peak filesystem quota.
Reserve remaining worst-case output before the next stage and stop if it
cannot fit. No cleanup deletes original failure or required release evidence.

The latest capacity observation is **43,654,914,048 free bytes**, a preparation
fact requiring a fresh admission-time check. The older approximately 93.6 MB
is retained separately; both old data and the full proposed new footprint must
fit the applicable engineering storage guard. The scientific 50 GiB start /
45 GiB later reserve remains unsatisfied and unwaived. This bounded engineering
proposal does not change it.

## Freeze, ownership and approval handoff

The private controls recipe is sealed for review at 12,594 bytes,
SHA-256 `877b279e23221a9a562e901ac6567352eae4b4bfc76c761e83261ba2129ce504`. It records the exact diagnostic
argv and paths, eleven existing control-donor hashes, owners, all A–E and CI
limits, required command shapes, evidence pools, closure sequence and finite
rules for filling dependent identities. It is a review recipe, not an executable
admission. The prior source and runtime controls are read-only donors; their old
allocations and approval records cannot be executed again.

Before each dependent launch, Lead materializes and independently seals its
actual commands/argv, allowlisted environment, source/runtime maps, admission,
controller/guard hashes, complete process/read/output bounds, writers and
closure sequence. Only the approved new paths, limits, actual predecessor
identities, exact test census and evidence-backed two-alias repair may change.
A's parent preflight and full read census must fit A's own allocation; the
diagnostic's four input reads are not a bound on its parent's work. Future
source, CI, artifact and installation identities are necessarily bound after
their successful predecessors. No missing pin, placeholder command, unreviewed
helper or broader behavior may become an executable admission.

A's exact diagnostic and existing-input pins are frozen first. The conditional
alias rule and maximum test scope are proposed for prospective approval; the actual
evidence-backed edit and final B source are then frozen before their commands.
PR/main identities and installation records are bound to their actual successful
predecessors, never fabricated in advance. Controls must not embed a digest
cycle in their own source; external immutable approval/provenance binds them.

- **Research:** source repair, exact startup/source proof and bounded regressions.
- **Quality:** independent controls, policy, stage evidence and failure review.
- **Platform:** delivery identity, original CI evidence and ledger consistency.
- **Lead:** one approval handoff, admissions, sole actual executor, custody and
  final reconciliation/publication.

Research authored the source and diagnostic; Quality independently reviewed
both and the full plan. Platform checked the dependency order and arithmetic.
These are static preparation results; no new tests or runtime have run.

No execution is currently approved by this draft. One direct approval would
authorize only this finite package and its explicit conditional edits.
Any out-of-scope diagnosis, exceeded cycle/stage limit, unknown ownership,
changed source, missing identity or inability to retain required evidence
stops the dependent path. Closeout records distinguish pass, fail, unknown and
unrun work; no silent exclusion, automatic retry or inferred leftover balance.

Final delivery requires independent review of the exact source/candidate,
every consumed attempt, output census and separate known/unknown cost scopes.
A successful capture would qualify that bounded path only. Scientific exposure,
numerical adequacy, evaluation independence, recovery/generalization and
enterprise readiness remain separate gates.
