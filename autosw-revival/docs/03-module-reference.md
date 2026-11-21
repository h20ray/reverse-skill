# AutoSW — Module Reference (classes, threads, methods)

> Part of the `autosw-revival/docs/` revival set. Per-module breakdown of every
> Cython `.pyd` and native binary: what each class does, the methods it
> exposes, and the worker-thread model. The 180-method `SWAPI` surface has its
> own document (`04-swapi-reference.md`); crypto primitives are detailed in
> `02-crypto-protocol.md`; the big picture is in `01-architecture.md`.
> Raw evidence: [`../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md`](../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md)
> (§2, §5, §6, §8).

All Python modules are Cython-compiled (`.pyd`, CPython 3.11 win-amd64) inside
the PyInstaller bundle. Method names below were recovered from module strings,
Cython symbol tables, and dynamic behavior.

---

## 1. `ui.pyd` — frontend host

| Symbol | Role |
|--------|------|
| `main()` | Entry point called by the PyInstaller bootloader. Starts the WebView2 window, tray icon, and the Python-side event loop. |
| `MyCustomApiBridge` | JS↔Python IPC bridge class exposed to the SPA. The frontend calls methods on it; the names map onto `IndexControl` / `MainControl` methods (see §2). |
| tray (via `pystray`) | System-tray icon with show/exit menu. |

Frontend assets: `work/autosw/sample/html/` — Vue/Vuetify SPA (`main.html`,
`index.html`, `js/chunk-vendors.js`, `js/main.js`), Material Design Icons
fonts. UI strings extracted to [`../../work/autosw/ui_strings.json`](../../work/autosw/ui_strings.json).

---

## 2. `control.pyd` — setup wizard, dashboard, task scheduler

Two bridge-facing controller classes plus one `threading.Thread` subclass per
task type.

### 2.1 `IndexControl` (setup stage — certs, proxy, login, updates)

| Method | Purpose |
|--------|---------|
| `_install_windows` | Installs `CN=swfarm CA` into `Cert:\LocalMachine\Root` via CryptoAPI |
| `check_cert` | Verifies whether `swfarm CA` is already trusted on the host |
| `cert_install` | Installs the root CA to Windows or a detected emulator |
| `cert_push` | Pushes the CA into an Android emulator filesystem via ADB |
| `su_check` | Verifies emulator root via `adb shell su` |
| `fake_fs` | `su -c "mount -t tmpfs tmpfs /system/etc/security/cacerts"` (bypasses read-only `/system`) |
| `start_proxy` | Starts the embedded mitmproxy engine |
| `change_proxy` | Switches manual proxy / transparent WinDivert / emulator proxy |
| `proxy_set` | Sets Windows system proxy or emulator `http_proxy 127.0.0.1:8080` |
| `proxy_unset` | Restores original proxy settings |
| `net_optimize` | Tests/applies Alibaba DoH `223.5.5.5` resolution |
| `steam_login` | Hooks the Steam PC client network path |
| `steam_cleanup` | Removes Steam proxy redirects on exit |
| `list_profiles` | Enumerates saved account configurations |
| `login` | License-key auth against `autosw.net` |
| `check_update` | Checks `autosw.net/update` for new versions |
| `show_log` / `clear_log` / `add_log` / `update_log` | UI console log buffer |
| `progress` / `progress_max` | UI progress bars |
| `cf_add_log` / `cf_log` / `cf_max` / `cf_val` | Solver/telemetry log widgets |
| `open_modal` / `close_modal` | WebView2 modal dialogs |
| `set_val` / `locale` / `message` / `tutorial` | UI state helpers |

### 2.2 `MainControl` (operational dashboard)

