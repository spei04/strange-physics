"""Force plugins and the three reference families."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Annotated, Protocol

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from strange_physics.contracts import Identifier, Message, Structure

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class Geometry:
    mobile_count: int
    edges: tuple[tuple[int, int], ...]

    @classmethod
    def from_structure(cls, structure: Structure) -> Geometry:
        ids = (*structure.particle_ids, *(a.id for a in structure.anchors))
        indices = {identity: index for index, identity in enumerate(ids)}
        return cls(
            len(structure.particle_ids),
            tuple((indices[edge.a], indices[edge.b]) for edge in structure.connections),
        )


class ForceLaw(Protocol):
    """Trusted plugins return forces for every body, including fixed anchors."""

    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray: ...


class LawSpec(Message):
    """Private configuration: never include this in an observation message."""

    kind: Identifier
    parameters: dict[str, Annotated[float, Field(allow_inf_nan=False)]]


class SpringParameters(Message):
    linear: Annotated[float, Field(ge=0, le=4)] = 1.0
    cubic: Annotated[float, Field(ge=0, le=2)] = 0.0


class RadialParameters(Message):
    strength: Annotated[float, Field(ge=-1, le=1)] = -0.1
    exponent: Annotated[float, Field(ge=0.5, le=3)] = 2.0
    softening: Annotated[float, Field(ge=0.1, le=1)] = 0.25


class VelocityParameters(Message):
    linear: Annotated[float, Field(ge=0, le=2)] = 0.2
    cubic: Annotated[float, Field(ge=0, le=1)] = 0.0
    transverse: Annotated[float, Field(ge=-3, le=3)] = 0.0


@dataclass(frozen=True)
class SpringLaw:
    parameters: SpringParameters

    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        result = np.zeros_like(positions)
        for a, b in geometry.edges:
            displacement = positions[a] - positions[b]
            scale = self.parameters.linear + self.parameters.cubic * float(
                displacement @ displacement
            )
            force = -scale * displacement
            result[a] += force
            result[b] -= force
        return result


@dataclass(frozen=True)
class RadialLaw:
    parameters: RadialParameters

    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        result = np.zeros_like(positions)
        for a, b in geometry.edges:
            displacement = positions[a] - positions[b]
            radius_squared = float(displacement @ displacement) + self.parameters.softening**2
            force = (
                self.parameters.strength
                * displacement
                / (radius_squared ** ((self.parameters.exponent + 1) / 2))
            )
            result[a] += force
            result[b] -= force
        return result


@dataclass(frozen=True)
class VelocityLaw:
    parameters: VelocityParameters

    def forces(
        self, positions: FloatArray, velocities: FloatArray, geometry: Geometry
    ) -> FloatArray:
        speed_squared = np.sum(velocities**2, axis=1, keepdims=True)
        rotated = np.column_stack((-velocities[:, 1], velocities[:, 0]))
        return np.asarray(
            -(self.parameters.linear + self.parameters.cubic * speed_squared) * velocities
            + self.parameters.transverse * rotated,
            dtype=np.float64,
        )


LawFactory = Callable[[Mapping[str, float]], ForceLaw]


class LawRegistry:
    """Explicit local registration; no dynamic imports from untrusted configuration."""

    def __init__(self) -> None:
        self._factories: dict[str, LawFactory] = {}
        self._versions: dict[str, str] = {}

    def register(self, kind: str, factory: LawFactory, *, implementation_id: str) -> None:
        LawSpec(kind=kind, parameters={})
        if not implementation_id or len(implementation_id) > 256:
            raise ValueError("plugins require a bounded implementation version or digest")
        if kind in self._factories:
            raise ValueError(f"law plugin already registered: {kind}")
        self._factories[kind] = factory
        self._versions[kind] = implementation_id

    @property
    def versions(self) -> dict[str, str]:
        return dict(self._versions)

    def build(self, spec: LawSpec) -> ForceLaw:
        if spec.kind not in self._factories:
            raise ValueError(f"law plugin is not registered: {spec.kind}")
        return self._factories[spec.kind](dict(spec.parameters))


def reference_registry() -> LawRegistry:
    registry = LawRegistry()
    registry.register(
        "spring",
        lambda p: SpringLaw(SpringParameters.model_validate(dict(p))),
        implementation_id="spring-v1",
    )
    registry.register(
        "radial",
        lambda p: RadialLaw(RadialParameters.model_validate(dict(p))),
        implementation_id="radial-v1",
    )
    registry.register(
        "velocity",
        lambda p: VelocityLaw(VelocityParameters.model_validate(dict(p))),
        implementation_id="velocity-v1",
    )
    return registry
