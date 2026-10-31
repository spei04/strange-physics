# D1 primitive file sink

Synthetic filesystem checks accepted, 2026-10-31. The private helper
[tests/d1_primitive_sink.py](../../tests/d1_primitive_sink.py) implements a
synchronous file callback for the unchanged [primitive recorder](D1_PRIMITIVE_RECORDING.md).
All 59 synthetic cases and full 213-file typing passed at
e76284a3c5e950783c4d25c6cb14d22b50398d11, with independent outcome review.
This does not install instrumentation, run an actual primitive, authenticate
source, admit a batch, complete the report binder or establish production or
power-loss durability.

## Contract and ownership

`PrimitiveFileSink.create(root, context)` creates one new owner-private root.
`SinkContext` accepts only opaque recorder/run IDs, source commit/tree, protocol,
source-manifest, recorder and sink SHA-256 identities, `max_calls`, and total
`max_bytes`. Exact types are checked before JSON encoding: booleans cannot become
integer allowances. No arbitrary payload, path, truth, verification flag or
caller-selected derived ceiling is accepted. These pins are declared identities;
the future execution binder must compare them to actual retained source bytes.

The context is compact sorted-key ASCII JSON plus one newline, with nonfinite
values rejected. It is not JCS. Its exact bytes are retained as `context.json`.
The sink rechecks the original context before each append and uses frozen private
limits for allocation. No source or scientific input is read from these hashes.

The writer owns one PID, one thread and one new directory; reentry, another
owner, a previous finish or a previous append failure prevents further append
work. `finish()` consumes its opportunity before cleanup or terminal writing.
No existing directory, even an empty or interrupted one, may be reopened for
writing. There is no resume, reset, retry, truncation or deletion operation.

The immediate parent must already be trusted and private. Creation pins its
open directory descriptor and device/inode/UID/mode, creates the child relative
to that descriptor, and pins the child similarly. Every file has a generated
name and is opened relative to the pinned root with exclusive creation,
no-follow and close-on-exec flags. Reads also use nonblocking opens, then reject
nonregular, public or multiply linked files. Descriptor/name identity and
extent are checked; root/parent replacement is rejected at the authorization
boundaries. `workflow_io.private_stat` and its preliminary `safe_path` check are
reused, with the missing descriptor/name and link checks implemented locally.
These checks assume a trusted private namespace and exclusive cooperating
writer. They are not a hostile-owner filesystem sandbox or a proof against all
possible kernel/filesystem failures.

## Exact byte and event limits

All allowances must be explicit. The total domain ceiling remains 64 MiB; it
is not a run allocation or a claim that the full transcript fits. The context
fixes these derived limits:

| Item | Fixed bound |
| --- | ---: |
| Context reservation | 4,096 bytes |
| Terminal reservation | 16,384 bytes |
| Event capacity | `max_bytes - 20,480` |
| Raw event | 4,096 bytes, including its single final newline |
| Shard | 4 MiB |
| Shards | 16 |
| Calls | `1 <= max_calls <= 55,100` |
| Events | `2 * max_calls + 1`, at most 110,201 |
| Named files | At most 18: context, terminal, 16 shards |

A successful recorder call emits intent and return. The one extra event covers
its final failure path, including allowance exhaustion after successful calls;
no additional scientific invocation is implied. The sink stores opaque exact
line bytes, not a second event schema. A complete line is not automatically a
valid recorder event; later transcript parsing must join its actual sequence,
call/instance/scope/argument/return semantics and complete primitive census.

Each append reserves the complete event's bytes and ordinal before filesystem
work. A failed append retains that reservation even if zero bytes were written.
`reserved_bytes`, `confirmed_bytes` and `written_bytes` in the snapshot describe
event bytes only; the fixed 20,480-byte metadata reservation is additional inside
the same total. `written_bytes` counts positive write-return observations, not
unknown bytes written before an exception. Inspection separately measures actual
retained file extents. Metadata, partial files, unconfirmed events and copied
outputs must all remain in the later physical-output ledger; no equal-hash copy
is free. Filesystem blocks, directory metadata and in-memory copies are separate
from these logical-byte counts.

