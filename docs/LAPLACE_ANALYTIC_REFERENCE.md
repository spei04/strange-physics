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

## Planned validation and limits

The handwritten source declares 24 cases: eight fixed vectors, five exact
relations, four plausible-defect checks, five closed-domain/work failures,
and two semantic examples. It generates the successful reference table once.
Four invalid build attempts reject before reference arithmetic; one exhausted
attempt stops during constant preparation. Tiny-input guards check allocation
and GCD exhaustion without constructing a maximal-sized integer.

Each vector records its input digest, exact-enclosure width, directed
normalizer bounds, and binary64 error before numerical assertions. The fixed
software comparison criterion is `2e-12` absolute error; this is a proposed
test criterion, not a universal standard-library guarantee or scientific
tolerance. Jacobian, density-versus-cell, support clipping and omitted
remainder defects have explicit sensitivity checks.

This source-only checkpoint has not been imported, collected or executed.
Formatting, typing, actual work counters, CPU/memory fit and numerical outcomes
remain to be verified under a separately bounded run. No endpoint package,
schema, production code, dependency, study allocation or task graph changes
are part of this pack. Later comparative Laplace acceptance still requires
shared accepted continuous prior/likelihood semantics, derivative and boundary
policies, independent fixtures and justified grid resolution. An unvalidated
grid is not ground truth.
