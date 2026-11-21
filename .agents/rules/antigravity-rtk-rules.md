# RTK - Rust Token Killer (Google Antigravity & Agent Rules)

**Usage**: Token-optimized CLI proxy for shell commands in the `reverse-skill` workspace.

## Core Rule

Whenever executing shell commands in this workspace via PowerShell/Bash/Cmd, prefix commands with `rtk` to filter noise, banners, and redundant logs, saving 60–90% of LLM context tokens.

### Common reverse-skill Command Mappings

```powershell
# Routing & Verification Quality Gates
rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/smoke.ps1
rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/verify-routing-coherence.ps1
rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/test-routing.ps1
rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/master-route.ps1 -Hint "<task>"
rtk powershell -NoProfile -ExecutionPolicy Bypass -File skills/scripts/case-init.ps1 -Hint "<task>"

# Python Analysis & Case Review
rtk python skills/case-review/scripts/review_case.py work/<case> --verify-hashes --strict
rtk python skills/case-review/tests/test_review_case.py

# Reverse Engineering CLI Utilities
rtk r2 -q -c "aaa; afl" <target_binary>
rtk jadx --no-res -d <out_dir> <apk>
rtk apktool d -f -o <out_dir> <apk>

# Version Control
rtk git status
rtk git diff
rtk git log -n 5

# Filesystem & Search
rtk ls skills/
rtk find "*.ps1" skills/scripts/
rtk grep "keyword" skills/
```

### Meta Commands

```powershell
rtk gain              # Show accumulated token savings summary
rtk gain --history    # History of commands and token compression
rtk discover          # Find missed RTK opportunities
rtk proxy <cmd>       # Pass through raw command (debugging only)
```

## Exceptions

Do **not** use `rtk` for:
- Long-running daemons, watchers, or interactive debuggers (e.g. Frida live tracing `frida -U -f ...`, interactive IDA Python).
- Commands where raw binary streams or unformatted machine outputs are piped directly into binary decoders.
