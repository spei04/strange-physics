# Native study manifests and cumulative accounting (RA-02)

This unit implements the bounded native STUDY/COST interface for issue #105.
It does not execute a study, authorize providers, implement broader study
tracks or alter the frozen 40-slot public protocol. The approved local
comparison has six opaque stationary worlds, two policy seeds, three selectors
and 36 cells. Each cell reserves 12 purchased slots, including four calibration
slots. The cumulative limits are 432 purchases, eight measured CPU-core-hours
and 1 GiB of newly created artifacts.

## Freeze and accounting identity

The immutable NativeAccountingPlan exists before any cost-bearing reference,
calibration or sensitivity work. It fixes one study identity, purpose and
cumulative limits. NativeStudyLedger is anchored to the canonical plan hash.
A later freeze event attaches the actual NativeStudyManifest to that existing
history; it does not erase prior work or start another allowance.

The initial examples are explicitly synthetic. Actual source, lock,
configuration, grid, priors, likelihood, discrepancy, menu, calibration,
failure/termination policies and model-independent scoring policy are frozen only after
RA-N01, RA-N02.a, RA-N03 and RA-N04 acceptance. A StudyGate is retained trusted
acceptance evidence, not a bearer permission. The run producer must verify the
actual accepted identities and existing scoped approval before starting work.
Shape validation cannot authenticate arbitrary supplied gate claims.

The 36 cells form the complete ordered world/seed/selector Cartesian product.
Each arm has a distinct journal and cell identity. World IDs are opaque;
neither hidden definitions nor their low-entropy hashes belong in selector
inputs. The required NativeWorldCatalog is a separate evaluator-only artifact
containing the actual six-world mapping. Its private definitions and catalog hash
never enter a selector projection. Actual freeze checks its ordered IDs and the
stationary one-particle, fixed-anchor, zero-cubic, zero-observation-noise domain.
Its declared action space stays within the accepted purchased bounds: mass
0.5–2, position radius at most 2, velocity radius at most 2, impulse radius at most 1
and duration at most 2 seconds. Narrower lawful spaces are allowed. These are
admission limits for this first study, not changes to frozen CORE/SCI. Prediction
probes keep their separate accepted counterfactual domain; purchased-action
validation does not apply to those probes.
Catalog generation and retention count in the same cumulative artifact budget.
All roots in study.schema.json are owner-only accounting records.
A model/report hash in these records is not permission to disclose evaluator
material. N01 receives its actual public prefix and operation-local inputs,
not the full ledger or evaluator records.

Candidate-production and prediction configurations have distinct required artifact
identities. The actual candidate configuration binds the model's fit_config_sha256;
it does not substitute for predictor configuration or scoring policy.
The common scoring policy contains no eventual selected-model or instantiated
request/protocol digest. Each cell later retains its actual model-bound protocol
separately; an unstarted/interrupted cell does not invent one. The manifest
also pins the actual Journal engine fingerprint.

StudyArtifact identifies exact canonical producer bytes. Raw-byte equality
is distinct from typed scientific equivalence. Consumers must validate the
appropriate artifact type and cross-message joins, not trust a digest string.
The canonical profile includes defaults and preserves the existing Python
JSON numeric/Unicode behavior. No CORE/SCI/v1 message is changed.

## Attempts and measurements

The ledger issues an opaque attempt identity before work. N01 and later
numerical producers report operation-local NativeWorkFacts: actual input,
configuration, observation/model/output identities and a complete disjoint
requested/completed/failed/not-assessed partition. The output hash excludes
the facts wrapper to avoid self-reference. Counts are declared local units,
not total hardware work or proof of measurement authenticity.
An attempt is one bounded supervised work envelope. Internal forward calls
may be aggregated under it with their complete counts; they are not free
work. Measurements must partition execution: overlapping parent/child CPU
must not be double-charged. A repeated envelope gets a fresh attempt ID.

RA-02 owns phase/cell scope, reservations and global totals. Every real
re-execution uses a new attempt ID; exact receipt replay performs no work and
adds no cost. Purchased operation identity is separate from computation
attempt identity: retrying a pending purchase must not buy another slot.
All actual Journal reservations count, including pending and physically
failed calibration observations.

