# D1 checkout-file observation: implementation and verification

Research's assigned source slice follows the reviewed
[owned-file design](D1_SOURCE_FILE_OBSERVATION_DESIGN.md) at `b94d812`.
The original 60-case helper/test checkpoint is
`c11f95e91fb931bd4edf00e55badb48de9d4b421`. Independent source review found
two busy-state windows around the first and final owner guards. This successor
keeps busy state across both guards and cleanup, with two additional regressions;
the original 60 cases and assertions remain unchanged.
Only `tests/d1_source_files.py`, `tests/test_d1_source_files.py` and this guide
belong to the slice. Lead owns central progress and A. Source review and a fresh
bounded engineering unit are prerequisites to execution; the parser's own
qualification is separate. No tests, imports, formatting, type checks, source
resolution or scientific work were executed during authoring.

## Concrete boundary and limitations

`CheckoutObservationAttempt(catalog_raw, plan, root_fd=..., expected_root=...)`
is an I/O-free constructor. `observe()` consumes that instance once; `snapshot()`
returns bounded in-memory attempt facts without filesystem work. The immutable
records `ExpectedCheckoutFile`, `ExpectedCheckoutPlan` and `RootIdentity` are
revalidated before an owned descriptor is acquired. Exact classes, tuple/string/
integer types, positive lengths and bounded fields are required; booleans and
subclasses cannot substitute. The helper reparses actual raw catalog bytes with
`parse_catalog`, then copies and compares the complete ordered checkout subset.
The expected catalog member's hash/length must match those actual supplied bytes.
The existing mandatory root locators and literal `uv.lock` policy remain enforced
by the parser. No raw S or presumed protected SHA(S) is required before pass1.

The helper's independent expected plan is an **external prerequisite**, not a
protected-plan producer. Matching self-supplied pins establish consistency only.
The source commit/tree fields are labels; there is no Git invocation, repository
discovery, path-selected import, runtime-member read or callable lookup.
`CheckoutObservation` returns hashes, lengths, file identities/timestamps, root
identity and explicitly unobserved runtime-member IDs. Snapshot `completed`
means this file observation returned after its owned closes, not authentication,
loaded-code provenance, installation, readiness or permission to retain A.
The final catalog, runtime trust, fixture hook, emitter, installer, S sealing,
second-pass captures/routing and outer admission remain independently unresolved.

The caller lends a live directory FD and independently supplies its expected
identity. It remains caller-owned. The helper checks that actual descriptor,
opens its own `.` reference and walks canonical relative components with held
parent FDs. All named checks use descriptor-relative `follow_symlinks=False`;
an opened name replaced by a symlink to the same target still fails. Source
files/directories may have ordinary `0644`/`0755` permissions, but require current
UID ownership and no group/world write bits. Leaves must be regular and
single-linked. File/ancestor identity, extent, mode and timestamps are compared
at the documented boundaries; root checks compare identity/permission fields.
Repeated physical leaf identities are rejected even when a file was renamed
between members and still has only one link.

This is a trusted single-owner interval. Borrowed-root acquisition/named ancestry,
immutable source custody and absence of other writers remain outer premises.
Boundary checks cannot prove historical creation identity, detect arbitrary
replace-and-restore, establish an atomic multi-file snapshot, or show where
already-loaded Python objects came from. Reading fake files under the tests'
owned checkout-shaped directory proves none of those scientific premises.

## Failure and ownership behavior

Consume the opportunity before parsing or filesystem work. PID/thread mismatch
or reentry latches the first exception. Rejected nested entry never clears an
outer busy flag. Entry marks used/busy before any owner callback; the first guard
runs inside protected cleanup, and an outermost finally clears busy only after
the final guard and completion decision. A swallowed nested call from either
guard therefore latches the exact original exception. A later consumed call
performs no I/O or cleanup. Sticky faults
block further observation work, including after swallowed callbacks, while all
remaining independently owned closes still execute once. Slots are removed
before close; the borrowed FD is never in the ownership stack.

