# Proposed fixed-D1 source manifest and resolver boundary

Design only, based on immutable source
`2f87c51b1c01cae174a880ccd91a0a4eae243f61` (tree
`eb0a0477934d2690321c966ec9bb76ed15cdde9e`). Conditional T retention is
source-accepted; its runtime qualification is pending at this checkpoint.
No S schema implementation, source resolver, A writer, project import, numerical
work or actual authentication is performed here.

The lead-retained private dependency audit has SHA256
`c843709cfa3619c9e37e63342697466cd161639dbd2208ba4dff03d4496a70b8`.
It found no existing complete D1 S producer/resolver. Its private evidence is not
copied into this public document. The [codec contract](D1_PRIMITIVE_CODEC_CONTRACT.md)
and [T-retention design](D1_TABLE_RETENTION_DESIGN.md) retain their limits and
acyclic meaning. All new limits below are **proposed contract ceilings requiring
whole-allocation evidence**, not permission, available balance or an enlargement
of any existing budget.

## What S establishes, and what it cannot establish alone

S is one immutable canonical manifest that identifies the exact reviewed D1
source set, fixed roles, primitive definitions and dispatch bindings. Its local
resolver compares actual bounded source bytes and actual owned Python objects
to an independently trusted expected plan. A self-consistent S, matching hash,
commit string, owner-readable file or typed receipt is not independent authority.

The outer trusted prerequisites are:

* An independently accepted exact commit/tree and **closed complete D1 source
  catalog**, expected S identity and runtime-admission evidence; S cannot select
  its own trusted root, completeness policy or expected digest.
* Held source/runtime roots and a trusted import/installation path for the whole
  controlled interval. Matching a file now does not authenticate already-loaded
  code, monkeypatches or a native function. This is not hostile-Python isolation.
* The actual producer/reference/emitter/recorder objects and a reviewed installer
  that exposes them before any numerical call, preserves their ownership, and
  routes the fixed call sites through the bound dispatch slots without bypass.
* A protected outer admission that joins actual retained S/T/C/A and the complete
  resource/attempt authority before activation. This document supplies none.

Local enforcement can reject malformed bytes, incomplete or substituted catalog
rows, wrong actual files, wrong loaded origins, wrong method/owner identities,
reused oracle objects, unmatched T refs and failed retention/closure. It cannot
infer external approval, historical completeness or the missing runtime proof.

## Small wire contract

Propose schema `strange-physics.d1-source-manifest.v1` and fixed private filename
`source-manifest.json`, outside the unchanged T/sink allowlists. S has exactly:

```text
schema, source_commit, source_tree, protocol_sha256, uv_lock_sha256,
recorder_sha256, codec_sha256, sink_sha256, run_id, recorder_id,
catalog_ref, catalog_sha256, runtime_admission_ref, runtime_admission_sha256,
installation_member_ref, members, definitions, instances, bindings, limits
```

Hashes are lowercase SHA256; commit/tree are 40 lowercase hex characters. The
protocol pin is the frozen `657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399`.
Run/recorder IDs use the existing 1–96 character opaque sink-token lexicon.
Member/catalog/runtime references use 1–32 characters matching
`[A-Za-z0-9][A-Za-z0-9_.:-]{0,31}`. A reference is not a path or capability.
Unknown fields, duplicates, booleans in integer slots, floats, alternate JSON
spellings and coercion through model serialization are rejected.

Use the existing canonical compact sorted-key ASCII JSON convention, with
`allow_nan=False`, UTF-8 and exactly one LF; explicitly not JCS. Before parsing,
require exact immutable bytes of length 1–65,536, bounded depth 3, at most 2,048
JSON nodes and at most 10 characters in an integer token including any sign.
After strict parsing, reserialize and compare exact bytes. Exact per-field integer
ranges reject negative counts or unsupported values; the token guard is not a
permission to choose limits. Strings have the closed lexicons below; no Unicode
normalization or caller-selected encodings are allowed.

The four row arrays have these positional forms:

| Array | Exact row | Completeness/order |
| --- | --- | --- |
| `members` | `[member_id, origin, locator, sha256, byte_length, loaded_module_or_null]` | 1–64 rows, unique IDs, sorted by ID; exact membership/locators must equal the independently expected source catalog. |
| `definitions` | `[definition_id, member_id, kind, module, qualname]` | Exactly d0–d4, in that order; expected definitions below, no S-selected callable discovery. |
| `instances` | `[instance_id, role, case_index_or_null, source_member_ref]` | Exactly i00–i13 in T order, same roles/case mapping and source-binding refs. |
| `bindings` | `[instance_id, primitive_code, definition_id, dispatch_id]` | Exactly 23 rows, ordered by instance then primitive code; fixed mapping below. |

