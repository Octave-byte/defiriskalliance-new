"""DRA v3.0 engine: collect attestations -> resolve -> roll up to stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .compose import applicable_layers, build_matrix, layer_stage, strategy_stage
from .criteria import get_criterion
from .entities import StrategyContext
from .merge import resolve_attestations
from .types import (
    COMPONENTS,
    CriterionAttestation,
    CriterionStatus,
    Layer,
    Stage,
    StageMatrix,
)


class Rater(Protocol):
    name: str

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]: ...

    def supported_criteria(self) -> set[str]: ...


@dataclass
class DRAResult:
    strategy_stage: Stage
    layer_stages: dict[Layer, Stage]
    matrix: StageMatrix
    criteria_status: dict[str, CriterionStatus]
    attestations: list[CriterionAttestation] = field(default_factory=list)
    methodology_version: str = "v3.0"
    mode: str = "A"
    underlying_vault_stages: list[Stage] | None = None
    meta_vault_stage: Stage | None = None

    def applicable_layers(self) -> tuple[Layer, ...]:
        return applicable_layers(self.mode)  # type: ignore[arg-type]

    def unsatisfied_criteria(self) -> list[CriterionStatus]:
        return [s for s in self.criteria_status.values() if not s.satisfied]


class DRAEngine:
    """Drives a list of raters, resolves attestations, returns a ``DRAResult``."""

    def __init__(
        self,
        raters: list[Rater],
    ) -> None:
        self.raters = list(raters)

    def score(
        self,
        ctx: StrategyContext,
        *,
        underlying_vault_stages: list[Stage] | None = None,
        meta_vault_stage: Stage | None = None,
    ) -> DRAResult:
        all_attestations: list[CriterionAttestation] = []

        for r in self.raters:
            attestations = r.attest(ctx)
            for a in attestations:
                all_attestations.append(
                    CriterionAttestation(
                        layer=a.layer,
                        component=a.component,
                        criterion_id=a.criterion_id,
                        verdict=a.verdict,
                        source=a.source or r.name,
                        evidence=a.evidence,
                        weight=a.weight,
                    )
                )

        for ly, co, cid, verdict in ctx.manual_cells:
            crit = get_criterion(cid)
            if crit.layer != ly or crit.component != co:
                raise ValueError(
                    f"manual cell {cid!r} is registered as {crit.layer}/{crit.component}, not {ly}/{co}"
                )
            if verdict not in ("verified", "violated", "unknown"):
                raise ValueError(f"bad manual verdict {verdict!r}")
            all_attestations.append(
                CriterionAttestation(
                    layer=ly,
                    component=co,
                    criterion_id=cid,
                    verdict=verdict,  # type: ignore[arg-type]
                    source="manual",
                    evidence="manual override",
                )
            )
        all_attestations.extend(ctx.manual_attestations)

        statuses = resolve_attestations(all_attestations)
        matrix = build_matrix(statuses)
        layers: dict[Layer, Stage] = {
            ly: layer_stage(ly, statuses) for ly in ("asset", "market", "vault")
        }
        strat = strategy_stage(
            layers,
            ctx.mode,
            underlying_vault_stages=underlying_vault_stages,
            meta_vault_stage=meta_vault_stage,
        )

        return DRAResult(
            strategy_stage=strat,
            layer_stages=layers,
            matrix=matrix,
            criteria_status=statuses,
            attestations=all_attestations,
            methodology_version=ctx.methodology_version,
            mode=ctx.mode,
            underlying_vault_stages=underlying_vault_stages,
            meta_vault_stage=meta_vault_stage,
        )


__all__ = ["COMPONENTS", "DRAEngine", "DRAResult", "Rater"]
