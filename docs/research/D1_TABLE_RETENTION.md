# Conditional T retention source slice

Source-only implementation of the accepted
[table retention design](D1_TABLE_RETENTION_DESIGN.md), based on
`2b372fb5937eda4c53507c42425a154e83564732`. New code/tests have not been
imported, collected, formatted, type-checked or executed. Earlier context
observation qualification does not qualify this new operation.

## Files and interface

* `tests/d1_table_retention.py`: concrete once-only metadata owner,
  `TableRetentionAttempt(metadata_root, sink, table_raw).retain()`.
* `tests/test_d1_table_retention.py`: owned synthetic T/C files and fault cases.
* `tests/d1_primitive_sink.py`: only the optional `_Anchor(...,
  expected_parent=None)` argument and a comparison before mkdir; existing
  callers keep their default behavior. No reader, sink or observation method
  changes.

The frozen/slotted result has exactly six fields: actual `table_raw`,
`table_sha256`, `table_bytes`, `context_raw`, `context_sha256`, `context_bytes`.
It carries no authentication, readiness or activation field. In-memory fault
facts and `RetentionSnapshot` describe the single attempt; no snapshot is
accepted as permission, input proof, serialized receipt or retry authority.
`context_observations` counts completed observations, not failed attempts to
read C. Creation-entered versus confirmed-created fields distinguish uncertainty
from absence. `metadata_close_confirmed=False` includes a constructor that
failed without returning an anchor; it does not prove any descriptor leaked.

Construction captures owner identity and inputs without filesystem I/O. The
attempt is consumed before validation. Wrong owner/reentry consumes it too;
swallowed reentry is sticky. `first_exception` preserves the original object.
At most 16 supplemental/primary phase/type summaries are kept, type strings are
bounded to 192 characters, and further records increment an excess counter.
Arbitrary exception messages/objects are not serialized. This is not a bound on
Python exception heap size or a hostile-Python sandbox.

## Actual sibling and byte joins

The helper parses actual T bytes with `parse_table`, obtains C through the real
sink's `observe_context`, and reuses `_context` for exact shared declarations,
fixed call/event limits and the existing physical-capacity withholding. It
creates no bridge, decoder cursor, Event or scientific callback.

After the first fresh observation, it borrows only read-only checks/fstat of the
actual sink anchor, never ownership of its descriptors. Its own metadata parent
must have that actual full device/inode/uid/mode identity before mkdir. Root
names and actual root device/inode must differ. The metadata anchor independently
owns its parent/root fds and validates current named identities. Matching strings
or caller-supplied identity tuples cannot replace this join. No sink private
stop/busy field is mutated by the T operation.

The created T file's identity is retained for named checks at later boundaries.
This catches a stable same-byte inode substitution as well as changed bytes;
unlike C, its creation identity is available here. It is not a universal defense
against concurrent replace-and-restore during a read. The existing `_read_file`
loop is unchanged. Exact actual readback bytes must match the initially parsed
canonical T, and only that actual readback supplies the returned T identity.

The successful sequence is: fresh C/join; exclusive sibling creation; direct T
write and file/directory fsync; once-only writer close; bounded exact readback;
independent metadata cleanup; own sticky-state check; final fresh C/join;
byte-only result and final own sticky-state check. Metadata close callbacks
therefore precede the final C read. A close hook that swallows reentry cannot
cause a second C read. A final-C hook that swallows reentry cannot cause success.
The caller must maintain the reviewed single-owner idle interval; this is not a
filesystem transaction or protection against a separate concurrent actor.

## Failure and ownership

Full validated T length is reserved before creation/write and is never refunded
after partial or unknown delivery. Positive short writes continue that same
file; zero progress, interruption or error stops. No temporary copy, overwrite,
rename-over recovery, delete, reopen or retry is performed by the helper.

On a primary error, remember it before supplemental close records. Clear each
owned fd slot before its one close attempt. Close all remaining owned descriptors
independently; a close confirmation lost after actual closure still blocks
success. `_Anchor` construction can create a root before raising without returning
an object. Its original exception/close notes and entered-but-unknown state stay
retained; no automatic probe or cleanup replay invents complete closure.

An error before final C, including during metadata close, prevents another C
read. A final C failure can leave fully written T but no successful joint
observation. Actual bytes on disk do not imply an acknowledgement or authority.
The caller retains responsibility for sink `finish()` once on abandonment;
metadata errors do not stop the sink privately or authorize a new operation.
No process-global once-only guarantee follows from a consumed Python instance.

