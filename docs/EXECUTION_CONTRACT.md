# Package and worker execution contract

Status: EXEC1 API accepted; pure runtime predicates are under independent
review. Real package processing, hosted producers and the full SP-01.c freeze
remain pending.
[ART1](ARTIFACT_CONTRACT.md), [C2](RUN_CREDENTIAL_CONTRACT.md), CORE and SCI
retain their accepted boundaries. This document defines typed inputs and pure
proposal shapes; constructing a trusted record does not verify its provenance.

## Package identity and safe ingress

`PackageManifest` is the only public root in
`contracts/execution.schema.json`. Its reference closure contains only itself
and the accepted generation-bearing `ArtifactRef`. Private storage locators,
inspection/build evidence, internal authority, original admission and runtime
instance identifiers are not public schema roots. There are no public launch,
termination, credential-mint or predictor-invocation routes in this slice.

The manifest is detached from the source archive, so its exact source object
generation does not create a self-referential archive hash. The archive and
manifest have separate package-owned catalog records; neither uses a fictitious
run. Trusted producers must read the exact raw manifest bytes, verify ART size,
hash and generation, decode the strict model within policy caps, and retain that
parsed value with its object evidence. A caller constructing `PackageSource`
does not establish this readback.

The existing `CreateRunRequest.agent_package_sha256` and
`CheckpointBinding.agent_package_sha256` both mean
`message_sha256(PackageManifest)`: the canonical JSON hash of the complete
parsed v1 manifest. This binds the exact source `ArtifactRef` (including raw
archive hash, size and generation), protocol, entrypoint, lock profile/path and
raw lock-content hash. It is distinct from the raw archive hash, the raw
detached-manifest hash, the raw lock hash and the OCI image digest. Reformatting
manifest JSON changes its raw artifact identity but preserves its parsed
canonical package identity. Object generations and identities are never
reconstructed from a digest alone.

Entrypoint validation checks Python module/factory syntax and the declared
profile. It neither imports the package nor verifies Agent conformance.
Configuration-dependent Agent identity belongs to original admission's
`CheckpointBinding`, not the manifest. The later SP-16.b startup producer must
instantiate the configured Agent inside the approved sandbox and check its
actual protocol and `Agent.identity` against the pinned admission identity
before enabling work.

## Explicit policies and provenance

Package, worker and internal-control policies are required, versioned inputs
with no production defaults. Fixture values are synthetic. Adapters must cap
raw metadata, manifest, lock and archive bytes before decoding or allocation.
Decoded limits also bound entry count, canonical relative path length/depth,
individual expanded bytes, cumulative expanded bytes and expansion ratio.
Archive entries are regular files or directories only: no symlink, hardlink,
device, traversal, duplicate path or file-as-parent is accepted. Extraction
must enforce these limits incrementally; a claimed inspection list is not
proof that safe extraction occurred. No pickle or caller-supplied executable
deserializer is permitted.

Agent configuration is bounded by canonical UTF-8 bytes (protocol maximum
262144), depth (32) and structural nodes (10000, including keys). Deployment
policy can be stricter. A decoded structure alone cannot enforce a transport
cap, so adapters must apply predecode byte limits independently. The structural
walk rejects aggregate key/string characters beyond the canonical byte ceiling
before calling the serializer, then applies exact final UTF-8 byte validation.
Resource limits separately bound CPU, wall time, memory, processes, scratch and output;
actual enforcement belongs to later producers. Per-launch ceilings do not
prove remaining cumulative run/workspace resources across replacement attempts:
SP-12.a resource reservation and settlement remains mandatory at actual admission
and dispatch. This slice introduces no accounting ledger.

Package inspection retains the exact verified archive and detached manifest,
canonical source-envelope and policy identities, sorted entry metadata and
actual lock entry digest. A separate trusted lock-resolution record states
that the pinned-lock producer completed validation; a matching raw hash alone
does not prove reproducible dependency resolution.

Build evidence distinguishes the canonical source envelope, raw lock contents,
build recipe, builder image, output runtime image, build policy and verified
build-provenance bytes. Scan evidence binds that exact build and image to its
scan policy, outcome and validity. Approval binds the build, scan, canonical
purpose/profile subject and approval policy. Inspection, lock validation,
build, scan and approval have separate producer identities and times; a model
validator is not a signature verifier or a successful build.

Submitted-agent approval and built-in analytic approval are different kinds.
The built-in source names its configured repository, source commit/tree and
real lock/recipe/build evidence, with no fictitious uploaded package. Its
approved subject includes native-prediction purpose, predictor profile/version
and canonical prediction-configuration digest. COMP1 will bind actual typed
configuration and actual model bytes to that approval. Fitter configuration
digests remain captured provenance unless separately supplied and verified.
Launch consumes the approved immutable image and retained package provenance;
it does not deliver source/archive bytes. Historical available rows inside
PackageSource are inspection provenance, not a current catalog read. Any later
source delivery requires separate current package catalog authorization and
exact-object verification. Current image approval and worker policy remain
mandatory at launch and each relevant broker boundary.

Two independently approved purposes may legitimately yield the same OCI
digest; image equality never substitutes one approval kind for the other.
`WorkerLaunchRecord` accepts submitted-agent approval only, not a native
predictor/evaluator launch.

## Original admission and current state

`OriginalExecutionAdmission` joins the actual retained `CreateRunRequest`,
its exact completed `StoredRequest`/run-creation Operation, the original
admitted RunView and RunOwnership, and the actual server-selected bounded
configuration plus CheckpointBinding. It recomputes request/configuration
hashes, checks immutable principal/workspace/run/space/budget joins and
preserves the original wall deadline and package/config/runtime identity.

The named C2 `admit_run_ownership` producer commits the initial queued,
revision-zero, zero-experiment run and ownership together; EXEC1 retains that
original snapshot. This is an internal producer requirement, not a new
restriction on the frozen generic `RunCreationResult`. Its run value may
contain later mutable counters/status. Runtime recovery compares current run
identity, immutable experiment space and total budget to original admission;
it must not require current remaining budget, experiment count, status or
revision to equal their initial values. World version and track are taken from
the digest-bound original request. Server-selected configuration and identity,
which the public creation request does not carry, must be atomically retained
by the original admission producer, never invented at launch.

Historical creator/leaf-key metadata identifies the admission receipt; it
does not become a live launch dependency. Current durable ownership,
principal/grant generations and incarnations, workspace, lease and C2
credential state remain separate mandatory authority checks. Replacement or
retry cannot reset the original deadline or increase original resource caps.
Current stricter policy may deny work.

## Launch, dispatch and broker ordering

The producer sequence is:

1. Admit the logical current attempt and running lease with the immutable
   original ownership/deadline.
2. Issue the C2 keyset under its existing current-running requirements.
3. Atomically persist the exact launch record, initial lifecycle and command
   outbox with run/keyset CAS expectations.
4. Dispatch by that immutable launch identity, retain unknown outcomes, and
   confirm the exact provider instance before enabling broker work.

Fresh launch requires an authoritative lookup and a database uniqueness
invariant on `(workspace_id, run_id, attempt_id, lease_epoch)` (or an equivalent
exact key). The producer atomically guards that unique row, the current run/
keyset CAS and the launch/lifecycle/outbox insertion. An existing immutable
launch wins; partial evidence requires recovery and cannot justify a second
launch. The private lookup always carries the exact workspace/run/attempt/epoch
key, including for an empty result. A caller-supplied empty lookup is not proof
of authoritative absence. There is one immutable dispatch outbox per launch.
An insertion conflict requires rereading the retained launch and comparing the
actual full request hash, rather than relying on unchanged run/keyset CAS.

