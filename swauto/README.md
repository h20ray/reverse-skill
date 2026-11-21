# swauto

Cross-platform (Windows / macOS / Linux) clean-room rebuild of the AutoSW
automation engine. Based entirely on documented behavior from the
reverse-engineering case (`../work/autosw/`) — see `docs/07-pipeline-flow.md`
for the full pipeline reference. **No original code is used.**

## Design principles

1. **asyncio core** — worker threads replaced by async tasks with an
   `asyncio.Event` stop signal (cooperative stop: the in-flight battle always
   completes before the loop exits).
2. **Platform abstraction** — everything OS-specific lives in
   `swauto/platform/`; the core is pure Python and runs anywhere.
3. **Injectable transport** — `net/transport.py` defines the seam; offline
   testing uses scripted transports, live HTTP is opt-in.
4. **Passive capture only — never tampering.** The original AutoSW's "Power
   proxy" half (mitmproxy `SWAddon` rewriting *battle* responses to nerf enemy
   stats — `apply_nerfs`, WinDivert/kernel capture, `TransparentProxyThread`) is
   **excluded by design**. What *is* built (B8, `swauto/proxy/`) is the
   **passive login-capture** half AutoSW also needs to obtain a session: a local
   transparent-TLS MITM of the operator's **own** game client login, which
   decrypts only the `HubUserLogin`/`GetWizardInfo` envelope and saves the
   session profile. It never rewrites a byte. A per-install root CA is
   generated (never AutoSW's shared `swfarm` CA — F-AUTOSW-01), and the capture
   sees only the operator's own account on `qpyou.cn` gateway hosts.

## Layout

| Path | Contents |
|------|----------|
| `src/swauto/platform/` | OS abstraction: data dirs, log dirs, UI backend selection |
| `src/swauto/net/` | envelope crypto, Transport protocol, HTTP + scripted transports, Session (`send()`) |
| `src/swauto/config/` | account snapshot loader, task profiles, rulesets |
| `src/swauto/proxy/` | own-account login capture (B8): per-install CA, envelope decode + classify, mitmproxy addon/runner, profile save — optional `[proxy]` extra |
| `src/swauto/game/` | constants, timing tables, rune scoring, keep/sell rules, battle units, loops |
| `src/swauto/scheduler/` | async TaskManager: conflict sets, verbatim task params, cooperative stop |
| `src/swauto/ui/` | headless CLI (first); WebView backend later |
| `docs/` | reference docs copied from the case analysis (01–07) |
| `tests/` | pytest + pytest-asyncio |

## Quickstart

```bash
cd swauto
pip install -e ".[dev]"
pytest

swauto run --profile examples/profile.json --task dungeon   # offline demo
```

## Capturing a session (own account)

A live `HubUserLogin` from scratch is refused (`ret_code 1006`): a fresh
session is minted only by the **real game client** logging in (B7 — AutoSW
MITMs that login and saves the response as `profiles/<wizard_id>.json`, then
re-serves its `session_key`/`session_key_node`). This repo reproduces the
*capture* leg (never the tamper leg):

```bash
pip install -e ".[proxy]"          # optional heavy mitmproxy extra
swauto proxy capture               # local transparent-TLS proxy on 127.0.0.1:8080
```

Point the operator's own game client (Steam PC client or emulator) at
`127.0.0.1:8080` and trust the freshly generated per-install root CA (printed
at startup; saved under `profiles/`). Log into one's own account once — the
addon unwraps the `HubUserLogin` envelope, saves the snapshot as
`profiles/<wizard_id>.json`, and the bot can `establish_from_profile(...)` from
it. The raw capture is a live secret: it lives only under the gitignored
`profiles/`, and `AccountSnapshot.sanitize()` is the only shareable form.

## Status

- ✅ crypto, account/config loaders, timing tables, rune scoring (exact
  recovered weights), keep/sell rules, energy-refill policy, dungeon battle
  unit, async scheduler, headless CLI
- ✅ deck building (`game/equip.py` — documented `best_equip` contract,
    verified against the original on a real account), craft grading
    (`game/crafts.py`), upgrade-cycle wire shape (`UpgradeRune_v2`)
- ✅ rune keep/sell semantics recovered exactly and ported to
  `game/evaluate.py`: `is_trash_stat` (flats 1/3/5), `get_valuable_stats`
  (class==6, Fatal/Guard de-emphasis, smart ignored), `smart_upgrade_check`
  (True/False/None + per-stat grown-value floors) — each verified 7500+/
  8300/ against the compiled oracle; inventory cleaner
  (`power_up_all_runes` / `inventory_clean` / `loop_inventory_clean`)
  implements the recovered `UpgradeRune_v2` upgrade-then-judge cycle
- ✅ artifact evaluation recovered exactly (`game/artifacts.py`: the
  `getArtifactValuableSub` keep/sell source as never/presence/value-floor
  membership — verified 777/777 real + 5000/5000 synthetic against the
  compiled oracle) and an artifact pass in the inventory cleaner
  (`power_up_all_artifacts` — structure-only +3-milestone
  `UpgradeArtifact_v2` cycle; the original's `smartArtifactUpgradeCheck` is
  live-session-gated, so the upgrade thresholds are NOT claimed exact)
- ✅ lock-aware inventory selling (Phase B1 corrective — the original is
  lock-blind): `profile.py` surfaces `rune_lock_list`/artifact `locked` as
  `locked_rune_ids()`/`locked_artifact_ids()`; every sell/upgrade path skips
  locked items. Rune sells batch as `SellRune {rune_id_list}` (the probed
  oracle wire shape). Count guard mirrors the probed caps
  `rune_max = artifact_max = 1500` (`over_rune_cap`/`over_artifact_cap`)
- ✅ scenario unit (Phase B2 — 2nd complete reference): `do_scenario` uses the
  captured `BattleScenarioStart` payload; `loop_scenario` reproduces the
  recovered `GetFriendList` → energy → battle chain and the friend-assist
  `helper_list` wire (rep unit drawn as `{unit_id, wizard_id}`)
- ✅ dungeon payload corrected + dimension-hole unit (Phase A4): driving the
  oracle's `loopDungeon` across the whole Cairos family proved the earlier
  `do_dungeon` payload was **wrong** in three fields — `stage`→**`stage_id`**,
  bare-int `unit_id_list`→**`[{"unit_id"}, ...]`**, `equip:[]`→**`equip:null`**
  (now fixed). New `do_dhole`/`loop_dhole` send the recovered-exact
  `BattleDimensionHoleDungeonStart` (16-unit `dungeon_units` deck with leader at
  slot 0). Evidence: `work/autosw/trace/_A4_content_recovery_outcome.md`
- ✅ login flow (Phase B3): `net/login.py` — the recovered-exact 8-field
  `HubUserLogin` request (`channel_uid, command, infocsv, loginextend_refcount,
  proto_ver, session_key, ts_val, wizard_id`), `fetch_version`,
  response-parser → `SessionState`, `apply_session` session wiring,
  `LoginClient`, `manual_relogin`, `check_login_block`. Verified by offline
  replay of the captured 7280513 response. The exact skey/cuid assignment was
  reconciled offline against the oracle (field-role probe): a signed `send()`
  reads ONLY `skey`/`cuid` — `account_info` is never consulted, so
  `account_info.channel_uid` is a red herring and the wire `wizard_id` is the
  wizard int. Evidence: `work/autosw/trace/_relogin_fieldrole_outcome.md`.
  Residual live-gated leg is the response-field→attr assignment *statement*
  (orchestrating caller not offline-reachable) — marked in code + A1 outcome
- ✅ profile → live Session (phase slice): `Session.send()` now emits the
  oracle-exact 8-field **signed envelope** once established, and
  `establish_from_profile(snapshot)` wires a raw HubUserLogin capture's session
  contract into a ready-to-send Session (`skey`/`cuid`/`wizard_id`/`server_id`,
  resolved gateway `server_host` via `transport.gateway_url`). It also **seeds
  the resource mirror** (energy/crystals/mana/arena_energy/social_points) from
  the capture's `wizard_info` via the same `_apply_wizard` translation `send()`
  uses live, so a session is live-ready immediately (no zero-report gap before
  a first refresh). Live-ready bot = `Loops(transport).establish_from_profile(snap)
  .from_snapshot(snap)` (locks + rune/artifact counts). Signing/seed is
  conditional on establishment, so bare offline Sessions are unchanged. Wiring
  verified offline (reconciliation probe — field-role outcome above). Note:
  there is **no `GetInventory` command** on the wire — inventory arrives bundled
  in the HubUserLogin capture, which this seeding reads directly
- ✅ live HTTP + version fetch (Phase B6): `net/transport.py` gained
  `GatewayTransport` (raw POST reproducing the captured gateway header set —
  User-Agent, `Content-Type: application/octet-stream`, `SmonTmVal`,
  `SmonChecker` placeholder, `timeout: 3`), `gateway_version_url()`, and
  `net/login.py` gained the recovered-exact **4-field** `build_version_request`
  (`{game_index, proto_ver, channel_uid, sec_ver}` — a *distinct* request
  family from the 8-field login envelope, recovered verbatim from the oracle),
  a live `LiveVersionFetcher`, and `version_topics` (the real `version_data` is
  a **list of per-topic rows** — ban_appid/cdnres/infocsv/intro/protocol/text —
  recovered **live**, 2026-09-07). `swauto live-login` performs the real
  version fetch + HubUserLogin and saves a fresh session to a gitignored
  profile. Evidence: `work/autosw/trace/_B6_live_login_outcome.md`.
  **Live-run result:** version_info_c2 fetch SUCCEEDED end-to-end; HubUserLogin
  is refused with `ret_code 1006` (not authenticated) on every variant because
  the RSA-4096 **session-key exchange** that precedes HubUserLogin (docs/07
  §1.3, report §3.3) is a live-only step no offline capture reconstructs (A1
  §5). The 8-field body + headers are request-faithful but do NOT authenticate
  alone — the login leg stays live-gated at that exchange
- ✅ Magic/Guild shop watcher (Phase B5): `game/shop.py` — the recovered-exact
  list/buy wire for both shops (they are the **"black markets"**:
  `GetBlackMarketList {cash_used:0}` / `BuyBlackMarketItem {item_master_type,
  item_no, item_master_id, amount, island anchor}` for the Magic shop;
  `GetGuildBlackMarketList {manual_update:0, guild_id}` /
  `BuyGuildBlackMarketItem {guild_id, item_no, refresh_ts}` for the Guild
  shop) and the recovered `checkShopItem` type→flag high-value predicate
  (item_master_type 9→`buy_scroll`, 27→`buy_stone`, 1/12→`buy_2star`/
  `buy_4star`; unavailable rows never buy). `check_and_buy_shop`/guild analogue
  scan + buy; the auto-refresh cadence is live-gated and not invented.
  Evidence: `work/autosw/trace/_B5_shop_recovery_outcome.md`
- ⏳ remaining content units (rift/raid/arena + tower floor field lists, HOH /
  secret/event, guildwar) — start payloads are **live-boundary**: each was
  given a real convergence attempt and its exact guard recorded in
  `work/autosw/trace/_A4_content_recovery_outcome.md` (§3–§6), not silently
  replaced by inferred skeletons. Complete references now: dungeon, scenario,
  dimension-hole; ToA tower wire already implemented (`do_tower`)
- 🚫 MITM / cert / driver plumbing — intentionally absent
