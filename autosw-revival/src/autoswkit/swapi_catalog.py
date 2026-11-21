"""Complete ``SWAPI`` method catalog (180 methods) as recovered from the
AutoSW sample (summon.pyd / common.pyd). Semantics for every entry are in
docs/04-swapi-reference.md; this module is the navigable skeleton for the
P1 protocol-layer implementation.

Methods marked as RPC in the docs issue their own (or a related) server
command; the rest are client-side helpers.
"""

CATEGORIES: tuple[str, ...] = (
    "auth_session",
    "dungeon_pve",
    "arena_pvp",
    "tower",
    "dimension_hole",
    "rift_raid",
    "guild",
    "runes_artifacts",
    "monsters_decks",
    "economy_shops",
    "quests_events_social",
    "telemetry_utils",
)

SWAPI_METHODS: dict[str, tuple[str, ...]] = {
    "auth_session": (
        "HubUserLogin", "login_rq", "manual_login_times", "manual_relogin",
        "checkLoginBlock", "fetch_version", "GetPlayerServerConnectElapsedTime",
        "knlCurrentUpTime", "refresh_ts", "send", "url", "server_host",
        "server_id", "appid", "inited", "debug",
    ),
    "dungeon_pve": (
        "DoDungeon", "loopDungeon", "GetDungeonList", "GetMAXDungeonStages",
        "DUNGEON_MAX_STAGES", "GetDungeonBestCommunityRanking",
        "no_record_stages", "get_dungeon_name", "DoScenario", "loopScenario",
        "get_HOH_current", "loopHOH", "loopInstance", "getInstanceList",
        "loopEventInstance",
    ),
    "arena_pvp": (
        "DoArena", "loopArena", "GetArenaWizardList", "GetArenaRank",
        "GetMyArenaRank", "getArenaBestRank", "getArenaList", "getRivalEnergy",
    ),
    "tower": (
        "DoTower", "loopTower", "loopAllTOA", "loopAllTower", "loopTOAHell",
        "getTowerTime", "getTowerTimeLegacy",
    ),
    "dimension_hole": (
        "DoDHole", "loop_D_HOLE", "GetDimensionHoleQuestInfo",
        "GetDimensionHoleRaidInfo", "GetBestDHOLERank", "doAllDHoleQuests",
        "UpdateDimensionHoleQuest", "RewardDimensionHoleQuest",
    ),
    "rift_raid": (
        "DoRift", "loopRift", "doAllRift", "GetBestClearRiftDungeon",
        "_create_rift_deck", "RIFT_CONFIG", "loopRaid",
        "GetRiftOfWorldsRaidServerInfo", "RAID_CONFIG",
    ),
    "guild": (
        "GetGuildInfo", "GetGuildID", "loopGuildwar", "loopGuildRival",
        "getGuildWarInfo", "getGuildWarEnergy", "getGuildRivalInfo",
        "getGWDefense", "DoMaze", "getMazeinfo",
    ),
    "runes_artifacts": (
        "eval_rune", "handle_rune", "sellRune", "SELL", "log_rune",
        "check_rune_count", "rune_count", "rune_max", "rune_options",
        "rune_check", "_rune_score", "_best_six_runes", "_get_rune_id",
        "process_ancient_rune", "SmartUpgradeCheckRune", "smartUpgradeCheck",
        "upgradeUntil", "power_up_all_runes", "checkMaxRoll",
        "handleRuneCraft", "sellRuneCraft", "log_stones", "isShitStone",
        "handle_artifact", "SellArtifacts", "log_artifact",
        "check_artifact_count", "arti_count", "arti_max", "arti_options",
        "artifact_check", "smartArtifactCheck", "smartArtifactUpgradeCheck",
        "upgradeArtifact", "upgradeArtifactUntil", "getArtifactValuableSub",
        "getValuableStats", "isTrashStats", "craft_options", "inventory_clean",
    ),
    "monsters_decks": (
        "eval_unit", "best_equip", "_sortUnits", "fill_unit", "unmaxed_unit",
        "updateUnitExp", "ConvertItemToUnit", "SetRepUnit", "GetRecentDecks",
        "_get_or_create_deck", "_resolve_unit_deck_ids", "log_team",
        "loopallunskill", "get_unit_name", "unit_images",
    ),
    "economy_shops": (
        "getShopList", "buyShopItem", "checkShopItem", "checkAndBuyShop",
        "getGuildShopList", "buyGuildShopItem", "buyitem", "BuyItemCart",
        "BuyAncientCrystal", "smart_refill",
    ),
    "quests_events_social": (
        "getAllDailyQuest", "doAllDailyQuests", "updateDailyQuest",
        "collabo_getQuestList", "collabo_dailyQuest", "collabo_updateQuestList",
        "collabo_rewardQuest", "doEvent", "doHiddenEvent", "getEventInstanceID",
        "GetEventTimeTable", "CheckDailyReward", "checkDailyReward",
        "getDailyReward", "getDailyRewardPoint", "ReceiveDailyRewardSpecial",
        "receiveDailyRewardInactive", "receiveDailyRewardNewUser",
        "receiveDailyRewardSpecialEvent", "receiveDailyRewardSpecialPass",
        "receivePlayPassReward", "GetMailList", "ReceiveMail", "claim_mail",
        "GetFriendList", "getFriendListWid", "sendDailyGift", "VisitFriend",
        "farm_rep", "farm_rep_error", "farm_deter",
    ),
    "telemetry_utils": (
        "getWizardInfo", "GetConfigFromLog", "getChecker", "load_rules",
        "save_rules", "rules", "get_all_coupons", "redeem_all_coupons",
        "used_coupon", "bot", "_initial",
    ),
}

assert sum(len(v) for v in SWAPI_METHODS.values()) == 180, "catalog must hold 180 methods"