The 16 by 4 MiB ceiling is not 64 MiB of payload permission. Shard tail slack and
the fixed metadata reservations can cause earlier exhaustion. The proposed
16 MiB transcript partition from the
[report design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md)
cannot hold the complete successful raw JSONL transcript: field names and
punctuation alone require 16,860,600 bytes, 83,384 bytes above that partition.
The [source-bound calculation](D1_TRANSCRIPT_BYTE_FIT.md) preserves the fixed
55,100-call plan and distinguishes full success from partial failure. Actual
64 MiB whole-science fit and a lossless compact representation remain unproved.
The unchanged sink does not supply a codec. A reviewed representation must fit the
unchanged allocation; never drop intents/returns or increase a cap silently.

## Append, failure and closeout

A new shard is created exclusively, its empty file is synced, then its directory
entry is synced before event writing. An append writes its exact bytes, checks
the pinned extent, fsyncs the data file and rechecks identities before confirming.
Positive short writes continue only the remaining portion of the same event.
The loop uses at most `len(raw)` write calls, because each return must advance
by at least one byte and never exceed the remaining buffer. Zero progress,
invalid counts, exceptions and interrupts stop immediately. There is no retry
of the logical append or primitive.

Any append error permanently stops append operations. The original exception
object is retained; bounded safe type/phase facts are separate from supplemental
close or retention failures. Exception arguments, arbitrary stringification and
tracebacks are not serialized. The snapshot stores up to 16 fault facts and
explicitly counts omitted supplemental facts. Partial files are preserved.
A failed fsync means unknown delivery even when the complete line is readable.
The recorder's attempt to append a failure event after a sink failure is rejected
without further write I/O; its own in-memory unknown/fault-retention facts remain
available to the enclosing driver.

`finish()` is a separate once-only terminal attempt, available after append
failure. It closes the active descriptor without retrying an ambiguously failed
close; reads bounded actual shard bytes for hashes, complete-line counts and
trailing-fragment sizes; and attempts `terminal.json` exclusively within its
reserved limit. A failed read produces an explicit unavailable observation.
First and supplemental faults remain distinct; all descriptor-close uncertainty
is propagated. No failure becomes a fabricated successful event or a refund.

The terminal file records `pending_external_confirmation`. It contains a snapshot
from before its own write and cannot attest to its own fsync or final descriptor/
process closure. The in-process `SinkCloseout` separately reports whether that
terminal write was acknowledged and whether descriptor closure was confirmed,
plus the latest snapshot. `SinkCloseout.terminal_sha256` identifies the intended
terminal bytes even when only a partial write is retained; `inspect_sink` instead
hashes the actual observed bytes. Neither flag is scientific success. A terminal write,
fsync, close or anchor failure can leave a partial or absent terminal file. There
is no replacement receipt or recursive failure-writing loop; external closeout
must retain the remaining unknowns. All calls still require an external bounded
service deadline; source-level loop counts do not bound blocked filesystem I/O.

## Read-only inspection

`inspect_sink(root, max_bytes=...)` pins a fresh read-only view, lists at most 19
entries to detect excess files, accepts only the generated names, and requires
contiguous shard indices. It bounds file reads by both per-file and remaining
aggregate allowances and rechecks inode, extent and modification metadata.
Raw line scanning uses advancing newline offsets, not a list of every line.
It enforces the global event-count and line-size ceilings without parsing or
recomputing scientific data.

A missing, partial or noncanonical context is visibly unconfirmed. Terminal bytes
are reported only as present-unconfirmed or missing. An orphan intent cannot
establish whether a primitive executed; a readable return cannot establish the
original caller received it. A trailing fragment, empty shard or partial terminal
remains evidence of incompleteness. The inspector always reports execution and
acknowledgement as `not-inferred` and authenticity as `unchecked`. It never resumes,
repairs, deletes or promotes recovered material to a successful original run.
A later binder must also authenticate actual bytes against independently retained
identities, parse the event schema, and reconcile process/service outcomes.

