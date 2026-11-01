# Cycle 3 source-freeze correction amendment

**Status: reviewed proposal awaiting owner approval. The correction is disabled and unexecuted.** This amendment completes the already approved third cycle by adding one preparation event and two bounded reviews. It does not repeat the original continuation approval.

## What happened and the approved instruction

The approved continuation decision at commit `57ca958b275376bdf3182acc1024c6a99b4d6ae3`, `docs/research/D1_RUNTIME_REPAIR_CONTINUATION_DECISION.md` (17,639 bytes; SHA-256 `0897608bc45a1463115a32a72c41c691d4cecfd3cf5bc20a944578acf63206be`), says:

> 3. Review and commit any formatting change, freeze the clean commit/tree and
>    full source map, then admit source-bound preparation. Never treat a
>    pre-commit collection as evidence for a different commit.

It also says:

> A failed phase consumes the proposed cycle and stops downstream work, with only its bounded cleanup and evidence retention allowed.

Software phase 5, the formatter, passed with known closure. Its receipt is 11,286 bytes, SHA-256 `5fd142f8856debacc3566bf437886194f393336485e5952b11f911eec7a29215`; observed outer elapsed time was 6.410000666015549 seconds. Its charged cost was 7.477703 CPU seconds and 10.804920787923038 wall seconds.

The subsequent source-freeze preparation incorrectly required the formatter to leave all source bytes unchanged. That contradicted the quoted review-and-commit path. The source-map digest changed from `db40b67b2bd874a783048e2df20abb1065e5bbeb0fc84c10d154255502be1475` to `16fdf01aa93a39cd6c5d45729da32a950a615a7ddc97da45fff8b23214027dc1`. The preparation stopped with an AssertionError before Git dispatch; it was known closed and wrote no next-phase admission. Its retained receipt is 2,724 bytes, SHA-256 `ddd7a98b864f1aa80fd71aa565f79357cf6b61eefef0d731faa61d93ef4f987e`.

The completed independent diagnosis found exactly one formatting-only change in `tests/d1_bootstrap.py`: a parenthesized conditional expression collapsed from three lines to one. The resulting file is 27,739 bytes, SHA-256 `23c155779dde7645445e99ea6a31c17455161f52f539ca2b2e746baf46f09888`. Lead verified identical Python syntax trees against the public 4d83811 source without executing it; Quality accepted the exact delta. All other 436 source-map entries are unchanged. The correction must commit this exact file content; no further source edit or formatter run is included.

This was an implementation and review error in the preparation operator, not a failed formatter phase. It does not establish that the whole software cycle failed. However, the approved inventory allowed only three preparation receipts/starts. Keeping the failed preparation and completing the intended path requires a fourth preparation event. Unused CPU or output headroom alone does not authorize that extra event. All original records and charges remain; no replay, replacement, refund, or account reset is proposed.

## One complete remaining software path

1. Independently review a corrected, versioned source-freeze operator and the minimal versioned runner change needed to retain and join the known failed preparation. The collector requires a literal-only helper-filename successor to join that runner. Preserve all collector logic, scientific denials, target selection, phase limits, and the exact process-guard bytes.
2. Execute the corrected freeze once, with a 10 CPU-second / 30 wall-second ceiling inside the existing cycle's 200/600 and aggregate B 400/1200 limits. Verify the actual successful format5 outcome, retained failed preparation, original approvals, source-map identity, and changed-path inventory. Commit only the independently reviewed `tests/d1_bootstrap.py` content pinned above. Verify that reversing the exact line collapse recovers its original SHA-256 `7a8f8bd7da492dda687019d026b282a226fcad90a2b7b7de8eafa3576c877f8b`. Freeze the resulting clean commit/tree and reuse the after-format source map. No fifth map copy.
3. Admit only phase 6 source-bound preparation, then the existing post-collection outcome/admission binder, then phase 7 checks. There is no repeated formatter, no additional collection attempt, no fourth cycle, and no phase beyond 7. Exact 345 cases / 1,035 prospective phases remain; successful collection alone is not successful regression execution.
4. Stop downstream work on a failed software phase, unresolved preparation failure, missing external outcome, unknown cost/closure, or exhausted reservation. Preserve partial files and failed charges; only the already bounded cleanup and evidence closeout may follow.

The fourth preparation is the corrected freeze: the complete inventory becomes initial preparation, failed original freeze, corrected freeze, and post-collection admission. The corrected freeze's 10/30 includes its activation, source/control and historical-record checks, bounded Git work, commit/freeze, admission creation, final output, and closeout. No additional B allocation or transfer from a closed account is proposed. Root remains sole executor. Actual control pins, exact outer outcome inputs, and the final source identity must be sealed after source review; this draft provides no runnable admission.

## Review allowance and unchanged downstream sequence

