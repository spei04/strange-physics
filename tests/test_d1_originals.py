"""Source-only authored original-owner cases; no primitive is an identity probe."""

from __future__ import annotations

import math
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import BuiltinFunctionType, FunctionType, ModuleType
from typing import Any, NoReturn

import d1_fixture_reference as fixture_module
import d1_prefix_evidence as reference_module
import endpoint_belief_reference as oracle_module
import pytest
from d1_fixture_reference import D1FixtureProducer, SourcePin
from d1_originals import OriginalAnchors, PreparedOriginals, prepare_originals
from d1_prefix_evidence import D1Reference
from endpoint_belief_reference import EndpointOracle

ROOT = Path("/synthetic/owned/d1")
COMMIT = "a" * 40
PATHS = (
    "docs/research/RA_N03_CALIBRATION_SLICE.md",
    "tests/endpoint_belief_reference.py",
    "tests/d1_fixture_reference.py",
    "src/strange_physics/calibration_fixture_contracts.py",
    "src/strange_physics/contracts.py",
    "src/strange_physics/bounded_json.py",
    "src/strange_physics/research_contracts.py",
)


def anchors() -> OriginalAnchors:
    values = tuple(
        vars(EndpointOracle)[name] for name in ("position", "exp", "log", "circle_constant")
    )
    assert len(values) == 4 and all(type(value) is FunctionType for value in values)
    emitter = vars(math)["exp"]
    assert type(emitter) is BuiltinFunctionType
    return OriginalAnchors(
        oracle_module,
        EndpointOracle,
        (values[0], values[1], values[2], values[3]),
        (values[0].__code__, values[1].__code__, values[2].__code__, values[3].__code__),
        math,
        emitter,
    )


def pins() -> tuple[SourcePin, ...]:
    return tuple(SourcePin(path=path, sha256="b" * 64) for path in PATHS)


def prepare(value: OriginalAnchors | None = None) -> PreparedOriginals:
    return prepare_originals(
        anchors() if value is None else value, root=ROOT, commit=COMMIT, pins=pins()
    )


def denied(*args: object, **kwargs: object) -> NoReturn:
    raise AssertionError("Producer/numerical work forbidden during original preparation")


@pytest.fixture(autouse=True)
def no_producer_or_reference_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep original oracle code intact for identity checks. The bounded engineering
    # collector separately denies entry to all five defining oracle code objects.
    monkeypatch.setattr(D1FixtureProducer, "run", denied)
    for name in ("coefficients", "fixed_plan", "verify_sources", "_inventories"):
        monkeypatch.setattr(fixture_module, name, denied)
    for name in ("constants", "normalize", "_endpoint", "training", "future"):
        monkeypatch.setattr(D1Reference, name, denied)


def test_actual_consumers_own_all_thirteen_and_fixed_original_slots() -> None:
    saved = anchors()
    result = prepare(saved)
    assert result.producer.prepared_reference_owner is result.owners[0]
    assert all(
        a is b for a, b in zip(result.owners[1:4], result.reference.channels.values(), strict=True)
    )
    assert all(
        a is b
        for a, b in zip(result.owners[4:12], result.reference.arithmetic.values(), strict=True)
    )
    assert result.owners[12] is result.reference.constants_oracle
    assert len({id(owner) for owner in result.owners}) == 13
    assert len({id(owner.values) for owner in result.owners}) == 13
    expected = (
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 1),
        (4, 2),
        (5, 1),
        (5, 2),
        (6, 1),
        (6, 2),
        (7, 1),
        (7, 2),
        (8, 1),
        (8, 2),
        (9, 1),
        (9, 2),
        (10, 1),
        (10, 2),
        (11, 1),
        (11, 2),
        (12, 2),
        (12, 3),
    )
    assert len(result.original_methods) == 22
    for method, (owner_index, definition) in zip(result.original_methods, expected, strict=True):
        assert (
            method.__self__ is result.owners[owner_index]
            and method.__func__ is saved.functions[definition]
        )
    assert result.emitter is saved.emitter and result.emitter is math.exp
    for owner in result.owners:
        assert (
            owner.lookups,
            owner.series_values,
            owner.exp_calls,
            owner.log_calls,
            owner.trig_calls,
            owner.machin_terms,
        ) == (0, 0, 0, 0, 0, 0)
        assert owner.values == {} and owner.pi is None