Measured CPU is CPU consumption, not scorer wall time. The supervising
producer must include child/thread CPU, forward/likelihood/ranking,
preparation/reference/sensitivity, scoring, retries, failures, accounting
overhead and newly created retained or deleted artifacts. Unknown cost
evidence never means zero: reserved capacity remains held until measured
reconciliation. The schema accepts measured overrun so evidence can be
retained honestly; complete transitions block further reservations beyond a cap. Aggregate totals
use bounded Python integers large enough to retain multiple measured overruns;
they must not be coerced through a lossy JavaScript Number. Later diagnostic work cannot open a replacement budget.

Persistence and real process measurement are producer duties. Pure functions
cannot make a caller stop CPU consumption or prevent a second untracked
ledger. The single study namespace, append-only records, original plan,
atomic compare-and-swap persistence and reconciliation must be enforced by
the future local runner. No hosted storage or scheduler is implemented here.

## Complete accounting boundaries in this increment

append_study_attempt validates the full bounded ledger before proposing a
reservation or measurement append. A required expected_revision is the current
record count. Exact event-ID/canonical-payload replay returns the original ledger
without work or charge, including after the ledger has advanced; a conflicting
event fails. Fresh appends require current revision and an unused attempt ID.
The caller must atomically persist the proposed ledger using that same CAS.
New appends preserve record and byte headroom for one bounded final measurement
record per unresolved envelope; capacity exhaustion stops further work before
those final accounting records would become impossible to retain.

Unresolved attempts charge at least their original reserved CPU/artifact
capacity and any higher measured amount. Null updates never erase prior known
measurements. Final measurements cannot regress. Repeated computation has a
fresh attempt and charges again; an unresolved predecessor remains held.
Known completed local facts are immutable. Finalized attempts cannot be reopened.
The supervising producer must prevent overlapping measurement envelopes and
must include any future ledger/freeze/reconciliation overhead in measured work.

Purchase intents are charged before calling Journal.reserve. Their ordinals
are contiguous, unique per cell and bounded at 12. The first four are explicitly
calibration reservations. An exact operation retry retains its slot and must
name the preceding attempt; changed action/ordinal/scope conflicts fail.
The purchased_slots summary is the number of charged reservation intents,
including an interrupted intent that has not yet appeared in the Journal.
Such uncertainty is never a refund.

freeze_native_study attaches the one actual manifest without resetting the
plan, historical records, costs or unresolved holds. It verifies supplied source
identity, actual lock bytes, engine fingerprint and every exact canonical artifact
byte string, plus the private world catalog. These materials have an aggregate
8 MiB bound. Source checkout identity, accepted gate evidence and kind-specific
numerical policy validation are trusted producer obligations; generic canonical
JSON is not proof of a valid prior, selector, prediction policy or experiment.
The frozen scoring-policy artifact is model-independent. Its N01 typed composition
and actual per-cell protocol/report binding remain the next RA-02 unit.

read_study_ledger enforces the strict 8 MiB / depth 32 / one-million-node input limits, duplicate-key
and nonfinite rejection, exact canonical chain, and every retained transition.
A chain authenticates neither arbitrary imported records nor real measurements.
It cannot re-prove scientific payloads that were accepted by a future publisher.
Only reservation/update and unfinished-cell publication are exposed in this
increment; no complete/scored-cell publisher exists yet.

summarize_study derives all 36 frozen cells, including unstarted, failed,
interrupted and cap-limited cells. seal_unfinished_cell records a bounded stop
without inventing a model, protocol or report. It seals new cell work while
allowing already reserved unknown costs to reconcile. Missing metrics remain
missing; no successful-only aggregation or scientific score is invented.

## Actual Journal reconciliation

reconcile_study_journal first validates the full ledger and then reads the actual
owner-private, quiescent rollback-mode SQLite Journal. It rejects sidecars,
symlinks, public permissions, incompatible tables/schema, byte/row limits and
changed bytes. This is read-only and does not repair or resume a Journal.
A producer must stop its writer before taking this snapshot; this adapter does
not provide a hostile-process snapshot or an atomic transaction with the ledger.

