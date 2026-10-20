# Artifact and checkpoint contract — ART1

SP-01.c / issue #89, first review unit. Typed messages and pure admission/recovery
predicates are implemented for review. Full ART/EXEC acceptance still requires
the package/worker unit and final composition; this is not hosted enforcement.

[Schema](../contracts/artifacts.schema.json),
[synthetic examples](../contracts/artifacts.examples.json) and
[models](../src/strange_physics/artifact_contracts.py) describe the boundary.
Only `ArtifactRef` and `CheckpointRequest` are public. Every other model is a
trusted server projection or pure commit proposal. Constructing one does not
verify stored bytes, establish current authority or commit a transaction.

## Public identity and private storage

The formerly draft artifact reference now includes a required immutable
`generation`: a 1–20 digit positive decimal string. It is never a JavaScript
number. The storage adapter additionally validates the provider's generation
domain. Artifact identity is tenant-scoped; hashes confer no access and do not
enable cross-tenant deduplication.

The private locator identifies a configured storage namespace and server-assigned
canonical object key. Namespace mappings are immutable identities for the
provider/account/bucket security boundary; changing a mapping requires a new
namespace ID. A client cannot select a namespace, key, URL or credentials.
The exact locator and generation participate in verification. GCS metageneration
is distinct from content generation; mutable object user metadata is not
authorization or evidence of the content hash. See Google's
[object fields](https://docs.cloud.google.com/storage/docs/json_api/v1/objects).

`sha256` hashes the complete raw stored bytes, including any declared encoding.
It is not the SCI canonical model/message hash. The producer reads the entire
exact object generation, applies configured byte limits and checks transport
integrity before recording SHA-256/size/media type and readback provenance.
A metadata HEAD or client-supplied digest is insufficient. GCS's
[transport checksums](https://docs.cloud.google.com/storage/docs/data-validation)
are separate from this content identity.
Generation-bound [preconditions](https://docs.cloud.google.com/storage/docs/request-preconditions)
must protect uploads, reads and deletion from replacement races.

`RunArtifactRecord` is the current catalog row for a run-owned object.
Availability, visibility, revision and namespace ownership are server facts.
Checkpoint state in this first profile must be explicitly `agent-visible`;
workspace-private, evaluator-only and public objects are not implicitly
declassified into agent state. Sharing and publication remain separate flows.

## Checkpoint request and proposed admission

CORE Checkpoint bytes and SCI messages stay unchanged. The public body retains
`checkpoint`, `runtime_image_sha256`, and its ordered list of at most 128
artifacts. Duplicate logical artifact IDs are invalid. The exact normalized
full-body digest includes generation and all reference metadata in order.

The required `ArtifactPolicy` supplies explicit versioned envelope, JSON depth,
node count, ref count, per-object and aggregate byte limits and a sorted media
allowlist. Examples are test policy values, not approved deployment defaults.
CORE's existing 256 KiB cap still applies independently. Adapters must enforce
bounded transport/decode limits before constructing Python objects.

The complete [checkpoint entry point](../src/strange_physics/artifact_checkpoints.py) composes current
`authorize_product(checkpoints:write)` before replay, joins actual typed
verification to the exact workspace/run/request/ref list, recomputes the full
request hash and derives the completed prefix from the complete accepted ledger.
No client `artifacts_verified` boolean or optional current-authority bypass is
allowed. The old internal producer interface is amended explicitly:
`control_contracts.validate_checkpoint_write` is replaced by the clearly
incomplete `validate_checkpoint_metadata` helper, with no artifact boolean.
The named complete `artifact_checkpoints.validate_checkpoint_write` requires
authority, actual request, policy, current attempt binding, exact verification,
complete accepted ledger and natural-key lookup. There is no optional binder.
Repository inventory found only the old control test helper as a caller; it
now exercises the renamed low-level primitive. No HTTP/SDK consumer is hidden
behind a compatibility shim.

`CheckpointArtifacts` binds an ordered current catalog/readback set to a
request and actual policy digest. Verification must cover every referenced
object exactly. Currency, complete upload and genuine readback provenance
remain mandatory trusted-producer obligations; timestamps alone prove none.

## Atomic history and recovery

A pure `CheckpointCommitPlan` joins immutable history, latest pointer and
outbox identity. The SQL producer commits all projections under the run and
checkpoint CAS together with current authorization/lease checks. The outbox
identity is retained for the run lifetime even after dispatch; delivery state
is separate. No proposal acknowledges that SQL or storage actually committed.

The bounded `CheckpointLookup` contains the natural-key target, current latest
head, and explicit target/latest record and retained outbox projections. It deliberately permits
missing projections so runtime recovery can deny partial evidence explicitly,
without loading the entire checkpoint history (at most two checkpoint records).
Even a fresh write requires the latest head to join its actual committed record
and outbox; a pointer alone cannot let a new checkpoint advance past corruption. Producers prove lookup absence
and currency under the same lock. Exact historical replay must not move latest,
allocate another checkpoint or debit resources.

Upload completion precedes a DB reference. A DB failure can orphan an object;
missing/partial objects, ref rows, history, head or outbox cannot become a
successful checkpoint. Reconciliation must distinguish verified-but-unreferenced
objects, lost acknowledgement and corrupt/partial DB evidence. Cleanup requires
configured retention/grace, no active consumer and a current reference scan;
the roadmap's proposed retention numbers are not approved by this contract.

Restore-candidate validation is explicitly non-authorizing. The later
restore adapter must establish current read authority before any payload
delivery; this slice adds no read route, role or controller permission.
Choosing an earlier complete compatible checkpoint is an explicit recovery
decision, never silent use of an incomplete latest checkpoint. Budgets and
already committed observations remain independent of the checkpoint.

No pickle or agent-specific executable deserialization runs in a trusted
process. This slice implements no storage adapter, SQL/HTTP handler, sandbox,
retention worker, token verifier or live concurrency guarantee. Package/worker
envelopes are the next SP-01.c unit; full executable predictors remain SP-19.a.

## Producer ordering and safe failures

The complete boundary first composes the current workspace, verified credential,
durable owner/generation/grant incarnation and current lease. This includes
expired/revoked/replaced worker tokens and role downgrades before any replay.
The trusted `CheckpointAttempt` must match that run/attempt/lease and supplies
the pinned package/config/runtime. Then the boundary enforces actual policy and
CORE limits, exact ordered object evidence, complete accepted ledger and retained
record/head/outbox consistency. Failed physical records advance the completed
prefix; pending, missing and aborted slots do not.

Current policy bounds apply to historical replay as well: a retry cannot use
a previously accepted body to bypass current parse/resource or visibility
constraints. Request identity remains the entire normalized public body;
policy and private storage proofs do not secretly alter its replay key.
Quota accounting and resource reservations still require their later SQL
producers; these predicates never debit or refund.

The producer locks current artifact catalog rows in a deterministic order and
compares available state/revision while installing checkpoint references.
Orphan cleanup uses the same lock/CAS boundary: after current reference and
consumer checks it transitions the row to tombstoned before deleting the exact
generation. Thus either admission installs a reference first and cleanup
must retain it, or tombstoning wins and admission fails. A no-reference scan
followed by an unlocked delete is insufficient, even with a generation
precondition. The proposed record retains each exact artifact revision for
this comparison. Out-of-band deletion is prohibited by the later IAM/storage
adapter; this pure contract cannot make an object durable.

Immutable history, latest pointer and retained outbox identity commit atomically.
A retry with one missing projection yields `409 recovery_required`; an exact
historical request returns its original body without changing latest. Changed
existing content yields `409 idempotency_conflict`. Incompatible prefix/runtime
or lifecycle changes yield `409 incompatible_state`; invalid object evidence
or actual bounds yield `422 invalid_request`. Missing policy yields
`503 policy_unavailable`. Existing current-authority errors remain
401/403/non-enumerating 404 as specified by C2. No error embeds a private locator,
artifact bytes, secrets, evaluator data or request state.

The pure raw-buffer helper independently checks actual byte length and SHA-256;
it does not read cloud storage or prove a location. The lifecycle predicate
allows uploading → available or tombstoned, available → tombstoned, and
tombstoned → deleted, with revision CAS and immutable identity/visibility.
It never resurrects deleted/tombstoned state. Promotion to available still
requires trusted storage completion evidence; visibility changes need a
separately authorized publication/sharing flow, not this lifecycle helper.

Replay and restore-candidate validation require each current available artifact catalog row to equal its
retained snapshot exactly. This lifecycle has no available-to-available revision
transition; a higher available revision cannot imply legitimate resurrection.
A new independently bound byte readback may differ without changing that row.

Latest and historical commit witnesses must match the current immutable run
binding, cannot name a future lease epoch or run revision, and cannot claim a
future commit time. The same lease epoch implies the same attempt identity.
A currently authorized replacement attempt may replay a compatible older
checkpoint. When target and latest denote the same checkpoint, both retained
record and outbox projections must be identical.
The older target also cannot have a later run revision, commit time or lease
epoch than the latest record; equal epochs identify the same attempt in both.

Restore compatibility applies the same expected-attempt lineage rule: a future
epoch or another attempt in the same epoch is invalid, while an older compatible
checkpoint may be considered by the separately authorized recovery adapter.
