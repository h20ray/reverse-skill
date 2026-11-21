"""Battle units — one battle each (clean-room port of the recovered Do*
flow, docs/07 §3). The dungeon and dimension-hole units use recovered-exact
start payloads (A4 — see work/autosw/trace/_A4_content_recovery_outcome.md);
scenario is a second complete reference. Content whose battle start is a
live boundary (rift/tower-floor-fields/hoh/guildwar) is marked in docs/07
§3.8, not stubbed silently.
"""

from __future__ import annotations

import logging

from ..net.session import Session
from . import constants as C
from .score import flatten_rune, rune_score
from .rules import check_any, RuleSet
from .evaluate import get_valuable_stats, smart_upgrade_check
from .monsters import get_monster_name
from .shop import ShopMixin
from .timing import dungeon_time, tower_time

log = logging.getLogger("swauto.game")


class BattleClient(ShopMixin, Session):
    """Session + one-battle units + drop handling."""

    def __init__(self, *args, smart_level: int = 0, keep_selling: bool = True,
                 rune_rules: list[RuleSet] | None = None,
                 locked_rune_ids: set[int] | None = None,
                 locked_artifact_ids: set[int] | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.smart_level = smart_level
        self.keep_selling = keep_selling
        self.rune_rules = rune_rules or []
        # player-pinned ids the cleaner must never sell (Phase B1 corrective:
        # surfaced from the server lock fields, which the original ignores).
        self.locked_rune_ids = locked_rune_ids or set()
        self.locked_artifact_ids = locked_artifact_ids or set()
        # current inventory counts (fed by the operator or refresh); the
        # count guard mirrors the probed oracle caps (1500/1500).
        self.rune_count = 0
        self.rune_max = C.RUNE_CAP
        self.artifact_count = 0
        self.artifact_max = C.ARTIFACT_CAP
        # guild id for the Guild-shop RPCs (set by the operator from the
        # account's `guild` section; the shop mixin reads it defensively).
        self.gid: int = 0

    def from_snapshot(self, snap) -> "BattleClient":
        """Feed lock + count state from an :class:`AccountSnapshot` (or any
        object exposing ``locked_rune_ids()``/``locked_artifact_ids()`` and
        ``runes``/``artifacts``).

        A live-ready bot is the composition of the two snapshot methods
        (each returns ``self``)::

            bot = Loops(transport)
            bot.establish_from_profile(snap)   # identity/signing/host + resource
                                               # mirror (Session layer)
            bot.from_snapshot(snap)            # locks + rune/artifact counts
                                               # (BattleClient layer)

        The mirror (energy/crystals/…) lives on the base Session and is seeded
        by ``establish_from_profile`` from the capture's ``wizard_info``; this
        method seeds only the BattleClient-level inventory counts and locks.
        A live refresh (any response carrying ``wizard_info``) can overwrite
        the mirror later."""
        self.locked_rune_ids = set(snap.locked_rune_ids())
        self.locked_artifact_ids = set(snap.locked_artifact_ids())
        # live snapshot inventory size is the best available count; a refresh
        # can overwrite it later.
        self.rune_count = len(getattr(snap, "runes", []) or [])
        self.artifact_count = len(getattr(snap, "artifacts", []) or [])
        return self

    # -- lock/cap awareness (Phase B1 corrective — docs/07 §3.9) -------------
    def _rune_locked(self, rune: dict) -> bool:
        return rune.get("rune_id") in self.locked_rune_ids

    def _artifact_locked(self, artifact: dict) -> bool:
        return artifact.get("rid") in self.locked_artifact_ids

    def over_rune_cap(self) -> bool:
        """Mirror ``check_rune_count``: True strictly over the cap (count > max)."""
        return self.rune_count > self.rune_max

    def over_artifact_cap(self) -> bool:
        return self.artifact_count > self.artifact_max

    # -- battle units --------------------------------------------------------
    async def do_dungeon(self, dungeon_id: int, stage: int, deck: list[int],
                         group_id: int = 1) -> dict:
        """One Cairos clear — recovered-exact ``BattleDungeonStart`` payload.

        Oracle capture (work/autosw/trace/_A4_content_recovery_outcome.md §1,
        drive: ``loopDungeon`` across the whole Cairos family) proves the wire
        shape differs from the earlier skeleton in three fields that are fixed
        here:

        - the stage field is **``stage_id``** (not ``stage``);
        - ``unit_id_list`` is ``[{"unit_id": int}, ...]`` — one object per
          entering unit, NOT a list of bare ints;
        - ``equip`` is ``null`` (not ``[]``).

        The full chain is ``GetDungeonList -> GetDungeonBestCommunityRanking
        {group_id:1} -> GetWizardInfo -> BattleDungeonStart``, and the start
        payload carries ``dungeon_id/stage_id`` plus empty helper arrays and the
        root flags. ``helper_list``/``mentor_helper_list``/``npc_friend_helper_list``
        are sent as ``[]`` and ``is_rooting/cash_used/retry/auto_repeat`` as 0.
        """
        record = await self._dungeon_record(group_id)
        start = self.send("BattleDungeonStart", dungeon_id=dungeon_id,
                          stage_id=stage,
                          unit_id_list=[{"unit_id": u} for u in deck],
                          equip=None,
                          helper_list=[], mentor_helper_list=[],
                          npc_friend_helper_list=[], is_rooting=0,
                          cash_used=0, retry=0, auto_repeat=0)
        drops = start.get("drop_list", [])
        wait = start.get("clear_time") or dungeon_time(record, rng=self.rng)
        log.info("Waiting for %.1f seconds...", wait)
        await self.sleep(wait)
        result = self.send("BattleDungeonResult_V2", dungeon_id=dungeon_id,
                           stage=stage, win=1, drop_list=drops)
        await self.handle_drops(drops)
        return result

    def get_dungeon_list(self) -> list[dict]:
        """Fetch and parse available dungeons from GetDungeonList.

        Returns structured list for UI dropdowns and task scheduling:
        [
            {
                "id": dungeon_id,
                "name": str,
                "group_id": int,
                "is_hoh": bool,
                "cleared_stage": int,
                "total_stages": int,
                "stages": [{"stage_id": int, "cleared": bool}, ...],
                "monster_name": str | None,
            },
            ...
        ]
        """
        resp = self.send("GetDungeonList")
        raw_list = resp.get("dungeon_list", [])
        result = []
        for d in raw_list:
            did = d.get("dungeon_id", 0)
            gid = d.get("group_id", 0)
            stages = d.get("stage_list", [])

            # Detect HoH: group_id == 10, or explicit 'hoh' key, or 10 stages with unit_master_id
            is_hoh = bool(d.get("hoh") or gid == 10 or (len(stages) == C.HOH_STAGES and (d.get("unit_master_id") or "hoh" in str(d).lower())))

            monster_master_id = d.get("unit_master_id") or d.get("monster_id")
            monster_name = get_monster_name(monster_master_id) if monster_master_id else None

            if is_hoh:
                name = f"Hall of Heroes: {monster_name}" if monster_name else f"Hall of Heroes ({did})"
            else:
                name = C.DUNGEON_EN.get(did, f"Dungeon {did}")

            cleared_stages = [s.get("stage_id", i + 1) for i, s in enumerate(stages) if s.get("cleared")]
            max_cleared = max(cleared_stages) if cleared_stages else 0

            stage_entries = []
            if stages:
                for i, s in enumerate(stages):
                    stage_entries.append({
                        "stage_id": s.get("stage_id", i + 1),
                        "cleared": bool(s.get("cleared")),
                    })
            else:
                total = C.HOH_STAGES if is_hoh else 1
                stage_entries = [{"stage_id": i + 1, "cleared": False} for i in range(total)]

            result.append({
                "id": did,
                "name": name,
                "group_id": gid,
                "is_hoh": is_hoh,
                "cleared_stage": max_cleared,
                "total_stages": len(stage_entries),
                "stages": stage_entries,
                "monster_name": monster_name,
            })
        return result

    async def do_hoh_stage(self, dungeon_id: int, stage: int, deck: list[int]) -> dict:
        """One Hall of Heroes stage clear (Floor 1..10).

        Uses progressive floor scaling delay (B1 ~35s, B10 ~135s+jitter) and
        submits BattleDungeonStart + BattleDungeonResult_V2 with win=1.
        """
        base_time = 25.0 + (stage * 10.0)
        jitter = self.rng.uniform(-5.0, 10.0) if getattr(self, "rng", None) else 0.0
        wait = max(15.0, base_time + jitter)

        start = self.send("BattleDungeonStart", dungeon_id=dungeon_id,
                          stage_id=stage,
                          unit_id_list=[{"unit_id": u} for u in deck],
                          equip=None,
                          helper_list=[], mentor_helper_list=[],
                          npc_friend_helper_list=[], is_rooting=0,
                          cash_used=0, retry=0, auto_repeat=0)
        drops = start.get("drop_list", [])
        actual_wait = start.get("clear_time") or wait
        log.info("HoH Floor %d (Dungeon %d): waiting %.1f s...", stage, dungeon_id, actual_wait)
        await self.sleep(actual_wait)
        result = self.send("BattleDungeonResult_V2", dungeon_id=dungeon_id,
                           stage=stage, win=1, drop_list=drops)
        await self.handle_drops(drops)
        log.info("HoH Floor %d cleared! Got %d pieces.", stage, C.HOH_PIECES_PER_STAGE)
        return result

    async def do_dhole(self, dungeon_id: int, deck: list[int],
                       difficulty: int = 5, dungeon_level: int = 1,
                       dungeon_stage: int = 1) -> dict:
        """Enter a Dimension-Hole dungeon — recovered-exact payload.

        Oracle drive ``loop_D_HOLE`` (work/autosw/trace/_A4_content_recovery_outcome.md §2)
        yields ``BattleDimensionHoleDungeonStart``. The 16-unit deck is sent as
        ``dungeon_units`` — ``[{"unit_id", "leader", "position"}]`` — with the
        leader occupying slot 0 (``leader: 1``, no ``position``) and the rest
        at ``position`` 1..15. ``difficulty`` defaults to 5 (the captured value)
        and ``dungeon_level/stage`` default to 1.

        The post-start result parse (``BattleDimensionHoleDungeonResult_v2``)
        mutates a live-session response structure and is therefore a documented
        live boundary — the start payload above is the recovered, authoritative
        wire.
        """
        dungeon_units = [{"unit_id": u, "leader": 1 if i == 0 else 0,
                          **({"position": i} if i > 0 else {})}
                         for i, u in enumerate(deck)]
        start = self.send("BattleDimensionHoleDungeonStart", dungeon_id=dungeon_id,
                          difficulty=difficulty, practice_mode=0, retry=0,
                          is_rooting=0, auto_repeat=0, dungeon_units=dungeon_units,
                          dungeon_level=dungeon_level, dungeon_stage=dungeon_stage,
                          helper_list=[], npc_friend_helper_list=[])
        drops = start.get("drop_list", [])
        log.info("Waiting for the dimension-hole dungeon to clear...")
        await self.sleep(C.SCENARIO_WAIT_DEFAULT)
        result = self.send("BattleDimensionHoleDungeonResult_v2",
                           dungeon_id=dungeon_id, win=1, drop_list=drops)
        await self.handle_drops(drops)
        return result

    async def do_tower(self, level: int, difficulty: int, deck: list[int]) -> dict:
        """ToA floor — timing from the exact tables."""
        start = self.send("BattleTrialTowerStart_v3", level=level,
                          difficulty=difficulty, unit_id_list=deck)
        drops = start.get("drop_list", [])
        wait = tower_time(level, difficulty, self.rng)
        log.info("Waiting for %.1f seconds...", wait)
        await self.sleep(wait)
        result = self.send("BattleTrialTowerResult_v3", level=level,
                           difficulty=difficulty, win=1, drop_list=drops)
        await self.handle_drops(drops)
        return result

    # -- scenario (2nd complete reference — wire recovered offline, see
    #    work/autosw/trace/_A2_unit_outcome.md) ------------------------------
    # live-gated (see docs/07 §3.8 + A4 §3-§6): rift/raid/tower-field-list/
    # hoh/guildwar/arena. dhole is recovered above (A4 §2).
    def _pick_friend_assist(self, resp: dict) -> list[dict]:
        """Choose a friend assist for a scenario battle from a GetFriendList
        response, returning the ``helper_list`` entry (or [] if none usable).

        Oracle-recovered semantics (B2 re-probe): ``loopScenario`` scans the
        friend list for a friend that can assist (a rep unit is set) and draws
        that rep into the battle as a helper. The wire helper entry is exactly
        ``{"unit_id": <rep_unit_id>, "wizard_id": <friend wizard_id>}``.
        Degrades to [] when the response has no usable friend, matching the
        friendless ``helper_list: []`` capture.
        """
        for friend in resp.get("friend_list", []) or []:
            rep = friend.get("rep_unit_id")
            if rep and friend.get("wizard_id"):
                return [{"unit_id": rep, "wizard_id": friend["wizard_id"]}]
        return []

    async def _scenario_friends(self) -> list[dict]:
        """Scenario loop's first fetch (documented ``GetFriendList`` — the
        original calls this once before the battle loop to pick an assist)."""
        return self._pick_friend_assist(self.send("GetFriendList"))

    async def do_scenario(self, region: int, stage: int, difficulty: int, deck: list[int],
                          helper_list: list[dict] | None = None) -> dict:
        """One scenario stage clear (the captured request contract).

        Wire shape is the recovered-exact ``BattleScenarioStart`` payload (A2
        probe, friendless capture + B2 friend capture both match):

        - ``helper_list`` carries a chosen friend's rep unit as
          ``[{"unit_id", "wizard_id"}]`` (see ``_pick_friend_assist``), else [];
        - the loop prefetches friends once via ``_scenario_friends``, then
          syncs energy (``GetWizardInfo`` via the loop) and clears the stage.
        """
        helper_list = helper_list if helper_list is not None else []
        start = self.send("BattleScenarioStart", region_id=region, stage_no=stage,
                          difficulty=difficulty, unit_id_list=deck,
                          helper_list=helper_list, mentor_helper_list=[],
                          npc_friend_helper_list=[], retry=0, auto_repeat=0)
        drops = start.get("drop_list", [])
        # prefer the server clear_time; fall back to the recovered DoScenario
        # default wait (the oracle's per-stage timing is not offline-exact).
        wait = (start.get("clear_time") or 0) / 1000 if start.get("clear_time") \
            else C.SCENARIO_WAIT_DEFAULT
        log.info("Scenario %d-%d (diff %d): waiting %.1f s", region, stage, difficulty, wait)
        await self.sleep(wait)
        # Result wire: name confirmed on the oracle; field list NOT
        # offline-recoverable (DoScenario errors post-start before sending a
        # result), so this mirrors the documented Do* convention
        # (region/win/drop_list), consistent with the dungeon result shape.
        result = self.send("BattleScenarioResult", region_id=region,
                           win=1, drop_list=drops)
        await self.handle_drops(drops)
        return result

    # -- record fetch ---------------------------------------------------------
    async def _dungeon_record(self, group_id: int) -> float | None:
        """Own best clear record (seconds) from the community-ranking call."""
        resp = self.send("GetDungeonBestCommunityRanking", group_id=group_id)
        ms = (resp.get("my_ranking") or {}).get("clear_time")
        return ms / 1000 if ms else None

    # -- drop handling ----------------------------------------------------------
    async def handle_drops(self, drops: list[dict]) -> None:
        for drop in drops:
            if drop.get("type") == "rune":
                await self.handle_rune(drop)
            elif drop.get("type") == "artifact":
                await self.handle_artifact(drop)

    async def handle_rune(self, rune: dict) -> bool:
        flat = flatten_rune(rune)
        if self.smart_level and self.rune_rules:
            kept = rune_score(flat) >= self.smart_level or check_any(flat, self.rune_rules)
        elif self.smart_level:
            kept = rune_score(flat) >= self.smart_level
        elif self.rune_rules:
            kept = check_any(flat, self.rune_rules)
        else:
            kept = True
        log.info("Got a rune (set=%s class=%s): %s", rune.get("set_id"),
                 rune.get("class"), "keep" if kept else "sell")
        if kept:
            return True
        if self._rune_locked(rune):
            log.info("rune %s is player-locked — not selling", rune.get("rune_id"))
            return True  # a locked rune is not sold; treat as kept for the caller
        if self.keep_selling:
            self._sell_runes([rune["rune_id"]])
        return False

    async def handle_artifact(self, artifact: dict) -> bool:
        """Keep when at least one substat is valuable (the recovered
        ``valuable_subs`` membership rule — docs/07 §3.6), or when an
        explicit ruleset accepts the flattened map."""
        from .artifacts import flatten_artifact, valuable_subs
        flat = flatten_artifact(artifact)
        if self.rune_rules:
            kept = check_any(flat, self.rune_rules)
        else:
            kept = bool(valuable_subs(artifact))
        log.info("Got an artifact (%s %s): %s — valuable=%s",
                 flat.get("unit_style"), flat.get("attribute"),
                 "keep" if kept else "sell", sorted(valuable_subs(artifact)))
        if kept:
            return True
        if self._artifact_locked(artifact):
            log.info("artifact %s is player-locked — not selling", artifact.get("rid"))
            return True  # locked artifact treated as kept
        if self.keep_selling:
            self.send("SellArtifacts", artifact_ids=[artifact["rid"]])
        return False

    def _sell_runes(self, ids: list[int]) -> None:
        """Batch-sell runes (wire shape from the oracle: ``SellRune
        {rune_id_list: [...]}`` — probed live, 2026-09-07). Filters out any id
        that became locked since the caller filtered."""
        ids = [i for i in ids if i not in self.locked_rune_ids]
        if ids:
            self.send("SellRune", rune_id_list=ids)

    # -- artifact upgrade (structure-only — docs/07 §3.6/§3.9) ---------------
    async def power_up_all_artifacts(self, artifacts: list[dict],
                                     options: dict | None = None) -> int:
        """Power up unequipped artifacts and keep/sell by valuable substats.

        Structure-only port (live-session-gated): the original's
        ``smartArtifactUpgradeCheck`` reads server/login state that cannot be
        reproduced offline (Phase A probe — it returns ``False`` for every
        dict input, so its exact thresholds are NOT recovered). The cycle
        below mirrors the documented artifact model and the recovered-exact
        keep/sell source ``valuable_subs``:

        - an artifact already at the upgrade cap (``level >= limit``) is never
          upgraded and is kept or sold outright by ``valuable_subs``: at the
          cap nothing can change, so a never-valid/floored-below-floor set is
          final (sold) and a valuable set is kept;
        - a sub-max artifact is never trash by its current substats alone —
          artifact properties are *revealed* only at +3/+6/+9/+12, so each
          cycle powers to the next +3 milestone (capped at ``limit``, default
          15) via ``UpgradeArtifact_v2``, then re-judges the fresh state with
          ``valuable_subs``: a valuable substat appeared or crossed its floor
          -> keep and stop; otherwise keep powering until the cap;
        - reaching the cap with no valuable substat -> sell
          (``SellArtifacts``).

        Returns the number of artifacts upgraded (powered at least one level).
        ``options`` mirrors the rune options (``smart``/``keep``/``max``); the
        compiled artifact threshold is live-gated, so ``smart`` currently only
        selects the valuable-source and the +3 cadence /
        ``UpgradeArtifact_v2`` payload are best-effort.
        """
        from .artifacts import valuable_subs
        opts = options or {}
        limit = int(opts.get("max") or 15)  # artifact max level
        upgraded = 0
        for artifact in artifacts:
            if self._artifact_locked(artifact):
                log.info("artifact %s is player-locked — skipping", artifact.get("rid"))
                continue
            current = int(artifact.get("level", 0) or 0)
            if current >= limit:
                # no upgrade possible: keep if it already carries a valuable
                # substat, else sell (nothing can change at the cap).
                if not valuable_subs(artifact) and self.keep_selling:
                    log.info("artifact %s at cap with no valuable substat — sell",
                             artifact["rid"])
                    self.send("SellArtifacts", artifact_ids=[artifact["rid"]])
                continue
            touched = False
            fresh = artifact
            # artifacts reveal a new substat only at +3 milestones; each cycle
            # powers to the next one so a reveal can be judged.
            while current < limit:
                target = min(((current // 3) + 1) * 3, limit)
                resp = self.send("UpgradeArtifact_v2", artifact_id=artifact["rid"],
                                 upgrade_target=target, cash_used=0)
                fresh = (resp or {}).get("artifact", artifact)
                next_level = int(fresh.get("level", current) or current)
                touched = touched or next_level > current
                if valuable_subs(fresh):
                    log.info("artifact %s has a valuable substat — keep",
                             artifact["rid"])
                    break
                current = next_level
            # reached the cap with no valuable reveal -> sell
            if (current >= limit and not valuable_subs(fresh) and self.keep_selling
                    and not self._artifact_locked(fresh)):
                log.info("artifact %s reached max with no valuable substat — sell",
                         artifact["rid"])
                self.send("SellArtifacts", artifact_ids=[artifact["rid"]])
            if touched:
                upgraded += 1
        return upgraded

    # -- inventory cleaner (recovered upgrade cycle — docs/07 §3.9) ----------
    async def power_up_all_runes(self, runes: list[dict],
                                 options: dict | None = None) -> int:
        """Power up unequipped runes one level per ``UpgradeRune_v2`` and judge.

        Recovered wire shape + orchestration (live-probed against the original):

        - only unequipped, sub-max runes are eligible;
        - each cycle sends ``UpgradeRune_v2 {rune_id, cash_used:0,
          loginextend_refcount:0, upgrade_target:upgrade_limit}`` (+1 level);
        - after each upgrade the rune is re-judged with ``smart_upgrade_check``:
            - a valuable stat rolled high enough (``True``) -> keep, stop powering;
            - nothing valuable grew (``None``) -> keep powering (next cycle);
            - a trash/low roll (``False``) -> sell, stop powering;
        - stops at the upgrade limit (``upgrade_target``).

        Returns the number of runes upgraded. ``options`` is accepted for
        call-compatibility (``smart``/``keep``/``special``/``max``), matching
        the original's ``runes_options``.
        """
        opts = options or {}
        limit = int(opts.get("max") or 15)  # rune upgrade_target (max level)
        smart = int(opts.get("smart", self.smart_level))
        upgraded = 0
        for rune in runes:
            if self._rune_locked(rune):
                log.info("rune %s is player-locked — skipping", rune["rune_id"])
                continue
            current = int(rune.get("upgrade_curr", 0) or 0)
            if current >= (int(rune.get("upgrade_limit") or limit)):
                continue
            touched = False
            while current < limit:
                resp = self.send("UpgradeRune_v2", rune_id=rune["rune_id"],
                                 cash_used=0, loginextend_refcount=0,
                                 upgrade_target=limit)
                fresh = (resp or {}).get("rune", rune)
                next_level = int(fresh.get("upgrade_curr", current) or current)
                touched = touched or next_level > current
                # judge after the roll: valuable -> keep; trash -> sell; else continue
                vstats = get_valuable_stats(rune, smart)
                verdict = smart_upgrade_check(rune, fresh, vstats)
                if verdict is True:
                    log.info("rune %s rolled valuable (%.1f score) — keep",
                             rune["rune_id"], rune_score(flatten_rune(fresh)))
                    break
                if verdict is False:
                    log.info("rune %s rolled trash — sell", rune["rune_id"])
                    if self.keep_selling:
                        self._sell_runes([rune["rune_id"]])
                    break
                current = next_level
            if touched:
                upgraded += 1
        return upgraded

    async def inventory_clean(self, runes: list[dict],
                              artifacts: list[dict] | None = None,
                              options: dict | None = None) -> int:
        """Batch inventory cleaner: evaluate unequipped runes and artifacts,
        power the promising ones, sell the trash (docs/07 §3.9).

        Rune pass over the unequipped pool, mirroring the recovered policy,
        followed by an artifact pass when ``artifacts`` is supplied:

        1. Sell runes that are trash by construction — non-legend (never any
           valuable) or legend with no hard substat present (all flats or
           RES/ACC utility). These are never worth an upgrade roll.
        2. Power up the rest via :meth:`power_up_all_runes` (the recovered
           upgrade-then-judge cycle keeps the runes that roll valuable and
           sells the ones that roll trash).
        3. Artifacts (if any): hand every unequipped artifact to
           :meth:`power_up_all_artifacts`. Artifacts reveal a new substat only
           at +3 milestones, so a sub-max artifact is never trash by
           construction — one whose current substats are all never-valuable
           can still reveal a valuable sub while leveling. The cycle keeps
           artifacts that reveal a valuable substat and sells artifacts that
           reach the upgrade cap with none (nothing can change at the cap).

        Returns the number of runes sold in the rune trash pass (backward-
        compatible with the original rune-only return; artifact sales are
        reported only via logs).

        Phase B1 corrective: player-locked runes (``locked_rune_ids``) and
        artifacts (``locked_artifact_ids``) are never sold, upgraded, or
        counted as sold — they drop out of the pass entirely.
        """
        opts = options or {}
        smart = int(opts.get("smart", self.smart_level))
        keep_candidates, trash = [], []
        for rune in runes:
            if self._rune_locked(rune):
                log.info("rune %s is player-locked — skipping", rune["rune_id"])
                continue
            # a valuable map is empty exactly when the rune can never roll
            # valuable (wrong class, or only flats/utility substats)
            (keep_candidates if get_valuable_stats(rune, smart) else trash).append(rune)
        sold = 0
        if self.keep_selling and trash:
            self._sell_runes([rune["rune_id"] for rune in trash])
            sold = len(trash)
        await self.power_up_all_runes(keep_candidates, options)

        if artifacts is not None:
            await self.power_up_all_artifacts(artifacts, options)
        return sold

    # -- energy policy (exact thresholds — docs/07 §3.5) ------------------------
    def smart_refill(self, required: int = 8) -> bool:
        if self.energy >= required:
            return True
        if self.social_points > C.SOCIAL_REFILL_MIN:
            log.info("Buying energy by social points...")
            self.send("BuyShopItem", item_id=C.SHOP_HEART_ENERGY)
            self.social_points -= 500
            self.energy += 10
            return True
        if self.crystals >= C.CRYSTAL_REFILL_MIN:
            log.info("Buying energy by crystals...")
            self.send("BuyShopItem", item_id=C.SHOP_ENERGY_290)
            self.crystals -= 300
            self.energy += 10
            return True
        log.info("Cannot refresh energy!")
        return False
