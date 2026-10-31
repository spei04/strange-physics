"""Fixed benign leader-exit handshake; never invokes capture or science."""

from __future__ import annotations

import hashlib
import math
import os
import select
import stat
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import d1_owned_capture as owned
from scripts.grid_q1_supervisor import (
    CommandFailure,
    Fault,
    Plan,
    Snapshot,
    Supervisor,
    confirms_empty_unit_cleanup,
    private_bytes,
)


@dataclass(frozen=True, kw_only=True)
class DescendantPlan(Plan):
    interpreter: Path
    token: str
    started: float

    def __post_init__(self) -> None:
        super().__post_init__()
        owned._digest(self.token)
        if type(self.started) is not float or not math.isfinite(self.started) or self.started < 0:
            raise ValueError("Original finite benign start required")
        if any(getattr(self, key) != value for key, value in owned.PROFILE.items()):
            raise ValueError("Fixed capture profile required for benign qualification")
        if not self.interpreter.is_absolute():
            raise ValueError("Protected absolute interpreter required")

    @property
    def unit(self) -> str:
        return (
            "d1-descendant-"
            + hashlib.sha256(f"{self.root}:{self.admission_sha256}".encode()).hexdigest()[:24]
            + ".service"
        )

    @property
    def request(self) -> bytes:
        return owned.encoded(
            {
                "schema": "d1-descendant-request-v1",
                "unit": self.unit,
                "token": self.token,
                "deadline": self.started + 30.0,
            }
        )

    @property
    def request_sha256(self) -> str:
        return hashlib.sha256(self.request).hexdigest()

    @property
    def argv(self) -> list[str]:
        return [
            str(self.interpreter),
            "-I",
            "-B",
            str(Path(__file__).resolve()),
            "worker",
            str(self.root / "descendant-request.json"),
            self.request_sha256,
        ]


class Handshake(Protocol):
    def prepare(self, plan: DescendantPlan) -> None: ...
    def ready(self) -> dict[str, object]: ...
    def done(self) -> dict[str, object]: ...
    def release(self, token: str) -> None: ...


