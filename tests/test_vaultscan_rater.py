"""Tests for ``providers.vaultscan.VaultscanRater``.

We bypass real HTTP by populating the per-context cache key the adapter uses
(``vaultscan:{id}``) before calling ``attest()``. Empty-env behaviour is
covered with ``monkeypatch.delenv`` so the adapter exits before touching the
network.
"""

from __future__ import annotations

from methodology import StrategyContext
from methodology.criteria import all_criterion_ids
from providers import VaultscanRater


def test_vaultscan_supported_criteria_is_subset_of_registry():
    sup = VaultscanRater().supported_criteria()
    assert sup, "VaultscanRater declares no criteria"
    assert sup <= all_criterion_ids(), "VaultscanRater declares unknown criteria"


def test_vaultscan_no_id_returns_empty(monkeypatch):
    monkeypatch.setenv("VAULTSCAN_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("VAULTSCAN_SUPABASE_ANON_KEY", "anon-key")
    ctx = StrategyContext(mode="A", vaultscan_id=None)
    assert VaultscanRater().attest(ctx) == []


def test_vaultscan_no_env_returns_empty(monkeypatch):
    monkeypatch.delenv("VAULTSCAN_SUPABASE_URL", raising=False)
    monkeypatch.delenv("VAULTSCAN_SUPABASE_ANON_KEY", raising=False)
    ctx = StrategyContext(mode="A", vaultscan_id="morpho-1-0xabc")
    assert VaultscanRater().attest(ctx) == []


def test_vaultscan_missing_row_returns_empty(monkeypatch):
    monkeypatch.setenv("VAULTSCAN_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("VAULTSCAN_SUPABASE_ANON_KEY", "anon-key")
    ctx = StrategyContext(mode="A", vaultscan_id="morpho-1-0xabc")
    ctx._cache["vaultscan:morpho-1-0xabc"] = None
    assert VaultscanRater().attest(ctx) == []


def test_vaultscan_vault_row_high_asset_mid_market_low_governance(monkeypatch):
    """Vault entry: asset=8.5 -> S1+S2 verified, market=6 -> S1 verified only,
    governance=3 -> S1 violated on vault.operations."""
    monkeypatch.setenv("VAULTSCAN_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("VAULTSCAN_SUPABASE_ANON_KEY", "anon-key")
    vid = "morpho-1-0xbeef"
    ctx = StrategyContext(mode="A", vaultscan_id=vid)
    ctx._cache[f"vaultscan:{vid}"] = {
        "asset_score": 8.5,
        "market_score": 6.0,
        "governance_score": 3.0,
        "protocol": "morpho",
        "entry_type": "vault",
    }

    atts = VaultscanRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}

    # asset.strategy_economics: both S1 and S2 verified (>= 8 threshold)
    assert ("asset.strategy_economics.s1.peg_or_market_stable_12m", "verified") in by_id
    assert ("asset.strategy_economics.s1.collateral_adequate", "verified") in by_id
    assert ("asset.strategy_economics.s2.peg_or_market_stable_36m", "verified") in by_id
    assert ("asset.strategy_economics.s2.deep_liquidity", "verified") in by_id

    # market.strategy_economics + market.operations: S1 verified, no S2 (mid band)
    assert ("market.strategy_economics.s1.conservative_params", "verified") in by_id
    assert ("market.strategy_economics.s1.healthy_utilization", "verified") in by_id
    assert ("market.strategy_economics.s2.proven_under_stress", "verified") not in by_id
    assert ("market.operations.s1.timelock_24h", "verified") in by_id
    assert ("market.operations.s1.quality_oracle", "verified") in by_id
    assert ("market.operations.s2.timelock_7d_or_immutable", "verified") not in by_id

    # vault.operations: governance below S1 threshold -> violated
    assert ("vault.operations.s1.timelock_24h", "violated") in by_id
    assert ("vault.operations.s1.public_strategy_doc", "violated") in by_id
    # No vault.operations verifications from this rater on this row
    assert not any(
        a.criterion_id.startswith("vault.operations.") and a.verdict == "verified"
        for a in atts
    )


def test_vaultscan_market_row_routes_governance_to_market_operations(monkeypatch):
    """Market entry: governance score should land on market.operations, not
    vault.operations (since this entry is a market, not a vault)."""
    monkeypatch.setenv("VAULTSCAN_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("VAULTSCAN_SUPABASE_ANON_KEY", "anon-key")
    vid = "aave-v3-1-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ctx = StrategyContext(mode="C", vaultscan_id=vid)
    ctx._cache[f"vaultscan:{vid}"] = {
        "asset_score": 9.0,
        "market_score": 9.5,
        "governance_score": 8.5,
        "protocol": "aave-v3",
        "entry_type": "market",
    }

    atts = VaultscanRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}

    # All Stage 1 + Stage 2 criteria verified across asset/market because every
    # score >= 8.
    assert ("market.operations.s2.timelock_7d_or_immutable", "verified") in by_id
    assert ("market.operations.s2.dual_oracle", "verified") in by_id
    assert ("market.strategy_economics.s2.proven_under_stress", "verified") in by_id

    # Critically: no vault.operations attestations (this is a market entry).
    assert not any(a.layer == "vault" for a in atts)
