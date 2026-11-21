"""Envelope decode + request/response classification for the capture proxy.

AutoSW's SWAddon means this specific text:

```text
[SWProxy] Intercepting Login Request...
[SWProxy] Login Response Captured
[SWProxy] Account data sent to GUI
```

This module isolates that logic from mitmproxy so it is pure and unit-testable
without the (heavy) mitmproxy + cryptography stack: it takes bytes of a request
body / response payload and returns a typed outcome (``LoginRequest``,
``LoginResponse``, ``WizardRequest``, ``WizardResponse``, ``Ignored``).

The target set is deliberately narrow and mirrors the evidence in
``work/autosw/strings/proxy.pyd.strings.txt``: only the two login-envelope
commands -- ``HubUserLogin`` and ``GetWizardInfo`` -- on the ``qpyou.cn``
gateway hosts (``gateway_c2.php`` / ``location_c2.php``). Everything else is
ignored.

Only the **envelope** is stripped here. The decrypted plaintext still grants a
live session (``session_key``/``session_key_node``/``reqid``) and the full
account snapshot — it is a live secret. Callers must route decoded bodies to
:mod:`swauto.proxy.profile` (which sanitises before anything leaves the machine)
and must never log them. See the memory note ``autosw-never-on-git``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from swauto.net import crypto

log = logging.getLogger("swauto.proxy")

# Target hosts are the Com2uS gateway load balancers (the SEA profile is
# server_id 4 → "sea"; capture target set is host-agnostic over the qpyou.cn
# zone so tunnel/TLS interception works across regions).
_TARGET_DOMAIN = "qpyou.cn"
_LOGIN_PATH_SUFFIX = "gateway_c2.php"
_WIZARD_PATH_SUFFIX = "location_c2.php"

# Commands carried by the encrypted envelope (proxy.pyd strings: HubUserLogin,
# GetWizardInfo).
CMD_HUB_LOGIN = "HubUserLogin"
CMD_WIZARD_INFO = "GetWizardInfo"

# A full HubUserLogin body is a huge flat account snapshot (wizard_id, units,
# runes...). Requiring BOTH this non-trivial size AND the login command keeps
# classification robust against a thin error body.
_MIN_SNAPSHOT_BYTES = 4096


@dataclass(frozen=True)
class Intercept:
    """A decoded and classified login-envelope body."""
    kind: str            # "hub_login" | "wizard_info"
    command: str
    body: dict           # decrypted plaintext parsed (LIVE secret — handle via sanitize)
    plain: str           # decrypted plaintext verbatim (already-valid JSON; write this, not a re-serialized dict)
    path: str
    host: str = ""


# -- plaintext classification (no envelope dependency) -------------------------


def _path_suffix(path: str) -> bool:
    return path.endswith(_LOGIN_PATH_SUFFIX) or path.endswith(_WIZARD_PATH_SUFFIX)


def _loads(text: str) -> dict:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return {}


def classify_plaintext(plain: str, path: str) -> Intercept | None:
    """Classify an already-decrypted body string against the target set.

    Returns ``None`` for anything not on the login/wizard envelopes. The
    returned ``Intercept.body`` is the full decoded snapshot — a live secret.
    """
    if not _path_suffix(path):
        return None
    body = _loads(plain)
    command = body.get("command", "")

    if command == CMD_HUB_LOGIN and len(plain) >= _MIN_SNAPSHOT_BYTES:
        return Intercept(kind="hub_login", command=CMD_HUB_LOGIN,
                         body=body, plain=plain, path=path)
    if command == CMD_HUB_LOGIN and len(plain) < _MIN_SNAPSHOT_BYTES:
        # A thin HubUserLogin body is the request envelope echoing back, or a
        # short error — not the account snapshot we cache.
        return None
    if command == CMD_WIZARD_INFO:
        return Intercept(kind="wizard_info", command=CMD_WIZARD_INFO,
                         body=body, plain=plain, path=path)
    return None


# -- request / response decode helpers -----------------------------------------


def decode_response_payload(payload: str) -> str:
    """Strip the zlib+AES envelope from a response payload string."""
    try:
        return crypto.decrypt_response(payload)
    except Exception:
        raise ValueError("response is not a valid envelope") from None


def decode_request_payload(raw: bytes) -> dict:
    """Best-effort JSON of the (uncompressed) request body.

    Requests are plaintext JSON through the proxy; if it is an envelope blob we
    still return an empty dict rather than classify a login we cannot verify.
    """
    text = raw.decode("utf-8", "replace").lstrip("﻿")
    return _loads(text)


def should_intercept(flow) -> bool:
    """Whitelist target hosts to avoid churn on unrelated TLS."""
    return _is_target(flow.request.pretty_host)


def _is_target(host: str) -> bool:
    return (bool(host) and host.endswith(_TARGET_DOMAIN)) or _is_localhost(host)


def _is_localhost(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0")