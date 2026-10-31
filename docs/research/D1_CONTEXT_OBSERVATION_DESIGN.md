# Owned idle sink context observation

Proposed source prerequisite only; no method is implemented or executed here.
This document is based on `8e4bb1224e68dfad74fe448a3ec310b9ed91b543` and the exact
`tests/d1_primitive_sink.py` bytes with SHA256
`2a72b57fe71a81f5ec44dfd38572c115cd1201ae1311422e577d00a02c14ac96`.
The [conditional handoff](D1_CODEC_HANDOFF.md), [append design](D1_CODEC_APPEND_DESIGN.md)
and [codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md) retain their existing scopes.
No source/activation authority, scientific allocation, new S budget or numerical
result follows from this proposal.

## Small interface and result

Add only `PrimitiveFileSink.observe_context() -> ContextObservation`, with a
frozen, slotted output carrying `raw: bytes`, `sha256: str`, `byte_length: int`.
The hash and length are computed from the actual returned bytes, bounded by the
existing `CONTEXT_BYTES=4096`. There is no path, descriptor, anchor, mutable
SinkContext, readiness flag, verification flag or caller-selected limit in this
result. It is an observation, not a source/authentication or admission receipt.
A caller-created result is never accepted as proof of a later read or join.

The method uses the existing sink object and its pinned `_Anchor`; it does not
reopen the root by path, construct a second sink, create metadata, append an Event,
invoke a primitive, activate the codec or finish the sink. The existing owner
retains responsibility for its separately once-only `finish()`.

## Entry, exact bytes and failure ordering

1. Call the sink's existing `_enter(finishing=False)` **outside** the acquired
   operation's try/finally, as `append` does. Require the same PID/thread, no busy
   operation, no stopped/finished state and unchanged canonical context model.
   A rejected nested `_enter` must not clear the outer operation's `_busy` flag.
2. After successful entry, require zero reserved Events before opening C. Even
   an append that reserved an Event but wrote no bytes is not an idle context
   observation opportunity. Non-idle misuse stops the sink before further I/O.
   Previously retained close faults or `closure_uncertain` must also block the
   observation; they cannot be treated as a fresh clean read.
3. Read only literal `context.json` through
   `_read_file(self._anchor, "context.json", CONTEXT_BYTES)`. That helper owns its
   temporary read fd and checks the current fd/name identity, owner, mode, link
   count, extent and within-read mtime/ctime using the existing pinned root.
   Do not expose or close the root/parent anchor descriptors.
4. Require the actual bytes to equal `_context_raw` exactly. `_enter` has already
   validated that the current typed context serializes to those stored canonical
   bytes. This exact equality establishes canonical actual C without a new JSON
   parser or lossy DTO roundtrip. Any additional parser would need an explicit
   bound and cannot replace byte equality.
5. Drain supplemental close faults, reject any closure uncertainty, construct the
   bounded immutable observation, then check the sink's sticky active/reentry
   state immediately before returning. An injected reader can call a nested
   append/observation, catch its error and return bytes: those bytes must not
   escape as a successful observation after the sink has been consumed.
6. Clear `_busy` in the acquired operation's finally. No return in finally, reset
   of stopped/invalid-owner state, second read, retry or anchor transfer is allowed.

On any primary observation/read/validation error, record that error with the
sink's `_remember` **before** draining `_anchor.close_faults`. Thus simultaneous
read and read-fd-close failure cannot make the later close error the first fault.
Preserve an already latched earlier error, such as reentry, rather than replacing
it with a later exception. Drain supplemental closes on every acquired-operation
path. A read-fd close that succeeded but lost confirmation still prevents a return
and all later append work. Cleanup failure must not mask the original error.
Do not retry an ambiguously closed fd; `_read_file` owns its existing close path.

This method must use the sink's fault/stop machinery, not merely propagate
`_read_file` errors: that helper can mark anchor close uncertainty without itself
stopping `PrimitiveFileSink.append`. There is no public safe observation boundary
until this composition is implemented and qualified.

## Repeated observations and ownership limits

Repeated successful observations are allowed while the sink remains idle and
unconsumed. Later T/C/A construction may need separate checks before retaining T
and before retaining A. Each call performs a fresh bounded read, equality check,
hash and close; it is not a free cached receipt. The sink retains no observation
history or growing list of byte copies. Aggregate observation/copy counts and
finite caller allowances must be declared by that later unit, not invented here.
An observation failure consumes the sink and cannot be retried as another success.

