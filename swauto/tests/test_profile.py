"""Account snapshot lock-state readers (Phase B1) + sanitize contract."""

import json
from pathlib import Path

from swauto.config.profile import AccountSnapshot, SENSITIVE_KEYS

FIXTURE = Path(__file__).parent / "fixtures" / "account_fixture.json"


def _acct(**over):
    base = {
        "wizard_id": 7280513,
        "this_server_id": 4,
        "rune_lock_list": [],
        "runes": [],
        "artifacts": [],
        "account_info": {"token": "live-token", "game_index": 2623},
    }
    base.update(over)
    return AccountSnapshot(base)


def test_locked_rune_ids_from_server_lock_list():
    acct = _acct(rune_lock_list=[
        {"lock_type": 1, "rune_id": 38533068720, "wizard_id": 7280513},
        {"lock_type": 1, "rune_id": 42, "wizard_id": 7280513},
        # lock_type 0 = unlocked; unknown shapes ignored -> never block a sale
        {"lock_type": 0, "rune_id": 7, "wizard_id": 7280513},
        "garbage",
    ])
    assert acct.locked_rune_ids() == {38533068720, 42}


def test_locked_rune_ids_empty_when_no_lock_list():
    acct = _acct()  # no rune_lock_list key at all
    assert acct.locked_rune_ids() == set()


def test_locked_artifact_ids_from_locked_field():
    acct = _acct(artifacts=[
        {"rid": 1, "locked": 1},
        {"rid": 2, "locked": 0},
        {"rid": 3},                      # field absent -> unlocked
    ])
    assert acct.locked_artifact_ids() == {1}


def test_sanitize_strips_session_keys_and_token():
    acct = _acct(session_key="s" * 40, session_key_node="n" * 40,
                 reqid="r" * 36, ts_val=12345)
    clean = acct.sanitize()
    for key in SENSITIVE_KEYS:
        assert key not in clean
    assert "token" not in clean["account_info"]
    assert clean["wizard_id"] == 7280513


def test_fixture_lock_readers_degrade_gracefully():
    """The committed fixture has no rune_lock_list and only locked:0 artifacts —
    both readers must return empty, never raise."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    acct = AccountSnapshot(data)
    assert acct.locked_rune_ids() == set()
    assert acct.locked_artifact_ids() == set()
