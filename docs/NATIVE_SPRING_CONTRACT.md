# Native spring candidate identity

This is the first contract slice of [RA-N01](https://github.com/spei04/strange-physics/issues/106). It defines bounded native candidate identities, local work facts and a selected-candidate receipt. It does not produce numerical predictions, compute a posterior, prove a MAP choice, adapt the private scoring workflow or execute the comparison. RA-N01 remains incomplete until those later slices are independently reviewed.

The existing CORE/SCI messages, paired-Simpson fitter, analytic predictor v1 and scoring mathematics remain unchanged. A native model uses the existing `LinearSpringModel` envelope with honest `strange-physics.linear-spring.native-candidates.v1` producer provenance and the digest of the actual `NativeCandidateConfig`. It cannot enter the old predictor by pretending to be a paired-Simpson fit. The old predictor must continue to reject this producer. The later separate native prediction profile will use the existing pure analytic kernel internally.

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
