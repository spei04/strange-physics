"""Fresh lexical inventory and unchanged installed-file trust checks."""

from __future__ import annotations

import hashlib
import json
import platform
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from strange_physics import installed_identity as identity
from strange_physics.installed_identity import BuildFile, TrustedInstallation
from strange_physics.laws import reference_registry
from strange_physics.serialization import engine_fingerprint
from strange_physics.study_ledger import StudyLedgerError


def private(path: Path, value: bytes = b"fixture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    path.chmod(0o600)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@pytest.mark.parametrize("root_name", ["site-packages", "strange_physics", "__pycache__/site"])
def test_dependency_names_preserve_full_lexical_membership(tmp_path: Path, root_name: str) -> None:
    site = tmp_path / root_name
    included = {
        "dependency.py",
        "nested/naïve 数据.py",
        "other/strange_physics/kept.py",
        "mystrange_physics/kept.py",
        "strange_physics_extra/kept.py",
        "__pycache__extra/kept.py",
    }
    excluded = {"strange_physics/module.py", "__pycache__/bytecode.pyc", "nested/__pycache__/x.pyc"}
    for name in included | excluded:
        private(site / name)
    private(Path(str(site) + "-sibling") / "foreign.py")
    (site / "empty").mkdir()
    package = site / "strange_physics"
    legacy = {
        str(path.relative_to(site))
        for path in site.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and package not in path.parents
    }
    assert identity._dependency_names(site) == legacy
    assert legacy == (set() if "__pycache__" in site.parts else included)


def test_project_named_file_and_file_links_are_not_silently_excluded(tmp_path: Path) -> None:
    site = tmp_path / "site"
    private(site / "strange_physics")
    private(site / "target")
    (site / "file-link").symlink_to(site / "target")
    outside = tmp_path / "outside"
    private(outside / "untraversed.py")
    (site / "directory-link").symlink_to(outside, target_is_directory=True)
    assert identity._dependency_names(site) == {"strange_physics", "target", "file-link"}


def test_fresh_inventory_observes_added_and_removed_files(tmp_path: Path) -> None:
    private(tmp_path / "first")
    assert identity._dependency_names(tmp_path) == {"first"}
    private(tmp_path / "second")
    assert identity._dependency_names(tmp_path) == {"first", "second"}
    (tmp_path / "first").unlink()
    assert identity._dependency_names(tmp_path) == {"second"}


def test_every_file_ancestor_including_root_is_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "nested" / "file"
    private(path)
    expected = [path, *path.parents]
    seen: list[Path] = []
    original = Path.is_symlink

    def observe(current: Path) -> bool:
        seen.append(current)
        return original(current)

    monkeypatch.setattr(Path, "is_symlink", observe)
    assert identity._installed_bytes(path, 64) == b"fixture"
    assert seen == expected


@pytest.mark.parametrize("position", ["leaf", "ancestor"])
def test_file_or_ancestor_symlink_is_denied(tmp_path: Path, position: str) -> None:
    actual = tmp_path / "actual" / "file"
    private(actual)
    if position == "leaf":
        path = tmp_path / "leaf"
        path.symlink_to(actual)
    else:
        (tmp_path / "linked").symlink_to(actual.parent, target_is_directory=True)
        path = tmp_path / "linked" / "file"
    with pytest.raises(StudyLedgerError, match="^installed_identity_path$"):
        identity._installed_bytes(path, 64)


def test_root_symlink_check_is_not_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "file"
    private(path)
    original = Path.is_symlink

    def root_denied(current: Path) -> bool:
        return current == Path(current.anchor) or original(current)

    monkeypatch.setattr(Path, "is_symlink", root_denied)
    with pytest.raises(StudyLedgerError, match="^installed_identity_path$"):
        identity._installed_bytes(path, 64)


@pytest.fixture
def synthetic_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[TrustedInstallation, Path]:
    """Small isolated verifier fixture; never changes the installed environment."""
    site = tmp_path / "site"
    package = site / "strange_physics"
    private(package / "__init__.py", b"# synthetic module\n")
    private(site / "nested/dependency.py", b"original")
    private(tmp_path / "python", b"synthetic executable")
    private(tmp_path / "uv.lock", b"synthetic lock")
    wheel = tmp_path / "fixture.zip"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.write(package / "__init__.py", "strange_physics/__init__.py")
    wheel.chmod(0o600)
    source = "a" * 40
    archive_sha = digest(wheel.read_bytes())
    lock_sha = digest((tmp_path / "uv.lock").read_bytes())
    private(
        tmp_path / "provenance.json",
        json.dumps(
            {
                "source_commit": source,
                "uv_lock_sha256": lock_sha,
                "archive_sha256": archive_sha,
                "evidence_kind": "synthetic_installed_snapshot",
            }
        ).encode(),
    )
    monkeypatch.setattr(
        identity, "sysconfig", SimpleNamespace(get_paths=lambda: {"purelib": str(site)})
    )
    monkeypatch.setattr(
        identity, "strange_physics", SimpleNamespace(__file__=str(package / "__init__.py"))
    )
    monkeypatch.setattr(
        identity, "sys", SimpleNamespace(executable=str(tmp_path / "python"), modules={})
    )
    build = TrustedInstallation(
        evidence_kind="synthetic_installed_snapshot",
        source_commit=source,
        uv_lock_sha256=lock_sha,
        lock_path=str(tmp_path / "uv.lock"),
        archive_path=str(wheel),
        archive_sha256=archive_sha,
        provenance_path=str(tmp_path / "provenance.json"),
        provenance_sha256=digest((tmp_path / "provenance.json").read_bytes()),
        python_version=platform.python_version(),
        python_executable_sha256=digest((tmp_path / "python").read_bytes()),
        engine_fingerprint=engine_fingerprint(reference_registry()),
        package_files=(
            BuildFile(
                path="__init__.py",
                sha256=digest((package / "__init__.py").read_bytes()),
                bytes=(package / "__init__.py").stat().st_size,
            ),
        ),
        dependency_files=(
            BuildFile(path="nested/dependency.py", sha256=digest(b"original"), bytes=8),
        ),
    )
    return build, site


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("changed", "installed_identity_dependency"),
        ("extra", "installed_identity_dependency_set"),
        ("missing", "installed_identity_dependency_set"),
        ("symlink", "installed_identity_path"),
        ("hardlink", "installed_identity_path"),
        ("writable", "installed_identity_path"),
    ],
)
def test_public_verifier_keeps_fresh_membership_bytes_and_file_guards(
    synthetic_installation: tuple[TrustedInstallation, Path], mutation: str, error: str
) -> None:
    build, site = synthetic_installation
    assert identity.verify_native_installation(build).source_commit == build.source_commit
    path = site / "nested/dependency.py"
    if mutation == "changed":
        private(path, b"modified")
    elif mutation == "extra":
        private(site / "extra.py")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        target = site.parent / "target"
        private(target, b"original")
        path.unlink()
        path.symlink_to(target)
    elif mutation == "hardlink":
        (site.parent / "another-link").hardlink_to(path)
    elif mutation == "writable":
        path.chmod(0o622)
    else:
        raise AssertionError(mutation)
    with pytest.raises(StudyLedgerError, match=f"^{error}$"):
        identity.verify_native_installation(build)
