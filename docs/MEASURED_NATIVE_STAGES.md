# Measured native stages

The trusted-local entrypoints in `measured_native_stages.py` commit preparation,
prediction and scoring through the existing candidate store. They accept
`NativePreparationRequest`, `NativePredictionRequest` and `NativeScoreRequest`
respectively; each returns a typed `CommittedNativeStage`. The candidate API,
request/receipt wire contracts, authoritative ledger, finite ticket namespace
and SQLite store remain shared. There is no caller-selected callable or module.

These entrypoints admit only the existing plan-bound pre-freeze reference,
calibration and sensitivity phases. Comparison is rejected until its real Journal
adapter exists. Classical execution, purchased simulation, authority handoff and
full-study admission remain separate requirements.

## Identity and retained results

Each operation parses its existing native input, calls exactly its fixed native
producer in the supervised child, and validates the result with the existing
input/result/facts binder. Preparation's deterministic protocol recomputation is
inside charged parent work, including recovery; recovery does not rerun a
numerical producer. Stage receipts carry their operation and a distinct version.
A receipt cannot be substituted across stages or for a candidate receipt.

Standalone prediction binds the supplied model/provenance, request, configuration
and result to the verified current executing installation. Its existing input has
no historical engine field, and the wrapper does not invent one or authenticate
the model's historical origin. Preparation/scoring preserve and check their actual
observation engine. An integrated lineage claim requires actual retained candidate
and preparation materials and their complete model/configuration/prefix/protocol
joins. These local bindings do not establish comparison Journal ancestry.

Exact recovery consumes a fresh finite ticket and work reservation. It validates
the original request, raw input/result, receipt, original reservation boundary and
retained prefix, preserving the original output bytes and facts. A lost
acknowledgement can use the original submitted head; a new execution still uses
current-head CAS. Unknown attempts and the control hold remain charged. Stage
failure, corruption, deadline and storage paths inherit the same bounded
supervisor/store behavior.

## Bounds and validation scope

Candidate/prediction input and result caps remain 8/4 MiB; preparation/scoring use
their existing 16/8 MiB parser caps. Canonical execution requests stay within
8 KiB. Admission protects recovery and finalization headroom as well as the
publisher's actual work formula, 16 MiB per-call floor and 512 MiB ceiling.

The proposed synthetic chain uses 30 tickets (27 executions and three recoveries)
and a 2 MiB store, plus a retained unresolved 32 MiB/120-second synthetic
setup/material-assembly reservation created before observation fixtures. It
asserts retained material sizes without presenting that hold as exact cost. Its measured usability and exact material sizes must pass
before it is accepted as a fixture. It is not a study run or evidence that
432 purchases or 36 cells fit. The existing conservative per-ticket transaction
envelopes and per-cell publication escrow make large profiles inadmissible under
the unchanged global cap; a separate storage/control design is still required.

This is an initial executable checkpoint under review. Focused contract, stage,
fault and installed-source checks accompany the implementation; final source
acceptance, configured checks and hosted delivery are separate evidence gates.
