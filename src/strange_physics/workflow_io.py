"""Bounded owner-private local artifacts, with completion written last."""

from __future__ import annotations

import hashlib
import os
import stat
from itertools import islice
from pathlib import Path

from pydantic import ValidationError

from strange_physics.contracts import Message
from strange_physics.workflow_contracts import ArtifactFile, FailureCode, Stage, StageCompletion

MAX_JSON_BYTES = 64 * 1024 * 1024


class WorkflowError(ValueError):
    """Only this bounded code is safe to display; never retain private parser payloads."""

    def __init__(self, code: FailureCode) -> None:
        self.code = code
        super().__init__(code)


def safe_path(path: Path) -> Path:
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise WorkflowError("unsafe_path")
    for parent in (absolute, *absolute.parents):
        if parent.is_symlink():
            raise WorkflowError("unsafe_path")
    return absolute


def private_stat(info: os.stat_result, *, directory: bool = False) -> None:
    correct_type = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not correct_type or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise WorkflowError("unsafe_path")


def read_bytes(path: Path, *, limit: int = MAX_JSON_BYTES) -> bytes:
    path = safe_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        private_stat(before)
        if before.st_size > limit:
            raise WorkflowError("input_limit")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            data = os.read(fd, min(1024 * 1024, remaining))
            if not data:
                break
            chunks.append(data)
            remaining -= len(data)
        after = os.fstat(fd)
        if remaining == 0:
            raise WorkflowError("input_limit")
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise WorkflowError("artifact_mismatch")
        return b"".join(chunks)
    finally:
        os.close(fd)


def read_message[T: Message](path: Path, model: type[T], *, limit: int = MAX_JSON_BYTES) -> T:
    try:
        return model.model_validate_json(read_bytes(path, limit=limit))
    except ValidationError:
        raise WorkflowError("invalid_input") from None


def write_stage(
    path: Path,
    stage: Stage,
    files: dict[str, Message],
    input_hashes: tuple[str, ...],
    elapsed_ms: int,
) -> StageCompletion:
    """Create a new private directory. An interrupted write retains no completion."""
    path = safe_path(path)
    if not path.parent.is_dir():
        raise WorkflowError("unsafe_path")
    if not 1 <= len(files) <= 8:
        raise WorkflowError("input_limit")
    encoded: dict[str, bytes] = {}
    total = 0
    for name, message in files.items():
        data = (message.model_dump_json() + "\n").encode()
        total += len(data)
        if total > MAX_JSON_BYTES:
            raise WorkflowError("input_limit")
        ArtifactFile(name=name, bytes=len(data), bytes_sha256=hashlib.sha256(data).hexdigest())
        encoded[name] = data
    completion = StageCompletion(
        stage=stage,
        files=tuple(
            ArtifactFile(name=name, bytes=len(data), bytes_sha256=hashlib.sha256(data).hexdigest())
            for name, data in encoded.items()
        ),
        input_message_sha256=input_hashes,
        elapsed_ms=elapsed_ms,
    )
    # mkdir is exclusive even for existing empty directories and dangling links.
    path.mkdir(mode=0o700)
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    published = False
    try:
        private_stat(os.fstat(directory), directory=True)
        for name, data in (
            *encoded.items(),
            (".completion-pending", (completion.model_dump_json() + "\n").encode()),
        ):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
            )
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
        # The complete manifest appears atomically only after every payload and
        # its own bytes are flushed. link is exclusive; it cannot overwrite.
        os.link(
            ".completion-pending",
            "completion.json",
            src_dir_fd=directory,
            dst_dir_fd=directory,
            follow_symlinks=False,
        )
        published = True
        os.unlink(".completion-pending", dir_fd=directory)
        os.fsync(directory)
    except BaseException:
        if published:
            os.unlink("completion.json", dir_fd=directory)
        raise
    finally:
        os.close(directory)
    return completion


def read_stage(path: Path, stage: Stage) -> dict[str, bytes]:
    """Validate every raw file before parsing any stage payload."""
    path = safe_path(path)
    private_stat(path.stat(), directory=True)
    completion = read_message(path / "completion.json", StageCompletion, limit=16 * 1024)
    if completion.stage != stage:
        raise WorkflowError("artifact_mismatch")
    if set(p.name for p in islice(path.iterdir(), 10)) != {
        "completion.json",
        *(f.name for f in completion.files),
    }:
        raise WorkflowError("incomplete_artifacts")
    result: dict[str, bytes] = {}
    for file in completion.files:
        data = read_bytes(path / file.name, limit=file.bytes)
        if len(data) != file.bytes or hashlib.sha256(data).hexdigest() != file.bytes_sha256:
            raise WorkflowError("artifact_mismatch")
        result[file.name] = data
    return result


def stage_message[T: Message](files: dict[str, bytes], name: str, model: type[T]) -> T:
    try:
        return model.model_validate_json(files[name])
    except (KeyError, ValidationError):
        raise WorkflowError("invalid_input") from None
