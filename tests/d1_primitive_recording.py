"""One-call D1 primitive recording; no scientific implementation or file writer.

Sink success is a caller-supplied retention promise, not proof of durable storage.
The driver must bind the actual callable, source, instance and append-only sink.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from typing import Literal

Primitive = Literal["position", "exp", "log", "circle_constant", "native_exp"]
Phase = Literal["preflight", "intent_sink", "primitive", "return_encoding", "return_sink"]
MAX_CALLS = 55_100  # 29,500 reference calls plus 25,600 native emitted conversions.
MAX_BYTES = 64 * 1024**2  # Domain ceiling, not a reservation or a proven codec fit.
EVENT_BYTES = 4096
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,95}\Z")


@dataclass(frozen=True)
class Value:
    """Exact bounded representation; Decimal quantum and signed zero survive."""

    kind: Literal["decimal", "binary64", "position_key", "none", "unavailable"]
    parts: tuple[str, ...]


@dataclass(frozen=True)
class Intent:
    ordinal: int
    call_id: str
    instance_id: str
    primitive: Primitive
    scope: tuple[str, ...]
    arguments: Value


@dataclass(frozen=True)
class Fault:
    ordinal: int
    phase: str
    exception_type: str
    exception_type_complete: bool
    call_id: str | None


@dataclass(frozen=True)
class Event:
    sequence: int
    kind: Literal["intent", "returned", "failed"]
    intent: Intent | None
    returned: Value | None = None
    fault: Fault | None = None


@dataclass(frozen=True)
class RetainedEvent:
    event: Event
    raw: bytes
    delivery: Literal["confirmed", "unknown"]


@dataclass(frozen=True)
class Snapshot:
    reserved: int
    invoked: int
    returned: int
    primitive_failed: int
    retained_bytes: int
    stopped: bool
    events: tuple[RetainedEvent, ...]
    faults: tuple[Fault, ...]


class RecorderStopped(ValueError):
    """The recorder cannot consume another call after any failure."""


def _token(value: object) -> str:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        raise ValueError("A bounded opaque identity token is required")
    return value


def _decimal(value: object) -> Value:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("A finite exact Decimal return or argument is required")
    sign, digits, exponent = value.as_tuple()
    if not isinstance(exponent, int) or not -256 <= exponent <= 128:
        raise ValueError("Decimal exponent outside the retained domain")
    if len(digits) > 120:
        raise ValueError("Decimal coefficient outside the retained domain")
    return Value("decimal", (str(sign), "".join(map(str, digits)), str(exponent)))


def _binary(value: object) -> str:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("A finite exact binary64 return or argument is required")
    return value.hex()


def _arguments(primitive: Primitive, value: object) -> Value:
    if primitive == "position":
        if type(value) is not tuple or len(value) != 7:
            raise ValueError("A complete seven-component position key is required")
        return Value("position_key", tuple(_binary(item) for item in value))
    if primitive in ("exp", "log"):
        return _decimal(value)
    if primitive == "circle_constant":
        if value is not None:
            raise ValueError("The circle constant has no argument")
        return Value("none", ())
    if primitive == "native_exp":
        return Value("binary64", (_binary(value),))
    raise ValueError("Unsupported D1 primitive")


class PrimitiveRecorder:
    """Single-threaded, bounded, fail-stop facade around an already owned callable.

    append(raw) must return only after retaining this exact complete event. A raised
    append has unknown delivery, even when some bytes may have reached its sink.
    This class never retries it. No callable, instance or execution authenticity
    follows from the declared labels alone.
    """

    def __init__(self, append: Callable[[bytes], None], *, max_calls: int, max_bytes: int) -> None:
        if type(max_calls) is not int or not 1 <= max_calls <= MAX_CALLS:
            raise ValueError("Explicit bounded call allowance required")
        if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES:
            raise ValueError("Explicit bounded retained-byte allowance required")
        if not callable(append):
            raise ValueError("A synchronous retention sink is required")
        self._append = append
        self._max_calls, self._max_bytes = max_calls, max_bytes
        self._ids: set[str] = set()
        self._events: list[RetainedEvent] = []
        self._faults: list[Fault] = []
        self._reserved = self._invoked = self._returned = self._primitive_failed = 0
        self._bytes = 0
        self._active = self._stopped = False
        self.first_exception: BaseException | None = None

    def snapshot(self) -> Snapshot:
        return Snapshot(
            self._reserved,
            self._invoked,
            self._returned,
            self._primitive_failed,
            self._bytes,
            self._stopped,
            tuple(self._events),
            tuple(self._faults),
        )

    def _remember(self, phase: str, error: BaseException, intent: Intent | None) -> Fault:
        self._stopped = True
        if self.first_exception is None:
            self.first_exception = error
        # Do not call arbitrary exception __str__, serialize args or copy a traceback.
        name = type(error).__module__ + "." + type(error).__qualname__
        fault = Fault(
            len(self._faults),
            phase,
            name[:192],
            len(name) <= 192,
            intent.call_id if intent else None,
        )
        self._faults.append(fault)
        return fault

    def _emit(self, event: Event) -> None:
        raw = (json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(raw) > EVENT_BYTES or self._bytes + len(raw) > self._max_bytes:
            raise ValueError("Retained event byte allowance exhausted")
        index = len(self._events)
        self._events.append(RetainedEvent(event, raw, "unknown"))
        self._bytes += len(raw)
        self._append(raw)
        self._events[index] = replace(self._events[index], delivery="confirmed")

    def _abort(self, phase: str, error: BaseException, intent: Intent | None) -> None:
        fault = (
            self._faults[0]
            if self.first_exception is error
            else self._remember(phase, error, intent)
        )
        try:
            self._emit(Event(len(self._events), "failed", intent, fault=fault))
        except BaseException as supplemental:
            self._remember("fault_retention", supplemental, intent)

    def call[T: Decimal | float](
        self,
        *,
        call_id: str,
        instance_id: str,
        primitive: Primitive,
        scope: tuple[str, ...],
        arguments: object,
        invoke: Callable[[], T],
    ) -> T:
        if self._stopped:
            raise RecorderStopped("A prior failure consumed this recorder")
        if self._active:
            error = RecorderStopped("Nested calls are not allowed")
            self._remember("reentry", error, None)
            raise error
        self._active = True
        intent: Intent | None = None
        phase: Phase = "preflight"
        try:
            if self._reserved >= self._max_calls:
                raise ValueError("Primitive call allowance exhausted")
            self._reserved += 1
            identity = _token(call_id)
            if identity in self._ids:
                raise ValueError("Primitive call identity already consumed")
            self._ids.add(identity)
            if type(scope) is not tuple or not 1 <= len(scope) <= 6:
                raise ValueError("A bounded logical call scope is required")
            if type(primitive) is not str or primitive not in (
                "position",
                "exp",
                "log",
                "circle_constant",
                "native_exp",
            ):
                raise ValueError("Unsupported D1 primitive")
            intent = Intent(
                self._reserved - 1,
                identity,
                _token(instance_id),
                primitive,
                tuple(_token(item) for item in scope),
                _arguments(primitive, arguments),
            )
            if not callable(invoke):
                raise ValueError("An owned primitive callback is required")
            phase = "intent_sink"
            self._emit(Event(len(self._events), "intent", intent))
            if self._stopped:
                assert self.first_exception is not None
                raise self.first_exception
            phase = "primitive"
            self._invoked += 1
            try:
                result = invoke()
            except BaseException:
                self._primitive_failed += 1
                raise
            self._returned += 1
            phase = "return_encoding"
            try:
                value = (
                    Value("binary64", (_binary(result),))
                    if primitive == "native_exp"
                    else _decimal(result)
                )
            except BaseException as error:
                # Record the fact of return without pretending invalid material was retained.
                self._remember(phase, error, intent)
                try:
                    self._emit(
                        Event(
                            len(self._events),
                            "returned",
                            intent,
                            Value(
                                "unavailable",
                                (type(result).__module__ + "." + type(result).__qualname__,),
                            ),
                        )
                    )
                except BaseException as supplemental:
                    self._remember("return_sink", supplemental, intent)
                raise
            phase = "return_sink"
            self._emit(Event(len(self._events), "returned", intent, value))
            if self._stopped:
                assert self.first_exception is not None
                raise self.first_exception
            return result
        except BaseException as error:
            self._abort(phase, error, intent)
            raise
        finally:
            self._active = False
