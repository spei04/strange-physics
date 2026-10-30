# Test-only Gaussian analytic references

This pack prepares independent software fixtures for later Laplace work. It does
not implement an optimizer, native model adapter, posterior, or study profile.
It imports no product module. Its fixed numerical cases are software examples,
not selected scientific priors, discrepancy, covariance, or calibration values.

## Domain and meaning

For the quadratic log kernel `ell(k) = c - r²(k-mu)²/2`, the reference measure
is Lebesgue `dk`. The closed family uses `r in {1/2,1,2}`,
`mu in {-1,0,1}`, and `c in {-16,0,16}`. Finite endpoints and density
queries use standardized `t = r(k-mu) = integer/16` in `[-4,4]`.
Support is either the real line or one positive-width closed interval.

`tests/laplace_analytic_reference.py` returns exact rational enclosures for
`log Z - c`, supported-point log density, and integrated cell log mass.
This shifted normalizer keeps the common log offset explicit. Exact-zero cells
have a separate tag and no logarithm. A disjoint or singleton intersection has
zero Lebesgue mass; an endpoint can still have a finite density. The supported
mode is `clip(mu,L,U)`, including equality at a boundary. The returned
`kernel_variance = 1/r²` is the unbounded kernel variance, not the truncated
distribution variance. These results do not authorize a boundary Laplace fit.

A single fixed table has three real-line and five bounded cases. Each has two
positive cells, two zero-mass cells, and three supported density queries.
The bounded cases cover positive partial support overlap, symmetry, both endpoint
modes, the finite tail
`t in [3.5,4]`, and a narrow support dominated by its bounds. No deep-tail,
ultranarrow-tail, arbitrary-precision integration, or general-domain claim is
made. The exact local-support bump example explains why identical local
value/gradient/curvature cannot determine global mass. It is not a multimodality
detector. The bump evaluator and exact monomial-antiderivative assertion share
one explicit coefficient/exponent table, so that assertion checks the implemented
polynomial rather than a separate hard-coded integral.
Nonstationarity and nonpositive-curvature examples are mathematical
witnesses; there is no general optimizer or curvature classifier in this pack.

## Independent reference and finite work

Finite integrals use the degree-192 Taylor polynomial of `exp(-t²/2)`,
integrated as a 97-term rational polynomial. Its enclosure adds
`(upper-lower) * 2^-194` on each side. Logarithms use exact range reduction
and the first 64 terms of `2*atanh(z)`, with the positive remainder
`2*z^129 / (129*(1-z²))`. Machin's identity uses two 64-term alternating
arctangent sums and their next-term remainders. One shared log-two enclosure
also supplies `log(r)`.

The fixed successful table requires 21 integrals, 42 polynomial endpoint
evaluations (4,074 coefficient visits), 44 endpoint logarithms including the
two log(2*pi) endpoints, 2,880 log-series terms including shared log two,
and 128 Machin terms. No cache or implicit extra evaluation is needed.
Public test-helper input cardinalities are checked before this work.
The accepted maximum of 96 endpoint logs still includes log(2*pi).

The rational core checks integer operand widths before multiplication, powers,
addition and GCD. Reduced rationals are limited to 2^21 bits and temporary
integer allocations to 2^22 bits. Core work is capped at 100,000 checked
operations and 4,096 GCD calls/normalization charges. These are fail-closed
software bounds, not measured CPU or process-memory guarantees. Common
denominators and integer Horner evaluation avoid a Fraction reduction at
every series term. Any exceeded bound raises without returning a partial pack.

The mathematical bounds give finite-integral log width below `2^-178` and
each returned log-expression width below `2^-170`. Exact Fraction
comparisons remain authoritative. Directed 96-digit Decimal conversion is
diagnostic only; on these bounded outputs its extra interval width is below
`2e-93`. The independent binary64 comparator uses `erf/erfc` closed
formulas; it is compared against the rational enclosures, never used to
construct them.

## Validation and limits

The handwritten source declares 24 cases: eight fixed vectors, five exact
relations, four plausible-defect checks, five closed-domain/work failures,
and two semantic examples. It generates the successful reference table once.
Four invalid build attempts reject before reference arithmetic; one exhausted
attempt stops during constant preparation. Tiny-input guards check allocation
and GCD exhaustion without constructing a maximal-sized integer.

Each vector records its input digest, exact-enclosure width, directed
normalizer bounds, and binary64 error before numerical assertions. The fixed
software comparison criterion is `2e-12` absolute error; this is a predeclared
test criterion, not a universal standard-library guarantee or scientific
tolerance. Jacobian, density-versus-cell, support clipping and omitted
remainder defects have explicit sensitivity checks.

