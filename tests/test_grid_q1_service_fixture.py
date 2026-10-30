"""Pure failure checks for the disabled live-fixture operator protocol."""

from __future__ import annotations

import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import grid_q1_service_fixture as fixture
from scripts import grid_q1_supervisor as core


@pytest.fixture(autouse=True)
def no_process_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("Real process/service work is forbidden")

    monkeypatch.setattr(os, "fork", denied)
    monkeypatch.setattr(os, "execv", denied)
    monkeypatch.setattr(os, "kill", denied)
    monkeypatch.setattr(os, "killpg", denied)
    monkeypatch.setattr(subprocess, "Popen", denied)


def private_dir(path: Path) -> Path:
    path.mkdir(mode=0o700)
    return path


def save(path: Path, value: object) -> str:
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


def authorized(tmp_path: Path) -> dict[str, object]:
    root = private_dir(tmp_path / "normal")
    outer = private_dir(tmp_path / "normal-control")
    data: dict[str, object] = {
        "source": fixture.SOURCE,
        "combined_id": "future-fixed-unit",
        "binding_id": "normal",
        "contract": fixture.CONTRACT,
        "owned_roots": [str(root), str(outer)],
        "root": str(root),
        "control_root": str(outer),
        "owner_admitted": True,
        "kind": "normal",
        "adapter": {"path": "unused", "sha256": "d" * 64},
        "fixture_active_sha256": "b" * 64,
    }
    owner: dict[str, object] = {
        "approved": True,
        "combined_id": data["combined_id"],
        "source": fixture.SOURCE,
        "contract": fixture.CONTRACT,
        "historical_costs": "unknowns-preserved-no-reset",
        "owned_roots": data["owned_roots"],
        "qualification_roots": {"normal": [str(root), str(outer)]},
        "fixture_active_sha256": "b" * 64,
        "adapter_sha256": "d" * 64,
    }
    path = tmp_path / "owner.json"
    data["owner"] = {"path": str(path), "sha256": save(path, owner)}
    return data


def test_owner_projection_binds_exact_source_and_roots(tmp_path: Path) -> None:
    data = authorized(tmp_path)
    fixture.owner_check(data)
    data["root"] = str(tmp_path)
    with pytest.raises(ValueError, match="Owner-bound"):
        fixture.owner_check(data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("owner_admitted", False),
        ("source", "0" * 40),
        ("combined_id", "different"),
        ("contract", {}),
    ],
)
def test_owner_rejects_inactive_or_changed_plan(
    tmp_path: Path,
    key: str,
    value: object,
) -> None:
    data = authorized(tmp_path)
    data[key] = value
    with pytest.raises(ValueError):
        fixture.owner_check(data)


@pytest.mark.parametrize(
    "kind,result,code,status,expected",
    [
        ("normal", "success", "1", "0", True),
        ("nonzero", "exit-code", "1", "7", True),
        ("timeout", "timeout", "2", "15", True),
        ("timeout", "timeout", "2", "9", True),
        ("normal", "success", "1", "7", False),
        ("nonzero", "success", "1", "0", False),
        ("timeout", "success", "2", "15", False),
        ("timeout", "timeout", "1", "0", False),
    ],
)
def test_exact_terminal_outcomes(
    kind: str,
    result: str,
    code: str,
    status: str,
    expected: bool,
) -> None:
    assert (
        fixture.expected_terminal(
            kind,
            {
                "Result": result,
                "ExecMainCode": code,
                "ExecMainStatus": status,
            },
        )
        is expected
    )


def lease() -> dict[str, object]:
    return {
        "start_monotonic_ns": 100,
        "end_monotonic_ns": 1000,
        "maximum_cpu_count": 4,
        "boot_start": "boot",
        "boot_end": "boot",
        "closed": True,
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("end_monotonic_ns", 2_400_000_000_101),
        ("end_monotonic_ns", 99),
        ("closed", False),
        ("maximum_cpu_count", 5),
        ("maximum_cpu_count", True),
        ("boot_end", "changed"),
        ("boot_start", ""),
        ("start_monotonic_ns", 1.5),
    ],
)
def test_lease_rejects_unknown_or_out_of_contract(key: str, value: object) -> None:
    data = lease()
    data[key] = value
    with pytest.raises(ValueError):
        fixture.lease_check(data, 4)


def test_closed_lease_is_accepted() -> None:
    fixture.lease_check(lease(), 4)


