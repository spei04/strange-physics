"""Source-audit provenance and admission failures; no external imports or execution."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import socket
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.research_sources import (
    MANIFEST,
    MAX_BYTES,
    SCHEMA,
    SourceAdmission,
    audit_summary,
    load_manifest,
    schema,
)
from strange_physics.control_contracts import ContractViolation

Draft202012Validator = importlib.import_module("jsonschema").Draft202012Validator


def document() -> dict[str, Any]:
    value = json.loads(MANIFEST.read_text())
    assert isinstance(value, dict)
    return value


def parse(value: dict[str, Any]) -> SourceAdmission:
    return SourceAdmission.model_validate_json(json.dumps(value))


def test_complete_offline_audit_and_schema() -> None:
    value = load_manifest()
    assert len(value.methods) == 10
    assert len(value.repositories) == 11
    assert len(value.runtime_notices) == 22
    assert json.loads(SCHEMA.read_text()) == schema()
    Draft202012Validator.check_schema(schema())
    Draft202012Validator(schema()).validate(document())
    summary = audit_summary(value)
    assert summary["decisions"] == {
        "native-linear-spring": "native_implementation",
        "newtonbench": "deferred",
        "mda": "no_go",
        "autoscilab": "deferred",
        "aces": "no_go",
        "pysr": "deferred",
        "pysindy": "deferred",
        "zsindy": "no_go",
        "neuronbench": "deferred",
        "glucosebench": "deferred",
    }
    assert summary["external_code_executed"] is False
    assert summary["comparison_executed"] is False
    with pytest.raises(ValueError, match="Unknown method"):
        audit_summary(value, "absent")


def test_canonical_manifest_identity_is_distinct_from_raw_file_bytes() -> None:
    value = load_manifest()
    canonical = json.dumps(
        value.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    assert audit_summary(value)["canonical_manifest_sha256"] == digest
    reformatted = SourceAdmission.model_validate_json(json.dumps(document(), indent=4))
    assert audit_summary(reformatted)["canonical_manifest_sha256"] == digest
    assert digest != hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert "manifest_sha256" not in audit_summary(value)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("methods", 0, "license", "evidence_ids"), []),
        (("methods", 0, "license", "evidence_ids"), ["pysr-license"]),
        (("methods", 0, "license", "evidence_ids"), ["native-lock"]),
        (("methods", 0, "dependencies", "evidence_ids"), ["native-license"]),
        (("methods", 0, "dependencies", "evidence_ids"), []),
        (("methods", 0, "dependencies", "status"), "unlocked_external"),
        (("methods", 0, "recipe", "commands"), []),
        (("methods", 0, "recipe", "commands"), [[]]),
        (("methods", 0, "recipe", "executed_in_ra01"), True),
        (("methods", 0, "recipe", "kind"), "upstream_unexecuted"),
        (("methods", 1, "recipe", "kind"), "existing_native_validation"),
        (("methods", 0, "reproduction_status"), "not_reproduced"),
        (("methods", 0, "inspiration_only"), True),
        (("methods", 1, "admission"), "native_implementation"),
        (("methods", 1, "reproduction_status"), "reproduced"),
        (("methods", 2, "admission"), "deferred"),
        (("methods", 2, "license", "expression"), "MIT"),
        (("methods", 2, "recipe", "commands"), [["python", "missing.py"]]),
        (("methods", 4, "license", "status"), "grant_verified"),
        (("methods", 4, "repository_ids"), ["unknown"]),
        (("methods", 4, "repository_ids"), ["aces", "aces"]),
        (("methods", 0, "review_date"), "2026-10-20"),
        (("methods", 1, "papers", 0, "version_published"), "2027-01-01"),
        (("methods", 1, "papers", 0, "first_published"), "2027-01-01"),
        (("repositories", 0, "commit"), None),
        (("repositories", 0, "tree"), "short"),
        (("repositories", 0, "committed_on"), "2027-01-01"),
        (("repositories", 10, "commit"), "a" * 40),
        (("evidence", 0, "repository_id"), "mda"),
        (("evidence", 0, "path"), "../LICENSE"),
        (("evidence", 0, "path"), "/LICENSE"),
        (("evidence", 0, "bytes"), True),
        (("evidence", 0, "sha256"), "0" * 63),
        (("review_due",), "2026-10-21"),
        (("future_native_run_recipe",), "run-now"),
    ],
)
def test_bad_provenance_and_claims(path: tuple[str | int, ...], replacement: Any) -> None:
    value = document()
    cursor: Any = value
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = replacement
    with pytest.raises(ValidationError):
        parse(value)


@pytest.mark.parametrize("field", ["methods", "repositories", "evidence", "runtime_notices"])
def test_duplicate_identities(field: str) -> None:
    value = document()
    value[field].append(copy.deepcopy(value[field][0]))
    with pytest.raises(ValidationError, match="Duplicate"):
        parse(value)


@pytest.mark.parametrize("method_id", ["mda", "aces", "zsindy"])
def test_missing_external_grant_does_not_block_own_native_admission(method_id: str) -> None:
    manifest = load_manifest()
    decisions = audit_summary(manifest)["decisions"]
    assert isinstance(decisions, dict)
    assert decisions[method_id] == "no_go"
    assert decisions["native-linear-spring"] == "native_implementation"


def test_historical_native_baseline_is_not_relabelled_current() -> None:
    manifest = load_manifest()
    native = next(item for item in manifest.repositories if item.id == "strange-physics")
    assert native.commit == "33ddfbf74837dde29e0f1db3b1b4263e7031ddc2"
    lock = next(item for item in manifest.evidence if item.id == "native-lock")
    assert lock.repository_id == native.id
    assert lock.path == "uv.lock"
    assert lock.sha256 == "b83593cf033d0459848ceb699b1067706566ac09e23d864733698a5077b04b85"
    assert manifest.future_native_run_recipe == "unresolved_until_producer_and_manifest_gates"


def test_new_license_keeps_leakage_and_reproduction_gates() -> None:
    manifest = load_manifest()
    method = next(item for item in manifest.methods if item.id == "autoscilab")
    repo = next(item for item in manifest.repositories if item.id == "autoscilab")
    assert repo.commit == "467fa184ba537d26b2228ee3f3a8c052d9bfca58"
    assert method.license.status == "grant_verified"
    assert method.admission == "deferred"
    assert method.reproduction_status == "not_reproduced"
    assert "evaluate_law" in method.leakage_boundary
    assert "GT_RMSLE" in method.leakage_boundary


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":"a","schema_version":"b"}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":1e999}',
        b'{"a":"\xff"}',
        b"[" * 17 + b"0" + b"]" * 17,
        b" " * (MAX_BYTES + 1),
        b"",
    ],
)
def test_strict_bounded_input(raw: bytes, tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    with pytest.raises((ContractViolation, ValueError)):
        load_manifest(path)


def test_unknown_fields_and_boolean_types_rejected() -> None:
    value = document()
    value["methods"][0]["allow_external_execution"] = True
    with pytest.raises(ValidationError):
        parse(value)
    value = document()
    value["methods"][1]["inspiration_only"] = 1
    with pytest.raises(ValidationError):
        parse(value)


def test_no_missing_full_scope_source() -> None:
    value = document()
    value["methods"] = value["methods"][:1]
    with pytest.raises(ValidationError, match="coverage"):
        parse(value)


def test_multi_repository_license_coverage() -> None:
    value = document()
    pysr = next(item for item in value["methods"] if item["id"] == "pysr")
    pysr["license"]["evidence_ids"] = ["pysr-license"]
    with pytest.raises(ValidationError, match="Every code"):
        parse(value)


def test_conflicting_file_claims_cannot_hide_behind_new_id() -> None:
    value = document()
    second = copy.deepcopy(value["evidence"][0])
    second.update(id="conflicting-copy", sha256="f" * 64)
    value["evidence"].append(second)
    with pytest.raises(ValidationError, match="Duplicate file"):
        parse(value)


def test_unavailable_source_cannot_supply_executable_recipe() -> None:
    value = document()
    mda = next(item for item in value["methods"] if item["id"] == "mda")
    mda["recipe"].update(kind="upstream_unexecuted", commands=[["python", "absent.py"]])
    with pytest.raises(ValidationError, match="Unavailable source"):
        parse(value)


@pytest.mark.parametrize("value", [0, 1, "false", None, True])
def test_executed_boolean_runtime_schema_parity(value: Any) -> None:
    raw = document()
    raw["methods"][0]["recipe"]["executed_in_ra01"] = value
    with pytest.raises(ValidationError):
        parse(raw)
    assert list(Draft202012Validator(schema()).iter_errors(raw))


def test_audit_never_runs_commands_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Source audit attempted a process or network call")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    manifest = load_manifest()
    for method in manifest.methods:
        assert audit_summary(manifest, method.id)["external_code_executed"] is False


@pytest.mark.parametrize(
    ("root", "field", "invalid"),
    [
        ("Repository", "url", "https:///"),
        ("Repository", "url", "https://"),
        ("Repository", "url", "https://-github.com/source"),
        ("Repository", "url", "https://github..com/source"),
        ("Repository", "url", "https://github.com/source\n"),
        ("Repository", "id", "native\n"),
        ("FileEvidence", "path", "LICENSE\x00"),
        ("FileEvidence", "path", "LICENSE\n"),
        ("FileEvidence", "path", "LICENSE\x85"),
    ],
)
def test_source_lexical_runtime_schema_parity(root: str, field: str, invalid: str) -> None:
    manifest = document()
    section = "repositories" if root == "Repository" else "evidence"
    item = manifest[section][0]
    item[field] = invalid
    with pytest.raises(ValidationError):
        parse(manifest)
    defs = schema()["$defs"]
    assert isinstance(defs, dict)
    Draft202012Validator(defs[root]).check_schema(defs[root])
    assert not Draft202012Validator(defs[root]).is_valid(item)


def test_duplicate_key_on_otherwise_valid_manifest(tmp_path: Path) -> None:
    raw = json.dumps(document()).encode()
    duplicate = b'{"schema_version":"strange-physics.source-admission.v1",' + raw[1:]
    assert SourceAdmission.model_validate_json(duplicate) == load_manifest()
    path = tmp_path / "duplicate.json"
    path.write_bytes(duplicate)
    with pytest.raises(ContractViolation, match="invalid_request"):
        load_manifest(path)


def test_actual_raw_byte_limit_equality_and_one_over(tmp_path: Path) -> None:
    raw = MANIFEST.read_bytes()
    path = tmp_path / "at-limit.json"
    path.write_bytes(raw + b" " * (MAX_BYTES - len(raw)))
    assert load_manifest(path) == load_manifest()
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bounded"):
        load_manifest(path)
