# Final implementation defaults — proposed

These recommendations close the remaining architecture choices. They are not yet
approved or implemented. Exact compatible package versions will be selected and
locked when scaffolding; numerical thresholds will follow development measurements.

## Application interfaces

Use Python/FastAPI for the API and Python/NumPy/SciPy for simulation and fitting.
Use TypeScript, React, Vite and Canvas 2D for the web interface. Exchange validated
HTTP/JSON requests and stream committed events over server-sent events with a
durable resume cursor. Avoid a second browser implementation of the physics.

Generate the TypeScript API client from a versioned OpenAPI schema, with stable
operation IDs and a CI check for generated changes. FastAPI supports this
[client-generation workflow](https://fastapi.tiangolo.com/advanced/generate-clients/).
Keep the Python agent/checkpoint SDK as a small deliberate interface around the
same validated contracts. A raw generated HTTP client is not the entire agent SDK.

## Identity and workspace permissions

Google Identity Platform supports both [Google sign-in](https://docs.cloud.google.com/identity-platform/docs/web/google)
and [GitHub sign-in](https://docs.cloud.google.com/identity-platform/docs/web/github).
Use separate development and production provider configurations. Request only
the scopes needed to sign in; GitHub login does not require repository access.

Keep workspace memberships, invitations and owner/researcher/viewer roles in
PostgreSQL, keyed by the verified identity-provider user ID. A user may join more
than one workspace. Identity Platform tenants isolate user populations and
provider settings; they are not required simply to model application workspaces.
See [Identity Platform tenants](https://docs.cloud.google.com/identity-platform/docs/multi-tenancy).

Verify signed ID tokens in the API, then enforce current account and membership
status from application state. Avoid placing an entire membership list in token
claims: updates require refreshed tokens and claim size is limited. See
[ID-token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
and [custom claims](https://firebase.google.com/docs/auth/admin/custom-claims).

Self-hosted deployments use a documented OIDC adapter. Specify issuer, audience,
key discovery and verified subject mapping explicitly; never treat an arbitrary
decoded token or email domain as authentication or workspace membership.

## Infrastructure, images and credentials

Use Terraform for repeatable infrastructure and GitHub Actions for checks and
releases. Use [Workload Identity Federation](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)
for short-lived deployment credentials. Restrict trust to the intended repository,
owner and approved deployment context; use immutable numeric repository/owner
identifiers where supported. Do not add long-lived Google service-account keys
to GitHub to work around integration problems.

The [Google GitHub authentication action](https://github.com/google-github-actions/auth)
documents a Firebase Admin SDK limitation with its federation credentials. Run
runtime token verification under the application's Google Cloud service identity.
Keep CI deployment operations on supported Terraform and Google Cloud APIs.

Store runtime images in Artifact Registry and secrets in Secret Manager. Workload
identity does not eliminate all secrets: GitHub OAuth and user model providers
still need appropriate credentials. Only trusted gateway/application services
may access those secrets; uploaded code must not inherit them.

Build uploaded packages in an isolated build environment with pinned manifests.
Do not execute package installation hooks in a trusted deployment pipeline. Check
the final artifact digest before launch and record it in the run manifest.

## Availability, retention and scientific defaults

Start with a single US primary region, multi-zone production PostgreSQL, automated
backups and exercised restore procedures. Select the exact region after verifying
service compatibility, permissions and capacity. Publish achieved operating
limits only after measurement; a design target is not a verified availability SLA.

Keep customer run artifacts until an authorized owner deletes them or configures
a retention policy. Distinguish customer artifacts, operational diagnostics,
backups and immutable published reference releases; each has its own lifecycle.
Document when deletions stop being recoverable from backups and preserve required
release records. Local temporary diagnostics retain the existing 30-day review
rule. No bulk deletion is implied by this proposal.

Choose solver step size, sensor noise, feature grids, detector thresholds and
suite sizes on development worlds. Record rationale and sensitivity checks,
then freeze configurations before scored evaluation. The accepted 40-experiment
default, visible world information and primary scoring choices remain fixed
unless the design is explicitly revised.

## Implementation handoff

After approval, start with the M0 simulator, typed contracts, package interfaces
and tests. Then complete evaluation and durable execution against those contracts.
Routine reversible engineering choices can follow project conventions and the
accepted constraints, with significant decisions recorded in the repository.
Surface changes to product scope, trust boundaries or scientific claims.

The complete release still requires hosted investigations, private workspaces,
isolated submitted code, recovery tests, self-hosting and an external integration.
Neither the local scaffold nor a successful animation fulfills that release gate.
