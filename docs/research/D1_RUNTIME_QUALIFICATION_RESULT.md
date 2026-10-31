# D1 actual runtime qualification result

**Result: incomplete.** Installation materialization, three benign guard probes and the live-descendant witness passed. The single capture attempt failed during initial Python startup validation. Its independent owner also failed to reconcile the already-cleared service. There is no accepted capture and no D1 scientific run.

## Source and authority

This result belongs to exact main [5e0b3e7db436061f4d7c9a5e983f7878cea31974](https://github.com/spei04/strange-physics/commit/5e0b3e7db436061f4d7c9a5e983f7878cea31974), its accepted same-run candidate from [CI 41230418150/1](https://github.com/spei04/strange-physics/actions/runs/41230418150/attempts/1), and the actual private Linux installation. Later documentation commits are not newly qualified candidates.

The user approved the [reviewed continuation](https://github.com/spei04/strange-physics/blob/f54a7d609ec77e75771b653aed158275dd8271f9/docs/research/D1_RUNTIME_CONTINUATION_DECISION.md): one increase from 200 to **400 CPU seconds**, with **600 active-wall seconds** unchanged and all prior charges retained. It authorized one attempt at each of four remaining engineering stages. The equivalent approval question in project coordination does not create another allocation.

The original operator and unused materialization admission remain preserved. Approval record SHA-256: `1819fd874c135c032ad01bcdaa5097a5841ae4a80090b5b2859684b6a42edd16`. The executed continuation operator is `aa1d3916598c3ada568a5004939600d14b80b7ab1a304d75b6cf1db2d4b6da0e`, bound to proposal `32c3e66359f64e08cd7b375f0d980184492122c06e65417968404831a68e754a`.

## Actual outcomes and accounting

| Stage | Outcome | Charged CPU seconds | Charged active-wall seconds |
| --- | --- | ---: | ---: |
| Native attempts 1–3, retained | Third attempt passed; both earlier failures retained | 48.888820 | 66.534427 |
| Materialization | Passed; no child or service launch | 7.609223 | 10.553777 |
| Guard probes | Passed; three expected exit-86 denials and clean subprocess closure | 4.101099 | 7.201204 |
| Live-descendant witness | Passed; leader exit did not imply completion | 5.011944 | 10.037435 |
| Capture only | Failed; full 150 CPU-second service hold retained | 154.301334 | 19.470323 |
| **Runtime account total** | **Capture remains unqualified** | **219.912420** | **113.797166** |

Each continuation stage includes its 2 CPU / 5 wall closeout reserve. Charges are not all measured consumption: the capture row includes the unreleased 150 CPU-second reservation. There is no refund, reset, transfer from a closed account or automatic retry.

The separate setup account retains **22.297874 CPU / 43.566476 active-wall seconds**, including its failed first attempt and custody correction. Source qualification and hosted CI retain their previously reported scopes.

Materialization joined 2,498 protected-plan file rows to the native inventory, accepted source/candidate and installation evidence. All 97 installed package rows match exported source; 1,091 dependency rows match the accepted inventory. The installation record is 161,081 bytes; the protected plan is 612,843 bytes.

The guard probes used benign retained Python code, a fixed source route and C builtin `len`. The C probe's diagnostic label is `math.exp`; it did not invoke `math.exp` or a D1 primitive. Each produced exactly the expected denial, without a benign-body or return marker. All three processes were reaped with EOF and closed pipes; all three fresh cache directories remained empty.

The witness observed a successful leader exit while its cgroup remained populated by the child. Completion was withheld until the explicit release was acknowledged. Later evidence records an empty `ControlGroup` and `populated=null`; those raw values are preserved, not changed to `false`. Its original provisional `accepted=false` remains unchanged. Named-service CPU was 0.185838 seconds, separate from the parent/waited-child scope.

## Capture failure and closure evidence

The retained 892-byte child log reports `BootstrapError: Unlisted frozen module` at the initial `_check_loaded` call, before standard-library preparation and the capture routine. The current error does not record the offending module name. A specific module or alias is therefore **not established** by this attempt. No valid capture completion report was produced.

A second defect affected independent owner reconciliation. The owner waited for the controller and raised on its nonzero exit before binding the retained controller terminal evidence. By then the controller had already observed closure and cleared the service. The owner's first observation lacked the quota/burst values needed to bind its identity, so it retained null invocation/group identity, `closed=false`, `cleanup_confirmed=false` and unknown usage. Those original records are unchanged.

Controller observations do retain one matching invocation, its failed terminal exit, empty cgroup and **5,574,222,000 ns** of service CPU. Both outer subprocesses were reaped with EOF and clean process-group handling. Supplemental read-only checks found the exact named cgroup and both outer process paths absent. Review found no essential additional service action. These scoped observations do not repair the original owner record, prove arbitrary escaped-process absence or turn the failed attempt into a successful capture.

The outer receipt accordingly remains `closed=false`, `usage_known=false`, with its complete 150 CPU-second service reservation. Its post-capture output census is null, and the later source/native rechecks did not complete on this failure path; no successful final custody validation is claimed. The controller's measured 5.574222 seconds is separate evidence; it does not replace that reservation or get added again to the retained charge.

## Independent review and evidence

Independent reviews accepted the materialization, guard and benign-witness evidence while preserving capture failure:

- Materialization and probes: `f7b67ce19329db5cbfd290fc9df0b79b0b45d3ec75e771a5c29382b4a4a8acba`.
- Benign/capture semantics and source diagnosis: `ef9ebe6ed2d0481c2ff72d3dd988da5e614973e676b4cc77dd8b275f7f7aeb36`.
- All four stages' process/accounting review: `7604e59cc4316c280354e34e200789fd354daa0460d2471df4ef4d7f9b9feed0`.

The unchanged review/closure account is 50 CPU / 150 wall seconds. Its retained known charges and assigned holds, including the final closeout reservation, sum to **46.304715 CPU / 134.198665 wall seconds**. This arithmetic leaves 3.695285 CPU / 15.801335 wall seconds, but it is not a complete measured-cost or hard-cap compliance claim: some setup/admission peer reads and diagnostic closeout lack standalone measurements. Those within-review coverage gaps remain unknown, separate from unmeasured authoring, SSH/GitHub administration and provider costs. Each combined/successor hold is counted once, including failed preparation. No closed-account balance transfers are used. The private reconciliation ledger is `2d2a592e453686667d07069188cfed762b7c1bdb624c3506c17cf3ad46949f71` (16 entries and 17 exact receipt pins).

| Retained artifact | SHA-256 |
| --- | --- |
| Materialization receipt | `14b84c190c1473430d8a812abeede6cb1b641d87f184770e524212bd34340036` |
| Guard probes receipt | `2e660dac7d49fec4b7a891cb0c24e53fdac5f56da6c3afb405b514ca135acfd6` |
| Benign witness receipt | `50b2aa570465882342142f2ba51b27ca29f9079afdd1fdca51e86afe36ec2e59` |
| Failed capture receipt | `bb55fdfb736774e56a6607c740be3e1ca2e4d0de9a30514cb3a4d2cccaa7923f` |
| Actual child failure log | `379ad64f0373cd12934fb5397143e0027bfd6156c763d89d0e880b7f5a08b7a6` |
| Original independent-owner final | `52521d8665cb702b2d2e8818c803813a721c026f685f1a4f492b662cdd5dc3c8` |
| Controller terminal before stop | `1b4143bd6cd0ef4ec9cf05805ff66a1d0f297b240e54b31cbce54dc6ba0a1ea1` |

Evidence and the actual installation remain private in the cloud, owner protected, with review date 2026-11-30. No local project copy, new checkout, scientific batch, provider expansion or release was created for this continuation.

## Follow-up work

The owner approved the separate [complete repair and validation package](D1_RUNTIME_REPAIR_PLAN.md)
at commit `ca0b26ae`. Its [startup diagnosis passed](D1_RUNTIME_REPAIR_RESULT.md);
the source repair now includes the two observed importlib aliases and 16 additional
regression cases. Software checks, new candidate delivery and actual capture remain
pending. The closed Unit22 account, this consumed continuation, its failed outcome,
full service hold and unresolved evidence are retained separately.

The source repair must address both defects without weakening rejection:

1. Add bounded diagnostics for the rejected loaded-module key and import specification. Admit any frozen-module alias only with concrete evidence and exact protected identity checks; retain negative cases for forged or unlisted aliases.
2. Reconcile a failed controller through verified retained invocation/group/profile evidence before service cleanup makes independent binding impossible. Preserve rejection of identity mismatch, missing evidence and uncertain closure. A failed capture must remain failed even when its service is closed.
3. Add focused regression cases for both failures and independently review the changes. Qualify the resulting exact source/candidate and prepare a complete finite validation plan before another actual attempt.

The current one-attempt sequence is consumed. No new capture, scientific run or additional allocation follows automatically. Scientific exposure, numerical adequacy, evaluation independence, disk reserve and enterprise readiness remain separate open gates.
