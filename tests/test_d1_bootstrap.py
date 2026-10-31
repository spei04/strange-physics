"""Retained-reference tests with synthetic owners; no endpoint or exp call."""

from __future__ import annotations

import hashlib
import importlib.machinery
import json
import math
import sys
from pathlib import Path
from types import CodeType, FrameType, ModuleType, SimpleNamespace
from typing import Any, NoReturn, cast

import d1_bootstrap as bootstrap
import pytest


@pytest.fixture(autouse=True)
def isolated_denied_work_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test isolation only: the production once-per-child latch has no reset API.
    monkeypatch.setattr(bootstrap, "_DENIED_WORK", None)
    monkeypatch.setattr(bootstrap, "_STANDARD_ATTEMPTED", False)
    monkeypatch.setattr(bootstrap, "_PREPARED_RANDOM", None)
    monkeypatch.setattr(bootstrap, "_PREPARED_EXP", None)
    monkeypatch.setattr(bootstrap, "_WINDOW", None)


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

        def trig(self) -> None:
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
    objects = {
        "endpoint_belief_reference": oracle,
        "math": actual_math,
        "d1_fixture_reference": fixture,
        "d1_prefix_evidence": prefix,
        "d1_originals": originals,
    }
    captured: list[tuple[Any, ...]] = []

    def anchors(*values: Any) -> tuple[Any, ...]:
        calls.append("anchors")
        captured.append(values)
        return values

    def prepare(held: tuple[Any, ...], **kwargs: Any) -> SimpleNamespace:
        calls.append("prepare")
        assert kwargs["commit"] == "a" * 40
        assert kwargs["pins"] == tuple(
            {"path": rel, "sha256": "b" * 64} for rel in bootstrap.SOURCE_PIN_PATHS
        )
        assert held[0] is oracle and held[1] is Owner and held[-1] is math.exp
        return SimpleNamespace(
            reference=object(),
            producer=object(),
            owners=(Owner(),) * 13,
            original_methods=(Owner().position,) * 22,
            emitter=math.exp,
        )

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
    profile_state: list[object] = [None]

    def set_profile(callback: object) -> None:
        bootstrap._deny_external_work("sys.setprofile", ())
        profile_state[0] = callback

    def stopped(code: int) -> NoReturn:
        assert code == 86
        raise bootstrap.BootstrapError(
            "Capture observed denied work: " + str(bootstrap._DENIED_WORK)
        )

    monkeypatch.setattr(
        bootstrap,
        "sys",
        SimpleNamespace(
            modules=module_table,
            getprofile=lambda: profile_state[0],
            setprofile=set_profile,
            gettrace=lambda: None,
        ),
    )
    monkeypatch.setattr(
        bootstrap, "os", SimpleNamespace(write=lambda fd, raw: len(raw), _exit=stopped)
    )
    prepared_random = ModuleType("random")
    prepared_random.__dict__["_exp"] = math.exp
    module_table["random"] = prepared_random
    monkeypatch.setattr(bootstrap, "_STANDARD_ATTEMPTED", True)
    monkeypatch.setattr(bootstrap, "_PREPARED_RANDOM", prepared_random)
    monkeypatch.setattr(bootstrap, "_PREPARED_EXP", math.exp)
    monkeypatch.setattr(bootstrap, "math", actual_math)
    monkeypatch.setattr(
        bootstrap, "importlib", SimpleNamespace(import_module=lambda name: objects[name])
    )
    monkeypatch.setattr(bootstrap, "_check_loaded", lambda plan: None)
    for name in ("endpoint_belief_reference", *bootstrap.CONSUMERS):
        module_table.pop(name, None)
    module_table["math"] = actual_math
    plan = {
        "checkout": "/synthetic",
        "site_packages": "/synthetic/venv/site-packages",
        "source_commit": "a" * 40,
        "import_map": {"endpoint_belief_reference": Owner.position.__code__.co_filename},
        "files": [
            {"path": "/synthetic/" + rel, "sha256": "b" * 64} for rel in bootstrap.SOURCE_PIN_PATHS
        ],
    }
    return plan, {
        "calls": calls,
        "objects": objects,
        "owner": Owner,
        "captured": captured,
        "modules": module_table,
        "profile": profile_state,
    }


