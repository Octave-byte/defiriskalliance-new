# Score Provider Participation Guide

This guide explains how score providers can participate in the DeFi Vault scoring methodology.

## Overview

Score providers contribute ratings for specific segments of the scoring methodology. Each provider has defined capabilities for which segments they can score.

## Provider Capabilities

| Provider | Assets | Protocols | Oracles | Markets | Vaults |
|----------|--------|-----------|---------|---------|--------|
| **stablewatch** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **particula** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **credora** | ✅ | ✅ | ❌ | ✅ | ✅ |
| **exponential.fi** | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| **vaults.fyi** | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

## Implementation Steps

### 1. Create Your Provider Module

Create a new file in the `providers/` directory following the naming convention: `your_provider_name.py`

### 2. Implement the Provider Interface

Your provider must implement the `ScoreProvider` interface:

```python
from methodology.providers import ScoreProvider
from methodology.models import Asset, Protocol, Oracle, Market, Vault

class YourProvider(ScoreProvider):
    """Your provider implementation"""
    
    @property
    def name(self) -> str:
        return "your_provider_name"
    
    @property
    def capabilities(self) -> dict:
        return {
            'assets': True,      # Can you score assets?
            'protocols': True,   # Can you score protocols?
            'oracles': False,    # Can you score oracles?
            'markets': False,    # Can you score markets?
            'vaults': False      # Can you score vaults?
        }
    
    def score_asset(self, asset: Asset) -> float:
        """Score an asset (0-1)"""
        # Your scoring logic here
        pass
    
    def score_protocol(self, protocol: Protocol) -> float:
        """Score a protocol (0-1)"""
        # Your scoring logic here
        pass
    
    # Implement only the methods for segments you can score
```

### 3. Example: stablewatch Provider

```python
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
        Returns a score between 0 and 1.
        """
        # Example: Evaluate asset based on reserves, peg performance, etc.
        score = 0.0
        
        # Quality metrics (0.5 total weight)
        score += asset.creditworthiness * 0.125
        score += asset.peg_performance * 0.125
        score += asset.market_confidence * 0.125
        score += asset.reserves_backing * 0.125
        
        # Compliance (0.1 weight)
        score += asset.regulatory_status * 0.1
        
        # Tech (0.2 weight)
        score += asset.smart_contract_audits * 0.05
        score += asset.custody_safety * 0.1
        score += asset.complexity * 0.05
        
        # Transparency (0.2 weight)
        score += asset.reserve_verifiability * 0.1
        score += asset.custodian_track_record * 0.05
        score += asset.user_entitlement_definition * 0.05
        
        return min(1.0, max(0.0, score))
    
    def score_protocol(self, protocol: Protocol) -> float:
        """
        Score a protocol based on stablewatch methodology.
        Returns a score between 0 and 1.
        """
        # Example: Evaluate protocol based on audits, hacks, bug bounty
        score = (
            protocol.audits * 0.4 +
            protocol.hacks * 0.3 +
            protocol.bug_bounty * 0.3
        )
        
        return min(1.0, max(0.0, score))
```

### 4. Example: credora Provider

```python
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
        """Credora's asset scoring methodology"""
        # Your implementation
        pass
    
    def score_protocol(self, protocol: Protocol) -> float:
        """Credora's protocol scoring methodology"""
        # Your implementation
        pass
    
    def score_market(self, market: Market) -> float:
        """Credora's market scoring methodology"""
        # Your implementation
        pass
    
    def score_vault(self, vault: Vault) -> float:
        """Credora's vault scoring methodology"""
        # Your implementation
        pass
```

## Integration with Scoring System

### Registering Your Provider

```python
from methodology.scoring import VaultScorer
from providers.your_provider import YourProvider

# Create scorer
scorer = VaultScorer()

# Register your provider with weights
scorer.register_provider(
    YourProvider(),
    weights={
        'assets': 0.3,      # 30% weight for asset scores
        'protocols': 0.2,   # 20% weight for protocol scores
        # ... other segments
    }
)
```

