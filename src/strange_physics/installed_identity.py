"""Verify an owner-trusted build against this actual installed interpreter.

The protected admission is supplied by an independent owner verification step.
This does not authenticate a self-issued provenance document or hostile Python.
"""

from __future__ import annotations

import hashlib
import io
import os
import platform
import stat
import sys
import sysconfig
import zipfile
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

import strange_physics
from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message
from strange_physics.laws import reference_registry
from strange_physics.research_contracts import Digest, message_sha256
from strange_physics.serialization import engine_fingerprint
from strange_physics.study_contracts import Commit
from strange_physics.study_ledger import StudyLedgerError
from strange_physics.workflow_io import read_bytes


class BuildFile(Message):
    path: Annotated[str, Field(min_length=1, max_length=512)]
    sha256: Digest
    bytes: Annotated[int, Field(ge=0, le=64 * 1024**2)]


class TrustedInstallation(Message):
    """Fixed independently checked file sets; never a caller-selected import root."""

    evidence_kind: Literal["accepted_release_candidate", "synthetic_installed_snapshot"]
    source_commit: Commit
    uv_lock_sha256: Digest
    lock_path: Annotated[str, Field(min_length=1, max_length=4096)]
    archive_path: Annotated[str, Field(min_length=1, max_length=4096)]
    archive_sha256: Digest
    provenance_path: Annotated[str, Field(min_length=1, max_length=4096)]
    provenance_sha256: Digest
    python_version: Annotated[str, Field(min_length=1, max_length=32)]
    python_executable_sha256: Digest
    engine_fingerprint: Digest
    package_files: Annotated[tuple[BuildFile, ...], Field(min_length=1, max_length=128)]
    dependency_files: Annotated[tuple[BuildFile, ...], Field(min_length=1, max_length=10000)]

    @model_validator(mode="after")
    def paths(self) -> Self:
        for group in (self.package_files, self.dependency_files):
            names = [f.path for f in group]
            if len(names) != len(set(names)):
                raise ValueError("Build file names must be unique")
            for name in names:
                p = PurePosixPath(name)
                if p.is_absolute() or ".." in p.parts or "\\" in name or str(p) != name:
                    raise ValueError("Build file names must be relative canonical paths")
        if any("/" in f.path for f in self.package_files):
            raise ValueError("The reviewed package has only its fixed top-level modules")
        if any(f.path.startswith("strange_physics/") for f in self.dependency_files):
            raise ValueError("Project bytes are separate from dependency bytes")
        return self


class ObservedInstallation(Message):
    source_commit: Commit
    uv_lock_sha256: Digest
    engine_fingerprint: Digest
    installation_sha256: Digest


class _Provenance(Message):
    source_commit: Commit
    uv_lock_sha256: Digest
    archive_sha256: Digest
    evidence_kind: Literal["accepted_release_candidate", "synthetic_installed_snapshot"]


class _DistributionFile(Message):
    name: Annotated[str, Field(min_length=1, max_length=128)]
    sha256: Digest
    bytes: Annotated[int, Field(ge=1, le=32 * 1024**2)]


class _ReleaseProvenance(Message):
    schema_version: Literal["strange-physics.release-candidate.v1"]
    source_commit: Commit
    repository: Literal["spei04/strange-physics"]
    workflow_run_id: Annotated[str, Field(min_length=1, max_length=32)]
    workflow_run_attempt: Annotated[str, Field(min_length=1, max_length=32)]
    uv_version: Literal["0.13.4"]
    python_version: Annotated[str, Field(min_length=1, max_length=256)]
    uv_lock_sha256: Digest
    runtime_requirements_sha256: Digest
    distribution_files: Annotated[tuple[_DistributionFile, ...], Field(min_length=2, max_length=2)]
    scope: Annotated[str, Field(min_length=1, max_length=256)]


