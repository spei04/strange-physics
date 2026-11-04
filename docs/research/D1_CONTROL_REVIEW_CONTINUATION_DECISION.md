# D1 control-review repair and validation continuation

**Proposed; no successor invocation is authorized by this document.** Approve one complete engineering continuation after the [recorded control-review failure](D1_TEST_BOUNDARY_CONTINUATION_RESULT.md). The existing source correction remains at `ae0eea284132c4ca67815b29ba4cadfc5a6d2891`. The proposal does not repeat that patch or commit.

## Smallest semantic correction

Move the existing `approval = data(APPROVAL)` load before the first `refs[APPROVAL]` comparison. Research authored the exact 1,307-byte diff, SHA-256 `424b988721e66b7cbc1ffba910d1a04f13223aa80d62a539ab0b365779c14ec1`; Quality independently reconstructed the proposed 37,350-byte disabled reader, SHA-256 `ac8827a78adcc5cf02b76b9ae25ecf9eb5c7e6d8e723a45dda09b122e8de9c95`. It preserves every approval assertion and adds no read. The diff is prospective and has not been applied to an executable.

The failed review and completed handoff consumed their original exclusive records. Re-entry therefore also requires finite namespace, charge and predecessor-reference changes. Reusing those consumed names or rewriting their inputs would erase the failure boundary.

## One successor sequence

Use a new cycle-5 namespace for controls, admissions, preparation, reviews, proof and final closeout. Reuse only phase numbers 8 and 9, which have never been invoked. Existing phases 1–7, successful cycle-4 apply, failed control review and cycle-4 handoff remain immutable. This explicitly amends the prior “no fifth cycle” restriction.

| Event | CPU seconds | Active-wall seconds | Required result |
| --- | ---: | ---: | --- |
| Control regression and source/control rebind | 15 | 45 | Independent bounded regression 5/15, then staging 10/30; unchanged source/environment and exact reviewed successor controls |
| Copied-control review, E2 | 4 | 12 | Cold-cache approval join, actual rebind and original apply evidence accepted |
| Phase 8 preparation | 25 | 100 | Python/C sentinel checks and exactly 345 collected cases, no test bodies |
| Postcollection preparation | 5 | 15 | Original phase-8 output and collection bound to one check admission |
| Phase 9 checks | 180 | 500 | Format check, lint, typing and the same 345 cases / 1,035 ordered passing non-xfail phases |
| Outcome review, E2 | 4 | 12 | Complete original logs, source/environment, costs and process closure accepted |
| One success or failure-only handoff, E2 | 2 | 6 | Durable terminal evidence and truthful completion or stop |

B has exactly two successor preparation events and phases 8/9. Its new cycle allowance is **225 CPU / 675 active-wall seconds**; named B events sum to 225/660, leaving 15 wall seconds of contingency inside the allowance. Contingency grants no extra invocation. E2 has exactly three named slots totaling 10/30; failed early work permits only the already-budgeted failure closeout.

The isolated regression must exercise the corrected approval lookup with an initially empty cache, rejection of missing or mismatched approval material, and a failure-only closeout that retains the failure and grants no next-stage admission. It uses the exact final reader's lookup/validation and failure-closeout code through independently reviewed synthetic filesystem bindings, without invoking its production entry point. The four fixed cases are cold-cache valid approval, missing approval, mismatched approval, and failure after intent but before proof. Synthetic receipts are explicitly non-operational and never enter real E2 accounting. Harness setup, execution, any owned child, evidence writing and cleanup all fit within the same 5/15 sub-envelope; there is no extra setup slot. It uses explicitly enumerated synthetic fixture paths and bounded outputs, not the real dispatch namespace, a service, scientific primitives or project tests. Its exact fixture, commands and limits must be independently reviewed before the first invocation. Passing this regression does not replace the timed review of the actual retained records.

## Preserved history and finite interface changes

1. Reuse the already-committed test correction, source-map identity and locked environment. Recheck current identity and custody; do not alter application/test bytes, re-run the apply event, reinstall dependencies or create another checkout.
2. Keep all original source/control files, failed dispatch/intent/input/receipt, the successful failure handoff and stopped index. New cycle-5 files use exclusive names. Reuse unchanged guarded-child behavior and transport where their identities remain valid.
3. Rebind only fixed cycle/helper/record names, exact approved ceiling fields, actual predecessor identities and E2 totals. The B runner, postcollection binder and E2 outcome/handoff consumers must agree on the new control proof and receipt. Preparation references become 12 before phase 8 and 13 after postcollection. Current helper identities bind to the new counted rebind; the original source-freeze receipt remains source provenance. The old cycle-4 apply approval and the new cycle-5 authority are joined separately; neither is relabelled as the other. Original control proof absence remains a recorded failure.
4. Carry the original cycle-4 **220/660** hold exactly once. Its successful apply charge is contained within that hold. The successor history joins the stopped index and its actual apply/control/handoff receipts; it must not expect the sum of successful receipts alone to equal that conservative hold.
5. Use an explicit append-only inventory transition: every original path, byte count, hash and pool remains unchanged; add only named successor controls, fixture/proposal records and receipts. Preserve the original saved apply input. A new inventory may not masquerade as that original input.
6. The counted rebind must prove unchanged source/environment, accepted control identities, prior-cost continuity, complete output reservations and fresh filesystem fit. The actual copied-control review must validate these joins before phase 8.
7. Preserve one original complete stdout/exit/elapsed observation per event. Retain full bounded logs for semantic review, observed child closure and unknown/failure accounting. No reconstructed or truncated output can authorize a dependent stage.

