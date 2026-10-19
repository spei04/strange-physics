# Local scientific contracts v1

Status: first local SCI subset accepted and integrated for SP-01.a in PR #51,
merge cc24aef592f3157b67024e3cab41159489c77ffa. Independent review and matching
Python 3.12/3.14 CI passed; the execution log records the evidence. The scientific domain,
fitter, predictor and evaluator remain separate implementation tasks.

The authoritative messages are in
[src/strange_physics/research_contracts.py](../src/strange_physics/research_contracts.py),
with generated [JSON Schema](../contracts/research.schema.json) and
[synthetic fixtures](../contracts/research.examples.json). They extend the existing
public [core contract](../src/strange_physics/contracts.py). These fixtures contain
made-up numbers to test interfaces; they are not observations, fitted results or
benchmark evidence.

This subset serves trusted local code. It does not authenticate a purchaser or
prove that an observation came from an authorized server. Hosted ownership,
artifact generations, storage authorization and executable predictor isolation
belong to the later HTTP, ART and EXEC contracts. A content hash establishes
byte identity, not authorship or scientific validity.

## Messages and call sequence

1. Parse `SpringFitInput` from JSON. It includes only an `ObservationBundle`
   containing the exact purchased prefix, its final `through_index`, and a
   `fit_config_sha256`. The prefix must contain at least one completed record;
   empty or all-failed inputs are not fit inputs.
2. A future fitter produces `LinearSpringModel`. Call
   `validate_model_for_fit(model, fit_input)` before accepting it.
3. Parse `PredictionRequest`, then call
   `validate_prediction_model(model, request)` before running the future predictor.
4. Parse `PredictionResponse`, then call
   `validate_prediction_response(request, response)` before accepting predictions.
5. A future development evaluator produces `EvaluationReport`. Its validator
   checks counts, failure semantics and normalization arithmetic.

These steps are interface validation, not an implementation of steps that learn,
propagate or score. The model asserts a shared, nonnegative, zero-rest-length
linear spring coefficient; no supported accuracy, generalization range or
conditioning threshold is claimed before SP-03.b calibration and SP-04 evidence.
Prediction runtime compatibility beyond this versioned local model remains the
responsibility of the later predictor implementation.

All messages reject extra fields and nonfinite numbers. JSON parsing applies
strict Pydantic types. In trusted Python code use normal constructors or
`model_validate_json`; do not bypass validation using `model_construct`,
unchecked `model_copy(update=...)`, or mutation of nested dictionaries.

## Purchased observations and fit provenance

The embedded core `ObservationBundle` validates contiguous indices, unique
operation IDs, legal purchased actions, particle identity and order, mass/action
bounds, observation counts and sampling times. `through_index` must equal
`len(records) - 1`; a request cannot include later records while claiming to fit
an earlier prefix.

Accepted failed simulations remain in the prefix and its hash. They consumed
budget and may advance a hidden regime boundary. `fit_record_indices` is a
nonempty, unique, strictly increasing selection of completed records within the
prefix; the cross-message helper rejects selected failed records. The model's
prefix index and fit-configuration digest must match its input. The digest binds
all public run, engine, structure, sampling, action, failure and observation data.

The fit configuration remains separately versioned and hashed. This contract
does not select an excitation threshold, regularizer or numerical acceptance
tolerance ahead of the calibration work. The caller is responsible for retaining
the actual configuration corresponding to `fit_config_sha256`; comparing digest
strings alone cannot establish that the implementation used that configuration.

## Canonical bytes and hashes

The profile name is `strange-physics.python-json.v1`. `message_sha256` computes
SHA-256 over this exact sequence:

1. `message.model_dump(mode="json")`, including every field, defaults and explicit
   null values. No `exclude_unset`, `exclude_defaults` or `exclude_none`.
2. Existing `canonical_json`: Python `json.dumps` with sorted keys, separators
   `(",", ":")`, `allow_nan=False`, and its default `ensure_ascii=True`.
3. Encode the resulting string as UTF-8, without a trailing newline.