## Authored test census and estimates

There are **33 cases in 16 test functions**, with explicit short parameter IDs;
99 setup/call/teardown phases are prospective, not observed.

| Family | Cases |
| --- | ---: |
| Exact success/order/immutable byte result | 1 |
| Mutable, oversized, noncanonical or mismatched T | 4 |
| Different parent, sink-root collision, existing root | 3 |
| Wrong PID/thread, initially non-idle/stopped sink | 4 |
| Positive short/zero progress, partial/interrupted write | 4 |
| Parent/file/directory fsync failure | 3 |
| Substituted readback/read error | 2 |
| Real-close-then-error at writer/reader/root | 3 |
| Swallowed reentry at write/close/final C | 3 |
| Constructor primary plus supplemental close failure | 1 |
| Intervening sink append/context change | 2 |
| Same-parent root substitution and same-byte T inode replacement | 2 |
| Original write error plus independent root-close error | 1 |

OS fault wrappers restore before caller sink finish and pytest teardown. Lost
close-confirmation cases call original close first for the exact owned target,
inject once, and separately assert EBADF. Sink anchors remain caller-owned.
Repeated failed/successful `retain` calls are tested with filesystem functions
poisoned. Table/context bytes are synthetic declarations; named scientific
imports are blocked in test bodies, with future execution controls still needed.

Each fixture asserts its valid T is at most 4,096 bytes. The one oversized input
is only an in-memory parser negative (57,857 bytes), never a file. Reserve a
conservative **32,768 temporary payload bytes per case**, or **1,081,344 bytes**
over all 33 cases. This includes C/terminal, T/partial T, a transient replacement
copy and the tiny raw sink line in the two idle-violation cases. No full profile,
55,100-call stream, 4 MiB shard fixture, S or A is generated.

Conservative filesystem census: 33 pytest parents, 33 sink roots, at most 33
metadata roots, plus at most two additional roots for different-parent and
rename/substitution cases. At most 101 retained regular-file names cover C,
terminal, T and two tiny event files; one transient replacement adds at most one
regular-file creation. No symlink, hardlink or FIFO fixture is authored here.
These are source upper estimates, not observed retained counts or allocation.
Directory blocks, logs/JUnit, control files, source versions and exported/copied
artifacts must be accounted separately by the finite engineering plan.

## Production-shaped bounds still conditional

The helper preserves T<=57,856 and C<=4,096 bytes. On a successful attempt there
is one T parse, one direct write, one bounded T readback and two fresh C reads;
read payload is at most 66,048 bytes. Metadata opens are bounded to independent
parent/root, write fd and read fd, plus the two sink-owned temporary C read fds.
The normal path performs three fsyncs: root parent, T and metadata directory.

For W positive T writes, `_write_remaining` invokes its active/identity check
before and after each write. The surrounding success path invokes that same
check seven more times: `2W+7`, with W<=57,856. Each includes real stat/identity
work, not constant/free bookkeeping. Failure paths preserve attempted progress
and cleanup costs. C/T read loops are bounded by their positive one-byte extent;
zero/early EOF/error stops. Exact admitted command/syscall measurements remain
future engineering evidence.

Successful validation still hashes T twice (parser and actual readback) and C
four times (observations plus both `_context` validations). Input T, parser JSON
objects/fixed row views/canonical temporaries, readback chunks and joined bytes,
two C observations and result-held references are distinct memory operands.
The result aliases actual readback/final C bytes; it writes no extra copy.
Encoded limits are not a measured Python heap bound.

T uses the existing 65,536 T/A reservation, with full attempted T charged after
failure. The separate 65,536 temporary-copy reservation remains withheld and is
not reassigned merely because this writer uses no disk copy. Existing sink
20,480 metadata reservation and 65,536 rotation withholding remain unchanged.
The proposed 16 MiB transcript partition and whole-science/logical 64 MiB limits
supply no fresh allocation. No serialized operation receipt, S budget or claimed
aggregate fit is added.

## Remaining work

Independent source review, configured full typing/lint/format and bounded owned
filesystem tests are pending. Qualified storage behavior, external failure
retention/closure, actual source bindings and aggregate science-output fit remain
separate. Defer all candidate A construction and fixed `codec-activation.json`
retention until the resolved/authenticated S and outer-admission slice. This
operation supplies no S schema, source resolver, callable installation, history
inventory, exposure decision, activation or scientific result.
