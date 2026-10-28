"""Synthetic sealed ledger/real SQLite primitives; no public or scientific calls."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from test_publication_handoff_store import Fixture, changed, prepared
from test_study_ledger import append, reserve

from strange_physics import publication_activation as activation
from strange_physics.candidate_store import read_sealed_handoff
from strange_physics.execution_publication_handoff import _export
from strange_physics.measured_publication_contracts import (
    NativePublicationRequest,
    PublicationAdmission,
    PublicationFile,
)
from strange_physics.publication_handoff_contracts import (
    HANDOFF_MATERIAL_NAMES,
    HandoffPublicationAdmission,
    PublicationHandoffBundle,
    PublicationHandoffOrigin,
    handoff_control_hold,
)
from strange_physics.publication_store import Extents, Store, digest, head, raw
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import NativeStudyLedger, NativeWorkFacts, StudyAttemptUpdate
from strange_physics.study_ledger import StudyLedgerError, summarize_study

__all__ = ["prepared"]


@dataclass
class Target:
    root: Path
    origin: PublicationHandoffOrigin
    admission: HandoffPublicationAdmission
    seed: NativeStudyLedger


def target(fixture: Fixture) -> Target:
    root = Path(fixture.seal.intent.destination.root)
    bundle = PublicationHandoffBundle(
        files=tuple(
            PublicationFile(
                name=n, path=str(root / (n + ".json")), sha256=digest(b"{}"), byte_count=2
            )
            for n in sorted(HANDOFF_MATERIAL_NAMES)
        ),
        journal_sha256=digest(b"0" * 100),
        journal_bytes=100,
        installation_raw_sha256=digest(b"{}"),
        installation_bytes=2,
        diagnostic_attempt_id="original-diagnostic",
    )
    old = fixture.after.records[-2].event
    assert isinstance(old, StudyAttemptUpdate) and old.facts is not None
    facts = NativeWorkFacts.model_validate_json(
        json.dumps(old.facts.model_dump(mode="json") | {"output_sha256": message_sha256(bundle)})
    )
    update = StudyAttemptUpdate.model_validate_json(
        json.dumps(old.model_dump(mode="json") | {"facts": facts.model_dump(mode="json")})
    )
    seed = append(append(fixture.before, update), handoff_control_hold(fixture.seal))
    seal = changed(
        fixture.seal,
        bundle_sha256=message_sha256(bundle),
        sealed_head_sha256=head(seed),
        seed_ledger_sha256=digest(raw(seed)),
        seed_ledger_bytes=len(raw(seed)),
    )
    origin = PublicationHandoffOrigin(seal=seal, bundle=bundle)
    admission = HandoffPublicationAdmission(
        version="strange-physics.handoff-publication-admission.v1",
        control=seal.intent.destination,
        source_root=str(fixture.store.root),
        origin_sha256=message_sha256(origin),
        seed_ledger_sha256=digest(raw(seed)),
    )
    with fixture.store.transaction():
        fixture.store.seal(fixture.before, seed, seal)
    for name, value in (
        ("origin.json", raw(origin)),
        ("seed-ledger.json", raw(seed)),
        ("admission.json", raw(admission)),
    ):
        (root / name).write_bytes(value)
        (root / name).chmod(0o600)
    return Target(root, origin, admission, seed)


def request(value: Target, **changes: Any) -> NativePublicationRequest:
    return NativePublicationRequest.model_validate_json(
        json.dumps(
            {
                "mode": "scored",
                "event_id": "publication",
                "cell_id": value.origin.seal.intent.cell_id,
                "attempt_id": "publication-attempt",
                "ticket": 0,
                "expected_revision": len(value.seed.records),
                "expected_head_sha256": head(value.seed),
                "journal_path": str(value.root / "journal.sqlite3"),
                "journal_sha256": value.origin.bundle.journal_sha256,
                "files": [f.model_dump(mode="json") for f in value.origin.bundle.files],
                "diagnostic_attempt_id": value.origin.bundle.diagnostic_attempt_id,
                "cpu_reservation_ns": 30_000_000_000,
                "artifact_reservation_bytes": 23_592_960,
                "output_limit_bytes": 2 * 1024**2,
                "wall_limit_ns": 30_000_000_000,
            }
            | changes
        )
    )


def open_target(value: Target) -> Store:
    return Store(
        value.root, value.admission, raw(value.seed), Extents(value.root), origin=value.origin
    )


def test_readonly_seal_requires_commit_and_preserves_source(prepared: Fixture) -> None:
    with pytest.raises(StudyLedgerError, match="candidate_store_unsealed"):
        read_sealed_handoff(prepared.store.root, prepared.store.admission)
    value = target(prepared)
    path = prepared.store.path
    before = path.read_bytes()
    seal, data = read_sealed_handoff(prepared.store.root, prepared.store.admission)
    assert seal == value.origin.seal and data == raw(value.seed)
    assert path.read_bytes() == before


def test_admission_roundtrip_and_legacy_bytes(prepared: Fixture) -> None:
    value = target(prepared)
    assert activation.read_publication_admission(raw(value.admission)) == value.admission
    legacy = PublicationAdmission(
        control=value.admission.control, seed_ledger_sha256=value.admission.seed_ledger_sha256
    )
    assert set(json.loads(raw(legacy))) == {"control", "seed_ledger_sha256"}
    assert type(activation.read_publication_admission(raw(legacy))) is PublicationAdmission


@pytest.mark.parametrize("kind", ["missing_origin", "stripped_admission"])
def test_handoff_cannot_initialize_as_legacy(prepared: Fixture, kind: str) -> None:
    value = target(prepared)
    admission: PublicationAdmission = value.admission
    if kind == "stripped_admission":
        admission = PublicationAdmission(
            control=admission.control, seed_ledger_sha256=admission.seed_ledger_sha256
        )
    with pytest.raises(StudyLedgerError, match="publication_origin"):
        Store(value.root, admission, raw(value.seed), Extents(value.root))
    assert not (value.root / "publication.sqlite3").exists()
    assert not (value.root / "store-created").exists()


@pytest.mark.parametrize("cut", ["fresh", "marker", "empty"])
def test_authenticated_initialization_cuts(prepared: Fixture, cut: str) -> None:
    value = target(prepared)
    if cut != "fresh":
        marker = value.root / "store-created"
        marker.write_bytes(digest(raw(value.admission)).encode())
        marker.chmod(0o600)
    if cut == "empty":
        path = value.root / "publication.sqlite3"
        path.write_bytes(b"")
        path.chmod(0o600)
    store = open_target(value)
    try:
        assert store.db.execute("PRAGMA user_version").fetchone() == (2,)
        assert raw(store.ledger()) == raw(value.seed)
        assert store.db.execute("SELECT data FROM origin WHERE id=1").fetchone() == (
            raw(value.origin),
        )
    finally:
        store.close()
    reopened = open_target(value)
    reopened.close()


@pytest.mark.parametrize("change", ["missing", "digest", "version"])
def test_persisted_origin_cannot_be_removed_or_downgraded(prepared: Fixture, change: str) -> None:
    value = target(prepared)
    store = open_target(value)
    if change == "missing":
        store.db.execute("DELETE FROM origin")
    elif change == "digest":
        store.db.execute("UPDATE origin SET digest=?", ("f" * 64,))
    else:
        store.db.execute("PRAGMA user_version=1")
    store.close()
    with pytest.raises(StudyLedgerError, match="publication_origin_identity|store_corrupt"):
        open_target(value)


def test_complete_target_does_not_read_source(
    prepared: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = target(prepared)
    verified: list[str] = []
    monkeypatch.setattr(
        activation, "_installation", lambda root, origin: verified.append(origin.seal.bundle_sha256)
    )
    with activation.publication_authority(value.root, value.admission) as origin:
        assert origin == value.origin
        store = open_target(value)
        store.close()

    def forbidden(*args: object) -> None:
        raise AssertionError("completed target must not consult source")

    monkeypatch.setattr(activation, "read_sealed_handoff", forbidden)
    with activation.publication_authority(value.root, value.admission) as origin:
        assert origin == value.origin
        store = open_target(value)
        store.close()
    assert verified == [value.origin.seal.bundle_sha256] * 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("cpu_reservation_ns", 30_000_000_001),
        ("artifact_reservation_bytes", 23_592_961),
        ("output_limit_bytes", 2 * 1024**2 + 1),
        ("wall_limit_ns", 30_000_000_001),
        ("journal_sha256", "e" * 64),
        ("diagnostic_attempt_id", "wrong-attempt"),
    ],
)
def test_sealed_request_ceiling_and_original_identity(
    prepared: Fixture, field: str, value: Any
) -> None:
    fixture = target(prepared)
    good = request(fixture)
    activation.publication_request_bounds(fixture.origin, good, fixture.seed)
    with pytest.raises(StudyLedgerError, match="publication_handoff_bounds"):
        activation.publication_request_bounds(
            fixture.origin, request(fixture, **{field: value}), fixture.seed
        )


@pytest.mark.parametrize("deficit", [0, 1])
def test_actual_control_counted_once_and_future_work_protected(
    prepared: Fixture, deficit: int
) -> None:
    value = target(prepared)
    held = append(
        value.seed,
        reserve(
            "publication-attempt",
            phase="accounting",
            operation="accounting",
            cpu_reservation_ns=30_000_000_000,
            artifact_reservation_bytes=23_592_960,
        ),
    )
    required = 2 * 23_592_960 + 16 * 1024**2
    margin = summarize_study(held).budget.remaining_artifact_bytes - required
    held = append(
        held,
        reserve(
            "unrelated-unknown",
            phase="accounting",
            operation="accounting",
            artifact_reservation_bytes=margin + deficit,
        ),
    )
    ticket = value.root / "ticket-0"
    ticket.write_bytes(b"{}")
    ticket.chmod(0o600)
    if deficit:
        with pytest.raises(StudyLedgerError, match="publication_handoff_headroom"):
            activation.publication_remaining_capacity(value.root, value.origin, held)
    else:
        activation.publication_remaining_capacity(value.root, value.origin, held)


def test_export_partial_and_one_below_deny_before_write(tmp_path: Path) -> None:
    meter = Extents(tmp_path)
    path = tmp_path / "export"
    with pytest.raises(StudyLedgerError, match="handoff_copy_headroom"):
        _export(meter, path, b"abcd", 0, 3)
    assert not path.exists() and meter.total == 0
    _export(meter, path, b"abcd", 0, 4)
    _export(meter, path, b"abcd", 0, 4)
    assert meter.total == 4
    path.write_bytes(b"abc")
    with pytest.raises(StudyLedgerError, match="handoff_export_conflict"):
        _export(meter, path, b"abcd", 0, 4)
    assert path.read_bytes() == b"abc"


@pytest.mark.parametrize("hot", [False, True])
def test_hot_recovery_is_denied_before_open(
    prepared: Fixture, monkeypatch: pytest.MonkeyPatch, hot: bool
) -> None:
    value = target(prepared)
    store = open_target(value)
    store.close()
    path = value.root / "publication.sqlite3-journal"
    original = path.read_bytes()
    assert original[:8] == b"\x00" * 8
    if hot:
        altered = bytes.fromhex("d9d505f920a163d7") + original[8:]
        path.write_bytes(altered)

        def forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError("hot activation must be denied before SQLite open")

        monkeypatch.setattr(sqlite3, "connect", forbidden)
        with pytest.raises(StudyLedgerError, match="publication_activation_recovery_required"):
            open_target(value)
        assert path.read_bytes() == altered
    else:
        reopened = open_target(value)
        reopened.close()
