"""Envelope property + round-trip tests for autoswkit.crypto.

The original cross-validation vectors lived in the (removed) Rust project;
these tests pin the same invariants: exact key/IV parameters, PKCS#7
behaviour including the full-block case, direction differences (zlib), the
auto-detect order, and byte-level round-trips in both directions.
"""

import base64
import json
import zlib

import pytest

from autoswkit import crypto


SAMPLE = json.dumps({"command": "GetWizardInfo", "wizard_id": 12345})
SAMPLE_RESP = json.dumps({"command": "GetWizardInfo", "result": {"mana": 1000}})


def test_key_table_matches_case():
    assert crypto.KEYS[2] == b"Gr4S2eiNl7zq5MrU"
    assert crypto.KEYS[1] == b"E2wN5Eo0t4gle92Z"
    assert crypto.ZERO_IV == b"\x00" * 16


def test_pad_pkcs7_full_block_when_aligned():
    assert crypto.pad_pkcs7(b"A" * 16) == b"A" * 16 + b"\x10" * 16
    assert crypto.pad_pkcs7(b"A" * 15) == b"A" * 15 + b"\x01"
    assert crypto.pad_pkcs7(b"") == b"\x10" * 16


def test_unpad_rejects_bad_padding():
    with pytest.raises(ValueError):
        crypto.unpad_pkcs7(b"\x00" * 16)
    with pytest.raises(ValueError):
        crypto.unpad_pkcs7(b"A" * 15 + b"\x03")  # inconsistent pad bytes


def test_request_round_trip_all_versions():
    for version in (1, 2):
        envelope = crypto.encrypt_request(SAMPLE, version=version)
        assert crypto.decrypt_request(envelope, version=version) == SAMPLE
        # standard base64, multiple of 16 bytes raw
        assert len(base64.b64decode(envelope)) % 16 == 0


def test_custom_key_round_trip():
    key = b"0123456789abcdef"
    envelope = crypto.encrypt_request(SAMPLE, custom_key=key.decode())
    assert crypto.decrypt_request(envelope, custom_key=key.decode()) == SAMPLE


def test_response_round_trip_has_zlib_inner_payload():
    envelope = crypto.encrypt_response(SAMPLE_RESP, version=2)
    raw = base64.b64decode(envelope)
    inner = crypto.unpad_pkcs7(crypto._cbc(crypto.KEYS[2]).decrypt(raw))
    assert inner[:2] == b"\x78\x9c"  # zlib header, like the real responses
    assert crypto.decrypt_response(envelope, version=2) == SAMPLE_RESP


def test_zero_iv_is_deterministic():
    # Documented (insecure) property of the original format: same plaintext,
    # same key -> same ciphertext. Kept as a spec pin; do not reuse this design.
    a = crypto.encrypt_request(SAMPLE, version=2)
    b = crypto.encrypt_request(SAMPLE, version=2)
    assert a == b


def test_auto_detect_prefers_response_then_request():
    resp = crypto.encrypt_response(SAMPLE_RESP, version=2)
    kind, text = crypto.auto_decrypt(resp)
    assert kind == "response (v2)"
    assert json.loads(text) == json.loads(SAMPLE_RESP)

    req = crypto.encrypt_request(SAMPLE, version=2)
    kind, text = crypto.auto_decrypt(req)
    assert kind == "request (v2)"
    assert json.loads(text) == json.loads(SAMPLE)


def test_auto_detect_falls_back_to_legacy_key():
    req_v1 = crypto.encrypt_request(SAMPLE, version=1)
    kind, text = crypto.auto_decrypt(req_v1, version=2)
    assert kind == "request (v1)"
    assert json.loads(text) == json.loads(SAMPLE)


def test_auto_detect_failure_message():
    # 31 bytes: not a multiple of the block size, so every attempt fails
    # deterministically.
    with pytest.raises(ValueError, match="session key"):
        crypto.auto_decrypt(base64.b64encode(b"\x00" * 31).decode())


def test_zlib_round_trip_plain():
    assert zlib.decompress(zlib.compress(b"hello")) == b"hello"
