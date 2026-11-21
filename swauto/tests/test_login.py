"""Login flow tests — request builder, response parser, session wiring.

The captured HubUserLogin response (profile_test/, gitignored) carries LIVE
session keys, so these tests use SYNTHETIC tokens (a self-consistent pair the
way the A1 probe proved) rather than real ones. The parser/wiring logic is
identical either way.
"""

import json
from pathlib import Path

from swauto.net.login import (
    DEFAULT_GAME_INDEX,
    DEFAULT_INFOCSV,
    DEFAULT_PROTO_VER,
    LoginClient,
    build_login_request,
    parse_login_response,
    apply_session,
)
from swauto.net.transport import ScriptedTransport
from swauto.game.loops import Loops

FIXTURE = Path(__file__).parent / "fixtures" / "account_fixture.json"


def test_build_login_request_is_eight_fields():
    """The login body is the 8-field wire shape recovered by the A1 probe."""
    req = build_login_request(7280513, ts_val=1991346175)
    assert req == {
        "channel_uid": "",
        "command": "HubUserLogin",
        "infocsv": "4.08.41_Zdu2ehyV",
        "loginextend_refcount": 0,
        "proto_ver": 12160,
        "session_key": "",
        "ts_val": 1991346175,
        "wizard_id": 7280513,
    }


def test_build_login_request_relogin_carries_stored_tokens():
    """A relogin passes the stored session_key/channel_uid (self.skey/cuid)."""
    req = build_login_request(7280513,
                              session_key="s" * 40, channel_uid="n" * 40,
                              ts_val=1)
    assert req["session_key"] == "s" * 40
    assert req["channel_uid"] == "n" * 40
    assert req["command"] == "HubUserLogin"


def test_parse_login_response_maps_session_contract():
    """Response session_key/session_key_node -> skey/cuid (self-consistent
    pair — the A1 §4 default mapping)."""
    resp = {
        "command": "HubUserLogin",
        "wizard_id": 7280513,
        "this_server_id": 4,
        "session_key": "s" * 40,
        "session_key_node": "n" * 40,
        "reqid": "d11d63ba-ba37-4b4f-a4ce-058bbbc62ac1",
        "ts_val": 1991346175,
        "tvalue": 1788722722,
        "account_info": {"id": "Jaum1405", "game_index": 2624},
    }
    state = parse_login_response(resp)
    assert state.wizard_id == 7280513
    assert state.server_id == 4
    assert state.session_key == "s" * 40
    assert state.session_key_node == "n" * 40
    assert state.skey == "s" * 40          # default wiring
    assert state.cuid == "n" * 40
    assert state.reqid == "d11d63ba-ba37-4b4f-a4ce-058bbbc62ac1"
    assert state.account_info["id"] == "Jaum1405"


def test_parse_login_response_tolerates_missing_tokens():
    """A sanitized response (no session_key/node) still parses to a valid
    empty-credential state — never raises."""
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    state = parse_login_response(d)
    assert state.wizard_id == 7280513
    assert state.server_id == 4
    assert state.skey == ""                # sanitized -> no creds, no crash
    assert state.cuid == ""
    assert state.account_info == d.get("account_info", {})


def test_apply_session_wires_request_attrs():
    """apply_session populates the exact attrs the request layer signs with
    (A1 field-role map: skey -> session_key wire, cuid -> channel_uid wire)."""
    resp = {
        "wizard_id": 7280513, "this_server_id": 4,
        "session_key": "s" * 40, "session_key_node": "n" * 40,
        "reqid": "r" * 36, "account_info": {"id": "Jaum1405"},
    }
    state = parse_login_response(resp)
    session = Loops(ScriptedTransport({"*": lambda p: {"ret_code": 0}}),
                    sleeper=lambda s: None)
    apply_session(state, session)
    assert session.wizard_id == 7280513
    assert session.server_id == 4
    assert session.skey == "s" * 40
    assert session.cuid == "n" * 40
    assert session.session_key == "s" * 40
    assert session.session_key_node == "n" * 40


def test_login_client_replays_captured_response():
    """LoginClient.login sends the 8-field request and parses the response into
    session state (offline replay against a scripted transport)."""
    captured = {
        "command": "HubUserLogin", "wizard_id": 7280513, "this_server_id": 4,
        "session_key": "s" * 40, "session_key_node": "n" * 40,
        "reqid": "r" * 36, "account_info": {"id": "Jaum1405", "game_index": 2624},
    }
    sent = []

    def handler(payload):
        sent.append(payload)
        return captured

    client = LoginClient(ScriptedTransport({"HubUserLogin": handler}))
    state = client.login(7280513, ts_val=123)
    req = sent[0]
    assert req["command"] == "HubUserLogin"
    assert req["wizard_id"] == 7280513
    assert req["proto_ver"] == DEFAULT_PROTO_VER
    assert req["infocsv"] == DEFAULT_INFOCSV
    assert req["ts_val"] == 123
    assert state.skey == "s" * 40
    assert state.cuid == "n" * 40


def test_login_client_configured_proto_infocsv_and_defaults():
    client = LoginClient(ScriptedTransport({}))
    assert client.proto_ver == DEFAULT_PROTO_VER
    assert client.infocsv == DEFAULT_INFOCSV
    assert DEFAULT_GAME_INDEX == 2623
    # no version fetcher wired -> configured constants stand
    assert client.fetch_version(2624) == {"proto_ver": 12160,
                                          "infocsv": "4.08.41_Zdu2ehyV"}


def test_manual_relogin_reissues_login_with_fresh_ts():
    """manual_relogin runs the version fetch first, then the identical
    8-field login — re-wiring the fresh session contract on the response."""
    captured = {
        "command": "HubUserLogin", "wizard_id": 7280513, "this_server_id": 4,
        "session_key": "s" * 40, "session_key_node": "n" * 40,
        "reqid": "r" * 36,
    }
    sent = []

    def handler(payload):
        sent.append(payload)
        return captured

    fetches = []
    client = LoginClient(ScriptedTransport({"HubUserLogin": handler}),
                         fetch_version=lambda g: fetches.append(g) or
                         {"proto_ver": 12160, "infocsv": "4.08.41_Zdu2ehyV"})
    state = client.manual_relogin(7280513, session_key="old" * 20,
                                  channel_uid="node" * 20, ts_val=99)
    assert fetches == [2623]                      # version fetch ran first
    req = sent[0]
    assert req["command"] == "HubUserLogin"
    assert req["ts_val"] == 99                    # fresh scaled ts
    assert req["session_key"] == "old" * 20       # stored tokens carried
    assert req["channel_uid"] == "node" * 20
    assert state.skey == "s" * 40                 # fresh contract wired


def test_check_login_block_detects_flag_and_ban():
    client = LoginClient(ScriptedTransport({}))
    # normal login is not blocked
    assert client.check_login_block({"ret_code": 0, "wizard_id": 7280513}) is False
    # gateway refusal / explicit flag / ban are all blocked
    assert client.check_login_block({"ret_code": 9001}) is True
    assert client.check_login_block({"login_block": 1}) is True
    assert client.check_login_block({"is_banned": 1}) is True
    # absent ret_code behaves like 0 (unblocked)
    assert client.check_login_block({"wizard_id": 7280513}) is False
