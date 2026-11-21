# xStomper 2.0 — cross-platform Rust + Tauri v2 analysis toolkit

Branding: all new artifacts use the **xStomper** brand. No xStomper artifact markets itself as an AutoSW rebuild; mentions of the audited sample inside the case report are purely factual. Scope: decryptor (CLI + GUI), protocol doc, CA-exposure audit CLI. **No** bot/automation functionality, no packet crafting against game servers, no session-capture automation.

**Cross-platform**: Windows, macOS, Linux. Rust core is OS-agnostic; the Tauri shell uses WebView2 / WKWebView / webkit2gtk respectively. Only `xstomper audit` (cert-store checks) is Windows-specific and is hidden/unavailable on other OSes with a clear notice.

## 1. Toolchain check
- Verify `cargo`, `rustc`, `node`, `npm`; install rustup (msvc on Windows) and Node LTS if missing.
- Check `python -c "import Crypto"` — only needed to generate cross-validation test vectors; skip gracefully if absent.

## 2. Project layout: `C:\GitHub\reverse-skill\xstomper\`
```
xstomper/
  package.json + vite.config.ts      # Vue 3 + Vite + TypeScript frontend
  index.html
  src/                               # UI: decrypt workspace (xStomper branding)
    App.vue, components/ (PayloadInput, ResultViewer, KeyPicker)
  src-tauri/
    Cargo.toml                       # tauri v2, aes, cbc, flate2, base64, serde_json, anyhow
    tauri.conf.json
    src/main.rs                      # Tauri entry, invokes core
    src/commands.rs                  # #[tauri::command] decrypt_payload / load_payload_file
    src/core/crypto.rs               # keys v1/v2, zero IV, PKCS7, AES-128-CBC
    src/core/payload.rs              # decrypt_request / decrypt_response(zlib) / auto-detect chain
    src/core/audit.rs                # CA-exposure checker (cfg(windows))
    src/bin/xstomper.rs              # thin headless CLI (same flags as decrypt_tool.py + `audit` subcommand)
  tests/vectors.rs                   # core unit tests + cross-validation vectors
```

## 3. Crypto core (parity with work/autosw/decrypt_tool.py)
- AES-128-CBC, all-zero IV, PKCS7; requests = plain JSON, responses = zlib-compressed.
- Auto mode: response-v2 → request-v2 → response-v1 → request-v1, then error suggesting custom key.
- Shared by both the Tauri commands and the CLI binary — one implementation.

## 4. UI — decrypt workspace (Vue 3, Tauri v2)
- Paste payload or load a file (drag-drop), key version picker (v1/v2/custom key field), mode selector (auto/request/response).
- Result pane: pretty-printed JSON (UTF-8 preserved), copy button, clear error banner when decryption fails.
- Clean xStomper-branded layout; no bot/automation UI of any kind.
- Launching the app opens this workspace; the headless CLI remains for scripting/tests.

## 5. Tests and cross-validation
- `cargo test` on core: PKCS7 edge cases, AES round-trip, zlib envelope.
- Vectors generated with the existing Python script (if pycryptodome present), asserted byte-for-byte in decrypt + re-encrypt directions; otherwise fixed AES-128 known-answer vectors.

## 6. `xstomper audit` (CLI-only, F-AUTOSW-01 checker)
- `certutil -store Root` scan for `CN=swfarm CA` (SHA1 `3962db24e5eba9689e775ca428c0d34ef2b63769`); check install paths for plaintext `ca.key`/`ca.crt`.
- Prints findings + remediation commands; read-only. On non-Windows: prints "Windows-only check" notice.

## 7. Protocol documentation deliverable
- `work/autosw/report/packet-protocol.md`: descriptive spec of the packet envelope (base64(AES-128-CBC(zero-IV, PKCS7, key v1|v2))), request vs response (zlib), session-key variant, referenced to F-AUTOSW-01/02. Documentation only, sourced from existing case evidence.

## 8. Case bookkeeping (per AGENTS.md / case ops)
- Append to `work/autosw/timeline.md`; update `work/autosw/workitems.md`.

## 9. Build & verify
- `cargo test` green; `npm install && npm run tauri build` produces installers: `.msi`/`.exe` (Windows), `.app`/`.dmg` (macOS), `.deb`/`.AppImage` (Linux).
- Smoke tests: decrypt a generated sample payload in both CLI and UI; run `xstomper audit` on this machine and sanity-check output.
- Routing regression tests not required (no changes to routing.json or skills).