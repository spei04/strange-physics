"""Resolve fixed comparison stages from this store's retained paid authority.

No live input path or live Journal is consulted. Fresh scoring observes the
original prediction files and no-closure state; a closed score's paid replay
uses its authenticated original transport witness and ledger prefix instead.
Later retries or output appearance cannot rewrite that historical score.
"""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from strange_physics.candidate_execution_contracts import REQUEST_BYTES
from strange_physics.candidate_store import CandidateStore
from strange_physics.comparison_stage_binding import (
    bind_prediction_material,
    bind_preparation_material,
    bind_score_material,
    comparison_prediction_input,
)
from strange_physics.native_prediction_contracts import (
    NativePredictionInput,
    NativePredictionResult,
    parse_native_prediction_result,
    validate_native_prediction_result,
)
from strange_physics.native_scoring_contracts import (
    NativePreparationResult,
    NativeProbeOutcome,
)
from strange_physics.native_spring_contracts import NativeCandidateInput, NativeCandidateResult
from strange_physics.native_stage_execution_contracts import (
    NativeComparisonPreparationInput,
    NativePredictionReference,
    NativePredictionRequest,
    NativePreparationRequest,
    NativeScoreRequest,
    parse_comparison_prediction_input,
    parse_comparison_preparation_input,
    parse_comparison_score_input,
)
from strange_physics.publication_store import Extents, digest, raw, regular
from strange_physics.research_contracts import message_sha256
from strange_physics.study_contracts import (
    NativeStudyLedger,
    NativeStudyManifest,
    StudyAttemptReservation,
    StudyAttemptUpdate,
)
from strange_physics.study_execution_contracts import (
    NativeComparisonCandidateRequest,
    NativeFreezeInput,
)
from strange_physics.study_ledger import StudyLedgerError, study_manifest
from strange_physics.workflow_io import read_bytes

if TYPE_CHECKING:
    from strange_physics.measured_candidates import (
        ExecutionInput,
        ExecutionReceipt,
        ExecutionRequest,
        ExecutionResult,
    )

type ComparisonStageRequest = (
    NativePreparationRequest | NativePredictionRequest | NativeScoreRequest
)
type ParentOperation = Literal["freeze", "comparison_candidate", "preparation", "prediction"]


@dataclass
class RetainedStageWitness:
    """Bounded raw witnesses remain stable through the caller's closure COMMIT."""

    files: dict[Path, tuple[int, str] | None] = field(default_factory=dict)

    def remember(self, path: Path, value: bytes | None) -> None:
        identity = None if value is None else (len(value), digest(value))
        if path in self.files and self.files[path] != identity:
            raise StudyLedgerError("comparison_retained_changed")
        self.files[path] = identity

    def read(self, path: Path, limit: int) -> bytes:
        value = read_bytes(path, limit=limit)
        self.remember(path, value)
        return value

    def recheck(self) -> None:
        for path, identity in self.files.items():
            if identity is None:
                # Permission, symlink and I/O failures are never absence evidence.
                if regular(path, missing=True) is not None:
                    raise StudyLedgerError("comparison_retained_changed")
            else:
                length, sha256 = identity
                value = read_bytes(path, limit=length)
                if (len(value), digest(value)) != (length, sha256):
                    raise StudyLedgerError("comparison_retained_changed")


@dataclass(frozen=True)
class _Closed:
    request: ExecutionRequest
    receipt: ExecutionReceipt
    actual: ExecutionInput
    result: ExecutionResult
    input_raw: bytes
    original: NativeStudyLedger


