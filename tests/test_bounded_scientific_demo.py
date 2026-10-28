"""Nonnumerical example guards; full demo execution is separately bounded."""

from __future__ import annotations

import hashlib
import math
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from examples import bounded_scientific_demo as demo
from examples.bounded_scientific_demo import _target_met, _write


@pytest.fixture(autouse=True)
def restore_process_umask() -> Iterator[None]:
    original = os.umask(0o077)
    os.umask(original)
    try:
        yield
    finally:
        os.umask(original)


@pytest.mark.parametrize(
    ("values", "claimed", "expected"),
    [
        ((0.0001,) * 24, True, True),
        ((0.0001,) * 23, True, False),
        ((0.0001,) * 23 + (0.002,), True, False),
        ((0.0001,) * 23 + (math.nan,), True, False),
        ((0.0001,) * 24, False, False),
    ],
)
def test_demo_requires_every_held_out_target(
    values: tuple[float | None, ...], claimed: bool, expected: bool
) -> None:
    assert _target_met(values, claimed) is expected


def test_demo_retains_existing_output(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    _write(path, b"original")
    with pytest.raises(FileExistsError):
        _write(path, b"replacement")
    assert path.read_bytes() == b"original"
    assert path.stat().st_mode & 0o777 == 0o600


def test_existing_demo_directory_rejects_before_any_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "existing"
    output.mkdir(mode=0o700)
    retained = output / "keep"
    retained.write_bytes(b"original")

    def forbidden(*args: object) -> dict[str, object]:
        raise AssertionError("No source or numerical command may run")

    monkeypatch.setattr(demo, "_identity", forbidden)
    monkeypatch.setattr(demo, "_run", forbidden)
    assert demo.main([
        "--output", str(output), "--source-commit", "0" * 40,
        "--cells", "16", "--discrepancy", "0.25",
    ]) == 2
    assert retained.read_bytes() == b"original"
    assert sorted(p.name for p in output.iterdir()) == ["keep"]


def test_cli_failure_retains_partial_run_and_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "failed"
    calls: list[list[str]] = []

    def identity(commit: str) -> dict[str, object]:
        return {"source_commit": commit, "test": "nonnumerical injected CLI failure"}

    def fail(argv: list[str]) -> int:
        calls.append(argv)
        return 1

    monkeypatch.setattr(demo, "_identity", identity)
    monkeypatch.setattr(demo, "physics_main", fail)
    assert demo.main([
        "--output", str(output), "--source-commit", "0" * 40,
        "--cells", "16", "--discrepancy", "0.25",
    ]) == 2
    assert len(calls) == 1 and calls[0][0] == "investigate"
    assert (output / "command-0.json").is_file()
    assert (output / "failure.json").is_file()
    assert not (output / "command-1.json").exists()
    assert not (output / "belief").exists()
    assert not (output / "completion.json").exists()


def test_installed_identity_includes_typing_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "uv.lock").write_bytes(b"test lock")
    environment = tmp_path / "environment"
    package = environment / "strange_physics"
    package.mkdir(parents=True)
    files = {"__init__.py": b"", "py.typed": b""}
    entries = []
    for name, data in files.items():
        (package / name).write_bytes(data)
        blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data, usedforsecurity=False
        ).hexdigest()
        entries.append(f"100644 blob {blob}\tsrc/strange_physics/{name}")

    def git(*args: str) -> str:
        if args[0] == "rev-parse":
            return "a" * 40 + "\n" + "b" * 40 + "\n"
        if args[0] == "status":
            return ""
        assert args == ("ls-tree", "-r", "HEAD", "src/strange_physics")
        return "\n".join(entries) + "\n"

    monkeypatch.setattr(demo, "SOURCE_ROOT", source)
    monkeypatch.setattr(demo, "_git", git)
    monkeypatch.setattr(demo.strange_physics, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr(demo.sys, "prefix", str(environment))
    result = demo._identity("a" * 40)
    assert result["installed_package_sha256"] == {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()
    }
