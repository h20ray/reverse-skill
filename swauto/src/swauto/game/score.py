"""Rune scoring — exact recovered weights (docs/07 §3.6).

``eval_rune(rune) = Σ substat_value × weight`` — substats only; prefix,
upgrade level and roll counts have no effect.
"""

from __future__ import annotations

from .constants import STAT_NAMES

WEIGHTS: dict[str, float] = {
    "SPD": 10.0 / 3,        # 3.3333
    "CRate": 10.0 / 3,      # 3.3333
    "CDmg": 20.0 / 7,       # 2.8571
    "HP%": 2.5, "ATK%": 2.5, "DEF%": 2.5, "ACC": 2.5, "RES": 2.5,
    "ATK flat": 0.35, "DEF flat": 0.35,
    "HP flat": 7.0 / 375,   # 0.018667
}


def flatten_rune(rune: dict) -> dict:
    """Flatten a wire-format rune (pri_eff/sec_eff) into the rule map."""
    flat: dict = {
        "rune_id": rune.get("rune_id"),
        "set_id": rune.get("set_id"),
        "class": rune.get("class"),
        "rank": rune.get("rank"),
        "slot_no": rune.get("slot_no"),
        "upgrade_level": rune.get("upgrade_curr", rune.get("upgrade_level", 0)),
        "occupied_id": rune.get("occupied_id", 0),
    }
    for name in WEIGHTS:
        if name in rune:
            flat[name] = rune[name]
    if "sec_eff" in rune:  # live wire format
        for eff in rune.get("sec_eff", []) or []:
            name = STAT_NAMES.get(eff[0], str(eff[0]))
            flat[name] = flat.get(name, 0) + eff[1]
            flat.setdefault("sec_eff_map", {})[eff[0]] = eff[1]
        pri = rune.get("pri_eff") or [0, 0]
        flat["main_" + STAT_NAMES.get(pri[0], str(pri[0]))] = pri[1]
        return flat
    for sub in rune.get("substat_list", []) or []:  # synthetic shape
        name = STAT_NAMES.get(sub.get("type"), str(sub.get("type")))
        flat[name] = flat.get(name, 0) + sub.get("value", 0)
    main = rune.get("main_stat") or {}
    if main:
        name = STAT_NAMES.get(main.get("type"), str(main.get("type")))
        flat["main_" + name] = main.get("value", 0)
    return flat


def rune_score(flat: dict, weights: dict[str, float] | None = None) -> float:
    w = weights or WEIGHTS
    return sum(flat.get(stat, 0) * weight for stat, weight in w.items())