def test_first_fault_survives_cleanup_fault(tmp_path: Path) -> None:
    root = private_dir(tmp_path / "control")
    error = core.CommandFailure(
        TimeoutError("submit lost acknowledgement"),
        (core.Fault("log_fsync", "PermissionError", "denied"),),
    )
    fixture.record_fault(root, "start", error)
    fixture.record_fault(root, "finish", PermissionError("cleanup denied"))
    first = json.loads((root / "first-fault.json").read_text())
    later = json.loads((root / "cleanup-fault-00.json").read_text())
    assert first["kind"] == "TimeoutError"
    assert first["supplemental"] == [
        {"stage": "log_fsync", "kind": "PermissionError", "detail": "denied"},
    ]
    assert later["kind"] == "PermissionError"


def test_one_start_intent_prevents_second_submission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = authorized(tmp_path)
    root = Path(str(data["root"]))
    outer = Path(str(data["control_root"]))
    plan = core.Plan(
        root, "a" * 64, "b" * 64, 8, 3, 2, 50, 100000, 7_000_000_000, 1, 8, 1, 1, 15, 1024**2
    )
    monkeypatch.setattr(fixture, "qualification_plan", lambda *_: plan)
    fixture.write(outer, "intent.json", {"unknown_dispatch": True})
    with pytest.raises(FileExistsError):
        fixture.start(data, "a" * 64)


def test_three_live_qualification_receipts_are_required() -> None:
    with pytest.raises(ValueError, match="Exactly three"):
        fixture.fixture_barrier({"fixtures": []})


def test_failed_barrier_cannot_exec_grid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = private_dir(tmp_path / "control")

    def incomplete(_: dict[str, object]) -> list[dict[str, object]]:
        raise ValueError("qualification incomplete")

    monkeypatch.setattr(fixture, "fixture_barrier", incomplete)
    with pytest.raises(ValueError, match="qualification incomplete"):
        fixture.dispatch({"control_root": str(root), "combined_id": "test", "owner": {}})


def test_default_cli_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fixture, "ENABLED", False)
    with pytest.raises(SystemExit, match="Disabled"):
        fixture.main()


def test_receipt_exclusive_and_private(tmp_path: Path) -> None:
    root = private_dir(tmp_path / "control")
    fixture.write(root, "intent.json", {"dispatch": False})
    with pytest.raises(FileExistsError):
        fixture.write(root, "intent.json", {"dispatch": True})
    assert (root / "intent.json").stat().st_mode & 0o777 == 0o600


def test_output_census_rejects_unlisted_root(tmp_path: Path) -> None:
    root = private_dir(tmp_path / "control")
    manifest: dict[str, object] = {
        "owned_roots": [str(root)],
        "output_pools": {
            name: [] for name in ("inner", "qualification", "source", "grid_control", "transport")
        },
    }
    with pytest.raises(ValueError, match="Incomplete"):
        fixture.output_census(manifest)


def test_output_census_rejects_alias(tmp_path: Path) -> None:
    root = private_dir(tmp_path / "control")
    (root / "alias").symlink_to(tmp_path)
    manifest: dict[str, object] = {
        "owned_roots": [str(root)],
        "output_pools": {
            "inner": [],
            "qualification": [],
            "source": [],
            "grid_control": [],
            "transport": [str(root)],
        },
    }
    with pytest.raises(ValueError):
        fixture.output_census(manifest)


@pytest.mark.parametrize("kind,code", [("normal", 0), ("nonzero", 7)])
def test_worker_requires_exact_release_before_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    code: int,
) -> None:
    data = authorized(tmp_path)
    data["kind"] = kind
    data["fixture_active_sha256"] = fixture.digest(b"pinned-fixture")
    spec_sha = "a" * 64
    invocation = "b" * 32
    token = {"spec_sha256": spec_sha, "invocation_id": invocation, "kind": kind}
    rows: list[tuple[str, dict[str, object]]] = []

    def retained(_: Path, name: str, value: dict[str, object]) -> str:
        rows.append((name, value))
        return "c" * 64

    monkeypatch.setenv("INVOCATION_ID", invocation)
    monkeypatch.setattr(fixture, "read", lambda *_: b"pinned-fixture")
    monkeypatch.setattr(fixture, "write", retained)
    with monkeypatch.context() as worker_mocks:
        worker_mocks.setattr(os, "mkfifo", lambda *_: None)
        worker_mocks.setattr(os, "open", lambda *_: 17)
        worker_mocks.setattr(os, "close", lambda *_: None)
        worker_mocks.setattr(os, "read", lambda *_: json.dumps(token).encode())
        worker_mocks.setattr(select, "select", lambda *_: ([17], [], []))
        assert fixture.worker(data, spec_sha) == code
    assert [name for name, _ in rows] == ["worker-ready.json", "worker-released.json"]
    assert rows[-1][1] == token


