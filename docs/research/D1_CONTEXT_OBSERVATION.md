# D1 owned context observation

Source-only implementation of the accepted
[context observation design](D1_CONTEXT_OBSERVATION_DESIGN.md), based on
`c8ea6092b63b65ee3ffff8caac95af39e8d6b92d`. The new tests are authored but have not
been imported, collected or executed. Formatting, lint, configured typing and
finite engineering validation remain pending. No scientific or operational
qualification follows from this source checkpoint.

## Exact scope

`tests/d1_primitive_sink.py` adds a frozen, slotted `ContextObservation` with
`raw: bytes`, `sha256: str`, and `byte_length: int`, and the narrow method
`PrimitiveFileSink.observe_context()`. All other sink helper/method bodies remain
unchanged. The new test module is `tests/test_d1_context_observation.py`.

The result describes actual bounded C bytes, not source authenticity, historical
inode continuity, codec readiness or admitted authority. No consumer accepts a
caller-constructed observation as proof. Observation does not create a file,
reserve an Event, invoke a primitive, transfer an anchor or finish the sink.

Entry reuses the sink's same-PID/thread, non-reentry, unconsumed and canonical
context checks. `_enter(finishing=False)` stays outside the acquired-operation
try/finally, so a rejected nested call cannot clear the outer busy flag. Zero
reserved Events are required before C I/O. Prior close faults or closure
uncertainty stop the operation before another read.

The existing pinned anchor reads only `context.json`, with the existing 4,096-byte
limit and current fd/name, ownership, single-link, mode, extent and timestamp
checks. Actual bytes must equal the stored canonical C bytes exactly; no parser
or DTO roundtrip is added. The temporary read fd remains owned by `_read_file`.
Parent/root descriptors stay with the sink and its separately once-only finish.

A primary observation/read error is remembered before supplemental close faults
are drained. An earlier sticky fault remains first. Lost read-fd close
confirmation prevents return and future append even when the injected close
actually released the descriptor. The acquired finally only releases busy state.
A swallowed nested observe/append cannot recover an outer success: active/reentry
state is checked immediately before handoff. No retry, reset or second read is
performed after a failure.

Repeated successful idle observations are allowed, with fresh bounded reads,
comparison/hash work and read-fd cleanup each time; no observation history is
stored. The sink never stored C's creation inode. An otherwise safe same-byte
replacement before a read can pass; the test explicitly preserves this limited
claim rather than pretending to detect all historical replacement.

## Authored tests and work estimate

The source has **25 cases in 10 test functions**, with explicit short parameter
IDs; a future ordinary pytest run would produce 75 setup/call/teardown phases.
These are static counts, not observed outcomes.

| Family | Cases | Distinct checks |
| --- | ---: | --- |
| Idle success/repetition and positive short reads | 2 | Actual bytes/hash/length, frozen/slotted result, no Event changes, fresh reads and unchanged anchor ownership. |
| Ineligible state | 4 | Reserved, stopped, finished and changed model reject before C read; no resumed append. |
| Wrong owner | 2 | PID/thread mismatch stops and closes anchors on finish without promising terminal acknowledgement. |
| Swallowed reentry | 2 | Nested observe/append preserves outer busy state and blocks bytes despite the reader returning normally. |
| Changed/unsafe C | 7 | Contents, spelling, oversized extent, symlink, hardlink, missing file and FIFO fail closed. |
| Identity/time limitations | 2 | Safe identical-byte replacement is allowed; within-read timestamp mutation fails even with identical returned bytes. |
| Read/close faults | 4 | Read, real-close-then-error, both, and early EOF; first/supplemental identity, actual fd closure and uncertainty remain separate. |
| Prior closure state | 2 | Previously retained close error or explicit uncertainty blocks a fresh read. |

The test source constructs 25 owned sinks and makes at most 39 observation calls,
including rejected and deliberately nested calls. At most 18 reach the bounded
C-read helper; their payload bound is `18 * 4096 = 73,728` bytes, not a measured
read total. The positive-short-read case permits one-byte progress, so one read
loop may make up to 4,096 reads. Each actual observation attempt also performs
entry/context validation, identity/stat checks, equality and (when reached) one
SHA256 operation. Temporary chunks, joined bytes, immutable results and returned
copies are work; these encoded-byte estimates are not Python heap/time bounds.

Each case reserves a conservative **32,768 bytes of temporary payload**, or
**819,200 bytes** over all 25 cases. This covers its C/terminal files, tiny raw
append where used, changed/oversized C, one extra private target/link or transient
replacement, and partial failure files. No 4 MiB shard fixture is used. Filesystem
metadata, pytest/JUnit/logs, source, control files and any copied artifacts must be
counted separately in the later engineering plan. This is not measured output or
permission to borrow from another allocation. Assuming every case's temporary
files are retained, the source-level final upper census is 25 sink roots plus
25 pytest-owned parent directories, 50 regular-file names (including one extra
hardlink name), one symlink and one FIFO. The hardlink shares an inode; its bytes
still count per retained name. Across setup/cleanup transitions there are at most
53 regular-file creations plus that hardlink name, including the temporary
same-byte replacement and symlink target. Missing/replaced original C files are
not silently refunded from the per-case payload estimate. The FIFO has zero file
payload; symlink target bytes and directory metadata remain distinct census items.
These are source bounds, not observed filesystem measurements.

Shared OS mocks are scoped to the observation and restored before finish and
pytest temporary cleanup. Close-fault tests first close the exact captured read
fd normally, then raise one synthetic EIO; other descriptors pass through. Tests
assert the temporary fd is actually closed while `descriptors_closed` honestly
remains false when confirmation is uncertain. An owned fixture closes anchors
once on failure paths and checks actual EBADF; no ambiguous close is retried.
Wrong-owner/reentry tests separately preserve the possible unacknowledged
terminal write. Test-body import guards exclude named scientific producers;
future reviewed controls still supply execution boundaries, not a Python sandbox.

## Still separate

The [conditional handoff](D1_CODEC_HANDOFF.md) and
[codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md) keep their existing limits.
No real recorder/bridge installation, T writer, activation writer, source resolver,
protected inventory or scientific work is added here. A later finite operation
may retain T under separate sibling-root ownership and join it to fresh actual C
observations; its aggregate read/copy/work budget must be declared separately.

Do not write fixed `codec-activation.json` from unchecked S. The exact A schema
has no unchecked/admitted-false escape field. Actual S/member/callable resolution,
source authority and outer admission must precede the later activation workflow;
C alone authenticates neither S nor A. No new S budget, scientific allocation,
whole-transcript fit or power-loss durability claim is introduced.
