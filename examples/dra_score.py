"""Score a market position (Mode C) and a vault strategy (Mode A) under DRA v3.0.

Outputs the strategy stage, per-layer stages, the 3x3 cell matrix, and the
list of criteria that gated each layer.

Run from repo root::

    python examples/dra_score.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from methodology import COMPONENTS, DRAEngine, DRAResult, LAYERS, StrategyContext
from providers import (
    DefiscanRater,
    PharosRater,
    PhilidorRater,
    StakingRewardsRater,
    WebacyRater,
    XerberusRater,
)


def _print_result(label: str, result: DRAResult) -> None:
    print(f"=== {label} (mode {result.mode}) ===")
    print(f"strategy_stage = {result.strategy_stage}")
    for layer in result.applicable_layers():
        print(f"  layer {layer:<6}= stage {result.layer_stages[layer]}")
    print("  cell stages:")
    header = " " * 8 + "  ".join(f"{c:<20}" for c in COMPONENTS)
    print(header)
    for layer in LAYERS:
        row = " ".join(f"{result.matrix.cells[layer][c]:^20}" for c in COMPONENTS)
        print(f"  {layer:<6} {row}")
    print("  unsatisfied criteria (the floor):")
    for status in result.unsatisfied_criteria()[:10]:
        c = status.criterion
        sources = ",".join(a.source for a in status.violations) or "none"
        print(f"    - {c.id} (s{c.stage}) violations={sources}")
    print()


def main() -> None:
    raters = [
        XerberusRater(),
        PharosRater(),
        PhilidorRater(),
        WebacyRater(),
        StakingRewardsRater(),
        DefiscanRater(),
    ]
    engine = DRAEngine(raters)

    ctx_c = StrategyContext(
        mode="C",
        asset_is_stablecoin=True,
        xerberus_asset_symbol="USDC",
        pharos_stablecoin_id="usdc-circle",
        xerberus_protocol_slug="aave-v3",
        defiscan_market_slug="aave-v3",
        staking_rewards_name_substr="aave",
        staking_rewards_chain="ethereum",
    )
    _print_result("Aave v3 USDC supply", engine.score(ctx_c))

    morpho_usdc_vault = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C077EE1C5"  # placeholder
    ctx_a = StrategyContext(
        mode="A",
        asset_is_stablecoin=True,
        xerberus_asset_symbol="USDC",
        pharos_stablecoin_id="usdc-circle",
        xerberus_protocol_slug="morpho-v1",
        defiscan_market_slug="morpho-blue",
        defiscan_vault_slug="morpho-vault",
        philidor_network="ethereum",
        vault_address=morpho_usdc_vault,
        webacy_chain="eth",
        philidor_fill_market_from_vault=True,
        staking_rewards_name_substr="morpho",
    )
    _print_result("Morpho USDC vault", engine.score(ctx_a))


if __name__ == "__main__":
    main()
