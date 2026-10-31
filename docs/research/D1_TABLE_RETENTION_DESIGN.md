# Conditional D1 table retention and fresh C join

Design only, based on source parent
`72ec513dd4e05979effb2667e6c37b8d526682fe` (tree
`d867cfc1ff17daad682f8f53119be531284b78b6`). No implementation, file-retention
attempt, project import or test execution is performed by this proposal. The
parent records the accepted local context-observation checks; it does not
qualify the new operation described here.

| Read dependency | Exact source SHA256 |
| --- | --- |
| `tests/d1_primitive_sink.py` | `a0db630931c969c76de297e453c8c5f1cde8709c68dfcf1b44521c5e7055e325` |
| `tests/d1_primitive_codec_table.py` | `3f72f06ac924d254ca08008dd4690e8124bfa3bd188d5a2861fb1de221d36a38` |
| `tests/d1_codec_append.py` | `43ea859caed1e09301f2f94b24829ec6ad6b8714bd7f3fd99b91b1937260fc4c` |
| `docs/research/D1_PRIMITIVE_CODEC_CONTRACT.md` | `ec4be04622e57a9fb2fa7009830b62d71676f2f63faf2e658f7fe212579d9c8d` |

The [codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md),
[context observation design](D1_CONTEXT_OBSERVATION_DESIGN.md) and
[implemented observation scope](D1_CONTEXT_OBSERVATION.md) remain authoritative
for their respective boundaries. This slice changes no scientific plan, byte
ceiling, source-manifest meaning or activation requirement.

## Small operation and byte-only result

Propose a private `TableRetentionAttempt(metadata_root: Path,
sink: PrimitiveFileSink, table_raw: bytes)` with one `retain()` operation.
Construction performs no I/O. The instance exists concretely to own the metadata
fds, one attempted reservation, first/supplemental fault facts and the consumed
state; it is not a generic transaction, journal or execution framework.
`retain()` consumes the opportunity before its first validation/I/O. Same
PID/thread, no reentry and sticky failure apply. A nested failure swallowed by an
injected operation cannot allow the outer call to return successfully.

A successful call returns a frozen, slotted `TableContextObservation` containing
only `table_raw: bytes`, `table_sha256: str`, `table_bytes: int`,
`context_raw: bytes`, `context_sha256: str`, and `context_bytes: int`.
These are actual retained/read bytes and their computed identities. There is no
readiness, activation, authentication or unchecked flag; the result is not
consumed as authority elsewhere. Caller-constructed views and matching hashes
are not substitutes for this operation's actual reads.

The only retained new file is literal `identity-table.json`, under an exclusive
private sibling metadata root. No caller-selected table filename, source path,
extra journal, terminal file, export, temporary disk copy or A file is accepted.
The existing caller owns the sink and its separately once-only finish. The new
operation owns and closes only its independently acquired metadata descriptors.

## Enforce the sibling relation using actual owned descriptors

A caller's matching path strings are insufficient. Choose this narrow private
utility extension rather than duplicate `_Anchor` or introduce a general store:

* Add an optional `expected_parent: Identity | None = None` argument to the
  existing `_Anchor` constructor. After opening its own parent fd and applying
  existing owner/type/mode validation, compare its full actual
  `(st_dev, st_ino, st_uid, st_mode)` with the required identity **before mkdir**.
  A mismatch raises and closes that newly owned parent; no metadata root is
  created. Existing callers use the unchanged default and retain identical
  behavior, checks and ownership.
* The T operation must obtain the required identity itself after the first
  successful fresh `sink.observe_context()`. Read-only use of the actual sink's
  `_anchor.check()` and `os.fstat` on its existing parent/root fds binds their
  live identities to the sink's stored pinned identities and named entries.
  Do not accept an expected identity or snapshot supplied by the caller. Do not
  duplicate, close, adopt or store ownership of those borrowed sink fds, and do
  not change sink busy/stop/owner fields. Borrowed access is confined to this
  reviewed private integration; it is not a new public descriptor API.
* Require a normalized absolute metadata path and a distinct basename from the
  actual pinned sink root. Construct the metadata `_Anchor` with the actual
  expected parent identity. Its independent parent fd must designate the same
  parent object, and its newly created root must have a distinct device/inode
  from the sink root. Existing-root/name collision fails; never reopen it.
  The actual identity checks, not basename equality, establish the relation.
* Recheck the metadata anchor and actual sink parent/root identities at the
  write/read boundaries while they are open, and before metadata cleanup. A
  parent/root rename, substitution, missing name or changed identity fails.
  The final C observation rechecks the sink after all metadata fds are closed.

Checking a path in a preliminary probe and then reopening it without the
before-mkdir identity comparison would leave an avoidable check/use gap. The
optional constructor check is the only proposed shared-utility change; there is
no unrelated redesign or weakening of existing private-file checks.

The caller must keep this sink idle and exclusively owned throughout the
operation: no appended Events, finishes, other consumer or concurrent mutation.
Observation does not hold a sink lock across T I/O. The two fresh observations
and descriptor checks detect the covered intervening changes; they are not
hostile-Python isolation, a cross-process filesystem transaction or protection
against an actor that changes and restores state between observations. A
same-byte safe C replacement remains within the existing observation's limited
claim. No creation-inode continuity claim is added.

