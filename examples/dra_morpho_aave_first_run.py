"""First DRA v3.0 batch ratings for Morpho vaults and Aave v3 reserves.

Scores a curated set of 5 Morpho vaults (mode ``A``) and 5 Aave v3 reserves
(mode ``C``) using only the five providers requested for this first run:

* ``vaultscan``      — ``VaultscanRater`` (asset/market/vault economics + ops)
* ``pharos``         — ``PharosRater`` (asset.* for stablecoins)
* ``philidor``       — ``PhilidorRater`` (vault.* and optional market.*)
* ``staking_rewards``— ``StakingRewardsRater`` (market.* + vault.*)
* ``yearn``          — ``YearnCurationRater`` (when ``yearn_curation_report_url`` set)

Run from the repo root::

    python examples/dra_morpho_aave_first_run.py

Outputs:

* a markdown summary table on stdout
* a per-entry JSON dump to ``examples/output/dra_morpho_aave_first_run.json``

Adapters that lack their respective env keys (``VAULTSCAN_SUPABASE_*``,
``PHAROS_API_KEY``, ``STAKING_REWARDS_API_KEY``) skip silently — the script
still runs and you'll see Stage 0 for cells with no data.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_dotenv(path: Path) -> None:
    """Lightweight ``KEY=VALUE`` loader; existing env vars win."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


_load_dotenv(ROOT / ".env")

from methodology import COMPONENTS, DRAEngine, DRAResult, LAYERS, StrategyContext
from providers import (
    PharosRater,
    PhilidorRater,
    StakingRewardsRater,
    VaultscanRater,
    YearnCurationRater,
)

