# 2026-09-13 — Pokémon TCG Pocket APK Static Security Review (MuMu 15)

- **Case**: `20260913-054815-apk-security-analysis-of-pokemon` (`work/<case>/report/REPORT.md` has the full findings)
- **Target**: `jp.pokemon.pokemontcgp` (TCG Pocket), pulled from operator-owned MuMu Player 15 "Game Lib" instance (index 3, adb `127.0.0.1:16480`)
- **Lane**: offline static analysis only; no live-service interaction, no cheat development

## What was done

1. Locate package via `MuMuManager adb -v 3 -c "shell pm list packages"` → `jp.pokemon.pokemontcgp`; pull 3 splits (`base` 46 MB, `arm64_v8a` 191 MB, `bundledtree` 551 MB) with the 15.0 adb (`MSYS_NO_PATHCONV=1`).
2. `decode.ps1` (must run under **pwsh** — Windows PowerShell 5.1 chokes on UTF-8-no-BOM in `ToolDiscovery.ps1`): jadx 11,308 files, apktool clean.
3. Manifest summary + grep sweeps + Python strings scan on native libs.

## Architecture facts worth remembering

- Unity **IL2CPP**; all game logic in `libil2cpp.so` (135.6 MB) — Java layer is pure SDK glue.
- Auth chain: Nintendo NPf BAAS (`*.baas.nintendo.com`) + Play Games + Firebase Auth.
- `libsigner.so` is just the **Adjust** signature lib, not app crypto.

## Findings (TL;DR)

| ID | Sev | Finding |
|----|-----|---------|
| F3 | Low→Med | unity-webview `CWebViewPlugin$4` sets `setAllowUniversalAccessFromFileURLs(true)` + JS bridge `"Unity"`; severity depends on whether remote URLs are loaded (lives in IL2CPP) |
| F4 | Low | `global-metadata.dat` unencrypted → Il2CppDumper trivially recovers C# symbols (matches 2026-09-12 journal) |
| F7 | Low | Broad legacy perms (`BLUETOOTH*`, `ACCESS_COARSE_LOCATION`, legacy storage) on targetSdk 36 |
| F1/F2 | Info | Firebase API key + `npf.json` present but contain no secrets (basicAuth empty) |
| F5/F6/F8 | Pass | `allowBackup=false`, account prefs excluded from backup/transfer; no debuggable/cleartext/world-readable/custom-TrustManager; exported components all framework-standard |

## Gotchas hit

- MuMu instance 3 has **no root** (`su` missing, adb is uid 2000) — on-device `shared_prefs` inspection blocked; verify F5 encryption later on a rooted instance.
- `unzip "lib/*"` glob fails inside Git Bash on the split APK; use Python `zipfile`.
- PowerShell 5.1 vs pwsh encoding issue above — affects every script that dot-sources `skills/scripts/lib/ToolDiscovery.ps1`.