This is the existing Python JSON codec, **not RFC 8785/JCS** and not a promise that
browser `JSON.stringify` produces equivalent bytes. Integer-valued floating
fields serialize as Pydantic JSON-mode floats, Unicode is escaped, and negative
zero remains distinct from positive zero. Consumers must hash the normalized
typed message, not arbitrary incoming JSON whitespace, key order or omitted
defaults. The fixture includes an exact canonical model string and digest,
including a Unicode fitter version. A serialization-profile change requires a
compatibility decision and new vectors.

`observation_sha256` hashes the entire supplied `ObservationBundle`.
`PredictionRequest.model_sha256` hashes the entire `LinearSpringModel`, including
provenance and selected records. The model-request helper recomputes that digest.
The response-request helper compares the returned digest with the request.

## Prediction order, time and work bounds

A prediction request uses public structure, initial conditions and one optional
initial impulse. Particle identities and their order must match the structure.
Frame arrays use that order; frames have no separate identity labels, so shape
validation cannot detect a predictor that lies about the meaning of an array
position. Analytic and permutation tests of the predictor itself remain required
under SP-04.b.

Prediction probes may exceed purchased-action bounds, because they include
initial-condition extrapolation. Do not pass them through
`ExperimentSpace.validate_experiment`. Core finite values, positive masses,
structure validity and impulse target validation still apply. Solver stability
and the calibrated extrapolation domain remain runtime/scientific checks.

Times start at zero, strictly increase, stay within ten seconds and align to
`integration_dt` within the existing grid-ratio tolerance of `1e-8`.
Rounded integration-step indices must also strictly increase: two distinct float
times cannot alias the same step, and the horizon must include a positive step.
There are 2–2,001 output times, integration steps are between 0.0001 and 0.05,
and the horizon may require no more than 20,000 steps. The response must have
exactly the requested times and particle count. A predictor should retain the
requested timestamp values in its output rather than recompute them with a
different floating representation. The core trajectory contract checks finite
coordinates, equal position/velocity counts and increasing times.

## Development report semantics

`EvaluationReport` accepts only `split="development"`. It cannot claim to be a
reference or blind benchmark report. Counts include every requested probe and
must satisfy `valid_prediction_count + failed_prediction_count == probe_count`.

The fixed local diagnostic policy is `unscorable-on-any-failure.v1`: any missing,
invalid or failed prediction makes `status="unscorable"` and both primary MSE
fields null. No mean over surviving predictions is presented as the primary
score. All-valid predictions require `status="scored"` and finite nonnegative
MSE values. A true all-valid zero error remains valid. This deliberately leaves
the full benchmark penalty policy unfrozen.

`position_mse` is the mean squared coordinate error, in squared coordinate
units, with averaging dimensions and probes specified by the retained protocol
identified by `protocol_sha256`. `normalization_scale` is a fixed coordinate
scale in coordinate units, not a variance or squared scale:

`normalized_position_mse = position_mse / normalization_scale**2`.

The report validator checks that the squared scale is representable, finite and
positive, and that normalization neither overflows nor underflows a positive
error to zero. The reported normalized value must agree within relative
tolerance `1e-12`, with zero absolute tolerance. It cannot validate the
underlying error calculation without predictions and labels; SP-06.a provides
that independent evaluator and hand-calculated score tests. Runtime is a
nonnegative integer number of milliseconds. These public contracts must not be
used to give evaluator-only labels or reports to a live agent.

## Schema and compatibility checks

The JSON Schema is self-contained and generated by `research_json_schema()`.
Validate against a named `$defs` entry. JSON Schema alone cannot enforce all
ordered-prefix, frame-grid, count-arithmetic or cross-message relationships;
call the Pydantic validators and helpers above as well. Tests verify generated
schema equality, local reference resolution, synthetic fixture round trips,
golden bytes, invalid fields and semantic/cross-message failure cases.

The earlier `contracts/draft/research.schema.json` is retained as a historical
draft for its existing fixtures and unimplemented hosted API references. Its SCI
messages use `draft1` versions and are superseded for this local subset; there is
no implicit draft-to-v1 conversion. In particular, v1 adds an exact fit input and
record selection, and restricts reports to explicit development diagnostics.
`ArtifactRef` remains a draft ART interface and is not frozen here.

Review ownership: the Research implementation, independent SDK/quality review,
and technical-lead integration decision are recorded in
[EXECUTION_LOG.md](EXECUTION_LOG.md). This document does not substitute for that
review evidence or the later numerical and production readiness gates.
