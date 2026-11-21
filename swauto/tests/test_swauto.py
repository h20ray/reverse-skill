"""swauto skeleton tests: crypto round-trip, timing formulas, scoring,
rules, offline end-to-end dungeon loop through the async scheduler."""

import asyncio
import json

import pytest

from swauto.game import constants as C
from swauto.game.timing import dungeon_time, tower_time
from swauto.game.score import flatten_rune, rune_score
from swauto.game.rules import Rule, RuleSet
from swauto.game.loops import Loops
from swauto.net.transport import ScriptedTransport
from swauto.scheduler.engine import TaskConflictError, TaskManager, UnknownTaskError


# --- crypto -------------------------------------------------------------------
def test_crypto_envelope_round_trip():
    from swauto.net import crypto
    wire = crypto.encrypt_request('{"a": 1}', version=2)
    assert crypto.decrypt_request(wire, 2) == '{"a": 1}'
    resp = crypto.encrypt_response('{"b": 2}', version=2)
    assert crypto.decrypt_response(resp, 2) == '{"b": 2}'
    kind, _ = crypto.auto_decrypt(resp, 2)
    assert kind == "response"


# --- timing -------------------------------------------------------------------
def test_tower_formulas():
    assert tower_time(1, 1) == pytest.approx(15.4)
    assert tower_time(50, 1) == pytest.approx(320.0)
    assert tower_time(100, 2) == pytest.approx(1040.0)


def test_dungeon_time_floor_and_jitter():
    vals = [dungeon_time(32.0, rng=__import__("random").Random(1)) for _ in range(30)]
    assert all(32.0 <= v <= 38.0 for v in vals)
    floored = [dungeon_time(5.0, rng=__import__("random").Random(1)) for _ in range(30)]
    assert all(20.0 <= v <= 26.0 for v in floored)
    assert dungeon_time(None, rng=__import__("random").Random(1)) >= 240.0


# --- scoring -------------------------------------------------------------------
def test_exact_recovered_weights():
    assert rune_score({"HP%": 14, "RES": 13, "SPD": 6, "ACC": 7}) == pytest.approx(105.0)
    assert rune_score({"SPD": 16, "RES": 8, "HP%": 6, "CDmg": 7}) == pytest.approx(108.3333333)


def test_flatten_wire_format():
    raw = {"rune_id": 1, "set_id": 1, "class": 6, "rank": 5, "slot_no": 3,
           "upgrade_curr": 15, "pri_eff": [5, 160],
           "sec_eff": [[2, 14, 0, 2], [8, 6, 0, 1]]}
    flat = flatten_rune(raw)
    assert flat["HP%"] == 14 and flat["SPD"] == 6 and flat["upgrade_level"] == 15


# --- rules ---------------------------------------------------------------------
def test_ruleset_semantics():
    rs = RuleSet(name="p", rune_sets=[13], rules=[["SPD", ">=", 10]])
    assert rs.check({"set_id": 13, "SPD": 11})[0]
    assert not rs.check({"set_id": 13, "SPD": 5})[0]
    assert not rs.check({"set_id": 3, "SPD": 20})[0]


# --- end-to-end ------------------------------------------------------------------
def demo_server(record_ms=32000):
    def handler(payload):
        cmd = payload["command"]
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "GetFriendList":
            return {"ret_code": 0, "assist_count": 0, "friend_list": []}
        if cmd == "GetDungeonBestCommunityRanking":
            return {"my_ranking": {"clear_time": record_ms, "my_unit_deck_list": []}}
        if cmd == "BattleDungeonStart" or cmd == "BattleScenarioStart":
            return {"battle_key": 1, "drop_list": [{"type": "rune", "rune_id": 9,
                                                    "set_id": 13, "class": 6, "rank": 5,
                                                    "slot_no": 2, "upgrade_curr": 12,
                                                    "sec_eff": [[8, 15, 0, 1]]}]}
        return {"ret_code": 0, "drop_list": []}
    return ScriptedTransport({"*": handler})


