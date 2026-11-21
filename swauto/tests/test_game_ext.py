"""Craft grading, upgrade-cycle wire shape, and deck-building tests."""

import json
from pathlib import Path

import pytest

from swauto.game.crafts import is_shit_stone, craft_grade
from swauto.game.equip import best_equip
from swauto.net.transport import ScriptedTransport
from swauto.game.loops import Loops

FIXTURE = Path(__file__).parent / "fixtures" / "account_fixture.json"


def test_craft_grades_match_recovered_policy():
    g3 = {"craft_type": 1, "craft_type_id": 10903}
    g4 = {"craft_type": 1, "craft_type_id": 10804}
    g5 = {"craft_type": 1, "craft_type_id": 10205}
    grind5 = {"craft_type": 2, "craft_type_id": 10205}
    ancient_grind = {"craft_type": 5, "craft_type_id": 10815}
    # grade 5 always kept
    assert is_shit_stone(g5, smart=100) is False
    assert is_shit_stone(grind5, smart=80) is False
    # grade 4 kept only at low smart
    assert is_shit_stone(g4, smart=0) is False
    assert is_shit_stone(g4, smart=80) is True
    # grade 3 always sold
    assert is_shit_stone(g3, smart=0) is True
    # ancient grindstones always kept
    assert is_shit_stone(ancient_grind, smart=80) is False


def test_craft_grade_extraction():
    assert craft_grade({"craft_type": 1, "craft_type_id": 10204}) == 4
    assert craft_grade({"craft_type": 2, "craft_type_id": 20205}) == 5
    assert craft_grade({"craft_type": 5, "craft_type_id": 10815}) is None


def test_upgrade_wire_command():
    """The inventory-cleaner upgrade cycle uses UpgradeRune_v2 {rune_id}."""
    seen = []

    def handler(payload):
        cmd = payload["command"]
        seen.append(cmd)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeRune_v2":
            return {"ret_code": 0, "rune": {"rune_id": payload["rune_id"], "upgrade_curr": 10}}
        return {"ret_code": 0}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    session.send("UpgradeRune_v2", rune_id=42)
    assert "UpgradeRune_v2" in seen


def test_best_equip_contract_on_real_data():
    snap = json.loads(FIXTURE.read_text(encoding="utf-8"))
    units, runes, artis = snap["unit_list"], snap["runes"], snap["artifacts"]
    ids = [u["unit_id"] for u in units[:3]]
    result = best_equip(units, runes, artis, unit_ids=ids)
    assert len(result) == 3
    for entry in result:
        assert entry["unit_id"] in ids
        assert len(set(entry["rune_id_list"])) == len(entry["rune_id_list"])
        assert len(entry["rune_id_list"]) <= 6
    # runes are exclusive across units
    all_runes = [r for e in result for r in e["rune_id_list"]]
    assert len(all_runes) == len(set(all_runes))


def test_best_equip_full_six_slots_with_abundant_runes():
    # 3 units, plenty of runes per slot -> contract: 6 per unit, slots 1..6
    units = [{"unit_id": i, "class": 6, "unit_level": 40, "spd": 100} for i in (1, 2, 3)]
    runes = [{"rune_id": 100 * slot + i, "set_id": 1, "class": 6, "rank": 5,
              "slot_no": slot, "upgrade_curr": 12, "occupied_id": 0,
              "sec_eff": [[8, 10 + i, 0, 1]]}
             for slot in range(1, 7) for i in range(4)]
    result = best_equip(units, runes, [], unit_ids=[1, 2, 3])
    for entry in result:
        assert len(entry["rune_id_list"]) == 6
    all_runes = [r for e in result for r in e["rune_id_list"]]
    assert len(all_runes) == len(set(all_runes))


