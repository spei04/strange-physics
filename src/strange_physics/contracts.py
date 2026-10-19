"""Public, versioned messages. Hidden world parameters do not belong here."""

from __future__ import annotations

import math
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
Number = Annotated[float, Field(allow_inf_nan=False)]
Vector = tuple[Number, Number]


class Message(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, validate_default=True, allow_inf_nan=False
    )


class Anchor(Message):
    id: Identifier
    position: Vector


class Connection(Message):
    a: Identifier
    b: Identifier


class Structure(Message):
    particle_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=8)]
    anchors: Annotated[tuple[Anchor, ...], Field(max_length=8)] = ()
    connections: Annotated[tuple[Connection, ...], Field(max_length=120)] = ()

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        ids = (*self.particle_ids, *(anchor.id for anchor in self.anchors))
        if len(ids) != len(set(ids)):
            raise ValueError("particle and anchor identities must be unique")
        edges: set[frozenset[str]] = set()
        for connection in self.connections:
            if connection.a not in ids or connection.b not in ids:
                raise ValueError("connection endpoints must exist")
            edge = frozenset((connection.a, connection.b))
            if len(edge) != 2 or edge in edges:
                raise ValueError(
                    "connections must be unique and cannot connect an object to itself"
                )
            if not edge.intersection(self.particle_ids):
                raise ValueError("a connection must include a movable particle")
            edges.add(edge)
        return self


class Sampling(Message):
    duration: Annotated[float, Field(gt=0, le=10)] = 2.0
    dt: Annotated[float, Field(ge=0.0001, le=0.05)] = 0.01
    sample_interval: Annotated[float, Field(gt=0, le=1)] = 0.05
    position_noise: Annotated[float, Field(ge=0, le=0.1)] = 0.0
    velocity_noise: Annotated[float, Field(ge=0, le=0.1)] = 0.0

    @model_validator(mode="after")
    def validate_grid(self) -> Self:
        ratios = (
            self.duration / self.dt,
            self.sample_interval / self.dt,
            self.duration / self.sample_interval,
        )
        if any(
            ratio < 1 or not math.isclose(ratio, round(ratio), rel_tol=0, abs_tol=1e-8)
            for ratio in ratios
        ):
            raise ValueError(
                "duration and observation interval must align with the integration grid"
            )
        if round(ratios[0]) > 20_000 or round(ratios[2]) > 2_000:
            raise ValueError("sampling exceeds the supported work or observation limit")
        return self


class Limits(Message):
    position_norm: Annotated[float, Field(gt=0, le=10)] = 2.0
    velocity_norm: Annotated[float, Field(gt=0, le=10)] = 2.0
    impulse_norm: Annotated[float, Field(gt=0, le=10)] = 1.0
    min_mass: Annotated[float, Field(gt=0, le=10)] = 0.5
    max_mass: Annotated[float, Field(gt=0, le=10)] = 2.0

    @model_validator(mode="after")
    def validate_mass_range(self) -> Self:
        if self.min_mass > self.max_mass:
            raise ValueError("minimum mass exceeds maximum mass")
        return self


class ParticleInitial(Message):
    id: Identifier
    position: Vector
    velocity: Vector = (0.0, 0.0)
    mass: Annotated[float, Field(gt=0)] = 1.0


class Impulse(Message):
    particle_id: Identifier
    vector: Vector


class Experiment(Message):
    schema_version: Literal["strange-physics.experiment.v1"] = "strange-physics.experiment.v1"
    particles: Annotated[tuple[ParticleInitial, ...], Field(min_length=1, max_length=8)]
    impulse: Impulse | None = None

    @model_validator(mode="after")
    def validate_identities(self) -> Self:
        ids = tuple(particle.id for particle in self.particles)
        if len(set(ids)) != len(ids):
            raise ValueError("initial particle identities must be unique")
        if self.impulse and self.impulse.particle_id not in ids:
            raise ValueError("the impulse must target a movable particle in this experiment")
        return self


