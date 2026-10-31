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
allow new paths. Ordinary checkout source byte length is 1–131,072, including the
catalog. Exactly one mandatory member has origin `checkout_source`, the literal
canonical locator `uv.lock`, and `loaded_module_or_null=null`. Only that row may
have length 1–262,144 under the fixed `lock_file_bytes` limit, and it occupies one
of the existing 64 member slots. Its hash must equal root `uv_lock_sha256`, the
SHA256 of the actual bounded lockfile bytes and the independently protected
expected lockfile hash; its length must equal the actual and protected expected
byte lengths.
Reject an omitted, duplicate or aliased lock row, an alternate origin/locator,
a non-null loaded module, or a second member resolving to that same lockfile.
Matching declaration strings alone do not establish any of these actual joins.
No other source or loaded copy receives the lock-specific ceiling.

The following root pins also require exactly one declared `checkout_source` row
at each literal canonical locator. Require unique member locators and the exact
loaded-module declaration shown; that member's declared hash must equal the root
pin. These are declaration joins, not observations of actual/protected bytes or
loaded objects. The fixed protocol hash above remains mandatory.

| Root pin | Required canonical locator | Loaded module |
| --- | --- | --- |
| `protocol_sha256` | `docs/research/RA_N03_CALIBRATION_SLICE.md` | null |
| `recorder_sha256` | `tests/d1_primitive_recording.py` | `d1_primitive_recording` |
| `codec_sha256` | `tests/d1_primitive_codec.py` | `d1_primitive_codec` |
| `sink_sha256` | `tests/d1_primitive_sink.py` | `d1_primitive_sink` |

The separate literal `uv.lock` row retains its null module and root-hash rule.
Actual/protected source identities and filesystem aliases remain resolver duties.

A runtime locator is an opaque member ID in the independently verified runtime
view, not an S-supplied filename;
its exact hash/size must match that view, with declared size at most 67,108,864.
Runtime bytes are not included inline or freshly read by this source resolver.
Their independent verification and interval validity remain explicit outer work.

`loaded_module_or_null`, definition `module` and `qualname` are fixed catalog
names, ASCII identifiers/dotted identifiers at most 128 characters. No arbitrary
`importlib`, attribute-chain execution or filesystem lookup follows an S string.
The resolver receives actual expected objects from the trusted owner and compares
the closed names/identities. A module origin that is unavailable, ambiguous,
changed or outside its expected source/runtime root fails closed.

### Acyclic catalog policy and exact comparison boundary

`catalog_ref` names a source-owned **policy file**, not another source-hash
manifest. Choose the simplest acyclic representation: no file digests, sizes,
source commit/tree values or generated S/T/C/A/terminal hashes appear inside the
catalog, including for its own member. Its own actual byte digest is pinned by
the independently trusted outer source plan and by S's `catalog_sha256` and
corresponding member row. Those two S declarations must match each other and the
actual catalog bytes. There is no catalog self-hash to solve.

The minimal catalog has exactly `schema` (literal
`strange-physics.d1-source-catalog.v1`), `members`, `definitions`, `instances`,
`dispatch_policy`, and `installation_member_ref`. It uses the same canonical
compact ASCII encoding, strict types and bounded name/reference lexicons. As a
source member its complete bytes remain within 131,072; no separate parser or
retention allowance is borrowed. For the first pure-parser slice, explicitly
apply the same predecode depth3/node2,048/integer-token10 guards to catalog bytes,
counting containers, object keys and scalar values before decoding. The token
limit includes any minus sign. Apply the same4,096-byte empty-row header and
512-byte row-plus-separator ceilings; the catalog has no `limits` object. This
prospective parser clarification adds no source member, validation pass, retained
copy or allocation. Its closed rows are:

| Array | Policy row / comparison |
| --- | --- |
| `members` | `[member_id, origin, locator, loaded_module_or_null]`, sorted unique IDs, at most64; includes the catalog's own ID/path and the complete D1 source closure, but no hashes/sizes. |
| `definitions` | The same five definition rows as S, with exact member/kind/module/qualname policy. |
| `instances` | The same fourteen instance rows as S, including legitimate repeated member refs. |
| `dispatch_policy` | `[instance_id, primitive_code, definition_id, dispatch_id, wrapper_member_id, wrapper_qualname, consumer_member_id, consumer_qualname, capture_layout]`, exactly23 in fixed slot order. |

