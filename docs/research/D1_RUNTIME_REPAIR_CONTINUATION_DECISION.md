# D1 repair: proposed final software cycle and remaining delivery

**Status: proposed for approval; not approved or executable.** The original two software
cycles are consumed. The final independent failure review is complete and the narrow source
fix is independently accepted by static review. It remains unexecuted. Source and document preparation are authorized; this
document does not admit another command, CI run, installation or capture.

## Result and exact change requested

The [current result](D1_RUNTIME_REPAIR_RESULT.md#second-cycle-check-stopped-at-typing-2026-11-01)
records formatting and lint passes followed by five typing errors. Regression
tests were not dispatched. The retained B charge is **76.648979 CPU /
110.11677537020296 active-wall seconds**, including failed work and reservations;
cycle two accounts for **59.049469 / 78.45667469128966**. E2 is closed at 20 CPU / 60 wall. No passing regression result is inferred.

Approve one additional software cycle, **cycle three**, at most **200 CPU /
600 active-wall seconds**, inside the existing aggregate B **400 / 1,200**.
Also add **10 CPU / 30 wall** to E2 for the repair, control and outcome reviews.
This changes the package ceiling from **1,190 / 2,970** to **1,200 / 3,000**;
it does not add to B, reset an account, refund failed work or transfer another
partition's remaining capacity.

The complete remaining delivery path is included below. The original one PR
and one protected-main sequence, **181 configured CI job-minutes**, and all
candidate/runtime/output limits remain unchanged. There is no fourth software
cycle, automatic retry, extra CI attempt, scientific run or capacity purchase.

## Source repair and qualification gate

The failed source is `fbe9d367fba03719ea9018961eaf013831ffb436`, tree
`ace4404a5da45dedf6f6c32434502bdc50221b84`. The reported failures are a
non-overlapping comparison in `tests/d1_bootstrap.py`, three test argument-type
errors involving frozen-loader/specification objects, and one test use of a
no-return function. The original typing log is 798 bytes, SHA-256
`b56ff9aa898815e81a851acd46aa55a1bb07be063046a52ffb5e89d097fc2f34`.

The reviewed fix is [4d83811cb46892c55e772392b5b29dc7ce008b42](https://github.com/spei04/strange-physics/commit/4d83811cb46892c55e772392b5b29dc7ce008b42),
parent `fbe9d367fba03719ea9018961eaf013831ffb436`, tree
`dfa20b44235dd9f87ab6300b6f9835ef6796ac83`. Research authored it and Lead
and Quality accepted its source. Only two files changed, 14 additions and 11
deletions; imports and case counts are unchanged.

| Reviewed file | Bytes | SHA-256 |
| --- | ---: | --- |
| `tests/d1_bootstrap.py` | 27,771 | `7a8f8bd7da492dda687019d026b282a226fcad90a2b7b7de8eafa3576c877f8b` |
| `tests/test_d1_bootstrap.py` | 39,105 | `278a02841ca6d6f63a8782b67d116d43ae689cc0462e78af4dbb2e8dd76af698` |

The fix uses explicitly typed specification storage while preserving exact
`FrozenImporter` class identity. The fixtures assign that same class through
specification storage and call the `None`-returning check directly, retaining
the other assertions. No suppression, weakened guard or reduced typing scope
is introduced. **No typing or tests have run on this fix.** Its static source
acceptance does not establish software qualification.

The current seven-target census is 345 cases / 1,035 prospective phases.
Collection is source-bound and executes zero bodies. Actual final collection
and phase receipts are decisive; this number is not a test result.

## One finite third cycle

Use the existing checkout and its owned pinned environment. Preserve every
earlier start, admission, receipt, stdout, outcome, source map and failure.
The new literal namespace is `run_checks-cycle3.py`,
`contract_child-cycle3.py`, and `admission-cycle3-{format,prepare,check}.json`.
Keep the process guard and every scientific/operational denial unchanged.
The diagnosed typing repair changes only the two files pinned above; no guard
exception is included.

Four phase invocations have already been consumed. The reviewed cycle-three
runner must set **PHASE_LIMIT = 7**, permitting only attempt **5 format**,
**6 prepare/collect**, and **7 check**. Increasing the cycle number without
increasing this exact phase bound would leave the proposal unusable. No
previous filename or admission may be overwritten or replayed.

1. Seal the corrected source, literal controls, cumulative ledger and writer
   ownership. Count staging and every Git/read/write/closeout operation in this
   cycle before dispatch; unknown predecessor facts stop admission.
2. Run format/import sorting only on the four existing paths:
   `scripts/d1_capture_owner.py`, `tests/d1_bootstrap.py`,
   `tests/test_d1_capture_owner.py` and `tests/test_d1_bootstrap.py`.
   Observe and retain its exact outer exit/stdout.
3. Review and commit any formatting change, freeze the clean commit/tree and
   full source map, then admit source-bound preparation. Never treat a
   pre-commit collection as evidence for a different commit.
4. Run the existing Python/C benign sentinels and collect the exact seven
   targets without bodies. Join all earlier preparations and outcomes once.
5. Run format check, lint, full `mypy src tests examples`, and the guarded
   regression targets. Preserve original objects and all primitive, service,
   process and network restrictions.
6. Seal actual stages, phases, owned-process closure, source/environment
   parity, output census and external completion. A missing receipt, unknown
   closure, mismatched stdout or late terminal failure blocks progression.

All staging, formatting, source freeze, collection, checks and failure closeout
fit within the single 200/600 cycle and cumulative B 400/1,200. The arithmetic
remaining before new work is **323.351021 CPU / 1,089.883224629797 wall**.
After reserving the full proposed cycle, **123.351021 / 489.883224629797**
remains inside the aggregate; that arithmetic does not authorize a fourth cycle
or work outside B. A failed phase consumes the proposed cycle and stops
downstream work, with only its bounded cleanup and evidence retention allowed.

## Complete remaining path and ceilings

| Partition | Ceiling CPU / active wall | Continuation |
| --- | ---: | --- |
| A | 40 / 120 | Completed; no repeat |
| B | 400 / 1,200 aggregate | Prior charges retained; one final 200/600 cycle |
| C | 150 / 450 | One exact candidate acquisition and one new installation |
| D | 500 / 900 | One ordered runtime sequence and one capture |
| E | 110 / 330 | Original reviews plus the proposed E2 10/30 extension |
| **Whole package** | **1,200 / 3,000** | Includes old package consumption; no reset |

E2 would become **30 CPU / 90 wall**, including its original 20/60. Its proposed
increment is assigned once: repair/control review **4/12**, actual outcome and
closure review **4/12**, final handoff **2/6**. The final original E2 reader closed successfully and the full original
20/60 remains charged. E1 is retained at 10/25; E5
retains 4/10. E3/E4/E6 remain reserved for their named downstream work. Lead
completed one known successful closeout charged **3 CPU / 10 wall** within
the original E7 10/30. That receipt is retained once; **E7 has 7/20 left**
for final work and is not increased. Its 2,906-byte result has SHA-256
`b8586716e965b29570b0386e996cd0e09a3c825ca1578a4dee3d24a02fc463ff`. Unused or unmeasured amounts in one review partition do
not silently fund another.

After independent B acceptance, Lead freezes the source and creates **one
original PR CI run**: two Checks jobs at 20 minutes, two analytic jobs at
15 minutes, security at 10 minutes and gate at 3 minutes, totaling **83
configured job-minutes**. Preserve actual head/base/tested merge/tree, all
complete raw logs and the two bounded analytic artifacts. E3 remains 15/45
and PR evidence 12 MiB. Source/evidence preparation, cloud receipt writes,
inspection and final review count inside that allowance.

Only successful original PR checks and source review permit normal protected
main integration. The **one original main run** adds the 15-minute candidate
job, totaling **98 configured job-minutes**. E4 remains 15/45 and main evidence
12 MiB. No conflict repair, source churn, rerun, manual dispatch or second main
candidate is included. Such a need stops this continuation.

C then receives the exact same-run five-file candidate: wheel, sdist,
provenance, checksums and retained runtime requirements. Authenticate the
artifact/run/main joins; keep the reported GitHub digest distinct from observed
download hashes. Stream bytes to cloud storage without a Mac artifact file.
Do not regenerate requirements with the different cloud uv version. Use one
new owned genuine uv installation, the verified regular interpreter copy,
preserved sibling links and the pinned runtime-only dependencies. Keep the
old accepted installation and failed capture evidence unchanged.

D retains these stage limits and order:

| Stage | CPU / active wall |
| --- | ---: |
| Native inventory and closure | 100 / 150 |
| Existing installation/plan record materialization | 25 / 60 |
| Actual-candidate startup-only diagnostic | 20 / 45 |
| Three fixed benign guard probes | 15 / 45 |
| Leader-exit/live-descendant witness | 80 / 90 |
| One capture and closeout | 200 / 330 |
| **Six stages** | **440 / 720** |
| Failure cleanup/retention only | 60 / 180 |

The capture keeps its full **300-second outer profile**, 150 CPU service hold
and existing service/quota settings. Do not shorten it to fit. Each stage
requires known predecessor closure, exact candidate/runtime/custody identities,
remaining CPU/wall and complete future output reservations. The startup result
must match the evidence-backed two-alias mapping; a mismatch stops the path.
The C probe is benign builtin `len`, not a real `math.exp` probe. Failure
preserves its original outcome and reservations; no second capture is included.

## Storage, measurements and stop rules

The unchanged **1 GiB** limit counts all new copies and partials: installation
512 MiB, temporary work 128 MiB, candidate representations 48 MiB, source/control
copies 32 MiB, evidence 96 MiB and failure retention 208 MiB. Evidence remains software 32, PR 12, main 12, runtime 32 and review 8 MiB.
The following complete cycle-three write reservation includes the retained
software files and every proposed output class. These are hard retained-output
ceilings to be sealed in the controls, not measured future usage.

| Software output class | Multiplicity and cap | Reserved bytes |
| --- | --- | ---: |
| Already retained software | Existing complete census | 721,512 |
| Fixture payloads and names | 8 MiB; covers unchanged 8,024,322-byte two-suite bound | 8,388,608 |
| Command logs | Exactly 9 logs × 256 KiB | 2,359,296 |
| Sentinel tripwire/continued leaves | At most 4 × 4 KiB | 16,384 |
| Collection manifest | 1 × 1 MiB | 1,048,576 |
| Collection receipt | 1 × 1 MiB | 1,048,576 |
| Test receipt | 1 × 1 MiB | 1,048,576 |
| JUnit, including failed partial | 2 MiB aggregate | 2,097,152 |
| Phase parent receipts | 3 × 2 MiB | 6,291,456 |
| Preparation receipts | 3 × 512 KiB | 1,572,864 |
| Other fixed metadata | Detailed inventory below; 2 MiB aggregate | 2,097,152 |
| Source maps | Exactly 4 × 64 KiB | 262,144 |
| New deployed software helper copies | 128 KiB aggregate | 131,072 |
| Framework, failure and closeout outputs | 2 MiB aggregate, including partials | 2,097,152 |
| **Complete upper bound** | | **29,180,520** |
| **Unallocated space within 32 MiB** | 33,554,432 − 29,180,520 | **4,373,912** |

The nine command logs belong to the existing two format stages, three
preparation stages and four check stages. The proposed narrow control change
caps each at **256 KiB**. Overflow fails the phase, preserves all bytes already
written, closes the owned process and stops downstream dispatch. It never
produces a truncated passing result, reduces the typing/test scope or weakens
a scientific denial. All report and receipt bounds remain explicit; a bound
failure cannot be hidden by omitting an output from the census.

Other metadata has this complete **34-leaf** inventory:

| Fixed metadata class | Multiplicity and cap | Maximum bytes |
| --- | --- | ---: |
| New phase admissions, retained admission snapshots, phase starts, preparation starts, phase stdout and outcomes, failed-attempt-four stdout/outcome, restart record | 21 × 64 KiB | 1,376,256 |
| Preparation inputs | 3 × 128 KiB | 393,216 |
| Optional failure/uncertainty latches | At most 6 × 8 KiB | 49,152 |
| Optional preparation stdout records | At most 3 × 64 KiB | 196,608 |
| Index/final closeout record | 1 × 64 KiB | 65,536 |
| **Metadata maximum** | **34 leaves** | **2,080,768** |
| **Headroom in the reserved metadata row** | | **16,384** |

The 21 records are three each of phase admissions, admission snapshots, phase
starts, preparation starts, phase stdout records and outcomes, plus the two
failed-attempt-four records and one restart record. Inputs, latches and the
index are separately capped as shown. Optional records reserve failure bytes;
they do not authorize another attempt, stage or retry. The reviewed seal must
enumerate the exact filenames and schemas for these 34 leaves before execution.
No other metadata writer is allowed. Earlier outcomes one through three are
already retained and are referenced without making new copies.

The source-map writer uses the existing sealed **437 keys** and 64-character
SHA-256 values. The two-file fix changes neither keys nor schema; canonical
map output remains **46,768 bytes**. Enforce the proposed 64 KiB limit before
writing. The four copies are the new initial map and the map after format,
prepare and check. Source freeze reuses the after-format reference; it does not
write a fifth map. The two versioned runner/collector helpers currently total
60,215 bytes within the 128 KiB aggregate; the guard is reused. Any additional
copy in the software root must fit that same helper aggregate. Source-authoring
drafts and controllers retained separately belong to the existing source/control
pool and global 1 GiB bound, not an uncounted exemption.

Research confirmed that the unchanged two-suite fixture bound conservatively
covers the single proposed suite; no new fixture payload or case is introduced.
The table counts hard-link names and retained special-file names without
following links. Every partial file remains in its class, and nested data in a
receipt is charged as part of that file rather than counted again as a fictional
standalone copy.

Before each stage, all actual retained software bytes plus that stage's complete
worst-case writes and closeout reservation must fit 32 MiB and its applicable
sub-bounds. Earlier maxima cannot be treated as permission to consume an unused
slot twice. File writes check their bounds before writing, and the no-follow
census verifies all owned names and bytes. These are control and acceptance
bounds, not a universal filesystem quota or proof of every transient peak.
Failure preserves the partials and reservations. No pool increase or deletion
of retained failures is proposed.

Fresh storage and custody checks precede actual admission. The final closeout
observed **43,511,271,424 free bytes** and a conservative combined retained-data
upper bound of **66,300,369 bytes** including its result reservation. The latter
includes old and new private records; it is neither new growth nor an allocation
of the entire historical evidence directory to this package. No data was
deleted and the old installation was not reread. The old installation and
archives remain retained separately. The scientific 50 GiB start / 45 GiB
later guards remain unchanged, and the separate disk-capacity proposal is not
approved by this decision.

CPU charges, active-wall charges, measured lower bounds, conservative holds,
configured hosted job-minutes and provider dollars are distinct. Cloud evidence
reads/writes and inspections join E; external source authoring, inference and
Mac/SSH/GitHub control costs remain separately unmeasured rather than zero.
Known totals do not establish a kernel-wide or whole-operation CPU bound.

Missing identities, incomplete evidence, unsafe diagnostics, an exceeded
phase/cycle/output limit, failed CI, changed candidate content or unknown
ownership stop the dependent path. Preserve the consumed attempts and full
required holds; no inferred refund, manual bypass or automatic retry follows.

## Owners and approval handoff

- **Research:** exact source fix, source/fixture census and reviewed cycle-three
  source-freeze/collection joins.
- **Quality:** independent source, control, typing/test outcome and closure review.
- **Platform:** coherent decision/ledger, fixed hosted evidence controls and
  exact source/candidate delivery joins.
- **Lead:** one complete approval handoff, sealed admissions, sole execution,
  integration, custody and final publication.

The reviewed fix and unchanged fixture bound are pinned above. Before each
admission, verify the complete cumulative output reservation and predecessor
receipts. This decision specifies the finite control changes and remaining
delivery recipes; every future executable
controller need not be implemented before the owner reviews the package. After
approval, Lead seals and obtains independent acceptance of the exact controls,
commands and dependent identities before each stage. Actual run/artifact/runtime
identities come only from successful predecessors. A placeholder never permits
execution. The proposed amendment remains unexecuted.
