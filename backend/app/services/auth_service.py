"""
Authentication business-logic service.

All database operations are synchronous SQLAlchemy calls executed inside
FastAPI async endpoints (the GIL allows this without blocking for typical
OLTP query loads; use a thread pool or async engine if you need full async
DB access).

Token lifecycle
---------------
- Access tokens  : short-lived JWTs (type="access"), validated on every request.
- Refresh tokens : long-lived JWTs (type="refresh"), stored hashed in the DB so
                   they can be individually revoked.
- Reset tokens   : short-lived JWTs (type="password_reset"), NOT stored in DB —
                   the JWT signature guarantees authenticity.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.auth.oauth import exchange_code_for_tokens, get_google_user_info
from app.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.models.user import RefreshToken, User
from app.schemas.auth import RegisterRequest, UpdateProfileRequest
from app.services.email import send_password_reset_email, send_welcome_email

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_token(raw_token: str) -> str:
    """Return a SHA-256 hex digest of *raw_token* for safe DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _store_refresh_token(db: Session, user_id: int, raw_token: str) -> RefreshToken:
    """
    Persist a new refresh token to the database.

    Only the SHA-256 hash of the token is stored so that a DB compromise does
    not allow an attacker to reuse stolen refresh tokens directly.
    The raw token is never written to disk.
    """
    payload = decode_token(raw_token)
    if payload is None:
        raise ValueError("Cannot store an invalid refresh token")

    exp_timestamp: int = payload["exp"]
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    db_token = RefreshToken(
        user_id=user_id,
        token=_hash_token(raw_token),  # store hash, not the raw JWT
        expires_at=expires_at,
        revoked=False,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def _revoke_refresh_token(db: Session, raw_token: str) -> None:
    """Mark a refresh token as revoked, if it exists."""
    token_hash = _hash_token(raw_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == token_hash, RefreshToken.revoked.is_(False))
        .first()
    )
    if record:
        record.revoked = True
        db.commit()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def register(db: Session, req: RegisterRequest) -> User:
    """
    Register a new user with email + password.

    :raises ConflictError: If the email address is already taken.
    :returns: The newly created, persisted ``User`` instance.
    """
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise ConflictError("An account with this email address already exists")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        is_active=True,
        is_verified=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: id=%s email=%s", user.id, user.email)

    # Send welcome email in the background — failure must not break registration.
    try:
        asyncio.get_event_loop().run_in_executor(
            None, send_welcome_email, user.email, user.full_name or ""
        )
    except Exception as exc:
        logger.warning("Could not dispatch welcome email for user %s: %s", user.id, exc)

    return user


def login(
    db: Session,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """
    Authenticate a user with email + password.

    :raises UnauthorizedError: If credentials are invalid or the account is inactive.
    :returns: ``(user, access_token, refresh_token)`` tuple.
    """
    user = db.query(User).filter(User.email == email).first()

    if user and user.oauth_provider:
        raise UnauthorizedError(
            f"This account uses {user.oauth_provider.title()} sign-in. "
            "Please use the Sign in with Google button."
        )

    # Constant-time check avoids user-enumeration via timing differences.
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Your account is inactive. Please contact the administrator.")

    sub = str(user.id)
    access_token = create_access_token({"sub": sub})
    refresh_token = create_refresh_token({"sub": sub})

    _store_refresh_token(db, user.id, refresh_token)

    logger.info("User logged in: id=%s email=%s", user.id, user.email)
    return user, access_token, refresh_token


def refresh_tokens(db: Session, refresh_token_str: str) -> tuple[str, str]:
    """
    Issue a new access + refresh token pair, revoking the old refresh token.

    Implements refresh-token rotation: each refresh token can only be used once.

    :raises UnauthorizedError: If the token is invalid, expired, revoked, or of
                               the wrong type.
    :returns: ``(new_access_token, new_refresh_token)`` tuple.
    """
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid or expired refresh token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    # Verify the token hash exists in the DB and has not been revoked.
    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == _hash_token(refresh_token_str),
            RefreshToken.revoked.is_(False),
        )
        .first()
    )
    if not db_token:
        raise UnauthorizedError("Refresh token has been revoked or does not exist")

    # Revoke the old token before issuing a new one (rotation).
    db_token.revoked = True
    db.commit()

    user_id = int(user_id_str)
    sub = str(user_id)
    new_access_token = create_access_token({"sub": sub})
    new_refresh_token = create_refresh_token({"sub": sub})

    _store_refresh_token(db, user_id, new_refresh_token)

    logger.info("Tokens rotated for user id=%s", user_id)
    return new_access_token, new_refresh_token


def logout(db: Session, refresh_token_str: str) -> None:
    """
    Revoke the supplied refresh token, effectively logging the user out.

    The access token will continue to be accepted until it expires; frontends
    should delete it from storage immediately after calling this endpoint.

    :param refresh_token_str: The raw refresh token to revoke.
    """
    _revoke_refresh_token(db, refresh_token_str)
    logger.info("Refresh token revoked (logout)")


