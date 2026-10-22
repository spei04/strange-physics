# Pure native scoring core

This is an additive RA-N01/#106 increment over the delivered candidate producer
and native predictor. It prepares and scores supplied material; it neither reads
a Journal nor publishes a study cell. RA-N01 and RA-02 remain incomplete until the
actual-Journal publisher and the honestly labelled same-prefix classical-fit
diagnostic are delivered. No comparison, inference, calibration or new spending
is performed by these functions.

## Policy and actual inputs

NativeScoringPolicy is the model-independent interpretation of the existing
strange-physics.i1-spring-probes.v1 recipe in scientific_workflow.i1_protocol.
That unchanged recipe specifies all 24 public conditions in mass/case order,
41 times i * .05, integration_dt .01, normalization 1, equal probe averaging and
the existing Decimal reference/failure semantics. The source commit separately
pins that recipe's implementation. The policy contains no model, purchased
prefix, selected coefficient, world identity or evaluator label. Its digest is
the RA-02 scoring_policy artifact; it is not the eventual model-bound protocol
digest.

prepare_native_evaluation consumes NativeEvaluationInput: actual candidate
input, complete production result, expected production-attempt ID, selected
candidate (or explicit absence), policy and actual native prediction config.
It executes the existing actual-input candidate/selection binders. A failed
candidate production or absent selection yields a rejected preparation with no
invented model. Selection remains selected-candidate-only; no MAP proof is
implied.

The complete actual protocol is recomputed with i1_protocol and canonical-hash
compared when retained preparation is supplied. Every purchased record participates
in disjointness, including physical failures. The unchanged condition_keys helper
recognizes exact action and post-impulse equivalence, including absent versus
zero impulse, relative anchor translation and reversed edge orientation.
An overlap returns the first probe/record indices and no protocol. Probes are
never redrawn or chosen using held-out outcomes. Canonical identity preserves
signed zero independently of physical-condition equivalence.

## Scoring and accounting

NativePredictionCollection retains exactly 24 ordered NativeProbeOutcome entries.
Each names the exact probe/request and its distinct expected per-probe attempt.
A present NativePredictionResult is bound against the reconstructed actual
NativePredictionInput (selected model, actual candidate config, exact request
and actual prediction config). Missing and invalid transport outcomes are
explicit; only their derived SCI submissions omit a missing probe. Native
prediction failures retain their original frame diagnostics and become failed
submissions. Foreign/reordered or inconsistently bound material is a preparation
or prediction mismatch before the evaluator runs.

score_native_predictions calls the unchanged evaluate_spring_predictions after
these joins and exact canonical world.space versus purchased space equality.
The supplied private world is actual material for this call, not authenticated
Journal provenance. The existing evaluator alone generates private labels and
metrics. Its full result, ordered diagnostics and measured report hash are
retained; no numerical formula, normalization or threshold is changed.

A valid but inaccurate prediction remains scored. The I1 .001 development
fixture target is not a cell-success or candidate-eligibility gate. Missing,
failed or invalid predictions produce the existing unscorable SCI report with
null primary metrics. Protocol, reference or metric failures keep report=None
and their actual prediction/metric/reference counts. No surviving subset is
averaged, and evaluator failures never relabel valid predictions as failed.

The only NativeWorkFacts extension is unit=work for one scorer invocation:
requested_count=1. A scored or unscorable evaluator outcome completes that unit;
a protocol/evaluator/arithmetic failure fails it; preflight rejection leaves it
unassessed. Detailed probe/frame counts stay in their original results.
Preparation retains unit=preparation. Candidate/frame units are unchanged.
output_sha256 excludes the facts themselves; scoring input/output hashes include
private material and remain evaluator-private.

These are operation-local facts, not CPU/wall/new-byte measurements or ledger
settlements. Each per-probe prediction needs its own reserved and measured
attempt at the later composition boundary, plus a separate scorer attempt.
Twenty-four different input hashes cannot settle one reservation. This collection
does not invent a measured prediction-batch envelope. Missing/invalid entries are
transport assessments, not proof of execution or an authorization to refund work.

## Privacy, bounds and trust

NativeScoringInput, NativeScoreOutcome and NativeScoreResult are private roots,
including their digests, reference labels, detailed metrics and facts. They must
never enter candidate production, likelihood, acquisition, online selection or
tuning. There is no callback, mutable selector state, file/network access or
candidate-switching path in this core. Selection and purchased history must be
frozen before held-out scoring. Even a truth-free SCI report schema is not
permission to feed its metrics back into a live selector.

Only the explicit policy, public material/preparation and protocol projections
are suitable for agent-facing composition. The generated schema includes both
audiences and marks its private roots; publishing the whole schema's closure is
not an audience grant. Existing evaluation binders prove input identity and
shape, not numerical authenticity; the real producer must execute this evaluator
or consume its trusted immutable execution result.

