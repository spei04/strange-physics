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

## Bounded interface and pending checks

Public JSON is limited to 32 KiB; private audit/inventory messages to 1 MiB.
An inventory contains at most 1,024 supplied rows. These are parser bounds, not
the D1 study's output allocation or a claim that all history fits one file.
A producer encountering excess must stop and propose an explicit partition
without dropping entries; this checkpoint provides no partition-completeness
claim. Existing bounded parsing rejects duplicate JSON keys, oversized nesting,
nonfinite values, out-of-range hexadecimal exponents and extra fields.

The schema function labels public versus private roots. The source generator
\`scripts/generate_calibration_fixture_schema.py --output-dir DIRECTORY\` emits
schema JSON plus arbitrary structural examples; its default is \`contracts/\`.
It imports no oracle, predictor or test helper. The schema audit registration,
archive module allowlist and persisted-schema byte/example parity tests are
authored. Running generation, independent schema validation and tests remains
pending the next engineering step. No tests or project imports were run while authoring
this checkpoint. Test endpoints are arbitrary legal structural values, not
reference-generated D1 truth; the five actual reference-oracle methods are
poisoned in the authored test fixture.

The historical Q1 files, CORE contracts, NativeWorldCatalog, scientific gates,
prior costs and reservations are unchanged. The future D1 generator, exposure
inventory production/review, numerical/CDF/quantile/score proofs, runner,
complete operation/output census and execution allocation remain separate work.
