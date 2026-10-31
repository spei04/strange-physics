# D1 runtime continuation decision

Status: **independently reviewed proposal; awaiting user approval**. The current runtime account remains **200 CPU / 600 active-wall seconds**. No remaining stage has started.

## Decision requested

Approve **400 CPU / 600 active-wall seconds** for the existing runtime qualification account: an increase of **200 CPU seconds only**. Keep all previous charges and failed attempts. This is a finite continuation of the engineering checks, with one attempt per remaining stage. It does not authorize a scientific run, new infrastructure, deployment, release or additional provider spending.

The total four-part local command allocation would change from 600 CPU / 1,800 active-wall seconds to **800 CPU / 1,800 active-wall seconds**. Source qualification stays 200/600, acquisition/setup stays 150/450, and review/closure stays 50/150. Closed balances cannot transfer into this account.

## Verified starting point

The exact source is [5e0b3e7db436061f4d7c9a5e983f7878cea31974](https://github.com/spei04/strange-physics/commit/5e0b3e7db436061f4d7c9a5e983f7878cea31974). [Main CI run 41230418150, attempt 1](https://github.com/spei04/strange-physics/actions/runs/41230418150) passed all seven jobs, including the unpublished candidate build and installed-wheel smoke. The candidate archive, five retained inputs and actual private installation were verified. This proposal does not relabel a later documentation commit as that candidate.

Setup completed with five closed subprocesses. The earlier startup-cache rejection remains retained; its exact root-owned bytecode was checked against the pinned source without executing it. A single installer-created empty lockfile was changed from mode 0666 to 0600 with its identity preserved. The final setup account is **22.297874 CPU / 43.566476 active-wall seconds**, separate from the runtime account.

Native attempt 3 passed: **115 loadable ELF files, 234 dependency edges and 116 closed subprocesses**. Attempts 1 and 2 remain failed and charged; all 147 subprocesses across the three attempts have closed. The runtime account retains **48.88882 CPU / 66.534427 active-wall seconds**. Its native closure and process accounting received independent reviews.

The two failures identified a duplicate ELF-version label and a compiler object that is not a loadable library. Narrow parser/classification repairs were checked against retained output and negative fixtures. The compiler object remains in the full hashed inventory; it was not silently removed from custody checks.

## Why the current allowance is insufficient

The existing account has 151.11118 CPU seconds left. The fixed capture requires its **150 CPU-second service reservation plus 10 CPU seconds of headroom**, before the preceding stages or their closeout. It therefore cannot be admitted within the current cap. No materialization, guard probe, live-descendant witness or capture was launched after this determination.

A previous 300/900 draft was neither admitted nor executed. It is superseded by this explicit proposal; it did not change authorization.

## Remaining allocation

| Ordered stage | CPU seconds | Active-wall seconds | Included work |
| --- | ---: | ---: | --- |
| Materialize | 25 | 60 | Recheck actual inventory and create the installation record and protected capture plan. |
| Guard probes | 15 | 45 | Three separately reaped benign callbacks using retained Python code, a source route and C builtin `len`. |
| Descendant witness | 80 | 90 | Fixed leader-exit/live-descendant handshake; 35 service + 30 outer command + 15 other CPU seconds. |
| Capture only | 200 | 330 | Sole fixed independent-owner invocation; 150 service + 30 outer command + 20 other CPU seconds. |
| **Remaining maximum allocations** | **320** | **525** | Each stage includes its 2 CPU / 5 wall closeout reserve. |
| **Previously retained charge** | **48.88882** | **66.534427** | Both failed native attempts and successful attempt 3. |
| **Prospective total** | **368.88882** | **591.534427** | Within proposed 400/600, conditional on live admission checks. |

The arithmetic leaves 31.11118 CPU and approximately 8.465573 wall seconds below the proposed aggregate ceilings. This is not a promise that every stage will fit: stage and aggregate checks must preserve future reservations. Capture must have its full 300-second outer invocation available after prechecks or refuse dispatch. The plan does not shorten the capture profile to manufacture a fit.

The fixed service limits, per-child CPU ceilings, output bounds, source identities, prior receipts and failure handling remain in force. Uncertain closure retains its reservation and prevents advancement. Any stage failure stops this sequence after closure and accounting; another attempt requires a revised concrete plan.

## Review and execution boundary

The exact continuation operator passed static construction checks and independent source/plan review. It rejects a new native attempt, binds the four stage allocations, and preserves the earlier native charges exactly once. It remains separate from the active controls and has not executed. A hash-bound approval record must correspond to a direct user answer; creating a JSON record cannot supply authority.

| Private retained artifact | SHA-256 |
| --- | --- |
| Complete continuation proposal | `32c3e66359f64e08cd7b375f0d980184492122c06e65417968404831a68e754a` |
| Unexecuted continuation operator | `aa1d3916598c3ada568a5004939600d14b80b7ab1a304d75b6cf1db2d4b6da0e` |
| Author static-check receipt | `f6704d8778a69072bfd117ea2a8f99048cb62b3312b00de742859ca871e96d86` |
| Independent source/plan review | `9f74e44b6853eea6d7c35dc9560912622cafa70403a65d96815e2b5ceb4fc419` |
| Successful native attempt 3 receipt | `df820792dad7d964f7894d2e41ffbcfc5ae0c8b0924a6c0529d43e6b319742ec` |
| Actual native closure | `ea85c3347f1ab25658032ac2a4994678130fbcd34dd8d43f987461546865c483` |

Static review is not execution evidence. Each engineer's final proposal review retains its full 5 CPU / 15 wall hold in the unchanged review partition. The author's earlier failed validation assertion is retained within that same author hold. No remaining runtime stage or new CI run was needed to prepare this decision.

The original materialize admission was prepared under 200/600 but never executed. If approved, preserve it as an unused record and create a distinct admission for the reviewed continuation. Each later admission must bind the actual preceding successful receipt. No stage may run on a placeholder or stale artifact identity.

These are prospective command allocations and observed accounting scopes, not a hard kernel-wide aggregate CPU guarantee. Named-service CPU is separate from parent/waited-child CPU; overlapping inner scopes are not added twice. Authoring, SSH/GitHub administration, whole-operation CPU and provider dollars remain unmeasured. Storage checks are observed inventories and per-file bounds, not a universal transient-peak quota.

Static native closure does not prove that every future API or opaque dynamic load is covered. This path checks the pinned installation and capture-only invocation. NumPy startup may perform its ordinary sanity arithmetic; the guard forbids D1 scientific primitive execution. Original provisional `accepted=false` records remain unchanged; any external qualification must be a separate evidence-backed record.

The scientific batch, disjoint evaluation inventory, numerical adequacy and recovery/generalization claims remain separate gates. The scientific disk reserve is unwaived. Passing this continuation would establish the bounded capture path, not production readiness or a research result.

## Team and progress

- Lead: evidence custody, finite allocation proposal, approval handoff and sole future executor.
- Quality engineer: exact continuation operator, stage limits and failure-path review.
- Research engineer: independent allocation, source and evidence review.
- Platform engineer: consistent roadmap, backlog and assignment updates.

Private evidence stays in the existing protected cloud record. Review date: 2026-11-30. Both current checkouts are retained for reuse; no new worktree or local project copy is needed.
