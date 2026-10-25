# Bounded Journal prerequisite

This internal I/O path implements no purchase API, ledger reservation, receipt,
simulation or settlement. The caller must durably retain a prepaid allowance
before allocating JournalEpochs. Its one parent-owned partition consumes14
writer epochs and1 holder epoch without refund; a kernel one-use writer token
prevents forked copies from each opening another writer. The parent closes its
token descriptor after forking. Child limits never apply to the parent store.

An optional Journal bounded path requires the child-installed128KiB file cap
before creation/recovery, preserves stricter inherited limits, and precharges
fixed configuration/schema/initialize/reserve/commit/failure boundaries.
Unsupported/repeated writes deny. Auto-vacuum is readback-only. Legitimate
rollback growth above128KiB fails; no guarantee all32-page writes fit.

capture_journal starts only the fixed2s holder under the original absolute
deadline. The holder owns live BEGIN IMMEDIATE and every same-inode raw
descriptor through caller COMMIT/rollback acknowledgement; parent reads only
bounded transferred bytes. Call recheck immediately before the parent's commit.
The holder is always released or killed/reaped, and actual wait4 observation is
available through the supplied epoch object even when initial capture fails.
That observation is not an original work measurement or settled ledger cost.
A failed/unknown holder retains its prepaid control allowance.

This checkpoint is draft and unvalidated. The finite lower-level test plan
covers real small-row SQLite creation, legacy row semantics, inherited limits,
fork-token reuse, hot-header races/caps, epoch reuse, directory-fsync failure,
fresh-exec lock exclusion and release, IPC/deadline/parent-death/reap boundaries,
and sensitive raw-descriptor-close/late-cap mutants. No16-call specimen or
runtime admission is claimed here.
