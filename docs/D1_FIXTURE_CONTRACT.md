# D1 fixture contracts — source checkpoint

This is unit 1 of [RA-N03-D1](research/RA_N03_CALIBRATION_SLICE.md), pinned to
protocol SHA-256
`657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
It supplies bounded data contracts and joins only. It generates no endpoint,
reference, prediction, score, numerical certificate, run authority or fixture
freeze. Source authoring is authorized; no new numerical allocation follows.

## Separate audiences

`D1PublicFixture` contains an existing CORE `ObservationBundle` and common
synthetic terminal-x/unused-velocity labels. The candidate projection explicitly
reconstructs only CORE's public fields. It accepts the public type only, rechecks
its bounded JSON (including nested model-copy/construct bypasses), and never copies a private envelope with an exclusion list.

All eight cases use the same synthetic engine version and protocol fingerprint.
The fingerprint identifies the synthetic protocol, not a simulator execution.
Run and operation IDs have an opaque token grammar. The trusted producer must
issue those IDs independently of hidden case/coefficient/regime information and
keep the blueprint mapping private. Grammar alone cannot prove that arbitrary
caller strings contain no covert information. Public protocol authors already
know the blueprint; this is not a claim of human-blind data.

`D1PrivateAudit` alone joins a fixed blueprint, true coefficient metadata,
reference/rounding evidence references, training label claims, future answer and
the exact canonical public-envelope digest. These are supplied claims, not
proof that reference work happened. `validate_fixture_binding` checks public
bytes/shape/labels after revalidating nested private models; later numerical qualification must verify the actual
reference artifacts and one-rounding argument.

Private `D1FixtureOutcome` rows retain every planned construction as unrun,
failed or materialized. Failed construction does not become a fake completed
trajectory or a simulator-failed purchase. The complete outcomes envelope fixes
the eight-case order; `validate_materialized_fixtures` binds exactly the available
public subset using normalized revalidated objects and checks matched/repeat/weak future labels among every available member, even when M03 is unavailable. It preserves every
unavailable row. There is no Journal adapter or purchase authority.

## Structural constraints

The fixed protocol table is private construction metadata: four matched worlds,
one duplicate, two omitted-force controls and one weak-excitation control; 40
belief profiles across the declared grids/scales. Public input has one mass-1
particle, anchor zero, explicit zero impulse, zero initial velocity and declared
noise, duration/sample interval 0.5, dt 1/64 and exactly two frames. Terminal
velocities are unused zero placeholders. CORE validates legal actions, ordinal
continuity and distinct operation IDs; the D1 layer checks its exact narrower
shape and generic provenance.

The only two-record prefix repeats the same physical experiment and trajectory
with its distinct CORE ordinal/operation. All materialized D1 envelopes must have distinct run IDs, and operation IDs must also be globally distinct across those envelopes (CORE alone checks only within a run). The paired fixtures reuse physical construction values, not operation identities. Pairing with M03 is a separate private
join, not a public blueprint lookup. F remains a synthetic omitted-force fixture;
it cannot claim the unchanged simulator produced it.

## Supplied-inventory exposure checks

Private canonical signatures separate physical world, ordered observed history,
actions and future query. They exclude case/run/operation/display IDs and
reference-proof file identities. A matching world is flagged even if a supplied
entry uses different history, action order or identifiers; an exact full
construction match is also retained. Signed zero has one physical-signature encoding; chronological history order remains meaningful, while world overlap is independent of that order. D03's deliberate within-development repeat
never grants a cross-split exception. Reserved-comparison checks additionally reject any of the four coefficient values, even if a mechanism or action changes; the reservation is not limited to the currently queried case.

`check_supplied_inventory` compares only the supplied private D1-codec signatures.
It returns their actual denominator, overlap count and first matching indices.
An empty or incomplete inventory can only yield
`no-overlap-in-supplied-inventory`, never historical disjointness. Producers of
earlier fixture/comparison signatures must normalize the actual physical
material to this codec and retain source evidence. This module does not discover
or authenticate those inventories, and does not claim to handle arbitrary
world families.

`D1OwnerReviewReference` is a pointer to external independent review, not a
signature, grant or validator of historical completeness. Before numerical
admission, retain complete development and reserved-comparison inventories,
bind every materialized fixture to them, obtain the separate owner's review,
and exclude the four reserved coefficient values and eight paired construction blueprints from untouched study data; this is not exclusion of all linear-spring laws.
Neither an `externally-reviewed` string nor successful parsing closes RA-N03.

## Bounded interface and engineering checks

Public JSON is limited to 32 KiB; private audit/inventory messages to 1 MiB.
An inventory contains at most 1,024 supplied rows. These are parser bounds, not
the D1 study's output allocation or a claim that all history fits one file.
A producer encountering excess must stop and propose an explicit partition
without dropping entries; this checkpoint provides no partition-completeness
claim. Existing bounded parsing rejects duplicate JSON keys, oversized nesting,
nonfinite values, out-of-range hexadecimal exponents and extra fields.

The schema function labels public versus private roots. The source generator
`scripts/generate_calibration_fixture_schema.py --output-dir DIRECTORY` emits
schema JSON plus arbitrary structural examples; its default is `contracts/`.
It imports no oracle, predictor or test helper. The schema audit registration,
archive module allowlist and persisted-schema byte/example parity tests are
included. Test endpoints are arbitrary legal structural values, not
reference-generated D1 truth; the five actual reference-oracle methods are
poisoned in the test fixture.

At source `0b9f39f4ce5ba02cdc0ebc4e5dd687ed5427141d`, focused cloud checks
passed formatting, lint, strict typing across 195 files and all 76 contract
cases (228 setup/call/teardown phases). Structural generation produced six
valid, nine schema-negative and five runtime-negative examples. The test
receipt records zero forbidden calls. Fixed future position `1.0` and time
`0.75` have equal minimum/maximum constraints, with both runtime and schema
negative cases.

The first typing attempt failed on unsupported floating-point `Literal`
annotations; the fixed-value repair then passed. Two attempts at the full schema audit
ended at CPU limits before a child receipt was available. Their
internal progress is unknown and neither establishes schema-audit acceptance.
Both failures remain retained. The unchanged source and environment were
verified after each closed attempt. Subsequently, all six required jobs in
[PR #138 CI](https://github.com/spei04/strange-physics/actions/runs/41152465569)
passed on head `8b7704a85a42052f4d68718467844d82cf1e1379`: each Python 3.12/3.14
job passed 4,966 ordinary tests, 1,567 schema checks, package inspection and
CLI smoke; each separate analytic job passed 24 cases. Security and the final
gate passed. This closes the configured engineering checks for unit1, while
retaining the failed local audits. The protected-main release candidate was
correctly skipped; this is not a release or production-readiness claim.

The local engineering unit is closed to further execution: measured process
CPU plus five retained closeout reservations charged 118.962146 of 120 CPU
seconds; active wall plus reservations charged 148.230369 of 300 seconds.
Reservations are not measured consumption. External control/authoring CPU
remains unknown, so these totals are not whole-operation cost. This ledger
does not replenish earlier scientific allocations.

The historical Q1 files, CORE contracts, NativeWorldCatalog, scientific gates,
prior costs and reservations are unchanged. The future D1 generator, exposure
inventory production/review, numerical/CDF/quantile/score proofs, runner,
complete operation/output census and execution allocation remain separate work.
