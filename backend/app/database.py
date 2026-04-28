"""
Database engine, session factory, declarative base, and dependency injection helper.

Usage in FastAPI endpoints:
    from app.database import get_db
    from sqlalchemy.orm import Session

    @router.get("/example")
    async def example(db: Session = Depends(get_db)):
        ...
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # recycle stale connections transparently
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # recycle connections after 1 hour
    echo=settings.DEBUG,  # log SQL in debug mode only
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Declarative base — ALL models must inherit from this
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for the duration of a request, then close it.

    Example:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Database session error — rolling back")
        db.rollback()
        raise
    finally:
        db.close()
