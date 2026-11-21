"""Unit tests for the per-install root-CA generator (:mod:`swauto.proxy.ca`).

The whole point of ``ca.py`` is F-AUTOSW-01 not being reproduced: AutoSW ships
a **shared** root CA + plaintext key (``CN=swfarm CA``). This clean-room
generator must produce a fresh, per-install, self-signed CA whose key is never
shared. These tests assert the essential X.509 properties directly via
``cryptography`` (already a swauto dependency).
"""

from __future__ import annotations

import pytest

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from swauto.proxy import ca


def test_generate_root_ca_is_self_signed_ca():
    cert_pem, key_pem = ca.generate_root_ca()
    cert = x509.load_pem_x509_certificate(cert_pem)
    key = serialization.load_pem_private_key(key_pem, password=None)

    assert x509.load_pem_x509_certificate(cert.public_bytes(serialization.Encoding.PEM))  # noqa: E501
    assert cert.issuer == cert.subject  # self-signed
    # must be a CA with key-cert-sign (used to mint per-host leaf certs)
    basic = cert.extensions.get_extension_for_class(x509.BasicConstraints)
    assert basic.value.ca is True
    usage = cert.extensions.get_extension_for_class(x509.KeyUsage)
    assert usage.value.key_cert_sign is True
    assert cert.serial_number > 0
    assert key_public_matches(cert, key)


def key_public_matches(cert, key) -> bool:
    from cryptography.hazmat.primitives import serialization as _s
    cert_pub = cert.public_key().public_bytes(_s.Encoding.PEM,
                                              _s.PublicFormat.SubjectPublicKeyInfo)
    key_pub = key.public_key().public_bytes(_s.Encoding.PEM,
                                            _s.PublicFormat.SubjectPublicKeyInfo)
    return cert_pub == key_pub


def test_generate_root_ca_is_unique_per_install():
    """Two generations must never reuse the same key/serial (per-install)."""
    cert_pem_a, key_pem_a = ca.generate_root_ca()
    cert_pem_b, key_pem_b = ca.generate_root_ca()
    assert cert_pem_a != cert_pem_b
    assert key_pem_a != key_pem_b


def test_common_name_is_swauto_not_swfarm():
    """F-AUTOSW-01: must NOT be AutoSW's shared 'swfarm CA'."""
    cert_pem, _ = ca.generate_root_ca()
    cert = x509.load_pem_x509_certificate(cert_pem)
    cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    assert "swfarm" not in cn.lower()  # never reproduce the shared CA identity
    assert "swauto" in cn.lower()


def test_load_or_create_is_idempotent(tmp_path):
    """First call generates + persists; second call reuses the same files."""
    path_a, cert_a, key_a = ca.load_or_create_ca(tmp_path)
    path_b, cert_b, key_b = ca.load_or_create_ca(tmp_path)
    assert path_a == path_b
    assert cert_a == cert_b
    assert key_a == key_b
    assert (tmp_path / "swauto-ca.crt").exists()
    assert (tmp_path / "swauto-ca.key").exists()