"""Materialize existing D1 records from protected bytes; never grant acceptance.

Run only in the independently reviewed outer preparation context. There is no
installer, launcher, network client, scientific import or acceptance switch.
Candidate delivery and runtime completeness are independently reviewed premises.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import re
import stat
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from scripts import ci_artifacts
from scripts import d1_bootstrap_control as control


def encoded(value: object) -> bytes:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if len(raw) > control.PLAN_LIMIT:
        raise ValueError("Existing record exceeds its 4 MiB ceiling")
    return raw


def _bytes(path: Path, limit: int = control.FILE_LIMIT) -> bytes:
    info = path.lstat()
    if info.st_uid not in (0, os.getuid()):
        raise ValueError("Unapproved file owner")
    return control._read(path, limit, info.st_uid)


def collect_inventory(
    roots: tuple[Path, ...],
    files: tuple[Path, ...],
    *,
    stdlib: Path,
    venv: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Close named roots, deduplicating literal paths and reviewed alias targets."""
    aliases = control.runtime_aliases({"stdlib": stdlib, "venv_root": venv})
    interpreter_links = {venv / "bin" / name for name in ("python", "python3", "python3.12")}
    pending = list(roots + files)
    if len(pending) > control.ENTRY_LIMIT:
        raise ValueError("Too many inventory inputs")
    result: dict[str, list[dict[str, Any]]] = {"files": [], "directories": [], "links": []}
    seen: set[Path] = set()
    total = 0
    while pending:
        path = control._path(str(pending.pop()))
        if path in seen:
            continue
        if len(seen) >= control.ENTRY_LIMIT:
            raise ValueError("Inventory entry ceiling exceeded")
        seen.add(path)
        control._ancestors(path)
        info = path.lstat()
        if info.st_uid not in (0, os.getuid()):
            raise ValueError("Unapproved inventory owner")
        if stat.S_ISDIR(info.st_mode):
            control._safe_mode(info, info.st_uid, directory=True)
            names = control._names(path, control.ENTRY_LIMIT - len(seen))
            result["directories"].append({"path": str(path), "uid": info.st_uid, "entries": sorted(names)})
            pending.extend(path / name for name in names)
        elif stat.S_ISREG(info.st_mode):
            total += info.st_size
            if total > control.TOTAL_INPUT_LIMIT:
                raise ValueError("Inventory payload ceiling exceeded")
            raw = _bytes(path)
            result["files"].append({
                "path": str(path), "uid": info.st_uid, "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            })
        elif stat.S_ISLNK(info.st_mode):
            literal = os.readlink(path)
            if path in aliases:
                expected, target, _, _, owner = aliases[path]
                if literal != expected or info.st_uid != owner:
                    raise ValueError("Reviewed alias differs")
            elif path in interpreter_links:
                relative = Path(literal)
                if not literal or str(relative) != literal or ".." in relative.parts:
                    raise ValueError("Noncanonical interpreter target")
                target = relative if relative.is_absolute() else path.parent / relative
            else:
                raise ValueError("Unreviewed inventory link")
            result["links"].append({"path": str(path), "uid": info.st_uid, "target": literal})
            pending.append(target)
        else:
            raise ValueError("Inventory contains a special file")
        # Aliases/overlapping roots can duplicate queued names, not unbound memory.
        if len(pending) + len(seen) > 2 * control.ENTRY_LIMIT:
            raise ValueError("Inventory traversal queue ceiling exceeded")
    for values in result.values():
        values.sort(key=lambda item: item["path"])
    encoded(result)
    return result


def _engine_identity(
    package: Path, python_version: str, dependencies: list[dict[str, Any]], site: Path
) -> str:
    """Reproduce the existing metadata/source digest without importing any laws."""
    init = ast.parse(_bytes(package / "__init__.py", ci_artifacts.MAX_MEMBER_BYTES))
    versions = [
        ast.literal_eval(node.value)
        for node in init.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
    ]
    if len(versions) != 1 or not isinstance(versions[0], str):
        raise ValueError("Review the package version declaration")
    laws = ast.parse(_bytes(package / "laws.py", ci_artifacts.MAX_MEMBER_BYTES))
    functions = [node for node in laws.body if isinstance(node, ast.FunctionDef) and node.name == "reference_registry"]
    if len(functions) != 1:
        raise ValueError("Reference registry source is ambiguous")
    body = functions[0].body
    if (
        len(body) != 5
        or ast.unparse(body[0]) != "registry = LawRegistry()"
        or ast.unparse(body[-1]) != "return registry"
    ):
        raise ValueError("Review changed reference registry structure")
    plugins: dict[str, str] = {}
    for statement in body[1:-1]:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            raise ValueError("Reference registry is no longer literal registration")
        call = statement.value
        if (
            not isinstance(call.func, ast.Attribute) or call.func.attr != "register"
            or not isinstance(call.func.value, ast.Name) or call.func.value.id != "registry"
            or len(call.args) != 2 or len(call.keywords) != 1
            or call.keywords[0].arg != "implementation_id"
        ):
            raise ValueError("Review changed reference registry calls")
        kind, implementation = ast.literal_eval(call.args[0]), ast.literal_eval(call.keywords[0].value)
        if not isinstance(kind, str) or not isinstance(implementation, str) or kind in plugins:
            raise ValueError("Invalid literal plugin identity")
        plugins[kind] = implementation
    if plugins != {"spring": "spring-v1", "radial": "radial-v1", "velocity": "velocity-v1"}:
        raise ValueError("Review changed reference plugin identities")
    dependency_versions: dict[str, str] = {}
    for entry in dependencies:
        path = Path(entry["path"])
        if len(path.parts) == 2 and path.parts[0].endswith(".dist-info") and path.name == "METADATA":
            metadata = BytesParser().parsebytes(_bytes(site / path, ci_artifacts.MAX_MEMBER_BYTES))
            name, version = metadata["Name"], metadata["Version"]
            if name in ("numpy", "pydantic"):
                if name in dependency_versions or not isinstance(version, str):
                    raise ValueError("Dependency metadata identity is ambiguous")
                dependency_versions[name] = version
    if set(dependency_versions) != {"numpy", "pydantic"}:
        raise ValueError("Required installed dependency metadata is missing")
    identity = {"package": versions[0], "python": python_version, **dependency_versions, "plugins": plugins}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    for name in sorted(ci_artifacts.MODULES):
        if name.endswith(".py"):
            digest.update(name.encode())
            digest.update(_bytes(package / name, ci_artifacts.MAX_MEMBER_BYTES))
    return digest.hexdigest()


def materialize_installation(
    *,
    checkout: Path,
    site: Path,
    interpreter_file: Path,
    python_version: str,
    source_commit: str,
    wheel: Path,
    provenance: Path,
    expected_provenance_sha256: str,
    requirements: Path,
) -> dict[str, Any]:
    """Construct TrustedInstallation fields after independent candidate acceptance.

    The expected provenance digest and source revision come from that external
    decision. Calling this function cannot establish the decision or runtime custody.
    """
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None or re.fullmatch(r"3\.[0-9]+\.[0-9]+", python_version) is None:
        raise ValueError("Exact source commit and observed runtime version required")
    raw = _bytes(provenance, 65536)
    if hashlib.sha256(raw).hexdigest() != control._digest(expected_provenance_sha256):
        raise ValueError("Independently pinned provenance differs")
    candidate = json.loads(raw, object_pairs_hook=control._object_pairs)
    if not isinstance(candidate, dict):
        raise ValueError("Candidate provenance must be an object")
    lock = checkout / "uv.lock"
    lock_sha = hashlib.sha256(_bytes(lock, 8 * 1024**2)).hexdigest()
    if (
        candidate.get("schema_version") != "strange-physics.release-candidate.v1"
        or candidate.get("repository") != "spei04/strange-physics"
        or candidate.get("source_commit") != source_commit
        or candidate.get("uv_lock_sha256") != lock_sha
        or candidate.get("uv_version") != "0.13.4"
        or candidate.get("runtime_requirements_sha256") != hashlib.sha256(_bytes(requirements, 8 * 1024**2)).hexdigest()
    ):
        raise ValueError("Candidate source, lock or exact requirements export differs")
    archive = _bytes(wheel, ci_artifacts.MAX_ARCHIVE_BYTES)
    wheel_sha = hashlib.sha256(archive).hexdigest()
    distributions = candidate.get("distribution_files")
    if not isinstance(distributions, list) or len(distributions) != 2:
        raise ValueError("Expected exact candidate distribution pair")
    if sum(item == {"name": wheel.name, "sha256": wheel_sha, "bytes": len(archive)} for item in distributions) != 1:
        raise ValueError("Candidate wheel identity differs")
    # Complete archive policy is independently checked by ci_artifacts before
    # materialization; repeat the actual package-byte join here.
    package = site / "strange_physics"
    package_files: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        members = bundle.infolist()
        names = [item.filename for item in members]
        if len(members) > ci_artifacts.MAX_MEMBERS or len(names) != len(set(names)):
            raise ValueError("Wheel membership exceeds its bound")
        expected = {"strange_physics/" + name for name in ci_artifacts.MODULES}
        if {name for name in names if name.startswith("strange_physics/")} != expected:
            raise ValueError("Wheel package membership differs")
        if sum(item.file_size for item in members) > ci_artifacts.MAX_ARCHIVE_BYTES:
            raise ValueError("Expanded wheel exceeds its bound")
        for item in members:
            ci_artifacts.check_name(item.filename)
            if item.is_dir() or stat.S_ISLNK(item.external_attr >> 16) or item.file_size > ci_artifacts.MAX_MEMBER_BYTES:
                raise ValueError("Unsafe wheel member")
        for name in sorted(ci_artifacts.MODULES):
            installed = _bytes(package / name, ci_artifacts.MAX_MEMBER_BYTES)
            if installed != bundle.read("strange_physics/" + name) or installed != _bytes(checkout / "src/strange_physics" / name, ci_artifacts.MAX_MEMBER_BYTES):
                raise ValueError("Installed package, archive and reviewed source differ")
            package_files.append({"path": name, "bytes": len(installed), "sha256": hashlib.sha256(installed).hexdigest()})
    inventory = collect_inventory((site,), (), stdlib=Path("/unsupported"), venv=site)
    dependencies = [
        {"path": str(Path(item["path"]).relative_to(site)), "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in inventory["files"]
        if not Path(item["path"]).is_relative_to(package)
        and "__pycache__" not in Path(item["path"]).relative_to(site).parts
    ]
    observed_package = {
        Path(item["path"]).name for item in inventory["files"]
        if Path(item["path"]).parent == package
    }
    nested_package = [
        item["path"] for item in inventory["directories"]
        if Path(item["path"]).is_relative_to(package)
        and Path(item["path"]) != package
        and "__pycache__" not in Path(item["path"]).relative_to(package).parts
    ]
    if observed_package != ci_artifacts.MODULES or nested_package or not 1 <= len(dependencies) <= 10000:
        raise ValueError("Installed membership differs from the supported profile")
    record = {
        "evidence_kind": "accepted_release_candidate",
        "source_commit": source_commit, "uv_lock_sha256": lock_sha, "lock_path": str(lock),
        "archive_path": str(wheel), "archive_sha256": wheel_sha,
        "provenance_path": str(provenance), "provenance_sha256": expected_provenance_sha256,
        "python_version": python_version,
        "python_executable_sha256": hashlib.sha256(_bytes(interpreter_file)).hexdigest(),
        "engine_fingerprint": _engine_identity(package, python_version, dependencies, site),
        "package_files": package_files, "dependency_files": dependencies,
    }
    encoded(record)
    return record


def materialize_plan(
    binding: dict[str, Any], *, runtime_files: tuple[Path, ...]
) -> dict[str, Any]:
    """Fill the existing launch record; never infer complete native/deferred coverage.

    binding holds independently observed startup fields and fixed source/runtime
    locations. runtime_files is the reviewed external ELF/loader input closure;
    an empty or incomplete list must not be approved by the outer reviewer.
    """
    if {"files", "directories", "links"} & binding.keys():
        raise ValueError("Inventory must be freshly observed, not supplied")
    if not runtime_files or len(runtime_files) != len(set(runtime_files)):
        raise ValueError("Explicit reviewed native/runtime file closure is required")
    paths = {key: control._path(binding[key]) for key in (
        "checkout", "stdlib", "venv_root", "site_packages", "installation_record",
        "controller", "controller_interpreter", "bootstrap",
    )}
    installation = json.loads(_bytes(paths["installation_record"], control.PLAN_LIMIT), object_pairs_hook=control._object_pairs)
    routes = {
        name: str(paths["checkout"] / "tests" / (name + ".py"))
        for name in control.HELPERS
    }
    for name in control.NATIVE_MODULES:
        relative = name.replace(".", "/") + ("/__init__.py" if name == "strange_physics" else ".py")
        routes[name] = str(paths["site_packages"] / relative)
    if binding.get("import_map") != routes:
        raise ValueError("Canonical source routes differ")
    source_files = tuple(paths["checkout"] / rel for rel in control.SOURCE_PIN_PATHS) + tuple(
        paths["checkout"] / "src" / (name.replace(".", "/") + ("/__init__.py" if name == "strange_physics" else ".py"))
        for name in control.NATIVE_MODULES
    )
    extras = (
        *runtime_files, *source_files, *(Path(path) for path in routes.values()),
        paths["controller"], paths["controller_interpreter"], paths["bootstrap"],
        paths["checkout"] / "scripts/d1_owned_capture.py",
        paths["checkout"] / "scripts/grid_q1_supervisor.py",
        paths["installation_record"],
        *(control._path(installation[key]) for key in ("lock_path", "archive_path", "provenance_path")),
    )
    inventory = collect_inventory(
        (paths["stdlib"], paths["venv_root"]), extras,
        stdlib=paths["stdlib"], venv=paths["venv_root"],
    )
    result = {**binding, **inventory}
    control.validate_plan(result)
    encoded(result)
    return result


def write_record(path: Path, record: dict[str, Any]) -> str:
    """Exclusive owner-only output; caller accounts all writes and partial failures."""
    raw = encoded(record)
    control._ancestors(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    # Preserve any partial output on failure; never overwrite or claim success.
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    return hashlib.sha256(raw).hexdigest()
