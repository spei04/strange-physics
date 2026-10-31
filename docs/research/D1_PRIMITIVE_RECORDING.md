# D1 primitive-return recorder

Source slice, 2026-10-31. The facade in
`tests/d1_primitive_recording.py` passed bounded ordinary synthetic engineering
checks, as recorded below. It implements the in-memory ordering boundary from the
[report design](https://github.com/spei04/strange-physics/blob/23b5765e2f967e5286754d4c70be8b1da71ef56f/docs/research/D1_REPORT_BINDING_DESIGN.md), not a durable file sink, a driver,
a report schema or numerical admission. Existing numerical files are unchanged.

## Exact interface and supported boundary

`PrimitiveRecorder(append, max_calls=..., max_bytes=...)` owns one single-threaded,
fail-stop transcript. Its `call` accepts a unique opaque call ID, an existing
instance ID, a primitive name, a bounded logical scope, the declared argument
and an already owned zero-argument callback. The callback is invoked at most
once, only after the exact intent event has been synchronously accepted by
`append(raw: bytes)`. Its unmodified return reaches the caller only after the
return event has likewise been accepted. The driver must bind the callback to
the declared method, arguments and existing instance. Labels do not prove this
binding; the facade does not inspect code, instantiate an oracle or intercept
an existing method.

The supported D1 reference boundary is `position` (seven exact binary64
arguments), `exp` and `log` (one exact Decimal argument), and `circle_constant`
(no argument), each returning Decimal. `native_exp` separately records the
binary64 emitted-weight conversion, with binary64 input and return. Internal
native normalizer exponentials are not intercepted. No D1 primitive at these
boundaries returns a tuple, interval or proof object. `trig` is outside the D1
call plan and unsupported; fixture proofs and derived intervals remain the
producer/adapter's responsibility. A malformed or unsupported return is marked
returned with its type but unavailable value, never silently converted into
successful evidence.

Decimal recording retains sign, coefficient digits and exponent, including
negative zero and trailing zeros, without rounding or arithmetic. The codec
accepts finite coefficients of at most120 digits and exponents from -256 to128;
this encoding domain does not establish the narrower numerical premises.
Binary64 values use exact `float.hex()` strings and reject nonfinite values.
Neither encoding calls a scientific function, exp or log.

## Progress, failure and retention semantics

Each successful call has two immutable events: intent then returned. Event
sequence, call/instance/scope and exact arguments bind the return to its intent.
The snapshot distinguishes reserved calls, invoked primitives, returned
primitives and primitive exceptions; a sink exception is never counted as a
primitive exception. Confirmed sink delivery means only that the supplied sink
returned successfully. On a sink exception, delivery remains unknown even if
it wrote some or all bytes. The event is retained in memory before append;
there is no retry of the same event or call.

An invalid intent or failed intent append prevents invocation. A successful
primitive followed by return-encoding or append failure retains the known
return fact and stops. A failed primitive preserves its original exception
object and re-raises that same object. The first fault records phase, call ID
when available and exception type; exception arguments, traceback and arbitrary
`__str__` are not serialized. Oversized type names are explicitly marked
incomplete. A separate fault-retention error is supplemental and cannot replace
the original fault. Fault recording is attempted once and is not recursively
retried when it fails. Failed encoding, exhausted allowance and nested calls
also stop further calls. There is no reset.

In-process snapshots are evidence of what this facade retained, not proof that
a process survived or that bytes reached stable storage. If recording fails
before an event fits, the snapshot retains counters and the fault, but does not
claim the missing value was preserved. Downstream adapter validation occurs
after the primitive returns: its enclosing driver must retain that separate
fault and stop; it cannot erase the already confirmed primitive return or
mistake the downstream failure for a primitive failure.

## Explicit bounds and census

Both allowances are required, with no inferred run allocation. `max_calls` is
at most55,100:29,500 reference primitive calls (25,600 exp,46 log,one circle
constant,3,840 candidate positions and13 fixture positions) plus25,600 native
emitted conversions. The facade does not create any of those calls; wrapping
one existing call adds zero scientific evaluations. The single-invocation call
plan and the existing per-instance oracle guards still belong to the driver.
Cache hits and reused slots must not invoke the facade again merely to create
another physical-call record.

Each canonical JSON-line event is capped at4,096 encoded bytes. The explicit
retained-byte allowance counts every in-memory encoded event, including an
append whose delivery is unknown; its domain ceiling is64 MiB, not a proposed
partition or a proof that a full transcript fits. Limits are checked before the
sink is called. Fault records consume the same allowance and may themselves
fail to fit, leaving an explicit in-memory retention fault. Object/exception
memory, snapshot copies, sink temporary files, duplicate writes and filesystem
blocks are not measured by this serialized-byte counter. A future writer must
account for them and reserve its terminal space within the unchanged approved
whole-run limits. This slice does not increase the64 MiB scientific cap.

One full successful wrapping would add110,200 intent/return event encodings
before failure/control records. Those records must be joined or encoded
losslessly within the later report codec's physical writer census; the earlier
29,500 primitive-return-row target is not permission to omit intent records or
to double-count the same physical bytes. No serializer fit or CPU cost has been
measured here.

## Authored checks and next boundary

The test module uses owned constant-returning/raising callbacks and fake sinks;
all five real `EndpointOracle` methods are poisoned before each test. Tests
cover exact argument/return encoding, partial constant/exp progress, failed
intent with zero invocations, successful return followed by sink failure,
primary exception plus failed fault retention, invalid returned material,
call/byte exhaustion, duplicate IDs, nested calls and downstream rejection.
They also cover KeyboardInterrupt/SystemExit and an exception whose `__str__`
raises. All 57 cases passed the guarded check; the exact collection and 171 test phases
were independently verified. These use fake callbacks and sinks.

Before a scientific run, independently review and qualify a concrete durable
append sink, its no-follow/exclusive path and fsync behavior, its fallback
receipt and capacity handling, the complete failure-inclusive operation/byte
census, and scoped installation on the exact already owned primitive instances.
The source/runtime and actual-argument joins must be retained, not inferred
from this callback interface. Integrate the recorder before the first primitive
call, preserve partial returns before adapter consumption, and restore any
instrumentation in the enclosing finally path. Ordinary fake-only engineering
checks are separate from that implementation and from numerical authority.


## Engineering checkpoint

Source 98f55f88c89f2d1ed145691090e218a8590de0be passed formatting, lint and full
typing across 203 source files. All 57 synthetic cases and 171 ordered
setup/call/teardown phases passed, with no skips, expected failures or forbidden
events. The sealed collection, source/helper identities, unchanged environment,
raw logs and JUnit counts were independently reviewed. Formatting preserved
the authored AST except ordering of identical import statements.

Both local attempts passed and all 12 owned processes closed. The cumulative
charge is 46.092669 CPU seconds / 55.725405 wall seconds, including the retained
per-attempt closeout holds. Retained unit output is 1,613,326 bytes within the
120 CPU / 300 wall / 8 MiB engineering allowance. Additional controller
headroom was withheld from child selection, not charged again. Prior failed
units and reservations remain retained; external-control and whole-operation
costs remain unknown.

Hosted verification is a separate pending step after the parent adapter PR
qualifies. This checkpoint establishes fake-only ordering, codec and failure
behavior. It does not establish actual sink durability, callable/argument
authenticity, complete transcript storage fit, a D1 scientific result or
production readiness.
