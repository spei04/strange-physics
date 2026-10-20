# Local scientific workflow: preregistration and contract

SP-04.e / I1 connects the accepted purchased-observation fitter, analytic
predictor and independent development scorer. This document freezes the
workflow policy before end-to-end outcome measurements. It does not activate
the later research amendment, hosted services or a population benchmark.

## Frozen execution sequence

```sh
strange-physics investigate --family spring --particles 1 --budget 4 \
  --stationary --noise 0 --seed 7 --directory RUN
strange-physics fit-spring --observations RUN/observations.json --output RUN/fit
strange-physics prepare-spring-evaluation --journal RUN/session.sqlite \
  --fit RUN/fit --output RUN/evaluation
strange-physics predict-spring --model RUN/fit/model.json \
  --manifest RUN/evaluation/protocol.json --output RUN/predictions
strange-physics score-spring --journal RUN/session.sqlite --fit RUN/fit \
  --evaluation RUN/evaluation --predictions RUN/predictions --output RUN/score
```

The same typed adapters serve SDK callers and these CLI commands. The fitter
receives only the purchased public ObservationBundle and actual SpringFitConfig.
The predictor receives only the actual LinearSpringModel, public frozen
SpringEvaluationProtocol and actual SpringPredictionConfig. Only preparation
and scoring may read the private journal. Scoring calls the independent
evaluate_spring_predictions implementation; no fitting or propagation math is
duplicated. A fitted coefficient is not an accuracy or supported-prediction claim.

## Fixed probe policy

The policy identifier is `strange-physics.i1-spring-probes.v1`. There are exactly
24 probes, in mass-major then condition order, at masses 0.5, 1.0 and 2.0.
Use the public particle/anchor identifiers and original connection orientation.
Set u = 1 / sqrt(2), evaluated as Python `1 / math.sqrt(2)`; it is not replaced
by a numerically different expression. Numeric tuples below are
(anchor position; particle position; initial velocity; impulse):

1. (-0.5,0; 3,0; 2,0; 1,0)
2. (-0.5,0; 3,0; -2,0; -1,0)
3. (0,-0.5; 0,3; 0,2; 0,1)
4. (0,-0.5; 0,3; 0,-2; 0,-1)
5. (-0.5u,-0.5u; 3u,3u; 2u,-2u; u,-u)
6. (0,0; 0,0; 2,0; 1,0)
7. (0,0; 1.5,0.2; 0.3,-0.6; 0.2,0.1)
8. (0,0; 0,0; 0,0; no impulse)

Every request has times `tuple(i * 0.05 for i in range(41))`,
integration_dt 0.01, and the actual model digest. The protocol uses scale 1.0,
the existing ordered per-coordinate/time then per-probe MSE averaging, and the
existing all-failures-unscorable policy. No coefficient or measured outcome
selects, redraws, filters or orders probes.

Preparation rejects the entire protocol if any probe overlaps any purchased
action, including failed records. The physical comparison ignores incidental
IDs, treats reversed connection orientation as equivalent, normalizes absent
and zero impulses, and compares mass, position relative to the anchor, initial
velocity and impulse. A second exact key compares relative position, mass and
post-impulse velocity so equivalent velocity/impulse decompositions also
collide. Pure translations therefore collide. These are exact normalized
numeric comparisons of specified equivalences, not a claim to enumerate all
physical symmetries. A rejection retains the reason and never chooses a
replacement probe.

## Provenance and failure contract

Fit artifacts retain the entire actual public bundle/config and, when
constructible, frozen SpringFitInput and SpringFitResult. Empty or all-failed
bundles produce an explicit adapter input rejection with no fabricated fit
input/model. Other fitter failures retain their real result and cannot advance
preparation. Finite estimates above the calibrated coefficient range are not
clipped or dropped.

Preparation binds the exact full journal prefix (including failed records),
engine fingerprint, configuration and operation/request/record joins to the
fit input. Appended or edited journals fail this check. Its private receipt
binds the actual world digest; this is provenance, not confidentiality.
The protocol is the prediction manifest, so no duplicate request format exists.

Prediction retains every ordered per-probe result and explicit scorer
submission, including unsupported or numerical failures. Scoring revalidates
the actual inputs, exact prefix, prepared protocol and prediction associations.
It retains the full evaluator result privately and exports the unchanged
EvaluationReport only as an explicit public-safe projection. A derived summary
retains every per-probe position MSE/RMSE and the maximum, with unavailable
metrics null. A fully scored scientific miss remains a valid retained result;
it is never relabelled an infrastructure failure or hidden by survivor means.

