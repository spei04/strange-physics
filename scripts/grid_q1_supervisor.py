"""Disabled Linux-only control adapter for one separately admitted GRID-Q1 unit."""

import argparse
import hashlib
import json
import os
import re
import resource
import stat
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

ENABLED = False
if __name__ == "__main__" and not ENABLED:
    raise SystemExit("Disabled pending source, qualification and new combined admission")

SOURCE = "cec936a2a5a6534861eb9183861c4d6fcf931f67"
GRID_PROFILE = {
    "runtime_seconds": 1710,
    "start_timeout_seconds": 10,
    "stop_timeout_seconds": 10,
    "cpu_quota_percent": 50,
    "quota_period_us": 100_000,
    "cpu_watch_ns": 580_000_000_000,
    "poll_seconds": 30,
    "observations": 58,
    "command_seconds": 5,
    "term_grace_seconds": 2,
    "terminal_seconds": 1740,
    "service_file_bytes": 16 * 1024**2,
}
QUALIFICATION_PROFILE = {
    "runtime_seconds": 8,
    "start_timeout_seconds": 3,
    "stop_timeout_seconds": 2,
    "cpu_quota_percent": 50,
    "quota_period_us": 100_000,
    "cpu_watch_ns": 7_000_000_000,
    "poll_seconds": 1,
    "observations": 8,
    "command_seconds": 1,
    "term_grace_seconds": 1,
    "terminal_seconds": 15,
    "service_file_bytes": 1024**2,
}
# These are proposed configuration values, not an allocation or activation.
WHOLE_LEASE_SECONDS = 2400
WHOLE_HOST_CPU_UPPER_SECONDS = 33_600
WHOLE_OUTPUT_BYTES = 104 * 1024**2

MAX_RECORD = 64 * 1024
MAX_COMMAND_LOG = 8 * 1024
MAX_COMMANDS = 100
PROPERTIES = (
    "Id",
    "LoadState",
    "ActiveState",
    "SubState",
    "Type",
    "ExitType",
    "RemainAfterExit",
    "CPUAccounting",
    "Restart",
    "KillMode",
    "SendSIGKILL",
    "UMask",
    "LimitFSIZE",
    "LimitFSIZESoft",
    "RuntimeMaxUSec",
    "RuntimeRandomizedExtraUSec",
    "TimeoutStartUSec",
    "TimeoutStopUSec",
    "CPUQuotaPerSecUSec",
    "CPUQuotaPeriodUSec",
    "InvocationID",
    "ControlGroup",
    "CPUUsageNSec",
    "Result",
    "ExecMainCode",
    "ExecMainStatus",
    "ExecMainStartTimestamp",
    "ExecMainExitTimestamp",
    "ExecMainStartTimestampMonotonic",
    "ExecMainExitTimestampMonotonic",
    "NRestarts",
)


