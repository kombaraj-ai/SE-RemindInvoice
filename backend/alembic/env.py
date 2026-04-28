"""
Alembic environment script.

Configures the migration context to:
  - Pull DATABASE_URL from the environment (or .env via app.config.settings).
  - Import all SQLAlchemy models so autogenerate can detect schema changes.
  - Support both "offline" (SQL script generation) and "online" (live DB) modes.
"""

import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Make sure the backend/ package root is on sys.path so `app.*` imports work
# regardless of how alembic is invoked.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Import the declarative Base and ALL models.
# The models __init__ import triggers registration of every Table in
# Base.metadata, which autogenerate uses to diff against the live schema.
# ---------------------------------------------------------------------------
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401  — registers all models with metadata

# ---------------------------------------------------------------------------
# Pull DATABASE_URL from the environment / app settings.
# We do this before touching the Alembic config so env vars always win.
# ---------------------------------------------------------------------------
try:
    from app.config import settings as app_settings
    _database_url: str = app_settings.DATABASE_URL
except Exception:
    # Fallback: read directly from the environment (useful in CI pipelines
    # where the full app might not be importable due to missing deps).
    _database_url = os.environ.get("DATABASE_URL", "")
    if not _database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Provide it as an environment variable or in backend/.env"
        )

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url from alembic.ini with the real value.
config.set_main_option("sqlalchemy.url", _database_url)

# ---------------------------------------------------------------------------
# Set up Python logging from alembic.ini
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ---------------------------------------------------------------------------
# Target metadata — Alembic will diff against this to autogenerate migrations
# ---------------------------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def include_object(object, name, type_, reflected, compare_to):  # noqa: A002
    """
    Filter out objects that should not be managed by Alembic.

    Currently excludes nothing, but this hook is ready for future use
    (e.g. skipping spatial or extension tables).
    """
    return True


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and no DB connection,
    then emits migration SQL to stdout / a file for manual review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates a real connection to the database and applies migrations
    within a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    logger.info("Running migrations in OFFLINE mode")
    run_migrations_offline()
else:
    logger.info("Running migrations in ONLINE mode")
    run_migrations_online()
