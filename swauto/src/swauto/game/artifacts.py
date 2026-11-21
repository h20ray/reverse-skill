"""Artifact evaluation — clean-room port of the recovered semantics.

Wire format (HubUserLogin): ``pri_effect: [id, value, ...]`` with ids
100/101/102 (HP/ATK/DEF flat main), ``sec_effects: [[id, value, ...], ...]``
with ids 200–411 per the ARTI_SUB table.

Recovered evaluation semantics (live probe against the compiled oracle,
docs/07 evidence index). ``getArtifactValuableSub(arti, guess)`` (STATIC) was
swept exhaustively over the 777 real MooN artifacts plus adversarial synthetic
artifacts:

- ``guess=True`` -> ``{sid: ratio}`` for each PRESENT valuable sub;
- ``guess=False`` -> ``{sid: 1}`` for the strict subset whose value is above
  the sub's per-sub floor.

A sub is *valuable* iff its id is in the valuable union (presence-only group
OR value-floored group) and NOT in the never set. Verified 777/777 real,
5000/5000 synthetic, and exhaustive floor-boundary sweeps against the compiled
module — the old ``ratio >= 1.0`` heuristic was WRONG (it counted never-valid
subs above ratio 1 and dropped presence/floor groups below it).
"""

from __future__ import annotations

# main stat ids (pri_effect)
ARTI_MAIN: dict[int, str] = {100: "HP flat", 101: "ATK flat", 102: "DEF flat"}

# Substat ids that are NEVER valuable regardless of value (whitelist-excluded).
# Recovered by sweeping every ARTI_SUB id 200–411 at huge value: these never
# register. SPD-under-inability, CR-increasing effect, counterattack dmg,
# reflect dmg, crushing-hit dmg, dmg-received-under-inability, HP/ATB-when-
# revived, Skill-4 CD.
ARTI_NEVER_VALUABLE: frozenset[int] = frozenset({203, 207, 209, 211, 212, 213,
                                                 216, 217, 403})

# Substat ids that are valuable whenever PRESENT (any value, even 0/negative).
# Recovered: these register at value 0.0 in the compiled valuable set.
ARTI_PRESENCE_VALUABLE: frozenset[int] = frozenset({204, 205, 218, 219, 220,
                                                    221, 226, 400, 401, 402,
                                                    404, 405, 406, 407, 408,
                                                    409, 410, 411})

# Per-sub minimum *value* before a floored sub registers valuable (guess=False
# form). Recovered by sweeping each sub's value at 0.5 steps from 0 and reading
# the first value that appears. Values are the raw sec_effects value.
ARTI_VALUE_FLOOR: dict[int, float] = {
    200: 12, 201: 12, 202: 12,   # HP/ATK/DEF% proportional to lost HP
    206: 5, 208: 3, 210: 3,      # SPD incr., counter/co-op dmg, bomb dmg
    214: 3, 215: 6,              # CD received, life drain
    222: 5, 223: 10,             # CD up as enemy HP good/bad
    224: 3, 225: 3,              # single-target CD, counter/co-op DMG
    300: 4, 301: 4, 302: 4, 303: 4, 304: 4,   # damage dealt on element
    305: 5, 306: 5, 307: 5, 308: 5, 309: 5,   # damage received from element
}

