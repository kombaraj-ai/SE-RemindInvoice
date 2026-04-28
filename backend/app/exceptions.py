"""
Custom application exceptions and FastAPI exception handlers.

Register the handler with:
    from app.exceptions import AppException, app_exception_handler
    app.add_exception_handler(AppException, app_exception_handler)
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)


class ConflictError(AppException):
    """Raised when a write operation conflicts with existing data."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT", 409)


class ForbiddenError(AppException):
    """Raised when the authenticated user lacks permission for an action."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, "FORBIDDEN", 403)


class UnauthorizedError(AppException):
    """Raised when the request is missing or carries invalid credentials."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, "UNAUTHORIZED", 401)


class ValidationError(AppException):
    """Raised when business-logic validation fails (distinct from Pydantic errors)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR", 422)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convert AppException subclasses into consistent JSON error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )
