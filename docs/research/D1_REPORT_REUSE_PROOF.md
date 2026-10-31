# D1 repeated-loss witness and prior-pair views

Mathematical and interface proposal, 2026-10-30, against source
`06ef7a97f3decb6925f6500e99b232f4c723630d`. This resolves two implementation
proposals in the [gate registry](D1_REPORT_GATE_REGISTRY.md), subject to independent
review. The [frozen protocol](RA_N03_CALIBRATION_SLICE.md), its tolerances and
135-row denominator remain unchanged. The source-stage conditional kernel below
implements only the arithmetic comparison. No full binder, numerical qualification,
fixture generation or run admission is supplied by this document.

## 1. A sufficient D03 repeated-loss comparison

This check concerns the **finite midpoint distributions** for M03 and D03 at the
same N in {256,1024} and base sigma1/4. It is separate from the continuous-dk
forecast certificate and from `duplicate_forecast`, which supplies the earlier
D03 record1 prequential forecast. There are exactly two repeated-loss witnesses,
one within each existing D03:M03 stress row, not two additional rows.

### Required actual material

Before either witness, B2 reconstructs the two complete
`QualifiedPrefixEvidence` objects using `recheck_prefix_evidence`, the actual raw
native inputs/results/captures, retained reference primitive returns and their
source/execution bindings. Both existing posterior certificates and all required
reference/reserve gates must pass. The later resolver must read actual pinned
bytes; matching supplied digest strings or a caller's `validated=True` is not
sufficient. No new physical or transcendental call is permitted.

In addition to each profile's own validation, require:

- M03 has exactly one recorded experiment and D03 exactly two; both D03 physical
  experiments and recorded values equal M03's first record. Keep their actual
  distinct run/operation/model IDs and result hashes. Numerical equivalence
  does not authorize replacing provenance.
- Same uniform physical-dk support, ordered cells, representatives, masses
  `pi_i=1/N`, source/protocol, prediction configuration, physical training query
  and base loss. Both D03 loss terms use that same recorded binary64 value.
- The per-node independent physical reference input and returned value used for
  M03 is the identical retained input/value for each D03 term. The actual selected
  Gaussian and log-prior constants agree. This is a same-physical-key join,
  independent of different display/run/model IDs; no fresh reference is called.
- Retain all actual native per-record predictions and whole-prefix log weights.
  They need not be assumed bit-identical across separately executed requests:
  their existing endpoint/whole-prefix arithmetic certificates bound their
  differences. No duplicate term or candidate may be dropped.
- The M03 and D03 emitted arrays are the exact positive finite binary64 outputs
  from their recorded exp-conversion calls. Their normalized ratios and
  independent reference probabilities are reconstructed, not trusted aliases.
  Full normalized logs, centered evidence and native arithmetic remain available.

A missing join is unavailable; an established substitution or contradicted join
is a rejected contract/material check. Actual primitive/source authentication
remains a necessary external premise, not a property of interval algebra.

### Exact ideal identity

Write the ideal one-record joint log weight as

    J_M,i = log(pi_i) + ell_i,
    ell_i = gaussian_constant - (recorded_y - f_i)^2 / (2*sigma^2).

The repeated physical observation gives, exactly,

    J_D,i = log(pi_i) + 2*ell_i = 2*J_M,i - log(pi_i).

Thus for their normalized exact independent finite distributions P and Q,

    Q_i = T(P)_i,
    T(p)_i = (p_i^2 / pi_i) / sum_j(p_j^2 / pi_j).

The same prior appears once, not twice. The identities above are algebra on the
joined complete inputs and the fixed loss definition, not a numerical test that
two independently widened intervals happen to overlap. They hold for the shared
recorded binary64 label; the unknown generating coefficient or future truth does
not enter this check.

### Use the existing inclusive probability-error bounds

Let q and r be the exact normalized ratios of the actual M03 and D03 emitted
binary64 vectors. The accepted adapter's `probability_ratio_bound` supplies

    c_M = M.arithmetic.probability_representation_log_error_upper,
    c_D = D.arithmetic.probability_representation_log_error_upper.

These scalars must be the exact **reconstructed** maxima for their retained
arrays/reference enclosures. For each node the adapter first bounds
`rho=max|actual/reference-1|<1`, then uses `rho/(1-rho)` to bound the absolute log
ratio. Consequently, conditional on its actual reference proof,

    |log(q_i/P_i)| <= c_M,     |log(r_i/Q_i)| <= c_D.

