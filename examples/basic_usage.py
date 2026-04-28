"""Minimal DRA v3.0 example: score a strategy with no live providers.

Demonstrates how reviewer-supplied attestations alone determine the stage. Run
``python examples/dra_score.py`` for the full multi-provider example.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from methodology import (
    CRITERIA,
    CriterionAttestation,
    DRAEngine,
    StrategyContext,
)


def main() -> None:
    attestations = [
        CriterionAttestation(
            layer=c.layer,
            component=c.component,
            criterion_id=c.id,
            verdict="verified",
            source="manual",
            evidence="reviewer-supplied baseline",
        )
        for c in CRITERIA
        if c.stage == 1
    ]

    ctx = StrategyContext(mode="C", manual_attestations=attestations)
    engine = DRAEngine(raters=[])
    result = engine.score(ctx)

    print(f"strategy_stage = {result.strategy_stage}")
    print(f"layer_stages   = {result.layer_stages}")
    print("If we now violate one criterion, the layer drops:")
    ctx.manual_attestations.append(
        CriterionAttestation(
            layer="market",
            component="security",
            criterion_id="market.security.s1.audited",
            verdict="violated",
            source="manual",
            evidence="found unresolved critical finding",
        )
    )
    result = engine.score(ctx)
    print(f"strategy_stage = {result.strategy_stage}")
    print(f"layer_stages   = {result.layer_stages}")


if __name__ == "__main__":
    main()