class ExperimentSpace(Message):
    schema_version: Literal["strange-physics.space.v1"] = "strange-physics.space.v1"
    structure: Structure
    sampling: Sampling
    limits: Limits = Limits()
    budget: Annotated[int, Field(ge=1, le=10_000)] = 40
    calibration_experiments: Annotated[int, Field(ge=0)] = 4

    @model_validator(mode="after")
    def validate_calibration(self) -> Self:
        if self.calibration_experiments > self.budget:
            raise ValueError("calibration cannot exceed the experiment budget")
        return self

    def validate_experiment(self, experiment: Experiment) -> None:
        if tuple(p.id for p in experiment.particles) != self.structure.particle_ids:
            raise ValueError("particles must match the published identities and order")
        for particle in experiment.particles:
            if math.hypot(*particle.position) > self.limits.position_norm:
                raise ValueError("initial position exceeds the legal radius")
            if math.hypot(*particle.velocity) > self.limits.velocity_norm:
                raise ValueError("initial velocity exceeds the legal radius")
            if not self.limits.min_mass <= particle.mass <= self.limits.max_mass:
                raise ValueError("mass is outside the legal range")
        if experiment.impulse and math.hypot(*experiment.impulse.vector) > self.limits.impulse_norm:
            raise ValueError("initial impulse exceeds the legal radius")


class Frame(Message):
    time: Annotated[float, Field(ge=0)]
    positions: Annotated[tuple[Vector, ...], Field(min_length=1, max_length=8)]
    velocities: Annotated[tuple[Vector, ...], Field(min_length=1, max_length=8)]

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        if len(self.positions) != len(self.velocities):
            raise ValueError("position and velocity counts must match")
        return self


class Trajectory(Message):
    frames: Annotated[tuple[Frame, ...], Field(min_length=2, max_length=2_001)]

    @model_validator(mode="after")
    def validate_frames(self) -> Self:
        count = len(self.frames[0].positions)
        if self.frames[0].time != 0:
            raise ValueError("the initial observation must be at time zero")
        for previous, current in zip(self.frames, self.frames[1:], strict=False):
            if current.time <= previous.time or len(current.positions) != count:
                raise ValueError("frames need increasing times and consistent particle counts")
        return self


class ExperimentRecord(Message):
    operation_id: Identifier
    index: Annotated[int, Field(ge=0)]
    experiment: Experiment
    status: Literal["completed", "failed"]
    trajectory: Trajectory | None = None
    error: Literal["simulation_failed"] | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        if self.status == "completed":
            if self.trajectory is None or self.error is not None:
                raise ValueError("completed experiments require a trajectory and no error")
            if any(
                len(frame.positions) != len(self.experiment.particles)
                for frame in self.trajectory.frames
            ):
                raise ValueError("trajectory particle count must match the request")
        elif self.trajectory is not None or self.error != "simulation_failed":
            raise ValueError("failed experiments require an error and no trajectory")
        return self


class Checkpoint(Message):
    schema_version: Literal["strange-physics.checkpoint.v1"] = "strange-physics.checkpoint.v1"
    agent_id: Identifier
    through_index: Annotated[int, Field(ge=-1)]
    state: dict[str, JsonValue]


class ObservationBundle(Message):
    schema_version: Literal["strange-physics.observations.v1"] = "strange-physics.observations.v1"
    run_id: Identifier
    engine_version: str
    engine_fingerprint: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    space: ExperimentSpace
    records: Annotated[tuple[ExperimentRecord, ...], Field(max_length=10_000)]

    @model_validator(mode="after")
    def validate_records(self) -> Self:
        if len(self.records) > self.space.budget:
            raise ValueError("record count exceeds budget")
        keys: set[str] = set()
        for index, record in enumerate(self.records):
            if record.index != index or record.operation_id in keys:
                raise ValueError("records must be contiguous with unique operation identities")
            self.space.validate_experiment(record.experiment)
            if record.trajectory:
                sampling = self.space.sampling
                expected_count = round(sampling.duration / sampling.sample_interval) + 1
                if len(record.trajectory.frames) != expected_count:
                    raise ValueError("trajectory does not match the published observation count")
                for frame_index, frame in enumerate(record.trajectory.frames):
                    if not math.isclose(
                        frame.time, frame_index * sampling.sample_interval, rel_tol=0, abs_tol=1e-9
                    ):
                        raise ValueError(
                            "trajectory does not match the published observation times"
                        )
            keys.add(record.operation_id)
        return self
