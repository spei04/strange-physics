# Measured purchase implementation handoff

Status: pure contracts/binder 3df6dc3 accepted and published on 2026-10-26. Actual purchase facade, lifecycle, receipt and recovery implementation continues; first-purchase evidence, the conditional V3 specimen and the research comparison remain pending. No purchase PR or merge is claimed.

This handoff is pinned to [main c784f15](https://github.com/spei04/strange-physics/tree/c784f15dd91dfed169a5af0847dbd31445bcad88), with the existing plan and delivery record at [aeca99b](https://github.com/spei04/strange-physics/blob/aeca99b3e865937d8e89e6b41afb77a1999174e0/docs/EXECUTION_LOG.md). PR #123 supplies the bounded Journal primitive; it does not supply durable purchase authority or cost settlement.

## Ownership and execution prerequisite

| Owner | Work |
| --- | --- |
| Quality | Exclusive identity author for actual purchase execution and recovery following the accepted pure checkpoint |
| Platform | Independent file/process limits, durable charging, cost and recovery review |
| Research | Six-document progress reconciliation, then independent identity, history and recovery review |
| Project lead | Checkout handoff, review integration, delivery and progress consistency |

Cloud access and checkout ownership were verified at the 2026-10-26 handoff: both checkouts were clean, no consumers were found and 93,668,601,856 bytes were free. Quality continues in the existing identity checkout on feat/measured-journal-purchase from accepted c784f15; Research owns this bounded six-document update until release to Lead. Retained source-bound validation at 3df6dc3 matches 86 package files across Git, wheel, sdist and the installed-file manifest; 4,689 unchanged dependencies are the author record. Revalidate the next frozen runtime checkpoint rather than assuming an unchanged mutable environment. Keep all work and evidence in the cloud. Historical PR #123 acceptance remains unchanged.

## Implementation checkpoints

1. **Pure contracts accepted; caller binding remains.** The accepted purchase_execution_contracts.py and purchase_execution_binding.py define immutable purchase intent, separate current context, four ordered calibration actions, canonical membership in a menu of up to 128 actions, and distinct execution/reconciliation receipts carrying StudyPurchase. Connect these through measured_study.py and the actual retained-authority path. Bind the retained freeze, source/lock/current engine, catalog world, cell/run, action and ordinal. The current context must be produced during paid work and receipt-bound; a tagged predecessor reference must resolve the actual execution or reconciliation closure. Pure supplied-material validation does not authenticate those runtime joins. No caller-supplied callable or unmetered Journal snapshot becomes authority.

2. **Charged execution and closure.** In `measured_candidates.py`, persist the actual `StudyPurchase` reservation before allocating `JournalEpochs`, opening/recovering SQLite or simulating. Both execution and retained-closure reconstruction currently use `purchase=None`; both need an explicit purchase join. Preserve capacity for finalization and recovery. Use a fixed purchase child that preserves inherited soft/hard limits, installs the 128 KiB cap before Journal access, closes the parent's one-use token after fork, and retains the original deadline. Confirm writer exit/reaping before starting the holder; an unavailable observation cannot authorize capture. Keep the holder through the CandidateStore closure commit or rollback, with recheck immediately before commit.

3. **Receipt and recovery.** Store an immutable receipt bound to the successful attempt's retained request, paid context, full captured Journal, result and ledger transition. A retry may change attempt ID, ticket and CAS head; the original purchase input, logical identity, action and ordinal remain fixed. Exact recovery returns the retained receipt without rebuilding it against current state. Settle known measured costs through the existing accounting rules; retain unknown or unmeasured costs conservatively. Keep the existing four CandidateStore transaction-attempt envelopes, including failed attempts. Separate Journal and CandidateStore commits are not one atomic transaction. Implement the three recovery outcomes below without weakening unrelated operations.

The pure checkpoint fixes the closed wire and calibration/menu interpretation without implementing a selector or proving numerical execution. Raw artifact identity alone does not prove semantic menu membership. The 64 KiB action-artifact parser bound is unchanged. Caller implementation and review remain within the existing design and require no new product-owner approval gate. See the [checkpoint evidence](EXECUTION_LOG.md#2026-10-26--pure-purchase-contracts-accepted).

These are independently reviewable checkpoints within the existing PR2 unit. Delivery requires the complete purchase-and-recovery path; contracts alone do not satisfy its exit gate.

## Required behavior and paired evidence

| Boundary | Required evidence |
| --- | --- |
| Durable reservation | Valid reservation permits work; CAS, durability or capacity rejection prevents Journal access and retains applicable charges. |
| Frozen identity | The real retained action/world/ordinal succeeds; action, raw bytes, signed-zero identity, engine or prefix substitutions fail before numerical work. Retry consumes the same purchase slot. |
| Child limits and capture | The real purchase dispatch preserves stricter inherited limits and the original deadline. A live or ambiguously reaped writer cannot start a holder. A fresh-process writer stays excluded through closure and succeeds after release. |
| Truthful failure and cost | Only declared `SimulationError` creates a failed simulation record. I/O, cap, timeout, transport and missing measurement failures remain unknown. Known zero CPU remains distinguishable from unavailable CPU; failure-log, output and copy costs are accounted for. An injected simulation failure is a labeled fault fixture; known measurements do not release unresolved original or control-tail holds. |
| Successful purchase | One end-to-end bounded purchase produces the expected real Journal row, immutable receipt and corresponding measured-cost settlement. Validate byte and identity joins independently. |
| Recovery | Inject interruption before Journal reserve, after pending reserve, after terminal Journal commit and after store commit/lost acknowledgement. Prove the distinct outcomes below and retained charges. |

Recovery outcomes:

- **Intact closure:** A fresh paid accounting recovery returns the original retained bytes and receipt. Numerical callables are poisoned, and live input paths are unnecessary.
- **Missing or pending row:** An explicit fresh charged retry keeps the original input, action, ordinal and purchase identity. Its paid current context proves the original prefix plus an absent or matching pending row.
- **Terminal row without closure:** A fresh paid reconciliation returns a distinct reconciliation receipt. It neither simulates again nor invents the original receipt or OS measurements; prior unknown holds remain retained.

Preserve all purchased history, including failed calibration and pending rows. Downstream candidate/classical readiness still requires the complete actual 12-row committed history, including failures. Absent native selection remains distinct from independent classical success.

Reuse PR #123's accepted lower-level Journal proof. Add focused tests of the new caller boundaries and sensitive failures; do not repeat the entire prerequisite matrix without a new reason.

## Exit gates and remaining scope

The initial integration checkpoint requires one end-to-end purchase, an immutable receipt, known cost settlement and recovery evidence. Full PR2 acceptance also requires the declared bounded 12-slot mixed history, retry/reconciliation and downstream candidate/classical consumption proof. An unproved V3 specimen remains an explicit limitation; one purchase alone does not establish the complete path.

Delivery requires independent Platform and Research review; configured formatting/lint/type/schema/security/tests/package checks; required PR CI; and exact main candidate verification.

V3 remains conditional. Its declared envelope is not observed usability, additional allocation or full-study admission. Preserve cumulative caps and unresolved holds. Publisher authority handoff, full-study capacity and explicit parent audits remain open under #105/#106.

Before study admission, re-estimate remaining purchase/recovery work, publisher handoff, capacity/accounting and parent acceptance, then the finite-grid reference, calibration, acquisition and comparison tasks. Historical estimates remain historical; do not add the old two-PR estimate to parent totals or infer a new completion date. Grid remains first; Laplace and its approximation audit remain later.

Out of scope: new scientific models or policies, simulator changes, provider calls, cloud provisioning, cap increases, signing/deployment and claims of production readiness.
