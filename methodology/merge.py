"""Resolve provider attestations into a per-criterion satisfied/unsatisfied status.

Resolution rule (DRA v3.0 §6):

- If at least one provider files ``verified`` AND no provider files ``violated``
  for criterion ``c`` -> ``c`` is **satisfied**.
- If any provider files ``violated`` -> ``c`` is **unsatisfied**, regardless of
  how many ``verified`` attestations exist (default-to-worse).
- If no attestations exist or all are ``unknown`` -> ``c`` is **unsatisfied**
  (opacity is penalised).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .criteria import CRITERIA, get_criterion
from .types import CriterionAttestation, CriterionStatus


def resolve_attestations(attestations: Iterable[CriterionAttestation]) -> dict[str, CriterionStatus]:
    """Group attestations by criterion id and apply the resolution rule.

    Unknown criterion ids are silently dropped (with a debug-friendly accumulator)
    so a stale provider mapping cannot corrupt the matrix. Tests should validate
    that adapters only attest known criteria.
    """
    grouped: dict[str, list[CriterionAttestation]] = defaultdict(list)
    for a in attestations:
        grouped[a.criterion_id].append(a)

    statuses: dict[str, CriterionStatus] = {}
    for criterion in CRITERIA:
        atts = grouped.get(criterion.id, [])
        verifications = [a for a in atts if a.verdict == "verified"]
        violations = [a for a in atts if a.verdict == "violated"]
        satisfied = bool(verifications) and not violations
        statuses[criterion.id] = CriterionStatus(
            criterion=criterion,
            satisfied=satisfied,
            verifications=verifications,
            violations=violations,
        )

    for cid, atts in grouped.items():
        if cid in statuses:
            continue
        try:
            criterion = get_criterion(cid)
        except KeyError:
            continue
        verifications = [a for a in atts if a.verdict == "verified"]
        violations = [a for a in atts if a.verdict == "violated"]
        statuses[cid] = CriterionStatus(
            criterion=criterion,
            satisfied=bool(verifications) and not violations,
            verifications=verifications,
            violations=violations,
        )

    return statuses
