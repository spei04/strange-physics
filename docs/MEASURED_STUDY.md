# Measured freeze and Journal-bound candidates

This owner-local slice extends the existing candidate store with two fixed
entrypoints: `commit_native_freeze` and `commit_journal_candidates`. It does not
implement a purchase producer, classical dispatch, publication transfer, hosted
isolation, or a full study.

A freeze request points to bounded raw `NativeFreezeInput` bytes containing the
manifest and its canonical artifact strings. The current installed source, lock,
engine and owner-trusted build are verified using the existing admission. A
fresh work reservation commits before material validation. The pure
`freeze_native_study` validator runs under the measured parent work clock; the
manifest event, measured outcome and immutable receipt then commit in the same
closure transaction. No separate fifth store transaction is introduced.
Validation failures retain known costs and the unresolved work reservation.

The comparison entrypoint is separately tagged. The original candidate API
continues to deny comparison requests that supply only an observation bundle.
A comparison request binds a retained freeze receipt and the raw identity of a
real private Journal. It acquires the existing root lock, then the Journal's
real `BEGIN IMMEDIATE` exclusion and retained raw descriptor. A separate captured
inode supplies the bounded reader; no extra descriptor for the live Journal is
closed while that exclusion is held. The reader's actual digest, all twelve
charged intents and rows (including failures), world, run, engine, frozen pool
and configuration reconstruct the complete candidate input. Missing or pending
rows deny the request. Capture and live-file rechecks precede the closure commit.

Only the candidate input reaches the numerical producer. The trusted forked
child also parses the private request wrapper; this is not a hostile-process
sandbox. Generic frozen menu bytes do not establish a future selector or menu
implementation, and an absent selection is not a native scientific failure.

Recovery requires a fresh paid recovery ticket. It accepts the original request
head after a lost acknowledgement, while reserving new accounting work on the
current locked head. Original request/result bytes, original reservation prefix,
freeze event and facts remain bound. Retained artifacts are checked against all
manifest references before reuse; nested receipts also match the current
installation. Recovery reads the retained capture instead of the current
Journal and does not rerun freeze or numerical production. Unknown costs are
never refunded, reseeded or erased.

## Bounded synthetic construction

The test fixture has six finite slots but executes four calls: freeze and
comparison candidate at slots 0/1, then their recoveries at 3/4. Classical slots 2/5
remain unused. Its ordinary classical 8 MiB/120 s is not escrowed; the unused third
recovery and publication promises remain protected by the existing admission.

The declared first-slice envelope is 269,631,488 bytes and 342 CPU seconds. It
includes the unresolved 48 MiB/120 s setup hold, control hold, twelve unresolved
1 MiB/5 s purchase holds, the actual work ceilings, all three recovery ceilings and
80 MiB/71 s publication protection. It is not measured expenditure or throughput.

A real same-store freeze precedes a clearly test-only injection of twelve
purchase intents in one existing-store transaction. No production import API
exists for that seam. A fixed isolated child then creates genuine current-engine
observations: eleven successful simulations and one explicitly injected failure.
Historical synthetic engine fingerprints are never rewritten or adopted.

Before file creation the child applies a 262,400-byte file-size ceiling; it
never opens CandidateStore. An exact-path, original-connection fixture guard
applies and reads back 4096-byte pages, 32 pages, spill OFF, DELETE rollback mode
and FULL synchronization before schema writes. Its pre-write epoch guard
counts the 32 ordinary Journal epochs and three configuration epochs, denying
before epoch 37. This bounds each Journal DB/journal epoch by 393,472 bytes.
Four conservative 2 MiB store envelopes plus 36 Journal envelopes and a cumulative
4 MiB export/copy allowance total 35,677,184 bytes inside the setup hold. Parent and
child each have at most 60 CPU seconds under one absolute 180-second setup
deadline; failure terminates/reaps the child without automatic retry.

The first-slice successful ledger has 23 records and 14 unresolved holds. The
fixture retains a 256 KiB raw-ledger cap and 14 finalization records/64 KiB, and
protects a 512 KiB publisher-ledger allowance. Larger public classical limits
remain future integration tests, not a reason to truncate data here.

These are implementation and fixture acceptance requirements. Source-specific
test and package evidence is retained privately; an implementation checkpoint
alone does not establish runtime admission or production readiness.
