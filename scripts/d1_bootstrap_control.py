"""Preflight and retain one D1 capture-only child; standalone launch stays disabled.

This module must run in an independently accepted controller interpreter. A plan
digest authenticates bytes relative to that outer invocation, not their author.
It neither repairs custody nor grants scientific execution authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import stat
import threading
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLAN_LIMIT = 4 * 1024**2
FILE_LIMIT = 64 * 1024**2
TOTAL_INPUT_LIMIT = 512 * 1024**2
ENTRY_LIMIT = 32768
LOG_LIMIT = 64 * 1024
CHILD_CPU_LIMIT = 30
CHILD_WALL_LIMIT = 60
CLEANUP_LIMIT = 5
HELPERS = (
    "d1_bootstrap", "d1_bounds", "d1_fixture_reference", "d1_originals",
    "d1_prefix_evidence", "endpoint_belief_reference", "grid_q1_bounds",
    "grid_q1_evidence", "grid_q1_inputs", "grid_q1_reference",
)
NATIVE_MODULES = (
    "strange_physics", "strange_physics.bounded_json",
    "strange_physics.calibration_fixture_contracts", "strange_physics.contracts",
    "strange_physics.control_contracts", "strange_physics.finite_log_weight_contracts",
    "strange_physics.fitting_contracts", "strange_physics.laws",
    "strange_physics.native_endpoint_belief_contracts",
    "strange_physics.native_prediction_contracts", "strange_physics.native_spring_contracts",
    "strange_physics.prediction_contracts", "strange_physics.research_contracts",
    "strange_physics.serialization",
)
SOURCE_PIN_PATHS = (
    "docs/research/RA_N03_CALIBRATION_SLICE.md", "tests/endpoint_belief_reference.py",
    "tests/d1_fixture_reference.py", "src/strange_physics/calibration_fixture_contracts.py",
    "src/strange_physics/contracts.py", "src/strange_physics/bounded_json.py",
    "src/strange_physics/research_contracts.py",
)


class PreflightError(ValueError):
    """Missing, changed, incomplete, or insufficiently protected launch evidence."""


@dataclass(frozen=True, slots=True)
class LaunchResult:
    exit_code: int | None
    reaped: bool
    timed_out: bool
    custody_rechecked: bool
    stdout_bytes: int
    wall_seconds: float
    child_cpu_seconds: float | None
    captured: bool
    failure: str | None


def _path(value: object) -> Path:
    if not isinstance(value, str) or len(value) > 4096:
        raise PreflightError("Invalid absolute inventory path")
    path = Path(value)
    if not path.is_absolute() or str(path) != value or ".." in path.parts:
        raise PreflightError("Inventory paths must be canonical and absolute")
    return path


def _digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise PreflightError("Invalid SHA256")
    return value


def _safe_mode(info: os.stat_result, uid: int, *, directory: bool = False) -> None:
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != uid or info.st_mode & 0o022:
        raise PreflightError("Custody requires the exact owner, type and non-writable permissions")
    if not directory and info.st_nlink != 1:
        raise PreflightError("Protected regular files must have one link")


def _ancestors(path: Path) -> None:
    for parent in path.parents:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0, os.getuid()):
            raise PreflightError("Unapproved ancestor type or owner")
        if info.st_mode & 0o022:
            raise PreflightError("Writable ancestor prevents protected custody")


def _read(path: Path, limit: int, uid: int) -> bytes:
    _ancestors(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        _safe_mode(before, uid)
        if before.st_size > limit:
            raise PreflightError("Protected file exceeds its bound")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            block = os.read(descriptor, min(65536, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        after = os.fstat(descriptor)
        raw = b"".join(chunks)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if len(raw) > limit or any(getattr(before, key) != getattr(after, key) for key in fields) or len(raw) != before.st_size:
            raise PreflightError("Protected file changed during bounded read")
        return raw
    finally:
        os.close(descriptor)


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError("Duplicate plan key")
        result[key] = value
    return result


def read_plan(path: Path, digest: str) -> dict[str, Any]:
    """Read the externally pinned plan without starting the target interpreter."""
    raw = _read(path, PLAN_LIMIT, os.getuid())
    if hashlib.sha256(raw).hexdigest() != _digest(digest):
        raise PreflightError("Protected launch record digest differs")
    value = json.loads(raw, object_pairs_hook=_object_pairs)
    if not isinstance(value, dict):
        raise PreflightError("Launch record must be an object")
    return value


def validate_plan(plan: dict[str, Any]) -> dict[str, str]:
    """Check a closed inventory, actual source routes and controller before launch."""
    required = {
        "version", "source_commit", "checkout", "interpreter", "bootstrap",
        "controller", "controller_interpreter", "site_packages", "stdlib", "venv_root",
        "python_version", "startup_hook_files", "absent_startup_paths", "installation_record", "files", "directories", "links", "import_map",
        "startup_sys_path", "frozen_modules", "builtin_modules",
    }
    if set(plan) != required or plan["version"] != "d1-protected-capture-v1":
        raise PreflightError("Launch record is incomplete or has unknown fields")
    if re.fullmatch("[0-9a-f]{40}", str(plan["source_commit"])) is None:
        raise PreflightError("Invalid source commit")
    paths = {key: _path(plan[key]) for key in (
        "checkout", "interpreter", "bootstrap", "controller", "controller_interpreter",
        "site_packages", "stdlib", "venv_root", "installation_record",
    )}
    for field in ("startup_sys_path", "frozen_modules", "builtin_modules",
                  "startup_hook_files", "absent_startup_paths"):
        if not isinstance(plan[field], list) or len(plan[field]) > 1024:
            raise PreflightError("Missing bounded startup inventory")
        if len(plan[field]) != len(set(plan[field])) or not all(
            isinstance(item, str) and len(item) <= 4096 for item in plan[field]
        ):
            raise PreflightError("Invalid startup inventory")
    if not plan["startup_sys_path"] or not plan["frozen_modules"] or not plan["builtin_modules"]:
        raise PreflightError("Runtime startup inventory cannot be empty")
    if re.fullmatch(r"3\.[0-9]+\.[0-9]+", str(plan["python_version"])) is None:
        raise PreflightError("Exact reviewed Python version is required")
    if paths["interpreter"] != paths["venv_root"] / "bin/python":
        raise PreflightError("Target must use the pinned virtual environment entry point")
    minor = ".".join(plan["python_version"].split(".")[:2])
    if paths["site_packages"] != paths["venv_root"] / "lib" / ("python" + minor) / "site-packages":
        raise PreflightError("Installation path differs from the fixed Linux virtual environment layout")
    files, directories, links = plan["files"], plan["directories"], plan["links"]
    if not all(isinstance(items, list) for items in (files, directories, links)):
        raise PreflightError("Inventory collections must be lists")
    if not 1 <= len(files) + len(directories) + len(links) <= ENTRY_LIMIT:
        raise PreflightError("Protected inventory count exceeds its bound")
    inventory: dict[Path, str] = {}
    hashes: dict[str, str] = {}
    total = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes", "uid"}:
            raise PreflightError("Invalid file entry")
        path = _path(item["path"])
        size, uid = item["bytes"], item["uid"]
        if type(size) is not int or not 0 <= size <= FILE_LIMIT or type(uid) is not int:
            raise PreflightError("Invalid protected file size or owner")
        if uid not in (0, os.getuid()) or path in inventory:
            raise PreflightError("Duplicate file or unapproved owner")
        total += size
        if total > TOTAL_INPUT_LIMIT:
            raise PreflightError("Combined protected input exceeds its bound")
        raw = _read(path, size, uid)
        digest = _digest(item["sha256"])
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise PreflightError("Protected file bytes differ")
        inventory[path], hashes[str(path)] = "file", digest
    for item in directories:
        if not isinstance(item, dict) or set(item) != {"path", "uid", "entries"}:
            raise PreflightError("Invalid directory entry")
        path = _path(item["path"])
        if path in inventory or type(item["uid"]) is not int or item["uid"] not in (0, os.getuid()):
            raise PreflightError("Duplicate directory or unapproved owner")
        _ancestors(path)
        _safe_mode(path.lstat(), item["uid"], directory=True)
        entries = item["entries"]
        if not isinstance(entries, list) or len(entries) > ENTRY_LIMIT or any(
            not isinstance(name, str) or name in ("", ".", "..") or "/" in name for name in entries
        ) or len(entries) != len(set(entries)):
            raise PreflightError("Invalid closed directory membership")
        if sorted(os.listdir(path)) != sorted(entries):
            raise PreflightError("Directory membership differs")
        inventory[path] = "directory"
    allowed_links = {
        paths["interpreter"].parent / "python", paths["interpreter"].parent / "python3",
        paths["interpreter"].parent / "python3.12",
    }
    for item in links:
        if not isinstance(item, dict) or set(item) != {"path", "uid", "target"}:
            raise PreflightError("Invalid interpreter link")
        path = _path(item["path"])
        if path not in allowed_links or path in inventory:
            raise PreflightError("Only the explicit interpreter links are permitted")
        _ancestors(path)
        info = path.lstat()
        if not stat.S_ISLNK(info.st_mode) or info.st_uid != item["uid"]:
            raise PreflightError("Interpreter link owner or type differs")
        if os.readlink(path) != item["target"] or path.resolve() not in inventory:
            raise PreflightError("Interpreter link target is not a pinned regular file")
        inventory[path] = "link"
    for item in directories:
        if any(_path(item["path"]) / name not in inventory for name in item["entries"]):
            raise PreflightError("Closed directory contains an unpinned entry")
    if any(inventory.get(paths[key]) != "directory" for key in ("stdlib", "site_packages", "venv_root")):
        raise PreflightError("Complete stdlib and installation roots are required")
    venv_config = paths["venv_root"] / "pyvenv.cfg"
    if inventory.get(venv_config) != "file":
        raise PreflightError("Virtual environment configuration is not pinned")
    config = _read(venv_config, 65536, os.getuid()).decode("utf-8")
    settings = {
        line.split("=", 1)[0].strip().lower(): line.split("=", 1)[1].strip()
        for line in config.splitlines() if "=" in line
    }
    if settings.get("include-system-site-packages") != "false":
        raise PreflightError("Global site packages must be disabled")
    if settings.get("version_info") != plan["python_version"]:
        raise PreflightError("Virtual environment version differs")
    for name in plan["startup_hook_files"]:
        if inventory.get(_path(name)) != "file":
            raise PreflightError("Reviewed startup hook source is missing")
    for name in plan["absent_startup_paths"]:
        path = _path(name)
        _ancestors(path)
        if path.exists() or path.is_symlink() or inventory.get(path.parent) != "directory":
            raise PreflightError("Startup absence requires closed parent membership")
    for name in plan["startup_sys_path"]:
        path = _path(name)
        if path not in inventory and name not in plan["absent_startup_paths"]:
            raise PreflightError("Startup search path is neither pinned nor observed absent")
    if paths["controller"] != Path(__file__).absolute() or paths["controller_interpreter"] != Path(
        sys.executable
    ).resolve():
        raise PreflightError("Controller context differs from the independently accepted invocation")
    for key in ("controller", "controller_interpreter", "bootstrap", "installation_record"):
        if inventory.get(paths[key]) != "file":
            raise PreflightError("Launch/control/installation evidence is not pinned")
    if inventory.get(paths["interpreter"]) not in ("file", "link"):
        raise PreflightError("Target interpreter is not pinned")
    if paths["bootstrap"] != paths["checkout"] / "tests/d1_bootstrap.py":
        raise PreflightError("Only the source-owned bootstrap may run")
    routes = plan["import_map"]
    if not isinstance(routes, dict) or set(routes) != set(HELPERS + NATIVE_MODULES):
        raise PreflightError("Fixed helper/native import map is incomplete")
    for name in HELPERS + NATIVE_MODULES:
        relative = name.replace(".", "/")
        expected = (
            paths["checkout"] / "tests" / (name + ".py") if name in HELPERS else
            paths["site_packages"] / (relative + ("/__init__.py" if name == "strange_physics" else ".py"))
        )
        if _path(routes[name]) != expected or inventory.get(expected) != "file":
            raise PreflightError("Module route differs from the fixed normal-import layout")
        if name in NATIVE_MODULES:
            checkout_copy = paths["checkout"] / "src" / (
                relative + ("/__init__.py" if name == "strange_physics" else ".py")
            )
            if hashes.get(str(checkout_copy)) != hashes[str(expected)]:
                raise PreflightError("Installed project bytes differ from reviewed source")
    if any(str(paths["checkout"] / rel) not in hashes for rel in SOURCE_PIN_PATHS):
        raise PreflightError("Fixture source pins are incomplete")
    # The record is the existing accepted installation evidence, not a new trust flag.
    accepted = json.loads(_read(paths["installation_record"], PLAN_LIMIT, os.getuid()))
    if not isinstance(accepted, dict) or accepted.get("evidence_kind") != "accepted_release_candidate":
        raise PreflightError("Missing independently accepted installed build")
    if accepted.get("source_commit") != plan["source_commit"]:
        raise PreflightError("Accepted installation source differs")
    if accepted.get("python_version") != plan["python_version"] or accepted.get(
        "python_executable_sha256"
    ) != hashes.get(str(paths["interpreter"].resolve())):
        raise PreflightError("Accepted interpreter identity differs")
    for key, hash_key in (
        ("lock_path", "uv_lock_sha256"), ("archive_path", "archive_sha256"),
        ("provenance_path", "provenance_sha256"),
    ):
        if hashes.get(str(_path(accepted.get(key)))) != _digest(accepted.get(hash_key)):
            raise PreflightError("Accepted build provenance is absent from protected inventory")
    for field, base in (("package_files", paths["site_packages"] / "strange_physics"),
                        ("dependency_files", paths["site_packages"])):
        entries = accepted.get(field)
        limit = 128 if field == "package_files" else 10000
        if not isinstance(entries, list) or not 1 <= len(entries) <= limit:
            raise PreflightError("Accepted package/dependency membership is missing")
        named: set[str] = set()
        sizes = {item["path"]: item["bytes"] for item in files}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise PreflightError("Invalid accepted installation member")
            rel = Path(entry["path"])
            if rel.is_absolute() or ".." in rel.parts or str(rel) != entry["path"]:
                raise PreflightError("Accepted installation member escapes its root")
            if entry["path"] in named:
                raise PreflightError("Duplicate accepted installation member")
            named.add(entry["path"])
            if sizes.get(str(base / rel)) != entry.get("bytes"):
                raise PreflightError("Accepted installation member size differs")
            if hashes.get(str(base / rel)) != _digest(entry.get("sha256")):
                raise PreflightError("Accepted installation bytes are not protected")
        observed = {
            str(path.relative_to(base)) for path, kind in inventory.items()
            if kind == "file" and path.is_relative_to(base)
            and "__pycache__" not in path.relative_to(base).parts
            and (field == "package_files" or not path.is_relative_to(base / "strange_physics"))
        }
        if observed != named:
            raise PreflightError("Accepted installation membership is not complete")
    return hashes


def _child_limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (CHILD_CPU_LIMIT, CHILD_CPU_LIMIT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LOG_LIMIT, LOG_LIMIT))
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def launch(plan_path: Path, plan_sha256: str, output: Path) -> LaunchResult:
    """Called only by an independently accepted, single-threaded outer controller.

    No standalone CLI accepts an authority record. This source slice supplies the
    concrete capture path; its actual protected environment and invocation remain
    to be qualified. A caller-held digest does not establish historical acceptance.
    """
    if sys.platform != "linux" or threading.active_count() != 1:
        raise PreflightError("Capture requires the reviewed single-threaded Linux controller")
    plan = read_plan(plan_path, plan_sha256)
    validate_plan(plan)
    _ancestors(output)
    if any(output.is_relative_to(Path(plan[key])) for key in ("checkout", "venv_root", "stdlib")):
        raise PreflightError("Capture output must be outside protected source and runtime roots")
    if output.exists() or output.is_symlink():
        raise PreflightError("Capture output must be fresh")
    output.mkdir(mode=0o700)
    cache = output / "pycache"
    cache.mkdir(mode=0o700)
    start = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    process: subprocess.Popen[bytes] | None = None
    code: int | None = None
    reaped = timed_out = custody = False
    failure: str | None = None
    try:
        with (output / "child.log").open("xb") as log:
            os.chmod(output / "child.log", 0o600)
            process = subprocess.Popen(
                [
                    plan["interpreter"], "-I", "-B", "-X", f"pycache_prefix={cache}",
                    plan["bootstrap"], str(plan_path), plan_sha256, str(cache),
                ],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
                cwd=output, close_fds=True, preexec_fn=_child_limits,
            )
            try:
                code = process.wait(timeout=CHILD_WALL_LIMIT)
                reaped = True
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                if not reaped:
                    try:
                        process.kill()
                    except OSError:
                        failure = "child_signal_failed"
                    finally:
                        try:
                            code = process.wait(timeout=CLEANUP_LIMIT)
                            reaped = True
                        except (OSError, subprocess.TimeoutExpired):
                            failure = "child_closure_unproved"
        validate_plan(read_plan(plan_path, plan_sha256))
        custody = True
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        failure = type(exc).__name__
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    elapsed = time.monotonic() - start
    log_path = output / "child.log"
    size = log_path.stat().st_size if log_path.exists() else 0
    report_ok = False
    if reaped and code == 0 and size <= LOG_LIMIT:
        try:
            report = json.loads(_read(log_path, LOG_LIMIT, os.getuid()))
            report_ok = report == {
                "kind": "d1-capture-only", "source_commit": plan["source_commit"],
                "owners": 13, "original_methods": 22, "emitter": "math.exp",
                "primitive_calls_permitted": False, "retention_activated": False,
            }
        except (OSError, ValueError):
            failure = "invalid_capture_report"
    try:
        if any(cache.iterdir()) or set(os.listdir(output)) != {"pycache", "child.log"}:
            failure = "unexpected_capture_output"
    except OSError:
        failure = "output_census_unavailable"
    captured = (
        reaped and code == 0 and custody and not timed_out and size <= LOG_LIMIT
        and report_ok and failure is None and elapsed <= CHILD_WALL_LIMIT + CLEANUP_LIMIT
    )
    # No concurrent child work is permitted in the accepted controller context.
    cpu = (after.ru_utime + after.ru_stime) - (before.ru_utime + before.ru_stime) if reaped else None
    return LaunchResult(code, reaped, timed_out, custody, size, elapsed, cpu, captured, failure)


def main() -> int:
    print("D1 protected capture is disabled pending an independently accepted runtime and invocation.")
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
