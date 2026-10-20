# CI and unpublished release candidates

CI-01 adds a baseline for the current Python research package. It does not
implement the hosted service, deploy infrastructure, publish packages, or
establish production readiness. The scientific, identity and artifact contract
gates in the execution backlog remain separate.

## Required checks

Every push to main, pull request and manual dispatch runs:

- Python 3.12 and 3.14: Ruff lint/format, strict mypy, the entire pytest suite,
  external JSON Schema fixtures/reference resolution, offline wheel/sdist
  builds with archive inspection, and the eight-particle/eight-experiment
  spring investigate/inspect smoke.
- Locked dependency vulnerability checking with pip-audit, including development,
  build and security-tool groups. Advisory lookup failures fail the job.
- Bandit on application and CI script code at medium severity and above.
  This is a proportionate static baseline, not a penetration test or proof of
  absence of vulnerabilities.

The final required check is named exactly **CI gate**. It uses `always()`,
depends on every required job, and accepts only `success` from each. Failed,
cancelled, skipped, missing and unknown results fail. A skipped optional
candidate job is not a substitute for this check. New required jobs must be
added to both its `needs` list and the tested aggregate predicate.

Dependencies install only in bootstrap steps from `uv.lock` with uv 0.11.21.
The project installs as a regular wheel offline against the locked Hatchling
backend; editable-build helpers are not required. Check steps
use `uv run --no-sync`; they cannot silently resolve a new environment.
The vulnerability job exports pinned, hashed requirements from the same lock,
then disables pip-audit dependency resolution. Scientific smoke tests run the
local simulator without provider credentials or model calls. Schema fixtures
are synthetic interface data, not experiment or benchmark results.

All jobs run on GitHub-hosted runners with bounded timeouts, workflow/ref
concurrency and a read-only contents token. Checkout does not persist
credentials. Actions use verified full commit pins, with release labels kept
as review hints. There are no privileged PR triggers, deployment credentials,
package publication permissions or consumption of artifacts from another run.

## Delivery gate and bootstrap

The candidate job runs only after this run's CI gate succeeds, on a push or
manual dispatch for `refs/heads/main`, when GitHub reports
`github.ref_protected == true`. Pull requests and other branches cannot deliver
a candidate. Unknown/unprotected branch state fails closed by skipping
delivery. A manual dispatch reruns every required check before delivery; it
does not bypass verification.

**Repository settings are managed separately from this change.** At authoring,
the full-SHA Actions policy was enabled, but the stable CI gate was not yet
live and main protection was pending. The
settings owner must verify that main requires the exact CI gate, restricts
bypasses and direct writes appropriately, requires review under the chosen
policy, and keeps Actions tokens read-only and external-fork execution behind
maintainer approval. `ref_protected` establishes that GitHub applies a rule or
protection to the ref; it does not prove the rule has all those settings.
Do not describe delivery as policy-verified until the settings owner records
that separate read-back evidence.

Only `spei04` is currently configured as a code owner. GitHub does not let a
PR author approve their own PR. Independent source review by the engineering
agents is recorded separately and must not be represented as an independent
GitHub account approval. Add an authorized human collaborator before depending
on mandatory independent GitHub approvals; any bootstrap exception must be
explicit, recorded and removed. Do not silently weaken protection to get a
green run.

After the gate is live and settings are verified, dispatch CI against protected
main and retain the run URL, source SHA, check results, artifact identifier and
protection evidence. A checked-in workflow or passing PR with delivery skipped
is not evidence of an actual successful delivery.

## What a candidate contains

A candidate is an unpublished installable wheel and source distribution of the
reviewed package version. It is not a public release or a deployed service.
Before delivery, the archive validator enforces an exact package-file allowlist,
compares package bytes with the checkout, checks metadata identity and rejects
extra archive files, links, duplicate/unsafe paths and oversized members.
Build commands use uv's supported `--no-create-gitignore` option so its default
output-directory marker does not relax that allowlist.
The tracked public `.gitignore` is included in the source distribution as one
explicit metadata file and must match the reviewed checkout byte for byte; no
other dotfile is allowed. The output directory still rejects a `.gitignore`.
The source distribution deliberately excludes tests, docs, runs, private
evidence and environment files. New package modules require an explicit
allowlist review.

The job then creates a fresh environment with only the hashed runtime
dependencies exported from the lock and the candidate wheel installed without
dependency resolution. It checks installed metadata dependencies, runs outside
the checkout, removes Python path overrides, verifies the import comes from the
fresh environment, checks development/build tools are absent, and executes the
spring investigate/inspect smoke through that environment's CLI. It never uses
`uv run` or a source-project fallback for this acceptance step.

Only the validated wheel, source distribution, `provenance.json` and
`SHA256SUMS` are uploaded. Provenance identifies the source commit, repository,
workflow run/attempt, Python/uv versions, lock checksum, exported runtime-lock
checksum and distribution hashes/sizes. These are integrity and traceability
records, not signatures or an attestation of independent authorship. Smoke
outputs and raw observations are not uploaded.

Artifacts expire after seven days. An approved release process must copy its
required records to approved durable release storage before that expiry.
No durable release storage, package publication or deployment is authorized
or configured by this workflow.

## Promotion, rollback and maintenance

Before promoting a candidate, verify its source SHA is the approved protected
main revision, all required jobs and the isolated smoke passed in that run,
checksums match, and the target environment's release/security/migration gates
are met. Promotion needs a separate reviewed release change and credentials;
do not rebuild or replace candidate bytes under the same identity.

There is currently nothing hosted to roll back. If a candidate fails, keep the
previous approved artifact identity and do not promote the failed candidate.
Revert or fix source through a reviewed PR, rerun CI and produce a new
candidate. Future deployments must add rehearsed rollback and data-recovery
procedures before claiming deployment readiness.

Dependabot proposes weekly updates for GitHub Actions and uv, capped at three
open update PRs per ecosystem. Review upstream releases, full action SHAs,
lock changes and security findings; require all CI checks on the proposed
revision. There is no auto-merge. Keep the exact uv version synchronized in
all workflow jobs, documentation and provenance. Keep the locked build backend
aligned with `build-system.requires`.

CODEOWNERS requests review for workflows, dependency manifests/lock, CI scripts,
their tests and this document; it does not independently enforce repository
settings. Review changes to triggers, permissions, dependency bootstrap, gate
membership, candidate scope and archive allowlists as trust-boundary changes.
Resolve security failures with scoped fixes; do not add blanket suppressions
or convert an unavailable advisory service into success.

Useful references: [GitHub required-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
[uv locked environments](https://docs.astral.sh/uv/concepts/projects/sync/),
and [pip-audit](https://github.com/pypa/pip-audit).
