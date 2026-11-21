"""Profile → live Session: signed-envelope send + server routing + establish.

These tests drive the established (signed) request path offline. All tokens
are SYNTHETIC (a self-consistent pair, per the A1 §4 default) — the real
profile_test/ captures carry LIVE session keys and are never loaded here.
The signing is conditional on establishment: a bare Session (no skey/cuid)
sends unsigned bodies exactly as before (backward-compat guard).
"""

from swauto.config.profile import AccountSnapshot
from swauto.game.loops import Loops
from swauto.net.login import DEFAULT_INFOCSV, DEFAULT_PROTO_VER
from swauto.net.session import Session
from swauto.net.transport import (REGION_HOSTS, ScriptedTransport, gateway_url)

SK = "s" * 40   # synthetic session_key
SKN = "n" * 40  # synthetic session_key_node


def _snapshot(**over):
    """AccountSnapshot with the live-session contract fields a raw capture has."""
    base = {
        "command": "HubUserLogin",
        "wizard_id": 7280513,
        "this_server_id": 4,
        "session_key": SK,
        "session_key_node": SKN,
        "reqid": "d11d63ba-ba37-4b4f-a4ce-058bbbc62ac1",
        "account_info": {"id": "Jaum1405", "game_index": 2624, "token": "live-token"},
        "wizard_info": {"wizard_energy": 37, "wizard_crystal": 2000,
                        "wizard_mana": 3_000_000, "arena_energy": 2,
                        "social_point_current": 90},
        "unit_list": [],
        "runes": [],
        "artifacts": [],
    }
    base.update(over)
    return AccountSnapshot(base)


def _established(transport=None):
    """A Loops session established from a snapshot's session contract."""
    session = Loops(transport or ScriptedTransport({"*": lambda p: {"ret_code": 0}}),
                    sleeper=lambda s: None)
    session.establish_from_profile(_snapshot())
    return session


# -- backward compatibility ---------------------------------------------------

def test_bare_session_sends_no_envelope():
    """A Session that was never established sends the bare (command, params)
    body — no envelope keys leak into the offline payloads."""
    transport = ScriptedTransport({"GetWizardInfo": {"ret_code": 0}})
    session = Session(transport)
    session.send("GetWizardInfo")
    _, payload = transport.calls[0]
    assert set(payload) == {"command"}
    # signing attrs default empty
    assert session.skey == "" and session.cuid == ""


def test_bare_session_signed_envelope_is_opt_in():
    """Establishing sets skey/cuid; then the envelope is added. This is the
    flip side of the guard above — signing is per-session state."""
    session = _established()
    assert session.skey == SK
    assert session.cuid == SKN


# -- established (signed) envelope -------------------------------------------

def test_established_send_emits_full_envelope():
    """Once established, send overlays the 8-field signed envelope."""
    transport = ScriptedTransport({"GetWizardInfo": {"ret_code": 0, "wizard_info": {"wizard_energy": 30}}})
    session = _established(transport)
    session.send("GetWizardInfo")
    _, payload = transport.calls[0]
    assert payload["command"] == "GetWizardInfo"
    assert payload["channel_uid"] == SKN        # cuid -> channel_uid
    assert payload["session_key"] == SK          # skey -> session_key
    assert payload["infocsv"] == DEFAULT_INFOCSV
    assert payload["proto_ver"] == DEFAULT_PROTO_VER
    assert payload["loginextend_refcount"] == 0
    assert payload["wizard_id"] == 7280513
    assert isinstance(payload["ts_val"], int)


def test_send_ts_val_recomputed_per_call():
    """Each send recomputes ts_val from the clock (A1 §1 per-send scaled
    timestamp). scaled_ts_val() is second-granular, so two rapid sends may
    collide — the invariant is that the value is always present and derives
    from the current time, i.e. non-decreasing across calls."""
    transport = ScriptedTransport({"*": {"ret_code": 0}})
    session = _established(transport)
    session.send("GetWizardInfo")
    t1 = transport.calls[0][1]["ts_val"]
    session.send("GetWizardInfo")
    t2 = transport.calls[1][1]["ts_val"]
    assert isinstance(t1, int) and isinstance(t2, int)
    assert t2 >= t1