Logical `RunStatus.running` is not proof of a running process. `prepared`
and `dispatch_unknown` are not work-authorized states; `active` requires an
exact bound instance. Cancellation, lost acknowledgements or replacement
between any two stages must fence the exact launch and reconcile durable
outbox/instance evidence. Missing or partial projections fail closed, not as
permission to dispatch again. A current launch receipt is metadata, not an
execution capability. Launch creation cannot predate its retained approval
decision and must fall before that retained scan expires; current approval
validity is an additional runtime requirement.

Internal launch and termination authority is purpose-bound
(`workers:launch` or `workers:terminate`), with current trusted issuer,
audience, principal identity/generation, revocation and expiry. These are
internal producer capabilities, not additions to public/service/run scopes
and not aliases for C2 `run-credentials:manage`. Launch authority is scoped to
a run; termination also names the exact immutable launch. Runtime admission
must validate current projections and all duplicate joins before replay.

The broker operation map is closed:

| Broker operation | Existing product permission |
| --- | --- |
| list_experiments | experiments:read |
| execute_experiment | experiments:write |
| save_checkpoint | checkpoints:write |
| submit_model | models:write |

Every operation composes the existing mandatory `authorize_product` entry
point: current ownership/generation/incarnation/workspace/lease/credential
checks, then that operation's current role permission, immutable creation
ceiling and bounded worker scope. A valid credential tuple is not blanket
broker authority. `models:write` gives no predictor invocation, provider call
or evaluator-label access. Provider/model-call operations remain unregistered
until SP-17.a's later reviewed contract and implementation.

Every relevant broker operation, commit and payload batch, positive launch
replay and re-dispatch must also establish current exact runtime approval and
required available isolation/network policy. Retained approval is provenance,
not perpetual permission. Revocation, expiry or inability to establish
required isolation denies further work and requires exact-launch fencing and
termination. Fenced/stopping/stopped states cannot resume work even if policy
or approval later recovers. No cached grace period is authorized.

## Exact termination and recovery

Termination remains possible for an exact older retained launch after lease
advancement, cancellation, owning-principal disable, workspace quarantine or
approval/isolation loss. It requires independent current internal termination
authority. It does not require the old worker credential, owner or policy to
be work-authorized. This distinction must not enable a stale acknowledgement
to stop a newer launch or mutate the current lease/global run status.

Normal Agent completion and experiment-budget exhaustion use the explicit
`completed` and `budget_exhausted` reasons, with the same irreversible fence
and exact-instance reconciliation. The later SP-16 completion/settlement
producer supplies the reason from its current run evidence; a reason string
alone establishes neither successful science nor a completed global run.
Normal exit must not masquerade as operator cancellation.

A termination proposal binds the exact launch and body hash, expected
per-launch lifecycle revision, irreversible fence, retained termination record
and exact command outbox. Its acceptance and first irreversible fence cannot
predate the retained launch creation. The completion model binds the original request,
fence and trusted outcome evidence to that same lifecycle. Completion requires
the retained first fence to exist by the original acceptance time, even when
subsequent per-launch lifecycle revisions have advanced. A known instance
must match its provider namespace, instance and launch identity. A
`terminated` outcome requires that exact instance; `never_started` requires
positive reconciliation after dispatch of that launch is fenced. Unknown
outcomes remain pending/recovery-required and cannot be converted into success
by assuming that an instance was never created.

A stopped lifecycle cannot be reopened. An old exact-launch acknowledgement
can settle only that retained launch's CAS; current run/lease settlement and
scheduling a replacement are separate controller obligations. No process is
created or terminated by these pure proposal models.

## API checkpoint evidence and next producers

`execution.examples.json` is synthetic and contains all named models plus
structural and semantic negative cases. The generated JSON Schema describes
structural validation; cross-record joins and transition invariants additionally
require the Python model validators. Independent raw-schema checks deliberately
distinguish these two classes. Tests cover public-schema closure, distinct
hashes, purpose substitution, original-admission corruption, irreversible
fences and stale termination acknowledgements.