Do not use only the normalized-log error, replace either value by a chosen
constant, or enlarge it to the allowed ceiling. The existing certificate checks
already constrain the inclusive normalized-probability component to1e-9; those
checks remain prerequisites, not replaced by this witness.

Put `q_i=P_i*exp(e_i)`, where `|e_i|<=c_M`. Squaring gives positive factors in
`[exp(-2c_M),exp(2c_M)]`. Their positive weighted sum has the same bounds, so
normalization contributes at most another2c_M in log distance:

    |log(T(q)_i/Q_i)| <= 4*c_M,
    |log(r_i/T(q)_i)| <= gamma = 4*c_M + c_D.

This positive-sum argument is essential; a loose absolute reciprocal bound is
not a substitute. The errors may overlap or be correlated; the triangle bound
does not assume statistical independence. Compute gamma outward and require `0<=gamma<1`. The already
qualified c_M/c_D make this a very small quantity, but do not replace the actual
derived value with5e-9 or any other constant. No exp/log evaluation is needed:

    exp(-gamma) >= 1-gamma,
    exp(gamma) <= 1/(1-gamma),
    therefore r_i/T(q)_i belongs to A=[1-gamma, 1/(1-gamma)].

Both endpoints of A are rounded outward. This is a sufficient acceptance
enclosure derived from existing allowances, not a new scientific tolerance.

### Construct and compare the retained vectors

For actual M03 emitted binary64 values E_i, `q_i=E_i/sum(E)`. In D1's exactly
uniform prior the common factors cancel:

    T(q)_i = E_i^2 / sum_j(E_j^2).

Require uniform pi before using that simplification; reject another prior
instead of silently generalizing the diagnostic. Using the existing directed
interval primitives, construct `s_i=square(point(E_i))`, `S=total(s)`,
`t_i=divide(s_i,S)`, then `R_i=divide(r_interval_i,t_i)`. All endpoints/denominators
must be finite, ordered and strictly positive. These enclose the exact desired
ratios without another exp conversion or finite-log normalizer invocation.

Freeze the following sufficient decision for this proposed implementation:

| Material result | Witness disposition |
| --- | --- |
| All prerequisite joins/gates verified and every R_i is contained in A, including equal endpoints | Certified repeated-loss consistency at the derived allowances. |
| A verified R_i is disjoint from A | Rejected consistency check: the actual retained material contradicts the joined ideal relation and existing error bounds. Preserve its node and all component evidence. |
| No disjoint interval, but at least one R_i overlaps A without containment | Unavailable/nonclosing sufficient proof. Overlap alone is not a pass; do not refine, rerun or enlarge gamma. |
| Required material/closure/authentication missing | Unavailable. No manufactured numerical discrepancy or zero error. |

If a profile's pre-existing gate is rejected, retain that earlier rejection;
do not run this comparison with loosened allowances to rehabilitate it. A
required rejected or unavailable witness stops subsequent batch work under the
frozen fail-stop policy, retaining the evaluation and all later unrun rows.
These outcomes concern numerical/material consistency, not whether duplicate
noiseless data is scientifically independent. Its narrower beliefs or changed
scores remain separate diagnostics even when this witness is certified.

The proposed witness record needs the two exact profile/material identities,
shared-input join evidence, original c_M/c_D fields, derived gamma/A, S,
coefficient-ordered t_i/R_i, complete coverage and first failing or unresolved
node(s). It must retain original inputs, not only a maximum or pass boolean.
The binder recomputes the witness from those actual inputs with the same fixed
recipe. Any persisted `gamma`, transformed vector or disposition is a claim to
check, not an authority.

### Additional work to count

For one witness with N nodes, after the already-required full material binding:

- N interval `square` calls, N additions in `total`, N transformed-weight
  `divide` calls and N ratio `divide` calls: **4N interval primitive calls**;
- one multiply, one add, one subtract and one divide for outward gamma/A:
  **4 additional interval primitive calls**;
- N exact binary64-to-point conversions, complete input/identity checks, at most
  4N containment/disjoint endpoint comparisons, and fixed scalar domain checks;
- no physical/reference/exp/log/CDF/quantile calls.

