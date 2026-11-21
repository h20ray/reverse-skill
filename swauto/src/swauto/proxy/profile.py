"""Save a captured login response as a session profile.

Clean-room counterpart of AutoSW's ``control.pyd`` ``ProfileThread``, which
writes the captured ``login_response`` to ``profiles/<name>.json`` (the B7
evidence: the 4.5 MB ``7280513.json`` is exactly such a captured response). The
saved file is a raw account snapshot, so it is a **live secret**: only ever
write it under the configured (gitignored) profiles dir, and only expose
``AccountSnapshot.sanitize()`` output anywhere shareable.

Naming mirrors the original: the profile is stored as ``<wizard_id>.json``
under ``profiles/`` (the operator's account wizard 7280513 → ``7280513.json``).
"""

from __future__ import annotations

import logging
from pathlib import Path

from swauto.config.profile import AccountSnapshot

log = logging.getLogger("swauto.proxy")

PROFILES_DIR_NAME = "profiles"


def default_profiles_dir() -> Path:
    """The gitignored profile store for this project (created on demand)."""
    return Path(__file__).resolve().parents[3] / PROFILES_DIR_NAME


def _wizard_id(body: dict) -> int | None:
    wid = body.get("wizard_id")
    try:
        return int(wid)
    except (TypeError, ValueError):
        return None


def save_login_response(body: dict, *, profiles_dir: str | Path | None = None,
                        filename: str | None = None,
                        plain: str | None = None) -> Path:
    """Write a captured HubUserLogin response to ``profiles/<wizard_id>.json``.

    ``body`` is the full decoded account snapshot (live secret). ``plain`` is
    the **verbatim decoded plaintext** — the exact already-valid JSON string
    from the wire. When ``plain`` is given it is written as-is (round-tripping
    a 100KB+ snapshot through ``json.dumps`` can fail on non-UTF8/surrogate or
    exotic values that the wire already serialised fine). Otherwise the body is
    re-serialised. The file is a live secret — only :meth:`AccountSnapshot.sanitize`
    output is shareable. Returns the path written. Raises ``ValueError`` when
    the body carries no usable ``wizard_id``.
    """
    wid = _wizard_id(body)
    if wid is None:
        raise ValueError("captured login response has no wizard_id")
    directory = Path(profiles_dir) if profiles_dir else default_profiles_dir()
    directory.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = f"{wid}.json"
    # Never clobber a different account's profile silently.
    target = (directory / filename).resolve()
    log.info("[SWProxy] Login Response Captured -> %s", target)
    if plain is not None:
        target.write_text(plain, encoding="utf-8")
    else:
        target.write_text(_json_dumps(body), encoding="utf-8")
    log.info("[SWProxy] Account data sent to GUI (profile %s)", wid)
    return target


def _json_dumps(body: dict) -> str:
    import json
    return json.dumps(body, ensure_ascii=False, indent=1)


def load_captured_profile(path: str | Path) -> AccountSnapshot:
    """Load a saved capture back as an account snapshot (sanitizable)."""
    return AccountSnapshot.load(path)