`origin` is exactly `checkout_source` or `trusted_runtime_member`. A checkout
locator is a canonical repository-relative ASCII path, at most 160 characters,
with no absolute path, empty/dot/dot-dot component, backslash or control character.
Its spelling must equal the reviewed catalog; the parser's lexical rule does not
allow new paths. Source byte length is 1–131,072. A runtime locator is an opaque
member ID in the independently verified runtime view, not an S-supplied filename;
its exact hash/size must match that view, with declared size at most 67,108,864.
Runtime bytes are not included inline or freshly read by this source resolver.
Their independent verification and interval validity remain explicit outer work.

`loaded_module_or_null`, definition `module` and `qualname` are fixed catalog
names, ASCII identifiers/dotted identifiers at most 128 characters. No arbitrary
`importlib`, attribute-chain execution or filesystem lookup follows an S string.
The resolver receives actual expected objects from the trusted owner and compares
the closed names/identities. A module origin that is unavailable, ambiguous,
changed or outside its expected source/runtime root fails closed.

`catalog_ref` resolves to the actual verified source-owned catalog member;
`catalog_sha256` matches its bytes and the outer expected catalog. The catalog
must enumerate every project helper/production module/configuration needed by
the final D1 path, not merely the five primitive definitions. It includes the
protocol, lock/config identity, fixture/prefix/bounds/evidence code, recorder,
codec/table/bridge, sink/retention/resolver/installer and final driver/binder
closure. That complete catalog does **not yet exist**. Its source authoring and
review, including missing final driver files, precede sealing a usable S. More
than 64 required members is an explicit failed-fit finding, not permission to
omit members or expand this proposed ceiling automatically.

## Fixed definition and instance joins

Definitions d0–d3 are the actual reviewed `EndpointOracle.position`, `exp`, `log`
and `circle_constant` methods in `endpoint_belief_reference`, all resolved to
that verified source member and its trusted loaded definition objects. d4 is
the single injected native emitter. Its exact reviewed implementation, kind
(`python_function` or `runtime_builtin`), module/member and qualification name
remain a **pre-sealing prerequisite**, fixed by the outer catalog, not chosen by
S at runtime. This proposal does not silently promote `math.exp` or a test lambda
to the scientific emitter. The allowed kinds for d0–d3 are only `python_method`.

Instance rows repeat T's fixed mapping: i00 fixture; i01/i02/i03 strong/weak/future;
i04–i11 arithmetic for M01/M02/M03/M04/D03/F02/F04/W03; i12 constants;
i13 native_emit. All except the eight arithmetic rows have null case indexes.
Every T `source_binding_ref` must equal its S instance row's source member and
resolve to the corresponding definition member. Multiple oracle instances may
legitimately use the same source member. That does not permit shared instance
identity or count fourteen oracles: there are thirteen distinct oracle objects
and one emitter role.

| Instances | Required binding slots | Definition |
| --- | --- | --- |
| i00–i03 | position, code0, once per instance | d0 |
| i04–i11 | exp/code1 and log/code2, per instance | d1/d2 |
| i12 | log/code2 and circle_constant/code3 | d2/d3 |
| i13 | native_exp/code4 | d4 |

This gives `4 + 8*2 + 2 + 1 = 23` actual primitive callable slots and five
underlying definitions. `dispatch_id` is exactly j00–j22 in that row order. It
names a reviewed installer slot under `installation_member_ref`; it is not a
caller-selected callback. The source catalog fixes the actual dispatch function,
its expected capture layout and call-site join. That installer is also pending.

For Python methods, require the exact expected class, actual bound `__self__`
identity, exact independently verified `__func__`/code object and expected
module origin. Reject subclass substitutes, instance-level method overrides,
partial/decorated callables or closures unless the final catalog explicitly
specifies that exact installation object. Compare object identity with `is`,
not dataclass equality; never serialize `id()` or an address as durable proof.
The owner retains strong references through the one attempt. Re-reading source
bytes cannot substitute for the trusted loaded-code provenance requirement.

Resolve the twelve `D1Reference` objects from its actual channels, eight
arithmetic entries and constants member. The fixture oracle is presently a
local created inside `D1FixtureProducer.run`; a narrow reviewed pre-call
installation hook is needed to expose/bind that same object. Do not create a
second oracle, reset counters/cache, invoke a method as an identity probe or
assume the fixture object was bound before it existed. Unused initial counters
and empty caches may be checked without numerical evaluation, but those state
checks are not proof of past execution history.