Across the two existing witnesses this recipe has
`4*(256+1024)+2*4=5128` interval primitive calls per construction or independent
reconstruction pass. This counts interval API calls, not their internal directed
Decimal operations, constructor validation, hashing, parsing or sorting. Those
categories remain separate. If the binder rechecks either profile again rather
than reusing its already rebuilt immutable material, every such recheck is an
additional charged pure pass. The original40-profile reconstruction cannot be
counted twice as both new work and a reused result.

A simple evidence layout retains two intervals per node (t_i and R_i), hence
2560 intervals across both witnesses, plus two S/gamma/A records and identity
references. This is a logical field census, not a byte-fit proof or permission
to add a new output pool. The codec must account for all endpoints/copies inside
the existing64MiB science limit.

## 2. Forty views of sixteen original prior forecasts

Each case/grid has one physically computed no-learning prior forecast, with
uniform masses and no fitted residual. The existing16 originals supply all40
posterior/prior comparisons. M/F each has three posterior scales; D/W only base.
There is no new prior evaluation, selected prior scale or learned baseline.

The current `pair_scores` rejects different certificate scale identities and
revalidates scores through CDF/quantile helpers. Do not evade that rule by
rewriting an original certificate or claiming40 original priors. Introduce a
small explicit B2 view path, keeping the existing function unchanged.

### Narrow interfaces

These are proposed private binder interfaces, not a new public SDK or a generic
validated-object framework:

| Type/function | Required shape and role |
| --- | --- |
| `PriorPairView` | Exact prior row key `(case,N)`, exact posterior row key `(case,N,scale)`, references to the actual original prior and posterior score material, and both complete original identities. No replacement prior certificate or copied numerical arrays. |
| `bind_prior_views(...)` | Given B2's actual-material-rebuilt immutable16 prior and40 posterior contexts plus the proposed40 view records, require the complete fixed mapping and all joins below. Return views resolved to those actual contexts. No predictor, reference, exp/log, CDF construction/query or score reconstruction inside the alias loop. |
| `pair_from_prior_view(...)` | Read the resolved original score fields, keep both identities, and return a distinct `AliasedPairedScores` with exactly two outward differences: posterior-minus-original-prior squared loss and interval score. It is not a forged `PairedScores` with a rewritten certificate. |
| `classify_matched_views(...)` | Resolve exactly the four M/1024/base pairs from that complete mapping; recheck paired differences from their actual score fields and apply the unchanged two-metric aggregate/sign rule. Keep incomplete rows and null aggregates. No calls through the identity-incompatible `pair_scores` path. |

The contexts are built once by the full B2 boundary from actual raw referenced
bytes and independently bound source/primitive/truth material. Their original
CDFs/quantiles/moments/scores are validated or reconstructed there, before any
alias. They are stored as immutable tuples/objects local to that binding
operation. A decoded `PriorPairView`, nominal type, cached digest or caller's
claim of prior validation cannot replace that mandatory producer. A persisted
report validation starts by rebuilding this table from the actual material; it
does not deserialize a privileged cache or accept a stale `verified` flag.

Thus no **additional** CDF/quantile work is introduced by the40 alias bindings.
The existing56 physical forecast/score contexts and their necessary validation
passes still occur and remain charged. Do not call `enclose_scores`,
`enclose_predictive`, `pair_scores` or the old panel helper repeatedly from the
alias loop: those calls would add work and some would reject the intended
identity relation. If later implementation cannot enforce this call boundary,
it must revise the explicit pure-validation census before execution.

### Exact joins and preserved identities

For every view, require the original prior and posterior to have the same case,
N, source commit, protocol, observation/prefix identity, physical future query,
ordered future-vector material and actual truth enclosure/evidence identity.
Their candidate cells/configurations must join the same retained case/grid pool.
The prior still has role prior, uniform masses, delta0 and its own intact
probability/evidence identity; posterior retains its own different mass/evidence
identity. Both original certificate/material objects remain present and byte-bound.

The target pairing scale is exactly the posterior's permitted frozen scale.
The original prior's scale field is only the one frozen provenance anchor in
its existing context: it is recorded unchanged, not substituted by each target
scale. The view records the difference explicitly. No other shared identity
mismatch is relaxed, and the prior's independent probability/evidence identities
are not required to equal the posterior's. Do not allow cross-case, cross-grid,
changed-prefix, changed-truth or changed-source aliasing.

