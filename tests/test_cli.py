from __future__ import annotations

import json
from pathlib import Path

import pytest

from strange_physics.cli import main


def test_cli_create_resume_and_inspect(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    directory = str(tmp_path / "investigation")
    assert (
        main(
            ["investigate", "--directory", directory, "--budget", "6", "--max-new-experiments", "2"]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["experiments"] == 2
    assert main(["resume", "--directory", directory]) == 0
    assert json.loads(capsys.readouterr().out)["experiments"] == 6
    assert main(["inspect", str(Path(directory) / "observations.json")]) == 0
    assert json.loads(capsys.readouterr().out)["failed"] == 0
    assert main(["investigate", "--directory", directory, "--budget", "6"]) == 2
    assert "File exists" in capsys.readouterr().err


def test_cli_rejects_invalid_parameters_before_creating_a_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["investigate", "--directory", str(tmp_path / "invalid"), "--particles", "9"]) == 2
    assert "eight" in capsys.readouterr().err
    assert not (tmp_path / "invalid").exists()


def test_public_schema_does_not_include_hidden_world_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["schema", "observations"]) == 0
    schema = capsys.readouterr().out
    assert json.loads(schema)["title"] == "ObservationBundle"
    assert "initial_law" not in schema
    assert "change_after" not in schema
