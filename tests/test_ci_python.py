"""Actual file boundaries for copied CI interpreters; no toolcache mutation."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

from scripts.ci_python import check, copied_executable, create, inspect_file


def binary(root: Path, data: bytes = b"trusted-interpreter") -> Path:
    path = root / "bin/python"
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    path.chmod(0o755)
    return path


def test_copied_interpreter_matches_bytes_and_owned_profile(tmp_path: Path) -> None:
    root = tmp_path / "environment"
    path = binary(root)
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    result = copied_executable(root, expected)
    assert (result["uid"], result["nlink"], result["mode"]) == (os.getuid(), 1, "0o755")
    assert result["sha256"] == expected


@pytest.mark.parametrize("mode", [0o775, 0o777])
def test_shared_source_mode_does_not_authorize_writable_copy(tmp_path: Path, mode: int) -> None:
    path = binary(tmp_path)
    path.chmod(mode)
    assert inspect_file(path, owned=False)["mode"] == oct(mode)
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(path, owned=True)


def test_copied_interpreter_rejects_changed_bytes(tmp_path: Path) -> None:
    path = binary(tmp_path)
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_bytes(b"substituted-interpreter")
    with pytest.raises(ValueError, match="identity differs"):
        copied_executable(tmp_path, expected)


def test_copied_interpreter_rejects_shared_inode(tmp_path: Path) -> None:
    path = binary(tmp_path)
    os.link(path, tmp_path / "alias")
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(path, owned=True)
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(path, owned=False)


def test_copied_interpreter_rejects_symlink(tmp_path: Path) -> None:
    path = binary(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(path)
    with pytest.raises(ValueError, match="symlink"):
        inspect_file(alias, owned=True)


def test_copied_interpreter_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(tmp_path, owned=True)


def test_copied_interpreter_rejects_oversized_file(tmp_path: Path) -> None:
    path = binary(tmp_path)
    with path.open("ab") as stream:
        stream.truncate(64 * 1024**2 + 1)
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(path, owned=True)


def test_copied_interpreter_rejects_foreign_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = binary(tmp_path)
    monkeypatch.setattr(os, "getuid", lambda: -1)
    with pytest.raises(ValueError, match="stat rejected"):
        inspect_file(path, owned=True)


def test_bootstrap_does_not_reuse_existing_environment(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fresh environment"):
        create(tmp_path, tmp_path / "record.json")
    assert not (tmp_path / "record.json").exists()


@pytest.mark.parametrize("replacement", ["bytes", "symlink"])
def test_actual_bootstrap_and_check_reject_replaced_copy(tmp_path: Path, replacement: str) -> None:
    root, record = tmp_path / "environment", tmp_path / "record.json"
    original = create(root, record)
    assert check(root, record) == original
    assert original["copied"]["sha256"] == original["source"]["sha256"]
    assert original["copied"]["nlink"] == 1
    path = root / "bin/python"
    if replacement == "bytes":
        with path.open("ab") as stream:
            stream.write(b"changed")
        expected = "identity differs"
    else:
        path.unlink()
        path.symlink_to(Path(sys.executable).resolve())
        expected = "symlink"
    with pytest.raises(ValueError, match=expected):
        check(root, record)


def test_actual_bootstrap_check_rejects_writable_installed_file(tmp_path: Path) -> None:
    root, record = tmp_path / "environment", tmp_path / "record.json"
    create(root, record)
    site = next(root.glob("lib/python*/site-packages"))
    package = site / "example.py"
    package.write_text("value = 1\n")
    package.chmod(0o644)
    assert check(root, record)["installed_files"] == 1
    package.chmod(0o666)
    with pytest.raises(ValueError, match="stat rejected"):
        check(root, record)
