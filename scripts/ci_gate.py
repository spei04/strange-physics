"""Aggregate required CI results; skipped, cancelled and unknown results fail closed."""

from __future__ import annotations

import json
import os
from typing import Any

REQUIRED_JOBS = frozenset({"checks", "security"})


def require_success(needs: Any) -> None:
    if not isinstance(needs, dict) or set(needs) != REQUIRED_JOBS:
        raise ValueError("CI gate requires exactly the configured required jobs")
    for name in sorted(REQUIRED_JOBS):
        result = needs[name]
        if not isinstance(result, dict) or result.get("result") != "success":
            raise ValueError(f"Required job {name} did not succeed")


if __name__ == "__main__":
    require_success(json.loads(os.environ["CI_NEEDS"]))
    print("All required CI jobs succeeded.")
