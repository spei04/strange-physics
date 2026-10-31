"""Authored synthetic D1 contract checks; no truth generation or numerical evaluation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, NoReturn, cast

import pytest
from pydantic import ValidationError

from strange_physics.calibration_fixture_contracts import (
    CASE_IDS,
    MAX_INVENTORY_ROWS,
    MAX_PUBLIC_BYTES,
    PROTOCOL_SHA256,
    D1Blueprint,
    D1ExposureEntry,
    D1ExposureFinding,
    D1ExposureInventory,
    D1FixtureOutcome,
    D1FixtureOutcomes,
    D1LabelClaim,
    D1OwnerReviewReference,
    D1PhysicalHistory,
    D1PhysicalIdentity,
    D1PrivateAudit,
    D1PublicFixture,
    D1WorldSignature,
    calibration_fixture_json_schema,
    candidate_material,
    check_supplied_inventory,
    parse_d1_audit,
    parse_d1_inventory,
    parse_d1_public,
    physical_identity,
    validate_fixture_binding,
    validate_materialized_fixtures,
)
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import message_sha256

S = "a" * 64
T = "b" * 64


@pytest.fixture(autouse=True)
def no_numerical_work(monkeypatch: pytest.MonkeyPatch) -> None:
    # Importing the existing reference class does not execute its methods.
    from endpoint_belief_reference import EndpointOracle

    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("D1 contract tests may not generate numerical reference data")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)


def blueprint(case: str = "M03") -> D1Blueprint:
    row = {
        "M01": (1, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        "M02": (5, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        "M03": (13, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        "M04": (27, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        "D03": (13, "zero-rest-spring", 1.0, 2, (0.25,)),
        "F02": (5, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
        "F04": (27, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
        "W03": (13, "zero-rest-spring", 0.125, 1, (0.25,)),
    }[case]
    return D1Blueprint.model_validate(
        dict(
            case_id=case,
            coefficient_numerator=row[0],
            mechanism=row[1],
            initial_x=row[2],
            record_count=row[3],
            scales=row[4],
        )
    )


def public_data(case: str = "M03", token: str = "1") -> dict[str, Any]:
    b = blueprint(case)
    q = b.initial_x
    # Arbitrary legal labels deliberately NOT reference solutions or future truth.
    observed = 0.75 if q == 1.0 else 0.09375
    experiment = {
        "particles": [{"id": "p0", "position": [q, 0.0], "velocity": [0.0, 0.0], "mass": 1.0}],
        "impulse": {"particle_id": "p0", "vector": [0.0, 0.0]},
    }
    trajectory = {
        "frames": [
            {"time": 0.0, "positions": [[q, 0.0]], "velocities": [[0.0, 0.0]]},
            {"time": 0.5, "positions": [[observed, 0.0]], "velocities": [[0.0, 0.0]]},
        ]
    }
    return {
        "observations": {
            "run_id": "d1r-" + token * 32,
            "engine_version": "synthetic-ra-n03-d1.v1",
            "engine_fingerprint": PROTOCOL_SHA256,
            "space": {
                "structure": {
                    "particle_ids": ["p0"],
                    "anchors": [{"id": "a0", "position": [0.0, 0.0]}],
                    "connections": [{"a": "p0", "b": "a0"}],
                },
                "sampling": {
                    "duration": 0.5,
                    "dt": 1 / 64,
                    "sample_interval": 0.5,
                    "position_noise": 0.0,
                    "velocity_noise": 0.0,
                },
                "budget": b.record_count,
                "calibration_experiments": 0,
            },
            "records": [
                {
                    "operation_id": "d1o-" + token * 31 + str(index),
                    "index": index,
                    "experiment": experiment,
                    "status": "completed",
                    "trajectory": trajectory,
                }
                for index in range(b.record_count)
            ],
        }
    }


def public(case: str = "M03", token: str = "1") -> D1PublicFixture:
    return parse_d1_public(json.dumps(public_data(case, token)).encode())


def audit(value: D1PublicFixture, case: str = "M03") -> D1PrivateAudit:
    b = blueprint(case)
    record = value.observations.records[0]
    assert record.trajectory is not None
    claim = D1LabelClaim(
        recorded_x_hex=record.trajectory.frames[-1].positions[0][0].hex(),
        reference_evidence_sha256=S,
        rounding_evidence_sha256=T,
    )
    return D1PrivateAudit(
        source_commit="c" * 40,
        blueprint=b,
        public_sha256=message_sha256(value),
        coefficient_hex=(b.coefficient_numerator / 7).hex(),
        training_labels=(claim,) * b.record_count,
        future_label=D1LabelClaim(
            recorded_x_hex=(0.625).hex(),
            reference_evidence_sha256=T,
            rounding_evidence_sha256=S,
        ),
    )


def inventory(*identities: D1PhysicalIdentity) -> D1ExposureInventory:
    return D1ExposureInventory(
        inventory_kind="exposed-development",
        entries=tuple(D1ExposureEntry(source_evidence_sha256=S, identity=x) for x in identities),
    )


@pytest.mark.parametrize("case", CASE_IDS)
def test_fixed_cases_are_structural_material_only(case: str) -> None:
    p = public(case)
    a = audit(p, case)
    validate_fixture_binding(p, a)
    material = candidate_material(p)
    assert material == p.observations
    assert material.engine_version == "synthetic-ra-n03-d1.v1"
    assert material.engine_fingerprint == PROTOCOL_SHA256
    assert p.velocity_semantics == "unused-zero-placeholder"
    assert a.authority == "supplied-material-not-numerical-proof"
    assert parse_d1_audit(a.model_dump_json().encode()) == a
    assert tuple(record.index for record in material.records) == tuple(range(len(material.records)))


def test_projection_is_a_core_allowlist_without_private_mapping() -> None:
    p = public("F02")
    a = audit(p, "F02")
    material = candidate_material(p).model_dump(mode="json")
    assert set(material) == {
        "schema_version",
        "run_id",
        "engine_version",
        "engine_fingerprint",
        "space",
        "records",
    }
    for private_name in (
        "blueprint",
        "case_id",
        "coefficient_hex",
        "mechanism",
        "training_labels",
        "future_label",
        "public_sha256",
        "reference_evidence_sha256",
    ):
        assert private_name not in json.dumps(material)
    with pytest.raises(ValueError, match="separate D1 public type"):
        candidate_material(cast(D1PublicFixture, a))


@pytest.mark.parametrize(
    "extra", ("blueprint", "truth_coefficient", "future_label", "audit_sha256")
)
def test_private_extras_never_parse_as_public(extra: str) -> None:
    data = public_data()
    data[extra] = S
    with pytest.raises(ContractViolation):
        parse_d1_public(json.dumps(data).encode())


@pytest.mark.parametrize(
    "field,value",
    (
        ("run_id", "D1-M03"),
        ("run_id", "d1r-" + "a" * 31),
        ("run_id", "d1r-" + "a" * 32 + "\n"),
        ("engine_version", "synthetic-omitted-force-F02"),
        ("engine_fingerprint", S),
    ),
)
def test_public_provenance_does_not_accept_blueprint_tags(field: str, value: str) -> None:
    data = public_data()
    data["observations"][field] = value
    with pytest.raises(ContractViolation):
        parse_d1_public(json.dumps(data).encode())


@pytest.mark.parametrize(
    "field,value",
    (
        ("duration", 0.75),
        ("dt", 1 / 32),
        ("sample_interval", 0.25),
        ("position_noise", 0.01),
        ("velocity_noise", 0.01),
    ),
)
def test_sampling_is_exact_not_just_a_compatible_terminal(field: str, value: float) -> None:
    data = public_data()
    data["observations"]["space"]["sampling"][field] = value
    with pytest.raises(ContractViolation):
        parse_d1_public(json.dumps(data).encode())


@pytest.mark.parametrize("kind", ("ordinal", "operation_reuse", "changed_action", "changed_value"))
def test_duplicate_is_physical_repeat_not_identity_reuse(kind: str) -> None:
    data = json.loads(json.dumps(public_data("D03")))
    a, b = data["observations"]["records"]
    if kind == "ordinal":
        b["index"] = 2
    elif kind == "operation_reuse":
        b["operation_id"] = a["operation_id"]
    elif kind == "changed_action":
        b["experiment"]["particles"][0]["position"][0] = 0.125
    else:
        b["trajectory"]["frames"][-1]["positions"][0][0] = 0.8
    with pytest.raises(ContractViolation):
        parse_d1_public(json.dumps(data).encode())


@pytest.mark.parametrize(
    "kind", ("initial_frame", "terminal_time", "velocity", "negative_zero", "failed")
)
def test_synthetic_frames_cannot_masquerade_as_general_trajectories(kind: str) -> None:
    data = public_data()
    record = data["observations"]["records"][0]
    if kind == "initial_frame":
        record["trajectory"]["frames"][0]["positions"][0][0] = 0.8
    elif kind == "terminal_time":
        record["trajectory"]["frames"][-1]["time"] = 0.5 + 1e-10
    elif kind == "velocity":
        record["trajectory"]["frames"][-1]["velocities"][0][0] = 0.1
    elif kind == "negative_zero":
        record["experiment"]["particles"][0]["position"][1] = -0.0
    else:
        record["status"], record["trajectory"], record["error"] = (
            "failed",
            None,
            "simulation_failed",
        )
    with pytest.raises(ContractViolation):
        parse_d1_public(json.dumps(data).encode())


@pytest.mark.parametrize("kind", ("digest", "initial", "label", "case"))
def test_audit_binds_exact_public_values_and_shape(kind: str) -> None:
    p = public()
    a = audit(p)
    data = a.model_dump(mode="json")
    if kind == "digest":
        data["public_sha256"] = S
    elif kind == "initial":
        p = public("W03")
        data["public_sha256"] = message_sha256(p)
    elif kind == "label":
        data["training_labels"][0]["recorded_x_hex"] = (0.8).hex()
    else:
        p = public("D03")
        data["public_sha256"] = message_sha256(p)
    changed = parse_d1_audit(json.dumps(data).encode())
    with pytest.raises(ValueError, match="audit|Audit"):
        validate_fixture_binding(p, changed)


@pytest.mark.parametrize(
    "field,value",
    (
        ("coefficient_hex", "nan"),
        ("coefficient_hex", "0x1p+0"),
        ("coefficient_hex", (2.0).hex()),
        ("protocol_sha256", S),
        ("future_initial_x", 0.75),
        ("future_time", 1.0),
    ),
)
def test_private_claim_shape_rejects_wrong_profile(field: str, value: object) -> None:
    data = audit(public()).model_dump(mode="json")
    data[field] = value
    with pytest.raises(ContractViolation):
        parse_d1_audit(json.dumps(data).encode())


@pytest.mark.parametrize(
    "field,value",
    (
        ("coefficient_numerator", 5),
        ("initial_x", 0.125),
        ("mechanism", "spring-plus-k-over-eight-force"),
        ("record_count", 2),
        ("scales", (0.125, 0.25)),
        ("counts", (64, 1024)),
    ),
)
def test_blueprint_cannot_silently_expand_matrix(field: str, value: object) -> None:
    data = blueprint().model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        D1Blueprint.model_validate(data)


def test_construction_failures_preserve_all_eight_planned_denominators() -> None:
    outcomes = tuple(
        D1FixtureOutcome(
            blueprint=blueprint(case),
            status="failed" if case == "F02" else "unrun",
            failure_stage="reference" if case == "F02" else None,
            failure_evidence_sha256=S if case == "F02" else None,
            audit=None,
        )
        for case in CASE_IDS
    )
    report = D1FixtureOutcomes(outcomes=outcomes)
    assert len(report.outcomes) == 8
    assert sum(x.status == "failed" for x in report.outcomes) == 1
    assert all(x.audit is None for x in report.outcomes)
    assert "observations" not in report.model_dump_json()
    with pytest.raises(ValidationError):
        D1FixtureOutcomes(outcomes=outcomes[:-1])
    with pytest.raises(ValidationError):
        D1FixtureOutcomes(outcomes=tuple(reversed(outcomes)))


@pytest.mark.parametrize("status", ("unrun", "failed"))
def test_unavailable_fixture_cannot_carry_materialized_claim(status: str) -> None:
    data = {
        "blueprint": blueprint(),
        "status": status,
        "failure_stage": None,
        "failure_evidence_sha256": None,
        "audit": audit(public()),
    }
    with pytest.raises(ValidationError):
        D1FixtureOutcome.model_validate(data)


def test_renaming_ids_cannot_clear_physical_exposure() -> None:
    p1, p2 = public(token="1"), public(token="2")
    a1, a2 = audit(p1), audit(p2)
    assert a1.public_sha256 != a2.public_sha256
    i1, i2 = physical_identity(p1, a1), physical_identity(p2, a2)
    assert i1 == i2
    check = check_supplied_inventory(i2, inventory(i1))
    assert check.overlapping_world_entries == 1
    assert check.first_exact_construction_index == 0
    assert check.conclusion == "overlap-in-supplied-inventory"


def test_changed_history_does_not_hide_reused_physical_world() -> None:
    p, repeated = public(), public("D03", token="2")
    a, repeated_audit = audit(p), audit(repeated, "D03")
    single = physical_identity(p, a)
    duplicate = physical_identity(repeated, repeated_audit)
    assert single.world_sha256 == duplicate.world_sha256
    assert single.history_sha256 != duplicate.history_sha256
    check = check_supplied_inventory(duplicate, inventory(single))
    assert check.first_overlap_index == 0
    assert check.first_exact_construction_index is None


def test_weak_action_is_same_world_but_force_is_different_mechanism() -> None:
    m, w, f = public(), public("W03"), public("F02")
    mi = physical_identity(m, audit(m))
    wi = physical_identity(w, audit(w, "W03"))
    fi = physical_identity(f, audit(f, "F02"))
    assert check_supplied_inventory(wi, inventory(mi)).overlapping_world_entries == 1
    m2 = public("M02")
    m2i = physical_identity(m2, audit(m2, "M02"))
    assert check_supplied_inventory(fi, inventory(m2i)).overlapping_world_entries == 0
    assert wi.probe_sha256 == mi.probe_sha256
    assert wi.action_sha256 != mi.action_sha256


def test_empty_inventory_is_only_a_supplied_inventory_statement() -> None:
    p = public()
    empty = inventory()
    result = check_supplied_inventory(physical_identity(p, audit(p)), empty)
    assert result.supplied_entries == 0
    assert result.conclusion == "no-overlap-in-supplied-inventory"
    assert empty.completeness == "not-established-by-this-contract"
    review = D1OwnerReviewReference(
        development_inventory_sha256=message_sha256(empty),
        comparison_inventory_sha256=S,
        fixture_outcomes_sha256=T,
        review_evidence_sha256=S,
        disposition="pending",
    )
    assert review.scope == "historical-completeness-requires-independent-review"
    assert "accepted" not in review.model_dump_json()


def test_inventory_is_bounded_and_parser_rejects_overclaims() -> None:
    p = public()
    i = physical_identity(p, audit(p))
    entry = D1ExposureEntry(source_evidence_sha256=S, identity=i)
    with pytest.raises(ValidationError):
        D1ExposureInventory(
            inventory_kind="exposed-development", entries=(entry,) * (MAX_INVENTORY_ROWS + 1)
        )
    raw = inventory(i).model_dump(mode="json")
    raw["completeness"] = "complete"
    with pytest.raises(ContractViolation):
        parse_d1_inventory(json.dumps(raw).encode())
    with pytest.raises(ContractViolation):
        parse_d1_public(b" " * (MAX_PUBLIC_BYTES + 1))
    with pytest.raises(ContractViolation):
        parse_d1_public(b'{"observations":{},"observations":{}}')


def test_exposure_findings_cannot_hide_a_missing_denominator() -> None:
    with pytest.raises(ValidationError):
        D1ExposureFinding(
            identity_sha256=S,
            inventory_sha256=T,
            inventory_kind="exposed-development",
            supplied_entries=0,
            reserved_coefficient_entries=0,
            first_reserved_coefficient_index=None,
            overlapping_world_entries=1,
            first_overlap_index=0,
            first_exact_construction_index=None,
            conclusion="no-overlap-in-supplied-inventory",
        )


def test_schema_separates_public_and_private_roots() -> None:
    schema = calibration_fixture_json_schema()
    assert schema["x-public-roots"] == ["D1PublicFixture"]
    assert "D1PrivateAudit" in schema["x-private-roots"]
    public_schema = schema["$defs"]["D1PublicFixture"]
    assert set(public_schema["properties"]) == {
        "schema_version",
        "provenance",
        "velocity_semantics",
        "observations",
    }
    assert public_schema["additionalProperties"] is False


def test_complete_materialized_subset_requires_exact_private_joins() -> None:
    values = tuple(public(case, token=format(i + 1, "x")) for i, case in enumerate(CASE_IDS))
    outcomes = D1FixtureOutcomes(
        outcomes=tuple(
            D1FixtureOutcome(
                blueprint=blueprint(case),
                status="materialized",
                failure_stage=None,
                failure_evidence_sha256=None,
                audit=audit(value, case),
            )
            for case, value in zip(CASE_IDS, values, strict=True)
        )
    )
    validate_materialized_fixtures(values, outcomes)
    with pytest.raises(ValueError, match="subset"):
        validate_materialized_fixtures(values[:-1], outcomes)
    with pytest.raises(ValueError, match="audit"):
        validate_materialized_fixtures(tuple(reversed(values)), outcomes)
    changed = json.loads(values[4].model_dump_json())
    for record in changed["observations"]["records"]:
        record["trajectory"]["frames"][-1]["positions"][0][0] = 0.8
    repeated = parse_d1_public(json.dumps(changed).encode())
    changed_values = (*values[:4], repeated, *values[5:])
    changed_outcomes = D1FixtureOutcomes(
        outcomes=tuple(
            D1FixtureOutcome(
                blueprint=blueprint(case),
                status="materialized",
                failure_stage=None,
                failure_evidence_sha256=None,
                audit=audit(value, case),
            )
            for case, value in zip(CASE_IDS, changed_values, strict=True)
        )
    )
    with pytest.raises(ValueError, match="matched physical first record"):
        validate_materialized_fixtures(changed_values, changed_outcomes)


def test_public_projection_revalidates_nested_model_copy_bypass() -> None:
    p = public()
    wrong_sampling = p.observations.space.sampling.model_copy(update={"position_noise": 0.1})
    wrong_space = p.observations.space.model_copy(update={"sampling": wrong_sampling})
    wrong_observations = p.observations.model_copy(update={"space": wrong_space})
    bypass = p.model_copy(update={"observations": wrong_observations})
    with pytest.raises(ContractViolation):
        candidate_material(bypass)


def test_private_binding_revalidates_nested_construct_bypass() -> None:
    p = public()
    a = audit(p)
    invalid = D1Blueprint.model_construct(
        case_id="M03",
        coefficient_numerator=13,
        coefficient_denominator=7,
        mechanism="spring-plus-k-over-eight-force",
        initial_x=1.0,
        record_count=1,
        scales=(0.125, 0.25, 0.5),
        counts=(256, 1024),
    )
    bypass = a.model_copy(update={"blueprint": invalid})
    with pytest.raises(ContractViolation):
        validate_fixture_binding(p, bypass)
    with pytest.raises(ContractViolation):
        physical_identity(p, bypass)


def test_signed_zero_has_one_physical_identity_encoding() -> None:
    a = D1WorldSignature(mechanism="zero-rest-spring", coefficient_hex=(0.0).hex())
    b = D1WorldSignature(mechanism="zero-rest-spring", coefficient_hex=(-0.0).hex())
    assert message_sha256(a) == message_sha256(b)
    first = D1PhysicalHistory(action_sha256=(S,), recorded_x_hex=((0.0).hex(),))
    second = D1PhysicalHistory(action_sha256=(S,), recorded_x_hex=((-0.0).hex(),))
    assert message_sha256(first) == message_sha256(second)


def test_history_order_changes_history_but_never_clears_world_overlap() -> None:
    p = public()
    identity = physical_identity(p, audit(p))
    altered = D1PhysicalIdentity(
        coefficient_hex=identity.coefficient_hex,
        world_sha256=identity.world_sha256,
        history_sha256=S,
        action_sha256=tuple(reversed((S, T))),
        probe_sha256=identity.probe_sha256,
    )
    result = check_supplied_inventory(identity, inventory(altered))
    assert result.overlapping_world_entries == 1
    assert result.first_exact_construction_index is None


@pytest.mark.parametrize("case", ("M01", "M02", "M03", "M04"))
def test_reserved_comparison_excludes_every_coefficient_not_only_current_case(case: str) -> None:
    current = public("M01")
    other = public(case)
    identity = physical_identity(other, audit(other, case))
    # A different mechanism/world hash does not evade this deliberately broader reservation.
    changed = identity.model_copy(update={"world_sha256": S})
    retained = D1ExposureInventory(
        inventory_kind="reserved-comparison",
        entries=(D1ExposureEntry(source_evidence_sha256=S, identity=changed),),
    )
    result = check_supplied_inventory(physical_identity(current, audit(current, "M01")), retained)
    assert result.overlapping_world_entries == 0
    assert result.reserved_coefficient_entries == 1
    assert result.first_reserved_coefficient_index == 0
    assert result.conclusion == "overlap-in-supplied-inventory"


def test_inventory_boundary_revalidates_constructed_nested_values() -> None:
    p = public()
    identity = physical_identity(p, audit(p))
    invalid = identity.model_copy(update={"coefficient_hex": "not-a-hex"})
    retained = inventory().model_copy(
        update={
            "entries": (
                D1ExposureEntry.model_construct(source_evidence_sha256=S, identity=invalid),
            )
        }
    )
    with pytest.raises(ContractViolation):
        check_supplied_inventory(identity, retained)


@pytest.mark.parametrize("target", ("audit", "inventory"))
def test_hex_overflow_is_a_contained_raw_parse_rejection(target: str) -> None:
    p = public()
    a = audit(p)
    if target == "audit":
        data = a.model_dump(mode="json")
        data["coefficient_hex"] = "0x1p+9999"
        with pytest.raises(ContractViolation):
            parse_d1_audit(json.dumps(data).encode())
    else:
        data = inventory(physical_identity(p, a)).model_dump(mode="json")
        data["entries"][0]["identity"]["coefficient_hex"] = "0x1p+9999"
        with pytest.raises(ContractViolation):
            parse_d1_inventory(json.dumps(data).encode())


def partial_outcomes(
    supplied: tuple[tuple[str, D1PublicFixture, D1PrivateAudit], ...],
) -> D1FixtureOutcomes:
    by_case = {case: retained for case, _, retained in supplied}
    return D1FixtureOutcomes(
        outcomes=tuple(
            D1FixtureOutcome(
                blueprint=blueprint(case),
                status="materialized" if case in by_case else "unrun",
                failure_stage=None,
                failure_evidence_sha256=None,
                audit=by_case.get(case),
            )
            for case in CASE_IDS
        )
    )


def test_paired_join_uses_normalized_valid_nested_construct_material() -> None:
    matched, repeated = public(token="1"), public("D03", token="2")
    ma, da = audit(matched), audit(repeated, "D03")
    report = partial_outcomes((("M03", matched, ma), ("D03", repeated, da)))
    # Valid serialized nested dictionaries are allowed through revalidation;
    # subsequent joins must use normalized models, not these original mappings.
    nested = D1PublicFixture.model_construct(**matched.model_dump(mode="json"))
    validate_materialized_fixtures((nested, repeated), report)


@pytest.mark.parametrize("collision", ("run", "operation"))
def test_cross_fixture_ids_are_distinct_even_when_public_digests_differ(collision: str) -> None:
    matched, weak = public(token="1"), public("W03", token="2")
    data = weak.model_dump(mode="json")
    if collision == "run":
        data["observations"]["run_id"] = matched.observations.run_id
    else:
        data["observations"]["records"][0]["operation_id"] = matched.observations.records[
            0
        ].operation_id
    weak = parse_d1_public(json.dumps(data).encode())
    ma, wa = audit(matched), audit(weak, "W03")
    assert ma.public_sha256 != wa.public_sha256
    report = partial_outcomes((("M03", matched, ma), ("W03", weak, wa)))
    with pytest.raises(ValueError, match="distinct"):
        validate_materialized_fixtures((matched, weak), report)


def test_shared_future_join_survives_missing_matched_denominator() -> None:
    repeated, weak = public("D03", token="2"), public("W03", token="3")
    da, wa = audit(repeated, "D03"), audit(weak, "W03")
    data = wa.model_dump(mode="json")
    data["future_label"]["recorded_x_hex"] = (0.7).hex()
    wa = parse_d1_audit(json.dumps(data).encode())
    report = partial_outcomes((("D03", repeated, da), ("W03", weak, wa)))
    assert report.outcomes[2].status == "unrun"
    with pytest.raises(ValueError, match="same physical future answer"):
        validate_materialized_fixtures((repeated, weak), report)


def test_persisted_schema_has_exact_generated_bytes() -> None:
    path = Path(__file__).resolve().parents[1] / "contracts/calibration-fixture.schema.json"
    expected = (
        json.dumps(calibration_fixture_json_schema(), indent=2, sort_keys=True) + "\n"
    ).encode()
    assert path.read_bytes() == expected


def test_persisted_examples_validate_runtime_and_reject_both_negative_groups() -> None:
    path = Path(__file__).resolve().parents[1] / "contracts/calibration-fixture.examples.json"
    fixtures = json.loads(path.read_text())
    models = {
        model.__name__: model
        for model in (
            D1PublicFixture,
            D1PrivateAudit,
            D1FixtureOutcomes,
            D1ExposureInventory,
            D1ExposureFinding,
            D1OwnerReviewReference,
        )
    }
    for name, value in fixtures["valid"].items():
        assert models[name].model_validate_json(json.dumps(value)).model_dump(mode="json") == value
    for group in ("schema_negative", "runtime_negative"):
        for fixture in fixtures[group]:
            value = copy.deepcopy(fixtures["valid"][fixture["model"]])
            value[fixture["field"]] = fixture["value"]
            with pytest.raises(ValidationError):
                models[fixture["model"]].model_validate_json(json.dumps(value))