def object_map(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("Expected string-keyed object")
    return dict(value)


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected string")
    return value


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected integer")
    return value


def private_bytes(path: Path, maximum: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_size > maximum
        ):
            raise ValueError("Private regular bounded input required")
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Record extent")
    return raw


def duration_us(value: str) -> int:
    """Parse only finite systemd show time spans, without evaluating expressions."""
    units = {"us": 1, "ms": 1000, "s": 1_000_000, "min": 60_000_000, "h": 3_600_000_000}
    if value == "0":
        return 0
    parts = value.split()
    if not 1 <= len(parts) <= 4:
        raise ValueError("Duration shape")
    total = Decimal(0)
    for part in parts:
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(us|ms|s|min|h)", part)
        if match is None:
            raise ValueError("Unsupported duration")
        total += Decimal(match[1]) * units[match[2]]
    if total != total.to_integral_value() or not 0 <= total <= 86_400_000_000:
        raise ValueError("Duration range")
    return int(total)


@dataclass(frozen=True)
class Plan:
    root: Path
    admission_sha256: str
    controller_sha256: str
    runtime_seconds: int
    start_timeout_seconds: int
    stop_timeout_seconds: int
    cpu_quota_percent: int
    quota_period_us: int
    cpu_watch_ns: int
    poll_seconds: int
    observations: int
    command_seconds: int
    term_grace_seconds: int
    terminal_seconds: int
    service_file_bytes: int = 16 * 1024**2

    def __post_init__(self) -> None:
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("Exact absolute run root required")
        if self.root != self.root.resolve():
            raise ValueError("Run root aliases forbidden")
        root_stat = self.root.stat()
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or root_stat.st_uid != os.getuid()
            or stat.S_IMODE(root_stat.st_mode) != 0o700
        ):
            raise ValueError("Owner-private directory required")
        for digest in (self.admission_sha256, self.controller_sha256):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("Digest")
        for value in (
            self.runtime_seconds,
            self.start_timeout_seconds,
            self.stop_timeout_seconds,
            self.cpu_quota_percent,
            self.quota_period_us,
            self.cpu_watch_ns,
            self.poll_seconds,
            self.observations,
            self.command_seconds,
            self.term_grace_seconds,
            self.terminal_seconds,
            self.service_file_bytes,
        ):
            if type(value) is not int or value <= 0:
                raise ValueError("Positive explicit limits required")
        if (
            self.runtime_seconds > 1800
            or self.cpu_quota_percent > 100
            or self.service_file_bytes not in (1024**2, 16 * 1024**2)
            or self.quota_period_us > 1_000_000
            or self.observations > 64
            or self.command_seconds > 10
            or self.terminal_seconds > 1800
            or self.terminal_seconds <= self.runtime_seconds
            or self.term_grace_seconds + 2 * self.command_seconds >= self.terminal_seconds
            or self.poll_seconds * self.observations < self.runtime_seconds
        ):
            raise ValueError("Unreviewed control limits")

    @property
    def control_root(self) -> Path:
        return self.root.with_name(self.root.name + "-control")

    @property
    def unit(self) -> str:
        identity = f"{self.root}:{self.admission_sha256}".encode()
        return "grid-q1-" + hashlib.sha256(identity).hexdigest()[:24] + ".service"

    @property
    def argv(self) -> list[str]:
        return [
            "/usr/bin/python3",
            "-I",
            "-B",
            str(self.root / "run.py"),
            str(self.root / "admission.json"),
            self.admission_sha256,
        ]

    @property
    def required(self) -> dict[str, str]:
        return {
            "Type": "exec",
            "ExitType": "cgroup",
            "RemainAfterExit": "yes",
            "CPUAccounting": "yes",
            "Restart": "no",
            "KillMode": "control-group",
            "SendSIGKILL": "yes",
            "UMask": "0077",
            "NRestarts": "0",
            "LimitFSIZE": str(self.service_file_bytes),
            "LimitFSIZESoft": str(self.service_file_bytes),
        }


@dataclass(frozen=True)
class Snapshot:
    properties: dict[str, str]
    populated: bool | None

    @property
    def invocation(self) -> str:
        return self.properties.get("InvocationID", "")

    @property
    def cgroup(self) -> str:
        return self.properties.get("ControlGroup", "")

    @property
    def terminal(self) -> bool:
        return (
            self.properties.get("SubState") in ("exited", "dead", "failed")
            and int(self.properties.get("ExecMainExitTimestampMonotonic", "0")) > 0
        )

    @property
    def cpu_ns(self) -> int:
        raw = self.properties.get("CPUUsageNSec", "")
        if not raw.isdecimal() or not 0 <= int(raw) < 2**64 - 1:
            raise ValueError("Missing or sentinel CPU accounting")
        return int(raw)

    def bind(self, plan: Plan, invocation: str | None) -> None:
        if self.properties.get("Id") != plan.unit:
            raise ValueError("Unit identity changed")
        if re.fullmatch(r"[0-9a-f]{32}", self.invocation) is None:
            raise ValueError("Invocation identity missing")
        if invocation is not None and self.invocation != invocation:
            raise ValueError("Invocation identity changed")
        for key, expected in plan.required.items():
            if self.properties.get(key) != expected:
                raise ValueError(f"Supervisor property mismatch: {key}")
        durations = {
            "RuntimeMaxUSec": plan.runtime_seconds * 1_000_000,
            "RuntimeRandomizedExtraUSec": 0,
            "TimeoutStartUSec": plan.start_timeout_seconds * 1_000_000,
            "TimeoutStopUSec": plan.stop_timeout_seconds * 1_000_000,
            "CPUQuotaPerSecUSec": plan.cpu_quota_percent * 10_000,
            "CPUQuotaPeriodUSec": plan.quota_period_us,
        }
        for key, expected_duration in durations.items():
            if duration_us(self.properties.get(key, "")) != expected_duration:
                raise ValueError(f"Supervisor duration mismatch: {key}")
        expected_quota = (
            f"{plan.quota_period_us * plan.cpu_quota_percent // 100} {plan.quota_period_us}"
        )
        if (
            self.properties.get("ObservedCPUMax") != expected_quota
            or self.properties.get("ObservedCPUMaxBurst") != "0"
        ):
            raise ValueError("Actual quota/burst observation missing")
        _ = self.cpu_ns  # Validate accounting before binding this invocation.


