"""WORLD1 typed contracts. Parsing trusted snapshots does not authorize access."""

from __future__ import annotations

import re
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, Field, TypeAdapter, model_validator

from strange_physics.contracts import ExperimentSpace, Identifier, Message
from strange_physics.control_contracts import CreateRunRequest, Role, RunView
from strange_physics.laws import LawSpec, RadialParameters, SpringParameters, VelocityParameters
from strange_physics.research_contracts import Count, Digest, message_sha256
from strange_physics.run_credential_contracts import HumanProductAuthority
from strange_physics.worker_contracts import OriginalExecutionAdmission
from strange_physics.workspace_contracts import IdempotencyKey, WorkspaceAuthority
from strange_physics.worlds import WorldDefinition

DEFINITION_BYTES = 64 * 1024
PAGE_BYTES = 1024 * 1024
METADATA_BYTES = 4 * 1024 * 1024
MAX_UINT64 = 2**64 - 1


def _uint64_pattern() -> str:
    maximum = str(MAX_UINT64)
    parts = ["0", "[1-9][0-9]{0,18}"]
    for index, char in enumerate(maximum):
        lower = 1 if index == 0 else 0
        digit = int(char)
        if digit > lower:
            atom = str(lower) if digit == lower + 1 else f"[{lower}-{digit - 1}]"
            remaining = len(maximum) - index - 1
            parts.append(maximum[:index] + atom + (f"[0-9]{{{remaining}}}" if remaining else ""))
    parts.append(maximum)
    return "^(?:" + "|".join(parts) + ")$"


UINT64_PATTERN = _uint64_pattern()


def _seed(value: str) -> str:
    if re.fullmatch(UINT64_PATTERN, value) is None:
        raise ValueError("Seed must be a canonical unsigned 64-bit decimal string")
    return value


BrowserSeed = Annotated[
    str,
    Field(
        min_length=1,
        max_length=20,
        pattern=UINT64_PATTERN,
        json_schema_extra={"not": {"pattern": "[^0-9]"}},
    ),
    AfterValidator(_seed),
]
WorldTitle = Annotated[str, Field(min_length=1, max_length=128)]
VersionNumber = Annotated[int, Field(strict=True, ge=1, le=10_000)]
WorldClassification = Literal["customer_authored", "official_blind"]
WorldCapability = Literal[
    "worlds:read", "worlds:write", "worlds:preview", "worlds:preview-grants:manage"
]


class BrowserSpringLaw(Message):
    kind: Literal["spring"]
    parameters: Annotated[
        dict[str, float],
        Field(
            max_length=2,
            json_schema_extra={
                "properties": SpringParameters.model_json_schema()["properties"],
                "additionalProperties": False,
            },
        ),
    ]

    @model_validator(mode="after")
    def supported(self) -> Self:
        SpringParameters.model_validate(self.parameters)
        return self


class BrowserRadialLaw(Message):
    kind: Literal["radial"]
    parameters: Annotated[
        dict[str, float],
        Field(
            max_length=3,
            json_schema_extra={
                "properties": RadialParameters.model_json_schema()["properties"],
                "additionalProperties": False,
            },
        ),
    ]

    @model_validator(mode="after")
    def supported(self) -> Self:
        RadialParameters.model_validate(self.parameters)
        return self


class BrowserVelocityLaw(Message):
    kind: Literal["velocity"]
    parameters: Annotated[
        dict[str, float],
        Field(
            max_length=3,
            json_schema_extra={
                "properties": VelocityParameters.model_json_schema()["properties"],
                "additionalProperties": False,
            },
        ),
    ]

    @model_validator(mode="after")
    def supported(self) -> Self:
        VelocityParameters.model_validate(self.parameters)
        return self


BrowserLaw = Annotated[
    BrowserSpringLaw | BrowserRadialLaw | BrowserVelocityLaw, Field(discriminator="kind")
]


