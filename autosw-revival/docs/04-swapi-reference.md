# AutoSW — `SWAPI` Method Reference (180 methods)

> Part of the `autosw-revival/docs/` revival set. Complete inventory of the
> `common.SWAPI` / `summon.SWAPI` class — the headless game client that speaks
> the encrypted Com2uS protocol directly (`gateway_c2.php`, envelope spec in
> `02-crypto-protocol.md`). Names recovered from `summon.pyd` / `common.pyd`
> string tables and dynamic analysis; full evidence in
> [`../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md`](../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md)
> §8.1. The names are also available as data in
> `src/autoswkit/swapi_catalog.py`.

Methods marked **RPC** send their own name (or a related server command) as the
encrypted request `command`; the rest are client-side helpers/properties.

---

## Category 1 — Authentication, Session & Protocol Core (16)

| Method | Purpose |
|--------|---------|
| `HubUserLogin` | Initial authentication handshake with the Com2uS gateway |
| `login_rq` | Constructs the encrypted login request payload |
| `manual_login_times` | Tracks login frequency to avoid rate-limit triggers |
| `manual_relogin` | Refreshes expired session tokens |
| `checkLoginBlock` | Verifies whether the account is flagged/banned |
| `fetch_version` | Queries the Com2uS CDN for live client/resource patch versions |
| `GetPlayerServerConnectElapsedTime` | Server uptime / latency offset |
| `knlCurrentUpTime` | Windows kernel boot time, to mimic client telemetry |
| `refresh_ts` | Synchronizes client timestamps with the server clock |
| `send` | **Low-level dispatcher**: encrypt → HTTP POST → decrypt (the only network path) |
| `url` | Target endpoint URL (`gateway_c2.php`) |
| `server_host` | Hostname of the active server cluster |
| `server_id` | Numeric game-server ID (1=Korea, 2=Global, 3=Europe, 4=Asia, 5=Japan, 6=China) |
| `appid` | Game application identifier |
| `inited` | Initialization-state flag |
| `debug` | Logging verbosity flag |

## Category 2 — Dungeon & PVE (15)

| Method | Purpose |
|--------|---------|
| `DoDungeon` | Single dungeon run: start → sleep simulated clear time → submit result |
| `loopDungeon` | Persistent dungeon-farming loop (drives `DThread`) |
| `GetDungeonList` | Unlocked Cairos dungeons + stages |
| `GetMAXDungeonStages` | Highest completed stage per dungeon |
| `DUNGEON_MAX_STAGES` | Static stage map (e.g. Abyss 1–12) |
| `GetDungeonBestCommunityRanking` | Top community clear times |
| `no_record_stages` | Skip record submission to avoid leaderboard flags |
| `get_dungeon_name` | Dungeon ID → display name |
| `DoScenario` | Single story-scenario run |
| `loopScenario` | Scenario farming loop (drives `SThread`) |
| `get_HOH_current` | Active Hall of Heroes info |
| `loopHOH` | Clears all 10 Hall of Heroes stages |
| `loopInstance` | Generic instance-dungeon loop |
| `getInstanceList` | Active Secret Dungeons / elemental rifts |
| `loopEventInstance` | Event farming dungeons |

## Category 3 — Arena & PVP (8)

| Method | Purpose |
|--------|---------|
| `DoArena` | Battle a targeted arena opponent |
| `loopArena` | Arena loop: opponents + NPC rivals (drives `AThread`) |
| `GetArenaWizardList` | Matchmaking list of 10 arena targets |
| `GetArenaRank` | Current arena ranking/score tier |
| `GetMyArenaRank` | Personal arena standing |
| `getArenaBestRank` | All-time peak ranking |
| `getArenaList` | Parsed list of current arena targets |
| `getRivalEnergy` | NPC rival battles remaining + cooldowns |

## Category 4 — Tower of Ascension (7)

| Method | Purpose |
|--------|---------|
| `DoTower` | Single ToA floor battle |
| `loopTower` | Continuous normal-ToA climb |
| `loopAllTOA` | Normal + Hard, both 100-floor rotations |
| `loopAllTower` | Master orchestrator for monthly ToA resets |
| `loopTOAHell` | 10 ToA Hell floors with difficulty handicaps |
| `getTowerTime` | Human-like clear-time calculator (also used for dungeons) |
| `getTowerTimeLegacy` | Legacy timing algorithm |

## Category 5 — Dimension Hole (8)

