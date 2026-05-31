"""Argon2id password hashing and verification service.

Only hashes are stored; cleartext passwords are never logged or persisted.
"""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

# Argon2id parameters: time_cost=3, memory_cost=65536 (64 MiB), parallelism=4
# These are conservative defaults suitable for a local academic platform.
_HASHER: PasswordHasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plaintext: str) -> str:
    """Return an Argon2id hash for *plaintext*.

    The result is safe to store in ``users.password_hash``.
    Cleartext is never logged.
    """
    return _HASHER.hash(plaintext)


def verify_password(password_hash: str, plaintext: str) -> bool:
    """Return *True* if *plaintext* matches *password_hash*, *False* otherwise.

    Swallows all argon2 verification errors and returns *False* to avoid
    leaking information about failure reason.
    """
    try:
        return _HASHER.verify(password_hash, plaintext)
    except (VerifyMismatchError, VerificationError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Return *True* if *password_hash* should be re-hashed with current parameters."""
    return _HASHER.check_needs_rehash(password_hash)