The dispatch wrapper itself must also be the independently verified installer
function/code with its exact expected captures (original callable, actual owner,
recorder and fixed slot). After installation, verify that the actual consumer
holds that same wrapper and its preserved original; checking only an unused
correct method would not establish routing. Hold those references and recheck
slot/owner identity at the reviewed dispatch boundary without extra primitive
calls. This requires concrete source hooks and remains unimplemented here.

Native binding must cover only the exact injected `emit(native_log_probability)`
in `qualify_prefix`. The native normalizer's separate internal exponentials are
not additional recorder slots. Cache hits, first-consumer scopes, prequential
reuse and full call order still require the external driver/binder witnesses;
S establishes none of those by enumerating roles.

## Resolver and sealing sequence

The narrow pure parser returns an immutable view of **raw S bytes**. Constructed
views are never validation inputs. A separate local resolver takes those bytes,
the independently supplied closed expected plan/runtime view, held source roots
and actual owned object map. It performs no primitive call, provider request or
S-selected import. Its result is transient resolved references plus observed
byte identities, not transferable authority or a new release framework.

Source reads use independently owned pinned root/ancestor descriptors, exact
catalog-relative names and no-follow regular single-link files. Checkout source
must be owned by the expected user and not group/world writable; public source
mode0644 is not confused with private retained S mode0600. Check fd/name identity,
exact declared length and before/after extent/mtime/ctime, with one explicitly
counted overflow probe and once-only read-fd close. A path-only preliminary
`resolve()` check is insufficient. Preserve primary read errors before
supplemental close uncertainty. These are bounded current observations under the
held-root premise, not historical continuity or hostile concurrent-mutation proof.
The final implementation must account for every ancestor/open/stat/close action.

1. The outer owner fixes the final source catalog, runtime evidence, emitter and
   installation code; holds actual roots and supplies the expected objects.
   Verify the closed source/member set against that expectation, with real
   bounded reads and the independent loaded-code provenance premise.
2. Inspect and bind the actual owned roles before their first primitive call;
   check all 23 definition/owner/dispatch slots. No global monkeypatch of the
   underlying numeric functions is an acceptable replacement for exact hooks.
3. Build strict S bytes from observed members and the fixed plan, then retain
   once in its own owner-private source-evidence root. Use exclusive no-follow
   file creation and separately owned pinned descriptors, direct bounded write,
   file/directory fsync, exact bounded readback and once-only close. A full
   reservation remains charged after partial write or uncertain close.
4. Only after actual S readback/closure succeeds may T/C bind its actual SHA(S).
   Keep the dependency graph `source/runtime evidence -> S -> T/C -> A`. S
   contains no S/T/C/A digest, future terminal hash or self-referential receipt.
   Its member hashes refer to immutable source/runtime files, not generated
   downstream metadata. Any earlier runtime/catalog evidence referenced by S
   must also be free of S/T/C/A hashes; the later outer admission is a distinct
   artifact and cannot be used to manufacture a backward dependency. Source
   catalog/installer code likewise cannot embed the
   future generated S digest as a required self-pin.
5. A separately admitted outer resolver must revalidate retained S and current
   source/runtime/object joins before any later A retention/activation. This
   proposal allows at most two S/source validation passes, described below;
   additional passes are a new census/fit issue, never an invisible retry.

A failed preflight, source read, binding, retention, readback or close consumes
that sealing/verification opportunity. Preserve entered/partial/unknown state,
original error and bounded supplemental cleanup facts. Independently close
remaining owned fds once; never retry an ambiguously closed descriptor, delete
partial S or infer acknowledgement from parseable bytes. Constructor failure
before an owner object returns may leave created artifacts and uncertain closes.
No T/C/A or primitive is authorized by failure. External attempt registration,
controller receipts and no-retry enforcement remain required; this design does
not invent their schema or budget.

## Proposed finite byte/read/copy ceilings

The `limits` object has exactly these integer declarations; the parser compares
against the source-owned constants rather than accepting caller policy:

```text
manifest_bytes=65536, header_bytes=4096, row_with_separator_bytes=512,
source_members=64, definitions=5, instances=14, bindings=23,
source_file_bytes=131072, loaded_source_copies=64,
validation_passes=2, json_depth=3, json_nodes=2048,
integer_token_chars=10, retained_source_copies=0, retained_manifest_copies=0
```

