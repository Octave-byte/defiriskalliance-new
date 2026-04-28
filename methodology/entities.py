"""Strategy context passed to provider adapters in DRA v3.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import Component, CompositionMode, CriterionAttestation, Layer


@dataclass
class StrategyContext:
    """All identifiers and overrides a provider may need to attest criteria.

    The engine never inspects most of these fields directly — they are passed
    through to provider adapters which look up the bits they care about.
    """

    methodology_version: str = "v3.0"
    mode: CompositionMode = "A"

    asset_is_stablecoin: bool = True
    xerberus_asset_symbol: str = ""
    pharos_stablecoin_id: str | None = None

    xerberus_protocol_slug: str | None = None
    defiscan_market_slug: str | None = None
    defiscan_vault_slug: str | None = None

    philidor_network: str | None = None
    vault_address: str | None = None
    webacy_chain: str | None = None

    staking_rewards_name_substr: str | None = None
    staking_rewards_chain: str | None = None

    yearn_curation_report_url: str | None = None

    vaultscan_id: str | None = None

    philidor_fill_market_from_vault: bool = False

    manual_attestations: list[CriterionAttestation] = field(default_factory=list)
    """Reviewer-supplied attestations that bypass automated providers."""

    manual_cells: list[tuple[Layer, Component, str, str]] = field(default_factory=list)
    """Convenience override: ``(layer, component, criterion_id, verdict)`` rows
    converted into manual attestations at engine time."""

    _cache: dict[str, Any] = field(default_factory=dict, repr=False)
