from __future__ import annotations

import io
import json
import stat
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest

from scripts.ci_artifacts import MODULES, read_archive, validate_archives, write_provenance
from scripts.ci_gate import require_success

STEM = "strange_physics-0.1.0a1"


@pytest.mark.parametrize("status", ["failure", "cancelled", "skipped", "neutral", "", None])
@pytest.mark.parametrize("job", ["checks", "security"])
def test_ci_gate_rejects_any_required_job_without_success(job: str, status: Any) -> None:
    needs = {"checks": {"result": "success"}, "security": {"result": "success"}}
    needs[job] = {"result": status}
    with pytest.raises(ValueError, match="did not succeed"):
        require_success(needs)


@pytest.mark.parametrize(
    "needs",
    [
        None,
        [],
        {},
        {"checks": {"result": "success"}},
        {"checks": {"result": "success"}, "security": None},
        {"checks": {"result": "success"}, "security": {"result": "success"}, "extra": {}},
    ],
)
def test_ci_gate_rejects_missing_unknown_or_malformed_results(needs: Any) -> None:
    with pytest.raises(ValueError):
        require_success(needs)


def test_ci_gate_accepts_only_complete_success() -> None:
    require_success({"checks": {"result": "success"}, "security": {"result": "success"}})


def make_source(root: Path) -> None:
    package = root / "src/strange_physics"
    package.mkdir(parents=True)
    for name in MODULES:
        (package / name).write_bytes(b"" if name == "py.typed" else b"# synthetic package\n")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "strange-physics"\nversion = "0.1.0a1"\nrequires-python = ">=3.12"\n'
    )
    (root / "README.md").write_text("Synthetic fixture, not a release.\n")
    (root / "LICENSE").write_text("Synthetic license fixture.\n")
    (root / ".gitignore").write_text(".venv/\n.env\n")
    (root / "uv.lock").write_text("Synthetic lock fixture.\n")