## Ordered successful path

1. Latch the attempt, validate exact immutable bounded T bytes with
   `parse_table`, and retain the source-owned fixed table view only internally.
   No constructed `TableView` is accepted at this boundary.
2. Obtain fresh C through the actual `PrimitiveFileSink.observe_context()`;
   call the existing pure `d1_codec_append._context(raw_C, parsed_table)`.
   This reuses its exact canonical flat C parser, seven shared identity joins,
   fixed 55,100/110,201 plan, eight-digit context number bound and unchanged
   metadata/fallback/partition limits. It creates no `CodecAppendBridge` or
   event cursor. C's declared sink hash and T's declared codec/source hashes
   remain declarations; neither is source authentication.
3. Establish the actual sibling relation above. Reserve the complete validated
   T length before creation/write, then create the exclusive metadata root and
   its literal T file. Use the existing `_Anchor` private open/check/sync/close
   semantics and `_write_remaining` positive-progress rule; no sink anchor is
   borrowed for writing. File mode is 0600, root 0700, no-follow/single-link and
   fd/name identity checks apply.
4. Write T once, check identity/extent, fsync its file and metadata directory,
   and close the write fd once. Read back only T through the metadata-owned
   anchor and existing bounded `_read_file`. Require exact equality with the
   previously validated bytes and compute the returned T identity from actual
   readback. Equality supplies canonical actual T without a second parse.
5. Check pinned identities and close all metadata-owned descriptors, including
   the temporary read fd and parent/root anchors. Every required write/sync/read/
   close must have returned without uncertainty. There are no metadata close
   callbacks remaining after this step. After every owned close has been
   attempted, check the T attempt's sticky active/reentry state **before** the
   final C observation. A close hook may swallow a nested `retain()` failure and
   return normally; that earlier failure still prohibits a second C read.
   Preserve its first fault while independently attempting all remaining owned
   closes; the latch check must not bypass cleanup.
6. Obtain the second fresh C observation, reapply `_context`, and require exact
   equality with the first C bytes and the same derived binding. Immediately
   before returning, check the T attempt's own sticky active/reentry state again.
   A hook in that final observation can swallow a nested `retain()` failure;
   correct C bytes do not erase the attempt's first fault or permit success.
   Only then return the byte-only result. No source resolution, candidate A construction,
   activation, Event append or primitive invocation occurs.

The fresh C reads occur exactly twice on the successful path. Failure before
step 6 does not trigger a compensating/diagnostic second read. A final C failure
can coexist with successfully written/synced T; the joint result still fails.
A later operation must perform its own current-state checks, not treat this
result as permission to resume or activate.

## Failure and cleanup semantics

Any input, ownership, sibling, creation, write, sync, readback or close failure
consumes this attempt. Preserve partial T and full attempted reservation; never
truncate, delete, recreate, rename over, retry or reopen an existing attempt.
Keep bounded in-memory phase, reserved/written extent, known completion and
first/supplemental exception facts. Their later external retention and byte/cost
accounting belong to the controller; this slice invents no serialized receipt.
Preserve the original first exception object, with bounded supplemental phase/type
records (at most 16 records, each type name at most 192 characters, plus an excess
count); do not replace it with a summary string or serialize arbitrary exception
messages/objects. These record bounds do not assert a bound on Python exception
heap size.

An `_Anchor` constructor can fail after mkdir or parent fsync but before returning
an anchor to the caller. Record creation entered and artifact/closure status as
unknown where unobserved; preserve the constructor's original exception and its
supplemental close notes. Do not claim that no root exists or that all descriptors
closed merely because construction raised. Do not reacquire, delete or retry
unknown descriptors/artifacts to manufacture a clean attempt. The external
controller later accounts for these retained unknowns.

Remember an operational primary error before cleanup. Independently attempt
once-only close of each owned fd, clearing its ownership slot before close; a
close that raises is uncertain and must not be retried. If there was no earlier
error, the first close error becomes primary; otherwise preserve it as a
supplement. Continue other owned closes without replacing the original error.
Even a real close followed by a synthetic error prevents success. In particular,
a failure while closing metadata means **no second C read**, no success return
and no automatic retry/delete. File presence, complete JSON or later inspection
cannot infer an acknowledgement that was not returned.

Do not mutate the sink's private stop state to simulate a transaction. The
caller remains responsible for one sink `finish()` on abandonment, preserving
its terminal acknowledgement and descriptor-closure uncertainty separately.
A metadata failure does not admit another operation or primitive. Per-object
consumption and exclusive file creation do not prove globally once-only use:
registration and no-retry enforcement across replacement objects/controllers
remain outer admission obligations.

## Unchanged reservations and bounded work

