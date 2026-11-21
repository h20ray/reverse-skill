"""MVP bot-engine tests: timing, rules, profile, and an end-to-end
dungeon loop against a scripted fake server (offline, no sleeps)."""

from __future__ import annotations

import threading
import time

import pytest

from autoswkit import constants as C
from autoswkit import timing
from autoswkit.api import SWAPI
from autoswkit.engine import TaskConflictError, TaskManager, UnknownTaskError
from autoswkit.profile import ProfileStore
from autoswkit.rules import Rule, RuleSet, check_ruleset
from autoswkit.score import flatten_rune, rune_score


# --- timing -----------------------------------------------------------------
def test_tower_time_matches_recovered_formulas():
    assert timing.get_tower_time(1, 1) == pytest.approx(15.4)
    assert timing.get_tower_time(2, 1) == pytest.approx(12.8)
    assert timing.get_tower_time(50, 1) == pytest.approx(6.4 * 50)
    assert timing.get_tower_time(100, 1) == pytest.approx(640.0)
    for level in range(1, 101):
        assert timing.get_tower_time(level, 2) == pytest.approx(10.4 * level)


def test_tower_time_hell_is_jittered():
    samples = [timing.get_tower_time(1, 3) for _ in range(50)]
    assert all(1400 < s < 2300 for s in samples)
    assert len(set(samples)) > 10  # non-deterministic


# --- rules -------------------------------------------------------------------
def test_ruleset_check_semantics_match_original():
    rs = RuleSet(name="p", enabled=True, rune_sets=[13], rules=[["SPD", ">=", 10]])
    keep, _ = rs.check({"set_id": 13, "SPD": 11})
    assert keep
    keep, _ = rs.check({"set_id": 13, "SPD": 5})
    assert not keep
    keep, _ = rs.check({"set_id": 3, "SPD": 20})  # wrong set filter
    assert not keep


def test_rule_operator_map_matches_original():
    for op in ("==", "!=", ">", ">=", "<", "<="):
        Rule("SPD", op, 10)
    with pytest.raises(ValueError):
        Rule("SPD", "~=", 10)


def test_check_ruleset_any_enabled_accepts():
    a = RuleSet(name="a", enabled=True, rules=[["SPD", ">=", 20]])
    b = RuleSet(name="b", enabled=True, rules=[["HP%", ">=", 5]])
    assert check_ruleset({"SPD": 3, "HP%": 7}, [a, b])


# --- scoring -----------------------------------------------------------------
def test_flatten_rune_from_raw_game_shape():
    raw = {"rune_id": 1, "set_id": 13, "class": 5, "slot_no": 2, "upgrade_level": 12,
           "main_stat": {"type": 9, "value": 15},
           "substat_list": [{"type": 8, "value": 11}, {"type": 10, "value": 6}]}
    flat = flatten_rune(raw)
    assert flat["SPD"] == 11          # type 8
    assert flat["CDmg"] == 6          # type 10
    assert flat["set_id"] == 13
    assert rune_score(flat) > 0


# --- profile ------------------------------------------------------------------
def test_profile_store_round_trip(tmp_path):
    store = ProfileStore(tmp_path / "profiles")
    prof = ProfileStore(tmp_path / "profiles").load.__self__  # noqa: F841
    from autoswkit.profile import Profile
    store.save(Profile("acct1", {
        "tasks": [{"task_name": "dungeon", "task_params": {"dungeon_id": C.GIANT, "times": 100}}]
    }))
    assert store.list_profiles() == ["acct1"]
    loaded = store.load("acct1")
    assert loaded.tasks[0]["task_params"]["dungeon_id"] == C.GIANT


# --- engine end-to-end ---------------------------------------------------------
class FakeServer:
    """Scripted gateway: remembers every command, returns drops."""

    def __init__(self, drop: dict):
        self.calls: list[tuple[str, dict]] = []
        self.drop = drop

    def __call__(self, command: str, params: dict) -> dict:
        self.calls.append((command, params))
        return {"wizard_info": {"energy": 999, "crystals": 1000},
                "drop_list": [self.drop]}


@pytest.fixture
def no_sleep(monkeypatch):
    real = time.sleep
    seen: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: seen.append(s))
    yield seen
    assert all(s > 0 for s in seen)  # sleeps were simulated, not skipped


