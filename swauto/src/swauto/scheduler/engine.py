"""Async scheduler — clean-room port of the documented task engine
(docs/06, docs/07 §2).

- one asyncio task per accepted task ("FarmThread" equivalent),
- cooperative stop via asyncio.Event: the in-flight battle completes,
- conflict sets reject overlapping energy consumers at start time,
- task params stored verbatim for restart/status display.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from ..config.profile import PVP_TASKS, TASK_CONFLICTS
from ..game.loops import Loops
from ..game import constants as C

log = logging.getLogger("swauto.scheduler")

FOREVER = 99999


class TaskConflictError(RuntimeError):
    pass


class PvpRequiredError(RuntimeError):
    pass


class UnknownTaskError(ValueError):
    pass


@dataclass
class TaskHandle:
    task_id: int
    name: str
    params: dict
    pvp_required: bool
    conflict: frozenset[str]
    status: str = "Running"
    runs: int = 0
    event: asyncio.Event = field(default_factory=asyncio.Event)
    runner: asyncio.Task | None = None


class TaskManager:
    def __init__(self, session: Loops, pvp_enabled: bool = True) -> None:
        self.session = session
        self.pvp_enabled = pvp_enabled
        self.tasks: dict[int, TaskHandle] = {}
        self._next_id = 1

    # -- payload builders (task name -> loop coroutine) -----------------------
    def _runner(self, name: str, params: dict, handle: TaskHandle):
        s = self.session
        n = name.lower()
        units = params.get("units") or []
        times = params.get("times")

        if n == "dungeon":
            return s.loop_dungeon(int(params["dungeon_id"]), times, stage=int(params.get("stage", 1)),
                                  group_id=int(params.get("group_id", 1)), units=units,
                                  stop_event=handle.event)
        if n == "toa":
            return self._tower_climb(s, 1, params, handle)
        if n == "toah":
            return self._tower_climb(s, 2, params, handle)
        if n == "toahell":
            return self._tower_climb(s, 3, params, handle)
        if n == "hoh":
            return s.loop_hoh(int(params["dungeon_id"]),
                              start_stage=int(params.get("start_stage", params.get("stage", 1))),
                              end_stage=int(params.get("end_stage", 10)),
                              units=units,
                              auto_climb=params.get("auto_climb", True),
                              stop_event=handle.event)
        if n == "scenario":
            return s.loop_scenario(int(params.get("region", 1)), int(params.get("stage", 1)),
                                   times, difficulty=int(params.get("difficulty", 1)),
                                   units=units, stop_event=handle.event)
        raise UnknownTaskError(
            f"Task {name!r} not implemented yet (dungeon/hoh/toa/toah/toahell/scenario available)")

    async def _tower_climb(self, s: Loops, difficulty: int, params: dict, handle: TaskHandle):
        floor = int(params.get("floor", 1))
        deck = (params.get("units") or [])[:C.TOA_DECK]
        done = 0
        while floor <= 100 and not handle.event.is_set():
            if not s.smart_refill():
                break
            await s.do_tower(floor, difficulty, deck)
            floor += 1
            done += 1
        return done

    # -- surface (mirrors MainControl) ----------------------------------------
    def create_task(self, name: str, params: dict) -> int:
        n = name.lower()
        if n in PVP_TASKS and not self.pvp_enabled:
            raise PvpRequiredError("PVP mode required")
        conflicts = TASK_CONFLICTS.get(n)
        if conflicts is None:
            raise UnknownTaskError(f"Unknown task: {name!r}")
        for h in self.tasks.values():
            if h.status == "Running" and h.conflict & conflicts:
                raise TaskConflictError(f"Task conflict with running task {h.task_id}")
        task_id = self._next_id
        self._next_id += 1
        handle = TaskHandle(task_id, n, dict(params), n in PVP_TASKS, conflicts)
        handle.params = params  # verbatim
        handle.runner = asyncio.get_running_loop().create_task(self._run(handle))
        self.tasks[task_id] = handle
        return task_id

    async def _run(self, handle: TaskHandle) -> None:
        try:
            log.info("Task %s (%s) started", handle.task_id, handle.name)
            handle.runs = await self._runner(handle.name, handle.params, handle) or 0
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("%s error in task %s", handle.name, handle.task_id)
        finally:
            handle.status = "Stopped"
            log.info("%s farming stopped (task %s)", handle.name, handle.task_id)

    def stop_task(self, task_id: int) -> None:
        self._get(task_id).event.set()

    def stop_all(self) -> None:
        for h in self.tasks.values():
            h.event.set()

    def remove_task(self, task_id: int) -> None:
        h = self._get(task_id)
        h.event.set()
        del self.tasks[task_id]

    def status(self, task_id: int) -> str:
        return self._get(task_id).status

    def _get(self, task_id: int) -> TaskHandle:
        try:
            return self.tasks[task_id]
        except KeyError:
            raise KeyError("Task not found") from None

    async def wait_all(self) -> None:
        runners = [h.runner for h in self.tasks.values() if h.runner]
        for r in runners:
            try:
                await r
            except asyncio.CancelledError:
                pass
