"""Conditional codec append ordering; no recorder, sink, activation or science wiring."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal, cast

from d1_primitive_codec import (
    EVENT_BYTES,
    MAX_CALLS,
    MAX_EVENTS,
    PrimitiveEventCodec,
    _canonical,
    _int,
    _list,
    _no_float,
    _object,
    _pairs,
    _parse,
    _str,
    _value,
)
from d1_primitive_codec_table import TableView, parse_table

Kind = Literal["intent", "returned", "failed"]
Phase = Literal["preflight", "intent_sink", "primitive", "return_encoding", "return_sink", "reentry"]
Primitive = Literal["position", "exp", "log", "circle_constant", "native_exp"]
CallbackState = Literal["not_entered", "entered", "returned", "raised"]
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,95}\Z")
_EVENT_FIELDS = frozenset(("sequence", "kind", "intent", "returned", "fault"))
_INTENT_FIELDS = frozenset(("ordinal", "call_id", "instance_id", "primitive", "scope", "arguments"))
_FAULT_FIELDS = frozenset(("ordinal", "phase", "exception_type", "exception_type_complete", "call_id"))
_TAGS = {"position": "p", "exp": "d", "log": "d", "circle_constant": "n", "native_exp": "b"}
_PHASES = frozenset(("preflight", "intent_sink", "primitive", "return_encoding", "return_sink", "reentry"))
_CONTEXT_FIXED = {
    "max_calls": MAX_CALLS, "max_events": MAX_EVENTS, "event_bytes": EVENT_BYTES,
    "shard_bytes": 4_194_304, "max_shards": 16, "context_bytes": 4096, "terminal_bytes": 16384,
}
_SHARED = ("run_id", "recorder_id", "source_commit", "source_tree", "protocol_sha256", "source_manifest_sha256", "recorder_sha256")
_CONTEXT_FIELDS = frozenset((*_SHARED, "sink_sha256", "schema", "max_bytes", "event_capacity", *_CONTEXT_FIXED))
LOGICAL_BYTES = 67_108_864
METADATA_BYTES = 20_480
MAX_SINK_BYTES = 16_777_216 - 3 * 65_536
FALLBACK_BYTES = 8192
MAX_FAULTS = 4  # Bounded diagnostic summaries; repeated misuse is not an event retry.


class BridgeStopped(ValueError):
    """Consumed conversion/append opportunity; never a retention acknowledgement."""


@dataclass(frozen=True, slots=True)
class RawIntent:
    ordinal: int
    call_id: str
    instance_id: str
    primitive: Primitive
    scope: tuple[str, ...]
    raw: bytes


@dataclass(frozen=True, slots=True)
class RawFault:
    ordinal: int
    phase: Phase
    exception_type: str
    exception_type_complete: bool
    call_id: str | None


@dataclass(frozen=True, slots=True)
class RawEvent:
    raw: bytes
    sequence: int
    kind: Kind
    intent: RawIntent | None
    returned: bytes | None
    unavailable: bool
    fault: RawFault | None

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"


def _token(value: object) -> str:
    text = _str(value)
    if _TOKEN.fullmatch(text) is None:
        raise ValueError("Recorder token shape")
    return text


def _intent(value: object) -> RawIntent:
    fields = _object(value, _INTENT_FIELDS)
    primitive = _str(fields["primitive"])
    if primitive not in _TAGS:
        raise ValueError("Recorder primitive vocabulary")
    scope = _list(fields["scope"])
    if not 1 <= len(scope) <= 6:
        raise ValueError("Recorder scope extent")
    _value(fields["arguments"], _TAGS[primitive], wire=False)
    return RawIntent(
        _int(fields["ordinal"], 0, MAX_CALLS - 1), _token(fields["call_id"]),
        _token(fields["instance_id"]), cast(Primitive, primitive), tuple(_token(x) for x in scope),
        _canonical(fields),
    )


def _fault(value: object, intent: RawIntent | None) -> RawFault:
    fields = _object(value, _FAULT_FIELDS)
    ordinal = _int(fields["ordinal"], 0, 3)
    phase = _str(fields["phase"])
    if phase not in _PHASES:
        raise ValueError("Failed Event phase; fault_retention is snapshot-only")
    name = _str(fields["exception_type"])
    complete = fields["exception_type_complete"]
    if type(complete) is not bool or not 1 <= len(name) <= 192 or (not complete and len(name) != 192):
        raise ValueError("Exact bounded exception type and completeness")
    call_id = None if fields["call_id"] is None else _token(fields["call_id"])
    if phase == "reentry":
        if ordinal != 0 or call_id is not None:
            raise ValueError("First reentry has null fault call identity")
    elif intent is None:
        if phase != "preflight" or call_id is not None:
            raise ValueError("Null Intent only supports preflight or reentry")
    elif call_id != intent.call_id:
        raise ValueError("Fault/Intent call identity differs")
    if ordinal >= 2 and phase != "return_encoding":
        raise ValueError("Later terminal ordinals require the return-encoding path")
    return RawFault(ordinal, cast(Phase, phase), name, complete, call_id)


def classify_raw(raw: bytes) -> RawEvent:
    """Reparse bytes; a constructed output view is never accepted as proof."""
    fields = _object(_parse(raw, 4), _EVENT_FIELDS)
    sequence = _int(fields["sequence"], 0, MAX_EVENTS - 1)
    kind = fields["kind"]
    if type(kind) is not str or kind not in ("intent", "returned", "failed"):
        raise ValueError("Recorder Event kind")
    intent = None if fields["intent"] is None else _intent(fields["intent"])
    if kind == "failed":
        if fields["returned"] is not None:
            raise ValueError("Failed Event cannot carry a returned Value")
        fault = _fault(fields["fault"], intent)
        return RawEvent(raw, sequence, "failed", intent, None, False, fault)
    if intent is None or fields["fault"] is not None:
        raise ValueError("Successful-shape Event needs Intent and null fault")
    if kind == "intent":
        if fields["returned"] is not None:
            raise ValueError("Intent cannot carry a returned Value")
        return RawEvent(raw, sequence, "intent", intent, None, False, None)
    returned = _object(fields["returned"], frozenset(("kind", "parts")))
    if returned["kind"] == "unavailable":
        parts = _list(returned["parts"], 1)
        if not _str(parts[0]):
            raise ValueError("Unavailable return needs its exact type name")
        unavailable = True
    else:
        _value(returned, "b" if intent.primitive == "native_exp" else "d", wire=False)
        unavailable = False
    return RawEvent(raw, sequence, "returned", intent, _canonical(returned), unavailable, None)


@dataclass(frozen=True, slots=True)
class ContextBinding:
    table_sha256: str
    context_sha256: str
    max_bytes: int
    event_capacity: int

    @property
    def ordinary_capacity(self) -> int:
        return self.event_capacity - FALLBACK_BYTES

    @property
    def material_authenticity(self) -> Literal["unchecked"]:
        return "unchecked"


def _context_number(text: str) -> int:
    if len(text.removeprefix("-")) > 8:
        raise ValueError("Context integer token exceeds eight digits")
    return int(text)


def _context(raw: bytes, table: TableView) -> ContextBinding:
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
        raise ValueError("Context predecode byte bound")
    # C is flat, unlike an Event. Bound nesting before json.loads and integers
    # before int; do not widen the Event codec's separate six-digit guard.
    depth = 0
    quoted = escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 1:
                raise ValueError("Context must be flat")
        elif byte in (93, 125):
            depth -= 1
            if depth < 0:
                raise ValueError("Context structure")
    if depth or quoted:
        raise ValueError("Truncated context")
    try:
        data: object = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs,
                                  parse_int=_context_number, parse_float=_no_float,
                                  parse_constant=_no_float)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Strict context JSON") from error
    fields = _object(data, _CONTEXT_FIELDS)
    if _canonical(fields) != raw or fields["schema"] != "strange-physics.d1-primitive-sink.v1":
        raise ValueError("Exact canonical sink context required")
    for name in _SHARED:
        if type(fields[name]) is not str or fields[name] != getattr(table.identity, name):
            raise ValueError("Table/context identity mismatch")
    sink_hash = _str(fields["sink_sha256"])
    if re.fullmatch("[0-9a-f]{64}", sink_hash) is None:
        raise ValueError("Declared sink hash shape")
    for name, expected in _CONTEXT_FIXED.items():
        if type(fields[name]) is not int or fields[name] != expected:
            raise ValueError("Unsupported context limit")
    maximum = _int(fields["max_bytes"], METADATA_BYTES + FALLBACK_BYTES + 1, MAX_SINK_BYTES)
    capacity = _int(fields["event_capacity"], FALLBACK_BYTES + 1, MAX_SINK_BYTES - METADATA_BYTES)
    if capacity != maximum - METADATA_BYTES:
        raise ValueError("Context capacity excludes its fixed metadata reservation")
    return ContextBinding(table.sha256, hashlib.sha256(raw).hexdigest(), maximum, capacity)


@dataclass(frozen=True, slots=True)
class Attempt:
    sequence: int
    kind: Kind
    raw_sha256: str
    raw_bytes: int
    physical_sha256: str | None = None
    physical_bytes: int = 0
    mode: Literal["none", "compact", "raw"] = "none"
    callback: CallbackState = "not_entered"
    acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class BridgeFault:
    phase: str
    exception_type: str
    exception_type_complete: bool


@dataclass(frozen=True, slots=True)
class BridgeSnapshot:
    binding: ContextBinding
    raw_attempts: int
    raw_bytes: int
    next_sequence: int
    next_ordinal: int
    physical_attempts: int
    physical_bytes: int
    compact_bytes: int
    callback_returns: int
    acknowledgements: int
    fallback_attempts: int
    fallback_bytes: int
    stopped: bool
    physical_blocked: bool
    terminal_consumed: bool
    finish_consumed: bool
    first_failed_attempt: Attempt | None
    last_attempt: Attempt | None
    faults: tuple[BridgeFault, ...]
    unretained_faults: int

    @property
    def activation(self) -> Literal["not-established"]:
        return "not-established"


class CodecAppendBridge:
    """Conditional synchronous retention callback; does not install or own a sink."""

    first_exception: BaseException | None
    _binding: ContextBinding
    _codec: PrimitiveEventCodec
    _pid: int
    _thread: int
    _busy: bool
    _stopped: bool
    _physical_blocked: bool
    _terminal: bool
    _finished: bool
    _allow_failed: bool
    _raw_attempts: int
    _raw_bytes: int
    _sequence: int
    _ordinal: int
    _physical_attempts: int
    _physical_bytes: int
    _callback_returns: int
    _acks: int
    _fallback_attempts: int
    _fallback_bytes: int
    _compact_bytes: int
    _unretained_faults: int

    def __init__(self, table_raw: bytes, context_raw: bytes, *, append: Callable[[bytes], None]) -> None:
        if not callable(append):
            raise ValueError("Synchronous owned callback required")
        table = parse_table(table_raw)
        self._binding = _context(context_raw, table)
        self._codec = PrimitiveEventCodec(table_raw, mode="encode")
        self._append: Callable[[bytes], object] = append  # Validate the actual None return at the boundary.
        self._pid, self._thread = os.getpid(), threading.get_ident()
        self._busy = self._stopped = self._physical_blocked = self._terminal = self._finished = False
        self._allow_failed = False
        self._raw_attempts = self._raw_bytes = self._sequence = self._ordinal = 0
        self._physical_attempts = self._physical_bytes = self._callback_returns = self._acks = 0
        self._fallback_attempts = self._fallback_bytes = self._compact_bytes = 0
        self._current: RawIntent | None = None
        self._last_intent: RawIntent | None = None
        self._last_kind: Kind | None = None
        self._attempt: Attempt | None = None
        self._first_failed_attempt: Attempt | None = None
        self._faults: list[BridgeFault] = []
        self._unretained_faults = 0
        self.first_exception = None
        self._last_latched_exception: BaseException | None = None

    def snapshot(self) -> BridgeSnapshot:
        return BridgeSnapshot(
            self._binding, self._raw_attempts, self._raw_bytes, self._sequence, self._ordinal,
            self._physical_attempts, self._physical_bytes, self._compact_bytes, self._callback_returns, self._acks,
            self._fallback_attempts, self._fallback_bytes, self._stopped, self._physical_blocked,
            self._terminal, self._finished, self._first_failed_attempt, self._attempt,
            tuple(self._faults), self._unretained_faults,
        )

    def _latch(self, phase: str, error: BaseException, *, block: bool) -> None:
        self._stopped = True
        self._physical_blocked = self._physical_blocked or block
        if error is self.first_exception or error is self._last_latched_exception:
            return
        self._last_latched_exception = error
        if self.first_exception is None:
            self.first_exception = error
        if len(self._faults) < MAX_FAULTS:
            name = type(error).__module__ + "." + type(error).__qualname__
            self._faults.append(BridgeFault(phase, name[:192], len(name) <= 192))
        else:
            self._unretained_faults += 1

    def _owner(self) -> None:
        if self._busy or os.getpid() != self._pid or threading.get_ident() != self._thread:
            error = BridgeStopped("Wrong owner or bridge reentry")
            self._latch("ownership_or_reentry", error, block=True)
            raise error

    def _join(self, event: RawEvent) -> None:
        if event.sequence != self._sequence:
            raise ValueError("Next visible reserved Event sequence required")
        intent = event.intent
        if event.kind == "intent":
            if intent is None or self._current is not None or intent.ordinal != self._ordinal:
                raise ValueError("One current ordered intent")
        elif event.kind == "returned":
            if intent is None or intent != self._current:
                raise ValueError("Complete returned Intent differs")
        else:
            assert event.fault is not None
            if self._current is not None:
                if intent != self._current or event.fault.phase == "preflight":
                    raise ValueError("Terminal current Intent or phase differs")
            elif intent is None:
                if self._stopped:
                    raise ValueError("Known append failure cannot erase its Intent")
            elif self._last_kind == "returned" and intent == self._last_intent:
                if event.fault.phase not in ("return_sink", "reentry"):
                    raise ValueError("Completed return cannot move back to an earlier phase")
                # The codec may already have advanced and cleared its intent.
            elif not self._stopped and intent.ordinal == self._ordinal and event.fault.phase in ("preflight", "intent_sink"):
                pass  # Recorder _emit can fail before reservation or callback.
            else:
                raise ValueError("Terminal Intent lacks a visible or preflight join")

    def _write(self, raw: bytes, *, fallback: bool) -> None:
        if self._physical_blocked:
            raise BridgeStopped("Prior callback/ownership failure forbids physical writes")
        if self._physical_attempts >= MAX_EVENTS or self._physical_bytes + len(raw) > self._binding.event_capacity:
            raise BridgeStopped("Physical reservation exhausted")
        if not fallback and self._compact_bytes + len(raw) > self._binding.ordinary_capacity:
            raise BridgeStopped("Ordinary bytes cannot consume the failure reserve")
        if fallback and (self._fallback_attempts >= 2 or self._fallback_bytes + len(raw) > FALLBACK_BYTES):
            raise BridgeStopped("Terminal fallback reservation exhausted")
        self._physical_attempts += 1
        self._physical_bytes += len(raw)
        if fallback:
            self._fallback_attempts += 1
            self._fallback_bytes += len(raw)
        else:
            self._compact_bytes += len(raw)
        assert self._attempt is not None
        self._attempt = replace(self._attempt, physical_sha256=hashlib.sha256(raw).hexdigest(),
                                physical_bytes=len(raw), mode="raw" if fallback else "compact", callback="entered")
        try:
            result = self._append(raw)
        except BaseException as error:
            self._attempt = replace(self._attempt, callback="raised")
            self._latch("physical_callback", error, block=True)
            raise
        self._callback_returns += 1
        self._attempt = replace(self._attempt, callback="returned")
        if result is not None:
            error = ValueError("Append callback must return None")
            self._latch("callback_result", error, block=True)
            raise error
        # A callback can swallow a nested bridge error. Its normal return is a
        # separate observation and must not clear that sticky consumed state.
        if self._physical_blocked:
            assert self.first_exception is not None
            raise self.first_exception

    def append(self, raw: bytes) -> None:
        self._owner()
        if self._finished or self._terminal or (self._stopped and not self._allow_failed):
            raise BridgeStopped("Bridge opportunity consumed")
        self._busy = True
        visible = False
        try:
            if type(raw) is not bytes or not 1 <= len(raw) <= EVENT_BYTES:
                raise ValueError("Raw Event predecode bound")
            if self._raw_attempts >= MAX_EVENTS or self._raw_bytes + len(raw) > LOGICAL_BYTES:
                raise BridgeStopped("Logical raw reservation exhausted")
            self._raw_attempts += 1
            self._raw_bytes += len(raw)
            event = classify_raw(raw)
            if self._stopped and event.kind != "failed":
                raise BridgeStopped("Only one failed Event can follow a stopped append")
            self._join(event)
            self._sequence += 1  # Recorder reserved this line before calling us.
            visible = True
            self._attempt = Attempt(event.sequence, event.kind, hashlib.sha256(raw).hexdigest(), len(raw))
            if event.kind == "failed":
                self._terminal = True
                self._allow_failed = False
                self._stopped = True
                if self._physical_blocked:
                    raise BridgeStopped("Terminal classified; physical callback remains forbidden")
                self._write(raw, fallback=True)
                raise BridgeStopped("Raw terminal retained without recorder acknowledgement")
            self._allow_failed = True
            self._last_intent, self._last_kind = event.intent, event.kind
            if event.kind == "intent":
                self._current = event.intent
            conversion = self._codec.convert(raw)
            if conversion.status == "converted":
                if conversion.raw_event != raw or conversion.wire_event is None or conversion.table_sha256 != self._binding.table_sha256:
                    raise ValueError("Conversion bytes/table binding differs")
                if event.kind == "returned":
                    self._current = None
                    self._ordinal += 1
                self._allow_failed = True
                self._write(conversion.wire_event, fallback=False)
                if self._stopped:
                    assert self.first_exception is not None
                    raise self.first_exception
                self._acks += 1
                self._attempt = replace(self._attempt, acknowledged=True)
                self._allow_failed = False
                return
            self._stopped = True
            self._allow_failed = True
            self._write(raw, fallback=True)
            raise BridgeStopped("Raw fallback retained without recorder acknowledgement")
        except BaseException as error:
            # Invalid/unjoinable input has no trustworthy next forensic slot.
            # A valid visible line may still be followed by its one failed Event.
            if not visible:
                self._terminal = True
                self._allow_failed = False
            self._latch("append", error, block=not visible)
            if self._first_failed_attempt is None and visible:
                self._first_failed_attempt = self._attempt
            raise
        finally:
            self._busy = False

    def finish(self) -> BridgeSnapshot:
        self._owner()
        if self._finished:
            raise BridgeStopped("Finish opportunity consumed")
        self._finished = True
        self._stopped = True
        self._terminal = True
        self._allow_failed = False
        return self.snapshot()
