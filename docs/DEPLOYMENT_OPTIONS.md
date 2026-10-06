# First production deployment — decision pending

The architecture review has accepted durable remote jobs and isolated execution
of user-supplied agents and predictors. The cloud provider has not been selected.
This document records factual constraints behind the AWS recommendation.

## AWS reference deployment

Candidate components: ECS/Fargate for application and worker tasks, RDS
PostgreSQL for durable job/workspace metadata, S3 for versioned artifacts, and
SQS for dispatch. A queue is a delivery mechanism, not the authoritative record
of whether an experiment has completed.

- Fargate provides hardware-virtualized isolation between tasks. Containers in
  one task share resources and networking. Run arbitrary agent code in separate
  tasks from the trusted coordinator, simulator and evaluator. This boundary
  follows from [AWS's task isolation guidance](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-fargate-ec2.html).
- Task IAM credentials are accessible to containers inside the task. Give
  untrusted tasks no broad application role or provider secrets. Distinguish
  application roles from the execution role used for image pulls and logging.
  See [task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html).
- A private subnet alone does not establish closed network access. Security
  groups cannot block the VPC Route 53 Resolver, so DNS controls are required
  alongside egress restrictions. See [security-group limitations](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html).
- Fargate restricts privileged containers and host-level capabilities. Do not
  design around nested Docker or assume an in-task sandbox can use those
  privileges. See [Fargate security considerations](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-security-considerations.html).
- SQS Standard can redeliver messages. Use stable identities, durable state
  transitions and fenced worker leases to prevent duplicate logical work. See
  [delivery behavior](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html).
- SQS visibility cannot extend beyond 12 hours after receipt. Dispatch bounded
  work units and checkpoint long investigations rather than treating one queue
  receipt as an indefinite job lease. See [visibility limits](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/best-practices-processing-messages-timely-manner.html).

These are service capabilities and constraints, not proof that an application
configuration is secure or reliable. Validate isolation, authorization, recovery
and restore behavior in the actual deployment before release.

## Managed application platform alternative

A managed platform can reduce application-service operations. However, general
background-worker support does not establish the isolation required for hostile
agent code. For example, Render one-off jobs inherit the parent service's
configuration and environment variables; using that mechanism requires careful
separation of secrets and trust boundaries. See [Render one-off jobs](https://render.com/docs/one-off-jobs).

A managed control plane paired with a separate execution provider remains an
option. It introduces another integration and operational boundary.

## Portability requirement

Keep the simulator, agent messages, job state machine and artifact schemas
independent of the cloud provider. Put task launch, queue delivery and object
access behind small adapters. Define a supported self-hosting configuration
after choosing the reference deployment. Local Docker should not be advertised
as equivalent to a hardware-isolated shared hosted environment.

Choosing AWS accepts responsibility for IAM, networking and deployment
configuration in exchange for a coherent deployment in a customer's cloud
account. No infrastructure has been provisioned.
