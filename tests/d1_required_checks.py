"""Source-owned D1 expected-check descriptors, never evidence or gate evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from d1_report_contracts import ROW_MANIFEST, Kind, RowSpec

D = Decimal
type Category = Literal["predicate", "upper-bound", "diagnostic", "decision"]
type Applicability = Literal["all", "coarse-only", "finest-only"]


@dataclass(frozen=True)
class Operand:
    row_key: str
    field: str


@dataclass(frozen=True)
class RequiredCheck:
    name: str
    category: Category
    producer: str
    relation: str
    operands: tuple[Operand, ...]
    limit: Decimal | None = None
    constants: tuple[str, ...] = ()
    applicability: Applicability = "all"


@dataclass(frozen=True)
class ExpectedRow:
    ordinal: int
    key: str
    kind: Kind
    dependencies: tuple[str, ...]
    checks: tuple[RequiredCheck, ...]

    @property
    def verification_scope(self) -> Literal["required-check-descriptors-only"]:
        return "required-check-descriptors-only"

    @property
    def on_required_rejection(
        self,
    ) -> Literal["stop-subsequent-batch-retain-fault-and-later-unrun"]:
        return "stop-subsequent-batch-retain-fault-and-later-unrun"


_BY_KEY = {row.key: (i, row) for i, row in enumerate(ROW_MANIFEST)}
_FINE = (
    ("finest_cell_mass", "delta_upper", "0.0081"),
    ("finest_mean", "mean_error", "0.018"),
    ("finest_second", "second_error", "0.019"),
    ("finest_variance", "variance_error", "0.056"),
)


def _p(
    key: str,
    name: str,
    producer: str,
    *fields: str,
    relation: str = "rebuild-exact-material",
    constants: tuple[str, ...] = (),
) -> RequiredCheck:
    return RequiredCheck(
        name,
        "predicate",
        producer,
        relation,
        tuple(Operand(key, field) for field in fields),
        constants=constants,
    )


def _n(
    key: str,
    name: str,
    producer: str,
    field: str,
    limit: str,
    *,
    constants: tuple[str, ...] = (),
    relation: str = "upper<=",
) -> RequiredCheck:
    return RequiredCheck(
        name, "upper-bound", producer, relation, (Operand(key, field),), D(limit), constants
    )


def _d(
    key: str, name: str, producer: str, *fields: str, constants: tuple[str, ...] = ()
) -> RequiredCheck:
    return RequiredCheck(
        name,
        "diagnostic",
        producer,
        "retain-without-pass-flag",
        tuple(Operand(key, field) for field in fields),
        constants=constants,
    )


def _finest(key: str, count: int) -> tuple[RequiredCheck, ...]:
    return tuple(
        RequiredCheck(
            name,
            "upper-bound" if count == 1024 else "diagnostic",
            "D1Certificate",
            "upper<=" if count == 1024 else "retain-without-pass-flag",
            (Operand(key, "D1Certificate." + field),),
            D(limit) if count == 1024 else None,
            applicability="finest-only" if count == 1024 else "coarse-only",
        )
        for name, field, limit in _FINE
    )


def _future(key: str, *, prior: bool) -> tuple[RequiredCheck, ...]:
    return (
        _p(
            key,
            "bind.forecast",
            "enclose_predictive",
            "PredictiveEnclosure.certificate",
            "captured-future-endpoints",
            "exact-emitted-ratios" if not prior else "uniform-prior-masses",
            constants=(
                "complete-ordered-arrays",
                "exact-mass-feasibility",
                "role=prior" if prior else "role=posterior",
            ),
        ),
        _p(
            key,
            "forecast.moments",
            "enclose_predictive",
            "PredictiveEnclosure.finite_mean",
            "PredictiveEnclosure.finite_second",
            "PredictiveEnclosure.finite_variance",
            "PredictiveEnclosure.mean",
            "PredictiveEnclosure.second",
            "PredictiveEnclosure.variance",
            constants=("continuous-dk-separate-from-finite", "t=0.75"),
        ),
        _p(
            key,
            "forecast.cdf",
            "enclose_cdf",
            "PredictiveEnclosure.finite_cdf",
            "PredictiveEnclosure.cdf",
            "actual-cells-and-masses",
            constants=(
                "continuous-support=[-1,1]",
                "finite-support=endpoint-extrema",
                "complete-tie-groups",
                "same-vector-TV",
                "zero-below/one-at-upper-support",
            ),
        ),
        _p(
            key,
            "forecast.quantiles",
            "generalized_quantile",
            "PredictiveEnclosure.finite_quantiles",
            "PredictiveEnclosure.quantiles",
            constants=(
                "tails=0.05,0.95",
                "inverse=>=",
                "no-interpolation",
                "retain-crossing-ambiguity",
            ),
        ),
        RequiredCheck(
            "bind.truth",
            "predicate",
            "fixture-reference-and-release-binder",
            "rebuild-exact-material",
            (
                Operand(key, "ScoreEnclosure.truth"),
                Operand(key, "ScoreEnclosure.truth_evidence_sha256"),
                Operand(key, "forecast-before-truth-release"),
                Operand("fixture/" + key.split("/")[1], "independent-unrounded-future-proof"),
            ),
            constants=("independent-unrounded-future", "no-public-rounded-label-substitution"),
        ),
        _p(
            key,
            "score.rebuilt",
            "enclose_scores",
            "ScoreEnclosure.squared_loss",
            "ScoreEnclosure.interval_score",
            constants=(
                "ordered-feasible-tails",
                "alpha=0.1",
                "outside-multiplier=20",
                "continuous-dk-target",
            ),
        ),
        _d(
            key,
            "forecast.diagnostics",
            "forecast-and-score-material",
            "signed-residual",
            "width",
            "closed-interval-inclusion",
            "absolute-error",
            "squared-error",
            "finite-scores",
            "continuous-score-enclosures",
            constants=("indeterminate-inclusion-retained", "no-coverage-or-absolute-adequacy-gate"),
        ),
    )


def _posterior(key: str, case: str, count: int) -> tuple[RequiredCheck, ...]:
    records = 2 if case == "D03" else 1
    return (
        _p(
            key,
            "bind.prefix",
            "recheck_prefix_evidence",
            "QualifiedPrefixEvidence.bound",
            "QualifiedPrefixEvidence.nodes",
            "QualifiedPrefixEvidence.constants",
            "QualifiedPrefixEvidence.normalization",
            "QualifiedPrefixEvidence.emitted",
            "QualifiedPrefixEvidence.probabilities",
            "QualifiedPrefixEvidence.training",
            "QualifiedPrefixEvidence.arithmetic",
            constants=(
                "native-input-result-attempt-joins",
                "node-major-record-order",
                "coherent-substitution-defense",
            ),
        ),
        _p(
            key,
            "coverage.training",
            "D1PrefixPremises",
            "D1PrefixPremises.training[*]",
            relation="exact-ordered-coverage",
            constants=(f"records={records}", f"indices=0..{count - 1}", "failed=empty"),
        ),
        _p(
            key,
            "coverage.future",
            "D1PrefixPremises",
            "D1PrefixPremises.future",
            relation="exact-ordered-coverage",
            constants=(f"indices=0..{count - 1}", "failed=empty"),
        ),
        _p(
            key,
            "reference.endpoint",
            "reference-source-query-primitive-binder",
            "training-and-future-reference-enclosures",
            relation="exact-allowance-and-proof",
            constants=("reference_error_upper=1e-60", "all-physical-queries-and-returns"),
        ),
        _n(
            key,
            "training_endpoint",
            "D1PrefixPremises",
            "max(training[*].max_abs_error_upper)",
            "1e-12",
        ),
        _n(
            key,
            "future_endpoint",
            "QualifiedFutureEvidence",
            "QualifiedFutureEvidence.endpoints.max_abs_error_upper",
            "1e-12",
        ),
        _n(
            key,
            "reference.constants",
            "recheck_constants",
            "QualifiedPrefixEvidence.constants",
            "1e-48",
            relation="complete-rebuild-and-every-radius<=",
            constants=("pi-radius=1e-60", "exact-dyadic-scale-and-prior"),
        ),
        _n(
            key,
            "reference.normalization",
            "recheck_normalization/require_reference_reserve",
            "QualifiedPrefixEvidence.normalization",
            "1e-48",
            relation="complete-rebuild-and-every-radius<=",
            constants=(
                "two-global-plus-four-per-node-checks",
                "retain-vector-and-maximum",
                "joint-domain=[-32,4]",
                "perturbation<1",
                "positive-exp-sum-denominators",
            ),
        ),
        _p(
            key,
            "normalizer.complete",
            "bind_prefix",
            "BoundPrefix.result.normalization",
            "BoundPrefix.result.normalizer_input",
            "QualifiedPrefixEvidence.emitted",
            relation="exact-normalized-work-and-positive-emissions",
            constants=(
                f"exp_evaluations={count}",
                "log_evaluations=1",
                "underflow=empty",
                "all-finite-joint-and-normalized-logs",
                "0<emitted<=1",
            ),
        ),
        _n(
            key,
            "whole_prefix_node_error",
            "certify_d1_prefix",
            "D1Certificate.reserve_components[0]",
            "1e-9",
            constants=("max(observed,full-endpoint-plus-conditioned-native)",),
        ),
        _n(
            key,
            "centered_normalizer_error",
            "certify_d1_prefix",
            "D1Certificate.reserve_components[1]",
            "1e-9",
        ),
        _n(
            key,
            "normalized_probability_error",
            "certify_d1_prefix",
            "D1Certificate.reserve_components[2]",
            "1e-9",
            constants=("inclusive-emitted-ratio-bound-required",),
        ),
        _n(
            key,
            "overlapping_reserve",
            "certify_d1_prefix",
            "D1Certificate.reserve_upper",
            "3e-9",
            constants=(
                "D1Certificate.fixed_reserve=3e-9",
                "variation-uses-fixed-reserve",
                "overlapping-not-independent",
            ),
        ),
        _p(
            key,
            "certificate.rebuilt",
            "certify_d1_prefix",
            "D1PrefixPremises",
            "D1Certificate",
            constants=("exact-identity-fields-reasons-and-pass-value", "no-stored-flag-authority"),
        ),
    )


def _prior(key: str, count: int) -> tuple[RequiredCheck, ...]:
    return (
        _p(
            key,
            "bind.prior_freeze",
            "pre-label-pool-and-forecast-binder",
            "frozen-pool-and-query",
            "original-prior-context",
            constants=("before-label-release", "one-original-per-case-grid"),
        ),
        _p(
            key,
            "coverage.future",
            "EndpointEvidence",
            "EndpointEvidence",
            relation="exact-ordered-coverage",
            constants=(f"indices=0..{count - 1}", "failed=empty"),
        ),
        _p(
            key,
            "reference.endpoint",
            "reference-source-query-primitive-binder",
            "future-reference-enclosures",
            relation="exact-allowance-and-proof",
            constants=("reference_error_upper=1e-60",),
        ),
        _n(
            key,
            "future_endpoint",
            "EndpointEvidence",
            "EndpointEvidence.max_abs_error_upper",
            "1e-12",
        ),
        _p(
            key,
            "prior.uniform",
            "certify_d1_prior/enclose_predictive",
            "prior-cell-masses",
            "D1Certificate",
            relation="exact-uniform-and-zero-likelihood",
            constants=(
                f"mass=1/{count}",
                "delta=0",
                "likelihood-and-reserve-fields=0",
                "no-training-normalization-gates",
            ),
        ),
        _p(
            key,
            "certificate.rebuilt",
            "certify_d1_prior",
            "D1Identity",
            "EndpointEvidence",
            "D1Certificate",
        ),
    )


def _pair(
    name: str, producer: str, left: str, right: str, *fields: str, constants: tuple[str, ...] = ()
) -> RequiredCheck:
    return RequiredCheck(
        name,
        "predicate",
        producer,
        "exact-ordered-operand-pair",
        tuple(Operand(row, field) for row in (left, right) for field in fields),
        constants=constants,
    )


def _checks(spec: RowSpec) -> tuple[RequiredCheck, ...]:
    key, kind = spec.key, spec.kind
    tokens = key.split("/")
    if kind == "fixture":
        return tuple(
            _p(key, name, producer, *fields, constants=constants)
            for name, producer, fields, constants in (
                (
                    "bind.fixture",
                    "bind_attempt/verify_sources",
                    (
                        "FixtureBatch.plan",
                        "FixtureBatch.sources",
                        "FixtureBatch.query_trace",
                        "Attempt.public",
                        "Attempt.audit",
                    ),
                    ("exact-case-and-attempt", "all-available-shared-joins"),
                ),
                (
                    "fixture.reference",
                    "reference-execution-binder",
                    ("FixtureBatch.references", "FixtureBatch.reuse"),
                    ("recorded-binary64-coefficient", "complete-fixed-proof-plan"),
                ),
                (
                    "fixture.rounding",
                    "verify_rounding",
                    ("FixtureBatch.roundings",),
                    (
                        "lower_midpoint<lower<=upper<upper_midpoint",
                        "touch-or-straddle:fail-closed/no-retry",
                    ),
                ),
                (
                    "fixture.public_projection",
                    "candidate_material/validate_fixture_binding",
                    ("Attempt.public", "Attempt.audit"),
                    (
                        "opaque-public-IDs",
                        "private-F-anchor=1/8",
                        "public-anchor=0",
                        "no-truth-leak",
                    ),
                ),
                (
                    "fixture.exposure",
                    "authenticated-exposure-and-custody-binder",
                    ("Attempt.findings", "exposure-collection-and-owner-disposition"),
                    ("supplied-inventory-receipt-not-complete-history",),
                ),
            )
        )
    if kind in ("belief", "prior"):
        case, count = tokens[1], int(tokens[2])
        prior = kind == "prior"
        block = _prior(key, count) if prior else _posterior(key, case, count)
        alias = (
            ()
            if prior
            else (
                _pair(
                    "bind.prior_alias",
                    "B2.prior-view-binder",
                    key,
                    f"prior/{case}/{count}",
                    "original-forecast-and-score-context",
                    constants=(
                        "preserve-both-identities",
                        "no-new-CDF-or-forward",
                        "16-originals/40-views",
                    ),
                ),
            )
        )
        return block + _finest(key, count) + _future(key, prior=prior) + alias
    if kind == "prequential":
        case, count, record = tokens[1], int(tokens[2]), tokens[3]
        source = key if record == "record0" else f"belief/M03/{count}/0.25"
        bind = (
            _p(
                key,
                "bind.prequential_freeze",
                "FirstRecordCache.seal_prior",
                "frozen-pool-query-and-request-results",
                constants=("before-record0-label", "uniform-masses", "delta=0"),
            )
            if record == "record0"
            else _pair(
                "bind.duplicate_forecast",
                "duplicate_forecast",
                source,
                key,
                "original-physical-record-and-material",
                constants=(
                    "retain-distinct-original-identities",
                    "exact-record0-equivalence",
                    "before-record1-release",
                    "matched-one-record-delta",
                ),
            )
        )
        return (
            bind,
            _p(
                key,
                "coverage.training",
                "prequential-capture-binder",
                "training-request-result-reference-coverage",
                relation="exact-ordered-coverage",
                constants=(f"indices=0..{count - 1}", "failed=empty"),
            ),
            _p(
                key,
                "reference.endpoint",
                "reference-source-query-primitive-binder",
                "training-reference-enclosures",
                relation="exact-allowance-and-proof",
                constants=("reference_error_upper=1e-60",),
            ),
            _n(
                key,
                "training_endpoint",
                "prequential-capture-binder",
                "EndpointEvidence.max_abs_error_upper",
                "1e-12",
            ),
            RequiredCheck(
                "prequential.mean",
                "predicate",
                "training_forecast",
                "rebuild-exact-material",
                (
                    Operand(key, "TrainingForecast"),
                    Operand(source, "prior-or-matched-base-masses-and-delta"),
                ),
                constants=(
                    "radius=2*q*delta+q/(4*N)+endpoint_error",
                    "t=0.5",
                    "q=1/8" if case == "W03" else "q=1",
                    "endpoint_error<=1e-12+1e-60",
                ),
            ),
            RequiredCheck(
                "prequential.innovation",
                "predicate",
                "innovation",
                "rebuild-exact-material",
                (
                    Operand(key, "TrainingForecast.continuous_mean"),
                    Operand("fixture/" + case, f"actual-recorded-binary64-{record}"),
                ),
                constants=("label-minus-forecast-after-freeze", "no-utility-cutoff"),
            ),
        )
    if kind == "refinement":
        left, right = spec.dependencies
        pair = _pair(
            "bind.refinement",
            "B2.refinement",
            left,
            right,
            "finite-emitted-probabilities-and-moments",
            constants=(
                "same-case-scale-physical-prefix-query-truth",
                "group-four-consecutive-fine-cells",
            ),
        )
        fields = (
            (
                "refinement.cell_tv",
                "QualifiedPrefixEvidence.probabilities",
                "0.001",
                "sum(abs(coarse-grouped_fine))/2",
            ),
            ("refinement.mean", "PredictiveEnclosure.finite_mean", "0.0005", "abs(coarse-fine)"),
            (
                "refinement.variance",
                "PredictiveEnclosure.finite_variance",
                "0.001",
                "abs(coarse-fine)",
            ),
        )
        return (pair,) + tuple(
            RequiredCheck(
                name,
                "upper-bound",
                "B2.refinement",
                "upper<=",
                (Operand(left, field), Operand(right, field)),
                D(limit),
                (formula,),
            )
            for name, field, limit, formula in fields
        )
    if kind in ("scale", "stress"):
        left, right = spec.dependencies[:2]
        constants = (
            ("finest-adjacent-scales", "no-winning-scale")
            if kind == "scale"
            else ("own-truth-per-force-world", "different-private-force-constructions")
            if tokens[1].startswith("F")
            else ("shared-future-truth", "different-training-excitation")
            if tokens[1].startswith("W")
            else ("same-world-grid-prior-base", "both-D03-loss-terms-retained")
        )
        result: tuple[RequiredCheck, ...] = (
            _pair(
                "bind." + kind,
                "B2.contrast",
                left,
                right,
                "qualified-forecast-score-and-prefix",
                constants=constants,
            ),
            _pair("contrast.rebuilt", "B2.contrast", left, right, "diagnostic-operands"),
            RequiredCheck(
                "contrast.diagnostics",
                "diagnostic",
                "B2.contrast",
                "retain-without-pass-flag",
                (
                    Operand(left, "residual-width-score-inclusion-mass"),
                    Operand(right, "residual-width-score-inclusion-mass"),
                ),
            ),
        )
        if kind == "stress" and tokens[1] == "D03:M03":
            result += (
                RequiredCheck(
                    "duplicate.loss_identity",
                    "predicate",
                    "B2.material-bound-repeated-loss",
                    "contained-and-actual-material-joined",
                    (
                        Operand(left, "QualifiedPrefixEvidence"),
                        Operand(right, "QualifiedPrefixEvidence"),
                        Operand(spec.dependencies[2], "DuplicateForecast"),
                        Operand(key, "RepeatedLossWitness"),
                    ),
                    constants=(
                        "gamma=4*c_M+c_D",
                        "uniform-prior-square-law",
                        "disjoint=rejected",
                        "overlap=unavailable",
                        "kernel-alone-not-authenticity",
                    ),
                ),
            )
        return result
    if kind == "primary":
        posterior_key, prior_key = spec.dependencies
        return (
            _pair(
                "bind.primary",
                "B2.primary",
                posterior_key,
                prior_key,
                "actual-continuous-dk-score-and-truth",
                constants=("exact-matched-finest-base",),
            ),
            _pair(
                "bind.prior_alias",
                "B2.prior-view-binder",
                posterior_key,
                prior_key,
                "original-context-identities",
                constants=("no-certificate-identity-rewrite",),
            ),
            _pair(
                "paired_scores.rebuilt",
                "B2.pair-from-prior-view",
                posterior_key,
                prior_key,
                "ScoreEnclosure.squared_loss",
                "ScoreEnclosure.interval_score",
                constants=("posterior-minus-prior",),
            ),
            _p(
                key,
                "primary.diagnostics_complete",
                "B2.primary",
                "per-world-diagnostics",
                constants=(
                    "residual-width-inclusion-errors-finite-and-continuous-scores",
                    "no-individual-improvement-gate",
                ),
            ),
        )
    assert kind == "aggregate"
    primary = tuple(f"primary/{case}/1024/0.25" for case in ("M01", "M02", "M03", "M04"))
    return (
        _p(
            key,
            "bind.complete_panel",
            "B2.whole-report",
            "D1ReportStructure.rows",
            "D1ReportStructure.denominators",
            constants=("exact135-rows/9-denominators", "no-survivors"),
        ),
        RequiredCheck(
            "aggregate.rebuilt",
            "predicate",
            "B2.classify-matched-views",
            "rebuild-equal-four-world-mean",
            tuple(
                Operand(row, field)
                for row in primary
                for field in ("point_difference", "interval_difference")
            ),
            constants=("continuous-dk", "missing-primary=null-aggregate"),
        ),
        _p(
            key,
            "qualification.complete",
            "B2.whole-report",
            "all-required-gates",
            "source-runtime-authority-exposure-chronology",
            "actual-native-reference-callback-reuse-census",
            "primitive-transcript",
            constants=("preserve-rejection", "missing-proof=unavailable"),
        ),
        _p(
            key,
            "execution.complete",
            "B2.whole-report",
            "planned-row-evaluations",
            "control-process-retention-and-byte-closure",
            "first-and-supplemental-faults",
            constants=("transport-failure-not-numerical-failure", "no-budget-refund"),
        ),
        RequiredCheck(
            "utility.co_primary",
            "decision",
            "B2.classify-matched-views",
            "strict-co-primary-sign",
            (
                Operand(key, "aggregate-point-difference"),
                Operand(key, "aggregate-interval-difference"),
            ),
            constants=(
                "both-upper<0:local-screen-passed",
                "either-lower>=0:screen-not-met",
                "otherwise:inconclusive",
                "exact-tie:screen-not-met",
                "requires-complete-execution-and-qualification",
                "no-metric-tradeoff",
            ),
        ),
        _d(
            key,
            "aggregate.diagnostics",
            "B2.whole-report",
            "max-per-world-absolute-error-enclosure",
        ),
    )


def expected_checks(row_key: str) -> ExpectedRow:
    if type(row_key) is not str or row_key not in _BY_KEY:
        raise ValueError("Exact fixed D1 row key required")
    ordinal, spec = _BY_KEY[row_key]
    return ExpectedRow(ordinal, spec.key, spec.kind, spec.dependencies, _checks(spec))


def expected_registry() -> tuple[ExpectedRow, ...]:
    return tuple(expected_checks(spec.key) for spec in ROW_MANIFEST)


def _text(value: str) -> None:
    if type(value) is not str or not value or len(value) > 512:
        raise ValueError("Bounded exact descriptor text required")


def _row_types(value: ExpectedRow) -> None:
    if (
        type(value) is not ExpectedRow
        or type(value.ordinal) is not int
        or not 0 <= value.ordinal < 135
    ):
        raise ValueError("Exact expected-row descriptor required")
    for text in (value.key, value.kind):
        _text(text)
    if type(value.dependencies) is not tuple or len(value.dependencies) > 134:
        raise ValueError("Fixed bounded dependency tuple required")
    for text in value.dependencies:
        _text(text)
    if type(value.checks) is not tuple or not 1 <= len(value.checks) <= 64:
        raise ValueError("Fixed bounded required-check tuple required")
    for check in value.checks:
        if type(check) is not RequiredCheck:
            raise ValueError("Exact required-check descriptor required")
        for text in (
            check.name,
            check.category,
            check.producer,
            check.relation,
            check.applicability,
        ):
            _text(text)
        if type(check.constants) is not tuple or len(check.constants) > 16:
            raise ValueError("Fixed bounded constants required")
        for text in check.constants:
            _text(text)
        if type(check.operands) is not tuple or not 1 <= len(check.operands) <= 16:
            raise ValueError("Fixed bounded operand tuple required")
        for operand in check.operands:
            if type(operand) is not Operand:
                raise ValueError("Exact source-owned operand descriptor required")
            _text(operand.row_key)
            _text(operand.field)
        if check.limit is not None and (
            type(check.limit) is not Decimal or not check.limit.is_finite()
        ):
            raise ValueError("Limits are exact finite Decimal metadata, never booleans")


def validate_expected_row(value: ExpectedRow) -> ExpectedRow:
    """Compare descriptors to policy; does not inspect observations or pass a gate."""
    _row_types(value)
    expected = expected_checks(value.key)
    if value != expected or any(
        actual.limit is not None
        and fixed.limit is not None
        and actual.limit.as_tuple() != fixed.limit.as_tuple()
        for actual, fixed in zip(value.checks, expected.checks, strict=True)
    ):
        raise ValueError("Caller cannot select gates, operands, applicability, relations or limits")
    return expected


def validate_registry(values: tuple[ExpectedRow, ...]) -> tuple[ExpectedRow, ...]:
    if type(values) is not tuple or len(values) != 135:
        raise ValueError("Every planned row is required; no selected family or page")
    actual = tuple(validate_expected_row(value) for value in values)
    if tuple(row.key for row in actual) != tuple(row.key for row in ROW_MANIFEST):
        raise ValueError("Exact135-row order required, without duplication or substitution")
    return actual
