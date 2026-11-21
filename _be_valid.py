import json, sys
sys.path.insert(0, r'C:/GitHub/reverse-skill/swauto/src')
from swauto.game.equip import best_equip
PROFILE = r'C:/GitHub/reverse-skill/swauto/profile_test/MooN_sanitized.json'
ACCT = json.load(open(PROFILE, encoding='utf-8'))
units, runes, artis = ACCT["unit_list"], ACCT["runes"], ACCT["artifacts"]

# A real dungeon team: pick 7 real units from an actual deck
team_ids = [9245507685, 21399877718, 4183494507, 4881344423, 11493260569, 8031624683]
# resolve to real unit ids present
inv = {u["unit_id"] for u in units}
ids = [t for t in team_ids if t in inv]
print('resolving team on real units:', ids, 'of', team_ids)

res = best_equip(units, runes, artis, unit_ids=ids)
print('swauto best_equip on %d real units:' % len(ids))
ok = True
for e in res:
    nr = len(e['rune_id_list']); na = len(e['artifact_id_list'])
    slots = set()
    for rid in e['rune_id_list']:
        r = next((x for x in runes if x['rune_id']==rid), None)
        if r: slots.add(r['slot_no'])
    print('  unit %s: %d runes slots=%s | %d artis | runes-in-inventory=%s' % (
        e['unit_id'], nr, sorted(slots) if slots else '?', na,
        all(r in {x['rune_id'] for x in runes} for r in e['rune_id_list'])))
# exclusivity
allr = [rid for e in res for rid in e['rune_id_list']]
print('exclusive:', len(set(allr))==len(allr), '| total', len(allr))
