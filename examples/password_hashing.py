#!/usr/bin/env python3
"""Utilities for hashing and verifying passwords with bcrypt.

This module centralises bcrypt usage with support for cost tuning and a
configurable pepper.  It can be imported by applications or executed
as a small CLI to hash / verify passwords from the terminal.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from typing import Optional

try:
    import bcrypt
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "The bcrypt package is required. Install it with 'pip install bcrypt'."
    ) from exc


BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
PEPPER = os.environ.get("PASSWORD_PEPPER")


def _ensure_bytes(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def _apply_pepper(password: bytes) -> bytes:
    if not PEPPER:
        return password
    pepper_bytes = _ensure_bytes(PEPPER)
    return password + pepper_bytes


def hash_password(password: str | bytes) -> bytes:
    """Return the bcrypt hash of ``password`` as bytes."""
    pw = _ensure_bytes(password)
    pw = _apply_pepper(pw)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(pw, salt)


def check_password(candidate: str | bytes, stored_hash: str | bytes) -> bool:
    """Return ``True`` when ``candidate`` matches the ``stored_hash``."""
    try:
        candidate_bytes = _apply_pepper(_ensure_bytes(candidate))
        stored_hash_bytes = _ensure_bytes(stored_hash)
        return bcrypt.checkpw(candidate_bytes, stored_hash_bytes)
    except ValueError:
        return False


def needs_rehash(stored_hash: str | bytes) -> bool:
    """Return ``True`` if ``stored_hash`` uses fewer rounds than configured."""
    try:
        stored_hash_str = _ensure_bytes(stored_hash).decode("utf-8")
        parts = stored_hash_str.split("$")
        if len(parts) < 4:
            return True
        rounds = int(parts[2])
        return rounds < BCRYPT_ROUNDS
    except Exception:
        return True


def _password_argument(value: Optional[str]) -> bytes:
    if value is not None:
        return _ensure_bytes(value)
    prompt = "Password: "
    return _ensure_bytes(getpass.getpass(prompt))


def _hash_cmd(args: argparse.Namespace) -> int:
    password = _password_argument(args.password)
    hashed = hash_password(password)
    output = hashed.decode("utf-8")
    if args.print_rounds:
        print(f"rounds={BCRYPT_ROUNDS}")
    print(output)
    return 0


def _check_cmd(args: argparse.Namespace) -> int:
    password = _password_argument(args.password)
    stored_hash = _ensure_bytes(args.hash)
    if check_password(password, stored_hash):
        print("OK")
        return 0
    print("INVALID", file=sys.stderr)
    return 1


def _rehash_cmd(args: argparse.Namespace) -> int:
    stored_hash = _ensure_bytes(args.hash)
    if needs_rehash(stored_hash):
        print("re-hash recommended")
        return 2
    print("no re-hash needed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_parser = subparsers.add_parser("hash", help="Hash a password using bcrypt")
    hash_parser.add_argument("--password", help="Plaintext password. If omitted you will be prompted securely.")
    hash_parser.add_argument("--print-rounds", action="store_true", help="Include the rounds used in stdout")
    hash_parser.set_defaults(func=_hash_cmd)

    check_parser = subparsers.add_parser("check", help="Verify a password against a stored hash")
    check_parser.add_argument("hash", help="Existing bcrypt hash to compare against")
    check_parser.add_argument("--password", help="Plaintext password. If omitted you will be prompted securely.")
    check_parser.set_defaults(func=_check_cmd)

    rehash_parser = subparsers.add_parser("needs-rehash", help="Determine whether a stored hash should be re-generated")
    rehash_parser.add_argument("hash", help="Existing bcrypt hash to inspect")
    rehash_parser.set_defaults(func=_rehash_cmd)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
