# Measured native publication

`commit_native_publication(store_root, request)` is an owner-local Linux producer
for the existing early-stop and scored publication proposals. Its fixed child
performs composition only. It never runs candidate generation, simulation,
prediction, fitting, scoring, classical diagnostics, providers or a study.

Acceptance covers process crashes and faults, original scored outcomes,
concurrent publication, resource limits, retained control failures and package
checks. Exact source identities, independent reviews and gate results are retained
in private indexed evidence; repository integration still requires its CI gates.
The public handoff below connects accepted measured execution to this publisher.
Its bounded evidence does not itself close the parents, admit finite-grid work
or authorize a study; exact source and delivery requirements remain separate.

## Admission and retention

The caller must already retain an owner-private root with `admission.json` and
the exact `seed-ledger.json`. No initializer or budget-reset API is provided.
The admission binds the absolute root, plan, source commit and lock digest.
Its control attempt is an existing unresolved global accounting reservation.
Its size must cover all finite tickets' CPU/artifact ceilings plus fixed
one-time overhead (one CPU-second and 16 MiB). This publication API never
settles or releases that control hold.

A ticket is an index in the admission's finite closed set. Each invocation
creates an exclusive owner-only ticket file and fsyncs it and the directory
before parsing the complete ledger or opening the store. The complete canonical
request is capped at 128 KiB before ticket consumption, including JSON escaping;
recovery uses the same byte cap. Contention and
startup failure consume tickets. An uncertain/consumed ticket cannot execute
again. A retry needs a new ticket and a new charged work attempt.

Only tiny bounded request/admission checks precede consumption. Rejected calls
at that boundary are not admitted measured execution, do not launch work and
must not be wrapped in automatic unlimited retry. The trusted caller retains
the admission and its original costs before invoking this API; fixture setup
is not evidence of such an external producer. The immutable control hold,
known publication measurements and available study allowance are distinct.
Neither denial nor the final measurement write is advertised as exact zero.

Root, admission, seed, store and ticket tombstones must survive restart.
A durable creation marker precedes first store creation. For legacy admission,
a missing store after that marker fails closed. Partial/corrupt stores and current
ledgers lacking the exact original seed prefix never fall back to a new seed
budget. The versioned handoff below permits only its specified paid cold-activation
cuts.
Absolute-root binding rejects relocation but cannot detect wholesale rollback
of all trusted state at the same path. Owner-controlled retention, protected
ancestors and a local filesystem honoring SQLite/fsync locks are prerequisites.
This is not an adversarial filesystem sandbox or a fork-proof budget service.

## Execution-to-publisher handoff

`commit_publication_handoff(source_root, request)`, from
`strange_physics.execution_publication_handoff`, is the fixed paid source API.
Its `PublicationHandoffRequest` and related intent/origin types are defined in
`strange_physics.publication_handoff_contracts`. It transfers one scored cell
from the retained execution store to a distinct publisher directory. It does
not run a scientific producer or initialize the target SQLite store.

The source must already have its original candidate admission, installation
descriptor, ledger and retained native-score/classical closures. The initial
source control must protect the three-call publication escrow and its finite
source recovery allowance. Before seed/admission, the trusted owner must retain
the descriptor's original lock, archive and provenance files durably at their
admitted paths, together with the installed bytes they describe. Initial
creation/copy costs need their own retained setup allowance; the handoff does
not retroactively measure them. It copies the descriptor unchanged, not those
referenced files, and cannot rebase their paths after sealing.

The target directory must already be owner-private and durable, with an
absolute normalized path outside the source directory and neither directory
containing the other. Its device/inode identity is part of the intent. Initially
it is empty; recovery permits only the exact complete expected exports. Directory
creation is trusted setup, not a free initializer hidden in this API.

Construct the request from existing authority:

