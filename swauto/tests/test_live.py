"""Live-gateway path — offline pins for the operator-authorized live leg (A1 §2).

These tests pin the recovered wire/header contract WITHOUT any network:
- the captured gateway header set (User-Agent / octet-stream / SmonTmVal /
  SmonChecker / timeout) that a real live POST must reproduce;
- the version_info_c2 request body — a distinct **4-field** family
  (game_index/proto_ver/channel_uid/sec_ver), recovered verbatim from the
  oracle (work/autosw/trace/_version_request_capture.py);
- the 8-field HubUserLogin envelope;
- LoginClient.fetch_version adopting proto_ver/infocsv from a live fetcher.

The live POST itself (scope: authorized_target_only, operator's own account)
is exercised only by the explicit `swauto live-login` CLI, never here.
"""

import json

from swauto.net import crypto
from swauto.net.transport import (GATEWAY_CONTENT_TYPE,
                                  SMON_CHECKER_PLACEHOLDER, USER_AGENT,
                                  GatewayTransport, VERSION_SEC_VER,
                                  gateway_url, gateway_version_url)
from swauto.net.login import (DEFAULT_GAME_INDEX, DEFAULT_INFOCSV,
                              DEFAULT_PROTO_VER, LiveVersionFetcher,
                              LoginClient, build_login_request,
                              build_version_request)
from swauto.net.transport import ScriptedTransport

# Synthetic (never real) tokens.
SK = "s" * 40
SKN = "n" * 40


class _FakeGateway:
    """Minimal stand-in for GatewayTransport.post(): records the URL/body and
    answers with a server-style envelope (base64(AES(zlib(json))))."""

    def __init__(self, responses: dict):
        self.calls: list[tuple[str, bytes]] = []
        self._responses = responses  # url-suffix -> plaintext dict

    def post(self, url: str, body: bytes) -> str:
        self.calls.append((url, body))
        for key, payload in self._responses.items():
            if key in url:
                wire = crypto.encrypt_response(json.dumps(payload))
                return wire
        raise AssertionError(f"no scripted response for {url}")


def _ver_plain(proto=DEFAULT_PROTO_VER, infocsv=DEFAULT_INFOCSV, ret=0):
    """A real-shaped version_info_c2 response: version_data is a LIST of
    per-topic rows (recovered live 2026-09-07)."""
    return {
        "version_data": [
            {"game_index": DEFAULT_GAME_INDEX, "topic": "ban_appid", "name": "ban_appid",
             "version": "", "cdnroot": "https://summonerswar-fn.qpyou.cn/smon"},
            {"game_index": DEFAULT_GAME_INDEX, "topic": "infocsv", "name": "infocsv",
             "version": infocsv, "cdnroot": "https://summonerswar-fn.qpyou.cn/smon"},
            {"game_index": DEFAULT_GAME_INDEX, "topic": "protocol", "name": "protocol",
             "version": str(proto), "cdnroot": "https://summonerswar-fn.qpyou.cn/smon"},
            {"game_index": DEFAULT_GAME_INDEX, "topic": "text", "name": "text",
             "version": "1.07.61_Zdu2ehyV", "cdnroot": "https://summonerswar-fn.qpyou.cn/smon"},
        ],
        "ret_code": ret,
    }


# -- header contract (A1 §2) --------------------------------------------------

def test_gateway_header_constants_captured():
    """The header set is the exact captured production set (A1 §2)."""
    assert USER_AGENT == ("Summoners%20War/6.3.6.63600 "
                          "CFNetwork/1121.2.2 Darwin/19.3.0")
    assert GATEWAY_CONTENT_TYPE == "application/octet-stream"
    assert len(SMON_CHECKER_PLACEHOLDER) == 40


def test_gateway_transport_headers_are_captured_set():
    t = GatewayTransport("https://x/api/gateway_c2.php")
    h = t.headers()
    assert h["User-Agent"] == USER_AGENT
    assert h["Content-Type"] == GATEWAY_CONTENT_TYPE
    assert h["SmonChecker"] == SMON_CHECKER_PLACEHOLDER
    assert h["timeout"] == "3"
    # SmonTmVal is a scaled int timestamp (present, plausible)
    assert h["SmonTmVal"].isdigit() and int(h["SmonTmVal"]) > 0


