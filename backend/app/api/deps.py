"""Shared FastAPI dependencies for authentication and authorization."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.db import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.utils.security import verify_token


async def get_bearer_token(
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


async def get_current_user_id(
    token: Annotated[str, Depends(get_bearer_token)],
) -> int:
    """Resolve authenticated user ID from JWT access token."""
    token_data = verify_token(token, token_type="access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(token_data.sub)


async def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Load the authenticated active user."""
    user = await AuthService.get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    if settings.require_email_verification and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return user


async def require_superuser(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require platform superuser privileges."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return user


async def require_admin_api_key(
    x_admin_api_key: Annotated[Optional[str], Header()] = None,
) -> None:
    """Protect internal/admin endpoints with a shared API key."""
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is not configured",
        )
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
        )


async def require_admin(
    _: Annotated[None, Depends(require_admin_api_key)],
) -> None:
    """Alias dependency for admin-only routes."""
