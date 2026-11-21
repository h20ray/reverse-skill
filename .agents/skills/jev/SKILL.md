---
name: jev
description: "Universal TypeSafe Jev integration for reverse-skill. Use Jev MCP tools (jev_receipt, jev_guard, jev_decide_noul, jev_decide_choice, jev_decide_score, jev_compact) and CLI for log dehydration, authorization safety guardrails, routing decision primitives, and token-efficient reasoning."
---

# reverse-skill — Universal Jev Integration & Decision Standard

## Overview

**Universal TypeSafe Jev** provides sub-second decision primitives, verified log receipt extraction (saving up to 95%+ context tokens), context compaction, and safety guardrails.

In the **reverse-skill** workspace, Jev operates alongside **RTK (Rust Token Killer)** to minimize context bloating, guard against unauthorized actions, and enforce rigorous evidence traceability.

---

## The Two-Tier Context Preservation Architecture

```
┌────────────────────────────────────────────────────────┐
│  Tier 1: RTK CLI Proxy (Pre-Filtering at Shell Level) │
│  - Prefix terminal commands: `rtk powershell ...`, etc │
│  - Drops progress bars, banners, raw pass logs         │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│  Tier 2: Jev Receipt Engine (Post-Execution Dehydration│
│  - Tool: `jev_receipt` (or CLI: `jev receipt`)         │
│  - Dehydrates >1200 char outputs into verified receipts│
│  - Isolates exact diagnostics & traces upon failure    │
└────────────────────────────────────────────────────────┘
```

---

## When to Use Jev Tools in reverse-skill

### 1. Log Dehydration & Diagnostic Isolation (`jev_receipt`)
- **Long Execution Outputs**: When test runs, smoke tests, or disassembler dumps exceed **1200 characters**, use `jev_receipt` to compress passing output into `[Jev Verified Receipt ✓]` or extract targeted error blocks into `[Jev Diagnostic Warning ⚠️]`.
- **Test Failure Diagnostics**: When `smoke.ps1` or `test-routing.ps1` fails, pass `exitCode: 1` along with the raw log to isolate failed assertions or route drift immediately.

```json
// Example MCP Call
{
  "ServerName": "jev",
  "ToolName": "jev_receipt",
  "Arguments": {
    "output": "<raw smoke output>",
    "command": "powershell -File skills/scripts/smoke.ps1",
    "thresholdChars": 1200,
    "exitCode": 0
  }
}
```

### 2. Pre-Flight Command Safety Guard (`jev_guard`)
Always verify safety before running sensitive, destructive, or system-altering actions:
- Verifying the Authorization Hard Gate before active probes or exploitation (`work/<case>/scope.md` has `auth.status=granted`).
- Running active network scanning or exploit modules against external hosts.
- Destructive git operations (`git reset --hard`, `git clean -fdx`).

```json
// Example MCP Call
{
  "ServerName": "jev",
  "ToolName": "jev_guard",
  "Arguments": {
    "action": "Run active nuclei scan against target domain",
    "context": "Verifying case scope.md authorization status before scan"
  }
}
```

### 3. Calibrated Routing & Case Verification (`jev_decide_noul`)
Use `jev_decide_noul` for high-precision, sub-second boolean verification:
- **Authorization Gate Check**: Ensure `ready_for_act` conditions and explicit sample paths are verified before testing.
- **Evidence-Finding-Path Traceability**: Verify that every finding is linked to an immutable evidence artifact.
- **Ground-Truth Disassembler Gate**: Verify that decompiled blocks match authenticated disassembler output.

```json
// Example MCP Call
{
  "ServerName": "jev",
  "ToolName": "jev_decide_noul",
  "Arguments": {
    "hypothesis": "Case scope.md has auth.status=granted and in_scope targets defined.",
    "state": "<scope.md content>"
  }
}
```

### 4. Route Disambiguation & Classification (`jev_decide_choice`)
Use `jev_decide_choice` for fast deterministic classification:
- Primary skill routing disambiguation when keywords overlap multiple domains.
- Target binary architecture and runtime classification (`delphi_native`, `dotnet_cil`, `native_pe_x64`, `dalvik_dex`, `arm64_elf`).

```json
// Example MCP Call
{
  "ServerName": "jev",
  "ToolName": "jev_decide_choice",
  "Arguments": {
    "decision": "Determine primary routing domain for multi-domain prompt",
    "criteria": "apk-reverse:Android APK and smali decompile, js-reverse:Web frontend obfuscation, ida-reverse:Native PE/ELF disassembly",
    "state": "Task: decompile packed native library inside Android APK"
  }
}
```

### 5. Benchmark Dumps & Transcript Compaction (`jev_compact`)
When inspecting large test suites (`routing-benchmark.json` test runs), bulky tool indices, or multi-turn transcripts:
- Use `jev_compact` to prune obsolete verbose command outputs while keeping findings and evidence chains 100% verbatim.

---

## Summary of Available Jev Tools

| Tool Name | Type | Primary Use Case in reverse-skill |
| :--- | :--- | :--- |
| `jev_status` | Probe | Check Jev provider connectivity and response latency |
| `jev_receipt` | Dehydrator | Compress long test/routing outputs (>1200 chars) into verified receipts |
| `jev_guard` | Safety | Validate authorization hard gates and destructive commands |
| `jev_decide_noul` | Boolean | Calibrated true/false check for authorization readiness and evidence links |
| `jev_decide_choice` | Classifier | Route disambiguation and architecture resolution |
| `jev_decide_score` | Scorer | Case review scoring and report completeness rating |
| `jev_compact` | Compactor | Compact large test logs, tool index dumps, and transcripts |
