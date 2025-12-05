"""
Tests for the core scoring methodology.
"""

import pytest
from methodology import VaultScorer, Asset, Protocol, Oracle, Market, Vault


def test_asset_validation():
    """Test that asset validation works correctly."""
    # Valid asset
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.8, peg_performance=0.9, market_confidence=0.8,
        reserves_backing=0.85, regulatory_status=0.7, smart_contract_audits=0.8,
        custody_safety=0.75, complexity=0.6, reserve_verifiability=0.8,
        custodian_track_record=0.75, user_entitlement_definition=0.8
    )
    assert asset.creditworthiness == 0.8
    
    # Invalid asset (score > 1)
    with pytest.raises(ValueError):
        Asset(
            chain_id=1,
            contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            creditworthiness=1.5, peg_performance=0.9, market_confidence=0.8,
            reserves_backing=0.85, regulatory_status=0.7, smart_contract_audits=0.8,
            custody_safety=0.75, complexity=0.6, reserve_verifiability=0.8,
            custodian_track_record=0.75, user_entitlement_definition=0.8
        )


def test_protocol_validation():
    """Test that protocol validation works correctly."""
    protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.8, hacks=0.2, bug_bounty=0.7
    )
    assert protocol.audits == 0.8
    
    with pytest.raises(ValueError):
        Protocol(
            chain_id=1,
            contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            version="v3",
            audits=1.5, hacks=0.2, bug_bounty=0.7
        )


def test_market_validation():
    """Test that market validation works correctly."""
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.8, peg_performance=0.9, market_confidence=0.8,
        reserves_backing=0.85, regulatory_status=0.7, smart_contract_audits=0.8,
        custody_safety=0.75, complexity=0.6, reserve_verifiability=0.8,
        custodian_track_record=0.75, user_entitlement_definition=0.8
    )
    protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.8, hacks=0.2, bug_bounty=0.7
    )
    oracle = Oracle(hardcoded_oracle=0.8, vendor_config_uncertainty=0.3)
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0, liquidity=0.8, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset, protocol=protocol, oracle=oracle
    )
    assert market.share == 1.0
    
    with pytest.raises(ValueError):
        Market(
            chain_id=1,
            contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
            share=1.5, liquidity=0.8, volatility=0.3, leverage=0.5,
            second_order_effect=0.4, asset=asset, protocol=protocol, oracle=oracle
        )


def test_vault_validation():
    """Test that vault validation works correctly."""
    asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.8, peg_performance=0.9, market_confidence=0.8,
        reserves_backing=0.85, regulatory_status=0.7, smart_contract_audits=0.8,
        custody_safety=0.75, complexity=0.6, reserve_verifiability=0.8,
        custodian_track_record=0.75, user_entitlement_definition=0.8
    )
    protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.8, hacks=0.2, bug_bounty=0.7
    )
    oracle = Oracle(hardcoded_oracle=0.8, vendor_config_uncertainty=0.3)
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0, liquidity=0.8, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset, protocol=protocol, oracle=oracle
    )
    
    vault = Vault(
        markets=[market],
        protocol_score=0.8, liquidity_score=0.7, concentration_score=0.6,
        governance_structure=0.8, curator_reputation=0.75, timelock=0.8
    )
    assert len(vault.markets) == 1
    
    # Test invalid vault (shares don't sum to 1)
    market2 = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=0.5, liquidity=0.8, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset, protocol=protocol, oracle=oracle
    )
    
    with pytest.raises(ValueError):
        Vault(
            markets=[market2],
            protocol_score=0.8, liquidity_score=0.7, concentration_score=0.6,
            governance_structure=0.8, curator_reputation=0.75, timelock=0.8
        )


def test_basic_scoring():
    """Test basic scoring without providers."""
    scorer = VaultScorer(beta=1.0)
    
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
    
    vault = Vault(
        markets=[market],
        protocol_score=0.85, liquidity_score=0.9, concentration_score=0.7,
        governance_structure=0.8, curator_reputation=0.85, timelock=0.9
    )
    
    score = scorer.calculate_vault_score(vault)
    assert 0 <= score <= 1


def test_multi_market_vault():
    """Test scoring a vault with multiple markets."""
    scorer = VaultScorer(beta=1.0)
    
    asset1 = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    asset2 = Asset(
        chain_id=1,
        contract_address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
        creditworthiness=0.85, peg_performance=0.9, market_confidence=0.85,
        reserves_backing=0.9, regulatory_status=0.7, smart_contract_audits=0.85,
        custody_safety=0.8, complexity=0.6, reserve_verifiability=0.85,
        custodian_track_record=0.8, user_entitlement_definition=0.85
    )
    
    market1 = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=0.6, liquidity=0.9, volatility=0.3, leverage=0.5,
        second_order_effect=0.4, asset=asset1,
        protocol=Protocol(
            chain_id=1,
            contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            version="v3",
            audits=0.9, hacks=0.1, bug_bounty=0.8
        ),
        oracle=Oracle(hardcoded_oracle=0.9, vendor_config_uncertainty=0.2)
    )
    
    market2 = Market(
        chain_id=1,
        contract_address="0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
        share=0.4, liquidity=0.85, volatility=0.35, leverage=0.6,
        second_order_effect=0.45, asset=asset2,
        protocol=Protocol(
            chain_id=1,
            contract_address="0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
            version="v3",
            audits=0.85, hacks=0.15, bug_bounty=0.75
        ),
        oracle=Oracle(hardcoded_oracle=0.85, vendor_config_uncertainty=0.25)
    )
    
    vault = Vault(
        markets=[market1, market2],
        protocol_score=0.8, liquidity_score=0.85, concentration_score=0.65,
        governance_structure=0.75, curator_reputation=0.8, timelock=0.85
    )
    
    score = scorer.calculate_vault_score(vault)
    assert 0 <= score <= 1


