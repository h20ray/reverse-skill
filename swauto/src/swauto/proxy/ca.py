"""Per-install unique root CA for the local capture proxy.

AutoSW ships a **shared** root CA (``CN=swfarm CA``, SHA1 ``3962db24…``) plus a
plaintext ``ca.key`` in its install dir — a finding (F-AUTOSW-01) that the
clean-room build must NOT reproduce: anyone who trusts that cert can MITM every
AutoSW user. So unlike the original we generate a **fresh root CA per install**
and never reuse/publish a key. Install only ever happens on the operator's own
machine for the operator's own login capture (see case scope).

Default CA subject/validity mirror what the transparent-proxy use needs
(generate once, cache under the profiles dir next to the secret store).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

log = logging.getLogger("swauto.proxy")

# Avoid any ambiguity with AutoSW's shared "swfarm" identity — this is a fresh,
# locally-generated CA, never distributed.
CA_COMMON_NAME = "swauto-local capture CA"
CA_ORGANIZATION = "swauto (per-install)"


def _random_serial() -> int:
    import secrets
    # 159 bits keeps it positive within X.509's 20-byte serial ceiling.
    return int.from_bytes(secrets.token_bytes(20), "big") >> 1


def generate_root_ca(*, common_name: str = CA_COMMON_NAME,
                     org: str = CA_ORGANIZATION,
                     valid_days: int = 3650,
                     key_size: int = 2048) -> tuple[bytes, bytes]:
    """Generate a fresh (cert_pem, key_pem) root-CA pair.

    Returns PEM bytes. The caller decides persistence; the key must never be
    committed or shared. ``valid_days`` default 10 years; CA generation is
    deliberately per-install and unique.
    """
    now = datetime.now(timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)                      # self-signed root
        .public_key(key.public_key())
        .serial_number(_random_serial())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=valid_days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                       critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True, key_encipherment=False,
            key_cert_sign=True, crl_sign=True, content_commitment=False,
            data_encipherment=False, key_agreement=False,
            encipher_only=False, decipher_only=False), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def load_or_create_ca(store_dir: str | Path, *,
                      cert_name: str = "swauto-ca.crt",
                      key_name: str = "swauto-ca.key") -> tuple[Path, bytes, bytes]:
    """Load the per-install CA from ``store_dir``, generating it on first use.

    Returns ``(cert_path, cert_pem, key_pem)``. ``store_dir`` is the private
    store (default the gitignored profiles dir). Key bytes are kept in memory
    only; the file is created with the default umask (best-effort on Windows).
    """
    directory = Path(store_dir)
    directory.mkdir(parents=True, exist_ok=True)
    cert_path = directory / cert_name
    key_path = directory / key_name
    if cert_path.exists() and key_path.exists():
        cert_pem = cert_path.read_bytes()
        key_pem = key_path.read_bytes()
        log.info("Using existing per-install CA: %s", cert_path)
        return cert_path, cert_pem, key_pem
    cert_pem, key_pem = generate_root_ca()
    cert_path.write_bytes(cert_pem)
    key_path.write_bytes(key_pem)
    log.info("Generated fresh per-install CA: %s", cert_path)
    return cert_path, cert_pem, key_pem