def test_signed_send_command_specific_fields_overlay():
    """Command-specific params ride alongside the envelope (not under it)."""
    transport = ScriptedTransport({"UpgradeRune_v2": {"ret_code": 0, "rune": {"rune_id": 42, "upgrade_curr": 10}}})
    session = _established(transport)
    session.send("UpgradeRune_v2", rune_id=42)
    _, payload = transport.calls[0]
    assert payload["rune_id"] == 42             # overlay survives
    assert payload["command"] == "UpgradeRune_v2"
    assert payload["channel_uid"] == SKN
    assert payload["session_key"] == SK


def test_establish_sets_signing_state_and_host():
    """establish_from_profile wires skey/cuid/wizard_id/server_id + server_host."""
    session = _established()
    assert session.wizard_id == 7280513
    assert session.server_id == 4
    assert session.session_key == SK
    assert session.session_key_node == SKN
    assert session.reqid == "d11d63ba-ba37-4b4f-a4ce-058bbbc62ac1"
    assert session.server_host == gateway_url(4)


def test_establish_from_sanitized_contract_degrades():
    """A capture without tokens (sanitized) establishes empty creds without
    raising — signing stays off (skey/cuid empty), so sends are unsigned."""
    snap = _snapshot(session_key="", session_key_node="", account_info={"id": "Jaum1405"})
    session = Loops(ScriptedTransport({"GetWizardInfo": {"ret_code": 0}}),
                    sleeper=lambda s: None)
    session.establish_from_profile(snap)
    assert session.skey == "" and session.cuid == ""
    # signing disabled -> bare body
    session.send("GetWizardInfo")
    _, payload = session._transport.calls[0]
    assert set(payload) == {"command"}


# -- routing -----------------------------------------------------------------

def test_gateway_url_resolves_captured_host():
    """server_id 4 (Asia) routes to the captured summonerswar-sea host."""
    assert gateway_url(4) == "https://summonerswar-sea-lb.qpyou.cn/api/gateway_c2.php"


def test_gateway_url_all_regions():
    assert gateway_url(1) == "https://summonerswar-kr-lb.qpyou.cn/api/gateway_c2.php"
    assert gateway_url(2) == "https://summonerswar-global-lb.qpyou.cn/api/gateway_c2.php"
    assert gateway_url(3) == "https://summonerswar-eu-lb.qpyou.cn/api/gateway_c2.php"
    assert gateway_url(5) == "https://summonerswar-jp-lb.qpyou.cn/api/gateway_c2.php"
    assert gateway_url(6) == "https://summonerswar-cn-lb.qpyou.cn/api/gateway_c2.php"
    assert set(REGION_HOSTS) == {1, 2, 3, 4, 5, 6}


def test_gateway_url_unknown_server_raises():
    import pytest
    with pytest.raises(ValueError):
        gateway_url(99)


# -- parser <-> signer integration -------------------------------------------

def test_establish_roundtrip_parser_to_signer():
    """A captured HubUserLogin response parsed by parse_login_response and
    applied to a Session yields a signed envelope matching the parser output."""
    from swauto.net.login import apply_session, parse_login_response
    captured = {
        "command": "HubUserLogin", "wizard_id": 7280513, "this_server_id": 4,
        "session_key": SK, "session_key_node": SKN, "reqid": "r" * 36,
        "account_info": {"id": "Jaum1405"},
    }
    state = parse_login_response(captured)
    transport = ScriptedTransport({"GetWizardInfo": {"ret_code": 0}})
    session = Loops(transport, sleeper=lambda s: None)
    apply_session(state, session)
    session.send("GetWizardInfo")
    _, payload = transport.calls[0]
    assert payload["channel_uid"] == state.cuid
    assert payload["session_key"] == state.skey
    assert payload["wizard_id"] == state.wizard_id