| Method | Purpose |
|--------|---------|
| `bot` | Launches the headless automation loop |
| `noatk_proxy` | Toggles the live MITM proxy with stat nerfing (`ProxyNOATKThread`) |
| `dungeon` / `arena` / `dhole` / `dq` / `gw` / `raid` / `rift` / `scenario` / `toa` / `toah` / `toahell` / `collab_quests` / `inv_clean` | One starter per task type — each spawns its worker thread (§2.3) |
| `create_task` / `start_task` / `stop_task` / `remove_task` | Task scheduler CRUD |
| `stop_all` / `remove_all` | Halt & reset everything |
| `task_status` / `task_conflict` | Thread state monitoring + conflict detection |
| `add_rule` / `update_rule_by_index` / `delete_rule_by_index` / `get_rules` | Rune/artifact keep-sell rule CRUD (feeds `rules.pyd`) |
| `activate` | Validates activation/license keys |
| `alipay` / `btc` | Payment link generation (commercial) |
| `get_aff` | Affiliate referral stats |
| `dungeon_list` | Populates UI dungeon dropdowns |
| `load_unit_images` | Monster avatar thumbnails (via `SWAPI.unit_images`) |
| `show_time` / `sub_time` | Remaining subscription time |
| `open_url` | External browser to tutorial/shop pages |
| `set_locale` / `locale` / `logout` / `append_log` / `clear_log` / `message` | UI management helpers |

### 2.3 Worker threads

Each enabled task runs as its own `threading.Thread` subclass. Tasks declare
`task_conflict` sets so two energy-consuming tasks never run simultaneously.

| Thread | Automates |
|--------|-----------|
| `DThread` | Cairos dungeons (Giants/Dragon/Necro/Steel/Punisher/Spirit Realm); stage progression, energy monitoring |
| `AThread` | Arena invitations, NPC rivals, picks low-power targets from `GetArenaWizardList` |
| `DHThread` | Dimension Hole: 2A EXP farming, ancient runes |
| `TThread` / `THellThread` | ToA normal/hard and ToA Hell (floors 1–100) |
| `RaidThread` / `RThread` | Rift Raid (multiplayer & solo R1–R5) and elemental rift beasts |
| `GThread` | Guild War, Guild Rivals, Tartarus' Labyrinth |
| `SThread` | Scenario stages / fodder leveling |
| `CollabQuestsThread` / `QThread` | Collab event missions, daily quests |
| `ICThread` | Inventory-clean: batch evaluate + bulk sell runes/artifacts |
| `ProxyNOATKThread` | Live MITM proxy with nerfing active (manual proxy mode) |
| `TransparentProxyThread` | WinDivert kernel-capture loop (transparent mode) |

ADB helpers in this module also drive emulator setup: cert push, proxy set,
root checks (port 5037).

---

## 3. `summon.pyd` — headless game client

`summon.pyd` contains **two classes** (string-table evidence; earlier drafts
conflated them):

- **`SWCore`** (~128 methods) — the game client proper: most of the RPC
  wrappers (`Get*`, `Buy*`, `Battle*` command dispatch, `send`), login/relogin
  (`HubUserLogin`, `manual_relogin`), deck building (`_get_or_create_deck`,
  `best_equip`), drop handling (`handle_rune`, `handle_artifact`), evaluation
  glue into `score.pyd`/`rules.pyd` (`eval_rune`, `load_rules`, `save_rules`,
  `rune_check`, `getChecker`, `smartUpgradeCheck`), shops, quests, mail.
- **`SWAPI`** (~28 methods) — the orchestration class the worker threads call
  into: all `loop*` entry points (`loopDungeon`, `loopArena`, …), `bot`,
  `inventory_clean`, `smart_refill`, `farm_deter`, `power_up_all_runes`,
  mail/coupon claims. It sits on top of `SWCore`, which itself builds on the
  session plumbing in `common.pyd`.

Full method inventory: `04-swapi-reference.md`. Highlights:

- `DoDungeon` / `loopDungeon` — start battle → read drops from the start
  response → sleep a simulated clear time (`getTowerTime`) → submit result →
  evaluate/sell drops → refill energy when low.
- `loopArena`, `loopAllTower`, `loopRaid`, `loop_D_HOLE`, `loopGuildwar`,
  `loopScenario`, `inventory_clean` — the loop entry points each worker thread
  calls.
- Drop handling delegates to `score.pyd` + `rules.pyd`; selling goes through
  `sellRune` / `SellArtifacts`.

---

## 4. `common.pyd` — shared plumbing