def archive_contents(root: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    metadata = b"Name: strange-physics\nVersion: 0.1.0a1\nRequires-Python: >=3.12\n"
    wheel = {
        f"strange_physics/{name}": (root / "src/strange_physics" / name).read_bytes()
        for name in MODULES
    }
    info = f"{STEM}.dist-info"
    wheel.update(
        {
            f"{info}/METADATA": metadata,
            f"{info}/WHEEL": b"Wheel-Version: 1.0\n",
            f"{info}/entry_points.txt": (
                b"[console_scripts]\nstrange-physics=strange_physics.cli:main"
            ),
            f"{info}/RECORD": b"",
            f"{info}/licenses/LICENSE": (root / "LICENSE").read_bytes(),
        }
    )
    sdist = {
        f"{STEM}/src/strange_physics/{name}": (root / "src/strange_physics" / name).read_bytes()
        for name in MODULES
    }
    sdist.update(
        {
            f"{STEM}/{name}": (root / name).read_bytes()
            for name in ["README.md", "LICENSE", "pyproject.toml", ".gitignore"]
        }
    )
    sdist[f"{STEM}/PKG-INFO"] = metadata
    return wheel, sdist


def write_archives(
    dist: Path, wheel: dict[str, bytes], sdist: dict[str, bytes]
) -> tuple[Path, Path]:
    dist.mkdir(exist_ok=True)
    paths = dist / f"{STEM}-py3-none-any.whl", dist / f"{STEM}.tar.gz"
    with zipfile.ZipFile(paths[0], "w") as archive:
        for name, content in wheel.items():
            archive.writestr(name, content)
    with tarfile.open(paths[1], "w:gz") as source:
        for name, content in sdist.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            source.addfile(member, io.BytesIO(content))
    return paths


def test_candidate_allowlist_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "source"
    make_source(root)
    paths = write_archives(tmp_path / "dist", *archive_contents(root))
    assert validate_archives(tmp_path / "dist", root) == paths
    requirements = tmp_path / "runtime.txt"
    requirements.write_text("Synthetic requirements fixture.\n")
    for key, value in {
        "GITHUB_SHA": "a" * 40,
        "GITHUB_REPOSITORY": "spei04/strange-physics",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
    }.items():
        monkeypatch.setenv(key, value)
    write_provenance(paths, root, requirements)
    manifest = json.loads((tmp_path / "dist/provenance.json").read_text())
    assert manifest["source_commit"] == "a" * 40
    assert {item["name"] for item in manifest["distribution_files"]} == {p.name for p in paths}
    checksums = (tmp_path / "dist/SHA256SUMS").read_text().splitlines()
    assert len(checksums) == 3
    assert {line.split("  ")[1] for line in checksums} == {
        paths[0].name,
        paths[1].name,
        "provenance.json",
    }


@pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
@pytest.mark.parametrize("injection", ["runs/observations.json", ".env", "../outside", "/absolute"])
def test_candidate_rejects_unlisted_or_unsafe_archive_content(
    tmp_path: Path, archive_kind: str, injection: str
) -> None:
    root = tmp_path / "source"
    make_source(root)
    wheel, sdist = archive_contents(root)
    selected = wheel if archive_kind == "wheel" else sdist
    selected[injection] = b"must not ship"
    write_archives(tmp_path / "dist", wheel, sdist)
    with pytest.raises(ValueError):
        validate_archives(tmp_path / "dist", root)


@pytest.mark.parametrize("extra", ["debug.json", ".gitignore"])
def test_candidate_rejects_source_drift_and_extra_files(tmp_path: Path, extra: str) -> None:
    root = tmp_path / "source"
    make_source(root)
    wheel, sdist = archive_contents(root)
    wheel["strange_physics/cli.py"] = b"different code"
    write_archives(tmp_path / "dist", wheel, sdist)
    with pytest.raises(ValueError, match="differs from reviewed source"):
        validate_archives(tmp_path / "dist", root)
    (tmp_path / "dist" / extra).write_text("{}")
    with pytest.raises(ValueError, match="unexpected=") as error:
        validate_archives(tmp_path / "dist", root)
    assert repr(extra) in str(error.value)


@pytest.mark.parametrize("kind", ["zip", "tar"])
def test_candidate_rejects_archive_symlinks(tmp_path: Path, kind: str) -> None:
    if kind == "zip":
        path = tmp_path / "bad.whl"
        with zipfile.ZipFile(path, "w") as archive:
            member = zipfile.ZipInfo("strange_physics/cli.py")
            member.create_system = 3
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(member, "/private/evidence")
    else:
        path = tmp_path / "bad.tar.gz"
        with tarfile.open(path, "w:gz") as source:
            entry = tarfile.TarInfo("strange_physics/cli.py")
            entry.type = tarfile.SYMTYPE
            entry.linkname = "/private/evidence"
            source.addfile(entry)
    with pytest.raises(ValueError, match="regular files"):
        read_archive(path)


def test_candidate_rejects_duplicate_members(tmp_path: Path) -> None:
    path = tmp_path / "bad.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("same.py", b"first")
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("same.py", b"second")
    with pytest.raises(ValueError, match="Duplicate"):
        read_archive(path)


def test_candidate_rejects_noncommit_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_SHA", "main")
    with pytest.raises(ValueError, match="full source commit"):
        write_provenance((tmp_path / "a", tmp_path / "b"), tmp_path, tmp_path / "runtime")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_archive_allowlist_diagnostics_report_names_only(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "source"
    make_source(root)
    wheel, sdist = archive_contents(root)
    selected = wheel if kind == "wheel" else sdist
    prefix = "strange_physics" if kind == "wheel" else f"{STEM}/src/strange_physics"
    missing = f"{prefix}/sdk.py"
    unexpected = f"{prefix}/private.json"
    del selected[missing]
    selected[unexpected] = b"do not print this content"
    write_archives(tmp_path / "dist", wheel, sdist)
    with pytest.raises(ValueError, match="allowlist") as error:
        validate_archives(tmp_path / "dist", root)
    assert repr(missing) in str(error.value)
    assert repr(unexpected) in str(error.value)
    assert "do not print this content" not in str(error.value)


def test_source_archive_gitignore_must_match_reviewed_bytes(tmp_path: Path) -> None:
    root = tmp_path / "source"
    make_source(root)
    wheel, sdist = archive_contents(root)
    sdist[f"{STEM}/.gitignore"] = b"different repository metadata"
    write_archives(tmp_path / "dist", wheel, sdist)
    with pytest.raises(ValueError, match="Source archive differs from reviewed source"):
        validate_archives(tmp_path / "dist", root)
