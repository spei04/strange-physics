# D1 test-boundary correction and validation continuation

**Proposed; owner approval is required before applying the patch or executing another software phase.** This decision covers the reviewed test-only correction and one bounded validation cycle. Successful validation can then resume the original approved PR, protected-main CI, installation and runtime gates. It does not add a scientific run.

## Actual result and cause

The approved correction at `17ab2b2cd5cbb8f076f49826300dfc96b476f1dd` was executed. Corrected source freeze, independent control review and collection passed on `de464a1719c2e68f7773d7e04cdef0a8b9be5d51`. Check 7 passed formatting, lint and typing across 236 source files. Its guarded tests recorded **344 passed and one failed**, with all 345 setup and teardown phases passing. The 1,035 phase rows contain one failed call; no forbidden attempt or oracle poison was recorded. Source and environment identities matched before and after both software phases.

The failure is `tests/test_d1_capture_owner.py::test_reaped_controller_rejoins_live_before_cleared_terminal[failed-child]`. Its assertion checks the entire shared event history. The fixture first runs a successful synthetic controller, which reads `capture-service.json`, then rewrites the retained receipts into a failed-child scenario. The parent resumes afterward. The parent's report join is already conditional on a successful child and no prior fault. The assertion therefore includes a fixture read from before the behavior it intends to test.

Platform and Quality independently traced this sequence through the immutable source; Lead also reviewed it. This is a source-based causal explanation supported by the original failure, not a new executed reproduction. Production code does not need a change for this assertion.

The final diagnostic review passed once. Its proof is 389,735 bytes, SHA-256 `bf5541be4edc67cb79ee1af1ec1a26399bfd2406233b1bc55835836518206b60`; receipt: 1,062 bytes, `b2749903115188ea722c074e7061126c37906a1afd55baef74236776e3c3cd11`. Failure-only handoff also passed once, retaining the failed outcome and creating no admission. Its 2,232-byte receipt is `ed1ea85e2cdbb51d15d68a1b3dd3bed9e5c8f335a2b0e92b6ea8f5492cc045e5`. The 4,813-byte software index is `eb522b9cb86333f05e4e4ab78ee98eae560542aa49c9aad2eec68455c4b5499c`. Full logs, collector receipt and JUnit remain private.

## Exact proposed correction

Change only `tests/test_d1_capture_owner.py`. Record one explicit boundary immediately before the fixture controller returns. Require the fixture prefix to contain its service read. Require the failed-parent suffix to contain no service read and the successful-parent suffix to contain one. Preserve the full event history and every existing result, ownership, identity, CPU, cleanup and first-fault assertion.

Original: 21,417 bytes, SHA-256 `ded18accff95536292dc4d742f19350b9191026e8d3a3c15c417b66e7ad16e03`, Git blob `28ff382af466ffa231e09e5fbc95bfe69d945a5f`.
Proposed: 21,893 bytes, SHA-256 `f994306e3852f85ca38a21b23f2ddc438a9f48ce06df653193d1fdf7f76afc3d`.
Patch: 1,795 bytes, SHA-256 `52a02f02be4cf88faeb96aec1be2d57c3907ea186c500bf191cf2291cb978512`.

The patch has independent static acceptance and an exact reverse comparison to the original bytes. It changes no imports, test IDs, decorators, parameters or case counts. It has not been applied or tested. The complete diff follows.

```diff
--- a/tests/test_d1_capture_owner.py
+++ b/tests/test_d1_capture_owner.py
@@ -371,6 +371,8 @@
             del current["ObservedCPUMaxBurst"]
             current["CPUUsageNSec"] = "350"
             manager.queue.append(Snapshot(current, None))
+        # Keep fixture controller reads separate from the parent that resumes next.
+        records.events.append("fixture-controller-return")
         return child
 
     monkeypatch.setattr(start, "start", completed)
@@ -385,6 +387,10 @@
     item, _, records, start, manager = values
     retained_terminal_start(values, monkeypatch, failed=failed)
     result = watch(values)
+    assert records.events.count("fixture-controller-return") == 1
+    controller_return = records.events.index("fixture-controller-return")
+    assert "read:capture-service.json" in records.events[:controller_return]
+    owner_events = records.events[controller_return + 1 :]
     assert result["status"] == ("incomplete" if failed else "provisional_complete"), result
     assert result["accepted"] is False and result["named_ownership_released"] is False
     assert result["child_reaped"] is True and result["child_code"] == (1 if failed else 0)
@@ -397,12 +403,13 @@
     if failed:
         assert first(result)["detail"] == "Owned controller returned a failure"
         assert result["supplemental"] == []
-        assert "read:capture-service.json" not in records.events
+        assert "read:capture-service.json" not in owner_events
         saved = records.records["capture-owner-terminal.json"]["snapshot"]
         assert type(saved) is dict
         assert "ObservedCPUMax" not in saved["properties"]
     else:
         assert result["first_fault"] is None
+        assert "read:capture-service.json" in owner_events
 
 
 @pytest.mark.parametrize(
```

## Authorized sequence requested

| Step | CPU seconds | Active-wall seconds | Required result |
| --- | ---: | ---: | --- |
| Apply, review-bound source freeze and control preparation | 10 | 30 | Exact old/new test bytes, only one changed path, clean commit/tree, complete source/environment identity and retained failure joins |
| Phase 8: guarded preparation | 25 | 100 | Both sentinel denials and source-bound collection of the same 345 cases; no test bodies during collection |
| Postcollection admission | 5 | 15 | Actual successful phase 8 outcome, complete collection and preserved prior charges |
| Phase 9: checks | 180 | 500 | Formatting check, lint, full typing and all 345 guarded tests / 1,035 passed phases |
| **Stage envelopes** | **220** | **645** | All control and closeout work included |
| **Cycle 4 ceiling** | **220** | **660** | The extra 15 wall seconds is contingency, not another invocation |

