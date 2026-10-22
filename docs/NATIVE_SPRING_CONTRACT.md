# Native spring candidate identity

This partial [RA-N01](https://github.com/spei04/strange-physics/issues/106) implementation defines bounded native candidate identities, actual candidate production, a separate native analytic predictor, local work facts and a selected-candidate receipt. It does not compute a posterior, prove a MAP choice, adapt the private scoring workflow or execute the comparison. RA-N01 remains incomplete; the candidate/prediction increment has passed independent source review and local checks, with hosted integration gates still pending.

The existing CORE/SCI messages, paired-Simpson fitter, analytic predictor v1 and scoring mathematics remain unchanged. A native model uses the existing `LinearSpringModel` envelope with honest `strange-physics.linear-spring.native-candidates.v1` producer provenance and the digest of the actual `NativeCandidateConfig`. It cannot enter the old predictor by pretending to be a paired-Simpson fit. The old predictor must continue to reject this producer. The separate native prediction profile uses the existing pure analytic kernel internally.

## Identity and input boundaries

`NativeSpringPool` contains strictly increasing, finite coefficients in [0, 4], with at most 1,025 nodes. It fixes neither the comparison grid nor a prior, reference measure, cell geometry or posterior policy. RA-N02.a owns those decisions. The pool digest is common across arms. Each actual model instead binds its own entire purchased `ObservationBundle`, including completed physical-failure records, and every completed scientific record index. Identical coefficients do not imply identical model hashes across arms.

Here “completed record” means `ExperimentRecord.status == completed`; a purchased record with `status == failed` remains in the prefix and counts, but is not a fitting selection. Pending, running or abandoned operation reservations are not `ExperimentRecord` values. A future journal adapter must establish the complete committed journal prefix and reject unresolved reservations; it must not silently shorten a journal into an apparently complete prefix. This contract alone cannot authenticate a caller-constructed observation bundle.

The support envelope permits at most 12 committed purchased records and an engine-version identity of at most 128 characters. These are additional native-profile bounds, not changes to CORE. All models select exactly every completed record. An empty prefix or a prefix containing only physical failures returns an explicit `no_completed_records` rejection with no model and no fabricated indices. The outer prefix index is -1 when empty; no invalid SCI model is created.

Physical node ordering rejects duplicate +0/-0 nodes together. A single accepted signed zero is preserved in its exact canonical identity. Exact joins use the frozen Python canonical message hash, not ordinary float/model equality. Pool, prefix, producer configuration, whole input, result payload and selected model identities have distinct roles.

## Complete outcomes and work facts

Candidate production is all-or-failed: success returns every requested model in pool order. A construction failure returns no partial set, but retains the number successfully constructed before the failed index, one failed unit, and the unassessed suffix. Preflight rejection records all candidate work as unassessed. These counts describe candidate units, not experiment slots or measured CPU.

`NativeWorkFacts` carries an opaque, ledger-issued `attempt_id`, operation/producer/config/input/output identities, a declared unit and disjoint requested/completed/failed/not-assessed counts. The output digest covers the payload **excluding facts**, avoiding self-reference. An attempt is a supervised work envelope; internal local calls may share its ID. This module neither creates attempts nor asserts globally unique call IDs.

RA-02 owns study/cell/phase, reservation, CPU/wall/new-byte measurements, retry accounting, reconciliation and aggregate caps. Unknown work must not become zero cost. Accounting begins before cost-bearing reference/calibration work; final manifest freeze continues that ledger rather than resetting its budget. The adapter must join actual local facts to the reserved envelope without double-counting overlapping measurements. Facts are not proof of execution.

`SelectedNativeCandidate` names an actual candidate from a complete, input-bound result. It claims only selection. A later posterior/argmax/tie receipt must refer to this exact candidate; no MAP proof is manufactured here.

## Bounds, parsing and consumers

Use `parse_native_candidate_input` on raw input and `parse_native_candidate_result` on stored result bytes. They enforce 8 MiB input / 4 MiB result byte limits before decode, depth 32, one million lexical nodes, strict UTF-8/JSON, duplicate-key rejection and finite numbers. Typed constructors are for already decoded inputs and cannot establish predecode safety. Raw artifact SHA must be checked on original bytes; parsing and reserialization cannot verify it.

Typed field bounds limit prefix/model counts and unbounded CORE engine-version strings before canonical serialization. Existing finite frame/particle limits bound the remaining graph. Incremental encoding enforces exact canonical byte caps without constructing one full encoded string; Pydantic still constructs the bounded typed graph and JSON-mode projection. These caps are not a memory/RSS or large-study performance proof. Over-limit ingress fails explicitly; a supervising ledger retains its failed attempt without inventing canonical identities for unparsed material.

Consumers must call `validate_native_candidate_result` with the actual input and expected attempt correlation, and `validate_selected_native_candidate` with the actual complete result. Parsing or a coherent set of asserted hashes is insufficient. Schema validation is structural; semantic validators and actual-input binders are also required. None of these checks proves numerical authenticity, posterior quality, observation publisher authenticity or authorization.

The checked-in examples are synthetic contract fixtures. They contain no private world, evaluator labels, journal locator or provider secret. The future private preparation/scorer adapter must consume actual journal and protocol inputs, keep labels/reference mathematics private, distinguish prediction failures from evaluator failures, and preserve disjoint held-out probes. No `SpringFitArtifact` may be forged to reuse a legacy workflow. Study execution and final manifest gates remain separate from this API checkpoint.

## Initial contract checkpoint validation

The initial API checkpoint passes 82 native contract cases (140 with existing fitting/prediction contract tests), all repository Ruff and format checks (144 files), strict `mypy src tests examples` (98 files), and 1,444 external schema fixture/reference checks. The configured Bandit threshold also passes. The examples and tests construct synthetic contract messages; they do not execute a scientific comparison. Full-suite and package evidence will be recorded separately against an immutable source identity.

## Candidate production and native prediction increment

`produce_native_candidates(actual_input, attempt_id=...)` constructs one honest
SCI `LinearSpringModel` per declared pool node, in order. Every model binds the
actual candidate configuration and whole committed observation bundle, including
physical failures; its selected record indices are exactly all completed records.
Empty/all-failed prefixes return `no_completed_records`. The runtime does not
accept a Journal or infer completeness from a shortened prefix. The later
publisher must first check RA-02 reconciliation's pending and missing-intent lists.

The native producer supports one mobile particle, one fixed anchor and their
single edge (either orientation), anchor norm at most 0.5, actual purchased mass
0.5–2, position/velocity norms at most 2 and impulse norm at most 1, with sampling
horizon at most 2. Actual actions in failed records receive the same checks.
The public space may advertise wider limits; these are this producer's support
bounds. CORE-valid sampling grids and declared observation noise are retained
without imposing the paired-Simpson cadence. Enumeration does not infer a
stationary true law, fit quality, likelihood, prior, grid weights or MAP.

Preflight leaves all candidate units unassessed. A construction failure at node
`i` reports `i` completed constructions, one failed candidate and the remaining
suffix unassessed, returning no partial model list. The accepted configuration
still has canonical SHA256
`155d375afb628eb79411c3d331ca0d940e2e7bef41d6c3eab17761352c3bebb1`.
The 1,025-node/12-record caps bound model construction before the final 4 MiB
canonical result check. This is synthetic contract/runtime verification, not a
chosen scientific candidate pool.

`NativePredictionInput` supplies the actual model, actual
`NativeCandidateConfig`, unchanged SCI request and distinct
`NativePredictionConfig`. `predict_native_spring(..., attempt_id=...)` uses the
existing pure oscillator kernel with a separate preflight and result contract.
It does not call the old predictor under fabricated paired-Simpson provenance.
The old predictor/configuration and frozen CORE/SCI messages remain unchanged,
and the old predictor continues to reject native candidates.

This is a local native profile; it does not widen COMP1 hosted runtime admission.
The new profile is
`strange-physics.linear-spring.native-analytic.v1`. It requires the actual native
producer and supported candidate-configuration digest. Counterfactual position
norm is at most 3, separately from purchased norm 2; mass/anchor/velocity/impulse/
coefficient/horizon and output bounds match the accepted analytic kernel's
domain. It evaluates exact requested times, up to 2,001 frames and the existing
20,000 reference-step bound. `integration_dt` is alignment/replay metadata,
not an executed integrator step. Reversed valid edges, exact time zero,
once-applied impulses, signed zero and zero/subnormal stiffness retain their
meaning. No hidden truth, evaluator labels or provider input is accepted.

A prediction result carries actual/requested model identities, request,
candidate/predictor configuration and captured observation hashes, plus the
complete response or an explicit preflight/numerical failure. The first failing
frame terminates propagation: computed prefix count is retained, one frame is
failed, the remainder unassessed, and no partial trajectory is returned.
The payload hash excludes its accompanying work facts. The actual-input binder
also checks response time/particle/model association, preserving signed-zero time identity. These joins are identity
and shape evidence; a model's captured prefix digest alone does not authenticate
candidate production. Use the actual candidate-result/selection binders for
that boundary. No result proves MAP, numerical authenticity or forecast accuracy.

Raw input/result parsers reject bytes over 8 MiB/4 MiB before JSON decoding, then
apply depth 32/node 1,000,000, duplicate-key and finite-number rules. Typed inputs
have bounded model metadata and CORE structures before canonical encoding.
A successful prediction constructs at most 2,001 one-particle frames; finite
binary64 values and bounded metadata keep this well below the final result
ceiling. Invalid raw inputs or unexpected process failures do not fabricate a
successful result or an input identity; the supervising ledger retains the
unresolved measured/reserved cost. Expected construction/arithmetic failures
use safe reason codes, not exception text.

`NativeWorkFacts` stays operation-local. Candidate and frame units retain the
same schema and count partition accepted by RA-02. Internal calls may share a
ledger-issued parent attempt ID; the measured parent envelope is settled once,
against its reserved operation/config/input, without double charging child
calls or assuming unit counts measure CPU/wall/output bytes. This pure runtime
neither reserves nor settles a study attempt. It does not reset cumulative caps.

This increment leaves N01 incomplete. A model-independent scoring policy,
actual policy-to-protocol/scorer adaptation, the RA-02 scored-cell publisher,
posterior/MAP evidence and the scientific comparison remain later units.
The scorer's whole-operation failure representation is not added to these
candidate/frame contracts.

## Candidate/prediction runtime validation

The reviewed implementation is `c3988d9356e47965dea33746c9fac3268099912a`
(tree `e7ffeed92554479c68be6946578ef0ce7e1e9b0b`). Its exact local checks passed
3,714 full tests, 383 focused native cases, Ruff lint/format over 156 files,
configured strict `mypy src tests examples` over 109 files, and 1,473 external
schema checks. The configured `bandit -r src scripts -ll`, locked all-groups
hashed dependency audit, lock check and installed-dependency consistency also
passed. CORE/SCI, the old fitter/predictor/evaluator, RA-02 modules and both
dependency manifests remain byte-identical to the accepted base.

Quality independently passed the 383 focused cases plus 49 provenance, parser
and accounting cases, detecting six sensitive guard mutations. Research passed
the 383 cases plus 100 domain, kernel, oracle and failure cases, detecting six
numerical/domain mutations. The independent Decimal-oracle checks retain the
existing 1e-12 component tolerance. Their measured maximum position/velocity
component discrepancies were approximately 3.22e-15/6.22e-15. These synthetic
conformance checks are not RA-N03 calibration or scientific comparison results.

Offline wheel and sdist archives matched all 60 allowed source files. A temporary
project-only wheel installation exercised actual candidate production, native
prediction, RA-02 facts parsing and old-v1 rejection outside the checkout.
Eight module files were compared with source; the temporary target was removed.
This used existing pinned dependencies and does not claim a clean runtime-only
environment. The author's private exact-source index SHA256 is
`141bc3e2179a92921ed4e556c6f1950fba7d00b44baf01f66b5b78f9e53eb980`.

The actual native prediction configuration has canonical SHA256
`e1807ebdd737715291dd6a9e92e07ed3a4d69291506d0d66513c6b76c64b1530`.
This is distinct from the candidate configuration identity. Final documentation
does not alter tested runtime/schema/test/package bytes. Required hosted
PR/main/candidate verification remains an integration obligation; scoring,
the RA-02 scored-cell publisher and the measured comparison have not run.