async def test_power_up_all_runes_wire_shape_and_judge_cycle():
    """UpgradeRune_v2 carries the exact 4 fields; valuable roll keeps, then stops."""
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeRune_v2":
            # a valuable SPD roll on the first upgrade
            rune = {"rune_id": payload["rune_id"], "upgrade_curr": 12,
                    "class": 6, "set_id": 1,
                    "sec_eff": [[8, 22, 0, 3], [9, 10, 0, 3]]}
            return {"ret_code": 0, "rune": rune}
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    rune = {"rune_id": 42, "upgrade_curr": 11, "upgrade_limit": 15,
            "class": 6, "set_id": 1, "sec_eff": [[8, 15, 0, 2], [9, 10, 0, 3]]}
    n = await session.power_up_all_runes([rune])
    ups = [p for p in sent if p["command"] == "UpgradeRune_v2"]
    assert len(ups) == 1  # one roll judged valuable -> stopped after one cycle
    assert ups[0]["rune_id"] == 42
    assert ups[0]["cash_used"] == 0
    assert ups[0]["loginextend_refcount"] == 0
    assert ups[0]["upgrade_target"] == 15
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert not sells  # a valuable roll is kept, not sold
    assert n == 1


async def test_power_up_all_runes_sells_trash_roll():
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeRune_v2":
            rune = {"rune_id": payload["rune_id"], "upgrade_curr": 12,
                    "class": 6, "set_id": 1,
                    "sec_eff": [[8, 9, 0, 1], [9, 10, 0, 3]]}  # SPD below 10 floor
            return {"ret_code": 0, "rune": rune}
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    rune = {"rune_id": 42, "upgrade_curr": 11, "upgrade_limit": 15,
            "class": 6, "set_id": 1, "sec_eff": [[8, 5, 0, 0], [9, 10, 0, 3]]}
    n = await session.power_up_all_runes([rune])
    ups = [p for p in sent if p["command"] == "UpgradeRune_v2"]
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert len(ups) == 1
    assert len(sells) == 1  # trash roll -> sold (batched rune_id_list wire shape)
    assert sells[0]["rune_id_list"] == [42]


async def test_inventory_clean_sells_construction_trash_powers_rest():
    """Non-legend/no-hard runes sell immediately; legend runes get powered."""
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeRune_v2":
            rune = {"rune_id": payload["rune_id"], "upgrade_curr": 12,
                    "class": 6, "set_id": 1,
                    "sec_eff": [[8, 22, 0, 3], [9, 10, 0, 3]]}
            return {"ret_code": 0, "rune": rune}
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    trash = {"rune_id": 1, "upgrade_curr": 0, "upgrade_limit": 15, "class": 5,
             "set_id": 1, "sec_eff": []}                     # non-legend: never valuable
    legend = {"rune_id": 2, "upgrade_curr": 11, "upgrade_limit": 15, "class": 6,
              "set_id": 1, "sec_eff": [[8, 15, 0, 2], [9, 10, 0, 3]]}
    sold = await session.inventory_clean([trash, legend])
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert [i for p in sells for i in p["rune_id_list"]] == [1]
    assert sold == 1
    ups = [p for p in sent if p["command"] == "UpgradeRune_v2"]
    assert ups and ups[0]["rune_id"] == 2


# --- Phase B1: lock-aware selling + batched sell + count guard -----------------
async def test_inventory_clean_batches_trash_sell_as_rune_id_list():
    """The trash pass sells the whole set in ONE batched SellRune {rune_id_list},
    matching the oracle wire shape (probed live, 2026-09-07)."""
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    trash_a = {"rune_id": 1, "upgrade_curr": 0, "upgrade_limit": 15, "class": 1,
               "set_id": 1, "sec_eff": []}
    trash_b = {"rune_id": 2, "upgrade_curr": 0, "upgrade_limit": 15, "class": 1,
               "set_id": 2, "sec_eff": []}
    sold = await session.inventory_clean([trash_a, trash_b])
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert sold == 2
    assert len(sells) == 1  # one batched call for the whole trash set
    assert sorted(sells[0]["rune_id_list"]) == [1, 2]