def make_session(server):
    return SWAPI(transport=server, sleeper=time.sleep, default_clear_seconds=0.5)


def test_dungeon_loop_end_to_end(no_sleep):
    server = FakeServer({"type": "rune", "rune_id": 42, "set_id": 13,
                         "class": 5, "slot_no": 2, "upgrade_level": 12,
                         "substat_list": [{"type": 8, "value": 15}]})
    session = make_session(server)
    session.rune_rules = [RuleSet(name="keep-spd", rules=[["SPD", ">=", 10]])]
    mgr = TaskManager(session)
    tid = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 3,
                                      "stage": 1, "units": [1, 2, 3, 4, 5, 6, 7]})
    mgr.wait_all(timeout=5)
    assert mgr.task_status(tid) == "Stopped"
    starts = [c for c in server.calls if c[0] == "BattleDungeonStart_v2"]
    results = [c for c in server.calls if c[0] == "BattleDungeonResult_V2"]
    sells = [c for c in server.calls if c[0] == "SellRune"]
    assert len(starts) == len(results) == 3   # 3 runs
    assert not sells                          # SPD 15 passes -> kept
    assert starts[0][1]["dungeon_id"] == C.GIANT


def test_dungeon_loop_sells_failing_rune(no_sleep):
    server = FakeServer({"type": "rune", "rune_id": 7, "set_id": 13,
                         "class": 5, "slot_no": 2, "upgrade_level": 12,
                         "substat_list": [{"type": 10, "value": 4}]})
    session = make_session(server)
    session.rune_rules = [RuleSet(name="keep-spd", rules=[["SPD", ">=", 10]])]
    mgr = TaskManager(session)
    mgr.create_task("dungeon", {"dungeon_id": C.DRAGON, "times": 2,
                                "stage": 1, "units": [1] * 8})
    mgr.wait_all(timeout=5)
    sells = [c for c in server.calls if c[0] == "SellRune"]
    assert len(sells) == 2
    assert sells[0][1]["rune_id"] == 7


def test_conflict_gate_rejects_overlap(no_sleep):
    # energy is 999 -> smart_refill passes without buying; run forever
    server = FakeServer({"type": "rune", "rune_id": 1, "set_id": 1,
                         "class": 1, "slot_no": 1, "upgrade_level": 0,
                         "substat_list": []})
    session = make_session(server)
    mgr = TaskManager(session)
    t1 = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 0, "units": []})
    with pytest.raises(TaskConflictError):
        mgr.create_task("raid", {"level": 1, "times": 0, "units": []})
    mgr.stop_task(t1)
    mgr.wait_all(timeout=5)
    # after stop, the conflicting task can start
    t2 = mgr.create_task("raid", {"level": 1, "times": 1, "units": []})
    mgr.wait_all(timeout=5)
    assert mgr.task_status(t2) == "Stopped"


def test_unknown_task_and_verbatim_params(no_sleep):
    server = FakeServer({"type": "rune", "set_id": 1, "class": 1,
                         "slot_no": 1, "upgrade_level": 0, "substat_list": []})
    session = make_session(server)
    mgr = TaskManager(session)
    with pytest.raises(UnknownTaskError):
        mgr.create_task("nope", {})
    params = {"dungeon_id": C.GIANT, "times": 1, "units": [], "custom_field": {"a": 1}}
    mgr.create_task("dungeon", params)
    mgr.wait_all(timeout=5)
    stored = list(mgr.task_params.values())[0]
    assert stored == params  # task_params kept verbatim


def test_cooperative_stop_finishes_current_battle(no_sleep):
    server = FakeServer({"type": "rune", "set_id": 1, "class": 1,
                         "slot_no": 1, "upgrade_level": 0, "substat_list": []})
    session = make_session(server)
    started = threading.Event()
    real_do = session.DoDungeon

    def slow_do(*a, **k):
        started.set()
        time.sleep(0.05)
        return real_do(*a, **k)

    session.DoDungeon = slow_do
    mgr = TaskManager(session)
    tid = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 0, "units": []})
    started.wait(1)
    mgr.stop_task(tid)          # stop while battle 1 in flight
    mgr.wait_all(timeout=5)
    results = [c for c in server.calls if c[0] == "BattleDungeonResult_V2"]
    assert len(results) >= 1    # in-flight battle completed and submitted