def _installed_bytes(path: Path, limit: int, *, system: bool = False) -> bytes:
    for p in (path, *path.parents):
        if p.is_symlink():
            raise StudyLedgerError("installed_identity_path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        if (
            not stat.S_ISREG(s.st_mode)
            or s.st_uid not in ({0, os.getuid()} if system else {os.getuid()})
            or s.st_nlink != 1
            or s.st_mode & 0o022
            or s.st_size > limit
        ):
            raise StudyLedgerError("installed_identity_path")
        chunks = []
        remaining = limit + 1
        while remaining:
            part = os.read(fd, min(remaining, 1024 * 1024))
            if not part:
                break
            chunks.append(part)
            remaining -= len(part)
        after = os.fstat(fd)
        if remaining == 0 or (s.st_ino, s.st_size, s.st_mtime_ns) != (
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise StudyLedgerError("installed_identity_changed")
        return b"".join(chunks)
    finally:
        os.close(fd)


def verify_native_installation(build: TrustedInstallation) -> ObservedInstallation:
    """Perform real bounded inspection inside an already charged control envelope."""
    site = Path(sysconfig.get_paths()["purelib"])
    package = site / "strange_physics"
    if Path(strange_physics.__file__).resolve().parent != package:
        raise StudyLedgerError("installed_identity_origin")
    if platform.python_version() != build.python_version:
        raise StudyLedgerError("installed_identity_runtime")
    executable = _installed_bytes(Path(sys.executable).resolve(), 64 * 1024**2, system=True)
    if hashlib.sha256(executable).hexdigest() != build.python_executable_sha256:
        raise StudyLedgerError("installed_identity_runtime")
    for name, module in tuple(sys.modules.items()):
        if name == "strange_physics" or name.startswith("strange_physics."):
            origin = getattr(module, "__file__", None)
            if origin is not None and Path(origin).resolve().parent != package:
                raise StudyLedgerError("installed_identity_origin")
    for path, sha, limit in (
        (build.lock_path, build.uv_lock_sha256, 8 * 1024**2),
        (build.provenance_path, build.provenance_sha256, 64 * 1024),
    ):
        data = read_bytes(Path(path), limit=limit)
        if hashlib.sha256(data).hexdigest() != sha:
            raise StudyLedgerError("installed_identity_digest")
    provenance_raw = read_bytes(Path(build.provenance_path), limit=64 * 1024)
    if build.evidence_kind == "accepted_release_candidate":
        released = parse_bounded_json(
            provenance_raw, _ReleaseProvenance, max_bytes=64 * 1024, max_depth=8, max_nodes=128
        )
        matches = [
            f
            for f in released.distribution_files
            if f.name == Path(build.archive_path).name and f.sha256 == build.archive_sha256
        ]
        if (released.source_commit, released.uv_lock_sha256) != (
            build.source_commit,
            build.uv_lock_sha256,
        ) or len(matches) != 1:
            raise StudyLedgerError("installed_identity_provenance")
    else:
        synthetic = parse_bounded_json(
            provenance_raw, _Provenance, max_bytes=64 * 1024, max_depth=4, max_nodes=32
        )
        if (
            synthetic.source_commit,
            synthetic.uv_lock_sha256,
            synthetic.archive_sha256,
            synthetic.evidence_kind,
        ) != (build.source_commit, build.uv_lock_sha256, build.archive_sha256, build.evidence_kind):
            raise StudyLedgerError("installed_identity_provenance")
    archive = read_bytes(Path(build.archive_path), limit=32 * 1024**2)
    if hashlib.sha256(archive).hexdigest() != build.archive_sha256:
        raise StudyLedgerError("installed_identity_archive")
    if build.evidence_kind == "accepted_release_candidate" and len(archive) != matches[0].bytes:
        raise StudyLedgerError("installed_identity_provenance")
    expected = {"strange_physics/" + f.path: f for f in build.package_files}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = z.namelist()
        if len(names) > 160 or len(set(names)) != len(names):
            raise StudyLedgerError("installed_identity_archive")
        found = {n for n in names if n.startswith("strange_physics/")}
        if found != set(expected):
            raise StudyLedgerError("installed_identity_archive")
        for entry in z.infolist():
            p = PurePosixPath(entry.filename)
            if (
                p.is_absolute()
                or ".." in p.parts
                or "\\" in entry.filename
                or entry.is_dir()
                or stat.S_ISLNK(entry.external_attr >> 16)
                or entry.file_size > 4 * 1024**2
            ):
                raise StudyLedgerError("installed_identity_archive")
            if entry.filename not in expected and not (
                p.parts[0].endswith(".dist-info")
                and (
                    len(p.parts) == 2
                    and p.name in {"METADATA", "WHEEL", "RECORD", "entry_points.txt"}
                    or len(p.parts) == 3
                    and p.parts[1:] == ("licenses", "LICENSE")
                )
            ):
                raise StudyLedgerError("installed_identity_archive")
        if any(p.is_dir() and p.name != "__pycache__" for p in package.iterdir()):
            raise StudyLedgerError("installed_identity_package")
        actual_names = {p.name for p in package.iterdir() if p.is_file()}
        if actual_names != {f.path for f in build.package_files}:
            raise StudyLedgerError("installed_identity_package")
        for name, f in expected.items():
            data = z.read(name)
            installed = _installed_bytes(package / f.path, 4 * 1024**2)
            if (len(data), hashlib.sha256(data).hexdigest()) != (
                f.bytes,
                f.sha256,
            ) or data != installed:
                raise StudyLedgerError("installed_identity_package")
    actual_dependencies = {
        str(p.relative_to(site))
        for p in site.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and package not in p.parents
    }
    if actual_dependencies != {f.path for f in build.dependency_files}:
        raise StudyLedgerError("installed_identity_dependency_set")
    for f in build.dependency_files:
        data = _installed_bytes(site / f.path, 64 * 1024**2)
        if (len(data), hashlib.sha256(data).hexdigest()) != (f.bytes, f.sha256):
            raise StudyLedgerError("installed_identity_dependency")
    actual_engine = engine_fingerprint(reference_registry())
    if actual_engine != build.engine_fingerprint:
        raise StudyLedgerError("installed_identity_engine")
    return ObservedInstallation(
        source_commit=build.source_commit,
        uv_lock_sha256=build.uv_lock_sha256,
        engine_fingerprint=actual_engine,
        installation_sha256=message_sha256(build),
    )
