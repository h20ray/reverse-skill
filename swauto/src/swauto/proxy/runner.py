"""mitmproxy runner for the own-account login capture proxy.

Clean-room counterpart of AutoSW's ``proxy.pyd`` ``MitmRunner`` (which serves a
transparent proxy and prints ``[Mitmproxy] Running on...``). This wraps a
:class:`~swauto.proxy.addon.LoginCaptureAddon` on an mitmproxy ``Master`` and
provides a small CLI driver (``swauto proxy capture``) so an operator can
import the swauto module freely while leaving the heavy mitmproxy dependency
optional.

MITM captures the **operator's own** game client login only; the addon's
whitelist keeps unrelated TLS traffic untouched.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

log = logging.getLogger("swauto.proxy")


def run_capture(listen_host: str = "127.0.0.1", listen_port: int = 8080,
                save_dir: str | Path | None = None, *,
                ca_store: str | Path | None = None) -> None:
    """Run the mitmproxy capture loop (blocking).

    ``save_dir`` defaults to the gitignored ``profiles/`` store; ``ca_store``
    defaults to the same directory (per-install CA persisted there). The game
    client must be told to send its gateway traffic through ``listen_host:
    listen_port`` and to trust the generated root CA.
    """
    from swauto.proxy import ca, profile

    store = Path(save_dir) if save_dir else profile.default_profiles_dir()
    ca_dir = Path(ca_store) if ca_store else store
    # Generate/load the per-install CA before starting so a failure is loud and
    # the operator can install/trust it before the client connects.
    ca_cert_path, _cert_pem, _key_pem = ca.load_or_create_ca(ca_dir)
    log.info("[Setup] per-install CA ready: %s", ca_cert_path)
    log.info("[Setup] point the game client at proxy %s:%s and trust the CA",
             listen_host, listen_port)

    # mitmproxy is an optional extra; import lazily so the pure core (and the
    # rest of swauto) import without it.
    from mitmproxy import options
    from mitmproxy.tools.dump import DumpMaster

    async def _serve() -> None:
        master = DumpMaster(options.Options(
            listen_host=listen_host, listen_port=listen_port,
            mode=["regular"]))
        try:
            from swauto.proxy.addon import LoginCaptureAddon
            master.addons.add(LoginCaptureAddon(store))
            log.info("[Mitmproxy] Running on %s:%s", listen_host, listen_port)
            await master.run()   # async: serves until the proxy exits
        finally:
            master.shutdown()

    asyncio.run(_serve())


def cmd_capture(args) -> int:
    """CLI entry: ``swauto proxy capture``."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_capture(listen_host=args.host, listen_port=args.port,
                save_dir=args.save_dir or None)
    return 0


def add_capture_subcommand(subparsers) -> None:
    """Register the ``proxy capture`` subcommand on a parser's subparsers."""
    p = subparsers.add_parser(
        "proxy", help="run the own-account login capture proxy")
    cap = p.add_subparsers(dest="proxy_cmd", required=True)
    c = cap.add_parser(
        "capture",
        help="MITM the operator's OWN game login and save a session profile")
    c.add_argument("--host", default="127.0.0.1")
    c.add_argument("--port", type=int, default=8080)
    c.add_argument("--save-dir", default="",
                   help="where to save profiles/ (default: gitignored profiles/)")
    c.set_defaults(func=cmd_capture)
