"""Policy descriptor checks only; no producer or gate evaluator is called."""

from __future__ import annotations

from dataclasses import fields, replace
from decimal import Decimal
from typing import NoReturn, cast

import d1_bounds
import pytest
from d1_report_contracts import ROW_MANIFEST
from d1_required_checks import (
    ExpectedRow,
    Operand,
    RequiredCheck,
    expected_checks,
    expected_registry,
    validate_expected_row,
    validate_registry,
)
from endpoint_belief_reference import EndpointOracle

import strange_physics.native_endpoint_beliefs as beliefs
import strange_physics.native_prediction as prediction
import strange_physics.simulation as simulation

D = Decimal


@pytest.fixture(autouse=True)
def no_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Expected policy metadata is not evidence or an evaluation")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)
    monkeypatch.setattr(prediction, "predict_native_spring", deny)
    monkeypatch.setattr(prediction, "_state_at_time", deny)
    monkeypatch.setattr(beliefs, "compute_native_endpoint_belief", deny)
    monkeypatch.setattr(simulation, "simulate", deny)
    for name in ("certify_d1_prefix", "certify_d1_prior", "enclose_predictive", "enclose_cdf",
                 "generalized_quantile", "enclose_scores",
                 "pair_scores", "classify_matched_panel"):
        monkeypatch.setattr(d1_bounds, name, deny)


def by_name(value: ExpectedRow) -> dict[str, RequiredCheck]:
    return {check.name: check for check in value.checks}


def replace_check(value: ExpectedRow, name: str, changed: RequiredCheck) -> ExpectedRow:
    return replace(value, checks=tuple(changed if c.name == name else c for c in value.checks))


def test_full_registry_preserves_manifest_denominators_dependencies_and_no_results() -> None:
    rows = expected_registry()
    assert len(rows) == 135 and validate_registry(rows) == rows
    assert tuple((r.key, r.kind, r.dependencies) for r in rows) == tuple(
        (r.key, r.kind, r.dependencies) for r in ROW_MANIFEST
    )
    assert {kind: sum(r.kind == kind for r in rows) for kind in {r.kind for r in rows}} == {
        "fixture": 8, "belief": 40, "prior": 16, "prequential": 18, "refinement": 20,
        "scale": 12, "stress": 16, "primary": 4, "aggregate": 1,
    }
    assert all(len({c.name for c in row.checks}) == len(row.checks) for row in rows)
    assert all(operand.row_key in {r.key for r in rows}
               for row in rows for check in row.checks for operand in check.operands)
    assert not {"passed", "observed", "qualification", "utility"}.intersection(
        f.name for f in fields(RequiredCheck)
    )
    assert all(r.verification_scope == "required-check-descriptors-only" for r in rows)
    assert all(r.on_required_rejection == "stop-subsequent-batch-retain-fault-and-later-unrun"
               for r in rows)


@pytest.mark.parametrize("family", ("belief", "prior"))
def test_coarse_certificates_are_diagnostics_while_finest_bounds_are_inclusive(family: str) -> None:
    suffix = "/0.25" if family == "belief" else ""
    coarse = by_name(expected_checks(f"{family}/M03/256{suffix}"))
    fine = by_name(expected_checks(f"{family}/M03/1024{suffix}"))
    for name in ("finest_cell_mass", "finest_mean", "finest_second", "finest_variance"):
        assert coarse[name].category == "diagnostic" and coarse[name].limit is None
        assert coarse[name].relation == "retain-without-pass-flag"
        assert coarse[name].applicability == "coarse-only"
        assert fine[name].category == "upper-bound" and fine[name].relation == "upper<="
        assert fine[name].applicability == "finest-only"
    assert fine["finest_cell_mass"].limit == D("0.0081")
    assert fine["finest_variance"].limit == D("0.056")


def test_prior_has_no_posterior_training_loss_or_normalizer_gate() -> None:
    prior = by_name(expected_checks("prior/D03/1024"))
    posterior = by_name(expected_checks("belief/D03/1024/0.25"))
    forbidden = {"bind.prefix", "coverage.training", "training_endpoint", "normalizer.complete",
                 "whole_prefix_node_error", "overlapping_reserve", "reference.normalization"}
    assert forbidden.isdisjoint(prior)
    assert forbidden.issubset(posterior)
    assert "delta=0" in prior["prior.uniform"].constants
    assert "likelihood-and-reserve-fields=0" in prior["prior.uniform"].constants
    assert prior["certificate.rebuilt"].producer == "certify_d1_prior"
    assert "bind.prior_alias" not in prior and "bind.prior_alias" in posterior