@pytest.mark.parametrize(
    "kind",
    (
        "record",
        "function-list",
        "function-count",
        "code-list",
        "code-count",
        "code",
        "class",
        "module",
        "math-module",
        "emitter",
    ),
    ids=(
        "record",
        "function-list",
        "function-count",
        "code-list",
        "code-count",
        "code",
        "class",
        "module",
        "math-module",
        "emitter",
    ),
)
def test_bad_anchors_reject_before_construction(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    value = anchors()
    malformed: Any = value
    if kind == "record":
        malformed = vars(oracle_module)
    elif kind == "function-list":
        object.__setattr__(value, "functions", list(value.functions))
    elif kind == "function-count":
        object.__setattr__(value, "functions", value.functions[:3])
    elif kind == "code-list":
        object.__setattr__(value, "codes", list(value.codes))
    elif kind == "code-count":
        object.__setattr__(value, "codes", value.codes[:3])
    elif kind == "code":
        object.__setattr__(value, "codes", (denied.__code__, *value.codes[1:]))
    elif kind == "class":
        object.__setattr__(value, "oracle_class", type("Other", (EndpointOracle,), {}))
    elif kind == "module":
        object.__setattr__(value, "oracle_module", ModuleType("endpoint_belief_reference"))
    elif kind == "math-module":
        object.__setattr__(value, "math_module", ModuleType("math"))
    else:
        object.__setattr__(value, "emitter", math.expm1)
    with monkeypatch.context() as scoped:
        scoped.setattr(D1Reference, "__init__", denied)
        with pytest.raises(ValueError):
            prepare(malformed)


@pytest.mark.parametrize(
    "kind",
    ("root", "commit", "count", "order", "digest"),
    ids=("root", "commit", "count", "order", "digest"),
)
def test_bad_producer_declarations_precede_construction(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, commit, source_pins = ROOT, COMMIT, pins()
    if kind == "root":
        root = Path("relative")
    elif kind == "commit":
        commit = "a" * 39
    elif kind == "count":
        source_pins = source_pins[:-1]
    elif kind == "order":
        source_pins = tuple(reversed(source_pins))
    else:
        source_pins = (source_pins[0].model_copy(update={"sha256": True}), *source_pins[1:])
    with monkeypatch.context() as scoped:
        scoped.setattr(D1Reference, "__init__", denied)
        with pytest.raises(ValueError):
            prepare_originals(anchors(), root=root, commit=commit, pins=source_pins)


@pytest.mark.parametrize(
    "kind",
    ("fixture-alias", "reference-alias", "producer-class", "reference-class", "namespace"),
    ids=("fixture-alias", "reference-alias", "producer-class", "reference-class", "namespace"),
)
def test_changed_consumers_reject_before_construction(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    saved = anchors()
    with monkeypatch.context() as scoped:
        scoped.setattr(D1Reference, "__init__", denied)
        if kind == "fixture-alias":
            scoped.setattr(fixture_module, "EndpointOracle", object())
        elif kind == "reference-alias":
            scoped.setattr(reference_module, "EndpointOracle", object())
        elif kind == "producer-class":
            scoped.setattr(fixture_module, "D1FixtureProducer", object())
        elif kind == "reference-class":
            scoped.setattr(reference_module, "D1Reference", object())
        else:
            scoped.setitem(sys.modules, "tests.endpoint_belief_reference", oracle_module)
        with pytest.raises(ValueError):
            prepare(saved)


@pytest.mark.parametrize(
    "kind",
    (
        "duplicate",
        "shared-cache",
        "bool-counter",
        "used-cache",
        "pi",
        "shadow",
        "wrong-owner",
        "channel-order",
        "case-order",
    ),
    ids=(
        "duplicate",
        "shared-cache",
        "bool-counter",
        "used-cache",
        "pi",
        "shadow",
        "wrong-owner",
        "channel-order",
        "case-order",
    ),
)
def test_actual_owner_container_mutations_fail(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    original_init = D1Reference.__init__

    def initialize(reference: D1Reference) -> None:
        original_init(reference)
        strong, weak = reference.channels["strong"], reference.channels["weak"]
        if kind == "duplicate":
            reference.channels["weak"] = strong
        elif kind == "shared-cache":
            weak.values = strong.values
        elif kind == "bool-counter":
            object.__setattr__(strong, "lookups", False)
        elif kind == "used-cache":
            object.__setattr__(strong, "values", {"untrusted": None})
        elif kind == "pi":
            object.__setattr__(strong, "pi", 0)
        elif kind == "shadow":
            object.__setattr__(strong, "position", denied)
        elif kind == "wrong-owner":
            reference.channels["weak"] = type("Other", (EndpointOracle,), {})()
        elif kind == "channel-order":
            reference.channels = dict(reversed(tuple(reference.channels.items())))
        else:
            reference.arithmetic = dict(reversed(tuple(reference.arithmetic.items())))

    with monkeypatch.context() as scoped:
        scoped.setattr(D1Reference, "__init__", initialize)
        with pytest.raises(ValueError):
            prepare()


@pytest.mark.parametrize("kind", ("code", "emitter", "alias"), ids=("code", "emitter", "alias"))
def test_definitions_rechecked_after_all_owners_created(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    saved = anchors()
    original_prepare = D1FixtureProducer.prepare_reference_owner
    created: list[EndpointOracle] = []
    with monkeypatch.context() as scoped:

        def prepare_owner(producer: D1FixtureProducer) -> EndpointOracle:
            owner = original_prepare(producer)
            created.append(owner)
            if kind == "code":
                scoped.setattr(saved.functions[0], "__code__", denied.__code__)
            elif kind == "emitter":
                scoped.setattr(math, "exp", math.expm1)
            else:
                scoped.setattr(fixture_module, "EndpointOracle", object())
            return owner

        scoped.setattr(D1FixtureProducer, "prepare_reference_owner", prepare_owner)
        with pytest.raises(ValueError):
            prepare(saved)
    assert len(created) == 1 and created[0].lookups == 0 and created[0].values == {}


@pytest.mark.parametrize("kind", ("anchors", "output"), ids=("anchors", "output"))
def test_outputs_are_frozen_but_not_authority(kind: str) -> None:
    value: Any = anchors() if kind == "anchors" else prepare()
    with pytest.raises(FrozenInstanceError):
        value.emitter = math.expm1


def test_constructor_failure_propagates_exact_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = OSError("synthetic constructor failure")
    called: list[str] = []

    def fail(reference: D1Reference) -> NoReturn:
        called.append("reference")
        raise failure

    with monkeypatch.context() as scoped:
        scoped.setattr(D1Reference, "__init__", fail)
        scoped.setattr(D1FixtureProducer, "__init__", denied)
        with pytest.raises(OSError) as raised:
            prepare()
    assert raised.value is failure and called == ["reference"]


@pytest.mark.parametrize(
    "kind",
    (
        "oracle-counter",
        "reference-field",
        "producer-field",
        "oracle-hook",
        "reference-hook",
        "producer-hook",
    ),
    ids=(
        "oracle-counter",
        "reference-field",
        "producer-field",
        "oracle-hook",
        "reference-hook",
        "producer-hook",
    ),
)
def test_postconstruction_descriptor_and_hook_never_execute(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    saved = anchors()
    original_prepare = D1FixtureProducer.prepare_reference_owner
    getter_calls: list[str] = []
    created: list[EndpointOracle] = []

    def getter(value: object) -> object:
        getter_calls.append("descriptor")
        raise AssertionError("Freshness validation must not evaluate a substituted descriptor")

    def lookup(value: object, name: str) -> object:
        getter_calls.append("hook")
        raise AssertionError("Freshness validation must not evaluate a substituted lookup hook")

    with monkeypatch.context() as scoped:

        def prepare_owner(producer: D1FixtureProducer) -> EndpointOracle:
            owner = original_prepare(producer)
            created.append(owner)
            if kind == "oracle-counter":
                scoped.setattr(EndpointOracle, "lookups", property(getter))
            elif kind == "reference-field":
                scoped.setattr(D1Reference, "channels", property(getter), raising=False)
            elif kind == "producer-field":
                scoped.setattr(
                    D1FixtureProducer, "_prepared_reference_owner", property(getter), raising=False
                )
            elif kind == "oracle-hook":
                scoped.setattr(EndpointOracle, "__getattribute__", lookup)
            elif kind == "reference-hook":
                scoped.setattr(D1Reference, "__getattribute__", lookup)
            else:
                scoped.setattr(D1FixtureProducer, "__getattribute__", lookup)
            return owner

        scoped.setattr(D1FixtureProducer, "prepare_reference_owner", prepare_owner)
        with pytest.raises(ValueError):
            prepare(saved)
    assert len(created) == 1 and getter_calls == []
    assert created[0].values == {} and created[0].lookups == 0
