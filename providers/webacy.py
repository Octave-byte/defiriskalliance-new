"""Webacy ERC-4626 vault risk -> ``vault.security`` violation/verification.

Webacy returns an ``overallRisk`` between 0 (safest) and 100 (most risky). We
treat it as a one-way violation source on ``vault.security.s1.no_critical_findings``
and an optional verifier of the lighter Stage 1 / Stage 2 criteria when the
overall risk is low.

Requires ``WEBACY_API_KEY``.
"""

from __future__ import annotations

import os
import urllib.parse

from methodology.criteria import all_criterion_ids
from methodology.entities import StrategyContext
from methodology.http_util import HttpError, get_json
from methodology.types import CriterionAttestation
from providers.base import RaterBase

DEFAULT_WEBACY = "https://api.webacy.com"

VIOLATE_THRESHOLD = 60.0
VERIFY_S1_BELOW = 30.0
VERIFY_S2_BELOW = 10.0

VAULT_SEC_S1 = ("vault.security.s1.audited", "vault.security.s1.no_critical_findings")
VAULT_SEC_S2 = ("vault.security.s2.multi_audit_bounty", "vault.security.s2.lindy_1y")


def _att(cid: str, verdict: str, source: str, evidence: str) -> CriterionAttestation:
    return CriterionAttestation(
        layer="vault",
        component="security",
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
        evidence=evidence,
    )


class WebacyRater(RaterBase):
    @property
    def name(self) -> str:
        return "webacy"

    def supported_criteria(self) -> set[str]:
        return {*VAULT_SEC_S1, *VAULT_SEC_S2} & all_criterion_ids()

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        key = os.environ.get("WEBACY_API_KEY", "").strip()
        if not key or not ctx.vault_address or not ctx.webacy_chain:
            return []
        base = os.environ.get("WEBACY_API_BASE", DEFAULT_WEBACY).rstrip("/")
        addr = ctx.vault_address
        if not addr.startswith("0x"):
            return []
        q = urllib.parse.urlencode({"chain": ctx.webacy_chain})
        url = f"{base}/vaults/{addr}?{q}"
        ck = f"webacy:{ctx.webacy_chain}:{addr.lower()}"
        if ck in ctx._cache:
            body = ctx._cache[ck]
        else:
            try:
                body = get_json(url, headers={"x-api-key": key, "Accept": "application/json"})
            except HttpError:
                body = None
            ctx._cache[ck] = body
        if not isinstance(body, dict):
            return []
        risk = body.get("risk") or {}
        overall = risk.get("overallRisk")
        if overall is None:
            overall = risk.get("score")
        if overall is None:
            return []
        try:
            risk_value = float(overall)
        except (TypeError, ValueError):
            return []

        evidence = f"webacy.overallRisk={risk_value}"
        out: list[CriterionAttestation] = []
        if risk_value >= VIOLATE_THRESHOLD:
            for cid in VAULT_SEC_S1:
                out.append(_att(cid, "violated", self.name, evidence))
            return out
        if risk_value < VERIFY_S1_BELOW:
            for cid in VAULT_SEC_S1:
                out.append(_att(cid, "verified", self.name, evidence))
            if risk_value < VERIFY_S2_BELOW:
                for cid in VAULT_SEC_S2:
                    out.append(_att(cid, "verified", self.name, evidence))
        return out