It binds actual run ID, engine, exact canonical private world, all operation IDs,
ordinals and action identities. Pending, completed and physically failed rows
all count. Completed rows beyond a pending hole are still validated, but the
exposed ObservationBundle stops at the first pending row and retains failed
records in that contiguous prefix. Every actual reservation must match a charged
ledger intent. Missing Journal rows remain explicit held intents; extra or
changed rows fail. A contiguous returned prefix does not establish that all
purchases have resolved. The later N01 publisher must separately inspect the
pending and missing-intent lists before claiming a complete purchased state.
The returned snapshot is owner-only and contains no private definition/law/seed
or definition hash.

The adapter and ledger do not authorize a scientific run. RA-02 remains partial
until the final N01 scoring-policy/model/protocol/report composition and its
independent review are complete. Actual source/config/world values remain
synthetic in checked-in examples. All real reference/calibration/sensitivity and
comparison work remains subject to preregistration and the approved entry gates.

## Actual Journal and native score reconciliation

The read-only `reconcile_native_study_score` boundary consumes bounded raw ledger,
scoring input and retained scoring result bytes, a real owner-only Journal path,
and the actual frozen catalog, pool, candidate configuration, prediction
configuration and model-independent scoring policy bytes. It replays the complete
ledger, reconciles the actual Journal, and requires twelve charged purchase intents
and twelve committed rows with no pending or missing reservation. Physical failed
records remain in the complete prefix. A shorter contiguous prefix is insufficient.

It reconstructs the candidate input from that exact prefix and frozen artifacts,
selects the private world from the catalog's cell association, and binds the actual
candidate result, selected receipt, preparation, ordered prediction inputs/results,
protocol and retained evaluator result. Each present result must match its own
actual terminal measured attempt, including full work facts. Candidate, preparation,
twenty-four prediction and scorer attempts have distinct identities. Missing or
invalid prediction transport retains its actual attempt state and accumulated
measurements, including unresolved reservations; it never implies zero cost.
Unrelated unresolved cell attempts and the global cumulative budget remain visible.

The evaluator's actual result is retained whole, including unscorable reports,
reference/metric failure diagnostics, no-report outcomes and its existing measured
runtime. Binding does not rerun numerical evaluation, fabricate timings or establish
numerical execution authenticity. Unavailable selection/preparation has no actual
probe inputs to bind and fails this score-specific boundary explicitly; its charged
attempts and unfinished-cell sealing remain available through the ledger interface.
The Journal's raw identity is checked again across the complete binding operation.

The new three schema roots are evaluator/owner-only. Their raw and typed canonical
identities, private result and truth-derived hashes must not be exported to the
online selector. A parsed evidence object alone does not authenticate its producer,
read the Journal, authorize work, establish MAP selection, or publish a complete cell.
The complete boundary performs those supplied-material joins it documents; durable
producer authenticity and process measurements remain separate responsibilities.

### Compatible accounting mappings

Existing fifteen-role manifests retain exactly their original canonical bytes.
An optional sixteenth, final `classical_diagnostic_config` role is accepted;
a `classical_diagnostic` attempt requires its actual frozen hash. This is a study
accounting mapping only, without an import of diagnostic types or a fabricated
diagnostic outcome. Comparison preparation accepts the frozen menu or scoring
policy. Native evaluation reconciliation specifically requires the scoring policy
and actual native preparation binder, so a ledger-valid menu preparation cannot
impersonate evaluation preparation. Native prediction configuration is unchanged.

### Remaining producer and publication work

This unit returns private evidence and does not append a complete-cell event.
Synthetic interface tests do not assert a real selection, actual future source
gates or a measured comparison. Joint native/classical source composition can be
reviewed before later selector implementation; actual comparison publication still
requires genuine grid/argmax/tie and selection-before-feedback evidence, calibration,
sensitivity, the actual final manifest, and the later runner's measured persistence.

The supervisor must measure all child/thread/process CPU, wall time and every new
artifact byte, including failures, retries and removed temporary output; reserve
before work; enforce remaining caps and record overruns; hold unknown work; and
avoid settling informational child facts twice. Quiescent Journal ownership,
durable ledger compare-and-swap, fsync/crash recovery and atomic publication remain
producer duties. Reconciliation itself and private catalog/evidence storage consume
the same cumulative budget. There is no new study, spending permission or reset.
