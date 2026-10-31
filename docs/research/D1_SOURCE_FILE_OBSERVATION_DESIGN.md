# Proposed first-pass D1 checkout-file observation

Assignment: Research owns this one design document after the source-only Unit17
handoff `e6b222a80cb9013e1f69cd8136c1a8c28f74b9b1` (tree
`0e2e45060931744ce6f4c44bab75120f2a20c779`). Lead owns the central board and A.
The proposed next PR is one private checkout-file helper, owned-fake-file tests
and a scope note. No implementation, imports, tests, filesystem fixtures,
scientific work or allocation are performed here.

Reuse [the accepted S design](D1_SOURCE_MANIFEST_DESIGN.md) and
[the declaration parser](D1_SOURCE_MANIFEST.md); do not reproduce its broader
catalog/installation contract. Split filesystem observation from loaded-object
provenance. A successful file observation is not a completed S pass1, authenticated
source set, loaded-code proof, release, or permission to construct/activate A.

## Small concrete interface

Propose `tests/d1_source_files.py` with these private, frozen/slotted records and
one synchronous owner. The exact records are local interfaces, not new serialized
receipts, signatures or a protected-plan producer.

* `ExpectedCheckoutFile(member_id, locator, loaded_module, sha256, byte_length)`.
* `ExpectedCheckoutPlan(source_commit, source_tree, catalog_ref, files)`.
* `RootIdentity(device, inode, uid, mode)` from an independently established root.
* `CheckoutObservationAttempt(catalog_raw, plan, *, root_fd, expected_root)`;
  constructor performs no I/O. `observe()` consumes this instance once and returns
  `CheckoutObservation`. `snapshot()` reports bounded attempt facts without I/O.

The inputs are exact immutable catalog bytes and exact fixed record types, never
an S view or caller-created parser view. Revalidate every raw field and copy the
validated primitives into owned immutable records before using them. Reject
mappings/extra fields, subclasses, mutable/arbitrary iterables, booleans in integer
fields, missing slots and coercion. Plan commits/trees are 40 lowercase hex;
`catalog_ref` and member IDs use the accepted 1–32 opaque lexicon. Locators and
module declarations use the catalog's 160/128-character rules. SHA256 is lowercase
64 hex; file lengths are positive and obey the existing ordinary/catalog 131,072
or literal-lock 262,144 ceilings. `files` is an exact tuple with at most 64 rows.
Its declared text is bounded by
`64 * (32 + 160 + 128 + 64) + 40 + 40 + 32 = 24,688` ASCII characters, plus 64
bounded length integers and fixed record/container overhead. This is not a heap
measurement. Root fields are exact nonnegative kernel-identity integers carried
within unsigned 64-bit bounds for this proposed Linux-only carrier; `mode` is
`stat.S_IMODE(st_mode)` and directory kind is checked separately. `root_fd` is an
exact nonnegative signed 32-bit descriptor number, not an ownership grant.

Call `parse_catalog(catalog_raw)` once. Require the plan's IDs, order, locators
and module declarations to equal **all and only** its `checkout_source` members,
including the mandatory root locators and lock policy. The plan's `catalog_ref`
must name one checkout member whose protected expected SHA/length equal the
actual supplied catalog bytes; that row also obeys the ordinary catalog cap.
The catalog has no embedded hashes, so this expected-plan -> catalog relation is
acyclic. Reject missing/extra/swapped plans and duplicate identities/locators.

The plan/catalog pins and their completeness/provenance must come independently
from the outer reviewed source plan. A caller deriving expectations from the same
files and signing or typing them does not establish that premise. No protected
whole-S hash is assumed: source bytes can be observed before S is built/sealed.
Fixed S protocol/root-hash joins still belong to later S construction/parse; fake
expected pins prove only owned-file observation and need not pretend to be a
sealable scientific source set. Source commit/tree labels are not verified by a
Git invocation here. The helper does not enumerate a repository or discover files.

The caller supplies an already-open, independently pinned checkout directory FD
and keeps it open and stable through the call. Validate its fstat identity, owner
and mode, then obtain an independently owned reference with the fixed
`os.open('.', O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=root_fd)` and compare
its identity. Never close/transfer the borrowed FD. This validates the actual held
root inode, not a matching pathname string. Acquiring and binding that FD to an
approved named checkout, its external ancestors and immutable interval remains
an outer prerequisite; root rename/history is not inferred from its descriptor.

## One bounded observation sequence

Consume before parsing or I/O, record PID/thread ownership and latch reentry or
wrong-owner faults. A rejected nested entry must not release the outer busy flag.
After every work call, check sticky state before another observation operation.
Sticky faults stop observation work, but never suppress the remaining independent
owned-FD closes. A later call on the consumed instance rejects before any work or
cleanup; it cannot close the borrowed root or repeat an earlier close. This is a
reviewed single-owner interval, not hostile-Python or concurrent-writer isolation.