This checkpoint implements pure admission against supplied trusted projections;
it does not implement package extraction,
a lock resolver, build/scan/promotion service, token verification, resource or
network isolation, a scheduler, object/SQL atomicity, or live recovery drills.
Bounded pure admission/replay/broker/termination predicates test unavailable,
partial and stale evidence; later hosted producers must establish its origin
and currency. SP-01.c remains open through EXEC1 acceptance and COMP1.

Later production ownership remains SP-14.a extraction/pinned-lock validation,
SP-14.b isolated builds, SP-14.c scans/promotion, SP-15.b resource admission,
SP-15.c the scoped broker, SP-15.d network isolation, and SP-16.a–c orchestration,
recovery and termination. SP-17.a owns provider-call contract freeze.
SP-19.a retains the full custom predictor protocol and execution scope.

## Pure runtime boundaries and retained recovery

The complete pure launch boundary is `admit_worker_launch`; it composes
current purpose-bound internal authority, current C2 ownership/keyset, current
workspace and exact policies/approval/isolation before reading retained
launch or restore evidence. `advance_worker_launch` uses that same admission
before proposing dispatch or exact-instance confirmation.
`authorize_worker_broker` composes current `authorize_product` for the named
closed-map operation, checks duplicate current projections and current runtime
policy, and permits work only in the confirmed active lifecycle.
`terminate_worker_launch` and `complete_worker_termination` require their
separate current internal authority and exact retained launch closure, without
requiring the old launch to remain work-authorized.

These functions return immutable proposals or safe metadata; they do not
read authoritative storage, verify signatures, commit SQL or control a
provider process. The producer must obtain one current authoritative
snapshot and recheck its relevant authority, run/keyset/lifecycle CAS, policy,
uniqueness and resource reservations in the transaction that commits the
proposal and outbox. In particular, a policy-denial exception does not itself
persist a fence: the later controller must durably fence and request exact
termination on approval/isolation loss before allowing any subsequent work.
Reapproval cannot reactivate an already fenced lifecycle.

Current same-attempt credential rotation is accepted with the newer current
pointer, generation and keyset revision; the launch's original leaf is retained
provenance. A revoked or expired presented worker credential fails before
broker replay. Current run progress may advance, but immutable original
ownership, space, total budget, package/config/runtime identities and deadline
remain pinned. Current policy may be stricter than original admission.
The fixed acyclic lifecycle admits only reachable revision ranges; exact
no-op replay does not increase a revision. Retained termination completion
cannot predate that termination's acceptance.

A requested restore has an explicit transient `RestoreCandidate`: actual
complete Operation ledger, scoped ART1 target/latest/head/outbox closure,
current artifact readback and required artifact policy. Candidate presence
must exactly match the requested reference; there is no automatic latest
selection. The selected record and outbox are mandatory. Its index, full
ordered request hash and record hash must match the reference; target/latest
history and current run revision/attempt lineage must also agree.
The shared non-authorizing `checkpoint_committed_prefix` validates the
complete ordinal range, unique operation IDs, exact workspace/run/count and
the existing 10,000-operation cap before deriving the contiguous observed
prefix. A completed Operation with a failed scientific record advances this
prefix; pending/running/failed/cancelled Operations without a committed record
block it even if later ordinals completed. Initial index -1 remains compatible
with a pending first reservation, and an older compatible target may precede
a consistent later head. All ledger/run/head/catalog projections must share
the producer's authoritative snapshot; commit rechecks the relevant fences.
This validation returns no checkpoint payload and grants no read authority.

The full-body ledger is a conformance input, not a scalable database read
strategy. Count caps alone do not bound trajectory materialization adequately.
Before production, SP-09.d durable result commits, SP-13.c checkpoint/model
reference commits and SP-16.b restore must supply a separately reviewed
internal transactional metadata/closure projection with byte-capped paginated
reads, exact operation/ordinal/status/body-hash joins and gap checks. Neither
a client-supplied prefix scalar nor full trajectory materialization on every
restore is an acceptable substitute. SP-12.a owns cumulative resource
reservations; SP-11 owns authorization/RLS. This slice does not implement
that future storage projection or claim scalable storage enforcement.
