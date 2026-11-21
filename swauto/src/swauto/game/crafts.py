"""Craft items (gems/grinds/enchants) and upgrade decisions.

Recovered semantics (live-probed against the original, docs/07 evidence):

- ``craft_type``: 1 gems, 2 grindstones, 3/4 enchant gems, 5/6 ancient.
- Gem quality is grade-based: the last digit of ``craft_type_id`` is the
  grade (3/4/5). Observed policy vs the smart threshold:
    grade 5  -> always kept
    grade 4  -> kept only while smart <= 4
    grade 3  -> never kept (sold even at smart 0)
- Ancient grindstones (type 5) are always kept; ancient gems (6) and enchant
  gems (3/4) follow grade thresholds.
- The upgrade decision (``smartUpgradeCheck``) is a power-up-then-judge
  cycle: each cycle sends ``UpgradeRune_v2 {rune_id}`` (+1 level), then
  re-evaluates the rune; the caller repeats until the rune is sold, kept,
  or at max level.
"""

from __future__ import annotations

from . import constants as C
from .evaluate import is_trash_stat  # flat-substat "trash" predicate (the drop half)


def craft_grade(craft: dict) -> int | None:
    """Grade for normal gems/grinds (types 1/2): last digit of type_id."""
    ct = craft.get("craft_type")
    if ct in (1, 2):
        return int(str(craft.get("craft_type_id"))[-1])
    return None


# ``is_trash_stat`` (recovered from SWCore.isTrashStats) is the *flat substat*
# trash predicate — the keep/sell decision's "does this roll count as trash"
# half, paired with ``is_shit_stone`` for craft items. Re-exported here for
# callers that group both drop kinds together.

is_trash_stat = is_trash_stat  # re-export


def is_shit_stone(craft: dict, smart: int = 0) -> bool:
    """Sell decision for craft items (port of the observed policy).

    Ancient grindstones are always kept; everything else is graded, and
    the smart threshold decides (mirrors the original's bisection-verified
    behaviour).
    """
    ct = craft.get("craft_type")
    if ct == 5:
        return False  # ancient grindstones always kept
    grade = craft_grade(craft)
    if grade is None:  # enchant (3/4) and ancient gems (6): treated high-grade
        return smart > 80
    if grade >= 5:
        return False
    if grade == 4:
        return smart > 4
    return True  # grade <= 3: always sold
