"""
Credora score provider implementation.

Credora can score: Assets, Protocols, Markets, Vaults
"""

from methodology.providers import ScoreProvider
from methodology.models import Asset, Protocol, Market, Vault


class CredoraProvider(ScoreProvider):
    """Credora provider - scores Assets, Protocols, Markets, and Vaults"""
    
    @property
    def name(self) -> str:
        return "credora"
    
    @property
    def capabilities(self) -> dict:
        return {
            'assets': True,
            'protocols': True,
            'oracles': False,
            'markets': True,
            'vaults': True
        }
    
    def score_asset(self, asset: Asset) -> float:
        """
        Score an asset based on credora methodology.
        
        Returns:
            Asset score between 0 and 1
        """
        # Credora's asset scoring methodology
        # Using standard weights - can be customized based on credora's specific approach
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
    
    def score_protocol(self, protocol: Protocol) -> float:
        """
        Score a protocol based on credora methodology.
        
        Returns:
            Protocol score between 0 and 1
        """
        hacks_score = 1.0 - protocol.hacks
        
        score = (
            protocol.audits * 0.4 +
            hacks_score * 0.3 +
            protocol.bug_bounty * 0.3
        )
        
        return min(1.0, max(0.0, score))
    
    def score_market(self, market: Market) -> float:
        """
        Score a market based on credora methodology.
        
        Credora can provide direct market scores, which may incorporate
        additional analysis beyond the standard formula.
        
        Returns:
            Market score between 0 and 1
        """
        # Credora's market scoring may use additional factors
        # For now, using a simplified approach - can be enhanced
        pillar_product = (
            market.liquidity *
            market.volatility *
            market.leverage *
            market.second_order_effect
        )
        
        # Credora may weight components differently
        # This is a placeholder - should be customized based on credora's methodology
        asset_score = self.score_asset(market.asset)
        protocol_score = self.score_protocol(market.protocol)
        
        # Credora's market score formula (example - adjust as needed)
        score = (
            0.4 * pillar_product +
            0.4 * asset_score +
            0.1 * protocol_score +
            0.1 * 0.5  # Placeholder for oracle (credora doesn't score oracles)
        )
        
        return min(1.0, max(0.0, score))
    
    def score_vault(self, vault: Vault) -> float:
        """
        Score a vault based on credora methodology.
        
        Returns:
            Vault score between 0 and 1
        """
        # Credora's vault-level scoring
        # May incorporate additional factors beyond the standard metrics
        score = (
            vault.protocol_score * 0.2 +
            vault.liquidity_score * 0.1 +
            vault.concentration_score * 0.1 +
            vault.governance_structure * 0.2 +
            vault.curator_reputation * 0.2 +
            vault.timelock * 0.2
        )
        
        return min(1.0, max(0.0, score))


