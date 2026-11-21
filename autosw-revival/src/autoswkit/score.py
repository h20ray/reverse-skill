"""Rune scoring (smart level) — Python port of the ``score.pyd`` semantics.

The original computes a linear weighted score over substats:
``RuneScore = sum(substat_value * weight)`` with SPD the dominant weight.
Exact weight constants live in compiled code; they are configurable here so
captured/real values can be plugged in later (docs/03 §7).
"""

from __future__ import annotations

from .constants import EFF_TYPE

# Stat-name -> weight per point. EXACT values recovered from the original
# ``eval_rune`` by probing synthetic runes (docs/07 §3.3); verified against
# real runes (e.g. legend 6-star scores 105.0 = 14*2.5 + 13*2.5 + 6*3.333 + 7*2.5).
DEFAULT_WEIGHTS: dict[str, float] = {
    "SPD": 10.0 / 3,          # 3.3333
    "CRate": 10.0 / 3,        # 3.3333
    "CDmg": 20.0 / 7,         # 2.8571
    "HP%": 2.5,
    "ATK%": 2.5,
    "DEF%": 2.5,
    "ACC": 2.5,
    "RES": 2.5,
    "ATK flat": 0.35,
    "DEF flat": 0.35,
    "HP flat": 7.0 / 375,     # 0.018667
}

# EFF_TYPE id -> flat-map stat name
STAT_NAMES: dict[int, str] = {eid: spec[0] for eid, spec in EFF_TYPE.items()}


def flatten_rune(rune: dict) -> dict:
    """Build the flat attribute map the rule engine evaluates.

    Accepts either shape:
    - the **live wire format** (``sec_eff``/``pri_eff``/``upgrade_curr``,
      from HubUserLogin captures — see ``autoswkit.account``);
    - the synthetic shape (``substat_list``/``main_stat`` with numeric
      ``type`` ids).

    The returned map carries the substats by name plus the rune identity
    fields used by rulesets (``set_id``, ``class``, ``rank``, ``slot_no``,
    ``upgrade_level``).
    """
    flat = {
        "rune_id": rune.get("rune_id"),
        "set_id": rune.get("set_id"),
        "class": rune.get("class"),
        "rank": rune.get("rank"),
        "slot_no": rune.get("slot_no"),
        "upgrade_level": rune.get("upgrade_curr", rune.get("upgrade_level", 0)),
        "occupied_id": rune.get("occupied_id", 0),
    }
    for key in ("SPD", "CRate", "CDmg", "ATK%", "HP%", "DEF%",
                "ATK flat", "HP flat", "DEF flat", "ACC", "RES"):
        if key in rune:  # already flat
            flat[key] = rune[key]
    if "sec_eff" in rune:  # live wire format
        for eff in rune.get("sec_eff", []) or []:
            eid, value = eff[0], eff[1]
            name = STAT_NAMES.get(eid, str(eid))
            flat[name] = flat.get(name, 0) + value
            flat.setdefault("sec_eff_map", {})[eid] = value
        pri = rune.get("pri_eff") or [0, 0]
        flat["main_" + STAT_NAMES.get(pri[0], str(pri[0]))] = pri[1]
        return flat
    for sub in rune.get("substat_list", []) or []:
        name = STAT_NAMES.get(sub.get("type"), str(sub.get("type")))
        flat[name] = flat.get(name, 0) + sub.get("value", 0)
    main = rune.get("main_stat") or {}
    if main:
        name = STAT_NAMES.get(main.get("type"), str(main.get("type")))
        flat["main_" + name] = main.get("value", 0)
    return flat


def rune_score(flat: dict, weights: dict[str, float] | None = None) -> float:
    """Weighted substat score (``Σ value × weight``); SPD dominant."""
    w = weights or DEFAULT_WEIGHTS
    return sum(flat.get(stat, 0) * weight for stat, weight in w.items())
