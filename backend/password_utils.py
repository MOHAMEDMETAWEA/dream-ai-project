"""
Password hashing helpers for DreamAI.

Uses stdlib PBKDF2 so the project can initialize and run tests without
requiring an external bcrypt package.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a salted password hash string."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = os.urandom(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"{ALGORITHM}${ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    if not stored_hash or not password:
        return False

    try:
        algorithm, iterations_str, salt_b64, hash_b64 = stored_hash.split("$", 3)
        if algorithm != ALGORITHM:
            return False

        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_hash = base64.b64decode(hash_b64.encode("ascii"))
    except (ValueError, TypeError, base64.binascii.Error):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_hash, expected_hash)
