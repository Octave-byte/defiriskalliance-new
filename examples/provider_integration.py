"""Worked example of writing a custom DRA v3.0 provider adapter.

A provider declares the criteria it can verify and emits
``CriterionAttestation`` records with verdicts ``verified`` / ``violated`` /
``unknown``. The engine resolves them against the open criteria registry.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from methodology import CriterionAttestation, DRAEngine, StrategyContext
from providers.base import RaterBase


class CustomVaultMonitor(RaterBase):
    """Minimal provider that verifies vault security criteria from local data."""

    @property
    def name(self) -> str:
        return "custom_vault_monitor"

    def supported_criteria(self) -> set[str]:
        return {
            "vault.security.s1.audited",
            "vault.security.s1.no_critical_findings",
            "vault.security.s2.lindy_1y",
        }

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]:
        if not ctx.vault_address:
            return []
        evidence = f"local audit ledger entry for {ctx.vault_address}"
        return [
            CriterionAttestation(
                layer="vault",
                component="security",
                criterion_id=cid,
                verdict="verified",
                source=self.name,
                evidence=evidence,
            )
            for cid in (
                "vault.security.s1.audited",
                "vault.security.s1.no_critical_findings",
                "vault.security.s2.lindy_1y",
            )
        ]


def main() -> None:
    ctx = StrategyContext(
        mode="B",
        vault_address="0x1234000000000000000000000000000000000000",
    )
    engine = DRAEngine([CustomVaultMonitor()])
    result = engine.score(ctx)
    print(f"strategy_stage = {result.strategy_stage}")
    print(f"layer_stages   = {result.layer_stages}")
    print("vault security cell satisfied criteria:")
    for status in result.criteria_status.values():
        if status.criterion.layer == "vault" and status.criterion.component == "security":
            mark = "OK" if status.satisfied else "--"
            print(f"  {mark} {status.criterion.id}")


if __name__ == "__main__":
    main()