# -- no-leak invariant -------------------------------------------------------

def test_session_contract_carries_only_contract_fields():
    """session_contract() returns the parser's read fields, never extra secrets
    and never the full raw capture (account_info.token stays out)."""
    contract = _snapshot().session_contract()
    assert set(contract) == {"wizard_id", "this_server_id", "session_key",
                             "session_key_node", "reqid", "account_info"}
    assert contract["wizard_id"] == 7280513
    assert contract["this_server_id"] == 4
    assert "token" not in contract["account_info"]


def test_sanitize_still_drops_tokens_after_getters_added():
    """sanitize() remains the shareable path — the new getters do not weaken it."""
    clean = _snapshot().sanitize()
    for key in ("session_key", "session_key_node", "reqid", "ts_val"):
        assert key not in clean
    assert "token" not in clean["account_info"]


# -- establish-time resource-mirror seeding ----------------------------------

def test_establish_seeds_resource_mirror():
    """establish_from_profile seeds the mirror from the capture's wizard_info,
    so a live-ready session doesn't report zero resources before a refresh."""
    session = _established()
    assert session.energy == 37
    assert session.crystals == 2000
    assert session.mana == 3_000_000
    assert session.arena_energy == 2
    assert session.social_points == 90
    assert session.wizard == _snapshot().wizard_info


def test_establish_seeds_fallback_wire_names():
    """Bare wire names (energy/crystals/social_points) seed the same attrs —
    parity with the live send() refresh translation."""
    snap = _snapshot(wizard_info={"energy": 5, "crystals": 60,
                                  "social_points": 7, "mana": 1,
                                  "arena_energy": 1})
    session = Loops(ScriptedTransport({"*": {"ret_code": 0}}), sleeper=lambda s: None)
    session.establish_from_profile(snap)
    assert session.energy == 5
    assert session.crystals == 60
    assert session.social_points == 7


def test_establish_without_wizard_info_degrades():
    """A capture with no wizard_info keeps the mirror at defaults, never raises."""
    snap = _snapshot(wizard_info=None)
    session = Loops(ScriptedTransport({"*": {"ret_code": 0}}), sleeper=lambda s: None)
    session.establish_from_profile(snap)
    assert session.energy == 0
    assert session.crystals == 0
    assert session.wizard == {}
    # signing still wired
    assert session.skey == SK and session.cuid == SKN


def test_live_ready_composition_seeds_mirror_and_counts():
    """establish_from_profile + from_snapshot together make a live-ready bot:
    identity/signing/mirror from establish, locks+counts from the snapshot."""
    snap = _snapshot(runes=[{"rune_id": 1}, {"rune_id": 2}],
                     artifacts=[{"rid": 10}],
                     rune_lock_list=[{"lock_type": 1, "rune_id": 1}])
    bot = Loops(ScriptedTransport({"*": {"ret_code": 0}}), sleeper=lambda s: None)
    bot.establish_from_profile(snap)
    bot.from_snapshot(snap)
    # mirror from establish
    assert bot.energy == 37
    assert bot.skey == SK and bot.cuid == SKN
    # counts + locks from from_snapshot
    assert bot.rune_count == 2
    assert bot.artifact_count == 1
    assert bot.locked_rune_ids == {1}


def test_establish_seed_parity_with_live_refresh():
    """Seeding and a live GetWizardInfo round-trip produce identical mirror
    state (same _apply_wizard translation) — no drift between the two paths."""
    snap = _snapshot()
    seeded = Loops(ScriptedTransport({"*": {"ret_code": 0}}), sleeper=lambda s: None)
    seeded.establish_from_profile(snap)

    refreshed = Loops(ScriptedTransport({"*": {"ret_code": 0}}), sleeper=lambda s: None)
    refreshed._apply_wizard(snap.wizard_info)   # what a live response would do

    for attr in ("energy", "crystals", "mana", "arena_energy", "social_points", "wizard"):
        assert getattr(seeded, attr) == getattr(refreshed, attr)
