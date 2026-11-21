"""SWAPI — the loop layer (Python port of ``summon.SWAPI``).

Mirrors the original call chain (docs/06 §2.3):

    thread.run -> SWAPI.loop* -> Do* (one battle) -> smart_refill

Every loop:

- counts down ``times`` (default ``99999`` = farm forever, as the UI sends),
- checks its ``stop_event`` **between** battles only (cooperative stop — the
  in-flight battle always completes, never cancelled mid-fight),
- runs ``smart_refill`` after each battle and stops when energy can't be
  refreshed.
"""

from __future__ import annotations

import logging
import threading

from .client import SWCore
from . import constants as C

log = logging.getLogger("autoswkit")

FOREVER = 99999


class SWAPI(SWCore):
    """Loop entry points; one instance serves one account session."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.loop_times = 0
        self.account = None

    @classmethod
    def from_account(cls, account, **kwargs):
        """Build a session seeded from a HubUserLogin snapshot
        (:class:`autoswkit.account.AccountProfile`)."""
        sw = cls(**kwargs)
        sw.account = account
        sw.wizard = dict(account.wizard_info)
        sw.energy = account.energy
        sw.crystals = account.crystals
        sw.arena_energy = account.arena_energy
        return sw

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _deck(units: list[int], size: int) -> list[int]:
        """MVP deck builder: first `size` units (real deck-building,
        including rune assignment, is a later milestone — see roadmap)."""
        return list(units[:size])

    def _loop(self, times: int, stop_event: threading.Event | None,
              run_once, label: str, energy_cost: int = 8) -> int:
        """Shared counted-loop skeleton. Returns the runs completed.

        Mirrors the original's two-tier error model (docs/06 §6.1):
        per-iteration failures are logged and skipped, the loop continues
        until the count is exhausted or the stop flag is set.
        """
        if times is None or times <= 0:
            times = FOREVER
        self.sync_wizard()  # resource mirror before the first refill check
        done = 0
        while times > 0 and not (stop_event and stop_event.is_set()):
            try:
                if not self.smart_refill(energy_cost):
                    log.info("%s farming stopped (out of energy)", label)
                    break
                run_once()
                done += 1
            except Exception:
                log.exception("Error in farming iteration (%s)", label)
            times -= 1
        log.info("%s farming stopped", label)
        return done

    # -- loops (names match summon.SWAPI) -----------------------------------
    def loopDungeon(self, dungeon_id: int, times: int | None = None, *,
                    stage: int = 1, units: list[int] | None = None,
                    stop_event: threading.Event | None = None) -> int:
        size = C.GIANT_DECK if dungeon_id == C.GIANT else (C.DRAGON_DECK if dungeon_id == C.DRAGON else C.DUNGEON_DECK)
        deck = self._deck(units or [], size)
        return self._loop(times, stop_event,
                          lambda: self.DoDungeon(dungeon_id, stage, deck),
                          self.get_dungeon_name(dungeon_id))

    def loop_D_HOLE(self, dhole_id: int, times: int | None = None, *,
                    stage: int = 1, units: list[int] | None = None,
                    stop_event: threading.Event | None = None) -> int:
        deck = self._deck(units or [], C.D_HOLE_DECK)
        return self._loop(times, stop_event,
                          lambda: self.DoDHole(dhole_id, stage, deck),
                          f"Dimension hole {dhole_id}")

    def loopAllTower(self, difficulty: int = 1, *,
                     stop_event: threading.Event | None = None,
                     units: list[int] | None = None) -> int:
        """ToA climb: current floor -> 100, then stop (no run count)."""
        floor = int(self.wizard.get("toa_floor", 1))
        deck = self._deck(units or [], C.TOA_DECK)
        done = 0
        while floor <= 100 and not (stop_event and stop_event.is_set()):
            if not self.smart_refill():
                break
            self.DoTower(floor, difficulty, deck)
            self.wizard["toa_floor"] = floor + 1
            floor += 1
            done += 1
        log.info("TOA/H stopped at floor %s", floor)
        return done

    def loopScenario(self, stage_id: int, times: int | None = None, *,
                     units: list[int] | None = None,
                     stop_event: threading.Event | None = None) -> int:
        deck = self._deck(units or [], C.DUNGEON_DECK)
        return self._loop(times, stop_event,
                          lambda: self.DoScenario(stage_id, deck),
                          "Scenario")

    def loopRift(self, rift_id: int, times: int | None = None, *,
                 units: list[int] | None = None,
                 stop_event: threading.Event | None = None) -> int:
        deck = self._deck(units or [], C.DUNGEON_DECK)
        return self._loop(times, stop_event,
                          lambda: self.DoRift(rift_id, deck),
                          "Rift")

    def loopRaid(self, level: int = 1, times: int | None = None, *,
                 units: list[int] | None = None,
                 stop_event: threading.Event | None = None) -> int:
        deck = self._deck(units or [], C.GUILD_DECK)
        return self._loop(times, stop_event,
                          lambda: self.DoRaid(level, deck),
                          "Raid", energy_cost=15)

    # -- naming -------------------------------------------------------------
    @staticmethod
    def get_dungeon_name(dungeon_id: int) -> str:
        return C.DUNGEON_EN.get(dungeon_id, f"dungeon {dungeon_id}")

    # -- inventory clean (ICThread equivalent) --------------------------------
    def inventory_clean(self, account=None, *, clean_runes: bool = True,
                        stop_event: threading.Event | None = None) -> dict:
        """Batch-evaluate unequipped runes and bulk-sell failures.

        Mirrors the original inventory cleaner: evaluate against
        ``rune_rules`` + ``smart_level`` (already configured on the
        session), then sell what fails. Returns a summary dict.
        """
        account = account or self.account
        if account is None:
            raise ValueError("inventory_clean needs an AccountProfile")
        kept = sold = 0
        for rune in account.unequipped_runes():
            if stop_event and stop_event.is_set():
                break
            if self.handle_rune(rune):
                kept += 1
            else:
                sold += 1
        log.info("Inventory cleaner done: kept=%d sold=%d", kept, sold)
        return {"kept": kept, "sold": sold}
