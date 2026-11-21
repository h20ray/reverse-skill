"""Recovered rune-evaluation predicates (docs/07 §3.8–3.9).

Every rule in this file was recovered empirically against the compiled module
(runnable oracle, `work/autosw/trace/`) and verified over the real account pool
(MooN capture): isTrashStats 7512/7512, getValuableStats 7452/7452,
smartUpgradeCheck 8300/8300. These tests pin the port to those exact rules.
"""

import pytest

from swauto.game.evaluate import (
    HARD_VALUABLE_IDS,
    MIN_VALUABLE_VALUE,
    SET_DEEMPHASIS,
    get_valuable_stats,
    is_trash_stat,
    is_trash_stats,
    smart_upgrade_check,
)


# --- is_trash_stat -----------------------------------------------------------
def test_flat_substats_are_trash():
    assert is_trash_stat(1)   # HP flat
    assert is_trash_stat(3)   # ATK flat
    assert is_trash_stat(5)   # DEF flat


def test_nonflat_substats_are_not_trash():
    for prop in (2, 4, 6, 8, 9, 10, 11, 12):
        assert not is_trash_stat(prop)


def test_full_signature_alias():
    # the compiled SWCore.isTrashStats(sets, prop) ignores `sets`
    assert is_trash_stats([], 1) is True
    assert is_trash_stats({6, 2}, 8) is False
    assert is_trash_stats((1,), 5) is True


# --- get_valuable_stats ------------------------------------------------------
def _mk(sec_eff, cls=6, set_id=1, **kw):
    rune = {"class": cls, "set_id": set_id, "sec_eff": [list(s) for s in sec_eff]}
    rune.update(kw)
    return rune


def test_nonlegend_class_never_valuable():
    rune = _mk([[8, 15, 0, 2], [9, 12, 0, 3]], cls=5)
    assert get_valuable_stats(rune) == {}
    for cls in (7, 15, 16):  # ancient-era classes do not register either
        assert get_valuable_stats(_mk([[8, 15, 0, 2]], cls=cls)) == {}


def test_legend_all_hard_substats_valuable():
    rune = _mk([[8, 15, 0, 2], [4, 11, 0, 3], [9, 12, 0, 1], [6, 10, 1, 0]])
    assert get_valuable_stats(rune) == {8: 1, 4: 1, 9: 1, 6: 1}


def test_flats_and_utility_never_valuable():
    rune = _mk([[1, 513, 0, 2], [11, 20, 0, 0], [12, 15, 0, 0], [8, 16, 0, 4]])
    assert get_valuable_stats(rune) == {8: 1}


def test_set_deemphasis_fatal_drops_def_percent():
    rune = _mk([[2, 11, 0, 6], [4, 11, 0, 6], [6, 10, 0, 6], [8, 18, 0, 4],
                [9, 12, 0, 4], [10, 8, 0, 4]], set_id=8)  # Fatal
    assert get_valuable_stats(rune) == {2: 1, 4: 1, 8: 1, 9: 1, 10: 1}


def test_set_deemphasis_guard_drops_atk_percent():
    rune = _mk([[2, 11, 0, 6], [4, 11, 0, 6], [6, 10, 0, 6], [8, 18, 0, 4],
                [9, 12, 0, 4], [10, 8, 0, 4]], set_id=2)  # Guard
    assert get_valuable_stats(rune) == {2: 1, 6: 1, 8: 1, 9: 1, 10: 1}


def test_set_deemphasis_other_sets_keep_all():
    rune = _mk([[2, 11, 0, 6], [4, 11, 0, 6], [6, 10, 0, 6], [8, 18, 0, 4],
                [9, 12, 0, 4], [10, 8, 0, 4]], set_id=13)  # Violent
    assert get_valuable_stats(rune) == {2: 1, 4: 1, 6: 1, 8: 1, 9: 1, 10: 1}


def test_smart_argument_ignored():
    rune = _mk([[8, 15, 0, 2], [9, 12, 0, 3]])
    base = get_valuable_stats(rune, smart=0)
    for smart in (2, 3, 5, 80):
        assert get_valuable_stats(rune, smart=smart) == base


def test_values_always_one():
    rune = _mk([[8, 15, 0, 2], [4, 11, 0, 3], [9, 12, 0, 1], [2, 16, 0, 4]])
    vs = get_valuable_stats(rune)
    assert set(vs.values()) == {1}


# --- smart_upgrade_check -----------------------------------------------------
def test_grown_valuable_stat_above_floor_is_true():
    old = _mk([[8, 15, 0, 2], [9, 10, 0, 3]])
    new = _mk([[8, 22, 0, 3], [9, 10, 0, 3]])  # SPD 15 -> 22 (>= 10 floor)
    assert smart_upgrade_check(old, new, {8: 1, 9: 1}) is True


def test_grown_valuable_below_floor_is_false():
    old = _mk([[8, 5, 0, 0], [9, 10, 0, 3]])
    new = _mk([[8, 9, 0, 1], [9, 10, 0, 3]])  # SPD 5 -> 9 (< 10 floor)
    assert smart_upgrade_check(old, new, {8: 1, 9: 1}) is False


def test_no_valuable_stat_grown_is_none():
    old = _mk([[8, 15, 0, 2], [9, 10, 0, 3]])
    new = _mk([[8, 15, 0, 2], [9, 10, 0, 3]])  # unchanged
    assert smart_upgrade_check(old, new, {8: 1, 9: 1}) is None


def test_speed_upgrade_only_true_only_on_spd_growth():
    old = _mk([[8, 15, 0, 2], [9, 10, 0, 3]])
    spd_grew = _mk([[8, 22, 0, 3], [9, 10, 0, 3]])
    cr_grew = _mk([[8, 15, 0, 2], [9, 16, 0, 4]])
    assert smart_upgrade_check(old, spd_grew, {8: 1, 9: 1}, speed_upgrade_only=True) is True
    # speed-only hunt: CR growth while SPD static is a "failed speed hunt"
    assert smart_upgrade_check(old, cr_grew, {8: 1, 9: 1}, speed_upgrade_only=True) is False


def test_speed_upgrade_only_ignores_non_spd_vstats():
    old = _mk([[8, 15, 0, 2], [9, 10, 0, 3]])
    cr_grew = _mk([[8, 15, 0, 2], [9, 16, 0, 4]])
    # vs has CR but speed-only: CR growth not in the "speed candidate" set
    assert smart_upgrade_check(old, cr_grew, {9: 1}, speed_upgrade_only=True) is False


def test_floor_thresholds_match_recovered_table():
    # SPD/CR floor 10, CD floor 11, %stats floor 13
    assert MIN_VALUABLE_VALUE[8] == 10
    assert MIN_VALUABLE_VALUE[9] == 10
    assert MIN_VALUABLE_VALUE[10] == 11
    for stat in (2, 4, 6):
        assert MIN_VALUABLE_VALUE[stat] == 13


def test_deemphasis_table_sanity():
    assert SET_DEEMPHASIS == {8: 6, 2: 4}
    assert HARD_VALUABLE_IDS == frozenset({2, 4, 6, 8, 9, 10})
