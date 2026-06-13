"""HTTP error helpers for production-safe responses."""

from app.config import settings


def safe_error_detail(
    error: Exception,
    *,
    fallback: str = "An internal error occurred",
) -> str:
    """Return detailed errors in development, generic message in production."""
    if settings.debug:
        return str(error)
    return fallback
