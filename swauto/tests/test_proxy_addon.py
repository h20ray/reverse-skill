"""Integration test for the mitmproxy addon hook wiring.

Runs only when mitmproxy is installed (the ``[proxy]`` extra). Uses duck-typed
stub flow objects (the addon never touches mitmproxy types directly beyond
``flow.request``/``flow.response``), so the test validates the real hook
sequence — host whitelist → envelope decode → classify → profile save →
notifier — without spinning up a proxy.
"""

from __future__ import annotations

import json

import pytest

mitmproxy = pytest.importorskip("mitmproxy")

from swauto.net import crypto  # noqa: E402
from swauto.proxy import profile  # noqa: E402


class _StubRequest:
    def __init__(self, host: str, path: str) -> None:
        self.pretty_host = host
        self.path = path


class _StubResponse:
    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self) -> str:
        return self._text


class _StubFlow:
    def __init__(self, host: str, path: str, response_text: str) -> None:
        self.request = _StubRequest(host, path)
        self.response = _StubResponse(response_text)


def _hub_login_body() -> dict:
    return {
        "command": "HubUserLogin",
        "wizard_id": 7280513,
        "this_server_id": 4,
        "session_key": "sk_capture",
        "session_key_node": "skn_capture",
        "reqid": "req_capture",
        "account_info": {"token": "tok_capture", "channel_uid": 131301622},
        "runes": [{"rune_id": i} for i in range(900)],  # exceed snapshot floor
    }


def test_addon_captures_login_response(tmp_path):
    from swauto.proxy.addon import LoginCaptureAddon

    seen: list = []

    def handler(kind, target, body):
        seen.append((kind, target, body))

    addon = LoginCaptureAddon(save_dir=tmp_path, handler=handler)

    body = json.dumps(_hub_login_body())
    assert len(body) >= 4096
    wire = crypto.encrypt_response(body)  # base64(AES(zlib(json)))
    flow = _StubFlow("summonerswar-sea-lb.qpyou.cn",
                     "/api/gateway_c2.php", wire)

    addon.response(flow)

    # profile saved under profiles/<wizard_id>.json
    saved = tmp_path / "7280513.json"
    assert saved.exists()
    snap = profile.load_captured_profile(saved)
    assert snap.wizard_id == 7280513
    assert snap.session_key() == "sk_capture"
    # notifier fired with the classified kind
    assert seen and seen[0][0] == "hub_login"
    # and the decoded body handed to the handler is the live snapshot
    assert seen[0][2]["session_key"] == "sk_capture"


def test_addon_ignores_non_target_host(tmp_path):
    from swauto.proxy.addon import LoginCaptureAddon

    addon = LoginCaptureAddon(save_dir=tmp_path)
    body = json.dumps(_hub_login_body())
    wire = crypto.encrypt_response(body)
    # wrong host (not qpyou.cn) → whitelist refuses; nothing saved
    flow = _StubFlow("evil.example.com", "/api/gateway_c2.php", wire)
    addon.response(flow)
    assert not (tmp_path / "7280513.json").exists()


def test_addon_ignores_non_login_path(tmp_path):
    from swauto.proxy.addon import LoginCaptureAddon

    addon = LoginCaptureAddon(save_dir=tmp_path)
    body = json.dumps(_hub_login_body())
    wire = crypto.encrypt_response(body)
    flow = _StubFlow("summonerswar-sea-lb.qpyou.cn",
                     "/api/something_else.php", wire)
    addon.response(flow)
    assert not (tmp_path / "7280513.json").exists()


def test_addon_silently_skips_non_envelope(tmp_path):
    from swauto.proxy.addon import LoginCaptureAddon

    addon = LoginCaptureAddon(save_dir=tmp_path)
    flow = _StubFlow("summonerswar-sea-lb.qpyou.cn",
                     "/api/gateway_c2.php", "not-an-envelope")
    addon.response(flow)  # must not raise
    assert not (tmp_path / "7280513.json").exists()