1. Validate raw inputs/plan/catalog before acquiring any owned descriptor. Reserve
   the complete planned checkout-read envelope; failure does not authorize a new
   attempt or refund/reallocate a hold. Record entry to each open/read before it.
2. Visit checkout members in catalog order. Walk each canonical locator from the
   owned root, opening directories relative to their actual parent descriptors
   with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`; hold that complete chain for this file.
   Validate each directory's fstat/named identity before descending. Every named
   metadata check, both before and after reading, uses
   `os.stat(component, dir_fd=held_parent, follow_symlinks=False)` or equivalent
   descriptor-relative lstat. Reject a symlink itself even when it points to the
   already-open target; `O_NOFOLLOW` on the earlier open is not sufficient. Require the
   current user and no group/world write bits; public source modes such as 0755
   directories and 0644 files are allowed, without imposing private 0600/0700 rules.
3. Open the leaf `O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK`. Register every returned
   FD immediately. Require regular, single-link, expected-owner/non-group-world-
   writable file and matching fd/named identity. Reject a second checkout row
   resolving to an already encountered `(device,inode)`, without deduplicating its
   work into an accepted alias. Require exact expected positive size before reads.
4. Read predetermined chunks of at most 65,536 bytes until exactly the declared
   size has been returned. Each call must return exact `bytes` of exactly the
   requested positive length. A short/zero return, interruption, error or malformed
   return consumes failure; do not fill, retry or continue. Hash accepted chunks
   incrementally without retaining a chunk list or raw source bundle. Release the
   helper's accepted chunk reference after hashing and before the next data read
   or EOF probe; no record or closure retains it. This preserves the one-chunk bound.
5. Make exactly one 1-byte overflow/EOF request after all declared data. Only here
   is `b''` the required successful return. Any returned byte fails. An empty source
   file or zero declared length is never admitted. Record requested bytes before
   calls and known returned bytes separately; neither is a receipt of unobserved
   kernel work or an authority to replay after an exception.
6. Recheck the held chain and leaf's fd/named identity, owner/mode/link count,
   extent and before/after `mtime_ns`/`ctime_ns`, then compare the digest. These are
   boundary observations: they do not detect every replace-and-restore or prove a
   historical/atomic multi-file snapshot. Earlier files are not silently reread at
   the end; the outer immutable interval is necessary.
7. Independently close leaf and ancestor FDs in reverse order before advancing.
   Clear each ownership slot **before** its one close attempt. A fault or sticky
   reentry prohibits the next member, even if a hook swallowed the nested error.
   After the final member, check root identities, close the owned root, and check
   the sticky latch again before returning. Borrowed-root ownership is unchanged.

Output is byte/identity evidence only:
`FileObservation(member_id, sha256, byte_length, identity, mtime_ns, ctime_ns)`
with `identity=(device, inode)`, and
`CheckoutObservation(source_commit, source_tree, catalog_sha256, root_identity,
files, unobserved_runtime_member_ids)`. No raw source payload, resolved callable,
authenticated/ready flag or activation record is returned. Runtime IDs are listed
explicitly as outside this observation, not marked verified by a successful pass.

On failure, preserve the first exception object and raise it after all independent
cleanup, even when a later operation throws a different error after swallowed
reentry. Retain bounded supplemental phase/member/type facts (at most 16, type text
at most 192 characters, with an overflow counter). Keep planned/entered/fully
observed member IDs, requested/known-returned byte counts, open/close attempts and
closure uncertainty in the in-memory snapshot; later members stay unrun. Full
byte observations whose cleanup failed are not a successful returned batch.
A snapshot is not a serialized receipt, source authority or resume point.

Open entry without a returned/registered FD and ambiguous closes remain explicit
uncertainties; do not invent complete closure, scan the process for handles, retry
an uncertain close, delete source or silently skip remaining independent closes.
All known owned FDs get one cleanup attempt. Kernel/process interruption before
registration or a blocked call still needs outer process/closure evidence. There
is no separate finish/reopen method and no source/metadata write or fsync here.

## Finite accounting to test against actual code

For N checkout members, let P be each locator's component count. The 160-character
canonical path limit gives P<=80 (minimum length for 80 components is 159). Keep at
most 81 owned descriptors simultaneously: owned root, 79 ancestors and one leaf;
the caller's borrowed root and all other process FDs are additional and remain
outside this helper's ownership/census.

| Per-attempt filesystem work | Conservative ceiling |
| --- | ---: |
| Owned opens | `1 + sum(P) <= 5,121` |
| Once-only closes of returned owned descriptors | <=5,121 |
| fstat/named-stat checks, using the sequence above | `4 + sum(4*P+2) <= 20,612` |
| Content-read calls, including one EOF probe/member | `63*3 + 5 = 194` |
| Sum of requested source payload bytes | `63*131073 + 262145 = 8,519,744` |
| Simultaneous source data chunk | 65,536 bytes |
| Full source payload intentionally retained/written | 0 bytes |

The metadata formula counts two root-acquisition/final checks each; for a file,
each ancestor and leaf has fd/named checks before and after, plus the root checks.
Any added metadata check must appear in the implementation census. Owner/PID/thread
checks, hashing, parser work, Python object operations and failure records are
separate work; these are Python-level filesystem call counts, not a kernel syscall,
CPU or worst-case wall-time proof. Positive short-read failure is deliberate: a
fill loop could request the same remaining allowance repeatedly and invalidate
the stated sum-of-request-sizes ceiling. Ordinary static-file reads that return
short are retained failures, not a reason for automatic retry.

This is only the checkout part of one source pass. Loaded-source copies, runtime
verification and S-file reads are absent. The accepted two-pass 33,947,906-byte
ceiling and original source/recheck costs are unchanged; a later pass2 is a second
identified call inside an admitted two-pass plan, not an automatic new unit.
Raw catalog/expected-plan acquisition, retained inputs, parser/canonical copies,
transport, installer work and closeout must be counted separately in the complete
plan. In particular, a caller reading the catalog to supply these bytes must not
silently call that an additional free file read. No aggregate fit is proved here.

Inputs include at most 131,072 catalog bytes and the bounded plan above. Catalog
parse/canonical temporary objects, at most 64 result records, held ancestor/stat
records, one read chunk and digest state are distinct memory operands. Proposed
synthetic tests should retain at most 1 MiB of owned file payload including copies
and per-name hardlink accounting; directory/FIFO/symlink entries and diagnostics
must also be inventoried. This is a planning target requiring source-derived
fixture counts and a fresh engineering envelope, not an allocation or measured fit.

## Focused fake-file acceptance matrix and deferred work

Use owned tiny source-shaped files and the independent literal catalog policy.
No actual protocol/history/protected dataset is read to manufacture fake authority.
The final authored case/operation/fixture census must precede engineering admission.

* Positive multi-file observation: exact bytes/hash/length/order, EOF requests,
  all owned closes, caller root still usable, runtime rows explicitly unobserved.
* Invalid plan/catalog shape, pins, types, length, root identity and membership
  reject before unintended file reads. Valid expected pins are independent test
  data, not observations made by the helper to approve itself.
* Owned symlink/FIFO/directory/hardlink/unsafe-mode leaves and substituted ancestors
  fail without following links or blocking on FIFO. Distinct names resolving to
  one file are not accepted as independent checkout members. Deterministically
  replace an opened name with a symlink to the same held target before its next
  named check; non-following metadata must reject it despite identical target bytes.
* Deterministic extent/mtime/ctime or named-identity change during an owned read,
  plus digest mismatch with unchanged size. Use explicit mutations/hooks, no sleeps.
* Short/zero/error/interrupted data reads stop without fill/probe/retry. A synthetic
  nonempty EOF probe with otherwise unchanged metadata isolates the probe check;
  exact chunk/EOF ordering and constant bounds are independently asserted.
* Read error plus close error retains the original object and supplemental facts.
  A scoped real-close-then-EIO injection closes one exact owned FD once but leaves
  acknowledgement uncertain; restore mocks before caller-root/pytest cleanup.
* Swallowed work- or close-hook reentry, including a later distinct error, cannot
  return a batch or advance; all remaining independent owned closes still run.
  Retry of the consumed instance performs neither observation I/O nor cleanup,
  and never closes the caller's borrowed root.
* A mid-batch failure preserves earlier observations and the full planned/failed/
  unrun denominator. Validate descriptor ownership per allocation, not by assuming
  numeric FD values are never reused. Small test-only chunk substitution can
  exercise progress boundaries without claiming full-profile load qualification.

Do not reuse `workflow_io.read_bytes` or sink `_Anchor/_read_file` wholesale:
they enforce private modes or reopen path strings and have different read/close
semantics. Do not broaden them for this helper. Reuse `parse_catalog` and the
reviewed first-fault/once-only ownership patterns, with a focused source-file walk.
`verify_sources` remains its separate seven-checkout/four-loaded-copy boundary;
`verify_native_installation` also reads archives/dependencies/runtime and computes
an engine fingerprint. Neither is a cheap substitute or an automatically covered
call here.

The next independently reviewable boundary is loaded-source origin and actual
original-definition/owner validation under protected runtime/import premises.
Reading a current source path does not prove already-loaded code came from it.
The final closed catalog, fixture pre-call hook, d4 emitter, installer/captures,
S retention/sealing, pass2 routing checks and outer S/T/C/A admission all remain
unimplemented or independently required. This document changes none of those
interfaces, study gates, primitive calls or historical charges.
