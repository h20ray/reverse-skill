"""Rune evaluation helpers recovered from the compiled modules (docs/07 §3.8–3.9).

Clean-room ports of three documented ``summon.SWCore`` predicates, each verified
empirically against the compiled module (runnable oracle, `work/autosw/trace/`):

- ``isTrashStats(sets, prop)``  — static predicate; **True iff ``prop`` is a
  flat HP/ATK/DEF substat id** (1/3/5). The ``sets`` argument is ignored by the
  compiled body (dead parameter kept for call compatibility).
- ``getValuableStats(rune, smart)`` — which substats count as "valuable" for a
  rune at a smart level (see module rule below).
- ``smartUpgradeCheck(old, new, vstats, speed_upgrade_only)`` — whether the
  upgrade rolled a valuable stat (``True`` = stop powering / keep) or not
  (``None`` = keep powering).
"""

from __future__ import annotations

# flat substat ids are "trash" rolls (never valuable)
TRASH_FLAT_IDS = frozenset({1, 3, 5})           # HP/ATK/DEF flat

# "hard" valuable substat ids: percentage stats + SPD/CR/CD.
HARD_VALUABLE_IDS = frozenset({2, 4, 6, 8, 9, 10})  # HP%/ATK%/DEF%/SPD/CR/CD%

# rune class that ever registers valuable stats. Recovered empirically: of the
# real account's classes (0..20 swept), only ``class == 6`` yielded any
# valuable; classes 7+ are "ancient"-era ids that the original treats as trash.
LEGEND_CLASS = 6

# set-specific stat de-emphasis. The original drops ONE percentage stat from the
# valuable set based on the rune set: Fatal (ATK-oriented) de-emphasises DEF%,
# Guard (DEF-oriented) de-emphasises ATK%. Recovered by sweeping set_id over a
# fixed 6-sub rune and confirming 7452/7452 over the real pool.
SET_DEEMPHASIS = {8: 6, 2: 4}   # Fatal -> drops DEF%(6); Guard -> drops ATK%(4)

# Per-stat minimum *grown* value before a roll counts as a valuable upgrade.
# Recovered by sweeping each stat's value on the compiled module: a roll that
# lands the stat below this floor is a failed/trash roll (the caller does not
# keep the rune as a result of that stat). Units are the raw substat wire value
# (SPD is integer speed, CR/CD are percent points, HP%/ATK%/DEF% are percent).
MIN_VALUABLE_VALUE = {
    2: 13,   # HP%
    4: 13,   # ATK%
    6: 13,   # DEF%
    8: 10,   # SPD
    9: 10,   # CR%
    10: 11,  # CD%
}


def is_trash_stat(prop: int) -> bool:
    """True iff ``prop`` is a flat HP/ATK/DEF substat id (the "trash" roll).

    Port of ``SWCore.isTrashStats(sets, prop)``. The compiled module ignores
    ``sets`` and returns ``prop in (1, 3, 5)``; the parameter is retained only
    for signature compatibility with callers that pass a set list.
    """
    return prop in TRASH_FLAT_IDS


def is_trash_stats(_sets, prop: int) -> bool:
    """Full-signature alias: ``isTrashStats(sets, prop) -> bool``.

    Some call sites pass the two-argument form; ``_sets`` is unused.
    """
    return is_trash_stat(prop)


def _substat_ids(rune: dict) -> list[int]:
    """Substat type ids from the live ``sec_eff`` wire format
    (``[type_id, value, inherent, upgrade_count]``)."""
    return [eff[0] for eff in rune.get("sec_eff", []) or []]


def _stat_value(rune: dict, stat_id: int) -> int:
    """Raw substat value for one stat id (0 if absent). See ``sec_eff`` layout."""
    for eff in rune.get("sec_eff", []) or []:
        if eff[0] == stat_id:
            return eff[1]
    return 0


def _upgraded_value(rune_old: dict, rune_new: dict, stat_id: int) -> int:
    """Substat value delta for one stat id across an upgrade."""
    return _stat_value(rune_new, stat_id) - _stat_value(rune_old, stat_id)


def get_valuable_stats(rune: dict, smart: int = 0) -> dict[int, int]:
    """Which substats count as valuable on ``rune``.

    Recovered rule (verified 7452/7452 against the compiled ``SWCore`` over the
    real account pool at smart 0/3/5/80):

    - ``class != 6`` -> always ``{}`` (only the legend class registers any).
    - ``class == 6`` -> every hard sub present is valuable at value ``1``,
      except:
        - flats (1/3/5) and utility (11 RES / 12 ACC) are never valuable;
        - Fatal runes (set 8) drop DEF%(6); Guard runes (set 2) drop ATK%(4).
    - ``smart`` is read but never changes the result on any observed input
      (kept in the signature for call compatibility only).

    Returns ``{type_id: 1, ...}``.
    """
    if int(rune.get("class", 0) or 0) != LEGEND_CLASS:
        return {}
    drop = SET_DEEMPHASIS.get(rune.get("set_id"))
    subs = _substat_ids(rune)
    return {sid: 1 for sid in subs
            if sid in HARD_VALUABLE_IDS and sid != drop}


def smart_upgrade_check(rune_old: dict, rune_new: dict, vstats: dict[int, int],
                        speed_upgrade_only: bool = False) -> bool | None:
    """Whether the upgrade ``rune_old -> rune_new`` rolled a valuable stat.

    Port of ``SWCore.smartUpgradeCheck`` (return domain recovered empirically):

    - ``True``  — a ``vstats``-listed substat grew AND its grown value is at
      least ``MIN_VALUABLE_VALUE[sid]``. The caller stops powering and keeps
      the rune.
    - ``False`` — a ``vstats``-listed substat grew but never cleared its value
      floor (a low/trash roll), OR (under ``speed_upgrade_only``) a valuable
      non-SPD stat grew while SPD did not. The rune is not a keeper as-is.
    - ``None``  — no ``vstats``-listed stat grew at all; keep powering.

    ``vstats`` is the authoritative valuable map (from ``get_valuable_stats`` on
    the pre-upgrade rune). Stat ids not present in ``vstats`` are treated as
    non-valuable even if they grew. ``speed_upgrade_only`` restricts "True" to
    SPD (stat id 8); any other valuable gain is reported as ``False`` (a failed
    speed hunt rather than a keep).
    """
    for sid in vstats:
        if _upgraded_value(rune_old, rune_new, sid) > 0:
            if _stat_value(rune_new, sid) < MIN_VALUABLE_VALUE[sid]:
                return False
            if speed_upgrade_only:
                return True if sid == 8 else False
            return True
    return None