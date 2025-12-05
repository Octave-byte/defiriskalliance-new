"""
Core scoring logic for DeFi Vaults.
"""

from typing import List, Dict, Optional
from .models import Asset, Protocol, Oracle, Market, Vault
from .providers import ScoreProvider


class VaultScorer:
    """
    Main scoring engine for DeFi Vaults.
    
    Supports multiple score providers with configurable weights.
    """
    
    def __init__(self, beta: float = 1.0):
        """
        Initialize the vault scorer.
        
        Args:
            beta: Adjustment factor for market pillar product (default: 1.0)
        """
        self.beta = beta
        self.providers: List[ScoreProvider] = []
        self.provider_weights: Dict[str, Dict[str, float]] = {}  # provider_name -> segment -> weight
    
    def register_provider(self, provider: ScoreProvider, weights: Dict[str, float]):
        """
        Register a score provider with weights for each segment.
        
        Args:
            provider: The score provider instance
            weights: Dictionary mapping segment names to weights
                    (e.g., {'assets': 0.3, 'protocols': 0.2})
        """
        # Validate capabilities
        for segment, weight in weights.items():
            if segment not in ['assets', 'protocols', 'oracles', 'markets', 'vaults']:
                raise ValueError(f"Unknown segment: {segment}")
            if not provider.capabilities.get(segment, False):
                raise ValueError(f"Provider {provider.name} cannot score {segment}")
        
        self.providers.append(provider)
        self.provider_weights[provider.name] = weights
    
    def _calculate_asset_score(self, asset: Asset) -> float:
        """Calculate asset score using registered providers."""
        scores = []
        total_weight = 0.0
        
        for provider in self.providers:
            if provider.capabilities.get('assets', False):
                weight = self.provider_weights.get(provider.name, {}).get('assets', 0.0)
                if weight > 0:
                    try:
                        score = provider.score_asset(asset)
                        scores.append(score * weight)
                        total_weight += weight
                    except NotImplementedError:
                        pass
        
        if total_weight == 0:
            # Fallback to default calculation if no providers
            return self._default_asset_score(asset)
        
        return sum(scores) / total_weight if total_weight > 0 else 0.0
    
    def _default_asset_score(self, asset: Asset) -> float:
        """Default asset scoring if no providers are registered."""
        score = (
            asset.creditworthiness * 0.125 +
            asset.peg_performance * 0.125 +
            asset.market_confidence * 0.125 +
            asset.reserves_backing * 0.125 +
            asset.regulatory_status * 0.1 +
            asset.smart_contract_audits * 0.05 +
            asset.custody_safety * 0.1 +
            asset.complexity * 0.05 +
            asset.reserve_verifiability * 0.1 +
            asset.custodian_track_record * 0.05 +
            asset.user_entitlement_definition * 0.05
        )
        return min(1.0, max(0.0, score))
    
    def _calculate_protocol_score(self, protocol: Protocol) -> float:
        """Calculate protocol score using registered providers."""
        scores = []
        total_weight = 0.0
        
        for provider in self.providers:
            if provider.capabilities.get('protocols', False):
                weight = self.provider_weights.get(provider.name, {}).get('protocols', 0.0)
                if weight > 0:
                    try:
                        score = provider.score_protocol(protocol)
                        scores.append(score * weight)
                        total_weight += weight
                    except NotImplementedError:
                        pass
        
        if total_weight == 0:
            # Fallback to default calculation
            return self._default_protocol_score(protocol)
        
        return sum(scores) / total_weight if total_weight > 0 else 0.0
    
    def _default_protocol_score(self, protocol: Protocol) -> float:
        """Default protocol scoring if no providers are registered."""
        # Note: hacks score is inverted (lower hacks = higher score)
        hacks_score = 1.0 - protocol.hacks
        
        score = (
            protocol.audits * 0.4 +
            hacks_score * 0.3 +
            protocol.bug_bounty * 0.3
        )
        return min(1.0, max(0.0, score))
    
    def _calculate_oracle_score(self, oracle: Oracle) -> float:
        """Calculate oracle score using registered providers."""
        scores = []
        total_weight = 0.0
        
        for provider in self.providers:
            if provider.capabilities.get('oracles', False):
                weight = self.provider_weights.get(provider.name, {}).get('oracles', 0.0)
                if weight > 0:
                    try:
                        score = provider.score_oracle(oracle)
                        scores.append(score * weight)
                        total_weight += weight
                    except NotImplementedError:
                        pass
        
        if total_weight == 0:
            # Fallback to default calculation
            return self._default_oracle_score(oracle)
        
        return sum(scores) / total_weight if total_weight > 0 else 0.0
    
    def _default_oracle_score(self, oracle: Oracle) -> float:
        """Default oracle scoring if no providers are registered."""
        score = (
            oracle.hardcoded_oracle * 0.5 +
            oracle.vendor_config_uncertainty * 0.5
        )
        return min(1.0, max(0.0, score))
    
    def _calculate_market_score(self, market: Market) -> float:
        """
        Calculate adjusted market score.
        
        Formula: 0.4 × (∏si)^β + 0.4 × r1 + 0.1 × r2 + 0.1 × r3
        Where:
        - si = market pillar scores (liquidity, volatility, leverage, second_order_effect)
        - r1 = asset rating
        - r2 = protocol rating
        - r3 = oracle rating
        """
        # Calculate product of market pillars
        pillar_product = (
            market.liquidity *
            market.volatility *
            market.leverage *
            market.second_order_effect
        )
        
        # Calculate component scores
        asset_score = self._calculate_asset_score(market.asset)
        protocol_score = self._calculate_protocol_score(market.protocol)
        oracle_score = self._calculate_oracle_score(market.oracle)
        
        # Check if any provider can score markets directly
        market_scores = []
        total_weight = 0.0
        
        for provider in self.providers:
            if provider.capabilities.get('markets', False):
                weight = self.provider_weights.get(provider.name, {}).get('markets', 0.0)
                if weight > 0:
                    try:
                        score = provider.score_market(market)
                        market_scores.append(score * weight)
                        total_weight += weight
                    except NotImplementedError:
                        pass
        
        if total_weight > 0:
            # Use provider market scores if available
            provider_market_score = sum(market_scores) / total_weight
            # Blend with calculated score (can be adjusted)
            calculated_score = (
                0.4 * (pillar_product ** self.beta) +
                0.4 * asset_score +
                0.1 * protocol_score +
                0.1 * oracle_score
            )
            # Weighted average (adjust weights as needed)
            return 0.5 * provider_market_score + 0.5 * calculated_score
        else:
            # Use calculated score
            return (
                0.4 * (pillar_product ** self.beta) +
                0.4 * asset_score +
                0.1 * protocol_score +
                0.1 * oracle_score
            )
    
    def _calculate_vault_level_score(self, vault: Vault) -> float:
        """Calculate vault-level score."""
        # Check if any provider can score vaults directly
        vault_scores = []
        total_weight = 0.0
        
        for provider in self.providers:
            if provider.capabilities.get('vaults', False):
                weight = self.provider_weights.get(provider.name, {}).get('vaults', 0.0)
                if weight > 0:
                    try:
                        score = provider.score_vault(vault)
                        vault_scores.append(score * weight)
                        total_weight += weight
                    except NotImplementedError:
                        pass
        
        if total_weight > 0:
            # Use provider vault scores if available
            provider_vault_score = sum(vault_scores) / total_weight
            # Blend with calculated score
            calculated_score = (
                vault.protocol_score * 0.2 +
                vault.liquidity_score * 0.1 +
                vault.concentration_score * 0.1 +
                vault.governance_structure * 0.2 +
                vault.curator_reputation * 0.2 +
                vault.timelock * 0.2
            )
            # Weighted average
            return 0.5 * provider_vault_score + 0.5 * calculated_score
        else:
            # Use calculated score
            return (
                vault.protocol_score * 0.2 +
                vault.liquidity_score * 0.1 +
                vault.concentration_score * 0.1 +
                vault.governance_structure * 0.2 +
                vault.curator_reputation * 0.2 +
                vault.timelock * 0.2
            )
    
    def calculate_vault_score(self, vault: Vault) -> float:
        """
        Calculate the final vault score.
        
        Formula: 0.85 × ∑(Market Score_i × Share_i) + 0.15 × Vault Rating
        
        Args:
            vault: The vault to score
            
        Returns:
            Final vault score (0-1)
        """
        # Calculate weighted market scores
        market_score_sum = sum(
            self._calculate_market_score(market) * market.share
            for market in vault.markets
        )
        
        # Calculate vault-level score
        vault_level_score = self._calculate_vault_level_score(vault)
        
        # Final score
        final_score = 0.85 * market_score_sum + 0.15 * vault_level_score
        
        return min(1.0, max(0.0, final_score))


