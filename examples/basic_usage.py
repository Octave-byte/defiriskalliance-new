"""
Basic usage example for DeFi Vault scoring.
"""

from methodology import VaultScorer, Asset, Protocol, Oracle, Market, Vault


def example_basic_scoring():
    """Example of basic vault scoring without providers."""
    
    # Create a scorer
    scorer = VaultScorer(beta=1.0)
    
    # Define an asset (e.g., USDC on Ethereum)
    usdc_asset = Asset(
        chain_id=1,  # Ethereum mainnet
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC contract
        creditworthiness=0.9,
        peg_performance=0.95,
        market_confidence=0.9,
        reserves_backing=0.95,
        regulatory_status=0.8,
        smart_contract_audits=0.9,
        custody_safety=0.85,
        complexity=0.7,
        reserve_verifiability=0.9,
        custodian_track_record=0.85,
        user_entitlement_definition=0.9
    )
    
    # Define a protocol (e.g., Aave v3)
    aave_protocol = Protocol(
        chain_id=1,  # Ethereum mainnet
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Aave v3 Pool
        version="v3",
        audits=0.9,
        hacks=0.1,  # Low hacks = good
        bug_bounty=0.8
    )
    
    # Define an oracle (e.g., Chainlink)
    chainlink_oracle = Oracle(
        hardcoded_oracle=0.9,
        vendor_config_uncertainty=0.2  # Low uncertainty = good
    )
    
    # Define a market
    usdc_aave_market = Market(
        chain_id=1,  # Ethereum mainnet
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",  # aUSDC market
        share=1.0,  # 100% of vault
        liquidity=0.9,
        volatility=0.3,  # Low volatility = good
        leverage=0.5,
        second_order_effect=0.4,
        asset=usdc_asset,
        protocol=aave_protocol,
        oracle=chainlink_oracle
    )
    
    # Define a vault
    vault = Vault(
        markets=[usdc_aave_market],
        protocol_score=0.85,
        liquidity_score=0.9,
        concentration_score=0.7,
        governance_structure=0.8,
        curator_reputation=0.85,
        timelock=0.9
    )
    
    # Calculate score
    score = scorer.calculate_vault_score(vault)
    
    print(f"Vault Score: {score:.4f}")
    return score


def example_multi_market_vault():
    """Example of a vault with multiple markets."""
    
    scorer = VaultScorer(beta=1.0)
    
    # Market 1: USDC on Aave (60% of vault)
    usdc_asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.9, peg_performance=0.95, market_confidence=0.9,
        reserves_backing=0.95, regulatory_status=0.8, smart_contract_audits=0.9,
        custody_safety=0.85, complexity=0.7, reserve_verifiability=0.9,
        custodian_track_record=0.85, user_entitlement_definition=0.9
    )
    
    market1 = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=0.6,
        liquidity=0.9, volatility=0.3, leverage=0.5, second_order_effect=0.4,
        asset=usdc_asset,
        protocol=Protocol(
            chain_id=1,
            contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            version="v3",
            audits=0.9, hacks=0.1, bug_bounty=0.8
        ),
        oracle=Oracle(hardcoded_oracle=0.9, vendor_config_uncertainty=0.2)
    )
    
    # Market 2: DAI on Compound (40% of vault)
    dai_asset = Asset(
        chain_id=1,
        contract_address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
        creditworthiness=0.85, peg_performance=0.9, market_confidence=0.85,
        reserves_backing=0.9, regulatory_status=0.7, smart_contract_audits=0.85,
        custody_safety=0.8, complexity=0.6, reserve_verifiability=0.85,
        custodian_track_record=0.8, user_entitlement_definition=0.85
    )
    
    market2 = Market(
        chain_id=1,
        contract_address="0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
        share=0.4,
        liquidity=0.85, volatility=0.35, leverage=0.6, second_order_effect=0.45,
        asset=dai_asset,
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
        protocol_score=0.8,
        liquidity_score=0.85,
        concentration_score=0.65,
        governance_structure=0.75,
        curator_reputation=0.8,
        timelock=0.85
    )
    
    score = scorer.calculate_vault_score(vault)
    print(f"Multi-Market Vault Score: {score:.4f}")
    return score


if __name__ == "__main__":
    print("=== Basic Vault Scoring ===")
    example_basic_scoring()
    
    print("\n=== Multi-Market Vault Scoring ===")
    example_multi_market_vault()

