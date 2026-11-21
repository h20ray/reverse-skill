"""Monster ID to Name resolution and Bestiary lookup.

Provides fast O(1) in-memory resolution for all 1,778 Summoners War monsters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


class LeaderSkill(TypedDict, total=False):
    attr: str
    amount: int
    area: str


class MonsterInfo(TypedDict, total=False):
    name: str
    element: str
    family: str
    archetype: str
    speed: int
    icon: str
    skillups: int
    leader: LeaderSkill | None


ELEMENT_MAP: dict[int, str] = {
    1: "Water",
    2: "Fire",
    3: "Wind",
    4: "Light",
    5: "Dark",
}

_MONSTER_DB: dict[int, MonsterInfo] = {}
_ID_TO_NAME: dict[int, str] = {}


def _load_databases() -> None:
    global _MONSTER_DB, _ID_TO_NAME
    if _ID_TO_NAME:
        return

    data_dir = Path(__file__).parent / "data"

    id_name_path = data_dir / "monster_id_to_name.json"
    if id_name_path.exists():
        with open(id_name_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            _ID_TO_NAME = {int(k): v for k, v in raw.items()}

    monsters_path = data_dir / "monsters.json"
    if monsters_path.exists():
        with open(monsters_path, "r", encoding="utf-8") as f:
            raw_meta = json.load(f)
            _MONSTER_DB = {int(k): v for k, v in raw_meta.items()}


def get_monster_name(master_id: int | None) -> str:
    """Resolve monster master ID into human-readable monster name.

    Examples:
        >>> get_monster_name(10712)
        'Perna'
        >>> get_monster_name(10111)
        'Elucia'
        >>> get_monster_name(99999)
        'Monster #99999'
    """
    if master_id is None or master_id == 0:
        return "Unknown"

    _load_databases()
    if master_id in _ID_TO_NAME:
        return _ID_TO_NAME[master_id]

    # Fallback deduction if unknown / newly released ID
    elem_id = master_id % 10
    elem_name = ELEMENT_MAP.get(elem_id, "Unknown")
    return f"{elem_name} Monster #{master_id}"


def get_monster_info(master_id: int | None) -> MonsterInfo:
    """Get complete metadata (element, family, archetype, base speed, etc.) for a monster."""
    if master_id is None or master_id == 0:
        return {
            "name": "Unknown",
            "element": "Unknown",
            "family": "",
            "archetype": "",
            "speed": 100,
            "icon": "",
            "skillups": 0,
            "leader": None,
        }

    _load_databases()
    if master_id in _MONSTER_DB:
        return _MONSTER_DB[master_id]

    elem_id = master_id % 10
    elem_name = ELEMENT_MAP.get(elem_id, "Unknown")
    return {
        "name": f"{elem_name} Monster #{master_id}",
        "element": elem_name,
        "family": "",
        "archetype": "",
        "speed": 100,
        "icon": f"unit_icon_{master_id}.png",
        "skillups": 0,
        "leader": None,
    }
