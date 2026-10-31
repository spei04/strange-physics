# D1 runtime continuation decision

Status: **approved continuation attempted; capture failed; runtime not qualified**. Materialization, three guard probes and the descendant witness passed. Capture failed before capture JSON with an unlisted frozen module; its name is unknown. The runtime account retains **219.91242 CPU / 113.7971664420329 active-wall seconds**, including the unreconciled 150 CPU service hold, within the approved 400/600 allocation. No retry or new service is admitted.

## Original request — approved on 2026-10-31

Approve **400 CPU / 600 active-wall seconds** for the existing runtime qualification account: an increase of **200 CPU seconds only**. Keep all previous charges and failed attempts. This is a finite continuation of the engineering checks, with one attempt per remaining stage. It does not authorize a scientific run, new infrastructure, deployment, release or additional provider spending.

The approved total four-part local command allocation changes from 600 CPU / 1,800 active-wall seconds to **800 CPU / 1,800 active-wall seconds**. Source qualification stays 200/600, acquisition/setup stays 150/450, and review/closure stays 50/150. Closed balances cannot transfer into this account.

## Verified starting point

The exact source is [5e0b3e7db436061f4d7c9a5e983f7878cea31974](https://github.com/spei04/strange-physics/commit/5e0b3e7db436061f4d7c9a5e983f7878cea31974). [Main CI run 41230418150, attempt 1](https://github.com/spei04/strange-physics/actions/runs/41230418150) passed all seven jobs, including the unpublished candidate build and installed-wheel smoke. The candidate archive, five retained inputs and actual private installation were verified. This proposal does not relabel a later documentation commit as that candidate.

Setup completed with five closed subprocesses. The earlier startup-cache rejection remains retained; its exact root-owned bytecode was checked against the pinned source without executing it. A single installer-created empty lockfile was changed from mode 0666 to 0600 with its identity preserved. The final setup account is **22.297874 CPU / 43.566476 active-wall seconds**, separate from the runtime account.

Native attempt 3 passed: **115 loadable ELF files, 234 dependency edges and 116 closed subprocesses**. Attempts 1 and 2 remain failed and charged; all 147 subprocesses across the three attempts have closed. The runtime account retains **48.88882 CPU / 66.534427 active-wall seconds**. Its native closure and process accounting received independent reviews.

The two failures identified a duplicate ELF-version label and a compiler object that is not a loadable library. Narrow parser/classification repairs were checked against retained output and negative fixtures. The compiler object remains in the full hashed inventory; it was not silently removed from custody checks.

## Why the original allowance was insufficient

At the original 200/600 limit, the account had 151.11118 CPU seconds left. The fixed capture requires its **150 CPU-second service reservation plus 10 CPU seconds of headroom**, before the preceding stages or their closeout. It could not be admitted within that cap. No materialization, guard probe, live-descendant witness or capture was launched before the direct continuation approval.

A previous 300/900 draft was neither admitted nor executed. It was superseded by this explicit request and did not change authorization. Only the later direct owner answer approved the 400/600 continuation.

## Approved continuation allocation

| Ordered stage | CPU seconds | Active-wall seconds | Included work |
| --- | ---: | ---: | --- |
| Materialize | 25 | 60 | Recheck actual inventory and create the installation record and protected capture plan. |
| Guard probes | 15 | 45 | Three separately reaped benign callbacks using retained Python code, a source route and C builtin `len`. |
| Descendant witness | 80 | 90 | Fixed leader-exit/live-descendant handshake; 35 service + 30 outer command + 15 other CPU seconds. |
| Capture only | 200 | 330 | Sole fixed independent-owner invocation; 150 service + 30 outer command + 20 other CPU seconds. |
| **Remaining maximum allocations** | **320** | **525** | Each stage includes its 2 CPU / 5 wall closeout reserve. |
| **Previously retained charge** | **48.88882** | **66.534427** | Both failed native attempts and successful attempt 3. |
| **Prospective total** | **368.88882** | **591.534427** | Within approved 400/600, conditional on live admission checks. |

The original maximum-allocation arithmetic leaves 31.11118 CPU and approximately 8.465573 wall seconds below the approved aggregate ceilings. This is not a promise that every stage will fit: stage and aggregate checks must preserve future reservations. Capture must have its full 300-second outer invocation available after prechecks or refuse dispatch. The plan does not shorten the capture profile to manufacture a fit.

The fixed service limits, per-child CPU ceilings, output bounds, source identities, prior receipts and failure handling remain in force. Uncertain closure retains its reservation and prevents advancement. Any stage failure stops this sequence after closure and accounting; another attempt requires a revised concrete plan.

## Review and execution boundary

The exact continuation operator passed static construction checks and independent source/plan review. It rejects a new native attempt, binds the four stage allocations, and preserves the earlier native charges exactly once. The direct owner answer approved this exact reviewed continuation. The active operator is bound to that approval; the earlier native3 operator and receipts remain preserved. A hash-bound record records the answer and cannot supply authority on its own.

| Private retained artifact | SHA-256 |
| --- | --- |
| Complete continuation proposal | `32c3e66359f64e08cd7b375f0d980184492122c06e65417968404831a68e754a` |
| Approved continuation operator | `aa1d3916598c3ada568a5004939600d14b80b7ab1a304d75b6cf1db2d4b6da0e` |
| Author static-check receipt | `f6704d8778a69072bfd117ea2a8f99048cb62b3312b00de742859ca871e96d86` |
| Independent source/plan review | `9f74e44b6853eea6d7c35dc9560912622cafa70403a65d96815e2b5ceb4fc419` |
| Direct-answer approval record | `1819fd874c135c032ad01bcdaa5097a5841ae4a80090b5b2859684b6a42edd16` |
| Successful native attempt 3 receipt | `df820792dad7d964f7894d2e41ffbcfc5ae0c8b0924a6c0529d43e6b319742ec` |
| Actual native closure | `ea85c3347f1ab25658032ac2a4994678130fbcd34dd8d43f987461546865c483` |

Static review is not execution evidence. Each engineer's final proposal review retains its full 5 CPU / 15 wall hold in the unchanged review partition. The author's earlier failed validation assertion is retained within that same author hold. No remaining runtime stage or new CI run was needed to prepare this decision.

The original materialize admission was prepared under 200/600 but never executed and remains an unused pre-approval record. The single materialization attempt passed under the approved 25 CPU / 60 wall stage ceiling and was independently accepted before probes. The subsequent probe and benign stages passed; capture failed as recorded below. Each later admission must bind the actual preceding successful receipt. No stage may run on a placeholder or stale artifact identity.

These are prospective command allocations and observed accounting scopes, not a hard kernel-wide aggregate CPU guarantee. Named-service CPU is separate from parent/waited-child CPU; overlapping inner scopes are not added twice. Authoring, SSH/GitHub administration, whole-operation CPU and provider dollars remain unmeasured. Storage checks are observed inventories and per-file bounds, not a universal transient-peak quota.

Static native closure does not prove that every future API or opaque dynamic load is covered. This path checks the pinned installation and capture-only invocation. NumPy startup may perform its ordinary sanity arithmetic; the guard forbids D1 scientific primitive execution. Original provisional `accepted=false` records remain unchanged; any external qualification must be a separate evidence-backed record.

The scientific batch, disjoint evaluation inventory, numerical adequacy and recovery/generalization claims remain separate gates. The scientific disk reserve is unwaived. Passing this continuation would establish the bounded capture path, not production readiness or a research result.

## Team and progress

- Lead: evidence custody, approved allocation enforcement and sole executor.
- Quality engineer: actual closure/accounting and stage-limit review.
- Research engineer: independent actual source/guard and evidence review.
- Platform engineer: consistent roadmap, backlog and assignment updates.

Private evidence stays in the existing protected cloud record. Review date: 2026-11-30. Both current checkouts are retained for reuse; no new worktree or local project copy is needed.

## Approval checkpoint

The original request and independent review remain available at
[documentation commit f54a7d6](https://github.com/spei04/strange-physics/blob/f54a7d609ec77e75771b653aed158275dd8271f9/docs/research/D1_RUNTIME_CONTINUATION_DECISION.md).
The direct answer was recorded at 2026-10-31T19:39:28.354764+00:00; its retained
1,477-byte approval record binds the proposal, operator, independent review,
prior native charges and exact candidate source. This documentation update
does not replace main 5e0b3e7 as the candidate identity. The finite sequence subsequently reached capture and failed; no protected-runtime
acceptance or retry is implied.

## Actual materialization outcome

The single attempt passed, producing the installation record (161,081 bytes,
SHA-256 `65ead13d4d7b8bc6d7f11b090e63820e61db34bc4b11f1401beec633a2a1b8d5`)
and protected plan (612,843 bytes, SHA-256
`18925a4e08ade05a73978813a2e8ed1035982b627df0f549e7f77abca8558d3c`).
There were no children/services or cleanup failures. Stage charges are
7.609223 CPU / 10.553777021821588 active-wall seconds; cumulative runtime
charges, including every native attempt, are 56.498043 CPU /
77.08820401737466 wall seconds.

Materialization was independently accepted before probes. Record construction
is not itself protected-runtime acceptance; subsequent outcomes are recorded below.

## Actual continuation outcome

| Stage | Result | Charged CPU seconds | Charged active-wall seconds |
| --- | --- | ---: | ---: |
| Native attempts 1–3, retained | Third passed; first two failures retained | 48.88882 | 66.53442699555308 |
| Materialization | Passed; no children/services or cleanup failures | 7.609223 | 10.553777021821588 |
| Three guard probes | Passed; three exit-86 children closed/reaped, clean EOF | 4.101099 | 7.201204144861549 |
| Benign descendant witness | Passed; acknowledged release, cgroup closure/cleanup confirmed | 5.011944 | 10.037434913683683 |
| Capture | Failed; original closure/usage uncertainty retained | 154.301334 | 19.470323366113007 |
| **Cumulative runtime account** | **Runtime not qualified** | **219.91242** | **113.7971664420329** |

Each probe recorded one expected denial without executing or returning from its
benign body. The C probe used builtin `len` through the retained-C event branch
labelled `math.exp`; it did not invoke actual `math.exp`.
Probe receipt SHA-256:
`2e660dac7d49fec4b7a891cb0c24e53fdac5f56da6c3afb405b514ca135acfd6`.

The benign witness observed a populated cgroup after leader exit, received the
release acknowledgement, and confirmed terminal closure and cleanup. Both
outer commands closed at exit 0. Its original `accepted=false` remains unchanged.
The 5.011944 CPU charge includes 0.185838 service CPU, 2.826106
parent/waited-child CPU and a 2 CPU closeout reserve, each counted once.
Benign receipt SHA-256:
`50b2aa570465882342142f2ba51b27ca29f9079afdd1fdca51e86afe36ec2e59`.

Capture failed before producing capture JSON. The child reported
`BootstrapError: Unlisted frozen module`; the actual frozen module name is
unknown. The two outer children closed (manager exit 0, invoker exit 1).
The original capture receipt retains `closed=false`, unknown usage and a
cleanup `AssertionError`. Controller final evidence reports cgroup closure,
successful cleanup and 5.574222 service CPU seconds. The independent owner
lacks final identity/quota/burst observations after the service was cleared and
remains false/unknown. Later absence of the named cgroup and outer PIDs is a
limited diagnostic; it does not supply the missing owner observations.

The full 150 CPU service hold remains inside the capture charge without a
refund. These charged amounts are not complete measured whole-operation costs.
Capture receipt SHA-256:
`bb55fdfb736774e56a6607c740be3e1ca2e4d0de9a30514cb3a4d2cccaa7923f`.
Research and Quality independently accepted the failed-run evidence and retained
accounting. The source repair has passed static review. Software qualification,
new candidate delivery and actual execution await the [complete repair and
validation proposal](D1_RUNTIME_REPAIR_PLAN.md).
All four continuation attempts are consumed; no test, retry, new service or
remainder transfer is admitted. The scientific run remains unstarted.

## Final review and ledger

The [consolidated qualification result](D1_RUNTIME_QUALIFICATION_RESULT.md)
records the source-only repair proposals and the accepted evidence of capture
failure; this is not capture acceptance.

| Retained closeout record | SHA-256 |
| --- | --- |
| Quality combined continuation review | `7604e59cc4316c280354e34e200789fd354daa0460d2471df4ef4d7f9b9feed0` |
| Research benign/capture review | `ef9ebe6ed2d0481c2ff72d3dd988da5e614973e676b4cc77dd8b275f7f7aeb36` |
| Review/closure ledger | `2d2a592e453686667d07069188cfed762b7c1bdb624c3506c17cf3ad46949f71` |

The unchanged 50 CPU / 150 wall review account has 46.304715 CPU /
134.19866465963423 wall seconds of known observations plus retained/reserved
amounts. This includes each combined reviewer hold once, one 2/5 ledger-reader
hold and one reserved 2/5 Lead final-verification/closeout hold. Failed
construction/review attempts remain contained in their named holds, without
duplicate charges or refunds.

Unmeasured setup/admission peer reads and diagnostic closeout are explicit
within-review coverage gaps. Authoring, SSH/GitHub administration and provider
dollars are distinct external unknowns. Consequently this rollup is not a
complete observed cost or proof of hard 50/150 fit; its modeled margin is not
reusable authority. Original runtime usage/closure uncertainties are unchanged.
