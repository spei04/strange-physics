# Contract tooling checkpoint

VAL1 starts with an explicit inventory and compatibility vectors. Bundle
generation, drift CLI/CI integration, TypeScript execution and mock transports
are not implemented by this first checkpoint.

The authoritative contracts remain their existing schema, OpenAPI and Python
files. The tooling manifest pins their actual bytes, names every approved root
and records all 51 operations in the seven non-draft OpenAPI files. Static
OpenAPI is an authored input to validation/projection; it is not claimed to be
generated from, or served by, an HTTP implementation.

The additional control-v1 CreateRunRequest, RunCreationResult, RunView,
Operation and ModelReceipt roots are approved messages only. No route from
`contracts/draft/openapi.json` is included or frozen. Operation can carry a full
scientific result: it is not a 64 KiB WEB event projection. Its result/error
closure and semantic validators remain required.

## Audiences and closure

The manifest is an exact allowlist, not a wildcard export of co-located
`$defs`. The later generator must resolve the complete reachable closure of
each approved root using only registered local sources. Private roots that are
not explicitly listed cannot become entry points. A type name alone is not a
classification rule: accepted service metadata legitimately includes
GrantAuthority, while trusted current-authority projections remain private.

Audience labels distinguish browser authentication material, one-time secrets,
owner management, explicit world author input, granted private definitions,
run-viewer data, purchased observations, prediction traffic and evaluator-only
development diagnostics. They describe intended handling, not current access.
Agent-safe structure does not grant permission to view a run. Opaque checkpoint
state is agent-supplied JSON; arbitrary contents are not certified safe to publish.
No preview/owner/author role automatically grants private truth access.

## Byte vectors and validation layers

The synthetic fixture file stores original bytes as base64 with their raw
SHA-256. This preserves numeric lexemes, UTF-8 and malformed input without a
lossy JSON-value round trip. Successful direct typed parsing has separate exact
canonical bytes and SHA under `strange-physics.python-json.v1`: every normalized
field/default/null, sorted Python code-point keys, compact ASCII-escaped JSON,
and nonfinite rejection. This is not JCS or JavaScript JSON.stringify.

Each case names independent expectations for strict JSON syntax/representability,
JSON Schema structure, direct typed parsing, complete bounded typed ingress,
canonicalization and, where needed, a cross-message helper. Null schema
expectations mean strict JSON decoding was rejected and structural validation
was not assessed. Canonical bytes are derived from direct typed parsing, even
when strict ingress rejects the raw input; they do not imply ingress acceptance.

Existing opaque JsonValue parsing preserves integer versus float identity:
`1` differs from `1.0`, and `-0` becomes integer zero while `-0.0` retains its
sign. Typed Number fields normalize integral inputs to floats. Underflow and
subnormal behavior remains the existing binary64 behavior. Direct opaque
Pydantic parsing can accept nonfinite values that strict ingress and canonical
encoding reject. The fixtures record these different layers without changing
CORE. Unicode normalization is not performed; astral/BMP key ordering follows
the frozen Python profile.

WORLD seed strings cover the exact uint64 range without JS Number conversion.
ART generation strings have their own broader range. Failed scientific records
remain in the purchased prefix/hash; an all-failed fit input is rejected, and a
model selecting a failed record is rejected by the actual-prefix helper.
An unscorable evaluation report retains null primary metrics rather than an
average over surviving predictions. Neither fixtures nor schema validity prove
numerical accuracy, storage authenticity or authorization.

## Remaining VAL1 work and later units

After independent acceptance of this manifest/fixture checkpoint, VAL1 will add
deterministic offline closure generation, explicit unsupported-root/reference
errors, check-mode drift detection and CI integration. The existing
workspace/invitation status annotations will be reconciled with schema equality
excluding that metadata. No product contract shape changes are planned.

VAL1 uses the existing uv 0.11.21 and lockfile, with no added dependencies.
CLIENT1 separately requires reviewed Node/TypeScript/Ajv/runtime/license pins
and a byte-preserving cross-language strategy. MOCK1 separately supplies bounded
deterministic HTTP/SSE behavior. Neither unit is completed by these vectors, and
no mock or contract test establishes deployed security, load capacity or
production readiness. All SP-01.e prerequisites and exact integration gates
remain in force.
