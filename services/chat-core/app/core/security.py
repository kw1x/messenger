"""Password hashing and JWT helpers.

Bcrypt directly (no passlib) — passlib is unmaintained and brings nothing on
top of bcrypt's own API for the simple username/password use case.
"""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