Every open/read attempt is counted before its call. A returned FD is registered
before checking sticky state. Entered opens without registered returned FDs are
reported as unknown; known returned byte counts are distinct from requested
bytes. Every data read must return exactly the requested positive length. A
short/zero/interrupted/error return fails without fill/retry. The accepted chunk
reference is released after hashing, before the next data read or single-byte
EOF probe. Only that probe may return empty bytes successfully.

The original exception object is raised after independent cleanup, even if a
later callback or close raises a different error. Snapshot fault records retain
phase/member/type only, bounded to 16 records and 192 type characters plus an
overflow count. Observed earlier files and all planned/entered IDs remain visible;
cleanup failure prevents complete success. A close callback that actually closes
its FD and then raises still produces explicit closure uncertainty. No uncertain
close is retried, and no filesystem or descriptor scan tries to reconstruct it.
Process interruption, blocked calls or failure before FD registration require
external process/closure evidence. There is no separate finish, serialized receipt,
resume mechanism, metadata write or fsync.

## Static operation and copy census

For a whole declared checkout subset, `N <= 64`, with exactly one lock member.
Ordinary/catalog lengths are at most 131,072 bytes; only literal `uv.lock` may be
262,144. A canonical 160-character locator has at most 80 components. The source
implements the following per-attempt ceilings, without granting a run allowance:

| Work or live ownership | Ceiling |
| --- | ---: |
| Owned opens and independent once-only close attempts | 5,121 each |
| Descriptor/named stat calls | 20,612 |
| Data-read plus EOF calls | 194 |
| Sum of requested source bytes | 8,519,744 |
| Fully returned source data, before EOF probes | 8,519,680 bytes |
| Simultaneously owned descriptors | 81 |
| Accepted data chunk held by the reader | 65,536 bytes |
| Per-file source digests | 64 |

These follow `1 + sum(P)`, `4 + sum(4P+2)`, `63*3+5` and
`63*131073+262145`, respectively. Borrowed-root and other process FDs are additional.
The state guard runs at most `2*(5121+20612+194)+64+6 = 51,924` times on a complete
maximal attempt: before/after each work syscall plus entry, validation boundaries,
per-member cleanup and final return. PID/thread, UID, metadata comparisons,
parsing, hashing and Python allocations are separate work; these are source call
counts, not kernel/CPU/wall bounds or hostile-process isolation.

One catalog parse has the already-reviewed parser bounds. Its raw input may be
131,072 bytes. Expected-plan text is at most 24,688 ASCII characters plus 64
bounded length integers and fixed containers. Parser views/canonical copies,
input catalog storage, immutable plan copies, ancestor/stat records, up to 64
result records and digest state are separate operands. No raw source bundle is
retained or written. The first exception and its traceback can retain failing
frames/operands; the single accepted-reader-chunk claim is not a total Python
heap bound, and caller callbacks may retain their own copies.

Raw catalog/expected-plan acquisition, all input copies, later loaded-source reads,
runtime verification, original `verify_sources` calls and controller/transport/
closeout work still need a complete ledger. A caller's extra catalog acquisition
is not a free read inside the existing two-pass 33,947,906-byte S/source ceiling.
No allocation, historical-cost settlement or whole-science fit follows here.

## Authored tests and retained fixture estimate

Static AST inspection finds **62 cases in 18 test functions**, **186 prospective
phase reports**, and maximum node-ID length **106**. All parameterizations have
short literal IDs. Source review derived these counts; the final repaired
engineering check below collected and passed the same cases.

