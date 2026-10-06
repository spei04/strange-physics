# Google Cloud reference deployment

Google Cloud is the accepted provider because existing credits are available.
The GitHub repository remains in the personal account `spei04`. The principal
service mapping and separate development/production projects were accepted in
architecture-review round 3. Detailed configuration remains under review.
No infrastructure has been provisioned.

## Accepted principal services

| Responsibility | Google Cloud component |
| --- | --- |
| Web application, authenticated API, coordinator and model gateway | Cloud Run services |
| Uploaded Python agents and submitted predictors | Separate GKE execution cluster using GKE Sandbox |
| Workspace permissions, run state, budgets, experiment identities and outbox | Cloud SQL for PostgreSQL |
| Trajectories, checkpoints, manifests, predictors and replay assets | Cloud Storage |
| Short dispatch and reconciliation operations | Cloud Tasks |

Artifact Registry for versioned images and Secret Manager/workload identity for
trusted-service credentials remain proposed supporting components. Provider and
service selection do not approve a specific IAM policy or secret-access path.

Use separate development and production projects linked to the eligible billing
account. This boundary is accepted but not yet provisioned. Keep
unrelated applications outside these projects. Organization/folder placement,
regions and IAM must be resolved from actual permissions and project policies.

## Submitted code and isolation

GKE Sandbox explicitly supports untrusted and third-party code. Use a separate
execution tier with an isolated unit for each investigation, resource limits and
network policy. Permit only authenticated operations on the run broker. Do not
provide user code with Kubernetes service-account tokens, broad cloud IAM roles,
model-provider credentials, database access, shared writable volumes or hidden
evaluation assets. Submitted predictors evaluated on blind inputs should have
no network. These are proposed controls informed by [GKE Sandbox documentation](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/sandbox-pods)
and [GKE network policy](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/network-policy).

DNS policy belongs in the isolation tests: blocking ordinary internet traffic
while allowing arbitrary public DNS queries still leaves an exfiltration path.
Use fixed broker endpoints or an allowlisted resolver. Run-scoped broker
credentials authorize only the operations and artifacts needed by that run.
The simulator and evaluator execute separately from arbitrary agent code.

Cloud Run is not inherently unsuitable for isolated execution: Google documents
a virtual-machine-monitor boundary and multiple isolation layers. The GKE
recommendation favors explicit workload lifecycle, network and metadata controls
for submitted code. Cloud Run Jobs remain an option for trusted reference sweeps.
See [Cloud Run security](https://docs.cloud.google.com/run/docs/securing/security)
and the [runtime contract](https://docs.cloud.google.com/run/docs/container-contract).

Validate the pinned scientific stack under the selected GKE Sandbox runtime.
Service capabilities alone do not establish application-level isolation or
correctness; exercise adversarial access, termination and recovery tests.

## Durable dispatch and execution

Cloud Tasks dispatches a short, idempotent operation to ensure that an execution
exists. It must not hold open an HTTP request for the whole investigation. HTTP
handlers have a maximum deadline of 30 minutes, and duplicate task executions
can occur. See [HTTP target deadlines](https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks)
and [duplicate executions](https://docs.cloud.google.com/tasks/docs/common-pitfalls).

Record launch intent in a transactional outbox. Use deterministic execution IDs,
unique experiment-step keys, worker leases with fencing, and reconciliation.
PostgreSQL is authoritative for whether an experiment consumed budget; the
queue is not. Checkpoint committed experiment boundaries and make cancellation
and partial failure visible. External provider attempts need their own records
because ambiguous responses can still incur cost.

Cloud Run CPU job tasks can be configured up to 168 hours, but maintenance can
break outbound VPC connections. Do not use task lifetime as a durability
guarantee. See [job timeout and maintenance](https://docs.cloud.google.com/run/docs/configuring/task-timeout).

Pub/Sub is not required for initial job dispatch. Revisit it when independent
consumers need the same events. Its exactly-once feature does not make external
model calls or database side effects transactional. See [Cloud Tasks versus Pub/Sub](https://docs.cloud.google.com/tasks/docs/comp-pub-sub)
and [exactly-once delivery scope](https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery).

## Durability and artifacts

Recommend regional high availability for the production database, automated
backups, point-in-time recovery and tested restoration. Cloud SQL supports
cross-zone replication in its [HA configuration](https://docs.cloud.google.com/sql/docs/postgres/high-availability).
Protect immutable artifacts with hashes, object generation identifiers and
[generation preconditions](https://docs.cloud.google.com/storage/docs/request-preconditions)
for safe retries. Replication, backups and artifact reproducibility serve distinct
purposes; test all required recovery paths.

The accepted load target is 100 simultaneous investigations per deployment.
Verify CPU/IP quotas, database connection limits, provider rate limits, workload
resource requirements and startup behavior before claiming that capacity.

## Credits and account verification

A Google login identifies a user; it does not establish the resource organization,
project owner, billing account or applicable credit balance. Project usage is
charged to its linked billing account. Credits can have scope and expiry
conditions. Check the actual credit-bearing account, credit eligibility and
expiration before provisioning. See [Cloud Billing setup](https://docs.cloud.google.com/billing/docs/how-to/create-billing-account)
and [billing/credit details](https://docs.cloud.google.com/billing/docs/how-to/resolve-issues).

Keep account identifiers, credit balances and organization-specific settings
outside public documentation. The personal GitHub repository and Google Cloud
resource ownership are separate decisions. Do not assume the selected cloud
identity can create projects, attach billing or bypass organization policies.

## Portability

Keep the simulator, agent messages, job state machine and artifact schemas
independent of Google Cloud. Put execution launch, queue delivery and object
access behind small adapters. Document a supported self-hosting configuration.
Local Docker is useful for trusted development but should not be advertised as
equivalent to the hosted isolation boundary for arbitrary customer code.
