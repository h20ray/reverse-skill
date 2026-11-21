---
name: rtk
description: Use RTK (Rust Token Killer) CLI proxy to execute shell commands (powershell, python, git, r2, jadx, find, grep) with compressed, token-optimized output to save 60-90% LLM context tokens.
---

# RTK (Rust Token Killer) Skill

## Overview

**RTK** is a high-performance CLI proxy installed at `C:\tools\rtk\rtk.exe` that filters boilerplate, progress bars, banners, and redundant logs from shell command outputs before returning them to the agent's context window.

By running commands through `rtk`, terminal output size is reduced by **60–90%**, significantly preserving context window space and reducing latency.

---

## When to Use RTK

Always prefer prefixing shell commands with `rtk` during test runs, skill routing, case audits, and reverse engineering:

### 1. Verification & Test Suites
- `rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/smoke.ps1`
- `rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/verify-routing-coherence.ps1`
- `rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/test-routing.ps1`
- `rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/master-route.ps1 -Hint "<task>"`
- `rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/case-init.ps1 -Hint "<task>"`

### 2. Python Case Review & Verification
- `rtk python skills/case-review/scripts/review_case.py work/<case> --verify-hashes --strict`
- `rtk python skills/case-review/tests/test_review_case.py`

### 3. RE & Disassembly CLI Tools
- `rtk r2 -q -c "aaa; afl" <binary>`
- `rtk jadx --no-res -d <out_dir> <apk>`
- `rtk apktool d -f -o <out_dir> <apk>`

### 4. Git Operations
- `rtk git status` (ultra-compact branch and file state)
- `rtk git diff` (condensed diff showing only changed blocks)
- `rtk git log -n 5`
- `rtk git branch -a`

### 5. Search & Inspection
- `rtk grep "keyword" skills/`
- `rtk find "*.ps1" skills/scripts/`
- `rtk ls skills/`

---

## Meta & Diagnostic Commands

- `rtk gain` — Display accumulated token savings across sessions.
- `rtk gain --history` — View historical command savings breakdown.
- `rtk discover` — Scan terminal history for missed RTK compression opportunities.
- `rtk proxy <cmd>` — Run a command through RTK without filtering (for debugging raw output).

---

## When NOT to Use RTK

- Do NOT use RTK for long-running daemon/watcher processes (e.g. interactive Frida tracing).
- Do NOT use RTK when the raw uncompressed binary output must be piped into another script that requires exact unformatted byte streams.