Header H is the canonical complete S with all four row arrays empty, including
root/limits punctuation and LF. H<=4,096. Each row's exact canonical bytes plus
one separator reserve is <=512. Thus the maximum structural envelope is
`4096 + (64+5+14+23)*512 = 58,368 <= 65,536` bytes. Row/header validation and
actual extrema need independent tests; this is arithmetic, not measured fit.

Each source pass admits at most 64 checkout source files and at most 64 actual
loaded project/helper source copies, each with 131,072 accepted bytes plus one
explicit overflow-probe byte. Repeated physical reads count again even when
digests match. Same-file aliases can avoid a duplicate read only after actual
fd/name identity and held-root conditions are established; the ceiling assumes
no such saving. Two passes plus two S reads with their one-byte probes give:

```text
2 * (128 * 131073 + 65537) = 33,685,762 maximum attempted payload-read bytes.
```

Source files are read serially; there is no retained source bundle or copied
checkout. The newly retained S file reserves at most 65,536 bytes, including a
failed partial file. No export/temporary manifest copy is permitted by this
proposal; introducing one requires explicit within-allocation accounting.
Original input S, parser objects/canonical temporary, read chunks/join and
result-held references are separate memory operands, not additional disk
permission or a proven heap/time limit. Control/failure records, directory
blocks and existing source/runtime retention still require aggregate accounting.
The T/A 65,536 pool and its separate copy reservation cannot be borrowed for S.

A `trusted_runtime_member` is resolved against independently observed native/
interpreter evidence; it does not cause a new native-binary read under the
131,072 source-file ceiling. If that proof is absent, stale or not valid for the
held interval, verification stops. Any fresh runtime/dependency/archive scan is
separate explicitly bounded outer work and must be included in the complete
allocation; it cannot be relabeled free metadata or assumed covered by this
33,685,762-byte source-read ceiling.

## Existing checks remain scoped, and repeated work remains charged

`d1_fixture_reference.verify_sources` checks seven ordered checkout files and
four loaded production copies, each via a 131,073-byte attempted read. That is
up to **1,441,803 attempted read bytes per call**. The producer calls it initially
and again after construction; `candidate_materials` can call it again. The full
frozen driver's exact recheck count remains a required census. This S proposal
does not remove or silently deduplicate those checks: add
`1,441,803 * actual_verify_sources_call_count` to the attempted-read ceiling
when they run, preserving failed calls too. A verified S is not a drop-in cache
waiver for existing independent boundaries.

`verify_native_installation` requires independently trusted build evidence and
checks installed/runtime bytes within its own larger bounds. Its admitted
snapshot/closure can be an outer premise, but it neither covers the complete
D1 helper/owned-object graph nor supplies this manifest's authority. Release
`ci_artifacts` provenance and literature-admission parser limits are likewise
not substitutes or transferable S budgets. Costs of all existing/failed units
and unknown historical scientific usage stay retained; no fresh balance follows.

## Small source slices and unresolved prerequisites

First implement only bounded S wire/catalog comparison and synthetic negative
cases: duplicate/unknown fields, noncanonical bytes, booleans, depth/token/size
limits, reordered/missing/extra members, mismatched row/header identities and
all 14/23 joins. Independent literal fixtures should distinguish lexical
consistency from actual resolution. This source work needs no numerical output.

Next review the bounded owned-file resolver and source/loaded-origin checks,
with fake callable owners and owned temporary source files. Cases must reject
wrong roots, substituted/hardlinked/changed files, incomplete catalog, two roles
sharing one oracle, wrong bound self/function, stale/missing runtime evidence,
missing fixture hook and unapproved emitter. Retention/cleanup fault tests must
preserve original-plus-supplemental errors and forbid downstream activation;
no primitive is called to establish any identity.

Before a usable S can be sealed, separately finish and independently review:

* The complete final D1 source catalog and trusted loaded-source/runtime
  provenance, including actual callable definitions; their completeness cannot
  be delegated to the manifest being checked.
* The fixture pre-call ownership hook, exact emitter selection and complete
  installer/dispatch/capture plan; current sources do not already supply these.
* Actual S/parser/member fit, all source/recheck/runtime read counts, retention,
  copies/memory and failure/closeout costs inside the full unchanged allocation.
* The protected outer S/T/C/A admission join and fixed one-attempt authority.

These are concrete source and evidence prerequisites, not additional scientific
experiments or a new study agenda. No A construction/retention, source authority,
scientific allocation, calibration result or whole-science fit is claimed here.