The producer must freeze that single original context identity before making
views. This proposal does not select a new numerical prior scale or prescribe
which already-admitted scale label anchors the metadata; the eventual producer
must document its deterministic choice before outcomes and preserve it. This is
an interface/provenance detail for review, not a new scientific baseline.
The separate pre-label physical freeze proves independence from the observed
label; matching a later observation digest alone never proves it.

A view may store references and small identities only. It must resolve to the
same original cells, mass vector, future endpoints, CDFs, quantiles, moments,
truth and scores. Replacing a field while updating every claimed digest must
still fail against the reconstructed table. Repeated references do not count
as new forecasts, but repeated serialized copies do count as physical output.

### Pairing and panel work census

The fixed mapping has40 bindings and40 paired differences, with two interval
subtractions per pair (80 calls). These are the report design's already-planned
40 pair calculations, not an additional40 on top. A later validation pass that
recomputes them adds80 calls and must be recorded separately.

For the primary aggregate, rechecking its four actual paired differences uses
8 more subtractions, then two four-term outward totals and division by4 use
8 additions and2 divisions. This is18 interval primitive calls per independent
primary validation/classification pass, excluding field/identity checks and the
already-required per-world diagnostics. There are no extra CDF, quantile,
forward, primitive, prior-normalization or reference calls in this path.
The exact count of independent validator passes must be fixed by source, not
hidden under a cache label or inferred from the135 row count.

## 3. Preserve all contrast and decision meanings

The two repeated-loss witnesses occupy the two D03:M03 rows within the existing
16 stresses (2 duplicate,12 force,2 weak). They do not add comparisons or worlds.
All20 same-scale256-to-1024 refinements retain their existing numerical ceilings;
the12 finest-grid adjacent-scale contrasts and F/W effects remain diagnostic,
with no winning-scale or desired-direction gate. Force pairs have different
truth constructions; weak pairs share future truth but differ in training.
Neither may enter the prior alias or primary matched pairing through a shared ID.

Only M01/M02/M03/M04 at N1024/base enter the equal-weight continuous-dk primary
panel. Both aggregate upper endpoints strictly below0 pass the local screen;
either lower endpoint nonnegative, including exact tie, means screen not met;
otherwise it is inconclusive. No individual-world improvement requirement or
tradeoff between metrics is added. Any unavailable primary yields null aggregate
differences, not a survivor average. All required report/qualification/completion
gates still precede utility, and a later transport failure preserves earlier
rejections while making execution incomplete.

## 4. Fake/rational test plan and remaining gates

The next source slice can use only synthetic arrays and retained fake material:

- Exact uniform masses and a two-node nonuniform rational surrogate: with
  q=(1/4,3/4) and uniform prior, T(q)=(1/10,9/10). Zero error gives A={1}; a
  truly exact ratio passes. This illustrates the pure kernel only, not a D1
  fixture; the actual D1 wrapper still rejects N other than256/1024.
- Nonzero derived c_M/c_D, containment at inclusive endpoints, disjointness,
  partial overlap, gamma0, invalid gamma/domain, zero/missing candidate and
  outward-rounding/ambient-context cases. No exp/log call may be used to test
  or implement the bound.
- Wrong prior, changed sigma/cells/query/record0, omitted second loss term and
  reordered nodes; different display/run/operation identities with otherwise
  legitimate physical joins. Two independently widened intervals that overlap
  must not establish the ideal identity.
- Coherently changed emitted vectors plus regenerated probabilities, certificates,
  witnesses and digests must fail against actual raw source/primitive material.
  Forged c_M/c_D must fail the material reconstruction, not obtain a wider A.
- Exactly16 original priors and40 views; missing/duplicate/foreign pair, altered
  prefix/truth/source/vector, substituted original CDF/score with matching new
  claimed hashes, or a mutated context after binding must fail. Original
  identities/numerical objects remain unchanged through legitimate aliasing.
- Poison predictor/reference/exp/log/CDF/quantile entrypoints during the view and
  pairing stages. Validate synthetic contexts before poisoning those boundaries;
  the production call graph must enforce the same one-time reconstruction path.
- Four-world exact ties, opposed metric signs, ambiguous intervals, incomplete
  or attempted worlds, stress substitutions and a late control failure. Preserve
  the fixed decision and null-denominator behavior without a p-value or tolerance.

