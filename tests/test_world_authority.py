"""Complete WORLD1 capability checks and unchanged shared C2/JSON seams."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from strange_physics.bounded_json import bounded_canonical, parse_bounded_json
from strange_physics.control_contracts import ContractViolation
from strange_physics.research_contracts import message_sha256
from strange_physics.serialization import canonical_json
from strange_physics.world_authority import authorize_world
from strange_physics.world_contracts import (
    CreateWorldVersionRequest,
    WorldBrowserAuthority,
    WorldCapability,
    WorldPolicy,
)

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts/world.examples.json").read_text()
)


def authority(**changes: Any) -> WorldBrowserAuthority:
    value = copy.deepcopy(FIXTURES["valid"]["WorldBrowserAuthority"])
    for path, replacement in changes.items():
        fields = path.split("__")
        target = value
        for field in fields[:-1]:
            target = target[field]
        target[fields[-1]] = replacement
    return WorldBrowserAuthority.model_validate_json(json.dumps(value))


def policy(**changes: Any) -> WorldPolicy:
    return WorldPolicy.model_validate_json(json.dumps(FIXTURES["valid"]["WorldPolicy"] | changes))


@pytest.mark.parametrize("role", ["owner", "researcher", "viewer"])
@pytest.mark.parametrize(
    ("capability", "mutation", "allowed"),
    [
        ("worlds:read", False, {"owner", "researcher", "viewer"}),
        ("worlds:write", True, {"owner", "researcher"}),
        ("worlds:preview-grants:manage", False, {"owner"}),
        ("worlds:preview-grants:manage", True, {"owner"}),
        ("worlds:preview", False, {"owner", "researcher", "viewer"}),
    ],
)
def test_world_role_matrix(role: str, capability: str, mutation: bool, allowed: set[str]) -> None:
    current = authority(
        identity__owner__grant__membership__role=role,
        workspace__active_owner_ids=["principal-1"] if role == "owner" else ["another-owner"],
    )
    if role in allowed:
        assert (
            authorize_world(
                current,
                policy(),
                capability=cast(WorldCapability, capability),
                workspace_id="workspace-1",
                mutation=mutation,
                now=1020,
            )
            == policy()
        )
    else:
        with pytest.raises(ContractViolation, match="forbidden"):
            authorize_world(
                current,
                policy(),
                capability=cast(WorldCapability, capability),
                workspace_id="workspace-1",
                mutation=mutation,
                now=1020,
            )


@pytest.mark.parametrize(
    ("changes", "code", "status"),
    [
        ({"identity__actor__context__has_bearer": True}, "ambiguous_credentials", 400),
        ({"identity__actor__context__origin": "https://evil.example"}, "forbidden", 403),
        ({"identity__actor__context__csrf_matches": False}, "forbidden", 403),
        ({"identity__actor__context__has_session_cookie": False}, "unauthenticated", 401),
        ({"identity__owner__principal__active": False}, "unauthenticated", 401),
        ({"identity__owner__principal__generation": 1}, "unauthenticated", 401),
        (
            {
                "identity__owner__grant__membership__active": False,
                "workspace__active_owner_ids": ["other-owner"],
            },
            "forbidden",
            403,
        ),
        ({"workspace__disabled_owner_ids": ["principal-1"]}, "forbidden", 403),
        ({"workspace__workspace__state": "quarantined"}, "forbidden", 403),
        (
            {
                "identity__owner__grant__membership__role": "viewer",
                "workspace__active_owner_ids": ["other-owner"],
            },
            "forbidden",
            403,
        ),
    ],
)
def test_invalid_current_authority_precedes_management_freshness(
    changes: dict[str, Any], code: str, status: int
) -> None:
    with pytest.raises(ContractViolation) as caught:
        authorize_world(
            authority(**changes),
            policy(),
            capability="worlds:preview-grants:manage",
            workspace_id="workspace-1",
            mutation=True,
            now=1110,
        )
    assert (caught.value.code, caught.value.status) == (code, status)


@pytest.mark.parametrize(
    ("capability", "mutation"),
    [
        ("worlds:read", False),
        ("worlds:write", True),
        ("worlds:preview-grants:manage", False),
        ("worlds:preview", False),
    ],
)
def test_ordinary_operations_do_not_require_recent_auth(capability: str, mutation: bool) -> None:
    authorize_world(
        authority(),
        policy(),
        capability=cast(WorldCapability, capability),
        workspace_id="workspace-1",
        mutation=mutation,
        now=1110,
    )


def test_management_mutation_requires_recent_auth_at_boundary() -> None:
    for now in (1109, 1110):
        if now == 1109:
            authorize_world(
                authority(),
                policy(),
                capability="worlds:preview-grants:manage",
                workspace_id="workspace-1",
                mutation=True,
                now=now,
            )
        else:
            with pytest.raises(ContractViolation, match="reauthentication_required"):
                authorize_world(
                    authority(),
                    policy(),
                    capability="worlds:preview-grants:manage",
                    workspace_id="workspace-1",
                    mutation=True,
                    now=now,
                )


def test_policy_unavailable_and_current_preview_role() -> None:
    with pytest.raises(ContractViolation) as missing:
        authorize_world(
            authority(),
            None,
            capability="worlds:read",
            workspace_id="workspace-1",
            mutation=False,
            now=1020,
        )
    assert (missing.value.code, missing.value.status) == ("policy_unavailable", 503)
    with pytest.raises(ContractViolation, match="forbidden"):
        authorize_world(
            authority(),
            policy(preview_reader_roles=["viewer"]),
            capability="worlds:preview",
            workspace_id="workspace-1",
            mutation=False,
            now=1020,
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"title":"a","title":"b"}',
        b'{"title":"a","\\u0074itle":"b"}',
        b'{"title":NaN}',
        b'{"title":Infinity}',
        b'{"title":1e999}',
        b"\xff",
        b"[[[[[0]]]]]",
        b'["a","b","c","d"]',
        b'{"title":"unterminated}',
    ],
)
def test_strict_json_rejects_before_model_validation(raw: bytes) -> None:
    with pytest.raises(ContractViolation, match="invalid_request"):
        parse_bounded_json(
            raw, CreateWorldVersionRequest, max_bytes=65536, max_depth=4, max_nodes=4
        )


def test_raw_bound_precedes_decoder(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("decoder must not run")

    monkeypatch.setattr("strange_physics.bounded_json.json.loads", forbidden)
    with pytest.raises(ContractViolation, match="invalid_request"):
        parse_bounded_json(
            b" " * 33, CreateWorldVersionRequest, max_bytes=32, max_depth=32, max_nodes=1000
        )


@pytest.mark.parametrize("zero", [0.0, -0.0])
def test_exact_canonical_identity_with_unicode_and_signed_zero(zero: float) -> None:
    data = copy.deepcopy(FIXTURES["valid"]["CreateWorldVersionRequest"])
    data["title"] = "World \u2603"
    data["definition"]["space"]["sampling"]["position_noise"] = zero
    raw = json.dumps(data, ensure_ascii=False).encode()
    value = parse_bounded_json(
        raw, CreateWorldVersionRequest, max_bytes=65536, max_depth=32, max_nodes=1000000
    )
    expected = canonical_json(value.model_dump(mode="json"))
    assert bounded_canonical(value, len(expected)) == (message_sha256(value), len(expected))
    with pytest.raises(ContractViolation, match="invalid_request"):
        bounded_canonical(value, len(expected) - 1)