On 2026-10-28, source `479896f95b9a6dbb761d494547fbce3ab9111411`
passed all 24 cases and 72 phases on CPython 3.12.3 / pytest 9.1.1. All eight
vectors passed the unchanged exact-Fraction comparisons. The largest observed
binary64 error was `3.1624509165526476e-15`; the largest reported enclosure
width was `2.1906444477876626e-55`. Actual core counts were 32,694 checked
operations and 2,117 charged GCD/normalizations, with the planned 21 integrals,
44 endpoint logs, 4,074 coefficient visits, 2,880 logarithm terms and 128 Machin
terms. All five expected rejection reasons were retained. Independent numerical
and accounting reviews accepted the saved result without repeating it.

The single numerical process used 101.677477 CPU seconds and 101.895227 wall
seconds, with a peak RSS of 47,388 KiB. A preceding permission preflight ran no
numerical process; its failure and cost remain recorded. The complete engineering
unit retained its 180 CPU-second / 420 active-wall-second allowance and stayed
within its 8 MiB output ceiling. No previous allowance was reopened. The numerical
receipt SHA256 is `77e6026ae382077e0592960226ac5911be2c41b53716356704ac77069f56dd9b`.

Full repository and hosted CI for this additive pack remain pending. The roughly
102-second module needs a separate required CI job on both supported Python
versions: adding it to the observed 826–832-second suites risks their existing
15-minute limit. This local result is not a hosted-runtime timing guarantee. No endpoint package,
schema, production code, dependency, study allocation or task graph changes
are part of this pack. Later comparative Laplace acceptance still requires
shared accepted continuous prior/likelihood semantics, derivative and boundary
policies, independent fixtures and justified grid resolution. An unvalidated
grid is not ground truth.

## Required CI partition

The proposed CI integration runs this exact module in a separate required
`analytic_reference` matrix on Python 3.12 and 3.14. The ordinary matrix
excludes only `tests/test_laplace_analytic_reference.py`; its other tests,
formatting, typing, schema, security, package and CLI gates are unchanged.
The aggregate gate requires both matrices and security to succeed, including
rejecting skipped, cancelled, missing and unknown results.

`scripts/ci_analytic_reference.py` invokes the module once with an owned
interpreter, `-I -B`, no shared conftest or plugin autoload, and the fixed test
selection. It preserves JUnit and 72 phase reports, eight vector identities
and error/enclosure diagnostics, five rejection reasons and the exact work
census. It requires 2,117 core GCD charges and fewer than 40,000 checked core
operations. Missing, skipped, changed or incomplete evidence fails even if
pytest returns zero. Synthetic CI-policy tests exercise these report and
process-failure checks without constructing a reference pack.

The prospective hosted engineering bounds are a 15-minute job, one child
with CPU soft/hard limits of 295/300 seconds, a 512 MiB address-space limit,
and a 360-second monotonic parent wait followed by at most five seconds
waiting for the killed child. Each output file is limited to 128 KiB and
combined reports/logs to 1 MiB. Standard output and error go directly to the
bounded log file; no unbounded pipe buffer is retained. Failure keeps
available diagnostics and exits unsuccessfully, with no automatic retry.
These controls cover the audited single child, not arbitrary descendants
or indefinite kernel stalls. They are prospective ceilings, not measured
performance promises, and do not reopen the closed local 180/420 allowance.

On 2026-10-30, source 9b4e701fb59f3023917d391e7643c172ffe5652a
passed scoped formatting, lint, strict typing and all 60 synthetic policy/report
cases. Independent source review verified the unchanged numerical files and
the report checks. Validation retained its initial formatting failure, mypy
namespace-mapping failure and test-only import failure. The final two corrections
used explicit namespace mapping and a direct standard-library import; no checks
or assertions were weakened. The final pytest selection took 0.34 seconds and
constructed no numerical reference pack.

The cumulative local verification charge, including its retained preparation
hold and prior attempts, is 28.749847867 CPU seconds and 40.132602115 active-wall
seconds within the 60/120 engineering limits. The retained unit occupied
1,368,374 bytes at sealing, below 8 MiB. Its outcome index SHA-256 is
fc9c3b1f17f72c417f1cff4dba2cb8164b9032abd416f28d45d0b4dd372770b9.

Hosted execution on both Python versions remains a separate integration gate.
This partition adds no scientific calibration, available study balance, or
native Laplace implementation claim.
