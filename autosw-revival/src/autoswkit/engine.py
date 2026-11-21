"""Task engine — Python port of the ``control.pyd`` scheduler
(docs/06-worker-threads.md).

Preserved behaviors:

- ``create_task`` is a factory: allocates a task_id, wraps the task in a
  FarmThread, registers it, starts it.
- **Cooperative stop**: ``stop_task`` sets the thread's ``quit_event``;
  the current battle completes, the loop then exits.
- **Conflict sets**: starting a task whose conflict set intersects a
  running task's set is rejected outright ("Task conflict") — no queue.
- ``task_params`` are stored verbatim so status/restart reuse the exact
  original payload.
"""

from __future__ import annotations

import logging
import threading

from .api import SWAPI
from .profile import PVP_TASKS, TASK_CONFLICTS

log = logging.getLogger("autoswkit")


class TaskConflictError(RuntimeError):
    pass


class PvpRequiredError(RuntimeError):
    pass


class UnknownTaskError(ValueError):
    pass


class FarmThread(threading.Thread):
    """One task: params as attributes + quit_event + run() -> loop call."""

    def __init__(self, task_id: int, task_name: str, task_params: dict,
                 loop_fn, pvp_required: bool = False) -> None:
        super().__init__(name=f"FarmThread-{task_id}-{task_name}", daemon=True)
        self.task_id = task_id
        self.task_name = task_name
        self.task_params = task_params  # verbatim payload
        self.task_status = "Running"
        self.quit_event = threading.Event()
        self.pvp_required = pvp_required
        self._loop_fn = loop_fn
        self.runs_completed = 0

    def run(self) -> None:
        try:
            log.info("Task %s (%s) started", self.task_id, self.task_name)
            self.runs_completed = self._loop_fn(self.quit_event) or 0
        except Exception:
            log.exception("%s error in task %s", self.task_name, self.task_id)
        finally:
            self.task_status = "Stopped"
            log.info("%s farming stopped (task %s)", self.task_name, self.task_id)

    def stop(self) -> None:
        self.quit_event.set()


class TaskManager:
    """Registry + conflict gate + thread factory (mirrors MainControl)."""

    def __init__(self, session: SWAPI, pvp_enabled: bool = True) -> None:
        self.session = session
        self.pvp_enabled = pvp_enabled
        self.tasks: dict[int, FarmThread] = {}
        self.task_params: dict[int, dict] = {}
        self.statuses: dict[int, str] = {}
        self.task_conflict: dict[int, frozenset[str]] = {}
        self._next_id = 1

    # -- payload builders: task_params -> loop call -------------------------
    def _loop_for(self, task_name: str, params: dict):
        """Return a callable(stop_event) that runs the task's loop."""
        sw = self.session
        name = task_name.lower()

        if name == "dungeon":
            return lambda ev: sw.loopDungeon(
                int(params["dungeon_id"]), params.get("times"),
                stage=int(params.get("stage", 1)),
                units=params.get("units") or [], stop_event=ev)
        if name == "dhole":
            return lambda ev: sw.loop_D_HOLE(
                int(params["dhole_id"]), params.get("times"),
                stage=int(params.get("stage", 1)),
                units=params.get("units") or [], stop_event=ev)
        if name in ("toa", "toah"):
            return lambda ev: sw.loopAllTower(
                difficulty=2 if name == "toah" else 1,
                units=params.get("units") or [], stop_event=ev)
        if name == "toahell":
            return lambda ev: sw.loopAllTower(difficulty=3,
                                              units=params.get("units") or [],
                                              stop_event=ev)
        if name == "scenario":
            return lambda ev: sw.loopScenario(
                int(params["stage_id"]), params.get("times"),
                units=params.get("units") or [], stop_event=ev)
        if name == "rift":
            return lambda ev: sw.loopRift(
                int(params["rift_id"]), params.get("times"),
                units=params.get("units") or [], stop_event=ev)
        if name == "raid":
            return lambda ev: sw.loopRaid(
                int(params.get("level", 1)), params.get("times"),
                units=params.get("units") or [], stop_event=ev)
        raise UnknownTaskError(
            f"Task {task_name!r} is not implemented in the MVP "
            f"(known: dungeon/dhole/toa/toah/toahell/scenario/rift/raid)")

    # -- MainControl surface -------------------------------------------------
    def create_task(self, task_name: str, task_params: dict) -> int:
        name = task_name.lower()
        if name in PVP_TASKS and not self.pvp_enabled:
            raise PvpRequiredError("PVP mode required")
        conflicts = TASK_CONFLICTS.get(name)
        if conflicts is None:
            raise UnknownTaskError(f"Unknown task: {task_name!r}")
        for tid, thread in self.tasks.items():
            if (thread.task_status == "Running"
                    and self.task_conflict[tid] & conflicts):
                raise TaskConflictError(f"Task conflict with running task {tid}")
        loop_fn = self._loop_for(name, task_params)
        task_id = self._next_id
        self._next_id += 1
        thread = FarmThread(task_id, name, task_params, loop_fn,
                            pvp_required=name in PVP_TASKS)
        self.tasks[task_id] = thread
        self.task_params[task_id] = task_params  # verbatim
        self.statuses[task_id] = "Running"
        self.task_conflict[task_id] = conflicts
        thread.start()
        return task_id

    def start_task(self, task_id: int) -> None:
        thread = self.tasks.get(task_id)
        if thread is None:
            raise KeyError("Task not found")
        if thread.task_status == "Running":
            return
        loop_fn = self._loop_for(thread.task_name, self.task_params[task_id])
        fresh = FarmThread(task_id, thread.task_name,
                           self.task_params[task_id], loop_fn,
                           pvp_required=thread.pvp_required)
        self.tasks[task_id] = fresh
        self.statuses[task_id] = "Running"
        fresh.start()

    def stop_task(self, task_id: int) -> None:
        thread = self.tasks.get(task_id)
        if thread is None:
            raise KeyError("Task not found")
        thread.stop()

    def stop_all(self) -> None:
        for thread in self.tasks.values():
            thread.stop()

    def remove_task(self, task_id: int) -> None:
        thread = self.tasks.pop(task_id, None)
        if thread is None:
            raise KeyError("Task not found")
        thread.stop()
        self.task_params.pop(task_id, None)
        self.statuses.pop(task_id, None)
        self.task_conflict.pop(task_id, None)

    def remove_all(self) -> None:
        for task_id in list(self.tasks):
            self.remove_task(task_id)

    def task_status(self, task_id: int) -> str:
        thread = self.tasks.get(task_id)
        if thread is None:
            return self.statuses.get(task_id, "Unknown")
        return thread.task_status

    def wait_all(self, timeout: float | None = None) -> None:
        for thread in self.tasks.values():
            thread.join(timeout)
