"""
Data models for DeFi Vault scoring methodology.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Asset:
    """Represents an asset with all scoring criteria."""
    
    # Identification
    chain_id: int            # Chain ID (e.g., 1 for Ethereum mainnet, 137 for Polygon)
    contract_address: str    # Contract address or ID of the asset
    
    # Quality metrics (0.5 total weight)
    creditworthiness: float  # Creditworthiness/resilience of reserves (0.125)
    peg_performance: float    # Historical peg performance (0.125)
    market_confidence: float  # Market confidence (0.125)
    reserves_backing: float  # Level of Reserves backing (0.125)
    
    # Compliance (0.1 weight)
    regulatory_status: float  # Regulatory status of issuer (0.1)
    
    # Tech (0.2 weight)
    smart_contract_audits: float  # Smart contract audits (0.05)
    custody_safety: float         # Safety of custody arrangements (0.1)
    complexity: float             # Complexity of the asset (0.05)
    
    # Transparency (0.2 weight)
    reserve_verifiability: float      # Verifiability of reserve assets (0.1)
    custodian_track_record: float     # Track record of custodians (0.05)
    user_entitlement_definition: float  # User entitlement definition (0.05)
    
    def __post_init__(self):
        """Validate that all scores are between 0 and 1."""
        fields = [
            self.creditworthiness, self.peg_performance, self.market_confidence,
            self.reserves_backing, self.regulatory_status, self.smart_contract_audits,
            self.custody_safety, self.complexity, self.reserve_verifiability,
            self.custodian_track_record, self.user_entitlement_definition
        ]
        for field in fields:
            if not 0 <= field <= 1:
                raise ValueError(f"Asset scores must be between 0 and 1, got {field}")


@dataclass
class Protocol:
    """Represents a protocol with scoring criteria."""
    
    # Identification
    chain_id: int            # Chain ID where the protocol is deployed
    contract_address: str    # Contract address of the protocol
    version: str             # Protocol version (e.g., "v2", "v3", "1.0.0")
    
    audits: float      # Audits score (0.4 weight)
    hacks: float       # Hacks score (0.3 weight) - lower is better, may need inversion
    bug_bounty: float  # Bug Bounty score (0.3 weight)
    
    def __post_init__(self):
        """Validate that all scores are between 0 and 1."""
        if not 0 <= self.audits <= 1:
            raise ValueError(f"Protocol audits score must be between 0 and 1, got {self.audits}")
        if not 0 <= self.hacks <= 1:
            raise ValueError(f"Protocol hacks score must be between 0 and 1, got {self.hacks}")
        if not 0 <= self.bug_bounty <= 1:
            raise ValueError(f"Protocol bug_bounty score must be between 0 and 1, got {self.bug_bounty}")


@dataclass
class Oracle:
    """Represents an oracle with scoring criteria."""
    
    hardcoded_oracle: float           # Hardcoded Oracle score (0.5 weight)
    vendor_config_uncertainty: float   # Vendor/Config Uncertainty score (0.5 weight)
    
    def __post_init__(self):
        """Validate that all scores are between 0 and 1."""
        if not 0 <= self.hardcoded_oracle <= 1:
            raise ValueError(f"Oracle hardcoded_oracle score must be between 0 and 1, got {self.hardcoded_oracle}")
        if not 0 <= self.vendor_config_uncertainty <= 1:
            raise ValueError(f"Oracle vendor_config_uncertainty score must be between 0 and 1, got {self.vendor_config_uncertainty}")


@dataclass
class Market:
    """Represents a market with its components."""
    
    # Identification
    chain_id: int            # Chain ID where the market exists
    contract_address: str    # Contract address or ID of the market
    
    share: float              # Share in vault (0-1, should sum to 1 across all markets)
    liquidity: float          # Liquidity score (0-1)
    volatility: float         # Volatility score (0-1)
    leverage: float           # Leverage score (0-1)
    second_order_effect: float  # Second order effect score (0-1)
    
    asset: Asset
    protocol: Protocol
    oracle: Oracle
    
    def __post_init__(self):
        """Validate market scores."""
        if not 0 <= self.share <= 1:
            raise ValueError(f"Market share must be between 0 and 1, got {self.share}")
        if not 0 <= self.liquidity <= 1:
            raise ValueError(f"Market liquidity score must be between 0 and 1, got {self.liquidity}")
        if not 0 <= self.volatility <= 1:
            raise ValueError(f"Market volatility score must be between 0 and 1, got {self.volatility}")
        if not 0 <= self.leverage <= 1:
            raise ValueError(f"Market leverage score must be between 0 and 1, got {self.leverage}")
        if not 0 <= self.second_order_effect <= 1:
            raise ValueError(f"Market second_order_effect score must be between 0 and 1, got {self.second_order_effect}")


@dataclass
class Vault:
    """Represents a vault with markets and vault-level metrics."""
    
    markets: List[Market]
    
    # Vault-level scores
    protocol_score: float         # Protocol score (0.2 weight)
    liquidity_score: float        # Liquidity score (0.1 weight)
    concentration_score: float    # Concentration of holders (0.1 weight)
    governance_structure: float   # Governance structure (0.2 weight)
    curator_reputation: float     # Curator reputation (0.2 weight)
    timelock: float               # Timelock score (0.2 weight)
    
    def __post_init__(self):
        """Validate vault scores and market shares."""
        if not self.markets:
            raise ValueError("Vault must have at least one market")
        
        total_share = sum(market.share for market in self.markets)
        if not abs(total_share - 1.0) < 0.01:  # Allow small floating point errors
            raise ValueError(f"Market shares must sum to 1.0, got {total_share}")
        
        vault_scores = [
            self.protocol_score, self.liquidity_score, self.concentration_score,
            self.governance_structure, self.curator_reputation, self.timelock
        ]
        for score in vault_scores:
            if not 0 <= score <= 1:
                raise ValueError(f"Vault scores must be between 0 and 1, got {score}")


