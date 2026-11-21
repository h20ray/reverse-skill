"""Clear-time simulation (documented formulas — docs/07 §3.3).

Cairos: max(own best record, 20) + uniform(0, 6) seconds.
ToA: exact per-floor curves recovered from the original.
"""

from __future__ import annotations

import random

from . import constants as C

TOA_NORMAL, TOA_HARD, TOA_HELL = 1, 2, 3
_NORMAL_F1, _NORMAL_F2, _NORMAL_PER = 15.4, 12.8, 6.4
_HARD_PER = 10.4
_HELL_BASE_1, _HELL_PER, _HELL_JITTER = 1810.0, 7.0, 300.0


def tower_time(level: int, difficulty: int, rng: random.Random | None = None) -> float:
    rng = rng or random.Random()
    level = max(1, int(level))
    if difficulty == TOA_HARD:
        return _HARD_PER * level
    if difficulty == TOA_HELL:
        base = _HELL_BASE_1 + _HELL_PER * (level - 1)
        return float(rng.uniform(base - _HELL_JITTER, base + _HELL_JITTER))
    if level == 1:
        return _NORMAL_F1
    if level == 2:
        return _NORMAL_F2
    return _NORMAL_PER * level


def dungeon_time(best_record_seconds: float | None,
                 fallback: float = C.NO_RECORD_FALLBACK_SECONDS,
                 rng: random.Random | None = None) -> float:
    """max(record|fallback, floor) + uniform(0, jitter)."""
    rng = rng or random.Random()
    base = best_record_seconds if best_record_seconds else fallback
    return max(base, C.CLEAR_FLOOR_SECONDS) + rng.uniform(0, C.CLEAR_JITTER_SECONDS)
