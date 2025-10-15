"""
Generate a Fernet key for encrypting wearable credentials.

Usage:
  python ULTIMATE_COACH_BACKEND/scripts/generate_fernet_key.py

Output:
  - Base64 URL-safe Fernet key (32-byte key)
  - Export lines you can copy into your environment

Note:
  This script does NOT require the cryptography package to run; it uses
  os.urandom + base64.urlsafe_b64encode to generate a valid Fernet key.
  The backend at runtime will still require the cryptography package for
  actual encryption/decryption (already listed in requirements).
"""

from __future__ import annotations

import base64
import os


def main() -> None:
    raw = os.urandom(32)  # 32 random bytes
    key = base64.urlsafe_b64encode(raw).decode("utf-8")
    print("\nGenerated Fernet key (base64, url-safe):\n")
    print(key)
    print("\nSet this in your backend environment as:\n")
    print("# Shell (Linux/Mac):")
    print(f"export WEARABLE_CRED_SECRET=\"{key}\"")
    print("\n# Windows PowerShell:")
    print(f"$env:WEARABLE_CRED_SECRET=\"{key}\"")
    print("\n# .env file (ULTIMATE_COACH_BACKEND/.env):")
    print(f"WEARABLE_CRED_SECRET=\"{key}\"")


if __name__ == "__main__":
    main()
