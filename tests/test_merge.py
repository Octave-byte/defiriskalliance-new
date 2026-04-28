"""Tests for the criterion-resolution rule."""

from __future__ import annotations

from methodology.merge import resolve_attestations
from methodology.types import CriterionAttestation


def _att(cid: str, verdict: str, source: str = "p") -> CriterionAttestation:
    layer, component, _stage_marker, _name = cid.split(".", 3)
    return CriterionAttestation(
        layer=layer,  # type: ignore[arg-type]
        component=component,  # type: ignore[arg-type]
        criterion_id=cid,
        verdict=verdict,  # type: ignore[arg-type]
        source=source,
    )


def test_no_attestations_means_unsatisfied():
    statuses = resolve_attestations([])
    for s in statuses.values():
        assert not s.satisfied
        assert s.attestation_count == 0


def test_single_verification_satisfies():
    cid = "asset.security.s1.audited"
    statuses = resolve_attestations([_att(cid, "verified")])
    assert statuses[cid].satisfied
    assert len(statuses[cid].verifications) == 1
    assert not statuses[cid].violations


def test_violation_overrides_verifications():
    cid = "asset.security.s1.audited"
    attestations = [
        _att(cid, "verified", source="p1"),
        _att(cid, "verified", source="p2"),
        _att(cid, "violated", source="p3"),
    ]
    statuses = resolve_attestations(attestations)
    assert not statuses[cid].satisfied
    assert len(statuses[cid].verifications) == 2
    assert len(statuses[cid].violations) == 1


def test_unknown_alone_does_not_satisfy():
    cid = "asset.security.s1.audited"
    statuses = resolve_attestations([_att(cid, "unknown")])
    assert not statuses[cid].satisfied


def test_unknown_is_ignored_when_verified_present():
    cid = "asset.security.s1.audited"
    statuses = resolve_attestations(
        [_att(cid, "unknown", "p1"), _att(cid, "verified", "p2")]
    )
    assert statuses[cid].satisfied


def test_unknown_criterion_id_is_silently_dropped():
    statuses = resolve_attestations(
        [
            CriterionAttestation(
                layer="asset",
                component="security",
                criterion_id="asset.security.s1.does_not_exist",
                verdict="verified",
                source="p",
            )
        ]
    )
    assert "asset.security.s1.does_not_exist" not in statuses
