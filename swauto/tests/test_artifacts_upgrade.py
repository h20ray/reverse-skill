"""Recovered artifact-evaluation membership rule + structure-only upgrade.

Every rule in this file was recovered empirically against the compiled module
(runnable oracle, `work/autosw/trace/`) and verified over the real account pool
(MooN capture, 777 artifacts): ``getArtifactValuableSub(arti, guess=False)``
matched **777/777** real artifacts and **5000/5000** adversarial synthetic
artifacts, plus exhaustive per-sub floor-boundary sweeps (all zero mismatches).

The artifact *upgrade* method ``smartArtifactUpgradeCheck`` is NOT recoverable
offline (Phase A probe: returns ``False`` for every real/synthetic dict —
live-session-gated), so the upgrade orchestration in ``client.py`` is a
structure-only port judged by ``valuable_subs``; this file does NOT claim its
thresholds are exact.
"""

import pytest

from swauto.game.artifacts import (
    ARTI_NEVER_VALUABLE,
    ARTI_PRESENCE_VALUABLE,
    ARTI_VALUE_FLOOR,
    sub_ratio,
    valuable_subs,
)

# --- table sanity ---------------------------------------------------------------
def test_tables_are_fully_partitioned():
    """Every defined substat id is in exactly one group (never/presence/floor)."""
    from swauto.game.artifacts import ARTI_SUB
    defined = set(ARTI_SUB)
    never, presence, floored = (
        set(ARTI_NEVER_VALUABLE), set(ARTI_PRESENCE_VALUABLE), set(ARTI_VALUE_FLOOR))
    assert never.isdisjoint(presence) and never.isdisjoint(floored)
    assert presence.isdisjoint(floored)
    assert never | presence | floored == defined, (
        (defined - never - presence - floored))


def test_never_valuable_ids():
    assert ARTI_NEVER_VALUABLE == frozenset({203, 207, 209, 211, 212, 213,
                                             216, 217, 403})


def test_presence_valuable_ids():
    assert ARTI_PRESENCE_VALUABLE == frozenset({204, 205, 218, 219, 220, 221,
                                                226, 400, 401, 402, 404, 405,
                                                406, 407, 408, 409, 410, 411})


def test_value_floor_ids():
    assert set(ARTI_VALUE_FLOOR) == {200, 201, 202, 206, 208, 210, 214, 215,
                                     222, 223, 224, 225,
                                     300, 301, 302, 303, 304,
                                     305, 306, 307, 308, 309}


# --- never-valuable: excluded at any value -------------------------------------
def test_never_valuable_never_counts():
    for sid in ARTI_NEVER_VALUABLE:
        a = {"level": 15, "sec_effects": [[sid, 999, 0, 0, 0]]}
        assert valuable_subs(a) == {}


# --- presence-valuable: count at any value (even 0/negative) -------------------
@pytest.mark.parametrize("val", [-1.0, 0.0, 0.3, 50.0])
def test_presence_valuable_counts_at_any_value(val):
    for sid in sorted(ARTI_PRESENCE_VALUABLE):
        a = {"level": 15, "sec_effects": [[sid, val, 0, 0, 0]]}
        assert valuable_subs(a) == {sid: 1}


# --- value-floored: value >= floor counts, just below does not ------------------
@pytest.mark.parametrize("sid", sorted(ARTI_VALUE_FLOOR))
def test_value_floor_boundary(sid):
    floor = ARTI_VALUE_FLOOR[sid]
    a_in = {"level": 15, "sec_effects": [[sid, floor, 0, 0, 0]]}
    a_out = {"level": 15, "sec_effects": [[sid, floor - 0.5, 0, 0, 0]]}
    assert valuable_subs(a_in) == {sid: 1}
    assert valuable_subs(a_out) == {}


def test_value_floor_values_match_recovered():
    assert ARTI_VALUE_FLOOR[200] == 12
    assert ARTI_VALUE_FLOOR[215] == 6   # life drain, floor not mid 6.5
    assert ARTI_VALUE_FLOOR[223] == 10
    assert ARTI_VALUE_FLOOR[300] == 4
    assert ARTI_VALUE_FLOOR[305] == 5


# --- real-artifact pin (docs/07 §3.6 rid 304066801) ----------------------------
REAL_ARTI = {"rid": 304066801, "type": 2, "attribute": 0, "unit_style": 3,
             "rank": 5, "level": 15, "occupied_id": 0,
             "pri_effect": [101, 100, 15, 0, 0],
             "sec_effects": [[200, 9, 0, 0, 0], [401, 24, 4, 0, 0],
                             [215, 5, 0, 0, 0], [208, 4, 0, 0, 0]]}


def test_real_artifact_valuable_subs_match_compiled():
    # compiled getArtifactValuableSub(guess=False) on this real artifact:
    # {401, 208} (401@4.8, 208@1.33; 200@0.78 and 215@0.77 are below floor)
    assert set(valuable_subs(REAL_ARTI)) == {401, 208}


def test_real_artifact_ratios():
    assert sub_ratio(9, 200) == pytest.approx(0.7826, abs=1e-3)
    assert sub_ratio(24, 401) == pytest.approx(4.8)


# --- keep/sell value source feeds the upgrade decision (cap vs sub-max) ---------
def test_submax_never_valid_only_is_a_power_candidate():
    """A sub-max artifact is never trash by its current substats alone: it
    reveals a NEW substat only at +3 milestones, so an artifact whose present
    subs are all never-valid can still become valuable while leveling. The
    empty ``valuable_subs`` is not a sell signal until the cap (nothing can
    change above it) — the upgrade cycle owns that decision."""
    a = {"level": 9, "sec_effects": [[209, 3, 0, 0, 0], [403, 5, 0, 0, 0]]}
    assert valuable_subs(a) == {}   # not valuable NOW...
    assert a["level"] < 15          # ...but a +12 reveal is still possible


def test_at_cap_valuable_subs_is_the_final_keep_sell_word():
    """At the upgrade cap an artifact can no longer reveal anything, so
    ``valuable_subs`` alone decides: floored-below-floor subs never cross, and
    never-valid subs never register — both read as a sell."""
    at_cap = {"level": 15, "sec_effects": [[200, 9, 0, 0, 0], [209, 3, 0, 0, 0]]}
    assert valuable_subs(at_cap) == {}   # 200 below floor 12, 209 never-valid
    keep = {"level": 15, "sec_effects": [[200, 12, 0, 0, 0]]}
    assert valuable_subs(keep) == {200: 1}