Each stage records measured monotonic elapsed milliseconds. Actual normalized
message digests and raw file digests are labelled separately. Artifact binders
prove shape/provenance relationships, not numerical authenticity or private
data protection.

## Bounded private file policy

New stage directories are owner-only (0700), files owner-only (0600).
Existing output paths and symlinks are rejected; stages never overwrite.
A completion manifest naming every output file, its raw byte length/hash,
stage identity and input message hashes is written last, after file flush/fsync.
A partial directory has no completion claim and must not be consumed as a
completed stage. Readers validate the manifest and bounded exact filenames.

JSON input files are capped at 64 MiB before reading/parsing; aggregate stage
bytes are bounded. Journal reads are limited to 128 MiB including sidecars,
64 MiB aggregate JSON, 1 MiB per world/record/request and 10,000 experiment rows.
No large allocation or unbounded fetch precedes these limits.

The journal reader is read-only and requires a regular, non-symlink,
owner-private file. It rejects any existing -wal, -shm or -journal sidecar and
WAL-mode header before opening. It uses SQLite URI mode=ro (never immutable=1),
query_only, trusted_schema off, SQLite length/work limits, and one read
transaction. It requires known application/user versions, exactly one run,
contiguous records and no pending reservations, verifies joins and rechecks
quiescence before returning. It never opens Journal/LocalSession for mutation,
resumes a run, checkpoints WAL, changes input permissions or deletes sidecars.
Tests compare input bytes, permissions and sidecar existence before/after
success and failure; access-time changes are outside that claim.

Malformed/provenance/I/O failures use safe bounded codes rather than printing
private Pydantic payloads or SQLite errors. Stage outcomes are retained when
the output directory can be safely created. Exit 0 means a completed scientific
outcome (including a fully scored miss of the development target); exit 1
means a retained scientific stage failure; exit 2 means malformed/provenance
or I/O rejection. Completion means artifact completeness, not scientific success.

## Fixed validation and I1 gate

Before claiming I1, execute the CLI sequence above from a fresh temporary
owner-private directory. Require exactly four purchased records, 24 disjoint
requests, all 24 associated predictions and independent scores. Each probe's
derived position RMSE must be at most 0.001; an aggregate mean alone cannot
pass. Keep all requested counts, failures and per-probe values.

Also exercise an SDK stationary zero-noise one-particle spring with true k=1,
mass=1 and public purchased initial condition. Require the accepted coefficient
criterion (relative error at most 1%, with the existing evaluator-only absolute
floor for zero/near-zero fixtures) and every held-out per-probe RMSE <=0.001.
Truth is used only by this independent acceptance fixture/evaluator, never by
fitting, selection or prediction.

Failure tests cover empty/all-failed fit input, weak excitation, failed prefix
records, unsupported/noisy worlds, above-range estimates, overlap by identity,
translation, zero impulse, reverse edge and equal post-impulse state; tampered
config/model/prefix/protocol/files, appended journal, pending reservation,
malformed SQLite, WAL/hot sidecars, oversized input, unsafe output paths,
partial writes, missing/failed/invalid predictions, and retained scientific
target misses. Existing assertions and frozen SCI bytes remain unchanged.

Passing this gate establishes the bounded local I1 vertical slice. It does not
establish broader scientific generalization, a benchmark study, hosted security
or enterprise production readiness.

## Implemented SDK and artifacts

The shared adapters are `fit_spring`, `prepare_spring_evaluation`,
`predict_spring` and `score_spring` in `strange_physics.scientific_workflow`.
Call `fit_spring(observations, SpringFitConfig())`, retain the returned
`SpringFitArtifact`, and stop if its model is absent. Preparation takes the
private journal path and fit artifact. Only its successful public protocol
and the fitted model go to `predict_spring(model, protocol, SpringPredictionConfig())`.
Pass the journal path, fit, preparation and prediction artifacts to `score_spring`.
The full score is private; `score.result.report` is its explicit public-safe
SCI projection. Inspect all `score.probes` and `score.target_passed`.

| Stage directory | Exact outputs on success |
| --- | --- |
| fit | fit.json, config.json, input.json, model.json, completion.json |
| evaluation | preparation.json, protocol.json, completion.json |
| predictions | predictions.json, config.json, submissions.json, completion.json |
| score | score.json, report.json, completion.json |

