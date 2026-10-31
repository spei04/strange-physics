"""Emit D1 schema and structural examples; no endpoint/reference generation."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from strange_physics.calibration_fixture_contracts import (
    CASE_IDS,
    PROTOCOL_SHA256,
    D1Blueprint,
    D1ExposureInventory,
    D1FixtureOutcome,
    D1FixtureOutcomes,
    D1LabelClaim,
    D1OwnerReviewReference,
    D1PrivateAudit,
    calibration_fixture_json_schema,
    check_supplied_inventory,
    parse_d1_public,
    physical_identity,
)
from strange_physics.research_contracts import message_sha256


def structural_examples() -> dict[str, Any]:
    """Labels are arbitrary legal placeholders, never reference-generated D1 outcomes."""
    rows = (
        (1, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        (5, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        (13, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        (27, "zero-rest-spring", 1.0, 1, (0.125, 0.25, 0.5)),
        (13, "zero-rest-spring", 1.0, 2, (0.25,)),
        (5, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
        (27, "spring-plus-k-over-eight-force", 1.0, 1, (0.125, 0.25, 0.5)),
        (13, "zero-rest-spring", 0.125, 1, (0.25,)),
    )
    blueprints = tuple(
        D1Blueprint.model_validate(
            dict(
                case_id=case,
                coefficient_numerator=row[0],
                mechanism=row[1],
                initial_x=row[2],
                record_count=row[3],
                scales=row[4],
            )
        )
        for case, row in zip(CASE_IDS, rows, strict=True)
    )
    public = parse_d1_public(
        json.dumps(
            {
                "observations": {
                    "run_id": "d1r-" + "1" * 32,
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
                        "budget": 1,
                        "calibration_experiments": 0,
                    },
                    "records": [
                        {
                            "operation_id": "d1o-" + "2" * 32,
                            "index": 0,
                            "status": "completed",
                            "experiment": {
                                "particles": [
                                    {
                                        "id": "p0",
                                        "position": [1.0, 0.0],
                                        "velocity": [0.0, 0.0],
                                        "mass": 1.0,
                                    }
                                ],
                                "impulse": {"particle_id": "p0", "vector": [0.0, 0.0]},
                            },
                            "trajectory": {
                                "frames": [
                                    {
                                        "time": 0.0,
                                        "positions": [[1.0, 0.0]],
                                        "velocities": [[0.0, 0.0]],
                                    },
                                    {
                                        "time": 0.5,
                                        "positions": [[0.75, 0.0]],
                                        "velocities": [[0.0, 0.0]],
                                    },
                                ]
                            },
                        }
                    ],
                },
            }
        ).encode("utf-8")
    )
    label = D1LabelClaim(
        recorded_x_hex=(0.75).hex(),
        reference_evidence_sha256="a" * 64,
        rounding_evidence_sha256="b" * 64,
    )
    audit = D1PrivateAudit(
        source_commit="c" * 40,
        blueprint=blueprints[2],
        public_sha256=message_sha256(public),
        coefficient_hex=(13 / 7).hex(),
        training_labels=(label,),
        future_label=D1LabelClaim(
            recorded_x_hex=(0.625).hex(),
            reference_evidence_sha256="a" * 64,
            rounding_evidence_sha256="b" * 64,
        ),
    )
    outcomes = D1FixtureOutcomes(
        outcomes=tuple(
            D1FixtureOutcome(
                blueprint=blueprint,
                status="unrun",
                failure_stage=None,
                failure_evidence_sha256=None,
                audit=None,
            )
            for blueprint in blueprints
        )
    )
    inventory = D1ExposureInventory(inventory_kind="exposed-development", entries=())
    finding = check_supplied_inventory(physical_identity(public, audit), inventory)
    review = D1OwnerReviewReference(
        development_inventory_sha256=message_sha256(inventory),
        comparison_inventory_sha256="d" * 64,
        fixture_outcomes_sha256=message_sha256(outcomes),
        review_evidence_sha256="e" * 64,
        disposition="pending",
    )
    valid = {
        type(model).__name__: model.model_dump(mode="json")
        for model in (public, audit, outcomes, inventory, finding, review)
    }
    wrong_provenance = copy.deepcopy(valid["D1PublicFixture"]["observations"])
    wrong_provenance["engine_version"] = "synthetic-force-F02"
    return {
        "description": "Structural placeholders only; no true D1 labels or exposure acceptance.",
        "valid": valid,
        "schema_negative": [
            {"model": "D1PublicFixture", "field": "schema_version", "value": "wrong"},
            {"model": "D1PrivateAudit", "field": "protocol_sha256", "value": "a" * 64},
            {"model": "D1PrivateAudit", "field": "coefficient_hex", "value": "x" * 33},
            {"model": "D1FixtureOutcomes", "field": "outcomes", "value": []},
            {"model": "D1ExposureInventory", "field": "completeness", "value": "complete"},
            {"model": "D1ExposureFinding", "field": "conclusion", "value": "certified-disjoint"},
            {"model": "D1OwnerReviewReference", "field": "execution_authorized", "value": True},
        ],
        "runtime_negative": [
            {"model": "D1PublicFixture", "field": "observations", "value": wrong_provenance},
            {"model": "D1PrivateAudit", "field": "coefficient_hex", "value": "0x1p+9999"},
            {
                "model": "D1PrivateAudit",
                "field": "training_labels",
                "value": [label.model_dump(mode="json")] * 2,
            },
            {
                "model": "D1FixtureOutcomes",
                "field": "outcomes",
                "value": list(reversed(valid["D1FixtureOutcomes"]["outcomes"])),
            },
            {"model": "D1ExposureFinding", "field": "overlapping_world_entries", "value": 1},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "contracts"
    )
    args = parser.parse_args()
    output: Path = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("calibration-fixture.schema.json", calibration_fixture_json_schema()),
        ("calibration-fixture.examples.json", structural_examples()),
    ):
        (output / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
