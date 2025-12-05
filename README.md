# DeFi Vault Scoring Methodology

This repository defines a comprehensive methodology for scoring DeFi Vaults, providing a structured framework for risk assessment and rating.

## Overview

The DeFi Vault scoring methodology evaluates vaults through a multi-layered approach that considers:
- **Underlying Markets**: The markets that compose the vault
- **Assets**: The underlying assets in those markets
- **Protocols**: The protocols powering the markets
- **Oracles**: The oracles providing price feeds
- **Vault-Level Metrics**: Protocol, liquidity, governance, and other vault-specific factors

## Methodology Structure

### 1. Underlying Markets

Each market in a vault is scored based on four pillars (each rated 0-1):
- **Liquidity**: Market liquidity depth
- **Volatility**: Price volatility risk
- **Leverage**: Leverage exposure
- **Second Order Effect**: Cascading risk effects

### 2. Market Rating Components

A market's rating combines:
- The product of the four market pillars
- Asset rating (r1)
- Protocol rating (r2)
- Oracle rating (r3)

**Adjusted Market Score Formula:**
```
Adjusted Market Score = 0.4 × (∏si)^β + 0.4 × r1 + 0.1 × r2 + 0.1 × r3
```
Where:
- `si` = score of each market pillar (Liquidity, Volatility, Leverage, Second Order Effect)
- `r1` = Asset rating
- `r2` = Protocol rating
- `r3` = Oracle rating
- `β` = adjustment factor (typically 1, but can be calibrated)

### 3. Asset Ratings

Assets are scored on 11 criteria across 4 categories:

| Category | Criterion | Weight |
|----------|-----------|--------|
| Quality | Creditworthiness/resilience of reserves | 0.125 |
| Quality | Historical peg performance | 0.125 |
| Quality | Market confidence | 0.125 |
| Quality | Level of Reserves backing | 0.125 |
| Compliance | Regulatory status of issuer | 0.1 |
| Tech | Smart contract audits | 0.05 |
| Tech | Safety of custody arrangements | 0.1 |
| Tech | Complexity of the asset | 0.05 |
| Transparency | Verifiability of reserve assets | 0.1 |
| Transparency | Track record of custodians | 0.05 |
| Transparency | User entitlement definition | 0.05 |

Each criterion is scored 0-1, and the final asset rating is the weighted sum.

### 4. Protocol Ratings

Protocols are scored on three factors:

| Factor | Weight |
|--------|--------|
| Audits | 0.4 |
| Hacks | 0.3 |
| Bug Bounty | 0.3 |

Each factor is scored 0-1, with the final protocol rating being the weighted sum.

### 5. Oracle Ratings

Oracles are scored on two factors:

| Factor | Weight |
|--------|--------|
| Hardcoded Oracle | 0.5 |
| Vendor/Config Uncertainty | 0.5 |

Each factor is scored 0-1, with the final oracle rating being the weighted sum.

### 6. Vault-Level Ratings

Vaults are scored on six criteria:

| Category | Subcategory | Weight |
|----------|-------------|--------|
| Tech | Protocol | 0.2 |
| Liquidity | Liquidity | 0.1 |
| Liquidity | Concentration of holders | 0.1 |
| Governance | Governance structure | 0.2 |
| Governance | Curator reputation | 0.2 |
| Governance | Timelock | 0.2 |

Each criterion is scored 0-1, and the final vault rating is the weighted sum.

### 7. Final Vault Score

The final vault score combines market scores (weighted by their share in the vault) and vault-level rating:

```
Final Vault Score = 0.85 × ∑(Market Score_i × Share in Vault_i) + 0.15 × Vault Rating
```

## Score Providers

The methodology supports multiple score providers, each specializing in different segments:

| Provider | Can Score |
|----------|-----------|
| **stablewatch** | Protocols, Assets |
| **exponential.fi** | [To be defined] |
| **vaults.fyi** | [To be defined] |
| **credora** | Assets, Protocols, Vaults, Markets |
| **particula** | Protocols, Assets |

The final rating is a weighted sum of provider scores, where weights reflect the credibility assigned to each provider for each segment.

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from methodology.scoring import VaultScorer
from methodology.models import Vault, Market, Asset, Protocol, Oracle

# Create a vault scorer
scorer = VaultScorer()

# Define your vault structure
vault = Vault(
    markets=[
        Market(
            share=0.5,
            liquidity=0.8,
            volatility=0.6,
            leverage=0.7,
            second_order_effect=0.5,
            asset=Asset(...),
            protocol=Protocol(...),
            oracle=Oracle(...)
        )
    ],
    protocol_score=0.8,
    liquidity_score=0.7,
    concentration_score=0.6,
    governance_structure=0.9,
    curator_reputation=0.8,
    timelock=0.7
)

# Calculate score
score = scorer.calculate_vault_score(vault)
```

## Provider Participation

See [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md) for detailed instructions on how to participate as a score provider.

## Repository Structure

```
.
├── README.md                 # This file
├── PROVIDER_GUIDE.md        # Guide for score providers
├── methodology/              # Core scoring methodology
│   ├── __init__.py
│   ├── models.py            # Data models
│   ├── scoring.py           # Core scoring logic
│   └── providers.py         # Provider interface
├── providers/                # Provider implementations
│   ├── __init__.py
│   ├── stablewatch.py
│   ├── credora.py
│   ├── particula.py
│   └── examples/            # Example provider implementations
├── examples/                 # Usage examples
│   ├── basic_usage.py
│   └── provider_integration.py
└── tests/                    # Test suite
    ├── test_scoring.py
    └── test_providers.py
```

## Contributing

See [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md) for information on how to contribute as a score provider.

## License