| Field | Required identity |
| --- | --- |
| `intent.source_admission_sha256` | Canonical digest of the original candidate admission |
| `intent.cell_id` | The one cell shared by the retained score and diagnostic |
| `intent.scoring`, `intent.diagnostic` | Distinct retained logical IDs and exact receipt digests |
| `intent.destination` | A `PublicationControl` with the same plan/source/lock, a distinct control attempt, and exactly three tickets: publication, original replay and one recovery spare |
| `intent.destination_device`, `intent.destination_inode` | The originally prepared target directory's identity |
| `ticket`, `attempt_id`, expected revision/head | An unused source ticket, fresh attempt and actual current source head |
| Work CPU/artifacts/wall limits | Within the original source/recovery bounds, including the pre-write export allowance |
| `mode`, `recover_attempt_id` | `execute`/None initially; `recover`/original unresolved transfer attempt only for protected source recovery |

The canonical handoff request is at most 8 KiB. A durable source ticket precedes
fresh installed-build verification and store access. The caller reserves work
before inspecting the target or exporting materials, locks source then target,
and rechecks retained history, original inputs and exported bytes through the
source commit. Its bounded copy requirement includes the publication material
and Journal ceilings, the 2 MiB installation-descriptor ceiling and 4 MiB
additional allowance; small actual payloads do not waive this admission check.

The returned `CommittedPublicationHandoff` contains `origin`, `admission`,
`ledger` and `measurements`. The target receives ten original material JSON
files, the retained Journal, unchanged installation descriptor, `origin.json`,
`seed-ledger.json` and `admission.json`. The ten material roles are world
catalog, candidate config, prediction config, pool, scoring policy, classical
diagnostic config, native scoring input/result and classical diagnostic
input/result. The original diagnostic may have `selected=None`; it is not
rewritten to look like the primary selected candidate. Both pipelines must bind
the same actual history and frozen context.

The source atomically commits its known handoff work update, the actual
publisher-control reservation and a version-2 seal. The original ledger remains
an exact prefix. All source setup, control and unresolved work remain charged.
The promised publisher-control escrow becomes an actual hold once; remaining
capacity protects future target work and the original source recovery allowance
without counting that control protection twice. Final commit/acknowledgement
tails remain under the unresolved control hold, not an exact-zero measurement.

**Sealing is irreversible.** Every source append path, including execution,
paid replay, reconciliation, stop and another handoff, rejects the sealed store.
A lost return after source COMMIT does not permit source settlement or reseeding.
Retain the source and target authority even when no result was returned.

### Paid activation and original replay

Use the existing `commit_native_publication(target_root, request)` API with a
`NativePublicationRequest` from `strange_physics.measured_publication_contracts`.
There is no separate free activation call. The handoff admission has mandatory
version `strange-physics.handoff-publication-admission.v1`; its original seed,
origin digest, source path, destination control and directory identity must match.
Removing the origin or discriminator cannot turn a handoff seed/store into a
legacy admission. Ordinary legacy admissions and their existing wire remain
supported separately.

For first publication, set `mode="scored"`, the sealed cell ID, a new event ID,
unused target ticket and fresh attempt. Use the sealed ledger revision/head,
`origin.bundle.files`, `origin.bundle.diagnostic_attempt_id`, and the target's
`journal.sqlite3` path with the bundle's raw digest. CPU, artifact, output and
wall limits must fit the original escrow and target control. This handoff does
not activate the early-stop publisher route.

The target consumes and fsyncs its ticket before activation inspection. Each
call freshly verifies the retained installation descriptor and its original
referenced files. Cold initialization holds source then target locks, reads the
committed source seal without a writable source open, and creates a version-2
target store containing that exact origin and seed. A completed target validates
its own retained authority without reopening the source. Locks remain held
through the publisher's closure.

For an exact original replay, retain the original event and request/material
identity, but use a fresh attempt and unused target ticket. Publication reserves
and measures this work again. It uses the original stored ledger, materials,
Journal, evidence and receipt, so disposable live scientific exports may be
absent. The target's admission, seed, origin, installation descriptor, store,
tickets and original trusted lock/archive/provenance files must still survive.
Replay performs the fixed composition/validation child; it does not recompute
the candidate, predictions, score or diagnostic.