# Curated entries. Addresses are mainnet (chain id 1) unless noted.
# Vaultscan id format: ``morpho-{chainId}-{vaultAddress lower}`` for Morpho
# vaults, ``aave-v3-{chainId}-{underlyingTokenAddress lower}`` for Aave
# reserves (verified against vaultscan/src/lib/aave/client.ts and
# vaultscan/src/lib/protocols/morpho/normalize.ts).
ENTRIES: list[dict[str, Any]] = [
    {
        "label": "Morpho · Steakhouse USDC",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0xBEEF01735c132Ada46AA9aA4c54623caA92A64CB",
        "philidor_fill_market_from_vault": True,
        "staking_rewards_name_substr": "morpho",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "morpho-1-0xbeef01735c132ada46aa9aa4c54623caa92a64cb",
    },
    {
        "label": "Morpho · Gauntlet USDC Core",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "philidor_network": "ethereum",
        "vault_address": "0x8eB67A509616cd6A7c1B3c8C21D48FF57df3d458",
        "philidor_fill_market_from_vault": True,
        "staking_rewards_name_substr": "morpho",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "morpho-1-0x8eb67a509616cd6a7c1b3c8c21d48ff57df3d458",
    },
    {
        "label": "Morpho · Steakhouse PYUSD",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "pyusd-paypal",
        "philidor_network": "ethereum",
        "vault_address": "0xbEEf02e5E13584ab96848af90261f0C8Ee04722a",
        "philidor_fill_market_from_vault": True,
        "staking_rewards_name_substr": "morpho",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "morpho-1-0xbeef02e5e13584ab96848af90261f0c8ee04722a",
    },
    {
        "label": "Morpho · Steakhouse USDT",
        "mode": "A",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdt-tether",
        "philidor_network": "ethereum",
        "vault_address": "0xbEef047a543E45807105E51A8BBEFCc5950fcfBa",
        "philidor_fill_market_from_vault": True,
        "staking_rewards_name_substr": "morpho",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "morpho-1-0xbeef047a543e45807105e51a8bbefcc5950fcfba",
    },
    {
        "label": "Morpho · MEV Capital wETH",
        "mode": "A",
        "asset_is_stablecoin": False,
        "philidor_network": "ethereum",
        "vault_address": "0x9a8bC3B04b7f3D87cfC09ba407dCED575f2d61D8",
        "philidor_fill_market_from_vault": True,
        "staking_rewards_name_substr": "morpho",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "morpho-1-0x9a8bc3b04b7f3d87cfc09ba407dced575f2d61d8",
    },
    {
        "label": "Aave v3 · USDC (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdc-circle",
        "staking_rewards_name_substr": "aave",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "aave-v3-1-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    },
    {
        "label": "Aave v3 · USDT (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "usdt-tether",
        "staking_rewards_name_substr": "aave",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "aave-v3-1-0xdac17f958d2ee523a2206206994597c13d831ec7",
    },
    {
        "label": "Aave v3 · DAI (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": True,
        "pharos_stablecoin_id": "dai-makerdao",
        "staking_rewards_name_substr": "aave",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "aave-v3-1-0x6b175474e89094c44da98b954eedeac495271d0f",
    },
    {
        "label": "Aave v3 · WETH (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": False,
        "staking_rewards_name_substr": "aave",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "aave-v3-1-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    },
    {
        "label": "Aave v3 · WBTC (Ethereum)",
        "mode": "C",
        "asset_is_stablecoin": False,
        "staking_rewards_name_substr": "aave",
        "staking_rewards_chain": "ethereum",
        "vaultscan_id": "aave-v3-1-0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    },
]


def _ctx_from_entry(entry: dict[str, Any]) -> StrategyContext:
    fields = {k: v for k, v in entry.items() if k != "label"}
    return StrategyContext(**fields)


def _top_blocker(result: DRAResult) -> str:
    """Return the lowest-stage unsatisfied criterion id (the ratchet point)."""
    unsatisfied = result.unsatisfied_criteria()
    if not unsatisfied:
        return "—"
    unsatisfied.sort(key=lambda s: (s.criterion.stage, s.criterion.id))
    return unsatisfied[0].criterion.id


def _print_markdown_summary(rows: list[tuple[str, DRAResult]]) -> None:
    print("# DRA v3.0 — first batch ratings (Morpho + Aave)")
    print()
    print("| Entry | Mode | Strategy | asset | market | vault | top blocker |")
    print("|---|---|---|---|---|---|---|")
    for label, res in rows:
        ls = res.layer_stages
        print(
            f"| {label} | {res.mode} | {res.strategy_stage} "
            f"| {ls.get('asset', 0)} | {ls.get('market', 0)} | {ls.get('vault', 0)} "
            f"| {_top_blocker(res)} |"
        )
    print()


def _print_per_entry_detail(label: str, res: DRAResult) -> None:
    print(f"## {label} (mode {res.mode}) — strategy stage {res.strategy_stage}")
    print()
    print("Per-cell stages:")
    print()
    header = "| layer \\ component | " + " | ".join(COMPONENTS) + " |"
    sep = "|---" * (len(COMPONENTS) + 1) + "|"
    print(header)
    print(sep)
    for layer in LAYERS:
        row = " | ".join(str(res.matrix.cells[layer][c]) for c in COMPONENTS)
        print(f"| {layer} | {row} |")
    print()
    blockers = res.unsatisfied_criteria()
    if blockers:
        print("Top unsatisfied criteria (ordered by stage):")
        blockers.sort(key=lambda s: (s.criterion.stage, s.criterion.id))
        for status in blockers[:6]:
            sources_v = ", ".join(a.source for a in status.violations) or "-"
            sources_ok = ", ".join(a.source for a in status.verifications) or "-"
            print(
                f"- `{status.criterion.id}` (s{status.criterion.stage}) "
                f"violations=[{sources_v}] verifications=[{sources_ok}]"
            )
        print()


def _serialise_result(label: str, entry: dict[str, Any], res: DRAResult) -> dict[str, Any]:
    def _ser(obj: Any) -> Any:
        if is_dataclass(obj):
            return _ser(asdict(obj))
        if isinstance(obj, dict):
            return {k: _ser(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_ser(v) for v in obj]
        return obj

    return {
        "label": label,
        "entry": entry,
        "mode": res.mode,
        "strategy_stage": res.strategy_stage,
        "layer_stages": dict(res.layer_stages),
        "matrix": _ser(res.matrix.cells),
        "criteria_status": {
            cid: {
                "satisfied": status.satisfied,
                "stage": status.criterion.stage,
                "layer": status.criterion.layer,
                "component": status.criterion.component,
                "verifications": [_ser(a) for a in status.verifications],
                "violations": [_ser(a) for a in status.violations],
            }
            for cid, status in res.criteria_status.items()
        },
        "attestations": [_ser(a) for a in res.attestations],
    }


def main() -> None:
    engine = DRAEngine(
        [
            VaultscanRater(),
            PharosRater(),
            PhilidorRater(),
            StakingRewardsRater(),
            YearnCurationRater(),
        ]
    )

    results: list[tuple[str, DRAResult]] = []
    serialised: list[dict[str, Any]] = []
    for entry in ENTRIES:
        label = entry["label"]
        ctx = _ctx_from_entry(entry)
        res = engine.score(ctx)
        results.append((label, res))
        serialised.append(_serialise_result(label, entry, res))

    _print_markdown_summary(results)
    for label, res in results:
        _print_per_entry_detail(label, res)

    out_dir = ROOT / "examples" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dra_morpho_aave_first_run.json"
    out_path.write_text(json.dumps(serialised, indent=2, sort_keys=True))
    print(f"Wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