@dataclass
class _Resolver:
    store: CandidateStore
    view: NativeStudyLedger
    cell_id: str
    meter: Extents
    scope: ExitStack
    witness: RetainedStageWitness = field(default_factory=RetainedStageWitness)
    _validated_view: NativeStudyLedger | None = field(default=None, init=False, repr=False)
    _manifest: NativeStudyManifest | None = field(default=None, init=False, repr=False)

    def manifest(self) -> NativeStudyManifest:
        """Validate this immutable view once; replacing the view invalidates reuse."""
        if self._validated_view is not self.view:
            # Never use model_construct: later prefix-head joins rely on this full
            # canonical chain validation as well as the semantic manifest scan.
            validated = NativeStudyLedger(plan=self.view.plan, records=self.view.records)
            manifest = study_manifest(validated)
            self._validated_view = self.view
            self._manifest = manifest
        assert self._manifest is not None
        return self._manifest

    def closed(self, logical_id: str, receipt_sha256: str, operation: ParentOperation) -> _Closed:
        # The measured supervisor owns the concrete closure format and validators.
        # Import lazily to keep its fixed entrypoints free of an import cycle.
        from strange_physics import measured_candidates as measured

        row = self.store.db.execute(
            "SELECT length(request) FROM closures WHERE logical_id=?", (logical_id,)
        ).fetchone()
        if row is None or not 0 < row[0] <= REQUEST_BYTES:
            raise StudyLedgerError("comparison_parent_missing")
        saved_raw = self.store.db.execute(
            "SELECT request FROM closures WHERE logical_id=?", (logical_id,)
        ).fetchone()[0]
        saved = measured._request(saved_raw, operation)
        if (
            saved.logical_id != logical_id
            or saved.mode != "execute"
            or saved.ticket
            >= self.store.admission.control.tickets - self.store.admission.control.recovery_tickets
            or operation != "freeze"
            and (saved.phase != "comparison" or saved.cell_id != self.cell_id)
        ):
            raise StudyLedgerError("comparison_parent_identity")
        ticket = self.witness.read(
            self.store.root / f"candidate-ticket-{saved.ticket}", REQUEST_BYTES
        )
        if ticket != saved_raw:
            raise StudyLedgerError("comparison_ticket_identity")
        if operation != "freeze":
            measured._bind_frozen_context(self.manifest(), saved, self.store.admission.control)
        retained = measured._closure(self.store, saved, self.view)
        if retained is None:
            raise StudyLedgerError("comparison_parent_missing")
        receipt, input_raw, result_raw, original = retained
        if len(result_raw) > saved.output_limit_bytes:
            raise StudyLedgerError("comparison_parent_output_bound")
        control = self.store.admission.control
        if digest(raw(receipt)) != receipt_sha256 or (
            receipt.source_commit,
            receipt.installation_sha256,
        ) != (control.source_commit, control.installation_sha256):
            raise StudyLedgerError("comparison_parent_identity")
        actual, result = measured._input(input_raw, saved), measured._result(result_raw, saved)
        measured._check_engine(actual, control.engine_fingerprint)
        measured._validate(result, actual, saved.attempt_id)
        if (message_sha256(actual), measured._config(actual)) != (
            saved.input_sha256,
            saved.config_sha256,
        ):
            raise StudyLedgerError("comparison_parent_identity")
        updates = [
            r.event
            for r in self.view.records
            if isinstance(r.event, StudyAttemptUpdate) and r.event.attempt_id == saved.attempt_id
        ]
        if not updates or updates[-1].state != result.facts.outcome:
            raise StudyLedgerError("comparison_parent_unknown")
        self.witness.remember(self.store.root / f"candidate-input-{saved.ticket}", input_raw)
        self.witness.remember(self.store.root / f"candidate-output-{saved.ticket}", result_raw)
        return _Closed(saved, receipt, actual, result, input_raw, original)

    def preparation_context(self, material: NativeComparisonPreparationInput) -> NativeFreezeInput:
        from strange_physics import measured_candidates as measured

        candidate = self.closed(
            material.candidate_logical_id, material.candidate_receipt_sha256, "comparison_candidate"
        )
        assert isinstance(candidate.request, NativeComparisonCandidateRequest)
        assert isinstance(candidate.actual, NativeCandidateInput)
        assert isinstance(candidate.result, NativeCandidateResult)
        candidate_material = measured._comparison_input(candidate.input_raw)
        frozen = self.closed(
            candidate_material.freeze_logical_id,
            candidate_material.freeze_receipt_sha256,
            "freeze",
        )
        assert isinstance(frozen.actual, NativeFreezeInput)
        capture = measured._bind_comparison(
            self.store,
            candidate.request,
            candidate.input_raw,
            candidate.original,
            self.meter,
            self.scope,
            replayed=True,
        )
        # Bind the actual captured reader and retain the same raw identity through closure.
        self.witness.read(capture.path, capture.byte_count)
        capture.recheck()
        bind_preparation_material(
            material.context,
            candidate=candidate.actual,
            result=candidate.result,
            attempt_id=candidate.request.attempt_id,
            freeze=frozen.actual,
            cell_id=self.cell_id,
        )
        return frozen.actual

    def preparation(
        self, logical_id: str, receipt_sha256: str
    ) -> tuple[NativeComparisonPreparationInput, NativePreparationResult, str, NativeFreezeInput]:
        parent = self.closed(logical_id, receipt_sha256, "preparation")
        assert isinstance(parent.request, NativePreparationRequest)
        assert isinstance(parent.result, NativePreparationResult)
        material = parse_comparison_preparation_input(parent.input_raw)
        _before_feedback(parent.original, self.cell_id)
        frozen = self.preparation_context(material)
        return material, parent.result, parent.request.attempt_id, frozen

    def prediction(
        self,
        reference: NativePredictionReference,
        *,
        preparation_logical_id: str,
        preparation_receipt_sha256: str,
        expected: NativePredictionInput,
        preparation: NativePreparationResult,
        probe_index: int,
        historical_transport: bool,
    ) -> NativeProbeOutcome:
        from strange_physics import measured_candidates as measured

        control = self.store.admission.control
        if reference.ticket >= control.tickets - control.recovery_tickets:
            raise StudyLedgerError("comparison_prediction_ticket")
        ticket_raw = self.witness.read(
            self.store.root / f"candidate-ticket-{reference.ticket}", REQUEST_BYTES
        )
        if digest(ticket_raw) != reference.request_raw_sha256:
            raise StudyLedgerError("comparison_prediction_ticket")
        saved = measured._request(ticket_raw, "prediction")
        assert isinstance(saved, NativePredictionRequest)
        if (
            saved.logical_id,
            saved.attempt_id,
            saved.ticket,
            saved.mode,
            saved.phase,
            saved.cell_id,
        ) != (
            reference.logical_id,
            reference.attempt_id,
            reference.ticket,
            "execute",
            "comparison",
            self.cell_id,
        ):
            raise StudyLedgerError("comparison_prediction_ticket")
        measured._bind_frozen_context(self.manifest(), saved, control)
        if (saved.input_sha256, saved.config_sha256) != (
            message_sha256(expected),
            message_sha256(expected.config),
        ):
            raise StudyLedgerError("comparison_prediction_input")
        self.prediction_reservation(saved)
        input_raw = self.witness.read(
            self.store.root / f"candidate-input-{saved.ticket}", measured._input_limit(saved)
        )
        if (len(input_raw), digest(input_raw)) != (saved.input_bytes, saved.input_raw_sha256):
            raise StudyLedgerError("comparison_prediction_input")
        material = parse_comparison_prediction_input(input_raw)
        if (
            material.preparation_logical_id,
            material.preparation_receipt_sha256,
            material.probe_index,
            message_sha256(material.prediction),
        ) != (
            preparation_logical_id,
            preparation_receipt_sha256,
            probe_index,
            message_sha256(expected),
        ):
            raise StudyLedgerError("comparison_prediction_input")
        result: NativePredictionResult | None = None
        if reference.status == "result":
            assert reference.receipt_sha256 is not None
            parent = self.closed(reference.logical_id, reference.receipt_sha256, "prediction")
            assert isinstance(parent.result, NativePredictionResult)
            if (
                parent.request.attempt_id != saved.attempt_id
                or parent.request.ticket != saved.ticket
                or parent.receipt.result_raw_sha256 != reference.output_raw_sha256
            ):
                raise StudyLedgerError("comparison_prediction_result")
            result = parent.result
        else:
            self.unavailable(reference, saved, expected, historical_transport=historical_transport)
        protocol = preparation.payload.protocol
        if protocol is None:
            raise StudyLedgerError("comparison_preparation_unavailable")
        probe = protocol.probes[probe_index]
        return NativeProbeOutcome(
            probe_id=probe.probe_id,
            request_sha256=message_sha256(probe.request),
            attempt_id=saved.attempt_id,
            status=reference.status,
            result=result,
        )

    def prediction_reservation(self, saved: NativePredictionRequest) -> None:
        """A consumed ticket alone proves neither admitted work nor its original input."""
        if saved.expected_revision >= len(self.view.records):
            raise StudyLedgerError("comparison_prediction_reservation")
        self.manifest()  # Validate the full exact view before reusing its chain link.
        before_head = self.view.records[saved.expected_revision].previous_sha256
        expected = StudyAttemptReservation(
            attempt_id=saved.attempt_id,
            phase=saved.phase,
            cell_id=saved.cell_id,
            operation="prediction",
            config_sha256=saved.config_sha256,
            input_sha256=saved.input_sha256,
            retry_of=saved.retry_of,
            cpu_reservation_ns=saved.cpu_reservation_ns,
            artifact_reservation_bytes=saved.artifact_reservation_bytes,
            purchase=None,
        )
        reservations = [
            r.event
            for r in self.view.records
            if isinstance(r.event, StudyAttemptReservation)
            and r.event.attempt_id == saved.attempt_id
        ]
        if (
            before_head != saved.expected_head_sha256
            or self.view.records[saved.expected_revision].event != expected
            or reservations != [expected]
        ):
            raise StudyLedgerError("comparison_prediction_reservation")

    def unavailable(
        self,
        reference: NativePredictionReference,
        saved: NativePredictionRequest,
        expected: NativePredictionInput,
        *,
        historical_transport: bool,
    ) -> None:
        updates = [
            r.event
            for r in self.view.records
            if isinstance(r.event, StudyAttemptUpdate) and r.event.attempt_id == saved.attempt_id
        ]
        if updates and (
            updates[-1].state not in ("running", "unknown")
            or any(update.facts is not None for update in updates)
        ):
            raise StudyLedgerError("comparison_prediction_transport")
        if historical_transport:
            # Only the supervisor may select this branch after validating this score's
            # existing receipt/input/result and original ledger prefix. That original
            # score binds its observed absence; later retry closures or file
            # appearance cannot change it. Invalid transport still needs its
            # original retained bytes, checked below, never a retry's output.
            if reference.status == "missing":
                return
        elif (
            self.store.db.execute(
                "SELECT 1 FROM closures WHERE logical_id=?", (saved.logical_id,)
            ).fetchone()
            is not None
        ):
            raise StudyLedgerError("comparison_prediction_transport")
        output = self.store.root / f"candidate-output-{saved.ticket}"
        info = regular(output, missing=True)
        if reference.status == "missing":
            if info is not None:
                raise StudyLedgerError("comparison_prediction_transport")
            self.witness.remember(output, None)
            return
        if info is None:
            raise StudyLedgerError("comparison_prediction_transport")
        output_raw = self.witness.read(output, saved.output_limit_bytes)
        if digest(output_raw) != reference.output_raw_sha256:
            raise StudyLedgerError("comparison_prediction_transport")
        try:
            result = parse_native_prediction_result(output_raw)
            validate_native_prediction_result(result, expected, attempt_id=saved.attempt_id)
        except ValueError:
            # Only a typed parse/binding failure is invalid transport. Filesystem and
            # store failures escaped above. A valid unclosed result is incomplete,
            # not an invalid output and not permission to manufacture a receipt.
            return
        raise StudyLedgerError("comparison_prediction_unclosed_result")


