"""Vaultscan unified-entry scores -> asset/market/vault attestations.

Vaultscan publishes per-entry composite scores (``asset_score``, ``market_score``,
``governance_score``) on a 0-10 scale through its Supabase ``unified_entries``
table. We bucket those scores into Stage 1/2 attestations using the same
``5.0`` / ``8.0`` band already used by Philidor and Staking Rewards.

Requires ``VAULTSCAN_SUPABASE_URL`` and ``VAULTSCAN_SUPABASE_ANON_KEY``. Missing
env, missing ``ctx.vaultscan_id``, or any HTTP failure produces an empty
attestation list (no hard error).
"""

from __future__ import annotations

import os
from typing import Any

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

S1_THRESHOLD = 5.0
S2_THRESHOLD = 8.0

ASSET_ECO_S1 = (
    "asset.strategy_economics.s1.peg_or_market_stable_12m",
    "asset.strategy_economics.s1.collateral_adequate",
)
ASSET_ECO_S2 = (
    "asset.strategy_economics.s2.peg_or_market_stable_36m",
    "asset.strategy_economics.s2.deep_liquidity",
)

MARKET_ECO_S1 = (
    "market.strategy_economics.s1.conservative_params",
    "market.strategy_economics.s1.healthy_utilization",
)
MARKET_ECO_S2 = (
    "market.strategy_economics.s2.proven_under_stress",
    "market.strategy_economics.s2.diversified_collateral",
)
MARKET_OPS_S1 = (
    "market.operations.s1.timelock_24h",
    "market.operations.s1.quality_oracle",
)
MARKET_OPS_S2 = (
    "market.operations.s2.timelock_7d_or_immutable",
    "market.operations.s2.dual_oracle",
)

VAULT_OPS_S1 = (
    "vault.operations.s1.timelock_24h",
    "vault.operations.s1.public_strategy_doc",
)
VAULT_OPS_S2 = (
    "vault.operations.s2.immutable_or_long_timelock",
    "vault.operations.s2.fast_withdrawal",
)


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fetch_row(ctx: StrategyContext) -> dict | None:
    """Look up the unified_entries row for ``ctx.vaultscan_id`` via Supabase REST.

    Returns ``None`` if not configured, the id is missing, the row does not
    exist, or any HTTP error occurs. Result is cached on ``ctx._cache`` so a
    single context only triggers one network call.
    """
    vid = (ctx.vaultscan_id or "").strip()
    if not vid:
        return None
    cache_key = f"vaultscan:{vid}"
    if cache_key in ctx._cache:
        return ctx._cache[cache_key]

    base = os.environ.get("VAULTSCAN_SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("VAULTSCAN_SUPABASE_ANON_KEY", "").strip()
    if not base or not key:
        ctx._cache[cache_key] = None
        return None

    url = (
        f"{base}/rest/v1/unified_entries"
        f"?id=ilike.{vid}"
        f"&select=asset_score,market_score,governance_score,protocol,entry_type"
        f"&limit=1"
    )
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    try:
        body = get_json(url, headers=headers)
    except HttpError:
        body = None

    row: dict | None = None
    if isinstance(body, list) and body:
        first = body[0]
        if isinstance(first, dict):
            row = first
    elif isinstance(body, dict):
        row = body

    ctx._cache[cache_key] = row
    return row


class VaultscanRater(RaterBase):
    """Adapter for Vaultscan's per-entry composite scores."""

    @property
    def name(self) -> str:
        return "vaultscan"

    def supported_criteria(self) -> set[str]:
        return {
            *ASSET_ECO_S1, *ASSET_ECO_S2,
            *MARKET_ECO_S1, *MARKET_ECO_S2,
            *MARKET_OPS_S1, *MARKET_OPS_S2,
            *VAULT_OPS_S1, *VAULT_OPS_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        row = _fetch_row(ctx)
        if not row:
            return []

        asset_score = _f(row.get("asset_score"))
        market_score = _f(row.get("market_score"))
        gov_score = _f(row.get("governance_score"))
        entry_type = str(row.get("entry_type") or "").lower()
        protocol = str(row.get("protocol") or "").lower()

        out: list[CriterionAttestation] = []

        evidence_asset = (
            f"vaultscan.asset_score={asset_score} "
            f"({protocol}:{entry_type or 'entry'})"
        )
        out.extend(
            threshold_attestations(
                asset_score,
                layer="asset",
                component="strategy_economics",
                s1_criteria=ASSET_ECO_S1,
                s2_criteria=ASSET_ECO_S2,
                s1_threshold=S1_THRESHOLD,
                s2_threshold=S2_THRESHOLD,
                source=self.name,
                evidence=evidence_asset,
            )
        )

        evidence_market = (
            f"vaultscan.market_score={market_score} "
            f"({protocol}:{entry_type or 'entry'})"
        )
        out.extend(
            threshold_attestations(
                market_score,
                layer="market",
                component="strategy_economics",
                s1_criteria=MARKET_ECO_S1,
                s2_criteria=MARKET_ECO_S2,
                s1_threshold=S1_THRESHOLD,
                s2_threshold=S2_THRESHOLD,
                source=self.name,
                evidence=evidence_market,
            )
        )
        out.extend(
            threshold_attestations(
                market_score,
                layer="market",
                component="operations",
                s1_criteria=MARKET_OPS_S1,
                s2_criteria=MARKET_OPS_S2,
                s1_threshold=S1_THRESHOLD,
                s2_threshold=S2_THRESHOLD,
                source=self.name,
                evidence=evidence_market,
            )
        )

        evidence_gov = (
            f"vaultscan.governance_score={gov_score} "
            f"({protocol}:{entry_type or 'entry'})"
        )
        if entry_type == "vault":
            out.extend(
                threshold_attestations(
                    gov_score,
                    layer="vault",
                    component="operations",
                    s1_criteria=VAULT_OPS_S1,
                    s2_criteria=VAULT_OPS_S2,
                    s1_threshold=S1_THRESHOLD,
                    s2_threshold=S2_THRESHOLD,
                    source=self.name,
                    evidence=evidence_gov,
                )
            )
        else:
            out.extend(
                threshold_attestations(
                    gov_score,
                    layer="market",
                    component="operations",
                    s1_criteria=MARKET_OPS_S1,
                    s2_criteria=MARKET_OPS_S2,
                    s1_threshold=S1_THRESHOLD,
                    s2_threshold=S2_THRESHOLD,
                    source=self.name,
                    evidence=evidence_gov,
                )
            )

        return out
