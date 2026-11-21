# AutoSW Revival Docs

Developer-reference documentation for the AutoSW application, produced by
reverse-engineering the installed build (case: [`../../work/autosw/`](../../work/autosw/)).
This is the canonical home for the revival doc set; the copies under
`work/autosw/docs/` are the frozen case record.

| Doc | Contents |
|-----|----------|
| [01-architecture.md](01-architecture.md) | What AutoSW is, high-level data flow, module map, both runtime flows, threading model, external touchpoints |
| [02-crypto-protocol.md](02-crypto-protocol.md) | Wire envelope (AES-128-CBC + PKCS#7 + zlib + Base64), key table, RSA exchange, reference implementations |
| [03-module-reference.md](03-module-reference.md) | Per-module breakdown: `ui`, `control` (IndexControl/MainControl/worker threads), `summon`, `common`, `cipher`, `proxy` (`SWAddon` + nerf algorithm), `score`, `rules`, native binaries |
| [04-swapi-reference.md](04-swapi-reference.md) | All 180 `SWAPI` methods in 12 categories, and how the bot loops use them |
| [05-automation-engine.md](05-automation-engine.md) | Automation deep dive: profile JSON layout, frontend→backend task contract (exact payloads), scheduler/conflict model, battle-loop template, all wait/retry constants, porting notes |
| [06-worker-threads.md](06-worker-threads.md) | Worker-thread mechanics: FarmThread base, DThread/AThread anatomy, quit_event cooperative stop, task registry & conflicts, thread↔SWCore call chain, worked DThread life, porting map |
| [07-pipeline-flow.md](07-pipeline-flow.md) | **The full pipeline walkthrough**: boot → login → profile → task creation → dungeon battle loop (exact wire traffic), confirmed timing formulas, two-tier failure model, per-task pipeline table, autoswkit implementation status, evidence index |

## Where the case material lives

- Security findings & incident response: [`../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md`](../../work/autosw/report/AUTOSW_DETAILED_ANALYSIS.md) (§9–10), [`../../work/autosw/report/report.md`](../../work/autosw/report/report.md), [`../../work/autosw/evidence/findings/`](../../work/autosw/evidence/findings/)
- Descriptive packet-envelope spec (audit record): [`../../work/autosw/report/packet-protocol.md`](../../work/autosw/report/packet-protocol.md)
- Reference decryptor: [`../../work/autosw/decrypt_tool.py`](../../work/autosw/decrypt_tool.py) (the original `xstomper` Rust rebuild was removed from the repo; Python is the implementation path)
- Case ops: [`../../work/autosw/scope.md`](../../work/autosw/scope.md), `timeline.md`, `workitems.md`

## Quick orientation for a rebuild

1. **Crypto is implemented** — `src/autoswkit/crypto.py` reproduces the
   envelope (AES-128-CBC, zero IV, PKCS#7, zlib, auto-detect, v1/v2/custom
   keys) with tests; it is the port of the case-validated decryptor.
2. **Protocol surface is documented** — `04-swapi-reference.md` is the complete
   RPC map (mirrored as data in `src/autoswkit/swapi_catalog.py`); `02` tells
   you how each call is packaged.
3. **Decision logic is separable** — rune/artifact scoring (`score.pyd`) and
   the keep/sell rule engine (`rules.pyd`) are pure logic with no OS
   dependencies; the easiest pieces to port.
4. **OS glue needs re-implementation** — cert injection, WinDivert/mitmproxy
   interception, ADB scripting, WebView2 IPC, and tray integration are all
   Windows/Python-specific (see `03` §10). The MITM tampering subsystem is
   deliberately out of scope for the revival (see the project README).
