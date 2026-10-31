"""Bounded source-manifest declarations; no source reads or authentication.

Only raw immutable bytes enter validation boundaries. Returned frozen views are
output-only descriptions, never independently trusted catalog/runtime evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal, NoReturn

MANIFEST_SCHEMA = "strange-physics.d1-source-manifest.v1"
CATALOG_SCHEMA = "strange-physics.d1-source-catalog.v1"
PROTOCOL_SHA256 = "657c3c74346aedb165473b4672ed18ba5671da82e4873a2a3e6f514b58387399"
MANIFEST_BYTES = 65_536
CATALOG_BYTES = 131_072
HEADER_BYTES = 4_096
ROW_BYTES = 512
MAX_NODES = 2_048
MAX_DEPTH = 3
INTEGER_TOKEN_CHARS = 10
LIMITS = (
    ("manifest_bytes", 65_536),
    ("header_bytes", 4_096),
    ("row_with_separator_bytes", 512),
    ("source_members", 64),
    ("definitions", 5),
    ("instances", 14),
    ("bindings", 23),
    ("source_file_bytes", 131_072),
    ("lock_file_bytes", 262_144),
    ("loaded_source_copies", 64),
    ("validation_passes", 2),
    ("json_depth", 3),
    ("json_nodes", 2_048),
    ("integer_token_chars", 10),
    ("retained_source_copies", 0),
    ("retained_manifest_copies", 0),
)
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,31}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\Z")
Origin = Literal["checkout_source", "trusted_runtime_member"]
Kind = Literal["python_method", "python_function", "runtime_builtin"]


@dataclass(frozen=True, slots=True)
class MemberPolicy:
    member_id: str
    origin: Origin
    locator: str
    loaded_module: str | None


@dataclass(frozen=True, slots=True)
class SourceMember:
    policy: MemberPolicy
    sha256: str
    byte_length: int


@dataclass(frozen=True, slots=True)
class Definition:
    definition_id: str
    member_id: str
    kind: Kind
    module: str
    qualname: str


@dataclass(frozen=True, slots=True)
class Instance:
    instance_id: str
    role: str
    case_index: int | None
    source_member_ref: str


@dataclass(frozen=True, slots=True)
class Binding:
    instance_id: str
    primitive_code: int
    definition_id: str
    dispatch_id: str


@dataclass(frozen=True, slots=True)
class DispatchPolicy:
    binding: Binding
    wrapper_member_id: str
    wrapper_qualname: str
    consumer_member_id: str
    consumer_qualname: str
    capture_layout: str


@dataclass(frozen=True, slots=True)
class ManifestIdentity:
    source_commit: str
    source_tree: str
    protocol_sha256: str
    uv_lock_sha256: str
    recorder_sha256: str
    codec_sha256: str
    sink_sha256: str
    run_id: str
    recorder_id: str
    catalog_ref: str
    catalog_sha256: str
    runtime_admission_ref: str
    runtime_admission_sha256: str
    installation_member_ref: str


@dataclass(frozen=True, slots=True)
class ManifestView:
    raw: bytes
    sha256: str
    identity: ManifestIdentity
    members: tuple[SourceMember, ...]
    definitions: tuple[Definition, ...]
    instances: tuple[Instance, ...]
    bindings: tuple[Binding, ...]


@dataclass(frozen=True, slots=True)
class CatalogView:
    raw: bytes
    sha256: str
    members: tuple[MemberPolicy, ...]
    definitions: tuple[Definition, ...]
    instances: tuple[Instance, ...]
    dispatch_policy: tuple[DispatchPolicy, ...]
    installation_member_ref: str


@dataclass(frozen=True, slots=True)
class DeclaredSources:
    manifest: ManifestView
    catalog: CatalogView


def _encode(value: object, *, newline: bool = True) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + ("\n" if newline else "")
    ).encode("ascii")


def _scan(raw: bytes) -> None:
    """Count keys, scalar values and containers before JSON object allocation."""
    depth = nodes = token_chars = 0
    quoted = escaped = scalar = numeric = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
            continue
        if byte == 34:
            quoted = True
            scalar = numeric = False
            token_chars = 0
            nodes += 1
        elif byte in (91, 123):
            depth += 1
            nodes += 1
            scalar = numeric = False
            token_chars = 0
        elif byte in (93, 125):
            depth -= 1
            scalar = numeric = False
            token_chars = 0
        elif byte in (9, 10, 13, 32, 44, 58):
            scalar = numeric = False
            token_chars = 0
        elif not scalar:
            nodes += 1
            scalar = True
            numeric = byte == 45 or 48 <= byte <= 57
            token_chars = 1 if numeric else 0
        elif numeric:
            token_chars += 1
        if token_chars > INTEGER_TOKEN_CHARS:
            raise ValueError("Integer token including sign exceeds ten characters")
        if depth < 0 or depth > MAX_DEPTH or nodes > MAX_NODES:
            raise ValueError("Source declaration depth or node ceiling exceeded")
    if depth or quoted:
        raise ValueError("Truncated source declaration JSON")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _integer(text: str) -> int:
    if len(text) > INTEGER_TOKEN_CHARS:
        raise ValueError("Integer token including sign exceeds ten characters")
    return int(text)


def _reject_number(text: str) -> NoReturn:
    raise ValueError("Source declaration numbers must be strict integers")


def _document(raw: bytes, limit: int, keys: frozenset[str]) -> dict[str, object]:
    if type(raw) is not bytes or not 1 <= len(raw) <= limit:
        raise ValueError("Complete bounded immutable source declaration bytes required")
    _scan(raw)
    try:
        value: object = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_unique_pairs,
            parse_int=_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, RecursionError) as parse_error:
        raise ValueError("Invalid strict source declaration JSON") from parse_error
    if type(value) is not dict or set(value) != keys:
        raise ValueError("Exact source declaration root fields required")
    if _encode(value) != raw:
        raise ValueError("Exact canonical compact ASCII JSON and one LF required")
    return {key: value[key] for key in keys}


def _text(value: object) -> str:
    if type(value) is not str:
        raise ValueError("Exact string required")
    return value


def _ref(value: object) -> str:
    text = _text(value)
    if _REF.fullmatch(text) is None:
        raise ValueError("Bounded opaque member reference required")
    return text


def _name(value: object) -> str:
    text = _text(value)
    if len(text) > 128 or _NAME.fullmatch(text) is None:
        raise ValueError("Bounded ASCII dotted identifier required")
    return text


def _hash(value: object, size: int = 64) -> str:
    text = _text(value)
    if re.fullmatch("[0-9a-f]{" + str(size) + "}", text) is None:
        raise ValueError("Exact lowercase hexadecimal identity required")
    return text


def _int(value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError("Strict bounded integer required")
    return value


def _origin(value: object) -> Origin:
    if type(value) is str:
        if value == "checkout_source":
            return "checkout_source"
        if value == "trusted_runtime_member":
            return "trusted_runtime_member"
    raise ValueError("Closed source origin required")


def _kind(value: object) -> Kind:
    if type(value) is str:
        if value == "python_method":
            return "python_method"
        if value == "python_function":
            return "python_function"
        if value == "runtime_builtin":
            return "runtime_builtin"
    raise ValueError("Closed definition kind required")


def _path(value: object) -> str:
    text = _text(value)
    if (
        not 1 <= len(text) <= 160
        or any(ord(char) < 32 or ord(char) > 126 for char in text)
        or "\\" in text
        or any(part in ("", ".", "..") for part in text.split("/"))
    ):
        raise ValueError("Canonical bounded repository-relative ASCII locator required")
    return text


def _rows(value: object, count: int | None) -> list[object]:
    if type(value) is not list or not 1 <= len(value) <= 64:
        raise ValueError("Complete bounded row array required")
    if count is not None and len(value) != count:
        raise ValueError("Fixed complete row count required")
    return list(value)


def _row(value: object, count: int) -> list[object]:
    if type(value) is not list or len(value) != count:
        raise ValueError("Exact flat row shape required")
    if any(type(atom) not in (str, int, type(None)) for atom in value):
        raise ValueError("Strict flat row atoms required; booleans cannot coerce")
    if len(_encode(value, newline=False)) + 1 > ROW_BYTES:
        raise ValueError("Canonical row plus separator exceeds 512 bytes")
    return list(value)


def _policy(member_id: object, origin: object, locator: object, module: object) -> MemberPolicy:
    selected_origin = _origin(origin)
    selected_locator = _path(locator) if selected_origin == "checkout_source" else _ref(locator)
    return MemberPolicy(
        _ref(member_id), selected_origin, selected_locator,
        None if module is None else _name(module),
    )


def _member_policies(values: tuple[MemberPolicy, ...]) -> dict[str, MemberPolicy]:
    ids = tuple(value.member_id for value in values)
    if ids != tuple(sorted(set(ids))):
        raise ValueError("Member IDs must be unique and ordered")
    locations = tuple(value.locator for value in values)
    if len(set(locations)) != len(locations):
        raise ValueError("Duplicate or aliased member locator declaration")
    locks = tuple(value for value in values if value.locator == "uv.lock")
    if (
        len(locks) != 1
        or locks[0].origin != "checkout_source"
        or locks[0].loaded_module is not None
    ):
        raise ValueError("Exactly one literal checkout uv.lock with null loaded module required")
    return {value.member_id: value for value in values}


def _definitions(value: object, members: dict[str, MemberPolicy]) -> tuple[Definition, ...]:
    result: list[Definition] = []
    method_names = ("position", "exp", "log", "circle_constant")
    for index, item in enumerate(_rows(value, 5)):
        row = _row(item, 5)
        definition = Definition(
            _ref(row[0]), _ref(row[1]), _kind(row[2]), _name(row[3]), _name(row[4])
        )
        if definition.definition_id != f"d{index}" or definition.member_id not in members:
            raise ValueError("Exact ordered definition IDs and present members required")
        member = members[definition.member_id]
        if member.loaded_module != definition.module:
            raise ValueError("Definition module differs from member declaration")
        if index < 4:
            if (
                definition.kind != "python_method"
                or definition.module != "endpoint_belief_reference"
                or definition.qualname != "EndpointOracle." + method_names[index]
                or member.origin != "checkout_source"
                or (result and definition.member_id != result[0].member_id)
            ):
                raise ValueError("Fixed EndpointOracle definitions must share one source member")
        elif definition.kind not in ("python_function", "runtime_builtin"):
            raise ValueError("Native emitter definition remains an explicit function or builtin")
        if definition.kind == "python_function" and member.origin != "checkout_source":
            raise ValueError("Python function requires a checkout source member")
        if definition.kind == "runtime_builtin" and member.origin != "trusted_runtime_member":
            raise ValueError("Runtime builtin requires a declared trusted runtime member")
        result.append(definition)
    return tuple(result)


def _instances(value: object, members: dict[str, MemberPolicy]) -> tuple[Instance, ...]:
    result: list[Instance] = []
    roles = (
        "fixture", "strong", "weak", "future", *("arithmetic",) * 8, "constants", "native_emit"
    )
    for index, item in enumerate(_rows(value, 14)):
        row = _row(item, 4)
        case_index = None if row[2] is None else _int(row[2], 0, 7)
        instance = Instance(_ref(row[0]), _text(row[1]), case_index, _ref(row[3]))
        if (
            instance.instance_id != f"i{index:02d}"
            or instance.role != roles[index]
            or instance.case_index != (index - 4 if 4 <= index <= 11 else None)
            or instance.source_member_ref not in members
        ):
            raise ValueError("Fixed ordered instance role/case/member mapping required")
        result.append(instance)
    return tuple(result)


_SLOTS = (
    (0, 0), (1, 0), (2, 0), (3, 0),
    (4, 1), (4, 2), (5, 1), (5, 2), (6, 1), (6, 2), (7, 1), (7, 2),
    (8, 1), (8, 2), (9, 1), (9, 2), (10, 1), (10, 2), (11, 1), (11, 2),
    (12, 2), (12, 3), (13, 4),
)


def _binding(row: list[object], index: int) -> Binding:
    result = Binding(_ref(row[0]), _int(row[1], 0, 4), _ref(row[2]), _ref(row[3]))
    instance, code = _SLOTS[index]
    if result != Binding(f"i{instance:02d}", code, f"d{code}", f"j{index:02d}"):
        raise ValueError("Exact ordered 23 dispatch slots required")
    return result


def _joins(
    definitions: tuple[Definition, ...], instances: tuple[Instance, ...],
    bindings: tuple[Binding, ...],
) -> None:
    for binding in bindings:
        instance = instances[int(binding.instance_id[1:])]
        definition = definitions[binding.primitive_code]
        if instance.source_member_ref != definition.member_id:
            raise ValueError("Slot definition and owned-instance member declarations differ")


def _header(document: dict[str, object], arrays: tuple[str, ...]) -> None:
    header = dict(document)
    for name in arrays:
        header[name] = []
    if len(_encode(header)) > HEADER_BYTES:
        raise ValueError("Canonical empty-array header exceeds 4096 bytes")


_ROOT_PINS = (
    ("protocol_sha256", "docs/research/RA_N03_CALIBRATION_SLICE.md", None),
    ("recorder_sha256", "tests/d1_primitive_recording.py", "d1_primitive_recording"),
    ("codec_sha256", "tests/d1_primitive_codec.py", "d1_primitive_codec"),
    ("sink_sha256", "tests/d1_primitive_sink.py", "d1_primitive_sink"),
)
_IDENTITY_KEYS = frozenset(
    (
        "source_commit", "source_tree", "protocol_sha256", "uv_lock_sha256",
        "recorder_sha256", "codec_sha256", "sink_sha256", "run_id", "recorder_id",
        "catalog_ref", "catalog_sha256", "runtime_admission_ref", "runtime_admission_sha256",
        "installation_member_ref",
    )
)
_MANIFEST_ARRAYS = ("members", "definitions", "instances", "bindings")
_CATALOG_ARRAYS = ("members", "definitions", "instances", "dispatch_policy")
_MANIFEST_KEYS = _IDENTITY_KEYS | frozenset(("schema", "limits", *_MANIFEST_ARRAYS))
_CATALOG_KEYS = frozenset(("schema", "installation_member_ref", *_CATALOG_ARRAYS))


def _root_policies(members: dict[str, MemberPolicy]) -> None:
    for _, locator, module in _ROOT_PINS:
        selected = tuple(member for member in members.values() if member.locator == locator)
        if (
            len(selected) != 1
            or selected[0].origin != "checkout_source"
            or selected[0].loaded_module != module
        ):
            raise ValueError("Required root-pin checkout locator/module declaration missing")


def _identity(document: dict[str, object]) -> ManifestIdentity:
    run_id, recorder_id = _text(document["run_id"]), _text(document["recorder_id"])
    if _ID.fullmatch(run_id) is None or _ID.fullmatch(recorder_id) is None:
        raise ValueError("Bounded opaque run/recorder identities required")
    protocol = _hash(document["protocol_sha256"])
    if protocol != PROTOCOL_SHA256:
        raise ValueError("Frozen D1 protocol hash required")
    return ManifestIdentity(
        _hash(document["source_commit"], 40), _hash(document["source_tree"], 40), protocol,
        _hash(document["uv_lock_sha256"]), _hash(document["recorder_sha256"]),
        _hash(document["codec_sha256"]), _hash(document["sink_sha256"]), run_id, recorder_id,
        _ref(document["catalog_ref"]), _hash(document["catalog_sha256"]),
        _ref(document["runtime_admission_ref"]), _hash(document["runtime_admission_sha256"]),
        _ref(document["installation_member_ref"]),
    )


def parse_manifest(raw: bytes) -> ManifestView:
    """Parse S declarations only; no expected-plan, file or runtime authentication."""
    document = _document(raw, MANIFEST_BYTES, _MANIFEST_KEYS)
    if document["schema"] != MANIFEST_SCHEMA:
        raise ValueError("Fixed source-manifest schema required")
    given_limits = document["limits"]
    if type(given_limits) is not dict or set(given_limits) != {name for name, _ in LIMITS}:
        raise ValueError("Exactly 16 fixed source limits required")
    for name, expected in LIMITS:
        if type(given_limits[name]) is not int or given_limits[name] != expected:
            raise ValueError("Caller cannot choose source limits")
    identity = _identity(document)
    members: list[SourceMember] = []
    for item in _rows(document["members"], None):
        row = _row(item, 6)
        policy = _policy(row[0], row[1], row[2], row[5])
        ceiling = (
            67_108_864 if policy.origin == "trusted_runtime_member"
            else 262_144 if policy.locator == "uv.lock" else 131_072
        )
        members.append(SourceMember(policy, _hash(row[3]), _int(row[4], 1, ceiling)))
    policies = _member_policies(tuple(member.policy for member in members))
    _root_policies(policies)
    by_id = {member.policy.member_id: member for member in members}
    if identity.catalog_ref not in by_id or identity.installation_member_ref not in by_id:
        raise ValueError("Catalog and installer references must name members")
    catalog = by_id[identity.catalog_ref]
    if (
        catalog.policy.origin != "checkout_source"
        or catalog.byte_length > CATALOG_BYTES
        or catalog.sha256 != identity.catalog_sha256
    ):
        raise ValueError("Catalog source member and root hash declarations differ")
    by_path = {
        member.policy.locator: member
        for member in members
        if member.policy.origin == "checkout_source"
    }
    if by_path["uv.lock"].sha256 != identity.uv_lock_sha256:
        raise ValueError("Lock member hash differs from root declaration")
    for field, locator, _ in _ROOT_PINS:
        if by_path[locator].sha256 != getattr(identity, field):
            raise ValueError("Required source member hash differs from root pin")
    definitions = _definitions(document["definitions"], policies)
    instances = _instances(document["instances"], policies)
    bindings = tuple(
        _binding(_row(item, 4), index)
        for index, item in enumerate(_rows(document["bindings"], 23))
    )
    _joins(definitions, instances, bindings)
    _header(document, _MANIFEST_ARRAYS)
    return ManifestView(
        raw, hashlib.sha256(raw).hexdigest(), identity, tuple(members),
        definitions, instances, bindings,
    )


def parse_catalog(raw: bytes) -> CatalogView:
    """Parse policy declarations without treating them as a trusted closed catalog."""
    document = _document(raw, CATALOG_BYTES, _CATALOG_KEYS)
    if document["schema"] != CATALOG_SCHEMA:
        raise ValueError("Fixed source-catalog schema required")
    members: list[MemberPolicy] = []
    for item in _rows(document["members"], None):
        row = _row(item, 4)
        members.append(_policy(row[0], row[1], row[2], row[3]))
    policies = _member_policies(tuple(members))
    _root_policies(policies)
    installation = _ref(document["installation_member_ref"])
    if installation not in policies:
        raise ValueError("Installer reference must name a catalog member")
    definitions = _definitions(document["definitions"], policies)
    instances = _instances(document["instances"], policies)
    dispatch: list[DispatchPolicy] = []
    for index, item in enumerate(_rows(document["dispatch_policy"], 23)):
        row = _row(item, 9)
        binding = _binding(row[:4], index)
        wrapper, consumer = _ref(row[4]), _ref(row[6])
        if wrapper not in policies or consumer not in policies:
            raise ValueError("Wrapper/consumer references must name catalog members")
        capture = _text(row[8])
        expected = (
            "native_callable_recorder_slot_v1"
            if binding.primitive_code == 4 else "bound_method_recorder_slot_v1"
        )
        if capture != expected:
            raise ValueError("Fixed slot capture-layout declaration required")
        dispatch.append(
            DispatchPolicy(binding, wrapper, _name(row[5]), consumer, _name(row[7]), capture)
        )
    _joins(definitions, instances, tuple(policy.binding for policy in dispatch))
    _header(document, _CATALOG_ARRAYS)
    return CatalogView(
        raw, hashlib.sha256(raw).hexdigest(), tuple(members), definitions,
        instances, tuple(dispatch), installation,
    )


def compare_declarations(manifest_raw: bytes, catalog_raw: bytes) -> DeclaredSources:
    """Reparse both byte inputs and join declarations to actual supplied catalog bytes.

This does not authenticate the supplied catalog or compare T, files, loaded code,
owned objects, runtime evidence, installation, retention or an outer admission.
"""
    manifest, catalog = parse_manifest(manifest_raw), parse_catalog(catalog_raw)
    member = next(
        value for value in manifest.members
        if value.policy.member_id == manifest.identity.catalog_ref
    )
    if (
        member.byte_length != len(catalog.raw)
        or member.sha256 != catalog.sha256
        or manifest.identity.catalog_sha256 != catalog.sha256
    ):
        raise ValueError("Actual supplied catalog bytes differ from S hash/length declarations")
    if (
        tuple(value.policy for value in manifest.members) != catalog.members
        or manifest.definitions != catalog.definitions
        or manifest.instances != catalog.instances
        or manifest.bindings != tuple(value.binding for value in catalog.dispatch_policy)
        or manifest.identity.installation_member_ref != catalog.installation_member_ref
    ):
        raise ValueError("S policy projection differs from the complete supplied catalog")
    return DeclaredSources(manifest, catalog)
