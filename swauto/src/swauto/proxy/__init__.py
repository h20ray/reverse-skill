"""Own-account login capture proxy.

The AutoSW original never authenticates from scratch — it MITMs the real
Summoners War client's login to the Com2uS gateway and saves the captured
``HubUserLogin``/``GetWizardInfo`` response as a profile (B7: ``control.pyd``
``IndexControl``/``ProfileThread`` + ``proxy.pyd`` ``SWAddon``/``MitmRunner``).
This package is the clean-room rebuild of that capture leg:

- ``ca``       — per-install unique root CA (never the shared AutoSW "swfarm"
                 CA — F-AUTOSW-01 is deliberately not reproduced).
- ``intercept``— pure envelope-decode + request/response classification
                 (no mitmproxy import — unit-testable standalone).
- ``addon``    — :mod:`mitmproxy` addon mirroring ``proxy.pyd``'s SWAddon.
- ``runner``   — :mod:`mitmproxy` runner (the ``MitmRunner`` equivalent).
- ``profile``  — save a captured response as ``profiles/<wizard_id>.json`` via
                 :class:`swauto.config.profile.AccountSnapshot`/``sanitize()``.

Boundaries (unchanged from the rest of swauto): this only ever sees the
**operator's own** game client logging in to the operator's own account. It is
a local transparent-TLS capture, not a "Power proxy" for arbitrary traffic.
"""