The caller may still invoke the existing `finish()` once to close the sink after
an observation failure. Wrong-owner/reentry rejection sets `_invalid_owner`, so
finish can close anchor descriptors while its terminal write fails through
`_check_reentry`. Tests must keep `terminal_acknowledged`, actual descriptor
closure, intended/observed terminal bytes and external confirmation separate;
terminal acknowledgement is not guaranteed in every error case.

The existing sink stores C bytes, **not C's creation inode**. Within-read fd/name,
extent and timestamp checks plus equality with stored canonical bytes do not
prove inode continuity since creation. An otherwise safe identical-byte replacement
before observation can pass; do not describe it as historically detected or
source-authenticated. Requiring creation-inode continuity would be a separate
reviewed storage/interface change, not a hidden assertion in this method.

## Bounded work and candidate tests

One call has at most one bounded C file-read attempt, with at most 4,096 payload
bytes. Existing `_read_file` rejects excess size before payload read, premature
EOF and changed extents/timestamps; positive short reads are allowed, and
one-byte progress bounds its
read loop by the file length. The method adds one byte equality and one SHA256
computation, plus canonical context validation already performed by `_enter`.
Stat/identity checks, transient chunk copies, hash/output bytes and failure cleanup
are real work. Encoded-byte bounds are not a measured Python heap or wall-time cap.
No Event reservation or fixed scientific byte/call limit is changed.

The smallest next code unit is the method and immutable output in the existing
private sink helper, a focused observation test module, and a scope guide. Reuse
the existing helper semantics; do not add a generic resolver/framework. Tests use
small owned temporary C files and scoped faults, never actual primitives or S:

| Family | Required assertions |
| --- | --- |
| Idle success and repetition | Exact sink-created bytes/hash/length; zero Event counters; repeated fresh reads; no retained observation history. |
| Non-idle/stopped/finished | Reject before C I/O; preserve original stop facts; no later append or implicit retry. |
| Wrong owner and swallowed reentry | Nested entry cannot clear outer busy state; caught reentry cannot return C; cleanup/terminal outcomes remain separate. |
| Changed or unsafe C | Changed contents, symlink/hardlink/type/extent or within-read mutation fail with first fault preserved and sink stopped. |
| Read plus close failures | Primary read error precedes supplemental close error; close-after-success synthetic uncertainty returns no observation; temporary fd actually closes. |
| Canonical/content boundary | Equal stored canonical bytes pass without parsing; altered JSON spelling fails; same-byte safe replacement demonstrates the explicitly limited continuity claim. |
| Cleanup ownership | Only the C read fd belongs to observation; anchor stays open on success, caller finishes once; no descriptor leak, reopen or second finish. |

Write/read/close mocks must target only owned files/fds or the defining helper and
restore before unrelated cleanup and pytest teardown. A synthetic lost close
confirmation may call original close then raise once for that owned fd, preserving
actual closure and reported uncertainty separately. Exact case count, counters,
retained temporary-file/log ceiling and runtime guard pins follow authored source;
no test or allocation is admitted by this matrix.

## Follow-on metadata boundary

After this prerequisite is qualified, a separate finite operation can retain T
exclusively in a sibling metadata root and join it to actual C observations.
Its metadata owner must have separately opened descriptors; it must not adopt or
close the sink's anchor. Reserve and account T, partial files, copies, readbacks
and failures under the existing codec reservations. No extra T/A file belongs in
the unchanged sink root or Event stream.

Candidate A may be constructed in memory while readiness remains unavailable.
Do **not** write the fixed `codec-activation.json` from unchecked S declarations.
A's exact current field set has no metadata-only/admitted=false escape flag, and
adding one would change the contract. Actual A retention remains a later
source/admission workflow: resolve immutable accessible S and actual source-member/
callable proof, retain A, then bind and validate its exact retained bytes through
outer admission before any activation. Preserve the existing C source-manifest
binding to SHA(S) and the accepted acyclic S -> T/C -> A order; C alone does not
authenticate A. The bounded S producer/resolver, actual length/read/copy contract and authority
join remain unfinished. This document supplies none of them and introduces no
new S budget or scientific execution permission.
