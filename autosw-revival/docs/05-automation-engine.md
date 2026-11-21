# AutoSW — Automation Engine Deep Dive (profiles, scheduler, loops, timing)

This doc explains **how the automation actually works, end to end**: how a user
profile is built and persisted, how tasks become threads, how each battle loop
is driven, and where every wait/loop-count comes from. It is the reference for
any future port (macOS / Rust / Bun) and for understanding `score`/`rules`
integration in context.

Evidence sources (all from case `work/autosw/`):

- `sample/html/js/main.js` — the Vue SPA running inside the WebView2 window.
  This is the *clearest* artifact in the whole build: it contains the full
  frontend→backend contract (every task's parameter payload, defaults, and the
  ruleset schema) in readable form. A beautified copy is kept at
  `work/autosw/main.beautified.js`.
- `sample/control.pyd`, `sample/summon.pyd` — Cython-compiled backend. String
  dumps used for this doc are in `work/autosw/strings/*.strings.txt`.
- Prior case reports: `report/AUTOSW_DETAILED_ANALYSIS.md` §6,
  `docs/03-module-reference.md` §2–3.

---

## 1. Process topology (who talks to whom)

```
┌────────────────────────────────────────────────────────────────┐
│ main.exe  (single Python process, WebView2 host = ui.pyd)      │
│                                                                │
│  Vue SPA (html/js/main.js)                                     │
│    │  window.pywebview.api.MainControl.<method>(json args)     │
│    ▼                                                           │
│  control.pyd                                                   │
│    ├─ IndexControl  — login, profiles, certs, proxy, updates   │
│    ├─ MainControl   — task CRUD + thread factory               │
│    └─ worker threads (DThread, AThread, ...)                   │
│    │  calls loop entry points, one thread per enabled task     │
│    ▼                                                           │
│  summon.pyd (SWCore) — headless game client                    │
│    ├─ SWAPI.send(): encrypt → POST gateway_c2.php → decrypt    │
│    └─ loopDungeon / loopArena / loopRaid / ... battle loops    │
│         │ drop evaluation                                      │
│         ▼                                                      │
│       score.pyd + rules.pyd  (keep/sell decision, pure math)   │
└────────────────────────────────────────────────────────────────┘
```

The UI never touches the network. The UI only creates/stops tasks and renders
polls. Everything game-related happens inside `summon.pyd` on worker threads
owned by `control.pyd`.

---

## 2. The profile system

### 2.1 What a "profile" is

- Profiles live in `profiles/*.json` next to the executable (string evidence:
  `profiles/`, `.json`, `profile_data`, `profile_name`, `list_profiles`,
  `ProfileThread` in `control.pyd`).
- One JSON file = one game account = a named set of *tasks* the user has
  configured. The sample install's `profiles/` directory is empty — files are
  created at runtime when a user saves task configuration.
- `IndexControl.list_profiles` enumerates them for the login dropdown; the SPA
  keeps `form: { name, profiles }` and a `ProfileThread` handles the save/load
  work off the UI thread (`ProfileThread.run`, `ProfileThread._log_error`).

### 2.2 What is stored per task record

Reconstructed from the frontend payloads (§4 below) plus backend field names
(`task_id`, `task_params`, `task_status`, `task_conflict` in `control.pyd`):

```json
{
  "task_id":      "<int, backend-assigned handle used by start/stop/status>",
  "task_name":    "\"Dungeon\" (button label from the UI)",
  "task_params":  { "...exact kwargs the UI passed, see §4..." },
  "task_status":  "\"Running\" | \"Stopped\"",
  "task_conflict":[ "dungeon", "raid", ... ],
  "pvp_required": true
}
```

- `task_params` is **the UI payload verbatim** — the frontend is the schema
  source of truth. That is why §4 matters: whatever JSON shape the SPA sends is
  what `summon.pyd` reads back.
- `pvp_required` is set by the frontend for tasks that need the paid PVP
  subscription (arena/gw inside `bot(...)`, `noatk`). `MainControl.start_task`
  refuses to start such a task unless PVP mode is enabled ("PVP mode required").

### 2.3 Where rules live

Keep/sell rulesets are **not** part of the profile — `common.pyd` reads/writes
JSON config & rules files next to the executable. The rules file is a list of
rulesets (schema in §5), toggled per-ruleset (`enabled` flag) and applied by
`rules.pyd` / `score.pyd` at drop time.

---

## 3. Scheduler: from button click to running loop

### 3.1 Task creation

