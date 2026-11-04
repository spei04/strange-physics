# D1 control-review continuation result

**Status: stopped after the initial rebind's final report failed.** The owner-approved [cycle-5 continuation](D1_CONTROL_REVIEW_CONTINUATION_DECISION.md) ran on 2026-11-04 UTC. All four isolated regression cases passed, but the parent returned exit 1 and no terminal stdout. The sole failure handoff passed. No copied-control review, phase 8/9, CI, installation, runtime capture or scientific run followed.

## Actual sequence

| Event | Original exit | Remote elapsed seconds | Outcome |
| --- | ---: | ---: | --- |
| Regression and source/control rebind | 1 | 6.2504616770893335 | Final report raised `KeyError: 'kind'`; stdout was empty |
| Sole failure-only handoff | 0 | 0.5422803652472794 | Durable stopped index; no new admission |

These are original received exits and elapsed observations. The complete original streams are retained privately in a 7,385-byte record, SHA-256 `e75fb3c4d2f615d59b6bde72cd82e47716260347e4ab4bf295acb59e4ca7cde6`. They were not reconstructed from saved candidate receipts.

Source remains `ae0eea284132c4ca67815b29ba4cadfc5a6d2891`, tree `0b251cc063504992cffde4b7b68d94dc70064567`. There was no new application/test change, commit, dependency installation or checkout. Both existing checkouts remain needed.

## What the retained preparation establishes

Administrative incident inspection after the failure handoff found:

- All four exact regression cases passed: cold-cache valid approval, missing approval, mismatched approval, and failure after intent before proof. Their synthetic receipts grant no operational admission.
- The regression fixture was cleaned up. Its recorded maximum was 1,652 bytes / 25 entries.
- All five owned children returned exit 0 with reaped leaders, EOF, closed pipes and no recorded process errors.
- The preparation records no earlier failure; it verified 437 source paths and the unchanged environment, and wrote the two expected helper copies and a candidate prepare admission.
- The final report failed afterward. Existing inner receipts and that admission do not override the actual nonzero exit and absent original success output.

The regression receipt is 1,680 bytes, SHA-256 `bd50f78540a5d2c5b8142f906747d8081911902510aae3e201733a723e6229aa`. The preparation is 20,499 bytes, SHA-256 `dcfdab02a4b580a911d5c0a7937d851afde0a8a4e1a8bfbf54d8dfc0d4c9a9c6`. Independent incident review verified these exact records. This is scoped engineering evidence, not completed software qualification or a research result.

## Cause and correction

The new regression dispatch records `kind: "regression"`. The inherited Git producer records only `argv` and `output_cap`. The final report requires every row to have `kind`:

```python
sum(item["kind"] == "git" for item in attempted)
```

The first Git row therefore raises `KeyError`. The exception occurs while constructing the report, before its output handler. The later control reader also expects explicit Git kinds, so merely making the report use a default would hide the contract mismatch.

The smallest correction is to add `"kind": "git"` at the Git producer's append. Platform prepared the one-line prospective diff; Quality independently verified its exact bytes and resulting source identity. It is unapplied and unexecuted:

- Diff: 579 bytes, SHA-256 `2a132aad99b30760c3d2a2bbf50961cacd9782bbde9aba5b4fe0b92125aa3a0c`.
- Prospective corrected disabled source: 58,054 bytes, SHA-256 `21fbeb9901dfb6f022c7d93959a75f7942b2cebbac076832f2911b41165ce5a5`.

Static review checked the consumer's expected kinds but missed the producer's actual dictionary shape. The four regression cases covered approval loading and failure closeout, not this mixed dispatch-record/report path. Lead and both source reviewers missed that join. The correction needs a focused check of the actual producer and reporting expression before another expensive stage; adding another supervisor is unnecessary.

## Retained accounting and custody

The preparation recorded 7.912113 CPU / 11.188860496040434 active-wall seconds including its 2/5 closeout reservation. That inner charge is contained in the full failed-cycle hold; it is not added again.

The stopped B index retains the prior 367.445086 / 863.1534917629324 plus the full cycle-5 225/675 once: **592.445086 CPU / 1,538.1534917629324 wall**. E2 retains **46/138** after its sole 2/6 failure handoff. The index preserves unknown actual-cost limits and does not claim a measured whole-operation bill.

The handoff receipt is 4,305 bytes, SHA-256 `36f47d58cf0f374970e1eebf7eb28c8e94ba8d8f97138f845f0b351c76584891`; the stopped index is 3,104 bytes, SHA-256 `3b81b5a47c99b4cba8dde15be3b2f739cca39941780f0674bb89ba57ee0f6440`.

The frozen input preserved all 267 original rows and added 33 records: 300 rows, 1,166,744 appended bytes. The original input was 75,018 bytes, SHA-256 `c83b60b341514fa26dea7c5cb8ad6365593b7b3cd430c3af473cbd9379e5a327`. Before dispatch, the complete remaining output reservation was 1,063,496,843 bytes against 41,220,575,232 available filesystem bytes. Subsequent original-output and incident records remain private and separately counted; they do not rewrite this frozen input. Required evidence is preserved beyond its 2026-12-04 diagnostic review date when unresolved or otherwise required.

Source authoring, static/administrative incident inspection, coordination and transport are separately unmeasured. No cost, failure or admission is erased by this result.

## Remaining work

The [minimal complete continuation proposal](D1_DISPATCH_RECORD_CONTINUATION_DECISION.md) covers the reviewed producer correction, one bounded contract acceptance check, the still-uninvoked software phases, and the original conditional CI/install/runtime sequence. It is not approval.

The approved cycle-5 decision explicitly says: “No second successor attempt, sixth cycle or phase beyond 9 is authorized.” Its stop and closeout are complete. No retry, scientific execution, capacity operation, deployment or release has been started.
