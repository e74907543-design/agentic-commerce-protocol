"""Example utilities for bcrypt password hashing with optional pepper support.

The helpers below aim to be copy/paste friendly and safe-by-default:

* Environment variables control the bcrypt cost factor (``BCRYPT_ROUNDS``) and
  an optional secret pepper (``PASSWORD_PEPPER``).
* Callers can provide either ``str`` or ``bytes`` inputs—everything is coerced to
  ``bytes`` internally.
* ``needs_rehash`` lets you detect when a stored hash uses a lower cost factor
  than the current configuration, so you can transparently upgrade hashes on
  the next successful login.
"""

from __future__ import annotations

import os
from typing import Final

import bcrypt

# bcrypt accepts log-rounds in the range [4, 31]. Anything outside that range is
# clamped to ensure we never raise when an invalid value sneaks in via env vars.
_MIN_ROUNDS: Final[int] = 4
_MAX_ROUNDS: Final[int] = 31
_DEFAULT_ROUNDS: Final[int] = 12


def _coerce_rounds(raw_value: str | None) -> int:
    """Parse the rounds value from the environment with validation."""

    if not raw_value:
        return _DEFAULT_ROUNDS

    try:
        rounds = int(raw_value)
    except (TypeError, ValueError):
        return _DEFAULT_ROUNDS

    return max(_MIN_ROUNDS, min(_MAX_ROUNDS, rounds))


# Configure cost via env var
BCRYPT_ROUNDS: Final[int] = _coerce_rounds(os.environ.get("BCRYPT_ROUNDS"))


def _coerce_bytes(value: bytes | str) -> bytes:
    """Ensure ``value`` is expressed as bytes (utf-8 for strings)."""

    return value if isinstance(value, bytes) else value.encode("utf-8")


def _load_pepper() -> bytes | None:
    """Read and normalise the optional pepper from the environment."""

    raw_pepper = os.environ.get("PASSWORD_PEPPER")
    if raw_pepper in (None, ""):
        return None
    return _coerce_bytes(raw_pepper)


# Optional pepper (keep in secrets manager)
PEPPER: Final[bytes | None] = _load_pepper()


def _apply_pepper(password: bytes | str) -> bytes:
    """Return ``password`` with the pepper appended (if configured)."""

    pw_bytes = _coerce_bytes(password)
    if PEPPER is None:
        return pw_bytes
    return pw_bytes + PEPPER


def hash_password(password: bytes | str) -> bytes:
    """Return a bcrypt hash suitable for storage (as bytes)."""

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(_apply_pepper(password), salt)
    return hashed  # store this (bytes) or hashed.decode("utf-8") in DB


def check_password(candidate: bytes | str, stored_hash: bytes | str) -> bool:
    """Verify the ``candidate`` password against a stored bcrypt hash."""

    try:
        return bcrypt.checkpw(_apply_pepper(candidate), _coerce_bytes(stored_hash))
    except (TypeError, ValueError):
        # If stored_hash is malformed raise or treat as invalid
        return False


def needs_rehash(stored_hash: bytes | str, desired_rounds: int | None = None) -> bool:
    """Return ``True`` if ``stored_hash`` is using fewer rounds than desired.

    ``desired_rounds`` allows callers to opt into a higher work factor before
    the environment variable is rolled out (useful for canary testing).
    """

    try:
        rounds = _extract_rounds(_coerce_bytes(stored_hash))
    except ValueError:
        return True

    target_rounds = desired_rounds or BCRYPT_ROUNDS
    target_rounds = max(_MIN_ROUNDS, min(_MAX_ROUNDS, target_rounds))
    return rounds < target_rounds


def _extract_rounds(stored_hash: bytes) -> int:
    """Parse the cost factor from a bcrypt hash."""

    try:
        parts = stored_hash.decode().split("$")
        # bcrypt format: $2b$12$<salt+hash>
        rounds_token = parts[2]
        return int(rounds_token)
    except (IndexError, ValueError, UnicodeDecodeError) as exc:  # pragma: no cover - defensive
        raise ValueError("Invalid bcrypt hash") from exc


if __name__ == "__main__":  # pragma: no cover - example usage
    password = "s3cr3t-password"
    stored = hash_password(password)
    print("hash:", stored.decode())
    print("valid:", check_password(password, stored))
    print("needs rehash:", needs_rehash(stored))