def test_gateway_urls_share_host():
    g = gateway_url(4)
    v = gateway_version_url(4)
    assert g == "https://summonerswar-sea-lb.qpyou.cn/api/gateway_c2.php"
    assert v == "https://summonerswar-sea-lb.qpyou.cn/api/version_info_c2.php"


# -- version request: the distinct 4-field family ------------------------------

def test_build_version_request_is_four_field():
    req = build_version_request(DEFAULT_GAME_INDEX)
    assert req == {
        "game_index": DEFAULT_GAME_INDEX,
        "proto_ver": DEFAULT_PROTO_VER,
        "channel_uid": "",
        "sec_ver": VERSION_SEC_VER,
    }
    # captured default channel_uid is 0 on a fresh pre-login fetch
    assert build_version_request(channel_uid=0)["channel_uid"] == 0


def test_build_version_request_distinct_from_login():
    """The version body is a different family from the 8-field HubUserLogin
    envelope — no command / session_key / infocsv / ts_val."""
    ver = build_version_request()
    login = build_login_request(7280513, ts_val=1)
    assert "command" not in ver
    assert "session_key" not in ver and "infocsv" not in ver
    assert "ts_val" not in ver
    assert "command" in login and "wizard_id" in login


# -- version POST round-trip via the live fetcher (fake gateway) ---------------

def test_live_version_fetcher_posts_4field_and_decrypts():
    gate = _FakeGateway({"/api/version_info_c2.php": _ver_plain()})
    fetcher = LiveVersionFetcher(gate, "https://summonerswar-sea-lb.qpyou.cn/api/version_info_c2.php")
    out = fetcher()
    assert gate.calls and "version_info_c2" in gate.calls[0][0]
    # the plaintext request (encrypted then decrypted) is the 4-field body
    wire = gate.calls[0][1]
    plain = crypto.decrypt_request(wire.decode(), 2)
    sent = json.loads(plain)
    assert set(sent) == {"game_index", "proto_ver", "channel_uid", "sec_ver"}
    assert sent["sec_ver"] == VERSION_SEC_VER
    # version_data is a LIST of per-topic rows; version_topics normalises it
    topics = out["version_topics"]
    assert set(topics) >= {"infocsv", "protocol", "text", "ban_appid"}
    assert topics["protocol"]["version"] == str(DEFAULT_PROTO_VER)


def test_login_client_fetch_version_adopts_live_proto_infocsv():
    """A wired live fetcher refreshes LoginClient's proto_ver/infocsv from the
    version response's topic rows (the oracle sets self.protocol/infocsv)."""
    gate = _FakeGateway({"/api/version_info_c2.php": _ver_plain(proto=12200,
                                                                infocsv="4.09.00_Xyz")})
    fetcher = LiveVersionFetcher(gate, "https://host/api/version_info_c2.php")
    client = LoginClient(ScriptedTransport({}), fetch_version=fetcher)
    assert client.proto_ver == DEFAULT_PROTO_VER
    client.fetch_version()
    assert client.proto_ver == 12200
    assert client.infocsv == "4.09.00_Xyz"


# -- HubUserLogin envelope over a live-shaped transport ------------------------

def test_login_request_still_eight_field():
    req = build_login_request(7280513, ts_val=1991346175)
    assert req["command"] == "HubUserLogin"
    assert len(req) == 8


def test_login_client_blocked_returns_none():
    """A refused login (ret_code != 0) yields None, not a SessionState."""
    client = LoginClient(ScriptedTransport(
        {"HubUserLogin": lambda p: {"ret_code": 9001}}))
    assert client.login(7280513, ts_val=1) is None


def test_login_client_login_response_returns_raw_and_state():
    """login_response surfaces the raw snapshot body (docs/07 §1.4) alongside
    the parsed state."""
    captured = {"command": "HubUserLogin", "wizard_id": 7280513,
                "this_server_id": 4, "session_key": SK, "session_key_node": SKN,
                "reqid": "r" * 36, "account_info": {"id": "Jaum1405"}}
    sent = []

    def handler(payload):
        sent.append(payload)
        return captured

    client = LoginClient(ScriptedTransport({"HubUserLogin": handler}))
    resp, state = client.login_response(7280513, ts_val=1)
    assert resp == captured
    assert state.session_key == SK
    assert state.session_key_node == SKN
    assert sent[0]["command"] == "HubUserLogin"
    assert len(sent[0]) == 8
