"""
Lightweight symmetric encryption helpers for storing wearable credentials.

Uses Fernet (AES-128 in CBC with HMAC) via cryptography library. The secret
must be provided as a URL-safe base64-encoded 32-byte key.
"""

from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Optional[Fernet]:
    key = settings.WEARABLE_CRED_SECRET
    if not key:
        return None
    try:
        return Fernet(key.encode("utf-8"))
    except Exception:
        return None


def encrypt_text(plaintext: str) -> Optional[str]:
    f = _get_fernet()
    if not f:
        return None
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(ciphertext: str) -> Optional[str]:
    f = _get_fernet()
    if not f:
        return None
    try:
        data = f.decrypt(ciphertext.encode("utf-8"))
        return data.decode("utf-8")
    except InvalidToken:
        return None
    except Exception:
        return None

