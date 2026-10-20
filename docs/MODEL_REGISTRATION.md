# Native model registration — COMP1

Status: native contracts and pure admission/completion/replay proposals independently
reviewed; hosted producers remain pending. The current integration and parent
freeze gates are recorded in the execution backlog. Actual storage/SQL producers
are not implemented by this slice. Synthetic fixtures do
not establish deployed approval, process isolation, fitting accuracy or production
readiness.

## Public native profile

The run-only `submitModel` route retains its existing run bearer authentication,
idempotency key and asynchronous `Operation` responses: 202 admits a pending
operation; 200 returns the existing logical operation after current authorization.
The frozen `Operation`, `ModelReceipt`, CORE and SCI messages are unchanged.

`SubmitModelRequest` replaces the stale draft predictor identifier with the
existing SCI v1 request/response versions, the fixed native analytic profile and
predictor version. It binds an ART1 reference including its lossless generation,
the canonical `LinearSpringModel` digest, the purchased `through_index`, the
actual prediction configuration digest, and a distinct predictor runtime image.
Only nonempty application/json model objects are supported. A native fitted model
requires a nonnegative prefix index; the unchanged general receipt type can still
represent its pre-existing broader range.

Stored raw model bytes, parsed canonical model identity, canonical observations,
the prediction configuration and the OCI image are separate identities. Permitted
JSON formatting changes can preserve the canonical model while changing the
stored bytes. Complete readback must match the exact reference's generation,
raw SHA-256, byte length and media type.

A finite nonnegative coefficient above four, an unknown fitter version, or a
different fit-configuration digest does not make a SCI-valid model an invalid
registration. Those models remain artifacts; prediction can later return an
explicit incompatibility. Registration does not run fitting or prediction and
does not authenticate the model's fit-configuration claim.

## Fixed reference bounds

The private configured policy may lower these maxima. An over-limit input fails
explicitly; there is no truncation, selected-record substitution or client prefix
claim.

| Material | Maximum |
| --- | ---: |
| Raw model object | 256 KiB |
| Raw private ledger snapshot | 8 MiB |
| Canonical selected SCI observation bundle | 8 MiB |
| Private proposal/record metadata | 4 MiB |
| Parsed JSON depth | 32 |
| Lexical JSON node starts (including keys) | 1,000,000 |
| Complete accepted-operation ledger | 10,000 operations |

The runtime checks raw byte limits before decoding and rejects
duplicate JSON keys, nonfinite constants and excessive nesting. The canonical
prefix limit is a separate bound, enforced during incremental encoding before
accumulating an oversized serialization. Its hash must be byte-identical to
SCI's `message_sha256`: stdlib JSON with sorted keys, compact comma/colon
separators, `allow_nan=False`, default `ensure_ascii=True`, and UTF-8 bytes.
Tests must include Unicode, signed zero, exact boundaries and failure before
large parsing/serialization.

