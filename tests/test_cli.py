from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from strange_physics import cli
from strange_physics.cli import main
from strange_physics.contracts import ObservationBundle
from strange_physics.session import LocalSession


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


def test_cli_inspect_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "observations.fifo"
    os.mkfifo(fifo, 0o600)
    result = subprocess.run(
        [sys.executable, "-m", "strange_physics.cli", "inspect", str(fifo)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "observation bundle must be a regular file" in result.stderr


@pytest.mark.parametrize("kind", ["device", "symlink"])
def test_cli_inspect_rejects_nonregular_before_parsing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    class ForbiddenParser:
        @staticmethod
        def model_validate_json(data: bytes) -> ObservationBundle:
            raise AssertionError("nonregular input reached the parser")

    monkeypatch.setattr(cli, "ObservationBundle", ForbiddenParser)
    if kind == "device":
        target = Path(os.devnull)
    else:
        source = tmp_path / "source.json"
        source.write_text("private input")
        target = tmp_path / "observations.json"
        target.symlink_to(source)
    assert main(["inspect", str(target)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    assert "private input" not in captured.err


@pytest.mark.parametrize("grow_after_stat", [False, True])
def test_cli_inspect_keeps_the_read_bounded(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    grow_after_stat: bool,
) -> None:
    target = tmp_path / "observations.json"
    target.write_bytes(b"12345678" if grow_after_stat else b"123456789")
    monkeypatch.setattr(cli, "_INSPECTION_LIMIT", 8)
    if grow_after_stat:
        original_fstat = os.fstat

        def growing_file(fd: int) -> os.stat_result:
            before = original_fstat(fd)
            with target.open("ab") as stream:
                stream.write(b"9")
            return before

        monkeypatch.setattr(os, "fstat", growing_file)
    assert main(["inspect", str(target)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "observation bundle exceeds the 64 MiB local inspection limit" in captured.err


def test_cli_resume_rejects_malformed_sqlite_safely(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    journal = tmp_path / "session.sqlite"
    original = b"private malformed journal content" * 8
    journal.write_bytes(original)
    assert main(["resume", "--directory", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: invalid SQLite run journal\n"
    assert journal.read_bytes() == original


def test_cli_resume_does_not_swallow_unrelated_database_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = sqlite3.OperationalError("unexpected database error")
    error.sqlite_errorcode = sqlite3.SQLITE_ERROR

    def fail_open(path: Path) -> LocalSession:
        raise error

    monkeypatch.setattr(LocalSession, "open", fail_open)
    with pytest.raises(sqlite3.OperationalError) as caught:
        main(["resume", "--directory", str(tmp_path)])
    assert caught.value is error
