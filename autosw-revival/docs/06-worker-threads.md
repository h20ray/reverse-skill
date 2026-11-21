# AutoSW — Worker Threads: How They Work (DThread, AThread, …)

Companion to `05-automation-engine.md` (which covers profiles, task payloads,
and the battle-loop template). This doc zooms into **the thread layer in
`control.pyd`**: how a task thread is born, what it holds, how it runs, how it
is stopped, and how it talks to the game client in `summon.pyd`.

Evidence: string layout of `control.pyd` and `summon.pyd` (Cython emits every
attribute name and string constant, in code order — see
`work/autosw/strings/*.strings.txt`), plus the frontend contract in
`work/autosw/main.beautified.js`.

---

## 1. The design in one picture

AutoSW's automation is a **two-layer** system:

```
control.pyd                              summon.pyd
┌──────────────────────────────┐         ┌──────────────────────────────────┐
│ MainControl                  │         │ SWAPI / SWCore (one per account) │
│  tasks: {task_id: thread}    │         │                                  │
│  task_params / task_status   │         │  loopDungeon()      ← loop layer │
│  task_conflict sets          │  calls  │    └─ DoDungeon()   ← one battle │
│  create_task / start_task    │ ──────► │    └─ smart_refill()             │
│  stop_task / stop_all        │         │  loopArena(), loopRaid(), ...    │
│                              │         │  DoArena(), DoTower(), ...       │
│ FarmThread (threading.Thread)│         │                                  │
│  ├─ DThread   → loopDungeon  │         │  SWAPI.send(): encrypt → POST    │
│  ├─ AThread   → loopArena    │         │    gateway_c2.php → decrypt      │
│  ├─ DHThread  → loop_D_HOLE  │         │  responses / no_responses queue  │
│  └─ ... (one per task type)   │         └──────────────────────────────────┘
└──────────────────────────────┘
```

- **Thread layer** (`control.pyd`): owns *configuration* (the params the UI
  passed), *state* (running/stopped), and *cancellation* (a stop event). It
  knows nothing about the game protocol.
- **Loop layer** (`summon.pyd`): `loop*` functions run the actual N-times
  battle cycle, calling a `Do*` function once per iteration, and checking the
  stop flag between iterations.
- **Unit layer** (`summon.pyd`): each `Do*` function is exactly one battle
  (start RPC → simulated wait → result RPC → drop evaluation → sell).

This split is why the task table in the UI can start/stop/inspect any task
uniformly: every thread looks identical from the outside.

---

## 2. Anatomy of a task thread

### 2.1 `__init__` — the params become attributes

`create_task` instantiates the right `FarmThread` subclass with the payload
from the UI. The thread's `__init__` stores everything as plain attributes —
every one of these names appears as a string in `control.pyd`:

| Attribute | Set for | Meaning |
|---|---|---|
| `dungeon` / `dhole` | D/DH/B | selected dungeon or 2A dungeon id |
| `farm_times` | all farming threads | loop count (frontend default `99999`) |
| `rune_options` | D/DH/raid/rift/bot | the rune-keep object `{all, keep, smart, speed_required, …}` |
| `spacial` *(sic)* | dhole/raid/rift/bot | the special gem-keep object (typo is in the original code) |
| `energy` / `crystals` / `arena_energy` / `wizard_energy` | most | live resource counters mirrored from server responses |
| `running` | all | boolean mirrored into `task_status` |
| `quit_event` | all | `threading.Event` — the stop flag |

`quit_event` + `Event` + `is_set` all appear in `control.pyd`: **stopping a
task is cooperative** — `stop_task` sets the event, and the loop checks it
between battles. Threads are never killed mid-battle; the in-flight battle
always completes and its result is submitted.

### 2.2 `run()` — one call, nothing else

Every thread's `run()` is the same three-step shape:

```python
# reconstructed shape (DThread)
def run(self):
    try:
        self.running = True
        swapi = ...                      # get the account's SWCore session
        swapi.loopDungeon(self.dungeon, self.farm_times,
                          self.rune_options, self.spacial, ...)
    except Exception:
        log.error("Dungeon error in %s", ...)
    finally:
        self.running = False             # task_status -> "Stopped"
        log.info("Dungeon farming stopped")
```

Log-line evidence for each thread's exit path: "Dungeon farming stopped",
"Arena farming stopped", "Dimension hole farming stopped", "Raid farming
stopped", "Rift farming stopped", "Guild rival farming stopped", "HOH farming
stopped", "Inventory cleaner stopped", "TOA/H stopped", "TOAHell stopped",
"Bot stopped". Matching per-domain error lines ("Dimension hole error in ",
"Arena error ") show the try/except wraps exactly the loop call.

So **the thread does not loop — the `loop*` function in `summon.pyd` does.**
The thread only supplies parameters, resource state, and the stop flag.

### 2.3 The thread ↔ SWCore call chain

`summon.pyd` is organized in three named layers (all visible in its string
table), split across two classes: the `loop*`/`Do*`/helper orchestration lives
on **`summon.SWAPI`** (28 methods), while the RPC wrappers, login, deck
building, and drop evaluation live on **`summon.SWCore`** (~128 methods):

