"""SWCore — headless game client (Python port of ``summon.SWCore``).

Mirrors the original structure (docs/06-worker-threads.md):

- ``send()`` is the single network touchpoint: one command per call,
  encrypted envelope handled by the transport. The wire format is the
  one implemented in :mod:`autoswkit.crypto` (AES-128-CBC + zlib).
- The transport is **injectable** so the bot can be exercised offline
  against a scripted server (tests) — no code path touches the network
  unless a real transport is installed.
- Resources (energy, crystals, arena/wizard energy) are mirrored from
  server responses, as in the original.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, Protocol

from . import constants as C

log = logging.getLogger("autoswkit")

# Command names as they appear on the wire (subset used by the MVP)
BATTLE_DUNGEON_START = "BattleDungeonStart_v2"
BATTLE_DUNGEON_RESULT = "BattleDungeonResult_V2"
BATTLE_TOWER_START = "BattleTrialTowerStart_v3"
BATTLE_TOWER_RESULT = "BattleTrialTowerResult_v3"
BATTLE_SCENARIO_START = "BattleScenarioStart"
BATTLE_SCENARIO_RESULT = "BattleScenarioResult"
BATTLE_RAID_START = "BattleRiftOfWorldsRaidStart"
BATTLE_RAID_RESULT = "BattleRiftOfWorldsRaidResult"
BATTLE_RIFT_START = "BattleRiftDungeonStart"
BATTLE_RIFT_RESULT = "BattleRiftDungeonResult"
BATTLE_DHOLE_START = "BattleDimensionHoleDungeonStart"
BATTLE_DHOLE_RESULT = "BattleDimensionHoleDungeonResult_v2"
GET_WIZARD_INFO = "GetWizardInfo"
GET_DUNGEON_LIST = "GetDungeonList"
GET_DUNGEON_BEST_COMMUNITY_RANKING = "GetDungeonBestCommunityRanking"
BUY_SHOP_ITEM = "BuyShopItem"
SELL_RUNE = "SellRune"
SELL_ARTIFACTS = "SellArtifacts"

Transport = Callable[[str, dict], dict]


class HttpTransport:
    """Real transport: POST the encrypted envelope to ``gateway_c2.php``.

    Included for wiring completeness; the MVP targets offline analysis and
    leaves the endpoint host configuration to the operator.
    """

    def __init__(self, server_host: str, server_id: str = "", key_version: int = 2,
                 session_token: str = "", timeout: float = 15.0) -> None:
        self.server_host = server_host
        self.server_id = server_id
        self.key_version = key_version
        self.session_token = session_token
        self.timeout = timeout

    def __call__(self, command: str, payload: dict) -> dict:  # pragma: no cover
        raise NotImplementedError(
            "Live transport is intentionally not implemented in the MVP; "
            "inject a Transport callable (see tests) for offline use."
        )


class SWCore:
    """Session state + one-shot battle units + drop handling."""

    def __init__(self, transport: Transport | None = None,
                 default_clear_seconds: float = 240.0,
                 sleeper: Callable[[float], None] = time.sleep,
                 rng: random.Random | None = None) -> None:
        self._transport = transport or HttpTransport("gateway.example.invalid")
        self.sleeper = sleeper
        self.default_clear_seconds = default_clear_seconds
        self.rng = rng or random.Random()
        # resource mirror (updated from responses)
        self.energy = 0
        self.crystals = 0
        self.arena_energy = 0
        self.social_points = 0
        self.wizard_energy = 0
        self.wizard: dict = {}
        # rune/artifact evaluation hooks (set by the engine from profile rules)
        self.rune_rules: list = []
        self.artifact_rules: list = []
        self.smart_level = 0
        self.keep_selling = True  # sell what doesn't pass

    # -- session ----------------------------------------------------------
    def send(self, command: str, **params) -> dict:
        """One encrypted request/response exchange."""
        log.debug("send %s %s", command, params)
        resp = self._transport(command, params)
        wizard = resp.get("wizard_info") or {}
        if wizard:
            self.wizard = wizard
            # wire names: wizard_energy / wizard_crystal (see account.py);
            # older synthetic shapes use energy / crystals.
            self.energy = wizard.get("wizard_energy", wizard.get("energy", self.energy))
            self.crystals = wizard.get("wizard_crystal", wizard.get("crystals", self.crystals))
            self.arena_energy = wizard.get("arena_energy", self.arena_energy)
            self.social_points = wizard.get("social_point_current", wizard.get("social_points", self.social_points))
        return resp

    def sync_wizard(self) -> dict:
        """Refresh the resource mirror from the server (login equivalent)."""
        return self.send(GET_WIZARD_INFO)

    # -- battle units (one battle each, mirrors Do*) ------------------------
    def get_dungeon_record(self, group_id: int) -> float | None:
        """Fetch the account's best clear record (seconds) for a dungeon
        group, live from the server — mirrors the original's
        ``GetDungeonBestCommunityRanking`` + ``my_ranking.clear_time``
        flow. Returns None when the account has no record."""
        resp = self.send(GET_DUNGEON_BEST_COMMUNITY_RANKING, group_id=group_id)
        record = resp.get("my_ranking") or {}
        ms = record.get("clear_time")
        return ms / 1000 if ms else None

    def get_dungeon_time(self, dungeon_id: int, stage: int,
                         record_seconds: float | None = None) -> float:
        """Simulated clear time — CONFIRMED formula (live probe,
        docs/05 §7): ``max(best_record, 20) + uniform(0, 6)`` seconds.
        When no record exists the original resets to a conservative
        default (240 s)."""
        base = record_seconds if record_seconds else self.default_clear_seconds
        return max(base, 20.0) + self.rng.uniform(0.0, 6.0)

    def _sleep_clear(self, seconds: float) -> None:
        log.info("Waiting for %.1f seconds...", seconds)
        self.sleeper(seconds)

    def DoDungeon(self, dungeon_id: int, stage: int, deck: list[int],
                  group_id: int = 1) -> dict:
        record = self.get_dungeon_record(group_id)   # account's best clear
        start = self.send(BATTLE_DUNGEON_START, dungeon_id=dungeon_id,
                          stage=stage, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(start.get("clear_time")
                          or self.get_dungeon_time(dungeon_id, stage, record))
        result = self.send(BATTLE_DUNGEON_RESULT, dungeon_id=dungeon_id,
                           stage=stage, win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    def DoDHole(self, dhole_id: int, stage: int, deck: list[int]) -> dict:
        start = self.send(BATTLE_DHOLE_START, dungeon_id=dhole_id, stage=stage, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(self.get_dungeon_time(dhole_id, stage))
        result = self.send(BATTLE_DHOLE_RESULT, dungeon_id=dhole_id, stage=stage,
                           win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    def DoTower(self, floor: int, difficulty: int, deck: list[int]) -> dict:
        from .timing import get_tower_time
        start = self.send(BATTLE_TOWER_START, floor=floor, difficulty=difficulty, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(get_tower_time(floor, difficulty))
        result = self.send(BATTLE_TOWER_RESULT, floor=floor, difficulty=difficulty,
                           win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    def DoScenario(self, stage_id: int, deck: list[int]) -> dict:
        start = self.send(BATTLE_SCENARIO_START, stage_id=stage_id, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(self.get_dungeon_time(stage_id, 1))
        result = self.send(BATTLE_SCENARIO_RESULT, stage_id=stage_id, win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    def DoRift(self, rift_id: int, deck: list[int]) -> dict:
        start = self.send(BATTLE_RIFT_START, rift_id=rift_id, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(self.get_dungeon_time(rift_id, 1))
        result = self.send(BATTLE_RIFT_RESULT, rift_id=rift_id, win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    def DoRaid(self, level: int, deck: list[int]) -> dict:
        start = self.send(BATTLE_RAID_START, level=level, deck=deck)
        drops = start.get("drop_list", [])
        self._sleep_clear(self.get_dungeon_time(-1, level))
        result = self.send(BATTLE_RAID_RESULT, level=level, win=1, drop_list=drops)
        self.handle_drops(drops, result)
        return result

    # -- drop handling -----------------------------------------------------
    def handle_drops(self, drops: list[dict], result: dict) -> None:
        """Evaluate runes/artifacts; sell what fails rules/smart level."""
        for drop in drops:
            if drop.get("type") == "rune":
                self.handle_rune(drop)
            elif drop.get("type") == "artifact":
                self.handle_artifact(drop)

    def handle_rune(self, rune: dict) -> bool:
        from .score import flatten_rune, rune_score
        from .rules import check_ruleset
        flat = flatten_rune(rune)
        if self.smart_level and self.rune_rules:
            kept = (rune_score(flat) >= self.smart_level
                    or check_ruleset(flat, self.rune_rules))
        elif self.smart_level:
            kept = rune_score(flat) >= self.smart_level
        elif self.rune_rules:
            kept = check_ruleset(flat, self.rune_rules)
        else:
            kept = True
        log.info("Got a rune (set=%s class=%s): %s", rune.get("set_id"),
                 rune.get("class"), "keep" if kept else "sell")
        if self.keep_selling and not kept:
            self.send(SELL_RUNE, rune_id=rune.get("rune_id"))
        return kept

    def handle_artifact(self, artifact: dict) -> bool:
        from .rules import check_ruleset
        flat = dict(artifact)
        kept = check_ruleset(flat, self.artifact_rules) if self.artifact_rules else True
        log.info("Got an artifact: %s", "keep" if kept else "sell")
        if self.keep_selling and not kept:
            self.send(SELL_ARTIFACTS, artifact_ids=[artifact.get("item_id")])
        return kept

    # -- energy policy (recovered exactly from live probe, docs/07 §3.2) -----
    def smart_refill(self, required: int = 8) -> bool:
        """Original policy, in order:
        1. energy >= required -> True (no request)
        2. social points > 500 -> BuyShopItem 2201001 (Heart/Social energy)
        3. crystals >= 300    -> BuyShopItem 100004 (290-crystal energy)
        4. otherwise False ("Cannot refresh energy!")
        """
        if self.energy >= required:
            return True
        if getattr(self, "social_points", 0) > 500:
            log.info("Buying energy by social points...")
            self.send(BUY_SHOP_ITEM, item_id=C.SHOP_HEART_ENERGY)
            self.social_points -= 500
            self.energy += 10
            return True
        if self.crystals >= 300:
            log.info("Buying energy by crystals...")
            self.send(BUY_SHOP_ITEM, item_id=C.SHOP_ENERGY_290)
            self.crystals -= 300
            self.energy += 10
            return True
        log.info("Cannot refresh energy!")
        return False
