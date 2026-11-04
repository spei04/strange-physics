# D1 durable-delivery and end-to-end validation continuation

**Proposed; not approved or executed.** This is one complete approval package for implementing and qualifying the delivery changes, then finishing engineering validation. Source and retained-record inspection informed it; the proposed transport has not been implemented or qualified. Independent review status is recorded at the end. Approval of this document would not establish runtime success or authorize a scientific study.

## Decision requested and retained result

Authorize the finite package below: at most two transport-qualification passes; one software qualification cycle plus one conditional, known-closed software repair cycle; the original single PR/main CI sequence, one candidate installation and one actual runtime/capture sequence; their named reviews and failure cleanup. Approve the explicit delivery-call limits, new T account and larger engineering artifact ceiling together. Routine source corrections before an unconsumed event remain inside these scopes; no piecemeal reapproval is needed unless a limit or scope changes.

The [cycle-6 result](D1_DISPATCH_RECORD_CONTINUATION_RESULT.md) remains failed or unknown. Its SSH connection ended during banner exchange; no original remote duration or usage was observed. The completed failure handoff does not establish zero remote work. Later successful reads and the observed high Mac load do not establish the earlier cause or prove a network repair.

Preserve B's **817.445086 CPU / 2213.1534917629324 wall** retained hold and E2's **48 / 144**. They include earlier failures once and are not measured whole-operation bills. E5 has already retained **4 / 10**, leaving **11 / 35** of its 15/45 ceiling; E7 has retained **3 / 10**, leaving **7 / 20**. No historical reservation is refunded, moved to T or relabelled known.