def test_duplicate_prefix_keeps_both_channels_and_one_overlapping_reserve() -> None:
    one = by_name(expected_checks("belief/M03/256/0.25"))
    two = by_name(expected_checks("belief/D03/256/0.25"))
    assert "records=1" in one["coverage.training"].constants
    assert "records=2" in two["coverage.training"].constants
    assert two["training_endpoint"].operands[0].field == "max(training[*].max_abs_error_upper)"
    assert two["overlapping_reserve"].limit == one["overlapping_reserve"].limit == D("3e-9")
    assert "variation-uses-fixed-reserve" in two["overlapping_reserve"].constants
    assert two["reference.normalization"].limit == D("1e-48")
    assert "two-global-plus-four-per-node-checks" in two["reference.normalization"].constants
    assert tuple(operand.field for operand in two["normalizer.complete"].operands[:2]) == (
        "BoundPrefix.result.normalization", "BoundPrefix.result.normalizer_input",
    )


def test_record1_uses_matched_posterior_and_training_time_not_a_second_prior() -> None:
    first = by_name(expected_checks("prequential/D03/256/record0"))
    second = by_name(expected_checks("prequential/D03/256/record1"))
    weak = by_name(expected_checks("prequential/W03/256/record0"))
    assert "bind.prequential_freeze" in first and "bind.prequential_freeze" not in second
    assert "bind.duplicate_forecast" in second
    assert second["prequential.mean"].operands[1].row_key == "belief/M03/256/0.25"
    assert "matched-one-record-delta" in second["bind.duplicate_forecast"].constants
    assert "t=0.5" in second["prequential.mean"].constants
    assert "q=1/8" in weak["prequential.mean"].constants
    assert "forecast.cdf" not in second and "score.rebuilt" not in second
    assert second["training_endpoint"].operands[0].field == "EndpointEvidence.max_abs_error_upper"


def test_refinement_uses_ordered_finite_operands_and_no_continuous_error_substitution() -> None:
    value = by_name(expected_checks("refinement/F02/0.5/256-to-1024"))
    binding = value["bind.refinement"]
    assert tuple(x.row_key for x in binding.operands) == ("belief/F02/256/0.5", "belief/F02/1024/0.5")
    assert "group-four-consecutive-fine-cells" in binding.constants
    assert value["refinement.mean"].limit == D("0.0005")
    assert "finite_mean" in value["refinement.mean"].operands[0].field
    assert all(c.relation == "upper<=" for c in value.values() if c.category == "upper-bound")


@pytest.mark.parametrize("key", ("scale/M02/1024/0.125-to-0.25", "stress/F04:M04/1024/0.5",
                                  "stress/W03:M03/256/0.25"))
def test_scale_and_force_weak_effects_are_diagnostics_without_utility_threshold(key: str) -> None:
    checks = by_name(expected_checks(key))
    assert all(c.category != "upper-bound" and c.limit is None for c in checks.values())
    diagnostic = checks["contrast.diagnostics"]
    assert diagnostic.category == "diagnostic" and diagnostic.relation == "retain-without-pass-flag"
    assert "duplicate.loss_identity" not in checks
    if "/F" in key:
        assert "own-truth-per-force-world" in checks["bind.stress"].constants
    elif "/W" in key:
        assert "shared-future-truth" in checks["bind.stress"].constants


def test_duplicate_witness_descriptor_keeps_material_gate_and_unavailable_overlap() -> None:
    check = by_name(expected_checks("stress/D03:M03/1024/0.25"))["duplicate.loss_identity"]
    assert check.limit is None and check.category == "predicate"
    assert check.relation == "contained-and-actual-material-joined"
    assert "kernel-alone-not-authenticity" in check.constants and "overlap=unavailable" in check.constants
    assert tuple(x.row_key for x in check.operands[:3]) == (
        "belief/D03/1024/0.25", "belief/M03/1024/0.25", "prequential/D03/1024/record1",
    )


def test_co_primary_rule_is_strict_paired_and_not_individual_world_superiority() -> None:
    primary = by_name(expected_checks("primary/M01/1024/0.25"))
    aggregate = expected_checks("aggregate/matched/base/continuous-dk")
    checks = by_name(aggregate)
    assert len(aggregate.dependencies) == 134
    assert "no-individual-improvement-gate" in primary["primary.diagnostics_complete"].constants
    assert "posterior-minus-prior" in primary["paired_scores.rebuilt"].constants
    assert {o.row_key for o in checks["aggregate.rebuilt"].operands} == {
        f"primary/M0{i}/1024/0.25" for i in range(1, 5)
    }
    decision = checks["utility.co_primary"]
    assert decision.category == "decision" and decision.limit is None
    assert "both-upper<0:local-screen-passed" in decision.constants
    assert "either-lower>=0:screen-not-met" in decision.constants
    assert "exact-tie:screen-not-met" in decision.constants
    assert "missing-primary=null-aggregate" in checks["aggregate.rebuilt"].constants


