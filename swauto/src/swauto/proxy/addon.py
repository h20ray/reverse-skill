"""mitmproxy addon for the own-account login capture.

Clean-room counterpart of ``proxy.pyd``'s ``SWAddon`` (a mitmproxy addon whose
``request``/``response`` hooks log ``[SWProxy] Intercepting Login Request...`` /
``[SWProxy] Login Response Captured`` / ``[SWProxy] Account data sent to GUI``).

The addon:

- only inspects ``*gateway_c2.php`` / ``*location_c2.php`` requests on the
  ``qpyou.cn`` gateway hosts (a narrow whitelist — no churn on unrelated TLS);
- on a matching response, strips the zlib+AES envelope via
  :func:`swauto.net.crypto.decrypt_response`, classifies the plaintext, and
  saves a captured ``HubUserLogin``/``GetWizardInfo`` snapshot to the profile
  store through :mod:`swauto.proxy.profile`.

Decoded bodies are live secrets and are never logged. mitmproxy itself is an
optional dependency (``pip install swauto[proxy]``); importing this module is
lazy so the pure core stays importable without the heavy stack.

Hook signature contract: mitmproxy calls addon hooks with (flow) — the flow's
``request``/``response`` carry the bytes. For a request hook we do nothing but
observe; interception of the client's own login is what the transparent proxy
does by design (the game client is the operator's own).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("swauto.proxy")

# Commands that carry a cacheable account snapshot in the response.
SNAPSHOT_COMMANDS = ("HubUserLogin",)


def _try_import_mitmproxy():
    try:
        import mitmproxy  # noqa: F401  (optional extra)
    except ImportError as exc:  # pragma: no cover - exercised only when missing
        raise ImportError(
            "mitmproxy is required for the capture proxy; install with "
            "`pip install swauto[proxy]`"
        ) from exc


class LoginCaptureAddon:
    """mitmproxy addon: capture the operator's own game login.

    Wire one instance per mitmproxy ``master.addons.add(...)``. The addon only
    reacts to the gateway login endpoints; everything else passes through.
    """

    def __init__(self, save_dir=None, *, handler=None) -> None:
        _try_import_mitmproxy()  # fail fast with a clear message if not present
        from swauto.proxy.intercept import should_intercept
        from swauto.proxy.profile import default_profiles_dir, save_login_response
        self._should_intercept = should_intercept
        self._save_login_response = save_login_response
        self._profiles_dir = Path(save_dir) if save_dir else default_profiles_dir()
        # handler(path, kind, body) hook: e.g. wire to a GUI/notifier. Optional.
        self._handler = handler
        log.info("[SWProxy] addon ready; profiles_dir=%s", self._profiles_dir)
        log.info("[SWProxy] addon cwd=%s", os.getcwd())

    # -- mitmproxy hook surface -------------------------------------------------

    def request(self, flow) -> None:
        """Observe (do not modify) an outgoing request.

        Kept for parity with SWAddon.request (the original logs "Intercepting
        Login Request..."). No request body is mutated — this is a passive
        capture.
        """
        if not self._should_intercept(flow):
            return
        host = flow.request.pretty_host
        path = flow.request.path
        if "gateway_c2.php" in path or "location_c2.php" in path:
            log.debug("[SWProxy] Intercepting Login Request (%s%s)", host, path)

    def response(self, flow) -> None:
        """Decode + save a captured login response if it matches.

        Flow is the mitmproxy ``http.HTTPFlow``. The response content bytes are
        the zlib+AES envelope (``gateway_c2.php`` returns ``base64(AES-CBC(zlib(
        json)))``); we unwrap via the shared crypto module.
        """
        if not self._should_intercept(flow):
            return
        try:
            from swauto.proxy.intercept import (
                classify_plaintext, decode_response_payload,
            )
            plain = decode_response_payload(flow.response.get_text())
        except Exception:
            return  # not one of our envelopes — ignore silently
        hit = classify_plaintext(plain, flow.request.path)
        if hit is None:
            return
        target = None
        try:
            target = self._save_login_response(hit.body, plain=hit.plain,
                                               profiles_dir=self._profiles_dir)
            log.info("[SWProxy] Login Response Captured -> %s", target)
            log.info("[SWProxy] write check exists=%s size=%s",
                     target.exists(),
                     target.stat().st_size if target.exists() else -1)
        except ValueError as exc:
            log.warning("[SWProxy] Response had no wizard_id; not saved (%s)", exc)
        except Exception:
            log.exception("[SWProxy] Failed to save login response")
        if self._handler is not None:
            try:
                self._handler(hit.kind, target, hit.body)
            except Exception:  # notifier must never break the flow
                log.exception("capture handler failed")