### Using Multiple Providers

```python
from methodology.scoring import VaultScorer
from providers.stablewatch import StablewatchProvider
from providers.credora import CredoraProvider

scorer = VaultScorer()

# Register multiple providers with different weights
scorer.register_provider(
    StablewatchProvider(),
    weights={
        'assets': 0.4,
        'protocols': 0.3
    }
)

scorer.register_provider(
    CredoraProvider(),
    weights={
        'assets': 0.3,
        'protocols': 0.2,
        'markets': 0.5,
        'vaults': 0.4
    }
)

# Calculate score (automatically aggregates provider scores)
score = scorer.calculate_vault_score(vault)
```

## Data Models

### Asset Model

```python
Asset(
    # Identification
    chain_id: int,            # Chain ID (e.g., 1 for Ethereum mainnet, 137 for Polygon)
    contract_address: str,    # Contract address or ID of the asset
    
    # Quality metrics
    creditworthiness: float,        # 0-1
    peg_performance: float,         # 0-1
    market_confidence: float,       # 0-1
    reserves_backing: float,        # 0-1
    
    # Compliance
    regulatory_status: float,       # 0-1
    
    # Tech
    smart_contract_audits: float,   # 0-1
    custody_safety: float,          # 0-1
    complexity: float,              # 0-1
    
    # Transparency
    reserve_verifiability: float,   # 0-1
    custodian_track_record: float,  # 0-1
    user_entitlement_definition: float  # 0-1
)
```

### Protocol Model

```python
Protocol(
    # Identification
    chain_id: int,            # Chain ID where the protocol is deployed
    contract_address: str,    # Contract address of the protocol
    version: str,             # Protocol version (e.g., "v2", "v3", "1.0.0")
    
    audits: float,      # 0-1
    hacks: float,       # 0-1 (lower is better, may need inversion)
    bug_bounty: float   # 0-1
)
```

### Oracle Model

```python
Oracle(
    hardcoded_oracle: float,           # 0-1
    vendor_config_uncertainty: float   # 0-1
)
```

### Market Model

```python
Market(
    # Identification
    chain_id: int,            # Chain ID where the market exists
    contract_address: str,    # Contract address or ID of the market
    
    share: float,              # Share in vault (0-1, should sum to 1)
    liquidity: float,          # 0-1
    volatility: float,         # 0-1
    leverage: float,           # 0-1
    second_order_effect: float, # 0-1
    asset: Asset,
    protocol: Protocol,
    oracle: Oracle
)
```

### Vault Model

```python
Vault(
    markets: List[Market],
    protocol_score: float,         # 0-1
    liquidity_score: float,        # 0-1
    concentration_score: float,    # 0-1
    governance_structure: float,   # 0-1
    curator_reputation: float,     # 0-1
    timelock: float                # 0-1
)
```

## Testing Your Provider

Create tests in `tests/test_providers.py`:

```python
import pytest
from providers.your_provider import YourProvider
from methodology.models import Asset, Protocol

def test_your_provider_asset_scoring():
    provider = YourProvider()
    
    asset = Asset(
        creditworthiness=0.8,
        peg_performance=0.9,
        # ... other fields
    )
    
    score = provider.score_asset(asset)
    assert 0 <= score <= 1

def test_your_provider_capabilities():
    provider = YourProvider()
    caps = provider.capabilities
    
    assert caps['assets'] == True
    assert caps['protocols'] == True
    # ... verify capabilities
```

## Best Practices

1. **Score Normalization**: Always ensure scores are between 0 and 1
2. **Documentation**: Document your scoring methodology clearly
3. **Transparency**: Make your scoring logic transparent and auditable
4. **Consistency**: Use consistent scoring scales across all segments
5. **Error Handling**: Handle edge cases and invalid inputs gracefully

## Questions?

For questions about provider participation, please open an issue in this repository.