The sufficient repeated-loss algorithm and alias types above need independent
source/proof review and authored implementation tests before use. The producer's
single prior metadata anchor must be fixed explicitly; no hidden choice is
made here. Full codecs, actual resolver/exposure/primitive and chronology binds,
proof of retained bytes, exact validator-pass census, durable recorder integration
and operational/numerical admission remain separate prerequisites. No absolute
product tolerance, coverage criterion or scientific policy is invented to close
them. Source authoring and algebraic derivation are not numerical qualification.


## 5. Conditional kernel source checkpoint

[tests/d1_repeated_loss.py](../../tests/d1_repeated_loss.py) implements only the
interval recipe in section1. Its tests are authored synthetic/rational cases;
imports, tests, typing, lint and numerical qualification have not been run for
this checkpoint. The existing Q1 directed primitives are reused unchanged.

`repeated_loss_witness(RepeatedLossInput)` takes an immutable ordered tuple of
`RepeatedLossNode(index, one_emitted, two_probability, prior_mass)`, the declared
count, and both original Decimal log-ratio bounds. `one_emitted` must be an exact
positive finite binary64 value within the reused interval representation domain;
`two_probability` is a supplied positive directed interval within[0,1]. Each
prior mass is an exact `Fraction(1,N)`, checked before using the uniform-prior
cancellation. Rational masses describe the fixed uniform prior, not another
prior-normalization calculation. All node indices must match0 throughN-1.

The pure kernel permits1 through1024 nodes so exact small rational surrogates can
exercise the proof. This is not the D1 profile admission surface: the future
binder must require precisely the two M03/D03 base-scale256/1024 pairs. It also
must supply actual-source-bound material, all profile gates, the exact reference
and physical-record joins, and reconstructed c_M/c_D. The kernel does not check
those premises. Its error-domain validation[0,1] and derived gamma<1 are algebraic
requirements, not replacements for the existing inclusive1e-9 profile ceiling.

Probability feasibility uses exact rational sums of the supplied lower and upper
endpoints, requiring `sum(lower)<=1<=sum(upper)`. A100-digit rounded sum could hide
a tiny inconsistent point-mass residual. The reused endpoint representation
bounds and1024-node limit bound this exact validation; it performs2N Decimal-to-
Fraction conversions and2N rational additions, separately from interval work.
Raw dataclass fields are revalidated, including exact scalar types, even if an
input object was manufactured without its normal constructor.

`RepeatedLossWitness` retains the complete original inputs, outward gamma,
allowance, squared sum, and each transformed probability, observed ratio and
relation. Inclusive containment means `contained`; strict separation means
`disjoint`; an intersection without containment means `overlap`. All nodes are
processed and retained; any disjoint node takes overall precedence, while the
separate disjoint/overlap index lists preserve both findings. A touching interval
that extends outside the allowance remains overlap. Missing/malformed/domain-
invalid input raises `ValueError`; it cannot manufacture a discrepancy result
or a successful report. B2 remains responsible for its unavailable/rejected/
unrun mapping and fail-stop policy.

Every returned witness exposes `material_authenticity="unchecked"` and
`qualification="unavailable"`; there is no `passed` field. A caller can supply
another internally consistent synthetic pair and obtain containment. That is
expected for a conditional kernel and is **not** the coherent-substitution
defense required at the full actual-material boundary. The later binder must
rebuild the input arrays/allowances against raw producer outputs and reference
returns, including a forged-vector-plus-updated-certificate regression. Persisted
witnesses and claimed digests cannot skip that obligation.

The complete recipe still uses4N+4 interval API calls per witness; both actual D1
witnesses use5128 per construction/reconstruction pass. There are N+7 calls to
`point` including the fixed scalar and total-initializer calls, plus bounded raw
field checks, exact rational feasibility and prior comparisons. Internal directed
Decimal operations, object validations, future parsing/hashing and every repeated
binder pass are separate census categories. The output adds2N+3 interval objects
besides its retained input references; serialized copies and actual codec fit
remain unproved and inside the existing output allowance. No oracle, physical,
exp/log, normalizer, CDF, quantile or score call is introduced.

The companion tests poison actual reference, predictor, simulator, normalizer
and CDF/score entrypoints. They exercise exact rational enclosure, both allowed
endpoints, disjoint/overlap precedence, complete coverage, normalized feasibility
below directed precision, malformed bypass objects, signed zero, finite/domain
limits and hostile ambient Decimal settings. These are proposed software checks,
not D1 outcomes. Prior alias implementation, the full report binder and its
physical-byte/operational evidence remain pending.
