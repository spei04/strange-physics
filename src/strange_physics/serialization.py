"""Canonical JSON and content identity for local reproducibility."""

from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

from strange_physics import __version__
from strange_physics.laws import LawRegistry


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def engine_fingerprint(registry: LawRegistry) -> str:
    digest = hashlib.sha256()
    identity = {
        "package": __version__,
        "python": platform.python_version(),
        "numpy": version("numpy"),
        "pydantic": version("pydantic"),
        "plugins": registry.versions,
    }
    digest.update(canonical_json(identity).encode())
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
