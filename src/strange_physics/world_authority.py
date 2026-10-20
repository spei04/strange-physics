"""Complete browser-world capabilities over the unchanged current C2 identity seams.

Trusted current projections must be fetched/rechecked under the producer's
transaction. No function here verifies a cookie, acquires a lock or grants a
service/run credential a new scope.
"""

from __future__ import annotations

from strange_physics.control_contracts import ContractViolation
from strange_physics.product_authority import validate_human_product_identity
from strange_physics.research_contracts import message_sha256
from strange_physics.session_contracts import require_policy
from strange_physics.workspace_contracts import validate_product_workspace
from strange_physics.world_contracts import (
    WorldActorAncestry,
    WorldBrowserAuthority,
    WorldCapability,
    WorldPolicy,
)


def authorize_world(
    authority: WorldBrowserAuthority,
    policy: WorldPolicy | None,
    *,
    capability: WorldCapability,
    workspace_id: str,
    mutation: bool,
    now: int,
) -> WorldPolicy:
    """Mandatory complete capability guard; resource-specific grant checks follow."""
    member = validate_human_product_identity(authority.identity, mutation=mutation, now=now)
    if member.workspace_id != workspace_id:
        raise ContractViolation("not_found", 404)
    if not member.active:
        raise ContractViolation("forbidden", 403)
    validate_product_workspace(authority.workspace, workspace_id, member)
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    if (
        capability
        not in {"worlds:read", "worlds:write", "worlds:preview", "worlds:preview-grants:manage"}
        or (capability == "worlds:write" and member.role not in {"owner", "researcher"})
        or (capability == "worlds:preview-grants:manage" and member.role != "owner")
        or (capability == "worlds:preview" and member.role not in policy.preview_reader_roles)
        or (mutation and capability not in {"worlds:write", "worlds:preview-grants:manage"})
        or (capability == "worlds:write" and not mutation)
    ):
        raise ContractViolation("forbidden", 403)
    if mutation and capability == "worlds:preview-grants:manage":
        configured = require_policy(authority.identity.policy)
        if (
            now - authority.identity.actor.session.authenticated_at
            >= configured.recent_auth_seconds
        ):
            raise ContractViolation("reauthentication_required", 401)
    return policy


def world_actor(authority: WorldBrowserAuthority) -> WorldActorAncestry:
    """Pure audit projection, not an authorization entrypoint."""
    owner = authority.identity.owner
    member = owner.grant.membership
    return WorldActorAncestry(
        workspace_id=member.workspace_id,
        principal_id=owner.principal.principal_id,
        principal_generation=owner.principal.generation,
        grant_incarnation=owner.grant.incarnation,
        membership_revision=member.revision,
    )


def world_authority_sha256(authority: WorldBrowserAuthority) -> str:
    """Private producer CAS identity; includes current session and complete workspace snapshot."""
    return message_sha256(authority)
