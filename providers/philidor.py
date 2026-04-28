"""Philidor public REST vault detail -> vault (and optional market) attestations.

The Philidor API returns ``risk_vectors`` per vault: ``platform`` (security),
``control`` (operations), and ``platform.details.strategyScore`` (economics),
all on a 0-10 scale internally. We bucket them into Stage 1/2 attestations.
"""

from __future__ import annotations

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers._helpers import threshold_attestations
from providers.base import RaterBase

S1_THRESHOLD = 5.0
S2_THRESHOLD = 8.0

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

ASSET_SEC_S1 = ("asset.security.s1.audited", "asset.security.s1.no_recent_exploit")
ASSET_SEC_S2 = ("asset.security.s2.lindy_3y_clean", "asset.security.s2.bug_bounty_active")
ASSET_ECO_S1 = (
    "asset.strategy_economics.s1.peg_or_market_stable_12m",
    "asset.strategy_economics.s1.collateral_adequate",
)
ASSET_ECO_S2 = (
    "asset.strategy_economics.s2.peg_or_market_stable_36m",
    "asset.strategy_economics.s2.deep_liquidity",
)


def _vault_payload(ctx: StrategyContext) -> dict | None:
    key = f"philidor:{ctx.philidor_network}:{ctx.vault_address}"
    if key in ctx._cache:
        return ctx._cache[key]
    if not ctx.philidor_network or not ctx.vault_address:
        return None
    url = f"https://api.philidor.io/v1/vault/{ctx.philidor_network}/{ctx.vault_address}"
    try:
        body = get_json(url)
    except HttpError:
        ctx._cache[key] = None
        return None
    vault = (body.get("data") or {}).get("vault")
    ctx._cache[key] = vault if isinstance(vault, dict) else None
    return ctx._cache[key]


def _f(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class PhilidorRater(RaterBase):
    @property
    def name(self) -> str:
        return "philidor"

    def supported_criteria(self) -> set[str]:
        return {
            *VAULT_SEC_S1, *VAULT_SEC_S2, *VAULT_OPS_S1, *VAULT_OPS_S2, *VAULT_ECO_S1, *VAULT_ECO_S2,
            *MARKET_SEC_S1, *MARKET_SEC_S2, *MARKET_OPS_S1, *MARKET_OPS_S2, *MARKET_ECO_S1, *MARKET_ECO_S2,
            *ASSET_SEC_S1, *ASSET_SEC_S2, *ASSET_ECO_S1, *ASSET_ECO_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        v = _vault_payload(ctx)
        if not v:
            return []
        rv = v.get("risk_vectors") or {}
        plat = rv.get("platform") or {}
        ctrl = rv.get("control") or {}
        det = plat.get("details") or {}
        plat_score = _f(plat.get("score"))
        ctrl_score = _f(ctrl.get("score"))
        strat_score = _f(det.get("strategyScore"))

        out: list[CriterionAttestation] = []

        def emit(layer: str, sec_s1, sec_s2, ops_s1, ops_s2, eco_s1, eco_s2) -> None:
            out.extend(
                threshold_attestations(
                    plat_score,
                    layer=layer,  # type: ignore[arg-type]
                    component="security",
                    s1_criteria=sec_s1, s2_criteria=sec_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"philidor.platform={plat_score}",
                )
            )
            out.extend(
                threshold_attestations(
                    ctrl_score,
                    layer=layer,  # type: ignore[arg-type]
                    component="operations",
                    s1_criteria=ops_s1, s2_criteria=ops_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"philidor.control={ctrl_score}",
                )
            )
            out.extend(
                threshold_attestations(
                    strat_score,
                    layer=layer,  # type: ignore[arg-type]
                    component="strategy_economics",
                    s1_criteria=eco_s1, s2_criteria=eco_s2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"philidor.strategy={strat_score}",
                )
            )

        emit("vault", VAULT_SEC_S1, VAULT_SEC_S2, VAULT_OPS_S1, VAULT_OPS_S2, VAULT_ECO_S1, VAULT_ECO_S2)
        if ctx.philidor_fill_market_from_vault:
            emit("market", MARKET_SEC_S1, MARKET_SEC_S2, MARKET_OPS_S1, MARKET_OPS_S2, MARKET_ECO_S1, MARKET_ECO_S2)

        asset_blk = rv.get("asset")
        if isinstance(asset_blk, dict) and not ctx.asset_is_stablecoin:
            asset_score = _f(asset_blk.get("score"))
            out.extend(
                threshold_attestations(
                    asset_score,
                    layer="asset",
                    component="security",
                    s1_criteria=ASSET_SEC_S1, s2_criteria=ASSET_SEC_S2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"philidor.asset={asset_score}",
                )
            )
            out.extend(
                threshold_attestations(
                    asset_score,
                    layer="asset",
                    component="strategy_economics",
                    s1_criteria=ASSET_ECO_S1, s2_criteria=ASSET_ECO_S2,
                    s1_threshold=S1_THRESHOLD, s2_threshold=S2_THRESHOLD,
                    source=self.name, evidence=f"philidor.asset={asset_score}",
                )
            )
        return out
