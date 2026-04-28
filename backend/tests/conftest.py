"""
Shared pytest fixtures for the RemindInvoice test suite.

Uses an on-disk SQLite database (test.db) so tests run without a real
PostgreSQL instance. The database schema is rebuilt fresh for every test
function to guarantee isolation.

The DATABASE_URL and SECRET_KEY environment variables are patched *before*
any application code is imported, because pydantic-settings reads them once
at module load time.
"""

import os

# ---------------------------------------------------------------------------
# Patch env vars BEFORE any app module is imported.
# pydantic-settings caches Settings via @lru_cache, so we set required vars
# early. The DATABASE_URL validator checks the prefix; we satisfy it here but
# the actual engine used in tests is SQLite (created below, not from config).
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_remindinvoice")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-do-not-use-in-production")
os.environ.setdefault("SENDGRID_API_KEY", "")  # disables email sending in tests
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Import all models so Base.metadata knows about every table
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# Test database — SQLite (file-based so FK pragma can be set per connection)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite:///./test_remindinvoice.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)


# Enable SQLite foreign-key enforcement (off by default in SQLite)
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db():
    """
    Provide a fresh SQLite session for each test.

    Creates all tables before the test and drops them afterwards so every
    test starts with a clean database.
    """
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Provide a FastAPI TestClient wired to the test SQLite session.

    Overrides the ``get_db`` dependency so all endpoint handlers use the
    same session as the test instead of the real PostgreSQL connection.
    """
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Higher-level convenience fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registered_user(client):
    """Register a user and return the response JSON."""
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client, registered_user):
    """Login with the registered test user and return Authorization headers."""
    resp = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_client_data(client, auth_headers):
    """Create a test client for the authenticated user and return the JSON."""
    resp = client.post(
        "/api/v1/clients",
        json={
            "name": "Acme Corp",
            "email": "acme@example.com",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def invoice_payload(test_client_data):
    """Return a minimal valid InvoiceCreate payload."""
    return {
        "client_id": test_client_data["id"],
        "issue_date": "2026-04-01",
        "due_date": "2026-04-30",
        "items": [
            {
                "description": "Web development",
                "quantity": "2",
                "unit_price": "500.00",
                "sort_order": 0,
            }
        ],
    }


@pytest.fixture()
def created_invoice(client, auth_headers, invoice_payload):
    """Create a draft invoice and return its JSON."""
    resp = client.post(
        "/api/v1/invoices",
        json=invoice_payload,
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