These are finite adaptations of the reviewed controls, not permission to replace the control architecture or relax scientific boundaries. Final exact successor sources, fixture and prospective input/output manifest require independent review before execution.

## Complete allowance and retained charges

| Account | Current approved ceiling | Proposed ceiling | Change |
| --- | ---: | ---: | ---: |
| B software | 400 CPU / 1,200 wall | **600 CPU / 1,800 wall** | +200 / +600 |
| E2 review | 48 CPU / 144 wall | **54 CPU / 162 wall** | +6 / +18 |
| All review accounts | 128 CPU / 384 wall | **134 CPU / 402 wall** | +6 / +18 |
| Complete repair package | 1,218 CPU / 3,054 wall | **1,424 CPU / 3,672 wall** | +206 / +618 |

The original B retained hold is **367.445086 / 863.1534917629324**. Adding the full new 225/675 allowance gives **592.445086 / 1,538.1534917629324**, within the proposed B ceiling. No earlier charge or failure is refunded.

E2 opens at the actual retained **44/132** and progresses at most through 48/144, 52/156 and 54/162. The successor dispatch predecessors are 44, 48 and 52 CPU seconds. Its sole failure handoff may finish at 46/138, 50/150 or 54/162 according to the failed boundary. The allocation increase is 6/18 because the prior ceiling already included an uninvoked 4/12 slot; that unused slot alone granted no retry authority.

These are allocations and conservative holds, not measured whole-operation bills. Unknown usage remains unknown; a conservative held index does not waive actual process-closure checks. Authoring, static review, transport and project administration remain separately unmeasured.

## Storage and downstream scope

The existing **1 GiB global output cap and ten pool caps remain unchanged**, including software 32 MiB, review 8 MiB and source/controls 32 MiB. Retain all old files and classify every new source, fixture, input, receipt, log and failure leaf. The regression fixture and rebind outputs must fit inside the existing successor preparation/metadata/failure categories, with their exact named caps frozen before execution. No removal or reclassification is allowed to manufacture room.

The prospective fixed forecast is:

| Pool / output | Retained bytes | New reservation bytes | Forecast bytes |
| --- | ---: | ---: | ---: |
| Software | 1,989,471 | 25,509,888 | **27,499,359** of 33,554,432 |
| Review | 1,970,085 | 2,744,320 | **4,714,405** of 8,388,608 |
| Source and controls | 5,075,514 | 2,097,152 | **7,172,666** of 33,554,432 |
| New isolated regression fixture | 0 | 1,048,576 | **1,048,576** within the existing 134,217,728 temporary pool |

The private regression tree is `R/temporary/cycle5-control-regression`, at most 1 MiB / 128 entries, without links. Its software log and JSON receipt, `cycle5-control-regression.log` and `cycle5-control-regression.json`, are each at most 64 KiB. Their combined 128 KiB is carved from the existing 2,359,296-byte software metadata reservation, so the 25,509,888-byte software growth allowance does not increase. R denotes the existing owned repair root; no new cloud resource or checkout is needed.

All 267 original external rows and their classifications must be preserved against the actual original sealed input. Subsequent administrative/proposal artifacts and every successor copy count in the explicit append-only additions and source/controls bound.

An actual fresh census and complete remaining-write forecast, including the old cycle-4 records plus every proposed output, must fit before dispatch and at the existing boundaries. Existing available disk is an observation, not a reservation or scientific-capacity waiver. If the fixed package cannot fit, stop before invoking it.

After successful software, outcome and handoff acceptance, only the original conditional sequence may follow: one original PR CI sequence (83 configured job-minutes), one protected-main sequence (98), C installation 150 CPU / 450 wall and D runtime 500 CPU / 900 wall with its single capture. Their original admission/review/cleanup requirements remain in force. No CI rerun, new runtime attempt, scientific run, capacity operation, deployment or release authority is added.

## Exit and failure gates

- The independent cold-cache/failure-closeout regression passes within its 5/15 sub-envelope; the actual source/control rebind and copied-control review then pass.
- Collection is exactly 345 cases; checks preserve the same target inventory, 1,035 ordered passing phases, no xfail/skip/error/oracle-poison result, unchanged source/environment and known owned-process closure.
- Full original seven-stage logs, collector/JUnit evidence and actual charges are accepted by the outcome review; the sole handoff preserves the result.
- Any failed or unknown executed event stops dependent work. Preserve partial files and all holds; only its named bounded failure closeout may follow. No second successor attempt, sixth cycle or phase beyond 9 is authorized.

## Approval requested

Approve this complete cycle-5 control repair and validation package, including the finite record/inventory transition, bounded regression, B600/1800 and E2 54/162 ceilings, and the original downstream sequence conditional on every gate passing. The minimal semantic patch and accounting/sequence are reviewed; exact successor control and fixture review remains a prerequisite within this package, not an additional permission request.
