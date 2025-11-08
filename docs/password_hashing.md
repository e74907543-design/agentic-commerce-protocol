# bcrypt Password Hashing Helper

The `examples/password_hashing.py` module centralises our bcrypt usage with a
few security-minded defaults:

* **Configurable work factor** – Set `BCRYPT_ROUNDS` to tune CPU cost without
  redeploying code.
* **Optional pepper** – Provide `PASSWORD_PEPPER` to append a secret value that
  lives outside the primary database (for example, in a secrets manager).
* **Safe checks** – Verification, re-hash detection, and malformed hash handling
  are wrapped in helper functions so callers do not repeat boilerplate.

Install dependencies and export configuration before using the CLI:

```bash
pip install bcrypt
export BCRYPT_ROUNDS=12
export PASSWORD_PEPPER="my-super-secret-pepper"
```

## Hash a password

```bash
python examples/password_hashing.py hash
```

If you omit `--password`, the script prompts securely via `getpass`.  Include
`--print-rounds` to echo the configured work factor alongside the hash.

## Verify an existing hash

```bash
python examples/password_hashing.py check '$2b$12$example...hash'
```

The command exits with status `0` when the password is correct and prints
`OK`.  Incorrect credentials print `INVALID` to `stderr` and exit with status
`1`.

## Decide whether to re-hash

```bash
python examples/password_hashing.py needs-rehash '$2b$10$legacyhashvalue'
```

If the stored hash used a lower work factor than `BCRYPT_ROUNDS`, the helper
suggests re-hashing and returns exit code `2`.  Hashes at or above the current
work factor print `no re-hash needed`.

## Import as a library

Applications can import the helpers directly:

```python
from examples.password_hashing import hash_password, check_password, needs_rehash
```

* `hash_password(password)` returns the bcrypt hash (`bytes`).
* `check_password(candidate, stored_hash)` returns a boolean.
* `needs_rehash(stored_hash)` flags legacy hashes that should be regenerated.

All helpers accept `str` or `bytes` and automatically apply the pepper when
configured.