| Item | Existing bound / required accounting |
| --- | --- |
| T bytes | At most 57,856, including canonical LF; reserve its full validated length before I/O, including unknown partial delivery. |
| T/A reservation | 65,536; T uses this existing pool. No A is constructed here; its existing 4,096 ceiling and combined 61,952 upper bound stay unchanged. |
| Temporary retained T/A copy | Existing 65,536 reservation remains withheld; this direct-write operation uses no disk copy and does not reassign that capacity. |
| Actual C reads | Two successful-path reads of at most 4,096 each. C is already retained under the sink's existing context reservation; no second C file is written. |
| T readback | One read of at most 57,856; T plus both C reads total at most 66,048 payload bytes. |
| Successful syncs | Three: new metadata-root parent, T file and metadata directory. Failure/cleanup work is additionally counted, not refunded. |
| Sink metadata / rotation | Existing 20,480 context-plus-terminal reservation and 65,536 rotation withholding are unchanged; neither is a fresh T budget. |

One T parse includes fixed-row checks and canonical encodings. Existing `_context`
revalidation happens twice, and both `observe_context` calls repeat canonical
context validation, byte comparison and hashing. Under the proposed direct
reuse, there are two T SHA256 evaluations (input parser and actual readback) and
four C SHA256 evaluations (two observations and two `_context` validations).
Do not silently call these repeated validations free or remove a boundary merely
to match an optimistic census. A final implementation must confirm these counts.

Positive short writes continue only that same attempted file; at least one byte
of progress bounds write iterations by `len(T) <= 57,856`. Each bounded read loop
also permits at most its file length in positive one-byte reads. Zero progress,
early EOF, error or interruption stops. Per-iteration active/identity checks,
stat calls, hashing, parsing, transient chunks and cleanup are real work, not
constant-time metadata bookkeeping. Exact helper/syscall census and engineering
runtime allowance follow authored source; no numerical allocation is requested.

Account these in-memory operands separately from disk reservations:

* Original immutable input T is held once; parser `TableView.raw` aliases those
  bytes, while decoded JSON containers, immutable rows and expected fixed rows
  are additional objects. Canonical row/header/root encodings are transient
  allocations, not free references.
* T readback chunks have aggregate payload at most 57,856 bytes; their joined
  actual T is a separate bytes allocation. Both can briefly coexist with input
  T. Hashing/equality and parser work are counted separately from writing T.
* The two C observations each hold at most 4,096 actual bytes. Their read chunks,
  joins, canonical-validation temporaries and `_context` parser/binding objects
  are additional transient allocations.
* The result holds references to actual readback T and the final C bytes; it does
  not encode another table/context copy. The first C and input T may still be
  live in the attempt/call frame. No growing read/observation history is retained.

These are bounded encoded operands, not a proved Python heap bound. Any
serialized snapshot, export or retained copy would consume the existing
copy/output pools and needs separate review. This slice adds none. Filesystem blocks, control logs, failure summaries and later
readbacks still need their explicit controller accounting. No new S byte budget,
16 MiB allocation, whole-science fit or refund follows from this design.

## Focused implementation and test boundary

The next coherent source slice is a private T-attempt helper, the narrow optional
`_Anchor` parent check, focused synthetic temporary-file tests and a scope guide.
No decoder, scientific producer, source resolver or activation API is needed.
Tests should cover these distinct behaviors before any runtime qualification:

* Exact T/C success and ordering, with final C read after all metadata fds close;
  existing sink anchor fds remain owned/open, and no Event or A file appears.
* Invalid/noncanonical T or mismatched C identity/limits before metadata creation;
  initial non-idle/stopped sink cannot start T retention.
* Actual different parent rejected before mkdir, distinct-root/name collision,
  and same-parent root substitution/rename rejected by descriptor/name checks.
  Existing `_Anchor` callers retain unchanged default behavior.
* Intervening sink append/C change prevents final join; supplied observation
  objects or matching declared hashes cannot replace actual C reads.
* Positive short write/read, zero progress, interrupted/partial write, file-fsync
  and directory-fsync failure, T readback substitution and read-fd close failure.
* Original failure plus supplemental close failure; owned real-close-then-error
  leaves no descriptor leak but no success/second-C read; all other owned closes
  are attempted once with mocks restored before caller finish/pytest teardown.
* A metadata-close hook swallows nested `retain()` failure and returns normally:
  retain the first fault, independently attempt every remaining owned close,
  then reject before any second C read. No close or retention retry is allowed.
* Wrong-owner/reentrant attempt, including a swallowed nested failure during the
  final C observation, consumes the object; repeated `retain()` does no further
  I/O. Failed files stay intact.
* Constructor failure after root creation preserves an entered/unknown outcome
  and supplemental close facts even when no anchor object is returned.

Freeze exact authored cases, file/copy/output bounds and helper source pins
before a separately reviewed engineering run. Temporary-file tests establish
conditional software behavior, not power-loss durability or hostile-actor safety.

## A and source authority remain later

Defer candidate A construction completely. There is no fixed
`codec-activation.json` or alternative unchecked-A schema in this unit. A later
resolved-S/admission slice must establish immutable accessible S, actual source
members/callables, exact retained T/C/S joins, A retention and outer binding before
activation. It needs its own bounded S producer/resolver/read/copy contract;
matching source hashes here do not supply one. The accepted acyclic S -> T/C -> A
meaning and every existing scientific prerequisite remain unchanged.
