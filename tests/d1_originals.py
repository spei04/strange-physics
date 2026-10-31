"""Fixed original-owner preparation for the same controlled D1 child.

Bootstrap must capture the supplied references before importing consumers. This
module establishes current object joins, not independent import/runtime trust.
It does not call a primitive, run a producer, retain S/A, or activate a recorder.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import BuiltinFunctionType, CodeType, FunctionType, MethodType, ModuleType

import d1_fixture_reference as fixture_module
import d1_prefix_evidence as reference_module
import endpoint_belief_reference as oracle_module
from d1_fixture_reference import SOURCE_PATHS, D1FixtureProducer, SourcePin
from d1_prefix_evidence import D1Reference
from endpoint_belief_reference import EndpointOracle

_METHOD_NAMES = ("position", "exp", "log", "circle_constant")
_CASES = ("M01", "M02", "M03", "M04", "D03", "F02", "F04", "W03")
_COUNTERS = ("series_values", "lookups", "exp_calls", "log_calls", "trig_calls", "machin_terms")
# j00..j21; j22 is the separately retained exact math.exp builtin.
_SLOTS = (
    (0, 0), (1, 0), (2, 0), (3, 0),
    (4, 1), (4, 2), (5, 1), (5, 2), (6, 1), (6, 2), (7, 1), (7, 2),
    (8, 1), (8, 2), (9, 1), (9, 2), (10, 1), (10, 2), (11, 1), (11, 2),
    (12, 2), (12, 3),
)


@dataclass(frozen=True, slots=True)
class OriginalAnchors:
    """References held by bootstrap, not an authentication token by construction."""

    oracle_module: ModuleType
    oracle_class: type[EndpointOracle]
    functions: tuple[FunctionType, FunctionType, FunctionType, FunctionType]
    codes: tuple[CodeType, CodeType, CodeType, CodeType]
    math_module: ModuleType
    emitter: BuiltinFunctionType


@dataclass(frozen=True, slots=True)
class PreparedOriginals:
    """Output-only live references; the continuation must stay in this child."""

    reference: D1Reference
    producer: D1FixtureProducer
    owners: tuple[EndpointOracle, ...]
    original_methods: tuple[MethodType, ...]
    emitter: BuiltinFunctionType


def _anchors(value: OriginalAnchors) -> None:
    if type(value) is not OriginalAnchors:
        raise ValueError("Exact original-anchor record required")
    if (
        type(value.oracle_module) is not ModuleType
        or value.oracle_module is not oracle_module
        or sys.modules.get("endpoint_belief_reference") is not oracle_module
        or "tests.endpoint_belief_reference" in sys.modules
        or value.oracle_module.__name__ != "endpoint_belief_reference"
        or value.oracle_class is not EndpointOracle
        or oracle_module.__dict__.get("EndpointOracle") is not value.oracle_class
        or fixture_module.__dict__.get("EndpointOracle") is not value.oracle_class
        or reference_module.__dict__.get("EndpointOracle") is not value.oracle_class
        or value.oracle_class.__module__ != "endpoint_belief_reference"
        or value.oracle_class.__qualname__ != "EndpointOracle"
        or any(name in value.oracle_class.__dict__ for name in ("__getattribute__", "__getattr__"))
    ):
        raise ValueError("Canonical oracle class/module/consumer aliases required")
    if type(value.functions) is not tuple or type(value.codes) is not tuple:
        raise ValueError("Exact ordered function/code tuples required")
    if len(value.functions) != 4 or len(value.codes) != 4:
        raise ValueError("Exactly four original definitions required")
    for name, function, code in zip(_METHOD_NAMES, value.functions, value.codes, strict=True):
        if (
            type(function) is not FunctionType
            or type(code) is not CodeType
            or value.oracle_class.__dict__.get(name) is not function
            or function.__code__ is not code
            or function.__globals__ is not value.oracle_module.__dict__
            or function.__module__ != "endpoint_belief_reference"
            or function.__qualname__ != "EndpointOracle." + name
            or function.__defaults__ is not None
            or function.__kwdefaults__ is not None
            or function.__closure__ is not None
        ):
            raise ValueError("Original function/code/layout changed")
    if (
        type(value.math_module) is not ModuleType
        or value.math_module is not math
        or sys.modules.get("math") is not math
        or value.math_module.__name__ != "math"
        or type(value.emitter) is not BuiltinFunctionType
        or value.math_module.__dict__.get("exp") is not value.emitter
        or value.emitter.__module__ != "math"
        or value.emitter.__name__ != "exp"
        or value.emitter.__qualname__ != "exp"
        or value.emitter.__self__ is not value.math_module
    ):
        raise ValueError("Exact original math.exp runtime builtin required")
    if (
        fixture_module.D1FixtureProducer is not D1FixtureProducer
        or reference_module.D1Reference is not D1Reference
        or sys.modules.get("d1_fixture_reference") is not fixture_module
        or sys.modules.get("d1_prefix_evidence") is not reference_module
        or any(name in sys.modules for name in ("tests.d1_fixture_reference", "tests.d1_prefix_evidence"))
    ):
        raise ValueError("Fixed canonical consumer classes required")


def _inputs(root: Path, commit: str, pins: tuple[SourcePin, ...]) -> None:
    if type(root) is not type(Path()) or not root.is_absolute() or ".." in root.parts:
        raise ValueError("Absolute declared checkout root required")
    if type(commit) is not str or re.fullmatch("[0-9a-f]{40}", commit) is None:
        raise ValueError("Exact declared source commit required")
    if type(pins) is not tuple or len(pins) != len(SOURCE_PATHS):
        raise ValueError("Exact seven producer source pins required")
    for path, pin in zip(SOURCE_PATHS, pins, strict=True):
        if (
            type(pin) is not SourcePin
            or type(pin.path) is not str
            or pin.path != path
            or type(pin.sha256) is not str
            or re.fullmatch("[0-9a-f]{64}", pin.sha256) is None
        ):
            raise ValueError("Ordered producer source-pin declarations required")


def _owners(reference: D1Reference, producer: D1FixtureProducer) -> tuple[EndpointOracle, ...]:
    if type(reference) is not D1Reference or type(producer) is not D1FixtureProducer:
        raise ValueError("Actual fixed reference and fixture producer required")
    if (
        type(reference.channels) is not dict
        or tuple(reference.channels) != ("strong", "weak", "future")
        or type(reference.arithmetic) is not dict
        or tuple(reference.arithmetic) != _CASES
        or producer.started
    ):
        raise ValueError("Actual ordered consumer owner containers required")
    owners = (
        producer.prepared_reference_owner,
        reference.channels["strong"], reference.channels["weak"], reference.channels["future"],
        *reference.arithmetic.values(),
        reference.constants_oracle,
    )
    for index, owner in enumerate(owners):
        if type(owner) is not EndpointOracle:
            raise ValueError("Every owner must be the exact captured oracle class")
        if any(owner is previous for previous in owners[:index]):
            raise ValueError("All thirteen oracle owners must be distinct")
        if type(owner.values) is not dict or owner.values or owner.pi is not None:
            raise ValueError("Fresh empty oracle cache and absent pi required")
        if any(owner.values is previous.values for previous in owners[:index]):
            raise ValueError("Oracle caches must have distinct identities")
        if any(type(getattr(owner, name)) is not int or getattr(owner, name) != 0 for name in _COUNTERS):
            raise ValueError("All six original oracle counters must be exact zero integers")
        instance_fields = vars(owner)
        if any(name in instance_fields for name in (*_METHOD_NAMES, "trig")):
            raise ValueError("Original owner methods must not be shadowed")
    return owners


def prepare_originals(
    anchors: OriginalAnchors, *, root: Path, commit: str, pins: tuple[SourcePin, ...]
) -> PreparedOriginals:
    """Called once by the same-child bootstrap after its protected preflight.

    No filesystem/source/runtime authentication happens here. The outer attempt
    owns consumption, partial-construction facts and first/supplemental failures;
    absence of a returned result is never permission to create replacement owners.
    """
    _inputs(root, commit, pins)
    _anchors(anchors)
    reference = D1Reference()
    producer = D1FixtureProducer(root, commit, pins)
    fixture_owner = producer.prepare_reference_owner()
    _anchors(anchors)
    owners = _owners(reference, producer)
    if owners[0] is not fixture_owner:
        raise ValueError("Producer changed its prepared fixture owner")
    methods: list[MethodType] = []
    for owner_index, definition_index in _SLOTS:
        method = getattr(owners[owner_index], _METHOD_NAMES[definition_index])
        if (
            type(method) is not MethodType
            or method.__self__ is not owners[owner_index]
            or method.__func__ is not anchors.functions[definition_index]
        ):
            raise ValueError("Actual original bound-method slot differs")
        methods.append(method)
    _anchors(anchors)
    final_owners = _owners(reference, producer)
    if any(left is not right for left, right in zip(owners, final_owners, strict=True)):
        raise ValueError("Actual owner identities changed during preparation")
    return PreparedOriginals(reference, producer, owners, tuple(methods), anchors.emitter)
