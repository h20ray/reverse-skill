"""Packet envelope crypto, reverse-engineered from AutoSW's ``cipher.pyd``.

Wire envelope (both directions, see docs/02-crypto-protocol.md):

    base64( AES-128-CBC( PKCS7( payload_bytes ) ) )

- AES-128, CBC, fixed all-zero IV.
- PKCS#7 padding; a full extra block is appended when the input is already
  16-aligned.
- Requests carry uncompressed UTF-8 JSON; responses are zlib-compressed
  before encryption.
- Keys are static per version (v1 legacy, v2 current); a custom/session key
  may be supplied instead.

NOTE: the zero IV + static keys reproduce the original wire format so
captured payloads remain readable. Do not reuse this design for new
protocols — identical plaintexts yield identical ciphertexts.
"""

from __future__ import annotations

import base64
import zlib
from Crypto.Cipher import AES

KEY_V1 = b"E2wN5Eo0t4gle92Z"  # legacy
KEY_V2 = b"Gr4S2eiNl7zq5MrU"  # current production key
KEYS: dict[int, bytes] = {1: KEY_V1, 2: KEY_V2}

ZERO_IV = b"\x00" * 16


def resolve_key(version: int = 2, custom_key: str = "") -> bytes:
    """Return the 16-byte AES key for a version, or a custom key."""
    if custom_key:
        key = custom_key.encode()
    else:
        try:
            key = KEYS[version]
        except KeyError:
            raise ValueError(f"Unknown key version: {version!r} (expected 1 or 2)") from None
    if len(key) != 16:
        raise ValueError(f"AES-128 key must be 16 bytes, got {len(key)}")
    return key


def pad_pkcs7(data: bytes, block_size: int = 16) -> bytes:
    """PKCS#7 pad; always appends at least one byte (full block when aligned)."""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def unpad_pkcs7(data: bytes, block_size: int = 16) -> bytes:
    if not data or len(data) % block_size:
        raise ValueError("Ciphertext length is not a multiple of the block size")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise ValueError(f"Invalid PKCS#7 padding byte: {pad_len}")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Malformed PKCS#7 padding")
    return data[:-pad_len]


def _cbc(key: bytes) -> AES.Cipher:
    return AES.new(key, AES.MODE_CBC, ZERO_IV)


def decrypt_request(payload: str, version: int = 2, custom_key: str = "") -> str:
    """Request envelope: base64 -> AES decrypt -> unpad -> UTF-8 text."""
    raw = base64.b64decode(payload.strip())
    return unpad_pkcs7(_cbc(resolve_key(version, custom_key)).decrypt(raw)).decode(
        "utf-8", errors="replace"
    )


def encrypt_request(plaintext: str, version: int = 2, custom_key: str = "") -> str:
    """Request envelope: UTF-8 -> pad -> AES encrypt -> base64."""
    encrypted = _cbc(resolve_key(version, custom_key)).encrypt(pad_pkcs7(plaintext.encode("utf-8")))
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_response(payload: str, version: int = 2, custom_key: str = "") -> str:
    """Response envelope: as requests, plus a final zlib inflate."""
    raw = base64.b64decode(payload.strip())
    plain = unpad_pkcs7(_cbc(resolve_key(version, custom_key)).decrypt(raw))
    return zlib.decompress(plain).decode("utf-8", errors="replace")


def encrypt_response(plaintext: str, version: int = 2, custom_key: str = "") -> str:
    """Response envelope: UTF-8 -> zlib deflate -> pad -> AES encrypt -> base64."""
    compressed = zlib.compress(plaintext.encode("utf-8"))
    encrypted = _cbc(resolve_key(version, custom_key)).encrypt(pad_pkcs7(compressed))
    return base64.b64encode(encrypted).decode("ascii")


def auto_decrypt(payload: str, version: int = 2, custom_key: str = "") -> tuple[str, str]:
    """Try every envelope/key combination; returns ``(kind, plaintext)``.

    Order matches the reference decryptor: response-v2 -> request-v2 ->
    response-v1 -> request-v1.
    """
    attempts = [
        (f"response (v{version})", lambda p: decrypt_response(p, version, custom_key)),
        (f"request (v{version})", lambda p: decrypt_request(p, version, custom_key)),
    ]
    other = 1 if version == 2 else 2
    attempts += [
        (f"response (v{other})", lambda p: decrypt_response(p, other, custom_key)),
        (f"request (v{other})", lambda p: decrypt_request(p, other, custom_key)),
    ]
    for name, fn in attempts:
        try:
            return name, fn(payload)
        except Exception:
            continue
    raise ValueError(
        "Failed to decrypt with both v1 and v2 keys. If this payload uses a "
        "session key, pass custom_key."
    )