# substat ids -> (description, min_roll, max_roll)
ARTI_SUB: dict[int, tuple[str, float, float]] = {
    200: ("ATK% proportional to lost HP", 9, 14),
    201: ("DEF% proportional to lost HP", 9, 14),
    202: ("SPD% proportional to lost HP", 9, 14),
    203: ("SPD under inability", 3, 6),
    204: ("ATK increasing effect", 3, 5),
    205: ("DEF increasing effect", 2, 4),
    206: ("SPD increasing effect", 4, 6),
    207: ("CR increasing effect", 3, 6),
    208: ("Damage by counterattack", 2, 4),
    209: ("Damage by attack together", 2, 4),
    210: ("Bomb damage", 2, 4),
    211: ("Reflect damage", 1, 3),
    212: ("Crushing hit damage", 2, 4),
    213: ("Damage received under inability", 1, 3),
    214: ("CD received", 2, 4),
    215: ("Life drain", 5, 8),
    216: ("HP when revived", 4, 6),
    217: ("ATB when revived", 4, 6),
    218: ("Addition damage by HP", 0.2, 0.3),
    219: ("Addition damage by ATK", 2, 4),
    220: ("Addition damage by DEF", 2, 4),
    221: ("Addition damage by SPD", 25, 40),
    222: ("CD up as enemy HP good", 4, 6),
    223: ("CD up as enemy HP bad", 8, 12),
    224: ("Single target skill CD", 2, 4),
    225: ("Counterattack/Co-op DMG", 2, 4),
    226: ("ATK/DEF increasing effect", 3, 5),
    300: ("Damage dealt on fire", 3, 5),
    301: ("Damage dealt on water", 3, 5),
    302: ("Damage dealt on wind", 3, 5),
    303: ("Damage dealt on light", 3, 5),
    304: ("Damage dealt on dark", 3, 5),
    305: ("Damage received from fire", 4, 6),
    306: ("Damage received from water", 4, 6),
    307: ("Damage received from wind", 4, 6),
    308: ("Damage received from light", 4, 6),
    309: ("Damage received from dark", 4, 6),
    400: ("Skill 1 CD", 4, 6),
    401: ("Skill 2 CD", 4, 6),
    402: ("Skill 3 CD", 4, 6),
    403: ("Skill 4 CD", 4, 6),
    404: ("Skill 1 Recovery", 4, 6),
    405: ("Skill 2 Recovery", 4, 6),
    406: ("Skill 3 Recovery", 4, 6),
    407: ("Skill 1 Accuracy", 4, 6),
    408: ("Skill 2 Accuracy", 4, 6),
    409: ("Skill 3 Accuracy", 4, 6),
    410: ("Skill 3/4 CD", 4, 6),
    411: ("First Attack CD", 4, 6),
}

# archetype/unit style ids (unit_style field)
UNIT_STYLES: dict[int, str] = {0: "None", 1: "Attack", 2: "Defense", 3: "HP", 4: "Support"}
# attribute ids (attribute field)
ATTRIBUTES: dict[int, str] = {0: "Any", 1: "Water", 2: "Fire", 3: "Wind",
                              4: "Light", 5: "Dark", 98: "Intangible"}


def sub_ratio(value: float, sub_id: int) -> float:
    """Roll-quality ratio: value / midpoint(min_roll, max_roll)."""
    _, lo, hi = ARTI_SUB[sub_id]
    return value / ((lo + hi) / 2)


def flatten_artifact(arti: dict) -> dict:
    """Flatten a wire-format artifact into the rule-engine map.

    Flat keys: identity fields (`type`, `attribute` name, `unit_style`
    name, `rank`, `level`), main stat (`main_HP flat` etc.) and one entry
    per substat by description name, plus `sub_ratios` {id: ratio}.
    """
    flat: dict = {
        "artifact_id": arti.get("rid"),
        "type": arti.get("type"),
        "attribute": ATTRIBUTES.get(arti.get("attribute", 0), arti.get("attribute")),
        "unit_style": UNIT_STYLES.get(arti.get("unit_style", 0), arti.get("unit_style")),
        "rank": arti.get("rank"),
        "upgrade_level": arti.get("level", 0),
        "occupied_id": arti.get("occupied_id", 0),
    }
    pri = arti.get("pri_effect") or [0, 0]
    flat["main_" + ARTI_MAIN.get(pri[0], str(pri[0]))] = pri[1]
    ratios: dict[int, float] = {}
    for eff in arti.get("sec_effects", []) or []:
        sid, value = eff[0], eff[1]
        name = ARTI_SUB[sid][0] if sid in ARTI_SUB else str(sid)
        flat[name] = value
        if sid in ARTI_SUB:
            ratios[sid] = round(sub_ratio(value, sid), 4)
    flat["sub_ratios"] = ratios
    return flat


def valuable_subs(arti: dict) -> dict[int, float]:
    """Substat ids that count as valuable on this artifact (port of the
    compiled ``getArtifactValuableSub(arti, guess=False)`` -> ``{sid: 1}``).

    A present substat is valuable iff its id is in the valuable union and NOT
    in :data:`ARTI_NEVER_VALUABLE`, AND (it is in
    :data:`ARTI_PRESENCE_VALUABLE` OR its raw value is >= its floor in
    :data:`ARTI_VALUE_FLOOR`).

    Verified 777/777 real artifacts + 5000/5000 synthetic + exhaustive
    floor-boundary sweeps against the compiled module.
    """
    valuable: dict[int, float] = {}
    for eff in arti.get("sec_effects", []) or []:
        sid, value = eff[0], eff[1]
        if sid in ARTI_NEVER_VALUABLE:
            continue
        if sid in ARTI_PRESENCE_VALUABLE:
            valuable[sid] = 1
        elif sid in ARTI_VALUE_FLOOR and value >= ARTI_VALUE_FLOOR[sid]:
            valuable[sid] = 1
    return valuable
