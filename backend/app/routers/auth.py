"""
Authentication router — /api/v1/auth/*

Endpoints
---------
POST /register           Register a new account (rate-limited)
POST /login              Obtain tokens via email + password (rate-limited)
POST /refresh            Rotate tokens using a refresh token
POST /logout             Revoke a refresh token
GET  /me                 Return the authenticated user's profile
PUT  /me                 Update the authenticated user's profile
GET  /google             Return the Google OAuth authorization URL
GET  /google/callback    Handle the Google OAuth callback
POST /forgot-password    Send a password-reset email (rate-limited)
POST /reset-password     Complete the password-reset flow
"""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth.oauth import generate_oauth_state, get_google_auth_url
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import AppException
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter — shared with the application-level limiter in main.py
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_STATE_COOKIE = "oauth_state"


def _handle_app_exception(exc: AppException) -> None:
    """Re-raise an AppException as an HTTPException so FastAPI handles it."""
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("5/15minutes")
async def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a new user account with email and password."""
    try:
        user = auth_service.register(db, body)
    except AppException as exc:
        _handle_app_exception(exc)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Login (form-encoded so FastAPI /docs Authorize button works)
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtain access and refresh tokens",
)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.

    Accepts ``application/x-www-form-urlencoded`` (username = email).
    """
    try:
        _user, access_token, refresh_token = auth_service.login(
            db, email=form_data.username, password=form_data.password
        )
    except AppException as exc:
        _handle_app_exception(exc)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate tokens using a refresh token",
)
async def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        access_token, refresh_token = auth_service.refresh_tokens(db, body.refresh_token)
    except AppException as exc:
        _handle_app_exception(exc)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the refresh token (logout)",
)
async def logout(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> Response:
    """Revoke the provided refresh token. The client must delete stored tokens."""
    auth_service.logout(db, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Current user profile
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Return the authenticated user's profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile information for the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the authenticated user's profile",
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update mutable profile fields (full_name, avatar_url)."""
    try:
        user = auth_service.update_profile(db, current_user.id, body)
    except AppException as exc:
        _handle_app_exception(exc)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Google OAuth — initiate
# ---------------------------------------------------------------------------

@router.get(
    "/google",
    summary="Redirect browser to Google OAuth authorization URL",
)
async def google_auth() -> RedirectResponse:
    """
    Set the CSRF state cookie and redirect the browser directly to Google.

    Must be a full browser navigation (not an AJAX call) so that the
    Set-Cookie header is accepted by the browser for localhost:8000.
    """
    state = generate_oauth_state()
    auth_url = get_google_auth_url(state)

    redirect = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key=_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=600,
    )
    return redirect


# ---------------------------------------------------------------------------
# Google OAuth — callback
# ---------------------------------------------------------------------------

@router.get(
    "/google/callback",
    status_code=status.HTTP_200_OK,
    summary="Handle the Google OAuth callback",
)
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
    oauth_state: str | None = Cookie(default=None, alias=_STATE_COOKIE),
) -> RedirectResponse:
    """
    Complete the Google OAuth flow.

    Validates the state parameter, exchanges the authorization code for
    tokens, upserts the user, and redirects to the frontend with JWT
    tokens as query parameters.

    Note: Passing tokens in the URL is acceptable for the initial OAuth
    redirect; the frontend should immediately move them to memory / secure
    storage and strip them from the address bar.
    """
    expected_state = oauth_state or ""
    if not expected_state:
        logger.warning("Google callback received but no state cookie found")
        redirect_url = f"{settings.FRONTEND_URL}/login?error=oauth_state_missing"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    try:
        _user, access_token, refresh_token = await auth_service.google_callback(
            db=db,
            code=code,
            state=state,
            expected_state=expected_state,
        )
    except AppException as exc:
        logger.error("Google OAuth callback failed: %s", exc.message)
        redirect_url = f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    # Use a URL fragment (#) so tokens are NOT sent to the server in Referer
    # headers and do not appear in server access logs or browser history.
    # The frontend JavaScript reads window.location.hash and must immediately
    # strip the fragment from the address bar after extracting the tokens.
    params = urlencode({"access_token": access_token, "refresh_token": refresh_token})
    redirect_url = f"{settings.FRONTEND_URL}/oauth/callback#{params}"

    resp = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    # Clear the state cookie.
    resp.delete_cookie(key=_STATE_COOKIE)
    return resp


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Send a password-reset email",
)
@limiter.limit("5/15minutes")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Send a password-reset link to the specified email address.

    Always returns the same response regardless of whether the email exists
    in order to prevent user-enumeration attacks.
    """
    auth_service.forgot_password(db, body.email)
    return {"message": "If an account with that email exists, a reset link has been sent"}


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Complete the password-reset flow",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Apply a new password using the signed reset token from the email link."""
    try:
        auth_service.reset_password(db, body.token, body.new_password)
    except AppException as exc:
        _handle_app_exception(exc)
    except Exception:
        logger.exception("Unexpected error during password reset")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )
    return {"message": "Password updated successfully"}