```
control.DThread.run
  → summon.SWAPI.loopDungeon          # counted loop, owns stop/energy checks
      → summon.SWAPI.DoDungeon        # one battle: Start → wait → Result → drops
          → handle_rune / handle_artifact
          → sellRune / SellArtifacts
      → summon.SWAPI.smart_refill     # energy low? buy with crystals / social pts
      (repeat until loop_times exhausted or quit_event set)
```

Loop entry points on `summon.SWAPI`: `loopDungeon`, `loop_D_HOLE`, `loopTower`,
`loopAllTower`, `loopAllTOA`, `loopTOAHell`, `loopArena`, `loopRaid`,
`loopRift`, `loopScenario`, `loopGuildwar`, `loopGuildRival`, `loopSiege`,
`loopHOH`, `loopInstance`, `loopEventInstance`, `loopallunskill`,
`inventory_clean`. Single-battle units: `DoDungeon`, `DoDHole`, `DoTower`,
`DoScenario`, `DoRift`, `DoMaze`, `DoArena`.

Two helpers stand out:

- **`farm_deter`** — the "what do I farm next" decider used by loops without an
  explicit target (scenario fodder leveling picks the stage; arena picks the
  opponent from `GetArenaWizardList`).
- **`smart_refill`** — the energy policy: when `energy` is below the cost of
  the next run, buy energy with crystals (`buyShopItem`) or social points;
  aborts the loop when neither is possible ("Cannot refresh energy!").

`loopHOH` / `get_HOH_current` implement the Hall-of-Heroes special case —
the 10-run cap applied in the frontend plus querying the current HOH entry.

---

## 3. The task registry (MainControl)

`MainControl` keeps the authoritative task state in parallel dicts — the four
strings `task_id`, `task_params`, `task_status`, `task_conflict` appear as
sibling attributes:

```python
tasks = {}          # task_id -> thread instance (the only place threads live)
task_params = {}    # task_id -> original UI payload (verbatim, for status display)
task_status = {}    # task_id -> "Running" | "Stopped"
task_conflict = {}  # task_id -> conflict set for the task type
```

- **`create_task(thread_cls, params...)`** — evidence `Type[FarmThread]`:
  takes the *class* plus params, allocates a fresh `task_id`, registers it,
  starts the thread, returns the id (this is what the SPA stores in its table
  row via `add_task`).
- **`start_task(id)`** — re-arms a stopped task row (restarts the loop);
  refuses if the task type needs PVP subscription and it's disabled
  ("PVP mode required").
- **Conflict gate** — before starting, `task_conflict` sets are intersected
  with running tasks' sets; a hit returns "Task conflict". Energy-consuming
  PVE tasks all conflict with each other; PVP tasks conflict with each other;
  non-energy tasks (daily quests, inventory clean) don't.
- **`stop_task(id)` / `stop_all`** — set the thread's `quit_event`; the status
  flips to Stopped when `run()` exits.
