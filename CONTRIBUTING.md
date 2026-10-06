# Contributing

Read the implementation plan and draft benchmark protocol before changing
experimental behavior. Keep changes scoped and distinguish demos from evidence.

The repository is currently at the design stage. Runtime setup and CI will be
added with the first implementation. The proposed Python checks are Ruff, strict
mypy and pytest. Commit a dependency lockfile when adding dependencies. Add
regression tests for meaningful behavior, especially integration, budgets,
regime changes and data isolation.

Changes to an evaluation protocol must state whether existing results remain
comparable. Do not tune prompts or algorithms on evaluation worlds. Never commit
provider credentials, private transcripts, local environments or bulk run outputs.

Describe the concrete problem, final behavior and validation in pull requests.
Retain required attribution and licenses for any third-party code or assets.
