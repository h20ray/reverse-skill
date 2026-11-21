"""Account-profile tests: load a sanitized HubUserLogin snapshot, verify
resource seeding, deck picking, and an offline inventory_clean pass."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from autoswkit.account import AccountProfile, flatten_rune_game
from autoswkit.api import SWAPI
from autoswkit.engine import TaskManager
from autoswkit.rules import RuleSet

FIXTURE = Path(__file__).parent / "fixtures" / "account_fixture.json"


@pytest.fixture
def account() -> AccountProfile:
    return AccountProfile.load(FIXTURE)


def test_account_resources_map_from_wire_names(account):
    assert account.wizard_id == 7280513
    assert account.energy == account.wizard_info["wizard_energy"]
    assert account.crystals == account.wizard_info["wizard_crystal"]
    assert account.arena_energy == account.wizard_info["arena_energy"]


def test_sanitize_drops_session_secrets(account):
    clean = account.sanitize()
    assert "session_key" not in clean
    assert "token" not in clean.get("account_info", {})


def test_flatten_rune_game_shape_extracts_sec_eff(account):
    rune = next(r for r in account.runes if r.get("sec_eff"))
    flat = flatten_rune_game(rune)
    assert flat["upgrade_level"] == rune["upgrade_curr"]
    for eff in rune["sec_eff"]:
        assert eff[0] in flat["sec_eff_map"]


def test_best_units_returns_requested_count_sorted(account):
    ids = account.best_units(5)
    assert len(ids) == 5
    top = max(account.units, key=lambda u: (u.get("class", 0), u.get("unit_level", 0), u.get("spd", 0)))
    assert ids[0] == top["unit_id"]


class RecordingServer:
    def __init__(self):
        self.calls = []

    def __call__(self, command, params):
        self.calls.append((command, params))
        return {"wizard_info": {}, "drop_list": []}


def test_session_from_account_seeds_resources(account):
    server = RecordingServer()
    session = SWAPI.from_account(account, transport=server, sleeper=time.sleep)
    assert session.energy == account.energy
    assert session.crystals == account.crystals
    assert session.account is account


def test_inventory_clean_end_to_end(account):
    server = RecordingServer()
    session = SWAPI.from_account(account, transport=server, sleeper=time.sleep)
    # only keep runes with a SPD substat >= 10
    session.rune_rules = [RuleSet(name="spd10", rules=[["SPD", ">=", 10]])]
    summary = session.inventory_clean(account)
    unequipped = account.unequipped_runes()
    assert summary["kept"] + summary["sold"] == len(unequipped)
    sells = [c for c in server.calls if c[0] == "SellRune"]
    assert len(sells) == summary["sold"]
    # every sold rune indeed fails the SPD rule
    for cmd, params in sells:
        rune = next(r for r in unequipped if r["rune_id"] == params["rune_id"])
        flat = flatten_rune_game(rune)
        assert not (flat.get("SPD", 0) >= 10)


def test_dungeon_task_uses_account_units_when_missing(account):
    seen = []
    server = RecordingServer()
    session = SWAPI.from_account(account, transport=server,
                                 sleeper=lambda s: seen.append(s))
    seen.clear()
    session.rng.seed(42)   # deterministic jitter
    mgr = TaskManager(session)
    deck_size = 7  # Giant deck
    tid = mgr.create_task("dungeon", {"dungeon_id": 8001, "times": 2, "units": account.best_units(deck_size)})
    mgr.wait_all(timeout=5)
    starts = [p for c, p in server.calls if c == "BattleDungeonStart_v2"]
    assert len(starts) == 2
    assert starts[0]["deck"] == account.best_units(deck_size)
    assert mgr.task_status(tid) == "Stopped"
