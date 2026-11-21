"""Configuration loaders: account snapshots, task profiles, rulesets.

Clean-room reimplementation of the documented formats (docs/07 §1–2).
Never commit raw account captures — they contain session keys/tokens;
`AccountSnapshot.sanitize()` produces a shareable copy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SENSITIVE_KEYS = ("session_key", "session_key_node", "reqid", "ts_val")

# Tasks with mutual-exclusion sets (energy consumers vs PVP vs passive).
TASK_CONFLICTS: dict[str, frozenset[str]] = {
    "dungeon": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "dhole": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "raid": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "rift": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "scenario": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "toa": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot", "hoh"}),
    "toah": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "toah", "arena", "gw", "bot", "hoh"}),
    "toahell": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "toahell", "arena", "gw", "bot", "hoh"}),
    "hoh": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot", "hoh"}),
    "arena": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot", "hoh"}),
    "gw": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot", "hoh"}),
    "bot": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot", "hoh"}),
    "dq": frozenset(),
    "inventory_clean": frozenset(),
}
PVP_TASKS = frozenset({"arena", "gw"})


@dataclass
class TaskSpec:
    """One task record; `params` is the exact UI-style payload (docs/05 §4)."""
    name: str
    params: dict = field(default_factory=dict)
    pvp_required: bool = False
    task_id: int | None = None


class AccountSnapshot:
    """A HubUserLogin capture (wizard_info, units, runes, artifacts)."""

    def __init__(self, data: dict) -> None:
        self.data = data
        self.wizard_id = data.get("wizard_id")
        self.server_id = data.get("this_server_id")
        self.wizard_info = data.get("wizard_info", {})
        self.units = data.get("unit_list", [])
        self.runes = data.get("runes", [])
        self.artifacts = data.get("artifacts", [])

    @classmethod
    def load(cls, path: str | Path) -> "AccountSnapshot":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def sanitize(self) -> dict:
        clean = {k: v for k, v in self.data.items() if k not in SENSITIVE_KEYS}
        acct = dict(clean.get("account_info", {}))
        acct.pop("token", None)
        clean["account_info"] = acct
        return clean

    # resources (wire names)
    @property
    def energy(self) -> int:
        return int(self.wizard_info.get("wizard_energy", 0))

    @property
    def crystals(self) -> int:
        return int(self.wizard_info.get("wizard_crystal", 0))

    @property
    def social_points(self) -> int:
        return int(self.wizard_info.get("social_point_current", 0))

    # -- live-session contract (raw capture only; see sanitize()) -------------
    def session_key(self) -> str:
        return str(self.data.get("session_key") or "")

    def session_key_node(self) -> str:
        return str(self.data.get("session_key_node") or "")

    def reqid(self) -> str:
        return str(self.data.get("reqid") or "")

    def account_info(self) -> dict:
        return dict(self.data.get("account_info", {}) or {})

    def session_contract(self) -> dict:
        """The HubUserLogin-response fields needed to establish a live Session.

        Returns only the fields :func:`net.login.parse_login_response` reads
        (wizard_id, this_server_id, session_key, session_key_node, reqid,
        account_info). ``account_info.token`` is dropped (it is not part of the
        request-signing contract and must never leave this snapshot in a
        loggable dict). The remaining tokens are still live secrets — callers
        must not log or persist this dict; ``sanitize()`` remains the shareable
        path.
        """
        acct = self.account_info()
        acct.pop("token", None)
        return {
            "wizard_id": self.wizard_id,
            "this_server_id": self.server_id,
            "session_key": self.session_key(),
            "session_key_node": self.session_key_node(),
            "reqid": self.reqid(),
            "account_info": acct,
        }

    def best_units(self, n: int) -> list[int]:
        """MVP deck picker (stars → level → spd). Full best_equip is pending."""
        ranked = sorted(self.units,
                        key=lambda u: (u.get("class", 0), u.get("unit_level", 0), u.get("spd", 0)),
                        reverse=True)
        return [u["unit_id"] for u in ranked[:n]]

    def locked_rune_ids(self) -> set[int]:
        """Rune ids the player has locked (server ``rune_lock_list``).

        The HubUserLogin response carries ``rune_lock_list`` as entries of the
        form ``{"lock_type": 1, "rune_id": ...}``. A ``lock_type`` of 1 is the
        active player lock — the cleaner must never sell these. The original
        app never reads this field (Phase A3 probe: it is lock-blind and would
        sell a locked rune); surfacing it here is the clean-room corrective.
        Any entry without a recognized ``lock_type`` is ignored so an unknown
        shape degrades to "not locked" rather than blocking a sale.
        """
        locked = set()
        for entry in self.data.get("rune_lock_list", []):
            if not isinstance(entry, dict):
                continue
            if entry.get("lock_type") not in (1, True):
                continue
            rid = entry.get("rune_id")
            if rid is not None:
                locked.add(int(rid))
        return locked

    def locked_artifact_ids(self) -> set[int]:
        """Artifact ids whose ``locked`` field is non-zero.

        Unlike runes (a separate ``rune_lock_list`` top-level field), each
        artifact object carries its own ``locked: 0/1``. Artifacts with a
        non-zero ``locked`` are player-pinned and must not be sold. Implicitly
        filters out any artifact lacking the field (treated as unlocked).
        """
        return {int(a["rid"]) for a in self.artifacts
                if a.get("locked") and a.get("rid") is not None}

    def unequipped_runes(self) -> list[dict]:
        return [r for r in self.runes if not r.get("occupied_id")]

    def unequipped_artifacts(self) -> list[dict]:
        return [a for a in self.artifacts if not a.get("occupied_id")]


class TaskProfile:
    """A named list of tasks (what the original stored in profiles/*.json)."""

    def __init__(self, name: str, tasks: list[dict]) -> None:
        self.name = name
        self.tasks = [TaskSpec(
            name=t.get("task_name") or t.get("task") or "",
            params=t.get("task_params", {}),
            pvp_required=(t.get("task_name") or t.get("task", "")) in PVP_TASKS,
        ) for t in tasks]

    @classmethod
    def load(cls, path: str | Path) -> "TaskProfile":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(d.get("name", Path(path).stem), d.get("tasks", []))
