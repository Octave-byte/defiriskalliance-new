"""
Tests for score providers.
"""

import pytest
from methodology import Asset, Protocol, Market, Vault, Oracle
from providers import StablewatchProvider, CredoraProvider, ParticulaProvider


def test_stablewatch_capabilities():
    """Test stablewatch provider capabilities."""
    provider = StablewatchProvider()
    
    assert provider.name == "stablewatch"
    caps = provider.capabilities
    assert caps['assets'] == True
    assert caps['protocols'] == True
    assert caps['oracles'] == False
    assert caps['markets'] == False
    assert caps['vaults'] == False


def test_stablewatch_asset_scoring():
    """Test stablewatch asset scoring."""
    provider = StablewatchProvider()
    
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    score = provider.score_asset(asset)
    assert 0 <= score <= 1


def test_stablewatch_protocol_scoring():
    """Test stablewatch protocol scoring."""
    provider = StablewatchProvider()
    
    protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.9, hacks=0.1, bug_bounty=0.8
    )
    score = provider.score_protocol(protocol)
    assert 0 <= score <= 1


def test_stablewatch_unsupported_segments():
    """Test that stablewatch raises errors for unsupported segments."""
    provider = StablewatchProvider()
    
    oracle = Oracle(hardcoded_oracle=0.8, vendor_config_uncertainty=0.3)
    
    with pytest.raises(NotImplementedError):
        provider.score_oracle(oracle)


def test_credora_capabilities():
    """Test credora provider capabilities."""
    provider = CredoraProvider()
    
    assert provider.name == "credora"
    caps = provider.capabilities
    assert caps['assets'] == True
    assert caps['protocols'] == True
    assert caps['markets'] == True
    assert caps['vaults'] == True
    assert caps['oracles'] == False


def test_credora_market_scoring():
    """Test credora market scoring."""
    provider = CredoraProvider()
    
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.9, hacks=0.1, bug_bounty=0.8
    )
    oracle = Oracle(hardcoded_oracle=0.9, vendor_config_uncertainty=0.2)
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0, liquidity=0.9, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset, protocol=protocol, oracle=oracle
    )
    
    score = provider.score_market(market)
    assert 0 <= score <= 1


def test_credora_vault_scoring():
    """Test credora vault scoring."""
    provider = CredoraProvider()
    
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0, liquidity=0.9, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset,
        protocol=Protocol(
            chain_id=1,
            contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            version="v3",
            audits=0.9, hacks=0.1, bug_bounty=0.8
        ),
        oracle=Oracle(hardcoded_oracle=0.9, vendor_config_uncertainty=0.2)
    )
    
    vault = Vault(
        markets=[market],
        protocol_score=0.85, liquidity_score=0.9, concentration_score=0.7,
        governance_structure=0.8, curator_reputation=0.85, timelock=0.9
    )
    
    score = provider.score_vault(vault)
    assert 0 <= score <= 1


def test_particula_capabilities():
    """Test particula provider capabilities."""
    provider = ParticulaProvider()
    
    assert provider.name == "particula"
    caps = provider.capabilities
    assert caps['assets'] == True
    assert caps['protocols'] == True
    assert caps['oracles'] == False
    assert caps['markets'] == False
    assert caps['vaults'] == False


def test_provider_integration():
    """Test provider integration with scorer."""
    from methodology import VaultScorer
    
    scorer = VaultScorer()
    
    # Register providers
    scorer.register_provider(
        StablewatchProvider(),
        weights={'assets': 0.5, 'protocols': 0.5}
    )
    
    scorer.register_provider(
        CredoraProvider(),
        weights={'assets': 0.5, 'protocols': 0.5, 'markets': 1.0, 'vaults': 1.0}
    )
    
    # Create test vault
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0, liquidity=0.9, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset,
        protocol=Protocol(
            chain_id=1,
            contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            version="v3",
            audits=0.9, hacks=0.1, bug_bounty=0.8
        ),
        oracle=Oracle(hardcoded_oracle=0.9, vendor_config_uncertainty=0.2)
    )
    
    vault = Vault(
        markets=[market],
        protocol_score=0.85, liquidity_score=0.9, concentration_score=0.7,
        governance_structure=0.8, curator_reputation=0.85, timelock=0.9
    )
    
    score = scorer.calculate_vault_score(vault)
    assert 0 <= score <= 1