Source starts at [ae0eea284132c4ca67815b29ba4cadfc5a6d2891](https://github.com/spei04/strange-physics/commit/ae0eea284132c4ca67815b29ba4cadfc5a6d2891), tree 0b251cc063504992cffde4b7b68d94dc70064567. Reuse the two existing cloud checkouts and pinned independent environments. Preserve local computer-use work. No new VM, disk resize, service, queue, daemon, model-provider inference call or dependency upgrade is included.

## Source findings and implementation boundary

The current remote outer inherits SSH's stdin/stdout/stderr, waits for its child and sends its only terminal observation to SSH stderr. The local transport retains requests, operation IDs and original buffers in a volatile Map. The CI memory operator additionally depends on a vanished shared SSH master with ProxyCommand=false, and compares local connection elapsed time against remote 8/25/12-second review limits. These are concrete recoverability and timing-contract defects; none identifies the cause of the failed connection.

Implement a **durable foreground wrapper**, retaining the existing stage guards and clocks. It saves the original request, input, claim, streams and terminal evidence in private cloud storage before acknowledging completion. It does not promise survival of an SSH/session/host failure. A detached worker or service would need a separate lifecycle design and is excluded here. The objective is authentic recoverable evidence and at-most-once child launch, not a claim that connections cannot fail.

Platform owns the versioned transport, CI caller/counters and declarative operation/pool catalog. Lead owns versioned B/E2 wiring, source composition, admissions and execution. Platform also finishes C receiver ownership/census and the C-to-D startup adapter. Quality independently reviews exact source, contracts, fixtures and outcomes. No code is enabled from a placeholder or from this prose alone.

The immutable catalog fixes operation IDs, command templates, permitted field-derivation recipes, caps and predecessor requirements. Future accepted CI/run/candidate identities are not known at its initial seal. Before each operation reaches READY, its separate immutable manifest must bind every such field to authentic accepted predecessor evidence. No placeholder or later mutable lookup reaches execution. A changed derivation rule requires source review before any dependent event.

Every active consumer must use the same pinned pool/catalog version: B helpers, E2, CI collectors, C receiver/setup, D controller and E5–E7. Preserve old source and receipts. A single declarative data record is sufficient; no replacement orchestration framework is needed. Static checks must cover every caller, input schema, pool sum, namespace, predecessor join and possible failure closeout before the first qualification pass.

## Delivery, capture and recovery contract

Use the private cloud repair root's new transport subtree. Each finite operation ID binds an approved plan identity, exact source and environment identities, argv array, working directory, input length/hash, predecessor receipts, account, stage deadline, stream caps and allowed submission slots. No shell fragments, arbitrary commands or credential values may enter the catalog. File and directory custody remains owner-only, regular single-link/no-follow where required; reject path escape, symlinks at evidence boundaries and changed identities.

| State | Required action and permitted transition |
| --- | --- |
| STAGING | Write only one of two predeclared, exclusive upload paths. Bound and retain partial uploads. No workload may start. |
| READY | Verify complete input, manifest, hashes and custody; fsync files and directory. The complete request is immutable. An identical submission may reuse it; a different digest under the same ID is rejected. |
| CLAIMED | Exclusively create the operation's one claim; fsync both its file and containing directory before any child spawn. Record boot and owner start identity. Any existing or partial claim is consumed; it never permits respawn, even when no child was observed. |
| RUNNING | Launch the one catalog command under its existing guard, with stdin from the verified spool and stdout/stderr captured by the remote owner to bounded cloud files. Do not attach required original evidence to SSH file descriptors. |
| TERMINAL | Require original wait/EOF/descriptor observations, hash the original captured bytes, and persist the original terminal, accounting and closure facts. Fsync those files, an exclusive completion marker and their containing directory before acknowledgement. A partial terminal or marker is not success. |
| RECONCILE | At most two priced read-only queries may return this operation's original durable record. Never launch a child from a status query. Missing terminal, changed boot, lost owner, incomplete capture or exhausted reconciliation leaves unknown/full hold/stop; only named owned cleanup and closeout may follow. |

Operation IDs and transmission-attempt IDs are distinct. The cloud catalog contains the two immutable submission slots and two reconciliation slots for each operation; the caller Map is only a cache. The catalog seal reserves all maximum transmission slots/costs up front. Each received attempt journals its slot, request digest and supplied cumulative caller count before a stage effect. The caller also counts failed pre-handler connections; they are not made free by absence from the server journal. Persist complete counter checkpoints through the declared protocol operations or existing responses, never through an extra uncounted SSH handshake. A second send after caller loss requires the original durable count. If a transmission may have occurred and its count cannot be established, consume the remainder conservatively and stop; a new client or empty Map never resets an allowance.

There are at most **two same-ID submissions and two read-only reconciliations per catalog envelope**. These are newly proposed control-call allowances, not a relabelling of workload retries. A second submission may claim only when no prior claim exists and the identical complete request is verified atomically. A losing concurrent submitter returns status. Crash after claim but before a PID/terminal record does not establish zero work. An existing claim is never deleted, recycled or retried.

The prospective authoritative observation is the original cloud outer/capture record produced within that invocation. A lost acknowledgement may be resolved by retrieving that exact original record; it cannot be replaced with later process listings, reconstructed timestamps or a new execution. The historical cycle-6 record remains unknown. Unknown times are null with a reason. Local connection duration is stored separately and never substituted for remote duration.

Transport admission/staging/capture has its own bounded clock. Each inner command retains its catalog-sealed stage deadline and cleanup reserve: C/D/E are unchanged and the new B limits are explicit below. The wrapper cannot extend or restart them. Set each outer deadline before dispatch to the declared inner maximum plus bounded transport allowance. T records the full local submission round trip, including the stage wait; it never subtracts a remote duration from a local clock. Those wall scopes overlap and must not be added as measured spending or latency. Unknown remote usage remains null with the full affected reservations retained. Only the claim-owning submission may wait for a stage; duplicate submissions and reconciliation return bounded status/readback without starting a second stage-wait interval. Reserve final publication tails explicitly instead of claiming a final write measured itself.

CI's six collector calls use this protocol and actual remote stage elapsed time, preserving E3/E4 limits. Restore CI request/poll state from eight fixed cloud tickets: four tickets per run, each permitting at most 48 logical GETs and 15 poll rounds. Persist a ticket before use. The next already-declared ticket submission carries the preceding batch's counters and required original response bytes; its remote handler durably seals that batch before issuing the next ticket. The last batch, or an early-terminal batch with unused tickets, is carried by the existing terminal collector; the existing final collector closes its acceptance/accounting records. Each batch remains provisional until that exact original cloud acknowledgement. There is no separate update call and no mutation through reconciliation. All eight ticket inputs are bounded to16MiB and use the declared large-input exception. The16MiB bound applies to the complete encoded input, including counters, original responses and framing. Stop if that full input would exceed its input/output/body allowance; never truncate evidence or split it into an unlisted upload. A required original response lost before durable transfer is missing evidence and stops dependent work; it is never reconstructed by a new GET. A lost batch consumes its entire outstanding ticket without refund. Another ticket requires known closure of the prior local request owner and remaining original run budget; unknown ownership stops. Never resume an API loop from a reset in-memory counter.

Credentials use only an ephemeral private channel and are excluded from request/evidence files, argv, environment snapshots and logs. Authenticated GitHub responses establish provenance; a matching hash alone does not authenticate a response. Required initial/terminal identity data, complete original logs and artifacts are retained. Unchanged polling bodies need not be archived, but their counted request, status, length/hash and retention status must be recorded. A missing required original response is missing evidence; a later separately counted request is a new observation, not a reconstruction of it.

## Qualification and bounded software contingency

After approval, implement and independently seal the exact source and finite fixture recipe. No current production run or protocol is used as a rehearsal. T permits at most **two passes of these twelve fixed transport cases**, each bounded to 20 CPU / 300 wall seconds and at most four SSH calls, including setup, capture, verification and owned cleanup:

1. Healthy original input/stream/terminal capture and acknowledgement, exercising one full16MiB synthetic input slot per pass. Generate directly into the retained transport spool with bounded buffers; do not create another16MiB scratch copy. Use no real GitHub/provider data and no second healthy upload. Any bounded C header framing uses the metadata reservation.
2. Preclaim upload loss and the second predeclared submission path.
3. Concurrent identical submissions: one claim and at most one child.
4. Same ID with changed source/argv/input digest is rejected.
5. Lost acknowledgement with known transmission history, and caller reset after an acknowledged durable checkpoint: recover original bytes only. A reset with unknown wire-attempt count must stop, not invent available slots.
6. Failure after exclusive claim and before spawn, including failed claim write/close: retain a consumed/unknown claim.
7. Mid-child SSH disconnect: retain original closure evidence or explicit unknown; no relaunch. Admission requires the qualification harness's own fixture/process ownership to be reconciled.
8. Child deadline exhaustion without extending any original clock.
9. Stdout overflow: stop, retain prefix and overflow; never label it complete.
10. Stderr overflow with the same rule.
11. Terminal write/fsync failure, including simulated ENOSPC in owned fixtures: never publish success.
12. Stale boot/PID-start identity and nullable timing rejection/acceptance. Simulate identities; do not reboot or signal unrelated processes.

A second T pass is allowed only after a known-closed implementation failure, reconciled owned fixtures and independently reviewed scoped correction. An expected unknown fixture record is not permission to leave an actual owned process unresolved. Do not fill the real disk, terminate unrelated work, import project primitives or call protected services in these fixtures. Before pass2, Quality must accept the exact corrected source/recipe. Its remote staging, freeze and readback are charged within that pass's first case preparation and existing20/300/four-SSH allocation; they grant no fifth protocol operation. Both passes and every partial remain counted.

Keep three test sets distinct: the twelve transport cases per T pass; the existing **seven actual-function control-harness cases** per B rebind; and the project collection of **345 cases / 1035 phases** initially. The optional second B cycle may add at most eight focused regression node IDs across the package, for at most **353 / 1059**. Preserve all original 345 IDs and their relative order/meaningful assertions. Freeze the complete ordered census and source tree before each check; never adjust expected counts to conceal missing tests.

The second B cycle is permitted only after a typed **current-attempt eligibility proof** in its metered failure closeout: complete original source/input/outer/guard joins, known owned-child/EOF closure, current usage within limits and an ordinary captured format, lint, typing, collection/import or test-assertion failure. An unexpected source/census identity mismatch, authority/guard violation, transport ambiguity, missing original capture, timeout, CPU/output limit, or unknown ownership is ineligible. Historical usage may remain unknown; handoff_complete alone is not this proof. A scoped correction and independent source review then precede the one new immutable freeze. Eligible application edits are limited to scripts/d1_bootstrap_control.py, scripts/d1_owned_capture.py, scripts/d1_capture_owner.py, scripts/d1_capture_descendant.py, scripts/d1_runtime_inventory.py, tests/d1_bootstrap.py, tests/d1_originals.py and the seven existing test targets: test_d1_originals.py, test_d1_bootstrap_control.py, test_d1_bootstrap.py, test_d1_owned_capture.py, test_d1_capture_owner.py, test_d1_capture_descendant.py and test_d1_runtime_inventory.py. Preserve the approved two-alias policy; no broader native/frozen allowlist or change to physics, fitting, calibration or scientific behavior. No third B cycle, broader target, dependency change or reduced assertion is authorized.

## Finite operation catalog and exit gates

This catalog contains **52 logical envelopes**. Skipped stages stay unrun; do not charge a skipped E2 slot or assume a fixed opening after an early failure. IDs include this continuation identity, cycle/run and stage; no cycle-6 claim or phase ID is reused. Each real receipt is appended once. Expected predecessor sets derive from the enumerated branch actually taken, not an invented receipt or unconditional preparation-count increment.

| Group and fixed envelopes | Count | Limit and acceptance |
| --- | ---: | --- |
| B1 and optional B2: freeze/rebind; control review; prepare; postcollection; check; outcome review; terminal handoff | 14 | Per-cycle B table below; E2 actual consumed slots. Current source/environment, all historical records and seven harness cases must join. Prepare executes no bodies; check requires full typing and exact ordered passing phases. |
| Original PR and protected-main collectors: initial; terminal; final | 6 | Each run E3/E4 15/45 split 3/8, 8/25, 4/12. One original CI attempt per run, complete logs and exact tested/source/candidate identities. |
| Four durable request/poll tickets for each CI run | 8 | T-only control records; four 48-GET/15-poll tickets per run, each with a16MiB sealed input for the preceding batch; no extra review or job. |
| C: prepare-export; export; prepare-receive; receive; verify; setup | 6 | Both preparations share original 5/15. Export20/60, receive5/30, verify30/90, setup90/255; total150/450. |
| D: native closure; materialization; startup; three-probe group; live-descendant witness; capture; failure cleanup/retention | 7 | Original D partition below; cleanup is not another normal stage or capture. |
| E5: C controls; candidate acceptance; setup outcome; native closure outcome | 4 | Remaining11/35 split 2/5, 3/10, 3/10, 3/10. Preserve earlier4/10. |
| E6: materialization; startup; probes; witness; capture; cleanup review | 6 | 15/45 split 2/6, 2/6, 2/6, 2/6, 4/12, 3/9. |
| E7: final reconciliation/publication record | 1 | Remaining7/20; earlier3/10 retained. |
| **Total** | **52** | Source/argv/input/output bindings are sealed before each actual dependent event. |

Each B cycle reserves **300 CPU / 900 active-wall seconds**: source correction/format/freeze and seven-case rebind75/225; preparation35/120; postcollection10/30; full check180/525. Each of these four envelopes includes its own preparation, verification and owned closure. There is no additional unnamed B cleanup invocation. Transport-owned capture is charged to T without adding stage CPU twice. E2 separately provides control4/12, outcome4/12 and one success/failure handoff2/6 per cycle. A first-pass success skips B2. Failure uses only the actually reached reviews and handoff; the next cycle's E2 opening comes from original receipts.

Only accepted B outcome and handoff permit the **one original PR CI sequence (83 configured job-minutes)**, followed by normal protected-main integration and **one original main sequence (98)**. No workflow dispatch/rerun, head churn, check bypass, extra PR or second candidate run. Source/base conflict stops before another CI attempt. Future main/tree/run/artifact identities come from the actual accepted predecessors; no placeholder is an admission. Ordinary CI's existing numerical tests are retained but are not the scientific D1 study.

The dependency order is explicit: accepted B outcome/handoff → original PR/E3 acceptance → protected main/E4 acceptance → E5 C-controls acceptance → C prepare-export/export/prepare-receive/receive/verify → E5 candidate acceptance → C setup → E5 setup acceptance → D native closure → E5 native acceptance → D materialization/E6 acceptance → D startup/E6 acceptance → D probes/E6 acceptance → D witness/E6 acceptance → D capture/E6 acceptance → E7 final reconciliation. Each CI retrieval ticket follows the run identity and previous-ticket closure it requires. Named failure cleanup and its E6 review replace the remaining normal path when needed; E7 records failed, unknown and unrun stages. No stage consumes a future acceptance or invents a predecessor receipt.

C receiver changes are part of implementation: set claim ownership immediately after successful O_EXCL creation, before write/close; keep the claim on later failure; use the current no-follow whole-package census with only its existing permitted fixture FIFOs. Preserve the header/ZIP receipt contract. The16MiB input allowance bounds ZIP bytes; each of the two receiver submission slots also has a header bounded to64KiB within the16MiB transport metadata reservation. Seal the exact combined header-plus-ZIP stream length/hash. Stage the single authenticated ZIP in the durable transport spool, then stream its header and ZIP into the one bounded C receiver without a third spool ZIP copy; it verifies/copies the candidate into its original location. Preserve GitHub-reported digest separately from observed stream/cloud hashes; verify all five candidate files, source export, lock, runtime requirements and installation. The setup envelope constructs its actual setup admission from accepted verifier evidence after the E5 candidate gate, before installation, inside its existing90/255 allocation. This is not a third preparation event. No Mac artifact file, second installation or old-Q identity substitution.

Construct D's startup observation from accepted C facts, inside the original D-native preparation: python_version, executable, prefix, startup_sys_path, frozen_modules and builtin_modules from actual metadata; startup_hook_files and absent_startup_paths from actual final-startup evidence. The latter are unique path-string lists, at most1024 items and4096 characters/item, matching [the existing validator](https://github.com/spei04/strange-physics/blob/ae0eea284132c4ca67815b29ba4cadfc5a6d2891/scripts/d1_bootstrap_control.py#L374). Verify exact hook membership and actual absent paths; do not copy historical values or insert another startup probe.

D remains native100/150; materialization25/60; startup20/45; fixed benign probes15/45; witness80/90; capture200/330; additional failure cleanup60/180 = **500/900**. Preserve the fixed capture's300-second outer limit and150CPU service reservation. Original owner/service identity, quota/burst, child closure and cleanup evidence must join. Failure stops dependent stages; only named owned cleanup and review follow. Do not repeat capture or treat setup/probes as capture qualification.

## Complete command, delivery and calendar allowances

All figures are prospective allocation ceilings, not measured costs or cloud prices. A and completed historical work are not rerun.

| Account | Current ceiling | Proposed ceiling | Increase |
| --- | --- | --- | --- |
| A | 40 CPU /120 wall | unchanged | 0 |
| B | 825/2475 | **1425/4275** | 600/1800 |
| C | 150/450 | unchanged | 0 |
| D | 500/900 | unchanged | 0 |
| E2 within E | 56/168 | **68/204** | 12/36 |
| All E | 136/408 | **148/444** | 12/36 |
| New T: protocol qualification, transport and mechanical administration | none | **4200/72000** | 4200/72000 |
| **Complete package, including retained ceilings** | **1651/4353** | **6463/78189** | **4812/73836** |

After two full new B holds, retained B would be1417.445086/4013.1534917629324, within1425/4275. New E2 work is at most20/60 from the actual48/144 opening. A skipped contingency is unused allocation; it never refunds old holds or permits another action.

T's exact maxima are deliberately generous for the full path, not another set of tiny repair budgets:

| Named T work | Maximum | CPU | Wall seconds |
| --- | ---: | ---: | ---: |
| Submissions | 104 ×10CPU/(45connect+120non-stage wall) |1040|17160|
| Read-only reconciliations |104 ×5/(45+30)|520|7800|
| CI logical GETs |384 ×5/60|1920|23040|
| Candidate ZIP logical GET |1 ×5/60|5|60|
| Poll waits |120 ×60 seconds|0 structural CPU for the wait itself|7200|
| Transport qualification |24 cases ×20/300; each includes at most4 SSH calls|480|7200|
| Protocol preparations/finalization |4 ×20/120|80|480|
| Git/GitHub delivery/publication actions |6 ×5/60|30|360|
| Nested stage wait, once per claim-owning submission | B1800+E260+C450+D900+E3/E490+E535+E645+E720 |0 additional stage CPU|3400|
| **Named sum** | |**4075**|**66700**|
| **Reserved contingency; no additional calls or attempts** | |**125**|**5300**|
| **T ceiling** | |**4200**|**72000**|

The four protocol operations are catalog/source seal, transport qualification freeze, CI/candidate delivery seal, and final transport evidence/counter reconciliation. The six Git actions are qualified-branch push, one PR creation, one protected merge, fetch accepted main objects, final documentation commit and its push. Unknown PR/merge outcomes may be reconciled only by counted reads, never by replaying the mutation. The maximum is **314 SSH calls**:208 submission/reconciliation,96 qualification,4 protocol and6 Git. Library retries and connection fan-out are disabled.

The **385 logical HTTP GETs** cover only the ticketed CI/candidate retrieval surface, including the single candidate ZIP. Each permits at most three HTTPS hops sharing its one60-second deadline and body cap: at most1155 hops on that surface. The six named Git/GitHub commands may perform their own internal refs, discovery and authentication reads; SSH/IAP may also authenticate. Those requests are outside the ticketed GET count, remain inside their named action/connection deadlines and CPU reservations, and do not authorize additional application-data retrieval, mutation replay or hidden retries. This is not a ceiling on all network packets or provider-side authentication requests. Count redirect hops and pagination explicitly; each new page is a new logical GET. Never forward credentials across an origin change. Freeze allowed authenticated GitHub/artifact redirect handling before qualification; unexpected origins stop. No hidden retry loop may spend another request. Poll waits count toward T wall and the calendar clock. Model-provider inference and scientific-run requests remain excluded; the one engineering D runtime and the specified GitHub operations are included.

CPU attribution separates local caller/SSH/IAP and HTTP helper CPU, remote wrapper SELF/non-stage helpers, synthetic fault children, and the existing B/C/D/E stage/process/service scopes. Count each measured scope once; do not add waited-child stage CPU to T again. Missing process-tree coverage stays unknown with its reservation retained. Mechanical overhead must be instrumented and checked during qualification; these allocations are not a kernel-wide CPU bound or proof of complete provider billing. Human/model reasoning and external authoring remain separately unmeasured; do not call them zero or transfer historical unknown work into T.

Set a **24-hour original calendar window** from the first qualification dispatch through final closeout. Its clock includes polling, queues and operator pauses; it does not reset on reconnect or the second pass/cycle. The181 configured CI job-minutes are a separate hosted limit, not measured CPU or an additive estimate of elapsed latency. Before each launch, require the full stage maximum, remaining downstream requirement and owned cleanup reserve to fit its account and the remaining calendar window. T already reserves the full nested stage wait once; it does not subtract either known or unknown remote time from local observations. The sum of account ceilings includes overlapping wall scopes and historical holds, so it is not measured whole-operation elapsed time. Expiration stops new normal dispatch, while already-owned cleanup retains its original reserved deadline; no work is abandoned to satisfy the calendar label.

## Output, transient storage and independent study gates

Request an **engineering-only global retained-output ceiling of2048MiB**, replacing this repair package's1024MiB. Preserve all existing data and count every partial, input, original stream, capture copy, receipt and source. This is a proposed increase, not current authority and not a scientific storage amendment.

| Pool | Proposed MiB | Change |
| --- | ---: | --- |
| Installation |512|unchanged|
| Temporary |128|unchanged|
| Candidate |48|unchanged|
| Source/controls |32|unchanged|
| Software |64|was32|
| PR CI |12|unchanged|
| Main CI |12|unchanged|
| Runtime evidence |32|unchanged|
| Review |8|unchanged|
| Failure retention |208|unchanged|
| New durable transport |992|new|
| **Total** |**2048**|**+1024**|

Software retains2,194,225 bytes and reserves at most30MiB for each new cycle:65,108,785 bytes total, below67,108,864. This preserves both cycles' original fixtures/failures without relying on deleting the first cycle to admit the second. Exact per-file/entry/source-map/JUnit limits must fit that reservation; assertions and complete-output requirements are not weakened.

Transport's conservative complete reservation is **961.25MiB**: fourteen CI collector/ticket envelopes ×two16MiB inputs =448MiB; one C receiver ×two16MiB =32MiB; other37 envelopes ×two128KiB =9.25MiB; all52 production original stdout/stderr pairs ×(4+1)MiB =260MiB;24 qualification cases ×5MiB streams plus22 cases ×2MiB inputs and2 healthy cases ×one16MiB input =196MiB; metadata/catalog/partial-management, including the two64KiB receiver headers and bounded synthetic header framing, =16MiB. Failed upload bytes are inside their two input slots, not an uncounted third copy. Existing CI outputs are bounded to16KiB and fit the conservative4MiB limit. Do not retain duplicate copies on read-only reconciliation. This leaves30.75MiB of transport headroom, which grants no additional operations.

Use at most16MiB of live transport fixture scratch within the existing128MiB temporary pool, sequentially with other stages; keep required original outputs in their retained pool. Bound streaming buffers; do not hold whole candidate/log trees in unbounded memory. New source/control additions are at most4MiB after an exact post-cycle6 baseline, within the32MiB pool. Preserve the prior1,438,717-byte addition and every original row; no allowance resets. Freeze original-row prefixes, new classified paths, at most512 external rows and actual complete inputs at most131072 bytes for ordinary stages; CI and candidate payload exceptions are exactly those listed above. An artifact's existence or content hash does not itself grant execution authority.

Before any write/dispatch, the actual full no-follow census, all remaining retained-write forecasts, active temporary peak and other owners' outstanding reservations must fit the applicable pools and actual available space. Existing point observations are not admission; other-owner/transient demand is unknown until reconciled, not zero. Record logical/allocated sizes and filesystem availability; pool limits are not a universal OS physical-peak quota. Do not delete retained evidence or active consumers to force a fit.

The **scientific1GiB cap**, **50GiB start /45GiB stop-new-dispatch reserve**, exposure rules, independent evaluation owner, numerical adequacy and study approval remain separate and unchanged. The previously noted1168MiB study publication floor is not solved by this engineering allowance. This proposal grants no maintenance window, disk resize, held-out evaluation, D1 comparison or enterprise-readiness claim.

## Source and evidence anchors

Private basenames below resolve under the existing cloud evidence/runtime roots; raw evidence remains private. Public source links identify inspected code, not unimplemented successor behavior.

| Anchor | Exact identity |
| --- | --- |
| Prior proposal and immutable results | [cycle-6 decision](D1_DISPATCH_RECORD_CONTINUATION_DECISION.md), [result](D1_DISPATCH_RECORD_CONTINUATION_RESULT.md), [original full repair plan](D1_RUNTIME_REPAIR_PLAN.md) |
| Original remote outer | repair-b-cycle4-lead-transport-v1.py;2283B;ce64bfa670892462315b7cf1caf3d7d42d1761dc715148f9b2b30b0b0dc6c3a3 |
| Original local transport | repair-b-cycle4-lead-transport-v2.js;5833B;a6667947919bafeb2437018a18211e785364a41a96bae36a028504530e326489 |
| Existing CI memory operator | repair-ci-mac-memory-operator-v1-draft.mjs;24342B;89564cd41bf55cc02d9b89985b4855b957e27351ae5d5af1fa891cc0fda82330 |
| C v2 recipe | repair-c-v2-recipe.json;17722B;a86d5fe2f04354461165fea5739ff2a9db7fbbd4f7c1a0a5157f12f42b002870 |
| E5 original cumulative receipt | E5-correction-receipt.json;915B;c769d930a575784062b6b78a63a786955a24d161a25f9921419107d557dbfc85;retained4/10 |
| E7 original retained result | E7-repair-stop-result.json;2906B;b8586716e965b29570b0386e996cd0e09a3c825ca1578a4dee3d24a02fc463ff;retained3/10 |
| Failed transport evidence | repair-cycle6-original-transport-observation-20261104.json;3473B;dac39010d9119f2923d317cd2781de59506331541db1552856a59cdbc3aae010 |
| Completed closeout original evidence | repair-cycle6-closeout-original-execution-record-20261104.json;4658B;162ccb508249ee85faa97935099809274d007392d488b89bdb75e158f1fab827 |
| Current stopped index | cycle6-software-index.json;4451B;d2d1b1e9de9791dbaa7d9f16659d58a00e741db78dbd24fad35e2ee65b42e899 |
| Existing startup materialization | [materializer](https://github.com/spei04/strange-physics/blob/ae0eea284132c4ca67815b29ba4cadfc5a6d2891/scripts/d1_runtime_inventory.py), [validator](https://github.com/spei04/strange-physics/blob/ae0eea284132c4ca67815b29ba4cadfc5a6d2891/scripts/d1_bootstrap_control.py) |

## Final acceptance and review status

Success requires exact accepted source, full original PR/main logs, authentic candidate/source/install joins, every required runtime receipt, the one capture's qualified result, owned closure, reconciled counter/output inventories and independent final evidence acceptance. Report pass, fail, unknown and unrun stages separately. A source review, fixture pass, successful SSH read, later missing process or written plan cannot substitute for those results.

A failed or unknown production event stops dependent work except the expressly eligible second B cycle or named owned cleanup/closeout. No automatic stage replay, third qualification/B pass, second CI sequence, installation or capture exists. If the finite package cannot be completed, preserve the result and prepare a new decision rather than expanding limits during execution.

**Independent planning review: accepted 2026-11-04 Pacific.** Platform reviewed the complete35,062-byte decision, SHA-256 `025f1bea8cd3597a65c01cb71616d09ca4d37653a3cf1d8f7199cb9735f95791`. Quality reviewed the complete34,682-byte predecessor, SHA-256 `f8e9f1e0e310624f9761695a72f3c1b22673b508320072035cbe9ea368c76bde`, and accepted the sole subsequent amendment: the streamed16MiB healthy input slot per pass and its28MiB storage adjustment. Platform verified that amendment in the final file. This publication changes only the review verdict from that reviewed text.

The reviews resolved directory-fsync, setup-admission placement, header framing, future identity bindings, stage order, ticket response persistence, HTTP-count scope and full-size input coverage. Both accepted the finite arithmetic and remaining failure limitations. This is approval-ready planning, not source qualification, runtime success or execution authority. No new tests, probes, validation, CI or paid execution were performed to prepare it.