async def test_inventory_clean_never_sells_locked_rune():
    """A player-locked rune is neither sold nor counted as sold (Phase B1)."""
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    trash = {"rune_id": 1, "upgrade_curr": 0, "upgrade_limit": 15, "class": 1,
             "set_id": 1, "sec_eff": []}
    locked = {"rune_id": 38533068720, "upgrade_curr": 0, "upgrade_limit": 15,
              "class": 1, "set_id": 2, "sec_eff": []}
    session.locked_rune_ids = {38533068720}
    sold = await session.inventory_clean([trash, locked])
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert [i for p in sells for i in p["rune_id_list"]] == [1]
    assert sold == 1  # locked rune not counted as sold


async def test_handle_rune_skips_locked():
    sent = []

    def handler(payload):
        sent.append(payload)
        return {"ret_code": 0}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    session.smart_level = 100            # score can never reach -> judged sell-worthy
    session.locked_rune_ids = {99}
    locked = {"rune_id": 99, "set_id": 1, "class": 1, "sec_eff": []}
    kept = await session.handle_rune(locked)  # non-valuable by score
    sells = [p for p in sent if p["command"] == "SellRune"]
    assert kept is True       # locked => treated as kept, never sold
    assert not sells


def test_count_guard_strict_over_cap_semantics():
    """check_rune_count/check_artifact_count fire STRICTLY over the cap
    (count > max), mirroring the probed oracle polarity and caps
    (rune_max=artifact_max=1500 — see _A3_inventory_outcome.md §5)."""
    session = Loops(ScriptedTransport({"*": lambda p: {"ret_code": 0}}),
                    sleeper=lambda s: None)
    session.rune_count = 1500
    session.rune_max = 1500
    assert not session.over_rune_cap()   # equal -> not over (matches oracle)
    session.rune_count = 1501
    assert session.over_rune_cap()
    session.rune_count = 940
    session.rune_max = 1000              # arbitrary max still honored
    assert not session.over_rune_cap()
    # defaults are the probed caps (1500/1500)
    fresh = Loops(ScriptedTransport({"*": lambda p: {"ret_code": 0}}),
                  sleeper=lambda s: None)
    assert fresh.rune_max == 1500
    assert fresh.artifact_max == 1500


# --- artifact upgrade wire shape (structure-only, docs/07 §3.6/§3.9) ----------
def _fresh_artifact(payload, subs):
    return {"ret_code": 0,
            "artifact": {"rid": payload["artifact_id"],
                         "level": payload.get("upgrade_target", 15),
                         "type": 2, "attribute": 0, "unit_style": 3,
                         "rank": 5, "occupied_id": 0,
                         "pri_effect": [101, 100, 15, 0, 0],
                         "sec_effects": [list(s) for s in subs]}}


async def test_power_up_all_artifacts_wire_shape_and_keep_on_valuable():
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeArtifact_v2":
            # a valuable presence sub (401) revealed at the target level
            return _fresh_artifact(payload, [[209, 3, 0, 0, 0], [401, 12, 0, 0, 0]])
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    arti = {"rid": 7, "type": 2, "attribute": 0, "unit_style": 3, "rank": 5,
            "level": 12, "occupied_id": 0, "pri_effect": [101, 100, 15, 0, 0],
            "sec_effects": [[209, 3, 0, 0, 0]]}
    n = await session.power_up_all_artifacts([arti])
    ups = [p for p in sent if p["command"] == "UpgradeArtifact_v2"]
    assert len(ups) == 1  # one milestone judged valuable -> kept, stopped
    assert ups[0]["artifact_id"] == 7
    assert ups[0]["upgrade_target"] == 15  # next +3 milestone from level 12
    sells = [p for p in sent if p["command"] == "SellArtifacts"]
    assert not sells  # a valuable reveal is kept
    assert n == 1


async def test_power_up_all_artifacts_sells_on_no_valuable_at_max():
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeArtifact_v2":
            # only never-valid subs at max level -> never valuable
            return _fresh_artifact(payload, [[209, 3, 0, 0, 0], [403, 5, 0, 0, 0]])
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    arti = {"rid": 7, "type": 2, "attribute": 0, "unit_style": 3, "rank": 5,
            "level": 14, "occupied_id": 0, "pri_effect": [101, 100, 15, 0, 0],
            "sec_effects": [[209, 3, 0, 0, 0]]}
    n = await session.power_up_all_artifacts([arti])
    ups = [p for p in sent if p["command"] == "UpgradeArtifact_v2"]
    sells = [p for p in sent if p["command"] == "SellArtifacts"]
    assert len(ups) == 1
    assert len(sells) == 1  # reached max with no valuable -> sold
    assert sells[0]["artifact_ids"] == [7]


