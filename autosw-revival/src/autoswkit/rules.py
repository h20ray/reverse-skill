"""Keep/sell rule engine — Python port of ``rules.pyd`` (live-probed API,
see docs/03-module-reference.md §8).

Semantics preserved from the original:

- A ruleset is a named, enabled flag plus filters (rune sets/classes,
  main stats, slots, minimum upgrade level) and a list of
  ``[key, op, value]`` conditions.
- ``check(obj)`` evaluates rules against a **flat attribute map** with
  case-sensitive keys, returning ``(keep, obj)``.
- Operators are the six comparison ops of the original's ``op_map``.
- An empty filter matches everything; a ruleset whose conditions all pass
  keeps the drop.
"""

from __future__ import annotations

import operator

OP_MAP: dict[str, object] = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le,
}


class Rule:
    """One condition: ``key op value`` against the flat map."""

    def __init__(self, key: str | int, op: str, value) -> None:
        if op not in OP_MAP:
            raise ValueError(f"Unknown operator: {op!r} (expected one of {sorted(OP_MAP)})")
        self.key, self.op, self.value = key, op, value
        self._fn = OP_MAP[op]

    def check(self, obj: dict) -> bool:
        return bool(self._fn(obj.get(self.key, 0), self.value))

    def to_config_list(self) -> list:
        return [self.key, self.op, self.value]

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Rule({self.key!r} {self.op} {self.value!r})"


class RuleSet:
    """Keep-ruleset; ``type`` selects rune vs artifact payload fields."""

    _registry: dict[str, type["RuleSet"]] = {}

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
        """Build from the UI/task_params ruleset payload (docs 05 §5)."""
        rules = payload.get("rules") or []
        return cls(
            name=payload.get("name", ""),
            enabled=payload.get("enabled", True),
            upgrade_level=payload.get("upgrade_level", 0),
            rune_sets=payload.get("rune_sets"),
            rune_classes=payload.get("rune_classes"),
            main_stats=payload.get("main_stats"),
            slots=payload.get("slots"),
            rules=rules,
            type=payload.get("type", "rune"),
            **{k: v for k, v in payload.items()
               if k not in {"name", "enabled", "upgrade_level", "rune_sets",
                            "rune_classes", "main_stats", "slots", "rules", "type"}},
        )

    def _filters_pass(self, obj: dict) -> bool:
        if self.rune_sets and obj.get("set_id") not in self.rune_sets:
            return False
        if self.rune_classes and obj.get("class") not in self.rune_classes:
            return False
        if self.main_stats:
            for ms in self.main_stats:
                if obj.get("main_" + str(ms)) is not None or obj.get("main_stat_name") == ms:
                    break
            else:
                return False
        if self.slots and obj.get("slot_no") not in self.slots:
            return False
        return obj.get("upgrade_level", 0) >= self.min_upgrade_level

    def check(self, obj: dict) -> tuple[bool, dict]:
        """``(keep, obj)`` — all conditions must pass; empty rules keep."""
        if not self.enabled:
            return False, obj
        if not self._filters_pass(obj):
            return False, obj
        keep = all(rule.check(obj) for rule in self.rules)
        return keep, obj

    def to_dict(self) -> dict:
        return {
            "type": self.type, "name": self.name, "enabled": self.enabled,
            "upgrade_level": self.min_upgrade_level,
            "rune_sets": self.rune_sets, "rune_classes": self.rune_classes,
            "main_stats": self.main_stats, "slots": self.slots,
            "rules": [r.to_config_list() for r in self.rules],
        }


def check_ruleset(obj: dict, rulesets: list[RuleSet]) -> bool:
    """Keep if ANY enabled ruleset accepts the drop (original semantics)."""
    return any(rs.check(obj)[0] for rs in rulesets)
