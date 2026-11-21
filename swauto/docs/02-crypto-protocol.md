# AutoSW — Crypto & Wire Protocol Reference

> Part of the `autosw-revival/docs/` revival set. Describes the `cipher.pyd`
> engine and the exact wire format used by both the headless bot and the live
> proxy. Verified against the case decryptor
> ([`../../work/autosw/decrypt_tool.py`](../../work/autosw/decrypt_tool.py));
> implemented in this project as `src/autoswkit/crypto.py`. Security
> observations (static keys, zero IV) are cross-referenced in the case report
> and [`../../work/autosw/evidence/findings/`](../../work/autosw/evidence/findings/).

## 1. Envelope (both directions)

```
base64( AES-128-CBC( PKCS7( payload_bytes ) ) )
```

| Parameter | Value |
|-----------|-------|
| Cipher | AES-128 (16-byte key, 16-byte block) |
| Mode | CBC |
| IV | 16 zero bytes — fixed, never random |
| Padding | PKCS#7 (a full `0x10` block is appended when the input is already 16-aligned) |
| Outer encoding | Standard Base64 (RFC 4648) |

## 2. Key table

| Version | ASCII key | Status |
|---------|-----------|--------|
| 1 (legacy) | `E2wN5Eo0t4gle92Z` | Deprecated fallback |
| 2 (active) | `Gr4S2eiNl7zq5MrU` | Current production key on all regions |

Both keys are static, shipped inside `cipher.pyd`, identical for every
installation. A per-session key variant can be selected (the AES-128-CBC
envelope itself is unchanged) — the tools accept it via `-k` / `custom_key`.

## 3. Direction differences

| Direction | Inner payload | Detection hint |
|-----------|---------------|----------------|
| Request (client → server) | UTF-8 JSON, **not** compressed | decrypts straight to JSON |
| Response (server → client) | UTF-8 JSON, **zlib**-compressed (header `78 9c`) | AES-decrypt output starts with zlib magic |

Auto-detection order (as implemented in `autoswkit.crypto.auto_decrypt`):
response-v2 → request-v2 → response-v1 → request-v1. A request tried as a
response fails zlib decompression; a response tried as a request yields
non-JSON bytes.

## 4. Transformation pipelines

Request (client → server):

```
plain JSON dict
  → UTF-8 encode
  → PKCS#7 pad to 16
  → AES-128-CBC encrypt (key, IV = 00*16)
  → Base64
  → HTTP POST body
```

Response (server → client):

```
HTTP body (Base64)
  → Base64 decode
  → AES-128-CBC decrypt (key, IV = 00*16)
  → PKCS#7 unpad
  → zlib decompress
  → UTF-8 decode → JSON parse
```

## 5. RSA session-key exchange

For session-token exchange / license handshakes AutoSW uses **4096-bit** RSA with
`PKCS1_v1_5` padding. The RSA public key is hardcoded in `common.pub_key`
(SPKI prefix `MIICIjA…`, 512-byte modulus — measured off the oracle `common.pyd`,
2026-09-07; see `../../work/autosw/trace/_B4_doc_recon_outcome.md`). Earlier
notes here said 2048-bit, which is wrong for `pub_key` (2048-bit belongs to the
MITM root-CA `ca.key` instead). This path is separate from the AES envelope
above; the AES key stays static in the analyzed build.

## 6. Reference implementations

### Case decryptor (original reference)

`../../work/autosw/decrypt_tool.py` — standalone decryptor/encryptor
(pyCryptodome). CLI: `decrypt-req` / `decrypt-resp` / `decrypt-file` /
`encrypt`, or `-r/-p/-a/-f/-v/-k/-o` flags. It was validated against live
captured payloads during the case.

### This project (`autoswkit`)

`src/autoswkit/crypto.py` — clean port of the same envelope with the same
functions (`decrypt_request`, `encrypt_request`, `decrypt_response`,
`encrypt_response`, `auto_decrypt`, PKCS#7 helpers) and the same CLI flags
(`autoswkit -a/-r/-p/-f/-e -v {1,2} -k <key> -o <out>`). The pytest suite pins
the envelope properties: exact keys/IV, full-block PKCS#7, zlib inner payload
for responses, auto-detect order, and byte-level round-trips.

> The earlier Rust rebuild (`xstomper`, byte-for-byte validated against the
> Python reference) was removed from the repo; Python is the implementation
> path going forward.

## 7. Revival notes

- The whole cipher layer is ~50 lines of code in any modern language; the hard
  part is everything *around* it (session management, RPC wrappers).
- If building *new* protocol code, do **not** reproduce the zero IV / static
  key design — it makes identical plaintexts produce identical ciphertexts
  (finding F-AUTOSW-02) and lets anyone with the extracted keys read/rewrite
  captured traffic offline. Use a random IV per message and derive keys per
  session.