async def test_dungeon_loop_end_to_end():
    server = demo_server()
    session = Loops(server, sleeper=lambda s: None, rng_seed=7)
    session.rune_rules = [RuleSet(name="spd", rules=[["SPD", ">=", 10]])]
    mgr = TaskManager(session)
    tid = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 3,
                                      "stage": 1, "units": [1, 2, 3, 4, 5, 6, 7]})
    await mgr.wait_all()
    assert mgr.status(tid) == "Stopped"
    assert mgr.tasks[tid].runs == 3
    cmds = [c for c, _ in server.calls]
    assert cmds.count("BattleDungeonStart") == 3
    assert cmds.count("BattleDungeonResult_V2") == 3
    assert "SellRune" not in cmds        # SPD 15 passes


async def test_scheduler_conflict_and_stop():
    server = demo_server()
    session = Loops(server, sleeper=lambda s: None, rng_seed=7)
    mgr = TaskManager(session)
    t1 = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 0, "units": []})
    with pytest.raises(TaskConflictError):
        mgr.create_task("raid", {"times": 1, "units": []})
    mgr.stop_task(t1)
    await mgr.wait_all()
    with pytest.raises(UnknownTaskError):
        mgr.create_task("nope", {})


# --- artifacts -------------------------------------------------------------------
REAL_ARTI = {"rid": 304066801, "type": 2, "attribute": 0, "unit_style": 3, "rank": 5,
             "level": 15, "occupied_id": 0,
             "pri_effect": [101, 100, 15, 0, 0],
             "sec_effects": [[200, 9, 0, 0, 0], [401, 24, 4, 0, 0],
                             [215, 5, 0, 0, 0], [208, 4, 0, 0, 0]]}


def test_artifact_valuable_subs_match_original():
    """Recovered semantics: valuable = value >= midpoint(min,max).
    Expected from the live module on this real artifact: {401, 208}."""
    from swauto.game.artifacts import valuable_subs, sub_ratio
    v = valuable_subs(REAL_ARTI)
    assert set(v) == {401, 208}
    assert sub_ratio(9, 200) == pytest.approx(0.7826, abs=1e-3)
    assert sub_ratio(24, 401) == pytest.approx(4.8)
    assert sub_ratio(5, 215) == pytest.approx(0.7692, abs=1e-3)


def test_artifact_flatten_wire_format():
    from swauto.game.artifacts import flatten_artifact
    flat = flatten_artifact(REAL_ARTI)
    assert flat["unit_style"] == "HP"
    assert flat["main_ATK flat"] == 100
    assert flat["Skill 2 CD"] == 24
    assert flat["sub_ratios"][401] == 4.8


async def test_handle_artifact_sells_unvaluable():
    server_calls = []
    session = Loops(ScriptedTransport({"*": lambda p: (server_calls.append(p["command"]), {"ret_code": 0})[1]}),
                    sleeper=lambda s: None)
    session.keep_selling = True
    bad = {"rid": 1, "type": 1, "attribute": 0, "unit_style": 0, "rank": 1, "level": 0,
           "pri_effect": [100, 500], "sec_effects": [[306, 4, 0, 0, 0], [307, 4, 0, 0, 0],
                                                     [305, 3, 0, 0, 0], [308, 3, 0, 0, 0]]}
    kept = await session.handle_artifact(bad)
    assert kept is False
    assert "SellArtifacts" in server_calls


# --- Phase B2: scenario scheduler runner (docs/05 SThread + docs/07 §3.7) -----
async def test_scenario_task_runner_end_to_end():
    """The scenario scheduler runner drives the recovered loop chain
    (GetFriendList -> GetWizardInfo -> BattleScenarioStart) and stops cleanly
    on stop_task (cooperative stop)."""
    server = demo_server()
    session = Loops(server, sleeper=lambda s: None, rng_seed=3)
    mgr = TaskManager(session)
    tid = mgr.create_task("scenario", {"region": 9, "stage": 1, "difficulty": 3,
                                       "times": 3,
                                       "units": [1, 2, 3, 4, 5]})
    await mgr.wait_all()
    assert mgr.status(tid) == "Stopped"
    assert mgr.tasks[tid].runs == 3
    cmds = [c for c, _ in server.calls]
    assert cmds.count("GetFriendList") == 1          # prefetched once
    assert cmds.count("BattleScenarioStart") == 3
    assert cmds[0] == "GetFriendList"                # first fetch before battle