async def test_inventory_clean_artifact_pass_sells_cap_trash_powers_rest():
    """At-cap never-valid artifacts sell; sub-max artifacts (even never-valid
    today) power, because a +3 milestone can still reveal a valuable sub."""
    sent = []

    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "UpgradeArtifact_v2":
            return _fresh_artifact(payload, [[401, 12, 0, 0, 0], [208, 4, 0, 0, 0]])
        return {"ret_code": 0, "wizard_info": {"wizard_energy": 999}}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None)
    cap_trash = {"rid": 1, "type": 1, "attribute": 0, "unit_style": 0, "rank": 4,
                 "level": 15, "occupied_id": 0, "pri_effect": [100, 1500],
                 "sec_effects": [[209, 3, 0, 0, 0], [403, 5, 0, 0, 0]]}  # at cap, never-valid only
    submax = {"rid": 2, "type": 2, "attribute": 0, "unit_style": 3, "rank": 5,
              "level": 12, "occupied_id": 0, "pri_effect": [101, 100],
              "sec_effects": [[209, 3, 0, 0, 0]]}   # sub-max: power, reveal possible
    sold = await session.inventory_clean([], artifacts=[cap_trash, submax])
    sells = [p for p in sent if p["command"] == "SellArtifacts"]
    assert [s["artifact_ids"] for s in sells] == [[1]]
    ups = [p for p in sent if p["command"] == "UpgradeArtifact_v2"]
    assert ups and ups[0]["artifact_id"] == 2
    assert sold == 0  # rune-only return stays backward-compatible


async def test_dungeon_uses_best_equip_deck():
    snap = json.loads(FIXTURE.read_text(encoding="utf-8"))
    server_calls = []

    def handler(payload):
        cmd = payload["command"]
        server_calls.append(cmd)
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "GetDungeonBestCommunityRanking":
            return {"my_ranking": {"clear_time": 32000, "my_unit_deck_list": []}}
        if cmd == "BattleDungeonStart":
            return {"battle_key": 1, "drop_list": []}
        return {"ret_code": 0, "drop_list": []}

    session = Loops(ScriptedTransport({"*": handler}), sleeper=lambda s: None, rng_seed=1)
    deck_units = snap["unit_list"][:7]
    deck = best_equip(snap["unit_list"], snap["runes"], snap["artifacts"],
                      unit_ids=[u["unit_id"] for u in deck_units])
    tid_units = [e["unit_id"] for e in deck]
    await session.loop_dungeon(8001, 1, units=tid_units)
    starts = [c for c in server_calls if c == "BattleDungeonStart"]
    assert starts


# --- Phase B2: scenario as 2nd complete reference (docs/07 §3.7/§3.8) ----------
def _scenario_handler(sent, friends=None):
    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetFriendList":
            return {"ret_code": 0, "assist_count": 2,
                    "friend_list": friends or []}
        if cmd == "GetWizardInfo":
            return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 1000}}
        if cmd == "BattleScenarioStart":
            return {"ret_code": 0, "battle_key": 1, "clear_time": 30000,
                    "drop_list": []}
        return {"ret_code": 0, "drop_list": [], "result": 1}
    return handler


