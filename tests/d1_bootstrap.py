"""Fresh-child, installed-origin capture of the original D1 objects.

The protected parent validates startup, custody and the complete byte inventory
before this module can run. This module cannot establish that external authority.
No primitive, density emitter, recorder, bridge or retention operation is called.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.machinery
import json
import math
import os
import sys
from pathlib import Path
from types import BuiltinFunctionType, CodeType, FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from d1_originals import PreparedOriginals
    from endpoint_belief_reference import EndpointOracle

METHOD_NAMES = ("position", "exp", "log", "circle_constant")
CONSUMERS = ("d1_fixture_reference", "d1_prefix_evidence", "d1_originals")
FORBIDDEN_HELPERS = (
    "d1_primitive_recording", "d1_primitive_sink", "d1_primitive_bridge",
    "d1_primitive_codec", "d1_codec_append", "d1_table_retention", "d1_source_files",
)
SOURCE_PIN_PATHS = (
    "docs/research/RA_N03_CALIBRATION_SLICE.md", "tests/endpoint_belief_reference.py",
    "tests/d1_fixture_reference.py", "src/strange_physics/calibration_fixture_contracts.py",
    "src/strange_physics/contracts.py", "src/strange_physics/bounded_json.py",
    "src/strange_physics/research_contracts.py",
)
PLAN_LIMIT = 4 * 1024**2
REPORT_LIMIT = 4096
_DENIED_WORK: str | None = None


class BootstrapError(ValueError):
    """The actual fresh-child import or retained-object boundary differs."""


def read_launch_record(path: Path, expected_sha256: str) -> dict[str, Any]:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if before.st_size > PLAN_LIMIT:
            raise BootstrapError("Launch record exceeds its bound")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(PLAN_LIMIT + 1)
        after = os.fstat(descriptor)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, key) != getattr(after, key) for key in fields) or len(raw) != before.st_size:
            raise BootstrapError("Launch record changed")
    finally:
        os.close(descriptor)
    if len(raw) > PLAN_LIMIT or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise BootstrapError("Launch record bytes differ")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise BootstrapError("Launch record must be an object")
    return value


def _source_module(name: str, plan: dict[str, Any]) -> ModuleType:
    module = importlib.import_module(name)
    origin = plan["import_map"].get(name)
    spec = module.__spec__
    if (
        not isinstance(origin, str) or spec is None
        or type(spec.loader) is not importlib.machinery.SourceFileLoader
        or spec.origin != origin or module.__file__ != origin
    ):
        raise BootstrapError("Canonical source module origin or ordinary loader differs")
    return module


def _check_loaded(plan: dict[str, Any]) -> None:
    files = {item["path"]: item for item in plan["files"]}
    routes = plan["import_map"]
    frozen = set(plan["frozen_modules"])
    builtin = set(plan["builtin_modules"])
    for name, module in tuple(sys.modules.items()):
        if module is None:
            continue
        if name.startswith("tests.") or name in FORBIDDEN_HELPERS:
            raise BootstrapError("Alternate helper alias or inactive component was loaded")
        if name in ("typing.io", "typing.re"):
            # Python 3.12 registers these two namespace classes as module aliases.
            # Inspect the protected parent directly, without alias attribute hooks.
            parent = sys.modules.get("typing")
            if type(parent) is not ModuleType:
                raise BootstrapError("Typing alias lacks its canonical module")
            parent_spec = parent.__dict__.get("__spec__")
            expected = str(Path(plan["stdlib"]) / "typing.py")
            if (
                parent_spec is None or parent_spec.name != "typing"
                or type(parent_spec.loader) is not importlib.machinery.SourceFileLoader
                or parent_spec.origin != expected or parent.__dict__.get("__file__") != expected
                or expected not in files
                or not isinstance(module, type)
                or module is not parent.__dict__.get(name.partition(".")[2])
            ):
                raise BootstrapError("Typing namespace alias or protected parent origin differs")
            continue
        spec = getattr(module, "__spec__", None)
        if name == "__main__":
            continue
        if spec is None:
            raise BootstrapError("Unmapped module has no import specification")
        origin = spec.origin
        if origin == "built-in":
            if name not in builtin:
                raise BootstrapError("Unlisted builtin module")
        elif origin == "frozen":
            if name not in frozen:
                raise BootstrapError("Unlisted frozen module")
        elif origin not in files:
            raise BootstrapError("Loaded module origin is outside the protected runtime inventory")
        if isinstance(origin, str):
            source_roots = (
                Path(plan["checkout"]) / "tests", Path(plan["checkout"]) / "src",
                Path(plan["site_packages"]) / "strange_physics",
            )
            if any(Path(origin).is_relative_to(root) for root in source_roots):
                if routes.get(name) != origin:
                    raise BootstrapError("Unmapped helper or installed project source was loaded")
        if origin in routes.values() and name not in routes:
            raise BootstrapError("Protected helper or native source was loaded under an alias")
        if name.startswith("strange_physics") and name not in routes:
            raise BootstrapError("Unmapped installed project import")
        if name in routes and (origin != routes[name] or type(spec.loader) is not
                               importlib.machinery.SourceFileLoader):
            raise BootstrapError("Mapped module escaped its source loader")


def _raw_anchors(plan: dict[str, Any]) -> tuple[
    ModuleType, type[EndpointOracle],
    tuple[FunctionType, FunctionType, FunctionType, FunctionType],
    tuple[CodeType, CodeType, CodeType, CodeType], ModuleType, BuiltinFunctionType,
]:
    oracle = _source_module("endpoint_belief_reference", plan)
    owner = oracle.__dict__.get("EndpointOracle")
    if not isinstance(owner, type) or owner.__module__ != "endpoint_belief_reference":
        raise BootstrapError("Original oracle class is missing")
    values = tuple(owner.__dict__.get(name) for name in METHOD_NAMES)
    if any(type(value) is not FunctionType for value in values):
        raise BootstrapError("Original oracle methods are not intact Python functions")
    functions = cast(tuple[FunctionType, FunctionType, FunctionType, FunctionType], values)
    codes = tuple(function.__code__ for function in functions)
    origin = plan["import_map"]["endpoint_belief_reference"]
    if any(code.co_filename != origin for code in codes):
        raise BootstrapError("Original code does not belong to the pinned oracle source")
    actual_math = importlib.import_module("math")
    emitter = actual_math.__dict__.get("exp")
    if actual_math is not math or type(emitter) is not BuiltinFunctionType:
        raise BootstrapError("Original runtime math.exp is missing")
    if emitter.__module__ != "math" or emitter.__name__ != "exp":
        raise BootstrapError("Density emitter differs from the fixed runtime builtin")
    return (
        oracle, cast("type[EndpointOracle]", owner), functions,
        cast(tuple[CodeType, CodeType, CodeType, CodeType], codes),
        actual_math, emitter,
    )


def _unchanged(
    raw: tuple[
        ModuleType, type[EndpointOracle],
        tuple[FunctionType, FunctionType, FunctionType, FunctionType],
        tuple[CodeType, CodeType, CodeType, CodeType], ModuleType, BuiltinFunctionType,
    ],
) -> None:
    oracle, owner, functions, codes, actual_math, emitter = raw
    if sys.modules.get("endpoint_belief_reference") is not oracle:
        raise BootstrapError("Canonical oracle module was replaced")
    if oracle.__dict__.get("EndpointOracle") is not owner:
        raise BootstrapError("Canonical oracle class was replaced")
    for name, function, code in zip(METHOD_NAMES, functions, codes, strict=True):
        if owner.__dict__.get(name) is not function or function.__code__ is not code:
            raise BootstrapError("Original function or separate code reference changed")
    if sys.modules.get("math") is not actual_math or actual_math.__dict__.get("exp") is not emitter:
        raise BootstrapError("Original math module or emitter changed")


def _require_no_denied_work() -> None:
    if _DENIED_WORK is not None:
        raise BootstrapError("Capture observed denied work: " + _DENIED_WORK)


def capture(plan: dict[str, Any]) -> PreparedOriginals:
    """Retain real objects in this child; the returned references are not serializable authority."""
    _require_no_denied_work()
    if any(name in sys.modules for name in ("endpoint_belief_reference", *CONSUMERS)):
        raise BootstrapError("Capture requires a fresh helper namespace")
    raw = _raw_anchors(plan)
    # Save raw references before any consumer or record-construction helper import.
    fixture = _source_module("d1_fixture_reference", plan)
    _source_module("d1_prefix_evidence", plan)
    _source_module("d1_originals", plan)
    _require_no_denied_work()
    _unchanged(raw)
    _check_loaded(plan)
    from d1_originals import OriginalAnchors, prepare_originals

    anchors = OriginalAnchors(*raw)
    _require_no_denied_work()
    _unchanged(raw)
    root = Path(plan["checkout"])
    file_pins = {item["path"]: item["sha256"] for item in plan["files"]}
    if fixture.SOURCE_PATHS != SOURCE_PIN_PATHS:
        raise BootstrapError("Fixture source-pin contract differs")
    pins = tuple(
        fixture.SourcePin(path=relative, sha256=file_pins[str(root / relative)])
        for relative in fixture.SOURCE_PATHS
    )
    _require_no_denied_work()
    prepared = prepare_originals(
        anchors, root=root, commit=plan["source_commit"], pins=pins,
    )
    _require_no_denied_work()
    _unchanged(raw)
    _check_loaded(plan)
    if len(prepared.owners) != 13 or len(prepared.original_methods) != 22:
        raise BootstrapError("Prepared owner or bound-method census differs")
    if prepared.emitter is not raw[-1]:
        raise BootstrapError("Prepared emitter lost the retained runtime identity")
    return prepared


def _deny_external_work(event: str, args: tuple[object, ...]) -> None:
    global _DENIED_WORK
    del args
    if event in (
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.fork",
        "os.forkpty", "pty.spawn",
    ) or event.startswith("socket."):
        if _DENIED_WORK is None:
            _DENIED_WORK = event[:128]
        raise BootstrapError("Capture child cannot spawn processes or use the network")


def _empty_cache(cache: Path) -> bool:
    with os.scandir(cache) as entries:
        return next(entries, None) is None


def child(plan_path: Path, plan_digest: str, cache: Path) -> dict[str, object]:
    if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
        raise BootstrapError("Expected isolated interpreter and disabled bytecode writes")
    if sys._xoptions.get("pycache_prefix") != str(cache) or not cache.is_dir() or not _empty_cache(cache):
        raise BootstrapError("Expected the fresh owned empty bytecode prefix")
    plan = read_launch_record(plan_path, plan_digest)
    if ".".join(str(part) for part in sys.version_info[:3]) != plan["python_version"]:
        raise BootstrapError("Interpreter version differs")
    if Path(sys.prefix) != Path(plan["venv_root"]):
        raise BootstrapError("Interpreter virtual environment prefix differs")
    if sys.path != plan["startup_sys_path"]:
        raise BootstrapError("Interpreter startup path differs")
    if sorted(sys.builtin_module_names) != sorted(plan["builtin_modules"]):
        raise BootstrapError("Interpreter builtin inventory differs")
    if Path(__file__).absolute() != Path(plan["bootstrap"]):
        raise BootstrapError("Unexpected bootstrap path")
    _check_loaded(plan)
    root = Path(plan["checkout"])
    helper_root = str(root / "tests")
    if helper_root in sys.path or str(root / "src") in sys.path or str(root) in sys.path:
        raise BootstrapError("Checkout was already present in startup search paths")
    sys.addaudithook(_deny_external_work)
    sys.path.insert(0, helper_root)
    prepared = capture(plan)
    _require_no_denied_work()
    # Strong references stay alive through the final checks. No future child can
    # reconstruct these anchors from this bounded capture-only completion report.
    return {
        "kind": "d1-capture-only", "source_commit": plan["source_commit"],
        "owners": len(prepared.owners), "original_methods": len(prepared.original_methods),
        "emitter": "math.exp", "primitive_calls_permitted": False, "retention_activated": False,
    }


def main() -> int:
    if len(sys.argv) != 4:
        raise BootstrapError("Expected only the protected record, digest and owned cache path")
    result = child(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
    raw = json.dumps(result, sort_keys=True)
    if len(raw.encode("utf-8")) + 1 > REPORT_LIMIT:
        raise BootstrapError("Capture report exceeds its bound")
    print(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
