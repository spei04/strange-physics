# Bounded Journal prerequisite

This internal path provides bounded Journal I/O and a fixed capture holder. It
implements no public purchase API, ledger reservation, receipt, simulation or
settlement. Its caller must durably retain the allowance before allocating
`JournalEpochs`; this helper does not establish that durable authority.

One parent-owned partition consumes 14 writer epochs and one holder epoch without
refund. A kernel token prevents forked copies from each opening another writer.
The parent closes its token descriptor after forking. The future purchase caller
must finish and reap its writer before starting the holder. Neither child file
limit applies to the parent's store.

The optional bounded `Journal` path requires a child-installed 128 KiB file cap
before creation or recovery, preserves stricter inherited soft and hard limits,
and precharges fixed open, configuration, schema, initialization, reservation,
commit and failure-log boundaries. Unsupported or repeated writes deny before
SQL. Auto-vacuum is checked without changing it. Ordinary Journal callers retain
their existing behavior and do not import the optional Unix resource helper.

`capture_journal` starts only the fixed two-second CPU holder under the original
absolute deadline, including any stricter timer captured before fork. The holder
keeps `BEGIN IMMEDIATE` and its raw descriptor through the caller's commit or
rollback acknowledgement. The parent receives bounded, complete captured bytes;
it does not open the live Journal. Call `recheck` immediately before the parent's
commit, and leave the context only after that commit or rollback. This primitive
supports that lifetime but does not implement the future purchase closure.

Cleanup releases or terminates the holder and attempts to reap it. Actual
`wait4` observations, including a valid zero CPU value, remain available through
the supplied epoch object even if initial capture fails. Unavailable status or
usage stays unknown; cleanup preserves an existing caller error and never signals
a PID after an ambiguous reap failure. These observations do not settle ledger
costs. The caller must retain the prepaid allowance on failure or uncertainty.

The permanent conformance tests cover small-row creation, legacy mixed and pending
records, inherited limits, one-use epochs, whole-file capture, raced hot recovery,
directory durability, framed IPC, original deadlines, parent death, cleanup
faults and independent-process writer exclusion through release. Independent
review also exercised sensitive cap, descriptor-close and short-read mutations.
These are SQLite/process fixtures, not numerical purchase evidence.

The enforced 128 KiB file cap can reject legitimate rollback growth. A smaller
rollback was demonstrated to work; a dirty-all-pages 128 KiB profile failed
honestly. There is no promise that every 32-page transaction fits, no public
purchase or recovery admission, and no completed 16-call specimen in this PR.
