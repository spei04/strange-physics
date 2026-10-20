# Initial staging configuration and cost proposal

SP-02.c preparation. **Approval pending; no provisioning authorization is
recorded by this document.** Pricing checked on 2026-10-19 using the primary
Google Cloud sources below. Reprice the exact reviewed infrastructure plan before
approval. Dedicated project details, credit coverage/expiry and target-project
permissions/quotas remain unverified.

This is the smallest proposed environment for exercising the accepted Cloud Run,
GKE Sandbox and regional HA PostgreSQL architecture. It is not evidence of
production readiness or a new architecture decision. The separate development
disk/snapshot proposal is outside this bill of materials and remains subject to
its own approval.

## Validation boundary

Use a dedicated staging project in **us-central1**, isolated from development and
production. Use synthetic studies and invited test identities. Preserve the
existing shared development VM and every other project's resources.

The first deployment should test a real authorized run, immutable artifacts,
cancellation/recovery, tenant denial, sandbox compatibility, database failover
and a restore into isolation. Tests run only when their producer code and security
gates exist. A zonal worker cluster cannot establish regional worker availability,
the 100-investigation capacity target, official benchmark validity or customer
SLOs. Those need separately sized and approved environments/tests.

## Proposed configuration

| Component | Initial setting | Bound or unresolved detail |
| --- | --- | --- |
| Region/project | Dedicated staging project; us-central1 | Exact project, organization, billing/credits, IAM and quotas must be verified |
| GKE | Standard zonal cluster in us-central1-a | Supported version/patch and compatibility evidence pinned before apply |
| System pool | One e2-standard-2, 2 vCPU/8 GiB, 50 GiB pd-balanced | Trusted system/egress components only; no submitted workloads |
| Sandbox pool | One e2-standard-4, 4 vCPU/16 GiB, 50 GiB pd-balanced; COS/containerd; explicit gVisor | Fail closed if sandbox unavailable; no GPU; no autoscaling or node auto-provisioning |
| Worker admission | One active investigation; builds serialized with investigations | Initial agent/predictor 1 vCPU/2 GiB; build 1 vCPU/4 GiB; hard wall/output/ephemeral limits frozen after compatibility tests |
| Cloud Run | Web, API/run broker, coordinator and model gateway; distinct appropriate identities | Request billing; min 0; API max 2, others max 1; initial 1 vCPU/512 MiB each |
| Trusted simulation/evaluation | Separately authorized jobs, aggregate concurrency 1 | Initial 1 vCPU/2 GiB; no blind truth in agent/gateway identity |
| Cloud SQL | Enterprise PostgreSQL; regional HA across two us-central1 zones; 2 vCPU/7.5 GiB; 20 GiB SSD; private IP | Supported major version pinned; storage growth capped at 50 GiB; deletion protection |
| SQL recovery | Daily backups, seven retained; explicitly enabled seven-day PITR | One temporary equivalent restore instance for at most 24 hours in validation window |
| Artifacts | Regional Standard GCS; private uniform access/public-access prevention | 100 GiB initial usage assumption; generation/hash/size verification and current DB authority |
| Images | Regional Artifact Registry, quarantined builds and approved digests | 20 GiB usage assumption; scanning/cleanup and dependency mirror policy reviewed |
| Dispatch | Cloud Tasks and bounded reconciliation | Queue rate 2 dispatches/second, max 2 concurrent dispatches; application run limit remains 1 |
| Secrets/identity | Secret Manager, keyless CI and scoped service identities | No provider/platform credentials in submitted code; public ID contracts remain unfinished |
| Network | Private GKE nodes, private SQL, Private Google Access; one NAT address for approved egress | Broker-only agent policy and networkless predictor must pass negative tests |
| Telemetry | Safe operational logs/metrics and private evidence | Initial 10 GiB/month log-volume assumption, sampled diagnostic detail; redaction and retention reviewed |

