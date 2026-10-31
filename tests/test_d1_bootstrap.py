"""Retained-reference tests with synthetic owners; no endpoint or exp call."""

from __future__ import annotations

import hashlib
import importlib.machinery
import json
import math
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import d1_bootstrap as bootstrap
import pytest


@pytest.fixture(autouse=True)
def isolated_denied_work_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test isolation only: the production once-per-child latch has no reset API.
    monkeypatch.setattr(bootstrap, "_DENIED_WORK", None)


def fake_boundary(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    calls: list[str] = []
    oracle = ModuleType("endpoint_belief_reference")

    class Owner:
        def position(self) -> None:
            raise AssertionError("primitive body must never run")

        def exp(self) -> None:
            raise AssertionError("primitive body must never run")

        def log(self) -> None:
            raise AssertionError("primitive body must never run")

        def circle_constant(self) -> None:
            raise AssertionError("primitive body must never run")

    Owner.__module__ = "endpoint_belief_reference"
    oracle.__dict__["EndpointOracle"] = Owner
    actual_math = ModuleType("math")
    actual_math.__dict__["exp"] = math.exp
    fixture = ModuleType("d1_fixture_reference")
    fixture.__dict__["SOURCE_PATHS"] = bootstrap.SOURCE_PIN_PATHS
    fixture.__dict__["SourcePin"] = lambda **kw: kw
    originals = ModuleType("d1_originals")
    prefix = ModuleType("d1_prefix_evidence")
    objects = {"endpoint_belief_reference": oracle, "math": actual_math,
               "d1_fixture_reference": fixture, "d1_prefix_evidence": prefix,
               "d1_originals": originals}
    captured: list[tuple[Any, ...]] = []

    def anchors(*values: Any) -> tuple[Any, ...]:
        calls.append("anchors")
        captured.append(values)
        return values

    def prepare(held: tuple[Any, ...], **kwargs: Any) -> SimpleNamespace:
        calls.append("prepare")
        assert kwargs["commit"] == "a" * 40
        assert kwargs["pins"] == tuple({"path": rel, "sha256": "b" * 64}
                                       for rel in bootstrap.SOURCE_PIN_PATHS)
        assert held[0] is oracle and held[1] is Owner and held[-1] is math.exp
        return SimpleNamespace(reference=object(), producer=object(), owners=(Owner(),) * 13,
                               original_methods=(Owner().position,) * 22, emitter=math.exp)

    originals.__dict__["OriginalAnchors"] = anchors
    originals.__dict__["prepare_originals"] = prepare

    module_table = dict(sys.modules)

    def source(name: str, plan: dict[str, Any]) -> ModuleType:
        calls.append(name)
        module_table[name] = objects[name]
        if name == "d1_originals":
            monkeypatch.setitem(sys.modules, name, objects[name])
        return objects[name]

    monkeypatch.setattr(bootstrap, "_source_module", source)
    monkeypatch.setattr(bootstrap, "sys", SimpleNamespace(modules=module_table))
    monkeypatch.setattr(bootstrap, "math", actual_math)
    monkeypatch.setattr(bootstrap, "importlib", SimpleNamespace(import_module=lambda name: objects[name]))
    monkeypatch.setattr(bootstrap, "_check_loaded", lambda plan: None)
    for name in ("endpoint_belief_reference", *bootstrap.CONSUMERS):
        module_table.pop(name, None)
    module_table["math"] = actual_math
    plan = {
        "checkout": "/synthetic", "source_commit": "a" * 40,
        "import_map": {"endpoint_belief_reference": Owner.position.__code__.co_filename},
        "files": [{"path": "/synthetic/" + rel, "sha256": "b" * 64}
                  for rel in bootstrap.SOURCE_PIN_PATHS],
    }
    return plan, {"calls": calls, "objects": objects, "owner": Owner, "captured": captured, "modules": module_table}


def test_capture_retains_before_consumers_and_constructs_once(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, context = fake_boundary(monkeypatch)
    prepared = bootstrap.capture(plan)
    assert context["calls"] == [
        "endpoint_belief_reference", "d1_fixture_reference", "d1_prefix_evidence",
        "d1_originals", "anchors", "prepare",
    ]
    held = context["captured"][0]
    for name, function, code in zip(bootstrap.METHOD_NAMES, held[2], held[3], strict=True):
        assert context["owner"].__dict__[name] is function
        assert function.__code__ is code
    assert prepared.emitter is held[-1] and len(prepared.owners) == 13


@pytest.mark.parametrize("mutation", ["module", "class", "function", "code", "math_module", "emitter"])
def test_retained_identity_detects_replacement(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    plan, context = fake_boundary(monkeypatch)
    raw = bootstrap._raw_anchors(plan)
    owner = context["owner"]
    if mutation == "module":
        context["modules"]["endpoint_belief_reference"] = ModuleType("replacement")
    elif mutation == "class":
        context["objects"]["endpoint_belief_reference"].EndpointOracle = object
    elif mutation == "function":
        owner.position = lambda self: None
    elif mutation == "code":
        owner.position.__code__ = (lambda self: None).__code__
    elif mutation == "math_module":
        context["modules"]["math"] = ModuleType("replacement")
    else:
        context["objects"]["math"].exp = math.log
    with pytest.raises(bootstrap.BootstrapError):
        bootstrap._unchanged(raw)


def test_preloaded_consumer_is_rejected_before_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, context = fake_boundary(monkeypatch)
    context["modules"]["d1_prefix_evidence"] = ModuleType("d1_prefix_evidence")
    with pytest.raises(bootstrap.BootstrapError, match="fresh"):
        bootstrap.capture(plan)
    assert context["calls"] == []


def test_poisoned_function_is_not_accepted_as_original(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, context = fake_boundary(monkeypatch)
    context["owner"].position = staticmethod(math.log)
    with pytest.raises(bootstrap.BootstrapError, match="intact"):
        bootstrap._raw_anchors(plan)


def test_code_origin_must_match_reviewed_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, context = fake_boundary(monkeypatch)
    plan["import_map"]["endpoint_belief_reference"] = "/wrong/oracle.py"
    with pytest.raises(bootstrap.BootstrapError, match="code"):
        bootstrap._raw_anchors(plan)
    assert context["calls"] == ["endpoint_belief_reference"]


def test_consumer_import_mutation_is_rejected_before_owner_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, context = fake_boundary(monkeypatch)
    original_import = bootstrap._source_module

    def altered_import(name: str, record: dict[str, Any]) -> ModuleType:
        result = original_import(name, record)
        if name == "d1_originals":
            context["owner"].position = lambda self: None
        return result

    monkeypatch.setattr(bootstrap, "_source_module", altered_import)
    with pytest.raises(bootstrap.BootstrapError, match="function"):
        bootstrap.capture(plan)
    assert "anchors" not in context["calls"] and "prepare" not in context["calls"]


def test_normal_source_loader_and_origin_are_required(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("synthetic")
    loader = importlib.machinery.SourceFileLoader("synthetic", "/owned/source.py")
    module.__spec__ = importlib.machinery.ModuleSpec("synthetic", loader, origin="/owned/source.py")
    module.__file__ = "/owned/source.py"
    proxy = SimpleNamespace(import_module=lambda name: module, machinery=importlib.machinery)
    monkeypatch.setattr(bootstrap, "importlib", proxy)
    plan = {"import_map": {"synthetic": "/owned/source.py"}}
    assert bootstrap._source_module("synthetic", plan) is module
    module.__spec__.origin = "/different/source.py"
    with pytest.raises(bootstrap.BootstrapError, match="origin"):
        bootstrap._source_module("synthetic", plan)


@pytest.mark.parametrize("event", ["subprocess.Popen", "os.system", "os.exec", "os.fork",
                                  "os.posix_spawn", "socket.connect", "socket.__new__"])
def test_external_work_events_are_rejected_without_invocation(event: str) -> None:
    with pytest.raises(bootstrap.BootstrapError, match="spawn"):
        bootstrap._deny_external_work(event, ())


def test_benign_audit_event_is_allowed() -> None:
    bootstrap._deny_external_work("open", ("/synthetic", "r", 0))


def test_record_read_uses_expected_digest(tmp_path: Path) -> None:
    path = tmp_path / "record"
    raw = json.dumps({"source_commit": "a" * 40}).encode()
    path.write_bytes(raw)
    assert bootstrap.read_launch_record(path, hashlib.sha256(raw).hexdigest()) == {
        "source_commit": "a" * 40,
    }
    with pytest.raises(bootstrap.BootstrapError, match="bytes"):
        bootstrap.read_launch_record(path, "0" * 64)


@pytest.mark.parametrize("case", ["allowed", "unknown_origin", "alias", "tests_alias", "missing_spec",
                                 "unknown_builtin", "unknown_frozen", "native_outside_map"])
def test_loaded_registry_matches_fixed_origins(
    monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    name = "owned"
    origin = "/owned/source.py"
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "files": [{"path": origin}], "import_map": {name: origin}, "checkout": "/owned",
        "frozen_modules": ["os"], "builtin_modules": ["sys"],
        "site_packages": "/owned/.venv/lib/python3.12/site-packages",
    }
    if case == "unknown_origin":
        module.__spec__.origin = "/unreviewed/source.py"
    elif case == "alias":
        name = "alternative_name"
    elif case == "tests_alias":
        name = "tests.owned"
    elif case == "missing_spec":
        module.__spec__ = None
    elif case == "unknown_builtin":
        module.__spec__.origin = "built-in"
    elif case == "unknown_frozen":
        module.__spec__.origin = "frozen"
    elif case == "native_outside_map":
        name = "strange_physics.unlisted"
    monkeypatch.setattr(bootstrap, "sys", SimpleNamespace(modules={name: module}))
    if case == "allowed":
        bootstrap._check_loaded(plan)
    else:
        with pytest.raises(bootstrap.BootstrapError):
            bootstrap._check_loaded(plan)


@pytest.mark.parametrize("case", ["success", "not_isolated", "bytecode_writes", "used_cache",
                                 "path", "version", "prefix", "checkout_path"])
def test_child_startup_gates_without_importing_consumers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    root = tmp_path / "checkout"
    venv = tmp_path / "venv"
    captured: list[object] = []
    hooks: list[object] = []
    plan = {
        "checkout": str(root), "venv_root": str(venv), "python_version": "3.12.3",
        "startup_sys_path": ["/owned/stdlib"], "builtin_modules": ["sys"],
        "bootstrap": str(Path(bootstrap.__file__).absolute()), "source_commit": "a" * 40,
    }
    state = SimpleNamespace(
        flags=SimpleNamespace(isolated=1, dont_write_bytecode=1),
        _xoptions={"pycache_prefix": str(cache)}, version_info=(3, 12, 3),
        prefix=str(venv), path=["/owned/stdlib"], builtin_module_names=("sys",),
        addaudithook=hooks.append,
    )
    if case == "not_isolated":
        state.flags.isolated = 0
    elif case == "bytecode_writes":
        state.flags.dont_write_bytecode = 0
    elif case == "used_cache":
        (cache / "old.pyc").write_bytes(b"x")
    elif case == "path":
        state.path = ["/unexpected"]
    elif case == "version":
        state.version_info = (3, 12, 4)
    elif case == "prefix":
        state.prefix = "/wrong"
    elif case == "checkout_path":
        state.path = [str(root / "tests")]
        plan["startup_sys_path"] = list(state.path)
    monkeypatch.setattr(bootstrap, "sys", state)
    monkeypatch.setattr(bootstrap, "read_launch_record", lambda *args: plan)
    monkeypatch.setattr(bootstrap, "_check_loaded", lambda record: None)

    def capture(record: dict[str, Any]) -> SimpleNamespace:
        captured.append(record)
        return SimpleNamespace(owners=(object(),) * 13, original_methods=(object(),) * 22)

    monkeypatch.setattr(bootstrap, "capture", capture)
    if case == "success":
        result = bootstrap.child(tmp_path / "record", "b" * 64, cache)
        assert result["owners"] == 13 and result["primitive_calls_permitted"] is False
        assert captured == [plan] and hooks == [bootstrap._deny_external_work]
    else:
        with pytest.raises(bootstrap.BootstrapError):
            bootstrap.child(tmp_path / "record", "b" * 64, cache)
        assert captured == [] and hooks == []


@pytest.mark.parametrize("name", [
    "d1_primitive_recording", "d1_primitive_sink", "d1_codec_append",
    "d1_table_retention", "unmapped_helper", "strange_physics.unmapped",
])
def test_pinned_but_unmapped_checkout_origin_is_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    origin = "/owned/tests/" + name + ".py"
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "checkout": "/owned", "files": [{"path": origin}], "import_map": {},
        "frozen_modules": [], "builtin_modules": [],
        "site_packages": "/owned/.venv/lib/python3.12/site-packages",
    }
    monkeypatch.setattr(bootstrap, "sys", SimpleNamespace(modules={name: module}))
    with pytest.raises(bootstrap.BootstrapError):
        bootstrap._check_loaded(plan)


def test_cache_scan_observes_only_first_unexpected_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[int] = []

    class Entries:
        def __enter__(self) -> Entries:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def __iter__(self) -> Entries:
            return self

        def __next__(self) -> object:
            seen.append(len(seen))
            return object()

    monkeypatch.setattr(bootstrap, "os", SimpleNamespace(scandir=lambda path: Entries()))
    assert not bootstrap._empty_cache(Path("/synthetic"))
    assert seen == [0]


@pytest.mark.parametrize("stage", ["consumer", "anchors", "prepare"])
def test_swallowed_denied_work_still_rejects_capture(
    monkeypatch: pytest.MonkeyPatch, stage: str,
) -> None:
    plan, context = fake_boundary(monkeypatch)

    def swallowed_attempt() -> None:
        try:
            bootstrap._deny_external_work("socket.connect", ())
        except bootstrap.BootstrapError:
            pass

    if stage == "consumer":
        original_import = bootstrap._source_module

        def importer(name: str, record: dict[str, Any]) -> ModuleType:
            result = original_import(name, record)
            if name == "d1_prefix_evidence":
                swallowed_attempt()
            return result

        monkeypatch.setattr(bootstrap, "_source_module", importer)
    else:
        name = "OriginalAnchors" if stage == "anchors" else "prepare_originals"
        module = context["objects"]["d1_originals"]
        original = module.__dict__[name]

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            swallowed_attempt()
            return result

        module.__dict__[name] = wrapped
    with pytest.raises(bootstrap.BootstrapError, match="denied work"):
        bootstrap.capture(plan)
    assert bootstrap._DENIED_WORK == "socket.connect"
    if stage in ("consumer", "anchors"):
        assert "prepare" not in context["calls"]


def test_first_denied_event_remains_sticky() -> None:
    for event in ("socket.connect", "os.fork"):
        with pytest.raises(bootstrap.BootstrapError):
            bootstrap._deny_external_work(event, ())
    assert bootstrap._DENIED_WORK == "socket.connect"
    with pytest.raises(bootstrap.BootstrapError, match="socket.connect"):
        bootstrap._require_no_denied_work()


@pytest.mark.parametrize("case", ["dependency_inside_checkout_venv", "installed_project_alias"])
def test_runtime_inside_checkout_preserves_installed_source_boundary(
    monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    site = "/owned/.venv/lib/python3.12/site-packages"
    name = "dependency.module" if case == "dependency_inside_checkout_venv" else "project_alias"
    suffix = "/dependency/module.py" if case == "dependency_inside_checkout_venv" else (
        "/strange_physics/unlisted.py"
    )
    origin = site + suffix
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "checkout": "/owned", "site_packages": site, "files": [{"path": origin}],
        "import_map": {}, "frozen_modules": [], "builtin_modules": [],
    }
    monkeypatch.setattr(bootstrap, "sys", SimpleNamespace(modules={name: module}))
    if case == "dependency_inside_checkout_venv":
        bootstrap._check_loaded(plan)
    else:
        with pytest.raises(bootstrap.BootstrapError, match="installed project"):
            bootstrap._check_loaded(plan)


@pytest.mark.parametrize("namespace", ["io", "re"])
@pytest.mark.parametrize("case", ["canonical", "impostor", "wrong_parent_origin"])
def test_typing_namespace_alias_requires_exact_protected_parent(
    monkeypatch: pytest.MonkeyPatch, namespace: str, case: str,
) -> None:
    origin = "/runtime/stdlib/typing.py"
    parent = ModuleType("typing")
    loader = importlib.machinery.SourceFileLoader("typing", origin)
    parent.__spec__ = importlib.machinery.ModuleSpec("typing", loader, origin=origin)
    parent.__file__ = origin
    alias = type("synthetic_namespace", (), {})
    parent.__dict__[namespace] = alias
    observed = alias
    if case == "impostor":
        observed = type("synthetic_namespace", (), {})
    elif case == "wrong_parent_origin":
        parent.__spec__.origin = "/runtime/other/typing.py"
        parent.__file__ = "/runtime/other/typing.py"
    plan: dict[str, Any] = {
        "checkout": "/owned", "site_packages": "/owned/.venv/site", "stdlib": "/runtime/stdlib",
        "files": [{"path": origin}, {"path": "/runtime/other/typing.py"}],
        "import_map": {}, "frozen_modules": [], "builtin_modules": [],
    }
    monkeypatch.setattr(bootstrap, "sys", SimpleNamespace(modules={
        "typing": parent, "typing." + namespace: observed,
    }))
    if case == "canonical":
        bootstrap._check_loaded(plan)
    else:
        with pytest.raises(bootstrap.BootstrapError, match="Typing namespace"):
            bootstrap._check_loaded(plan)
