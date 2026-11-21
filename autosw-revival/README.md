# AutoSW Revival

Clean Python workspace for rebuilding the AutoSW codebase, based on the
reverse-engineering case in [`work/autosw/`](../work/autosw/). This folder is
the **canonical home** for the revival docs and all new implementation code.
The `work/autosw/` case directory remains untouched as the audit record
(sample, evidence, reports).

> Language decision: **Python first**. An earlier Rust rebuild (`xstomper/`)
> was removed from the repo to avoid ambiguity; revisit Rust only after the
> Python implementation is stable.

## Layout

| Path | Contents |
|------|----------|
| `docs/` | Revival reference set (moved from the case dir): architecture, crypto/wire protocol, module reference, 180-method SWAPI catalog |
| `src/autoswkit/` | The new implementation package |
| `src/autoswkit/crypto.py` | Packet envelope engine (AES-128-CBC, zero IV, PKCS#7, zlib, auto-detect) — port of the validated `work/autosw/decrypt_tool.py` |
| `src/autoswkit/swapi_catalog.py` | All 180 `SWAPI` method names grouped by category (navigable skeleton; semantics in `docs/04-swapi-reference.md`) |
| `src/autoswkit/cli.py` | `autoswkit` CLI — same flags as the reference decryptor |
| `tests/` | Round-trip + envelope property tests |

## Quickstart

```bash
cd autosw-revival
pip install -e .            # deps: pycryptodome
pytest                      # run tests

autoswkit -a "<base64>"     # auto-detect and decrypt a captured payload
autoswkit -f payload.txt -o out.json
autoswkit -e --text '{"a":1}'                 # encrypt as request envelope
autoswkit -e --response-mode --text '...'     # encrypt as response envelope
```

## MVP bot engine (P1/P2 baseline)

`autoswkit` now contains a runnable offline MVP of the automation engine,
mirroring the original architecture (docs/05, docs/06):

```
engine.TaskManager   <- control.pyd scheduler (FarmThread, quit_event, conflict sets)
api.SWAPI(SWCore)    <- summon.pyd loop layer (loopDungeon, loop_D_HOLE, loopAllTower, ...)
client.SWCore        <- headless client (send() is the only network touchpoint; transport injectable)
score + rules        <- keep/sell decision (port of score.pyd / rules.pyd semantics)
profile.ProfileStore <- profiles/*.json (schema: docs/05 section 2; loader is tolerant of extra fields)
constants + timing   <- recovered IDs, deck sizes, and the exact getTowerTime tables
```

Example — run a profile task list against an injected (offline) transport:

```python
from autoswkit.profile import ProfileStore
from autoswkit.api import SWAPI
from autoswkit.engine import TaskManager
from autoswkit.client import SWCore

session = SWAPI(transport=my_transport, sleeper=time.sleep)
session.rune_rules = [load rulesets from the profile]
session.smart_level = 80

mgr = TaskManager(session)                      # mirrors MainControl
tid = mgr.create_task("dungeon", {              # task_params = UI payload verbatim
    "dungeon_id": 8001, "times": 100, "stage": 1, "units": [...]})
mgr.stop_task(tid)                              # cooperative stop; battle finishes first
```

Run the suite: `pytest` (crypto round-trips + engine end-to-end against a
scripted fake server, no real network, no real sleeps).

## Roadmap

- [x] **P0 — crypto layer**: `autoswkit.crypto` + CLI + tests (ported from the
  case-validated decryptor; round-trip and envelope-property tests).
- [~] **P1 — protocol layer**: MVP done — `SWCore` with injectable
  transport and `send()` dispatcher, `SWAPI` loop layer (`loopDungeon`,
  `loop_D_HOLE`, `loopAllTower`, `loopScenario`, `loopRift`, `loopRaid`),
  task scheduler with conflicts + cooperative stop. Remaining: real login
  flow, full SWAPI wrapper coverage, deck building.
- [~] **P2 — decision logic**: MVP done — `rules.pyd` semantics ported
  (RuleSet/Rule/op_map/flat-map check, verified against the live module),
  smart-level scoring with configurable weights. Remaining: recover exact
  score weights, artifact scoring details.
- [ ] **P3 — scheduler/UI**: task threads with conflict model, then a modern
  UI (the WebView2/Python IPC glue does not need to survive).

## Scope note

This rebuild is an analysis/interop toolkit. Two parts of the original app are
deliberately **not** being re-implemented:

- The live MITM stat-tampering proxy (`proxy.SWAddon` "NO-ATK"): it rewrites
  *other players'* matches and is the main ban vector for accounts (case
  report §9.3), and the associated root-CA trick is a serious security hazard
  (finding F-AUTOSW-01).
- Root-CA installation / WinDivert kernel interception: not needed for offline
  packet analysis, which is what the crypto layer covers.

The docs describe these subsystems for understanding the original sample only.

## Source material

- Case root: [`../work/autosw/`](../work/autosw/) (scope, timeline, evidence, reports)
- Detailed analysis: [`../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md`](../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md)
- Reference decryptor: [`../work/autosw/decrypt_tool.py`](../work/autosw/decrypt_tool.py)
