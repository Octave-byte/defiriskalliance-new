"""DRA v3.0 methodology types: layers, components, stages, criteria, attestations.

This module is the single source of truth for the data model used throughout the
engine and the provider adapters. All scoring is expressed as discrete Stages
(0/1/2), never as a continuous 0-10 number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

Layer = Literal["asset", "market", "vault"]
Component = Literal["security", "operations", "strategy_economics"]
CompositionMode = Literal["A", "B", "C", "D"]
Stage = Literal[0, 1, 2]
Verdict = Literal["verified", "violated", "unknown"]

LAYERS: tuple[Layer, ...] = ("asset", "market", "vault")
COMPONENTS: tuple[Component, ...] = ("security", "operations", "strategy_economics")
STAGES: tuple[Stage, ...] = (0, 1, 2)


@dataclass(frozen=True)
class Criterion:
    """A single, named requirement that a (layer, component) cell must meet
    in order to reach a given Stage. Criteria are monotonic: a cell at Stage N
    must satisfy every criterion at every stage ``s`` such that ``1 <= s <= N``.
    """

    id: str
    layer: Layer
    component: Component
    stage: Stage
    description: str

    def __post_init__(self) -> None:
        if self.stage not in (1, 2):
            raise ValueError(f"criteria are only defined for stage 1 or 2, got {self.stage}")
        prefix = f"{self.layer}.{self.component}.s{self.stage}."
        if not self.id.startswith(prefix):
            raise ValueError(f"criterion id {self.id!r} must start with {prefix!r}")


@dataclass
class CriterionAttestation:
    """One provider's verdict on one criterion."""

    layer: Layer
    component: Component
    criterion_id: str
    verdict: Verdict
    source: str
    evidence: str = ""
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.verdict not in ("verified", "violated", "unknown"):
            raise ValueError(f"bad verdict {self.verdict!r}")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")


@dataclass
class CriterionStatus:
    """Resolved status for one criterion after merging all attestations."""

    criterion: Criterion
    satisfied: bool
    verifications: list[CriterionAttestation] = field(default_factory=list)
    violations: list[CriterionAttestation] = field(default_factory=list)

    @property
    def attestation_count(self) -> int:
        return len(self.verifications) + len(self.violations)


@dataclass
class StageMatrix:
    """Per-cell stage after rollup. Missing entries default to Stage 0."""

    cells: dict[Layer, dict[Component, Stage]] = field(default_factory=lambda: _zero_cells())

    def as_flat(self) -> dict[tuple[Layer, Component], Stage]:
        return {(ly, co): self.cells[ly][co] for ly in LAYERS for co in COMPONENTS}


def _zero_cells() -> dict[Layer, dict[Component, Stage]]:
    return {ly: {co: 0 for co in COMPONENTS} for ly in LAYERS}


def matrix_from_mapping(m: Mapping[tuple[Layer, Component], Stage]) -> StageMatrix:
    cells = _zero_cells()
    for ly in LAYERS:
        for co in COMPONENTS:
            v = m.get((ly, co), 0)
            if v not in (0, 1, 2):
                raise ValueError(f"stage must be 0/1/2, got {v} for {ly}/{co}")
            cells[ly][co] = v  # type: ignore[assignment]
    return StageMatrix(cells=cells)