class PipeHandshake:
    def __init__(self, root: Path) -> None:
        self.root = root

    def prepare(self, plan: DescendantPlan) -> None:
        if self.root != plan.root:
            raise ValueError("Benign handshake root differs")
        # Actual source bytes are checked; protected custody remains external.
        with Path(__file__).open("rb") as stream:
            source = stream.read(131073)
        if len(source) > 131072 or hashlib.sha256(source).hexdigest() != plan.controller_sha256:
            raise ValueError("Benign worker source differs")
        plan.control_root.mkdir(mode=0o700)
        os.mkfifo(self.root / "release.fifo", 0o600)
        owned.write_request(self.root / "descendant-request.json", plan.request)

    def ready(self) -> dict[str, object]:
        return owned.decoded(private_bytes(self.root / "descendant-ready.json", 4096), 4096)

    def done(self) -> dict[str, object]:
        return owned.decoded(private_bytes(self.root / "descendant-done.json", 4096), 4096)

    def release(self, token: str) -> None:
        fd = os.open(self.root / "release.fifo", os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        primary: BaseException | None = None
        supplemental: list[Fault] = []
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISFIFO(info.st_mode)
                or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise ValueError("Owned private FIFO required")
            raw = (owned._digest(token) + "\n").encode("ascii")
            if os.write(fd, raw) != len(raw):
                raise OSError("Unknown/partial release write; no retry")
        except BaseException as release_error:
            primary = release_error
        try:
            os.close(fd)  # Exactly one attempt, including lost close confirmation.
        except BaseException as close_error:
            if primary is None:
                primary = close_error
            else:
                supplemental.append(Fault.capture("release_close", close_error))
        if primary is not None:
            if supplemental:
                raise CommandFailure(primary, tuple(supplemental)) from None
            raise primary


def watch_descendant(
    plan: DescendantPlan,
    manager: Supervisor,
    files: owned.ReceiptIO,
    handshake: Handshake,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Only accepts leader-exited/populated BEFORE releasing the owned descendant.

    The exclusive intent precedes request/FIFO preparation and one submission.
    This is a separate benign unit, never a GRID or capture report producer.
    """
    started = plan.started
    token = plan.token
    deadline = started + 60.0
    first: Fault | None = None
    supplemental: list[Fault] = []
    invocation: str | None = None
    group: str | None = None
    latest: Snapshot | None = None
    claimed = submitted = witnessed = released = closed = stopped = False

    def remaining() -> float:
        value = min(5.0, deadline - clock())
        if value <= 0:
            raise TimeoutError("Benign handshake deadline")
        return value

    def fault(stage: str, error: BaseException) -> None:
        nonlocal first
        original = error.primary if isinstance(error, CommandFailure) else error
        value = Fault.capture(stage, original)
        if first is None:
            first = value
        elif len(supplemental) < 8:
            supplemental.append(value)
        if isinstance(error, CommandFailure):
            supplemental.extend(error.supplemental[: max(0, 8 - len(supplemental))])

    def bind(value: Snapshot) -> None:
        nonlocal invocation, group, latest, closed
        value.bind(plan, invocation)
        if group is None:
            if not value.cgroup or value.populated is None:
                raise ValueError("Actual benign group observation required")
            group = value.cgroup
        elif value.cgroup and value.cgroup != group:
            raise ValueError("Benign group changed")
        if latest is not None and value.cpu_ns < latest.cpu_ns:
            raise ValueError("Benign CPU decreased")
        invocation, latest = value.invocation, value
        closed = value.terminal and value.populated is not True

    try:
        owned._digest(token)
        if files.root != plan.root:
            raise ValueError("Benign receipt root differs")
        files.write(
            "descendant-intent.json",
            {
                "unit": plan.unit,
                "started": started,
                "deadline": deadline,
                "request_sha256": plan.request_sha256,
                "no_retry": True,
            },
        )
        claimed = True
        if not started <= clock() < started + 30.0:
            raise TimeoutError("Benign preparation missed original worker window")
        handshake.prepare(plan)
        if manager.snapshot(plan, remaining()).properties.get("LoadState") != "not-found":
            raise ValueError("Benign unit exists")
        submitted = True
        manager.submit(plan, remaining())
        for _ in range(10):
            bind(manager.snapshot(plan, remaining()))
            assert latest is not None
            leader_exit = latest.properties.get("ExecMainExitTimestampMonotonic", "0")
            if (
                not released
                and leader_exit.isdecimal()
                and int(leader_exit) > 0
                and latest.populated is True
            ):
                if (
                    latest.properties.get("ExecMainCode") != "1"
                    or latest.properties.get("ExecMainStatus") != "0"
                ):
                    raise ValueError("Benign leader did not exit successfully")
                ready = handshake.ready()
                if ready != {
                    "schema": "d1-descendant-ready-v1",
                    "unit": plan.unit,
                    "invocation_id": invocation,
                    "cgroup": group,
                    "token": token,
                }:
                    raise ValueError("Ready bytes do not bind the observed populated group")
                files.write(
                    "descendant-populated.json", {"snapshot": asdict(latest), "ready": ready}
                )
                witnessed = True
                handshake.release(token)
                released = True
            if closed:
                if not witnessed or not released:
                    raise ValueError("Empty/leader-only fixture cannot qualify descendants")
                if handshake.done() != {
                    "schema": "d1-descendant-done-v1",
                    "unit": plan.unit,
                    "invocation_id": invocation,
                    "cgroup": group,
                    "token": token,
                    "exit_code": 0,
                    "first_fault": None,
                    "supplemental": [],
                }:
                    raise ValueError("Descendant completion/close acknowledgement differs")
                break
            pause(min(1.0, remaining()))
        if not closed:
            raise TimeoutError("Benign descendant did not close after release")
    except BaseException as operation_error:
        fault("benign", operation_error)
    if not claimed:
        return {
            "status": "incomplete",
            "first_fault": None if first is None else asdict(first),
            "no_retry": True,
        }
    if submitted and not closed:
        try:
            bind(manager.snapshot(plan, remaining()))
            if not closed:
                assert invocation is not None
                manager.signal(plan, invocation, "SIGKILL", remaining())
                for _ in range(3):
                    bind(manager.snapshot(plan, remaining()))
                    if closed:
                        break
                    pause(min(1.0, remaining()))
        except BaseException as cleanup_error:
            fault("benign_cleanup", cleanup_error)
    terminal_saved = False
    try:
        remaining()
        files.write(
            "descendant-terminal.json",
            {
                "unit": plan.unit,
                "snapshot": None if latest is None else asdict(latest),
                "closed": closed,
                "first_fault": None if first is None else asdict(first),
            },
        )
        terminal_saved = True
    except BaseException as receipt_error:
        fault("benign_terminal", receipt_error)
    if closed and terminal_saved and latest is not None and invocation is not None:
        try:
            manager.stop(plan, invocation, remaining())
            stopped = confirms_empty_unit_cleanup(plan, latest, manager.snapshot(plan, remaining()))
            if not stopped:
                raise ValueError("Benign cleanup not confirmed")
        except BaseException as stop_error:
            fault("benign_stop", stop_error)
    result: dict[str, object] = {
        "status": "provisional_complete"
        if first is None and witnessed and released and closed and stopped
        else "incomplete",
        "accepted": False,
        "witnessed_populated_after_leader_exit": witnessed,
        "release_acknowledged": released,
        "cgroup_closed": closed,
        "cleanup_confirmed": stopped,
        "first_fault": None if first is None else asdict(first),
        "supplemental": [asdict(value) for value in supplemental],
        "no_retry": True,
    }
    try:
        remaining()
        files.write("descendant-final.json", result)
        remaining()
    except BaseException as final_error:
        result["status"] = "incomplete"
        result["final_receipt_error"] = asdict(Fault.capture("benign_final", final_error))
    return result


def worker(path: Path, digest: str) -> int:
    raw = private_bytes(path, 4096)
    if hashlib.sha256(raw).hexdigest() != owned._digest(digest):
        raise ValueError("Benign request bytes differ")
    request = owned.decoded(raw, 4096)
    if (
        set(request) != {"schema", "unit", "token", "deadline"}
        or request["schema"] != "d1-descendant-request-v1"
    ):
        raise ValueError("Exact benign request required")
    unit, token, deadline = request["unit"], request["token"], request["deadline"]
    if (
        type(unit) is not str
        or not unit.startswith("d1-descendant-")
        or not unit.endswith(".service")
    ):
        raise ValueError("Fixed benign unit name required")
    owned._digest(unit[len("d1-descendant-") : -len(".service")], 24)
    token = owned._digest(token)
    if type(deadline) is not float or not 0 < deadline - time.monotonic() <= 30.0:
        raise ValueError("Finite original benign child deadline required")
    if (
        path.name != "descendant-request.json"
        or sys.flags.isolated != 1
        or sys.flags.dont_write_bytecode != 1
    ):
        raise ValueError("Fixed isolated benign worker required")
    invocation, group = owned.service_identity(unit)
    ready_r, ready_w = os.pipe()
    descriptors = {ready_r, ready_w}
    primary: BaseException | None = None
    primary_phase = "worker"
    supplemental: list[Fault] = []

    def remember(stage: str, error: BaseException) -> None:
        nonlocal primary, primary_phase
        if primary is None:
            primary, primary_phase = error, stage
        else:
            supplemental.append(Fault.capture(stage, error))

    def close_once(descriptor: int) -> None:
        if descriptor not in descriptors:
            return
        descriptors.remove(descriptor)  # A failed close consumes ownership too.
        try:
            os.close(descriptor)
        except BaseException as close_error:
            remember("worker_close", close_error)

    try:
        child = os.fork()
    except BaseException as fork_error:
        remember("fork", fork_error)
        for descriptor in tuple(sorted(descriptors)):
            close_once(descriptor)
        if supplemental:
            raise CommandFailure(fork_error, tuple(supplemental)) from None
        raise
    if child:
        close_once(ready_w)
        try:
            if primary is None:
                readable, _, _ = select.select(
                    [ready_r], [], [], min(5.0, max(0.0, deadline - time.monotonic()))
                )
                if not readable or os.read(ready_r, 2) != b"R":
                    raise TimeoutError("Descendant did not acknowledge readiness")
        except BaseException as ready_error:
            remember("leader_ready", ready_error)
        finally:
            for descriptor in tuple(sorted(descriptors)):
                close_once(descriptor)
        if primary is not None:
            if supplemental:
                raise CommandFailure(primary, tuple(supplemental)) from None
            raise primary
        return 0  # The service leader exits while its descendant still waits.
    close_once(ready_r)
    code = 1
    try:
        if primary is None:
            release_fd = os.open(
                path.parent / "release.fifo", os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW
            )
            descriptors.add(release_fd)
            info = os.fstat(release_fd)
            if (
                not stat.S_ISFIFO(info.st_mode)
                or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise ValueError("Owned private release FIFO required")
            body = owned.encoded(
                {
                    "schema": "d1-descendant-ready-v1",
                    "unit": unit,
                    "invocation_id": invocation,
                    "cgroup": group,
                    "token": token,
                }
            )
            owned.write_request(path.parent / "descendant-ready.json", body)
            if os.write(ready_w, b"R") != 1:
                raise OSError("Ready handoff failed")
            close_once(ready_w)
            if primary is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Original descendant deadline before release wait")
                readable, _, _ = select.select([release_fd], [], [], remaining)
                if not readable:
                    raise TimeoutError("Release missing before descendant deadline")
                release = os.read(release_fd, 66)
                if time.monotonic() >= deadline:
                    raise TimeoutError("Original descendant deadline after release read")
                if release != (token + "\n").encode("ascii"):
                    raise ValueError("Release token substituted")
                code = 0
    except BaseException as child_error:
        remember("descendant", child_error)
    finally:
        for descriptor in tuple(sorted(descriptors)):
            close_once(descriptor)
        if primary is not None:
            code = 1
        done = {
            "schema": "d1-descendant-done-v1",
            "unit": unit,
            "invocation_id": invocation,
            "cgroup": group,
            "token": token,
            "exit_code": code,
            "first_fault": None
            if primary is None
            else asdict(Fault.capture(primary_phase, primary)),
            "supplemental": [asdict(item) for item in supplemental],
        }
        try:
            owned.write_request(path.parent / "descendant-done.json", owned.encoded(done))
        except BaseException:
            code = 1  # Missing/partial done record cannot pass the external watcher.
        os._exit(code)


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] != "worker":
        raise ValueError("Only the fixed benign worker role exists")
    return worker(Path(sys.argv[2]), sys.argv[3])


if __name__ == "__main__":
    raise SystemExit(main())
