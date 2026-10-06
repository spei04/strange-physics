"""Private world definitions and development fixtures, not a frozen evaluation suite."""

from __future__ import annotations

from typing import Annotated, Literal, Self

import numpy as np
from pydantic import Field, model_validator

from strange_physics.contracts import (
    Anchor,
    Connection,
    ExperimentSpace,
    Message,
    Sampling,
    Structure,
)
from strange_physics.laws import LawSpec


class WorldDefinition(Message):
    schema_version: Literal["strange-physics.world.v1"] = "strange-physics.world.v1"
    space: ExperimentSpace
    noise_seed: Annotated[int, Field(ge=0, lt=2**64)]
    initial_law: LawSpec
    changed_law: LawSpec | None = None
    change_after: Annotated[int, Field(ge=1)] | None = None

    @model_validator(mode="after")
    def validate_change(self) -> Self:
        if (self.changed_law is None) != (self.change_after is None):
            raise ValueError("a change requires both a replacement law and a boundary")
        if self.change_after is not None:
            if not self.space.calibration_experiments <= self.change_after < self.space.budget:
                raise ValueError("a change must follow calibration and leave a post-change budget")
        return self

    def law_at(self, experiment_index: int) -> LawSpec:
        if not 0 <= experiment_index < self.space.budget:
            raise ValueError("experiment index is outside the budget")
        if self.change_after is not None and experiment_index >= self.change_after:
            assert self.changed_law is not None
            return self.changed_law
        return self.initial_law


def reference_world(
    family: str,
    *,
    seed: int = 7,
    particles: int = 3,
    budget: int = 40,
    changed: bool = True,
    noise: float = 0.002,
) -> WorldDefinition:
    """Create reproducible development worlds. Seeds and families are caller-known."""
    if not 1 <= particles <= 8:
        raise ValueError("reference worlds support one to eight movable particles")
    if not 0 <= seed < 2**64:
        raise ValueError("seed must be an unsigned 64-bit integer")
    if not 1 <= budget <= 10_000:
        raise ValueError("budget must be between 1 and 10000")
    calibration = min(4, budget)
    if changed and budget <= calibration:
        raise ValueError("changed worlds need a budget greater than calibration")
    rng = np.random.default_rng(seed)
    ids = tuple(f"particle-{index}" for index in range(particles))
    edges = (
        Connection(a=ids[0], b="anchor"),
        *(Connection(a=ids[index - 1], b=ids[index]) for index in range(1, particles)),
    )
    structure = Structure(
        particle_ids=ids,
        anchors=(Anchor(id="anchor", position=(0.0, 0.0)),),
        connections=edges,
    )
    if family == "spring":
        linear = float(rng.uniform(0.3, 0.9))
        initial = LawSpec(kind="spring", parameters={"linear": linear, "cubic": 0.0})
        replacement = LawSpec(kind="spring", parameters={"linear": linear, "cubic": 0.25})
    elif family == "radial":
        strength = float(rng.uniform(0.04, 0.12))
        initial = LawSpec(kind="radial", parameters={"strength": -strength, "exponent": 2.0})
        replacement = LawSpec(kind="radial", parameters={"strength": strength, "exponent": 2.0})
    elif family == "velocity":
        linear = float(rng.uniform(0.1, 0.4))
        initial = LawSpec(kind="velocity", parameters={"linear": linear, "transverse": 0.0})
        replacement = LawSpec(kind="velocity", parameters={"linear": linear, "transverse": 0.8})
    else:
        raise ValueError("family must be spring, radial, or velocity")
    return WorldDefinition(
        space=ExperimentSpace(
            structure=structure,
            sampling=Sampling(position_noise=noise, velocity_noise=noise),
            budget=budget,
            calibration_experiments=calibration,
        ),
        noise_seed=seed,
        initial_law=initial,
        changed_law=replacement if changed else None,
        change_after=max(calibration, budget // 2) if changed else None,
    )
