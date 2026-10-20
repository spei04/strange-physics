"""Current viewer authority; no cookie verification, DB lookup or hosted transport.

Every caller supplies independently verified current transactional projections.
The context and returned policy are not reusable authorization capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass

from strange_physics.control_contracts import (
    ContractViolation,
    Membership,
    RunView,
    VerifiedCredential,
)
from strange_physics.research_contracts import message_sha256
from strange_physics.run_credential_contracts import ProductAuthority
from strange_physics.web_contracts import MAX_SAFE, StreamNamespace, WebPolicy
from strange_physics.workspace_contracts import WorkspaceAuthority, authorize_product


@dataclass(frozen=True)
class ViewerContext:
    """Private current input; transport presence comes from the trusted HTTP adapter."""

    authority: ProductAuthority
    credential: VerifiedCredential
    membership: Membership
    workspace: WorkspaceAuthority
    run: RunView | None
    has_session_cookie: bool
    has_bearer: bool


def authorize_viewer(
    context: ViewerContext, policy: WebPolicy | None, namespace: StreamNamespace, *, now: int
) -> WebPolicy:
    """Complete read gate before any cursor, catalog, bytes or retained state inspection."""
    if type(context.has_session_cookie) is not bool or type(context.has_bearer) is not bool:
        raise ContractViolation("invalid_request", 400)
    if context.has_session_cookie and context.has_bearer:
        raise ContractViolation("ambiguous_credentials", 400)
    if context.authority.kind == "user":
        browser = context.authority.actor.context
        if (
            not context.has_session_cookie
            or context.has_bearer
            or browser.has_session_cookie != context.has_session_cookie
            or browser.has_bearer != context.has_bearer
        ):
            raise ContractViolation("unauthenticated", 401)
    elif context.authority.kind == "service":
        if context.has_session_cookie or not context.has_bearer:
            raise ContractViolation("unauthenticated", 401)
    else:
        raise ContractViolation("unauthenticated", 401)
    authorize_product(
        context.workspace,
        context.credential,
        context.membership,
        authority=context.authority,
        permission="runs:read",
        workspace_id=namespace.workspace_id,
        run_id=namespace.run_id,
        now=now,
    )
    if policy is None:
        raise ContractViolation("policy_unavailable", 503)
    if type(now) is not int or not 0 <= now <= MAX_SAFE:
        raise ContractViolation("invalid_request", 422)
    if context.run is None or (context.run.workspace_id, context.run.run_id) != (
        namespace.workspace_id,
        namespace.run_id,
    ):
        raise ContractViolation("not_found", 404)
    return policy


def check_run_capture(captured: RunView, current: RunView) -> None:
    """Incomplete historical join: immutable space, monotonic progress, exact equal revision."""
    if (
        (captured.workspace_id, captured.run_id) != (current.workspace_id, current.run_id)
        or message_sha256(captured.space) != message_sha256(current.space)
        or current.revision < captured.revision
        or current.experiments_accepted < captured.experiments_accepted
        or current.budget_remaining > captured.budget_remaining
        or (
            current.revision == captured.revision
            and message_sha256(current) != message_sha256(captured)
        )
    ):
        raise ContractViolation("recovery_required", 409)
