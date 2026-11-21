"""Profile store — the ``profiles/*.json`` layout from AutoSW
(docs/05-automation-engine.md §2).

One JSON file per game account. Each holds a list of task records; the
``task_params`` of each record are the exact payload the original UI sends
(docs 05 §4). The loader is tolerant: unknown task names and unknown
fields are preserved, not rejected, so profiles captured from a real
install can be loaded before every field is mapped.
"""

from __future__ import annotations

import json
from pathlib import Path

# Tasks the MVP engine can run, with their conflict sets (energy-consuming
# PVE tasks conflict with each other; PVP with PVP — docs/06 §3).
TASK_CONFLICTS: dict[str, frozenset[str]] = {
    "dungeon": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "dhole": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "raid": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "rift": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "scenario": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "toa": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "arena", "gw", "bot"}),
    "toah": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "toah", "arena", "gw", "bot"}),
    "toahell": frozenset({"dungeon", "dhole", "raid", "rift", "scenario", "toa", "toahell", "arena", "gw", "bot"}),
    "arena": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot"}),
    "gw": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot"}),
    "bot": frozenset({"arena", "gw", "dungeon", "dhole", "raid", "rift", "scenario", "toa", "bot"}),
    "dq": frozenset(),
    "inventory_clean": frozenset(),
}
PVP_TASKS = frozenset({"arena", "gw"})


class Profile:
    def __init__(self, name: str, data: dict, path: Path | None = None) -> None:
        self.name = name
        self.data = data
        self.path = path

    @property
    def tasks(self) -> list[dict]:
        """Task records: dicts with task_name/task_params (+ extra fields)."""
        return list(self.data.get("tasks", []))

    def get(self, key: str, default=None):
        return self.data.get(key, default)


class ProfileStore:
    """Reads/writes ``profiles/*.json`` next to the app (original layout)."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> list[str]:
        return sorted(p.stem for p in self.directory.glob("*.json"))

    def load(self, name: str) -> Profile:
        path = self.directory / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Profile not found: {path}")
        return Profile(name, json.loads(path.read_text(encoding="utf-8")), path)

    def save(self, profile: Profile) -> None:
        path = self.directory / f"{profile.name}.json"
        path.write_text(json.dumps(profile.data, indent=2, ensure_ascii=False), encoding="utf-8")
        profile.path = path