`capture_layout` is a closed source-owned tag, proposed as
`bound_method_recorder_slot_v1` or `native_callable_recorder_slot_v1`. The first
requires the original bound method, exact owner, actual recorder and fixed slot;
the second requires the original emitter, actual recorder and fixed slot. The
installer/resolver must freeze their precise object fields/closure positions and
wrapper/consumer definitions before use. Tags are not instructions to evaluate
arbitrary attribute paths or dynamic imports. That implementation is pending.

The comparison boundary is exact: project every S member onto its four policy
fields and require equality with catalog `members`; require S definitions and
instances to equal those arrays; require every S binding to equal the first four
fields of the corresponding dispatch-policy row. The installer member must
match. Independently compare each S file hash/length with actual bounded bytes
and the protected expected source/runtime pins, including the catalog's own
bytes. Policy equality alone never authorizes a file digest or establishes
loaded-code provenance. Wrapper/capture/consumer fields are compared to actual
objects only in pass2 below, not invented in pass1.

The complete catalog must enumerate every helper/production module/configuration
needed by the final D1 path, not merely the five primitive definitions. This
includes protocol, lock/config identity, fixture/prefix/bounds/evidence code,
recorder, codec/table/bridge, sink/retention/resolver/installer and final
driver/binder closure. That catalog does **not yet exist**. Its source authoring
and review, including missing final files, precede usable S sealing. More than64
required members is a failed-fit finding, not permission to omit members or
increase the proposed ceiling automatically.

A bounded static audit at `e63d8eae0a77566f3ce1c29adff973aec3cf05b2` found
47 candidate members (44 Python files), including the known native implementation
and installation-check imports, deferred imports, protocol and lock/config.
This is a conservative current-known set, **not the complete final catalog**;
resolver, installer, driver/binder, emitter selection and runtime-member joins
remain unfinished. The actual `uv.lock` is 250,735 bytes, SHA256
`45ea41dd4302e48ecaf42178e094a2e15aa19fa0506d4a36ece6f886920bc838`;
it exceeds the former uniform 131,072-byte proposal by 119,663 bytes. The largest
known Python member is `tests/d1_prefix_evidence.py` at 69,136 bytes. This finding
motivates only the literal-lock exception above, not a general source-cap increase
or proof that future members fit. The private audit remains retained unchanged;
its metadata does not authenticate sources or authorize their use.

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

