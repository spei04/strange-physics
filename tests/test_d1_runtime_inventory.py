"""Owned synthetic bytes and metadata parity; no installation, force evaluation or child launch."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts import d1_runtime_inventory as inventory


def put(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(raw)
    path.chmod(0o600)


@pytest.fixture
def owned(monkeypatch: pytest.MonkeyPatch) -> None:
    # /tmp is deliberately not a protected runtime. Test only owned fixture I/O.
    monkeypatch.setattr(inventory.control, "_ancestors", lambda path: None)


def test_inventory_deduplicates_overlapping_roots_and_alias_target(
    tmp_path: Path, owned: None
) -> None:
    venv = tmp_path / "venv"
    put(venv / "lib/value", b"value")
    (venv / "lib64").symlink_to("lib")
    result = inventory.collect_inventory(
        (venv, venv / "lib"), (), stdlib=tmp_path / "stdlib", venv=venv
    )
    assert len(result["files"]) == 1
    assert len(result["directories"]) == 2
    assert result["links"] == [{"path": str(venv / "lib64"), "uid": os.getuid(), "target": "lib"}]


@pytest.mark.parametrize("kind", ["link", "fifo", "writable", "hardlink"])
def test_inventory_rejects_unreviewed_or_unprotected_entries(
    tmp_path: Path, owned: None, kind: str
) -> None:
    root = tmp_path / "root"
    root.mkdir(mode=0o700)
    path = root / "bad"
    if kind == "link":
        path.symlink_to(tmp_path / "elsewhere")
    elif kind == "fifo":
        os.mkfifo(path, mode=0o600)
    else:
        put(path, b"x")
        if kind == "writable":
            path.chmod(0o666)
        else:
            os.link(path, root / "second")
    with pytest.raises((ValueError, OSError)):
        inventory.collect_inventory((root,), (), stdlib=tmp_path / "stdlib", venv=tmp_path / "venv")


@pytest.mark.parametrize("bound", ["entries", "payload"])
def test_inventory_stops_at_cumulative_limits(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch, bound: str
) -> None:
    put(tmp_path / "root/a", b"abc")
    put(tmp_path / "root/b", b"def")
    if bound == "entries":
        monkeypatch.setattr(inventory.control, "ENTRY_LIMIT", 2)
    else:
        monkeypatch.setattr(inventory.control, "TOTAL_INPUT_LIMIT", 5)
    with pytest.raises(ValueError):
        inventory.collect_inventory(
            (tmp_path / "root",), (), stdlib=tmp_path / "stdlib", venv=tmp_path / "venv"
        )


def fixture_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, bytes]]:
    root, site = tmp_path / "source", tmp_path / "site"
    package = site / "strange_physics"
    content = {
        "__init__.py": b'__version__ = "0.1.0a1"\n',
        "laws.py": (
            "def reference_registry():\n"
            "    registry = LawRegistry()\n"
            '    registry.register("spring", lambda p: None, implementation_id="spring-v1")\n'
            '    registry.register("radial", lambda p: None, implementation_id="radial-v1")\n'
            '    registry.register("velocity", lambda p: None, implementation_id="velocity-v1")\n'
            "    return registry\n"
        ).encode(),
        "py.typed": b"",
    }
    original = inventory.ci_artifacts
    monkeypatch.setattr(
        inventory,
        "ci_artifacts",
        SimpleNamespace(
            MODULES=frozenset(content),
            MAX_MEMBER_BYTES=original.MAX_MEMBER_BYTES,
            MAX_ARCHIVE_BYTES=original.MAX_ARCHIVE_BYTES,
            MAX_MEMBERS=original.MAX_MEMBERS,
            check_name=original.check_name,
        ),
    )
    for name, raw in content.items():
        put(root / "src/strange_physics" / name, raw)
        put(package / name, raw)
    put(site / "numpy-2.dist-info/METADATA", b"Name: numpy\nVersion: 2.0\n")
    put(site / "pydantic-2.dist-info/METADATA", b"Name: pydantic\nVersion: 2.0\n")
    lock, requirements, interpreter = (
        root / "uv.lock",
        tmp_path / "requirements",
        tmp_path / "python",
    )
    put(lock, b"fixed lock")
    put(requirements, b"fixed exact export\n")
    put(interpreter, b"synthetic executable, never executed")
    wheel = tmp_path / "strange_physics-0.1.0a1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, raw in content.items():
            archive.writestr("strange_physics/" + name, raw)
    wheel.chmod(0o600)
    provenance = tmp_path / "provenance.json"
    candidate = {
        "schema_version": "strange-physics.release-candidate.v1",
        "repository": "spei04/strange-physics",
        "source_commit": "a" * 40,
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "uv_version": "0.13.4",
        "runtime_requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
        "distribution_files": [
            {
                "name": wheel.name,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "bytes": wheel.stat().st_size,
            },
            {"name": "strange_physics-0.1.0a1.tar.gz", "sha256": "b" * 64, "bytes": 1},
        ],
    }
    put(provenance, json.dumps(candidate).encode())
    return {
        "checkout": root,
        "site": site,
        "interpreter_file": interpreter,
        "python_version": "3.12.3",
        "source_commit": "a" * 40,
        "wheel": wheel,
        "provenance": provenance,
        "expected_provenance_sha256": hashlib.sha256(provenance.read_bytes()).hexdigest(),
        "requirements": requirements,
    }, content


def test_installation_materializes_actual_membership(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    args, content = fixture_installation(tmp_path, monkeypatch)
    record = inventory.materialize_installation(**args)
    assert {item["path"] for item in record["package_files"]} == set(content)
    assert {item["path"] for item in record["dependency_files"]} == {
        "numpy-2.dist-info/METADATA",
        "pydantic-2.dist-info/METADATA",
    }
    assert record["source_commit"] == "a" * 40
    assert (
        record["python_executable_sha256"]
        == hashlib.sha256(args["interpreter_file"].read_bytes()).hexdigest()
    )
    # A declaration of the existing evidence kind is not an independent acceptance.
    assert set(record) == {
        "evidence_kind",
        "source_commit",
        "uv_lock_sha256",
        "lock_path",
        "archive_path",
        "archive_sha256",
        "provenance_path",
        "provenance_sha256",
        "python_version",
        "python_executable_sha256",
        "engine_fingerprint",
        "package_files",
        "dependency_files",
    }


@pytest.mark.parametrize(
    "fault",
    [
        "provenance",
        "requirements",
        "source",
        "installed",
        "lock",
        "wheel",
        "extra_package",
        "duplicate_metadata",
    ],
)
def test_materialization_rejects_mismatched_actual_bytes(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    args, _ = fixture_installation(tmp_path, monkeypatch)
    paths = {
        "provenance": args["provenance"],
        "requirements": args["requirements"],
        "source": args["checkout"] / "src/strange_physics/laws.py",
        "installed": args["site"] / "strange_physics/laws.py",
        "lock": args["checkout"] / "uv.lock",
        "wheel": args["wheel"],
    }
    if fault in paths:
        paths[fault].write_bytes(paths[fault].read_bytes() + b"\n")
    elif fault == "extra_package":
        put(args["site"] / "strange_physics/extra.py", b"extra")
    else:
        put(args["site"] / "numpy-other.dist-info/METADATA", b"Name: numpy\nVersion: 9\n")
    with pytest.raises(ValueError):
        inventory.materialize_installation(**args)


def test_existing_engine_digest_matches_metadata_and_source_changes(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    args, _ = fixture_installation(tmp_path, monkeypatch)
    original = inventory.materialize_installation(**args)["engine_fingerprint"]
    put(args["site"] / "numpy-2.dist-info/METADATA", b"Name: numpy\nVersion: 2.1\n")
    changed_dependency = inventory.materialize_installation(**args)["engine_fingerprint"]
    args["python_version"] = "3.12.4"
    changed_runtime = inventory.materialize_installation(**args)["engine_fingerprint"]
    assert len({original, changed_dependency, changed_runtime}) == 3


def test_records_are_exclusive_owner_only_and_bounded(tmp_path: Path, owned: None) -> None:
    path = tmp_path / "record.json"
    digest = inventory.write_record(path, {"observed": 1})
    assert path.stat().st_mode & 0o777 == 0o600
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    with pytest.raises(FileExistsError):
        inventory.write_record(path, {"observed": 2})
    assert json.loads(path.read_bytes()) == {"observed": 1}
    with pytest.raises(ValueError, match="ceiling"):
        inventory.encoded({"value": "x" * inventory.control.PLAN_LIMIT})


def test_materialize_plan_rejects_supplied_inventory() -> None:
    with pytest.raises(ValueError, match="freshly"):
        inventory.materialize_plan({"files": []}, runtime_files=())


def test_materialize_plan_requires_explicit_runtime_closure() -> None:
    with pytest.raises(ValueError, match="closure"):
        inventory.materialize_plan({}, runtime_files=())


def test_engine_digest_parity_with_existing_implementation(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Import existing definitions for metadata parity only; no law is built/evaluated.
    from strange_physics import serialization
    from strange_physics.laws import LawRegistry

    args, _ = fixture_installation(tmp_path, monkeypatch)
    record = inventory.materialize_installation(**args)
    registry = LawRegistry()
    for kind in ("spring", "radial", "velocity"):
        registry.register(
            kind,
            lambda parameters: pytest.fail("No law construction"),
            implementation_id=kind + "-v1",
        )
    monkeypatch.setattr(serialization, "__version__", "0.1.0a1")
    monkeypatch.setattr(serialization, "platform", SimpleNamespace(python_version=lambda: "3.12.3"))
    monkeypatch.setattr(serialization, "version", lambda name: "2.0")
    monkeypatch.setattr(
        serialization, "__file__", str(args["site"] / "strange_physics/serialization.py")
    )
    assert record["engine_fingerprint"] == serialization.engine_fingerprint(registry)


def test_plan_materialization_joins_required_source_and_calls_existing_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_d1_bootstrap_control import synthetic_plan

    complete = synthetic_plan(tmp_path, monkeypatch)
    binding = {
        key: value
        for key, value in complete.items()
        if key not in ("files", "directories", "links")
    }
    selected: list[tuple[Path, ...]] = []

    def census(roots: tuple[Path, ...], files: tuple[Path, ...], **kwargs: Any) -> dict[str, Any]:
        assert roots == (Path(binding["stdlib"]), Path(binding["venv_root"]))
        selected.append(files)
        return {key: complete[key] for key in ("files", "directories", "links")}

    monkeypatch.setattr(inventory, "collect_inventory", census)
    monkeypatch.setattr(
        inventory, "_bytes", lambda path, limit: inventory.control._read(path, limit, os.getuid())
    )
    runtime = Path("/reviewed/native.so")
    observed = inventory.materialize_plan(binding, runtime_files=(runtime,))
    assert observed == complete
    assert runtime in selected[0]
    for source in (
        "d1_owned_capture.py",
        "d1_capture_owner.py",
        "d1_capture_descendant.py",
        "grid_q1_supervisor.py",
    ):
        assert Path(binding["checkout"]) / "scripts" / source in selected[0]
    # The existing validator, rather than a new trust flag, rejects an invalid join.
    binding["source_commit"] = "b" * 40
    with pytest.raises(ValueError, match="source differs"):
        inventory.materialize_plan(binding, runtime_files=(runtime,))


@pytest.mark.parametrize("replacement", [b"abcd", b"ab"], ids=["growth", "shrink"])
def test_inventory_binds_read_to_original_extent(
    tmp_path: Path, owned: None, monkeypatch: pytest.MonkeyPatch, replacement: bytes
) -> None:
    path = tmp_path / "root/value"
    put(path, b"abc")
    original = inventory._bytes
    limits: list[int] = []

    def changed(value: Path, limit: int) -> bytes:
        assert value == path
        limits.append(limit)
        value.write_bytes(replacement)
        return original(value, limit)

    monkeypatch.setattr(inventory, "_bytes", changed)
    with pytest.raises(ValueError):
        inventory.collect_inventory(
            (path.parent,), (), stdlib=tmp_path / "stdlib", venv=tmp_path / "venv"
        )
    assert limits == [3]


@pytest.mark.parametrize("missing", ["d1_capture_owner.py", "d1_capture_descendant.py"])
def test_materialization_cannot_omit_missing_fixed_entry_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    from test_d1_bootstrap_control import synthetic_plan

    complete = synthetic_plan(tmp_path, monkeypatch)
    binding = {
        key: value
        for key, value in complete.items()
        if key not in ("files", "directories", "links")
    }
    expected = Path(binding["checkout"]) / "scripts" / missing

    def census(roots: tuple[Path, ...], files: tuple[Path, ...], **kwargs: Any) -> dict[str, Any]:
        # Perform the actual missing-file observation only for this mandatory
        # input; other source/custody fields use the existing structural fixture.
        for path in files:
            if path == expected:
                path.lstat()
        return {key: complete[key] for key in ("files", "directories", "links")}

    monkeypatch.setattr(inventory, "collect_inventory", census)
    monkeypatch.setattr(
        inventory, "_bytes", lambda path, limit: inventory.control._read(path, limit, os.getuid())
    )
    with pytest.raises(FileNotFoundError):
        inventory.materialize_plan(binding, runtime_files=(Path("/reviewed/native.so"),))
