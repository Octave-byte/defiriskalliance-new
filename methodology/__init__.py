"""
DeFi Vault Scoring Methodology

A comprehensive framework for scoring DeFi Vaults based on underlying markets,
assets, protocols, oracles, and vault-level metrics.
"""

from .models import (
    Asset,
    Protocol,
    Oracle,
    Market,
    Vault
)

from .scoring import VaultScorer

from .providers import ScoreProvider

__all__ = [
    'Asset',
    'Protocol',
    'Oracle',
    'Market',
    'Vault',
    'VaultScorer',
    'ScoreProvider'
]

__version__ = '1.0.0'


