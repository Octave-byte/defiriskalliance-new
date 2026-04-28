"""Sanity tests for the criteria registry."""

from __future__ import annotations

from methodology.criteria import (
    CRITERIA,
    all_criterion_ids,
    assert_registry_well_formed,
    criteria_for,
    get_criterion,
)
from methodology.types import COMPONENTS, LAYERS


def test_registry_well_formed():
    assert_registry_well_formed()


def test_every_cell_has_stage1_and_stage2():
    for layer in LAYERS:
        for component in COMPONENTS:
            assert criteria_for(layer, component, 1), f"missing s1 for {layer}/{component}"
            assert criteria_for(layer, component, 2), f"missing s2 for {layer}/{component}"


def test_ids_unique():
    ids = [c.id for c in CRITERIA]
    assert len(ids) == len(set(ids))


def test_get_criterion_round_trip():
    for c in CRITERIA:
        assert get_criterion(c.id) is c


def test_only_stages_1_and_2_have_criteria():
    for c in CRITERIA:
        assert c.stage in (1, 2)


def test_id_prefix_matches_layer_component_stage():
    for c in CRITERIA:
        assert c.id.startswith(f"{c.layer}.{c.component}.s{c.stage}.")


def test_all_criterion_ids_matches_registry():
    assert all_criterion_ids() == {c.id for c in CRITERIA}
