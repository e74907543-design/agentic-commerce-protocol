"""Example utilities for bcrypt password hashing with optional pepper support."""
from __future__ import annotations

import os

import bcrypt

# Configure cost via env var
BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
# Optional pepper (keep in secrets manager)
PEPPER = os.environ.get("PASSWORD_PEPPER")  # e.g., b"my-very-secret-pepper" or None

def _apply_pepper(password: bytes) -> bytes:
    if not PEPPER:
        return password
    # Ensure pepper is bytes
    return password + (PEPPER.encode() if isinstance(PEPPER, str) else PEPPER)

def hash_password(password: bytes) -> bytes:
    """Return bcrypt hash (bytes)."""
    pw = _apply_pepper(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(pw, salt)
    return hashed  # store this (bytes) or hashed.decode('utf-8') in DB

def check_password(candidate: bytes, stored_hash: bytes) -> bool:
    """Verify password. If cost changed, caller may rehash and store updated hash."""
    try:
        return bcrypt.checkpw(_apply_pepper(candidate), stored_hash)
    except ValueError:
        # If stored_hash is malformed raise or treat as invalid
        return False

def needs_rehash(stored_hash: bytes) -> bool:
    """Return True if stored hash uses lower rounds than current."""
    try:
        # bcrypt hash format: $2b$12$<22charSalt><31charHash>
        parts = stored_hash.decode().split('$')
        if len(parts) < 3:
            return True
        rounds = int(parts[2])
        return rounds != BCRYPT_ROUNDS
    except Exception:
        return True
