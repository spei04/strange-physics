"""Current principal/grant generations supplied by trusted identity producers.

These wrappers add revocation ancestry without changing the accepted session or
membership messages. Parsing a wrapper does not establish its currency.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import ContractViolation, Membership
from strange_physics.research_contracts import Count


class PrincipalAuthority(Message):
    kind: Literal["human", "service"]
    principal_id: Identifier
    active: bool
    generation: Count


class GrantAuthority(Message):
    """Incarnation advances on remove/regrant; membership revision is ordinary CAS."""

    membership: Membership
    incarnation: Count


class CredentialOwner(Message):
    principal: PrincipalAuthority
    grant: GrantAuthority

    @model_validator(mode="after")
    def same_principal(self) -> Self:
        if self.principal.principal_id != self.grant.membership.principal_id:
            raise ValueError("Owner and current grant must name the same principal")
        return self


def validate_principal_state(before: PrincipalAuthority, after: PrincipalAuthority) -> None:
    """Producer transition: either active-state change consumes a new generation."""
    changed = before.active != after.active
    if (
        before.kind != after.kind
        or before.principal_id != after.principal_id
        or after.generation != before.generation + int(changed)
    ):
        raise ContractViolation("incompatible_state", 409)


def validate_grant_update(before: GrantAuthority, after: GrantAuthority) -> None:
    """Removal and regrant change incarnation; ordinary role changes only change CAS."""
    old, new = before.membership, after.membership
    changed = old != new
    if (
        (old.workspace_id, old.principal_id) != (new.workspace_id, new.principal_id)
        or new.revision != old.revision + int(changed)
        or after.incarnation != before.incarnation + int(old.active != new.active)
    ):
        raise ContractViolation("incompatible_state", 409)
