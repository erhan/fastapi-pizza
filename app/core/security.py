"""Passwords and login tokens. Standard library + PyJWT: nothing here knows about FastAPI."""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000  # slow on purpose: a stolen database should be expensive to crack


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
