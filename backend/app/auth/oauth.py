"""
Google OAuth 2.0 helpers.

All client credentials come from the settings object — never hardcoded.
"""

import logging
import secrets
from urllib.parse import urlencode

from httpx import AsyncClient, HTTPStatusError

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google OAuth endpoints
# ---------------------------------------------------------------------------
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def generate_oauth_state() -> str:
    """Generate a cryptographically-random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def get_google_auth_url(state: str) -> str:
    """
    Build the Google authorization URL that the browser should be redirected to.

    :param state: Opaque CSRF-protection value; must be validated in the callback.
    :returns: Full Google authorization URL with all required query parameters.
    """
    params: dict[str, str] = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange an authorization code for Google access / refresh tokens.

    :param code: The one-time authorization code received in the OAuth callback.
    :returns: Google token response payload (access_token, id_token, …).
    :raises HTTPStatusError: If Google returns a non-2xx response.
    """
    async with AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
        )
        try:
            resp.raise_for_status()
        except HTTPStatusError:
            logger.error(
                "Google token exchange failed: status=%s body=%s",
                resp.status_code,
                resp.text,
            )
            raise
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    """
    Fetch the authenticated user's profile from Google.

    :param access_token: A valid Google OAuth access token.
    :returns: User-info payload (id, email, name, picture, …).
    :raises HTTPStatusError: If Google returns a non-2xx response.
    """
    async with AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            resp.raise_for_status()
        except HTTPStatusError:
            logger.error(
                "Google user-info request failed: status=%s body=%s",
                resp.status_code,
                resp.text,
            )
            raise
        return resp.json()
