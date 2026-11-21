"""Keep/sell rule engine — documented semantics (docs/03 §8, docs/05 §5).

Rules evaluate against a flat attribute map with case-sensitive keys and
the six comparison operators. A ruleset keeps a drop when all its
conditions pass; `check_any` keeps when ANY enabled ruleset accepts.
"""

from __future__ import annotations

import operator

OP_MAP = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le,
}


class Rule:
    def __init__(self, key: str | int, op: str, value) -> None:
        if op not in OP_MAP:
            raise ValueError(f"Unknown operator {op!r}")
        self.key, self.op, self.value = key, op, value
        self._fn = OP_MAP[op]

    def check(self, obj: dict) -> bool:
        return bool(self._fn(obj.get(self.key, 0), self.value))

    def to_config_list(self) -> list:
        return [self.key, self.op, self.value]


class RuleSet:
    def __init__(self, name: str, enabled: bool = True, upgrade_level: int | str = 0,
                 rune_sets: list | None = None, rune_classes: list | None = None,
                 main_stats: list | None = None, slots: list | None = None,
                 rules: list | None = None, type: str = "rune", **extra) -> None:
        self.name = name
        self.enabled = bool(enabled)
        self.type = type
        self.min_upgrade_level = int(upgrade_level)
        self.rune_sets = list(rune_sets or [])
        self.rune_classes = list(rune_classes or [])
        self.main_stats = list(main_stats or [])
        self.slots = list(slots or [])
        self.rules = [r if isinstance(r, Rule) else Rule(*r) for r in (rules or [])]
        self.extra = extra

    @classmethod
    def from_payload(cls, payload: dict) -> "RuleSet":
        return cls(
            name=payload.get("name", ""),
            enabled=payload.get("enabled", True),
            upgrade_level=payload.get("upgrade_level", 0),
            rune_sets=payload.get("rune_sets"),
            rune_classes=payload.get("rune_classes"),
            main_stats=payload.get("main_stats"),
            slots=payload.get("slots"),
            rules=payload.get("rules"),
            type=payload.get("type", "rune"),
        )

    def _filters_pass(self, obj: dict) -> bool:
        if self.rune_sets and obj.get("set_id") not in self.rune_sets:
            return False
        if self.rune_classes and obj.get("class") not in self.rune_classes:
            return False
        if self.slots and obj.get("slot_no") not in self.slots:
            return False
        return obj.get("upgrade_level", 0) >= self.min_upgrade_level

    def check(self, obj: dict) -> tuple[bool, dict]:
        if not self.enabled or not self._filters_pass(obj):
            return False, obj
        return all(rule.check(obj) for rule in self.rules), obj

    def to_dict(self) -> dict:
        return {
            "type": self.type, "name": self.name, "enabled": self.enabled,
            "upgrade_level": self.min_upgrade_level,
            "rune_sets": self.rune_sets, "rune_classes": self.rune_classes,
            "main_stats": self.main_stats, "slots": self.slots,
            "rules": [r.to_config_list() for r in self.rules],
        }


def check_any(obj: dict, rulesets: list[RuleSet]) -> bool:
    return any(rs.check(obj)[0] for rs in rulesets)
