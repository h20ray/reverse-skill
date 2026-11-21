"""AccountProfile — parses the ``HubUserLogin`` snapshot the game client
receives at login (the ``profiles/<wizard_id>.json`` file).

This is the account data AutoSW's bot works from: resources
(``wizard_info``), units (deck building), runes/artifacts (inventory
cleaning), and the server id. Field names are the live wire format
(verified against a real capture, 2026-09-07):

- resources: ``wizard_info.wizard_energy`` / ``wizard_crystal`` /
  ``wizard_mana`` / ``arena_energy``
- runes: ``pri_eff: [type, value]``, ``sec_eff: [[type, value, ...], ...]``,
  ``upgrade_curr`` (level), ``class`` (stars 1-6), ``rank`` (quality,
  5=legend), ``occupied_id`` (equipped unit id or 0)
- units: ``unit_id``, ``unit_level``, ``class`` (stars), ``spd``/``atk``/…,
  ``runes`` (equipped rune ids)

NOTE: captures contain session keys and device tokens. Never commit a raw
capture; use :meth:`AccountProfile.sanitize` before persisting fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

from .constants import EFF_TYPE

SENSITIVE_KEYS = ("session_key", "session_key_node", "reqid", "ts_val")


class AccountProfile:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.wizard_id = data.get("wizard_id")
        self.server_id = data.get("this_server_id")
        self.wizard_info = data.get("wizard_info", {})
        self.units: list[dict] = data.get("unit_list", [])
        self.runes: list[dict] = data.get("runes", [])
        self.artifacts: list[dict] = data.get("artifacts", [])

    # -- loading -----------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "AccountProfile":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_json(cls, text: str) -> "AccountProfile":
        return cls(json.loads(text))

    def sanitize(self) -> dict:
        """Return a copy safe to keep in tests/docs (drops session data)."""
        clean = {k: v for k, v in self.data.items() if k not in SENSITIVE_KEYS}
        acct = dict(clean.get("account_info", {}))
        acct.pop("token", None)
        clean["account_info"] = acct
        return clean

    # -- resources (wire names -> engine names) ------------------------------
    @property
    def energy(self) -> int:
        return int(self.wizard_info.get("wizard_energy", 0))

    @property
    def crystals(self) -> int:
        return int(self.wizard_info.get("wizard_crystal", 0))

    @property
    def mana(self) -> int:
        return int(self.wizard_info.get("wizard_mana", 0))

    @property
    def arena_energy(self) -> int:
        return int(self.wizard_info.get("arena_energy", 0))

    # -- units ---------------------------------------------------------------
    def best_units(self, n: int) -> list[int]:
        """MVP deck picker: highest stars then level then SPD.

        The original uses full deck-building with rune assignment
        (``best_equip``/``_best_six_runes``); that is a later milestone.
        """
        ranked = sorted(self.units,
                        key=lambda u: (u.get("class", 0), u.get("unit_level", 0),
                                       u.get("spd", 0)), reverse=True)
        return [u["unit_id"] for u in ranked[:n]]

    def unit_by_id(self, unit_id: int) -> dict | None:
        return next((u for u in self.units if u.get("unit_id") == unit_id), None)

    # -- inventory -------------------------------------------------------------
    def unequipped_runes(self) -> list[dict]:
        return [r for r in self.runes if not r.get("occupied_id")]

    def unequipped_artifacts(self) -> list[dict]:
        return [a for a in self.artifacts if not a.get("occupied_id")]


def flatten_rune_game(rune: dict) -> dict:
    """Flatten a **live wire-format** rune into the rule-engine map.

    Field names differ from the older synthetic shape: substats live in
    ``sec_eff`` (id, value, ...) using ``EFF_TYPE`` ids, the level is
    ``upgrade_curr``, ``class`` is the star count and ``rank`` the quality.
    """
    names = {eid: spec[0] for eid, spec in EFF_TYPE.items()}
    flat: dict = {
        "rune_id": rune.get("rune_id"),
        "set_id": rune.get("set_id"),
        "class": rune.get("class"),
        "rank": rune.get("rank"),
        "slot_no": rune.get("slot_no"),
        "upgrade_level": rune.get("upgrade_curr", 0),
        "occupied_id": rune.get("occupied_id", 0),
        "sec_eff_map": {},
    }
    pri = rune.get("pri_eff") or [0, 0]
    flat["main_" + names.get(pri[0], str(pri[0]))] = pri[1]
    for eff in rune.get("sec_eff", []) or []:
        eid, value = eff[0], eff[1]
        name = names.get(eid, str(eid))
        flat[name] = flat.get(name, 0) + value
        flat["sec_eff_map"][eid] = value
    return flat