def test_capture_retains_before_consumers_and_constructs_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, context = fake_boundary(monkeypatch)
    prepared = bootstrap.capture(plan)
    assert context["calls"] == [
        "endpoint_belief_reference",
        "d1_fixture_reference",
        "d1_prefix_evidence",
        "d1_originals",
        "anchors",
        "prepare",
    ]
    held = context["captured"][0]
    for name, function, code in zip(bootstrap.METHOD_NAMES, held[2], held[3], strict=True):
        assert context["owner"].__dict__[name] is function
        assert function.__code__ is code
    assert prepared.emitter is held[-1] and len(prepared.owners) == 13
    window = bootstrap._WINDOW
    assert window is not None and context["profile"][0] is window.callback
    assert len(window.codes) == 5
    assert all(
        actual is expected for actual, expected in zip(window.codes[:4], held[3], strict=True)
    )


@pytest.mark.parametrize(
    "mutation", ["module", "class", "function", "code", "math_module", "emitter"]
)
def test_retained_identity_detects_replacement(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
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


@pytest.mark.parametrize(
    "event",
    [
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.fork",
        "os.posix_spawn",
        "socket.connect",
        "socket.__new__",
    ],
)
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


@pytest.mark.parametrize(
    "case",
    [
        "allowed",
        "unknown_origin",
        "alias",
        "tests_alias",
        "missing_spec",
        "unknown_builtin",
        "unknown_frozen",
        "native_outside_map",
    ],
)
def test_loaded_registry_matches_fixed_origins(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    name = "owned"
    origin = "/owned/source.py"
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "files": [{"path": origin}],
        "import_map": {name: origin},
        "checkout": "/owned",
        "frozen_modules": ["os"],
        "builtin_modules": ["sys"],
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


@pytest.mark.parametrize(
    "case",
    [
        "success",
        "not_isolated",
        "bytecode_writes",
        "used_cache",
        "path",
        "version",
        "prefix",
        "checkout_path",
    ],
)
def test_child_startup_gates_without_importing_consumers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    root = tmp_path / "checkout"
    venv = tmp_path / "venv"
    captured: list[object] = []
    hooks: list[object] = []
    plan = {
        "checkout": str(root),
        "venv_root": str(venv),
        "python_version": "3.12.3",
        "startup_sys_path": ["/owned/stdlib"],
        "builtin_modules": ["sys"],
        "bootstrap": str(Path(bootstrap.__file__).absolute()),
        "source_commit": "a" * 40,
    }
    state = SimpleNamespace(
        flags=SimpleNamespace(isolated=1, dont_write_bytecode=1),
        _xoptions={"pycache_prefix": str(cache)},
        version_info=(3, 12, 3),
        prefix=str(venv),
        path=["/owned/stdlib"],
        builtin_module_names=("sys",),
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
    standard: list[object] = []
    monkeypatch.setattr(bootstrap, "_prepare_standard_library", standard.append)

    def capture(record: dict[str, Any]) -> SimpleNamespace:
        captured.append(record)
        return SimpleNamespace(owners=(object(),) * 13, original_methods=(object(),) * 22)

    monkeypatch.setattr(bootstrap, "capture", capture)
    if case == "success":
        result = bootstrap.child(tmp_path / "record", "b" * 64, cache)
        assert result["owners"] == 13 and result["primitive_calls_permitted"] is False
        assert captured == [plan] and hooks == [bootstrap._deny_external_work]
        assert standard == [plan]
    else:
        with pytest.raises(bootstrap.BootstrapError):
            bootstrap.child(tmp_path / "record", "b" * 64, cache)
        assert captured == [] and hooks == [] and standard == []


@pytest.mark.parametrize(
    "name",
    [
        "d1_primitive_recording",
        "d1_primitive_sink",
        "d1_codec_append",
        "d1_table_retention",
        "unmapped_helper",
        "strange_physics.unmapped",
    ],
)
def test_pinned_but_unmapped_checkout_origin_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    origin = "/owned/tests/" + name + ".py"
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "checkout": "/owned",
        "files": [{"path": origin}],
        "import_map": {},
        "frozen_modules": [],
        "builtin_modules": [],
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
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
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
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    site = "/owned/.venv/lib/python3.12/site-packages"
    name = "dependency.module" if case == "dependency_inside_checkout_venv" else "project_alias"
    suffix = (
        "/dependency/module.py"
        if case == "dependency_inside_checkout_venv"
        else ("/strange_physics/unlisted.py")
    )
    origin = site + suffix
    module = ModuleType(name)
    loader = importlib.machinery.SourceFileLoader(name, origin)
    module.__spec__ = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    plan = {
        "checkout": "/owned",
        "site_packages": site,
        "files": [{"path": origin}],
        "import_map": {},
        "frozen_modules": [],
        "builtin_modules": [],
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
    monkeypatch: pytest.MonkeyPatch,
    namespace: str,
    case: str,
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
        "checkout": "/owned",
        "site_packages": "/owned/.venv/site",
        "stdlib": "/runtime/stdlib",
        "files": [{"path": origin}, {"path": "/runtime/other/typing.py"}],
        "import_map": {},
        "frozen_modules": [],
        "builtin_modules": [],
    }
    monkeypatch.setattr(
        bootstrap,
        "sys",
        SimpleNamespace(
            modules={
                "typing": parent,
                "typing." + namespace: observed,
            }
        ),
    )
    if case == "canonical":
        bootstrap._check_loaded(plan)
    else:
        with pytest.raises(bootstrap.BootstrapError, match="Typing namespace"):
            bootstrap._check_loaded(plan)


# All frame/code objects below are owned synthetic metadata. The dummy body is
# never called, and helper-local sys/os proxies never install a real profiler.
def guard_dummy() -> None:
    raise AssertionError("synthetic primitive body must not execute")


def frame_for(code: CodeType) -> FrameType:
    return cast(FrameType, SimpleNamespace(f_code=code))


def fresh_window(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[str, Any], bootstrap._PrimitiveWindow]:
    plan, context = fake_boundary(monkeypatch)
    window = bootstrap._start_window(plan)
    return plan, context, window


@pytest.mark.parametrize(
    "name",
    ("position", "exp", "log", "circle_constant", "trig"),
    ids=("position", "exp", "log", "circle", "trig"),
)
def test_fixed_oracle_routes_deny_before_retained_codes(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    _, _, window = fresh_window(monkeypatch)
    assert window.codes == ()
    code = guard_dummy.__code__.replace(
        co_filename="/synthetic/tests/endpoint_belief_reference.py",
        co_qualname="EndpointOracle." + name,
    )
    with pytest.raises(bootstrap.BootstrapError, match="denied work"):
        window.profile(frame_for(code), "call", None)
    assert bootstrap._DENIED_WORK == "source:EndpointOracle." + name


def test_first_oracle_import_is_inside_window(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, context = fake_boundary(monkeypatch)
    original_import = bootstrap._source_module

    def importer(name: str, record: dict[str, Any]) -> ModuleType:
        if name == "endpoint_belief_reference":
            window = bootstrap._WINDOW
            assert window is not None and window.armed and window.codes == ()
            code = guard_dummy.__code__.replace(
                co_filename="/synthetic/tests/endpoint_belief_reference.py",
                co_qualname="EndpointOracle.position",
            )
            window.profile(frame_for(code), "call", None)
        return original_import(name, record)

    monkeypatch.setattr(bootstrap, "_source_module", importer)
    with pytest.raises(bootstrap.BootstrapError, match="EndpointOracle.position"):
        bootstrap.capture(plan)
    assert context["calls"] == [] and context["captured"] == []


def test_exact_retained_code_is_bound_before_first_consumer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, context = fake_boundary(monkeypatch)
    original_import = bootstrap._source_module

    def importer(name: str, record: dict[str, Any]) -> ModuleType:
        if name == "d1_fixture_reference":
            window = bootstrap._WINDOW
            assert window is not None and len(window.codes) == 5
            code = context["owner"].position.__code__
            assert code is window.codes[0]
            window.profile(frame_for(code), "call", None)
        return original_import(name, record)

    monkeypatch.setattr(bootstrap, "_source_module", importer)
    with pytest.raises(bootstrap.BootstrapError, match="retained-oracle-code"):
        bootstrap.capture(plan)
    assert context["calls"] == ["endpoint_belief_reference"]
    assert context["captured"] == []


@pytest.mark.parametrize("denied", (True, False), ids=("exp", "other"))
def test_retained_c_identity_without_invoking_callable(
    monkeypatch: pytest.MonkeyPatch, denied: bool
) -> None:
    _, _, window = fresh_window(monkeypatch)
    if denied:
        with pytest.raises(bootstrap.BootstrapError, match="retained-c:math.exp"):
            window.profile(frame_for(guard_dummy.__code__), "c_call", math.exp)
    else:
        window.profile(frame_for(guard_dummy.__code__), "c_call", len)
        window.profile(frame_for(guard_dummy.__code__), "call", None)
        window.profile(frame_for(guard_dummy.__code__), "return", math.exp)
        window.check()
        assert bootstrap._DENIED_WORK is None


def test_consumer_scientific_route_is_denied_without_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, context, window = fresh_window(monkeypatch)
    code = guard_dummy.__code__.replace(
        co_filename="/synthetic/tests/d1_prefix_evidence.py", co_qualname="qualify_prefix"
    )
    with pytest.raises(bootstrap.BootstrapError, match="source:qualify_prefix"):
        window.profile(frame_for(code), "call", None)
    assert context["calls"] == []


@pytest.mark.parametrize("event", ("sys.setprofile", "sys.settrace"), ids=("profile", "trace"))
def test_armed_guard_replacement_is_fatal(monkeypatch: pytest.MonkeyPatch, event: str) -> None:
    _, context, window = fresh_window(monkeypatch)
    with pytest.raises(bootstrap.BootstrapError, match="guard-removal"):
        bootstrap._deny_external_work(event, ())
    assert context["profile"][0] is window.callback
    assert bootstrap._DENIED_WORK == "guard-removal:" + event


@pytest.mark.parametrize("kind", ("profile", "trace"), ids=("profile", "trace"))
def test_preexisting_instrumentation_rejects_before_import(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    plan, context = fake_boundary(monkeypatch)
    if kind == "profile":
        context["profile"][0] = object()
    else:
        # Change only the helper-local namespace; never global sys tracing.
        proxy = SimpleNamespace(
            modules=context["modules"],
            getprofile=lambda: None,
            gettrace=lambda: object(),
            setprofile=lambda callback: None,
        )
        monkeypatch.setattr(bootstrap, "sys", proxy)
    with pytest.raises(bootstrap.BootstrapError, match="preexisting"):
        bootstrap.capture(plan)
    assert context["calls"] == []


def test_missing_profile_cannot_produce_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _, context, window = fresh_window(monkeypatch)
    context["profile"][0] = None
    with pytest.raises(bootstrap.BootstrapError, match="capture-profile-missing"):
        window.check()


@pytest.mark.parametrize("write_fails", (False, True), ids=("diagnostic", "write-failed"))
def test_swallowed_first_denial_survives_diagnostic_uncertainty(
    monkeypatch: pytest.MonkeyPatch,
    write_fails: bool,
) -> None:
    _, _, window = fresh_window(monkeypatch)
    writes: list[bytes] = []
    exits: list[int] = []

    def write(fd: int, raw: bytes) -> int:
        assert fd == 2
        writes.append(raw)
        if write_fails:
            raise OSError("synthetic diagnostic failure")
        return 1  # Deliberately partial: no diagnostic acknowledgement claim.

    def stop(code: int) -> NoReturn:
        exits.append(code)
        raise bootstrap.BootstrapError("synthetic fatal child exit")

    monkeypatch.setattr(bootstrap, "os", SimpleNamespace(write=write, _exit=stop))
    for label in ("first-denial", "later-denial"):
        with pytest.raises(bootstrap.BootstrapError):
            window.deny(label)
    with pytest.raises(bootstrap.BootstrapError):
        window.check()
    assert bootstrap._DENIED_WORK == "first-denial"
    assert writes == [b"D1_DENIED:first-denial\n"] and exits == [86, 86, 86]


def standard_boundary(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    module = ModuleType("random")
    origin = "/runtime/stdlib/random.py"
    module.__file__ = origin
    loader = importlib.machinery.SourceFileLoader("random", origin)
    module.__spec__ = importlib.machinery.ModuleSpec("random", loader, origin=origin)
    module.__dict__["_exp"] = math.exp
    actual_math = ModuleType("math")
    actual_math.__dict__["exp"] = math.exp
    imports: list[str] = []
    checks: list[object] = []
    state = SimpleNamespace(path=["/runtime/stdlib"], modules={"random": module})

    def load(name: str) -> ModuleType:
        assert bootstrap._WINDOW is None and state.path == ["/runtime/stdlib"]
        imports.append(name)
        return module

    monkeypatch.setattr(bootstrap, "sys", state)
    monkeypatch.setattr(bootstrap, "math", actual_math)
    monkeypatch.setattr(
        bootstrap, "importlib", SimpleNamespace(import_module=load, machinery=importlib.machinery)
    )
    monkeypatch.setattr(bootstrap, "_check_loaded", checks.append)
    plan = {
        "checkout": "/owned",
        "stdlib": "/runtime/stdlib",
        "files": [
            {
                "path": origin,
                "bytes": 34683,
                "sha256": "0693d4ded36916f5b07d6c395cc331dbf1011bb70e90daaa29eaa32490a09425",
            }
        ],
    }
    return plan, {"module": module, "state": state, "imports": imports, "checks": checks}


def test_reviewed_standard_initialization_precedes_helper_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, context = standard_boundary(monkeypatch)
    bootstrap._prepare_standard_library(plan)
    assert context["imports"] == ["random"] and context["checks"] == [plan]
    assert bootstrap._PREPARED_RANDOM is context["module"]
    assert bootstrap._PREPARED_EXP is math.exp and bootstrap._WINDOW is None
    with pytest.raises(bootstrap.BootstrapError, match="consumed"):
        bootstrap._prepare_standard_library(plan)
    assert context["imports"] == ["random"]


@pytest.mark.parametrize(
    "kind",
    ("pin", "origin", "alias", "helper-path", "import-error"),
    ids=("pin", "origin", "alias", "lookup", "import"),
)
def test_standard_failure_cannot_start_capture(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    plan, context = standard_boundary(monkeypatch)
    if kind == "pin":
        plan["files"][0]["sha256"] = "0" * 64
    elif kind == "origin":
        context["module"].__spec__.origin = "/other/random.py"
    elif kind == "alias":
        context["module"].__dict__["_exp"] = len
    elif kind == "helper-path":
        context["state"].path.append("/owned/tests")
    else:

        def failed_import(name: str) -> NoReturn:
            raise OSError("synthetic stdlib import failure")

        monkeypatch.setattr(bootstrap, "importlib", SimpleNamespace(import_module=failed_import))
    with pytest.raises((bootstrap.BootstrapError, OSError)):
        bootstrap._prepare_standard_library(plan)
    assert bootstrap._PREPARED_RANDOM is None and bootstrap._PREPARED_EXP is None
    assert bootstrap._WINDOW is None and bootstrap._STANDARD_ATTEMPTED is True
    with pytest.raises(bootstrap.BootstrapError, match="consumed"):
        bootstrap._prepare_standard_library(plan)
    with pytest.raises(bootstrap.BootstrapError, match="initialization"):
        bootstrap._start_window(plan)


def test_window_cannot_be_recreated_after_consumption(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, _, window = fresh_window(monkeypatch)
    with pytest.raises(bootstrap.BootstrapError, match="consumed"):
        bootstrap._start_window(plan)
    assert bootstrap._WINDOW is window