def confirms_empty_unit_cleanup(plan: Plan, terminal: Snapshot, after: Snapshot) -> bool:
    """v255 retains failed units on stop; never reset their accounting to pass."""
    if after.properties.get("ActiveState") == "inactive":
        return after.populated is not True
    if after.properties.get("ActiveState") != "failed":
        return False
    after.bind(plan, terminal.invocation)
    retained = (
        "Result",
        "ExecMainCode",
        "ExecMainStatus",
        "ExecMainStartTimestampMonotonic",
        "ExecMainExitTimestampMonotonic",
    )
    return (
        terminal.properties.get("ActiveState") == "failed"
        and terminal.terminal
        and after.terminal
        and terminal.populated is not True
        and after.populated is not True
        and after.cgroup in ("", terminal.cgroup)
        and after.cpu_ns >= terminal.cpu_ns
        and all(after.properties.get(key) == terminal.properties.get(key) for key in retained)
    )


@dataclass(frozen=True)
class Fault:
    stage: str
    kind: str
    detail: str

    @classmethod
    def capture(cls, stage: str, error: BaseException) -> "Fault":
        return cls(stage, type(error).__name__, str(error)[:512])


class Supervisor(Protocol):
    def snapshot(self, plan: Plan, timeout: float) -> Snapshot: ...
    def submit(self, plan: Plan, timeout: float) -> None: ...
    def signal(self, plan: Plan, invocation: str, signal_name: str, timeout: float) -> None: ...
    def stop(self, plan: Plan, invocation: str, timeout: float) -> None: ...


class Receipts(Protocol):
    def write(self, name: str, record: dict[str, object]) -> None: ...
    def result(self, plan: Plan, invocation: str) -> dict[str, object]: ...


class Files:
    def __init__(self, root: Path, inner_root: Path | None = None) -> None:
        self.root = root
        self.inner_root = root if inner_root is None else inner_root

    def write(self, name: str, record: dict[str, object]) -> None:
        raw = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
        if len(raw) > MAX_RECORD:
            raise ValueError("Receipt extent")
        fd = os.open(self.root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def result(self, plan: Plan, invocation: str) -> dict[str, object]:
        result_raw = private_bytes(self.inner_root / "result.json", MAX_RECORD)
        verification_raw = private_bytes(self.inner_root / "verification.json", 128 * 1024)
        report_raw = private_bytes(self.inner_root / "product/report.json", 512 * 1024)
        result = object_map(json.loads(result_raw))
        verification = object_map(json.loads(verification_raw))
        report_sha = hashlib.sha256(report_raw).hexdigest()
        if (
            verification.get("source") != SOURCE
            or verification.get("authority_sha256") != plan.admission_sha256
            or verification.get("report_sha256") != report_sha
            or verification.get("outcome") != result.get("diagnostic_outcome")
            or verification.get("bare_helper_identity_verified") is not True
        ):
            raise ValueError("Current source/admission/report verification join")
        self.write(
            "supervisor-controller-result-join.json",
            {
                "unit": plan.unit,
                "invocation_id": invocation,
                "source": SOURCE,
                "admission_sha256": plan.admission_sha256,
                "report_sha256": report_sha,
                "result_sha256": hashlib.sha256(result_raw).hexdigest(),
                "verification_sha256": hashlib.sha256(verification_raw).hexdigest(),
            },
        )
        return result


def command_file_limit() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_COMMAND_LOG, MAX_COMMAND_LOG))


class CommandFailure(Exception):
    def __init__(self, primary: BaseException, supplemental: tuple[Fault, ...]) -> None:
        super().__init__(str(primary))
        self.primary = primary
        self.supplemental = supplemental