### Supported recovery cuts

Recovery never refunds an unknown attempt or enlarges the original ticket set.

| State | Supported action or denial |
| --- | --- |
| Source work failed before seal, with an unresolved transfer and exact complete exports | Use a fresh protected source recovery ticket, fresh attempt, current source head and the same intent; name the original attempt in `recover_attempt_id`. Its unknown hold remains. An ordinary execute retry is denied. |
| Source seal committed, including lost acknowledgement | Do not append to the source. A fresh paid target call must authenticate the committed seal and exported authority. |
| Fresh target, exact creation marker with missing DB, or exact empty DB | A paid handoff activation may initialize after source/origin checks; nonempty initialization sidecars are rejected. These exceptions do not weaken legacy marker handling. |
| Committed target, including lost acknowledgement | Reopen only with exact persisted admission/origin/seed. A new paid call may replay an intact original closure. A bounded cold PERSIST sidecar with its invalidated zero header is allowed. |
| Partial/conflicting exports, pre-seal metadata inconsistent with the new attempt, hot/ambiguous rollback, nonempty partial/corrupt DB, altered/missing authority or exhausted tickets | Preserve the state and deny. Do not delete a marker, clear a journal, reset a root or switch to legacy admission. |

The exported scientific Journal uses the existing quiescent snapshot rules;
the target store's cold PERSIST sidecar is a different file with different
checks. Arbitrary crash repair and hostile same-owner filesystem replacement
are outside the supported local/cooperating-lock contract.

### Bounded scope and later integration

The accepted 44-call specimen demonstrates one cell: 42 source calls and two
paid publisher calls, with three unresolved setup/source-control/publisher-control
holds. It preserves failed purchased rows, original score/diagnostic identity and
paid replay. Primitive store/activation evidence and the separate caller-fault
supplement have distinct scopes; current acceptance and pending delivery are in
the [handoff status](MEASURED_COMPARISON_HANDOFF.md). This is fixed-selection
conformance, not MAP inference, accuracy or a completed research comparison.

The ledger's 36-cell/432-slot/8-CPU-core-hour/1-GiB plan remains global. A
single-cell seal cannot serve all 36 cells by repeating this fixture, reseeding
authorities, discounting earlier charges or reclaiming unresolved holds. The
current simultaneous reservation floor for 36 publications alone is 1,168 MiB,
before source/scientific work, so the unmodified full-study profile is not
admissible under 1 GiB. That is a reservation bound, not observed physical usage.

Before RA-07.b admission, Lead owns the later multi-cell allocation/coordination
decision, Quality the assigned authority integration, and Platform/Research its
independent accounting/scientific review. This does not require a new service.
Actual N02/N04 execution cadence, complete cost census and a measured feasible
profile must follow those algorithms and precede the study. They are not circular
prerequisites for implementing the algorithms or closing the bounded parent
interfaces. Caps, graph, grid-first sequencing and later Laplace gates are unchanged.

## Publication and recovery

A fresh caller head is checked before the work reservation. The durable
reservation is phase=accounting, operation=accounting, cell_id=None. The proposal
then uses the exact post-reservation ledger as its original preappend ledger.
Reservation construction and persistence remain under the control CPU timer;
the work timer starts only after that transaction is durable.

The store lock precedes the actual present-Journal `BEGIN IMMEDIATE` lock.
The latter excludes existing Journal writers, not merely cooperating advisory
lock users. It is held through byte snapshot, live recheck and publication
commit, without Journal writes or mode conversion. One raw descriptor remains
open until after SQLite rollback/close; raw snapshot and recheck use pread.
Closing another descriptor for the same inode would cancel POSIX locks. All
caller material reads therefore precede the Journal lock. Contention tests
launch a fresh interpreter, avoiding inherited SQLite fork-local lock state. Composition reads the
owner-private immutable copy. For original absence, only creators that also
acquire `publication_store.root_lock(root)` are excluded; legacy or hostile
creators are not covered by that guarantee.

