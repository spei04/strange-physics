"""Synthetic files and fake child handles; never launch the D1 bootstrap."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts import d1_bootstrap_control as control


def fake_process_api(start: Any) -> SimpleNamespace:
    return SimpleNamespace(
        Popen=start,
        TimeoutExpired=subprocess.TimeoutExpired,
        SubprocessError=subprocess.SubprocessError,
        DEVNULL=subprocess.DEVNULL,
        STDOUT=subprocess.STDOUT,
    )


def test_standalone_entry_is_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    assert control.main() == 64
    assert "disabled" in capsys.readouterr().out


@pytest.mark.parametrize("value", ["relative", "/a/../b", "/a//b", "", None])
def test_reject_noncanonical_paths(value: object) -> None:
    with pytest.raises(control.PreflightError):
        control._path(value)


@pytest.mark.parametrize("value", ["a" * 63, "A" * 64, None])
def test_reject_bad_digest(value: object) -> None:
    with pytest.raises(control.PreflightError):
        control._digest(value)


def test_duplicate_record_key_is_rejected() -> None:
    with pytest.raises(control.PreflightError, match="Duplicate"):
        control._object_pairs([("a", 1), ("a", 2)])


def test_writable_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "entry"
    path.write_bytes(b"x")
    path.chmod(0o664)
    with pytest.raises(control.PreflightError, match="Custody"):
        control._safe_mode(path.stat(), os.getuid())


def test_regular_file_link_count_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "entry"
    path.write_bytes(b"x")
    path.chmod(0o600)
    os.link(path, tmp_path / "alias")
    with pytest.raises(control.PreflightError, match="one link"):
        control._safe_mode(path.stat(), os.getuid())


def test_writable_ancestor_is_rejected(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(mode=0o777)
    parent.chmod(0o777)
    with pytest.raises(control.PreflightError, match="Writable ancestor"):
        control._ancestors(parent / "entry")


def test_read_bound_and_no_follow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "entry"
    path.write_bytes(b"abc")
    path.chmod(0o600)
    monkeypatch.setattr(control, "_ancestors", lambda path: None)
    assert control._read(path, 3, os.getuid()) == b"abc"
    with pytest.raises(control.PreflightError, match="bound"):
        control._read(path, 2, os.getuid())
    link = tmp_path / "alias"
    link.symlink_to(path)
    with pytest.raises(OSError):
        control._read(link, 3, os.getuid())


def test_record_hash_and_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "plan"
    raw = b'{"version":"synthetic"}'
    path.write_bytes(raw)
    path.chmod(0o600)
    monkeypatch.setattr(control, "_ancestors", lambda path: None)
    assert control.read_plan(path, hashlib.sha256(raw).hexdigest()) == {"version": "synthetic"}
    with pytest.raises(control.PreflightError, match="digest"):
        control.read_plan(path, "0" * 64)


def synthetic_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """A structural inventory fixture; mocked reads do not establish real custody."""
    root = tmp_path / "checkout"
    venv = tmp_path / "venv"
    (venv / "bin").mkdir(parents=True, mode=0o700)
    site = venv / "lib/python3.12/site-packages"
    stdlib = tmp_path / "stdlib"
    site.mkdir(parents=True, mode=0o700)
    stdlib.mkdir(mode=0o700)
    package = site / "strange_physics"
    package.mkdir(mode=0o700)
    payloads: dict[str, bytes] = {}

    def add(path: Path, raw: bytes = b"synthetic source\n") -> None:
        payloads[str(path)] = raw
        if path.is_relative_to(site) or path == venv / "pyvenv.cfg":
            path.write_bytes(raw)
            path.chmod(0o600)

    routes: dict[str, str] = {}
    for name in control.HELPERS:
        path = root / "tests" / (name + ".py")
        routes[name] = str(path)
        add(path)
    for name in control.NATIVE_MODULES:
        rel = name.replace(".", "/") + ("/__init__.py" if name == "strange_physics" else ".py")
        path = site / rel
        routes[name] = str(path)
        add(path)
        add(root / "src" / rel)
    for rel in control.SOURCE_PIN_PATHS:
        add(root / rel)
    controller = Path(control.__file__).absolute()
    interpreter = Path(sys.executable).resolve()
    add(controller)
    add(interpreter)
    (venv / "bin/python").symlink_to(interpreter)
    add(venv / "pyvenv.cfg", b"include-system-site-packages = false\nversion_info = 3.12.3\n")
    dependency = site / "dependency.py"
    add(dependency)
    lock, archive, provenance = (tmp_path / name for name in ("lock", "archive", "provenance"))
    for path in (lock, archive, provenance):
        add(path)
    digest = hashlib.sha256(b"synthetic source\n").hexdigest()
    installation = {
        "evidence_kind": "accepted_release_candidate",
        "source_commit": "a" * 40,
        "python_version": "3.12.3",
        "python_executable_sha256": digest,
        "lock_path": str(lock),
        "uv_lock_sha256": digest,
        "archive_path": str(archive),
        "archive_sha256": digest,
        "provenance_path": str(provenance),
        "provenance_sha256": digest,
        "package_files": [
            {"path": path.name, "sha256": digest, "bytes": 17} for path in sorted(package.iterdir())
        ],
        "dependency_files": [{"path": "dependency.py", "sha256": digest, "bytes": 17}],
    }
    record = tmp_path / "installation.json"
    add(record, json.dumps(installation).encode())
    monkeypatch.setattr(control, "_ancestors", lambda path: None)

    def fake_read(path: Path, limit: int, uid: int) -> bytes:
        assert uid in (0, os.getuid())
        raw = payloads[str(path)]
        assert len(raw) <= limit
        return raw

    monkeypatch.setattr(control, "_read", fake_read)
    return {
        "version": "d1-protected-capture-v1",
        "source_commit": "a" * 40,
        "checkout": str(root),
        "interpreter": str(venv / "bin/python"),
        "venv_root": str(venv),
        "python_version": "3.12.3",
        "startup_hook_files": [],
        "absent_startup_paths": [],
        "bootstrap": routes["d1_bootstrap"],
        "controller": str(controller),
        "controller_interpreter": str(interpreter),
        "site_packages": str(site),
        "stdlib": str(stdlib),
        "installation_record": str(record),
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "uid": os.getuid(),
            }
            for path, raw in payloads.items()
        ],
        "directories": [
            {"path": str(path), "uid": os.getuid(), "entries": sorted(os.listdir(path))}
            for path in (
                venv,
                venv / "bin",
                venv / "lib",
                venv / "lib/python3.12",
                site,
                package,
                stdlib,
            )
        ],
        "links": [
            {"path": str(venv / "bin/python"), "uid": os.getuid(), "target": str(interpreter)}
        ],
        "import_map": routes,
        "startup_sys_path": [str(site), str(stdlib)],
        "frozen_modules": ["os"],
        "builtin_modules": ["sys"],
    }


def test_structural_inventory_accepts_exact_routes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = synthetic_plan(tmp_path, monkeypatch)
    hashes = control.validate_plan(plan)
    assert plan["bootstrap"] in hashes


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_route",
        "checkout_native",
        "source_mismatch",
        "unlisted_member",
        "missing_runtime",
        "controller",
        "unapproved_link",
        "duplicate",
        "extra_field",
    ],
)
def test_inventory_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    plan = synthetic_plan(tmp_path, monkeypatch)
    if mutation == "missing_route":
        del plan["import_map"]["d1_originals"]
    elif mutation == "checkout_native":
        plan["import_map"]["strange_physics"] = str(Path(plan["checkout"]) / "src/strange_physics")
    elif mutation == "source_mismatch":
        plan["files"] = [
            item
            for item in plan["files"]
            if item["path"] != str(Path(plan["checkout"]) / "src/strange_physics/contracts.py")
        ]
    elif mutation == "unlisted_member":
        plan["directories"][0]["entries"].append("missing.py")
    elif mutation == "missing_runtime":
        plan["directories"] = [
            item for item in plan["directories"] if item["path"] != plan["stdlib"]
        ]
    elif mutation == "controller":
        plan["controller"] = "/wrong/controller.py"
    elif mutation == "unapproved_link":
        plan["links"].append({"path": "/wrong/link", "target": "/wrong", "uid": os.getuid()})
    elif mutation == "duplicate":
        plan["files"].append(plan["files"][0])
    else:
        plan["trusted"] = True
    with pytest.raises(control.PreflightError):
        control.validate_plan(plan)


def test_failed_preflight_never_starts_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts: list[object] = []

    def reject(path: Path, digest: str) -> dict[str, Any]:
        raise control.PreflightError("missing custody")

    monkeypatch.setattr(control, "read_plan", reject)
    monkeypatch.setattr(control, "subprocess", fake_process_api(lambda *a, **k: attempts.append(a)))
    with pytest.raises(control.PreflightError, match="custody"):
        control.launch(tmp_path / "missing", "a" * 64, tmp_path / "output")
    assert attempts == []
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("outcome", ["success", "nonzero", "timeout", "malformed", "custody"])
def test_owned_fake_child_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    plan = {
        "interpreter": "/fixed/python",
        "bootstrap": "/fixed/bootstrap.py",
        "source_commit": "a" * 40,
        "checkout": "/fixed/source",
        "venv_root": "/fixed/venv",
        "stdlib": "/fixed/stdlib",
    }
    validations: list[object] = []
    launches: list[tuple[list[str], dict[str, Any]]] = []
    killed: list[bool] = []
    waits: list[int] = []
    monkeypatch.setattr(control, "read_plan", lambda *args: plan)
    monkeypatch.setattr(control, "_ancestors", lambda path: None)

    def validate(value: dict[str, Any]) -> dict[str, str]:
        validations.append(value)
        if len(validations) == 2 and outcome == "custody":
            raise control.PreflightError("changed")
        return {}

    monkeypatch.setattr(control, "validate_plan", validate)

    class FakeChild:
        def wait(self, timeout: int) -> int:
            waits.append(timeout)
            if outcome == "timeout" and len(waits) == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            return 1 if outcome == "nonzero" else 0

        def kill(self) -> None:
            killed.append(True)

    def start(argv: list[str], **kwargs: Any) -> FakeChild:
        launches.append((argv, kwargs))
        report = {
            "kind": "d1-capture-only",
            "source_commit": plan["source_commit"],
            "owners": 13,
            "original_methods": 22,
            "emitter": "math.exp",
            "primitive_calls_permitted": False,
            "retention_activated": False,
        }
        kwargs["stdout"].write(
            b"invalid" if outcome == "malformed" else json.dumps(report).encode()
        )
        kwargs["stdout"].flush()
        return FakeChild()

    monkeypatch.setattr(control, "subprocess", fake_process_api(start))
    result = control.launch(tmp_path / "record", "a" * 64, tmp_path / "output")
    assert len(launches) == 1
    argv, kwargs = launches[0]
    assert argv[:4] == ["/fixed/python", "-I", "-B", "-X"]
    assert kwargs["env"] == {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    assert kwargs["stdin"] == subprocess.DEVNULL and kwargs["close_fds"]
    assert result.reaped and result.capture_observed == (outcome == "success")
    assert result.captured is False and result.owned_tree_closed is None
    if outcome == "success":
        assert result.failure == "outer_owned_tree_closure_unproved"
    assert killed == ([True] if outcome == "timeout" else [])
    assert stat.S_IMODE((tmp_path / "output/child.log").stat().st_mode) == 0o600


@pytest.mark.parametrize("case", ["direct", "declared_hop", "unprotected_hop", "cycle"])
def test_literal_interpreter_chain_never_skips_a_hop(case: str) -> None:
    start, alias, binary = (
        Path(value) for value in ("/owned/python", "/owned/python3", "/runtime/python")
    )
    inventory = {start: "link", binary: "file"}
    targets = {start: str(binary)}
    if case == "declared_hop":
        inventory[alias] = "link"
        targets = {start: "python3", alias: str(binary)}
    elif case == "unprotected_hop":
        targets[start] = "/tmp/flip"
    elif case == "cycle":
        inventory[alias] = "link"
        targets = {start: "python3", alias: "python"}
    if case in ("direct", "declared_hop"):
        assert control._interpreter_file(start, inventory, targets) == binary
    else:
        with pytest.raises(control.PreflightError):
            control._interpreter_file(start, inventory, targets)


def test_indirect_uninventoried_interpreter_link_fails_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = synthetic_plan(tmp_path, monkeypatch)
    entry = Path(plan["interpreter"])
    flip = tmp_path / "flip"
    flip.symlink_to(Path(sys.executable).resolve())
    entry.unlink()
    entry.symlink_to(flip)
    plan["links"][0]["target"] = str(flip)
    with pytest.raises(control.PreflightError, match="hop"):
        control.validate_plan(plan)


def test_membership_overflow_stops_after_one_extra_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[int] = []

    class Entries:
        def __enter__(self) -> Entries:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def __iter__(self) -> Any:
            for number in range(100):
                seen.append(number)
                yield SimpleNamespace(name=str(number))

    monkeypatch.setattr(control, "os", SimpleNamespace(scandir=lambda path: Entries()))
    with pytest.raises(control.PreflightError, match="bound"):
        control._names(Path("/synthetic"), 2)
    assert seen == [0, 1, 2]


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "reviewed",
        "omitted",
        "unknown_pth",
        "customize",
        "archive",
        "changed_source",
        "changed_import_line",
    ],
)
def test_startup_hook_membership_is_derived_not_asserted(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    site = Path("/protected/site")
    hook, source = site / "_virtualenv.pth", site / "_virtualenv.py"
    entries = [] if case == "empty" else [hook.name, source.name]
    expected = [] if case in ("empty", "omitted") else [str(hook), str(source)]
    plan: dict[str, Any] = {
        "startup_sys_path": [str(site)],
        "startup_hook_files": expected,
        "directories": [{"path": str(site), "entries": entries}],
        "files": [{"path": str(hook), "uid": os.getuid()}],
    }
    inventory = {site: "directory", hook: "file", source: "file"}
    hashes = {str(source): control.VIRTUALENV_HOOK_SHA256}
    raw = b"import _virtualenv"
    if case == "unknown_pth":
        entries.append("unknown.pth")
    elif case == "customize":
        entries.append("sitecustomize.py")
    elif case == "archive":
        plan["startup_sys_path"].append("/protected/runtime.zip")
        inventory[Path("/protected/runtime.zip")] = "file"
    elif case == "changed_source":
        hashes[str(source)] = "0" * 64
    elif case == "changed_import_line":
        raw = b"import arbitrary_startup\n"
    monkeypatch.setattr(control, "_read", lambda *args: raw)
    if case in ("empty", "reviewed"):
        control._startup_hooks(plan, {"site_packages": site}, inventory, hashes)
    else:
        with pytest.raises(control.PreflightError):
            control._startup_hooks(plan, {"site_packages": site}, inventory, hashes)


def test_absence_does_not_inventory_unrelated_siblings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(control, "_ancestors", lambda path: None)
    (tmp_path / "unrelated").symlink_to("/not-followed")
    control._absent(tmp_path / "python312.zip")


@pytest.mark.parametrize("kind", ["regular", "directory", "dangling"])
def test_absence_rejects_every_existing_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    monkeypatch.setattr(control, "_ancestors", lambda path: None)
    path = tmp_path / "python312.zip"
    if kind == "regular":
        path.write_bytes(b"archive")
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(tmp_path / "missing")
    with pytest.raises(control.PreflightError, match="present"):
        control._absent(path)


def test_absence_does_not_hide_permission_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(control, "_ancestors", lambda path: None)
    class DeniedPath(Path):
        def lstat(self) -> os.stat_result:
            if self.name == "python312.zip":
                raise PermissionError("synthetic")
            return super().lstat()

    with pytest.raises(PermissionError):
        control._absent(DeniedPath("/python312.zip"))


@pytest.mark.parametrize("literal", ["lib", "other"])
def test_closed_venv_lib64_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, literal: str
) -> None:
    plan = synthetic_plan(tmp_path, monkeypatch)
    alias = Path(plan["venv_root"]) / "lib64"
    alias.symlink_to(literal)
    plan["links"].append({"path": str(alias), "uid": os.getuid(), "target": literal})
    next(d for d in plan["directories"] if d["path"] == plan["venv_root"])["entries"].append("lib64")
    if literal == "lib":
        control.validate_plan(plan)
    else:
        with pytest.raises(control.PreflightError, match="runtime alias"):
            control.validate_plan(plan)


@pytest.mark.parametrize("case", ["reviewed", "changed_hash", "omitted", "apport_py", "apport_dir", "apport_so", "apport_pyc", "apport_frozen", "apport_builtin"])
def test_reviewed_ubuntu_hook_requires_absent_optional_dependency(case: str) -> None:
    stdlib = Path("/protected/stdlib")
    site = Path("/protected/site")
    dynamic = stdlib / "lib-dynload"
    hook = stdlib / "sitecustomize.py"
    target = Path("/etc/python3.12/sitecustomize.py")
    plan: dict[str, Any] = {
        "startup_sys_path": [str(stdlib), str(dynamic), str(site)],
        "startup_hook_files": [] if case == "omitted" else [str(hook), str(target)],
        "directories": [
            {"path": str(stdlib), "entries": ["sitecustomize.py", "lib-dynload"]},
            {"path": str(site), "entries": []},
            {"path": str(dynamic), "entries": []},
        ],
        "links": [{"path": str(hook), "uid": 0, "target": str(target)}],
        "builtin_modules": [], "frozen_modules": [],
    }
    if case in ("apport_py", "apport_dir", "apport_so", "apport_pyc"):
        suffix = {"apport_py": ".py", "apport_dir": "", "apport_so": ".cpython-312-x86_64-linux-gnu.so", "apport_pyc": ".pyc"}[case]
        plan["directories"][2]["entries"].append("apport_python_hook" + suffix)
    if case == "apport_frozen":
        plan["frozen_modules"] = ["apport_python_hook"]
    if case == "apport_builtin":
        plan["builtin_modules"] = ["apport_python_hook"]
    inventory = {stdlib: "directory", site: "directory", dynamic: "directory", hook: "link", target: "file"}
    hashes = {str(target): "0" * 64 if case == "changed_hash" else control.SITE_CUSTOMIZE_SHA256}
    if case == "reviewed":
        control._startup_hooks(plan, {"stdlib": stdlib, "site_packages": site}, inventory, hashes)
    else:
        with pytest.raises(control.PreflightError):
            control._startup_hooks(plan, {"stdlib": stdlib, "site_packages": site}, inventory, hashes)
