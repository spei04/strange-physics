# Private available-stage early-stop composition

This unit composes actual retained materials into a private no-score publication
proposal. It extends the accepted scored publication path without changing
StudyCellOutcome, existing ledger variants, or their default canonical bytes.
Its tests use synthetic frozen studies and real fixture Journals; they do not
run the comparison or establish MAP, calibration or selection-before-feedback.

reconcile_study_early_stop reads the complete bounded ledger, actual frozen
artifacts and current private Journal. propose_study_early_stop uses the same
pure CAS and idempotent replay implementation as propose_study_publication.
Neither callable persists files or measures work. Returned evidence is strictly
owner/evaluator-only: it contains private identity hashes and may contain a
classical diagnostic's world and report. It must not be given to a selector.

## Actual available stages

The witness document contains a bounded, tagged collection of actual candidate
inputs/results, selected-candidate receipts, preparation inputs/results,
per-probe prediction outcomes or missing/invalid transport, and classical
diagnostic inputs/results. Identical embedded predecessors may be reused;
duplicate explicit stage identities reject. Distinct prediction retries retain
their own measured attempt and result, even for the same probe.

The composer retains all charged cell attempts, including unrelated retries and
reserved/running/unknown work. Present numerical outcomes require the exact
terminal measured facts from the ledger. Missing earlier terminal material is
explicit material_recovery, never a fabricated typed failure or zero cost.
Legacy menu-preparation attempts remain charged without being misclassified as
missing evaluation-preparation results; this adapter binds evaluation preparation
to the actual scoring policy. A supplied historical stage is joined to its exact prefix of actual contiguous
Journal records and identified separately; it cannot establish current progress.

| Actual retained state | Derived no-score state |
| --- | --- |
| No purchases, empty or actually absent Journal | Unstarted, incomplete |
| 1–11 purchases, pending rows or charged missing rows | Purchase-incomplete |
| Complete purchases, no available candidate | Candidate-unavailable, incomplete |
| Actual rejected/failed candidate, no unresolved work or other progress | Failed execution |
| Produced candidates, no selection | Selection-unavailable, incomplete |
| Actual selection, no preparation | Preparation-unavailable, incomplete |
| Actual rejected preparation, no later/other progress | Failed execution |
| Prepared protocol and partial/unstarted predictions or scoring | Incomplete |
| Missing earlier terminal result bytes | Material recovery, incomplete |

Actual Journal absence is determined by a safe local read, not a caller flag,
and the composer does not create a missing Journal. Every actual row is retained
as an identity/status projection, including failed or completed rows after a
pending hole. Only the contiguous committed prefix feeds candidate material.
Twelve charged and committed rows, no pending/missing intents, and actual current
stage materials are required before a resolved candidate/preparation failure can
be classified as the current cell's failure. A later produced candidate or
different valid selected receipt cannot be hidden by an older rejection.
Later completed generic selector work also prevents an older rejection being
called final, but supplies no invented model receipt or MAP proof.

An actual terminal scoring attempt always requires the existing scored
publication boundary, even when its result bytes are unavailable. Recovery must
supply those bytes; the caller cannot hide a possible scored/unscorable report by
choosing an earlier failure. Nonterminal/unknown scoring with no result remains
incomplete. An actual classical result is independently bound to the same actual
prefix, frozen diagnostic config and private catalog world; it never supplies
the missing native primary score or overrides its state.

Only an actual exhausted aggregate CPU/artifact budget or an observed overrun
can produce cap_limited. A local preflight resource rejection or absence of work
does not prove global exhaustion. All known measurements and unresolved holds
come from the complete ledger; this proposal neither resets nor settles them.
Selected-candidate receipts bind membership/provenance, not an N02/N04 MAP or
chronology proof. Multiple retained model choices remain explicit witnesses
instead of being arbitrarily promoted to one primary model.

## Bounded identity and replay

Frozen material raw hashes/sizes and typed canonical hashes are both checked.
Frozen materials total at most 8 MiB; witness raw/canonical bytes at most 16 MiB;
evidence canonical bytes at most 32 MiB; combined supplied ledger/material/witness
bytes at most 64 MiB. Strict parsing rejects duplicate keys, nonfinite JSON and
excessive depth/nodes before typed validation. The complete ledger and Journal
retain their existing independent bounds. A final raw Journal reread detects
changes during composition.

The evidence binds the original pre-append ledger and all supplied raw/canonical
materials; the compact event references that evidence and derived original
outcome; the receipt binds the resulting record. No receipt is hashed back into
its own event. Fresh proposals require current CAS. Replay requires the original
raw ledger and evidence, proves the original ledger is the exact retained prefix
of the current ledger, rebinds original material, and returns the original receipt
after unrelated appends without another record or charge. Scored and no-score
evidence cannot substitute for one another. Original Journal/material snapshots
must be retained for retry; changing live material is not a new original proof.

## Remaining producer work

This is a source/interface proposal boundary, not durable publication. A real
producer still must lock/reconcile the Journal, measure CPU/wall/new artifact
extents, reserve publication/recovery overhead, persist original evidence and
ledger atomically with CAS/fsync, handle crash/lost acknowledgements and enforce
the cumulative study caps. Genuine N02/N03/N04 selection/calibration and the
actual final frozen study remain required before comparison execution. These
future scientific producers are not imports or caller readiness flags in this
source unit. Both research parent tasks remain partial pending their complete
source/interface and producer obligations.
