"""Bounded strict JSON and SCI-equivalent canonical identity utilities.

These helpers do not authorize access. Complete boundaries must check current
authority before invoking them on private material.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from strange_physics.contracts import Message
from strange_physics.control_contracts import ContractViolation


def bounded_canonical(value: Message, limit: int) -> tuple[str, int]:
    """Hash the exact SCI canonical encoding without accumulating encoded bytes."""
    digest = hashlib.sha256()
    size = 0
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    for chunk in encoder.iterencode(value.model_dump(mode="json")):
        size += len(chunk)  # ensure_ascii=True: each character is one UTF-8 byte.
        if size > limit:
            raise ContractViolation("invalid_request", 422)
        digest.update(chunk.encode("utf-8"))
    return digest.hexdigest(), size


def _structure(raw: bytes, *, max_depth: int, max_nodes: int) -> None:
    depth = nodes = 0
    quoted = escaped = scalar = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
            continue
        if byte == 34:
            quoted = True
            scalar = False
            nodes += 1
        elif byte in (91, 123):
            depth += 1
            nodes += 1
            scalar = False
        elif byte in (93, 125):
            depth -= 1
            scalar = False
        elif byte in (9, 10, 13, 32, 44, 58):
            scalar = False
        elif not scalar:
            nodes += 1
            scalar = True
        if depth < 0 or depth > max_depth or nodes > max_nodes:
            raise ContractViolation("invalid_request", 422)
    if depth != 0 or quoted:
        raise ContractViolation("invalid_request", 422)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite JSON number")
    return value


def _no_constant(text: str) -> None:
    raise ValueError("Nonstandard JSON constant")


def parse_bounded_json[M: Message](
    raw: bytes, model: type[M], *, max_bytes: int, max_depth: int, max_nodes: int
) -> M:
    """Reject byte/nesting/node excess before decoding; reject duplicate keys."""
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= max_bytes:
        raise ContractViolation("invalid_request", 422)
    _structure(raw, max_depth=max_depth, max_nodes=max_nodes)
    try:
        # Discard the semantic-check parse before JSON-mode typed validation.
        # JSON mode preserves the existing strict tuple/array contract.
        json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_float=_finite_float,
            parse_constant=_no_constant,
        )
        return model.model_validate_json(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ContractViolation("invalid_request", 422) from None