def _before_feedback(view: NativeStudyLedger, cell_id: str) -> None:
    # Any earlier evaluator reservation may have exposed feedback, including an
    # interrupted attempt. Selection is fixed before that boundary, not certified MAP.
    if any(
        isinstance(record.event, StudyAttemptReservation)
        and record.event.cell_id == cell_id
        and record.event.operation in ("scoring", "classical_diagnostic")
        for record in view.records
    ):
        raise StudyLedgerError("comparison_selection_after_feedback")


def bind_retained_stage(
    store: CandidateStore,
    request: ComparisonStageRequest,
    input_raw: bytes,
    view: NativeStudyLedger,
    meter: Extents,
    scope: ExitStack,
    *,
    replayed: bool,
) -> RetainedStageWitness:
    """Resolve concrete original authorities within the caller's charged work clock."""
    if request.phase != "comparison" or request.cell_id is None:
        raise StudyLedgerError("comparison_stage_scope")
    resolver = _Resolver(store, view, request.cell_id, meter, scope)
    if isinstance(request, NativePreparationRequest):
        _before_feedback(view, request.cell_id)
        resolver.preparation_context(parse_comparison_preparation_input(input_raw))
    elif isinstance(request, NativePredictionRequest):
        material = parse_comparison_prediction_input(input_raw)
        parent, preparation, attempt_id, _ = resolver.preparation(
            material.preparation_logical_id, material.preparation_receipt_sha256
        )
        bind_prediction_material(
            material.prediction,
            context=parent.context,
            preparation=preparation,
            preparation_attempt_id=attempt_id,
            probe_index=material.probe_index,
        )
    else:
        scoring = parse_comparison_score_input(input_raw)
        parent, preparation, attempt_id, frozen = resolver.preparation(
            scoring.preparation_logical_id, scoring.preparation_receipt_sha256
        )
        # Validate/reconstruct the prepared protocol once; each expected predictor
        # input remains a fully validated bounded model, with no persisted copy.
        first = comparison_prediction_input(
            parent.context, preparation, preparation_attempt_id=attempt_id, probe_index=0
        )
        protocol = preparation.payload.protocol
        assert protocol is not None
        expected_inputs = tuple(
            NativePredictionInput(
                model=first.model,
                candidate_config=first.candidate_config,
                request=probe.request,
                config=first.config,
            )
            for probe in protocol.probes
        )
        outcomes = tuple(
            resolver.prediction(
                reference,
                preparation_logical_id=scoring.preparation_logical_id,
                preparation_receipt_sha256=scoring.preparation_receipt_sha256,
                expected=expected_inputs[index],
                preparation=preparation,
                probe_index=index,
                historical_transport=replayed,
            )
            for index, reference in enumerate(scoring.predictions)
        )
        bind_score_material(
            scoring.scoring,
            context=parent.context,
            preparation=preparation,
            preparation_attempt_id=attempt_id,
            predictions=outcomes,
            freeze=frozen,
            cell_id=request.cell_id,
            scoring_attempt_id=request.attempt_id,
        )
    resolver.witness.recheck()
    return resolver.witness