| Method | Purpose |
|--------|---------|
| `DoDHole` | Single Dimension Hole battle |
| `loop_D_HOLE` | Dimension Hole energy loop (drives `DHThread`) |
| `GetDimensionHoleQuestInfo` | Daily/weekly DHole quest objectives |
| `GetDimensionHoleRaidInfo` | DHole raid progress |
| `GetBestDHOLERank` | Best DHole record |
| `doAllDHoleQuests` | Complete + claim all DHole quests |
| `UpdateDimensionHoleQuest` | Submit quest progress |
| `RewardDimensionHoleQuest` | Claim quest rewards |

## Category 6 — Rift of Worlds & Raids (9)

| Method | Purpose |
|--------|---------|
| `DoRift` | Elemental rift-beast run |
| `loopRift` | Rift farming loop |
| `doAllRift` | Loop all 5 elemental rifts for craft materials |
| `GetBestClearRiftDungeon` | Best grades (SSS records) |
| `_create_rift_deck` | Auto-configures front/back-line positioning |
| `RIFT_CONFIG` | Elemental beast configuration map |
| `loopRaid` | Rift Raid loop R1–R5 (drives `RaidThread`) |
| `GetRiftOfWorldsRaidServerInfo` | Raid room coordinator connection |
| `RAID_CONFIG` | Configuration mapping for 3-player and solo raid setups |

## Category 7 — Guild Content (10)

| Method | Purpose |
|--------|---------|
| `GetGuildInfo` | Guild profile, roster, level |
| `GetGuildID` | Active guild ID |
| `loopGuildwar` | Guild War loop (drives `GThread`) |
| `loopGuildRival` | AI Guild Rival battles |
| `getGuildWarInfo` | Matchup state + opponent towers |
| `getGuildWarEnergy` | Guild War swords remaining |
| `getGuildRivalInfo` | Guild Rival battle status |
| `getGWDefense` | Inspect opponent defense teams |
| `DoMaze` | Tartarus' Labyrinth tile battle |
| `getMazeinfo` | Tartarus' Labyrinth exploration grid |

## Category 8 — Runes & Artifacts (40)

| Method | Purpose |
|--------|---------|
| `eval_rune` | Evaluate one rune against user criteria |
| `handle_rune` | Keep / sell / power-up decision for a new drop |
| `sellRune` | Server request: sell rune IDs for mana |
| `SELL` | Batch-sale orchestrator |
| `log_rune` | Write rune drops to local JSON log |
| `check_rune_count` | Remaining rune capacity (cap 1,000) |
| `rune_count` / `rune_max` | Current / max rune inventory |
| `rune_options` | Active rune-filter preferences |
| `rune_check` | Validate rune integrity & sub-rolls |
| `_rune_score` | Weighted math score (weights from `score.pyd`) |
| `_best_six_runes` | Optimal 6-rune loadout for a monster |
| `_get_rune_id` | Extract rune instance ID |
| `process_ancient_rune` | Ancient-rune evaluator (Dimension Hole) |
| `SmartUpgradeCheckRune` | Predict upgrade value before spending mana |
| `smartUpgradeCheck` | Auto +3/+6/+9/+12 power-ups |
| `upgradeUntil` | Power up until milestone or fail limit |
| `power_up_all_runes` | Mass-upgrade eligible runes |
| `checkMaxRoll` | Has the rune hit max roll thresholds |
| `handleRuneCraft` | Keep/sell grindstones & enchanted gems |
| `sellRuneCraft` | Sell grindstones/gems |
| `log_stones` | Log grindstone/gem drops |
| `isShitStone` | Heuristic filter for low-tier/flat grindstones |
| `handle_artifact` | Keep/sell decision for artifacts |
| `SellArtifacts` | Server request: sell artifacts |
| `log_artifact` | Log artifact drops |
| `check_artifact_count` | Remaining artifact capacity |
| `arti_count` / `arti_max` / `arti_options` | Artifact inventory state & preferences |
| `artifact_check` | Validate artifact sub-property rolls |
| `smartArtifactCheck` / `smartArtifactUpgradeCheck` | Artifact upgrade viability & thresholds |
| `upgradeArtifact` / `upgradeArtifactUntil` | Single / continuous artifact upgrades |
| `getArtifactValuableSub` | High-priority artifact substat list |
| `getValuableStats` | Master dictionary of desirable stat combos |
| `isTrashStats` | Heuristic filter for worthless combos |
| `craft_options` | Crafting-building automation config |
| `inventory_clean` | Full purge pass over runes + artifacts (drives `ICThread`) |

## Category 9 — Monsters & Decks (15)