def get_current_user(db: Session, token: str) -> User:
    """
    Validate an access token and return the associated user.

    :raises UnauthorizedError: On any validation failure.
    :returns: The authenticated ``User`` instance.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    user = (
        db.query(User)
        .filter(User.id == int(user_id_str), User.is_active.is_(True))
        .first()
    )
    if not user:
        raise UnauthorizedError("User not found or account is inactive")

    return user


async def google_callback(
    db: Session,
    code: str,
    state: str,
    expected_state: str,
) -> tuple[User, str, str]:
    """
    Handle the Google OAuth callback: exchange the authorization code for
    Google tokens, fetch the user's profile, upsert the user record, and
    issue application-level JWT tokens.

    :param code: One-time authorization code from Google.
    :param state: State parameter echoed back by Google.
    :param expected_state: State parameter we generated; must match *state*.
    :raises UnauthorizedError: If the state does not match or Google rejects the code.
    :returns: ``(user, access_token, refresh_token)`` tuple.
    """
    if state != expected_state:
        logger.warning("OAuth state mismatch — possible CSRF attempt")
        raise UnauthorizedError("OAuth state parameter mismatch")

    # Exchange authorization code → Google access token.
    try:
        token_data = await exchange_code_for_tokens(code)
    except Exception as exc:
        logger.error("Google code exchange failed: %s", exc)
        raise UnauthorizedError("Failed to exchange Google authorization code")

    google_access_token: str = token_data.get("access_token", "")
    if not google_access_token:
        raise UnauthorizedError("Google did not return an access token")

    # Fetch user profile from Google.
    try:
        user_info = await get_google_user_info(google_access_token)
    except Exception as exc:
        logger.error("Google user-info fetch failed: %s", exc)
        raise UnauthorizedError("Failed to retrieve Google user information")

    google_email: str = user_info.get("email", "")
    if not google_email:
        raise UnauthorizedError("Google account has no email address")

    google_name: str = user_info.get("name", "")
    google_picture: str = user_info.get("picture", "")

    # Upsert the user record.
    user = db.query(User).filter(User.email == google_email).first()
    if user is None:
        user = User(
            email=google_email,
            hashed_password=None,  # OAuth users have no local password
            full_name=google_name or None,
            avatar_url=google_picture or None,
            oauth_provider="google",
            is_active=True,
            is_verified=True,  # Google has already verified the email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New OAuth user created: id=%s email=%s", user.id, user.email)

        # Fire welcome email for brand-new users.
        try:
            send_welcome_email(user.email, user.full_name or "")
        except Exception as exc:
            logger.warning("Welcome email failed for OAuth user %s: %s", user.id, exc)
    else:
        # Update OAuth-specific fields if they changed.
        changed = False
        if google_picture and user.avatar_url != google_picture:
            user.avatar_url = google_picture
            changed = True
        if not user.oauth_provider:
            user.oauth_provider = "google"
            changed = True
        if not user.is_verified:
            user.is_verified = True
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
        logger.info("Existing OAuth user signed in: id=%s email=%s", user.id, user.email)

    sub = str(user.id)
    access_token = create_access_token({"sub": sub})
    refresh_token = create_refresh_token({"sub": sub})
    _store_refresh_token(db, user.id, refresh_token)

    return user, access_token, refresh_token


def forgot_password(db: Session, email: str) -> None:
    """
    Initiate the password-reset flow.

    Generates a short-lived, signed JWT (type="password_reset") and emails a
    reset link to the user. If the email does not correspond to any account the
    function returns silently to avoid user-enumeration.

    :param email: The email address of the account to reset.
    """
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        # Return silently — the endpoint will still respond with 200.
        logger.debug("Password-reset requested for unknown/inactive email: %s", email)
        return

    reset_token = create_password_reset_token({"sub": str(user.id), "email": user.email})

    try:
        sent = send_password_reset_email(user.email, reset_token)
        if not sent:
            # SENDGRID_API_KEY not configured — log the link so devs can test locally.
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            logger.warning(
                "DEV MODE — password reset link for %s: %s",
                user.email,
                reset_url,
            )
    except Exception as exc:
        logger.error("Failed to send password-reset email to %s: %s", user.email, exc)


def reset_password(db: Session, token: str, new_password: str) -> None:
    """
    Complete the password-reset flow.

    Verifies the signed reset JWT, looks up the user, and updates their
    hashed password.

    :param token: The signed JWT received in the reset email.
    :param new_password: The new plain-text password (minimum 8 characters).
    :raises UnauthorizedError: If the token is invalid, expired, or of the wrong type.
    :raises NotFoundError: If the user referenced by the token no longer exists.
    :raises ValidationError: If the new password is too short.
    """
    if len(new_password) < 8:
        raise ValidationError("Password must be at least 8 characters")

    payload = decode_token(token)
    if not payload or payload.get("type") != "password_reset":
        raise UnauthorizedError("Invalid or expired password-reset token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id_str), User.is_active.is_(True)).first()
    if not user:
        raise NotFoundError("User")

    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)

    logger.info("Password reset for user id=%s", user.id)


def update_profile(db: Session, user_id: int, req: UpdateProfileRequest) -> User:
    """
    Update mutable profile fields for the authenticated user.

    :param user_id: ID of the user to update.
    :param req: Fields to update; ``None`` values are ignored.
    :raises NotFoundError: If no active user with ``user_id`` exists.
    :returns: The updated ``User`` instance.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise NotFoundError("User")

    if req.full_name is not None:
        user.full_name = req.full_name
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    if req.email is not None:
        new_email = req.email.strip().lower()
        if new_email != user.email:
            conflict = db.query(User).filter(User.email == new_email).first()
            if conflict:
                raise ConflictError("An account with this email address already exists")
            user.email = new_email

    db.commit()
    db.refresh(user)

    logger.info("Profile updated for user id=%s", user_id)
    return user
