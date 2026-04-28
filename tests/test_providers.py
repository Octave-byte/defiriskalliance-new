"""Provider adapter tests with stubbed HTTP responses."""

from __future__ import annotations

from methodology import StrategyContext
from methodology.criteria import all_criterion_ids
from providers import DefiscanRater, PharosRater, PhilidorRater, WebacyRater, XerberusRater


def test_supported_criteria_subset_of_registry():
    valid = all_criterion_ids()
    for rater in (
        XerberusRater(),
        PharosRater(),
        PhilidorRater(),
        WebacyRater(),
        DefiscanRater(),
    ):
        sup = rater.supported_criteria()
        assert sup, f"{rater.name} declares no criteria"
        assert sup <= valid, f"{rater.name} declares unknown criteria"


def test_defiscan_known_market_reaches_stage_one_ops():
    ctx = StrategyContext(mode="C", defiscan_market_slug="aave-v3")
    atts = DefiscanRater().attest(ctx)
    assert any(a.criterion_id == "market.operations.s1.timelock_24h" and a.verdict == "verified" for a in atts)


def test_defiscan_unknown_slug_yields_no_attestations():
    ctx = StrategyContext(mode="C", defiscan_market_slug="not-a-real-protocol")
    assert DefiscanRater().attest(ctx) == []


def test_xerberus_uses_cache_when_present():
    ctx = StrategyContext(
        mode="A",
        xerberus_asset_symbol="USDC",
        xerberus_protocol_slug="aave-v3",
    )
    ctx._cache["xerberus"] = {
        "assets": {
            "USDC": {"domain_scores": {"regulatory": 0.85, "valuation": 0.5}},
        },
        "protocols": {
            "aave-v3": {"domain_scores": {"security": 0.75, "governance": 0.45, "economics": 0.2}},
        },
    }
    atts = XerberusRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    assert ("asset.operations.s2.regulated_issuer", "verified") in by_id
    assert ("asset.strategy_economics.s1.collateral_adequate", "verified") in by_id
    assert ("market.security.s2.lindy_3y", "verified") in by_id
    assert any(
        a.criterion_id.startswith("market.strategy_economics.s1") and a.verdict == "violated"
        for a in atts
    )


def test_philidor_reads_cached_payload():
    ctx = StrategyContext(
        mode="A",
        philidor_network="ethereum",
        vault_address="0xVAULT",
    )
    ctx._cache["philidor:ethereum:0xVAULT"] = {
        "risk_vectors": {
            "platform": {"score": 9.0, "details": {"strategyScore": 6.0}},
            "control": {"score": 7.0},
        }
    }
    atts = PhilidorRater().attest(ctx)
    by_id = {(a.criterion_id, a.verdict) for a in atts}
    assert ("vault.security.s2.lindy_1y", "verified") in by_id
    assert ("vault.operations.s1.timelock_24h", "verified") in by_id
    assert ("vault.strategy_economics.s1.simple_strategy", "verified") in by_id
    assert ("vault.strategy_economics.s2.proven_track_record", "verified") not in by_id


def test_webacy_high_risk_files_violation(monkeypatch):
    monkeypatch.setenv("WEBACY_API_KEY", "x")
    ctx = StrategyContext(mode="B", vault_address="0xabc0000000000000000000000000000000000000", webacy_chain="eth")
    ctx._cache["webacy:eth:0xabc0000000000000000000000000000000000000"] = {
        "risk": {"overallRisk": 90}
    }
    atts = WebacyRater().attest(ctx)
    assert atts and all(a.verdict == "violated" for a in atts)


def test_webacy_low_risk_verifies(monkeypatch):
    monkeypatch.setenv("WEBACY_API_KEY", "x")
    ctx = StrategyContext(mode="B", vault_address="0xabc0000000000000000000000000000000000000", webacy_chain="eth")
    ctx._cache["webacy:eth:0xabc0000000000000000000000000000000000000"] = {
        "risk": {"overallRisk": 5}
    }
    atts = WebacyRater().attest(ctx)
    assert atts
    assert any(a.criterion_id == "vault.security.s2.multi_audit_bounty" and a.verdict == "verified" for a in atts)
