"""
Shared FastAPI dependency providers.

These allow all routers to import ``get_current_user``,
``get_current_active_user``, and ``get_admin_user`` from a single location,
preventing circular-import issues while keeping the JWT logic in
``app.auth.jwt``.
"""

import logging

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the bearer access token and return the authenticated ``User``.

    :raises UnauthorizedError: If the token is missing, malformed, expired,
                               or does not reference an active user account.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedError("Invalid token payload")

    user: User | None = (
        db.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise UnauthorizedError("User not found or account is inactive")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Return the current user only when the account is active."""
    if not user.is_active:
        raise ForbiddenError("Inactive user")
    return user


async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """Return the current user only when the account has admin privileges."""
    if not user.is_admin:
        raise ForbiddenError("Admin access required")
    return user