1. User clicks a task button (e.g. "Dungeon"). If `sub_time > 0` (license
   gate), the SPA opens a settings dialog and stashes a closure as
   `this.action`.
2. On "Settings saved" → `perform_action()` invokes the closure, which calls
   `window.pywebview.api.MainControl.<task>(...params...)`.
3. Backend returns a response; the SPA checks it with `this.response(e)` and
   calls `add_task(label, id, pvp_required)` which appends a local table row
   `{ task, start: now, end: "", status: "Running", id, pvp_required }`.
4. Backend side: `MainControl.create_task` is the thread factory. The string
   `Type[FarmThread]` in `control.pyd` shows the design: every task thread
   derives from a common `FarmThread` base, and `create_task` instantiates the
   right subclass, stores `{task_id, task_params, task_status, task_conflict}`,
   and starts the thread. Its `run()` immediately calls the matching
   `SWCore.loop*` entry point.

### 3.2 Conflict model

`MainControl.task_conflict` + per-thread `task_conflict` sets: tasks declare
which other tasks they conflict with (all energy-consuming PVE tasks conflict
with each other; PVP tasks conflict with each other). Starting a conflicting
task returns "Task conflict" / the UI shows "Task conflict" toast, and the task
is *not* started. This is how "one energy drain at a time" is enforced —
there is no queue, only mutual exclusion.

### 3.3 Task management surface (SPA polling)

- The SPA polls `MainControl.task_status(task.id)` **every 3 s** (`setInterval
  3e3`) for every row whose status is `"Running"`, and updates the row's
  status/end time. Status transitions are entirely UI-poll-driven.
- `start_task(id)` / `stop_task(id)` / `remove_task(id)` / `remove_all` /
  `stop_all` ("Stop Selected" = stop + remove in the UI code).
- A `TimeThread` also runs continuously (`MainControl.show_time`) keeping the
  dashboard clock / subscription countdown fresh.

### 3.4 Full worker-thread roster (`control.pyd`)

| Thread class | Loop entry (`summon.SWCore`) | Params come from |
|---|---|---|
| `DThread` | `loopDungeon` | `dungeon(dungeon_id, hoh, times, rune_keep, rune_opts)` |
| `DHThread` | `loop_D_HOLE` | `dhole(dhole_id, times, rune_opts, rune_keep, gem_keep)` |
| `TThread` / `THellhread` | `loopAllTower` / `loopTOAHell` | `toa()` / `toah()` / `toahell()` — no params |
| `RaidThread` / `RThread` | `loopRaid` / `loopRift` | `raid(times, keep)` / `rift(rift_id, times, keep)` |
| `GThread` | `loopGuildwar` / `loopGuildRival` / `loopSiege` | `gw()` |
| `AThread` | `loopArena` | `arena()` |
| `SThread` | `loopScenario` | `scenario(times)` |
| `HOHThread` | `loopHOH` | dungeon entry flagged `hoh: true` (capped at 10 runs) |
| `QThread` / `CollabQuestsThread` | `doAllDailyQuests` / collab trio | `dq()` / `collab_quests()` |
| `ICThread` | `inventory_clean` | `inv_clean({rune, artifact, smart})` |
| `BThread` | composite bot loop | `bot({...}, times, keep)` — see §4 |
| `CFThread` | CloudFlare IP ping/select | net optimize (not a game task) |
| `ProxyNOATKThread` / `TransparentProxyThread` | `proxy.pyd` machinery | `noatk_proxy(level)` (out of revival scope) |
| `UpdateThread`, `TimeThread`, `InfoThread`, `ProfileThread`, `purchase_monitor` | — | infrastructure |

(`loopInstance`/`loopEventInstance` back event/collab instances; `loopallunskill`
is the 1★-fodder skill-up helper.)

---

## 4. The frontend→backend task contract (exact payloads)

Every task button in the SPA ends in one of these calls. **These payloads are
the profile JSON's `task_params`** — reproduce them byte-for-byte in a port.

Common pre-processing (in the SPA, `get_farm_params()`):

