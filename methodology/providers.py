"""
Provider interface for score providers.
"""

from abc import ABC, abstractmethod
from typing import Dict
from .models import Asset, Protocol, Oracle, Market, Vault


class ScoreProvider(ABC):
    """Base class for score providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """
        Return a dictionary indicating which segments this provider can score.
        
        Returns:
            Dict with keys: 'assets', 'protocols', 'oracles', 'markets', 'vaults'
            Values are True if the provider can score that segment, False otherwise.
        """
        pass
    
    def score_asset(self, asset: Asset) -> float:
        """
        Score an asset. Returns a value between 0 and 1.
        
        Raises:
            NotImplementedError: If provider doesn't support asset scoring
        """
        if not self.capabilities.get('assets', False):
            raise NotImplementedError(f"{self.name} does not support asset scoring")
        raise NotImplementedError("Subclass must implement score_asset")
    
    def score_protocol(self, protocol: Protocol) -> float:
        """
        Score a protocol. Returns a value between 0 and 1.
        
        Raises:
            NotImplementedError: If provider doesn't support protocol scoring
        """
        if not self.capabilities.get('protocols', False):
            raise NotImplementedError(f"{self.name} does not support protocol scoring")
        raise NotImplementedError("Subclass must implement score_protocol")
    
    def score_oracle(self, oracle: Oracle) -> float:
        """
        Score an oracle. Returns a value between 0 and 1.
        
        Raises:
            NotImplementedError: If provider doesn't support oracle scoring
        """
        if not self.capabilities.get('oracles', False):
            raise NotImplementedError(f"{self.name} does not support oracle scoring")
        raise NotImplementedError("Subclass must implement score_oracle")
    
    def score_market(self, market: Market) -> float:
        """
        Score a market. Returns a value between 0 and 1.
        
        Raises:
            NotImplementedError: If provider doesn't support market scoring
        """
        if not self.capabilities.get('markets', False):
            raise NotImplementedError(f"{self.name} does not support market scoring")
        raise NotImplementedError("Subclass must implement score_market")
    
    def score_vault(self, vault: Vault) -> float:
        """
        Score a vault. Returns a value between 0 and 1.
        
        Raises:
            NotImplementedError: If provider doesn't support vault scoring
        """
        if not self.capabilities.get('vaults', False):
            raise NotImplementedError(f"{self.name} does not support vault scoring")
        raise NotImplementedError("Subclass must implement score_vault")


