"""Authentication service."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password
from app.services.icpIdentityManager import ICPIdentityManager, ICPError

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""

    @staticmethod
    async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user with automatic ICP identity setup."""
        # Check if user already exists
        stmt = select(User).where(
            (User.email == user_create.email) | (User.username == user_create.username)
        )
        result = await session.execute(stmt)
        if result.scalars().first():
            raise ValueError("User with this email or username already exists")

        # Create new user
        hashed_password = hash_password(user_create.password)
        user = User(
            email=user_create.email,
            username=user_create.username,
            password_hash=hashed_password,
            full_name=user_create.full_name,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # Automatically create ICP identity for the user
        try:
            identity_info = await ICPIdentityManager.create_user_identity(session, user)
            logger.info(
                f"Created ICP identity for new user {user.id}: {identity_info['principal_id']}"
            )
        except ICPError as e:
            logger.warning(f"Failed to create ICP identity for user {user.id}: {str(e)}")
            # Continue with user creation even if identity creation fails
            # User can set up identity later through the dashboard

        return user

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user or not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()