def test_wrong_release_does_not_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = authorized(tmp_path)
    data["kind"] = "normal"
    data["fixture_active_sha256"] = fixture.digest(b"pinned-fixture")
    names: list[str] = []

    def retained(_: Path, name: str, value: dict[str, object]) -> str:
        names.append(name)
        return "c" * 64

    monkeypatch.setenv("INVOCATION_ID", "b" * 32)
    monkeypatch.setattr(fixture, "read", lambda *_: b"pinned-fixture")
    monkeypatch.setattr(fixture, "write", retained)
    with monkeypatch.context() as worker_mocks:
        worker_mocks.setattr(os, "mkfifo", lambda *_: None)
        worker_mocks.setattr(os, "open", lambda *_: 17)
        worker_mocks.setattr(os, "close", lambda *_: None)
        worker_mocks.setattr(os, "read", lambda *_: b'{"invocation_id":"wrong"}')
        worker_mocks.setattr(select, "select", lambda *_: ([17], [], []))
        with pytest.raises(ValueError, match="Release identity"):
            fixture.worker(data, "a" * 64)
    assert names == ["worker-ready.json"]


def test_three_automatic_handshakes_reach_barrier_without_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the operator order with fake manager/FIFO operations, not just fields."""
    owned: list[str] = []
    specs: list[dict[str, object]] = []
    for kind in fixture.KINDS:
        root = private_dir(tmp_path / kind)
        outer = private_dir(tmp_path / (kind + "-control"))
        (root / "run.py").write_bytes(b"active-fixture")
        (root / "run.py").chmod(0o600)
        owned.extend((str(root), str(outer)))
        specs.append(
            {
                "source": fixture.SOURCE,
                "combined_id": "one-new-combined-unit",
                "binding_id": kind,
                "contract": fixture.CONTRACT,
                "kind": kind,
                "root": str(root),
                "control_root": str(outer),
                "fixture_active_sha256": fixture.digest(b"active-fixture"),
                "adapter": {"sha256": "d" * 64, "path": "not-imported-in-fake"},
                "profile": fixture.QUALIFICATION,
                "owner_admitted": True,
            }
        )
    for spec in specs:
        spec["owned_roots"] = owned
    combined_control = private_dir(tmp_path / "combined-control")
    grid_root = private_dir(tmp_path / "grid")
    grid_control = private_dir(tmp_path / "grid-control")
    owned.extend((str(combined_control), str(grid_root), str(grid_control)))
    inner_owner_path = tmp_path / "inner-owner.json"
    inner_sha = save(inner_owner_path, {"approved": True, "root": str(grid_root)})
    template_path = tmp_path / "grid-template.json"
    template_sha = save(
        template_path,
        {
            "source": fixture.SOURCE,
            "run_root": str(grid_root),
            "owner": {"path": str(inner_owner_path), "sha256": inner_sha},
        },
    )
    engineering_path = combined_control / "engineering.json"
    engineering_ref = {
        "path": str(engineering_path),
        "sha256": save(
            engineering_path,
            {
                "status": "accepted_fake_only",
                "scientific_calls": 0,
                "real_process_attempts": 0,
                "adapter_sha256": "d" * 64,
                "fixture_disabled_sha256": "f" * 64,
                "all_cases_passed": True,
            },
        ),
    }
    lease_refs: dict[str, object] = {}
    for host, cpus in (("client", 10), ("server", 4)):
        lease_path = combined_control / (host + "-observation.json")
        lease_refs[host] = {
            "path": str(lease_path),
            "sha256": save(
                lease_path,
                {
                    "source": fixture.SOURCE,
                    "combined_id": "one-new-combined-unit",
                    "start_monotonic_ns": 1,
                    "observed_monotonic_ns": 2,
                    "maximum_cpu_count": cpus,
                    "boot_start": "boot",
                    "boot_observed": "boot",
                    "closed": False,
                },
            ),
        }
    output_pools = {
        "qualification": [str(spec[key]) for spec in specs for key in ("root", "control_root")],
        "inner": [str(grid_root)],
        "grid_control": [str(grid_control)],
        "transport": [str(combined_control)],
        "source": [],
    }
    operator_ref = {"path": str(tmp_path / "operator.sh"), "sha256": "9" * 64}
    owner_path = tmp_path / "owner.json"
    owner_sha = save(
        owner_path,
        {
            "approved": True,
            "combined_id": "one-new-combined-unit",
            "source": fixture.SOURCE,
            "contract": fixture.CONTRACT,
            "historical_costs": "unknowns-preserved-no-reset",
            "owned_roots": owned,
            "qualification_roots": {
                str(spec["kind"]): [spec["root"], spec["control_root"]] for spec in specs
            },
            "fixture_active_sha256": fixture.digest(b"active-fixture"),
            "adapter_sha256": "d" * 64,
            "fixture_disabled_sha256": "f" * 64,
            "combined_control_root": str(combined_control),
            "grid_run_root": str(grid_root),
            "grid_control_root": str(grid_control),
            "grid_template_sha256": template_sha,
            "leases": lease_refs,
            "output_pools": output_pools,
            "engineering": engineering_ref,
            "operator": operator_ref,
        },
    )
    owner = {"path": str(owner_path), "sha256": owner_sha}
    entries: list[dict[str, object]] = []
    for spec in specs:
        spec["owner"] = owner
        path = Path(str(spec["root"])) / "admission.json"
        entries.append({"path": str(path), "sha256": save(path, spec)})
    real_lstat = Path.lstat
    real_open = os.open
    real_close = os.close
    invocation = "e" * 32
    active: dict[str, object] = {}

    class FakeManager:
        def __init__(self, data: dict[str, object], sha: str, plan: core.Plan) -> None:
            self.data = data
            self.sha = sha
            self.plan = plan
            self.submitted = False
            self.released = False
            self.stopped = False

        def snapshot(self, plan: core.Plan, timeout: float) -> core.Snapshot:
            assert timeout > 0
            if not self.submitted:
                return core.Snapshot({"LoadState": "not-found"}, None)
            properties = {
                **plan.required,
                "Id": plan.unit,
                "InvocationID": invocation,
                "ControlGroup": "/fake-owned",
                "CPUUsageNSec": "100",
                "ObservedCPUMax": "50000 100000",
                "ObservedCPUMaxBurst": "0",
                "RuntimeMaxUSec": "8s",
                "RuntimeRandomizedExtraUSec": "0",
                "TimeoutStartUSec": "3s",
                "TimeoutStopUSec": "2s",
                "CPUQuotaPerSecUSec": "500ms",
                "CPUQuotaPeriodUSec": "100ms",
                "ActiveState": "inactive" if self.stopped else "active",
                "SubState": "exited" if self.released else "running",
                "ExecMainExitTimestampMonotonic": "1" if self.released else "0",
            }
            kind = str(self.data["kind"])
            values = {
                "normal": ("success", "1", "0"),
                "nonzero": ("exit-code", "1", "7"),
                "timeout": ("timeout", "2", "15"),
            }[kind]
            properties.update(
                dict(zip(("Result", "ExecMainCode", "ExecMainStatus"), values, strict=True))
            )
            if self.released and kind in ("nonzero", "timeout"):
                properties.update(ActiveState="failed", SubState="failed")
            return core.Snapshot(properties, not self.released)

        def submit(self, plan: core.Plan, timeout: float) -> None:
            assert not self.submitted and timeout == 3
            self.submitted = True
            fixture.write(
                plan.root,
                "worker-ready.json",
                {
                    "spec_sha256": self.sha,
                    "invocation_id": invocation,
                    "kind": self.data["kind"],
                    "fixture_sha256": fixture.digest(b"active-fixture"),
                    "pid": 123,
                    "descendant_pid": 124 if self.data["kind"] == "timeout" else None,
                },
            )

        def stop(self, plan: core.Plan, owner: str, timeout: float) -> None:
            assert owner == invocation and self.released and timeout > 0
            assert (plan.control_root / "terminal-before-stop.json").exists()
            self.stopped = True

    def fifo_lstat(path: Path, *, follow_symlinks: bool = False) -> os.stat_result:
        if path.name == "release.fifo":
            return os.stat_result((0o010600, 1, 1, 1, os.getuid(), os.getgid(), 0, 0, 0, 0))
        return real_lstat(path)

    def fifo_open(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        if isinstance(path, Path) and path.name == "release.fifo":
            return 9876
        if not isinstance(path, (str, bytes, Path)):
            raise AssertionError("Unexpected path")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    def fifo_write(fd: int, raw: bytes) -> int:
        assert fd == 9876
        backend = active["backend"]
        assert isinstance(backend, FakeManager)
        token = json.loads(raw)
        fixture.write(backend.plan.root, "worker-released.json", token)
        backend.released = True
        return len(raw)

    monkeypatch.setattr(Path, "lstat", fifo_lstat)
    monkeypatch.setattr(os, "open", fifo_open)
    monkeypatch.setattr(os, "close", lambda fd: None if fd == 9876 else real_close(fd))
    monkeypatch.setattr(os, "write", fifo_write)
    monkeypatch.setattr(time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(
        os,
        "statvfs",
        lambda _: os.statvfs_result(
            (4096, 4096, 2**24, 2**24, 2**24, 2**24, 2**24, 2**24, 0, 255),
        ),
    )
    for spec, entry in zip(specs, entries, strict=True):
        sha = str(entry["sha256"])
        root = Path(str(spec["root"]))
        plan = core.Plan(
            root,
            sha,
            fixture.digest(b"active-fixture"),
            8,
            3,
            2,
            50,
            100000,
            7_000_000_000,
            1,
            8,
            1,
            1,
            15,
            1024**2,
        )
        backend = FakeManager(spec, sha, plan)
        active["backend"] = backend
        monkeypatch.setattr(fixture, "qualification_plan", lambda *_, p=plan: p)
        monkeypatch.setattr(fixture, "backend_for", lambda *_, b=backend: b)
        fixture.start(spec, sha)
        fixture.ready(spec, sha)
        fixture.release(spec, sha)
        assert fixture.finish(spec, sha)
        assert backend.submitted and backend.stopped
        final_state = backend.snapshot(plan, 1)
        assert final_state.properties["ActiveState"] == (
            "inactive" if spec["kind"] == "normal" else "failed"
        )
        assert final_state.populated is False
    combined: dict[str, object] = {
        "fixtures": entries,
        "leases": lease_refs,
        "output_pools": output_pools,
        "engineering": engineering_ref,
        "operator": operator_ref,
        "combined_id": "one-new-combined-unit",
        "owner": owner,
        "owned_roots": owned,
        "source": fixture.SOURCE,
        "contract": fixture.CONTRACT,
        "owner_admitted": True,
        "control_root": str(combined_control),
        "fixture_disabled_sha256": "f" * 64,
        "adapter": {"path": "unused", "sha256": "d" * 64},
        "grid": {
            "root": str(grid_root),
            "control_root": str(grid_control),
            "template_path": str(template_path),
            "template_sha256": template_sha,
        },
    }
    fixture.owner_check(combined)
    rows = fixture.fixture_barrier(combined)
    assert [row["kind"] for row in rows] == list(fixture.KINDS)
    fixture.barrier(combined)
    assert (combined_control / "qualification-barrier.json").is_file()
    for changed in (
        "client_path",
        "server_path",
        "lease_digest",
        "pool_swap",
        "engineering_digest",
        "operator_digest",
    ):
        altered = fixture.mapping(json.loads(json.dumps(combined)))
        if changed in ("client_path", "server_path", "lease_digest"):
            host = "server" if changed == "server_path" else "client"
            refs = fixture.mapping(altered["leases"])
            ref = fixture.mapping(refs[host])
            ref["sha256" if changed == "lease_digest" else "path"] = (
                "0" * 64 if changed == "lease_digest" else str(tmp_path / "later-start.json")
            )
            refs[host] = ref
            altered["leases"] = refs
        elif changed == "pool_swap":
            pools = fixture.mapping(altered["output_pools"])
            pools["inner"], pools["grid_control"] = pools["grid_control"], pools["inner"]
            altered["output_pools"] = pools
        else:
            field = "operator" if changed == "operator_digest" else "engineering"
            ref = fixture.mapping(altered[field])
            ref["sha256"] = "0" * 64
            altered[field] = ref
        with pytest.raises(ValueError, match="Owner-bound combined"):
            fixture.owner_check(altered)


@pytest.mark.parametrize("stage", ["barrier", "dispatch"])
def test_failed_stage_cannot_reopen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    root = private_dir(tmp_path / "control")
    manifest: dict[str, object] = {
        "control_root": str(root),
        "combined_id": "test",
        "owner": {},
    }

    def reject(_: dict[str, object]) -> list[dict[str, object]]:
        raise ValueError("Failed dependent preflight")

    monkeypatch.setattr(fixture, "fixture_barrier", reject)
    action = fixture.barrier if stage == "barrier" else fixture.dispatch
    with pytest.raises(ValueError, match="Failed dependent preflight"):
        action(manifest)
    with pytest.raises(FileExistsError):
        action(manifest)
    assert (root / (stage + "-claim.json")).exists()


def test_existing_combined_fault_blocks_dispatch(tmp_path: Path) -> None:
    root = private_dir(tmp_path / "control")
    fixture.record_fault(root, "capacity", ValueError("insufficient space"))
    with pytest.raises(ValueError, match="Prior combined fault"):
        fixture.dispatch({"control_root": str(root), "combined_id": "test", "owner": {}})


def test_activation_changes_only_anchored_entry_assignment() -> None:
    source = b'\nENABLED = False\ntext = b"ENABLED = False"\n'
    active = fixture.activate(source)
    assert active == b'\nENABLED = True\ntext = b"ENABLED = False"\n'
    with pytest.raises(ValueError, match="Exactly one"):
        fixture.activate(source + b"\nENABLED = False\n")


def closeout_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, object], Path, Path]:
    """Exercise ledger IO; manager/process behavior is outside this collector."""
    outer = private_dir(tmp_path / "control")
    grid_root = private_dir(tmp_path / "grid-control")
    owner: dict[str, object] = {"path": "already-verified-owner", "sha256": "a" * 64}
    entries: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []
    owned = [str(outer), str(grid_root)]
    for kind in fixture.KINDS:
        inner = private_dir(tmp_path / kind)
        control_root = private_dir(tmp_path / (kind + "-control"))
        owned.extend((str(inner), str(control_root)))
        spec: dict[str, object] = {
            "kind": kind,
            "owner": owner,
            "root": str(inner),
            "control_root": str(control_root),
            "owned_roots": owned,
        }
        path = inner / "admission.json"
        entries.append({"path": str(path), "sha256": save(path, spec)})
        rows.append({"kind": kind, "unit": kind + ".service"})
        for name in (
            "intent.json",
            "bound.json",
            "qualification-verdict.json",
            "terminal-before-stop.json",
        ):
            save(control_root / name, {"status": "qualified", "kind": kind})
    leases: dict[str, object] = {}
    for host, maximum in (("client", 10), ("server", 4)):
        path = outer / (host + "-open.json")
        leases[host] = {
            "path": str(path),
            "sha256": save(
                path,
                {
                    "start_monotonic_ns": 100,
                    "observed_monotonic_ns": 1000,
                    "maximum_cpu_count": maximum,
                    "boot_start": "boot",
                    "boot_observed": "boot",
                    "closed": False,
                    "combined_id": "collector-test",
                    "source": fixture.SOURCE,
                },
            ),
        }
    save(outer / "phase-status.json", {"qualification_exit": 0, "grid_exit": 0})
    save(outer / "qualification-barrier.json", {"fixtures": rows, "owner": owner})
    save(outer / "grid-dispatch-intent.json", {"unit": "grid.service", "source": fixture.SOURCE})
    save(
        grid_root / "supervisor-final.json",
        {
            "status": "provisional_complete",
            "unit": "grid.service",
            "cgroup_closed": True,
            "unit_cleanup_confirmed": True,
            "first_fault": None,
            "cleanup_errors": [],
            "diagnostic_outcome": "passed",
        },
    )
    manifest: dict[str, object] = {
        "control_root": str(outer),
        "combined_id": "collector-test",
        "owner": owner,
        "leases": leases,
        "fixtures": entries,
        "grid": {"control_root": str(grid_root)},
        "owned_roots": owned,
    }

    def loaded(path: Path, sha: str) -> dict[str, object]:
        assert fixture.digest(path.read_bytes()) == sha
        return fixture.mapping(json.loads(path.read_text()))

    monkeypatch.setattr(fixture, "load", loaded)
    monkeypatch.setattr(fixture, "fixture_barrier", lambda _: rows)
    monkeypatch.setattr(fixture, "output_census", lambda _: {"logical_bytes": 42})
    monkeypatch.setattr(
        os,
        "statvfs",
        lambda _: os.statvfs_result(
            (4096, 4096, 2**24, 2**24, 2**24, 2**24, 2**24, 2**24, 0, 255),
        ),
    )
    return manifest, outer, grid_root


@pytest.mark.parametrize("outcome", ["passed", "complete_negative"])
def test_closeout_retains_provisional_positive_and_negative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
) -> None:
    manifest, outer, grid = closeout_setup(tmp_path, monkeypatch)
    result = json.loads((grid / "supervisor-final.json").read_text())
    result["diagnostic_outcome"] = outcome
    save(grid / "supervisor-final.json", result)
    assert fixture.closeout(manifest)
    raw = (outer / "combined-closeout.json").read_bytes()
    summary = json.loads(raw)
    marker = json.loads(capsys.readouterr().out)
    assert summary["status"] == "pending_external_witness"
    assert summary["attempt_status"] == "provisional_complete"
    assert summary["provisional_diagnostic_outcome"] == outcome
    assert summary["accepted"] is False
    assert marker["ledger_retained"] is True
    assert marker["combined_closeout_sha256"] == fixture.digest(raw)


def test_closeout_qualification_failure_without_grid_still_inventories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, grid = closeout_setup(tmp_path, monkeypatch)
    save(outer / "phase-status.json", {"qualification_exit": 1, "grid_exit": None})
    (grid / "supervisor-final.json").unlink()
    (outer / "grid-dispatch-intent.json").unlink()
    original = save(outer / "first-fault.json", {"kind": "TimeoutError", "stage": "ready"})
    calls: list[str] = []

    def rejected(_: dict[str, object]) -> list[dict[str, object]]:
        raise ValueError("Qualification failed before GRID")

    def census(_: dict[str, object]) -> dict[str, object]:
        calls.append("census")
        return {"logical_bytes": 43}

    monkeypatch.setattr(fixture, "fixture_barrier", rejected)
    monkeypatch.setattr(fixture, "output_census", census)
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert calls == ["census"]
    assert summary["attempt_status"] == "incomplete"
    assert summary["provisional_diagnostic_outcome"] is None
    assert summary["phase_status"] == {"qualification_exit": 1, "grid_exit": None}
    assert summary["retained_receipts"]["grid/supervisor-final.json"]["status"] == "missing"
    assert summary["retained_receipts"]["combined/first-fault.json"]["sha256"] == original
    assert fixture.digest((outer / "first-fault.json").read_bytes()) == original
    assert summary["missing_records_do_not_prove_no_invocation"] is True


def test_closeout_missing_phase_status_cannot_be_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)
    (outer / "phase-status.json").unlink()
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["attempt_status"] == "incomplete"
    assert summary["phase_status"] is None
    assert any(row["stage"] == "combined/phase-status.json" for row in summary["issues"])


def test_closeout_failed_grid_preserves_fallback_and_fault_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, grid = closeout_setup(tmp_path, monkeypatch)
    save(outer / "phase-status.json", {"qualification_exit": 0, "grid_exit": 1})
    failed = {"status": "incomplete", "first_fault": {"kind": "OSError"}, "cleanup_errors": []}
    final_sha = save(grid / "supervisor-final.json", failed)
    fallback_sha = save(grid / "supervisor-fallback.json", failed)
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["attempt_status"] == "incomplete"
    assert summary["provisional_diagnostic_outcome"] is None
    assert summary["retained_receipts"]["grid/supervisor-final.json"]["sha256"] == final_sha
    assert summary["retained_receipts"]["grid/supervisor-fallback.json"]["sha256"] == fallback_sha


def test_closeout_collects_lease_census_and_capacity_faults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)
    save(outer / "client-open.json", {"later_start": "must not replace pinned evidence"})

    def failed_census(_: dict[str, object]) -> dict[str, object]:
        raise PermissionError("census denied")

    monkeypatch.setattr(fixture, "output_census", failed_census)
    monkeypatch.setattr(
        os,
        "statvfs",
        lambda _: os.statvfs_result(
            (4096, 4096, 0, 0, 0, 0, 0, 0, 0, 255),
        ),
    )
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["attempt_status"] == "incomplete"
    assert summary["output_census"] is None
    assert {"lease/client", "output_census", "capacity"} <= {r["stage"] for r in summary["issues"]}
    assert summary["retained_receipts"]["grid/supervisor-final.json"]["status"] == "retained"


@pytest.mark.parametrize("target", ["phase-status.json", "supervisor-final.json"])
def test_closeout_unreadable_record_does_not_skip_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)
    original_read = fixture.read

    def read_with_fault(path: Path, maximum: int = 128 * 1024) -> bytes:
        if path.name == target:
            raise PermissionError("retained read fault")
        return original_read(path, maximum)

    monkeypatch.setattr(fixture, "read", read_with_fault)
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["attempt_status"] == "incomplete"
    assert any(row["kind"] == "PermissionError" for row in summary["issues"])
    assert summary["output_census"] == {"logical_bytes": 42}


@pytest.mark.parametrize("partial", [False, True])
def test_closeout_write_failure_retains_first_fault_and_terminal_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    partial: bool,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)
    first_sha = save(outer / "first-fault.json", {"stage": "ready", "kind": "TimeoutError"})

    def write_failed(root: Path, name: str, value: dict[str, object]) -> str:
        assert root == outer and name == "combined-closeout.json"
        if partial:
            (root / name).write_bytes(b'{"partial":')
            (root / name).chmod(0o600)
        raise PermissionError("summary fsync failed")

    monkeypatch.setattr(fixture, "write", write_failed)
    assert not fixture.closeout(manifest)
    marker = json.loads(capsys.readouterr().out)
    assert marker["kind"] == "closeout_write_failed"
    assert marker["combined_closeout_sha256"] is None
    assert marker["ledger_retained"] is False
    fallback = marker["fallback_summary"]
    assert fallback["retained_receipts"]["combined/first-fault.json"]["sha256"] == first_sha
    assert any(row["stage"] == "combined_closeout_write" for row in fallback["issues"])
    assert fixture.digest((outer / "first-fault.json").read_bytes()) == first_sha
    if partial:
        assert (outer / "combined-closeout.json").read_bytes() == b'{"partial":'


def test_closeout_terminal_failure_leaves_durable_ledger_provisional(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)

    def broken_terminal(*args: object, **kwargs: object) -> None:
        raise BrokenPipeError("transport closed")

    monkeypatch.setattr("builtins.print", broken_terminal)
    assert not fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["status"] == "pending_external_witness"
    assert summary["accepted"] is False


def test_closeout_repeat_never_overwrites_earlier_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, _ = closeout_setup(tmp_path, monkeypatch)
    assert fixture.closeout(manifest)
    original = (outer / "combined-closeout.json").read_bytes()
    assert not fixture.closeout(manifest)
    assert (outer / "combined-closeout.json").read_bytes() == original


def test_closeout_missing_final_retains_real_supervisor_fault(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, outer, grid = closeout_setup(tmp_path, monkeypatch)
    (grid / "supervisor-final.json").unlink()
    primary = save(
        grid / "supervisor-first-fault.json",
        {
            "kind": "PermissionError",
            "stage": "command_cleanup",
        },
    )
    terminal = save(
        grid / "supervisor-terminal-before-stop.json",
        {
            "cgroup_closed": True,
            "cpu_ns": 100,
        },
    )
    assert fixture.closeout(manifest)
    summary = json.loads((outer / "combined-closeout.json").read_text())
    assert summary["attempt_status"] == "incomplete"
    receipts = summary["retained_receipts"]
    assert receipts["grid/supervisor-final.json"]["status"] == "missing"
    assert receipts["grid/supervisor-first-fault.json"]["sha256"] == primary
    assert receipts["grid/supervisor-terminal-before-stop.json"]["sha256"] == terminal
    assert any(row["stage"] == "grid/primary_fault" for row in summary["issues"])


@pytest.mark.parametrize("case", ["complete", "incomplete", "missing", "boot_changed", "late"])
def test_operator_final_observation_rejects_incomplete_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    operator = Path(__file__).resolve().parents[1] / "scripts/grid_q1_operator.sh"
    blocks = re.findall(r"<<'PY'\n(.*?)\nPY", operator.read_text(), re.DOTALL)
    assert len(blocks) == 3
    for block in blocks:
        compile(block, str(operator), "exec")
    control = private_dir(tmp_path / "control")
    anchor = control / "server-open.json"
    anchor_sha = save(
        anchor,
        {
            "combined_id": "operator-test",
            "source": fixture.SOURCE,
            "start_monotonic_ns": 100,
            "boot_start": "boot",
        },
    )
    manifest = tmp_path / "manifest.json"
    manifest_sha = save(
        manifest,
        {
            "leases": {"server": {"path": str(anchor), "sha256": anchor_sha}},
            "control_root": str(control),
        },
    )
    if case != "missing":
        save(
            control / "combined-closeout.json",
            {
                "attempt_status": "incomplete" if case == "incomplete" else "provisional_complete",
            },
        )
    real_read_text = Path.read_text

    def read_text(path: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if str(path) == "/proc/sys/kernel/random/boot_id":
            return "changed" if case == "boot_changed" else "boot"
        if str(path) == "/sys/devices/system/cpu/possible":
            return "0-3"
        return real_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(sys, "argv", ["-", str(manifest), manifest_sha, "0"])
    monkeypatch.setattr(time, "monotonic_ns", lambda: 2_400_000_000_101 if case == "late" else 200)
    with pytest.raises(SystemExit) as stopped:
        exec(compile(blocks[-1], str(operator), "exec"), {"__name__": "operator_test"})
    assert stopped.value.code == (0 if case == "complete" else 1)
    marker = json.loads(capsys.readouterr().out)
    assert marker["accepted"] is False
    assert marker["manifest_sha256"] == manifest_sha