class BrowserWorldDefinition(Message):
    """Sensitive author input/granted output. Never an agent-safe catalog projection."""

    schema_version: Literal["strange-physics.browser-world.v1"] = "strange-physics.browser-world.v1"
    space: ExperimentSpace
    noise_seed: BrowserSeed
    initial_law: BrowserLaw
    changed_law: BrowserLaw | None = None
    change_after: Annotated[int, Field(strict=True, ge=1, le=9_999)] | None = None

    def to_core(self) -> WorldDefinition:
        def law(value: BrowserLaw) -> LawSpec:
            return LawSpec(kind=value.kind, parameters=dict(value.parameters))

        return WorldDefinition(
            space=self.space,
            noise_seed=int(self.noise_seed),
            initial_law=law(self.initial_law),
            changed_law=None if self.changed_law is None else law(self.changed_law),
            change_after=self.change_after,
        )

    @classmethod
    def from_core(cls, value: WorldDefinition) -> Self:
        adapter: TypeAdapter[BrowserLaw] = TypeAdapter(BrowserLaw)
        return cls(
            space=value.space,
            noise_seed=str(value.noise_seed),
            initial_law=adapter.validate_python(value.initial_law.model_dump()),
            changed_law=None
            if value.changed_law is None
            else adapter.validate_python(value.changed_law.model_dump()),
            change_after=value.change_after,
        )

    @model_validator(mode="after")
    def core_schedule(self) -> Self:
        self.to_core()
        return self


class WorldPolicy(Message):
    """Configured bounds and current role policy; no production defaults or client control."""

    policy_id: Identifier
    max_definition_bytes: Annotated[int, Field(strict=True, ge=1, le=DEFINITION_BYTES)]
    max_metadata_bytes: Annotated[int, Field(strict=True, ge=1, le=METADATA_BYTES)]
    max_page_bytes: Annotated[int, Field(strict=True, ge=1, le=PAGE_BYTES)]
    max_page_items: Annotated[int, Field(strict=True, ge=1, le=128)]
    preview_ttl_seconds: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]
    receipt_retention_seconds: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]
    preview_reader_roles: Annotated[tuple[Role, ...], Field(min_length=1, max_length=3)]

    @model_validator(mode="after")
    def ordered_roles(self) -> Self:
        if tuple(sorted(set(self.preview_reader_roles))) != self.preview_reader_roles:
            raise ValueError("Preview reader roles must be unique and sorted")
        return self


class WorldBrowserAuthority(Message):
    """Current C2 human identity + workspace snapshot; shape is not complete authorization."""

    identity: HumanProductAuthority
    workspace: WorkspaceAuthority

    @model_validator(mode="after")
    def same_workspace(self) -> Self:
        if (
            self.identity.owner.grant.membership.workspace_id
            != self.workspace.workspace.workspace_id
        ):
            raise ValueError("World browser authority must name one current workspace")
        return self


class WorldActorAncestry(Message):
    """Historical issuer/author audit identity; never current recipient authorization."""

    workspace_id: Identifier
    principal_id: Identifier
    principal_generation: Count
    grant_incarnation: Count
    membership_revision: Count


class WorldVersionView(Message):
    """Agent-safe immutable version metadata; titles are author-supplied, not a blindness proof."""

    workspace_id: Identifier
    world_id: Identifier
    version_id: Identifier
    version_number: VersionNumber
    parent_version_id: Identifier | None
    title: WorldTitle
    space: ExperimentSpace
    created_at: Count

    @model_validator(mode="after")
    def parent_shape(self) -> Self:
        if (self.parent_version_id is None) != (self.version_number == 1):
            raise ValueError("Only version one has no parent")
        if self.parent_version_id == self.version_id:
            raise ValueError("A version cannot parent itself")
        return self


class WorldVersionRecord(Message):
    """Immutable private definition. This record is world-owned, never a fake run artifact."""

    view: WorldVersionView
    classification: WorldClassification
    definition: WorldDefinition
    definition_sha256: Digest
    author: WorldActorAncestry

    @model_validator(mode="after")
    def exact_definition(self) -> Self:
        # Validate the supported profile without adding absent parameter defaults.
        adapted = BrowserWorldDefinition.from_core(self.definition)
        if (
            message_sha256(adapted.to_core()) != message_sha256(self.definition)
            or self.definition_sha256 != message_sha256(self.definition)
            or message_sha256(self.view.space) != message_sha256(self.definition.space)
            or self.author.workspace_id != self.view.workspace_id
        ):
            raise ValueError(
                "Version must bind actual supported definition, space and author scope"
            )
        return self


