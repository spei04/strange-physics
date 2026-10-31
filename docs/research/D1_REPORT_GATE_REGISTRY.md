# D1 report gate registry

Original design, 2026-10-30; implementation checked on 2026-10-31. This maps the frozen
[RA-N03-D1 protocol](RA_N03_CALIBRATION_SLICE.md) and
[report design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md) to the existing conditional
producers. The private descriptor implementation below does not amend their
scientific policy, admit a run, complete B1/B2, authenticate evidence, or prove
that the payloads fit the output budget.

The original proposal inspected source `30f3cbeef72554748a7d77699a74c79a25a1ce87`.
Its protocol digest is
`657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
The current [structural envelope](D1_REPORT_CONTRACT.md) must continue to report
qualification and utility as `unavailable`, and material authenticity as
`unchecked`. The proposed names below belong to a later full private report;
this document does not retrofit numerical acceptance into that envelope.

## Registry semantics

A source-owned registry should expand a row's exact kind/key into its required
checks. Persisted data may supply observations and evidence references, never
new gate names, limits, operands or applicability. Missing, extra, duplicated,
reordered or substituted checks are invalid. A predicate has an exact expected
relation; a numerical gate has a fixed Decimal upper ceiling; a diagnostic has
no pass flag or acceptance threshold. These are different record categories.

For a complete, valid upper-bound measurement, `observed_upper <= limit` passes
and `observed_upper > limit` fails that sufficient-certificate gate. Equality
passes. Failure means the declared bound does not meet the ceiling; it need not
prove that the unknown exact error exceeds it. Missing material is unavailable,
never zero. Malformed identities or a demonstrated inconsistency are rejected
with their actual evidence; an exception or missing file alone does not establish
a numerical discrepancy. Bounds, signs and nulls must remain exact in the codec.

Row completion and qualification differ. A row can complete its declared
evaluation with a retained rejected gate. If work stops, preserve all later
unrun rows, actual partial returns and the first fault. No failed node, profile
or world is removed to obtain a successful normalization or average.
A completed evaluation with a rejected required gate stops subsequent batch
work and leaves later rows unrun, preserving the frozen protocol.

Gate evaluation is a pure reconstruction from already retained material. It
must not rerun a predictor, oracle, exp, log, label generator or primitive.
Existing helpers sometimes perform repeated pure validation; those repetitions
remain charged work, not new physical calls or new statistical samples.

## Authorities and producer vocabulary

| Authority | Existing source / relevant fields |
| --- | --- |
| Exact fixtures, public/private separation and supplied inventories | [calibration_fixture_contracts.py](../../src/strange_physics/calibration_fixture_contracts.py): `candidate_material`, `validate_fixture_binding`, `validate_materialized_fixtures`, `check_supplied_inventory`; [d1_fixture_reference.py](../../tests/d1_fixture_reference.py): `FixtureBatch`, `bind_attempt`, `verify_sources`, `verify_rounding`, `candidate_materials`. |
| Actual native/request/reference joins | [d1_prefix_evidence.py](../../tests/d1_prefix_evidence.py): `bind_candidates`, `bind_prefix`, `validate_future`, `recheck_prefix_evidence`, `recheck_constants`, `recheck_normalization`, `require_reference_reserve`; these rebuild fields from retained material but still need authenticated primitive/execution inputs. |
| Whole-prefix and predictive certificates | [d1_bounds.py](../../tests/d1_bounds.py): `D1PrefixPremises`, `D1Certificate`, `certify_d1_prefix`, `certify_d1_prior`, `enclose_predictive`, `enclose_scores`, `pair_scores`, `classify_matched_panel`. Proof: [D1_BOUNDS_PROOF.md](D1_BOUNDS_PROOF.md). |
| Endpoint/arithmetic evidence field meanings | Unchanged [grid_q1_bounds.py](../../tests/grid_q1_bounds.py): `EndpointEvidence`, `ArithmeticEvidence`. Reusing these data types does not transfer Q1's one-record proof to D1. |
| Rows and dependencies | [d1_report_contracts.py](../../tests/d1_report_contracts.py): `ROW_MANIFEST`, `RowState`, `TableRef`, `TableSlot`, `D1ReportStructure`. This validates structure, not the payloads below. |

The proposed shared prefix `bind.*` means exact raw-byte/typed-material joins,
not equality between two caller-supplied digest strings. The future confined
resolver must first verify the actual bytes, codec, record index and source.
Reference centers must join the retained primitive intent/return transcript;
recomputing interval algebra from a fabricated center cannot authenticate it.

## Shared numerical blocks

### Posterior block P: all 40 belief profiles

Each block binds its actual case, grid, scale, prefix, ordered training captures,
future captures, independent references and normalized emitted-vector identity.
There is one training channel per record: one for M/F/W and two for D03.

| Proposed required check | Actual producer / retained field | Fixed relation and authority |
| --- | --- | --- |
| `bind.prefix` | `bind_prefix`, `recheck_prefix_evidence`; `QualifiedPrefixEvidence.bound`, `.nodes`, `.constants`, `.normalization`, `.emitted`, `.probabilities`, `.training`, `.arithmetic` | Reparse full native input/result; match candidate/config/attempt, node-major record order and every result hash. Rebuild all derived arrays and fields, including a coherently changed vector plus replacement certificate. Adapter's existing material recheck is mandatory. |
| `coverage.training` and `coverage.future` | `D1PrefixPremises.training[j]`, `.future`; each `EndpointEvidence.requested/completed/failed` | Exact indices `0..N-1`, in order, with no failed/missing index. Exactly the declared prefix count; D03 retains both equal recorded points and both record contributions. Protocol: Profiles and Per-prefix numerical qualification. |
| `reference.endpoint` | Each retained reference enclosure; `EndpointEvidence.reference_error_upper` | Exactly the fixed `1e-60` allowance, with source/query/domain/primitive proof. A stated allowance by itself is insufficient. |
| `training_endpoint` | Maximum of `training[j].max_abs_error_upper` over all prefix channels | `<= 1e-12`; each field is the outward distance from the captured native endpoint to the independent reference center. Reference uncertainty remains separately bound. |
| `future_endpoint` | `.future.endpoints.max_abs_error_upper` / premise `.future.max_abs_error_upper` | `<= 1e-12`, for every future node. No reuse of a training-time maximum. |
| `reference.constants` | `ReferenceConstants.gaussian`, `.log_prior`, `.pi`, `.log_two_pi_center`, `.log_scale_centers`; `recheck_constants` | Existing dyadic scales/prior inputs, actual retained constants and perturbation algebra agree; every derived Gaussian/prior center-radius check is `<= 1e-48`. Pi's source allowance is `1e-60`. |
| `reference.normalization` | `ReferenceNormalization.joint/emitted/sum_center/log_evidence/centered_log_evidence/normalized_logs/probabilities`; `recheck_normalization`, `require_reference_reserve` | Positive sums/denominators, exact complete coverage and retained exp/log centers reconstruct the same normalization. Every existing `require_reference_reserve` check is `<= 1e-48`: two global log-evidence radii and four per-node joint/log-probability/relative-exp/relative-probability checks. Preserve the complete check vector and its maximum, not an invented substitute norm. |
| `normalizer.complete` | `BoundPrefix.result.normalization`, `BoundPrefix.result.normalizer_input` and raw result; existing adapter assertions | Status normalized, N finite joint and normalized log entries, `exp_evaluations=N`, `log_evaluations=1`, no exp-underflow indices; every actual emitted binary64 exp output is positive and at most one. Exact normalized emitted ratios, not a rounded independently normalized vector, feed later moments/CDFs. |
| `whole_prefix_node_error` | `D1Certificate.reserve_components[0]` | `A <= 1e-9`, as defined below; this is the certificate's existing reason name. |
| `centered_normalizer_error` | `.reserve_components[1]` | `B <= 1e-9`. Keep native shift and log-scaled-sum separately; this compares native `log_scaled_sum` to the independent centered log evidence. |
| `normalized_probability_error` | `.reserve_components[2]` | `C <= 1e-9`. The inclusive emitted-ratio bound is required; normalized logs alone are insufficient. |
| `overlapping_reserve` | `.reserve_upper`, `.fixed_reserve` | Actual outward `A+B+C <= 3e-9`, and `.fixed_reserve` is exactly `3e-9`. The variation calculation uses the fixed reserve, not a smaller outcome-selected sum. |
| `certificate.rebuilt` | Exact output of `certify_d1_prefix(actual_premises)` | All certificate fields, identity, reasons and pass value agree with the material-derived premises. A hash-shaped identity is not proof of this relation. |

Here `epsilon=1e-12+1e-60`, `q=1/8` for W03 and `q=1` otherwise,
`R=q/2+epsilon`, and `D=q/8`. For the actual one/two-record prefix:

    endpoint = sum_j[R*epsilon/sigma² + epsilon²/(2*sigma²)]
    A = max(node_observed_error_upper, endpoint + node_other_arithmetic_upper)
    B = shifted_log_evidence_error_upper
    C = normalized_log_error_upper + probability_representation_log_error_upper
    variation = (2/N) * sum_j[D*R/sigma²]
    delta = variation + 3e-9

All arithmetic is outward. `node_other_arithmetic_upper` is rebuilt with each
captured binary64 endpoint held fixed, including the complete native record
summation and reference-constant uncertainty. It cannot be replaced by `1e-48`
or by an individual-record error. Preserve `node_observed_error_upper` and the
conditioned-native bound separately. The three reserve components overlap;
they are not independent uncertainty sources or three scientific noise terms.

The reference finite domain already requires joint enclosures in `[-32,4]`,
perturbation radius below one, and positive exp/sum arguments. These are proof
premises, not new scientific thresholds. A failed premise cannot silently
increase the reference radius, change an oracle guard, or trigger refinement.

### Finest-grid block F: conditional on N=1024 only

| Existing gate name | `D1Certificate` field | Inclusive upper ceiling |
| --- | --- | --- |
| `finest_cell_mass` | `delta_upper` | `0.0081` |
| `finest_mean` | `mean_error` | `0.018` |
| `finest_second` | `second_error` | `0.019` |
| `finest_variance` | `variance_error` | `0.056` |

Authority: protocol Per-prefix numerical qualification and the accepted unit2
`_finest_reasons` implementation. The t=3/4 formulas are
`2*delta+9/(16N)+epsilon`, `2*delta+9/(8N)+3*epsilon`, then
`second_error+2*mean_error+mean_error²`. D03 uses its own full two-record delta.
At N=256 these four fields are required diagnostics, with no finest-grid gate
or manufactured pass. They are not errors against truth or utility thresholds.

### Future forecast and score block S: 56 distinct contexts

There are 40 posterior and 16 no-learning prior contexts. Forty explicit prior
pairing views are aliases to those 16 originals, not 40 new forecasts.

| Proposed required check | Existing producer / fields | Exact requirement |
| --- | --- | --- |
| `bind.forecast` | `enclose_predictive`; `PredictiveEnclosure.certificate`, actual endpoint/mass arrays | Rebuilt passing certificate, exact source/query/vector identities and full ordered arrays. Positive finite D1 masses; prior masses exactly `1/N`. Enforce exact mass feasibility before support-endpoint CDF rules. |
| `forecast.moments` | `.finite_mean/.finite_second/.finite_variance` and `.mean/.second/.variance` | Reconstruct finite moments from the same emitted ratios and captured endpoints; outward expansion/clipping uses that certificate's t=3/4 bounds. Preserve finite and continuous-dk fields separately. |
| `forecast.cdf` | `.finite_cdf`, `.cdf`, retained cells and actual masses | Rebuild both sweeps from those arrays; knot shape/monotonicity alone is insufficient. Continuous support `[-1,1]`, finite support the actual endpoint extrema; zero below support and one at/above its upper endpoint. Complete exact-tie groups precede crossings. Same-vector TV bound, exact feasible mass totals and correct update census are required. |
| `forecast.quantiles` | `.finite_quantiles`, `.quantiles`; `generalized_quantile` | Exact Decimal tails `0.05/0.95`, generalized inverse with `>=`, no interpolation. Retain `crossing_ambiguous` and the complete interval; ambiguity is not a numerical failure by itself. |
| `bind.truth` | `ScoreEnclosure.truth`, `.truth_evidence_sha256`; fixture reference, not its rounded public label | Same independent unrounded future enclosure, actual source/query/proof and forecast-before-release record. Missing chronology/authentication is unavailable; generating private truth earlier is not itself learner exposure. |
| `score.rebuilt` | `enclose_scores`, `.squared_loss`, `.interval_score` | Outward `(mean-y)²` and `(u-l)+20*max(l-y,0)+20*max(y-u,0)` with ordered feasible tails. Multiplier20 is fixed by alpha0.1, not a selected penalty. Recompute the mean expansion, CDF/quantile/score joins from actual material. |

Widths, signed residuals, absolute/squared errors and inclusion are required
diagnostics, with no absolute adequacy tolerance. Inclusion uses the closed
interval: definite inside requires the truth enclosure entirely between the
inner guaranteed tail endpoints; definite outside requires it wholly below the
lower tail enclosure or above the upper tail enclosure. Otherwise retain
indeterminate. No zero-filled missing scores or nominal-coverage pass exists.
CDF/quantile ambiguity can still produce a decisive score enclosure; it must
not automatically be converted either to a pass or to an inconclusive panel.

## Required expansion by top-level row

The fixed manifest remains 8/40/16/18/20/12/16/4/1 = 135 rows. The dependency
lists in `ROW_MANIFEST` stay unchanged; source chronology is an additional
material obligation, not an inference from report row order.

| Row family | Required check expansion and existing inputs | Status of implementation |
| --- | --- | --- |
| `fixture/{case}` (8) | `bind.fixture`, `fixture.reference`, `fixture.rounding`, `fixture.public_projection`, `fixture.exposure`. Bind `FixtureBatch` source/plan/query/trace to actual `Attempt.public/audit/findings`; all four coefficient proofs and the case's training/future proofs use the recorded binary64 coefficient. Strict rounding enclosure interior: `lower_midpoint < lower <= upper < upper_midpoint`; touching/straddling fails closed, with no rerun. F's private equilibrium1/8 and public anchor0 remain distinct. D03 and M03/W03 shared material/reuse must join all available cases; source/IDs/projections remain distinct. | Unit1/3 implement structural/material checks and retain partial outcomes. Actual independent execution/proof, full exposure inventory and chronology evidence remain required. `candidate_materials` is an all-success batch boundary, not a per-row classifier; do not call it on a partial batch and reinterpret all rows as failed. |
| `belief/{case}/{N}/{scale}` (40) | Shared P, applicable F, S for posterior, `bind.prior_alias` for its corresponding no-learning pair. Exact fixture/prior/record0 dependencies; D03 also depends on its record1 witness. The independent reference binds the entire prefix, not only its last record. | Conditional adapter/certificate algorithms exist. Full payload, primitive execution binding, alias adapter and persisted checks are pending. |
| `prior/{case}/{N}` (16) | `bind.prior_freeze`, `coverage.future`, `reference.endpoint`, `future_endpoint`, `prior.uniform`, `certificate.rebuilt`, applicable F, and S for prior. `certify_d1_prior` has exact zero delta and zero likelihood/reserve fields, with uniform physical-dk cells. It has no posterior training/log-normalization gates. | Prior certificate and forecast algebra exist. Actual pre-label pool/forecast freeze evidence and original-identity alias binding remain pending. Scale metadata cannot select a different prior. |
| `prequential/{case}/{N}/record0` (16) | `bind.prequential_freeze`, `coverage.training`, `reference.endpoint`, `training_endpoint`, `prequential.mean`, `prequential.innovation`. `FirstRecordCache.seal_prior` and `TrainingForecast` bind the label-independent pool, physical training query, endpoints, uniform masses and zero delta. `innovation` subtracts its continuous mean from the actual recorded binary64 training point only after forecast retention. | Conditional cache/forecast exists; durable ordering and pure reconstruction from retained full requests/results remain binder duties. No future-score/CDF gate is invented for this mean-only forecast. |
| `prequential/D03/{N}/record1` (2) | Same training mean/innovation checks, plus `bind.duplicate_forecast`. `duplicate_forecast` rechecks the actual M03/base one-record material and certificate, then compares exact pool/cells/config/physical action/first observation/private reference and rounding evidence. Use `DuplicateForecast.forecast` with the original qualified M03 masses/delta. Retain distinct runs/operations/models and both source identities. | The material equivalence helper exists. Durable release ordering and persisted witness codec remain pending. This is not the repeated-loss check on the later two-record D03 posterior. |
| `refinement/{case}/{scale}/256-to-1024` (20) | `bind.refinement`, `refinement.cell_tv`, `refinement.mean`, `refinement.variance`. Exact ordered coarse/fine same-case/same-scale operands, matching truth/query/prefix physics; group four consecutive fine cell masses per coarse cell. Outward finite TV `sum(abs(p_coarse - grouped_p_fine))/2 <= 0.001`, absolute finite mean difference `<=0.0005`, absolute finite variance difference `<=0.001`. | Fixed thresholds are protocol policy. Pure comparison producer/payload/validator is not implemented in unit2/4. Use finite emitted ratios/moments, not continuous-error certificates or a survivor subset. |
| `scale/{case}/1024/{adjacent pair}` (12) | `bind.scale` and `contrast.rebuilt`: exact M01–04/F02/F04, finest grid, half-to-base or base-to-double operands. Retain outward diagnostic differences and both qualified forecasts/scores. | Operand/count policy fixed; codec/pure contrast implementation pending. No magnitude threshold, preferred direction or winning-scale gate is authorized. |
| `stress/D03:M03/{N}/0.25` (2) | `bind.stress`, `duplicate.loss_identity`, and rebuilt diagnostic residual/width/score/mass contrasts. Required exact repeated first record, same physical grid/prior/base loss, and the record1 equivalence witness. | The two-record identity policy is fixed; the reviewed [reuse proposal](D1_REPORT_REUSE_PROOF.md) supplies a sufficient conditional comparison. Full actual-material binding remains pending. Narrower duplicate uncertainty by itself is an interpretation diagnostic, not a numerical defect. |
| `stress/F02:M02` and `stress/F04:M04` (12) | `bind.stress`, `contrast.rebuilt`: exact named pair/grid/scale, matched public candidate conditions, private omitted-force construction and each world's own held-out truth. Retain signed training/future residuals and width/score/inclusion contrasts. | Diagnostic policy fixed. No equality-of-truth join across F/M and no threshold that would require the misspecified model to be accurate. Definite bias/miss is retained finite-panel inadequacy evidence. |
| `stress/W03:M03/{N}/0.25` (2) | `bind.stress`, `contrast.rebuilt`: shared coefficient/future world/query/truth, distinct fixed training excitation and prefixes. Retain diagnostic effects; no threshold on width or improvement. | Pure contrast implementation/payload pending. Sharing future truth does not make the two training experiments identical. |
| `primary/{M01..M04}/1024/0.25` (4) | `bind.primary`, `bind.prior_alias`, `paired_scores.rebuilt`, `primary.diagnostics_complete`. Use `PairedScores.point_difference/interval_difference` from exact continuous-dk posterior-minus-prior `ScoreEnclosure`s. Keep each world's residual, width/inclusion, squared/absolute error, literal finite scores and continuous enclosures. | Pairing algebra exists; actual-byte aliases and diagnostic codec remain pending. No requirement for each individual world to improve is added. |
| `aggregate/matched/base/continuous-dk` (1) | `bind.complete_panel`, `aggregate.rebuilt`, `qualification.complete`, `execution.complete`, then the co-primary decision below. All other134 rows remain required dependencies; the averaging unit is only the four ordered M worlds at finest/base. Retain maximum per-world absolute-error enclosure. | `classify_matched_panel` provides conditional four-world arithmetic. Whole-report qualification/closure and exact missing-state mapping are future binder work. |

The training-mean radius for the 18 prequential rows is the existing
`2*q*delta + q/(4*N) + endpoint_error` in `training_forecast`, with `q=1/8`
only for W03. First-record priors have delta0; the second D03 forecast uses the
qualified M03 one-record delta. Its endpoint error is bounded by the fixed
`1e-12+1e-60`. Do not substitute the future t=3/4 moment formula or invent a
prequential utility cutoff. A shared future, primitive proof or prior may be
referenced repeatedly; physical calls and reference rechecks are distinct counts.

## Whole-report qualifications and decision

Before any scientific utility classification, the full binder must establish:

- exact135 rows, all nine denominators and all required gate expansions;
  complete node/record/primitive and result identities, no survivors or aliases
  replacing planned outputs;
- actual independently reviewed exposure inventories under the accepted policy,
  pinned source/runtime/authority, pre-label pool/forecast freezes and one-way
  evaluator release; a typed no-overlap finding only covers its supplied inventory;
- exact fixed native/reference/callback/reuse census and failure-preserving
  primitive transcript; `D1Reference.require_complete` covers its own37120
  logical requests/3840 position calls/40 normalizations, not every other activity;
  unit3's separate13 position calls and repeated pure validations are not erased;
- retained bounded payloads, actual files/copies, complete first/supplemental
  failures, process/control closure and applicable resource authority. Structural
  descriptor totals alone establish neither durable evidence nor physical fit.

These are run prerequisites/qualification joins, not extra scalar scientific
gates or a new cost allowance. Their exact codecs and complete counters remain
implementation work. The numerical reference gate never refunds earlier failed
attempts or resolves historical unknown charges.

Maintain three separate axes from the report design:

| Axis | Required derivation |
| --- | --- |
| `execution` | Complete only after every planned row's evaluation and actual operational/retention closure complete; otherwise incomplete. Transport/receipt failure is not a numerical failure. |
| `qualification` | Preserve any demonstrated contract/reference/numerical rejection, even if later closure fails. Qualified requires all required verified gates. Missing required proof is unavailable; no stored certificate flag overrides missing raw evidence. |
| `utility` | Available only when execution is complete and all required qualification/identity/completion checks pass. Missing any primary row produces null aggregate differences, not a survivor average. |

For the two outward equal-weight four-M-world differences: both upper endpoints
strictly below0 means `local-screen-passed`; either lower endpoint nonnegative
means `screen-not-met`, including an exact tie; otherwise `inconclusive`.
There is no averaging or tradeoff between the point and interval metrics.
`classify_matched_panel` has no `attempted` state: the future report adapter must
keep that row state visible and return unavailable utility, not relabel an
unfinished operation completed to call the helper.

This is neither calibrated coverage, absolute product adequacy, MAP evaluation,
selector superiority, unseen-law validation nor the full RA-N03 fixture freeze.
Stress/scale/grid rows never increase the four-world primary denominator.

## Open implementation and policy boundaries

1. **Repeated-loss design is resolved; full binding remains pending.** The
   reviewed [reuse proof](D1_REPORT_REUSE_PROOF.md#1-a-sufficient-d03-repeated-loss-comparison)
   derives gamma=4*c_M+c_D and a sufficient outward ratio comparison from the
   existing inclusive error allowances, with no new exp/log calls or tolerance.
   Its conditional kernel cannot authenticate input arrays or approve a report.
   B2 must reconstruct actual material, join both identical D03 loss terms to M03,
   and retain all required profile gates before using the witness. Overlap without
   containment remains unavailable; coherent vector/certificate substitution must
   fail against actual producer material.
2. **Prior alias interface is proposed; implementation remains pending.** The
   reviewed [prior-view design](D1_REPORT_REUSE_PROOF.md#2-forty-views-of-sixteen-original-prior-forecasts)
   gives40 explicit paired views of the16 original prior contexts, keeping both
   complete identities and introducing no new forecast/CDF calls. Existing
   `pair_scores` identity checks remain unchanged. Full actual-byte reconstruction,
   the narrow view adapter and its independent pass census are still required;
   the proposal changes no scientific baseline, threshold or denominator.
3. **Operational authenticity is external to conditional algebra.** Source/
   primitive/exposure/chronology evidence producers and the confined resolver
   are still required. The policy is already explicit; making up a boolean
   `verified` field does not implement it. The current structural schema must
   keep its unavailable/unchecked literals until a separate full binder exists.
4. **Diagnostic payload shape needs a finite implementation choice.** Signed
   residuals, widths, inclusion, scores and declared paired effects are mandatory;
   the exact codec and which already-retained finite fields are also serialized
   must be frozen within the existing byte/call census. This cannot introduce a
   diagnostic pass threshold, omit required fields, or add forward work.
5. **Absolute usefulness and general calibration are not settled policy.** No
   absolute error/width cutoff, nominal-coverage rate or population decision is
   available. Keep these claims out of the registry. The relative co-primary
   screen is already fixed and needs no new threshold selection.

## Small implementation/test split

The implemented B1 descriptor slice provides the pure row-key-to-required-check mapping,
fixed operand/threshold descriptors and synthetic positive/negative examples.
It retains structural-only scope until the full payload/binder is ready.
Tests alter gate names/limits/applicability/operands and exercise coarse
versus finest rows and prior versus posterior blocks; reject missing fields,
zero-filled unavailable evidence and coherent digest/certificate substitution.

B2 then supplies pure material reconstruction adapters, prior aliases, refinement
and stress comparisons, and whole-report classification. Tests need fixed
rational/synthetic arrays, exact ceiling equalities, violated ceilings, quantile
ties/ambiguous crossings, strict zero-score ties, mixed source/truth operands,
incomplete denominators and a later transport failure after a retained rejection.
The repeated-loss test must include an altered two-record vector with all claimed
digests updated, not only a stale-hash mutation. No actual D1 truth or predictor/
reference calls are needed for this engineering qualification.

Codec losslessness, worst-shape byte fit, schema/runtime parity, callback
installation/restoration and complete work/retention counts remain separate
reviewable obligations. The original mapping was prepared by source inspection;
the implementation validation below is subsequent synthetic engineering evidence.


## Source-owned descriptor implementation checkpoint

[tests/d1_required_checks.py](../../tests/d1_required_checks.py) implements this
registry as private frozen `Operand`, `RequiredCheck` and `ExpectedRow` dataclasses.
`expected_checks(row_key)` accepts only an exact key from the unchanged
`ROW_MANIFEST`; `expected_registry()` expands all 135 rows. There is no user-selected
list of thresholds, optional gate configuration, observed value, gate pass flag
or scientific evaluator. The separate structural report remains unavailable/
unchecked for qualification, utility and authenticity.

Every operand carries its exact source row key and fixed field vocabulary.
Posterior/prior pairing uses the original same-case/grid prior row; held-out truth
binds that case's fixture row; D03 record 1 names the M03/base one-record posterior;
refinement and contrasts retain ordered coarse/fine, adjacent-scale or exact
stress-pair identities. Fields describe the named existing producer or a still-
pending B2 semantic input. They are not an executable JSONPath language and do
not create the unfinished payload codec or resolver. Producer labels beginning
`B2.` and named chronology/authentication binders explicitly denote unfinished
implementations. No predictor, reference, CDF, score or certificate is called.

`validate_expected_row` validates raw dataclass field types before comparing the
complete descriptor to its source-owned expansion, including Decimal limit
representation. `validate_registry` additionally requires all 135 original rows
in their exact order. Boolean ordinals/limits cannot exploit numeric equality.
Missing, additional, duplicated, reordered or coherently substituted checks,
relations, operands, producer names, applicability or constants are rejected.
Accepting these descriptors proves only that their policy labels match this
source; it does not validate any report material or enforce runtime stopping.

Numerical upper gates keep the existing inclusive relations. Reference constant/
normalization descriptors require a complete rebuild and every original radius
check at 1e-48, rather than only a convenient supplied maximum. Exact 1e-60 endpoint
allowance and fixed 3e-9 reserve remain separate required constants. At N=256 the
four finest fields are diagnostics with no limit or pass flag; N=1024 retains the
four inclusive ceilings. Prior rows omit posterior training, likelihood and log
normalization gates. The 18 prequential rows use t=.5 mean/innovation semantics,
with delta 0 only for record 0; record 1 preserves the matched posterior delta.

The concrete names `forecast.diagnostics`, `contrast.diagnostics` and
`aggregate.diagnostics` label already-required retained information, not extra
scientific acceptance gates. `utility.co_primary` describes the existing aggregate
sign rule: both upper bounds strictly negative pass the local screen, either
lower bound nonnegative (including an exact tie) does not meet it, otherwise
inconclusive. It adds no individual-world superiority gate or metric tradeoff.
The fixed descriptor property `on_required_rejection` states that subsequent
batch work stops while retaining the fault and later unrun rows; a future binder/
runner must actually enforce that policy. Missing proof is never zero-filled.

The expansion has source-derived 1,648 descriptors: 8 × 5 fixture, 40 × 26 posterior,
16 × 17 prior, 18 × 6 prequential, 20 × 4 refinement, 12 × 3 scale, 2 × 4 duplicate stress,
14 × 3 force/weak stress, 4 × 4 primary and 6 aggregate. These are metadata rows, not
new physical calls, samples or budget grants. Construction/reconstruction and
validation passes remain counted as pure engineering work in subsequent integration.
No serialized descriptor/table byte fit or timing claim follows from this count.

At source a7f3abb, the 18 test functions passed all 48 synthetic cases and 144
ordered setup/call/teardown phases. Formatting, linting and full configured typing
across 211 files passed. The tests exercise completeness and substitution, original
dependency order, coarse/finest and prior/posterior distinctions, duplicate-prefix
coverage, prequential reuse, finite refinement operands, diagnostic-only contrasts,
exact co-primary ties and strict raw booleans/Decimal limits. Real scientific
producers and certificate/score evaluators are poisoned.

An earlier check stopped at typing with 15 errors before any test bodies ran.
The narrow repair separates boolean and row-key variable names and uses explicitly
typed construction for the same negative cases; no policy or assertion changed.
Fresh preparation and final checks used the same cumulative engineering account.
Independent review verified the immutable source, all 48 identities, unchanged
environment and closure of all 23 children across four attempts. Earlier failures
remain recorded. JSON Schema generation/parity remains pending.
Full material authentication, payload/codec/schema parity, prior aliases,
actual repeated-loss joins, work/byte accounting and numerical admission remain
separate obligations.
