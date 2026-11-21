"""Game constants (clean-room mirror of the documented tables — docs/07 §3
and the full dump in the case record)."""

GIANT = 8001
DRAGON = 9001
NECRO = 6001
MAGIC = 5001
STEEL = 9501

DUNGEON_EN: dict[int, str] = {
    9001: "Dragon", 9011: "Dragon-Abyss", 8001: "Giant", 8011: "Giant-Abyss",
    6001: "Necro", 6011: "Necro-Abyss", 5001: "Magic", 9501: "Steel",
    9511: "Steel-Abyss", 9502: "Punisher", 9512: "Punisher-Abyss",
    9503: "Spiritual", 9513: "Spiritual-Abyss",
    1001: "Dark", 7001: "Light", 3001: "Water", 2001: "Fire", 4001: "Wind",
}

# units per battle team
DUNGEON_DECK = 3
GIANT_DECK = 7
DRAGON_DECK = 8
MAGIC_DECK = 5
NECRO_DECK = 14
TOA_DECK = 5
ARENA_DECK = 2
GUILD_DECK = 6
D_HOLE_DECK = 16
SECRET_DECK = 9
HOH_DECK = 9
HOH_STAGES = 10
HOH_PIECES_PER_STAGE = 25
RAID_DECK = 9
RIFT_DECK = 8

# rift elements (overlap the elemental-dungeon id space — recovered from the
# oracle constant dump: RIFT_ICE=1001/FIRE=2001/WIND=3001/LIGHT=4001/DARK=5001)
RIFT_ICE = 1001
RIFT_FIRE = 2001
RIFT_WIND = 3001
RIFT_LIGHT = 4001
RIFT_DARK = 5001

# dimension-hole 2A-family monster dungeons (recovered oracle constants —
# D_HOLE_2A_FAMILY maps each dhole monster id to its level). The rune dungeons
# are a separate list D_HOLE_RUNE_DUNGEON = [3101,4101,2101,1101,5101,6101].
D_HOLE_RUNE_DUNGEON = [3101, 4101, 2101, 1101, 5101, 6101]

RUNE_SET: dict[int, str] = {
    1: "Energy", 2: "Guard", 3: "Swift", 4: "Blade", 5: "Rage", 6: "Focus",
    7: "Endure", 8: "Fatal", 10: "Despair", 11: "Vampire", 13: "Violent",
    14: "Nemesis", 15: "Will", 16: "Shield", 17: "Revenge", 18: "Destroy",
    19: "Fight", 20: "Determination", 21: "Enhance", 22: "Accuracy",
    23: "Tolerance", 24: "Seal", 25: "Intangible",
}

# substat ids -> (name, min roll, max roll)
EFF_TYPE: dict[int, tuple[str, int, int]] = {
    1: ("HP flat", 135, 375), 2: ("HP%", 5, 8), 3: ("ATK flat", 10, 20),
    4: ("ATK%", 5, 8), 5: ("DEF flat", 10, 20), 6: ("DEF%", 5, 8),
    8: ("SPD", 4, 6), 9: ("CRate", 4, 6), 10: ("CDmg", 4, 7),
    11: ("RES", 4, 8), 12: ("ACC", 4, 8),
}
STAT_NAMES = {eid: spec[0] for eid, spec in EFF_TYPE.items()}
RUNE_PROPERTY_SPD = 8

SHOP_HEART_ENERGY = 2201001   # social-point energy refill
SHOP_ENERGY_290 = 100004      # 290-crystal energy refill

# refill policy thresholds (docs/07 §3.5)
SOCIAL_REFILL_MIN = 500       # strictly greater than
CRYSTAL_REFILL_MIN = 300      # at least

# magic-shop / guild-shop wire (recovered — work/autosw/trace/_B5_shop_recovery_outcome.md)
SHOP_LIST = "GetBlackMarketList"
SHOP_BUY = "BuyBlackMarketItem"
GUILD_SHOP_LIST = "GetGuildBlackMarketList"
GUILD_SHOP_BUY = "BuyGuildBlackMarketItem"

# item_master_type -> shop-row kind (what a Magic/Guild shop row offers).
# Recovered from the oracle checkShopItem dispatch (B5 §2): 9 == scroll,
# 27 == rune stone, 1/12 == star-monster rows, 8 == the row box itself.
SHOP_TYPE_SCROLL = 9
SHOP_TYPE_STONE = 27
SHOP_TYPE_2STAR = 1
SHOP_TYPE_4STAR = 12
SHOP_TYPE_RUNE = 8  # rune slot rows share this master type (see checkShopItem)

# buy-flags config keys (docs/05 shop checkboxes — the checkShopItem 3rd arg).
SHOP_FLAG_KEYS = ("buy_rune", "buy_stone", "buy_scroll", "buy_unknow",
                  "buy_2star", "buy_4star")

# clear-time policy (docs/07 §3.3)
CLEAR_FLOOR_SECONDS = 20.0
CLEAR_JITTER_SECONDS = 6.0
NO_RECORD_FALLBACK_SECONDS = 240.0

# scenario clear-wait default (recovered DoScenario signature default
# wait=30; exact per-stage timing is not offline-recoverable — the port
# prefers the response clear_time and falls back to this constant).
SCENARIO_WAIT_DEFAULT = 30.0

# inventory capacity caps (probed live from the oracle, 2026-09-07 —
# fresh SWCore instances default rune_max=1500 and artifact_max=1500; the
# check_*_count guards fire strictly over the cap: count > max).
# NOTE: docs/04 §Category-8 says "cap 1,000" — that is WRONG (doc drift,
# see work/autosw/trace/_A3_inventory_outcome.md §5). The real caps are 1500.
RUNE_CAP = 1500
ARTIFACT_CAP = 1500