The existing 4 CPU / 12 wall failure review completed once: exit 0, 0.6669587920187041 observed outer seconds, no reader failure. Its 53,186-byte proof has SHA-256 `1695e3843effe944b6df2d80a59d907111d885711d75421694a06bc24bb82317`; its 1,052-byte receipt has SHA-256 `15635259c84d2bf58cba59cc79b50423ad5451f65d8c334ff9c7fe95e0c23f0c`. E2 now retains 28 CPU / 84 wall, leaving the existing 2/6 handoff reserve. B retains 88.53152 CPU / 131.49357407726347 wall, including this cycle's 11.882541 / 21.376798707060516. The failed freeze retains 2.069936 / 5.048387152142823; none of these charges is refunded.

Propose E2 +8 CPU / +24 wall: one corrected-control review at 4/12 and one final-outcome review at 4/12, retaining the existing 2/6 handoff reserve. E2's proposed cap becomes 38/114; all named review accounts together become 118/354; the whole package becomes 1,208 CPU seconds / 3,024 active wall seconds. These are ceilings and reservations, not measurements. Every new admission must join that exact retained failure and the accepted outcome proof.

Everything else stays as approved: B 400/1200 aggregate and 200/600 for this cycle; one original PR workflow at 83 configured job-minutes and one original protected-main workflow at 98, with no rerun or head churn; C acquisition/setup 150/450; D runtime qualification 500/900 with its existing stage and failure-closeout partitions; E7's retained 3/10 and remaining 7/20; existing source, runtime, candidate, installation, temporary, review, and global 1 GiB output partitions. CI job-minutes are not measured CPU or provider dollars. Source authoring and external transport/admin costs remain separately unmeasured. No scientific, capacity-purchase, deployment, or release authority is added.

## Complete software output reservation

All retained files, partial writes, hardlink names, and failed outcomes count. No deletion is assumed. Writers must enforce these prospective maxima before writing and fail without truncating evidence into a passing result.

| Category | Maximum bytes |
| --- | ---: |
| Already retained software output | 721,512 |
| Fixtures, including retained special entries | 8,388,608 |
| Nine command logs, each at most 256 KiB | 2,359,296 |
| Four sentinel tripwire/continued leaves | 16,384 |
| Collection manifest, collection receipt, test receipt: 1 MiB each | 3,145,728 |
| JUnit, including partial output | 2,097,152 |
| Three phase-parent receipts: 2 MiB each | 6,291,456 |
| Four preparation receipts: 512 KiB each | 2,097,152 |
| Other metadata: 39 fixed leaves, 2.25 MiB aggregate | 2,359,296 |
| Four source maps: 64 KiB each | 262,144 |
| New deployed helpers, aggregate | 131,072 |
| Framework/failure closeout | 2,097,152 |
| **Total worst-case software output** | **29,966,952** |
| **Headroom under 33,554,432 bytes (32 MiB)** | **3,587,480** |

The former 34-leaf OTHER metadata census is preserved. Five additional possible leaves are bounded explicitly: one preparation start at 64 KiB, one input at 128 KiB, one optional preparation stdout at 64 KiB, and two optional failure/uncertainty latches at 8 KiB each. Its maximum changes from 2,080,768 to 2,359,296 bytes; no unlisted metadata writer is admitted. The two extra latch allowances do not authorize extra attempts.

The new versioned runner and literal-only collector successor are capped at 64 KiB COMBINED; the guard is reused unchanged. Existing helper bytes of 61,116 plus 65,536 give 126,652 bytes, within the unchanged 128 KiB helper pool by 4,420 bytes. The two new helper leaves belong to that helper row, not the metadata row. Old helpers remain immutable. The four source maps remain initial plus after format/prepare/check; freeze uses the existing after-format map. Existing stdout5/outcome5 are verified and reused, never overwritten or duplicated. D authoring copies remain counted in the separate source/control partition and global 1 GiB limit.

The initial 721,512-byte baseline is the retained software at the start of this cycle. The later actual census of 85 entries / 912,737 logical bytes includes already consumed portions of the new rows; it is not added again. The exact enabled successor helpers will total 62,823 bytes, making retained and new helper copies 123,939 bytes, below 131,072.

This table is the complete proposed output-class reservation. Before admission, the corrected source must match its leaf names, per-file caps, partial-output behavior, and absolute deadlines. Each stage must also fit all retained bytes plus its complete remaining write/closeout reservation. The table does not by itself certify an unreviewed control implementation.

## Independently reviewed correction identities

Lead reviewed the complete corrected-freeze source and its final timer fix; Quality independently accepted it and the complete remaining software controls. A final-stdout deadline gap was fixed before approval: every terminal path retains the original start plus 30 seconds, including after an earlier timer signal. Static review is not a passing execution result.

