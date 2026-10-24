"""Prepare and verify owned copied Python executables for Linux CI only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any

LIMIT = 64 * 1024**2
PROBE = (
    "import json,sys,sysconfig;"
    "print(json.dumps(dict(executable=sys.executable,prefix=sys.prefix,"
    "version=sys.version,site=sysconfig.get_paths()['purelib'])))"
)


def inspect_file(path: Path, *, owned: bool) -> dict[str, Any]:
    """Allow a trusted setup-python source mode; copied/installed files stay strict."""
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("CI installation path contains a symlink")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        info: dict[str, Any] = {
            "path": str(path),
            "uid": before.st_uid,
            "nlink": before.st_nlink,
            "mode": oct(stat.S_IMODE(before.st_mode)),
            "bytes": before.st_size,
        }
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid not in ({os.getuid()} if owned else {0, os.getuid()})
            or before.st_nlink != 1
            or before.st_size > LIMIT
            or (owned and before.st_mode & 0o022)
        ):
            raise ValueError("CI installation stat rejected: " + json.dumps(info, sort_keys=True))
        digest = hashlib.sha256()
        count = 0
        while chunk := os.read(fd, 1024 * 1024):
            count += len(chunk)
            if count > LIMIT:
                raise ValueError("CI installation file grew beyond its bound")
            digest.update(chunk)
        after = os.fstat(fd)
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ) or count != before.st_size:
            raise ValueError("CI installation file changed during readback")
        info["sha256"] = digest.hexdigest()
        return info
    finally:
        os.close(fd)


def copied_executable(root: Path, expected_sha256: str) -> dict[str, Any]:
    path = root / "bin/python"
    info = inspect_file(path, owned=True)
    if not path.resolve().is_relative_to(root) or info["sha256"] != expected_sha256:
        raise ValueError("CI copied interpreter identity differs from setup-python")
    return info


def check(root: Path, record: Path) -> dict[str, Any]:
    inspect_file(record, owned=True)
    expected = json.loads(record.read_text())
    copied = copied_executable(root, expected["source"]["sha256"])
    result = subprocess.run(
        [str(root / "bin/python"), "-I", "-B", "-c", PROBE],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    actual = json.loads(result.stdout)
    if (
        Path(actual["executable"]).resolve() != root / "bin/python"
        or Path(actual["prefix"]).resolve() != root
        or actual["version"] != expected["version"]
    ):
        raise ValueError("CI executed interpreter escaped or changed its copied environment")
    site = Path(actual["site"])
    if not site.is_relative_to(root):
        raise ValueError("CI installed package directory escaped its environment")
    count = 0
    for path in site.rglob("*"):
        if "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise ValueError("CI installed dependency is a symlink")
        if path.is_file():
            inspect_file(path, owned=True)
            count += 1
    return {"source": expected["source"], "copied": copied, "installed_files": count}


def create(root: Path, record: Path) -> dict[str, Any]:
    if root.exists() or root.is_symlink() or record.exists() or record.is_symlink():
        raise ValueError("CI bootstrap requires fresh environment and record paths")
    source_path = Path(sys.executable).resolve()
    source = inspect_file(source_path, owned=False)
    venv.EnvBuilder(with_pip=False, symlinks=False).create(root)
    copied_executable(root, source["sha256"])
    if inspect_file(source_path, owned=False) != source:
        raise ValueError("Shared source interpreter changed during copying")
    with record.open("x") as stream:
        os.chmod(record, 0o600)
        json.dump({"source": source, "version": sys.version}, stream, sort_keys=True)
        stream.write("\n")
    return check(root, record)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "check"))
    parser.add_argument("environment", type=Path)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("This bootstrap is restricted to the Linux hosted CI profile")
    root, record = args.environment.absolute(), args.record.absolute()
    result = create(root, record) if args.action == "create" else check(root, record)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
