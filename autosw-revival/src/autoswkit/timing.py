"""Clear-time simulation, ported from the live-probed ``summon.SWCore``
(``work/autosw/trace/tower*.py``, 2026-09-07).

Original: ``SWCore.getTowerTime(self, level, difficulty)`` — ToA floors.
Normal/Hard are deterministic linear curves; Hell adds a large uniform
jitter on a slowly growing base (formula inferred from sampling, exact
constant unknown — see docs/05-automation-engine.md §7).
"""

from __future__ import annotations

import random

# ToA difficulty ids used by the original (1=normal, 2=hard, 3=hell)
TOA_NORMAL = 1
TOA_HARD = 2
TOA_HELL = 3

_NORMAL_FLOOR_1 = 15.4
_NORMAL_FLOOR_2 = 12.8
_NORMAL_PER_FLOOR = 6.4      # floors 3..100: exactly 6.4 * floor
_HARD_PER_FLOOR = 10.4       # all floors: exactly 10.4 * floor
_HELL_BASE_1 = 1810.0        # sampled mean at floor 1
_HELL_PER_FLOOR = 7.0        # base growth (sampled: mean 1824 -> 2190 over 49 floors)
_HELL_JITTER = 300.0         # sampled spread roughly +/-300 s


def get_tower_time(level: int, difficulty: int,
                   rng: random.Random | None = None) -> float:
    """Simulated human-like clear time in seconds for a ToA floor.

    Matches the original's output for normal/hard; hell is statistical.
    """
    rng = rng or random.Random()
    r = rng.uniform if hasattr(rng, "uniform") else (lambda a, b: rng() * (b - a) + a)
    level = max(1, int(level))
    if difficulty == TOA_HARD:
        return _HARD_PER_FLOOR * level
    if difficulty == TOA_HELL:
        base = _HELL_BASE_1 + _HELL_PER_FLOOR * (level - 1)
        return float(r(base - _HELL_JITTER, base + _HELL_JITTER))
    if level == 1:
        return _NORMAL_FLOOR_1
    if level == 2:
        return _NORMAL_FLOOR_2
    return _NORMAL_PER_FLOOR * level