| Method | Purpose |
|--------|---------|
| `eval_unit` | Combat effectiveness + rune quality of a monster |
| `best_equip` | Auto-assign optimal runes to a monster |
| `_sortUnits` | Sort by grade/stars/combat power |
| `fill_unit` | Fill empty deck slots with suitable monsters |
| `unmaxed_unit` | Find monsters below level cap |
| `updateUnitExp` | Track EXP after scenario battles |
| `ConvertItemToUnit` | Summon from inventory summoning pieces |
| `SetRepUnit` | Set profile representative monster |
| `GetRecentDecks` | Previously used deck configurations |
| `_get_or_create_deck` | Retrieve/provision a team preset |
| `_resolve_unit_deck_ids` | Instance IDs → unit template IDs |
| `log_team` | Log team composition & performance |
| `loopallunskill` | Find monsters with unmaxed skills |
| `get_unit_name` | Monster ID → display name |
| `unit_images` | Monster avatar asset URLs |

## Category 10 — Economy, Shops & Refills (10)

| Method | Purpose |
|--------|---------|
| `getShopList` | Magic Shop inventory |
| `buyShopItem` | Buy a shop slot |
| `checkShopItem` | Is an item high-value (mystical/legendary scrolls, LD pieces) |
| `checkAndBuyShop` | Scan shop → buy targets → crystal refresh |
| `getGuildShopList` | Guild Magic Shop inventory |
| `buyGuildShopItem` | Buy with guild points |
| `buyitem` | Generic purchase dispatcher |
| `BuyItemCart` | Bulk cart purchase |
| `BuyAncientCrystal` | Convert surplus nat-5★ to Ancient Crystals |
| `smart_refill` | Buy energy with crystals/social points when depleted |

## Category 11 — Quests, Events & Social (31)

| Method | Purpose |
|--------|---------|
| `getAllDailyQuest` | Standard daily quest list |
| `doAllDailyQuests` | Complete + claim all dailies (drives `QThread`) |
| `updateDailyQuest` | Submit daily progress |
| `collabo_getQuestList` / `collabo_dailyQuest` / `collabo_updateQuestList` / `collabo_rewardQuest` | Collab event missions (drives `CollabQuestsThread`) |
| `doEvent` / `doHiddenEvent` | Webview events, incl. unadvertised ones |
| `getEventInstanceID` / `GetEventTimeTable` | Event IDs & schedules |
| `CheckDailyReward` / `checkDailyReward` | Login calendar check-in status |
| `getDailyReward` / `getDailyRewardPoint` | Claim login rewards / activity points |
| `ReceiveDailyRewardSpecial` / `receiveDailyRewardInactive` / `receiveDailyRewardNewUser` / `receiveDailyRewardSpecialEvent` / `receiveDailyRewardSpecialPass` | Special/seasonal/returning-player/pass check-ins |
| `receivePlayPassReward` | Battle-pass level rewards |
| `GetMailList` / `ReceiveMail` / `claim_mail` | Inbox: list, collect one, batch-collect all |
| `GetFriendList` / `getFriendListWid` | Friends + their wizard IDs |
| `sendDailyGift` | Send friendship hearts |
| `VisitFriend` | Simulate island visits for social points |
| `farm_rep` / `farm_rep_error` / `farm_deter` | Borrow friend rep monsters for farming + error/fallback handling |

## Category 12 — Telemetry & Utilities (11)

| Method | Purpose |
|--------|---------|
| `getWizardInfo` | Full account state: mana, crystals, energy, wings, level |
| `GetConfigFromLog` | Recover deck/run preferences from past battle logs |
| `getChecker` | Internal packet sanity validator |
| `load_rules` / `save_rules` / `rules` | Deserialize / persist / access the active `RuleSet` (rules.json) |
| `get_all_coupons` | Fetch promo codes from `swq.jp` |
| `redeem_all_coupons` | Auto-redeem via `coupon.qpyou.cn` |
| `used_coupon` | Cache of redeemed codes |
| `bot` | Reference to the parent orchestrator |
| `_initial` | Internal state initializer |

---

## How the loops fit together

```
Worker thread (control.pyd)      SWAPI (summon.pyd)                 Server
──────────────────────────      ─────────────────────              ──────
DThread.run ──────────────────► loopDungeon
                                  ├─ DoDungeon ──────────────────► BattleDungeonStart
                                  │   (reads drops from start response)
                                  ├─ sleep(getTowerTime())        [simulated clear time]
                                  ├─ send("BattleDungeonResult") ► result
                                  ├─ handle_rune/handle_artifact
                                  │    └─ score.pyd + rules.pyd
                                  │         └─ sellRune/SellArtifacts ► SellRune/SellArtifact
                                  └─ smart_refill if energy low   ► BuyShopItem
```

The start response for every battle mode already contains the full drop table,
so the bot knows the outcome before "fighting" — the sleep only simulates
elapsed time. Clear times that are faster than plausibly possible are the main
server-side ban vector (see case analysis §9.3).
