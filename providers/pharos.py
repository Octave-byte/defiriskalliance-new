"""Pharos Watch Worker (Bluechip + report cards + DEX liquidity).

Anchors ``asset.security``, ``asset.operations``, and ``asset.strategy_economics``
attestations for stablecoins. Requires ``PHAROS_API_KEY``.
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

PHAROS_BASE = "https://api.pharos.watch"

# Bluechip letter grade -> Stage of asset.security.
PHAROS_GRADE_TO_STAGE: dict[str, int] = {
    "A+": 2, "A": 2, "A-": 2,
    "B+": 1, "B": 1, "B-": 1,
    "C+": 0, "C": 0, "C-": 0, "D+": 0, "D": 0, "D-": 0, "F": 0,
}

ASSET_SECURITY_S1 = ("asset.security.s1.audited", "asset.security.s1.no_recent_exploit")
ASSET_SECURITY_S2 = ("asset.security.s2.lindy_3y_clean", "asset.security.s2.bug_bounty_active")

ASSET_OPS_S1 = ("asset.operations.s1.public_docs", "asset.operations.s1.reserves_attested")
ASSET_OPS_S2 = ("asset.operations.s2.reserves_realtime", "asset.operations.s2.regulated_issuer")

ASSET_ECON_S1 = (
    "asset.strategy_economics.s1.peg_or_market_stable_12m",
    "asset.strategy_economics.s1.collateral_adequate",
)
ASSET_ECON_S2 = (
    "asset.strategy_economics.s2.peg_or_market_stable_36m",
    "asset.strategy_economics.s2.deep_liquidity",
)


def _headers() -> dict[str, str] | None:
    key = os.environ.get("PHAROS_API_KEY", "").strip()
    if not key:
        return None
    return {"X-API-Key": key, "Accept": "application/json"}


def _get(ctx: StrategyContext, path: str) -> Any | None:
    h = _headers()
    if not h:
        return None
    cache_key = f"pharos:{path}"
    if cache_key in ctx._cache:
        return ctx._cache[cache_key]
    try:
        body = get_json(f"{PHAROS_BASE}{path}", headers=h)
    except HttpError:
        body = None
    ctx._cache[cache_key] = body
    return body


def _row_id(row: dict[str, Any]) -> str:
    return str(
        row.get("id")
        or row.get("stablecoinId")
        or row.get("stablecoin_id")
        or row.get("tickerIssuer")
        or ""
    ).lower()


def _find_row(payload: Any, stablecoin_id: str, list_keys: tuple[str, ...]) -> dict[str, Any] | None:
    """Locate a row by stablecoin id across the two shapes Pharos returns.

    Pharos endpoints are inconsistent: some return ``{"<list_key>": [{...}, ...]}``
    (e.g. ``/api/report-cards``) while others return ``{"<id>": {...}, ...}``
    keyed directly by stablecoin id (e.g. ``/api/bluechip-ratings`` and
    ``/api/dex-liquidity``). Walk both shapes so the caller doesn't care.
    """
    if not isinstance(payload, dict):
        return None
    sid = stablecoin_id.lower()
    for key in list_keys:
        rows = payload.get(key)
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and _row_id(row) == sid:
                    return row
    direct = payload.get(stablecoin_id) or payload.get(sid)
    if isinstance(direct, dict):
        return direct
    for k, v in payload.items():
        if isinstance(v, dict) and str(k).lower() == sid:
            return v
    inner = payload.get("data")
    if isinstance(inner, dict):
        return _find_row(inner, stablecoin_id, list_keys)
    if isinstance(inner, list):
        return _find_row({list_keys[0]: inner} if list_keys else {}, stablecoin_id, list_keys)
    return None


def _find_card(payload: Any, stablecoin_id: str) -> dict[str, Any] | None:
    return _find_row(payload, stablecoin_id, ("cards", "reportCards", "items"))


def _dimensions(card: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    dims = card.get("dimensions") or card.get("dimensionScores")
    if isinstance(dims, dict):
        for k, v in dims.items():
            if isinstance(v, (int, float)):
                out[str(k)] = float(v)
            elif isinstance(v, dict) and isinstance(v.get("score"), (int, float)):
                out[str(k)] = float(v["score"])
    return out


def _grade_to_attestations(grade: str | None, source: str) -> list[CriterionAttestation]:
    if not grade:
        return []
    g = grade.strip().upper()
    stage = PHAROS_GRADE_TO_STAGE.get(g)
    if stage is None:
        return []
    out: list[CriterionAttestation] = []
    if stage >= 1:
        for cid in ASSET_SECURITY_S1:
            out.append(_v(cid, "asset", "security", "verified", source, f"bluechip={g}"))
        if stage >= 2:
            for cid in ASSET_SECURITY_S2:
                out.append(_v(cid, "asset", "security", "verified", source, f"bluechip={g}"))
    else:
        for cid in ASSET_SECURITY_S1:
            out.append(_v(cid, "asset", "security", "violated", source, f"bluechip={g}"))
    return out


def _v(cid: str, layer: str, component: str, verdict: str, source: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
        evidence=evidence,
    )


class PharosRater(RaterBase):
    @property
    def name(self) -> str:
        return "pharos"

    def supported_criteria(self) -> set[str]:
        return {
            *ASSET_SECURITY_S1, *ASSET_SECURITY_S2,
            *ASSET_OPS_S1, *ASSET_OPS_S2,
            *ASSET_ECON_S1, *ASSET_ECON_S2,
        } & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not ctx.asset_is_stablecoin or not ctx.pharos_stablecoin_id:
            return []
        sid = ctx.pharos_stablecoin_id
        out: list[CriterionAttestation] = []

        ratings = _get(ctx, "/api/bluechip-ratings")
        grade: str | None = None
        rating_row = _find_row(ratings or {}, sid, ("data", "ratings", "coins"))
        if isinstance(rating_row, dict):
            raw_grade = (
                rating_row.get("grade")
                or rating_row.get("letterGrade")
                or rating_row.get("smidgeGrade")
            )
            if isinstance(raw_grade, str):
                grade = raw_grade.strip()
        out.extend(_grade_to_attestations(grade, self.name))

        cards_body = _get(ctx, "/api/report-cards")
        card = _find_card(cards_body or {}, sid)
        if card:
            dims = _dimensions(card)
            res = dims.get("resilience")
            dep = dims.get("dependencyRisk")
            ops_signal = None
            samples = [v for v in (res, dep) if v is not None]
            if samples:
                ops_signal = sum(samples) / len(samples)
            out.extend(
                threshold_attestations(
                    ops_signal,
                    layer="asset",
                    component="operations",
                    s1_criteria=ASSET_OPS_S1,
                    s2_criteria=ASSET_OPS_S2,
                    s1_threshold=50.0,
                    s2_threshold=80.0,
                    source=self.name,
                    evidence=f"pharos.report-card resilience/dependency avg={ops_signal}",
                )
            )

            liq = dims.get("liquidity")
            peg = dims.get("pegStability")
            econ_signal = None
            samples = [v for v in (liq, peg) if v is not None]
            if samples:
                econ_signal = sum(samples) / len(samples)
            out.extend(
                threshold_attestations(
                    econ_signal,
                    layer="asset",
                    component="strategy_economics",
                    s1_criteria=ASSET_ECON_S1,
                    s2_criteria=ASSET_ECON_S2,
                    s1_threshold=50.0,
                    s2_threshold=80.0,
                    source=self.name,
                    evidence=f"pharos.report-card liquidity/peg avg={econ_signal}",
                )
            )

        dex = _get(ctx, "/api/dex-liquidity")
        dex_row = _find_row(dex or {}, sid, ("coins", "data", "items"))
        if isinstance(dex_row, dict):
            # Prefer an explicit ``liquidityScore`` if Pharos publishes one;
            # otherwise derive a deep-liquidity verdict from raw TVL since the
            # current shape exposes ``totalTvlUsd`` per coin. The $50M floor
            # mirrors the spirit of the original ≥80/100 score gate without
            # synthesising a bogus 0-100 number.
            score = dex_row.get("liquidityScore")
            tvl = dex_row.get("totalTvlUsd") or dex_row.get("tvlUsd")
            if isinstance(score, (int, float)) and float(score) >= 80.0:
                out.append(
                    _v(
                        "asset.strategy_economics.s2.deep_liquidity",
                        "asset",
                        "strategy_economics",
                        "verified",
                        self.name,
                        f"pharos.dex-liquidity score={score}",
                    )
                )
            elif isinstance(tvl, (int, float)) and float(tvl) >= 50_000_000.0:
                out.append(
                    _v(
                        "asset.strategy_economics.s2.deep_liquidity",
                        "asset",
                        "strategy_economics",
                        "verified",
                        self.name,
                        f"pharos.dex-liquidity tvl={int(tvl)}",
                    )
                )

        return out