# --- dungeon timing formula (live-probed, docs/05 §7) ---------------------------
class RecordServer:
    """Answers the ranking call with a best record, then a battle."""

    def __init__(self, record_ms):
        self.record_ms = record_ms
        self.calls = []

    def __call__(self, command, params):
        self.calls.append(command)
        if command == "GetDungeonBestCommunityRanking":
            return {"ret_code": 0,
                    "my_ranking": {"clear_time": self.record_ms,
                                   "my_unit_deck_list": []}}
        return {"battle_key": 1, "dungeon_unit_list": [],
                "drop_list": [], "reward_list": []}


def test_dungeon_time_is_best_record_plus_jitter(no_sleep):
    server = RecordServer(record_ms=32000)   # 32 s best record
    session = make_session(server)
    session.rng.seed(7)
    session.DoDungeon(8001, 1, [1, 2, 3])
    assert server.calls == ["GetDungeonBestCommunityRanking",
                            "BattleDungeonStart_v2", "BattleDungeonResult_V2"]
    waited = no_sleep[0]
    assert 32.0 <= waited <= 38.0          # record + U(0,6)


def test_dungeon_time_floored_at_20s(no_sleep):
    server = RecordServer(record_ms=5000)  # 5 s record -> floor 20 s
    session = make_session(server)
    session.rng.seed(7)
    session.DoDungeon(8001, 1, [1])
    assert 20.0 <= no_sleep[0] <= 26.0


def test_no_record_uses_conservative_default(no_sleep):
    server = RecordServer(record_ms=None)  # no my_ranking record
    session = make_session(server)
    session.default_clear_seconds = 240.0  # original's 240 s reset
    session.rng.seed(7)
    session.DoDungeon(8001, 1, [1])
    assert 240.0 <= no_sleep[0] <= 246.0   # original's 240 s reset


def test_failing_transport_does_not_abort_loop(no_sleep):
    """Per-iteration failures are logged and skipped (docs/06 §6.1)."""
    class FailOnce:
        def __init__(self):
            self.calls = []

        def __call__(self, command, params):
            self.calls.append(command)
            if command == "GetWizardInfo":
                return {"wizard_info": {"wizard_energy": 999, "wizard_crystal": 100}}
            raise ConnectionError("server down")

    server = FailOnce()
    session = make_session(server)
    mgr = TaskManager(session)
    tid = mgr.create_task("dungeon", {"dungeon_id": C.GIANT, "times": 3, "units": []})
    mgr.wait_all(timeout=5)
    starts = [c for c in server.calls if c == "BattleDungeonStart_v2"]
    assert mgr.task_status(tid) == "Stopped"
    assert not starts                  # every iteration failed at the send layer


def test_smart_refill_exact_recovered_policy():
    from autoswkit.client import SWCore
    calls = []
    session = SWCore(transport=lambda c, p: (calls.append(c), {"wizard_info": {}})[1],
                     sleeper=lambda s: None)
    session.energy = 5
    # 1. enough energy -> no request
    session.energy = 999
    assert session.smart_refill(8) is True and not calls
    # 2. social path: > 500 points -> item 2201001
    session.energy = 5; session.social_points = 501; session.crystals = 0
    assert session.smart_refill(8) is True
    assert calls[-1] == "BuyShopItem"
    # 3. crystal path: >= 300 -> item 100004
    session.energy = 5; session.social_points = 0; session.crystals = 300
    assert session.smart_refill(8) is True
    # 4. neither -> False
    session.energy = 5; session.crystals = 299
    assert session.smart_refill(8) is False


def test_eval_rune_weights_match_original():
    """Recovered weights must reproduce the original's scores exactly."""
    from autoswkit.score import rune_score
    flat = {"HP%": 14, "RES": 13, "SPD": 6, "ACC": 7}
    assert rune_score(flat) == pytest.approx(105.0)   # real rune 3570259156
    flat2 = {"SPD": 16, "RES": 8, "HP%": 6, "CDmg": 7}
    assert rune_score(flat2) == pytest.approx(108.3333333)  # real rune 6787667696