- **`remove_task(id)` / `remove_all`** — unregister (UI error strings: "Task
  not found", "Task params not found", "Remove task success").
- The **SPA polls `task_status(id)` every 3 s** and renders the row's status
  and end time — the backend pushes nothing; it is a pure pull model.

---

## 4. Thread ↔ thread coordination

- **Response correlation:** `summon.pyd` keeps `responses` / `no_responses`
  and `control.pyd` imports `Queue` — each request/response exchange is
  correlated through a queue so concurrent task threads sharing one account
  session don't cross wires. The login request object is held on the session
  (`login_rq`), and one SWCore instance serves the task threads that are
  actually running (conflicts guarantee at most one energy consumer, but
  daily-quest style tasks can coexist with them).
- **Logging is centralized:** threads don't print; they go through the
  `logging` `Handler` (`LogHandler.emit` in control.pyd) into
  `logs\General.log` (`%(asctime)s [%(levelname)s] %(message)s`), which is
  **rotated by archiving** — `7za.exe a -y -- logs\general.…` (7-Zip archive
  of the old log). This is why the shipped `General.log` in the sample is 0
  bytes: it was archived/emptied before installation was captured.
- **Die-with-parent:** the whole process sits in a Windows Job Object
  (`assign_process_to_job_object`, common.pyd) — killing the UI kills all
  task threads.

---

## 5. Worked example — one full DThread life

1. UI: user picks Giant B10, smart level 80, farm 100 runs →
   `MainControl.dungeon("giant", false, 100, {all:true, keep:[], smart:80}, {...})`.
2. `create_task` allocates task_id 7, constructs `DThread(dungeon="giant",
   farm_times=100, rune_options=…, quit_event=Event())`, registers in
   `tasks`, starts it, returns 7. SPA row appears: start time stamped.
3. `DThread.run` → `SWAPI.loopDungeon("giant", 100, …)`.
4. Each iteration: check `quit_event.is_set()` → check energy →
   `DoDungeon` → `BattleDungeonStart` (drops known immediately) → sleep
   simulated clear time → `BattleDungeonResult_V2` → `handle_rune`
   (score vs smart level / rulesets → keep or `sellRune`) → decrement
   `loop_times`.
5. Energy empty mid-loop → `smart_refill` buys crystals; if impossible → log
   "Cannot refresh energy!" → loop exits early.
6. User clicks stop → `stop_task(7)` sets `quit_event` → current battle
   finishes and result is submitted → loop sees flag → returns →
   `run()` finally logs "Dungeon farming stopped", status "Stopped".
   UI row updates on the next 3 s poll.
7. User clicks remove → `remove_task(7)` → thread object dropped.

---

## 6. Porting notes (macOS / Rust / Bun)

The thread layer maps almost 1:1 to modern async runtimes:

| AutoSW construct | Python here | Rust/Bun equivalent |
|---|---|---|
| `FarmThread` subclass | `threading.Thread` + attrs | a task struct (params + `CancellationToken`) spawned per job |
| `quit_event` | `threading.Event` | `tokio_util::sync::CancellationToken` / `AbortSignal` |
| `loop*` functions | blocking loop with `sleep` | async loop with `tokio::time::sleep` / `setTimeout` |
| `responses` Queue | `queue.Queue` | `mpsc` channel / per-session request map |
| `tasks`/`task_status` dicts | plain dicts behind GIL | `Arc<Mutex<HashMap<u64, TaskHandle>>>` |
| 3 s UI poll | SPA `setInterval` | keep as-is (works unchanged over any IPC bridge) |

Key behaviors worth preserving (they're the non-obvious ones):

1. **Cooperative stop only** — never cancel mid-battle; finish and submit the
   result, *then* check the flag (the server-side anti-cheat makes this
   behaviorally required, not just polite).
2. **Conflict sets, not a queue** — starting a conflicting task is rejected
   outright with a user-visible error.
3. **`task_params` stored verbatim** — status display and restart reuse the
   exact original payload.
4. **Per-domain exit log lines** — cheap, but they're how users debug the bot;
   keep the naming convention (`"<Domain> farming stopped"`).

---

## 6.1 Failure semantics — what dies and what continues (live-probed)

Probing the original `loopDungeon`/`DoDungeon` with failing responses
(`work/autosw/trace/loop_fail*.py`, `fail_probe.py`) reveals a **two-tier
error model**:

**Tier 1 — loop start (fatal for the task).** `loopDungeon` fetches
`GetDungeonList` itself before the first battle and passes it to
`GetMAXDungeonStages`, which indexes the list by dungeon id:

- response missing the `dungeon_list` key → `KeyError('dungeon_list')` raises
  **through** `loopDungeon`,
- empty list / requested dungeon id absent → `KeyError(<dungeon_id>)`.

Either way the exception escapes the loop, the worker thread's try/except
catches it, logs "Dungeon error in <dungeon>", and the task ends (UI shows
Stopped on the next 3 s poll). The app never crashes.

**Tier 2 — per-battle (logged and skipped).** Inside `DoDungeon`, transient
failures are swallowed by internal handlers: bad `ret_code`, missing
`my_ranking`, even a raw network exception (it prints the error via C-level
stderr and returns `None`). The loop then just logs "Error in farming N
times" / "Error in energy refill" for that iteration and **continues** the
remaining iterations. A permanently dead server therefore does not stop the
task — it just produces empty iterations until `loop_times` is exhausted.

So: profile loading never needs `GetDungeonList`; only *starting a dungeon
task* does, and there it is mandatory — but failure is contained at the task
level, never at the app level.

---

## 7. Open items

1. Confirm whether each task thread creates its **own SWCore instance** or
   shares one per account (string evidence suggests a shared session with a
   response-correlation queue; needs a runtime trace or disassembly of
   `SWAPI.__init__` to settle).
2. `farm_deter`'s exact selection rules (scenario stage order, arena power
   threshold) are behavioral only — same caveat as the remaining dungeon
   timing unknowns in `05-automation-engine.md` §10.
3. Whether `start_task` on a stopped task restarts the *same* thread object or
   re-creates it from `task_params` (the registry layout supports either).

### 7.1 Settled by live probing (2026-09-07)

Importing the `.pyd` modules under Python 3.11 (see `work/autosw/trace/`)
settled the class-relationship questions:

- **Inheritance chain (definitive, from `__mro__`):**
  `object → summon.SWCore → summon.SWAPI`. The 28-method orchestration class
  subclasses the ~157-member client class. **`common.SWAPI` is not a
  base class** — `common.py` line 36 does `from summon import SWAPI`, i.e.
  `common` merely **re-exports** `summon.SWAPI` (its earlier description as
  "the base SWAPI in common.pyd" was wrong). `common.SWUser` is standalone.
- **Import-order quirk:** `import summon` first fails with
  `ImportError: cannot import name SWAPI` because `summon`'s init triggers
  `common`'s init, which re-imports `SWAPI` from the still-initializing
  `summon`. Importing `common` first resolves the cycle.
- `SWCore.getTowerTime(self, level, difficulty)` and
  `getTowerTimeLegacy(self, level)` signatures confirmed (see 05 §7 for the
  recovered timing tables; legacy is broken dead code).
