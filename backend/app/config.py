"""
Application settings loaded from environment variables.

All secrets and environment-specific values must be provided via .env or
the shell environment — never hardcoded here.
"""

import logging
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    APP_NAME: str = "RemindInvoice"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str  # required — no default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str  # required — e.g. postgresql://user:pass@host:5432/db

    # ------------------------------------------------------------------
    # Google OAuth
    # ------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ------------------------------------------------------------------
    # Email (SendGrid)
    # ------------------------------------------------------------------
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "hello@remindinvoice.com"
    FROM_NAME: str = "RemindInvoice"
    # Legacy aliases kept for compatibility
    EMAIL_FROM: str = "noreply@remindinvoice.com"
    EMAIL_FROM_NAME: str = "RemindInvoice"
    RESEND_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Frontend / CORS
    # ------------------------------------------------------------------
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ------------------------------------------------------------------
    # File storage
    # ------------------------------------------------------------------
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ------------------------------------------------------------------
    # Dodo Payments
    # ------------------------------------------------------------------
    DODO_API_KEY: str = ""
    DODO_WEBHOOK_SECRET: str = ""
    DODO_PRODUCT_ID_SILVER: str = ""   # product ID for ₹5/month Silver plan
    DODO_PRODUCT_ID_GOLD: str = ""     # product ID for ₹10/month Gold plan

    # ------------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()


settings: Settings = get_settings()