| Case group | Cases |
| --- | ---: |
| Complete observation and no-I/O consumed retry | 1 |
| Plan equality, types, ordered completeness and pins | 14 |
| Exact raw/record/root/FD boundaries | 6 |
| Borrowed-root mismatch | 1 |
| Unsafe/nonregular paths | 6 |
| Post-open same-target symlink, leaf and ancestor | 2 |
| Deterministic extent/time/replacement/digest failures | 4 |
| Short/zero/interrupted/error/type/EOF reads | 6 |
| Real 131,072-byte synthetic chunk schedule | 1 |
| Read error plus real-close-then-error | 1 |
| Swallowed read/close reentry, with/without later error | 4 |
| Entered open with no returned FD | 1 |
| Wrong PID/thread using scoped substitution | 2 |
| Swallowed reentry during first/final owner guard | 2 |
| Descriptor/named-stat failures | 2 |
| First-leaf/final-root close uncertainty | 2 |
| Explicit plan field/member/length caps | 6 |
| Renamed single-link physical alias across rows | 1 |

Each case constructs the same independent literal catalog and eight tiny fake
checkout files; the emitter row is runtime-declared and never materialized.
There are no real protocol, protected runtime/history or scientific fixture reads.
The catalog's literal AST has a 3,469-byte canonical JSON shape including LF;
the two runtime-declaration substitutions add at most 128 bytes, giving the
conservative 3,597-byte input/file bound. The fixture also asserts its encoded
length is below 8,192 before writing. This is static syntax arithmetic, not an
observed encoding measurement or a scientific table/batch encoding run.

The seven other initial files each contain nine fake bytes. Across **all 62
retained parametrized cases**, the conservative payload calculation is:

`62*(3597+7*9) + 131063 + 9 + 9 + 1 + 64 = 358,066 bytes`.

The additions cover the one large-file replacement delta, retained replacement
copy, extra hardlink pathname, appended byte and all symlink payloads. This fits
a proposed **384 KiB fixture payload ceiling**, below the accepted 1 MiB planning
target; it is not measured retention or an engineering admission. Count each
hardlink name, not just unique physical bytes. At most 498 regular-file names,
4 symlinks, 1 FIFO and 311 fixture-owned directories are retained; the 62 pytest
case directories and pytest's own parent/cache/log files are additional. Symlinks
are not followed in the later whole-output census. No mock survives its context
into caller-root close or pytest teardown.

Fixture setup invokes at most 559 high-level `mkdir` calls and 500 content-write
calls, including mutations; recursive `Path.mkdir` internals are distinct from
those high-level counts. Each fixture explicitly chmods only its root and four
known owned parent directories to 0755 (310 directory chmods across all cases);
this avoids dependence on inherited umask and makes public-mode coverage explicit.
There are at most 498 file chmods including the two mode mutations. There is one
hardlink creation, one FIFO creation, four
symlinks and five renames. Helper work across this authored matrix is bounded by
1,054 opens/closes, 5,208 stat calls and 993 read calls (8 fixed members per case,
with one additional data chunk in the large case). Fixture/hook metadata checks,
caller-root opens/closes, test reads/writes, Python/pathlib internals and logs are
additional, not hidden inside those helper counts. Each test lends one root FD;
this concrete matrix needs at most four helper-owned FDs plus that borrowed FD,
and one transient mutation writer. Whole-process FD usage is not bounded by six.

The only helper dependency is the immutable pure `d1_source_manifest` parser plus
stdlib modules. Tests add pytest and stdlib; their catalog is literal independent
material, and their import guard rejects scientific/recorder/sink modules.
Wrong-owner tests substitute identities without processes, threads or sleeps.
Source review and later controls must preserve these boundaries; successful
synthetic file tests would still not authenticate S or qualify a D1 experiment.


## Test-isolation repair after the interrupted local attempt

Lead reports local check2 stopped with exit86 and no terminal test census; only
the first case's fixture was retained. Historical test phases are unknown, and
no tripwire event receipt was retained. Global test patches of `os.stat`/`os.open` can
intercept the collector's own `Path.resolve` and failure-event writes. That is a
concrete compatible mechanism; the missing receipt leaves the exact historical
tripwire reason unknown. The failed attempt and its charges remain retained.
Lead records the numerical ledger and execution evidence separately; this repair
did not reset that account or authorize a retry; the later continuation was
reviewed separately within the same limits.

