"""Session — the single network touchpoint (clean-room port of the
documented SWCore.send flow).

Mirrors the original behavior (docs/07 §3):
- one command per call,
- resource mirror refreshed from any response carrying wizard_info,
- GetWizardInfo() to sync at loop start.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .login import (DEFAULT_INFOCSV, DEFAULT_PROTO_VER, apply_session,
                    parse_login_response, scaled_ts_val)
from .transport import Transport, gateway_url

log = logging.getLogger("swauto.net")


class Session:
    def __init__(self, transport: Transport,
                 sleeper: Callable[[float], Any] | None = None,
                 rng_seed: int | None = None) -> None:
        import random
        self._transport = transport
        # None -> asyncio.sleep (async-native); pass time.sleep for sync use
        self.sleeper = sleeper
        self.rng = random.Random(rng_seed)
        # resource mirror
        self.energy = 0
        self.crystals = 0
        self.mana = 0
        self.arena_energy = 0
        self.social_points = 0
        # dimension-hole energy is its own pool (recovered schema — A4 §2: the
        # real profile carries dimension_hole_info {energy, energy_max, ...},
        # NOT regular wizard energy).
        self.dimension_hole_energy = 0
        self.wizard: dict = {}
        # request-signing attrs (A1 field-role map). Empty until a session is
        # established (from a HubUserLogin capture) — a bare offline Session
        # sends unsigned bodies exactly as before.
        self.skey = ""
        self.cuid = ""
        self.wizard_id: int | None = None
        self.server_id: int | None = None
        self.session_key = ""
        self.session_key_node = ""
        self.reqid = ""
        self.account_info: dict = {}
        # resolved gateway endpoint for this server (set on establish); a live
        # caller builds HttpTransport(self.server_host) from it.
        self.server_host = ""

    def _apply_wizard(self, wizard: dict) -> None:
        """Refresh the resource mirror from a wizard_info dict (wire keys with
        fallbacks). One source of truth for the wire-key translation — used on
        every send() response and at establish time, so seeded state and live-
        refreshed state never drift."""
        if not wizard:
            return
        self.wizard = wizard
        self.energy = int(wizard.get("wizard_energy", wizard.get("energy", self.energy)))
        self.crystals = int(wizard.get("wizard_crystal", wizard.get("crystals", self.crystals)))
        self.mana = int(wizard.get("wizard_mana", wizard.get("mana", self.mana)))
        self.arena_energy = int(wizard.get("arena_energy", self.arena_energy))
        self.social_points = int(wizard.get("social_point_current",
                                            wizard.get("social_points", self.social_points)))
        # dimension-hole energy is nested under dimension_hole_info (real schema
        # has energy_max, NOT max_energy — recovered, A4 §2).
        dhi = wizard.get("dimension_hole_info") or {}
        if dhi.get("energy") is not None:
            self.dimension_hole_energy = int(dhi["energy"])

    def establish_from_profile(self, snap) -> "Session":
        """Wire this session from an :class:`AccountSnapshot` (a raw HubUserLogin
        capture) so ``send`` signs requests as the established account.

        Reads the capture's session contract (server_id, session keys, reqid,
        account_info) through the snapshot's getters, parses it with the login
        response parser (:func:`net.login.parse_login_response`), and applies
        it via :func:`net.login.apply_session`. Also resolves the server's
        gateway endpoint onto ``server_host`` (via
        :func:`net.transport.gateway_url`) and seeds the resource mirror from
        the capture's ``wizard_info`` so the session is live-ready immediately
        (no zero-report gap before the first live refresh).

        The transport is left untouched — the caller decides live
        (``HttpTransport(session.server_host)``) vs offline replay
        (``ScriptedTransport``). Only the session state changes here.
        """
        state = parse_login_response(snap.session_contract())
        apply_session(state, self)
        if state.server_id is not None:
            self.server_host = gateway_url(state.server_id)
        # Seed the mirror from the capture (no-op when wizard_info is absent).
        self._apply_wizard(getattr(snap, "wizard_info", None) or {})
        return self

    def send(self, command: str, **params) -> dict:
        log.debug("send %s", command)
        body = {"command": command, **params}
        if self.skey and self.cuid:
            # Signed envelope, exactly the post-login body the oracle sends
            # (A1 §1/§3): the 8 login fields overlaid on the command body with
            # a fresh per-send ts_val. Reconciliation probe (field-role): the
            # request layer reads ONLY self.cuid/self.skey for the auth pair —
            # account_info is never consulted, so the account's platform UID
            # (account_info.channel_uid) plays no role in signing. The wire
            # wizard_id tracks the oracle's self.id (the wizard int), which
            # establishment seeds equal to the profile wizard_id; the account
            # display name (account_info.id, e.g. "Jaum1405") is never the wire
            # wizard_id.
            body = {
                "channel_uid": self.cuid,          # self.cuid → channel_uid
                "command": command,
                "infocsv": DEFAULT_INFOCSV,
                "loginextend_refcount": 0,
                "proto_ver": DEFAULT_PROTO_VER,
                "session_key": self.skey,          # self.skey → session_key
                "ts_val": scaled_ts_val(),
                "wizard_id": self.wizard_id or 0,  # == oracle self.id (wizard int)
                **params,                          # command-specific fields
            }
        resp = self._transport(command, body)
        self._apply_wizard(resp.get("wizard_info") or {})
        return resp

    def sync_wizard(self) -> dict:
        return self.send("GetWizardInfo")

    async def sleep(self, seconds: float) -> None:
        """Asynchronous clear-time wait. The injected sleeper may be sync
        (run as-is; call sites still await) or a coroutine function."""
        import asyncio
        if seconds > 0:
            result = self.sleeper(seconds)
            if hasattr(result, "__await__"):
                await result
