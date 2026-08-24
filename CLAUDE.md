# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This repository is a **task skill router** for authorized reverse engineering, mobile/security analysis, and pentest workflows. There is no build step — it is a routing/config package. CI (`.github/workflows/ci.yml`) runs the test suite on Windows + Ubuntu for every push/PR and it is the gate for any routing/config/script change.

## On Any Task

`RULES.md` is the single source of truth for behavior chain and authorization.

Routing order:

1. `skills/MASTER-ROUTING.md` or `skills/scripts/master-route.ps1 -Hint "..."`
2. `skills/scripts/case-init.ps1` → current analysis project's `work/<case>/scope.md` (must grant auth before ACT)
3. `skills/routing.md` when ambiguous; roles in `skills/ops/role-map.md`
4. Open PRIMARY `SKILL.md` and execute ACTION REQUIRED
5. Timeline/workitems + Evidence→Finding→Path (`skills/ops/`)
6. `skills/tool-index.md` for real tool paths (never guess)
7. Missing tool → `skills/scripts/bootstrap-reverse.ps1` (manifest capabilities only)

**Routing single source of truth is `skills/config/routing.json`** (43 rules R0–R44 + a `priority` array). `master-route.ps1` reads it to choose PRIMARY by keyword score; `skills/routing.md` and `skills/MASTER-ROUTING.md` are human-readable mirrors. **Change routing only in `routing.json`**, then keep the markdown tables in sync and rerun the coherence check. `verify-routing-coherence.ps1` asserts the markdown priority table matches the JSON `priority` array.

**Authorization hard gate**: no target ACT (scan/hook/exploit/active probe) until the case's `scope.md` is initialized via `case-init` with `auth.status=granted`, `in_scope` set, and a `network_profile` chosen. `ready_for_act` is auto-set only for a valid granted scope (or an `offline-sample` preset with an explicit local sample path). `case-guard -Force` / `--force` is a compatibility flag and MUST NOT bypass the auth gate. Offline/local samples may stay `network_profile.mode=offline`.

**Identity**: lightweight skill router — see `skills/ops/IDENTITY.md` (not a Z3r0 platform; deliberately avoids the Z3r0 server/DB/UI stack). Conclusions use Evidence→Finding→Path (`skills/ops/evidence-finding-path.md`).

## First-Run Setup

`skills/tool-index.md` is not in fresh clones (gitignored). Generate it:

```bash
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/refresh-tool-index.ps1

# macOS / Linux
bash skills/scripts/refresh-tool-index.sh

# Kali
bash kali/scripts/refresh-tool-index.sh
```

This emits `skills/tool-index.md` + `skills/tool-index.json` for the current machine. Skip it and routing breaks (RULES.md reads tool-index.md). Read `README_AI.md` for the full bootstrap sequence.

## Test Commands (run after any routing/config/script change)

The PowerShell suite is primary; the `.sh` counterparts provide Linux/macOS parity and are exercised in CI.

```powershell
# 1. Routing regression — runs all routing-benchmark.json (hint → expected PRIMARY), fails on mismatch
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/test-routing.ps1
#   -Quick   only the minimal fast subset

# 2. Structure coherence + supply-chain pin gate (unpinned auto-install fails)
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/verify-routing-coherence.ps1

# 3. Smoke: verify + script parse + quick route matrix (incl. Chinese hints)
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/smoke.ps1

# 4. INDEX.md drift check — regenerate via extract-summaries.ps1 if this reports dirty
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/extract-summaries.ps1 -Check
```

Linux/macOS parity and other focused suites:

```bash
bash skills/scripts/test-routing.sh
bash skills/scripts/test-bootstrap-manifest.sh
bash skills/scripts/test-bash-workflow.sh
bash skills/scripts/test-client-neutral-bootstrap.sh
```

Bash/PowerShell syntax is itself checked in CI (`bash -n` all `.sh`; `Parser` all tracked `.ps1`). Note the BOM rule: **every non-ASCII `.ps1` must carry a UTF-8 BOM** or Windows PowerShell 5.1 mis-parses Chinese string literals — CI enforces this.

Case-contract (evidence graph review) and version checks:

```bash
python3 skills/case-review/scripts/review_case.py work/<case> --verify-hashes --strict
python3 skills/case-review/tests/test_review_case.py
```

`VERSION` must match the latest `## [x.y.z]` header in `CHANGELOG.md` — CI enforces this; bump both together on releases.

## Coherence check

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/verify-routing-coherence.ps1
```

## Architecture

Two layers, both platform-agnostic by design:

- **`skills/`** — the router + methodology modules. Each subdirectory (`apk-reverse/`, `ida-reverse/`, `js-reverse/`, `malware-analysis/`, `pentest-tools/`, `attack-chain/`, `pwn-chain/`, `firmware-pentest/`, `edr-bypass-re/`, etc.) is a self-contained module with its own `SKILL.md` whose frontmatter `name`/`description` is aggregated into `skills/INDEX.md` by `extract-summaries.ps1`. The `routing.json` keywords map hints to these modules; `priority` breaks ties.
- **`CTF-Sandbox-Orchestrator/`** — separate CTF competition stack (42 sub-skills), GPLv3, referenced from `skills/routing.md` as `../CTF-Sandbox-Orchestrator/...`.

Cross-platform execution: the shared routing/case/bootstrap contract is duplicated as PowerShell (`.ps1`, Windows) and Bash (`.sh`, Linux/macOS/Kali). `RULES.md` is the Windows canonical rule set; `kali/RULES-kali.md` is the Kali variant. Kernel of the flow:

```
master-route  → PRIMARY (routing.json)
case-init     → work/<case>/scope.md  (auth gate before ACT)
bootstrap     → tool-index.md         (manifest capabilities only)
skill SKILL.md → ACTION REQUIRED      (methodology)
case-review   → Evidence/Finding/Path audit → docs-generator + field-journal
```

Key contracts in `skills/ops/`: `scope-contract.md` (start gate), `evidence-finding-path.md` (Evidence→Finding→Path), `role-map.md` (lead/cie/cpe/cre/cae/cbe/doc → skill), `timeline-workitem.md` (decision_delta + carry_forward_refs), `skill-supply-chain.md` (external skill/MCP install gate). `README_AI.md` is the human-facing AI bootstrap; `AGENTS.md` is the platform-neutral repo entry.

**Client-neutrality**: routing core, test suite, and manifests must not depend on a specific AI client. Claude/Codex/Cursor/OpenCode connect only via their own adapters or project-instruction files; client-specific config stays optional and outside the routing contract. `skills/INDEX.md` is generated, never hard-coded to a client or module count.
