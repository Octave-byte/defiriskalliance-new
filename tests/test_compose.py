"""Tests for the floor rollup (component -> layer -> strategy)."""

from __future__ import annotations

import pytest

from methodology.compose import (
    applicable_layers,
    component_stage,
    layer_stage,
    strategy_stage,
)
from methodology.criteria import CRITERIA, criteria_for
from methodology.merge import resolve_attestations
from methodology.types import COMPONENTS, LAYERS, CriterionAttestation


def _verify(cids):
    return [
        CriterionAttestation(
            layer=cid.split(".")[0],  # type: ignore[arg-type]
            component=cid.split(".")[1],  # type: ignore[arg-type]
            criterion_id=cid,
            verdict="verified",
            source="test",
        )
        for cid in cids
    ]


def _all_s1_ids():
    return [c.id for c in CRITERIA if c.stage == 1]


def _all_s2_ids():
    return [c.id for c in CRITERIA if c.stage == 2]


def test_no_attestations_yields_stage_zero_everywhere():
    statuses = resolve_attestations([])
    for layer in LAYERS:
        for component in COMPONENTS:
            assert component_stage(layer, component, statuses) == 0
        assert layer_stage(layer, statuses) == 0


def test_all_s1_verified_yields_stage_one_everywhere():
    statuses = resolve_attestations(_verify(_all_s1_ids()))
    for layer in LAYERS:
        for component in COMPONENTS:
            assert component_stage(layer, component, statuses) == 1
        assert layer_stage(layer, statuses) == 1


def test_all_criteria_verified_yields_stage_two():
    statuses = resolve_attestations(_verify(_all_s1_ids() + _all_s2_ids()))
    for layer in LAYERS:
        assert layer_stage(layer, statuses) == 2


def test_floor_rule_one_missing_s1_drops_layer_to_zero():
    s1 = _all_s1_ids()
    sample = "market.security.s1.audited"
    s1.remove(sample)
    statuses = resolve_attestations(_verify(s1))
    assert component_stage("market", "security", statuses) == 0
    assert layer_stage("market", statuses) == 0
    # other layers reach Stage 1 fully
    assert layer_stage("asset", statuses) == 1
    assert layer_stage("vault", statuses) == 1


def test_strategy_stage_mode_c_ignores_vault():
    s1 = _all_s1_ids()
    bad_vault = [c.id for c in criteria_for("vault", "security", 1)][0]
    s1.remove(bad_vault)
    statuses = resolve_attestations(_verify(s1))
    layers = {ly: layer_stage(ly, statuses) for ly in LAYERS}
    assert layers["vault"] == 0
    assert strategy_stage(layers, "C") == 1
    assert strategy_stage(layers, "A") == 0


def test_strategy_mode_d_floors_underlying():
    layers = {"asset": 2, "market": 2, "vault": 2}
    assert strategy_stage(
        layers, "D",
        underlying_vault_stages=[2, 1, 2],
        meta_vault_stage=2,
    ) == 1


def test_mode_d_requires_args():
    layers = {"asset": 2, "market": 2, "vault": 2}
    with pytest.raises(ValueError):
        strategy_stage(layers, "D")


def test_applicable_layers_per_mode():
    assert applicable_layers("A") == ("asset", "market", "vault")
    assert applicable_layers("B") == ("asset", "vault")
    assert applicable_layers("C") == ("asset", "market")
    assert applicable_layers("D") == ("asset", "vault")
    with pytest.raises(ValueError):
        applicable_layers("Z")  # type: ignore[arg-type]
