from pathlib import Path

import pytest

from examples.custom_extension import investigate


def test_external_agent_and_law_work_without_core_modifications(tmp_path: Path) -> None:
    result = investigate(tmp_path)
    assert len(result.records) == 8
    assert all(record.status == "completed" for record in result.records)
    for record in result.records[4:]:
        assert record.trajectory is not None
        mass = record.experiment.particles[0].mass
        # After the change, a constant force of -0.2 accelerates a probe from rest for 2 s.
        assert record.trajectory.frames[-1].positions[0][0] == pytest.approx(-0.4 / mass)
    assert investigate(tmp_path) == result
