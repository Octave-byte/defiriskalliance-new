"""
Example of integrating score providers into the vault scoring system.
"""

from methodology import VaultScorer, Asset, Protocol, Oracle, Market, Vault
from providers import StablewatchProvider, CredoraProvider, ParticulaProvider


def example_with_providers():
    """Example using multiple score providers."""
    
    # Create scorer
    scorer = VaultScorer(beta=1.0)
    
    # Register providers with weights
    # Stablewatch: 40% weight for assets, 30% for protocols
    scorer.register_provider(
        StablewatchProvider(),
        weights={
            'assets': 0.4,
            'protocols': 0.3
        }
    )
    
    # Particula: 30% weight for assets, 20% for protocols
    scorer.register_provider(
        ParticulaProvider(),
        weights={
            'assets': 0.3,
            'protocols': 0.2
        }
    )
    
    # Credora: 30% weight for assets, 50% for protocols, 50% for markets, 40% for vaults
    scorer.register_provider(
        CredoraProvider(),
        weights={
            'assets': 0.3,
            'protocols': 0.5,
            'markets': 0.5,
            'vaults': 0.4
        }
    )
    
    # Create a vault
    usdc_asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
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
    
    aave_protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.9,
        hacks=0.1,
        bug_bounty=0.8
    )
    
    chainlink_oracle = Oracle(
        hardcoded_oracle=0.9,
        vendor_config_uncertainty=0.2
    )
    
    market = Market(
        chain_id=1,
        contract_address="0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
        share=1.0,
        liquidity=0.9,
        volatility=0.3,
        leverage=0.5,
        second_order_effect=0.4,
        asset=usdc_asset,
        protocol=aave_protocol,
        oracle=chainlink_oracle
    )
    
    vault = Vault(
        markets=[market],
        protocol_score=0.85,
        liquidity_score=0.9,
        concentration_score=0.7,
        governance_structure=0.8,
        curator_reputation=0.85,
        timelock=0.9
    )
    
    # Calculate score (will use provider scores)
    score = scorer.calculate_vault_score(vault)
    
    print(f"Vault Score (with providers): {score:.4f}")
    return score


def example_provider_comparison():
    """Compare scores from different providers."""
    
    # Create test asset
    test_asset = Asset(
        chain_id=1,
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        creditworthiness=0.8,
        peg_performance=0.85,
        market_confidence=0.8,
        reserves_backing=0.85,
        regulatory_status=0.7,
        smart_contract_audits=0.8,
        custody_safety=0.75,
        complexity=0.6,
        reserve_verifiability=0.8,
        custodian_track_record=0.75,
        user_entitlement_definition=0.8
    )
    
    # Compare asset scores from different providers
    stablewatch = StablewatchProvider()
    particula = ParticulaProvider()
    credora = CredoraProvider()
    
    stablewatch_score = stablewatch.score_asset(test_asset)
    particula_score = particula.score_asset(test_asset)
    credora_score = credora.score_asset(test_asset)
    
    print("=== Asset Score Comparison ===")
    print(f"Stablewatch: {stablewatch_score:.4f}")
    print(f"Particula: {particula_score:.4f}")
    print(f"Credora: {credora_score:.4f}")
    
    # Compare protocol scores
    test_protocol = Protocol(
        chain_id=1,
        contract_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        version="v3",
        audits=0.85, hacks=0.15, bug_bounty=0.75
    )
    
    stablewatch_protocol = stablewatch.score_protocol(test_protocol)
    particula_protocol = particula.score_protocol(test_protocol)
    credora_protocol = credora.score_protocol(test_protocol)
    
    print("\n=== Protocol Score Comparison ===")
    print(f"Stablewatch: {stablewatch_protocol:.4f}")
    print(f"Particula: {particula_protocol:.4f}")
    print(f"Credora: {credora_protocol:.4f}")


if __name__ == "__main__":
    print("=== Scoring with Multiple Providers ===")
    example_with_providers()
    
    print("\n=== Provider Comparison ===")
    example_provider_comparison()


