# D1 test-boundary continuation result

**Status: stopped after a failed control review; source correction applied, regression validation unrun.** The owner approved the [test-boundary continuation](D1_TEST_BOUNDARY_CONTINUATION_DECISION.md) on 2026-11-03. The three executions below completed on 2026-11-04 UTC (2026-11-03 Pacific). No scientific result or production-readiness claim follows from this engineering work.

## Observed sequence

| Event | Original exit | Remote elapsed seconds | Result |
| --- | ---: | ---: | --- |
| Approved apply and source freeze | 0 | 7.751964611932635 | Exact test-only correction committed; 437 source paths, pinned environment and two copied helpers verified |
| Timed copied-control review | 1 | 0.4114115238189697 | `KeyError:'d1-test-boundary-owner-approval-20261103.json'`; no control proof |
| Sole failure-only handoff | 0 | 0.534108798019588 | Failure index retained; no downstream admission |

Source commit: `ae0eea284132c4ca67815b29ba4cadfc5a6d2891`; tree: `0b251cc063504992cffde4b7b68d94dc70064567`; parent: `de464a1719c2e68f7773d7e04cdef0a8b9be5d51`. The only changed path is `tests/test_d1_capture_owner.py`. Its SHA-256 is `f994306e3852f85ca38a21b23f2ddc438a9f48ce06df653193d1fdf7f76afc3d`. The fixture marker distinguishes setup activity from the resumed parent's service access.

The source freeze completed all nine owned Git observations with recorded closure and verified the environment before and after the commit. The source map is 46,768 bytes, SHA-256 `935b893d42c960196cf076261f68b682c680519d36218e8e6edaa678d392fe53`.

Phases 8 and 9 were never invoked; their attempt receipts are absent. No new regression pass, formatter/lint/type result, CI run, installation, capture or scientific execution is claimed. The earlier 344-pass/one-failure result remains historical evidence from the preceding source.

## Defect and independent diagnosis

The control reader initializes a cache of verified file references lazily. In accepted control-v4, line 434 compares the preparation's approval reference with `refs[APPROVAL]`, while the existing `approval = data(APPROVAL)` load occurs at line 445. Defining the expected hash in `PINS` and hashing external files do not populate `refs`. A fresh invocation therefore fails at the first comparison.

Research, Quality and Lead confirmed this ordering from the exact source. The prospective semantic correction moves the existing pinned approval read before the comparison and preserves all approval identity and scope assertions. No extra file read, production-code change or repeat application of the test patch is needed for that semantic correction.

Static review missed this defect. Its prior acceptance remains retained and is not represented as successful runtime validation. The narrow related review found the outcome reader already loads this approval before comparing its reference; the handoff has no corresponding approval-reference lookup. This does not establish that every future execution path has been tested.

## Retained accounting

The apply preparation retains **7.907211 CPU / 12.694739777129143 active-wall seconds**, including its fixed closeout reservations. Its successful preparation brings known B receipt charges to **155.352297 / 215.84823154006153**.

The stopped cycle index conservatively retains the full current-cycle **220 / 660** hold, producing **367.445086 / 863.1534917629324** with the earlier B opening amounts. The preparation charge is already inside that current-cycle hold and must not be added again. The index explicitly does not assert a measured whole-operation cost or a proven upper bound for unknown usage. It grants no refund or replay.

E2 retains **44 CPU / 132 wall seconds**: earlier 38/114, failed control 4/12 and completed failure handoff 2/6. Source authoring, static review, transport and project administration remain separately unmeasured.

The complete original stdout and stderr were captured once in bounded memory and retained privately after closeout. No second execution or reconstructed output substitutes for those streams.

## Evidence identities

| Private record | Bytes | SHA-256 |
| --- | ---: | --- |
| Successful preparation | 19,911 | `2f3a646aa018c09e2d5d5cdd231921b65de3c80717be5e2bfc8ba8348dcc74f7` |
| Failed control receipt | 2,529 | `37a5309f95133933432abe6bc4bb7b35273ad8fedcd6e0383492ded78c303b4f` |
| Failure handoff receipt | 4,231 | `8045485e4477c72a2880f9ca57d724566f855b8af6d76badba1d707995a81a52` |
| Stopped cycle index | 2,072 | `f0a8460efc2a45c6eb5d8110a44202734b82f78b875b4c4de3963684fb9de134` |
| Original execution observations | 16,058 | `89eecf4c4964969fea49c248777b68fb0b3db3d7907fda90cf235d48b93e1cb3` |

Private records remain owner-readable in the cloud evidence/runtime locations, outside disposable checkouts. Review the administrative archive on 2026-12-04; preserve unresolved and required release/incident evidence beyond that date. No off-device backup is claimed.

## Storage, assignments and next boundary

The sealed initial input covered 267 external files / 4,969,873 bytes and all retained package outputs. Fresh checks reserved the remaining approved output space; the initial available filesystem space was 41,259,806,720 bytes. These engineering checks do not waive the separate scientific free-space reserve.

Platform authored B controls; Research authored E2 controls; Quality independently reviewed both; Lead sealed and executed the three events. After the failure, Research owns the minimal source correction, Platform owns the complete successor dependency and resource plan, Quality independently reviews the correction and proposal, and Lead maintains evidence and publication.

Both existing cloud checkouts remain required. No checkout, environment, failed evidence or retained release branch was removed. No capacity snapshot, restored-disk recovery, attachment or resize was executed; the owner's existing 320 GiB and restore-copy recovery approvals remain valid for a freshly coordinated maintenance entry.

The approved stopping rule says: “A failed or unknown executed preparation, phase, review or handoff stops dependent work.” Its failure closeout is complete. The subsequently approved [successor decision](D1_CONTROL_REVIEW_CONTINUATION_DECISION.md) preserved these records and executed once. Its [separate cycle-5 result](D1_CONTROL_REVIEW_CONTINUATION_RESULT.md) records a later report-contract failure; neither result authorizes another invocation.
