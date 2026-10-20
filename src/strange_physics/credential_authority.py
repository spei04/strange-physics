"""Current principal/grant generations supplied by trusted identity producers.

These wrappers add revocation ancestry without changing the accepted session or
membership messages. Parsing a wrapper does not establish its currency.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from strange_physics.contracts import Identifier, Message
from strange_physics.control_contracts import Membership
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
