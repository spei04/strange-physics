"""Check release archive contents before creating a small delivery manifest.

This is an allowlist and integrity check, not a signature or a security audit.
The package module list intentionally requires review when new modules ship.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

MODULES = frozenset(
    {
        "__init__.py",
        "cli.py",
        "contracts.py",
        "control_contracts.py",
        "credential_authority.py",
        "evaluation.py",
        "evaluation_contracts.py",
        "fitting_contracts.py",
        "fitting.py",
        "invitation_contracts.py",
        "journal.py",
        "laws.py",
        "linking_contracts.py",
        "prediction.py",
        "prediction_contracts.py",
        "py.typed",
        "research_contracts.py",
        "run_credential_contracts.py",
        "run_credentials.py",
        "product_authority.py",
        "sdk.py",
        "serialization.py",
        "session.py",
        "session_contracts.py",
        "service_contracts.py",
        "service_credentials.py",
        "simulation.py",
        "worlds.py",
        "workspace_contracts.py",
    }
)
MAX_MEMBER_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 128


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_name(name: str) -> None:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or "\\" in name
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or str(path) != name
    ):
        raise ValueError("Archive contains an unsafe path")


def read_archive(path: Path) -> dict[str, bytes]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive must be a bounded regular file")
    members: dict[str, bytes] = {}

    def add(name: str, size: int, content: bytes) -> None:
        check_name(name)
        if name in members or len(members) >= MAX_MEMBERS:
            raise ValueError("Duplicate or excessive archive members")
        if size < 0 or size > MAX_MEMBER_BYTES or len(content) != size:
            raise ValueError("Archive member exceeds size bound")
        if sum(map(len, members.values())) + size > MAX_ARCHIVE_BYTES:
            raise ValueError("Expanded archive exceeds size bound")
        members[name] = content

    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                mode = member.external_attr >> 16
                if member.is_dir() or (stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    raise ValueError("Wheel must contain only regular files")
                if member.file_size > MAX_MEMBER_BYTES:
                    raise ValueError("Archive member exceeds size bound")
                add(member.filename, member.file_size, archive.read(member))
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as source_archive:
            for entry in source_archive:
                if not entry.isfile() or entry.size > MAX_MEMBER_BYTES:
                    raise ValueError("Source archive must contain bounded regular files")
                stream = source_archive.extractfile(entry)
                if stream is None:
                    raise ValueError("Source archive member cannot be read")
                with stream:
                    add(entry.name, entry.size, stream.read(MAX_MEMBER_BYTES + 1))
    else:
        raise ValueError("Unexpected distribution format")
    return members


def validate_archives(dist: Path, source_root: Path) -> tuple[Path, Path]:
    project = tomllib.loads((source_root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    if project["name"] != "strange-physics" or not re.fullmatch(r"[0-9A-Za-z.]+", version):
        raise ValueError("Review archive policy before changing package identity")
    stem = f"strange_physics-{version}"
    wheel = dist / f"{stem}-py3-none-any.whl"
    sdist = dist / f"{stem}.tar.gz"
    actual = {p.name for p in dist.iterdir()}
    expected = {wheel.name, sdist.name}
    if actual != expected:
        raise ValueError(
            "Distribution directory must contain exactly the wheel and sdist; "
            f"unexpected={sorted(actual - expected)[:10]!r}; "
            f"missing={sorted(expected - actual)!r}"
        )
    source = {name: (source_root / "src/strange_physics" / name).read_bytes() for name in MODULES}
    info = f"{stem}.dist-info"
    wheel_files = read_archive(wheel)
    wheel_metadata = {
        f"{info}/METADATA",
        f"{info}/WHEEL",
        f"{info}/entry_points.txt",
        f"{info}/RECORD",
        f"{info}/licenses/LICENSE",
    }
    expected_wheel = {f"strange_physics/{n}" for n in MODULES} | wheel_metadata
    if set(wheel_files) != expected_wheel:
        raise ValueError(
            "Wheel contents differ from the package allowlist; "
            f"unexpected={sorted(set(wheel_files) - expected_wheel)[:10]!r}; "
            f"missing={sorted(expected_wheel - set(wheel_files))[:10]!r}"
        )
    source_files = read_archive(sdist)
    fixed_source = {"README.md", "LICENSE", "pyproject.toml", ".gitignore"}
    expected_source = (
        {f"{stem}/src/strange_physics/{n}" for n in MODULES}
        | {f"{stem}/{n}" for n in fixed_source}
        | {f"{stem}/PKG-INFO"}
    )
    if set(source_files) != expected_source:
        raise ValueError(
            "Source archive contents differ from the package allowlist; "
            f"unexpected={sorted(set(source_files) - expected_source)[:10]!r}; "
            f"missing={sorted(expected_source - set(source_files))[:10]!r}"
        )
    for name, content in source.items():
        if (
            wheel_files[f"strange_physics/{name}"] != content
            or source_files[f"{stem}/src/strange_physics/{name}"] != content
        ):
            raise ValueError("Packaged module differs from reviewed source")
    for name in fixed_source:
        if source_files[f"{stem}/{name}"] != (source_root / name).read_bytes():
            raise ValueError("Source archive differs from reviewed source")
    if wheel_files[f"{info}/licenses/LICENSE"] != (source_root / "LICENSE").read_bytes():
        raise ValueError("Wheel license differs from reviewed source")
    for metadata in [wheel_files[f"{info}/METADATA"], source_files[f"{stem}/PKG-INFO"]]:
        parsed = BytesParser().parsebytes(metadata)
        if parsed["Name"] != project["name"] or parsed["Version"] != version:
            raise ValueError("Package metadata has the wrong identity")
        if parsed["Requires-Python"] != project["requires-python"]:
            raise ValueError("Package metadata has the wrong Python requirement")
    return wheel, sdist


def write_provenance(
    paths: tuple[Path, Path], source_root: Path, runtime_requirements: Path
) -> None:
    commit = os.environ["GITHUB_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected full source commit identity")
    manifest = {
        "schema_version": "strange-physics.release-candidate.v1",
        "source_commit": commit,
        "repository": os.environ["GITHUB_REPOSITORY"],
        "workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "uv_version": "0.11.21",
        "python_version": sys.version,
        "uv_lock_sha256": sha256(source_root / "uv.lock"),
        "runtime_requirements_sha256": sha256(runtime_requirements),
        "distribution_files": [
            {"name": p.name, "sha256": sha256(p), "bytes": p.stat().st_size} for p in paths
        ],
        "scope": "Unpublished candidate; no deployment, signing or production-readiness claim.",
    }
    directory = paths[0].parent
    manifest_path = directory / "provenance.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    checksums = "".join(f"{sha256(p)}  {p.name}\n" for p in sorted([*paths, manifest_path]))
    (directory / "SHA256SUMS").write_text(checksums)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-requirements", type=Path)
    args = parser.parse_args()
    paths = validate_archives(args.dist, args.source_root)
    if args.runtime_requirements is not None:
        write_provenance(paths, args.source_root, args.runtime_requirements)
    print("Wheel and sdist match the reviewed package allowlist.")


if __name__ == "__main__":
    main()
