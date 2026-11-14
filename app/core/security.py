"""Passwords and login tokens. Standard library + PyJWT: nothing here knows about FastAPI."""

import asyncio
import base64
import hashlib
import hmac
import secrets
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000  # slow on purpose: a stolen database should be expensive to crack

# Hashing is pure CPU work, so it gets two threads of its own. A rush of sign-ups queues up
# here instead of taking the CPU away from everybody who only wants to read the menu.
_hashers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="hasher")


async def run_in_hasher[T](func: Callable[..., T], *args: Any) -> T:
    """Run `hash_password` / `verify_password` off the event loop, at most two at a time."""
    return await asyncio.get_running_loop().run_in_executor(_hashers, func, *args)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return "$".join([ALGORITHM, str(ITERATIONS), _b64(salt), _b64(digest)])


def verify_password(password: str, hashed: str) -> bool:
    try:
        algorithm, iterations, salt, expected = hashed.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt), int(iterations)
        )
    except ValueError:
        return False
    return hmac.compare_digest(_b64(digest), expected)


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    """The user id inside a valid token; None if it is expired, forged or malformed."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")
