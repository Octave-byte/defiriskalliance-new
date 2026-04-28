"""Staking Rewards DeFi ratings -> market and vault attestations.

Staking Rewards exposes per-strategy security/operations/strategy ratings.
Requires ``STAKING_REWARDS_API_KEY``.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

API = "https://api.stakingrewards.com/ratings/defi"

S1_THRESHOLD = 5.0
S2_THRESHOLD = 8.0

MARKET_SEC_S1 = ("market.security.s1.audited", "market.security.s1.lindy_1y")
MARKET_SEC_S2 = ("market.security.s2.multi_audit_bounty", "market.security.s2.lindy_3y")
MARKET_OPS_S1 = ("market.operations.s1.timelock_24h", "market.operations.s1.quality_oracle")
MARKET_OPS_S2 = ("market.operations.s2.timelock_7d_or_immutable", "market.operations.s2.dual_oracle")
MARKET_ECO_S1 = (
    "market.strategy_economics.s1.conservative_params",
    "market.strategy_economics.s1.healthy_utilization",
)
MARKET_ECO_S2 = (
    "market.strategy_economics.s2.proven_under_stress",
    "market.strategy_economics.s2.diversified_collateral",
)

VAULT_SEC_S1 = ("vault.security.s1.audited", "vault.security.s1.no_critical_findings")
VAULT_SEC_S2 = ("vault.security.s2.multi_audit_bounty", "vault.security.s2.lindy_1y")
VAULT_OPS_S1 = ("vault.operations.s1.timelock_24h", "vault.operations.s1.public_strategy_doc")
VAULT_OPS_S2 = ("vault.operations.s2.immutable_or_long_timelock", "vault.operations.s2.fast_withdrawal")
VAULT_ECO_S1 = (
    "vault.strategy_economics.s1.simple_strategy",
    "vault.strategy_economics.s1.curator_accountable",
)
VAULT_ECO_S2 = (
    "vault.strategy_economics.s2.proven_track_record",
    "vault.strategy_economics.s2.transparent_positions",
)


def _avg_subcats(block: dict[str, Any] | None) -> float | None:
    if not isinstance(block, dict):
        return None
    subs = block.get("sub_categories") or block.get("subCategories")
    if not isinstance(subs, dict):
        r = block.get("rating")
        if isinstance(r, (int, float)):
            return _normalize(float(r))
        return None
    nums = [float(v) for v in subs.values() if isinstance(v, (int, float))]
    if not nums:
        return None
    avg = sum(nums) / len(nums)
    return _normalize(avg)


def _normalize(v: float) -> float:
    """Normalise to 0-10 regardless of upstream scale."""
    if v <= 1.0:
        return v * 10.0
    if v <= 10.0:
        return v
    return v / 10.0


class StakingRewardsRater(RaterBase):
    @property
    def name(self) -> str:
        return "staking_rewards"

    def supported_criteria(self) -> set[str]:
        return {
            *MARKET_SEC_S1, *MARKET_SEC_S2, *MARKET_OPS_S1, *MARKET_OPS_S2, *MARKET_ECO_S1, *MARKET_ECO_S2,
            *VAULT_SEC_S1, *VAULT_SEC_S2, *VAULT_OPS_S1, *VAULT_OPS_S2, *VAULT_ECO_S1, *VAULT_ECO_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        key = os.environ.get("STAKING_REWARDS_API_KEY", "").strip()
        sub = (ctx.staking_rewards_name_substr or "").lower()
        chain = (ctx.staking_rewards_chain or "").lower()
        if not key or not sub:
            return []

        if "staking_rewards_page" not in ctx._cache:
            try:
                page = get_json(
                    API + "?" + urllib.parse.urlencode({"limit": 200, "offset": 0}),
                    headers={"X-API-KEY": key},
                )
            except HttpError:
                page = {}
            ctx._cache["staking_rewards_page"] = page
        else:
            page = ctx._cache["staking_rewards_page"]

        rows = page.get("data") if isinstance(page, dict) else None
        if not isinstance(rows, list):
            return []
        chosen = None
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", "")).lower()
            ch = str(row.get("chain", "")).lower()
            if sub in name and (not chain or chain == ch or chain in ch):
                chosen = row
                break
        if chosen is None:
            return []

        rd = chosen.get("rating_data") or {}
        sec = _avg_subcats(rd.get("security"))
        ops = _avg_subcats(rd.get("operations"))
        strat = _avg_subcats(rd.get("strategy"))

        out: list[CriterionAttestation] = []
        for layer, sec_s1, sec_s2, ops_s1, ops_s2, eco_s1, eco_s2 in (
            ("market", MARKET_SEC_S1, MARKET_SEC_S2, MARKET_OPS_S1, MARKET_OPS_S2, MARKET_ECO_S1, MARKET_ECO_S2),
            ("vault", VAULT_SEC_S1, VAULT_SEC_S2, VAULT_OPS_S1, VAULT_OPS_S2, VAULT_ECO_S1, VAULT_ECO_S2),
        ):
            out.extend(
                threshold_attestations(
                    sec, layer=layer, component="security",  # type: ignore[arg-type]
                    s1_criteria=sec_s1, s2_criteria=sec_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"staking_rewards.security={sec}",
                )
            )
            out.extend(
                threshold_attestations(
                    ops, layer=layer, component="operations",  # type: ignore[arg-type]
                    s1_criteria=ops_s1, s2_criteria=ops_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"staking_rewards.operations={ops}",
                )
            )
            out.extend(
                threshold_attestations(
                    strat, layer=layer, component="strategy_economics",  # type: ignore[arg-type]
                    s1_criteria=eco_s1, s2_criteria=eco_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"staking_rewards.strategy={strat}",
                )
            )
        return out
