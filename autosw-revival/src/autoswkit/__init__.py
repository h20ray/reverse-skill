"""AutoSW revival toolkit.

Analysis/interop toolkit rebuilt from the reverse-engineered AutoSW sample
(case: work/autosw). See docs/ for the full reference set.
"""

from autoswkit.crypto import (
    KEYS,
    ZERO_IV,
    auto_decrypt,
    decrypt_request,
    decrypt_response,
    encrypt_request,
    encrypt_response,
    resolve_key,
    unpad_pkcs7,
    pad_pkcs7,
)

__version__ = "0.1.0"

__all__ = [
    "KEYS",
    "ZERO_IV",
    "auto_decrypt",
    "decrypt_request",
    "decrypt_response",
    "encrypt_request",
    "encrypt_response",
    "resolve_key",
    "pad_pkcs7",
    "unpad_pkcs7",
    "__version__",
]
