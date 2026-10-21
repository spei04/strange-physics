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
failure/termination policies and scorer protocol are frozen only after
RA-N01, RA-N02.a, RA-N03 and RA-N04 acceptance. A StudyGate is retained trusted
acceptance evidence, not a bearer permission. The run producer must verify the
actual accepted identities and existing scoped approval before starting work.
Shape validation cannot authenticate arbitrary supplied gate claims.

The 36 cells form the complete ordered world/seed/selector Cartesian product.
Each arm has a distinct journal and cell identity. World IDs are opaque;
neither hidden definitions nor their low-entropy hashes belong in selector
inputs. All roots in study.schema.json are owner-only accounting records.
A model/report hash in these records is not permission to disclose evaluator
material. N01 receives its actual public prefix and operation-local inputs,
not the full ledger or evaluator records.

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
retained honestly; complete transitions will block further work after a cap
is reached. Later diagnostic work cannot open a replacement budget.

Persistence and real process measurement are producer duties. Pure functions
cannot make a caller stop CPU consumption or prevent a second untracked
ledger. The single study namespace, append-only records, original plan,
atomic compare-and-swap persistence and reconciliation must be enforced by
the future local runner. No hosted storage or scheduler is implemented here.

## Current checkpoint

This first checkpoint supplies strict typed shapes, canonical hash-chain
structure, synthetic fixtures and structural/semantic tests. Complete
reservation/update/replay/cap transitions, actual Journal reconciliation,
actual-material bindings and derived summaries follow in the same RA-02
unit. Parsing this checkpoint alone is not complete ledger admission.

The final summary must include every frozen cell, including unstarted,
failed, interrupted and cap-limited cells. Missing metrics remain missing;
no successful-only aggregation or scientific score is invented.
