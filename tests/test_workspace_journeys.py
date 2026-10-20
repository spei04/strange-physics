from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY: dict[str, Any] = json.loads(
    (ROOT / "docs/workspace-journeys.inventory.json").read_text()
)
DOCUMENT = (ROOT / "docs/WORKSPACE_JOURNEYS.md").read_text()


def test_journey_run_states_match_actual_control_contract() -> None:
    source = INVENTORY["run_state_source"]
    node: Any = json.loads((ROOT / source["path"]).read_text())
    for part in source["pointer"].lstrip("/").split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    expected = set(node)
    assert len(INVENTORY["run_states"]) == len(expected)
    assert set(INVENTORY["run_states"]) == expected
    covered: set[str] = set()
    for fixture in INVENTORY["fixtures"]:
        states = set(fixture["run_states"])
        assert states <= expected, fixture["id"]
        covered.update(states)
    assert covered == expected


def test_journeys_reference_real_producers_and_documented_scenarios() -> None:
    backlog = json.loads((ROOT / "docs/execution-backlog.json").read_text())
    task_ids = {task["id"] for task in backlog["tasks"]}
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', DOCUMENT))
    journeys = {journey["id"]: journey for journey in INVENTORY["journeys"]}
    assert len(journeys) == len(INVENTORY["journeys"])
    assert INVENTORY["task"] in task_ids
    assert set(INVENTORY["integration_evidence_tasks"]) <= task_ids
    for journey in journeys.values():
        assert journey["anchor"] in anchors
        assert journey["producer_tasks"]
        assert set(journey["producer_tasks"]) <= task_ids
    seen: set[str] = set()
    covered: set[str] = set()
    for fixture in INVENTORY["fixtures"]:
        assert fixture["id"] not in seen
        seen.add(fixture["id"])
        assert f"| {fixture['id']} |" in DOCUMENT
        assert fixture["journey"] in journeys
        covered.add(fixture["journey"])
        assert fixture["producer_tasks"]
        assert set(fixture["producer_tasks"]) <= task_ids
        assert set(fixture["producer_tasks"]) <= set(journeys[fixture["journey"]]["producer_tasks"])
    assert covered == set(journeys)


def test_accessibility_checks_and_shared_states_have_fixture_links() -> None:
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', DOCUMENT))
    checks = set(INVENTORY["accessibility_checks"])
    states = set(INVENTORY["ui_states"])
    assert checks <= anchors
    covered_checks: set[str] = set()
    covered_states: set[str] = set()
    for fixture in INVENTORY["fixtures"]:
        assigned_checks = set(fixture["accessibility_checks"])
        assigned_states = set(fixture["ui_states"])
        assert assigned_checks and assigned_checks <= checks, fixture["id"]
        assert assigned_states and assigned_states <= states, fixture["id"]
        covered_checks.update(assigned_checks)
        covered_states.update(assigned_states)
    assert covered_checks == checks
    assert covered_states == states
