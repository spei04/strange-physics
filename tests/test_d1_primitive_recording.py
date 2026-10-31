"""Owned fake calls only; no reference arithmetic, physical model or service use."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import NoReturn

import pytest
from d1_primitive_recording import (
    MAX_BYTES,
    MAX_CALLS,
    Primitive,
    PrimitiveRecorder,
    RecorderStopped,
)
from endpoint_belief_reference import EndpointOracle

D = Decimal
KEY = (0.5, 1.0, 0.0, 1.0, 0.0, 0.0, 0.5)


@pytest.fixture(autouse=True)
def poison_real_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Real reference calls are forbidden in recorder tests")

    for name in ("position", "exp", "log", "circle_constant", "trig"):
        monkeypatch.setattr(EndpointOracle, name, deny)


class Sink:
    def __init__(self, fail_at: tuple[int, ...] = ()) -> None:
        self.raw: list[bytes] = []
        self.attempts: list[bytes] = []
        self.fail_at = fail_at
        self.error = PermissionError("owned fake sink failure")

    def __call__(self, raw: bytes) -> None:
        self.attempts.append(raw)
        if len(self.attempts) in self.fail_at:
            raise self.error
        self.raw.append(raw)


def make(sink: Sink | None = None, *, calls: int = 20, size: int = 100_000) -> PrimitiveRecorder:
    return PrimitiveRecorder(sink or Sink(), max_calls=calls, max_bytes=size)


def call(recorder: PrimitiveRecorder, call_id: str = "call-0") -> Decimal:
    return recorder.call(
        call_id=call_id,
        instance_id="constant-0",
        primitive="log",
        scope=("constants", "log-scale"),
        arguments=D("0.25"),
        invoke=lambda: D("-1.25"),
    )


@pytest.mark.parametrize(
    "primitive,arguments,result",
    [
        ("position", KEY, D("0.75")),
        ("exp", D("-2.50"), D("0.1250")),
        ("log", D("0.25"), D("-1.25")),
        ("circle_constant", None, D("3.125")),
        ("native_exp", -2.5, 0.125),
    ],
)
def test_exact_intent_then_return(
    primitive: Primitive, arguments: object, result: Decimal | float
) -> None:
    sink = Sink()
    recorder = make(sink)
    invoked = []

    def invoke() -> Decimal | float:
        assert len(sink.raw) == 1
        assert json.loads(sink.raw[0])["kind"] == "intent"
        invoked.append(True)
        return result

    actual = recorder.call(
        call_id="one",
        instance_id="owned",
        primitive=primitive,
        scope=("M03", "256", "node-0"),
        arguments=arguments,
        invoke=invoke,
    )
    assert actual is result and invoked == [True]
    view = recorder.snapshot()
    assert (view.reserved, view.invoked, view.returned, view.primitive_failed) == (1, 1, 1, 0)
    assert [x.event.kind for x in view.events] == ["intent", "returned"]
    assert all(x.delivery == "confirmed" for x in view.events)
    assert view.retained_bytes == sum(map(len, sink.raw))
    assert not view.stopped and not view.faults


@pytest.mark.parametrize("text", ["-0.000", "1.2300", "1e-256"])
def test_decimal_structure_survives_without_rounding(text: str) -> None:
    value = D(text)
    recorder = make()
    actual = recorder.call(
        call_id="decimal",
        instance_id="owned",
        primitive="log",
        scope=("constants",),
        arguments=value,
        invoke=lambda: value,
    )
    assert actual is value
    encoded = recorder.snapshot().events[-1].event.returned
    assert encoded is not None
    sign, digits, exponent = encoded.parts
    rebuilt = D((int(sign), tuple(map(int, digits)), int(exponent)))
    assert rebuilt.as_tuple() == value.as_tuple()
    intent = recorder.snapshot().events[0].event.intent
    assert intent is not None and intent.arguments == encoded


def test_binary64_negative_zero_and_complete_key_are_exact() -> None:
    recorder = make()
    key = (-0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.5)
    recorder.call(
        call_id="key",
        instance_id="owned",
        primitive="position",
        scope=("fixture",),
        arguments=key,
        invoke=lambda: D("0"),
    )
    intent = recorder.snapshot().events[0].event.intent
    assert intent is not None and intent.arguments.parts == tuple(x.hex() for x in key)
    assert intent.arguments.parts[0] == "-0x0.0p+0"


@pytest.mark.parametrize("failed_index", [0, 1, 2])
def test_partial_constants_preserve_every_return_before_later_fault(failed_index: int) -> None:
    recorder = make()
    error = ValueError("owned fake constant failure")
    calls = []
    values = (D("3.125"), D("1.75"), D("-1.25"))
    with pytest.raises(ValueError) as caught:
        for index, value in enumerate(values):

            def invoke(index: int = index, value: Decimal = value) -> Decimal:
                calls.append(index)
                if index == failed_index:
                    raise error
                return value

            recorder.call(
                call_id=f"constant-{index}",
                instance_id="constants",
                primitive="log",
                scope=("constants", str(index)),
                arguments=D("0.25"),
                invoke=invoke,
            )
    assert caught.value is error and recorder.first_exception is error
    view = recorder.snapshot()
    assert calls == list(range(failed_index + 1))
    assert (view.invoked, view.returned, view.primitive_failed) == (
        failed_index + 1,
        failed_index,
        1,
    )
    assert len([x for x in view.events if x.event.kind == "returned"]) == failed_index
    assert view.events[-1].event.fault == view.faults[0]
    assert view.faults[0].phase == "primitive"
    with pytest.raises(RecorderStopped):
        call(recorder, "later")
    assert recorder.snapshot() == view


def test_partial_exp_sequence_does_not_disappear_with_failed_normalization() -> None:
    recorder = make()
    error = ArithmeticError("owned fake normalization failure")
    for index in range(3):
        recorder.call(
            call_id=f"exp-{index}",
            instance_id="M03-arithmetic",
            primitive="exp",
            scope=("M03", "256", "0.25", str(index)),
            arguments=D("-1"),
            invoke=lambda: D("0.25"),
        )

    def fail() -> Decimal:
        raise error

    with pytest.raises(ArithmeticError) as caught:
        recorder.call(
            call_id="log-sum",
            instance_id="M03-arithmetic",
            primitive="log",
            scope=("M03", "256", "0.25", "normalizer"),
            arguments=D("0.75"),
            invoke=fail,
        )
    assert caught.value is error
    view = recorder.snapshot()
    assert (view.invoked, view.returned, view.primitive_failed) == (4, 3, 1)
    assert [
        x.event.intent.call_id
        for x in view.events
        if x.event.kind == "returned" and x.event.intent is not None
    ] == ["exp-0", "exp-1", "exp-2"]


def test_failed_intent_append_prevents_invocation_and_cannot_retry() -> None:
    sink = Sink((1,))
    recorder = make(sink)
    with pytest.raises(PermissionError) as caught:
        call(recorder)
    assert caught.value is sink.error
    view = recorder.snapshot()
    assert (view.invoked, view.returned, view.primitive_failed) == (0, 0, 0)
    assert view.events[0].delivery == "unknown" and view.faults[0].phase == "intent_sink"
    with pytest.raises(RecorderStopped):
        call(recorder)
    assert recorder.snapshot() == view and len(sink.attempts) == 2


def test_return_append_failure_is_not_a_primitive_failure() -> None:
    sink = Sink((2,))
    recorder = make(sink)
    with pytest.raises(PermissionError) as caught:
        call(recorder)
    assert caught.value is sink.error
    view = recorder.snapshot()
    assert (view.invoked, view.returned, view.primitive_failed) == (1, 1, 0)
    assert view.events[1].event.kind == "returned"
    assert view.events[1].event.returned is not None
    assert view.events[1].delivery == "unknown"
    assert view.faults[0].phase == "return_sink"
    assert [x.event.sequence for x in view.events] == [0, 1, 2]


@pytest.mark.parametrize("error", [ValueError("first"), KeyboardInterrupt(), SystemExit(7)])
def test_original_failure_survives_fault_sink_failure(error: BaseException) -> None:
    sink = Sink((2,))
    recorder = make(sink)

    def fail() -> Decimal:
        raise error

    with pytest.raises(type(error)) as caught:
        recorder.call(
            call_id="failed",
            instance_id="owned",
            primitive="log",
            scope=("constants",),
            arguments=D("1"),
            invoke=fail,
        )
    assert caught.value is error and recorder.first_exception is error
    view = recorder.snapshot()
    assert [x.phase for x in view.faults] == ["primitive", "fault_retention"]
    assert view.events[-1].delivery == "unknown"
    assert view.events[-1].event.fault == view.faults[0]
    assert view.primitive_failed == 1


@pytest.mark.parametrize(
    "primitive,argument",
    [
        ("position", list(KEY)),
        ("position", KEY[:-1]),
        ("position", (float("nan"), *KEY[1:])),
        ("exp", 1.0),
        ("exp", D("NaN")),
        ("exp", D("1e129")),
        ("exp", D("1e-257")),
        ("exp", D("1" * 121)),
        ("log", D("Infinity")),
        ("circle_constant", 0),
        ("native_exp", D("1")),
        ("native_exp", float("inf")),
    ],
)
def test_invalid_arguments_stop_before_invocation(primitive: Primitive, argument: object) -> None:
    recorder = make()
    with pytest.raises(ValueError):
        recorder.call(
            call_id="invalid",
            instance_id="owned",
            primitive=primitive,
            scope=("scope",),
            arguments=argument,
            invoke=lambda: D("1"),
        )
    view = recorder.snapshot()
    assert view.stopped and view.invoked == 0 and view.faults[0].phase == "preflight"
    assert all(x.event.kind != "intent" for x in view.events)


@pytest.mark.parametrize(
    "primitive,result",
    [
        ("exp", D("NaN")),
        ("exp", D("Infinity")),
        ("exp", D("1e129")),
        ("exp", D("1" * 121)),
        ("exp", 1.0),
        ("native_exp", D("1")),
        ("native_exp", float("inf")),
    ],
)
def test_invalid_return_retains_return_fact_without_claiming_value(
    primitive: Primitive, result: Decimal | float
) -> None:
    recorder = make()
    with pytest.raises(ValueError):
        recorder.call(
            call_id="invalid-return",
            instance_id="owned",
            primitive=primitive,
            scope=("scope",),
            arguments=1.0 if primitive == "native_exp" else D("1"),
            invoke=lambda: result,
        )
    view = recorder.snapshot()
    assert (view.invoked, view.returned, view.primitive_failed) == (1, 1, 0)
    returned = view.events[1].event.returned
    assert returned is not None and returned.kind == "unavailable"
    assert returned.parts == (type(result).__module__ + "." + type(result).__qualname__,)
    assert len(view.faults) == 1 and view.faults[0].phase == "return_encoding"


def test_encoding_fault_remains_first_when_both_later_sink_attempts_fail() -> None:
    recorder = make(Sink((2, 3)))
    with pytest.raises(ValueError) as caught:
        recorder.call(
            call_id="bad-return",
            instance_id="owned",
            primitive="exp",
            scope=("scope",),
            arguments=D("1"),
            invoke=lambda: D("NaN"),
        )
    assert recorder.first_exception is caught.value
    assert [x.phase for x in recorder.snapshot().faults] == [
        "return_encoding",
        "return_sink",
        "fault_retention",
    ]


@pytest.mark.parametrize(
    "call_id,instance,scope",
    [
        ("", "owned", ("scope",)),
        ("line\nbreak", "owned", ("scope",)),
        ("call", "", ("scope",)),
        ("call", "owned", ()),
        ("call", "owned", ("scope",) * 7),
        ("call", "owned", ("",)),
    ],
)
def test_bad_identity_or_scope_is_not_a_call(
    call_id: str, instance: str, scope: tuple[str, ...]
) -> None:
    recorder = make()
    with pytest.raises(ValueError):
        recorder.call(
            call_id=call_id,
            instance_id=instance,
            primitive="log",
            scope=scope,
            arguments=D("1"),
            invoke=lambda: D("0"),
        )
    assert recorder.snapshot().invoked == 0


def test_duplicate_call_id_is_consumed_without_second_primitive() -> None:
    recorder = make()
    call(recorder)
    with pytest.raises(ValueError, match="already consumed"):
        call(recorder)
    assert recorder.snapshot().invoked == 1 and recorder.snapshot().stopped


def test_call_allowance_is_cumulative() -> None:
    recorder = make(calls=1)
    call(recorder)
    with pytest.raises(ValueError, match="allowance"):
        call(recorder, "second")
    assert recorder.snapshot().reserved == recorder.snapshot().invoked == 1


def test_tiny_byte_allowance_cannot_invoke_or_fabricate_fault_delivery() -> None:
    sink = Sink()
    recorder = make(sink, size=1)
    with pytest.raises(ValueError, match="allowance"):
        call(recorder)
    view = recorder.snapshot()
    assert not sink.attempts and not view.events
    assert view.invoked == 0 and view.retained_bytes == 0
    assert [x.phase for x in view.faults] == ["intent_sink", "fault_retention"]


def test_return_byte_overflow_preserves_known_return_and_unknown_material() -> None:
    probe = make()
    call(probe)
    recorder = make(size=len(probe.snapshot().events[0].raw) + 1)
    with pytest.raises(ValueError, match="allowance"):
        call(recorder)
    view = recorder.snapshot()
    assert (view.invoked, view.returned, view.primitive_failed) == (1, 1, 0)
    assert len(view.events) == 1 and view.events[0].delivery == "confirmed"
    assert view.faults[0].phase == "return_sink"


@pytest.mark.parametrize(
    "calls,size",
    [
        (0, 1000),
        (MAX_CALLS + 1, 1000),
        (True, 1000),
        (1, 0),
        (1, MAX_BYTES + 1),
        (1, True),
    ],
)
def test_invalid_allowance_does_not_create_recorder(calls: int, size: int) -> None:
    with pytest.raises(ValueError):
        PrimitiveRecorder(Sink(), max_calls=calls, max_bytes=size)


def test_swallowed_nested_call_fault_still_stops_outer_completion() -> None:
    recorder = make()

    def invoke() -> Decimal:
        with pytest.raises(RecorderStopped):
            call(recorder, "nested")
        return D("1")

    with pytest.raises(RecorderStopped) as caught:
        recorder.call(
            call_id="outer",
            instance_id="owned",
            primitive="log",
            scope=("scope",),
            arguments=D("1"),
            invoke=invoke,
        )
    view = recorder.snapshot()
    assert view.invoked == 1 and view.returned == 1 and view.primitive_failed == 0
    assert view.faults[0].phase == "reentry" and view.stopped
    assert caught.value is recorder.first_exception


def test_later_consumer_rejection_does_not_erase_completed_primitive_return() -> None:
    recorder = make()
    with pytest.raises(ValueError, match="consumer"):
        value = call(recorder)
        assert value == D("-1.25")
        raise ValueError("owned downstream consumer rejection")
    view = recorder.snapshot()
    assert view.returned == 1 and view.events[-1].delivery == "confirmed"
    # The enclosing driver must record/stop on its own failure; it is not a primitive fault.
    assert not view.faults


def test_exception_stringification_cannot_replace_primary_fault() -> None:
    class OpaqueError(Exception):
        def __str__(self) -> str:
            raise RuntimeError("Exception stringification must not run")

    error = OpaqueError()
    recorder = make(Sink((2,)))

    def fail() -> Decimal:
        raise error

    with pytest.raises(OpaqueError) as caught:
        recorder.call(
            call_id="opaque",
            instance_id="owned",
            primitive="log",
            scope=("scope",),
            arguments=D("1"),
            invoke=fail,
        )
    assert caught.value is error and recorder.first_exception is error
    fault = recorder.snapshot().faults[0]
    assert fault.exception_type.endswith("OpaqueError") and fault.exception_type_complete