class WorldHead(Message):
    workspace_id: Identifier
    world_id: Identifier
    version_id: Identifier
    revision: VersionNumber
    changed_at: Count


class WorldPage(Message):
    items: Annotated[tuple[WorldVersionView, ...], Field(max_length=128)]
    next_cursor: Identifier | None

    @model_validator(mode="after")
    def unique_items(self) -> Self:
        ids = tuple(item.version_id for item in self.items)
        if len(set(ids)) != len(ids) or len({x.workspace_id for x in self.items}) > 1:
            raise ValueError("World page must contain unique versions in one workspace")
        return self


class CreateWorldVersionRequest(Message):
    """First version uses null/zero; later versions use the exact displayed head."""

    title: WorldTitle
    definition: BrowserWorldDefinition
    expected_version_id: Identifier | None
    expected_head_revision: Annotated[int, Field(strict=True, ge=0, le=9_999)]

    @model_validator(mode="after")
    def expected_head(self) -> Self:
        if (self.expected_version_id is None) != (self.expected_head_revision == 0):
            raise ValueError("A new world has no prior head")
        return self


class WorldMutationScope(Message):
    workspace_id: Identifier
    principal_id: Identifier
    world_id: Identifier | None
    operation: Literal["create_version", "issue_preview", "renew_preview", "revoke_preview"]
    key: IdempotencyKey

    @model_validator(mode="after")
    def initial_creation_scope(self) -> Self:
        if self.world_id is None and self.operation != "create_version":
            raise ValueError("Only initial world creation can omit an allocated world ID")
        return self


class WorldVersionResult(Message):
    version: WorldVersionView
    head: WorldHead

    @model_validator(mode="after")
    def head_binding(self) -> Self:
        if (
            self.head.workspace_id,
            self.head.world_id,
            self.head.version_id,
            self.head.revision,
        ) != (
            self.version.workspace_id,
            self.version.world_id,
            self.version.version_id,
            self.version.version_number,
        ) or self.head.changed_at != self.version.created_at:
            raise ValueError("Version result must expose its exact head revision")
        return self


class WorldVersionCommit(Message):
    """Immutable atomic version/head/receipt proposal; no DB writes or authorization."""

    receipt_id: Identifier
    scope: WorldMutationScope
    request: CreateWorldVersionRequest
    request_sha256: Digest
    parent: WorldVersionRecord | None
    before: WorldHead | None
    version: WorldVersionRecord
    result: WorldVersionResult
    policy: WorldPolicy
    policy_sha256: Digest
    committed_at: Count
    receipt_expires_at: Count

    @model_validator(mode="after")
    def closure(self) -> Self:
        view = self.version.view
        if (
            self.scope.operation != "create_version"
            or self.policy_sha256 != message_sha256(self.policy)
            or self.receipt_expires_at != self.committed_at + self.policy.receipt_retention_seconds
            or (self.scope.workspace_id, self.scope.principal_id)
            != (view.workspace_id, self.version.author.principal_id)
            or self.scope.world_id != (None if view.version_number == 1 else view.world_id)
            or self.request_sha256 != message_sha256(self.request)
            or self.version.classification != "customer_authored"
            or message_sha256(self.version.definition)
            != message_sha256(self.request.definition.to_core())
            or view.title != self.request.title
            or view.created_at != self.committed_at
            or message_sha256(self.result.version) != message_sha256(view)
            or view.version_number != self.request.expected_head_revision + 1
            or view.parent_version_id != self.request.expected_version_id
        ):
            raise ValueError(
                "Version commit must bind actual request, author, definition and result"
            )
        if self.parent is None or self.before is None:
            if self.parent is not None or self.before is not None or view.version_number != 1:
                raise ValueError("First-version closure requires absence of both parent and head")
        else:
            previous = self.parent.view
            if (
                self.parent.classification != "customer_authored"
                or (previous.workspace_id, previous.world_id) != (view.workspace_id, view.world_id)
                or previous.version_id != view.parent_version_id
                or previous.version_number + 1 != view.version_number
                or previous.created_at > view.created_at
                or self.before
                != WorldHead(
                    workspace_id=previous.workspace_id,
                    world_id=previous.world_id,
                    version_id=previous.version_id,
                    revision=previous.version_number,
                    changed_at=previous.created_at,
                )
            ):
                raise ValueError("Version parent/head ancestry must be exact and chronological")
        return self