class Systemd:
    """Known Linux CLI children only; systemd owns the actual service cgroup."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.commands = 0
        self.groups: dict[str, str] = {}
        self.quotas: dict[str, tuple[str, str]] = {}

    def command(self, argv: list[str], timeout: float, allow_missing: bool = False) -> str:
        if timeout <= 0 or self.commands >= MAX_COMMANDS:
            raise TimeoutError("Control command budget")
        self.commands += 1
        path = self.root / f"supervisor-command-{self.commands:03d}.log"
        stream = path.open("xb")
        os.chmod(path, 0o600)
        primary: BaseException | None = None
        supplemental: list[Fault] = []
        child: subprocess.CompletedProcess[bytes] | None = None
        try:
            child = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=stream,
                timeout=timeout,
                check=False,
                preexec_fn=command_file_limit,
                env={**os.environ, "SYSTEMD_PAGER": "cat", "SYSTEMD_COLORS": "0", "LC_ALL": "C"},
            )
            if child.returncode not in ((0, 1) if allow_missing else (0,)):
                raise RuntimeError(
                    f"Control command exited {child.returncode}; retained {path.name}"
                )
        except BaseException as error:
            primary = error
        for label, action in (
            ("log_flush", stream.flush),
            ("log_fsync", lambda: os.fsync(stream.fileno())),
            ("log_close", stream.close),
        ):
            try:
                action()
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    supplemental.append(Fault.capture(label, error))
        if primary is not None:
            raise CommandFailure(primary, tuple(supplemental))
        if child is None:
            raise RuntimeError("Command observation missing")
        raw = path.read_bytes()
        if len(raw) >= MAX_COMMAND_LOG:
            raise ValueError("Control output limit reached")
        return raw.decode("utf-8", errors="strict")

    def snapshot(self, plan: Plan, timeout: float) -> Snapshot:
        raw = self.command(
            [
                "/usr/bin/systemctl",
                "--user",
                "--no-ask-password",
                "show",
                "--property=" + ",".join(PROPERTIES),
                plan.unit,
            ],
            timeout,
            allow_missing=True,
        )
        properties: dict[str, str] = {}
        for line in raw.splitlines():
            key, separator, value = line.partition("=")
            if not separator or key not in PROPERTIES or key in properties:
                raise ValueError("Unexpected supervisor response")
            properties[key] = value
        reported_group = properties.get("ControlGroup", "")
        if reported_group:
            previous = self.groups.get(plan.unit)
            if previous is not None and reported_group != previous:
                raise ValueError("Cgroup identity changed")
            self.groups[plan.unit] = reported_group
        cgroup = reported_group or self.groups.get(plan.unit, "")
        populated: bool | None = None
        if cgroup:
            path = Path("/sys/fs/cgroup") / cgroup.lstrip("/")
            if ".." in Path(cgroup).parts or not cgroup.startswith("/"):
                raise ValueError("Cgroup path")
            try:
                event_text = (path / "cgroup.events").read_text()
            except FileNotFoundError:
                if path.exists():
                    raise
            else:
                values = dict(line.split() for line in event_text.splitlines())
                if values.get("populated") not in ("0", "1"):
                    raise ValueError("Missing populated state")
                populated = values["populated"] == "1"
                quota = (path / "cpu.max").read_text().strip()
                burst = (path / "cpu.max.burst").read_text().strip()
                expected_quota = (
                    f"{plan.quota_period_us * plan.cpu_quota_percent // 100} {plan.quota_period_us}"
                )
                if quota != expected_quota or burst != "0":
                    raise ValueError("Unqualified actual cgroup quota/burst")
                self.quotas[plan.unit] = (quota, burst)
        if plan.unit in self.quotas:
            properties["ObservedCPUMax"], properties["ObservedCPUMaxBurst"] = self.quotas[plan.unit]
        return Snapshot(properties, populated)

    def submit(self, plan: Plan, timeout: float) -> None:
        properties = {
            "ExitType": "cgroup",
            "CPUAccounting": "yes",
            "Restart": "no",
            "RuntimeMaxSec": str(plan.runtime_seconds),
            "RuntimeRandomizedExtraSec": "0",
            "TimeoutStartSec": str(plan.start_timeout_seconds),
            "TimeoutStopSec": str(plan.stop_timeout_seconds),
            "KillMode": "control-group",
            "SendSIGKILL": "yes",
            "UMask": "0077",
            "LimitFSIZE": str(plan.service_file_bytes),
            "LimitCORE": "0",
            "CPUQuota": f"{plan.cpu_quota_percent}%",
            "CPUQuotaPeriodSec": f"{plan.quota_period_us}us",
            "StandardOutput": f"append:{plan.control_root / 'supervisor-service.log'}",
            "StandardError": f"append:{plan.control_root / 'supervisor-service.log'}",
        }
        with (plan.control_root / "supervisor-service.log").open("xb"):
            pass
        os.chmod(plan.control_root / "supervisor-service.log", 0o600)
        argv = [
            "/usr/bin/systemd-run",
            "--user",
            "--quiet",
            "--no-ask-password",
            "--service-type=exec",
            "--remain-after-exit",
            "--expand-environment=no",
            "--unit=" + plan.unit,
            "--working-directory=" + str(plan.root),
        ]
        argv.extend(f"--property={key}={value}" for key, value in properties.items())
        self.command([*argv, "--", *plan.argv], timeout)

    def signal(self, plan: Plan, invocation: str, signal_name: str, timeout: float) -> None:
        if signal_name not in ("SIGTERM", "SIGKILL"):
            raise ValueError("Signal allowlist")
        deadline = time.monotonic() + timeout
        self.snapshot(plan, timeout).bind(plan, invocation)
        self.command(
            [
                "/usr/bin/systemctl",
                "--user",
                "--no-ask-password",
                "kill",
                "--kill-whom=all",
                "--signal=" + signal_name,
                plan.unit,
            ],
            deadline - time.monotonic(),
        )

    def stop(self, plan: Plan, invocation: str, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        snapshot = self.snapshot(plan, timeout)
        snapshot.bind(plan, invocation)
        if not snapshot.terminal or snapshot.populated is True:
            raise ValueError("Refuse to stop a populated/nonterminal unit")
        self.command(
            ["/usr/bin/systemctl", "--user", "--no-ask-password", "stop", plan.unit],
            deadline - time.monotonic(),
        )


def execute(
    plan: Plan,
    supervisor: Supervisor,
    receipts: Receipts,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """One dispatch; qualification and the final external ledger remain separate gates."""
    record: dict[str, object]
    first: Fault | None = None
    errors: list[Fault] = []
    invocation: str | None = None
    cgroup: str | None = None
    latest: Snapshot | None = None
    dispatch_attempted = False
    claimed = False
    duplicate_claim = False
    closed = False
    stopped = False
    snapshot_saved = False
    bound_saved = False
    outcome: str | None = None
    start = clock()

    def fault(stage: str, error: BaseException) -> None:
        nonlocal first
        supplemental = error.supplemental if isinstance(error, CommandFailure) else ()
        original = error.primary if isinstance(error, CommandFailure) else error
        captured = Fault.capture(stage, original)
        if first is None:
            first = captured
            try:
                receipts.write("supervisor-first-fault.json", asdict(captured))
            except BaseException as write_error:
                errors.append(Fault.capture("first_fault_receipt", write_error))
        else:
            errors.append(captured)
        errors.extend(supplemental)

    def bind(snapshot: Snapshot) -> None:
        nonlocal invocation, cgroup, latest, closed, bound_saved
        snapshot.bind(plan, invocation)
        invocation = snapshot.invocation
        if cgroup is None:
            if not snapshot.cgroup or (snapshot.terminal and snapshot.populated is None):
                raise ValueError("No previously captured cgroup identity for disappearance")
            cgroup = snapshot.cgroup
        elif snapshot.cgroup and snapshot.cgroup != cgroup:
            raise ValueError("Cgroup identity changed")
        if latest is not None and snapshot.cpu_ns < latest.cpu_ns:
            raise ValueError("Cgroup CPU accounting decreased")
        latest = snapshot
        if not bound_saved:
            receipts.write(
                "supervisor-bound.json",
                {
                    "unit": plan.unit,
                    "invocation_id": invocation,
                    "cgroup": cgroup,
                    "source": SOURCE,
                    "admission_sha256": plan.admission_sha256,
                    "snapshot": asdict(snapshot),
                    "monotonic_bound": clock(),
                },
            )
            bound_saved = True
        # None is qualified only after a real cgroup path was bound for this invocation.
        closed = snapshot.terminal and snapshot.populated is not True

    try:
        receipts.write(
            "supervisor-intent.json",
            {
                "unit": plan.unit,
                "source": SOURCE,
                "run_root": str(plan.root),
                "control_root": str(plan.control_root),
                "admission_sha256": plan.admission_sha256,
                "argv": plan.argv,
                "controller_sha256": plan.controller_sha256,
                "no_retry": True,
                "monotonic_start": start,
                "realtime_start_ns": time.time_ns(),
            },
        )
        claimed = True
        initial = supervisor.snapshot(plan, plan.command_seconds)
        if initial.properties.get("LoadState") != "not-found":
            raise ValueError("Unit already exists; never resubmit")
        dispatch_attempted = True
        supervisor.submit(plan, plan.command_seconds)
        observation_deadline = start + plan.runtime_seconds + plan.start_timeout_seconds
        for _ in range(plan.observations):
            left = observation_deadline - clock()
            if left <= 0:
                raise TimeoutError("Observation deadline")
            bind(supervisor.snapshot(plan, min(float(plan.command_seconds), left)))
            if latest is not None and latest.cpu_ns >= plan.cpu_watch_ns:
                raise RuntimeError("CPU watch margin reached")
            if closed:
                break
            pause(max(0.0, min(float(plan.poll_seconds), observation_deadline - clock())))
        if not closed:
            raise TimeoutError("Observation census exhausted")
        assert invocation is not None
        result = receipts.result(plan, invocation)
        candidate = result.get("diagnostic_outcome")
        if (
            result.get("final_status") != "complete"
            or result.get("within_envelope") is not True
            or candidate not in ("passed", "failed")
            or latest is None
            or latest.properties.get("Result")
            != ("success" if candidate == "passed" else "exit-code")
            or latest.properties.get("ExecMainCode") != "1"
            or latest.properties.get("ExecMainStatus") != ("0" if candidate == "passed" else "1")
        ):
            raise ValueError("Incomplete or inconsistent controller result")
        outcome = "passed" if candidate == "passed" else "complete_negative"
    except BaseException as error:
        if isinstance(error, FileExistsError) and not claimed:
            duplicate_claim = True
        else:
            fault("dispatch_or_observation", error)
    finally:
        if duplicate_claim:
            # Existing unit evidence is immutable; do not append another attempt.
            record = {
                "status": "incomplete",
                "accepted": False,
                "numerical_attempt": "not_started",
                "reason": "exclusive_claim_exists",
                "no_retry": True,
            }
        else:
            terminal_deadline = start + plan.terminal_seconds

            def remaining() -> float:
                value = min(float(plan.command_seconds), terminal_deadline - clock())
                if value <= 0:
                    raise TimeoutError("Terminal deadline")
                return value

            if dispatch_attempted and not closed:
                try:
                    bind(supervisor.snapshot(plan, remaining()))
                    if not closed:
                        assert invocation is not None
                        supervisor.signal(plan, invocation, "SIGTERM", remaining())
                        pause(min(float(plan.term_grace_seconds), remaining()))
                        bind(supervisor.snapshot(plan, remaining()))
                        if not closed:
                            supervisor.signal(plan, invocation, "SIGKILL", remaining())
                        while not closed:
                            bind(supervisor.snapshot(plan, remaining()))
                            if not closed:
                                pause(min(1.0, remaining()))
                except BaseException as error:
                    fault("termination", error)
            try:
                receipts.write(
                    "supervisor-terminal-before-stop.json",
                    {
                        "unit": plan.unit,
                        "invocation_id": invocation,
                        "cgroup": cgroup,
                        "snapshot": None if latest is None else asdict(latest),
                        "closed": closed,
                        "first_fault": None if first is None else asdict(first),
                        "cleanup_errors": [asdict(error) for error in errors],
                        "accounting_retained_before_stop": True,
                    },
                )
                snapshot_saved = True
            except BaseException as error:
                fault("terminal_snapshot_receipt", error)
            if closed and snapshot_saved and invocation is not None:
                try:
                    supervisor.stop(plan, invocation, remaining())
                    final = supervisor.snapshot(plan, remaining())
                    assert latest is not None
                    if not confirms_empty_unit_cleanup(plan, latest, final):
                        raise ValueError("Unit cleanup unconfirmed")
                    stopped = True
                except BaseException as error:
                    fault("empty_unit_cleanup", error)
            record = {
                "unit": plan.unit,
                "invocation_id": invocation,
                "cgroup": cgroup,
                "dispatch_attempted": dispatch_attempted,
                "numerical_attempt": (
                    "not_started"
                    if not dispatch_attempted
                    else "completed"
                    if outcome is not None
                    else "attempt_unknown"
                ),
                "diagnostic_outcome": outcome,
                "first_fault": None if first is None else asdict(first),
                "cleanup_errors": [asdict(error) for error in errors],
                "cgroup_closed": closed,
                "unit_cleanup_confirmed": stopped,
                "terminal_snapshot_saved_before_stop": snapshot_saved,
                "status": (
                    "provisional_complete"
                    if first is None and not errors and closed and stopped and outcome is not None
                    else "incomplete"
                ),
                "accepted": False,
                "external_combined_ledger_closure_required": True,
                "active_wall_before_final_receipt": clock() - start,
                "no_retry": True,
            }
            try:
                receipts.write("supervisor-final.json", record)
            except BaseException as error:
                record["status"] = "incomplete"
                record["final_receipt_error"] = asdict(Fault.capture("final_receipt", error))
                try:
                    receipts.write("supervisor-fallback.json", record)
                except BaseException as fallback_error:
                    record["fallback_receipt_error"] = asdict(
                        Fault.capture("fallback_receipt", fallback_error)
                    )
    return record


def load_plan(admission_path: Path, expected_sha256: str) -> Plan:
    root = admission_path.parent
    if admission_path.name != "admission.json":
        raise ValueError("Exact admission path")
    raw = private_bytes(admission_path, MAX_RECORD)
    if len(raw) > MAX_RECORD or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Admission digest/extent")
    admission = object_map(json.loads(raw))
    if (
        admission.get("admitted") is not True
        or admission.get("source") != SOURCE
        or admission.get("run_root") != str(root)
    ):
        raise ValueError("New exact source/run admission required")
    fields = object_map(admission.get("supervisor"))
    for key, expected in GRID_PROFILE.items():
        if fields.get(key) != expected:
            raise ValueError("Unreviewed GRID supervisor profile")
    if fields.get("qualification_accepted") is not True:
        raise ValueError("Wrapper qualification pending")
    controller = private_bytes(root / "run.py", 256 * 1024)
    digest = text(fields.get("controller_sha256"))
    if hashlib.sha256(controller).hexdigest() != digest:
        raise ValueError("Controller identity")
    prior = (
        "started.json",
        "source",
        "product",
        "result.json",
        "verification.json",
        "activation.json",
        "controller-exception.json",
        "administrative-outcome.json",
        "held-attempt.json",
        "held-attempt-receipt.json",
    )
    if any(os.path.lexists(root / name) for name in prior):
        raise ValueError("No previous attempt, held authority or controller outcome")
    control_root = root.with_name(root.name + "-control")
    if admission.get("supervisor_control_root") != str(control_root):
        raise ValueError("Exact independent outer control root required")
    if control_root != control_root.resolve():
        raise ValueError("Control root aliases forbidden")
    control_stat = control_root.stat()
    if (
        not stat.S_ISDIR(control_stat.st_mode)
        or control_stat.st_uid != os.getuid()
        or stat.S_IMODE(control_stat.st_mode) != 0o700
    ):
        raise ValueError("Private outer control root required")
    return Plan(
        root,
        expected_sha256,
        digest,
        integer(fields.get("runtime_seconds")),
        integer(fields.get("start_timeout_seconds")),
        integer(fields.get("stop_timeout_seconds")),
        integer(fields.get("cpu_quota_percent")),
        integer(fields.get("quota_period_us")),
        integer(fields.get("cpu_watch_ns")),
        integer(fields.get("poll_seconds")),
        integer(fields.get("observations")),
        integer(fields.get("command_seconds")),
        integer(fields.get("term_grace_seconds")),
        integer(fields.get("terminal_seconds")),
        integer(fields.get("service_file_bytes")),
    )


def main() -> int:
    if not ENABLED:
        raise SystemExit("Disabled pending new combined admission")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    plan = load_plan(args.admission, args.sha256)
    result = execute(plan, Systemd(plan.control_root), Files(plan.control_root, plan.root))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "provisional_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
