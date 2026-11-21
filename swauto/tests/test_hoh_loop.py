"""Tests for Hall of Heroes (HoH) dropdown discovery, stage listing, and auto-climb loop."""

import asyncio
import pytest

from swauto.game import constants as C
from swauto.game.loops import Loops
from swauto.net.transport import ScriptedTransport
from swauto.scheduler.engine import TaskManager


def make_hoh_session(cleared_stages=None, wizard_energy=999):
    cleared_stages = cleared_stages or []
    calls = []

    def handler(payload):
        cmd = payload.get("command")
        calls.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": wizard_energy, "wizard_crystal": 1000}}
        if cmd == "GetDungeonList":
            return {
                "ret_code": 0,
                "dungeon_list": [
                    {
                        "dungeon_id": 8001,
                        "group_id": 1,
                        "stage_list": [{"stage_id": i + 1, "cleared": 1} for i in range(10)],
                    },
                    {
                        "dungeon_id": 10065,
                        "group_id": 10,
                        "unit_master_id": 18212,  # Pirate Captain / Barque
                        "stage_list": [
                            {"stage_id": i + 1, "cleared": 1 if (i + 1) in cleared_stages else 0}
                            for i in range(10)
                        ],
                    },
                ],
            }
        if cmd == "BattleDungeonStart":
            return {"battle_key": payload.get("stage_id", 1), "drop_list": []}
        if cmd == "BattleDungeonResult_V2":
            return {"ret_code": 0, "drop_list": []}
        return {"ret_code": 0}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    return session, calls


def test_dungeon_list_hoh_parsing():
    session, _ = make_hoh_session(cleared_stages=[1, 2, 3])
    dungeons = session.get_dungeon_list()

    assert len(dungeons) == 2
    giant = next(d for d in dungeons if d["id"] == 8001)
    assert not giant["is_hoh"]
    assert giant["name"] == "Giant"
    assert giant["cleared_stage"] == 10

    hoh = next(d for d in dungeons if d["id"] == 10065)
    assert hoh["is_hoh"]
    assert "Barque" in hoh["name"] or "Pirate Captain" in hoh["name"] or "Hall of Heroes" in hoh["name"]
    assert hoh["cleared_stage"] == 3
    assert hoh["total_stages"] == 10
    assert len(hoh["stages"]) == 10

    # Verify each stage in the 10-stage list
    assert hoh["stages"][0] == {"stage_id": 1, "cleared": True}
    assert hoh["stages"][1] == {"stage_id": 2, "cleared": True}
    assert hoh["stages"][2] == {"stage_id": 3, "cleared": True}
    assert hoh["stages"][3] == {"stage_id": 4, "cleared": False}
    assert hoh["stages"][9] == {"stage_id": 10, "cleared": False}


@pytest.mark.asyncio
async def test_loop_hoh_full_clear():
    session, calls = make_hoh_session(cleared_stages=[])
    cleared = await session.loop_hoh(10065, start_stage=1, end_stage=10, auto_climb=True)

    assert cleared == 10
    start_calls = [c for c in calls if c.get("command") == "BattleDungeonStart"]
    assert len(start_calls) == 10
    stages_run = [c.get("stage_id") for c in start_calls]
    assert stages_run == list(range(1, 11))


@pytest.mark.asyncio
async def test_loop_hoh_resume_from_uncleared():
    # Stages 1, 2, 3 already cleared -> auto-climb should start at Floor 4
    session, calls = make_hoh_session(cleared_stages=[1, 2, 3])
    cleared = await session.loop_hoh(10065, start_stage=1, end_stage=10, auto_climb=True)

    assert cleared == 7
    start_calls = [c for c in calls if c.get("command") == "BattleDungeonStart"]
    assert len(start_calls) == 7
    stages_run = [c.get("stage_id") for c in start_calls]
    assert stages_run == [4, 5, 6, 7, 8, 9, 10]


@pytest.mark.asyncio
async def test_task_manager_hoh_task():
    session, calls = make_hoh_session(cleared_stages=[1, 2, 3, 4, 5])
    mgr = TaskManager(session)

    tid = mgr.create_task("hoh", {"dungeon_id": 10065, "auto_climb": True})
    await mgr.wait_all()

    assert mgr.status(tid) == "Stopped"
    assert mgr.tasks[tid].runs == 5  # Floors 6, 7, 8, 9, 10