One SQLite transaction commits the ledger head, sequence/event identities,
original ledger, original Journal bytes/absence, input bytes, evidence and
original receipt. FULL synchronization and directory fsync precede return.
Replay reserves current work but composes from the retained original ledger,
materials and Journal. It checks the original evidence and receipt byte for
byte. Later Journal progress and unrelated ledger appends cannot rewrite them.
Missing closure rows, raw identity mismatches or partial state are corruption,
not a new event or a free rerun.

## Resource interpretation

Child user+system CPU comes from wait4/rusage; parent process CPU is measured
separately and excludes child CPU. Operation wall duration is monotonic and
includes waiting. The fixed child has CPU/file-size/core limits; the owning
single-threaded parent has CPU/wall deadlines. Startup/control, work and the
remaining control tail have disjoint CPU timers; refunded work capacity cannot
fund cleanup. All phases share one absolute wall deadline, bounded by the smaller
request and control wall allowance; phase changes cannot restart it. The child
inherits the remaining wall allowance through its own timer, bounding it even
if its parent exits. It rechecks the absolute deadline after fork before
composition; delayed scheduling cannot create a new wall allowance. Inherited child hard limits are preserved or tightened, and every
child setup/execution failure exits inside the fixed child boundary. This API cannot borrow another
thread's timers.

The artifact metric is logical newly-created file extents, not physical disk
allocation or write amplification. Controlled exclusive scratch writes are
counted even after deletion. The SQLite database and retained PERSIST journal
are measured by monotone extent growth; logical BLOB lengths are not added a
second time. The store must use the verified 4096-byte page profile before page-count byte limits apply. WAL, disk temporary files and VACUUM are outside the profile.
Missing/shrinking tracked extents fail rather than imply negative work.

Actual known operation measurements are followed by a separate ledger update.
The global controller hold covers startup, cleanup, final commit/measurement
and acknowledgement tails. It remains unresolved, even when a scientific cell
is complete. Reaped failed children and parent output/validation/publication failures retain
known CPU/wall/artifact measurements under an unknown work hold when the
remaining control allowance and store permit. A failed measurement write adds
a fixed diagnostic note while preserving the original error and durable hold.
Crashes keep the whole work reservation; recovery consumes fresh
capacity. These measurements do not retroactively meter the native numerical
results supplied to the publisher.


SQLite byte headroom includes both files. With spill disabled, the fixed
transaction profile journals each old page at most once, with eight record
bytes. The preflight reserves `old_pages * (4096 + 8) + 2 * 65536` for the
journal envelope, subtracting its retained high-water size, before assigning
the remaining allowance to database page growth. The two sectors cover
header/alignment at SQLite's maximum sector size. This follows the
[rollback-journal format](https://www.sqlite.org/fileformat.html#the_rollback_journal)
and the [SQLite pager](https://github.com/sqlite/sqlite/blob/version-3.45.1/src/pager.c):
cache stress can create another header, so `cache_spill=OFF` is checked, along
with the page, PERSIST, memory-temp and no-auto-vacuum profile. These bounds rely
on the standard SQLite pager behavior; runtime upgrades require this profile's
compatibility tests. This is not a binary-authenticity claim.

The prelimit is recalculated before initialization, reservation, publication
and success/unknown settlement. The work allowance also reserves the bounded
snapshot and child-output extents. Settlement uses only the remaining control
allowance, even when unused work capacity exists. The work-end artifact count is
frozen; any bytes created by a failed control settlement reduce the fallback's
remaining allowance and cannot inflate the recorded work measurement. Insufficient
headroom denies
the operation; a larger store may therefore require an admission with a larger
already-retained control allowance chosen at initial admission. An existing
admission cannot be enlarged or replaced to recover capacity.
