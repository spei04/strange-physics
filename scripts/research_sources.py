"""Offline RA-01 source admission checks; never fetch or execute recipe commands."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from strange_physics.bounded_json import parse_bounded_json
from strange_physics.contracts import Message

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/research/source-admission.json"
SCHEMA = ROOT / "docs/research/source-admission.schema.json"
Sha = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$", min_length=40, max_length=40)]
Key = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]*$", min_length=1, max_length=80)]
Text = Annotated[str, Field(min_length=1, max_length=4000)]
Url = Annotated[str, Field(pattern=r"^https://[A-Za-z0-9./_#?=%+:-]+$", max_length=1000)]
MAX_BYTES = 512 * 1024


class Paper(Message):
    """Publication identity is independent of the code's commit or release."""

    title: Text
    url: Url
    version: Text
    first_published: date
    version_published: date
    sections: Text

    @model_validator(mode="after")
    def chronology(self) -> Self:
        if self.first_published > self.version_published:
            raise ValueError("Paper version predates first publication")
        return self


class Repository(Message):
    id: Key
    url: Url
    availability: Literal["available", "unavailable"]
    commit: Commit | None
    tree: Commit | None
    committed_on: date | None
    observed_default_head: Commit | None
    evidence: Text

    @model_validator(mode="after")
    def available_identity(self) -> Self:
        values = (self.commit, self.tree, self.committed_on, self.observed_default_head)
        if self.availability == "available":
            if any(value is None for value in values):
                raise ValueError("Available code requires exact dated commit/tree")
        elif any(value is not None for value in values):
            raise ValueError("Unavailable code cannot invent a commit")
        return self


class FileEvidence(Message):
    id: Key
    repository_id: Key
    path: Annotated[str, Field(min_length=1, max_length=300)]
    sha256: Sha
    bytes: Annotated[int, Field(ge=1, le=4 * 1024 * 1024)]
    purpose: Literal["license", "notice", "dependencies", "recipe", "leakage", "provenance"]

    @model_validator(mode="after")
    def relative_path(self) -> Self:
        if (
            self.path.startswith("/")
            or "\\" in self.path
            or any(part in {"", ".", ".."} for part in self.path.split("/"))
        ):
            raise ValueError("Evidence paths must be repository relative")
        return self


class LicenseReview(Message):
    status: Literal["grant_verified", "missing_grant", "unavailable"]
    expression: Text | None
    evidence_ids: Annotated[tuple[Key, ...], Field(max_length=16)]
    obligations: Text

    @model_validator(mode="after")
    def grant(self) -> Self:
        if self.status == "grant_verified":
            if self.expression is None or not self.evidence_ids:
                raise ValueError("A badge or repository metadata is not a license grant")
        elif self.expression is not None or self.evidence_ids:
            raise ValueError("Unverified grants cannot be asserted")
        return self


class Dependencies(Message):
    status: Literal["existing_locked_runtime", "unlocked_external", "unavailable"]
    runtime: Text
    evidence_ids: Annotated[tuple[Key, ...], Field(max_length=16)]
    transitive_review: Text

    @model_validator(mode="after")
    def known_dependencies(self) -> Self:
        if self.status != "unavailable" and not self.evidence_ids:
            raise ValueError("Dependency claims need actual manifest evidence")
        return self


class Recipe(Message):
    """Human-reviewed instructions, never an execution capability."""

    kind: Literal["existing_native_validation", "upstream_unexecuted", "unavailable"]
    commands: Annotated[tuple[tuple[Text, ...], ...], Field(max_length=12)]
    working_directory: Text
    prerequisites: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]
    inputs: Text
    expected_artifacts: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]
    executed_in_ra01: Annotated[bool, Field(json_schema_extra={"const": False})]
    limitations: Text

    @model_validator(mode="after")
    def executable_or_missing(self) -> Self:
        if self.executed_in_ra01:
            raise ValueError("Recipe execution was not part of RA-01")
        if (self.kind == "unavailable") != (len(self.commands) == 0):
            raise ValueError("Only an unavailable recipe may omit commands")
        if any(not command or len(command) > 32 for command in self.commands):
            raise ValueError("Each recipe command needs bounded argv")
        return self


class Method(Message):
    id: Key
    title: Text
    papers: Annotated[tuple[Paper, ...], Field(min_length=1, max_length=4)]
    repository_ids: Annotated[tuple[Key, ...], Field(min_length=1, max_length=4)]
    license: LicenseReview
    dependencies: Dependencies
    recipe: Recipe
    reproduction_status: Literal["self_authored_baseline", "not_reproduced"]
    review_date: date
    admission: Literal["native_implementation", "deferred", "no_go"]
    rationale: Text
    artifact_availability: Text
    leakage_boundary: Text
    inspiration_only: bool

    @model_validator(mode="after")
    def admission_gate(self) -> Self:
        if self.admission == "native_implementation":
            if (
                self.id != "native-linear-spring"
                or self.repository_ids != ("strange-physics",)
                or self.license.status != "grant_verified"
                or self.dependencies.status != "existing_locked_runtime"
                or self.recipe.kind != "existing_native_validation"
                or self.reproduction_status != "self_authored_baseline"
                or self.inspiration_only
            ):
                raise ValueError("Native admission requires own locked, licensed baseline")
        else:
            if self.dependencies.status == "existing_locked_runtime":
                raise ValueError("External code is not part of the existing runtime")
            if not self.inspiration_only:
                raise ValueError("No external code reuse was admitted")
            if self.reproduction_status != "not_reproduced":
                raise ValueError("External reproduction was not executed in this audit")
        if self.license.status != "grant_verified" and self.admission != "no_go":
            raise ValueError("Missing grant requires explicit reuse no-go")
        return self


