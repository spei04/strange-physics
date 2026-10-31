"""Synthetic fixture-reference checks: every real oracle method is replaced."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from decimal import ROUND_UP, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import NoReturn

import d1_fixture_reference as producer
import endpoint_belief_reference as oracle_module
import pytest
from d1_fixture_reference import (
    ORACLE_SHA256,
    SOURCE_PATHS,
    D1FixtureProducer,
    FixtureBatch,
    PublicIds,
    Ratio,
    SourcePin,
    bind_attempt,
    candidate_materials,
    coefficients,
    fixed_plan,
    midpoint_cell,
    ratio,
    round_once,
    verify_rounding,
    verify_sources,
)
from endpoint_belief_reference import EndpointOracle, Key

import strange_physics.calibration_fixture_contracts as fixture_module
from strange_physics.calibration_fixture_contracts import (
    CASE_IDS,
    D1ExposureEntry,
    D1ExposureInventory,
    physical_identity,
)

D = Decimal
ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40  # Supplied test provenance, not a claimed Git attestation.


def pins() -> tuple[SourcePin, ...]:
    return tuple(
        SourcePin(path=name, sha256=hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        for name in SOURCE_PATHS
    )


def ids() -> tuple[PublicIds, ...]:
    # Synthetic IDs only. This test does not claim secret-independent issuance.
    return tuple(
        PublicIds(
            run_id=f"d1r-{i + 1:032x}",
            operations=tuple(f"d1o-{16 * (i + 1) + j:032x}" for j in range(2 if i == 4 else 1)),
        )
        for i in range(8)
    )


def inventories() -> tuple[D1ExposureInventory, ...]:
    return (
        D1ExposureInventory(inventory_kind="exposed-development", entries=()),
        D1ExposureInventory(inventory_kind="reserved-comparison", entries=()),
    )


@pytest.fixture(autouse=True)
def poison_real_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Real reference execution is forbidden in these synthetic tests")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)


@dataclass
class FakeReference:
    calls: list[Key] = field(default_factory=list)
    fail_at: int | None = None
    kind: str = "exception"


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeReference:
    state = FakeReference()

    def position(oracle: EndpointOracle, key: Key) -> Decimal:
        index = len(state.calls)
        state.calls.append(key)
        oracle.lookups += 1
        if state.fail_at == index and state.kind == "exception":
            raise RuntimeError("synthetic reference failure")
        # These are arbitrary legal values, never solutions of the D1 equations.
        value = D("0.09375") if key[3] == 0.125 else D("0.75") if key[6] == 0.5 else D("0.625")
        if state.fail_at == index:
            if state.kind == "midpoint":
                value = D("0.750000000000000055511151231257827021181583404541015625")
            elif state.kind == "nan":
                value = D("NaN")
            elif state.kind == "too_many_digits":
                value = D("0." + "1" * 121)
        if key in oracle.values:
            raise AssertionError("Producer repeated an already computed physical key")
        oracle.values[key] = value
        oracle.series_values += 1
        return value

    monkeypatch.setattr(EndpointOracle, "position", position)
    return state


def run() -> FixtureBatch:
    return D1FixtureProducer(ROOT, COMMIT, pins()).run(ids(), inventories())


def test_actual_source_bytes_and_loaded_locations_are_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = verify_sources(ROOT, COMMIT, pins())
    assert len(value.pins) == len(value.sizes) == 7
    assert value.pins[1].sha256 == ORACLE_SHA256
    assert all(0 < x <= producer.FILE_LIMIT for x in value.sizes)
    monkeypatch.setattr(fixture_module, "__file__", None)
    with pytest.raises(ValueError, match="Loaded production module has no source file"):
        verify_sources(ROOT, COMMIT, pins())


@pytest.mark.parametrize("kind", ("digest", "order", "missing", "commit", "loaded_location"))
def test_source_pin_mismatches_fail_before_any_reference(
    kind: str, monkeypatch: pytest.MonkeyPatch, fake: FakeReference
) -> None:
    actual = pins()
    commit = COMMIT
    if kind == "digest":
        actual = (actual[0].model_copy(update={"sha256": "0" * 64}), *actual[1:])
    elif kind == "order":
        actual = tuple(reversed(actual))
    elif kind == "missing":
        actual = actual[:-1]
    elif kind == "commit":
        commit = "a" * 39
    else:
        monkeypatch.setattr(oracle_module, "__file__", str(ROOT / "tests/not-the-oracle.py"))
    batch = D1FixtureProducer(ROOT, commit, actual).run(ids(), inventories())
    assert batch.first_fault is not None
    assert batch.outcomes.outcomes[0].status == "failed"
    assert [x.status for x in batch.outcomes.outcomes[1:]] == ["unrun"] * 7
    assert fake.calls == [] and batch.lookup_attempted == 0


def test_coefficient_proofs_enclose_exact_rationals_and_plan_uses_recorded_k() -> None:
    source = verify_sources(ROOT, COMMIT, pins())
    proofs = coefficients()
    plan = fixed_plan(source, proofs)
    assert [p.numerator for p in proofs] == [1, 5, 13, 27]
    assert len(plan.queries) == len({q.key for q in plan.queries}) == 13
    for proof in proofs:
        exact = Fraction(proof.numerator, 7)
        value = verify_rounding(
            proof.rounding, exact, exact, producer.coefficient_source(proof.numerator)
        )
        assert proof.rounding.lower.fraction() == proof.rounding.upper.fraction() == exact
        for query, spec in zip(plan.queries, producer.QUERY_SPECS, strict=True):
            if spec[1] == proof.numerator:
                assert query.key[0] == value.hex()
    for query in plan.queries:
        k, mass, anchor, initial, velocity, impulse, time = map(float.fromhex, query.key)
        assert Fraction(k) * Fraction(time) ** 2 / Fraction(mass) <= 4
        assert abs(initial - anchor) <= 1 and velocity == impulse == 0
        assert anchor == (0.125 if "-F" in query.name else 0.0)


@pytest.mark.parametrize(
    "kind", ("touch_lower", "touch_upper", "straddle", "reversed", "digest", "cell")
)
def test_rounding_needs_whole_strict_cell_and_actual_reference_identity(kind: str) -> None:
    value = 0.75
    low, high = midpoint_cell(value)
    center = Fraction(value)
    source = "b" * 64
    proof = round_once(value, center, center, source)
    lo, hi, expected = center, center, source
    if kind == "touch_lower":
        lo = low
    elif kind == "touch_upper":
        hi = high
    elif kind == "straddle":
        lo, hi = low - Fraction(1, 10**60), high + Fraction(1, 10**60)
    elif kind == "reversed":
        lo, hi = high, low
    elif kind == "digest":
        expected = "c" * 64
    else:
        proof = proof.model_copy(update={"upper_midpoint": ratio(high + 1)})
    with pytest.raises(ValueError, match="Strict rounding"):
        if kind in ("digest", "cell"):
            verify_rounding(proof, lo, hi, expected)
        else:
            round_once(value, lo, hi, source)


@pytest.mark.parametrize(
    "bad",
    (
        Ratio(numerator="2", denominator="4"),
        Ratio(numerator="1", denominator="0"),
        Ratio(numerator="01", denominator="2"),
    ),
)
def test_noncanonical_rational_evidence_is_rejected(bad: Ratio) -> None:
    with pytest.raises(ValueError):
        bad.fraction()


def test_complete_fake_batch_preserves_denominators_and_public_projection(
    fake: FakeReference,
) -> None:
    batch = run()
    assert batch.first_fault is None
    assert batch.source_rechecked
    assert (batch.lookup_attempted, batch.lookup_completed, batch.series_completed) == (13, 13, 13)
    assert batch.oracle_census == (13, 13, 0, 0, 0, 0, 13)
    assert len(fake.calls) == len(set(fake.calls)) == 13
    assert [x.status for x in batch.query_trace] == ["completed"] * 13
    assert [x.blueprint.case_id for x in batch.outcomes.outcomes] == list(CASE_IDS)
    assert [x.status for x in batch.outcomes.outcomes] == ["materialized"] * 8
    public = candidate_materials(batch)
    assert len(public) == 8 and sum(len(x.records) for x in public) == 9
    for bundle in public:
        encoded = bundle.model_dump_json()
        for private in ("coefficient", "rounding", "reference", "future", "M01", "F02", "force"):
            assert private not in encoded
        assert bundle.space.structure.anchors[0].position == (0.0, 0.0)
    assert len(batch.attempts) == 8
    assert sum(len(x.findings) for x in batch.attempts) == 16


def test_repeat_and_weak_share_actual_proofs_without_new_calls(fake: FakeReference) -> None:
    batch = run()
    matched, duplicate, weak = (batch.attempts[i].audit for i in (2, 4, 7))
    assert duplicate.training_labels == (matched.training_labels[0],) * 2
    assert matched.future_label == duplicate.future_label == weak.future_label
    assert matched.training_labels != weak.training_labels
    assert [(x.case, x.query_name, x.consumer_slots) for x in batch.reuse] == [
        ("D03", "train-M03", 2),
        ("D03", "future-M03", 1),
        ("W03", "future-M03", 1),
    ]
    public = candidate_materials(batch)
    assert public[2].records[0].operation_id != public[4].records[0].operation_id
    assert public[4].records[0].operation_id != public[4].records[1].operation_id
    assert len(fake.calls) == 13


def test_second_attempt_is_rejected_without_another_reference(fake: FakeReference) -> None:
    value = D1FixtureProducer(ROOT, COMMIT, pins())
    first = value.run(ids(), inventories())
    with pytest.raises(ValueError, match="consumed"):
        value.run(ids(), inventories())
    assert first.first_fault is None and len(fake.calls) == 13


@pytest.mark.parametrize(
    "kind,stage,reference_count,rounding_count",
    (
        ("exception", "reference", 4, 4),
        ("midpoint", "rounding", 5, 4),
        ("nan", "reference", 4, 4),
        ("too_many_digits", "reference", 4, 4),
    ),
)
def test_first_reference_or_rounding_failure_stops_and_retains_full_plan(
    kind: str, stage: str, reference_count: int, rounding_count: int, fake: FakeReference
) -> None:
    fake.fail_at, fake.kind = 4, kind
    batch = run()
    assert batch.first_fault is not None
    assert batch.first_fault.case == "M03" and batch.first_fault.stage == stage
    assert batch.first_fault.query == "train-M03"
    assert [x.status for x in batch.outcomes.outcomes] == ["materialized"] * 2 + ["failed"] + [
        "unrun"
    ] * 5
    assert len(batch.references) == reference_count and len(batch.roundings) == rounding_count
    assert len(fake.calls) == batch.lookup_attempted == 5
    assert batch.lookup_completed == (4 if kind == "exception" else 5)
    assert batch.query_trace[4].status == (
        "rounding_failed" if stage == "rounding" else "reference_failed"
    )
    assert [x.status for x in batch.query_trace[5:]] == ["unrun"] * 8
    if kind != "exception":
        assert batch.query_trace[4].returned_center is not None
    with pytest.raises(ValueError, match="Incomplete"):
        candidate_materials(batch)


@pytest.mark.parametrize(
    "kind", ("run_collision", "operation_collision", "slots", "constructed_id")
)
def test_invalid_id_plan_fails_without_numeric_calls(kind: str, fake: FakeReference) -> None:
    values = list(ids())
    if kind == "run_collision":
        values[1] = values[1].model_copy(update={"run_id": values[0].run_id})
    elif kind == "operation_collision":
        values[1] = values[1].model_copy(update={"operations": values[0].operations})
    elif kind == "slots":
        values[4] = values[4].model_copy(update={"operations": values[4].operations[:1]})
    else:
        values[0] = PublicIds.model_construct(run_id="D1-M01", operations=values[0].operations)
    batch = D1FixtureProducer(ROOT, COMMIT, pins()).run(tuple(values), inventories())
    assert batch.first_fault is not None and batch.first_fault.stage == "public_binding"
    assert fake.calls == []


@pytest.mark.parametrize("kind", ("missing", "reversed"))
def test_both_inventory_kinds_required_before_reference(kind: str, fake: FakeReference) -> None:
    values = inventories()[:1] if kind == "missing" else tuple(reversed(inventories()))
    batch = D1FixtureProducer(ROOT, COMMIT, pins()).run(ids(), values)
    assert batch.first_fault is not None and batch.first_fault.stage == "exposure"
    assert fake.calls == []


@pytest.mark.parametrize("kind", ("exposed-development", "reserved-comparison"))
def test_supplied_overlap_blocks_release_but_retains_private_findings(
    kind: str, fake: FakeReference
) -> None:
    baseline = run()
    attempt = baseline.attempts[0]
    identity = physical_identity(attempt.public, attempt.audit)
    inventory = D1ExposureInventory.model_validate(
        {
            "inventory_kind": kind,
            "entries": (D1ExposureEntry(source_evidence_sha256="e" * 64, identity=identity),),
        }
    )
    supplied = (
        (inventory, inventories()[1])
        if kind == "exposed-development"
        else (inventories()[0], inventory)
    )
    fake.calls.clear()
    batch = D1FixtureProducer(ROOT, COMMIT, pins()).run(ids(), supplied)
    assert batch.first_fault is not None and batch.first_fault.stage == "exposure"
    assert [x.status for x in batch.outcomes.outcomes] == ["failed"] + ["unrun"] * 7
    assert len(batch.attempts) == 1 and len(fake.calls) == 2
    assert any(x.conclusion == "overlap-in-supplied-inventory" for x in batch.attempts[0].findings)
    assert all(x.completeness == "not-established-by-this-contract" for x in batch.inventories)
    with pytest.raises(ValueError):
        candidate_materials(batch)


@pytest.mark.parametrize(
    "kind", ("center", "query", "reference_source", "rounding_source", "audit", "finding")
)
def test_retained_proofs_bind_material_not_just_matching_digest_claims(
    kind: str, fake: FakeReference
) -> None:
    batch = run()
    assert batch.plan is not None and batch.sources is not None
    refs, rounds = list(batch.references), list(batch.roundings)
    attempt = batch.attempts[0]
    if kind == "center":
        refs[0] = refs[0].model_copy(update={"center": "0.5"})
    elif kind == "query":
        refs[0] = refs[0].model_copy(update={"query": batch.plan.queries[1]})
    elif kind == "reference_source":
        refs[0] = refs[0].model_copy(update={"source_sha256": "f" * 64})
    elif kind == "rounding_source":
        rounds[0] = rounds[0].model_copy(update={"source_sha256": "f" * 64})
    elif kind == "audit":
        attempt = replace(
            attempt, audit=attempt.audit.model_copy(update={"public_sha256": "f" * 64})
        )
    else:
        attempt = replace(attempt, findings=(attempt.findings[0], attempt.findings[0]))
    with pytest.raises((ValueError, KeyError)):
        bind_attempt(
            attempt, batch.plan, batch.sources, tuple(refs), tuple(rounds), batch.inventories
        )


def test_source_change_at_closeout_preserves_all_observed_work(
    fake: FakeReference, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = producer.verify_sources
    calls = 0

    def check(root: Path, commit: str, supplied: tuple[SourcePin, ...]) -> producer.Sources:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("synthetic source mutation")
        return original(root, commit, supplied)

    monkeypatch.setattr(producer, "verify_sources", check)
    batch = run()
    assert batch.first_fault is not None and not batch.source_rechecked
    assert batch.first_fault.query is None
    assert len(batch.references) == len(batch.roundings) == 13 and len(batch.attempts) == 8
    assert len(fake.calls) == 13 and batch.oracle_census == (13, 13, 0, 0, 0, 0, 13)
    assert [x.status for x in batch.outcomes.outcomes] == ["materialized"] * 7 + ["failed"]
    with pytest.raises(ValueError):
        candidate_materials(batch)


def test_hostile_ambient_context_does_not_change_fake_material(fake: FakeReference) -> None:
    normal = run()
    fake.calls.clear()
    with localcontext() as context:
        context.prec, context.rounding = 3, ROUND_UP
        context.Emin, context.Emax = -9, 9
        hostile = run()
    assert normal.first_fault is hostile.first_fault is None
    assert normal.references == hostile.references and normal.roundings == hostile.roundings
    assert normal.outcomes == hostile.outcomes


def test_outcome_audit_cannot_be_substituted_after_binding(fake: FakeReference) -> None:
    batch = run()
    outcome = batch.outcomes.outcomes[0]
    assert outcome.audit is not None
    changed = outcome.audit.model_copy(update={"source_commit": "b" * 40})
    bad_outcome = outcome.model_copy(update={"audit": changed})
    bad = replace(
        batch,
        outcomes=batch.outcomes.model_copy(
            update={
                "outcomes": (bad_outcome, *batch.outcomes.outcomes[1:]),
            }
        ),
    )
    with pytest.raises(ValueError, match="exact private audit"):
        candidate_materials(bad)


@pytest.mark.parametrize("replacement", (None, "0.5"))
def test_completed_trace_center_must_match_reference(
    replacement: str | None, fake: FakeReference
) -> None:
    batch = run()
    changed = batch.query_trace[0].model_copy(update={"returned_center": replacement})
    bad = replace(batch, query_trace=(changed, *batch.query_trace[1:]))
    with pytest.raises(ValueError, match="actual reference center"):
        candidate_materials(bad)
    assert len(fake.calls) == 13
