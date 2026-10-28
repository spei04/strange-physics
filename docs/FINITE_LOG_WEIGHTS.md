# Finite log-weight normalization

This additive RA-N02.a building block normalizes supplied algebraic log weights.
It does not choose a scientific grid, prior, likelihood, covariance, discrepancy
or calibration tolerance. It implements no native belief update, MAP selection,
Laplace approximation, measured operation or study admission.

## Input and result

`normalize_finite_log_weights(actual)` accepts `FiniteLogWeightInput`: an ordered
tuple of 1–1,025 entries with unique SHA-256 correlation labels. Every entry is
either `finite` with a finite log weight, `exact_zero` without a value, or
`upstream_failed` without a value. The labels are opaque; they do not authenticate
candidates or the source of a supplied weight.

Success retains every label and position, returning finite normalized **log**
weights and separately tagged exact zeros. The normalizer is retained as
`maximum_log_weight` and `log_scaled_sum`. These components are not combined:
a large common offset can absorb the smaller component in binary64.

The implementation centers finite inputs at their maximum, evaluates their
exponentials, sums with `math.fsum`, and applies `math.log`. Normalized logs are
rounded binary64 approximations. No ordinary probability array is returned.
When a finite centered exponential underflows, its index is reported and its
finite normalized log is preserved. It is never converted into an exact-zero
entry. This diagnostic does not describe every rounding loss: a representable
tail such as `exp(-500)` can be absorbed when added to one.

All upstream failures are collected before numerical work; surviving entries
are never normalized on their own. All-zero input is a different outcome.
Nonfinite required arithmetic produces a whole-operation failure with its
stage and, where applicable, original entry index. There is no partial
normalization. Counts retain attempted exponential, sum and logarithm calls;
they are local operation counts, not measured CPU or ledger settlements.
Exceptions unrelated to arithmetic propagate.

## Validation boundaries

Use the bounded raw parsers before decoding untrusted input or result bytes.
Each transport has a 256 KiB limit, depth 16 and 20,000 lexical JSON nodes.
Typed inputs and results entering the public binder are structurally bounded
before serialization and revalidated;
this covers ordinary instances and Pydantic construction/copy bypasses. It is
not a sandbox for arbitrary Python objects or monkeypatched classes.

`bind_finite_log_weight_result(result, actual)` checks the complete canonical
input identity, ordered labels, entry kinds, counts and diagnostic association.
Original raw-byte identity is separate from canonical identity, including
signed zero. Parsing, structural validity and this identity join do not prove
that a result was actually computed or that its numerical values are correct.
The normalizer computes results; independent reference tests assess its
numerical behavior. No result is a posterior, MAP proof or authenticated
marginal-evidence calculation.

The fixed transport/cardinality limits are software bounds. Existing native,
selection, ledger, execution and publication contracts and cumulative study
limits remain unchanged.

## Reference tests and implementation checkpoint

The focused source declares 40 tests and, for a complete successful run,
37 normalizer invocations and 11 independent Decimal reference vectors.
Scientific forward, likelihood, simulator, public measured and product-child
calls are all zero. The test module reports actual invocation counts on teardown.
Per-vector diagnostics record input identity, size, independent positive tails,
observed errors and applicable tolerances before numerical assertions. The
source census is not a claim that tests have executed.

The independent oracle uses exact input floats, a direct unshifted Decimal
finite sum and precision 700. It preserves the positive centered logarithms in
both `[0, -500]` and `[0, -1000]`; an 80-digit oracle would itself lose those
tails. Huge common offsets use separate analytic equal-weight checks rather
than enormous-exponent Decimal calculations.

Predeclared finite-regression criteria are absolute centered-log-normalizer
error at most `1e-12`, and normalized-log error at most `1e-12` plus four
reference ULPs. These are numerical software-test criteria, not scientific
calibration values or universal accuracy guarantees. Tests also retain typed
failures, unrelated interruptions, malformed raw inputs, maximum cardinality,
signed-zero identity and pre-serialization rejection.

The schema generator is `finite_log_weight_json_schema()`. Generated schema
output and all runtime checks are pending separate validation at this initial
source checkpoint. Synthetic examples contain no scientific profile.
