"""
JWT token creation / verification and password hashing utilities.

All secrets are sourced from the settings object — never hardcoded.
"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing — bcrypt directly (passlib 1.7.4 is incompatible with bcrypt 4+)
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the *hashed* bcrypt password."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password* (cost factor 12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """
    Create a short-lived JWT access token.

    The ``type`` claim is set to ``"access"`` to prevent refresh tokens from
    being used as access tokens.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {**data, "exp": expire, "type": "access"}
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(data: dict) -> str:
    """
    Create a long-lived JWT refresh token.

    The ``type`` claim is set to ``"refresh"`` so it cannot be used to
    authenticate regular API calls.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {**data, "exp": expire, "type": "refresh"}
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_password_reset_token(data: dict) -> str:
    """
    Create a short-lived JWT for the password-reset flow (1-hour expiry).

    The ``type`` claim is set to ``"password_reset"`` to avoid token confusion.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {**data, "exp": expire, "type": "password_reset"}
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


# ---------------------------------------------------------------------------
# Token decoding
# ---------------------------------------------------------------------------

def decode_token(token: str) -> dict | None:
    """
    Decode and verify a JWT.

    Returns the payload dict on success, or ``None`` if the token is invalid
    or expired. Errors are logged at DEBUG level to avoid leaking token
    contents into production logs.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        logger.debug("Token decode failed: %s", exc)
        return None
