"""Generate only the additive endpoint-belief schema from its strict messages."""

from __future__ import annotations

import json
from pathlib import Path

from strange_physics.native_endpoint_belief_contracts import native_endpoint_belief_json_schema


def main() -> None:
    destination = (
        Path(__file__).resolve().parents[1] / "contracts/native-endpoint-belief.schema.json"
    )
    content = json.dumps(native_endpoint_belief_json_schema(), indent=2, sort_keys=True) + "\n"
    if len(content.encode()) > 128 * 1024:
        raise ValueError("Endpoint schema exceeds the declared generation bound")
    destination.write_text(content)


if __name__ == "__main__":
    main()