@pytest.mark.parametrize("change", ("missing", "extra", "duplicate", "order", "wrong-family"))
def test_no_subset_or_family_substitution_can_validate(change: str) -> None:
    rows = expected_registry()
    if change == "missing":
        changed = rows[:-1]
    elif change == "extra":
        changed = (*rows, rows[0])
    elif change == "duplicate":
        changed = (rows[1], *rows[1:])
    elif change == "order":
        changed = (rows[1], rows[0], *rows[2:])
    else:
        changed = (expected_checks("prior/M01/256"), *rows[1:])
    with pytest.raises(ValueError):
        validate_registry(changed)


@pytest.mark.parametrize("change", ("name", "category", "producer", "relation", "limit", "quantum",
                                    "operand-row", "operand-field", "applicability", "constants"))
def test_callers_cannot_choose_a_numerical_policy(change: str) -> None:
    row = expected_checks("belief/M01/1024/0.25")
    check = by_name(row)["finest_mean"]
    changes: dict[str, object] = {
        "name": "made-up", "category": "diagnostic", "producer": "unreviewed",
        "relation": "upper<", "limit": D("0.18"), "quantum": D("0.0180"),
        "operand-row": (Operand("belief/M02/1024/0.25", check.operands[0].field),),
        "operand-field": (Operand(row.key, "finite-error-instead"),),
        "applicability": "coarse-only", "constants": ("optional=true",),
    }
    field = {"quantum": "limit", "operand-row": "operands", "operand-field": "operands"}.get(change, change)
    altered = replace(check, **{field: changes[change]})
    with pytest.raises(ValueError):
        validate_expected_row(replace_check(row, check.name, altered))


@pytest.mark.parametrize("change", ("missing", "extra", "duplicate", "reordered", "coherent-foreign-block"))
def test_gate_sequence_cannot_drop_or_replace_requirements(change: str) -> None:
    row = expected_checks("belief/M01/1024/0.25")
    if change == "missing":
        checks = row.checks[:-1]
    elif change == "extra":
        checks = (*row.checks, row.checks[0])
    elif change == "duplicate":
        checks = (row.checks[1], *row.checks[1:])
    elif change == "reordered":
        checks = (row.checks[1], row.checks[0], *row.checks[2:])
    else:
        checks = expected_checks("prior/M01/1024").checks
    with pytest.raises(ValueError):
        validate_expected_row(replace(row, checks=checks))


@pytest.mark.parametrize("bad", (True, False, 0.018, D("NaN"), D("Infinity")))
def test_non_decimal_or_nonfinite_limits_fail_before_equality(bad: object) -> None:
    row = expected_checks("belief/M01/1024/0.25")
    check = by_name(row)["finest_mean"]
    with pytest.raises(ValueError):
        validate_expected_row(replace_check(row, check.name, replace(check, limit=cast(Decimal, bad))))


def test_boolean_ordinal_is_not_equal_to_zero_ordinal() -> None:
    with pytest.raises(ValueError):
        validate_expected_row(replace(expected_checks("fixture/M01"), ordinal=False))


def test_coherent_diagnostic_fake_pass_descriptor_is_rejected() -> None:
    row = expected_checks("scale/F02/1024/0.25-to-0.5")
    check = by_name(row)["contrast.diagnostics"]
    attempted = replace(check, category="upper-bound", relation="upper<=", limit=D(1))
    with pytest.raises(ValueError):
        validate_expected_row(replace_check(row, check.name, attempted))


@pytest.mark.parametrize("key", ("belief/D03/256/0.125", "primary/F02/1024/0.25",
                                  "belief/M01/64/0.25", "unknown", "fixture/M01\n"))
def test_no_unregistered_rows_are_inferred_from_lookalike_keys(key: str) -> None:
    with pytest.raises(ValueError):
        expected_checks(key)


@pytest.mark.parametrize("change", ("dependencies", "ordinal", "kind"))
def test_row_header_cannot_retarget_an_otherwise_correct_check_list(change: str) -> None:
    row = expected_checks("belief/D03/1024/0.25")
    replacement: object = () if change == "dependencies" else 0 if change == "ordinal" else "prior"
    with pytest.raises(ValueError):
        validate_expected_row(replace(row, **{change: replacement}))


def test_strict_tie_decision_cannot_be_replaced_by_an_inclusive_pass() -> None:
    row = expected_checks("aggregate/matched/base/continuous-dk")
    check = by_name(row)["utility.co_primary"]
    changed = replace(check, constants=tuple(
        "both-upper<=0:local-screen-passed" if x == "both-upper<0:local-screen-passed" else x
        for x in check.constants
    ))
    with pytest.raises(ValueError):
        validate_expected_row(replace_check(row, check.name, changed))
