# Conditional T retention source slice

Implementation of the accepted
[table retention design](D1_TABLE_RETENTION_DESIGN.md), based on
`2b372fb5937eda4c53507c42425a154e83564732`. Independent source review is complete;
local qualification closed incomplete after four attempts. Final source
`87884ac1de70aabf7ef4bc188962bb23f9683da4` contains the reviewed fixes and passed
its separate original hosted CI check at the documentation successor recorded below. Earlier context observation qualification does
not qualify this new operation.

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
`context_observations` counts observations returned to this helper, not failed
attempts to read C. A hook can complete an actual C read and then raise before
handoff; the corresponding regression records that separate observation count. Creation-entered versus confirmed-created fields distinguish uncertainty
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

On a primary error, remember it before supplemental close records. The outer
exception boundary re-raises that same latched first exception object after
cleanup, even if a hook swallowed it and then raised a distinct EIO. Later
phase/type facts remain supplemental; neither the outward exception nor the
stored first fault is replaced. Clear each
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

There are **35 cases in 17 test functions**, with explicit short parameter IDs;
105 setup/call/teardown phases are prospective, not observed.

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
| Swallowed reentry then distinct EIO at parent fsync/final C | 2 |

OS fault wrappers restore before caller sink finish and pytest teardown. Lost
close-confirmation cases call original close first for the exact owned target,
inject once, and separately assert EBADF. Sink anchors remain caller-owned.
Repeated failed/successful `retain` calls are tested with filesystem functions
poisoned. Table/context bytes are synthetic declarations; named scientific
imports are blocked in test bodies, with future execution controls still needed.

Each fixture asserts its valid T is at most 4,096 bytes. The one oversized input
is only an in-memory parser negative (57,857 bytes), never a file. Reserve a
conservative **32,768 temporary payload bytes per case**, or **1,146,880 bytes**
over all 35 cases. This includes C/terminal, T/partial T, a transient replacement
copy and the tiny raw sink line in the two idle-violation cases. No full profile,
55,100-call stream, 4 MiB shard fixture, S or A is generated.

Conservative filesystem census: 35 pytest parents, 35 sink roots, at most 35
metadata roots, plus at most two additional roots for different-parent and
rename/substitution cases. At most 107 retained regular-file names cover C,
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

## Local verification record

The private Unit16 account closed after four attempts. Preparation collected
35 ordered IDs with zero test phases, verified the owned sentinel and preserved
the source/environment/guard checks. Attempt2 then stopped on lint B904 before
typing or test execution. The reviewed fix preserves a same-object exception
chain and explicitly suppresses a distinct later error as the cause of the
retained first exception. Preparation3 collected the same 35 IDs at
`70542438d2009cabfc417f9b3db2c88c96930d28`.

Attempt4 passed formatting and lint, then full configured typing across 223 files
reported one redundant disjoint-type identity comparison in the new test.
It stopped before test bodies. The final one-line test repair removes only that
comparison: outward first-error identity, stored first-error identity, later
fault metadata, cleanup and all 35 cases remain. No private runtime was performed
on the final source, and no private 35-case/105-phase pass is claimed.

Independent review verified all 21 child closures across the four attempts,
unchanged pinned helpers/environment and the before/after source identities.
Measured CPU was 49.863723 seconds; including four retained 5-second CPU and
10-second active-wall closeout holds, the cumulative charge is **69.863723 CPU
seconds and 89.96028027124703 active-wall seconds**. The final unit contains
2,401,856 logical bytes in 54 regular files and two directories, with no links,
FIFO or executed test fixtures. Separately sampled wall differences remain in
the private record. External authoring, review and transport costs remain
unknown; these numbers are not complete operation accounting.

No fifth local attempt is planned. Repeating source-bound preparation and full
typing would leave an estimated 20-second typing ceiling under unchanged
withholdings, below the observed 25.746082 typing CPU seconds, before the guarded
tests. This is a fit forecast, not a new measurement or balance reset. One
separately recorded ordinary hosted CI attempt will validate the frozen final
source. Its result cannot retroactively supply the private guard census.

Parent [PR #152](https://github.com/spei04/strange-physics/pull/152) passed its
original CI attempt: six required jobs, 5,875 tests per runtime, 221-file typing,
1,567 schema checks, package inspection and the existing reference/smoke checks.
Ordinary CI includes historical physics tests; it is separate from the pending
D1 scientific batch.

## Hosted CI verification

[PR #153](https://github.com/spei04/strange-physics/pull/153) passed original
[CI attempt 1](https://github.com/spei04/strange-physics/actions/runs/41183211071)
on frozen head `3ee39ee27053a7947e4f358bfc7a9c2d5a333cc3`. The tested merge
`63f8167b76e14abaf20e513d0ea117dded9f0b0e` has the exact parent/head pair and
the same source tree. All six required jobs succeeded; the protected-main
candidate job was skipped, as expected for this draft PR.

Both Python 3.12 and 3.14 passed 5,910 tests, full typing across 223 files, 1,567
schema checks with all references resolving, the package allowlist and one
8/8 CLI smoke run. Each separate analytic job passed 24 cases/72 phases.
The two existing serializer warnings per main runtime and the security tool's
flag warnings remain in the original logs. Independent review matched the
immutable source and original logs; 17 private evidence files total 445,255 bytes.

The 35 new cases are included in ordinary source selection and aggregate passing
counts. This does not create a private ordered 35-case/105-phase execution receipt:
the four-attempt local qualification above remains incomplete. Observed required
job durations sum to 1,532 seconds versus 4,980 configured timeout seconds.
Provider elapsed time was 777 seconds, a separate concurrent interval. These are
not CPU or billed-cost measurements; external costs and previous charges remain
retained. CI establishes engineering validation of this source, not source
authority, production readiness or a D1 scientific result.

## Remaining work

Source review and final-source ordinary CI are accepted. The local qualification
limits above remain explicit. Qualified storage behavior, external failure
retention/closure, actual source bindings and aggregate science-output fit remain
separate. Defer all candidate A construction and fixed `codec-activation.json`
retention until the resolved/authenticated S and outer-admission slice. This
operation supplies no S schema, source resolver, callable installation, history
inventory, exposure decision, activation or scientific result.