- `farm_times` → `parseInt`; if `NaN` or `<= 0` → **`99999`** (i.e. "farm
  forever"). The value is capped at **10** only when the selected dungeon is a
  Hall of Heroes (`hoh: true`).
- Rune-keep object (`dungeon`'s 5th arg, `dhole`'s 4th, etc.):

  ```json
  {
    "all":  true,             // false if any class filter chosen
    "keep": [5, 4, 3],        // rune classes to keep: 5=legend, 4=hero, 3=rare
                              //   "l"→[5]  "h"→[5,4]  "r"→[5,4,3]
    "6":    [5],              // separate 6★-rune filter: "6l"→[5], "6h"→[5,4], "6r"→[5,4,3]
    "smart": <int>,           // smart level slider, 0 = off
    "speed_required": true,   // optional: only keep runes with SPD substat
    "speed_upgrade_only": true// optional: only keep runes that rolled SPD
  }
  ```
- Gem/stone keep object (raid/rift/dhole): `{ all: false, keep: [5, 4],
  smart: <int>, special: [<gem class ids from "special_gem_select">] }`.

| UI call (`MainControl.*`) | Payload |
|---|---|
| `dungeon(dungeon_id, hoh, times, rune_keep, rune_opts)` | `dungeon_id` from `dungeon_list()`; `rune_opts` is the rune-keep object above (it is also passed where artifacts are evaluated) |
| `dhole(dhole_id, times, rune_opts, rune_keep, gem_keep)` | `dhole_id` ∈ 2A unit list (`2a_inugami` … 17 entries); gem_keep = `special` object |
| `raid(times, gem_keep)` | solo raid loop; keep object as above |
| `rift(rift_id, times, rune_opts)` | `rift_id` ∈ elemental rift beasts |
| `scenario(times)` | no other params — the loop picks the fodder stage itself |
| `toa()` / `toah()` / `toahell()` | **no params** — climb from current floor to 100, then stop |
| `arena()` | no params; SPA warns if account level < 50 (`confirm_arena`), needs `pvp` |
| `gw()` | no params; needs `pvp` (marks task `pvp_required`) |
| `dq()` / `collab_quests()` | no params |
| `inv_clean({ rune: bool, artifact: bool, smart: int })` | inventory cleaner; rule mode (`smart_level_inv` vs rules) chosen in UI |
| `bot({ dungeon, dhole, daily, arena, gw, shop }, times, keep)` | composite idle-bot: `shop` = `{ buy_rune, buy_stone, buy_scroll, buy_unknow, buy_2star, buy_4star }` from the shop-refresh checkboxes; `daily/arena/gw` from the options list ("all" enables daily + arena + gw, gated by `pvp`); whole task becomes `pvp_required` if arena or gw is on |
| `noatk_proxy(level)` | level 0–10, 10 strongest; MITM stat-nerf proxy (excluded from revival) |
| `shopref` | shop refresh loop — uses the same `shop` checkboxes |

`dungeon_list()` is itself a backend call — the UI does **not** hardcode dungeon
IDs; the backend supplies `{value, text, hoh}` rows. A port should keep that
shape.

---

## 5. Ruleset schema (keep/sell rule engine input)

From the SPA's ruleset modal (`handleEditOrAddRulesetOk`), the payload saved via
`add_rule` / `update_rule_by_index` is:

```json
{
  "name": "My ruleset",
  "enabled": true,
  "type": "rune",                       // or "artifact" (artifact modal, no type override)
  "upgrade_level": 9,                   // minimum +level before judging
  "rune_sets":    [13, 3],              // Violent=13, Swift=3, ... ALL=-1
  "rune_classes": [5, 4],               // legend/hero/...
  "main_stats":   ["SPD", ...],
  "slots":        [2, 4, 6],
  "rules": [ ["<stat>", "<op>", <value>], ... ]   // condition1/op/value rows
}
```

Rune-set enum (from the UI source): Energy 1, Guard 2, Swift 3, Blade 4, Rage 5,
Focus 6, Endure 7, Fatal 8, Despair 10, Vampire 11, Violent 13, Nemesis 14,
Will 15, Shield 16, Revenge 17, Destroy 18, Fight 19, Determination 20,
Enhance 21, Accuracy 22, Tolerance 23, Seal 24, ALL −1.

Artifact rulesets swap `rune_sets`/`slots` for `{ artifact_type, classes,
attributes, unit_styles, rules: [[substat, op, value]] }`.

The **smart level** is a global quality threshold (slider 0–N); when
`enableSlider` mode is on, `score.pyd`'s weighted score must clear it; the
rulesets (`enableRuleCreation` mode) are evaluated by `rules.pyd` in listed
order. Both modes can coexist; inventory-cleaner has its own `inv_smart_level`.
(Score math itself: `docs/03-module-reference.md` §7–8.)

---

## 6. The core battle loop (how one task actually runs)

Using `loopDungeon` as the template (all `loop*` functions follow it):

1. **Guards.** Check energy/wings ("Current energy", "Cannot refresh energy!");
   refill paths: `buyShopItem` with crystals ("Buying energy by crystals...") or
   social points ("Buying energy by social points..."). If a required resource
   is absent the loop stops with the matching log line ("No guildwar energy!",
   "Cannot get RAID server! Energy not enough.").
2. **Team selection.** `_get_or_create_deck` / `best_equip` / `_best_six_runes`
   build the deck from the account's units; runes are assigned by
   `_rune_score` / `_sortUnits`. Team changes invalidate the timing cache —
   "Best dungeon team conflict! Reset time to 240s..." (see §7).
3. **Start battle.** `BattleDungeonStart` (or the domain's Start RPC). **The
   drop table arrives in the start response** — the bot knows the rewards
   before "fighting".
4. **Simulate clear time.** Compute a plausible duration
   (`getTowerTime` / `getTowerTimeLegacy`; state vars `play_time`, `play_speed`,
   `newsec`) and `sleep()` it — the log line is "Waiting for {} seconds...".
   This is the anti-detection delay: the result RPC must arrive no faster than
   a human run (see the ban-risk note in the case report §9.4).
5. **Submit result.** `BattleDungeonResult_V2` (domain-appropriate Result RPC:
   `BattleScenarioResult`, `BattleTrialTowerResult_v3`, `BattleRiftDungeonResult`,
   `BattleGuildWarResult`, ...). Server returns rewards.
6. **Evaluate drops.** `handle_rune` / `handle_artifact` →
   `eval_rune`/`_rune_score` + rulesets → keep (log "Got a ...", "Got an ancient
   ...") or sell via `sellRune` / `SellArtifacts`. Raid gems/grinds go through
   `isShitStone`/`isTrashStats` with the `special` keep list.
7. **Housekeeping.** Daily-quest hooks (`doAllDailyQuests`, shop refresh via
   `checkAndBuyShop` + `market_refresh_ts`), mail/claims, then decrement the
   run counter (`loop_times` / `looptimes`) and continue until 0 (or 99999) —
   "Farming level", "Climbing level" progress logs.

ToA variants climb floors 1→100 sequentially (`loopAllTower` /
`loopAllTOA`), which is why they take no parameters. Arena refreshes its
target list and picks low-power opponents from `GetArenaWizardList`.

---

## 7. All wait/retry constants found (string evidence)

| Situation | Behavior / log line | Value |
|---|---|---|
| Per-battle wait (ToA) | "Waiting for {} seconds..." | `getTowerTime` tables (§7) |
| Per-battle wait (Cairos) | "Waiting for {} seconds..." | `max(own best record, 20) + U(0,6)` s (§7) |
| Team/deck changed mid-farm | "Best dungeon team conflict! Reset time to 240s..." | 240 s cooldown |
| Relogin forced | "Relogin detected, sleep for 10 mins...." | 600 s |
| Arena out of invitations | "Arena tailing, wait for 30 mins...." | 1800 s |
| Manual-login cap | `manual_login_times` + "Too many relogin attempt!" | bounded retries |
| Session expired | "Session expired! Please relogin!" → `manual_relogin` | re-auth loop |
| Run count | `farm_times` default | 99999 (HOH capped at 10) |
| UI status poll | SPA `setInterval` | 3 s |

**Timing formulas — CONFIRMED by live probing** (importing the `.pyd` modules
under Python 3.11 and calling them directly; see `work/autosw/trace/`,
script `tower*.py`, full table in `tower_times.json`):

- `getTowerTime(level, difficulty)` — ToA clear-time simulation, in seconds:
  - **Normal (diff 1):** floor 1 = 15.4 s, floor 2 = 12.8 s, floor 3–100 =
    exactly `6.4 × floor` (12.8 … 640 s).
  - **Hard (diff 2):** exactly `10.4 × floor` for all floors 1–100
    (10.4 … 1040 s).
  - **Hell (diff 3):** non-deterministic — a per-floor base with a large
    uniform jitter: floor 1 ≈ 1513–2104 s (mean 1824), floor 50 ≈ 1903–2463 s
    (mean 2190). Bases grow slowly with floor (~7 s/floor); jitter ≈ ±300 s.
- `getTowerTimeLegacy(level)` — **broken code**: the compiled body computes
  `int * self` and always raises `TypeError`. It is dead code; callers use
  `getTowerTime`.

**Dungeon (Cairos, e.g. Giant) timing — CONFIRMED by live probe**
(`work/autosw/trace/dungeon_loop2.py`, `timing_experiment*.py`): the
per-battle wait is **derived from the account's own best clear record**, not
computed from unit stats and not a constant table:

1. Before each battle `DoDungeon` calls `GetDungeonList`, validates the stage
   (`stage_list` → `cleared` → `cost` vs energy), then calls
   `GetDungeonBestCommunityRanking(group_id)` and reads **`my_ranking`** —
   the account's own best-clear record for that dungeon group — including
   `clear_time` (ms) and `my_unit_deck_list`.
2. The simulated wait is `max(best_record_seconds, 20) + uniform(0, 6)`
   seconds. Verified over sampled runs: record 32 s → sleeps 32.4–37.8 s;
   record 128 s → 128.2–133.2 s; record 0 → floored at 20.0–25.9 s. The
   enemy waves (`dungeon_unit_list`[:-1] vs [-1] boss wave) and turn count
   do **not** affect the wait.
3. If the account has **no record** for the stage, the bot tracks it in
   `no_record_stages` and falls back to a conservative default — the
   240 s reset in "Best dungeon team conflict! Reset time to 240s...".

So the "RNG time" the user sees is: **own best record (floored at 20 s) plus
a uniform 0–6 s jitter**, fetched live from the server, not stored in the
profile JSON. The profile itself carries best records only for Rift Raid
(`raid_best_clear_info_list`).

---

## 8. Response handling & error model

- All traffic goes through `SWAPI.send()`: encrypt → POST `gateway_c2.php` →
  decrypt (spec: `02-crypto-protocol.md`).
- Backend error strings surface in the battle log: "Network error[Com2us]!",
  "Network error[Server]!", "No Internet!", "Timeout connect to server",
  "Cannot refresh arena list!". Non-fatal ones are logged and the loop
  continues; fatal ones stop the thread and the UI row shows the status via the
  3 s poll.
- `MainControl.append_log` / `IndexControl.add_log` feed both the UI battle log
  and `logs/General.log` (format `%(asctime)s [%(levelname)s] %(message)s`).
- Re-login is a distinct path (`manual_relogin`) with its own retry budget;
  proxies can require "Refresh fail! Relogin via proxy required".

---

## 9. Porting notes (macOS / Rust / Bun, later)

Port cleanly:

- The **task contract in §4** — it is just JSON in/out; keep field names.
- The **loop template in §6** — each loop is a straightforward async function;
  worker threads map to `asyncio` tasks or `tokio`/Bun tasks naturally.
- **score/rules** — pure logic, no OS calls (already the P2 target).
- **profiles** — directory of JSON files; trivially portable. Keep
  `profiles/` + config/rules JSON next to the binary for behavioral parity.

Needs rethinking on macOS:

- WebView2/pywebview IPC → use WKWebView (Tauri/tao or pywebview's macOS
  backend); the `window.pywebview.api.<Class>.<method>` surface should be
  re-exposed as-is to reuse the SPA bundle (`html/js/main.js` is portable
  unchanged if the bridge object exists).
- Cert/proxy/WinDivert/ADB glue is Windows-specific; the revival excludes the
  MITM path anyway. "Power proxy" must not be ported.
- The Windows Job Object (die-with-parent) has no macOS equivalent — drop it or
  emulate with process-group signals.

---

## 10. Open items for the next evidence pass

1. ~~Disassemble `getTowerTime`~~ **DONE** — live-probed; formulas in §7.
   Remaining timing unknowns: per-dungeon (non-ToA) clear-time computation and
   `play_speed` units.
2. **Capture a real `profiles/*.json`** (run the app and save a profile) to
   confirm the persisted record layout matches §2.2 — the current shape is
   inferred from the frontend payloads.
3. **Capture `rules.json`** written by the app to confirm the on-disk ruleset
   serialization (`rules.pyd` exposes `load_ruleset`/`save_ruleset` and
   `RuleSet.to_dict`; the `to_dict` output is likely the disk format — verified
   round-trippable shape in `work/autosw/trace/rules_check*.py`).
4. Confirm whether `bot()`'s composite loop runs sub-loops sequentially or in
   nested interleaving (string order suggests sequential with daily tasks
   checked between battles).
5. ~~Rune field names for `sec_eff_map`~~ **SETTLED** — a real `HubUserLogin`
   capture (user-provided profile) shows the wire format: runes carry
   `pri_eff: [type, value]` and `sec_eff: [[type, value, ...], ...]` with
   `EFF_TYPE` ids, level = `upgrade_curr`, `class` = stars, `rank` = quality,
   equipped unit = `occupied_id`. `autoswkit.score.flatten_rune` now handles
   this shape natively (`autoswkit.account.flatten_rune_game`).
