# Comparable same-prefix classical diagnostic

This RA-N01 slice executes the unchanged paired-Simpson fitter, accepted legacy
analytic predictor and independent evaluator on supplied actual material. Its
output is a diagnostic, never a replacement for the primary native candidate,
a posterior/MAP receipt, calibration evidence or permission to run a study.
Both RA-N01 and RA-02 remain partial until the separately reviewed actual-Journal
composition and required source/interface joins are delivered.

## Actual material and fixed comparison

`ClassicalDiagnosticInput` contains the actual `NativeEvaluationInput`, an
explicit `ClassicalDiagnosticConfig` and the private world. The configuration
bundle contains the actual `SpringFitConfig`, `SpringPredictionConfig` and
model-independent `NativeScoringPolicy`; its canonical digest is the diagnostic
operation's configuration identity. The full private input and output digests
are evaluator-only because they bind world/reference material.

`run_classical_diagnostic` first validates the retained native production and,
when present, selected-candidate receipt against the actual pool/configuration
and complete supplied prefix. Invalid provenance rejects before fitting. A
valid native production failure or absent selection still permits the diagnostic.
It then calls the real `fit_spring` with precisely that prefix and actual old
fit configuration. The returned `SpringFitArtifact` is retained; its outer and
inner observation copies are joined canonically, including signed zero. Every
failed purchased record remains part of provenance and domain checking. There
is no different subset, resampling, noise removal, coefficient clipping or
fabricated fitter artifact. The old fitter's unsupported sampling/domain,
insufficient excitation, negative estimate and numerical failure stay explicit.

With a real fitted model, the adapter derives the existing fixed I1 protocol:
24 probes, their unchanged order/conditions, 41 requested times, scale one and
unchanged failure/averaging/reference rules. `classical_condition_sha256`
excludes exactly the top-level model digest, each probe's request digest and
each request's model digest; every other canonical field remains. When a native
selection exists, both actual model-bound protocols must have this same
condition identity. Their complete protocol/model/request hashes remain distinct.

Every purchased action, including physical failures, participates in the
existing exact `condition_keys` disjointness check: absent versus zero impulse,
reversed connection orientation, relative anchor position and post-impulse
velocity equivalences. A collision fails preparation without replacing or
redrawing a probe. The unchanged old predictor executes all 24 requests in order;
its real per-probe result and computed/failed/unassessed frame counts are kept.
A learned coefficient above four remains in the fit artifact and can produce
unsupported-domain predictions and an unscorable evaluation.

The unchanged `evaluate_spring_predictions` receives the actual fitted model,
derived ordered submissions, full fixed protocol and private world. Valid poor
scores remain scored. The I1 fixture target is never an admission/success filter.
Missing later stages remain absent; no survivor mean or invented prediction
failure replaces a fitter, reference, metric or whole-evaluator failure.

## Identity, privacy and accounting

`validate_classical_diagnostic_result` recomputes the actual input/config/prefix
and selected/native identities, exact protocol, ordered prediction/submission
joins and evaluator material binding. It proves canonical identity and shape;
it does not independently rerun numerical work or authenticate a Journal.
Actual trusted execution or retained immutable producer evidence is required
for a later publication. Even a truth-free report schema is not permission to
feed held-out metrics back to a selector, pool, prior, acquisition rule or tuning.
Only the evaluator receives the world. The fitter and predictor receive public
prefix/model/request/configuration arguments, with no callback or selection write.

One ledger-issued outer attempt measures the entire diagnostic. NativeWorkFacts
adds only operation `classical_diagnostic`; the existing `work` unit is used
with requested count one. Output identity excludes the facts themselves.

| Actual outcome | Whole-operation facts | Retained stages |
| --- | --- | --- |
| Preflight or no-completed-prefix rejection | rejected, unassessed 1 | Exact rejection; real empty-prefix fitter artifact when invoked |
| Attempted fit or preparation failure | failed 1 | Real fit diagnostics/model and any overlap indices |
| Evaluator returns scored or unscorable | completed 1 | All 24 prediction outcomes and full evaluator diagnostics/report |
| Evaluator/reference/metric arithmetic failure | failed 1 | Actual completed stages/counts; no invented prediction failures |

