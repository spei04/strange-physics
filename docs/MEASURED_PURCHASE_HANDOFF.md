# Measured purchase implementation handoff

Status: implementation assigned on 2026-10-26 after verified cloud handoff. The first immutable source checkpoint and real purchase evidence remain pending; the conditional V3 specimen and research comparison have not started.

This handoff is pinned to [main c784f15](https://github.com/spei04/strange-physics/tree/c784f15dd91dfed169a5af0847dbd31445bcad88), with the existing plan and delivery record at [aeca99b](https://github.com/spei04/strange-physics/blob/aeca99b3e865937d8e89e6b41afb77a1999174e0/docs/EXECUTION_LOG.md). PR #123 supplies the bounded Journal primitive; it does not supply durable purchase authority or cost settlement.

## Ownership and execution prerequisite

| Owner | Work |
| --- | --- |
| Quality | Exclusive author for purchase contracts, binding, execution and recovery in the existing identity checkout |
| Platform | Independent file/process limits, durable charging, cost and recovery review |
| Research | Independent frozen identity, failure semantics, complete history and recovery review |
| Project lead | Checkout handoff, review integration, delivery and progress consistency |

Cloud access and checkout ownership were verified on 2026-10-26: both checkouts were clean, no checkout consumers were found and 93,668,601,856 bytes were free. Primary is synchronized to the reviewed f6c58bf4 handoff; Quality owns the existing identity checkout on feat/measured-journal-purchase at accepted c784f15. Revalidate the owned installed source, lock and interpreter before runtime. Keep source, dependencies, tests, outputs and private evidence in the cloud. The new private assignment snapshot records this transition; historical PR #123 acceptance remains source-qualified and unchanged.

## Implementation checkpoints

1. **Contracts and frozen binding.** Extend the closed request/input/result/receipt types in `study_execution_contracts.py`, the public facade in `measured_study.py`, and validation in `study_execution_binding.py`. Bind the actual retained freeze, source/lock/current engine, catalog world, cell/run, canonical action, ordinal and calibration/menu role. Keep the original purchase input and logical identity immutable. A separately bounded current attempt context must be produced during paid work and bound to the receipt. No caller-supplied callable or unmetered Journal snapshot becomes authority.

2. **Charged execution and closure.** In `measured_candidates.py`, persist the actual `StudyPurchase` reservation before allocating `JournalEpochs`, opening/recovering SQLite or simulating. Both execution and retained-closure reconstruction currently use `purchase=None`; both need an explicit purchase join. Preserve capacity for finalization and recovery. Use a fixed purchase child that preserves inherited soft/hard limits, installs the 128 KiB cap before Journal access, closes the parent's one-use token after fork, and retains the original deadline. Confirm writer exit/reaping before starting the holder; an unavailable observation cannot authorize capture. Keep the holder through the CandidateStore closure commit or rollback, with recheck immediately before commit.

3. **Receipt and recovery.** Store an immutable receipt bound to the successful attempt's retained request, paid context, full captured Journal, result and ledger transition. A retry may change attempt ID, ticket and CAS head; the original purchase input, logical identity, action and ordinal remain fixed. Exact recovery returns the retained receipt without rebuilding it against current state. Settle known measured costs through the existing accounting rules; retain unknown or unmeasured costs conservatively. Keep the existing four CandidateStore transaction-attempt envelopes, including failed attempts. Separate Journal and CandidateStore commits are not one atomic transaction. Implement the three recovery outcomes below without weakening unrelated operations.

At the first contract checkpoint, freeze the closed wire distinction between original execution and reconciliation receipts, and the strict calibration/menu action interpretation. Raw artifact identity alone does not prove semantic menu membership. Resolve these details within the existing design and peer review; they do not introduce a new product-owner approval gate.

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
