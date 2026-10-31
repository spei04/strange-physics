# D1 repair package progress

**Startup diagnosis passed; software qualification is next.** The approved package is still in progress. No new capture, scientific run or release has occurred.

## Approval and source

The owner approved the complete [repair and validation proposal](https://github.com/spei04/strange-physics/blob/ca0b26ae4763fd5f0db080395d0d8cd61fb6b833/docs/research/D1_RUNTIME_REPAIR_PLAN.md): 1,190 CPU / 2,970 active-wall seconds, one original PR/main CI sequence capped at 181 configured job-minutes, and 1 GiB of new artifacts. This is a fresh bounded package; the [previous failed capture](D1_RUNTIME_QUALIFICATION_RESULT.md), its full service reservation and all earlier charges/unknowns remain intact.

The new source draft is [58a8be4e873eb39ab7b0f37d7745ed85a5bae619](https://github.com/spei04/strange-physics/commit/58a8be4e873eb39ab7b0f37d7745ed85a5bae619), following the reviewed owner/diagnostic repair at `ed3053a`. The latest change touches only the two bootstrap files. It checks the two observed aliases before generic origin admission and adds 16 regression cases. The seven-target census is **345 cases / 1,035 prospective phases**; those checks have not run.

## Actual startup evidence

One diagnostic used the original accepted installation and exact source `5e0b3e7`. Its controller and launch admission were independently reviewed before execution. The diagnostic observed 81 registry entries and 18 frozen rows. Its only unlisted keys were:

| Observed key | Canonical module |
| --- | --- |
| `importlib._bootstrap` | `_frozen_importlib` |
| `importlib._bootstrap_external` | `_frozen_importlib_external` |

For both, actual observations joined the same canonical module object, exact specification name, frozen origin and `FrozenImporter` identity; the canonical name was already accepted. The pinned standard-library source contains both exact registry assignments. There were no unsupported unlisted keys. This satisfies the proposal's condition for the two narrow alias rules.

This result does **not** identify the unrecorded module name from the historical failed capture. The diagnostic observed the top-level import boundary, did not execute the original child validators, and did not invoke capture or a scientific primitive.

The one child exited zero, was reaped, reached EOF and closed its pipe. Its owned group was signaled before reap; no timeout, interruption, error or ownership loss was recorded. Parent execution also returned zero. The terminal records known usage and closure, with no first or supplemental fault.

Fresh before/after checks covered 437 source files, 2,498 protected-plan files and 123 native files. The explicit parent reader requested 553,662,678 bytes in 19,365 calls, with 102,155 metadata calls and 11,630 directory-entry observations, within the sealed limits. The child's fixed input-read scope is separate. Directory-entry observations are not a final filesystem census.

## Accounting and retained evidence

| A component | Charged CPU seconds | Charged active-wall seconds |
| --- | ---: | ---: |
| Activation preparation | 2 | 5 |
| Staging preparation | 4 | 10 |
| Diagnostic controller, child and included closeout | 6.296822 | 9.187402 |
| **A cumulative** | **12.296822** | **24.187402** |

Measured controller plus waited-child CPU was 4.296822 seconds; active wall was 4.187402 seconds. The last row above includes its 2 CPU / 5 wall closeout hold. Preparation is counted once. These are charged values with retained reservations, not a whole-operation cost measurement.

The five E1 review readers are closed at **10 CPU / 25 wall seconds**, within their 10/30 allocation. E2 software-control review remains in progress. Authoring, inference, transport and provider-dollar costs are separately unmeasured.

| Private evidence | SHA-256 |
| --- | --- |
| Direct approval | `a8f05cf1f0c312f2d87d608f649d2b902e139db143d0b4579a466ef642b8a7d3` |
| Executed A controller | `8730119ff075ade1640591d372264f8a3d8c8acfc56c8debcb8d6cbfc9c24828` |
| A launch admission | `dce20909d793b1bac5d475e0107cc4af4b4f4e59be569e1dbe8c658b807a1824` |
| A terminal, 12,029 bytes | `194931c3a064db2dda267457a887af663795d4eb48ff6a75c882790e0612da14` |
| Diagnostic log, 7,808 bytes | `6b98b78815d671f01df23b91cc88060801bc277a1cfc609e3d77372f815f9f7a` |
| Independent outcome reader | `67a0038713857fdc4f9c61cde53115079ef50bb247365a7afef29bbb95df53d0` |

The external control-copy census retained 37 files / 406,013 bytes. The controller checked the runtime-root output bound but discarded that census's returned totals; no exact final runtime-root byte/count claim is made. Later whole-package accounting must retain its own fresh census. This does not erase the known terminal/log sizes or earlier evidence.

All records and installations remain private in the cloud, with their prior retention obligations. Both existing checkouts are reused.

## Next owners and gates

Research supplies the final source/import/fixture census. Quality reviews the exact source and disabled software controls. Lead then seals and executes B's bounded formatter, collection, typing and guarded-test sequence. Platform has prepared disabled candidate-acquisition/setup controls.

Only accepted B evidence permits the one original PR CI sequence and protected-main candidate delivery. A passing startup diagnostic does not establish capture qualification, scientific adequacy, exposure independence or production readiness. Scientific storage guards remain unchanged; the separate capacity proposal has not been approved or executed.