## Verified synthetic checks and operation accounting

The 26 test functions passed all 59 synthetic cases and 177 ordered
setup/call/teardown phases in the bounded engineering checks. They cover strict context/limits; exact byte retention;
private/exclusive paths; positive short writes and zero progress; partial writes,
interrupts and fsync failures; primary plus close failure; recorder intent failure
with zero invocation and return retention failure without a primitive failure;
file/root substitution, hard links and FIFOs; PID/thread/reentry rejection;
consumed finish; and bounded recovery without acknowledgment inference. Focused
regressions require parent-directory fsync before context writes and zero further
stat/open/write/fsync calls after a failed append, including the recorder fallback.

Rotation/count tests substitute only test-local 8/3-byte shard limits and a
2-shard limit, restoring them before teardown. Separate checks pin the actual
4 MiB/16-shard context constants. These small fixtures exercise the boundary
logic without allocating full 4 MiB shards. One case writes exactly 4,096 event
bytes; other cases write only small synthetic lines. A conservative source-only
retained test-file estimate is below 1.5 MiB: at most 59 directories, each bounded
by 20,480 metadata bytes plus 4,096 synthetic event bytes and 64 substitution/
orphan bytes. Actual counts/bytes, pytest artifacts and engineering-control files
were measured under the engineering allowance; this initial estimate is neither
total observed engineering output nor full scientific-transcript fit. Maximum context and terminal
shapes are tested by pure encoding without sixteen data files. No test calls an
actual oracle, predictor, simulator, historical reader or protected inventory.
Shared `os` monkeypatches use scoped contexts so temporary-directory teardown
sees the original functions.

For E successful appended events across S shards, data writes use between E and
sum(event lengths) positive-return calls; each event has one data fsync, and each
shard creation adds one empty-file fsync and one directory fsync. Context and
terminal each add their bounded write loop, one file fsync and one directory
fsync; creating the root adds one parent fsync. Finish and inspection separately
read/hash actual bytes, count bounded lines, and close their descriptors. Every
partial write, unsuccessful fsync, metadata attempt, repeated inspection and
failure branch must appear in the final work manifest. This conditional source
census does not measure latency, device writes, CPU cost or power-loss behavior.

Initial source authoring used AST parsing, inspection and Git whitespace
checks only. An over-specific edit-script assertion stopped after its helper
edit; that diff was inspected and the test edit completed separately.

Subsequent bounded engineering retained two failures: initial collection
rejected a 4,185-character automatically generated test ID, and full typing
rejected reuse of an exception-target name in a cleanup loop. Descriptive IDs
and a distinct loop variable repaired those issues without changing test
values, assertions or sink behavior. Both failed attempts remain in the ledger.

The final check passed formatting, linting, full configured typing across 213
files, all 59 cases and all 177 ordered phases, with no skip, xfail or forbidden
entrypoint attempt. Independent review joined source, environment, collection,
raw phase records and JUnit, and confirmed all 29 child closures across five
attempts. The cumulative charge was 104.997527 CPU seconds and 131.587996 active
wall seconds within the unchanged 120/300-second engineering limits.

Retained output was 3,009,024 logical bytes: 3,005,264 regular-file bytes plus
3,760 bytes belonging to 27 symlinks, with one zero-payload FIFO and 113
directories separately counted. The census never followed links or opened the
FIFO. Both earlier control snapshots, failures and partial records remain.
Filesystem-block usage, external authoring/review/publication costs and
whole-operation accounting are not established by that logical-byte count.

Lossless codec fit, scoped primitive installation/restoration, actual source
authentication, complete material binding, operational closure and numerical
admission remain pending.
