"""
FastAPI application factory for RemindInvoice.

Instantiates the app, wires up middleware, registers exception handlers,
mounts the health-check endpoint, and (when Phase 2 modules are ready)
includes all API routers under /api/v1.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.exceptions import AppException, app_exception_handler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router imports
# ---------------------------------------------------------------------------
from app.routers import auth, clients, invoices, reminders, dashboard, admin, subscription  # noqa: E402


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown logic."""
    # --- Startup ---
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    logger.info("Upload directory ensured at: %s", upload_dir)
    logger.info(
        "%s v%s starting (debug=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DEBUG,
    )

    yield  # application runs here

    # --- Shutdown ---
    logger.info("%s shutting down.", settings.APP_NAME)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # --- Rate limiting ---
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    application.add_middleware(SlowAPIMiddleware)

    # --- CORS ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handlers ---
    application.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]

    # --- Health check ---
    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    # --- API routers ---
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(clients.router, prefix="/api/v1")
    application.include_router(invoices.router, prefix="/api/v1")
    application.include_router(reminders.router, prefix="/api/v1")
    application.include_router(dashboard.router, prefix="/api/v1")
    application.include_router(admin.router, prefix="/api/v1")
    application.include_router(subscription.router, prefix="/api/v1")

    return application


app = create_app()