Unexpected interruption propagates for the supervisor to preserve an unresolved
attempt and its charges. A real re-execution needs a new admitted attempt; retained
metadata replay does not execute this function. Child fit/probe counts do not
settle additional reservations or infer CPU/wall/output-byte measurements.
A terminal failed/rejected/unscorable diagnostic does not erase a valid native
primary score. Unknown, interrupted, missing or cap-blocked diagnostic work keeps
later complete publication incomplete/cap-limited.

Quality owns the separate optional-compatible study operation/config-role mapping:
old manifests retain their bytes, while a classical attempt or complete publisher
must bind the real frozen `classical_diagnostic_config`. The later private study
adapter must itself call `reconcile_study_journal`, establish 12 reserved rows
with no pending/missing intents, join the complete canonical prefix and same
catalog world, and validate actual measured terminal envelopes. This module has
no study import, Journal reader, readiness flag, child settlement or persistence.
Real final manifests, N02.a argmax/tie evidence, acquisition/selection ordering,
calibration, measurement and durable publication remain later gates; synthetic
fixtures neither supply those facts nor consume a comparison run.

## Resource and transport boundary

Input and result parsers enforce 16 MiB before decode, depth 32 and one million
structural nodes, strict UTF-8 JSON, unique keys and finite numbers. Typed inputs
retain the existing bounded native prefix/pool/configuration contracts and the
64 KiB private-world/free-metadata limit. Canonical hashing is incremental and
rejects over-limit envelopes; over-limit outputs are never truncated. Producers
must preserve unknown attempt/cost evidence if an interruption or envelope limit
prevents a complete return. Bounded models do not prove production memory/RSS,
durable storage, concurrent ledger serialization or hosted isolation.

The new schema exposes the configuration root separately and marks input,
outcome and result roots evaluator-private. It introduces no HTTP route, client
grant, scientific hash dialect or frozen CORE/SCI/legacy runtime amendment.

## Exact source validation — 2026-10-22

Runtime source `0ff9e3b3e161db3e4c1e6a21f0277eb95c2713c9`, tree
`62e20bfcfa5005e49f7bf62ce860037f7c4e2708`, passed 3,874 full tests,
Ruff/format checks over 164 files, configured strict `mypy src tests examples`
over 115 source files, 1,495 external schema checks and configured
`bandit -r src scripts -ll`. Locked offline consistency, installed dependency
consistency and strict hash-pinned all-group dependency audit also passed.

The focused native run passed 543 cases, including 73 new classical cases.
Its production source matches this checkpoint; the final typed free-metadata
bound fixture was subsequently refined and passed separately. The exact full
suite includes that final fixture. Initial test-harness corrections are retained
privately and are not presented as product failures or accepted-source evidence.

Offline wheel/sdist builds passed the exact 64-package-file allowlists.
A temporary project-only wheel installation executed actual scored,
unscorable coefficient-above-four and fitter-failure paths, validated their
results, and matched all 64 package files to source. The temporary installation
was removed. This used the existing pinned dependencies; it is not a separate
clean runtime-only environment or hosted-CI claim. Actual configuration SHA256:
`2a24df7a1f598eecee6dae8aa9919e626025723c4aec66f5fe06bc8e28713873`.

Quality independently accepted 73 authored plus 30 additional checks and four
sensitive guard mutations. Research accepted 73 authored plus 55 independent
behavioral checks and one canonical-prefix guard mutation, covering actual
old-runtime parity, all 24 comparable probes, poor/unscorable results and staged
failures. Both reviews found no remaining blocker in this supplied-material
diagnostic scope. Frozen CORE/SCI, legacy fitter/predictor/evaluator, study source
and dependency pins remain byte-identical to the accepted base.

Owner-readable evidence is stored outside the checkout with review date
2026-11-21. Author index SHA256:
`f753168565a377fe499bb316462b4f3c1f27e7e2c484baeb170b449561e93eae`;
Quality index:
`120586d1b57b219790f887d0f20078468d9703f12acc232852872d424ffc2a6a`;
Research index:
`1a0ce08a843061a50d6862c486565645e6edc9a2b5d9d09d3aa15c3f40917d08`.
Exact integration/hosted gates, the separate actual-Journal composition and
durable measured publication remain required. No study, posterior/MAP inference,
calibration, provider call or new spending occurred; cumulative limits remain
unchanged.
