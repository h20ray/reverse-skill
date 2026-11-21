"""Game constants recovered from AutoSW's ``constants.pyd`` (live-probed
2026-09-07; full dump at ``work/autosw/trace/constants_dump.json``).

Only the subset the MVP bot engine needs is mirrored here. Keys and values
are identical to the original module.
"""

from __future__ import annotations

# --- Cairos dungeons -------------------------------------------------------
GIANT = 8001
DRAGON = 9001
NECRO = 6001
MAGIC = 5001
STEEL = 9501
DARK_DUNGEON = 1001
LIGHT_DUNGEON = 7001
WATER_DUNGEON = 3001
FIRE_DUNGEON = 2001
WIND_DUNGEON = 4001

DUNGEON_EN: dict[int, str] = {
    9001: "Dragon", 9011: "Dragon-Abyss",
    8001: "Giant", 8011: "Giant-Abyss",
    6001: "Necro", 6011: "Necro-Abyss",
    5001: "Magic",
    9501: "Steel", 9511: "Steel-Abyss",
    9502: "Punisher", 9512: "Punisher-Abyss",
    9503: "Spiritual", 9513: "Spiritual-Abyss",
    1001: "Dark", 7001: "Light", 3001: "Water",
    2001: "Fire", 4001: "Wind",
}

# Deck sizes per content (units per battle team)
DUNGEON_DECK = 3
GIANT_DECK = 7
DRAGON_DECK = 8
MAGIC_DECK = 5
TOA_DECK = 5
SECRET_DECK = 9
ARENA_DECK = 2
GUILD_DECK = 6
D_HOLE_DECK = 16

# --- Dimension Hole (2A) ---------------------------------------------------
D_HOLE_INU = 2202
D_HOLE_BEAR = 2201
D_HOLE_PIXIE = 1202
D_HOLE_FAIRY = 1201
# 2A dungeon id -> unit family id
D_HOLE_2A_FAMILY: dict[int, int] = {
    2202: 110, 2201: 107, 2203: 115, 1201: 101, 1202: 103, 1203: 120,
    3201: 140, 3202: 150, 4201: 132, 4202: 160, 5201: 152, 5202: 159,
    4204: 208, 4203: 165, 6201: 117, 6202: 106,
}

# --- Rune classes / qualities (as used in keep=[5,4,3] payloads) -----------
RUNE_QUALITY: dict[int, str] = {1: "Common", 2: "Magic", 3: "Rare", 4: "Hero", 5: "Legend"}

RUNE_SET: dict[int, str] = {
    1: "Energy", 2: "Guard", 3: "Swift", 4: "Blade", 5: "Rage", 6: "Focus",
    7: "Endure", 8: "Fatal", 10: "Despair", 11: "Vampire", 13: "Violent",
    14: "Nemesis", 15: "Will", 16: "Shield", 17: "Revenge", 18: "Destroy",
    19: "Fight", 20: "Determination", 21: "Enhance", 22: "Accuracy",
    23: "Tolerance", 24: "Seal", 25: "Intangible",
}

# Substat property ids (EFF_TYPE table)
EFF_TYPE: dict[int, tuple[str, int, int]] = {
    1: ("HP flat", 135, 375), 2: ("HP%", 5, 8), 3: ("ATK flat", 10, 20),
    4: ("ATK%", 5, 8), 5: ("DEF flat", 10, 20), 6: ("DEF%", 5, 8),
    8: ("SPD", 4, 6), 9: ("CRate", 4, 6), 10: ("CDmg", 4, 7),
    11: ("RES", 4, 8), 12: ("ACC", 4, 8),
}
RUNE_PROPERTY_SPD = 8
RUNE_PROPERTY_CR = 9
RUNE_PROPERTY_CD = 10
RUNE_PROPERTY_RES = 11
RUNE_PROPERTY_ACC = 12

# --- Shop item ids (energy refill paths) -----------------------------------
SHOP_ENERGY = 100001
SHOP_ENERGY_190 = 2201008
SHOP_ENERGY_290 = 100004
SHOP_HEART_ENERGY = 2201001  # social-point energy refill
