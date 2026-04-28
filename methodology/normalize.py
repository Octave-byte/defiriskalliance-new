"""Scale helpers: map external signals to DRA 0–10 (higher = safer)."""

from __future__ import annotations

import re


def clamp_10(x: float) -> float:
    return max(0.0, min(10.0, float(x)))


def scale_01_to_10(x: float | None) -> float | None:
    if x is None:
        return None
    return clamp_10(float(x) * 10.0)


def scale_0_100_to_10(x: float | None) -> float | None:
    if x is None:
        return None
    return clamp_10(float(x) / 10.0)


_GRADE_MAP = {
    "A+": 10.0, "A": 9.0, "A-": 8.5,
    "B+": 8.0, "B": 7.0, "B-": 6.5,
    "C+": 6.0, "C": 5.5, "C-": 5.0,
    "D+": 4.0, "D": 3.0, "D-": 2.5,
    "F": 0.0, "NR": 0.0,
}


def bluechip_letter_to_10(grade: str | None) -> float | None:
    if not grade:
        return None
    g = grade.strip().upper()
    if g in _GRADE_MAP:
        return _GRADE_MAP[g]
    m = re.match(r"^([ABCDF][+-]?)$", g)
    if m:
        return _GRADE_MAP.get(m.group(1))
    return None
