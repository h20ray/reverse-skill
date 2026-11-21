"""Transport seam: one `send` per command, platform-agnostic.

The Session calls a Transport with (command, payload) and gets a plain dict
back. Implementations:

- :class:`GatewayTransport` — the live gateway. Raw signed POST carrying the
  captured gateway headers; the caller encrypts its own body (VersionFetch and
  Login each control their own envelope). This is the only network path and is
  never enabled implicitly — a live driver must be invoked explicitly.
- :class:`HttpTransport` — envelope-encrypted POST wrapper (legacy; use
  :class:`GatewayTransport` for the recovered header/body contract).
- :class:`ScriptedTransport` — offline testing: maps commands to canned
  responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.request
from typing import Callable, Protocol

from . import crypto

log = logging.getLogger("swauto.net")


class Transport(Protocol):
    def __call__(self, command: str, payload: dict) -> dict: ...


# Game-server → gateway host slug. Recovered from the case analysis report
# (`server_id`: 1=Korea, 2=Global, 3=Europe, 4=Asia, 5=Japan, 6=China — work/
# autosw report line 362) cross-checked against the host strings in summon.pyd
# (strings 6392-6397) and the captured gateway URL for the server_id 4 profile
# (`summonerswar-sea-lb.qpyou.cn`). "us"/"gb" (older docs / oracle live list)
# == "global". Confidence: 4→sea is oracle+capture-confirmed; ids 1/2/3/5/6
# are inferred from the docs + host string set (the oracle latches the captured
# region offline and cannot be forced to emit a non-sea host) — see
# work/autosw/trace/_relogin_fieldrole_outcome.md Q2.
REGION_HOSTS: dict[int, str] = {
    1: "kr",
    2: "global",
    3: "eu",
    4: "sea",
    5: "jp",
    6: "cn",
}
# A HubUserLogin capture carries no server url — the gateway host is resolved
# from the account's server_id. Full endpoint paths (A1 §2): the login endpoint
# and the version_info_c2 fetch share the same host.
GATEWAY_PATH = "/api/gateway_c2.php"
VERSION_PATH = "/api/version_info_c2.php"


def _gateway_host(server_id: int) -> str:
    """Resolve the live gateway host origin for a game-server id.

    Raises ValueError for an unknown server id so a mis-routed account fails
    loudly instead of POSTing to the wrong region.
    """
    slug = REGION_HOSTS.get(int(server_id))
    if slug is None:
        raise ValueError(f"Unknown server_id {server_id!r}; expected one of "
                         f"{sorted(REGION_HOSTS)}")
    return f"https://summonerswar-{slug}-lb.qpyou.cn"


def gateway_url(server_id: int) -> str:
    """Full gateway (login) endpoint for a game-server id."""
    return f"{_gateway_host(server_id)}{GATEWAY_PATH}"


def gateway_version_url(server_id: int) -> str:
    """Full version_info_c2 endpoint for a game-server id."""
    return f"{_gateway_host(server_id)}{VERSION_PATH}"


class HttpTransport:
    """Legacy live gateway transport. Envelope-encrypted POST.

    Retained for backward compatibility with the earlier envelope-shaped
    transport. Prefer :class:`GatewayTransport` for the recovered gateway
    header/body contract.
    """

    def __init__(self, url: str, key_version: int = 2, custom_key: str = "",
                 timeout: float = 15.0) -> None:
        self.url = url
        self.key_version = key_version
        self.custom_key = custom_key
        self.timeout = timeout

    def __call__(self, command: str, payload: dict) -> dict:
        body = json.dumps({"command": command, **payload})
        wire = crypto.encrypt_request(body, self.key_version, self.custom_key)
        req = urllib.request.Request(
            self.url, data=wire.encode(),
            headers={"Content-Type": "text/plain"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            plain = crypto.decrypt_response(resp.read().decode())
        return json.loads(plain)


# Captured gateway request headers (A1 login outcome §2). The server requires
# this exact set when talking to a real gateway endpoint; the clean-room HTTP
# layer reproduces them verbatim so a live POST is header-faithful.
USER_AGENT = "Summoners%20War/6.3.6.63600 CFNetwork/1121.2.2 Darwin/19.3.0"
GATEWAY_CONTENT_TYPE = "application/octet-stream"

# SmonChecker: a 40-hex checksum the client sends with each request. It is the
# ONE live-only unknown of the login leg — its exact algorithm is not documented
# anywhere in the case (the oracle's getChecker is a red herring; the analytics
# strip is a separate channel). The placeholder below reproduces the *header
# shape* (40 hex chars) so the header contract is faithful; the operator must
# verify/override this value before a real session is used. Never guess the
# value silently.
SMON_CHECKER_PLACEHOLDER = "0" * 40


def smon_tm_val(scale: float = 1.0, offset: float = 0.0) -> int:
    """Scaled request timestamp header value.

    The real ``SmonTmVal`` is a monotonic scaled clock (A1 §2) whose exact
    basis is not offline-recoverable; this returns ``int(now*scale + offset)``
    so the header is a plausible int. Callers may pass an exact value.
    """
    return int(time.time() * scale + offset)


# The version_info_c2 request body's ``sec_ver`` field. Captured verbatim from
# the oracle's real fetch_version request (the 4-field version body — see
# work/autosw/trace/_version_request_capture.py). It is a client-build token,
# not a per-call secret, so it is reproduced as a constant rather than rotated.
VERSION_SEC_VER = "Vsn82q2F"


class GatewayTransport:
    """Live gateway transport — raw signed POST with the captured headers.

    Unlike :class:`HttpTransport`, this does **not** encrypt the body itself:
    the caller (VersionFetch / Login) builds its own envelope so the exact
    recovered wire body (e.g. the 4-field version request vs the 8-field login
    envelope) is preserved verbatim. Only the transport + headers are supplied
    here.

    :param url: full gateway endpoint (``gateway_url(server_id)``).
    :param custom_key: AES-128 envelope key, or ``""`` for the production key.
    :param smon_checker: SmonChecker header value; defaults to the placeholder
        (operator must set the real checksum before a live session).
    :param user_agent: User-Agent header; defaults to the captured one.
    """

    def __init__(self, url: str, *, custom_key: str = "",
                 smon_checker: str = SMON_CHECKER_PLACEHOLDER,
                 user_agent: str = USER_AGENT, timeout: float = 15.0,
                 tm_scale: float = 1.0, tm_offset: float = 0.0) -> None:
        self.url = url
        self.custom_key = custom_key
        self.smon_checker = smon_checker
        self.user_agent = user_agent
        self.timeout = timeout
        self.tm_scale = tm_scale
        self.tm_offset = tm_offset

    def headers(self) -> dict:
        return {
            "User-Agent": self.user_agent,
            "Content-Type": GATEWAY_CONTENT_TYPE,
            "SmonTmVal": str(smon_tm_val(self.tm_scale, self.tm_offset)),
            "SmonChecker": self.smon_checker,
            "timeout": "3",
        }

    def post(self, url: str, body: bytes) -> str:
        """POST `body` (already-enveloped bytes) to ``url``; return the raw
        response payload as-is (the caller strips the envelope)."""
        req = urllib.request.Request(url, data=body, headers=self.headers())
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode()

    def __call__(self, command: str, payload: dict) -> dict:
        """Transport-protocol entry point.

        Net-preserving fallback: the version endpoint is aware of the raw body,
        so this builds the same 4-field version body and POSTs it, then tries to
        decrypt the response (zlib envelope). It is primarily a convenience for
        callers that only have a ``Transport``; dedicated drivers
        (:func:`swauto.net.login.LiveVersionFetcher`) use :meth:`post` for full
        control. Raises if the response is not a decryptable JSON envelope.
        """
        body = json.dumps(payload)
        wire = crypto.encrypt_request(body, 2, self.custom_key)
        raw = self.post(self.url, wire.encode())
        plain = crypto.decrypt_response(raw, 2, self.custom_key)
        return json.loads(plain)


class ScriptedTransport:
    """Offline: `responses` maps command -> dict (or callable(payload)->dict)."""

    def __init__(self, responses: dict[str, dict | Callable[[dict], dict]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, command: str, payload: dict) -> dict:
        self.calls.append((command, payload))
        handler = self.responses.get(command, self.responses.get("*"))
        if handler is None:
            raise KeyError(f"No scripted response for command {command!r}")
        if callable(handler):
            return handler({**payload, "command": command})
        return handler
