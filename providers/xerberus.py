"""Xerberus dendrogram public JSON -> Stage attestations for asset and protocol.

Xerberus exposes domain scores in the [0, 1] range. We bucket them into Stage 1
and Stage 2 attestations using the thresholds at the top of this file. The
mapping table is part of the open methodology and may be tuned in the future.
"""

from __future__ import annotations

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

XERBERUS_URL = "https://app.xerberus.io/api/dendrogram/scores"

# Domain-score buckets (0..1 scale).
S1_THRESHOLD = 0.4
S2_THRESHOLD = 0.7

ASSET_REGULATORY_CRITERIA = (
    ("asset.operations.s1.public_docs", "asset.operations.s1.reserves_attested"),
    ("asset.operations.s2.reserves_realtime", "asset.operations.s2.regulated_issuer"),
)
ASSET_VALUATION_CRITERIA = (
    (
        "asset.strategy_economics.s1.peg_or_market_stable_12m",
        "asset.strategy_economics.s1.collateral_adequate",
    ),
    (
        "asset.strategy_economics.s2.peg_or_market_stable_36m",
        "asset.strategy_economics.s2.deep_liquidity",
    ),
)
PROTOCOL_SECURITY_CRITERIA = {
    "market": (
        ("market.security.s1.audited", "market.security.s1.lindy_1y"),
        ("market.security.s2.multi_audit_bounty", "market.security.s2.lindy_3y"),
    ),
    "vault": (
        ("vault.security.s1.audited", "vault.security.s1.no_critical_findings"),
        ("vault.security.s2.multi_audit_bounty", "vault.security.s2.lindy_1y"),
    ),
}
PROTOCOL_GOVERNANCE_CRITERIA = {
    "market": (
        ("market.operations.s1.timelock_24h", "market.operations.s1.quality_oracle"),
        ("market.operations.s2.timelock_7d_or_immutable", "market.operations.s2.dual_oracle"),
    ),
    "vault": (
        ("vault.operations.s1.timelock_24h", "vault.operations.s1.public_strategy_doc"),
        ("vault.operations.s2.immutable_or_long_timelock", "vault.operations.s2.fast_withdrawal"),
    ),
}
PROTOCOL_ECONOMICS_CRITERIA = {
    "market": (
        (
            "market.strategy_economics.s1.conservative_params",
            "market.strategy_economics.s1.healthy_utilization",
        ),
        (
            "market.strategy_economics.s2.proven_under_stress",
            "market.strategy_economics.s2.diversified_collateral",
        ),
    ),
    "vault": (
        (
            "vault.strategy_economics.s1.simple_strategy",
            "vault.strategy_economics.s1.curator_accountable",
        ),
        (
            "vault.strategy_economics.s2.proven_track_record",
            "vault.strategy_economics.s2.transparent_positions",
        ),
    ),
}


class XerberusRater(RaterBase):
    @property
    def name(self) -> str:
        return "xerberus"

    def supported_criteria(self) -> set[str]:
        ids: set[str] = set()
        for s1, s2 in (ASSET_REGULATORY_CRITERIA, ASSET_VALUATION_CRITERIA):
            ids.update(s1)
            ids.update(s2)
        for table in (PROTOCOL_SECURITY_CRITERIA, PROTOCOL_GOVERNANCE_CRITERIA, PROTOCOL_ECONOMICS_CRITERIA):
            for s1, s2 in table.values():
                ids.update(s1)
                ids.update(s2)
        return ids & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        data = ctx._cache.get("xerberus")
        if data is None:
            try:
                data = get_json(XERBERUS_URL).get("data") or {}
            except HttpError:
                data = {}
            ctx._cache["xerberus"] = data

        out: list[CriterionAttestation] = []
        sym = (ctx.xerberus_asset_symbol or "").strip().upper()
        if sym:
            asset = (data.get("assets") or {}).get(sym)
            if isinstance(asset, dict):
                ds = asset.get("domain_scores") or {}
                out.extend(
                    threshold_attestations(
                        ds.get("regulatory"),
                        layer="asset",
                        component="operations",
                        s1_criteria=ASSET_REGULATORY_CRITERIA[0],
                        s2_criteria=ASSET_REGULATORY_CRITERIA[1],
                        s1_threshold=S1_THRESHOLD,
                        s2_threshold=S2_THRESHOLD,
                        source=self.name,
                        evidence=f"xerberus.asset.regulatory={ds.get('regulatory')}",
                    )
                )
                out.extend(
                    threshold_attestations(
                        ds.get("valuation"),
                        layer="asset",
                        component="strategy_economics",
                        s1_criteria=ASSET_VALUATION_CRITERIA[0],
                        s2_criteria=ASSET_VALUATION_CRITERIA[1],
                        s1_threshold=S1_THRESHOLD,
                        s2_threshold=S2_THRESHOLD,
                        source=self.name,
                        evidence=f"xerberus.asset.valuation={ds.get('valuation')}",
                    )
                )

        slug = (ctx.xerberus_protocol_slug or "").strip().lower()
        if slug:
            proto = (data.get("protocols") or {}).get(slug)
            if isinstance(proto, dict):
                ds = proto.get("domain_scores") or {}
                for layer in ("market", "vault"):
                    sec_s1, sec_s2 = PROTOCOL_SECURITY_CRITERIA[layer]
                    gov_s1, gov_s2 = PROTOCOL_GOVERNANCE_CRITERIA[layer]
                    eco_s1, eco_s2 = PROTOCOL_ECONOMICS_CRITERIA[layer]
                    out.extend(
                        threshold_attestations(
                            ds.get("security"),
                            layer=layer,  # type: ignore[arg-type]
                            component="security",
                            s1_criteria=sec_s1,
                            s2_criteria=sec_s2,
                            s1_threshold=S1_THRESHOLD,
                            s2_threshold=S2_THRESHOLD,
                            source=self.name,
                            evidence=f"xerberus.protocol.{slug}.security={ds.get('security')}",
                        )
                    )
                    out.extend(
                        threshold_attestations(
                            ds.get("governance"),
                            layer=layer,  # type: ignore[arg-type]
                            component="operations",
                            s1_criteria=gov_s1,
                            s2_criteria=gov_s2,
                            s1_threshold=S1_THRESHOLD,
                            s2_threshold=S2_THRESHOLD,
                            source=self.name,
                            evidence=f"xerberus.protocol.{slug}.governance={ds.get('governance')}",
                        )
                    )
                    out.extend(
                        threshold_attestations(
                            ds.get("economics"),
                            layer=layer,  # type: ignore[arg-type]
                            component="strategy_economics",
                            s1_criteria=eco_s1,
                            s2_criteria=eco_s2,
                            s1_threshold=S1_THRESHOLD,
                            s2_threshold=S2_THRESHOLD,
                            source=self.name,
                            evidence=f"xerberus.protocol.{slug}.economics={ds.get('economics')}",
                        )
                    )
        return out