Tests now give `d1_source_files` fresh, explicitly populated `SimpleNamespace`
OS/threading objects per case. Every untouched attribute is checked against the
actual standard-library object. Fault patches target only those helper namespaces;
fixture setup, captured real callbacks, descriptor assertions, pytest and the
collector continue using actual `os`/`threading`. The no-I/O retry helper also
asserts shared `open/read/fstat/stat/close` identities remain unchanged while its
local functions are poisoned. Scoped mocks restore before caller-root fixture
cleanup and pytest teardown. No helper API, scientific guard, original test assertion,
case ID or file-payload ceiling changes. The two tiny namespace objects per case
are in-memory test machinery, not additional fixture files or an OS sandbox.

## Verified engineering checkpoint

The repaired source fe369cd2983c610c1f6d572027fef25fd8df5cce passed formatting/lint, full
configured typing over 227 files and all 62 synthetic cases with 186 ordered passing
setup/call/teardown phases. Separate collection bound the same 62 IDs with zero
phases; JUnit agreed, with no skips, xfails or forbidden events in the final check.
All 24 owned child processes across four attempts closed cleanly. Source, helper
and pinned environment identities matched. Both formatting steps preserved the
complete target ASTs. The production helper and trusted guard remained unchanged
by the test-isolation repair.

The cumulative account charges 106.312864 CPU seconds and 122.782534929 wall seconds,
including closeout holds. Its 3,018,011 logical bytes comprise 568 regular files,
28 symlinks and one unread FIFO, under 385 directories. The final suite's 62 owned
checkout roots retain 350,139 payload bytes, below the 358,066 source-derived bound.
Hardlink pathnames are counted separately; link targets were not followed.
Planning/review records are inventoried separately; external control usage and
peak memory remain unknown. The interrupted check 2 retains its original exit 86,
unknown exact trigger/phase/forbidden-entry census and all charges. Later success
does not reconstruct that missing history or reset earlier scientific unknowns.
The private checkpoint digest is 212f2261db7a9305dc9470697b7a2692dbf3873cf43ae31503177f5ab30954c9.

The original ordinary PR CI result is recorded below. That broader suite includes
historical physics checks and cannot substitute for the private guard receipt or
authorize D1 science. The next integration path and missing trust/resource evidence
are listed in the [loaded-definition design](D1_LOADED_DEFINITION_DESIGN.md).

## Original CI acceptance

[PR #155](https://github.com/spei04/strange-physics/pull/155)'s
[original CI run](https://github.com/spei04/strange-physics/actions/runs/41190075377)
passed all six required jobs in attempt 1. The frozen head is
`f36f0895b7dc0ef6c809ba6b59d579734cd165b2`; tested merge
`82301e8068753eaae3e94722749689c0bed75898` has the exact PR base/head parents and
the same tree. The release-candidate job was correctly skipped for this PR.

Python 3.12 and 3.14 each passed 6,086 tests, full typing over 227 files and
1,567 external JSON Schema fixture checks with all references resolved. Package
allowlists passed, and each runtime completed one eight-experiment smoke run
without failure. Repeated printed smoke summaries represent the same run.
Both analytic-reference jobs passed 24 cases/72 phases. Dependency and static
security checks reported no identified issues. The existing two serializer
warnings per runtime and three dependency-audit flag advisories remain retained;
the serializer warning details match the parent run after timestamp removal.

The six required jobs total 1,367 elapsed job-seconds against 4,980 configured
timeout-seconds. The provider start-to-terminal interval is separately 600 seconds;
these overlapping wall measures are not added or represented as CPU or billing.
Whole-CI CPU, provider cost and external control usage remain unknown. The private
CI seal digest is
`cce91ac198e050b07cebf8baf813ff530ef089518d7366465b4b0d00ced7b9e7`.

Hosted aggregate counts and source selection support coverage of the new tests;
they do not reproduce the local ordered 62-case/186-phase guard receipt or
reconstruct the interrupted attempt's missing history. The draft remains
unmerged. This acceptance does not establish actual runtime provenance, reserved
inventory acceptance, whole-path fit or D1 scientific admission.
