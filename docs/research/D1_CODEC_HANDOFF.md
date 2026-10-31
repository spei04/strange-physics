# Conditional recorder, codec and file-sink handoff tests

This is an authored test slice, not an installed D1 execution path. Its base is
`56a5c473fb113e03bd519764dcee81937320097c`, containing the accepted Unit13 bridge
code at `1c815203bbe1519207933dd1819fbc93203e6dd5`. Only
`tests/test_d1_codec_handoff.py` and this guide are added. Existing recorder,
bridge, codec, table and sink code are unchanged. No imports, collection, tests,
formatter, typing, actual files or callbacks were executed during authoring.

The [bridge scope](D1_CODEC_APPEND.md), [append design](D1_CODEC_APPEND_DESIGN.md)
and [codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md) remain authoritative.
The tests require a new independently reviewed engineering guard and admission
before execution; no scientific allocation or earlier balance is inherited.

## Conditional objects and actual bytes

Each case creates one actual `PrimitiveFileSink` in its owned pytest temporary
root. It supplies synthetic fixed identity declarations and a 65,536-byte sink
context, preserving the full 55,100-call/110,201-line declaration while exercising
only a tiny prefix. The real sink writes C; the test reads its actual bounded
`context.json` bytes into the real `CodecAppendBridge`. The real
`PrimitiveRecorder` calls that bridge, which calls the real sink through an owned
observing callback. The recorder's logical byte limit remains 64 MiB.

T is exact validated synthetic table bytes kept in memory. No S/A resolver,
authenticated source/member mapping, durable T retention, metadata activation or
production installation is supplied. Matching T/C declarations are not evidence
of those missing joins. Passing these tests can establish conditional code order
and byte replay in this process; it cannot establish an activated durable
transcript or authorize actual D1 primitives.

Source-defined fake callbacks only return fixed `Decimal("1.2500")`, signed
binary64 zero, deliberately invalid `object()`, or a named synthetic exception.
No forward model, normalization, reference, true endpoint or scientific primitive
is called. Numeric spellings/quantum are tested without calculating a scientific
answer. The test-body guard poisons transcendental math functions and blocks new
imports of named scientific producers; independent execution guards must also
retain their defining-code/alias/process/network denials. This is not an OS sandbox.

## Eight authored cases

| Case | Required observation |
| --- | --- |
| Decimal success | Intent is confirmed before fake callback entry; exact quantum survives; return is confirmed before consumer handoff. |
| Signed-binary64 success | Same order, preserving the exact negative-zero hex spelling. |
| Intent write failure | Zero fake invocations; logical intent/failed Event remain unknown; one physical attempt only. |
| Return partial write and lost close confirmation | One fake invocation, no value handoff; actual prefix bytes/unknown full reservation retained; original write error survives real sink closeout uncertainty. |
| Fake primitive exception | Same original exception, distinct terminal raw fallback and recorder unknown acknowledgement despite physical callback return. |
| Swallowed recorder reentry then invalid return | Original reentry error differs from outer encoding error; unavailable/failed raw Events yield failed ordinal3 and snapshot-only fault_retention ordinal4. |
| Swallowed bridge reentry after physical write | Physical callback returned, but no bridge/recorder acknowledgement or fake invocation; no physical failed-event retry. |
| Context mismatch after sink creation | Constructor rejects without an event callback; the already-owned sink is still finished once. |

Static census: eight cases in seven test functions, with 24 prospective pytest
setup/call/teardown phases. They have not run. The one parameterization uses two
short explicit IDs; other cases are individually named.

Success cases expand actual shard lines with the same T and compare the resulting
bytes to the actual recorder snapshot. Failure cases keep raw terminal lines,
logical delivery labels, bridge callback observations and sink counters distinct.
Inspection never promotes a complete line or partial fragment to acknowledgement.
No test returns a stored snapshot as a resume/authority input.

## Owned failure injection and once-only cleanup

Event-write injection patches only the defining sink `_write_remaining` helper
inside the recorder call. It verifies the fd is the case's active event fd. The
intent fault writes nothing; the return fault lets the intent use the original
helper, then performs one positive write of at most seven return bytes and raises.
The progress counter records those actual bytes. The patch is restored before
cleanup, so terminal writing and subsequent tempfile teardown use normal helpers.

In the partial-return case only, a separate `os.close` wrapper surrounds the single
actual `sink.finish()`. It calls the original close on every descriptor. For the
one owned active event fd, after successful close it raises synthetic
`OSError(EIO)` exactly once, modeling lost confirmation. Later reuse of that fd
number passes through normally. The real sink's `data_close` and
`closure_uncertain` paths therefore report `descriptors_closed=false`, while
post-cleanup fd checks require all captured owned descriptors to be actually
closed. This is an injected condition, not a claim that a kernel close failed.
The wrapper is restored before descriptor readback and pytest/tempfile teardown.

The test owner attempts bridge finish once when constructed, then sink finish once,
independently preserving supplemental cleanup exceptions if the body already
failed. No second finish or close retry is invoked. The original partial-write
exception remains both the raised body error and the sink's first exception; the
synthetic close uncertainty appears separately in the actual sink closeout.
Terminal receipts remain `pending_external_confirmation`, including when their
own write was acknowledged. No fixture manufactures external confirmation.

## Source-derived work and output envelope

The authored matrix plans eight sink creations and eight sink finishes, seven
successful bridge/recorder constructions and seven bridge finishes. There are
seven outer recorder-call attempts plus one denied nested recorder call. Exactly
five owned fake callback entries are expected across the matrix; only the two
success cases hand a value to a consumer. These are expectations for guard/review,
not measured execution results or scientific calls.

The source paths plan at most 13 physical sink append attempts across all cases.
Each individual case has at most three physical lines, including forensic raw
fallbacks. No rotation, 55,100-event batch or full profile is constructed. The
existing shard, total and logical limits are unchanged.

For a conservative retained-file estimate per case:

```text
context <= 4,096
terminal <= 16,384
at most three event lines <= 3 * 4,096
case payload <= 32,768 bytes
eight cases <= 262,144 bytes
```

The owner asserts the per-case payload ceiling after cleanup. Seven cases can have
C/one shard/terminal and the context-rejection case only C/terminal: at most 23
payload files in eight sink roots, with no T/A file, extra transcript copy, symlink
or FIFO authored by this suite. Directory blocks, source/control files, pytest
logs, JUnit/phase reports, retained failures and other engineering outputs remain
separately counted. The estimate is not measured physical disk use or proof of
whole-study fit. All actual I/O must remain under the owned temporary paths.

## Limits of a future passing result

A passing engineering run would support these specific source interfaces, failure
orders, exact small-line replay and resource cleanup assertions. It would not
supply S/T/C/A custody/activation, real primitive/source ownership, historical
exposure completeness, crash/power-loss durability, full-call memory/byte fit,
scientific calibration, report binding or a scientific run admission. Those
obligations remain explicit later work.
