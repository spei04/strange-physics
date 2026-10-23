# Measured native publication

`commit_native_publication(store_root, request)` is an owner-local Linux producer
for the existing early-stop and scored publication proposals. Its fixed child
performs composition only. It never runs candidate generation, simulation,
prediction, fitting, scoring, classical diagnostics, providers or a study.

This initial executable checkpoint is under review. The remaining acceptance
matrix includes kill/fault injection, original scored outcomes, concurrent
publication, resource exhaustion, retained control failures and package gates.
It is not parent closure or permission to admit the finite-grid stage. The
numerical and purchased-simulation metering wrappers are separate obligations.

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
A durable creation marker precedes first store creation. Missing stores after that
marker, partial/corrupt stores, and current ledgers lacking the exact original
seed prefix fail closed; they never fall back to a new seed budget.
Absolute-root binding rejects relocation but cannot detect wholesale rollback
of all trusted state at the same path. Owner-controlled retention, protected
ancestors and a local filesystem honoring SQLite/fsync locks are prerequisites.
This is not an adversarial filesystem sandbox or a fork-proof budget service.

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
fund cleanup. Inherited child hard limits are preserved or tightened, and every
child setup/execution failure exits inside the fixed child boundary. This API cannot borrow another
thread's timers.

The artifact metric is logical newly-created file extents, not physical disk
allocation or write amplification. Controlled exclusive scratch writes are
counted even after deletion. The SQLite database and retained PERSIST journal
are measured by monotone extent growth; logical BLOB lengths are not added a
second time. WAL, disk temporary files and VACUUM are outside the profile.
Missing/shrinking tracked extents fail rather than imply negative work.

Actual known operation measurements are followed by a separate ledger update.
The global controller hold covers startup, cleanup, final commit/measurement
and acknowledgement tails. It remains unresolved, even when a scientific cell
is complete. Reaped failed children retain known CPU/wall/artifact measurements under an
unknown work hold. Crashes keep the whole work reservation; recovery consumes fresh
capacity. These measurements do not retroactively meter the native numerical
results supplied to the publisher.