class RuntimeNotice(Message):
    package: Text
    version: Text
    path: Text
    sha256: Sha
    bytes: Annotated[int, Field(ge=1, le=1024 * 1024)]


class SourceAdmission(Message):
    schema_version: Literal["strange-physics.source-admission.v1"]
    audited_on: date
    review_due: date
    scope: Literal["RA-01 source admission only; no comparison execution or reproduction"]
    repositories: Annotated[tuple[Repository, ...], Field(min_length=1, max_length=24)]
    evidence: Annotated[tuple[FileEvidence, ...], Field(min_length=1, max_length=128)]
    runtime_notices: Annotated[tuple[RuntimeNotice, ...], Field(min_length=1, max_length=64)]
    methods: Annotated[tuple[Method, ...], Field(min_length=1, max_length=24)]
    future_native_run_recipe: Literal["unresolved_until_producer_and_manifest_gates"]

    @model_validator(mode="after")
    def provenance(self) -> Self:
        repos = {value.id: value for value in self.repositories}
        files = {value.id: value for value in self.evidence}
        methods = {value.id: value for value in self.methods}
        if (len(repos), len(files), len(methods)) != (
            len(self.repositories),
            len(self.evidence),
            len(self.methods),
        ):
            raise ValueError("Duplicate source/evidence/method identity")
        if self.review_due <= self.audited_on:
            raise ValueError("Review date must follow audit")
        for repo in self.repositories:
            if repo.committed_on is not None and repo.committed_on > self.audited_on:
                raise ValueError("Future source identity")
        file_keys = [(item.repository_id, item.path) for item in self.evidence]
        if len(set(file_keys)) != len(file_keys):
            raise ValueError("Duplicate file claims under different evidence IDs")
        for item in self.evidence:
            if item.repository_id not in repos or repos[item.repository_id].commit is None:
                raise ValueError("File evidence requires an available pinned repository")
        for method in self.methods:
            if method.review_date != self.audited_on:
                raise ValueError("All method decisions must be dated at this audit")
            if any(paper.version_published > self.audited_on for paper in method.papers):
                raise ValueError("Future publication")
            if len(set(method.repository_ids)) != len(method.repository_ids) or any(
                name not in repos for name in method.repository_ids
            ):
                raise ValueError("Unknown or duplicate method repository")
            for key in (*method.license.evidence_ids, *method.dependencies.evidence_ids):
                if key not in files or files[key].repository_id not in method.repository_ids:
                    raise ValueError("Evidence belongs to another source")
            if any(repos[key].availability == "unavailable" for key in method.repository_ids):
                if method.recipe.kind != "unavailable":
                    raise ValueError("Unavailable source cannot have executable recipe")
            if method.license.status == "grant_verified":
                covered = {
                    files[key].repository_id
                    for key in method.license.evidence_ids
                    if files[key].purpose == "license"
                }
                if covered != set(method.repository_ids):
                    raise ValueError("Every code repository needs its own license evidence")
            if any(
                files[key].purpose != "dependencies" for key in method.dependencies.evidence_ids
            ):
                raise ValueError("Dependency evidence must name actual manifests")
        required = {
            "native-linear-spring",
            "newtonbench",
            "mda",
            "autoscilab",
            "aces",
            "pysr",
            "pysindy",
            "zsindy",
            "neuronbench",
            "glucosebench",
        }
        if set(methods) != required:
            raise ValueError("RA-01 source coverage is incomplete or unreviewed")
        native = methods.get("native-linear-spring")
        if native is None or native.admission != "native_implementation":
            raise ValueError("Native source decision must remain explicit")
        notice_keys = [(item.package, item.version, item.path) for item in self.runtime_notices]
        if len(set(notice_keys)) != len(notice_keys):
            raise ValueError("Duplicate dependency notice")
        return self


def load_manifest(path: Path = MANIFEST) -> SourceAdmission:
    """Read at most the fixed audit envelope; no network, subprocess or imports from sources."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Manifest must be a bounded regular file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return parse_bounded_json(
        raw, SourceAdmission, max_bytes=MAX_BYTES, max_depth=16, max_nodes=50_000
    )


def schema() -> dict[str, object]:
    return SourceAdmission.model_json_schema() | {
        "$id": "https://strange-physics.invalid/research/source-admission.schema.json",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "RA-01 shapes; cross-field admission joins require the validator.",
    }


def audit_summary(manifest: SourceAdmission, method_id: str | None = None) -> dict[str, object]:
    selected = [item for item in manifest.methods if method_id is None or item.id == method_id]
    if not selected:
        raise ValueError("Unknown method")
    return {
        "audited_on": manifest.audited_on.isoformat(),
        "scope": manifest.scope,
        "manifest_sha256": hashlib.sha256(
            json.dumps(
                manifest.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest(),
        "decisions": {item.id: item.admission for item in selected},
        "external_code_executed": False,
        "comparison_executed": False,
        "future_native_run_recipe": manifest.future_native_run_recipe,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--method")
    parser.add_argument("--check-schema", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if args.check_schema and json.loads(SCHEMA.read_text()) != schema():
        raise ValueError("Stored source-admission schema differs from typed model")
    print(json.dumps(audit_summary(manifest, args.method), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
