"""
Stablewatch score provider implementation.

Stablewatch can score: Assets, Protocols
"""

from methodology.providers import ScoreProvider
from methodology.models import Asset, Protocol


class StablewatchProvider(ScoreProvider):
    """Stablewatch provider - scores Assets and Protocols"""
    
    @property
    def name(self) -> str:
        return "stablewatch"
    
    @property
    def capabilities(self) -> dict:
        return {
            'assets': True,
            'protocols': True,
            'oracles': False,
            'markets': False,
            'vaults': False
        }
    
    def score_asset(self, asset: Asset) -> float:
        """
        Score an asset based on stablewatch methodology.
        
        Uses the standard asset scoring weights:
        - Quality: 0.5 total (4 criteria × 0.125 each)
        - Compliance: 0.1
        - Tech: 0.2 (3 criteria with varying weights)
        - Transparency: 0.2 (3 criteria with varying weights)
        
        Returns:
            Asset score between 0 and 1
        """
        score = (
            # Quality metrics (0.5 total)
            asset.creditworthiness * 0.125 +
            asset.peg_performance * 0.125 +
            asset.market_confidence * 0.125 +
            asset.reserves_backing * 0.125 +
            
            # Compliance (0.1)
            asset.regulatory_status * 0.1 +
            
            # Tech (0.2)
            asset.smart_contract_audits * 0.05 +
            asset.custody_safety * 0.1 +
            asset.complexity * 0.05 +
            
            # Transparency (0.2)
            asset.reserve_verifiability * 0.1 +
            asset.custodian_track_record * 0.05 +
            asset.user_entitlement_definition * 0.05
        )
        
        return min(1.0, max(0.0, score))
    
    def score_protocol(self, protocol: Protocol) -> float:
        """
        Score a protocol based on stablewatch methodology.
        
        Uses the standard protocol scoring weights:
        - Audits: 0.4
        - Hacks: 0.3 (inverted - lower hacks = higher score)
        - Bug Bounty: 0.3
        
        Returns:
            Protocol score between 0 and 1
        """
        # Invert hacks score (lower hacks = better)
        hacks_score = 1.0 - protocol.hacks
        
        score = (
            protocol.audits * 0.4 +
            hacks_score * 0.3 +
            protocol.bug_bounty * 0.3
        )
        
        return min(1.0, max(0.0, score))