async def test_do_scenario_friendless_matches_captured_payload():
    """Friendless BattleScenarioStart exactly matches the A2 capture verbatim."""
    sent = []
    session = Loops(ScriptedTransport({"*": _scenario_handler(sent)}),
                    sleeper=lambda s: None)
    # the five unit ids from the A2 capture/7280513 profile
    deck = [26390577257, 26609043194, 26609037532, 35784261882, 35784261883]
    await session.do_scenario(9, 1, 3, deck)
    starts = [p for p in sent if p["command"] == "BattleScenarioStart"]
    assert len(starts) == 1
    start = starts[0]
    assert start["region_id"] == 9
    assert start["difficulty"] == 3
    assert start["stage_no"] == 1
    assert start["unit_id_list"] == deck
    assert start["helper_list"] == []
    assert start["mentor_helper_list"] == []
    assert start["npc_friend_helper_list"] == []
    assert start["retry"] == 0
    assert start["auto_repeat"] == 0


async def test_do_scenario_draws_friend_assist_helper():
    """A friend with a rep unit becomes helper_list [{"unit_id","wizard_id"}]."""
    sent = []
    friends = [{"wizard_id": 900000001, "name": "RepA", "level": 50,
                "assist_count": 2, "rep_unit_id": 26390577257}]
    session = Loops(ScriptedTransport({"*": _scenario_handler(sent, friends)}),
                    sleeper=lambda s: None)
    await session.do_scenario(9, 1, 3, [26609043194, 26609037532], helper_list=[{"unit_id": 26390577257, "wizard_id": 900000001}])
    starts = [p for p in sent if p["command"] == "BattleScenarioStart"]
    assert starts[0]["helper_list"] == [{"unit_id": 26390577257, "wizard_id": 900000001}]


async def test_pick_friend_assist_uses_rep_unit():
    """_pick_friend_assist returns [] when no usable friend, and the helper
    entry carries unit_id (the rep) + wizard_id when one is usable."""
    session = Loops(ScriptedTransport({"*": lambda p: {"ret_code": 0}}),
                    sleeper=lambda s: None)
    assert session._pick_friend_assist({}) == []
    assert session._pick_friend_assist({"friend_list": [{"name": "no-rep"}]}) == []
    assert session._pick_friend_assist({
        "friend_list": [{"wizard_id": 900000001, "name": "A",
                         "rep_unit_id": 26390577257}]}) == \
        [{"unit_id": 26390577257, "wizard_id": 900000001}]


async def test_loop_scenario_chain_getfriendlist_then_battle():
    """loop_scenario prefetches friends ONCE (GetFriendList), syncs energy
    (GetWizardInfo), then fires the captured BattleScenarioStart — the
    recovered loop chain (B2 re-probe)."""
    sent = []
    friends = [{"wizard_id": 900000001, "name": "RepA", "level": 50,
                "assist_count": 2, "rep_unit_id": 26390577257}]
    session = Loops(ScriptedTransport({"*": _scenario_handler(sent, friends)}),
                    sleeper=lambda s: None)
    await session.loop_scenario(9, 1, times=2, units=[26390577257, 26609043194, 26609037532])
    cmds = [p["command"] for p in sent]
    # sequence: friend fetch must come before any battle start, and only once
    assert cmds.index("GetFriendList") < cmds.index("BattleScenarioStart")
    friend_fetches = [p for p in sent if p["command"] == "GetFriendList"]
    assert len(friend_fetches) == 1  # prefetched once, not per-run
    starts = [p for p in sent if p["command"] == "BattleScenarioStart"]
    assert len(starts) == 2
    assert starts[0]["helper_list"] == [{"unit_id": 26390577257, "wizard_id": 900000001}]


# --- A4: recovered-exact content payloads (work/autosw/trace/_A4_*.md) --------
def _content_handler(sent, wizard=None):
    def handler(payload):
        cmd = payload["command"]
        sent.append(payload)
        if cmd == "GetDungeonBestCommunityRanking":
            return {"ret_code": 0, "my_ranking": {"clear_time": 32000}}
        if cmd == "GetWizardInfo":
            return {"ret_code": 0, "wizard_info": wizard or
                    {"wizard_energy": 999, "wizard_crystal": 1000,
                     "dimension_hole_info": {"energy": 1200, "energy_max": 1150}}}
        if cmd in ("BattleDungeonStart", "BattleDimensionHoleDungeonStart"):
            return {"ret_code": 0, "battle_key": 1, "drop_list": []}
        return {"ret_code": 0, "drop_list": [], "result": 1}
    return handler