The aggregate B ceiling remains **400 CPU / 1,200 active-wall seconds**. B already retains **147.445086 / 203.1534917629324**. Reserving the full new cycle produces **367.445086 / 863.1534917629324**, within that aggregate. No earlier failure, reservation or charge is refunded.

The preparation children retain their existing limits: Python sentinel 2/10, retained-C sentinel 2/10, collection 15/60. Check children retain formatting check 5/20, lint 5/20, typing 60/120 and guarded tests 90/240. Parent identity checks and closure fit inside the larger phase envelopes above. No formatter write or import-fix pass is requested.

The existing runner assumes a successful same-cycle formatter before preparation. The cycle-4 successor must explicitly replace that prerequisite with the counted apply/freeze receipt, exact reviewed patch, clean source identity and source map. It must not invent a formatter outcome. Historical format outcomes and all failed attempts remain immutable. Check 9 still requires the actual phase-8 collection. This is a required control change, not a literal cycle-number substitution.

E2 is closed at **38/114**. Request **+10 CPU / +30 wall**: copied-control review 4/12, outcome review 4/12 and handoff 2/6. E2 becomes **48/144**; all review accounts become **128/384**; the complete package becomes **1,218 CPU / 3,054 active-wall seconds**. These are allocations, not measured bills.

Source controls must be prepared and independently reviewed before their first invocation. Lead remains the sole executor. Their review is an execution prerequisite within this package, not permission to widen its scope. Actual source, approval and output pins must be sealed prospectively.

## Output and custody

Keep the software pool at 32 MiB, reviews at 8 MiB and the global new-artifact limit at 1 GiB. Retain the existing cloud checkout and its owned environment. Do not delete failed outputs to make space.

The following conservative software forecast retains the actual 1,761,294-byte census plus the entire 196,608-byte handoff allowance, although its three actual outputs are smaller.

| Category | Maximum bytes |
| --- | ---: |
| Retained software and handoff allowance | 1,957,902 |
| New fixture allowance | 8,388,608 |
| Seven logs at 256 KiB each | 1,835,008 |
| Sentinel tripwire/continued leaves | 16,384 |
| Collection manifest and two collector receipts | 3,145,728 |
| JUnit including partial output | 2,097,152 |
| Two phase-parent receipts | 4,194,304 |
| Two preparation receipts | 1,048,576 |
| Fixed metadata allowance | 2,359,296 |
| Three source maps | 196,608 |
| New helper pair | 131,072 |
| Framework/failure closeout | 2,097,152 |
| **Total** | **27,467,790** |
| **Headroom within 33,554,432** | **6,086,642** |

The fixed manifest must enumerate initial preparation, phase-8, postcollection, phase-9 and final handoff leaves before activation. Use exclusive new names. Admit only two software phases and two preparation events; optional failure records cannot become extra attempts. New maps cover the initial source and after phases 8/9. Full source and environment checks remain required.

The accepted diagnostic reader's preflight and actual output sizes bound retained reviews, including handoff, at **4,451,570 bytes**. The next control review reserves 417,792 bytes; outcome review 2,252,800; handoff 73,728. The resulting **7,195,890-byte** review bound leaves **1,192,718 bytes** within 8 MiB.

The future outcome review reserves 2 MiB for its proof, while the serialized summary itself must fit within 1 MiB. It validates the complete original collector, JUnit and log bytes, and records their exact references, counts and joins in that summary. Complete raw stage logs are returned within the original timed stdout for Lead's semantic review, without requiring another stored copy of every original in the review proof. Seven separately base64-encoded 256 KiB logs require at most 2,446,696 bytes. Together with the 1 MiB summary, this leaves 699,032 bytes for the fixed JSON envelope inside the 4 MiB stdout cap. Seal the complete serialization calculation before activation. No truncation may be accepted as complete evidence. Partial and failed files count in their pools. Fresh software, review and global reservation checks must pass before dependent execution.

## Exit gates and stopping rules

- The exact test-only patch and versioned control sources must pass independent review. Only the reviewed test file may change.
- Validate actual outer exit, complete stdout, source/environment identity, known child closure and every cumulative charge. An admission file alone does not permit continuation.
- All 345 existing cases must pass with 1,035 ordered, non-xfail phases; no skips, errors, forbidden operations or oracle poisons. Preserve the two sentinel checks and all existing guard bindings.
- A failed or unknown executed preparation, phase, review or handoff stops dependent work. Only its already-budgeted failure closeout may follow. There is no replay, fifth cycle or phase beyond 9.
- Only successful B acceptance permits the original single PR workflow, protected-main integration and original main workflow, followed by the existing candidate-installation and runtime sequence. Their limits remain 83 + 98 configured CI job-minutes, C 150/450 and D 500/900, with one installation and one capture.
- No additional CI run, scientific evaluation, capacity purchase, deployment or release is included.

The previous approved decision explicitly says “no fourth cycle” and “no phase beyond 7.” This proposal changes those two limits for the specified correction and adds the named review allowance. Unused aggregate budget is not treated as approval.

Source authoring, static reviews, external transport and administration remain separately unmeasured. A separate portfolio review supplied diagnostic leads; its work is not claimed as part of the accounted E2 measurement. Preserve unique evidence and unfinished work; review reproducible diagnostics on 2026-12-01 after checking consumers.

## Decision

Approve this test-only correction, the one cycle and E2 allowance above, and the unchanged downstream sequence conditional on every gate passing. The prospective patch is independently reviewed; the new control sources and actual pins remain execution prerequisites. Until approval, keep the current failed outcome and do not apply the patch or start phase 8.
