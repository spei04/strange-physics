# D1 repair package progress

**Software qualification stopped at typing; both approved cycles are consumed.** Formatting and lint passed, but five typing errors prevented regression-test dispatch. E2 is closed with all charges retained. The narrow typing fix is source-reviewed but unexecuted; the [complete continuation decision](D1_RUNTIME_REPAIR_CONTINUATION_DECISION.md) remains proposed, not approved. CI, candidate setup and actual capture are unstarted.

## Approval and source

The owner approved the complete [repair and validation proposal](https://github.com/spei04/strange-physics/blob/ca0b26ae4763fd5f0db080395d0d8cd61fb6b833/docs/research/D1_RUNTIME_REPAIR_PLAN.md): 1,190 CPU / 2,970 active-wall seconds, one original PR/main CI sequence capped at 181 configured job-minutes, and 1 GiB of new artifacts. This is a fresh bounded package; the [previous failed capture](D1_RUNTIME_QUALIFICATION_RESULT.md), its full service reservation and all earlier charges/unknowns remain intact.

Source [58a8be4e873eb39ab7b0f37d7745ed85a5bae619](https://github.com/spei04/strange-physics/commit/58a8be4e873eb39ab7b0f37d7745ed85a5bae619) and its final import/fixture census are independently accepted by source review. It follows the owner/diagnostic repair at `ed3053a`; the latest change touches only the two bootstrap files, checks the two observed aliases before generic origin admission and adds 16 regression cases. The seven targets contain **345 cases / 1,035 prospective phases**. The regression bodies have not run; current software-check outcomes are recorded below. The independently accepted preparation `bd9701de` has now executed once; its successful result, the withdrawn original admission and the later first format outcome are recorded below.

## Software preparation and controls

The one preparation passed with **four closed children and known usage**, producing exactly seven files / 111,250 bytes. Source and environment identities were unchanged. Its terminal is 4,460 bytes, pinned in the evidence table below.

The preparation charge is **5.566901 CPU / 9.263535339850932 active-wall seconds**, including the 2 CPU / 5 wall closeout reservation once. The initial 10 CPU / 30 wall intent is not an additional charge. The later final observed counters were 3.568835 CPU / 4.270335783716291 wall; these are a separate observation, not a value to add to the charged total.

Quality accepted the actual preparation and prospective formatting admission. Before formatting began, Lead found missing-child-record handling, unknown-usage charging, cleanup and `SIGHUP` weaknesses in the shared check runner `97b026d8`. **That original formatting admission was withdrawn before use.** Platform produced the versioned correction, Quality accepted its source and actual reseal, and Lead executed the first format phase under the replacement admission. The successful original preparation and all withdrawn controls remain retained.

The one control reseal returned zero with known usage, no children and no phase dispatch. Its exact readback contains the original seven files plus five versioned outputs: **12 files / 177,592 bytes**. The reseal charge is **2.24322 CPU / 5.25870868191123 wall seconds**, including its 2/5 closeout hold. Its initial 5/15 reservation is nonadditive. Combined B preparation is **7.810121 CPU / 14.522244021762162 wall**.

The first format phase then returned zero with a single matching-identity stdout, known closure/usage and no terminal-write error. It reports **5.714151 measured CPU / 7.083330078050494 active wall**, charged **7.714151 / 12.083330078050494** including closeout. The observed outer completion took 9.365 seconds, within that retained wall charge. Cumulative B is **15.524272 CPU / 26.605574099812657 wall**. The later preparation verified the exact format attempt, six child dispatches, two stages and original stdout, then stopped before Git while checking source custody. No regression-test result is inferred from formatting.

C v2 acquisition/setup controls are independently accepted for their disabled source scope, indexed by `ba417a6c`. The complete exporter, candidate verifier and setup bodies were reviewed with their diffs and recipe. Exact candidate, receiver, tool/startup/custody identities and acquisition charges still require sealing before execution. Their storage checks are detection and acceptance ceilings, not an aggregate filesystem quota.

### Source-freeze checkpoint

The one source-freeze invocation returned exit one with known usage/closure, no children, no Git dispatch and no next admission. It retained the successful format outcome and reported only two formatter changes: the capture-owner helper and its tests. Its charge is **2.075238 CPU / 5.054526579100639 wall**, including the 2/5 closeout hold. Cumulative B is now **17.59951 CPU / 31.660100678913295 wall**; the original 5/15 preparation reservation is nonadditive.

The exact failed receipt records 187,055 requested read bytes, 23 software entries / 239,917 bytes before the source check, and a bare assertion failure. A bounded metadata diagnosis inspected the 437 manifest entries and 12 distinct parent directories without reading checkout payloads or executing project code. It found **393 ordinary checkout files rejected only by the new no-group-write rule**; the first current rejection is `.gitattributes` with mode `0664`. All three helper files have the expected private metadata and exact hashes. The accepted phase runner did not impose that source-file mode restriction. The historical exception did not record its line or path, so the metadata observation is not presented as a recovered traceback.

The correction separates ordinary checkout reads from strict private-record reads; no permission changes are needed. The known failed preparation consumes cycle one. Quality accepted using the already approved second cycle with every prior charge retained once: cycle two remains limited to 200 CPU / 600 wall within aggregate 400/1,200, without transferring unused cycle-one capacity. Its preparation will commit only the two verified formatting changes, preserve the original files and version the controls. Actual format attempt two must then be observed before its source-freeze record, collection and checks can be admitted. No future result is preclaimed.

### Second software cycle

The approved second-cycle preparation passed once with known usage and closure. Its eight Git operations committed only the two retained formatter changes, verified all 437 source files, and confirmed a clean checkout at `fbe9d367fba03719ea9018961eaf013831ffb436` (tree `ace4404a5da45dedf6f6c32434502bdc50221b84`). The separate checkout reader permits normal source-file permissions without changing them; private records retain their stricter checks. Original controls, the failed first-cycle checkpoint, and its successful formatting outcome remain preserved.

Preparation charged **2.448797 CPU / 5.844272852875292 wall seconds**, including the 2/5 closeout reservation. It read back its saved records and the namespace-only second-cycle controls within that counted invocation. The exact preparation receipt is 10,396 bytes, SHA-256 `b12fa5bca4318f7b0e18ba508fe4542ffdb586f1b61ceac5e1c4a2e58c86e0d3`; its format admission is 3,153 bytes, SHA-256 `4e41617d0ef8cb73ba4e7b454ecc0557eab4957010771efc110ce50b965de62a`. Independent review accepted these actual joins without another E2 reader.

Format attempt two then returned exit zero, known closure and usage, no failure and no terminal-write error. Actual stdout identifies the 10,282-byte attempt receipt, SHA-256 `a32a5e6ce87fea6042a338f48156cc8ac380c7733db08b777fb294bd22fe7321`. It measured 4.644141 CPU / 5.073653000872582 active-wall seconds and retained **6.644141 CPU / 10.073653000872582 wall**, including closeout. The outer process completed in 5.529233457986265 seconds, covered by that charge.

B now retains **26.692448000000002 CPU / 47.57802653266117 wall seconds** across both cycles; cycle two retains **9.092938 CPU / 15.917925853747874 wall**. Failed first-cycle work remains charged once. E2 remains 18/45, with its final 2/15 slot retained for software evidence review. Formatting is not a regression-test result: a counted checkpoint must still reconcile the exact durable attempt and original stdout, source manifests and current commit before admitting collection. No third cycle is authorized.

### Second-cycle check stopped at typing (2026-11-01)

The second cycle is closed with a software qualification failure. Formatting
and lint passed, then full typing reported **five errors in two files, checking
236 source files**. The failures are four loader/specification type mismatches
and one assertion using a function that returns `None`. The unchanged original
798-byte typing log has SHA-256
`b56ff9aa898815e81a851acd46aa55a1bb07be063046a52ffb5e89d097fc2f34`.
The three check stages are format, lint and typing; **regression tests were not
dispatched**, and there is no test collector receipt or JUnit result.

All four phase invocations and six preparation charges are retained once.
B totals **76.648979 CPU / 110.11677537020296 active-wall seconds**;
cycle two totals **59.049469 / 78.45667469128966**. These charged totals include
retained closeout reservations and failed work, not just measured test CPU.
The retained software census contains **66 entries / 721,512 bytes**.

The final independent E2 evidence reader returned zero, with an empty stderr,
no reader failure and observed outer elapsed time 0.239522499992745 seconds.
Its 971-byte receipt is
`b178bedf775530ed2243494d82b6d342d020349767ca41331cacb81bc626518d`;
the 64,069-byte evidence payload is
`250dbe1ee26616f7b249df05ca4c0e62ffdef3b2b9facc82e70181d9f06f8091`.
Its reserved 2 CPU / 15 wall closes E2 at **20 / 60**, rather than creating a
new allowance. Known closure does not turn the typing failure into a pass.

Both approved B cycles are consumed. Research committed the two-file typing
fix at [4d83811cb46892c55e772392b5b29dc7ce008b42](https://github.com/spei04/strange-physics/commit/4d83811cb46892c55e772392b5b29dc7ce008b42),
tree `dfa20b44235dd9f87ab6300b6f9835ef6796ac83`. Lead and Quality accepted
its source: exact frozen-loader identity and behavioral assertions remain
intact; imports and case counts are unchanged. No typing or regression tests
have run on the fix. The [continuation decision](D1_RUNTIME_REPAIR_CONTINUATION_DECISION.md)
proposes one final 200/600 cycle within unchanged aggregate B 400/1,200, plus
10/30 for E2 review. That would make the package 1,200 CPU / 3,000 active-wall
seconds; it is **not approved or admitted**. The original PR/main sequence,
C/D work, installations and capture remain unstarted. No scientific or
capacity action is included.

### Current package closeout (2026-11-01)

The one final E7 closeout returned zero with no failure; its outer elapsed time
was 0.9306244170002174 seconds. The fixed **3 CPU / 10 wall** charge is retained
once inside original E7 10/30, leaving **7/20** for later final review. The
2,906-byte result has SHA-256
`b8586716e965b29570b0386e996cd0e09a3c825ca1578a4dee3d24a02fc463ff`.
This elapsed observation is not the charged command allowance.

| Retained scope | Entries | Logical bytes |
| --- | ---: | ---: |
| Current repair root | 157 | 2,247,844 |
| All old and new records in the named private evidence directory | 4,672 | 63,995,181 |

The repair root includes software 721,512 bytes, reviews 1,384,184, controls
88,276 and evidence 53,872. The no-follow census also retained 179 links,
10 hard-link names and four FIFOs in the wider evidence directory. The
conservative combined upper bound, including the result reservation, is
**66,300,369 bytes**, below 1 GiB. It includes historical records: it is not
new growth, a fresh pool allocation or proof of a universal transient-peak
quota. The old installation was not reread and no data was deleted.

Actual free space was **43,511,271,424 bytes**. Scientific storage guards remain
unchanged. Research confirmed the unchanged 8,024,322-byte two-suite fixture
bound covers the single proposed suite, but every future stage must still fit
all retained bytes plus its full writes and closeout reservation in its pool.
Source `4d83811c` is published on a feature branch without a PR or CI run.
The [complete amendment](D1_RUNTIME_REPAIR_CONTINUATION_DECISION.md) remains
proposed, not approved; no additional software or runtime command followed.

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

The five E1 review readers are closed at **10 CPU / 25 wall seconds**, within their 10/30 allocation. E2 software-control, preparation and failure-evidence review is closed at **20 CPU / 60 wall seconds**, including the final 2/15 reader once. The slots named `cycle2-admission` and `cycle2-result` were used for cycle-one reseal and failed-checkpoint diagnosis; these historical review names describe those earlier uses, not additional cycle-two charges. E5 retains **4 CPU / 10 wall seconds**: the original operator read at 2/5 remains charged, and the complete correction read adds 2/5. Its full nine-file packet was retained in memory and reviewed without another cloud read; C v2 source acceptance does not authorize acquisition or setup. Authoring, inference, transport and provider-dollar costs are separately unmeasured.

| Private evidence | SHA-256 |
| --- | --- |
| Direct approval | `a8f05cf1f0c312f2d87d608f649d2b902e139db143d0b4579a466ef642b8a7d3` |
| Executed A controller | `8730119ff075ade1640591d372264f8a3d8c8acfc56c8debcb8d6cbfc9c24828` |
| A launch admission | `dce20909d793b1bac5d475e0107cc4af4b4f4e59be569e1dbe8c658b807a1824` |
| A terminal, 12,029 bytes | `194931c3a064db2dda267457a887af663795d4eb48ff6a75c882790e0612da14` |
| Diagnostic log, 7,808 bytes | `6b98b78815d671f01df23b91cc88060801bc277a1cfc609e3d77372f815f9f7a` |
| Independent outcome reader | `67a0038713857fdc4f9c61cde53115079ef50bb247365a7afef29bbb95df53d0` |
| Successful software-preparation terminal, 4,460 bytes | `4e93b26ac6a533e79ceafdbab853499f28c83dd503b2146c307a492f9369b817` |
| E2 preparation readback receipt, 936 bytes | `d09da0c082a019d7e060dbf0f183ce3fcf993a5de2f71515b48857e79a8f29cb` |
| Successful reseal terminal, 2,145 bytes | `1af743d95d3b4f5c2ae659067fdb900a1eda0f20041f6188440ef043aa53dff5` |
| Replacement format admission, 2,521 bytes | `48c4ecc903b9db4433056151e9b7dea81d63e7330d763ffc7b28aa51b07b59ba` |
| E2 reseal readback receipt, 933 bytes | `eda992437bdbc371e0d5d81eb4e8eb51c2e1f99531d6a4225a72df9f63b6f7c6` |
| Format attempt receipt, 9,800 bytes; durable join verified | `bc610a2cc424e3ea70fb9bbb6d77c92a0bf4a88964954cfeb3accc43aa5d37f6` |
| Known failed source-freeze preparation, 1,959 bytes | `e60bc27e4b927224a729bd40b22b1a45159a404cd5aa2d1338a8fd8f3893ade8` |
| Retained successful format outcome, 1,089 bytes | `1571d9d5f4016b4eaa4e6df926acb82fb5ec2a5888bdf0ba8b0ee4066bc5c483` |
| E2 failed-checkpoint metadata reader, 924 bytes | `985aabce24df0bcb8b73e6ac6e55fe70aeab3ec199411ea90ad5102b14d666fb` |
| Accepted disabled C v2 index, 2,926 bytes | `ba417a6c514e233b3e35b405fb3b89388d122fadb5dff20b94d7f24c9334b501` |
| E5 complete correction reader, 915 bytes | `c769d930a575784062b6b78a63a786955a24d161a25f9921419107d557dbfc85` |

The external control-copy census retained 37 files / 406,013 bytes. The controller checked the runtime-root output bound but discarded that census's returned totals; no exact final runtime-root byte/count claim is made. Later whole-package accounting must retain its own fresh census. This does not erase the known terminal/log sizes or earlier evidence.

All records and installations remain private in the cloud, with their prior retention obligations. Both existing checkouts are reused.

## Next owners and gates

Research's narrow typing fix is source-reviewed; Quality will independently
review its eventual qualification evidence. Platform maintains the complete
continuation decision and preserved delivery/runtime drafts. Lead owns the
one approval handoff and
remains the sole executor. No third-cycle command is admitted.

The [proposed amendment](D1_RUNTIME_REPAIR_CONTINUATION_DECISION.md) pins the reviewed
fix and finite cycle-three namespace. Cumulative fixture/output fit and exact
executable controls must be sealed before admission after approval. Both prior cycles, their failures and E2 consumption
remain retained. C v2 and D v6 remain disabled source checkpoints; actual
candidate/runtime pins and hosted evidence controls still require sealing.

Only independently accepted B evidence permits the original PR CI sequence and
protected-main candidate delivery. Startup diagnosis does not establish capture
qualification, scientific adequacy, exposure independence or production
readiness. Scientific storage guards remain unchanged; the separate capacity
proposal has not been approved or executed.
