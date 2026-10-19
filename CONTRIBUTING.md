# Contributing

Read the [roadmap](docs/ROADMAP.md), [execution backlog](docs/EXECUTION_BACKLOG.md) and draft benchmark protocol before changing experimental behavior. Select one approved PR task, verify actual prerequisites, and keep task evidence, roadmap progress and the machine-readable ledger consistent. Keep changes scoped and distinguish demonstrations from evidence.

Use `uv sync --locked` and the Ruff, strict mypy and pytest checks listed in the
README. CI checks Python 3.12 and 3.14 and builds the distribution. Commit the
updated lockfile when adding dependencies. Add
regression tests for meaningful behavior, especially integration, budgets,
regime changes and data isolation.

Local SQLite journals contain private world definitions and must never be
committed or attached to a public PR. Observation exports omit hidden parameters,
but customer-owned observations still require publication authorization. Never
load an uploaded Python plugin into the trusted hosted control plane; current
local plugins are for trusted development only.

Changes to an evaluation protocol must state whether existing results remain
comparable. Do not tune prompts or algorithms on evaluation worlds. Never commit
provider credentials, private transcripts, local environments or bulk run outputs.

Describe the concrete problem, final behavior and validation in pull requests.
Retain required attribution and licenses for any third-party code or assets.