Standard GKE Sandbox requires at least one non-sandbox node in a separate pool.
Advertised node vCPUs are not a usable-job capacity guarantee: system reservations
and gVisor/SMT behavior must be measured. Do not enable SMT solely to reach a
throughput claim. Set upgrade surge to zero and accept planned staging disruption
unless a separately priced surge is approved. Runtime admission must prevent
submitted work from falling back onto the system pool.
[GKE Sandbox requirements](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods),
[configuration](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/sandbox-pods).

Keep the approved modular API/run-broker arrangement. An agent reaches a trusted
egress proxy with fixed broker destination, method and route allowlists plus
run/attempt/epoch authorization. Shared Google IP allowlisting alone does not
restrict access to the broker. Block alternate DNS, metadata, private-network
escape, redirects and IPv6 bypasses. Predictors have no outbound path, including
DNS. Build dependency retrieval is separately constrained and cannot use deploy
credentials. Uploaded code remains disabled until these deployed controls pass.

Use Direct VPC egress for Cloud Run's private SQL access rather than introducing
a connector solely for that path. Role/pool limits and aggregate instance limits
must leave database headroom for migrations and recovery; no connection per SSE
viewer. Configure current membership checks, tenant RLS and separate migration
ownership in the actual backend.
[Direct VPC egress](https://docs.cloud.google.com/run/docs/configuring/vpc-direct-vpc).

Explicitly enable PITR: Enterprise instances created through Terraform/API do not
enable it by default. Verify seven-day retention and actually restore into a new
isolated instance; a backup setting is not recovery evidence. HA failover and
backup recovery address different failure modes.
[Cloud SQL recovery](https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/restore?hl=en),
[HA](https://docs.cloud.google.com/sql/docs/postgres/high-availability).

## Price basis

USD on demand, 730 hours/month, no free-tier, promotional credit, commitment,
tax or support adjustment assumed. HA rates below already include HA pricing;
do not double them again. Storage charges depend on provisioned capacity or
actual retained bytes as specified.

| Item | Calculation | Monthly USD |
| --- | --- | ---: |
| GKE node compute | 730 × (0.06701142 + 0.13402284) | 146.76 |
| GKE cluster management | 730 × 0.10 | 73.00 |
| Two node disks | 100 GiB × approximately 0.10/GiB-month | 10.00 |
| SQL HA CPU/memory | 730 × (2 × 0.0826 + 7.5 × 0.014) | 197.25 |
| SQL HA SSD | 20 GiB × approximately 0.34/GiB-month | 6.80 |
| NAT two-node endpoint/address basis | 730 × (2 × 0.0014 + 0.005) | 5.69 |
| **Configured resource floor** | Before traffic and retained-data usage | **439.50** |
| GCS artifact usage assumption | 100 GiB × approximately 0.02/GiB-month | 2.00 |
| Artifact Registry usage assumption | 20 GiB × approximately 0.10/GiB-month | 2.00 |
| SQL backup usage assumption | 100 GiB × approximately 0.08/GiB-month | 8.00 |
| **Configuration plus stated storage usage** | Sum before consumption allowance | **451.50** |

Compute/cluster/disk inputs:
[Compute pricing](https://cloud.google.com/products/compute/pricing/general-purpose?hl=en),
[GKE pricing](https://cloud.google.com/kubernetes-engine/pricing),
[disk pricing](https://cloud.google.com/compute/disks-image-pricing).
Database inputs: [Cloud SQL pricing](https://cloud.google.com/sql/pricing?hl=en).
Data/network inputs: [NAT pricing](https://cloud.google.com/nat/pricing),
[Cloud Storage pricing](https://cloud.google.com/storage/pricing),
[Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing).

**Low-traffic planning range: approximately $450–550/month before credits.**
The stated configuration/storage basis costs about **$104 for seven days**.
This is an estimate, not an invoice cap. Unverified retention, traffic and
resource requirements can move it outside that range.

Consumption dimensions are separate:

- Cloud Run request-billed active CPU is $0.000024/vCPU-second, memory
  $0.0000025/GiB-second, plus $0.40/million requests at the selected region/rate.
  Five continuously active 1-vCPU/0.5-GiB service instances would cost about
  $332/month before requests, showing why a low-traffic estimate is conditional.
  Jobs add their own billed runtime. Max-instance settings can temporarily
  overshoot and are not a billing guarantee.
  [Cloud Run pricing](https://cloud.google.com/run/pricing).
- NAT processing is $0.045/GiB in addition to endpoint/address and network
  transfer charges; additional endpoint usage changes the basis.
  [NAT pricing](https://cloud.google.com/nat/pricing).
- Storage operations, image scans, logs/metrics, secret accesses/versions,
  identity usage, queue operations and internet/cross-zone transfer depend on
  measured usage. Allow approximately $0–100/month initially rather than
  presenting them as free. Retained versions, soft-deleted objects and backups
  also consume storage; an application upload quota alone cannot cap them.
  [Secret Manager](https://cloud.google.com/secret-manager/pricing),
  [Cloud Tasks](https://cloud.google.com/tasks/pricing),
  [Registry scanning charges](https://cloud.google.com/artifact-registry/pricing).
- A temporary equivalent HA SQL restore instance for up to 24 hours adds about
  $7 in compute/provisioned storage before backup/traffic; reserve $10 for that
  test. The original instance remains protected until restoration is verified.
- **Model spend starts at zero using a fake provider.** A real-provider trial
  requires a separate capped request/token/cost plan; a cloud credit balance does
  not prove provider coverage. No official sweep or customer traffic is included.

## Proposed approval envelope and stop behavior

Propose a **seven-day validation window with a $250 operational authorization
envelope**. No resource creation happens until the exact plan and permissions are
approved. Review daily usage; alert at $125, $175 and $225; stop new admissions
at $175 or before the window expires, leaving reconciliation/teardown headroom.

This is an operational limit, not a guaranteed invoice hard stop. Billing data
lags, existing resources keep charging during recovery, and alerts do not stop
resources. Enforce resource counts, run deadlines, storage limits, queue
concurrency and credential scopes independently. Any expansion, real model trial
or extension needs a new reviewed estimate and authorization.

Attach owner, purpose and expiry metadata to staging resources. The approval
must explicitly cover teardown authority and retained-data costs. A proposed
30-day review of synthetic staging evidence/final backups is a review date,
not permission to delete unique incident/release evidence. Verify applicable
service retention/soft-delete rules before promising a deletion date.

## Rollback and teardown

1. Stop admission and revoke new launch authority; reconcile every accepted
   operation, lease, artifact reference and held allowance.
2. Roll back trusted service revisions and worker image digests if compatible.
   Database changes use expand/contract migration and verified restore paths;
   no destructive schema rollback or blind replay of paid provider calls.
3. Restore/PITR into isolation when needed; fence old epochs and reapply current
   membership, deletion and revocation records before reopening access.
4. Verify required private evidence and final backup identities outside disposable
   runtime resources. Keep explicit owner/source/purpose/review metadata.
5. Remove approved staging compute, queues/schedulers, NAT/IPs and unused images
   after checking consumers. Retain required backups/artifacts under the approved
   policy and report their ongoing charges. Do not delete the whole project as
   a shortcut or alter shared development resources.

## Remaining gates

| Gate | Required before proceeding | Owner |
| --- | --- | --- |
| Target account/project | Exact project, organization/billing attachment, private credit coverage/expiry proof, target IAM and quota/region checks | Product owner + Platform |
| Concrete configuration | Reviewed IaC plan, supported runtime/database versions, APIs and service identities; cost dimensions checked against actual resources | Platform + security |
| Authority and spending | Seven-day scope, $250 envelope, recovery test, retention and teardown authorization | Product owner |
| Contract/policy safety | Required ID/ART/EXEC/WEB producers, deployed tenant/network/sandbox tests, pinned approved images | Backend + Platform + security |
| Completion evidence | Configuration/policy checks and producer/consumer review; record actual approval rather than infer it from backlog approval | Technical lead |
| Later expansions | Real providers, benchmark sweeps, customer access, capacity/DR expansion and production release | Their separate named gates |

SP-02.c stays pending until concrete configuration, permissions and spending are
approved and its required checks/review pass. Publishing this proposal does not
enable an API, change IAM, purchase resources or release a production service.