async def test_do_dungeon_payload_matches_recovered_capture():
    """do_dungeon emits the recovered-exact BattleDungeonStart (A4 §1): the
    stage field is stage_id, unit_id_list is [{unit_id},...] objects, equip is
    null — NOT the old skeleton's stage/bare-int-list/equip:[]."""
    sent = []
    deck = [26390577257, 26609043194, 26609037532, 35784261882, 35784261883]
    session = Loops(ScriptedTransport({"*": _content_handler(sent)}),
                    sleeper=lambda s: None)
    await session.do_dungeon(9001, 1, deck)
    starts = [p for p in sent if p["command"] == "BattleDungeonStart"]
    assert len(starts) == 1
    start = starts[0]
    # the three corrected fields
    assert start["stage_id"] == 1
    assert "stage" not in start          # old (wrong) field name is gone
    assert start["unit_id_list"] == [{"unit_id": u} for u in deck]  # objects, not ints
    assert start["equip"] is None        # null, not []
    # the recovered fixed/flag fields
    assert start["dungeon_id"] == 9001
    assert start["helper_list"] == []
    assert start["mentor_helper_list"] == []
    assert start["npc_friend_helper_list"] == []
    assert start["is_rooting"] == 0
    assert start["cash_used"] == 0
    assert start["retry"] == 0
    assert start["auto_repeat"] == 0


async def test_do_dungeon_cairos_family_uses_generic_unit():
    """The whole Cairos family (giant/dragon/necro/...) rides the one generic
    BattleDungeonStart unit — regression that the recovered payload covers each
    id (A4 §1: rd_8001..rd_9501 all share the identical shape)."""
    for did in (8001, 9001, 6001, 9501, 5001, 1001):
        sent = []
        deck = [26390577257, 26609043194, 26609037532]
        session = Loops(ScriptedTransport({"*": _content_handler(sent)}),
                        sleeper=lambda s: None)
        await session.do_dungeon(did, 1, deck)
        starts = [p for p in sent if p["command"] == "BattleDungeonStart"]
        assert len(starts) == 1
        assert starts[0]["dungeon_id"] == did
        assert starts[0]["stage_id"] == 1
        assert starts[0]["unit_id_list"] == [{"unit_id": u} for u in deck]


async def test_do_dhole_payload_matches_recovered_capture():
    """do_dhole emits the recovered-exact BattleDimensionHoleDungeonStart (A4
    §2): dungeon_id/difficulty, a 16-unit dungeon_units deck as
    [{unit_id, leader, position}] with leader at slot 0, dungeon_level/stage."""
    sent = []
    # fixture only has 8 units; use them and pad is unnecessary — shape is what
    # the recovery grounded (D_HOLE_DECK caps at 16 when enough units exist).
    deck = [26390577257, 26609043194, 26609037532, 35784261882, 35784261883,
            26390577257, 26609043194, 26609037532, 35784261882, 35784261883,
            26390577257, 26609043194, 26609037532, 35784261882, 35784261883,
            26609043194]
    session = Loops(ScriptedTransport({"*": _content_handler(sent)}),
                    sleeper=lambda s: None)
    await session.do_dhole(2202, deck)
    starts = [p for p in sent if p["command"] == "BattleDimensionHoleDungeonStart"]
    assert len(starts) == 1
    start = starts[0]
    assert start["dungeon_id"] == 2202
    assert start["difficulty"] == 5
    assert start["practice_mode"] == 0
    assert start["retry"] == 0
    assert start["is_rooting"] == 0
    assert start["auto_repeat"] == 0
    dus = start["dungeon_units"]
    assert len(dus) == len(deck)
    # leader at slot 0 only
    assert dus[0] == {"unit_id": deck[0], "leader": 1}
    for i in range(1, len(dus)):
        assert dus[i] == {"unit_id": deck[i], "leader": 0, "position": i}
    assert start["dungeon_level"] == 1
    assert start["dungeon_stage"] == 1
    assert start["helper_list"] == []
    assert start["npc_friend_helper_list"] == []