Failed fitting omits model.json; no-completed-input rejection also omits input.json.
Rejected preparation omits protocol.json. Every typed prediction failure stays in
predictions.json and submissions.json. Scoring with no SCI report omits report.json.
Malformed/provenance/I/O rejection writes failure.json and completion.json when
a safe new destination is available. Existing or unwritable outputs are preserved;
stderr explicitly records whether the failure artifact could be retained.

fit.json includes the actual public bundle/config/input/result; preparation.json
binds it and the exact private journal bytes. predictions.json includes the actual
model/config/protocol and every ordered outcome. score.json includes private labels
and truth provenance, plus all derived per-probe MSE/RMSE and the worst-probe target.
Matching hashes are neither publication permission nor numerical authenticity.

Completion consumers verify exact filenames, raw bytes, input message joins,
projection equality and retained elapsed time. The manifest is first flushed to
a private pending file, then published by an exclusive link after all payloads
are flushed. Interrupted outputs remain incomplete and cannot be consumed.

The journal must remain quiescent throughout evaluation. The reader compares
the source fingerprint with the current runtime and verifies initial/final
journal bytes. This local consistency check is not a distributed lease or a
sandbox against hostile same-user filesystem races. It never recovers a live run.
An independently supplied malformed/missing predictions stage is an artifact
failure; it never silently removes a requested probe. The lower-level independent
scorer separately supports explicit missing/invalid external submissions.

## Evidence record

Preregistration: `4678c514f3d20a1401f2ff7822e7ff3d16b56ce9`.
Runtime: `0587c333806655732b442beb00461f9f8a1f8541`; extended failure tests and
duration binding: `ed3ce1d09106788501391aca8987fc18862a6ef4`.
The full source check passed 1,609 tests; the subsequent explicit elapsed-time
regression brings focused workflow coverage to 79 passing cases. Ruff and
format checks (94 files), strict mypy (59 files), 586 external schema fixtures
and the configured Bandit medium/high severity gate. Hosted checks remain
an integration requirement. No probe, threshold or normalization changed.

The above-range failure fixture initially attempted an illegal true coefficient
of 5; the simulator correctly rejected it. The corrected fixture explicitly
constructs a synthetic mistaken learned coefficient with consistent provenance
to test all-24 failure accounting. A separate synthetic wrong model tests a
fully scored miss. Neither is claimed as an actual fitter estimate.

Installed-wheel execution evidence and measured per-probe extrema:

Installed-wheel acceptance at source `1bec36474e8896129e26355f2714f468960d59c3`
used Python 3.12.3 and the pinned offline build. Wheel and source archive contents
matched the reviewed package allowlist; the wheel was installed into a temporary
owned directory and imported there under isolated Python, outside the checkout.
Temporary package/install files were removed after the checks.

| Fixed development case | Purchased records | Predicted/scored probes | Estimated k | Worst per-probe position RMSE |
| --- | ---: | ---: | ---: | ---: |
| Preregistered seed-7 CLI sequence | 4 | 24 / 24 | 0.6750572721112501 | 3.154199886178306e-8 |
| SDK true k=1, mass=1 fixture | 1 | 24 / 24 | 0.9999999651839258 | 1.0098004529061669e-7 |

Every probe passed the predeclared 0.001 RMSE bound. Each RMSE is the square
root of the independent scorer's mean squared x/y position error across that
probe's 41 times; the maximum is taken over all 24 probes. It is not the
square root of a pooled mean used to conceal a failing probe. The SDK estimate
also passed the predeclared 1% coefficient criterion.

The installed SDK fixture uses position (1,0.25), velocity (0.25,-0.5), mass 1,
no impulse, a static anchor at the origin and a stationary noiseless linear
spring. The separate automated SDK fixture also covers a purchased impulse
and an interspersed failed record. Neither uses evaluator labels for fitting,
probe selection or prediction.

Full runs, reference labels, all per-probe values, environment/build records
and the exact command results are retained only in an owner-private evidence
directory outside the checkout. Its index identifies source, task owner,
purpose and a 2026-11-19 retention review. No private journal or labels are
committed. The public values above concern synthetic development fixtures only.

Independent review accepted the runtime and documented boundaries. Exact-head
hosted CI and protected-main integration remain required before the project
lead marks the delivery gate complete. These results establish the bounded
local scientific path, not discovery across changing laws or production readiness.