In pass2, after the real S-bound T/C, Bridge and Recorder exist, the dispatch
wrapper must also be the independently verified installer function/code with
its exact expected captures (original callable, actual owner,
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

1. **Pass1: source/runtime and originals.** The outer owner fixes the final catalog,
   runtime evidence, emitter and installation code, holds actual roots and
   supplies the original owned objects. Validate bounded source/member bytes,
   trusted loaded-code provenance and the same thirteen oracle objects/emitter
   with all23 original definition/owner slots. Compare the **declared dispatch
   policy** with the reviewed catalog. Do not claim an actual recorder capture,
   wrapper or consumer route has already been verified.
2. **Seal S.** Build S from those observed bytes/originals and fixed policy, retain
   once in its private source-evidence root, with direct bounded write,
   file/directory fsync, exact bounded readback and once-only close. A full reservation remains charged
   on partial write or uncertain close. The actual readback is the first of the
   two admitted S-file reads; source-pass1 bytes are not silently read again.
3. **Construct the real downstream objects, without invoking them.** Retain actual
   C/T binding the retained SHA(S). Then construct the real `CodecAppendBridge`
   from that T/C and the owned sink append callback; construct the real
   `PrimitiveRecorder` with the bridge's synchronous append callback; install
   the reviewed wrappers capturing that recorder and the held originals. This
   order is necessary: Recorder requires append, and Bridge requires T/C whose
   source-manifest fields already bind S. No deferred/stub append callback,
   temporary recorder, replaced oracle, reset or resealed S is allowed. Constructed
   objects are not activated; no Event or primitive is invoked.
4. **Pass2: current bytes, originals and actual installation.** Re-read retained S
   and revalidate held source/runtime premises and original owner/definition
   identities against pass1 and the external expected plan. Check actual wrapper
   code/captures, the real Recorder/Bridge/sink callback chain and the actual
   consumer routing against all23 dispatch-policy rows. Original references are
   retained throughout; checking a separate unused correct callable is not
   sufficient. Any missing fixture hook, stale runtime proof, substituted owner,
   callback/capture or bypass fails before A/admission.
5. **Only after both passes:** a separate later slice may construct/retain candidate
   A and obtain the protected outer S/T/C/A admission before activation. Source
   and runtime evidence -> S -> C/T -> real Bridge/Recorder/wrappers -> pass2 ->
   candidate A/outer admission is the construction order. The hash graph remains
   S -> T/C -> A; actual wrapper identities are transient resolved references,
   not new fields that require rewriting S. S contains no self/T/C/A/future
   terminal digest. Earlier catalog/runtime evidence cannot contain those later
   hashes either; the final outer admission is a distinct artifact.

The same two source/S validation passes and byte ceilings below apply. Installing
wrappers and checking actual captures/routing is additional explicitly counted
non-numerical work, not a third source pass or free work. No new primitive call,
source retry, catalog reseal or bypass is implied. A global numerical-function
monkeypatch is not a substitute for the reviewed exact call-site installation.

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

The `limits` object has exactly these 16 integer declarations; the parser compares
against the source-owned constants rather than accepting caller policy:

```text
manifest_bytes=65536, header_bytes=4096, row_with_separator_bytes=512,
source_members=64, definitions=5, instances=14, bindings=23,
source_file_bytes=131072, lock_file_bytes=262144, loaded_source_copies=64,
validation_passes=2, json_depth=3, json_nodes=2048,
integer_token_chars=10, retained_source_copies=0, retained_manifest_copies=0
```

Header H is the canonical complete S with all four row arrays empty, including
root/limits punctuation and LF. Adding the fixed `lock_file_bytes` key/value
contributes 25 canonical header bytes (including its comma); H<=4,096 remains
unchanged. Each row's exact canonical bytes plus one separator reserve is <=512.
Thus the maximum structural envelope is
`4096 + (64+5+14+23)*512 = 58,368 <= 65,536` bytes. Row/header validation and
actual extrema need independent tests; this is arithmetic, not measured fit.

Each source pass admits at most 63 ordinary checkout source files at 131,072
accepted bytes each, the one mandatory checkout `uv.lock` at 262,144 bytes, and
at most 64 actual loaded project/helper source copies at 131,072 bytes each.
The lockfile is not a loaded module. Every read has one explicitly counted
overflow-probe byte. The source-member maximum remains 64; runtime-member rows
occupy that same maximum rather than creating extra checkout slots. Repeated
physical reads count again even when digests match. Same-file aliases for ordinary
source/loaded-copy reads can avoid a duplicate read only after actual fd/name
identity and held-root conditions are established; lock-member aliases remain
rejected. The ceiling assumes no read savings. Two passes plus two S reads give:

```text
2 * (63 * 131073 + 262145 + 64 * 131073 + 65537)
= 2 * (127 * 131073 + 262145 + 65537)
= 33,947,906 maximum attempted payload-read bytes.
```

The lock-only correction adds 262,144 attempted read bytes over the former uniform
source-file formula. It does not add a source member, loaded-copy slot, validation
pass, retained source copy or budget. Actual row/header/manifest fit remains
unqualified; the fixed structural reservations above are unchanged.

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
33,947,906-byte source-read ceiling.

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
all 14/23 joins. Lock-specific cases must reject omitted/duplicate/aliased rows,
wrong origin or locator, non-null loaded module, wrong root hash or actual/protected
hash/length joins, and any ordinary/catalog/loaded source attempting to use the
larger lock ceiling. Test the exact 16 limit keys and unchanged header/row/manifest
bounds without treating this proposal as actual-fit evidence.
Independent literal fixtures should distinguish lexical
consistency from actual resolution. This source work needs no numerical output.
The first interface is only `parse_manifest(raw)`, `parse_catalog(raw)`, and
`compare_declarations(manifest_raw, catalog_raw)`. Each comparison reparses exact
raw bytes and returns immutable output-only views; constructed views do not enter
validation boundaries. Compare the root/member declarations above and exact
catalog projections, fixed definitions/instance/slot joins and capture-layout
tags. Raw T identity/reference comparison is deferred to a separate boundary;
this parser does not authenticate a supplied catalog or select a scientific emitter.

Next review the bounded owned-file resolver and source/loaded-origin checks,
with fake callable owners and owned temporary source files. Independently test
that catalog projection comparison contains no self-hash dependency, pass1
cannot assert actual recorder capture, and pass2 rejects substituted real callback
chains or wrappers after S-bound T/C construction. Cases must reject
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
