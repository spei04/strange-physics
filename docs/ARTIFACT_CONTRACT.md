# Artifact and checkpoint contract — ART1 API checkpoint

SP-01.c / issue #89, first review unit. This checkpoint defines typed messages
and cross-message invariants. Complete admission, recovery predicates and their
runtime review follow; this is not final ART/EXEC acceptance.

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

The upcoming complete checkpoint entry point will compose current
`authorize_product(checkpoints:write)` before replay, join actual typed
verification to the exact workspace/run/request/ref list, recompute the full
request hash and derive the completed prefix from the complete accepted ledger.
No client `artifacts_verified` boolean or optional current-authority bypass is
allowed. The existing metadata predicate is not complete hosted admission.

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
head and independently read retained outbox projection. It deliberately permits
missing projections so runtime recovery can deny partial evidence explicitly,
without loading the entire checkpoint history. Producers prove lookup absence
and currency under the same lock. Exact historical replay must not move latest,
allocate another checkpoint or debit resources.

Upload completion precedes a DB reference. A DB failure can orphan an object;
missing/partial objects, ref rows, history, head or outbox cannot become a
successful checkpoint. Reconciliation must distinguish verified-but-unreferenced
objects, lost acknowledgement and corrupt/partial DB evidence. Cleanup requires
configured retention/grace, no active consumer and a current reference scan;
the roadmap's proposed retention numbers are not approved by this contract.

Restore-candidate validation will be explicitly non-authorizing. The later
restore adapter must establish current read authority before any payload
delivery; this slice adds no read route, role or controller permission.
Choosing an earlier complete compatible checkpoint is an explicit recovery
decision, never silent use of an incomplete latest checkpoint. Budgets and
already committed observations remain independent of the checkpoint.

No pickle or agent-specific executable deserialization runs in a trusted
process. This slice implements no storage adapter, SQL/HTTP handler, sandbox,
retention worker, token verifier or live concurrency guarantee. Package/worker
envelopes are the next SP-01.c unit; full executable predictors remain SP-19.a.
