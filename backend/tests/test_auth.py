"""
Tests for the authentication router — /api/v1/auth/*

Covers: register, login, token refresh, logout, profile (/me).
All tests use the SQLite in-memory fixture provided by conftest.py.
"""

import pytest


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """Valid payload should create a user and return 201 with user data."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "strongpass1",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        # Ensure password is never exposed
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_returns_user_flags(self, client):
        """Newly registered user should be active but not verified or admin."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "flags@example.com",
                "password": "flagspass99",
                "full_name": "Flag Tester",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert data["is_admin"] is False

    def test_register_duplicate_email(self, client):
        """Registering twice with the same email should return 409 Conflict."""
        payload = {
            "email": "dup@example.com",
            "password": "duppass99",
            "full_name": "Dup User",
        }
        resp1 = client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409

    def test_register_short_password(self, client):
        """Password shorter than 8 characters should be rejected with 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "abc",
                "full_name": "Short Pass",
            },
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        """Malformed email address should be rejected with 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "validpass1",
                "full_name": "Bad Email",
            },
        )
        assert resp.status_code == 422

    def test_register_missing_full_name(self, client):
        """Omitting required full_name field should return 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "noname@example.com",
                "password": "validpass1",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    """POST /api/v1/auth/login (form data)"""

    def test_login_success(self, client, registered_user):
        """Valid credentials should return 200 with access_token and refresh_token."""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpass123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 10
        assert len(data["refresh_token"]) > 10

    def test_login_wrong_password(self, client, registered_user):
        """Wrong password should return 401."""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        """Unknown email should return 401 (no user-enumeration)."""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nobody@example.com",
                "password": "somepassword",
            },
        )
        assert resp.status_code == 401

    def test_login_empty_password(self, client, registered_user):
        """Empty password should return 401."""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "",
            },
        )
        assert resp.status_code == 401

    def test_login_tokens_are_different(self, client, registered_user):
        """Access token and refresh token must be distinct strings."""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] != data["refresh_token"]


# ---------------------------------------------------------------------------
# Current user profile — GET /me
# ---------------------------------------------------------------------------


class TestGetMe:
    """GET /api/v1/auth/me"""

    def test_get_me_authenticated(self, client, auth_headers):
        """Valid bearer token should return the user's own profile."""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data

    def test_get_me_unauthenticated(self, client):
        """Missing bearer token should return 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Malformed/fake token should return 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.a.real.jwt"},
        )
        assert resp.status_code == 401

    def test_get_me_response_fields(self, client, auth_headers):
        """Response must include all expected user fields."""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        required_fields = {
            "id", "email", "full_name", "is_active",
            "is_verified", "is_admin", "created_at",
        }
        assert required_fields.issubset(data.keys())


# ---------------------------------------------------------------------------
# Update profile — PUT /me
# ---------------------------------------------------------------------------


class TestUpdateMe:
    """PUT /api/v1/auth/me"""

    def test_update_full_name(self, client, auth_headers):
        """Should update full_name and return updated user object."""
        resp = client.put(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_update_avatar_url(self, client, auth_headers):
        """Should update avatar_url field."""
        resp = client.put(
            "/api/v1/auth/me",
            json={"avatar_url": "https://example.com/avatar.png"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["avatar_url"] == "https://example.com/avatar.png"

    def test_update_me_unauthenticated(self, client):
        """Unauthenticated update attempt should return 401."""
        resp = client.put("/api/v1/auth/me", json={"full_name": "Hacker"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """POST /api/v1/auth/refresh"""

    def test_refresh_token_success(self, client, registered_user):
        """Valid refresh token should return a new token pair with 200."""
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_rotates_token(self, client, registered_user):
        """After refresh, the old refresh token must not be reusable (rotation)."""
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )
        old_refresh = login_resp.json()["refresh_token"]

        # Use it once successfully
        resp1 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp1.status_code == 200

        # Attempt to reuse the old token — should fail
        resp2 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp2.status_code == 401

    def test_refresh_invalid_token(self, client):
        """Garbage refresh token should return 401."""
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "totally.invalid.token"},
        )
        assert resp.status_code == 401

    def test_refresh_with_access_token_fails(self, client, auth_headers):
        """Passing an access token to the refresh endpoint should fail (wrong type)."""
        access_token = auth_headers["Authorization"].split(" ")[1]
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    """POST /api/v1/auth/logout"""

    def test_logout_success(self, client, registered_user):
        """Valid refresh token should be revoked and return 204 No Content."""
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 204

    def test_logout_revokes_token(self, client, registered_user):
        """After logout the refresh token must not be accepted for rotation."""
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpass123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Logout
        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Attempt to use the token after logout
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401

    def test_logout_unknown_token_is_no_op(self, client, registered_user):
        """
        Logout with an unknown token should silently succeed (204).

        The endpoint must not leak whether the token existed.
        """
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "unknown.token.value"},
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Forgot / reset password
# ---------------------------------------------------------------------------


class TestForgotResetPassword:
    """POST /api/v1/auth/forgot-password and /api/v1/auth/reset-password"""

    def test_forgot_password_always_200(self, client, registered_user):
        """Should return 200 regardless of whether the email exists (anti-enumeration)."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        assert resp.status_code == 200

    def test_forgot_password_unknown_email(self, client):
        """Should still return 200 for unknown emails."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@nowhere.com"},
        )
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """An invalid/fake reset token should return 401."""
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "not.a.real.reset.token",
                "new_password": "newstrongpass",
            },
        )
        assert resp.status_code == 401

    def test_reset_password_short_new_password(self, client):
        """New password shorter than 8 characters should return 422."""
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "doesnt.matter.here",
                "new_password": "short",
            },
        )
        assert resp.status_code == 422
