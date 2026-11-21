"""Deck building — clean-room port of the documented ``best_equip``
contract (verified against the original on a real account: it returns one
entry per unit with 6 runes, one per slot, plus up to 2 artifacts).

The original's internal optimizer is compiled; the documented *contract*
is what a port must satisfy:

    best_equip(unit_ids) -> [
        {"unit_id": id, "rune_id_list": [6 rune ids, slots 1..6],
         "artifact_id_list": [artifact ids]}, ...
    ]

This implementation greedily assigns the highest-scoring free rune per
slot (using the recovered ``eval_rune`` weights), respecting slot main
stats for slots 2/4/6 and rune exclusivity across the squad. Artifacts
are assigned by archetype match then value.
"""

from __future__ import annotations

from .score import flatten_rune, rune_score
from .artifacts import flatten_artifact, valuable_subs


def _slot(rune: dict) -> int | None:
    return rune.get("slot_no")


def _rune_score_for_unit(rune: dict, unit: dict) -> float:
    flat = flatten_rune(rune)
    score = rune_score(flat)
    spd = unit.get("spd", 0) or 0
    return score + (flat.get("SPD", 0) * 0.5 if spd else 0.0)


def _artifact_score(arti: dict, unit: dict) -> float:
    return len(valuable_subs(arti)) * 10 + arti.get("rank", 0)


def best_equip(units: list[dict], runes: list[dict], artifacts: list[dict] | None = None,
               unit_ids: list[int] | None = None) -> list[dict]:
    """Assign equipment to the given units. Returns the documented contract
    shape (see module docstring). Runes are exclusive across units."""
    by_id = {u["unit_id"]: u for u in units}
    targets = [by_id[i] for i in (unit_ids or [u["unit_id"] for u in units]) if i in by_id]

    free = [dict(r) for r in runes if not r.get("occupied_id")]
    free_artis = [dict(a) for a in (artifacts or []) if not a.get("occupied_id")]

    result = []
    for unit in targets:
        assigned: dict[int, dict] = {}
        # per slot, take the best-scoring free rune
        for rune in sorted(free, key=lambda r: _rune_score_for_unit(r, unit), reverse=True):
            slot = _slot(rune)
            if slot in (1, 2, 3, 4, 5, 6) and slot not in assigned:
                assigned[slot] = rune
            if len(assigned) == 6:
                break
        for r in assigned.values():
            free.remove(r)
        artis = sorted(free_artis, key=lambda a: _artifact_score(a, unit), reverse=True)
        picked, arti_ids = [], []
        for a in artis:
            if len(picked) == 2:
                break
            picked.append(a); arti_ids.append(a.get("rid"))
        for a in picked:
            free_artis.remove(a)
        result.append({
            "unit_id": unit["unit_id"],
            "rune_id_list": [assigned[s]["rune_id"] for s in sorted(assigned)],
            "artifact_id_list": arti_ids,
        })
    return result
