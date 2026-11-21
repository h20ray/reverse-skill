# Universal TypeSafe Jev Integration & Decision Standard

**Usage**: Cross-Agent Decision Primitives, Log Receipt Dehydration, and Authorization Guardrails in the `reverse-skill` workspace.

## Core Rules

### 1. Two-Tier Context Preservation (RTK + Jev)
Terminal output and test runs in this workspace follow a strict two-tier compression workflow:
- **Tier 1 (Execution)**: Always prefix terminal commands with `rtk` (`rtk powershell ...`, `rtk python ...`, `rtk git ...`, `rtk r2 ...`) to strip noisy banners, pass logs, and progress indicators.
- **Tier 2 (Post-Execution Dehydration)**: When terminal output, smoke test summaries, or disassembler dumps exceed **1200 characters**, invoke `jev_receipt` to extract concise verified receipts `[Jev Verified Receipt ✓]` or targeted failure diagnostic blocks `[Jev Diagnostic Warning ⚠️]`.

### 2. Pre-Flight Command Safety Guard (`jev_guard`)
Run `jev_guard` before executing potentially destructive, perimeter-altering, or active-probing operations:
- Verifying the Authorization Hard Gate: ensuring `work/<case>/scope.md` has `auth.status=granted` before executing any active probe or exploitation.
- Destructive git operations (`git reset --hard`, `git clean -fdx`).
- Running network scanning/pentesting tools against targets outside the designated `network_profile`.
- System-modifying containment or hook injections.

### 3. Calibrated Audit & Evidence Verification (`jev_decide_noul`)
Use `jev_decide_noul` for sub-second calibrated boolean verification:
- Validate authorization readiness: verify that `ready_for_act` conditions and explicit sample paths are satisfied.
- Evidence chain traceability: confirm each finding in `evidence-finding-path.md` maps to an immutable evidence artifact.
- Disassembly ground-truth verification: confirm decompiled functions match genuine disassembler exports.

### 4. Classification & Route Disambiguation (`jev_decide_choice`)
Use `jev_decide_choice` for fast deterministic multi-option classification:
- Primary skill routing disambiguation when multi-domain keywords overlap (`apk-reverse` vs `mobile-reverse`, `ida-reverse` vs `radare2` vs `ghidra-reverse`, `js-reverse` vs `api-security`).
- Target binary architecture and runtime resolution (`delphi_native`, `dotnet_cil`, `native_pe_x64`, `dalvik_dex`, `arm64_elf`).
- Risk and triage level categorization.

### 5. Benchmark & Transcript Compaction (`jev_compact`)
When inspecting large test suites (`routing-benchmark.json` test runs), bulky tool indices, or multi-turn transcripts:
- Use `jev_compact` to prune obsolete verbose command outputs while keeping core findings, case scope, and evidence chains 100% verbatim.