| Symbol | Role |
|--------|------|
| `SWAPI` (base class) | Session state, `send()` dispatcher (encrypt → POST `gateway_c2.php` → decrypt), endpoint URL/host/server-id properties (`url`, `server_host`, `server_id`, `appid`) |
| `SWUser` | License/account model (autosw.net auth state) |
| `query_doh` | DNS-over-HTTPS resolver against `https://223.5.5.5/dns-query` to pin game-host IPs |
| `assign_process_to_job_object` | Puts the process in a Windows Job Object (die-with-parent semantics) |
| global config | Reads/writes JSON config & rules files next to the executable |
| `pub_key` | Hardcoded RSA-2048 public key for session exchange (§02-crypto-protocol) |

---

## 5. `cipher.pyd` — crypto primitives

`encrypt` / `decrypt` (AES-128-CBC + PKCS#7 + Base64), zlib helpers, RSA token
routines. Full spec, keys, and pipelines: `02-crypto-protocol.md`.

---

## 6. `proxy.pyd` — live interception (`SWAddon`)

A mitmproxy addon class. Two halves:

### 6.1 Intercepted commands (battle-start responses)

| Command | Mode | Monster list key |
|---------|------|------------------|
| `BattleDungeonStart` | Cairos dungeons | `dungeon_unit_list` |
| `BattleScenarioStart` | Scenario | `dungeon_unit_list` |
| `BattleRiftDungeonStart` | Elemental rifts | `dungeon_unit_list` |
| `BattleRaidStart` | Rift raid R1–R5 | `raid_unit_list` |
| `BattleTrialTowerStart_v2` | ToA / ToAH / Hell | `trial_tower_unit_list` |
| `BattleDimensionHoleDungeonStart` | Dimension Hole | `dungeon_unit_list` |
| `BattleGuildSiegeStart_v2` | Guild Siege | `guildsiege_opp_unit_list` |
| `BattleArenaStart` | Arena / World Arena | `opp_unit_list` |
| `GetGuildSiegeBattleInfo` | Siege defense inspection | `guildsiege_opp_unit_list` |

### 6.2 `apply_nerfs` / `nerf_unit` — the stat-rewrite algorithm

Reconstructed logic (verified against module behavior):

```python
def nerf_unit(unit_info, mode="pve", power_proxy_level=0):
    if mode in ("pve", "raid"):
        unit_info["atk"] = 1                      # hard floor
        unit_info["spd"] = unit_info.get("spd", 100) // 4   # -75%
        unit_info["resist"] = 1
    if mode == "raid":
        unit_info["accuracy"] = 0
        unit_info["critical_rate"] = 1
        unit_info["critical_damage"] = 1
        unit_info["crit_damage_reduction"] = 0
    for skill in unit_info.get("skills", []):
        skill[1] = 1                              # skills back to level 1
    for rune in unit_info.get("runes", []):       # NOATKRunesProcess
        for sub in rune.get("sec_eff", []):
            if sub[0] == 8:   sub[1] = 1          # SPD substat → 1
            elif sub[0] == 4: sub[1] = 1          # ATK% substat → 1
    if mode in ("siege", "arena"):                # scaled PVP nerf
        scale = (10 - power_proxy_level) / 10.0
        unit_info["def"]            = max(5,  int(unit_info.get("def", 100) * scale))
        unit_info["critical_rate"]  = max(5,  int(unit_info.get("critical_rate", 15) * scale))
        unit_info["critical_damage"]= max(10, int(unit_info.get("critical_damage", 50) * scale))
```

Flow: decrypt response (via `cipher.pyd`) → if command is in the table above,
walk the monster list and `nerf_unit` each enemy → re-encrypt → forward to the
client. Trust is established by the `swfarm CA` install (see `IndexControl`).

> This subsystem is documented for understanding the sample only; the revival
> does not re-implement it (see the project README scope note).

---

## 7. `score.pyd` — rune/artifact math

| Symbol | Role |
|--------|------|
| `calc_artifact_score` | Scores artifact sub-properties vs. monster archetype |
| `calc_skill_completion` | Whether a monster's skills are fully leveled |
| `collect_battle_rune_set_context` | Detects set bonuses (Violent/Swift/Will…) and compound efficiency |
| `SPD_WEIGHT` / `CR_WEIGHT` / `CD_WEIGHT` / `ACC_WEIGHT` / `RES_WEIGHT` | Linear stat weights: `RuneScore = Σ(substat × weight)`; SPD is the dominant weight |

## 8. `rules.pyd` — keep/sell rule engine

Live-probed API (Python 3.11, `work/autosw/trace/rules_check*.py`):

| Symbol | Role (confirmed) |
|--------|------|
| `RuleSet` | Factory base class: `RuleSet("rune"/"artifact", **fields)` dispatches via `__new__` through a type registry (`RuleSet._registry = {'rune': RuneRuleSet, 'artifact': ArtifactRuleSet}`) |
| `RuneRuleSet.__init__` | `(enabled: bool, main_stats: List[Any], name: str, rune_sets: List[Any], rules: List[List[Any]], slots: List[Any], upgrade_level: Union[str,int], rune_classes: List[Any], type: str = 'rune')` — exactly the UI payload from `05-automation-engine.md` §5 |
| `ArtifactRuleSet.__init__` | `(enabled, name, rules, artifact_types=None, attributes=None, unit_styles=None, main_stats=None, artifact_classes=None, upgrade_level=0, type='artifact')` |
| `Rule` | `(key: Union[str,int], op: str, value: Any)` with `.check()` / `.to_config_list()` |
| `op_map` | `{==, !=, >, >=, <, <=}` → `operator` functions (case-sensitive string keys) |
| `check(obj)` | Returns `(keep: bool, flattened_obj: dict)`; rules evaluate against a **flat attribute map** (e.g. `{"SPD": 11, ...}`); the object is augmented with `sec_eff_map` during checking (built by the caller from the raw rune — see `SWCore.getValuableStats`) |
| `check_ruleset(obj, rules: Iterable[RuleSet], upgrade_func=None)` | Batch evaluation over all enabled rulesets |
| `load_ruleset(filename)` / `save_ruleset(ruleset, filename)` | Per-ruleset JSON persistence; `to_dict()` is the serialization (round-trip verified) |

Note: constructing through the factory double-calls `__init__` when done
naively from Python (`RuneRuleSet(cfg_dict)` raises `TypeError`); the compiled
app constructs these internally, so this quirk doesn't affect it — but a port
should implement the straightforward `__init__` semantics, not the factory
double-dispatch.

## 9. Native binaries

| Binary | Role |
|--------|------|
| `main.exe` | PyInstaller bootloader (Python 3.11 runtime, launches `ui.main()`) |
| `windows-redirector.exe` | Go binary bridging WinDivert kernel capture → local mitmproxy `127.0.0.1:8080`; CLI filter e.g. `--mode local:SummonersWar.exe` |
| `WinDivert64.sys` (+32-bit variant under `pydivert/`) | Kernel driver capturing outbound TCP/443 from the game process |
| `update.exe` + `7za.exe` | Auto-update: download zip → 7za unpack → restart `main.exe` |
| `adb.exe` + AdbWin* | Emulator control (cert push, proxy, root checks) |
| `ca.crt` / `ca.key` / `cert.key` | The MITM root CA **with its plaintext private key** — critical exposure (finding F-AUTOSW-01) |

## 10. Revival notes

- The clean seams for a rebuild are already visible: crypto (done —
  `autoswkit.crypto`), the `SWAPI` protocol layer, the `score`/`rules`
  evaluation logic, and the thread-per-task scheduler are separable pieces;
  the WebView2 bridge can be replaced by any modern UI stack.
- Python-specific glue that does **not** survive as-is: `pystray`/`pywebview`
  IPC, `certutil`/CryptoAPI cert injection, WinDivert + mitmproxy wiring, and
  ADB scripting. On a modern stack, expect to re-implement these against
  native APIs — or drop them (the MITM path is out of scope for the revival).
- Keep the task-conflict model (energy-consuming tasks are mutually exclusive)
  — it is a behavioral invariant, not an implementation detail.
