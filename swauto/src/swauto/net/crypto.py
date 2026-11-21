"""Packet envelope crypto — clean-room implementation of the documented
wire format (docs/02-crypto-protocol.md):

    base64( AES-128-CBC( PKCS7( payload_bytes ) ) )

AES-128, CBC, fixed all-zero IV, PKCS#7 with an always-present padding
block. Requests carry uncompressed UTF-8 JSON; responses are zlib-compressed
before encryption. Static per-version keys reproduce the original wire
format for interoperability with captured payloads.
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
    if custom_key:
        key = custom_key.encode()
    elif version in KEYS:
        key = KEYS[version]
    else:
        raise ValueError(f"Unknown key version: {version!r} (expected 1 or 2)")
    if len(key) != 16:
        raise ValueError("AES-128 key must be 16 bytes")
    return key


def pad_pkcs7(data: bytes, block: int = 16) -> bytes:
    n = block - (len(data) % block)
    return data + bytes([n]) * n


def unpad_pkcs7(data: bytes, block: int = 16) -> bytes:
    if not data or len(data) % block:
        raise ValueError("Ciphertext not block-aligned")
    n = data[-1]
    if not 1 <= n <= block or data[-n:] != bytes([n]) * n:
        raise ValueError("Bad PKCS#7 padding")
    return data[:-n]


def _cbc(key: bytes):
    return AES.new(key, AES.MODE_CBC, ZERO_IV)


def encrypt_request(plaintext: str, version: int = 2, custom_key: str = "") -> str:
    data = pad_pkcs7(plaintext.encode())
    return base64.b64encode(_cbc(resolve_key(version, custom_key)).encrypt(data)).decode()


def decrypt_response(payload: str, version: int = 2, custom_key: str = "") -> str:
    raw = base64.b64decode(payload)
    data = unpad_pkcs7(_cbc(resolve_key(version, custom_key)).decrypt(raw))
    try:
        return zlib.decompress(data).decode()
    except zlib.error:
        return data.decode()


def encrypt_response(plaintext: str, version: int = 2, custom_key: str = "") -> str:
    data = pad_pkcs7(zlib.compress(plaintext.encode()))
    return base64.b64encode(_cbc(resolve_key(version, custom_key)).encrypt(data)).decode()


def decrypt_request(payload: str, version: int = 2, custom_key: str = "") -> str:
    raw = base64.b64decode(payload)
    return unpad_pkcs7(_cbc(resolve_key(version, custom_key)).decrypt(raw)).decode()


def auto_decrypt(payload: str, version: int = 2, custom_key: str = "") -> tuple[str, str]:
    """Try both directions; returns (kind, plaintext)."""
    for kind, fn in (("response", decrypt_response), ("request", decrypt_request)):
        try:
            return kind, fn(payload, version, custom_key)
        except Exception:
            continue
    raise ValueError("Payload matches neither envelope direction")
