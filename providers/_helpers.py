"""Shared helpers for provider adapters: threshold-bucketing numeric signals
into ``CriterionAttestation`` records.

Adapters keep their per-provider mapping tables at the top of their own file —
this module only centralises the verdict logic so it stays uniform.
"""

from __future__ import annotations

from collections.abc import Iterable

from methodology.criteria import get_criterion
from methodology.types import Component, CriterionAttestation, Layer


def threshold_attestations(
    value: float | None,
    *,
    layer: Layer,
    component: Component,
    s1_criteria: Iterable[str],
    s2_criteria: Iterable[str],
    s1_threshold: float,
    s2_threshold: float,
    source: str,
    evidence: str,
    violate_below_s1: bool = True,
) -> list[CriterionAttestation]:
    """Bucket a numeric signal into criterion verdicts.

    * ``value >= s2_threshold`` -> verifies every Stage 1 and Stage 2 criterion.
    * ``s1_threshold <= value < s2_threshold`` -> verifies Stage 1, leaves
      Stage 2 as ``unknown`` (omitted from output).
    * ``value < s1_threshold`` -> if ``violate_below_s1`` is set, files a
      ``violated`` verdict on every Stage 1 criterion (default-to-worse).
    * ``value is None`` -> no attestation.
    """
    if value is None:
        return []
    out: list[CriterionAttestation] = []
    if value >= s2_threshold:
        for cid in s1_criteria:
            _validate(cid, layer, component)
            out.append(_a(layer, component, cid, "verified", source, evidence))
        for cid in s2_criteria:
            _validate(cid, layer, component)
            out.append(_a(layer, component, cid, "verified", source, evidence))
    elif value >= s1_threshold:
        for cid in s1_criteria:
            _validate(cid, layer, component)
            out.append(_a(layer, component, cid, "verified", source, evidence))
    elif violate_below_s1:
        for cid in s1_criteria:
            _validate(cid, layer, component)
            out.append(_a(layer, component, cid, "violated", source, evidence))
    return out


def _a(
    layer: Layer,
    component: Component,
    cid: str,
    verdict: str,
    source: str,
    evidence: str,
) -> CriterionAttestation:
    return CriterionAttestation(
        layer=layer,
        component=component,
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
        evidence=evidence,
    )


def _validate(cid: str, layer: Layer, component: Component) -> None:
    c = get_criterion(cid)
    if c.layer != layer or c.component != component:
        raise ValueError(
            f"criterion {cid!r} is registered as {c.layer}/{c.component}, not {layer}/{component}"
        )