These limits define a small conformance path. They do not demonstrate scalable
database reads or bound bytes already allocated by a caller. Real producers must
apply byte limits while fetching and before constructing the envelope. The
[ledger scaling constraint](EXECUTION_BACKLOG.md#sp-09-d) remains assigned to
SP-09.d, SP-13.c and SP-16.b; cumulative allowances remain SP-12.a. A production
indexed projection needs its own reviewed transactional/body-identity evidence,
rather than treating these full-record fixtures as that proof.

## Original engine and actual scientific prefix

`RunEngineBinding` is a private immutable trusted projection of original engine
selection. It binds the workspace/run, original execution admission identity and
digest, actual creation-request digest and world version, original ownership and
space digests, original engine version/fingerprint and commit time. Engine
version metadata is bounded to 128 characters. The trusted run-creation/result
producer must persist this binding; constructing or parsing it does not
authenticate its origin.

The existing `RunView` and `OriginalExecutionAdmission` do not contain engine
metadata. The current predictor or server package cannot supply the original
engine fingerprint: the existing engine fingerprint includes package code and
runtime/plugin inputs that can change. No hidden world definition is needed or
permitted in this boundary.

`ModelLedgerSnapshot` contains this binding, the run revision and the complete
accepted scientific `Operation` ledger from one consistent transaction. At
runtime its count/scope/ordinals/operation identities join the actual current
run, using the existing committed-prefix helper. A pending, running, failed or
cancelled operation stops the committed scientific prefix. A completed operation
whose `ExperimentRecord.status` is failed remains a purchased observation and is
included in the prefix and hash.

Construct the existing `ObservationBundle` from the selected actual records,
original engine metadata and actual immutable `RunView.space`. Its existing
validator checks purchased actions, particle ordering, bounds, sample counts and
sample times. The selected prefix must be complete through the requested index.
Later accepted observations do not alter this historical prefix. Selected fitted
indices must refer to completed scientific records; accepted scientific failures
remain in the provenance but cannot be selected as successful fitting rows.
No new observation schema or weaker hash is introduced.

## Mandatory authorization and distinct native runtime approval

Both complete admission/replay and completion entrypoints invoke
`authorize_worker_broker("submit_model", ...)` with the actual current credential,
run authority, `WorkerEnvironment` and `WorkerLaunchLookup` before inspecting
private model bytes, ledger, idempotency lookup or completed replay. This composes
C2 permissions/current ownership/key/lease with the active submitted-worker
launch, current package approval and required isolation policy. A C2-only helper
or a caller boolean is not the complete registration boundary. No human/service
model-submission route is added.

The built-in analytic predictor approval is a separate check. It binds the
actual fixed `SpringPredictionConfig`, native purpose/profile/version, exact
trusted source/build/lock/recipe/image evidence, and current configured build,
scan and approval policy. Agent-package approval or image equality alone is
insufficient. This check grants no prediction invocation, provider access or
evaluator access.

An immutable model record retains the approval that was valid at commit.
A later current scan/approval may renew for the same complete immutable
`BuiltinBuild` and profile. Current state/time/policy checks remain mandatory;
same-row revisions and decision times must be nondecreasing, equal revisions exact, and a different
approval ID requires the producer's authoritative current lookup. Renewal does
not rewrite the retained record/outbox or cause an idempotency conflict.
Different source/build/purpose is not equivalent merely because the image matches.
A higher revision can reuse the same still-valid scan; no scan-observation-time
monotonicity is inferred. The decision-time check is intrinsic retained/current
row chronology, not a new authorization claim.

## Asynchronous admission and recovery

`ModelSubmissionAdmission` retains the normalized request/hash, full idempotency
scope, operation ID, historical accepting worker, run revision and acceptance
time. `ModelAdmissionPlan` atomically proposes that record with a pending
`StoredRequest`/`Operation`; it contains no successful model receipt.

`ModelCommitPlan` binds the exact pending/running operation to a completed
operation, `ModelRegistrationRecord` and `ModelRegistrationOutbox`.
The model record contains the typed model, actual configuration, raw artifact
verification, engine binding, original acceptance, committing worker and bounded
provenance identities. Historical acceptance and committing-worker identities
remain separate so a later eligible attempt can finish the same operation.
Same-epoch aliases are rejected; run revisions and commit chronology cannot
move backwards. A later-epoch worker must have a run revision at least as new as
the accepted submission, not only an eventual commit revision that dominates both.
A renewed credential in the same immutable worker launch does not change that
launch's identity.

A completed operation must join the exact model receipt, normalized request,
immutable model record and outbox. Pending/running/failed/cancelled operations
remain explicit; they do not carry a fabricated successful record. Partial
lookup states remain representable in `ModelRegistrationLookup` so runtime
recovery can reject missing/orphaned evidence instead of normalizing it into
absence. `ModelSubmissionReplay` is only the safe existing operation projection;
its shape is not authorization or proof that the private closure was checked.

Real producers must commit each proposal atomically under the original
idempotency uniqueness constraint and current run/lease/CAS checks, and re-read
on conflicts. A lost acknowledgement returns the retained logical operation
only after current complete authorization. Failed validation must be recorded
with the existing explicit safe operation-failure protocol where applicable;
raising a validation error is never reported as a successful commit. There is
no latest-model pointer, new lease counter, SQL implementation, object read
adapter, custom predictor execution or provider/evaluator capability here.

## Necessary EXEC1 integration correction

COMP1's actual-configuration fixture exposed that
`BuiltinPredictionProfile.predictor_version` used the generic `Identifier`
pattern, which rejects dots in the existing frozen value
`strange-physics.linear-spring.analytic.v1`. The earlier synthetic hyphenated
fixture did not exercise this real join.

The narrow correction reuses the existing fixed `PredictorVersion` type for
this private built-in profile and regenerates its schema and fixture digests.
The dependency imports only contracts, without a predictor runtime or import
cycle. Public `PackageManifest` closure and submitted-worker behavior are
unchanged. This is a compatibility repair, not a new predictor version or an
alias for the frozen value.

## Historical API checkpoint

The fixture intentionally uses a SCI-valid coefficient of five with an unknown
fitter and different fit-configuration claim. It includes a purchased failed
scientific record, exact actual-config/native approval identities, pending
admission and a complete model operation/record/outbox example.

Contract tests cover strict bounds, public/private closure, raw versus canonical
identity, actual engine/admission joins, scope and chronology, completed receipt
and outbox substitution, later-attempt commits, partial recovery states and all
retained operation statuses. They also compare frozen model/receipt definitions.
The API checkpoint alone did not verify runtime parsing, authorization ordering,
actual canonical prefix hashing or current approval renewal. Those checks are
now covered by the separately reviewed runtime below. Storage behavior remains
a future producer obligation.

## Runtime behavior and evidence

`model_submissions.admit_model_submission` and `commit_model_submission` are
pure complete-boundary proposal functions. Both first invoke the existing
current worker broker authorization, then validate the independently current
native runtime/artifact/engine projections and status-specific retained closure.
`NativeModelEnvironment` is trusted producer input, not a client request.

Admission creates a pending operation or returns the exact retained operation.
Its completed replay validates the immutable completed closure and current
approval/catalog/readback; it does not refit or reinterpret historical bytes.
Completion additionally consumes actual bounded model and full-ledger bytes,
derives the exact SCI prefix and checks its hash and selected fitting rows.
A completion retry verifies the same historical model/prefix against the current
complete ledger, allowing later observations without rewriting the original
commit provenance. Failed/cancelled operations remain explicit terminal outcomes.

The raw byte caps precede decoding; a lexical depth/node guard precedes strict
JSON decoding, which rejects duplicate keys and nonfinite values. Canonical SCI
encoding uses the existing sorted/compact ASCII-escaped JSON semantics with an
incrementally checked byte limit. This avoids accumulating an unbounded encoded
prefix string; the already bounded typed input still occupies memory. These
reference bounds do not establish scalable database reads or hosted throughput.

The historical first runtime checkpoint, `59ea2ca`, passed 25 focused runtime
cases plus the 94 accepted contract cases. Further tests and independent review
produced the final source checkpoint below.
No database/object adapter, predictor execution or deployed approval is supplied.

Admission replay depends on authoritative immutable completed projections
produced by a previously validated atomic commit. It does not freshly prove raw
model/canonical-prefix correspondence without those bytes. Coherent corruption
of every trusted retained projection is outside this metadata-only replay proof.
Completion/retry checks actual material and rejects mismatched raw-model identity
or scientific provenance; no status-only replay is described as that stronger
verification.

### Final authored source verification

Runtime source `b7c944c0c4065a96a62e777e3d6d2975ba3787d5` passed:

- 2,423 whole-repository tests, including 47 runtime registration cases and
  94 registration contract cases.
- Ruff and formatting checks across 117 files; configured strict mypy across
  78 source files; 764 external JSON Schema fixture checks and reference resolution.
- The configured Bandit medium/high threshold. Existing low-severity findings
  are not described as a zero-finding security audit.
- Offline wheel/sdist building and exact reviewed archive allowlist checks.
  A temporary wheel-only target installation, outside the checkout, verified
  the shipped module identity, callable imports, actual bounded model/ledger
  parsing and canonical model identity using the existing pinned dependency
  environment. The temporary installation and package archives were removed.

All three independent reviewers accepted that runtime. Review included current
authority before poisoned private inputs, partial/status-specific commit witnesses,
renewed credentials and later workers, exact historical prefixes, raw/canonical
identity, approval renewal and mutation-sensitive guard checks. The retained
private author evidence index has SHA-256
`b21ade1a706be6034bbe297f66a1d157c7a15ad3e8ac86123da5e5bddc10654e`.
Prior API and runtime diagnostics remain retained separately; final status prose
does not relabel those earlier checkpoints as proof of the final source.

The final documentation/schema-status change preserves all contract definitions
and runtime behavior. Hosted exact-head CI, protected-main acceptance and the
parent contract freeze are separate integration gates. The local wheel smoke is
not a fresh dependency-install proof, live persistence test, worker isolation
proof, predictor invocation or deployment.

### Producer composition

Use the actual current worker authority, original engine binding, current native
approval and exact verified object readback for admission. Persist the returned
`ModelAdmissionPlan` atomically under the full idempotency key. For completion,
read a consistent complete byte-capped ledger and exact immutable model bytes,
call `commit_model_submission`, and atomically apply the returned `ModelCommitPlan`
with its operation, model record and outbox. Recheck current C2 keyset, run/lease,
launch lifecycle, approval and catalog/CAS conditions in that transaction;
historical launch credential fields are not current authorization fences.

SP-09.d owns durable scientific result producers; SP-13.c owns checkpoint/model
reference commits; SP-16.b owns restore composition; SP-12.a owns cumulative
resource accounting. Those producers must provide consistent indexed, byte-capped
internal reads and retain failure outcomes. An 8 MiB accepted reference envelope
rejects larger histories without truncation; it does not demonstrate that every
otherwise legal 10,000-operation run can be loaded or served at enterprise scale.
