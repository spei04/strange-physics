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
