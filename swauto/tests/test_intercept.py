"""Unit tests for the capture-proxy core (no mitmproxy needed).

Covers the pure envelope-decode + classification logic in
:mod:`swauto.proxy.intercept` and the profile save/load round-trip in
:mod:`swauto.proxy.profile`. These run anywhere — mitmproxy is not required.
"""

from __future__ import annotations

import json

import pytest

from swauto.net import crypto
from swauto.proxy import intercept, profile


def _hub_login_body(wizard_id: int = 7280513, **overrides) -> dict:
    """A realistic full HubUserLogin response body (flat account snapshot)."""
    body = {
        "command": "HubUserLogin",
        "wizard_id": wizard_id,
        "this_server_id": 4,
        "session_key": "sk_test",
        "session_key_node": "skn_test",
        "reqid": "req_123",
        "account_info": {"channel_uid": 131301622, "token": "tok_abc"},
        "wizard_info": {"wizard_energy": 99},
        "unit_list": [],
        "runes": [],
    }
    body.update(overrides)
    return body


# -- classify_plaintext --------------------------------------------------------


def test_classify_hub_login_full_snapshot():
    # A real HubUserLogin snapshot is large (hundreds of units + runes). Our
    # helper deliberately builds a realistic-looking one with enough bulk to
    # exceed the snapshot-size floor (which exists only to reject thin echos).
    body = json.dumps(_hub_login_body(runes=[{"rune_id": i} for i in range(900)]))
    assert len(body) >= intercept._MIN_SNAPSHOT_BYTES
    hit = intercept.classify_plaintext(body, "/api/gateway_c2.php")
    assert hit is not None
    assert hit.kind == "hub_login"
    assert hit.command == "HubUserLogin"
    assert hit.body["wizard_id"] == 7280513


def test_classify_thin_hub_login_ignored():
    # A short HubUserLogin body is an echo/error, not a cacheable snapshot.
    thin = json.dumps({"command": "HubUserLogin", "ret_code": 1006})
    assert intercept.classify_plaintext(thin, "/api/gateway_c2.php") is None


def test_classify_wizard_info():
    body = json.dumps({"command": "GetWizardInfo", "wizard_id": 7280513,
                       "wizard_info": {"wizard_energy": 50}})
    hit = intercept.classify_plaintext(body, "/api/location_c2.php")
    assert hit is not None
    assert hit.kind == "wizard_info"
    assert hit.command == "GetWizardInfo"


def test_classify_wrong_path_ignored():
    body = json.dumps(_hub_login_body())
    # Even a real HubUserLogin is ignored when it is not on a gateway path.
    assert intercept.classify_plaintext(body, "/api/something_else.php") is None


def test_classify_non_envelope_command_ignored():
    body = json.dumps({"command": "GetMonsterList", "unit_list": []})
    assert intercept.classify_plaintext(body, "/api/gateway_c2.php") is None


def test_classify_garbage_ignored():
    assert intercept.classify_plaintext("not json", "/api/gateway_c2.php") is None


# -- decode_response_payload (envelope round-trip) ------------------------------


def test_decode_response_payload_round_trip():
    snap = json.dumps(_hub_login_body())
    wire = crypto.encrypt_response(snap)  # base64(AES(zlib(json)))
    assert intercept.decode_response_payload(wire) == snap


def test_decode_response_payload_rejects_garbage():
    with pytest.raises(ValueError):
        intercept.decode_response_payload("not-an-envelope")


def test_decode_request_payload_parses_plaintext_json():
    assert intercept.decode_request_payload(b'{"command": "x"}') == {"command": "x"}


def test_decode_request_payload_garbage_is_empty():
    assert intercept.decode_request_payload(b"\x00\x01 not json") == {}


# -- path/host target filters ---------------------------------------------------


def test_target_domain_matches_gateway_host():
    assert intercept._is_target("summonerswar-sea-lb.qpyou.cn")
    assert intercept._is_target("summonerswar-global-lb.qpyou.cn")
    assert intercept._is_target("localhost")  # dev
    assert not intercept._is_target("example.com")


def test_path_suffix():
    assert intercept._path_suffix("/api/gateway_c2.php")
    assert intercept._path_suffix("/api/location_c2.php")
    assert not intercept._path_suffix("/api/other.php")


# -- profile save/load round-trip ----------------------------------------------


def test_save_login_response_writes_gitignored_profile(tmp_path):
    body = _hub_login_body(wizard_id=7280513)
    out = profile.save_login_response(body, profiles_dir=tmp_path)
    assert out.name == "7280513.json"
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["session_key"] == "sk_test"
    assert saved["wizard_id"] == 7280513


def test_save_login_response_requires_wizard_id(tmp_path):
    with pytest.raises(ValueError):
        profile.save_login_response({"command": "HubUserLogin"},
                                    profiles_dir=tmp_path)


def test_custom_filename(tmp_path):
    body = _hub_login_body(wizard_id=42)
    out = profile.save_login_response(body, profiles_dir=tmp_path,
                                      filename="fresh.json")
    assert out.name == "fresh.json"


def test_saved_profile_is_sanitizable(tmp_path):
    """The saved raw capture loads as an AccountSnapshot whose sanitize() is
    the only shareable form — secrets stripped."""
    body = _hub_login_body()
    out = profile.save_login_response(body, profiles_dir=tmp_path)
    snap = profile.load_captured_profile(out)
    assert snap.session_key() == "sk_test"
    clean = snap.sanitize()
    assert "session_key" not in clean
    assert clean["account_info"].get("token") is None
    assert clean["wizard_id"] == 7280513