class WorldExpiredMutation(Message):
    """Private uniqueness tombstone for the retained namespace lifetime, not deletion authority."""

    scope: WorldMutationScope
    request_sha256: Digest
    receipt_id: Identifier
    allocated_world_id: Identifier
    policy_sha256: Digest
    retention_seconds: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)]
    committed_at: Count
    expires_at: Count

    @model_validator(mode="after")
    def original_scope_and_time(self) -> Self:
        if (
            self.scope.world_id not in (None, self.allocated_world_id)
            or self.expires_at != self.committed_at + self.retention_seconds
        ):
            raise ValueError("Expired key must preserve allocated world and original retention")
        return self


class WorldVersionLookup(Message):
    """Partial states stay representable for later recovery checks, never normalized to absence."""

    scope: WorldMutationScope
    receipt: WorldVersionCommit | None
    expired: WorldExpiredMutation | None
    target: WorldVersionRecord | None
    current_head: WorldHead | None
    current_commit: WorldVersionCommit | None

    @model_validator(mode="after")
    def version_operation(self) -> Self:
        if self.scope.operation != "create_version":
            raise ValueError("Version lookup requires a version mutation scope")
        return self


class WorldCatalogEligibility(Message):
    """Trusted current catalog decision for NEW run selection only, not an author preview grant."""

    workspace_id: Identifier
    world_id: Identifier
    version_id: Identifier
    definition_sha256: Digest
    space_sha256: Digest
    revision: Count
    eligible_for_new_runs: bool
    observed_at: Count


class WorldRunSelection(Message):
    """Retained exact selection; later catalog withdrawal does not rewrite an admitted run."""

    selection_id: Identifier
    version: WorldVersionRecord
    catalog: WorldCatalogEligibility
    admission: OriginalExecutionAdmission
    creation_request_sha256: Digest
    selected_at: Count

    @model_validator(mode="after")
    def exact_run(self) -> Self:
        view = self.version.view
        request: CreateRunRequest = self.admission.request
        result = self.admission.stored_request.operation.result
        if (
            result is None
            or not isinstance(result.value, RunView)
            or message_sha256(result.value) != message_sha256(self.admission.admitted_run)
            or (self.catalog.workspace_id, self.catalog.world_id, self.catalog.version_id)
            != (view.workspace_id, view.world_id, view.version_id)
            or self.catalog.definition_sha256 != self.version.definition_sha256
            or self.catalog.space_sha256 != message_sha256(view.space)
            or not self.catalog.eligible_for_new_runs
            or not view.created_at <= self.catalog.observed_at <= self.selected_at
            or view.created_at > self.selected_at
            or self.admission.ownership.workspace_id != view.workspace_id
            or self.selected_at != self.admission.ownership.created_at
            or request.world_version_id != view.version_id
            or request.experiment_budget != view.space.budget
            or message_sha256(self.admission.admitted_run.space) != message_sha256(view.space)
            or self.creation_request_sha256 != message_sha256(request)
        ):
            raise ValueError(
                "Run selection must bind actual immutable version, catalog and admission"
            )
        return self


WORLD_MODELS: tuple[type[Message], ...] = (
    BrowserSpringLaw,
    BrowserRadialLaw,
    BrowserVelocityLaw,
    BrowserWorldDefinition,
    WorldPolicy,
    WorldBrowserAuthority,
    WorldActorAncestry,
    WorldVersionView,
    WorldVersionRecord,
    WorldHead,
    WorldPage,
    CreateWorldVersionRequest,
    WorldMutationScope,
    WorldVersionResult,
    WorldVersionCommit,
    WorldExpiredMutation,
    WorldVersionLookup,
    WorldCatalogEligibility,
    WorldRunSelection,
)