Raw ingress is capped before decoding: 16 MiB inputs, 8 MiB results, depth 32 and
one million JSON nodes; duplicate keys, nonfinite values and invalid UTF-8 reject.
Canonical encoding has the same frozen SCI meaning and separate bounded size.
Existing 12-record/1,025-candidate limits apply, and the prediction collection
requires 24 results with 41 requested frames each. Private world material is
capped at 64 KiB, with at most 32 law parameters and 128-character parameter
names checked before serialization. These pure caps are not scalable storage or
hostile-process isolation claims.

## Required later composition

The RA-02 scored-cell publisher must itself call reconcile_study_journal with
the current ledger, actual Journal path, actual frozen catalog and cell.
A complete cell requires 12 actual reserved rows, no pending rows and no missing
charged intents. It must compare actual raw Journal identity, full canonical
prefix/space/engine/run and all frozen pool/config/policy/model/protocol/result
joins. A caller-supplied ready flag, scalar prefix, or reconciliation snapshot
is not sufficient. Physical failures stay in the full prefix and accounting.

That producer must bind each actual result/facts to its matching measured terminal
ledger attempt, retain the actual report digest including measured evaluator time,
and require later N02/N04 selection evidence instead of treating this selected
candidate receipt as a MAP/selector proof. The final manifest requires the real
later gates; synthetic complete fixtures verify interfaces without fabricating
future study hashes. No pre-freeze cost exemption or budget reset is introduced.

The legacy workflow Journal reader is not a replacement for this reconciliation.
The classical fitter diagnostic must use the actual same prefix and its real
fitter/config, remain labelled diagnostic, and cannot substitute for the primary
native candidate. Neither pending seam is implemented here. The cumulative
36-episode, 432-slot, 8-CPU-hour and 1-GiB comparison limits remain unchanged.

The currently accepted RA-02 comparison preparation operation binds its menu
artifact. These local evaluation-preparation facts truthfully bind scoring_policy;
the later publisher must explicitly reconcile that operation/config mapping or
account for preparation inside a measured enclosing envelope. They must not be
settled against the menu by relabelling a digest. Scoring already maps to the
scoring_policy role. This is a remaining composition obligation, not a ledger
amendment in this increment.

## Reviewed pure-core validation

The reviewed runtime is `da3d529ac462051d80be00762f6dcc8d57c767f2`
(tree `edf035810d9585a89665e74f3e57b66a69219dc7`). Its exact full suite passed
3,801 tests, including 87 scoring tests. The 470 focused native cases also
passed with identical source/test blobs; the final compact schema fixture was
rechecked separately and is included in the full suite. Ruff lint and format
over 160 files, configured strict `mypy src tests examples` over 112 files,
1,487 external schema checks and `bandit -r src scripts -ll` passed.
Lock/dependency consistency and the locked all-groups hashed dependency audit
also passed. No dependency manifest changed.

Quality independently passed 223 contract/scoring cases and 49 parametrized
boundary checks (48 distinct variants), detecting six sensitive guard mutations.
Research passed 470 focused cases plus 129 independent checks, detecting five
sensitive mutations. These checks include all 64 valid/missing/invalid/failed
combinations at three probe positions, coherently rehashed protocol changes,
all-purchase overlap equivalences, hand-computed metrics and failures after
earlier metrics or all 24 metrics had completed. Poor valid predictions remain
scored. Synthetic accounting checks cover each whole-invocation work outcome;
they do not implement measured Journal publication.

Offline wheel and sdist verification matched all 62 allowed package files.
A temporary project-only wheel installation exercised actual candidate selection,
all 24 native predictions, scoring, all-missing unscorable behavior, old-v1
rejection and RA-02 work-facts parsing. Ten installed module files matched source.
The temporary target was removed; existing pinned dependencies were used, so
this is not a clean runtime-only environment claim. CORE/SCI, the old
fitter/predictor/evaluator, workflow and RA-02 source are unchanged. The shared
native WorkFacts/schema amendment is limited to the reviewed `work` unit.

The author's private exact-source evidence index SHA256 is
`2e8d0b659eb0690a395da5a957d288efe3b9a999467b273a3c88731dee0d31c0`.
The actual model-independent scoring policy has canonical SHA256
`e14ffaef239ec38a020f8e0a27712fa27d32c7d36bd638486af7afca780e64ce`.
This policy identity is distinct from each actual model-bound protocol.

These results accept only the pure scoring increment. Hosted PR/main/candidate
verification remains an integration obligation. Actual-Journal composition,
same-prefix classical diagnostics, posterior/MAP evidence, calibration and the
comparison remain pending; no scientific study or budget reset occurred.
