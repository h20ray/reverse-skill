"""Loop layer — counted async loops over battle units (docs/07 §3.2, §3.5).

Preserved behaviors:
- default run count 99999 (farm forever),
- cooperative stop: stop_event checked between battles only,
- energy policy applied before each battle; failure stops the loop,
- per-iteration failures are logged and skipped (two-tier error model).
"""

from __future__ import annotations

import logging

from .client import BattleClient
from . import constants as C

log = logging.getLogger("swauto.game")

FOREVER = 99999


class Loops(BattleClient):
    async def loop_dungeon(self, dungeon_id: int, times: int | None = None, *,
                           stage: int = 1, group_id: int = 1,
                           units: list[int] | None = None,
                           stop_event=None) -> int:
        size = (C.GIANT_DECK if dungeon_id == C.GIANT
                else C.DRAGON_DECK if dungeon_id == C.DRAGON else C.DUNGEON_DECK)
        deck = (units or [])[:size]
        return await self._loop(times, stop_event, lambda: self.do_dungeon(
            dungeon_id, stage, deck, group_id), C.DUNGEON_EN.get(dungeon_id, f"dungeon {dungeon_id}"))

    async def loop_tower(self, level: int, difficulty: int = 1, *,
                         units: list[int] | None = None, stop_event=None) -> int:
        deck = (units or [])[:C.TOA_DECK]
        return await self._loop(1, stop_event, lambda: self.do_tower(level, difficulty, deck),
                                f"tower {level}")

    async def loop_hoh(self, dungeon_id: int, start_stage: int = 1, end_stage: int = 10, *,
                       units: list[int] | None = None, auto_climb: bool = True,
                       stop_event=None) -> int:
        """Hall of Heroes loop — clears floor 1..10 (or resumes uncleared floors).

        Deck size is capped at SECRET_DECK (9).
        Auto-refills energy (8 energy per floor).
        """
        deck = (units or [])[:C.SECRET_DECK]

        current_stage = start_stage
        if auto_climb:
            try:
                d_list = self.get_dungeon_list()
                target_d = next((d for d in d_list if d["id"] == dungeon_id), None)
                if target_d:
                    uncleared = [s["stage_id"] for s in target_d.get("stages", []) if not s.get("cleared")]
                    if uncleared:
                        current_stage = max(start_stage, min(uncleared))
                    elif target_d.get("cleared_stage", 0) >= C.HOH_STAGES:
                        log.info("HoH dungeon %d already completed all stages!", dungeon_id)
                        return 0
            except Exception:
                log.warning("Could not pre-fetch HoH stage list; defaulting to stage %d", start_stage)

        self.sync_wizard()
        done = 0
        log.info("Starting HoH dungeon %d from Floor %d to Floor %d", dungeon_id, current_stage, end_stage)

        for stage in range(current_stage, min(end_stage, C.HOH_STAGES) + 1):
            if stop_event and stop_event.is_set():
                log.info("HoH farming stopped (stop requested)")
                break
            if not self.smart_refill(required=8):
                log.info("HoH farming stopped (out of energy)")
                break
            try:
                await self.do_hoh_stage(dungeon_id, stage, deck)
                done += 1
            except Exception:
                log.exception("Error in HoH iteration (Floor %d)", stage)
                break

        log.info("HoH farming stopped (%d floors cleared)", done)
        return done

    async def loop_dhole(self, dungeon_id: int, times: int | None = None, *,
                         units: list[int] | None = None, difficulty: int = 5,
                         stop_event=None) -> int:
        """Dimension-Hole loop — the 16-unit dhole deck (recovered, A4 §2).

        Energy comes from the dimension-hole energy pool (``dimension_hole_info``
        with ``energy_max`` — NOT the regular wizard energy), so this loop does
        not use the regular 8-energy refill. The deck is capped at
        ``D_HOLE_DECK`` (16)."""
        deck = (units or [])[:C.D_HOLE_DECK]
        # dhole energy is its own pool; only battle when there is at least 1
        energy = int(getattr(self, "dimension_hole_energy", 0) or 0)
        if energy <= 0:
            log.info("dhole farming stopped (no dimension-hole energy)")
            return 0
        return await self._loop(times, stop_event,
                                lambda: self.do_dhole(dungeon_id, deck,
                                                      difficulty=difficulty),
                                f"dhole {dungeon_id}", energy_cost=0)

    async def loop_scenario(self, region: int, stage: int, times: int | None = None, *,
                            difficulty: int = 1, units: list[int] | None = None,
                            stop_event=None) -> int:
        deck = (units or [])[:C.DUNGEON_DECK]
        # the original's loopScenario fetches friends ONCE before the battle
        # loop (GetFriendList -> picks an assist) — recovered offline (B2).
        helper = await self._scenario_friends()
        return await self._loop(times, stop_event,
                                lambda: self.do_scenario(region, stage, difficulty,
                                                         deck, helper),
                                "scenario")

    async def loop_inventory_clean(self, runes: list[dict], *,
                                   artifacts: list[dict] | None = None,
                                   options: dict | None = None) -> int:
        """Inventory-clean entry (docs/07 §3.9): sell trash, power the rest.

        Runs the recovered two-pass cleaner over the given unequipped rune
        pool, plus an equivalent artifact pass when ``artifacts`` is supplied.
        """
        return await self.inventory_clean(runes, artifacts, options)

    async def _loop(self, times: int | None, stop_event, run_once, label: str,
                    energy_cost: int = 8) -> int:
        if times is None or times <= 0:
            times = FOREVER
        self.sync_wizard()
        done = 0
        while times > 0 and not (stop_event and stop_event.is_set()):
            try:
                if not self.smart_refill(energy_cost):
                    log.info("%s farming stopped (out of energy)", label)
                    break
                await run_once()
                done += 1
            except Exception:
                log.exception("Error in farming iteration (%s)", label)
            times -= 1
        log.info("%s farming stopped", label)
        return done