| Disabled source | Bytes | SHA-256 |
| --- | ---: | --- |
| `repair-b-cycle3-corrected-freeze-v2-draft.py` | 45,580 | `092c5fa198a27570726c69d779c4f26b3c120d45bcf1ed0790aa2aaa57c28fa7` |
| `repair-b-cycle3-freeze-run_checks-draft.py` | 38,122 | `8b37492a662ae4209bbabe3f9b81764a38ef84f0a31d0918523e42c0cd90b12c` |
| `repair-b-cycle3-freeze-contract_child-draft.py` | 24,647 | `56c0f29dfe9c76cd45366f48d3b684fb798eca4ff62ca7a7ad47ad7e27f44db5` |
| `repair-b-cycle3-freeze-post-collection-draft.py` | 29,901 | `8e62cb0f3442376792215b13382a7dd4d44959e99c4e562e29dae8ec2d082d59` |

The corrected freeze makes exactly eight guarded Git calls: original HEAD, tracked inventory, dirty status, whitespace check, stage the one file, commit, resulting commit/parent/author/tree, and clean status. It hashes all 437 source files before and after committing. Its maximum new software-root payload is 849,255 bytes, below its 1 MiB preparation reservation; the separately counted approval copy is at most 64 KiB outside that root. It preserves the known failed freeze and both historical approval identities. Its receipt embeds the correction review; no second standalone restart record is created.

The versioned runner permits only attempts 6 and 7. Its one failed-preparation exception is the exact retained `ddd7a98…` receipt, joined to the successful amended freeze and new direct approval. Earlier failures remain charged. The collector changes only its three helper-filename literals. The postcollection binder launches no child, retains its 5/15 ceiling, and joins nine prior preparations before writing the tenth overall preparation (the fourth in this cycle).

Future substitution is limited to the explicit enable flags, direct amendment approval reference, hashes derived from those sealed helper bytes, actual committed source/tree, and actual successful phase-6 outcome pins. These values cannot be guessed or self-approved. All other reviewed source bytes stay fixed.

## Exact remaining writers and delivery gates

The following are the actual remaining software writers; all older leaves, including failed preparations and prior outcome5/stdout5, remain immutable. Reserved optional leaves do not authorize extra executions.

| Writer | New leaves / bounded scope |
| --- | --- |
| Corrected freeze | `source-freeze-cycle3-correction-start.json` ≤64 KiB; `source-freeze-cycle3-correction-input.json` ≤128 KiB; `preparation-cycle3-source-freeze-correction.json` ≤512 KiB; first `admission-cycle3-prepare.json` ≤64 KiB; `run_checks-cycle3-freeze.py` and `contract_child-cycle3-freeze.py` together ≤64 KiB. |
| Approval custody | One `repair-freeze-correction-direct-approval.json` ≤64 KiB in runtime evidence, counted outside the software pool in the existing source/control/global reservations. |
| Phase 6 | `admission-6.json`, `start-6.json`, `source-after-6.json`, `attempt-6.json`; `6-sentinel.log`, `6-sentinel-c.log`, `6-collect.log`; `6-sentinel-tripwire.json`, `6-sentinel-c-tripwire.json` and the corresponding two `-continued.json` leaves; `6-collected-nodeids.json` and `6-collect-receipt.json`. Existing row caps apply. |
| Postcollection binder | `stage-cycle3-check-admission-start.json`; `terminal-stdout-6.json`; `prior-outcome-6.json`; `preparation-cycle3-check-admission.json`; first `admission-cycle3-check.json`; `preparation-cycle3-check-admission-late-failure.json` ≤8 KiB. |
| Phase 7 | `admission-7.json`, `start-7.json`, `source-after-7.json`, `attempt-7.json`; `7-format.log`, `7-lint.log`, `7-typing.log`, `7-tests.log`; `7-tests-receipt.json` and `junit-7.xml`. Fixtures and framework/partial outputs stay in their existing bounded classes. |
| Final software review/handoff | The reserved `terminal-stdout-7.json`, `prior-outcome-7.json` and `cycle3-software-index.json` ≤64 KiB, plus bounded review records in the unchanged 8 MiB review pool. |
| Extra optional correction slots | `source-freeze-cycle3-correction-stdout.json` ≤64 KiB, plus `source-freeze-cycle3-correction-failure.json` and `source-freeze-cycle3-correction-uncertainty.json` ≤8 KiB each are reserved in the five-leaf addition. The reviewed correction currently writes stdout/stderr to the external observer and does not create these optional files; they cannot silently become new writers. |

Before any dependent launch, Lead must accept the complete external exit/stdout, byte readbacks, closure and cumulative charges. A newly written admission alone is insufficient. After the corrected freeze, the proposed 4/12 control review validates its actual files and new source identity. Phase6 must pass both benign sentinel denials and source-bound collection; the counted postcollection binder joins that result. Phase7 must pass formatting, lint, full typing and all guarded regression targets. The proposed 4/12 final-outcome review and retained 2/6 handoff complete B acceptance.

Only then does the already approved original PR run proceed, followed by successful protected-main integration and its original candidate run, one verified candidate installation, and the existing ordered runtime stages including one capture. Their original evidence, closure, output, custody and failure-stop gates still apply. The exact original plan remains the source of unchanged C/D stage ceilings. No rerun, fourth software cycle, additional capture, scientific claim or new infrastructure is admitted by this amendment.
